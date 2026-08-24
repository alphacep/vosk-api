from __future__ import annotations

import base64
import hashlib
import secrets
import socket
import sys

from .typing import BytesLike


__all__ = ["accept_key", "apply_mask", "get_socket_name"]


GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def generate_key() -> str:
    """
    Generate a random key for the Sec-WebSocket-Key header.

    """
    key = secrets.token_bytes(16)
    return base64.b64encode(key).decode()


def accept_key(key: str) -> str:
    """
    Compute the value of the Sec-WebSocket-Accept header.

    Args:
        key: Value of the Sec-WebSocket-Key header.

    """
    sha1 = hashlib.sha1((key + GUID).encode()).digest()
    return base64.b64encode(sha1).decode()


def apply_mask(data: BytesLike, mask: bytes | bytearray) -> bytes:
    """
    Apply masking to the data of a WebSocket message.

    Args:
        data: Data to mask.
        mask: 4-bytes mask.

    """
    if len(mask) != 4:
        raise ValueError("mask must contain 4 bytes")

    # Python 3.15+ requires C-contiguous buffers for int.from_bytes().
    if isinstance(data, memoryview) and not data.c_contiguous:
        data = bytes(data)

    data_int = int.from_bytes(data, sys.byteorder)
    mask_repeated = mask * (len(data) // 4) + mask[: len(data) % 4]
    mask_int = int.from_bytes(mask_repeated, sys.byteorder)
    return (data_int ^ mask_int).to_bytes(len(data), sys.byteorder)


def get_socket_name(sock: socket.socket) -> str:
    """
    Return a string representation of :meth:`~socket.socket.getsockname()`.

    """
    match sock.family:
        case socket.AF_INET:
            return "%s:%d" % sock.getsockname()
        case socket.AF_INET6:
            return "[%s]:%d" % sock.getsockname()[:2]
        case socket.AF_UNIX:
            return str(sock.getsockname())
        case _:  # pragma: no cover
            # Don't crash in case someone runs a WebSocket server
            # on a protocol other than IP or Unix domain sockets.
            raise AssertionError("unsupported socket family")
