"""Answers Being Shot (2026-11-22; Brandon, play-testing 3.6.1: "monsters
dying left and right without really doing anything").

The diagnosis of 1,560 staged fights (DIFFICULTY_DIAGNOSIS_2026_11_22.md):
a creature that could not shoot back walked one tile a turn into a bow's
free shots, and nothing it knew answered being shot. Now a creature knows
when it is under fire, and what it does about it is its kind's nature:

  * a charger (its kind's own ``rush`` in monsters.json: an orc warrior, a
    bugbear, an ogre, a troll, a bear, a minotaur...) RUSHES: two strides a
    turn for a short burst, then it must catch its breath before it can
    rush again. Not a speed: it walks as it always did until it is shot;
  * a thinking kind ducks out of the line of fire and waits round the
    corner (the Tactical Mind's ``take_cover``, src/tactical_mind.py);
  * a band's goblin with a sling pelts the hero back (packs.band_sling);
  * a band's leader under fire stops hanging back behind his guards
    (tactics.activation, tactical_mind.band_order);
  * an archer or a caster answers with its own shot, as it always did.

Under fire: hurt by a blow since its last turn while neither it nor the hero
stood beside the other (at the top of its last turn or now) and no pet was
at it: an arrow, a bolt, a thrown flask, a spell from across the room (a
wound bleeding, burning or poisoned is no blow: ``blow_hp``). It stays
under fire ``memory`` turns (data/monster_ai.json ``under_fire``).

State in the creature's own __dict__ (``_uf_hp``, ``_uf_adj``, ``_uf_turns``,
``_uf_new``, ``_rush_left``, ``_rush_rest``), every read with a default: an
old save's monster or the simulator's copy needs nothing. Pure module.
"""
from __future__ import annotations

import ai_lines
import kind_data


def rules() -> dict:
    return kind_data.rules('under_fire')


def _int(d: dict, key: str) -> int:
    try:
        return int(d.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0


def blow_hp(m) -> int:
    """Its health with what a wound ticking took (a bleed, a burn, poison:
    Monster.take_damage's ``_dot_lost``) put back: it falls only to a blow.
    Every "struck since its last turn" test compares this, never bare
    health (here; morale's caught as it runs; a pack waiting at a narrow
    way; the Tactical Mind's hurt and its watch; a territorial creature
    roused on its ground: home_ground.leash): a goblin bleeding from a
    sword cut was taken for one shot from afar and ran for cover, and a
    charger rushed at a hero who had only stepped back. A wound that keeps
    bleeding is not a new blow (it springs no lurker and breaks no chant
    either: Monster.take_damage)."""
    return int(getattr(m, 'hp', 0) or 0) + int(getattr(m, '__dict__', {}).get('_dot_lost', 0) or 0)


def note(m, player, pets=()) -> bool:
    """At the top of its turn: was it shot since its last one? Updates its
    state and returns True when it was (a fresh wound from afar)."""
    if m is None or player is None:
        return False
    d = m.__dict__
    adj = bool(m._adjacent_to(player))
    was_hp = d.get('_uf_hp')
    was_adj = bool(d.get('_uf_adj', False))
    hurt = was_hp is not None and blow_hp(m) < int(was_hp)
    at_it = any(getattr(p, 'alive', False) and max(abs(p.x - m.x), abs(p.y - m.y)) <= 1
                for p in pets or ())
    shot = bool(hurt and not adj and not was_adj and not at_it)
    left = _int(d, '_uf_turns')
    if shot:
        m._uf_turns = int(rules().get('memory', 6))
    elif left > 0:
        m._uf_turns = left - 1
    m._uf_new = shot
    m._uf_hp = blow_hp(m)
    m._uf_adj = adj
    rest = _int(d, '_rush_rest')
    if rest > 0:
        m._rush_rest = rest - 1
    return shot


def under_fire(m) -> bool:
    """Shot within its memory of it (``note``)."""
    return _int(getattr(m, '__dict__', {}), '_uf_turns') > 0


def shot_now(m) -> bool:
    """Shot since its last turn (this turn's ``note``)."""
    return bool(getattr(m, '__dict__', {}).get('_uf_new'))


# ---------------------------------------------------------------------------
# The rush (a charger's answer)
# ---------------------------------------------------------------------------

def rush_spec(m) -> dict | None:
    """Its kind's rush ({} of its own numbers), or None when it is no charger."""
    spec = kind_data.field(m, 'rush', None)
    if spec is True:
        return {}
    if isinstance(spec, dict):
        return spec
    return None


def rusher(m) -> bool:
    return rush_spec(m) is not None


def rushing(m) -> bool:
    """It is in its rush now: two strides a turn."""
    return _int(getattr(m, '__dict__', {}), '_rush_left') > 0


def start_rush(m, player) -> bool:
    """A charger shot from afar this turn, with its breath back, starts its
    rush (its line said once a fight). True if it did."""
    spec = rush_spec(m)
    if spec is None or player is None or rushing(m) or not shot_now(m):
        return False
    if kind_data.named(m) or kind_data.outside_rules(m):
        return False                         # a named foe keeps its own tuned fight
    d = m.__dict__
    if _int(d, '_rush_rest') > 0 or m._adjacent_to(player):
        return False
    r = rules()
    m._rush_left = int(spec.get('turns', r.get('rush_turns', 3)))
    if ai_lines.once(m, 'rush'):
        ai_lines.say(m, ai_lines.fill(m, spec.get('line') or r.get('rush_line', '')),
                     spec.get('unseen') or r.get('rush_unseen', ''), 'warning')
    return True


def steps(m, base: int = 1) -> int:
    """Its strides this turn: ``base`` (2 for a fast creature), 2 in its rush."""
    return max(int(base), 2) if rushing(m) else int(base)


def spend_rush(m, player) -> None:
    """After its move: a stride of the rush spent; beside the hero (it has
    arrived) or at its end, the rush is over and it catches its breath."""
    d = m.__dict__
    left = _int(d, '_rush_left')
    if left <= 0:
        return
    left -= 1
    if left <= 0 or (player is not None and m._adjacent_to(player)):
        spec = rush_spec(m) or {}
        m._rush_left = 0
        m._rush_rest = int(spec.get('rest', rules().get('rush_rest', 12)))
    else:
        m._rush_left = left


def tell_keys(m) -> list:
    """Its tells (data/tells.json): a charger's rush."""
    if rusher(m) and not kind_data.named(m) and not kind_data.outside_rules(m):
        return ['rush']
    return []


def bestiary_lines(kind) -> list:
    """The Bestiary's line for a kind that rushes when shot at."""
    class _K:
        pass
    k = _K()
    k.kind = str(kind or '')
    if not rusher(k):
        return []
    line = rules().get('bestiary', '')
    return [line] if line else []


def stop(m) -> None:
    """Broken, frightened or held: no rush goes on."""
    if _int(getattr(m, '__dict__', {}), '_rush_left') > 0:
        m._rush_left = 0
