"""Regression tests for bugs found in the pre-v3.0 audit (2026-10-04).

Each test names the audit id from PRE_V3_AUDIT_REPORT.md.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))

from quiz_engine import QuizEngine  # noqa: E402


def _q(tier, text, answer='right'):
    return {'tier': tier, 'question': text, 'answer': answer,
            'choices': [answer, 'w1', 'w2', 'w3']}


def _engine(n=8):
    eng = QuizEngine()
    eng._cache['math'] = [_q(1, f'Q{i}') for i in range(n)]
    return eng


# ---- B2: a finished quiz must not finish twice ----------------------------

def test_b2_end_fires_callback_once():
    eng = _engine()
    calls = []
    eng.start_quiz('threshold', 'math', tier=1, callback=calls.append,
                   threshold=1)
    eng._end(success=False)
    eng._end(success=False)          # stray second end (e.g. ESC)
    assert len(calls) == 1
    assert eng.callback is None


# ---- B7: Tablet reroll flag is one-shot -----------------------------------

def test_b7_reroll_flag_applies_to_one_quiz_only():
    eng = _engine()
    eng._reroll_flag = True
    eng.start_quiz('chain', 'math', tier=1, callback=lambda r: None)
    assert eng.reroll_available is True
    eng._end(success=True)
    eng.start_quiz('threshold', 'math', tier=1, callback=lambda r: None,
                   threshold=1)
    assert eng.reroll_available is False, \
        "a combat reroll must not leak into the next quiz"


def test_b7_reroll_does_not_grant_a_free_chain():
    eng = _engine()
    eng._reroll_flag = True
    eng.start_quiz('chain', 'math', tier=1, callback=lambda r: None)
    eng.answer('w1')                  # wrong first answer
    eng.result_timer = 0
    eng._advance()
    assert eng.reroll_was_used is True
    assert eng.chain == 0


# ---- B19: scroll offset resets per question --------------------------------

def test_b19_scroll_offset_resets_on_next_question():
    eng = _engine()
    eng.start_quiz('chain', 'math', tier=1, callback=lambda r: None)
    eng._quiz_scroll_offset = 96
    eng._next_question()
    assert eng._quiz_scroll_offset == 0


# ---- B13: tick_all must not resurrect an effect removed mid-tick -----------

def test_b13_poison_damage_wakes_sleeper_for_good():
    from player import Player
    from status_effects import tick_all
    p = Player()
    p.hp = p.max_hp = 50
    p.status_effects.clear()
    p.status_effects['poisoned'] = 5
    p.status_effects['sleeping'] = 4
    tick_all(p)
    assert 'sleeping' not in p.status_effects


# ---- B15: no duplicate keys in the expire-message table --------------------

def test_b15_no_duplicate_expire_messages():
    src = (_ROOT / 'src' / 'status_effects.py').read_text(encoding='utf-8')
    start = src.index('_EXPIRE_MSGS')
    block = src[start:src.index('\n}\n', start)]
    keys = [line.split("'")[1] for line in block.splitlines()
            if line.strip().startswith("'")]
    dupes = {k for k in keys if keys.count(k) > 1}
    assert not dupes, dupes


# ---- B16: joiners inside hyphenated names stay lowercase -------------------

def test_b16_hyphenated_small_words():
    from naming import proper_name
    assert proper_name("will-o'-the-wisp") == "Will-o'-the-Wisp"
    assert proper_name('ox-hide shield') == 'Ox-Hide Shield'


# ---- W1: every rage bonus in the data can be rolled ------------------------

def test_w1_rage_damage_bonus_never_crashes():
    from monster import Monster
    defs = json.loads((_ROOT / 'data' / 'monsters.json').read_text(encoding='utf-8'))
    checked = 0
    for mid, d in defs.items():
        if not isinstance(d, dict) or not d.get('rage_damage_bonus'):
            continue
        d = dict(d)
        d.setdefault('id', mid)
        m = Monster(d, 0, 0)
        assert isinstance(m._roll_rage_bonus(), int), mid
        checked += 1
    assert checked >= 1


# ---- W12: merchant placement tests FLOOR, not a magic number ---------------

def test_w12_merchant_uses_floor_constant():
    src = (_ROOT / 'src' / 'mystery_system.py').read_text(encoding='utf-8')
    assert '== 3  # FLOOR' not in src
    from dungeon import FLOOR, STAIRS_DOWN
    assert FLOOR != STAIRS_DOWN


# ---- W5: Vidar's Sandal template is where the altar looks for it -----------

def test_w5_vidars_sandal_is_an_artifact():
    from items import load_items
    assert any(a.id == 'vidars_sandal' for a in load_items('artifact'))
    src = (_ROOT / 'src' / 'game_divine.py').read_text(encoding='utf-8')
    block = src[src.index('def _check_vidar_altar'):]
    block = block[:block.index('\n    def ', 10)]
    assert "load_items('artifact')" in block
    assert block.index('sandal_t =') < block.index('self.ground_items.remove(scrap)')


# ---- B6: slings resolve as ranged even with ammo=None ---------------------

def test_b6_ranged_flag_selects_the_ranged_weapon():
    """Structure-level guard: player_attack picks the weapon from an
    explicit ranged flag, and the ranged caller passes it."""
    src = (_ROOT / 'src' / 'combat.py').read_text(encoding='utf-8')
    head = src[src.index('def player_attack('):src.index('def _callback(result)')]
    assert 'is_ranged = bool(ammo) if ranged is None else bool(ranged)' in head
    assert 'weapon = player.ranged_weapon if is_ranged else player.weapon' in head
    # The caller for ranged fire passes the flag explicitly.
    gc = (_ROOT / 'src' / 'game_combat.py').read_text(encoding='utf-8')
    assert 'ammo=ammo_item, ranged=True' in gc


# ---- B4 / W10: collateral and reflect kills are processed ------------------

def test_b4_collateral_kills_are_swept_after_an_attack():
    from types import SimpleNamespace
    from game_combat import CombatMixin

    handled = []

    class _G(CombatMixin):
        def _on_monster_killed(self, monster, **kw):
            monster._kill_handled = True
            handled.append(monster.name)

    g = _G()
    primary = SimpleNamespace(name='primary', alive=False)
    bystander = SimpleNamespace(name='bystander', alive=False)
    long_dead = SimpleNamespace(name='long dead', alive=False)
    survivor = SimpleNamespace(name='survivor', alive=True)
    already = SimpleNamespace(name='already handled', alive=False,
                              _kill_handled=True)
    g.monsters = [primary, bystander, long_dead, survivor, already]
    alive_before = {id(primary), id(bystander), id(survivor), id(already)}
    g._process_collateral_kills(primary, alive_before, chain=5)
    assert handled == ['bystander']


def test_b5_curtana_flag_is_not_consumed_by_the_kill_handler():
    src = (_ROOT / 'src' / 'game_combat.py').read_text(encoding='utf-8')
    block = src[src.index('    def _on_monster_killed('):]
    block = block[:block.index('self._drop_treasure(monster)')]
    assert "Curtana's mercy" not in block, \
        "the mercy line belongs to the melee on_complete, not the kill handler"
    assert 'monster._kill_handled = True' in block


# ---- B8: unequipping a weapon removes its while-equipped effects -----------

def test_b8_unequip_reverses_weapon_passives():
    from player import Player
    from types import SimpleNamespace
    p = Player()
    base_per = p.PER
    hofud = SimpleNamespace(vigilance_aware=True, cursed_lineage=False,
                            prophecy_blade=False)
    for _ in range(3):
        p._apply_weapon_passives(hofud)
        p._remove_weapon_passives(hofud)
    assert p.PER == base_per
    src = (_ROOT / 'src' / 'main.py').read_text(encoding='utf-8')
    block = src[src.index('    def _unequip_slot('):]
    block = block[:block.index("elif slot_name == 'shield':")]
    assert 'self.player._remove_weapon_passives(item)' in block


# ---- B12: "while worn" chain-equip statuses are permanent, not 999 turns ---

def test_b12_chain_equip_while_worn_status_is_permanent():
    from types import SimpleNamespace
    import chain_equip
    src = (_ROOT / 'src' / 'chain_equip.py').read_text(encoding='utf-8')
    assert 'player.status_effects[status_name] = -1' in src
    # tick_all leaves a permanent (-1) effect alone.
    from player import Player
    from status_effects import tick_all
    p = Player()
    p.status_effects.clear()
    p.status_effects['fire_resist'] = -1
    for _ in range(5):
        tick_all(p)
    assert p.status_effects.get('fire_resist') == -1
    assert p.has_effect('fire_resist')
    del SimpleNamespace, chain_equip


# ---- B20: id()-keyed combat marks are not saved -----------------------------

def test_b20_id_keyed_marks_are_dropped_on_save():
    from player import Player
    p = Player()
    p._death_omen_target = 123456
    p._et_tu_target = 654321
    p._revealed_tag_ids = {1, 2, 3}
    state = p.__getstate__()
    for key in ('_death_omen_target', '_et_tu_target', '_revealed_tag_ids'):
        assert key not in state


# ---- B22: HUD and menus agree on what "identified" means -------------------

def test_b22_hud_needs_id_level_5_for_a_plain_name():
    from types import SimpleNamespace
    from hud_context import hud_item_name
    player = SimpleNamespace(knows_item_type=lambda item: True,
                             known_item_ids=set())
    item = SimpleNamespace(id='ring_x', name='Ring of X',
                           unidentified_name='A Plain Ring', id_level=4,
                           identified=True, buc='uncursed', buc_known=False,
                           count=1)
    assert hud_item_name(player, item).startswith('Unidentified')
    item.id_level = 5
    assert hud_item_name(player, item) == 'Ring of X'


# ---- W20: Cu Chulainn's permanent fear immunity (-1) actually applies ------

def test_w20_permanent_fear_immunity_blocks_fear():
    from player import Player
    p = Player()
    p.status_effects.clear()
    p.status_effects['fear_immune'] = -1
    assert p.add_effect('feared', 5) is False
    assert not p.has_effect('feared')


# ---- W9: pets do not target allied NPCs -------------------------------------

def test_w9_pet_targeting_skips_allies():
    src = (_ROOT / 'src' / 'pet_system.py').read_text(encoding='utf-8')
    block = src[src.index('# Find nearest alive enemy monster'):]
    block = block[:block.index('# Adjacent enemy')]
    assert "getattr(m, 'is_allied', False)" in block


# ---- W18: recalling a pet with a full pack keeps the pet -------------------

def test_w18_pet_recall_checks_the_pack_first():
    src = (_ROOT / 'src' / 'game_menus.py').read_text(encoding='utf-8')
    block = src[src.index('sphere.bound_pet = pet'):]
    block = block[:block.index('dissolves into the sphere')]
    assert block.index('if not self.player.add_to_inventory(sphere):') < \
        block.index('self.pets.remove(pet)')


# ---- B3: a cursed wielded weapon must not eat the new weapon ---------------

def test_b3_equip_checks_current_weapon_before_removing_new_one():
    src = (_ROOT / 'src' / 'main.py').read_text(encoding='utf-8')
    block = src[src.index('    def _equip_item(self, item):'):]
    block = block[:block.index('elif isinstance(item, Shield)')]
    assert block.index('try_unequip_slot(_current)') < \
        block.index('self.player.remove_from_inventory(item)')
