from internal.clock.clock import Clock
from internal.expiration.expiration_manager import ExpirationManager
from internal.expiration.ttl_calculator import TtlCalculator
from internal.protocol.resp.types import RespValue
from internal.protocol.resp.types import number
from internal.repository.store_repository import StoreRepository
from internal.repository.ttl_repository import TtlRepository


class TtlService:
    def __init__(
        self,
        clock: Clock,
        store_repository: StoreRepository,
        ttl_repository: TtlRepository,
        expiration_manager: ExpirationManager,
        ttl_calculator: TtlCalculator,
    ) -> None:
        self._clock = clock
        self._store_repository = store_repository
        self._ttl_repository = ttl_repository
        self._expiration_manager = expiration_manager
        self._ttl_calculator = ttl_calculator

    def execute(self, key: str) -> RespValue:
        self._expiration_manager.purge_if_expired(key)
        if self._store_repository.get(key) is None:
            return number(-2)

        expires_at = self._ttl_repository.get_expiration(key)
        if expires_at is None:
            return number(-1)

        remaining_seconds = self._ttl_calculator.calculate_remaining_seconds(
            now=self._clock.now(),
            expires_at=expires_at,
        )
        return number(remaining_seconds)
