import logging
import msgpack
import asyncio

from typing import Dict, Any
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from asyncio.selector_events import BaseSelectorEventLoop as EventLoop

from app.jobs import Job
from . import Worker

log = logging.getLogger(__name__)


class QueueClient:

    @classmethod
    async def create(cls, ioloop: EventLoop, conf: Dict[str, Any]):
        management_recv_topic = conf['kafka.topics.management_recv']
        data_recv_topic = conf['kafka.topics.management_recv']

        consumer = AIOKafkaConsumer(
            [management_recv_topic, data_recv_topic],
            loop=ioloop, bootstrap_servers=conf['kafka.servers'],
            group_id=conf['kafka.consumer_group'],
            key_deserializer=QueueClient._KeyDeserializer(),
            value_deserializer=QueueClient._ValueDeserializer())

        producer = AIOKafkaProducer(
            loop=ioloop, bootstrap_servers=conf['kafka.servers'],
            key_serializer=QueueClient._KeySerializer(),
            value_serializer=QueueClient._ValueSerializer())

        self = QueueClient(
            management_recv_topic,
            data_recv_topic,
            consumer,
            producer
        )

        await self.consumer.start()
        await self.producer.start()

        worker_timeout = conf['worker.timeout_seconds']
        asyncio.Task(self._update_worker_timeout(worker_timeout), loop=ioloop)

        return self

    def __init__(self,
                 management_recv_topic: str,
                 data_recv_topic: str,
                 consumer: AIOKafkaConsumer,
                 producer: AIOKafkaProducer) -> None:
        self.workers: Dict[str, Worker] = {}
        self.management_recv_topic: str = management_recv_topic
        self.data_recv_topic: str = data_recv_topic
        self.consumer = consumer
        self.producer = producer

    async def _consume(self):
        try:
            # Consume messages
            async for msg in self.consumer:
                log.debug('consumed: [{}, {}, {}, {}, {}, {}]'.format(msg.topic, msg.partition, msg.offset,
                          msg.key, msg.value, msg.timestamp))
                if msg.topic == self.management_recv_topic:
                    if msg.key == 'heartbeat':
                        worker_id = msg.value['worker_id']
                        self._handle_worker_heartbeat(worker_id, msg.timestamp)
                if msg.topic == self.data_recv_topic:
                    pass
        finally:
            # Will leave consumer group; perform autocommit if enabled.
            await self.consumer.stop()
            await self.producer.stop()

    def _handle_worker_heartbeat(self, worker_id: str, hb_timestamp_utc: int):
        if worker_id in self.workers:
            self.workers[worker_id].update_heartbeat(hb_timestamp_utc)
        else:
            log.info('Worker [{}] joined.'.format(worker_id))
            worker = Worker(worker_id)
            worker.update_heartbeat(hb_timestamp_utc)
            self.workers[worker_id] = worker

    async def _update_worker_timeout(self, worker_timeout_seconds):
        while True:
            try:
                await asyncio.sleep(0.5)
            except asyncio.CancelledError as e:
                log.info('Exiting update_worker_timeout loop')
                raise e
            for worker_id in list(self.workers.keys()):
                if not self.workers[worker_id].alive(worker_timeout_seconds):
                    del self.workers[worker_id]
                    log.warn('Worker [{}] timed out.'.format(worker_id))

    async def _send_one(self, topic, key=None, value=None):
        try:
            # Produce message
            await self.producer.send(topic, key=key, value=value)
        finally:
            # Wait for all pending messages to be delivered or expire.
            pass

    async def submit_job(self, job: Job):
        # self.submitted[job.id] = job
        pass

    def get_results(id):
        pass

    class _KeySerializer:
        def __call__(self, key: str) -> bytes:
            return key.encode(encoding='utf_8') if key is not None else b''

    class _ValueSerializer:
        def __call__(self, value: object) -> bytes:
            return msgpack.packb(value, use_bin_type=True)

    class _KeyDeserializer:
        def __call__(self, keyBytes: bytes) -> str:
            return keyBytes.decode(encoding='utf-8') if bytes is not None else ''

    class _ValueDeserializer:
        def __call__(self, valueBytes: bytes) -> object:
            return msgpack.unpackb(valueBytes)
