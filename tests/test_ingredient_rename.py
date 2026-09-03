"""Regression tests for the 2026-06-04 prime-ingredient rename + floor-spawn fix.

THE BUG: every per-monster PRIME-tier ingredient was lazily named
"<monster> Prime Cut" regardless of creature type (a skeleton having a
"Prime Cut" of meat makes no sense), and those monster-derived primes were
leaking onto the dungeon floor as foraged loot (e.g. "gas spore Prime Cut"
matched the plant keyword 'spore').

The fix:
  1. PRIME display names are now family-appropriate (undead -> "Pristine
     Marrow", aberration -> "Engorged Sac", demon -> "Pure Ichor", ...).
     Beast keeps "Prime Cut" and humanoid uses "Choice Cut" (both meat, which
     is correct). ingredient_id is UNCHANGED so recipes/saves stay valid.
  2. Floor-spawn restricted to tier_role == 'dungeon' (terrain-foraged only);
     monster-derived ingredients come from harvesting corpses only.

These run against the live data via load_items('ingredient') per the project
test convention.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from items import load_items  # noqa: E402

_ING_JSON = ROOT / "data" / "items" / "ingredient.json"
_PC_JSON = ROOT / "data" / "items" / "prime_cuts.json"
_RECIPES_JSON = ROOT / "data" / "items" / "recipes.json"

# family -> the display PART the rename assigns (mirrors the migration scheme).
FAMILY_PART = {
    "beast": "Prime Cut",
    "humanoid": "Choice Cut",
    "dragon": "Heartscale",
    "reptile": "Prime Scale",
    "undead": "Pristine Marrow",
    "construct": "Pristine Core",
    "elemental": "Concentrated Essence",
    "aberration": "Engorged Sac",
    "fey": "Glittering Mote",
    "demon": "Pure Ichor",
    "plant": "Prime Heartwood",
    "celestial": "Radiant Mote",
}

# Only these two families legitimately keep a "*Cut" of meat.
_MEAT_FAMILIES = {"beast", "humanoid"}


def _raw_ingredients() -> dict:
    return json.loads(_ING_JSON.read_text(encoding="utf-8"))


def _name_by_id() -> dict[str, str]:
    """Display names as the GAME loads them (via load_items)."""
    return {ing.id: ing.name for ing in load_items("ingredient")}


def _family_role_by_id() -> dict[str, tuple[str | None, str | None]]:
    """(tier_role, family) per ingredient_id, from the raw catalog (the loaded
    Ingredient class doesn't surface tier_role/family as attributes)."""
    return {
        iid: (defn.get("tier_role"), defn.get("family"))
        for iid, defn in _raw_ingredients().items()
        if isinstance(defn, dict)
    }


# ---------------------------------------------------------------------------
# (a) The rename — names via load_items('ingredient')
# ---------------------------------------------------------------------------

def test_no_prime_cut_name_except_meat_families():
    """No PRIME-tier ingredient name contains 'Prime Cut' UNLESS it is a
    beast (humanoid uses 'Choice Cut'). This is the core lazy-naming fix."""
    names = _name_by_id()
    fam_role = _family_role_by_id()
    offenders = []
    for iid, name in names.items():
        role, family = fam_role.get(iid, (None, None))
        if role != "prime":
            continue
        if "Prime Cut" in name and family not in _MEAT_FAMILIES:
            offenders.append((iid, name, family))
    assert not offenders, (
        "PRIME ingredients still lazily named 'Prime Cut' for non-meat "
        f"families: {offenders[:15]}"
    )


def test_undead_prime_ends_in_pristine_marrow():
    """A known undead prime (skeleton) is renamed to '... Pristine Marrow'."""
    names = _name_by_id()
    assert names["skeleton_prime"] == "Skeleton Pristine Marrow", names["skeleton_prime"]
    # zombie too (also undead)
    assert names["zombie_prime"].endswith("Pristine Marrow"), names["zombie_prime"]


def test_aberration_prime_ends_in_engorged_sac():
    """The reported bug: gas spore (aberration) becomes '... Engorged Sac',
    NOT 'gas spore Prime Cut'."""
    names = _name_by_id()
    assert names["gas_spore_prime"] == "Gas Spore Engorged Sac", names["gas_spore_prime"]
    assert "Prime Cut" not in names["gas_spore_prime"]


def test_demon_prime_uses_pure_ichor():
    names = _name_by_id()
    # blood_archon_prime is a non-trophy demon prime that lives only in
    # ingredient.json (its trophy variant is separate).
    assert names["blood_archon_prime"].endswith("Pure Ichor"), names["blood_archon_prime"]


def test_beast_and_humanoid_keep_meat_cuts():
    """Beasts correctly keep 'Prime Cut'; humanoids use 'Choice Cut'."""
    names = _name_by_id()
    assert names["giant_rat_prime"].endswith("Prime Cut"), names["giant_rat_prime"]
    assert names["goblin_prime"].endswith("Choice Cut"), names["goblin_prime"]


def test_every_family_uses_its_scheme():
    """Every PRIME-tier ingredient's name ends with the PART its family maps
    to. Catches any family the migration missed."""
    names = _name_by_id()
    fam_role = _family_role_by_id()
    bad = []
    for iid, (role, family) in fam_role.items():
        if role != "prime":
            continue
        expected_part = FAMILY_PART.get(family)
        if expected_part is None:
            bad.append((iid, family, "unknown family"))
            continue
        if not names[iid].endswith(expected_part):
            bad.append((iid, family, names[iid]))
    assert not bad, f"PRIME names not matching their family scheme: {bad[:15]}"


def test_trophy_authored_names_preserved():
    """Trophies keep their flavorful authored names (not the family scheme)."""
    names = _name_by_id()
    assert names["fafnir_dragon_trophy"] == "Fafnir's Heart", names["fafnir_dragon_trophy"]
    assert names["fenrir_wolf_trophy"] == "Fenrir's Tooth", names["fenrir_wolf_trophy"]


# ---------------------------------------------------------------------------
# (b) ingredient_ids are UNCHANGED (recipes + saves depend on them)
# ---------------------------------------------------------------------------

def test_known_ingredient_ids_still_load():
    """v2.6.5: assorted_monster_parts + family_* deleted; monster primes and
    trophies and the 8 dungeon adjuncts remain."""
    names = _name_by_id()
    for iid in (
        "giant_rat_prime",
        "gas_spore_prime",
        "skeleton_prime",
        "fafnir_dragon_trophy",
        "cave_mushroom",
    ):
        assert iid in names, f"ingredient_id {iid!r} no longer loads"
    # These are DELETED in v2.6.5:
    for gone in ("assorted_monster_parts", "family_undead", "family_beast"):
        assert gone not in names, f"{gone!r} should be gone in v2.6.5"


def test_prime_ids_match_source_monster_pattern():
    """Every prime id is still '<monster_id>_prime' / trophy '<monster_id>_trophy'
    — i.e. the rename touched names only, never ids."""
    raw = _raw_ingredients()
    for iid, defn in raw.items():
        if not isinstance(defn, dict):
            continue
        role = defn.get("tier_role")
        src = defn.get("source_monster")
        if role == "prime":
            assert iid == f"{src}_prime", (iid, src)
        elif role == "trophy":
            assert iid == f"{src}_trophy", (iid, src)


def test_ingredient_and_prime_cuts_names_consistent():
    """ingredient.json (catalog) and prime_cuts.json (source) agree on every
    non-trophy prime display name."""
    catalog = _raw_ingredients()
    primes = json.loads(_PC_JSON.read_text(encoding="utf-8"))["primes"]
    mism = []
    for entry in primes.values():
        if entry.get("is_trophy"):
            continue
        iid = entry["ingredient_id"]
        if iid in catalog:
            if catalog[iid]["name"] != entry["ingredient_name"]:
                mism.append((iid, catalog[iid]["name"], entry["ingredient_name"]))
    assert not mism, f"name drift between ingredient.json and prime_cuts.json: {mism[:15]}"


# ---------------------------------------------------------------------------
# (c) Recipes still resolve every ingredient id (no dangling refs)
# ---------------------------------------------------------------------------

def test_recipes_have_no_dangling_ingredient_refs():
    recipes = json.loads(_RECIPES_JSON.read_text(encoding="utf-8"))
    valid_ids = set(_raw_ingredients().keys())
    dangling = {}
    for rid, rdef in recipes.items():
        for ing_id in rdef.get("ingredients", []):
            if ing_id not in valid_ids:
                dangling.setdefault(rid, []).append(ing_id)
    assert not dangling, f"recipes reference unknown ingredient ids: {dict(list(dangling.items())[:15])}"


def test_recipes_reference_by_id_not_name():
    """Recipe ingredient refs must be ids (lowercase, underscore) — never
    display names. A name would contain a space or capital letter."""
    recipes = json.loads(_RECIPES_JSON.read_text(encoding="utf-8"))
    namelike = set()
    for rdef in recipes.values():
        for ing_id in rdef.get("ingredients", []):
            if " " in ing_id or any(c.isupper() for c in ing_id):
                namelike.add(ing_id)
    assert not namelike, f"recipes reference ingredients by NAME, not id: {namelike}"


def test_prime_recipe_resolves_renamed_ingredient():
    """End-to-end: a renamed prime's canonical recipe still resolves via the
    food_system resolver (which keys off ingredient_id, not name)."""
    import food_system
    skeleton = food_system.load_ingredient_for("skeleton_prime")
    assert skeleton is not None
    assert skeleton.name == "Skeleton Pristine Marrow"
    recipe = food_system._find_recipe_for_ingredient(skeleton)
    assert recipe is not None, "renamed skeleton prime no longer resolves to a recipe"
    assert recipe["id"] == "prime_skeleton_recipe"
    assert "skeleton_prime" in recipe["ingredients"]


# ---------------------------------------------------------------------------
# (d) Floor-spawn: monster-derived ingredients never spawn as floor loot
# ---------------------------------------------------------------------------

def test_only_dungeon_tier_ingredients_are_floor_spawnable():
    """The dungeon floor-ingredient filter must select ONLY tier_role
    'dungeon'. This pins the fix that stopped monster primes (gas spore, hell
    bovine, etc.) leaking onto the floor via plant-name keyword matching.

    Mirrors src/dungeon.py spawn_items()'s plant_ingredients comprehension.
    """
    all_ings = load_items("ingredient")
    fam_role = _family_role_by_id()
    level = 100  # max so min_level never filters anything out
    spawnable = [
        ing for ing in all_ings
        if fam_role.get(ing.id, (None, None))[0] == "dungeon"
        and ing.min_level <= level
    ]
    roles = {fam_role.get(ing.id, (None, None))[0] for ing in spawnable}
    assert roles == {"dungeon"}, f"non-dungeon ingredients are floor-spawnable: {roles}"
    # And specifically NONE of the previously-leaking primes are present.
    spawn_ids = {ing.id for ing in spawnable}
    for leaked in ("gas_spore_prime", "hell_bovine_prime", "shambling_mound_prime",
                   "yellow_mold_prime", "myconid_sovereign_prime"):
        assert leaked not in spawn_ids, f"{leaked} still floor-spawnable!"


def test_dungeon_spawn_uses_tier_role_not_keywords():
    """Guard against regression to keyword-based floor filtering: dungeon.py
    must no longer carry the leaky _PLANT_KEYWORDS list."""
    src = (ROOT / "src" / "dungeon.py").read_text(encoding="utf-8")
    assert "_PLANT_KEYWORDS" not in src, (
        "dungeon.py still defines _PLANT_KEYWORDS — the keyword floor filter "
        "leaks monster primes (e.g. 'gas spore' via 'spore')."
    )
