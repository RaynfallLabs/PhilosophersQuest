"""Call 12 (bug bash 4): chain stuns on named foes go through the named-foe
cap, with a short immunity after a hold ends.

The chain specials (mace, maul, fist, sling...) wrote 'stunned' straight
into status_effects, so they skipped Monster.add_effect's named-foe rule,
and a fresh stun every turn kept the last one from running out: a maul at
chain 10 every turn held Asterion for the whole fight (D19: he attacked 0
times in 20 turns). Logic tests: boss fights cannot be play-tested quickly.
"""
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import combat  # noqa: E402
import items  # noqa: E402
from monster import (DeathMonster, Monster, NAMED_FOE_CONTROL_CAP,  # noqa: E402
                     NAMED_FOE_CONTROL_GRACE)
from player import Player  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    _DEFS = json.load(_f)


def _mon(kind):
    m = Monster(dict(_DEFS[kind], id=kind), 6, 5)
    m.hp = m.max_hp = 10 ** 8
    return m


def _held(m):
    return any(m.status_effects.get(e, 0) > 0
               for e in ('stunned', 'paralyzed', 'frozen', 'sleeping'))


def _fight(kind, template, chain, turns=30):
    """A chain-``chain`` blow every turn, then the monster's turn (skipped
    while held) and its status tick. Returns the list of held flags."""
    p = Player()
    p.x, p.y = 5, 5
    w = items.instantiate_weapon(template, 'iron')
    m = _mon(kind)
    log = []
    for _ in range(turns):
        combat._apply_chain_class_post_damage(p, m, w, chain, [m], None, 100)
        log.append(_held(m))          # the monster's turn: held or not
        m.tick_effects()
    return log


def test_asterion_is_a_named_foe():
    assert _mon('asterion_minotaur')._is_named_foe()
    assert not _mon('giant_rat')._is_named_foe()


def test_a_chain_stun_on_a_named_foe_is_capped():
    m = _mon('asterion_minotaur')
    combat._max_status(m, 'stunned', 3)          # mace C20 / fist C20 duration
    assert m.status_effects['stunned'] == NAMED_FOE_CONTROL_CAP


def test_chain_stuns_every_turn_no_longer_lock_a_boss():
    for kind in ('asterion_minotaur', 'fafnir_dragon', 'abaddon_destroyer'):
        for template, chain in (('maul', 10), ('mace', 15), ('mace', 20), ('sling', 15)):
            log = _fight(kind, template, chain)
            free = log.count(False)
            # Held at most CAP turns in a row, then GRACE free turns.
            run = longest = 0
            for h in log:
                run = run + 1 if h else 0
                longest = max(longest, run)
            assert longest <= NAMED_FOE_CONTROL_CAP, (kind, template, longest)
            assert free >= 30 * NAMED_FOE_CONTROL_GRACE // (
                NAMED_FOE_CONTROL_CAP + NAMED_FOE_CONTROL_GRACE), (kind, template, free)


def test_ordinary_monsters_are_still_held_by_chain_stuns():
    log = _fight('giant_rat', 'maul', 10)
    assert all(log)


def test_after_a_hold_ends_the_foe_shakes_off_the_next_for_a_while():
    m = _mon('asterion_minotaur')
    m.add_effect('stunned', 2)
    m.tick_effects()
    m.tick_effects()
    assert not m.has_effect('stunned')
    assert m.status_effects.get('control_immune') == NAMED_FOE_CONTROL_GRACE
    m.add_effect('sleeping', 5)                  # any hold, any source
    combat._max_status(m, 'paralyzed', 2)
    assert not _held(m)
    for _ in range(NAMED_FOE_CONTROL_GRACE):
        m.tick_effects()
    assert not m.has_effect('control_immune')
    m.add_effect('sleeping', 5)
    assert m.status_effects['sleeping'] == NAMED_FOE_CONTROL_CAP


def test_a_running_hold_on_a_named_foe_is_not_refreshed():
    m = _mon('fafnir_dragon')
    m.add_effect('stunned', 2)
    m.tick_effects()
    m.add_effect('stunned', 2)
    assert m.status_effects['stunned'] == 1


def test_chain_specials_do_not_stick_to_death():
    d = DeathMonster(6, 5)
    combat._max_status(d, 'stunned', 3)
    assert not d.has_effect('stunned')
