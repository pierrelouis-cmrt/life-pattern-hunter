try:
    from eniseboard import eniseboard
except ImportError:
    eniseboard = None

import random
import tkinter as tk
from dataclasses import dataclass


# ============================================================
#  PARAMÈTRES GÉNÉRAUX
# ============================================================

ROWS = 24
COLS = 24
CELL_SIZE = 24
TOROIDAL_BORDERS = False

DEFAULT_MAX_STEPS = 48
DEFAULT_PERIOD = {
    "Exploration": 50,
    "Soup Hunter": 60,
    "Methuselah Lab": 80,
    "Emitter / Ash": 60,
    "Weird Stable": 70,
    "Still life": 1,
    "Oscillator": 2,
    "Glider": 4,
    "Spaceship": 4,
    "Methuselah": 80,
    "Novelty": 50,
}

TARGETS = [
    "Exploration",
    "Soup Hunter",
    "Methuselah Lab",
    "Emitter / Ash",
    "Weird Stable",
    "Still life",
    "Oscillator",
    "Glider",
    "Spaceship",
    "Methuselah",
    "Novelty",
]
TARGET_FR = {
    "Exploration": "exploration créative",
    "Soup Hunter": "soupes aléatoires",
    "Methuselah Lab": "laboratoire methuselah",
    "Emitter / Ash": "émetteur / cendres",
    "Weird Stable": "stabilité étrange",
    "Still life": "vie stable",
    "Oscillator": "oscillateur",
    "Glider": "planeur",
    "Spaceship": "vaisseau",
    "Methuselah": "methuselah",
    "Novelty": "nouveauté",
}

BASE_CANDIDATE_SIZE = 12
WIDE_CANDIDATE_SIZE = 16
PLAYBACK_DELAY_MS = 220
SOLVER_DELAY_MS = 20
SOLVER_ITERATIONS_PER_TICK = 1


# ============================================================
#  PARAMÈTRES DE L'ALGORITHME GÉNÉTIQUE
# ============================================================

POPULATION_SIZE = 60
ELITE_COUNT = 8
MAX_GENETIC_GENERATIONS = 650
LOCAL_IMPROVEMENT_TRIES = 3
INITIAL_DENSITIES = [0.06, 0.10, 0.14, 0.20, 0.28, 0.36]
BASE_MUTATION_RATE = 0.018
RANDOM_INJECTION_RATE = 0.08
MAX_CACHE_SIZE = 12000
HALL_OF_FAME_SIZE = 12
ARCHIVE_MAX_BEHAVIORS = 900
NOVELTY_NEIGHBORS = 10
FAST_EVAL_STEPS = 10
FULL_EVAL_COUNT = 10
SPACESHIP_PERIODS = (4, 5, 6, 8, 10, 12)
DEEP_POPULATION_SIZE = 150
DEEP_FULL_EVAL_COUNT = 34
DEEP_LOCAL_TRIES = 14
MAX_REASONABLE_POPULATION = 135
EXPLOSION_POPULATION_LIMIT = 190


# ============================================================
#  COULEURS
# ============================================================

BG_COLOR = "#f5f1e8"
LIVE_COLOR = "#181818"
PLAYBACK_LIVE_COLOR = "#2563eb"
CANDIDATE_ZONE_COLOR = "#ebe4d6"
RECENT_CHANGE_COLOR = "#7dd3fc"
ARCHIVE_COLOR = "#a7f3d0"
TEXT_COLOR = "#222222"
IMPORTANT_TEXT_COLOR = "#6c4ab6"
UI_BG = "#f8fafc"
BUTTON_BG = "#e2e8f0"
PRIMARY_BUTTON_BG = "#bbf7d0"
DANGER_BUTTON_BG = "#fee2e2"


# ============================================================
#  TYPES DE DONNÉES
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
    avg_population: float = 0.0
    growth: int = 0
    mobility: float = 0.0
    symmetry: float = 0.0
    activity: float = 0.0
    ash_objects: int = 0
    glider_like_events: int = 0


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
    fast_steps: int = FAST_EVAL_STEPS
    full_eval_count: int = FULL_EVAL_COUNT
    deep: bool = False


@dataclass
class BehaviorVector:
    values: tuple
    niche: tuple


@dataclass
class Evaluation:
    score: float
    grid: list
    history: list
    metrics: PatternMetrics
    signature: tuple
    behavior: BehaviorVector = None
    quality_score: float = 0.0
    novelty_score: float = 0.0
    rarity_score: float = 0.0
    aesthetic_score: float = 0.0
    generation_found: int = 0
    full_evaluated: bool = True


@dataclass
class HallEntry:
    score: float
    grid: list
    metrics: PatternMetrics


@dataclass
class ArchiveCell:
    niche: tuple
    evaluation: Evaluation
    seen: int = 1


@dataclass
class SearchArchive:
    cells: dict
    behaviors: list
    discoveries: list

    def filled(self):
        return len(self.cells)


@dataclass
class MutationProfile:
    bit_flip: float = 0.016
    translate: float = 0.12
    duplicate: float = 0.10
    mirror: float = 0.08
    rotate: float = 0.08
    erode: float = 0.08
    densify: float = 0.08
    blast: float = 0.06
    seed: float = 0.10


@dataclass
class Discovery:
    score: float
    grid: list
    metrics: PatternMetrics
    behavior: BehaviorVector
    rle: str
    coordinates: str
    generation: int


@dataclass
class CandidateTrace:
    rank: int
    score: float
    quality_score: float
    novelty_score: float
    kind: str
    period: int
    lifespan: int
    population: int
    niche: tuple


@dataclass
class GenerationTrace:
    generation: int
    evaluated_count: int
    full_eval_count: int
    archive_filled: int
    archive_inserted: int
    best_score: float
    average_score: float
    average_novelty: float
    diversity: int
    stagnation: int
    parents_from_archive: int
    parents_from_population: int
    mutation_rate: float
    injection_count: int
    best_candidates: list
    explanation: str


# ============================================================
#  ÉTAT GLOBAL DE L'INTERFACE
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
    "archive_view_index": 0,
    "generation_trace": None,
    "previous_display_grid": None,
    "auto_preview": True,
}

ui = {
    "panel": None,
    "target_var": None,
    "period_entry": None,
    "max_steps_entry": None,
    "status_label": None,
    "trace_label": None,
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
    if target in ("Exploration", "Soup Hunter", "Methuselah Lab", "Emitter / Ash", "Weird Stable", "Spaceship", "Methuselah", "Novelty"):
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


def active_bounds(grid, margin=1):
    cells = live_cells(grid)
    if not cells:
        return (0, -1, 0, -1)
    min_row = max(0, min(row for row, _ in cells) - margin)
    max_row = min(ROWS - 1, max(row for row, _ in cells) + margin)
    min_col = max(0, min(col for _, col in cells) - margin)
    max_col = min(COLS - 1, max(col for _, col in cells) + margin)
    return (min_row, max_row, min_col, max_col)


def trim_to_zone(grid, zone):
    trimmed = new_grid(0)
    top, bottom, left, right = zone
    for i in range(top, bottom + 1):
        for j in range(left, right + 1):
            trimmed[i][j] = grid[i][j]
    return trimmed


def paste_cells(grid, cells, top, left, zone):
    result = copy_grid(grid)
    ztop, zbottom, zleft, zright = zone
    for dr, dc in cells:
        row = top + dr
        col = left + dc
        if ztop <= row <= zbottom and zleft <= col <= zright:
            result[row][col] = 1
    return result


def clear_zone_part(grid, top, bottom, left, right):
    result = copy_grid(grid)
    for row in range(max(0, top), min(ROWS - 1, bottom) + 1):
        for col in range(max(0, left), min(COLS - 1, right) + 1):
            result[row][col] = 0
    return result


def shifted_grid(grid, dr, dc):
    shifted = new_grid(0)
    for row, col in live_cells(grid):
        nr = row + dr
        nc = col + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS:
            shifted[nr][nc] = 1
    return shifted


def shape_symmetry_score(grid):
    info = normalize_pattern(grid)
    if info.population == 0:
        return 0.0
    cells = set(info.cells)
    horizontal = sum(1 for row, col in cells if (info.height - 1 - row, col) in cells) / info.population
    vertical = sum(1 for row, col in cells if (row, info.width - 1 - col) in cells) / info.population
    diagonal = 0.0
    if info.width == info.height:
        diagonal = sum(1 for row, col in cells if (col, row) in cells) / info.population
    return max(horizontal, vertical, diagonal)


def alive_transitions(history):
    if len(history) < 2:
        return 0
    total = 0
    for a, b in zip(history, history[1:]):
        total += cell_difference(a, b)
    return total


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


def next_generation_active(grid):
    if is_empty(grid):
        return new_grid(0)

    top, bottom, left, right = active_bounds(grid, margin=1)
    nxt = new_grid(0)
    for i in range(top, bottom + 1):
        for j in range(left, right + 1):
            neighbors = count_neighbors(grid, i, j)
            if grid[i][j] == 1 and neighbors in (2, 3):
                nxt[i][j] = 1
            elif grid[i][j] == 0 and neighbors == 3:
                nxt[i][j] = 1
    return nxt


def simulate(grid, steps):
    current = copy_grid(grid)
    for _ in range(steps):
        current = next_generation_active(current)
    return current


def simulate_history(grid, max_steps):
    history = [copy_grid(grid)]
    current = copy_grid(grid)
    for _ in range(max_steps):
        current = next_generation_active(current)
        history.append(copy_grid(current))
    return history


# ============================================================
#  CLASSIFICATION ET METRIQUES
# ============================================================

def is_glider_signature(period, shift):
    return period == 4 and abs(shift[0]) == 1 and abs(shift[1]) == 1


def count_components(grid):
    cells = set(live_cells(grid))
    components = 0
    while cells:
        components += 1
        stack = [cells.pop()]
        while stack:
            row, col = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    neighbor = (row + dr, col + dc)
                    if neighbor in cells:
                        cells.remove(neighbor)
                        stack.append(neighbor)
    return components


def count_glider_like_events(infos):
    events = 0
    for b in range(1, len(infos)):
        for a in range(max(0, b - 6), b):
            if infos[a].population == 5 and infos[a].cells == infos[b].cells:
                shift = (
                    infos[b].origin[0] - infos[a].origin[0],
                    infos[b].origin[1] - infos[a].origin[1],
                )
                if is_glider_signature(b - a, shift):
                    events += 1
    return events


def base_metrics(history):
    infos = [normalize_pattern(grid) for grid in history]
    live_counts = [info.population for info in infos]
    diversity = len(set(info.cells for info in infos if info.population > 0))
    last_live = 0
    for index, count in enumerate(live_counts):
        if count > 0:
            last_live = index
    origins = [info.origin for info in infos if info.population > 0]
    mobility = 0.0
    if len(origins) >= 2:
        first = origins[0]
        mobility = max(abs(row - first[0]) + abs(col - first[1]) for row, col in origins)
    avg_population = sum(live_counts) / len(live_counts) if live_counts else 0.0

    return infos, PatternMetrics(
        kind="unknown",
        lifespan=last_live,
        initial_population=live_counts[0] if live_counts else 0,
        max_population=max(live_counts) if live_counts else 0,
        final_population=live_counts[-1] if live_counts else 0,
        bounding_box_area=max((info.area for info in infos), default=0),
        diversity=diversity,
        avg_population=avg_population,
        growth=(max(live_counts) - live_counts[0]) if live_counts else 0,
        mobility=mobility,
        symmetry=shape_symmetry_score(history[0]),
        activity=alive_transitions(history) / max(1, len(history) - 1),
        ash_objects=count_components(history[-1]) if history else 0,
        glider_like_events=count_glider_like_events(infos),
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

    seen_shapes = {}
    for generation, info in enumerate(infos):
        if info.population == 0:
            continue
        earlier = seen_shapes.get(info.cells)
        if earlier is not None:
            a, info_a = earlier
            period = generation - a
            shift = (
                info.origin[0] - info_a.origin[0],
                info.origin[1] - info_a.origin[1],
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
                    metrics.label = "oscillateur période {}".format(period)
                return metrics

            metrics.kind = "glider" if is_glider_signature(period, shift) else "spaceship"
            return metrics
        seen_shapes[info.cells] = (generation, info)

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
        "died": "mort après {} génération(s)".format(metrics.generation),
        "still_life": "vie stable",
        "oscillator": "oscillateur période {}".format(metrics.period),
        "glider": "planeur période {}, déplacement {}".format(metrics.period, metrics.shift),
        "spaceship": "vaisseau période {}, déplacement {}".format(metrics.period, metrics.shift),
        "stabilized": "stabilisé à t={} ({})".format(metrics.generation, metrics.label),
        "exploding": "explosion contrôlée difficile",
        "methuselah": "methuselah actif {} générations".format(metrics.lifespan),
        "unknown": "inconnu dans la limite d'analyse",
    }
    return names.get(metrics.kind, metrics.kind)


def pattern_signature(metrics):
    return (metrics.kind, metrics.period, metrics.shift, metrics.final_population, metrics.bounding_box_area)


KIND_INDEX = {
    "empty": 0,
    "died": 1,
    "still_life": 2,
    "oscillator": 3,
    "glider": 4,
    "spaceship": 5,
    "stabilized": 6,
    "methuselah": 7,
    "exploding": 8,
    "unknown": 9,
}


def bucket(value, limits):
    for index, limit in enumerate(limits):
        if value <= limit:
            return index
    return len(limits)


def behavior_vector(metrics):
    mobility = abs(metrics.shift[0]) + abs(metrics.shift[1]) + metrics.mobility
    values = (
        KIND_INDEX.get(metrics.kind, 9) / 9.0,
        min(metrics.period, 40) / 40.0,
        min(metrics.lifespan, 160) / 160.0,
        min(metrics.max_population, 220) / 220.0,
        min(metrics.diversity, 120) / 120.0,
        min(metrics.bounding_box_area, ROWS * COLS) / (ROWS * COLS),
        min(metrics.growth + 80, 240) / 240.0,
        min(mobility, 40) / 40.0,
        min(metrics.symmetry, 1.0),
        min(metrics.ash_objects, 18) / 18.0,
        min(metrics.glider_like_events, 8) / 8.0,
    )
    niche = (
        metrics.kind,
        bucket(metrics.period, [1, 2, 4, 8, 16, 32]),
        bucket(metrics.lifespan, [4, 12, 30, 70, 140]),
        bucket(metrics.max_population, [5, 12, 25, 55, 110, 180]),
        bucket(metrics.diversity, [1, 3, 8, 18, 40, 80]),
        bucket(metrics.bounding_box_area, [4, 9, 20, 50, 120, 250]),
        bucket(mobility, [0, 1, 3, 6, 12, 24]),
        bucket(metrics.symmetry, [0.20, 0.50, 0.80]),
    )
    return BehaviorVector(values=values, niche=niche)


def behavior_distance(a, b):
    return sum((x - y) ** 2 for x, y in zip(a.values, b.values)) ** 0.5


def novelty_score(behavior, archive, k=NOVELTY_NEIGHBORS):
    if archive is None or not archive.behaviors:
        return 1.0
    distances = sorted(behavior_distance(behavior, other) for other in archive.behaviors)
    nearest = distances[:max(1, min(k, len(distances)))]
    return sum(nearest) / len(nearest)


def rarity_score(behavior, archive):
    if archive is None:
        return 1.0
    cell = archive.cells.get(behavior.niche)
    if cell is None:
        return 3.0
    return 1.0 / (1 + cell.seen)


def make_archive():
    return SearchArchive(cells={}, behaviors=[], discoveries=[])


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
    initial_info = normalize_pattern(history[0])
    if initial_info.population == 0:
        return 10000

    max_period = min(max(SPACESHIP_PERIODS), len(history) - 1)
    if max_period < 4:
        history = simulate_history(grid, max(SPACESHIP_PERIODS))
        max_period = max(SPACESHIP_PERIODS)

    best_period_score = 10000
    for period in SPACESHIP_PERIODS:
        if period > max_period:
            continue
        final_info = normalize_pattern(history[period])
        if final_info.population == 0:
            continue
        shift = (
            final_info.origin[0] - initial_info.origin[0],
            final_info.origin[1] - initial_info.origin[1],
        )
        same_shape = initial_info.cells == final_info.cells
        shape_error = 0 if same_shape else cell_difference(history[0], history[period])
        moved = shift != (0, 0)
        candidate_score = shape_error * 12
        candidate_score += 220 if not moved else -80
        candidate_score += abs(initial_info.population - final_info.population) * 4
        if same_shape and moved:
            candidate_score -= 100
        if is_glider_signature(period, shift) and initial_info.population == 5 and initial_info.area <= 9:
            candidate_score += 650
        best_period_score = min(best_period_score, candidate_score)

    score = best_period_score + compactness_penalty(grid)
    score -= min(initial_info.population, 24) * 3
    score -= min(initial_info.area, 80) * 0.8
    if initial_info.population <= 5:
        score += 280
    if initial_info.area <= 9:
        score += 150
    if metrics.kind == "spaceship":
        score -= 260
    else:
        score += 420
    if metrics.kind == "glider":
        score += 800
    if metrics.kind in ("still_life", "oscillator", "stabilized", "died", "empty"):
        score += 220
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


def aesthetic_value(metrics):
    value = 0.0
    value += min(metrics.diversity, 90) * 1.15
    value += min(metrics.lifespan, 160) * 0.45
    value += min(metrics.ash_objects, 20) * 2.0
    value += min(metrics.glider_like_events, 10) * 8.0
    value += min(metrics.mobility, 40) * 1.4
    value += min(metrics.bounding_box_area, 220) * 0.10
    value += (1.0 - min(metrics.symmetry, 1.0)) * 18.0
    if metrics.kind in ("still_life", "oscillator", "glider"):
        value -= 25
    if metrics.kind in ("spaceship", "methuselah", "stabilized", "unknown"):
        value += 20
    return value


def score_exploration(metrics):
    if metrics.initial_population == 0:
        return 10000
    score = 120
    score -= metrics.diversity * 1.5
    score -= min(metrics.lifespan, 140) * 0.9
    score -= min(metrics.mobility, 35) * 2.0
    score -= metrics.ash_objects * 2.2
    score += abs(metrics.max_population - 70) * 0.35
    score += max(0, metrics.max_population - 175) * 4.0
    if metrics.kind in ("still_life", "oscillator", "glider", "died"):
        score += 130
    return score


def score_soup_hunter(metrics):
    if metrics.initial_population == 0:
        return 10000
    score = 160
    score -= metrics.ash_objects * 7.0
    score -= metrics.glider_like_events * 18.0
    score -= metrics.diversity * 0.9
    score -= min(metrics.lifespan, 110) * 0.35
    score += max(0, metrics.max_population - 170) * 3.2
    if metrics.kind in ("spaceship", "methuselah", "stabilized", "unknown"):
        score -= 55
    if metrics.kind in ("still_life", "oscillator", "glider") and metrics.ash_objects <= 1:
        score += 110
    return score


def score_emitter_ash(metrics):
    if metrics.initial_population == 0:
        return 10000
    score = 150
    score -= metrics.glider_like_events * 26.0
    score -= metrics.ash_objects * 5.0
    score -= min(metrics.mobility, 35) * 2.5
    score -= metrics.diversity * 1.1
    score += max(0, metrics.max_population - 160) * 3.5
    if metrics.kind in ("spaceship", "methuselah", "unknown"):
        score -= 30
    if metrics.kind in ("still_life", "oscillator", "died"):
        score += 80
    return score


def score_weird_stable(metrics):
    if metrics.initial_population == 0:
        return 10000
    score = 130
    score -= metrics.final_population * 0.7
    score -= metrics.ash_objects * 6.0
    score -= min(metrics.bounding_box_area, 240) * 0.28
    score -= (1.0 - min(metrics.symmetry, 1.0)) * 40.0
    score += max(0, 22 - metrics.final_population) * 2.5
    if metrics.kind == "stabilized":
        score -= 90
    elif metrics.kind == "still_life" and metrics.initial_population > 8:
        score -= 35
    elif metrics.kind in ("died", "empty", "exploding"):
        score += 120
    return score


def quality_score_for_target(grid, config, history, metrics):
    if config.target == "Still life":
        return score_still_life(grid, config, history, metrics)
    if config.target == "Oscillator":
        return score_oscillator(grid, config, history, metrics)
    if config.target == "Glider":
        return score_glider(grid, config, history, metrics)
    if config.target == "Spaceship":
        return score_spaceship(grid, config, history, metrics)
    if config.target in ("Methuselah", "Methuselah Lab"):
        return score_methuselah(grid, config, history, metrics)
    if config.target == "Soup Hunter":
        return score_soup_hunter(metrics)
    if config.target == "Emitter / Ash":
        return score_emitter_ash(metrics)
    if config.target == "Weird Stable":
        return score_weird_stable(metrics)
    if config.target in ("Exploration", "Novelty"):
        return score_exploration(metrics)
    return score_exploration(metrics)


def combined_score(config, quality, novelty, rarity, aesthetic):
    if config.target in ("Exploration", "Novelty"):
        return quality - novelty * 150 - rarity * 30 - aesthetic * 0.9
    if config.target == "Soup Hunter":
        return quality - novelty * 95 - rarity * 24 - aesthetic * 0.55
    if config.target in ("Methuselah Lab", "Emitter / Ash", "Weird Stable"):
        return quality - novelty * 75 - rarity * 18 - aesthetic * 0.45
    return quality - novelty * 30 - rarity * 8 - aesthetic * 0.12


def evaluate_candidate(grid, config, cache, archive=None):
    key = (config.target, config.period, config.max_steps, grid_key(grid))
    if key in cache:
        cached = cache[key]
        history = [copy_grid(item) for item in cached.history]
        metrics = cached.metrics
        behavior = cached.behavior
    else:
        history = simulate_history(grid, max(1, config.max_steps))
        metrics = classify_history(history)
        behavior = behavior_vector(metrics)
        cache[key] = Evaluation(0, copy_grid(grid), [copy_grid(item) for item in history], metrics, pattern_signature(metrics), behavior)
        limit_cache(cache)

    quality = quality_score_for_target(grid, config, history, metrics)
    novelty = novelty_score(behavior, archive)
    rarity = rarity_score(behavior, archive)
    aesthetic = aesthetic_value(metrics)
    score = combined_score(config, quality, novelty, rarity, aesthetic)
    return Evaluation(
        score,
        copy_grid(grid),
        [copy_grid(item) for item in history],
        metrics,
        pattern_signature(metrics),
        behavior,
        quality,
        novelty,
        rarity,
        aesthetic,
    )


def evaluate_candidate_fast(grid, config, cache, archive=None):
    steps = min(config.max_steps, max(2, config.fast_steps))
    if config.target == "Spaceship":
        steps = min(config.max_steps, max(steps, max(SPACESHIP_PERIODS)))
    key = (config.target, config.period, steps, "fast", grid_key(grid))
    if key in cache:
        cached = cache[key]
        history = [copy_grid(item) for item in cached.history]
        metrics = cached.metrics
        behavior = cached.behavior
    else:
        history = simulate_history(grid, steps)
        metrics = classify_history(history)
        behavior = behavior_vector(metrics)
        cache[key] = Evaluation(0, copy_grid(grid), [copy_grid(item) for item in history], metrics, pattern_signature(metrics), behavior, full_evaluated=False)
        limit_cache(cache)

    quality = quality_score_for_target(grid, config, history, metrics)
    novelty = novelty_score(behavior, archive)
    rarity = rarity_score(behavior, archive)
    aesthetic = aesthetic_value(metrics)
    score = combined_score(config, quality, novelty, rarity, aesthetic)
    return Evaluation(
        score,
        copy_grid(grid),
        [copy_grid(item) for item in history],
        metrics,
        pattern_signature(metrics),
        behavior,
        quality,
        novelty,
        rarity,
        aesthetic,
        full_evaluated=False,
    )


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


def classic_seed_candidates(zone, target=None):
    top, _, left, _ = zone
    top += 4
    left += 4
    seeds = [
        place_shape([(0, 0), (0, 1), (1, 0), (1, 1)], top, left),
        place_shape([(0, 0), (0, 1), (0, 2)], top, left),
        place_shape([(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)], top, left),
        place_shape([(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)], top - 3, left - 3),
        place_shape([(0, 1), (1, 0), (1, 1), (2, 1), (2, 2)], top, left),
        place_shape([(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)], top, left),
    ]
    if target == "Spaceship":
        seeds.extend([
            place_shape([(0, 0), (0, 3), (1, 4), (2, 0), (2, 4), (3, 1), (3, 2), (3, 3), (3, 4)], top, left),
            place_shape([(0, 1), (0, 4), (1, 0), (2, 0), (2, 4), (3, 0), (3, 1), (3, 2), (3, 3)], top, left),
        ])
    if target == "Spaceship":
        seeds = [grid for grid in seeds if classify_grid(grid, 8).kind != "glider"]
    return seeds


def random_uniform_candidate(zone, density):
    if density is None:
        density = random.choice(INITIAL_DENSITIES)
    grid = new_grid(0)
    for i, j in cells_in_zone(zone):
        if random.random() < density:
            grid[i][j] = 1
    return grid


def random_gaussian_candidate(zone, density=None):
    if density is None:
        density = random.choice(INITIAL_DENSITIES)
    grid = new_grid(0)
    top, bottom, left, right = zone
    center_row = random.uniform(top + 2, bottom - 2)
    center_col = random.uniform(left + 2, right - 2)
    spread = random.uniform(2.0, max(3.0, (bottom - top) / 2.0))
    for i, j in cells_in_zone(zone):
        d2 = (i - center_row) ** 2 + (j - center_col) ** 2
        probability = min(0.70, density * 2.8 / (1 + d2 / (spread * spread)))
        if random.random() < probability:
            grid[i][j] = 1
    return grid


def random_symmetric_candidate(zone, density=None, symmetry=None):
    if density is None:
        density = random.choice([0.08, 0.12, 0.18, 0.24])
    if symmetry is None:
        symmetry = random.choice(["C2", "C4", "D2", "D4"])
    grid = new_grid(0)
    top, bottom, left, right = zone
    height = bottom - top + 1
    width = right - left + 1
    for i in range(top, bottom + 1):
        for j in range(left, right + 1):
            if random.random() >= density:
                continue
            points = {(i, j)}
            points.add((top + bottom - i, left + right - j))
            if symmetry in ("D2", "D4"):
                points.add((top + bottom - i, j))
                points.add((i, left + right - j))
            if symmetry in ("C4", "D4") and height == width:
                ri = i - top
                cj = j - left
                points.add((top + cj, left + width - 1 - ri))
                points.add((top + height - 1 - cj, left + ri))
            for row, col in points:
                if top <= row <= bottom and left <= col <= right:
                    grid[row][col] = 1
    return grid


def random_cluster_candidate(zone):
    grid = new_grid(0)
    top, bottom, left, right = zone
    for _ in range(random.randint(3, 8)):
        row = random.randint(top, bottom)
        col = random.randint(left, right)
        radius = random.randint(1, 3)
        for i in range(row - radius, row + radius + 1):
            for j in range(col - radius, col + radius + 1):
                if top <= i <= bottom and left <= j <= right and random.random() < 0.45:
                    grid[i][j] = 1
    return grid


def random_line_candidate(zone):
    grid = new_grid(0)
    top, bottom, left, right = zone
    row = random.randint(top, bottom)
    col = random.randint(left, right)
    for _ in range(random.randint(12, 34)):
        if top <= row <= bottom and left <= col <= right:
            grid[row][col] = 1
            if random.random() < 0.35:
                grid[max(top, min(bottom, row + random.choice([-1, 1])))][col] = 1
        row += random.choice([-1, 0, 1])
        col += random.choice([-1, 0, 1])
        row = max(top, min(bottom, row))
        col = max(left, min(right, col))
    return grid


def random_ring_candidate(zone):
    grid = new_grid(0)
    top, bottom, left, right = zone
    center_row = random.randint(top + 3, bottom - 3)
    center_col = random.randint(left + 3, right - 3)
    radius = random.randint(3, max(3, min(bottom - top, right - left) // 2))
    for i, j in cells_in_zone(zone):
        distance = abs(((i - center_row) ** 2 + (j - center_col) ** 2) ** 0.5 - radius)
        if distance < 1.25 and random.random() < 0.70:
            grid[i][j] = 1
    return grid


def random_composite_seed_candidate(zone):
    grid = new_grid(0)
    seeds = classic_seed_candidates(zone)
    for _ in range(random.randint(2, 5)):
        seed = random.choice(seeds)
        info = normalize_pattern(seed)
        if info.population == 0:
            continue
        top, bottom, left, right = zone
        row = random.randint(top, max(top, bottom - max(1, info.height)))
        col = random.randint(left, max(left, right - max(1, info.width)))
        grid = paste_cells(grid, info.cells, row, col, zone)
    return grid


def random_candidate(zone, density=None, style=None):
    if style is None:
        style = random.choice(["uniform", "gaussian", "symmetric", "cluster", "line", "ring", "composite"])
    if style == "uniform":
        return random_uniform_candidate(zone, density)
    if style == "gaussian":
        return random_gaussian_candidate(zone, density)
    if style == "symmetric":
        return random_symmetric_candidate(zone, density)
    if style == "cluster":
        return random_cluster_candidate(zone)
    if style == "line":
        return random_line_candidate(zone)
    if style == "ring":
        return random_ring_candidate(zone)
    return random_composite_seed_candidate(zone)


def mutate(grid, zone, mutation_rate):
    mutated = copy_grid(grid)
    for i, j in cells_in_zone(zone):
        if random.random() < mutation_rate:
            mutated[i][j] = 1 - mutated[i][j]
    return mutated


def mutate_structural(grid, zone, mutation_rate, profile=None):
    profile = profile or MutationProfile(bit_flip=mutation_rate)
    mutated = mutate(grid, zone, profile.bit_flip)
    info = normalize_pattern(mutated)
    top, bottom, left, right = zone

    if info.population > 0 and random.random() < profile.translate:
        dr = random.randint(-3, 3)
        dc = random.randint(-3, 3)
        moved = new_grid(0)
        for row, col in live_cells(mutated):
            nr = row + dr
            nc = col + dc
            if top <= nr <= bottom and left <= nc <= right:
                moved[nr][nc] = 1
        mutated = moved
        info = normalize_pattern(mutated)

    if info.population > 0 and random.random() < profile.duplicate:
        row = random.randint(top, bottom)
        col = random.randint(left, right)
        mutated = paste_cells(mutated, info.cells, row, col, zone)

    if info.population > 0 and random.random() < profile.mirror:
        mirrored = tuple((row, info.width - 1 - col) for row, col in info.cells)
        row = random.randint(top, bottom)
        col = random.randint(left, right)
        mutated = paste_cells(mutated, mirrored, row, col, zone)

    if info.population > 0 and random.random() < profile.rotate:
        rotated = tuple((col, info.height - 1 - row) for row, col in info.cells)
        row = random.randint(top, bottom)
        col = random.randint(left, right)
        mutated = paste_cells(mutated, rotated, row, col, zone)

    if random.random() < profile.erode:
        for i, j in cells_in_zone(zone):
            if mutated[i][j] == 1 and random.random() < 0.20:
                mutated[i][j] = 0

    if random.random() < profile.densify:
        row = random.randint(top, bottom)
        col = random.randint(left, right)
        radius = random.randint(1, 3)
        for i in range(row - radius, row + radius + 1):
            for j in range(col - radius, col + radius + 1):
                if top <= i <= bottom and left <= j <= right and random.random() < 0.35:
                    mutated[i][j] = 1

    if random.random() < profile.blast:
        row = random.randint(top, bottom)
        col = random.randint(left, right)
        radius = random.randint(1, 3)
        for i in range(row - radius, row + radius + 1):
            for j in range(col - radius, col + radius + 1):
                if top <= i <= bottom and left <= j <= right:
                    mutated[i][j] = 1 if random.random() < 0.42 else 0

    if random.random() < profile.seed:
        seed = normalize_pattern(random.choice(classic_seed_candidates(zone)))
        row = random.randint(top, bottom)
        col = random.randint(left, right)
        mutated = paste_cells(mutated, seed.cells, row, col, zone)

    return trim_to_zone(mutated, zone)


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


def crossover_band(parent_a, parent_b, zone):
    child = copy_grid(parent_a)
    top, bottom, left, right = zone
    if random.random() < 0.5:
        cut = random.randint(top, bottom)
        for i in range(cut, bottom + 1):
            for j in range(left, right + 1):
                child[i][j] = parent_b[i][j]
    else:
        cut = random.randint(left, right)
        for i in range(top, bottom + 1):
            for j in range(cut, right + 1):
                child[i][j] = parent_b[i][j]
    return trim_to_zone(child, zone)


def crossover_organic(parent_a, parent_b, zone):
    child = new_grid(0)
    top, bottom, left, right = zone
    center_row = random.uniform(top, bottom)
    center_col = random.uniform(left, right)
    scale = random.uniform(2.0, max(3.0, (bottom - top) / 2.0))
    for i, j in cells_in_zone(zone):
        wave = ((i - center_row) ** 2 + (j - center_col) ** 2) / (scale * scale)
        noise = random.uniform(-0.35, 0.35)
        child[i][j] = parent_a[i][j] if wave + noise < 1.0 else parent_b[i][j]
    return child


def crossover_fragment(parent_a, parent_b, zone):
    info_a = normalize_pattern(parent_a)
    info_b = normalize_pattern(parent_b)
    if info_a.population == 0:
        return trim_to_zone(parent_b, zone)
    if info_b.population == 0:
        return trim_to_zone(parent_a, zone)
    child = new_grid(0)
    top, bottom, left, right = zone
    for info in (info_a, info_b):
        row = random.randint(top, max(top, bottom - max(1, info.height)))
        col = random.randint(left, max(left, right - max(1, info.width)))
        child = paste_cells(child, info.cells, row, col, zone)
    return child


def crossover_creative(parent_a, parent_b, zone):
    operator = random.choice([
        crossover_uniform,
        crossover_rectangle,
        crossover_band,
        crossover_organic,
        crossover_fragment,
    ])
    return operator(parent_a, parent_b, zone)


def tournament(evaluated, size=5):
    sample = random.sample(evaluated, min(size, len(evaluated)))
    return min(sample, key=lambda item: item.score).grid


def select_archive_parent(archive):
    if archive is None or not archive.cells:
        return None
    cells = list(archive.cells.values())
    weights = [1.0 / (cell.seen + 1) + max(0.0, cell.evaluation.novelty_score) for cell in cells]
    total = sum(weights)
    pick = random.random() * total
    running = 0.0
    for cell, weight in zip(cells, weights):
        running += weight
        if running >= pick:
            return cell.evaluation.grid
    return random.choice(cells).evaluation.grid


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

    population.extend(classic_seed_candidates(config.zone, config.target))
    for density in INITIAL_DENSITIES:
        for style in ("uniform", "gaussian", "symmetric"):
            for _ in range(3):
                population.append(random_candidate(config.zone, density, style))

    for style in ("cluster", "line", "ring", "composite"):
        for _ in range(10):
            population.append(random_candidate(config.zone, style=style))

    while len(population) < config.population_size:
        if config.target == "Soup Hunter":
            population.append(random_candidate(config.zone, random.choice([0.12, 0.18, 0.25, 0.32]), "uniform"))
        else:
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


def discovery_from_evaluation(evaluation, generation):
    return Discovery(
        evaluation.score,
        copy_grid(evaluation.grid),
        evaluation.metrics,
        evaluation.behavior,
        grid_to_rle(evaluation.grid),
        grid_to_coordinates(evaluation.grid),
        generation,
    )


def archive_insert(archive, evaluation, generation=0):
    if archive is None:
        return False
    niche = evaluation.behavior.niche
    existing = archive.cells.get(niche)
    inserted = False
    if existing is None:
        archive.cells[niche] = ArchiveCell(niche, evaluation, 1)
        inserted = True
    else:
        existing.seen += 1
        if evaluation.score < existing.evaluation.score:
            existing.evaluation = evaluation
            inserted = True

    archive.behaviors.append(evaluation.behavior)
    if len(archive.behaviors) > ARCHIVE_MAX_BEHAVIORS:
        archive.behaviors = archive.behaviors[-ARCHIVE_MAX_BEHAVIORS:]

    if inserted:
        archive.discoveries.append(discovery_from_evaluation(evaluation, generation))
        archive.discoveries.sort(key=lambda item: item.score)
        archive.discoveries = archive.discoveries[:HALL_OF_FAME_SIZE * 4]
    return inserted


def archive_elites(archive):
    if archive is None:
        return []
    return sorted((cell.evaluation for cell in archive.cells.values()), key=lambda item: item.score)


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


def make_config(target, period, max_steps, deep=False):
    target = target if target in TARGETS else "Glider"
    period = max(1, period)
    max_steps = max(2, max_steps)
    if target == "Spaceship":
        max_steps = max(max_steps, max(SPACESHIP_PERIODS))
    if deep and target in ("Exploration", "Soup Hunter", "Methuselah Lab", "Emitter / Ash", "Weird Stable"):
        max_steps = max(max_steps, DEFAULT_PERIOD[target])
    return SearchConfig(
        target=target,
        period=period,
        max_steps=max_steps,
        population_size=DEEP_POPULATION_SIZE if deep else POPULATION_SIZE,
        elite_count=ELITE_COUNT + 6 if deep else ELITE_COUNT,
        local_tries=DEEP_LOCAL_TRIES if deep else LOCAL_IMPROVEMENT_TRIES,
        zone=zone_for_target(target),
        fast_steps=max(FAST_EVAL_STEPS, max(SPACESHIP_PERIODS)) if target == "Spaceship" else FAST_EVAL_STEPS,
        full_eval_count=DEEP_FULL_EVAL_COUNT if deep else FULL_EVAL_COUNT,
        deep=deep,
    )


def initialize_search(target, period, max_steps, manual_grid=None, deep=False):
    config = make_config(target, period, max_steps, deep)
    state["search"] = {
        "config": config,
        "population": create_initial_population(config, manual_grid),
        "generation": 0,
        "best": None,
        "cache": {},
        "fast_cache": {},
        "stagnation": 0,
        "archive": make_archive(),
        "archive_index": 0,
    }
    state["generation_trace"] = None
    state["search_active"] = True


def candidate_trace(rank, evaluation):
    return CandidateTrace(
        rank,
        evaluation.score,
        evaluation.quality_score,
        evaluation.novelty_score,
        evaluation.metrics.kind,
        evaluation.metrics.period,
        evaluation.metrics.lifespan,
        evaluation.metrics.initial_population,
        evaluation.behavior.niche,
    )


def explain_generation_text(trace):
    if trace is None:
        return "Aucune génération génétique n'a encore été évaluée."
    best = trace.best_candidates[0] if trace.best_candidates else None
    best_text = "aucun meilleur candidat"
    if best is not None:
        best_text = "{} score {:.1f}, Q {:.1f}, N {:.2f}, période {}, vie {}".format(
            best.kind,
            best.score,
            best.quality_score,
            best.novelty_score,
            best.period,
            best.lifespan,
        )
    return (
        "Génération {gen}: {evaluated} candidats filtrés rapidement, {full} évaluations complètes. "
        "Archive QD: {archive} niches, {inserted} insertions. "
        "Sélection: {pa} parents depuis l'archive, {pp} depuis la population. "
        "Mutation moyenne {mut:.3f}, injections {inj}. Meilleur: {best}."
    ).format(
        gen=trace.generation,
        evaluated=trace.evaluated_count,
        full=trace.full_eval_count,
        archive=trace.archive_filled,
        inserted=trace.archive_inserted,
        pa=trace.parents_from_archive,
        pp=trace.parents_from_population,
        mut=trace.mutation_rate,
        inj=trace.injection_count,
        best=best_text,
    )


def advance_search_one_generation():
    search = state["search"]
    config = search["config"]
    cache = search["cache"]
    fast_cache = search.setdefault("fast_cache", {})
    archive = search["archive"]

    fast_evaluated = [
        evaluate_candidate_fast(candidate, config, fast_cache, archive)
        for candidate in search["population"]
    ]
    fast_evaluated.sort(key=lambda item: item.score)
    full_candidates = fast_evaluated[:min(config.full_eval_count, len(fast_evaluated))]

    evaluated = [
        evaluate_candidate(candidate.grid, config, cache, archive)
        for candidate in full_candidates
    ]
    evaluated.sort(key=lambda item: item.score)
    archive_insertions = 0
    for item in evaluated:
        if archive_insert(archive, item, search["generation"]):
            archive_insertions += 1

    if config.local_tries > 0 and evaluated:
        improved = local_improvement(evaluated[0], config, cache, archive)
        if improved.score < evaluated[0].score:
            evaluated.insert(0, improved)
            if archive_insert(archive, improved, search["generation"]):
                archive_insertions += 1
        else:
            evaluated.append(improved)
            evaluated.sort(key=lambda item: item.score)

    elites = archive_elites(archive)
    current_best = min([evaluated[0]] + elites[:8], key=lambda item: item.score)

    if search["best"] is None or current_best.score < search["best"].score:
        search["best"] = current_best
        state["previous_display_grid"] = copy_grid(state["display_grid"]) if state["display_grid"] is not None else None
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

    if current_best.score <= 0.01 and config.target not in ("Spaceship", "Methuselah", "Novelty", "Exploration", "Soup Hunter", "Methuselah Lab", "Emitter / Ash", "Weird Stable"):
        state["search_active"] = False
        return

    mutation_rate = config.base_mutation_rate * (1 + min(6, search["stagnation"] // 25))
    injection_rate = config.injection_rate
    if search["stagnation"] >= 35:
        injection_rate = min(0.24, config.injection_rate * 2.7)
    if search["stagnation"] >= 90:
        injection_rate = min(0.38, injection_rate * 1.5)

    next_population = []
    for item in evaluated[:config.elite_count]:
        next_population.append(copy_grid(item.grid))

    for item in elites[:min(12, len(elites))]:
        next_population.append(mutate_structural(item.grid, config.zone, mutation_rate * 0.7))

    injection_count = int(config.population_size * injection_rate)
    for _ in range(injection_count):
        style = None
        if config.target == "Soup Hunter":
            style = random.choice(["uniform", "gaussian", "symmetric"])
        next_population.append(random_candidate(config.zone, style=style))

    parents_from_archive = 0
    parents_from_population = 0
    while len(next_population) < config.population_size:
        parent_a = select_archive_parent(archive) if random.random() < 0.65 else None
        parent_b = select_archive_parent(archive) if random.random() < 0.65 else None
        if parent_a is None:
            parent_a = tournament(evaluated)
            parents_from_population += 1
        else:
            parents_from_archive += 1
        if parent_b is None:
            parent_b = tournament(evaluated)
            parents_from_population += 1
        else:
            parents_from_archive += 1
        child = crossover_creative(parent_a, parent_b, config.zone)
        next_population.append(mutate_structural(child, config.zone, mutation_rate))

    traces = [candidate_trace(index + 1, item) for index, item in enumerate((evaluated + elites)[:5])]
    state["generation_trace"] = GenerationTrace(
        search["generation"],
        len(fast_evaluated),
        len(full_candidates),
        archive.filled(),
        archive_insertions,
        current_best.score,
        sum(item.score for item in fast_evaluated) / max(1, len(fast_evaluated)),
        sum(item.novelty_score for item in fast_evaluated) / max(1, len(fast_evaluated)),
        len(set(item.signature for item in fast_evaluated)),
        search["stagnation"],
        parents_from_archive,
        parents_from_population,
        mutation_rate,
        injection_count,
        traces,
        "",
    )
    state["generation_trace"].explanation = explain_generation_text(state["generation_trace"])
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
        return "Exploration"
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

    panel = tk.Frame(root, bg=UI_BG, width=285)
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
    ui["target_var"] = tk.StringVar(value=target_option("Exploration"))
    ui["target_var"].trace_add("write", target_changed)
    tk.OptionMenu(panel, ui["target_var"], *[target_option(target) for target in TARGETS]).pack(fill="x", padx=8, pady=(0, 8))

    tk.Label(panel, text="Période visée", bg=UI_BG, fg=TEXT_COLOR, anchor="w").pack(fill="x", padx=8)
    ui["period_entry"] = tk.Entry(panel, justify="center")
    ui["period_entry"].insert(0, str(DEFAULT_PERIOD["Exploration"]))
    ui["period_entry"].pack(fill="x", padx=8, pady=(2, 8))

    tk.Label(panel, text="Générations analysées", bg=UI_BG, fg=TEXT_COLOR, anchor="w").pack(fill="x", padx=8)
    ui["max_steps_entry"] = tk.Entry(panel, justify="center")
    ui["max_steps_entry"].insert(0, str(DEFAULT_MAX_STEPS))
    ui["max_steps_entry"].pack(fill="x", padx=8, pady=(2, 10))

    ui["search_button"] = create_button(panel, "Fast search (S)", lambda: start_search(board), PRIMARY_BUTTON_BG)
    create_button(panel, "Deep run", lambda: start_deep_run(board), PRIMARY_BUTTON_BG)
    create_button(panel, "Pause", lambda: stop_all(board))
    create_button(panel, "Explain", lambda: explain_current_generation(board))
    create_button(panel, "Auto preview", lambda: toggle_auto_preview(board))
    ui["stop_button"] = create_button(panel, "Arreter (Esc)", lambda: stop_all(board))

    section(panel, "Motif")
    create_button(panel, "Classifier (C)", lambda: classify_current(board))
    create_button(panel, "Lire / pause (Espace)", lambda: toggle_playback(board))
    create_button(panel, "Étape suivante (N)", lambda: step_once(board))
    create_button(panel, "Aléatoire (R)", lambda: randomize_grid(board))
    create_button(panel, "Prochaine découverte", lambda: show_next_discovery(board))
    create_button(panel, "Archive", lambda: show_archive_best(board))
    create_button(panel, "Exporter console", lambda: export_current(board))
    create_button(panel, "Exporter archive", lambda: export_all_discoveries(board))
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
    ui["trace_label"] = tk.Label(
        panel,
        text="Processus génétique en attente.",
        bg=UI_BG,
        fg="#334155",
        justify="left",
        wraplength=245,
        anchor="w",
    )
    ui["trace_label"].pack(fill="x", padx=8, pady=(10, 0))
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
            text = "Gen {} | score {:.1f} | Q {:.1f} N {:.2f} | niches {} | {}".format(
                search["generation"],
                best.score,
                best.quality_score,
                best.novelty_score,
                search["archive"].filled(),
                describe_metrics(best.metrics),
            )
        status.configure(text=text)
        update_trace_label()
        return

    if state["playback_active"] and state["history"]:
        status.configure(text="Lecture génération {} / {}".format(state["history_index"], len(state["history"]) - 1))
        return

    metrics = state["last_metrics"]
    if metrics is not None:
        status.configure(text="{} | vivantes {} | diversité {} | mobilité {:.1f}".format(
            describe_metrics(metrics),
            count_live_cells(state["display_grid"] or state["grid"]),
            metrics.diversity,
            metrics.mobility,
        ))
    else:
        status.configure(text="Dessinez un motif, classifiez-le ou lancez la recherche.")
    update_trace_label()


def update_trace_label():
    trace_label = ui.get("trace_label")
    if trace_label is None or not trace_label.winfo_exists():
        return
    trace = state.get("generation_trace")
    if trace is None:
        trace_label.configure(text="Processus génétique en attente.")
        return
    best_lines = []
    for item in trace.best_candidates[:3]:
        best_lines.append("#{} {} sc {:.1f} N {:.2f}".format(item.rank, item.kind, item.score, item.novelty_score))
    trace_label.configure(text=(
        "Processus génétique\n"
        "Éval rapide: {} | complètes: {}\n"
        "Archive: {} niches | +{}\n"
        "Moy score {:.1f} | N moy {:.2f}\n"
        "Diversité {} | stagnation {}\n"
        "{}"
    ).format(
        trace.evaluated_count,
        trace.full_eval_count,
        trace.archive_filled,
        trace.archive_inserted,
        trace.average_score,
        trace.average_novelty,
        trace.diversity,
        trace.stagnation,
        "\n".join(best_lines),
    ))


def display_line(board, row, text, color=TEXT_COLOR):
    board.display(text.ljust(120), row=row, col=0, color=color)


def active_zone():
    if state["search"] is not None:
        return state["search"]["config"].zone
    return zone_for_target(current_target())


def refresh_board(board):
    grid = state["display_grid"] if state["display_grid"] is not None else state["grid"]
    previous = state.get("previous_display_grid")
    top, bottom, left, right = active_zone()
    archived = False
    current_key = grid_key(grid)
    for discovery in current_archive_discoveries():
        if grid_key(discovery.grid) == current_key:
            archived = True
            break

    for i in range(ROWS):
        for j in range(COLS):
            color = ""
            if grid[i][j] == 1:
                changed = previous is not None and previous[i][j] != grid[i][j]
                if changed:
                    color = RECENT_CHANGE_COLOR
                elif archived:
                    color = ARCHIVE_COLOR
                else:
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
        line = "Recherche: {} | gen {} / {} | score {} | niches {} | cache {} | {}".format(
            TARGET_FR[config.target],
            search["generation"],
            config.max_generations,
            best_score,
            search["archive"].filled(),
            len(search["cache"]),
            "deep" if config.deep else "fast",
        )
    else:
        line = "Cible: {} | période {} | analyse {} générations".format(
            TARGET_FR[current_target()],
            current_period(),
            current_max_steps(),
        )

    display_line(board, 0, line, IMPORTANT_TEXT_COLOR)

    metrics = state["last_metrics"]
    if metrics and search is not None and search.get("best") is not None:
        best = search["best"]
        display_line(board, 1, "{} | Q {:.1f} N {:.2f} R {:.2f} A {:.1f}".format(
            describe_metrics(metrics),
            best.quality_score,
            best.novelty_score,
            best.rarity_score,
            best.aesthetic_score,
        ))
    else:
        display_line(board, 1, describe_metrics(metrics) if metrics else "Aucune classification")
    display_line(board, 2, "S fast | D deep | Explain bouton | Auto preview {} | E export | 1-9/0/- cible".format(
        "ON" if state["auto_preview"] else "OFF"
    ))

    if state["history"]:
        display_line(board, 3, "Génération {} / {} | cellules vivantes {} | zone de recherche en beige".format(
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


def start_search(board, deep=False):
    stop_all(board)
    initialize_search(current_target(), current_period(), current_max_steps(), state["grid"], deep=deep)
    refresh_board(board)
    refresh_info(board)
    board.after(1, search_loop, board)


def start_deep_run(board):
    if ui["max_steps_entry"] is not None and ui["max_steps_entry"].winfo_exists():
        value = max(current_max_steps(), 160)
        ui["max_steps_entry"].delete(0, tk.END)
        ui["max_steps_entry"].insert(0, str(value))
    start_search(board, deep=True)


def toggle_auto_preview(board):
    state["auto_preview"] = not state["auto_preview"]
    board.console("Auto preview:", "ON" if state["auto_preview"] else "OFF")
    refresh_info(board)


def advance_auto_preview():
    if not state["auto_preview"] or not state["history"]:
        return
    if state["history_index"] < len(state["history"]) - 1:
        state["history_index"] += 1
    else:
        state["history_index"] = 0
    state["display_grid"] = copy_grid(state["history"][state["history_index"]])


def search_loop(board):
    if not state["search_active"]:
        refresh_board(board)
        refresh_info(board)
        return

    for _ in range(SOLVER_ITERATIONS_PER_TICK):
        if state["search_active"]:
            advance_search_one_generation()
    advance_auto_preview()

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


def explain_current_generation(board):
    text = explain_generation_text(state.get("generation_trace"))
    board.console("=== EXPLICATION GENERATION ===")
    for part in text.split(". "):
        if part:
            board.console(part.strip())


def current_archive_discoveries():
    if state["search"] is None:
        return []
    archive = state["search"].get("archive")
    if archive is None:
        return []
    return archive.discoveries


def display_discovery(board, discovery):
    state["grid"] = copy_grid(discovery.grid)
    state["history"] = simulate_history(state["grid"], current_max_steps())
    state["history_index"] = 0
    state["display_grid"] = copy_grid(state["history"][0])
    state["last_metrics"] = discovery.metrics
    refresh_board(board)
    refresh_info(board)


def show_next_discovery(board):
    discoveries = current_archive_discoveries()
    if not discoveries:
        board.console("Archive vide pour le moment.")
        return
    state["archive_view_index"] = (state["archive_view_index"] + 1) % len(discoveries)
    display_discovery(board, discoveries[state["archive_view_index"]])


def show_archive_best(board):
    discoveries = current_archive_discoveries()
    if not discoveries:
        board.console("Archive vide pour le moment.")
        return
    state["archive_view_index"] = 0
    display_discovery(board, discoveries[0])


def export_all_discoveries(board):
    discoveries = current_archive_discoveries()
    if not discoveries:
        board.console("Aucune découverte à exporter.")
        return
    board.console("=== EXPORT ARCHIVE QD ===")
    for index, discovery in enumerate(discoveries, start=1):
        board.console("#{} | gen {} | score {:.2f} | {}".format(
            index,
            discovery.generation,
            discovery.score,
            describe_metrics(discovery.metrics),
        ))
        for line in discovery.rle.splitlines():
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
    elif key == "d":
        start_deep_run(board)
    elif key == "e":
        export_current(board)
    elif key in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
        set_target_by_index(int(key) - 1)
    elif key == "0":
        set_target_by_index(9)
    elif key == "minus":
        set_target_by_index(10)
    elif key == "a":
        show_archive_best(board)
    elif key == "plus":
        show_next_discovery(board)
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
    board.console("Chasseur de motifs prêt.")
    board.console("Dessinez un motif, classifiez-le, lancez la recherche génétique ou exportez le meilleur motif.")


def main():
    if eniseboard is None:
        raise RuntimeError("eniseboard n'est pas installé. Lancez: pip install eniseboard")

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
