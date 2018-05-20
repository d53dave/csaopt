import logging
import msgpack
import asyncio

from typing import Dict, Optional, Any
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from asyncio.selector_events import BaseSelectorEventLoop as EventLoop

from ..jobs import Job
from . import Worker, ActiveJob

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
        self.management_recv_topic: str = management_recv_topic
        self.data_recv_topic: str = data_recv_topic
        self.consumer = consumer
        self.producer = producer
        self.workers: Dict[str, Worker] = {}
        self.submitted_jobs: Dict[str, ActiveJob] = {}

    async def _consume(self):
        try:
            # Consume messages
            async for msg in self.consumer:
                log.debug('consumed: [{}, {}, {}, {}, {}, {}]'.format(
                          msg.topic, msg.partition, msg.offset,
                          msg.key, msg.value, msg.timestamp))

                if msg.topic == self.management_recv_topic:
                    worker_id = msg.value['worker_id']
                    if msg.key == 'heartbeat':
                        self._handle_worker_heartbeat(worker_id, msg.timestamp)
                    elif msg.key == 'join':
                        self._handle_worker_join(worker_id, msg.timestamp)
                    elif msg.key == 'stats':
                        self._handle_worker_stats(worker_id, msg.value)
                if msg.topic == self.data_recv_topic:
                    if msg.key == 'result_states':
                        self._handle_job_results(worker_id, msg.value)
                    if msg.key == 'result_values':
                        self._handle_job_values(worker_id, msg.value)
                else:
                    log.error('Received unrecognized message on queue: {}', msg)
                    
        finally:
            # Will leave consumer group; perform autocommit if enabled.
            await self.consumer.stop()
            await self.producer.stop()

    def _handle_job_results(self, worker_id: str, results: Dict[str, Any]) -> None:
        job_id = results.get('job_id', None)
        if job_id is not None and job_id in self.submitted_jobs:
            job = self.submitted_jobs[job_id].job
            job.results.append(results['data'])

    def _handle_job_values(self, worker_id: str, values: Dict[str, Any]) -> None:
        job_id = values.get('job_id', None)
        if job_id is not None and job_id in self.submitted_jobs:
            job = self.submitted_jobs[job_id].job
            job.values.append(values['data'])

    def _handle_worker_heartbeat(self, worker_id: str, hb_timestamp_utc: int):
        if worker_id in self.workers:
            self.workers[worker_id].update_heartbeat(hb_timestamp_utc)
        else:
            log.warn(
                'Worker [{}] sent heartbeat but has not previously joined.'.format(worker_id))

    def _handle_worker_join(self, worker_id: str, hb_timestamp_utc: int):
        if worker_id not in self.workers:
            log.info('Worker [{}] joined.'.format(worker_id))
            worker = Worker(worker_id)
            worker.update_heartbeat(hb_timestamp_utc)
            self.workers[worker_id] = worker
        else:
            log.warn(
                'Worker [{}] tried to join but is already joined.'.format(worker_id))

    def _handle_worker_stats(self, worker_id: str, stats: Dict[str, Any]) -> None:
        if worker_id in self.workers:
            self.workers[worker_id].add_stats(stats)
        else:
            log.warn(
                'Worker [{}] tried to push stats but has not joined.'.format(worker_id)) 

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
        self.submitted_jobs[job.id] = (job, [])
        # TODO: generate params and send job to workers
        pass

    def get_results(self, job_id: str) -> Optional[Job]:
        results = self.submitted_jobs.get(job_id, None)
        if results is not None and results.job.finished is True:
            return results
        return None

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
