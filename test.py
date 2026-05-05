from dataclasses import dataclass
from typing import Callable, List, Tuple, Optional
import random


Grille = List[List[int]]
Zone = Tuple[int, int, int, int]
FonctionEvolution = Callable[[Grille], Grille]


@dataclass
class ParametresSolveur:
    taille_population: int = 120
    nb_elites: int = 14

    taux_mutation: float = 0.018
    taux_injection_aleatoire: float = 0.06
    densite_initiale: float = 0.23

    nb_generations_genetiques_max: int = 420
    nb_essais_amelioration_locale: int = 18

    marge_recherche: int = 4
    max_marge_recherche: int = 10

    penalite_faux_negatif: float = 4.0
    penalite_faux_positif: float = 1.0
    penalite_distance_extra: float = 0.12
    penalite_cellule_initiale: float = 0.001

    taille_cache_max: int = 8000


@dataclass
class ResultatSolveur:
    grille_initiale: Grille
    grille_finale: Grille
    erreur: float
    score_exactitude: float
    generation: int
    solution_exacte: bool


# ============================================================
#  OUTILS DE GRILLE
# ============================================================

def dimensions(grille: Grille) -> Tuple[int, int]:
    return len(grille), len(grille[0])


def nouvelle_grille(lignes: int, colonnes: int, valeur: int = 0) -> Grille:
    return [[valeur for _ in range(colonnes)] for _ in range(lignes)]


def copier_grille(grille: Grille) -> Grille:
    return [ligne[:] for ligne in grille]


def cle_grille(grille: Grille) -> Tuple[int, ...]:
    return tuple(cellule for ligne in grille for cellule in ligne)


def nombre_cellules_vivantes(grille: Grille) -> int:
    return sum(sum(ligne) for ligne in grille)


def cellules_zone(zone: Zone) -> List[Tuple[int, int]]:
    lmin, lmax, cmin, cmax = zone
    return [
        (i, j)
        for i in range(lmin, lmax + 1)
        for j in range(cmin, cmax + 1)
    ]


def simuler(
    grille_initiale: Grille,
    nb_generations: int,
    evolution: FonctionEvolution
) -> Grille:
    grille = copier_grille(grille_initiale)

    for _ in range(nb_generations):
        grille = evolution(grille)

    return grille


# ============================================================
#  ZONE DE RECHERCHE
# ============================================================

def calculer_zone_recherche(
    cible: Grille,
    nb_generations_inverse: int,
    params: ParametresSolveur
) -> Zone:
    lignes, colonnes = dimensions(cible)

    lignes_vivantes = []
    colonnes_vivantes = []

    for i in range(lignes):
        for j in range(colonnes):
            if cible[i][j] == 1:
                lignes_vivantes.append(i)
                colonnes_vivantes.append(j)

    if not lignes_vivantes:
        return (0, lignes - 1, 0, colonnes - 1)

    marge = max(
        params.marge_recherche,
        min(params.max_marge_recherche, nb_generations_inverse + 2)
    )

    lmin = max(0, min(lignes_vivantes) - marge)
    lmax = min(lignes - 1, max(lignes_vivantes) + marge)
    cmin = max(0, min(colonnes_vivantes) - marge)
    cmax = min(colonnes - 1, max(colonnes_vivantes) + marge)

    return (lmin, lmax, cmin, cmax)


def construire_carte_distance_cible(
    cible: Grille,
    params: ParametresSolveur
) -> Grille:
    lignes, colonnes = dimensions(cible)

    cellules_cibles = [
        (i, j)
        for i in range(lignes)
        for j in range(colonnes)
        if cible[i][j] == 1
    ]

    distance_defaut = params.max_marge_recherche + 1
    carte = nouvelle_grille(lignes, colonnes, distance_defaut)

    if not cellules_cibles:
        return carte

    for i in range(lignes):
        for j in range(colonnes):
            meilleure_distance = distance_defaut

            for ci, cj in cellules_cibles:
                distance = max(abs(i - ci), abs(j - cj))

                if distance < meilleure_distance:
                    meilleure_distance = distance

            carte[i][j] = meilleure_distance

    return carte


# ============================================================
#  ÉVALUATION
# ============================================================

def erreur_par_rapport_a_cible(
    resultat: Grille,
    cible: Grille,
    carte_distance: Grille,
    params: ParametresSolveur
) -> float:
    lignes, colonnes = dimensions(cible)
    erreur = 0.0

    for i in range(lignes):
        for j in range(colonnes):
            r = resultat[i][j]
            c = cible[i][j]

            if c == 1 and r == 0:
                erreur += params.penalite_faux_negatif

            elif c == 0 and r == 1:
                erreur += params.penalite_faux_positif
                erreur += (
                    min(carte_distance[i][j], params.max_marge_recherche)
                    * params.penalite_distance_extra
                )

    return erreur


def score_exactitude(resultat: Grille, cible: Grille) -> float:
    lignes, colonnes = dimensions(cible)
    total = lignes * colonnes
    identiques = 0

    for i in range(lignes):
        for j in range(colonnes):
            if resultat[i][j] == cible[i][j]:
                identiques += 1

    return 100.0 * identiques / total


def limiter_cache(cache: dict, taille_max: int) -> None:
    if len(cache) <= taille_max:
        return

    nb_a_supprimer = len(cache) - taille_max

    for cle in list(cache.keys())[:nb_a_supprimer]:
        del cache[cle]


def evaluer_individu(
    individu: Grille,
    cible: Grille,
    nb_generations_inverse: int,
    evolution: FonctionEvolution,
    carte_distance: Grille,
    cache: dict,
    params: ParametresSolveur
):
    cle = cle_grille(individu)

    if cle in cache:
        note_tri, erreur_cible, resultat = cache[cle]
        return note_tri, erreur_cible, individu, copier_grille(resultat)

    resultat = simuler(individu, nb_generations_inverse, evolution)

    erreur_cible = erreur_par_rapport_a_cible(
        resultat,
        cible,
        carte_distance,
        params
    )

    note_tri = (
        erreur_cible
        + nombre_cellules_vivantes(individu) * params.penalite_cellule_initiale
    )

    cache[cle] = (note_tri, erreur_cible, copier_grille(resultat))
    limiter_cache(cache, params.taille_cache_max)

    return note_tri, erreur_cible, individu, resultat


def evaluer_population(
    population: List[Grille],
    cible: Grille,
    nb_generations_inverse: int,
    evolution: FonctionEvolution,
    carte_distance: Grille,
    cache: dict,
    params: ParametresSolveur
):
    population_evaluee = [
        evaluer_individu(
            individu,
            cible,
            nb_generations_inverse,
            evolution,
            carte_distance,
            cache,
            params
        )
        for individu in population
    ]

    population_evaluee.sort(key=lambda x: x[0])
    return population_evaluee


# ============================================================
#  CRÉATION DES INDIVIDUS
# ============================================================

def individu_aleatoire_guide(
    cible: Grille,
    zone: Zone,
    carte_distance: Grille,
    densite: float,
    params: ParametresSolveur
) -> Grille:
    lignes, colonnes = dimensions(cible)
    individu = nouvelle_grille(lignes, colonnes, 0)

    lmin, lmax, cmin, cmax = zone

    for i in range(lmin, lmax + 1):
        for j in range(cmin, cmax + 1):
            distance = carte_distance[i][j]
            bonus_pres_cible = max(0, 4 - distance) * 0.035
            proba = min(0.55, densite + bonus_pres_cible)

            if random.random() < proba:
                individu[i][j] = 1

    return individu


def muter_zone_guidee(
    individu: Grille,
    zone: Zone,
    carte_distance: Grille,
    taux_mutation: float
) -> None:
    lmin, lmax, cmin, cmax = zone

    for i in range(lmin, lmax + 1):
        for j in range(cmin, cmax + 1):
            distance = carte_distance[i][j]
            proba = taux_mutation

            if distance <= 2:
                proba *= 1.35
            elif distance >= 7:
                proba *= 0.75

            if random.random() < proba:
                individu[i][j] = 1 - individu[i][j]


def croiser(parent_a: Grille, parent_b: Grille, zone: Zone) -> Grille:
    lignes, colonnes = dimensions(parent_a)
    enfant = nouvelle_grille(lignes, colonnes, 0)

    lmin, lmax, cmin, cmax = zone

    for i in range(lmin, lmax + 1):
        for j in range(cmin, cmax + 1):
            if random.random() < 0.5:
                enfant[i][j] = parent_a[i][j]
            else:
                enfant[i][j] = parent_b[i][j]

    return enfant


def creer_population_initiale(
    cible: Grille,
    zone: Zone,
    carte_distance: Grille,
    params: ParametresSolveur,
    grille_depart: Optional[Grille] = None
) -> List[Grille]:
    lignes, colonnes = dimensions(cible)
    population = []

    if grille_depart is not None:
        population.append(copier_grille(grille_depart))
    else:
        population.append(nouvelle_grille(lignes, colonnes, 0))

    population.append(copier_grille(cible))

    for _ in range(8):
        individu = copier_grille(cible)
        muter_zone_guidee(individu, zone, carte_distance, 0.12)
        population.append(individu)

    densites = [0.08, 0.14, 0.20, 0.28, 0.36]

    for densite in densites:
        for _ in range(5):
            population.append(
                individu_aleatoire_guide(
                    cible,
                    zone,
                    carte_distance,
                    densite,
                    params
                )
            )

    while len(population) < params.taille_population:
        densite = random.choice(densites + [params.densite_initiale])
        population.append(
            individu_aleatoire_guide(
                cible,
                zone,
                carte_distance,
                densite,
                params
            )
        )

    return population[:params.taille_population]


def population_sans_doublons(
    population: List[Grille],
    cible: Grille,
    zone: Zone,
    carte_distance: Grille,
    params: ParametresSolveur
) -> List[Grille]:
    uniques = []
    vus = set()

    for individu in population:
        cle = cle_grille(individu)

        if cle not in vus:
            vus.add(cle)
            uniques.append(individu)

    densites = [0.08, 0.14, 0.20, 0.28, 0.36, params.densite_initiale]

    while len(uniques) < params.taille_population:
        individu = individu_aleatoire_guide(
            cible,
            zone,
            carte_distance,
            random.choice(densites),
            params
        )

        cle = cle_grille(individu)

        if cle not in vus:
            vus.add(cle)
            uniques.append(individu)

    return uniques[:params.taille_population]


# ============================================================
#  SÉLECTION ET AMÉLIORATION
# ============================================================

def selection_tournoi(population_evaluee, taille_tournoi: int = 5) -> Grille:
    candidats = random.sample(population_evaluee, taille_tournoi)
    meilleur = min(candidats, key=lambda x: x[0])
    return meilleur[2]


def ameliorer_individu_local(
    individu: Grille,
    cible: Grille,
    nb_generations_inverse: int,
    evolution: FonctionEvolution,
    zone: Zone,
    carte_distance: Grille,
    cache: dict,
    params: ParametresSolveur
):
    meilleur = copier_grille(individu)

    meilleur_eval = evaluer_individu(
        meilleur,
        cible,
        nb_generations_inverse,
        evolution,
        carte_distance,
        cache,
        params
    )

    cellules = cellules_zone(zone)

    for _ in range(params.nb_essais_amelioration_locale):
        i, j = random.choice(cellules)

        candidat = copier_grille(meilleur)
        candidat[i][j] = 1 - candidat[i][j]

        candidat_eval = evaluer_individu(
            candidat,
            cible,
            nb_generations_inverse,
            evolution,
            carte_distance,
            cache,
            params
        )

        if candidat_eval[0] < meilleur_eval[0]:
            meilleur = candidat
            meilleur_eval = candidat_eval

    return meilleur_eval


# ============================================================
#  SOLVEUR INVERSE
# ============================================================

def resoudre_inverse(
    cible: Grille,
    nb_generations_inverse: int,
    evolution: FonctionEvolution,
    params: Optional[ParametresSolveur] = None,
    grille_depart: Optional[Grille] = None,
    seed: Optional[int] = None
) -> ResultatSolveur:
    """
    Cherche une grille initiale G0 telle que evolution^k(G0)
    soit aussi proche que possible de la cible.

    Le solveur ne connaît pas les règles du jeu.
    Il utilise seulement la fonction evolution(grille).
    """

    if params is None:
        params = ParametresSolveur()

    if seed is not None:
        random.seed(seed)

    zone = calculer_zone_recherche(
        cible,
        nb_generations_inverse,
        params
    )

    carte_distance = construire_carte_distance_cible(cible, params)

    population = creer_population_initiale(
        cible,
        zone,
        carte_distance,
        params,
        grille_depart
    )

    cache = {}

    meilleure_note_tri = None
    meilleure_erreur = None
    meilleur_individu = None
    meilleur_resultat = None
    meilleure_generation = 0

    stagnation = 0

    for generation in range(params.nb_generations_genetiques_max + 1):

        population_evaluee = evaluer_population(
            population,
            cible,
            nb_generations_inverse,
            evolution,
            carte_distance,
            cache,
            params
        )

        candidat_local = ameliorer_individu_local(
            population_evaluee[0][2],
            cible,
            nb_generations_inverse,
            evolution,
            zone,
            carte_distance,
            cache,
            params
        )

        population_evaluee.append(candidat_local)
        population_evaluee.sort(key=lambda x: x[0])

        note_tri, erreur_cible, individu, resultat = population_evaluee[0]

        if meilleure_note_tri is None or note_tri < meilleure_note_tri:
            meilleure_note_tri = note_tri
            meilleure_erreur = erreur_cible
            meilleur_individu = copier_grille(individu)
            meilleur_resultat = copier_grille(resultat)
            meilleure_generation = generation
            stagnation = 0
        else:
            stagnation += 1

        if erreur_cible == 0:
            return ResultatSolveur(
                grille_initiale=copier_grille(individu),
                grille_finale=copier_grille(resultat),
                erreur=erreur_cible,
                score_exactitude=score_exactitude(resultat, cible),
                generation=generation,
                solution_exacte=True
            )

        nouvelle_population = []

        taux_mutation = params.taux_mutation * (1 + min(4, stagnation // 25))

        taux_injection = params.taux_injection_aleatoire
        if stagnation >= 35:
            taux_injection = min(
                0.18,
                params.taux_injection_aleatoire * 2.5
            )

        for i in range(params.nb_elites):
            elite = population_evaluee[i][2]
            nouvelle_population.append(copier_grille(elite))

        nb_injections = int(params.taille_population * taux_injection)
        densites = [0.08, 0.14, 0.20, 0.28, 0.36, params.densite_initiale]

        for _ in range(nb_injections):
            nouvelle_population.append(
                individu_aleatoire_guide(
                    cible,
                    zone,
                    carte_distance,
                    random.choice(densites),
                    params
                )
            )

        while len(nouvelle_population) < params.taille_population:
            parent_a = selection_tournoi(population_evaluee)
            parent_b = selection_tournoi(population_evaluee)

            enfant = croiser(parent_a, parent_b, zone)
            muter_zone_guidee(
                enfant,
                zone,
                carte_distance,
                taux_mutation
            )

            nouvelle_population.append(enfant)

        population = population_sans_doublons(
            nouvelle_population,
            cible,
            zone,
            carte_distance,
            params
        )

    return ResultatSolveur(
        grille_initiale=meilleur_individu,
        grille_finale=meilleur_resultat,
        erreur=meilleure_erreur,
        score_exactitude=score_exactitude(meilleur_resultat, cible),
        generation=meilleure_generation,
        solution_exacte=False
    )