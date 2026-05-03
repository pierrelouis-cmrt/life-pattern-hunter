from eniseboard import *
import random
import tkinter as tk


# ============================================================
#  PARAMÈTRES GÉNÉRAUX
# ============================================================

LIGNES = 24
COLONNES = 24
TAILLE_CASE = 24

# Si False : les cellules hors de la grille sont considérées mortes.
# Si True  : la grille se replie sur elle-même comme un tore.
BORDS_TORIQUES = False

DELAI_ANIMATION_MS = 180

# Nombre de générations du Game of Life utilisées par le solveur inverse.
NB_GENERATIONS_INVERSE = 5

# Marge autour de la cible dans laquelle le solveur a le droit de chercher.
MARGE_RECHERCHE = 4
MAX_MARGE_RECHERCHE = 10


# ============================================================
#  PARAMÈTRES DE L'ALGORITHME GÉNÉTIQUE
# ============================================================

TAILLE_POPULATION = 120
NB_ELITES = 14
TAUX_MUTATION = 0.018
TAUX_INJECTION_ALEATOIRE = 0.06
DENSITE_INITIALE = 0.23

NB_GENERATIONS_GENETIQUES_MAX = 420
NB_ITERATIONS_SOLVEUR_PAR_TICK = 2
DELAI_SOLVEUR_MS = 20
DELAI_EVOLUTION_MS = 280
NB_ESSAIS_AMELIORATION_LOCALE = 18
TAILLE_CACHE_EVALUATION_MAX = 8000

# Pénalités utilisées pour comparer le résultat simulé à la cible.
# Faux négatif : la cible veut une cellule vivante, mais le résultat est mort.
# Faux positif : le résultat a une cellule vivante alors que la cible est morte.
PENALITE_FAUX_NEGATIF = 4
PENALITE_FAUX_POSITIF = 1
PENALITE_DISTANCE_EXTRA = 0.12


# ============================================================
#  COULEURS
# ============================================================

COULEUR_FOND = "#f5f1e8"
COULEUR_GRILLE = "#ddd6c7"

COULEUR_VIVANT = "#2563eb"
COULEUR_CIBLE = "#181818"
COULEUR_INITIAL_ET_CIBLE = "#6c4ab6"

COULEUR_RESULTAT_OK = "#2ecc71"
COULEUR_RESULTAT_EN_TROP = "#e74c3c"
COULEUR_RESULTAT_MANQUANT = "#f39c12"

COULEUR_TEXTE = "#222222"
COULEUR_TEXTE_IMPORTANT = "#7a3cff"
COULEUR_UI_FOND = "#f8fafc"
COULEUR_UI_BOUTON = "#e2e8f0"
COULEUR_UI_BOUTON_PRIMAIRE = "#bbf7d0"
COULEUR_UI_BOUTON_DANGER = "#fee2e2"

# Tiny tie-breaker: when two candidates reach the target equally well,
# prefer the one with fewer live cells in the initial grid.
PENALITE_CELLULE_INITIALE = 0.001


# ============================================================
#  ÉTAT GLOBAL DU PROGRAMME
# ============================================================

etat = {
    "grille": None,              # grille initiale / grille courante
    "cible": None,               # grille finale désirée
    "resultat": None,            # résultat de la meilleure solution trouvée
    "mode": "cible",             # l'interface simple édite seulement la cible
    "vue": "edition",            # "edition", "initial", "resultat" ou "evolution"
    "lecture": False,
    "generation_life": 0,
    "delai_animation": DELAI_ANIMATION_MS,
    "k_inverse": NB_GENERATIONS_INVERSE,

    "solveur_actif": False,
    "solveur": None,
    "evolution": None,
    "evolution_index": 0,
    "evolution_active": False,
    "evolution_id": 0,
}

ui = {
    "panel": None,
    "entree_etapes": None,
    "bouton_start": None,
    "bouton_cible": None,
    "bouton_initial": None,
    "bouton_resultat": None,
    "bouton_evolution": None,
    "bouton_precedent": None,
    "bouton_suivant": None,
    "label_status": None,
}


# ============================================================
#  OUTILS DE GRILLE
# ============================================================

def nouvelle_grille(valeur=0):
    return [[valeur for _ in range(COLONNES)] for _ in range(LIGNES)]


def copier_grille(grille):
    return [ligne[:] for ligne in grille]


def grille_vide(grille):
    for i in range(LIGNES):
        for j in range(COLONNES):
            if grille[i][j] == 1:
                return False
    return True


def nombre_cellules_vivantes(grille):
    total = 0
    for i in range(LIGNES):
        for j in range(COLONNES):
            total += grille[i][j]
    return total


def cle_grille(grille):
    return tuple(cellule for ligne in grille for cellule in ligne)


def cellules_zone(zone):
    lmin, lmax, cmin, cmax = zone
    cellules = []
    for i in range(lmin, lmax + 1):
        for j in range(cmin, cmax + 1):
            cellules.append((i, j))
    return cellules


def limiter_cache(cache):
    if len(cache) <= TAILLE_CACHE_EVALUATION_MAX:
        return

    for cle in list(cache.keys())[:len(cache) - TAILLE_CACHE_EVALUATION_MAX]:
        del cache[cle]


def compter_voisins(grille, ligne, col):
    total = 0

    for dl in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dl == 0 and dc == 0:
                continue

            nl = ligne + dl
            nc = col + dc

            if BORDS_TORIQUES:
                nl = nl % LIGNES
                nc = nc % COLONNES
                total += grille[nl][nc]
            else:
                if 0 <= nl < LIGNES and 0 <= nc < COLONNES:
                    total += grille[nl][nc]

    return total


def generation_suivante(grille):
    suivante = nouvelle_grille(0)

    for i in range(LIGNES):
        for j in range(COLONNES):
            voisins = compter_voisins(grille, i, j)

            if grille[i][j] == 1:
                # Survie si 2 ou 3 voisines vivantes.
                if voisins == 2 or voisins == 3:
                    suivante[i][j] = 1
            else:
                # Naissance si exactement 3 voisines vivantes.
                if voisins == 3:
                    suivante[i][j] = 1

    return suivante


def simuler(grille_initiale, nb_generations):
    grille = copier_grille(grille_initiale)

    for _ in range(nb_generations):
        grille = generation_suivante(grille)

    return grille


def grilles_identiques(g1, g2):
    for i in range(LIGNES):
        for j in range(COLONNES):
            if g1[i][j] != g2[i][j]:
                return False
    return True


# ============================================================
#  SCORE DU SOLVEUR INVERSE
# ============================================================

def construire_carte_distance_cible(cible):
    cellules_cibles = []
    for i in range(LIGNES):
        for j in range(COLONNES):
            if cible[i][j] == 1:
                cellules_cibles.append((i, j))

    carte = [[MAX_MARGE_RECHERCHE + 1 for _ in range(COLONNES)] for _ in range(LIGNES)]
    if not cellules_cibles:
        return carte

    for i in range(LIGNES):
        for j in range(COLONNES):
            meilleur = MAX_MARGE_RECHERCHE + 1
            for ci, cj in cellules_cibles:
                distance = max(abs(i - ci), abs(j - cj))
                if distance < meilleur:
                    meilleur = distance
            carte[i][j] = meilleur

    return carte


def erreur_par_rapport_a_cible(resultat, cible, carte_distance=None):
    """
    Plus l'erreur est petite, meilleure est la solution.

    On pénalise plus fortement les cellules manquantes dans la cible
    que les cellules en trop. Cela évite que le solveur favorise
    trop vite les grilles presque vides. Les cellules en trop loin de
    la cible coûtent un peu plus cher que celles collées à la forme.
    """
    erreur = 0

    for i in range(LIGNES):
        for j in range(COLONNES):
            r = resultat[i][j]
            c = cible[i][j]

            if c == 1 and r == 0:
                erreur += PENALITE_FAUX_NEGATIF
            elif c == 0 and r == 1:
                erreur += PENALITE_FAUX_POSITIF
                if carte_distance is not None:
                    erreur += min(carte_distance[i][j], MAX_MARGE_RECHERCHE) * PENALITE_DISTANCE_EXTRA

    return erreur


def score_exactitude(resultat, cible):
    """
    Pourcentage de cases identiques entre le résultat obtenu et la cible.
    Sert surtout à l'affichage.
    """
    total = LIGNES * COLONNES
    identiques = 0

    for i in range(LIGNES):
        for j in range(COLONNES):
            if resultat[i][j] == cible[i][j]:
                identiques += 1

    return 100.0 * identiques / total


# ============================================================
#  ZONE DE RECHERCHE DU SOLVEUR
# ============================================================

def calculer_zone_recherche(cible, k=NB_GENERATIONS_INVERSE):
    """
    On limite la recherche autour de la cible, avec une marge.
    Cela rend l'algorithme beaucoup plus efficace que chercher
    partout sur la grille.
    """
    lignes = []
    cols = []

    for i in range(LIGNES):
        for j in range(COLONNES):
            if cible[i][j] == 1:
                lignes.append(i)
                cols.append(j)

    if len(lignes) == 0:
        return (0, LIGNES - 1, 0, COLONNES - 1)

    marge = max(MARGE_RECHERCHE, min(MAX_MARGE_RECHERCHE, k + 2))
    lmin = max(0, min(lignes) - marge)
    lmax = min(LIGNES - 1, max(lignes) + marge)
    cmin = max(0, min(cols) - marge)
    cmax = min(COLONNES - 1, max(cols) + marge)

    return (lmin, lmax, cmin, cmax)


def case_dans_zone(i, j, zone):
    lmin, lmax, cmin, cmax = zone
    return lmin <= i <= lmax and cmin <= j <= cmax


# ============================================================
#  ALGORITHME GÉNÉTIQUE
# ============================================================

def individu_aleatoire(zone, densite=DENSITE_INITIALE):
    individu = nouvelle_grille(0)

    lmin, lmax, cmin, cmax = zone

    for i in range(lmin, lmax + 1):
        for j in range(cmin, cmax + 1):
            if random.random() < densite:
                individu[i][j] = 1

    return individu


def individu_aleatoire_guide(zone, carte_distance, densite=DENSITE_INITIALE):
    individu = nouvelle_grille(0)

    lmin, lmax, cmin, cmax = zone
    for i in range(lmin, lmax + 1):
        for j in range(cmin, cmax + 1):
            distance = carte_distance[i][j]
            bonus_pres_cible = max(0, 4 - distance) * 0.035
            proba = min(0.55, densite + bonus_pres_cible)
            if random.random() < proba:
                individu[i][j] = 1

    return individu


def muter(individu, zone, taux_mutation):
    """
    Mutation : chaque cellule de la zone de recherche a une petite chance
    d'être inversée.
    """
    lmin, lmax, cmin, cmax = zone

    for i in range(lmin, lmax + 1):
        for j in range(cmin, cmax + 1):
            if random.random() < taux_mutation:
                individu[i][j] = 1 - individu[i][j]


def muter_zone_guidee(individu, zone, carte_distance, taux_mutation):
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


def croiser(parent_a, parent_b, zone):
    """
    Croisement uniforme :
    chaque cellule vient soit du parent A, soit du parent B.
    """
    enfant = nouvelle_grille(0)

    lmin, lmax, cmin, cmax = zone

    for i in range(lmin, lmax + 1):
        for j in range(cmin, cmax + 1):
            if random.random() < 0.5:
                enfant[i][j] = parent_a[i][j]
            else:
                enfant[i][j] = parent_b[i][j]

    return enfant


def selection_tournoi(population_evaluee, taille_tournoi=5):
    """
    Sélection par tournoi.
    population_evaluee contient des tuples :
    (score_tri, erreur_cible, individu, resultat_simule)
    """
    candidats = random.sample(population_evaluee, taille_tournoi)
    meilleur = min(candidats, key=lambda x: x[0])
    return meilleur[2]


def evaluer_individu(individu, cible, k, cache, carte_distance):
    cle = cle_grille(individu)
    if cle in cache:
        score_tri, erreur_cible, resultat = cache[cle]
        return (score_tri, erreur_cible, individu, copier_grille(resultat))

    resultat = simuler(individu, k)
    erreur_cible = erreur_par_rapport_a_cible(resultat, cible, carte_distance)
    score_tri = erreur_cible + nombre_cellules_vivantes(individu) * PENALITE_CELLULE_INITIALE
    cache[cle] = (score_tri, erreur_cible, copier_grille(resultat))
    limiter_cache(cache)
    return (score_tri, erreur_cible, individu, resultat)


def evaluer_population(population, cible, k, cache, carte_distance):
    population_evaluee = []

    for individu in population:
        population_evaluee.append(evaluer_individu(individu, cible, k, cache, carte_distance))

    population_evaluee.sort(key=lambda x: x[0])
    return population_evaluee


def creer_population_initiale(grille_actuelle, cible, zone, carte_distance):
    population = []

    # 1. On teste la grille actuellement dessinée.
    population.append(copier_grille(grille_actuelle))

    # 2. On teste aussi la cible elle-même comme point de départ naïf.
    population.append(copier_grille(cible))

    # 3. Quelques versions bruitées de la cible.
    for _ in range(8):
        individu = copier_grille(cible)
        muter_zone_guidee(individu, zone, carte_distance, 0.12)
        population.append(individu)

    # 4. Plusieurs densités donnent de meilleurs départs selon le motif cible.
    densites = [0.08, 0.14, 0.20, 0.28, 0.36]
    for densite in densites:
        for _ in range(5):
            population.append(individu_aleatoire_guide(zone, carte_distance, densite))

    # 5. Le reste est généré aléatoirement pour garder de la diversité.
    while len(population) < TAILLE_POPULATION:
        densite = random.choice(densites + [DENSITE_INITIALE])
        population.append(individu_aleatoire_guide(zone, carte_distance, densite))

    return population


def population_sans_doublons(population, zone, carte_distance):
    uniques = []
    vus = set()

    for individu in population:
        cle = cle_grille(individu)
        if cle not in vus:
            vus.add(cle)
            uniques.append(individu)

    densites = [0.08, 0.14, 0.20, 0.28, 0.36, DENSITE_INITIALE]
    while len(uniques) < TAILLE_POPULATION:
        individu = individu_aleatoire_guide(zone, carte_distance, random.choice(densites))
        cle = cle_grille(individu)
        if cle not in vus:
            vus.add(cle)
            uniques.append(individu)

    return uniques[:TAILLE_POPULATION]


def ameliorer_individu_local(individu, cible, k, zone, cache, carte_distance):
    meilleur = copier_grille(individu)
    meilleur_eval = evaluer_individu(meilleur, cible, k, cache, carte_distance)
    cellules = cellules_zone(zone)

    for _ in range(NB_ESSAIS_AMELIORATION_LOCALE):
        i, j = random.choice(cellules)
        candidat = copier_grille(meilleur)
        candidat[i][j] = 1 - candidat[i][j]
        candidat_eval = evaluer_individu(candidat, cible, k, cache, carte_distance)

        if candidat_eval[0] < meilleur_eval[0]:
            meilleur = candidat
            meilleur_eval = candidat_eval

    return meilleur_eval


def initialiser_solveur():
    zone = calculer_zone_recherche(etat["cible"], etat["k_inverse"])
    carte_distance = construire_carte_distance_cible(etat["cible"])

    population = creer_population_initiale(
        etat["grille"],
        etat["cible"],
        zone,
        carte_distance
    )

    etat["solveur"] = {
        "population": population,
        "generation": 0,
        "zone": zone,
        "carte_distance": carte_distance,
        "cache": {},
        "stagnation": 0,
        "meilleure_note_tri": None,
        "meilleure_erreur": None,
        "meilleur_individu": None,
        "meilleur_resultat": None,
        "meilleur_score": 0.0,
    }

    etat["solveur_actif"] = True
    etat["lecture"] = False
    etat["vue"] = "initial"


def avancer_solveur_une_generation():
    solveur = etat["solveur"]
    cible = etat["cible"]
    k = etat["k_inverse"]
    zone = solveur["zone"]
    cache = solveur["cache"]
    carte_distance = solveur["carte_distance"]

    population = solveur["population"]
    population_evaluee = evaluer_population(population, cible, k, cache, carte_distance)

    candidat_local = ameliorer_individu_local(population_evaluee[0][2], cible, k, zone, cache, carte_distance)
    if candidat_local[0] < population_evaluee[0][0]:
        population_evaluee.insert(0, candidat_local)
    else:
        population_evaluee.append(candidat_local)
        population_evaluee.sort(key=lambda x: x[0])

    meilleure_note_tri, meilleure_erreur, meilleur_individu, meilleur_resultat = population_evaluee[0]
    meilleur_score = score_exactitude(meilleur_resultat, cible)

    if solveur["meilleure_note_tri"] is None or meilleure_note_tri < solveur["meilleure_note_tri"]:
        solveur["meilleure_note_tri"] = meilleure_note_tri
        solveur["meilleure_erreur"] = meilleure_erreur
        solveur["meilleur_individu"] = copier_grille(meilleur_individu)
        solveur["meilleur_resultat"] = copier_grille(meilleur_resultat)
        solveur["meilleur_score"] = meilleur_score

        etat["grille"] = copier_grille(meilleur_individu)
        etat["resultat"] = copier_grille(meilleur_resultat)
        etat["evolution"] = None
        etat["evolution_index"] = 0
        solveur["stagnation"] = 0
    else:
        solveur["stagnation"] += 1

    # Condition d'arrêt parfaite.
    if meilleure_erreur == 0:
        etat["solveur_actif"] = False
        return

    # Condition d'arrêt par nombre de générations génétiques.
    if solveur["generation"] >= NB_GENERATIONS_GENETIQUES_MAX:
        etat["solveur_actif"] = False
        return

    nouvelle_population = []
    taux_mutation = TAUX_MUTATION * (1 + min(4, solveur["stagnation"] // 25))
    taux_injection = TAUX_INJECTION_ALEATOIRE
    if solveur["stagnation"] >= 35:
        taux_injection = min(0.18, TAUX_INJECTION_ALEATOIRE * 2.5)

    # Élitisme : on garde les meilleurs tels quels.
    for i in range(NB_ELITES):
        elite = population_evaluee[i][2]
        nouvelle_population.append(copier_grille(elite))

    # Injection aléatoire : évite que la population devienne trop uniforme.
    nb_injections = int(TAILLE_POPULATION * taux_injection)
    densites = [0.08, 0.14, 0.20, 0.28, 0.36, DENSITE_INITIALE]
    for _ in range(nb_injections):
        nouvelle_population.append(individu_aleatoire_guide(zone, carte_distance, random.choice(densites)))

    # Reproduction : sélection + croisement + mutation.
    while len(nouvelle_population) < TAILLE_POPULATION:
        parent_a = selection_tournoi(population_evaluee)
        parent_b = selection_tournoi(population_evaluee)

        enfant = croiser(parent_a, parent_b, zone)
        muter_zone_guidee(enfant, zone, carte_distance, taux_mutation)

        nouvelle_population.append(enfant)

    solveur["population"] = population_sans_doublons(nouvelle_population, zone, carte_distance)
    solveur["generation"] += 1


# ============================================================
#  AFFICHAGE ENISEBOARD
# ============================================================

def couleur_case_edition(i, j):
    if etat["cible"][i][j] == 1:
        return COULEUR_CIBLE

    return ""


def couleur_case_initiale(i, j):
    vivant = etat["grille"][i][j]
    cible = etat["cible"][i][j]

    if vivant == 1 and cible == 1:
        return COULEUR_INITIAL_ET_CIBLE
    if vivant == 1:
        return COULEUR_VIVANT
    if cible == 1:
        return "#cbd5e1"

    return ""


def couleur_case_resultat(i, j):
    if etat["resultat"] is None:
        return couleur_case_initiale(i, j)

    resultat = etat["resultat"][i][j]
    cible = etat["cible"][i][j]

    if resultat == 1 and cible == 1:
        return COULEUR_RESULTAT_OK
    if resultat == 1 and cible == 0:
        return COULEUR_RESULTAT_EN_TROP
    if resultat == 0 and cible == 1:
        return COULEUR_RESULTAT_MANQUANT

    return ""


def couleur_case_evolution(i, j):
    if etat["evolution"] is None:
        return couleur_case_initiale(i, j)

    courant = etat["evolution"][etat["evolution_index"]][i][j]
    cible = etat["cible"][i][j]

    if courant == 1 and cible == 1:
        return COULEUR_INITIAL_ET_CIBLE
    if courant == 1:
        return COULEUR_VIVANT
    if cible == 1:
        return "#f8c471"

    return ""


def rafraichir_plateau(board):
    for i in range(LIGNES):
        for j in range(COLONNES):
            if etat["vue"] == "resultat":
                couleur = couleur_case_resultat(i, j)
            elif etat["vue"] == "evolution":
                couleur = couleur_case_evolution(i, j)
            elif etat["vue"] == "initial":
                couleur = couleur_case_initiale(i, j)
            else:
                couleur = couleur_case_edition(i, j)

            board.setBgColor(i, j, couleur)


def afficher_ligne(board, ligne, texte, couleur=COULEUR_TEXTE):
    # Padding pour effacer correctement l'ancien contenu de la ligne.
    board.display(texte.ljust(120), row=ligne, col=0, color=couleur)


def racine_tk(board):
    return getattr(board, "_eniseboard__root", None)


def creer_bouton(parent, texte, commande, couleur=COULEUR_UI_BOUTON):
    bouton = tk.Button(
        parent,
        text=texte,
        command=commande,
        bg=couleur,
        fg=COULEUR_TEXTE,
        activebackground=couleur,
        activeforeground=COULEUR_TEXTE,
        relief=tk.FLAT,
        bd=0,
        padx=12,
        pady=8,
        cursor="hand2",
        anchor="w",
    )
    bouton.pack(fill="x", pady=4)
    return bouton


def creer_titre_section(parent, texte):
    tk.Label(
        parent,
        text=texte.upper(),
        bg=COULEUR_UI_FOND,
        fg="#64748b",
        font=("TkDefaultFont", 9, "bold"),
        anchor="w",
    ).pack(fill="x", padx=8, pady=(12, 2))


def creer_interface_simple(board):
    root = racine_tk(board)
    if root is None:
        return

    root.configure(bg=COULEUR_UI_FOND)
    root.columnconfigure(0, weight=0)
    root.columnconfigure(1, weight=0)
    root.rowconfigure(0, weight=1)

    if ui["panel"] is not None and ui["panel"].winfo_exists():
        ui["panel"].destroy()

    panel = tk.Frame(root, bg=COULEUR_UI_FOND, width=210)
    panel.grid(row=0, column=1, rowspan=3, sticky="ns", padx=(8, 10), pady=10)
    panel.grid_propagate(False)
    ui["panel"] = panel

    tk.Label(
        panel,
        text="Life Pattern Hunter",
        bg=COULEUR_UI_FOND,
        fg=COULEUR_TEXTE,
        font=("TkDefaultFont", 13, "bold"),
        anchor="w",
    ).pack(fill="x", padx=8, pady=(2, 10))

    tk.Label(
        panel,
        text="Steps",
        bg=COULEUR_UI_FOND,
        fg=COULEUR_TEXTE,
        font=("TkDefaultFont", 10, "bold"),
        anchor="w",
    ).pack(fill="x", padx=8)

    entree = tk.Entry(panel, width=8, justify="center")
    entree.insert(0, str(etat["k_inverse"]))
    entree.pack(fill="x", padx=8, pady=(4, 12))
    ui["entree_etapes"] = entree

    ui["bouton_start"] = creer_bouton(
        panel,
        "Start",
        lambda: lancer_ou_arreter_solveur(board),
        COULEUR_UI_BOUTON_PRIMAIRE,
    )

    creer_titre_section(panel, "View")
    ui["bouton_cible"] = creer_bouton(
        panel,
        "Edit target",
        lambda: afficher_vue(board, "edition"),
    )
    ui["bouton_initial"] = creer_bouton(
        panel,
        "Best initial",
        lambda: afficher_vue(board, "initial"),
    )
    ui["bouton_resultat"] = creer_bouton(
        panel,
        "Show result",
        lambda: afficher_vue(board, "resultat"),
    )
    ui["bouton_evolution"] = creer_bouton(
        panel,
        "Play evolution",
        lambda: lancer_ou_arreter_evolution(board),
    )
    ui["bouton_precedent"] = creer_bouton(
        panel,
        "Previous step",
        lambda: deplacer_evolution(board, -1),
    )
    ui["bouton_suivant"] = creer_bouton(
        panel,
        "Next step",
        lambda: deplacer_evolution(board, 1),
    )

    creer_titre_section(panel, "Reset")
    creer_bouton(panel, "Clear", lambda: effacer_depuis_interface(board), COULEUR_UI_BOUTON_DANGER)

    ui["label_status"] = tk.Label(
        panel,
        text="Draw the finish pattern. Set Steps. Press Start.",
        bg=COULEUR_UI_FOND,
        fg="#475569",
        justify="left",
        wraplength=180,
        anchor="w",
    )
    ui["label_status"].pack(fill="x", padx=8, pady=(12, 0))

    actualiser_interface()


def actualiser_interface():
    bouton_start = ui.get("bouton_start")
    if bouton_start is not None and bouton_start.winfo_exists():
        bouton_start.configure(text="Stop" if etat["solveur_actif"] else "Start")

    resultat_disponible = etat["resultat"] is not None
    evolution_disponible = resultat_disponible or etat["evolution"] is not None

    for key in ("bouton_initial", "bouton_resultat"):
        bouton = ui.get(key)
        if bouton is not None and bouton.winfo_exists():
            bouton.configure(state=tk.NORMAL if resultat_disponible else tk.DISABLED)

    for key in ("bouton_evolution", "bouton_precedent", "bouton_suivant"):
        bouton = ui.get(key)
        if bouton is not None and bouton.winfo_exists():
            bouton.configure(state=tk.NORMAL if evolution_disponible else tk.DISABLED)

    bouton_evolution = ui.get("bouton_evolution")
    if bouton_evolution is not None and bouton_evolution.winfo_exists():
        bouton_evolution.configure(text="Stop evolution" if etat["evolution_active"] else "Play evolution")

    status = ui.get("label_status")
    if status is not None and status.winfo_exists():
        if etat["solveur_actif"] and etat["solveur"] is not None:
            s = etat["solveur"]
            status.configure(
                text="Searching... gen {} / {}, error {:.2f}, cache {}".format(
                    s["generation"],
                    NB_GENERATIONS_GENETIQUES_MAX,
                    s["meilleure_erreur"] if s["meilleure_erreur"] is not None else 0,
                    len(s["cache"]),
                )
            )
        elif etat["vue"] == "evolution" and etat["evolution"] is not None:
            status.configure(
                text="Evolution step {} / {}.".format(
                    etat["evolution_index"],
                    len(etat["evolution"]) - 1,
                )
            )
        elif resultat_disponible:
            status.configure(text="Best initial grid found. Check result or play evolution.")
        else:
            status.configure(text="Draw the finish pattern. Set Steps. Press Start.")


def lire_nb_etapes_depuis_interface(board):
    entree = ui.get("entree_etapes")
    if entree is None or not entree.winfo_exists():
        return True

    texte = entree.get().strip()
    try:
        valeur = int(texte)
    except ValueError:
        board.console("Nombre d'étapes invalide :", texte)
        entree.delete(0, tk.END)
        entree.insert(0, str(etat["k_inverse"]))
        return False

    if valeur < 1:
        board.console("Le nombre d'étapes doit être au moins 1.")
        entree.delete(0, tk.END)
        entree.insert(0, str(etat["k_inverse"]))
        return False

    etat["k_inverse"] = valeur
    return True


def synchroniser_entree_etapes():
    entree = ui.get("entree_etapes")
    if entree is not None and entree.winfo_exists():
        entree.delete(0, tk.END)
        entree.insert(0, str(etat["k_inverse"]))


def effacer_depuis_interface(board):
    tout_effacer()
    rafraichir_plateau(board)
    afficher_infos(board)


def afficher_vue(board, vue):
    if vue in ("initial", "resultat") and etat["resultat"] is None:
        return

    if vue == "evolution":
        preparer_evolution()
        if etat["evolution"] is None:
            return
    else:
        etat["evolution_active"] = False

    if vue == "edition":
        etat["solveur_actif"] = False

    etat["vue"] = vue
    rafraichir_plateau(board)
    afficher_infos(board)


def preparer_evolution(reset_index=True):
    if etat["grille"] is None or etat["resultat"] is None:
        return

    if etat["evolution"] is not None and len(etat["evolution"]) == etat["k_inverse"] + 1:
        if reset_index:
            etat["evolution_index"] = 0
        else:
            etat["evolution_index"] = min(etat["evolution_index"], len(etat["evolution"]) - 1)
        return

    ancien_index = etat["evolution_index"]
    evolution = [copier_grille(etat["grille"])]
    courant = copier_grille(etat["grille"])

    for _ in range(etat["k_inverse"]):
        courant = generation_suivante(courant)
        evolution.append(copier_grille(courant))

    etat["evolution"] = evolution
    if reset_index:
        etat["evolution_index"] = 0
    else:
        etat["evolution_index"] = min(ancien_index, len(evolution) - 1)


def lancer_ou_arreter_evolution(board):
    if etat["evolution_active"]:
        etat["evolution_active"] = False
        afficher_infos(board)
        return

    preparer_evolution()
    if etat["evolution"] is None:
        return

    etat["evolution_id"] += 1
    evolution_id = etat["evolution_id"]
    etat["evolution_active"] = True
    etat["evolution_index"] = 0
    etat["vue"] = "evolution"
    rafraichir_plateau(board)
    afficher_infos(board)
    board.after(DELAI_EVOLUTION_MS, boucle_evolution, board, evolution_id)


def boucle_evolution(board, evolution_id):
    if not etat["evolution_active"] or evolution_id != etat["evolution_id"]:
        return

    if etat["evolution"] is None:
        etat["evolution_active"] = False
        afficher_infos(board)
        return

    if etat["evolution_index"] >= len(etat["evolution"]) - 1:
        etat["evolution_active"] = False
        afficher_infos(board)
        return

    etat["evolution_index"] += 1
    etat["vue"] = "evolution"
    rafraichir_plateau(board)
    afficher_infos(board)
    board.after(DELAI_EVOLUTION_MS, boucle_evolution, board, evolution_id)


def deplacer_evolution(board, delta):
    preparer_evolution(reset_index=False)
    if etat["evolution"] is None:
        return

    etat["evolution_active"] = False
    etat["evolution_index"] = max(
        0,
        min(len(etat["evolution"]) - 1, etat["evolution_index"] + delta)
    )
    etat["vue"] = "evolution"
    rafraichir_plateau(board)
    afficher_infos(board)


def afficher_infos(board):
    vue = etat["vue"]
    k = etat["k_inverse"]

    afficher_ligne(
        board,
        0,
        "Target cells: {} | View: {} | Steps: {}".format(
            nombre_cellules_vivantes(etat["cible"]),
            vue.upper(),
            k
        ),
        COULEUR_TEXTE_IMPORTANT
    )

    if etat["vue"] == "evolution" and etat["evolution"] is not None:
        ligne_1 = "Evolution step {} / {}: blue=current, purple=matches target, orange=missing target.".format(
            etat["evolution_index"],
            len(etat["evolution"]) - 1,
        )
    else:
        ligne_1 = "Draw the desired finish grid, set Steps, then click Start."

    afficher_ligne(board, 1, ligne_1)

    afficher_ligne(
        board,
        2,
        "Keys: S start/stop | V result/initial | T edit target | X clear | ↑/↓ steps"
    )

    if etat["solveur_actif"] and etat["solveur"] is not None:
        s = etat["solveur"]
        afficher_ligne(
            board,
            3,
            "Searching | genetic gen {} / {} | error {:.2f} | accuracy {:.2f}% | stagnation {}".format(
                s["generation"],
                NB_GENERATIONS_GENETIQUES_MAX,
                s["meilleure_erreur"] if s["meilleure_erreur"] is not None else 0,
                s["meilleur_score"],
                s["stagnation"]
            ),
            COULEUR_TEXTE_IMPORTANT
        )

    elif etat["solveur"] is not None:
        s = etat["solveur"]
        afficher_ligne(
            board,
            3,
            "Stopped | genetic gen {} | error {:.2f} | accuracy {:.2f}% | initial cells {}".format(
                s["generation"],
                s["meilleure_erreur"] if s["meilleure_erreur"] is not None else 0,
                s["meilleur_score"],
                nombre_cellules_vivantes(etat["grille"])
            ),
            COULEUR_TEXTE_IMPORTANT
        )

    else:
        afficher_ligne(
            board,
            3,
            "Initial live cells: {} | desired finish cells: {}".format(
                nombre_cellules_vivantes(etat["grille"]) if etat["grille"] is not None else 0,
                nombre_cellules_vivantes(etat["cible"])
            )
        )

    actualiser_interface()


# ============================================================
#  BOUCLES TEMPORELLES
# ============================================================

def boucle_animation(board):
    if not etat["lecture"]:
        return

    etat["grille"] = generation_suivante(etat["grille"])
    etat["generation_life"] += 1
    etat["resultat"] = None
    etat["vue"] = "edition"

    rafraichir_plateau(board)
    afficher_infos(board)

    board.after(etat["delai_animation"], boucle_animation, board)


def boucle_solveur(board):
    if not etat["solveur_actif"]:
        rafraichir_plateau(board)
        afficher_infos(board)
        return

    for _ in range(NB_ITERATIONS_SOLVEUR_PAR_TICK):
        if etat["solveur_actif"]:
            avancer_solveur_une_generation()

    rafraichir_plateau(board)
    afficher_infos(board)

    if etat["solveur_actif"]:
        board.after(DELAI_SOLVEUR_MS, boucle_solveur, board)


# ============================================================
#  ACTIONS UTILISATEUR
# ============================================================

def effacer_mode_courant():
    if etat["mode"] == "initial":
        etat["grille"] = nouvelle_grille(0)
        etat["generation_life"] = 0
    else:
        etat["cible"] = nouvelle_grille(0)

    etat["resultat"] = None
    etat["solveur"] = None
    etat["solveur_actif"] = False


def tout_effacer():
    etat["grille"] = nouvelle_grille(0)
    etat["cible"] = nouvelle_grille(0)
    etat["resultat"] = None
    etat["solveur"] = None
    etat["solveur_actif"] = False
    etat["evolution"] = None
    etat["evolution_index"] = 0
    etat["evolution_active"] = False
    etat["evolution_id"] += 1
    etat["generation_life"] = 0
    etat["lecture"] = False
    etat["vue"] = "edition"


def remplir_initial_aleatoire():
    etat["grille"] = nouvelle_grille(0)

    for i in range(LIGNES):
        for j in range(COLONNES):
            if random.random() < DENSITE_INITIALE:
                etat["grille"][i][j] = 1

    etat["generation_life"] = 0
    etat["resultat"] = None
    etat["solveur"] = None
    etat["solveur_actif"] = False
    etat["evolution"] = None
    etat["evolution_index"] = 0
    etat["evolution_active"] = False
    etat["evolution_id"] += 1
    etat["vue"] = "edition"


def lancer_ou_arreter_solveur(board):
    if etat["solveur_actif"]:
        etat["solveur_actif"] = False
        rafraichir_plateau(board)
        afficher_infos(board)
        return

    if not lire_nb_etapes_depuis_interface(board):
        rafraichir_plateau(board)
        afficher_infos(board)
        return

    if grille_vide(etat["cible"]):
        board.console("Impossible de lancer le solveur : la cible est vide.")
        return

    etat["evolution_active"] = False
    etat["evolution"] = None
    etat["evolution_index"] = 0
    etat["evolution_id"] += 1
    initialiser_solveur()
    rafraichir_plateau(board)
    afficher_infos(board)
    board.after(1, boucle_solveur, board)


def basculer_vue(board=None):
    if etat["resultat"] is None:
        return

    etat["evolution_active"] = False
    if etat["vue"] == "resultat":
        etat["vue"] = "initial"
    else:
        etat["vue"] = "resultat"

    if board is not None:
        rafraichir_plateau(board)
        afficher_infos(board)


# ============================================================
#  CALLBACK SOURIS
# ============================================================

def gestion_souris(board, event):
    ligne = event["row"]
    col = event["col"]

    if not (0 <= ligne < LIGNES and 0 <= col < COLONNES):
        return

    grille = etat["cible"]

    # Clic droit : efface.
    if event.get("button3", False):
        grille[ligne][col] = 0
    else:
        # Clic gauche : inverse l'état.
        grille[ligne][col] = 1 - grille[ligne][col]

    etat["resultat"] = None
    etat["solveur"] = None
    etat["solveur_actif"] = False
    etat["evolution"] = None
    etat["evolution_index"] = 0
    etat["evolution_active"] = False
    etat["evolution_id"] += 1
    etat["vue"] = "edition"

    rafraichir_plateau(board)
    afficher_infos(board)


# ============================================================
#  CALLBACK CLAVIER
# ============================================================

def gestion_clavier(board, event):
    touche = event["keysym"]
    t = touche.lower()

    if t == "t":
        etat["evolution_active"] = False
        etat["vue"] = "edition"

    elif t == "v":
        basculer_vue()

    elif t == "x":
        tout_effacer()

    elif t == "s":
        lancer_ou_arreter_solveur(board)

    elif t in ("up", "right"):
        etat["k_inverse"] += 1
        synchroniser_entree_etapes()
        etat["resultat"] = None
        etat["solveur"] = None
        etat["solveur_actif"] = False
        etat["evolution"] = None
        etat["evolution_active"] = False
        etat["evolution_id"] += 1

    elif t in ("down", "left"):
        etat["k_inverse"] = max(1, etat["k_inverse"] - 1)
        synchroniser_entree_etapes()
        etat["resultat"] = None
        etat["solveur"] = None
        etat["solveur_actif"] = False
        etat["evolution"] = None
        etat["evolution_active"] = False
        etat["evolution_id"] += 1

    elif t == "escape":
        etat["lecture"] = False
        etat["solveur_actif"] = False
        etat["evolution_active"] = False

    rafraichir_plateau(board)
    afficher_infos(board)


# ============================================================
#  INITIALISATION ENISEBOARD
# ============================================================

def initialiser(board):
    etat["grille"] = nouvelle_grille(0)
    etat["cible"] = nouvelle_grille(0)
    etat["resultat"] = None

    creer_interface_simple(board)
    rafraichir_plateau(board)
    afficher_infos(board)

    board.console("Life Pattern Hunter prêt.")
    board.console("Dessinez la grille finale, choisissez Steps, puis cliquez Start.")


# ============================================================
#  LANCEMENT
# ============================================================

eniseboard(
    hsize=COLONNES,
    vsize=LIGNES,
    cell=TAILLE_CASE,
    grid=True,
    title="Life Pattern Hunter",
    bgcolor=COULEUR_FOND,
    info=True,
    infoPlace="down",
    infoLines=4,
    console=True,
    consolePlace="down",
    init=initialiser,
    click=gestion_souris,
    key=gestion_clavier
)
