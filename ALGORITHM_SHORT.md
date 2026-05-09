# Fonctionnement concis de l'algorithme

Le mode **Résolution** cherche une grille initiale du jeu de la vie qui devient proche d'une cible après `X` générations.

## Séparation du code

- `life_rules.py` applique uniquement les règles normales du jeu de la vie.
- `reverse_search_algorithm.py` contient uniquement le solveur génétique.
- `ui_app.py` affiche les grilles, la progression et la population.
- `clean-solution.py` nettoie une solution depuis deux fichiers texte.

Cette séparation rend l'algorithme testable sans interface graphique.

## Famille d'algorithme

La recherche inverse est une métaheuristique évolutionnaire, plus précisément un algorithme génétique.

Chaque individu est une grille initiale possible. Pour l'évaluer, on ne remonte pas le temps : on le simule normalement pendant `X` générations, puis on compare le résultat à la cible.

## Boucle principale

1. Calculer une zone de recherche autour de la cible.
2. Si la cible est très petite, créer quelques graines locales en énumérant de mini-ancêtres plausibles.
3. Créer une population variée de grilles candidates.
4. Simuler chaque candidat pendant `X` générations.
5. Calculer son erreur par rapport à la cible.
6. Garder les meilleurs candidats comme élites.
7. Ajouter quelques candidats aléatoires pour conserver de la diversité.
8. Réinjecter des graines locales quand la recherche stagne.
9. Lancer une relance forte si la stagnation devient longue.
10. Si la stagnation semble devoir durer jusqu'à la limite, essayer automatiquement un autre nombre de générations.
11. Produire des enfants par sélection, croisement et mutation.
12. Tester quelques petites modifications locales du meilleur candidat.
13. Nettoyer conservativement le meilleur global.
14. Recommencer jusqu'à solution exacte ou limite de générations.

## Score

Plus le score est bas, meilleure est la solution.

Le programme pénalise :

- les cellules cible manquantes ;
- les cellules vivantes en trop ;
- les cellules en trop éloignées de la cible ;
- très légèrement les grilles initiales trop chargées.

Les cellules manquantes coûtent plus cher que les cellules en trop pour éviter que le solveur favorise des grilles presque vides.

## Anti-stagnation

Les cibles finales avec seulement quelques cellules sont difficiles pour un tirage aléatoire : une bonne solution peut être très précise, comme le blinker perpendiculaire qui produit une ligne de 3 cellules.

Le solveur ajoute donc des **graines locales**. Pour une cible clairsemée, il énumère de petites grilles autour de la cible, les simule sous forme d'ensemble de cellules vivantes, puis garde les meilleures dans la population initiale. Si le nombre de générations demandé est grand, les mini-graines sont aussi testées sur de courts horizons `1..8`, ce qui aide les motifs périodiques simples.

Si la stagnation devient longue, le solveur conserve les élites mais remplace une partie de la population par des candidats très clairsemés, des graines locales et des mutations plus fortes du meilleur global.

Si cette stagnation continue assez longtemps, l'interface garde le meilleur essai courant et relance automatiquement le solveur depuis le minimum automatique saisi, puis `minimum + 1`, puis `minimum + 2`. Elle teste au maximum 8 valeurs au total, essai initial inclus. Le statut final résume les stats des meilleurs essais.

## Nettoyage

Avant d'enregistrer une nouvelle meilleure solution, le solveur essaie de retirer des cellules de la grille initiale. Une suppression est gardée seulement si le résultat final garde la même erreur ou l'améliore. Une solution exacte reste donc exacte.

Le script `clean-solution.py` permet de faire le même nettoyage à part avec des fichiers ASCII (`#` vivant, `.` mort).

## Complexité

Avec :

- `N` cellules ;
- `X` générations du jeu de la vie ;
- `P` individus ;
- `L` essais locaux ;
- `G` générations génétiques ;
- `Q` graines locales bornées ;
- `R` essais de nettoyage bornés ;

une simulation coûte :

```text
O(X * N)
```

une génération génétique coûte environ :

```text
O((P + L + R) * X * N)
```

et la recherche complète coûte au pire :

```text
O(G * (P + L + R) * X * N)
```

La création des graines locales ajoute seulement :

```text
O(Q * X * K)
```

`K` est le nombre de cellules actives pendant la simulation d'une mini-graine. Comme `Q` et la taille initiale des graines sont plafonnés, cette aide reste légère.

La fenêtre `Voir population` n'ajoute pas de logique algorithmique : elle affiche les instantanés déjà produits par le solveur pour rendre la recherche compréhensible.
