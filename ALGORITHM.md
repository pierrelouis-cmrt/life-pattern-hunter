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
- des versions bruitees de la cible ;
- des candidats aléatoires guidés par la distance à la cible ;
- plusieurs densites de depart.

Cette diversite est importante : certains motifs viennent d'une grille tres sparse, d'autres d'une grille plus dense.

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
7. Injecter quelques nouveaux candidats aléatoires.
8. Remplir le reste par sélection, croisement et mutation.
9. Supprimer les doublons.
10. Produire un instantané pour l'interface.

## Selection, croisement, mutation

La sélection utilise un tournoi : on tire quelques candidats au hasard, puis on garde le meilleur comme parent.

Le croisement est uniforme : pour chaque cellule de la zone de recherche, l'enfant prend soit la valeur du parent A, soit celle du parent B.

La mutation est guidée :

- pres de la cible, elle est un peu plus forte ;
- loin de la cible, elle est un peu plus faible.

Si le solveur stagne, le taux de mutation et le taux d'injection aléatoire augmentent. Cela force la recherche à explorer de nouvelles pistes.

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

On note :

- `N` : nombre de cellules, ici `576` ;
- `A` : nombre de cellules dans la zone active de recherche ;
- `X` : nombre de générations du jeu de la vie à simuler ;
- `P` : taille de population ;
- `L` : essais d'amelioration locale ;
- `G` : nombre maximal de générations génétiques ;
- `C` : taille maximale du cache.

Une simulation coute :

```text
O(X * N)
```

Une génération génétique évalue environ `P + L` candidats :

```text
O((P + L) * X * N)
```

Sur toute la recherche :

```text
O(G * (P + L) * X * N)
```

La memoire utilisee est approximativement :

```text
O(P * N + C * N + X * N)
```

Elle stocke la population, le cache et l'historique d'évolution affiché par l'interface.

## Référence de comparaison aléatoire

`random-bruteforce.py` sert de comparaison. Il réutilise les règles de `life_rules.py`, mais n'utilise pas l'algorithme génétique.

Il repete :

1. tirer des candidats au hasard ;
2. les simuler pendant `X` générations ;
3. calculer l'erreur ;
4. garder le meilleur résultat.

Il n'y a ni sélection, ni croisement, ni mutation guidée, ni apprentissage entre générations.
