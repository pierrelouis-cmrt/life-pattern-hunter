# Life Pattern Hunter

Application Eniseboard pour chercher automatiquement des motifs interessants du jeu de la vie de Conway avec un algorithme genetique.

## Lancer

```bash
pip install eniseboard
python3 pattern-hunter.py
```

Le fichier principal est `pattern-hunter.py`. Le fichier `reverse-search.py` est conserve comme experience secondaire de recherche inverse vers une cible dessinee.

## Utilisation

- Clic gauche : inverse une cellule.
- Clic droit : efface une cellule.
- `S` : lancer ou arreter la recherche genetique.
- `Espace` : lire ou mettre en pause l'evolution.
- `N` : avancer d'une generation.
- `C` : classifier le motif courant.
- `R` : remplir aleatoirement la zone de recherche.
- `X` : effacer.
- `E` : exporter le meilleur motif dans la console.
- `1` a `6` : choisir le type de motif cherche.

La zone beige est la zone dans laquelle l'algorithme genetique construit les candidats. Elle est plus grande pour les vaisseaux, les methuselahs et la recherche de nouveaute.

## Modes de recherche

- `Still life` : motif stable.
- `Oscillator` : motif qui revient sans se deplacer.
- `Glider` : planeur classique, periode 4 avec deplacement diagonal.
- `Spaceship` : motif periodique qui se deplace.
- `Methuselah` : petit motif initial qui reste actif longtemps.
- `Novelty` : motif inhabituel, diversifie et non trivial.

## Tests

Les tests n'ont pas besoin d'Eniseboard.

```bash
python3 -m unittest discover -s tests -v
```
