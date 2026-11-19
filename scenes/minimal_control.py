"""A restrained 16 s visual analogy. Hand-authored motion, not a controller test."""
import os
import numpy as np
from manim import *

config.frame_width = 9
config.frame_height = 16
config.pixel_width = int(os.getenv("MINIMAL_WIDTH", "1080"))
config.pixel_height = int(config.pixel_width * 16 / 9)
config.frame_rate = 30
config.background_color = "#111B29"

INK = "#EEECE4"
MINT = "#A6D3C3"
PEACH = "#DFB09A"
MUTED = "#82929F"


def caption(text):
    return Text(text, font="Segoe UI", font_size=35, color=INK,
                weight=MEDIUM, disable_ligatures=True).move_to([0, 5.85, 0])


def rover():
    """Soft overhead toy rover, with the front indicated by two small lamps."""
    shadow = RoundedRectangle(width=1.17, height=1.48, corner_radius=.29,
                              fill_color="#060C14", fill_opacity=.24,
                              stroke_width=0).shift(DOWN * .09 + RIGHT * .045)
    wheels = VGroup(*[
        RoundedRectangle(width=.18, height=.36, corner_radius=.07,
                         fill_color="#607581", fill_opacity=1, stroke_width=0)
        .move_to([x, y, 0])
        for x in [-.44, .44] for y in [-.40, .40]
    ])
    body = RoundedRectangle(width=.84, height=1.27, corner_radius=.23,
                            fill_color="#CDD9D3", fill_opacity=1,
                            stroke_width=1, stroke_color="#E1E7DF")
    roof = RoundedRectangle(width=.64, height=.69, corner_radius=.18,
                            fill_color="#AABDBA", fill_opacity=1,
                            stroke_width=0).shift(DOWN * .05)
    sensor = Circle(radius=.105, fill_color="#516C78", fill_opacity=1,
                    stroke_width=0).shift(DOWN * .08)
    lamps = VGroup(*[
        RoundedRectangle(width=.16, height=.045, corner_radius=.02,
                         fill_color=MINT, fill_opacity=1, stroke_width=0)
        .move_to([x, .52, 0]) for x in [-.23, .23]
    ])
    return VGroup(shadow, wheels, body, roof, sensor, lamps).set_z_index(5)


def wind(center):
    curves = VGroup()
    for dy, length in [(-.25, .62), (0, .94), (.25, .73)]:
        line = CubicBezier(np.array([-length, dy, 0]), np.array([-.56, dy+.09, 0]),
                           np.array([-.18, dy+.09, 0]), np.array([0, dy, 0]),
                           color=PEACH, stroke_width=3, stroke_opacity=.75)
        curves.add(line)
    return curves.move_to(center).set_z_index(6)


class MinimalControlBase(Scene):
    labels = False

    def construct(self):
        # Both versions share every geometry, movement, and shot duration.
        floor = RoundedRectangle(width=6.1, height=10.6, corner_radius=.52,
                                 fill_color="#1B2A3A", fill_opacity=1, stroke_width=0)
        floor_shadow = floor.copy().set_fill("#080F19", .28).shift(DOWN*.12)
        walls = VGroup(*[
            RoundedRectangle(width=.45, height=8.65, corner_radius=.19,
                             fill_color="#526573", fill_opacity=1,
                             stroke_color="#617481", stroke_width=.6)
            .move_to([x, 0, 0]) for x in [-2.5, 2.5]
        ]).set_z_index(3)
        note = Text("SCHEMATIC", font="Segoe UI", font_size=14, color=MUTED,
                    disable_ligatures=True).move_to([0, -5.85, 0])
        road = VGroup(floor_shadow, floor, walls, note)
        first_x = 1.05
        first_path = DashedLine([first_x, -4.05, 0], [first_x, 4.05, 0],
                                color=PEACH, stroke_width=3, dash_length=.12,
                                dashed_ratio=.52, stroke_opacity=.52).set_z_index(2)
        bot = rover().move_to([first_x, -3.8, 0])
        label = caption("Perfect plan") if self.labels else VGroup()
        self.play(FadeIn(road), FadeIn(first_path), FadeIn(bot), FadeIn(label), run_time=.7)
        self.wait(.5)
        self.play(bot.animate.move_to([first_x, -.9, 0]), run_time=2.4, rate_func=smooth)
        wind_1 = wind([-0.39, -.9, 0])
        if self.labels:
            self.play(FadeIn(wind_1), Transform(label, caption("Small push")), run_time=.4)
        else:
            self.play(FadeIn(wind_1), run_time=.4)
        # Exactly the same +0.73 lateral displacement is used in both passes.
        self.play(bot.animate.move_to([1.78, 0, 0]), wind_1.animate.shift(RIGHT*.73+UP*.9),
                  run_time=.8, rate_func=smooth)
        contact = Circle(radius=.18, color=PEACH, stroke_width=3).move_to([2.28, .18, 0]).set_z_index(8)
        wall_mark = RoundedRectangle(width=.45, height=1.30, corner_radius=.17,
                                     fill_color=PEACH, fill_opacity=.7, stroke_width=0)
        wall_mark.move_to([2.5, .12, 0]).set_z_index(4)
        self.play(FadeIn(wall_mark), Create(contact), run_time=.45)
        self.play(contact.animate.scale(2.2).set_stroke(opacity=0), run_time=.45)
        self.wait(.4)
        self.play(FadeOut(bot), FadeOut(first_path), FadeOut(wind_1),
                  FadeOut(contact), FadeOut(wall_mark), FadeOut(label), run_time=.7)
        # A faint corridor shows reserved space without equations or dimensions.
        margin = RoundedRectangle(width=2.25, height=8.15, corner_radius=.5,
                                  fill_color=MINT, fill_opacity=.07,
                                  stroke_width=0).set_z_index(1)
        center_path = DashedLine([0, -4.05, 0], [0, 4.05, 0],
                                 color=MINT, stroke_width=3, dash_length=.12,
                                 dashed_ratio=.52, stroke_opacity=.62).set_z_index(2)
        bot2 = rover().move_to([0, -3.8, 0])
        label2 = caption("Leave room") if self.labels else VGroup()
        self.play(FadeIn(margin), FadeIn(center_path), FadeIn(bot2), FadeIn(label2), run_time=.7)
        self.wait(.5)
        self.play(bot2.animate.move_to([0, -.9, 0]), run_time=2.4, rate_func=smooth)
        wind_2 = wind([-1.44, -.9, 0])
        self.play(FadeIn(wind_2), run_time=.4)
        self.play(bot2.animate.move_to([.73, 0, 0]), wind_2.animate.shift(RIGHT*.73+UP*.9),
                  run_time=.8, rate_func=smooth)
        return_path = CubicBezier(np.array([.73, 0, 0]), np.array([.73, 1.45, 0]),
                                 np.array([0, 1.85, 0]), np.array([0, 3.8, 0]))
        self.play(MoveAlongPath(bot2, return_path), FadeOut(wind_2), run_time=2.0, rate_func=smooth)
        self.wait(.9)
        self.play(FadeOut(bot2, shift=UP*.45), FadeOut(margin), FadeOut(center_path),
                  FadeOut(label2), run_time=.8)
        self.wait(.7)


class MinimalControlA(MinimalControlBase):
    labels = False


class MinimalControlB(MinimalControlBase):
    labels = True
