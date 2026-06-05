"""Save/load lifecycle (round-trip) tests for Philosopher's Quest.

These tests build a real Game in headless pygame, mutate state in
ways that mirror gameplay, run the full save -> pickle -> load_state
restoration cycle, then compare the result against the source state.

Each test cleans up its own save file via delete_save.

Focus areas (per the 2026-05-19 save-lifecycle audit):
  - Chain-equip items: player.damage_resistances, regen_bonus,
    item.achieved_tier, item._chain_passives, _chain_resistances,
    _chain_stat_bonuses, _chain_statuses, _chain_baseline.
  - Corpse id_level (property/setter migration via __setstate__).
  - LevelManager._planned_mini_bosses + _placed_mini_bosses.
  - Per-floor chain_passive_charges + per-run once-per-run set.
  - Status effects with durations.
  - Cross-floor state via level_mgr._saved.
  - Legacy compat shims (old saves missing newer fields).
"""

import os
import sys
import pickle

import pygame

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Headless pygame init -- many src modules import pygame at load time.
pygame.init()
_SCREEN = None


def _screen():
    """Lazy single-display-mode helper. Required for Game construction."""
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _new_game(name: str):
    """Build a fresh Game with a known per-test save-file name."""
    from main import Game
    return Game(_screen(), player_name=name)


def _save_then_load(game):
    """save_game(game) -> load_game -> new Game.load_state. Returns (new_game, state).

    Uses the game's own player_name as the save key. Caller is responsible
    for delete_save() teardown.
    """
    from save_system import save_game, load_game
    assert save_game(game), "save_game returned False"
    state = load_game(game.player_name)
    assert state is not None, "load_game returned None"
    new_game = _new_game(game.player_name)
    new_game.load_state(state)
    return new_game, state


def _cleanup(name: str):
    from save_system import delete_save
    delete_save(name)


# ---------------------------------------------------------------------------
# 1. Chain-equip armor: damage_resistances + ac_bonus override + passives
# ---------------------------------------------------------------------------

def test_chain_equip_armor_t5_round_trip():
    """Save with T5 chain-equip armor; load restores ac override, resistances,
    passives, baseline, achieved_tier."""
    name = '__test_lifecycle_chain_armor__'
    try:
        from items import load_items
        from chain_equip import apply_tier_bonuses, is_chain_equip

        g = _new_game(name)
        armors = load_items('armor')
        chain_armor = next((a for a in armors if is_chain_equip(a)), None)
        assert chain_armor is not None, "no chain-equip armor in JSON"

        # Equip + apply T5 bonuses
        g.player.armor_slots[1] = chain_armor  # body slot
        apply_tier_bonuses(g.player, chain_armor, 5)

        ac_before = chain_armor.ac_bonus
        res_before = dict(g.player.damage_resistances)
        passives_before = dict(chain_armor._chain_passives)
        baseline_before = dict(chain_armor._chain_baseline)
        assert chain_armor.achieved_tier == 5

        g2, _ = _save_then_load(g)
        restored = g2.player.armor_slots[1]

        assert restored is not None, "armor not restored to slot 1"
        assert restored.achieved_tier == 5
        assert restored.ac_bonus == ac_before
        assert dict(g2.player.damage_resistances) == res_before
        assert dict(restored._chain_passives) == passives_before
        assert dict(restored._chain_baseline) == baseline_before
    finally:
        _cleanup(name)


def test_chain_equip_revert_after_load_restores_baseline_ac():
    """A reload of a chain-equipped item still has its _chain_baseline,
    so revert_tier_bonuses can undo the ac_bonus override after load."""
    name = '__test_lifecycle_revert__'
    try:
        from items import load_items
        from chain_equip import apply_tier_bonuses, revert_tier_bonuses, is_chain_equip

        g = _new_game(name)
        armors = load_items('armor')
        chain_armor = next((a for a in armors if is_chain_equip(a)), None)
        assert chain_armor is not None
        original_ac = chain_armor.ac_bonus

        g.player.armor_slots[1] = chain_armor
        apply_tier_bonuses(g.player, chain_armor, 5)
        ac_at_t5 = chain_armor.ac_bonus

        g2, _ = _save_then_load(g)
        restored = g2.player.armor_slots[1]
        assert restored.ac_bonus == ac_at_t5

        # Revert after load should restore the original baseline ac
        revert_tier_bonuses(g2.player, restored)
        assert restored.ac_bonus == original_ac
        assert restored.achieved_tier == 0
        # Player-side state should be empty after revert
        assert g2.player.damage_resistances == {}
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# 2. Chain-equip accessory: stat_bonus + passives + status
# ---------------------------------------------------------------------------

def test_chain_equip_accessory_t4_round_trip():
    """Save with T4 chain-equip ring/amulet; verify stat bonuses + passives
    survive the round trip."""
    name = '__test_lifecycle_chain_acc__'
    try:
        from items import load_items
        from chain_equip import apply_tier_bonuses, is_chain_equip

        g = _new_game(name)
        acc = load_items('accessory')
        chain_acc = next((a for a in acc if is_chain_equip(a)), None)
        assert chain_acc is not None, "no chain-equip accessory in JSON"

        # Find a tier with stat_bonus_* in it
        tier = None
        for t in (5, 4, 3):
            bonuses = chain_acc.tier_bonuses.get(str(t), chain_acc.tier_bonuses.get(t, {}))
            if any(k.startswith('stat_bonus_') for k in bonuses):
                tier = t
                break
        if tier is None:
            tier = 4  # fallback even if no stat bonus

        if getattr(chain_acc, 'slot', 'ring') == 'amulet':
            g.player.amulet_slot = chain_acc
        else:
            g.player.accessory_slots[0] = chain_acc
        apply_tier_bonuses(g.player, chain_acc, tier)

        stats_before = (g.player.STR, g.player.CON, g.player.DEX,
                        g.player.INT, g.player.WIS, g.player.PER)
        passives_before = dict(chain_acc._chain_passives)
        stat_bonuses_before = dict(chain_acc._chain_stat_bonuses)

        g2, _ = _save_then_load(g)

        if getattr(chain_acc, 'slot', 'ring') == 'amulet':
            restored = g2.player.amulet_slot
        else:
            restored = g2.player.accessory_slots[0]
        assert restored is not None
        assert restored.achieved_tier == tier

        stats_after = (g2.player.STR, g2.player.CON, g2.player.DEX,
                       g2.player.INT, g2.player.WIS, g2.player.PER)
        assert stats_after == stats_before
        assert dict(restored._chain_passives) == passives_before
        assert dict(restored._chain_stat_bonuses) == stat_bonuses_before
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# 3. Chain-equip regen_bonus survives reload (player.regen_bonus)
# ---------------------------------------------------------------------------

def test_chain_equip_regen_bonus_round_trip():
    """An item with passive regen_bonus tier_bonus updates player.regen_bonus
    on equip; the value must survive save/load."""
    name = '__test_lifecycle_regen__'
    try:
        from items import load_items
        from chain_equip import apply_tier_bonuses, is_chain_equip

        # Find any chain-equip item with regen_bonus in any tier
        regen_item = None
        regen_tier = 0
        for category in ('armor', 'accessory', 'shield'):
            for it in load_items(category):
                if not is_chain_equip(it):
                    continue
                for t_key, bonuses in it.tier_bonuses.items():
                    if 'regen_bonus' in bonuses:
                        regen_item = it
                        regen_tier = int(t_key)
                        break
                if regen_item:
                    break
            if regen_item:
                break

        if regen_item is None:
            import pytest
            pytest.skip("no chain-equip item with regen_bonus tier_bonus in JSON")

        g = _new_game(name)
        if isinstance(regen_item, type(load_items('armor')[0])) and \
                hasattr(regen_item, 'slot') and regen_item.slot in (
                'head', 'body', 'arms', 'hands', 'legs', 'feet', 'cloak', 'shirt'):
            from items import ARMOR_SLOTS
            idx = ARMOR_SLOTS.index(regen_item.slot)
            g.player.armor_slots[idx] = regen_item
        elif getattr(regen_item, 'slot', '') == 'shield':
            g.player.shield = regen_item
        else:
            g.player.accessory_slots[0] = regen_item

        apply_tier_bonuses(g.player, regen_item, regen_tier)
        regen_before = g.player.regen_bonus
        assert regen_before > 0, "expected non-zero regen after apply"

        g2, _ = _save_then_load(g)
        assert g2.player.regen_bonus == regen_before
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# 4. Chain-equip mp_bonus: max_mp on player + _chain_mp_bonus on item
# ---------------------------------------------------------------------------

def test_chain_equip_mp_bonus_round_trip():
    """robe_of_the_magus T1 adds passive_mp_bonus + stat_bonus_INT. After
    reload, max_mp/INT and the item-side _chain_mp_bonus must match."""
    name = '__test_lifecycle_mp__'
    try:
        from items import load_items
        from chain_equip import apply_tier_bonuses

        armors = load_items('armor')
        robe = next((a for a in armors if a.id == 'robe_of_the_magus'), None)
        if robe is None:
            import pytest
            pytest.skip("robe_of_the_magus not in JSON")

        g = _new_game(name)
        mp_before = g.player.max_mp
        int_before = g.player.INT

        g.player.armor_slots[1] = robe  # body
        apply_tier_bonuses(g.player, robe, 1)
        mp_after = g.player.max_mp
        int_after = g.player.INT
        assert mp_after > mp_before
        assert int_after > int_before
        assert robe._chain_mp_bonus == 5

        g2, _ = _save_then_load(g)
        restored = g2.player.armor_slots[1]
        assert g2.player.max_mp == mp_after
        assert g2.player.INT == int_after
        assert restored._chain_mp_bonus == 5
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# 5. Corpse id_level survives pickle as property + __setstate__ migration
# ---------------------------------------------------------------------------

def test_corpse_id_level_round_trip():
    """A corpse with id_level=3 should reload with id_level=3 and
    lore_identified=False (since lore_identified is a property of id_level>=4)."""
    name = '__test_lifecycle_corpse__'
    try:
        from items import Corpse

        g = _new_game(name)
        c = Corpse('test wolf', 'test_wolf', 0, 0, harvest_tier=1,
                   harvest_threshold=5, ingredient_id='wolf_meat', lore='lore')
        c.id_level = 3
        g.player.inventory.append(c)

        g2, _ = _save_then_load(g)
        restored = next(i for i in g2.player.inventory if isinstance(i, Corpse))
        assert restored.id_level == 3
        assert restored.lore_identified is False  # property: needs >=4

        # And setter still works post-reload
        restored.lore_identified = True
        assert restored.id_level == 4
        assert restored.lore_identified is True
    finally:
        _cleanup(name)


def test_corpse_legacy_setstate_migration():
    """Old saves stored lore_identified as a plain attribute. __setstate__
    must drop the attribute and translate it to id_level >= 4."""
    from items import Corpse

    legacy_state = {
        'id': 'corpse_test', 'name': 'test corpse', 'symbol': '%',
        'color': (160, 60, 60), 'weight': 5.0, 'item_class': 'corpse',
        'min_level': 1, 'count': 1, 'identified': True,
        'unidentified_name': 'test corpse', 'buc': 'uncursed',
        'buc_known': False, 'lore': '', 'set_id': '', 'set_name': '',
        'mastery_blessing': None, 'is_unique': False,
        'peak_floor': 0, 'spread': 10, 'peak_weight': 0.0,
        'monster_id': 'test', 'monster_name': 'test',
        'harvest_tier': 1, 'harvest_threshold': 5,
        'ingredient_id': 'wolf_meat', 'monster_def': {},
        'lore_identified': True,   # legacy attribute, must be migrated
        'x': 0, 'y': 0,
    }
    # Instantiate without calling __init__ then apply state
    c = Corpse.__new__(Corpse)
    c.__setstate__(legacy_state)
    # lore_identified should now be a property derived from id_level
    assert 'lore_identified' not in c.__dict__, "legacy attr not removed"
    assert c.id_level >= 4, f"id_level should be >=4 (was {c.id_level})"
    assert c.lore_identified is True

    # Round-trip through pickle to confirm
    b = pickle.dumps(c)
    c2 = pickle.loads(b)
    assert c2.id_level == c.id_level
    assert c2.lore_identified is True


# ---------------------------------------------------------------------------
# 6. LevelManager: planned + placed mini-bosses
# ---------------------------------------------------------------------------

def test_planned_mini_bosses_round_trip():
    """LevelManager._planned_mini_bosses is rolled at run start; must
    survive save/load identically."""
    name = '__test_lifecycle_minibosses__'
    try:
        g = _new_game(name)
        planned_before = dict(g.level_mgr._planned_mini_bosses)
        placed_before = set(g.level_mgr._placed_mini_bosses)
        placed_before.add('test_already_placed_boss')
        g.level_mgr._placed_mini_bosses = placed_before

        g2, _ = _save_then_load(g)
        assert dict(g2.level_mgr._planned_mini_bosses) == planned_before
        assert set(g2.level_mgr._placed_mini_bosses) == placed_before
    finally:
        _cleanup(name)


def test_legacy_level_mgr_missing_planned_mini_bosses_backfills():
    """Old saves predate the _planned_mini_bosses pre-roll. load_state must
    backfill the field on the *restored* level_mgr (not the freshly-built
    one in __init__)."""
    name = '__test_lifecycle_legacy_lm__'
    try:
        from save_system import save_game, load_game

        g = _new_game(name)
        assert save_game(g)
        state = load_game(name)
        # Simulate an old save by stripping the field on the level_mgr in state
        delattr(state['level_mgr'], '_planned_mini_bosses')
        assert not hasattr(state['level_mgr'], '_planned_mini_bosses')

        g2 = _new_game(name)
        g2.load_state(state)
        # After load_state, g2.level_mgr is state['level_mgr'] and must have
        # the field freshly rolled.
        assert hasattr(g2.level_mgr, '_planned_mini_bosses')
        assert isinstance(g2.level_mgr._planned_mini_bosses, dict)
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# 7. Per-floor chain_passive_charges + per-run once-per-run set
# ---------------------------------------------------------------------------

def test_chain_passive_charges_round_trip():
    """Per-floor charges (consumed mid-floor) and per-run once-set must
    survive save/load — these gate things like free_cast_once_per_floor."""
    name = '__test_lifecycle_charges__'
    try:
        g = _new_game(name)
        g.player._chain_passive_charges = {
            'free_cast_once_per_floor': True,
            'free_escape_once_per_floor': True,
        }
        g.player._chain_passive_once_per_run = {'psychopomp_step', 'reassembly'}
        g.player._gorgoneion_used_this_floor = True
        g.player._chain_no_move_counter = 3
        g.player._chain_move_counter = 7

        g2, _ = _save_then_load(g)
        assert g2.player._chain_passive_charges == {
            'free_cast_once_per_floor': True,
            'free_escape_once_per_floor': True,
        }
        assert g2.player._chain_passive_once_per_run == {'psychopomp_step', 'reassembly'}
        assert g2.player._gorgoneion_used_this_floor is True
        assert g2.player._chain_no_move_counter == 3
        assert g2.player._chain_move_counter == 7
    finally:
        _cleanup(name)


def test_legacy_player_missing_chain_charges_backfills():
    """Old saves lack the chain-equip charge fields. load_state must
    backfill them with empty defaults."""
    name = '__test_lifecycle_legacy_charges__'
    try:
        from save_system import save_game, load_game

        g = _new_game(name)
        assert save_game(g)
        state = load_game(name)
        # Strip chain-equip charge fields
        for attr in ('_chain_passive_charges', '_chain_passive_once_per_run',
                     '_gorgoneion_used_this_floor', '_chain_move_counter',
                     '_chain_no_move_counter', 'damage_resistances',
                     'regen_bonus', 'unlocked_monster_class_masteries'):
            if hasattr(state['player'], attr):
                delattr(state['player'], attr)

        g2 = _new_game(name)
        g2.load_state(state)
        assert g2.player._chain_passive_charges == {}
        assert g2.player._chain_passive_once_per_run == set()
        assert g2.player._gorgoneion_used_this_floor is False
        assert g2.player._chain_move_counter == 0
        assert g2.player._chain_no_move_counter == 0
        assert g2.player.damage_resistances == {}
        assert g2.player.regen_bonus == 0
        assert g2.player.unlocked_monster_class_masteries == {}
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# 8. Family mastery (unlocked_monster_class_masteries) round-trip
# ---------------------------------------------------------------------------

def test_family_mastery_round_trip():
    """The SET of mastered families (corpse-identify chain-5) survives save/load.
    Blessings are canonical: on load they are re-synced to the current
    MONSTER_FAMILY_BLESSINGS, so a blessing redesign (e.g. the 2026-06 save-bonus
    conversion of fey/undead) auto-updates returning players rather than leaving
    them holding a stale/inert blessing."""
    from monster_classes import MONSTER_FAMILY_BLESSINGS as MFB
    name = '__test_lifecycle_family__'
    try:
        g = _new_game(name)
        # Seed with deliberately STALE blessing shapes (pre-conversion forms).
        g.player.unlocked_monster_class_masteries = {
            'dragon': {'kind': 'damage_vs_tag', 'tag': 'dragon', 'value': 2, 'desc': '_'},
            'undead': {'kind': 'turn_undead', 'value': 3},          # obsolete kind
            'fey':    {'kind': 'resist_charm', 'value': 1},          # pre-conversion
        }

        g2, _ = _save_then_load(g)
        fams = g2.player.unlocked_monster_class_masteries
        # Same families remembered...
        assert set(fams) == {'dragon', 'undead', 'fey'}
        # ...and each blessing re-synced to the current canonical definition.
        assert fams['fey'] == MFB['fey']        # now a WIS save_bonus
        assert fams['undead'] == MFB['undead']  # now a CON save_bonus
        assert fams['dragon'] == MFB['dragon']
    finally:
        _cleanup(name)


def test_combat_game_ref_does_not_block_save():
    """Regression for the silent save-Surface loss: player._combat_game_ref is a
    Game backref set during combat (game_combat) that holds the pygame screen,
    fonts, and quiz-engine callbacks. It made the player unpicklable, so a save
    made after ANY fight failed (and atomic-write then left no file). Player
    __getstate__ now drops it; the save must succeed."""
    name = '__test_lifecycle_combatref__'
    try:
        g = _new_game(name)
        g.player._combat_game_ref = g     # simulate post-combat state
        g.turn_count = 77
        g2, _ = _save_then_load(g)         # must NOT fail (this was the bug)
        assert g2.turn_count == 77
        assert getattr(g2.player, '_combat_game_ref', None) is None
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# 9. Cross-floor: descending then returning preserves floor state
# ---------------------------------------------------------------------------

def test_cross_floor_state_via_level_mgr_save():
    """Descend, save, load — return to floor 1 — same monsters/items as
    before the descent. Catches level_mgr._saved pickling issues."""
    name = '__test_lifecycle_descent__'
    try:
        g = _new_game(name)
        # Snapshot floor 1
        floor1_monster_n = len(g.monsters)
        floor1_item_n = len(g.ground_items)

        # Descend to floor 2 — saves floor 1 into level_mgr._saved
        g._change_level(2, enter_from_top=True)
        assert g.dungeon_level == 2
        assert 1 in g.level_mgr._saved

        g2, _ = _save_then_load(g)
        assert g2.dungeon_level == 2
        assert 1 in g2.level_mgr._saved

        # Ascend back to floor 1 — should restore the same monsters/items
        g2._change_level(1, enter_from_top=False)
        assert g2.dungeon_level == 1
        assert len(g2.monsters) == floor1_monster_n
        assert len(g2.ground_items) == floor1_item_n
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# 10. Status effects with durations
# ---------------------------------------------------------------------------

def test_status_effects_durations_round_trip():
    """Active status effects (with durations and permanent -1 entries)
    must survive save/load intact."""
    name = '__test_lifecycle_status__'
    try:
        g = _new_game(name)
        g.player.status_effects.update({
            'blessed': 50,
            'hasted': 25,
            'poisoned': 10,
            'fire_resist': -1,   # permanent (-1)
            'invisible': 5,
        })

        g2, _ = _save_then_load(g)
        assert g2.player.status_effects == {
            'blessed': 50,
            'hasted': 25,
            'poisoned': 10,
            'fire_resist': -1,
            'invisible': 5,
        }
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# 11. Per-run flags (npc encounters, lore items, judgment)
# ---------------------------------------------------------------------------

def test_per_run_flags_round_trip():
    """Game-level per-run flags (_encountered_npcs, _lore_placed,
    _judgment_resolved, etc.) must survive save/load."""
    name = '__test_lifecycle_flags__'
    try:
        g = _new_game(name)
        g._encountered_npcs.add('priest')
        g._encountered_flavor_npcs.add('merchant')
        g._lore_placed.add('shimmer')
        g._npc_triggered_items.add('rosary')
        g.karma = 5
        g.player_title = 'Paladin'
        g._abaddon_empowered = True
        g._locusts_strengthened = True
        g._judgment_resolved = True

        g2, _ = _save_then_load(g)
        assert 'priest' in g2._encountered_npcs
        assert 'merchant' in g2._encountered_flavor_npcs
        assert 'shimmer' in g2._lore_placed
        assert 'rosary' in g2._npc_triggered_items
        assert g2.karma == 5
        assert g2.player_title == 'Paladin'
        assert g2._abaddon_empowered is True
        assert g2._locusts_strengthened is True
        assert g2._judgment_resolved is True
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# 12. Quirk system: game ref is re-bound on load
# ---------------------------------------------------------------------------

def test_quirk_system_round_trip_and_game_rebind():
    """quirk_system has a `.game` back-reference that must be re-bound to
    the new Game instance after load (the original game is gone)."""
    name = '__test_lifecycle_quirks__'
    try:
        g = _new_game(name)
        g.player.unlocked_quirks.add('hermes')
        g.player.quirk_progress['hermes_active'] = True
        g.player.power_cooldowns['blink'] = 50
        g.player.power_uses['blink'] = 3
        g.player.quiz_timer_bonuses['math'] = 5

        g2, _ = _save_then_load(g)
        assert g2.player.unlocked_quirks == {'hermes'}
        assert g2.player.quirk_progress == {'hermes_active': True}
        assert g2.player.power_cooldowns == {'blink': 50}
        assert g2.player.power_uses == {'blink': 3}
        assert g2.player.quiz_timer_bonuses == {'math': 5}
        # Critical: the game backreference is the new game, not the old one
        assert g2.quirk_system.game is g2
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# 13. Magic carrot + ethereal unicorn one-shot spawn state
# ---------------------------------------------------------------------------


def test_magic_carrot_and_unicorn_spawn_state_round_trip():
    """One-shot spawns (carrot L1-19, unicorn L21-39) randomize their target
    floor on first eligible entry, then guard against respawn with a
    `_spawned` boolean. Both fields must survive save/load — otherwise a
    reload re-randomizes the target and the player can get TWO of the
    one-shot item per run."""
    name = '__test_lifecycle_oneshots__'
    try:
        g = _new_game(name)
        g._magic_carrot_spawned = True
        g._magic_carrot_target_level = 7
        g._unicorn_spawned = False
        g._unicorn_target_level = 25

        g2, _ = _save_then_load(g)
        assert g2._magic_carrot_spawned is True
        assert g2._magic_carrot_target_level == 7
        assert g2._unicorn_spawned is False
        assert g2._unicorn_target_level == 25
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# 14. Mastery state (unique + class) + philosopher career arc
# ---------------------------------------------------------------------------

def test_mastery_and_career_arc_round_trip():
    """unlocked_masteries (per-item) + unlocked_class_masteries (per-class
    of common item) + philosopher_tier_claimed + philosophers_mantle +
    total_identifies must all survive save/load."""
    name = '__test_lifecycle_mastery__'
    try:
        g = _new_game(name)
        g.player.unlocked_masteries['soul_reaver'] = {
            'kind': 'extra_damage', 'value': 5, 'desc': 'Vorpal'
        }
        g.player.unlocked_class_masteries['ring_of_strength'] = {
            'kind': 'class_acc_stat_bonus', 'value': 2,
            'desc': '+2 STR while equipped'
        }
        g.player.total_identifies = 75
        g.player.philosopher_tier_claimed.add(25)
        g.player.philosopher_tier_claimed.add(75)
        g.player.philosophers_mantle = True
        g.player.known_class_ids.add('ring_of_strength')

        g2, _ = _save_then_load(g)
        assert g2.player.unlocked_masteries == {
            'soul_reaver': {'kind': 'extra_damage', 'value': 5, 'desc': 'Vorpal'}
        }
        assert g2.player.unlocked_class_masteries == {
            'ring_of_strength': {'kind': 'class_acc_stat_bonus', 'value': 2,
                                  'desc': '+2 STR while equipped'}
        }
        assert g2.player.total_identifies == 75
        assert g2.player.philosopher_tier_claimed == {25, 75}
        assert g2.player.philosophers_mantle is True
        assert 'ring_of_strength' in g2.player.known_class_ids
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# 15. Permadeath lifecycle: the save is removed ONLY when the run ends,
#     never on load. (Regression: load used to delete the save before
#     load_state ran, so a partial restore or a crash destroyed progress.)
# ---------------------------------------------------------------------------

def test_core_fields_round_trip():
    """The headline fields a player checks after loading -- floor, turn, HP,
    weapon -- survive the full save/load cycle, and the load-summary popup
    reports them."""
    name = '__test_lifecycle_core__'
    try:
        g = _new_game(name)
        g.turn_count = 137
        g.dungeon_level = 4
        g.player.hp = 7
        weapon_name = g.player.weapon.name if g.player.weapon else None

        g2, _ = _save_then_load(g)
        assert g2.turn_count == 137
        assert g2.dungeon_level == 4
        assert g2.player.hp == 7
        if weapon_name is not None:
            assert g2.player.weapon is not None
            assert g2.player.weapon.name == weapon_name

        # The visible load confirmation reads these fields; it must build a
        # popup that names the restored floor.
        g2._show_load_summary_popup()
        assert g2.popup_data['title'] == 'JOURNEY RESTORED'
        assert any(str(g2.dungeon_level) in line for line in g2.popup_data['lines'])
    finally:
        _cleanup(name)


def test_failed_save_does_not_destroy_existing_save():
    """A save that fails to pickle (an unpicklable pygame Surface sneaks into
    state) must NOT truncate or destroy the prior good save. Regression for the
    0-byte save-wipe: save_game opened the real file in 'wb' (truncating it)
    before pickling, so a mid-dump failure wiped the existing save. The fix
    writes to a temp file and only atomically replaces on full success."""
    name = '__test_lifecycle_atomic__'
    try:
        from save_system import save_game, load_game, save_exists

        g = _new_game(name)
        g.turn_count = 99
        assert save_game(g), "baseline good save should succeed"
        assert save_exists(name)

        # Inject an unpicklable object into saved state, then save again.
        g.ground_items.append(pygame.Surface((4, 4)))
        assert save_game(g) is False, "save with a Surface in state should fail"

        # The prior good save must still be intact and loadable.
        st = load_game(name)
        assert st is not None, "a failed save destroyed the existing save!"
        assert st.get('turn_count') == 99
    finally:
        _cleanup(name)


def test_load_does_not_consume_save():
    """Loading a save must NOT delete it. This is the core fix: the save now
    persists on disk as a recovery anchor until the run actually ends, so a
    silent load_state failure or a hard process kill can't destroy progress."""
    name = '__test_lifecycle_load_persist__'
    try:
        from save_system import save_game, load_game, save_exists

        g = _new_game(name)
        g.turn_count = 42
        assert save_game(g)
        assert save_exists(name)

        # Mirror main()'s load path: read the state and restore it -- but do
        # NOT delete. The save file must still be on disk afterwards.
        state = load_game(name)
        assert state is not None
        g2 = _new_game(name)
        g2.load_state(state)
        assert save_exists(name), "loading a save must NOT delete it (regression)"
    finally:
        _cleanup(name)


def test_game_over_deletes_save():
    """Permadeath still works: ending the run via _on_game_over deletes the
    save. Combined with test_load_does_not_consume_save, this pins the contract
    'removed on death, not on load.'"""
    name = '__test_lifecycle_permadeath__'
    try:
        from save_system import save_game, save_exists

        g = _new_game(name)
        assert save_game(g)
        assert save_exists(name)

        g.defeat_reason = 'died'
        g._on_game_over()   # writes bones, no-op sound, and deletes the save
        assert not save_exists(name), "death must delete the save (permadeath)"
    finally:
        _cleanup(name)


def test_load_looks_valid_guard():
    """_load_looks_valid accepts a faithful restore and rejects a broken one
    (missing dungeon / mismatched floor). The caller uses this to refuse to
    enter the game loop on a bad load, so the intact on-disk save can't be
    overwritten on quit."""
    name = '__test_lifecycle_guard__'
    try:
        from save_system import save_game, load_game

        g = _new_game(name)
        assert save_game(g)
        state = load_game(name)
        assert state is not None

        g_ok = _new_game(name)
        g_ok.load_state(state)
        assert g_ok._load_looks_valid(state) is True

        # Dungeon dropped -> invalid
        g_bad = _new_game(name)
        g_bad.load_state(state)
        g_bad.dungeon = None
        assert g_bad._load_looks_valid(state) is False

        # Floor mismatch -> invalid
        g_bad2 = _new_game(name)
        g_bad2.load_state(state)
        g_bad2.dungeon_level = (state.get('dungeon_level') or 1) + 99
        assert g_bad2._load_looks_valid(state) is False
    finally:
        _cleanup(name)
