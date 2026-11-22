"""The arsenal's tools (winning-build plan 2026-11-13, slice 5): coatings on
the wielded weapon, thrown flasks for damage, thrown weapons that meet a
weakness, Press or Guard, the two-hander's parry, and the named counters.

Brandon: a kid should "identify and learn about monsters, then strategically
find a way to exploit the weakness... throwing potions, targeting
weaknesses, sacrificing defense for damage based on monster... elemental
attacks and status attacks both ways".

Logic tests on the real data and the real rules (and a headless Game where
the path runs through it). Whether coating a mace before the werewolf or
pressing a skeleton FEELS right is Brandon's play-test: Claude cannot drive
Pygame.
"""
import json
import os
import pickle
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import affinity  # noqa: E402
import coatings  # noqa: E402
import combat  # noqa: E402
import counters  # noqa: E402
import floor_curve  # noqa: E402
import items  # noqa: E402
import stance  # noqa: E402
from items import instantiate_shield, instantiate_weapon, make_item_by_id  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402


def _load(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return json.load(f)


MONS = _load('data', 'monsters.json')
FLASKS = _load('data', 'items', 'flask.json')


def _mon(kind):
    return Monster({**MONS[kind], 'id': kind}, 0, 0)


def _hero(weapon=None, shield=None):
    p = Player()
    p.weapon = weapon
    p.shield = shield
    p.ranged_weapon = None
    p.armor_slots = [None] * 8
    p.inventory = []
    return p


def _flask(fid, n=1):
    it = make_item_by_id('flask', fid)
    it.count = n
    return it


@pytest.fixture(autouse=True)
def _clean():
    coatings.drain()
    affinity.drain()
    yield
    coatings.drain()
    affinity.drain()


# ---------------------------------------------------------------- coatings

def test_silver_dust_makes_a_steel_mace_strike_a_werewolf_as_silver_for_its_blows():
    ww = _mon('werewolf')
    mace = instantiate_weapon('mace', 'steel')
    p = _hero(mace)
    assert combat.weapon_type_multiplier(mace, ww) == (0.5, 1.0)      # it shrugs at steel
    dust = _flask('silver_dust')
    assert coatings.refusal(p, dust) == ''
    line = coatings.apply(p, dust)
    assert 'Silver Dust' in line and '12' in line
    assert combat.weapon_type_multiplier(mace, ww) == (0.5, 2.0)      # silver: the weak step
    assert coatings.weapon_card_lines(mace) and '12' in coatings.weapon_card_lines(mace)[0]
    blows = FLASKS['silver_dust']['coat']['blows']
    out = []
    for _ in range(blows):
        out = coatings.after_blow(p, ww, mace, 5)
    assert mace.coating is None
    assert out and 'wears off' in out[-1][0]
    assert combat.weapon_type_multiplier(mace, ww) == (0.5, 1.0)


def test_a_coating_lives_on_the_weapon_not_the_hero():
    ww = _mon('werewolf')
    mace = instantiate_weapon('mace', 'steel')
    axe = instantiate_weapon('battleaxe', 'steel')
    p = _hero(mace)
    coatings.apply(p, _flask('silver_dust'))
    p.weapon = axe                               # S: the axe from At Your Back
    assert coatings.coat_substance(axe) is None
    assert combat.weapon_type_multiplier(axe, ww)[1] == 1.0
    p.weapon = mace
    assert coatings.coat_substance(mace) == 'silver'
    # A copy of a coated weapon (a save, a trader's shelf) is spent on its own.
    clone = pickle.loads(pickle.dumps(mace))
    coatings.spend_blow(p, clone)
    assert clone.coating['blows'] == mace.coating['blows'] - 1


def test_a_coating_is_refused_where_it_would_add_nothing():
    # On a weapon the hero has identified: a refusal on one he has not would
    # name its metal or its blessing (bug bash WB-A12, test_bugbash_wb_a.py).
    silver = instantiate_weapon('mace', 'silver')
    silver.id_level = 5
    p = _hero(silver)
    assert 'already' in coatings.refusal(p, _flask('silver_dust'))
    blessed = instantiate_weapon('mace', 'steel')
    blessed.buc = 'blessed'
    blessed.id_level = 5
    assert 'already' in coatings.refusal(_hero(blessed), _flask('flask_of_holy_water'))
    assert coatings.refusal(_hero(None), _flask('silver_dust'))
    bow = instantiate_weapon('longbow', 'yew')
    assert coatings.refusal(_hero(bow), _flask('silver_dust'))
    # An acid flask coats nothing (it would eat the blade).
    assert coatings.coat_spec(_flask('flask_of_acid')) is None


def test_venom_does_nothing_to_the_poison_immune_and_poisons_the_living(monkeypatch):
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    sk = _mon('skeleton')                         # no blood to poison
    assert 'poisoned' in sk.status_immune
    blade = instantiate_weapon('longsword', 'steel')
    p = _hero(blade)
    coatings.apply(p, _flask('viper_venom'))
    out = coatings.after_blow(p, sk, blade, 6)
    assert not sk.has_effect('poisoned')
    assert out and 'does nothing' in out[0][0]
    assert coatings.after_blow(p, sk, blade, 6) == []          # said once a fight
    rat = _mon('giant_rat')
    coatings.after_blow(p, rat, blade, 6)
    assert rat.has_effect('poisoned')
    # A poison-resistant creature that could be poisoned refuses it too.
    zombie = _mon('zombie')
    assert 'poison' in zombie.resistances
    coatings.after_blow(p, zombie, blade, 6)
    assert not zombie.has_effect('poisoned')


def test_a_fire_coating_frightens_a_beast_that_fears_fire():
    wolf = _mon('dire_wolf_alpha')
    assert affinity.FEAR_OF_FIRE in wolf.status_weak
    blade = instantiate_weapon('longsword', 'steel')
    p = _hero(blade)
    coatings.apply(p, _flask('flask_of_fire_oil'))
    assert combat.weapon_type_multiplier(blade, wolf)[1] == 2.0          # weak to fire
    coatings.after_blow(p, wolf, blade, 4)
    assert wolf.has_effect('feared')


def test_the_blow_spends_the_coating_through_the_real_attack():
    """combat.player_attack's callback spends one blow of the coating."""
    from types import SimpleNamespace
    ww = _mon('werewolf')
    ww.hp = ww.max_hp = 10 ** 6
    mace = instantiate_weapon('mace', 'steel')
    p = _hero(mace)
    coatings.apply(p, _flask('silver_dust'))

    class _QE:
        def start_quiz(self, **kw):
            kw['callback'](SimpleNamespace(score=3, struck_early=False))

    got = {}
    combat.player_attack(p, ww, _QE(), lambda dmg, killed, chain, **kw: got.update(dmg=dmg))
    assert got['dmg'] > 0
    assert mace.coating['blows'] == FLASKS['silver_dust']['coat']['blows'] - 1


# ---------------------------------------------------------------- thrown flasks

def test_every_thrown_flask_is_sized_from_one_attack_at_its_own_depth():
    """LORE NOT FLOOR: real base damage, about one chain of a common weapon of
    its depth on a weak kind (floor_curve.ONE_ATTACK at 'sized_at', halved
    for the weak step), written in the data."""
    seen = 0
    for fid, d in FLASKS.items():
        t = d.get('throw')
        if not t:
            continue
        if t.get('counting'):
            # A handful of seed is thrown to hold a vampire while it counts
            # (2026-11-19, coatings._counting), not to hurt: no damage.
            assert t['damage'] == 0 and t['counting']['kinds'], fid
            continue
        seen += 1
        assert t['damage'] == int(round(floor_curve.one_attack(t['sized_at']) / 2)), fid
        assert t['damage_type'] in ('fire', 'holy', 'acid'), fid
    assert seen == 9


def test_holy_water_harms_the_dead_and_not_a_wolf():
    hw = _flask('flask_of_holy_water')
    z = _mon('zombie')
    z.hp = z.max_hp = 1000
    lines = coatings.throw_at(hw, z)
    assert z.hp == 1000 - FLASKS['flask_of_holy_water']['throw']['damage'] * 2   # weak x2
    assert 'bursts' in lines[0][0]
    wolf = _mon('dire_wolf_alpha')
    before = wolf.hp
    lines = coatings.throw_at(hw, wolf)
    assert wolf.hp == before and 'only water' in lines[0][0]
    # The holy water foraged at an altar is the same thing.
    foraged = make_item_by_id('ingredient', 'holy_water')
    assert coatings.throw_spec(foraged) == coatings.throw_spec(hw)
    assert coatings.coat_spec(foraged)['substance'] == 'holy'


def test_an_oil_flask_sets_burning_and_frightens_a_fear_of_fire_beast():
    oil = _flask('flask_of_fire_oil')
    wolf = _mon('dire_wolf_alpha')
    wolf.hp = wolf.max_hp = 1000
    lines = coatings.throw_at(oil, wolf)
    assert wolf.hp == 1000 - FLASKS['flask_of_fire_oil']['throw']['damage'] * 2   # weak to fire
    assert wolf.has_effect('burning') and wolf.has_effect('feared')
    assert any('alight' in t for t, _k in lines)
    notes = affinity.drain()
    assert any(k == affinity.WEAK for _m, k, _w in notes)
    assert any(k == affinity.FIRE_FRIGHT for _m, k, _w in notes)


def test_acid_pits_a_hide_and_stops_a_trolls_mending():
    acid = _flask('flask_of_acid')
    troll = _mon('troll')
    troll.hp = troll.max_hp = 1000
    coatings.throw_at(acid, troll)
    assert troll.hp == 1000 - FLASKS['flask_of_acid']['throw']['damage'] * 2
    assert troll.has_effect('armor_crack')
    assert troll.__dict__.get('_regen_blocked', 0) > 0


def test_a_thrown_flask_goes_by_the_throw_menu_and_its_own_path():
    g = _game()
    z = _place(g, 'zombie')
    z.hp = z.max_hp = 1000
    hw = _flask('flask_of_holy_water', 2)
    g.player.inventory.append(hw)
    g._open_throw_menu()
    assert hw in g.throw_menu_items
    assert dict(g._THROW_TABS)['Flasks'](hw)
    assert not dict(g._THROW_TABS)['Other'](hw)
    g._throw_potion = hw
    g._throw_reach = 5
    g.target_cursor_x, g.target_cursor_y = z.x, z.y
    g._confirm_throw_target()
    assert z.hp < 1000 and hw.count == 1


# ---------------------------------------------------------------- thrown weapons

def test_a_thrown_silver_dagger_counts_as_silver():
    g = _game()
    ww = _place(g, 'werewolf')
    ww.hp = ww.max_hp = 10 ** 6
    res = {}
    for mat in ('steel', 'silver'):
        dag = instantiate_weapon('dagger', mat)
        g.player.inventory.append(dag)
        base = g._get_weapon_throw_damage(dag)
        before = ww.hp
        g._throw_weapon(dag, ww, ww.x, ww.y)
        res[mat] = (before - ww.hp, base)
        affinity.drain()
    f, s = combat.weapon_type_multiplier(instantiate_weapon('dagger', 'silver'), ww)
    assert s == 2.0
    assert res['silver'][0] == max(1, int(round(res['silver'][1] * affinity.capped(f * s))))
    assert res['steel'][0] == max(1, int(round(res['steel'][1] * 0.5)))   # it resists a point


def test_a_thrown_coated_weapon_counts_as_coated():
    ww = _mon('werewolf')
    dag = instantiate_weapon('dagger', 'steel')
    dag.coating = {'id': 'silver_dust', 'name': 'Silver Dust', 'substance': 'silver', 'blows': 3}
    assert combat.weapon_type_multiplier(dag, ww)[1] == 2.0


# ---------------------------------------------------------------- Press or Guard

def test_press_and_guard_change_damage_and_ac_both_ways():
    goblin = _mon('goblin')
    goblin.hp = goblin.max_hp = 10 ** 6
    p = _hero(instantiate_weapon('longsword', 'steel'))
    plain_ac = p.get_ac()
    plain = combat.strike_damage(p, goblin, 4)
    p.stance = 'press'
    assert p.get_ac() == plain_ac + 2                         # 2 AC worse
    assert combat.strike_damage(p, goblin, 4) == round(plain * 1.3) or \
        abs(combat.strike_damage(p, goblin, 4) - plain * 1.3) <= 1
    p.stance = 'guard'
    assert p.get_ac() == plain_ac - 2                         # 2 AC better
    assert abs(combat.strike_damage(p, goblin, 4) - plain * 0.7) <= 1
    # The Strike Now preview is the same blow.
    assert combat.strike_preview(p, goblin, 4) == combat.strike_damage(p, goblin, 4)


def test_the_stance_key_steps_round_and_takes_a_turn():
    g = _game()
    t0 = g.turn_count
    seen = []
    for _ in range(3):
        _press(g, pygame.K_s, 'S')
        seen.append(g.player.stance)
    assert seen == ['press', 'guard', 'neutral']
    assert g.turn_count == t0 + 3
    assert any('press the attack' in t for t in _texts(g, 12))


def test_the_stance_numbers_are_data_and_old_saves_stand_neutral():
    d = _load('data', 'arsenal.json')['stance']
    assert (d['press']['damage'], d['press']['ac']) == (1.3, -2)
    assert (d['guard']['damage'], d['guard']['ac']) == (0.7, 2)
    p = Player()
    state = dict(p.__dict__)
    state.pop('stance', None)
    state.pop('ears_stopped', None)
    q = Player.__new__(Player)
    q.__setstate__(state)
    assert stance.of(q) == 'neutral' and q.ears_stopped is False


# ---------------------------------------------------------------- the parry

def test_a_two_hander_with_no_shield_parries_and_a_one_hander_does_not():
    gs = instantiate_weapon('greatsword', 'steel')
    p = _hero(gs)
    base = _hero(None).get_ac()
    assert stance.weapon_parry(gs) == 2
    assert p.get_ac() == base - 2
    assert any('Parry +2' in ln for ln in stance.card_lines(gs))
    assert stance.weapon_parry(instantiate_weapon('maul', 'steel')) == 1
    one = instantiate_weapon('longsword', 'steel')
    assert stance.weapon_parry(one) == 0 and _hero(one).get_ac() == base
    assert stance.card_lines(one) == []
    # A shield forced onto the arm (an old save) gives no parry with it.
    p.shield = instantiate_shield('mirror_shield', 'steel')
    assert stance.parry_ac(p) == 0


def test_a_high_tier_two_hander_parries_one_more():
    mats = items.load_materials('weapons')
    deep = next(mid for mid, m in sorted(mats.items()) if items.material_tier(m) >= 4
                and items.get_template('weapons', 'greatsword') and m.get('material_class') in
                ('metal', 'rare_metal', 'magical_metal'))
    gs = instantiate_weapon('greatsword', deep)
    assert gs.tier >= 4 and stance.weapon_parry(gs) == 3


# ---------------------------------------------------------------- named counters

def test_the_mirror_shield_turns_a_gaze_no_damage_no_rider():
    ms = instantiate_shield('mirror_shield', 'steel')
    assert counters.item_counters(ms) == ['gaze']
    p = _hero(instantiate_weapon('longsword', 'steel'), ms)
    hp = p.hp
    med = _mon('medusa')
    gaze = next(a for a in med.attacks if 'Gaze' in a['name'])
    dmg, msg = med._resolve_blow(gaze, p)
    assert dmg == 0 and 'gaze slides off' in msg
    assert p.hp == hp and not p.has_effect('paralyzed')
    # Without it the stone takes him, now and then.
    p.shield = None
    assert counters.blocks_gaze(p) is None


def test_the_mirror_shield_turns_a_floating_eyes_stare():
    eye = _mon('floating_eye')
    eye.x, eye.y = 1, 0
    p = _hero(None, instantiate_shield('mirror_shield', 'steel'))
    p.x, p.y = 0, 0
    hp = p.hp
    for _ in range(5):
        eye._gaze_cooldown = 0
        dmg, msg = eye.attack(p)
        assert dmg == 0 and not p.has_effect('paralyzed'), msg
    assert p.hp == hp


def test_the_cold_iron_charm_carried_stops_fey_glamour(monkeypatch):
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    ch = make_item_by_id('accessory', 'cold_iron_charm')
    assert ch.slot == 'none' and ch.identified
    cg = _mon('changeling')
    atk = dict(next(a for a in cg.attacks if a.get('effect') == 'confused'), effect_chance=1.0)
    p = _hero()
    p.inventory = [ch]
    out = cg._apply_attack_effect(atk, p)
    assert 'cold iron' in out.lower() and not p.has_effect('confused')
    # Not against what is not of the Fair Folk.
    assert counters.blocks_rider(p, _mon('goblin'), atk, 'confused') is None


def test_the_earplugs_stop_a_voice_and_deafen_him(monkeypatch):
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    plugs = make_item_by_id('accessory', 'beeswax_earplugs')
    p = _hero()
    p.inventory = [plugs]
    bans = _mon('banshee')
    wail = dict(next(a for a in bans.attacks if a['name'] == 'Death Wail'), effect_chance=1.0)
    assert counters.blocks_rider(p, bans, wail, 'paralyzed') is None      # not in yet
    assert not counters.deafened(p)
    assert 'quiet' in counters.toggle_ears(p)
    assert counters.ears_stopped(p) and counters.deafened(p)
    out = bans._apply_attack_effect(wail, p)
    assert 'wax' in out and not p.has_effect('paralyzed')
    # A blow is no voice: the plugs do nothing to a claw's rider.
    assert counters.blocks_rider(p, bans, {'name': 'Spirit Claw', 'effect': 'weakened'},
                                 'weakened') is None
    # Out of the pack, out of his ears.
    p.inventory = []
    assert not counters.ears_stopped(p)


def test_stopped_ears_hear_no_war_band_and_no_growl():
    g = _game()
    g.player.inventory.append(make_item_by_id('accessory', 'beeswax_earplugs'))
    g.player.ears_stopped = True
    leader = _place(g, 'goblin')
    leader._band_uid = 'b1'
    g.dungeon.band = {'id': next(iter(_load('data', 'war_bands.json')['bands'])), 'uid': 'b1',
                      'leader_kind': 'goblin'}
    n = len(g.msg_log.entries)
    g._announce_band()
    assert len(g.msg_log.entries) == n


def test_the_tells_name_the_counters():
    t = _load('data', 'tells.json')['effects']
    assert 'mirror shield' in t['gaze_paralyze']['counter']
    assert 'Aegis' not in t['gaze_paralyze']['counter']
    assert 'Wax' in t['confused']['counter'] and 'cold iron' in t['confused']['counter']
    assert 'wax' in t['feared']['counter']
    assert counters.names_for(_mon('medusa'), 'petrify_lethal') == ['gaze']    # stone, 2026-11-22
    assert counters.names_for(_mon('banshee'), 'feared') == ['voice']    # her wail is dread, 2026-11-22
    assert 'fey_glamour' in counters.names_for(_mon('changeling'), 'confused')


# ---------------------------------------------------------------- Kit Sense's hook

def test_kit_sense_names_the_coating_and_the_flask_that_serve():
    ww = _mon('werewolf')
    mace = instantiate_weapon('mace', 'steel')
    p = _hero(mace)
    dust, hw, acid = _flask('silver_dust'), _flask('flask_of_holy_water'), _flask('flask_of_acid')
    p.inventory = [acid, hw, dust]
    got = coatings.kit_sense_tools(p, ww)
    # Silver and holy serve a werewolf alike (it shrugs at a mace's head
    # either way): both coatings first, and no acid.
    assert {(dust, 'coat'), (hw, 'coat')} == set(got[:2])
    assert all(it is not acid for it, _w in got)
    z = _mon('zombie')
    got = coatings.kit_sense_tools(p, z)
    assert (hw, 'coat') in got and (dust, 'coat') in got        # the dead hate silver too
    gob = _mon('goblin')
    assert coatings.kit_sense_tools(p, gob) == []               # nothing it cannot bear
    troll = _mon('troll')
    p2 = _hero(None)
    p2.inventory = [acid]
    assert coatings.kit_sense_tools(p2, troll) == [(acid, 'throw')]


# ---------------------------------------------------------------- wiring

def test_every_flask_is_wired():
    import economy
    import renderer
    import traders
    for fid in FLASKS:
        it = make_item_by_id('flask', fid)
        assert isinstance(it, items.Flask) and it.identified, fid
        assert coatings.is_tool(it), fid
        p = renderer._resolve_item_sprite_path(fid)
        assert p and os.path.basename(p) == f"{fid}.png", fid
        assert economy.merchant_price(it, 10) > 0
        a, b = make_item_by_id('flask', fid), make_item_by_id('flask', fid)
        assert isinstance(a, items.Item._STACKABLE_CLASSES)
        assert a.id == b.id
    assert 'flask' in traders.SELLABLE_CLASSES
    for aid in ('beeswax_earplugs', 'cold_iron_charm'):
        p = renderer._resolve_item_sprite_path(aid)
        assert p and os.path.basename(p) == f"{aid}.png"
    p = renderer._resolve_item_sprite_path('steel_mirror_shield')
    assert p and 'mirror_shield' in os.path.basename(p)


def test_flasks_turn_up_in_the_floor_loot_by_depth():
    from dungeon import generate_dungeon, spawn_items
    found = {}
    random.seed(11)
    for lvl in (3, 8, 30, 70):
        for _ in range(4):
            d = generate_dungeon(level=lvl)
            for it in spawn_items(d.rooms, lvl, d, structures=False):
                if getattr(it, 'item_class', '') == 'flask':
                    found.setdefault(lvl, set()).add(it.id)
    assert found.get(3) or found.get(8)
    for lvl, ids in found.items():
        for fid in ids:
            assert FLASKS[fid]['min_level'] <= lvl, (lvl, fid)


def test_mother_wort_and_the_sutler_keep_a_flask_on_the_shelf():
    import traders
    for kind, lvl in (('apothecary', 12), ('sutler', 19), ('sutler', 39)):
        for seed in range(4):
            items.bind_unique_registry(set())
            stock = traders.build_stock(traders.kind_def(kind), lvl, random.Random(seed))
            assert any(getattr(i, 'item_class', '') == 'flask' for i in stock), (kind, lvl, seed)


def test_the_stall_counters_can_set_out_a_coating_or_a_named_counter():
    import domain_counters as dc
    cfg = dc.config()
    offers = [o for need in cfg['weak'].values() for o in need['offers']]
    flask_ids = {i for o in offers if o.get('class') == 'flask' for i in o['ids']}
    assert flask_ids <= set(FLASKS) and 'silver_dust' in flask_ids
    for key in ('gaze', 'voice', 'fey_glamour'):
        assert cfg['guard'][key]['offers']
    # Mother Wort, where the dead walk, offers holy water as her counter.
    d = dict(_load('data', 'traders.json')['traders']['apothecary'])
    rng = random.Random(1)
    got = []
    for lvl in range(2, 36):
        for ware, info in dc.stall_counters(d, lvl, rng):
            got.append((info['key'], getattr(ware, 'item_class', '')))
    assert ('holy', 'flask') in got or ('silver', 'flask') in got or ('fire', 'flask') in got
    # An armourer sets out a mirror shield where the gorgons are (a metal
    # shield is found from about floor 10: none can be made before).
    gaze_floors = [lvl for lvl in range(20, 100)
                   if any(s == 'guard' and k == 'gaze' and sh >= 0.04 for s, k, sh, _f in dc.needs(lvl))]
    assert gaze_floors
    s = dc._make({'gear': 'shield', 'template': 'mirror_shield'}, gaze_floors[0], random.Random(2))
    assert s is not None and counters.item_counters(s) == ['gaze']


def test_the_mirror_shield_is_a_metal_template_rarer_than_a_kite():
    import gear
    t = items.get_template('shields', 'mirror_shield')
    assert t['counters'] == ['gaze'] and t['base_ac_value'] == 1
    assert set(t['compatible_material_classes']) <= {'metal', 'rare_metal', 'magical_metal'}
    kite = items.get_template('shields', 'kite_shield')
    assert gear.template_weight(t, 30) < gear.template_weight(kite, 30)


def test_the_kit_offers_apply_and_shift_c_coats():
    g = _game()
    mace = instantiate_weapon('mace', 'steel')
    g.player.weapon = mace
    dust = _flask('silver_dust', 2)
    g.player.inventory.append(dust)
    acts = {a['id']: a for a in g._item_actions(dust, 'pack')}
    assert acts['apply']['label'] == 'Coat Weapon' and acts['apply']['enabled']
    t0 = g.turn_count
    _press(g, pygame.K_c, 'C')
    from game_states import STATE_QUAFF_MENU
    assert g.state == STATE_QUAFF_MENU and g._quaff_mode == 'coat'
    g._quaff_sel = 0
    g._quaff_menu_input(pygame.K_RETURN)
    assert coatings.coat_substance(mace) == 'silver' and dust.count == 1
    assert g.turn_count == t0 + 1
    plugs = make_item_by_id('accessory', 'beeswax_earplugs')
    g.player.inventory.append(plugs)
    acts = {a['id']: a for a in g._item_actions(plugs, 'pack')}
    assert acts['apply']['label'] == 'Put In'
    g._apply_item(plugs)
    assert counters.ears_stopped(g.player)
    assert any(lab == 'Ears Stopped' for lab, _c, _e in __import__('ui').arsenal_rows(g.player))


def test_the_qa_build_gets_the_arsenal():
    g = _game()
    g.player.qa_tools = True
    n = len(g.player.inventory)
    g._qa_arsenal_sampler()
    ids = {getattr(i, 'id', '') for i in g.player.inventory[n:]}
    assert set(FLASKS) <= ids and {'beeswax_earplugs', 'cold_iron_charm'} <= ids


# ---------------------------------------------------------------- helpers

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _game(name='__test_arsenal__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(5)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    g.visible = {(x, y) for y in range(g.dungeon.height) for x in range(g.dungeon.width)}
    return g


def _place(g, kind):
    m = _mon(kind)
    px, py = g.player.x, g.player.y
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        if g.dungeon.is_walkable(px + dx, py + dy):
            m.x, m.y = px + dx, py + dy
            break
    g.monsters.append(m)
    return m


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))


def _texts(g, n=8):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]
