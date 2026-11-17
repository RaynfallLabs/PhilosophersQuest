"""Mini-boss tuning (2026-11-14): every band mini-boss, legendary wanderer
and seal demon sits in its group's band against floor_curve's anchors, has
a technique the hero can see coming, and aims truer than the creatures of
its floor. The numbers are written by tools/balance/mini_boss_bands.py and
were measured with the difficulty simulator (tools/balance/mini_boss_fights.py;
docs/systems/monsters.md, "Mini-boss tuning")."""
import json
import os
import statistics
import sys

import pytest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import floor_curve  # noqa: E402
import mini_boss_bands as mb  # noqa: E402


@pytest.fixture(scope='module')
def monsters():
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        return json.load(f)


def test_the_roster_is_every_rolled_mini_boss_and_the_seven_seals(monsters):
    """26 band foes and Polyphemus, the named Cyclops seated in Medusa's
    temple by ruling 13 (2026-11-17: tools/balance/mini_boss_seats.py)."""
    groups = mb.roster(monsters)
    count = {g: sum(1 for x in groups.values() if x == g) for g in ('band', 'legend', 'seal')}
    assert count == {'band': 27, 'legend': 5, 'seal': 7}, count
    assert set(groups) == set(mb.FOES), sorted(set(groups) ^ set(mb.FOES))


def test_every_foe_sits_in_its_band(monsters):
    out = []
    for mid, g in mb.roster(monsters).items():
        h, b = mb.where(mid, monsters[mid])
        if not mb.in_band(g, h, b):
            out.append((mid, g, round(h, 1), round(b, 3)))
    assert not out, out


def test_the_bands_are_a_family_not_a_scatter():
    for g, band in mb.BANDS.items():
        lo, hi = band['hp']
        assert 4.0 <= lo < hi <= 4 * lo, (g, band)
        lo, hi = band['blows']
        assert 0.0 < lo < hi <= mb.BLOWS_CAP, (g, band)


def test_the_data_matches_the_tool(monsters):
    """Running the tool on the data changes nothing: a hand edit that drifts
    off the table shows up here."""
    copy = json.loads(json.dumps(monsters))
    assert mb.apply(copy) == []


def test_no_named_foe_is_tankier_than_the_final_boss(monsters):
    cap = mb.hp_cap(monsters)
    for mid in mb.roster(monsters):
        assert mb.dice_avg(monsters[mid]['hp']) <= 1.01 * cap, mid


def test_no_turn_is_a_one_blow_death(monsters):
    """Every blow of a turn landing is at most BLOWS_CAP of a steady cook's
    health bar, and the enraged flurry at most RAGE_CAP."""
    for mid in mb.roster(monsters):
        d = monsters[mid]
        bar = floor_curve.health_bar(mb.floor_of(d))
        assert mb.blows(d) <= mb.BLOWS_CAP * bar * 1.04, mid
        assert mb.rage_blows(d) <= mb.RAGE_CAP * bar * 1.04, mid


def test_every_foe_has_a_technique_or_a_tell(monsters):
    import tells
    from monster import Monster
    bare = []
    for mid in mb.roster(monsters):
        m = Monster({**monsters[mid], 'id': mid}, 0, 0)
        if not tells.abilities(m):
            bare.append(mid)
    assert not bare, bare


def test_named_foes_aim_truer_than_their_floor(monsters):
    """A named foe's THAC0 sits under that of the ordinary creatures seated
    near its floor: it needs NAMED_NEED against the armour line's hero where
    they need a 10 (a rare big blow is luck; a sure one is a fight)."""
    ordinary = [(int(d.get('peak_floor') or 1), int(d['thac0'])) for d in monsters.values()
                if float(d.get('peak_weight', 0) or 0) > 0 and not d.get('is_mini_boss')
                and not d.get('is_boss') and 'thac0' in d]
    loose = []
    for mid in mb.roster(monsters):
        f = mb.floor_of(monsters[mid])
        near = [t for pf, t in ordinary if abs(pf - f) <= 5]
        if int(monsters[mid]['thac0']) > statistics.median(near) - 2:
            loose.append((mid, monsters[mid]['thac0'], statistics.median(near)))
    assert not loose, loose


def test_the_armour_line_rule_for_named_foes(monsters):
    """named_thac0: NAMED_NEED on the d20 against the line's hero, plus the
    foe's own aim; rebake_thac0 uses it for every foe the band tool owns."""
    line = {f: -3.4 for f in range(1, 101)}
    for mid in mb.roster(monsters):
        assert mb.named_thac0(mid, monsters[mid], line) == \
            -3 + mb.NAMED_NEED + int(mb.FOES[mid].get('aim', 0))
    import inspect
    import rebake_thac0
    assert 'named_thac0' in inspect.getsource(rebake_thac0.rebake)


def test_the_new_techniques_read_as_lines(monsters):
    """The four that had none (Talos, Cacus, the Sphinx, the Nemean Lion) and
    the Calydonian Boar's charge."""
    from monster import Monster, attack_line
    talos = Monster({**monsters['talos'], 'id': 'talos'}, 0, 0)
    hug = next(a for a in talos.attacks if a['name'] == 'Red-Hot Hug')
    assert hug['effect'] == 'burning' and hug['delivery'] == 'grapple'
    assert attack_line(talos, hug, 9) == 'Talos hugs you to a red-hot chest for 9 damage!'
    sphinx = Monster({**monsters['the_sphinx'], 'id': 'the_sphinx'}, 0, 0)
    riddle = next(a for a in sphinx.attacks if a['name'] == 'Whispered Riddle')
    assert riddle['effect'] == 'confused' and riddle['delivery'] == 'voice'
    assert attack_line(sphinx, riddle, 2) == 'The Sphinx puts a riddle to you for 2 damage!'
    assert sphinx._miss_text(riddle) == "The Sphinx's whispered riddle fails to take hold of you!"
    cacus = monsters['cacus']
    assert {a.get('effect') for a in cacus['attacks']} >= {'burning', 'blinded'}
    assert any(a.get('effect') == 'bleeding' for a in monsters['nemean_lion']['attacks'])
    assert monsters['calydonian_boar'].get('can_charge') is True
