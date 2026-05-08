"""Solveur inverse par algorithme génétique.

Le module contient uniquement la logique de recherche. L'interface graphique
peut l'appeler génération par génération et lire les instantanés pédagogiques.
"""

from dataclasses import dataclass, field
import random

from life_rules import (
    COLS,
    ROWS,
    TOROIDAL_BORDERS,
    cle_grille,
    copier_grille,
    nombre_cellules_vivantes,
    nouvelle_grille,
    simuler,
)


@dataclass
class SearchConfig:
    rows: int = ROWS
    cols: int = COLS
    bords_toriques: bool = TOROIDAL_BORDERS
    marge_recherche: int = 4
    max_marge_recherche: int = 10
    taille_population: int = 120
    nb_elites: int = 14
    taux_mutation: float = 0.018
    taux_injection_aleatoire: float = 0.06
    densite_initiale: float = 0.23
    nb_generations_max: int = 420
    nb_essais_amelioration_locale: int = 18
    taille_cache_max: int = 8000
    penalite_faux_negatif: float = 4
    penalite_faux_positif: float = 1
    penalite_distance_extra: float = 0.12
    penalite_cellule_initiale: float = 0.001


@dataclass
class Evaluation:
    score_tri: float
    erreur: float
    exactitude: float
    individu: list
    resultat: list
    role: str = "candidat"
    rang: int = 0


@dataclass
class GenerationSnapshot:
    generation: int
    population_evaluee: list
    meilleurs_precedents: list
    meilleur_global: Evaluation | None
    taux_mutation: float
    taux_injection: float
    stagnation: int
    taille_cache: int
    zone: tuple


@dataclass
class SolverState:
    cible: list
    steps: int
    config: SearchConfig
    zone: tuple
    carte_distance: list
    population: list
    roles_population: list
    rng: random.Random = field(default_factory=random.Random)
    generation: int = 0
    cache: dict = field(default_factory=dict)
    stagnation: int = 0
    meilleure_note_tri: float | None = None
    meilleure_erreur: float | None = None
    meilleur_individu: list | None = None
    meilleur_resultat: list | None = None
    meilleur_score: float = 0.0
    meilleurs_precedents: list = field(default_factory=list)
    dernier_snapshot: GenerationSnapshot | None = None
    termine: bool = False
    raison_arret: str = ""


def cellules_zone(zone):
    lmin, lmax, cmin, cmax = zone
    return [(i, j) for i in range(lmin, lmax + 1) for j in range(cmin, cmax + 1)]


def limiter_cache(cache, taille_max):
    if len(cache) <= taille_max:
        return

    for cle in list(cache.keys())[:len(cache) - taille_max]:
        del cache[cle]


def construire_carte_distance_cible(cible, config=None):
    config = config or SearchConfig()
    cellules_cibles = []

    for i in range(config.rows):
        for j in range(config.cols):
            if cible[i][j] == 1:
                cellules_cibles.append((i, j))

    carte = [
        [config.max_marge_recherche + 1 for _ in range(config.cols)]
        for _ in range(config.rows)
    ]
    if not cellules_cibles:
        return carte

    for i in range(config.rows):
        for j in range(config.cols):
            carte[i][j] = min(max(abs(i - ci), abs(j - cj)) for ci, cj in cellules_cibles)

    return carte


def erreur_par_rapport_a_cible(resultat, cible, carte_distance=None, config=None):
    config = config or SearchConfig()
    erreur = 0

    for i in range(config.rows):
        for j in range(config.cols):
            r = resultat[i][j]
            c = cible[i][j]

            if c == 1 and r == 0:
                erreur += config.penalite_faux_negatif
            elif c == 0 and r == 1:
                erreur += config.penalite_faux_positif
                if carte_distance is not None:
                    distance = min(carte_distance[i][j], config.max_marge_recherche)
                    erreur += distance * config.penalite_distance_extra

    return erreur


def compter_differences(resultat, cible, config=None):
    config = config or SearchConfig()
    manquantes = 0
    en_trop = 0

    for i in range(config.rows):
        for j in range(config.cols):
            if cible[i][j] == 1 and resultat[i][j] == 0:
                manquantes += 1
            elif cible[i][j] == 0 and resultat[i][j] == 1:
                en_trop += 1

    return manquantes, en_trop


def score_exactitude(resultat, cible, config=None):
    config = config or SearchConfig()
    identiques = 0

    for i in range(config.rows):
        for j in range(config.cols):
            if resultat[i][j] == cible[i][j]:
                identiques += 1

    return 100.0 * identiques / (config.rows * config.cols)


def calculer_zone_recherche(cible, steps, config=None):
    config = config or SearchConfig()
    lignes = []
    cols = []

    for i in range(config.rows):
        for j in range(config.cols):
            if cible[i][j] == 1:
                lignes.append(i)
                cols.append(j)

    if not lignes:
        return (0, config.rows - 1, 0, config.cols - 1)

    marge = max(config.marge_recherche, min(config.max_marge_recherche, steps + 2))
    return (
        max(0, min(lignes) - marge),
        min(config.rows - 1, max(lignes) + marge),
        max(0, min(cols) - marge),
        min(config.cols - 1, max(cols) + marge),
    )


def individu_aleatoire_guide(zone, carte_distance, densite, config, rng):
    individu = nouvelle_grille(0, config.rows, config.cols)
    lmin, lmax, cmin, cmax = zone

    for i in range(lmin, lmax + 1):
        for j in range(cmin, cmax + 1):
            distance = carte_distance[i][j]
            bonus_pres_cible = max(0, 4 - distance) * 0.035
            proba = min(0.55, densite + bonus_pres_cible)
            if rng.random() < proba:
                individu[i][j] = 1

    return individu


def muter_zone_guidee(individu, zone, carte_distance, taux_mutation, rng):
    lmin, lmax, cmin, cmax = zone

    for i in range(lmin, lmax + 1):
        for j in range(cmin, cmax + 1):
            distance = carte_distance[i][j]
            proba = taux_mutation
            if distance <= 2:
                proba *= 1.35
            elif distance >= 7:
                proba *= 0.75

            if rng.random() < proba:
                individu[i][j] = 1 - individu[i][j]


def croiser(parent_a, parent_b, zone, config, rng):
    enfant = nouvelle_grille(0, config.rows, config.cols)
    lmin, lmax, cmin, cmax = zone

    for i in range(lmin, lmax + 1):
        for j in range(cmin, cmax + 1):
            enfant[i][j] = parent_a[i][j] if rng.random() < 0.5 else parent_b[i][j]

    return enfant


def selection_tournoi(population_evaluee, rng, taille_tournoi=5):
    taille = min(taille_tournoi, len(population_evaluee))
    candidats = rng.sample(population_evaluee, taille)
    return min(candidats, key=lambda item: item.score_tri).individu


def evaluer_individu(individu, role, cible, steps, cache, carte_distance, config):
    cle = cle_grille(individu)
    if cle in cache:
        score_tri, erreur, exactitude, resultat = cache[cle]
        return Evaluation(score_tri, erreur, exactitude, copier_grille(individu), copier_grille(resultat), role)

    resultat = simuler(individu, steps, config.bords_toriques)
    erreur = erreur_par_rapport_a_cible(resultat, cible, carte_distance, config)
    exactitude = score_exactitude(resultat, cible, config)
    score_tri = erreur + nombre_cellules_vivantes(individu) * config.penalite_cellule_initiale
    cache[cle] = (score_tri, erreur, exactitude, copier_grille(resultat))
    limiter_cache(cache, config.taille_cache_max)
    return Evaluation(score_tri, erreur, exactitude, copier_grille(individu), resultat, role)


def evaluer_population(population, roles, cible, steps, cache, carte_distance, config):
    population_evaluee = [
        evaluer_individu(individu, roles[index], cible, steps, cache, carte_distance, config)
        for index, individu in enumerate(population)
    ]
    population_evaluee.sort(key=lambda item: item.score_tri)

    for rang, evaluation in enumerate(population_evaluee, start=1):
        evaluation.rang = rang
        if rang <= config.nb_elites:
            evaluation.role = "elite"

    return population_evaluee


def creer_population_initiale(grille_actuelle, cible, zone, carte_distance, config, rng):
    population = [copier_grille(grille_actuelle), copier_grille(cible)]
    roles = ["dessin actuel", "cible naive"]

    for _ in range(8):
        individu = copier_grille(cible)
        muter_zone_guidee(individu, zone, carte_distance, 0.12, rng)
        population.append(individu)
        roles.append("cible bruitee")

    densites = [0.08, 0.14, 0.20, 0.28, 0.36]
    for densite in densites:
        for _ in range(5):
            population.append(individu_aleatoire_guide(zone, carte_distance, densite, config, rng))
            roles.append("aléatoire guidé")

    while len(population) < config.taille_population:
        densite = rng.choice(densites + [config.densite_initiale])
        population.append(individu_aleatoire_guide(zone, carte_distance, densite, config, rng))
        roles.append("aléatoire guidé")

    return population[:config.taille_population], roles[:config.taille_population]


def population_sans_doublons(population, roles, zone, carte_distance, config, rng):
    uniques = []
    roles_uniques = []
    vus = set()

    for index, individu in enumerate(population):
        cle = cle_grille(individu)
        if cle not in vus:
            vus.add(cle)
            uniques.append(individu)
            roles_uniques.append(roles[index])

    densites = [0.08, 0.14, 0.20, 0.28, 0.36, config.densite_initiale]
    while len(uniques) < config.taille_population:
        individu = individu_aleatoire_guide(zone, carte_distance, rng.choice(densites), config, rng)
        cle = cle_grille(individu)
        if cle not in vus:
            vus.add(cle)
            uniques.append(individu)
        roles_uniques.append("remplacement de doublon")

    return uniques[:config.taille_population], roles_uniques[:config.taille_population]


def ameliorer_individu_local(individu, cible, steps, zone, cache, carte_distance, config, rng):
    meilleur = copier_grille(individu)
    meilleur_eval = evaluer_individu(
        meilleur,
        "amelioration locale",
        cible,
        steps,
        cache,
        carte_distance,
        config,
    )
    cellules = cellules_zone(zone)

    for _ in range(config.nb_essais_amelioration_locale):
        i, j = rng.choice(cellules)
        candidat = copier_grille(meilleur)
        candidat[i][j] = 1 - candidat[i][j]
        candidat_eval = evaluer_individu(
            candidat,
            "amelioration locale",
            cible,
            steps,
            cache,
            carte_distance,
            config,
        )

        if candidat_eval.score_tri < meilleur_eval.score_tri:
            meilleur = candidat
            meilleur_eval = candidat_eval

    return meilleur_eval


def initialiser_solveur(grille_actuelle, cible, steps, config=None, rng=None):
    config = config or SearchConfig()
    rng = rng or random.Random()
    zone = calculer_zone_recherche(cible, steps, config)
    carte_distance = construire_carte_distance_cible(cible, config)
    population, roles = creer_population_initiale(
        grille_actuelle,
        cible,
        zone,
        carte_distance,
        config,
        rng,
    )

    return SolverState(
        cible=copier_grille(cible),
        steps=steps,
        config=config,
        zone=zone,
        carte_distance=carte_distance,
        population=population,
        roles_population=roles,
        rng=rng,
    )


def _copier_evaluation(evaluation, role=None):
    return Evaluation(
        score_tri=evaluation.score_tri,
        erreur=evaluation.erreur,
        exactitude=evaluation.exactitude,
        individu=copier_grille(evaluation.individu),
        resultat=copier_grille(evaluation.resultat),
        role=role or evaluation.role,
        rang=evaluation.rang,
    )


def _mettre_a_jour_meilleur_global(solveur, meilleure):
    if solveur.meilleure_note_tri is None or meilleure.score_tri < solveur.meilleure_note_tri:
        solveur.meilleure_note_tri = meilleure.score_tri
        solveur.meilleure_erreur = meilleure.erreur
        solveur.meilleur_individu = copier_grille(meilleure.individu)
        solveur.meilleur_resultat = copier_grille(meilleure.resultat)
        solveur.meilleur_score = meilleure.exactitude
        solveur.stagnation = 0
        return True

    solveur.stagnation += 1
    return False


def avancer_solveur_une_generation(solveur):
    if solveur.termine:
        return solveur

    config = solveur.config
    population_evaluee = evaluer_population(
        solveur.population,
        solveur.roles_population,
        solveur.cible,
        solveur.steps,
        solveur.cache,
        solveur.carte_distance,
        config,
    )

    candidat_local = ameliorer_individu_local(
        population_evaluee[0].individu,
        solveur.cible,
        solveur.steps,
        solveur.zone,
        solveur.cache,
        solveur.carte_distance,
        config,
        solveur.rng,
    )
    if candidat_local.score_tri < population_evaluee[0].score_tri:
        population_evaluee.insert(0, candidat_local)
    else:
        population_evaluee.append(candidat_local)
        population_evaluee.sort(key=lambda item: item.score_tri)

    for rang, evaluation in enumerate(population_evaluee, start=1):
        evaluation.rang = rang
        if rang <= config.nb_elites:
            evaluation.role = "elite"

    meilleure = population_evaluee[0]
    _mettre_a_jour_meilleur_global(solveur, meilleure)

    taux_mutation = config.taux_mutation * (1 + min(4, solveur.stagnation // 25))
    taux_injection = config.taux_injection_aleatoire
    if solveur.stagnation >= 35:
        taux_injection = min(0.18, config.taux_injection_aleatoire * 2.5)

    meilleur_global = None
    if solveur.meilleur_individu is not None:
        meilleur_global = Evaluation(
            solveur.meilleure_note_tri,
            solveur.meilleure_erreur,
            solveur.meilleur_score,
            copier_grille(solveur.meilleur_individu),
            copier_grille(solveur.meilleur_resultat),
            "meilleur global",
            1,
        )

    solveur.dernier_snapshot = GenerationSnapshot(
        generation=solveur.generation,
        population_evaluee=[_copier_evaluation(item) for item in population_evaluee[:config.taille_population]],
        meilleurs_precedents=[
            _copier_evaluation(item, "meilleur precedent") for item in solveur.meilleurs_precedents
        ],
        meilleur_global=meilleur_global,
        taux_mutation=taux_mutation,
        taux_injection=taux_injection,
        stagnation=solveur.stagnation,
        taille_cache=len(solveur.cache),
        zone=solveur.zone,
    )

    solveur.meilleurs_precedents = [_copier_evaluation(item, "meilleur precedent") for item in population_evaluee[:config.nb_elites]]

    if meilleure.erreur == 0:
        solveur.termine = True
        solveur.raison_arret = "solution exacte"
        return solveur

    if solveur.generation >= config.nb_generations_max:
        solveur.termine = True
        solveur.raison_arret = "limite de générations"
        return solveur

    nouvelle_population = []
    nouveaux_roles = []

    for i in range(config.nb_elites):
        nouvelle_population.append(copier_grille(population_evaluee[i].individu))
        nouveaux_roles.append("elite conservee")

    nb_injections = int(config.taille_population * taux_injection)
    densites = [0.08, 0.14, 0.20, 0.28, 0.36, config.densite_initiale]
    for _ in range(nb_injections):
        nouvelle_population.append(
            individu_aleatoire_guide(
                solveur.zone,
                solveur.carte_distance,
                solveur.rng.choice(densites),
                config,
                solveur.rng,
            )
        )
        nouveaux_roles.append("injection")

    while len(nouvelle_population) < config.taille_population:
        parent_a = selection_tournoi(population_evaluee, solveur.rng)
        parent_b = selection_tournoi(population_evaluee, solveur.rng)
        enfant = croiser(parent_a, parent_b, solveur.zone, config, solveur.rng)
        muter_zone_guidee(enfant, solveur.zone, solveur.carte_distance, taux_mutation, solveur.rng)
        nouvelle_population.append(enfant)
        nouveaux_roles.append("enfant")

    solveur.population, solveur.roles_population = population_sans_doublons(
        nouvelle_population,
        nouveaux_roles,
        solveur.zone,
        solveur.carte_distance,
        config,
        solveur.rng,
    )
    solveur.generation += 1
    return solveur
