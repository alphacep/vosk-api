from __future__ import annotations

import dataclasses
import enum
import io
import os
import secrets
import struct
from collections.abc import Generator, Sequence
from typing import Callable, Self

from .exceptions import PayloadTooBig, ProtocolError
from .typing import BytesLike


try:
    from .speedups import apply_mask
except ImportError:
    from .utils import apply_mask


__all__ = [
    "Opcode",
    "CloseCode",
    "Frame",
    "Close",
]


class Opcode(enum.IntEnum):
    """Opcode values for WebSocket frames."""

    CONT, TEXT, BINARY = 0x00, 0x01, 0x02
    CLOSE, PING, PONG = 0x08, 0x09, 0x0A


CONT = Opcode.CONT
TEXT = Opcode.TEXT
BINARY = Opcode.BINARY
CLOSE = Opcode.CLOSE
PING = Opcode.PING
PONG = Opcode.PONG

DATA_OPCODES = CONT, TEXT, BINARY
CTRL_OPCODES = CLOSE, PING, PONG


class CloseCode(enum.IntEnum):
    """Close code values for WebSocket close frames."""

    NORMAL_CLOSURE = 1000
    GOING_AWAY = 1001
    PROTOCOL_ERROR = 1002
    UNSUPPORTED_DATA = 1003
    # 1004 is reserved
    NO_STATUS_RCVD = 1005
    ABNORMAL_CLOSURE = 1006
    INVALID_DATA = 1007
    POLICY_VIOLATION = 1008
    MESSAGE_TOO_BIG = 1009
    MANDATORY_EXTENSION = 1010
    INTERNAL_ERROR = 1011
    SERVICE_RESTART = 1012
    TRY_AGAIN_LATER = 1013
    BAD_GATEWAY = 1014
    TLS_HANDSHAKE = 1015


# See https://www.iana.org/assignments/websocket/websocket.xhtml
CLOSE_CODE_EXPLANATIONS: dict[int, str] = {
    CloseCode.NORMAL_CLOSURE: "OK",
    CloseCode.GOING_AWAY: "going away",
    CloseCode.PROTOCOL_ERROR: "protocol error",
    CloseCode.UNSUPPORTED_DATA: "unsupported data",
    CloseCode.NO_STATUS_RCVD: "no status received [internal]",
    CloseCode.ABNORMAL_CLOSURE: "abnormal closure [internal]",
    CloseCode.INVALID_DATA: "invalid frame payload data",
    CloseCode.POLICY_VIOLATION: "policy violation",
    CloseCode.MESSAGE_TOO_BIG: "message too big",
    CloseCode.MANDATORY_EXTENSION: "mandatory extension",
    CloseCode.INTERNAL_ERROR: "internal error",
    CloseCode.SERVICE_RESTART: "service restart",
    CloseCode.TRY_AGAIN_LATER: "try again later",
    CloseCode.BAD_GATEWAY: "bad gateway",
    CloseCode.TLS_HANDSHAKE: "TLS handshake failure [internal]",
}


# Close code that are allowed in a close frame.
# Using a set optimizes `code in EXTERNAL_CLOSE_CODES`.
EXTERNAL_CLOSE_CODES = {
    CloseCode.NORMAL_CLOSURE,
    CloseCode.GOING_AWAY,
    CloseCode.PROTOCOL_ERROR,
    CloseCode.UNSUPPORTED_DATA,
    CloseCode.INVALID_DATA,
    CloseCode.POLICY_VIOLATION,
    CloseCode.MESSAGE_TOO_BIG,
    CloseCode.MANDATORY_EXTENSION,
    CloseCode.INTERNAL_ERROR,
    CloseCode.SERVICE_RESTART,
    CloseCode.TRY_AGAIN_LATER,
    CloseCode.BAD_GATEWAY,
}


OK_CLOSE_CODES = {
    CloseCode.NORMAL_CLOSURE,
    CloseCode.GOING_AWAY,
    CloseCode.NO_STATUS_RCVD,
}


@dataclasses.dataclass
class Frame:
    """
    WebSocket frame.

    Attributes:
        opcode: Opcode.
        data: Payload data.
        fin: FIN bit.
        rsv1: RSV1 bit.
        rsv2: RSV2 bit.
        rsv3: RSV3 bit.

    Only these fields are needed. The MASK bit, payload length and masking-key
    are handled on the fly when parsing and serializing frames.

    """

    opcode: Opcode
    data: BytesLike
    fin: bool = True
    rsv1: bool = False
    rsv2: bool = False
    rsv3: bool = False

    # Configure if you want to see more in logs. Should be a multiple of 3.
    MAX_LOG_SIZE = int(os.environ.get("WEBSOCKETS_MAX_LOG_SIZE", "75"))

    DEFAULT_IS_TEXT = {TEXT: True, BINARY: False, CLOSE: True}

    def __str__(self) -> str:
        """
        Return a human-readable representation of a frame.

        This function is intended for logging and debugging. It doesn't aim to
        support round-tripping because payloads can be too long for displaying
        conveniently. Instead, it shows the beginning and the end. It's robust
        to incorrect data.

        It attempts to decode UTF-8 payloads whenever possible, even for binary
        frames and control frames, because those frequently contain UTF-8 data.
        It applies the same logic to continuation frames, because we don't know
        if they continue a text frame or a binary frame.

        """
        expect_text = self.DEFAULT_IS_TEXT.get(self.opcode)
        data_repr, is_text = self._data_repr()

        data_type = "" if expect_text == is_text else ("text" if is_text else "binary")
        length = f"{len(self.data)} byte{'' if len(self.data) == 1 else 's'}"
        non_final = "" if self.fin else "continued"
        metadata = ", ".join(filter(None, [data_type, length, non_final]))

        return f"{self.opcode.name} {data_repr} [{metadata}]"

    def _data_repr(self) -> tuple[str, bool | None]:
        """
        Return a human-readable representation of the payload.

        Also returns whether the payload is text.

        The representation is elided to fit ``MAX_LOG_SIZE``.

        This is a helper for the __str__ method.

        """
        if not self.data:
            return "''", self.DEFAULT_IS_TEXT.get(self.opcode)

        # Special case for close frames: parse close code and reason.
        # Fall back to the standard case if the payload is malformed.

        if self.opcode is CLOSE:
            try:
                return str(Close.parse(self.data)), True
            except (ProtocolError, UnicodeDecodeError):
                pass

        # Guess whether the payload is UTF-8 or binary, regardless of opcode, to
        # display UTF-8 text in binary frames nicely and generally to be helpful
        # and robust. Also support frames fragmented within UTF-8 sequences.

        if len(self.data) > 4 * self.MAX_LOG_SIZE:
            # Process only the start and the end, as the middle will be elided.
            # Cast to bytes because self.data could be a memoryview.
            data_start = bytes(self.data[: 8 * self.MAX_LOG_SIZE // 3])
            data_end = bytes(self.data[-4 * self.MAX_LOG_SIZE // 3 :])
            is_text = is_utf8_fragment(
                data_start,
                must_start_clean=self.opcode != CONT,
            ) and is_utf8_fragment(
                data_end,
                must_end_clean=self.fin,
            )
            if is_text:
                data_repr = repr((data_start + data_end).decode(errors="replace"))

        else:
            # Cast to bytes because self.data could be a memoryview.
            data = bytes(self.data)
            is_text = is_utf8_fragment(
                data,
                must_start_clean=self.opcode != CONT,
                must_end_clean=self.fin,
            )
            if is_text:
                data_repr = repr(data.decode(errors="replace"))

        # When the payload is text (except perhaps for boundaries), we decoded
        # enough in ``data_repr``. Now, do the same when the payload is binary.

        if not is_text:
            binary = self.data
            if len(binary) > self.MAX_LOG_SIZE // 3:
                cut = (self.MAX_LOG_SIZE // 3 - 1) // 3  # by default cut = 8
                # Encode two dummy bytes to force eliding and adding an ellipsis.
                binary = b"".join([binary[: 2 * cut], b"\x00\x00", binary[-cut:]])
            data_repr = " ".join(f"{byte:02x}" for byte in binary)

        # Elide the middle of the representation to fit the maximum log size.

        if len(data_repr) > self.MAX_LOG_SIZE:
            cut = self.MAX_LOG_SIZE // 3 - 1  # by default cut = 24
            data_repr = data_repr[: 2 * cut] + "..." + data_repr[-cut:]

        return data_repr, is_text

    @classmethod
    def parse(
        cls,
        read_exact: Callable[[int], Generator[None, None, bytes | bytearray]],
        *,
        mask: bool,
        max_size: int | None = None,
        extensions: Sequence[extensions.Extension] | None = None,
    ) -> Generator[None, None, Frame]:
        """
        Parse a WebSocket frame.

        This is a generator-based coroutine.

        Args:
            read_exact: Generator-based coroutine that reads the requested
                bytes or raises an exception if there isn't enough data.
            mask: Whether the frame should be masked i.e. whether the read
                happens on the server side.
            max_size: Maximum payload size in bytes.
            extensions: List of extensions, applied in reverse order.

        Raises:
            EOFError: If the connection is closed without a full WebSocket frame.
            PayloadTooBig: If the frame's payload size exceeds ``max_size``.
            ProtocolError: If the frame contains incorrect values.

        """
        # Read the header.
        data = yield from read_exact(2)
        head1, head2 = struct.unpack("!BB", data)

        # While not Pythonic, this is marginally faster than calling bool().
        fin = True if head1 & 0b10000000 else False
        rsv1 = True if head1 & 0b01000000 else False
        rsv2 = True if head1 & 0b00100000 else False
        rsv3 = True if head1 & 0b00010000 else False

        try:
            opcode = Opcode(head1 & 0b00001111)
        except ValueError as exc:
            raise ProtocolError("invalid opcode") from exc

        if (True if head2 & 0b10000000 else False) != mask:
            raise ProtocolError("incorrect masking")

        length = head2 & 0b01111111
        if length == 126:
            data = yield from read_exact(2)
            (length,) = struct.unpack("!H", data)
        elif length == 127:
            data = yield from read_exact(8)
            (length,) = struct.unpack("!Q", data)
        if max_size is not None and length > max_size:
            raise PayloadTooBig(length, max_size)
        if mask:
            mask_bytes = yield from read_exact(4)

        # Read the data.
        data = yield from read_exact(length)
        if mask:
            data = apply_mask(data, mask_bytes)

        frame = cls(opcode, data, fin, rsv1, rsv2, rsv3)

        if extensions is None:
            extensions = []
        for extension in reversed(extensions):
            frame = extension.decode(frame, max_size=max_size)

        frame.check()

        return frame

    def serialize(
        self,
        *,
        mask: bool,
        extensions: Sequence[extensions.Extension] | None = None,
    ) -> bytes:
        """
        Serialize a WebSocket frame.

        Args:
            mask: Whether the frame should be masked i.e. whether the write
                happens on the client side.
            extensions: List of extensions, applied in order.

        Raises:
            ProtocolError: If the frame contains incorrect values.

        """
        self.check()

        if extensions is None:
            extensions = []
        for extension in extensions:
            self = extension.encode(self)

        output = io.BytesIO()

        # Prepare the header.
        head1 = (
            (0b10000000 if self.fin else 0)
            | (0b01000000 if self.rsv1 else 0)
            | (0b00100000 if self.rsv2 else 0)
            | (0b00010000 if self.rsv3 else 0)
            | self.opcode
        )

        head2 = 0b10000000 if mask else 0

        length = len(self.data)
        if length < 126:
            output.write(struct.pack("!BB", head1, head2 | length))
        elif length < 65536:
            output.write(struct.pack("!BBH", head1, head2 | 126, length))
        else:
            output.write(struct.pack("!BBQ", head1, head2 | 127, length))

        if mask:
            mask_bytes = secrets.token_bytes(4)
            output.write(mask_bytes)

        # Prepare the data.
        data: BytesLike
        if mask:
            data = apply_mask(self.data, mask_bytes)
        else:
            data = self.data
        output.write(data)

        return output.getvalue()

    def check(self) -> None:
        """
        Check that reserved bits and opcode have acceptable values.

        Raises:
            ProtocolError: If a reserved bit or the opcode is invalid.

        """
        if self.rsv1 or self.rsv2 or self.rsv3:
            raise ProtocolError("reserved bits must be 0")

        if self.opcode in CTRL_OPCODES:
            if len(self.data) > 125:
                raise ProtocolError("control frame too long")
            if not self.fin:
                raise ProtocolError("fragmented control frame")


@dataclasses.dataclass
class Close:
    """
    Code and reason for WebSocket close frames.

    Attributes:
        code: Close code.
        reason: Close reason.

    """

    code: CloseCode | int
    reason: str

    def __str__(self) -> str:
        """
        Return a human-readable representation of a close code and reason.

        """
        if 3000 <= self.code < 4000:
            explanation = "registered"
        elif 4000 <= self.code < 5000:
            explanation = "private use"
        else:
            explanation = CLOSE_CODE_EXPLANATIONS.get(self.code, "unknown")
        result = f"{self.code} ({explanation})"

        if self.reason:
            result = f"{result} {self.reason}"

        return result

    @classmethod
    def parse(cls, data: BytesLike) -> Self:
        """
        Parse the payload of a close frame.

        Args:
            data: Payload of the close frame.

        Raises:
            ProtocolError: If data is ill-formed.
            UnicodeDecodeError: If the reason isn't valid UTF-8.

        """
        if isinstance(data, memoryview):
            raise AssertionError("only compressed outgoing frames use memoryview")
        if len(data) >= 2:
            (code,) = struct.unpack("!H", data[:2])
            reason = data[2:].decode()
            close = cls(code, reason)
            close.check()
            return close
        elif len(data) == 0:
            return cls(CloseCode.NO_STATUS_RCVD, "")
        else:
            raise ProtocolError("close frame too short")

    def serialize(self) -> bytes:
        """
        Serialize the payload of a close frame.

        """
        self.check()
        return struct.pack("!H", self.code) + self.reason.encode()

    def check(self) -> None:
        """
        Check that the close code has a valid value for a close frame.

        Raises:
            ProtocolError: If the close code is invalid.

        """
        if not (self.code in EXTERNAL_CLOSE_CODES or 3000 <= self.code < 5000):
            raise ProtocolError("invalid status code")


def is_utf8_fragment(
    data: bytes,
    must_start_clean: bool = False,
    must_end_clean: bool = False,
) -> bool:
    """Guess if data is a fragment of UTF-8 text."""
    # Possible byte sequences for UTF-8 characters are:
    # 0xxxxxxx
    # 110xxxxx 10xxxxxx
    # 1110xxxx 10xxxxxx 10xxxxxx
    # 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx

    # The algorithm determines ``start`` and ``end`` so that ``data[start:end]``
    # must be a valid UTF-8 sequence for data to be a valid UTF-8 fragment.

    start, end = 0, len(data)

    if not must_start_clean:
        # Remove continuation bytes from the beginning.
        max_start = min(3, len(data))
        while start < max_start:
            byte = data[start]

            # Continuation byte
            if byte & 0b11000000 == 0b10000000:
                start += 1
                continue

            break

    if not must_end_clean:
        # Remove a partial multibyte sequence from the end.
        end -= 1  # index of the last byte
        min_end = max(len(data) - 4, start)
        while end >= min_end:
            byte = data[end]
            # Continuation byte
            if byte & 0b11000000 == 0b10000000:
                end -= 1
                continue

            # ASCII byte
            if byte & 0b10000000 == 0b00000000:
                seq_len = 1
            # Leading byte of a 2-byte sequence
            elif byte & 0b11100000 == 0b11000000:
                seq_len = 2
            # Leading byte of a 3-byte sequence
            elif byte & 0b11110000 == 0b11100000:
                seq_len = 3
            # Leading byte of a 4-byte sequence
            elif byte & 0b11111000 == 0b11110000:
                seq_len = 4
            # Invalid byte
            else:
                seq_len = 0

            # Cut only when there's an incomplete sequence at the end.
            if seq_len <= len(data) - end:
                end = len(data)

            break

    try:
        text = data[start:end].decode()
    except UnicodeDecodeError:
        return False
    else:
        # Non-printable characters signal binary data.
        return "\\x" not in repr(text)


# At the bottom to break import cycles created by type annotations.
from . import extensions  # noqa: E402
