# Conway's Reverse Game of Life

Application Tkinter/Eniseboard pour dessiner une cible du Jeu de la vie et
chercher une grille de départ qui peut la produire après quelques passages.

## Lancer
    
```bash
python3.10 lancer.py
```

## Eniseboard

Utiliser Python 3.10 pour éviter les soucis de compatibilité avec Eniseboard.

Installation conseillée :

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install eniseboard
```

Puis lancer avec :

```bash
python lancer.py
```

## Fichiers

- `lancer.py` : lance l'application.
- `interface_application.py` : interface graphique.
- `etat_application.py` : état partagé de l'application.
- `regles_jeudelavie.py` : règles du Jeu de la vie.
- `recherche_genetique.py` : recherche de la grille de départ.
- `théorie_algo.md` et `complexite_algo.md` : explication et complexité.
- `notes_oral.md` : notes de présentation.
