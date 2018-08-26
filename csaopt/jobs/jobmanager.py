import asyncio
import logging

from typing import List, Dict
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
        self.execution_type: ExecutionType = self._get_execution_type(
            models, configs)
        self.jobs: List[Job] = []
        if self.broker is not None:
            self.queue_models_deployed: Dict[str, bool] = {
                queue_id: False for queue_id in self.broker.queue_ids}

    async def wait_for_worker_join(self, is_retry=False):
        joined_workers = []
        for queue_id in self.broker.queue_ids:
            try:
                if self.broker.ping(queue_id) is True:
                    joined_workers.append(queue_id)
                else:
                    raise AssertionError(
                        'Worker {} failed to join'.format(queue_id))
            except Exception as e:
                if is_retry:
                    log.exception(
                        'Exception occurred while waiting for workers to join')
                    raise e

                log.warn('Retrying to contact broker in order to ping workers')
                await asyncio.sleep(3)
                await self.wait_for_worker_join(is_retry=True)

        self.broker.clear_queue_messages()
        return joined_workers

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

    async def deploy_model(self) -> None:
        if self.execution_type is ExecutionType.SingleModelSingleConf:
            self.broker.broadcast(WorkerCommand.DeployModel,
                                  self.models[0].to_dict())
        elif self.execution_type is ExecutionType.SingleModelMultiConf:
            self.broker.broadcast(WorkerCommand.DeployModel,
                                  self.models[0].to_dict())
        else:
            for n, queue_id in enumerate(self.broker.queue_ids):
                log.debug(
                    'Deploying model to queue {} with id {}'.format(n, queue_id))
                self.broker.send_to_queue(
                    queue_id, WorkerCommand.DeployModel, self.models[n].to_dict())

        results = await self.broker.get_all_results(timeout=10)
        for queue_id, results in results.items():
            for message in results:
                if message == 'model_deployed':
                    self.queue_models_deployed[queue_id] = True
                else:
                    log.warn(
                        'Worker on Queue %s didn\'nt successfully deploy model: "%s"', queue_id, message)
                    log.warn('Results: ' + repr(results))

        assert not any((not model_deployed for queue_id, model_deployed in self.queue_models_deployed.items())), \
            'Not all queues reported a deployed model'

        log.debug('queue.models_deployed() finished')

        self.models_deployed = True
        self.broker.clear_queue_messages()

    async def submit(self) -> List[Job]:
        if not self.models_deployed:
            raise AssertionError(
                'Trying to submit job without deploying model')

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
        if not self.models_deployed:
            raise AssertionError(
                'wait_for_results called but no models are deployed')
        if len(self.jobs) == 0:
            raise AssertionError(
                'wait_for_results called but no jobs submitted')

        results = await self.broker.get_all_results(timeout=50.0)
        for job in self.jobs:
            for queue_id in job.submitted_to:
                for message in results[queue_id]:
                    if message.get('failure') is not None:
                        job.failure = message.get('failure')
                    else:
                        job.values.append(message['values'])
                        job.results.append(message['states'])
