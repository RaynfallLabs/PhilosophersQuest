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


# ===========================================================================
# Round 2 (2026-10-04): trophy powers, monster control, open findings
# ===========================================================================

def _all_permanent_powers():
    import glob
    import re
    powers = set()
    for f in glob.glob(str(_ROOT / 'data' / 'items' / '*.json')):
        text = Path(f).read_text(encoding='utf-8')
        powers |= set(re.findall(r'"permanent_power": "([a-z0-9_]+)"', text))
    return sorted(powers)


def test_w8_every_trophy_power_changes_the_player():
    """Each permanent power in the data must leave a real, READ effect:
    a stat, a status the engine honours, a resistance, or a known flag."""
    from player import Player
    from food_system import _apply_permanent_power
    from status_effects import EFFECT_INFO
    powers = _all_permanent_powers()
    assert len(powers) >= 10
    flags = ('_asmodeus_pact', '_green_knight_revive', '_fafnir_per_descent_hp',
             '_nidhogg_per_descent_mp', '_blood_archon_lifesteal')
    stats = ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER')
    for power in powers:
        p = Player()
        before_fx = dict(p.status_effects)
        before_stats = {s: getattr(p, s) for s in stats}
        _apply_permanent_power(p, power, {})
        new_fx = [k for k, v in p.status_effects.items() if before_fx.get(k) != v]
        changed = (new_fx
                   or any(getattr(p, s) != before_stats[s] for s in stats)
                   or p.damage_resistances
                   or any(getattr(p, f, None) for f in flags))
        assert changed, f"trophy power {power!r} does nothing"
        for fx in new_fx:
            assert fx in EFFECT_INFO, f"{power}: status {fx!r} is unknown to the engine"


def test_w8_trophy_immunities_block_their_effect():
    from player import Player
    for immunity, effect in (('petrify_immune', 'petrifying'),
                             ('confuse_immune', 'confused'),
                             ('acid_resist', 'corroding')):
        p = Player()
        p.status_effects.clear()
        p.add_effect(immunity, -1)
        assert p.add_effect(effect, 5) is False, immunity


def _monster(tags=(), **flags):
    from monster import Monster
    defn = {'id': 'test_mon', 'name': 'test monster', 'symbol': 'm',
            'color': [200, 200, 200], 'hp': '10', 'thac0': 20,
            'attacks': [{'name': 'bite', 'damage': '1d4'}],
            'tags': list(tags)}
    defn.update(flags)
    return Monster(defn, 5, 5)


def test_w11_control_immunities_follow_creature_nature():
    golem = _monster(tags=['construct'])
    zombie = _monster(tags=['undead'])
    wolf = _monster(tags=['beast'])
    boss = _monster(tags=['demon'], is_boss=True)
    mini = _monster(tags=['beast'], is_mini_boss=True)
    assert golem.resists_control('feared') and golem.resists_control('charmed')
    assert golem.resists_control('confused')
    assert zombie.resists_control('charmed') and not zombie.resists_control('feared')
    for effect in ('feared', 'charmed', 'confused', 'blinded', 'immobilized'):
        assert not wolf.resists_control(effect), effect
    assert boss.resists_control('feared') and boss.resists_control('immobilized')
    assert mini.resists_control('charmed') and not mini.resists_control('immobilized')


def test_w11_feared_ranged_monster_flees_instead_of_shooting():
    """Special AI patterns used to return before the fear check."""
    from types import SimpleNamespace
    m = _monster(tags=['humanoid'], ai_pattern='ranged')
    m.status_effects['feared'] = 5
    called = []
    m._flee_from = lambda *a, **k: called.append('flee')
    m._ranged_turn = lambda *a, **k: called.append('shoot') or True
    player = SimpleNamespace(x=7, y=5, has_effect=lambda n: False,
                             equipped_accessories=[])
    dungeon = SimpleNamespace()
    assert m.take_turn(player, dungeon, [m]) is False
    assert called == ['flee']


def test_w16_multi_attack_applies_on_hit_effect_once(monkeypatch):
    # Pin the to-hit rolls: a natural 1 on the first swing made this flaky.
    import random as _random
    monkeypatch.setattr(_random, 'randint', lambda a, b: b)
    monkeypatch.setattr(_random, 'random', lambda: 0.0)
    m = _monster(tags=['giant'])
    seen = []
    m._apply_attack_effect = lambda atk, player: (seen.append(atk['name']) or ' You are stunned!')
    m.attacks = [{'name': 'a', 'damage': '2d4', 'effect': 'stunned'},
                 {'name': 'b', 'damage': '2d4', 'effect': 'frozen'}]
    m.thac0 = -50          # always hits

    class _P:
        def get_ac(self):
            return 10

        def take_damage(self, dmg, dtype='physical'):
            return dmg

    total, msg = m._fenrir_multi_attack(_P())
    assert total > 0
    assert seen == ['a'], "one effect per flurry"
    assert msg.endswith('You are stunned!')


def test_w15_bones_rebuild_composed_gear():
    from bones import _recompose_gear
    sword = _recompose_gear('iron_longsword', 'weapon')
    assert sword is not None and sword.id == 'iron_longsword'
    two_word = _recompose_gear('cold_iron_bastard_sword', 'weapon')
    assert two_word is not None and two_word.id == 'cold_iron_bastard_sword'
    assert _recompose_gear('not_a_real_thing', 'weapon') is None


def test_w19_reveal_floor_uses_real_dungeon_api():
    src = (_ROOT / 'src' / 'hero_specials.py').read_text(encoding='utf-8')
    block = src[src.index('def _eff_reveal_floor'):]
    block = block[:block.index('\ndef ', 10)]
    assert 'game.dungeon.is_door(' not in block
    assert 'game.explored.add' not in block
    assert 'game.dungeon.explored.add' in block


def test_w24_no_two_composed_gear_items_share_a_name():
    """Every (template, material) pair must produce a distinct item name.
    "Adamantine Shirt" used to be both a chain shirt (body, AC 6) and a
    padded shirt (shirt slot, AC 4)."""
    import collections
    from items import load_templates, load_materials, compose_item_name
    by_name = collections.defaultdict(set)
    for tcat, mcat in (('weapons', 'weapons'), ('armor', 'armor'),
                       ('shields', 'armor')):
        mats = load_materials(mcat)
        for tid, tpl in load_templates(tcat).items():
            ok = set(tpl.get('compatible_material_classes') or [])
            for mat in mats.values():
                if ok and mat.get('material_class') not in ok:
                    continue
                name = compose_item_name(mat['name'], tpl['name'],
                                         tpl.get('noun', ''))
                by_name[name].add((tcat, tid))
    clashes = {n: sorted(v) for n, v in by_name.items() if len(v) > 1}
    assert not clashes, list(clashes.items())[:6]
