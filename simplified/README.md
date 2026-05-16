# Chasseur de motifs simplifié

Ce dossier contient une version autonome du projet, prévue pour étudier une
recherche inverse plus simple que le projet principal, mais moins naïve que le
premier algorithme barebones.

## Lancement

Depuis la racine du dépôt :

```bash
python3 simplified/main.py
```

Si Eniseboard n'est pas installé :

```bash
pip install eniseboard
```

## Fichiers

- `main.py` : point d'entrée de l'application simplifiée.
- `ui_app.py` : interface Tkinter/Eniseboard adaptée à un seul essai de recherche.
- `app_state.py` : état partagé de cette version.
- `life_rules.py` : règles normales du Jeu de la vie, copiées pour garder le dossier autonome.
- `simple_genetic_algorithm.py` : algorithme génétique barebones.
- `ALGORITHME_SIMPLIFIE.md` : description complète du fonctionnement.
- `COMPLEXITE_ALGORITHME_SIMPLIFIE.md` : calcul de complexité.
- `tests/` : tests unitaires propres à cette version.

## Différence avec le projet principal

Le projet principal contient plusieurs aides pratiques : zone de recherche
autour de la cible, graines locales, cache, amélioration locale, nettoyage,
relances et essais automatiques de plusieurs valeurs de passages.

Cette version retire volontairement les aides les plus lourdes. Elle garde les
éléments qui ont le meilleur rendement pratique :

1. zone de recherche autour de la cible dessinée ;
2. score pondéré qui punit plus fortement les cellules cibles manquantes ;
3. population initiale aléatoire dans la zone active ;
4. sélection des élites ;
5. croisement uniforme entre élites ;
6. mutation simple, plus forte quand la recherche stagne ;
7. quelques nouveaux individus aléatoires à chaque génération.

Elle ne contient toujours pas :

1. cache ;
2. graines locales pour petites formes ;
3. amélioration locale ;
4. nettoyage final ;
5. essai automatique de plusieurs valeurs de passages ;
6. relances complexes.

Le but n'est pas d'être le meilleur solveur possible, mais d'obtenir une base
simple à expliquer, tester et comparer, tout en évitant la stagnation trop
rapide de la version entièrement aléatoire.

## Tests

```bash
python3 -m unittest discover -s simplified/tests
```
