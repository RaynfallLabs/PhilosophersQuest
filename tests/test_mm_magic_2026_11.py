"""MONSTERS AND MAGIC, slice G (2026-11-19): the wards, the monster gates, the
new spells, scrolls, potions, oils, wands, the prayer and the Sceptre.

Seeded and deterministic: every roll that matters is pinned (thac0, the
monster's to-hit, random seeds). Data-layer tests load the JSON and check the
mechanical fields; the engines are pure modules (src/wards.py,
src/attack_gates.py) tested directly; the handlers through a stub game built
on MagicMixin (whose base, MagicWardsMixin, carries them).
"""
import json
import os
import random
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import attack_gates  # noqa: E402
import status_effects  # noqa: E402
import wards  # noqa: E402
from game_magic import MagicMixin  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402
from spells import LEARNABLE_SPELLS, spell_reach  # noqa: E402


def _data(*p):
    with open(os.path.join(ROOT, 'data', *p), encoding='utf-8') as f:
        return json.load(f)


MONS = _data('monsters.json')

NEW_BOOKS = ['spellbook_galdr_of_loosing', 'spellbook_cockcrow', 'spellbook_sanctuary',
             'spellbook_elf_shot', 'spellbook_stayed_spear', 'spellbook_tacitas_seal',
             'spellbook_dionysus_vine', 'spellbook_shrink_the_earth', 'spellbook_bough_of_somnus',
             'spellbook_dulled_blades', 'spellbook_confusion_of_tongues',
             'spellbook_darkness_of_egypt', 'spellbook_pans_panic', 'spellbook_settled_strife',
             'spellbook_mist_of_manannan', 'spellbook_hush_of_the_feralia']
NEW_SCROLLS = ['scroll_of_the_lemuria', 'scroll_of_the_hamelin_piper', 'scroll_of_daniel',
               'scroll_of_the_psylli', 'scroll_of_the_heart_sutra', 'scroll_of_saint_martha',
               'scroll_of_the_udug_hul']
NEW_POTIONS = ['goatherds_coffee', 'nepenthe', 'oil_of_rue', 'fern_flower_tincture', 'moly',
               'theriac', 'water_of_epidaurus', 'charm_of_prometheus', 'water_of_the_styx']
NEW_WANDS = ['wand_of_unstringing', 'krotala_of_athena']


def mon(kind, x=5, y=5):
    m = Monster({**MONS[kind], 'id': kind}, x, y)
    m.thac0 = -100                      # every roll hits: what stops it is the ward
    m._slipped = lambda player, atk: False
    return m


def kind_of(family, pred=lambda d: True, named=False):
    import family_lore
    for k in family_lore.members(family):
        d = MONS.get(k)
        if not d or bool(d.get('is_boss') or d.get('is_mini_boss') or d.get('is_seal_demon')) != named:
            continue
        if pred(d):
            return k
    raise LookupError(family)


def hero():
    p = Player()
    p.x, p.y = 4, 5
    p.status_effects = {}
    return p


def melee(d):
    import guards
    return any(guards.delivery(a) in ('blow', 'bite', 'touch', 'grapple', 'sting', 'trample')
               for a in d.get('attacks') or ())


def ranged(d):
    import guards
    return any(guards.delivery(a) == 'ranged' for a in d.get('attacks') or ())


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def test_every_new_spellbook_teaches_a_real_spell_at_its_own_tier():
    books = _data('items', 'spellbook.json')
    unids = [b.get('unidentified_name') for b in books.values()]
    for bid in NEW_BOOKS:
        b = books[bid]
        sp = LEARNABLE_SPELLS[b['spell_id']]
        assert b['tier'] == sp['tier'] == b['quiz_tier'], bid
        assert b['mp_cost'] == sp['mp_cost'] and b['spell_name'] == sp['name'], bid
        assert (b['peak_floor'] - 1) // 20 + 1 == b['tier'], bid      # tier by depth
        assert unids.count(b['unidentified_name']) == 1, bid
        assert len(b['lore']) > 120, bid
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'items', bid + '.png')), bid


def test_every_new_spell_has_a_handler_and_a_plain_line():
    for sid in ('galdr_of_loosing_spell', 'cockcrow_spell', 'sanctuary_spell', 'elf_shot_spell',
                'stayed_spear_spell', 'tacitas_seal_spell', 'dionysus_vine_spell',
                'shrink_the_earth_spell', 'bough_of_somnus_spell', 'dulled_blades_spell',
                'confusion_of_tongues_spell', 'darkness_of_egypt_spell', 'pans_panic_spell',
                'settled_strife_spell', 'mist_of_manannan_spell', 'hush_of_the_feralia_spell'):
        sp = LEARNABLE_SPELLS[sid]
        assert sp['desc'] and '(' not in sp['desc'], sid
    assert spell_reach(LEARNABLE_SPELLS['shrink_the_earth_spell']) == 6
    # The flat hold ladder, fixed by lore: Paralyze (T4) holds longer than Hold Monster (T2).
    assert LEARNABLE_SPELLS['paralyze_spell']['duration'] > 8
    assert LEARNABLE_SPELLS['elf_shot_spell']['duration'] == 3


def test_scrolls_name_a_ward_that_exists_and_the_rites_keep_their_story():
    scrolls = _data('items', 'scroll.json')
    for sid in NEW_SCROLLS:
        s = scrolls[sid]
        assert (s['peak_floor'] - 1) // 20 + 1 == s['tier'], sid
        if s['effect'] == 'family_ward':
            assert wards.ward_spec(s['ward']), sid
        else:
            assert s['effect'] == 'family_rout' and s['family'] == 'vermin'
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'items', sid + '.png')), sid
    also = {k: v['ward_also'] for k, v in scrolls.items() if v.get('ward_also')}
    assert set(also) == {'scroll_of_protection', 'scroll_of_greater_protection',
                         'scroll_of_aegis', 'scroll_of_absolute_ward'}
    for sid, rows in also.items():
        for st, turns in rows:
            assert st in status_effects.EFFECT_INFO and turns > 0, (sid, st)
    assert scrolls['scroll_of_ward'].get('ward_also') is None


def test_potions_have_a_tier_by_depth_and_a_drink_line():
    import tier_census
    pots = _data('items', 'potion.json')
    for pid in NEW_POTIONS:
        p = pots[pid]
        assert p['tier'] in (1, 2, 3, 4, 5) and p.get('drink_line'), pid
        found = tier_census.found_floor(p)
        assert abs(tier_census.band(found) - p['tier']) <= 1, (pid, found)
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'items', pid + '.png')), pid
    assert pots['water_of_the_styx']['rare'] is True


def test_wands_and_the_sceptre():
    w = _data('items', 'wand.json')
    for wid in NEW_WANDS:
        assert w[wid]['effect'] in ('unstring_monster', 'family_rout')
        assert (w[wid]['peak_floor'] - 1) // 20 + 1 == w[wid]['tier']
    weap = _data('items', 'weapon.json')['sceptre_of_agamemnon']
    assert weap['is_unique'] and weap['quiz_tier'] == weap['tier'] == 3
    assert weap['effects']['status'] == 'silenced'
    assert set(weap['effects']['families']) == {'mortals', 'goblinkin'}


def test_every_ward_status_is_a_named_buff():
    reg = wards.status_registry()
    assert len(reg) >= 15
    for sid in reg:
        assert sid in status_effects.EFFECT_INFO and sid in status_effects.BUFFS, sid


# ---------------------------------------------------------------------------
# Family wards
# ---------------------------------------------------------------------------

def test_lemuria_keeps_the_restless_dead_off_until_struck():
    random.seed(1)
    p = hero()
    k = kind_of('restless_dead', melee)
    a, b = mon(k), mon(k, 6, 6)
    wards.grant(p, 'ward_lemuria', 15)
    hp0 = p.hp
    dmg, msg = a.attack(p)
    assert dmg == 0 and p.hp == hp0, msg
    # Struck, that one is no longer held off; the other still is.
    wards.hero_struck(p, a)
    for _ in range(20):
        if a.attack(p)[0] > 0:
            break
    assert p.hp < hp0
    hp1 = p.hp
    assert b.attack(p)[0] == 0 and p.hp == hp1
    # A new rite forgets the old breaks.
    p.status_effects.pop('ward_lemuria')
    wards.grant(p, 'ward_lemuria', 15)
    assert a.attack(p)[0] == 0


def test_a_named_foe_is_too_strong_for_a_melee_ward():
    p = hero()
    m = mon(kind_of('restless_dead', melee))
    m.is_mini_boss = True
    wards.grant(p, 'ward_lemuria', 15)
    atk = next(a for a in m.attacks if wards.is_melee(a))
    assert wards.blow_gate(p, m, atk) is None          # the blow goes on...
    assert wards.damage_mult(p, m) == 0.5              # ...half spent, once
    assert wards.damage_mult(p, m) == 1.0
    assert wards.blow_gate(p, m, atk) is None          # and the ward is broken for it


def test_psylli_keeps_a_serpents_poison_out():
    p = hero()
    m = mon(kind_of('serpents'))
    wards.grant(p, 'ward_psylli', 25)
    assert wards.rider_line(p, m, 'poisoned')
    assert wards.rider_line(p, m, 'feared') is None    # not its riders
    other = mon(kind_of('great_beasts'))
    assert wards.rider_line(p, other, 'poisoned') is None


def test_hoichi_hides_the_hero_from_ghosts_until_he_strikes_one():
    import senses
    p = hero()
    g = mon(kind_of('ghosts'))
    wards.grant(p, 'ward_hoichi', 20)
    assert senses._hidden(g, p, None)
    wards.hero_struck(p, g)
    assert not p.has_effect('ward_hoichi')
    assert not senses._hidden(g, p, None)


def test_martha_halves_dragons_named_or_not():
    p = hero()
    wards.grant(p, 'ward_martha', 25)
    d = mon(kind_of('dragons'))
    assert wards.damage_mult(p, d) == 0.5
    d.is_boss = True
    assert wards.damage_mult(p, d) == 0.5
    assert wards.damage_mult(p, mon(kind_of('great_beasts'))) == 1.0


# ---------------------------------------------------------------------------
# Missiles, mist, sanctuary, the Styx
# ---------------------------------------------------------------------------

def _shot(m):
    return next(a for a in m.attacks if wards.is_missile(a))


def test_the_missile_wards():
    p = hero()
    m = mon(kind_of('goblinkin', ranged), 9, 5)
    shot = _shot(m)
    assert wards.blow_gate(p, m, shot) is None
    wards.grant(p, 'missile_ward', 10)
    assert wards.blow_gate(p, m, shot)[0] == 0
    p.status_effects.pop('missile_ward')
    wards.grant(p, 'stayed_spear', 10)
    assert wards.blow_gate(p, m, shot)[0] == 0
    m.invisible = True                       # an archer he cannot see still finds him
    import unseen
    if unseen.concealed(m, p):
        assert wards.blow_gate(p, m, shot) is None
    p.status_effects.pop('stayed_spear')
    wards.grant(p, 'veiled', 10)
    assert wards.blow_gate(p, m, shot)[0] == 0          # 5 tiles off, in the mist
    m.x, m.y = 6, 5
    assert wards.blow_gate(p, m, shot) is None          # close enough to see


def test_sanctuary_ends_on_a_strike_and_not_for_the_hurt():
    p = hero()
    m = mon(kind_of('mortals', melee))
    atk = next(a for a in m.attacks if wards.is_melee(a))
    wards.grant(p, 'sanctuary', 8)
    assert wards.blow_gate(p, m, atk)[0] == 0
    assert wards.hostile_act(p)
    assert not p.has_effect('sanctuary')
    wards.grant(p, 'sanctuary', 8)
    wards.hero_struck(p, m)                  # a blow lands: sanctuary is over
    assert not p.has_effect('sanctuary')
    wards.grant(p, 'sanctuary', 8)
    assert wards.blow_gate(p, m, atk) is None           # he hurt this one


def test_the_styx_turns_a_seen_blow_and_an_unseen_one_finds_the_heel():
    p = hero()
    m = mon(kind_of('giants', melee))
    atk = next(a for a in m.attacks if wards.delivery(a) in ('blow', 'bite')
               and a.get('type', 'physical') in ('physical', 'blunt', 'slash', 'pierce'))
    wards.grant(p, 'styx_dipped', 6)
    assert wards.blow_gate(p, m, atk)[0] == 0
    m.invisible = True
    import unseen
    if unseen.concealed(m, p):
        assert wards.blow_gate(p, m, atk) is None
        assert wards.damage_mult(p, m) == 0.5


def test_free_action_wakeful_and_clear_sight_keep_their_statuses_off():
    p = hero()
    p.add_effect('free_action', 6)
    assert not p.add_effect('immobilized', 4)
    p.add_effect('wakeful', 10)
    assert not p.add_effect('sleeping', 4)
    assert p.add_effect('paralyzed', 2)                 # coffee is not a cure for paralysis
    p.add_effect('clear_sight', 10)
    assert not p.add_effect('hallucinating', 5)


def test_a_loosed_hero_is_not_dragged():
    import monster as monster_mod
    p = hero()
    assert monster_mod._loosed(p) is False
    p.add_effect('free_action', 6)
    assert monster_mod._loosed(p) is True


def test_all_round_ward_takes_the_swarm_off_a_pack():
    import packs
    p = hero()
    rats = [mon('giant_rat', 3, 5), mon('giant_rat', 5, 5), mon('giant_rat', 4, 4)]
    if packs.pack_of(rats[0]) is None or 'swarm' not in packs.tricks_of(rats[0]):
        pytest.skip('giant rats are not a swarming pack in this data')
    atk = rats[0].attacks[0]
    assert packs.blow_mult(rats[0], p, atk, rats)[0] > 1.0
    wards.grant(p, 'all_round_ward', 20)
    assert packs.blow_mult(rats[0], p, atk, rats)[0] == 1.0


# ---------------------------------------------------------------------------
# Monster gates
# ---------------------------------------------------------------------------

def _with_delivery(d, want):
    import guards
    return any(guards.delivery(a) == want for a in d.get('attacks') or ())


def test_a_silenced_voice_cannot_wail():
    k = next(k for k, d in MONS.items() if isinstance(d, dict) and _with_delivery(d, 'voice')
             and not (d.get('is_boss') or d.get('is_mini_boss')))
    m = mon(k)
    voice = next(a for a in m.attacks if wards.delivery(a) == 'voice')
    assert attack_gates.blocks_attack(m, voice) == ''
    assert attack_gates.inflict(m, 'silenced', 10) == 10
    assert attack_gates.blocks_attack(m, voice) == 'silenced'
    m.x, m.y = 9, 9                          # not beside the hero: no blow at all
    p = hero()
    new, stop = attack_gates.blow_gate(m, voice, p)
    assert stop is not None and stop[0] == 0


def test_a_silenced_summoner_comes_to_fight_and_the_mouthless_cannot_be_silenced():
    k = next(k for k, d in MONS.items() if isinstance(d, dict) and d.get('ai_pattern') == 'summoner')
    m = mon(k)
    assert not attack_gates.must_close(m)
    m.add_effect('silenced', 6)              # through Monster.add_effect: the gate's rules
    assert attack_gates.must_close(m) and not attack_gates.may_summon(m)
    ooze = mon(kind_of('oozes'))
    assert ooze.add_effect('silenced', 6) == 0


def test_a_named_foe_holds_a_gate_three_turns_then_steadies():
    m = mon(kind_of('dragons'))
    m.is_boss = True
    assert attack_gates.inflict(m, 'unstrung', 8) == 3
    m.status_effects['unstrung'] = 0
    assert attack_gates.inflict(m, 'unstrung', 8) == 0          # steadying
    m.status_effects['gate_grace'] = 0
    assert attack_gates.inflict(m, 'unstrung', 8) == 3


def test_unstrung_stops_missile_breath_and_gaze():
    m = mon(kind_of('dragons', lambda d: _with_delivery(d, 'breath')))
    breath = next(a for a in m.attacks if wards.delivery(a) == 'breath')
    attack_gates.inflict(m, 'unstrung', 8)
    assert attack_gates.blocks_attack(m, breath) == 'unstrung'
    assert attack_gates.blocks_attack(m, {'name': 'Stony Gaze', 'delivery': 'gaze'})
    if m.ai_pattern in ('ranged', 'dragon'):
        assert attack_gates.must_close(m)


def test_babbling_packs_forget_their_ways():
    import packs
    m = mon('giant_rat')
    if packs.pack_of(m) is None:
        pytest.skip('no pack')
    assert packs.in_pack(m)
    attack_gates.inflict(m, 'babbled', 12)
    assert not packs.in_pack(m) and packs.tricks_of(m) == []


# ---------------------------------------------------------------------------
# Potions, oils, the kitchen, the vines
# ---------------------------------------------------------------------------

def _potion(pid, buc='uncursed'):
    from items import make_item_by_id
    it = make_item_by_id('potion', pid)
    it.buc = buc
    return it


def test_the_ward_potions_clear_then_keep_off():
    from food_system import drink_potion
    p = hero()
    p.status_effects['confused'] = 5
    drink_potion(p, _potion('moly'))
    assert not p.has_effect('confused') and not p.add_effect('confused', 5)
    assert not p.add_effect('hallucinating', 5)
    p = hero()
    p.status_effects['petrifying'] = 4
    drink_potion(p, _potion('oil_of_rue'))
    assert not p.has_effect('petrifying') and p.has_effect('petrify_immune')
    p = hero()
    p.status_effects['poisoned'] = 4
    drink_potion(p, _potion('theriac'))
    assert not p.has_effect('poisoned') and not p.add_effect('poisoned', 4)
    assert p.status_effects['poison_resist'] == 80
    p = hero()
    drink_potion(p, _potion('goatherds_coffee', 'blessed'))
    assert p.status_effects['wakeful'] == 90
    p = hero()
    drink_potion(p, _potion('nepenthe', 'cursed'))
    assert p.status_effects['fear_immune'] == 25
    p = hero()
    drink_potion(p, _potion('charm_of_prometheus'))
    assert p.has_effect('fire_shield') and p.has_effect('shielded')
    p = hero()
    drink_potion(p, _potion('water_of_the_styx'))
    assert p.status_effects['styx_dipped'] == 6


def test_water_of_epidaurus_gives_back_what_was_drained():
    from food_system import drink_potion
    p = hero()
    con, wis = p.CON, p.WIS
    p.apply_stat_bonus('CON', -2)
    p.apply_stat_bonus('WIS', -1)
    status_effects.note_stat_drain(p, 'CON', 2)
    status_effects.note_stat_drain(p, 'WIS', 1)
    p.status_effects['diseased'] = 10
    random.seed(3)
    drink_potion(p, _potion('water_of_epidaurus'))
    assert (p.CON, p.WIS) == (con, wis) and not p.has_effect('diseased')
    assert not p.__dict__.get('drained')


def test_the_fern_flower_signals_the_game():
    from food_system import drink_potion
    assert '_treasure_sight' in drink_potion(hero(), _potion('fern_flower_tincture'))


def test_theriac_is_brewed_to_carry():
    import kitchen
    rec = _data('items', 'recipes.json')['brew_theriac']
    assert kitchen.makes_ref(rec) == ('potion', 'theriac')
    p = hero()
    p.inventory = []
    lines = kitchen.make_to_carry(p, rec)
    assert any(getattr(i, 'id', '') == 'theriac' for i in p.inventory), lines
    assert any('If drunk' in ln for ln in kitchen.carry_lines(rec))
    assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'items', rec['art'] + '.png'))


def test_conjured_vines_wither_when_their_turn_comes():
    import decor
    import hazards

    class D:
        pass
    d = D()
    assert decor.place_for(d, (3, 3), 'conjured_vine', 12)
    assert hazards.hazard_def('conjured_vine')['status'][0] == 'immobilized'
    assert not decor.place_for(d, (3, 3), 'conjured_vine', 20)    # one fixture a tile
    assert decor.expire(d, 11) == []
    assert decor.expire(d, 12) == [(3, 3)]
    assert decor.fixture_at(d, 3, 3) is None


# ---------------------------------------------------------------------------
# The prayer
# ---------------------------------------------------------------------------

def test_deliver_us_is_opened_by_karma_and_grows_with_the_chain():
    import prayers
    assert 'deliver_us' not in [p['id'] for p in prayers.available(2)]
    assert 'deliver_us' in [p['id'] for p in prayers.available(3)]
    assert prayers.deliver_us(0) == 0
    assert prayers.deliver_us(2) == 8
    assert prayers.deliver_us(9) == prayers.DELIVER_CAP
    assert prayers.deliver_us(2, desperate=True) == 10


# ---------------------------------------------------------------------------
# The handlers, through a stub game
# ---------------------------------------------------------------------------

class _D:
    def __init__(self, w=20, h=20):
        self.width, self.height = w, h
        self.tiles = [[1] * w for _ in range(h)]      # dungeon.FLOOR
        self.explored = set()

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        return self.in_bounds(x, y)


class _G(MagicMixin):
    def __init__(self):
        self.player = hero()
        self.player.INT = 10
        self.dungeon = _D()
        self.monsters, self.pets, self.ground_items = [], [], []
        self.visible = {(x, y) for x in range(20) for y in range(20)}
        self.dungeon_level, self.turn_count = 5, 100
        self.messages = []
        self._wand_override_target = None
        self._last_spell_crit = self._last_spell_anti_being = False

    def add_message(self, text, kind='info'):
        self.messages.append(text)

    def _on_monster_killed(self, m, **kw):
        pass

    def _refresh_fov(self):
        pass

    def _occupants(self, hero=True):
        return set()

    def _make_noise(self, *a, **kw):
        self.noise = a


def cast(g, sid, target=None):
    g._apply_spell_effect(LEARNABLE_SPELLS[sid], target)


def test_the_area_spells_lay_their_status_on_what_the_hero_sees():
    random.seed(5)
    g = _G()
    foes = [mon(kind_of('mortals', melee), 6, 5), mon(kind_of('goblinkin', melee), 7, 5)]
    g.monsters = foes
    cast(g, 'dulled_blades_spell')
    assert all(m.has_effect('weakened') for m in foes)
    cast(g, 'darkness_of_egypt_spell')
    assert all(m.has_effect('blinded') for m in foes)
    cast(g, 'hush_of_the_feralia_spell')
    assert all(m.has_effect('silenced') for m in foes)
    cast(g, 'confusion_of_tongues_spell')
    assert all(m.has_effect('babbled') for m in foes)


def test_settled_strife_takes_people_only_and_a_blow_ends_it():
    random.seed(2)
    g = _G()
    man = mon(kind_of('mortals', melee), 6, 5)
    beast = mon(kind_of('great_beasts', melee), 7, 5)
    g.monsters = [man, beast]
    cast(g, 'settled_strife_spell')
    assert man.has_effect('charmed') and not beast.has_effect('charmed')
    g._damage_by = 'hero'
    g._ward_hero_struck(man)
    assert not man.has_effect('charmed')


def test_pans_panic_reaches_four_steps():
    random.seed(4)
    g = _G()
    near = mon(kind_of('mortals', melee), 7, 5)
    far = mon(kind_of('mortals', melee), 12, 5)
    g.monsters = [near, far]
    cast(g, 'pans_panic_spell')
    assert near.has_effect('feared') and not far.has_effect('feared')


def test_the_self_wards_from_spells():
    g = _G()
    for sid, st in (('stayed_spear_spell', 'stayed_spear'), ('sanctuary_spell', 'sanctuary'),
                    ('mist_of_manannan_spell', 'veiled'), ('galdr_of_loosing_spell', 'free_action')):
        cast(g, sid)
        assert g.player.has_effect(st), sid
    g.player.status_effects['immobilized'] = 3
    cast(g, 'galdr_of_loosing_spell')
    assert not g.player.has_effect('immobilized')


def test_tacitas_seal_and_elf_shot_and_somnus():
    random.seed(6)
    g = _G()
    a = mon(kind_of('mortals', melee), 6, 5)
    b = mon(kind_of('mortals', melee), 7, 5)
    c = mon(kind_of('mortals', melee), 12, 12)
    g.monsters = [a, b, c]
    cast(g, 'tacitas_seal_spell', a)
    assert a.has_effect('silenced')
    cast(g, 'elf_shot_spell', c)
    assert 0 < c.status_effects.get('paralyzed', 0) <= 3
    cast(g, 'bough_of_somnus_spell', a)
    assert a.has_effect('sleeping') and b.has_effect('sleeping')


def test_dionysus_vine_holds_the_knot_and_grows_vines():
    import decor
    random.seed(7)
    g = _G()
    a = mon(kind_of('mortals', melee), 10, 10)
    g.monsters = [a]
    cast(g, 'dionysus_vine_spell', a)
    assert a.has_effect('immobilized')
    assert decor.fixture_at(g.dungeon, 10, 11) == 'conjured_vine'
    assert decor.expire(g.dungeon, g.turn_count + 12)


def test_shrink_the_earth_steps_to_a_seen_empty_tile_and_refuses_the_rest():
    g = _G()
    m = mon(kind_of('mortals', melee), 8, 5)
    g.monsters = [m]
    assert g._aimed_step_refused(8, 5)                  # someone there
    assert g._aimed_step_refused(15, 5)                 # too far
    g.visible.discard((7, 7))
    assert g._aimed_step_refused(7, 7)                  # not in sight
    assert g._aimed_step_refused(9, 6) == ''
    g._aimed_tile = (9, 6)
    cast(g, 'shrink_the_earth_spell')
    assert (g.player.x, g.player.y) == (9, 6)


def test_the_family_ward_scroll_and_the_pipers_tune():
    from items import make_item_by_id
    random.seed(8)
    g = _G()
    s = make_item_by_id('scroll', 'scroll_of_the_lemuria')
    s.buc = 'blessed'
    g._apply_scroll_effect(s)
    assert g.player.status_effects['ward_lemuria'] == 22
    k = kind_of('vermin', lambda d: True)
    rats = [mon(k, 6, 5), mon(k, 7, 5)]
    g.monsters = rats + [mon(kind_of('mortals', melee), 8, 5)]
    g._apply_scroll_effect(make_item_by_id('scroll', 'scroll_of_the_hamelin_piper'))
    assert all(r.has_effect('feared') for r in rats if not r.resists_control('feared'))
    assert not g.monsters[-1].has_effect('feared')


def test_the_protection_rites_keep_off_what_their_story_names():
    from items import make_item_by_id
    g = _G()
    g._apply_scroll_effect(make_item_by_id('scroll', 'scroll_of_greater_protection'))
    assert g.player.has_effect('shielded') and g.player.has_effect('missile_ward')
    assert g.player.has_effect('fear_immune')
    g = _G()
    s = make_item_by_id('scroll', 'scroll_of_aegis')
    s.buc = 'cursed'
    g._apply_scroll_effect(s)
    assert g.player.has_effect('shielded') and not g.player.has_effect('petrify_immune')


def test_the_wands():
    from items import make_item_by_id
    random.seed(9)
    g = _G()
    archer = mon(kind_of('goblinkin', ranged), 9, 5)
    g.monsters = [archer]
    g._wand_override_target = archer
    g._apply_wand_effect(make_item_by_id('wand', 'wand_of_unstringing'))
    assert archer.has_effect('unstrung')
    g._wand_override_target = None
    bird = mon(kind_of('birds'), 6, 5)
    g.monsters = [bird]
    g._apply_wand_effect(make_item_by_id('wand', 'krotala_of_athena'))
    assert bird.has_effect('feared') and g.noise == ('shout',)


def test_the_sceptre_calls_the_assembly_once_a_floor():
    from items import make_item_by_id
    g = _G()
    assert g._sceptre_power_rows() == []
    g.player.weapon = make_item_by_id('weapon', 'sceptre_of_agamemnon')
    rows = g._sceptre_power_rows()
    assert rows and rows[0][0] == 'sceptre_assembly' and rows[0][2] == 1
    g.player._sceptre_floor = g.dungeon_level
    assert g._sceptre_power_rows()[0][2] == 0


# ---------------------------------------------------------------------------
# The real game: the V menu, the tile aim, the strike hook, the tincture
# ---------------------------------------------------------------------------

def _game():
    import pygame
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    pygame.init()
    import items as items_mod
    from game_states import STATE_PLAYER
    from main import Game
    random.seed(5)
    items_mod.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1280, 720)), player_name='__test_mm_magic__')
    g.monsters = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def test_in_the_game_the_sceptre_is_a_power_and_the_strike_hook_is_set():
    import monster as monster_mod
    from items import make_item_by_id
    g = _game()
    assert monster_mod.HERO_STRUCK == g._ward_hero_struck
    g.player.weapon = make_item_by_id('weapon', 'sceptre_of_agamemnon')
    g._open_power_menu()
    assert any(row[0] == 'sceptre_assembly' for row in g._power_menu_list)
    # The hero's own blow on a warded family breaks the ward against it.
    m = mon(kind_of('restless_dead', melee), g.player.x + 1, g.player.y)
    g.monsters = [m]
    wards.grant(g.player, 'ward_lemuria', 15)
    g._damage_by = 'hero'
    m.take_damage(1)
    assert wards.blow_gate(g.player, m, next(a for a in m.attacks if wards.is_melee(a))) is None


def test_in_the_game_shrink_the_earth_aims_at_a_tile():
    from game_states import STATE_QUIZ, STATE_TARGET
    g = _game()
    g.player.max_mp = max(int(g.player.max_mp), 30)
    g.player.mp = full = g.player.max_mp
    g._invoke_spell('shrink_the_earth_spell')
    assert g.state == STATE_TARGET and g._pending_power == 'spell_shrink_the_earth_spell'
    # A spot it cannot reach: refused, the MP given back.
    g.target_cursor_x, g.target_cursor_y = g.player.x + 9, g.player.y
    g._confirm_power_target()
    assert g.state != STATE_QUIZ and g.player.mp == full
    # A seen floor tile two steps off: the quiz opens.
    spot = next((x, y) for (x, y) in sorted(g.visible)
                if max(abs(x - g.player.x), abs(y - g.player.y)) == 2 and not g._aimed_step_refused(x, y))
    g._invoke_spell('shrink_the_earth_spell')
    g.target_cursor_x, g.target_cursor_y = spot
    g._confirm_power_target()
    assert g.state == STATE_QUIZ and g._aimed_tile == spot


def test_in_the_game_the_fern_flower_marks_the_treasure():
    import pygame
    from items import make_item_by_id
    g = _game()
    pot = make_item_by_id('potion', 'fern_flower_tincture')
    g.player.inventory.append(pot)
    g._open_quaff_menu()
    g._quaff_sel = g.quaff_menu_items.index(pot)
    g._quaff_menu_input(pygame.K_RETURN)
    assert pot not in g.player.inventory
    assert hasattr(g, '_treasure_seen')


def test_the_qa_sampler_hands_over_the_new_magic():
    g = _game()
    g.player.qa_tools = True
    g._qa_magic_sampler()
    from game_wards import QA_SPELLS
    assert QA_SPELLS <= set(g.player.known_spells)
    ids = {getattr(i, 'id', '') for i in g.player.inventory}
    assert {'scroll_of_the_lemuria', 'water_of_the_styx', 'wand_of_unstringing',
            'sceptre_of_agamemnon'} <= ids
