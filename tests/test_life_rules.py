import unittest

from life_rules import (
    grilles_identiques,
    historique_evolution,
    nouvelle_grille,
    simuler,
    generation_suivante,
)


def grille_depuis_cellules(cellules, rows=5, cols=5):
    grille = nouvelle_grille(0, rows, cols)
    for ligne, col in cellules:
        grille[ligne][col] = 1
    return grille


class LifeRulesTests(unittest.TestCase):
    def test_block_is_stable(self):
        block = grille_depuis_cellules([(1, 1), (1, 2), (2, 1), (2, 2)])

        self.assertTrue(grilles_identiques(block, generation_suivante(block)))
        self.assertTrue(grilles_identiques(block, simuler(block, 4)))

    def test_blinker_oscillates_every_two_generations(self):
        vertical = grille_depuis_cellules([(1, 2), (2, 2), (3, 2)])
        horizontal = grille_depuis_cellules([(2, 1), (2, 2), (2, 3)])

        self.assertTrue(grilles_identiques(horizontal, generation_suivante(vertical)))
        self.assertTrue(grilles_identiques(vertical, simuler(vertical, 2)))

    def test_historique_contains_initial_and_each_step(self):
        grid = grille_depuis_cellules([(1, 2), (2, 2), (3, 2)])
        historique = historique_evolution(grid, 3)

        self.assertEqual(4, len(historique))
        self.assertTrue(grilles_identiques(grid, historique[0]))
        self.assertTrue(grilles_identiques(simuler(grid, 3), historique[-1]))


if __name__ == "__main__":
    unittest.main()
