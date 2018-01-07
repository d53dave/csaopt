__all__ = ['model_loader', 'model_validator']
import ujson

from typing import Dict
from ..model.optimization import Precision, RandomDistribution


class ValidationError(Exception):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class Model:
    def __init__(self, name: str,
                 dimensions: int,
                 precision: Precision,
                 random_distr: RandomDistribution,
                 functions: Dict[str, str]) -> None:
        self.name: str = name
        self.dimensions: int = dimensions
        self.random_dist: RandomDistribution = random_distr
        self.precision: Precision = precision
        self.functions: Dict[str, str] = functions

    def __str__(self) -> str:
        return ujson.dumps(self, indent=4)
