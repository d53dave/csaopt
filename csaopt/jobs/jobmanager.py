import asyncio
import logging

from typing import List
from pyhocon import ConfigTree

from . import Job, ExecutionType
from ..model import Model
from ..broker import Broker, WorkerCommand

# TODO: this (or somebody else) needs to check for n Models == n Workers in several cases

log = logging.getLogger(__name__)


class JobManager():
    """This class handles submission, tracking and retrieval of optimization jobs.

    This abstracts away the detailed communication with the message queue through
    the msgqueue client class.

    """
    def __init__(self,
                 ctx,
                 broker: Broker,
                 models: List[Model],
                 configs: List[ConfigTree]) -> None:

        self.broker = broker
        self.models_deployed = False
        self.models = models
        self.configs = configs
        self.execution_type: ExecutionType = self._get_execution_type(models, configs)
        self.jobs: List[Job] = []

    def _get_execution_type(self, models: List[Model], configs: List[ConfigTree]) -> ExecutionType:
        len_models = len(models)
        len_configs = len(configs)

        if len_models < 1:
            raise AssertionError('No models provided')
        if len_configs < 1:
            raise AssertionError('No configs provided')

        if len_models > 1 and len_configs > 1 and len_configs != len_models:
            raise AssertionError('For len(models) == {}, there should be {} configs, but found {}'.format(
                                 len_models, len_models, len_configs))

        if len_models == 1 and len_configs == 1:
            return ExecutionType.SingleModelSingleConf
        elif len_models == 1 and len_configs > 1:
            return ExecutionType.SingleModelMultiConf
        elif len_models > 1 and len_configs == 1:
            return ExecutionType.MultiModelSingleConf
        elif len_models > 1 and len_configs > 1:
            return ExecutionType.MultiModelMultiConf
        else:
            raise AssertionError('Could not determine Exec Type for len(models) == {} and len(configs) == {}'.format(
                                 len_models, len_configs))

    async def deploy_model(self):
        if self.execution_type is ExecutionType.SingleModelSingleConf:
            self.broker.broadcast_deploy_model(self.models[0])
        elif self.execution_type is ExecutionType.SingleModelMultiConf:
            self.broker.broadcast_deploy_model(self.models[0])
        else:
            for n, worker_id in enumerate(self.broker.workers.keys()):
                log.debug('Processing Worker {} with id {}'.format(n, worker_id))
                self.broker.deploy_model(worker_id, self.models[n])

        while not self.broker.model_deployed():
            log.debug('Awaiting queue.models_deployed()')
            asyncio.sleep(2)

        log.debug('queue.models_deployed() finished')

        self.models_deployed = True

    def submit(self) -> List[Job]:
        if not self.models_deployed:
            raise AssertionError('Trying to submit job without deploying model')

        cmd = WorkerCommand.RunOptimization

        if self.execution_type is ExecutionType.SingleModelSingleConf:
            job = Job(self.models[0], self.configs[0])
            self.broker.broadcast(cmd, job.to_dict())
            job.submitted_to.extend(self.broker.queue_ids) 
            self.jobs.append(job)
        elif self.execution_type is ExecutionType.SingleModelMultiConf:
            for n, queue_id in enumerate(self.broker.queue_ids):
                job = Job(self.models[0], self.configs[n])
                self.broker.send_to_queue(queue_id, cmd, job.to_dict())
                job.submitted_to = [queue_id]
                self.jobs.append(job)
        elif self.execution_type is ExecutionType.MultiModelSingleConf:
            for n, queue_id in enumerate(self.broker.queue_ids):
                job = Job(self.models[n], self.configs[0])
                self.broker.send_to_queue(queue_id, cmd, job.to_dict())
                job.submitted_to = [queue_id]
                self.jobs.append(job)
        elif self.execution_type is ExecutionType.MultiModelMultiConf:
            for n, queue_id in enumerate(self.broker.queue_ids):
                job = Job(self.models[n], self.configs[n])
                self.broker.send_to_queue(queue_id, cmd, job.to_dict())
                job.submitted_to = [queue_id]
                self.jobs.append(job)

        return self.jobs

    async def wait_for_results(self) -> None:
        if len(self.jobs) == 0:
            raise AssertionError('wait_for_results called but no jobs submitted')
        while any(not job.completed for job in self.jobs):
            log.debug('Waiting for results...')
            asyncio.sleep(2.5)
