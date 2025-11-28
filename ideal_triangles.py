"""
Ideal Triangles on the Poincaré Disk
=====================================
This example demonstrates how to draw ideal triangles in the Poincaré disk
model of hyperbolic geometry. An ideal triangle has all three vertices on
the boundary circle (at infinity), and its sides are hyperbolic geodesics.
"""

from manim import *
import numpy as np


def geodesic_arc(p1, p2, num_points=50):
    """
    Compute a hyperbolic geodesic between two points on the unit circle.

    In the Poincaré disk model, geodesics are either:
    - Diameters (if points are antipodal)
    - Circular arcs orthogonal to the boundary circle

    Parameters:
        p1, p2: Points on the unit circle (ideal points)
        num_points: Number of points to sample along the arc

    Returns:
        Array of points along the geodesic
    """
    p1 = np.array(p1[:2])  # Ensure 2D
    p2 = np.array(p2[:2])

    # Check if points are antipodal (geodesic is a diameter)
    if np.allclose(p1, -p2, atol=1e-6):
        t = np.linspace(0, 1, num_points)
        points = np.outer(1 - t, p1) + np.outer(t, p2)
        return [np.array([*pt, 0]) for pt in points]

    # Find the center of the orthogonal circle
    # The center lies on the perpendicular bisector of p1-p2
    # and the line through origin perpendicular to (p1+p2)

    # For points on unit circle, the orthogonal circle center is:
    # c = (p1 + p2) / (p1 · p2 + 1) when p1, p2 are on unit circle
    # But we need a different approach for ideal points

    # The orthogonal circle passes through p1, p2 and is perpendicular
    # to the unit circle. Its center is at distance > 1 from origin.

    mid = (p1 + p2) / 2

    # Direction perpendicular to chord
    perp = np.array([-( p2[1] - p1[1]), p2[0] - p1[0]])
    perp = perp / np.linalg.norm(perp)

    # The center of the orthogonal circle lies along: mid + t * perp
    # For the circle to be orthogonal to unit circle at p1:
    # |center - p1|^2 = |center|^2 - 1
    # This gives us: (mid + t*perp - p1) · (mid + t*perp - p1) = |mid + t*perp|^2 - 1

    # Let's solve for t
    # |mid - p1|^2 + 2t*(mid-p1)·perp + t^2 = |mid|^2 + 2t*mid·perp + t^2 - 1
    # |mid - p1|^2 + 2t*(mid-p1)·perp = |mid|^2 + 2t*mid·perp - 1

    d = mid - p1
    # |d|^2 - |mid|^2 + 1 = 2t*(mid·perp - d·perp) = 2t * p1·perp

    lhs = np.dot(d, d) - np.dot(mid, mid) + 1
    rhs_coeff = 2 * np.dot(p1, perp)

    if abs(rhs_coeff) < 1e-10:
        # Points are antipodal, return diameter
        t = np.linspace(0, 1, num_points)
        points = np.outer(1 - t, p1) + np.outer(t, p2)
        return [np.array([*pt, 0]) for pt in points]

    t_param = lhs / rhs_coeff
    center = mid + t_param * perp
    radius = np.linalg.norm(p1 - center)

    # Parameterize the arc
    angle1 = np.arctan2(p1[1] - center[1], p1[0] - center[0])
    angle2 = np.arctan2(p2[1] - center[1], p2[0] - center[0])

    # Ensure we take the arc inside the disk
    # The arc should curve toward the origin
    center_dist = np.linalg.norm(center)

    # Adjust angles to go the short way (inside the disk)
    if angle2 < angle1:
        angle1, angle2 = angle2, angle1
        p1, p2 = p2, p1

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

    return points


class IdealTriangle(VMobject):
    """A single ideal triangle on the Poincaré disk."""

    def __init__(self, angles, radius=1.0, num_points_per_side=100, **kwargs):
        """
        Create an ideal triangle with vertices at given angles on the boundary.

        Parameters:
            angles: List of 3 angles (in radians) specifying vertex positions
                   on the boundary circle
            radius: Radius of the Poincaré disk (default 1.0)
            num_points_per_side: Points per geodesic arc (more = smoother curves)
        """
        super().__init__(**kwargs)

        self.radius = radius

        # Vertices on the boundary circle (at the given radius)
        self.ideal_vertices = [
            radius * np.array([np.cos(a), np.sin(a), 0]) for a in angles
        ]

        # Create the three geodesic sides
        # Compute geodesics on unit circle, then scale the result
        all_points = []
        for i in range(3):
            # Get unit circle points for geodesic calculation
            p1_unit = np.array([np.cos(angles[i]), np.sin(angles[i]), 0])
            p2_unit = np.array([np.cos(angles[(i + 1) % 3]), np.sin(angles[(i + 1) % 3]), 0])
            arc_points = geodesic_arc(p1_unit, p2_unit, num_points=num_points_per_side)
            # Scale to disk radius
            scaled_points = [radius * pt for pt in arc_points]
            all_points.extend(scaled_points[:-1])  # Avoid duplicating endpoints

        self.set_points_as_corners(all_points + [all_points[0]])


class PoincareDisk(VGroup):
    """The Poincaré disk boundary and optional decorations."""

    def __init__(self, radius=2.5, show_grid=False, **kwargs):
        super().__init__(**kwargs)

        self.disk_radius = radius

        # Boundary circle
        self.boundary = Circle(radius=radius, color=WHITE, stroke_width=2)
        self.add(self.boundary)

        if show_grid:
            self.add_hyperbolic_grid()

    def add_hyperbolic_grid(self, num_lines=8):
        """Add some geodesic lines to show hyperbolic geometry."""
        for i in range(num_lines):
            angle = i * PI / num_lines
            # Create a diameter
            start = self.disk_radius * np.array([np.cos(angle), np.sin(angle), 0])
            end = -start
            line = Line(start, end, stroke_width=0.5, color=GREY)
            self.add(line)


class IdealTriangleScene(Scene):
    """Basic scene showing a single ideal triangle."""

    def construct(self):
        # Title
        title = Text("Ideal Triangle on the Poincaré Disk", font_size=36)
        title.to_edge(UP)

        # Create the disk
        disk = PoincareDisk(radius=2.5)

        # Create an ideal triangle with vertices at 120° apart
        angles = [0, 2*PI/3, 4*PI/3]
        triangle = IdealTriangle(angles, radius=2.5, color=BLUE, stroke_width=3)

        # Mark the ideal vertices
        vertices = VGroup(*[
            Dot(point=2.5 * np.array([np.cos(a), np.sin(a), 0]),
                color=YELLOW, radius=0.08)
            for a in angles
        ])

        # Animate
        self.play(Write(title))
        self.play(Create(disk.boundary))
        self.wait(0.5)
        self.play(Create(triangle), run_time=2)
        self.play(FadeIn(vertices))

        # Add label
        label = Text("All vertices lie on the boundary circle (at infinity)",
                    font_size=24, color=GREY)
        label.to_edge(DOWN)
        self.play(Write(label))

        self.wait(2)


class MultipleIdealTriangles(Scene):
    """Scene showing multiple ideal triangles tessellating the disk."""

    def construct(self):
        title = Text("Ideal Triangle Tessellation", font_size=36)
        title.to_edge(UP)

        disk = PoincareDisk(radius=2.5)

        # Create several ideal triangles with different colors
        triangles = VGroup()
        colors = [BLUE, RED, GREEN, YELLOW, PURPLE, ORANGE]

        # Central triangle
        central_angles = [PI/6, PI/6 + 2*PI/3, PI/6 + 4*PI/3]
        central = IdealTriangle(central_angles, radius=2.5, color=BLUE, stroke_width=2)
        triangles.add(central)

        # Adjacent triangles sharing edges
        adjacent_configs = [
            ([PI/6, PI/6 + 2*PI/3, PI/2], RED),
            ([PI/6 + 2*PI/3, PI/6 + 4*PI/3, PI/6 + PI], GREEN),
            ([PI/6 + 4*PI/3, PI/6, -PI/6], PURPLE),
        ]

        for angles, color in adjacent_configs:
            tri = IdealTriangle(angles, radius=2.5, color=color, stroke_width=2)
            triangles.add(tri)

        self.play(Write(title))
        self.play(Create(disk.boundary))

        for tri in triangles:
            self.play(Create(tri), run_time=0.8)

        # Explanation
        explanation = VGroup(
            Text("In hyperbolic geometry:", font_size=24),
            Text("• All ideal triangles have the same area", font_size=20),
            Text("• The sum of angles is 0 (all vertices at infinity)", font_size=20),
        ).arrange(DOWN, aligned_edge=LEFT).to_edge(DOWN)

        self.play(Write(explanation), run_time=2)
        self.wait(3)


class AnimatedIdealTriangle(Scene):
    """Animate an ideal triangle morphing as vertices move on the boundary."""

    def construct(self):
        title = Text("Ideal Triangle with Moving Vertices", font_size=36)
        title.to_edge(UP)

        disk = PoincareDisk(radius=2.5)

        # Initial angles
        angles = ValueTracker(0)

        def get_triangle():
            a = angles.get_value()
            triangle_angles = [a, a + 2*PI/3, a + 4*PI/3]
            tri = IdealTriangle(triangle_angles, radius=2.5, color=BLUE, stroke_width=3)
            return tri

        triangle = always_redraw(get_triangle)

        # Vertices that follow
        def get_vertices():
            a = angles.get_value()
            return VGroup(*[
                Dot(point=2.5 * np.array([np.cos(a + i*2*PI/3),
                                          np.sin(a + i*2*PI/3), 0]),
                    color=YELLOW, radius=0.08)
                for i in range(3)
            ])

        vertices = always_redraw(get_vertices)

        self.play(Write(title))
        self.play(Create(disk.boundary))
        self.add(triangle, vertices)

        # Rotate the triangle
        self.play(angles.animate.set_value(2*PI), run_time=6, rate_func=linear)

        self.wait(1)


class IdealTriangleConstruction(Scene):
    """Step-by-step construction of an ideal triangle."""

    def construct(self):
        title = Text("Constructing an Ideal Triangle", font_size=36)
        title.to_edge(UP)

        disk = PoincareDisk(radius=2.5)

        # Three ideal points
        angles = [PI/4, 3*PI/4, -PI/2]
        ideal_points = [
            2.5 * np.array([np.cos(a), np.sin(a), 0]) for a in angles
        ]

        # Labels
        labels = ["A", "B", "C"]
        point_labels = VGroup(*[
            Text(label, font_size=24).next_to(
                2.8 * np.array([np.cos(a), np.sin(a), 0]),
                direction=np.array([np.cos(a), np.sin(a), 0])
            )
            for label, a in zip(labels, angles)
        ])

        # Dots for ideal points
        dots = VGroup(*[
            Dot(point=pt, color=YELLOW, radius=0.1) for pt in ideal_points
        ])

        # Geodesic sides
        sides = []
        side_labels = ["Geodesic AB", "Geodesic BC", "Geodesic CA"]

        for i in range(3):
            p1 = ideal_points[i]
            p2 = ideal_points[(i+1) % 3]
            arc_points = geodesic_arc(p1, p2, num_points=50)
            # Scale points
            arc_points = [2.5 * pt / np.linalg.norm(pt[:2]) if np.linalg.norm(pt[:2]) > 0.01
                         else 2.5 * pt for pt in arc_points]

            # Actually recalculate properly
            p1_norm = p1 / 2.5
            p2_norm = p2 / 2.5
            arc_points = geodesic_arc(p1_norm, p2_norm, num_points=50)
            arc_points = [2.5 * pt for pt in arc_points]

            side = VMobject(color=[BLUE, GREEN, RED][i], stroke_width=3)
            side.set_points_as_corners(arc_points)
            sides.append(side)

        # Step by step construction
        self.play(Write(title))
        self.play(Create(disk.boundary), run_time=1.5)

        step1 = Text("Step 1: Choose three ideal points on the boundary",
                    font_size=24).to_edge(DOWN)
        self.play(Write(step1))

        for dot, label in zip(dots, point_labels):
            self.play(FadeIn(dot), Write(label), run_time=0.5)

        self.wait(1)

        step2 = Text("Step 2: Connect with hyperbolic geodesics (circular arcs ⊥ to boundary)",
                    font_size=22).to_edge(DOWN)
        self.play(Transform(step1, step2))

        for i, side in enumerate(sides):
            self.play(Create(side), run_time=1)

        self.wait(1)

        step3 = Text("Result: An ideal triangle with all angles = 0",
                    font_size=24, color=YELLOW).to_edge(DOWN)
        self.play(Transform(step1, step3))

        # Fill the triangle
        triangle = IdealTriangle(angles, radius=2.5, fill_opacity=0.3, fill_color=BLUE,
                                stroke_width=0)
        self.play(FadeIn(triangle))

        self.wait(3)


# To render, run one of:
# manim -pql ideal_triangles.py IdealTriangleScene
# manim -pql ideal_triangles.py MultipleIdealTriangles
# manim -pql ideal_triangles.py AnimatedIdealTriangle
# manim -pql ideal_triangles.py IdealTriangleConstruction
#
# Use -pqh for high quality, -pqm for medium quality
