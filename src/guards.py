"""Slot guards: what the minor armour slots turn aside (bug bash 3.3.2).

docs/design/ARMOR_REDESIGN_PLAN.md section 7, data/armor_guards.json. The
helm, gloves, bracers, greaves, boots, cloak and shirt give no AC (gear.py);
each guards one family of attack: the helm voice and gaze and the riders of
the mind, the gloves touch and grapple and the holds, the bracers missiles,
the legs bites and stings and poison, the boots trample and what pins the
feet, the cloak breath and the elements, the shirt poison, drain and
necrotic harm and the riders of the blood.

A worn piece guards by its template's weight class (a little) and by its
enchantment when that enchantment is its slot's guard (enchantments.py, the
real power). Several pieces that match one attack each take their share.

Pure rules: no pygame. monster.py asks `guard_keep` when a blow lands and
`rider_keep` when its rider rolls; `touch_ac` is the AC a touch attack
rolls against (3e "touch AC": no body armour, no shield).
"""
from __future__ import annotations

import json
from functools import lru_cache

DELIVERIES = ('blow', 'bite', 'sting', 'trample', 'grapple', 'touch',
              'voice', 'gaze', 'breath', 'ranged')


@lru_cache(maxsize=1)
def rules() -> dict:
    from paths import data_path
    with open(data_path('data', 'armor_guards.json'), encoding='utf-8') as f:
        return json.load(f)


_RULES = (
    ('gaze', r'gaze|stare|glare'),
    ('voice', r'wail|scream|shriek|howl|song|roar|mind|psych|charm|hex|curse|whisper'),
    ('touch', r'touch|drain|pseudopod|engulf'),
    ('bite', r'bite|fang|maw|jaws'),
    ('sting', r'sting|stinger|tail'),
    ('trample', r'trample|stomp|sweep|charge|gore|ram\b'),
    ('grapple', r'constrict|crush|grab|grapple|squeeze|tentacle|hug|wrap'),
)
_BREATH = r'breath|spit|spray|exhal'
_RANGED = r'bolt|ray|shard|hurl|arrow|volley|throw|javelin|missile'


def classify(atk: dict) -> str:
    """Read an attack's delivery from its name, `ranged` flag and damage
    type (the rules tools/balance/armor_model.py priced the guards with)."""
    import re
    atk = atk or {}
    n = str(atk.get('name', '')).lower()
    if re.search(_BREATH, n):
        return 'breath'
    if atk.get('ranged') or re.search(_RANGED, n):
        return 'ranged'
    for d, pat in _RULES:
        if re.search(pat, n) or (d == 'voice' and atk.get('type') == 'psionic'):
            return d
    return 'blow'


def delivery(atk: dict) -> str:
    """How an attack lands: its `delivery` (written into monsters.json by
    tools/content/tag_attack_delivery.py), else read from it (an attack made
    at runtime: a summoned or shaped creature)."""
    d = (atk or {}).get('delivery')
    if d in DELIVERIES:
        return d
    return classify(atk)


def family(slot: str) -> dict:
    return rules()['families'].get(slot) or {}


def matches(fam: dict, atk: dict) -> tuple:
    """(guards its damage, guards its rider) for one family and one attack."""
    d = delivery(atk)
    typ = str(atk.get('type', 'physical'))
    eff = atk.get('effect')
    dels = fam.get('deliveries') or ()
    dmg = d in dels or typ in (fam.get('elements') or ())
    rider = bool(eff) and (
        d in dels
        or bool(fam.get('riders_all'))           # a Ring of Protection's saving throw
        or eff in (fam.get('riders_any') or ())
        or d in ((fam.get('riders_from') or {}).get(eff) or ()))
    return dmg, rider


def piece_strength(piece) -> tuple:
    """(rider shrug, damage turn-aside) a worn minor piece gives its slot's
    family: the template's weight class, plus its guard enchantment."""
    base = rules()['base_by_weight_class'].get(
        str(getattr(piece, 'weight_class', None) or 'light'), {})
    rider, damage = float(base.get('rider', 0.0)), float(base.get('damage', 0.0))
    try:
        import enchantments
        r2, d2 = enchantments.guard_strength(piece)
        rider, damage = rider + r2, damage + d2
    except ImportError:
        pass
    return rider, damage


def _worn_minor(player):
    import gear
    from items import ARMOR_SLOTS
    for i, piece in enumerate(getattr(player, 'armor_slots', None) or ()):
        if piece is None:
            continue
        slot = getattr(piece, 'slot', None) or (ARMOR_SLOTS[i] if i < len(ARMOR_SLOTS) else '')
        if slot in gear.MINOR_SLOTS:
            yield slot, piece


def guard_keep(player, atk: dict) -> tuple:
    """(share of the damage kept, share of the rider chance kept, the piece
    that guarded the rider most) for an attack against `player`."""
    caps = rules()['cap']
    keep_d = keep_r = 1.0
    best, best_r = None, 0.0
    for slot, piece in _worn_minor(player):
        # The slot's own family (the template's base guard, plus a guard
        # enchantment of that family), then any family a guard enchantment
        # names for itself (the cloak's Elementward and Vapourward).
        parts = [(family(slot),) + piece_strength(piece)]
        try:
            import enchantments
            parts += [(fam, r, d) for fam, r, d in enchantments.guard_families(piece)]
        except ImportError:
            pass
        for fam, r, d in parts:
            dmg, rider = matches(fam, atk)
            if dmg:
                keep_d *= max(0.0, 1.0 - d)
            if rider:
                keep_r *= max(0.0, 1.0 - r)
                if r > best_r:
                    best, best_r = piece, r
    # Rings (rings.py): Protection, a saving throw against every rider;
    # Spell Turning, magic, shadow and psionic damage turned aside.
    try:
        import rings
        for fam, r, d, ring in rings.guard_parts(player):
            dmg, rider = matches(fam, atk)
            if dmg and d:
                keep_d *= max(0.0, 1.0 - d)
            if rider and r:
                keep_r *= max(0.0, 1.0 - r)
                if r > best_r:
                    best, best_r = ring, r
    except ImportError:
        pass
    keep_d = max(1.0 - caps['damage'], keep_d)
    keep_r = max(1.0 - caps['rider'], keep_r)
    return keep_d, keep_r, best


def touch_ac(player) -> int:
    """The AC a touch attack rolls against: the hero's AC without body
    armour and shield (a ghoul's touch does not care how thick the plate
    is; the gloves guard against it instead)."""
    core = int(getattr(player, 'core_ac', lambda: 0)() or 0)
    return int(player.get_ac()) + core
