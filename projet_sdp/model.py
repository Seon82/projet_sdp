import gurobipy
import numpy as np
from loader import Data


class Model:
    def __init__(self, data: Data):
        self.model = gurobipy.Model()
        self.data = data

        self._projet = self._define_projet()
        self._realise = self._define_realise()
        self._affecte = self._define_affecte()
        self._debute = self._define_debute()

    def objective_max_gain(self):
        sum_gain = sum(self.data.gain(p) * self.realise(p, self.data.N - 1) for p in range(self.data.P))
        sum_penalite = sum(
            self.data.penalite(p, j) * (1 - self.realise(p, j - 1))
            for j in range(self.data.N)
            for p in range(self.data.P)
        )
        self.model.setObjective(sum_gain - sum_penalite, gurobipy.GRB.MAXIMIZE)

    def update(self):
        self.model.update()

    def optimize(self):
        self.model.optimize()

    def constraint_no_qual_work(self):
        for e in range(self.data.E):
            for j in range(self.data.N):
                for p in range(self.data.P):
                    for q in range(self.data.Q):
                        if q not in self.data.qualifications(e):
                            self.model.addConstr(self.projet(e, j, p, q) == 0)

    def constraint_one_project_per_day(self):
        for e in range(self.data.E):
            for j in range(self.data.N):
                sum_projet = sum(self.projet(e, j, p, q) for p in range(self.data.P) for q in range(self.data.Q))
                self.model.addConstr(sum_projet <= 1)

    def constraint_cant_work_on_days_off(self):
        for e in range(self.data.E):
            for p in range(self.data.P):
                for q in range(self.data.Q):
                    for j in self.data.conges(e):
                        self.model.addConstr(self.projet(e, j, p, q) == 0)

    def constraint_cant_work_more_than_needed(self):
        for p in range(self.data.P):
            for q in range(self.data.Q):
                sum_projet = sum(self.projet(e, j, p, q) for e in range(self.data.E) for j in range(self.data.N))
                self.model.addConstr(sum_projet <= self.data.duree(p, q))

    def determine_realise(self):
        for p in range(self.data.P):
            for j in range(self.data.N):
                sum_duree = sum(self.data.duree(p, q) for q in range(self.data.Q))
                sum_projet = sum(
                    self.projet(e, j_prime, p, q)
                    for j_prime in range(j + 1)
                    for e in range(self.data.E)
                    for q in range(self.data.Q)
                )
                self.model.addConstr(sum_duree - sum_projet <= self.data.M * (1 - self.realise(p, j)))

    def determine_affecte(self):
        for p in range(self.data.P):
            for e in range(self.data.E):
                sum_projet = sum(self.projet(e, j, p, q) for j in range(self.data.N) for q in range(self.data.Q))
                self.model.addConstr(sum_projet <= self.data.M * self.affecte(e, p))

    def determine_debute(self):
        for p in range(self.data.P):
            for j in range(self.data.N):
                sum_projet = sum(
                    self.projet(e, j_prime, p, q)
                    for j_prime in range(j + 1)
                    for q in range(self.data.Q)
                    for e in range(self.data.E)
                )
                self.model.addConstr(sum_projet <= self.data.M * self.debute(p, j))

    def _define_debute(self):
        _debute = np.ndarray(shape=(self.data.P, self.data.N), dtype=object)
        for p in range(self.data.P):
            for j in range(self.data.N):
                _debute[p, j] = self.model.addVar(name=f"[Debute]projet:{self.data.projet_name(p)}_jour:{j}", vtype="B")
        return _debute

    def debute(self, p, j):
        return self._debute[p, j]

    def _define_affecte(self):
        _affecte = np.ndarray(shape=(self.data.E, self.data.P), dtype=object)
        for e in range(self.data.E):
            for p in range(self.data.P):
                _affecte[e, p] = self.model.addVar(
                    name=f"[Affecte]employe:{self.data.employee_name(e)}_projet:{self.data.projet_name(p)}", vtype="B"
                )
        return _affecte

    def affecte(self, e, p):
        return self._affecte[e, p]

    def _define_realise(self):
        _realise = np.ndarray(shape=(self.data.P, self.data.N), dtype=object)
        for j in range(self.data.N):
            for p in range(self.data.P):
                _realise[p, j] = self.model.addVar(
                    name=f"[Realise]projet:{self.data.projet_name(p)}_jour:{j}", vtype="B"
                )
        return _realise

    def realise(self, p, j):
        return self._realise[p, j]

    def _define_projet(self):
        _projet = np.ndarray(shape=(self.data.E, self.data.N, self.data.P, self.data.Q), dtype=object)
        for e in range(self.data.E):
            for j in range(self.data.N):
                for p in range(self.data.P):
                    for q in range(self.data.Q):
                        _projet[e, j, p, q] = self.model.addVar(
                            name=f"[PROJET]employe:{self.data.employee_name(e)}_projet:{self.data.projet_name(p)}_qual:{self.data.qualification_name(q)}_jour:{j}",
                            vtype="B",
                        )
        return _projet

    def projet(self, e, j, p, q):
        return self._projet[e, j, p, q]
