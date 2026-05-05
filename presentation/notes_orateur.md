# Notes orateur - Life Pattern Hunter

Presentation prevue pour environ 10 minutes. Les slides sont volontairement legeres : l'idee est de parler autour des schemas, pas de lire le deck.

## Slide 1 - Titre

Dire que le projet part du jeu de la vie de Conway, mais qu'on ne se contente pas de le simuler. Notre objectif est inverse : l'utilisateur dessine un motif final, choisit un nombre d'etapes `X`, et le programme cherche une grille initiale qui, apres `X` generations, ressemble le plus possible a cette cible.

Insister sur la difference entre "faire evoluer une grille" et "retrouver une origine probable". Le premier est direct, le second est un probleme de recherche.

## Slide 2 - Le jeu de la vie en 30 secondes

Presenter la grille comme un automate cellulaire : chaque case est morte ou vivante, et toute la grille est mise a jour en meme temps.

Les regles classiques sont `B3/S23` :

- une cellule morte nait si elle a exactement 3 voisines vivantes ;
- une cellule vivante survit si elle a 2 ou 3 voisines vivantes ;
- dans tous les autres cas, elle meurt ou reste morte.

Dire que ces regles simples creent des comportements riches : vies stables, oscillateurs, planeurs, disparitions, explosions.

## Slide 3 - Pourquoi notre probleme est difficile

Expliquer que les regles sont faciles a appliquer vers le futur, mais pas faciles a inverser. Une meme grille finale peut avoir plusieurs parents, aucun parent, ou des parents tres differents.

La grille fait `24 x 24`, donc `576` cellules. Comme chaque cellule vaut 0 ou 1, une recherche exhaustive testerait `2^576` grilles initiales. C'est impossible en pratique.

Conclusion orale : on ne peut pas garantir l'optimum exact ; on cherche une tres bonne solution avec un budget de calcul raisonnable.

## Slide 4 - Idee generale de l'algorithme genetique

Presenter chaque individu comme une grille initiale candidate. Le programme garde une population de candidats.

Pour evaluer un candidat, on ne remonte pas les regles : on le simule normalement pendant `X` generations, puis on compare le resultat a la cible.

Ensuite, comme en selection naturelle :

- les meilleurs candidats sont conserves ;
- des parents sont choisis ;
- ils produisent des enfants par croisement ;
- les enfants sont modifies par mutation ;
- quelques candidats aleatoires sont reinjectes pour eviter que toute la population se ressemble.

## Slide 5 - Le score

Le score est une erreur : plus il est bas, meilleur est le candidat.

Le programme distingue deux erreurs :

- faux negatif : une cellule devrait etre vivante dans la cible, mais elle est morte dans le resultat ;
- faux positif : une cellule est vivante dans le resultat, mais elle ne devrait pas l'etre.

Les faux negatifs coutent plus cher : `4` contre `1`. Cela evite que l'algorithme prefere des grilles presque vides. Les cellules en trop loin de la cible recoivent aussi une petite penalite supplementaire avec la carte de distance.

Enfin, si deux candidats ont presque le meme resultat, on prefere legerement la grille initiale la plus simple avec `0.001` par cellule vivante.

## Slide 6 - Pseudo-code

Presenter le pseudo-code comme la boucle centrale :

```text
zone <- rectangle autour de la cible
population <- candidats varies

pour generation de 1 a G :
    evaluer chaque candidat :
        resultat <- simuler(candidat, X)
        score <- erreur(resultat, cible)

    ameliorer localement le meilleur candidat
    si score == 0 : arreter

    nouvelle_population <- elites
    ajouter quelques candidats aleatoires

    tant que la population n'est pas remplie :
        parent_a <- tournoi(population)
        parent_b <- tournoi(population)
        enfant <- croisement(parent_a, parent_b)
        mutation_guidee(enfant)
        ajouter enfant

    supprimer les doublons
```

Expliquer rapidement les mots :

- elite : les meilleurs sont copies tels quels ;
- tournoi : on tire quelques candidats au hasard et on prend le meilleur ;
- croisement uniforme : chaque cellule de l'enfant vient du parent A ou B ;
- mutation guidee : pres de la cible on mute un peu plus, loin de la cible un peu moins.

## Slide 7 - Les optimisations pratiques

Dire que l'algorithme genetique de base serait deja utilisable, mais plusieurs details le rendent beaucoup plus efficace :

- zone de recherche : on ne cherche pas dans toute la grille si la cible est petite ;
- population initiale variee : cible brute, cible bruitee, densites differentes, candidats guides par la distance ;
- cache : si une grille reapparait, on reutilise sa simulation ;
- suppression des doublons : evite de gaspiller des evaluations ;
- amelioration locale : on teste quelques inversions de cellule autour du meilleur ;
- stagnation : si le score ne s'ameliore plus, on augmente mutation et injection aleatoire.

## Slide 8 - Complexite

Definir les variables :

- `N` : nombre de cellules, ici `576` ;
- `X` : nombre de generations du jeu de la vie simulees ;
- `P` : taille de population, par defaut `120` ;
- `L` : essais d'amelioration locale, par defaut `18` ;
- `G` : nombre maximal de generations genetiques, par defaut `420`.

Une generation du jeu de la vie parcourt la grille, donc une simulation coute :

```text
O(X * N)
```

Une generation genetique evalue environ `P + L` candidats :

```text
O((P + L) * X * N)
```

Sur toute la recherche :

```text
O(G * (P + L) * X * N)
```

Mentionner que le tri de population coute `O(P log P)`, mais qu'il est secondaire lorsque `X` grandit. Le cache aide en pratique, mais ne change pas le pire cas theorique.

## Slide 9 - Conclusion / demo

Conclure sur le compromis : l'algorithme n'est pas exact, mais il transforme un espace gigantesque en recherche guidee.

Comparer avec `random-bruteforce.py` : le brute force aleatoire utilise un budget comparable par iteration, mais il ne reutilise aucune information. Le genetique apprend indirectement en recomposant les bons morceaux de solutions.

Pour la demo, montrer :

1. dessin d'une cible ;
2. choix du nombre `Steps` ;
3. lancement de la recherche ;
4. affichage de la meilleure grille initiale ;
5. lecture de l'evolution jusqu'a la cible.

Phrase de fin possible : "Le point important, ce n'est pas seulement de simuler le jeu de la vie ; c'est d'utiliser la simulation comme fonction d'evaluation dans un probleme inverse."
