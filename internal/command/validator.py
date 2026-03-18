from internal.command.command import Command
from internal.command.errors import CommandValidationError


class CommandValidator:
    _SUPPORTED_ARITY = {
        "HELLO": 1,
        "SET": 2,
        "GET": 1,
        "DEL": 1,
        "EXPIRE": 2,
        "TTL": 1,
    }

    def validate(self, command: Command) -> None:
        if command.name not in self._SUPPORTED_ARITY:
            raise CommandValidationError("unsupported command")
        if len(command.arguments) != self._SUPPORTED_ARITY[command.name]:
            raise CommandValidationError("wrong number of arguments")
        if command.name == "HELLO":
            self._parse_positive_integer(command.arguments[0], "protocol version must be an integer")
        if command.name == "EXPIRE":
            seconds = self._parse_positive_integer(
                command.arguments[1],
                "seconds must be a positive integer",
            )
            if seconds <= 0:
                raise CommandValidationError("seconds must be a positive integer")

    def _parse_positive_integer(self, raw_value: str, message: str) -> int:
        try:
            return int(raw_value)
        except ValueError as exc:
            raise CommandValidationError(message) from exc
