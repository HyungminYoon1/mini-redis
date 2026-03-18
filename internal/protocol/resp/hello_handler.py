from internal.protocol.resp.types import RespValue
from internal.protocol.resp.types import error
from internal.protocol.resp.types import map_value
from internal.protocol.resp.types import number
from internal.protocol.resp.types import simple_string


class HelloHandler:
    def handle(self, version: int) -> RespValue:
        if version != 3:
            return error("unsupported protocol version")
        return map_value(
            [
                (simple_string("server"), simple_string("mini-redis")),
                (simple_string("version"), simple_string("1.0")),
                (simple_string("proto"), number(3)),
            ]
        )
