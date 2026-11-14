"""Know your enemy: what the hero can learn of a creature on purpose
(winning-build plan 2026-11-13, section 3.1).

Brandon, 2026-11-12: "no omniscient monsters". Studying a corpse is the
main road to knowing a kind (family_lore.knowledge KNOWN). This module holds
the others, and the words they say (data/enemy_lore.json):

  * THE WAND OF PROBING (`probe_lines`, `probe_learn_line`): its health and
    everything it is made of (weaknesses, resistances, what it shrugs off,
    refuses and falls to easily). Probing is a deliberate tool, so it reads
    all of it, and it teaches the kind as a corpse study does (Brandon,
    2026-11-14): KNOWN, and one more kind toward its family's tiers
    (Game._learn_kind).
  * THE QUEST TEACHES THE BOSS (`quest_lines`, `page_line`): a gate boss
    has no corpse to study before the fight, so the key step of his quest
    (Ariadne's shrine, Athena's, Odin's altar, the Dwarven Forge, the Last
    Judgment) opens his page, and the quest-giver names his weakness.

Recall Lore is not here: it is the trivia quiz that gives a random hint
(data/hints.json) and never looks at a creature (Brandon, 2026-11-14).

Pure module: no pygame, no Game.
"""
from __future__ import annotations

import json

_DATA: dict | None = None


def data() -> dict:
    """data/enemy_lore.json, loaded once (bundled: PhilosophersQuest.spec)."""
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'enemy_lore.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def _fill(m, text: str, **kw) -> str:
    from monster import the_name
    t = (text or '').replace('{The}', the_name(m)).replace('{the}', the_name(m, lower=True))
    for k, v in kw.items():
        t = t.replace('{' + k + '}', str(v))
    return t[:1].upper() + t[1:]


# ---------------------------------------------------------------------------
# The Wand of Probing
# ---------------------------------------------------------------------------
def _cap(x: str) -> str:
    return str(x).replace('_', ' ').title()


def probe_lines(m) -> list:
    """What the Wand of Probing reads of `m`: its health, then what it is
    weak to and resists, then what it shrugs off, refuses and falls to
    easily (the Bestiary's own rows, affinity.page_lines)."""
    import affinity
    p = data()['probe']
    out = [_fill(m, p['hp'], hp=getattr(m, 'hp', 0), max_hp=getattr(m, 'max_hp', 0))]
    bits = []
    weak = list(getattr(m, 'weaknesses', None) or ())
    res = list(getattr(m, 'resistances', None) or ())
    if weak:
        bits.append(p['weak'].replace('{list}', ', '.join(_cap(w) for w in weak)))
    if res:
        bits.append(p['resists'].replace('{list}', ', '.join(_cap(w) for w in res)))
    bits += [t + '.' for _k, t in affinity.page_lines(m)]
    out.append(' '.join(bits) if bits else p['nothing'])
    return out


def probe_learn_line(m) -> str:
    """Said when a probe teaches the kind (a kind not yet studied, with a
    family): "You learn the ways of the Zombie." """
    return _fill(m, data()['probe']['learn'])


# ---------------------------------------------------------------------------
# The quest teaches the boss
# ---------------------------------------------------------------------------
def quest_entry(boss_kind) -> dict:
    return (data().get('quest_teach') or {}).get(str(boss_kind or '')) or {}


def quest_lines(boss_kind) -> list:
    """The quest-giver's line naming the boss's weakness, or []."""
    return list(quest_entry(boss_kind).get('lines') or ())


def page_line(boss_kind) -> str:
    return str(quest_entry(boss_kind).get('page', '') or '')
