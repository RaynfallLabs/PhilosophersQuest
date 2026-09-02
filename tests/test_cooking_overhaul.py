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


def test_assorted_ingredient_is_renamed_jerky():
    e = INGREDIENTS[ASSORTED]
    assert e["name"] == "Assorted Monster Jerky", e["name"]


def test_assorted_jerky_is_edible_safe_with_raw_sp_25():
    e = INGREDIENTS[ASSORTED]
    assert e.get("edible_safe") is True
    assert e.get("raw_sp") == 25


def test_eat_jerky_restores_25_sp_and_never_poisons():
    """Loop the RNG hard: jerky must give +25 SP and NEVER apply food poison.

    Raw jerky SP raised 12 -> 25 (2026-06-07 SP-economy tune): jerky 25, low
    cook 50, good cook 100 -- a clear raw < low-cook < good-cook ladder."""
    import food_system
    from food_system import load_ingredient_for

    for _ in range(400):
        pl = _MockPlayer()
        jerky = load_ingredient_for(ASSORTED)
        assert jerky is not None
        msgs = food_system.eat_raw(pl, jerky)
        assert pl.sp == 25, f"expected +25 SP, got {pl.sp}"
        assert pl.hp == 50, "jerky grants no HP (HP stays behind cooking)"
        assert "poisoned" not in pl.effects, "jerky must never poison"
        assert not any("poison" in m.lower() for m in msgs)


def test_jerky_loaded_ingredient_carries_flags():
    from food_system import load_ingredient_for
    jerky = load_ingredient_for(ASSORTED)
    assert jerky.edible_safe is True
    assert jerky.raw_sp == 25


def test_non_cured_ingredient_still_risks_poison():
    """A prime (no edible_safe) keeps the 30% raw-poison roll: the exemption is
    jerky-specific, not a blanket removal."""
    import food_system
    from food_system import load_ingredient_for
    poisoned_once = False
    for _ in range(300):
        pl = _MockPlayer()
        prime = load_ingredient_for("giant_rat_prime")
        assert not getattr(prime, "edible_safe", False)
        food_system.eat_raw(pl, prime)
        if "poisoned" in pl.effects:
            poisoned_once = True
            break
    assert poisoned_once, "raw non-cured ingredients must still be able to poison"


# ---------------------------------------------------------------------------
# (B) basic stew removed
# ---------------------------------------------------------------------------

def test_basic_stew_deleted():
    assert "basic_monster_stew" not in RECIPES
    assert not _recipes_of("basic")


def test_assorted_parts_have_no_solo_recipe():
    """With basic stew gone, eating jerky is the ONLY use for a lone assorted
    part -- _find_recipe_for_ingredient must return None for it."""
    import food_system
    from food_system import load_ingredient_for
    jerky = load_ingredient_for(ASSORTED)
    assert food_system._find_recipe_for_ingredient(jerky) is None


# ---------------------------------------------------------------------------
# (C) Richer recipe costs per class
# ---------------------------------------------------------------------------

# v2.6.4 (2026-09-02) recipe economy replaces the class-uniform costs above.
# recipe_class is retired; recipes are keyed by id prefix (u_ / family_ /
# trophy_ / prime_ / combo_) and every recipe references an outcome archetype
# in data/items/cook_outcomes.json.

def _recipes_by_prefix(prefix: str) -> dict:
    return {rid: r for rid, r in RECIPES.items() if rid.startswith(prefix)}


def test_v264_family_recipes_are_2_family_and_4_assorted():
    fams = {rid: r for rid, r in RECIPES.items()
            if rid.startswith("family_") and rid.endswith("_recipe")}
    assert len(fams) == 12, f"expected 12 family recipes, got {len(fams)}"
    for rid in fams:
        r = _roles(rid)
        assert r == Counter({"family": 2, "assorted": 4}), (rid, dict(r))


def test_v264_solo_prime_recipes_are_lightweight():
    """v2.6.4: solo prime cooks cost just the prime + 2 assorted. Simpler
    than the pre-v2.6.4 economy (which forced primes to also spend family
    cuts). Combo prime recipes (with dungeon adjuncts) sit at 3 ingredients
    too. See PLAYABILITY_PASS_AUDIT.md for the redesign rationale."""
    primes = _recipes_by_prefix("prime_")
    assert len(primes) >= 500, f"expected 500+ prime recipes, got {len(primes)}"
    for rid in primes:
        r = _roles(rid)
        assert r["prime"] == 1, (rid, dict(r))
        assert r["assorted"] == 2, (rid, dict(r))


def test_v264_trophy_recipes_use_boss_trophy():
    troph = _recipes_by_prefix("trophy_")
    assert len(troph) == 14, f"expected 14 trophy recipes, got {len(troph)}"
    for rid in troph:
        r = _roles(rid)
        assert r["trophy"] == 1, (rid, dict(r))
        assert r["family"] == 2, (rid, dict(r))
        assert r["assorted"] == 5, (rid, dict(r))


def test_v264_combo_recipes_pair_prime_with_dungeon_ingredient():
    """Signature-monster combos take 1 prime + 1 dungeon-role adjunct +
    1 assorted. The pairing drives which outcome archetype fires
    (mushroom -> perception, salt -> poison_resist, etc.)."""
    combos = _recipes_by_prefix("combo_")
    assert len(combos) >= 30, f"expected 30+ combo recipes, got {len(combos)}"
    for rid in combos:
        r = _roles(rid)
        assert r["prime"] == 1, (rid, dict(r))
        assert r["dungeon"] == 1, (rid, dict(r))
        assert r["assorted"] == 1, (rid, dict(r))


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
    """Safety net: if _cook_item is somehow called on jerky, it must NOT destroy
    the part (no solo recipe) -- the pre-overhaul flow removed it up-front."""
    from food_system import load_ingredient_for
    g = _headless_game()
    g.player.inventory = [load_ingredient_for(ASSORTED) for _ in range(3)]
    jerky = g.player.inventory[0]
    started = {"quiz": False}
    g.quiz_engine.start_quiz = lambda **kw: started.__setitem__("quiz", True)
    g._cook_item(jerky)
    held = sum(1 for i in g.player.inventory if i.id == ASSORTED)
    assert held == 3, f"jerky was consumed by a solo cook ({held} left)"
    assert started["quiz"] is False, "no cooking quiz should start for un-cookable jerky"


def test_prime_recipe_family_matches_its_monster_family():
    """A prime recipe's 2 family parts must be THIS monster's family -- the
    auto-cluster guarantee (the family co-spawns with the prime by definition)."""
    mism = []
    for rid, r in _recipes_of("prime").items():
        prime = next(i for i in r["ingredients"] if _classify(i) == "prime")
        mon = prime[: -len("_prime")]
        want = f"family_{PRIMES[mon]['family']}"
        fams = [i for i in r["ingredients"] if _classify(i) == "family"]
        if any(f != want for f in fams):
            mism.append((rid, fams, want))
    assert not mism, f"prime recipes whose family part mismatches the monster: {mism[:10]}"
