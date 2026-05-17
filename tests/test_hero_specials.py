"""Tests for the 2026-05-17 hero specials rebuild (Phase 3B/3C/3D)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ---------------------------------------------------------------------------
# Data shape — every hero special has the required fields
# ---------------------------------------------------------------------------

_REQUIRED_ACTIVE_FIELDS = {'id', 'name', 'desc', 'cooldown', 'effect', 'tier_effects'}


def test_every_active_special_has_required_fields():
    import hero_specials
    for build_name, sp in hero_specials.HERO_SPECIALS.items():
        if sp is None:
            continue
        actives = sp if isinstance(sp, list) else [sp]
        for s in actives:
            if not isinstance(s, dict):
                continue
            missing = _REQUIRED_ACTIVE_FIELDS - set(s.keys())
            assert not missing, f"{build_name} -> {s.get('id')}: missing {missing}"


def test_tier_effects_cover_0_to_5():
    """Every active special must define tier_effects for chain depths 0..5."""
    import hero_specials
    for build_name, sp in hero_specials.HERO_SPECIALS.items():
        if sp is None:
            continue
        actives = sp if isinstance(sp, list) else [sp]
        for s in actives:
            if not isinstance(s, dict):
                continue
            te = s.get('tier_effects', {})
            for chain in range(6):
                assert chain in te, f"{s.get('id')}: tier_effects missing chain {chain}"


def test_hero_special_ids_are_unique():
    import hero_specials
    seen = set()
    for sp in hero_specials.HERO_SPECIALS.values():
        if sp is None:
            continue
        actives = sp if isinstance(sp, list) else [sp]
        for s in actives:
            if not isinstance(s, dict):
                continue
            assert s['id'] not in seen, f"duplicate hero special id: {s['id']}"
            seen.add(s['id'])


def test_hero_special_ids_start_with_hero():
    """The 'hero_' prefix is what _activate_power uses to route to the resolver."""
    import hero_specials
    for sp in hero_specials.HERO_SPECIALS.values():
        if sp is None:
            continue
        actives = sp if isinstance(sp, list) else [sp]
        for s in actives:
            if not isinstance(s, dict):
                continue
            assert s['id'].startswith('hero_'), \
                f"hero special id must start with 'hero_': {s['id']}"


def test_every_active_effect_has_a_resolver():
    """Each effect string must map to a resolver in _DISPATCH."""
    import hero_specials
    for sp in hero_specials.HERO_SPECIALS.values():
        if sp is None:
            continue
        actives = sp if isinstance(sp, list) else [sp]
        for s in actives:
            if not isinstance(s, dict):
                continue
            eff = s.get('effect')
            assert eff in hero_specials._DISPATCH, \
                f"{s['id']}: effect '{eff}' has no resolver"


# ---------------------------------------------------------------------------
# SECRET_BUILDS integration — every build referenced in HERO_SPECIALS exists
# ---------------------------------------------------------------------------

def test_hero_specials_builds_exist_in_secret_builds():
    import hero_specials
    import welcome_screen
    for build_name in hero_specials.HERO_SPECIALS:
        assert build_name in welcome_screen.SECRET_BUILDS, \
            f"HERO_SPECIALS has '{build_name}' but it's not in SECRET_BUILDS"


def test_hero_passives_builds_exist_in_secret_builds():
    import hero_specials
    import welcome_screen
    for build_name in hero_specials.HERO_PASSIVES:
        assert build_name in welcome_screen.SECRET_BUILDS, \
            f"HERO_PASSIVES has '{build_name}' but it's not in SECRET_BUILDS"


def test_all_8_new_builds_present():
    import welcome_screen
    new_builds = [
        'ada augusta byron lovelace',
        'leonardo di ser piero da vinci',
        'boudicca queen of the iceni',
        'saint joan of arc maid of orleans',
        "sir arthur conan doyle's sherlock holmes",
        'miyamoto musashi the sword saint',
        'saint hildegard von bingen',
        'nikola tesla the wizard of menlo park',
    ]
    for name in new_builds:
        assert name in welcome_screen.SECRET_BUILDS, f"missing build: {name}"
        b = welcome_screen.SECRET_BUILDS[name]
        # Each new build should have a greeting and a sprite
        assert '_greeting' in b, f"{name}: missing _greeting"


# ---------------------------------------------------------------------------
# Journal entries — every active/passive build has a journal line
# ---------------------------------------------------------------------------

def test_every_hero_build_has_journal_entry():
    """Builds with either an active special OR a passive should have a journal entry."""
    import hero_specials
    builds_with_specials = set(hero_specials.HERO_SPECIALS) | set(hero_specials.HERO_PASSIVES)
    for name in builds_with_specials:
        entry = hero_specials.HERO_JOURNAL.get(name)
        assert entry, f"{name}: missing journal entry"


# ---------------------------------------------------------------------------
# Boss-immunity helper
# ---------------------------------------------------------------------------

def test_is_boss_or_huge_handles_none():
    from hero_specials import is_boss_or_huge
    assert is_boss_or_huge(None) is False


def test_is_boss_or_huge_recognizes_flag():
    from hero_specials import is_boss_or_huge

    class M:
        is_boss = True
        max_hp = 100
    assert is_boss_or_huge(M()) is True


def test_is_boss_or_huge_recognizes_high_hp():
    from hero_specials import is_boss_or_huge

    class M:
        is_boss = False
        max_hp = 600
    assert is_boss_or_huge(M()) is True


def test_is_boss_or_huge_skips_normal():
    from hero_specials import is_boss_or_huge

    class M:
        is_boss = False
        max_hp = 60
    assert is_boss_or_huge(M()) is False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def test_get_specials_for_build_returns_list():
    """Ash Williams has 3 actives; others usually 0 or 1."""
    from hero_specials import get_specials_for_build
    ash = get_specials_for_build('ash williams')
    assert len(ash) == 3, f"Ash Williams should have 3 actives; got {len(ash)}"
    achilles = get_specials_for_build('achilles son of peleus')
    assert achilles == []   # passive build
    aristotle = get_specials_for_build('aristotle of stagira')
    assert len(aristotle) == 1


def test_get_passives_for_build():
    from hero_specials import get_passives_for_build
    plato = get_passives_for_build('plato of athens')
    assert 'plato_no_shard' in plato
    geralt = get_passives_for_build('geralt of rivia')
    assert 'witcher_mutations' in geralt
    assert 'witcher_resists' in geralt
    achilles = get_passives_for_build('achilles son of peleus')
    assert achilles == ['demigod_hide_25']


# ---------------------------------------------------------------------------
# Off-curve item rebalance smoke checks
# ---------------------------------------------------------------------------

def test_achilles_spear_is_tier_1_now():
    import json
    from pathlib import Path
    w = json.loads(Path('data/items/weapon.json').read_text(encoding='utf-8'))
    spear = w['achilles_spear']
    assert spear['tier'] == 1
    assert spear['peak_floor'] <= 10
    assert spear['baseDamage'] <= 7


def test_tablet_of_hammurabi_is_starter_grade():
    import json
    from pathlib import Path
    a = json.loads(Path('data/items/accessory.json').read_text(encoding='utf-8'))
    tab = a['tablet_of_hammurabi']
    assert tab['peak_floor'] <= 12
    assert tab['effects']['amount'] == 1


def test_ring_protection_iron_exists():
    import json
    from pathlib import Path
    a = json.loads(Path('data/items/accessory.json').read_text(encoding='utf-8'))
    assert 'ring_protection_iron' in a
    r = a['ring_protection_iron']
    assert r['tier'] == 1
    assert r['peak_floor'] <= 10
    assert r['effects'] == {'stat': 'AC', 'amount': 1}


# ---------------------------------------------------------------------------
# Monster tag — female_attractive
# ---------------------------------------------------------------------------

def test_female_attractive_tag_on_expected_monsters():
    import json
    from pathlib import Path
    m = json.loads(Path('data/monsters.json').read_text(encoding='utf-8'))
    expected = ['lamia', 'succubus_shade', 'dryad_guardian', 'harpy',
                'banshee', 'medusa', 'medusa_gorgon']
    for kind in expected:
        if kind in m:
            assert 'female_attractive' in m[kind].get('tags', []), \
                f"{kind}: missing 'female_attractive' tag"
