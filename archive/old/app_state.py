"""État applicatif partagé par l'interface."""

from dataclasses import dataclass, field

from life_rules import COLS, ROWS, nouvelle_grille
from reverse_search_algorithm import SearchConfig


DELAI_ANIMATION_MS = 180
DELAI_SOLVEUR_MS = 20
NB_ITERATIONS_SOLVEUR_PAR_TICK = 2
DELAI_EVOLUTION_MS = 280


@dataclass
class AppState:
    grille: list = field(default_factory=lambda: nouvelle_grille(0, ROWS, COLS))
    cible: list = field(default_factory=lambda: nouvelle_grille(0, ROWS, COLS))
    resultat: list | None = None
    mode_app: str = "resolution"
    vue: str = "edition"
    lecture: bool = False
    generation_life: int = 0
    delai_animation: int = DELAI_ANIMATION_MS
    k_inverse: int = 1
    solveur_actif: bool = False
    solveur: object | None = None
    evolution: list | None = None
    evolution_index: int = 0
    evolution_active: bool = False
    evolution_id: int = 0
    recommendation_steps: str = ""
    auto_steps_actif: bool = False
    auto_steps_queue: list = field(default_factory=list)
    auto_steps_tentes: list = field(default_factory=list)
    auto_steps_resultats: list = field(default_factory=list)
    auto_steps_depart: int = 0
    auto_steps_min: int | None = None
    auto_steps_plan: list = field(default_factory=list)
    auto_steps_max_essais: int = 8
    auto_steps_best: object | None = None
    config_recherche: SearchConfig = field(default_factory=SearchConfig)


def nouvel_etat():
    return AppState()
