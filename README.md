# Life Pattern Hunter

Projet Eniseboard autour du jeu de la vie de Conway.

Le projet `Pattern Hunter` est pour l'instant mis en pause. Le travail courant se concentre sur la **reverse search** : chercher une grille initiale qui, apres `X` generations, produit une cible finale dessinee par l'utilisateur.

L'ancien explorateur de motifs est conserve dans `archive/`.

## Programme principal

Le programme principal est maintenant :

```bash
python3 reverse-search.py
```

Il ouvre une interface graphique ou l'utilisateur dessine le motif final souhaite, choisit le nombre d'etapes, puis lance un solveur inverse.

## Installation

```bash
pip install eniseboard
```

## Lancer la reverse search

```bash
python3 reverse-search.py
```

Dans l'interface :

- dessiner la cible finale sur la grille ;
- regler `Steps`, le nombre de generations a remonter indirectement ;
- cliquer sur `Start` pour lancer la recherche ;
- utiliser `Best initial`, `Show result` et `Play evolution` pour inspecter la solution trouvee.

Le solveur garde la meilleure grille initiale rencontree. Si une solution exacte existe et est trouvee, l'erreur tombe a `0`.

## Idee de l'algorithme

Le probleme est inverse : les regles du jeu de la vie sont simples a appliquer vers le futur, mais il n'existe pas de retour en arriere direct et unique.

Le programme utilise donc un algorithme genetique :

- creation d'une population de grilles initiales candidates ;
- simulation de chaque candidate pendant `X` generations ;
- comparaison du resultat avec la cible finale ;
- conservation des meilleurs candidats ;
- generation de nouveaux candidats par selection, croisement, mutation et injection aleatoire ;
- amelioration locale du meilleur candidat courant.

Le score penalise les cellules manquantes dans la cible, les cellules en trop, les cellules parasites eloignees de la cible et, tres legerement, les grilles initiales trop chargees.

Les explications detaillees sont dans :

- `ALGORITHM_SHORT.md` : version concise ;
- `ALGORITHM.md` : version complete avec complexite.

## Baseline aleatoire

`random-bruteforce.py` sert de comparaison avec une strategie volontairement simple : tirer des grilles initiales au hasard, les simuler, puis garder la meilleure.

Exemple :

```bash
python3 random-bruteforce.py --target block --steps 5 --runs 5 --show-best
```

Options principales :

- `--target block|blinker|glider` : cible predefinie ;
- `--steps` : nombre de generations a simuler ;
- `--runs` : nombre de runs independants ;
- `--max-iterations` : limite d'iterations par run ;
- `--samples-per-iteration` : nombre de candidats tires par iteration ;
- `--seed` : graine aleatoire reproductible ;
- `--show-best` : affiche la meilleure grille initiale trouvee.

## Pattern Hunter en pause

La premiere version du projet explorait automatiquement des motifs inhabituels du jeu de la vie avec un algorithme genetique Quality-Diversity.

Cette piste est mise en pause pour l'instant. Le code et les tests associes ont ete deplaces dans `archive/` afin de garder l'historique sans melanger les priorites actuelles.
