"""Regles normales du jeu de la vie de Conway.

Ce module ne connait ni Tkinter, ni Eniseboard, ni l'algorithme genetique.
Il sert de socle testable pour les deux modes de l'application.
"""

ROWS = 24
COLS = 24
TOROIDAL_BORDERS = False


def nouvelle_grille(valeur=0, rows=ROWS, cols=COLS):
    return [[valeur for _ in range(cols)] for _ in range(rows)]


def copier_grille(grille):
    return [ligne[:] for ligne in grille]


def dimensions(grille):
    return len(grille), len(grille[0]) if grille else 0


def grille_vide(grille):
    return all(cellule == 0 for ligne in grille for cellule in ligne)


def nombre_cellules_vivantes(grille):
    return sum(sum(ligne) for ligne in grille)


def cle_grille(grille):
    return tuple(cellule for ligne in grille for cellule in ligne)


def grilles_identiques(g1, g2):
    return g1 == g2


def compter_voisins(grille, ligne, col, bords_toriques=TOROIDAL_BORDERS):
    rows, cols = dimensions(grille)
    total = 0

    for dl in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dl == 0 and dc == 0:
                continue

            nl = ligne + dl
            nc = col + dc

            if bords_toriques:
                total += grille[nl % rows][nc % cols]
            elif 0 <= nl < rows and 0 <= nc < cols:
                total += grille[nl][nc]

    return total


def generation_suivante(grille, bords_toriques=TOROIDAL_BORDERS):
    rows, cols = dimensions(grille)
    suivante = nouvelle_grille(0, rows, cols)

    for i in range(rows):
        for j in range(cols):
            voisins = compter_voisins(grille, i, j, bords_toriques)

            if grille[i][j] == 1 and voisins in (2, 3):
                suivante[i][j] = 1
            elif grille[i][j] == 0 and voisins == 3:
                suivante[i][j] = 1

    return suivante


def simuler(grille_initiale, nb_generations, bords_toriques=TOROIDAL_BORDERS):
    grille = copier_grille(grille_initiale)

    for _ in range(nb_generations):
        grille = generation_suivante(grille, bords_toriques)

    return grille


def historique_evolution(grille_initiale, nb_generations, bords_toriques=TOROIDAL_BORDERS):
    historique = [copier_grille(grille_initiale)]
    courant = copier_grille(grille_initiale)

    for _ in range(nb_generations):
        courant = generation_suivante(courant, bords_toriques)
        historique.append(copier_grille(courant))

    return historique
