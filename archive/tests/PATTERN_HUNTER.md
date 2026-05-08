# Rapport court - Chasseur génétique créatif

## Objectif

`pattern-hunter.py` est une application graphique Eniseboard qui explore automatiquement le jeu de la vie de Conway. L'utilisateur peut dessiner un motif, le simuler, le classifier, puis lancer un algorithme génétique. La version avancée ne cherche pas seulement à converger vers un bloc, un blinker ou un planeur : elle tente de découvrir une archive de motifs variés et inhabituels.

## Inspiration

Le programme s'inspire de trois idées existantes. D'abord, les recherches de "soups" comme apgsearch génèrent beaucoup de petites grilles aléatoires puis recensent les objets intéressants obtenus après évolution. Ensuite, des travaux sur les conditions initiales intéressantes du Game of Life utilisent des algorithmes génétiques pour maximiser l'apparition de planeurs, R-pentominoes ou explosions contrôlées. Enfin, les algorithmes Novelty Search et Quality-Diversity ne gardent pas seulement le meilleur individu global : ils récompensent la différence de comportement et conservent des élites dans plusieurs niches.

## Classification et comportement

Chaque grille candidate est simulée pendant `T` générations. À chaque génération, les cellules vivantes sont normalisées dans leur boîte englobante. Cela permet de reconnaître les vies stables, oscillateurs, planeurs, vaisseaux, stabilisations, disparitions, explosions et methuselahs. Les répétitions sont détectées avec un dictionnaire de fingerprints normalisés, ce qui évite de comparer toutes les paires de générations.

Le classifieur produit aussi un `BehaviorVector` composé de métriques numériques : type de motif, période, déplacement, durée de vie, population maximale, population finale, aire, croissance, mobilité, symétrie, nombre d'objets de cendre et événements proches d'un planeur. Ce vecteur sert à mesurer la nouveauté et à placer le motif dans une niche de l'archive.

## Algorithme génétique Quality-Diversity

La population initiale mélange plusieurs générateurs : bruit uniforme, bruit gaussien, soupes symétriques, clusters, lignes brisées, anneaux et compositions de fragments connus. À chaque génération génétique :

1. une évaluation rapide simule toute la population pendant peu de générations ;
2. seuls les meilleurs candidats reçoivent une évaluation complète ;
3. ils sont évalués par qualité, nouveauté, rareté et esthétique ;
4. chaque candidat complet est inséré dans une niche de l'archive s'il est nouveau ou meilleur que l'élite existante ;
5. les parents sont choisis à la fois dans la population courante et dans l'archive ;
6. les enfants sont produits par croisements uniforme, rectangulaire, bande, masque organique ou fragments ;
7. des mutations structurelles traduisent, dupliquent, reflètent, tournent, érodent, densifient ou perturbent localement les motifs ;
8. en cas de stagnation, davantage de soupes aléatoires sont injectées sans vider l'archive.

Les modes `Exploration`, `Soup Hunter`, `Methuselah Lab`, `Emitter / Ash` et `Weird Stable` changent la pondération du score. Le mode `Spaceship` est traité comme "vaisseau non-planeur" : le glider est gardé dans son propre mode et devient une mauvaise solution pour `Spaceship`.

## Complexité

Soit `N` le nombre de cellules (`24 * 24 = 576`), `A` le nombre de cellules de la région active, `Tf` le nombre de générations rapides, `T` le nombre de générations complètes, `P` la taille de population, `K` le nombre de candidats complètement évalués, `G` le nombre de générations génétiques, `L` les essais d'amélioration locale, `B` le nombre de comportements archivés et `k` le nombre de voisins utilisés pour la nouveauté.

Une simulation classique coûte `O(T * N)`. Ici, la région active donne plutôt `O(T * A)` dans les cas compacts, avec `A <= N`. La classification par dictionnaire de fingerprints est linéaire dans l'historique, soit environ `O(T * N)` pour construire les fingerprints. La nouveauté k-plus-proches-voisins coûte `O(B log B)` par candidat avec l'implémentation simple par tri.

Le coût total d'une recherche est donc approximativement :

```text
O(G * (P * Tf * A + (K + L) * (T * A + B log B)))
```

La mémoire principale stocke la population, le cache de simulations, l'historique courant et l'archive :

```text
O(P * N + C * N + T * N + B)
```

Ce compromis reste volontairement lisible pour un projet ENISE, sans dépendance externe ni HashLife complet.
