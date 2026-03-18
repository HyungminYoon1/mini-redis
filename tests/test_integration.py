import io
import importlib.util
import socket
import unittest
from contextlib import redirect_stderr
from contextlib import redirect_stdout
from pathlib import Path

from internal.config.runtime_config import RuntimeConfig
from internal.server.server import MiniRedisServer


CLI_MAIN_PATH = Path(__file__).resolve().parents[1] / "cmd" / "mini_redis_cli" / "main.py"
CLI_SPEC = importlib.util.spec_from_file_location("mini_redis_cli_main", CLI_MAIN_PATH)
CLI_MODULE = importlib.util.module_from_spec(CLI_SPEC)
assert CLI_SPEC is not None
assert CLI_SPEC.loader is not None
CLI_SPEC.loader.exec_module(CLI_MODULE)
cli_main = CLI_MODULE.main


def build_test_config(port: int = 0) -> RuntimeConfig:
    defaults = RuntimeConfig.default()
    return RuntimeConfig(
        host=defaults.host,
        port=port,
        connect_timeout_seconds=defaults.connect_timeout_seconds,
        read_timeout_seconds=defaults.read_timeout_seconds,
        write_timeout_seconds=defaults.write_timeout_seconds,
        idle_timeout_seconds=defaults.idle_timeout_seconds,
        max_connections=defaults.max_connections,
        max_request_size_bytes=defaults.max_request_size_bytes,
        max_array_items=defaults.max_array_items,
        max_resp_depth=defaults.max_resp_depth,
        max_blob_size_bytes=defaults.max_blob_size_bytes,
        expiration_sweep_interval_seconds=defaults.expiration_sweep_interval_seconds,
        expiration_sweep_batch_size=defaults.expiration_sweep_batch_size,
        expiration_sweep_enabled=False,
        graceful_shutdown_seconds=defaults.graceful_shutdown_seconds,
    )


class IntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = MiniRedisServer(build_test_config())
        self.server.start()
        self.host, self.port = self.server.address

    def tearDown(self) -> None:
        self.server.stop()

    def test_cli_roundtrip_set_get(self) -> None:
        set_stdout = io.StringIO()
        with redirect_stdout(set_stdout):
            set_exit_code = cli_main(
                ["--host", self.host, "--port", str(self.port), "SET", "framework", "python"]
            )

        get_stdout = io.StringIO()
        with redirect_stdout(get_stdout):
            get_exit_code = cli_main(
                ["--host", self.host, "--port", str(self.port), "GET", "framework"]
            )

        self.assertEqual(set_exit_code, 0)
        self.assertEqual(get_exit_code, 0)
        self.assertEqual(set_stdout.getvalue().strip(), "OK")
        self.assertEqual(get_stdout.getvalue().strip(), "python")

    def test_server_requires_hello_first(self) -> None:
        with socket.create_connection((self.host, self.port), timeout=1) as connection:
            connection.sendall(b"*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n")
            raw_response = connection.recv(4096)

        self.assertIn(b"HELLO 3 must be issued before other commands", raw_response)

    def test_cli_reports_missing_key_as_nil(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = cli_main(
                ["--host", self.host, "--port", str(self.port), "GET", "missing"]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue().strip(), "(nil)")
        self.assertEqual(stderr.getvalue().strip(), "")
