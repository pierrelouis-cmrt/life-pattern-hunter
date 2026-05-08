import random
import unittest

from life_rules import nouvelle_grille
from reverse_search_algorithm import (
    SearchConfig,
    avancer_solveur_une_generation,
    calculer_zone_recherche,
    construire_carte_distance_cible,
    erreur_par_rapport_a_cible,
    evaluer_population,
    initialiser_solveur,
    score_exactitude,
)


def grille_depuis_cellules(cellules, rows=5, cols=5):
    grille = nouvelle_grille(0, rows, cols)
    for ligne, col in cellules:
        grille[ligne][col] = 1
    return grille


class ReverseSearchAlgorithmTests(unittest.TestCase):
    def small_config(self):
        return SearchConfig(
            rows=5,
            cols=5,
            taille_population=18,
            nb_elites=4,
            nb_generations_max=5,
            nb_essais_amelioration_locale=3,
            taille_cache_max=100,
        )

    def test_score_counts_missing_and_extra_cells(self):
        config = SearchConfig(rows=3, cols=3)
        cible = grille_depuis_cellules([(1, 1)], rows=3, cols=3)
        resultat_vide = nouvelle_grille(0, 3, 3)
        resultat_extra = grille_depuis_cellules([(0, 0), (1, 1)], rows=3, cols=3)
        carte = construire_carte_distance_cible(cible, config)

        self.assertEqual(4, erreur_par_rapport_a_cible(resultat_vide, cible, carte, config))
        self.assertAlmostEqual(1.12, erreur_par_rapport_a_cible(resultat_extra, cible, carte, config))
        self.assertAlmostEqual(100.0, score_exactitude(cible, cible, config))

    def test_population_evaluation_is_sorted(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(1, 1), (1, 2), (2, 1), (2, 2)])
        carte = construire_carte_distance_cible(cible, config)
        population = [nouvelle_grille(0, 5, 5), cible]
        roles = ["vide", "block"]

        evaluated = evaluer_population(population, roles, cible, 1, {}, carte, config)

        self.assertEqual(0, evaluated[0].erreur)
        self.assertLessEqual(evaluated[0].score_tri, evaluated[1].score_tri)

    def test_solver_keeps_population_size_and_exposes_snapshot(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(1, 1), (1, 2), (2, 1), (2, 2)])
        rng = random.Random(123)
        solveur = initialiser_solveur(cible, cible, 1, config, rng)

        avancer_solveur_une_generation(solveur)

        self.assertEqual(config.taille_population, len(solveur.population))
        self.assertIsNotNone(solveur.dernier_snapshot)
        self.assertEqual(config.taille_population, len(solveur.dernier_snapshot.population_evaluee))

    def test_solver_stops_on_exact_solution(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(1, 1), (1, 2), (2, 1), (2, 2)])
        solveur = initialiser_solveur(cible, cible, 1, config, random.Random(1))

        avancer_solveur_une_generation(solveur)

        self.assertTrue(solveur.termine)
        self.assertEqual("solution exacte", solveur.raison_arret)
        self.assertEqual(0, solveur.meilleure_erreur)

    def test_search_zone_wraps_target_with_margin(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(2, 2)])

        self.assertEqual((0, 4, 0, 4), calculer_zone_recherche(cible, 2, config))


if __name__ == "__main__":
    unittest.main()
