from internal.command.command import Command
from internal.command.errors import CommandValidationError
from internal.protocol.resp.types import RESP_ARRAY
from internal.protocol.resp.types import RESP_BLOB_STRING
from internal.protocol.resp.types import RESP_NUMBER
from internal.protocol.resp.types import RESP_SIMPLE_STRING
from internal.protocol.resp.types import RespValue


class CommandParser:
    def parse(self, request: RespValue) -> Command:
        if request.kind != RESP_ARRAY:
            raise CommandValidationError("request must be a RESP array")

        parts = [self._coerce_argument(item) for item in request.value]
        if not parts:
            raise CommandValidationError("empty command")
        return Command(name=parts[0].upper(), arguments=parts[1:])

    def _coerce_argument(self, value: RespValue) -> str:
        if value.kind in {RESP_SIMPLE_STRING, RESP_BLOB_STRING}:
            return str(value.value)
        if value.kind == RESP_NUMBER:
            return str(value.value)
        raise CommandValidationError("command arguments must be strings or numbers")
