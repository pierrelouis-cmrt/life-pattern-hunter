# Algorithme de recherche inverse

Le mode **Résolution** cherche une grille initiale `G0` telle que :

```text
simuler(G0, X) ~= cible
```

`X` est le nombre de générations choisi dans l'interface. `~=` signifie "aussi proche que possible", car une cible peut avoir plusieurs ancêtres, aucun ancêtre, ou des ancêtres difficiles à trouver.

## Architecture du programme

Le projet est volontairement découpé pour que chaque fichier ait une responsabilité claire.

- `life_rules.py` : règles classiques du jeu de la vie. Ce fichier ne contient pas l'algorithme génétique.
- `reverse_search_algorithm.py` : recherche inverse par algorithme génétique. Ce fichier ne contient pas de Tkinter ni d'Eniseboard.
- `app_state.py` : état courant de l'application.
- `ui_app.py` : interface graphique, modes, boutons, barre de progression et fenêtre population.
- `reverse-search.py` : point d'entrée historique.

Cette séparation permet de tester l'algorithme sans ouvrir de fenêtre graphique.

## Règles normales du jeu de la vie

La fonction centrale est `generation_suivante`.

Pour chaque cellule :

- une cellule vivante survit avec 2 ou 3 voisines vivantes ;
- une cellule morte naît avec exactement 3 voisines vivantes ;
- dans tous les autres cas, la cellule devient ou reste morte.

La fonction `simuler(grille, X)` applique cette règle `X` fois. La fonction `historique_evolution` garde toutes les grilles intermédiaires pour l'affichage.

## Pourquoi le problème inverse est difficile

La grille fait `24 * 24 = 576` cellules. Chaque cellule peut être morte ou vivante. Tester toutes les grilles initiales possibles demanderait :

```text
2^576
```

possibilités. C'est inutilisable en pratique.

Le programme utilise donc une recherche approchée :

- il cherche seulement dans une zone autour de la cible ;
- il utilise une population de candidats ;
- il réutilise les meilleurs candidats pour créer les générations suivantes.

## État du solveur

`initialiser_solveur` construit un `SolverState`.

Cet état contient :

- la cible ;
- le nombre de générations ;
- la zone de recherche ;
- la carte de distance à la cible ;
- la population courante ;
- le cache d'évaluations ;
- la meilleure solution globale ;
- le dernier instantané pédagogique.

L'interface appelle ensuite `avancer_solveur_une_generation`. Cette fonction fait exactement une génération génétique, puis met à jour l'état.

## Zone de recherche

`calculer_zone_recherche` prend les cellules vivantes de la cible et construit un rectangle autour d'elles.

La marge dépend du nombre de générations :

```text
marge = max(MARGE_RECHERCHE, min(MAX_MARGE_RECHERCHE, générations + 2))
```

Intuition : si une cellule doit être vivante dans la cible finale, ses ancêtres probables sont souvent proches d'elle quelques générations plus tôt.

## Carte de distance

`construire_carte_distance_cible` calcule, pour chaque cellule, sa distance à la cellule cible vivante la plus proche.

Cette carte sert à deux choses :

- créer plus souvent des cellules vivantes près de la cible ;
- pénaliser davantage les cellules parasites loin du motif final.

La distance utilisée est la distance de Chebyshev :

```text
distance = max(abs(ligne - ligne_cible), abs(colonne - colonne_cible))
```

Elle est adaptée au jeu de la vie, car les voisins diagonaux comptent aussi.

## Population initiale

`creer_population_initiale` fabrique une population variée :

- la grille actuellement dessinée ;
- la cible elle-même comme point de départ simple ;
- des graines locales pour les cibles très clairsemées ;
- des versions bruitées de la cible ;
- des candidats aléatoires guidés par la distance à la cible ;
- plusieurs densités de départ.

Cette diversité est importante : certains motifs viennent d'une grille très sparse, d'autres d'une grille plus dense.

## Graines locales pour petites cibles

Les cibles très simples posent un piège à l'algorithme génétique : le bon ancêtre peut contenir seulement 3 ou 4 cellules, donc une population aléatoire produit souvent trop de parasites et la recherche stagne.

Pour corriger cela sans changer de famille d'algorithme, `creer_graines_locales_cible` ajoute une petite phase déterministe au lancement :

1. vérifier que la cible est clairsemée ;
2. construire une petite boîte autour de la cible ;
3. énumérer les combinaisons de 1 à 5 cellules vivantes dans cette boîte ;
4. simuler ces mini-candidats pendant `X` générations ;
5. garder seulement les meilleurs comme graines de départ.

Cette phase retrouve par exemple l'ancêtre perpendiculaire d'un blinker de 3 cellules. Elle est volontairement bornée : elle ne s'active que si la cible est petite, si la boîte locale reste petite et si le nombre de générations reste raisonnable.

Pour rester rapide, ces mini-candidats ne sont pas simulés comme des grilles complètes. Ils sont simulés comme des ensembles de cellules vivantes, ce qui rend leur coût proportionnel au nombre de cellules actives plutôt qu'aux `576` cases du plateau.

En cas de stagnation, les meilleures graines locales peuvent aussi être réinjectées dans la population avant les injections aléatoires classiques. Cela relance la recherche autour de structures plausibles au lieu d'ajouter seulement du bruit.

## Évaluation d'un individu

Un individu est une grille initiale candidate.

Pour l'évaluer :

1. On simule l'individu pendant `X` générations.
2. On compare le résultat à la cible.
3. On calcule une erreur.
4. On ajoute une très petite pénalité si la grille initiale est chargée.

Le score de tri vaut :

```text
score_tri = erreur_cible + cellules_initiales * PENALITE_CELLULE_INITIALE
```

La pénalité sur les cellules initiales est minuscule. Elle sert seulement à départager deux solutions presque équivalentes.

## Erreur par rapport à la cible

Le score distingue :

- faux négatif : la cible veut une cellule vivante, mais le résultat est mort ;
- faux positif : le résultat a une cellule vivante alors que la cible est morte.

Les faux négatifs coûtent plus cher :

```text
PENALITE_FAUX_NEGATIF = 4
PENALITE_FAUX_POSITIF = 1
```

Cela évite que l'algorithme préfère des grilles presque vides. Les cellules en trop loin de la cible reçoivent aussi une pénalité de distance.

## Cache

Une même grille peut réapparaître dans la population, par exemple parce qu'elle est élite ou parce qu'un croisement la reproduit.

`evaluer_individu` transforme la grille en clé immuable avec `cle_grille`. Si cette clé est déjà dans le cache, le solveur réutilise le résultat simulé et l'erreur.

Le cache améliore le temps réel, mais ne change pas le pire cas théorique.

## Une génération génétique

`avancer_solveur_une_generation` suit une séquence concrète :

1. Évaluer toute la population.
2. Trier les individus par score.
3. Tenter une petite amélioration locale du meilleur individu.
4. Mettre à jour le meilleur global.
5. Arrêter si une solution exacte est trouvée.
6. Garder les élites.
7. Si la recherche stagne, réinjecter quelques graines locales.
8. Injecter quelques nouveaux candidats aléatoires.
9. Remplir le reste par sélection, croisement et mutation.
10. Supprimer les doublons.
11. Produire un instantané pour l'interface.

## Sélection, croisement, mutation

La sélection utilise un tournoi : on tire quelques candidats au hasard, puis on garde le meilleur comme parent.

Le croisement est uniforme : pour chaque cellule de la zone de recherche, l'enfant prend soit la valeur du parent A, soit celle du parent B.

La mutation est guidée :

- près de la cible, elle est un peu plus forte ;
- loin de la cible, elle est un peu plus faible.

Si le solveur stagne, le taux de mutation et le taux d'injection aléatoire augmentent. Cela force la recherche à explorer de nouvelles pistes.

Pour les cibles clairsemées, les densités aléatoires sont aussi adaptées à la taille de la zone de recherche. Le solveur essaie davantage de candidats très peu chargés, ce qui évite que les petites cibles soient noyées sous des cellules parasites.

## Amélioration locale

Le meilleur candidat de la génération subit quelques tests simples :

1. choisir une cellule au hasard dans la zone de recherche ;
2. inverser cette cellule ;
3. évaluer le candidat modifié ;
4. garder la modification si elle améliore le score.

Cette partie agit comme une petite recherche locale greffée sur l'algorithme génétique.

## Instantanés pédagogiques

À chaque génération, le solveur produit un `GenerationSnapshot`.

Il contient :

- tous les individus évalués ;
- les meilleurs de la génération précédente ;
- le meilleur global ;
- le taux de mutation ;
- le taux d'injection ;
- la stagnation ;
- la taille du cache ;
- la zone de recherche.

La fenêtre `Voir population` utilise ces données pour afficher visuellement les élites, les injections, les enfants et leur évolution de `G0` à la génération cible.

## Barre de progression et recommandation

La barre de progression affiche :

```text
génération courante / générations maximales
```

Si la solution n'est pas exacte, l'interface regarde les cellules manquantes, les cellules en trop et la stagnation :

- beaucoup de cellules manquantes : essayer moins de générations ;
- résultat proche mais bruité : relancer avec le même nombre ou essayer une génération de plus ;
- forte stagnation : essayer moins de générations ou une cible plus compacte.

Cette recommandation n'est pas une preuve mathématique. C'est une aide de lecture pour guider les essais suivants.

## Complexité

### Notations utiles

On garde seulement les notations nécessaires :

- `N` : nombre total de cellules du plateau. Ici `N = 24 * 24 = 576` ;
- `X` : nombre de générations du jeu de la vie simulées pour tester un candidat ;
- `P` : taille de la population génétique ;
- `L` : nombre d'essais d'amélioration locale ;
- `G` : nombre maximal de générations génétiques ;
- `C` : taille maximale du cache ;
- `T` : nombre de cellules vivantes dans la cible ;
- `Q` : nombre de mini-graines testées au lancement.

Les valeurs principales du programme sont :

```text
N = 576
P = 120
L = 18
G = 420
C = 8000
```

### Évaluation d'un candidat

Un candidat est une grille initiale possible. Pour l'évaluer, le programme le simule pendant `X` générations, compare le résultat à la cible, calcule un score, puis garde les grilles utiles dans l'évaluation.

Une génération du jeu de la vie parcourt les `N` cellules. Pour chaque cellule, on regarde au plus 8 voisines. Le facteur 8 est constant, donc :

```text
coût d'une génération du jeu = O(N)
```

Simuler `X` générations coûte donc :

```text
O(X * N)
```

Les autres opérations de l'évaluation parcourent aussi la grille :

- `cle_grille` pour produire la clé du cache : `O(N)` ;
- `erreur_par_rapport_a_cible` : `O(N)` ;
- `score_exactitude` : `O(N)` ;
- `nombre_cellules_vivantes` : `O(N)` ;
- copies de grilles : `O(N)`.

Le coût complet d'une évaluation absente du cache est donc :

```text
O(X * N + N) = O((X + 1) * N)
```

Comme `X >= 1`, on retient :

```text
O(X * N)
```

Si le candidat est déjà dans le cache, la simulation est évitée. Il reste la clé et les copies :

```text
O(N)
```

Le cache accélère donc les cas réels, mais le pire cas reste `O(X * N)` par candidat, car tous les candidats peuvent être différents.

### Initialisation du solveur

`calculer_zone_recherche` parcourt la cible pour trouver les cellules vivantes :

```text
O(N)
```

`construire_carte_distance_cible` parcourt les `N` cellules du plateau et, pour chacune, cherche la plus proche des `T` cellules vivantes de la cible :

```text
O(N * T)
```

Comme `T <= N`, le pire cas théorique est :

```text
O(N^2)
```

En pratique, beaucoup de cibles ont peu de cellules vivantes, donc ce coût est souvent plus proche de `O(N * T)` avec `T` petit.

`creer_population_initiale` construit jusqu'à `P` grilles. Même quand un individu est généré seulement autour de la cible, il est stocké comme une grille complète de `N` cellules. Le coût total est donc borné par :

```text
O(P * N)
```

### Graines locales

Les graines locales sont une petite recherche déterministe ajoutée au début pour les cibles très simples. Le programme prend une petite boîte autour de la cible, puis teste les combinaisons de 1 à 5 cellules vivantes.

Avec les limites actuelles :

```text
boîte <= 18 cases
graine <= 5 cellules vivantes
Q <= C(18,1) + C(18,2) + C(18,3) + C(18,4) + C(18,5)
Q <= 12615
```

Ces graines ne sont pas simulées comme des grilles complètes. Elles sont simulées comme des ensembles de cellules vivantes. Si `K` est le nombre maximal de cellules actives pendant cette simulation, une graine coûte :

```text
O(X * K)
```

Après simulation, il faut aussi comparer la graine à la cible, ce qui coûte `O(T + K)`. Toutes les graines locales coûtent donc :

```text
O(Q * (X * K + T + K) + Q log Q)
```

Le `Q log Q` vient du tri des graines pour garder les meilleures. En pratique, cette phase reste bornée parce que `Q` est plafonné et qu'elle ne s'active que pour des petites cibles.

### Une génération génétique

Une génération de `avancer_solveur_une_generation` contient quatre coûts importants.

1. Évaluer la population :

```text
P évaluations * O(X * N) = O(P * X * N)
```

2. Trier la population par score :

Le code trie la population évaluée, puis peut retrier après l'amélioration locale. Deux tris restent dans le même ordre de grandeur :

```text
O(P log P)
```

3. Tester l'amélioration locale du meilleur candidat :

Le solveur essaie `L` petites mutations autour du meilleur individu. Dans le pire cas, chaque essai doit être simulé :

```text
O(L * X * N)
```

4. Construire la génération suivante :

Les élites sont copiées, l'instantané pédagogique est créé, les injections sont ajoutées, les enfants sont croisés puis mutés, et les doublons sont supprimés. Toutes ces opérations parcourent des grilles ou des zones de grille. Comme la zone de recherche ne peut pas dépasser le plateau, ce coût est borné par :

```text
O(P * N)
```

En additionnant :

```text
O(P * X * N + P log P + L * X * N + P * N)
```

On regroupe les évaluations de population et les essais locaux :

```text
O((P + L) * X * N + P log P + P * N)
```

Comme `X >= 1`, le terme `P * N` est inclus dans `P * X * N`. La complexité d'une génération génétique est donc :

```text
O((P + L) * X * N + P log P)
```

Dans ce programme, le terme dominant est presque toujours la simulation des candidats. On peut donc résumer le coût principal par :

```text
O((P + L) * X * N)
```

Cette simplification reste rigoureuse : le tri, les copies et le dédoublonnage ont été comptés avant d'être dominés.

### Recherche complète

Le solveur effectue au plus `G` générations génétiques. Le coût total hors initialisation est donc :

```text
O(G * ((P + L) * X * N + P log P))
```

En ajoutant l'initialisation et les graines locales :

```text
O(
  N * T
  + P * N
  + Q * (X * K + T + K)
  + Q log Q
  + G * ((P + L) * X * N + P log P)
)
```

Avec `T <= N`, la partie initialisation a pour pire cas `O(N^2)`. La formule de pire cas devient donc :

```text
O(
  N^2
  + P * N
  + Q * (X * K + N + K)
  + Q log Q
  + G * ((P + L) * X * N + P log P)
)
```

Dans la configuration réelle, `N`, `P`, `L`, `G` et `Q` sont plafonnés. Le temps d'exécution observé dépend donc surtout de :

- `X`, car chaque évaluation simule plus ou moins longtemps ;
- le nombre de générations génétiques réellement exécutées ;
- le nombre de répétitions dans la population, car le cache peut transformer une évaluation `O(X * N)` en `O(N)`.

### Mémoire

La mémoire vient principalement de quatre endroits :

- population courante : `O(P * N)` ;
- cache d'évaluations : `O(C * N)` ;
- instantané pédagogique de la population : `O(P * N)` ;
- historique d'évolution affiché par l'interface : `O(X * N)`.

La mémoire totale est donc :

```text
O(P * N + C * N + X * N)
```

Ce qui se simplifie en :

```text
O((P + C + X) * N)
```

Le terme dominant est généralement le cache, car `C = 8000` peut être beaucoup plus grand que `P = 120`.

## Référence de comparaison aléatoire

`random-bruteforce.py` sert de comparaison. Il réutilise les règles de `life_rules.py`, mais n'utilise pas l'algorithme génétique.

Il répète :

1. tirer des candidats au hasard ;
2. les simuler pendant `X` générations ;
3. calculer l'erreur ;
4. garder le meilleur résultat.

Il n'y a ni sélection, ni croisement, ni mutation guidée, ni apprentissage entre générations.
