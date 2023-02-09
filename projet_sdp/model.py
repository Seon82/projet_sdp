import gurobipy
import numpy as np

from .loader import Data


class Model:
    def __init__(self, data: Data):
        self.model = gurobipy.Model()
        self.data = data

        self._projet = self._define_projet()
        self._realise = self._define_realise()
        self._affecte = self._define_affecte()
        self._debute = self._define_debute()

    def objective_max_gain_func(self):
        sum_gain = sum(self.data.gain(p) * self.realise(p, self.data.N) for p in range(self.data.P))
        sum_penalite = sum(
            self.data.penalite(p, j) * (1 - self.realise(p, j)) for j in range(self.data.N) for p in range(self.data.P)
        )
        return sum_gain - sum_penalite

    def objective_max_gain(self):
        obj = self.objective_max_gain_func()
        self.model.setObjective(obj, gurobipy.GRB.MAXIMIZE)

    def objective_min_affecte_func(self):
        total_affectes = -sum(self.affecte(e, p) for e in range(self.data.E) for p in range(self.data.P))
        return total_affectes

    def objective_min_affecte(self):
        obj = self.objective_min_affecte_func()
        self.model.setObjective(obj, gurobipy.GRB.MAXIMIZE)

    def objective_min_length_func(self):
        total_lengths = sum(
            self.realise(p, j) - self.debute(p, j) for j in range(self.data.N) for p in range(self.data.P)
        )
        return total_lengths

    def objective_min_length(self):
        obj = self.objective_min_length_func()
        self.model.setObjective(obj, gurobipy.GRB.MAXIMIZE)

    def epsilon_constrained_method(self, quiet=True):
        if quiet:
            self.model.setParam("OutputFlag", 0)
        non_dominated = []
        self.model.setObjective(
            1_000_000 * self.objective_max_gain_func()
            + self.objective_min_affecte_func()
            + self.objective_min_length_func(),
            gurobipy.GRB.MAXIMIZE,
        )
        self.optimize()
        x = {var.VarName: var.X for var in self.model.getVars()}
        non_dominated.append({"var": x, "obj": self.objective_values()})

        # Determine min_epsilon_2
        min_epsilon_2 = self.objective_min_affecte_func().getValue()
        epsilon_3 = self.objective_min_length_func().getValue() + 1
        infeasible3 = False
        while not infeasible3:
            c_epsilon_3 = self.model.addConstr(self.objective_min_length_func() >= epsilon_3)
            try:
                self.optimize()
                x = {var.VarName: var.X for var in self.model.getVars()}
                non_dominated.append({"var": x, "obj": self.objective_values()})
                epsilon_3 = self.objective_min_length_func().getValue() + 1
                min_epsilon_2 = min(self.objective_min_affecte_func().getValue(), min_epsilon_2)

            except ValueError:
                infeasible3 = True

            finally:
                self.model.remove(c_epsilon_3)
                self.model.update()

        # Normal algorithm
        epsilon_2 = min_epsilon_2 + 1
        infeasible = False
        while not infeasible:
            c_epsilon_2 = self.model.addConstr(self.objective_min_affecte_func() >= epsilon_2)
            try:
                self.optimize()
                x = {var.VarName: var.X for var in self.model.getVars()}
                non_dominated.append({"var": x, "obj": self.objective_values()})
                epsilon_2 += 1

                epsilon_3 = self.objective_min_length_func().getValue() + 1
                infeasible3 = False
                while not infeasible3:
                    c_epsilon_3 = self.model.addConstr(self.objective_min_length_func() >= epsilon_3)
                    try:
                        self.optimize()
                        x = {var.VarName: var.X for var in self.model.getVars()}
                        non_dominated.append({"var": x, "obj": self.objective_values()})
                        epsilon_3 = self.objective_min_length_func().getValue() + 1

                    except ValueError:
                        infeasible3 = True

                    finally:
                        self.model.remove(c_epsilon_3)
                        self.model.update()

            except ValueError:
                infeasible = True

            finally:
                self.model.remove(c_epsilon_2)
                self.model.update()

        return non_dominated

    def objective_values(self):
        return (
            self.objective_max_gain_func().getValue(),
            self.objective_min_affecte_func().getValue(),
            self.objective_min_length_func().getValue(),
        )

    def update(self):
        self.model.update()

    def optimize(self):
        self.model.optimize()
        if self.model.status != gurobipy.GRB.OPTIMAL:
            raise ValueError("Model failed to find optimal solution")

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
            for j in range(self.data.N + 1):
                sum_duree = sum(self.data.duree(p, q) for q in range(self.data.Q))
                sum_projet = sum(
                    self.projet(e, j_prime, p, q)
                    for j_prime in range(min(j, self.data.N))
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
        _realise = np.ndarray(shape=(self.data.P, self.data.N + 1), dtype=object)
        for j in range(self.data.N + 1):
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
