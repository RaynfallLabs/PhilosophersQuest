"""Bug bash 3.3.1: follow-ups the three validation passes found on the way.

- Pelops' Sword at STR 1 took nothing on equip but gave a point back on
  unequip, and moved STR without its stamina.
- One death spent every worn source of life_save at once.
- A scimitar's disarm (paralyzed 1) wore off before the disarmed foe moved.
- The Heart of Ahriman's double was spent by an area spell that hit nothing.
- A story reward's enchant_weapon had no cap.
- The Helm of Aragorn's command could never hold an undead (immune to charm).
- A wrong answer saved by a never-miss weapon still took the warm-up head
  starts that come after the saves (Harpe): a light hit is chain 1.

Headless and pure; none of these is reachable in a few minutes of play.
"""
import json
import os
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import combat  # noqa: E402
import items  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    _DEFS = json.load(_f)

_SCREEN = None


def _game(seed=5):
    global _SCREEN
    from main import Game
    from game_states import STATE_PLAYER
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    random.seed(seed)
    g = Game(_SCREEN, player_name='__test_bugbash_331_followups__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _weapon(wid):
    return next(w for w in items.load_items('weapon') if w.id == wid)


def _accessory(aid):
    return next(a for a in items.load_items('accessory') if a.id == aid)


def _monster(kind, x=6, y=5, hp=10 ** 6):
    m = Monster(dict(_DEFS[kind], id=kind), x, y)
    m.hp = m.max_hp = hp
    return m


# ------------------------------------------------------------ Pelops' Sword
def test_pelops_sword_gives_back_only_what_it_took():
    p = Player()
    sword = _weapon('pelops_sword')
    p.STR = 1
    p._apply_weapon_passives(sword)
    assert p.STR == 1
    p._remove_weapon_passives(sword)
    assert p.STR == 1, "taking the sword off at STR 1 gave a free point"


def test_pelops_sword_moves_stamina_with_strength():
    p = Player()
    sword = _weapon('pelops_sword')
    p.STR = 12
    str0, sp0 = p.STR, p.max_sp
    p._apply_weapon_passives(sword)
    assert (p.STR, p.max_sp) == (str0 - 1, sp0 - 1)
    p._remove_weapon_passives(sword)
    assert (p.STR, p.max_sp) == (str0, sp0)


def test_pelops_sword_from_an_old_save_gives_back_one():
    p = Player()
    sword = _weapon('pelops_sword')
    p.STR = 11
    assert not hasattr(sword, '_pelops_str_taken')
    p._remove_weapon_passives(sword)
    assert p.STR == 12


# --------------------------------------------------- one death, one ward
def test_one_death_spends_one_life_save_source():
    g = _game()
    p = g.player
    amulet = _accessory('amulet_life_saving')
    ring = _accessory('amulet_life_saving')
    ring.slot = 'ring'                       # a second worn source of life_save
    p.amulet_slot = amulet
    p.accessory_slots[0] = ring
    p.status_effects['life_save'] = -1
    p.hp = 0
    g._answer_a_killing_blow()
    assert p.hp == 1
    spent = [it for it in (amulet, ring)
             if (getattr(it, 'effects', None) or {}).get('status') != 'life_save']
    assert len(spent) == 1, "one death spent both wards"
    assert p.status_effects.get('life_save') == -1, "the second ward still holds a life"
    p.hp = 0
    g._answer_a_killing_blow()
    assert p.hp == 1
    assert 'life_save' not in p.status_effects


# ------------------------------------------------------------ disarm lasts
def test_disarm_holds_through_the_foes_turn(monkeypatch):
    src = open(os.path.join(ROOT, 'src', 'combat.py'), encoding='utf-8').read()
    i = src.index("class_mech in ('disarm_at_max', 'reach_disarm') and at_max")
    block = src[i:i + 200]
    assert "add_effect('paralyzed', 2)" in block
    m = _monster('kobold')
    m.add_effect('paralyzed', 2)
    m.tick_effects()                         # _advance_turn ticks before monsters move
    assert m.has_effect('paralyzed')


# ------------------------------------------------- the Heart of Ahriman
def test_ahriman_charge_survives_an_area_spell_into_an_empty_room():
    g = _game()
    g.player._anti_being_charged = True
    g._apply_spell_effect({'effect': 'meteor', 'power': '4d6', 'tier': 4, 'name': 'Meteor'})
    assert g.player._anti_being_charged, "the charge went on a spell that hit nothing"


def test_ahriman_charge_is_spent_on_a_spell_that_hurts():
    g = _game()
    m = _monster('kobold', g.player.x + 1, g.player.y)
    g.monsters = [m]
    g.visible = {(m.x, m.y), (g.player.x, g.player.y)}
    g.player._anti_being_charged = True
    g._apply_spell_effect({'effect': 'meteor', 'power': '4d6', 'tier': 4, 'name': 'Meteor'})
    assert m.hp < m.max_hp
    assert not g.player._anti_being_charged


# ------------------------------------------------- story enchant is capped
def test_story_enchant_weapon_reward_respects_the_blades_cap():
    g = _game()
    w = _weapon('gungnir')
    g.player.weapon = w
    cap = items.effective_enchant_cap(g.player, 'weapon', w)
    w.enchant_bonus = cap
    g._apply_npc_reward({'type': 'enchant_weapon', 'amount': 2})
    assert w.enchant_bonus == cap
    w.enchant_bonus = cap - 1
    g._apply_npc_reward({'type': 'enchant_weapon', 'amount': 3})
    assert w.enchant_bonus == cap


# --------------------------------------------------- the Helm of Aragorn
def test_aragorns_oath_binds_an_undead_and_ends_with_the_charm():
    undead = next(k for k, d in _DEFS.items()
                  if 'undead' in (d.get('tags') or []) and not d.get('is_boss')
                  and 'legendary' not in (d.get('tags') or []))
    m = _monster(undead)
    m.add_effect('charmed', 3)
    assert m.resists_control('charmed'), "undead take no ordinary charm"
    m._oathbound = True
    assert not m.resists_control('charmed')
    assert m._under('charmed')
    for _ in range(3):
        m.tick_effects()
    assert not m.has_effect('charmed')
    assert '_oathbound' not in m.__dict__
    assert m.resists_control('charmed')


def test_aragorns_command_reaches_an_undead_in_sight():
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    i = src.index("if _flag == 'command_undead':")
    assert "_target._oathbound = True" in src[i:i + 400]


# ----------------------------------------- a saved wrong answer is light
class _Quiz:
    def __init__(self, score):
        self.score = score

    def start_quiz(self, callback=None, **_kw):
        callback(types.SimpleNamespace(score=self.score, success=True, struck_early=False))


def test_a_saved_wrong_answer_takes_no_warmup_head_start():
    harpe = _weapon('harpe')
    harpe.cannot_miss = True                 # a never-miss blade that also knows the foe
    p = Player()
    p.weapon = harpe
    tag_kind = next(k for k in harpe.skip_chain_warmup_vs_tag if k in _DEFS)
    m = _monster(tag_kind)
    assert combat.effective_chain(p, m, harpe, 0, consume=False) == 1
    assert combat.effective_chain(p, m, harpe, 1, consume=False) == 2


# ------------------------------------------- the Trainer's Cap's new level
def _wear_trainers_cap(p):
    from items import ARMOR_SLOTS
    cap = next(a for a in items.load_items('armor') if a.id == 'trainers_cap')
    p.armor_slots[ARMOR_SLOTS.index(cap.slot)] = cap
    return cap


def test_trainers_cap_levels_a_pet_that_can_grow_not_dad():
    from pet_system import DadPet, Pet
    from armor_procs import player_has_armor_proc
    g = _game()
    _wear_trainers_cap(g.player)
    assert player_has_armor_proc(g.player, 'bond_check')
    dad = DadPet(g.player.x + 1, g.player.y, duration=500)
    pup = Pet('fire', g.player.x - 1, g.player.y, level=3)
    g.pets = [dad, pup]
    g._change_level(g.dungeon_level + 1, enter_from_top=True)
    assert pup.level == 4, "the cap's level went to Dad, who never levels"


# --------------------------------- a weapon taken away sheds what it lent
def test_a_weapon_taken_by_a_story_takes_its_passives_and_status():
    g = _game()
    p = g.player
    hofud = _weapon('hofud')
    p._apply_weapon_passives(hofud)
    p.weapon = hofud
    per = p.PER
    assert g._npc_remove_item_by_id('hofud')
    assert p.weapon is None
    assert p.PER == per - 2, "Hofud's +2 PER stayed after the story took it"
    storm = _weapon('stormbringer')
    p.weapon = storm
    p.status_effects['berserk'] = -1
    assert g._npc_remove_item_by_id('stormbringer')
    assert 'berserk' not in p.status_effects
