from __future__ import annotations

import concurrent.futures
import hmac
import http
import logging
import re
import selectors
import socket
import ssl as ssl_module
import sys
import threading
import time
import warnings
from collections.abc import Iterable, Sequence
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
from .utils import Deadline


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
    :mod:`threading` implementation of a WebSocket server connection.

    :class:`ServerConnection` provides :meth:`recv` and :meth:`send` methods for
    receiving and sending messages.

    It supports iteration to receive messages::

        for message in websocket:
            process(message)

    The iterator exits normally when the connection is closed with code
    1000 (OK) or 1001 (going away) or without a close code. It raises a
    :exc:`~websockets.exceptions.ConnectionClosedError` when the connection is
    closed with any other code.

    The ``ping_interval``, ``ping_timeout``, ``close_timeout``, and
    ``max_queue`` arguments have the same meaning as in :func:`serve`.

    Args:
        socket: Socket connected to a WebSocket client.
        protocol: Sans-I/O connection.
        server: Server that manages this connection.

    """

    def __init__(
        self,
        sock: socket.socket,
        protocol: ServerProtocol,
        server: Server,
        *,
        ping_interval: float | None = 20,
        ping_timeout: float | None = 20,
        close_timeout: float | None = 10,
        max_queue: int | None | tuple[int | None, int | None] = 16,
    ) -> None:
        self.protocol: ServerProtocol
        self.request_rcvd = threading.Event()
        super().__init__(
            sock,
            protocol,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            close_timeout=close_timeout,
            max_queue=max_queue,
        )
        self.server = server
        self.username: str  # see basic_auth()
        self.handler: Callable[[ServerConnection], None]  # see route()
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

    def handshake(
        self,
        process_request: (
            Callable[
                [ServerConnection, Request],
                Response | None,
            ]
            | None
        ) = None,
        process_response: (
            Callable[
                [ServerConnection, Request, Response],
                Response | None,
            ]
            | None
        ) = None,
        server_header: str | None = SERVER,
        timeout: float | None = None,
    ) -> None:
        """
        Perform the opening handshake.

        """
        if not self.request_rcvd.wait(timeout):
            raise TimeoutError("timed out while waiting for handshake request")

        if self.request is not None:
            response = None

            if process_request is not None:
                try:
                    response = process_request(self, self.request)
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
                self.response = response

            if server_header is not None:
                self.response.headers["Server"] = server_header

            response = None

            if process_response is not None:
                try:
                    response = process_response(self, self.request, self.response)
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
                    self.response = response

            # Reject the connection if the server started closing during the
            # opening handshake. shutdown() runs a loop to catch cases where
            # the server shuts down between this check and send_response().
            if (
                self.response.status_code == http.HTTPStatus.SWITCHING_PROTOCOLS
                and self.server.socket_closed.is_set()
            ):
                self.response = self.protocol.reject(
                    http.HTTPStatus.SERVICE_UNAVAILABLE,
                    "Server is shutting down.\n",
                )

            # Don't respond if the connection was closed during the handshake.
            if self.state is CONNECTING:
                with self.send_context(expected_state=CONNECTING):
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

    def recv_events(self) -> None:
        """
        Read incoming data from the socket and process events.

        """
        try:
            super().recv_events()
        finally:
            # If the connection is closed during the handshake, unblock it.
            self.request_rcvd.set()


class Server:
    """
    WebSocket server returned by :func:`serve`.

    This class mirrors partially the API of :class:`~socketserver.BaseServer`.

    Args:
        socket: Server socket accepting new connections.
        handler: Handler for one connection. It receives the socket and address
            returned by :meth:`~socket.socket.accept`.
        logger: Logger for this server.
            It defaults to ``logging.getLogger("websockets.server")``.
            See the :doc:`logging guide <../../topics/logging>` for details.

    """

    SHUTDOWN_POLLING_INTERVAL = 0.1  # seconds

    def __init__(
        self,
        sock: socket.socket,
        handler: Callable[[socket.socket, Any], None],
        logger: LoggerLike | None = None,
    ) -> None:
        self.socket = sock
        self.handler = handler
        if logger is None:
            logger = logging.getLogger("websockets.server")
        self.logger = logger

        # Synchronize access to all_connections and handler_threads.
        self.lock = threading.Lock()

        # Keep track of active connections and connection handler threads.
        self.all_connections: set[ServerConnection] = set()
        self.handler_threads: set[threading.Thread] = set()

        # On Windows, closing the socket wakes up the poller in serve_forever(),
        # making the notification mechanism unnecessary.
        if sys.platform != "win32":
            self.shutdown_watcher, self.shutdown_notifier = socket.socketpair()

        # Set when serve_forever() no longer accepts new connections and starts
        # threads to handle them.
        self.socket_closed = threading.Event()

    @property
    def connections(self) -> set[ServerConnection]:
        """
        Set of active connections.

        This property contains all connections that completed the opening
        handshake successfully and didn't start the closing handshake yet.
        It can be useful in combination with :func:`~broadcast`.

        """
        with self.lock:
            return {
                connection
                for connection in self.all_connections
                if connection.protocol.state is OPEN
            }

    def serve_forever(self) -> None:
        """
        See :meth:`socketserver.BaseServer.serve_forever`.

        This method doesn't return. Calling :meth:`shutdown` from another thread
        stops the server.

        Typical use::

            with serve(...) as server:
                server.serve_forever()

        """
        poller = selectors.DefaultSelector()
        if sys.platform != "win32":
            poller.register(self.shutdown_watcher, selectors.EVENT_READ)

        try:
            try:
                poller.register(self.socket, selectors.EVENT_READ)
            except (OSError, ValueError):  # pragma: no cover
                # shutdown() was called before poller.register().
                # This may result in:
                # * OSError: [Errno 9] Bad file descriptor
                #   (only observed on free-threaded Python)
                # * ValueError: Invalid file descriptor: -1
                return

            self.logger.info("server listening on %s", get_socket_name(self.socket))

            while True:
                poller.select()
                try:
                    # If the socket is closed, this raises an exception and
                    # exits the loop; no need to check what select() returned.
                    sock, addr = self.socket.accept()
                except OSError:
                    break
                # shutdown() can let existing connections terminate on their own
                # or close them. Either way, it waits for connection handlers to
                # terminate, so there's no point using daemon threads.
                thread = threading.Thread(target=self.handler, args=(sock, addr))
                # The thread must be registered in self.handler_threads now,
                # before it's started. If it was registered in sock_handler(),
                # a race condition could happen when closing the server after
                # starting the thread but before it executes.
                with self.lock:
                    self.handler_threads.add(thread)
                thread.start()
        finally:
            self.socket_closed.set()
            if sys.platform != "win32":
                self.shutdown_watcher.close()

    def shutdown(
        self,
        close_connections: bool = True,
        code: CloseCode | int = CloseCode.GOING_AWAY,
        reason: str = "",
    ) -> None:
        """
        Close the server.

        * Close the listening socket to stop accepting new connections.
        * When ``close_connections`` is :obj:`True`, which is the default, close
          existing connections. Specifically:

          * Reject opening WebSocket connections with an HTTP 503 (service
            unavailable) error. This happens when the server accepted the TCP
            connection but didn't complete the opening handshake before closing.
          * Close open WebSocket connections with code 1001 (going away).
            ``code`` and ``reason`` can be customized, for example to use code
            1012 (service restart).

        * Wait until all connection handlers terminate.

        :meth:`shutdown` is idempotent.

        """
        self.logger.info("server closing")

        # Stop accepting new connections.
        self.socket.close()
        if sys.platform != "win32":
            try:
                self.shutdown_notifier.send(b"x")
            except OSError:
                pass  # shutdown() was already called
            finally:
                self.shutdown_notifier.close()

        # Wait until serve_forever() no longer accepts new connections nor
        # starts threads to handle them, meaning that self.handler_threads
        # won't get new entries.
        # Also reject OPENING connections with HTTP 503 — see handshake().
        self.socket_closed.wait()

        # Close OPEN connections.
        if close_connections:
            # At this point, all threads are started, but some may still be in
            # the opening handshake. Close open connections until no thread is
            # executing anymore. Some threads may be cleaning up; in that case
            # they're expected to terminate quickly, so waiting is fine.
            while True:
                with self.lock:
                    # Inline self.connections because it acquires self.lock,
                    # which isn't reentrant.
                    connections = [
                        connection
                        for connection in self.all_connections
                        if connection.protocol.state is OPEN
                    ]
                    threads = list(self.handler_threads)
                # No threads are executing anymore. Server is fully closed.
                if not threads:
                    break
                # Some threads are still executing, but no connections are OPEN.
                # Wait for connections to complete the opening handshake, or for
                # handler threads to terminate.
                if not connections:
                    time.sleep(self.SHUTDOWN_POLLING_INTERVAL)
                    continue
                # Close open connections and wait until they're closed.
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for connection in connections:
                        executor.submit(connection.close, code, reason)

        else:
            # At this point, all threads are started.
            with self.lock:
                threads = list(self.handler_threads)
            # Wait until all connection handlers terminate.
            for thread in threads:
                # This raises RuntimeError if shutdown() is called from a
                # connection handler. It's documented to return after all
                # connection handlers terminate, which is impossible when
                # it's called from a connection handler.
                thread.join()

        self.logger.info("server closed")

    def fileno(self) -> int:
        """
        See :meth:`socketserver.BaseServer.fileno`.

        """
        return self.socket.fileno()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.shutdown()


def __getattr__(name: str) -> Any:
    if name == "WebSocketServer":
        warnings.warn(  # deprecated in 13.0 - 2024-08-20
            "WebSocketServer was renamed to Server",
            DeprecationWarning,
        )
        return Server
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def serve(
    handler: Callable[[ServerConnection], None],
    host: str | None = None,
    port: int | None = None,
    *,
    # TCP/TLS
    sock: socket.socket | None = None,
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
            Response | None,
        ]
        | None
    ) = None,
    process_response: (
        Callable[
            [ServerConnection, Request, Response],
            Response | None,
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
    **kwargs: Any,
) -> Server:
    """
    Create a WebSocket server listening on ``host`` and ``port``.

    Whenever a client connects, the server creates a :class:`ServerConnection`,
    performs the opening handshake, and delegates to the ``handler`` function.

    The handler receives the :class:`ServerConnection` instance, which you can
    use to send and receive messages.

    Once the handler completes, either normally or with an exception, the server
    performs the closing handshake and closes the connection.

    This function returns a :class:`Server` object whose API mirrors
    :class:`~socketserver.BaseServer`. Treat it as a context manager to ensure
    that it will be closed gracefully and call :meth:`~Server.serve_forever` to
    serve requests::

        from websockets.sync.server import serve

        def handler(websocket):
            ...

        with serve(handler, ...) as server:
            server.serve_forever()

        To stop the server gracefully, call its :meth:`~Server.shutdown` method
        from another thread.

    Args:
        handler: Connection handler. It receives the WebSocket connection,
            which is a :class:`ServerConnection`, in argument.
        host: Network interfaces the server binds to.
            See :func:`~socket.create_server` for details.
        port: TCP port the server listens on.
            See :func:`~socket.create_server` for details.
        sock: Preexisting TCP socket. ``sock`` replaces ``host`` and ``port``.
            You may call :func:`socket.create_server` to create a suitable TCP
            socket.
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
            Return an HTTP response to force the response. Return :obj:`None` to
            continue normally. When you force an HTTP 101 Continue response, the
            handshake is successful. Else, the connection is aborted.
        process_response: Intercept the response during the opening handshake.
            Modify the response or return a new HTTP response to force the
            response. Return :obj:`None` to continue normally. When you force an
            HTTP 101 Continue response, the handshake is successful. Else, the
            connection is aborted.
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

    Any other keyword arguments are passed to :func:`~socket.create_server`.

    """

    # Process parameters

    # Backwards compatibility: ssl used to be called ssl_context.
    if ssl is None and "ssl_context" in kwargs:
        ssl = kwargs.pop("ssl_context")
        warnings.warn(  # deprecated in 13.0 - 2024-08-20
            "ssl_context was renamed to ssl",
            DeprecationWarning,
        )

    if subprotocols is not None:
        validate_subprotocols(subprotocols)

    if compression == "deflate":
        extensions = enable_server_permessage_deflate(extensions)
    elif compression is not None:
        raise ValueError(f"unsupported compression: {compression}")

    if create_connection is None:
        create_connection = ServerConnection

    # Bind socket and listen

    # Private APIs for unix_connect()
    unix: bool = kwargs.pop("unix", False)
    path: str | None = kwargs.pop("path", None)

    if sock is None:
        if unix:
            if path is None:
                raise ValueError("missing path argument")
            kwargs.setdefault("family", socket.AF_UNIX)
            sock = socket.create_server(path, **kwargs)
        else:
            sock = socket.create_server((host, port), **kwargs)
    else:
        if host is not None:
            raise ValueError("host is incompatible with sock")
        if port is not None:
            raise ValueError("port is incompatible with sock")
        if path is not None:
            raise ValueError("path is incompatible with sock")

    # Initialize TLS wrapper

    if ssl is not None:
        sock = ssl.wrap_socket(
            sock,
            server_side=True,
            # Delay TLS handshake until after we set a timeout on the socket.
            do_handshake_on_connect=False,
        )

    # Define request handler

    def sock_handler(sock: socket.socket, addr: Any) -> None:
        """
        Handle the lifecycle of a WebSocket connection.

        Since this function doesn't have a caller that can handle exceptions,
        it attempts to log relevant ones.

        It guarantees that the TCP connection is closed before exiting.

        """
        # Calculate timeouts on the TLS and WebSocket handshakes.
        # The TLS timeout must be set on the socket, then removed
        # to avoid conflicting with the WebSocket timeout in handshake().
        deadline = Deadline(open_timeout)

        try:
            # Disable Nagle algorithm

            if not unix:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)

            # Perform TLS handshake

            if ssl is not None:
                sock.settimeout(deadline.timeout())
                # mypy cannot figure this out
                assert isinstance(sock, ssl_module.SSLSocket)
                sock.do_handshake()
                sock.settimeout(None)

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

            # Initialize WebSocket protocol

            protocol = ServerProtocol(
                origins=origins,
                extensions=extensions,
                subprotocols=subprotocols,
                select_subprotocol=protocol_select_subprotocol,
                max_size=max_size,
                logger=logger,
            )

            # Initialize WebSocket connection

            assert create_connection is not None  # help mypy
            connection = create_connection(
                sock,
                protocol,
                server,
                ping_interval=ping_interval,
                ping_timeout=ping_timeout,
                close_timeout=close_timeout,
                max_queue=max_queue,
            )
        except Exception:
            try:
                sock.close()
                return
            finally:
                with server.lock:
                    server.handler_threads.discard(threading.current_thread())

        try:
            connection.handshake(
                process_request,
                process_response,
                server_header,
                deadline.timeout(),
            )

            if connection.protocol.state is not OPEN:
                connection.close_socket()
                return

            with server.lock:
                server.all_connections.add(connection)
            connection.start_keepalive()
            try:
                handler(connection)
            except Exception:
                connection.logger.error("connection handler failed", exc_info=True)
                connection.close(CloseCode.INTERNAL_ERROR)
            else:
                connection.close()
            finally:
                with server.lock:
                    server.all_connections.discard(connection)

        except Exception:
            # Don't leak sockets when the opening handshake times out or an
            # unexpected error occurs.
            connection.close_socket()

        finally:
            with server.lock:
                server.handler_threads.discard(threading.current_thread())

    # Initialize server

    # The server variable is captured by the closure of sock_handler().
    server = Server(sock, sock_handler, logger)
    return server


def unix_serve(
    handler: Callable[[ServerConnection], None],
    path: str | None = None,
    **kwargs: Any,
) -> Server:
    """
    Create a WebSocket server listening on a Unix socket.

    This function accepts the same keyword arguments as :func:`serve`.

    It's only available on Unix.

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
    check_credentials: Callable[[str, str], bool] | None = None,
) -> Callable[[ServerConnection, Request], Response | None]:
    """
    Factory for ``process_request`` to enforce HTTP Basic Authentication.

    :func:`basic_auth` is designed to integrate with :func:`serve` as follows::

        from websockets.sync.server import basic_auth, serve

        with serve(
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
        check_credentials: Function that verifies credentials.
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

    def process_request(
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

        if not check_credentials(username, password):
            response = connection.respond(
                http.HTTPStatus.UNAUTHORIZED,
                "Invalid credentials\n",
            )
            response.headers["WWW-Authenticate"] = build_www_authenticate_basic(realm)
            return response

        connection.username = username
        return None

    return process_request
