"""Quest and special-item lifecycle pin tests.

These pin the critical spawn / consume / effect wiring so any future
refactor that breaks them shows up immediately. The audit (2026-05-31)
verified each of these by tracing code paths inline; this file locks
them in.

Covered:
- Mini-boss → unique_drop_id → item exists in data
- Mini-boss spawn_chance > 0 (except Cow King — portal-based)
- Seal demon peak_floor matches SEAL_DEMON_FLOORS in level_manager
- Seal kill increments seals_broken (combat hook)
- F99 Pit gate requires len(seals_broken) >= 7
- Disabled items (pandoras_box, aladdins_lamp, wand_of_wonder_legendary)
  have no spawn references
- Plot-locked NPC reward items exist + are reachable
- Duck of Doom full lifecycle is wired
- _spawn_unique_item covers all categories used by unique_drop_id
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


def _load(rel):
    with open(ROOT / rel, encoding='utf-8') as f:
        return json.load(f)


def _all_items():
    out = {}
    for path in glob.glob(str(ROOT / "data" / "items" / "*.json")):
        cat = os.path.basename(path)[:-5]
        with open(path, encoding='utf-8') as f:
            for iid, it in json.load(f).items():
                out[iid] = (cat, it)
    return out


# ---------------------------------------------------------------------------
# Mini-boss → unique_drop_id reachability
# ---------------------------------------------------------------------------

EXPECTED_MINI_BOSSES = {
    'anansi', 'arachne', 'baba_yaga', 'cacus', 'camazotz', 'charybdis',
    'cow_king', 'echidna', 'erlking', 'green_knight', 'jormungandr_juvenile',
    'nemean_lion', 'nidhoggr_fragment', 'ravanas_arm', 'sets_jackal',
    'talos', 'the_sphinx', 'wendigo', 'wild_hunt_captain',
}

# Cow King is reached only via the Cow Level portal — spawn_chance 0 is correct.
PORTAL_ONLY_MINI_BOSSES = {'cow_king'}


def test_all_mini_bosses_exist_in_monsters_json():
    monsters = _load('data/monsters.json')
    missing = [b for b in EXPECTED_MINI_BOSSES if b not in monsters]
    assert not missing, f"Missing mini-boss defs: {missing}"


def test_mini_bosses_flagged_is_mini_boss():
    monsters = _load('data/monsters.json')
    bad = [b for b in EXPECTED_MINI_BOSSES
           if not monsters[b].get('is_mini_boss')]
    assert not bad, f"Mini-bosses missing is_mini_boss: {bad}"


def test_mini_bosses_have_spawn_chance():
    """Non-portal mini-bosses must have spawn_chance > 0 to ever appear."""
    monsters = _load('data/monsters.json')
    bad = []
    for b in EXPECTED_MINI_BOSSES - PORTAL_ONLY_MINI_BOSSES:
        if monsters[b].get('spawn_chance', 0) <= 0:
            bad.append(b)
    assert not bad, f"Mini-bosses with spawn_chance 0: {bad}"


def test_mini_boss_drops_resolve_to_real_items():
    monsters = _load('data/monsters.json')
    items = _all_items()
    bad = []
    for b in EXPECTED_MINI_BOSSES:
        drop = monsters[b].get('treasure', {}).get('unique_drop_id')
        if drop and drop not in items:
            bad.append((b, drop))
    assert not bad, f"Mini-bosses with unresolved drops: {bad}"


# ---------------------------------------------------------------------------
# Seal demon → F99 Pit gate
# ---------------------------------------------------------------------------

SEAL_DEMON_FLOORS = {
    83: 'seal_demon_wrath', 85: 'seal_demon_pestilence',
    87: 'seal_demon_famine', 89: 'seal_demon_war',
    91: 'seal_demon_death', 93: 'seal_demon_earthquake',
    97: 'seal_demon_silence',
}


def test_seal_demon_peak_floor_alignment():
    """Each seal demon's peak_floor must match its forced spawn floor."""
    monsters = _load('data/monsters.json')
    bad = []
    for lvl, did in SEAL_DEMON_FLOORS.items():
        mon = monsters.get(did)
        if not mon:
            bad.append(f"{did} missing")
            continue
        if mon.get('peak_floor') != lvl:
            bad.append(f"{did}: pf {mon.get('peak_floor')} != {lvl}")
        if not mon.get('is_seal_demon'):
            bad.append(f"{did}: is_seal_demon False")
        if not mon.get('is_mini_boss'):
            bad.append(f"{did}: is_mini_boss False")
    assert not bad, bad


def test_seal_demon_drops_match_kind():
    """Each seal demon must drop seal_of_<kind> matching its name."""
    monsters = _load('data/monsters.json')
    bad = []
    for did in SEAL_DEMON_FLOORS.values():
        mon = monsters[did]
        expected = 'seal_of_' + did.replace('seal_demon_', '')
        drop = mon.get('treasure', {}).get('unique_drop_id')
        if drop != expected:
            bad.append(f"{did}: drops {drop}, expected {expected}")
    assert not bad, bad


def test_seal_demon_floors_match_level_manager():
    """level_manager.SEAL_DEMON_FLOORS must match the JSON."""
    src = (ROOT / "src" / "level_manager.py").read_text(encoding='utf-8')
    for lvl, did in SEAL_DEMON_FLOORS.items():
        assert f"{lvl}: '{did}'" in src or f'{lvl}: "{did}"' in src, \
            f"level_manager missing {lvl}: {did}"


def test_seal_kill_increments_seals_broken():
    """game_combat handler must add seal id to seals_broken on demon kill."""
    src = (ROOT / "src" / "game_combat.py").read_text(encoding='utf-8')
    assert "is_seal_demon" in src
    assert "seals_broken.add" in src
    assert "seal_of_" in src


def test_f99_pit_gate_requires_seven_seals():
    src = (ROOT / "src" / "main.py").read_text(encoding='utf-8')
    assert "self.dungeon_level == 99" in src
    assert "len(self.seals_broken) < 7" in src


# ---------------------------------------------------------------------------
# Disabled chaos/wish/wonder items have no code references
# ---------------------------------------------------------------------------

DISABLED_ITEMS = ('pandoras_box', 'aladdins_lamp', 'wand_of_wonder_legendary')


def test_disabled_items_have_no_code_references():
    """No src/*.py file should import or reference these by id."""
    for disabled in DISABLED_ITEMS:
        for src_file in glob.glob(str(ROOT / "src" / "*.py")):
            text = open(src_file, encoding='utf-8').read()
            assert disabled not in text, \
                f"{disabled} referenced in {os.path.basename(src_file)} — should be code-orphan"


def test_disabled_items_have_no_min_level_spawn():
    """Disabled items must be unreachable via natural spawn (min_level >= 9999)."""
    items = _all_items()
    for disabled in DISABLED_ITEMS:
        if disabled in items:
            cat, it = items[disabled]
            assert it.get('min_level', 0) >= 9999, \
                f"{disabled} min_level {it.get('min_level')} — would spawn naturally"
            assert it.get('peak_floor', 1) == 0, \
                f"{disabled} peak_floor {it.get('peak_floor')} — would weight-spawn"
            assert it.get('_disabled_reason'), \
                f"{disabled} missing _disabled_reason marker"


# ---------------------------------------------------------------------------
# Plot-locked NPC reward items exist + reachable
# ---------------------------------------------------------------------------

NPC_REWARD_ITEMS = ('saints_reliquary', 'officers_signet', 'prophets_amulet')


def test_npc_reward_items_exist():
    items = _all_items()
    bad = [iid for iid in NPC_REWARD_ITEMS if iid not in items]
    assert not bad, f"NPC reward items missing from JSON: {bad}"


def test_npc_reward_items_referenced_in_npc_encounters():
    src = (ROOT / "src" / "npc_encounters.py").read_text(encoding='utf-8')
    bad = [iid for iid in NPC_REWARD_ITEMS if iid not in src]
    assert not bad, f"NPC reward items not referenced in encounters: {bad}"


# ---------------------------------------------------------------------------
# Duck of Doom lifecycle
# ---------------------------------------------------------------------------

def test_duck_of_doom_full_lifecycle_wired():
    """Duck of Doom must have: random floor placement, auto-equip on pickup,
    per-turn tick, transform-to-pet on 2026 turns."""
    src = (ROOT / "src" / "main.py").read_text(encoding='utf-8')
    assert "_duck_of_doom_floor" in src
    assert "_maybe_place_duck_of_doom" in src
    assert "_duck_of_doom_pickup" in src
    assert "_duck_of_doom_tick" in src
    assert "_duck_of_doom_transform" in src


def test_duck_of_doom_in_armor_with_auto_equip():
    items = _all_items()
    assert 'duck_of_doom' in items
    cat, duck = items['duck_of_doom']
    assert cat == 'armor'
    assert duck.get('auto_equip_on_pickup') is True


# ---------------------------------------------------------------------------
# _spawn_unique_item covers all drop categories
# ---------------------------------------------------------------------------

def test_spawn_unique_item_covers_all_drop_categories():
    """The category list in _spawn_unique_item must include every category
    that any mini-boss unique_drop_id points to."""
    monsters = _load('data/monsters.json')
    items = _all_items()
    drop_categories = set()
    for mon in monsters.values():
        drop = mon.get('treasure', {})
        if isinstance(drop, dict) and drop.get('unique_drop_id'):
            iid = drop['unique_drop_id']
            if iid in items:
                drop_categories.add(items[iid][0])

    src = (ROOT / "src" / "main.py").read_text(encoding='utf-8')
    # Find the _spawn_unique_item function and check its categories tuple.
    marker = "def _spawn_unique_item"
    assert marker in src
    snippet = src[src.index(marker):src.index(marker) + 800]
    missing = []
    for cat in drop_categories:
        if f"'{cat}'" not in snippet:
            missing.append(cat)
    assert not missing, \
        f"_spawn_unique_item categories missing: {missing} (drops include {drop_categories})"


# ---------------------------------------------------------------------------
# Charges decrement on use
# ---------------------------------------------------------------------------

def test_lyre_and_hand_of_glory_charge_dispatch():
    """The power-menu accessory-charge activation must decrement charges."""
    src = (ROOT / "src" / "game_menus.py").read_text(encoding='utf-8')
    assert "_activate_accessory_charge" in src
    assert "acc.charges -= 1" in src


# ---------------------------------------------------------------------------
# Resurrect / death-save items
# ---------------------------------------------------------------------------

def test_jade_cicada_death_save_wired():
    """game_combat must respect death_save flag (Jade Cicada)."""
    src = (ROOT / "src" / "game_combat.py").read_text(encoding='utf-8')
    assert "death_save" in src
    assert "jade cicada" in src.lower() or "Jade Cicada" in src


def test_ankh_of_isis_resurrect_wired():
    """game_combat must respect resurrect_on_death (Ankh of Isis)."""
    src = (ROOT / "src" / "game_combat.py").read_text(encoding='utf-8')
    assert "resurrect_on_death" in src
    assert "Ankh of Isis" in src or "ankh" in src.lower()
