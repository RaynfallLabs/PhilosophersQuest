"""The gear balance check of 2026-11-12 (NON_AC_GEAR_BALANCE_REPORT_2026_11_12.md).

Brandon: "I got some linen bracers of deflection like.. right away, and they
seem REALLY powerful..." The fight simulator found the bracers under budget
but their card misleading, and three powers far over it:

* every guard says what it does, in one number: it takes a share off the
  damage of the attacks it guards and stops a share of their harm (it never
  made them miss);
* Striking halved (about twice its budget);
* Displacement a ladder (a flat 15% was about three times its budget);
* Speed a speed rating, not haste (Brandon: "Monsters have a speed rating,
  yes? ... that's what this power should do"; "Wisdom increases timer, not
  how fast you are").

Old saves lose the statuses Speed and Displacement used to lend.
"""
import inspect
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import enchantments as E  # noqa: E402
import gear_saves  # noqa: E402
import guards  # noqa: E402
import items  # noqa: E402
from player import Player  # noqa: E402

ALL = E.data()['enchantments']


def _wear(p, item):
    p.inventory.append(item)
    p._apply_equip(item)
    p.remove_from_inventory(item)


def _piece(slot, ench_id, level):
    """A common piece of `slot` with `ench_id` at `level`, of the first
    template and material that fit."""
    for tid, d in items.load_templates('armor').items():
        if d.get('slot') != slot:
            continue
        for mat in items.load_materials('armor'):
            try:
                return items.instantiate_armor(tid, mat, level=level, ench_id=ench_id)
            except ValueError:
                continue
    raise AssertionError(f'no {slot} piece could be made')


def _bracers(level=1):
    return items.instantiate_armor('iron_vambraces', 'linen', level=level, ench_id='deflection')


# ------------------------------------------------------------- the words

def test_every_guard_says_it_takes_damage_off_and_never_that_it_turns_aside():
    for eid, e in ALL.items():
        if e.get('lane') == 'guard' and e.get('tiers') and eid != 'parrying':
            assert 'turns aside' not in e['text'], eid
            assert e['text'].startswith('takes {pct} off the damage of'), eid


def test_the_bracers_card_says_one_number():
    b = _bracers()
    assert E.is_slot_guard(b)
    line = guards.guard_text(b)
    assert line.startswith('Guards against arrows, bolts, rays and thrown things: takes 60% off')
    assert 'what they carry' not in line and 'poison' in line


def test_an_unknown_piece_does_not_give_its_enchantment_away():
    assert '6% off' in guards.guard_text(_bracers(), known=False)   # the medium make alone


def test_only_a_slot_guard_folds_into_the_guard_line():
    assert not E.is_slot_guard(_piece('feet', 'speed', 7))
    assert not E.is_slot_guard(_piece('cloak', 'elementward', 3))    # its own family, its own line
    assert E.is_slot_guard(_piece('head', 'iron_will', 1))


def test_the_cards_use_the_one_line():
    import game_render
    assert inspect.getsource(game_render).count('is_slot_guard(item)') >= 2   # Kit and lore cards


# --------------------------------------------------------- the ladders

def test_striking_is_halved():
    assert ALL['striking']['tiers'] == [0.04, 0.04, 0.05, 0.05, 0.06]
    assert E.level_value(ALL['striking'], 10) < 0.07


def test_displacement_is_a_ladder_not_a_status():
    d = ALL['displacement']
    assert 'status' not in d and d.get('miss')
    assert E.level_value(d, 5) == 0.05                         # tier III, where it starts
    assert E.level_value(d, 10) < 0.08
    import game_combat
    assert '_enchantments.displacement(self.player)' in inspect.getsource(game_combat)


def test_a_worn_cloak_of_displacement_misses_by_its_ladder():
    p = Player()
    _wear(p, _piece('cloak', 'displacement', 5))
    assert not p.has_effect('displacement')
    assert E.displacement(p) == 0.05


def test_speed_is_a_rating_not_haste():
    s = ALL['speed']
    assert 'status' not in s and s.get('quick')
    p = Player()
    assert p.get_speed() == 10
    _wear(p, _piece('feet', 'speed', 9))
    assert not p.has_effect('hasted')
    assert p.get_speed() == 10.7
    p.status_effects['hasted'] = 5
    assert p.get_speed() == 21.4                               # haste doubles it


def test_hermes_greaves_stay_hasted_by_their_lore():
    g = items.make_item_by_id('armor', 'greaves_of_hermes')
    assert g.on_equip_status == 'hasted'
    p = Player()
    _wear(p, g)
    assert p.get_speed() == 21.2                               # haste, and Speed IV's share


# ---------------------------------------------------------- old saves

def test_an_old_pair_of_speed_boots_gives_its_haste_back():
    p = Player()
    boots = _piece('feet', 'speed', 7)
    boots.on_equip_status = 'hasted'                           # as made before 2026-11-12
    boots.special = boots.ench_line = 'Makes you quick.'
    _wear(p, boots)
    assert p.has_effect('hasted')
    gear_saves.migrate(p, [boots])
    assert boots.on_equip_status == ''
    assert not p.has_effect('hasted')
    assert boots.special.startswith('Quickens you: you act 5% more often')
    assert p.get_speed() == 10.5


def test_an_old_named_cloak_of_displacement_loses_the_status():
    p = Player()
    c = items.make_item_by_id('armor', 'cloak_of_the_morrigan')
    c.on_equip_status = 'displacement'                         # as apply_named lent it before
    _wear(p, c)
    assert p.has_effect('displacement')
    gear_saves.migrate(p, [c])
    assert c.on_equip_status == ''
    assert not p.has_effect('displacement')


def test_old_striking_gloves_tell_todays_number():
    gl = _piece('hands', 'striking', 1)
    gl.special = gl.ench_line = 'Adds 8% to the damage of your blows.'
    gear_saves.enchant_common(gl)
    assert gl.special == 'Adds 4% to the damage of your blows.'
