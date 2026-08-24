from __future__ import annotations

import functools
import http
import logging
import re
import ssl as ssl_module
from collections.abc import Awaitable, Mapping, Sequence
from types import TracebackType
from typing import Any, Callable, Coroutine, Self

import trio
import trio.abc

from ..asyncio.server import basic_auth
from ..extensions.base import ServerExtensionFactory
from ..extensions.permessage_deflate import enable_server_permessage_deflate
from ..frames import CloseCode
from ..headers import validate_subprotocols
from ..http11 import SERVER, Request, Response
from ..protocol import CONNECTING, OPEN, Event
from ..server import ServerProtocol
from ..typing import LoggerLike, Origin, StatusLike, Subprotocol
from ..utils import get_socket_name
from .connection import Connection, broadcast
from .utils import race_events


__all__ = [
    "broadcast",
    "serve",
    "ServerConnection",
    "Server",
    "basic_auth",
]


class ServerConnection(Connection):
    """
    :mod:`trio` implementation of a WebSocket server connection.

    :class:`ServerConnection` provides :meth:`recv` and :meth:`send` methods for
    receiving and sending messages.

    It supports asynchronous iteration to receive messages::

        async for message in websocket:
            await process(message)

    The iterator exits normally when the connection is closed with close code
    1000 (OK) or 1001 (going away) or without a close code. It raises a
    :exc:`~websockets.exceptions.ConnectionClosedError` when the connection is
    closed with any other code.

    The ``ping_interval``, ``ping_timeout``, ``close_timeout``, and
    ``max_queue`` arguments have the same meaning as in :func:`serve`.

    Args:
        nursery: Trio nursery.
        stream: Trio stream connected to a WebSocket client.
        protocol: Sans-I/O connection.
        server: Server that manages this connection.

    """

    def __init__(
        self,
        nursery: trio.Nursery,
        stream: trio.abc.Stream,
        protocol: ServerProtocol,
        server: Server,
        *,
        ping_interval: float | None = 20,
        ping_timeout: float | None = 20,
        close_timeout: float | None = 10,
        max_queue: int | None | tuple[int | None, int | None] = 16,
    ) -> None:
        self.protocol: ServerProtocol
        super().__init__(
            nursery,
            stream,
            protocol,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            close_timeout=close_timeout,
            max_queue=max_queue,
        )
        self.server = server
        self.request_rcvd: trio.Event = trio.Event()
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
        await race_events(self.request_rcvd, self.stream_closed)

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
                and self.server.closing
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
            self.request_rcvd.set()
        # Later events - frames.
        else:
            super().process_event(event)


class Server(trio.abc.AsyncResource):
    """
    WebSocket server returned by :func:`serve`.

    Args:
        listeners: List of Trio listeners accepting new connections.
        handler: Handler for one connection. It receives a Trio stream.
        logger: Logger for this server.
            It defaults to ``logging.getLogger("websockets.server")``.
            See the :doc:`logging guide <../../topics/logging>` for details.

    """

    def __init__(
        self,
        listeners: list[trio.SocketListener],
        handler: Callable[[trio.abc.Stream], Coroutine[Any, Any, None]],
        logger: LoggerLike | None = None,
    ) -> None:
        self.listeners = listeners
        self.handler = handler
        if logger is None:
            logger = logging.getLogger("websockets.server")
        self.logger = logger

        # Keep track of active connections.
        # Trio keeps track of connection handler tasks.
        self.all_connections: set[ServerConnection] = set()

        # Completed when all handlers are done.
        self.handlers_waiter = trio.Event()

        self.closing = False

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

    async def serve_forever(
        self,
        task_status: trio.TaskStatus[Server] = trio.TASK_STATUS_IGNORED,
    ) -> None:
        # Running handlers in a dedicated nursery makes it possible to close
        # listeners while handlers finish running. The nursery for listeners
        # is created in trio.serve_listeners().
        async with trio.open_nursery() as self.handler_nursery:
            # Wrap trio.serve_listeners() in another nursery to return the
            # Server object in task_status instead of a list of listeners.
            async with trio.open_nursery() as self.serve_nursery:
                await self.serve_nursery.start(
                    functools.partial(
                        trio.serve_listeners,
                        self.handler,
                        self.listeners,
                        handler_nursery=self.handler_nursery,
                    )
                )
                for listener in self.listeners:
                    self.logger.info(
                        "server listening on %s",
                        # listener.socket is a Trio socket, not a socket.socket,
                        # but it offers the same APIs used by get_socket_name().
                        get_socket_name(listener.socket),  # type: ignore
                    )
                task_status.started(self)
        # When the nursery for handlers has exited, all handlers have returned.
        self.handlers_waiter.set()

    # Shutting down the server cleanly when serve_forever() is canceled would be
    # the most idiomatic in Trio. However, that would require shielding too many
    # asynchronous operations, including the TLS & WebSocket opening handshakes.

    async def aclose(
        self,
        close_connections: bool = True,
        code: CloseCode | int = CloseCode.GOING_AWAY,
        reason: str = "",
    ) -> None:
        """
        Close the server.

        * Close the TCP listeners.
        * When ``close_connections`` is :obj:`True`, which is the default,
          close existing connections. Specifically:

          * Reject opening WebSocket connections with an HTTP 503 (service
            unavailable) error. This happens when the server accepted the TCP
            connection but didn't complete the opening handshake before closing.
          * Close open WebSocket connections with close code 1001 (going away).
            ``code`` and ``reason`` can be customized, for example to use code
            1012 (service restart).

        * Wait until all connection handlers have returned.

        :meth:`aclose` is idempotent.

        """
        self.logger.info("server closing")

        # Stop accepting new connections.
        self.serve_nursery.cancel_scope.cancel()

        # Reject OPENING connections with HTTP 503 — see handshake().
        self.closing = True

        # Close OPEN connections.
        if close_connections:
            for connection in self.all_connections:
                if connection.protocol.state is OPEN:  # pragma: no branch
                    self.handler_nursery.start_soon(connection.aclose, code, reason)

        # Wait until all connection handlers have returned.
        await self.handlers_waiter.wait()

        self.logger.info("server closed")

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()


async def serve(
    handler: Callable[[ServerConnection], Awaitable[None]],
    port: int | None = None,
    *,
    # TCP/TLS
    host: str | bytes | None = None,
    backlog: int | None = None,
    listeners: list[trio.SocketListener] | None = None,
    ssl: ssl_module.SSLContext | None = None,
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
    # Logging
    logger: LoggerLike | None = None,
    # Escape hatch for advanced customization
    create_connection: type[ServerConnection] | None = None,
    # Compatibility with trio.Nursery.start()
    task_status: trio.TaskStatus[Server] = trio.TASK_STATUS_IGNORED,
) -> None:
    """
    Create a WebSocket server listening on ``port``.

    Whenever a client connects, the server creates a :class:`ServerConnection`,
    performs the opening handshake, and delegates to the ``handler`` coroutine.

    The handler receives the :class:`ServerConnection` instance, which you can
    use to send and receive messages.

    Once the handler completes, either normally or with an exception, the server
    performs the closing handshake and closes the connection.

    When using :func:`serve` with :meth:`nursery.start <trio.Nursery.start>`,
    you get back a :class:`Server` object. Treat it as an asynchronous context
    manager to ensure that the server will be closed gracefully::

        from websockets.trio.server import serve

        async def handler(websocket):
            ...

        # set this event to exit the server
        stop = trio.Event()

        with trio.open_nursery() as nursery:
            server = await nursery.start(serve, handler, port)
            async with server:
                await stop.wait()

    Alternatively, to stop the server gracefully, call its
    :meth:`~Server.aclose` method::

        with trio.open_nursery() as nursery:
            server = await nursery.start(serve, handler, port)
            try:
                await stop.wait()
            finally:
                await server.aclose()

    Args:
        handler: Connection handler. It receives the WebSocket connection,
            which is a :class:`ServerConnection`, in argument.
        port: TCP port the server listens on.
            See :func:`~trio.open_tcp_listeners` for details.
        host: Network interfaces the server binds to.
            See :func:`~trio.open_tcp_listeners` for details.
        backlog: Listen backlog. See :func:`~trio.open_tcp_listeners` for
            details.
        listeners: Preexisting TCP listeners. ``listeners`` replaces ``port``,
            ``host``, and ``backlog``. See :func:`trio.serve_listeners` for
            details.
        ssl: Configuration for enabling TLS on the connection.
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
        logger: Logger for this server.
            It defaults to ``logging.getLogger("websockets.server")``.
            See the :doc:`logging guide <../../topics/logging>` for details.
        create_connection: Factory for the :class:`ServerConnection` managing
            the connection. Set it to a wrapper or a subclass to customize
            connection handling.
        task_status: For compatibility with :meth:`nursery.start
            <trio.Nursery.start>`.

    """

    # Process parameters

    if subprotocols is not None:
        validate_subprotocols(subprotocols)

    if compression == "deflate":
        extensions = enable_server_permessage_deflate(extensions)
    elif compression is not None:
        raise ValueError(f"unsupported compression: {compression}")

    if create_connection is None:
        create_connection = ServerConnection

    # Create listeners

    if listeners is None:
        if port is None:
            raise ValueError("port is required when listeners is not provided")
        listeners = await trio.open_tcp_listeners(port, host=host, backlog=backlog)
    else:
        if port is not None:
            raise ValueError("port is incompatible with listeners")
        if host is not None:
            raise ValueError("host is incompatible with listeners")
        if backlog is not None:
            raise ValueError("backlog is incompatible with listeners")

    async def stream_handler(stream: trio.abc.Stream) -> None:
        """
        Handle the lifecycle of a WebSocket connection.

        Since this coroutine doesn't have a caller that can handle
        exceptions, it attempts to log relevant ones.

        It guarantees that the TCP connection is closed before exiting.

        """
        async with trio.open_nursery() as nursery:
            try:
                # Apply open_timeout to the TLS and WebSocket handshake.
                with (
                    trio.CancelScope()
                    if open_timeout is None
                    else trio.fail_after(open_timeout)
                ):
                    # Enable TLS.
                    if ssl is not None:
                        # Wrap with SSLStream here rather than with TLSListener
                        # in order to include the TLS handshake within open_timeout.
                        stream = trio.SSLStream(
                            stream,
                            ssl,
                            server_side=True,
                            https_compatible=True,
                        )
                        assert isinstance(stream, trio.SSLStream)  # help mypy
                        try:
                            await stream.do_handshake()
                        except trio.BrokenResourceError:
                            return

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

                    # Initialize WebSocket protocol.
                    protocol = ServerProtocol(
                        origins=origins,
                        extensions=extensions,
                        subprotocols=subprotocols,
                        select_subprotocol=protocol_select_subprotocol,
                        max_size=max_size,
                        logger=logger,
                    )

                    # Initialize WebSocket connection.
                    connection = create_connection(
                        nursery,
                        stream,
                        protocol,
                        server,
                        ping_interval=ping_interval,
                        ping_timeout=ping_timeout,
                        close_timeout=close_timeout,
                        max_queue=max_queue,
                    )

                    await connection.handshake(
                        process_request,
                        process_response,
                        server_header,
                    )

                if connection.protocol.state is not OPEN:
                    await connection.close_stream()
                    return

                server.all_connections.add(connection)
                connection.start_keepalive()
                try:
                    await handler(connection)
                except Exception:
                    connection.logger.error("connection handler failed", exc_info=True)
                    await connection.aclose(CloseCode.INTERNAL_ERROR)
                else:
                    await connection.aclose()
                finally:
                    server.all_connections.discard(connection)

            except Exception:
                # Don't leak connections when the opening handshake times out or
                # an unexpected error occurs.
                await trio.aclose_forcefully(stream)

    # The server variable is captured by the closure of conn_handler().
    server = Server(listeners, stream_handler, logger)
    await server.serve_forever(task_status=task_status)
