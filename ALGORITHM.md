# Algorithme de reverse search

`reverse-search.py` cherche une grille initiale du jeu de la vie de Conway qui, apres `X` generations, ressemble le plus possible a une grille finale dessinee par l'utilisateur.

Le probleme est un probleme inverse : les regles du jeu de la vie sont faciles a appliquer vers le futur, mais il n'existe pas de methode simple pour revenir exactement en arriere. Une meme grille finale peut avoir beaucoup de parents possibles, aucun parent, ou des parents tres differents. Le programme utilise donc une recherche approchee.

## Grande famille d'algorithmes

L'algorithme appartient a la famille des metaheuristiques evolutionnaires, plus precisement des algorithmes genetiques.

Il manipule une population de solutions candidates. Chaque candidat est une grille initiale possible. A chaque generation genetique, les candidats sont evalues, les meilleurs sont conserves, puis de nouveaux candidats sont fabriques par selection, croisement, mutation et injection aleatoire.

Ce n'est pas un algorithme exact. Il ne garantit pas de trouver la meilleure grille initiale possible. Son but est de trouver rapidement une bonne solution dans un espace de recherche beaucoup trop grand pour etre parcouru entierement.

## Pourquoi ne pas tout tester ?

La grille contient `24 * 24 = 576` cellules. Chaque cellule peut etre morte ou vivante. Tester toutes les grilles initiales possibles demanderait donc d'examiner :

```text
2^576
```

possibilites. Ce nombre est astronomique. Meme si une simulation etait tres rapide, une recherche exhaustive complete serait inutilisable.

Le solveur reduit donc le probleme de deux facons :

- il limite la recherche a une zone autour de la cible ;
- il utilise une recherche genetique pour privilegier les candidats prometteurs.

## Deroulement detaille

### 1. L'utilisateur definit la cible finale

Dans l'interface, l'utilisateur dessine la grille qu'il veut obtenir a la fin. Cette grille est stockee dans `etat["cible"]`.

Le solveur ne cherche pas a modifier cette cible. Il cherche une grille initiale `G0` telle que :

```text
simuler(G0, X) ~= cible
```

`~=` signifie "aussi proche que possible", car une solution exacte n'existe pas toujours ou peut etre difficile a trouver.

### 2. L'utilisateur choisit le nombre d'etapes inverses

La valeur `X`, appelee `Steps` dans l'interface, indique combien de generations du jeu de la vie seront appliquees au candidat initial.

Par exemple, si `X = 5`, le programme cherche une grille initiale qui donne la cible apres 5 generations :

```text
G0 -> G1 -> G2 -> G3 -> G4 -> G5
                         G5 doit ressembler a la cible
```

Plus `X` est grand, plus le probleme devient difficile, car une petite difference dans la grille initiale peut produire une evolution tres differente.

### 3. Le solveur calcule une zone de recherche

La fonction `calculer_zone_recherche` regarde ou se trouvent les cellules vivantes de la cible. Elle construit ensuite un rectangle autour de cette cible, avec une marge.

La marge vaut au minimum `MARGE_RECHERCHE`, et augmente un peu quand `X` augmente :

```text
marge = max(MARGE_RECHERCHE, min(MAX_MARGE_RECHERCHE, X + 2))
```

L'idee est simple : si une cellule doit etre vivante dans la cible finale, ses ancetres probables sont souvent proches d'elle quelques generations plus tot. Le solveur evite donc de chercher inutilement dans toute la grille.

Si la cible est vide, la zone devient toute la grille, mais l'interface empeche normalement de lancer le solveur sur une cible vide.

### 4. Le solveur construit une carte de distance a la cible

La fonction `construire_carte_distance_cible` calcule, pour chaque cellule de la grille, sa distance a la cellule vivante la plus proche dans la cible.

Cette carte sert a deux endroits :

- generer des candidats un peu plus denses pres de la cible ;
- penaliser davantage les cellules vivantes en trop qui apparaissent loin de la cible.

La distance utilise la distance de Chebyshev :

```text
distance = max(abs(ligne - ligne_cible), abs(colonne - colonne_cible))
```

Cette distance est adaptee a une grille ou les voisins diagonaux comptent aussi.

### 5. La population initiale est creee

La fonction `creer_population_initiale` fabrique `TAILLE_POPULATION` candidats. Par defaut, cela fait `120` grilles initiales possibles.

La population melange plusieurs sources :

- la grille courante dessinee par l'utilisateur ;
- la cible elle-meme comme point de depart naif ;
- des versions bruitees de la cible ;
- des grilles aleatoires de plusieurs densites ;
- des grilles aleatoires guidees par la carte de distance.

Utiliser plusieurs densites est important. Certains motifs ont besoin d'une origine tres sparse, d'autres d'une soupe plus dense.

### 6. Chaque candidat est simule vers l'avant

Pour evaluer un candidat, le programme n'essaie pas de remonter les regles du jeu de la vie. Il applique simplement les regles normales vers le futur.

La fonction `simuler` applique `generation_suivante` exactement `X` fois :

```text
resultat = simuler(candidat, X)
```

La regle utilisee est celle du jeu de la vie classique :

- une cellule vivante survit avec 2 ou 3 voisines vivantes ;
- une cellule morte nait avec exactement 3 voisines vivantes ;
- les autres cellules deviennent ou restent mortes.

### 7. Le resultat est compare a la cible

La fonction `erreur_par_rapport_a_cible` calcule une erreur. Plus l'erreur est petite, meilleur est le candidat.

Le score distingue deux types de fautes :

- faux negatif : la cible veut une cellule vivante, mais le resultat est mort ;
- faux positif : le resultat a une cellule vivante alors que la cible est morte.

Les faux negatifs coutent plus cher :

```text
PENALITE_FAUX_NEGATIF = 4
PENALITE_FAUX_POSITIF = 1
```

Cela evite que l'algorithme prefere trop facilement des grilles presque vides. Une cellule cible manquante est plus grave qu'une cellule en trop.

Les cellules vivantes en trop sont aussi penalisees selon leur distance a la cible :

```text
erreur += distance * PENALITE_DISTANCE_EXTRA
```

Ainsi, un parasite loin du motif final coute plus cher qu'une cellule supplementaire collee a la forme recherchee.

### 8. Un petit tie-breaker favorise les grilles simples

Deux candidats peuvent produire le meme niveau d'erreur finale. Dans ce cas, le programme prefere legerement celui qui contient moins de cellules vivantes au depart.

Le score de tri vaut :

```text
score_tri = erreur_cible + nb_cellules_initiales * PENALITE_CELLULE_INITIALE
```

Avec :

```text
PENALITE_CELLULE_INITIALE = 0.001
```

Cette penalite est volontairement tres faible. Elle ne doit pas dominer l'erreur finale ; elle sert seulement a departager deux solutions presque equivalentes.

### 9. Le cache evite de recalculer les memes candidats

Une grille candidate peut reapparaitre plusieurs fois, par exemple apres un croisement ou parce qu'elle fait partie des elites.

La fonction `evaluer_individu` transforme la grille en cle immuable avec `cle_grille`. Si cette cle existe deja dans le cache, le programme reutilise le resultat simule et l'erreur.

Le cache ne change pas la complexite theorique du pire cas, mais il ameliore le temps pratique quand la population contient des doublons.

### 10. Le meilleur candidat subit une amelioration locale

A chaque generation genetique, le meilleur individu courant est teste avec quelques petites modifications locales.

La fonction `ameliorer_individu_local` choisit `NB_ESSAIS_AMELIORATION_LOCALE` cellules au hasard dans la zone de recherche. Pour chaque essai, elle inverse une seule cellule :

```text
0 devient 1
1 devient 0
```

Si cette modification ameliore le score, elle est conservee. Par defaut, le programme fait `18` essais locaux par generation genetique.

Cette partie ressemble a une petite recherche locale greffee sur l'algorithme genetique.

### 11. Les meilleurs candidats sont conserves

Le programme trie tous les candidats par score. Les meilleurs sont copies directement dans la generation suivante.

C'est l'elitisme :

```text
NB_ELITES = 14
```

L'elitisme evite de perdre une bonne solution deja trouvee a cause d'une mutation aleatoire defavorable.

### 12. Des candidats aleatoires sont reinjectes

Une population genetique peut devenir trop uniforme. Dans ce cas, tous les individus se ressemblent et l'algorithme explore mal.

Pour limiter ce probleme, une partie de la nouvelle population est composee de nouvelles grilles aleatoires :

```text
TAUX_INJECTION_ALEATOIRE = 0.06
```

Si le solveur stagne pendant longtemps, ce taux augmente. Cela force l'algorithme a explorer de nouvelles zones de l'espace de recherche.

### 13. Les autres candidats sont produits par reproduction

Tant que la nouvelle population n'a pas atteint `TAILLE_POPULATION`, le programme fabrique des enfants.

Il choisit deux parents avec une selection par tournoi :

1. quelques candidats sont tires au hasard dans la population evaluee ;
2. le meilleur de ce petit groupe devient parent.

Ensuite, les deux parents sont croises avec `croiser`. Le croisement est uniforme : pour chaque cellule de la zone de recherche, l'enfant prend soit la valeur du parent A, soit celle du parent B.

Enfin, l'enfant est mute avec `muter_zone_guidee`. Chaque cellule a une petite probabilite d'etre inversee. La mutation est un peu plus forte pres de la cible et un peu plus faible loin d'elle.

### 14. Les doublons sont retires

La fonction `population_sans_doublons` supprime les grilles identiques avant de commencer la generation suivante.

Si la suppression cree une population trop petite, le programme ajoute de nouveaux individus aleatoires.

### 15. Conditions d'arret

Le solveur s'arrete dans deux cas :

- il trouve une solution exacte, donc `erreur_cible == 0` ;
- il atteint `NB_GENERATIONS_GENETIQUES_MAX`, soit `420` generations genetiques par defaut.

Si aucune solution exacte n'est trouvee, le programme garde quand meme la meilleure solution rencontree.

### 16. Lecture de l'evolution trouvee

Quand une bonne grille initiale est trouvee, l'interface peut afficher son evolution :

- l'etape `0` montre la grille initiale proposee ;
- l'etape `X` montre le resultat obtenu apres simulation ;
- les couleurs indiquent les cellules vivantes, les cellules correctes et les cellules manquantes.

Cela permet de verifier visuellement si la solution converge vraiment vers la cible.

## Baseline brute force aleatoire

Le fichier `random-bruteforce.py` sert de comparaison volontairement simple. Il ne contient pas d'algorithme genetique.

Il repete seulement l'operation suivante :

1. tirer des grilles initiales au hasard dans la meme zone de recherche ;
2. simuler chaque grille pendant `X` generations ;
3. calculer la meme erreur que le solveur genetique ;
4. garder la meilleure grille rencontree.

Il n'y a pas :

- d'elitisme ;
- de selection ;
- de croisement ;
- de mutation ;
- de cache ;
- d'apprentissage entre iterations.

Le but n'est pas de battre le vrai solveur. Le but est de montrer ce que donne un echantillonnage aleatoire quand on lui donne un budget de calcul comparable.

Par defaut, une iteration brute force teste :

```text
P + L = 120 + 18 = 138
```

candidats aleatoires. Cela correspond au nombre de candidats evalues dans une generation genetique du vrai solveur : `P` candidats de population plus `L` essais d'amelioration locale.

## Complexite

On note :

- `N` : nombre total de cellules, ici `24 * 24 = 576` ;
- `A` : nombre de cellules dans la zone active de recherche, avec `A <= N` ;
- `X` : nombre de generations du jeu de la vie a simuler ;
- `P` : taille de population, par defaut `120` ;
- `L` : nombre d'essais d'amelioration locale, par defaut `18` ;
- `G` : nombre maximal de generations genetiques, par defaut `420` ;
- `C` : nombre d'evaluations gardees dans le cache ;
- `I` : nombre d'iterations du brute force aleatoire ;
- `R` : nombre de runs independants du brute force.

### Cout d'une simulation

Une simulation applique `X` fois les regles du jeu de la vie sur la grille :

```text
O(X * N)
```

Dans ce programme, la grille fait toujours `24 * 24`, donc `N` est fixe. On garde quand meme `N` dans la formule pour montrer comment le cout grandirait avec une grille plus grande.

### Cout d'une generation genetique

Une generation genetique evalue environ :

- `P` candidats de population ;
- `L` variantes locales du meilleur candidat.

Le cout principal est donc :

```text
O((P + L) * X * N)
```

Le tri de la population coute `O(P log P)`, mais pour ce programme il est secondaire par rapport aux simulations quand `X` augmente.

### Cout total du solveur genetique

Sur `G` generations genetiques, le cout theorique maximal est :

```text
O(G * (P + L) * X * N)
```

Le cache peut reduire le temps reel si des candidats reapparaissent, mais dans le pire cas tous les candidats sont differents.

La memoire utilisee est approximativement :

```text
O(P * N + C * N + X * N)
```

Elle stocke la population, le cache d'evaluations et l'historique d'evolution affiche par l'interface.

### Cout du brute force aleatoire

Le script aleatoire teste aussi `P + L` candidats par iteration. Une iteration coute donc :

```text
O((P + L) * X * N)
```

Sur `I` iterations :

```text
O(I * (P + L) * X * N)
```

Sur `R` runs independants :

```text
O(R * I * (P + L) * X * N)
```

Si on fixe `I = G`, le brute force aleatoire retombe volontairement sur le meme ordre de complexite theorique que le solveur genetique :

```text
O(G * (P + L) * X * N)
```

La difference est qualitative : avec le meme budget asymptotique, le solveur genetique reutilise l'information des meilleurs candidats, alors que le brute force repart au hasard a chaque essai.
