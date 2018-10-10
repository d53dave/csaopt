import math

from csaopt.model import RandomDistribution, Precision
from csaopt.utils import clamp
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


def empty_state() -> Tuple:
    return (0.0, 0.0)


# Functions


def cool(initial_temp: float, old_temp: float, step: int) -> float:
    return initial_temp * math.pow(0.9, step)


def acceptance_func(e_old: float, e_new: float, temp: float, rnd: float) -> bool:
    # prevent math.exp from under or overflowing, we can anyway constrain 0 < e^x <= (e^0 == 1)
    x = clamp(-80, (e_old - e_new) / temp, 0.1)
    return math.exp(x) > rnd


def initialize(state: MutableSequence, randoms: Sequence[float]) -> None:
    for i in range(len(randoms)):
        state[i] = randoms[i]
    return


def evaluate(state: Sequence) -> float:
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


def generate_next(state: Sequence, new_state: MutableSequence, randoms: Sequence[float], step: int) -> Any:
    for i in range(len(state)):
        new_state[i] = clamp(0, state[i] + 0.3 * randoms[i], 10)
    return
