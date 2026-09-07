"""Smoke tests for the 10 spell handlers added in the V2 audit fix.

Each test stands up a minimal Game-like stub (just MagicMixin + the fields the
handler reads), casts the spell at chain 5 (max), and asserts that the expected
mutation occurred — NOT the generic-fallback damage.

If any handler regresses to the fallback (line ~1748 in game_magic.py:
`"The {effect.replace('_', ' ')} hits the {target.name} for {actual} dmg!"`),
the corresponding test will fail because the buff/status/reveal never lands.
"""
import os
import random as _random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game_magic import MagicMixin
from monster import Monster
from player import Player
from spells import LEARNABLE_SPELLS


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

class _StubDungeon:
    """A minimal dungeon: 20x20 walkable floor, no walls."""
    def __init__(self, w: int = 20, h: int = 20):
        self.width  = w
        self.height = h
        # tiles[y][x] = 0 (FLOOR). dungeon.FLOOR is the integer 0 per dungeon.py.
        self.tiles = [[0 for _ in range(w)] for _ in range(h)]
        self.explored: set = set()

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        return self.in_bounds(x, y)


class _StubGame(MagicMixin):
    """MagicMixin with just the attributes the spell handlers read."""

    def __init__(self):
        # Player: real Player so add_effect/restore_hp/apply_stat_bonus behave
        # exactly like the runtime. Status effects start empty.
        self.player = Player()
        # MagicMixin._spell_damage walks player.armor_slots/accessory_slots via
        # chain_passives.equipped_chain_items; Player() seeds these as None/lists.
        self.player.status_effects = {}

        # World state
        self.dungeon = _StubDungeon()
        self.monsters: list = []
        self.pets: list = []
        self.ground_items: list = []
        self.visible: set = set()
        self.dungeon_level: int = 5

        # Message log capture (tests inspect this for the success path)
        self.messages: list = []

        # MagicMixin reads but doesn't always set these; default safely.
        self._wand_override_target = None
        self._last_spell_crit = False
        self._last_spell_anti_being = False

    # MagicMixin / Game API the handlers call -----------------------------

    def add_message(self, text: str, msg_type: str = 'info'):
        self.messages.append((text, msg_type))

    def _on_monster_killed(self, monster, *, chain_score: int = 0,
                           ranged: bool = False, unarmed: bool = False,
                           hp_pct_before: float | None = None):
        # Just track that it was called. No treasure/quirks/popups in tests.
        if not hasattr(self, '_killed'):
            self._killed = []
        self._killed.append(monster)

    def _teleport_player(self):
        # Used by some spell flows; not exercised here but keep it safe.
        pass

    def _refresh_fov(self):
        pass

    def _a_or_an(self, word: str) -> str:
        return ('an ' if word[:1].lower() in 'aeiou' else 'a ') + word


def _make_monster(kind: str = 'kobold', x: int = 5, y: int = 5,
                  hp: int = 20, *, tags=None, is_boss: bool = False,
                  max_hp_override: int | None = None) -> Monster:
    defn = {
        'id': kind,
        'name': kind.replace('_', ' '),
        'symbol': 'k',
        'color': [255, 255, 255],
        'hp': str(hp),
        'attacks': [{'dmg': '1d4', 'type': 'physical'}],
        'tags': tags or [],
        'min_level': 1,
    }
    m = Monster(defn, x, y)
    if max_hp_override is not None:
        m.max_hp = max_hp_override
        m.hp = min(m.hp, m.max_hp)
    if is_boss:
        m.is_boss = True
    return m


def _spawn_visible_monster(g: _StubGame, **kwargs) -> Monster:
    m = _make_monster(**kwargs)
    g.monsters.append(m)
    g.visible.add((m.x, m.y))
    return m


def _cast(g: _StubGame, spell_id: str, chain: int = 5, target: Monster | None = None):
    """v2.12.0: chain arg retained for back-compat with existing tests but
    IGNORED -- _apply_spell_effect no longer accepts a chain parameter.
    Magnitude is baked into spell.power dice per tier."""
    spell = LEARNABLE_SPELLS[spell_id]
    g._apply_spell_effect(spell, target)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_mapping_spell_reveals_entire_floor():
    g = _StubGame()
    assert len(g.dungeon.explored) == 0
    _cast(g, 'mapping_spell', chain=5)
    # Every tile is explored
    assert len(g.dungeon.explored) == g.dungeon.width * g.dungeon.height
    assert (0, 0) in g.dungeon.explored
    assert (g.dungeon.width - 1, g.dungeon.height - 1) in g.dungeon.explored


def test_wish_spell_grants_a_bounded_boon():
    """Wish must do SOMETHING measurable: HP restored, stat raised, or a
    long-duration buff. With 3 outcomes the seeded RNG fixes the branch."""
    g = _StubGame()
    g.player.hp = 1
    g.player.sp = 1
    g.player.mp = 1
    pre_hp, pre_sp, pre_mp = g.player.hp, g.player.sp, g.player.mp
    pre_stats = (g.player.STR, g.player.CON, g.player.DEX,
                 g.player.INT, g.player.WIS, g.player.PER)
    pre_effects = dict(g.player.status_effects)

    # Seed temporarily so we cover a deterministic branch, then restore.
    _state = _random.getstate()
    try:
        _random.seed(0)
        _cast(g, 'wish_spell', chain=5)
    finally:
        _random.setstate(_state)

    post_hp, post_sp, post_mp = g.player.hp, g.player.sp, g.player.mp
    post_stats = (g.player.STR, g.player.CON, g.player.DEX,
                  g.player.INT, g.player.WIS, g.player.PER)
    post_effects = dict(g.player.status_effects)

    full_restore = (post_hp > pre_hp and post_sp > pre_sp and post_mp > pre_mp)
    stat_bonus   = post_stats != pre_stats
    new_buff     = post_effects != pre_effects
    assert full_restore or stat_bonus or new_buff, (
        "wish_spell didn't apply any bounded boon"
    )
    # Confirm the success message landed and the generic fallback did NOT.
    msgs = [t for t, _ in g.messages]
    assert any('WISH GRANTED' in m for m in msgs)


def test_levitate_spell_applies_levitating_status():
    g = _StubGame()
    assert not g.player.has_effect('levitating')
    _cast(g, 'levitate_spell', chain=5)
    assert g.player.has_effect('levitating'), \
        "levitate_spell did not apply the 'levitating' status"
    # Duration scales with chain: at chain 5 == base (12) * 1.0 = 12
    assert g.player.status_effects['levitating'] >= 6


def test_phase_door_spell_applies_phasing_status():
    g = _StubGame()
    assert not g.player.has_effect('phasing')
    _cast(g, 'phase_door_spell', chain=5)
    assert g.player.has_effect('phasing'), \
        "phase_door_spell did not apply the 'phasing' status"
    assert g.player.status_effects['phasing'] >= 6


def test_turn_undead_spell_damages_and_fears_visible_undead():
    g = _StubGame()
    # Undead and non-undead in sight
    skel = _spawn_visible_monster(g, kind='skeleton', x=5, y=5, hp=40,
                                  tags=['undead'])
    rat = _spawn_visible_monster(g, kind='giant_rat', x=6, y=6, hp=40)
    pre_skel_hp = skel.hp
    pre_rat_hp = rat.hp

    _cast(g, 'turn_undead_spell', chain=5)

    assert skel.hp < pre_skel_hp, "undead must take holy damage"
    assert skel.has_effect('feared'), "undead must be feared"
    # Non-undead is untouched
    assert rat.hp == pre_rat_hp, "non-undead should be unaffected"
    assert not rat.has_effect('feared')


def test_annihilation_spell_slays_low_hp_monsters():
    g = _StubGame()
    # Low-HP monster: should be vaporized (HP 5 / max 100 = 5%, below 35% @ chain 5)
    weak = _spawn_visible_monster(g, kind='kobold', x=5, y=5, hp=100)
    weak.hp = 5
    # Healthy monster: above threshold, takes big damage but might survive
    healthy = _spawn_visible_monster(g, kind='ogre', x=6, y=6, hp=100)
    healthy.hp = 100
    # Boss: never instakilled
    boss = _spawn_visible_monster(g, kind='dragon', x=7, y=7, hp=1000,
                                  max_hp_override=1000, is_boss=True)
    pre_boss_hp = boss.hp

    _cast(g, 'annihilation_spell', chain=5)

    assert not weak.alive, "low-HP monster must be vaporized"
    # Healthy monster took the big bite
    assert healthy.hp < 100, "healthy monster must take damage"
    # Boss survived but was hit
    assert boss.alive, "boss must NOT be instakilled"
    assert boss.hp < pre_boss_hp, "boss must take fixed damage"


def test_sleep_mass_spell_applies_sleeping_to_visible():
    g = _StubGame()
    m1 = _spawn_visible_monster(g, kind='kobold', x=5, y=5)
    m2 = _spawn_visible_monster(g, kind='goblin', x=6, y=6)
    # Off-screen monster ignored
    m3 = _make_monster(kind='ogre', x=15, y=15)
    g.monsters.append(m3)   # NOT in visible

    # v2.12.0: renamed from `sleep_mass_spell` to `mass_sleep_spell`.
    _cast(g, 'mass_sleep_spell', chain=5)

    # Mass Sleep (T3) applies the 'sleeping' status, not paralyzed
    assert m1.has_effect('sleeping'), "Mass Sleep must apply 'sleeping' to visible"
    assert m2.has_effect('sleeping')
    assert not m3.has_effect('sleeping'), "off-screen monsters must be untouched"
    assert not m3.has_effect('paralyzed')


def test_mass_paralyze_spell_applies_paralyzed_to_visible():
    g = _StubGame()
    m1 = _spawn_visible_monster(g, kind='kobold', x=5, y=5)
    m2 = _spawn_visible_monster(g, kind='goblin', x=6, y=6)

    _cast(g, 'mass_paralyze_spell', chain=5)

    # Mass Paralyze (T4) applies the stronger 'paralyzed' status
    assert m1.has_effect('paralyzed'), "Mass Paralyze must apply 'paralyzed' to visible"
    assert m2.has_effect('paralyzed')


def test_detect_magic_spell_reveals_wand_buc_in_sight():
    from items import Wand
    g = _StubGame()
    # A wand on the floor, in FOV
    wand_defn = {
        'id': 'wand_of_light', 'name': 'wand of light',
        'effect': 'light', 'charges_min': 3, 'charges_max': 3,
        'quiz_tier': 1, 'quiz_threshold': 2, 'symbol': '/',
        'color': [200, 200, 200],
        'unidentified_name': 'shimmering wand',
    }
    w = Wand(wand_defn)
    w.x, w.y = 8, 8
    w.buc = 'cursed'
    w.buc_known = False
    g.ground_items.append(w)
    g.visible.add((8, 8))

    _cast(g, 'detect_magic_spell', chain=5)

    assert w.buc_known is True, "detect_magic_spell must reveal BUC on floor wands"


def test_dispel_magic_spell_strips_target_buffs():
    g = _StubGame()
    m = _make_monster(kind='ogre', x=5, y=5, hp=100)
    # Buffs that should be stripped
    m.add_effect('shielded', 10)
    m.add_effect('hasted', 8)
    # DoT/debuff that should survive (player's investment)
    m.add_effect('poisoned', 10)
    g.monsters.append(m)
    g.visible.add((m.x, m.y))

    _cast(g, 'dispel_magic_spell', chain=5, target=m)

    assert not m.has_effect('shielded'), "buff 'shielded' must be stripped"
    assert not m.has_effect('hasted'),   "buff 'hasted' must be stripped"
    assert m.has_effect('poisoned'),     "DoT 'poisoned' must survive dispel"
    # And the monster must NOT have been damaged (generic fallback would deal dmg).
    assert m.hp == 100, \
        "dispel_magic must not deal damage (generic-fallback regression)"
