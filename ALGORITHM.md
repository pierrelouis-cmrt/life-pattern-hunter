# Algorithme de recherche inverse

Le mode **Résolution** cherche une grille initiale `G0` telle que :

```text
simuler(G0, X) ~= cible
```

`X` est le nombre de générations choisi dans l'interface. `~=` signifie "aussi proche que possible", car une cible peut avoir plusieurs ancêtres, aucun ancêtre, ou des ancêtres difficiles à trouver.

## Architecture du programme

Le projet est volontairement decoupe pour que chaque fichier ait une responsabilite claire.

- `life_rules.py` : règles classiques du jeu de la vie. Ce fichier ne contient pas l'algorithme génétique.
- `reverse_search_algorithm.py` : recherche inverse par algorithme génétique. Ce fichier ne contient pas de Tkinter ni d'Eniseboard.
- `app_state.py` : etat courant de l'application.
- `ui_app.py` : interface graphique, modes, boutons, barre de progression et fenêtre population.
- `reverse-search.py` : point d'entree historique.

Cette séparation permet de tester l'algorithme sans ouvrir de fenêtre graphique.

## Regles normales du jeu de la vie

La fonction centrale est `generation_suivante`.

Pour chaque cellule :

- une cellule vivante survit avec 2 ou 3 voisines vivantes ;
- une cellule morte nait avec exactement 3 voisines vivantes ;
- dans tous les autres cas, la cellule devient ou reste morte.

La fonction `simuler(grille, X)` applique cette règle `X` fois. La fonction `historique_evolution` garde toutes les grilles intermédiaires pour l'affichage.

## Pourquoi le probleme inverse est difficile

La grille fait `24 * 24 = 576` cellules. Chaque cellule peut être morte ou vivante. Tester toutes les grilles initiales possibles demanderait :

```text
2^576
```

possibilites. C'est inutilisable en pratique.

Le programme utilise donc une recherche approchee :

- il cherche seulement dans une zone autour de la cible ;
- il utilise une population de candidats ;
- il réutilise les meilleurs candidats pour créer les générations suivantes.

## Etat du solveur

`initialiser_solveur` construit un `SolverState`.

Cet etat contient :

- la cible ;
- le nombre de générations ;
- la zone de recherche ;
- la carte de distance a la cible ;
- la population courante ;
- le cache d'evaluations ;
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

`construire_carte_distance_cible` calcule, pour chaque cellule, sa distance a la cellule cible vivante la plus proche.

Cette carte sert a deux choses :

- créer plus souvent des cellules vivantes près de la cible ;
- penaliser davantage les cellules parasites loin du motif final.

La distance utilisee est la distance de Chebyshev :

```text
distance = max(abs(ligne - ligne_cible), abs(colonne - colonne_cible))
```

Elle est adaptee au jeu de la vie, car les voisins diagonaux comptent aussi.

## Population initiale

`creer_population_initiale` fabrique une population variée :

- la grille actuellement dessinee ;
- la cible elle-meme comme point de depart simple ;
- des graines locales pour les cibles tres clairsemees ;
- des versions bruitees de la cible ;
- des candidats aléatoires guidés par la distance à la cible ;
- plusieurs densites de depart.

Cette diversite est importante : certains motifs viennent d'une grille tres sparse, d'autres d'une grille plus dense.

## Graines locales pour petites cibles

Les cibles tres simples posent un piege a l'algorithme genetique : le bon ancetre peut contenir seulement 3 ou 4 cellules, donc une population aleatoire produit souvent trop de parasites et la recherche stagne.

Pour corriger cela sans changer de famille d'algorithme, `creer_graines_locales_cible` ajoute une petite phase deterministe au lancement :

1. verifier que la cible est clairsemee ;
2. construire une petite boite autour de la cible ;
3. enumerer les combinaisons de 1 a 5 cellules vivantes dans cette boite ;
4. simuler ces mini-candidats pendant `X` generations ;
5. garder seulement les meilleurs comme graines de depart.

Cette phase retrouve par exemple l'ancetre perpendiculaire d'un blinker de 3 cellules. Elle est volontairement bornee : elle ne s'active que si la cible est petite, si la boite locale reste petite et si le nombre de generations reste raisonnable.

Pour rester rapide, ces mini-candidats ne sont pas simules comme des grilles completes. Ils sont simules comme des ensembles de cellules vivantes, ce qui rend leur cout proportionnel au nombre de cellules actives plutot qu'aux `576` cases du plateau.

En cas de stagnation, les meilleures graines locales peuvent aussi etre reinjectees dans la population avant les injections aleatoires classiques. Cela relance la recherche autour de structures plausibles au lieu d'ajouter seulement du bruit.

## Evaluation d'un individu

Un individu est une grille initiale candidate.

Pour l'evaluer :

1. On simule l'individu pendant `X` générations.
2. On compare le résultat à la cible.
3. On calcule une erreur.
4. On ajoute une tres petite penalite si la grille initiale est chargee.

Le score de tri vaut :

```text
score_tri = erreur_cible + cellules_initiales * PENALITE_CELLULE_INITIALE
```

La penalite sur les cellules initiales est minuscule. Elle sert seulement a departager deux solutions presque equivalentes.

## Erreur par rapport a la cible

Le score distingue :

- faux négatif : la cible veut une cellule vivante, mais le résultat est mort ;
- faux positif : le résultat a une cellule vivante alors que la cible est morte.

Les faux négatifs coûtent plus cher :

```text
PENALITE_FAUX_NEGATIF = 4
PENALITE_FAUX_POSITIF = 1
```

Cela evite que l'algorithme prefere des grilles presque vides. Les cellules en trop loin de la cible recoivent aussi une penalite de distance.

## Cache

Une meme grille peut reapparaitre dans la population, par exemple parce qu'elle est elite ou parce qu'un croisement la reproduit.

`evaluer_individu` transforme la grille en clé immuable avec `cle_grille`. Si cette clé est déjà dans le cache, le solveur réutilise le résultat simulé et l'erreur.

Le cache ameliore le temps reel, mais ne change pas le pire cas theorique.

## Une génération génétique

`avancer_solveur_une_generation` suit une sequence concrete :

1. Evaluer toute la population.
2. Trier les individus par score.
3. Tenter une petite amelioration locale du meilleur individu.
4. Mettre a jour le meilleur global.
5. Arrêter si une solution exacte est trouvée.
6. Garder les elites.
7. Si la recherche stagne, reinjecter quelques graines locales.
8. Injecter quelques nouveaux candidats aléatoires.
9. Remplir le reste par sélection, croisement et mutation.
10. Supprimer les doublons.
11. Produire un instantané pour l'interface.

## Selection, croisement, mutation

La sélection utilise un tournoi : on tire quelques candidats au hasard, puis on garde le meilleur comme parent.

Le croisement est uniforme : pour chaque cellule de la zone de recherche, l'enfant prend soit la valeur du parent A, soit celle du parent B.

La mutation est guidée :

- pres de la cible, elle est un peu plus forte ;
- loin de la cible, elle est un peu plus faible.

Si le solveur stagne, le taux de mutation et le taux d'injection aléatoire augmentent. Cela force la recherche à explorer de nouvelles pistes.

Pour les cibles clairsemees, les densites aleatoires sont aussi adaptees a la taille de la zone de recherche. Le solveur essaie davantage de candidats tres peu charges, ce qui evite que les petites cibles soient noyees sous des cellules parasites.

## Amelioration locale

Le meilleur candidat de la generation subit quelques tests simples :

1. choisir une cellule au hasard dans la zone de recherche ;
2. inverser cette cellule ;
3. evaluer le candidat modifie ;
4. garder la modification si elle ameliore le score.

Cette partie agit comme une petite recherche locale greffée sur l'algorithme génétique.

## Instantanés pédagogiques

À chaque génération, le solveur produit un `GenerationSnapshot`.

Il contient :

- tous les individus evalues ;
- les meilleurs de la generation precedente ;
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

## Complexite

### Notations

On separe les constantes du programme et les paramètres qui peuvent varier :

- `R` : nombre de lignes du plateau ;
- `S` : nombre de colonnes du plateau ;
- `N = R * S` : nombre total de cellules. Dans l'application, `N = 24 * 24 = 576` ;
- `T` : nombre de cellules vivantes dans la cible ;
- `A` : nombre de cellules dans la zone de recherche. On a toujours `A <= N` ;
- `X` : nombre de generations du jeu de la vie simulees pour evaluer un candidat ;
- `P` : taille de la population genetique ;
- `E` : nombre d'elites conservees ;
- `L` : nombre d'essais d'amelioration locale ;
- `G` : nombre maximal de generations genetiques ;
- `C` : taille maximale du cache d'evaluations ;
- `B` : nombre de cases dans la petite boite des graines locales ;
- `M` : nombre maximal de cellules vivantes dans une graine locale ;
- `Q` : nombre de combinaisons de graines locales testees.

Dans la configuration actuelle :

```text
P = 120
E = 14
L = 18
G = 420
C = 8000
B <= 18
M <= 5
X <= 8 pour activer les graines locales
```

Le solveur travaille donc sur un plateau fixe dans l'interface, mais l'analyse ci-dessous garde `N`, `P`, `G` et `X` variables pour montrer le comportement general de l'algorithme.

### Cout des briques de base

Une generation du jeu de la vie parcourt les `N` cellules. Pour chaque cellule, `compter_voisins` teste au plus 8 voisines, donc un nombre constant d'operations. Le cout d'une generation est donc :

```text
O(8 * N) = O(N)
```

Simuler un candidat pendant `X` generations coute :

```text
O(X * N)
```

L'evaluation complete d'un individu ne contient pas seulement cette simulation. Elle fait aussi :

- `cle_grille` pour produire la cle du cache : `O(N)` ;
- `simuler` si l'individu n'est pas deja dans le cache : `O(X * N)` ;
- `erreur_par_rapport_a_cible` : `O(N)` ;
- `score_exactitude` : `O(N)` ;
- `nombre_cellules_vivantes` : `O(N)` ;
- des copies de grilles pour stocker l'evaluation : `O(N)`.

Le cout d'une evaluation non trouvee dans le cache est donc :

```text
O(N + X * N + N + N + N + N) = O((X + 1) * N)
```

Comme `X >= 1` dans les usages normaux du solveur, on peut simplifier en :

```text
O(X * N)
```

Une evaluation trouvee dans le cache evite la simulation et le recalcul de l'erreur, mais elle doit quand meme construire la cle et copier les grilles retournees. Son cout est donc :

```text
O(N)
```

Le cache ameliore donc le temps reel quand beaucoup d'individus reapparaissent, mais il ne change pas le pire cas : dans le pire cas, chaque candidat est nouveau et doit etre simule.

### Initialisation du solveur

`calculer_zone_recherche` parcourt la cible pour trouver les cellules vivantes :

```text
O(N)
```

`construire_carte_distance_cible` parcourt les `N` cellules du plateau et, pour chacune, cherche la plus proche des `T` cellules vivantes de la cible :

```text
O(N * T)
```

Comme `T <= N`, le pire cas theorique est :

```text
O(N^2)
```

En pratique, beaucoup de cibles ont peu de cellules vivantes, donc ce cout est souvent plus proche de `O(N * T)` avec `T` petit.

`creer_population_initiale` construit jusqu'a `P` grilles. Certaines operations copient une grille complete (`O(N)`), d'autres generent seulement la zone active (`O(A)`), mais chaque individu est stocke comme une grille de taille `N`. Le cout total est donc borne par :

```text
O(P * N)
```

### Graines locales

Les graines locales ne sont creees que si la cible est clairsemee et si `X` reste petit. La petite boite contient `B` cases, et le programme teste toutes les combinaisons de taille `1` a `M`. Le nombre de graines candidates testees est :

```text
Q = somme_{k=1..M} C(B, k)
```

Avec les bornes du programme :

```text
B <= 18
M <= 5
Q <= C(18,1) + C(18,2) + C(18,3) + C(18,4) + C(18,5)
Q <= 18 + 153 + 816 + 3060 + 8568
Q <= 12615
```

Chaque graine est simulee avec `simuler_cellules_vivantes`, qui ne parcourt pas tout le plateau. Elle parcourt les cellules vivantes et leurs voisines. Si `K_t` est le nombre de cellules vivantes a l'etape `t`, une simulation coute :

```text
O(somme_{t=0..X-1} K_t)
```

car chaque cellule vivante produit au plus 8 voisins a compter. Si on note `K = max(K_t)` pendant cette simulation, on obtient la borne simple :

```text
O(X * K)
```

La comparaison sparse avec la cible coute `O(T + K)`. Le cout total des graines locales est donc :

```text
O(Q * (X * K + T + K) + Q log Q)
```

Le terme `Q log Q` vient du tri des graines candidates avant de garder les meilleures. Comme `B`, `M`, `Q` et `X` sont strictement plafonnes par la configuration pour cette phase, ce cout est borne en pratique. Il reste neanmoins important de l'ecrire : les graines locales sont une enumeration combinatoire controlee, pas une operation constante en theorie si on retirait ces plafonds.

### Une generation genetique

Une generation de `avancer_solveur_une_generation` contient plusieurs etapes.

1. Evaluation de la population :

```text
P evaluations * O(X * N) = O(P * X * N)
```

2. Tri de la population evaluee :

```text
O(P log P)
```

3. Amelioration locale du meilleur individu :

Le meilleur candidat est evalue, puis `L` voisins obtenus par inversion d'une cellule sont testes. Dans le pire cas, aucun n'est dans le cache :

```text
O((L + 1) * X * N)
```

4. Nouveau tri apres l'amelioration locale :

Le code insere le candidat local puis retrie si necessaire une liste de taille environ `P + 1` :

```text
O(P log P)
```

5. Creation des instantanes pedagogiques :

Le snapshot copie jusqu'a `P` evaluations, et chaque evaluation contient une grille initiale et une grille resultat. Le cout est donc :

```text
O(P * N)
```

6. Conservation des elites :

Copier `E` grilles coute :

```text
O(E * N)
```

Comme `E <= P`, cette etape est incluse dans `O(P * N)`.

7. Injections aleatoires et relances locales :

Chaque nouvel individu aleatoire parcourt la zone active `A`, puis stocke une grille de taille `N`. Les relances locales copient des grilles completes et peuvent muter `A` cases. Pour au plus `P` individus :

```text
O(P * (N + A))
```

Comme `A <= N`, cela devient :

```text
O(P * N)
```

8. Selection, croisement et mutation des enfants :

La selection par tournoi tire au plus 5 candidats, donc elle coute `O(1)` par parent. Le croisement cree une grille puis remplit la zone active, et la mutation parcourt aussi la zone active :

```text
O(N + A) par enfant
```

Pour au plus `P` enfants :

```text
O(P * (N + A)) = O(P * N)
```

9. Suppression des doublons :

Pour chaque individu, `cle_grille` parcourt `N` cellules. Si des remplacements aleatoires sont necessaires, ils sont aussi bornes par la taille de population. Le cout est donc :

```text
O(P * N)
```

En additionnant les etapes d'une generation genetique :

```text
O(P * X * N)
+ O(P log P)
+ O((L + 1) * X * N)
+ O(P log P)
+ O(P * N)
+ O(P * N)
+ O(P * N)
+ O(P * N)
```

Ce qui donne :

```text
O((P + L) * X * N + P log P + P * N)
```

Comme `X >= 1`, le terme `P * N` est absorbe par `P * X * N`, donc la borne usuelle devient :

```text
O((P + L) * X * N + P log P)
```

Si `P log P` est negligeable devant les simulations, ce qui est le cas avec un plateau de 576 cellules et des simulations sur plusieurs generations, on peut retenir le terme dominant :

```text
O((P + L) * X * N)
```

Cette simplification est correcte seulement apres avoir verifie les autres couts : elle n'ignore pas le tri, les copies et le dedoublonnage, elle constate simplement qu'ils sont domines par les simulations dans le regime normal du programme.

### Recherche complete

La recherche effectue au plus `G` generations genetiques. Le cout total hors initialisation est donc :

```text
O(G * ((P + L) * X * N + P log P))
```

En ajoutant l'initialisation et les graines locales :

```text
O(
  N
  + N * T
  + P * N
  + Q * (X * K + T + K)
  + Q log Q
  + G * ((P + L) * X * N + P log P)
)
```

La borne de pire cas en fonction de `N`, en utilisant `T <= N` et `A <= N`, est :

```text
O(
  N^2
  + P * N
  + Q * (X * K + N + K)
  + Q log Q
  + G * ((P + L) * X * N + P log P)
)
```

Dans la configuration reelle, `Q` est plafonne, `P`, `L`, `G` et `C` sont fixes par `SearchConfig`, et `N = 576`. Le temps d'execution observe depend donc surtout de :

- `X`, car chaque evaluation simule plus ou moins longtemps ;
- `G`, car il fixe le nombre maximal de generations genetiques ;
- le nombre de repetitions dans la population, car le cache peut transformer une evaluation `O(X * N)` en `O(N)`.

### Memoire

La population courante stocke `P` grilles de `N` cellules :

```text
O(P * N)
```

Le cache stocke jusqu'a `C` entrees. Chaque entree contient une cle de `N` cellules et une grille resultat de `N` cellules, plus quelques scores scalaires. Le cout est donc :

```text
O(C * N)
```

Les instantanes pedagogiques stockent jusqu'a `P` evaluations, chacune avec un individu et son resultat :

```text
O(P * N)
```

L'historique d'evolution affiche par l'interface contient `X + 1` grilles :

```text
O((X + 1) * N) = O(X * N)
```

La carte de distance et la cible occupent chacune une grille :

```text
O(N)
```

La memoire totale est donc :

```text
O(P * N + C * N + X * N + N)
```

Ce qui se simplifie en :

```text
O((P + C + X) * N)
```

Le terme dominant est generalement le cache, car `C = 8000` peut etre beaucoup plus grand que `P = 120`.

## Référence de comparaison aléatoire

`random-bruteforce.py` sert de comparaison. Il réutilise les règles de `life_rules.py`, mais n'utilise pas l'algorithme génétique.

Il repete :

1. tirer des candidats au hasard ;
2. les simuler pendant `X` générations ;
3. calculer l'erreur ;
4. garder le meilleur résultat.

Il n'y a ni sélection, ni croisement, ni mutation guidée, ni apprentissage entre générations.
