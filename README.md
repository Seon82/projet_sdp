# projet_sdp
[![Linter Actions Status](https://github.com/Seon82/projet_sdp/actions/workflows/lint.yml//badge.svg?branch=main)](https://github.com/Seon82/projet_sdp/actions)

Notre projet d'optimisation pour l'entreprise fictive CompuOpti, réalisé dans le cadre du cours de SDP. Celui-ci permet:

* De charger des json décrivant le problème.
* De modéliser et résoudre le problème en gurobi.
* De visualiser les plannings générés.
* De trouver les solutions non-dominées à l'aide d'un algorithme ε-constraint.
* De simuler un décideur et d'apprendre ses préférences.

## Installation
Ce package nécessite `python>=3.10` ainsi qu'une installation gurobi.

* Cloner le repo.
* Exécuter `pip install .` depuis la racine du projet pour l'installer avec ses dépendances.

## Démarrage

Des notebooks présentant le package et ses principales fonctions sont disponibles dans le répertoire [`examples`](./examples/).


