"""Venom: how strong a poison is, how doses add, and what it will still take, pure.

Brandon, 2026-11-22: "poison is such a low number of turns I barely
noticed it; two damage? why have these cure poison potions...". A
poison tick was 2% of the hero's max HP whatever bit him, so a cobra
and a hydra bit alike, and on floors 6-20 the share rounded down to 1-2.

- **Each venom has its own strength:** the attack's ``venom`` field in
  data/monsters.json, damage a turn, written kind by kind from its lore
  (tools/content/poison_pass_2026_11_22.py). Never scaled by the floor;
  toughness and the rest of Player.take_damage still apply. A poison with
  no venom (a potion, a trap, foul water) keeps the old share
  (status_effects.dot_tick).
- **Doses add, a little:** a bite on a poisoned hero adds half its turns,
  never past one and a half of the longest dose (data/effects.json
  ``poison``). The strongest venom on him sets the tick.
- **A CON save halves the dose** (it never cancels the bite).
- **Venom Ward** (a plain meal against venom): half the venom, half the turns.
- **It shows:** what the venom will still take (``to_come``) is drawn on
  the HP bar and said on the chip and on each bite.

The record is ``player._venom``, a plain dict saved with the hero:
``venom`` (damage a turn, 0 for a share poison), ``dose`` (the longest
dose of this bout) and ``by`` (who laid the strongest).
"""
from __future__ import annotations

import random

import effect_rules

STATUS = 'poisoned'
WARD = 'venom_ward'


def rules() -> dict:
    return effect_rules.data()['poison']


def record(player) -> dict:
    d = player.__dict__.get('_venom')
    if not isinstance(d, dict):
        d = player.__dict__['_venom'] = {}
    return d


def on(player) -> bool:
    return int((getattr(player, 'status_effects', None) or {}).get(STATUS, 0) or 0) > 0


def warded(player) -> bool:
    return int((getattr(player, 'status_effects', None) or {}).get(WARD, 0) or 0) != 0


def _half(n: int) -> int:
    return max(1, (int(n) + 1) // 2)


# ---------------------------------------------------------------------------
# Doses
# ---------------------------------------------------------------------------

def dose(player, current: int, turns: int, limit: int) -> int:
    """The poison's turns after a new dose of ``turns`` lands on ``current``
    (status_effects.apply_effect). A first dose starts the bout afresh."""
    r = rules()
    turns = max(1, int(turns))
    if warded(player):
        turns = _half(turns)
    rec = record(player)
    if int(current or 0) <= 0:
        rec.clear()
        rec['venom'], rec['dose'] = 0, turns
        return min(turns, limit)
    # The longest single dose of the bout (what was left, for a poison from
    # an older save that kept no record), never the turns already added up.
    longest = max(int(rec.get('dose', 0) or 0) or int(current), turns)
    rec['dose'] = longest
    added = int(current) + int(round(turns * float(r['add_share']) + 1e-9))
    top = int(longest * float(r['most_doses']))
    return min(max(int(current), turns, min(added, top)), limit)


def lands(player, turns: int, dc: int, source=None, venom: int | None = None) -> tuple[bool, str]:
    """A monster's poison that passed its chance (status_effects.
    apply_debuff_with_save): a CON save halves the dose, then the venom is
    noted. Returns (applied, the line)."""
    r = rules()
    stat = 'CON'
    mod = (int(getattr(player, stat, 10)) - 10) // 2
    bonus = player.save_bonus_for(stat) if hasattr(player, 'save_bonus_for') else 0
    saved = random.randint(1, 20) + mod + bonus >= int(dc)
    turns = max(1, int(turns))
    if saved:
        turns = _half(turns)
    was = on(player)
    strong_before = int(record(player).get('venom', 0) or 0) if was else 0
    applied = player.add_effect(STATUS, turns)
    if not applied:
        return False, ''
    rec = record(player)
    v = max(0, int(venom or 0))
    if v >= strong_before and v > 0:
        rec['venom'] = v
        if source is not None:
            try:
                from monster import the_name
                rec['by'] = the_name(source)
            except Exception:
                rec['by'] = str(getattr(source, 'name', '') or '')
    n = to_come(player)
    lines = r['lines']
    warn = warn_once(player)
    warn = (' ' + warn) if warn else ''
    if saved:
        return True, lines['saved'].format(n=n) + warn
    by = rec.get('by') or ''
    if by and v > 0:
        return True, lines['bitten'].format(by=by, n=n) + warn
    return True, lines['poisoned'].format(n=n) + warn


# ---------------------------------------------------------------------------
# The tick, and what is still to come
# ---------------------------------------------------------------------------

def strength(player) -> int:
    """What one turn of the poison on him does before his body's share
    (the venom, or the old share of max HP for a poison with none)."""
    v = int(record(player).get('venom', 0) or 0) if on(player) else 0
    if v <= 0:
        from status_effects import dot_tick
        v = dot_tick(player)
    if warded(player):
        v = _half(v)
    return v


def _after_body(player, amount: int) -> int:
    """Player.take_damage's shares of a poison tick, without the damage: the
    lore circle, a dish's song, toughness."""
    if amount <= 1:
        return max(0, amount)
    try:
        import family_edges
        c = family_edges.any_damage_mult(player, 'poison')
        if c < 1.0:
            amount = max(1, int(round(amount * c)))
    except Exception:
        pass
    try:
        import songs
        m = songs.damage_mult(player)
        if m < 1.0:
            amount = max(1, int(round(amount * m)))
    except Exception:
        pass
    tough = getattr(player, 'toughness', None)
    if amount > 1 and callable(tough):
        amount = max(1, int(round(amount * (1.0 - tough()))))
    return amount


def per_turn(player) -> int:
    """HP one turn of it takes now (0 while poison is warded off whole)."""
    if not on(player) or player.has_effect('poison_resist') or player.has_effect('invulnerable'):
        return 0
    return _after_body(player, strength(player))


def to_come(player) -> int:
    """HP the poison will still take if nothing is done: a turn's toll for
    every turn left (status_effects.tick_all deals one a turn while it runs)."""
    if not on(player):
        return 0
    return per_turn(player) * int(player.status_effects.get(STATUS, 0) or 0)


def deadly(player) -> bool:
    """What is to come is more than he has: drink the cure now."""
    n = to_come(player)
    return n > 0 and n >= int(getattr(player, 'hp', 0) or 0)


def chip(player) -> str:
    """The chip's words: "Poisoned: 14 to come" (the sidebar draws it in the
    danger colour when it would kill: ui._effects)."""
    return rules()['lines']['chip'].format(n=to_come(player))


def warn_once(player) -> str:
    """The line that says the venom would kill him, once a bout (on the
    bite that makes it so, or the turn his health falls under it)."""
    rec = record(player)
    if not deadly(player) or rec.get('warned'):
        return ''
    rec['warned'] = True
    return rules()['lines']['deadly']


def attack_note(atk: dict) -> str:
    """A poison attack's venom for the Bestiary: "2 a turn, 6 turns"."""
    v = int((atk or {}).get('venom', 0) or 0)
    turns = (atk or {}).get('effect_duration')
    if v <= 0:
        return ''
    return rules()['lines']['bestiary'].format(v=v, t=turns if turns is not None else '?')
