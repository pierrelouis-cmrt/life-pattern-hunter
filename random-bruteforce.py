#!/usr/bin/env python3
import argparse
import random
from dataclasses import dataclass


ROWS = 24
COLS = 24
MARGE_RECHERCHE = 4
MAX_MARGE_RECHERCHE = 10

TAILLE_POPULATION = 120
NB_ESSAIS_AMELIORATION_LOCALE = 18
NB_GENERATIONS_GENETIQUES_MAX = 420

DENSITES = [0.08, 0.14, 0.20, 0.28, 0.36, 0.23]

PENALITE_FAUX_NEGATIF = 4
PENALITE_FAUX_POSITIF = 1
PENALITE_DISTANCE_EXTRA = 0.12
PENALITE_CELLULE_INITIALE = 0.001


@dataclass
class Evaluation:
    score_tri: float
    erreur: float
    exactitude: float
    candidat: list
    resultat: list
    iteration: int
    sample_index: int


@dataclass
class RunResult:
    run: int
    meilleure: Evaluation
    iterations: int
    candidats_testes: int
    solution_exacte: bool


def nouvelle_grille(valeur=0):
    return [[valeur for _ in range(COLS)] for _ in range(ROWS)]


def copier_grille(grille):
    return [ligne[:] for ligne in grille]


def nombre_cellules_vivantes(grille):
    return sum(sum(ligne) for ligne in grille)


def compter_voisins(grille, ligne, col):
    total = 0
    for dl in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dl == 0 and dc == 0:
                continue
            nl = ligne + dl
            nc = col + dc
            if 0 <= nl < ROWS and 0 <= nc < COLS:
                total += grille[nl][nc]
    return total


def generation_suivante(grille):
    suivante = nouvelle_grille(0)
    for i in range(ROWS):
        for j in range(COLS):
            voisins = compter_voisins(grille, i, j)
            if grille[i][j] == 1 and voisins in (2, 3):
                suivante[i][j] = 1
            elif grille[i][j] == 0 and voisins == 3:
                suivante[i][j] = 1
    return suivante


def simuler(grille_initiale, nb_generations):
    grille = copier_grille(grille_initiale)
    for _ in range(nb_generations):
        grille = generation_suivante(grille)
    return grille


def construire_cible(nom):
    cible = nouvelle_grille(0)
    top = ROWS // 2 - 1
    left = COLS // 2 - 1

    motifs = {
        "block": [(0, 0), (0, 1), (1, 0), (1, 1)],
        "blinker": [(1, 0), (1, 1), (1, 2)],
        "glider": [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)],
    }

    for dr, dc in motifs[nom]:
        cible[top + dr][left + dc] = 1
    return cible


def construire_carte_distance_cible(cible):
    cellules_cibles = []
    for i in range(ROWS):
        for j in range(COLS):
            if cible[i][j] == 1:
                cellules_cibles.append((i, j))

    carte = [[MAX_MARGE_RECHERCHE + 1 for _ in range(COLS)] for _ in range(ROWS)]
    if not cellules_cibles:
        return carte

    for i in range(ROWS):
        for j in range(COLS):
            meilleur = MAX_MARGE_RECHERCHE + 1
            for ci, cj in cellules_cibles:
                distance = max(abs(i - ci), abs(j - cj))
                if distance < meilleur:
                    meilleur = distance
            carte[i][j] = meilleur
    return carte


def calculer_zone_recherche(cible, steps):
    lignes = []
    cols = []
    for i in range(ROWS):
        for j in range(COLS):
            if cible[i][j] == 1:
                lignes.append(i)
                cols.append(j)

    if not lignes:
        return (0, ROWS - 1, 0, COLS - 1)

    marge = max(MARGE_RECHERCHE, min(MAX_MARGE_RECHERCHE, steps + 2))
    lmin = max(0, min(lignes) - marge)
    lmax = min(ROWS - 1, max(lignes) + marge)
    cmin = max(0, min(cols) - marge)
    cmax = min(COLS - 1, max(cols) + marge)
    return (lmin, lmax, cmin, cmax)


def erreur_par_rapport_a_cible(resultat, cible, carte_distance):
    erreur = 0
    for i in range(ROWS):
        for j in range(COLS):
            r = resultat[i][j]
            c = cible[i][j]
            if c == 1 and r == 0:
                erreur += PENALITE_FAUX_NEGATIF
            elif c == 0 and r == 1:
                erreur += PENALITE_FAUX_POSITIF
                erreur += min(carte_distance[i][j], MAX_MARGE_RECHERCHE) * PENALITE_DISTANCE_EXTRA
    return erreur


def score_exactitude(resultat, cible):
    identiques = 0
    for i in range(ROWS):
        for j in range(COLS):
            if resultat[i][j] == cible[i][j]:
                identiques += 1
    return 100.0 * identiques / (ROWS * COLS)


def candidat_aleatoire_pur(zone, rng):
    grille = nouvelle_grille(0)
    densite = rng.choice(DENSITES)
    lmin, lmax, cmin, cmax = zone
    for i in range(lmin, lmax + 1):
        for j in range(cmin, cmax + 1):
            if rng.random() < densite:
                grille[i][j] = 1
    return grille


def evaluer_candidat(candidat, cible, steps, carte_distance, iteration, sample_index):
    resultat = simuler(candidat, steps)
    erreur = erreur_par_rapport_a_cible(resultat, cible, carte_distance)
    score_tri = erreur + nombre_cellules_vivantes(candidat) * PENALITE_CELLULE_INITIALE
    return Evaluation(
        score_tri=score_tri,
        erreur=erreur,
        exactitude=score_exactitude(resultat, cible),
        candidat=copier_grille(candidat),
        resultat=resultat,
        iteration=iteration,
        sample_index=sample_index,
    )


def run_bruteforce(run_index, cible, steps, max_iterations, samples_per_iteration, rng):
    zone = calculer_zone_recherche(cible, steps)
    carte_distance = construire_carte_distance_cible(cible)
    meilleure = None
    candidats_testes = 0

    for iteration in range(1, max_iterations + 1):
        for sample_index in range(1, samples_per_iteration + 1):
            candidat = candidat_aleatoire_pur(zone, rng)
            evaluation = evaluer_candidat(
                candidat,
                cible,
                steps,
                carte_distance,
                iteration,
                sample_index,
            )
            candidats_testes += 1

            if meilleure is None or evaluation.score_tri < meilleure.score_tri:
                meilleure = evaluation

            if evaluation.erreur == 0:
                return RunResult(run_index, meilleure, iteration, candidats_testes, True)

    return RunResult(run_index, meilleure, max_iterations, candidats_testes, False)


def afficher_grille(titre, grille):
    print(titre)
    for ligne in grille:
        print("".join("#" if cellule else "." for cellule in ligne))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Baseline brute force aleatoire pour la reverse search du jeu de la vie."
    )
    parser.add_argument("--target", choices=("block", "blinker", "glider"), default="block")
    parser.add_argument("--steps", type=int, default=5)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--max-iterations", type=int, default=NB_GENERATIONS_GENETIQUES_MAX)
    parser.add_argument(
        "--samples-per-iteration",
        type=int,
        default=TAILLE_POPULATION + NB_ESSAIS_AMELIORATION_LOCALE,
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--show-best", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.steps < 1:
        raise SystemExit("--steps doit etre superieur ou egal a 1")
    if args.runs < 1:
        raise SystemExit("--runs doit etre superieur ou egal a 1")
    if args.max_iterations < 1:
        raise SystemExit("--max-iterations doit etre superieur ou egal a 1")
    if args.samples_per_iteration < 1:
        raise SystemExit("--samples-per-iteration doit etre superieur ou egal a 1")

    rng = random.Random(args.seed)
    cible = construire_cible(args.target)
    results = []

    print("Baseline brute force aleatoire")
    print("Target:", args.target)
    print("Steps:", args.steps)
    print("Runs:", args.runs)
    print("Max iterations par run:", args.max_iterations)
    print("Candidats par iteration:", args.samples_per_iteration)
    print("Budget theorique par run: O(I * (P + L) * X * N)")
    print()

    for run_index in range(1, args.runs + 1):
        result = run_bruteforce(
            run_index,
            cible,
            args.steps,
            args.max_iterations,
            args.samples_per_iteration,
            rng,
        )
        results.append(result)
        status = "solution exacte" if result.solution_exacte else "solution imparfaite"
        print(
            "Run {run}: {status}, erreur={erreur:.3f}, exactitude={exactitude:.2f}%, "
            "iterations={iterations}, meilleur_a_iteration={best_iteration}, candidats={candidats}".format(
                run=result.run,
                status=status,
                erreur=result.meilleure.erreur,
                exactitude=result.meilleure.exactitude,
                iterations=result.iterations,
                best_iteration=result.meilleure.iteration,
                candidats=result.candidats_testes,
            )
        )

    best = min(results, key=lambda item: item.meilleure.score_tri)
    successes = [item for item in results if item.solution_exacte]
    total_candidates = sum(item.candidats_testes for item in results)

    print()
    print("Resume")
    print("Meilleure erreur:", "{:.3f}".format(best.meilleure.erreur))
    print("Meilleure exactitude:", "{:.2f}%".format(best.meilleure.exactitude))
    print("Iteration ou la meilleure solution a ete trouvee:", best.meilleure.iteration)
    print("Total candidats testes:", total_candidates)
    print("Runs exacts:", "{}/{}".format(len(successes), args.runs))

    if successes:
        moyenne_iterations = sum(item.iterations for item in successes) / len(successes)
        print(
            "Moyenne des iterations necessaires sur les runs reussis:",
            "{:.2f}".format(moyenne_iterations),
        )
    else:
        print("Aucune solution exacte trouvee sur ces runs.")

    if args.show_best:
        print()
        afficher_grille("Meilleure grille initiale:", best.meilleure.candidat)
        print()
        afficher_grille("Resultat simule:", best.meilleure.resultat)


if __name__ == "__main__":
    main()
