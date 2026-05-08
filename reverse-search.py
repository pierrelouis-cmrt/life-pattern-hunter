#!/usr/bin/env python3
"""Point d'entrée historique du chasseur de motifs du jeu de la vie."""

try:
    from eniseboard import eniseboard
except ImportError:
    eniseboard = None

from ui_app import run_app


def main():
    if eniseboard is None:
        raise SystemExit("eniseboard n'est pas installe. Lancez: pip install eniseboard")

    run_app(eniseboard)


if __name__ == "__main__":
    main()
