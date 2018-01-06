import logging
import msgpack

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from app.jobs import Job

log = logging.getLogger(__name__)


class QueueClient:

    @classmethod
    async def create(cls, ioloop, conf):
        self = QueueClient()
        self.conf = conf
        print('Starting client with config: ', conf)
        self.consumer = AIOKafkaConsumer(
            *conf['kafka.consumer_topics'],
            loop=ioloop, bootstrap_servers=conf['kafka.servers'],
            group_id=conf['kafka.consumer_group'],
            key_deserializer=QueueClient._KeyDeserializer(),
            value_deserializer=QueueClient._ValueDeserializer())

        self.producer = AIOKafkaProducer(
            loop=ioloop, bootstrap_servers=conf['kafka.servers'],
            key_serializer=QueueClient._KeySerializer(),
            value_serializer=QueueClient._ValueSerializer())

        await self.consumer.start()
        await self.producer.start()

        return self

    def __init__(self):
        self.submitted = {}

    async def _consume(self):
        try:
            # Consume messages
            async for msg in self.consumer:
                log.debug("consumed: ", msg.topic, msg.partition, msg.offset,
                          msg.key, msg.value, msg.timestamp)
                if(msg.topic == 'csaopt.data.in.t'):
                    pass
                if(msg.topic == 'csaopt.stats.in.t'):
                    pass
                print(msg)
        finally:
            # Will leave consumer group; perform autocommit if enabled.
            await self.consumer.stop()
            await self.producer.stop()

    async def _send_one(self, topic, key=None, value=None):
        try:
            # Produce message
            await self.producer.send(topic, key=key, value=value)
        finally:
            # Wait for all pending messages to be delivered or expire.
            pass

    async def submit_job(self, job: Job):
        self.submitted[job.id] = job

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
