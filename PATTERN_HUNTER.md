# Rapport court - Chasseur automatique de motifs

## Objectif

Le programme `pattern-hunter.py` est une application graphique Eniseboard pour le jeu de la vie de Conway. L'utilisateur peut dessiner un motif avec la souris, le simuler au clavier, le classifier, puis lancer une recherche automatique. L'objectif de l'algorithme n'est pas de trouver une seule grille exacte, mais de decouvrir des motifs appartenant a une famille choisie : vie stable, oscillateur, planeur, vaisseau, methuselah ou nouveaute.

## Principe de classification

Chaque candidat est simule pendant `T` generations. Pour chaque generation, le programme extrait les cellules vivantes, calcule leur boite englobante et normalise le motif en coordonnees relatives. Deux generations qui possedent la meme forme normalisee representent donc le meme motif, meme si sa position absolue a change.

Cette representation permet de reconnaitre plusieurs cas :

- meme forme et meme position apres une periode `p` : vie stable si `p = 1`, oscillateur sinon ;
- meme forme mais position differente : vaisseau ; si `p = 4` et le deplacement est diagonal de 1 cellule, c'est un planeur ;
- disparition complete : motif mort ;
- repetition apres une phase transitoire : motif stabilise ;
- forte population ou activite longue sans repetition : explosion, methuselah ou motif inconnu.

Le classifieur conserve aussi des metriques utiles au score : population initiale, population maximale, population finale, duree de vie, periode, deplacement, aire maximale de la boite englobante et diversite des formes rencontrees.

## Algorithme genetique

La population contient des grilles candidates limitees a une zone centrale de la grille `24 x 24`. Elle est initialisee avec des motifs connus (bloc, blinker, planeur, r-pentomino) et des grilles aleatoires de densites variees. A chaque generation genetique :

1. chaque candidat est simule et classifie ;
2. une fonction de fitness donne un score, plus petit si le candidat ressemble a la famille recherchee ;
3. les meilleurs individus sont conserves par elitisme ;
4. de nouveaux enfants sont produits par selection par tournoi, croisement uniforme ou croisement rectangulaire ;
5. des mutations inversent aleatoirement des cellules dans la zone de recherche ;
6. quelques individus aleatoires sont injectes pour eviter la stagnation ;
7. une petite amelioration locale teste des inversions d'une cellule autour du meilleur candidat ;
8. un cache evite de resimuler deux fois la meme grille.

Un hall of fame garde plusieurs bons motifs differents. Il ajoute une pression de diversite, ce qui evite que la recherche redonne toujours le bloc, le blinker ou le planeur classique.

## Complexite

Soit `N` le nombre de cellules de la grille (`24 * 24 = 576`), `T` le nombre de generations simulees, `P` la taille de population, `G` le nombre de generations genetiques, `L` le nombre d'essais d'amelioration locale et `C` le nombre d'evaluations stockees en cache.

Une generation du jeu de la vie parcourt toutes les cellules et leurs huit voisines, donc une simulation coute `O(T * N)`. La classification compare les formes rencontrees dans l'historique ; dans le pire cas elle coute `O(T^2 * N)`, mais `T` reste petit dans l'interface. Une generation genetique evalue environ `P + L` candidats, donc le cout total est :

```text
O(G * (P + L) * (T * N + T^2 * N))
```

En pratique, le cache diminue ce cout lorsque des candidats reapparaissent. La memoire utilisee est principalement :

```text
O(P * N + T * N + C * N)
```

ce qui correspond a la population, l'historique d'un motif et les evaluations memorisees.
