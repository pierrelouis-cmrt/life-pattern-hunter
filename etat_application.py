"""État partagé par l'interface et la recherche."""

from dataclasses import dataclass, field

try:
    from .regles_jeudelavie import NB_COLONNES, NB_LIGNES, nouvelle_grille
    from .recherche_genetique import ConfigurationRecherche
except ImportError:
    from regles_jeudelavie import NB_COLONNES, NB_LIGNES, nouvelle_grille
    from recherche_genetique import ConfigurationRecherche


DELAI_ANIMATION_MS = 180
DELAI_SOLVEUR_MS = 20
NB_ITERATIONS_SOLVEUR_PAR_TICK = 2
DELAI_EVOLUTION_MS = 280


@dataclass
class EtatApplication:
    """Regroupe tout ce que l'interface doit mémoriser entre deux actions."""

    grille: list = field(default_factory=lambda: nouvelle_grille(0, NB_LIGNES, NB_COLONNES))
    cible: list = field(default_factory=lambda: nouvelle_grille(0, NB_LIGNES, NB_COLONNES))
    resultat: list | None = None
    mode_app: str = "resolution"
    vue: str = "edition"
    lecture: bool = False
    generation_vie: int = 0
    delai_animation: int = DELAI_ANIMATION_MS
    k_inverse: int = 1
    solveur_actif: bool = False
    solveur: object | None = None
    evolution: list | None = None
    index_evolution: int = 0
    lecture_evolution: bool = False
    id_evolution: int = 0
    message_recherche: str = ""
    config_recherche: ConfigurationRecherche = field(default_factory=ConfigurationRecherche)


def nouvel_etat():
    """Prépare un état neuf au lancement de l'application."""
    return EtatApplication()
