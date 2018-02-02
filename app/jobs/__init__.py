import uuid

from typing import Dict, List, Any

from ..model import Model

__all__ = ['jobmanager']


class Job():
    def __init__(self, model: Model, opt_params: Dict[str, Any]) -> None:
        self.id = str(uuid.uuid4())
        self.model = Model
        self.results: List[List[Any]] = []
        self.values: List[List[float]] = []
        self.finished = False
