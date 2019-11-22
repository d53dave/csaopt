"""
This module provides all required functionality for the communication between the application master and workers.
"""

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
    """Check whether a real or a stub broker should be used.

    This is useful for testing.

    Returns:
        True if USE_STUB_BROKER environemtn variable is set and truthy
    """
    return bool(os.environ.get('USE_STUB_BROKER')) is True


class WorkerCommand(Enum):
    """Enum for supported worker commands"""

    DeployModel = 'deploy_model'
    RunOptimization = 'run_optimization'


class _MsgPackEncoder(dramatiq.Encoder):
    def encode(self, data: dramatiq.encoder.MessageData) -> bytes:
        return msgpack.packb(data, use_bin_type=True)

    def decode(self, data: bytes) -> dramatiq.encoder.MessageData:
        return msgpack.unpackb(data, raw=False)


class Broker():
    """Class wrapping a Dramatiq broker

    This class wraps a Dramatiq Broker and offers sending messages and retrieving results from said broker. Since the
    worker code is, by design, separate from this codebase, the standard way of communicating with Dramatiq workers
    is unavailable. Therefore, messages are enqueued directly on the broker and kept track of by this class. When
    retrieving results, the stored messages are polled for results and then discarded.

    Per convention, there is one optimization worker per queue id, so the size of the list of queue ids must correspond
    with the overall number of worker processes, or more specifically, the number of worker instances, since one
    Dramatiq worker always only runs one process and therefore one optimization worker.


    Args:
        host: Hostname or IP address of Dramatiq broker infrastructure, currently Redis
        port: Redis port
        password: Redis password
        queue_ids: Queue ids of available workers
    """

    def __init__(self,
                 host: str = 'localhost',
                 port: int = 6379,
                 password: str = None,
                 queue_ids: List[str] = [],
                 **kwargs: str) -> None:

        if len(queue_ids) < 1:
            log.warning('Constructing {} without queue_ids'.format(Broker))

        if is_pytest_run() and _use_stub_broker():
            broker = StubBroker
            broker.emit_after('process_boot')
        else:
            self.dramatiq_broker = broker = RedisBroker(host=host, port=port, password=password, **kwargs)

            msgpack_encoder = _MsgPackEncoder()
            self.result_backend = backend = RedisBackend(encoder=msgpack_encoder, client=self.dramatiq_broker.client)
            broker.add_middleware(Results(backend=backend))

        dramatiq.set_broker(broker)
        dramatiq.set_encoder(msgpack_encoder)

        self.queue_ids: SortedSet = SortedSet(queue_ids)
        self.queue_messages: Dict[str, List[dramatiq.Message]] = defaultdict(list)

    def clear_queue_messages(self):
        """Clears messages that were queued on the broker

        The broker can only wait for results on message objects that were submitted to the Dramatiq broker.
        It does so by keeping an internal queue of messages. These messages will be polled for results in the
        next call to :meth:`~Broker.get_results`. Clearing the queue has the effect of 'forgetting' earlier
        messages.

        """
        self.queue_messages.clear()

    def ping(self, queue: Union[str, int]) -> bool:
        """Sends a `ping` message to the specified queue.

        The Dramatiq PingActor will receive a `ping` message and should respond with `pong`. This is a blocking call.

        Args:
            queue: Index or id of queue

        Returns:
            `True` if the actor responded with `pong`

        """
        queue_id = self.__extract_queue_id(queue)

        msg = self.dramatiq_broker.enqueue(
            Message(
                queue_name=queue_id,
                actor_name='PingActor',
                args=(),
                kwargs={},
                options={},
            ))

        # TODO refactor for dynamic timeout
        result = msg.get_result(backend=self.result_backend, block=True, timeout=2000)

        return result == 'pong'

    async def get_queue_results(self, queue: Union[str, int], timeout=10.0) -> List[Dict[str, Any]]:
        """Get results for specific queue.

        This will attempt to fetch all results from the Dramatiq results backend for a specific queue. Calls
        :meth:`~Broker.get_results` with the supplied queue index or id

        Args:
            queue: Index or id of queue
            timeout: Timeout in seconds

        Returns:
            A list of the retrieved results

        """
        for queue_id in self.queue_ids:
            results = await self.get_results(queues=[self.__extract_queue_id(queue)], result_timeout=timeout)

        return results[queue_id]

    async def get_all_results(self, timeout=10.0) -> Dict[str, List[Dict[str, Any]]]:
        """Get results for all known queue.

        This will attempt to fetch all results from the Dramatiq results backend for a all known queues. Calls
        :meth:`~Broker.get_results` with a list of all queue ids.


        Args:
            timeout: Overall timeout in seconds (i.e. not per-queue)

        Returns:
            A dictionary of queue ids and list of the retrieved results for each queue

        """
        return await self.get_results(queues=self.queue_ids, result_timeout=timeout)

    async def get_results(self, queues: List[str], result_timeout: float = 10.0) -> Dict[str, List[Dict[str, Any]]]:
        """Get results for a list of queue indices or ids.

        This will attempt to fetch results from the Dramatiq results backend for the specified queues. Internally,
        it constructs a list of messages that need to provide results and tries, in a non-blocking manner, to get
        results from the Dramatiq results backend. If a message has not yet received results, it will be re-tried
        after one-tenth of the specified timeout, but at a minimum of 1 second. Therefore, this method will re-try
        for a total number of 10 times, after which the overall timeout will stop the polling.


        Args:
            queues: List of queue indices or ids
            result_timeout: Overall timeout in seconds (i.e. not per-queue)

        Returns:
            A dictionary of queue ids and list of the retrieved results for each queue

        """
        messages_to_process: Dict[str, List[dramatiq.Message]] = {}
        for queue_id in self.queue_ids:
            for message in self.queue_messages[queue_id]:
                messages_to_process[message.message_id] = message
        log.debug('Messages to process is [{}]'.format(messages_to_process))

        message_ids_processed: List[str] = []
        results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        async with timeout(result_timeout) as timeout_cm:
            while len(messages_to_process) > 0:
                for msg in messages_to_process.values():
                    try:
                        msg_result = msg.get_result(  # type: ignore
                            backend=self.result_backend, timeout=int(result_timeout * 1e3))
                        results[msg.queue_name].append(msg_result)  # type: ignore

                        message_ids_processed.append(msg.message_id)  # type: ignore
                    except ResultMissing:
                        pass

                # Remove all processed messages from messages_to_process list
                for message_id in message_ids_processed:
                    messages_to_process.pop(message_id, None)

                message_ids_processed.clear()

                log.debug('Sleeping for {} seconds, there is/are still {} messages to be awaited.'.format(
                    max(1.0, result_timeout / 10.0), len(messages_to_process)))
                await asyncio.sleep(max(1.0, result_timeout / 10.0))

        if timeout_cm.expired:
            raise TimeoutError('Timed out while waiting for results')

        return results

    def broadcast(self, command: WorkerCommand, payload: Dict[str, Any]) -> None:
        """Send a command and payload to all registered queues.

        Args:
            command: Command
            payload: Any dictionary that can be serialized by msgpack (and msgpack-numpy)

        Returns:
            Nothing
        """
        log.debug('Broadcasting cmd [{}] and payload [{}] to queue ids: {}', command, payload, self.queue_ids)
        for queue_id in self.queue_ids:
            self.send_to_queue(queue_id, command, payload)

    def send_to_queue(self, queue: Union[str, int], command: WorkerCommand, payload: Dict[str, Any]) -> None:
        """Send a command and payload to a queue.

        Args:
            queue: Index or queue id
            command: Command
            payload: Any dictionary that can be serialized by msgpack (and msgpack-numpy)

        Returns:
            Nothing
        """
        queue_id = self.__extract_queue_id(queue)

        msg = self.dramatiq_broker.enqueue(
            Message(
                queue_name=queue_id,
                actor_name='OptimizationActor',
                args=(command.value, payload),
                kwargs={},
                options={},
            ))
        log.debug('Appending msg[{}] to queued_messages'.format(msg))
        self.queue_messages[queue_id].append(msg)

    def __extract_queue_id(self, queue: Union[str, int]) -> str:
        """Retrieves the queue id for a given index or id

        If the input is an integer, this method will select the queue at the speficied index. Otherwise, it will try
        to match the input as a string agains all known queue ids.

        Args:
            queue: Index or queue id

        Returns:
            Queue id for the queue at the specified index.

        Raises:
            AssertionError if the index is out of bounds or the queue id is unknown.
        """
        queue_id = str(queue)
        if type(queue) is int:
            if not int(queue) < len(self.queue_ids):
                raise AssertionError('Queue index out of range: ' + str(queue))
            queue_id = self.queue_ids[int(queue)]

        if queue_id not in self.queue_ids:
            raise AssertionError('Queue id not found: ' + queue_id)

        return queue_id
