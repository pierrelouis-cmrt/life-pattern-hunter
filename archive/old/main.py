#!/usr/bin/env python3
"""Point d'entrée principal du chasseur de motifs du Jeu de la vie."""

try:
    from eniseboard import eniseboard
except ImportError:
    eniseboard = None

from ui_app import run_app


def main():
    if eniseboard is None:
        raise SystemExit("eniseboard n'est pas installé. Lancez : pip install eniseboard")

    run_app(eniseboard)


if __name__ == "__main__":
    main()
