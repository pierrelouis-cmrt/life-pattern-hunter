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
- quelques nouveaux individus aléatoires ;
- le reste en enfants créés par croisement et mutation.

Copier les élites coûte `O(E * N)`, parce qu'une élite est une grille complète.

Pour le reste, on travaille seulement dans la zone active :

- créer un nouvel individu aléatoire coûte `O(Z)` ;
- croiser deux parents coûte `O(Z)` ;
- muter un enfant coûte `O(Z)`.

Pour rendre le calcul explicite, appelons `A` le nombre de nouveaux individus
aléatoires ajoutés à chaque génération. Après les élites, il reste `P - E`
places à remplir :

- les `A` nouveaux individus coûtent `O(A * Z)` ;
- les `P - E - A` enfants coûtent `O((P - E - A) * Z)`.

La partie active coûte donc :

```text
O(A * Z + (P - E - A) * Z)
```

Les deux termes utilisent la même zone active. On peut les regrouper :

```text
O((P - E) * Z)
```

En ajoutant la copie des élites :

```text
construction = O(E * N + (P - E) * Z)
```

Et comme `P - E <= P`, on peut écrire la forme plus simple :

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
