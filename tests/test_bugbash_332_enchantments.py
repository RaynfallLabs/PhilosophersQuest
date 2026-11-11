"""Armour 3/7 (bug bash 3.3.2): the minor-slot enchantment stable.

data/enchantments.json, src/enchantments.py: a minor piece of level 1-10
carries one enchantment of its own slot, in four lanes (guard, might,
craft, way). Guard ladders are the armour model's; might multiplies the
hero's blows; craft forgives the first wrong answer of every Nth quiz on
its subject (no chance); the way lane holds the powers moved off rings.
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import enchantments as E  # noqa: E402
import gear  # noqa: E402
import guards  # noqa: E402
import items  # noqa: E402

ALL = E.data()['enchantments']


# ---------------------------------------------------------------- data

def test_every_enchantment_lives_on_one_minor_slot_in_a_real_lane():
    for k, v in ALL.items():
        assert v['slot'] in gear.MINOR_SLOTS, k
        assert v['lane'] in ('guard', 'might', 'craft', 'way'), k
        assert v.get('name') and v.get('text'), k


def test_every_slot_is_a_choice():
    """At least two options a slot, and one of them its guard."""
    for slot in gear.MINOR_SLOTS:
        here = E.for_slot(slot)
        assert len(here) >= 2, slot
        assert any(v['lane'] == 'guard' for v in here.values()), slot


def test_one_home_per_power():
    statuses = [v['status'] for v in ALL.values() if v.get('status')]
    stats = [v['stat'] for v in ALL.values() if v.get('stat')]
    subjects = [v['subject'] for v in ALL.values() if v.get('subject')]
    assert len(statuses) == len(set(statuses))
    assert len(stats) == len(set(stats))
    assert len(subjects) == len(set(subjects))


def test_ladders_rise_and_stay_under_the_cap():
    cap = guards.rules()['cap']['rider']
    for k, v in ALL.items():
        if not v.get('tiers'):
            continue
        vals = [E.level_value(v, lv) for lv in range(1, 11)]
        assert vals == sorted(vals), k
        assert vals[-1] <= max(cap, 1.0), k


def test_lesser_and_greater_forms():
    iw = ALL['iron_will']
    assert E.level_value(iw, 3) == pytest.approx(0.46)                  # tier II lesser
    assert E.level_value(iw, 4) == pytest.approx((0.46 + 0.64) / 2)      # tier II greater
    assert E.display_name(iw, 3) == 'of Iron Will II'
    assert E.display_name(iw, 4) == 'of Greater Iron Will II'


def test_a_roll_respects_where_an_enchantment_is_found():
    rng = random.Random(1)
    for _ in range(400):
        lv = rng.randint(1, 10)
        k = E.roll('head', lv, rng)
        assert E.available(ALL[k], E.tier_of(lv)), (k, lv)
        k = E.roll('cloak', 7, rng)                       # tier IV: Vapourward skips it
        assert k != 'vapourward'
    assert all(E.roll('feet', 1, rng) != 'speed' for _ in range(200))   # from tier IV


# ---------------------------------------------------------------- pieces

def _piece(tpl, slot_ench, level, mat='damascus_steel'):
    return items.instantiate_armor(tpl, mat, level=level, ench_id=slot_ench)


def test_a_made_piece_carries_its_name_line_and_grants():
    helm = _piece('steel_helm', 'telepathy', 6)
    assert helm.name.endswith('of Greater Telepathy III')
    assert helm.special.startswith('Lets you sense minds')
    assert helm.on_equip_status == 'telepathy'
    gloves = _piece('gauntlets', 'ogre_power', 9)
    assert gloves.effects == {'stat': 'STR', 'amount': 5}
    boots = _piece('leather_boots', 'elvenkind', 4, mat='leather')
    assert boots.passive_silent_walk is True
    # Never on a core piece, never at level 0.
    assert not _piece('plate', 'iron_will', 5).ench_id
    assert not items.instantiate_armor('steel_helm', 'damascus_steel', ench_id='iron_will').ench_id


class _P:
    def __init__(self, pieces=()):
        self.armor_slots = [None] * len(items.ARMOR_SLOTS)
        for p in pieces:
            self.armor_slots[items.ARMOR_SLOTS.index(p.slot)] = p


def test_a_guard_enchantment_is_most_of_the_guard():
    plain = items.instantiate_armor('steel_helm', 'damascus_steel')
    iw = _piece('steel_helm', 'iron_will', 5)
    voice = {'delivery': 'voice', 'type': 'psionic', 'effect': 'feared'}
    kd0 = guards.guard_keep(_P([plain]), voice)[0]
    kd1 = guards.guard_keep(_P([iw]), voice)[0]
    assert kd1 < kd0
    # A medium helm's own 0.06 and Iron Will III's 0.64 add.
    assert kd1 == pytest.approx(1 - (0.06 + 0.64))


def test_elementward_guards_fire_from_any_attack():
    cloak = _piece('cloak', 'elementward', 9, mat='leather')
    fire_bite = {'delivery': 'bite', 'type': 'fire', 'effect': 'burning'}
    kd, kr, _ = guards.guard_keep(_P([cloak]), fire_bite)
    assert kd < 0.5 and kr < 0.5


def test_blessing_and_curse_move_the_working_level():
    p = _piece('steel_helm', 'iron_will', 5)
    assert E.effective_level(p) == 5
    p.buc = 'blessed'
    assert E.effective_level(p) == 6
    p.buc = 'cursed'
    assert E.effective_level(p) == 4


def test_wear_takes_a_level_and_the_smith_gives_it_back():
    p = _piece('steel_helm', 'iron_will', 6)
    assert items.wear_down(p)
    assert p.ench_level == 5 and p.wear_loss == 1 and p.enchant_bonus == 0
    assert p.quiz_tier == gear.tier_for_level(5)


# ---------------------------------------------------------------- in play

@pytest.fixture
def game(monkeypatch, tmp_path):
    import quiz_engine
    import save_system
    import bones
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda n: str(tmp_path / f'save_{n}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(5)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_bugbash_332_ench__')
    g.monsters = []
    g.state = STATE_PLAYER
    return g


def _wear(p, piece):
    p.armor_slots[items.ARMOR_SLOTS.index(piece.slot)] = piece


def test_striking_and_archery_add_to_the_blow(game):
    import combat
    from monster import Monster
    import json
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        rat = dict(json.load(f)['giant_rat'], id='giant_rat')
    m = Monster(rat, 0, 0)
    p = game.player
    before = combat.strike_damage(p, m, 5)
    _wear(p, _piece('gauntlets', 'striking', 10))
    after = combat.strike_damage(p, m, 5)
    assert after >= before
    assert E.might(p, 'striking') == pytest.approx(E.level_value(ALL['striking'], 10))


def test_parrying_turns_a_blow_from_beside(game, monkeypatch):
    import monster as monster_mod
    from monster import Monster
    import json
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        rat = dict(json.load(f)['giant_rat'], id='giant_rat')
    rat['thac0'] = -50                                    # always hits
    m = Monster(rat, game.player.x + 1, game.player.y)
    _wear(game.player, _piece('steel_vambraces', 'parrying', 10))
    # No dodge to slip it first (a rolled hero with DEX over 10 would).
    game.player.DEX = 10
    monkeypatch.setattr(type(game.player), 'dodge_chance', lambda self: 0.0, raising=False)
    monkeypatch.setattr(monster_mod.random, 'random', lambda: 0.0)
    dmg, msg = m._resolve_blow(m.attacks[0], game.player)
    assert dmg == 0 and 'parry' in msg


def test_craft_forgives_every_nth_quiz(game):
    p = game.player
    _wear(p, _piece('gauntlets', 'the_locksmith', 1))     # level 1: every 6th
    every = E.data()['craft_every'][0]
    hits = [game._craft_forgives('economics') for _ in range(every * 2)]
    assert hits.count(True) == 2 and hits[every - 1] and hits[-1]
    assert not game._craft_forgives('cooking')            # not its subject


def test_the_quiz_engine_arms_the_second_chance(game):
    p = game.player
    _wear(p, _piece('gauntlets', 'the_locksmith', 9))     # every 3rd
    qe = game.quiz_engine
    armed = []
    for _ in range(3):
        qe.start_quiz(mode='threshold', subject='economics', tier=1,
                      callback=lambda r: None, threshold=1, total_qs=1)
        armed.append(qe.reroll_available)
        qe._end(success=True)
    assert armed == [False, False, True]
    # A chain quiz gets the forgiveness, not a reroll.
    for _ in range(3):
        qe.start_quiz(mode='chain', subject='economics', tier=1,
                      callback=lambda r: None)
        last = qe.forgive_available
        qe._end(success=True)
    assert last is True


def test_swift_strokes_and_the_hair_shirt(game):
    p = game.player
    base = p.get_quiz_extra_seconds('math')
    _wear(p, _piece('steel_vambraces', 'swift_strokes', 10))
    assert p.get_quiz_extra_seconds('math') == base + 11
    _wear(p, _piece('padded_shirt', 'the_hair_shirt', 9, mat='leather'))
    p.prayer_cooldown = 200
    game._apply_prayer_cooldown_quirks()
    assert p.prayer_cooldown == round(200 * (1 - E.level_value(ALL['the_hair_shirt'], 9)))


def test_ogre_power_lends_strength_while_worn(game):
    p = game.player
    str0 = p.STR
    gloves = _piece('gauntlets', 'ogre_power', 5)          # tier III: +3
    p.inventory.append(gloves)
    p._apply_equip(gloves)
    assert p.STR == str0 + 3
    idx = items.ARMOR_SLOTS.index('hands')
    p.armor_slots[idx] = None
    p.shed_worn_grants(gloves)
    assert p.STR == str0


def test_elvenkind_boots_quiet_the_sleepers(game):
    import sleepers
    p = game.player
    assert not sleepers._wears(p, flag='passive_silent_walk')
    _wear(p, _piece('leather_boots', 'elvenkind', 4, mat='leather'))
    assert sleepers._wears(p, flag='passive_silent_walk')
    assert p.wears_flag('passive_silent_walk')
