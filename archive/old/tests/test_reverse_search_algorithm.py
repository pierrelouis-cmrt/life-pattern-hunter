import random
import unittest

from life_rules import nombre_cellules_vivantes, nouvelle_grille, simuler
from reverse_search_algorithm import (
    SearchConfig,
    avancer_solveur_une_generation,
    calculer_zone_recherche,
    construire_carte_distance_cible,
    creer_graines_locales_cible,
    erreur_par_rapport_a_cible,
    evaluer_population,
    initialiser_solveur,
    nettoyer_solution_initiale,
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

    def test_local_seeds_find_sparse_blinker_ancestor(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(2, 1), (2, 2), (2, 3)])
        zone = calculer_zone_recherche(cible, 1, config)
        carte = construire_carte_distance_cible(cible, config)

        graines = creer_graines_locales_cible(cible, 1, zone, carte, config)

        self.assertTrue(any(simuler(graine, 1) == cible for graine in graines))

    def test_solver_solves_sparse_blinker_from_local_seed(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(2, 1), (2, 2), (2, 3)])
        solveur = initialiser_solveur(nouvelle_grille(0, 5, 5), cible, 1, config, random.Random(7))

        avancer_solveur_une_generation(solveur)

        self.assertTrue(solveur.termine)
        self.assertEqual("solution exacte", solveur.raison_arret)
        self.assertEqual(0, solveur.meilleure_erreur)
        self.assertEqual(3, nombre_cellules_vivantes(solveur.meilleur_individu))

    def test_cleaner_removes_isolated_noise_when_result_stays_exact(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(2, 1), (2, 2), (2, 3)])
        initiale = grille_depuis_cellules([(1, 2), (2, 2), (3, 2), (4, 4)])
        carte = construire_carte_distance_cible(cible, config)

        nettoyee = nettoyer_solution_initiale(initiale, cible, 1, config, carte, {})

        self.assertEqual(0, nettoyee.erreur)
        self.assertEqual(3, nombre_cellules_vivantes(nettoyee.individu))
        self.assertEqual(cible, nettoyee.resultat)

    def test_cleaner_keeps_useful_cells(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(2, 1), (2, 2), (2, 3)])
        initiale = grille_depuis_cellules([(1, 2), (2, 2), (3, 2)])
        carte = construire_carte_distance_cible(cible, config)

        nettoyee = nettoyer_solution_initiale(initiale, cible, 1, config, carte, {})

        self.assertEqual(0, nettoyee.erreur)
        self.assertEqual(3, nombre_cellules_vivantes(nettoyee.individu))

    def test_solver_stores_clean_exact_solution(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(2, 1), (2, 2), (2, 3)])
        initiale = grille_depuis_cellules([(1, 2), (2, 2), (3, 2), (4, 4)])
        solveur = initialiser_solveur(initiale, cible, 1, config, random.Random(1))

        avancer_solveur_une_generation(solveur)

        self.assertTrue(solveur.termine)
        self.assertEqual(0, solveur.meilleure_erreur)
        self.assertEqual(3, nombre_cellules_vivantes(solveur.meilleur_individu))

    def test_local_seeds_still_work_with_large_sparse_blinker_steps(self):
        config = self.small_config()
        cible = grille_depuis_cellules([(2, 1), (2, 2), (2, 3)])
        zone = calculer_zone_recherche(cible, 9, config)
        carte = construire_carte_distance_cible(cible, config)

        graines = creer_graines_locales_cible(cible, 9, zone, carte, config)

        self.assertTrue(any(simuler(graine, 9) == cible for graine in graines))

    def test_stagnation_restart_keeps_population_size_and_tags_roles(self):
        config = SearchConfig(
            rows=6,
            cols=6,
            taille_population=24,
            nb_elites=4,
            nb_generations_max=10,
            nb_essais_amelioration_locale=2,
            taille_cache_max=100,
            seuil_cible_clairesemee=0,
            seuil_relance_stagnation=1,
            intervalle_relance_stagnation=1,
            fraction_relance_stagnation=0.50,
        )
        cible = grille_depuis_cellules([(3, 3)], rows=6, cols=6)
        vide = nouvelle_grille(0, 6, 6)
        solveur = initialiser_solveur(vide, cible, 1, config, random.Random(4))
        solveur.population = [nouvelle_grille(0, 6, 6) for _ in range(config.taille_population)]
        solveur.roles_population = ["vide force"] * config.taille_population
        solveur.meilleure_note_tri = -1
        solveur.meilleure_erreur = 999
        solveur.meilleur_individu = vide
        solveur.meilleur_resultat = vide

        avancer_solveur_une_generation(solveur)

        self.assertEqual(config.taille_population, len(solveur.population))
        self.assertIn("relance stagnation", solveur.roles_population)


if __name__ == "__main__":
    unittest.main()
