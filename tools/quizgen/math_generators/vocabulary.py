"""Vocabulary / concept-recognition strategies (Pillar 2).

Names for shapes, angles, properties, number categories, operations.
The pedagogical principle (Pimm 1987): students stall on word problems
when they don't recognize 'rhombus', 'supplementary', 'quotient',
'congruent'. Low-stakes exposure builds it.
"""
from __future__ import annotations

from tools.quizgen.math_generators.common import make_question


# ----- 2D shapes -----
def generate_polygon_by_side_count() -> list[dict]:
    """T1: triangle..decagon by side count. Two phrasings each."""
    out = []
    polygons = [
        (3, "triangle"), (4, "quadrilateral"), (5, "pentagon"),
        (6, "hexagon"), (7, "heptagon"), (8, "octagon"),
        (9, "nonagon"), (10, "decagon"), (12, "dodecagon"),
    ]
    all_names = [p[1].capitalize() for p in polygons]
    for sides, name in polygons:
        capname = name.capitalize()
        other_names = [n for n in all_names if n != capname]
        # Q1: name → sides
        out.append(make_question(
            tier=1, topic_cell="geometry_basics",
            strategy="polygon_by_side_count", pillar="vocabulary",
            question=f"How many sides does a {name} have?",
            answer=str(sides),
            distractors=[str(sides + 1), str(sides - 1), str(sides + 2)],
            context=f"A {name} has {sides} sides. Greek root: '{name[:-3] if len(name) > 5 else name}' means {sides}.",
        ))
        # Q2: sides → name
        out.append(make_question(
            tier=1, topic_cell="geometry_basics",
            strategy="polygon_by_side_count", pillar="vocabulary",
            question=f"A polygon with {sides} sides is called?",
            answer=capname,
            distractors=other_names[:3],
            context=f"{sides} sides → {name}.",
        ))
    return out


def generate_triangle_by_sides() -> list[dict]:
    """T2: equilateral / isosceles / scalene."""
    out = []
    cases = [
        ("all 3 sides equal", "Equilateral", ["Isosceles", "Scalene", "Right"]),
        ("exactly 2 sides equal", "Isosceles", ["Equilateral", "Scalene", "Obtuse"]),
        ("no sides equal", "Scalene", ["Equilateral", "Isosceles", "Acute"]),
    ]
    for desc, name, dist in cases:
        out.append(make_question(
            tier=2, topic_cell="geometry_basics",
            strategy="triangle_by_sides", pillar="vocabulary",
            question=f"A triangle with {desc} is called?",
            answer=name, distractors=dist,
            context=f"{name} = {desc}.",
        ))
    # also: reverse direction (name → description)
    for desc, name, dist in cases:
        out.append(make_question(
            tier=2, topic_cell="geometry_basics",
            strategy="triangle_by_sides", pillar="vocabulary",
            question=f"What defines an {name.lower()} triangle?",
            answer=desc.capitalize(),
            distractors=[d for d, _, _ in cases if d != desc][:3] or ["All angles equal", "Has a right angle", "Sum of angles is 180°"],
            context=f"An {name.lower()} triangle has {desc}.",
        ))
    return out


def generate_triangle_by_angles() -> list[dict]:
    """T2: acute / right / obtuse."""
    out = []
    cases = [
        ("a 90° angle", "Right", ["Acute", "Obtuse", "Equilateral"]),
        ("all angles less than 90°", "Acute", ["Right", "Obtuse", "Isosceles"]),
        ("one angle greater than 90°", "Obtuse", ["Acute", "Right", "Scalene"]),
    ]
    for desc, name, dist in cases:
        out.append(make_question(
            tier=2, topic_cell="geometry_basics",
            strategy="triangle_by_angles", pillar="vocabulary",
            question=f"A triangle with {desc} is called?",
            answer=name, distractors=dist,
            context=f"{name} triangle: {desc}.",
        ))
    return out


def generate_quadrilateral_types() -> list[dict]:
    """T2: square, rectangle, rhombus, parallelogram, trapezoid, kite."""
    out = []
    cases = [
        ("4 right angles and 4 equal sides", "Square", ["Rectangle", "Rhombus", "Parallelogram"]),
        ("4 right angles, opposite sides equal", "Rectangle", ["Square", "Parallelogram", "Rhombus"]),
        ("4 equal sides but angles aren't all 90°", "Rhombus", ["Square", "Trapezoid", "Parallelogram"]),
        ("opposite sides parallel and equal", "Parallelogram", ["Trapezoid", "Rectangle", "Kite"]),
        ("exactly one pair of parallel sides", "Trapezoid", ["Parallelogram", "Rhombus", "Kite"]),
        ("two pairs of adjacent equal sides", "Kite", ["Rhombus", "Parallelogram", "Trapezoid"]),
    ]
    for desc, name, dist in cases:
        out.append(make_question(
            tier=2, topic_cell="geometry_basics",
            strategy="quadrilateral_types", pillar="vocabulary",
            question=f"A quadrilateral with {desc} is called?",
            answer=name, distractors=dist,
            context=f"{name}: {desc}.",
        ))
    return out


def generate_solids_basic() -> list[dict]:
    """T2: cube, sphere, cylinder, cone, pyramid, prism."""
    out = []
    cases = [
        ("6 square faces", "Cube", ["Cuboid", "Prism", "Pyramid"]),
        ("a perfectly round 3D shape", "Sphere", ["Circle", "Cylinder", "Cone"]),
        ("two circular ends joined by a curved surface", "Cylinder", ["Cone", "Sphere", "Prism"]),
        ("a circular base tapering to a point", "Cone", ["Pyramid", "Cylinder", "Sphere"]),
        ("a polygonal base and triangular faces meeting at a point", "Pyramid", ["Cone", "Prism", "Tetrahedron"]),
        ("two identical polygonal bases connected by rectangles", "Prism", ["Pyramid", "Cylinder", "Cone"]),
    ]
    for desc, name, dist in cases:
        out.append(make_question(
            tier=2, topic_cell="geometry_basics",
            strategy="solids_basic", pillar="vocabulary",
            question=f"3D shape with {desc}:",
            answer=name, distractors=dist,
            context=f"{name}: {desc}.",
        ))
    return out


def generate_solid_components() -> list[dict]:
    """T2: vertex / edge / face counts on common solids."""
    out = []
    cases = [
        ("How many edges does a cube have?", "12", ["8", "6", "24"], "Cube: 12 edges, 8 vertices, 6 faces."),
        ("How many vertices does a cube have?", "8", ["6", "12", "4"], "8 corners."),
        ("How many faces does a cube have?", "6", ["8", "12", "4"], "6 squares."),
        ("How many edges does a tetrahedron have?", "6", ["4", "8", "12"], "Tetrahedron: 4 faces, 4 vertices, 6 edges."),
        ("How many faces does a tetrahedron have?", "4", ["6", "8", "3"], "All triangles."),
        ("How many vertices does a square pyramid have?", "5", ["4", "6", "8"], "4 base corners + 1 apex."),
        ("How many edges does an octahedron have?", "12", ["8", "6", "10"], "8 faces, 6 vertices, 12 edges."),
        ("Vertex, edge, face — which is a 0-dimensional point?", "Vertex", ["Edge", "Face", "Surface"], "Vertex = a single point."),
    ]
    for q, a, d, ctx in cases:
        out.append(make_question(
            tier=2, topic_cell="geometry_basics",
            strategy="solid_components", pillar="vocabulary",
            question=q, answer=a, distractors=d, context=ctx,
        ))
    return out


def generate_platonic_solids() -> list[dict]:
    """T4: the five regular polyhedra."""
    out = []
    cases = [
        ("4 equilateral triangle faces", "Tetrahedron", ["Cube", "Octahedron", "Pyramid"]),
        ("6 square faces", "Cube (hexahedron)", ["Tetrahedron", "Octahedron", "Dodecahedron"]),
        ("8 equilateral triangle faces", "Octahedron", ["Cube", "Icosahedron", "Tetrahedron"]),
        ("12 pentagonal faces", "Dodecahedron", ["Icosahedron", "Octahedron", "Cube"]),
        ("20 equilateral triangle faces", "Icosahedron", ["Dodecahedron", "Octahedron", "Tetrahedron"]),
        ("How many Platonic solids exist?", "5", ["4", "6", "Infinite"]),
    ]
    for desc, name, dist in cases[:5]:
        out.append(make_question(
            tier=4, topic_cell="geometry_advanced",
            strategy="platonic_solids", pillar="vocabulary",
            question=f"Platonic solid with {desc}:",
            answer=name, distractors=dist,
            context=f"{name}: {desc}. One of the five Platonic solids.",
        ))
    out.append(make_question(
        tier=4, topic_cell="geometry_advanced",
        strategy="platonic_solids", pillar="vocabulary",
        question="How many Platonic solids exist?", answer="5",
        distractors=["4", "6", "Infinite"],
        context="Euclid proved exactly 5: tetrahedron, cube, octahedron, dodecahedron, icosahedron.",
    ))
    return out


# ----- angles -----
def generate_angle_types() -> list[dict]:
    """T1-T2: acute / right / obtuse / straight / reflex."""
    out = []
    cases = [
        (45, "Acute", ["Right", "Obtuse", "Straight"]),
        (30, "Acute", ["Right", "Obtuse", "Reflex"]),
        (90, "Right", ["Acute", "Obtuse", "Straight"]),
        (110, "Obtuse", ["Acute", "Right", "Straight"]),
        (135, "Obtuse", ["Acute", "Right", "Reflex"]),
        (170, "Obtuse", ["Reflex", "Right", "Straight"]),
        (180, "Straight", ["Obtuse", "Right", "Reflex"]),
        (200, "Reflex", ["Obtuse", "Straight", "Right"]),
        (300, "Reflex", ["Obtuse", "Straight", "Acute"]),
    ]
    for deg, name, dist in cases:
        out.append(make_question(
            tier=1, topic_cell="geometry_basics",
            strategy="angle_types", pillar="vocabulary",
            question=f"A {deg}° angle is called?",
            answer=name, distractors=dist,
            context=f"Acute<90, Right=90, Obtuse 90-180, Straight=180, Reflex>180. {deg}° → {name}.",
        ))
    return out


def generate_angle_pair_relationships() -> list[dict]:
    """T2: complementary, supplementary, vertical."""
    out = []
    cases = [
        ("Two angles that sum to 90°:", "Complementary", ["Supplementary", "Vertical", "Adjacent"]),
        ("Two angles that sum to 180°:", "Supplementary", ["Complementary", "Vertical", "Adjacent"]),
        ("Angles across from each other at a line intersection:", "Vertical", ["Adjacent", "Complementary", "Supplementary"]),
        ("Complement of 30°:", "60°", ["150°", "90°", "120°"]),
        ("Complement of 45°:", "45°", ["135°", "90°", "180°"]),
        ("Supplement of 60°:", "120°", ["30°", "90°", "150°"]),
        ("Supplement of 110°:", "70°", ["20°", "180°", "90°"]),
        ("Supplement of 90°:", "90°", ["0°", "180°", "45°"]),
    ]
    for q, a, d in cases:
        ctx = "Complementary = sum to 90°; supplementary = sum to 180°."
        out.append(make_question(
            tier=2, topic_cell="geometry_basics",
            strategy="angle_pair_relationships", pillar="vocabulary",
            question=q, answer=a, distractors=d, context=ctx,
        ))
    return out


def generate_parallel_line_angles() -> list[dict]:
    """T3: alternate-interior, corresponding, co-interior."""
    out = []
    cases = [
        ("Angles in the same position at each intersection of a transversal:", "Corresponding", ["Alternate interior", "Vertical", "Co-interior"]),
        ("Angles on opposite sides of the transversal, between the parallel lines:", "Alternate interior", ["Corresponding", "Co-interior", "Vertical"]),
        ("Angles on the same side of the transversal, between the parallel lines, that sum to 180°:", "Co-interior", ["Corresponding", "Alternate exterior", "Vertical"]),
    ]
    for q, a, d in cases:
        out.append(make_question(
            tier=3, topic_cell="geometry_advanced",
            strategy="parallel_line_angles", pillar="vocabulary",
            question=q, answer=a, distractors=d,
            context=f"{a} angles: a defining feature of parallel-line geometry.",
        ))
    return out


# ----- number categories -----
def generate_even_odd() -> list[dict]:
    """T1: even/odd recognition."""
    out = []
    for n in [4, 7, 11, 16, 22, 33, 48, 51, 64, 77, 90, 101, 100, 102, 999]:
        is_even = n % 2 == 0
        ans = "Even" if is_even else "Odd"
        dist = ["Odd" if is_even else "Even", "Prime", "Composite"]
        out.append(make_question(
            tier=1, topic_cell="number_theory",
            strategy="even_odd", pillar="vocabulary",
            question=f"Is {n} even or odd?",
            answer=ans, distractors=dist,
            context=f"{n} ends in {n%10} — {ans.lower()}.",
        ))
    return out


def generate_figurate_numbers() -> list[dict]:
    """T3: square, triangular, perfect numbers."""
    out = []
    cases = [
        ("Which is a triangular number?", "10", ["12", "11", "13"], "1,3,6,10,15,21..."),
        ("Which is a square number?", "16", ["14", "18", "20"], "1,4,9,16,25..."),
        ("Which is a perfect number?", "28", ["27", "30", "32"], "Perfect: equals sum of proper divisors. 6, 28, 496..."),
        ("First perfect number:", "6", ["1", "10", "12"], "1+2+3 = 6."),
        ("Sequence 1, 4, 9, 16, 25 are called ___ numbers.", "Square", ["Triangular", "Cubic", "Perfect"], "n² values."),
        ("Sequence 1, 3, 6, 10, 15 are called ___ numbers.", "Triangular", ["Square", "Fibonacci", "Perfect"], "n(n+1)/2."),
        ("Sequence 1, 1, 2, 3, 5, 8, 13... is called?", "Fibonacci", ["Triangular", "Square", "Arithmetic"], "Each term = sum of the two before it."),
    ]
    for q, a, d, ctx in cases:
        out.append(make_question(
            tier=3, topic_cell="number_theory",
            strategy="figurate_numbers", pillar="vocabulary",
            question=q, answer=a, distractors=d, context=ctx,
        ))
    return out


def generate_integer_rational_real() -> list[dict]:
    """T3: number-set classification."""
    out = []
    cases = [
        ("π belongs to which set?", "Irrational", ["Rational", "Integer", "Natural"], "π cannot be written as p/q."),
        ("−5 belongs to which set?", "Integer", ["Natural", "Whole", "Irrational"], "Integers include negatives."),
        ("0.5 belongs to which set?", "Rational", ["Irrational", "Integer", "Natural"], "0.5 = 1/2."),
        ("√2 belongs to which set?", "Irrational", ["Rational", "Integer", "Natural"], "Proved irrational by Pythagoreans."),
        ("Which is NOT a natural number?", "−3", ["1", "10", "100"], "Natural numbers are 1, 2, 3..."),
        ("Which is NOT rational?", "π", ["1/2", "3", "0.25"], "Rational = expressible as a fraction."),
        ("Which set contains 0?", "Whole", ["Natural", "Negative", "Imaginary"], "Whole = 0, 1, 2, 3..."),
    ]
    for q, a, d, ctx in cases:
        out.append(make_question(
            tier=3, topic_cell="number_theory",
            strategy="integer_rational_real", pillar="vocabulary",
            question=q, answer=a, distractors=d, context=ctx,
        ))
    return out


def generate_irrational_famous() -> list[dict]:
    """T4: π, e, √2, φ."""
    out = []
    cases = [
        ("Ratio of a circle's circumference to its diameter:", "π", ["e", "φ", "√2"], "π ≈ 3.14159..."),
        ("Base of the natural logarithm:", "e", ["π", "φ", "i"], "e ≈ 2.71828..."),
        ("The golden ratio:", "φ", ["π", "e", "√3"], "φ = (1+√5)/2 ≈ 1.618."),
        ("Length of a unit square's diagonal:", "√2", ["π", "e", "φ"], "1²+1² = 2; diag = √2."),
        ("Which is approximately 2.718?", "e", ["π", "φ", "√2"], ""),
        ("Which is approximately 1.618?", "φ", ["π", "e", "√2"], "Golden ratio."),
        ("Which is approximately 1.414?", "√2", ["π", "e", "φ"], "Pythagorean diagonal."),
        ("Which is approximately 3.14?", "π", ["e", "φ", "√3"], ""),
    ]
    for q, a, d, ctx in cases:
        out.append(make_question(
            tier=4, topic_cell="number_theory",
            strategy="irrational_famous", pillar="vocabulary",
            question=q, answer=a, distractors=d, context=ctx,
        ))
    return out


# ----- operations vocabulary -----
def generate_operation_names_basic() -> list[dict]:
    """T1-T2: sum, difference, product, quotient, remainder."""
    out = []
    cases = [
        ("The result of an addition is called the ___.", "Sum", ["Product", "Difference", "Quotient"]),
        ("The result of a subtraction is called the ___.", "Difference", ["Sum", "Product", "Quotient"]),
        ("The result of a multiplication is called the ___.", "Product", ["Sum", "Quotient", "Total"]),
        ("The result of a division is called the ___.", "Quotient", ["Sum", "Product", "Difference"]),
        ("What's left over when dividing is called the ___.", "Remainder", ["Quotient", "Divisor", "Dividend"]),
        ("If a÷b = c with r left, c is the:", "Quotient", ["Remainder", "Dividend", "Divisor"]),
        ("If a÷b = c with r left, a is the:", "Dividend", ["Divisor", "Quotient", "Remainder"]),
        ("If a÷b = c with r left, b is the:", "Divisor", ["Dividend", "Quotient", "Remainder"]),
    ]
    for q, a, d in cases:
        out.append(make_question(
            tier=2, topic_cell="basic_arithmetic",
            strategy="operation_names_basic", pillar="vocabulary",
            question=q, answer=a, distractors=d,
            context=f"Operation vocabulary: {a}.",
        ))
    return out


def generate_fraction_parts() -> list[dict]:
    """T2: numerator, denominator, reciprocal, mixed/improper."""
    out = []
    cases = [
        ("Top number of a fraction is called the ___.", "Numerator", ["Denominator", "Divisor", "Quotient"]),
        ("Bottom number of a fraction is called the ___.", "Denominator", ["Numerator", "Divisor", "Dividend"]),
        ("Flip a fraction (3/4 → 4/3) and you get its ___.", "Reciprocal", ["Inverse", "Opposite", "Conjugate"]),
        ("A fraction whose numerator ≥ denominator is called?", "Improper fraction", ["Mixed number", "Proper fraction", "Decimal"]),
        ("A whole number plus a fraction (3½) is a ___.", "Mixed number", ["Improper fraction", "Compound fraction", "Decimal"]),
        ("Reciprocal of 5:", "1/5", ["5/1", "−5", "0.5"]),
        ("Reciprocal of 2/3:", "3/2", ["2/3", "−2/3", "1/2"]),
    ]
    for case in cases:
        q, a, d = case[0], case[1], case[2]
        out.append(make_question(
            tier=2, topic_cell="fractions_and_decimals",
            strategy="fraction_parts", pillar="vocabulary",
            question=q, answer=a, distractors=d,
            context=f"Fraction vocabulary: {a}.",
        ))
    return out


# ----- properties -----
def generate_property_names() -> list[dict]:
    """T2: commutative, associative, distributive, identity, inverse."""
    out = []
    cases = [
        ("Property that says a + b = b + a:", "Commutative", ["Associative", "Distributive", "Identity"]),
        ("Property that says (a + b) + c = a + (b + c):", "Associative", ["Commutative", "Distributive", "Inverse"]),
        ("Property that says a(b + c) = ab + ac:", "Distributive", ["Commutative", "Associative", "Identity"]),
        ("0 is the identity for which operation?", "Addition", ["Multiplication", "Division", "Subtraction"]),
        ("1 is the identity for which operation?", "Multiplication", ["Addition", "Subtraction", "Division"]),
        ("The additive inverse of 7 is:", "−7", ["1/7", "7", "0"]),
        ("The multiplicative inverse of 4 is:", "1/4", ["−4", "4", "0"]),
        ("Is subtraction commutative?", "No", ["Yes", "Sometimes", "Only for positives"]),
        ("Is multiplication commutative?", "Yes", ["No", "Only for whole numbers", "Sometimes"]),
        ("In 3(x+5) = 3x+15, which property is used?", "Distributive", ["Commutative", "Associative", "Identity"]),
    ]
    for q, a, d in cases:
        out.append(make_question(
            tier=2, topic_cell="basic_arithmetic",
            strategy="property_names", pillar="vocabulary",
            question=q, answer=a, distractors=d,
            context=f"Property: {a}.",
        ))
    return out


# ----- geometry vocabulary -----
def generate_perimeter_area_volume_words() -> list[dict]:
    """T2: perimeter vs area vs volume vs surface area."""
    out = []
    cases = [
        ("Distance around a 2D shape:", "Perimeter", ["Area", "Volume", "Circumference"]),
        ("Distance around a circle:", "Circumference", ["Perimeter", "Diameter", "Radius"]),
        ("Space inside a 2D shape:", "Area", ["Perimeter", "Volume", "Diameter"]),
        ("Space inside a 3D shape:", "Volume", ["Area", "Surface area", "Perimeter"]),
        ("Sum of the areas of all faces of a 3D shape:", "Surface area", ["Volume", "Perimeter", "Diameter"]),
        ("Units for area:", "Square units (cm²)", ["Linear units (cm)", "Cubic units (cm³)", "Degrees"]),
        ("Units for volume:", "Cubic units (cm³)", ["Square units (cm²)", "Linear units (cm)", "Radians"]),
    ]
    for q, a, d in cases:
        out.append(make_question(
            tier=2, topic_cell="geometry_basics",
            strategy="perimeter_area_volume_words", pillar="vocabulary",
            question=q, answer=a, distractors=d,
            context="Distinguishing measures.",
        ))
    return out


def generate_circle_vocabulary() -> list[dict]:
    """T2: radius, diameter, chord, arc, sector, tangent."""
    out = []
    cases = [
        ("Line from center to edge of a circle:", "Radius", ["Diameter", "Chord", "Tangent"]),
        ("Line across a circle through its center:", "Diameter", ["Radius", "Chord", "Arc"]),
        ("Any straight line between two points on a circle:", "Chord", ["Diameter", "Tangent", "Arc"]),
        ("Part of the circle's edge:", "Arc", ["Chord", "Diameter", "Sector"]),
        ("Pie-slice region of a circle:", "Sector", ["Arc", "Chord", "Segment"]),
        ("Line touching a circle at exactly one point:", "Tangent", ["Chord", "Secant", "Diameter"]),
        ("Diameter equals how many radii?", "2", ["1", "π", "4"]),
        ("If radius = 5, diameter = ?", "10", ["2.5", "25", "π·5"]),
    ]
    for q, a, d in cases:
        out.append(make_question(
            tier=2, topic_cell="geometry_basics",
            strategy="circle_vocabulary", pillar="vocabulary",
            question=q, answer=a, distractors=d,
            context="Circle parts.",
        ))
    return out


def generate_line_relationships() -> list[dict]:
    """T2: parallel, perpendicular, intersecting, skew."""
    out = []
    cases = [
        ("Lines that never meet:", "Parallel", ["Perpendicular", "Intersecting", "Skew"]),
        ("Lines meeting at a right angle:", "Perpendicular", ["Parallel", "Intersecting", "Skew"]),
        ("Lines crossing at any angle:", "Intersecting", ["Parallel", "Skew", "Tangent"]),
        ("3D lines that don't intersect AND aren't parallel:", "Skew", ["Parallel", "Perpendicular", "Intersecting"]),
        ("Two perpendicular lines form an angle of:", "90°", ["180°", "45°", "0°"]),
    ]
    for q, a, d in cases:
        out.append(make_question(
            tier=2, topic_cell="geometry_basics",
            strategy="line_relationships", pillar="vocabulary",
            question=q, answer=a, distractors=d,
            context="Line relationship vocabulary.",
        ))
    return out


def generate_congruent_similar() -> list[dict]:
    """T3: congruent vs similar."""
    out = []
    cases = [
        ("Two shapes the same size AND shape are:", "Congruent", ["Similar", "Equal", "Identical"]),
        ("Two shapes the same shape but possibly different sizes are:", "Similar", ["Congruent", "Equivalent", "Equal"]),
        ("If two triangles are similar, corresponding angles are:", "Equal", ["Supplementary", "Complementary", "Sum to 90°"]),
        ("If two triangles are similar, corresponding sides are:", "Proportional", ["Equal", "Perpendicular", "Parallel"]),
        ("All squares are similar — but are they all congruent?", "No", ["Yes", "Only if same color", "Depends on rotation"]),
    ]
    for q, a, d in cases:
        out.append(make_question(
            tier=3, topic_cell="geometry_advanced",
            strategy="congruent_similar", pillar="vocabulary",
            question=q, answer=a, distractors=d,
            context="Congruent = same; similar = scaled.",
        ))
    return out


# ----- statistics -----
def generate_central_tendency() -> list[dict]:
    """T3: mean, median, mode, range."""
    out = []
    cases = [
        ("The arithmetic average:", "Mean", ["Median", "Mode", "Range"]),
        ("The middle value when sorted:", "Median", ["Mean", "Mode", "Range"]),
        ("The most-frequent value:", "Mode", ["Mean", "Median", "Range"]),
        ("Max minus min:", "Range", ["Mean", "Median", "Variance"]),
        ("Mean of 2, 4, 6, 8:", "5", ["4", "6", "20"]),
        ("Median of 1, 3, 5, 7, 9:", "5", ["3", "7", "4.5"]),
        ("Mode of 2, 3, 3, 5, 7:", "3", ["2", "5", "4"]),
        ("Range of 3, 9, 5, 1, 8:", "8", ["5", "9", "1"]),
        ("If data has no repeats, the mode is:", "None / undefined", ["The mean", "The smallest", "The largest"]),
    ]
    for q, a, d in cases:
        out.append(make_question(
            tier=3, topic_cell="statistics",
            strategy="central_tendency", pillar="vocabulary",
            question=q, answer=a, distractors=d,
            context="Central tendency.",
        ))
    return out


def generate_prob_basic_words() -> list[dict]:
    """T2-T3: probability vocabulary."""
    out = []
    cases = [
        ("The set of all possible outcomes:", "Sample space", ["Event", "Probability", "Outcome"]),
        ("A specific outcome or set of outcomes:", "Event", ["Sample space", "Probability", "Trial"]),
        ("A number between 0 and 1 expressing likelihood:", "Probability", ["Odds", "Frequency", "Mean"]),
        ("Probability of an impossible event:", "0", ["1", "1/2", "−1"]),
        ("Probability of a certain event:", "1", ["0", "100", "0.5"]),
        ("Probability of heads on a fair coin:", "1/2", ["1/4", "1", "0"]),
        ("Probability of rolling a 6 on a fair die:", "1/6", ["1/2", "1/3", "6"]),
        ("Two events that can't both happen are called:", "Mutually exclusive", ["Independent", "Complementary", "Dependent"]),
        ("Two events whose outcomes don't influence each other are:", "Independent", ["Mutually exclusive", "Dependent", "Complementary"]),
    ]
    for q, a, d in cases:
        out.append(make_question(
            tier=3, topic_cell="probability",
            strategy="prob_basic_words", pillar="vocabulary",
            question=q, answer=a, distractors=d,
            context="Probability vocabulary.",
        ))
    return out


# ----- quantity names -----
def generate_quantity_names() -> list[dict]:
    """T1-T2: dozen, score, gross, baker's dozen, time periods."""
    out = []
    cases = [
        ("A dozen equals:", "12", ["10", "13", "20"], "12 — a dozen eggs, a dozen donuts."),
        ("A baker's dozen equals:", "13", ["12", "14", "15"], "Bakers added one extra to avoid being short-weight."),
        ("A score equals:", "20", ["10", "15", "30"], "Lincoln: 'Four score and seven years ago...'"),
        ("A gross equals:", "144", ["100", "120", "12"], "A gross = 12 × 12 = a dozen dozens."),
        ("A decade is how many years?", "10", ["100", "1000", "20"], ""),
        ("A century is how many years?", "100", ["10", "1000", "500"], ""),
        ("A millennium is how many years?", "1000", ["100", "10000", "500"], ""),
        ("Four score = ?", "80", ["40", "20", "100"], "4 × 20."),
    ]
    for q, a, d, ctx in cases:
        out.append(make_question(
            tier=1, topic_cell="number_sense",
            strategy="quantity_names", pillar="vocabulary",
            question=q, answer=a, distractors=d, context=ctx,
        ))
    return out


def generate_metric_prefixes() -> list[dict]:
    """T2-T3: kilo, mega, giga, milli, micro."""
    out = []
    cases = [
        ("Prefix 'kilo-' means:", "1,000", ["100", "10,000", "1,000,000"]),
        ("Prefix 'mega-' means:", "1,000,000", ["1,000", "1,000,000,000", "100,000"]),
        ("Prefix 'giga-' means:", "1,000,000,000", ["1,000,000", "100,000", "1,000,000,000,000"]),
        ("Prefix 'milli-' means:", "1/1,000", ["1/100", "1/10,000", "1/1,000,000"]),
        ("Prefix 'micro-' means:", "1/1,000,000", ["1/1,000", "1/100", "1/1,000,000,000"]),
        ("1 kilometer is how many meters?", "1,000", ["100", "10,000", "10"]),
        ("1 megabyte is how many bytes?", "1,000,000", ["1,000", "1,000,000,000", "100,000"]),
        ("1 millimeter is what fraction of a meter?", "1/1,000", ["1/100", "1/10", "1/1,000,000"]),
    ]
    for q, a, d in cases:
        out.append(make_question(
            tier=2, topic_cell="number_sense",
            strategy="metric_prefixes", pillar="vocabulary",
            question=q, answer=a, distractors=d,
            context="Metric prefixes scale by powers of 10.",
        ))
    return out


def generate_all_vocabulary() -> list[dict]:
    out = []
    out.extend(generate_polygon_by_side_count())
    out.extend(generate_triangle_by_sides())
    out.extend(generate_triangle_by_angles())
    out.extend(generate_quadrilateral_types())
    out.extend(generate_solids_basic())
    out.extend(generate_solid_components())
    out.extend(generate_platonic_solids())
    out.extend(generate_angle_types())
    out.extend(generate_angle_pair_relationships())
    out.extend(generate_parallel_line_angles())
    out.extend(generate_even_odd())
    out.extend(generate_figurate_numbers())
    out.extend(generate_integer_rational_real())
    out.extend(generate_irrational_famous())
    out.extend(generate_operation_names_basic())
    out.extend(generate_fraction_parts())
    out.extend(generate_property_names())
    out.extend(generate_perimeter_area_volume_words())
    out.extend(generate_circle_vocabulary())
    out.extend(generate_line_relationships())
    out.extend(generate_congruent_similar())
    out.extend(generate_central_tendency())
    out.extend(generate_prob_basic_words())
    out.extend(generate_quantity_names())
    out.extend(generate_metric_prefixes())
    return out


if __name__ == "__main__":
    qs = generate_all_vocabulary()
    print(f"Generated {len(qs)} vocabulary questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
