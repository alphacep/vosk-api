from __future__ import annotations

import asyncio
import hmac
import http
import logging
import re
import socket
from collections.abc import Awaitable, Coroutine, Generator, Iterable, Sequence
from types import TracebackType
from typing import Any, Callable, Mapping, Self, cast

from ..exceptions import InvalidHeader
from ..extensions.base import ServerExtensionFactory
from ..extensions.permessage_deflate import enable_server_permessage_deflate
from ..frames import CloseCode
from ..headers import (
    build_www_authenticate_basic,
    parse_authorization_basic,
    validate_subprotocols,
)
from ..http11 import SERVER, Request, Response
from ..protocol import CONNECTING, OPEN, Event
from ..server import ServerProtocol
from ..typing import LoggerLike, Origin, StatusLike, Subprotocol
from ..utils import get_socket_name
from .connection import Connection, broadcast


__all__ = [
    "broadcast",
    "serve",
    "unix_serve",
    "ServerConnection",
    "Server",
    "basic_auth",
]


class ServerConnection(Connection):
    """
    :mod:`asyncio` implementation of a WebSocket server connection.

    :class:`ServerConnection` provides :meth:`recv` and :meth:`send` methods for
    receiving and sending messages.

    It supports asynchronous iteration to receive messages::

        async for message in websocket:
            await process(message)

    The iterator exits normally when the connection is closed with code
    1000 (OK) or 1001 (going away) or without a close code. It raises a
    :exc:`~websockets.exceptions.ConnectionClosedError` when the connection is
    closed with any other code.

    The ``ping_interval``, ``ping_timeout``, ``close_timeout``, ``max_queue``,
    and ``write_limit`` arguments have the same meaning as in :func:`serve`.

    Args:
        protocol: Sans-I/O connection.
        server: Server that manages this connection.

    """

    def __init__(
        self,
        protocol: ServerProtocol,
        server: Server,
        *,
        ping_interval: float | None = 20,
        ping_timeout: float | None = 20,
        close_timeout: float | None = 10,
        max_queue: int | None | tuple[int | None, int | None] = 16,
        write_limit: int | tuple[int, int | None] = 2**15,
    ) -> None:
        self.protocol: ServerProtocol
        super().__init__(
            protocol,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            close_timeout=close_timeout,
            max_queue=max_queue,
            write_limit=write_limit,
        )
        self.server = server
        self.request_rcvd: asyncio.Future[None] = self.loop.create_future()
        self.username: str  # see basic_auth()
        self.handler: Callable[[ServerConnection], Awaitable[None]]  # see route()
        self.handler_kwargs: Mapping[str, Any]  # see route()

    def respond(self, status: StatusLike, text: str) -> Response:
        """
        Create a plain text HTTP response.

        ``process_request`` and ``process_response`` may call this method to
        return an HTTP response instead of performing the WebSocket opening
        handshake.

        You can modify the response before returning it, for example by changing
        HTTP headers.

        Args:
            status: HTTP status code.
            text: HTTP response body; it will be encoded to UTF-8.

        Returns:
            HTTP response to send to the client.

        """
        return self.protocol.reject(status, text)

    async def handshake(
        self,
        process_request: (
            Callable[
                [ServerConnection, Request],
                Awaitable[Response | None] | Response | None,
            ]
            | None
        ) = None,
        process_response: (
            Callable[
                [ServerConnection, Request, Response],
                Awaitable[Response | None] | Response | None,
            ]
            | None
        ) = None,
        server_header: str | None = SERVER,
    ) -> None:
        """
        Perform the opening handshake.

        """
        await asyncio.wait(
            [self.request_rcvd, self.connection_lost_waiter],
            return_when=asyncio.FIRST_COMPLETED,
        )

        if self.request is not None:
            response = None

            if process_request is not None:
                try:
                    response = process_request(self, self.request)
                    if isinstance(response, Awaitable):
                        response = await response
                except Exception as exc:
                    self.protocol.handshake_exc = exc
                    self.logger.error("process_request failed", exc_info=True)
                    response = self.protocol.reject(
                        http.HTTPStatus.INTERNAL_SERVER_ERROR,
                        (
                            "Failed to open a WebSocket connection.\n"
                            "See server log for more information.\n"
                        ),
                    )

            if response is None:
                self.response = self.protocol.accept(self.request)
            else:
                assert isinstance(response, Response)  # help mypy
                self.response = response

            if server_header is not None:
                self.response.headers["Server"] = server_header

            response = None

            if process_response is not None:
                try:
                    response = process_response(self, self.request, self.response)
                    if isinstance(response, Awaitable):
                        response = await response
                except Exception as exc:
                    self.protocol.handshake_exc = exc
                    self.logger.error("process_response failed", exc_info=True)
                    response = self.protocol.reject(
                        http.HTTPStatus.INTERNAL_SERVER_ERROR,
                        (
                            "Failed to open a WebSocket connection.\n"
                            "See server log for more information.\n"
                        ),
                    )

            if response is not None:
                assert isinstance(response, Response)  # help mypy
                self.response = response

            # Reject the connection if the server started closing during the
            # opening handshake. Don't yield before send_response() to avoid
            # a race condition after checking if the server is closing.
            if (
                self.response.status_code == http.HTTPStatus.SWITCHING_PROTOCOLS
                and not self.server.is_serving()
            ):
                self.response = self.protocol.reject(
                    http.HTTPStatus.SERVICE_UNAVAILABLE,
                    "Server is shutting down.\n",
                )

            # Don't respond if the connection was closed during the handshake.
            if self.state is CONNECTING:
                async with self.send_context(expected_state=CONNECTING):
                    self.protocol.send_response(self.response)

    def process_event(self, event: Event) -> None:
        """
        Process one incoming event.

        """
        # First event - handshake request.
        if self.request is None:
            assert isinstance(event, Request)
            self.request = event
            self.request_rcvd.set_result(None)
        # Later events - frames.
        else:
            super().process_event(event)

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        super().connection_made(transport)
        # The handler task must be registered in self.handler_tasks now. If it
        # was registered inside the task, a race condition could happen when
        # closing the server after scheduling the task but before it executes.
        handler_task = self.loop.create_task(self.server.handler(self))
        self.server.handler_tasks.add(handler_task)


class Server:
    """
    WebSocket server returned by :func:`serve`.

    This class mirrors most of the API of :class:`asyncio.Server`, with the
    following differences:

    * You can invoke :func:`serve` as ``async with serve(...) as server: ...``
      in addition to ``server = await serve(...)`` to start the server.

    * It doesn't provide ``close_clients`` or ``abort_clients``; by default,
      :meth:`close` closes existing connections with code 1001 (going away).

    Args:
        handler: Handler for one connection. It receives an asyncio protocol.
        logger: Logger for this server.
            It defaults to ``logging.getLogger("websockets.server")``.
            See the :doc:`logging guide <../../topics/logging>` for details.

    """

    def __init__(
        self,
        create_server: Callable[[], Coroutine[Any, Any, asyncio.Server]],
        handler: Callable[[ServerConnection], Coroutine[Any, Any, None]],
        logger: LoggerLike | None = None,
    ) -> None:
        self.create_server = create_server
        self.handler = handler
        if logger is None:
            logger = logging.getLogger("websockets.server")
        self.logger = logger

        # Keep track of active connections and connection handler tasks.
        self.all_connections: set[ServerConnection] = set()
        self.handler_tasks: set[asyncio.Task[None]] = set()

        # Task responsible for closing the server and terminating connections.
        self.close_task: asyncio.Task[None] | None = None

        # Completed when the server is closed and connections are terminated.
        loop = asyncio.get_running_loop()
        self.handlers_waiter: asyncio.Future[None] = loop.create_future()

    @property
    def connections(self) -> set[ServerConnection]:
        """
        Set of active connections.

        This property contains all connections that completed the opening
        handshake successfully and didn't start the closing handshake yet.
        It can be useful in combination with :func:`~broadcast`.

        """
        return {
            connection
            for connection in self.all_connections
            if connection.protocol.state is OPEN
        }

    def close(
        self,
        close_connections: bool = True,
        code: CloseCode | int = CloseCode.GOING_AWAY,
        reason: str = "",
    ) -> None:
        """
        Close the server.

        * Close the underlying :class:`asyncio.Server`.
        * When ``close_connections`` is :obj:`True`, which is the default, close
          existing connections. Specifically:

          * Reject opening WebSocket connections with an HTTP 503 (service
            unavailable) error. This happens when the server accepted the TCP
            connection but didn't complete the opening handshake before closing.
          * Close open WebSocket connections with code 1001 (going away).
            ``code`` and ``reason`` can be customized, for example to use code
            1012 (service restart).

        * Wait until all connection handlers have returned.

        :meth:`close` is idempotent.

        """
        if self.close_task is None:
            self.close_task = self.get_loop().create_task(
                self._close(close_connections, code, reason)
            )

    async def _close(
        self,
        close_connections: bool = True,
        code: CloseCode | int = CloseCode.GOING_AWAY,
        reason: str = "",
    ) -> None:
        """
        Implementation of :meth:`close`.

        This calls :meth:`~asyncio.Server.close` on the underlying
        :class:`asyncio.Server` object to stop accepting new connections and
        then closes open connections.

        """
        self.logger.info("server closing")

        # Stop accepting new connections.
        # Also reject OPENING connections with HTTP 503 — see handshake().
        self.server.close()

        # Close OPEN connections.
        if close_connections:
            close_tasks = [
                asyncio.create_task(connection.close(code, reason))
                for connection in self.all_connections
                if connection.protocol.state is OPEN
            ]
            # asyncio.wait doesn't accept an empty first argument.
            if close_tasks:
                await asyncio.wait(close_tasks)

        # Wait until all TCP connections are closed.
        await self.server.wait_closed()

        # Wait until all connection handlers have returned.
        # asyncio.wait doesn't accept an empty first argument.
        if self.handler_tasks:
            await asyncio.wait(self.handler_tasks)

        # Tell wait_closed() to return.
        self.handlers_waiter.set_result(None)

        self.logger.info("server closed")

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """
        See :meth:`asyncio.Server.get_loop`.

        """
        return self.server.get_loop()

    async def start_serving(self) -> None:
        """
        See :meth:`asyncio.Server.start_serving`.

        Typical use::

            server = await serve(..., start_serving=False)
            # perform additional setup here...
            # ... then start the server
            await server.start_serving()

        """
        await self.server.start_serving()

    async def serve_forever(self) -> None:
        """
        See :meth:`asyncio.Server.serve_forever`.

        Typical use::

            server = await serve(...)
            # this coroutine doesn't return
            # canceling it stops the server
            await server.serve_forever()

        This is an alternative to using :func:`serve` as an asynchronous context
        manager. Shutdown is triggered by canceling :meth:`serve_forever` or by
        calling :meth:`~Server.close` from another task.

        """
        try:
            if not self.is_serving():
                await self.start_serving()
            # If close() is called, wait_closed() will return, and we'll exit.
            await self.wait_closed()
        except asyncio.CancelledError:
            try:
                self.close()
                await self.wait_closed()
            finally:
                raise

    def is_serving(self) -> bool:
        """
        See :meth:`asyncio.Server.is_serving`.

        """
        return self.server.is_serving()

    async def wait_closed(self) -> None:
        """
        Wait until the server is closed.

        When :meth:`wait_closed` returns, all TCP connections are closed and
        all connection handlers have returned.

        To ensure a fast shutdown, a connection handler should always be
        awaiting at least one of:

        * :meth:`~ServerConnection.recv`: when the connection is closed,
          it raises :exc:`~websockets.exceptions.ConnectionClosedOK`;
        * :meth:`~ServerConnection.wait_closed`: when the connection is
          closed, it returns.

        Then the connection handler is immediately notified of the shutdown;
        it can clean up and exit.

        """
        await asyncio.shield(self.handlers_waiter)

    @property
    def sockets(self) -> tuple[socket.socket, ...]:
        """
        See :attr:`asyncio.Server.sockets`.

        """
        return self.server.sockets

    async def _await(self) -> Self:
        if not hasattr(self, "server"):
            self.server = await self.create_server()
            if self.server.is_serving():
                for sock in self.server.sockets:
                    self.logger.info("server listening on %s", get_socket_name(sock))
        return self

    def __await__(self) -> Generator[Any, None, Self]:
        # Create a suitable iterator by calling __await__ on a coroutine.
        return self._await().__await__()

    async def __aenter__(self) -> Self:
        return await self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
        await self.wait_closed()


# serve() is declared as a function rather than a coroutine in order to support
# async with serve(...) as server: ... in addition to server = await serve(...).


def serve(
    handler: Callable[[ServerConnection], Awaitable[None]],
    host: str | None = None,
    port: int | None = None,
    *,
    # WebSocket
    origins: Sequence[Origin | re.Pattern[str] | None] | None = None,
    extensions: Sequence[ServerExtensionFactory] | None = None,
    subprotocols: Sequence[Subprotocol] | None = None,
    select_subprotocol: (
        Callable[
            [ServerConnection, Sequence[Subprotocol]],
            Subprotocol | None,
        ]
        | None
    ) = None,
    compression: str | None = "deflate",
    # HTTP
    process_request: (
        Callable[
            [ServerConnection, Request],
            Awaitable[Response | None] | Response | None,
        ]
        | None
    ) = None,
    process_response: (
        Callable[
            [ServerConnection, Request, Response],
            Awaitable[Response | None] | Response | None,
        ]
        | None
    ) = None,
    server_header: str | None = SERVER,
    # Timeouts
    open_timeout: float | None = 10,
    ping_interval: float | None = 20,
    ping_timeout: float | None = 20,
    close_timeout: float | None = 10,
    # Limits
    max_size: int | None | tuple[int | None, int | None] = 2**20,
    max_queue: int | None | tuple[int | None, int | None] = 16,
    write_limit: int | tuple[int, int | None] = 2**15,
    # Logging
    logger: LoggerLike | None = None,
    # Escape hatch for advanced customization
    create_connection: type[ServerConnection] | None = None,
    # Other keyword arguments are passed to loop.create_server
    **kwargs: Any,
) -> Server:
    """
    Create a WebSocket server listening on ``host`` and ``port``.

    Whenever a client connects, the server creates a :class:`ServerConnection`,
    performs the opening handshake, and delegates to the ``handler`` coroutine.

    The handler receives the :class:`ServerConnection` instance, which you can
    use to send and receive messages.

    Once the handler completes, either normally or with an exception, the server
    performs the closing handshake and closes the connection.

    This function returns a :class:`Server` object whose API mirrors
    :class:`asyncio.Server`. Treat it as an asynchronous context manager to
    serve requests and ensure that the server will be closed gracefully::

        from websockets.asyncio.server import serve

        async def handler(websocket):
            ...

        # set this event to exit the server
        stop = asyncio.Event()

        async with serve(handler, host, port):
            await stop.wait()

    Alternatively, await it and call :meth:`~Server.serve_forever` to serve
    requests, then cancel it or call :meth:`~Server.close` to stop the server::

        server = await serve(handler, host, port)
        await server.serve_forever()

    The following pattern is functional but redundant: by the time the context
    manager exits, :meth:`~Server.serve_forever` has already closed the server::

        async with serve(handler, host, port) as server:
            await server.serve_forever()

    Args:
        handler: Connection handler. It receives the WebSocket connection,
            which is a :class:`ServerConnection`, in argument.
        host: Network interfaces the server binds to.
            See :meth:`~asyncio.loop.create_server` for details.
        port: TCP port the server listens on.
            See :meth:`~asyncio.loop.create_server` for details.
        origins: Acceptable values of the ``Origin`` header, for defending
            against Cross-Site WebSocket Hijacking attacks. Values can be
            :class:`str` to test for an exact match or regular expressions
            compiled by :func:`re.compile` to test against a pattern. Include
            :obj:`None` in the list if the lack of an origin is acceptable.
        extensions: List of supported extensions, in order in which they
            should be negotiated and run.
        subprotocols: List of supported subprotocols, in order of decreasing
            preference.
        select_subprotocol: Callback for selecting a subprotocol among
            those supported by the client and the server. It receives a
            :class:`ServerConnection` (not a
            :class:`~websockets.server.ServerProtocol`!) instance and a list of
            subprotocols offered by the client. Other than the first argument,
            it has the same behavior as the
            :meth:`ServerProtocol.select_subprotocol
            <websockets.server.ServerProtocol.select_subprotocol>` method.
        compression: The "permessage-deflate" extension is enabled by default.
            Set ``compression`` to :obj:`None` to disable it. See the
            :doc:`compression guide <../../topics/compression>` for details.
        process_request: Intercept the request during the opening handshake.
            Return an HTTP response to force the response or :obj:`None` to
            continue normally. When you force an HTTP 101 Continue response, the
            handshake is successful. Else, the connection is aborted.
            ``process_request`` may be a function or a coroutine.
        process_response: Intercept the response during the opening handshake.
            Return an HTTP response to force the response or :obj:`None` to
            continue normally. When you force an HTTP 101 Continue response, the
            handshake is successful. Else, the connection is aborted.
            ``process_response`` may be a function or a coroutine.
        server_header: Value of  the ``Server`` response header.
            It defaults to ``"Python/x.y.z websockets/X.Y"``. Setting it to
            :obj:`None` removes the header.
        open_timeout: Timeout for opening connections in seconds.
            :obj:`None` disables the timeout.
        ping_interval: Interval between keepalive pings in seconds.
            :obj:`None` disables keepalive.
        ping_timeout: Timeout for keepalive pings in seconds.
            :obj:`None` disables timeouts.
        close_timeout: Timeout for closing connections in seconds.
            :obj:`None` disables the timeout.
        max_size: Maximum size of incoming messages in bytes.
            :obj:`None` disables the limit. You may pass a ``(max_message_size,
            max_fragment_size)`` tuple to set different limits for messages and
            fragments when you expect long messages sent in short fragments.
        max_queue: High-water mark of the buffer where frames are received.
            It defaults to 16 frames. The low-water mark defaults to ``max_queue
            // 4``. You may pass a ``(high, low)`` tuple to set the high-water
            and low-water marks. If you want to disable flow control entirely,
            you may set it to ``None``, although that's a bad idea.
        write_limit: High-water mark of write buffer in bytes. It is passed to
            :meth:`~asyncio.WriteTransport.set_write_buffer_limits`. It defaults
            to 32 KiB. You may pass a ``(high, low)`` tuple to set the
            high-water and low-water marks.
        logger: Logger for this server.
            It defaults to ``logging.getLogger("websockets.server")``.
            See the :doc:`logging guide <../../topics/logging>` for details.
        create_connection: Factory for the :class:`ServerConnection` managing
            the connection. Set it to a wrapper or a subclass to customize
            connection handling.

    Any other keyword arguments are passed to the event loop's
    :meth:`~asyncio.loop.create_server` method.

    For example:

    * You can set ``ssl`` to a :class:`~ssl.SSLContext` to enable TLS.

    * You can set ``sock`` to provide a preexisting TCP socket. You may call
      :func:`socket.create_server` (not to be confused with the event loop's
      :meth:`~asyncio.loop.create_server` method) to create a suitable server
      socket and customize it.

    * You can set ``start_serving`` to ``False`` to start accepting connections
      only after you call :meth:`~Server.start_serving()` or
      :meth:`~Server.serve_forever()`.

    """
    if subprotocols is not None:
        validate_subprotocols(subprotocols)

    if compression == "deflate":
        extensions = enable_server_permessage_deflate(extensions)
    elif compression is not None:
        raise ValueError(f"unsupported compression: {compression}")

    if create_connection is None:
        create_connection = ServerConnection

    if kwargs.get("ssl") is not None:
        kwargs.setdefault("ssl_handshake_timeout", open_timeout)
        kwargs.setdefault("ssl_shutdown_timeout", close_timeout)

    async def create_server() -> asyncio.Server:
        loop = asyncio.get_running_loop()
        if kwargs.pop("unix", False):
            return await loop.create_unix_server(protocol_factory, **kwargs)
        else:
            # mypy cannot tell that kwargs must provide sock when port is None.
            return await loop.create_server(protocol_factory, host, port, **kwargs)  # type: ignore[arg-type]

    def protocol_factory() -> ServerConnection:
        """
        Create an asyncio protocol for managing a WebSocket connection.

        """
        # Create a closure to give select_subprotocol access to connection.
        protocol_select_subprotocol: (
            Callable[
                [ServerProtocol, Sequence[Subprotocol]],
                Subprotocol | None,
            ]
            | None
        ) = None
        if select_subprotocol is not None:

            def protocol_select_subprotocol(
                protocol: ServerProtocol,
                subprotocols: Sequence[Subprotocol],
            ) -> Subprotocol | None:
                # mypy doesn't know that select_subprotocol is immutable.
                assert select_subprotocol is not None
                # Ensure this function is only used in the intended context.
                assert protocol is connection.protocol
                return select_subprotocol(connection, subprotocols)

        # This is a protocol in the Sans-I/O implementation of websockets.
        protocol = ServerProtocol(
            origins=origins,
            extensions=extensions,
            subprotocols=subprotocols,
            select_subprotocol=protocol_select_subprotocol,
            max_size=max_size,
            logger=logger,
        )
        # This is a connection in websockets and a protocol in asyncio.
        connection = create_connection(
            protocol,
            server,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            close_timeout=close_timeout,
            max_queue=max_queue,
            write_limit=write_limit,
        )
        return connection

    async def protocol_handler(connection: ServerConnection) -> None:
        """
        Handle the lifecycle of a WebSocket connection.

        Since this coroutine doesn't have a caller that can handle
        exceptions, it attempts to log relevant ones.

        It guarantees that the TCP connection is closed before exiting.

        """
        try:
            # Apply open_timeout to the WebSocket handshake.
            # Use ssl_handshake_timeout for the TLS handshake.
            async with asyncio.timeout(open_timeout):
                await connection.handshake(
                    process_request,
                    process_response,
                    server_header,
                )

            if connection.protocol.state is not OPEN:
                connection.transport.abort()
                return

            server.all_connections.add(connection)
            connection.start_keepalive()
            try:
                await handler(connection)
            except Exception:
                connection.logger.error("connection handler failed", exc_info=True)
                await connection.close(CloseCode.INTERNAL_ERROR)
            else:
                await connection.close()
            finally:
                server.all_connections.discard(connection)

        except Exception:
            # Don't leak connections when the opening handshake times out or
            # an unexpected error occurs.
            connection.transport.abort()

        finally:
            server.handler_tasks.discard(asyncio.current_task())

    # The server variable is captured by the closure of conn_handler() and
    # protocol_factory().
    server = Server(create_server, protocol_handler, logger)
    return server


def unix_serve(
    handler: Callable[[ServerConnection], Awaitable[None]],
    path: str | None = None,
    **kwargs: Any,
) -> Server:
    """
    Create a WebSocket server listening on a Unix socket.

    This function is identical to :func:`serve`, except the ``host`` and
    ``port`` arguments are replaced by ``path``. It's only available on Unix.

    It's useful for deploying a server behind a reverse proxy such as nginx.

    Args:
        handler: Connection handler. It receives the WebSocket connection,
            which is a :class:`ServerConnection`, in argument.
        path: File system path to the Unix socket.

    """
    return serve(handler, unix=True, path=path, **kwargs)


def is_credentials(credentials: Any) -> bool:
    try:
        username, password = credentials
    except (TypeError, ValueError):
        return False
    else:
        return isinstance(username, str) and isinstance(password, str)


def basic_auth(
    realm: str = "",
    credentials: tuple[str, str] | Iterable[tuple[str, str]] | None = None,
    check_credentials: Callable[[str, str], Awaitable[bool] | bool] | None = None,
) -> Callable[[ServerConnection, Request], Awaitable[Response | None]]:
    """
    Factory for ``process_request`` to enforce HTTP Basic Authentication.

    :func:`basic_auth` is designed to integrate with :func:`serve` as follows::

        from websockets.asyncio.server import basic_auth, serve

        async with serve(
            ...,
            process_request=basic_auth(
                realm="my dev server",
                credentials=("hello", "iloveyou"),
            ),
        ):

    If authentication succeeds, the connection's ``username`` attribute is set.
    If it fails, the server responds with an HTTP 401 Unauthorized status.

    One of ``credentials`` or ``check_credentials`` must be provided; not both.

    Args:
        realm: Scope of protection. It should contain only ASCII characters
            because the encoding of non-ASCII characters is undefined. Refer to
            section 2.2 of :rfc:`7235` for details.
        credentials: Hard coded authorized credentials. It can be a
            ``(username, password)`` pair or a list of such pairs.
        check_credentials: Function or coroutine that verifies credentials.
            It receives ``username`` and ``password`` arguments and returns
            whether they're valid.
    Raises:
        TypeError: If ``credentials`` or ``check_credentials`` is wrong.
        ValueError: If ``credentials`` and ``check_credentials`` are both
            provided or both not provided.

    """
    if (credentials is None) == (check_credentials is None):
        raise ValueError("provide either credentials or check_credentials")

    if credentials is not None:
        if is_credentials(credentials):
            credentials_list = [cast(tuple[str, str], credentials)]
        elif isinstance(credentials, Iterable):
            credentials_list = list(cast(Iterable[tuple[str, str]], credentials))
            if not all(is_credentials(item) for item in credentials_list):
                raise TypeError(f"invalid credentials argument: {credentials}")
        else:
            raise TypeError(f"invalid credentials argument: {credentials}")

        credentials_dict = dict(credentials_list)

        def check_credentials(username: str, password: str) -> bool:
            try:
                expected_password = credentials_dict[username]
            except KeyError:
                return False
            return hmac.compare_digest(expected_password, password)

    assert check_credentials is not None  # help mypy

    async def process_request(
        connection: ServerConnection,
        request: Request,
    ) -> Response | None:
        """
        Perform HTTP Basic Authentication.

        If it succeeds, set the connection's ``username`` attribute and return
        :obj:`None`. If it fails, return an HTTP 401 Unauthorized responss.

        """
        try:
            authorization = request.headers["Authorization"]
        except KeyError:
            response = connection.respond(
                http.HTTPStatus.UNAUTHORIZED,
                "Missing credentials\n",
            )
            response.headers["WWW-Authenticate"] = build_www_authenticate_basic(realm)
            return response

        try:
            username, password = parse_authorization_basic(authorization)
        except InvalidHeader:
            response = connection.respond(
                http.HTTPStatus.UNAUTHORIZED,
                "Unsupported credentials\n",
            )
            response.headers["WWW-Authenticate"] = build_www_authenticate_basic(realm)
            return response

        valid_credentials = check_credentials(username, password)
        if isinstance(valid_credentials, Awaitable):
            valid_credentials = await valid_credentials

        if not valid_credentials:
            response = connection.respond(
                http.HTTPStatus.UNAUTHORIZED,
                "Invalid credentials\n",
            )
            response.headers["WWW-Authenticate"] = build_www_authenticate_basic(realm)
            return response

        connection.username = username
        return None

    return process_request
