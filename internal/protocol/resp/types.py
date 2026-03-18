from dataclasses import dataclass
from typing import Any


RESP_SIMPLE_STRING = "simple_string"
RESP_BLOB_STRING = "blob_string"
RESP_NUMBER = "number"
RESP_NULL = "null"
RESP_ERROR = "error"
RESP_ARRAY = "array"
RESP_MAP = "map"


@dataclass(frozen=True)
class RespValue:
    kind: str
    value: Any = None


def simple_string(value: str) -> RespValue:
    return RespValue(kind=RESP_SIMPLE_STRING, value=value)


def blob_string(value: str) -> RespValue:
    return RespValue(kind=RESP_BLOB_STRING, value=value)


def number(value: int) -> RespValue:
    return RespValue(kind=RESP_NUMBER, value=value)


def null() -> RespValue:
    return RespValue(kind=RESP_NULL, value=None)


def error(message: str) -> RespValue:
    return RespValue(kind=RESP_ERROR, value=message)


def array(values: list[RespValue]) -> RespValue:
    return RespValue(kind=RESP_ARRAY, value=values)


def map_value(entries: list[tuple[RespValue, RespValue]]) -> RespValue:
    return RespValue(kind=RESP_MAP, value=entries)
