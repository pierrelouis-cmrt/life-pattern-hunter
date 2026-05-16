#!/usr/bin/env python3
"""Génère les PNG pédagogiques utilisés par les markdowns et les slides.

Le script utilise uniquement la bibliothèque standard. Il écrit directement des
fichiers PNG RGB avec ``zlib`` pour éviter d'ajouter Pillow ou matplotlib au
projet.
"""

import argparse
import os
import struct
import zlib

from life_rules import generation_suivante, nouvelle_grille


ASSET_DIR = os.path.join("assets", "gol_visuals")

BLANC = (255, 255, 255)
FOND = (247, 250, 252)
PANNEAU = (239, 246, 255)
GRILLE = (184, 198, 219)
VIVANTE = (37, 99, 235)
MORTE = (241, 245, 249)
SURVIT = (22, 163, 74)
NAIT = (134, 239, 172)
MEURT = (239, 68, 68)
CIBLE = (17, 24, 39)
PARENT_A = (59, 130, 246)
PARENT_B = (147, 51, 234)
ENFANT = (20, 184, 166)
MUTATION = (236, 72, 153)
TEXTE = (15, 23, 42)
TEXTE_DISCRET = (71, 85, 105)


FONT_5X7 = {
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ">": ["10000", "01000", "00100", "00010", "00100", "01000", "10000"],
    "/": ["00001", "00010", "00100", "01000", "10000", "00000", "00000"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["10010", "10010", "10010", "11111", "00010", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10011", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}


def grille_depuis_cellules(rows, cols, cellules):
    grille = nouvelle_grille(0, rows, cols)
    for ligne, col in cellules:
        grille[ligne][col] = 1
    return grille


def creer_image(largeur, hauteur, couleur=BLANC):
    return [[couleur for _ in range(largeur)] for _ in range(hauteur)]


def remplir_rectangle(image, x0, y0, x1, y1, couleur):
    hauteur = len(image)
    largeur = len(image[0]) if image else 0
    for y in range(max(0, y0), min(hauteur, y1)):
        for x in range(max(0, x0), min(largeur, x1)):
            image[y][x] = couleur


def dessiner_rectangle_contour(image, x0, y0, x1, y1, couleur, epaisseur=2):
    remplir_rectangle(image, x0, y0, x1, y0 + epaisseur, couleur)
    remplir_rectangle(image, x0, y1 - epaisseur, x1, y1, couleur)
    remplir_rectangle(image, x0, y0, x0 + epaisseur, y1, couleur)
    remplir_rectangle(image, x1 - epaisseur, y0, x1, y1, couleur)


def dessiner_texte(image, texte, x, y, couleur=TEXTE, taille=2):
    curseur = x
    for caractere in texte.upper():
        motif = FONT_5X7.get(caractere, FONT_5X7[" "])
        for ligne, pixels in enumerate(motif):
            for col, pixel in enumerate(pixels):
                if pixel == "1":
                    remplir_rectangle(
                        image,
                        curseur + col * taille,
                        y + ligne * taille,
                        curseur + (col + 1) * taille,
                        y + (ligne + 1) * taille,
                        couleur,
                    )
        curseur += 6 * taille


def dessiner_fleche(image, x0, y0, x1, y1, couleur):
    if x0 == x1:
        pas = 1 if y1 >= y0 else -1
        for y in range(y0, y1, pas):
            remplir_rectangle(image, x0 - 2, y, x0 + 3, y + 1, couleur)
        pointe_y = y1
        remplir_rectangle(image, x1 - 6, pointe_y - pas * 7, x1 + 7, pointe_y - pas * 4, couleur)
        return

    pas = 1 if x1 >= x0 else -1
    for x in range(x0, x1, pas):
        remplir_rectangle(image, x, y0 - 2, x + 1, y0 + 3, couleur)
    pointe_x = x1
    remplir_rectangle(image, pointe_x - pas * 7, y1 - 6, pointe_x - pas * 4, y1 + 7, couleur)


def dessiner_plus(image, centre_x, centre_y, couleur):
    remplir_rectangle(image, centre_x - 18, centre_y - 4, centre_x + 19, centre_y + 5, couleur)
    remplir_rectangle(image, centre_x - 4, centre_y - 18, centre_x + 5, centre_y + 19, couleur)


def dessiner_egal(image, centre_x, centre_y, couleur):
    remplir_rectangle(image, centre_x - 20, centre_y - 12, centre_x + 21, centre_y - 4, couleur)
    remplir_rectangle(image, centre_x - 20, centre_y + 4, centre_x + 21, centre_y + 12, couleur)


def couleur_transition(avant, apres):
    if avant == 1 and apres == 1:
        return SURVIT
    if avant == 1 and apres == 0:
        return MEURT
    if avant == 0 and apres == 1:
        return NAIT
    return MORTE


def dessiner_grille(
    image,
    grille,
    x,
    y,
    cell=30,
    marge=2,
    couleurs=None,
    contour=True,
):
    couleurs = couleurs or {}
    rows = len(grille)
    cols = len(grille[0]) if rows else 0
    remplir_rectangle(image, x, y, x + cols * cell + marge, y + rows * cell + marge, GRILLE)

    for i in range(rows):
        for j in range(cols):
            couleur = couleurs.get((i, j))
            if couleur is None:
                couleur = VIVANTE if grille[i][j] else MORTE
            x0 = x + j * cell + marge
            y0 = y + i * cell + marge
            remplir_rectangle(image, x0, y0, x0 + cell - marge, y0 + cell - marge, couleur)

    if contour:
        dessiner_rectangle_contour(
            image,
            x,
            y,
            x + cols * cell + marge,
            y + rows * cell + marge,
            TEXTE,
            2,
        )


def ajouter_legende_couleurs(image, x, y, couleurs):
    for index, item in enumerate(couleurs):
        couleur, label = item if isinstance(item, tuple) and isinstance(item[1], str) else (item, "")
        x0 = x + index * 126
        remplir_rectangle(image, x0, y, x0 + 28, y + 28, couleur)
        dessiner_rectangle_contour(image, x0, y, x0 + 28, y + 28, TEXTE, 1)
        if label:
            dessiner_texte(image, label, x0 + 36, y + 6, TEXTE_DISCRET, 2)


def ecrire_png(chemin, image):
    hauteur = len(image)
    largeur = len(image[0]) if hauteur else 0

    def chunk(type_chunk, donnees):
        contenu = type_chunk + donnees
        return (
            struct.pack(">I", len(donnees))
            + contenu
            + struct.pack(">I", zlib.crc32(contenu) & 0xFFFFFFFF)
        )

    lignes = []
    for ligne in image:
        donnees_ligne = bytearray([0])
        for r, g, b in ligne:
            donnees_ligne.extend((r, g, b))
        lignes.append(bytes(donnees_ligne))

    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "wb") as fichier:
        fichier.write(b"\x89PNG\r\n\x1a\n")
        fichier.write(chunk(b"IHDR", struct.pack(">IIBBBBB", largeur, hauteur, 8, 2, 0, 0, 0)))
        fichier.write(chunk(b"IDAT", zlib.compress(b"".join(lignes), level=9)))
        fichier.write(chunk(b"IEND", b""))


def image_transition(output_dir):
    avant = grille_depuis_cellules(7, 7, [(2, 3), (3, 3), (4, 3)])
    apres = generation_suivante(avant)
    couleurs = {}
    for i in range(7):
        for j in range(7):
            couleurs[(i, j)] = couleur_transition(avant[i][j], apres[i][j])

    image = creer_image(980, 350, BLANC)
    remplir_rectangle(image, 0, 0, 980, 350, FOND)
    dessiner_texte(image, "REGLES EN UNE GENERATION", 40, 24, TEXTE, 3)
    dessiner_texte(image, "N", 126, 70, TEXTE_DISCRET, 2)
    dessiner_texte(image, "N+1/2", 450, 70, TEXTE_DISCRET, 2)
    dessiner_texte(image, "N+1", 784, 70, TEXTE_DISCRET, 2)
    dessiner_grille(image, avant, 40, 100, 28)
    dessiner_fleche(image, 270, 140, 340, 140, TEXTE)
    dessiner_grille(image, avant, 370, 100, 28, couleurs=couleurs)
    dessiner_fleche(image, 600, 140, 670, 140, TEXTE)
    dessiner_grille(image, apres, 700, 100, 28)
    ajouter_legende_couleurs(image, 285, 302, [(MEURT, "MEURT"), (NAIT, "NAIT"), (SURVIT, "SURVIT")])
    ecrire_png(os.path.join(output_dir, "gol_transition_blinker.png"), image)


def image_candidats(output_dir):
    cible = grille_depuis_cellules(9, 9, [(4, 3), (4, 4), (4, 5)])
    candidat_a = grille_depuis_cellules(9, 9, [(3, 4), (4, 4), (5, 4)])
    candidat_b = grille_depuis_cellules(9, 9, [(3, 3), (4, 4), (4, 5), (5, 4)])
    candidat_c = grille_depuis_cellules(9, 9, [(2, 3), (3, 4), (4, 5), (5, 6)])
    image = creer_image(980, 360, BLANC)
    remplir_rectangle(image, 0, 0, 980, 360, FOND)
    dessiner_texte(image, "UNE POPULATION = PLUSIEURS HYPOTHESES", 35, 22, TEXTE, 3)
    labels = ["CIBLE", "GRAINE", "CANDIDAT", "BRUIT"]
    for index, grille in enumerate([cible, candidat_a, candidat_b, candidat_c]):
        x = 35 + index * 235
        remplir_rectangle(image, x - 12, 74, x + 210, 315, BLANC)
        dessiner_rectangle_contour(image, x - 12, 74, x + 210, 315, GRILLE, 2)
        dessiner_texte(image, labels[index], x + 45, 92, TEXTE_DISCRET, 2)
        dessiner_grille(image, grille, x + 12, 125, 19)
    ecrire_png(os.path.join(output_dir, "population_candidates.png"), image)


def image_parents_enfant(output_dir):
    parent_a = grille_depuis_cellules(8, 8, [(2, 2), (2, 3), (3, 3), (5, 5)])
    parent_b = grille_depuis_cellules(8, 8, [(2, 3), (3, 2), (3, 3), (4, 3)])
    enfant = grille_depuis_cellules(8, 8, [(2, 2), (2, 3), (3, 3), (4, 3)])
    couleurs_a = {(i, j): PARENT_A for i in range(8) for j in range(8) if parent_a[i][j]}
    couleurs_b = {(i, j): PARENT_B for i in range(8) for j in range(8) if parent_b[i][j]}
    couleurs_e = {(i, j): ENFANT for i in range(8) for j in range(8) if enfant[i][j]}
    image = creer_image(980, 340, BLANC)
    remplir_rectangle(image, 0, 0, 980, 340, FOND)
    dessiner_texte(image, "CROISEMENT UNIFORME", 40, 22, TEXTE, 3)
    dessiner_texte(image, "PARENT A", 82, 74, PARENT_A, 2)
    dessiner_texte(image, "PARENT B", 405, 74, PARENT_B, 2)
    dessiner_texte(image, "ENFANT", 755, 74, ENFANT, 2)
    dessiner_grille(image, parent_a, 45, 105, 24, couleurs=couleurs_a)
    dessiner_plus(image, 315, 200, TEXTE)
    dessiner_grille(image, parent_b, 370, 105, 24, couleurs=couleurs_b)
    dessiner_egal(image, 645, 200, TEXTE)
    dessiner_grille(image, enfant, 700, 105, 24, couleurs=couleurs_e)
    ecrire_png(os.path.join(output_dir, "parents_child.png"), image)


def image_mutation(output_dir):
    avant = grille_depuis_cellules(8, 8, [(2, 3), (3, 3), (4, 3), (5, 4)])
    apres = grille_depuis_cellules(8, 8, [(1, 2), (2, 3), (2, 5), (3, 4), (4, 2), (4, 3), (5, 5), (6, 4)])
    cellules_modifiees = [(1, 2), (2, 5), (3, 3), (3, 4), (4, 2), (5, 4), (5, 5), (6, 4)]
    couleurs = {
        cellule: (MUTATION if apres[cellule[0]][cellule[1]] else MEURT)
        for cellule in cellules_modifiees
    }
    image = creer_image(760, 340, BLANC)
    remplir_rectangle(image, 0, 0, 760, 340, FOND)
    dessiner_texte(image, "MUTATION = EXPLORER", 40, 22, TEXTE, 3)
    dessiner_texte(image, "AVANT", 116, 74, TEXTE_DISCRET, 2)
    dessiner_texte(image, "APRES", 520, 74, TEXTE_DISCRET, 2)
    dessiner_grille(image, avant, 55, 105, 24)
    dessiner_fleche(image, 300, 200, 420, 200, TEXTE)
    dessiner_grille(image, apres, 465, 105, 24, couleurs=couleurs)
    ajouter_legende_couleurs(image, 210, 292, [(MUTATION, "AJOUT"), (MEURT, "RETRAIT")])
    ecrire_png(os.path.join(output_dir, "mutation.png"), image)


def image_erreur(output_dir):
    cible = grille_depuis_cellules(8, 8, [(3, 2), (3, 3), (3, 4), (3, 5)])
    resultat = grille_depuis_cellules(8, 8, [(3, 2), (3, 3), (4, 4), (5, 6)])
    couleurs = {}
    for i in range(8):
        for j in range(8):
            if resultat[i][j] == 1 and cible[i][j] == 1:
                couleurs[(i, j)] = SURVIT
            elif resultat[i][j] == 1 and cible[i][j] == 0:
                couleurs[(i, j)] = MEURT
            elif resultat[i][j] == 0 and cible[i][j] == 1:
                couleurs[(i, j)] = NAIT
    image = creer_image(760, 350, BLANC)
    remplir_rectangle(image, 0, 0, 760, 350, FOND)
    dessiner_texte(image, "SCORE = COMPARER AU RESULTAT VOULU", 35, 22, TEXTE, 3)
    dessiner_texte(image, "CIBLE", 116, 82, CIBLE, 2)
    dessiner_texte(image, "RESULTAT", 492, 82, TEXTE_DISCRET, 2)
    dessiner_grille(image, cible, 55, 112, 24, couleurs={(i, j): CIBLE for i in range(8) for j in range(8) if cible[i][j]})
    dessiner_fleche(image, 300, 207, 420, 207, TEXTE)
    dessiner_grille(image, resultat, 465, 112, 24, couleurs=couleurs)
    ajouter_legende_couleurs(image, 155, 302, [(SURVIT, "OK"), (MEURT, "TROP"), (NAIT, "MANQUE")])
    ecrire_png(os.path.join(output_dir, "error_score.png"), image)


def image_cycle_genetique(output_dir):
    image = creer_image(980, 340, BLANC)
    remplir_rectangle(image, 0, 0, 980, 340, FOND)
    dessiner_texte(image, "BOUCLE GENETIQUE", 40, 22, TEXTE, 3)
    etapes = [
        ("EVALUER", PARENT_A),
        ("ELITES", SURVIT),
        ("CROISER", ENFANT),
        ("MUTER", MUTATION),
    ]
    positions = [(55, 118), (285, 118), (515, 118), (745, 118)]
    for index, ((label, couleur), (x, y)) in enumerate(zip(etapes, positions)):
        remplir_rectangle(image, x, y, x + 160, y + 92, BLANC)
        dessiner_rectangle_contour(image, x, y, x + 160, y + 92, couleur, 5)
        dessiner_texte(image, label, x + 30, y + 36, couleur, 2)
        if index < len(positions) - 1:
            dessiner_fleche(image, x + 172, y + 46, positions[index + 1][0] - 14, y + 46, TEXTE)
    dessiner_fleche(image, 820, 245, 130, 245, TEXTE_DISCRET)
    dessiner_texte(image, "NOUVELLE GENERATION", 360, 270, TEXTE_DISCRET, 2)
    ecrire_png(os.path.join(output_dir, "genetic_cycle.png"), image)


def generer_tous_les_visuels(output_dir=ASSET_DIR):
    os.makedirs(output_dir, exist_ok=True)
    image_transition(output_dir)
    image_candidats(output_dir)
    image_parents_enfant(output_dir)
    image_mutation(output_dir)
    image_erreur(output_dir)
    image_cycle_genetique(output_dir)


def parse_args():
    parser = argparse.ArgumentParser(description="Génère les PNG pédagogiques du projet.")
    parser.add_argument("--output-dir", default=ASSET_DIR, help="dossier de sortie des PNG")
    return parser.parse_args()


def main():
    args = parse_args()
    generer_tous_les_visuels(args.output_dir)
    print("Visuels générés dans", args.output_dir)


if __name__ == "__main__":
    main()
