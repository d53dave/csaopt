import asyncio
import logging
import numpy as np

from typing import List, Dict, Tuple, Any
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

    def __init__(self, ctx, broker: Broker, models: List[Model], configs: List[ConfigTree]) -> None:

        self.broker = broker
        self.models_deployed = False
        self.models = models
        self.configs = configs
        self.execution_type: ExecutionType = self._get_execution_type(models, configs)
        self.jobs: List[Job] = []
        self.worker_join_retry_delay = ctx.internal_config['broker.worker_join_retry_delay']
        self.worker_join_retry_count = ctx.internal_config['broker.worker_join_retry_count']
        if self.broker is not None:
            self.queue_models_deployed: Dict[str, bool] = {queue_id: False for queue_id in self.broker.queue_ids}

    async def wait_for_worker_join(self, retry_count=0) -> List[str]:
        """Send ping to each worker and wait for response.

        Workers are expected to join immediately as the jobmanager will be called only after the
        instances are initialized. To be somewhat relaxed regarding the startup of instances,
        the ping operation will be retried once after a retry delay specified in the internal configuration.

        Args:
            is_retry: Indicate if call is a retry (i.e. this method calls itself recursively when retrying)

        Returns:
            A list of worker IDs of the joined workers
        """
        joined_workers = []
        for queue_id in self.broker.queue_ids:
            try:
                if self.broker.ping(queue_id) is True:
                    joined_workers.append(queue_id)
                else:
                    raise AssertionError('Worker {} failed to join'.format(queue_id))
            except Exception as e:
                if retry_count >= self.worker_join_retry_count:
                    log.exception('Exception occurred while waiting for workers to join')
                    raise e

                log.debug('Retrying to contact broker in order to ping workers')
                await asyncio.sleep(self.worker_join_retry_delay)
                await self.wait_for_worker_join(retry_count + 1)

        self.broker.clear_queue_messages()
        return joined_workers

    # TODO: Fix type links in comments
    def _get_execution_type(self, models: List[Model], configs: List[ConfigTree]) -> ExecutionType:
        """Determine the execution type of a given optimization run based on the number of models and configurations

        Args:
            models: A list of Models
            configs: A list of Configurations

        Returns:
            The ExecutionType of this optimization run
        """
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
        """Deploy model to workers.

        This method will deploy models depending on the execution type (i.e. the configuration).
        - If the execution type is `SingleModelSingleConf` or `SingleModelMultiConf`, the model is broadcast to all
          workers
        - Otherwise, each worker will receive the deployment information for one model in the same order they were
          passed to CSAOpt.
        """
        if self.execution_type is ExecutionType.SingleModelSingleConf or \
           self.execution_type is ExecutionType.SingleModelMultiConf:
            self.broker.broadcast(WorkerCommand.DeployModel, self.models[0].to_dict())
        else:
            for n, queue_id in enumerate(self.broker.queue_ids):
                log.debug('Deploying model to queue {} with id {}'.format(n, queue_id))
                self.broker.send_to_queue(queue_id, WorkerCommand.DeployModel, self.models[n].to_dict())

        all_results = await self.broker.get_all_results(timeout=10)
        for queue_id, results in all_results.items():
            for message in results:
                if message == 'model_deployed':
                    self.queue_models_deployed[queue_id] = True
                else:
                    log.warning('Worker on Queue %s didn\'t successfully deploy model: "%s"', queue_id, message)

        assert not any((not model_deployed for queue_id, model_deployed in self.queue_models_deployed.items())), \
            'Not all queues reported a deployed model'

        log.debug('queue.models_deployed() finished')

        self.models_deployed = True
        self.broker.clear_queue_messages()

    async def submit(self) -> List[Job]:
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
        """

        """
        if not self.models_deployed:
            raise AssertionError('wait_for_results called but no models are deployed')
        if len(self.jobs) == 0:
            raise AssertionError('wait_for_results called but no jobs submitted')

        results = await self.broker.get_all_results(timeout=150.0)
        log.debug('Received results: {}'.format(results))
        for job in self.jobs:
            for queue_id in job.submitted_to:
                for message in results[queue_id]:
                    log.debug('Processing message on queue {}, result={}'.format(queue_id, message))
                    if message.get('failure') is not None:
                        job.failure = message.get('failure')
                    else:
                        job.values = message['values']
                        job.results = message['states']

    def scan_for_best_result(self, jobs: List[Job]) -> Tuple[Job, float, np.array]:
        """Get best performing job and it's results from a list of jobs

        Args:
            jobs: List of jobs to process

        Returns:
            A tuple of job, result and state at which the result was evaluated
        """
        if len(jobs) < 1:
            raise AssertionError('Cannot scan for best result on empty jobs list')

        best_job = jobs[0]
        best_value, best_state = best_job.get_best_results()

        for job in jobs[1:]:
            value, state = job.get_best_results()

            if value < best_value:
                best_value = value
                best_state = state
                best_job = job

        return best_job, best_value, best_state
