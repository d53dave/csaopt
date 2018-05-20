import math

from csaopt.model import RandomDistribution, Precision
from typing import MutableSequence, Sequence, Any, Tuple
from math import pi


# -- Globals

m = 5
c = (1, 2, 5, 2, 3)
A = ((3, 5), (5, 2), (2, 1), (1, 4), (7, 9))

# -- Globals


# Configuration

def distribution() -> RandomDistribution:
    return RandomDistribution.Normal


def precision() -> Precision:
    return Precision.Float32


def dimensions() -> int:
    return 2


def get_state_shape() -> Tuple:
    return (3,)


def context() -> Sequence:
    pass


# Functions


def copy_state(src: Sequence, dst: MutableSequence):
    # print('Copying ' + str(src) + ' to '  + str(dst))
    for i in range(len(src)):
        dst[i] = src[i]


def cool(old_temp: float, step_ratio: float, ctx: Sequence) -> float:
    return old_temp * 0.96


def acceptance_func(e1: float, e2: float, temp: float, ctx: Any) -> bool:
    return math.exp(-(e2 - e1) / temp) > 0.5


def empty_state(state: MutableSequence):
    for i in range(len(state)):
        state[i] = 0.0


def initialize(state: MutableSequence, randoms: Sequence[float], ctx: Sequence) -> None:
    for i in range(len(randoms)):
        state[i] = randoms[i]


def evaluate(state: Sequence, ctx: Any) -> float:
    result = 0.0
    for i in range(m):  # sum from 0 to m-1
        t2 = 0.0
        for j in range(2):  # sum from 0..-1
            s_j = state[j]
            a_ij = A[i][j]
            t2 += (s_j - a_ij)**2
        t2 = -(1 / pi) * t2
        t3 = 0.0
        for j in range(2):  # sum from 0..d-1
            t3 += (state[j] - A[i][j])**2
        t3 = pi * t3
        result += c[i] * math.exp(t2) * math.cos(t3)
    return -result


def generate_next(state: Sequence, new_state: MutableSequence, randoms: Sequence[float]) -> Any:
    for i in range(len(state)):
        new_state[i] = state[i] + randoms[i]
