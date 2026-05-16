# Algorithme génétique simplifié

## Objectif

On cherche une grille initiale du Jeu de la vie qui, après un nombre fixé de
passages, donne une cible dessinée par l'utilisateur.

Le problème est inverse : simuler vers le futur est direct, mais retrouver un
passé exact ne l'est pas. On utilise donc un algorithme génétique simple, avec
seulement quelques aides à très bon rendement.

## Données utilisées

- `cible` : grille finale souhaitée.
- `X` : nombre de passages du Jeu de la vie à appliquer.
- `P` : taille de population.
- `E` : nombre d'élites conservées.
- `G` : nombre maximal de générations génétiques.
- `d` : densité initiale des grilles aléatoires.
- `m` : taux de mutation.
- `Z` : zone active autour de la cible.

Par défaut, la densité initiale vaut `0.23` et le taux de mutation vaut `0.05`.
Le taux de mutation peut monter jusqu'à `0.30` si le meilleur résultat global ne
s'améliore plus.

## Cycle complet

### 1. Zone active

Avant de créer la population, on calcule le rectangle qui contient toutes les
cellules vivantes de la cible. On l'agrandit avec une marge dépendant du nombre
de passages demandés.

L'algorithme ne crée, croise et mute des cellules que dans cette zone. Le reste
de la grille reste vide.

Cette idée change beaucoup les résultats : au lieu de chercher dans toute la
grille `24 * 24`, on cherche souvent dans une petite fenêtre autour du dessin.

### 2. Population initiale

Chaque individu est une grille vide, puis on remplit aléatoirement seulement la
zone active. Pour chaque case de cette zone, on tire un nombre aléatoire :

- si le tirage est inférieur à `d`, la cellule est vivante ;
- sinon, elle est morte.

La cible n'est pas ajoutée à la population. La grille dessinée courante n'est
pas ajoutée non plus. La population de départ est uniquement aléatoire.

La densité est ajustée à la taille de la cible : les petites cibles produisent
des candidats plus clairsemés que les grosses cibles.

### 3. Évaluation

Pour chaque individu :

1. on simule la grille pendant `X` passages du Jeu de la vie ;
2. on compare le résultat avec la cible ;
3. on compte le nombre de cases différentes.

Le score est pondéré :

```text
score = 4 * cellules cibles manquantes + 1 * cellules en trop
```

Un score de `0` signifie que l'individu est une solution exacte.

Cette pondération évite qu'une grille presque vide soit considérée trop bonne
pour une petite cible. Manquer une cellule dessinée est plus grave qu'avoir une
cellule parasite.

### 4. Sélection des élites

On trie toute la population par score croissant. Les `E` meilleurs individus
sont les élites. Elles sont recopiées telles quelles dans la génération
suivante.

Cette conservation évite de perdre le meilleur résultat déjà trouvé.

### 5. Nouveaux individus aléatoires

À chaque génération, une petite partie de la population est remplacée par de
nouveaux individus aléatoires dans la zone active.

C'est l'anti-stagnation le plus simple : même si les élites deviennent trop
semblables, la recherche reçoit régulièrement du matériel génétique neuf.

### 6. Croisement

Pour créer un enfant, on tire deux élites au hasard. Pour chaque case de la
zone active, l'enfant reçoit soit la cellule du premier parent, soit celle du
second parent, avec une probabilité de `50 %`.

Ce croisement est uniforme : à l'intérieur de la zone active, il ne tient pas
compte des formes ni d'une distance à la cible.

### 7. Mutation

Après le croisement, chaque cellule de l'enfant peut être inversée :

- vivante vers morte ;
- morte vers vivante.

La probabilité d'inversion est le taux de mutation courant. Elle commence à
`0.05`, puis augmente par paliers quand le meilleur résultat ne s'améliore plus.
Elle reste plafonnée à `0.30`.

### 8. Arrêt

La recherche s'arrête dans deux cas :

- le meilleur individu obtient un score de `0` ;
- la limite de `G` générations génétiques est atteinte.

## Pseudo-code

```text
zone = rectangle autour de la cible
population = créer P grilles aléatoires dans cette zone
meilleur_global = aucun

tant que la recherche n'est pas terminée :
    évaluations = []

    pour chaque individu dans population :
        résultat = simuler(individu, X passages)
        erreur = 4 * cellules manquantes + cellules en trop
        ajouter (individu, résultat, erreur) aux évaluations

    trier évaluations par erreur croissante
    meilleur = première évaluation
    mettre à jour meilleur_global si meilleur est meilleur

    si meilleur_global.erreur == 0 :
        arrêter : solution exacte

    si limite de générations atteinte :
        arrêter : limite atteinte

    élites = les E meilleures évaluations
    nouvelle_population = copie des élites
    ajouter quelques nouveaux individus aléatoires

    tant que nouvelle_population contient moins de P individus :
        parent_a, parent_b = deux élites au hasard
        enfant = croisement uniforme dans la zone active
        enfant = mutation simple dans la zone active
        ajouter enfant à nouvelle_population

    population = nouvelle_population
```

## Ce qui est volontairement absent

Cette version ne contient pas :

- cache ;
- nettoyage ;
- amélioration locale ;
- graines pour petites formes ;
- carte de distance ;
- relance complexe en cas de stagnation ;
- essai automatique de plusieurs valeurs de `X`.

Le compromis est volontaire : on réintroduit seulement ce qui améliore fortement
les résultats avec peu de code.
