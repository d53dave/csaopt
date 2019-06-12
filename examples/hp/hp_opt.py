import math

from typing import List, Tuple, MutableSequence, Sequence, Collection, Any

from csaopt.utils import clamp

# -- Globals

hp_str = 'PHHPPHPHPPHPHPHPPHPPHHHHH'
eps = -1
h_idxs = [idx for idx, mm in enumerate(hp_str) if mm == 'H']

# -- Globals

Chain2d = List[Tuple[int, int, int, int]]


def empty_state() -> Collection:
    return [(0, 0, 0, 0)] * len(hp_str)


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
    num_hs = len(h_idxs)
    num_contacts = 0
    # contacts: List[Tuple[int, int]] = []
    for i in range(num_hs):
        for j in range(i + 1, num_hs):
            h2 = h_idxs[j]
            h1 = h_idxs[i]
            if (h2 - h1) >= 3:
                # if the distance between the two hydrophobic monomers is greater than 3, they could be in contact
                d = float(state[h1][1] - state[h2][1])**2 +\
                    float(state[h1][2] - state[h2][2])**2  # euclidean distance
                if d < 1.05:  # if the distance is one, they are in contact
                    num_contacts += 1

    return num_contacts * eps


def rigid_rotation(chain: Chain2d, idx: int = 0, clckwise: bool = False):
    rot = 1 if clckwise else -1

    # Mutate the rest of the chain by the chosen rotation, starting from idx
    for i in range(idx, len(chain)):
        chain[i][3] = (chain[i][3] + rot) % 4


def crankshaft(chain: Chain2d, idx: int):
    tmp1 = chain[idx][3]
    tmp2 = chain[idx + 1][3]
    if tmp1 != tmp2:
        chain[idx][3] = tmp2
        chain[idx + 1][3] = tmp1


def three_bead_flip(chain, idx):
    pass


def generate_next(state: Sequence, new_state: MutableSequence, randoms: Sequence[float], step) -> Any:
    idx = int(math.floor((len(state) - 1.0001) * randoms[0]))

    for i in range(len(state)):
        new_state[i] = state[i]

    if randoms[1] < 0.3 or idx > (len(state) - 3):
        # if the vec index is on the end, do an end flip
        clckwise = randoms[2] < 0.5
        rigid_rotation(new_state, idx, clckwise=clckwise)
    elif randoms[1] < 0.66:
        # do a three-bead flip, i.e. switch two adjacent {n,e,w,s} directions
        crankshaft(new_state, idx)
    else:
        three_bead_flip(new_state, idx)
