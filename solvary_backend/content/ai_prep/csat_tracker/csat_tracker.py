class CSATTracker:
    """Part 1: record scores, rolling average. See the statement."""

    def __init__(self, window_size: int) -> None:
        raise NotImplementedError

    def record(self, conversation_id: str, score: int, timestamp: int) -> None:
        raise NotImplementedError

    def get_average(self, current_time: int) -> float:
        raise NotImplementedError
