"""SI units + prefixes + basic physics constants."""
from __future__ import annotations

from tools.quizgen.science_generators.common import make_question


# (quantity, SI_unit_full, SI_symbol, ctx)
SI_UNITS = [
    ("length", "meter", "m", "Defined by speed of light since 1983."),
    ("mass", "kilogram", "kg", "Redefined 2019 using Planck constant."),
    ("time", "second", "s", "Defined by Cs-133 atomic transition."),
    ("electric current", "ampere", "A", "Defined by elementary charge."),
    ("temperature", "kelvin", "K", "0 K is absolute zero."),
    ("amount of substance", "mole", "mol", "6.022 × 10²³ entities (Avogadro)."),
    ("luminous intensity", "candela", "cd", "Approximately one candle."),
    ("force", "newton", "N", "kg·m/s² — named for Isaac Newton."),
    ("energy", "joule", "J", "kg·m²/s² — named for James Joule."),
    ("power", "watt", "W", "Joules per second — named for James Watt."),
    ("pressure", "pascal", "Pa", "N/m² — named for Blaise Pascal."),
    ("frequency", "hertz", "Hz", "Cycles per second — named for Heinrich Hertz."),
    ("electric potential", "volt", "V", "Named for Alessandro Volta."),
    ("electric resistance", "ohm", "Ω", "Named for Georg Ohm."),
    ("electric charge", "coulomb", "C", "Named for Charles-Augustin de Coulomb."),
    ("magnetic flux density", "tesla", "T", "Named for Nikola Tesla."),
]


def generate_si_units() -> list[dict]:
    """T1-T2: SI unit names."""
    out = []
    all_units = [u for _, u, _, _ in SI_UNITS]
    for quantity, unit, _sym, ctx in SI_UNITS:
        distractors = [u for u in all_units if u != unit][:3]
        out.append(make_question(
            tier=2, topic_cell="physics",
            strategy="si_unit_attribution", pillar="physics",
            question=f"The SI unit of {quantity} is the:",
            answer=unit, distractors=distractors,
            context=ctx,
        ))
    return out


# SI prefixes
SI_PREFIXES = [
    ("kilo", "k", "10³ (1,000)", "Kilometer = 1,000 meters."),
    ("mega", "M", "10⁶ (1,000,000)", "Megabyte = ~1 million bytes."),
    ("giga", "G", "10⁹ (1 billion)", "Gigabyte = ~1 billion bytes."),
    ("tera", "T", "10¹² (1 trillion)", "Terabyte."),
    ("peta", "P", "10¹⁵ (1 quadrillion)", "Petabyte."),
    ("milli", "m", "10⁻³ (1/1,000)", "Millimeter = 1/1000 meter."),
    ("micro", "μ", "10⁻⁶ (1 millionth)", "Micrometer = 1/million meter."),
    ("nano", "n", "10⁻⁹ (1 billionth)", "Nanometer = 1/billion meter."),
    ("pico", "p", "10⁻¹² (1 trillionth)", "Picosecond."),
    ("centi", "c", "10⁻² (1/100)", "Centimeter = 1/100 meter."),
    ("hecto", "h", "10² (100)", "Hectare = 10,000 m²."),
    ("deci", "d", "10⁻¹ (1/10)", "Decimeter = 1/10 meter."),
]


def generate_si_prefixes() -> list[dict]:
    out = []
    all_meanings = [m for _, _, m, _ in SI_PREFIXES]
    for prefix, _sym, meaning, ctx in SI_PREFIXES:
        distractors = [m for m in all_meanings if m != meaning][:3]
        out.append(make_question(
            tier=2, topic_cell="physics",
            strategy="si_prefixes", pillar="physics",
            question=f"The SI prefix '{prefix}-' means:",
            answer=meaning, distractors=distractors,
            context=ctx,
        ))
    return out


def generate_all_physics_units() -> list[dict]:
    return generate_si_units() + generate_si_prefixes()


if __name__ == "__main__":
    qs = generate_all_physics_units()
    print(f"Generated {len(qs)} physics/unit questions")
