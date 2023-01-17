import json
from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass
class Data:
    N: int
    E: int
    Q: int
    P: int

    # Caching values for functions
    _qualifications: List[int]
    _conges: List[int]
    _duree: List[List[int]]
    _gain: List[int]
    _due_date: List[int]
    _penalty: List[int]

    # Utils to map numbers to names
    _employees_names: List[str]
    _qualifications_names: List[str]
    _projects_names: List[str]

    M: int = 10e6

    def employee_name(self, e: int) -> str:
        return self._employees_names[e]

    def qualification_name(self, q: int) -> str:
        return self._qualifications_names[q]

    def qualifications(self, e: int) -> List[int]:
        return self._qualifications[e]

    def projet_name(self, p: int) -> str:
        return self._projects_names[p]

    def conges(self, e: int) -> List[int]:
        return self._conges[e]

    def duree(self, p: int, q: int) -> int:
        return self._duree[p][q]

    def gain(self, p: int) -> int:
        return self._gain[p]

    def due_date(self, p: int) -> int:
        return self._due_date[p]

    def penalite(self, p: int, j: int) -> int:
        if j > self.due_date(p):
            return self._penalty[p]
        return 0


def load_data_from_json(path: str) -> Data:
    with open(path) as file:
        json_data = json.load(file)

        _employees_names = list(map(lambda x: x["name"], json_data["staff"]))

        _projects_names = list(map(lambda x: x["name"], json_data["jobs"]))

        _qualifications_names = json_data["qualifications"]
        _qualifications = list(
            map(
                lambda x: list(map(lambda qual_name: _qualifications_names.index(qual_name), x["qualifications"])),
                json_data["staff"],
            )
        )

        E = len(_employees_names)
        Q = len(_qualifications_names)
        P = len(_projects_names)
        N = json_data["horizon"]

        _duree = list(
            map(lambda x: list(map(lambda job: job, x["working_days_per_qualification"].items())), json_data["jobs"])
        )

        for p in range(P):
            duree = list(np.zeros(shape=(Q), dtype=int))
            for workload in _duree[p]:
                index = _qualifications_names.index(workload[0])
                duree[index] = workload[1]
            _duree[p] = duree

        _conges = list(map(lambda x: list(np.array(x["vacations"]) - 1), json_data["staff"]))
        _gain = list(map(lambda x: x["gain"], json_data["jobs"]))
        _due_date = list(map(lambda x: x["due_date"] - 1, json_data["jobs"]))
        _penalty = list(map(lambda x: x["daily_penalty"], json_data["jobs"]))

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
