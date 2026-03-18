from internal.command.command import Command
from internal.protocol.resp.hello_handler import HelloHandler
from internal.protocol.resp.types import RespValue
from internal.service.del_service import DelService
from internal.service.expire_service import ExpireService
from internal.service.get_service import GetService
from internal.service.set_service import SetService
from internal.service.ttl_service import TtlService


class CommandService:
    def __init__(
        self,
        hello_handler: HelloHandler,
        set_service: SetService,
        get_service: GetService,
        del_service: DelService,
        expire_service: ExpireService,
        ttl_service: TtlService,
    ) -> None:
        self._hello_handler = hello_handler
        self._set_service = set_service
        self._get_service = get_service
        self._del_service = del_service
        self._expire_service = expire_service
        self._ttl_service = ttl_service

    def execute(self, command: Command) -> RespValue:
        if command.name == "HELLO":
            return self._hello_handler.handle(int(command.arguments[0]))
        if command.name == "SET":
            return self._set_service.execute(command.arguments[0], command.arguments[1])
        if command.name == "GET":
            return self._get_service.execute(command.arguments[0])
        if command.name == "DEL":
            return self._del_service.execute(command.arguments[0])
        if command.name == "EXPIRE":
            return self._expire_service.execute(command.arguments[0], int(command.arguments[1]))
        if command.name == "TTL":
            return self._ttl_service.execute(command.arguments[0])
        raise ValueError(f"unsupported command: {command.name}")
