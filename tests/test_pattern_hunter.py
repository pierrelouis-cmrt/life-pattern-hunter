import importlib.util
import random
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pattern_hunter", ROOT / "pattern-hunter.py")
hunter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hunter)


def grid_from_shape(cells, top=10, left=10):
    grid = hunter.new_grid(0)
    for row, col in cells:
        grid[top + row][left + col] = 1
    return grid


class LifeClassifierTests(unittest.TestCase):
    def test_block_is_still_life(self):
        grid = grid_from_shape([(0, 0), (0, 1), (1, 0), (1, 1)])
        metrics = hunter.classify_grid(grid, 6)

        self.assertEqual("still_life", metrics.kind)
        self.assertEqual(1, metrics.period)
        self.assertEqual(4, metrics.initial_population)

    def test_blinker_is_period_two_oscillator(self):
        grid = grid_from_shape([(0, 0), (0, 1), (0, 2)])
        metrics = hunter.classify_grid(grid, 6)

        self.assertEqual("oscillator", metrics.kind)
        self.assertEqual(2, metrics.period)
        self.assertEqual((0, 0), metrics.shift)

    def test_glider_is_detected_by_shifted_period(self):
        grid = grid_from_shape([(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)], top=8, left=8)
        metrics = hunter.classify_grid(grid, 8)

        self.assertEqual("glider", metrics.kind)
        self.assertEqual(4, metrics.period)
        self.assertEqual((1, 1), metrics.shift)

    def test_empty_and_dying_patterns_are_classified(self):
        self.assertEqual("empty", hunter.classify_grid(hunter.new_grid(0), 4).kind)

        single_cell = grid_from_shape([(0, 0)])
        metrics = hunter.classify_grid(single_cell, 4)
        self.assertEqual("died", metrics.kind)
        self.assertEqual(1, metrics.generation)


class GeneticSearchTests(unittest.TestCase):
    def small_config(self, target="Still life"):
        return hunter.SearchConfig(
            target=target,
            period=hunter.DEFAULT_PERIOD[target],
            max_steps=12,
            population_size=36,
            elite_count=6,
            max_generations=5,
            local_tries=3,
            zone=hunter.zone_for_target(target),
        )

    def test_population_size_stays_stable(self):
        random.seed(123)
        config = self.small_config()
        population = hunter.create_initial_population(config)
        unique = hunter.unique_population(population, config)

        self.assertEqual(config.population_size, len(population))
        self.assertEqual(config.population_size, len(unique))

    def test_evaluation_cache_is_reused(self):
        config = self.small_config()
        cache = {}
        grid = grid_from_shape([(0, 0), (0, 1), (1, 0), (1, 1)])

        first = hunter.evaluate_candidate(grid, config, cache)
        second = hunter.evaluate_candidate(grid, config, cache)

        self.assertEqual(1, len(cache))
        self.assertEqual(first.score, second.score)
        self.assertEqual(first.metrics.kind, second.metrics.kind)

    def test_mutation_is_limited_to_search_zone(self):
        config = self.small_config()
        grid = hunter.new_grid(0)
        mutated = hunter.mutate(grid, config.zone, 1.0)
        top, bottom, left, right = config.zone

        for row in range(hunter.ROWS):
            for col in range(hunter.COLS):
                inside = top <= row <= bottom and left <= col <= right
                self.assertEqual(1 if inside else 0, mutated[row][col])

    def test_short_still_life_search_preserves_known_block_seed(self):
        random.seed(456)
        config = self.small_config("Still life")
        cache = {}
        population = hunter.create_initial_population(config)
        evaluated = [hunter.evaluate_candidate(candidate, config, cache) for candidate in population]
        best = min(evaluated, key=lambda item: item.score)

        self.assertEqual("still_life", best.metrics.kind)
        self.assertLess(best.score, 1.0)


if __name__ == "__main__":
    unittest.main()
