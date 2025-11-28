"""
Ideal Triangles on the Poincaré Disk
=====================================
"""

from manim import *
import numpy as np


def geodesic_arc(p1_in, p2_in, num_points=50):
    """
    Compute a hyperbolic geodesic between two points on the unit circle.

    Fixed to ensure points are always returned in order from p1_in to p2_in.
    """
    # Store originals to check direction later
    p1_orig = np.array(p1_in[:2])

    p1 = np.array(p1_in[:2])
    p2 = np.array(p2_in[:2])

    # Check if points are antipodal (geodesic is a diameter)
    if np.allclose(p1, -p2, atol=1e-6):
        t = np.linspace(0, 1, num_points)
        points = np.outer(1 - t, p1) + np.outer(t, p2)
        return [np.array([*pt, 0]) for pt in points]

    mid = (p1 + p2) / 2

    # Direction perpendicular to chord
    perp = np.array([-(p2[1] - p1[1]), p2[0] - p1[0]])
    perp = perp / np.linalg.norm(perp)

    d = mid - p1
    lhs = np.dot(d, d) - np.dot(mid, mid) + 1
    rhs_coeff = 2 * np.dot(p1, perp)

    if abs(rhs_coeff) < 1e-10:
        t = np.linspace(0, 1, num_points)
        points = np.outer(1 - t, p1) + np.outer(t, p2)
        return [np.array([*pt, 0]) for pt in points]

    t_param = lhs / rhs_coeff
    center = mid + t_param * perp
    radius = np.linalg.norm(p1 - center)

    # Parameterize the arc
    angle1 = np.arctan2(p1[1] - center[1], p1[0] - center[0])
    angle2 = np.arctan2(p2[1] - center[1], p2[0] - center[0])

    # Adjust angles to go the short way (inside the disk)
    if angle2 < angle1:
        angle1, angle2 = angle2, angle1
        # We swapped angles for calculation, but we won't swap p1/p2 variables
        # here to avoid confusion. We handle direction at the very end.

    # Check if we need to go the other way
    mid_angle = (angle1 + angle2) / 2
    mid_point = center + radius * np.array([np.cos(mid_angle), np.sin(mid_angle)])

    if np.linalg.norm(mid_point) > 1:
        # Wrong direction, go the long way
        angle2 -= 2 * np.pi
        angle1, angle2 = angle2, angle1

    angles = np.linspace(angle1, angle2, num_points)
    points = []
    for a in angles:
        pt = center + radius * np.array([np.cos(a), np.sin(a)])
        points.append(np.array([pt[0], pt[1], 0]))

    # --- CRITICAL FIX ---
    # Ensure the list starts closer to p1_in than p2_in.
    # If the generation logic made it run p2->p1, we reverse it.
    if len(points) > 0:
        dist_start = np.linalg.norm(points[0][:2] - p1_orig)
        dist_end = np.linalg.norm(points[-1][:2] - p1_orig)
        if dist_end < dist_start:
            points.reverse()

    return points


class IdealTriangle(VMobject):
    """A single ideal triangle on the Poincaré disk."""

    def __init__(self, angles, radius=1.0, num_points_per_side=200, **kwargs):
        super().__init__(**kwargs)
        self.radius = radius

        # Vertices on the boundary circle
        self.ideal_vertices = [
            radius * np.array([np.cos(a), np.sin(a), 0]) for a in angles
        ]

        all_points = []
        for i in range(3):
            p1_unit = np.array([np.cos(angles[i]), np.sin(angles[i]), 0])
            p2_unit = np.array([np.cos(angles[(i + 1) % 3]), np.sin(angles[(i + 1) % 3]), 0])

            arc_points = geodesic_arc(p1_unit, p2_unit, num_points=num_points_per_side)

            scaled_points = [radius * pt for pt in arc_points]
            all_points.extend(scaled_points[:-1])

        self.set_points_as_corners(all_points + [all_points[0]])


class PoincareDisk(VGroup):
    def __init__(self, radius=2.5, show_grid=False, **kwargs):
        super().__init__(**kwargs)
        self.disk_radius = radius
        self.boundary = Circle(radius=radius, color=WHITE, stroke_width=2)
        self.add(self.boundary)
        if show_grid:
            self.add_hyperbolic_grid()

    def add_hyperbolic_grid(self, num_lines=8):
        for i in range(num_lines):
            angle = i * PI / num_lines
            start = self.disk_radius * np.array([np.cos(angle), np.sin(angle), 0])
            end = -start
            line = Line(start, end, stroke_width=0.5, color=GREY)
            self.add(line)


class IdealTriangleScene(Scene):
    def construct(self):
        title = Text("Ideal Triangle on the Poincaré Disk", font_size=36)
        title.to_edge(UP)

        disk = PoincareDisk(radius=2.5)
        angles = [0, 2*PI/3, 4*PI/3]
        triangle = IdealTriangle(angles, radius=2.5, color=BLUE, stroke_width=3, fill_opacity=0.5)

        vertices = VGroup(*[
            Dot(point=2.5 * np.array([np.cos(a), np.sin(a), 0]),
                color=YELLOW, radius=0.08)
            for a in angles
        ])

        self.play(Write(title))
        self.play(Create(disk.boundary))
        self.play(Create(triangle), run_time=2)
        self.play(FadeIn(vertices))
        self.wait(2)


class MultipleIdealTriangles(Scene):
    def construct(self):
        title = Text("Ideal Triangle Tessellation", font_size=36)
        title.to_edge(UP)
        disk = PoincareDisk(radius=2.5)

        triangles = VGroup()

        # Central triangle
        central_angles = [PI/6, PI/6 + 2*PI/3, PI/6 + 4*PI/3]
        central = IdealTriangle(central_angles, radius=2.5, color=BLUE, stroke_width=2, fill_opacity=0.5)
        triangles.add(central)

        # Adjacent triangles
        adjacent_configs = [
            ([PI/6, PI/6 + 2*PI/3, PI/2], RED),
            ([PI/6 + 2*PI/3, PI/6 + 4*PI/3, PI/6 + PI], GREEN),
            ([PI/6 + 4*PI/3, PI/6, -PI/6], PURPLE),
        ]

        for angles, color in adjacent_configs:
            tri = IdealTriangle(angles, radius=2.5, color=color, stroke_width=2, fill_opacity=0.5)
            triangles.add(tri)

        self.play(Write(title), Create(disk.boundary))
        self.play(AnimationGroup(*[Create(t) for t in triangles], lag_ratio=0.2))
        self.wait(3)


class AnimatedIdealTriangle(Scene):
    def construct(self):
        title = Text("Ideal Triangle with Moving Vertices", font_size=36)
        title.to_edge(UP)
        disk = PoincareDisk(radius=2.5)

        angles = ValueTracker(0)

        def get_triangle():
            a = angles.get_value()
            triangle_angles = [a, a + 2*PI/3, a + 4*PI/3]
            tri = IdealTriangle(triangle_angles, radius=2.5, color=BLUE, stroke_width=3, fill_opacity=0.3)
            return tri

        triangle = always_redraw(get_triangle)

        def get_vertices():
            a = angles.get_value()
            return VGroup(*[
                Dot(point=2.5 * np.array([np.cos(a + i*2*PI/3),
                                          np.sin(a + i*2*PI/3), 0]),
                    color=YELLOW, radius=0.08)
                for i in range(3)
            ])

        vertices = always_redraw(get_vertices)

        self.play(Write(title), Create(disk.boundary))
        self.add(triangle, vertices)
        self.play(angles.animate.set_value(2*PI), run_time=6, rate_func=linear)
        self.wait(1)


class IdealTriangleConstruction(Scene):
    def construct(self):
        title = Text("Constructing an Ideal Triangle", font_size=36)
        title.to_edge(UP)

        disk = PoincareDisk(radius=2.5)
        angles = [PI/4, 3*PI/4, -PI/2]
        ideal_points = [2.5 * np.array([np.cos(a), np.sin(a), 0]) for a in angles]

        dots = VGroup(*[Dot(point=pt, color=YELLOW, radius=0.1) for pt in ideal_points])

        sides = []
        for i in range(3):
            p1 = ideal_points[i]
            p2 = ideal_points[(i+1) % 3]

            # Normalize to unit circle for calculation
            p1_norm = p1 / 2.5
            p2_norm = p2 / 2.5
            arc_points = geodesic_arc(p1_norm, p2_norm, num_points=200)

            # Scale back up
            arc_points = [2.5 * pt for pt in arc_points]

            side = VMobject(color=[BLUE, GREEN, RED][i], stroke_width=3)
            side.set_points_as_corners(arc_points)
            sides.append(side)

        self.play(Write(title), Create(disk.boundary))

        step1 = Text("Step 1: Choose three ideal points", font_size=24).to_edge(DOWN)
        self.play(Write(step1), FadeIn(dots))
        self.wait(1)

        step2 = Text("Step 2: Connect with hyperbolic geodesics", font_size=24).to_edge(DOWN)
        self.play(Transform(step1, step2))

        for side in sides:
            self.play(Create(side), run_time=1)
        self.wait(1)

        step3 = Text("Result: An ideal triangle", font_size=24).to_edge(DOWN)
        self.play(Transform(step1, step3))

        # Fill the triangle
        triangle = IdealTriangle(angles, radius=2.5, fill_opacity=0.3, fill_color=BLUE, stroke_width=0)
        self.play(FadeIn(triangle))

        self.wait(3)


# To render, run one of:
# manim -pql ideal_triangles.py IdealTriangleScene
# manim -pql ideal_triangles.py MultipleIdealTriangles
# manim -pql ideal_triangles.py AnimatedIdealTriangle
# manim -pql ideal_triangles.py IdealTriangleConstruction
#
# Use -pqh for high quality, -pqm for medium quality
