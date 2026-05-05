# Fonctionnement concis de l'algorithme

`reverse-search.py` cherche une grille initiale du jeu de la vie de Conway qui devient proche d'une cible apres `X` generations.

## Famille

L'algorithme est une metaheuristique evolutionnaire, plus precisement un algorithme genetique applique a un probleme inverse d'automate cellulaire.

Il ne garantit pas de trouver la solution optimale. Il cherche une bonne solution dans un espace trop grand pour etre teste exhaustivement.

## Idee generale

Tester toutes les grilles initiales possibles serait impossible :

```text
2^576 possibilites pour une grille 24 * 24
```

Le programme utilise donc une population de grilles candidates. Chaque candidate est simulee vers le futur, comparee a la cible, puis les meilleures servent a produire la generation suivante.

## Etapes principales

1. L'utilisateur dessine la grille finale souhaitee.
2. Il choisit `X`, le nombre de generations a remonter indirectement.
3. Le programme calcule une zone de recherche autour de la cible.
4. Il cree une population initiale de grilles possibles.
5. Chaque grille est simulee pendant `X` generations.
6. Le resultat obtenu est compare a la cible avec un score d'erreur.
7. Les meilleurs candidats sont conserves.
8. De nouveaux candidats sont produits par croisement et mutation.
9. Des candidats aleatoires sont reinjectes pour eviter la stagnation.
10. Le processus recommence jusqu'a trouver une solution exacte ou atteindre la limite de generations.

## Score

Le score mesure l'ecart entre le resultat simule et la cible. Plus il est bas, meilleure est la solution.

Le programme penalise :

- les cellules vivantes manquantes dans la cible ;
- les cellules vivantes en trop ;
- les cellules en trop eloignees de la cible ;
- tres legerement les grilles initiales trop chargees.

Les cellules cible manquantes coutent plus cher que les cellules en trop, afin d'eviter que l'algorithme favorise des grilles presque vides.

## Optimisations simples

Le solveur ajoute plusieurs ameliorations pratiques :

- zone de recherche limitee autour de la cible ;
- population initiale avec plusieurs densites ;
- candidats aleatoires guides par la distance a la cible ;
- cache pour ne pas recalculer deux fois la meme grille ;
- suppression des doublons ;
- mutation adaptee en cas de stagnation ;
- petite amelioration locale du meilleur candidat.

## Complexite

Avec :

- `N` cellules dans la grille ;
- `X` generations a simuler ;
- `P` candidats dans la population ;
- `L` essais d'amelioration locale ;
- `G` generations genetiques ;

une simulation coute :

```text
O(X * N)
```

une generation genetique coute environ :

```text
O((P + L) * X * N)
```

et toute la recherche coute au pire :

```text
O(G * (P + L) * X * N)
```

Le script `random-bruteforce.py` utilise volontairement le meme ordre de complexite par iteration, mais sans selection, croisement, mutation ni apprentissage. Il sert donc de comparaison avec une strategie purement aleatoire.
