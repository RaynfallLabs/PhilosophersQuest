"""Table etiquette, place settings, formal dining traditions.
"""
from __future__ import annotations

from tools.quizgen.cooking_generators.common import make_question


def generate_table_setting() -> list[dict]:
    return [
        make_question(
            tier=1, topic_cell="etiquette",
            strategy="napkin_in_lap_etiquette", pillar="family_ceremony",
            question="At a formal dinner, where does the napkin go when you sit down?",
            answer="Lap",
            distractors=["Collar tucked in", "Folded beside the plate", "Left in the chair"],
            context="Place the napkin in lap upon being seated. Place it on the chair if leaving the table briefly; on the table when leaving for good.",
        ),
        make_question(
            tier=2, topic_cell="etiquette",
            strategy="table_setting_basics", pillar="family_ceremony",
            question="On a standard place setting, the fork goes on which side of the plate?",
            answer="Left",
            distractors=["Right", "Above the plate", "Below the plate"],
            context="Fork left; knife (blade facing plate) + spoons right; glass upper right; bread plate upper left.",
        ),
        make_question(
            tier=3, topic_cell="etiquette",
            strategy="formal_table_setting_courses", pillar="family_ceremony",
            question="At a multi-course formal dinner, you have multiple forks. Which fork do you use first?",
            answer="The outermost fork",
            distractors=["The innermost fork", "The largest fork", "Either is fine"],
            context="Work from outside in as courses arrive. Salad fork (smaller) outside the dinner fork.",
        ),
        make_question(
            tier=2, topic_cell="etiquette",
            strategy="wait_for_host_etiquette", pillar="family_ceremony",
            question="When food is served at a formal dinner, you should:",
            answer="Wait for the host to begin or invite guests to start",
            distractors=["Start immediately while hot", "Wait until everyone is finished serving", "Ask the host's permission"],
            context="The host's signal is the cue. Exception: if the host insists on serving themselves last, they may say \"please begin.\"",
        ),
        make_question(
            tier=2, topic_cell="etiquette",
            strategy="please_pass_etiquette", pillar="family_ceremony",
            question="Out of reach of the bread basket. Correct action?",
            answer="Ask the nearest person: \"Could you please pass the bread?\"",
            distractors=["Reach across the table", "Lean across your neighbor", "Stand up"],
            context="Bread + condiments + serving dishes travel right (counter-clockwise) traditionally, but \"please pass\" works either way.",
        ),
        make_question(
            tier=3, topic_cell="etiquette",
            strategy="continental_vs_american_fork", pillar="family_ceremony",
            question="The American \"zigzag\" style of using fork and knife:",
            answer="Cut with knife in right hand + fork in left, then switch fork to right hand to eat",
            distractors=["Hold fork only in left hand throughout (never switching)", "Use knife in left hand", "Eat directly with fingers"],
            context="American (zigzag) vs. Continental (fork stays in left, tines down) — both correct. Continental more efficient; American more historically rooted in colonial single-implement use.",
        ),
        make_question(
            tier=3, topic_cell="etiquette",
            strategy="continental_vs_american_fork", pillar="family_ceremony",
            question="The European (Continental) style of using fork and knife:",
            answer="Fork stays in left hand (tines down), knife stays in right; no switching",
            distractors=["Fork switches to right hand to eat (zigzag)", "Fork only — knife as needed", "Knife in left, fork in right"],
            context="Continental style is older + more common globally. American zigzag has a specific 18th-19th c. history.",
        ),
        make_question(
            tier=2, topic_cell="etiquette",
            strategy="table_setting_basics", pillar="family_ceremony",
            question="The bread plate at a standard place setting goes:",
            answer="Upper left of the dinner plate",
            distractors=["Upper right", "Directly above the plate", "Bottom right"],
            context="Bread plate upper LEFT; glasses upper RIGHT. Memory: \"BMW\" — Bread / Meal / Water from left to right.",
        ),
        make_question(
            tier=2, topic_cell="etiquette",
            strategy="table_setting_basics", pillar="family_ceremony",
            question="The water glass at a standard place setting goes:",
            answer="Upper right of the plate (closest to plate); wine glasses to its right",
            distractors=["Upper left", "Directly above the plate", "Bottom right"],
            context="Glasses upper right. Water closest, wine glasses arrayed outward by use.",
        ),
        make_question(
            tier=1, topic_cell="etiquette",
            strategy="napkin_in_lap_etiquette", pillar="family_ceremony",
            question="At the end of a meal, you should place your napkin:",
            answer="Loosely folded to the left of your plate",
            distractors=["Tightly folded into a triangle", "On the dirty plate", "In the empty water glass"],
            context="Loosely folded napkin = \"I'm done.\" Tightly refolded = sometimes considered presumptuous.",
        ),
    ]


def generate_family_meals_basics() -> list[dict]:
    return [
        make_question(
            tier=1, topic_cell="family_meals",
            strategy="birthday_cake_candles", pillar="family_ceremony",
            question="Tradition of singing while presenting a cake with lit candles at:",
            answer="Birthday celebrations",
            distractors=["Weddings", "Christmas", "Easter"],
            context="Birthday cake + candles trace to ancient Greek moon offerings to Artemis; modern form German Kinderfest 18th c.",
        ),
        make_question(
            tier=2, topic_cell="family_meals",
            strategy="sunday_dinner_tradition", pillar="family_ceremony",
            question="In Italian-American + British + Polish-American households, the weekly multi-generational family meal traditionally happens on:",
            answer="Sunday",
            distractors=["Friday", "Saturday", "Wednesday"],
            context="Italian-American Sunday gravy; UK Sunday roast; Polish-American kielbasa Sunday — all converge.",
        ),
        make_question(
            tier=2, topic_cell="family_meals",
            strategy="thanksgiving_history", pillar="family_ceremony",
            question="The American Thanksgiving holiday traces to a 1621 harvest celebration at:",
            answer="Plymouth Colony",
            distractors=["Jamestown", "Boston", "New Amsterdam (NYC)"],
            context="3-day feast between Pilgrims + Wampanoag. Lincoln 1863 made it a national holiday; FDR 1941 fixed the 4th Thursday in November.",
        ),
        make_question(
            tier=2, topic_cell="family_meals",
            strategy="thanksgiving_history", pillar="family_ceremony",
            question="Thanksgiving became a fixed national holiday on the 4th Thursday of November under:",
            answer="Franklin D. Roosevelt (1941)",
            distractors=["George Washington", "Abraham Lincoln", "Theodore Roosevelt"],
            context="Lincoln proclaimed an annual Thanksgiving in 1863; FDR's 1941 act fixed the date.",
        ),
        make_question(
            tier=3, topic_cell="family_meals",
            strategy="breaking_bread_etymology", pillar="family_ceremony",
            question="The English word \"companion\" comes from Latin words meaning:",
            answer="With + bread",
            distractors=["Together + path", "Friend + table", "Equal + share"],
            context="*Com* (with) + *panis* (bread). A companion is literally \"one with whom you share bread.\"",
        ),
        make_question(
            tier=3, topic_cell="family_meals",
            strategy="saying_grace_blessing", pillar="family_ceremony",
            question="The Christian tradition of saying a brief prayer of gratitude before meals is most commonly called:",
            answer="Saying grace (or simply \"grace\")",
            distractors=["Saying the kaddish", "Reciting the Magnificat", "Pronouncing the bracha"],
            context="\"Saying grace\" — common across denominations. Kaddish = Jewish mourner's prayer (unrelated). Bracha = Jewish blessing (related concept, different tradition).",
        ),
    ]


def generate_holiday_basics() -> list[dict]:
    return [
        make_question(
            tier=2, topic_cell="holidays",
            strategy="christmas_dinner_western", pillar="family_ceremony",
            question="Which dish is most associated with the traditional British Christmas dinner?",
            answer="Roast turkey or goose",
            distractors=["Roast lamb", "Glazed ham", "Roast chicken"],
            context="Goose was traditional pre-WWI; turkey took over post-American influence. Followed by Christmas pudding.",
        ),
        make_question(
            tier=2, topic_cell="holidays",
            strategy="easter_lamb_tradition", pillar="family_ceremony",
            question="Lamb as the centerpiece of Easter dinner traces religiously to:",
            answer="The Jewish Passover lamb sacrifice",
            distractors=["Roman spring agriculture", "Anglo-Saxon spring festival", "Norse Ostara goddess"],
            context="Easter coincides with Passover (Pesach) — Christian symbolism of \"Lamb of God\" (Christ).",
        ),
        make_question(
            tier=3, topic_cell="holidays",
            strategy="mardi_gras_carnival_feast", pillar="family_ceremony",
            question="Mardi Gras (\"Fat Tuesday\") falls on the day before:",
            answer="Ash Wednesday — start of Lent",
            distractors=["Easter Sunday", "Christmas Eve", "Good Friday"],
            context="Pre-Lent indulgence — using up rich foods (butter, eggs, meat) before Lenten fasting. New Orleans + Brazilian Carnival famous.",
        ),
        make_question(
            tier=2, topic_cell="holidays",
            strategy="independence_day_4th_july", pillar="family_ceremony",
            question="The food tradition most associated with US Independence Day (4th of July):",
            answer="BBQ — hot dogs, hamburgers, watermelon, apple pie",
            distractors=["Roast turkey", "Lamb stew", "Fish and chips"],
            context="Summer cookout tradition — Coney Island hot-dog eating contest a 4th-of-July institution.",
        ),
        make_question(
            tier=3, topic_cell="holidays",
            strategy="hanukkah_oil_foods", pillar="family_ceremony",
            question="During Hanukkah, latkes (potato pancakes) and sufganiyot (jelly donuts) are eaten because they're:",
            answer="Fried in oil — commemorating the Temple oil miracle",
            distractors=["Round — symbolizing eternity", "Yellow — symbolizing gold", "Cold — symbolizing winter"],
            context="The 8-day oil miracle in the Maccabean Temple is the source. Oil-fried foods commemorate.",
        ),
    ]


def generate_all_etiquette() -> list[dict]:
    out = []
    out.extend(generate_table_setting())
    out.extend(generate_family_meals_basics())
    out.extend(generate_holiday_basics())
    return out


if __name__ == "__main__":
    qs = generate_all_etiquette()
    print(f"Generated {len(qs)} etiquette/family/holiday questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
    print("By tier:", dict(Counter(q["tier"] for q in qs)))
