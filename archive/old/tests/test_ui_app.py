import unittest
from unittest.mock import patch
from types import SimpleNamespace

import ui_app
from app_state import nouvel_etat
from life_rules import COLS, ROWS, nouvelle_grille


class FakeBoard:
    def __init__(self):
        self.colors = []
        self.messages = []
        self.info = []

    def setBgColor(self, row, col, color):
        self.colors.append((row, col, color))

    def display(self, text, row=0, col=0, color=None):
        self.info.append((text, row, col, color))

    def console(self, *message):
        self.messages.append(message)


class UiAppTests(unittest.TestCase):
    def setUp(self):
        ui_app.state = nouvel_etat()

    def petite_cible(self):
        ui_app.state.cible = nouvelle_grille(0)
        for cellule in [(12, 11), (12, 12), (12, 13)]:
            ui_app.state.cible[cellule[0]][cellule[1]] = 1

    def test_grid_click_is_ignored_while_resolution_solver_runs(self):
        resultat = object()
        solveur = object()
        ui_app.state.mode_app = "resolution"
        ui_app.state.solveur_actif = True
        ui_app.state.solveur = solveur
        ui_app.state.resultat = resultat

        ui_app.gestion_souris(None, {"row": 1, "col": 1})

        self.assertEqual(0, ui_app.state.cible[1][1])
        self.assertTrue(ui_app.state.solveur_actif)
        self.assertIs(solveur, ui_app.state.solveur)
        self.assertIs(resultat, ui_app.state.resultat)

    def test_resolution_random_button_fills_final_target_and_resets_solver_state(self):
        ui_app.state.mode_app = "resolution"
        ui_app.state.vue = "resultat"
        ui_app.state.resultat = nouvelle_grille(1)
        ui_app.state.solveur = object()
        ui_app.state.solveur_actif = True
        ui_app.state.evolution = [nouvelle_grille(0)]
        ui_app.state.evolution_active = True
        ui_app.state.recommendation_steps = "old recommendation"

        random_values = [0.0 if index % 2 == 0 else 1.0 for index in range(ROWS * COLS)]
        with patch("ui_app.random.random", side_effect=random_values):
            ui_app.remplir_cible_aleatoire(FakeBoard())

        self.assertEqual(ROWS * COLS // 2, sum(sum(ligne) for ligne in ui_app.state.cible))
        self.assertIsNone(ui_app.state.resultat)
        self.assertIsNone(ui_app.state.solveur)
        self.assertFalse(ui_app.state.solveur_actif)
        self.assertIsNone(ui_app.state.evolution)
        self.assertFalse(ui_app.state.evolution_active)
        self.assertEqual("", ui_app.state.recommendation_steps)
        self.assertEqual("edition", ui_app.state.vue)

    def test_resolution_random_button_is_ignored_outside_resolution_mode(self):
        ui_app.state.mode_app = "normal"
        ui_app.state.cible[0][0] = 1

        ui_app.remplir_cible_aleatoire(FakeBoard())

        self.assertEqual(1, ui_app.state.cible[0][0])

    def test_population_window_feature_is_removed(self):
        self.assertNotIn("population_button", ui_app.ui)
        self.assertFalse(hasattr(ui_app, "ouvrir_fenetre_population"))

    def test_recommendation_lists_concrete_steps_for_tiny_stagnating_target(self):
        ui_app.state.k_inverse = 9
        self.petite_cible()
        ui_app.state.resultat = nouvelle_grille(0)
        ui_app.state.solveur = SimpleNamespace(
            meilleure_erreur=12,
            meilleur_score=95,
            stagnation=40,
        )

        recommandation = ui_app.construire_recommandation_steps()

        self.assertIn("1, 2, 3, 4, 5, 6, 8", recommandation)

    def test_recommendation_mentions_neighbor_steps_for_noisy_result(self):
        ui_app.state.k_inverse = 5
        ui_app.state.cible = nouvelle_grille(0)
        for cellule in [(10, 10), (10, 11), (11, 10), (11, 11)]:
            ui_app.state.cible[cellule[0]][cellule[1]] = 1
        ui_app.state.resultat = [ligne[:] for ligne in ui_app.state.cible]
        for cellule in [(0, 0), (0, 1), (1, 0), (23, 23)]:
            ui_app.state.resultat[cellule[0]][cellule[1]] = 1
        ui_app.state.solveur = SimpleNamespace(
            meilleure_erreur=4,
            meilleur_score=99,
            stagnation=5,
        )

        recommandation = ui_app.construire_recommandation_steps()

        self.assertIn("5", recommandation)
        self.assertIn("4", recommandation)
        self.assertIn("6", recommandation)

    def test_probable_final_stagnation_is_detected_before_generation_limit(self):
        self.petite_cible()
        ui_app.state.solveur = SimpleNamespace(
            meilleure_erreur=10,
            generation=100,
            stagnation=80,
            config=ui_app.state.config_recherche,
        )

        self.assertTrue(ui_app.stagnation_probablement_finale())

    def test_auto_steps_switches_to_next_queued_step(self):
        class FakeBoard:
            def __init__(self):
                self.messages = []

            def console(self, message):
                self.messages.append(message)

        self.petite_cible()
        ui_app.state.k_inverse = 5
        ui_app.state.grille = nouvelle_grille(0)
        ui_app.state.auto_steps_actif = True
        ui_app.state.auto_steps_tentes = [5]
        ui_app.state.auto_steps_queue = [1]
        ui_app.state.solveur = SimpleNamespace(meilleur_individu=None)

        relancee = ui_app.essayer_step_auto_suivant(FakeBoard(), "test stagnation")

        self.assertTrue(relancee)
        self.assertEqual(1, ui_app.state.k_inverse)
        self.assertEqual([5, 1], ui_app.state.auto_steps_tentes)
        self.assertTrue(ui_app.state.solveur_actif)
        self.assertIsNotNone(ui_app.state.solveur)

    def test_auto_steps_respects_explicit_range(self):
        self.petite_cible()
        ui_app.state.k_inverse = 5
        ui_app.state.auto_steps_plan = [3, 4, 5, 6]
        ui_app.state.auto_steps_tentes = [5]

        steps = ui_app.generer_steps_alternatifs()

        self.assertEqual([3, 4, 6], steps)

    def test_steps_entry_accepts_single_value_or_range(self):
        self.assertEqual([2], ui_app.parser_steps_interface("2"))
        self.assertEqual([2, 3, 4, 5], ui_app.parser_steps_interface("2-5"))

    def test_auto_steps_records_stats_and_formats_them(self):
        self.petite_cible()
        individu = nouvelle_grille(0)
        individu[12][12] = 1
        ui_app.state.k_inverse = 4
        ui_app.state.solveur = SimpleNamespace(
            meilleur_individu=individu,
            meilleure_erreur=3.5,
            meilleure_note_tri=3.501,
            meilleur_score=98.0,
            generation=90,
            stagnation=77,
        )

        ui_app.enregistrer_meilleur_auto_steps()
        stats = ui_app.formater_stats_auto_steps()

        self.assertIn("4g", stats)
        self.assertIn("err 3.50", stats)
        self.assertIn("98.0%", stats)


if __name__ == "__main__":
    unittest.main()
