from . import Job
from . import SubmissionResult


class JobManager():
    """This class handles submission, tracking and retrieval of optimization jobs.

    This abstracts away the detailed communication with the message queue through
    the msgqueue client class.
    
    """
    def __init__(self):
        pass

    def submit(job: Job) -> SubmissionResult:
        pass
