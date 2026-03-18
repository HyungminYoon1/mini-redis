from internal.expiration.expiration_manager import ExpirationManager
from internal.protocol.resp.types import RespValue
from internal.protocol.resp.types import number
from internal.repository.store_repository import StoreRepository
from internal.repository.ttl_repository import TtlRepository


class DelService:
    def __init__(
        self,
        store_repository: StoreRepository,
        ttl_repository: TtlRepository,
        expiration_manager: ExpirationManager,
    ) -> None:
        self._store_repository = store_repository
        self._ttl_repository = ttl_repository
        self._expiration_manager = expiration_manager

    def execute(self, key: str) -> RespValue:
        self._expiration_manager.purge_if_expired(key)
        deleted = self._store_repository.delete(key)
        self._ttl_repository.delete_expiration(key)
        return number(1 if deleted else 0)
