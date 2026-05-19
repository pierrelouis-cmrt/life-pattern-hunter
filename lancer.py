#!/usr/bin/env python3
"""Point d'entrée du chasseur de motifs."""

try:
    from eniseboard import eniseboard
except ImportError:
    eniseboard = None

try:
    from .interface_application import run_app
except ImportError:
    from interface_application import run_app


def main():
    """Vérifie la dépendance graphique puis lance l'application."""
    if eniseboard is None:
        raise SystemExit("eniseboard n'est pas installé. Lancez : pip install eniseboard")

    run_app(eniseboard)


if __name__ == "__main__":
    main()
