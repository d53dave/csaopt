import arrow

from collections import deque
from arrow import Arrow
from typing import Dict, MutableSequence, NamedTuple, List
from ..jobs import Job


class Worker():
    """Wrapper class that keeps track of which workers are active and what jobs they are working on"""

    def __init__(self, id) -> None:
        self.id: str = id
        self.jobs: List[Job] = {}
        self.heartbeat = None
        self.stats: MutableSequence[Dict] = deque(maxlen=15)

    def alive(self, max_heartbeat_age_seconds: int) -> bool:
        """Tests weather the last heartbeat happened at most max_heartbeat_age_seconds ago"""
        if self.heartbeat is not None:
            now: Arrow = arrow.utcnow()
            return now.shift(seconds=-max_heartbeat_age_seconds) < self.heartbeat

        return False

    def update_heartbeat(self, heartbeat_timestamp: int) -> None:
        """Update the workers last heartbeat to track liveness"""
        self.heartbeat = Arrow.utcfromtimestamp(heartbeat_timestamp)

    def add_stats(self, stats: Dict) -> None:
        """Add a stats object to the deque of stats."""
        self.stats.append(stats)

    def latest_stats(self) -> Dict:
        """Get the most recent stats object"""
        *_, last = self.stats
        return last


class ActiveJob(NamedTuple):
    job: Job
    workers: List[Worker]
