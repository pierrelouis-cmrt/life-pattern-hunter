"""Interface Eniseboard/Tkinter de la version simplifiée."""

import random
import tkinter as tk
from tkinter import ttk

try:
    from .app_state import (
        DELAI_EVOLUTION_MS,
        DELAI_SOLVEUR_MS,
        NB_ITERATIONS_SOLVEUR_PAR_TICK,
        nouvel_etat,
    )
    from .life_rules import (
        COLS,
        ROWS,
        copier_grille,
        grille_vide,
        historique_evolution,
        nombre_cellules_vivantes,
        nouvelle_grille,
        generation_suivante,
    )
    from .simple_genetic_algorithm import (
        avancer_solveur_une_generation,
        initialiser_solveur,
        taille_zone,
    )
except ImportError:
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
    from simple_genetic_algorithm import (
        avancer_solveur_une_generation,
        initialiser_solveur,
        taille_zone,
    )


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
    "steps_entry": None,
    "start_solver_button": None,
    "normal_play_button": None,
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
    "target_random_button": None,
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

    bouton = ttk.Button(parent, text=texte, command=commande, style=style, cursor="hand2")
    bouton.pack(fill="x", pady=3)
    return bouton


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

    if board is None:
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

    cible_section = creer_section_simple(resolution_frame, "1. Cible finale")
    tk.Label(
        cible_section,
        text="Nombre de passages à tester",
        bg=CARD_BG,
        fg=TEXT_COLOR,
        font=("TkDefaultFont", 9, "bold"),
        anchor="w",
    ).pack(fill="x", pady=(8, 2))
    entree_steps = ttk.Entry(cible_section, justify="center", style="TEntry")
    entree_steps.insert(0, str(state.k_inverse))
    entree_steps.pack(fill="x", pady=(0, 2), ipady=5)
    ui["steps_entry"] = entree_steps
    ui["target_random_button"] = creer_bouton(cible_section, "Créer une cible aléatoire", lambda: remplir_cible_aleatoire(board), SECONDARY_BUTTON_BG)

    recherche_section = creer_section_simple(resolution_frame, "2. Recherche génétique simplifiée")
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
    if board is None:
        return
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

    bouton = ui.get("start_solver_button")
    if bouton is not None and bouton.winfo_exists():
        bouton.configure(
            text="Arrêter la recherche génétique" if state.solveur_actif else "Trouver une grille initiale",
            state=tk.NORMAL if resolution else tk.DISABLED,
        )

    bouton = ui.get("normal_play_button")
    if bouton is not None and bouton.winfo_exists():
        bouton.configure(
            text="Mettre la simulation en pause" if state.lecture else "Lire l'évolution du Jeu de la vie",
            state=tk.NORMAL if state.mode_app == "normal" else tk.DISABLED,
        )

    for key in ("normal_step_button", "normal_random_button"):
        bouton = ui.get(key)
        if bouton is not None and bouton.winfo_exists():
            bouton.configure(state=tk.NORMAL if state.mode_app == "normal" else tk.DISABLED)

    for key in ("target_random_button", "initial_button", "result_button", "evolution_button", "previous_button", "next_button"):
        bouton = ui.get(key)
        if bouton is not None and bouton.winfo_exists():
            bouton.configure(state=tk.NORMAL if resolution else tk.DISABLED)

    for key in ("initial_button", "result_button", "evolution_button", "previous_button", "next_button"):
        bouton = ui.get(key)
        if bouton is not None and bouton.winfo_exists():
            bouton.configure(state=tk.NORMAL if resolution and resultat_disponible else tk.DISABLED)

    bouton = ui.get("evolution_button")
    if bouton is not None and bouton.winfo_exists():
        bouton.configure(text="Arrêter la lecture de l'évolution" if state.evolution_active else "Rejouer l'évolution initiale -> cible")

    progress = ui.get("progress")
    progress_label = ui.get("progress_label")
    if progress is not None and progress.winfo_exists():
        progress["maximum"] = state.config_recherche.nb_generations_max
        progress["value"] = state.solveur.generation if state.solveur is not None else 0
    if progress_label is not None and progress_label.winfo_exists():
        if state.solveur is not None:
            s = state.solveur
            details = ""
            if s.dernier_snapshot is not None:
                details = " | mutation {:.1f}% | zone {} cases".format(
                    s.dernier_snapshot.taux_mutation * 100,
                    taille_zone(s.dernier_snapshot.zone),
                )
            progress_label.configure(
                text="Génération génétique {} / {} | erreur {} | exactitude {:.2f}%{}".format(
                    s.generation,
                    s.config.nb_generations_max,
                    "?" if s.meilleure_erreur is None else f"{s.meilleure_erreur:.2f}",
                    s.meilleur_score,
                    details,
                )
            )
        else:
            progress_label.configure(text="En attente.")


def texte_status():
    if state.mode_app == "normal":
        return ""

    if state.solveur_actif and state.solveur is not None:
        s = state.solveur
        return "Recherche : {} passage(s), génération {} | stagnation {}.".format(
            state.k_inverse,
            s.generation,
            s.stagnation,
        )

    if state.message_recherche:
        return state.message_recherche

    if state.resultat is not None:
        return "Solution disponible."

    return ""


def parser_steps_interface(texte):
    texte = texte.strip()
    if not texte:
        return 1
    if any(separateur in texte for separateur in ("-", "–", "—")):
        raise ValueError
    valeur = int(texte)
    if valeur < 1:
        raise ValueError
    return valeur


def lire_steps_depuis_interface(board):
    entree = ui.get("steps_entry")
    texte = entree.get() if entree is not None and entree.winfo_exists() else str(state.k_inverse)
    try:
        state.k_inverse = parser_steps_interface(texte)
    except ValueError:
        if board is not None:
            board.console("Nombre de passages invalide : entrez une seule valeur entière positive.")
        state.message_recherche = "Nombre de passages invalide."
        return False
    return True


def afficher_infos(board):
    if state.mode_app == "normal":
        afficher_ligne(board, 0, "Passage {} | cellules vivantes {}".format(state.generation_life, nombre_cellules_vivantes(state.grille)), IMPORTANT_TEXT)
        afficher_ligne(board, 1, "")
        afficher_ligne(board, 2, "")
        afficher_ligne(board, 3, "")
    else:
        if state.vue == "evolution" and state.evolution is not None:
            ligne_0 = "Lecture : passage {} / {}".format(state.evolution_index, len(state.evolution) - 1)
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
        afficher_ligne(board, 1, texte_status())
        if state.solveur is not None:
            mutation = state.config_recherche.taux_mutation
            if state.solveur.dernier_snapshot is not None:
                mutation = state.solveur.dernier_snapshot.taux_mutation
            afficher_ligne(
                board,
                2,
                "Zone active : {} cases | mutation courante {:.1f}% | nouveaux aléatoires {:.0f}%".format(
                    taille_zone(state.solveur.zone),
                    mutation * 100,
                    state.config_recherche.fraction_nouveaux_aleatoires * 100,
                ),
            )
        else:
            afficher_ligne(board, 2, "Algo simplifié : zone active, élites, croisements, mutations.")
        afficher_ligne(board, 3, "")

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
        if not state.solveur_actif:
            break
        avancer_solveur_une_generation(state.solveur)
        if state.solveur.meilleur_individu is not None:
            state.grille = copier_grille(state.solveur.meilleur_individu)
            state.resultat = copier_grille(state.solveur.meilleur_resultat)
            state.evolution = None
            state.evolution_index = 0

        if state.solveur.termine:
            state.solveur_actif = False
            if state.solveur.meilleure_erreur == 0:
                state.message_recherche = "Solution exacte trouvée pour {} passage(s).".format(state.k_inverse)
            else:
                state.message_recherche = "Limite atteinte pour {} passage(s), meilleur résultat conservé.".format(state.k_inverse)
            break

    rafraichir_plateau(board)
    afficher_infos(board)

    if state.solveur_actif:
        board.after(DELAI_SOLVEUR_MS, boucle_solveur, board)


def lancer_ou_arreter_solveur(board):
    if state.solveur_actif:
        state.solveur_actif = False
        rafraichir_plateau(board)
        afficher_infos(board)
        return

    if state.mode_app != "resolution":
        return
    if not lire_steps_depuis_interface(board):
        rafraichir_plateau(board)
        afficher_infos(board)
        return
    if grille_vide(state.cible):
        if board is not None:
            board.console("Impossible de lancer le solveur : la cible est vide.")
        state.message_recherche = "Impossible de lancer le solveur : la cible est vide."
        afficher_infos(board)
        return

    state.message_recherche = ""
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
    state.message_recherche = ""
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
    state.evolution = None
    state.evolution_index = 0
    state.evolution_active = False
    state.evolution_id += 1
    state.message_recherche = ""
    state.vue = "edition"
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
    state.message_recherche = ""
    state.vue = "normal" if state.mode_app == "normal" else "edition"


def tout_effacer_depuis_interface(board):
    tout_effacer()
    rafraichir_plateau(board)
    afficher_infos(board)


def afficher_vue(board, vue):
    if vue in ("initial", "resultat") and state.resultat is None:
        return
    state.evolution_active = False
    state.vue = vue
    rafraichir_plateau(board)
    afficher_infos(board)


def lancer_ou_arreter_evolution(board):
    if state.resultat is None:
        return

    if state.evolution_active:
        state.evolution_active = False
        afficher_infos(board)
        return

    state.evolution = historique_evolution(state.grille, state.k_inverse, state.config_recherche.bords_toriques)
    state.evolution_index = 0
    state.evolution_active = True
    state.vue = "evolution"
    state.evolution_id += 1
    identifiant = state.evolution_id
    avancer_evolution(board, identifiant)


def avancer_evolution(board, identifiant):
    if not state.evolution_active or state.evolution is None or identifiant != state.evolution_id:
        return

    state.vue = "evolution"
    rafraichir_plateau(board)
    afficher_infos(board)

    if state.evolution_index >= len(state.evolution) - 1:
        state.evolution_active = False
        afficher_infos(board)
        return

    state.evolution_index += 1
    board.after(DELAI_EVOLUTION_MS, avancer_evolution, board, identifiant)


def deplacer_evolution(board, delta):
    if state.evolution is None:
        if state.resultat is None:
            return
        state.evolution = historique_evolution(state.grille, state.k_inverse, state.config_recherche.bords_toriques)
        state.evolution_index = 0

    state.evolution_active = False
    state.evolution_index = max(0, min(len(state.evolution) - 1, state.evolution_index + delta))
    state.vue = "evolution"
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

    grille = state.grille if state.mode_app == "normal" else state.cible
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
    state.message_recherche = ""
    state.vue = "normal" if state.mode_app == "normal" else "edition"

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

    rafraichir_plateau(board)
    afficher_infos(board)


def initialiser(board):
    tout_effacer()
    state.mode_app = "resolution"
    state.vue = "edition"
    creer_interface(board)
    rafraichir_plateau(board)
    afficher_infos(board)
    board.console("Version simplifiée prête.")
    board.console("Dessinez une cible, choisissez un nombre de passages, puis lancez la recherche.")


def run_app(eniseboard):
    eniseboard(
        hsize=COLS,
        vsize=ROWS,
        cell=CELL_SIZE,
        grid=True,
        title="Chasseur de motifs simplifié",
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
