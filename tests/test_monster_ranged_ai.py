"""Fleeing casters/archers must actually threaten the player (2026-06-08).

A 'cowardly' monster only attacks if it STARTS a turn adjacent (monster.py:931);
in open ground it flees forever and never attacks. A Skeleton MAGE with a
melee-only 'cast' attack therefore did literally nothing. Casters/archers are now
'ranged' (kite + fire), ranged-attack recognition gained an explicit 'ranged'
flag plus 'cast'/'bow'/'spore'/'shock'/... keywords, and every ranged-pattern
monster must have a usable ranged attack.
"""
import json
from pathlib import Path

# Mirror monster.py's _RANGED_WORDS (kept in sync by the tests below).
_RANGED_WORDS = {'shoot', 'arrow', 'bolt', 'dart', 'spit', 'hurl', 'volley', 'ray',
                 'blast', 'breath', 'spike', 'gaze', 'song', 'wail', 'charm',
                 'psionic', 'disintegrat', 'cast', 'bow', 'sling', 'javelin',
                 'spore', 'shock', 'hex'}
_MON = json.loads((Path(__file__).resolve().parents[1] / 'data' / 'monsters.json')
                  .read_text(encoding='utf-8'))


def _is_ranged_attack(a):
    return bool(a.get('ranged')) or any(w in a.get('name', '').lower() for w in _RANGED_WORDS)


def test_ranged_words_match_monster_module():
    """Keep the test's word list in sync with monster.py so this file stays honest."""
    src = (Path(__file__).resolve().parents[1] / 'src' / 'monster.py').read_text(encoding='utf-8')
    for w in _RANGED_WORDS:
        assert f"'{w}'" in src, f"_RANGED_WORDS in monster.py missing {w!r}"


def test_every_ranged_monster_has_a_usable_ranged_attack():
    """A 'ranged' monster with no recognizable ranged attack can't kite -- it
    would flail at melee range or fire a melee weapon. The archer/caster bug."""
    bad = []
    for k, m in _MON.items():
        if m.get('ai_pattern') == 'ranged':
            if not any(_is_ranged_attack(a) for a in m.get('attacks', []) or []):
                bad.append(f"{m.get('name')} ({k}): {[a.get('name') for a in m.get('attacks', [])]}")
    assert not bad, "ranged monsters with NO usable ranged attack:\n  " + "\n  ".join(bad)


def test_fixed_casters_are_ranged_kiters_not_cowards():
    casters = ["Skeleton Mage", "Death Mage", "Bone Witch", "Necromancer Lord",
               "Lizardfolk Shaman", "goblin shaman", "battle mage", "drow mage"]
    by_name = {m['name']: m for m in _MON.values()}
    for nm in casters:
        m = by_name[nm]
        assert m['ai_pattern'] == 'ranged', f"{nm} should be ranged, is {m['ai_pattern']}"
        assert any(_is_ranged_attack(a) for a in m['attacks']), f"{nm} has no ranged spell"


def test_no_caster_tagged_monster_left_cowardly():
    """A 'caster' that flees never casts -- none should remain cowardly."""
    bad = [m['name'] for m in _MON.values()
           if 'caster' in (m.get('tags') or []) and m.get('ai_pattern') == 'cowardly']
    assert not bad, f"caster monsters still cowardly (flee, never cast): {bad}"


def test_archers_fire_their_bows():
    """orc/gnoll/bandit archers' bow attacks must now register as ranged."""
    by_name = {m['name']: m for m in _MON.values()}
    for nm in ['orc archer', 'gnoll archer', 'bandit archer']:
        m = by_name[nm]
        assert m['ai_pattern'] == 'ranged'
        assert any(_is_ranged_attack(a) for a in m['attacks']), f"{nm} bow not ranged-recognized"


def test_explicit_ranged_flag_is_honored():
    """A flag-only ranged attack (no keyword in its name) still counts -- Pale
    Master's 'death_wave'."""
    pm = next(m for m in _MON.values() if m['name'] == 'Pale Master')
    dw = next(a for a in pm['attacks'] if a['name'] == 'death_wave')
    assert dw.get('ranged') is True and _is_ranged_attack(dw)
