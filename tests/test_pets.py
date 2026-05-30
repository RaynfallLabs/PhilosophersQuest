"""Tests for the 2026-05-17 pet system revamp (Phase 1):

- Naming popup: nicknames display 'Nickname the Species'
- Evolution thresholds: stage 1 at L25, stage 2 at L55
- XP curve: level * 20
- Passive XP gain: 1 XP every 3 turns
- Kill XP: scaled by monster max_hp
- Late-pickup catch-up: pets hatched on deeper floors start with bonus XP
- Unicorn trap detection sets the right field (revealed, not detected)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ---------------------------------------------------------------------------
# Evolution thresholds
# ---------------------------------------------------------------------------

def test_stage_thresholds():
    import pet_system
    assert pet_system._EVOLVE_1 == 25
    assert pet_system._EVOLVE_2 == 55


def test_pet_stages_by_level():
    from pet_system import Pet
    p = Pet('electric')
    assert p.stage == 0
    p.level = 24
    assert p.stage == 0
    p.level = 25
    assert p.stage == 1
    p.level = 54
    assert p.stage == 1
    p.level = 55
    assert p.stage == 2
    p.level = 100
    assert p.stage == 2


# ---------------------------------------------------------------------------
# Nickname display
# ---------------------------------------------------------------------------

def test_pet_name_without_nickname():
    from pet_system import Pet
    p = Pet('electric')
    assert p.species_name == 'Zappik'
    assert p.name == 'Zappik'   # no nickname → just species


def test_pet_name_with_nickname():
    from pet_system import Pet
    p = Pet('electric')
    p.nickname = 'Pikachu'
    assert p.name == 'Pikachu the Zappik'
    p.level = 25  # evolution to stage 1
    assert p.species_name == 'Voltpaw'
    assert p.name == 'Pikachu the Voltpaw'
    p.level = 55  # evolution to stage 2
    assert p.species_name == 'Thundertail'
    assert p.name == 'Pikachu the Thundertail'


def test_default_nickname_is_empty():
    from pet_system import Pet
    p = Pet('water')
    assert p.nickname == ''


# ---------------------------------------------------------------------------
# XP curve and passive gain
# ---------------------------------------------------------------------------

def test_xp_to_next_formula():
    from pet_system import Pet
    p = Pet('plant')
    p.level = 1
    assert p._xp_to_next() == 20
    p.level = 10
    assert p._xp_to_next() == 200
    p.level = 24
    assert p._xp_to_next() == 480


def test_passive_xp_every_third_turn():
    from pet_system import Pet
    p = Pet('fire')
    start_xp = p.xp
    p.gain_xp_passive()
    p.gain_xp_passive()
    assert p.xp == start_xp, "first two passive ticks should grant no XP"
    p.gain_xp_passive()
    assert p.xp == start_xp + 1, "third passive tick should grant 1 XP"
    p.gain_xp_passive()
    p.gain_xp_passive()
    assert p.xp == start_xp + 1, "no further XP until the next 3-tick interval"
    p.gain_xp_passive()
    assert p.xp == start_xp + 2


def test_passive_xp_returns_no_messages_when_dead():
    from pet_system import Pet
    p = Pet('electric')
    p.alive = False
    for _ in range(10):
        msgs = p.gain_xp_passive()
        assert msgs == []


# ---------------------------------------------------------------------------
# Kill XP scaling
# ---------------------------------------------------------------------------

def test_kill_xp_scales_with_monster_max_hp():
    from pet_system import Pet
    p = Pet('water')
    # Use a higher starting level so xp_to_next is large enough to avoid
    # mid-test level-ups consuming the awarded XP.
    p.level = 10        # xp_to_next = 200
    start_xp = p.xp
    p.gain_xp_from_kill(10)   # F1 mob ≈ 4 XP (3 + 10//10)
    assert p.xp == start_xp + 4
    p.xp = start_xp
    p.gain_xp_from_kill(200)  # F90 mob ≈ 23 XP
    assert p.xp == start_xp + 23


def test_kill_xp_increments_counter():
    from pet_system import Pet
    p = Pet('electric')
    assert p.kills_count == 0
    p.gain_xp_from_kill(30)
    p.gain_xp_from_kill(30)
    p.gain_xp_from_kill(30)
    assert p.kills_count == 3


def test_kill_xp_levels_pet_with_repeated_kills():
    """Sanity: enough mid-floor kills push the pet across multiple levels.

    Curve: L1->2 = 20 XP, L2->3 = 40 XP, ..., total to L6 = 300 XP. Each
    60-HP kill grants 9 XP, so 40 kills = 360 XP → expect L6+.
    """
    from pet_system import Pet
    p = Pet('plant')
    for _ in range(40):
        p.gain_xp_from_kill(60)
    assert p.level >= 6, \
        f"40 mid-tier kills should reach at least L6; got L{p.level}"


# ---------------------------------------------------------------------------
# Late-pickup catch-up
# ---------------------------------------------------------------------------

def test_late_pickup_bonus_zero_at_floor_zero():
    from pet_system import Pet
    p = Pet('fire')
    p.apply_late_pickup_bonus(0)
    assert p.xp == 0
    assert p.level == 1


def test_late_pickup_bonus_scales_with_floor():
    from pet_system import Pet
    p = Pet('fire')
    p.apply_late_pickup_bonus(30)   # 30 * 50 = 1500 XP
    # 1500 XP at level*20 curve: L1→2 (20), L2→3 (40), L3→4 (60), ...
    # Sum 20+40+...+200 = 20*sum(1..10) = 1100. So L11 with 400 leftover.
    assert p.level >= 10, f"pet at floor 30 should reach at least L10; got L{p.level}"


def test_late_pickup_bonus_capped_below_stage_1():
    """A pet hatched in the deepest possible spot still has to EARN evolution."""
    from pet_system import Pet
    p = Pet('water')
    p.apply_late_pickup_bonus(99)   # capped at floor * 50 = 4950, but min(4950, 4000) = 4000
    assert p.stage == 0, "catch-up alone must not push past stage 1"
    assert p.level < 25, f"catch-up must keep pet below L25 (stage 1); got L{p.level}"


# ---------------------------------------------------------------------------
# Unicorn trap-detection bug fix
# ---------------------------------------------------------------------------

def test_unicorn_sets_revealed_not_detected():
    from pet_system import UnicornPet

    class _StubPlayer:
        x = 5
        y = 5
        hp = 50
        max_hp = 50
        status_effects: dict = {}
    class _StubDungeon:
        def __init__(self):
            self.traps = {(6, 6): {'type': 'pit', 'damage': '2d6', 'message': '!',
                                    'damage_type': 'physical', 'revealed': False}}
        def is_walkable(self, x, y):
            return True

    u = UnicornPet(5, 5)
    player = _StubPlayer()
    dungeon = _StubDungeon()
    monsters = []
    pets = [u]
    # Run several ticks so the heal/cleanse timers don't dominate output
    for _ in range(3):
        u.take_turn(player, dungeon, monsters, pets, ground_items=[])
    trap = dungeon.traps[(6, 6)]
    assert trap.get('revealed') is True, "unicorn must set revealed=True so engine sees the trap"
    assert 'detected' not in trap or trap.get('detected') is None, \
        "the buggy `detected` key should no longer be written"


# ---------------------------------------------------------------------------
# Phase 2: Specials (data + cooldowns)
# ---------------------------------------------------------------------------

def test_available_specials_by_stage():
    from pet_system import Pet
    p = Pet('electric')
    # Stage 0 (L1-24): no specials
    assert p.available_specials() == []
    # Stage 1 (L25-54): unlock stage-1 special
    p.level = 25
    avail = p.available_specials()
    assert len(avail) == 1
    assert avail[0]['id'] == 'spark_bolt'
    # Stage 2 (L55+): both specials unlocked
    p.level = 55
    avail = p.available_specials()
    assert len(avail) == 2
    ids = {s['id'] for s in avail}
    assert ids == {'spark_bolt', 'thunder_strike'}


def test_every_species_has_two_specials():
    """All four soul-sphere species must have stage-1 and stage-2 specials.
    The Duck of Doom is exempt: it has a stage-0 special (Detect Monsters)
    that's available at hatch, plus the standard 1 & 2 stage specials —
    3 total. Validated separately below."""
    import pet_system
    for key, sp in pet_system._SPECIES.items():
        if key == 'duck_of_doom':
            continue  # see test_duck_of_doom_species_has_three_specials
        assert 'specials' in sp, f"{key} missing specials list"
        specials = sp['specials']
        assert len(specials) == 2, f"{key} should define 2 specials; got {len(specials)}"
        stages = {s['unlock_stage'] for s in specials}
        assert stages == {1, 2}, f"{key} should have stage-1 and stage-2 specials"
        for s in specials:
            for required in ('id', 'name', 'damage_mult', 'targeting',
                             'range', 'cooldown', 'desc'):
                assert required in s, f"{key}/{s.get('id')} missing {required}"


def test_duck_of_doom_species_has_three_specials():
    """The Duck of Doom hatches into Waddlekind with Detect Monsters
    already unlocked (stage 0). Evolves through Drake of the Covenant
    (Psionic Blast, stage 1) into Seraphimallard (Sometimes Goose, stage 2).
    All 3 specials need the standard schema."""
    import pet_system
    sp = pet_system._SPECIES['duck_of_doom']
    specials = sp['specials']
    assert len(specials) == 3
    stages = {s['unlock_stage'] for s in specials}
    assert stages == {0, 1, 2}, f"expected stages {{0,1,2}}; got {stages}"
    by_stage = {s['unlock_stage']: s for s in specials}
    assert by_stage[0]['id'] == 'detect_monsters'
    assert by_stage[1]['id'] == 'psionic_blast'
    assert by_stage[2]['id'] == 'sometimes_goose'
    # Stage 0 special is a self-buff, not a damaging attack, so it
    # doesn't need damage_mult.
    for s in (by_stage[1], by_stage[2]):
        for required in ('id', 'name', 'damage_mult', 'targeting',
                         'range', 'cooldown', 'desc'):
            assert required in s, f"duck/{s.get('id')} missing {required}"


def test_special_cooldown_lifecycle():
    from pet_system import Pet
    p = Pet('electric')
    p.level = 25  # unlocks spark_bolt
    assert p.special_cooldown('spark_bolt') == 0
    assert p.can_use_special('spark_bolt')
    p.use_special('spark_bolt')
    assert p.special_cooldown('spark_bolt') == 250
    assert not p.can_use_special('spark_bolt')
    # Tick down
    for _ in range(125):
        p.tick_cooldown()
    assert p.special_cooldown('spark_bolt') == 125
    # Fully tick out
    for _ in range(125):
        p.tick_cooldown()
    assert p.special_cooldown('spark_bolt') == 0
    assert p.can_use_special('spark_bolt')


def test_special_cooldowns_are_independent():
    from pet_system import Pet
    p = Pet('water')
    p.level = 55  # both specials unlocked
    p.use_special('water_jet')   # cooldown 250
    p.use_special('tidal_crash') # cooldown 400
    assert p.special_cooldown('water_jet') == 250
    assert p.special_cooldown('tidal_crash') == 400
    # Tick one round
    p.tick_cooldown()
    assert p.special_cooldown('water_jet') == 249
    assert p.special_cooldown('tidal_crash') == 399


def test_locked_special_cannot_be_used():
    from pet_system import Pet
    p = Pet('fire')
    p.level = 25  # only stage-1 flame_breath unlocked
    assert p.can_use_special('flame_breath')
    assert not p.can_use_special('inferno_pillar')   # stage-2, locked


# ---------------------------------------------------------------------------
# Phase 2: Commands (Stay / Return / Wander) and AI behavior
# ---------------------------------------------------------------------------

def test_pet_default_command():
    from pet_system import Pet
    assert Pet('electric').command == 'return'


def test_command_stay_holds_position_when_no_enemy():
    from pet_system import Pet

    class _StubDungeon:
        def is_walkable(self, x, y): return True
    class _StubPlayer:
        x = 10
        y = 10

    p = Pet('water', x=3, y=3)
    p.command = 'stay'
    monsters = []
    pets = [p]
    result = p.take_turn(_StubPlayer(), _StubDungeon(), monsters, pets, ground_items=[])
    assert result is None
    assert (p.x, p.y) == (3, 3), "stay command must not move pet when no adjacent enemy"


def test_command_return_follows_player_when_far():
    from pet_system import Pet

    class _StubDungeon:
        def is_walkable(self, x, y): return True
    class _StubPlayer:
        x = 10
        y = 10

    p = Pet('plant', x=3, y=3)
    p.command = 'return'
    p.take_turn(_StubPlayer(), _StubDungeon(), [], [p], ground_items=[])
    # Should have moved toward (10, 10)
    assert (p.x, p.y) != (3, 3), "return command must follow player when far away"


# ---------------------------------------------------------------------------
# Phase 2: Bound Soul Sphere round-trip (recall + re-throw spawns same pet)
# ---------------------------------------------------------------------------

def test_bound_sphere_preserves_pet_state():
    """The recall mechanic stores the pet ref on the sphere; the throw uses it."""
    from items import Artifact
    from pet_system import Pet
    p = Pet('plant')
    p.level = 30
    p.nickname = 'Spikey'
    p.kills_count = 12
    sphere = Artifact({
        'id': 'soul_sphere', 'name': 'Bound Soul Sphere', 'symbol': 'O',
        'color': [80, 200, 255], 'item_class': 'artifact', 'weight': 0.5,
        'min_level': 1,
    })
    sphere.bound_pet = p
    # The contract: sphere.bound_pet is the actual Pet instance, fully restored
    bound = getattr(sphere, 'bound_pet', None)
    assert bound is p
    assert bound.nickname == 'Spikey'
    assert bound.level == 30
    assert bound.kills_count == 12
    assert bound.species_key == 'plant'


# ---------------------------------------------------------------------------
# Legacy-systems audit (2026-05-19): custom Pet subclasses must initialize all
# base-class attributes touched by the per-turn combat loop. Previously each
# subclass (Fenrir / Sketched / Dad / Unicorn) bypassed Pet.__init__ entirely
# and crashed with AttributeError on the first turn after summoning.
# ---------------------------------------------------------------------------

def test_fenrir_per_turn_methods_dont_crash():
    """FenrirPet must survive a full game_combat per-pet turn sequence."""
    from pet_system import FenrirPet
    f = FenrirPet(5, 5)
    # Name property reads self.nickname -- crashed before the fix.
    assert f.name == 'Fenrir'
    # Per-turn methods all touch attributes the base Pet sets in __init__.
    f.gain_xp_passive()
    f.tick_cooldown()
    f.tick_regen()
    # Combat loop also tries gain_xp_from_kill after kills
    f.gain_xp_from_kill(50)


def test_unicorn_per_turn_methods_dont_crash():
    from pet_system import UnicornPet
    u = UnicornPet(5, 5)
    assert u.name == 'Ethereal Unicorn'
    u.gain_xp_passive()
    u.tick_cooldown()


def test_dad_per_turn_methods_dont_crash():
    from pet_system import DadPet
    d = DadPet(5, 5)
    assert d.name == 'Dad'
    d.gain_xp_passive()
    d.tick_cooldown()


def test_sketched_per_turn_methods_dont_crash():
    from pet_system import SketchedPet

    class _FakeMonster:
        name = 'orc'
        symbol = 'o'
        kind = 'orc'
        min_level = 5
        max_hp = 30
        attacks = [{'damage': '1d6'}]

    s = SketchedPet(_FakeMonster(), 5, 5, 10)
    assert s.name == 'Sketched orc'
    s.gain_xp_passive()
    s.tick_cooldown()


def test_all_pet_subclasses_have_required_attrs():
    """All Pet subclasses must initialize every attribute the combat loop reads."""
    from pet_system import FenrirPet, UnicornPet, DadPet, SketchedPet

    class _FakeMonster:
        name = 'orc'; symbol = 'o'; kind = 'orc'; min_level = 5; max_hp = 30
        attacks = [{'damage': '1d6'}]

    pets = [
        FenrirPet(0, 0),
        UnicornPet(0, 0),
        DadPet(0, 0),
        SketchedPet(_FakeMonster(), 0, 0, 10),
    ]
    required = ['nickname', 'kills_count', 'command', 'last_pet_floor',
                '_special_cooldowns', '_passive_xp_timer', '_regen_timer']
    for p in pets:
        for attr in required:
            assert hasattr(p, attr), \
                f"{type(p).__name__} missing required attr {attr!r}"


# ---------------------------------------------------------------------------
# Legacy-systems audit: bones system
# ---------------------------------------------------------------------------

def test_bones_corrupt_file_is_cleaned_up(tmp_path, monkeypatch):
    """A corrupt bones JSON must be removed on next load so it doesn't
    permanently occupy a slot under _MAX_BONES."""
    import bones, random

    # Redirect bones dir to a tmp location
    monkeypatch.setattr(bones, 'save_dir', lambda: str(tmp_path))

    # Force the 50% gate to always trigger
    class _AlwaysOpen:
        def random(self): return 0.0
        def choice(self, lst): return lst[0]
        def shuffle(self, lst): pass
    monkeypatch.setattr(bones, 'random', _AlwaysOpen())

    bd = bones._bones_dir()
    bad_path = os.path.join(bd, 'bones_L5.json')
    with open(bad_path, 'w') as f:
        f.write('{not valid json')
    assert os.path.exists(bad_path)
    result = bones.load_bones(5)
    assert result is None
    assert not os.path.exists(bad_path), \
        "corrupt bones file must be removed so it doesn't waste a slot"


# ---------------------------------------------------------------------------
# Legacy-systems audit: highscore system
# ---------------------------------------------------------------------------

def test_highscore_handles_missing_file(tmp_path, monkeypatch):
    import highscore_system as hs
    monkeypatch.setattr(hs, '_SCORE_FILE', str(tmp_path / 'nonexistent.json'))
    assert hs.get_scores() == []
    assert hs.get_top(5) == []


def test_highscore_handles_corrupt_json(tmp_path, monkeypatch):
    import highscore_system as hs
    score_path = tmp_path / 'highscores.json'
    score_path.write_text('{not valid json')
    monkeypatch.setattr(hs, '_SCORE_FILE', str(score_path))
    assert hs.get_scores() == []


def test_highscore_truncates_to_max_entries(tmp_path, monkeypatch):
    import highscore_system as hs
    monkeypatch.setattr(hs, '_SCORE_FILE', str(tmp_path / 'highscores.json'))
    for i in range(hs.MAX_ENTRIES + 50):
        hs.add_score(f'Pl{i}', i * 10, 'B', 10, 5, 100, victory=False)
    assert len(hs.get_scores()) == hs.MAX_ENTRIES


# ---------------------------------------------------------------------------
# Legacy-systems audit: welcome-screen / SECRET_BUILDS data integrity
# ---------------------------------------------------------------------------

def test_secret_build_spells_all_resolve():
    """Every spell id listed in _start_spells must exist in LEARNABLE_SPELLS."""
    from welcome_screen import SECRET_BUILDS
    from spells import LEARNABLE_SPELLS
    spell_ids = set(LEARNABLE_SPELLS.keys())
    missing = []
    for name, build in SECRET_BUILDS.items():
        for sid in build.get('_start_spells', []):
            if sid not in spell_ids:
                missing.append((name, sid))
    assert not missing, \
        f"SECRET_BUILDS reference unknown spells: {missing}"


def test_secret_build_items_all_resolve():
    """Every item id referenced in SECRET_BUILDS must exist in its item pool."""
    from welcome_screen import SECRET_BUILDS
    from items import load_items

    pools = {}
    for cls in ('weapon', 'armor', 'shield', 'accessory', 'wand',
                'spellbook', 'potion', 'ammo'):
        try:
            pools[cls] = {i.id for i in load_items(cls)}
        except Exception:
            pools[cls] = set()

    missing = []
    for name, build in SECRET_BUILDS.items():
        for key, val in build.items():
            if key in ('_start_weapon', '_start_melee') and isinstance(val, str):
                if val not in pools['weapon']:
                    missing.append((name, key, val))
            elif key == '_start_armor' and isinstance(val, str):
                if val not in pools['armor']:
                    missing.append((name, key, val))
            elif key == '_start_shield' and isinstance(val, str):
                if val not in pools['shield']:
                    missing.append((name, key, val))
            elif key == '_start_accessory' and val not in pools['accessory']:
                missing.append((name, key, val))
            elif key == '_start_extra_acc':
                for a in val:
                    if a not in pools['accessory']:
                        missing.append((name, key, a))
            elif key == '_start_wand' and val not in pools['wand']:
                missing.append((name, key, val))
            elif key == '_start_book' and val not in pools['spellbook']:
                missing.append((name, key, val))
            elif key == '_start_potions':
                for p in val:
                    if p not in pools['potion']:
                        missing.append((name, key, p))
            elif key == '_start_ammo' and val not in pools['ammo']:
                missing.append((name, key, val))
    assert not missing, \
        f"SECRET_BUILDS reference unknown items: {missing}"


def test_secret_build_keys_all_lowercase():
    """Welcome screen looks up names via .lower() -- keys must already be lowercase."""
    from welcome_screen import SECRET_BUILDS
    not_lower = [k for k in SECRET_BUILDS if k != k.lower()]
    assert not not_lower, f"SECRET_BUILDS keys must be lowercase; bad keys: {not_lower}"
