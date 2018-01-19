import pytest
import asyncio
import arrow
import context  # noqa

from collections import namedtuple
from queue import Queue
from context import Worker, QueueClient


FakeMessage = namedtuple('FakeMessage', ['topic', 'partition', 'offset',
                                         'key', 'value', 'timestamp'])


class FakeConsumer:
    def __init__(self):
        self.messages = Queue()

    async def add(self, msg):
        self.messages.put(msg)

    async def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.messages.empty():
            return self.messages.get()
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
    return QueueClient('management.t', 'data.t', fake_consumer, fake_producer)


@pytest.mark.asyncio
async def test_lol(client: QueueClient, fake_producer: FakeProducer):
    await fake_producer.send('data.t', 'lol', 'lol')
    await client._consume()
    assert True


@pytest.mark.asyncio
async def test_worker_join(client: QueueClient, event_loop):
    event_loop.create_task(client._update_worker_timeout(worker_timeout_seconds=1))
    worker_msg = {'worker_id': '12345'}
    await client.producer.send('management.t', 'heartbeat', worker_msg)
    await client._consume()

    assert len(client.workers) == 1
    assert client.workers['12345'] is not None


@pytest.mark.timeout(10)
@pytest.mark.asyncio
async def test_worker_timeout(client: QueueClient, event_loop):
    task = asyncio.ensure_future(
        client._update_worker_timeout(worker_timeout_seconds=0.5), loop=event_loop)
    worker_msg = {'worker_id': '12345'}
    await client.producer.send('management.t', 'heartbeat', worker_msg)
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
