from internal.protocol.resp.types import RespValue
from internal.protocol.resp.types import simple_string
from internal.repository.store_repository import StoreRepository
from internal.repository.ttl_repository import TtlRepository


class SetService:
    def __init__(self, store_repository: StoreRepository, ttl_repository: TtlRepository) -> None:
        self._store_repository = store_repository
        self._ttl_repository = ttl_repository

    def execute(self, key: str, value: str) -> RespValue:
        self._store_repository.set(key, value)
        self._ttl_repository.delete_expiration(key)
        return simple_string("OK")
