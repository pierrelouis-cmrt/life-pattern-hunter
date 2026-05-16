import os
import struct
import tempfile
import unittest

import grid_visuals


def lire_dimensions_png(chemin):
    with open(chemin, "rb") as fichier:
        contenu = fichier.read(24)
    if contenu[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError("signature PNG invalide")
    return struct.unpack(">II", contenu[16:24])


class GridVisualsTests(unittest.TestCase):
    def test_generation_png_valide_et_deterministe(self):
        with tempfile.TemporaryDirectory() as dossier_a, tempfile.TemporaryDirectory() as dossier_b:
            grid_visuals.generer_tous_les_visuels(dossier_a)
            grid_visuals.generer_tous_les_visuels(dossier_b)

            chemin_a = os.path.join(dossier_a, "gol_transition_blinker.png")
            chemin_b = os.path.join(dossier_b, "gol_transition_blinker.png")

            self.assertEqual((980, 350), lire_dimensions_png(chemin_a))
            with open(chemin_a, "rb") as fichier_a, open(chemin_b, "rb") as fichier_b:
                self.assertEqual(fichier_a.read(), fichier_b.read())


if __name__ == "__main__":
    unittest.main()
