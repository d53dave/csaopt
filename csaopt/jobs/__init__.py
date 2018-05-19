import uuid
import os

from tinynumpy import tinynumpy as np
from typing import Dict, List, Any

from ..model import Model

__all__ = ['jobmanager']


class Job():
    def __init__(self, model: Model, opt_params: Dict[str, Any]) -> None:
        self.id = str(uuid.uuid4())
        self.model = Model
        self.results: List[List[np.ndarray]] = []
        self.values: List[List[float]] = []
        self.finished = False

    def write_files(self, path: str, binary: bool = False) -> None:
        suffix = 'bin' if binary else 'txt'

        if(os.path.isdir(path)):
            for idx, result in enumerate(self.results):
                for inner_idx, ndarr in enumerate(result):
                    output_file_results = os.path.join(
                        path, '{}_data_{}{}.{}'.format(self.id, idx, inner_idx, suffix))
                    output_file_values = os.path.join(
                        path, '{}_data_{}{}.{}'.format(self.id, idx, inner_idx, suffix))
                    ndarr.tofile(output_file_results, sep=('' if binary else ','))
                    ndarr.tofile(output_file_values, sep=('' if binary else ','))
