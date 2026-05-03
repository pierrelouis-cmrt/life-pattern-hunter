try:
    from eniseboard import eniseboard
except ImportError:
    eniseboard = None

import random
import tkinter as tk
from dataclasses import dataclass


# ============================================================
#  PARAMETRES GENERAUX
# ============================================================

ROWS = 24
COLS = 24
CELL_SIZE = 24
TOROIDAL_BORDERS = False

DEFAULT_MAX_STEPS = 90
DEFAULT_PERIOD = {
    "Still life": 1,
    "Oscillator": 2,
    "Glider": 4,
    "Spaceship": 4,
    "Methuselah": 90,
    "Novelty": 70,
}

TARGETS = ["Still life", "Oscillator", "Glider", "Spaceship", "Methuselah", "Novelty"]
TARGET_FR = {
    "Still life": "vie stable",
    "Oscillator": "oscillateur",
    "Glider": "planeur",
    "Spaceship": "vaisseau",
    "Methuselah": "methuselah",
    "Novelty": "nouveaute",
}

BASE_CANDIDATE_SIZE = 12
WIDE_CANDIDATE_SIZE = 16
PLAYBACK_DELAY_MS = 220
SOLVER_DELAY_MS = 20
SOLVER_ITERATIONS_PER_TICK = 2


# ============================================================
#  PARAMETRES DE L'ALGORITHME GENETIQUE
# ============================================================

POPULATION_SIZE = 150
ELITE_COUNT = 16
MAX_GENETIC_GENERATIONS = 650
LOCAL_IMPROVEMENT_TRIES = 18
INITIAL_DENSITIES = [0.06, 0.10, 0.14, 0.20, 0.28, 0.36]
BASE_MUTATION_RATE = 0.018
RANDOM_INJECTION_RATE = 0.08
MAX_CACHE_SIZE = 12000
HALL_OF_FAME_SIZE = 12
MAX_REASONABLE_POPULATION = 135
EXPLOSION_POPULATION_LIMIT = 190


# ============================================================
#  COULEURS
# ============================================================

BG_COLOR = "#f5f1e8"
LIVE_COLOR = "#181818"
PLAYBACK_LIVE_COLOR = "#2563eb"
CANDIDATE_ZONE_COLOR = "#ebe4d6"
TEXT_COLOR = "#222222"
IMPORTANT_TEXT_COLOR = "#6c4ab6"
UI_BG = "#f8fafc"
BUTTON_BG = "#e2e8f0"
PRIMARY_BUTTON_BG = "#bbf7d0"
DANGER_BUTTON_BG = "#fee2e2"


# ============================================================
#  TYPES DE DONNEES
# ============================================================

@dataclass
class PatternInfo:
    cells: tuple
    origin: tuple
    population: int
    width: int
    height: int

    @property
    def area(self):
        return self.width * self.height


@dataclass
class PatternMetrics:
    kind: str
    generation: int = 0
    period: int = 0
    shift: tuple = (0, 0)
    label: str = ""
    lifespan: int = 0
    initial_population: int = 0
    max_population: int = 0
    final_population: int = 0
    bounding_box_area: int = 0
    diversity: int = 0
    stabilization_generation: int = 0


@dataclass
class SearchConfig:
    target: str
    period: int
    max_steps: int
    population_size: int = POPULATION_SIZE
    elite_count: int = ELITE_COUNT
    max_generations: int = MAX_GENETIC_GENERATIONS
    base_mutation_rate: float = BASE_MUTATION_RATE
    injection_rate: float = RANDOM_INJECTION_RATE
    local_tries: int = LOCAL_IMPROVEMENT_TRIES
    zone: tuple = None


@dataclass
class Evaluation:
    score: float
    grid: list
    history: list
    metrics: PatternMetrics
    signature: tuple


@dataclass
class HallEntry:
    score: float
    grid: list
    metrics: PatternMetrics


# ============================================================
#  ETAT GLOBAL DE L'INTERFACE
# ============================================================

state = {
    "grid": None,
    "display_grid": None,
    "history": [],
    "history_index": 0,
    "playback_active": False,
    "playback_id": 0,
    "search_active": False,
    "search": None,
    "last_metrics": None,
}

ui = {
    "panel": None,
    "target_var": None,
    "period_entry": None,
    "max_steps_entry": None,
    "status_label": None,
    "search_button": None,
    "stop_button": None,
}


# ============================================================
#  OUTILS DE GRILLE
# ============================================================

def centered_zone(size):
    top = (ROWS - size) // 2
    left = (COLS - size) // 2
    return (top, top + size - 1, left, left + size - 1)


BASE_CANDIDATE_ZONE = centered_zone(BASE_CANDIDATE_SIZE)
WIDE_CANDIDATE_ZONE = centered_zone(WIDE_CANDIDATE_SIZE)


def zone_for_target(target):
    if target in ("Spaceship", "Methuselah", "Novelty"):
        return WIDE_CANDIDATE_ZONE
    return BASE_CANDIDATE_ZONE


def new_grid(value=0):
    return [[value for _ in range(COLS)] for _ in range(ROWS)]


def copy_grid(grid):
    return [row[:] for row in grid]


def grid_key(grid):
    return tuple(cell for row in grid for cell in row)


def grids_identical(a, b):
    for i in range(ROWS):
        for j in range(COLS):
            if a[i][j] != b[i][j]:
                return False
    return True


def count_live_cells(grid):
    return sum(sum(row) for row in grid)


def is_empty(grid):
    return count_live_cells(grid) == 0


def live_cells(grid):
    cells = []
    for i in range(ROWS):
        for j in range(COLS):
            if grid[i][j] == 1:
                cells.append((i, j))
    return cells


def cells_in_zone(zone):
    top, bottom, left, right = zone
    cells = []
    for i in range(top, bottom + 1):
        for j in range(left, right + 1):
            cells.append((i, j))
    return cells


def normalize_pattern(grid):
    cells = live_cells(grid)
    if not cells:
        return PatternInfo((), (0, 0), 0, 0, 0)

    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_row = max(row for row, _ in cells)
    max_col = max(col for _, col in cells)

    normalized = tuple(sorted((row - min_row, col - min_col) for row, col in cells))
    return PatternInfo(
        cells=normalized,
        origin=(min_row, min_col),
        population=len(cells),
        width=max_col - min_col + 1,
        height=max_row - min_row + 1,
    )


def trim_to_zone(grid, zone):
    trimmed = new_grid(0)
    top, bottom, left, right = zone
    for i in range(top, bottom + 1):
        for j in range(left, right + 1):
            trimmed[i][j] = grid[i][j]
    return trimmed


def shifted_grid(grid, dr, dc):
    shifted = new_grid(0)
    for row, col in live_cells(grid):
        nr = row + dr
        nc = col + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS:
            shifted[nr][nc] = 1
    return shifted


def cell_difference(a, b):
    diff = 0
    for i in range(ROWS):
        for j in range(COLS):
            if a[i][j] != b[i][j]:
                diff += 1
    return diff


def limit_cache(cache):
    if len(cache) <= MAX_CACHE_SIZE:
        return
    for key in list(cache.keys())[:len(cache) - MAX_CACHE_SIZE]:
        del cache[key]


# ============================================================
#  MOTEUR DU JEU DE LA VIE
# ============================================================

def count_neighbors(grid, row, col):
    total = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr = row + dr
            nc = col + dc
            if TOROIDAL_BORDERS:
                total += grid[nr % ROWS][nc % COLS]
            elif 0 <= nr < ROWS and 0 <= nc < COLS:
                total += grid[nr][nc]
    return total


def next_generation(grid):
    nxt = new_grid(0)
    for i in range(ROWS):
        for j in range(COLS):
            neighbors = count_neighbors(grid, i, j)
            if grid[i][j] == 1 and neighbors in (2, 3):
                nxt[i][j] = 1
            elif grid[i][j] == 0 and neighbors == 3:
                nxt[i][j] = 1
    return nxt


def simulate(grid, steps):
    current = copy_grid(grid)
    for _ in range(steps):
        current = next_generation(current)
    return current


def simulate_history(grid, max_steps):
    history = [copy_grid(grid)]
    current = copy_grid(grid)
    for _ in range(max_steps):
        current = next_generation(current)
        history.append(copy_grid(current))
    return history


# ============================================================
#  CLASSIFICATION ET METRIQUES
# ============================================================

def is_glider_signature(period, shift):
    return period == 4 and abs(shift[0]) == 1 and abs(shift[1]) == 1


def base_metrics(history):
    infos = [normalize_pattern(grid) for grid in history]
    live_counts = [info.population for info in infos]
    diversity = len(set(info.cells for info in infos if info.population > 0))
    last_live = 0
    for index, count in enumerate(live_counts):
        if count > 0:
            last_live = index

    return infos, PatternMetrics(
        kind="unknown",
        lifespan=last_live,
        initial_population=live_counts[0] if live_counts else 0,
        max_population=max(live_counts) if live_counts else 0,
        final_population=live_counts[-1] if live_counts else 0,
        bounding_box_area=max((info.area for info in infos), default=0),
        diversity=diversity,
    )


def classify_history(history):
    if not history:
        return PatternMetrics(kind="empty")

    infos, metrics = base_metrics(history)
    if metrics.initial_population == 0:
        metrics.kind = "empty"
        return metrics

    for generation, info in enumerate(infos[1:], start=1):
        if info.population == 0:
            metrics.kind = "died"
            metrics.generation = generation
            metrics.lifespan = generation - 1
            return metrics

    for b in range(1, len(history)):
        info_b = infos[b]
        if info_b.population == 0:
            continue
        for a in range(0, b):
            info_a = infos[a]
            if info_a.population == 0 or info_a.cells != info_b.cells:
                continue

            period = b - a
            shift = (
                info_b.origin[0] - info_a.origin[0],
                info_b.origin[1] - info_a.origin[1],
            )
            metrics.generation = a
            metrics.period = period
            metrics.shift = shift
            metrics.stabilization_generation = a

            if shift == (0, 0) and period == 1:
                if a == 0:
                    metrics.kind = "still_life"
                else:
                    metrics.kind = "stabilized"
                    metrics.label = "vie stable"
                return metrics

            if shift == (0, 0):
                if a == 0:
                    metrics.kind = "oscillator"
                else:
                    metrics.kind = "stabilized"
                    metrics.label = "oscillateur periode {}".format(period)
                return metrics

            metrics.kind = "glider" if is_glider_signature(period, shift) else "spaceship"
            return metrics

    if metrics.max_population >= EXPLOSION_POPULATION_LIMIT:
        metrics.kind = "exploding"
    elif metrics.initial_population <= 12 and metrics.lifespan >= max(35, int((len(history) - 1) * 0.75)):
        metrics.kind = "methuselah"
    else:
        metrics.kind = "unknown"
    return metrics


def classify_grid(grid, max_steps=DEFAULT_MAX_STEPS):
    return classify_history(simulate_history(grid, max_steps))


def describe_metrics(metrics):
    if metrics is None:
        return "aucune classification"

    names = {
        "empty": "motif vide",
        "died": "mort apres {} generation(s)".format(metrics.generation),
        "still_life": "vie stable",
        "oscillator": "oscillateur periode {}".format(metrics.period),
        "glider": "planeur periode {}, deplacement {}".format(metrics.period, metrics.shift),
        "spaceship": "vaisseau periode {}, deplacement {}".format(metrics.period, metrics.shift),
        "stabilized": "stabilise a t={} ({})".format(metrics.generation, metrics.label),
        "exploding": "explosion controlee difficile",
        "methuselah": "methuselah actif {} generations".format(metrics.lifespan),
        "unknown": "inconnu dans la limite d'analyse",
    }
    return names.get(metrics.kind, metrics.kind)


def pattern_signature(metrics):
    return (metrics.kind, metrics.period, metrics.shift, metrics.final_population, metrics.bounding_box_area)


# ============================================================
#  EXPORT TEXTE
# ============================================================

def grid_to_coordinates(grid):
    cells = live_cells(grid)
    if not cells:
        return "[]"
    return ", ".join("({}, {})".format(row, col) for row, col in cells)


def grid_to_rle(grid):
    info = normalize_pattern(grid)
    if info.population == 0:
        return "x = 0, y = 0, rule = B3/S23\n!"

    rows = [["b" for _ in range(info.width)] for _ in range(info.height)]
    for row, col in info.cells:
        rows[row][col] = "o"

    encoded_rows = []
    for row in rows:
        pieces = []
        current = row[0]
        count = 1
        for cell in row[1:]:
            if cell == current:
                count += 1
            else:
                pieces.append(("" if count == 1 else str(count)) + current)
                current = cell
                count = 1
        pieces.append(("" if count == 1 else str(count)) + current)
        encoded_rows.append("".join(pieces).rstrip("b") or "b")

    return "x = {}, y = {}, rule = B3/S23\n{}!".format(info.width, info.height, "$".join(encoded_rows))


# ============================================================
#  FITNESS DE L'ALGORITHME GENETIQUE
# ============================================================

def compactness_penalty(grid):
    info = normalize_pattern(grid)
    if info.population == 0:
        return 1000
    return info.area * 0.045 + info.population * 0.09


def population_explosion_penalty(metrics):
    if metrics.max_population <= MAX_REASONABLE_POPULATION:
        return 0
    return (metrics.max_population - MAX_REASONABLE_POPULATION) * 3.5


def diversity_penalty(metrics, hall):
    penalty = 0
    for entry in hall:
        if pattern_signature(metrics) == pattern_signature(entry.metrics):
            penalty += 45
        elif metrics.kind == entry.metrics.kind and metrics.period == entry.metrics.period:
            penalty += 8
    return penalty


def score_still_life(grid, config, history, metrics):
    if metrics.initial_population == 0:
        return 10000
    return cell_difference(history[0], history[1]) * 14 + compactness_penalty(grid)


def score_oscillator(grid, config, history, metrics):
    period = max(2, config.period)
    short_history = simulate_history(grid, period)
    score = cell_difference(short_history[0], short_history[period]) * 13
    score += compactness_penalty(grid)
    if metrics.kind == "oscillator":
        score -= 120
        score += abs(metrics.period - period) * 12
    if metrics.kind == "still_life":
        score += 300
    for t in range(1, period):
        if grids_identical(short_history[0], short_history[t]):
            score += 200
    return score + population_explosion_penalty(metrics)


def score_glider(grid, config, history, metrics):
    period = max(4, config.period)
    short_history = simulate_history(grid, period)
    shifts = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    best_error = min(cell_difference(shifted_grid(grid, dr, dc), short_history[period]) for dr, dc in shifts)
    score = best_error * 13 + compactness_penalty(grid)
    score += abs(count_live_cells(grid) - count_live_cells(short_history[period])) * 2
    if metrics.kind == "glider":
        score -= 180
    if metrics.kind in ("still_life", "oscillator"):
        score += 180
    return score + population_explosion_penalty(metrics)


def score_spaceship(grid, config, history, metrics):
    period = max(2, config.period)
    short_history = simulate_history(grid, period)
    initial_info = normalize_pattern(short_history[0])
    final_info = normalize_pattern(short_history[period])
    if initial_info.population == 0:
        return 10000

    shape_error = 0 if initial_info.cells == final_info.cells else cell_difference(short_history[0], short_history[period])
    moved = initial_info.origin != final_info.origin
    score = shape_error * 12 + compactness_penalty(grid)
    if moved:
        score -= 80
    else:
        score += 180
    if metrics.kind in ("spaceship", "glider"):
        score -= 150
    return score + population_explosion_penalty(metrics)


def score_methuselah(grid, config, history, metrics):
    if metrics.initial_population == 0:
        return 10000
    score = 0
    score -= metrics.lifespan * 2.6
    score -= metrics.diversity * 0.7
    score += metrics.initial_population * 4.0
    score += max(0, metrics.initial_population - 10) * 14
    score += population_explosion_penalty(metrics)
    if metrics.kind in ("still_life", "oscillator", "died") and metrics.lifespan < 25:
        score += 320
    if metrics.kind == "stabilized":
        score -= 70
    if metrics.kind == "methuselah":
        score -= 120
    return score


def score_novelty(grid, config, history, metrics, hall):
    if metrics.initial_population == 0:
        return 10000
    score = compactness_penalty(grid)
    score -= metrics.diversity * 1.1
    score -= min(metrics.lifespan, config.max_steps) * 1.0
    score -= min(metrics.max_population, 120) * 0.12
    if metrics.kind in ("still_life", "oscillator", "glider"):
        score += 160
    if metrics.kind in ("spaceship", "methuselah", "stabilized"):
        score -= 80
    return score + population_explosion_penalty(metrics) + diversity_penalty(metrics, hall) * 1.7


def evaluate_candidate(grid, config, cache, hall=None):
    hall = hall or []
    key = (config.target, config.period, config.max_steps, grid_key(grid))
    if key in cache:
        cached = cache[key]
        return Evaluation(
            cached.score,
            copy_grid(grid),
            [copy_grid(item) for item in cached.history],
            cached.metrics,
            cached.signature,
        )

    history = simulate_history(grid, max(1, config.max_steps))
    metrics = classify_history(history)

    if config.target == "Still life":
        score = score_still_life(grid, config, history, metrics)
    elif config.target == "Oscillator":
        score = score_oscillator(grid, config, history, metrics)
    elif config.target == "Glider":
        score = score_glider(grid, config, history, metrics)
    elif config.target == "Spaceship":
        score = score_spaceship(grid, config, history, metrics)
    elif config.target == "Methuselah":
        score = score_methuselah(grid, config, history, metrics)
    else:
        score = score_novelty(grid, config, history, metrics, hall)

    score += diversity_penalty(metrics, hall)
    result = Evaluation(score, copy_grid(grid), [copy_grid(item) for item in history], metrics, pattern_signature(metrics))
    cache[key] = result
    limit_cache(cache)
    return Evaluation(score, copy_grid(grid), [copy_grid(item) for item in history], metrics, result.signature)


# ============================================================
#  OPERATEURS GENETIQUES
# ============================================================

def place_shape(shape, top, left):
    grid = new_grid(0)
    for dr, dc in shape:
        row = top + dr
        col = left + dc
        if 0 <= row < ROWS and 0 <= col < COLS:
            grid[row][col] = 1
    return grid


def classic_seed_candidates(zone):
    top, _, left, _ = zone
    top += 4
    left += 4
    return [
        place_shape([(0, 0), (0, 1), (1, 0), (1, 1)], top, left),
        place_shape([(0, 0), (0, 1), (0, 2)], top, left),
        place_shape([(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)], top, left),
        place_shape([(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)], top - 3, left - 3),
        place_shape([(0, 1), (1, 0), (1, 1), (2, 1), (2, 2)], top, left),
        place_shape([(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)], top, left),
    ]


def random_candidate(zone, density=None):
    if density is None:
        density = random.choice(INITIAL_DENSITIES)
    grid = new_grid(0)
    for i, j in cells_in_zone(zone):
        if random.random() < density:
            grid[i][j] = 1
    return grid


def mutate(grid, zone, mutation_rate):
    mutated = copy_grid(grid)
    for i, j in cells_in_zone(zone):
        if random.random() < mutation_rate:
            mutated[i][j] = 1 - mutated[i][j]
    return mutated


def crossover_uniform(parent_a, parent_b, zone):
    child = new_grid(0)
    for i, j in cells_in_zone(zone):
        child[i][j] = parent_a[i][j] if random.random() < 0.5 else parent_b[i][j]
    return child


def crossover_rectangle(parent_a, parent_b, zone):
    child = copy_grid(parent_a)
    top, bottom, left, right = zone
    r1 = random.randint(top, bottom)
    r2 = random.randint(r1, bottom)
    c1 = random.randint(left, right)
    c2 = random.randint(c1, right)
    for i in range(r1, r2 + 1):
        for j in range(c1, c2 + 1):
            child[i][j] = parent_b[i][j]
    return trim_to_zone(child, zone)


def tournament(evaluated, size=5):
    sample = random.sample(evaluated, min(size, len(evaluated)))
    return min(sample, key=lambda item: item.score).grid


def unique_population(population, config):
    seen = set()
    unique = []
    zone = config.zone
    for grid in population:
        trimmed = trim_to_zone(grid, zone)
        key = grid_key(trimmed)
        if key not in seen:
            seen.add(key)
            unique.append(trimmed)

    while len(unique) < config.population_size:
        grid = random_candidate(zone)
        key = grid_key(grid)
        if key not in seen:
            seen.add(key)
            unique.append(grid)
    return unique[:config.population_size]


def create_initial_population(config, manual_grid=None):
    population = []
    if manual_grid is not None and not is_empty(manual_grid):
        population.append(trim_to_zone(manual_grid, config.zone))

    population.extend(classic_seed_candidates(config.zone))
    for density in INITIAL_DENSITIES:
        for _ in range(8):
            population.append(random_candidate(config.zone, density))

    while len(population) < config.population_size:
        population.append(random_candidate(config.zone))
    return unique_population(population, config)


def local_improvement(best_eval, config, cache, hall):
    best_grid = copy_grid(best_eval.grid)
    best = best_eval
    cells = cells_in_zone(config.zone)
    for _ in range(config.local_tries):
        row, col = random.choice(cells)
        candidate = copy_grid(best_grid)
        candidate[row][col] = 1 - candidate[row][col]
        evaluation = evaluate_candidate(candidate, config, cache, hall)
        if evaluation.score < best.score:
            best = evaluation
            best_grid = copy_grid(candidate)
    return best


def update_hall_of_fame(hall, evaluation):
    for entry in hall:
        if entry.score == evaluation.score and grid_key(entry.grid) == grid_key(evaluation.grid):
            return hall
    hall.append(HallEntry(evaluation.score, copy_grid(evaluation.grid), evaluation.metrics))
    hall.sort(key=lambda item: (item.metrics.kind, item.score))

    diverse = []
    seen_signatures = set()
    for entry in sorted(hall, key=lambda item: item.score):
        signature = pattern_signature(entry.metrics)
        if signature not in seen_signatures:
            diverse.append(entry)
            seen_signatures.add(signature)
        elif len(diverse) < HALL_OF_FAME_SIZE // 2:
            diverse.append(entry)
    return diverse[:HALL_OF_FAME_SIZE]


def make_config(target, period, max_steps):
    target = target if target in TARGETS else "Glider"
    period = max(1, period)
    max_steps = max(2, max_steps)
    return SearchConfig(target=target, period=period, max_steps=max_steps, zone=zone_for_target(target))


def initialize_search(target, period, max_steps, manual_grid=None):
    config = make_config(target, period, max_steps)
    state["search"] = {
        "config": config,
        "population": create_initial_population(config, manual_grid),
        "generation": 0,
        "best": None,
        "cache": {},
        "stagnation": 0,
        "hall": [],
    }
    state["search_active"] = True


def advance_search_one_generation():
    search = state["search"]
    config = search["config"]
    cache = search["cache"]
    hall = search["hall"]

    evaluated = [evaluate_candidate(candidate, config, cache, hall) for candidate in search["population"]]
    evaluated.sort(key=lambda item: item.score)

    improved = local_improvement(evaluated[0], config, cache, hall)
    if improved.score < evaluated[0].score:
        evaluated.insert(0, improved)
    else:
        evaluated.append(improved)
        evaluated.sort(key=lambda item: item.score)

    current_best = evaluated[0]
    search["hall"] = update_hall_of_fame(search["hall"], current_best)

    if search["best"] is None or current_best.score < search["best"].score:
        search["best"] = current_best
        state["grid"] = copy_grid(current_best.grid)
        state["display_grid"] = copy_grid(current_best.grid)
        state["history"] = [copy_grid(item) for item in current_best.history]
        state["history_index"] = 0
        state["last_metrics"] = current_best.metrics
        search["stagnation"] = 0
    else:
        search["stagnation"] += 1

    if search["generation"] >= config.max_generations:
        state["search_active"] = False
        return

    if current_best.score <= 0.01 and config.target not in ("Methuselah", "Novelty"):
        state["search_active"] = False
        return

    mutation_rate = config.base_mutation_rate * (1 + min(6, search["stagnation"] // 25))
    injection_rate = config.injection_rate
    if search["stagnation"] >= 35:
        injection_rate = min(0.24, config.injection_rate * 2.7)

    next_population = []
    for item in evaluated[:config.elite_count]:
        next_population.append(copy_grid(item.grid))

    for entry in search["hall"][:4]:
        next_population.append(mutate(entry.grid, config.zone, mutation_rate * 0.7))

    for _ in range(int(config.population_size * injection_rate)):
        next_population.append(random_candidate(config.zone))

    while len(next_population) < config.population_size:
        parent_a = tournament(evaluated)
        parent_b = tournament(evaluated)
        if random.random() < 0.55:
            child = crossover_uniform(parent_a, parent_b, config.zone)
        else:
            child = crossover_rectangle(parent_a, parent_b, config.zone)
        next_population.append(mutate(child, config.zone, mutation_rate))

    search["population"] = unique_population(next_population, config)
    search["generation"] += 1


# ============================================================
#  INTERFACE ENISEBOARD
# ============================================================

def root_tk(board):
    return getattr(board, "_eniseboard__root", None)


def create_button(parent, text, command, bg=BUTTON_BG):
    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=TEXT_COLOR,
        activebackground=bg,
        activeforeground=TEXT_COLOR,
        relief=tk.FLAT,
        bd=0,
        padx=12,
        pady=8,
        cursor="hand2",
        anchor="w",
    )
    button.pack(fill="x", pady=3)
    return button


def section(parent, text):
    tk.Label(
        parent,
        text=text.upper(),
        bg=UI_BG,
        fg="#64748b",
        font=("TkDefaultFont", 9, "bold"),
        anchor="w",
    ).pack(fill="x", padx=8, pady=(12, 2))


def read_int_entry(entry, default, minimum=1):
    try:
        value = int(entry.get().strip())
    except ValueError:
        value = default
    value = max(minimum, value)
    entry.delete(0, tk.END)
    entry.insert(0, str(value))
    return value


def current_target():
    if ui["target_var"] is None:
        return "Glider"
    value = ui["target_var"].get()
    if " - " in value:
        return value.split(" - ", 1)[0]
    return value


def current_period():
    target = current_target()
    if ui["period_entry"] is None:
        return DEFAULT_PERIOD.get(target, 2)
    return read_int_entry(ui["period_entry"], DEFAULT_PERIOD.get(target, 2), 1)


def current_max_steps():
    if ui["max_steps_entry"] is None:
        return DEFAULT_MAX_STEPS
    return read_int_entry(ui["max_steps_entry"], DEFAULT_MAX_STEPS, 2)


def target_option(target):
    return "{} - {}".format(target, TARGET_FR[target])


def target_changed(*_args):
    target = current_target()
    entry = ui.get("period_entry")
    if entry is not None and entry.winfo_exists():
        entry.delete(0, tk.END)
        entry.insert(0, str(DEFAULT_PERIOD.get(target, 2)))
    update_interface()


def create_interface(board):
    root = root_tk(board)
    if root is None:
        return

    root.configure(bg=UI_BG)
    root.columnconfigure(0, weight=0)
    root.columnconfigure(1, weight=0)
    root.rowconfigure(0, weight=1)

    if ui["panel"] is not None and ui["panel"].winfo_exists():
        ui["panel"].destroy()

    panel = tk.Frame(root, bg=UI_BG, width=245)
    panel.grid(row=0, column=1, rowspan=3, sticky="ns", padx=(8, 10), pady=10)
    panel.grid_propagate(False)
    ui["panel"] = panel

    tk.Label(
        panel,
        text="Chasseur de motifs",
        bg=UI_BG,
        fg=TEXT_COLOR,
        font=("TkDefaultFont", 13, "bold"),
        anchor="w",
    ).pack(fill="x", padx=8, pady=(2, 10))

    section(panel, "Recherche")
    ui["target_var"] = tk.StringVar(value=target_option("Glider"))
    ui["target_var"].trace_add("write", target_changed)
    tk.OptionMenu(panel, ui["target_var"], *[target_option(target) for target in TARGETS]).pack(fill="x", padx=8, pady=(0, 8))

    tk.Label(panel, text="Periode visee", bg=UI_BG, fg=TEXT_COLOR, anchor="w").pack(fill="x", padx=8)
    ui["period_entry"] = tk.Entry(panel, justify="center")
    ui["period_entry"].insert(0, "4")
    ui["period_entry"].pack(fill="x", padx=8, pady=(2, 8))

    tk.Label(panel, text="Generations analysees", bg=UI_BG, fg=TEXT_COLOR, anchor="w").pack(fill="x", padx=8)
    ui["max_steps_entry"] = tk.Entry(panel, justify="center")
    ui["max_steps_entry"].insert(0, str(DEFAULT_MAX_STEPS))
    ui["max_steps_entry"].pack(fill="x", padx=8, pady=(2, 10))

    ui["search_button"] = create_button(panel, "Lancer la recherche (S)", lambda: start_search(board), PRIMARY_BUTTON_BG)
    ui["stop_button"] = create_button(panel, "Arreter (Esc)", lambda: stop_all(board))

    section(panel, "Motif")
    create_button(panel, "Classifier (C)", lambda: classify_current(board))
    create_button(panel, "Lire / pause (Espace)", lambda: toggle_playback(board))
    create_button(panel, "Etape suivante (N)", lambda: step_once(board))
    create_button(panel, "Aleatoire (R)", lambda: randomize_grid(board))
    create_button(panel, "Exporter console", lambda: export_current(board))
    create_button(panel, "Effacer (X)", lambda: clear_grid(board), DANGER_BUTTON_BG)

    ui["status_label"] = tk.Label(
        panel,
        text="Dessinez un motif, classifiez-le ou lancez la recherche.",
        bg=UI_BG,
        fg="#475569",
        justify="left",
        wraplength=205,
        anchor="w",
    )
    ui["status_label"].pack(fill="x", padx=8, pady=(12, 0))
    update_interface()


def update_interface():
    search_button = ui.get("search_button")
    if search_button is not None and search_button.winfo_exists():
        search_button.configure(state=tk.DISABLED if state["search_active"] else tk.NORMAL)

    stop_button = ui.get("stop_button")
    if stop_button is not None and stop_button.winfo_exists():
        active = state["search_active"] or state["playback_active"]
        stop_button.configure(state=tk.NORMAL if active else tk.DISABLED)

    status = ui.get("status_label")
    if status is None or not status.winfo_exists():
        return

    if state["search_active"] and state["search"] is not None:
        search = state["search"]
        config = search["config"]
        best = search["best"]
        if best is None:
            text = "Recherche {}...".format(TARGET_FR[config.target])
        else:
            text = "Gen {} | score {:.2f} | cache {} | {}".format(
                search["generation"],
                best.score,
                len(search["cache"]),
                describe_metrics(best.metrics),
            )
        status.configure(text=text)
        return

    if state["playback_active"] and state["history"]:
        status.configure(text="Lecture generation {} / {}".format(state["history_index"], len(state["history"]) - 1))
        return

    metrics = state["last_metrics"]
    if metrics is not None:
        status.configure(text="{} | vivantes {} | diversite {}".format(
            describe_metrics(metrics),
            count_live_cells(state["display_grid"] or state["grid"]),
            metrics.diversity,
        ))
    else:
        status.configure(text="Dessinez un motif, classifiez-le ou lancez la recherche.")


def display_line(board, row, text, color=TEXT_COLOR):
    board.display(text.ljust(120), row=row, col=0, color=color)


def active_zone():
    if state["search"] is not None:
        return state["search"]["config"].zone
    return zone_for_target(current_target())


def refresh_board(board):
    grid = state["display_grid"] if state["display_grid"] is not None else state["grid"]
    top, bottom, left, right = active_zone()

    for i in range(ROWS):
        for j in range(COLS):
            color = ""
            if grid[i][j] == 1:
                color = PLAYBACK_LIVE_COLOR if state["playback_active"] else LIVE_COLOR
            elif top <= i <= bottom and left <= j <= right:
                color = CANDIDATE_ZONE_COLOR
            board.setBgColor(i, j, color)


def refresh_info(board):
    search = state["search"]
    if state["search_active"] and search is not None:
        config = search["config"]
        best = search["best"]
        best_score = "..." if best is None else "{:.2f}".format(best.score)
        line = "Recherche: {} | gen {} / {} | meilleur score {} | cache {}".format(
            TARGET_FR[config.target],
            search["generation"],
            config.max_generations,
            best_score,
            len(search["cache"]),
        )
    else:
        line = "Cible: {} | periode {} | analyse {} generations".format(
            TARGET_FR[current_target()],
            current_period(),
            current_max_steps(),
        )

    display_line(board, 0, line, IMPORTANT_TEXT_COLOR)

    metrics = state["last_metrics"]
    display_line(board, 1, describe_metrics(metrics) if metrics else "Aucune classification")
    display_line(board, 2, "S start/stop | Espace lecture | N pas | C classifier | R hasard | X effacer | 1-6 cible")

    if state["history"]:
        display_line(board, 3, "Generation {} / {} | cellules vivantes {} | zone de recherche en beige".format(
            state["history_index"],
            len(state["history"]) - 1,
            count_live_cells(state["display_grid"]),
        ))
    else:
        display_line(board, 3, "Cellules vivantes {} | zone de recherche en beige".format(count_live_cells(state["grid"])))

    update_interface()


# ============================================================
#  ACTIONS UTILISATEUR
# ============================================================

def stop_all(board):
    state["search_active"] = False
    state["playback_active"] = False
    state["playback_id"] += 1
    refresh_board(board)
    refresh_info(board)


def reset_history():
    state["history"] = []
    state["history_index"] = 0
    state["last_metrics"] = None


def clear_grid(board):
    stop_all(board)
    state["grid"] = new_grid(0)
    state["display_grid"] = copy_grid(state["grid"])
    reset_history()
    refresh_board(board)
    refresh_info(board)


def randomize_grid(board):
    stop_all(board)
    state["grid"] = random_candidate(active_zone(), 0.22)
    state["display_grid"] = copy_grid(state["grid"])
    reset_history()
    refresh_board(board)
    refresh_info(board)


def classify_current(board):
    stop_all(board)
    history = simulate_history(state["grid"], current_max_steps())
    state["history"] = history
    state["history_index"] = 0
    state["display_grid"] = copy_grid(history[0])
    state["last_metrics"] = classify_history(history)
    refresh_board(board)
    refresh_info(board)


def ensure_history():
    if state["history"]:
        return
    history = simulate_history(state["grid"], current_max_steps())
    state["history"] = history
    state["history_index"] = 0
    state["display_grid"] = copy_grid(history[0])
    state["last_metrics"] = classify_history(history)


def toggle_playback(board):
    if state["playback_active"]:
        state["playback_active"] = False
        refresh_info(board)
        return

    ensure_history()
    state["playback_active"] = True
    state["playback_id"] += 1
    playback_id = state["playback_id"]
    state["history_index"] = 0
    state["display_grid"] = copy_grid(state["history"][0])
    refresh_board(board)
    refresh_info(board)
    board.after(PLAYBACK_DELAY_MS, playback_tick, board, playback_id)


def playback_tick(board, playback_id):
    if not state["playback_active"] or playback_id != state["playback_id"]:
        return
    if state["history_index"] >= len(state["history"]) - 1:
        state["playback_active"] = False
        refresh_info(board)
        return
    state["history_index"] += 1
    state["display_grid"] = copy_grid(state["history"][state["history_index"]])
    refresh_board(board)
    refresh_info(board)
    board.after(PLAYBACK_DELAY_MS, playback_tick, board, playback_id)


def step_once(board):
    state["playback_active"] = False
    ensure_history()
    if state["history_index"] < len(state["history"]) - 1:
        state["history_index"] += 1
        state["display_grid"] = copy_grid(state["history"][state["history_index"]])
    else:
        state["display_grid"] = next_generation(state["display_grid"])
        state["history"].append(copy_grid(state["display_grid"]))
        state["history_index"] = len(state["history"]) - 1
        state["last_metrics"] = classify_history(state["history"])
    refresh_board(board)
    refresh_info(board)


def start_search(board):
    stop_all(board)
    initialize_search(current_target(), current_period(), current_max_steps(), state["grid"])
    refresh_board(board)
    refresh_info(board)
    board.after(1, search_loop, board)


def search_loop(board):
    if not state["search_active"]:
        refresh_board(board)
        refresh_info(board)
        return

    for _ in range(SOLVER_ITERATIONS_PER_TICK):
        if state["search_active"]:
            advance_search_one_generation()

    refresh_board(board)
    refresh_info(board)
    if state["search_active"]:
        board.after(SOLVER_DELAY_MS, search_loop, board)


def export_current(board):
    grid = state["grid"]
    if state["search"] is not None and state["search"]["best"] is not None:
        grid = state["search"]["best"].grid
    metrics = classify_grid(grid, current_max_steps())
    board.console("=== EXPORT MOTIF ===")
    board.console(describe_metrics(metrics))
    board.console("Coordonnees:", grid_to_coordinates(grid))
    board.console("RLE:")
    for line in grid_to_rle(grid).splitlines():
        board.console(line)


def set_target_by_index(index):
    if index < 0 or index >= len(TARGETS):
        return
    target = TARGETS[index]
    if ui["target_var"] is not None:
        ui["target_var"].set(target_option(target))


# ============================================================
#  CALLBACKS SOURIS / CLAVIER
# ============================================================

def handle_click(board, event):
    row = event["row"]
    col = event["col"]
    if not (0 <= row < ROWS and 0 <= col < COLS):
        return

    stop_all(board)
    if event.get("button3", False):
        state["grid"][row][col] = 0
    else:
        state["grid"][row][col] = 1 - state["grid"][row][col]

    state["display_grid"] = copy_grid(state["grid"])
    reset_history()
    refresh_board(board)
    refresh_info(board)


def handle_key(board, event):
    key = event["keysym"].lower()
    if key == "space":
        toggle_playback(board)
    elif key == "n":
        step_once(board)
    elif key == "c":
        classify_current(board)
    elif key == "r":
        randomize_grid(board)
    elif key == "x":
        clear_grid(board)
    elif key == "s":
        if state["search_active"]:
            stop_all(board)
        else:
            start_search(board)
    elif key == "e":
        export_current(board)
    elif key in ("1", "2", "3", "4", "5", "6"):
        set_target_by_index(int(key) - 1)
    elif key == "escape":
        stop_all(board)

    refresh_board(board)
    refresh_info(board)


# ============================================================
#  INITIALISATION
# ============================================================

def initialize(board):
    state["grid"] = new_grid(0)
    state["display_grid"] = copy_grid(state["grid"])
    reset_history()
    create_interface(board)
    refresh_board(board)
    refresh_info(board)
    board.console("Chasseur de motifs pret.")
    board.console("Dessinez un motif, classifiez-le, lancez la recherche genetique ou exportez le meilleur motif.")


def main():
    if eniseboard is None:
        raise RuntimeError("eniseboard n'est pas installe. Lancez: pip install eniseboard")

    eniseboard(
        hsize=COLS,
        vsize=ROWS,
        cell=CELL_SIZE,
        grid=True,
        title="Chasseur de motifs - Game of Life",
        bgcolor=BG_COLOR,
        info=True,
        infoPlace="down",
        infoLines=4,
        console=True,
        consolePlace="down",
        init=initialize,
        click=handle_click,
        key=handle_key,
    )


if __name__ == "__main__":
    main()
