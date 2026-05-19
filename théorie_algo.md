# Théorie de l'algorithme

## Objectif

Le but est de retrouver une grille de départ du Jeu de la vie. Cette grille,
après un nombre choisi de passages, doit produire la cible dessinée par
l'utilisateur.

C'est un problème inverse : faire avancer une grille est direct, mais retrouver
son passé ne l'est pas. L'application utilise donc une recherche génétique,
avec quelques choix simples pour guider la recherche sans rendre le code
difficile à suivre.

## Données utilisées

- `cible` : grille finale que l'on veut obtenir.
- `X` : nombre de passages du Jeu de la vie à appliquer.
- `P` : taille de population.
- `E` : nombre d'élites conservées.
- `G` : nombre maximal de générations génétiques.
- `d` : densité initiale des grilles aléatoires.
- `m` : taux de mutation.
- `Z` : zone active autour de la cible.

Par défaut, la densité initiale vaut `0.23` et le taux de mutation vaut `0.05`.
Si le meilleur résultat ne progresse plus, le taux de mutation peut monter
progressivement jusqu'à `0.30`.

## Cycle complet

### 1. Zone active

Avant de créer la population, on repère le rectangle qui contient toutes les
cellules vivantes de la cible. On l'agrandit ensuite avec une marge, car une
cellule utile peut se trouver un peu autour du dessin de départ.

La recherche ne crée, croise et mute des cellules que dans cette zone. Le reste
de la grille reste vide.

Cette zone rend la recherche plus raisonnable : au lieu de modifier toute la
grille `24 * 24`, on travaille surtout près du motif à retrouver.

### 2. Population initiale

Chaque candidat commence comme une grille vide. On remplit ensuite seulement la
zone active avec un tirage aléatoire :

- si le tirage est inférieur à `d`, la cellule est vivante ;
- sinon, elle est morte.

La cible n'est pas ajoutée directement dans la population. La grille dessinée
courante non plus. Au départ, la population est donc vraiment aléatoire.

La densité est ajustée à la taille de la cible. Une petite cible donne des
candidats plus clairsemés qu'une cible plus remplie.

### 3. Évaluation

Pour chaque candidat :

1. on simule la grille pendant `X` passages du Jeu de la vie ;
2. on compare le résultat avec la cible ;
3. on calcule son score d'erreur.

Le score est pondéré :

```text
score = 4 * cellules cibles manquantes + 1 * cellules en trop
```

Un score de `0` signifie que le candidat donne exactement la cible.

Cette pondération évite qu'une grille presque vide paraisse trop bonne pour une
petite cible. Dans ce projet, rater une cellule dessinée coûte donc plus cher
que produire une cellule en trop.

### 4. Sélection des élites

On trie toute la population du meilleur score au moins bon. Les `E` meilleurs
candidats deviennent les élites. Ils sont recopiés tels quels dans la
génération suivante.

Cela évite de perdre un bon résultat à cause d'un croisement ou d'une mutation.

### 5. Nouveaux candidats aléatoires

À chaque génération, une petite partie de la population est remplacée par de
nouveaux candidats aléatoires dans la zone active.

Cela aide quand la population tourne en rond. Même si les élites deviennent
trop semblables, la recherche reçoit régulièrement de nouvelles formes à tester.

### 6. Croisement

Pour créer un enfant, on choisit deux élites au hasard. Pour chaque case de la
zone active, l'enfant reprend soit la cellule du premier parent, soit celle du
second parent, avec une probabilité de `50 %`.

Ce croisement est uniforme : à l'intérieur de la zone active, il ne tient pas
compte des formes ni d'une distance à la cible.

### 7. Mutation

Après le croisement, chaque cellule de l'enfant peut être inversée :

- vivante vers morte ;
- morte vers vivante.

La probabilité d'inversion est le taux de mutation courant. Elle commence à
`0.05`, puis augmente par paliers si le meilleur résultat ne s'améliore plus.
Elle ne dépasse jamais `0.30`.

### 8. Arrêt

La recherche s'arrête dans deux situations :

- le meilleur candidat obtient un score de `0` ;
- la limite de `G` générations génétiques est atteinte.

## Pseudo-code

```text
zone = rectangle autour de la cible
population = créer P grilles aléatoires dans cette zone
meilleur_global = aucun

tant que la recherche n'est pas terminée :
    évaluations = []

    pour chaque candidat dans population :
        résultat = simuler(candidat, X passages)
        erreur = 4 * cellules manquantes + cellules en trop
        ajouter (candidat, résultat, erreur) aux évaluations

    trier évaluations par erreur croissante
    meilleur = première évaluation
    mettre à jour meilleur_global si meilleur est meilleur

    si meilleur_global.erreur == 0 :
        arrêter : solution exacte

    si limite de générations atteinte :
        arrêter : limite atteinte

    élites = les E meilleures évaluations
    nouvelle_population = copie des élites
    ajouter quelques nouveaux candidats aléatoires

    tant que nouvelle_population contient moins de P candidats :
        parent_a, parent_b = deux élites au hasard
        enfant = croisement uniforme dans la zone active
        enfant = mutation simple dans la zone active
        ajouter enfant à nouvelle_population

    population = nouvelle_population
```
