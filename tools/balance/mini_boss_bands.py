"""
Mini-boss bands: every named foe's health, blows and aim, against its floor's
anchors, written into data/monsters.json (LORE, NOT FLOOR).

Offline tooling (not loaded at runtime).

    py tools/balance/mini_boss_bands.py            # report: where each sits
    py tools/balance/mini_boss_bands.py --write    # rewrite HP, dice, THAC0

Why this exists
---------------
Brandon, 2026-11-14: "are our mini-bosses still working and tuned?" They were
placed (every planned one, 331 of 331) but not tuned: after the weapon curve
(2026-11-12) raised hero damage, the mastery hero killed every band
mini-boss, legendary wanderer and seal demon in one to five of his attacks
for 0-15% of his health. Named speed bumps. "Yes, tune them."

The targets (the lead's proposal, approved), measured with the difficulty
simulator: the kid model, each foe fought by the saved heroes of 100 runs at
full health (docs/systems/monsters.md, "Mini-boss tuning"):

    band mini-boss    mastery: about 6-10 attacks, a median 25-50% of his
                      health, deaths at most ~2%; committed: real danger
    legendary         the hardest: 8-12 attacks, 40-60% (see HP_CAP)
    seal demon        a little lighter, since there are seven in a row:
                      5-8 attacks, 20-40%

How a foe is written
--------------------
Each foe in FOES has two numbers against floor_curve's anchors at its peak
floor (the floor it is met on), and may have an aim:

    hp     its health, in ordinary monsters of that floor
           (floor_curve.target_hp: the median HP of what spawns there)
    blows  what it lands in one turn if every blow hits, as a share of a
           steady cook's health bar there (floor_curve.health_bar): the
           attacks Monster.attack fires in a turn (all of them for a flurry,
           the first N for multi_attack_count N, else one at random)
    aim    points off its THAC0 from its lore (see NAMED_NEED); usually 0

The group's band (BANDS) bounds hp and blows, and tests/test_mini_boss_
bands.py checks every foe sits inside it. Where in the band a foe sits was
measured, foe by foe, so that the mastery hero needs about the same number
of attacks for each (the family is the length of the fight): a foe whose
hide or resistances turn his usual blows needs less health to last as long,
and one he cuts through needs more. Danger is preferred to bulk: a foe whose
technique bites (a burn, a web, a riddle, a pull) carries fewer dice.

No turn is a one-blow death: a turn's blows are BLOWS_CAP of a health bar at
most, and the enraged flurry (enraged_multi_attack_count) RAGE_CAP.

To-hit: every foe needs NAMED_NEED or better on the d20 against the hero the
armour line assumes (tools/balance/rebake_thac0.py aims an ordinary monster
at a 10 and calls named_thac0 for these), plus its own aim. A big blow that
rarely lands is luck, and luck is what a careful kid on floor 90 must not
die to; a surer, smaller one is a fight he can read. His armour still
counts: every point of it is a point off the roll.

HP_CAP: no mini-boss is tankier than the final boss (test_high_med_batch_
finishing.test_no_mini_boss_is_tankier_than_abaddon). The mastery hero hits
so hard deep down that the legendary ones and the deepest seal demons
reach the cap before their attack target: they are dangerous rather than
long.

Idempotent: a foe already within 3% of its numbers is left alone, and dice
keep their die size.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
MONSTERS_PATH = ROOT / "data" / "monsters.json"

# (lo, hi): hp in ordinary monsters' health, blows as a share of a health
# bar. Read by the data test.
BANDS = {
    "band": {"hp": (7.0, 24.0), "blows": (0.05, 0.30)},
    "legend": {"hp": (17.0, 24.0), "blows": (0.18, 0.30)},
    "seal": {"hp": (11.0, 19.0), "blows": (0.14, 0.30)},
}
NAMED_NEED = 6          # the d20 roll a named foe needs against the armour line
BLOWS_CAP = 0.30        # a turn's blows, every one landing: at most this of a bar
RAGE_CAP = 0.45         # the enraged flurry, at most
HP_CAP_SHARE = 0.9      # of the final boss's health, at most

# hp: ordinary monsters of its floor; blows: share of a health bar a turn.
# Measured 2026-11-14 (mini_boss_fights.py, 100 kid-model runs a profile):
# the mastery hero needs about six attacks for each; a committed kid about
# twice that, and dies to one in twenty. The note says why each sits where
# it does in its band.
FOES: dict[str, dict] = {
    # --- band mini-bosses, by floor ---------------------------------------
    # Its horns "cannot hurt anyone"; it runs and sprays dung that burns.
    # The game's first named fight (floor 6): the burn and its pace are the
    # danger, so the lightest blows of all and the shortest fight.
    "bonnacon": dict(hp=10.8, blows=0.10),     # (its dice can go no lower: 1d3 and 1d4)
    # Her web slows; her thread is perfect. A slowed hero loses his pace.
    "arachne": dict(hp=14.6, blows=0.18),
    # A weakening, cold embrace: a weakened hero hits half as hard.
    "lamia": dict(hp=12.9, blows=0.18),
    # Bronze: edges and hammers glance off, so little health is needed to
    # last; the nail in his ankle is the way in. Red-hot embrace burns.
    "talos": dict(hp=10.6, blows=0.13),
    # The mother of monsters "never grows old": a deep well of health.
    "echidna": dict(hp=22.7, blows=0.26),
    # Bigger than a bull, bristles like spear shafts: swords glance off.
    # Its gore bleeds, its trample slows, and it charges. Met on floor 12 since
    # 2026-11-17 (mini_boss_seats.py): an early hero has little to mend with,
    # so its blows are lighter (0.24 on floor 27; at 0.24 on floor 12 a
    # careful kid died to it once in 100 runs).
    "calydonian_boar": dict(hp=15.5, blows=0.19),
    # Poseidon's son (2026-11-17): his club stuns and he hurls crags from
    # range; blunt blows are wasted on a giant's hide, the stake's point is
    # not. Wine and a blinding are what beat him, so he falls to both.
    "polyphemus": dict(hp=14.0, blows=0.20),
    # Fey, and cold iron spoils his mood; his lure confuses.
    "erlking": dict(hp=20.9, blows=0.21),
    # The death bat of Xibalba: his wing buffets blind.
    "camazotz": dict(hp=12.8, blows=0.18),
    # Fire and smoke: his breath burns, his smoke blinds, from range. He
    # turns fire and the club, so the fight ran twice the family's length
    # (12 attacks, a median 78-92% of the kids' health, one in ten more than
    # twice it, on 39 and on 47): less health, the same breath (2026-11-17).
    "cacus": dict(hp=12.5, blows=0.17),
    # His warhammer stuns; he grows furious as the fight goes on.
    "iron_patriarch": dict(hp=11.0, blows=0.22),
    # She eats those who cannot answer: rake and bite, and a riddle that
    # crowds the mind (confusion: every sum's numbers swim before they settle).
    "the_sphinx": dict(hp=16.9, blows=0.28),
    # Her hex confuses; she drains.
    "rangda": dict(hp=13.2, blows=0.30),
    # Edges are wasted on its hide; its own claws are the only thing that
    # cuts, and they bleed you. Met on floor 17 since 2026-11-17 (Heracles'
    # first labour): a hero there seldom has a crushing weapon yet and a
    # blade does nothing, so the fight is long; less health and lighter claws
    # keep it a fight he can read (at 14.5 and 0.25 on floor 17 two careful
    # kids died in 115 fights, and one in ten lost twice his health).
    "nemean_lion": dict(hp=10.0, blows=0.16),
    # Iron teeth that bleed, a hex that weakens, and she mends as she
    # fights: little health is needed.
    "baba_yaga": dict(hp=8.6, blows=0.30),
    # She calls the dead to her and whispers fear; her bolt is from range.
    "whispering_crone": dict(hp=14.9, blows=0.16),
    # Venom, and coils that hold a hero still: the hold is the danger.
    "jormungandr_juvenile": dict(hp=11.5, blows=0.19),
    # She rises once from death, and her gaze holds: two fights in one.
    "stheno_gorgon": dict(hp=7.5, blows=0.22),
    # The darkness of Set blinds; the shadow strike drains.
    "sets_jackal": dict(hp=12.2, blows=0.27),
    # The beheading game: he picks up his head (rises once) and mends.
    "green_knight": dict(hp=7.4, blows=0.29),
    # The whirlpool pulls; she fights from a distance.
    "charybdis": dict(hp=14.4, blows=0.16),
    # One of Ravana's twenty arms: its grab holds a hero still.
    "ravanas_arm": dict(hp=16.1, blows=0.14),
    # A blade that bleeds, a charge, a fury that builds.
    "blood_archon": dict(hp=15.5, blows=0.24),
    # Its ice slows, its hunger sickens.
    "wendigo": dict(hp=13.7, blows=0.30),
    # A hunter: he rides and strikes from a distance, his horn stuns, his
    # blade bleeds; the pace is the danger, not the weight of a blow.
    "wild_hunt_captain": dict(hp=12.8, blows=0.10),
    # The trickster's web confuses; his venom lingers.
    "anansi": dict(hp=15.1, blows=0.30),
    # The corpse-gnawer's venom spray; at the cap.
    "nidhoggr_fragment": dict(hp=17.8, blows=0.19),
    # --- the legendary ones (since 2026-11-17 they ride their band's slots:
    # Ymir's Last Spawn in the frost, the other four in the abyss; seats by
    # lore in tools/balance/mini_boss_seats.py). The deep four reach HP_CAP
    # first: dangerous rather than long.
    "hrungnirs_ghost": dict(hp=22.6, blows=0.21),     # stone heart; his whetstone bleeds
    "tiamat": dict(hp=21.1, blows=0.28),              # five breaths, five when enraged
    "ymir_last_spawn": dict(hp=19.9, blows=0.24),     # frost that freezes, a glacier that stuns
    "surtur": dict(hp=18.9, blows=0.30),              # the sword of doom; his aura burns
    "asmodeus": dict(hp=18.2, blows=0.30),            # the ruby rod; his mind blast confuses
    # --- the seven seal demons (floors 83-97, all of them, in a row) -------
    "seal_demon_wrath": dict(hp=17.7, blows=0.25),       # Amon: blazing fists, a fury that builds
    "seal_demon_pestilence": dict(hp=16.0, blows=0.16),  # Buer: plague and miasma, from range
    "seal_demon_famine": dict(hp=15.1, blows=0.30),      # Mammon: a touch armour cannot stop
    "seal_demon_war": dict(hp=11.9, blows=0.30),         # Bael: three blows a turn
    "seal_demon_death": dict(hp=17.0, blows=0.30),       # Samael: his touch feeds him
    "seal_demon_earthquake": dict(hp=15.0, blows=0.25),  # Beleth: the shatter stuns
    "seal_demon_silence": dict(hp=17.4, blows=0.30),     # Abyzou: silence and confusion; at the cap
}

SEAL_DEMONS = ("seal_demon_wrath", "seal_demon_pestilence", "seal_demon_famine",
               "seal_demon_war", "seal_demon_death", "seal_demon_earthquake",
               "seal_demon_silence")

_DICE_RE = re.compile(r"^\s*(\d+)d(\d+)(?:\s*([+-])\s*(\d+))?\s*$")


def dice_avg(d) -> float:
    if isinstance(d, (int, float)):
        return float(d)
    m = _DICE_RE.match(str(d))
    if not m:
        try:
            return float(d)
        except ValueError:
            return 0.0
    n, s = int(m.group(1)), int(m.group(2))
    mod = int(m.group(4)) * (1 if m.group(3) == "+" else -1) if m.group(3) else 0
    return n * (s + 1) / 2 + mod


def group_of(mid: str, d: dict) -> str | None:
    """'band', 'legend' or 'seal' for a foe this tool owns, else None: the
    mini-bosses level_manager rolls (spawn_chance > 0) and the seal demons.
    Gate bosses, the Cow King, Old Nickel and Euryale (Stheno's escort) are
    placed by hand and tuned with their own fights."""
    if mid in SEAL_DEMONS:
        return "seal"
    if not d.get("is_mini_boss") or float(d.get("spawn_chance", 0) or 0) <= 0:
        return None
    return "legend" if "legendary" in (d.get("tags") or []) else "band"


def roster(monsters: dict) -> dict[str, str]:
    """{id: group} of every foe this tool owns."""
    return {mid: g for mid, d in monsters.items() if (g := group_of(mid, d))}


def floor_of(d: dict) -> int:
    return int(d.get("peak_floor") or d.get("min_level") or 1)


def blows(d: dict) -> float:
    """Average damage of one turn's attacks, every blow landing (monster.py
    Monster.attack: the first N of a multi_attack_count under the attack
    count, every attack for a flurry, else one chosen at random)."""
    atks = list(d.get("attacks") or [])
    if not atks:
        return 0.0
    n = int(d.get("multi_attack_count") or 0)
    if 0 < n < len(atks):
        return sum(dice_avg(a.get("damage", 0)) for a in atks[:n])
    if (d.get("multi_attack_always") or n >= len(atks)) and len(atks) > 1:
        return sum(dice_avg(a.get("damage", 0)) for a in atks)
    return sum(dice_avg(a.get("damage", 0)) for a in atks) / len(atks)


def rage_blows(d: dict) -> float:
    """A turn's blows once enraged (enraged_multi_attack_count), else blows()."""
    m = int(d.get("enraged_multi_attack_count") or 0)
    if m <= 0:
        return blows(d)
    return sum(dice_avg(a.get("damage", 0)) for a in (d.get("attacks") or [])[:m])


def where(mid: str, d: dict) -> tuple[float, float]:
    """(hp, blows) of a foe: ordinary monsters' health, share of a bar."""
    import floor_curve
    f = floor_of(d)
    return (dice_avg(d["hp"]) / floor_curve.target_hp(f),
            blows(d) / floor_curve.health_bar(f))


def named_thac0(mid: str, d: dict, line: dict) -> int:
    """THAC0 of a foe this tool owns: it needs NAMED_NEED on the d20 against
    the hero of the armour line (`line`: rebake_thac0.measure_line), plus its
    own aim."""
    f = max(1, min(100, floor_of(d)))
    return int(round(line[f])) + NAMED_NEED + int(FOES.get(mid, {}).get("aim", 0))


def in_band(group: str, hp: float, blows_share: float) -> bool:
    """Inside the group's band, allowing 3% for dice rounding."""
    lo_h, hi_h = BANDS[group]["hp"]
    lo_b, hi_b = BANDS[group]["blows"]
    return (0.97 * lo_h <= hp <= 1.03 * hi_h) and (0.97 * lo_b <= blows_share <= 1.03 * hi_b)


def hp_cap(monsters: dict) -> float:
    return HP_CAP_SHARE * dice_avg(monsters["abaddon_destroyer"]["hp"])


def _scaled(dmg, k: float) -> str:
    return scale_dice(dmg, max(1.0, dice_avg(dmg) * k))


def scale_dice(dmg, target: float) -> str:
    """A dice string averaging about `target`, keeping the die size and the
    share of the average that is dice rather than bonus."""
    m = _DICE_RE.match(str(dmg))
    if not m:
        return str(dmg)
    n, sides = int(m.group(1)), int(m.group(2))
    cur = dice_avg(dmg)
    if cur <= 0:
        return str(dmg)
    n2 = max(1, int(round(n * target / cur)))
    mod = int(round(target - n2 * (sides + 1) / 2))
    while mod < 0 and n2 > 1:
        n2 -= 1
        mod = int(round(target - n2 * (sides + 1) / 2))
    return f"{n2}d{sides}+{mod}" if mod > 0 else f"{n2}d{sides}"


def scale_hp(hp, target: float) -> str:
    """HP dice averaging about `target`, keeping the die size."""
    m = _DICE_RE.match(str(hp))
    if not m:
        return str(int(round(target)))
    n, sides = int(m.group(1)), int(m.group(2))
    n2 = max(1, int(round(n * target / max(1.0, dice_avg(hp)))))
    mod = int(round(target - n2 * (sides + 1) / 2))
    while mod < 0 and n2 > 1:
        n2 -= 1
        mod = int(round(target - n2 * (sides + 1) / 2))
    return f"{n2}d{sides}+{mod}" if mod > 0 else f"{n2}d{sides}"


def apply(monsters: dict, line: dict | None = None) -> list[str]:
    """Write every FOES entry's numbers into `monsters` (and, given the
    armour line, its THAC0). Returns a log; empty when nothing moved."""
    import floor_curve
    log = []
    cap = hp_cap(monsters)
    for mid, want in FOES.items():
        d = monsters[mid]
        f = floor_of(d)
        hp_t = min(cap, want["hp"] * floor_curve.target_hp(f))
        if abs(dice_avg(d["hp"]) / hp_t - 1.0) > 0.03 and scale_hp(d["hp"], hp_t) != d["hp"]:
            old = d["hp"]
            d["hp"] = scale_hp(old, hp_t)
            log.append(f"{mid}: hp {old} ({dice_avg(old):.0f}) -> {d['hp']} ({dice_avg(d['hp']):.0f})")
        bar = floor_curve.health_bar(f)
        cur = blows(d)
        if cur > 0:
            # its share of a bar, unless that would make the enraged flurry
            # more than RAGE_CAP of one
            k = want["blows"] * bar / cur
            k = min(k, RAGE_CAP * bar / max(0.1, rage_blows(d)))
            if abs(k - 1.0) > 0.03:
                new = [_scaled(a["damage"], k) for a in d.get("attacks") or []]
                if new != [a["damage"] for a in d.get("attacks") or []]:
                    for a, dmg in zip(d["attacks"], new):
                        a["damage"] = dmg
                    log.append(f"{mid}: blows {cur:.1f} -> {blows(d):.1f} a turn")
        if line is not None:
            t = named_thac0(mid, d, line)
            if d.get("thac0") != t:
                log.append(f"{mid}: thac0 {d.get('thac0')} -> {t}")
                d["thac0"] = t
    return log


def report(monsters: dict) -> None:
    print(f"{'foe':24} {'group':6} {'floor':>5}  {'HP':>8} {'x HP':>6}  {'blows':>6} {'bar':>5}  thac0")
    for mid, g in sorted(roster(monsters).items(), key=lambda kv: floor_of(monsters[kv[0]])):
        d = monsters[mid]
        h, b = where(mid, d)
        lo_h, hi_h = BANDS[g]["hp"]
        lo_b, hi_b = BANDS[g]["blows"]
        flag = '' if in_band(g, h, b) else '  <- out of band'
        print(f"{mid:24} {g:6} {floor_of(d):5}  {dice_avg(d['hp']):8.0f} {h:6.1f}  "
              f"{blows(d):6.1f} {b:5.0%}  {d.get('thac0')}{flag}")
    print(f"HP cap (the final boss's health x {HP_CAP_SHARE}): {hp_cap(monsters):.0f}")


def main(argv: list[str]) -> int:
    monsters = json.loads(MONSTERS_PATH.read_text(encoding="utf-8"))
    missing = sorted(set(roster(monsters)) - set(FOES))
    if missing:
        print("not in FOES:", missing)
    if "--write" in argv:
        import rebake_thac0
        line = rebake_thac0.measure_line(300, 3, None)
        for entry in apply(monsters, line):
            print("  " + entry)
        MONSTERS_PATH.write_text(json.dumps(monsters, indent=2, ensure_ascii=False) + "\n",
                                 encoding="utf-8", newline="\n")
        print(f"wrote {MONSTERS_PATH}")
    report(monsters)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
