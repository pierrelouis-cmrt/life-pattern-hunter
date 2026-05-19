# Complexité de l'algorithme

## Notations

| Symbole | Sens |
| --- | --- |
| `N` | nombre total de cellules dans une grille |
| `P` | taille de la population |
| `E` | nombre d'élites conservées |
| `A` | nombre de nouveaux individus aléatoires ajoutés par génération |
| `X` | nombre de passages du Jeu de la vie simulés par candidat |
| `G` | nombre maximal de générations de recherche |
| `Z` | nombre de cellules dans la zone active autour de la cible |

Dans l'application, la grille fait `24 * 24`, donc `N = 576`.

La zone active est incluse dans la grille, donc :

```text
Z <= N
```

Et les élites sont une partie de la population :

```text
E <= P
```

## Initialisation

Avant de lancer la recherche, le code calcule la zone active autour de la cible.
Pour cela, il parcourt la grille et repère les cellules vivantes.

```text
zone active = O(N)
```

Ensuite, il crée la population de départ. Chaque candidat est une grille
complète, même si seules les cellules de la zone active sont tirées au hasard.

Créer une grille complète coûte `O(N)`. Parcourir la zone active coûte `O(Z)`.
Comme `Z <= N`, on peut écrire :

```text
un candidat aléatoire = O(N + Z) = O(N)
population initiale = O(P * N)
```

L'initialisation complète coûte donc :

```text
O(N + P * N)
```

Ce coût est payé une seule fois. Dans le coût total, il est généralement dominé
par les générations de recherche, qui se répètent jusqu'à `G` fois.

## Simulation du Jeu de la vie

Un passage du Jeu de la vie parcourt toutes les cellules. Pour chaque cellule,
on regarde au plus huit voisines. Huit est une constante, donc elle ne change
pas l'ordre de grandeur.

```text
un passage = O(N)
```

Simuler un candidat pendant `X` passages coûte :

```text
simulation = O(X * N)
```

Le code copie aussi la grille de départ avant de simuler. Cette copie coûte
`O(N)`, donc le coût exact de la partie simulation est :

```text
O(N + X * N)
```

Comme `X >= 1` dans l'interface, `X * N` absorbe le `N` seul :

```text
O(N + X * N) = O(X * N)
```

## Évaluation d'un candidat

Pour évaluer un candidat, le code fait quatre choses :

1. simuler le candidat pendant `X` passages : `O(X * N)` ;
2. calculer l'erreur pondérée face à la cible : `O(N)` ;
3. calculer le pourcentage d'exactitude : `O(N)` ;
4. copier la grille du candidat pour garder une évaluation stable : `O(N)`.

On obtient donc :

```text
évaluation = O(X * N + N + N + N)
```

Les trois termes `O(N)` se regroupent :

```text
évaluation = O(X * N + N)
```

Puis, comme `X >= 1` :

```text
évaluation = O(X * N)
```

Ce n'est pas une approximation vague : le terme `X * N` contient déjà au moins
un parcours complet de la grille, donc les autres parcours en `N` ne changent
pas la complexité asymptotique.

## Évaluation de la population

La population contient `P` candidats. On évalue chaque candidat une fois.

```text
population évaluée = P * O(X * N)
```

Donc :

```text
évaluation de la population = O(P * X * N)
```

## Tri et élites

Après l'évaluation, les `P` candidats sont triés par score.

```text
tri = O(P log P)
```

Ensuite, les `E` meilleurs candidats sont marqués comme élites. Ce passage est
au plus linéaire dans la population :

```text
marquage des rangs et des élites = O(P)
```

Dans cette partie, `O(P)` est négligeable devant `O(P log P)` dès que la
population grandit :

```text
O(P log P + P) = O(P log P)
```

## Construction de la génération suivante

La génération suivante contient :

1. les `E` élites recopiées ;
2. `A` nouveaux candidats aléatoires ;
3. `P - E - A` enfants créés par croisement et mutation.

### Copie des élites

Chaque élite est une grille complète.

```text
copie des élites = O(E * N)
```

### Nouveaux candidats aléatoires

Un nouveau candidat aléatoire crée d'abord une grille complète, puis remplit
seulement la zone active.

```text
un candidat aléatoire = O(N + Z)
```

Comme `Z <= N` :

```text
un candidat aléatoire = O(N)
```

Pour `A` candidats :

```text
nouveaux candidats = O(A * N)
```

### Enfants par croisement et mutation

Un enfant est créé en deux étapes :

1. croisement : création d'une grille complète `O(N)`, puis mélange dans la zone active `O(Z)` ;
2. mutation : parcours de la zone active `O(Z)`.

Donc :

```text
un enfant = O(N + Z + Z)
```

Comme `Z <= N` :

```text
un enfant = O(N)
```

Il y a `P - E - A` enfants :

```text
enfants = O((P - E - A) * N)
```

### Construction complète

On additionne les trois parties :

```text
construction =
O(E * N + A * N + (P - E - A) * N)
```

Les termes `E`, `A` et `P - E - A` se recomposent exactement en `P` :

```text
E + A + (P - E - A) = P
```

Donc :

```text
construction = O(P * N)
```

La zone active aide surtout la recherche en limitant les cellules modifiées.
Mais dans ce code, elle ne transforme pas la construction en `O(P * Z)`,
parce que les grilles restent stockées et créées en taille complète.

## Une génération de recherche

Une génération de recherche fait :

1. évaluation de la population : `O(P * X * N)` ;
2. tri et élites : `O(P log P)` ;
3. construction de la génération suivante : `O(P * N)`.

Donc :

```text
une génération =
O(P * X * N + P log P + P * N)
```

On peut regrouper les deux termes qui parcourent les grilles :

```text
O(P * X * N + P * N) = O(P * N * (X + 1))
```

Comme `X >= 1`, le `+ 1` est absorbé par `X` :

```text
O(P * N * (X + 1)) = O(P * X * N)
```

Il reste donc :

```text
une génération = O(P * X * N + P log P)
```

En pratique, le terme principal est presque toujours `P * X * N`, car il
correspond aux simulations répétées du Jeu de la vie. Le tri peut compter si la
population devient très grande, mais il ne dépend ni de la taille de la grille
ni du nombre de passages simulés.

## Coût total

La recherche fait au maximum `G` générations.

En gardant tous les termes importants :

```text
coût total =
O(N + P * N + G * (P * X * N + P log P + P * N))
```

Les deux premiers termes viennent de l'initialisation. Comme ils ne sont pas
répétés `G` fois, ils sont généralement négligés quand on étudie la recherche
complète.

On retient donc :

```text
coût total =
O(G * (P * X * N + P log P + P * N))
```

Puis `P * N` est absorbé par `P * X * N` puisque `X >= 1` :

```text
coût total =
O(G * (P * X * N + P log P))
```

Si l'on veut la forme dominante la plus lisible, on garde le coût des
simulations :

```text
coût total dominant = O(G * P * X * N)
```

Cette dernière ligne est la formule à retenir pour expliquer le comportement de
l'application : plus on augmente la population, le nombre de passages, le nombre
de générations ou la taille de la grille, plus le temps augmente
proportionnellement.
