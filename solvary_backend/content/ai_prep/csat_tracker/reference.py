from collections import deque
from math import ceil


class CSATTracker:
    def __init__(self, window_size):
        self._window = window_size
        # Active conversations in timestamp order, oldest first.
        self._queue: deque[tuple[int, str]] = deque()
        # Every conversation ever recorded: id -> (timestamp, score).
        # Kept after expiry so a repeated id is still rejected.
        self._seen: dict[str, tuple[int, int]] = {}
        # Histogram over the five possible scores (index 1..5), plus a running sum.
        self._hist = [0] * 6
        self._sum = 0
        self._last_ts = None

    @staticmethod
    def _check_score(score):
        if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
            raise ValueError("score must be an integer from 1 to 5")

    def _expire(self, current_time):
        # current_time never goes backwards, so expired entries stay expired.
        while self._queue and current_time - self._queue[0][0] > self._window:
            _, cid = self._queue.popleft()
            score = self._seen[cid][1]
            self._hist[score] -= 1
            self._sum -= score

    def record(self, conversation_id, score, timestamp):
        self._check_score(score)
        if self._last_ts is not None and timestamp <= self._last_ts:
            raise ValueError("timestamps must be strictly increasing")
        if conversation_id in self._seen:
            raise ValueError("conversation already recorded")
        self._last_ts = timestamp
        self._seen[conversation_id] = (timestamp, score)
        self._queue.append((timestamp, conversation_id))
        self._hist[score] += 1
        self._sum += score

    def get_average(self, current_time):
        self._expire(current_time)
        if not self._queue:
            return 0.0
        return round(self._sum / len(self._queue), 2)

    def update(self, conversation_id, score, current_time):
        self._check_score(score)
        self._expire(current_time)
        entry = self._seen.get(conversation_id)
        if entry is None or current_time - entry[0] > self._window:
            return False
        ts, old = entry
        self._seen[conversation_id] = (ts, score)
        self._hist[old] -= 1
        self._hist[score] += 1
        self._sum += score - old
        return True

    def get_percentile(self, current_time, p):
        if not 0 <= p <= 100:
            raise ValueError("p must be in [0, 100]")
        self._expire(current_time)
        n = len(self._queue)
        if n == 0:
            return None
        # p * n / 100 keeps integer p exact (p / 100 * n can round the wrong way).
        rank = max(0, min(n - 1, ceil(p * n / 100) - 1))
        seen = 0
        for score in range(1, 6):
            seen += self._hist[score]
            if seen > rank:
                return score

    def get_distribution(self, current_time):
        self._expire(current_time)
        return {score: self._hist[score] for score in range(1, 6)}
