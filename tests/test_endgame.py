"""Phase 6 of the rebalance (2026-10): the end of the game.

Logic tests: floor 80 to 100 and the climb out cannot be play-tested in
any useful way.
"""
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import floor_curve  # noqa: E402
from monster import DeathMonster  # noqa: E402
from player import Player  # noqa: E402


def _defs():
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        return json.load(f)


def _mean(dice):
    from dice import roll
    return sum(roll(dice) for _ in range(300)) / 300.0


def test_deaths_scythe_takes_a_share_of_your_health():
    """2d12+15 was nearly half of a 60-point health bar when it was written
    and 6% of the 450-point one a winner carries."""
    assert 0.05 <= floor_curve.DEATH_REAP_SHARE <= 0.15
    death = DeathMonster()
    big = Player()
    big.max_hp = big.hp = 500
    took, msg = death.attack(big)
    assert took == int(round(floor_curve.DEATH_REAP_SHARE * 500)) and 'scythe' in msg
    small = Player()                                   # the written dice still apply
    small.max_hp = small.hp = 60
    took, _ = death.attack(small)
    assert 17 <= took <= 39
    tough = Player()
    tough.max_hp = tough.hp = 500
    tough.CON = 30
    took, _ = death.attack(tough)
    assert took < int(round(floor_curve.DEATH_REAP_SHARE * 500))    # toughness still counts


def test_fenrir_is_worth_a_quest_and_abaddon_is_not_a_coin_flip():
    d = _defs()
    wolf = max(_mean(a['damage']) for a in d['fenrir_wolf']['attacks'])
    lord = max(_mean(a['damage']) for a in d['abaddon_destroyer']['attacks'])
    # Fenrir with the ribbon killed no one, so the Sandal saved nothing: he
    # now hits hard enough that both matter. Abaddon was taking half of
    # everyone who reached him with the altars.
    assert wolf >= 120, wolf
    assert lord <= 50, lord
    assert wolf > 2 * lord


def test_the_gate_bosses_keep_their_order_of_size():
    d = _defs()
    hp = [_mean(d[k]['hp']) for k in ('asterion_minotaur', 'medusa_gorgon', 'fafnir_dragon',
                                      'fenrir_wolf', 'abaddon_destroyer')]
    assert hp == sorted(hp)


# ------------------------------------------------- Phase 7: what the player sees

def test_the_sidebar_clock_is_the_clock_the_fight_will_get():
    p = Player()
    assert p.combat_clock() == 10
    p.add_effect('hasted', 5)
    assert p.combat_clock() == 12 or p.combat_clock() == 13        # x1.25
    q = Player()
    q.add_effect('confused', 5)
    assert q.combat_clock() < 10
    r = Player()
    r.grant_insight(6, 4)                                          # Michael, Guide My Hand
    assert r.combat_clock() == 16
    ui = open(os.path.join(ROOT, 'src', 'ui.py'), encoding='utf-8').read()
    assert 'player.combat_clock()' in ui and "get_quiz_timer('math')" not in ui


def test_a_weapon_card_says_which_sums_it_asks():
    import types
    import game_render
    w = types.SimpleNamespace(quiz_tier=3, class_mechanic=None, damage_types=['slash'],
                              two_handed=False, unique_effect=None)
    text = game_render.RenderMixin._kit_weapon_special(types.SimpleNamespace(), w, 5)
    assert text.startswith('Tier 3 Sums')


# ------------------------------------------- Death's chase, measured on real maps

def test_death_follows_up_the_stair_instead_of_waiting_in_ambush():
    """He was placed 6 tiles from the arrival stair: on the player's own
    path on 42% of floors, with 96% of his blows inside twelve turns."""
    assert floor_curve.DEATH_ARRIVAL_DELAY == {50: 6, 75: 5, 100: 4, 125: 3}
    assert floor_curve.death_arrival_delay(125) < floor_curve.death_arrival_delay(50)
    main = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    i = main.index('def _place_death_on_level')
    body = main[i:main.index('def _death_steps_onto_the_floor')]
    assert 'd._arrive_in = death_arrival_delay(' in body and 'range(6, 12)' not in body
    combat = open(os.path.join(ROOT, 'src', 'game_combat.py'), encoding='utf-8').read()
    assert 'self._death_steps_onto_the_floor()' in combat
    assert '(dm.x, dm.y) == (self.player.x, self.player.y)' in combat     # no safe square under him


def test_dead_mechanics_found_by_the_audit_are_wired():
    from monster import Monster
    d = _defs()
    for mid in ('blood_archon', 'cult_zealot'):
        m = Monster(dict(d[mid], id=mid), 1, 1)
        assert m.min_hit_chance == d[mid]['min_hit_chance']
        assert m._min_hit() == d[mid]['min_hit_chance']
    src = open(os.path.join(ROOT, 'src', 'combat.py'), encoding='utf-8').read()
    i = src.index("Cow King's Horns")
    assert 'if result.score >= 1:' in src[i:i + 600]              # never turns a miss into a hit
    import items
    assert items._material_resists({'resistances': ['fire', 'bludgeon']}) == {'fire': 0.75, 'blunt': 0.75}
    with open(os.path.join(ROOT, 'data', 'items', 'weapon.json'), encoding='utf-8') as f:
        w = json.load(f)
    assert 'medusa_gorgon' in w['harpe']['skip_chain_warmup_vs_tag']
    assert _mean(w['gram']['dragon_bonus_damage']) > 0.25 * w['gram']['base_damage']
    glam = next(x for x in items.load_items('weapon') if x.id == 'glamdring')
    assert {'goblin', 'goblinoid', 'orc'} <= set(glam.bonus_damage_vs_tag)
