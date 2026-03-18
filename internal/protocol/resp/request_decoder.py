from __future__ import annotations

from internal.guard.resource_guard import ResourceGuard
from internal.protocol.resp.errors import IncompleteRespError
from internal.protocol.resp.errors import RespProtocolError
from internal.protocol.resp.types import RespValue
from internal.protocol.resp.types import array
from internal.protocol.resp.types import blob_string
from internal.protocol.resp.types import error
from internal.protocol.resp.types import map_value
from internal.protocol.resp.types import null
from internal.protocol.resp.types import number
from internal.protocol.resp.types import simple_string


class RespRequestDecoder:
    def __init__(self, resource_guard: ResourceGuard | None = None) -> None:
        self._resource_guard = resource_guard

    def decode(self, data: bytes) -> RespValue:
        value, next_index = self.decode_prefix(data)
        if next_index != len(data):
            raise RespProtocolError("multiple RESP frames in a single payload are not supported")
        return value

    def decode_prefix(self, data: bytes) -> tuple[RespValue, int]:
        return self._parse(data=data, index=0, depth=1)

    def _parse(self, data: bytes, index: int, depth: int) -> tuple[RespValue, int]:
        if not self._is_valid_depth(depth):
            raise RespProtocolError("RESP nesting depth exceeded")
        if index >= len(data):
            raise IncompleteRespError("missing RESP type prefix")

        prefix = data[index:index + 1]
        if prefix == b"+":
            raw_value, next_index = self._read_line(data, index + 1)
            return simple_string(raw_value.decode("utf-8")), next_index
        if prefix == b"-":
            raw_value, next_index = self._read_line(data, index + 1)
            message = raw_value.decode("utf-8")
            if message.startswith("ERR "):
                message = message[4:]
            return error(message), next_index
        if prefix == b":":
            raw_value, next_index = self._read_line(data, index + 1)
            return number(self._parse_integer(raw_value.decode("utf-8"))), next_index
        if prefix == b"_":
            if len(data) < index + 3:
                raise IncompleteRespError("incomplete null frame")
            if data[index + 1:index + 3] != b"\r\n":
                raise RespProtocolError("invalid null frame terminator")
            return null(), index + 3
        if prefix == b"$":
            return self._parse_blob_string(data, index + 1)
        if prefix == b"*":
            return self._parse_array(data, index + 1, depth + 1)
        if prefix == b"%":
            return self._parse_map(data, index + 1, depth + 1)
        raise RespProtocolError(f"unsupported RESP type prefix: {prefix!r}")

    def _parse_blob_string(self, data: bytes, index: int) -> tuple[RespValue, int]:
        raw_length, next_index = self._read_line(data, index)
        length = self._parse_integer(raw_length.decode("utf-8"))
        if length == -1:
            return null(), next_index
        if length < 0:
            raise RespProtocolError("blob string length must not be negative")
        if not self._is_valid_blob_size(length):
            raise RespProtocolError("blob string length exceeded")

        end_index = next_index + length
        if len(data) < end_index + 2:
            raise IncompleteRespError("incomplete blob string payload")
        if data[end_index:end_index + 2] != b"\r\n":
            raise RespProtocolError("invalid blob string terminator")
        payload = data[next_index:end_index].decode("utf-8")
        return blob_string(payload), end_index + 2

    def _parse_array(self, data: bytes, index: int, depth: int) -> tuple[RespValue, int]:
        raw_count, next_index = self._read_line(data, index)
        count = self._parse_integer(raw_count.decode("utf-8"))
        if count < 0:
            raise RespProtocolError("array length must not be negative")
        if not self._is_valid_array_size(count):
            raise RespProtocolError("array item count exceeded")

        values: list[RespValue] = []
        current_index = next_index
        for _ in range(count):
            value, current_index = self._parse(data, current_index, depth)
            values.append(value)
        return array(values), current_index

    def _parse_map(self, data: bytes, index: int, depth: int) -> tuple[RespValue, int]:
        raw_count, next_index = self._read_line(data, index)
        count = self._parse_integer(raw_count.decode("utf-8"))
        if count < 0:
            raise RespProtocolError("map length must not be negative")
        if not self._is_valid_array_size(count * 2):
            raise RespProtocolError("map item count exceeded")

        entries: list[tuple[RespValue, RespValue]] = []
        current_index = next_index
        for _ in range(count):
            key, current_index = self._parse(data, current_index, depth)
            value, current_index = self._parse(data, current_index, depth)
            entries.append((key, value))
        return map_value(entries), current_index

    def _read_line(self, data: bytes, index: int) -> tuple[bytes, int]:
        line_end = data.find(b"\r\n", index)
        if line_end == -1:
            raise IncompleteRespError("incomplete RESP line")
        return data[index:line_end], line_end + 2

    def _parse_integer(self, raw_value: str) -> int:
        try:
            return int(raw_value)
        except ValueError as exc:
            raise RespProtocolError(f"invalid integer value: {raw_value}") from exc

    def _is_valid_array_size(self, count: int) -> bool:
        if self._resource_guard is None:
            return True
        return self._resource_guard.validate_array_items(count)

    def _is_valid_blob_size(self, size_bytes: int) -> bool:
        if self._resource_guard is None:
            return True
        return self._resource_guard.validate_blob_size(size_bytes)

    def _is_valid_depth(self, depth: int) -> bool:
        if self._resource_guard is None:
            return True
        return self._resource_guard.validate_resp_depth(depth)
