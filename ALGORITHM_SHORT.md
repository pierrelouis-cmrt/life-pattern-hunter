# Fonctionnement concis de l'algorithme

Le mode **Résolution** cherche une grille initiale du jeu de la vie qui devient proche d'une cible après `X` générations.

## Separation du code

- `life_rules.py` applique uniquement les règles normales du jeu de la vie.
- `reverse_search_algorithm.py` contient uniquement le solveur génétique.
- `ui_app.py` affiche les grilles, la progression et la population.

Cette separation rend l'algorithme testable sans interface graphique.

## Famille d'algorithme

La recherche inverse est une métaheuristique évolutionnaire, plus précisément un algorithme génétique.

Chaque individu est une grille initiale possible. Pour l'évaluer, on ne remonte pas le temps : on le simule normalement pendant `X` générations, puis on compare le résultat à la cible.

## Boucle principale

1. Calculer une zone de recherche autour de la cible.
2. Créer une population variée de grilles candidates.
3. Simuler chaque candidat pendant `X` générations.
4. Calculer son erreur par rapport à la cible.
5. Garder les meilleurs candidats comme élites.
6. Ajouter quelques candidats aléatoires pour conserver de la diversité.
7. Produire des enfants par sélection, croisement et mutation.
8. Tester quelques petites modifications locales du meilleur candidat.
9. Recommencer jusqu'à solution exacte ou limite de générations.

## Score

Plus le score est bas, meilleure est la solution.

Le programme penalise :

- les cellules cible manquantes ;
- les cellules vivantes en trop ;
- les cellules en trop éloignées de la cible ;
- très légèrement les grilles initiales trop chargées.

Les cellules manquantes coûtent plus cher que les cellules en trop pour éviter que le solveur favorise des grilles presque vides.

## Complexite

Avec :

- `N` cellules ;
- `X` générations du jeu de la vie ;
- `P` individus ;
- `L` essais locaux ;
- `G` générations génétiques ;

une simulation coûte :

```text
O(X * N)
```

une génération génétique coûte environ :

```text
O((P + L) * X * N)
```

et la recherche complète coûte au pire :

```text
O(G * (P + L) * X * N)
```

La fenêtre `Voir population` n'ajoute pas de logique algorithmique : elle affiche les instantanés déjà produits par le solveur pour rendre la recherche compréhensible.
