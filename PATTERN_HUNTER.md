# Rapport court - Chasseur genetique creatif

## Objectif

`pattern-hunter.py` est une application graphique Eniseboard qui explore automatiquement le jeu de la vie de Conway. L'utilisateur peut dessiner un motif, le simuler, le classifier, puis lancer un algorithme genetique. La version avancee ne cherche pas seulement a converger vers un bloc, un blinker ou un planeur : elle tente de decouvrir une archive de motifs varies et inhabituels.

## Inspiration

Le programme s'inspire de trois idees existantes. D'abord, les recherches de "soups" comme apgsearch generent beaucoup de petites grilles aleatoires puis recensent les objets interessants obtenus apres evolution. Ensuite, des travaux sur les conditions initiales interessantes du Game of Life utilisent des algorithmes genetiques pour maximiser l'apparition de planeurs, R-pentominoes ou explosions controlees. Enfin, les algorithmes Novelty Search et Quality-Diversity ne gardent pas seulement le meilleur individu global : ils recompensent la difference de comportement et conservent des elites dans plusieurs niches.

## Classification et comportement

Chaque grille candidate est simulee pendant `T` generations. A chaque generation, les cellules vivantes sont normalisees dans leur boite englobante. Cela permet de reconnaitre les vies stables, oscillateurs, planeurs, vaisseaux, stabilisations, disparitions, explosions et methuselahs.

Le classifieur produit aussi un `BehaviorVector` compose de metriques numeriques : type de motif, periode, deplacement, duree de vie, population maximale, population finale, aire, croissance, mobilite, symetrie, nombre d'objets de cendre et evenements proches d'un planeur. Ce vecteur sert a mesurer la nouveaute et a placer le motif dans une niche de l'archive.

## Algorithme genetique Quality-Diversity

La population initiale melange plusieurs generateurs : bruit uniforme, bruit gaussien, soupes symetriques, clusters, lignes brisees, anneaux et compositions de fragments connus. A chaque generation genetique :

1. les candidats sont simules avec une region active autour de la boite vivante ;
2. ils sont evalues par qualite, nouveaute, rarete et esthetique ;
3. chaque candidat est insere dans une niche de l'archive s'il est nouveau ou meilleur que l'elite existante ;
4. les parents sont choisis a la fois dans la population courante et dans l'archive ;
5. les enfants sont produits par croisements uniforme, rectangulaire, bande, masque organique ou fragments ;
6. des mutations structurelles traduisent, dupliquent, refletent, tournent, erodent, densifient ou perturbent localement les motifs ;
7. en cas de stagnation, davantage de soupes aleatoires sont injectees sans vider l'archive.

Les modes `Exploration`, `Soup Hunter`, `Methuselah Lab`, `Emitter / Ash` et `Weird Stable` changent la ponderation du score. Les anciens modes cibles restent disponibles.

## Complexite

Soit `N` le nombre de cellules (`24 * 24 = 576`), `A` le nombre de cellules de la region active, `T` le nombre de generations simulees, `P` la taille de population, `G` le nombre de generations genetiques, `L` les essais d'amelioration locale, `B` le nombre de comportements archives et `k` le nombre de voisins utilises pour la nouveaute.

Une simulation classique coute `O(T * N)`. Ici, la region active donne plutot `O(T * A)` dans les cas compacts, avec `A <= N`. La classification compare les fingerprints rencontres, donc son pire cas reste `O(T^2 * N)`, mais les grilles sont petites. La nouveaute k-plus-proches-voisins coute `O(B log B)` par candidat avec l'implementation simple par tri.

Le cout total d'une recherche est donc approximativement :

```text
O(G * (P + L) * (T * A + T^2 * N + B log B))
```

La memoire principale stocke la population, le cache de simulations, l'historique courant et l'archive :

```text
O(P * N + C * N + T * N + B)
```

Ce compromis reste volontairement lisible pour un projet ENISE, sans dependance externe ni HashLife complet.
