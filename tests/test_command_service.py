import unittest

from internal.clock.fake_clock import FakeClock
from internal.command.command import Command
from internal.expiration.expiration_manager import ExpirationManager
from internal.expiration.ttl_calculator import TtlCalculator
from internal.protocol.resp.hello_handler import HelloHandler
from internal.repository.in_memory_store import InMemoryStoreRepository
from internal.repository.in_memory_ttl import InMemoryTtlRepository
from internal.service.command_service import CommandService
from internal.service.del_service import DelService
from internal.service.expire_service import ExpireService
from internal.service.get_service import GetService
from internal.service.set_service import SetService
from internal.service.ttl_service import TtlService


class CommandServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock(current_time=100.0)
        self.store_repository = InMemoryStoreRepository()
        self.ttl_repository = InMemoryTtlRepository()
        self.expiration_manager = ExpirationManager(
            clock=self.clock,
            store_repository=self.store_repository,
            ttl_repository=self.ttl_repository,
        )
        self.command_service = CommandService(
            hello_handler=HelloHandler(),
            set_service=SetService(self.store_repository, self.ttl_repository),
            get_service=GetService(self.store_repository, self.expiration_manager),
            del_service=DelService(
                self.store_repository,
                self.ttl_repository,
                self.expiration_manager,
            ),
            expire_service=ExpireService(
                self.clock,
                self.store_repository,
                self.ttl_repository,
                self.expiration_manager,
            ),
            ttl_service=TtlService(
                self.clock,
                self.store_repository,
                self.ttl_repository,
                self.expiration_manager,
                TtlCalculator(),
            ),
        )

    def test_set_get_and_del_roundtrip(self) -> None:
        set_response = self.command_service.execute(Command("SET", ["language", "redis"]))
        get_response = self.command_service.execute(Command("GET", ["language"]))
        del_response = self.command_service.execute(Command("DEL", ["language"]))
        missing_response = self.command_service.execute(Command("GET", ["language"]))

        self.assertEqual(set_response.value, "OK")
        self.assertEqual(get_response.value, "redis")
        self.assertEqual(del_response.value, 1)
        self.assertEqual(missing_response.kind, "null")

    def test_expire_and_ttl_follow_clock(self) -> None:
        self.command_service.execute(Command("SET", ["session", "abc123"]))
        expire_response = self.command_service.execute(Command("EXPIRE", ["session", "5"]))
        initial_ttl = self.command_service.execute(Command("TTL", ["session"]))
        self.clock.advance(5)
        expired_get = self.command_service.execute(Command("GET", ["session"]))
        expired_ttl = self.command_service.execute(Command("TTL", ["session"]))

        self.assertEqual(expire_response.value, 1)
        self.assertEqual(initial_ttl.value, 5)
        self.assertEqual(expired_get.kind, "null")
        self.assertEqual(expired_ttl.value, -2)

    def test_set_clears_existing_ttl(self) -> None:
        self.command_service.execute(Command("SET", ["message", "hello"]))
        self.command_service.execute(Command("EXPIRE", ["message", "10"]))

        ttl_before_reset = self.command_service.execute(Command("TTL", ["message"]))
        self.command_service.execute(Command("SET", ["message", "world"]))
        ttl_after_reset = self.command_service.execute(Command("TTL", ["message"]))

        self.assertEqual(ttl_before_reset.value, 10)
        self.assertEqual(ttl_after_reset.value, -1)
