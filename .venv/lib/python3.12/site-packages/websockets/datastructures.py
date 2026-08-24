from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Mapping, MutableMapping
from typing import Any, Protocol


__all__ = [
    "Headers",
    "HeadersLike",
    "MultipleValuesError",
]


class MultipleValuesError(LookupError):
    """
    Exception raised when :class:`Headers` has multiple values for a key.

    """

    def __str__(self) -> str:
        # Implement the same logic as KeyError_str in Objects/exceptions.c.
        if len(self.args) == 1:
            return repr(self.args[0])
        return super().__str__()


# Same regex as http11._value_re, but for matching str rather than bytes.
is_valid_header_value = re.compile(r"[\x09\x20-\x7e\x80-\xff]*").fullmatch


class Headers(MutableMapping[str, str]):
    """
    Efficient data structure for manipulating HTTP headers.

    A :class:`list` of ``(name, values)`` is inefficient for lookups.

    A :class:`dict` doesn't suffice because header names are case-insensitive
    and multiple occurrences of headers with the same name are possible.

    :class:`Headers` stores HTTP headers in a hybrid data structure to provide
    efficient insertions and lookups while preserving the original data.

    In order to account for multiple values with minimal hassle,
    :class:`Headers` follows this logic:

    - When getting a header with ``headers[name]``:
        - if there's no value, :exc:`KeyError` is raised;
        - if there's exactly one value, it's returned;
        - if there's more than one value, :exc:`MultipleValuesError` is raised.

    - When setting a header with ``headers[name] = value``, the value is
      appended to the list of values for that header.

    - When deleting a header with ``del headers[name]``, all values for that
      header are removed (this is slow).

    Other methods for manipulating headers are consistent with this logic.

    As long as no header occurs multiple times, :class:`Headers` behaves like
    :class:`dict`, except keys are lower-cased to provide case-insensitivity.

    Two methods support manipulating multiple values explicitly:

    - :meth:`get_all` returns a list of all values for a header;
    - :meth:`raw_items` returns an iterator of ``(name, values)`` pairs.

    Header names and values are expected to contain only ASCII text. However,
    non-ASCII values happen in practice, even though there is no standard for
    transmitting non-ASCII data in HTTP headers. :class:`Headers` supports it
    by treating it as ISO-8859-1 data. This is a safe and reversible encoding
    to represent arbitrary data in a :class:`str`.

    When reading headers from the network, if the actual encoding isn't
    ISO-8859-1, you must re-encode and decode, e.g.::

        value = headers[key].encode("iso-8859-1").decode("utf-8")

    Conversely, when sending headers to the network, if you need to use a
    different encoding, you can encode and decode, e.g.::

        headers[key] = value.encode("utf-8").decode("iso-8859-1")

    When assigning a value to a header, as a security hardening measure, the
    value is checked for unsafe characters. The name isn't checked because it's
    usually a constant in code, unlikely to be tainted by user input.

    """

    __slots__ = ["_dict", "_list"]

    # Like dict, Headers accepts an optional "mapping or iterable" argument.
    def __init__(self, *args: HeadersLike, **kwargs: str) -> None:
        self._dict: dict[str, list[str]] = {}
        self._list: list[tuple[str, str]] = []
        self.update(*args, **kwargs)

    def __str__(self) -> str:
        return "".join(f"{key}: {value}\r\n" for key, value in self._list) + "\r\n"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._list!r})"

    def copy(self) -> Headers:
        copy = self.__class__()
        copy._dict = self._dict.copy()
        copy._list = self._list.copy()
        return copy

    def serialize(self) -> bytes:
        # parse_headers() supports non-ASCII header values. It decodes them as
        # ISO-8859-1. Encode back in ISO-8859-1 in order to round-trip cleanly.
        return str(self).encode("iso-8859-1")

    # Collection methods

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and key.lower() in self._dict

    def __iter__(self) -> Iterator[str]:
        return iter(self._dict)

    def __len__(self) -> int:
        return len(self._dict)

    # MutableMapping methods

    def __getitem__(self, key: str) -> str:
        value = self._dict[key.lower()]
        if len(value) == 1:
            return value[0]
        else:
            raise MultipleValuesError(key)

    def __setitem__(self, key: str, value: str) -> None:
        if not is_valid_header_value(str(value)):
            raise InvalidHeaderValue(key, value)
        self._dict.setdefault(key.lower(), []).append(value)
        self._list.append((key, value))

    def __delitem__(self, key: str) -> None:
        key_lower = key.lower()
        self._dict.__delitem__(key_lower)
        # This is inefficient. Fortunately deleting HTTP headers is uncommon.
        self._list = [(k, v) for k, v in self._list if k.lower() != key_lower]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Headers):
            return NotImplemented
        return self._dict == other._dict

    def clear(self) -> None:
        """
        Remove all headers.

        """
        self._dict = {}
        self._list = []

    def update(self, *args: HeadersLike, **kwargs: str) -> None:
        """
        Update from a :class:`Headers` instance and/or keyword arguments.

        """
        args = tuple(
            arg.raw_items() if isinstance(arg, Headers) else arg for arg in args
        )
        super().update(*args, **kwargs)

    # Methods for handling multiple values

    def get_all(self, key: str) -> list[str]:
        """
        Return the (possibly empty) list of all values for a header.

        Args:
            key: Header name.

        """
        return self._dict.get(key.lower(), [])

    def raw_items(self) -> Iterator[tuple[str, str]]:
        """
        Return an iterator of all values as ``(name, value)`` pairs.

        """
        return iter(self._list)

    # Internal methods

    def set_insecure(self, key: str, value: str) -> None:
        """
        Set a header without validating its value.

        """
        self._dict.setdefault(key.lower(), []).append(value)
        self._list.append((key, value))


# copy of _typeshed.SupportsKeysAndGetItem.
class SupportsKeysAndGetItem(Protocol):
    """
    Dict-like types with ``keys() -> str`` and ``__getitem__(key: str) -> str`` methods.

    """

    def keys(self) -> Iterable[str]: ...  # pragma: no branch

    def __getitem__(self, key: str) -> str: ...  # pragma: no branch


HeadersLike = (
    Headers | Mapping[str, str] | Iterable[tuple[str, str]] | SupportsKeysAndGetItem
)
"""
Types accepted where :class:`Headers` is expected.

In addition to :class:`Headers` itself, this includes dict-like types where both
keys and values are :class:`str`.

"""


# At the bottom to break an import cycle.
from .exceptions import InvalidHeaderValue  # noqa: E402
