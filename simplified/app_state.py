"""État applicatif de la version simplifiée."""

from dataclasses import dataclass, field

try:
    from .life_rules import COLS, ROWS, nouvelle_grille
    from .simple_genetic_algorithm import SimpleSearchConfig
except ImportError:
    from life_rules import COLS, ROWS, nouvelle_grille
    from simple_genetic_algorithm import SimpleSearchConfig


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
    message_recherche: str = ""
    config_recherche: SimpleSearchConfig = field(default_factory=SimpleSearchConfig)


def nouvel_etat():
    return AppState()
