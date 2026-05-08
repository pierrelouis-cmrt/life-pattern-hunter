import unittest

import ui_app
from app_state import nouvel_etat


class UiAppTests(unittest.TestCase):
    def setUp(self):
        ui_app.state = nouvel_etat()

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


if __name__ == "__main__":
    unittest.main()
