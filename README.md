# Chasseur de motifs du jeu de la vie

Projet Eniseboard autour du jeu de la vie de Conway.

L'application a deux usages :

- **Jeu normal** : dessiner une grille initiale et observer son évolution avec les règles classiques du jeu de la vie.
- **Résolution** : dessiner une cible finale, choisir éventuellement un minimum de passages du Jeu de la vie, puis chercher automatiquement une grille initiale qui produit cette cible.

## Lancement

```bash
python3 main.py
```

Si Eniseboard n'est pas installé :

```bash
pip install eniseboard
```

Les modules d'algorithme restent importables et testables même sans Eniseboard.

## Architecture

Le code principal est découpé en plusieurs fichiers :

- `life_rules.py` : règles normales du jeu de la vie, simulation et historique d'évolution.
- `reverse_search_algorithm.py` : algorithme génétique de recherche inverse pour une cible et une valeur fixe de passages du Jeu de la vie, sans interface graphique.
- `step_search_controller.py` : contrôleur des essais automatiques de plusieurs valeurs de passages.
- `app_state.py` : état partagé de l'application.
- `ui_app.py` : interface Tkinter/Eniseboard, modes de travail, boutons groupés, barre de progression et lecture de solution.
- `grid_visuals.py` : génération standard-library des PNG pédagogiques dans `assets/gol_visuals/`.
- `main.py` : point d'entrée principal de l'application.
- `tests/` : tests unitaires.
- `archive/` : anciens scripts, références et supports qui ne font plus partie du parcours principal.

## Mode jeu normal

Dans ce mode, la grille dessinée est la grille initiale.

Actions principales :

- clic gauche : inverser une cellule ;
- clic droit : effacer une cellule ;
- `Lire l'évolution du Jeu de la vie` : lancer ou arrêter l'évolution ;
- `Avancer d'un seul passage n -> n+1` : appliquer un passage du Jeu de la vie ;
- `Créer une grille initiale aléatoire` : remplir aléatoirement la grille ;
- `Effacer tout le plateau` : vider la grille.

## Mode résolution

Dans ce mode, la grille dessinée est la cible finale souhaitée.

Déroulement :

1. Dessiner la cible finale.
2. Optionnel : renseigner `Minimum de passages du Jeu de la vie à remonter` pour empêcher les relances automatiques de tester des valeurs trop petites.
3. Cliquer sur `Trouver une grille initiale`.
4. Observer la barre de progression, l'erreur, l'exactitude, la stagnation et la taille du cache.
5. Inspecter `Voir la grille initiale trouvée`, `Voir le résultat obtenu après évolution` et `Rejouer l'évolution initiale -> cible`.

Si le résultat final n'est pas exact, l'interface affiche des nombres de passages du Jeu de la vie concrets à essayer. Pour les cibles très petites, elle propose notamment des valeurs courtes comme `1, 2, 3, 4, 5, 6, 8`, et signale les périodes simples quand elle en détecte une. Quand la stagnation semble devoir durer jusqu'à la limite génétique, l'application lance automatiquement d'autres essais en partant du minimum demandé, puis en ajoutant `1` à chaque nouvel essai. Elle teste au maximum 8 valeurs de passages du Jeu de la vie au total, essai initial inclus, et garde le meilleur résultat global.

## Idée de l'algorithme

Le problème est inverse : les règles du jeu de la vie sont faciles à appliquer vers le futur, mais il n'existe pas de retour en arrière direct et unique.

Le solveur utilise donc un algorithme génétique :

- créer une population de grilles initiales candidates ;
- ajouter des graines locales quand la cible finale est très petite ;
- simuler chaque candidate pendant le nombre de passages du Jeu de la vie testé ;
- comparer le résultat à la cible ;
- conserver les meilleurs candidats ;
- créer de nouveaux candidats par sélection, croisement, mutation, graines locales et injection aléatoire ;
- améliorer localement le meilleur candidat courant ;
- nettoyer conservativement les meilleures solutions en retirant les cellules initiales inutiles.

Le score pénalise les cellules manquantes, les cellules en trop, les cellules parasites loin de la cible et, très légèrement, les grilles initiales trop chargées.

Pour éviter la stagnation sur les cibles de quelques cellules, le solveur énumère de petits ancêtres possibles autour de la cible. Ces mini-candidats sont simulés sous forme d'ensemble de cellules vivantes, puis les meilleurs sont placés dans la population initiale et peuvent être réinjectés si la recherche stagne. Même quand le nombre de passages demandé est grand, le solveur teste aussi de courts horizons utiles pour retrouver des motifs périodiques simples.

Quand la stagnation dure trop longtemps, une relance forte remplace une partie de la population par des injections très clairsemées, des graines locales et quelques mutations plus agressives du meilleur global. Les élites restent conservées.

Si cette relance ne débloque toujours pas la recherche, `step_search_controller.py` considère que le `steps` courant est probablement mauvais pour cette cible. Il passe alors automatiquement au minimum demandé, puis `minimum + 1`, puis `minimum + 2`, sans attendre les 420 générations génétiques, puis restaure le meilleur essai trouvé. Le statut final affiche les stats des essais : `steps`, erreur, exactitude, nombre de cellules de la meilleure grille initiale et stagnation. Le champ de minimum permet d'éviter les solutions trop courtes, par exemple celles à 1 passage du Jeu de la vie.

Le nettoyage automatique est conservateur : il retire une cellule de la grille initiale seulement si la simulation finale garde la même erreur ou l'améliore. Une solution exacte reste donc exacte. Le même nettoyage peut être lancé hors interface :

```bash
python3 archive/tools/solution_cleaner.py --initial initial.txt --target target.txt --steps 5 --output cleaned.txt
```

Les fichiers texte utilisent `#` pour une cellule vivante et `.` pour une cellule morte.

## Tests

Les tests unitaires ne dépendent pas de l'interface graphique :

```bash
python3 -m unittest discover -s tests
```

Ils couvrent les règles du jeu de la vie, le score, l'initialisation du solveur, les graines locales, le nettoyage, la relance anti-stagnation, les recommandations, les essais automatiques de `steps`, la génération des PNG pédagogiques, l'architecture des modules et l'arrêt sur solution exacte.

## Supports pédagogiques

- `ALGORITHM.md` : explication complète, pseudo-code français et analyse de complexité.
- `ORAL_PRESENTATION.md` : script d'oral d'environ 10 minutes.
- `assets/gol_visuals/` : visuels PNG générés par `python3 grid_visuals.py`.

## Archive

Les fichiers secondaires ont été sortis de la racine pour garder le projet lisible :

- `archive/tools/solution_cleaner.py` : nettoyeur conservateur de solution.
- `archive/tools/random_bruteforce_reference.py` : ancienne référence par force brute aléatoire.
- `archive/presentation_video/` : ancien support vidéo Manim.
- `archive/project_instructions.md` et `archive/pattern-hunter.py` : traces de versions précédentes.
