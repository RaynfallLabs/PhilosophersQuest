"""Domestication dates, founder domesticates, conservation laws.
"""
from __future__ import annotations

from tools.quizgen.animal_generators.common import (
    make_question,
    pick_length_balanced_distractors,
)


# ----- Animal domestication dates -----
DOMESTICATION_DATES = [
    ("Dog", "~15,000-40,000 BP", "First domesticate; from gray wolf; multiple-origin debate."),
    ("Sheep", "~11,000 BP", "Fertile Crescent + Iran; among first agricultural domesticates."),
    ("Goat", "~11,000 BP", "Zagros Mountains; same era as sheep."),
    ("Cattle", "~10,500 BP", "Independent in Near East (taurine), India (zebu), Africa."),
    ("Pig", "~9,000 BP", "Anatolia + East Asia independently from wild boar."),
    ("Cat", "~9,500 BP", "Cyprus burial + ~7,500 BP Egypt; self-domestication theory."),
    ("Horse", "~5,500 BP", "Botai culture Kazakhstan; revolutionized transport + warfare."),
    ("Donkey", "~6,000 BP", "Egypt; pack animal essential for caravan trade."),
    ("Chicken", "~5,500 BP", "Southeast Asia from red junglefowl (Gallus gallus)."),
    ("Llama / Alpaca", "~6,000 BP", "Andes; only large pack animal in pre-Columbian Americas."),
    ("Honeybee", "~6,000 BP", "Egyptian hieroglyphics document early managed hives."),
    ("Reindeer", "~2,000 BP", "Siberian Sami; most recent large-animal domesticate."),
]


def generate_domestication_dates() -> list[dict]:
    """T3: animal → when domesticated."""
    out = []
    dates = [d for _, d, _ in DOMESTICATION_DATES]
    for animal, date, desc in DOMESTICATION_DATES:
        distractors = pick_length_balanced_distractors(
            date, [d for d in dates if d != date], k=3
        )
        if distractors is None:
            continue
        out.append(make_question(
            tier=3,
            topic_cell="husbandry",
            strategy="domesticate_dates_14_main",
            pillar="husbandry",
            question=f"When was the {animal} domesticated?",
            answer=date,
            distractors=distractors,
            context=desc,
        ))
    return out


# ----- Conservation laws -----
CONSERVATION_LAWS = [
    ("Lacey Act", "1900", "First federal US wildlife law; banned trafficking of illegally taken wildlife."),
    ("Migratory Bird Treaty Act", "1918", "Between US and UK (Canada); protected migratory birds across borders."),
    ("Duck Stamp Act", "1934", "Federal Migratory Bird Hunting + Conservation Stamp; funds wetlands."),
    ("Pittman-Robertson Act", "1937", "11% federal excise tax on firearms + ammunition for state wildlife agencies."),
    ("Dingell-Johnson Act", "1950", "Sport Fish Restoration; analog to Pittman-Robertson for fisheries."),
    ("Wilderness Act", "1964", "Protected wilderness designation system; Howard Zahniser primary author."),
    ("Endangered Species Act", "1973", "Nixon-signed; designed to prevent extinction of imperiled species."),
    ("Marine Mammal Protection Act", "1972", "Banned harassment + hunting of all marine mammals in US waters."),
]


def generate_conservation_laws() -> list[dict]:
    """T3-T4: conservation law → year."""
    out = []
    years = [y for _, y, _ in CONSERVATION_LAWS]
    for law, year, desc in CONSERVATION_LAWS:
        distractors = pick_length_balanced_distractors(
            year, [y for y in years if y != year], k=3
        )
        if distractors is None:
            continue
        out.append(make_question(
            tier=3,
            topic_cell="hunting",
            strategy="conservation_laws_dates",
            pillar="hunting",
            question=f"The {law} was enacted in:",
            answer=year,
            distractors=distractors,
            context=desc,
        ))
    return out


# ----- Animal welfare framework dates -----
WELFARE_MILESTONES = [
    ("Martin's Act (UK)", "1822", "First animal cruelty law — Richard Martin 'Humanity Dick' authored."),
    ("RSPCA founded", "1824", "World's first animal welfare charity; royal patronage 1840."),
    ("ASPCA founded", "1866", "Henry Bergh, New York; observed beating of dog → got first US anti-cruelty law."),
    ("Animal Welfare Act (US)", "1966", "Federal regulation of treatment in research + commercial transport."),
    ("Five Freedoms (UK)", "1965", "UK Farm Animal Welfare Council — Brambell Committee."),
    ("Peter Singer Animal Liberation", "1975", "Utilitarian argument; popularized 'speciesism'; modern animal rights philosophy."),
    ("PETA founded", "1980", "Ingrid Newkirk + Alex Pacheco; Silver Spring monkey case."),
    ("Hunting Act (UK)", "2004", "Banned hunting wild mammals with dogs in England + Wales."),
]


def generate_welfare_milestones() -> list[dict]:
    """T3-T4: welfare milestone → year."""
    out = []
    years = [y for _, y, _ in WELFARE_MILESTONES]
    for event, year, desc in WELFARE_MILESTONES:
        distractors = pick_length_balanced_distractors(
            year, [y for y in years if y != year], k=3
        )
        if distractors is None:
            continue
        out.append(make_question(
            tier=3,
            topic_cell="culture",
            strategy="welfare_history_dates",
            pillar="culture",
            question=f"This event occurred in: {event}.",
            answer=year,
            distractors=distractors,
            context=desc,
        ))
    return out


def generate_all_domestication() -> list[dict]:
    out = []
    out.extend(generate_domestication_dates())
    out.extend(generate_conservation_laws())
    out.extend(generate_welfare_milestones())
    return out


if __name__ == "__main__":
    qs = generate_all_domestication()
    print(f"Generated {len(qs)} domestication/conservation questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
