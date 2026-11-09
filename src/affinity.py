"""Weakness and resistance: what a hit met, and the lines that say so.

Brandon, bug bash 3.3.2: "when you hit something with its weakness or with
its resistance, we should have a whole set of pokemon style messages, so
you know it when you are blocked or effective."

A hit that meets a creature's weakness or resistance is noted here: the
hero's blows and shots by combat.strike_damage (the form and substance of
the weapon, after every bypass), spells, wands and anything else typed by
Monster.take_damage. At the end of the action Game._advance_turn drains the
notes and says one line for each way creatures were struck (a weakness,
a resistance), picked from data/affinity_lines.json. Damage over time
(a burn ticking) is not a hit and is not noted.

When they are said (3.3.3 lore audit): a kill says them first, before "X is
slain!" and its loot (Game._say_action_lines, from _on_monster_killed); the
world's turn says its own at its end (Boots of Thor, a pet's typed blow), not
after the hero's next action; and the queue is emptied on a new game, a
load and a change of floor. A blow on which a family technique has just
said the weakness (Bonebreaker) is not noted (combat.strike_damage).
"""
from __future__ import annotations

import json
import random
from functools import lru_cache

WEAK = 'weak'
RESISTED = 'resisted'

_PENDING: list = []


@lru_cache(maxsize=1)
def lines() -> dict:
    from paths import data_path
    with open(data_path('data', 'affinity_lines.json'), encoding='utf-8') as f:
        return json.load(f)


def kind_of(mult: float) -> str:
    """'weak' above 1, 'resisted' below 1, '' for a plain hit."""
    if mult > 1.0 + 1e-9:
        return WEAK
    if mult < 1.0 - 1e-9:
        return RESISTED
    return ''


def note(monster, kind: str, word: str) -> None:
    """A hit on `monster` met its weakness or its resistance (`word`: the
    damage type, form or substance that did)."""
    if kind in (WEAK, RESISTED) and monster is not None:
        _PENDING.append((monster, kind, str(word or '')))


def drain() -> list:
    """The notes since the last drain, cleared."""
    out = list(_PENDING)
    _PENDING.clear()
    return out


def word_for(word: str) -> str:
    return str((lines().get('words') or {}).get(word, str(word).replace('_', ' ')))


def say(notes, rng=None) -> list:
    """The lines for one action's notes: one per kind of meeting (weakness,
    resistance), naming the creature, or all of them when several were
    struck the same way."""
    rng = rng or random
    from monster import the_name
    by_kind: dict = {}
    for m, kind, word in notes:
        by_kind.setdefault(kind, []).append((m, word))
    out = []
    for kind in (WEAK, RESISTED):
        hits = by_kind.get(kind)
        if not hits:
            continue
        monsters = []
        for m, _w in hits:
            if all(m is not x for x in monsters):
                monsters.append(m)
        m, word = hits[0]
        w = word_for(word)
        pool = lines().get(f"{kind}_many" if len(monsters) > 1 else kind) or lines().get(kind) or []
        if not pool:
            continue
        text = rng.choice(pool).format(name=the_name(m), the=the_name(m, lower=True),
                                       word=w, word_cap=w[:1].upper() + w[1:])
        out.append((text, kind))
    return out
