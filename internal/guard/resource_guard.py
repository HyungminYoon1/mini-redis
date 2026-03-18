from internal.guard.limits import ResourceLimits


class ResourceGuard:
    def __init__(self, limits: ResourceLimits) -> None:
        self._limits = limits

    def is_request_size_allowed(self, size_bytes: int) -> bool:
        return size_bytes <= self._limits.max_request_size_bytes

    def is_connection_allowed(self, active_connections: int) -> bool:
        return active_connections < self._limits.max_connections
