from . import Job
from . import SubmissionResult
from ..msgqclient.client import QueueClient


class JobManager():
    """This class handles submission, tracking and retrieval of optimization jobs.

    This abstracts away the detailed communication with the message queue through
    the msgqueue client class.
    
    """
    def __init__(self, msgqueue_client: QueueClient):
        self.queue = msgqueue_client

    def submit(self, job: Job) -> SubmissionResult:
        self.queue.submit_job(job)
