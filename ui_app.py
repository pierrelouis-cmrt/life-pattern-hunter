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
    compter_differences,
    avancer_solveur_une_generation,
    detecter_periode_simple,
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
    "info_frame": None,
    "info_labels": [],
    "info_rows_shifted": False,
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
        for widget in root.grid_slaves():
            if widget is panel:
                continue
            info = widget.grid_info()
            if int(info.get("column", 0)) == 0 and int(info.get("row", 0)) >= 1:
                widget.grid(row=int(info["row"]) + 1)
        ui["info_rows_shifted"] = True

    frame = tk.Frame(root, bg=UI_BG, bd=1, relief=tk.SOLID, highlightthickness=0)
    frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
    frame.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=0)
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
    root.columnconfigure(0, weight=0)
    root.columnconfigure(1, weight=0)
    root.rowconfigure(0, weight=1)

    if ui["panel"] is not None and ui["panel"].winfo_exists():
        ui["panel"].destroy()

    panel = tk.Frame(root, bg=UI_BG, width=285)
    panel.grid(row=0, column=1, rowspan=4, sticky="ns", padx=(8, 10), pady=10)
    panel.grid_propagate(False)
    ui["panel"] = panel

    tk.Label(
        panel,
        text="Chasseur de motifs du jeu de la vie",
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

    controls = tk.Frame(panel, bg=UI_BG)
    controls.pack(fill="x")
    ui["mode_controls_frame"] = controls

    normal_frame = tk.Frame(controls, bg=UI_BG)
    ui["normal_controls_frame"] = normal_frame
    creer_titre_section(normal_frame, "Jeu normal")
    ui["normal_play_button"] = creer_bouton(normal_frame, "Lire / pause", lambda: lancer_ou_arreter_jeu_normal(board), PRIMARY_BUTTON_BG)
    ui["normal_step_button"] = creer_bouton(normal_frame, "Avancer d'une génération", lambda: avancer_jeu_normal(board))
    ui["normal_random_button"] = creer_bouton(normal_frame, "Grille aléatoire", lambda: remplir_initial_aleatoire(board))

    resolution_frame = tk.Frame(controls, bg=UI_BG)
    ui["resolution_controls_frame"] = resolution_frame
    creer_titre_section(resolution_frame, "Résolution")
    tk.Label(resolution_frame, text="Minimum de générations (vide = 1)", bg=UI_BG, fg=TEXT_COLOR, anchor="w").pack(fill="x", padx=8)
    entree_min = tk.Entry(resolution_frame, justify="center")
    entree_min.pack(fill="x", padx=8, pady=(2, 8))
    ui["auto_min_steps_entry"] = entree_min

    ui["start_solver_button"] = creer_bouton(resolution_frame, "Lancer le solveur", lambda: lancer_ou_arreter_solveur(board), PRIMARY_BUTTON_BG)
    ui["target_button"] = creer_bouton(resolution_frame, "Modifier la cible", lambda: afficher_vue(board, "edition"))
    ui["target_random_button"] = creer_bouton(resolution_frame, "Grille finale aléatoire", lambda: remplir_cible_aleatoire(board))
    ui["initial_button"] = creer_bouton(resolution_frame, "Meilleure grille initiale", lambda: afficher_vue(board, "initial"))
    ui["result_button"] = creer_bouton(resolution_frame, "Afficher le résultat", lambda: afficher_vue(board, "resultat"))
    ui["evolution_button"] = creer_bouton(resolution_frame, "Lire l'évolution", lambda: lancer_ou_arreter_evolution(board))
    ui["previous_button"] = creer_bouton(resolution_frame, "Génération précédente", lambda: deplacer_evolution(board, -1))
    ui["next_button"] = creer_bouton(resolution_frame, "Génération suivante", lambda: deplacer_evolution(board, 1))
    ui["population_button"] = creer_bouton(resolution_frame, "Voir population", lambda: ouvrir_fenetre_population(board))

    ui["progress"] = ttk.Progressbar(
        resolution_frame,
        maximum=state.config_recherche.nb_generations_max,
        mode="determinate",
    )
    ui["progress"].pack(fill="x", padx=8, pady=(8, 2))
    ui["progress_label"] = tk.Label(resolution_frame, text="Progression en attente.", bg=UI_BG, fg=DISCREET_TEXT, anchor="w")
    ui["progress_label"].pack(fill="x", padx=8)

    creer_titre_section(panel, "Réinitialisation")
    creer_bouton(panel, "Effacer", lambda: tout_effacer_depuis_interface(board), DANGER_BUTTON_BG)

    ui["status_label"] = tk.Label(
        panel,
        text="Dessinez une cible, choisissez le minimum de générations si besoin, puis lancez le solveur.",
        bg=UI_BG,
        fg=DISCREET_TEXT,
        justify="left",
        wraplength=250,
        anchor="w",
    )
    ui["status_label"].pack(fill="x", padx=8, pady=(12, 0))

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

    definir_frame_visible(ui.get("resolution_controls_frame"), resolution)
    definir_frame_visible(ui.get("normal_controls_frame"), not resolution)

    if ui["start_solver_button"] is not None and ui["start_solver_button"].winfo_exists():
        ui["start_solver_button"].configure(
            text="Arrêter le solveur" if state.solveur_actif else "Lancer le solveur",
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

    for key in ("target_button", "target_random_button", "initial_button", "result_button", "evolution_button", "previous_button", "next_button"):
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
        ui["evolution_button"].configure(text="Arrêter l'évolution" if state.evolution_active else "Lire l'évolution")

    progress = ui.get("progress")
    progress_label = ui.get("progress_label")
    if progress is not None and progress.winfo_exists():
        progress["maximum"] = state.config_recherche.nb_generations_max
        progress["value"] = state.solveur.generation if state.solveur is not None else 0
    if progress_label is not None and progress_label.winfo_exists():
        if state.solveur is not None:
            s = state.solveur
            progress_label.configure(
                text="Génération {} / {} | erreur {} | exactitude {:.2f}%".format(
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


def texte_status():
    if state.mode_app == "normal":
        return "Mode jeu normal : dessinez une grille initiale, puis lancez ou avancez l'évolution."

    if state.solveur_actif and state.solveur is not None:
        s = state.solveur
        auto = ""
        if state.auto_steps_actif and state.auto_steps_tentes:
            auto = " | essais steps {}/{} : {}".format(
                len(state.auto_steps_tentes),
                state.auto_steps_max_essais,
                ", ".join(str(valeur) for valeur in state.auto_steps_tentes),
            )
        return "Recherche active. Stagnation {} | mémoire cache {} | zone {}{}.".format(
            s.stagnation,
            len(s.cache),
            s.zone,
            auto,
        )

    if state.recommendation_steps:
        return state.recommendation_steps

    if state.resultat is not None:
        return "Meilleure grille initiale disponible. Inspectez le résultat ou l'évolution."

    return "Mode résolution : dessinez la cible finale, choisissez le minimum de générations si besoin, puis lancez le solveur."


def lire_min_auto_steps_depuis_interface(board):
    entree = ui.get("auto_min_steps_entry")
    if entree is None or not entree.winfo_exists():
        state.auto_steps_min = None
        return True

    texte = entree.get().strip()
    if not texte:
        state.auto_steps_min = None
        return True

    try:
        valeur = int(texte)
    except ValueError:
        board.console("Minimum de générations invalide :", texte)
        state.auto_steps_min = None
        entree.delete(0, tk.END)
        return False

    if valeur < 1:
        board.console("Le minimum de générations doit être vide ou supérieur à 0.")
        state.auto_steps_min = None
        entree.delete(0, tk.END)
        return False

    state.auto_steps_min = valeur
    entree.delete(0, tk.END)
    entree.insert(0, str(valeur))
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
    mode = "JEU NORMAL" if state.mode_app == "normal" else "RÉSOLUTION"
    afficher_ligne(
        board,
        0,
        "Mode : {} | Vue : {} | génération testée : {} | cellules cible : {}".format(
            mode,
            libelle_vue(state.vue).upper(),
            state.k_inverse,
            nombre_cellules_vivantes(state.cible),
        ),
        IMPORTANT_TEXT,
    )

    if state.mode_app == "normal":
        afficher_ligne(board, 1, "Jeu normal : clic gauche pour inverser une cellule. Utilisez Lire/pause ou Avancer.")
        afficher_ligne(board, 2, "Touches : Espace lecture/pause | N avancer | R aléatoire | X effacer | M mode")
        afficher_ligne(board, 3, "Génération du jeu : {} | cellules vivantes : {}".format(state.generation_life, nombre_cellules_vivantes(state.grille)), IMPORTANT_TEXT)
    else:
        if state.vue == "evolution" and state.evolution is not None:
            ligne_1 = "Étape d'évolution {} / {} : bleu=courant, violet=cible atteinte, orange=cible manquante.".format(
                state.evolution_index,
                len(state.evolution) - 1,
            )
        else:
            ligne_1 = "Dessinez la grille finale souhaitée, réglez le minimum de générations si besoin, puis lancez le solveur."
        afficher_ligne(board, 1, ligne_1)
        afficher_ligne(board, 2, "Touches : S résoudre | V résultat/initiale | T cible | P population | X effacer")

        if state.solveur is not None:
            s = state.solveur
            afficher_ligne(
                board,
                3,
                "{} | génération {} | erreur {} | exactitude {:.2f}% | stagnation {}".format(
                    "Recherche en cours" if state.solveur_actif else "Recherche arrêtée",
                    s.generation,
                    "?" if s.meilleure_erreur is None else f"{s.meilleure_erreur:.2f}",
                    s.meilleur_score,
                    s.stagnation,
                ),
                IMPORTANT_TEXT,
            )
        else:
            afficher_ligne(board, 3, "Cellules initiales vivantes : {} | cellules finales souhaitées : {}".format(nombre_cellules_vivantes(state.grille), nombre_cellules_vivantes(state.cible)))

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
    state.auto_steps_actif = False
    state.auto_steps_queue = []
    state.auto_steps_tentes = []
    state.auto_steps_resultats = []
    state.auto_steps_depart = 0
    state.auto_steps_best = None


def generer_steps_alternatifs():
    minimum = state.auto_steps_min or 1
    deja_vus = set(state.auto_steps_tentes)
    essais_restants = max(0, state.auto_steps_max_essais - len(state.auto_steps_tentes))
    steps = []
    valeur = minimum

    while len(steps) < essais_restants:
        if valeur in deja_vus:
            valeur += 1
            continue

        steps.append(valeur)
        valeur += 1

    return steps


def stagnation_probablement_finale():
    if state.solveur is None:
        return False

    s = state.solveur
    if s.meilleure_erreur in (None, 0):
        return False

    cible_vivante = nombre_cellules_vivantes(state.cible)
    seuil_stagnation = 75 if cible_vivante <= state.config_recherche.seuil_cible_clairesemee else 95
    generation_min = max(60, seuil_stagnation)
    reste = s.config.nb_generations_max - s.generation

    return (
        s.generation >= generation_min
        and s.stagnation >= seuil_stagnation
        and reste >= 20
    )


def enregistrer_meilleur_auto_steps():
    if state.solveur is None or state.solveur.meilleur_individu is None:
        return

    erreur = float("inf") if state.solveur.meilleure_erreur is None else state.solveur.meilleure_erreur
    note = float("inf") if state.solveur.meilleure_note_tri is None else state.solveur.meilleure_note_tri
    stats = {
        "steps": state.k_inverse,
        "generation": state.solveur.generation,
        "erreur": erreur,
        "note": note,
        "exactitude": state.solveur.meilleur_score,
        "stagnation": state.solveur.stagnation,
        "cellules": nombre_cellules_vivantes(state.solveur.meilleur_individu),
    }
    for index, item in enumerate(state.auto_steps_resultats):
        if item["steps"] == state.k_inverse:
            state.auto_steps_resultats[index] = stats
            break
    else:
        state.auto_steps_resultats.append(stats)

    meilleur = state.auto_steps_best
    if meilleur is None or (erreur, note) < (meilleur["erreur"], meilleur["note"]):
        state.auto_steps_best = {
            "steps": state.k_inverse,
            "solveur": state.solveur,
            "erreur": erreur,
            "note": note,
        }


def formater_stats_auto_steps(exclure_solution_exacte=False):
    if not state.auto_steps_resultats:
        return ""

    resultats = sorted(state.auto_steps_resultats, key=lambda item: (item["erreur"], item["note"]))
    if exclure_solution_exacte:
        resultats = [item for item in resultats if item["erreur"] != 0]

    morceaux = []
    for item in resultats[:state.auto_steps_max_essais]:
        erreur = "?" if item["erreur"] == float("inf") else "{:.2f}".format(item["erreur"])
        morceaux.append(
            "{}g: err {}, {:.1f}%, {} cellules, stagn {}".format(
                item["steps"],
                erreur,
                item["exactitude"],
                item["cellules"],
                item["stagnation"],
            )
        )

    return " | ".join(morceaux)


def restaurer_meilleur_auto_steps():
    meilleur = state.auto_steps_best
    if meilleur is None:
        return

    state.k_inverse = meilleur["steps"]
    synchroniser_entree_etapes()
    state.solveur = meilleur["solveur"]
    if state.solveur.meilleur_individu is not None:
        state.grille = copier_grille(state.solveur.meilleur_individu)
        state.resultat = copier_grille(state.solveur.meilleur_resultat)
        state.evolution = None
        state.evolution_index = 0


def demarrer_solveur_pour_steps(steps):
    state.k_inverse = steps
    synchroniser_entree_etapes()
    state.solveur = initialiser_solveur(state.grille, state.cible, state.k_inverse, state.config_recherche)
    state.solveur_actif = True
    state.lecture = False
    state.vue = "initial"
    if steps not in state.auto_steps_tentes:
        state.auto_steps_tentes.append(steps)


def limite_essais_auto_atteinte():
    return len(state.auto_steps_tentes) >= state.auto_steps_max_essais


def essayer_step_auto_suivant(board, raison):
    if not state.auto_steps_actif:
        return False

    enregistrer_meilleur_auto_steps()
    if limite_essais_auto_atteinte():
        state.auto_steps_queue = []
        restaurer_meilleur_auto_steps()
        state.solveur_actif = False
        state.auto_steps_actif = False
        stats = formater_stats_auto_steps()
        suffixe = " Stats essais : {}.".format(stats) if stats else ""
        state.recommendation_steps = "Auto-steps arrêté après {} essais maximum. Meilleur essai conservé : {} générations.{}".format(
            state.auto_steps_max_essais,
            state.k_inverse,
            suffixe,
        )
        return False

    if not state.auto_steps_queue:
        state.auto_steps_queue = generer_steps_alternatifs()

    while state.auto_steps_queue:
        prochain = state.auto_steps_queue.pop(0)
        if prochain in state.auto_steps_tentes:
            continue
        if hasattr(board, "console"):
            board.console("Auto-steps : stagnation détectée, essai avec {} générations.".format(prochain))
        demarrer_solveur_pour_steps(prochain)
        state.recommendation_steps = "Auto-steps : {}. Essais en cours : {}.".format(
            raison,
            ", ".join(str(valeur) for valeur in state.auto_steps_tentes),
        )
        return True

    restaurer_meilleur_auto_steps()
    state.solveur_actif = False
    state.auto_steps_actif = False
    stats = formater_stats_auto_steps()
    suffixe = " Stats essais : {}.".format(stats) if stats else ""
    state.recommendation_steps = "{} Aucun autre nombre de générations n'a amélioré la recherche. Meilleur essai conservé : {} générations.".format(
        construire_recommandation_steps(),
        state.k_inverse,
    ) + suffixe
    return False


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
                    state.solveur_actif = False
                    state.auto_steps_actif = False
                    stats = formater_stats_auto_steps(exclure_solution_exacte=True)
                    suffixe = " Essais précédents : {}.".format(stats) if stats else ""
                    state.recommendation_steps = construire_recommandation_steps() + suffixe
                elif not essayer_step_auto_suivant(board, "limite atteinte pour {} générations".format(state.k_inverse)):
                    if not state.recommendation_steps:
                        state.recommendation_steps = construire_recommandation_steps()
                break
            if stagnation_probablement_finale():
                if not state.auto_steps_queue:
                    state.auto_steps_queue = generer_steps_alternatifs()
                if state.auto_steps_queue:
                    essayer_step_auto_suivant(
                        board,
                        "stagnation probable avant la limite pour {} générations".format(state.k_inverse),
                    )
                    break

    rafraichir_plateau(board)
    afficher_infos(board)

    if state.solveur_actif:
        board.after(DELAI_SOLVEUR_MS, boucle_solveur, board)


def construire_recommandation_steps():
    if state.solveur is None or state.resultat is None:
        return ""
    if state.solveur.meilleure_erreur == 0:
        return "Solution exacte trouvée pour {} générations.".format(state.k_inverse)

    manquantes, en_trop = compter_differences(state.resultat, state.cible, state.config_recherche)
    cible_vivante = max(1, nombre_cellules_vivantes(state.cible))
    voisins = sorted(set([
        max(1, state.k_inverse - 2),
        max(1, state.k_inverse - 1),
        state.k_inverse,
        state.k_inverse + 1,
        state.k_inverse + 2,
    ]))
    voisins_texte = ", ".join(str(valeur) for valeur in voisins)
    periode = detecter_periode_simple(state.cible, state.config_recherche)

    if cible_vivante <= state.config_recherche.seuil_cible_clairesemee and state.solveur.stagnation >= 35:
        valeurs = [1, 2, 3, 4, 5, 6, 8]
        if periode:
            return "Cible très petite et stagnation forte (période {}). Recommandation : tester {} générations.".format(
                periode,
                ", ".join(str(valeur) for valeur in valeurs),
            )
        return "Cible très petite et stagnation forte. Recommandation : tester {} générations.".format(
            ", ".join(str(valeur) for valeur in valeurs)
        )

    if periode:
        compatibles = [
            valeur for valeur in voisins
            if valeur % periode == state.k_inverse % periode
        ]
        if compatibles:
            return "Cible périodique détectée (période {}). Recommandation : comparer {} générations.".format(
                periode,
                ", ".join(str(valeur) for valeur in compatibles),
            )

    if manquantes >= cible_vivante / 2:
        valeurs = sorted(set([max(1, state.k_inverse - 3), max(1, state.k_inverse - 2), max(1, state.k_inverse - 1)]))
        return "Résultat imparfait : beaucoup de cellules cible manquent. Recommandation : essayer {} générations.".format(
            ", ".join(str(valeur) for valeur in valeurs)
        )
    if en_trop > manquantes * 2 and state.solveur.meilleur_score >= 92:
        return "Résultat proche mais bruité. Recommandation : réessayer {} générations, puis comparer avec {} et {}.".format(
            state.k_inverse,
            max(1, state.k_inverse - 1),
            state.k_inverse + 1,
        )
    if state.solveur.stagnation >= 35:
        return "Forte stagnation. Recommandation : essayer {} générations ou rendre la cible plus compacte.".format(voisins_texte)
    return "Résultat imparfait. Recommandation : relancer avec {}, puis comparer avec {} générations.".format(
        state.k_inverse,
        voisins_texte,
    )


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
    if grille_vide(state.cible):
        board.console("Impossible de lancer le solveur : la cible est vide.")
        return

    state.recommendation_steps = ""
    reinitialiser_auto_steps()
    state.k_inverse = state.auto_steps_min or 1
    state.auto_steps_actif = True
    state.auto_steps_depart = state.k_inverse
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
        elif t == "p":
            ouvrir_fenetre_population(board)
        elif t == "escape":
            state.solveur_actif = False
            state.evolution_active = False
            reinitialiser_auto_steps()

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
    fenetre.title("Population génétique - échantillon pédagogique")
    fenetre.configure(bg=UI_BG)
    fenetre.geometry("1080x760")
    fenetre.minsize(900, 560)
    ui["population_window"] = fenetre
    ui["population_step"] = 0

    tk.Label(
        fenetre,
        text="Échantillon de la population génétique",
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
    after_id = ui.get("population_after_id")
    if fenetre is not None and fenetre.winfo_exists() and after_id is not None:
        try:
            fenetre.after_cancel(after_id)
        except tk.TclError:
            pass
    if fenetre is not None and fenetre.winfo_exists():
        fenetre.destroy()
    ui["population_window"] = None
    ui["population_canvas"] = None
    ui["population_frame"] = None
    ui["population_after_id"] = None


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
    for colonne in range(3):
        frame.columnconfigure(colonne, weight=1)

    groupes = selectionner_echantillon_population(snapshot)
    ligne = dessiner_resume_population(frame, snapshot, 0)
    ligne = dessiner_cycle_genetique(frame, ligne)
    ligne = dessiner_section_population(frame, "Meilleur global et élites sélectionnées", groupes["elites"], ligne)
    ligne = dessiner_section_population(frame, "Mémoire courte de la génération précédente", groupes["precedents"], ligne)
    dessiner_section_population(frame, "Échantillon testé puis transformé", groupes["echantillon"], ligne)


def cle_evaluation(evaluation):
    return tuple(cellule for ligne in evaluation.individu for cellule in ligne)


def ajouter_unique(destination, evaluation, vus):
    if evaluation is None:
        return
    cle = cle_evaluation(evaluation)
    if cle in vus:
        return
    vus.add(cle)
    destination.append(evaluation)


def selectionner_echantillon_population(snapshot):
    vus = set()
    elites = []
    precedents = []
    echantillon = []

    ajouter_unique(elites, snapshot.meilleur_global, vus)
    for evaluation in snapshot.population_evaluee:
        if evaluation.role == "elite":
            ajouter_unique(elites, evaluation, vus)
        if len(elites) >= 5:
            break

    for evaluation in snapshot.meilleurs_precedents:
        ajouter_unique(precedents, evaluation, vus)
        if len(precedents) >= 3:
            break

    roles_prioritaires = (
        ("enfant", 3),
        ("injection", 2),
        ("elite conservee", 1),
        ("amelioration locale", 1),
        ("aléatoire", 1),
        ("aleatoire", 1),
        ("cible", 1),
        ("dessin", 1),
    )
    for fragment_role, limite in roles_prioritaires:
        ajoutes = 0
        for evaluation in snapshot.population_evaluee:
            if fragment_role in evaluation.role.lower():
                avant = len(echantillon)
                ajouter_unique(echantillon, evaluation, vus)
                ajoutes += len(echantillon) - avant
                if ajoutes >= limite or len(echantillon) >= 7:
                    break
        if len(echantillon) >= 7:
            break

    for evaluation in snapshot.population_evaluee:
        ajouter_unique(echantillon, evaluation, vus)
        if len(echantillon) >= 7:
            break

    return {
        "elites": elites[:5],
        "precedents": precedents[:3],
        "echantillon": echantillon[:7],
    }


def dessiner_resume_population(parent, snapshot, ligne):
    texte = "Génération {} | étape animée {} / {} | mutation {:.3f} | injection {:.2f} | mémoire cache {} | affichage limité à un échantillon".format(
        snapshot.generation,
        ui["population_step"],
        state.k_inverse,
        snapshot.taux_mutation,
        snapshot.taux_injection,
        snapshot.taille_cache,
    )
    tk.Label(parent, text=texte, bg=UI_BG, fg=IMPORTANT_TEXT, anchor="w").grid(
        row=ligne,
        column=0,
        columnspan=3,
        sticky="ew",
        padx=6,
        pady=(4, 8),
    )
    return ligne + 1


def dessiner_cycle_genetique(parent, ligne):
    cycle = tk.Frame(parent, bg="#e2e8f0", bd=0)
    cycle.grid(row=ligne, column=0, columnspan=3, sticky="ew", padx=6, pady=(0, 10))
    etapes = [
        ("1. Tester", "#dbeafe"),
        ("2. Sélectionner les élites", "#dcfce7"),
        ("3. Croiser + muter", "#fef3c7"),
        ("4. Nouvelle génération", "#ede9fe"),
    ]
    for colonne, (texte, couleur) in enumerate(etapes):
        cycle.columnconfigure(colonne, weight=1)
        tk.Label(
            cycle,
            text=texte,
            bg=couleur,
            fg=TEXT_COLOR,
            font=("TkDefaultFont", 9, "bold"),
            padx=10,
            pady=8,
        ).grid(row=0, column=colonne, sticky="ew", padx=1, pady=1)
    return ligne + 1


def dessiner_section_population(parent, titre, evaluations, ligne_depart, colonnes=3):
    if not evaluations:
        return ligne_depart

    tk.Label(
        parent,
        text=titre,
        bg=UI_BG,
        fg="#64748b",
        font=("TkDefaultFont", 9, "bold"),
        anchor="w",
    ).grid(row=ligne_depart, column=0, columnspan=colonnes, sticky="ew", padx=6, pady=(10, 0))

    return dessiner_cartes(parent, evaluations, ligne_depart + 1, colonnes)


def dessiner_cartes(parent, evaluations, ligne_depart, colonnes=3):
    ligne = ligne_depart
    colonne = 0
    for evaluation in evaluations:
        carte = tk.Frame(parent, bg="white", bd=1, relief=tk.SOLID)
        carte.grid(row=ligne, column=colonne, sticky="nsew", padx=6, pady=6)
        dessiner_carte_individu(carte, evaluation)
        colonne += 1
        if colonne >= colonnes:
            colonne = 0
            ligne += 1
    return ligne + (1 if colonne else 0)


def dessiner_carte_individu(parent, evaluation):
    header = "#{} | {} | erreur {:.2f} | {:.1f}% | {} cellules".format(
        evaluation.rang,
        libelle_role(evaluation.role),
        evaluation.erreur,
        evaluation.exactitude,
        nombre_cellules_vivantes(evaluation.individu),
    )
    tk.Label(parent, text=header, bg="white", fg=TEXT_COLOR, font=("TkDefaultFont", 8, "bold"), anchor="w").pack(fill="x", padx=6, pady=(5, 1))
    tk.Label(parent, text=description_role(evaluation.role), bg="white", fg=DISCREET_TEXT, font=("TkDefaultFont", 8), anchor="w").pack(fill="x", padx=6)

    grille_animee = evaluation.individu
    if ui["population_step"] > 0:
        grille_animee = historique_evolution(
            evaluation.individu,
            min(ui["population_step"], state.k_inverse),
            state.config_recherche.bords_toriques,
        )[-1]

    ligne_grilles = tk.Frame(parent, bg="white")
    ligne_grilles.pack(padx=6, pady=(5, 6))
    dessiner_mini_grille(ligne_grilles, "G0", evaluation.individu, "initial", evaluation, 0)
    dessiner_mini_grille(ligne_grilles, "G{}".format(ui["population_step"]), grille_animee, "anime", evaluation, 1)
    dessiner_mini_grille(ligne_grilles, "Résultat", evaluation.resultat, "resultat", evaluation, 2)


def libelle_role(role):
    return {
        "elite": "élite",
        "elite conservee": "élite conservée",
        "meilleur precedent": "meilleur précédent",
        "meilleur global": "meilleur global",
        "dessin actuel": "dessin actuel",
        "cible naive": "cible naïve",
        "cible bruitee": "cible bruitée",
        "graine locale": "graine locale",
        "relance locale": "relance locale",
        "relance stagnation": "relance stagnation",
        "aléatoire guidé": "aléatoire guidé",
        "aleatoire guide": "aléatoire guidé",
        "remplacement doublon": "remplacement de doublon",
        "remplacement de doublon": "remplacement de doublon",
        "amelioration locale": "amélioration locale",
        "injection": "injection",
        "enfant": "enfant",
        "candidat": "candidat",
    }.get(role, role)


def description_role(role):
    role_min = role.lower()
    if "meilleur global" in role_min:
        return "meilleur individu trouvé depuis le lancement"
    if "elite" in role_min:
        return "sélectionné pour survivre à la génération"
    if "enfant" in role_min:
        return "issu d'un croisement puis muté"
    if "injection" in role_min:
        return "nouvel individu aléatoire pour relancer la diversité"
    if "graine locale" in role_min:
        return "petit ancêtre possible énuméré près de la cible"
    if "relance stagnation" in role_min:
        return "nouveau candidat injecté pour casser une longue stagnation"
    if "relance locale" in role_min:
        return "graine locale réinjectée après stagnation"
    if "amelioration" in role_min:
        return "petite recherche locale autour du meilleur"
    if "precedent" in role_min:
        return "référence de la génération précédente"
    return "candidat évalué contre la cible"


def dessiner_mini_grille(parent, titre, grille, mode, evaluation, colonne):
    cell = 3
    bloc = tk.Frame(parent, bg="white")
    bloc.grid(row=0, column=colonne, padx=3, sticky="n")
    tk.Label(bloc, text=titre, bg="white", fg=DISCREET_TEXT, font=("TkDefaultFont", 8)).pack()

    canvas = tk.Canvas(bloc, width=COLS * cell, height=ROWS * cell, bg="#f8fafc", highlightthickness=1, highlightbackground="#e2e8f0")
    canvas.pack()
    for i in range(ROWS):
        for j in range(COLS):
            couleur = couleur_mini_grille(grille, mode, evaluation, i, j)
            if couleur:
                canvas.create_rectangle(j * cell, i * cell, (j + 1) * cell, (i + 1) * cell, fill=couleur, outline="")


def couleur_mini_grille(grille, mode, evaluation, i, j):
    if mode == "initial":
        return LIVE_COLOR if grille[i][j] == 1 else ""

    cible = state.cible[i][j]
    vivant = grille[i][j]
    if mode == "anime":
        if vivant == 1 and cible == 1:
            return INITIAL_AND_TARGET
        if vivant == 1:
            return LIVE_COLOR
        if cible == 1:
            return "#fde68a"
        return ""

    resultat = evaluation.resultat[i][j]
    if resultat == 1 and cible == 1:
        return RESULT_OK
    if resultat == 1 and cible == 0:
        return RESULT_EXTRA
    if resultat == 0 and cible == 1:
        return RESULT_MISSING
    return ""


def initialiser(board):
    tout_effacer()
    state.mode_app = "resolution"
    state.vue = "edition"
    creer_interface(board)
    rafraichir_plateau(board)
    afficher_infos(board)
    board.console("Chasseur de motifs du jeu de la vie prêt.")
    board.console("Mode résolution : dessinez une cible, choisissez le minimum de générations si besoin, puis lancez le solveur.")


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
