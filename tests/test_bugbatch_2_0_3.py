"""Regression tests for the 2.0.3 bug batch.

Each test would FAIL if the corresponding fix were reverted:

  Bug 1 - weapon class-mechanics are shown by NAME in the Kit screen and
          NAME + DESCRIPTION in the Examine panel (combat.CLASS_MECHANIC_INFO
          + RenderMixin wiring).
  Bug 2 - (secondary leak) chests no longer drop monster-derived ingredients
          (prime / family / trophy) -- only terrain-foraged ones.
  Bug 3 - the magic-missile WAND scales missile count with the science chain
          (escalator-chain quiz), instead of firing a single fixed bolt.
  Bug 4 - single-target monster projectiles do NOT pierce intervening enemies;
          AoE breath/beam attacks still do.

These are randomized / deep-dungeon / quiz-flow mechanics that the project's
play-test rule says to cover with logic tests rather than play-testing.
"""
from __future__ import annotations

import glob
import inspect
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pygame  # noqa: E402
pygame.init()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _w(**kw):
    """Build a minimal Weapon (mirrors the engine-wave test helpers)."""
    from items import Weapon
    defn = {
        'id': 't', 'name': 't', 'symbol': '(',
        'color': [255, 255, 255], 'weight': 1.0,
        'item_class': 'weapon', 'class': 'sword',
        'base_damage': 5, 'damage_types': ['slash'],
    }
    defn.update(kw)
    return Weapon(defn)


class _FakeRenderSelf:
    """Stand-in `self` for RenderMixin helpers that only need a few hooks."""
    font_sm = None

    def __init__(self, idl=5):
        self._idl = idl

    def _kit_visible_level(self, item):
        return self._idl

    def _wrap_text(self, text, font, width):
        return [text]


# ===========================================================================
# Bug 1 -- weapon class-mechanic display
# ===========================================================================

def test_every_template_mechanic_is_in_info_map():
    """Every weapon template's class_mechanic must have a curated entry in
    CLASS_MECHANIC_INFO, so no weapon falls back to a humanized id with an
    empty description in the Kit / Examine UI."""
    from combat import CLASS_MECHANIC_INFO
    missing = []
    for f in glob.glob(str(ROOT / 'data' / 'templates' / 'weapons' / '*.json')):
        d = json.load(open(f, encoding='utf-8'))
        mech = d.get('class_mechanic')
        if mech and mech not in CLASS_MECHANIC_INFO:
            missing.append(f"{os.path.basename(f)}: {mech}")
    assert not missing, (
        "weapon template mechanics missing from CLASS_MECHANIC_INFO:\n"
        + "\n".join(missing)
    )


def test_unique_weapon_mechanics_are_in_info_map():
    """Unique weapons (weapon.json) carry class_mechanic too -- every value
    used there must also be displayable."""
    from combat import CLASS_MECHANIC_INFO
    d = json.load(open(ROOT / 'data' / 'items' / 'weapon.json', encoding='utf-8'))
    missing = sorted({
        item['class_mechanic'] for item in d.values()
        if item.get('class_mechanic') and item['class_mechanic'] not in CLASS_MECHANIC_INFO
    })
    assert not missing, f"unique class_mechanics not in info map: {missing}"


def test_info_entries_have_name_and_desc():
    """Each curated entry must be a (non-empty name, non-empty description)."""
    from combat import CLASS_MECHANIC_INFO
    bad = []
    for mid, val in CLASS_MECHANIC_INFO.items():
        if not (isinstance(val, tuple) and len(val) == 2):
            bad.append(f"{mid}: not a 2-tuple")
            continue
        name, desc = val
        if not name or not name.strip():
            bad.append(f"{mid}: empty name")
        if not desc or not desc.strip():
            bad.append(f"{mid}: empty description")
    assert not bad, "\n".join(bad)


def test_class_mechanic_info_fallback_and_falsy():
    """Helper humanizes unknown ids (never blank) and returns None for falsy."""
    from combat import class_mechanic_info
    name, desc = class_mechanic_info('some_new_mech_at_max')
    assert name == 'Some New Mech'        # _at_max stripped, title-cased
    assert desc == ''                      # unknown -> no description
    assert class_mechanic_info(None) is None
    assert class_mechanic_info('') is None


def test_kit_weapon_special_shows_mechanic_name():
    """The Kit 'Special' column leads with the mechanic name once the weapon
    class is known (idl>=3), even before full identification."""
    from game_render import RenderMixin
    w = _w(class_mechanic='backstab')
    s3 = RenderMixin._kit_weapon_special(None, w, 3)
    assert 'Backstab' in s3
    # No mechanic -> a plain placeholder, never a crash.
    s_none = RenderMixin._kit_weapon_special(None, _w(), 5)
    assert isinstance(s_none, str)


def test_kit_weapon_special_gates_magical_extras():
    """Damage-type / blessing extras stay gated at idl>=4; the class mechanic
    is visible at idl>=3."""
    from game_render import RenderMixin
    w = _w(class_mechanic='backstab', two_handed=True)
    s3 = RenderMixin._kit_weapon_special(None, w, 3)
    s4 = RenderMixin._kit_weapon_special(None, w, 4)
    assert 'Backstab' in s3 and '2H' not in s3   # extras hidden at idl 3
    assert 'Backstab' in s4 and '2H' in s4       # extras shown at idl 4


def test_examine_detail_lines_name_and_description():
    """Examine surfaces the mechanic NAME line plus DESCRIPTION line(s) for a
    known weapon."""
    from game_render import RenderMixin
    from combat import CLASS_MECHANIC_INFO
    w = _w(class_mechanic='master_strike')
    lines = RenderMixin._weapon_mechanic_detail_lines(_FakeRenderSelf(idl=5), w)
    assert lines, "expected mechanic detail lines for a known weapon"
    assert 'Master Strike' in lines[0]
    # the curated description text appears on a following line
    desc = CLASS_MECHANIC_INFO['master_strike'][1]
    assert any(desc[:20] in ln for ln in lines[1:])


def test_examine_detail_lines_empty_cases():
    """No lines for non-weapons, mechanic-less weapons, or unidentified ones."""
    from game_render import RenderMixin
    # unidentified weapon (idl<3) hides its mechanic
    w = _w(class_mechanic='backstab')
    assert RenderMixin._weapon_mechanic_detail_lines(_FakeRenderSelf(idl=2), w) == []
    # weapon with no mechanic
    assert RenderMixin._weapon_mechanic_detail_lines(_FakeRenderSelf(idl=5), _w()) == []
    # non-weapon
    assert RenderMixin._weapon_mechanic_detail_lines(_FakeRenderSelf(idl=5), object()) == []


# ===========================================================================
# Bug 2 (secondary) -- chest loot must not include monster-derived ingredients
# ===========================================================================

def test_chest_common_pool_excludes_monster_ingredients():
    """A chest whose loot table includes 'ingredient' must only ever pool
    terrain-foraged ingredients (tier_role == 'dungeon') -- never family,
    prime, or trophy ingredients harvested from corpses."""
    import container_system
    pool = container_system._build_common_pool({'loot_table': {'ingredient': 1}}, 99)
    ingredients = [it for it in pool if type(it).__name__ == 'Ingredient']
    assert ingredients, "expected at least one foraged ingredient in the pool"
    leaked = [getattr(it, 'name', '?') for it in ingredients
              if getattr(it, 'tier_role', '') != 'dungeon']
    assert not leaked, f"monster-derived ingredients leaked into chest loot: {leaked}"


# ===========================================================================
# Bug 3 -- magic-missile WAND chain-scales (escalator-chain), not fixed bolt
# ===========================================================================

def test_magic_missile_wand_uses_escalator_chain_quiz():
    """_confirm_wand_target must route magic_missile through the escalator-chain
    science quiz and capture the chain on the game (reverting to a flat
    threshold quiz reintroduces the lame single-bolt behavior)."""
    import game_combat
    src = inspect.getsource(game_combat.CombatMixin._confirm_wand_target)
    assert 'escalator_chain' in src
    assert 'magic_missile' in src
    assert '_wand_chain' in src


def test_apply_wand_effect_magic_missile_scales_with_chain():
    """The magic_missile effect must derive its missile count from the captured
    chain (self._wand_chain), not solely from a fixed wand tier."""
    import game_magic
    src = inspect.getsource(game_magic.MagicMixin._apply_wand_effect)
    # locate the magic_missile branch and confirm it reads the chain
    idx = src.find("== 'magic_missile'")
    assert idx != -1, "magic_missile branch not found"
    window = src[idx:idx + 600]
    assert '_wand_chain' in window, "missile count no longer scales with the chain"


# ===========================================================================
# Bug 4 -- ranged attacks don't shoot through intervening enemies
# ===========================================================================

# Single-target projectiles that were flipped to piercing:false so they can be
# blocked by an intervening monster (same as the player's ranged attacks).
_SINGLE_TARGET_PROJECTILES = {
    'cyclops': 'boulder hurl',
    'hydra': 'acid spit',
    'fire_giant': 'magma hurl',
    'nidhogg_brood': 'shadow spit',
    'skeletal_giant': 'bone_hurl',
    'magma_elemental': 'lava spit',
    'stone_giant': 'rock hurl',
    'naga_guardian': 'poison_spit',
}

# AoE breath / beam / blast attacks that legitimately hit everything in line.
_AOE_BEAMS = {
    'chimera': 'fire_breath',
    'young_dragon': 'fire_breath',
    'adult_dragon': 'fire_breath',
    'ancient_dragon': 'frost_breath',
    'mind_flayer': 'mind_blast',
    'greater_lich': 'cold_wave',
}


def _monster_data():
    return json.load(open(ROOT / 'data' / 'monsters.json', encoding='utf-8'))


def test_single_target_projectiles_are_not_piercing():
    d = _monster_data()
    bad = []
    for mid, atk_name in _SINGLE_TARGET_PROJECTILES.items():
        m = d.get(mid)
        assert m, f"monster {mid} missing from monsters.json"
        atk = next((a for a in m.get('attacks', []) if a.get('name') == atk_name), None)
        assert atk, f"{mid} has no attack named {atk_name!r}"
        if atk.get('piercing') is True:
            bad.append(f"{mid}:{atk_name}")
    assert not bad, f"these single-target projectiles still pierce: {bad}"


def test_aoe_beams_still_pierce():
    """The AoE exception must remain: breath/beam attacks hit all in line."""
    d = _monster_data()
    bad = []
    for mid, atk_name in _AOE_BEAMS.items():
        m = d.get(mid)
        if not m:
            continue
        atk = next((a for a in m.get('attacks', []) if a.get('name') == atk_name), None)
        if atk and atk.get('piercing') is not True:
            bad.append(f"{mid}:{atk_name}")
    assert not bad, f"AoE beams that lost their piercing flag: {bad}"


def test_skeletal_archer_arrow_not_piercing():
    d = _monster_data()
    sa = d.get('skeletal_archer')
    assert sa, "skeletal_archer missing"
    assert sa.get('ai_pattern') == 'ranged'
    arrow = next((a for a in sa.get('attacks', []) if 'arrow' in a.get('name', '')), None)
    assert arrow, "skeletal_archer has no arrow attack"
    assert arrow.get('piercing') is not True


# ===========================================================================
# Crash found DURING the 2.0.3 play-test: game_magic referenced
# STATE_IDENTIFY_MENU without importing it, so reading a scroll of identify
# raised NameError at runtime (a code path no unit test exercised). Guard the
# whole class structurally with the AST: every bare STATE_* name LOADED in a
# module must be imported from game_states (or assigned locally). Using the AST
# (not a text grep) avoids false positives from comments / docstrings.
# ===========================================================================

def test_all_state_constants_are_imported_where_used():
    import ast
    src_dir = ROOT / 'src'

    defined = set()
    st_tree = ast.parse((src_dir / 'game_states.py').read_text(encoding='utf-8'))
    for node in ast.walk(st_tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.startswith('STATE_'):
                    defined.add(t.id)
    assert defined, "no STATE_ constants found in game_states.py"

    problems = []
    for f in sorted(src_dir.glob('*.py')):
        if f.name == 'game_states.py':
            continue
        tree = ast.parse(f.read_text(encoding='utf-8'))
        imported = set()
        imports_module = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == 'game_states':
                imported |= {a.asname or a.name for a in node.names}
            elif isinstance(node, ast.Import):
                if any(a.name == 'game_states' for a in node.names):
                    imports_module = True
        if imports_module:
            continue  # uses game_states.STATE_X attribute access -- always resolves
        used, assigned = set(), set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in defined:
                if isinstance(node.ctx, ast.Load):
                    used.add(node.id)
                elif isinstance(node.ctx, ast.Store):
                    assigned.add(node.id)
        missing = used - imported - assigned
        if missing:
            problems.append(f"{f.name}: {sorted(missing)}")
    assert not problems, (
        "modules reference STATE_ constants they never imported "
        "(NameError at runtime):\n" + "\n".join(problems)
    )
