"""Contrôleur des essais automatiques de nombres de générations.

Ce module ne connaît pas Tkinter. Il orchestre seulement les relances du
solveur quand une valeur de ``steps`` semble mauvaise pour la cible courante.
"""

from life_rules import (
    copier_grille,
    nombre_cellules_vivantes,
)
from reverse_search_algorithm import (
    compter_differences,
    detecter_periode_simple,
    initialiser_solveur,
)


def reinitialiser_auto_steps(etat):
    etat.auto_steps_actif = False
    etat.auto_steps_queue = []
    etat.auto_steps_tentes = []
    etat.auto_steps_resultats = []
    etat.auto_steps_depart = 0
    etat.auto_steps_plan = []
    etat.auto_steps_best = None


def generer_steps_alternatifs(etat):
    plan = getattr(etat, "auto_steps_plan", []) or []
    deja_vus = set(etat.auto_steps_tentes)
    return [steps for steps in plan if steps not in deja_vus]


def stagnation_probablement_finale(etat):
    if etat.solveur is None:
        return False

    solveur = etat.solveur
    if solveur.meilleure_erreur in (None, 0):
        return False

    cible_vivante = nombre_cellules_vivantes(etat.cible)
    seuil_stagnation = 75 if cible_vivante <= etat.config_recherche.seuil_cible_clairesemee else 95
    generation_min = max(60, seuil_stagnation)
    reste = solveur.config.nb_generations_max - solveur.generation

    return (
        solveur.generation >= generation_min
        and solveur.stagnation >= seuil_stagnation
        and reste >= 20
    )


def enregistrer_meilleur_auto_steps(etat):
    if etat.solveur is None or etat.solveur.meilleur_individu is None:
        return

    erreur = float("inf") if etat.solveur.meilleure_erreur is None else etat.solveur.meilleure_erreur
    note = float("inf") if etat.solveur.meilleure_note_tri is None else etat.solveur.meilleure_note_tri
    stats = {
        "steps": etat.k_inverse,
        "generation": etat.solveur.generation,
        "erreur": erreur,
        "note": note,
        "exactitude": etat.solveur.meilleur_score,
        "stagnation": etat.solveur.stagnation,
        "cellules": nombre_cellules_vivantes(etat.solveur.meilleur_individu),
    }

    for index, item in enumerate(etat.auto_steps_resultats):
        if item["steps"] == etat.k_inverse:
            etat.auto_steps_resultats[index] = stats
            break
    else:
        etat.auto_steps_resultats.append(stats)

    meilleur = etat.auto_steps_best
    if meilleur is None or (erreur, note) < (meilleur["erreur"], meilleur["note"]):
        etat.auto_steps_best = {
            "steps": etat.k_inverse,
            "solveur": etat.solveur,
            "erreur": erreur,
            "note": note,
        }


def formater_stats_auto_steps(etat, exclure_solution_exacte=False):
    if not etat.auto_steps_resultats:
        return ""

    resultats = sorted(etat.auto_steps_resultats, key=lambda item: (item["erreur"], item["note"]))
    if exclure_solution_exacte:
        resultats = [item for item in resultats if item["erreur"] != 0]

    morceaux = []
    for item in resultats[:etat.auto_steps_max_essais]:
        erreur = "?" if item["erreur"] == float("inf") else "{:.2f}".format(item["erreur"])
        morceaux.append(
            "{}g: err {}, {:.1f}%, {} cellules, stagn {}".format(
                item["steps"],
                erreur,
                item["exactitude"],
                item["cellules"],
                item["stagnation"],
            )
        )

    return " | ".join(morceaux)


def restaurer_meilleur_auto_steps(etat, synchroniser_entree_etapes=None):
    meilleur = etat.auto_steps_best
    if meilleur is None:
        return

    etat.k_inverse = meilleur["steps"]
    if synchroniser_entree_etapes is not None:
        synchroniser_entree_etapes()
    etat.solveur = meilleur["solveur"]
    if etat.solveur.meilleur_individu is not None:
        etat.grille = copier_grille(etat.solveur.meilleur_individu)
        etat.resultat = copier_grille(etat.solveur.meilleur_resultat)
        etat.evolution = None
        etat.evolution_index = 0


def demarrer_solveur_pour_steps(etat, steps, synchroniser_entree_etapes=None):
    etat.k_inverse = steps
    if synchroniser_entree_etapes is not None:
        synchroniser_entree_etapes()
    etat.solveur = initialiser_solveur(etat.grille, etat.cible, etat.k_inverse, etat.config_recherche)
    etat.solveur_actif = True
    etat.lecture = False
    etat.vue = "initial"
    if steps not in etat.auto_steps_tentes:
        etat.auto_steps_tentes.append(steps)


def limite_essais_auto_atteinte(etat):
    return len(etat.auto_steps_tentes) >= etat.auto_steps_max_essais


def essayer_step_auto_suivant(
    etat,
    board,
    raison,
    construire_recommandation=None,
    synchroniser_entree_etapes=None,
):
    if not etat.auto_steps_actif:
        return False

    enregistrer_meilleur_auto_steps(etat)
    if limite_essais_auto_atteinte(etat):
        etat.auto_steps_queue = []
        restaurer_meilleur_auto_steps(etat, synchroniser_entree_etapes)
        etat.solveur_actif = False
        etat.auto_steps_actif = False
        stats = formater_stats_auto_steps(etat)
        suffixe = " Stats essais : {}.".format(stats) if stats else ""
        etat.recommendation_steps = (
            "Auto-steps arrêté après {} essais maximum. "
            "Meilleur essai conservé : {} générations.{}"
        ).format(etat.auto_steps_max_essais, etat.k_inverse, suffixe)
        return False

    if not etat.auto_steps_queue:
        etat.auto_steps_queue = generer_steps_alternatifs(etat)

    while etat.auto_steps_queue:
        prochain = etat.auto_steps_queue.pop(0)
        if prochain in etat.auto_steps_tentes:
            continue
        if hasattr(board, "console"):
            board.console("Auto-steps : stagnation détectée, essai avec {} générations.".format(prochain))
        demarrer_solveur_pour_steps(etat, prochain, synchroniser_entree_etapes)
        etat.recommendation_steps = "Auto-steps : {}. Essais en cours : {}.".format(
            raison,
            ", ".join(str(valeur) for valeur in etat.auto_steps_tentes),
        )
        return True

    restaurer_meilleur_auto_steps(etat, synchroniser_entree_etapes)
    etat.solveur_actif = False
    etat.auto_steps_actif = False
    stats = formater_stats_auto_steps(etat)
    suffixe = " Stats essais : {}.".format(stats) if stats else ""
    recommandation = construire_recommandation() if construire_recommandation is not None else ""
    etat.recommendation_steps = (
        "{} Aucun autre nombre de générations n'a amélioré la recherche. "
        "Meilleur essai conservé : {} générations."
    ).format(recommandation, etat.k_inverse) + suffixe
    return False


def construire_recommandation_steps(etat):
    if etat.solveur is None or etat.resultat is None:
        return ""
    if etat.solveur.meilleure_erreur == 0:
        return "Solution exacte trouvée pour {} générations.".format(etat.k_inverse)

    manquantes, en_trop = compter_differences(etat.resultat, etat.cible, etat.config_recherche)
    cible_vivante = max(1, nombre_cellules_vivantes(etat.cible))
    voisins = sorted(set([
        max(1, etat.k_inverse - 2),
        max(1, etat.k_inverse - 1),
        etat.k_inverse,
        etat.k_inverse + 1,
        etat.k_inverse + 2,
    ]))
    voisins_texte = ", ".join(str(valeur) for valeur in voisins)
    periode = detecter_periode_simple(etat.cible, etat.config_recherche)

    if cible_vivante <= etat.config_recherche.seuil_cible_clairesemee and etat.solveur.stagnation >= 35:
        valeurs = [1, 2, 3, 4, 5, 6, 8]
        if periode:
            return "Cible très petite et stagnation forte (période {}). Recommandation : tester {} générations.".format(
                periode,
                ", ".join(str(valeur) for valeur in valeurs),
            )
        return "Cible très petite et stagnation forte. Recommandation : tester {} générations.".format(
            ", ".join(str(valeur) for valeur in valeurs)
        )

    if periode:
        compatibles = [
            valeur for valeur in voisins
            if valeur % periode == etat.k_inverse % periode
        ]
        if compatibles:
            return "Cible périodique détectée (période {}). Recommandation : comparer {} générations.".format(
                periode,
                ", ".join(str(valeur) for valeur in compatibles),
            )

    if manquantes >= cible_vivante / 2:
        valeurs = sorted(set([max(1, etat.k_inverse - 3), max(1, etat.k_inverse - 2), max(1, etat.k_inverse - 1)]))
        return "Résultat imparfait : beaucoup de cellules cible manquent. Recommandation : essayer {} générations.".format(
            ", ".join(str(valeur) for valeur in valeurs)
        )
    if en_trop > manquantes * 2 and etat.solveur.meilleur_score >= 92:
        return "Résultat proche mais bruité. Recommandation : réessayer {} générations, puis comparer avec {} et {}.".format(
            etat.k_inverse,
            max(1, etat.k_inverse - 1),
            etat.k_inverse + 1,
        )
    if etat.solveur.stagnation >= 35:
        return "Forte stagnation. Recommandation : essayer {} générations ou rendre la cible plus compacte.".format(voisins_texte)
    return "Résultat imparfait. Recommandation : relancer avec {}, puis comparer avec {} générations.".format(
        etat.k_inverse,
        voisins_texte,
    )
