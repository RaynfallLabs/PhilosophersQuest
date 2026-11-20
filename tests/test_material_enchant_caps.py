"""How much magic an armour material holds (Brandon, 2026-11-19: "lore caps;
this can add a new dimension to armor and materials; some materials hold
magic better (even if they're not inherently stronger) ... just make sure
you balance it").

A common body armour or shield holds at most its material's max_enchant
(gear.enchant_cap_for), whatever raises it: its level when found, an
Enchant Armour scroll, an NPC's reward, a smith.
"""
from __future__ import annotations

import glob
import json
import os
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import gear  # noqa: E402
import items  # noqa: E402


def _materials() -> dict:
    out = {}
    for f in glob.glob(os.path.join(ROOT, 'data', 'materials', 'armor', '*.json')):
        with open(f, encoding='utf-8') as fh:
            m = json.load(fh)
        out[m['id']] = m
    return out


def _ac_potential(tpl_ac, mat):
    return tpl_ac + int(mat.get('ac_bonus') or 0) + gear.material_enchant_cap(mat)


def test_every_armour_material_says_what_it_holds_and_why():
    ceiling = gear.rules()['enchant_cap']['ceiling']
    for mid, m in _materials().items():
        assert isinstance(m.get('max_enchant'), int), mid
        assert 1 <= m['max_enchant'] <= ceiling, mid
        note = m.get('enchant_note') or ''
        assert note and len(note) < 90 and note[0].isupper() and note.endswith('.'), mid


def test_the_caps_follow_the_lore():
    m = _materials()
    cap = {k: v['max_enchant'] for k, v in m.items()}
    # Cold iron turns magic aside; steel a little better; bronze, the heroes' metal, better still.
    assert cap['ring_iron'] < cap['chain_steel'] < cap['tempered_bronze']
    # Leather and hide hold a little; a drake's and a dragon's skin hold more.
    assert cap['leather'] == cap['hide'] == 2 < cap['drakeskin_armor'] < cap['dragonhide_armor']
    # The strongest metal is not the one that holds the most magic.
    assert m['adamantine']['ac_bonus'] > m['mithril']['ac_bonus']
    assert cap['adamantine'] < cap['mithril']
    # Elven silk is the weakest armour of its depth and drinks magic in.
    assert cap['elven_silk'] == gear.rules()['enchant_cap']['ceiling']
    assert cap['tungsten'] == cap['primordial_stone_armor'] == 1


def test_balanced_no_material_runs_away_with_its_depth():
    """What a fully enchanted piece can reach: the best light armour stays
    under the best heavy (light keeps its dodge and speed), and within each
    weight class the deep materials' potential stays close together."""
    m = _materials()
    light = _ac_potential(1, m['elven_silk'])            # padded
    medium = _ac_potential(3, m['mithril'])              # a mithril chain shirt
    heavy = max(_ac_potential(8, m[k]) for k in ('adamantine', 'dwarven_plate', 'orichalcum_armor',
                                                  'starmetal_armor', 'godweave_armor', 'mithril'))
    assert light < medium < heavy
    deep_plate = [_ac_potential(8, m[k]) for k in ('adamantine', 'dwarven_plate', 'orichalcum_armor',
                                                    'starmetal_armor', 'godweave_armor', 'sunsteel_armor',
                                                    'glassteel', 'soulsteel')]
    assert max(deep_plate) - min(deep_plate) <= 3, deep_plate


def test_a_found_piece_never_holds_more_than_its_material():
    leather = items.instantiate_armor('leather', 'leather', level=10)
    assert leather.enchant_bonus == gear.enchant_cap_for(leather) == 2
    mith = items.instantiate_armor('chain_shirt', 'mithril', level=10, enchant=3)
    assert mith.enchant_bonus == 6
    iron = items.instantiate_shield('kite_shield', 'iron', level=10)
    assert iron.enchant_bonus <= gear.enchant_cap_for(iron)


def test_a_named_piece_keeps_the_core_cap():
    p = types.SimpleNamespace(is_unique=True, material='leather', item_class='armor', slot='body')
    assert gear.enchant_cap_for(p) == gear.core_enchant_cap() == 5


def test_effective_enchant_cap_reads_the_piece_for_body_and_shield():
    leather = items.instantiate_armor('leather', 'leather')
    assert items.effective_enchant_cap(None, 'body', leather) == 2
    # Without a piece it is the slot's old figure, as before.
    assert items.effective_enchant_cap(None, 'body') == items.ENCHANT_CAP['body']


_SCREEN = None


def _game():
    global _SCREEN
    from main import Game
    from game_states import STATE_PLAYER
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    random.seed(7)
    items.bind_unique_registry(set())
    g = Game(_SCREEN, player_name='__test_enchant_caps__')
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    return g


def _wear(g, piece):
    i = items.ARMOR_SLOTS.index('body')
    g.player.armor_slots[i] = piece
    g.player.shield = None


def _read(g, buc='blessed', tier=5):
    g._apply_scroll_effect(types.SimpleNamespace(
        effect='enchant_armor', buc=buc, tier=tier, quiz_tier=tier, power=None, name='scroll'))


def test_a_scroll_stops_at_the_material_and_says_why():
    g = _game()
    piece = items.instantiate_armor('leather', 'leather')
    piece.enchant_bonus = 1
    _wear(g, piece)
    before = len(g.msg_log.entries)
    _read(g)                                 # blessed, tier 5: +4, held to +2
    assert piece.enchant_bonus == 2
    _read(g)
    assert piece.enchant_bonus == 2
    texts = [str(e[0]) for e in g.msg_log.entries[before:]]
    assert any('can hold no more enchantment' in t for t in texts), texts
    assert any(t == _materials()['leather']['enchant_note'] for t in texts), texts


def test_a_scroll_never_strips_an_old_saves_higher_plus():
    g = _game()
    piece = items.instantiate_armor('leather', 'leather')
    piece.enchant_bonus = 4                  # an old save's leather, enchanted before the caps
    _wear(g, piece)
    _read(g)
    assert piece.enchant_bonus == 4
    _read(g, buc='cursed')
    assert piece.enchant_bonus == 3          # a curse still takes a point off


def test_the_smith_reinforces_only_below_the_material_cap():
    g = _game()
    piece = items.instantiate_armor('leather', 'leather')
    _wear(g, piece)
    piece.enchant_bonus = 1
    assert g._service_targets('reinforce') == [piece]
    piece.enchant_bonus = 2
    assert g._service_targets('reinforce') == []


def test_an_npc_reward_stops_at_the_material():
    import npc_encounters
    piece = items.instantiate_armor('leather', 'leather')
    piece.enchant_bonus = 1
    old, new = npc_encounters.shift_armor_enchant(None, piece, 3)
    assert (old, new) == (1, 2)
