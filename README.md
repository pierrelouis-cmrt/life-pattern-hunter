# Life Pattern Hunter

Projet Eniseboard autour du jeu de la vie de Conway.

L'application a deux usages :

- **Jeu normal** : dessiner une grille initiale et observer son evolution avec les regles classiques du jeu de la vie.
- **Resolution** : dessiner une cible finale, choisir un nombre de `Steps`, puis chercher une grille initiale qui produit cette cible apres ces steps.

## Lancement

```bash
python3 reverse-search.py
```

Si Eniseboard n'est pas installe :

```bash
pip install eniseboard
```

Les modules d'algorithme restent importables et testables meme sans Eniseboard.

## Architecture

Le code principal est decoupe en plusieurs fichiers :

- `life_rules.py` : regles normales du jeu de la vie, simulation et historique d'evolution.
- `reverse_search_algorithm.py` : algorithme genetique de reverse search, sans aucune interface graphique.
- `app_state.py` : etat partage de l'application.
- `ui_app.py` : interface Tkinter/Eniseboard, boutons, modes, barre de chargement et fenetre population.
- `reverse-search.py` : petit launcher historique.
- `random-bruteforce.py` : baseline aleatoire de comparaison.

## Mode jeu normal

Dans ce mode, la grille dessinee est la grille initiale.

Actions principales :

- clic gauche : inverser une cellule ;
- clic droit : effacer une cellule ;
- `Lire / pause` : lancer ou arreter l'evolution ;
- `Step +1` : appliquer une generation ;
- `Grille aleatoire` : remplir aleatoirement la grille ;
- `Clear` : vider la grille.

## Mode resolution

Dans ce mode, la grille dessinee est la cible finale souhaitee.

Deroulement :

1. Dessiner la cible finale.
2. Choisir `Steps`, le nombre de generations entre la grille initiale cherchee et la cible.
3. Cliquer sur `Start solver`.
4. Observer la barre de progression, l'erreur, l'exactitude, la stagnation et la taille du cache.
5. Inspecter `Best initial`, `Show result` et `Play evolution`.

Si le resultat final n'est pas exact, l'interface affiche une recommendation de nombre de steps ou de simplification de cible.

## Fenetre population

Le bouton `Voir population` ouvre une deuxieme fenetre Tkinter. Elle affiche :

- tous les individus evalues dans la generation courante ;
- les meilleurs individus de la generation precedente ;
- le rang, le role, l'erreur, l'exactitude et le nombre de cellules vivantes ;
- une mini-animation de chaque individu de `G0` a `Gsteps`.

Cette vue sert a comprendre visuellement le fonctionnement genetique : elites conservees, injections aleatoires, enfants issus du croisement, stagnation et amelioration progressive.

## Idee de l'algorithme

Le probleme est inverse : les regles du jeu de la vie sont faciles a appliquer vers le futur, mais il n'existe pas de retour en arriere direct et unique.

Le solveur utilise donc un algorithme genetique :

- creer une population de grilles initiales candidates ;
- simuler chaque candidate pendant `Steps` generations ;
- comparer le resultat a la cible ;
- conserver les meilleurs candidats ;
- creer de nouveaux candidats par selection, croisement, mutation et injection aleatoire ;
- ameliorer localement le meilleur candidat courant.

Le score penalise les cellules manquantes, les cellules en trop, les cellules parasites loin de la cible et, tres legerement, les grilles initiales trop chargees.

## Tests

Les tests unitaires ne dependent pas de l'interface graphique :

```bash
python3 -m unittest discover -s tests
```

Ils couvrent les regles du jeu de la vie, le score, l'initialisation du solveur, les snapshots et l'arret sur solution exacte.
