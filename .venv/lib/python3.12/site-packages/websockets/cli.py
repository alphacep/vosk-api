from __future__ import annotations

import argparse
import asyncio
import itertools
import os
import ssl
import sys
import threading
from typing import Any, Callable

from .asyncio.client import ClientConnection, connect
from .exceptions import ConnectionClosed
from .frames import Close
from .version import version as websockets_version


__all__ = ["main"]

# Escape ASCII control characters (0-31 and 128-159) as well as DEL (127).
# Do not escape NO-BREAK SPACE (160) and SOFT HYPHEN (173), even if Python
# considers them non-printable, since they don't cause issues in terminal.

# >>> [i for i in range(256) if not any((
# ...     chr(i).isprintable(),
# ...     i < 32,
# ...     i == 127,
# ...     128 <= i < 160,
# ... ))]
# [160, 173]

TERMINAL_ESCAPES = str.maketrans(
    {i: repr(chr(i))[1:-1] for i in itertools.chain(range(32), range(127, 160))}
)


def escape(string: str) -> str:
    """Make a string safe for a terminal by escaping control characters."""
    return string.translate(TERMINAL_ESCAPES)


def print_during_input(string: str) -> None:
    sys.stdout.write(
        # Save cursor position
        "\N{ESC}7"
        # Add a new line
        "\N{LINE FEED}"
        # Move cursor up
        "\N{ESC}[A"
        # Insert blank line, scroll last line down
        "\N{ESC}[L"
        # Print string in the inserted blank line
        f"{string}\N{LINE FEED}"
        # Restore cursor position
        "\N{ESC}8"
        # Move cursor down
        "\N{ESC}[B"
    )
    sys.stdout.flush()


def print_over_input(string: str) -> None:
    sys.stdout.write(
        # Move cursor to beginning of line
        "\N{CARRIAGE RETURN}"
        # Delete current line
        "\N{ESC}[K"
        # Print string
        f"{string}\N{LINE FEED}"
    )
    sys.stdout.flush()


async def print_incoming_messages(websocket: ClientConnection) -> None:
    async for message in websocket:
        if isinstance(message, str):
            print_during_input("< " + escape(message))
        else:
            print_during_input("< (binary) " + message.hex())


def read_outgoing_messages(
    queue_for_sending: Callable[[str], None],
    notify_end_of_file: Callable[[], None],
) -> None:
    while True:
        sys.stdout.write("> ")
        sys.stdout.flush()
        line = sys.stdin.readline()
        if not line:
            notify_end_of_file()
            break
        message = line.rstrip("\r\n")
        queue_for_sending(message)


async def send_outgoing_messages(
    websocket: ClientConnection,
    messages: asyncio.Queue[str],
) -> None:
    while True:
        message = await messages.get()
        try:
            await websocket.send(message)
        except ConnectionClosed:  # pragma: no cover
            break


async def interactive_client(uri: str, **kwargs: Any) -> None:
    try:
        websocket = await connect(uri, **kwargs)
    except Exception as exc:
        print(f"Failed to connect to {uri}: {exc}.")
        sys.exit(1)
    else:
        print(f"Connected to {uri}.")

    # Read messages from stdin in a thread because Windows doesn't support
    # reading asynchronously (#1681), and a daemon thread to avoid blocking
    # Ctrl-C because signals are only delivered to the main thread.
    loop = asyncio.get_event_loop()
    messages: asyncio.Queue[str] = asyncio.Queue()
    # When dropping support for Python < 3.13, change notify_end_of_file() to
    # call messages.shutdown() and break when asyncio.QueueShutdownError is
    # raised in send_outgoing_messages().
    shutdown: asyncio.Future[None] = loop.create_future()

    def queue_for_sending(message: str) -> None:
        try:
            loop.call_soon_threadsafe(messages.put_nowait, message)
        except RuntimeError:  # Event loop is closed  # pragma: no cover
            pass

    def notify_end_of_file() -> None:
        try:
            loop.call_soon_threadsafe(shutdown.set_result, None)
        except RuntimeError:  # Event loop is closed  # pragma: no cover
            pass

    threading.Thread(
        target=read_outgoing_messages,
        args=(queue_for_sending, notify_end_of_file),
        daemon=True,
    ).start()

    incoming = asyncio.create_task(print_incoming_messages(websocket))
    outgoing = asyncio.create_task(send_outgoing_messages(websocket, messages))
    try:
        await asyncio.wait(
            [incoming, outgoing, shutdown],
            # Clean up and exit when the server closes the connection
            # or the user enters EOT (^D), whichever happens first.
            return_when=asyncio.FIRST_COMPLETED,
        )
    # asyncio.run() cancels the main task when the user triggers SIGINT (^C).
    # https://docs.python.org/3/library/asyncio-runner.html#handling-keyboard-interruption
    # Clean up and exit without re-raising CancelledError to prevent Python
    # from raising KeyboardInterrupt and displaying a stack track.
    except asyncio.CancelledError:  # pragma: no cover
        pass
    finally:
        incoming.cancel()
        outgoing.cancel()

    await websocket.close()
    assert websocket.close_code is not None and websocket.close_reason is not None
    close_status = Close(websocket.close_code, websocket.close_reason)
    print_over_input(f"Connection closed: {escape(str(close_status))}.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="websockets",
        description="Interactive WebSocket client.",
        add_help=False,
    )
    parser.add_argument(
        "--help",
        action="store_true",
        help="show usage and exit",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="disable TLS certificate verification",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="show version and exit",
    )
    parser.add_argument(
        "uri",
        metavar="<uri>",
        nargs="?",
    )
    args = parser.parse_args(argv)

    if args.help:
        parser.print_usage()
        sys.exit(0)

    if args.version:
        print(f"websockets {websockets_version}")
        sys.exit(0)

    if args.uri is None:
        parser.print_usage()
        sys.exit(2)

    # Enable VT100 to support ANSI escape codes in Command Prompt on Windows.
    # See https://github.com/python/cpython/issues/74261 for why this works.
    if sys.platform == "win32":
        os.system("")

    try:
        import readline  # noqa: F401
    except ImportError:  # readline isn't available on all platforms
        pass

    kwargs = {}
    if args.insecure and args.uri.startswith("wss://"):
        # This isn't a public API but it's mentioned in the changelog:
        # https://docs.python.org/3/whatsnew/3.4.html#changed-in-3-4-3
        kwargs["ssl"] = ssl._create_unverified_context()

    asyncio.run(interactive_client(args.uri, **kwargs))
