import unittest

from internal.config.runtime_config import RuntimeConfig
from internal.server.server import MiniRedisServer


class ImportsTest(unittest.TestCase):
    def test_runtime_config_default_can_be_created(self) -> None:
        config = RuntimeConfig.default()
        server = MiniRedisServer(config)
        self.assertIsNotNone(server)
