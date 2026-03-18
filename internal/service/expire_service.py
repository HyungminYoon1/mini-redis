from internal.clock.clock import Clock
from internal.expiration.expiration_manager import ExpirationManager
from internal.protocol.resp.types import RespValue
from internal.protocol.resp.types import number
from internal.repository.store_repository import StoreRepository
from internal.repository.ttl_repository import TtlRepository


class ExpireService:
    def __init__(
        self,
        clock: Clock,
        store_repository: StoreRepository,
        ttl_repository: TtlRepository,
        expiration_manager: ExpirationManager,
    ) -> None:
        self._clock = clock
        self._store_repository = store_repository
        self._ttl_repository = ttl_repository
        self._expiration_manager = expiration_manager

    def execute(self, key: str, seconds: int) -> RespValue:
        self._expiration_manager.purge_if_expired(key)
        if self._store_repository.get(key) is None:
            return number(0)

        expires_at = self._clock.now() + seconds
        self._ttl_repository.set_expiration(key, expires_at)
        return number(1)
