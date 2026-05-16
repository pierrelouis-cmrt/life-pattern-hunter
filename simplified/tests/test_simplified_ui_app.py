import unittest

from simplified import ui_app
from simplified.app_state import nouvel_etat
from simplified.life_rules import nouvelle_grille


class FakeBoard:
    def __init__(self):
        self.colors = []
        self.messages = []
        self.info = []
        self.after_calls = []

    def setBgColor(self, row, col, color):
        self.colors.append((row, col, color))

    def display(self, text, row=0, col=0, color=None):
        self.info.append((text, row, col, color))

    def console(self, *message):
        self.messages.append(message)

    def after(self, *args):
        self.after_calls.append(args)


class SimplifiedUiAppTests(unittest.TestCase):
    def setUp(self):
        ui_app.state = nouvel_etat()

    def test_steps_parser_accepts_only_single_positive_integer(self):
        self.assertEqual(2, ui_app.parser_steps_interface("2"))

        with self.assertRaises(ValueError):
            ui_app.parser_steps_interface("2-5")
        with self.assertRaises(ValueError):
            ui_app.parser_steps_interface("0")

    def test_grid_click_is_ignored_while_solver_runs(self):
        resultat = object()
        solveur = object()
        ui_app.state.mode_app = "resolution"
        ui_app.state.solveur_actif = True
        ui_app.state.solveur = solveur
        ui_app.state.resultat = resultat

        ui_app.gestion_souris(FakeBoard(), {"row": 1, "col": 1})

        self.assertEqual(0, ui_app.state.cible[1][1])
        self.assertTrue(ui_app.state.solveur_actif)
        self.assertIs(solveur, ui_app.state.solveur)
        self.assertIs(resultat, ui_app.state.resultat)

    def test_empty_target_does_not_start_solver(self):
        ui_app.state.mode_app = "resolution"
        ui_app.state.cible = nouvelle_grille(0)

        ui_app.lancer_ou_arreter_solveur(FakeBoard())

        self.assertFalse(ui_app.state.solveur_actif)
        self.assertIsNone(ui_app.state.solveur)
        self.assertIn("cible est vide", ui_app.state.message_recherche)


if __name__ == "__main__":
    unittest.main()
