# Algorithme de reverse search

Le mode **Resolution** cherche une grille initiale `G0` telle que :

```text
simuler(G0, X) ~= cible
```

`X` est le nombre de `Steps` choisi dans l'interface. `~=` signifie "aussi proche que possible", car une cible peut avoir plusieurs ancetres, aucun ancetre, ou des ancetres difficiles a trouver.

## Architecture du programme

Le projet est volontairement decoupe pour que chaque fichier ait une responsabilite claire.

- `life_rules.py` : regles classiques du jeu de la vie. Ce fichier ne contient pas l'algorithme genetique.
- `reverse_search_algorithm.py` : reverse search par algorithme genetique. Ce fichier ne contient pas de Tkinter ni d'Eniseboard.
- `app_state.py` : etat courant de l'application.
- `ui_app.py` : interface graphique, modes, boutons, barre de progression et fenetre population.
- `reverse-search.py` : point d'entree historique.

Cette separation permet de tester l'algorithme sans ouvrir de fenetre graphique.

## Regles normales du jeu de la vie

La fonction centrale est `generation_suivante`.

Pour chaque cellule :

- une cellule vivante survit avec 2 ou 3 voisines vivantes ;
- une cellule morte nait avec exactement 3 voisines vivantes ;
- dans tous les autres cas, la cellule devient ou reste morte.

La fonction `simuler(grille, X)` applique cette regle `X` fois. La fonction `historique_evolution` garde toutes les grilles intermediaires pour l'affichage.

## Pourquoi le probleme inverse est difficile

La grille fait `24 * 24 = 576` cellules. Chaque cellule peut etre morte ou vivante. Tester toutes les grilles initiales possibles demanderait :

```text
2^576
```

possibilites. C'est inutilisable en pratique.

Le programme utilise donc une recherche approchee :

- il cherche seulement dans une zone autour de la cible ;
- il utilise une population de candidats ;
- il reutilise les meilleurs candidats pour creer les generations suivantes.

## Etat du solveur

`initialiser_solveur` construit un `SolverState`.

Cet etat contient :

- la cible ;
- le nombre de steps ;
- la zone de recherche ;
- la carte de distance a la cible ;
- la population courante ;
- le cache d'evaluations ;
- la meilleure solution globale ;
- le dernier snapshot pedagogique.

L'interface appelle ensuite `avancer_solveur_une_generation`. Cette fonction fait exactement une generation genetique, puis met a jour l'etat.

## Zone de recherche

`calculer_zone_recherche` prend les cellules vivantes de la cible et construit un rectangle autour d'elles.

La marge depend du nombre de steps :

```text
marge = max(MARGE_RECHERCHE, min(MAX_MARGE_RECHERCHE, steps + 2))
```

Intuition : si une cellule doit etre vivante dans la cible finale, ses ancetres probables sont souvent proches d'elle quelques generations plus tot.

## Carte de distance

`construire_carte_distance_cible` calcule, pour chaque cellule, sa distance a la cellule cible vivante la plus proche.

Cette carte sert a deux choses :

- creer plus souvent des cellules vivantes pres de la cible ;
- penaliser davantage les cellules parasites loin du motif final.

La distance utilisee est la distance de Chebyshev :

```text
distance = max(abs(ligne - ligne_cible), abs(colonne - colonne_cible))
```

Elle est adaptee au jeu de la vie, car les voisins diagonaux comptent aussi.

## Population initiale

`creer_population_initiale` fabrique une population variee :

- la grille actuellement dessinee ;
- la cible elle-meme comme point de depart simple ;
- des versions bruitees de la cible ;
- des candidats aleatoires guides par la distance a la cible ;
- plusieurs densites de depart.

Cette diversite est importante : certains motifs viennent d'une grille tres sparse, d'autres d'une grille plus dense.

## Evaluation d'un individu

Un individu est une grille initiale candidate.

Pour l'evaluer :

1. On simule l'individu pendant `X` generations.
2. On compare le resultat a la cible.
3. On calcule une erreur.
4. On ajoute une tres petite penalite si la grille initiale est chargee.

Le score de tri vaut :

```text
score_tri = erreur_cible + cellules_initiales * PENALITE_CELLULE_INITIALE
```

La penalite sur les cellules initiales est minuscule. Elle sert seulement a departager deux solutions presque equivalentes.

## Erreur par rapport a la cible

Le score distingue :

- faux negatif : la cible veut une cellule vivante, mais le resultat est mort ;
- faux positif : le resultat a une cellule vivante alors que la cible est morte.

Les faux negatifs coutent plus cher :

```text
PENALITE_FAUX_NEGATIF = 4
PENALITE_FAUX_POSITIF = 1
```

Cela evite que l'algorithme prefere des grilles presque vides. Les cellules en trop loin de la cible recoivent aussi une penalite de distance.

## Cache

Une meme grille peut reapparaitre dans la population, par exemple parce qu'elle est elite ou parce qu'un croisement la reproduit.

`evaluer_individu` transforme la grille en cle immuable avec `cle_grille`. Si cette cle est deja dans le cache, le solveur reutilise le resultat simule et l'erreur.

Le cache ameliore le temps reel, mais ne change pas le pire cas theorique.

## Une generation genetique

`avancer_solveur_une_generation` suit une sequence concrete :

1. Evaluer toute la population.
2. Trier les individus par score.
3. Tenter une petite amelioration locale du meilleur individu.
4. Mettre a jour le meilleur global.
5. Arreter si une solution exacte est trouvee.
6. Garder les elites.
7. Injecter quelques nouveaux candidats aleatoires.
8. Remplir le reste par selection, croisement et mutation.
9. Supprimer les doublons.
10. Produire un snapshot pour l'interface.

## Selection, croisement, mutation

La selection utilise un tournoi : on tire quelques candidats au hasard, puis on garde le meilleur comme parent.

Le croisement est uniforme : pour chaque cellule de la zone de recherche, l'enfant prend soit la valeur du parent A, soit celle du parent B.

La mutation est guidee :

- pres de la cible, elle est un peu plus forte ;
- loin de la cible, elle est un peu plus faible.

Si le solveur stagne, le taux de mutation et le taux d'injection aleatoire augmentent. Cela force la recherche a explorer de nouvelles pistes.

## Amelioration locale

Le meilleur candidat de la generation subit quelques tests simples :

1. choisir une cellule au hasard dans la zone de recherche ;
2. inverser cette cellule ;
3. evaluer le candidat modifie ;
4. garder la modification si elle ameliore le score.

Cette partie agit comme une petite recherche locale greffee sur l'algorithme genetique.

## Snapshots pedagogiques

A chaque generation, le solveur produit un `GenerationSnapshot`.

Il contient :

- tous les individus evalues ;
- les meilleurs de la generation precedente ;
- le meilleur global ;
- le taux de mutation ;
- le taux d'injection ;
- la stagnation ;
- la taille du cache ;
- la zone de recherche.

La fenetre `Voir population` utilise ces donnees pour afficher visuellement les elites, les injections, les enfants et leur evolution de `G0` a `Gsteps`.

## Barre de progression et recommendation

La barre de progression affiche :

```text
generation courante / generations maximales
```

Si la solution n'est pas exacte, l'interface regarde les cellules manquantes, les cellules en trop et la stagnation :

- beaucoup de cellules manquantes : essayer moins de steps ;
- resultat proche mais bruite : relancer avec le meme nombre ou essayer `steps + 1` ;
- forte stagnation : essayer moins de steps ou une cible plus compacte.

Cette recommendation n'est pas une preuve mathematique. C'est une aide de lecture pour guider les essais suivants.

## Complexite

On note :

- `N` : nombre de cellules, ici `576` ;
- `A` : nombre de cellules dans la zone active de recherche ;
- `X` : nombre de generations du jeu de la vie a simuler ;
- `P` : taille de population ;
- `L` : essais d'amelioration locale ;
- `G` : nombre maximal de generations genetiques ;
- `C` : taille maximale du cache.

Une simulation coute :

```text
O(X * N)
```

Une generation genetique evalue environ `P + L` candidats :

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

Elle stocke la population, le cache et l'historique d'evolution affiche par l'interface.

## Baseline aleatoire

`random-bruteforce.py` sert de comparaison. Il reutilise les regles de `life_rules.py`, mais n'utilise pas l'algorithme genetique.

Il repete :

1. tirer des candidats au hasard ;
2. les simuler pendant `X` generations ;
3. calculer l'erreur ;
4. garder le meilleur resultat.

Il n'y a ni selection, ni croisement, ni mutation guidee, ni apprentissage entre generations.
