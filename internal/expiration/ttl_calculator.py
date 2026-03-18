class TtlCalculator:
    def calculate_remaining_seconds(self, now: float, expires_at: float) -> int:
        remaining = int(expires_at - now)
        if remaining < 0:
            return 0
        return remaining
