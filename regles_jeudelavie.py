"""Règles du Jeu de la vie de Conway.

Ce fichier ne cherche pas à résoudre le problème inverse. Il contient seulement
les outils de base pour créer, copier et faire évoluer une grille.
"""

NB_LIGNES = 24
NB_COLONNES = 24
BORDS_TORIQUES = False


def nouvelle_grille(valeur=0, lignes=NB_LIGNES, colonnes=NB_COLONNES):
    """Crée une grille remplie avec la même valeur partout."""
    return [[valeur for _ in range(colonnes)] for _ in range(lignes)]


def copier_grille(grille):
    """Copie une grille ligne par ligne pour éviter les modifications cachées."""
    return [ligne[:] for ligne in grille]


def dimensions(grille):
    """Renvoie le nombre de lignes et de colonnes d'une grille."""
    return len(grille), len(grille[0]) if grille else 0


def grille_vide(grille):
    """Indique si aucune cellule vivante n'est présente."""
    return all(cellule == 0 for ligne in grille for cellule in ligne)


def nombre_cellules_vivantes(grille):
    """Compte les cellules vivantes de toute la grille."""
    return sum(sum(ligne) for ligne in grille)


def cle_grille(grille):
    """Transforme une grille en tuple utilisable comme clé de dictionnaire."""
    return tuple(cellule for ligne in grille for cellule in ligne)


def grilles_identiques(premiere, seconde):
    """Compare deux grilles sans ajouter de logique supplémentaire."""
    return premiere == seconde


def compter_voisins(grille, ligne, colonne, bords_toriques=BORDS_TORIQUES):
    """Compte les voisines vivantes autour d'une cellule."""
    nb_lignes, nb_colonnes = dimensions(grille)
    total = 0

    for decalage_ligne in (-1, 0, 1):
        for decalage_colonne in (-1, 0, 1):
            if decalage_ligne == 0 and decalage_colonne == 0:
                continue

            voisine_ligne = ligne + decalage_ligne
            voisine_colonne = colonne + decalage_colonne

            if bords_toriques:
                total += grille[voisine_ligne % nb_lignes][voisine_colonne % nb_colonnes]
            elif 0 <= voisine_ligne < nb_lignes and 0 <= voisine_colonne < nb_colonnes:
                total += grille[voisine_ligne][voisine_colonne]

    return total


def generation_suivante(grille, bords_toriques=BORDS_TORIQUES):
    """Calcule la génération suivante avec les règles classiques."""
    nb_lignes, nb_colonnes = dimensions(grille)
    suivante = nouvelle_grille(0, nb_lignes, nb_colonnes)

    for ligne in range(nb_lignes):
        for colonne in range(nb_colonnes):
            voisins = compter_voisins(grille, ligne, colonne, bords_toriques)

            if grille[ligne][colonne] == 1 and voisins in (2, 3):
                suivante[ligne][colonne] = 1
            elif grille[ligne][colonne] == 0 and voisins == 3:
                suivante[ligne][colonne] = 1

    return suivante


def simuler(grille_initiale, nb_generations, bords_toriques=BORDS_TORIQUES):
    """Fait avancer une grille pendant un nombre donné de générations."""
    grille = copier_grille(grille_initiale)

    for _ in range(nb_generations):
        grille = generation_suivante(grille, bords_toriques)

    return grille


def historique_evolution(grille_initiale, nb_generations, bords_toriques=BORDS_TORIQUES):
    """Garde toutes les étapes d'une évolution pour pouvoir la rejouer."""
    historique = [copier_grille(grille_initiale)]
    courant = copier_grille(grille_initiale)

    for _ in range(nb_generations):
        courant = generation_suivante(courant, bords_toriques)
        historique.append(copier_grille(courant))

    return historique
