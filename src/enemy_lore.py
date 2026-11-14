"""Know your enemy: what the hero can learn of a creature on purpose
(winning-build plan 2026-11-13, section 3.1).

Brandon, 2026-11-12: "no omniscient monsters". Studying a corpse is the
main road to knowing a kind (family_lore.knowledge KNOWN). This module holds
the others, and the words they say (data/enemy_lore.json):

  * RECALL LORE about the creature in view (`recall_text`): by the chain of
    trivia answered, 1 its family; 2 one weakness; 3 its resistances; 4 what
    it shrugs off and what its nature refuses; 5 all of it, and its Bestiary
    page opens with no family credit (Game._open_kind_page). With nothing in
    view Recall Lore gives the general hints, as before.
  * THE WAND OF PROBING (`probe_lines`): its health and everything it is
    made of (weaknesses, resistances, what it shrugs off, refuses and falls
    to easily). Probing is a deliberate tool, so it reads all of it, and
    opens the page as Recall Lore's best does.
  * THE QUEST TEACHES THE BOSS (`quest_lines`, `page_line`): a gate boss
    has no corpse to study before the fight, so the key step of his quest
    (Ariadne's shrine, Athena's, Odin's altar, the Dwarven Forge, the Last
    Judgment) opens his page, and the quest-giver names his weakness.

Pure module: no pygame, no Game.
"""
from __future__ import annotations

import json
import random

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


def _and(words) -> str:
    words = list(words)
    return words[0] if len(words) == 1 else ', '.join(words[:-1]) + ' and ' + words[-1]


def _words_of(m, attr) -> list:
    from affinity import word_for
    return list(dict.fromkeys(word_for(w) for w in (getattr(m, attr, None) or ()) if w))


# ---------------------------------------------------------------------------
# Recall Lore about the creature in view
# ---------------------------------------------------------------------------
def recall_parts(m, chain: int, rng=None) -> list:
    """The sentences Recall Lore says of `m` at `chain` (1 to 5), in
    order; each chain says what the ones below it say."""
    rng = rng or random
    import family_lore
    import tells
    r = data()['recall']
    chain = max(1, min(5, int(chain)))
    out = []
    fid = family_lore.family_of(m)
    out.append(_fill(m, r['family'], kin=family_lore.kin(fid)) if fid else _fill(m, r['no_family']))
    if chain >= 5:
        # The whole page: everything it is made of (tells.lore_lines).
        out += tells.lore_lines(m) or [_fill(m, r['nothing_more'])]
        out.append(_fill(m, r['whole']))
        return out
    if chain >= 2:
        weak = [w for w in (getattr(m, 'weaknesses', None) or ()) if w]
        if weak:
            from affinity import word_for
            w = word_for(rng.choice(weak))
            out.append(_fill(m, r['weak'], word_cap=w[:1].upper() + w[1:]))
        else:
            out.append(_fill(m, r['no_weak']))
    if chain >= 3:
        res = _words_of(m, 'resistances')
        out.append(_fill(m, r['resists'], words=_and(res)) if res else _fill(m, r['no_resists']))
    if chain >= 4:
        more = []
        shrugs = _words_of(m, 'shrugs_off')
        if shrugs:
            more.append(_fill(m, r['shrugs_one' if len(shrugs) == 1 else 'shrugs_many'],
                              words=_and(shrugs)))
        words = tells.data().get('status_words') or {}
        immune = [words.get(e, str(e).replace('_', ' ')) for e in (getattr(m, 'status_immune', None) or ())]
        if immune:
            more.append(_fill(m, r['immune'], effects=tells._words(immune)))
        out += more or [_fill(m, r['nothing_more'])]
    return out


def recall_reach(player, m, chain: int) -> int:
    """How far the hero can remember a creature: the chain he answered, but
    no further than his family's name (chain 1) until he has begun to study
    its family (Recognise, family tier 1). Balance, 2026-11-13: with the
    whole page at chain 5 and no other bar, Recall Lore did the studying
    for him, and a kid who never studied a corpse lost almost nothing (the
    simulator's ablation: study worth 3 points of wins). You remember what
    you have learned about creatures LIKE this one."""
    import family_lore
    chain = int(chain)
    if chain <= 1 or player is None:
        return chain
    fid = family_lore.family_of(m)
    if fid and family_lore.tier(player, fid) >= 1:
        return chain
    return 1


def recall_text(m, chain: int, rng=None, player=None) -> str:
    """Recall Lore's card text for the creature in view. With `player`, the
    chain goes only as far as recall_reach allows, and the card says why."""
    reach = recall_reach(player, m, chain) if player is not None else int(chain)
    parts = recall_parts(m, reach, rng)
    if reach < int(chain):
        parts.append(_fill(m, data()['recall'].get(
            'unstudied', "You have not studied enough of its kind to remember more.")))
    return ' '.join(parts)


def recall_opens_page(chain: int) -> bool:
    """The whole page opens at chain 5."""
    return int(chain) >= 5


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


def probe_page_line() -> str:
    return data()['probe']['page']


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
