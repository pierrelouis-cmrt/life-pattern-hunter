"""Algorithme génétique inverse simplifié.

Cette version reste volontairement courte, mais elle garde trois aides à fort
rendement : zone active autour de la cible, score pondéré et anti-stagnation
simple par mutation adaptative plus nouveaux individus aléatoires.
"""

from dataclasses import dataclass, field
import random

try:
    from .life_rules import (
        COLS,
        ROWS,
        TOROIDAL_BORDERS,
        copier_grille,
        nouvelle_grille,
        simuler,
    )
except ImportError:
    from life_rules import (
        COLS,
        ROWS,
        TOROIDAL_BORDERS,
        copier_grille,
        nouvelle_grille,
        simuler,
    )


@dataclass
class SimpleSearchConfig:
    rows: int = ROWS
    cols: int = COLS
    bords_toriques: bool = TOROIDAL_BORDERS
    marge_recherche: int = 3
    max_marge_recherche: int = 10
    taille_population: int = 120
    nb_elites: int = 14
    densite_initiale: float = 0.23
    taux_mutation: float = 0.05
    taux_mutation_max: float = 0.30
    fraction_nouveaux_aleatoires: float = 0.18
    nb_generations_max: int = 420
    penalite_faux_negatif: float = 4.0
    penalite_faux_positif: float = 1.0


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
    meilleur_global: Evaluation | None
    taux_mutation: float
    stagnation: int
    zone: tuple


@dataclass
class SolverState:
    cible: list
    steps: int
    config: SimpleSearchConfig
    zone: tuple
    densite_active: float
    population: list
    rng: random.Random = field(default_factory=random.Random)
    generation: int = 0
    stagnation: int = 0
    meilleure_note_tri: float | None = None
    meilleure_erreur: float | None = None
    meilleur_individu: list | None = None
    meilleur_resultat: list | None = None
    meilleur_score: float = 0.0
    dernier_snapshot: GenerationSnapshot | None = None
    termine: bool = False
    raison_arret: str = ""


def valider_config(config):
    if config.taille_population < 2:
        raise ValueError("La population doit contenir au moins deux individus.")
    if config.nb_elites < 1:
        raise ValueError("Il faut garder au moins une élite.")
    if config.nb_elites > config.taille_population:
        raise ValueError("Le nombre d'élites ne peut pas dépasser la population.")
    if not 0 <= config.densite_initiale <= 1:
        raise ValueError("La densité initiale doit être entre 0 et 1.")
    if not 0 <= config.taux_mutation <= 1:
        raise ValueError("Le taux de mutation doit être entre 0 et 1.")
    if not 0 <= config.taux_mutation_max <= 1:
        raise ValueError("Le taux de mutation maximal doit être entre 0 et 1.")
    if config.taux_mutation_max < config.taux_mutation:
        raise ValueError("Le taux de mutation maximal doit être supérieur au taux de base.")
    if not 0 <= config.fraction_nouveaux_aleatoires <= 1:
        raise ValueError("La fraction de nouveaux individus doit être entre 0 et 1.")
    if config.marge_recherche < 0 or config.max_marge_recherche < config.marge_recherche:
        raise ValueError("Les marges de recherche sont incohérentes.")
    if config.penalite_faux_negatif <= 0 or config.penalite_faux_positif <= 0:
        raise ValueError("Les pénalités de score doivent être positives.")


def cellules_grille(config):
    for i in range(config.rows):
        for j in range(config.cols):
            yield i, j


def cellules_zone(zone):
    lmin, lmax, cmin, cmax = zone
    for i in range(lmin, lmax + 1):
        for j in range(cmin, cmax + 1):
            yield i, j


def taille_zone(zone):
    lmin, lmax, cmin, cmax = zone
    return (lmax - lmin + 1) * (cmax - cmin + 1)


def cellules_vivantes(grille, config):
    return [
        (i, j)
        for i in range(config.rows)
        for j in range(config.cols)
        if grille[i][j] == 1
    ]


def calculer_zone_recherche(cible, steps, config):
    vivantes = cellules_vivantes(cible, config)
    if not vivantes:
        return (0, config.rows - 1, 0, config.cols - 1)

    lignes = [i for i, _ in vivantes]
    colonnes = [j for _, j in vivantes]
    marge = max(config.marge_recherche, min(config.max_marge_recherche, steps + 2))
    return (
        max(0, min(lignes) - marge),
        min(config.rows - 1, max(lignes) + marge),
        max(0, min(colonnes) - marge),
        min(config.cols - 1, max(colonnes) + marge),
    )


def densite_pour_zone(cible, zone, config):
    vivantes = len(cellules_vivantes(cible, config))
    if vivantes == 0:
        return config.densite_initiale

    densite_cible = vivantes / max(1, taille_zone(zone))
    return min(0.35, max(0.04, densite_cible * 2.0, config.densite_initiale * 0.35))


def grille_aleatoire(config, rng, zone=None, densite=None):
    zone = zone or (0, config.rows - 1, 0, config.cols - 1)
    densite = config.densite_initiale if densite is None else densite
    grille = nouvelle_grille(0, config.rows, config.cols)
    for i, j in cellules_zone(zone):
        if rng.random() < densite:
            grille[i][j] = 1
    return grille


def creer_population_initiale(config, rng, zone=None, densite=None):
    valider_config(config)
    return [grille_aleatoire(config, rng, zone, densite) for _ in range(config.taille_population)]


def erreur_par_rapport_a_cible(resultat, cible, config):
    erreur = 0
    for i, j in cellules_grille(config):
        if cible[i][j] == 1 and resultat[i][j] == 0:
            erreur += config.penalite_faux_negatif
        elif cible[i][j] == 0 and resultat[i][j] == 1:
            erreur += config.penalite_faux_positif
    return erreur


def compter_differences(resultat, cible, config):
    differences = 0
    for i, j in cellules_grille(config):
        if resultat[i][j] != cible[i][j]:
            differences += 1
    return differences


def score_exactitude(resultat, cible, config):
    total = config.rows * config.cols
    if total == 0:
        return 100.0
    differences = compter_differences(resultat, cible, config)
    return 100.0 * (total - differences) / total


def evaluer_individu(individu, cible, steps, config, role="candidat"):
    resultat = simuler(individu, steps, config.bords_toriques)
    erreur = erreur_par_rapport_a_cible(resultat, cible, config)
    exactitude = score_exactitude(resultat, cible, config)
    return Evaluation(
        score_tri=erreur,
        erreur=erreur,
        exactitude=exactitude,
        individu=copier_grille(individu),
        resultat=resultat,
        role=role,
    )


def evaluer_population(population, cible, steps, config):
    evaluations = [
        evaluer_individu(individu, cible, steps, config)
        for individu in population
    ]
    evaluations.sort(key=lambda item: item.score_tri)
    for rang, evaluation in enumerate(evaluations, start=1):
        evaluation.rang = rang
        if rang <= config.nb_elites:
            evaluation.role = "elite"
    return evaluations


def croiser(parent_a, parent_b, config, rng, zone=None):
    zone = zone or (0, config.rows - 1, 0, config.cols - 1)
    enfant = nouvelle_grille(0, config.rows, config.cols)
    for i, j in cellules_zone(zone):
        enfant[i][j] = parent_a[i][j] if rng.random() < 0.5 else parent_b[i][j]
    return enfant


def muter(individu, config, rng, zone=None, taux_mutation=None):
    zone = zone or (0, config.rows - 1, 0, config.cols - 1)
    taux = config.taux_mutation if taux_mutation is None else taux_mutation
    for i, j in cellules_zone(zone):
        if rng.random() < taux:
            individu[i][j] = 1 - individu[i][j]
    return individu


def choisir_parents_elites(elites, rng):
    if len(elites) == 1:
        return elites[0].individu, elites[0].individu
    parent_a, parent_b = rng.sample(elites, 2)
    return parent_a.individu, parent_b.individu


def construire_population_suivante(evaluations, config, rng, zone=None, densite=None, taux_mutation=None):
    zone = zone or (0, config.rows - 1, 0, config.cols - 1)
    densite = config.densite_initiale if densite is None else densite
    taux_mutation = config.taux_mutation if taux_mutation is None else taux_mutation
    elites = evaluations[:config.nb_elites]
    nouvelle = [copier_grille(evaluation.individu) for evaluation in elites]
    nb_nouveaux = int(config.taille_population * config.fraction_nouveaux_aleatoires)

    while len(nouvelle) < config.nb_elites + nb_nouveaux and len(nouvelle) < config.taille_population:
        nouvelle.append(grille_aleatoire(config, rng, zone, densite))

    while len(nouvelle) < config.taille_population:
        parent_a, parent_b = choisir_parents_elites(elites, rng)
        enfant = croiser(parent_a, parent_b, config, rng, zone)
        nouvelle.append(muter(enfant, config, rng, zone, taux_mutation))

    return nouvelle


def copier_evaluation(evaluation, role=None):
    return Evaluation(
        evaluation.score_tri,
        evaluation.erreur,
        evaluation.exactitude,
        copier_grille(evaluation.individu),
        copier_grille(evaluation.resultat),
        role or evaluation.role,
        evaluation.rang,
    )


def evaluation_meilleur_global(solveur):
    if solveur.meilleur_individu is None:
        return None
    return Evaluation(
        solveur.meilleure_note_tri,
        solveur.meilleure_erreur,
        solveur.meilleur_score,
        copier_grille(solveur.meilleur_individu),
        copier_grille(solveur.meilleur_resultat),
        "meilleur global",
        1,
    )


def enregistrer_meilleur_global(solveur, evaluation):
    if solveur.meilleure_note_tri is not None and evaluation.score_tri >= solveur.meilleure_note_tri:
        solveur.stagnation += 1
        return

    solveur.meilleure_note_tri = evaluation.score_tri
    solveur.meilleure_erreur = evaluation.erreur
    solveur.meilleur_individu = copier_grille(evaluation.individu)
    solveur.meilleur_resultat = copier_grille(evaluation.resultat)
    solveur.meilleur_score = evaluation.exactitude
    solveur.stagnation = 0


def taux_mutation_effectif(solveur):
    multiplicateur = 1 + min(5, solveur.stagnation // 20)
    return min(solveur.config.taux_mutation_max, solveur.config.taux_mutation * multiplicateur)


def enregistrer_snapshot(solveur, evaluations, taux_mutation):
    solveur.dernier_snapshot = GenerationSnapshot(
        generation=solveur.generation,
        population_evaluee=[copier_evaluation(e) for e in evaluations[:solveur.config.taille_population]],
        meilleur_global=evaluation_meilleur_global(solveur),
        taux_mutation=taux_mutation,
        stagnation=solveur.stagnation,
        zone=solveur.zone,
    )


def initialiser_solveur(grille_actuelle, cible, steps, config=None, rng=None):
    del grille_actuelle
    config = config or SimpleSearchConfig()
    valider_config(config)
    rng = rng or random.Random()
    zone = calculer_zone_recherche(cible, steps, config)
    densite = densite_pour_zone(cible, zone, config)
    return SolverState(
        cible=copier_grille(cible),
        steps=steps,
        config=config,
        zone=zone,
        densite_active=densite,
        population=creer_population_initiale(config, rng, zone, densite),
        rng=rng,
    )


def avancer_solveur_une_generation(solveur):
    if solveur.termine:
        return solveur

    config = solveur.config
    evaluations = evaluer_population(solveur.population, solveur.cible, solveur.steps, config)
    enregistrer_meilleur_global(solveur, evaluations[0])
    mutation = taux_mutation_effectif(solveur)
    enregistrer_snapshot(solveur, evaluations, mutation)

    if solveur.meilleure_erreur == 0:
        solveur.termine = True
        solveur.raison_arret = "solution exacte"
        return solveur

    if solveur.generation >= config.nb_generations_max:
        solveur.termine = True
        solveur.raison_arret = "limite de générations"
        return solveur

    solveur.population = construire_population_suivante(
        evaluations,
        config,
        solveur.rng,
        solveur.zone,
        solveur.densite_active,
        mutation,
    )
    solveur.generation += 1
    return solveur


def lancer_recherche(grille_actuelle, cible, steps, config=None, rng=None):
    solveur = initialiser_solveur(grille_actuelle, cible, steps, config, rng)
    while not solveur.termine:
        avancer_solveur_une_generation(solveur)
    return solveur
