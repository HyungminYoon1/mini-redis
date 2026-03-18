from internal.server.server import MiniRedisServer


class ShutdownManager:
    def __init__(self, server: MiniRedisServer) -> None:
        self._server = server

    def shutdown(self) -> None:
        self._server.stop()
