# Complexite de la reverse search

Ce document resume le calcul de complexite de `reverse_search_algorithm.py`.

On utilise uniquement la notation grand O. Le calcul reste fait etape par etape : fonctions de base, evaluation d'un individu, population, generation genetique, puis recherche complete.

## 1. Notations

| Symbole | Sens |
| --- | --- |
| `H` | nombre de lignes |
| `W` | nombre de colonnes |
| `N` | nombre total de cellules, `N = H * W` |
| `Z` | nombre de cellules dans la zone de recherche |
| `T` | nombre de cellules vivantes dans la cible |
| `X` | nombre de generations du Jeu de la vie simulees, `steps` |
| `P` | taille de population |
| `E` | nombre d'elites |
| `G` | nombre maximal de generations genetiques |
| `L` | essais d'amelioration locale |
| `R` | essais de nettoyage |
| `M` | taille maximale du cache |
| `B` | cases candidates pour les graines locales |
| `A` | taille maximale d'une graine locale |
| `Q` | nombre de combinaisons de graines locales testees |
| `K` | cellules manipulees dans une simulation sparse |
| `S` | cellules vivantes dans un individu |

Valeurs par defaut principales :

```text
N = 24 * 24 = 576
P = 120
E = 14
G = 420
L = 18
R = 80
M = 8000
```

Toujours garder en tete :

```text
Z <= N
T <= N
S <= N
K <= N
```

La zone `Z` reduit certains parcours, mais beaucoup de fonctions copient, hashent ou simulent une grille complete. Ces operations coutent donc `O(N)`, pas `O(Z)`.

## 2. Fonctions de grille

Ces fonctions viennent surtout de `life_rules.py`.

| Fonction | Travail fait | Temps | Memoire |
| --- | --- | --- | --- |
| `nouvelle_grille` | cree une grille `H x W` | `O(N)` | `O(N)` |
| `copier_grille` | copie toutes les lignes | `O(N)` | `O(N)` |
| `nombre_cellules_vivantes` | parcourt toute la grille | `O(N)` | `O(1)` |
| `cle_grille` | transforme la grille en tuple | `O(N)` | `O(N)` |
| `compter_voisins` | regarde au plus 8 voisins | `O(1)` | `O(1)` |
| `generation_suivante` | calcule une generation du Jeu de la vie | `O(N)` | `O(N)` |
| `simuler` | copie puis applique `X` generations | `O(X * N)` | `O(N)` |

Le point important : une evaluation d'un candidat finit presque toujours par appeler `simuler`, donc par payer `O(X * N)`.

## 3. Outils internes de `reverse_search_algorithm.py`

| Fonction | Temps | Memoire | Remarque |
| --- | --- | --- | --- |
| `cellules_zone` | `O(Z)` | `O(Z)` | construit une liste de coordonnees |
| `cellules_vivantes` | `O(N)` | `O(S)` | scanne toute la grille |
| `grille_depuis_cellules` | `O(N)` | `O(N)` | cree une grille complete |
| `voisins_cellule` | `O(1)` | `O(1)` | au plus 8 voisins |
| `limiter_cache` | `O(d)` | `O(1)` | `d` suppressions, souvent 0 ou 1 |

`limiter_cache` ne domine pas le calcul : le cache est maintenu pres de `M`, donc on supprime generalement une seule entree apres une insertion.

## 4. Score et zone de recherche

### `construire_carte_distance_cible`

Etapes :

1. trouver les cellules vivantes de la cible : `O(N)` ;
2. si la cible est vide, remplir une carte : `O(N)` ;
3. sinon, pour chaque cellule du plateau, comparer aux `T` cellules cibles.

Complexite :

```text
O(N * T)
```

Pire cas :

```text
O(N^2)
```

### `erreur_par_rapport_a_cible`

Parcourt toutes les cellules et compare resultat/cible.

```text
O(N)
```

### `compter_differences`

Deux compteurs sur toute la grille.

```text
O(N)
```

### `score_exactitude`

Compte les cellules identiques sur toute la grille.

```text
O(N)
```

### `detecter_periode_simple`

Simule jusqu'a `U = max_periode` generations et compare les cles.

```text
O(U * N)
```

Avec `U = 8` par defaut :

```text
O(N)
```

### `calculer_zone_recherche`

Trouve les cellules vivantes, puis les bornes min/max.

```text
O(N)
```

## 5. Graines locales

Les graines locales ne sont utilisees que pour les petites cibles, mais leur calcul doit etre compte.

### `simuler_cellules_vivantes`

Simulation sparse : on manipule les cellules vivantes et leurs voisines, pas toute la grille dense.

```text
O(X * K)
```

Comme `K <= N`, le pire cas est :

```text
O(X * N)
```

### `erreur_cellules`

Differences d'ensembles entre resultat et cible.

```text
O(T + K)
```

### `creer_graines_locales_cible`

Etapes :

1. extraire les cellules cibles : `O(N)` ;
2. construire les `B` cases candidates ;
3. enumerer les combinaisons de tailles `1` a `A` ;
4. simuler et scorer chaque combinaison ;
5. trier les `Q` candidats ;
6. convertir les meilleures graines en grilles completes.

Nombre de combinaisons :

```text
Q = somme_{k=1..A} C(B, k)
```

Complexite :

```text
O(N + B + Q * (X * K + T + K) + Q log Q + Sg * N)
```

`Sg` est le nombre de graines gardees. Par defaut, `B`, `A` et `Sg` sont bornes par de petites constantes, donc cette partie reste controlee.

## 6. Population, selection, croisement, mutation

| Fonction | Temps | Pourquoi |
| --- | --- | --- |
| `densites_recherche` | `O(N + Z)` donc `O(N)` | compte les cellules vivantes et parfois la zone |
| `individu_aleatoire_guide` | `O(N + Z)` donc `O(N)` | cree une grille complete puis parcourt la zone |
| `muter_zone_guidee` | `O(Z)` | parcourt la zone |
| `croiser` | `O(N + Z)` donc `O(N)` | cree un enfant complet puis remplit la zone |
| `selection_tournoi` | `O(1)` | tournoi de taille 5 |

La creation d'un enfant coute donc :

```text
selection + croisement + mutation = O(N)
```

## 7. Evaluation d'un individu

Fonction centrale :

```python
evaluer_individu(...)
```

### Cas cache hit

Meme si l'individu est deja dans le cache :

1. fabriquer la cle : `O(N)` ;
2. copier l'individu et le resultat : `O(N)`.

Donc :

```text
O(N)
```

### Cas cache miss

Etapes :

1. fabriquer la cle : `O(N)` ;
2. simuler `X` generations : `O(X * N)` ;
3. calculer l'erreur : `O(N)` ;
4. compter les cellules initiales : `O(N)` ;
5. calculer l'exactitude : `O(N)` ;
6. copier pour le cache et l'evaluation : `O(N)`.

Donc :

```text
O(X * N)
```

C'est le cout dominant de toute la reverse search.

## 8. Evaluation d'une population

`evaluer_population` fait :

1. evaluer `P` individus ;
2. trier les evaluations ;
3. assigner les rangs.

Pire cas sans cache :

```text
O(P * X * N + P log P)
```

Si tout est deja en cache :

```text
O(P * N + P log P)
```

Pour une analyse de pire cas, on garde :

```text
O(P * X * N + P log P)
```

## 9. Population initiale

### `creer_population_initiale`

Elle cree :

1. la grille actuelle copiee ;
2. la cible naive copiee ;
3. les graines locales copiees ;
4. 8 cibles bruitees ;
5. des individus aleatoires jusqu'a atteindre `P`.

Chaque individu est une grille complete.

```text
O(P * N)
```

### `population_sans_doublons`

Elle :

1. fabrique une cle pour chaque individu : `O(P * N)` ;
2. regenere des individus si besoin : `O(Afill * N)`.

En temps attendu non pathologique :

```text
O(P * N)
```

Strictement, la boucle de remplacement depend de l'aleatoire : si le generateur retombait toujours sur des doublons, il n'y aurait pas de borne deterministe interessante. En pratique, l'espace des grilles est immense.

## 10. Amelioration locale et nettoyage

### `ameliorer_individu_local`

Etapes :

1. evaluer le meilleur courant ;
2. construire les cases de la zone ;
3. faire `L` essais :
   - copier la grille ;
   - inverser une cellule ;
   - evaluer le candidat.

Pire cas :

```text
O((L + 1) * X * N)
```

Dans le flux normal, le premier individu est souvent deja en cache, donc on retient surtout :

```text
O(L * X * N)
```

### `nettoyer_solution_initiale`

Etapes :

1. evaluer la solution ;
2. lister les cellules vivantes ;
3. trier ces cellules ;
4. tester jusqu'a `R` suppressions ;
5. chaque suppression reevalue un candidat.

Si `D = min(S, R)` :

```text
O((D + 1) * X * N + S log S)
```

Comme `D <= R` et `S <= N` :

```text
O((R + 1) * X * N + N log N)
```

Si la carte de distance doit etre reconstruite, ajouter :

```text
O(N * T)
```

Dans le solveur principal, elle est deja fournie.

## 11. Initialisation du solveur

`initialiser_solveur` fait :

1. `calculer_zone_recherche` : `O(N)` ;
2. `construire_carte_distance_cible` : `O(N * T)` ;
3. `creer_graines_locales_cible` ;
4. `creer_population_initiale` : `O(P * N)` ;
5. copier la cible : `O(N)`.

Donc :

```text
O(
  N * T
  + Q * (X * K + T + K)
  + Q log Q
  + P * N
  + Sg * N
  + B
)
```

Avec les bornes par defaut sur les graines locales, on lit surtout :

```text
O(N * T + P * N)
```

## 12. Snapshot et meilleur global

| Fonction | Temps | Remarque |
| --- | --- | --- |
| `copier_evaluation` | `O(N)` | copie individu + resultat |
| `evaluation_meilleur_global` | `O(N)` | si un meilleur existe |
| `taux_recherche` | `O(1)` | arithmetique |
| `relance_forte` | `O(1)` | comparaisons |
| `enregistrer_snapshot` | `O(P * N)` | copie jusqu'a `P` evaluations |
| `enregistrer_meilleur_global` | `O((R + 1) * X * N + N log N)` | domine par le nettoyage |

Le point a ne pas rater : `enregistrer_meilleur_global` appelle `nettoyer_solution_initiale`, donc il peut refaire jusqu'a `R` evaluations.

## 13. Population suivante

`construire_population_suivante` fait :

1. copier les `E` elites ;
2. eventuellement muter le meilleur global ;
3. eventuellement reinjecter des graines locales ;
4. injecter des individus aleatoires ;
5. produire des enfants par tournoi, croisement, mutation ;
6. supprimer les doublons.

Chaque grille creee ou copiee coute `O(N)`.

En temps attendu :

```text
O(P * N)
```

Memoire :

```text
O(P * N)
```

## 14. Une generation genetique

`avancer_solveur_une_generation` fait :

1. evaluer la population ;
2. ameliorer localement le meilleur ;
3. retrier ;
4. nettoyer/enregistrer le meilleur global ;
5. enregistrer le snapshot ;
6. construire la population suivante.

Couts :

```text
evaluer_population              O(P * X * N + P log P)
ameliorer_individu_local        O(L * X * N)
tri supplementaire              O(P log P)
enregistrer_meilleur_global     O(R * X * N + N log N)
enregistrer_snapshot            O(P * N)
construire_population_suivante  O(P * N)
```

Donc :

```text
O(
  (P + L + R) * X * N
  + P log P
  + N log N
  + P * N
)
```

Comme `X >= 1`, la lecture pratique est :

```text
O((P + L + R) * X * N + P log P + N log N)
```

Et le terme dominant est :

```text
O((P + L + R) * X * N)
```

Interpretation directe : une generation genetique simule environ `P + L + R` candidats pendant `X` generations du Jeu de la vie.

## 15. Recherche complete pour un `steps` fixe

La recherche complete contient :

1. l'initialisation ;
2. jusqu'a `G + 1` generations genetiques.

Le `+1` vient du code : le test `generation >= nb_generations_max` arrive apres l'evaluation de la generation courante. Asymptotiquement, `G + 1` reste `O(G)`, mais le detail est reel.

Formule complete :

```text
O(
  N * T
  + Q * (X * K + T + K)
  + Q log Q
  + P * N
  + Sg * N
  + B
  + (G + 1)
    * (
        (P + L + R) * X * N
        + P log P
        + N log N
        + P * N
      )
)
```

Forme pratique :

```text
O(G * (P + L + R) * X * N)
```

Forme ultra-resumee, moins precise mais utile a l'oral :

```text
O(G * P * X * N)
```

La forme rigoureuse garde `L` et `R`, parce que l'amelioration locale et le nettoyage appellent aussi `evaluer_individu`.

## 16. Memoire

Principaux postes :

| Element | Memoire |
| --- | --- |
| population | `O(P * N)` |
| carte de distance | `O(N)` |
| cible | `O(N)` |
| meilleur individu + meilleur resultat | `O(N)` |
| graines locales | `O(Sg * N)` |
| cache | `O(M * N)` |
| evaluations + snapshot | `O(P * N)` |

Memoire totale :

```text
O((M + P + Sg) * N)
```

Comme `Sg <= P` en pratique :

```text
O((M + P) * N)
```

Le cache est le plus gros poste potentiel : chaque entree stocke une cle de taille `N` et un resultat de taille `N`.

## 17. Comparaison avec la force brute

Une grille de `N` cellules binaires donne :

```text
2^N
```

grilles initiales possibles.

Tester tout l'espace couterait :

```text
O(2^N * X * N)
```

La reverse search genetique remplace ce cout exponentiel par un budget controle :

```text
O(G * (P + L + R) * X * N)
```

Ce n'est pas une garantie d'optimalite. C'est une heuristique bornee : on teste beaucoup moins que `2^N`, mais on choisit mieux quoi tester.

## 18. Recap final

Evaluation d'un candidat :

```text
O(X * N)
```

Evaluation d'une population :

```text
O(P * X * N + P log P)
```

Une generation genetique complete :

```text
O((P + L + R) * X * N + P log P + N log N)
```

Recherche complete :

```text
O(G * (P + L + R) * X * N)
```

Memoire :

```text
O((M + P) * N)
```

Le coeur du calcul est donc simple : l'algorithme coute cher parce qu'il simule beaucoup de candidats, pendant `X` generations du Jeu de la vie, et repete cela pendant `G` generations genetiques.
