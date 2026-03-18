from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from internal.config.runtime_config import RuntimeConfig
from internal.guard.limits import ResourceLimits
from internal.guard.resource_guard import ResourceGuard
from internal.protocol.resp.request_decoder import RespRequestDecoder
from internal.protocol.resp.response_encoder import RespResponseEncoder
from internal.protocol.resp.socket_io import RespSocketReader
from internal.protocol.resp.types import RESP_ARRAY
from internal.protocol.resp.types import RESP_BLOB_STRING
from internal.protocol.resp.types import RESP_ERROR
from internal.protocol.resp.types import RESP_MAP
from internal.protocol.resp.types import RESP_NULL
from internal.protocol.resp.types import RESP_NUMBER
from internal.protocol.resp.types import RESP_SIMPLE_STRING
from internal.protocol.resp.types import RespValue
from internal.protocol.resp.types import array
from internal.protocol.resp.types import blob_string
from internal.protocol.resp.types import number


def main(argv: list[str] | None = None) -> int:
    default_config = RuntimeConfig.default()
    parser = argparse.ArgumentParser(description="Run a single mini-redis command")
    parser.add_argument("--host", default=default_config.host, help="Server host")
    parser.add_argument("--port", default=default_config.port, type=int, help="Server port")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command and arguments")
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_usage(sys.stderr)
        return 2

    resource_guard = ResourceGuard(
        ResourceLimits(
            max_connections=default_config.max_connections,
            max_request_size_bytes=default_config.max_request_size_bytes,
            max_array_items=default_config.max_array_items,
            max_resp_depth=default_config.max_resp_depth,
            max_blob_size_bytes=default_config.max_blob_size_bytes,
        )
    )
    encoder = RespResponseEncoder()
    socket_reader = RespSocketReader(
        decoder=RespRequestDecoder(resource_guard),
        resource_guard=resource_guard,
    )

    hello_request = array([blob_string("HELLO"), number(3)])
    command_request = array([blob_string(part) for part in args.command])

    try:
        with socket.create_connection(
            (args.host, args.port),
            timeout=default_config.connect_timeout_seconds,
        ) as connection:
            connection.settimeout(default_config.read_timeout_seconds)
            connection.sendall(encoder.encode(hello_request))
            hello_response, _ = socket_reader.read_message(connection)
            if hello_response.kind == RESP_ERROR:
                print(f"ERR {hello_response.value}", file=sys.stderr)
                return 4

            connection.sendall(encoder.encode(command_request))
            response, _ = socket_reader.read_message(connection)
    except OSError as exc:
        print(f"connection error: {exc}", file=sys.stderr)
        return 3

    return _render_response(response)


def _render_response(value: RespValue) -> int:
    if value.kind in {RESP_SIMPLE_STRING, RESP_BLOB_STRING, RESP_NUMBER}:
        print(value.value)
        return 0
    if value.kind == RESP_NULL:
        print("(nil)")
        return 0
    if value.kind == RESP_ERROR:
        print(f"ERR {value.value}", file=sys.stderr)
        return 4
    if value.kind == RESP_MAP:
        for key, item_value in value.value:
            rendered_key = _render_inline(key)
            rendered_value = _render_inline(item_value)
            print(f"{rendered_key}: {rendered_value}")
        return 0
    if value.kind == RESP_ARRAY:
        for item in value.value:
            print(_render_inline(item))
        return 0

    print(f"unsupported response kind: {value.kind}", file=sys.stderr)
    return 4


def _render_inline(value: RespValue) -> str:
    if value.kind in {RESP_SIMPLE_STRING, RESP_BLOB_STRING, RESP_NUMBER}:
        return str(value.value)
    if value.kind == RESP_NULL:
        return "(nil)"
    if value.kind == RESP_ERROR:
        return f"ERR {value.value}"
    if value.kind == RESP_ARRAY:
        return "[" + ", ".join(_render_inline(item) for item in value.value) + "]"
    if value.kind == RESP_MAP:
        return "{" + ", ".join(
            f"{_render_inline(key)}: {_render_inline(item_value)}"
            for key, item_value in value.value
        ) + "}"
    return str(value.value)


if __name__ == "__main__":
    raise SystemExit(main())
