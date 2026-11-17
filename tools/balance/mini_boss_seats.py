"""
Mini-bosses by lore (Brandon's ruling 13, 2026-11-16): where each named foe
lives, what it drops, and why. Writes data/monsters.json (LORE, NOT FLOOR).

Offline tooling (not loaded at runtime; the data test reads SEATS and DROPS).

    py tools/balance/mini_boss_seats.py            # report: the plan by band
    py tools/balance/mini_boss_seats.py --write    # write the seats and drops
    py tools/balance/mini_boss_bands.py --write    # then health, blows and aim

His words: "We have the main bosses, and then mini-bosses with cool unique
drops are supposed to be spread through the whole game, maybe one or two
every 20 floors; gear they drop should be depth appropriate... why would they
all be concentrated at the end game? Use lore to determine weaker vs later
bosses."

How a seat is chosen
--------------------
Each band of twenty floors is one gate boss's domain (Asterion's Crete,
Medusa's temple, Fafnir's scorched caves, Fenrir's frost, Abaddon's abyss).
A mini-boss sits in the band its legend's might belongs to, and inside it in
lore order: the weaker legend shallower, the mightier one nearer the gate.
The domain decides between two bands where the might is close (the winter
things are Fenrir's; Vulcan's son and the jackal of the red desert are the
scorched caves'; Medusa's sisters come for her killer after her floor). The
reason is written beside each seat. Peaks stay off the gate floors (20, 40,
60, 80, 100) and the seal demons' (83, 85, 87, 89, 91, 93, 97), and off the
last floor before a gate (19, 39, 59, 79), where the common gear found is
already the next band's tier (gear.level_weights): a drop of its band's tier
is never under the commons around it.

What is written for a seated foe
--------------------------------
  * peak_floor (its seat) and min_level (two floors above it);
  * spawn_chance: its weight in its band's slots (level_manager.plan_mini_bosses);
    the legendary ones ride the band slots now, at LEGEND_WEIGHT;
  * treasure.gold: GOLD_LO..GOLD_HI of one floor's income at its seat, as
    every band mini-boss has had (Stheno and Euryale keep their own share);
  * treasure.item_tier and harvest_tier: one above its band, at most 5
    (a named foe is harder to know than its neighbours);
  * treasure.unique_drop_id: its signature drop (DROPS), whose tier is its
    band's (tier = (floor - 1) // 20 + 1).
Health, blows and THAC0 are mini_boss_bands.py's, against the new floor.

Idempotent: a second --write changes nothing.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
MONSTERS_PATH = ROOT / "data" / "monsters.json"

GATES = (20, 40, 60, 80, 100)
SEALS = (83, 85, 87, 89, 91, 93, 97)
GOLD_LO, GOLD_HI = 0.415, 0.77        # of economy.floor_income at the seat
LEGEND_WEIGHT = 0.3                   # a legendary's weight in its band's slots

# id: (seat, why). In band order, shallowest first. The band's tier is the
# tier of its drop.
SEATS: dict[str, tuple[int, str]] = {
    # --- floors 1-20: Asterion's Crete. The weaker legends, and the first
    # trials of the heroes who came before Theseus.
    "bonnacon": (6, "A bull of the bestiaries whose horns cannot hurt anyone; its only weapon is "
                    "burning dung. The weakest legend there is: the game's first named fight."),
    "arachne": (9, "A mortal weaver changed into a spider by Athena: cursed, not mighty."),
    "calydonian_boar": (12, "A boar, if a huge one, sent by Artemis to ravage Calydon. Atalanta's "
                            "arrow drew its blood and Meleager's spear ended it: mortal hunters "
                            "of the generation before Troy (it was floor 27)."),
    "lamia": (15, "A grieving queen turned child-stealing daemon: a terror of nurseries, not of "
                  "armies."),
    "nemean_lion": (17, "The first of Heracles' twelve labours, so before the Lernaean Hydra, his "
                        "second (floor 23): a beast a mortal hero strangled with his arms (it was "
                        "floor 55)."),
    "talos": (18, "Hephaestus' bronze guard who ran around Crete three times a day: met at the "
                  "shore of Minos' island, the last guard before the Labyrinth (it was floor 21)."),
    # --- floors 21-40: Medusa's forgotten temple. Monsters of the heroic age,
    # and the Gorgons' own kin.
    "polyphemus": (27, "Poseidon's son, the shepherd giant of the Odyssey: a man-eater, but beaten "
                       "with wine and a stake by one mortal. A named giant among the cyclopes of "
                       "floors 26-30 (new)."),
    "erlking": (29, "Goethe's elf-king of the night mist: a death spirit who takes a child, not a "
                    "host."),
    "camazotz": (34, "The death bat of Xibalba's House of Bats: a god's creature in a temple of "
                     "the dead."),
    "echidna": (37, "The mother of monsters, Hesiod's kin of the Gorgons, in the deepest part "
                    "of their temple: her brood is met around her (the Hydra 23, the Chimera 31) "
                    "and after her (the Sphinx 44). She was floor 24."),
    # --- floors 41-60: Fafnir's scorched caves. Witches, tricksters and the
    # sons and beasts of gods.
    "iron_patriarch": (42, "A tyrant king sealed in his crypt in his coronation plate, "
                           "still expecting an audience: a barrow-king of the dragon's "
                           "caves, a man, not a monster, the least of their legends (kept "
                           "at 42; on floor 32 his stun-locking hammer killed careful kids "
                           "in the Monte Carlo)."),
    "stheno_gorgon": (42, "Medusa's immortal sisters: when Perseus fled with her head they rose and "
                          "chased him. They come for her killer the floors after hers (they were "
                          "floor 67)."),
    "the_sphinx": (44, "The riddler on the road to Thebes, whom the city could not beat for "
                       "years and Oedipus beat with one answer: a monster of the heroic age, met "
                       "after Echidna, whose brood Hesiod makes her (kept at 44)."),
    "cacus": (47, "Vulcan's fire-breathing son in his smoking cave on the Aventine: the scorched "
                  "caves are his (he was floor 39)."),
    "rangda": (50, "Bali's widow-witch, queen of the leyaks, who fights the Barong forever and "
                   "never loses."),
    "sets_jackal": (53, "The beast of Set, lord of the red desert and of storms: the scorched place "
                        "is his country (it was floor 69)."),
    "baba_yaga": (58, "The iron-toothed witch whose hut walks on chicken legs: older than any "
                      "kingdom, met at the dragon's door."),
    # --- floors 61-80: Fenrir's frost. The winter things, and Loki's brood.
    "whispering_crone": (62, "A fortune-teller buried alive whose dead come at her call."),
    "jormungandr_juvenile": (66, "Fenrir's own brother, the World Serpent, young."),
    "wendigo": (69, "The winter hunger of the northern forests, whose heart is ice: the frost is "
                    "its country (it was floor 85)."),
    "green_knight": (74, "Morgan le Fay's enchanted knight, who keeps his chapel at the turn of the "
                         "year, in the snow."),
    "wild_hunt_captain": (76, "The riders of the winter storm, Wotan's or Herne's: the frost is "
                              "theirs (he was floor 90)."),
    "charybdis": (77, "The whirlpool that swallows the sea three times a day, opposite Scylla "
                      "(74)."),
    "ymir_last_spawn": (78, "A frost giant of the first morning, before the flood of Ymir's blood: "
                            "the mightiest of the frost, met at Fenrir's door (it was floor 85)."),
    # --- floors 81-100: Abaddon's abyss. Demons, primordial things and the
    # end of the world.
    "ravanas_arm": (82, "One arm of Ravana, king of the rakshasas, that did not die with him: a "
                        "demon's remnant, the least of the abyss."),
    "blood_archon": (84, "An older grade of fiend who keeps his ledger in blood."),
    "hrungnirs_ghost": (86, "The strongest of the giants, whom only Thor's hammer broke, walking "
                            "again."),
    "tiamat": (88, "The salt sea of the Enuma Elish, mother of gods and monsters: the abyss "
                   "itself."),
    "surtur": (90, "The fire giant who burns the world at Ragnarok."),
    "anansi": (92, "The spider who bought every story in the world from Nyame, the Sky God himself, "
                   "and paid in full: a trickster of the gods' own rank, among the gods and the "
                   "world's end (kept at 92)."),
    "asmodeus": (94, "A prince of Hell, the last great fiend before the Pit."),
    "nidhoggr_fragment": (96, "The corpse-gnawer at the root of the World Tree, who flies on after "
                              "Ragnarok: the last thing before the end."),
}

# Stheno never goes anywhere without Euryale (her escort, spawn_chance 0).
ESCORTS = {"euryale_gorgon": "stheno_gorgon"}

# id: (signature drop, why). One a foe, dropped on the kill.
DROPS: dict[str, tuple[str, str]] = {
    "bonnacon": ("armor:cloak:hide:elementward:2", "a cloak of its hide, proof against the "
                 "burning of its own dung (an enchanted piece made to that spec)"),
    "arachne": ("arachne_silk_cloak", "her silk, still perfect"),
    "calydonian_boar": ("calydonian_boar_hide", "the hide and tusked head Meleager gave Atalanta"),
    "lamia": ("eyes_of_lamia", "the eyes she took out to sleep (Plutarch: she kept them in a jar)"),
    "nemean_lion": ("hide_of_nemean_lion", "the pelt Heracles wore ever after"),
    "talos": ("bronze_aegis", "the shield of the bronze giant"),
    "the_sphinx": ("sphinx_crown", "her riddle-crown"),
    "polyphemus": ("club_of_polyphemus", "his olive-wood club, the mast-sized staff Odysseus cut "
                   "the stake from"),
    "erlking": ("erlking_mantle", "the Erlking's train ('Kron und Schweif')"),
    "camazotz": ("obsidian_talisman", "a stone of Xibalba's dark"),
    "echidna": ("echidna_fang", "the mother's fang"),
    "iron_patriarch": ("patriarchs_gavel", "the hammer that ends every audience"),
    "stheno_gorgon": ("brazen_hands_of_stheno", "the Gorgons' hands of bronze (Apollodorus)"),
    "cacus": ("vulcans_brand", "his father Vulcan's brand"),
    "rangda": ("rangdas_keris", "her keris, the dagger her spell turns on its own dancers"),
    "sets_jackal": ("anubis_scales", "the scales of the jackal who weighs hearts, its dark "
                    "reflection's prize"),
    "anansi": ("anansi_web_cloak", "the trickster's web"),
    "baba_yaga": ("iron_mortar_wand", "the mortar she flies in"),
    "whispering_crone": ("crones_burial_veil", "the veil she was buried in alive"),
    "jormungandr_juvenile": ("serpent_scale_mail", "the World Serpent's scales"),
    "wendigo": ("wendigo_fang", "its fang of ice"),
    "green_knight": ("green_girdle", "Lady Bertilak's girdle, which Gawain kept"),
    "wild_hunt_captain": ("hunt_captains_sword", "the captain's spectral blade"),
    "charybdis": ("sailors_amulet", "the driftwood of Odysseus' raft"),
    "ymir_last_spawn": ("vambraces_of_the_first_winter", "the ice of the first morning"),
    "ravanas_arm": ("ring_of_iron_grip", "the ring on a king's grip"),
    "blood_archon": ("exsanguinating_blade", "the blade he opens a vein with"),
    "hrungnirs_ghost": ("hrungnirs_stone_shield", "the stone shield he stood on"),
    "tiamat": ("", "her signature is the Scroll of Chromatic Doom, her five breaths"),
    "surtur": ("mantle_of_muspelheim", "the fire-world's mantle"),
    "asmodeus": ("ruby_rod", "the ruby rod that seals each bargain"),
    "nidhoggr_fragment": ("nidhoggr_scale", "one scale of the corpse-gnawer"),
}

# The new named foe: the Cyclops of the Odyssey (Book 9; Homer via Murray's
# translation on Perseus, checked 2026-11-17: the club "a staff of green
# olive-wood ... as large as is the mast of a black ship of twenty oars").
# Health, blows and THAC0 are placeholders mini_boss_bands.py writes.
NEW: dict[str, dict] = {
    "polyphemus": {
        "name": "Polyphemus",
        "symbol": "G",
        "color": [150, 115, 75],
        "hp": "100d10+100",
        "speed": 10,
        "ai_pattern": "aggressive",
        "thac0": 6,
        "spread": 2,
        "peak_weight": 0.0,
        "attacks": [
            {"name": "Olive-Trunk Club", "damage": "4d6+6", "type": "blunt", "delivery": "blow",
             "effect": "stunned", "effect_chance": 0.15, "effect_duration": 1},
            {"name": "Hurled Crag", "damage": "3d6+4", "type": "blunt", "delivery": "ranged",
             "ranged": True},
        ],
        "resistances": ["blunt"],
        "weaknesses": ["pierce"],
        "tags": ["humanoid", "giant"],
        "family": "giants",
        "pronoun": "he",
        "harvest_tier": 3,
        "treasure": {"gold": [0, 0], "item_chance": 1.0, "item_tier": 3, "purse": "kept"},
        "lore": ("Polyphemus, a son of Poseidon, kept his flocks in a cave on the island of the "
                 "Cyclopes and rolled a stone across its mouth that twenty-two wagons could not "
                 "have moved. He shut Odysseus and his men inside and ate them two at a time. "
                 "Odysseus gave him strong wine, told him his name was Nobody, and while he slept "
                 "drove a stake into his one eye, a stake cut from the giant's own club of green "
                 "olive wood, as long as the mast of a ship. Blind, he flung a hilltop after the "
                 "ship. He has his sight back, and he has not forgotten a single face."),
        "frequency": 0,
        "spawn_chance": 0.4,
        "is_mini_boss": True,
        "omen": "Sheep are bleating somewhere on this floor, and the air smells of wet fleece "
                "and new cheese.",
        "kill_chronicle": ("Killed Polyphemus, the Cyclops who ate Odysseus's men two at a time. "
                           "I stayed out from under his club, and nobody had to get him drunk "
                           "first."),
        "thac0_lore": 6,
        "shrugs_off": [],
        "status_immune": [],
        "status_weak": ["confused", "blinded"],
    },
}


# A technique eased for a foe's new, shallower floor, where the hero has less
# to resist it with: {id: {attack name: {field: value}}}, with the reason.
# Measured with the Monte Carlo (kid model, 100 runs a cell, 2026-11-17).
TECHNIQUES: dict[str, dict] = {
    # Odysseus' men were seized and eaten, not clubbed senseless: the club's
    # stun lands less often (it killed a careful kid once in 100 runs at 25%).
    "polyphemus": {"Olive-Trunk Club": {"effect_chance": 0.15}},
}


def band_of(floor: int) -> int:
    return max(1, min(5, (int(floor) - 1) // 20 + 1))


def _gold(floor: int, share: float = 1.0) -> list:
    import economy
    inc = economy.floor_income(floor)
    return [int(round(GOLD_LO * share * inc, -1)), int(round(GOLD_HI * share * inc, -1))]


def apply(monsters: dict) -> list[str]:
    """Write every seat and drop into `monsters`. Returns a log."""
    log = []
    for mid, d in NEW.items():
        if mid not in monsters:
            monsters[mid] = json.loads(json.dumps(d))
            log.append(f"{mid}: new")
    rows = {mid: seat for mid, (seat, _why) in SEATS.items()}
    rows.update({e: SEATS[leader][0] for e, leader in ESCORTS.items()})
    for mid, seat in rows.items():
        d = monsters[mid]
        band = band_of(seat)
        # The lore floor (min_level; its effects' save DC grows with it)
        # stays where it was written when it lies two to ten floors above
        # the seat (Tiamat's 85, Surtur's 80); else two floors above it.
        cur_min = d.get("min_level")
        keep = isinstance(cur_min, int) and seat - 10 <= cur_min <= seat - 2
        want = {
            "peak_floor": seat,
            "min_level": cur_min if keep else seat - 2,
            "harvest_tier": min(5, band + 1),
        }
        if mid in SEATS and "legendary" in (d.get("tags") or []):
            want["spawn_chance"] = LEGEND_WEIGHT
        for k, v in want.items():
            if d.get(k) != v:
                log.append(f"{mid}: {k} {d.get(k)} -> {v}")
                d[k] = v
        tr = d.setdefault("treasure", {})
        moved = {"item_tier": min(5, band + 1)}
        if mid in ("stheno_gorgon", "euryale_gorgon"):
            moved["gold"] = _gold(seat, 0.364 / GOLD_LO)
        elif not set(d.get("tags") or ()) & {"boss"}:
            moved["gold"] = _gold(seat)
        if mid in DROPS and DROPS[mid][0]:
            moved["unique_drop_id"] = DROPS[mid][0]
        for k, v in moved.items():
            if tr.get(k) != v:
                log.append(f"{mid}: treasure.{k} {tr.get(k)} -> {v}")
                tr[k] = v
    for mid, by_name in TECHNIQUES.items():
        for atk in monsters[mid].get("attacks") or []:
            for k, v in (by_name.get(atk.get("name")) or {}).items():
                if atk.get(k) != v:
                    log.append(f"{mid}: {atk['name']}.{k} {atk.get(k)} -> {v}")
                    atk[k] = v
    return log


def report(monsters: dict) -> None:
    import level_manager
    print(f"{'band':5} {'seat':>4}  {'foe':24} {'drop':34} why")
    for lo, hi in ((1, 20), (21, 40), (41, 60), (61, 80), (81, 100)):
        for mid, d, pf in sorted(level_manager.band_candidates(monsters, lo, hi), key=lambda r: r[2]):
            drop = (d.get("treasure") or {}).get("unique_drop_id") or "-"
            print(f"{band_of(pf):5} {pf:4}  {mid:24} {drop:34} {SEATS.get(mid, (0, '?'))[1][:70]}")


def main(argv: list[str]) -> int:
    monsters = json.loads(MONSTERS_PATH.read_text(encoding="utf-8"))
    log = apply(monsters)
    for line in log:
        print("  " + line)
    if "--write" in argv and log:
        MONSTERS_PATH.write_text(json.dumps(monsters, indent=2, ensure_ascii=False) + "\n",
                                 encoding="utf-8", newline="\n")
        print(f"wrote {MONSTERS_PATH}")
    report(monsters)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
