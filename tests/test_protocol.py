import unittest

from internal.guard.limits import ResourceLimits
from internal.guard.resource_guard import ResourceGuard
from internal.protocol.resp.request_decoder import RespRequestDecoder
from internal.protocol.resp.response_encoder import RespResponseEncoder
from internal.protocol.resp.types import RESP_ARRAY
from internal.protocol.resp.types import RESP_MAP
from internal.protocol.resp.types import blob_string
from internal.protocol.resp.types import map_value
from internal.protocol.resp.types import number
from internal.protocol.resp.types import simple_string


class ProtocolTest(unittest.TestCase):
    def setUp(self) -> None:
        guard = ResourceGuard(
            ResourceLimits(
                max_connections=10,
                max_request_size_bytes=4096,
                max_array_items=64,
                max_resp_depth=8,
                max_blob_size_bytes=4096,
            )
        )
        self.decoder = RespRequestDecoder(guard)
        self.encoder = RespResponseEncoder()

    def test_decoder_parses_hello_request(self) -> None:
        frame = b"*2\r\n$5\r\nHELLO\r\n:3\r\n"

        request = self.decoder.decode(frame)

        self.assertEqual(request.kind, RESP_ARRAY)
        self.assertEqual(request.value[0].value, "HELLO")
        self.assertEqual(request.value[1].value, 3)

    def test_encoder_serializes_map_response(self) -> None:
        response = map_value(
            [
                (simple_string("server"), simple_string("mini-redis")),
                (simple_string("proto"), number(3)),
            ]
        )

        encoded = self.encoder.encode(response)
        decoded = self.decoder.decode(encoded)

        self.assertEqual(decoded.kind, RESP_MAP)
        self.assertEqual(decoded.value[0][0].value, "server")
        self.assertEqual(decoded.value[0][1].value, "mini-redis")
        self.assertEqual(decoded.value[1][0].value, "proto")
        self.assertEqual(decoded.value[1][1].value, 3)

    def test_encoder_serializes_blob_string_request(self) -> None:
        request = self.encoder.encode(
            map_value([(simple_string("ignored"), blob_string("value"))])
        )

        decoded = self.decoder.decode(request)

        self.assertEqual(decoded.kind, RESP_MAP)
        self.assertEqual(decoded.value[0][1].value, "value")
