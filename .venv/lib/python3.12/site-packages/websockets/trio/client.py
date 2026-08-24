from __future__ import annotations

import logging
import os
import ssl as ssl_module
import traceback
import urllib.parse
from collections.abc import AsyncIterator, Generator, Sequence
from types import TracebackType
from typing import Any, Callable, Literal

import trio

from ..asyncio.client import process_exception
from ..client import ClientProtocol, backoff
from ..datastructures import Headers, HeadersLike
from ..exceptions import (
    InvalidProxyMessage,
    InvalidProxyStatus,
    InvalidStatus,
    ProxyError,
    SecurityError,
)
from ..extensions.base import ClientExtensionFactory
from ..extensions.permessage_deflate import enable_client_permessage_deflate
from ..headers import validate_subprotocols
from ..http11 import USER_AGENT, Response
from ..protocol import CONNECTING, Event
from ..proxy import Proxy, get_proxy, parse_proxy, prepare_connect_request
from ..streams import StreamReader
from ..typing import LoggerLike, Origin, Subprotocol
from ..uri import WebSocketURI, parse_uri
from .connection import Connection
from .utils import race_events


__all__ = ["connect", "unix_connect", "ClientConnection"]

MAX_REDIRECTS = int(os.environ.get("WEBSOCKETS_MAX_REDIRECTS", "10"))


class ClientConnection(Connection):
    """
    :mod:`trio` implementation of a WebSocket client connection.

    :class:`ClientConnection` provides :meth:`recv` and :meth:`send` coroutines
    for receiving and sending messages.

    It supports asynchronous iteration to receive messages::

        async for message in websocket:
            await process(message)

    The iterator exits normally when the connection is closed with close code
    1000 (OK) or 1001 (going away) or without a close code. It raises a
    :exc:`~websockets.exceptions.ConnectionClosedError` when the connection is
    closed with any other code.

    The ``ping_interval``, ``ping_timeout``, ``close_timeout``, and
    ``max_queue`` arguments have the same meaning as in :func:`connect`.

    Args:
        nursery: Trio nursery.
        stream: Trio stream connected to a WebSocket server.
        protocol: Sans-I/O connection.

    """

    def __init__(
        self,
        nursery: trio.Nursery,
        stream: trio.abc.Stream,
        protocol: ClientProtocol,
        *,
        ping_interval: float | None = 20,
        ping_timeout: float | None = 20,
        close_timeout: float | None = 10,
        max_queue: int | None | tuple[int | None, int | None] = 16,
    ) -> None:
        self.protocol: ClientProtocol
        super().__init__(
            nursery,
            stream,
            protocol,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            close_timeout=close_timeout,
            max_queue=max_queue,
        )
        self.response_rcvd = trio.Event()

    async def handshake(
        self,
        additional_headers: HeadersLike | None = None,
        user_agent_header: str | None = USER_AGENT,
    ) -> None:
        """
        Perform the opening handshake.

        """
        self.request = self.protocol.connect()
        if additional_headers is not None:
            self.request.headers.update(additional_headers)
        if user_agent_header is not None:
            self.request.headers.setdefault("User-Agent", user_agent_header)
        async with self.send_context(expected_state=CONNECTING):
            self.protocol.send_request(self.request)

        await race_events(self.response_rcvd, self.stream_closed)

        # self.protocol.handshake_exc is set when the connection is lost before
        # receiving a response, when the response cannot be parsed, or when the
        # response fails the handshake.

        if self.protocol.handshake_exc is not None:
            raise self.protocol.handshake_exc

    def process_event(self, event: Event) -> None:
        """
        Process one incoming event.

        """
        # First event - handshake response.
        if self.response is None:
            assert isinstance(event, Response)
            self.response = event
            self.response_rcvd.set()
        # Later events - frames.
        else:
            super().process_event(event)


# This is spelled in lower case because it's exposed as a callable in the API.
class connect:
    """
    Connect to the WebSocket server at ``uri``.

    This coroutine returns a :class:`ClientConnection` instance, which you can
    use to send and receive messages.

    :func:`connect` may be used as an asynchronous context manager::

        from websockets.trio.client import connect

        async with connect(...) as websocket:
            ...

    The connection is closed automatically when exiting the context.

    :func:`connect` can be used as an infinite asynchronous iterator to
    reconnect automatically on errors::

        async for websocket in connect(...):
            try:
                ...
            except websockets.exceptions.ConnectionClosed:
                continue

    If the connection fails with a transient error, it is retried with
    exponential backoff. If it fails with a fatal error, the exception is
    raised, breaking out of the loop.

    The connection is closed automatically after each iteration of the loop.

    Args:
        uri: URI of the WebSocket server.
        stream: Preexisting TCP stream. ``stream`` overrides the host and port
            from ``uri``. You may call :func:`~trio.open_tcp_stream` to create a
            suitable TCP stream.
        ssl: Configuration for enabling TLS on the connection.
        server_hostname: Host name for the TLS handshake. ``server_hostname``
            overrides the host name from ``uri``.
        origin: Value of the ``Origin`` header, for servers that require it.
        extensions: List of supported extensions, in order in which they
            should be negotiated and run.
        subprotocols: List of supported subprotocols, in order of decreasing
            preference.
        compression: The "permessage-deflate" extension is enabled by default.
            Set ``compression`` to :obj:`None` to disable it. See the
            :doc:`compression guide <../../topics/compression>` for details.
        additional_headers: Arbitrary HTTP headers to add to the handshake
            request.
        user_agent_header: Value of  the ``User-Agent`` request header.
            It defaults to ``"Python/x.y.z websockets/X.Y"``.
            Setting it to :obj:`None` removes the header.
        proxy: If a proxy is configured, it is used by default. Set ``proxy``
            to :obj:`None` to disable the proxy or to the address of a proxy
            to override the system configuration. See the :doc:`proxy docs
            <../../topics/proxies>` for details.
        proxy_ssl: Configuration for enabling TLS on the proxy connection.
        proxy_server_hostname: Host name for the TLS handshake with the proxy.
            ``proxy_server_hostname`` overrides the host name from ``proxy``.
        process_exception: When reconnecting automatically, tell whether an
            error is transient or fatal. The default behavior is defined by
            :func:`process_exception`. Refer to its documentation for details.
        open_timeout: Timeout for opening the connection in seconds.
            :obj:`None` disables the timeout.
        ping_interval: Interval between keepalive pings in seconds.
            :obj:`None` disables keepalive.
        ping_timeout: Timeout for keepalive pings in seconds.
            :obj:`None` disables timeouts.
        close_timeout: Timeout for closing the connection in seconds.
            :obj:`None` disables the timeout.
        reconnect_delays: Delays in seconds between reconnection attempts.
            Default is exponential backoff with 5s jitter, capped at 60s.
        max_size: Maximum size of incoming messages in bytes.
            :obj:`None` disables the limit. You may pass a ``(max_message_size,
            max_fragment_size)`` tuple to set different limits for messages and
            fragments when you expect long messages sent in short fragments.
        max_queue: High-water mark of the buffer where frames are received.
            It defaults to 16 frames. The low-water mark defaults to ``max_queue
            // 4``. You may pass a ``(high, low)`` tuple to set the high-water
            and low-water marks. If you want to disable flow control entirely,
            you may set it to ``None``, although that's a bad idea.
        logger: Logger for this client.
            It defaults to ``logging.getLogger("websockets.client")``.
            See the :doc:`logging guide <../../topics/logging>` for details.
        create_connection: Factory for the :class:`ClientConnection` managing
            the connection. Set it to a wrapper or a subclass to customize
            connection handling.

    Any other keyword arguments are passed to :func:`~trio.open_tcp_stream`.

    Raises:
        InvalidURI: If ``uri`` isn't a valid WebSocket URI.
        InvalidProxy: If ``proxy`` isn't a valid proxy.
        OSError: If the TCP connection fails.
        InvalidHandshake: If the opening handshake fails.
        TimeoutError: If the opening handshake times out.

    """

    # Arguments of type SSLContext don't render correctly in the documentation
    # because of https://github.com/sphinx-doc/sphinx/issues/13838.

    def __init__(
        self,
        uri: str,
        *,
        # TCP/TLS
        stream: trio.abc.Stream | None = None,
        ssl: ssl_module.SSLContext | None = None,
        server_hostname: str | None = None,
        # WebSocket
        origin: Origin | None = None,
        extensions: Sequence[ClientExtensionFactory] | None = None,
        subprotocols: Sequence[Subprotocol] | None = None,
        compression: str | None = "deflate",
        # HTTP
        additional_headers: HeadersLike | None = None,
        user_agent_header: str | None = USER_AGENT,
        proxy: str | Literal[True] | None = True,
        proxy_ssl: ssl_module.SSLContext | None = None,
        proxy_server_hostname: str | None = None,
        process_exception: Callable[[Exception], Exception | None] = process_exception,
        # Timeouts
        open_timeout: float | None = 10,
        ping_interval: float | None = 20,
        ping_timeout: float | None = 20,
        close_timeout: float | None = 10,
        reconnect_delays: Callable[[], Generator[float]] = backoff,
        # Limits
        max_size: int | None | tuple[int | None, int | None] = 2**20,
        max_queue: int | None | tuple[int | None, int | None] = 16,
        # Logging
        logger: LoggerLike | None = None,
        # Escape hatch for advanced customization
        create_connection: type[ClientConnection] | None = None,
        # Other keyword arguments are passed to trio.open_tcp_stream
        **kwargs: Any,
    ) -> None:
        self.uri = uri
        self.ws_uri = parse_uri(uri)
        if not self.ws_uri.secure and ssl is not None:
            raise ValueError("ssl argument is incompatible with a ws:// URI")

        if subprotocols is not None:
            validate_subprotocols(subprotocols)

        if compression == "deflate":
            extensions = enable_client_permessage_deflate(extensions)
        elif compression is not None:
            raise ValueError(f"unsupported compression: {compression}")

        if logger is None:
            logger = logging.getLogger("websockets.client")

        if create_connection is None:
            create_connection = ClientConnection

        self.stream = stream
        self.ssl = ssl
        self.server_hostname = server_hostname
        self.additional_headers = additional_headers
        self.user_agent_header = user_agent_header
        self.proxy = proxy
        self.proxy_ssl = proxy_ssl
        self.proxy_server_hostname = proxy_server_hostname
        self.process_exception = process_exception
        self.open_timeout = open_timeout
        self.reconnect_delays = reconnect_delays
        self.logger = logger
        self.create_connection = create_connection
        self.open_tcp_stream_kwargs = kwargs
        self.protocol_kwargs = dict(
            origin=origin,
            extensions=extensions,
            subprotocols=subprotocols,
            max_size=max_size,
            logger=logger,
        )
        self.connection_kwargs = dict(
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            close_timeout=close_timeout,
            max_queue=max_queue,
        )

    async def open_tcp_stream(self) -> trio.abc.Stream:
        """Open a TCP or Unix connection to the server, possibly through a proxy."""
        kwargs = self.open_tcp_stream_kwargs.copy()

        proxy = self.proxy
        if kwargs.get("unix", False):
            proxy = None
        if proxy is True:
            proxy = get_proxy(self.ws_uri)

        if kwargs.pop("unix", False):
            return await trio.open_unix_socket(kwargs["path"])

        elif proxy is not None:
            proxy_parsed = parse_proxy(proxy)

            if proxy_parsed.scheme[:5] == "socks":
                return await connect_socks_proxy(
                    proxy_parsed,
                    self.ws_uri,
                    # websockets is consistent with trio while python_socks is
                    # consistent across implementations.
                    local_addr=kwargs.pop("local_address", None),
                )

            elif proxy_parsed.scheme[:4] == "http":
                if proxy_parsed.scheme != "https" and self.proxy_ssl is not None:
                    raise ValueError(
                        "proxy_ssl argument is incompatible with an http:// proxy"
                    )
                return await connect_http_proxy(
                    proxy_parsed,
                    self.ws_uri,
                    user_agent_header=self.user_agent_header,
                    ssl=self.proxy_ssl,
                    server_hostname=self.proxy_server_hostname,
                    **kwargs,
                )

            else:
                raise AssertionError("parse_proxy returned unsupported proxy")

        else:  # proxy is None
            kwargs.setdefault("host", self.ws_uri.host)
            kwargs.setdefault("port", self.ws_uri.port)
            return await trio.open_tcp_stream(**kwargs)

    async def enable_tls(self, stream: trio.abc.Stream) -> trio.abc.Stream:
        """Enable TLS on the connection."""
        if self.ssl is None:
            ssl = ssl_module.create_default_context()
        else:
            ssl = self.ssl
        if self.server_hostname is None:
            server_hostname = self.ws_uri.host
        else:
            server_hostname = self.server_hostname
        ssl_stream = trio.SSLStream(
            stream,
            ssl,
            server_hostname=server_hostname,
            https_compatible=True,
        )
        await ssl_stream.do_handshake()
        return ssl_stream

    async def open_connection(self, nursery: trio.Nursery) -> ClientConnection:
        """Create a WebSocket connection."""
        # TCP connection is already established.
        if self.stream is None:
            stream = await self.open_tcp_stream()
        else:
            stream = self.stream

        try:
            if self.ws_uri.secure:
                stream = await self.enable_tls(stream)

            protocol = ClientProtocol(
                self.ws_uri,
                **self.protocol_kwargs,  # type: ignore
            )

            # self.create_connection defaults to ClientConnection.
            connection = self.create_connection(
                nursery,
                stream,
                protocol,
                **self.connection_kwargs,  # type: ignore
            )

            await connection.handshake(
                self.additional_headers,
                self.user_agent_header,
            )

            return connection

        except trio.Cancelled:
            await trio.aclose_forcefully(stream)
            # The nursery running this coroutine was canceled.
            # The next checkpoint raises trio.Cancelled.
            # aclose_forcefully() never returns.
            raise AssertionError("nursery should be canceled")
        except Exception:
            # Always close the connection even though keep-alive is the default
            # in HTTP/1.1 because the current implementation ties opening the
            # TCP/TLS connection with initializing the WebSocket protocol.
            await trio.aclose_forcefully(stream)
            raise

    def process_redirect(self, exc: Exception) -> Exception | str:
        """
        Determine whether a connection error is a redirect that can be followed.

        Return the new URI if it's a valid redirect. Else, return an exception.

        """
        if not (
            isinstance(exc, InvalidStatus)
            and exc.response.status_code
            in [
                300,  # Multiple Choices
                301,  # Moved Permanently
                302,  # Found
                303,  # See Other
                307,  # Temporary Redirect
                308,  # Permanent Redirect
            ]
            and "Location" in exc.response.headers
        ):
            return exc

        old_ws_uri = self.ws_uri
        new_uri = urllib.parse.urljoin(self.uri, exc.response.headers["Location"])
        new_ws_uri = parse_uri(new_uri)

        # If connect() received a stream, it is closed and cannot be reused.
        if self.stream is not None:
            return ValueError(
                f"cannot follow redirect to {new_uri} with a preexisting stream"
            )

        # TLS downgrade is forbidden.
        if old_ws_uri.secure and not new_ws_uri.secure:
            return SecurityError(f"cannot follow redirect to non-secure URI {new_uri}")

        # Apply restrictions to cross-origin redirects.
        if (
            old_ws_uri.secure != new_ws_uri.secure
            or old_ws_uri.host != new_ws_uri.host
            or old_ws_uri.port != new_ws_uri.port
        ):
            # Cross-origin redirects on Unix sockets don't quite make sense.
            if self.open_tcp_stream_kwargs.get("unix", False):
                return ValueError(
                    f"cannot follow cross-origin redirect to {new_uri} "
                    f"with a Unix socket"
                )
            # Cross-origin redirects when host and port are overridden are ill-defined.
            if (
                self.open_tcp_stream_kwargs.get("host") is not None
                or self.open_tcp_stream_kwargs.get("port") is not None
            ):
                return ValueError(
                    f"cannot follow cross-origin redirect to {new_uri} "
                    f"with an explicit host or port"
                )

            # Strip credentials to avoid leaking them to a different origin.
            if self.additional_headers is not None:
                self.additional_headers = Headers(
                    (
                        (key, value)
                        for key, value in Headers(self.additional_headers).raw_items()
                        if key.lower()
                        not in ["authorization", "cookie", "proxy-authorization"]
                    )
                )

        return new_uri

    async def connect(self, nursery: trio.Nursery) -> ClientConnection:
        try:
            with (
                trio.CancelScope()
                if self.open_timeout is None
                else trio.fail_after(self.open_timeout)
            ):
                for _ in range(MAX_REDIRECTS):
                    try:
                        connection = await self.open_connection(nursery)
                    except Exception as exc:
                        exc_or_uri = self.process_redirect(exc)
                        if isinstance(exc_or_uri, Exception):
                            # Response isn't a valid redirect; raise the exception.
                            if exc_or_uri is exc:
                                raise
                            else:
                                raise exc_or_uri from exc
                        else:
                            # Response is a valid redirect; follow it.
                            self.uri = exc_or_uri
                            self.ws_uri = parse_uri(exc_or_uri)
                            continue

                    else:
                        connection.start_keepalive()
                        return connection
                else:
                    raise SecurityError(f"more than {MAX_REDIRECTS} redirects")

        except trio.TooSlowError as exc:
            # Re-raise exception with an informative error message.
            raise TimeoutError("timed out during opening handshake") from exc

    # Do not define __await__ for... = await nursery.start(connect, ...)
    # because it doesn't look idiomatic in Trio.

    # async with connect(...) as ...: ...

    async def __aenter__(self) -> ClientConnection:
        await self.__aenter_nursery__()
        try:
            self.connection = await self.connect(self.nursery)
            return self.connection
        except BaseException as exc:
            await self.__aexit_nursery__(type(exc), exc, exc.__traceback__)
            raise AssertionError("expected __aexit_nursery__ to re-raise the exception")

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            try:
                await self.connection.aclose()
            finally:
                del self.connection
        finally:
            await self.__aexit_nursery__(exc_type, exc_value, traceback)

    async def __aenter_nursery__(self) -> None:
        if hasattr(self, "nursery_manager"):
            raise RuntimeError("connect() isn't reentrant")
        self.nursery_manager = trio.open_nursery()
        self.nursery = await self.nursery_manager.__aenter__()

    async def __aexit_nursery__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        # We need a nursery to start the recv_events and keepalive coroutines.
        # They aren't expected to raise exceptions; instead they catch and log
        # all unexpected errors. To keep the nursery an implementation detail,
        # unwrap exceptions raised by user code — per the second option here:
        # https://trio.readthedocs.io/en/stable/reference-core.html#designing-for-multiple-errors
        try:
            await self.nursery_manager.__aexit__(exc_type, exc_value, traceback)
        except BaseException as exc:
            assert isinstance(exc, BaseExceptionGroup)
            try:
                trio._util.raise_single_exception_from_group(exc)
            except trio._util.MultipleExceptionError:
                raise AssertionError(
                    "unexpected multiple exceptions; please file a bug report"
                ) from exc
        finally:
            del self.nursery_manager

    # async for ... in connect(...):

    async def __aiter__(self) -> AsyncIterator[ClientConnection]:
        delays: Generator[float] | None = None
        while True:
            try:
                async with self as connection:
                    yield connection
            except Exception as exc:
                # Determine whether the exception is retryable or fatal.
                # The API of process_exception is "return an exception or None";
                # "raise an exception" is also supported because it's a frequent
                # mistake. It isn't documented in order to keep the API simple.
                try:
                    new_exc = self.process_exception(exc)
                except Exception as raised_exc:
                    new_exc = raised_exc

                # The connection failed with a fatal error.
                # Raise the exception and exit the loop.
                if new_exc is exc:
                    raise
                if new_exc is not None:
                    raise new_exc from exc

                # The connection failed with a retryable error.
                # Start or continue backoff and reconnect.
                if delays is None:
                    delays = self.reconnect_delays()
                delay = next(delays)
                self.logger.info(
                    "connect failed; reconnecting in %.1f seconds: %s",
                    delay,
                    traceback.format_exception_only(exc)[0].strip(),
                )
                await trio.sleep(delay)

            else:
                # The connection succeeded. Reset backoff.
                delays = None


def unix_connect(
    path: str | None = None,
    uri: str | None = None,
    **kwargs: Any,
) -> connect:
    """
    Connect to a WebSocket server listening on a Unix socket.

    This function accepts the same keyword arguments as :func:`connect`.

    It's only available on Unix.

    It's mainly useful for debugging servers listening on Unix sockets.

    Args:
        path: File system path to the Unix socket.
        uri: URI of the WebSocket server. ``uri`` defaults to
            ``ws://localhost/`` or, when a ``ssl`` argument is provided, to
            ``wss://localhost/``.

    """
    if uri is None:
        if kwargs.get("ssl") is None:
            uri = "ws://localhost/"
        else:
            uri = "wss://localhost/"
    return connect(uri=uri, unix=True, path=path, **kwargs)


try:
    from python_socks import ProxyType
    from python_socks.async_.trio import Proxy as SocksProxy

except ImportError:

    async def connect_socks_proxy(
        proxy: Proxy,
        ws_uri: WebSocketURI,
        **kwargs: Any,
    ) -> trio.abc.Stream:
        raise ImportError("connecting through a SOCKS proxy requires python-socks")

else:
    SOCKS_PROXY_TYPES = {
        "socks5h": ProxyType.SOCKS5,
        "socks5": ProxyType.SOCKS5,
        "socks4a": ProxyType.SOCKS4,
        "socks4": ProxyType.SOCKS4,
    }

    SOCKS_PROXY_RDNS = {
        "socks5h": True,
        "socks5": False,
        "socks4a": True,
        "socks4": False,
    }

    async def connect_socks_proxy(
        proxy: Proxy,
        ws_uri: WebSocketURI,
        **kwargs: Any,
    ) -> trio.abc.Stream:
        """Connect via a SOCKS proxy and return the socket."""
        socks_proxy = SocksProxy(
            SOCKS_PROXY_TYPES[proxy.scheme],
            proxy.host,
            proxy.port,
            proxy.username,
            proxy.password,
            SOCKS_PROXY_RDNS[proxy.scheme],
        )
        # connect() is documented to raise OSError.
        # socks_proxy.connect() re-raises trio.TooSlowError as ProxyTimeoutError.
        # Wrap other exceptions in ProxyError, a subclass of InvalidHandshake.
        try:
            return trio.SocketStream(
                await socks_proxy.connect(ws_uri.host, ws_uri.port, **kwargs)
            )
        except OSError:
            raise
        except Exception as exc:
            raise ProxyError("failed to connect to SOCKS proxy") from exc


async def read_connect_response(stream: trio.abc.Stream) -> Response:
    reader = StreamReader()
    parser = Response.parse(
        reader.read_line,
        reader.read_exact,
        reader.read_to_eof,
        proxy=True,
    )
    try:
        while True:
            data = await stream.receive_some(4096)
            if data:
                reader.feed_data(data)
            else:
                reader.feed_eof()
            next(parser)
    except StopIteration as exc:
        assert isinstance(exc.value, Response)  # help mypy
        response = exc.value
        if 200 <= response.status_code < 300:
            return response
        else:
            raise InvalidProxyStatus(response)
    except Exception as exc:
        raise InvalidProxyMessage(
            "did not receive a valid HTTP response from proxy"
        ) from exc


async def connect_http_proxy(
    proxy: Proxy,
    ws_uri: WebSocketURI,
    *,
    user_agent_header: str | None = None,
    ssl: ssl_module.SSLContext | None = None,
    server_hostname: str | None = None,
    **kwargs: Any,
) -> trio.abc.Stream:
    stream: trio.abc.Stream
    stream = await trio.open_tcp_stream(proxy.host, proxy.port, **kwargs)

    try:
        # Initialize TLS wrapper and perform TLS handshake
        if proxy.scheme == "https":
            if ssl is None:
                ssl = ssl_module.create_default_context()
            if server_hostname is None:
                server_hostname = proxy.host
            ssl_stream = trio.SSLStream(
                stream,
                ssl,
                server_hostname=server_hostname,
                https_compatible=True,
            )
            await ssl_stream.do_handshake()
            stream = ssl_stream

        # Send CONNECT request to the proxy and read response.
        request = prepare_connect_request(proxy, ws_uri, user_agent_header)
        await stream.send_all(request)
        await read_connect_response(stream)

    except (trio.Cancelled, Exception):
        await trio.aclose_forcefully(stream)
        raise

    return stream
