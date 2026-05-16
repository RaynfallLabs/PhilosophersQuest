"""
Generator G — regenerate every monster's numerical content against the unified
balance curve. Reads `data/monsters.json`, preserves all flavor/design fields
(name, symbol, color, ai_pattern, attacks structure, tags, harvest, lore,
special abilities), and rewrites HP/THAC0/damage/spawn fields per
`tools/balance/curve.py`.

Output: `tools/balance/generated/data/monsters.json`.

Approach:
- spawn_peak_floor: derived from existing min_level (the "rough center" per the
  brief). For monsters with a max_level, we use the midpoint between min_level
  and max_level (clamped) — that's the natural bell-curve center the design
  already implied. Bosses use their fixed boss floor.
- spread: chosen from band width and "niche-ness" heuristic. Boss/mini-boss/
  seal demons get narrow spreads (1-3). Normal monsters: 8-12 typical, 14-20
  for "anywhere from early-mid" generalists.
- peak_weight: derived from existing `frequency` if present (1-10) — falls
  back to 5 for monsters without it. Bosses: 0 (forced spawn only).
- HP: dice string that AVERAGES close to the curve at the peak floor. Elite
  (tough) monsters tagged via heuristic (boss, mini-boss, "ancient", "elder",
  "lord", "king", "dragon", "titan", "primordial", "wyrm", "elemental", legs
  with original HP ≥ 1.4× the median at their floor).
- THAC0: med per floor; elites get -4.
- Attack damage: each attack's dice averages ~ monster_damage_med(peak_floor)
  for normal monsters. Tough monsters get ONE signature attack at
  monster_damage_tough; the rest median. Preserves attack name, type,
  effect, piercing.
- Special abilities preserved verbatim: can_phase_walls, dragon_scales,
  gaze_paralyze, gaze_cooldown, regen, regeneration, rage_*, sp_drain,
  locust_*, is_allied, is_boss, is_mini_boss, is_seal_demon, spawn_chance,
  attack_effects, base_resistances, pack.

Then we append 6 new "Abaddon's Lieutenant" species at peak_floor 91-99 to
fill the L91-99 variety gap flagged in the audit.
"""

from __future__ import annotations
import json
import math
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from curve import (
    monster_hp_med, monster_hp_tough,
    monster_damage_med, monster_damage_tough,
    monster_thac0_med, monster_thac0_elite,
    boss_hp_naive,
    TOTAL_FLOORS,
)


# ---------------------------------------------------------------------------
# Dice math helpers
# ---------------------------------------------------------------------------

def dice_avg(notation: str) -> float:
    """Average value of a dice expression like '3d8+12' or '15'."""
    if isinstance(notation, (int, float)):
        return float(notation)
    notation = str(notation).strip()
    if not notation:
        return 0.0
    # Pure integer
    if notation.isdigit() or (notation.startswith('-') and notation[1:].isdigit()):
        return float(notation)
    # Match NdM[+/-K]
    m = re.fullmatch(r'(\d+)d(\d+)([+-]\d+)?', notation)
    if m:
        n, d, mod = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        return n * (d + 1) / 2 + mod
    # Fallback
    try:
        return float(notation)
    except ValueError:
        return 0.0


def build_hp_dice(target_avg: int) -> str:
    """Build a dice string whose average is close to target_avg.
    Aim for moderate variance — pick a die size proportional to target.
    """
    target = max(1, int(round(target_avg)))
    if target <= 4:
        # 1d4..1d6 range
        if target <= 2:
            return "1d3"
        if target <= 4:
            return f"1d{2*target}"
        return f"1d{2*target}"
    if target <= 8:
        # NdM expressions: 2d4=5, 2d6=7, 2d8=9, 3d4=7.5, 3d6=10.5
        # Choose by closeness
        candidates = ["1d6+2", "2d4", "1d8+2", "2d6", "1d10+2", "2d8", "3d4"]
        return _closest(candidates, target)
    if target <= 20:
        # Use a base die d6 or d8 + flat modifier
        n = max(2, target // 4)
        d = 8
        base = n * (d + 1) / 2
        mod = int(round(target - base))
        if mod < 0:
            return f"{n}d{d}{mod}"
        if mod == 0:
            return f"{n}d{d}"
        return f"{n}d{d}+{mod}"
    if target <= 60:
        # Use d8 + flat
        n = max(3, target // 5)
        d = 8
        base = n * (d + 1) / 2
        mod = int(round(target - base))
        if mod < 0:
            return f"{n}d{d}{mod}"
        if mod == 0:
            return f"{n}d{d}"
        return f"{n}d{d}+{mod}"
    if target <= 200:
        # Use d10 + flat
        n = max(5, target // 8)
        d = 10
        base = n * (d + 1) / 2
        mod = int(round(target - base))
        if mod < 0:
            return f"{n}d{d}{mod}"
        if mod == 0:
            return f"{n}d{d}"
        return f"{n}d{d}+{mod}"
    # Big numbers (bosses)
    n = max(10, target // 12)
    d = 12
    base = n * (d + 1) / 2
    mod = int(round(target - base))
    if mod < 0:
        return f"{n}d{d}{mod}"
    if mod == 0:
        return f"{n}d{d}"
    return f"{n}d{d}+{mod}"


def _closest(candidates, target):
    best = min(candidates, key=lambda s: abs(dice_avg(s) - target))
    return best


def build_damage_dice(target_avg: int) -> str:
    """Build damage dice averaging close to target. Smaller targets get d4-d6;
    larger get d8-d10. Aim for AD&D feel."""
    target = max(1, int(round(target_avg)))
    if target <= 1:
        return "1d2"
    if target == 2:
        return "1d3"
    if target == 3:
        return "1d4+1"  # avg 3.5
    if target == 4:
        return "1d6+1"  # avg 4.5
    if target == 5:
        return "1d8+1"  # avg 5.5
    if target == 6:
        return "2d4+1"  # avg 6
    if target == 7:
        return "2d6"    # avg 7
    if target == 8:
        return "1d8+4"  # avg 8.5
    if target == 9:
        return "2d6+2"  # avg 9
    if target == 10:
        return "2d8+1"  # avg 10
    if target <= 12:
        return f"2d8+{target-9}"  # 9..14 range
    if target <= 16:
        return f"3d6+{target-10}" if target-10 >= 0 else f"3d6"  # 10.5 base
    if target <= 22:
        return f"3d8+{target-13}" if target-13 >= 0 else "3d8"  # 13.5 base
    # >22 (rare, mostly bosses): 4d8+mod or 4d10+mod
    base = 4 * 5.5  # 4d10 avg = 22
    n = 4
    d = 10
    mod = target - int(round(base))
    if mod < 0:
        return f"{n}d{d}{mod}"
    if mod == 0:
        return f"{n}d{d}"
    return f"{n}d{d}+{mod}"


# ---------------------------------------------------------------------------
# Curve helpers
# ---------------------------------------------------------------------------

def clamp_floor(f: int) -> int:
    return max(1, min(TOTAL_FLOORS, int(f)))


def derive_peak_floor(mon: dict) -> int:
    """Pick peak_floor as midpoint of (min_level, max_level) if both set, else
    min_level + 4 (since old data tended to spawn min_level..min_level+15).
    Clamped 1..100.
    """
    mn = int(mon.get('min_level', 1))
    mx = mon.get('max_level')
    if mx is not None:
        return clamp_floor((mn + int(mx)) // 2)
    return clamp_floor(mn + 4)


def derive_spread(mon: dict, peak: int) -> int:
    """Pick a spread (std-dev for spawn bell curve).
    - Bosses / mini-bosses / seal demons / forced single-floor: 1-3 (very narrow)
    - Floor-locked entries (min==max): 2
    - Niche/themed (locusts, allies): 2
    - Normal monsters: derive from min/max gap, default 10
    """
    if mon.get('is_boss') or mon.get('is_mini_boss') or mon.get('is_seal_demon'):
        return 2
    if mon.get('frequency') == 0:
        # Forced-spawn-only entries (canonical bosses without is_boss flag)
        return 2
    if mon.get('is_allied'):
        return 2
    mn = int(mon.get('min_level', 1))
    mx = mon.get('max_level')
    if mx is not None and int(mx) == mn:
        return 2
    if mx is not None:
        gap = int(mx) - mn
        if gap <= 0:
            return 4
        # spread = half-band ≈ gap/2 (bell std-dev tighter than full range)
        return max(4, min(20, gap // 2 + 3))
    # Open-ended (no max): broad
    return 12


def derive_peak_weight(mon: dict) -> float:
    """Derive peak_weight from existing frequency (1-10 typical).
    Bosses / mini-bosses / seal demons get 0 (handled by forced spawn code).
    """
    if mon.get('is_boss') or mon.get('is_mini_boss') or mon.get('is_seal_demon'):
        return 0.0
    if mon.get('is_allied'):
        return 0.0  # only summoned, not random spawn
    freq = mon.get('frequency')
    if freq is None:
        return 5.0
    return float(freq) if freq > 0 else 0.0


# ---------------------------------------------------------------------------
# Elite / tough heuristic
# ---------------------------------------------------------------------------

ELITE_NAME_PATTERNS = [
    'ancient', 'elder', 'lord', 'king', 'queen', 'arch', 'primordial', 'titan',
    'colossus', 'emperor', 'champion', 'lich', 'wyrm', 'dragon', 'demon prince',
    'greater', 'overlord', 'master', 'high ', 'royal', 'dread', 'infernal',
    'celestial', 'cosmic', 'world', 'destroyer', 'wraith', 'fafnir', 'fenrir',
    'asterion', 'medusa', 'abaddon', 'jormungandr', 'nidhoggr', 'tiamat',
    'leviathan', 'behemoth', 'sphinx', 'kraken', 'hydra', 'baba_yaga', 'wendigo',
    'echidna', 'green knight', 'wild_hunt',
]

ELITE_TAGS = {'dragon', 'celestial'}


def is_elite(mon: dict, peak: int, hp_avg: float) -> bool:
    """Heuristic: is this monster 'tough' (75th-percentile HP/damage)?"""
    name = mon.get('name', '').lower()
    for pat in ELITE_NAME_PATTERNS:
        if pat in name:
            return True
    tags = set(mon.get('tags') or [])
    if tags & ELITE_TAGS:
        return True
    # If the original HP was already heavy relative to its floor — call it elite
    med = monster_hp_med(peak)
    if hp_avg >= med * 1.35:
        return True
    return False


# ---------------------------------------------------------------------------
# Boss / seal demon / special handling
# ---------------------------------------------------------------------------

BOSS_IDS = {
    'asterion_minotaur': 20,
    'medusa_gorgon':     40,
    'fafnir_dragon':     60,
    'fenrir_wolf':       80,
    'abaddon_destroyer': 100,
}

# Seal demons get their existing fixed floors; we use monster_hp_tough(floor)
SEAL_IDS = {
    'seal_demon_wrath':      83,
    'seal_demon_pestilence': 85,
    'seal_demon_famine':     87,
    'seal_demon_war':        89,
    'seal_demon_death':      91,
    'seal_demon_earthquake': 93,
    'seal_demon_silence':    97,
}


def regenerate_attacks(attacks, peak_floor, is_tough):
    """Rebalance attack damage to fit curve. Preserves all non-damage fields."""
    med = monster_damage_med(peak_floor)
    tough = monster_damage_tough(peak_floor)
    out = []
    # If multiple attacks and monster is tough, ONE signature attack at tough,
    # others at median. Pick the first attack as the signature.
    for i, atk in enumerate(attacks):
        new_atk = dict(atk)  # preserves name, type, effect, piercing, etc.
        if is_tough and i == 0:
            target = tough
        else:
            target = med
        new_atk['damage'] = build_damage_dice(target)
        out.append(new_atk)
    return out


def regenerate_monster(mid: str, mon: dict) -> dict:
    """Build a regenerated monster entry preserving all flavor/design fields."""
    # ------- Detect category --------
    is_boss_main = mid in BOSS_IDS
    is_seal = mid in SEAL_IDS
    is_cow_king = mid == 'cow_king'
    is_locust = mid == 'abyssal_locust'
    is_angel = mid == 'heavenly_angel'

    # ------- Pick spawn center --------
    if is_boss_main:
        peak = BOSS_IDS[mid]
    elif is_seal:
        peak = SEAL_IDS[mid]
    elif is_cow_king:
        peak = 35  # midpoint of L30-39 random range
    elif is_locust or is_angel:
        peak = 100
    else:
        peak = derive_peak_floor(mon)

    # ------- HP --------
    if is_boss_main:
        target_hp = boss_hp_naive(peak)
    elif is_seal:
        target_hp = monster_hp_tough(peak)
    elif is_cow_king:
        # mini-boss: ~6x median (per brief)
        target_hp = monster_hp_med(peak) * 6
    elif is_locust:
        # Swarm chaff — much lower than the floor median (one-shot fodder)
        target_hp = max(3, monster_hp_med(peak) // 12)  # ~14 HP at L100
    elif is_angel:
        target_hp = 4  # angel-counter is glass cannon (preserved value)
    else:
        # Normal vs tough
        # Pre-pass: estimate target with med first
        original_avg = dice_avg(mon.get('hp', 0))
        elite = is_elite(mon, peak, original_avg)
        target_hp = monster_hp_tough(peak) if elite else monster_hp_med(peak)
        # Re-flag elite so attacks honor it
        mon['_elite'] = elite

    hp_str = build_hp_dice(target_hp)

    # ------- THAC0 --------
    if is_boss_main:
        # Bosses go a few points better than elite
        thac0 = monster_thac0_elite(peak) - 2  # 6 better than median total
    elif is_seal:
        thac0 = monster_thac0_elite(peak)
    elif is_cow_king:
        thac0 = monster_thac0_elite(peak)
    elif is_locust or is_angel:
        # Preserve their special tuning (these are scripted-spawn fodder)
        thac0 = monster_thac0_med(peak)
    else:
        elite = mon.get('_elite', False)
        thac0 = monster_thac0_elite(peak) if elite else monster_thac0_med(peak)

    # ------- Attacks --------
    if is_boss_main:
        # bosses: signature attack at tough+30%; others at tough
        attacks = []
        med = monster_damage_med(peak)
        tough = monster_damage_tough(peak)
        signature_dmg = int(round(tough * 1.3))  # boss-tier signature
        for i, atk in enumerate(mon.get('attacks', [])):
            new_atk = dict(atk)
            if i == 0:
                new_atk['damage'] = build_damage_dice(signature_dmg)
            else:
                new_atk['damage'] = build_damage_dice(tough)
            attacks.append(new_atk)
    elif is_seal:
        # Seal demons are elite-tier; one signature at tough, rest median
        attacks = regenerate_attacks(mon.get('attacks', []), peak, is_tough=True)
    elif is_cow_king:
        attacks = regenerate_attacks(mon.get('attacks', []), peak, is_tough=True)
    elif is_locust:
        # Locusts: low damage, just 1-2 dmg (a swarm, individuals matter via count)
        attacks = []
        for atk in mon.get('attacks', []):
            new_atk = dict(atk)
            new_atk['damage'] = build_damage_dice(2)
            attacks.append(new_atk)
    elif is_angel:
        attacks = mon.get('attacks', [])  # empty — handled by seek_locust pattern
    else:
        elite = mon.get('_elite', False)
        attacks = regenerate_attacks(mon.get('attacks', []), peak, is_tough=elite)

    # ------- Speed --------
    speed = mon.get('speed', 10)
    # Preserve special speeds (fenrir 12, locust 14, etc.)

    # ------- Spawn --------
    peak_weight = derive_peak_weight(mon)
    spread = derive_spread(mon, peak)

    # ------- Build output --------
    out = {
        'name': mon.get('name'),
        'symbol': mon.get('symbol'),
        'color': mon.get('color'),
        'hp': hp_str,
        'speed': speed,
        'ai_pattern': mon.get('ai_pattern'),
        'thac0': thac0,
        # New soft-spawn fields
        'peak_floor': peak,
        'spread': spread,
        'peak_weight': peak_weight,
        # Keep min_level as the floor where bell-weight crosses ~0.05 (engine
        # transition: callers can keep using min_level for plausibility checks)
        'min_level': max(1, peak - spread * 2),
        'attacks': attacks,
        'resistances': mon.get('resistances', []),
        'weaknesses': mon.get('weaknesses', []),
        'tags': mon.get('tags', []),
        'harvest_tier': mon.get('harvest_tier', 0),
        'harvest_threshold': mon.get('harvest_threshold', 0),
        'ingredient_id': mon.get('ingredient_id'),
        'treasure': mon.get('treasure', {}),
        'lore': mon.get('lore', ''),
    }

    # Preserve optional fields verbatim
    for key in ('frequency', 'pack', 'spawn_chance',
                'can_phase_walls', 'dragon_scales',
                'gaze_paralyze', 'gaze_cooldown',
                'regen', 'regeneration',
                'rage_interval', 'rage_damage_bonus',
                'sp_drain', 'locust_interval', 'locust_count',
                'is_boss', 'is_mini_boss', 'is_seal_demon', 'is_allied',
                'attack_effects', 'base_resistances'):
        if key in mon:
            out[key] = mon[key]

    return out


# ---------------------------------------------------------------------------
# New L91-99 monsters for the variety-gap fill
# ---------------------------------------------------------------------------
# Each themed as "Abaddon's lieutenants" — these are NOT the seal demons
# (which guard the seals on specific floors). These are the regular-spawn pool
# species so L91-99 has bench depth beyond the seal demons themselves.

NEW_ABADDON_ELITES = [
    {
        'id': 'locust_swarmlord',
        'name': "locust swarmlord",
        'symbol': 'I',
        'color': [120, 80, 40],
        'peak_floor': 92,
        'tags': ['demon', 'beast'],
        'ai_pattern': 'aggressive',
        'speed': 12,
        'is_elite': False,
        'attacks_template': [
            {'name': 'chitin scythe', 'type': 'slash'},
            {'name': 'swarm call', 'type': 'poison', 'effect': 'poisoned',
             'effect_chance': 0.4, 'effect_duration': 6},
        ],
        'resistances': ['poison'],
        'weaknesses': ['fire', 'holy'],
        'harvest_tier': 4,
        'harvest_threshold': 4,
        'ingredient_id': 'swarmlord_chitin',
        'lore': "Not a locust, but a captain of locusts. Twice the size of an "
                "ordinary swarm-spawn, its mandibles ring like a gong when it "
                "calls the smaller drones to feed. Where the swarmlord goes, "
                "the wheat fields are gone by morning.",
    },
    {
        'id': 'pit_executioner',
        'name': "pit executioner",
        'symbol': 'X',
        'color': [180, 30, 30],
        'peak_floor': 93,
        'tags': ['demon'],
        'ai_pattern': 'aggressive',
        'speed': 10,
        'is_elite': True,
        'attacks_template': [
            {'name': 'great cleaver', 'type': 'slash'},
            {'name': 'iron maul', 'type': 'blunt', 'effect': 'stunned',
             'effect_chance': 0.3, 'effect_duration': 2},
        ],
        'resistances': ['fire', 'slash'],
        'weaknesses': ['holy', 'cold'],
        'harvest_tier': 4,
        'harvest_threshold': 4,
        'ingredient_id': 'executioners_iron',
        'lore': "Abaddon's headsmen. Their hoods are mortared into the skull, "
                "the cleaver never set down. They were once judges of mortal "
                "kings — now they swing for the pit alone.",
    },
    {
        'id': 'void_seraph',
        'name': "void seraph",
        'symbol': 'V',
        'color': [60, 30, 90],
        'peak_floor': 94,
        'tags': ['demon', 'celestial'],
        'ai_pattern': 'ranged',
        'speed': 10,
        'is_elite': True,
        'attacks_template': [
            {'name': 'void lance', 'type': 'magic', 'piercing': True},
            {'name': 'unmaking gaze', 'type': 'magic', 'effect': 'weakened',
             'effect_chance': 0.35, 'effect_duration': 5},
        ],
        'resistances': ['magic', 'cold'],
        'weaknesses': ['holy'],
        'harvest_tier': 4,
        'harvest_threshold': 5,
        'ingredient_id': 'void_feather',
        'lore': "A fallen seraph who kept its wings but lost its name. Six "
                "wings, six absences where a face should be. Its voice is the "
                "sound a star makes going out.",
    },
    {
        'id': 'apocalypse_herald',
        'name': "apocalypse herald",
        'symbol': 'H',
        'color': [200, 80, 60],
        'peak_floor': 95,
        'tags': ['demon'],
        'ai_pattern': 'aggressive',
        'speed': 11,
        'is_elite': False,
        'attacks_template': [
            {'name': 'trumpet blast', 'type': 'magic', 'effect': 'feared',
             'effect_chance': 0.3, 'effect_duration': 5},
            {'name': 'sickle of the harvest', 'type': 'slash'},
        ],
        'resistances': ['fire'],
        'weaknesses': ['holy', 'cold'],
        'harvest_tier': 4,
        'harvest_threshold': 4,
        'ingredient_id': 'herald_trumpet_brass',
        'lore': "The horn is fused to its lung now. Every breath is the "
                "sound of a city being read its sentence. It cannot stop "
                "blowing; it cannot stop the blowing from making the news "
                "true.",
    },
    {
        'id': 'wormwood_blight',
        'name': "wormwood blight",
        'symbol': 'w',
        'color': [120, 140, 80],
        'peak_floor': 96,
        'tags': ['demon', 'aberration'],
        'ai_pattern': 'aggressive',
        'speed': 9,
        'is_elite': False,
        'attacks_template': [
            {'name': 'bitter spore', 'type': 'poison', 'effect': 'poisoned',
             'effect_chance': 0.5, 'effect_duration': 8},
            {'name': 'rotting touch', 'type': 'poison'},
        ],
        'resistances': ['poison', 'cold'],
        'weaknesses': ['fire', 'holy'],
        'sp_drain': 4,
        'harvest_tier': 4,
        'harvest_threshold': 5,
        'ingredient_id': 'wormwood_ash',
        'lore': "The third trumpet's star fell into the rivers and made "
                "wormwood of all sweet water. This thing is what remains "
                "where it touched ground. Drinks light, exhales bile.",
    },
    {
        'id': 'iron_horseman',
        'name': "iron horseman",
        'symbol': 'h',
        'color': [120, 100, 130],
        'peak_floor': 98,
        'tags': ['demon', 'undead'],
        'ai_pattern': 'aggressive',
        'speed': 13,
        'is_elite': True,
        'attacks_template': [
            {'name': 'lance charge', 'type': 'pierce'},
            {'name': 'hoof crush', 'type': 'blunt', 'effect': 'stunned',
             'effect_chance': 0.3, 'effect_duration': 2},
        ],
        'resistances': ['slash', 'pierce'],
        'weaknesses': ['holy', 'magic'],
        'harvest_tier': 4,
        'harvest_threshold': 5,
        'ingredient_id': 'horseman_lance_shard',
        'lore': "One of the lesser riders — not Famine, not Pestilence, "
                "not War, not Death, but the kind that comes with them. "
                "Armor welded shut. The horse is part of the man now.",
    },
]


def build_new_elite(spec):
    """Construct a full monster entry for a new Abaddon-elite species using
    the same curve-driven approach."""
    peak = spec['peak_floor']
    elite = spec.get('is_elite', False)

    target_hp = monster_hp_tough(peak) if elite else monster_hp_med(peak)
    hp_str = build_hp_dice(target_hp)
    thac0 = monster_thac0_elite(peak) if elite else monster_thac0_med(peak)

    med = monster_damage_med(peak)
    tough = monster_damage_tough(peak)
    attacks = []
    for i, atk in enumerate(spec['attacks_template']):
        new_atk = dict(atk)
        target = tough if (elite and i == 0) else med
        new_atk['damage'] = build_damage_dice(target)
        attacks.append(new_atk)

    out = {
        'name': spec['name'],
        'symbol': spec['symbol'],
        'color': spec['color'],
        'hp': hp_str,
        'speed': spec['speed'],
        'ai_pattern': spec['ai_pattern'],
        'thac0': thac0,
        'peak_floor': peak,
        'spread': 4,  # narrow — these are L91-99 specialists
        'peak_weight': 4.0,
        'min_level': max(1, peak - 8),
        'attacks': attacks,
        'resistances': spec['resistances'],
        'weaknesses': spec['weaknesses'],
        'tags': spec['tags'],
        'harvest_tier': spec['harvest_tier'],
        'harvest_threshold': spec['harvest_threshold'],
        'ingredient_id': spec['ingredient_id'],
        'treasure': {
            'gold': [int(peak * 1.5), int(peak * 4)],
            'item_chance': 0.55,
            'item_tier': 5,
        },
        'lore': spec['lore'],
    }
    if 'sp_drain' in spec:
        out['sp_drain'] = spec['sp_drain']
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                            'data', 'monsters.json')
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated', 'data')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'monsters.json')

    with open(src_path, encoding='utf-8') as f:
        existing = json.load(f)

    regenerated = {}
    for mid, mon in existing.items():
        new_mon = regenerate_monster(mid, mon)
        # Strip internal markers
        new_mon.pop('_elite', None)
        regenerated[mid] = new_mon

    # Add new species
    for spec in NEW_ABADDON_ELITES:
        regenerated[spec['id']] = build_new_elite(spec)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(regenerated, f, indent=2, ensure_ascii=False)

    # ----- Summary report --------
    print(f"Wrote {len(regenerated)} monsters to {out_path}")
    print(f"  - {len(existing)} regenerated from existing data")
    print(f"  - {len(NEW_ABADDON_ELITES)} new L91-99 Abaddon-elite species added")
    print()
    print("=== Bosses (regenerated) ===")
    for bid, bfloor in BOSS_IDS.items():
        b = regenerated[bid]
        hp_avg = dice_avg(b['hp'])
        print(f"  {b['name']:<28} L{bfloor:>3}  HP={b['hp']:<14} (avg {hp_avg:>6.1f})  "
              f"THAC0={b['thac0']:>4}  speed={b['speed']}")
        for atk in b['attacks']:
            print(f"      atk: {atk['name']:<22} dmg={atk['damage']:<10} "
                  f"(avg {dice_avg(atk['damage']):>5.1f}) [{atk.get('type','?')}]")

    print()
    print("=== Seal demons ===")
    for sid, sfloor in SEAL_IDS.items():
        s = regenerated[sid]
        hp_avg = dice_avg(s['hp'])
        print(f"  {s['name']:<32} L{sfloor:>3}  HP={s['hp']:<14} (avg {hp_avg:>6.1f})  "
              f"THAC0={s['thac0']:>4}")

    print()
    print("=== Spawn pool by 10-floor band (peak_floor) ===")
    from collections import Counter
    bands = Counter()
    for mid, mon in regenerated.items():
        if mon.get('peak_weight', 0) > 0:
            band = (mon['peak_floor'] // 10) * 10
            bands[band] += 1
    for b in sorted(bands.keys()):
        marker = " <-- target >= 10" if bands[b] < 10 else ""
        print(f"  L{b:>3}-{b+9}: {bands[b]} normal-spawn species{marker}")


if __name__ == '__main__':
    main()
