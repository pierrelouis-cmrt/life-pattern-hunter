| Site:  | [Ecole Nationale d'Ingénieurs de Saint-Etienne](https://pedagogie-ste.ec-lyon.fr/) |
| ------ | ---------------------------------------------------------------------------------- |
| Cours: | 25_P_CAPECL_S04_INFORMATIQUE Informatique 4                                        |
| Livre: | Sujet Projet: Algorithmie avec le module Eniseboard                                |

## 1\. Présentation du projet

**Objectif**: développer une application graphique avec le module Eniseboard, mettant en œuvre un algorithme complexe. Cet algorithme sera expliqué et sa complexité analysée.

**Le module Eniseboard**, créé par les enseignants en informatique de l'ENISE, permet de programmer facilement une interface graphique pour un jeu ou une application se déroulant sur une grille. Sa documentation est disponible sur [https://enise-info.gitlab.io/eniseboard/](https://enise-info.gitlab.io/eniseboard/)

**Exemple d'algorithme à mettre en œuvre:**

**\- Recherche de plus court chemin (ex. pour trouver la sortie d'un labyrinthe, aller d'un point à un autre d'une carte):** Recherche en Largeur (BFS), Recherche en Profondeur (DFS), Algorithme de Dijkstra.

\- **IA / résolution de jeu** (ex. puissance 4, sudoku, dames): algorithme Minimax, backtracking.

\- **Algorithme de remplissage (Flood Fill)**

**\- Algorithmes de construction de labyrinthes**

\***\*Quelques exemples graphiques:**  
\*\*

\*\*\*\*![RushHour](https://pedagogie-ste.ec-lyon.fr/pluginfile.php/121910/mod_book/chapter/783/rushhour.png)

---

\*\*\*\*![Labyrinthe](https://pedagogie-ste.ec-lyon.fr/pluginfile.php/121910/mod_book/chapter/783/t%C3%A9l%C3%A9chargement.png)

---

\*\*\*\*![Dames](https://pedagogie-ste.ec-lyon.fr/pluginfile.php/121910/mod_book/chapter/783/dames.png)

---

\*\*\*\*![Sudoku](https://pedagogie-ste.ec-lyon.fr/pluginfile.php/121910/mod_book/chapter/783/sudoku.png)

---

## 2\. Tutoriel Eniseboard 1

### Installation du module

Normalement, la distribution mis à disposition sur Moodle contient le module **eniseboard**.  
Si vous souhaitez l’installer sur une autre distribution de Python, il suffit de saisir dans l’interpréteur:

```
>>> pip install eniseboard
```

Puis de relancer l’interpréteur (ou de fermer et ouvrir de nouveau Pyzo)

### Découverte de la grille

**_Astuce: On n’oubliera pas d’importer le module avant de tester les exemples._**

Pour créer un plateau de jeu, il suffit simplement d’appeler la fonction `eniseboard`.

```python
from eniseboard import *

eniseboard()
```

On obtient une fenêtre d’environ 600 pixels de coté:

![Board](https://pedagogie-ste.ec-lyon.fr/pluginfile.php/121910/mod_book/chapter/785/eniseboard-defaut.png)

**Information importante:** La fonction `eniseboard` contient une boucle infinie que seule la fermeture de la fenêtre peut interrompre.

Dans le programme suivant, _qu’il faut tester_, le deuxième texte s’affiche uniquement après la fermeture du plateau.

```python
from eniseboard import *

print('Je suis avant le plateau')
eniseboard()
print('Je suis après le plateau')
```

Pour la suite, on retiendra que l’appel à la fonction `eniseboard` **doit être la dernière instruction du programme**.

### Arguments facultatifs

La fonction `eniseboard` semble ne pas avoir d’arguments alors qu’elle en a **plus d’une vingtaine**.  
Ces arguments sont tous _facultatifs_. Cela signifie qu’ils ont tous une valeur par défaut, utilisée lorsque la valeur n’est pas précisée lors de l’appel.

L’exemple suivant permet de faire afficher la grille séparant les cellules du plateau.

```python
from eniseboard import *

eniseboard(grid=True)
```

![Grid](https://pedagogie-ste.ec-lyon.fr/pluginfile.php/121910/mod_book/chapter/785/eniseboard-grid.png)

Il est aussi possible de changer la couleur de fond en utilisant la notation [RGB](https://www.w3schools.com/colors/colors_picker.asp)

```python
from eniseboard import *

eniseboard(grid=True, bgcolor='#96172E')
```

![Grid color](https://pedagogie-ste.ec-lyon.fr/pluginfile.php/121910/mod_book/chapter/785/eniseboard-grid-color.png)

On remarque que contrairement à ce que l’on a vu jusqu’à présent, il est nécessaire de **nommer les arguments** lors de l’appel de la fonction `eniseboard`.

## 3\. Tutoriel Eniseboard 2

Le module **eniseboard** permet de faire de la **programmation événementielle**, c’est-à-dire de lancer des actions en réaction à des événements provoqués par l’utilisateur.  
Le module permet de réagir à 5 types d’évènements, listés sur la page [https://enise-info.gitlab.io/eniseboard/evenements/evenementsemis/](https://enise-info.gitlab.io/eniseboard/evenements/evenementsemis/).  
Dans la suite de ce tutoriel, nous allons nous intéresser à deux types d’évènements particuliers: **la souris et le clavier**.

## 1\. Action au clic souris

La fonction `eniseboard` admet un argument, nommé **click**, permettant de préciser au plateau _la fonction_ qui doit être appelée lorsque l’utilisateur manipule **la souris** à l’intérieur de la fenêtre graphique.

Par exemple, le code suivant:

```python
from eniseboard import *

eniseboard(click=gestionSouris)
```

indique au plateau qu’il doit appeler la fonction nommée `gestionSouris` dans le cas où l’utilisateur manipule la souris.  
Ce code ne fonctionne pas en l’état car _aucune fonction de ce nom n’a été définie_.  
On peut tenter de remédier à ce problème en modifiant notre programme dans ce sens.

```python
from eniseboard import *

def gestionSouris():
    print("Je gère la souris !")

eniseboard(click=gestionSouris)
```

mais ce code ne fonctionne pas non plus. On obtient l’erreur suivante:

**TypeError: gestionSouris() takes 0 positional arguments but 2 were given**

Ce qui se traduit par _La fonction gestionSouris ne prend aucun argument alors qu’elle a été appelée avec 2 arguments_

En effet, lorsque qu’un évènement de type souris survient, le plateau appelle alors la fonction `gestionSouris` avec deux arguments:

- le premier argument correspond au plateau lui-même, que l’on nommera dans la suite de ce tutoriel `board` (mais que l’on peut aussi appelé `plateau`, `riviere`, `lune`, …)
- le deuxième correspond à l’évènement à l’origine de l’appel, que l’on nommera dans la suite de ce tutoriel `event` (mais que l’on peut aussi appelé `evt`, `table`, `parfum`, …)

Corrigeons notre programme.

```python
from eniseboard import *

def gestionSouris(board, event):
    print("Je gère la souris !")

eniseboard(click=gestionSouris)
```

Pour l’instant, le code de la fonction `gestionSouris` n’utilise aucun des deux arguments que le plateau lui fournit lors de l’appel. Changeons cela.

La variable `event` est un dictionnaire ([pour en savoir plus](https://enise-info.gitlab.io/python/Syntaxe/les%20types%20de%20variables/#les-dictionnaires)) et contient, en autre chose, les coordonnées de la case où l’utilisateur a cliqué.  
le numéro de ligne est donnée par `event['row']` et le numéro de la colonne par `event['col']`.

Testez le programme suivant pour comprendre le mécanisme. (Pour l’occasion, on fait afficher la grille)

```python
from eniseboard import *

def gestionSouris(board, event):
    print("vous avez cliqué sur la case en ligne",event['row'],"et colonne",event['col'])

eniseboard(grid=True, click=gestionSouris)
```

Sur cette page, vous trouverez l’ensemble des informations contenues dans `event`: [https://enise-info.gitlab.io/eniseboard/evenements/dicoevent/](https://enise-info.gitlab.io/eniseboard/evenements/dicoevent/)

La variable `board`, quant à elle, permet de manipuler le plateau de jeu.  
Par exemple, l’instruction `board.setBgColor(2, 3, 'blue')` colorie en bleu le fond de la case de coordonnées (2,3)  
_(Il est aussi possible d’utiliser une couleur définie par son code [RGB](https://www.w3schools.com/colors/colors_picker.asp))_

On peut utiliser cette fonction pour colorier la case sur laquelle l’utilisateur a cliqué.

```python
from eniseboard import *

def gestionSouris(board, event):
    board.setBgColor(event['row'], event['col'], 'blue')

eniseboard(grid=True, click=gestionSouris)
```

![Clic blue](https://pedagogie-ste.ec-lyon.fr/pluginfile.php/121910/mod_book/chapter/784/eniseboard-clic-color.png)

Sur cette page, vous trouverez l’ensemble des fonctions de manipulation du plateau: [https://enise-info.gitlab.io/eniseboard/plateaudejeu/manipplateau/](https://enise-info.gitlab.io/eniseboard/plateaudejeu/manipplateau/)

## 2\. Action à l’appui d’une touche du clavier

Sur le même principe, la fonction `eniseboard` admet un argument, nommé **key**, permettant de préciser au plateau _la fonction_ qui doit être appelée lorsque l’utilisateur appuie sur **le clavier** à l’intérieur de la fenêtre graphique.

Testez le code suivant:

```python
from eniseboard import *

def gestionClavier(board, event):
    lettre = event['keysym']
    board.console("Vous avez appuyé sur la touche", lettre)

eniseboard(grid=True, console=True, key=gestionClavier)
```

On rappelle que sur cette page, vous trouverez l’ensemble des informations contenues dans `event`:  
[https://enise-info.gitlab.io/eniseboard/evenements/dicoevent/](https://enise-info.gitlab.io/eniseboard/evenements/dicoevent/)

## 4\. Consignes

## Vous devez réaliser seul ou en binôme, un programme:

1. utilisant le module **eniseboard** pour l'interface graphique;
2. interagissant à l'aide du clavier et de la souris;
3. mettant en oeuvre un **algorithme complexe**

Le code commenté sera à rendre accompagné d’un **rapport d'une page décrivant l'algorithme mis en oeuvre associé à une étude de sa complexité**, au plus tard le **dimanche 1er Juin 2025 à 23h59**

---

---

Le code commenté est à rendre accompagné d’un rapport d'une page décrivant l'algorithme mis en œuvre associé à une étude de sa complexité, au plus tard le mardi 19 mai 2026 23h59.
