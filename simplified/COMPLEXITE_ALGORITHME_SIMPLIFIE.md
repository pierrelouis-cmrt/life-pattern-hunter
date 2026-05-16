# Complexité de l'algorithme simplifié

## Notations

On utilise des notations volontairement intuitives :

| Symbole | Sens |
| --- | --- |
| `N` | nombre total de cellules dans une grille |
| `P` | taille de population |
| `E` | nombre d'élites |
| `X` | nombre de passages du Jeu de la vie simulés pour évaluer un individu |
| `G` | nombre maximal de générations génétiques |
| `Z` | nombre de cellules dans la zone active autour de la cible |

Dans l'application, `N = lignes * colonnes`. Par défaut, la grille fait
`24 * 24`, donc `N = 576`.

## Simulation du Jeu de la vie

Un passage du Jeu de la vie parcourt toutes les cellules. Pour chaque cellule,
on regarde au plus 8 voisines.

Le coût d'un passage est donc :

```text
O(N)
```

Simuler un individu pendant `X` passages coûte :

```text
O(X * N)
```

## Zone active

La zone active est calculée à partir des cellules vivantes de la cible. On
parcourt la grille pour trouver ces cellules :

```text
calcul de la zone = O(N)
```

Ce coût est payé une seule fois au lancement de la recherche.

La zone ne réduit pas le coût de simulation dans cette version, car la fonction
de Jeu de la vie simule encore toute la grille. Elle réduit surtout la taille de
l'espace de recherche.

## Évaluation d'un individu

Pour évaluer un individu, on fait deux choses :

1. simuler `X` passages : `O(X * N)` ;
2. comparer le résultat avec la cible avec le score pondéré : `O(N)`.

Donc :

```text
évaluer un individu = O(X * N + N)
```

Comme `X * N` domine dès que `X >= 1`, on retient :

```text
évaluer un individu = O(X * N)
```

## Évaluation de la population

Il y a `P` individus dans la population.

```text
évaluer toute la population = O(P * X * N)
```

## Tri et sélection des élites

Après l'évaluation, on trie les `P` individus selon leur erreur.

```text
tri = O(P log P)
```

Prendre les `E` premiers après le tri coûte au plus :

```text
sélection des élites = O(E)
```

Comme `E <= P`, cette partie ne domine pas le tri.

## Construction de la génération suivante

La génération suivante contient :

- `E` copies d'élites ;
- `P - E` enfants créés par croisement et mutation.

Copier les élites coûte `O(E * N)`, parce qu'une élite est une grille complète.
Créer un nouvel individu aléatoire coûte `O(Z)`. Croiser deux parents coûte
`O(Z)`, car on choisit une cellule parentale seulement dans la zone active.
Muter un enfant coûte aussi `O(Z)`.

Donc, pour remplir une population complète :

```text
construction = O(E * N + P * Z)
```

## Coût d'une génération génétique

Une génération génétique fait :

1. évaluation de la population : `O(P * X * N)` ;
2. tri : `O(P log P)` ;
3. construction de la population suivante : `O(E * N + P * Z)`.

Donc :

```text
une génération = O(P * X * N + P log P + E * N + P * Z)
```

Comme la simulation est le coût principal, on lit souvent :

```text
une génération ≈ O(P * X * N)
```

Cette simplification est raisonnable quand `X` est non nul et que les grilles ne
sont pas minuscules.

## Coût total

Au maximum, la recherche fait `G` générations génétiques.

```text
coût total = O(G * (P * X * N + P log P + E * N + P * Z))
```

Forme dominante :

```text
coût total ≈ O(G * P * X * N)
```

## Mémoire

La mémoire principale contient la population. Chaque individu est une grille de
`N` cellules et il y a `P` individus.

```text
population = O(P * N)
```

Pendant l'évaluation, on stocke aussi les résultats et quelques copies des
meilleurs individus. Cela reste proportionnel à la taille de la population :

```text
mémoire totale = O(P * N)
```

Il n'y a pas de cache. La mémoire ne dépend donc pas du nombre d'individus déjà
vus dans les générations précédentes.

La zone active ajoute seulement quelques nombres : ses bornes et sa taille. Cela
reste `O(1)`.
