import random

from .loader import Data


def generate_random(N: int, E: int, P: int, Q: int) -> Data:
    _employees_names = [f"employee#{e}" for e in range(E)]
    _qualifications_names = [f"qual#{q}" for q in range(Q)]
    _projects_names = [f"project#{p}" for p in range(P)]

    _qualifications = [random.sample(range(Q), random.randint(1, Q - 1)) for e in range(E)]
    _conges = [random.sample(range(N), random.randint(0, int(0.5 * N))) for e in range(E)]

    _duree = [[random.randint(0, 5) for q in range(Q)] for p in range(P)]

    _gain = [random.randint(1, 100) for p in range(P)]
    _due_date = [random.randint(1, N + 1) for p in range(P)]
    _penalty = [random.randint(1, 100) for p in range(P)]

    return Data(
        N,
        E,
        Q,
        P,
        _qualifications,
        _conges,
        _duree,
        _gain,
        _due_date,
        _penalty,
        _employees_names,
        _qualifications_names,
        _projects_names,
    )
