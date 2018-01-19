import pytest
import uuid
import time
import arrow

import context # noqa
from context import Worker


@pytest.fixture
def worker():
    return Worker(str(uuid.uuid4()))


def test_liveness(worker: Worker):
    worker.update_heartbeat(arrow.utcnow().timestamp)
    assert worker.alive(1)


def test_dead(worker: Worker):
    worker.update_heartbeat(arrow.utcnow().timestamp)
    time.sleep(1.001)
    assert not worker.alive(1)


def test_no_timestamp(worker: Worker):
    assert not worker.alive(10)
