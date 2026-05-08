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
2. Si la cible est tres petite, créer quelques graines locales en enumerant de mini-ancetres plausibles.
3. Créer une population variée de grilles candidates.
4. Simuler chaque candidat pendant `X` générations.
5. Calculer son erreur par rapport à la cible.
6. Garder les meilleurs candidats comme élites.
7. Ajouter quelques candidats aléatoires pour conserver de la diversité.
8. Réinjecter des graines locales quand la recherche stagne.
9. Produire des enfants par sélection, croisement et mutation.
10. Tester quelques petites modifications locales du meilleur candidat.
11. Recommencer jusqu'à solution exacte ou limite de générations.

## Score

Plus le score est bas, meilleure est la solution.

Le programme penalise :

- les cellules cible manquantes ;
- les cellules vivantes en trop ;
- les cellules en trop éloignées de la cible ;
- très légèrement les grilles initiales trop chargées.

Les cellules manquantes coûtent plus cher que les cellules en trop pour éviter que le solveur favorise des grilles presque vides.

## Anti-stagnation

Les cibles finales avec seulement quelques cellules sont difficiles pour un tirage aleatoire : une bonne solution peut etre tres precise, comme le blinker perpendiculaire qui produit une ligne de 3 cellules.

Le solveur ajoute donc des **graines locales**. Pour une cible clairsemee, il enumere de petites grilles autour de la cible, les simule sous forme d'ensemble de cellules vivantes, puis garde les meilleures dans la population initiale. Si la recherche stagne, ces graines peuvent etre reinjectees avant les injections aleatoires.

## Complexite

Avec :

- `N` cellules ;
- `X` générations du jeu de la vie ;
- `P` individus ;
- `L` essais locaux ;
- `G` générations génétiques ;
- `Q` graines locales bornees ;

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

La création des graines locales ajoute seulement :

```text
O(Q * X * K)
```

`K` est le nombre de cellules actives pendant la simulation d'une mini-graine. Comme `Q` et la taille initiale des graines sont plafonnes, cette aide reste legere.

La fenêtre `Voir population` n'ajoute pas de logique algorithmique : elle affiche les instantanés déjà produits par le solveur pour rendre la recherche compréhensible.
