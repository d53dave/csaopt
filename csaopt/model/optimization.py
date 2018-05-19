from model import RandomDistribution, Precision
from typing import Sequence

# Configuration

def distribution() -> RandomDistribution:
    pass


def precision() -> Precision:
    pass


def dimensions() -> int:
    pass

# Functions


def generate_next(state: object, randoms: Sequence[float]) -> object:
    pass


def initialize(state: object, randoms: Sequence[float]) -> object:
    pass


def cool(old_temp: float) -> float:
    pass


def acceptance_func(e1: float, e2: float, temp: float) -> bool:
    pass


def evaluate(state: object) -> float:
    pass
