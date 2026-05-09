#!/usr/bin/env python3
"""Nettoie une grille initiale candidate sans dégrader sa cible finale."""

import argparse

from life_rules import nombre_cellules_vivantes
from reverse_search_algorithm import (
    SearchConfig,
    construire_carte_distance_cible,
    evaluer_individu,
    nettoyer_solution_initiale,
)


def lire_grille_ascii(chemin):
    lignes = []
    with open(chemin, "r", encoding="utf-8") as fichier:
        for ligne in fichier:
            ligne = ligne.strip()
            if not ligne:
                continue
            lignes.append([1 if caractere == "#" else 0 for caractere in ligne])

    if not lignes:
        raise ValueError(f"{chemin} ne contient aucune ligne de grille")

    largeur = len(lignes[0])
    if any(len(ligne) != largeur for ligne in lignes):
        raise ValueError(f"{chemin} contient des lignes de longueurs différentes")

    return lignes


def grille_vers_ascii(grille):
    return "\n".join("".join("#" if cellule else "." for cellule in ligne) for ligne in grille)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Retire les cellules inutiles d'une grille initiale Game of Life sans augmenter l'erreur finale."
    )
    parser.add_argument("--initial", required=True, help="fichier ASCII de la grille initiale candidate")
    parser.add_argument("--target", "--cible", required=True, help="fichier ASCII de la cible finale")
    parser.add_argument("--steps", "--generations", type=int, required=True, help="nombre de générations à simuler")
    parser.add_argument("--output", "--sortie", help="fichier où écrire la grille nettoyée")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.steps < 1:
        raise SystemExit("--steps doit être supérieur ou égal à 1")

    initiale = lire_grille_ascii(args.initial)
    cible = lire_grille_ascii(args.target)
    if len(initiale) != len(cible) or len(initiale[0]) != len(cible[0]):
        raise SystemExit("--initial et --target doivent avoir les mêmes dimensions")

    config = SearchConfig(rows=len(cible), cols=len(cible[0]))
    carte_distance = construire_carte_distance_cible(cible, config)
    cache = {}
    avant = evaluer_individu(initiale, "avant nettoyage", cible, args.steps, cache, carte_distance, config)
    apres = nettoyer_solution_initiale(initiale, cible, args.steps, config, carte_distance, cache)
    cellules_retirees = nombre_cellules_vivantes(avant.individu) - nombre_cellules_vivantes(apres.individu)
    texte_grille = grille_vers_ascii(apres.individu)

    print("Nettoyage conservateur")
    print("Steps:", args.steps)
    print("Cellules retirées:", cellules_retirees)
    print("Erreur avant:", "{:.3f}".format(avant.erreur))
    print("Erreur après:", "{:.3f}".format(apres.erreur))
    print("Exactitude avant:", "{:.2f} %".format(avant.exactitude))
    print("Exactitude après:", "{:.2f} %".format(apres.exactitude))
    print()
    print(texte_grille)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fichier:
            fichier.write(texte_grille + "\n")


if __name__ == "__main__":
    main()
