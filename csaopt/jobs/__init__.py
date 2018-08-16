import uuid
import os

from enum import Enum
from tinynumpy import tinynumpy as np
from typing import Dict, List, Any, Tuple

from ..model import Model

__all__ = ['jobmanager']


class ExecutionType(Enum):
    MultiModelMultiConf = 'MultiModelMultiConf'
    SingleModelMultiConf = 'SingleModelMultiConf'
    SingleModelSingleConf = 'SingleModelSingleConf'
    MultiModelSingleConf = 'MultiModelSingleConf'


class Job():
    def __init__(self, model: Model, opt_params: Dict[str, Any]) -> None:
        self.id = str(uuid.uuid4())
        self.message_id: str = None
        self.model: Model = model
        self.results: List[List[np.ndarray]] = []
        self.values: List[List[float]] = []
        self.completed: bool = False
        self.submitted_to: List[str] = []
        self.params: Dict[str, Any] = opt_params

    def __repr__(self):
        return 'Job[{}]: Model={}, Submitted={}, Completed={}, Params={}'.format(
            self.id, self.model.name, self.was_submitted, self.completed, self.params)

    def to_dict(self):
        return {
            'id': self.id,
            'params': self.params,
            'model': self.model.name
        }

    def get_best_results(self) -> Tuple[float, np.ndarray]:
        values_ndarr = np.ndarray(self.values)
        ind = np.unravel_index(
            np.argmin(values_ndarr, axis=None), values_ndarr.shape)
        val_min = values_ndarr[ind]
        best_res = self.results[ind]
        return val_min, best_res

    def write_files(self, path: str, binary: bool = False) -> None:
        suffix: str = 'bin' if binary else 'txt'

        if(os.path.isdir(path)):
            for idx, result in enumerate(self.results):
                for inner_idx, ndarr in enumerate(result):
                    output_file_results = os.path.join(
                        path, '{}_data_{}{}.{}'.format(self.id, idx, inner_idx, suffix))
                    output_file_values = os.path.join(
                        path, '{}_data_{}{}.{}'.format(self.id, idx, inner_idx, suffix))
                    ndarr.tofile(output_file_results, sep=('' if binary else ','))
                    ndarr.tofile(output_file_values, sep=('' if binary else ','))
