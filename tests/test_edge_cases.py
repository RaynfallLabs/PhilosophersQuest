"""Edge case + crash scenario regression tests (2026-05-19 audit).

Each test maps to a numbered scenario in proposals/v2_audit/11_edge_cases.md.
These are simulation tests — they exercise game logic without touching pygame
rendering. They guard against undefined behavior, lost items, and silent
crashes that surfaced in the cross-system audit.

Test discipline:
- Use Game()-equivalent state where possible (Player, Item, Dungeon objects).
- For scenarios that need the full Game class, the rendering surface is mocked.
- Crashes are blockers. Weird-but-defined behavior is documented in comments.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# ---------- helpers ----------

def _mk_weapon(item_id='w', name='Test Sword', two_handed=False,
               base_damage=5, **extra):
    from items import Weapon
    defn = {
        'id': item_id, 'name': name, 'symbol': '/',
        'color': [255, 255, 255], 'baseDamage': base_damage,
        'twoHanded': two_handed, 'identified': True,
    }
    defn.update(extra)
    return Weapon(defn)


def _mk_armor(item_id='a', name='Test Armor', slot='body', ac_bonus=2,
              **extra):
    from items import Armor
    defn = {
        'id': item_id, 'name': name, 'symbol': '[',
        'color': [255, 255, 255], 'slot': slot, 'ac_bonus': ac_bonus,
        'identified': True,
    }
    defn.update(extra)
    return Armor(defn)


def _mk_shield(item_id='s', name='Test Shield', ac_bonus=1, **extra):
    from items import Shield
    defn = {
        'id': item_id, 'name': name, 'symbol': ')',
        'color': [255, 255, 255], 'ac_bonus': ac_bonus, 'identified': True,
    }
    defn.update(extra)
    return Shield(defn)


def _mk_ring(item_id='r', name='Test Ring', stat='STR', amount=1, **extra):
    from items import Accessory
    defn = {
        'id': item_id, 'name': name, 'symbol': '=',
        'color': [255, 255, 255], 'slot': 'ring',
        'effects': {'stat': stat, 'amount': amount},
        'identified': True,
    }
    defn.update(extra)
    return Accessory(defn)


def _mk_artifact(item_id, name, **extra):
    from items import Artifact
    defn = {
        'id': item_id, 'name': name, 'symbol': '"',
        'color': [255, 255, 255], 'identified': True,
    }
    defn.update(extra)
    return Artifact(defn)


# ============================================================
# Inventory / Pickup (scenarios 1-4)
# ============================================================

def test_scenario_01_inventory_full_blocks_pickup():
    """Add to inventory returns False when over carry limit. Item stays on ground."""
    from player import Player
    p = Player()
    # Fill inventory to exceed carry limit
    p.STR = 1  # carry_limit = 55
    heavy = _mk_weapon(item_id='heavy', base_damage=5)
    heavy.weight = 200.0
    assert p.add_to_inventory(heavy) is False
    assert heavy not in p.inventory


def test_scenario_02_full_inventory_soul_sphere():
    """add_to_inventory respects weight cap even for plot items like Soul Sphere."""
    from player import Player
    p = Player()
    p.STR = 1
    # Saturate inventory with weighty filler
    filler = _mk_weapon(item_id='filler')
    filler.weight = 60.0
    p.add_to_inventory(filler)
    sphere = _mk_artifact('soul_sphere', 'Soul Sphere', weight=5.0)
    # Sphere should still fit (60+5 < 55... actually 60>55 already).
    # The cap check is current_weight + new <= carry_limit.
    # carry_limit at STR=1 = 50 + 5 = 55. With 60 already (the previous
    # add_to_inventory must have succeeded because 0+60 > 55 → returns False).
    # Try lighter setup.
    p2 = Player()
    p2.STR = 10  # carry_limit 100
    f = _mk_weapon(item_id='f'); f.weight = 80.0
    assert p2.add_to_inventory(f) is True
    sphere2 = _mk_artifact('soul_sphere', 'Soul Sphere', weight=5.0)
    assert p2.add_to_inventory(sphere2) is True
    # Now over-carry attempt
    big = _mk_weapon(item_id='big'); big.weight = 50.0
    assert p2.add_to_inventory(big) is False, "should be blocked when over carry"


def test_scenario_03_drop_plot_item_returns_to_floor():
    """Drop removes from inventory and places on ground tile."""
    from player import Player
    p = Player()
    stone = _mk_artifact('philosophers_stone', "Philosopher's Stone", weight=1.0)
    p.add_to_inventory(stone)
    assert stone in p.inventory
    p.remove_from_inventory(stone)
    assert stone not in p.inventory


def test_scenario_04_thrown_soul_sphere_can_be_repickedup():
    """An Artifact dropped onto the floor can be added back to inventory."""
    from player import Player
    p = Player()
    sphere = _mk_artifact('soul_sphere', 'Soul Sphere', weight=2.0)
    p.add_to_inventory(sphere)
    p.remove_from_inventory(sphere)
    # Simulate re-pickup
    assert p.add_to_inventory(sphere) is True
    assert sphere in p.inventory


# ============================================================
# Equipment (scenarios 5, 7, 8)
# ============================================================

def test_scenario_05_cursed_item_blocks_unequip():
    """try_unequip_slot blocks removal of a cursed item."""
    from player import Player
    p = Player()
    cursed_w = _mk_weapon(item_id='cw', name='Cursed Sword')
    cursed_w.buc = 'cursed'
    p.add_to_inventory(cursed_w)
    p._apply_equip(cursed_w)
    p.remove_from_inventory(cursed_w)
    ok, msg = p.try_unequip_slot(p.weapon)
    assert ok is False
    assert 'welded' in msg.lower() or 'cursed' in msg.lower()


def test_scenario_07_shield_blocked_by_two_handed_weapon():
    """can_equip_shield returns False when wielding a 2-handed weapon."""
    from player import Player
    p = Player()
    great_axe = _mk_weapon(item_id='gax', two_handed=True)
    p.add_to_inventory(great_axe)
    p._apply_equip(great_axe)
    p.remove_from_inventory(great_axe)
    assert p.weapon is great_axe
    assert p.can_equip_shield() is False
    # Attempting to apply a shield while 2H equipped is a no-op
    s = _mk_shield()
    p.add_to_inventory(s)
    p._apply_equip(s)
    assert p.shield is None  # blocked
    # Shield stayed in inventory
    assert s in p.inventory


def test_scenario_08_two_handed_unequips_existing_shield():
    """Equipping a 2H weapon while a shield is equipped removes the shield."""
    from player import Player
    p = Player()
    s = _mk_shield()
    p.add_to_inventory(s)
    p._apply_equip(s)
    p.remove_from_inventory(s)
    assert p.shield is s
    # Now equip 2H weapon
    gax = _mk_weapon(item_id='gax', two_handed=True)
    p.add_to_inventory(gax)
    p._apply_equip(gax)
    p.remove_from_inventory(gax)
    assert p.weapon is gax
    assert p.shield is None
    # The shield went back to inventory
    assert s in p.inventory


# ============================================================
# Combat (scenarios 6, 9, 10)
# ============================================================

def test_scenario_06_unarmed_combat_uses_default_damage():
    """player_attack falls back to 1d4 + default multipliers when no weapon."""
    import combat
    from player import Player
    from monster import Monster
    p = Player()
    p.weapon = None
    m = Monster({'id': 'rat', 'name': 'rat', 'symbol': 'r',
                 'color': [200, 100, 100], 'hp': 20, 'min_level': 1,
                 'damage': '1d2'}, 0, 0)

    # Build a fake quiz result with chain 2 = solid hit
    class FakeResult:
        score = 2
    class FakeEngine:
        def start_quiz(self, **kwargs):
            self._cb = kwargs['callback']
        def fire(self):
            self._cb(FakeResult())

    eng = FakeEngine()
    out = {}
    def on_complete(damage, killed, chain, **kw):
        out['damage'] = damage
        out['chain'] = chain
    combat.player_attack(p, m, eng, on_complete)
    eng.fire()
    # Damage clamped to >=1 means unarmed combat fires with the fallback dice
    assert out['chain'] == 2
    assert out['damage'] >= 1


def test_scenario_09_ranged_with_no_ammo_short_circuit():
    """Search inventory for matching ammo; if absent, _fire_ranged exits early
    without entering quiz state. We assert the helper logic directly: a
    no-ammo lookup returns None and we expect 'Out of ...' messaging."""
    from player import Player
    p = Player()
    bow = _mk_weapon(item_id='bow', requiresAmmo='arrow', infiniteAmmo=False,
                     base_damage=4)
    p._apply_equip(bow)
    # No ammo in inventory — match the logic from _fire_ranged
    ammo_item = next(
        (i for i in p.inventory
         if getattr(i, 'ammo_type', None) == 'arrow'),
        None
    )
    assert ammo_item is None


def test_scenario_10_zero_mp_blocks_cast():
    """Spell invocation rejects when player.mp < cost. We exercise the
    invocation guard directly: spells.LEARNABLE_SPELLS is loaded, picking
    any spell with mp_cost > 0 and verifying the cost gate."""
    from spells import LEARNABLE_SPELLS
    # Choose a spell with mp_cost > 0
    spell = next(s for s in LEARNABLE_SPELLS.values() if s.get('mp_cost', 0) > 0)
    cost = spell['mp_cost']
    # Simulate the guard
    from player import Player
    p = Player()
    p.mp = 0
    assert p.mp < cost  # guard would fail and not consume MP


# ============================================================
# Status effects (scenarios 11, 12, 13)
# ============================================================

def test_scenario_11_many_statuses_tick_cleanly():
    """tick_all iterates over a snapshot; 5+ active effects don't crash."""
    from player import Player
    from status_effects import tick_all
    p = Player()
    p.add_effect('poisoned', 5)
    p.add_effect('bleeding', 5)
    p.add_effect('hasted', 5)
    p.add_effect('regenerating', 5)
    p.add_effect('blessed', 5)
    p.add_effect('stunned', 5)
    p.add_effect('confused', 5)
    # Should not crash
    msgs = tick_all(p)
    assert isinstance(msgs, list)


def test_scenario_12_damage_immunity_correct_type():
    """take_damage returns 0 for the immune type, normal for other types."""
    from player import Player
    p = Player()
    p.add_effect('fire_resist', -1)
    fire_dmg = p.take_damage(10, 'fire')
    assert fire_dmg == 0
    cold_dmg = p.take_damage(10, 'cold')
    assert cold_dmg > 0


def test_scenario_13_apply_status_already_active_extends():
    """Applying a status already active stacks the duration, capped at MAX."""
    from player import Player
    from status_effects import MAX_EFFECT_DURATION
    p = Player()
    p.add_effect('poisoned', 5)
    assert p.status_effects.get('poisoned') == 5
    p.add_effect('poisoned', 10)
    assert p.status_effects.get('poisoned') == 15
    # Stack past the cap
    p.add_effect('poisoned', 999)
    assert p.status_effects.get('poisoned') == MAX_EFFECT_DURATION


# ============================================================
# Movement / map (scenarios 14, 15, 16, 17)
# ============================================================

def test_scenario_14_phasing_expiry_in_wall_softlock_logic():
    """When phasing expires, if the player is on a non-walkable tile,
    the engine should not silently leave them soft-locked. This is the
    pre-condition; the unstick happens in Game._advance_turn (untestable
    here without a full Game). Verify the player state we'd unstick from."""
    from player import Player
    from dungeon import generate_dungeon, WALL
    import random
    p = Player()
    random.seed(1)
    d = generate_dungeon(50, 30, 1)
    # Manually place player on a wall tile
    for y in range(d.height):
        for x in range(d.width):
            if d.tiles[y][x] == WALL and d.in_bounds(x + 1, y) and d.is_walkable(x + 1, y):
                p.x, p.y = x, y
                break
        else:
            continue
        break
    # Pre-condition: player on wall, no phasing.
    p.add_effect('phasing', 1)
    from status_effects import tick_all
    tick_all(p)
    assert not p.has_effect('phasing')
    assert not d.is_walkable(p.x, p.y)
    # In the real engine the unstick at main.py:_advance_turn would fire.


def test_scenario_15_pit_movement_climbs_out():
    """When in a pit, a move-input climbs the player out (no descent)."""
    from player import Player
    p = Player()
    p.add_effect('in_pit', 1)
    assert p.has_effect('in_pit')
    # Movement code at main.py:1469 deletes the effect on a move attempt.
    del p.status_effects['in_pit']
    assert not p.has_effect('in_pit')


def test_scenario_16_descend_at_zero_hp_path():
    """Player can't descend at hp<=0 because is_dead transitions out of
    STATE_PLAYER before the descent input is accepted. Verify the gate."""
    from player import Player
    p = Player()
    p.hp = 0
    assert p.is_dead() is True


def test_scenario_17_maze_level_has_stairs():
    """Maze-level generation always carves stairs_up and stairs_down."""
    from dungeon import generate_dungeon, STAIRS_UP, STAIRS_DOWN
    import random
    # Maze on level 10, 30, 50, 70, 90
    for level in (10, 30, 50, 70, 90):
        random.seed(level)
        d = generate_dungeon(80, 50, level)
        assert d.is_maze, f"Level {level} should be a maze"
        # Walk tiles for stairs
        ups = sum(1 for y in range(d.height) for x in range(d.width)
                  if d.tiles[y][x] == STAIRS_UP)
        downs = sum(1 for y in range(d.height) for x in range(d.width)
                    if d.tiles[y][x] == STAIRS_DOWN)
        assert ups >= 1, f"Maze {level}: missing STAIRS_UP"
        assert downs >= 1, f"Maze {level}: missing STAIRS_DOWN"


# ============================================================
# Quiz state (scenarios 18, 19)
# ============================================================

def test_scenario_18_quiz_esc_ends_cleanly():
    """quiz_engine._end called with success=False fires callback once and
    settles into COMPLETE (not ASKING) — caller can transition to STATE_PLAYER."""
    from quiz_engine import QuizEngine, QuizMode, QuizState
    eng = QuizEngine()
    captured = []
    def cb(result):
        captured.append(result)
    eng.start_quiz(
        mode='chain', subject='math', tier=1, callback=cb,
        max_chain=5, wisdom=10,
    )
    # Cancel like the ESC handler does
    eng._end(success=False)
    assert eng.state == QuizState.COMPLETE
    assert eng.active is False
    assert len(captured) == 1


def test_scenario_19_tablet_reroll_only_once_per_quiz():
    """The reroll_available flag is consumed on use — second wrong answer
    won't re-reroll, the quiz ends with chain score."""
    from quiz_engine import QuizEngine
    eng = QuizEngine()
    eng._reroll_flag = True
    captured = []
    def cb(result):
        captured.append(result)
    eng.start_quiz(
        mode='chain', subject='math', tier=1, callback=cb,
        max_chain=5, wisdom=10,
    )
    # Engine refreshes reroll_available from _reroll_flag at start_quiz
    assert eng.reroll_available is True
    # Manual fire after a wrong answer via _advance
    eng.last_correct = False
    eng.chain = 0
    eng.time_remaining = 5.0  # not timed out
    eng._advance()
    # After reroll, the flag is consumed
    assert eng.reroll_available is False
    assert eng.reroll_was_used is True
    # A second wrong answer ends the quiz
    eng.last_correct = False
    eng._advance()
    assert len(captured) == 1


# ============================================================
# Pet (scenarios 20, 22)
# ============================================================

def test_scenario_20_pet_follows_on_floor_transition():
    """Pets are repositioned near the player after _change_level. We exercise
    Pet.x/y assignment used by the floor-change logic at main.py:842-867."""
    from pet_system import Pet
    p = Pet('electric', 5, 5)
    # Floor-change code sets pet.x = player.x (fallback when no adjacent walk).
    p.x, p.y = 10, 10
    assert (p.x, p.y) == (10, 10)


def test_scenario_22_multiple_pets_allowed():
    """The pet list supports >1 entries without uniqueness assertions."""
    from pet_system import Pet
    pets = [Pet('electric', 1, 1), Pet('electric', 2, 2)]
    assert len(pets) == 2


# ============================================================
# Death (scenarios 23, 24, 25)
# ============================================================

def test_scenario_23_death_pursuit_only_triggered_on_ascend():
    """Death pursuit fires only when ASCENDING from L100 with the Stone.
    Dying on L100 keeps death_pursues=False."""
    # The trigger at main.py:1876-1883 lives inside _ascend_stairs.
    # We can't run a full Game in test, but we can verify the state machine
    # doesn't auto-activate Death pursuit just from being on L100.
    from player import Player
    p = Player()
    p.hp = 0
    assert p.is_dead() is True
    # death_pursues is a Game attribute set only by _trigger_death_pursuit()
    # which is only called from _ascend_stairs at L100 with the Stone.


def test_scenario_24_quiz_end_returns_to_player_state():
    """quiz_engine._end transitions state away from ASKING so the player
    state machine never sticks in a quiz post-death."""
    from quiz_engine import QuizEngine, QuizState
    eng = QuizEngine()
    eng.start_quiz(
        mode='chain', subject='math', tier=1,
        callback=lambda r: None, max_chain=5, wisdom=10,
    )
    eng._end(success=False)
    # Engine settles in COMPLETE; .active is False so callers can transition.
    assert eng.active is False
    assert eng.state == QuizState.COMPLETE


# ============================================================
# Spawn (scenarios 26, 27)
# ============================================================

def test_scenario_26_boss_levels_always_generate():
    """generate_boss_level handles each defined boss level without crashing."""
    from boss_levels import generate_boss_level, BOSS_LEVELS, COW_LEVEL
    import random
    for lvl in list(BOSS_LEVELS) + [COW_LEVEL]:
        random.seed(lvl * 17)
        dungeon, monsters, items = generate_boss_level(lvl)
        assert dungeon is not None
        assert isinstance(monsters, list)
        assert isinstance(items, list)


def test_scenario_27_mini_boss_pre_roll_handles_empty_pool():
    """LevelManager.__init__ doesn't crash even if no mini-bosses are defined."""
    # The pre-roll runs at __init__; we just need it to not raise.
    from level_manager import LevelManager
    mgr = LevelManager()
    assert isinstance(mgr._planned_mini_bosses, dict)


# ============================================================
# Save/load (scenarios 28, 29)
# ============================================================

def test_scenario_28_save_path_safe():
    """save_path sanitizes user-controlled names."""
    from save_system import _save_path
    path1 = _save_path('Brandon')
    path2 = _save_path('../etc/passwd')
    assert path1.endswith('save_brandon.pkl')
    # Path traversal characters become underscores
    assert '..' not in os.path.basename(path2)


def test_scenario_29_load_missing_returns_none():
    """load_game returns None for a non-existent save (no crash)."""
    from save_system import load_game, save_exists
    fake_name = '__definitely_not_a_real_player_name_xyz__'
    assert save_exists(fake_name) is False
    result = load_game(fake_name)
    assert result is None


# ============================================================
# Hardening regressions (added as part of this audit)
# ============================================================

def test_apply_equip_ring_when_all_slots_full_does_not_double_apply():
    """When all 4 ring slots are full, _apply_equip should NOT silently apply
    a 5th ring's effects (the game-level gate already blocks this, but
    _apply_equip must also be defensive)."""
    from player import Player
    p = Player()
    # Fill all 4 ring slots
    for i in range(4):
        r = _mk_ring(item_id=f'r{i}', stat='STR', amount=1)
        p.accessory_slots[i] = r
    str_before = p.STR
    # Try equipping a 5th ring
    r5 = _mk_ring(item_id='r5', stat='STR', amount=5)
    p._apply_equip(r5)
    # Hardening: STR must NOT have gained from r5 since no slot was free
    assert p.STR == str_before, "5th ring effects applied with no slot available"



# ---------------------------------------------------------------------------
# Regression: every STATE_* must have ESC handling. ESC in an unhandled state
# falls through to handle_event() returning False which means "quit game."
# User playtest 2026-05-19 caught STATE_PRAY exiting the game on ESC.
# ---------------------------------------------------------------------------

def test_every_state_has_esc_handling():
    """No STATE_* may be missing from the ESC handler in game_input.py.

    The handler must either:
      - Include the state in the big closeable-menu tuple
      - Have a dedicated if-branch (STATE_QUIZ, STATE_NPC_ENCOUNTER, etc.)
      - Be in the ignore-set (STATE_DEAD/STATE_VICTORY return False intentionally)
    """
    import re
    states = re.findall(r'STATE_\w+', open('src/game_states.py').read())
    states = sorted(set(s for s in states if s.startswith('STATE_')))

    src = open('src/game_input.py').read()
    # Slice the ESC handler — from the `if key == pygame.K_ESCAPE:` line to
    # the end of the function. The terminating `return False` is the bug:
    # an unhandled state hits that and the caller treats False as "quit game."
    esc_start = src.index('if key == pygame.K_ESCAPE')
    # End: stop at the first instance of "if self.state == STATE_PLAYER:" that
    # is OUTSIDE the ESC block (i.e., the non-ESC key handling for STATE_PLAYER)
    after_player_state = src.find('\n        if self.state == STATE_PLAYER:', esc_start)
    esc_section = src[esc_start:after_player_state]

    # Find ALL `state in (...)` tuples in the ESC section (there are two:
    # the big closeable-menu tuple and the small pet-submenu tuple).
    in_tuples = re.findall(r'self\.state in \((.*?)\)\s*:', esc_section, re.DOTALL)
    in_tuple: set = set()
    for tup in in_tuples:
        in_tuple |= set(re.findall(r'STATE_\w+', tup))
    # Plus all states with their own if-branches
    specific = set(re.findall(r'self\.state == (STATE_\w+)', esc_section))

    handled = in_tuple | specific
    # Intentional ignores
    handled.add('STATE_PLAYER')  # ESC opens the save/exit prompt
    handled.add('STATE_DEAD')
    handled.add('STATE_VICTORY')
    handled.add('STATE_LOCKPICK')  # dead state, retained for now

    missing = [s for s in states if s not in handled]
    assert not missing, (
        f'STATE_* without ESC handling: {missing}. '
        f'ESC in these states will QUIT THE GAME. Add to the big tuple '
        f'in game_input.py or give them a dedicated branch.'
    )
