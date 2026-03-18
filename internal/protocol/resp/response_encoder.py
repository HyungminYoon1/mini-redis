from internal.protocol.resp.types import RESP_ARRAY
from internal.protocol.resp.types import RESP_BLOB_STRING
from internal.protocol.resp.types import RESP_ERROR
from internal.protocol.resp.types import RESP_MAP
from internal.protocol.resp.types import RESP_NULL
from internal.protocol.resp.types import RESP_NUMBER
from internal.protocol.resp.types import RESP_SIMPLE_STRING
from internal.protocol.resp.types import RespValue


class RespResponseEncoder:
    def encode(self, value: RespValue) -> bytes:
        if value.kind == RESP_SIMPLE_STRING:
            return self._encode_line(prefix=b"+", payload=str(value.value))
        if value.kind == RESP_BLOB_STRING:
            encoded = str(value.value).encode("utf-8")
            return b"$" + str(len(encoded)).encode("ascii") + b"\r\n" + encoded + b"\r\n"
        if value.kind == RESP_NUMBER:
            return self._encode_line(prefix=b":", payload=str(value.value))
        if value.kind == RESP_NULL:
            return b"_\r\n"
        if value.kind == RESP_ERROR:
            return self._encode_line(prefix=b"-", payload=f"ERR {value.value}")
        if value.kind == RESP_ARRAY:
            encoded_items = b"".join(self.encode(item) for item in value.value)
            return b"*" + str(len(value.value)).encode("ascii") + b"\r\n" + encoded_items
        if value.kind == RESP_MAP:
            encoded_items = b"".join(
                self.encode(key) + self.encode(map_entry_value)
                for key, map_entry_value in value.value
            )
            return b"%" + str(len(value.value)).encode("ascii") + b"\r\n" + encoded_items
        raise ValueError(f"unsupported RESP value kind: {value.kind}")

    def _encode_line(self, prefix: bytes, payload: str) -> bytes:
        return prefix + payload.encode("utf-8") + b"\r\n"
