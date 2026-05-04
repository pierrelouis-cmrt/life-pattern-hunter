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

    def test_behavior_vector_and_niche_are_stable(self):
        grid = grid_from_shape([(0, 0), (0, 1), (1, 0), (1, 1)])
        metrics = hunter.classify_grid(grid, 6)

        first = hunter.behavior_vector(metrics)
        second = hunter.behavior_vector(metrics)

        self.assertEqual(first.values, second.values)
        self.assertEqual(first.niche, second.niche)

    def test_novelty_distance_uses_archive_neighbors(self):
        archive = hunter.make_archive()
        config = self.small_config("Still life")
        cache = {}
        block = grid_from_shape([(0, 0), (0, 1), (1, 0), (1, 1)])
        blinker = grid_from_shape([(0, 0), (0, 1), (0, 2)])

        block_eval = hunter.evaluate_candidate(block, config, cache, archive)
        hunter.archive_insert(archive, block_eval)
        blinker_eval = hunter.evaluate_candidate(blinker, config, cache, archive)

        self.assertGreater(blinker_eval.novelty_score, 0)
        self.assertNotEqual(block_eval.behavior.niche, blinker_eval.behavior.niche)

    def test_archive_replaces_worse_elite_in_same_niche(self):
        archive = hunter.make_archive()
        config = self.small_config("Still life")
        cache = {}
        block = grid_from_shape([(0, 0), (0, 1), (1, 0), (1, 1)])
        best = hunter.evaluate_candidate(block, config, cache, archive)
        worse = hunter.Evaluation(
            best.score + 100,
            best.grid,
            best.history,
            best.metrics,
            best.signature,
            best.behavior,
        )

        self.assertTrue(hunter.archive_insert(archive, worse))
        self.assertTrue(hunter.archive_insert(archive, best))
        self.assertEqual(best.score, archive.cells[best.behavior.niche].evaluation.score)

    def test_structural_mutation_is_limited_to_search_zone(self):
        random.seed(789)
        config = self.small_config("Exploration")
        grid = hunter.random_candidate(config.zone, style="cluster")
        profile = hunter.MutationProfile(
            bit_flip=0.0,
            translate=1.0,
            duplicate=1.0,
            mirror=1.0,
            rotate=1.0,
            erode=1.0,
            densify=1.0,
            blast=1.0,
            seed=1.0,
        )
        mutated = hunter.mutate_structural(grid, config.zone, 0.02, profile)
        top, bottom, left, right = config.zone

        for row in range(hunter.ROWS):
            for col in range(hunter.COLS):
                if not (top <= row <= bottom and left <= col <= right):
                    self.assertEqual(0, mutated[row][col])

    def test_creative_generators_respect_bounds(self):
        random.seed(321)
        config = self.small_config("Exploration")
        for style in ("uniform", "gaussian", "symmetric", "cluster", "line", "ring", "composite"):
            grid = hunter.random_candidate(config.zone, 0.20, style)
            self.assertFalse(hunter.is_empty(grid))
            trimmed = hunter.trim_to_zone(grid, config.zone)
            self.assertEqual(hunter.grid_key(trimmed), hunter.grid_key(grid))

    def test_short_exploration_search_fills_multiple_niches(self):
        random.seed(654)
        config = hunter.SearchConfig(
            target="Exploration",
            period=hunter.DEFAULT_PERIOD["Exploration"],
            max_steps=14,
            population_size=28,
            elite_count=5,
            max_generations=2,
            local_tries=2,
            zone=hunter.zone_for_target("Exploration"),
        )
        hunter.state["search"] = {
            "config": config,
            "population": hunter.create_initial_population(config),
            "generation": 0,
            "best": None,
            "cache": {},
            "stagnation": 0,
            "archive": hunter.make_archive(),
            "archive_index": 0,
        }
        hunter.state["search_active"] = True

        hunter.advance_search_one_generation()

        archive = hunter.state["search"]["archive"]
        self.assertGreaterEqual(archive.filled(), 2)
        self.assertEqual(config.population_size, len(hunter.state["search"]["population"]))

    def test_soup_hunter_archive_keeps_non_common_signatures(self):
        random.seed(987)
        config = hunter.SearchConfig(
            target="Soup Hunter",
            period=hunter.DEFAULT_PERIOD["Soup Hunter"],
            max_steps=18,
            population_size=30,
            elite_count=5,
            max_generations=2,
            local_tries=2,
            zone=hunter.zone_for_target("Soup Hunter"),
        )
        cache = {}
        archive = hunter.make_archive()
        for candidate in hunter.create_initial_population(config):
            evaluation = hunter.evaluate_candidate(candidate, config, cache, archive)
            hunter.archive_insert(archive, evaluation)

        kinds = {cell.evaluation.metrics.kind for cell in archive.cells.values()}
        self.assertTrue(kinds - {"still_life", "oscillator", "glider"})


if __name__ == "__main__":
    unittest.main()
