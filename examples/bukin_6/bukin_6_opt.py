# Bukin Function #6
# https://www.sfu.ca/~ssurjano/bukin6.html
#
# Dimensions: 2
# The sixth Bukin function has many local minima, all of which lie in a ridge.

# Input Domain:
# The function is usually evaluated on the rectangle x1 in [-15, -5], x2 in [-3, 3].

# Global Minimum:
# f(x*) = 0 at x* = (-10, 1)

# Reference:
# Global Optimization Test Functions Index. Retrieved June 2013, from http://infinity77.net/global_optimization/test_functions.html#test-functions-index.

import math

from csaopt.model import RandomDistribution, Precision
from csaopt.utils import clamp
from typing import MutableSequence, Sequence, Any, Tuple
from math import pi

# -- Globals

# -- Globals

# Configuration


def distribution() -> RandomDistribution:
    return RandomDistribution.Uniform


def precision() -> Precision:
    return Precision.Float32


def dimensions() -> int:
    return 2


def empty_state() -> Tuple:
    return (0.0, 0.0)


# Functions


def cool(initial_temp: float, old_temp: float, step: int) -> float:
    return initial_temp * math.pow(0.97, step)


def acceptance_func(e_old: float, e_new: float, temp: float, rnd: float) -> float:
    # prevent math.exp from under or overflowing, we can anyway constrain 0 < e^x <= (e^0 == 1)
    x = clamp(-80, (e_old - e_new) / temp, 0.1)
    return math.exp(x) > rnd


def initialize(state: MutableSequence, randoms: Sequence[float]) -> None:
    generate_next(state, state, randoms, 0)  # just delegate to generate_next
    return


def evaluate(state: Sequence) -> float:
    x1 = state[0]
    x2 = state[1]
    return 100 * math.sqrt(abs(x2 - 0.01 * x1 * x1)) + 0.01 * abs(x1 + 10)


def generate_next(state: Sequence, new_state: MutableSequence, randoms: Sequence[float], step) -> Any:
    new_state[0] = clamp(-15, (randoms[0] * 20) - 15, -5)
    new_state[1] = clamp(-3, (randoms[1] * 6) - 3, 3)
    return
