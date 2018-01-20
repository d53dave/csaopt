import pytest
import asyncio
import arrow
import context  # noqa

from collections import namedtuple, deque
from context import QueueClient


FakeMessage = namedtuple('FakeMessage', ['topic', 'partition', 'offset',
                                         'key', 'value', 'timestamp'])


management_topic = 'management.test.t'
data_topic = 'data.test.t'


class FakeConsumer:
    def __init__(self):
        self.messages = deque([])

    async def add(self, msg):
        self.messages.appendleft(msg)

    async def __aiter__(self):
        return self

    async def __anext__(self):
        if len(self.messages) > 0:
            return self.messages.pop()
        else:
            raise StopAsyncIteration

    async def stop(self):
        pass


class FakeProducer:
    def __init__(self, consumer: FakeConsumer) -> None:
        self.consumer: FakeConsumer = consumer

    async def send(self, topic, key, message):
        msg = FakeMessage(topic=topic, partition=0, offset=0,
                          key=key, value=message,
                          timestamp=arrow.utcnow().timestamp)
        await self.consumer.add(msg)

    async def stop(self):
        pass


@pytest.fixture
def fake_consumer():
    return FakeConsumer()


@pytest.fixture
def fake_producer(fake_consumer: FakeConsumer):
    return FakeProducer(fake_consumer)


@pytest.fixture
def client(fake_consumer, fake_producer):
    return QueueClient(management_topic, data_topic, fake_consumer, fake_producer)


@pytest.mark.asyncio
async def test_worker_join(client: QueueClient, fake_producer: FakeProducer, event_loop):
    event_loop.create_task(client._update_worker_timeout(worker_timeout_seconds=1))
    worker_msg = {'worker_id': '12345', 'gpus': 1, 'hostname': 'host1'}
    await fake_producer.send(management_topic, 'join', worker_msg)
    await client._consume()

    assert len(client.workers) == 1
    assert client.workers['12345'] is not None


@pytest.mark.timeout(10)
@pytest.mark.asyncio
async def test_worker_timeout(client: QueueClient, fake_producer: FakeProducer, event_loop):
    task = asyncio.ensure_future(
        client._update_worker_timeout(worker_timeout_seconds=0.5), loop=event_loop)
    worker_msg = {'worker_id': '12345'}
    await fake_producer.send(management_topic, 'join', worker_msg)
    await client._consume()

    assert len(client.workers) == 1
    assert client.workers['12345'] is not None

    await asyncio.sleep(1)
    assert len(client.workers) == 0
    task.cancel()
    # Exiting will produce a warning. I tried waiting for the task to finish
    # and it seems to be exiting fine. However! the loop will still have
    # this task pending somewhere, even if we are waiting it to finish before
    # this method finishes. Is this a bug?


@pytest.mark.timeout(10)
@pytest.mark.asyncio
async def test_worker_heartbeat(client: QueueClient, fake_producer: FakeProducer, event_loop):
    worker_msg = {'worker_id': '12345'}
    await fake_producer.send(management_topic, 'join', worker_msg)
    await client._consume()

    first_heartbeat: arrow.Arrow = client.workers['12345'].heartbeat

    await asyncio.sleep(1)
    await fake_producer.send(management_topic, 'heartbeat', worker_msg)
    await client._consume()

    second_heartbeat: arrow.Arrow = client.workers['12345'].heartbeat

    assert second_heartbeat > first_heartbeat


@pytest.mark.timeout(10)
@pytest.mark.asyncio
async def test_worker_sends_stats(client: QueueClient, fake_producer: FakeProducer):
    worker_msg = {'worker_id': '12345'}
    await fake_producer.send(management_topic, 'join', worker_msg)

    stats = {'worker_id': '12345', 'gpu': {}, 'mem': {}, 'cpu': {}}
    await fake_producer.send(management_topic, 'stats', stats)
    await client._consume()

    assert client.workers['12345'].latest_stats() == stats


@pytest.mark.timeout(10)
@pytest.mark.asyncio
async def test_worker_sends_stats_no_stats(client: QueueClient, fake_producer: FakeProducer):
    worker_msg = {'worker_id': '12345'}
    await fake_producer.send(management_topic, 'join', worker_msg)
    await client._consume()

    assert client.workers['12345'].latest_stats() is None


@pytest.mark.timeout(10)
@pytest.mark.asyncio
async def test_worker_sends_results_without_job(client: QueueClient):
    worker_msg = {'worker_id': '12345'}
    await fake_producer.send(management_topic, 'join', worker_msg)

    await fake_producer.send(data_topic, 'full', {'states': [[1], [2]]})
    


@pytest.mark.timeout(10)
@pytest.mark.asyncio
async def test_worker_sends_results(client: QueueClient):
    worker_msg = {'worker_id': '12345'}
    await fake_producer.send(data_topic, 'join', worker_msg)
