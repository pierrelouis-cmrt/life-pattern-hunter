"""Solveur inverse par algorithme génétique.

Le module ne gère qu'une recherche pour une cible et une valeur fixe de
``steps``.
"""

from dataclasses import dataclass, field
from itertools import combinations
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
    seuil_cible_clairesemee: int = 8
    nb_graines_locales: int = 16
    max_cellules_graines_locales: int = 5
    max_cases_graines_locales: int = 18
    marge_graines_locales: int = 1
    max_generations_graines_locales: int = 8
    seuil_relance_stagnation: int = 55
    intervalle_relance_stagnation: int = 20
    fraction_relance_stagnation: float = 0.45
    nb_essais_nettoyage: int = 80


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
    graines_locales: list = field(default_factory=list)
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


# ---------------------------------------------------------------------------
# Petits outils de grille


def cellules_zone(zone):
    lmin, lmax, cmin, cmax = zone
    return [(i, j) for i in range(lmin, lmax + 1) for j in range(cmin, cmax + 1)]


def cellules_vivantes(grille, config=None):
    config = config or SearchConfig()
    return [
        (i, j)
        for i in range(config.rows)
        for j in range(config.cols)
        if grille[i][j] == 1
    ]


def grille_depuis_cellules(cellules, config):
    grille = nouvelle_grille(0, config.rows, config.cols)
    for i, j in cellules:
        grille[i][j] = 1
    return grille


def voisins_cellule(ligne, col, config):
    for dl in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dl == 0 and dc == 0:
                continue
            nl, nc = ligne + dl, col + dc
            if config.bords_toriques:
                yield nl % config.rows, nc % config.cols
            elif 0 <= nl < config.rows and 0 <= nc < config.cols:
                yield nl, nc


def limiter_cache(cache, taille_max):
    while len(cache) > taille_max:
        del cache[next(iter(cache))]


# ---------------------------------------------------------------------------
# Score et zone de recherche


def construire_carte_distance_cible(cible, config=None):
    config = config or SearchConfig()
    cibles = cellules_vivantes(cible, config)
    valeur_lointaine = config.max_marge_recherche + 1
    if not cibles:
        return [[valeur_lointaine for _ in range(config.cols)] for _ in range(config.rows)]

    return [
        [min(max(abs(i - ci), abs(j - cj)) for ci, cj in cibles) for j in range(config.cols)]
        for i in range(config.rows)
    ]


def erreur_par_rapport_a_cible(resultat, cible, carte_distance=None, config=None):
    config = config or SearchConfig()
    erreur = 0
    for i in range(config.rows):
        for j in range(config.cols):
            if cible[i][j] == 1 and resultat[i][j] == 0:
                erreur += config.penalite_faux_negatif
            elif cible[i][j] == 0 and resultat[i][j] == 1:
                erreur += config.penalite_faux_positif
                if carte_distance is not None:
                    erreur += min(carte_distance[i][j], config.max_marge_recherche) * config.penalite_distance_extra
    return erreur


def compter_differences(resultat, cible, config=None):
    config = config or SearchConfig()
    manquantes = en_trop = 0
    for i in range(config.rows):
        for j in range(config.cols):
            manquantes += cible[i][j] == 1 and resultat[i][j] == 0
            en_trop += cible[i][j] == 0 and resultat[i][j] == 1
    return manquantes, en_trop


def score_exactitude(resultat, cible, config=None):
    config = config or SearchConfig()
    identiques = sum(
        resultat[i][j] == cible[i][j]
        for i in range(config.rows)
        for j in range(config.cols)
    )
    return 100.0 * identiques / (config.rows * config.cols)


def detecter_periode_simple(cible, config=None, max_periode=8):
    config = config or SearchConfig()
    reference = cle_grille(cible)
    courant = copier_grille(cible)
    for periode in range(1, max_periode + 1):
        courant = simuler(courant, 1, config.bords_toriques)
        if cle_grille(courant) == reference:
            return periode
    return None


def calculer_zone_recherche(cible, steps, config=None):
    config = config or SearchConfig()
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


# ---------------------------------------------------------------------------
# Graines locales : petit bonus déterministe pour les cibles très simples


def simuler_cellules_vivantes(cellules_initiales, steps, config):
    vivantes = set(cellules_initiales)
    for _ in range(steps):
        voisins = {}
        for cellule in vivantes:
            for voisine in voisins_cellule(cellule[0], cellule[1], config):
                voisins[voisine] = voisins.get(voisine, 0) + 1
        vivantes = {
            cellule
            for cellule, nb in voisins.items()
            if nb == 3 or (nb == 2 and cellule in vivantes)
        }
    return vivantes


def erreur_cellules(resultat, cible_cellules, carte_distance, config):
    erreur = len(cible_cellules - resultat) * config.penalite_faux_negatif
    for i, j in resultat - cible_cellules:
        erreur += config.penalite_faux_positif
        erreur += min(carte_distance[i][j], config.max_marge_recherche) * config.penalite_distance_extra
    return erreur


def creer_graines_locales_cible(cible, steps, zone, carte_distance, config):
    cible_cellules = set(cellules_vivantes(cible, config))
    if not cible_cellules or len(cible_cellules) > config.seuil_cible_clairesemee:
        return []

    lz0, lz1, cz0, cz1 = zone
    marge = config.marge_graines_locales
    lignes = [i for i, _ in cible_cellules]
    colonnes = [j for _, j in cible_cellules]
    l0, l1 = max(lz0, min(lignes) - marge), min(lz1, max(lignes) + marge)
    c0, c1 = max(cz0, min(colonnes) - marge), min(cz1, max(colonnes) + marge)
    cases = [(i, j) for i in range(l0, l1 + 1) for j in range(c0, c1 + 1)]
    if len(cases) > config.max_cases_graines_locales:
        return []

    candidats = []
    taille_max = min(config.max_cellules_graines_locales, len(cases))
    for taille in range(1, taille_max + 1):
        for choix in combinations(cases, taille):
            resultat = simuler_cellules_vivantes(choix, steps, config)
            erreur = erreur_cellules(resultat, cible_cellules, carte_distance, config)
            score = erreur + taille * config.penalite_cellule_initiale
            candidats.append((score, erreur, taille, choix))

    candidats.sort(key=lambda item: (item[0], item[1], item[2]))
    return [
        grille_depuis_cellules(cellules, config)
        for _, _, _, cellules in candidats[:config.nb_graines_locales]
    ]


# ---------------------------------------------------------------------------
# Coeur génétique : population, évaluation, sélection, croisement, mutation


def densites_recherche(cible, zone, config):
    if nombre_cellules_vivantes(cible) <= config.seuil_cible_clairesemee:
        densite = nombre_cellules_vivantes(cible) / max(1, len(cellules_zone(zone)))
        valeurs = [densite * 0.5, densite, densite * 1.5, 0.06, 0.10, config.densite_initiale]
    else:
        valeurs = [0.08, 0.14, 0.20, 0.28, 0.36, config.densite_initiale]
    return sorted({round(min(0.45, max(0.01, valeur)), 3) for valeur in valeurs})


def individu_aleatoire_guide(zone, carte_distance, densite, config, rng):
    individu = nouvelle_grille(0, config.rows, config.cols)
    for i, j in cellules_zone(zone):
        bonus = max(0, 4 - carte_distance[i][j]) * 0.035
        if rng.random() < min(0.55, densite + bonus):
            individu[i][j] = 1
    return individu


def muter_zone_guidee(individu, zone, carte_distance, taux_mutation, rng):
    for i, j in cellules_zone(zone):
        distance = carte_distance[i][j]
        facteur = 1.35 if distance <= 2 else 0.75 if distance >= 7 else 1.0
        if rng.random() < taux_mutation * facteur:
            individu[i][j] = 1 - individu[i][j]


def croiser(parent_a, parent_b, zone, config, rng):
    enfant = nouvelle_grille(0, config.rows, config.cols)
    for i, j in cellules_zone(zone):
        enfant[i][j] = parent_a[i][j] if rng.random() < 0.5 else parent_b[i][j]
    return enfant


def selection_tournoi(population_evaluee, rng, taille_tournoi=5):
    return min(
        rng.sample(population_evaluee, min(taille_tournoi, len(population_evaluee))),
        key=lambda item: item.score_tri,
    ).individu


def evaluer_individu(individu, role, cible, steps, cache, carte_distance, config):
    cle = cle_grille(individu)
    if cle in cache:
        score, erreur, exactitude, resultat = cache[cle]
        return Evaluation(score, erreur, exactitude, copier_grille(individu), copier_grille(resultat), role)

    resultat = simuler(individu, steps, config.bords_toriques)
    erreur = erreur_par_rapport_a_cible(resultat, cible, carte_distance, config)
    score = erreur + nombre_cellules_vivantes(individu) * config.penalite_cellule_initiale
    exactitude = score_exactitude(resultat, cible, config)
    cache[cle] = (score, erreur, exactitude, copier_grille(resultat))
    limiter_cache(cache, config.taille_cache_max)
    return Evaluation(score, erreur, exactitude, copier_grille(individu), resultat, role)


def evaluer_population(population, roles, cible, steps, cache, carte_distance, config):
    evaluations = [
        evaluer_individu(individu, roles[index], cible, steps, cache, carte_distance, config)
        for index, individu in enumerate(population)
    ]
    evaluations.sort(key=lambda item: item.score_tri)
    for rang, evaluation in enumerate(evaluations, start=1):
        evaluation.rang = rang
        if rang <= config.nb_elites:
            evaluation.role = "elite"
    return evaluations


def creer_population_initiale(grille_actuelle, cible, zone, carte_distance, config, rng, graines_locales=None):
    population = [copier_grille(grille_actuelle), copier_grille(cible)]
    roles = ["dessin actuel", "cible naive"]

    for graine in graines_locales or []:
        population.append(copier_grille(graine))
        roles.append("graine locale")

    for _ in range(8):
        individu = copier_grille(cible)
        muter_zone_guidee(individu, zone, carte_distance, 0.12, rng)
        population.append(individu)
        roles.append("cible bruitee")

    densites = densites_recherche(cible, zone, config)
    while len(population) < config.taille_population:
        population.append(individu_aleatoire_guide(zone, carte_distance, rng.choice(densites), config, rng))
        roles.append("aléatoire guidé")

    return population[:config.taille_population], roles[:config.taille_population]


def population_sans_doublons(population, roles, cible, zone, carte_distance, config, rng):
    uniques, roles_uniques, vus = [], [], set()
    for individu, role in zip(population, roles):
        cle = cle_grille(individu)
        if cle not in vus:
            vus.add(cle)
            uniques.append(individu)
            roles_uniques.append(role)

    densites = densites_recherche(cible, zone, config)
    while len(uniques) < config.taille_population:
        individu = individu_aleatoire_guide(zone, carte_distance, rng.choice(densites), config, rng)
        if cle_grille(individu) not in vus:
            vus.add(cle_grille(individu))
            uniques.append(individu)
            roles_uniques.append("remplacement de doublon")

    return uniques[:config.taille_population], roles_uniques[:config.taille_population]


# ---------------------------------------------------------------------------
# Petites corrections autour du meilleur individu


def cellule_isolee(individu, ligne, col, config):
    return all(individu[i][j] == 0 for i, j in voisins_cellule(ligne, col, config))


def ameliorer_individu_local(individu, cible, steps, zone, cache, carte_distance, config, rng):
    meilleur = evaluer_individu(individu, "amelioration locale", cible, steps, cache, carte_distance, config)
    cases = cellules_zone(zone)
    for _ in range(config.nb_essais_amelioration_locale):
        candidat = copier_grille(meilleur.individu)
        i, j = rng.choice(cases)
        candidat[i][j] = 1 - candidat[i][j]
        evaluation = evaluer_individu(candidat, "amelioration locale", cible, steps, cache, carte_distance, config)
        if evaluation.score_tri < meilleur.score_tri:
            meilleur = evaluation
    return meilleur


def nettoyer_solution_initiale(individu, cible, steps, config, carte_distance=None, cache=None):
    carte_distance = carte_distance or construire_carte_distance_cible(cible, config)
    cache = cache if cache is not None else {}
    meilleur = evaluer_individu(individu, "solution nettoyee", cible, steps, cache, carte_distance, config)
    erreur_depart = meilleur.erreur

    cellules = cellules_vivantes(meilleur.individu, config)
    cellules.sort(
        key=lambda cell: (cellule_isolee(meilleur.individu, cell[0], cell[1], config), carte_distance[cell[0]][cell[1]]),
        reverse=True,
    )
    for i, j in cellules[:config.nb_essais_nettoyage]:
        candidat = copier_grille(meilleur.individu)
        candidat[i][j] = 0
        evaluation = evaluer_individu(candidat, "solution nettoyee", cible, steps, cache, carte_distance, config)
        acceptable = evaluation.erreur == 0 if erreur_depart == 0 else evaluation.erreur <= meilleur.erreur
        if acceptable:
            meilleur = evaluation
    return meilleur


# ---------------------------------------------------------------------------
# Etat du solveur et boucle génétique


def initialiser_solveur(grille_actuelle, cible, steps, config=None, rng=None):
    config = config or SearchConfig()
    rng = rng or random.Random()
    zone = calculer_zone_recherche(cible, steps, config)
    carte_distance = construire_carte_distance_cible(cible, config)
    graines = creer_graines_locales_cible(cible, steps, zone, carte_distance, config)
    population, roles = creer_population_initiale(grille_actuelle, cible, zone, carte_distance, config, rng, graines)
    return SolverState(
        cible=copier_grille(cible),
        steps=steps,
        config=config,
        zone=zone,
        carte_distance=carte_distance,
        population=population,
        roles_population=roles,
        graines_locales=graines,
        rng=rng,
    )


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
    nettoyee = nettoyer_solution_initiale(
        evaluation.individu,
        solveur.cible,
        solveur.steps,
        solveur.config,
        solveur.carte_distance,
        solveur.cache,
    )
    if solveur.meilleure_note_tri is not None and nettoyee.score_tri >= solveur.meilleure_note_tri:
        solveur.stagnation += 1
        return

    solveur.meilleure_note_tri = nettoyee.score_tri
    solveur.meilleure_erreur = nettoyee.erreur
    solveur.meilleur_individu = copier_grille(nettoyee.individu)
    solveur.meilleur_resultat = copier_grille(nettoyee.resultat)
    solveur.meilleur_score = nettoyee.exactitude
    solveur.stagnation = 0


def taux_recherche(solveur):
    config = solveur.config
    mutation = config.taux_mutation * (1 + min(4, solveur.stagnation // 25))
    injection = config.taux_injection_aleatoire
    if solveur.stagnation >= 35:
        injection = min(0.18, injection * 2.5)
    return mutation, injection


def enregistrer_snapshot(solveur, evaluations, mutation, injection):
    config = solveur.config
    solveur.dernier_snapshot = GenerationSnapshot(
        generation=solveur.generation,
        population_evaluee=[copier_evaluation(e) for e in evaluations[:config.taille_population]],
        meilleurs_precedents=[copier_evaluation(e, "meilleur precedent") for e in solveur.meilleurs_precedents],
        meilleur_global=evaluation_meilleur_global(solveur),
        taux_mutation=mutation,
        taux_injection=injection,
        stagnation=solveur.stagnation,
        taille_cache=len(solveur.cache),
        zone=solveur.zone,
    )
    solveur.meilleurs_precedents = [copier_evaluation(e, "meilleur precedent") for e in evaluations[:config.nb_elites]]


def relance_forte(solveur):
    config = solveur.config
    return (
        solveur.stagnation >= config.seuil_relance_stagnation
        and config.intervalle_relance_stagnation > 0
        and (solveur.stagnation - config.seuil_relance_stagnation) % config.intervalle_relance_stagnation == 0
    )


def construire_population_suivante(solveur, evaluations, mutation, injection):
    config = solveur.config
    nouvelle = [copier_grille(e.individu) for e in evaluations[:config.nb_elites]]
    roles = ["elite conservee"] * len(nouvelle)
    forte = relance_forte(solveur)
    nb_injections = int(config.taille_population * injection)

    if forte:
        nb_injections = max(nb_injections, int(config.taille_population * config.fraction_relance_stagnation))
        if solveur.meilleur_individu is not None:
            meilleur_mute = copier_grille(solveur.meilleur_individu)
            muter_zone_guidee(meilleur_mute, solveur.zone, solveur.carte_distance, min(0.35, mutation * 4), solveur.rng)
            nouvelle.append(meilleur_mute)
            roles.append("relance stagnation")

    if solveur.graines_locales and solveur.stagnation >= 20:
        graines = [copier_grille(g) for g in solveur.graines_locales]
        solveur.rng.shuffle(graines)
        for graine in graines[:min(nb_injections, len(graines))]:
            if solveur.stagnation >= 35:
                muter_zone_guidee(graine, solveur.zone, solveur.carte_distance, mutation * 1.5, solveur.rng)
            nouvelle.append(graine)
            roles.append("relance stagnation" if forte else "relance locale")

    densites = densites_recherche(solveur.cible, solveur.zone, config)
    while len(nouvelle) < config.nb_elites + nb_injections:
        densite = solveur.rng.choice([0.01, 0.02, 0.04, densites[0]] if forte else densites)
        nouvelle.append(individu_aleatoire_guide(solveur.zone, solveur.carte_distance, densite, config, solveur.rng))
        roles.append("relance stagnation" if forte else "injection")

    while len(nouvelle) < config.taille_population:
        parent_a = selection_tournoi(evaluations, solveur.rng)
        parent_b = selection_tournoi(evaluations, solveur.rng)
        enfant = croiser(parent_a, parent_b, solveur.zone, config, solveur.rng)
        muter_zone_guidee(enfant, solveur.zone, solveur.carte_distance, mutation, solveur.rng)
        nouvelle.append(enfant)
        roles.append("enfant")

    return population_sans_doublons(nouvelle, roles, solveur.cible, solveur.zone, solveur.carte_distance, config, solveur.rng)


def avancer_solveur_une_generation(solveur):
    if solveur.termine:
        return solveur

    config = solveur.config
    evaluations = evaluer_population(
        solveur.population,
        solveur.roles_population,
        solveur.cible,
        solveur.steps,
        solveur.cache,
        solveur.carte_distance,
        config,
    )
    evaluations.append(
        ameliorer_individu_local(
            evaluations[0].individu,
            solveur.cible,
            solveur.steps,
            solveur.zone,
            solveur.cache,
            solveur.carte_distance,
            config,
            solveur.rng,
        )
    )
    evaluations.sort(key=lambda item: item.score_tri)
    for rang, evaluation in enumerate(evaluations, start=1):
        evaluation.rang = rang
        if rang <= config.nb_elites:
            evaluation.role = "elite"

    enregistrer_meilleur_global(solveur, evaluations[0])
    mutation, injection = taux_recherche(solveur)
    enregistrer_snapshot(solveur, evaluations, mutation, injection)

    if solveur.meilleure_erreur == 0:
        solveur.termine = True
        solveur.raison_arret = "solution exacte"
        return solveur
    if solveur.generation >= config.nb_generations_max:
        solveur.termine = True
        solveur.raison_arret = "limite de générations"
        return solveur

    solveur.population, solveur.roles_population = construire_population_suivante(solveur, evaluations, mutation, injection)
    solveur.generation += 1
    return solveur
