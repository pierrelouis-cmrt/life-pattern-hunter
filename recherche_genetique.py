"""Recherche inverse par population pour le Jeu de la vie.

Le module cherche une grille de départ qui donne une cible après un nombre de
passages choisi. Il reste volontairement lisible : population, score, élites,
croisement, mutation et quelques nouveaux candidats à chaque génération.
"""

from dataclasses import dataclass, field
import random

try:
    from .regles_jeudelavie import (
        BORDS_TORIQUES,
        NB_COLONNES,
        NB_LIGNES,
        copier_grille,
        nouvelle_grille,
        simuler,
    )
except ImportError:
    from regles_jeudelavie import (
        BORDS_TORIQUES,
        NB_COLONNES,
        NB_LIGNES,
        copier_grille,
        nouvelle_grille,
        simuler,
    )


@dataclass
class ConfigurationRecherche:
    """Réunit les réglages principaux de la recherche."""

    lignes: int = NB_LIGNES
    colonnes: int = NB_COLONNES
    bords_toriques: bool = BORDS_TORIQUES
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
    """Résultat d'un candidat après simulation et comparaison avec la cible."""

    score_tri: float
    erreur: float
    exactitude: float
    individu: list
    resultat: list
    role: str = "candidat"
    rang: int = 0


@dataclass
class InstantGeneration:
    """Résumé de la dernière génération utile pour l'affichage."""

    generation: int
    population_evaluee: list
    meilleur_global: Evaluation | None
    taux_mutation: float
    stagnation: int
    zone: tuple


@dataclass
class EtatSolveur:
    """Mémoire interne de la recherche en cours."""

    cible: list
    passages: int
    config: ConfigurationRecherche
    zone: tuple
    densite_active: float
    population: list
    hasard: random.Random = field(default_factory=random.Random)
    generation: int = 0
    stagnation: int = 0
    meilleure_note_tri: float | None = None
    meilleure_erreur: float | None = None
    meilleur_individu: list | None = None
    meilleur_resultat: list | None = None
    meilleur_score: float = 0.0
    dernier_snapshot: InstantGeneration | None = None
    termine: bool = False
    raison_arret: str = ""


def valider_config(config):
    """Vérifie les paramètres avant de lancer une recherche."""
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
    """Parcourt toutes les coordonnées de la grille."""
    for ligne in range(config.lignes):
        for colonne in range(config.colonnes):
            yield ligne, colonne


def cellules_zone(zone):
    """Parcourt les coordonnées d'une zone rectangulaire incluse dans la grille."""
    ligne_min, ligne_max, colonne_min, colonne_max = zone
    for ligne in range(ligne_min, ligne_max + 1):
        for colonne in range(colonne_min, colonne_max + 1):
            yield ligne, colonne


def taille_zone(zone):
    """Calcule le nombre de cellules couvertes par une zone."""
    ligne_min, ligne_max, colonne_min, colonne_max = zone
    return (ligne_max - ligne_min + 1) * (colonne_max - colonne_min + 1)


def cellules_vivantes(grille, config):
    """Liste les coordonnées des cellules vivantes."""
    return [
        (ligne, colonne)
        for ligne in range(config.lignes)
        for colonne in range(config.colonnes)
        if grille[ligne][colonne] == 1
    ]


def calculer_zone_recherche(cible, passages, config):
    """Délimite la zone de travail autour des cellules dessinées."""
    vivantes = cellules_vivantes(cible, config)
    if not vivantes:
        return (0, config.lignes - 1, 0, config.colonnes - 1)

    lignes = [ligne for ligne, _ in vivantes]
    colonnes = [colonne for _, colonne in vivantes]
    marge = max(config.marge_recherche, min(config.max_marge_recherche, passages + 2))
    return (
        max(0, min(lignes) - marge),
        min(config.lignes - 1, max(lignes) + marge),
        max(0, min(colonnes) - marge),
        min(config.colonnes - 1, max(colonnes) + marge),
    )


def densite_pour_zone(cible, zone, config):
    """Choisit une densité de départ raisonnable pour la taille de la cible."""
    vivantes = len(cellules_vivantes(cible, config))
    if vivantes == 0:
        return config.densite_initiale

    densite_cible = vivantes / max(1, taille_zone(zone))
    return min(0.35, max(0.04, densite_cible * 2.0, config.densite_initiale * 0.35))


def grille_aleatoire(config, hasard, zone=None, densite=None):
    """Crée un candidat aléatoire dans la zone de recherche."""
    zone = zone or (0, config.lignes - 1, 0, config.colonnes - 1)
    densite = config.densite_initiale if densite is None else densite
    grille = nouvelle_grille(0, config.lignes, config.colonnes)

    for ligne, colonne in cellules_zone(zone):
        if hasard.random() < densite:
            grille[ligne][colonne] = 1

    return grille


def creer_population_initiale(config, hasard, zone=None, densite=None):
    """Prépare la première population de candidats."""
    valider_config(config)
    return [
        grille_aleatoire(config, hasard, zone, densite)
        for _ in range(config.taille_population)
    ]


def erreur_par_rapport_a_cible(resultat, cible, config):
    """Mesure l'écart entre une simulation et la cible."""
    erreur = 0
    for ligne, colonne in cellules_grille(config):
        if cible[ligne][colonne] == 1 and resultat[ligne][colonne] == 0:
            erreur += config.penalite_faux_negatif
        elif cible[ligne][colonne] == 0 and resultat[ligne][colonne] == 1:
            erreur += config.penalite_faux_positif
    return erreur


def compter_differences(resultat, cible, config):
    """Compte simplement les cases différentes entre deux grilles."""
    differences = 0
    for ligne, colonne in cellules_grille(config):
        if resultat[ligne][colonne] != cible[ligne][colonne]:
            differences += 1
    return differences


def score_exactitude(resultat, cible, config):
    """Transforme les différences en pourcentage de ressemblance."""
    total = config.lignes * config.colonnes
    if total == 0:
        return 100.0

    differences = compter_differences(resultat, cible, config)
    return 100.0 * (total - differences) / total


def evaluer_individu(individu, cible, passages, config, role="candidat"):
    """Simule un candidat puis calcule son score."""
    resultat = simuler(individu, passages, config.bords_toriques)
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


def evaluer_population(population, cible, passages, config):
    """Évalue toute la population et place les meilleurs en premier."""
    evaluations = [
        evaluer_individu(individu, cible, passages, config)
        for individu in population
    ]
    evaluations.sort(key=lambda item: item.score_tri)

    for rang, evaluation in enumerate(evaluations, start=1):
        evaluation.rang = rang
        if rang <= config.nb_elites:
            evaluation.role = "elite"

    return evaluations


def croiser(parent_a, parent_b, config, hasard, zone=None):
    """Construit un enfant en mélangeant deux parents cellule par cellule."""
    zone = zone or (0, config.lignes - 1, 0, config.colonnes - 1)
    enfant = nouvelle_grille(0, config.lignes, config.colonnes)

    for ligne, colonne in cellules_zone(zone):
        enfant[ligne][colonne] = (
            parent_a[ligne][colonne]
            if hasard.random() < 0.5
            else parent_b[ligne][colonne]
        )

    return enfant


def muter(individu, config, hasard, zone=None, taux_mutation=None):
    """Inverse parfois des cellules pour garder de la variété."""
    zone = zone or (0, config.lignes - 1, 0, config.colonnes - 1)
    taux = config.taux_mutation if taux_mutation is None else taux_mutation

    for ligne, colonne in cellules_zone(zone):
        if hasard.random() < taux:
            individu[ligne][colonne] = 1 - individu[ligne][colonne]

    return individu


def choisir_parents_elites(elites, hasard):
    """Choisit deux bons parents pour créer un nouvel enfant."""
    if len(elites) == 1:
        return elites[0].individu, elites[0].individu

    parent_a, parent_b = hasard.sample(elites, 2)
    return parent_a.individu, parent_b.individu


def construire_population_suivante(
    evaluations,
    config,
    hasard,
    zone=None,
    densite=None,
    taux_mutation=None,
):
    """Prépare la population suivante à partir des meilleurs candidats."""
    zone = zone or (0, config.lignes - 1, 0, config.colonnes - 1)
    densite = config.densite_initiale if densite is None else densite
    taux_mutation = config.taux_mutation if taux_mutation is None else taux_mutation
    elites = evaluations[:config.nb_elites]

    # Les élites sont recopiées telles quelles pour conserver le meilleur acquis.
    nouvelle = [copier_grille(evaluation.individu) for evaluation in elites]
    nb_nouveaux = int(config.taille_population * config.fraction_nouveaux_aleatoires)

    while len(nouvelle) < config.nb_elites + nb_nouveaux and len(nouvelle) < config.taille_population:
        nouvelle.append(grille_aleatoire(config, hasard, zone, densite))

    while len(nouvelle) < config.taille_population:
        parent_a, parent_b = choisir_parents_elites(elites, hasard)
        enfant = croiser(parent_a, parent_b, config, hasard, zone)
        nouvelle.append(muter(enfant, config, hasard, zone, taux_mutation))

    return nouvelle


def copier_evaluation(evaluation, role=None):
    """Copie une évaluation pour l'affichage sans garder de référence fragile."""
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
    """Expose le meilleur candidat trouvé depuis le début."""
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
    """Met à jour le meilleur candidat si la génération fait mieux."""
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
    """Augmente doucement la mutation quand le score ne progresse plus."""
    multiplicateur = 1 + min(5, solveur.stagnation // 20)
    return min(solveur.config.taux_mutation_max, solveur.config.taux_mutation * multiplicateur)


def enregistrer_snapshot(solveur, evaluations, taux_mutation):
    """Mémorise ce qu'il faut pour informer l'utilisateur dans l'interface."""
    solveur.dernier_snapshot = InstantGeneration(
        generation=solveur.generation,
        population_evaluee=[copier_evaluation(e) for e in evaluations[:solveur.config.taille_population]],
        meilleur_global=evaluation_meilleur_global(solveur),
        taux_mutation=taux_mutation,
        stagnation=solveur.stagnation,
        zone=solveur.zone,
    )


def initialiser_solveur(grille_actuelle, cible, passages, config=None, hasard=None):
    """Crée un solveur prêt à avancer génération par génération."""
    del grille_actuelle
    config = config or ConfigurationRecherche()
    valider_config(config)
    hasard = hasard or random.Random()
    zone = calculer_zone_recherche(cible, passages, config)
    densite = densite_pour_zone(cible, zone, config)

    return EtatSolveur(
        cible=copier_grille(cible),
        passages=passages,
        config=config,
        zone=zone,
        densite_active=densite,
        population=creer_population_initiale(config, hasard, zone, densite),
        hasard=hasard,
    )


def avancer_solveur_une_generation(solveur):
    """Fait avancer la recherche d'une génération génétique."""
    if solveur.termine:
        return solveur

    config = solveur.config
    evaluations = evaluer_population(solveur.population, solveur.cible, solveur.passages, config)
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
        solveur.hasard,
        solveur.zone,
        solveur.densite_active,
        mutation,
    )
    solveur.generation += 1
    return solveur


def lancer_recherche(grille_actuelle, cible, passages, config=None, hasard=None):
    """Lance une recherche complète et renvoie son état final."""
    solveur = initialiser_solveur(grille_actuelle, cible, passages, config, hasard)
    while not solveur.termine:
        avancer_solveur_une_generation(solveur)
    return solveur
