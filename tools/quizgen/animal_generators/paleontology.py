"""Paleontology generators: geologic periods, mass extinctions, key fossils.
"""
from __future__ import annotations

from tools.quizgen.animal_generators.common import (
    make_question,
    pick_length_balanced_distractors,
)


# ----- Mass extinctions -----
MASS_EXTINCTIONS = [
    ("Ordovician-Silurian", "~445M years ago", "~85% marine species lost; glaciation + sea-level drop primary causes."),
    ("Late Devonian", "~372M years ago", "Multiple pulses over ~25M years; ~75% species lost; marine emphasis."),
    ("Permian-Triassic", "~252M years ago", "'The Great Dying' — ~95% marine + ~70% terrestrial species lost. Siberian Traps volcanism."),
    ("Triassic-Jurassic", "~201M years ago", "~80% species lost; opened ecological space for dinosaur radiation."),
    ("K-Pg (Cretaceous-Paleogene)", "~66M years ago", "Chicxulub asteroid + Deccan Traps; non-avian dinosaurs extinct."),
]


def generate_mass_extinctions() -> list[dict]:
    """T3: mass extinction → approximate timing."""
    out = []
    dates = [d for _, d, _ in MASS_EXTINCTIONS]
    for name, date, desc in MASS_EXTINCTIONS:
        distractors = pick_length_balanced_distractors(
            date, [d for d in dates if d != date], k=3
        )
        if distractors is None:
            continue
        out.append(make_question(
            tier=3,
            topic_cell="evolution",
            strategy="mass_extinctions_five",
            pillar="evolution",
            question=f"The {name} mass extinction occurred:",
            answer=date,
            distractors=distractors,
            context=desc,
        ))
    return out


# ----- Geologic periods → key event -----
PERIODS_KEY_EVENTS = [
    ("Cambrian", "Cambrian explosion — most animal phyla appear",
     ["Dinosaur origins", "First land plants", "Mammal radiation"],
     "~540-485M years ago. Burgess Shale fossils discovered 1909 by Walcott."),
    ("Devonian", "Age of Fishes — Tiktaalik transitional tetrapod",
     ["First dinosaurs", "Dinosaur extinction", "Mammal radiation"],
     "~419-359M years ago. Tiktaalik discovered 2004 by Neil Shubin in Ellesmere Island."),
    ("Carboniferous", "Coal-forming forests; giant insects",
     ["First dinosaurs", "Dinosaur extinction", "Cambrian explosion"],
     "~359-299M years ago. Meganeura dragonfly 70cm wingspan due to high O2."),
    ("Permian", "Synapsids dominate; ends in Great Dying",
     ["Dinosaur extinction", "Cambrian explosion", "First mammals"],
     "~299-252M years ago. Dimetrodon was a synapsid (mammal ancestor), NOT a dinosaur."),
    ("Triassic", "First dinosaurs + first mammals appear",
     ["Cambrian explosion", "Dinosaur extinction", "Whale evolution"],
     "~252-201M years ago. Morganucodon (~205M) among earliest mammals."),
    ("Jurassic", "Dinosaur diversity peak; first birds",
     ["First mammals", "Dinosaur extinction", "Cambrian explosion"],
     "~201-145M years ago. Archaeopteryx (~150M Solnhofen) shows bird-dinosaur transition."),
    ("Cretaceous", "T. rex era; ends with asteroid impact",
     ["First mammals", "First dinosaurs", "Cambrian explosion"],
     "~145-66M years ago. K-Pg extinction caused by Chicxulub asteroid."),
    ("Paleogene", "Mammal radiation after dinosaur extinction",
     ["First dinosaurs", "Cambrian explosion", "Human evolution"],
     "~66-23M years ago. Placental mammals diversify rapidly."),
    ("Neogene", "Modern mammal lineages diversify; early hominins",
     ["First dinosaurs", "Cambrian explosion", "Dinosaur extinction"],
     "~23-2.6M years ago. Australopithecus afarensis (Lucy) ~3.2M years ago."),
    ("Pleistocene", "Ice ages + megafauna extinction",
     ["First dinosaurs", "Cambrian explosion", "Dinosaur extinction"],
     "~2.6M-11.7K years ago. Mammoths, sabertooth cats; extinction ~12,000 BP."),
]


def generate_period_key_events() -> list[dict]:
    """T3: geologic period → defining biological event."""
    out = []
    for period, event, distractors, desc in PERIODS_KEY_EVENTS:
        out.append(make_question(
            tier=3,
            topic_cell="evolution",
            strategy="eras_periods_basic",
            pillar="evolution",
            question=f"What major biological event defines the {period} period?",
            answer=event,
            distractors=distractors,
            context=desc,
        ))
    return out


# ----- Famous fossils -----
FAMOUS_FOSSILS = [
    ("Lucy", "Australopithecus afarensis", "1974 Hadar Ethiopia, Donald Johanson; 3.2M years old; named after Beatles song."),
    ("Sue", "Tyrannosaurus rex", "1990 South Dakota, Sue Hendrickson; largest + most complete T. rex; Field Museum Chicago."),
    ("Tiktaalik", "First tetrapod-like fish", "2004 Ellesmere Island, Neil Shubin; predicted location + age."),
    ("Archaeopteryx", "Bird-dinosaur transitional", "1861 Solnhofen Germany; 12 specimens known."),
    ("Burgess Shale fauna", "Cambrian explosion fossils", "1909 Canadian Rockies, Charles Walcott; Anomalocaris, Opabinia."),
    ("Pakicetus", "Earliest whale ancestor", "1981 Pakistan; dog-sized; transitional to modern cetaceans."),
]


def generate_famous_fossils() -> list[dict]:
    """T3-T4: famous fossil → what it is."""
    out = []
    descriptions = [d for _, d, _ in FAMOUS_FOSSILS]
    for name, description, ctx in FAMOUS_FOSSILS:
        distractors = pick_length_balanced_distractors(
            description, [d for d in descriptions if d != description], k=3
        )
        if distractors is None:
            continue
        out.append(make_question(
            tier=3,
            topic_cell="evolution",
            strategy="famous_fossils",
            pillar="evolution",
            question=f"The famous fossil '{name}' is:",
            answer=description,
            distractors=distractors,
            context=ctx,
        ))
    return out


def generate_all_paleontology() -> list[dict]:
    out = []
    out.extend(generate_mass_extinctions())
    out.extend(generate_period_key_events())
    out.extend(generate_famous_fossils())
    return out


if __name__ == "__main__":
    qs = generate_all_paleontology()
    print(f"Generated {len(qs)} paleontology questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
