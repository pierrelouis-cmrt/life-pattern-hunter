"""Interface Eniseboard/Tkinter de Life Pattern Hunter."""

import random
import tkinter as tk
from tkinter import ttk

from app_state import (
    DELAI_EVOLUTION_MS,
    DELAI_SOLVEUR_MS,
    NB_ITERATIONS_SOLVEUR_PAR_TICK,
    nouvel_etat,
)
from life_rules import (
    COLS,
    ROWS,
    copier_grille,
    grille_vide,
    historique_evolution,
    nombre_cellules_vivantes,
    nouvelle_grille,
    generation_suivante,
)
from reverse_search_algorithm import (
    compter_differences,
    avancer_solveur_une_generation,
    initialiser_solveur,
)


CELL_SIZE = 24

BG_COLOR = "#f5f1e8"
GRID_COLOR = "#ddd6c7"
LIVE_COLOR = "#2563eb"
TARGET_COLOR = "#181818"
INITIAL_AND_TARGET = "#6c4ab6"
RESULT_OK = "#2ecc71"
RESULT_EXTRA = "#e74c3c"
RESULT_MISSING = "#f39c12"
TEXT_COLOR = "#222222"
IMPORTANT_TEXT = "#7a3cff"
UI_BG = "#f8fafc"
BUTTON_BG = "#e2e8f0"
PRIMARY_BUTTON_BG = "#bbf7d0"
DANGER_BUTTON_BG = "#fee2e2"
DISCREET_TEXT = "#475569"

state = nouvel_etat()

ui = {
    "panel": None,
    "mode_var": None,
    "steps_entry": None,
    "start_solver_button": None,
    "normal_play_button": None,
    "target_button": None,
    "initial_button": None,
    "result_button": None,
    "evolution_button": None,
    "previous_button": None,
    "next_button": None,
    "population_button": None,
    "progress": None,
    "progress_label": None,
    "status_label": None,
    "normal_step_button": None,
    "normal_random_button": None,
    "population_window": None,
    "population_canvas": None,
    "population_frame": None,
    "population_step": 0,
    "population_after_id": None,
}


def racine_tk(board):
    return getattr(board, "_eniseboard__root", None)


def creer_bouton(parent, texte, commande, couleur=BUTTON_BG):
    bouton = tk.Button(
        parent,
        text=texte,
        command=commande,
        bg=couleur,
        fg=TEXT_COLOR,
        activebackground=couleur,
        activeforeground=TEXT_COLOR,
        relief=tk.FLAT,
        bd=0,
        padx=12,
        pady=7,
        cursor="hand2",
        anchor="w",
    )
    bouton.pack(fill="x", pady=3)
    return bouton


def creer_titre_section(parent, texte):
    tk.Label(
        parent,
        text=texte.upper(),
        bg=UI_BG,
        fg="#64748b",
        font=("TkDefaultFont", 9, "bold"),
        anchor="w",
    ).pack(fill="x", padx=8, pady=(12, 2))


def fixer_taille_fenetre(root):
    root.update_idletasks()
    largeur = max(root.winfo_reqwidth(), 920)
    hauteur = max(root.winfo_reqheight(), 760)
    root.geometry(f"{largeur}x{hauteur}")
    root.minsize(largeur, hauteur)


def afficher_ligne(board, ligne, texte, couleur=TEXT_COLOR):
    board.display(texte.ljust(140), row=ligne, col=0, color=couleur)


def changer_mode(board):
    valeur = ui["mode_var"].get()
    state.mode_app = "normal" if valeur == "Jeu normal" else "resolution"
    state.lecture = False
    state.solveur_actif = False
    state.evolution_active = False
    state.evolution_id += 1
    state.vue = "normal" if state.mode_app == "normal" else "edition"
    rafraichir_plateau(board)
    afficher_infos(board)


def creer_interface(board):
    root = racine_tk(board)
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
        text="Life Pattern Hunter",
        bg=UI_BG,
        fg=TEXT_COLOR,
        font=("TkDefaultFont", 13, "bold"),
        anchor="w",
    ).pack(fill="x", padx=8, pady=(2, 10))

    creer_titre_section(panel, "Mode")
    ui["mode_var"] = tk.StringVar(value="Résolution")
    for label in ("Résolution", "Jeu normal"):
        tk.Radiobutton(
            panel,
            text=label,
            variable=ui["mode_var"],
            value=label,
            command=lambda b=board: changer_mode(b),
            bg=UI_BG,
            fg=TEXT_COLOR,
            activebackground=UI_BG,
            anchor="w",
        ).pack(fill="x", padx=8)

    creer_titre_section(panel, "Jeu normal")
    ui["normal_play_button"] = creer_bouton(panel, "Lire / pause", lambda: lancer_ou_arreter_jeu_normal(board), PRIMARY_BUTTON_BG)
    ui["normal_step_button"] = creer_bouton(panel, "Step +1", lambda: avancer_jeu_normal(board))
    ui["normal_random_button"] = creer_bouton(panel, "Grille aleatoire", lambda: remplir_initial_aleatoire(board))

    creer_titre_section(panel, "Résolution")
    tk.Label(panel, text="Steps", bg=UI_BG, fg=TEXT_COLOR, anchor="w").pack(fill="x", padx=8)
    entree = tk.Entry(panel, justify="center")
    entree.insert(0, str(state.k_inverse))
    entree.pack(fill="x", padx=8, pady=(2, 8))
    ui["steps_entry"] = entree

    ui["start_solver_button"] = creer_bouton(panel, "Start solver", lambda: lancer_ou_arreter_solveur(board), PRIMARY_BUTTON_BG)
    ui["target_button"] = creer_bouton(panel, "Edit target", lambda: afficher_vue(board, "edition"))
    ui["initial_button"] = creer_bouton(panel, "Best initial", lambda: afficher_vue(board, "initial"))
    ui["result_button"] = creer_bouton(panel, "Show result", lambda: afficher_vue(board, "resultat"))
    ui["evolution_button"] = creer_bouton(panel, "Play evolution", lambda: lancer_ou_arreter_evolution(board))
    ui["previous_button"] = creer_bouton(panel, "Previous step", lambda: deplacer_evolution(board, -1))
    ui["next_button"] = creer_bouton(panel, "Next step", lambda: deplacer_evolution(board, 1))
    ui["population_button"] = creer_bouton(panel, "Voir population", lambda: ouvrir_fenetre_population(board))

    ui["progress"] = ttk.Progressbar(
        panel,
        maximum=state.config_recherche.nb_generations_max,
        mode="determinate",
    )
    ui["progress"].pack(fill="x", padx=8, pady=(8, 2))
    ui["progress_label"] = tk.Label(panel, text="Progression en attente.", bg=UI_BG, fg=DISCREET_TEXT, anchor="w")
    ui["progress_label"].pack(fill="x", padx=8)

    creer_titre_section(panel, "Reset")
    creer_bouton(panel, "Clear", lambda: tout_effacer_depuis_interface(board), DANGER_BUTTON_BG)

    ui["status_label"] = tk.Label(
        panel,
        text="Dessinez une cible, choisissez Steps, puis lancez le solveur.",
        bg=UI_BG,
        fg=DISCREET_TEXT,
        justify="left",
        wraplength=250,
        anchor="w",
    )
    ui["status_label"].pack(fill="x", padx=8, pady=(12, 0))

    actualiser_interface()
    root.after(50, lambda: fixer_taille_fenetre(root))


def couleur_case_normale(i, j):
    return LIVE_COLOR if state.grille[i][j] == 1 else ""


def couleur_case_edition(i, j):
    return TARGET_COLOR if state.cible[i][j] == 1 else ""


def couleur_case_initiale(i, j):
    vivant = state.grille[i][j]
    cible = state.cible[i][j]
    if vivant == 1 and cible == 1:
        return INITIAL_AND_TARGET
    if vivant == 1:
        return LIVE_COLOR
    if cible == 1:
        return "#cbd5e1"
    return ""


def couleur_case_resultat(i, j):
    if state.resultat is None:
        return couleur_case_initiale(i, j)

    resultat = state.resultat[i][j]
    cible = state.cible[i][j]
    if resultat == 1 and cible == 1:
        return RESULT_OK
    if resultat == 1 and cible == 0:
        return RESULT_EXTRA
    if resultat == 0 and cible == 1:
        return RESULT_MISSING
    return ""


def couleur_case_evolution(i, j):
    if state.evolution is None:
        return couleur_case_initiale(i, j)

    courant = state.evolution[state.evolution_index][i][j]
    cible = state.cible[i][j]
    if courant == 1 and cible == 1:
        return INITIAL_AND_TARGET
    if courant == 1:
        return LIVE_COLOR
    if cible == 1:
        return "#f8c471"
    return ""


def rafraichir_plateau(board):
    for i in range(ROWS):
        for j in range(COLS):
            if state.mode_app == "normal" or state.vue == "normal":
                couleur = couleur_case_normale(i, j)
            elif state.vue == "resultat":
                couleur = couleur_case_resultat(i, j)
            elif state.vue == "evolution":
                couleur = couleur_case_evolution(i, j)
            elif state.vue == "initial":
                couleur = couleur_case_initiale(i, j)
            else:
                couleur = couleur_case_edition(i, j)

            board.setBgColor(i, j, couleur)


def actualiser_interface():
    solver_disponible = state.solveur is not None and state.solveur.dernier_snapshot is not None
    resultat_disponible = state.resultat is not None
    resolution = state.mode_app == "resolution"

    if ui["start_solver_button"] is not None and ui["start_solver_button"].winfo_exists():
        ui["start_solver_button"].configure(
            text="Stop solver" if state.solveur_actif else "Start solver",
            state=tk.NORMAL if resolution else tk.DISABLED,
        )

    if ui["normal_play_button"] is not None and ui["normal_play_button"].winfo_exists():
        ui["normal_play_button"].configure(
            text="Pause" if state.lecture else "Lire / pause",
            state=tk.NORMAL if state.mode_app == "normal" else tk.DISABLED,
        )
    for key in ("normal_step_button", "normal_random_button"):
        bouton = ui.get(key)
        if bouton is not None and bouton.winfo_exists():
            bouton.configure(state=tk.NORMAL if state.mode_app == "normal" else tk.DISABLED)

    for key in ("target_button", "initial_button", "result_button", "evolution_button", "previous_button", "next_button"):
        bouton = ui.get(key)
        if bouton is not None and bouton.winfo_exists():
            bouton.configure(state=tk.NORMAL if resolution else tk.DISABLED)

    for key in ("initial_button", "result_button", "evolution_button", "previous_button", "next_button"):
        bouton = ui.get(key)
        if bouton is not None and bouton.winfo_exists():
            bouton.configure(state=tk.NORMAL if resolution and resultat_disponible else tk.DISABLED)

    if ui["population_button"] is not None and ui["population_button"].winfo_exists():
        ui["population_button"].configure(state=tk.NORMAL if resolution and solver_disponible else tk.DISABLED)

    if ui["evolution_button"] is not None and ui["evolution_button"].winfo_exists():
        ui["evolution_button"].configure(text="Stop evolution" if state.evolution_active else "Play evolution")

    progress = ui.get("progress")
    progress_label = ui.get("progress_label")
    if progress is not None and progress.winfo_exists():
        progress["maximum"] = state.config_recherche.nb_generations_max
        progress["value"] = state.solveur.generation if state.solveur is not None else 0
    if progress_label is not None and progress_label.winfo_exists():
        if state.solveur is not None:
            s = state.solveur
            progress_label.configure(
                text="Gen {} / {} | erreur {} | exactitude {:.2f}%".format(
                    s.generation,
                    s.config.nb_generations_max,
                    "?" if s.meilleure_erreur is None else f"{s.meilleure_erreur:.2f}",
                    s.meilleur_score,
                )
            )
        else:
            progress_label.configure(text="Progression en attente.")

    status = ui.get("status_label")
    if status is not None and status.winfo_exists():
        status.configure(text=texte_status())

    rafraichir_fenetre_population()


def texte_status():
    if state.mode_app == "normal":
        return "Mode jeu normal : dessinez une grille initiale, puis lancez ou avancez l'evolution."

    if state.solveur_actif and state.solveur is not None:
        s = state.solveur
        return "Recherche active. Stagnation {} | cache {} | zone {}.".format(
            s.stagnation,
            len(s.cache),
            s.zone,
        )

    if state.recommendation_steps:
        return state.recommendation_steps

    if state.resultat is not None:
        return "Meilleure grille initiale disponible. Inspectez le resultat ou l'evolution."

    return "Mode resolution : dessinez la cible finale, choisissez Steps, puis lancez le solveur."


def lire_nb_etapes_depuis_interface(board):
    entree = ui.get("steps_entry")
    if entree is None or not entree.winfo_exists():
        return True

    texte = entree.get().strip()
    try:
        valeur = int(texte)
    except ValueError:
        board.console("Nombre d'etapes invalide :", texte)
        valeur = state.k_inverse

    if valeur < 1:
        board.console("Le nombre d'etapes doit etre au moins 1.")
        valeur = state.k_inverse

    state.k_inverse = max(1, valeur)
    entree.delete(0, tk.END)
    entree.insert(0, str(state.k_inverse))
    return valeur >= 1


def synchroniser_entree_etapes():
    entree = ui.get("steps_entry")
    if entree is not None and entree.winfo_exists():
        entree.delete(0, tk.END)
        entree.insert(0, str(state.k_inverse))


def afficher_vue(board, vue):
    if state.mode_app != "resolution":
        return
    if vue in ("initial", "resultat") and state.resultat is None:
        return

    if vue == "evolution":
        preparer_evolution()
        if state.evolution is None:
            return
    else:
        state.evolution_active = False

    if vue == "edition":
        state.solveur_actif = False

    state.vue = vue
    rafraichir_plateau(board)
    afficher_infos(board)


def preparer_evolution(reset_index=True):
    if state.grille is None or state.resultat is None:
        return

    if state.evolution is not None and len(state.evolution) == state.k_inverse + 1:
        state.evolution_index = 0 if reset_index else min(state.evolution_index, len(state.evolution) - 1)
        return

    ancien_index = state.evolution_index
    state.evolution = historique_evolution(state.grille, state.k_inverse, state.config_recherche.bords_toriques)
    state.evolution_index = 0 if reset_index else min(ancien_index, len(state.evolution) - 1)


def lancer_ou_arreter_evolution(board):
    if state.evolution_active:
        state.evolution_active = False
        afficher_infos(board)
        return

    preparer_evolution()
    if state.evolution is None:
        return

    state.evolution_id += 1
    evolution_id = state.evolution_id
    state.evolution_active = True
    state.evolution_index = 0
    state.vue = "evolution"
    rafraichir_plateau(board)
    afficher_infos(board)
    board.after(DELAI_EVOLUTION_MS, boucle_evolution, board, evolution_id)


def boucle_evolution(board, evolution_id):
    if not state.evolution_active or evolution_id != state.evolution_id:
        return
    if state.evolution is None or state.evolution_index >= len(state.evolution) - 1:
        state.evolution_active = False
        afficher_infos(board)
        return

    state.evolution_index += 1
    state.vue = "evolution"
    rafraichir_plateau(board)
    afficher_infos(board)
    board.after(DELAI_EVOLUTION_MS, boucle_evolution, board, evolution_id)


def deplacer_evolution(board, delta):
    preparer_evolution(reset_index=False)
    if state.evolution is None:
        return

    state.evolution_active = False
    state.evolution_index = max(0, min(len(state.evolution) - 1, state.evolution_index + delta))
    state.vue = "evolution"
    rafraichir_plateau(board)
    afficher_infos(board)


def afficher_infos(board):
    mode = "JEU NORMAL" if state.mode_app == "normal" else "RESOLUTION"
    afficher_ligne(
        board,
        0,
        "Mode: {} | View: {} | Steps: {} | target cells: {}".format(
            mode,
            state.vue.upper(),
            state.k_inverse,
            nombre_cellules_vivantes(state.cible),
        ),
        IMPORTANT_TEXT,
    )

    if state.mode_app == "normal":
        afficher_ligne(board, 1, "Normal: left click toggles cells. Use Lire/pause or Step +1.")
        afficher_ligne(board, 2, "Keys: Space play/pause | N next | R random | X clear | M mode")
        afficher_ligne(board, 3, "Life generation: {} | live cells: {}".format(state.generation_life, nombre_cellules_vivantes(state.grille)), IMPORTANT_TEXT)
    else:
        if state.vue == "evolution" and state.evolution is not None:
            ligne_1 = "Evolution step {} / {}: blue=current, purple=target match, orange=missing target.".format(
                state.evolution_index,
                len(state.evolution) - 1,
            )
        else:
            ligne_1 = "Draw the desired finish grid, set Steps, then click Start solver."
        afficher_ligne(board, 1, ligne_1)
        afficher_ligne(board, 2, "Keys: S solve | V result/initial | T target | P population | X clear | arrows steps")

        if state.solveur is not None:
            s = state.solveur
            afficher_ligne(
                board,
                3,
                "{} | gen {} | error {} | accuracy {:.2f}% | stagnation {}".format(
                    "Searching" if state.solveur_actif else "Stopped",
                    s.generation,
                    "?" if s.meilleure_erreur is None else f"{s.meilleure_erreur:.2f}",
                    s.meilleur_score,
                    s.stagnation,
                ),
                IMPORTANT_TEXT,
            )
        else:
            afficher_ligne(board, 3, "Initial live cells: {} | desired finish cells: {}".format(nombre_cellules_vivantes(state.grille), nombre_cellules_vivantes(state.cible)))

    actualiser_interface()


def boucle_animation_normale(board):
    if not state.lecture or state.mode_app != "normal":
        return

    state.grille = generation_suivante(state.grille, state.config_recherche.bords_toriques)
    state.generation_life += 1
    rafraichir_plateau(board)
    afficher_infos(board)
    board.after(state.delai_animation, boucle_animation_normale, board)


def lancer_ou_arreter_jeu_normal(board):
    if state.mode_app != "normal":
        return
    state.lecture = not state.lecture
    if state.lecture:
        board.after(state.delai_animation, boucle_animation_normale, board)
    afficher_infos(board)


def avancer_jeu_normal(board):
    if state.mode_app != "normal":
        return
    state.lecture = False
    state.grille = generation_suivante(state.grille, state.config_recherche.bords_toriques)
    state.generation_life += 1
    rafraichir_plateau(board)
    afficher_infos(board)


def boucle_solveur(board):
    if not state.solveur_actif:
        rafraichir_plateau(board)
        afficher_infos(board)
        return

    for _ in range(NB_ITERATIONS_SOLVEUR_PAR_TICK):
        if state.solveur_actif:
            avancer_solveur_une_generation(state.solveur)
            if state.solveur.meilleur_individu is not None:
                state.grille = copier_grille(state.solveur.meilleur_individu)
                state.resultat = copier_grille(state.solveur.meilleur_resultat)
                state.evolution = None
                state.evolution_index = 0
            if state.solveur.termine:
                state.solveur_actif = False
                state.recommendation_steps = construire_recommandation_steps()

    rafraichir_plateau(board)
    afficher_infos(board)

    if state.solveur_actif:
        board.after(DELAI_SOLVEUR_MS, boucle_solveur, board)


def construire_recommandation_steps():
    if state.solveur is None or state.resultat is None:
        return ""
    if state.solveur.meilleure_erreur == 0:
        return "Solution exacte trouvee pour {} steps.".format(state.k_inverse)

    manquantes, en_trop = compter_differences(state.resultat, state.cible, state.config_recherche)
    cible_vivante = max(1, nombre_cellules_vivantes(state.cible))
    moins = max(1, state.k_inverse - 1)
    plus = state.k_inverse + 1

    if manquantes >= cible_vivante / 2:
        return "Resultat imparfait : beaucoup de cellules cible manquent. Recommendation : essayer {} steps ou simplifier la cible.".format(moins)
    if en_trop > manquantes * 2 and state.solveur.meilleur_score >= 92:
        return "Resultat proche mais bruite. Recommendation : reessayer {} steps, puis tester {} steps si le bruit persiste.".format(state.k_inverse, plus)
    if state.solveur.stagnation >= 35:
        return "Forte stagnation. Recommendation : essayer {} steps ou redessiner une cible plus compacte.".format(moins)
    return "Resultat imparfait. Recommendation : relancer avec la meme valeur, puis comparer avec {} steps.".format(plus)


def lancer_ou_arreter_solveur(board):
    if state.solveur_actif:
        state.solveur_actif = False
        rafraichir_plateau(board)
        afficher_infos(board)
        return

    if state.mode_app != "resolution":
        return
    if not lire_nb_etapes_depuis_interface(board):
        rafraichir_plateau(board)
        afficher_infos(board)
        return
    if grille_vide(state.cible):
        board.console("Impossible de lancer le solveur : la cible est vide.")
        return

    state.recommendation_steps = ""
    state.evolution_active = False
    state.evolution = None
    state.evolution_index = 0
    state.evolution_id += 1
    state.solveur = initialiser_solveur(state.grille, state.cible, state.k_inverse, state.config_recherche)
    state.solveur_actif = True
    state.lecture = False
    state.vue = "initial"
    rafraichir_plateau(board)
    afficher_infos(board)
    board.after(1, boucle_solveur, board)


def remplir_initial_aleatoire(board):
    state.grille = nouvelle_grille(0, ROWS, COLS)
    for i in range(ROWS):
        for j in range(COLS):
            if random.random() < state.config_recherche.densite_initiale:
                state.grille[i][j] = 1
    state.generation_life = 0
    state.resultat = None
    state.solveur = None
    state.solveur_actif = False
    state.evolution = None
    state.evolution_active = False
    state.evolution_id += 1
    state.recommendation_steps = ""
    rafraichir_plateau(board)
    afficher_infos(board)


def tout_effacer():
    state.grille = nouvelle_grille(0, ROWS, COLS)
    state.cible = nouvelle_grille(0, ROWS, COLS)
    state.resultat = None
    state.solveur = None
    state.solveur_actif = False
    state.evolution = None
    state.evolution_index = 0
    state.evolution_active = False
    state.evolution_id += 1
    state.generation_life = 0
    state.lecture = False
    state.recommendation_steps = ""
    state.vue = "normal" if state.mode_app == "normal" else "edition"


def tout_effacer_depuis_interface(board):
    tout_effacer()
    rafraichir_plateau(board)
    afficher_infos(board)


def basculer_vue(board=None):
    if state.resultat is None:
        return
    state.evolution_active = False
    state.vue = "initial" if state.vue == "resultat" else "resultat"
    if board is not None:
        rafraichir_plateau(board)
        afficher_infos(board)


def gestion_souris(board, event):
    ligne = event["row"]
    col = event["col"]
    if not (0 <= ligne < ROWS and 0 <= col < COLS):
        return

    if state.mode_app == "normal":
        grille = state.grille
    else:
        grille = state.cible

    if event.get("button3", False):
        grille[ligne][col] = 0
    else:
        grille[ligne][col] = 1 - grille[ligne][col]

    state.resultat = None
    state.solveur = None
    state.solveur_actif = False
    state.evolution = None
    state.evolution_active = False
    state.evolution_id += 1
    state.recommendation_steps = ""
    if state.mode_app == "normal":
        state.vue = "normal"
    else:
        state.vue = "edition"

    rafraichir_plateau(board)
    afficher_infos(board)


def gestion_clavier(board, event):
    touche = event["keysym"]
    t = touche.lower()

    if t == "m":
        ui["mode_var"].set("Jeu normal" if state.mode_app == "resolution" else "Résolution")
        changer_mode(board)
    elif state.mode_app == "normal":
        if t == "space":
            lancer_ou_arreter_jeu_normal(board)
        elif t == "n":
            avancer_jeu_normal(board)
        elif t == "r":
            remplir_initial_aleatoire(board)
        elif t == "x":
            tout_effacer_depuis_interface(board)
        elif t == "escape":
            state.lecture = False
    else:
        if t == "t":
            afficher_vue(board, "edition")
        elif t == "v":
            basculer_vue(board)
        elif t == "x":
            tout_effacer_depuis_interface(board)
        elif t == "s":
            lancer_ou_arreter_solveur(board)
        elif t == "p":
            ouvrir_fenetre_population(board)
        elif t in ("up", "right"):
            state.k_inverse += 1
            synchroniser_entree_etapes()
            state.resultat = None
            state.solveur = None
            state.solveur_actif = False
            state.evolution = None
            state.evolution_active = False
            state.evolution_id += 1
        elif t in ("down", "left"):
            state.k_inverse = max(1, state.k_inverse - 1)
            synchroniser_entree_etapes()
            state.resultat = None
            state.solveur = None
            state.solveur_actif = False
            state.evolution = None
            state.evolution_active = False
            state.evolution_id += 1
        elif t == "escape":
            state.solveur_actif = False
            state.evolution_active = False

    rafraichir_plateau(board)
    afficher_infos(board)


def ouvrir_fenetre_population(board):
    root = racine_tk(board)
    if root is None or state.solveur is None or state.solveur.dernier_snapshot is None:
        return

    if ui["population_window"] is not None and ui["population_window"].winfo_exists():
        ui["population_window"].lift()
        return

    fenetre = tk.Toplevel(root)
    fenetre.title("Population genetique - individus testes")
    fenetre.configure(bg=UI_BG)
    fenetre.geometry("980x720")
    fenetre.minsize(780, 520)
    ui["population_window"] = fenetre
    ui["population_step"] = 0

    tk.Label(
        fenetre,
        text="Population courante et meilleurs de la generation precedente",
        bg=UI_BG,
        fg=TEXT_COLOR,
        font=("TkDefaultFont", 13, "bold"),
        anchor="w",
    ).pack(fill="x", padx=12, pady=(10, 4))

    canvas = tk.Canvas(fenetre, bg=UI_BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(fenetre, orient="vertical", command=canvas.yview)
    frame = tk.Frame(canvas, bg=UI_BG)
    frame.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=8)
    scrollbar.pack(side="right", fill="y", padx=(0, 12), pady=8)
    ui["population_canvas"] = canvas
    ui["population_frame"] = frame

    fenetre.protocol("WM_DELETE_WINDOW", fermer_fenetre_population)
    rafraichir_fenetre_population()
    animer_fenetre_population()


def fermer_fenetre_population():
    fenetre = ui.get("population_window")
    if fenetre is not None and fenetre.winfo_exists():
        fenetre.destroy()
    ui["population_window"] = None
    ui["population_canvas"] = None
    ui["population_frame"] = None


def animer_fenetre_population():
    fenetre = ui.get("population_window")
    if fenetre is None or not fenetre.winfo_exists():
        return
    ui["population_step"] = (ui["population_step"] + 1) % max(1, state.k_inverse + 1)
    rafraichir_fenetre_population()
    ui["population_after_id"] = fenetre.after(420, animer_fenetre_population)


def rafraichir_fenetre_population():
    frame = ui.get("population_frame")
    fenetre = ui.get("population_window")
    if frame is None or fenetre is None or not fenetre.winfo_exists():
        return
    if state.solveur is None or state.solveur.dernier_snapshot is None:
        return

    for enfant in frame.winfo_children():
        enfant.destroy()

    snapshot = state.solveur.dernier_snapshot
    titre = "Generation {} | step anime {} / {} | mutation {:.3f} | injection {:.2f} | cache {}".format(
        snapshot.generation,
        ui["population_step"],
        state.k_inverse,
        snapshot.taux_mutation,
        snapshot.taux_injection,
        snapshot.taille_cache,
    )
    tk.Label(frame, text=titre, bg=UI_BG, fg=IMPORTANT_TEXT, anchor="w").grid(row=0, column=0, columnspan=4, sticky="ew", padx=6, pady=(4, 8))

    ligne = 1
    if snapshot.meilleurs_precedents:
        tk.Label(frame, text="Meilleurs de la generation precedente", bg=UI_BG, fg="#64748b", font=("TkDefaultFont", 9, "bold"), anchor="w").grid(row=ligne, column=0, columnspan=4, sticky="ew", padx=6)
        ligne += 1
        ligne = dessiner_cartes(frame, snapshot.meilleurs_precedents[:8], ligne, colonnes=4)

    tk.Label(frame, text="Tous les individus evalues maintenant", bg=UI_BG, fg="#64748b", font=("TkDefaultFont", 9, "bold"), anchor="w").grid(row=ligne, column=0, columnspan=4, sticky="ew", padx=6, pady=(10, 0))
    ligne += 1
    dessiner_cartes(frame, snapshot.population_evaluee, ligne, colonnes=4)


def dessiner_cartes(parent, evaluations, ligne_depart, colonnes=4):
    ligne = ligne_depart
    colonne = 0
    for evaluation in evaluations:
        carte = tk.Frame(parent, bg="white", bd=1, relief=tk.SOLID)
        carte.grid(row=ligne, column=colonne, sticky="n", padx=6, pady=6)
        dessiner_carte_individu(carte, evaluation)
        colonne += 1
        if colonne >= colonnes:
            colonne = 0
            ligne += 1
    return ligne + (1 if colonne else 0)


def dessiner_carte_individu(parent, evaluation):
    header = "#{} | {} | err {:.2f} | {:.1f}% | {} cells".format(
        evaluation.rang,
        evaluation.role,
        evaluation.erreur,
        evaluation.exactitude,
        nombre_cellules_vivantes(evaluation.individu),
    )
    tk.Label(parent, text=header, bg="white", fg=TEXT_COLOR, font=("TkDefaultFont", 8), anchor="w").pack(fill="x", padx=5, pady=(4, 2))

    grille = evaluation.individu
    if ui["population_step"] > 0:
        grille = historique_evolution(evaluation.individu, min(ui["population_step"], state.k_inverse), state.config_recherche.bords_toriques)[-1]

    cell = 4
    canvas = tk.Canvas(parent, width=COLS * cell, height=ROWS * cell, bg="#f8fafc", highlightthickness=0)
    canvas.pack(padx=5, pady=(0, 5))
    for i in range(ROWS):
        for j in range(COLS):
            if grille[i][j] == 1:
                couleur = LIVE_COLOR if evaluation.resultat[i][j] == 0 else RESULT_OK
                canvas.create_rectangle(j * cell, i * cell, (j + 1) * cell, (i + 1) * cell, fill=couleur, outline="")


def initialiser(board):
    tout_effacer()
    state.mode_app = "resolution"
    state.vue = "edition"
    creer_interface(board)
    rafraichir_plateau(board)
    afficher_infos(board)
    board.console("Life Pattern Hunter pret.")
    board.console("Mode resolution : dessinez une cible, choisissez Steps, puis lancez le solveur.")


def run_app(eniseboard):
    eniseboard(
        hsize=COLS,
        vsize=ROWS,
        cell=CELL_SIZE,
        grid=True,
        title="Life Pattern Hunter",
        bgcolor=BG_COLOR,
        info=True,
        infoPlace="down",
        infoLines=4,
        console=True,
        consolePlace="down",
        init=initialiser,
        click=gestion_souris,
        key=gestion_clavier,
    )
