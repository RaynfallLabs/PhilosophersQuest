"""Geometry computation strategies: rectangle area/perimeter,
triangle area, circle area/circumference, Pythagorean triples,
volume of a box, angle sum of a triangle.
"""
from __future__ import annotations

from math import isqrt

from tools.quizgen.math_generators.common import make_question


def generate_rectangle_area() -> list[dict]:
    """T1: l × w."""
    out = []
    pairs = [(5, 4), (3, 7), (6, 8), (4, 9), (5, 12), (6, 10), (7, 8),
             (4, 11), (5, 9), (6, 12), (8, 10), (3, 14), (4, 15), (5, 8),
             (9, 10), (7, 12), (11, 4), (15, 3), (2, 14), (6, 11),
             (8, 12), (5, 15), (9, 9), (4, 16), (7, 11)]
    for l, w in pairs:
        area = l * w
        dist = [2 * (l + w), l + w, area + l]
        out.append(make_question(
            tier=1, topic_cell="geometry_basics",
            strategy="rectangle_area", pillar="computation",
            question=f"Rectangle {l} × {w}. Area?",
            answer=area, distractors=dist,
            context=f"Area = length × width = {l} × {w} = {area}.",
        ))
    return out


def generate_rectangle_perimeter() -> list[dict]:
    """T2: 2(l + w)."""
    out = []
    pairs = [(5, 4), (3, 7), (6, 8), (4, 9), (5, 12), (6, 10), (7, 8),
             (5, 9), (6, 12), (8, 10), (3, 14), (4, 15), (5, 8), (9, 10),
             (7, 12), (11, 4), (15, 3), (2, 14), (6, 11), (8, 12)]
    for l, w in pairs:
        perim = 2 * (l + w)
        dist = [l * w, l + w, perim + 2]
        out.append(make_question(
            tier=2, topic_cell="geometry_basics",
            strategy="rectangle_perimeter", pillar="computation",
            question=f"Rectangle {l} × {w}. Perimeter?",
            answer=perim, distractors=dist,
            context=f"Perimeter = 2(l + w) = 2({l}+{w}) = {perim}.",
        ))
    return out


def generate_triangle_area() -> list[dict]:
    """T2: ½ × base × height (even products → integer area)."""
    out = []
    pairs = [(4, 6), (8, 5), (10, 7), (6, 9), (12, 4), (8, 11), (10, 9),
             (14, 5), (6, 7), (8, 13), (12, 7), (16, 5), (6, 11), (10, 13),
             (4, 15), (8, 9), (12, 11), (14, 9), (6, 13), (10, 11)]
    for base, height in pairs:
        area = (base * height) // 2 if (base * height) % 2 == 0 else None
        if area is None:
            continue
        dist = [base * height, base + height, area + base]
        out.append(make_question(
            tier=2, topic_cell="geometry_basics",
            strategy="triangle_area", pillar="computation",
            question=f"Triangle: base {base}, height {height}. Area?",
            answer=area, distractors=dist,
            context=f"Area = ½ × base × height = ½ × {base} × {height} = {area}.",
        ))
    return out


def generate_circle_area_approx() -> list[dict]:
    """T3: A = πr² using π ≈ 3.14."""
    out = []
    for r in (1, 2, 3, 4, 5, 6, 7, 8, 10, 12):
        area = round(3.14 * r * r, 2)
        ans = f"{area:g}"
        dist = [f"{round(3.14 * 2 * r, 2):g}", f"{r*r:g}", f"{round(area * 2, 2):g}"]
        out.append(make_question(
            tier=3, topic_cell="geometry_basics",
            strategy="circle_area", pillar="computation",
            question=f"Circle r = {r}. Area? (π ≈ 3.14)",
            answer=ans, distractors=dist,
            context=f"A = πr² = 3.14 × {r}² = {ans}.",
        ))
    return out


def generate_circle_circumference_approx() -> list[dict]:
    """T3: C = 2πr."""
    out = []
    for r in (1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20):
        c = round(2 * 3.14 * r, 2)
        ans = f"{c:g}"
        dist = [f"{round(3.14 * r * r, 2):g}", f"{round(3.14 * r, 2):g}", f"{r*4:g}"]
        out.append(make_question(
            tier=3, topic_cell="geometry_basics",
            strategy="circle_circumference", pillar="computation",
            question=f"Circle r = {r}. Circumference? (π ≈ 3.14)",
            answer=ans, distractors=dist,
            context=f"C = 2πr = 2 × 3.14 × {r} = {ans}.",
        ))
    return out


def generate_pythagorean_triples() -> list[dict]:
    """T3: find the missing side of a right triangle."""
    out = []
    # famous Pythagorean triples
    triples = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25),
               (6, 8, 10), (9, 12, 15), (10, 24, 26), (12, 16, 20),
               (15, 20, 25), (20, 21, 29), (9, 40, 41), (11, 60, 61)]
    for a, b, c in triples:
        # ask for the hypotenuse
        dist = [a + b, a * b, c + 1]
        out.append(make_question(
            tier=3, topic_cell="geometry_advanced",
            strategy="pythagorean_3_4_5", pillar="computation",
            question=f"Right triangle legs {a} and {b}. Hypotenuse?",
            answer=c, distractors=dist,
            context=f"a² + b² = c²: {a*a}+{b*b}={c*c}. c = {c}.",
        ))
    return out


def generate_volume_box() -> list[dict]:
    """T3: V = l × w × h."""
    out = []
    triples = [(2, 3, 4), (3, 5, 6), (4, 5, 7), (2, 6, 8), (3, 4, 9),
               (5, 6, 8), (4, 7, 9), (3, 5, 10), (6, 7, 8), (5, 8, 10),
               (4, 5, 12), (6, 8, 9), (3, 7, 10), (5, 6, 12), (4, 9, 11)]
    for l, w, h in triples:
        vol = l * w * h
        dist = [2 * (l*w + w*h + l*h), l + w + h, vol // 2]
        out.append(make_question(
            tier=3, topic_cell="geometry_basics",
            strategy="volume_box", pillar="computation",
            question=f"Box {l} × {w} × {h}. Volume?",
            answer=vol, distractors=dist,
            context=f"V = l × w × h = {l}×{w}×{h} = {vol}.",
        ))
    return out


def generate_angle_sum_triangle() -> list[dict]:
    """T2: third angle of a triangle (sum 180°)."""
    out = []
    # pick two angles, ask third
    pairs = [(60, 60), (90, 45), (30, 60), (45, 90), (50, 70), (40, 80),
             (35, 55), (25, 65), (75, 75), (100, 40), (110, 30), (120, 30),
             (85, 35), (95, 35), (105, 25), (50, 50), (65, 75), (33, 47),
             (28, 92), (42, 88), (60, 80), (45, 105)]
    for a, b in pairs:
        c = 180 - a - b
        if c <= 0:
            continue
        ans = f"{c}°"
        dist = [f"{a + b}°", f"{180 - c}°", f"{c + 10}°"]
        out.append(make_question(
            tier=2, topic_cell="geometry_basics",
            strategy="angle_sum_triangle", pillar="computation",
            question=f"Triangle has angles {a}° and {b}°. Third angle?",
            answer=ans, distractors=dist,
            context=f"Angles in a triangle sum to 180°. 180−{a}−{b} = {c}.",
        ))
    return out


def generate_all_geometry() -> list[dict]:
    out = []
    out.extend(generate_rectangle_area())
    out.extend(generate_rectangle_perimeter())
    out.extend(generate_triangle_area())
    out.extend(generate_circle_area_approx())
    out.extend(generate_circle_circumference_approx())
    out.extend(generate_pythagorean_triples())
    out.extend(generate_volume_box())
    out.extend(generate_angle_sum_triangle())
    return out


if __name__ == "__main__":
    qs = generate_all_geometry()
    print(f"Generated {len(qs)} geometry questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
