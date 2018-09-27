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

from csaopt.model import RandomDistribution, Precision
from csaopt.utils import clamp
from typing import MutableSequence, Sequence, Any, Tuple
from math import pi

# -- Globals

a = 20
b = 0.2
c = 2 * pi

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
    return initial_temp * math.pow(0.97, step)


def acceptance_func(e_old: float, e_new: float, temp: float, rnd: float) -> float:
    # prevent math.exp from under or overflowing, we can anyway constrain 0 < e^x <= (e^0 == 1)
    x = clamp(-80, (e_old - e_new) / temp, 0.1)
    return math.exp(x) > rnd


def initialize(state: MutableSequence, randoms: Sequence[float]) -> None:
    generate_next(state, state, randoms, 0)  # just delegate to generate_next
    return


def evaluate(state: Sequence) -> float:
    d = 2
    t1_sum = 0.0
    t2_sum = 0.0

    for i in range(d):
        t1_sum += state[i] * state[i]
        t2_sum += math.cos(c * state[i])

    t1 = -a * math.exp(-b * math.sqrt(t1_sum / d))

    t2 = math.exp(t2_sum / d)

    return t1 - t2 + a + 2.71828182846
    # arg1 = -0.2 * math.sqrt(0.5 * (state[0]**2 + state[1]**2))
    # arg2 = 0.5 * (math.cos(2. * pi * state[0]) + math.cos(2. * pi * state[1]))
    # return -20. * math.exp(arg1) - math.exp(arg2) + 20. + 2.71828182846


def generate_next(state: Sequence, new_state: MutableSequence, randoms: Sequence[float], step) -> Any:
    for i in range(len(state)):
        new_state[i] = clamp(-32.768, 8 * randoms[i], 32.768)
    return
