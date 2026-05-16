import random
import unittest

from simplified.life_rules import nouvelle_grille
from simplified.simple_genetic_algorithm import (
    SimpleSearchConfig,
    avancer_solveur_une_generation,
    calculer_zone_recherche,
    construire_population_suivante,
    evaluer_individu,
    evaluer_population,
    initialiser_solveur,
    taille_zone,
    taux_mutation_effectif,
)


def grille_depuis_cellules(cellules, rows=5, cols=5):
    grille = nouvelle_grille(0, rows, cols)
    for ligne, col in cellules:
        grille[ligne][col] = 1
    return grille


class SimpleGeneticAlgorithmTests(unittest.TestCase):
    def small_config(self):
        return SimpleSearchConfig(
            rows=5,
            cols=5,
            taille_population=8,
            nb_elites=2,
            nb_generations_max=5,
            densite_initiale=0.20,
            taux_mutation=0.05,
        )

    def test_exact_candidate_has_zero_error(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(1, 1), (1, 2), (2, 1), (2, 2)])

        evaluation = evaluer_individu(cible, cible, 1, config)

        self.assertEqual(0, evaluation.erreur)
        self.assertEqual(100.0, evaluation.exactitude)

    def test_population_evaluation_is_sorted(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(1, 1), (1, 2), (2, 1), (2, 2)])
        population = [nouvelle_grille(0, 5, 5), cible]

        evaluations = evaluer_population(population, cible, 1, config)

        self.assertEqual(0, evaluations[0].erreur)
        self.assertLessEqual(evaluations[0].erreur, evaluations[1].erreur)
        self.assertEqual("elite", evaluations[0].role)

    def test_next_population_keeps_size_and_elites(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(1, 1), (1, 2), (2, 1), (2, 2)])
        vide = nouvelle_grille(0, 5, 5)
        population = [vide, cible] + [grille_depuis_cellules([(0, index)]) for index in range(4)]
        evaluations = evaluer_population(population, cible, 1, config)

        suivante = construire_population_suivante(evaluations, config, random.Random(3))

        self.assertEqual(config.taille_population, len(suivante))
        self.assertEqual(evaluations[0].individu, suivante[0])
        self.assertEqual(evaluations[1].individu, suivante[1])

    def test_initial_population_is_limited_to_target_zone(self):
        config = SimpleSearchConfig(
            rows=7,
            cols=7,
            taille_population=6,
            nb_elites=2,
            marge_recherche=1,
            max_marge_recherche=1,
            densite_initiale=1.0,
        )
        cible = grille_depuis_cellules([(3, 3)], rows=7, cols=7)
        solveur = initialiser_solveur(nouvelle_grille(0, 7, 7), cible, 1, config, random.Random(1))

        self.assertEqual((2, 4, 2, 4), solveur.zone)
        self.assertEqual(9, taille_zone(solveur.zone))
        for individu in solveur.population:
            for ligne in range(7):
                for col in range(7):
                    if not (2 <= ligne <= 4 and 2 <= col <= 4):
                        self.assertEqual(0, individu[ligne][col])

    def test_adaptive_mutation_increases_with_stagnation(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(1, 1)])
        solveur = initialiser_solveur(nouvelle_grille(0, 5, 5), cible, 1, config, random.Random(1))

        solveur.stagnation = 0
        self.assertAlmostEqual(config.taux_mutation, taux_mutation_effectif(solveur))
        solveur.stagnation = 45
        self.assertGreater(taux_mutation_effectif(solveur), config.taux_mutation)

    def test_search_zone_grows_with_steps_but_stays_bounded(self):
        config = SimpleSearchConfig(rows=20, cols=20, marge_recherche=2, max_marge_recherche=5)
        cible = grille_depuis_cellules([(10, 10)], rows=20, cols=20)

        zone = calculer_zone_recherche(cible, 20, config)

        self.assertEqual((5, 15, 5, 15), zone)

    def test_solver_stops_on_exact_solution(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(1, 1), (1, 2), (2, 1), (2, 2)])
        solveur = initialiser_solveur(nouvelle_grille(0, 5, 5), cible, 1, config, random.Random(1))
        solveur.population = [cible] + [nouvelle_grille(0, 5, 5) for _ in range(config.taille_population - 1)]

        avancer_solveur_une_generation(solveur)

        self.assertTrue(solveur.termine)
        self.assertEqual("solution exacte", solveur.raison_arret)
        self.assertEqual(0, solveur.meilleure_erreur)

    def test_solver_stops_on_generation_limit(self):
        config = SimpleSearchConfig(
            rows=4,
            cols=4,
            taille_population=6,
            nb_elites=2,
            nb_generations_max=0,
        )
        cible = grille_depuis_cellules([(1, 1)], rows=4, cols=4)
        solveur = initialiser_solveur(nouvelle_grille(0, 4, 4), cible, 1, config, random.Random(1))
        solveur.population = [nouvelle_grille(0, 4, 4) for _ in range(config.taille_population)]

        avancer_solveur_une_generation(solveur)

        self.assertTrue(solveur.termine)
        self.assertEqual("limite de générations", solveur.raison_arret)
        self.assertEqual(4, solveur.meilleure_erreur)


if __name__ == "__main__":
    unittest.main()
