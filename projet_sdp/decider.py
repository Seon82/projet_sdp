from typing import Tuple


class Decider:
    def __init__(self) -> None:
        pass

    def decide(self, scores: Tuple[int, int, int]) -> bool:
        # objectives: (max gain, min numbre affectation, min duree total)
        # scores signs: (+, -, -)
        gain, affectations, duree_total = scores

        total_score = 3 * gain + 2 * affectations + duree_total

        if total_score <= 0:
            return False
        return True
