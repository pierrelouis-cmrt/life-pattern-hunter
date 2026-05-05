# Rapport court - Chasseur genetique creatif

## Objectif

`pattern-hunter.py` est une application graphique Eniseboard qui explore automatiquement le jeu de la vie de Conway. L'utilisateur peut dessiner un motif, le simuler, le classifier, puis lancer un algorithme genetique. La version avancee ne cherche pas seulement a converger vers un bloc, un blinker ou un planeur : elle tente de decouvrir une archive de motifs varies et inhabituels.

## Inspiration

Le programme s'inspire de trois idees existantes. D'abord, les recherches de "soups" comme apgsearch generent beaucoup de petites grilles aleatoires puis recensent les objets interessants obtenus apres evolution. Ensuite, des travaux sur les conditions initiales interessantes du Game of Life utilisent des algorithmes genetiques pour maximiser l'apparition de planeurs, R-pentominoes ou explosions controlees. Enfin, les algorithmes Novelty Search et Quality-Diversity ne gardent pas seulement le meilleur individu global : ils recompensent la difference de comportement et conservent des elites dans plusieurs niches.

## Classification et comportement

Chaque grille candidate est simulee pendant `T` generations. A chaque generation, les cellules vivantes sont normalisees dans leur boite englobante. Cela permet de reconnaitre les vies stables, oscillateurs, planeurs, vaisseaux, stabilisations, disparitions, explosions et methuselahs. Les repetitions sont detectees avec un dictionnaire de fingerprints normalises, ce qui evite de comparer toutes les paires de generations.

Le classifieur produit aussi un `BehaviorVector` compose de metriques numeriques : type de motif, periode, deplacement, duree de vie, population maximale, population finale, aire, croissance, mobilite, symetrie, nombre d'objets de cendre et evenements proches d'un planeur. Ce vecteur sert a mesurer la nouveaute et a placer le motif dans une niche de l'archive.

## Algorithme genetique Quality-Diversity

La population initiale melange plusieurs generateurs : bruit uniforme, bruit gaussien, soupes symetriques, clusters, lignes brisees, anneaux et compositions de fragments connus. A chaque generation genetique :

1. une evaluation rapide simule toute la population pendant peu de generations ;
2. seuls les meilleurs candidats recoivent une evaluation complete ;
3. ils sont evalues par qualite, nouveaute, rarete et esthetique ;
4. chaque candidat complet est insere dans une niche de l'archive s'il est nouveau ou meilleur que l'elite existante ;
5. les parents sont choisis a la fois dans la population courante et dans l'archive ;
6. les enfants sont produits par croisements uniforme, rectangulaire, bande, masque organique ou fragments ;
7. des mutations structurelles traduisent, dupliquent, refletent, tournent, erodent, densifient ou perturbent localement les motifs ;
8. en cas de stagnation, davantage de soupes aleatoires sont injectees sans vider l'archive.

Les modes `Exploration`, `Soup Hunter`, `Methuselah Lab`, `Emitter / Ash` et `Weird Stable` changent la ponderation du score. Le mode `Spaceship` est traite comme "vaisseau non-planeur" : le glider est garde dans son propre mode et devient une mauvaise solution pour `Spaceship`.

## Complexite

Soit `N` le nombre de cellules (`24 * 24 = 576`), `A` le nombre de cellules de la region active, `Tf` le nombre de generations rapides, `T` le nombre de generations completes, `P` la taille de population, `K` le nombre de candidats completement evalues, `G` le nombre de generations genetiques, `L` les essais d'amelioration locale, `B` le nombre de comportements archives et `k` le nombre de voisins utilises pour la nouveaute.

Une simulation classique coute `O(T * N)`. Ici, la region active donne plutot `O(T * A)` dans les cas compacts, avec `A <= N`. La classification par dictionnaire de fingerprints est lineaire dans l'historique, soit environ `O(T * N)` pour construire les fingerprints. La nouveaute k-plus-proches-voisins coute `O(B log B)` par candidat avec l'implementation simple par tri.

Le cout total d'une recherche est donc approximativement :

```text
O(G * (P * Tf * A + (K + L) * (T * A + B log B)))
```

La memoire principale stocke la population, le cache de simulations, l'historique courant et l'archive :

```text
O(P * N + C * N + T * N + B)
```

Ce compromis reste volontairement lisible pour un projet ENISE, sans dependance externe ni HashLife complet.
