#!/usr/bin/env python3
"""Point d'entree historique de Life Pattern Hunter."""

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
