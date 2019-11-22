# Rastrigin Function
# https://www.sfu.ca/~ssurjano/rastr.html
#
# Dimensions: d
#
# The Rastrigin function has several local minima. It is highly multimodal, but locations of the minima are regularly
# distributed.
#
# Input Domain:
# The function is usually evaluated on the hypercube xi in [-5.12, 5.12], for all i = 1, ..., d.
#
# Global Minimum:
# f(x*) = 0, at (0, 0, 0, 0)
#
# References:
# Global Optimization Test Problems. Retrieved June 2013, from
# http://www-optima.amp.i.kyoto-u.ac.jp/member/student/hedar/Hedar_files/TestGO.htm.

# Pohlheim, H. GEATbx Examples: Examples of Objective Functions (2005). Retrieved June 2013, from http://www.geatbx.com/download/GEATbx_ObjFunExpl_v37.pdf.

import math

from csaopt.model import RandomDistribution, Precision
from csaopt.utils import clamp
from csaopt.utils import FakeCuda as cuda
from typing import MutableSequence, Sequence, Any, Tuple
from math import pi

# Configuration

# -- Globals

max_steps = 320


@cuda.jit(device=True)
def scale(val, old_min, old_max, new_min, new_max):
    return (val - old_min) / (old_max - old_min) * (new_max - new_min) + new_min


@cuda.jit(device=True, inline=True)
def copy_state(b, a):
    for i in range(len(b)):
        a[i] = b[i]


# -- Globals


def distribution() -> RandomDistribution:
    return RandomDistribution.Uniform


def precision() -> Precision:
    return Precision.Float64


def dimensions() -> int:
    return 2


def empty_state() -> Tuple:
    return (0.0, 0.0)


# Functions


def cool(initial_temp: float, old_temp: float, step: int) -> float:
    return (1 - 0.3) * old_temp


def acceptance_func(e_old: float, e_new: float, temp: float, rnd: float) -> float:
    # prevent math.exp from under or overflowing, we can anyway constrain 0 < e^x <= (e^0 == 1)
    x = clamp(-80, -(e_new - e_old) / temp, 0.1)
    return math.exp(x) >= rnd


def initialize(state: MutableSequence, randoms: Sequence[float]) -> None:
    for i in range(len(state)):
        state[i] = scale(randoms[i], 0.0, 1.0, -5.12, 5.12)
    return


def evaluate(state: Sequence) -> float:
    d = len(state)
    t1 = 0.0
    for i in range(d):
        x_i = state[i]
        t1 += x_i * x_i - 10 * math.cos(2 * pi * x_i)
    return 10 * d + t1


def generate_next(state: Sequence, new_state: MutableSequence, randoms: Sequence[float], step: int) -> Any:
    d = len(state)
    for dim in range(d):
        delta = (randoms[dim] - 0.5) * 7 * (1 - float(step) / max_steps * 1.1)
        new_val = state[dim] + delta
        # print('New val', new_val, 'at scale 1 -', step, '/', max_steps, '=',
        #   1 - (float(step) / max_steps))
        if new_val > 5.12 or new_val < -5.12:
            new_val = state[dim] - delta
        new_state[dim] = new_val
        return