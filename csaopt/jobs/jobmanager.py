import asyncio
import logging

from typing import List
from pyhocon import ConfigTree

from . import Job, ExecutionType
from ..model import Model
from ..msgqclient.client import QueueClient

# TODO: this (or somebody else) needs to check for n Models == n Workers in several cases

log = logging.getLogger(__name__)


class JobManager():
    """This class handles submission, tracking and retrieval of optimization jobs.

    This abstracts away the detailed communication with the message queue through
    the msgqueue client class.

    """
    def __init__(self,
                 ctx,
                 queue_client: QueueClient,
                 models: List[Model],
                 configs: List[ConfigTree]) -> None:
        self.queue: QueueClient = queue_client
        self.models_deployed = False
        self.models = models
        self.configs = configs
        self.execution_type: ExecutionType = ctx.exec_type
        self.jobs: List[Job] = []

    async def deploy_model(self):
        if self.execution_type is ExecutionType.SingleModelSingleConf:
            self.queue.broadcast_deploy_model(self.models[0])
        elif self.execution_type is ExecutionType.SingleModelMultiConf:
            self.queue.broadcast_deploy_model(self.models[0])
        else:
            for n, worker_id in enumerate(self.queue.workers.keys()):
                log.debug('Processing Worker {} with id {}'.format(n, worker_id))
                self.queue.deploy_model(worker_id, self.models[n])

        while not self.queue.model_deployed():
            log.debug('Awaiting queue.models_deployed()')
            asyncio.sleep(2)

        log.debug('queue.models_deployed() finished')

        self.models_deployed = True

    async def submit(self) -> List[Job]:
        if not self.models_deployed:
            raise AssertionError('Trying to submit job without deploying model')

        if self.execution_type is ExecutionType.SingleModelSingleConf:
            job = Job(self.models[0], self.configs[0])
            await self.queue.broadcast_job(job)
            job.was_submitted = True
            self.jobs.append(job)
        elif self.execution_type is ExecutionType.SingleModelMultiConf:
            for n, worker_id in enumerate(self.queue.workers.keys()):
                job = Job(self.models[0], self.configs[n])
                await self.queue.send_job(worker_id, job)
                job.was_submitted = True
                self.jobs.append(job)
        elif self.execution_type is ExecutionType.MultiModelSingleConf:
            for n, worker_id in enumerate(self.queue.workers.keys()):
                job = Job(self.models[n], self.configs[0])
                await self.queue.send_job(worker_id, job)
                job.was_submitted = True
                self.jobs.append(job)
        elif self.execution_type is ExecutionType.MultiModelMultiConf:
            for n, worker_id in enumerate(self.queue.workers.keys()):
                job = Job(self.models[n], self.configs[n])
                await self.queue.send_job(worker_id, job)
                job.was_submitted = True
                self.jobs.append(job)

        return self.jobs

    async def wait_for_results(self) -> None:
        if len(self.jobs) == 0:
            raise AssertionError('wait_for_results called but no jobs submitted')
        while any(not job.completed for job in self.jobs):
            log.debug('Waiting for results...')
            asyncio.sleep(2.5)
