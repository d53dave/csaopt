import uuid
import os
import numpy as np

from enum import Enum
from typing import Dict, List, Any, Tuple, Optional, Type

from ..model import Model

__all__ = ['jobmanager']

Failure = Optional[Tuple[Optional[Type[BaseException]], Optional[BaseException], str]]


class ExecutionType(Enum):
    MultiModelMultiConf = 'MultiModelMultiConf'
    SingleModelMultiConf = 'SingleModelMultiConf'
    SingleModelSingleConf = 'SingleModelSingleConf'
    MultiModelSingleConf = 'MultiModelSingleConf'


class Job():
    def __init__(self, model: Model, opt_params: Dict[str, Any]) -> None:
        self.id = str(uuid.uuid4())
        self.message_id: str = ''
        self.queue_id: str = ''
        self.model: Model = model
        self.results: List[np.ndarray] = []
        self.values: List[float] = []
        self.completed: bool = False
        self.failure: Failure = None
        self.submitted_to: List[str] = []
        self.params: Dict[str, Any] = opt_params

    def __repr__(self):
        return 'Job[{}]: Model={}, Queues={}, Completed={}, Params={}'.format(
            self.id, self.model.name, self.submitted_to, self.completed, self.params)

    def to_dict(self):
        return {'id': self.id, 'params': self.params, 'model': self.model.name}

    def get_best_results(self) -> Tuple[float, np.ndarray]:
        values_ndarr = np.asarray(self.values)
        ind = np.unravel_index(np.argmin(values_ndarr, axis=None), values_ndarr.shape)
        val_min = values_ndarr[ind]
        best_res = self.results[ind]
        return val_min, best_res

    def write_files(self, path: str, binary: bool = False, only_best: bool = False) -> None:
        suffix: str = 'bin' if binary else 'txt'

        if (os.path.isdir(path)):
            if only_best:
                best_val, best_state = self.get_best_results()
                self._write_file('{}_values_{}.{}'.format(self.id, 'best', suffix), path, binary,
                                 np.asarray([best_val]))
                self._write_file('{}_states_{}.{}'.format(self.id, 'best', suffix), path, binary, best_state)
            else:
                for idx, result in enumerate(self.results):
                    self._write_file('{}_values_{}.{}'.format(self.id, idx, suffix), path, binary,
                                     np.ndarr([self.values[idx]]))
                    self._write_file('{}_states_{}.{}'.format(self.id, idx, suffix), path, binary, self.values[idx])
        else:
            raise AttributeError('Cannot write to {}: not a directory.'.format(path))

    def _write_file(self, name: str, path: str, binary: bool, ndarr: np.ndarray) -> None:
        output_file = os.path.join(path, name)
        ndarr.tofile(output_file, sep=('' if binary else ','))
