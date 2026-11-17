"""Armour you choose, not just wear (winning-build plan 3.3, slice 4, 2026-11-13).

Brandon: "Ensure that kit armor defenses are IMPORTANT beyond AC; materials
can change weight and resistances, block certain monster attacks and status
effects... there should be a REAL choice to kit and armor, not just what has
the best AC", and "BALANCE armor and Dex (light vs heavy)... so that there
are many ways to play". This reverses the 3.3.2 rule that the material gives
"the weight and the wear, never protection".

  * The TEMPLATE sets the forms (plate turns an edge, mail parts under a
    point, quilting soaks a club): data/templates/armor `forms`.
  * The MATERIAL of the body armour sets the elements (iron carries the
    spark, leather burns, dragonscale sheds flame) and what it wards off
    (cold iron and fey glamour): data/materials/armor `protection`, `wards`.
  * The body armour's WEIGHT CLASS sets the dodge (full / half / none), the
    speed it costs until Strength pays it back (the defence model,
    2026-11-16: Dexterity gives no AC since), the footsteps (+0 / +1 / +2,
    metal +1) and a spell's cost in metal (x1 / x1.5 / x2; mithril casts
    freely).
  * The LOAD (the four tiers of 2026-11-16, tests/test_defence_model.py):
    Light over half the limit (a little less dodge), Heavy over 70% (half
    the dodge, slower), Burdened over 90% (no dodge, much slower),
    Overloaded past the limit (half speed).
  * A named piece's own resistances win; an old save's common armour takes
    its profile from its template and material.

Logic tests on the Player, the Monster and a real headless Game. Whether the
choice FEELS real is Brandon's play-test (plan section 6).
"""
import os
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content'))

import pygame  # noqa: E402
import pytest  # noqa: E402

import gear  # noqa: E402
import items  # noqa: E402
from player import Player  # noqa: E402

pygame.init()


def _wearing(tpl=None, mat=None, dex=10):
    p = Player()
    p.DEX = dex
    if tpl:
        p._apply_equip(items.instantiate_armor(tpl, mat))
    return p


def _hit(p, amount, kind):
    """What a blow of `kind` takes off a hero with plenty of health."""
    p.hp = p.max_hp = 500
    return p.take_damage(amount, kind)


# ------------------------------------------------------------ forms and elements

def test_mail_takes_more_from_a_spear_than_plate():
    mail = _wearing('chainmail', 'ring_iron')
    plate = _wearing('plate', 'ring_iron')
    naked = _wearing()
    assert _hit(mail, 40, 'pierce') == 46               # rings part under a point
    assert _hit(plate, 40, 'pierce') == 34              # a plate skids it aside
    assert _hit(naked, 40, 'pierce') == 40
    # ...and both turn an edge alike.
    assert _hit(mail, 40, 'slash') == _hit(plate, 40, 'slash') == 30


def test_padded_soaks_a_club():
    padded = _wearing('padded', 'linen')
    assert _hit(padded, 40, 'blunt') == 30
    assert _hit(_wearing(), 40, 'blunt') == 40
    assert _hit(_wearing('plate', 'chain_steel'), 40, 'blunt') == 40     # a hammer rings plate


def test_iron_conducts_lightning():
    assert _hit(_wearing('chainmail', 'ring_iron'), 40, 'lightning') == 50
    assert _hit(_wearing('leather', 'leather'), 40, 'lightning') == 40


def test_dragonscale_halves_fire_and_leather_burns():
    assert _hit(_wearing('scale', 'dragonscale'), 40, 'fire') == 20
    assert _hit(_wearing('leather', 'leather'), 40, 'fire') == 50
    assert _hit(_wearing('scale', 'dragonscale'), 40, 'cold') == 46     # the price: it stiffens


def test_only_the_body_armour_carries_its_material_and_the_tower_shield_its_form():
    p = Player()
    for tpl in ('leather', 'leather_cap', 'leather_boots', 'leather_gloves', 'leather_bracers'):
        p._apply_equip(items.instantiate_armor(tpl, 'leather'))
    assert gear.worn_factor(p, 'fire') == 1.25         # once, not five times
    p.shield = items.instantiate_shield('tower_shield', 'oak')
    assert gear.worn_factor(p, 'pierce') == pytest.approx(0.9)
    p.shield = items.instantiate_shield('buckler', 'oak')
    assert gear.worn_factor(p, 'pierce') == 1.0


def test_a_named_piece_keeps_its_own_resistances():
    lorica = items.make_item_by_id('armor', 'lorica_hamata_of_caesar')
    assert gear.piece_profile(lorica) == lorica.damage_resistances          # no mail x1.15
    assert gear.protection_line(lorica) == ''                              # its card says its own
    assert lorica.metal is True and gear.piece_weight_class(lorica) == 'medium'
    hide = items.make_item_by_id('armor', 'hide_of_nemean_lion')
    assert hide.metal is False and not gear.is_metal(hide)                  # material word: adamantine
    p = Player()
    p._apply_equip(lorica)
    assert p.spell_mp_cost(10) == 15


# ------------------------------------------------------------------ light vs heavy

def test_plate_has_the_ac_and_a_dex_hero_in_leather_the_dodge_and_the_speed():
    # The defence model (2026-11-16): AC from armour only, so plate always
    # out-armours leather; Dexterity is the dodge and the speed instead.
    leather = _wearing('leather', 'leather', dex=22)
    plate = _wearing('plate', 'chain_steel', dex=22)
    assert leather.get_ac() == 10 - 2
    assert plate.get_ac() == 10 - 7
    assert plate.get_ac() < leather.get_ac()                   # lower is better
    assert leather.dodge_chance() > 0 == plate.dodge_chance()
    assert leather.get_speed() > plate.get_speed()             # STR 10 in plate: its drag


def test_he_dodges_in_leather_and_not_in_plate():
    import defence
    per = defence.rules()['dodge_per_dex']
    leather = _wearing('leather', 'leather', dex=20)
    medium = _wearing('chain_shirt', 'chain_steel', dex=20)
    plate = _wearing('plate', 'chain_steel', dex=20)
    assert leather.dodge_chance() == pytest.approx(10 * per)
    assert medium.dodge_chance() == pytest.approx(5 * per)
    assert plate.dodge_chance() == 0.0


def test_a_slipped_blow_needs_the_dodge():
    from monster import Monster
    import json
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        d = json.load(f)['goblin']
    m = Monster(dict(d, id='goblin'), 5, 6)
    leather = _wearing('leather', 'leather', dex=50)
    plate = _wearing('plate', 'chain_steel', dex=50)
    for p in (leather, plate):
        p.x, p.y = 5, 5
    random.seed(4)
    slips = sum(m._slipped(leather, {'name': 'Claw'}) for _ in range(400))
    assert slips > 80                                           # the cap: 40% (defence.dodge_cap)
    assert not any(m._slipped(plate, {'name': 'Claw'}) for _ in range(200))


def test_heavy_armour_is_louder_and_metal_louder_still():
    import senses
    naked = senses.step_radius(_wearing())
    assert senses.step_radius(_wearing('leather', 'leather')) == naked
    assert senses.step_radius(_wearing('scale', 'dragonscale')) == naked + 1        # medium
    assert senses.step_radius(_wearing('scale', 'chain_steel')) == naked + 2        # medium metal
    assert senses.step_radius(_wearing('plate', 'chain_steel')) == naked + 3        # heavy metal
    assert senses.step_radius(_wearing('plate', 'mithril')) == naked + 2            # mithril is quiet


def test_sleepers_hear_the_plate():
    import sleepers
    leather = sleepers.factor(_wearing('leather', 'leather'), 'step')
    plate = sleepers.factor(_wearing('plate', 'chain_steel'), 'step')
    assert plate == pytest.approx(leather * 1.75)


def test_casting_in_steel_plate_costs_double_and_in_mithril_not():
    assert _wearing('plate', 'chain_steel').spell_mp_cost(10) == 20
    assert _wearing('chain_shirt', 'chain_steel').spell_mp_cost(10) == 15
    assert _wearing('plate', 'mithril').spell_mp_cost(10) == 10
    assert _wearing('scale', 'dragonscale').spell_mp_cost(10) == 10           # not metal
    assert _wearing('leather', 'leather').spell_mp_cost(10) == 10
    assert _wearing('chain_shirt', 'chain_steel').spell_mp_cost(3) == 5        # rounded up


# ------------------------------------------------------------------------ the load

def _weight(lb):
    it = items.instantiate_weapon('longsword', 'iron')
    it.weight = float(lb)
    return it


def test_the_load_takes_the_dodge_a_tier_at_a_time():
    import defence
    lr = defence.load_rules()
    p = _wearing('leather', 'leather', dex=20)        # 10 lb worn, limit 100
    full = p.dodge_chance()
    p.inventory.append(_weight(45))                    # 55: over half
    assert p.load_tier() == 'light'
    assert p.dodge_chance() == pytest.approx(full * lr['light']['dodge'])
    p.inventory.append(_weight(20))                    # 75: over 70%
    assert p.load_tier() == 'heavy'
    assert p.dodge_chance() == pytest.approx(full * lr['heavy']['dodge'])
    p.inventory.append(_weight(20))                    # 95: over 90%
    assert p.load_tier() == 'burdened'
    assert p.dodge_chance() == pytest.approx(full * lr['burdened']['dodge'])


def test_the_load_costs_speed_from_heavy_on():
    p = Player()
    p.inventory.append(_weight(60))
    assert p.load_tier() == 'light' and p.get_speed() == 10.0
    p.inventory.append(_weight(20))
    heavy = p.get_speed()
    assert p.load_tier() == 'heavy' and heavy < 10.0
    p.inventory.append(_weight(15))
    assert p.load_tier() == 'burdened' and p.get_speed() < heavy
    p.inventory.append(_weight(30))
    assert p.load_tier() == 'overloaded' and p.get_speed() == 5.0


def test_the_load_is_heard():
    import json
    import senses
    with open(os.path.join(ROOT, 'data', 'senses.json'), encoding='utf-8') as f:
        noise = json.load(f)['noise']
    p = Player()
    base = senses.step_radius(p)
    p.inventory.append(_weight(60))
    assert senses.step_radius(p) == base + noise['light']           # Light
    p.inventory.append(_weight(20))
    assert senses.step_radius(p) == base + noise['heavy']           # Heavy
    p.inventory.append(_weight(15))
    assert senses.step_radius(p) == base + noise['burdened']        # Burdened
    p.inventory.append(_weight(30))
    assert senses.step_radius(p) == base + noise['overloaded']      # Overloaded
    assert noise['light'] < noise['heavy'] < noise['burdened'] <= noise['overloaded']


# ----------------------------------------------------------- wards: riders stopped

def _monster(kind):
    import json
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        d = json.load(f)[kind]
    return Monster(dict(d, id=kind), 5, 6)


def test_cold_iron_turns_the_fair_folks_glamour():
    fey = _monster('changeling')
    assert fey.family == 'fair_folk'
    glamour = {'name': 'Glamour', 'type': 'magic', 'effect': 'confused', 'effect_chance': 1.0}
    iron = _wearing('chainmail', 'ring_iron')
    line = fey._apply_attack_effect(glamour, iron)
    assert 'cold iron' in line and 'glamour slides off' in line
    assert not iron.has_effect('confused')
    # Steel is not cold iron, and the iron does nothing against a goblin's blow.
    random.seed(1)
    assert 'cold iron' not in fey._apply_attack_effect(glamour, _wearing('chainmail', 'chain_steel'))
    assert gear.ward_against(iron, _monster('goblin'), 'confused') is None


def test_dragonscale_will_not_catch_fire():
    burn = {'name': 'Flame', 'type': 'fire', 'effect': 'burning', 'effect_chance': 1.0}
    p = _wearing('scale', 'dragonscale')
    line = _monster('goblin')._apply_attack_effect(burn, p)
    assert 'will not catch' in line and not p.has_effect('burning')


# ------------------------------------------------------------------- what he reads

def test_the_card_says_it_in_one_honest_line():
    mail = items.instantiate_armor('chainmail', 'ring_iron')
    assert gear.protection_line(mail) == (
        "Turns an edge: slash x0.75; parts under a point: pierce x1.15; "
        "conducts lightning x1.25; cold iron: fey glamour slides off")
    import defence
    fit = defence.fit_strength('heavy')
    assert gear.weight_line(mail) == (
        f"Heavy metal: no dodge or quickness, slower below Strength {fit}, footsteps +3, "
        f"spells cost x2 MP; rusts.")
    leather = items.instantiate_armor('leather', 'leather')
    assert gear.weight_line(leather) == "Light: full dodge and quickness; scorches."
    mithril = items.instantiate_armor('chain_shirt', 'mithril')
    assert 'spells at full cost' in gear.weight_line(mithril)
    assert 'never rusts' in gear.weight_line(mithril)
    assert gear.card_lines(items.instantiate_armor('leather_cap', 'leather')) == []


def test_the_spell_is_charged_what_the_menu_shows():
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(3)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_armour_spell__')
    g.state = STATE_PLAYER
    g.monsters = []
    p = g.player
    p._apply_equip(items.instantiate_armor('plate', 'chain_steel'))
    p.known_spells['cure_light_spell'] = 3
    p.max_mp = p.mp = 50
    g._invoke_spell('cure_light_spell')
    assert p.mp == 50 - 6                                 # 3 MP, doubled in steel plate


# ---------------------------------------------------------------------- old saves

def test_an_old_saves_common_armour_gains_its_profile():
    from main import Game
    from game_states import STATE_PLAYER
    from save_system import save_game, load_game, delete_save
    name = '__test_armour_old_save__'
    random.seed(3)
    screen = pygame.display.set_mode((1, 1))
    g = Game(screen, player_name=name)
    g.state = STATE_PLAYER
    g.monsters = []
    old = items.instantiate_armor('chainmail', 'ring_iron')
    # A piece from before: no template written down, the old flat material
    # resistance in its own dict, none of today's fields.
    for attr in ('template_basis', 'metal', 'quiet', 'casting_free', 'wards'):
        old.__dict__.pop(attr, None)
    old.damage_resistances = {'slash': 0.96}
    g.player.inventory.append(old)
    try:
        assert save_game(g)
        state = load_game(name)
        g2 = Game(screen, player_name=name)
        g2.load_state(state)
        piece = next(i for i in g2.player.inventory if getattr(i, 'id', '') == 'ring_iron_chainmail')
        assert piece.damage_resistances == {}
        assert piece.template_basis == 'chainmail'
        assert gear.piece_profile(piece) == {'slash': 0.75, 'pierce': 1.15, 'lightning': 1.25}
        assert gear.is_metal(piece) and gear.piece_wards(piece) == ['fey_glamour']
    finally:
        delete_save(name)


# ------------------------------------------------------------------------ the data

def test_every_body_template_has_its_forms_and_its_lore():
    tpls = items.load_templates('armor')
    for tid, t in tpls.items():
        if t.get('slot') != 'body':
            assert 'forms' not in t, tid
            continue
        forms = t.get('forms')
        assert forms, tid
        assert set(forms) <= set(gear.FORMS), tid
        assert all(0.5 <= v <= 1.25 for v in forms.values()), tid
        assert set(t.get('forms_words') or {}) == set(forms), tid
        assert t.get('forms_note'), tid
    # The plan's table.
    assert tpls['plate']['forms'] == {'slash': 0.75, 'pierce': 0.85}
    assert tpls['chainmail']['forms'] == {'slash': 0.75, 'pierce': 1.15}
    assert tpls['padded']['forms'] == {'slash': 0.9, 'blunt': 0.75}
    assert tpls['leather']['forms'] == {'slash': 0.9, 'blunt': 0.85}
    assert tpls['scale']['forms'] == {'slash': 0.8, 'pierce': 0.9}


def test_every_material_has_a_profile_and_a_price():
    """Plan section 6: every material file has a profile and a price for it.
    No material simply wins: a gift (anything under x1, quiet, free casting,
    a ward) comes with a price (something over x1, metal's clank and spell
    tax, real weight, wear, or the very bottom of the dungeon)."""
    import status_effects as se
    wards = gear.ward_rules()
    mats = items.load_materials('armor')
    assert len(mats) == 45
    for mid, m in mats.items():
        assert 'resistances' not in m and 'weaknesses' not in m, mid      # one source
        prot = m.get('protection')
        assert isinstance(prot, dict), mid
        assert all(0.4 <= float(v) <= 1.3 for v in prot.values()), mid
        assert set(m.get('protection_words') or {}) == set(prot), mid
        assert isinstance(m.get('metal'), bool), mid
        assert m.get('protection_note') and m.get('protection_price'), mid
        for w in m.get('wards') or ():
            assert w in wards, (mid, w)
        gift = (any(v < 1 for v in prot.values()) or m.get('quiet') or m.get('casting_free')
                or m.get('wards'))
        probe = types.SimpleNamespace(material=mid)
        price = (any(v > 1 for v in prot.values()) or m['metal']
                 or float(m.get('weight_mult', 1)) >= 1.3
                 or se._can_rust(probe) or se._can_scorch(probe)
                 or int(m.get('peak_floor', 0)) >= 85)
        assert not gift or price, mid
    assert mats['dragonscale']['protection']['fire'] == 0.5
    assert mats['ring_iron']['protection']['lightning'] == 1.25
    assert mats['leather']['protection']['fire'] == 1.25
    assert mats['mithril']['quiet'] and mats['mithril']['casting_free']


def test_every_named_body_armour_says_whether_it_is_metal():
    import json
    with open(os.path.join(ROOT, 'data', 'items', 'armor.json'), encoding='utf-8') as f:
        named = json.load(f)
    body = {k: v for k, v in named.items() if isinstance(v, dict) and v.get('slot') == 'body'}
    assert len(body) >= 17
    for k, v in body.items():
        assert isinstance(v.get('metal'), bool), k


def test_the_rules_are_in_the_data():
    r = gear.rules()
    assert 'dex_ac_cap' not in r['armour_weight']             # no Dexterity in AC (2026-11-16)
    assert r['armour_weight']['dodge_share'] == {'light': 1.0, 'medium': 0.5, 'heavy': 0.0}
    assert r['armour_weight']['casting_mult'] == {'light': 1.0, 'medium': 1.5, 'heavy': 2.0}
    assert (r['load']['light']['share'], r['load']['heavy']['share'],
            r['load']['burdened']['share']) == (0.5, 0.7, 0.9)
    assert r['defence']['armour_drag']['light'] == 0.0


def test_the_profile_pass_is_written_and_idempotent():
    import armour_profiles_2026_11 as pass_
    assert pass_.plan() == []
