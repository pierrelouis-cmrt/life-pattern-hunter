import unittest
from types import SimpleNamespace

import step_search_controller as controller
from app_state import nouvel_etat
from life_rules import nouvelle_grille


class StepSearchControllerTests(unittest.TestCase):
    def petite_cible(self, etat):
        etat.cible = nouvelle_grille(0)
        for ligne, col in [(12, 11), (12, 12), (12, 13)]:
            etat.cible[ligne][col] = 1

    def test_generer_steps_respecte_la_plage_explicite(self):
        etat = nouvel_etat()
        etat.auto_steps_plan = [3, 4, 5, 6]
        etat.auto_steps_tentes = [5]

        self.assertEqual([3, 4, 6], controller.generer_steps_alternatifs(etat))

    def test_stagnation_probable_est_detectee(self):
        etat = nouvel_etat()
        self.petite_cible(etat)
        etat.solveur = SimpleNamespace(
            meilleure_erreur=10,
            generation=100,
            stagnation=80,
            config=etat.config_recherche,
        )

        self.assertTrue(controller.stagnation_probablement_finale(etat))

    def test_recommandation_petite_cible_liste_des_steps_concrets(self):
        etat = nouvel_etat()
        self.petite_cible(etat)
        etat.k_inverse = 9
        etat.resultat = nouvelle_grille(0)
        etat.solveur = SimpleNamespace(
            meilleure_erreur=12,
            meilleur_score=95,
            stagnation=40,
        )

        recommandation = controller.construire_recommandation_steps(etat)

        self.assertIn("1, 2, 3, 4, 5, 6, 8", recommandation)

    def test_essayer_step_auto_suivant_lance_le_prochain_solveur(self):
        class FakeBoard:
            def __init__(self):
                self.messages = []

            def console(self, message):
                self.messages.append(message)

        etat = nouvel_etat()
        self.petite_cible(etat)
        etat.k_inverse = 5
        etat.grille = nouvelle_grille(0)
        etat.auto_steps_actif = True
        etat.auto_steps_tentes = [5]
        etat.auto_steps_queue = [1]
        etat.solveur = SimpleNamespace(meilleur_individu=None)

        relancee = controller.essayer_step_auto_suivant(etat, FakeBoard(), "test")

        self.assertTrue(relancee)
        self.assertEqual(1, etat.k_inverse)
        self.assertEqual([5, 1], etat.auto_steps_tentes)
        self.assertTrue(etat.solveur_actif)
        self.assertIsNotNone(etat.solveur)


if __name__ == "__main__":
    unittest.main()
