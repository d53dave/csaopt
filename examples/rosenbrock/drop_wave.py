"""Drop-Wave Function
https://www.sfu.ca/~ssurjano/drop.html

Dimensions: 2

The Drop-Wave function is multimodal and highly complex.

Input Domain:
The function is usually evaluated on the square xi in [-5.12, 5.12], for all i = 1, 2.

Global Minimum:
f(x*) = -1 at x* = (0, 0)

Reference:

Global Optimization Test Functions Index. Retrieved June 2013, from http://infinity77.net/global_optimization/test_functions.html#test-functions-index.
"""

import math

from csaopt.model import RandomDistribution, Precision
from typing import MutableSequence, Sequence, Any, Tuple
from math import pi

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
    return initial_temp * math.pow(0.95, step)


def acceptance_func(e1: float, e2: float, temp: float) -> bool:
    return math.exp(-(e2 - e1) / temp) > 0.5


def initialize(state: MutableSequence, randoms: Sequence[float]) -> None:
    for i in range(len(randoms)):
        state[i] = randoms[i]
    return


def evaluate(state: Sequence) -> float:
    x1 = state[0]
    x2 = state[1]
    t1 = x1 * x1 + x2 * x2
    return -((1 + math.cos(12 * math.sqrt(t1))) / (0.5 * t1 + 2))


def generate_next(state: Sequence, new_state: MutableSequence, randoms: Sequence[float]) -> Any:
    for i in range(len(state)):
        new_state[i] = clamp(-5.12, state[i] + randoms[i], 5.12)
    return
