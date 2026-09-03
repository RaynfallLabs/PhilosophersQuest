"""Cooking-overhaul data + behavior tests (2026-06-07).

Pins the approved overhaul (proposals/design/cooking_recipes_overhaul.md + the
user's refinements):

  * JERKY survival floor -- assorted_monster_parts is "Assorted Monster Jerky":
    eaten raw it restores +12 SP with NO food-poison roll, +0 HP.
  * basic_monster_stew DELETED -- assorted parts alone have no recipe.
  * Richer, CLUSTERED recipe costs per class (more parts, more variety):
        family   : 2 family + 4 assorted
        prime    : 1 prime  + 2 family + 4 assorted
        master   : 2 primes + 2 family + 3 assorted (primes CO-SPAWN)
        trophy   : 1 trophy + 2 family + 5 assorted
        dungeon  : 1 special + 1 prime + 2 family + 3 assorted
  * FLOOR CLUSTERING -- every recipe's monster-derived parts (primes/trophies)
    share a common spawn-floor band, so nothing forces cross-dungeon backtracking.

These are data-layer + pure-function tests: per the project's "play-test isn't
realistic" clause, the late-game / randomized recipe costs are validated here
rather than by play (jerky + the cheap family cook get the in-person play-test).
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

DATA = ROOT / "data" / "items"
RECIPES = json.loads((DATA / "recipes.json").read_text(encoding="utf-8"))
INGREDIENTS = json.loads((DATA / "ingredient.json").read_text(encoding="utf-8"))
PRIMES = json.loads((DATA / "prime_cuts.json").read_text(encoding="utf-8"))["primes"]
MONSTERS = json.loads((ROOT / "data" / "monsters.json").read_text(encoding="utf-8"))

ASSORTED = "assorted_monster_parts"


_DUNGEON_ING_IDS = frozenset({
    "cave_mushroom", "altar_incense", "swamp_moss", "river_salt",
    "holy_water", "crystal_shard", "deep_iron", "abyssal_kelp",
})


def _classify(ing: str) -> str:
    if ing == ASSORTED:
        return "assorted"
    if ing.startswith("family_"):
        return "family"
    if ing.endswith("_trophy"):
        return "trophy"
    if ing.endswith("_prime"):
        return "prime"
    if ing in _DUNGEON_ING_IDS:
        return "dungeon"
    return "special"


def _roles(rid: str) -> Counter:
    return Counter(_classify(i) for i in RECIPES[rid]["ingredients"])


def _recipes_of(cls: str):
    return {rid: r for rid, r in RECIPES.items() if r.get("recipe_class") == cls}


# ---------------------------------------------------------------------------
# (A) Jerky -- the survival floor
# ---------------------------------------------------------------------------

class _MockPlayer:
    """Minimal player for eat_raw: tracks SP + effects (+ HP, to prove jerky
    grants none)."""
    def __init__(self):
        self.sp = 0
        self.hp = 50
        self.effects = {}
    def restore_sp(self, amt):
        self.sp += amt
    def restore_hp(self, amt):
        self.hp += amt
    def add_effect(self, name, dur):
        self.effects[name] = dur
        return True
    def has_effect(self, name):
        return name in self.effects


# v2.6.5 (2026-09-03) rewrote the emergency-food safety net:
# assorted_monster_parts and family_* cuts are DELETED. Every monster prime
# is now edible_safe with tier-scaled raw_sp (T1=10, T5=30) so raw eating
# survives as a "you're desperate" fallback. Cooking is 3-5x more efficient
# but not required for survival.


def test_assorted_monster_parts_is_removed():
    """The v2.6.5 harvest rebuild ripped out the generic 'assorted' fallback."""
    assert ASSORTED not in INGREDIENTS


def test_family_cuts_are_removed():
    family_ids = [k for k in INGREDIENTS if k.startswith("family_")]
    assert family_ids == [], f"expected no family_* cuts, got {family_ids}"


def test_every_monster_prime_is_edible_raw():
    """v2.6.5: every prime is edible_safe with tier-scaled raw_sp. Ensures
    the player can never fully lose access to emergency food."""
    for ing_id, ing in INGREDIENTS.items():
        if ing.get("tier_role") != "prime":
            continue
        assert ing.get("edible_safe") is True, f"{ing_id} not edible_safe"
        raw_sp = int(ing.get("raw_sp", 0) or 0)
        assert 5 <= raw_sp <= 40, f"{ing_id} raw_sp={raw_sp} out of range"


def test_eat_raw_prime_never_poisons_v265(monkeypatch):
    """The emergency-food promise: raw-eating a prime never applies poisoned.
    (Loop the RNG hard.)"""
    import food_system
    from food_system import load_ingredient_for
    for _ in range(300):
        pl = _MockPlayer()
        prime = load_ingredient_for("giant_rat_prime")
        assert prime is not None
        food_system.eat_raw(pl, prime)
        assert "poisoned" not in pl.effects, "raw primes must never poison in v2.6.5"


# ---------------------------------------------------------------------------
# (B) basic stew removed
# ---------------------------------------------------------------------------

def test_basic_stew_deleted():
    assert "basic_monster_stew" not in RECIPES
    assert not _recipes_of("basic")


def test_assorted_parts_are_gone_v265():
    """v2.6.5: no lookup should return anything for the deleted assorted key."""
    from food_system import load_ingredient_for
    assert load_ingredient_for(ASSORTED) is None


# ---------------------------------------------------------------------------
# (C) Richer recipe costs per class
# ---------------------------------------------------------------------------

# v2.6.4 (2026-09-02) recipe economy replaces the class-uniform costs above.
# recipe_class is retired; recipes are keyed by id prefix (u_ / family_ /
# trophy_ / prime_ / combo_) and every recipe references an outcome archetype
# in data/items/cook_outcomes.json.

def _recipes_by_prefix(prefix: str) -> dict:
    return {rid: r for rid, r in RECIPES.items() if rid.startswith(prefix)}


def test_v265_family_recipes_are_3_same_family_monsters():
    """v2.6.5: family recipes use 3 same-family monster primes (no more
    abstract family_* or assorted ingredients)."""
    fams = {rid: r for rid, r in RECIPES.items()
            if rid.startswith("family_") and rid.endswith("_recipe")}
    assert len(fams) == 12, f"expected 12 family recipes, got {len(fams)}"
    for rid, r in fams.items():
        ings = r["ingredients"]
        assert len(ings) == 3, f"{rid} should have 3 ingredients, got {len(ings)}"
        # All 3 should be primes from the same family
        families = set()
        for ing_id in ings:
            defn = INGREDIENTS.get(ing_id, {})
            assert defn.get("tier_role") == "prime", f"{rid}: {ing_id} not a prime"
            families.add(defn.get("family"))
        assert len(families) == 1, f"{rid}: mixed families {families}"


def test_v265_solo_prime_recipes_are_single_ingredient():
    """v2.6.5: solo prime cooks are 1 ingredient (the prime alone)."""
    primes = _recipes_by_prefix("prime_")
    assert len(primes) >= 500, f"expected 500+ prime recipes, got {len(primes)}"
    for rid, r in primes.items():
        ings = r["ingredients"]
        assert len(ings) == 1, f"{rid} should have 1 ingredient, got {ings}"
        defn = INGREDIENTS.get(ings[0], {})
        assert defn.get("tier_role") == "prime", f"{rid}: {ings[0]} not a prime"


def test_v265_trophy_recipes_are_trophy_alone():
    """v2.6.5: trophies stand alone — precious, no gating behind extra grinding."""
    troph = _recipes_by_prefix("trophy_")
    assert len(troph) == 14, f"expected 14 trophy recipes, got {len(troph)}"
    for rid, r in troph.items():
        ings = r["ingredients"]
        assert len(ings) == 1, f"{rid} should have 1 ingredient, got {ings}"
        assert ings[0].endswith("_trophy"), f"{rid}: {ings[0]} not a trophy"


def test_v265_combo_recipes_pair_prime_with_dungeon():
    combos = _recipes_by_prefix("combo_")
    assert len(combos) >= 30, f"expected 30+ combo recipes, got {len(combos)}"
    for rid, r in combos.items():
        role_counter = _roles(rid)
        assert role_counter["prime"] == 1, (rid, dict(role_counter))
        assert role_counter["dungeon"] == 1, (rid, dict(role_counter))
        assert role_counter.get("assorted", 0) == 0, f"{rid} should have no assorted"


def test_every_recipe_references_existing_ingredients():
    valid = set(INGREDIENTS.keys())
    broken = {}
    for rid, r in RECIPES.items():
        for ing in r.get("ingredients", []):
            if ing not in valid:
                broken.setdefault(rid, []).append(ing)
    assert not broken, f"recipes reference missing ingredients: {dict(list(broken.items())[:10])}"


# ---------------------------------------------------------------------------
# (D) Floor clustering -- monster parts in a recipe share a spawn band
# ---------------------------------------------------------------------------

def _present_floors(mid: str, thresh: float = 0.05) -> set[int]:
    """Floors (1..100) where the monster has a non-negligible Gaussian spawn
    weight, mirroring dungeon._build_spawn_pool (peak_floor/spread bell gated by
    min_level)."""
    d = MONSTERS.get(mid, {})
    pf = d.get("peak_floor", d.get("min_level", 1))
    sp = max(1, d.get("spread", 10))
    ml = d.get("min_level", 1)
    out = set()
    for L in range(1, 101):
        if ml > L:
            continue
        if math.exp(-((L - pf) ** 2) / (2 * sp * sp)) >= thresh:
            out.add(L)
    return out


def _monsters_in(rid: str) -> list[str]:
    out = []
    for ing in RECIPES[rid]["ingredients"]:
        cl = _classify(ing)
        if cl == "prime":
            out.append(ing[: -len("_prime")])
        elif cl == "trophy":
            out.append(ing[: -len("_trophy")])
    return out


def test_every_recipe_monster_parts_share_a_floor_band():
    """No recipe may require primes/trophies from monsters that never co-spawn
    (would force cross-dungeon backtracking). Family/assorted/special are
    floor-agnostic and excluded from the check."""
    fails = []
    for rid in RECIPES:
        mons = _monsters_in(rid)
        if len(mons) < 2:
            continue
        bands = [_present_floors(m) for m in mons]
        if not set.intersection(*bands):
            ranges = {m: (min(b) if b else None, max(b) if b else None)
                      for m, b in zip(mons, bands)}
            fails.append((rid, ranges))
    assert not fails, f"recipes whose monster parts never co-spawn: {fails[:10]}"


# ---------------------------------------------------------------------------
# (E) Cook menu handles the no-solo-recipe jerky gracefully (play-reachable)
# ---------------------------------------------------------------------------

def _headless_game(name="cooktest"):
    import pygame as _pg
    _pg.init()  # font/display subsystems needed by Game construction
    from main import Game
    return Game(_pg.display.set_mode((1, 1)), player_name=name)


def test_cook_menu_excludes_jerky_from_single_tab():
    """Holding ONLY jerky: the Single tab is empty (jerky has no solo recipe)
    and opening the cook menu does NOT crash -- it reports nothing to cook."""
    from food_system import load_ingredient_for
    g = _headless_game()
    g.player.inventory = [load_ingredient_for(ASSORTED) for _ in range(6)]
    g._open_cook_menu()
    # jerky filtered out of the single tab
    assert g.cook_menu_items == []
    # 6 jerky can't satisfy any >=2-distinct-type compound recipe either
    assert g.cook_compound_recipes == []


def test_cook_item_on_jerky_does_not_consume_it():
    """v2.6.5: jerky/assorted_monster_parts is gone; this test is a
    load-through-no-op check that _cook_item handles the missing key without
    crashing (the caller filters upstream anyway)."""
    from food_system import load_ingredient_for
    assert load_ingredient_for(ASSORTED) is None
    # No crash on the lookup itself is the assertion.


def test_v265_family_recipes_have_family_matching_ingredients():
    """v2.6.5 family recipe uses 3 same-family monster primes. Verifies the
    generator picked monsters that actually match the family in the recipe id."""
    for fam_id, (name, _flavor) in [
        ("beast", (None, None)), ("humanoid", (None, None)),
        ("reptile", (None, None)), ("dragon", (None, None)),
        ("undead", (None, None)),
    ]:
        rid = f"family_{fam_id}_recipe"
        if rid not in RECIPES:
            continue
        for ing_id in RECIPES[rid]["ingredients"]:
            defn = INGREDIENTS.get(ing_id, {})
            assert defn.get("family") == fam_id, \
                f"{rid} ingredient {ing_id} has family={defn.get('family')}, expected {fam_id}"
