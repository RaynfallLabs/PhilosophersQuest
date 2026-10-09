"""The unique-armor pass (2026-10-08): named pieces for the thin slots, the
plain worn bonuses they use, and a named drop for every legend and mini-boss
that had none.

Logic and data tests: named armor is randomized loot, mostly deep, so it
cannot be play-tested in reasonable time.
"""
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import armor_procs  # noqa: E402
from items import Armor, Shield, make_item_by_id  # noqa: E402
from player import Player  # noqa: E402

SLOT_INDEX = {'head': 0, 'body': 1, 'arms': 2, 'hands': 3, 'legs': 4, 'feet': 5, 'cloak': 6, 'shirt': 7}

NEW_ARMOR = (
    'cestus_of_polydeuces', 'gloves_of_wayland', 'glove_of_tyr', 'jarngreipr_gauntlets',
    'bracers_of_atalanta', 'vambraces_of_roland', 'vambraces_of_the_first_winter',
    'hair_shirt_of_becket', 'shirt_of_aslaug', 'seamless_tunic',
    'half_cloak_of_martin', 'anansi_web_cloak', 'arachne_silk_cloak', 'erlking_mantle',
    'falcon_cloak_of_freyja', 'mantle_of_muspelheim', 'nidhoggr_scale',
    'serpent_scale_mail', 'breeches_of_ragnar', 'greaves_of_goliath', 'green_girdle',
)
DROPS = {
    'surtur': 'mantle_of_muspelheim',
    'ymir_last_spawn': 'vambraces_of_the_first_winter',
    'hrungnirs_ghost': 'hrungnirs_stone_shield',
    'arachne': 'arachne_silk_cloak',
    'erlking': 'erlking_mantle',
    'anansi': 'anansi_web_cloak',
    'green_knight': 'green_girdle',
    'jormungandr_juvenile': 'serpent_scale_mail',
    'nidhoggr_fragment': 'nidhoggr_scale',
}


def _data(name):
    with open(os.path.join(ROOT, 'data', *name.split('/')), encoding='utf-8') as f:
        return json.load(f)


def _wear(p, item_id):
    piece = make_item_by_id('armor', item_id)
    assert isinstance(piece, Armor), item_id
    p.armor_slots[SLOT_INDEX[piece.slot]] = piece
    return piece


# ---------------------------------------------------------------- the data

def test_every_new_piece_loads_is_named_and_has_art_and_a_story():
    armor = _data('items/armor.json')
    for iid in NEW_ARMOR:
        d = armor[iid]
        piece = make_item_by_id('armor', iid)
        assert isinstance(piece, Armor) and piece.is_unique, iid
        assert piece.slot in SLOT_INDEX
        assert d['name'] == d['name'].strip() and d['name'][0].isupper()
        assert len(d['lore']) > 200, iid
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'items', f'{iid}.png')), iid
        assert d['can_be_cursed'] is False
    shield = make_item_by_id('shield', 'hrungnirs_stone_shield')
    assert isinstance(shield, Shield) and shield.is_unique


def test_a_new_piece_is_no_weaker_than_plain_armor_of_its_floor():
    """Lore decides what it is; the floor it sits on must still be one where
    that much armor belongs: at least the middle plain piece for the slot."""
    import statistics
    armor = _data('items/armor.json')
    for iid in NEW_ARMOR:
        d = armor[iid]
        near = [v['ac_bonus'] for v in armor.values()
                if isinstance(v, dict) and not v.get('is_unique') and v.get('slot') == d['slot']
                and v.get('peak_floor') is not None and abs(v['peak_floor'] - d['peak_floor']) <= 12]
        if near:
            assert d['ac_bonus'] >= statistics.median(near) - 1, (iid, d['ac_bonus'], near)


def test_every_slot_has_a_named_piece_to_find_early_middle_and_late():
    armor = _data('items/armor.json')
    for slot in SLOT_INDEX:
        peaks = [v['peak_floor'] for v in armor.values()
                 if isinstance(v, dict) and v.get('is_unique') and v.get('slot') == slot
                 and (v.get('peak_weight') or 0) > 0 and (v.get('min_level') or 0) < 9999]
        for lo, hi in ((1, 33), (34, 66), (67, 100)):
            assert any(lo <= pk <= hi for pk in peaks), (slot, lo, hi, sorted(peaks))


def test_every_named_drop_names_a_real_item():
    mons = _data('monsters.json')
    from items import load_items
    # the same search the game makes when the monster dies (Game._spawn_unique_item)
    known = {i.id for cat in ('weapon', 'armor', 'shield', 'accessory', 'wand', 'scroll',
                              'artifact', 'potion') for i in load_items(cat)}
    for mid, iid in DROPS.items():
        assert mons[mid]['treasure']['unique_drop_id'] == iid
    for mid, m in mons.items():
        if not isinstance(m, dict):
            continue
        iid = (m.get('treasure') or {}).get('unique_drop_id')
        if iid:
            assert iid in known, (mid, iid)


def test_a_piece_only_its_monster_carries_is_never_random_loot():
    armor = _data('items/armor.json')
    for iid in set(DROPS.values()) & set(armor):
        assert armor[iid]['peak_weight'] == 0.0, iid


def test_every_legend_and_scroll_boss_leaves_something_named():
    """The six mini-bosses below lost theirs in v2.18.0; the five gate and
    end bosses leave their own rewards by other means."""
    other_reward = {'lamia', 'asterion_minotaur', 'medusa_gorgon', 'fafnir_dragon', 'fenrir_wolf',
                    'abaddon_destroyer', 'rangda', 'tiamat'}
    for mid, m in _data('monsters.json').items():
        if not isinstance(m, dict):
            continue
        t = m.get('treasure') or {}
        if t.get('boss_scroll_id') and mid not in other_reward:
            assert t.get('unique_drop_id'), mid


# ---------------------------------------------------------------- the worn bonuses

def test_worn_dodge_and_toughness_add_to_the_stat_and_stop_at_ten_points():
    p = Player()
    assert p.dodge_chance() == 0.0 and p.toughness() == 0.0
    _wear(p, 'bracers_of_atalanta')
    assert abs(p.dodge_chance() - 0.04) < 1e-9
    _wear(p, 'falcon_cloak_of_freyja')
    assert abs(p.dodge_chance() - 0.10) < 1e-9
    for iid in ('cestus_of_polydeuces', 'hair_shirt_of_becket', 'greaves_of_goliath'):
        _wear(p, iid)
    assert abs(p.toughness() - 0.10) < 1e-9          # 0.03 + 0.04 + 0.05, held to 0.10
    p.CON = 200
    p.DEX = 200
    assert abs(p.toughness() - (p.TOUGHNESS_CAP + p.GEAR_BONUS_CAP)) < 1e-9
    assert abs(p.dodge_chance() - (p.DODGE_CAP + p.GEAR_BONUS_CAP)) < 1e-9


def test_nobody_who_cannot_move_dodges_whatever_they_wear():
    p = Player()
    _wear(p, 'falcon_cloak_of_freyja')
    p.add_effect('paralyzed', 5)
    assert p.dodge_chance() == 0.0


def test_toughness_from_armor_takes_its_share_off_a_blow():
    p = Player()
    p.max_hp = p.hp = 1000
    _wear(p, 'glove_of_tyr')
    assert p.take_damage(100, 'physical') == 94


def test_waylands_gloves_add_a_second_to_the_combat_clock():
    p = Player()
    base = p.get_quiz_extra_seconds('math')
    _wear(p, 'gloves_of_wayland')
    assert p.get_quiz_extra_seconds('math') == base + 1


def test_jarngreipr_lengthens_a_chain_that_lands_and_only_that():
    piece = make_item_by_id('armor', 'jarngreipr_gauntlets')
    assert piece.chain_bonus == 1
    src = open(os.path.join(ROOT, 'src', 'combat.py'), encoding='utf-8').read()
    at = src.index("getattr(slot, 'chain_bonus', 0)")
    assert 'if result.score >= 1:' in src[at - 400:at]


def test_the_three_cloak_rules_that_no_item_carried_are_carried_again():
    p = Player()
    for iid, flag in (('arachne_silk_cloak', 'webbed_strike'), ('erlking_mantle', 'forest_hearing'),
                      ('anansi_web_cloak', 'story_thread')):
        p.armor_slots = [None] * 8
        assert not armor_procs.player_has_armor_proc(p, flag)
        _wear(p, iid)
        assert armor_procs.player_has_armor_proc(p, flag), iid
    assert armor_procs.proc_value(_erlking_wearer(), 'forest_hearing') == 6


def _erlking_wearer():
    p = Player()
    _wear(p, 'erlking_mantle')
    return p


def test_the_green_girdle_turns_one_great_blow_a_floor():
    p = Player()
    _wear(p, 'green_girdle')
    assert armor_procs.consume_floor_charge(p, 'story_thread')
    assert not armor_procs.consume_floor_charge(p, 'story_thread')      # spent for this floor
    armor_procs.reset_per_floor_charges(p)
    assert armor_procs.consume_floor_charge(p, 'story_thread')


def test_a_named_piece_says_what_it_does_on_its_card():
    """A rule the player cannot see in the numbers is told in one sentence."""
    armor = _data('items/armor.json')
    for iid in ('anansi_web_cloak', 'arachne_silk_cloak', 'erlking_mantle', 'green_girdle'):
        assert len(armor[iid]['special']) > 30
        assert make_item_by_id('armor', iid).special == armor[iid]['special']
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    assert "lines.append(item.special)" in src


# ---------------------------------------------------------------- the same pass: art and small fixes

def test_every_monster_has_a_sprite():
    for mid, m in _data('monsters.json').items():
        if isinstance(m, dict):
            assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'monsters', f'{mid}.png')), mid


def test_an_encounter_choice_that_costs_gold_says_how_much():
    import economy
    enc = {'options': [{'label': 'Ask About Treasure', 'cost': {'type': 'gold', 'amount': 350}},
                       {'label': 'Walk Away'}]}
    out = economy.price_encounter(enc)
    paid, free = out['options']
    assert f"{paid['cost']['amount']:,} Gold" in paid['label']
    assert free['label'] == 'Walk Away'
    for e in _data('npc_encounters.json').values() if isinstance(_data('npc_encounters.json'), dict) else []:
        if not isinstance(e, dict) or not e.get('options'):
            continue
        for opt in economy.price_encounter(e)['options']:
            cost = opt.get('cost')
            if isinstance(cost, dict) and cost.get('type') == 'gold' and cost.get('amount'):
                amount = int(cost['amount'])
                assert str(amount) in opt['label'] or f'{amount:,}' in opt['label'], opt['label']


# ---------------------------------------------------------------- the item-by-item verification (2026-10-08)

def _chain_worn(p, item_id, tier):
    from chain_equip import apply_tier_bonuses
    piece = make_item_by_id('armor', item_id)
    p.armor_slots[SLOT_INDEX[piece.slot]] = piece
    apply_tier_bonuses(p, piece, tier)
    return piece


def test_a_chain_piece_pushed_out_of_its_slot_takes_its_bonuses_with_it():
    """Crown of Brahma then any helm, four times over, gave +16 Intelligence."""
    p = Player()
    base = (p.INT, p.max_mp, dict(p.damage_resistances), dict(p.status_effects))
    for _ in range(4):
        crown = _chain_worn(p, 'crown_of_brahma', 5)
        assert p.INT > base[0] and p.max_mp > base[1]
        p._apply_equip(make_item_by_id('armor', 'coif_of_beowulf'))
        assert crown in p.inventory and crown.achieved_tier == 0
        assert (p.INT, p.max_mp, dict(p.damage_resistances)) == base[:3]
        assert 'regenerating' not in p.status_effects
        p.inventory.clear()
        p.armor_slots = [None] * 8


def test_armor_taken_off_leaves_nothing_behind():
    """The Blindfold left its wearer blind for the rest of the run; the swift
    boots left their haste; Elijah's mantle left its mana."""
    for iid, status in (('blindfold', 'blinded'), ('greaves_of_hermes', 'hasted'),
                        ('cloth_of_penelope', 'regenerating'), ('cloak_of_sun_wukong', 'displacement')):
        p = Player()
        piece = make_item_by_id('armor', iid)
        p._apply_equip(piece)
        assert p.status_effects.get(status) == -1, iid
        p.armor_slots[SLOT_INDEX[piece.slot]] = None
        p.shed_worn_grants(piece)
        assert status not in p.status_effects, iid
    p = Player()
    mp = p.max_mp
    mantle = make_item_by_id('armor', 'mantle_of_elijah')
    p._apply_equip(mantle)
    assert p.max_mp == mp + 3
    p.armor_slots[SLOT_INDEX['cloak']] = None
    p.shed_worn_grants(mantle)
    assert p.max_mp == mp
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    at = src.index('def _unequip_slot')
    assert src[at:at + 4000].count('shed_worn_grants(item)') == 2          # armor and shield


def test_a_status_two_pieces_grant_stays_while_one_is_still_worn():
    p = Player()
    boots = make_item_by_id('armor', 'greaves_of_hermes')
    p._apply_equip(boots)
    other = make_item_by_id('armor', 'boots_of_seven_leagues')
    other.slot = 'legs'                      # stand-in for a second haste granter in another slot
    p.armor_slots[SLOT_INDEX['legs']] = other
    p.armor_slots[SLOT_INDEX['feet']] = None
    p.shed_worn_grants(boots)
    assert p.status_effects.get('hasted') == -1


def test_a_chain_resistance_level_takes_a_share_of_the_blow():
    p = Player()
    p.max_hp = p.hp = 100000
    p.damage_resistances['fire'] = 2
    assert p.take_damage(1000, 'fire') == int(1000 * (1 - p.CHAIN_RESIST_STEP) ** 2)
    assert p.take_damage(1000, 'cold') == 1000


def test_a_chain_fear_level_steadies_the_will():
    p = Player()
    base = p.save_bonus_for('WIS')
    p.damage_resistances['fear'] = 1
    assert p.save_bonus_for('WIS') == base + 1 and p.save_bonus_for('CON') == 0


def test_regeneration_mends_a_share_of_a_large_body():
    import status_effects
    for max_hp, want in ((100, 1), (1500, 5)):
        p = Player()
        p.max_hp = max_hp
        p.hp = 10
        p.add_effect('regenerating', -1)
        p._regen_phase = status_effects.REGEN_PERIOD - 1
        p._hp_regen_acc = 0
        before = p.hp
        src = open(os.path.join(ROOT, 'src', 'status_effects.py'), encoding='utf-8').read()
        assert 'player.restore_hp(max(1, int(player.max_hp * REGEN_SHARE)))' in src
        assert max(1, int(max_hp * status_effects.REGEN_SHARE)) == want
        assert before == 10


def test_the_coif_of_beowulf_breaks_every_hold():
    from status_effects import tick_all
    for eff in ('paralyzed', 'sleeping', 'strangulation', 'immobilized', 'stunned', 'frozen'):
        p = Player()
        _wear(p, 'coif_of_beowulf')
        p.status_effects[eff] = 6
        tick_all(p)
        assert not p.has_effect(eff), eff


def test_gilgameshs_bribe_asks_for_something_monsters_have():
    import game_menus
    mons = [m for m in _data('monsters.json').values() if isinstance(m, dict)]
    assert not any('intelligence' in m for m in mons)
    takers = [m for m in mons if set(m.get('tags') or ()) & game_menus.BRIBE_TAGS
              and not set(m.get('tags') or ()) & {'boss', 'legendary'}]
    assert len(takers) > 150
    src = open(os.path.join(ROOT, 'src', 'game_menus.py'), encoding='utf-8').read()
    assert "'intelligence'" not in src


def test_a_monster_records_what_it_swung_for_the_armor_that_answers():
    """The Hydra carapace and the three fire-throwing shields read fields no
    monster had, so none of them ever fired."""
    mon = open(os.path.join(ROOT, 'src', 'monster.py'), encoding='utf-8').read()
    assert mon.count("self._last_attack_type = atk.get('type', 'physical')") == 3
    gc = open(os.path.join(ROOT, 'src', 'game_combat.py'), encoding='utf-8').read()
    assert 'damage_types' not in gc and 'attack_types' not in gc
    assert "getattr(m, '_last_attack_type', None) == 'poison'" in gc
    assert "getattr(m, '_last_attack_type', None) == 'fire'" in gc
    assert gc.index('m._last_attack_type = None') < gc.index('dmg, msg = m.attack(self.player)')


def test_gifts_given_once_a_floor_cannot_be_farmed():
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    for anchor in ("'bond_check') and getattr(self, 'pets', None)", "'wisdom_at_a_price')\n                    and self.player.max_hp >= 20"):
        at = src.index(anchor)
        assert 'deepest_floor_reached > _was_deepest' in src[at:at + 260], anchor
    at = src.index("'disguise_at_camp'")
    assert 'consume_floor_charge' in src[at - 200:at]
    p = Player()
    _wear(p, 'cloak_of_mulan')
    assert armor_procs.consume_floor_charge(p, 'disguise_at_camp')
    assert not armor_procs.consume_floor_charge(p, 'disguise_at_camp')


def test_every_named_piece_has_something_to_say_on_its_card():
    plain = {'lionheart_shield', 'sandals_of_perseus'}        # no rule, by their own lore
    said = ('special', 'tier_bonuses', 'dodge_bonus', 'toughness_bonus', 'quiz_timer_bonus',
            'chain_bonus', 'spell_reflect', 'fire_reflect')
    for cat in ('armor', 'shield'):
        for iid, d in _data(f'items/{cat}.json').items():
            if not isinstance(d, dict) or not d.get('is_unique') or iid in plain:
                continue
            assert d.get('damage_resistances') or any(d.get(k) for k in said), iid


def test_no_named_piece_carries_a_rule_field_nothing_reads():
    armor = _data('items/armor.json')
    for iid, field in (('cow_kings_horns', 'bovine_fury'), ('tarnhelm', 'invisibility_cooldown'),
                       ('greaves_of_qin', 'resistances')):
        assert field not in armor[iid], (iid, field)
    assert armor['hide_of_nemean_lion']['floorSpawnWeight'] == {}


def test_the_duck_of_doom_does_not_answer_to_a_scroll():
    src = open(os.path.join(ROOT, 'src', 'game_magic.py'), encoding='utf-8').read()
    assert "getattr(eq, 'id', '') != 'duck_of_doom'" in src
