"""Ackley Function
https://www.sfu.ca/~ssurjano/ackley.html

Description:
Dimensions: d

The Ackley function is widely used for testing optimization algorithms.
In its two-dimensional form, as shown in the plot [at the link above], it is characterized by a nearly flat outer
region, and a large hole at the centre. The function poses a risk for optimization algorithms, particularly
hillclimbing algorithms, to be trapped in one of its many local minima.

Recommended variable values are: a = 20, b = 0.2 and c = 2pi.

Input Domain:
The function is usually evaluated on the hypercube xi in [-32.768, 32.768], for all i = 1, ..., d,
although it may also be restricted to a smaller domain.

Global Minimum:
f(x*) = 0, at x* = (0, ..., 0)


References:

Adorio, E. P., & Diliman, U. P. MVF - Multivariate Test Functions Library in C for Unconstrained Global Optimization
(2005). Retrieved June 2013, from http://http://www.geocities.ws/eadorio/mvf.pdf.

Molga, M., & Smutnicki, C. Test functions for optimization needs (2005).
Retrieved June 2013, from http://www.zsd.ict.pwr.wroc.pl/files/docs/functions.pdf.

Back, T. (1996). Evolutionary algorithms in theory and practice: evolution strategies, evolutionary programming,
genetic algorithms. Oxford University Press on Demand. Global Optimization Test Functions Index. Retrieved June
2013, from http://infinity77.net/global_optimization/test_functions.html#test-functions-index.
"""

import math

from csaopt.utils import clamp
from csaopt.utils import FakeCuda as cuda
from typing import MutableSequence, Sequence, Any, Tuple
from math import pi

# -- Globals

a = 20
b = 0.2
c = 2 * pi
upper_bound = 32.768
lower_bound = -32.768
max_steps = 1000


@cuda.jit(device=True, inline=True)
def copy_state(b, a):
    for i in range(len(b)):
        a[i] = b[i]


@cuda.jit(device=True)
def scale(val, old_min, old_max, new_min, new_max):
    return (val - old_min) / (old_max - old_min) * (new_max - new_min) + new_min


# -- Globals

# Configuration


def empty_state() -> Tuple:
    return (0.0, 0.0)


# Functions


def cool(initial_temp: float, old_temp: float, step: int) -> float:
    return (1 - 0.14) * old_temp


def acceptance_func(e_old: float, e_new: float, temp: float, rnd: float) -> float:
    # prevent math.exp from under or overflowing, we can anyway constrain 0 < e^x <= (e^0 == 1)
    x = clamp(-80, -(e_new - e_old) / temp, 0.1)
    return math.exp(x) >= rnd


def initialize(state: MutableSequence, randoms: Sequence[float]) -> None:
    for i in range(len(state)):
        state[i] = scale(randoms[i], 0.0, 1.0, lower_bound, upper_bound)
    return


def evaluate(state: Sequence) -> float:
    d = len(state)
    t1_sum = 0.0
    t2_sum = 0.0
    for i in range(d):
        t1_sum += state[i] * state[i]
        t2_sum += math.cos(c * state[i])
    t1 = -a * math.exp(-b * math.sqrt(t1_sum / d))
    t2 = math.exp(t2_sum / d)
    return t1 - t2 + a + 2.71828182846


def generate_next(state: Sequence, new_state: MutableSequence, randoms: Sequence[float], step) -> Any:
    # i = int(randoms[0] * len(state)) % len(state)
    # delta = (randoms[dim] - 0.5) * 10 * (1 - float(step) / max_steps)
    d = len(state)
    for dim in range(d):
        if ((randoms[dim] * 100000) % 1 < 0.33):
            # skip with probability 0.66
            continue

        delta = scale(randoms[dim], 0.0, 1.0, lower_bound, upper_bound) * (1 - float(step) / (max_steps * 1.1))
        new_val = state[dim] + delta

        if new_val > 10 or new_val < -5:
            new_val = clamp(-5, state[dim] + delta, 10)

        new_state[dim] = new_val
        return  # empty return required by validator
