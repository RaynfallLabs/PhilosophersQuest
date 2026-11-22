"""Draft each part's strength and side gift from its creature's own data.

Kitchen variety, 2026-11-22 (Brandon: "many do EXACTLY the same thing, with
different art and ingredients"). Writes the content file the builder reads:

    py tools/content/kitchen/draft_lore.py <out.txt>
    (review it, then copy it over tools/content/kitchen/ingredient_lore.txt)
    py tools/content/kitchen/build_kitchen.py --lore

Strength (``richness``): the creature's hit points against its tier's typical
creature (the geometric mean of its tier's parts), squashed smoothly into
0.75-1.35 so that a creature never ties with a smaller one: a cave bear is
richer than a rat, a titan than an imp. Named and mini-boss creatures a little
more. Three decimals.

Side gift: the element it strikes with (fire, cold, lightning, acid, drain),
else an arcane part's mana, else its family's gift by lore, else a little
healing. Never poison resistance or the body's save (the effects branch tunes
those). A side that is the part's own power becomes healing instead.

``HAND`` holds the corrections made on review.
"""
import json
import math
import os
import re
import statistics
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
ELEMENT = {'fire': 'fire_resist', 'cold': 'cold_resist', 'lightning': 'shock_resist',
           'shock': 'shock_resist', 'acid': 'acid_resist', 'drain': 'drain_resist',
           'necrotic': 'drain_resist'}
FAMILY = {'demons': 'fire_resist', 'restless_dead': 'fear_immune', 'ghosts': 'see_invisible',
          'goblinkin': 'dark_vision', 'fair_folk': 'sleep_resist', 'vermin': 'searching',
          'giants': 'heal', 'serpents': 'warning', 'aberrations': 'save_guard_WIS', 'legend': 'heal',
          'vampires_liches': 'drain_resist', 'dragons': 'fire_resist', 'great_beasts': 'heal',
          'constructs': 'save_guard_DEX', 'elementals': 'heal', 'plants': 'regenerating',
          'oozes': 'acid_resist', 'birds': 'warning', 'shapeshifters': 'see_invisible',
          'gorgons': 'save_guard_DEX', 'celestials': 'save_guard_WIS', 'mortals': 'heal'}
FORAGE = {'abyssal_kelp': 'heal', 'altar_incense': 'save_guard_WIS', 'cave_mushroom': 'dark_vision',
          'crystal_shard': 'mp', 'deep_iron': 'fire_resist', 'holy_water': 'drain_resist',
          'river_salt': 'fear_immune', 'starnut': 'mp', 'sunroot': 'heal', 'swamp_moss': 'regenerating'}
# On review: (richness or None, side or None, why).
HAND = {
    'troll_prime': (1.10, 'regenerating', 'a troll regrows what is cut from it'),
    'chaos_troll_prime': (None, 'regenerating', 'a troll regrows what is cut from it'),
    'ice_troll_prime': (None, 'regenerating', 'a troll regrows what is cut from it'),
    'titan_prime': (1.20, None, 'the elder gods of the Golden Age'),
    'corrupted_angel_prime': (0.95, None, 'one of the host, fallen'),
    'arch_demon_prime': (0.85, None, 'a lord of the Pit'),
    'fenrir_pup_prime': (1.15, None, 'the wolf that will swallow the sun, young'),
    'cerberus_prime': (1.10, None, 'the hound of the underworld'),
    # Creatures that would otherwise give the same thing as a neighbour.
    'lamia_prime': (None, 'see_invisible', 'the lamia could take out her eyes and still see'),
    'carbuncle_prime': (None, 'dark_vision', 'the jewel on its brow shines in the dark'),
    'imp_prime': (None, 'fire_resist', 'an imp of the brimstone pits'),
    'poltergeist_prime': (None, 'see_invisible', 'the unseen hand that throws the crockery'),
    'earth_elemental_prime': (None, 'shock_resist', 'the earth grounds the lightning'),
    'rot_grub_swarm_prime': (None, 'regenerating', 'surgeons set maggots to clean a wound'),
    'myconid_worker_prime': (None, 'save_guard_WIS', 'the myconids share one mind through their spores'),
    'ravanas_arm_prime': (None, 'mp', 'Ravana, the ten-headed scholar-king, master of the Vedas'),
    'shadow_prime': (None, 'dark_vision', 'a shadow is at home in the dark'),
}
LOW, HIGH = 0.75, 1.35


def avg(d):
    m = re.fullmatch(r'(\d+)d(\d+)([+-]\d+)?', str(d).replace(' ', ''))
    if not m:
        try:
            return float(d)
        except ValueError:
            return 10.0
    n, s, b = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    return n * (s + 1) / 2 + b


def band(f):
    return max(1, min(5, (int(f) - 1) // 20 + 1))


def squash(x: float) -> float:
    """x (1.0 a typical creature) into LOW..HIGH smoothly, keeping order."""
    d = math.log(max(1e-6, x))
    room = (HIGH - 1.0) if d > 0 else (1.0 - LOW)
    return 1.0 + room * math.tanh(0.3 * d / room)


def draft():
    ings = json.load(open(os.path.join(ROOT, 'data', 'items', 'ingredient.json'), encoding='utf-8'))
    mons = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    hp = {k: avg(mons.get(v.get('source_monster', ''), {}).get('hp', 10))
          for k, v in ings.items() if v['tier_role'] == 'prime'}
    typical = {t: statistics.geometric_mean([hp[k] for k in hp if band(ings[k]['min_level']) == t])
               for t in range(1, 6)}
    rows = []
    for k, v in ings.items():
        if v['tier_role'] == 'dungeon':
            rows.append((k, 1.0, FORAGE[k], 'foraged find'))
            continue
        if v['tier_role'] != 'prime':
            continue
        m = mons.get(v.get('source_monster', ''), {})
        t = band(v['min_level'])
        named = bool(m.get('is_mini_boss') or m.get('is_boss') or m.get('proper_noun'))
        r = min(HIGH, squash(hp[k] / typical[t]) + (0.04 if named else 0.0))
        side, why = None, ''
        for a in m.get('attacks', []):
            e = ELEMENT.get(str(a.get('type', '')).lower())
            if e:
                side, why = e, f"strikes with {a.get('type')}"
                break
        if not side and v.get('nature') == 'mp':
            side, why = 'mp', 'an arcane part'
        if not side:
            side, why = FAMILY.get(m.get('family', ''), 'heal'), m.get('family', '?')
        if side == v.get('temp_power'):
            side, why = 'heal', why + ' (its own power is its dish)'
        why = (f"{m.get('name', k)}, {round(hp[k])} HP against a typical {round(typical[t])} "
               f"in tier {t}; {why}")
        if k in HAND:
            hr, hs, hw = HAND[k]
            r = hr if hr is not None else r
            side = hs or side
            why += f'; by hand: {hw}'
        rows.append((k, round(r, 3), side, why))
    return rows, ings


def main():
    rows, ings = draft()
    with open(sys.argv[1], 'w', encoding='utf-8', newline='\n') as f:
        f.write("# Each part's strength and side gift (kitchen variety, 2026-11-22). Drafted from its\n"
                "# creature's own data by draft_lore.py (hit points against its tier's typical creature,\n"
                "# squashed into 0.75-1.35; its element, else an arcane part's mana, else its family's\n"
                "# gift), then reviewed by hand (draft_lore.HAND).\n"
                "# key | richness | side | why\n")
        for k, r, s, why in rows:
            f.write(f'{k}|{r:.3f}|{s}|{why}\n')
    for t in range(1, 6):
        rs = [r for k, r, s, w in rows if ings[k]['tier_role'] == 'prime' and band(ings[k]['min_level']) == t]
        print('tier', t, 'parts', len(rs), 'mean', round(sum(rs) / len(rs), 3), 'min', min(rs), 'max', max(rs))


if __name__ == '__main__':
    main()
