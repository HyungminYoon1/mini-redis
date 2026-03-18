from __future__ import annotations

import socket
import threading
import time

from internal.clock.clock import Clock
from internal.clock.system_clock import SystemClock
from internal.command.parser import CommandParser
from internal.command.validator import CommandValidator
from internal.config.runtime_config import RuntimeConfig
from internal.expiration.expiration_manager import ExpirationManager
from internal.expiration.expiration_sweeper import ExpirationSweeper
from internal.expiration.ttl_calculator import TtlCalculator
from internal.guard.limits import ResourceLimits
from internal.guard.resource_guard import ResourceGuard
from internal.observability.logger import Logger
from internal.observability.metrics import Metrics
from internal.protocol.resp.hello_handler import HelloHandler
from internal.protocol.resp.request_decoder import RespRequestDecoder
from internal.protocol.resp.response_encoder import RespResponseEncoder
from internal.protocol.resp.socket_io import RespSocketReader
from internal.repository.in_memory_store import InMemoryStoreRepository
from internal.repository.in_memory_ttl import InMemoryTtlRepository
from internal.server.session_handler import SessionHandler
from internal.service.command_service import CommandService
from internal.service.del_service import DelService
from internal.service.expire_service import ExpireService
from internal.service.get_service import GetService
from internal.service.set_service import SetService
from internal.service.ttl_service import TtlService


class MiniRedisServer:
    def __init__(
        self,
        config: RuntimeConfig,
        clock: Clock | None = None,
        logger: Logger | None = None,
        metrics: Metrics | None = None,
    ) -> None:
        self._config = config
        self._clock = clock or SystemClock()
        self._logger = logger or Logger()
        self._metrics = metrics or Metrics()

        self._store_repository = InMemoryStoreRepository()
        self._ttl_repository = InMemoryTtlRepository()
        self._expiration_manager = ExpirationManager(
            clock=self._clock,
            store_repository=self._store_repository,
            ttl_repository=self._ttl_repository,
        )
        self._expiration_sweeper = ExpirationSweeper(
            clock=self._clock,
            store_repository=self._store_repository,
            ttl_repository=self._ttl_repository,
            sweep_batch_size=self._config.expiration_sweep_batch_size,
        )

        self._command_parser = CommandParser()
        self._command_validator = CommandValidator()
        self._command_service = CommandService(
            hello_handler=HelloHandler(),
            set_service=SetService(self._store_repository, self._ttl_repository),
            get_service=GetService(self._store_repository, self._expiration_manager),
            del_service=DelService(
                self._store_repository,
                self._ttl_repository,
                self._expiration_manager,
            ),
            expire_service=ExpireService(
                self._clock,
                self._store_repository,
                self._ttl_repository,
                self._expiration_manager,
            ),
            ttl_service=TtlService(
                self._clock,
                self._store_repository,
                self._ttl_repository,
                self._expiration_manager,
                TtlCalculator(),
            ),
        )
        self._resource_guard = ResourceGuard(
            ResourceLimits(
                max_connections=self._config.max_connections,
                max_request_size_bytes=self._config.max_request_size_bytes,
                max_array_items=self._config.max_array_items,
                max_resp_depth=self._config.max_resp_depth,
                max_blob_size_bytes=self._config.max_blob_size_bytes,
            )
        )
        self._socket_reader = RespSocketReader(
            decoder=RespRequestDecoder(self._resource_guard),
            resource_guard=self._resource_guard,
        )
        self._response_encoder = RespResponseEncoder()

        self._command_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._server_socket: socket.socket | None = None
        self._server_thread: threading.Thread | None = None
        self._sweeper_thread: threading.Thread | None = None
        self._client_threads: list[threading.Thread] = []
        self._address = (self._config.host, self._config.port)
        self._startup_error: Exception | None = None

    @property
    def address(self) -> tuple[str, int]:
        return self._address

    def wait_until_ready(self, timeout: float = 2.0) -> bool:
        return self._ready_event.wait(timeout)

    def run(self) -> None:
        self.start()
        try:
            while self._server_thread is not None and self._server_thread.is_alive():
                self._server_thread.join(timeout=0.2)
        except KeyboardInterrupt:
            self._logger.info("keyboard interrupt received, shutting down")
        finally:
            self.stop()

    def start(self) -> None:
        if self._server_thread is not None and self._server_thread.is_alive():
            return

        self._stop_event.clear()
        self._ready_event.clear()
        self._startup_error = None
        self._server_thread = threading.Thread(target=self._serve_loop, daemon=True)
        self._server_thread.start()

        if not self.wait_until_ready(timeout=self._config.connect_timeout_seconds):
            raise RuntimeError("server did not become ready in time")
        if self._startup_error is not None:
            raise RuntimeError(f"server failed to start: {self._startup_error}") from self._startup_error

    def stop(self) -> None:
        if self._stop_event.is_set():
            return

        self._stop_event.set()
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass

        if self._server_thread is not None and self._server_thread.is_alive():
            self._server_thread.join(timeout=self._config.graceful_shutdown_seconds)

        if self._sweeper_thread is not None and self._sweeper_thread.is_alive():
            self._sweeper_thread.join(timeout=self._config.graceful_shutdown_seconds)

        for client_thread in list(self._client_threads):
            if client_thread.is_alive():
                client_thread.join(timeout=self._config.graceful_shutdown_seconds)

    def _serve_loop(self) -> None:
        try:
            if self._config.expiration_sweep_enabled:
                self._sweeper_thread = threading.Thread(target=self._run_sweeper_loop, daemon=True)
                self._sweeper_thread.start()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((self._config.host, self._config.port))
                server_socket.listen(self._config.max_connections)
                server_socket.settimeout(0.5)

                self._server_socket = server_socket
                self._address = server_socket.getsockname()
                self._ready_event.set()
                self._logger.info(
                    f"mini-redis listening on {self._address[0]}:{self._address[1]}"
                )

                while not self._stop_event.is_set():
                    try:
                        connection, _ = server_socket.accept()
                    except socket.timeout:
                        continue
                    except OSError:
                        if self._stop_event.is_set():
                            break
                        raise

                    connection.settimeout(self._config.read_timeout_seconds)
                    client_thread = threading.Thread(
                        target=self._handle_connection,
                        args=(connection,),
                        daemon=True,
                    )
                    self._client_threads.append(client_thread)
                    client_thread.start()
        except Exception as exc:
            self._startup_error = exc
            self._ready_event.set()
            raise

    def _run_sweeper_loop(self) -> None:
        self._expiration_sweeper.start()
        while not self._stop_event.is_set():
            self._expiration_sweeper.sweep_once()
            time.sleep(self._config.expiration_sweep_interval_seconds)
        self._expiration_sweeper.stop()

    def _handle_connection(self, connection: socket.socket) -> None:
        self._metrics.connections_total += 1
        handler = SessionHandler(
            connection=connection,
            socket_reader=self._socket_reader,
            response_encoder=self._response_encoder,
            command_parser=self._command_parser,
            command_validator=self._command_validator,
            command_service=self._command_service,
            command_lock=self._command_lock,
            logger=self._logger,
            metrics=self._metrics,
        )
        handler.handle()
