from __future__ import annotations

from manim import *


config.frame_width = 16
config.frame_height = 9
config.background_color = "#10131a"


FONT = "Arial"
BG = "#10131a"
PANEL = "#181d26"
GRID_LINE = "#354052"
DEAD = "#202734"
LIVE = "#42d392"
BLUE = "#58a6ff"
AMBER = "#ffbf69"
RED = "#ff6b6b"
PURPLE = "#b983ff"
TEXT = "#f4f7fb"
MUTED = "#aab4c3"


def txt(message, size=34, color=TEXT, weight=NORMAL, **kwargs):
    return Text(message, font=FONT, font_size=size, color=color, weight=weight, **kwargs)


def small_caption(message, size=22, color=MUTED, width=4.0):
    label = txt(message, size=size, color=color)
    if label.width > width:
        label.scale_to_fit_width(width)
    return label


def life_grid(
    pattern,
    cell=0.36,
    live_color=LIVE,
    dead_color=DEAD,
    stroke_color=GRID_LINE,
    show_dead=True,
):
    rows = len(pattern)
    cols = len(pattern[0]) if rows else 0
    group = VGroup()

    for r, row in enumerate(pattern):
        for c, value in enumerate(row):
            fill = live_color if value else dead_color
            opacity = 1 if value or show_dead else 0
            square = Square(
                side_length=cell,
                stroke_width=1.3,
                stroke_color=stroke_color,
                fill_color=fill,
                fill_opacity=opacity,
            )
            square.move_to(
                np.array(
                    [
                        (c - (cols - 1) / 2) * cell,
                        ((rows - 1) / 2 - r) * cell,
                        0,
                    ]
                )
            )
            square.cell = (r, c)
            group.add(square)

    return group


def card(title, body, width=4.65, height=1.45, color=BLUE):
    box = RoundedRectangle(
        width=width,
        height=height,
        corner_radius=0.12,
        stroke_color=color,
        stroke_width=2,
        fill_color=PANEL,
        fill_opacity=0.94,
    )
    title_mob = txt(title, size=24, color=color, weight=BOLD)
    body_mob = txt(body, size=18, color=TEXT, line_spacing=0.82)
    if body_mob.width > width - 0.4:
        body_mob.scale_to_fit_width(width - 0.4)
    content = VGroup(title_mob, body_mob).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
    content.move_to(box.get_center())
    return VGroup(box, content)


def arrow_between(left, right, color=MUTED):
    arrow = Arrow(
        left.get_right() + RIGHT * 0.12,
        right.get_left() + LEFT * 0.12,
        buff=0,
        stroke_width=4,
        color=color,
        max_tip_length_to_length_ratio=0.18,
    )
    return arrow


class GeneticAlgorithmLifeFR(Scene):
    """Vidéo explicative Manim en français pour le solveur génétique."""

    def construct(self):
        self.camera.background_color = BG
        self.intro()
        self.rules_of_life()
        self.project_goal()
        self.genetic_cycle()
        self.crossover_and_mutation()
        self.loop_and_stagnation()
        self.outro()

    def intro(self):
        title = txt("Chasseur de motifs", size=68, color=TEXT, weight=BOLD)
        subtitle = txt(
            "Retrouver le passé du jeu de la vie avec un algorithme génétique",
            size=30,
            color=MUTED,
        )
        spark = life_grid(
            [
                [0, 1, 0, 0, 0],
                [0, 0, 1, 0, 0],
                [1, 1, 1, 0, 0],
                [0, 0, 0, 1, 1],
                [0, 0, 0, 1, 1],
            ],
            cell=0.45,
        ).scale(1.2)
        spark.next_to(title, UP, buff=0.55)
        group = VGroup(spark, title, subtitle).arrange(DOWN, buff=0.28)
        self.play(FadeIn(spark, shift=UP * 0.2), Write(title), FadeIn(subtitle))
        self.wait(1.0)
        self.play(FadeOut(group))

    def rules_of_life(self):
        title = txt("1. Les règles du jeu", size=46, weight=BOLD).to_edge(UP)
        self.play(Write(title))

        base = [
            [0, 0, 0, 0, 0],
            [0, 1, 1, 1, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
        board = life_grid(base, cell=0.42).to_edge(LEFT, buff=1.55).shift(DOWN * 0.15)
        board_label = txt("Ses 8 voisines décident de son sort", size=23, color=MUTED)
        board_label.scale_to_fit_width(3.7)
        board_label.next_to(board, DOWN, buff=0.35)
        self.play(Create(board), FadeIn(board_label))

        center = board[2 * 5 + 2]
        ring = VGroup()
        for idx in [6, 7, 8, 11, 13, 16, 17, 18]:
            ring.add(board[idx].copy().set_fill(BLUE, opacity=0.38).set_stroke(BLUE, width=3))
        focus = center.copy().set_fill(AMBER, opacity=0.5).set_stroke(AMBER, width=4)
        self.play(FadeIn(ring), FadeIn(focus), run_time=0.7)
        self.wait(0.5)

        rules = VGroup(
            card("Naissance", "morte + exactement 3 voisines\n=> elle naît", color=LIVE),
            card("Survie", "vivante + 2 ou 3 voisines\n=> elle reste vivante", color=BLUE),
            card("Disparition", "0, 1, 4, 5... voisines\n=> elle meurt", color=RED),
        ).arrange(DOWN, buff=0.24, aligned_edge=LEFT)
        rules.to_edge(RIGHT, buff=0.75).shift(DOWN * 0.05)
        self.play(LaggedStart(*[FadeIn(r, shift=LEFT * 0.2) for r in rules], lag_ratio=0.16))
        self.wait(1.2)

        blinker_a = life_grid([[0, 0, 0], [1, 1, 1], [0, 0, 0]], cell=0.38)
        blinker_b = life_grid([[0, 1, 0], [0, 1, 0], [0, 1, 0]], cell=0.38)
        blinker_a.next_to(board, RIGHT, buff=1.25).shift(DOWN * 2.55)
        blinker_b.next_to(blinker_a, RIGHT, buff=0.95)
        ar = arrow_between(blinker_a, blinker_b, color=AMBER)
        label_a = txt("génération t", size=20, color=MUTED).next_to(blinker_a, DOWN, buff=0.18)
        label_b = txt("génération t + 1", size=20, color=MUTED).next_to(blinker_b, DOWN, buff=0.18)
        self.play(FadeIn(blinker_a), FadeIn(label_a), GrowArrow(ar))
        self.play(TransformFromCopy(blinker_a, blinker_b), FadeIn(label_b))
        self.wait(1.0)
        self.play(FadeOut(VGroup(title, board, board_label, ring, focus, rules, blinker_a, blinker_b, ar, label_a, label_b)))

    def project_goal(self):
        title = txt("2. L'objectif du projet", size=46, weight=BOLD).to_edge(UP)
        problem = txt(
            "On connaît la cible finale. On cherche une grille initiale qui y arrive après X générations.",
            size=27,
            color=MUTED,
        ).next_to(title, DOWN, buff=0.25)
        if problem.width > 13.5:
            problem.scale_to_fit_width(13.5)

        unknown = life_grid(
            [
                [0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0],
                [0, 0, 1, 0, 0],
                [0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0],
            ],
            cell=0.45,
            live_color=BLUE,
        )
        target = life_grid(
            [
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [0, 1, 1, 1, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
            ],
            cell=0.45,
            live_color=LIVE,
        )
        unknown.shift(LEFT * 3.6 + DOWN * 0.2)
        target.shift(RIGHT * 3.6 + DOWN * 0.2)
        step_arrow = Arrow(unknown.get_right() + RIGHT * 0.25, target.get_left() + LEFT * 0.25, buff=0, color=AMBER, stroke_width=5)
        x_label = txt("simuler X = 1", size=24, color=AMBER).next_to(step_arrow, UP, buff=0.18)

        left_title = txt("candidat initial", size=25, color=BLUE).next_to(unknown, UP, buff=0.25)
        right_title = txt("cible dessinée", size=25, color=LIVE).next_to(target, UP, buff=0.25)
        question = txt("Problème inverse: il n'y a pas un seul retour en arrière.", size=25, color=TEXT)
        question.to_edge(DOWN, buff=0.8)

        self.play(Write(title), FadeIn(problem))
        self.play(FadeIn(left_title), Create(unknown), GrowArrow(step_arrow), FadeIn(x_label))
        self.play(Create(target), FadeIn(right_title))
        self.play(FadeIn(question, shift=UP * 0.15))
        self.wait(1.4)

        compare = VGroup(
            txt("Si le résultat simulé ressemble à la cible:", size=26, color=TEXT),
            txt("score bas => bon candidat", size=30, color=LIVE, weight=BOLD),
        ).arrange(DOWN, buff=0.16)
        compare.move_to(question)
        self.play(Transform(question, compare))
        self.wait(1.0)
        self.play(FadeOut(VGroup(title, problem, unknown, target, step_arrow, x_label, left_title, right_title, question)))

    def genetic_cycle(self):
        title = txt("3. L'algorithme génétique", size=46, weight=BOLD).to_edge(UP)
        self.play(Write(title))

        population = self.population_cards()
        population.arrange_in_grid(rows=2, cols=5, buff=(0.28, 0.34))
        population.scale(0.86).move_to(ORIGIN).shift(UP * 0.55)
        pop_label = txt("Population: plusieurs grilles initiales possibles", size=26, color=MUTED)
        pop_label.next_to(population, DOWN, buff=0.3)
        self.play(LaggedStart(*[FadeIn(p, scale=0.92) for p in population], lag_ratio=0.04), FadeIn(pop_label))
        self.wait(0.8)

        scores = [28, 9, 18, 4, 14, 33, 12, 7, 21, 16]
        score_labels = VGroup()
        for item, score in zip(population, scores):
            color = LIVE if score <= 7 else AMBER if score <= 14 else RED
            badge = RoundedRectangle(width=0.86, height=0.34, corner_radius=0.08, fill_color=color, fill_opacity=0.94, stroke_width=0)
            label = txt(str(score), size=17, color=BG, weight=BOLD).move_to(badge)
            badge_group = VGroup(badge, label).move_to(item.get_corner(UR) + LEFT * 0.28 + DOWN * 0.17)
            score_labels.add(badge_group)
        score_explain = txt("Évaluation: on simule chaque candidat, puis on mesure l'erreur", size=25, color=TEXT)
        score_explain.to_edge(DOWN, buff=0.6)
        self.play(LaggedStart(*[FadeIn(s, shift=DOWN * 0.08) for s in score_labels], lag_ratio=0.03), Transform(pop_label, score_explain))
        self.wait(0.9)

        selected = VGroup(population[3].copy(), population[7].copy()).arrange(RIGHT, buff=0.75)
        selected.move_to(ORIGIN).shift(UP * 0.3)
        selected_labels = VGroup(
            txt("Parent A", size=25, color=BLUE).next_to(selected[0], UP, buff=0.22),
            txt("Parent B", size=25, color=AMBER).next_to(selected[1], UP, buff=0.22),
        )
        selection_text = txt("Sélection par tournoi: quelques candidats au hasard, le meilleur gagne.", size=26, color=MUTED)
        selection_text.to_edge(DOWN, buff=0.8)
        self.play(FadeOut(pop_label), FadeOut(score_labels), FadeOut(population), FadeIn(selected), FadeIn(selected_labels), FadeIn(selection_text))
        self.wait(1.2)
        self.play(FadeOut(VGroup(title, selected, selected_labels, selection_text)))

    def crossover_and_mutation(self):
        title = txt("4. Croisement puis mutation", size=46, weight=BOLD).to_edge(UP)
        self.play(Write(title))

        parent_a_pattern = [
            [0, 1, 0, 0, 0],
            [0, 0, 1, 0, 0],
            [1, 1, 1, 0, 0],
            [0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0],
        ]
        parent_b_pattern = [
            [0, 0, 0, 1, 0],
            [0, 1, 1, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 1, 1, 0],
            [0, 0, 0, 0, 0],
        ]
        child_pattern = [
            [0, 1, 0, 1, 0],
            [0, 1, 1, 0, 0],
            [1, 1, 1, 0, 0],
            [0, 0, 1, 1, 0],
            [0, 0, 0, 0, 0],
        ]
        mutated_pattern = [
            [0, 1, 0, 1, 0],
            [0, 1, 1, 0, 0],
            [1, 1, 1, 0, 0],
            [0, 0, 1, 1, 0],
            [0, 0, 0, 1, 0],
        ]

        pa = life_grid(parent_a_pattern, cell=0.36, live_color=BLUE).shift(LEFT * 5.3 + UP * 0.55)
        pb = life_grid(parent_b_pattern, cell=0.36, live_color=AMBER).shift(LEFT * 2.2 + UP * 0.55)
        child = life_grid(child_pattern, cell=0.36, live_color=LIVE).shift(RIGHT * 1.2 + UP * 0.55)
        mutated = life_grid(mutated_pattern, cell=0.36, live_color=PURPLE).shift(RIGHT * 4.9 + UP * 0.55)

        labels = VGroup(
            txt("Parent A", size=23, color=BLUE).next_to(pa, UP, buff=0.22),
            txt("Parent B", size=23, color=AMBER).next_to(pb, UP, buff=0.22),
            txt("Enfant", size=23, color=LIVE).next_to(child, UP, buff=0.22),
            txt("Enfant muté", size=23, color=PURPLE).next_to(mutated, UP, buff=0.22),
        )
        self.play(FadeIn(pa), FadeIn(pb), FadeIn(labels[0]), FadeIn(labels[1]))

        mask = VGroup()
        for idx, square in enumerate(child):
            color = BLUE if idx % 2 == 0 else AMBER
            overlay = square.copy().set_fill(color, opacity=0.18).set_stroke(color, width=2.2)
            mask.add(overlay)
        mask_title = txt("Masque uniforme: chaque case vient de A ou de B", size=25, color=MUTED)
        mask_title.to_edge(DOWN, buff=0.75)

        self.play(FadeIn(mask_title))
        self.play(LaggedStart(*[FadeIn(m, scale=0.75) for m in mask], lag_ratio=0.015), run_time=1.1)
        self.play(GrowArrow(arrow_between(pb, child, color=LIVE)), TransformFromCopy(VGroup(pa, pb), child), FadeIn(labels[2]))
        self.wait(0.6)

        mut_cell = mutated[-2].copy().set_fill(RED, opacity=0.85).set_stroke(RED, width=4)
        mutation_text = txt("Mutation guidée: on inverse parfois une cellule", size=25, color=TEXT)
        mutation_text.move_to(mask_title)
        self.play(Transform(mask_title, mutation_text), GrowArrow(arrow_between(child, mutated, color=PURPLE)))
        self.play(TransformFromCopy(child, mutated), FadeIn(labels[3]))
        self.play(FadeIn(mut_cell), Flash(mut_cell.get_center(), color=PURPLE, flash_radius=0.7))
        self.wait(1.1)
        self.play(FadeOut(VGroup(title, pa, pb, child, mutated, labels, mask, mask_title, mut_cell)))

    def loop_and_stagnation(self):
        title = txt("5. Génération après génération", size=46, weight=BOLD).to_edge(UP)
        self.play(Write(title))

        cycle_items = VGroup(
            card("1. Évaluer", "simulation vers le futur\n+ comparaison à la cible", color=BLUE),
            card("2. Garder", "les élites: les meilleurs\nne sont pas perdus", color=LIVE),
            card("3. Reproduire", "tournoi, croisement,\nmutation guidée", color=AMBER),
            card("4. Diversifier", "injections, graines locales,\nrelance si stagnation", color=PURPLE),
        ).arrange(RIGHT, buff=0.3)
        cycle_items.scale(0.82).shift(UP * 1.0)
        arrows = VGroup()
        for left, right in zip(cycle_items, cycle_items[1:]):
            arrows.add(arrow_between(left, right, color=MUTED))
        back = CurvedArrow(
            cycle_items[-1].get_bottom() + DOWN * 0.2,
            cycle_items[0].get_bottom() + DOWN * 0.2,
            angle=-TAU / 4,
            color=MUTED,
            stroke_width=4,
        )
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in cycle_items], lag_ratio=0.12))
        self.play(LaggedStart(*[Create(a) for a in arrows], lag_ratio=0.12), Create(back))

        axis = NumberLine(x_range=[0, 7, 1], length=10.5, color=GRID_LINE, include_numbers=False)
        axis.shift(DOWN * 1.55)
        label_y = txt("erreur", size=22, color=MUTED).next_to(axis, LEFT, buff=0.3)
        points = [
            axis.n2p(0) + UP * 1.2,
            axis.n2p(1) + UP * 0.9,
            axis.n2p(2) + UP * 0.72,
            axis.n2p(3) + UP * 0.72,
            axis.n2p(4) + UP * 0.71,
            axis.n2p(5) + UP * 0.38,
            axis.n2p(6) + UP * 0.18,
            axis.n2p(7) + UP * 0.02,
        ]
        graph = VMobject(color=LIVE, stroke_width=5).set_points_smoothly(points)
        dots = VGroup(*[Dot(p, radius=0.065, color=LIVE) for p in points])
        stagnation = RoundedRectangle(width=2.9, height=0.68, corner_radius=0.12, fill_color=RED, fill_opacity=0.9, stroke_width=0)
        stagnation_label = txt("stagnation", size=24, color=BG, weight=BOLD).move_to(stagnation)
        stagnation_group = VGroup(stagnation, stagnation_label).next_to(axis, UP, buff=0.38).shift(RIGHT * 0.55)
        relaunch = txt("on secoue la population sans oublier les élites", size=25, color=PURPLE)
        relaunch.next_to(axis, DOWN, buff=0.5)

        self.play(Create(axis), FadeIn(label_y))
        self.play(Create(graph), LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.05), run_time=1.4)
        self.play(FadeIn(stagnation_group, scale=0.9))
        self.play(FadeIn(relaunch, shift=UP * 0.12))
        self.wait(1.2)

        exact = txt("But final: erreur = 0", size=42, color=LIVE, weight=BOLD)
        exact.to_edge(DOWN, buff=0.65)
        self.play(Transform(relaunch, exact), dots[-1].animate.set_color(AMBER).scale(1.8))
        self.wait(1.0)
        self.play(FadeOut(VGroup(title, cycle_items, arrows, back, axis, label_y, graph, dots, stagnation_group, relaunch)))

    def outro(self):
        title = txt("L'idée clé", size=52, color=TEXT, weight=BOLD)
        bullets = VGroup(
            txt("On ne remonte pas le temps.", size=31, color=RED),
            txt("On propose beaucoup de passés possibles.", size=31, color=BLUE),
            txt("On garde ce qui explique le mieux la cible.", size=31, color=LIVE),
            txt("Puis on recombine, on mute, et on recommence.", size=31, color=AMBER),
        ).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        VGroup(title, bullets).arrange(DOWN, buff=0.55).move_to(ORIGIN)
        self.play(Write(title))
        self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.2) for b in bullets], lag_ratio=0.16))
        self.wait(1.6)
        self.play(FadeOut(VGroup(title, bullets)))

    def population_cards(self):
        patterns = [
            [[0, 1, 0], [1, 0, 1], [0, 1, 0]],
            [[1, 1, 0], [0, 1, 0], [0, 0, 1]],
            [[0, 0, 1], [1, 1, 0], [0, 1, 0]],
            [[0, 1, 0], [0, 1, 0], [0, 1, 0]],
            [[1, 0, 0], [0, 1, 1], [1, 0, 0]],
            [[1, 0, 1], [0, 0, 0], [1, 0, 1]],
            [[0, 1, 1], [1, 0, 0], [0, 1, 0]],
            [[0, 0, 0], [1, 1, 1], [0, 0, 0]],
            [[1, 0, 0], [1, 1, 0], [0, 0, 1]],
            [[0, 1, 0], [1, 1, 0], [0, 0, 1]],
        ]
        cards = VGroup()
        for pattern in patterns:
            box = RoundedRectangle(
                width=1.38,
                height=1.38,
                corner_radius=0.08,
                stroke_color=GRID_LINE,
                stroke_width=1.5,
                fill_color=PANEL,
                fill_opacity=0.96,
            )
            grid = life_grid(pattern, cell=0.26).move_to(box)
            cards.add(VGroup(box, grid))
        return cards
