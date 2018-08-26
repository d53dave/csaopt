import dramatiq
import os
import msgpack
import msgpack_numpy
import uuid
import logging
import sys
import asyncio

from async_timeout import timeout
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker
from dramatiq.results import Results, ResultMissing
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


def _use_stub_broker() -> bool:
    return os.environ.get('USE_STUB_BROKER') is True


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
                 host: str='localhost',
                 port: int=6379,
                 password: str=None,
                 queue_ids: List[str]=[]) -> None:

        if len(queue_ids) < 1:
            log.warn('Constructing {} without queue_ids'.format(Broker))

        if is_pytest_run() and _use_stub_broker():
            broker = StubBroker
            broker.emit_after('process_boot')
        else:
            self.dramatiq_broker = broker = RedisBroker(
                host=host, port=port, password=password)

            msgpack_encoder = _MsgPackEncoder()
            self.result_backend = backend = RedisBackend(
                encoder=msgpack_encoder, client=self.dramatiq_broker.client)
            broker.add_middleware(Results(backend=backend))

        dramatiq.set_broker(broker)
        dramatiq.set_encoder(msgpack_encoder)

        self.queue_ids: SortedSet = SortedSet(queue_ids)
        self.queue_messages: Dict[str,
                                  List[dramatiq.Message]] = defaultdict(list)

    def clear_queue_messages(self):
        self.queue_messages.clear()

    def ping(self, queue: Union[str, int]) -> bool:
        queue_id = self.__extract_queue_id(queue)

        msg = self.dramatiq_broker.enqueue(Message(
            queue_name=queue_id,
            actor_name='PingActor',
            args=(), kwargs={},
            options={},
        ))

        # TODO refactor for dynamic timeout
        result = msg.get_result(
            backend=self.result_backend, block=True, timeout=2000)

        return result == 'pong'

    async def get_queue_results(self, queue: Union[str, int], timeout=10.0) -> List[Dict[str, Any]]:
        for queue_id in self.queue_ids:
            results = await self.get_results(
                queues=[self.__extract_queue_id(queue)], result_timeout=timeout)

        return results[queue_id]

    async def get_all_results(self, timeout=10.0):
        results = {}
        for queue_id in self.queue_ids:
            results = await self.get_results(
                queues=self.queue_ids, result_timeout=timeout)
        return results

    async def get_results(self, queues: List[str], result_timeout: float=10.0) -> Dict[str, List[Dict[str, Any]]]:
        messages_to_process: Dict[str, List[dramatiq.Message]] = {}
        for queue_id in self.queue_ids:
            for message in self.queue_messages[queue_id]:
                messages_to_process[message.message_id] = message
        log.warn('Messages to process is [{}]'.format(messages_to_process))

        message_ids_processed: List[str] = []
        results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        async with timeout(result_timeout) as timeout_cm:
            while len(messages_to_process) > 0:
                for msg in messages_to_process.values():
                    try:
                        results[msg.queue_name].append(msg.get_result(  # type: ignore
                            backend=self.result_backend, timeout=int(result_timeout * 1e3)))

                        message_ids_processed.append(
                            msg.message_id)  # type: ignore
                    except ResultMissing:
                        pass

                # Remove all processed messages from messages_to_process list
                for message_id in message_ids_processed:
                    messages_to_process.pop(message_id, None)

                log.debug('Sleeping for {} seconds, there is/are still {} messages to be processed.'.format(
                    max(1.0, result_timeout / 10.0), len(messages_to_process)))
                await asyncio.sleep(max(1.0, result_timeout / 10.0))

        if timeout_cm.expired:
            raise TimeoutError('Timed out while waiting for results')

        return results

    def broadcast(self, command: WorkerCommand, payload: Dict[str, Any]):
        for queue_id in self.queue_ids:
            self.send_to_queue(queue_id, command, payload)

    def send_to_queue(self, queue: Union[str, int], command: WorkerCommand, payload: Dict[str, Any]):
        queue_id = self.__extract_queue_id(queue)

        msg = self.dramatiq_broker.enqueue(Message(
            queue_name=queue_id,
            actor_name='OptimizationActor',
            args=(command.value, payload), kwargs={},
            options={},
        ))
        log.debug('Appending msg[{}] to queued_messages'.format(msg))
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
