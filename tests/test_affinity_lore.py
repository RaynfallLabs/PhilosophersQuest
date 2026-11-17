"""The monster lore pass (winning-build plan 2026-11-13, section 3.2;
slice 2: "Make the lore real in the data").

data/family_affinity.json says from each family's lore what it is weak to,
resists and shrugs off, and what its nature refuses or falls to easily;
tools/content/affinity_pass.py writes it into data/monsters.json; the steps
are data/affinity_rules.json (weak x2, resisted x0.5, shrugs off x0.25, no
full immunity, form x substance capped at x3).
"""
import json
import os
import random
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import affinity  # noqa: E402
import combat  # noqa: E402
from monster import Monster  # noqa: E402
from tools.content import affinity_pass as ap  # noqa: E402

FORMS = ('slash', 'pierce', 'blunt')


def _load(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(scope='module')
def mons():
    return _load('data', 'monsters.json')


@pytest.fixture(scope='module')
def prof():
    return _load('data', 'family_affinity.json')


def _mon(kind, mons):
    return Monster({**mons[kind], 'id': kind}, 0, 0)


class _W:
    def __init__(self, dts, mat='steel', buc='uncursed'):
        self.damage_types = list(dts) + ([mat] if mat not in ('iron', 'steel') else [])
        self.material = mat
        self.buc = buc


# ---------------------------------------------------------------- the rules
def test_the_steps_are_data_and_combat_reads_them():
    r = _load('data', 'affinity_rules.json')
    assert (r['weak'], r['resisted'], r['shrugs_off'], r['cap']) == (2.0, 0.5, 0.25, 3.0)
    assert (combat.WEAK_TO, combat.RESISTED, combat.SHRUGS_OFF, combat.AFFINITY_CAP) == (2.0, 0.5, 0.25, 3.0)
    assert r['shrugs_off'] > 0                        # no full immunity, ever


def test_a_skeleton_takes_double_from_a_mace_and_half_from_a_sword(mons):
    sk = _mon('skeleton', mons)
    assert combat.weapon_type_multiplier(_W(['blunt']), sk) == (2.0, 1.0)
    assert combat.weapon_type_multiplier(_W(['slash']), sk) == (0.5, 1.0)
    # a longsword cuts or thrusts, and the skeleton turns both
    assert combat.weapon_type_multiplier(_W(['slash', 'pierce']), sk)[0] == 0.5


def test_form_and_substance_multiply_but_are_capped_at_three(mons):
    sk = _mon('skeleton', mons)
    form, sub = combat.weapon_type_multiplier(_W(['blunt'], 'silver'), sk)
    assert (form, sub) == (2.0, 2.0)                  # the silver is substance, not a form
    assert affinity.capped(form * sub) == 3.0


def test_a_swarm_shrugs_off_a_sword_and_fire_is_its_answer(mons):
    sw = _mon('scarab_swarm', mons)
    assert combat.weapon_type_multiplier(_W(['slash']), sw)[0] == 0.25
    assert combat._damage_multiplier(['fire'], sw) == 2.0
    assert affinity.kind_of(0.25) == affinity.SHRUGS_OFF
    assert affinity.kind_of(0.5) == affinity.RESISTED


def test_spells_take_the_same_steps(mons):
    fe = _mon('fire_elemental', mons)
    assert combat._damage_multiplier(['fire'], fe) == 0.25        # living fire shrugs off fire
    assert combat._damage_multiplier(['cold'], fe) == 2.0
    hits = []
    affinity.drain()
    fe.take_damage(40, 'fire')
    hits = affinity.drain()
    assert hits and hits[0][1] == affinity.SHRUGS_OFF


def test_blessed_holy_is_for_the_unholy_only(mons):
    bear = _mon('cave_bear', mons)
    wight = _mon('wight', mons)
    blessed = _W(['slash'], buc='blessed')
    assert combat.weapon_type_multiplier(blessed, bear)[1] == 1.0
    assert combat.weapon_type_multiplier(blessed, wight)[1] == 2.0


def test_demons_are_no_longer_weak_to_silver_by_tag_but_devils_are(mons):
    imp = _mon('imp', mons)
    devil = _mon('bearded_devil', mons)
    silver = _W(['slash'], 'silver')
    assert combat.weapon_type_multiplier(silver, imp)[1] == 1.0
    assert combat.weapon_type_multiplier(silver, devil)[1] == 2.0
    # and the fair folk carry iron in their own weaknesses now
    assert 'iron' in mons['redcap']['weaknesses']


# ------------------------------------------------------------- the data
def test_every_family_has_a_written_profile_with_lore_and_source(mons, prof):
    fams = set(_load('data', 'monster_families.json')['families']) | {m['family'] for m in mons.values()}
    for fid in fams:
        p = prof['families'].get(fid)
        assert p is not None, fid
        assert len(p.get('lore', '')) > 20 and len(p.get('source', '')) > 5, fid
    for section in ('groups', 'kinds', 'tag_rules'):
        for key, p in prof[section].items():
            assert len(p.get('lore', '')) > 10 and len(p.get('source', '')) > 3, (section, key)
    for key in ('lore', 'source'):
        assert prof['unholy'][key]


def test_profiles_name_real_kinds_and_states(mons, prof):
    seen = {}
    for gid, g in prof['groups'].items():
        for k in g['kinds']:
            assert k in mons, (gid, k)
            assert k not in seen, f"{k} is in {seen.get(k)} and {gid}"
            seen[k] = gid
    for k in list(prof['kinds']) + list(prof['unholy']['cursed']):
        assert k in mons, k
    for layer in list(prof['families'].values()) + list(prof['groups'].values()) + list(prof['kinds'].values()):
        for f, st in (layer.get('form') or {}).items():
            assert f in FORMS and st in ap.STATES, (f, st)


def test_monsters_json_is_what_the_pass_writes(mons, prof):
    """Run tools/content/affinity_pass.py --write after changing a profile
    or adding a kind by hand."""
    for kind, m in mons.items():
        want = ap.resolve(kind, m, prof)
        for key, val in want.items():
            assert m.get(key) == val, (kind, key, m.get(key), val)
        assert all(a.get('type') != 'physical' for a in m['attacks']), kind


def test_no_type_is_both_weak_and_resisted(mons):
    for kind, m in mons.items():
        w, r, s = set(m['weaknesses']), set(m['resistances']), set(m['shrugs_off'])
        assert not (w & r or w & s or r & s), kind
        assert not set(m['status_immune']) & set(m['status_weak']), kind


def test_holy_weakness_only_on_the_unholy(mons, prof):
    for kind, m in mons.items():
        if 'holy' in m['weaknesses']:
            assert ap.is_unholy(kind, m, prof), kind
    assert sum(1 for m in mons.values() if 'holy' in m['weaknesses']) < 230


def test_named_foes_keep_their_quests(mons):
    ab = mons['abaddon_destroyer']
    assert {'slash', 'blunt'} <= set(ab['resistances']) and 'holy' in ab['weaknesses']
    assert ab['damage_ward'] > 0
    assert 'pierce' in mons['fafnir_dragon']['weaknesses']            # stabbed from below
    assert {'slash', 'blunt'} <= set(mons['fafnir_dragon']['resistances'])
    assert 'slash' in mons['medusa_gorgon']['weaknesses']             # the harpe
    assert 'pierce' in mons['asterion_minotaur']['weaknesses']
    assert 'fire' in mons['fenrir_wolf']['weaknesses']


# A spell of this element can be learned from this tier (spells.py), and a
# tier from this floor (the plan: T1 floor 1, T2 15, T3 35, T4 55, T5 75).
TIER_FLOOR = {1: 1, 2: 15, 3: 35, 4: 55, 5: 75}
SPELL_ELEMENTS = {'fire': 'fire', 'cold': 'cold', 'lightning': 'lightning', 'acid': 'acid'}


def _element_floor() -> dict:
    from spells import LEARNABLE_SPELLS
    out = {}
    for s in LEARNABLE_SPELLS.values():
        el = SPELL_ELEMENTS.get(s.get('spell_family'))
        if el:
            out[el] = min(out.get(el, 99), TIER_FLOOR[int(s['tier'])])
    return out


def _counters(kind, m, prof, materials, el_floor) -> list:
    pk = int(m['peak_floor'])
    tags = set(m['tags'])
    out = []
    for f in FORMS:
        if f in m['weaknesses']:
            out.append(f"a {f} weapon (from floor 1)")
    for mid, mat in materials.items():
        eff = set(mat.get('effective_against') or ())
        if int(mat.get('peak_floor', 99)) <= pk and (eff & tags or mid in m['weaknesses']):
            out.append(f"{mid} (peak floor {mat['peak_floor']})")
    for el, fl in el_floor.items():
        if el in m['weaknesses'] and fl <= pk:
            out.append(f"{el} spell (floor {fl})")
    if 'holy' in m['weaknesses'] and ap.is_unholy(kind, m, prof):
        out.append('a blessing')
    return out


def test_fairness_gate_every_lock_has_a_key_above_it(mons, prof):
    """A kind that shrugs off a form, or resists all three, has a counter
    the hero can have by its peak floor: a form it is weak to, a weapon
    material whose effective_against covers it (material peak floor at or
    above), an element a spell of a reachable tier carries, or a blessing
    for the unholy."""
    import glob
    materials = {}
    for path in glob.glob(os.path.join(ROOT, 'data', 'materials', 'weapons', '*.json')):
        with open(path, encoding='utf-8') as f:
            mat = json.load(f)
        materials[mat.get('id') or os.path.splitext(os.path.basename(path))[0]] = mat
    el_floor = _element_floor()
    # Acid Splash (tier 1, 2026-11-16) put acid in reach from floor 1, as
    # fire, cold and lightning already were.
    assert el_floor == {'fire': 1, 'cold': 1, 'lightning': 1, 'acid': 1}
    locked = []
    for kind, m in mons.items():
        hard = set(m['resistances']) | set(m['shrugs_off'])
        if not (set(m['shrugs_off']) & set(FORMS) or set(FORMS) <= hard):
            continue
        if not _counters(kind, m, prof, materials, el_floor):
            locked.append((kind, m['peak_floor'], m['resistances'], m['shrugs_off'], m['weaknesses']))
    assert not locked, locked


# --------------------------------------------------------------- status
def test_the_mindless_do_not_know_fear(mons):
    golem = _mon('clay_golem', mons)
    assert golem.add_effect('feared', 5) == 0
    assert not golem.has_effect('feared')
    line = affinity.status_line('immune', 'feared', golem)
    assert ('fear' in line or 'frighten' in line) and 'golem' in line.lower()


def test_the_dead_do_not_sleep_or_choke_on_poison(mons):
    z = _mon('zombie', mons)
    assert z.add_effect('sleeping', 5) == 0 and z.add_effect('poisoned', 5) == 0
    assert z.resists_control('charmed')
    # ...but they can still be turned (Turn the Dead) and their own rest holds
    assert z.add_effect('feared', 3) > 0


def test_status_weak_lasts_half_again_and_named_foes_keep_their_cap(mons):
    drake = _mon('drake_fire', mons)
    assert 'sleeping' in drake.status_weak            # Medea's song
    assert drake.add_effect('sleeping', 10) == 15
    fafnir = _mon('fafnir_dragon', mons)
    assert fafnir.add_effect('sleeping', 10) == 2     # NAMED_FOE_CONTROL_CAP


def test_status_weak_skips_a_big_foes_resist_roll(mons, monkeypatch):
    from game_magic import MagicMixin

    class _G:
        def _boss_resist_cc(self, target, duration):
            return 0, True                            # a big foe always throws it off
    g = _G()
    fafnir = _mon('fafnir_dragon', mons)
    got, _why = MagicMixin._inflict(g, fafnir, 'sleeping', 6)
    assert got == 2                                   # no roll; capped
    golem = _mon('clay_golem', mons)
    got, why = MagicMixin._inflict(g, golem, 'feared', 6)
    assert got == 0 and ('fear' in why or 'frighten' in why)
    wolf = _mon('dire_wolf_alpha', mons)
    got, why = MagicMixin._inflict(g, wolf, 'slowed', 6)
    assert got == 0 and why == ''                     # thrown off: the caller's own line


def test_poison_ticks_respect_poison_resistance(mons):
    base = dict(mons['giant_rat'], id='giant_rat')
    plain = Monster(dict(base, resistances=[], weaknesses=[]), 0, 0)
    tough = Monster(dict(base, resistances=['poison'], weaknesses=[]), 0, 0)
    for m in (plain, tough):
        m.max_hp = m.hp = 400
        m.add_effect('poisoned', 3)
        m.tick_effects()
    lost_plain = plain.max_hp - plain.hp
    lost_tough = tough.max_hp - tough.hp
    assert lost_plain > 0 and lost_tough == lost_plain // 2


def test_fire_puts_a_beast_to_flight_and_stops_a_troll_healing(mons):
    wolf = _mon('dire_wolf_alpha', mons)
    assert 'fear_of_fire' in wolf.status_weak
    affinity.drain()
    wolf.take_damage(3, 'fire')
    assert wolf.has_effect('feared')
    assert any(k == affinity.FIRE_FRIGHT for _m, k, _w in affinity.drain())
    troll = _mon('troll', mons)
    troll.hp = troll.max_hp - 50
    troll.take_damage(3, 'acid')
    hp = troll.hp
    troll.tick_effects()
    assert troll.hp == hp                             # the acid stopped the wound closing
    # a kind that resists fire does not fear it
    assert 'fear_of_fire' not in mons['winter_wolf']['status_weak'] or 'fire' not in mons['winter_wolf']['resistances']


# ------------------------------------------------------------ typed attacks
def test_every_plain_attack_has_a_form(mons):
    form = ap.attack_form
    assert form({'name': 'Bite', 'delivery': 'bite'}) == 'pierce'
    assert form({'name': 'Claw', 'delivery': 'blow'}) == 'slash'
    assert form({'name': 'Slam', 'delivery': 'blow'}) == 'blunt'
    assert form({'name': 'Tail Lash', 'delivery': 'sting'}) == 'blunt'
    assert form({'name': 'Tail Spike', 'delivery': 'sting'}) == 'pierce'
    assert form({'name': 'Gore', 'delivery': 'trample'}) == 'pierce'
    assert form({'name': 'Trample', 'delivery': 'trample'}) == 'blunt'
    assert form({'name': 'Battleaxe', 'delivery': 'blow'}) == 'slash'
    assert not [k for k, m in mons.items() for a in m['attacks'] if a['type'] == 'physical']


def test_a_typed_blow_is_still_a_blow_to_the_hero():
    from player import Player
    p = Player()
    p.add_effect('shielded', 5)
    hp = p.hp
    got = p.take_damage(20, 'slash')
    assert got <= 10 and p.hp == hp - got             # the shield halves a cut as it did a 'physical' blow


# ---------------------------------------------------------------- lines
def test_shrugs_off_has_its_own_lines():
    lines = affinity.lines()
    for pool in ('shrugs_off', 'shrugs_off_many', 'fire_fright'):
        assert len(lines[pool]) >= 2, pool
    for eff in ('feared', 'charmed', 'sleeping', 'poisoned', 'default'):
        assert lines['status_immune'][eff]
    assert all('they' not in s.lower().split()[:1] for s in lines['shrugs_off'])


def test_an_old_save_monster_takes_its_kinds_lists(mons):
    m = _mon('skeleton', mons)
    m.__dict__.pop('_affinity_pass')
    m.resistances, m.weaknesses = ['pierce'], ['blunt', 'holy']
    m.__dict__.pop('shrugs_off', None)
    assert affinity.refresh_from_data(m)
    assert m.resistances == mons['skeleton']['resistances']
    assert m.status_immune == mons['skeleton']['status_immune']
    assert not affinity.refresh_from_data(m)          # once


# ------------------------------------------------------------------ rust
class _Item:
    def __init__(self, material, item_class='weapon', enchant=0, **kw):
        self.material = material
        self.item_class = item_class
        self.enchant_bonus = enchant
        self.name = self.unidentified_name = f"{material} thing"
        self.identified = True
        self.id_level = 5
        self.special_properties = kw.get('special_properties', {})
        self.slot = kw.get('slot', 'body')


def test_wear_rules_read_the_material_files():
    from status_effects import _can_rust, _can_scorch, _can_corrode
    for mat in ('canvas', 'cured_leather_armor', 'boiled_leather_armor', 'studded_leather', 'spider_silk',
                'elven_silk', 'oak', 'ash', 'leather', 'bronze', 'silver', 'mithril', 'adamantine'):
        assert not _can_rust(_Item(mat)), mat
    for mat in ('iron', 'steel', 'chain_steel', 'ring_iron', 'cold_iron', 'damascus_steel'):
        assert _can_rust(_Item(mat)), mat
    assert _can_scorch(_Item('canvas')) and _can_scorch(_Item('oak'))
    assert not _can_scorch(_Item('dragonhide_armor')) and not _can_scorch(_Item('iron'))
    assert not _can_corrode(_Item('hardened_gold')) and _can_corrode(_Item('leather'))


def _hero_with(weapon=None, armour=None):
    from player import Player
    p = Player()
    p.weapon = weapon
    p.armor_slots = [armour] if armour else []
    p.shield = None
    p.ranged_weapon = None
    return p


def test_rust_takes_a_plus_off_worn_steel_but_never_off_leather():
    from status_effects import rust_worn_gear
    sword = _Item('steel', enchant=2)
    p = _hero_with(weapon=sword)
    msg, kind = rust_worn_gear(p, None, rng=random.Random(1))
    assert sword.enchant_bonus == 1 and 'rust' in msg.lower() and kind == 'danger'
    p2 = _hero_with(weapon=_Item('oak'))
    assert rust_worn_gear(p2, None) is None


def test_a_rustproof_wearer_keeps_rust_off_everything():
    from status_effects import rust_worn_gear
    sword = _Item('steel', enchant=2)
    cloak = _Item('silk', item_class='armor', special_properties={'rustproof_wearer': True}, slot='cloak')
    p = _hero_with(weapon=sword)
    p.armor_slots = [cloak]
    assert p.is_rustproof()
    msg, kind = rust_worn_gear(p, None)
    assert sword.enchant_bonus == 2 and kind == 'success' and 'keeps the rust' in msg


def test_the_rust_monsters_feelers_really_rust(mons, monkeypatch):
    atk = mons['rust_monster']['attacks'][0]
    assert atk['effect'] == 'rust'
    rm = _mon('rust_monster', mons)
    sword = _Item('steel', enchant=1)
    p = _hero_with(weapon=sword)
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    out = rm._apply_attack_effect(dict(atk, effect_chance=1.0), p)
    assert sword.enchant_bonus == 0 and 'feelers' in out


def test_a_uniques_own_bane_is_its_substance(mons):
    imp = _mon('imp', mons)
    bane = _W(['slash'], 'adamantine')
    bane.is_unique = True
    bane.effective_against = ['demon']
    assert combat.weapon_type_multiplier(bane, imp) == (1.0, 2.0)
    bane.effective_against = ['giant']
    assert combat.weapon_type_multiplier(bane, imp) == (1.0, 1.0)


def test_the_bestiary_page_names_what_it_shrugs_off_and_refuses(mons):
    got = dict(affinity.page_lines(mons['scarab_swarm']))
    assert got['shrugs_off'] == 'Shrugs Off: Slash, Pierce'
    assert 'Paralysis' in got['immune']
    assert affinity.page_lines(mons['goblin']) == []
    assert 'Fear of Fire' in dict(affinity.page_lines(mons['dire_wolf_alpha']))['easily']


def test_an_old_save_monsters_plain_blows_take_their_form(mons):
    z = _mon('zombie', mons)
    z.__dict__.pop('_affinity_pass')
    z.attacks = [dict(a, type='physical') for a in z.attacks]
    assert affinity.refresh_from_data(z)
    assert [a['type'] for a in z.attacks] == [a['type'] for a in mons['zombie']['attacks']]
    assert all(a['type'] != 'physical' for a in z.attacks)
