import socket
import threading

from internal.command.errors import CommandValidationError
from internal.command.parser import CommandParser
from internal.command.validator import CommandValidator
from internal.observability.logger import Logger
from internal.observability.metrics import Metrics
from internal.protocol.resp.errors import RespProtocolError
from internal.protocol.resp.response_encoder import RespResponseEncoder
from internal.protocol.resp.socket_io import RespSocketReader
from internal.protocol.resp.types import error
from internal.service.command_service import CommandService


class SessionHandler:
    def __init__(
        self,
        connection: socket.socket,
        socket_reader: RespSocketReader,
        response_encoder: RespResponseEncoder,
        command_parser: CommandParser,
        command_validator: CommandValidator,
        command_service: CommandService,
        command_lock: threading.Lock,
        logger: Logger,
        metrics: Metrics,
    ) -> None:
        self._connection = connection
        self._socket_reader = socket_reader
        self._response_encoder = response_encoder
        self._command_parser = command_parser
        self._command_validator = command_validator
        self._command_service = command_service
        self._command_lock = command_lock
        self._logger = logger
        self._metrics = metrics

    def handle(self) -> None:
        buffer = b""
        hello_completed = False

        with self._connection:
            while True:
                try:
                    request, buffer = self._socket_reader.read_message(self._connection, buffer)
                except EOFError:
                    return
                except RespProtocolError as exc:
                    self._metrics.errors_total += 1
                    self._connection.sendall(self._response_encoder.encode(error(str(exc))))
                    return

                try:
                    command = self._command_parser.parse(request)
                    self._command_validator.validate(command)
                    if not hello_completed and command.name != "HELLO":
                        response = error("HELLO 3 must be issued before other commands")
                    else:
                        with self._command_lock:
                            response = self._command_service.execute(command)
                    if command.name == "HELLO" and response.kind != "error":
                        hello_completed = True
                except CommandValidationError as exc:
                    self._metrics.errors_total += 1
                    response = error(str(exc))
                except Exception as exc:
                    self._metrics.errors_total += 1
                    self._logger.error(f"session error: {exc}")
                    response = error("internal server error")

                self._metrics.requests_total += 1
                self._connection.sendall(self._response_encoder.encode(response))
