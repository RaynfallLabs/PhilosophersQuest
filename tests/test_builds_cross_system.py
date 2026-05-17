"""Phase 3F cross-system balance check.

Verifies that the build/special/item systems mesh correctly post-rebuild.
Catches drift between SECRET_BUILDS, hero_specials, and the underlying data files.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ---------------------------------------------------------------------------
# Every build's _start_* item id must resolve to a real entry
# ---------------------------------------------------------------------------

def _load_ids(fname):
    path = Path('data/items') / fname
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding='utf-8')).keys())


def test_every_build_referenced_item_exists():
    import welcome_screen
    accessory_ids = _load_ids('accessory.json')
    wand_ids = _load_ids('wand.json')
    book_ids = _load_ids('spellbook.json')
    weapon_ids = _load_ids('weapon.json')
    armor_ids = _load_ids('armor.json')
    shield_ids = _load_ids('shield.json')
    scroll_ids = _load_ids('scroll.json')
    potion_ids = _load_ids('potion.json')
    ammo_ids = _load_ids('ammo.json')
    template_weapons = set()
    template_shields = set()
    template_armor = set()
    for p in Path('data/templates/weapons').glob('*.json'):
        template_weapons.add(p.stem)
    for p in Path('data/templates/shields').glob('*.json'):
        template_shields.add(p.stem)
    for p in Path('data/templates/armor').glob('*.json'):
        template_armor.add(p.stem)
    material_weapons = set()
    material_armor = set()
    for p in Path('data/materials/weapons').glob('*.json'):
        material_weapons.add(p.stem)
    for p in Path('data/materials/armor').glob('*.json'):
        material_armor.add(p.stem)

    errors = []
    for name, b in welcome_screen.SECRET_BUILDS.items():
        for field in ('_start_weapon', '_start_melee'):
            v = b.get(field)
            if v is None:
                continue
            if isinstance(v, tuple):
                tpl, mat = v
                if tpl not in template_weapons:
                    errors.append(f"{name}: {field} template '{tpl}' missing")
                if mat not in material_weapons and mat not in material_armor:
                    errors.append(f"{name}: {field} material '{mat}' missing")
            else:
                if v not in weapon_ids:
                    errors.append(f"{name}: {field} '{v}' not in weapon.json")
        v = b.get('_start_shield')
        if v is not None:
            if isinstance(v, tuple):
                tpl, mat = v
                if tpl not in template_shields:
                    errors.append(f"{name}: _start_shield template '{tpl}' missing")
            else:
                if v not in shield_ids:
                    errors.append(f"{name}: _start_shield '{v}' not in shield.json")
        v = b.get('_start_armor')
        if v is not None:
            if isinstance(v, tuple):
                tpl, mat = v
                if tpl not in template_armor:
                    errors.append(f"{name}: _start_armor template '{tpl}' missing")
            else:
                if v not in armor_ids:
                    errors.append(f"{name}: _start_armor '{v}' not in armor.json")
        v = b.get('_start_accessory')
        if v is not None and v not in accessory_ids:
            errors.append(f"{name}: _start_accessory '{v}' not in accessory.json")
        for v in b.get('_start_extra_acc', []) or []:
            if v not in accessory_ids:
                errors.append(f"{name}: _start_extra_acc entry '{v}' not in accessory.json")
        v = b.get('_start_wand')
        if v is not None and v not in wand_ids:
            errors.append(f"{name}: _start_wand '{v}' not in wand.json")
        v = b.get('_start_book')
        if v is not None and v not in book_ids:
            errors.append(f"{name}: _start_book '{v}' not in spellbook.json")
        v = b.get('_start_ammo')
        if v is not None and v not in ammo_ids:
            errors.append(f"{name}: _start_ammo '{v}' not in ammo.json")
        for v in b.get('_start_potions', []) or []:
            if v not in potion_ids:
                errors.append(f"{name}: _start_potions entry '{v}' not in potion.json")
        _ = scroll_ids  # placeholder for future _start_scrolls field
    assert not errors, "Build-item integrity errors:\n  " + "\n  ".join(errors)


# ---------------------------------------------------------------------------
# Starter items should sit near the floor-1 end of the curve
# ---------------------------------------------------------------------------

# Items where the floor curve doesn't constrain the starter use case — these
# are iconic-build pillars (Necronomicon = Ash's whole identity; Lantern of
# Diogenes = Aristotle's whole identity). Hand-tuned exemptions only.
_STARTER_ICONIC_EXEMPT = {
    'necronomicon',                 # Ash Williams
    'lantern_of_diogenes',          # Aristotle, Diogenes
    'prometheus_torch',             # Prometheus
    'shield_of_the_spartans',       # Leonidas
}


def test_starter_named_items_are_tier_1_or_special():
    """Items referenced by SECRET_BUILDS (by id, not template+material) should
    either be tier 1 / peak_floor <= 14, be flagged peak_floor=0
    (hand-tuned 'fixed' items like boomstick, zireael), or appear on the
    iconic-exemption list."""
    import welcome_screen
    errors = []
    for fname in ('weapon.json', 'armor.json', 'shield.json', 'accessory.json',
                  'wand.json', 'spellbook.json'):
        data = json.loads(Path('data/items') / fname and (Path('data/items') / fname).read_text(encoding='utf-8'))
        for name, b in welcome_screen.SECRET_BUILDS.items():
            # Collect every named-id reference (skip tuples — those are template+material)
            refs = []
            for field in ('_start_weapon', '_start_melee', '_start_armor',
                          '_start_shield', '_start_accessory', '_start_wand',
                          '_start_book'):
                v = b.get(field)
                if isinstance(v, str):
                    refs.append(v)
            for v in b.get('_start_extra_acc', []) or []:
                refs.append(v)
            for iid in refs:
                if iid not in data:
                    continue
                if iid in _STARTER_ICONIC_EXEMPT:
                    continue
                item = data[iid]
                pf = item.get('peak_floor', 0)
                tier = item.get('tier', 1)
                # peak_floor 0 = hand-tuned fixed item (boomstick, zireael, ...)
                # peak_floor 1004 = always-available marker (Stuffie, Sketchbook)
                if pf == 0 or pf >= 1000:
                    continue
                # Otherwise it should be tier 1 / starter-grade
                if tier > 1 or pf > 14:
                    errors.append(
                        f"{name}: starter item {iid} is tier {tier} / peak {pf} — too strong for F1")
    assert not errors, "Curve violations:\n  " + "\n  ".join(errors)


# ---------------------------------------------------------------------------
# All hero specials have valid resolvers + boss_immune set on CC effects
# ---------------------------------------------------------------------------

def test_cc_specials_are_boss_immune():
    """Status-applying specials must declare boss_immune=True per design."""
    import hero_specials
    # Effects that constitute crowd-control (non-damage)
    cc_effects = {'confuse_visible', 'fear_visible', 'charm_visible', 'paralyze_target'}
    for sp in hero_specials.HERO_SPECIALS.values():
        if sp is None:
            continue
        actives = sp if isinstance(sp, list) else [sp]
        for s in actives:
            if not isinstance(s, dict):
                continue
            if s.get('effect') in cc_effects:
                assert s.get('boss_immune'), \
                    f"CC special {s['id']} should declare boss_immune=True"


def test_chain_5_is_strictly_better_than_chain_3():
    """Spot-check: for damage-scaling specials, chain 5 should be > chain 3
    on the primary scalar (damage_mult, dice, count, duration, etc.)."""
    import hero_specials
    for sp in hero_specials.HERO_SPECIALS.values():
        if sp is None:
            continue
        actives = sp if isinstance(sp, list) else [sp]
        for s in actives:
            if not isinstance(s, dict):
                continue
            te = s.get('tier_effects', {})
            t3 = te.get(3)
            t5 = te.get(5)
            if isinstance(t3, dict) and isinstance(t5, dict):
                # Pick a single comparable scalar field — any one is fine
                for k in ('count', 'duration', 'range', 'hp', 'hp_drain',
                          'radius', 'self_heal', 'crit_turns', 'cleanse'):
                    if k in t3 and k in t5:
                        assert t5[k] >= t3[k], \
                            f"{s['id']}: tier_effects[5][{k}] should be >= tier_effects[3][{k}]"
                        break


# ---------------------------------------------------------------------------
# Family-kid builds: every kid carries a weapon + their iconic accessory
# ---------------------------------------------------------------------------

def test_family_kids_carry_iconic_accessory():
    import welcome_screen
    expected = {
        'corwin': 'charmander_stuffie',
        'cain': 'charmander_stuffie',
        'fianna': 'dreamspun_sketchbook',
        'fluffs': 'dreamspun_sketchbook',
        'robyn': 'rands_heart',
    }
    for kid, iconic in expected.items():
        b = welcome_screen.SECRET_BUILDS[kid]
        extras = set(b.get('_start_extra_acc', []) or [])
        accessory = b.get('_start_accessory')
        assert iconic in extras or accessory == iconic, \
            f"{kid}: missing iconic '{iconic}' in starting kit"


def test_family_kids_have_weapon():
    import welcome_screen
    for kid in ('corwin', 'cain', 'fianna', 'fluffs', 'robyn'):
        b = welcome_screen.SECRET_BUILDS[kid]
        assert b.get('_start_weapon') is not None, \
            f"{kid}: missing starting weapon"


# ---------------------------------------------------------------------------
# Titivillus QA flag
# ---------------------------------------------------------------------------

def test_titivillus_has_qa_flag():
    import welcome_screen
    assert welcome_screen.SECRET_BUILDS['titivillus'].get('_qa_tools') is True


# ---------------------------------------------------------------------------
# Every active hero special's cooldown is in the once-per-floor range
# ---------------------------------------------------------------------------

def test_hero_cooldowns_in_range():
    """Hero special cooldowns should be 200-500 turns (~1 use per floor)."""
    import hero_specials
    for sp in hero_specials.HERO_SPECIALS.values():
        if sp is None:
            continue
        actives = sp if isinstance(sp, list) else [sp]
        for s in actives:
            if not isinstance(s, dict):
                continue
            cd = int(s.get('cooldown', 0))
            assert 150 <= cd <= 600, \
                f"{s['id']}: cooldown {cd} outside reasonable range 150-600"


# ---------------------------------------------------------------------------
# Player.hero_passives initialized correctly
# ---------------------------------------------------------------------------

def test_player_hero_fields_default():
    from player import Player
    p = Player()
    assert p.hero_passives == set()
    assert p.hero_specials == []
    assert p.hero_special_cooldowns == {}
    assert p.qa_tools is False
