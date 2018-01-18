import uuid

from ..model import Model

__all__ = ['jobmanager']


class Job():
    def __init__(self, model: Model) -> None:
        self.id = str(uuid.uuid4())
        self.model = Model
        self.results = []

    def finished(self):
        return self.results is not None and len(self.results) > 0
