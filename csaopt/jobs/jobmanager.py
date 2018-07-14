import asyncio

from . import Job
from ..model import Model
from ..msgqclient.client import QueueClient


class JobManager():
    """This class handles submission, tracking and retrieval of optimization jobs.

    This abstracts away the detailed communication with the message queue through
    the msgqueue client class.

    """
    def __init__(self, ctx, queue_client: QueueClient, model: Model) -> None:
        self.queue: QueueClient = queue_client
        self.model_deployed = False
        self.opt_conf = ctx.config['optimization']
        self.job = Job(model, self.opt_conf)

    async def deploy_model(self):
        await self.queue.deploy_model(self.job.model)

    async def submit(self) -> Job:
        if not self.model_deployed:
            raise AssertionError('Trying to submit job without deploying model')
        await self.queue.submit_job(self.job)
        self.job.was_submitted = True
        return self.job

    async def wait_for_results(self) -> Job:
        while not self.job.completed:
            asyncio.sleep(2.5)
        return self.job
