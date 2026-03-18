from internal.expiration.expiration_manager import ExpirationManager
from internal.protocol.resp.types import RespValue
from internal.protocol.resp.types import blob_string
from internal.protocol.resp.types import null
from internal.repository.store_repository import StoreRepository


class GetService:
    def __init__(
        self,
        store_repository: StoreRepository,
        expiration_manager: ExpirationManager,
    ) -> None:
        self._store_repository = store_repository
        self._expiration_manager = expiration_manager

    def execute(self, key: str) -> RespValue:
        self._expiration_manager.purge_if_expired(key)
        value = self._store_repository.get(key)
        if value is None:
            return null()
        return blob_string(value)
