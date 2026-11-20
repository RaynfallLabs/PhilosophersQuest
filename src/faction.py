"""Whose side a monster is on, and the healer's choice (AI-1, fix_healer,
2026-11-19).

A healer used to mend any creature that shared ANY tag with it, so an orc
priest's 'humanoid' mended a bandit, and it spent its whole turn on a
one-point scratch, every turn, with no rest between prayers: two priests
side by side out-healed a weak chain.

Now a creature's side (ai_faction) is its war-band, else its pack, else its
family, else its kind; the loose tags (humanoid, beast, evil, undead,
caster...) never make a side. A healer mends only its own side, only one
badly hurt (under heal_below of its health, 0.6), the one fighting the hero
first, then the most hurt, and after a heal it must gather itself for
heal_cooldown turns (3) before the next. Pets, escorts, called allies, the
allied angels and the encounter people are never on a monster's side.

Pure module: the game's _healer_turn and the simulator both call it.
"""
from __future__ import annotations

import kind_data


def ai_faction(m) -> tuple:
    """('band', id) | ('pack', id) | ('family', family) | ('kind', kind)."""
    d = getattr(m, '__dict__', {})
    band = d.get('_band')
    if band is not None:
        return ('band', band)
    pack = d.get('_pack')
    if pack:
        return ('pack', pack)
    fam = getattr(m, 'family', None)
    if fam:
        return ('family', fam)
    return ('kind', getattr(m, 'kind', ''))


def _outsider(o) -> bool:
    return bool(kind_data.outside_rules(o) or getattr(o, '_is_pet', False)
                or getattr(o, 'is_pet', False) or getattr(o, '_is_escort', False)
                or getattr(o, '_called_ally', False))


def same_side(a, b) -> bool:
    """b fights on a's side (b is not a itself)."""
    if b is a or not getattr(b, 'alive', False) or _outsider(b):
        return False
    if getattr(b, 'kind', None) == getattr(a, 'kind', None):
        return True
    fa = ai_faction(a)
    if fa[0] == 'band':
        return b.__dict__.get('_band') == fa[1]       # a band heals its band only
    fb = ai_faction(b)
    if fa[0] == 'pack' and fb[0] == 'pack':
        return fa[1] == fb[1]
    fam_a, fam_b = getattr(a, 'family', None), getattr(b, 'family', None)
    return bool(fam_a) and fam_a == fam_b


def heal_rules(m) -> tuple:
    r = kind_data.rules('healer')
    cd = int(kind_data.field(m, 'heal_cooldown', r.get('heal_cooldown', 3)) or 0)
    below = float(kind_data.field(m, 'heal_below', r.get('heal_below', 0.6)) or 0.6)
    return cd, below


def heal_choice(healer, monsters, player=None, reach: int | None = 1):
    """The ally this healer mends now, or None: its own side, within
    ``reach`` tiles (None: anywhere, the simulator's melee), badly hurt and
    able to heal; the one beside the hero first, then the most hurt."""
    if int(healer.__dict__.get('_heal_cd', 0) or 0) > 0:
        return None
    _cd, below = heal_rules(healer)
    best = None
    for o in monsters or ():
        if not same_side(healer, o):
            continue
        if o.hp >= o.max_hp * below or o.hp <= 0:
            continue
        if hasattr(o, 'can_heal') and not o.can_heal():
            continue                                   # its wound will not close
        if reach is not None and max(abs(o.x - healer.x), abs(o.y - healer.y)) > reach:
            continue
        front = 0
        if player is not None and hasattr(o, '_adjacent_to'):
            try:
                front = 0 if o._adjacent_to(player) else 1
            except (AttributeError, TypeError):
                front = 1
        key = (front, o.hp / max(1, o.max_hp))
        if best is None or key < best[0]:
            best = (key, o)
    return best[1] if best else None


def heal(healer, target) -> int:
    """Mend ``target`` by the healer's share; the healer then rests its
    voice. Returns what was healed (the game's line reads _heal_target)."""
    amount = max(1, int(target.max_hp * float(getattr(healer, 'heal_amount_pct', 0.25) or 0.25)))
    actual = max(0, min(amount, target.max_hp - target.hp))
    target.hp += actual
    healer._heal_target = target
    healer._heal_amount = actual
    cd, _below = heal_rules(healer)
    healer._heal_cd = cd
    return actual


def tick(m) -> None:
    """One turn of a healer's rest (Monster.tick_effects)."""
    cd = int(m.__dict__.get('_heal_cd', 0) or 0)
    if cd > 0:
        m._heal_cd = cd - 1
