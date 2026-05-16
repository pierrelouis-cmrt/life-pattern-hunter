import pathlib
import unittest


class ArchitectureTests(unittest.TestCase):
    def test_reverse_search_algorithm_reste_dedie_au_solveur(self):
        racine = pathlib.Path(__file__).resolve().parents[1]
        contenu = (racine / "reverse_search_algorithm.py").read_text(encoding="utf-8")

        imports_interdits = [
            "tkinter",
            "eniseboard",
            "google",
            "markdown",
            "grid_visuals",
            "step_search_controller",
        ]
        for nom in imports_interdits:
            self.assertNotIn(nom, contenu)

    def test_racine_garde_un_point_entree_clair(self):
        racine = pathlib.Path(__file__).resolve().parents[1]

        self.assertTrue((racine / "main.py").exists())
        self.assertFalse((racine / "reverse-search.py").exists())
        self.assertFalse((racine / "clean-solution.py").exists())
        self.assertFalse((racine / "random-bruteforce.py").exists())


if __name__ == "__main__":
    unittest.main()
