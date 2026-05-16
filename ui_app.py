"""Interface Eniseboard/Tkinter du chasseur de motifs du jeu de la vie."""

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
    avancer_solveur_une_generation,
)
import step_search_controller as step_controller


CELL_SIZE = 24

BG_COLOR = "#f4f7fb"
GRID_COLOR = "#d9e2ef"
LIVE_COLOR = "#2563eb"
TARGET_COLOR = "#111827"
INITIAL_AND_TARGET = "#6d5dfc"
RESULT_OK = "#16a34a"
RESULT_EXTRA = "#dc2626"
RESULT_MISSING = "#ca8a04"
TEXT_COLOR = "#172033"
IMPORTANT_TEXT = "#4f46e5"
UI_BG = "#eef3f8"
CARD_BG = "#ffffff"
BORDER_COLOR = "#d6dfeb"
BUTTON_BG = "#e8eef6"
BUTTON_HOVER_BG = "#dbe5f2"
PRIMARY_BUTTON_BG = "#166534"
PRIMARY_BUTTON_FG = "#ffffff"
SECONDARY_BUTTON_BG = "#ddeafe"
DANGER_BUTTON_BG = "#fee2e2"
DANGER_TEXT = "#991b1b"
DISCREET_TEXT = "#5b677a"
FOCUS_RING = "#93c5fd"

state = nouvel_etat()

ui = {
    "panel": None,
    "top_mode_frame": None,
    "mode_buttons": {},
    "mode_controls_frame": None,
    "normal_controls_frame": None,
    "resolution_controls_frame": None,
    "mode_var": None,
    "auto_min_steps_entry": None,
    "start_solver_button": None,
    "normal_play_button": None,
    "target_button": None,
    "target_random_button": None,
    "initial_button": None,
    "result_button": None,
    "evolution_button": None,
    "previous_button": None,
    "next_button": None,
    "progress": None,
    "progress_label": None,
    "status_label": None,
    "normal_step_button": None,
    "normal_random_button": None,
    "info_frame": None,
    "info_labels": [],
    "info_rows_shifted": False,
    "main_rows_shifted": False,
}


def racine_tk(board):
    return getattr(board, "_eniseboard__root", None)


def configurer_theme_ttk(root):
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    style.configure(".", background=UI_BG, foreground=TEXT_COLOR, font=("TkDefaultFont", 10))
    style.configure("TFrame", background=UI_BG)
    style.configure("Card.TFrame", background=CARD_BG)
    style.configure("TLabel", background=UI_BG, foreground=TEXT_COLOR)
    style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT_COLOR)
    style.configure("Muted.Card.TLabel", background=CARD_BG, foreground=DISCREET_TEXT, font=("TkDefaultFont", 8))
    style.configure("TEntry", fieldbackground="#ffffff", foreground=TEXT_COLOR, bordercolor=BORDER_COLOR, lightcolor=FOCUS_RING, darkcolor=BORDER_COLOR, padding=(8, 5))

    style.configure("TButton", background=BUTTON_BG, foreground=TEXT_COLOR, borderwidth=1, focusthickness=1, focuscolor=FOCUS_RING, padding=(12, 8), relief="flat")
    style.map("TButton", background=[("active", BUTTON_HOVER_BG), ("disabled", "#edf2f7")], foreground=[("disabled", "#94a3b8")])

    style.configure("Primary.TButton", background=PRIMARY_BUTTON_BG, foreground=PRIMARY_BUTTON_FG, font=("TkDefaultFont", 10, "bold"))
    style.map("Primary.TButton", background=[("active", "#14532d"), ("disabled", "#d1d5db")], foreground=[("disabled", "#64748b")])

    style.configure("Secondary.TButton", background=SECONDARY_BUTTON_BG, foreground=TEXT_COLOR)
    style.map("Secondary.TButton", background=[("active", "#c7d2fe"), ("disabled", "#edf2f7")])

    style.configure("Danger.TButton", background=DANGER_BUTTON_BG, foreground=DANGER_TEXT, font=("TkDefaultFont", 10, "bold"))
    style.map("Danger.TButton", background=[("active", "#fecaca"), ("disabled", "#f8fafc")], foreground=[("disabled", "#cbd5e1")])

    style.configure("Horizontal.TProgressbar", troughcolor="#e5edf6", background=IMPORTANT_TEXT, bordercolor=BORDER_COLOR, lightcolor=IMPORTANT_TEXT, darkcolor=IMPORTANT_TEXT)


def creer_bouton(parent, texte, commande, couleur=BUTTON_BG, couleur_texte=TEXT_COLOR):
    if couleur == PRIMARY_BUTTON_BG:
        style = "Primary.TButton"
    elif couleur == SECONDARY_BUTTON_BG:
        style = "Secondary.TButton"
    elif couleur == DANGER_BUTTON_BG:
        style = "Danger.TButton"
    else:
        style = "TButton"

    bouton = ttk.Button(
        parent,
        text=texte,
        command=commande,
        style=style,
        cursor="hand2",
    )
    bouton.pack(fill="x", pady=3)
    return bouton


def creer_section(parent, titre, aide=None):
    section = tk.Frame(
        parent,
        bg=CARD_BG,
        highlightbackground=BORDER_COLOR,
        highlightcolor=BORDER_COLOR,
        highlightthickness=1,
        bd=0,
    )
    section.pack(fill="x", pady=6)
    tk.Label(
        section,
        text=titre,
        bg=CARD_BG,
        fg=TEXT_COLOR,
        font=("TkDefaultFont", 10, "bold"),
        anchor="w",
    ).pack(fill="x", padx=12, pady=(10, 1))
    if aide:
        tk.Label(
            section,
            text=aide,
            bg=CARD_BG,
            fg=DISCREET_TEXT,
            font=("TkDefaultFont", 8),
            justify="left",
            wraplength=285,
            anchor="w",
        ).pack(fill="x", padx=12, pady=(0, 6))
    corps = tk.Frame(section, bg=CARD_BG)
    corps.pack(fill="x", padx=10, pady=(2, 10))
    return corps


def creer_section_simple(parent, titre):
    section = tk.Frame(
        parent,
        bg=CARD_BG,
        highlightbackground=BORDER_COLOR,
        highlightcolor=BORDER_COLOR,
        highlightthickness=1,
        bd=0,
    )
    section.pack(fill="x", pady=6)
    tk.Label(
        section,
        text=titre,
        bg=CARD_BG,
        fg=TEXT_COLOR,
        font=("TkDefaultFont", 10, "bold"),
        anchor="w",
    ).pack(fill="x", padx=12, pady=(10, 1))
    corps = tk.Frame(section, bg=CARD_BG)
    corps.pack(fill="x", padx=10, pady=(2, 10))
    return corps


def fixer_taille_fenetre(root):
    root.update_idletasks()
    largeur = max(root.winfo_reqwidth(), 980)
    hauteur = max(root.winfo_reqheight(), 760)
    root.geometry(f"{largeur}x{hauteur}")
    root.minsize(largeur, hauteur)


def afficher_ligne(board, ligne, texte, couleur=TEXT_COLOR):
    labels = ui.get("info_labels") or []
    if 0 <= ligne < len(labels):
        label = labels[ligne]
        if label is not None and label.winfo_exists():
            label.configure(text=texte, fg=couleur)
            return

    try:
        board.display(texte.ljust(140), row=ligne, col=0, color=couleur)
    except Exception:
        pass


def creer_panneau_infos(root):
    ancien = ui.get("info_frame")
    if ancien is not None and ancien.winfo_exists():
        ancien.destroy()

    if not ui["info_rows_shifted"]:
        panel = ui.get("panel")
        top_mode = ui.get("top_mode_frame")
        for widget in root.grid_slaves():
            if widget in (panel, top_mode):
                continue
            info = widget.grid_info()
            if int(info.get("column", 0)) == 0 and int(info.get("row", 0)) >= 2:
                widget.grid(row=int(info["row"]) + 1)
        ui["info_rows_shifted"] = True

    frame = tk.Frame(root, bg=UI_BG, bd=1, relief=tk.SOLID, highlightthickness=0)
    frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 6))
    frame.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)
    root.rowconfigure(2, weight=0)
    ui["info_frame"] = frame
    ui["info_labels"] = []

    for index in range(4):
        label = tk.Label(
            frame,
            text="",
            bg=UI_BG,
            fg=TEXT_COLOR,
            anchor="w",
            justify="left",
            font=("TkDefaultFont", 9),
            padx=8,
            pady=2,
        )
        label.grid(row=index, column=0, sticky="ew")
        ui["info_labels"].append(label)


def creer_barre_modes(root, board):
    if not ui["main_rows_shifted"]:
        panel = ui.get("panel")
        for widget in root.grid_slaves():
            if widget is panel:
                continue
            info = widget.grid_info()
            if int(info.get("column", 0)) == 0 and int(info.get("row", 0)) >= 0:
                widget.grid(row=int(info["row"]) + 1)
        ui["main_rows_shifted"] = True

    ancien = ui.get("top_mode_frame")
    if ancien is not None and ancien.winfo_exists():
        ancien.destroy()

    frame = tk.Frame(root, bg=UI_BG)
    frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    ui["top_mode_frame"] = frame
    ui["mode_buttons"] = {}

    ui["mode_var"] = tk.StringVar(value="Résolution")
    for colonne, (texte, valeur) in enumerate((("Résolution inverse", "Résolution"), ("Simulation libre", "Jeu normal"))):
        bouton = tk.Radiobutton(
            frame,
            text=texte,
            variable=ui["mode_var"],
            value=valeur,
            command=lambda b=board: changer_mode(b),
            indicatoron=False,
            bg=BUTTON_BG,
            fg=TEXT_COLOR,
            activebackground=BUTTON_HOVER_BG,
            activeforeground=TEXT_COLOR,
            selectcolor=SECONDARY_BUTTON_BG,
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=8,
            cursor="hand2",
            font=("TkDefaultFont", 10, "bold"),
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=IMPORTANT_TEXT,
        )
        bouton.grid(row=0, column=colonne, sticky="ew", padx=(0, 4) if colonne == 0 else (4, 0))
        ui["mode_buttons"][valeur] = bouton

    actualiser_boutons_mode()


def actualiser_boutons_mode():
    valeur_active = ui["mode_var"].get() if ui.get("mode_var") is not None else "Résolution"
    for valeur, bouton in (ui.get("mode_buttons") or {}).items():
        if bouton is None or not bouton.winfo_exists():
            continue
        actif = valeur == valeur_active
        bouton.configure(
            bg=IMPORTANT_TEXT if actif else BUTTON_BG,
            fg="#ffffff" if actif else TEXT_COLOR,
            activebackground=IMPORTANT_TEXT if actif else BUTTON_HOVER_BG,
            activeforeground="#ffffff" if actif else TEXT_COLOR,
            selectcolor=IMPORTANT_TEXT if actif else BUTTON_BG,
            highlightbackground=IMPORTANT_TEXT if actif else BORDER_COLOR,
            relief=tk.SOLID if actif else tk.FLAT,
            bd=1 if actif else 0,
        )


def definir_frame_visible(frame, visible):
    if frame is None or not frame.winfo_exists():
        return
    if visible:
        if not frame.winfo_ismapped():
            frame.pack(fill="x")
    elif frame.winfo_ismapped():
        frame.pack_forget()


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
    configurer_theme_ttk(root)
    root.columnconfigure(0, weight=0)
    root.columnconfigure(1, weight=0)
    root.rowconfigure(0, weight=0)
    root.rowconfigure(1, weight=1)
    root.rowconfigure(2, weight=0)

    if ui["panel"] is not None and ui["panel"].winfo_exists():
        ui["panel"].destroy()

    panel = tk.Frame(root, bg=UI_BG, width=340)
    panel.grid(row=0, column=1, rowspan=4, sticky="ns", padx=(8, 10), pady=10)
    panel.grid_propagate(False)
    ui["panel"] = panel

    creer_barre_modes(root, board)

    controls = tk.Frame(panel, bg=UI_BG)
    controls.pack(fill="x")
    ui["mode_controls_frame"] = controls

    normal_frame = tk.Frame(controls, bg=UI_BG)
    ui["normal_controls_frame"] = normal_frame
    normal_actions = creer_section_simple(normal_frame, "Simulation libre")
    ui["normal_play_button"] = creer_bouton(
        normal_actions,
        "Lire l'évolution du Jeu de la vie",
        lambda: lancer_ou_arreter_jeu_normal(board),
        PRIMARY_BUTTON_BG,
        PRIMARY_BUTTON_FG,
    )
    ui["normal_step_button"] = creer_bouton(normal_actions, "Avancer d'un seul passage n -> n+1", lambda: avancer_jeu_normal(board))
    ui["normal_random_button"] = creer_bouton(normal_actions, "Créer une grille initiale aléatoire", lambda: remplir_initial_aleatoire(board), SECONDARY_BUTTON_BG)

    resolution_frame = tk.Frame(controls, bg=UI_BG)
    ui["resolution_controls_frame"] = resolution_frame

    cible_section = creer_section_simple(resolution_frame, "1. Cible finale (Dessiner en cliquant sur la grille)")
    tk.Label(
        cible_section,
        text="Nombre de générations du Jeu de la vie",
        bg=CARD_BG,
        fg=TEXT_COLOR,
        font=("TkDefaultFont", 9, "bold"),
        anchor="w",
    ).pack(fill="x", pady=(8, 2))
    entree_min = ttk.Entry(
        cible_section,
        justify="center",
        style="TEntry",
    )
    entree_min.pack(fill="x", pady=(0, 2), ipady=5)
    ttk.Label(
        cible_section,
        text="Exemples : 2 ou 2-5",
        style="Muted.Card.TLabel",
        anchor="w",
    ).pack(fill="x", pady=(0, 2))
    ui["auto_min_steps_entry"] = entree_min

    recherche_section = creer_section_simple(resolution_frame, "2. Recherche génétique")
    ui["start_solver_button"] = creer_bouton(
        recherche_section,
        "Trouver une grille initiale",
        lambda: lancer_ou_arreter_solveur(board),
        PRIMARY_BUTTON_BG,
        PRIMARY_BUTTON_FG,
    )

    ui["progress"] = ttk.Progressbar(
        recherche_section,
        maximum=state.config_recherche.nb_generations_max,
        mode="determinate",
    )
    ui["progress"].pack(fill="x", pady=(8, 2))
    ui["progress_label"] = tk.Label(recherche_section, text="En attente.", bg=CARD_BG, fg=DISCREET_TEXT, anchor="w", justify="left", wraplength=285)
    ui["progress_label"].pack(fill="x")

    solution_section = creer_section_simple(resolution_frame, "3. Voir la solution")
    ui["initial_button"] = creer_bouton(solution_section, "Voir la grille initiale trouvée", lambda: afficher_vue(board, "initial"))
    ui["result_button"] = creer_bouton(solution_section, "Voir le résultat obtenu après évolution", lambda: afficher_vue(board, "resultat"))
    ui["evolution_button"] = creer_bouton(solution_section, "Rejouer l'évolution initiale -> cible", lambda: lancer_ou_arreter_evolution(board), SECONDARY_BUTTON_BG)
    ligne_navigation = tk.Frame(solution_section, bg=CARD_BG)
    ligne_navigation.pack(fill="x", pady=(3, 0))
    ligne_navigation.columnconfigure(0, weight=1)
    ligne_navigation.columnconfigure(1, weight=1)
    ui["previous_button"] = tk.Button(
        ligne_navigation,
        text="Passage précédent",
        command=lambda: deplacer_evolution(board, -1),
        bg=BUTTON_BG,
        fg=TEXT_COLOR,
        activebackground=BUTTON_HOVER_BG,
        relief=tk.FLAT,
        bd=0,
        padx=8,
        pady=8,
        cursor="hand2",
    )
    ui["previous_button"].grid(row=0, column=0, sticky="ew", padx=(0, 3))
    ui["next_button"] = tk.Button(
        ligne_navigation,
        text="Passage suivant",
        command=lambda: deplacer_evolution(board, 1),
        bg=BUTTON_BG,
        fg=TEXT_COLOR,
        activebackground=BUTTON_HOVER_BG,
        relief=tk.FLAT,
        bd=0,
        padx=8,
        pady=8,
        cursor="hand2",
    )
    ui["next_button"].grid(row=0, column=1, sticky="ew", padx=(3, 0))

    tk.Frame(panel, bg=UI_BG).pack(fill="both", expand=True)
    creer_bouton(panel, "Effacer tout le plateau", lambda: tout_effacer_depuis_interface(board), DANGER_BUTTON_BG, DANGER_TEXT)

    ui["status_label"] = None

    creer_panneau_infos(root)
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
        return "#fde047"
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
    resultat_disponible = state.resultat is not None
    resolution = state.mode_app == "resolution"

    actualiser_boutons_mode()

    definir_frame_visible(ui.get("resolution_controls_frame"), resolution)
    definir_frame_visible(ui.get("normal_controls_frame"), not resolution)

    if ui["start_solver_button"] is not None and ui["start_solver_button"].winfo_exists():
        ui["start_solver_button"].configure(
            text="Arrêter la recherche génétique" if state.solveur_actif else "Trouver une grille initiale",
            state=tk.NORMAL if resolution else tk.DISABLED,
        )

    if ui["normal_play_button"] is not None and ui["normal_play_button"].winfo_exists():
        ui["normal_play_button"].configure(
            text="Mettre la simulation en pause" if state.lecture else "Lire l'évolution du Jeu de la vie",
            state=tk.NORMAL if state.mode_app == "normal" else tk.DISABLED,
        )
    for key in ("normal_step_button", "normal_random_button"):
        bouton = ui.get(key)
        if bouton is not None and bouton.winfo_exists():
            bouton.configure(state=tk.NORMAL if state.mode_app == "normal" else tk.DISABLED)

    for key in ("target_button", "target_random_button", "initial_button", "result_button", "evolution_button", "previous_button", "next_button"):
        bouton = ui.get(key)
        if bouton is not None and bouton.winfo_exists():
            bouton.configure(state=tk.NORMAL if resolution else tk.DISABLED)

    for key in ("initial_button", "result_button", "evolution_button", "previous_button", "next_button"):
        bouton = ui.get(key)
        if bouton is not None and bouton.winfo_exists():
            bouton.configure(state=tk.NORMAL if resolution and resultat_disponible else tk.DISABLED)

    if ui["evolution_button"] is not None and ui["evolution_button"].winfo_exists():
        ui["evolution_button"].configure(
            text="Arrêter la lecture de l'évolution" if state.evolution_active else "Rejouer l'évolution initiale -> cible"
        )

    progress = ui.get("progress")
    progress_label = ui.get("progress_label")
    if progress is not None and progress.winfo_exists():
        progress["maximum"] = state.config_recherche.nb_generations_max
        progress["value"] = state.solveur.generation if state.solveur is not None else 0
    if progress_label is not None and progress_label.winfo_exists():
        if state.solveur is not None:
            s = state.solveur
            progress_label.configure(
                text="Génération génétique {} / {} | erreur {} | exactitude {:.2f}%".format(
                    s.generation,
                    s.config.nb_generations_max,
                    "?" if s.meilleure_erreur is None else f"{s.meilleure_erreur:.2f}",
                    s.meilleur_score,
                )
            )
        else:
            progress_label.configure(text="En attente.")

    status = ui.get("status_label")
    if status is not None and status.winfo_exists():
        status.configure(text=texte_status())


def texte_status():
    if state.mode_app == "normal":
        return ""

    if state.solveur_actif and state.solveur is not None:
        s = state.solveur
        auto = ""
        if state.auto_steps_actif and state.auto_steps_tentes:
            auto = " | essais steps {}/{} : {}".format(
                len(state.auto_steps_tentes),
                state.auto_steps_max_essais,
                ", ".join(str(valeur) for valeur in state.auto_steps_tentes),
            )
        return "Recherche : génération {} | stagnation {}{}.".format(
            s.generation,
            s.stagnation,
            auto,
        )

    if state.recommendation_steps:
        return state.recommendation_steps

    if state.resultat is not None:
        return "Solution disponible."

    return ""


def parser_steps_interface(texte):
    texte = texte.strip().replace("–", "-").replace("—", "-")
    if not texte:
        return [1]

    if "-" not in texte:
        valeur = int(texte)
        if valeur < 1:
            raise ValueError
        return [valeur]

    morceaux = [morceau.strip() for morceau in texte.split("-")]
    if len(morceaux) != 2 or not morceaux[0] or not morceaux[1]:
        raise ValueError

    debut = int(morceaux[0])
    fin = int(morceaux[1])
    if debut < 1 or fin < debut:
        raise ValueError
    return list(range(debut, fin + 1))


def lire_min_auto_steps_depuis_interface(board):
    entree = ui.get("auto_min_steps_entry")
    if entree is None or not entree.winfo_exists():
        state.auto_steps_min = None
        return True

    try:
        steps = parser_steps_interface(entree.get())
    except ValueError:
        board.console("Passages du Jeu de la vie invalides :", entree.get().strip())
        state.auto_steps_min = None
        state.auto_steps_plan = []
        entree.delete(0, tk.END)
        return False

    state.auto_steps_min = steps[0]
    state.auto_steps_plan = steps
    entree.delete(0, tk.END)
    entree.insert(0, str(steps[0]) if len(steps) == 1 else "{}-{}".format(steps[0], steps[-1]))
    return True


def synchroniser_entree_etapes():
    return


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
    if state.mode_app == "normal":
        afficher_ligne(board, 0, "Passage {} | cellules vivantes {}".format(state.generation_life, nombre_cellules_vivantes(state.grille)), IMPORTANT_TEXT)
        afficher_ligne(board, 1, "")
        afficher_ligne(board, 2, "")
        afficher_ligne(board, 3, "")
    else:
        if state.vue == "evolution" and state.evolution is not None:
            ligne_0 = "Lecture : passage {} / {}".format(
                state.evolution_index,
                len(state.evolution) - 1,
            )
        elif state.solveur_actif and state.solveur is not None:
            ligne_0 = "Test {} passage(s) | génération génétique {} | stagnation {}".format(
                state.k_inverse,
                state.solveur.generation,
                state.solveur.stagnation,
            )
        elif state.solveur is not None:
            erreur = "?" if state.solveur.meilleure_erreur is None else f"{state.solveur.meilleure_erreur:.2f}"
            ligne_0 = "Meilleur test : {} passage(s) | erreur {} | exactitude {:.2f}%".format(
                state.k_inverse,
                erreur,
                state.solveur.meilleur_score,
            )
        else:
            ligne_0 = "Cellules cible : {}".format(nombre_cellules_vivantes(state.cible))
        afficher_ligne(board, 0, ligne_0, IMPORTANT_TEXT)
        afficher_ligne(board, 1, state.recommendation_steps if state.recommendation_steps else "")
        afficher_ligne(board, 2, formater_stats_auto_steps() if state.auto_steps_resultats else "")
        afficher_ligne(board, 3, "")

    actualiser_interface()


def libelle_vue(vue):
    return {
        "normal": "jeu",
        "edition": "édition",
        "initial": "initiale",
        "resultat": "résultat",
        "evolution": "évolution",
    }.get(vue, vue)


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


def reinitialiser_auto_steps():
    step_controller.reinitialiser_auto_steps(state)


def generer_steps_alternatifs():
    return step_controller.generer_steps_alternatifs(state)


def stagnation_probablement_finale():
    return step_controller.stagnation_probablement_finale(state)


def enregistrer_meilleur_auto_steps():
    step_controller.enregistrer_meilleur_auto_steps(state)


def formater_stats_auto_steps(exclure_solution_exacte=False):
    return step_controller.formater_stats_auto_steps(state, exclure_solution_exacte)


def restaurer_meilleur_auto_steps():
    step_controller.restaurer_meilleur_auto_steps(state, synchroniser_entree_etapes)


def demarrer_solveur_pour_steps(steps):
    step_controller.demarrer_solveur_pour_steps(state, steps, synchroniser_entree_etapes)


def limite_essais_auto_atteinte():
    return step_controller.limite_essais_auto_atteinte(state)


def essayer_step_auto_suivant(board, raison):
    return step_controller.essayer_step_auto_suivant(
        state,
        board,
        raison,
        construire_recommandation_steps,
        synchroniser_entree_etapes,
    )


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
                enregistrer_meilleur_auto_steps()
                if state.solveur.meilleure_erreur == 0:
                    if state.auto_steps_queue:
                        essayer_step_auto_suivant(
                            board,
                            "solution exacte trouvée pour {} passages du Jeu de la vie".format(state.k_inverse),
                        )
                    else:
                        state.solveur_actif = False
                        state.auto_steps_actif = False
                        stats = formater_stats_auto_steps(exclure_solution_exacte=True)
                        suffixe = " Essais précédents : {}.".format(stats) if stats else ""
                        state.recommendation_steps = construire_recommandation_steps() + suffixe
                elif not essayer_step_auto_suivant(board, "limite atteinte pour {} passages du Jeu de la vie".format(state.k_inverse)):
                    if not state.recommendation_steps:
                        state.recommendation_steps = construire_recommandation_steps()
                break
            if stagnation_probablement_finale():
                if not state.auto_steps_queue:
                    state.auto_steps_queue = generer_steps_alternatifs()
                if state.auto_steps_queue:
                    essayer_step_auto_suivant(
                        board,
                        "stagnation probable avant la limite pour {} passages du Jeu de la vie".format(state.k_inverse),
                    )
                    break

    rafraichir_plateau(board)
    afficher_infos(board)

    if state.solveur_actif:
        board.after(DELAI_SOLVEUR_MS, boucle_solveur, board)


def construire_recommandation_steps():
    return step_controller.construire_recommandation_steps(state)


def lancer_ou_arreter_solveur(board):
    if state.solveur_actif:
        state.solveur_actif = False
        reinitialiser_auto_steps()
        rafraichir_plateau(board)
        afficher_infos(board)
        return

    if state.mode_app != "resolution":
        return
    if not lire_min_auto_steps_depuis_interface(board):
        rafraichir_plateau(board)
        afficher_infos(board)
        return
    steps_plan = state.auto_steps_plan[:]
    if grille_vide(state.cible):
        board.console("Impossible de lancer le solveur : la cible est vide.")
        return

    state.recommendation_steps = ""
    reinitialiser_auto_steps()
    state.auto_steps_plan = steps_plan or [1]
    state.auto_steps_min = state.auto_steps_plan[0]
    state.k_inverse = state.auto_steps_plan[0]
    state.auto_steps_actif = True
    state.auto_steps_depart = state.k_inverse
    state.auto_steps_max_essais = len(state.auto_steps_plan)
    state.auto_steps_queue = state.auto_steps_plan[1:]
    state.evolution_active = False
    state.evolution = None
    state.evolution_index = 0
    state.evolution_id += 1
    demarrer_solveur_pour_steps(state.k_inverse)
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
    reinitialiser_auto_steps()
    state.evolution = None
    state.evolution_active = False
    state.evolution_id += 1
    state.recommendation_steps = ""
    rafraichir_plateau(board)
    afficher_infos(board)


def remplir_cible_aleatoire(board):
    if state.mode_app != "resolution":
        return

    state.cible = nouvelle_grille(0, ROWS, COLS)
    for i in range(ROWS):
        for j in range(COLS):
            if random.random() < state.config_recherche.densite_initiale:
                state.cible[i][j] = 1

    state.resultat = None
    state.solveur = None
    state.solveur_actif = False
    reinitialiser_auto_steps()
    state.evolution = None
    state.evolution_index = 0
    state.evolution_active = False
    state.evolution_id += 1
    state.recommendation_steps = ""
    state.vue = "edition"
    rafraichir_plateau(board)
    afficher_infos(board)


def tout_effacer():
    state.grille = nouvelle_grille(0, ROWS, COLS)
    state.cible = nouvelle_grille(0, ROWS, COLS)
    state.resultat = None
    state.solveur = None
    state.solveur_actif = False
    reinitialiser_auto_steps()
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
    if state.mode_app == "resolution" and state.solveur_actif:
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
    reinitialiser_auto_steps()
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
        elif t == "e":
            lancer_ou_arreter_evolution(board)
        elif t == "escape":
            state.solveur_actif = False
            state.evolution_active = False
            reinitialiser_auto_steps()

    rafraichir_plateau(board)
    afficher_infos(board)


def initialiser(board):
    tout_effacer()
    state.mode_app = "resolution"
    state.vue = "edition"
    creer_interface(board)
    rafraichir_plateau(board)
    afficher_infos(board)
    board.console("Chasseur de motifs du jeu de la vie prêt.")
    board.console("Mode résolution : dessinez une cible, indiquez les passages si besoin, puis lancez la recherche.")


def run_app(eniseboard):
    eniseboard(
        hsize=COLS,
        vsize=ROWS,
        cell=CELL_SIZE,
        grid=True,
        title="Chasseur de motifs du jeu de la vie",
        bgcolor=BG_COLOR,
        info=False,
        infoPlace="down",
        infoLines=0,
        console=True,
        consolePlace="down",
        init=initialiser,
        click=gestion_souris,
        key=gestion_clavier,
    )
