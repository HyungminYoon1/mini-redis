import socket

from internal.guard.resource_guard import ResourceGuard
from internal.protocol.resp.errors import IncompleteRespError
from internal.protocol.resp.errors import RespProtocolError
from internal.protocol.resp.request_decoder import RespRequestDecoder
from internal.protocol.resp.types import RespValue


class RespSocketReader:
    def __init__(self, decoder: RespRequestDecoder, resource_guard: ResourceGuard) -> None:
        self._decoder = decoder
        self._resource_guard = resource_guard

    def read_message(
        self,
        connection: socket.socket,
        buffer: bytes = b"",
    ) -> tuple[RespValue, bytes]:
        current_buffer = buffer
        while True:
            try:
                value, next_index = self._decoder.decode_prefix(current_buffer)
                return value, current_buffer[next_index:]
            except IncompleteRespError:
                chunk = connection.recv(4096)
                if not chunk:
                    if current_buffer:
                        raise RespProtocolError("connection closed before a full RESP frame was received")
                    raise EOFError
                current_buffer += chunk
                if not self._resource_guard.validate_request_size(len(current_buffer)):
                    raise RespProtocolError("request size exceeded")
