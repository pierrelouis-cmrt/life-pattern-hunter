# Recherche inverse du Jeu de la vie

Le programme cherche une grille initiale `G0` qui devient proche d'une cible après `X` **générations du Jeu de la vie**.

```text
simuler(G0, X) ≈ cible
```

Le problème est inverse : avancer le Jeu de la vie est facile, mais retrouver un passé possible ne l'est pas. Une grille `24 x 24` contient `576` cellules, donc une recherche exhaustive demanderait `2^576` essais.

## Deux sens du mot génération

Le projet utilise deux boucles différentes. Il faut les distinguer clairement.

- **Génération du Jeu de la vie** : un passage normal d'une grille `n` à une grille `n+1`.
- **Génération génétique** : une itération du solveur, où une population de candidats est évaluée puis remplacée par une nouvelle population.

Dans ce document :

- `X` désigne le nombre de générations du Jeu de la vie simulées pour évaluer un candidat ;
- `G` désigne le nombre maximal de générations génétiques du solveur.

## Architecture

- `life_rules.py` : règles normales du Jeu de la vie.
- `reverse_search_algorithm.py` : solveur génétique pour une cible et une valeur fixe de `steps`.
- `step_search_controller.py` : relance autour du solveur quand plusieurs valeurs de `steps` doivent être essayées.
- `grid_visuals.py` : génération des PNG pédagogiques.
- `ui_app.py` : interface Eniseboard/Tkinter.

Le solveur principal reste volontairement centré sur l'algorithme génétique. Les essais multi-steps et l'interface sont ailleurs.

## Règles du Jeu de la vie

À chaque **génération du Jeu de la vie** :

- une cellule vivante survit avec 2 ou 3 voisines ;
- une cellule morte naît avec exactement 3 voisines ;
- sinon, la cellule est morte.

![Transition GoL](assets/gol_visuals/gol_transition_blinker.png)

## Idée principale

Un **individu** est une grille initiale candidate.

Pour l'évaluer :

1. on simule l'individu pendant `X` générations du Jeu de la vie ;
2. on compare le résultat avec la cible ;
3. on garde un score : plus il est bas, mieux c'est.

![Population](assets/gol_visuals/population_candidates.png)

Le solveur fait ensuite évoluer une population. Une itération de cette boucle s'appelle une **génération génétique** :

```python
def avancer_solveur_une_generation(solveur):
    evaluations = evaluer_population(solveur.population)
    evaluations.append(ameliorer_localement(le_meilleur))
    trier_par_score(evaluations)

    enregistrer_meilleur_global(evaluations[0])
    enregistrer_snapshot_pour_l_interface(evaluations)

    if solution_exacte_ou_limite:
        arreter()
        return

    population = garder_les_elites(evaluations)
    population += injecter_des_candidats_si_besoin()

    while population_pas_complete:
        parent_a = selection_tournoi(evaluations)
        parent_b = selection_tournoi(evaluations)
        enfant = croiser(parent_a, parent_b)
        muter(enfant)
        population.append(enfant)
```

Ce pseudo-code est proche du code réel : le fichier d'algorithme est maintenant construit pour se lire comme cette boucle.

## Score

Le score mesure l'erreur finale.

```text
score = erreur_finale + 0.001 * cellules_initiales
```

L'erreur distingue trois cas :

- cellule cible manquante : pénalité forte ;
- cellule vivante en trop : pénalité moyenne ;
- cellule en trop loin de la cible : petite pénalité de distance.

```text
faux négatif = 4
faux positif = 1
distance extra = distance * 0.12
```

Les cellules manquantes coûtent plus cher pour éviter que l'algorithme favorise des grilles presque vides.

![Score](assets/gol_visuals/error_score.png)

## Coeur génétique

### Sélection

La sélection utilise un tournoi : on tire quelques individus au hasard et on garde le meilleur.

```python
def selection_tournoi(population):
    candidats = tirer_5_individus()
    return meilleur_score(candidats)
```

Cette méthode est simple et efficace : les bons individus ont plus de chances de se reproduire, mais les autres ne disparaissent pas instantanément.

### Croisement

Le croisement fabrique un enfant à partir de deux parents.

Pour chaque cellule de la zone de recherche, l'enfant prend soit la valeur du parent A, soit celle du parent B.

![Croisement](assets/gol_visuals/parents_child.png)

### Mutation

La mutation inverse quelques cellules. Elle évite que la population reste bloquée sur les mêmes motifs.

Dans le vrai algorithme, le taux reste faible. Le visuel est volontairement exagéré pour rendre l'action évidente.

![Mutation](assets/gol_visuals/mutation.png)

### Élites et injections

À chaque **génération génétique** :

- les meilleurs individus sont conservés tels quels ;
- quelques nouveaux candidats aléatoires sont ajoutés ;
- si la stagnation dure, l'injection augmente et une relance partielle est déclenchée.

![Cycle génétique](assets/gol_visuals/genetic_cycle.png)

## Heuristiques gardées

Le solveur est plus court, mais il garde les aides qui ont un vrai impact.

### Zone de recherche

Le programme modifie surtout une zone autour de la cible.

```text
marge = max(marge_minimale, min(marge_maximale, steps + 2))
```

Cela évite de remplir tout le plateau avec du bruit inutile.

### Carte de distance

Chaque case connaît sa distance à la cellule cible vivante la plus proche.

Cette carte sert à :

- créer plus de cellules près du motif final ;
- pénaliser les cellules parasites loin de la cible ;
- guider légèrement la mutation.

La distance utilisée est la distance de Chebyshev :

```text
distance = max(abs(ligne - ligne_cible), abs(colonne - colonne_cible))
```

### Graines locales

Pour les très petites cibles, le solveur ajoute quelques mini-ancêtres énumérés autour de la cible.

Cette partie est volontairement bornée :

- au plus 18 cases testées ;
- au plus 5 cellules vivantes par mini-candidat ;
- seules les meilleures graines sont injectées.

Elle aide beaucoup les motifs simples comme le blinker, sans transformer l'algorithme en force brute générale.

### Cache

Si une grille a déjà été évaluée, le résultat est réutilisé.

```python
if individu in cache:
    return cache[individu]
```

Le cache accélère les cas réels mais ne change pas le pire cas théorique.

### Amélioration locale et nettoyage

Le meilleur individu est légèrement testé autour de lui : on inverse une cellule au hasard et on garde la modification si elle améliore le score.

Quand une bonne solution est trouvée, le nettoyage essaie de retirer des cellules inutiles. Une suppression est acceptée seulement si l'erreur finale ne s'aggrave pas.

## Complexité

### Notations

- `N` : nombre de cellules du plateau ;
- `X` : nombre de générations du Jeu de la vie simulées pour évaluer un candidat ;
- `P` : taille de population ;
- `G` : nombre maximal de générations génétiques, donc nombre maximal d'itérations de population ;
- `L` : nombre d'essais d'amélioration locale ;
- `R` : nombre maximal d'essais de nettoyage ;
- `T` : nombre de cellules vivantes dans la cible ;
- `Q` : nombre de graines locales testées ;
- `K` : nombre de cellules actives pendant une simulation sparse de graine.

Valeurs principales :

```text
N = 576
P = 120
G = 420
L = 18
R = 80
```

### Évaluer un candidat

Une génération du Jeu de la vie, c'est uniquement le passage `n -> n+1` d'une grille. Elle parcourt toutes les cellules et regarde au plus 8 voisines par cellule.

```text
1 génération du Jeu de la vie = O(N)
X générations du Jeu de la vie = O(X * N)
```

Comparer le résultat à la cible coûte aussi `O(N)`, donc :

```text
évaluer un candidat = O(X * N)
```

Avec le cache, une grille déjà vue coûte seulement `O(N)` pour la clé et les copies. En pire cas, tous les candidats sont nouveaux, donc on garde `O(X * N)`.

### Initialisation

Construire la zone de recherche coûte :

```text
O(N)
```

Construire la carte de distance compare chaque cellule aux `T` cellules vivantes de la cible :

```text
O(N * T)
```

Comme `T <= N`, le pire cas est `O(N^2)`.

Créer la population initiale coûte :

```text
O(P * N)
```

Les graines locales coûtent :

```text
O(Q * (X * K + T + K) + Q log Q)
```

Mais `Q` est borné par les constantes du programme.

### Une génération génétique

Une génération génétique n'est pas une génération du Jeu de la vie. C'est une itération complète du solveur : évaluer la population, trier, garder les élites, croiser, muter et produire la population suivante.

Évaluer la population :

```text
O(P * X * N)
```

Trier la population :

```text
O(P log P)
```

Amélioration locale :

```text
O(L * X * N)
```

Nettoyage conservateur :

```text
O(R * X * N)
```

Créer la population de la génération génétique suivante, copier, croiser, muter et dédoublonner :

```text
O(P * N)
```

Comme `X >= 1`, `P * N` est dominé par `P * X * N`.

Donc :

```text
une génération génétique =
O((P + L + R) * X * N + P log P)
```

### Recherche complète

Le solveur fait au plus `G` générations génétiques, et chaque génération génétique évalue des candidats simulés pendant `X` générations du Jeu de la vie :

```text
O(G * ((P + L + R) * X * N + P log P))
```

En ajoutant l'initialisation :

```text
O(
  N * T
  + P * N
  + Q * (X * K + T + K)
  + Q log Q
  + G * ((P + L + R) * X * N + P log P)
)
```

Le terme dominant reste la simulation répétée des candidats :

```text
O(G * (P + L + R) * X * N)
```

## Mémoire

La mémoire vient surtout de :

- population : `O(P * N)` ;
- cache : `O(C * N)` ;
- snapshot pédagogique : `O(P * N)` ;
- historique d'évolution affiché : `O(X * N)`.

Donc :

```text
O((P + C + X) * N)
```

## Conclusion

Le projet remplace une recherche impossible en `2^N` par une recherche génétique guidée.

Le code garde les outils utiles pour obtenir de bons résultats, mais le coeur reste scolaire :

```text
évaluer -> sélectionner -> croiser -> muter -> recommencer
```

La complexité est calculable clairement, car le coût dominant est toujours le même : à chaque génération génétique, simuler beaucoup de candidats pendant `X` générations du Jeu de la vie.
