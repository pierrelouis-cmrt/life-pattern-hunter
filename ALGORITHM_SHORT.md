# Fonctionnement concis de l'algorithme

Le mode **Resolution** cherche une grille initiale du jeu de la vie qui devient proche d'une cible apres `X` generations.

## Separation du code

- `life_rules.py` applique uniquement les regles normales du jeu de la vie.
- `reverse_search_algorithm.py` contient uniquement le solveur genetique.
- `ui_app.py` affiche les grilles, la progression et la population.

Cette separation rend l'algorithme testable sans interface graphique.

## Famille d'algorithme

La reverse search est une metaheuristique evolutionnaire, plus precisement un algorithme genetique.

Chaque individu est une grille initiale possible. Pour l'evaluer, on ne remonte pas le temps : on le simule normalement pendant `X` generations, puis on compare le resultat a la cible.

## Boucle principale

1. Calculer une zone de recherche autour de la cible.
2. Creer une population variee de grilles candidates.
3. Simuler chaque candidat pendant `X` generations.
4. Calculer son erreur par rapport a la cible.
5. Garder les meilleurs candidats comme elites.
6. Ajouter quelques candidats aleatoires pour conserver de la diversite.
7. Produire des enfants par selection, croisement et mutation.
8. Tester quelques petites modifications locales du meilleur candidat.
9. Recommencer jusqu'a solution exacte ou limite de generations.

## Score

Plus le score est bas, meilleure est la solution.

Le programme penalise :

- les cellules cible manquantes ;
- les cellules vivantes en trop ;
- les cellules en trop eloignees de la cible ;
- tres legerement les grilles initiales trop chargees.

Les cellules manquantes coutent plus cher que les cellules en trop pour eviter que le solveur favorise des grilles presque vides.

## Complexite

Avec :

- `N` cellules ;
- `X` generations du jeu de la vie ;
- `P` individus ;
- `L` essais locaux ;
- `G` generations genetiques ;

une simulation coute :

```text
O(X * N)
```

une generation genetique coute environ :

```text
O((P + L) * X * N)
```

et la recherche complete coute au pire :

```text
O(G * (P + L) * X * N)
```

La fenetre `Voir population` n'ajoute pas de logique algorithmique : elle affiche les snapshots deja produits par le solveur pour rendre la recherche comprehensible.
