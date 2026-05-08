# Chasseur de motifs du jeu de la vie

Projet Eniseboard autour du jeu de la vie de Conway.

L'application a deux usages :

- **Jeu normal** : dessiner une grille initiale et observer son évolution avec les règles classiques du jeu de la vie.
- **Résolution** : dessiner une cible finale, choisir un nombre de générations, puis chercher une grille initiale qui produit cette cible après ces générations.

## Lancement

```bash
python3 reverse-search.py
```

Si Eniseboard n'est pas installé :

```bash
pip install eniseboard
```

Les modules d'algorithme restent importables et testables même sans Eniseboard.

## Architecture

Le code principal est découpé en plusieurs fichiers :

- `life_rules.py` : règles normales du jeu de la vie, simulation et historique d'évolution.
- `reverse_search_algorithm.py` : algorithme génétique de recherche inverse, sans aucune interface graphique.
- `app_state.py` : état partagé de l'application.
- `ui_app.py` : interface Tkinter/Eniseboard, boutons, modes, barre de chargement et fenêtre population.
- `reverse-search.py` : petit lanceur historique.
- `random-bruteforce.py` : référence de comparaison aléatoire par force brute.

## Mode jeu normal

Dans ce mode, la grille dessinée est la grille initiale.

Actions principales :

- clic gauche : inverser une cellule ;
- clic droit : effacer une cellule ;
- `Lire / pause` : lancer ou arrêter l'évolution ;
- `Avancer d'une génération` : appliquer une génération ;
- `Grille aléatoire` : remplir aléatoirement la grille ;
- `Effacer` : vider la grille.

## Mode résolution

Dans ce mode, la grille dessinée est la cible finale souhaitée.

Déroulement :

1. Dessiner la cible finale.
2. Choisir le nombre de générations entre la grille initiale cherchée et la cible.
3. Cliquer sur `Lancer le solveur`.
4. Observer la barre de progression, l'erreur, l'exactitude, la stagnation et la taille du cache.
5. Inspecter `Meilleure grille initiale`, `Afficher le résultat` et `Lire l'évolution`.

Si le résultat final n'est pas exact, l'interface affiche une recommandation de nombre de générations ou de simplification de cible.

## Fenêtre population

Le bouton `Voir population` ouvre une deuxième fenêtre Tkinter. Elle affiche :

- un échantillon des individus évalués dans la génération courante ;
- les meilleurs individus de la génération précédente ;
- le rang, le rôle, l'erreur, l'exactitude et le nombre de cellules vivantes ;
- une mini-animation de chaque individu de `G0` à la génération cible.

Cette vue sert à comprendre visuellement le fonctionnement génétique : élites conservées, injections aléatoires, enfants issus du croisement, stagnation et amélioration progressive.

## Idée de l'algorithme

Le problème est inverse : les règles du jeu de la vie sont faciles à appliquer vers le futur, mais il n'existe pas de retour en arrière direct et unique.

Le solveur utilise donc un algorithme génétique :

- créer une population de grilles initiales candidates ;
- ajouter des graines locales quand la cible finale est très petite ;
- simuler chaque candidate pendant le nombre de générations choisi ;
- comparer le résultat à la cible ;
- conserver les meilleurs candidats ;
- créer de nouveaux candidats par sélection, croisement, mutation, graines locales et injection aléatoire ;
- améliorer localement le meilleur candidat courant.

Le score pénalise les cellules manquantes, les cellules en trop, les cellules parasites loin de la cible et, très légèrement, les grilles initiales trop chargées.

Pour éviter la stagnation sur les cibles de quelques cellules, le solveur énumère maintenant de petits ancêtres possibles autour de la cible. Ces mini-candidats sont simulés sous forme d'ensemble de cellules vivantes, puis les meilleurs sont placés dans la population initiale et peuvent être réinjectés si la recherche stagne.

## Tests

Les tests unitaires ne dépendent pas de l'interface graphique :

```bash
python3 -m unittest discover -s tests
```

Ils couvrent les règles du jeu de la vie, le score, l'initialisation du solveur, les graines locales, les instantanés et l'arrêt sur solution exacte.
