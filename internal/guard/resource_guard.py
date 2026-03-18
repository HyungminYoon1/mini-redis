from internal.guard.limits import ResourceLimits


class ResourceGuard:
    def __init__(self, limits: ResourceLimits) -> None:
        self._limits = limits

    def validate_request_size(self, size_bytes: int) -> bool:
        return size_bytes <= self._limits.max_request_size_bytes

    def validate_array_items(self, count: int) -> bool:
        return count <= self._limits.max_array_items

    def validate_resp_depth(self, depth: int) -> bool:
        return depth <= self._limits.max_resp_depth

    def validate_blob_size(self, size_bytes: int) -> bool:
        return size_bytes <= self._limits.max_blob_size_bytes
