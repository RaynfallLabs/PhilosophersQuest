"""Food safety strategies: temperatures, cross-contamination, danger zone,
foodborne pathogens, safe thawing.
"""
from __future__ import annotations

from tools.quizgen.cooking_generators.common import make_question


SAFE_TEMPS = [
    ("Whole chicken / poultry", "165°F (74°C)", "Inserted into thickest part, not touching bone.", ["145°F (63°C)", "155°F (68°C)", "180°F (82°C)"]),
    ("Ground beef / pork", "160°F (71°C)", "Ground meat needs higher temp than whole cuts — bacteria mixed throughout.", ["140°F (60°C)", "155°F (68°C)", "180°F (82°C)"]),
    ("Beef steak (medium-rare)", "130-135°F (54-57°C)", "Whole-muscle beef — surface bacteria seared off, interior safe at lower temp.", ["165°F (74°C)", "180°F (82°C)", "100°F (38°C)"]),
    ("Pork chops / loins", "145°F (63°C) + 3 min rest", "USDA lowered from 160°F in 2011 after trichinella concerns largely eliminated.", ["165°F (74°C)", "180°F (82°C)", "130°F (54°C)"]),
    ("Fish", "145°F (63°C)", "Or until opaque and flakes with fork.", ["165°F (74°C)", "180°F (82°C)", "130°F (54°C)"]),
    ("Eggs (cooked dish, e.g., quiche)", "160°F (71°C)", "Eggs in mixed dish — fully cooked for safety.", ["145°F (63°C)", "180°F (82°C)", "120°F (49°C)"]),
    ("Leftovers reheated", "165°F (74°C)", "Reheat thoroughly — surface contamination from handling.", ["120°F (49°C)", "140°F (60°C)", "180°F (82°C)"]),
    ("Refrigerator setting", "Below 40°F (4°C)", "Below the upper bound of the bacterial danger zone.", ["50°F (10°C)", "32°F (0°C)", "60°F (16°C)"]),
    ("Freezer setting", "0°F (-18°C) or below", "Stops bacterial growth; doesn't kill bacteria.", ["32°F (0°C)", "20°F (-7°C)", "-40°F (-40°C)"]),
]


def generate_safe_temps() -> list[dict]:
    out = []
    for food, temp, ctx, distractors in SAFE_TEMPS:
        out.append(make_question(
            tier=2,
            topic_cell="food_safety",
            strategy="meat_doneness_temps",
            pillar="practical",
            question=f"Safe minimum internal temperature for {food}?",
            answer=temp,
            distractors=distractors,
            context=ctx,
        ))
    return out


# ----- Danger zone -----
def generate_danger_zone() -> list[dict]:
    return [
        make_question(
            tier=2, topic_cell="food_safety",
            strategy="temperature_danger_zone", pillar="practical",
            question="The \"danger zone\" — the temperature range where most foodborne bacteria multiply rapidly — is:",
            answer="40-140°F (4-60°C)",
            distractors=["32-100°F (0-38°C)", "70-200°F (21-93°C)", "0-50°F (-18-10°C)"],
            context="USDA standard. Food shouldn't sit in this range for more than 2 hours (1 hour above 90°F).",
        ),
        make_question(
            tier=2, topic_cell="food_safety",
            strategy="temperature_danger_zone", pillar="practical",
            question="A casserole sits at room temperature for how long before USDA considers it unsafe?",
            answer="2 hours",
            distractors=["30 minutes", "4 hours", "8 hours"],
            context="\"2-hour rule\" — cumulative time in the danger zone. 1 hour if above 90°F.",
        ),
        make_question(
            tier=2, topic_cell="food_safety",
            strategy="temperature_danger_zone", pillar="practical",
            question="A chef wraps and refrigerates a hot dish — how long can it cool through the danger zone before becoming a safety concern?",
            answer="Less than 2 hours (cool to 70°F within 2 hours; to 40°F within 4 more)",
            distractors=["Up to 6 hours", "Up to 12 hours", "Cooling time doesn't matter"],
            context="Two-stage cooling rule. Shallow containers + ice baths speed this.",
        ),
    ]


# ----- Pathogens -----
PATHOGENS = [
    ("Salmonella", "Raw chicken + eggs", "Most common US foodborne illness source — symptoms 6-72 hours.", ["Soft cheese", "Raw spinach", "Tuna"]),
    ("E. coli (O157:H7)", "Ground beef, leafy greens, unpasteurized cider", "Hemolytic uremic syndrome risk; Jack in the Box outbreak 1993 prompted reform.", ["Raw chicken", "Cured ham", "Cheese"]),
    ("Listeria", "Deli meats, soft cheeses, raw milk", "Particularly dangerous in pregnancy; FDA advisory.", ["Raw chicken", "Bread", "Honey"]),
    ("Norovirus", "Improperly handled produce, shellfish", "Most common foodborne illness — \"stomach flu\"; cruise ship outbreaks.", ["Raw chicken", "Hot dogs", "Bread"]),
    ("Campylobacter", "Raw poultry, unpasteurized milk", "Common but underreported; Guillain-Barré syndrome rare complication.", ["Soft cheese", "Bread", "Raw vegetables"]),
    ("Botulism (Clostridium)", "Improperly canned low-acid foods", "Toxin is what's deadly; bulging cans = warning sign; honey hazard for infants.", ["Raw chicken", "Bread", "Salad"]),
]


def generate_pathogens() -> list[dict]:
    out = []
    for pathogen, source, ctx, distractors in PATHOGENS:
        out.append(make_question(
            tier=3,
            topic_cell="food_safety",
            strategy="foodborne_pathogens_basic",
            pillar="practical",
            question=f"Which foodborne pathogen is most commonly associated with {source}?",
            answer=pathogen,
            distractors=distractors,
            context=ctx,
        ))
    return out


# ----- Cross-contamination -----
def generate_cross_contam() -> list[dict]:
    return [
        make_question(
            tier=2, topic_cell="food_safety",
            strategy="cross_contamination", pillar="practical",
            question="A cook cuts raw chicken on a cutting board, then chops lettuce on the same board. The risk is:",
            answer="Salmonella + Campylobacter transferring to lettuce",
            distractors=["No real risk — lettuce will be washed", "Only a risk if the chicken was warm", "Risk only if the knife wasn't rinsed"],
            context="Cutting boards must be sanitized between raw meat and ready-to-eat foods. Separate boards by color is one method.",
        ),
        make_question(
            tier=2, topic_cell="food_safety",
            strategy="raw_chicken_protocol", pillar="practical",
            question="A cook removes packaging from raw chicken and rinses it under the tap before cooking. The USDA recommends:",
            answer="DO NOT rinse — splashing spreads bacteria across the sink and counter",
            distractors=["Always rinse — washes off bacteria", "Rinse only if storing for later", "Rinse with vinegar first"],
            context="A 2019 USDA study showed rinsing spread bacteria up to 3 feet. Just cook to 165°F.",
        ),
        make_question(
            tier=2, topic_cell="food_safety",
            strategy="cross_contamination", pillar="practical",
            question="Best way to thaw frozen chicken safely?",
            answer="In the refrigerator overnight",
            distractors=["On the counter", "In warm water", "In sunlight"],
            context="Refrigerator (slowest, safest), cold-water bath (change water every 30 min), or microwave (cook immediately after).",
        ),
    ]


def generate_all_safety() -> list[dict]:
    out = []
    out.extend(generate_safe_temps())
    out.extend(generate_danger_zone())
    out.extend(generate_pathogens())
    out.extend(generate_cross_contam())
    return out


if __name__ == "__main__":
    qs = generate_all_safety()
    print(f"Generated {len(qs)} safety questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
