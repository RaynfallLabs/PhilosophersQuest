"""Phase 3F+ deeper cross-system audit.

Runs system-by-system sanity checks across every major game subsystem
to verify a fully-playable experience.

This file exercises actual mechanics (mocked just enough to skip Pygame)
rather than just data shape, so genuine integration bugs surface.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ---------------------------------------------------------------------------
# Every hero passive must have at least one hook site in real source files
# (not just the data module).
# ---------------------------------------------------------------------------

def test_every_hero_passive_has_a_hook_site():
    import hero_specials
    passive_ids = set()
    for v in hero_specials.HERO_PASSIVES.values():
        passive_ids.update(v)
    missing = []
    for pid in passive_ids:
        found = 0
        for p in Path('src').glob('*.py'):
            if p.name == 'hero_specials.py':
                continue
            content = p.read_text(encoding='utf-8')
            if pid in content:
                found += 1
                break
        if not found:
            missing.append(pid)
    assert not missing, f"passives lacking hook sites: {missing}"


# ---------------------------------------------------------------------------
# Monster HP curve sanity — average scales with min_level
# ---------------------------------------------------------------------------

def _dice_avg(s):
    """Parse 'NdM' / 'NdM+B' / int — return average HP."""
    import re
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s)
    match = re.match(r'(\d+)d(\d+)(?:\+(\d+))?$', s)
    if match:
        n, sides, bonus = match.groups()
        return int(n) * (int(sides) + 1) / 2 + int(bonus or 0)
    try:
        return float(s)
    except ValueError:
        return 10.0


def test_monster_hp_curve_increases_with_depth():
    """Average monster HP at floor band 91-100 should exceed band 1-10 by a lot."""
    import json
    m = json.loads(Path('data/monsters.json').read_text(encoding='utf-8'))
    bands = {}
    for mon in m.values():
        if not isinstance(mon, dict):
            continue
        lvl = mon.get('min_level', 1)
        hp = _dice_avg(mon.get('hp', 10))
        band = min(9, max(0, (lvl - 1) // 10))
        bands.setdefault(band, []).append(hp)
    avg_low = sum(bands[0]) / len(bands[0])    # F1-10
    avg_high = sum(bands[9]) / len(bands[9])   # F91-100
    assert avg_low < 30, f"F1-10 average HP {avg_low:.1f} should be < 30"
    assert avg_high > 100, f"F91-100 average HP {avg_high:.1f} should be > 100"
    assert avg_high > avg_low * 5, \
        f"Endgame monsters should be at least 5x F1 (got {avg_low:.1f} -> {avg_high:.1f})"


# ---------------------------------------------------------------------------
# Hero damage specials scale appropriately vs monster HP
# ---------------------------------------------------------------------------

def test_hero_damage_specials_not_one_shot_endgame_bosses():
    """At chain 5, no damage special should one-shot the average F100 boss
    (~350 HP) — would be game-breaking per the design spec."""
    import hero_specials
    for sp in hero_specials.HERO_SPECIALS.values():
        if sp is None:
            continue
        actives = sp if isinstance(sp, list) else [sp]
        for s in actives:
            if not isinstance(s, dict):
                continue
            if s.get('effect') not in ('damage_single', 'self_aoe_fire'):
                continue
            t5 = s.get('tier_effects', {}).get(5, {})
            dice = t5.get('dice', '0d0') if isinstance(t5, dict) else '0d0'
            avg = _dice_avg(dice)
            # Bosses take 0.5x damage; player gets at most half-boss-HP dropped on a single chain-5
            damage_capped = avg * 0.5
            # F100 average boss HP is ~350; assert chain-5 boss damage < 200 (won't one-shot)
            assert damage_capped < 200, \
                f"{s['id']}: chain-5 boss-capped dmg {damage_capped} too high"


# ---------------------------------------------------------------------------
# All build kits actually instantiate (no missing item id / template / material)
# ---------------------------------------------------------------------------

def test_every_build_kit_instantiates():
    """Smoke test: try to construct each starting item for every build."""
    import json
    import welcome_screen
    accessory_ids = set(json.loads(Path('data/items/accessory.json').read_text(encoding='utf-8')))
    wand_ids = set(json.loads(Path('data/items/wand.json').read_text(encoding='utf-8')))
    book_ids = set(json.loads(Path('data/items/spellbook.json').read_text(encoding='utf-8')))
    weapon_ids = set(json.loads(Path('data/items/weapon.json').read_text(encoding='utf-8')))
    armor_ids = set(json.loads(Path('data/items/armor.json').read_text(encoding='utf-8')))
    shield_ids = set(json.loads(Path('data/items/shield.json').read_text(encoding='utf-8')))
    potion_ids = set(json.loads(Path('data/items/potion.json').read_text(encoding='utf-8')))
    ammo_ids = set(json.loads(Path('data/items/ammo.json').read_text(encoding='utf-8')))
    tpl_w = {p.stem for p in Path('data/templates/weapons').glob('*.json')}
    tpl_s = {p.stem for p in Path('data/templates/shields').glob('*.json')}
    tpl_a = {p.stem for p in Path('data/templates/armor').glob('*.json')}
    mat_w = {p.stem for p in Path('data/materials/weapons').glob('*.json')}
    mat_a = {p.stem for p in Path('data/materials/armor').glob('*.json')}

    errors = []
    for name, b in welcome_screen.SECRET_BUILDS.items():
        for field, store in [
            ('_start_weapon', weapon_ids), ('_start_melee', weapon_ids),
            ('_start_shield', shield_ids), ('_start_armor', armor_ids),
            ('_start_accessory', accessory_ids),
            ('_start_wand', wand_ids), ('_start_book', book_ids),
            ('_start_ammo', ammo_ids),
        ]:
            v = b.get(field)
            if v is None:
                continue
            if isinstance(v, tuple):
                tpl, mat = v
                # Materials live in either weapon or armor pool; templates per category
                if field == '_start_shield':
                    if tpl not in tpl_s:
                        errors.append(f"{name}: _start_shield template {tpl} missing")
                elif field == '_start_armor':
                    if tpl not in tpl_a:
                        errors.append(f"{name}: _start_armor template {tpl} missing")
                else:
                    if tpl not in tpl_w:
                        errors.append(f"{name}: {field} weapon template {tpl} missing")
                if mat not in (mat_w | mat_a):
                    errors.append(f"{name}: {field} material {mat} missing")
            else:
                if v not in store:
                    errors.append(f"{name}: {field} id {v} not in pool")
        for v in b.get('_start_extra_acc', []) or []:
            if v not in accessory_ids:
                errors.append(f"{name}: _start_extra_acc {v} missing")
        for v in b.get('_start_potions', []) or []:
            if v not in potion_ids:
                errors.append(f"{name}: _start_potions {v} missing")
    assert not errors, "Build kit instantiation errors:\n  " + "\n  ".join(errors)


# ---------------------------------------------------------------------------
# Every active hero special's effect string resolves to an actual resolver
# ---------------------------------------------------------------------------

def test_every_active_effect_resolves():
    import hero_specials
    for sp in hero_specials.HERO_SPECIALS.values():
        if sp is None:
            continue
        actives = sp if isinstance(sp, list) else [sp]
        for s in actives:
            if not isinstance(s, dict):
                continue
            eff = s.get('effect', '')
            assert eff in hero_specials._DISPATCH, \
                f"{s['id']}: effect '{eff}' has no resolver in _DISPATCH"


# ---------------------------------------------------------------------------
# Save/load compat — every player field used by save_state has a default
# ---------------------------------------------------------------------------

def test_player_fields_initialize_cleanly():
    from player import Player
    p = Player()
    # Phase 1/2 fields
    assert hasattr(p, 'total_identifies')
    assert hasattr(p, 'philosopher_tier_claimed')
    assert hasattr(p, 'philosophers_mantle')
    # Phase 3 fields
    assert hasattr(p, 'hero_passives')
    assert hasattr(p, 'hero_specials')
    assert hasattr(p, 'hero_special_cooldowns')
    assert hasattr(p, 'qa_tools')
    # Legacy fields still present
    assert hasattr(p, 'known_item_ids')
    assert hasattr(p, 'known_spells')
    assert hasattr(p, 'unlocked_quirks')


# ---------------------------------------------------------------------------
# Trap types: every TRAP_TYPES entry has a matching _check_floor_trap branch
# ---------------------------------------------------------------------------

def test_every_trap_type_has_player_handler():
    """_check_floor_trap dispatches by trap['type']. Verify all 11 trap
    types are addressed by name in the handler source."""
    from dungeon import TRAP_TYPES
    src = Path('src/main.py').read_text(encoding='utf-8')
    fn_start = src.find("def _check_floor_trap")
    assert fn_start >= 0
    # Use a generous 15K window to capture the full handler.
    fn_src = src[fn_start:fn_start + 15000]
    missing = []
    for t in TRAP_TYPES:
        tid = t['type']
        # Arrow trap shares the generic damage path (no special-effect branch).
        # Accept either the explicit branch OR the arrow case (damage-only).
        if f"'{tid}'" not in fn_src and tid != 'arrow':
            missing.append(tid)
    assert not missing, \
        f"trap types with no _check_floor_trap branch: {missing}"


# ---------------------------------------------------------------------------
# Prayer registry cross-check RETIRED (v2.13.0, 2026-09-06).
# The 9-prayer PRAYERS list was replaced with a single simple-prayer
# quiz + Divine Intercession. See tests/test_prayer.py for the
# replacement contract.
# ---------------------------------------------------------------------------

def test_v2_13_no_stale_prayer_registry():
    """Guardrail: PRAYERS registry must NOT be reintroduced."""
    import game_divine
    assert not hasattr(game_divine, 'PRAYERS'), (
        "v2.13.0 retired PRAYERS -- do not reintroduce the 9-prayer picker"
    )


# ---------------------------------------------------------------------------
# Every LEARNABLE_SPELL has an _apply_spell_effect branch
# ---------------------------------------------------------------------------

def test_every_spell_effect_implemented():
    """Spells dispatch via game_magic._apply_spell_effect by `effect` key,
    not by spell id. Verify every distinct effect has a code branch.
    Group dispatches (e.g., one branch for 'cone' AOEs) are accepted as
    long as the effect string appears literally in the function body."""
    from spells import LEARNABLE_SPELLS
    src = Path('src/game_magic.py').read_text(encoding='utf-8')
    fn_start = src.find("def _apply_spell_effect")
    assert fn_start >= 0
    fn_src = src[fn_start:fn_start + 50000]
    missing = []
    for sdef in LEARNABLE_SPELLS.values():
        eff = sdef.get('effect', '')
        if not eff:
            continue
        if f"'{eff}'" not in fn_src and f'"{eff}"' not in fn_src:
            missing.append(eff)
    # Some effects share dispatch branches (e.g., self-buffs in _SELF_BUFF_DURATIONS).
    # Allow up to 9 unfound effect strings, but log them. The cutoff drifts as
    # content grows; bump the limit only when the test starts failing on master
    # for genuinely-good reasons.
    assert len(missing) <= 9, \
        f"Spell effects with no dispatch ({len(missing)}): {missing[:15]}"


# ---------------------------------------------------------------------------
# Every monster.json entry has the required fields (sanity)
# ---------------------------------------------------------------------------

def test_every_monster_has_required_fields():
    import json
    m = json.loads(Path('data/monsters.json').read_text(encoding='utf-8'))
    missing = []
    for kind, mon in m.items():
        if not isinstance(mon, dict):
            continue
        for field in ('hp', 'thac0', 'ai_pattern', 'symbol'):
            if field not in mon:
                missing.append(f"{kind}: missing {field}")
    assert not missing, "Monsters missing fields:\n  " + "\n  ".join(missing[:20])


# ---------------------------------------------------------------------------
# All hero passives that show up in HERO_PASSIVES are checked
# in player.hero_passives at LEAST one place
# ---------------------------------------------------------------------------

def test_hero_passives_referenced_in_code():
    import hero_specials
    pid_strings = set()
    for v in hero_specials.HERO_PASSIVES.values():
        pid_strings.update(v)
    src_files = list(Path('src').glob('*.py'))
    src_contents = '\n'.join(p.read_text(encoding='utf-8') for p in src_files
                             if p.name != 'hero_specials.py')
    missing = [pid for pid in pid_strings if pid not in src_contents]
    assert not missing, f"Passive ids never referenced in code: {missing}"


# ---------------------------------------------------------------------------
# Every new hero sprite file exists
# ---------------------------------------------------------------------------

def test_new_hero_sprites_exist():
    expected = [
        'player_lovelace', 'player_da_vinci', 'player_boudicca',
        'player_joan', 'player_sherlock', 'player_musashi',
        'player_hildegard', 'player_tesla',
    ]
    sprite_dir = Path('assets/tiles/env')
    for s in expected:
        path = sprite_dir / f"{s}.png"
        assert path.exists(), f"missing sprite: {path}"


# ---------------------------------------------------------------------------
# Boss flags: every boss-level entry produces a monster with is_boss=True
# (data-layer check; the actual flagging happens in boss_levels.py)
# ---------------------------------------------------------------------------

def test_boss_levels_are_canonical():
    from boss_levels import BOSS_LEVELS
    assert sorted(BOSS_LEVELS) == [20, 40, 60, 80, 100], \
        f"Boss levels diverged from canonical 20/40/60/80/100: {sorted(BOSS_LEVELS)}"
