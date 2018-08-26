from model import RandomDistribution, Precision
from typing import Sequence, Tuple


# Configuration


def distribution() -> RandomDistribution:
    pass


def precision() -> Precision:
    pass


def dimensions() -> int:
    pass


def empty_state() -> Tuple:
    pass


# Functions


def generate_next(state: object, randoms: Sequence[float]) -> object:
    pass


def initialize(state: object, randoms: Sequence[float]) -> object:
    pass


def cool(initial_temp: float, old_temp: float, step: int) -> float:
    pass


def acceptance_func(e1: float, e2: float, temp: float) -> bool:
    pass


def evaluate(state: object) -> float:
    pass
