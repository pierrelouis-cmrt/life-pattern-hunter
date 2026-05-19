# Notes d'oral - Life Pattern Hunter

Durée visée : 7 à 10 minutes.

Objectif : notes orales concises, avec des phrases scientifiques, directes et assez détaillées.

## Diapo 1 - Définition du Jeu de la vie

**Plan prof :** (a) présentation rapide de GoL

**À mettre sur la diapo :**

```text
Jeu de la vie de Conway
= automate cellulaire sur une grille
```

```text
1 cellule = morte ou vivante
1 génération = 1 mise à jour de toute la grille
```

**À dire :**

Le Jeu de la vie de Conway est un automate cellulaire.

Il se définit sur une grille composée de cellules. Chaque cellule possède un état binaire : morte ou vivante.

L'évolution est discrète. À chaque génération, une nouvelle grille est calculée à partir de la grille précédente.

Il n'y a pas de joueur. L'évolution dépend uniquement des règles.

**Illustration :**

- Petite grille avec cellules mortes/vivantes.
- Légende : blanc = mort, noir ou vert = vivant.

## Diapo 2 - Règles locales

**Plan prof :** (a) règles du GoL

**À mettre sur la diapo :**

```text
Chaque cellule regarde ses 8 voisines.
Toutes les cellules sont mises à jour en même temps.
```

```text
Vivante + 2 ou 3 voisines -> vivante
Morte + exactement 3 voisines -> vivante
Sinon -> morte
```

**À dire :**

L'état suivant d'une cellule dépend seulement de son état actuel et du nombre de voisines vivantes autour d'elle.

Le voisinage contient au maximum huit cellules : haut, bas, gauche, droite et diagonales.

Les mises à jour sont synchrones. On calcule toute la nouvelle grille à partir de l'ancienne grille.

Les règles sont locales, mais elles peuvent produire des comportements globaux complexes.

**Illustration conseillée :**

Schéma possible : trois petites grilles montrant un motif qui change d'une
génération à la suivante.

**Code possible :**

```python
if grille[i][j] == 1 and voisins in (2, 3):
    suivante[i][j] = 1
elif grille[i][j] == 0 and voisins == 3:
    suivante[i][j] = 1
```

## Diapo 3 - Problème direct et problème inverse

**Plan prof :** (a) déterminisme + enjeu inverse

**À mettre sur la diapo :**

```text
Problème direct :
G0 -> règles -> G1 -> ... -> GX

Problème inverse :
? -> règles appliquées X fois -> cible
```

**À dire :**

Dans le sens direct, le Jeu de la vie est déterministe. Une même grille initiale produit toujours le même futur.

Le projet traite le problème inverse. On connaît une cible finale et on cherche une grille initiale capable de produire cette cible après `X` générations.

L'inverse n'est pas une fonction simple. Une cible peut avoir aucun antécédent, un seul antécédent, ou plusieurs antécédents.

L'algorithme ne remonte pas le temps par une formule exacte. Il teste des grilles initiales candidates et garde celles qui produisent le résultat le plus proche.

## Diapo 4 - Taille de l'espace de recherche

**Plan prof :** (a) difficulté du problème

**À mettre sur la diapo :**

```text
Grille 24 x 24 = 576 cellules
Chaque cellule : 2 états possibles
Nombre de grilles possibles = 2^576
```

**À dire :**

Une grille de `N` cellules possède `2^N` configurations possibles.

Dans le projet, la grille par défaut fait `24 x 24`, donc `N = 576`.

Une recherche exhaustive devrait tester `2^576` grilles initiales. Ce nombre est trop grand pour être parcouru.

Le problème doit donc être formulé comme une recherche guidée. L'objectif est de trouver une bonne solution, pas de tester toutes les solutions possibles.

**Illustration possible :**

```text
grille candidate -> simulation X générations -> comparaison avec la cible
```

## Diapo 5 - Familles d'algorithmes possibles

**Plan prof :** (b) familles d'algorithmes et choix

**À mettre sur la diapo :**

| Famille | Principe | Limite |
| --- | --- | --- |
| Force brute | tester toutes les grilles | explosion en `2^N` |
| Contraintes / SAT | encoder les règles en contraintes | plus complexe |
| Recherche locale | modifier progressivement une grille | blocage possible |
| Génétique | faire évoluer une population | pas de garantie exacte |

**À dire :**

La force brute est théoriquement simple, mais inutilisable à cause du nombre de configurations.

Une approche par contraintes ou par SAT peut modéliser les règles de manière exacte. Elle est plus difficile à implémenter et moins adaptée à une présentation courte.

Une recherche locale peut améliorer une grille étape par étape. Elle risque cependant de rester bloquée dans un optimum local.

L'algorithme génétique est adapté ici parce qu'une grille binaire peut être vue comme un individu. Chaque cellule joue le rôle d'un gène.

Le choix est aussi pédagogique. On peut expliquer clairement la population, le score, la sélection, le croisement et la mutation.

## Diapo 6 - Principe de l'algorithme génétique

**Plan prof :** (c) présentation théorique de l'algorithme

**À mettre sur la diapo :**

```text
population -> évaluation -> élites -> croisement -> mutation -> nouvelle population
```

**À dire :**

La population contient plusieurs grilles initiales candidates.

Chaque candidat est évalué en le simulant pendant `X` générations du Jeu de la vie.

Le résultat simulé est comparé à la cible. Cette comparaison donne un score d'erreur.

Les meilleurs candidats sont appelés élites. Ils sont conservés dans la génération génétique suivante.

Les autres individus sont produits par croisement, mutation, et ajout de quelques nouveaux individus aléatoires.

Une génération du Jeu de la vie correspond à une évolution de la grille. Une génération génétique correspond à un cycle complet de l'algorithme sur toute la population.

**Illustrations conseillées :**

Schémas possibles : plusieurs grilles candidates côte à côte, puis une boucle
population -> évaluation -> sélection -> nouvelle population.

## Diapo 7 - Score et zone active

**Plan prof :** (c) détails théoriques

**À mettre sur la diapo :**

```text
score = 4 * cellules cibles manquantes + 1 * cellules en trop
```

```text
zone active = rectangle autour de la cible + marge
```

**À dire :**

Le score mesure l'écart entre le résultat simulé et la cible.

Un score de `0` correspond à une solution exacte.

Une cellule cible manquante coûte `4`. Une cellule en trop coûte `1`.

Cette pondération évite qu'une grille presque vide soit trop bien notée pour une petite cible.

La zone active limite la création, le croisement et la mutation aux cellules proches du motif cible.

Cette zone réduit l'espace de recherche. Elle évite aussi d'ajouter du bruit loin du motif.

**Illustration conseillée :**

Schéma possible : une cible, un résultat simulé, puis les cellules manquantes
et les cellules en trop colorées différemment.

## Diapo 8 - Croisement, mutation et pseudo-code

**Plan prof :** (c) pseudo-code

**À mettre sur la diapo :**

```text
population = créer P grilles aléatoires

tant que la recherche continue :
    évaluer chaque individu
    trier par score
    garder les E meilleurs

    nouvelle_population = élites
    ajouter quelques individus aléatoires

    tant que la population n'est pas complète :
        choisir deux élites
        enfant = croisement(parent_a, parent_b)
        enfant = mutation(enfant)
        ajouter enfant
```

**À dire :**

Le croisement combine deux parents. Pour chaque cellule de la zone active, l'enfant reçoit soit la valeur du parent A, soit la valeur du parent B.

La mutation inverse certaines cellules avec une faible probabilité. Une cellule morte peut devenir vivante, et une cellule vivante peut devenir morte.

La mutation est nécessaire pour créer de nouvelles variations qui ne sont pas présentes dans les parents.

L'ajout d'individus aléatoires limite la stagnation de la population.

**Illustrations conseillées :**

Schémas possibles : deux parents qui donnent un enfant, puis quelques cellules
qui changent d'état après mutation.

## Diapo 9 - Complexité théorique

**Plan prof :** (c) complexité théorique

**À mettre sur la diapo :**

```text
N = nombre de cellules
P = taille de population
E = nombre d'élites
X = générations GoL simulées par candidat
G = générations génétiques maximum
Z = taille de la zone active
```

```text
1 génération GoL = O(N)
1 candidat = O(X * N)
1 population = O(P * X * N)
```

```text
coût total =
O(G * (P * X * N + P log P + E * N + P * Z))
```

À retenir :

```text
O(G * P * X * N)
```

**À dire :**

Une génération du Jeu de la vie parcourt toutes les cellules de la grille.

Pour chaque cellule, on regarde au plus huit voisines. Ce facteur est constant, donc le coût d'une génération est `O(N)`.

Un candidat est simulé pendant `X` générations. Son évaluation coûte donc `O(X * N)`.

Une population contient `P` candidats. L'évaluation d'une population coûte `O(P * X * N)`.

À chaque génération génétique, on ajoute aussi le tri en `O(P log P)` et la construction de la nouvelle population.

Le terme dominant est généralement la simulation répétée des candidats. La forme principale est donc `O(G * P * X * N)`.

La zone active réduit l'espace de recherche, mais la simulation actuelle parcourt encore toute la grille.

## Diapo 10 - Implémentation Python

**Plan prof :** (d) algorithme implémenté

**À mettre sur la diapo :**

Paramètres réels :

```python
taille_population = 120
nb_elites = 14
taux_mutation = 0.05
taux_mutation_max = 0.30
fraction_nouveaux_aleatoires = 0.18
nb_generations_max = 420
```

Évaluation :

```python
resultat = simuler(individu, passages, config.bords_toriques)
erreur = erreur_par_rapport_a_cible(resultat, cible, config)
```

Génération suivante :

```python
elites = evaluations[:config.nb_elites]
nouvelle = [copier_grille(evaluation.individu) for evaluation in elites]

while len(nouvelle) < config.taille_population:
    parent_a, parent_b = choisir_parents_elites(elites, hasard)
    enfant = croiser(parent_a, parent_b, config, hasard, zone)
    nouvelle.append(muter(enfant, config, hasard, zone, taux_mutation))
```

**À dire :**

L'algorithme est implémenté dans `recherche_genetique.py`.

La classe `ConfigurationRecherche` regroupe les paramètres de recherche.

La fonction `evaluer_individu` simule un individu, compare le résultat à la cible, puis calcule son score.

La fonction `construire_population_suivante` conserve les élites, ajoute des individus aléatoires, puis crée les enfants par croisement et mutation.

Le code reste volontairement lisible. Il ne contient pas de cache, pas d'amélioration locale et pas de nettoyage final.

Le but est d'obtenir un algorithme lisible, testable et cohérent avec l'analyse de complexité.

## Diapo 11 - Complexité pratique

**Plan prof :** (e) complexité en pratique

**À mettre sur la diapo :**

```text
Si P, X et G sont fixes,
le temps doit surtout suivre N.
```

```text
Grille carrée : N = n^2
Grille 8 x 8 : N = 64 cellules
```

```text
cellules visitées ≈ G * P * X * N
```

**À dire :**

Sur une grille `8 x 8`, une génération du Jeu de la vie parcourt `64` cellules.

Cela ne signifie pas que tout l'algorithme coûte `64` opérations. Ce coût est répété pour chaque candidat, pour chaque génération simulée, et pour chaque génération génétique.

Avec `G = 100`, `P = 120`, `X = 3` et `N = 64`, on obtient environ :

```text
100 * 120 * 3 * 64 = 2 304 000 cellules visitées
```

Pour vérifier la tendance pratique, on fixe `P`, `X` et le nombre de générations génétiques, puis on fait varier seulement la taille de la grille.

**Tableau possible :**

Mesure indicative avec `P = 40`, `X = 2`, `25` générations génétiques fixes :

| Taille | N | Temps moyen | Temps / cellule |
| --- | ---: | ---: | ---: |
| 8 x 8 | 64 | 0,070 s | 1092 us |
| 12 x 12 | 144 | 0,161 s | 1115 us |
| 16 x 16 | 256 | 0,278 s | 1085 us |
| 24 x 24 | 576 | 0,624 s | 1083 us |

Le temps par cellule reste proche. Cela confirme que, lorsque les autres paramètres sont fixés, le coût suit principalement `N`, donc `n^2` pour une grille carrée.

## Diapo 12 - Conclusion

**À mettre sur la diapo :**

```text
GoL : règles simples, évolution déterministe
Problème inverse : espace de recherche énorme
Méthode : algorithme génétique
Coût dominant : O(G * P * X * N)
```

**À dire :**

Le Jeu de la vie est simple à simuler vers le futur, mais difficile à inverser.

La recherche exhaustive est impossible à cause du nombre de grilles initiales possibles.

L'algorithme génétique fournit une méthode de recherche guidée. Il manipule une population de grilles, sélectionne les meilleures, puis crée de nouveaux candidats par croisement et mutation.

L'algorithme ne garantit pas toujours une solution exacte. Il permet cependant d'explorer efficacement un espace trop grand pour la force brute.

Le coût principal vient de la simulation répétée des candidats.

## Répartition avec le plan du prof

| Plan imposé | Diapos |
| --- | --- |
| (a) GoL, règles, déterminisme, rôle de l'algo | 1, 2, 3, 4 |
| (b) Familles d'algorithmes, choix du génétique | 5 |
| (c) Théorie, pseudo-code, complexité | 6, 7, 8, 9 |
| (d) Implémentation Python | 10 |
| (e) Complexité pratique | 11 |

## Si vous devez raccourcir

- Fusionner les diapositives 3 et 4.
- Fusionner les diapositives 7 et 8.
- Enlever le tableau de la diapositive 11 et garder seulement l'exemple `8 x 8`.
