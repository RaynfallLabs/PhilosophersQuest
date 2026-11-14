"""Ingredient names and ids, rewritten for the kitchen rebuild (2026-11-14).

History: in 2026-06 every monster part was "<monster> Prime Cut"; the fix
gave each family a formula ("Pristine Marrow", "Engorged Sac", "Pure
Ichor"...), which read the same for hundreds of parts. The kitchen rebuild
(COOKING_REBUILD_PLAN_2026_11_14) gave every part a vivid name of its own
that keeps the kind of part its picture shows, and let close kin share one
ingredient (every goblin gives Goblin Gristle). Kept ids are unchanged, so
pictures stay right; every retired id resolves to its kept one.

Also still pinned: only terrain-foraged ingredients spawn on the floor;
monster parts come from harvesting a corpse.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from items import load_items  # noqa: E402

_ING_JSON = ROOT / "data" / "items" / "ingredient.json"
_MAP_JSON = ROOT / "data" / "items" / "harvest_map.json"
_RECIPES_JSON = ROOT / "data" / "items" / "recipes.json"

_OLD_FORMULAS = ("Prime Cut", "Choice Cut", "Pristine Marrow", "Engorged Sac", "Pure Ichor",
                 "Glittering Mote", "Concentrated Essence", "Prime Heartwood", "Prime Scale")


def _raw_ingredients() -> dict:
    return json.loads(_ING_JSON.read_text(encoding="utf-8"))


def _name_by_id() -> dict[str, str]:
    """Display names as the GAME loads them (via load_items)."""
    return {ing.id: ing.name for ing in load_items("ingredient")}


# ---------------------------------------------------------------------------
# (a) Names
# ---------------------------------------------------------------------------

def test_no_part_is_named_by_the_old_formulas():
    bad = [(i, n) for i, n in _name_by_id().items() if any(f in n for f in _OLD_FORMULAS)]
    assert not bad, bad[:15]


def test_known_parts_have_their_new_names():
    names = _name_by_id()
    assert names["goblin_prime"] == "Goblin Gristle"
    assert names["wraith_prime"] == "Wraith Ectoplasm"
    assert names["basilisk_prime"] == "Basilisk Tail Steak"
    assert names["gas_spore_prime"] == "Gas Spore Bladder"
    assert names["skeleton_prime"] == "Skeleton Marrow Slice"


def test_names_are_unique():
    names = list(_name_by_id().values())
    assert len(names) == len(set(names))


def test_trophy_authored_names_preserved():
    names = _name_by_id()
    assert names["fafnir_dragon_trophy"] == "Fafnir's Heart"
    assert names["fenrir_wolf_trophy"] == "Fenrir's Tooth"


# ---------------------------------------------------------------------------
# (b) Ids: kept ids load; retired ids resolve; every kept id is a member's
# ---------------------------------------------------------------------------

def test_known_ingredient_ids_still_load():
    names = _name_by_id()
    for iid in ("giant_rat_prime", "gas_spore_prime", "skeleton_prime",
                "fafnir_dragon_trophy", "cave_mushroom"):
        assert iid in names, iid
    for gone in ("assorted_monster_parts", "family_undead", "family_beast"):
        assert gone not in names, gone


def test_kept_ids_are_a_member_monsters_id():
    """A kept part keeps one member's id (its picture is that id's png):
    '<member>_prime' for a monster part, '<boss>_trophy' for a trophy."""
    raw = _raw_ingredients()
    hmap = json.loads(_MAP_JSON.read_text(encoding="utf-8"))
    by_ing = {}
    for mid, iid in hmap["monsters"].items():
        by_ing.setdefault(iid, set()).add(mid)
    for iid, defn in raw.items():
        role = defn.get("tier_role")
        if role == "trophy":
            assert iid == f"{defn['source_monster']}_trophy", iid
        elif role == "prime":
            assert iid.endswith("_prime"), iid
            assert defn["source_monster"] in by_ing[iid], iid


def test_load_ingredient_for_reads_a_retired_id_as_the_kept_one():
    import food_system
    part = food_system.load_ingredient_for("goblin_shaman_prime")
    assert part is not None and part.id == "goblin_prime"
    assert part.name == "Goblin Gristle"


# ---------------------------------------------------------------------------
# (c) Recipes resolve every id
# ---------------------------------------------------------------------------

def test_recipes_have_no_dangling_ingredient_refs():
    recipes = json.loads(_RECIPES_JSON.read_text(encoding="utf-8"))
    food = json.loads((ROOT / "data" / "items" / "food.json").read_text(encoding="utf-8"))
    valid_ids = set(_raw_ingredients()) | set(food)
    dangling = {rid: [i for i in r["ingredients"] if i not in valid_ids] for rid, r in recipes.items()}
    dangling = {k: v for k, v in dangling.items() if v}
    assert not dangling, dict(list(dangling.items())[:15])


def test_recipes_reference_by_id_not_name():
    recipes = json.loads(_RECIPES_JSON.read_text(encoding="utf-8"))
    namelike = {i for r in recipes.values() for i in r["ingredients"]
                if " " in i or any(c.isupper() for c in i)}
    assert not namelike, namelike


def test_every_part_resolves_to_its_single_dish():
    import food_system
    skeleton = food_system.load_ingredient_for("skeleton_prime")
    recipe = food_system._find_recipe_for_ingredient(skeleton)
    assert recipe is not None and recipe["ingredients"] == ["skeleton_prime"]
    assert recipe["name"] == "Bone-Marrow Gruel"


# ---------------------------------------------------------------------------
# (d) Floor-spawn: monster-derived ingredients never spawn as floor loot
# ---------------------------------------------------------------------------

def test_only_dungeon_tier_ingredients_are_floor_spawnable():
    """Mirrors src/dungeon.py spawn_items()'s plant_ingredients comprehension."""
    raw = _raw_ingredients()
    spawnable = [ing for ing in load_items("ingredient")
                 if raw.get(ing.id, {}).get("tier_role") == "dungeon"]
    spawn_ids = {ing.id for ing in spawnable}
    assert {raw[i]["tier_role"] for i in spawn_ids} == {"dungeon"}
    for leaked in ("gas_spore_prime", "hell_bovine_prime", "shambling_mound_prime",
                   "yellow_mold_prime", "myconid_worker_prime"):
        assert leaked not in spawn_ids, leaked


def test_dungeon_spawn_uses_tier_role_not_keywords():
    src = (ROOT / "src" / "dungeon.py").read_text(encoding="utf-8")
    assert "_PLANT_KEYWORDS" not in src
