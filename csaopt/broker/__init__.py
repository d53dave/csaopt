import dramatiq
import os
import msgpack
import msgpack_numpy
import uuid
import logging

from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend
from dramatiq import Message
from typing import Dict, Any, List, Union
from collections import defaultdict
from enum import Enum
from sortedcontainers import SortedSet

from ..model import Model
from ..utils import is_pytest_run

msgpack_numpy.patch()

log = logging.getLogger(__name__)


class WorkerCommand(Enum):
    DeployModel = 'deploy_model'
    RunOptimization = 'run_optimization'


class _MsgPackEncoder(dramatiq.Encoder):
    # MessageData = typing.Dict[str, typing.Any]
    def encode(self, data: dramatiq.encoder.MessageData) -> bytes:
        return msgpack.packb(data, use_bin_type=True)

    def decode(self, data: bytes) -> dramatiq.encoder.MessageData:
        return msgpack.unpackb(data, raw=False)


class Broker():
    def __init__(self,
                 redis_host: str='localhost',
                 redis_port: int=6379,
                 redis_password: str=None,
                 queue_ids: List[str]=[]) -> None:

        log.warn('Constructing {} without queue_ids'.format(Broker))

        if is_pytest_run():
            broker = StubBroker
            broker.emit_after('process_boot')
        else:
            self.dramatiq_broker = broker = RedisBroker(
                host=redis_host, port=redis_password, password=redis_password)

            msgpack_encoder = _MsgPackEncoder()
            self.result_backend = backend = RedisBackend(encoder=msgpack_encoder)
            broker.add_middleware(Results(backend=backend))

            dramatiq.set_broker(broker)
            dramatiq.set_encoder(msgpack_encoder)

        self.queue_ids: SortedSet = SortedSet(queue_ids)
        self.queue_messages: Dict[str, List[dramatiq.Message]] = defaultdict(list)

    def get_queue_results(self, queue: Union[str, int], timeout_ms=5000) -> List[Dict[str, Any]]:
        queue_id: str = self.__extract_queue_id(queue)
        results = []
        for msg in self.queue_messages[queue_id]:
            results.append(msg.get_result(self.result_backend, block=True, timeout=timeout_ms))
        return results

    def get_all_results(self, timeout_ms=5000) -> Dict[str, List[Dict[str, Any]]]:
        results = {}
        for queue_id in self.queue_ids:
            results[queue_id] = self.get_queue_results(queue_id, timeout_ms=timeout_ms)
        return results

    def broadcast(self, command: WorkerCommand, payload: Dict[str, Any]):
        for queue_id in self.queue_ids:
            self.send_to_queue(queue_id, command, payload)

    def send_to_queue(self, queue: Union[str, int], command: WorkerCommand, payload: Dict[str, Any]):
        queue_id = self.__extract_queue_id(queue)

        msg = self.dramatiq_broker.enqueue(Message(
            queue_name=queue_id,
            actor_name='WorkerActor',
            args=(command, payload), kwargs={},
            options={},
        ))
        self.queue_messages[queue_id].append(msg)

    def __extract_queue_id(self, queue: Union[str, int]) -> str:
        queue_id = str(queue)
        if type(queue) is int:
            if not int(queue) < len(self.queue_ids):
                raise AssertionError('Queue index out of range: ' + str(queue))
            queue_id = self.queue_ids[int(queue)]

        if queue_id not in self.queue_ids:
            raise AssertionError('Queue id not found: ' + queue_id)

        return queue_id
