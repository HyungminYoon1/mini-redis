from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from internal.config.runtime_config import RuntimeConfig
from internal.server.server import MiniRedisServer


def main(argv: list[str] | None = None) -> int:
    default_config = RuntimeConfig.default()
    parser = argparse.ArgumentParser(description="Run the mini-redis server")
    parser.add_argument("--host", default=default_config.host, help="Host to bind to")
    parser.add_argument("--port", default=default_config.port, type=int, help="Port to bind to")
    args = parser.parse_args(argv)

    config = RuntimeConfig(
        host=args.host,
        port=args.port,
        connect_timeout_seconds=default_config.connect_timeout_seconds,
        read_timeout_seconds=default_config.read_timeout_seconds,
        write_timeout_seconds=default_config.write_timeout_seconds,
        idle_timeout_seconds=default_config.idle_timeout_seconds,
        max_connections=default_config.max_connections,
        max_request_size_bytes=default_config.max_request_size_bytes,
        max_array_items=default_config.max_array_items,
        max_resp_depth=default_config.max_resp_depth,
        max_blob_size_bytes=default_config.max_blob_size_bytes,
        expiration_sweep_interval_seconds=default_config.expiration_sweep_interval_seconds,
        expiration_sweep_batch_size=default_config.expiration_sweep_batch_size,
        expiration_sweep_enabled=default_config.expiration_sweep_enabled,
        graceful_shutdown_seconds=default_config.graceful_shutdown_seconds,
    )
    server = MiniRedisServer(config)
    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
