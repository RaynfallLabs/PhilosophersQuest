"""Recipe ratios + scaling: vinaigrette, rice, pasta water, bread, conversions.
"""
from __future__ import annotations

from tools.quizgen.cooking_generators.common import make_question


# ----- Classic ratios -----
def generate_classic_ratios() -> list[dict]:
    return [
        make_question(
            tier=2, topic_cell="ratios",
            strategy="vinaigrette_ratio", pillar="practical",
            question="Classic vinaigrette ratio: parts oil to parts vinegar?",
            answer="3:1",
            distractors=["1:1", "1:3", "5:1"],
            context="3 parts oil + 1 part acid + mustard + salt — emulsify. Mediterranean origin.",
        ),
        make_question(
            tier=1, topic_cell="ratios",
            strategy="rice_water_ratio", pillar="practical",
            question="Long-grain white rice: parts water to parts rice (stovetop)?",
            answer="2:1",
            distractors=["1:1", "3:1", "4:1"],
            context="Short-grain rice uses ~1.25:1 (less water). Brown rice ~2.5:1 (more, longer cook).",
        ),
        make_question(
            tier=2, topic_cell="ratios",
            strategy="pasta_water_salt", pillar="practical",
            question="Pasta water salt: the chef's traditional standard is \"salty like the ___\"?",
            answer="Sea",
            distractors=["Pinch of salt per gallon", "Heavy stew", "Soup broth"],
            context="About 1-2 tablespoons salt per gallon — seasons the pasta from within and binds with starch in finishing sauces.",
        ),
        make_question(
            tier=3, topic_cell="ratios",
            strategy="bread_ratio_basics", pillar="practical",
            question="Baker's percentage for a basic lean bread dough — water content typically:",
            answer="60-70% of flour weight (hydration)",
            distractors=["10-20% of flour weight", "100% of flour weight", "Equal volumes flour and water"],
            context="Baker's % expresses everything relative to flour weight. 60% = stiff dough, 75% = soft, 85%+ = ciabatta/focaccia.",
        ),
        make_question(
            tier=2, topic_cell="ratios",
            strategy="vinaigrette_ratio", pillar="practical",
            question="A chef has 6 tablespoons of olive oil and wants the classic vinaigrette ratio. How much vinegar does she add?",
            answer="2 tablespoons",
            distractors=["6 tablespoons", "12 tablespoons", "1 teaspoon"],
            context="3:1 oil:vinegar — divide oil by 3.",
        ),
        make_question(
            tier=2, topic_cell="ratios",
            strategy="rice_water_ratio", pillar="practical",
            question="A chef cooks 1.5 cups of long-grain rice. How much water?",
            answer="3 cups",
            distractors=["1.5 cups", "2 cups", "4.5 cups"],
            context="2:1 water-to-rice for long-grain.",
        ),
    ]


# ----- Conversion -----
def generate_conversions() -> list[dict]:
    return [
        make_question(
            tier=1, topic_cell="conversions",
            strategy="recipe_double_halve", pillar="practical",
            question="1 tablespoon = how many teaspoons?",
            answer="3",
            distractors=["2", "4", "6"],
            context="Standard US measurement — memorize the small ones.",
        ),
        make_question(
            tier=1, topic_cell="conversions",
            strategy="recipe_double_halve", pillar="practical",
            question="1 cup = how many tablespoons?",
            answer="16",
            distractors=["8", "12", "32"],
            context="16 tablespoons = 1 cup; 4 tablespoons = 1/4 cup.",
        ),
        make_question(
            tier=2, topic_cell="conversions",
            strategy="recipe_double_halve", pillar="practical",
            question="1 cup = how many fluid ounces?",
            answer="8 fl oz",
            distractors=["4 fl oz", "16 fl oz", "32 fl oz"],
            context="1 cup = 8 fl oz; 2 cups = 1 pint = 16 fl oz.",
        ),
        make_question(
            tier=2, topic_cell="conversions",
            strategy="recipe_double_halve", pillar="practical",
            question="1 pint = how many cups?",
            answer="2",
            distractors=["1", "4", "8"],
            context="2 cups = 1 pint; 2 pints = 1 quart; 4 quarts = 1 gallon.",
        ),
        make_question(
            tier=2, topic_cell="conversions",
            strategy="recipe_double_halve", pillar="practical",
            question="1 stick of butter (US) = how many tablespoons?",
            answer="8",
            distractors=["4", "12", "16"],
            context="1 stick = 1/2 cup = 8 tablespoons = 1/4 pound = 113g.",
        ),
        make_question(
            tier=2, topic_cell="conversions",
            strategy="recipe_double_halve", pillar="practical",
            question="A recipe calls for 1/4 cup of butter. How many tablespoons?",
            answer="4",
            distractors=["2", "8", "16"],
            context="1/4 cup = 4 tablespoons. (1 stick = 8 tbsp = 1/2 cup.)",
        ),
        make_question(
            tier=2, topic_cell="conversions",
            strategy="recipe_double_halve", pillar="practical",
            question="A recipe for 4 servings needs 3 cups of flour. To make 6 servings, how much flour?",
            answer="4.5 cups",
            distractors=["6 cups", "3 cups", "9 cups"],
            context="6/4 = 1.5x. 3 × 1.5 = 4.5.",
        ),
        make_question(
            tier=2, topic_cell="conversions",
            strategy="recipe_double_halve", pillar="practical",
            question="To halve a recipe that calls for 3 eggs:",
            answer="Use 1 egg + 1 yolk (or 1 egg + 1 tablespoon water as estimate)",
            distractors=["Use 1.5 eggs", "Use 2 eggs", "Use 1 egg, less of other ingredients"],
            context="Eggs don't halve cleanly — beat egg and use half by weight, or substitute.",
        ),
        make_question(
            tier=3, topic_cell="conversions",
            strategy="recipe_scaling_thirds", pillar="practical",
            question="A bread recipe says 500g flour. You only have 333g. What proportion can you make?",
            answer="2/3 of the recipe",
            distractors=["1/2 of the recipe", "3/4 of the recipe", "Same recipe — just adjust water"],
            context="333/500 ≈ 0.67 = 2/3. Scale all other ingredients by 0.67.",
        ),
    ]


# ----- Doneness check ratios + cues -----
def generate_doneness_cues() -> list[dict]:
    return [
        make_question(
            tier=2, topic_cell="doneness",
            strategy="doneness_pasta_al_dente", pillar="practical",
            question="Pasta cooked \"al dente\" means:",
            answer="Firm to the bite — a tiny white core just disappearing",
            distractors=["Falling-apart soft", "Crunchy in the middle", "Completely white core remaining"],
            context="\"To the tooth\" — Italian standard, slightly undercooked vs. American taste.",
        ),
        make_question(
            tier=2, topic_cell="doneness",
            strategy="visual_doneness_bread", pillar="practical",
            question="A baker checks if bread is done by tapping the bottom. What sound indicates fully baked?",
            answer="Hollow",
            distractors=["Dull thud", "High-pitched ping", "Crackling pop"],
            context="Hollow sound = steam escaped + interior set. Combine with golden-brown crust + 200°F+ internal temp.",
        ),
        make_question(
            tier=2, topic_cell="doneness",
            strategy="doneness_eggs", pillar="practical",
            question="An egg with set whites + runny yolk is called:",
            answer="Soft-boiled (or sunny-side-up / over-easy depending on cooking method)",
            distractors=["Hard-boiled", "Scrambled", "Poached firm"],
            context="Soft-boiled in shell ~6 min boil. Sunny-side: yolk faces up, whites set. Over-easy: flipped briefly, yolk still runny.",
        ),
    ]


def generate_all_ratios() -> list[dict]:
    out = []
    out.extend(generate_classic_ratios())
    out.extend(generate_conversions())
    out.extend(generate_doneness_cues())
    return out


if __name__ == "__main__":
    qs = generate_all_ratios()
    print(f"Generated {len(qs)} ratio/conversion/doneness questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
