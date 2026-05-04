# Life Pattern Hunter

Application Eniseboard pour explorer automatiquement des motifs inhabituels du jeu de la vie de Conway avec un algorithme genetique creatif.

Le programme principal est `pattern-hunter.py`. Il ne cherche plus seulement "le meilleur" motif d'une famille : il maintient une archive Quality-Diversity de decouvertes differentes, afin de favoriser des formes originales, mobiles, longues, instables ou visuellement surprenantes.

## Lancer

```bash
pip install eniseboard
python3 pattern-hunter.py
```

Les tests n'ont pas besoin d'Eniseboard :

```bash
python3 -m unittest discover -s tests -v
```

## Controles

- Clic gauche : inverse une cellule.
- Clic droit : efface une cellule.
- `S` : lancer ou arreter l'exploration.
- `D` : lancer un deep run en mode Exploration avec plus de generations analysees.
- `Espace` : lire ou mettre en pause l'evolution.
- `N` : avancer d'une generation.
- `C` : classifier le motif courant.
- `R` : generer un motif aleatoire creatif.
- `E` : exporter le motif courant en console.
- `A` : afficher la meilleure decouverte de l'archive.
- `X` : effacer.
- `1` a `9`, puis `0` et `-` : changer de mode de recherche.

La zone beige est la zone ou l'algorithme genetique fabrique les candidats.

## Modes

- `Exploration` : mode par defaut, maximise nouveaute, diversite temporelle, mobilite et activite controlee.
- `Soup Hunter` : genere des soups aleatoires inspirees d'apgsearch et recompense les cendres variees.
- `Methuselah Lab` : cherche de petits motifs qui restent actifs longtemps.
- `Emitter / Ash` : favorise les fragments mobiles, evenements de type planeur et objets multiples.
- `Weird Stable` : cherche des stabilisations grandes, asymetriques ou composites.
- `Still life`, `Oscillator`, `Glider`, `Spaceship`, `Methuselah`, `Novelty` : modes cibles conserves.

## Algorithme

Chaque candidat est simule, classifie, puis transforme en `BehaviorVector`. Ce vecteur contient la famille du motif, sa periode, sa duree de vie, sa population maximale, sa diversite, son aire, sa croissance, sa mobilite, sa symetrie, ses cendres et ses evenements proches d'un planeur.

Le score final combine :

- qualite : adequation au mode choisi ;
- nouveaute : distance aux comportements deja vus ;
- rarete : bonus aux niches peu visitees ;
- esthetique : activite, mobilite, asymetrie et richesse des cendres.

La reproduction utilise des mutations structurelles : translation, duplication, miroir, rotation, erosion, densification, explosion locale et injection de fragments classiques.
