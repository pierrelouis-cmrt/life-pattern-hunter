import pathlib
import unittest


class SimplifiedArchitectureTests(unittest.TestCase):
    def test_ui_uses_only_simplified_solver(self):
        racine = pathlib.Path(__file__).resolve().parents[1]
        contenu = (racine / "ui_app.py").read_text(encoding="utf-8")

        self.assertNotIn("step_search_controller", contenu)
        self.assertNotIn("reverse_search_algorithm", contenu)
        self.assertIn("simple_genetic_algorithm", contenu)

    def test_algorithm_keeps_barebones_surface(self):
        racine = pathlib.Path(__file__).resolve().parents[1]
        contenu = (racine / "simple_genetic_algorithm.py").read_text(encoding="utf-8")

        mots_interdits = [
            "cache",
            "nettoyer",
            "ameliorer",
            "améliorer",
            "graine",
            "injection",
            "relance",
            "distance",
        ]
        for mot in mots_interdits:
            self.assertNotIn(mot, contenu)


if __name__ == "__main__":
    unittest.main()

