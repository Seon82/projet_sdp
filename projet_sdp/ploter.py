import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from .model import Model


class Ploter:
    def __init__(self, model: Model):
        self.model = model
        self.labels = model.data._qualifications_names + ["X"]
        _aux = plt.cm.get_cmap("hsv", len(self.labels))
        self.colors = [_aux(index) for index in range(len(self.labels) - 1)] + [(0, 0, 0, 1)]
        self._matrix = self._createMatrix()
        self._completion_day = [self._get_completion_day(p) for p in range(self.model.data.P)]

    def determine_qualification(self, p, e, j):
        conges = self.model.data.conges(e)
        work_day = list(map(lambda x: x.X, self.model._projet[e, j, p, :]))
        if sum(work_day) == 1:
            return self.labels[np.argmax(work_day)]
        elif j in conges:
            return "X"
        return None

    def _createMatrix(self):
        """
        Creating a matrix project-jour-employe to determine the task done
        """
        matrix = np.zeros((self.model.data.P, self.model.data.E, self.model.data.N), dtype="object")
        for p in range(self.model.data.P):
            for e in range(self.model.data.E):
                for j in range(self.model.data.N):
                    matrix[p, e, j] = self.determine_qualification(p, e, j)
        return matrix

    def matrix(self, p, e, j):
        return self._matrix[p, e, j]

    def _get_completion_day(self, p):
        for j in range(self.model.data.N):
            if self.model.realise(p, j).X == 1:
                return j
        return None

    def completion_day(self, p):
        return self._completion_day[p]

    def _gantt_project(self, ax: plt.Axes, p):
        data = self._matrix[p, :, :]
        columns = [day for day in range(self.model.data.N)]
        columns_colors = list(
            map(
                lambda day: (1 - (day == self.model.data.due_date(p)), 1 - (day + 1 == self.completion_day(p)), 1, 1),
                [day for day in range(self.model.data.N)],
            )
        )
        rows = [self.model.data.employee_name(e) for e in range(self.model.data.E)]

        # Setting colors
        colors = []
        aux = []
        for employee in data:
            aux = []
            for qualification in employee:
                if qualification is None:
                    aux.append((0, 0, 0, 0))
                else:
                    aux.append(self.colors[self.labels.index(qualification)])
            colors.append(aux.copy())

        qualis_required = [
            (self.model.data.qualification_name(q), self.model.data.duree(p, q)) for q in range(self.model.data.Q)
        ]
        ax.set_title(f"Project {self.model.data.projet_name(p)} {qualis_required}")
        ax.table(
            data,
            rowLabels=rows,
            colLabels=columns,
            colColours=columns_colors,
            loc="center",
            cellLoc="center",
            cellColours=colors,
        )
        # ax.vlines([0,1,2,3,4],0, 10, linestyles="solid")

    def gantt_projects(self):
        fig, gnt = plt.subplots(self.model.data.P, figsize=(20, self.model.data.P * 2))
        if type(gnt) != np.ndarray:
            gnt = [gnt]
        fig.tight_layout()
        for p in range(self.model.data.P):
            gnt[p].axis("off")
            gnt[p].axis("tight")
            self._gantt_project(gnt[p], p)
        colors = [Patch(color=(1, 0, 1, 1)), Patch(color=(0, 1, 1, 1)), Patch(color=(0, 0, 1, 1))] + [
            Patch(color=color) for color in self.colors
        ]
        labels = ["Completion Day", "Due Date", "Completion Day and Due Date"] + self.labels
        fig.legend(handles=colors, labels=labels, loc="upper right")
        plt.show()

    def _gantt_employee(self, ax: plt.Axes, e):
        data = self._matrix[:, e, :]
        columns = [day for day in range(self.model.data.N)]
        rows = [self.model.data.projet_name(p) for p in range(self.model.data.P)]

        # Setting colors
        colors = []
        aux = []
        for employee in data:
            aux = []
            for qualification in employee:
                if qualification is None:
                    aux.append((0, 0, 0, 0))
                else:
                    aux.append(self.colors[self.labels.index(qualification)])
            colors.append(aux.copy())

        qualifications = list(map(lambda q: self.model.data.qualification_name(q), self.model.data.qualifications(e)))

        ax.set_title(f"Employee {self.model.data.employee_name(e)} {qualifications}")
        ax.table(data, rowLabels=rows, colLabels=columns, loc="center", cellLoc="center", cellColours=colors)

    def gantt_employees(self):
        fig, gnt = plt.subplots(self.model.data.E, figsize=(20, self.model.data.E * 2))
        fig.tight_layout()
        for e in range(self.model.data.E):
            gnt[e].axis("off")
            gnt[e].axis("tight")
            self._gantt_employee(gnt[e], e)
        fig.legend(handles=[Patch(color=color) for color in self.colors], labels=self.labels, loc="upper right")
        plt.show()
