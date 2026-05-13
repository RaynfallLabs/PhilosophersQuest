"""Element symbols + chemistry facts."""
from __future__ import annotations

from tools.quizgen.science_generators.common import make_question


# (element_name, symbol, atomic_number, brief_context)
ELEMENTS = [
    ("Hydrogen", "H", 1, "Lightest element; most abundant in universe."),
    ("Helium", "He", 2, "Second-lightest; noble gas; used in balloons + cryogenics."),
    ("Lithium", "Li", 3, "Lightest metal; used in batteries + mood stabilizers."),
    ("Beryllium", "Be", 4, "Toxic light metal; aerospace + X-ray windows."),
    ("Boron", "B", 5, "Metalloid; borax + boric acid."),
    ("Carbon", "C", 6, "Basis of organic chemistry + all known life."),
    ("Nitrogen", "N", 7, "78% of Earth's atmosphere."),
    ("Oxygen", "O", 8, "21% of atmosphere; essential for respiration."),
    ("Fluorine", "F", 9, "Most reactive nonmetal; in toothpaste as fluoride."),
    ("Neon", "Ne", 10, "Noble gas; orange-red glow in signs."),
    ("Sodium", "Na", 11, "Soft alkali metal; from Latin natrium."),
    ("Magnesium", "Mg", 12, "Burns bright white; in chlorophyll."),
    ("Aluminum", "Al", 13, "Most abundant metal in Earth's crust."),
    ("Silicon", "Si", 14, "Second-most abundant in crust; semiconductors."),
    ("Phosphorus", "P", 15, "Essential for DNA + ATP; bone."),
    ("Sulfur", "S", 16, "Yellow nonmetal; smells like rotten eggs as H₂S."),
    ("Chlorine", "Cl", 17, "Halogen; pool sanitizer; table salt component."),
    ("Argon", "Ar", 18, "Third-most abundant in atmosphere; inert."),
    ("Potassium", "K", 19, "From Latin kalium; essential electrolyte; bananas."),
    ("Calcium", "Ca", 20, "Bones + teeth + signaling; dairy + leafy greens."),
    ("Iron", "Fe", 26, "From Latin ferrum; hemoglobin; magnetic."),
    ("Copper", "Cu", 29, "From Latin cuprum; electrical wiring; coins."),
    ("Zinc", "Zn", 30, "Essential trace element; brass component."),
    ("Silver", "Ag", 47, "From Latin argentum; most reflective metal."),
    ("Tin", "Sn", 50, "From Latin stannum; bronze component."),
    ("Iodine", "I", 53, "Essential for thyroid; iodized salt."),
    ("Gold", "Au", 79, "From Latin aurum; non-reactive precious metal."),
    ("Mercury", "Hg", 80, "From Latin hydrargyrum (water-silver); only liquid metal at room temp."),
    ("Lead", "Pb", 82, "From Latin plumbum; toxic dense metal."),
    ("Uranium", "U", 92, "Heaviest naturally occurring; nuclear fuel + weapons."),
    ("Plutonium", "Pu", 94, "Synthetic transuranium; nuclear weapons + reactors."),
    ("Tungsten", "W", 74, "From German Wolfram; highest melting point of metals."),
    ("Platinum", "Pt", 78, "Catalytic converters; jewelry; dense + non-reactive."),
    ("Nickel", "Ni", 28, "Stainless steel; coins; magnetic."),
    ("Cobalt", "Co", 27, "Cobalt blue pigment; lithium-ion batteries."),
    ("Titanium", "Ti", 22, "Strong + light; aerospace + medical implants."),
    ("Chromium", "Cr", 24, "Stainless steel; chrome plating."),
    ("Manganese", "Mn", 25, "Steel hardening; essential trace nutrient."),
]


def generate_element_symbol() -> list[dict]:
    """T1: element → symbol."""
    out = []
    all_symbols = [s for _, s, _, _ in ELEMENTS]
    for name, symbol, _z, ctx in ELEMENTS:
        distractors = [s for s in all_symbols if s != symbol][:3]
        out.append(make_question(
            tier=1, topic_cell="chemistry",
            strategy="element_symbols_common", pillar="chemistry",
            question=f"Chemical symbol for {name}:",
            answer=symbol, distractors=distractors,
            context=ctx,
        ))
    return out


def generate_symbol_to_element() -> list[dict]:
    """T1-T2: symbol → element name."""
    out = []
    all_names = [n for n, _, _, _ in ELEMENTS]
    for name, symbol, _z, ctx in ELEMENTS:
        distractors = [n for n in all_names if n != name][:3]
        out.append(make_question(
            tier=2, topic_cell="chemistry",
            strategy="symbol_to_element", pillar="chemistry",
            question=f"The element with symbol {symbol} is:",
            answer=name, distractors=distractors,
            context=ctx,
        ))
    return out


def generate_atomic_number() -> list[dict]:
    """T2: element → atomic number (the famous ones)."""
    out = []
    famous = [(n, str(z)) for n, _, z, _ in ELEMENTS]
    for name, _, z, ctx in ELEMENTS:
        z_str = str(z)
        wrong_z = [str(zz) for nn, _, zz, _ in ELEMENTS if zz != z][:3]
        out.append(make_question(
            tier=2, topic_cell="chemistry",
            strategy="atomic_number_definition", pillar="chemistry",
            question=f"Atomic number of {name}:",
            answer=z_str, distractors=wrong_z,
            context=f"{ctx}",
        ))
    return out


def generate_all_chemistry() -> list[dict]:
    out = []
    out.extend(generate_element_symbol())
    out.extend(generate_symbol_to_element())
    out.extend(generate_atomic_number())
    return out


if __name__ == "__main__":
    qs = generate_all_chemistry()
    print(f"Generated {len(qs)} chemistry questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
