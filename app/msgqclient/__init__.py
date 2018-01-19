import arrow
from arrow import Arrow
from typing import List
from ..jobs import Job


class Worker():
    """Wrapper class that keeps track of which workers are active and what jobs they are working on"""

    def __init__(self, id):
        self.id: str = id
        self.jobs: List[Job] = []
        self.heartbeat = None

    def alive(self, max_heartbeat_age_seconds: int):
        """Tests weather the last heartbeat happened at most max_heartbeat_age_seconds ago"""
        if self.heartbeat is not None:
            now: Arrow = arrow.utcnow()
            return now.shift(seconds=-max_heartbeat_age_seconds) < self.heartbeat

        return False

    def update_heartbeat(self, heartbeat_timestamp: int):
        """Update the workers last heartbeat to track liveness"""
        self.heartbeat = Arrow.utcfromtimestamp(heartbeat_timestamp)
