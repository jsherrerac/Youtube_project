from manim import *


class SineFromUnitCircle(Scene):
    def construct(self):
        # ── Layout ──────────────────────────────────────────────────────────
        circle_center = LEFT * 3.5
        wave_width    = 6.5
        full_period   = TAU

        # ── Ejes del círculo unitario ────────────────────────────────────────
        circle_axes = Axes(
            x_range=[-1.4, 1.4, 1],
            y_range=[-1.4, 1.4, 1],
            x_length=2.8,
            y_length=2.8,
            axis_config={"include_tip": False, "stroke_width": 2},
        ).move_to(circle_center)

        # ── Ejes de la onda seno ─────────────────────────────────────────────
        wave_axes = Axes(
            x_range=[0, full_period, PI / 2],
            y_range=[-1.4, 1.4, 1],
            x_length=wave_width,
            y_length=2.8,
            axis_config={"include_tip": False, "stroke_width": 2},
        ).shift(RIGHT * 2.0)

        # Etiquetas del eje x (sin LaTeX)
        x_labels = VGroup(
            Text("π/2", font_size=18).next_to(wave_axes.c2p(PI/2,   0), DOWN * 0.5),
            Text("π",   font_size=18).next_to(wave_axes.c2p(PI,     0), DOWN * 0.5),
            Text("3π/2",font_size=18).next_to(wave_axes.c2p(3*PI/2, 0), DOWN * 0.5),
            Text("2π",  font_size=18).next_to(wave_axes.c2p(TAU,    0), DOWN * 0.5),
        )

        # Etiquetas y
        y_label_pos = Text( "1", font_size=18).next_to(wave_axes.c2p(0,  1), LEFT * 0.4)
        y_label_neg = Text("-1", font_size=18).next_to(wave_axes.c2p(0, -1), LEFT * 0.4)

        # ── Círculo unitario ─────────────────────────────────────────────────
        unit_circle = Circle(
            radius=circle_axes.get_x_unit_size(),
            color=BLUE_B,
            stroke_width=2.5,
        ).move_to(circle_center)

        # ── Títulos ──────────────────────────────────────────────────────────
        title_circle = Text("Círculo Unitario", font_size=24, color=BLUE_B)\
            .next_to(circle_axes, UP, buff=0.25)
        title_wave = Text("Onda Seno", font_size=24, color=GREEN_B)\
            .next_to(wave_axes, UP, buff=0.25)

        # ── Aparición inicial ────────────────────────────────────────────────
        self.play(Create(circle_axes), Create(wave_axes), run_time=1.2)
        self.play(
            Create(unit_circle),
            Write(title_circle), Write(title_wave),
            FadeIn(x_labels), FadeIn(y_label_pos), FadeIn(y_label_neg),
            run_time=1.2,
        )

        # ── Objetos dinámicos ─────────────────────────────────────────────────
        angle_tracker = ValueTracker(0)
        r = circle_axes.get_x_unit_size()

        def circle_point():
            a = angle_tracker.get_value()
            return circle_center + np.array([r * np.cos(a), r * np.sin(a), 0])

        def wave_point():
            a = angle_tracker.get_value()
            return wave_axes.c2p(a, np.sin(a))

        dot_circle = always_redraw(
            lambda: Dot(circle_point(), radius=0.09, color=YELLOW)
        )
        radius_line = always_redraw(
            lambda: Line(circle_center, circle_point(), color=WHITE, stroke_width=2)
        )
        v_line = always_redraw(lambda: DashedLine(
            circle_point(),
            circle_center + np.array([r * np.cos(angle_tracker.get_value()), 0, 0]),
            color=RED,
            stroke_width=2,
            dash_length=0.08,
        ))
        h_connector = always_redraw(lambda: DashedLine(
            circle_point(),
            wave_axes.c2p(angle_tracker.get_value(), np.sin(angle_tracker.get_value())),
            color=RED_B,
            stroke_width=1.5,
            dash_length=0.07,
        ))
        dot_wave = always_redraw(
            lambda: Dot(wave_point(), radius=0.09, color=YELLOW)
        )
        arc_angle = always_redraw(lambda: Arc(
            radius=0.35,
            start_angle=0,
            angle=angle_tracker.get_value() % TAU,
            arc_center=circle_center,
            color=GREEN,
            stroke_width=2,
        ))
        theta_label = always_redraw(lambda: Text(
            "θ", font_size=24, color=GREEN
        ).move_to(
            circle_center + 0.58 * np.array([
                np.cos(angle_tracker.get_value() / 2),
                np.sin(angle_tracker.get_value() / 2),
                0,
            ])
        ))

        # Traza de la onda
        sine_curve = VMobject(color=GREEN_B, stroke_width=3)
        sine_curve.set_points_as_corners([wave_axes.c2p(0, 0), wave_axes.c2p(0, 0)])

        def update_sine_curve(mob):
            a = angle_tracker.get_value()
            if a < 1e-6:
                mob.set_points_as_corners([wave_axes.c2p(0, 0), wave_axes.c2p(0, 0)])
                return
            pts = [wave_axes.c2p(t, np.sin(t)) for t in np.linspace(0, a, max(2, int(a * 60)))]
            mob.set_points_smoothly(pts)

        sine_curve.add_updater(update_sine_curve)

        # ── Añadir objetos dinámicos ──────────────────────────────────────────
        self.play(
            FadeIn(dot_circle), FadeIn(radius_line),
            FadeIn(arc_angle),  FadeIn(theta_label),
            run_time=0.8,
        )
        self.add(sine_curve, v_line, h_connector, dot_wave)

        # ── Animación principal ───────────────────────────────────────────────
        self.play(
            angle_tracker.animate.set_value(TAU),
            rate_func=linear,
            run_time=8,
        )

        # ── Fórmula final (sin LaTeX) ─────────────────────────────────────────
        self.wait(0.5)
        formula = Text("f(θ) = sin(θ)", font_size=36, color=GREEN_B)\
            .to_edge(DOWN, buff=0.35)
        self.play(Write(formula), run_time=1)
        self.wait(2)
