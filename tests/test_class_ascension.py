"""Boss Class Ascension in-game integration (Phase 1) — logic + data tests.

The interactive Ascension screen is Pygame and play-tested by the user. These
tests lock the MECHANICS that feed it:

  * the four boss trophy recipes (floors 20/40/60/80) carry `class_ascension`;
    Abaddon (floor 100) does NOT;
  * food_system emits the `_class_ascension` SIGNAL on a successful boss-trophy
    cook and SUPPRESSES the old permanent_power (the meal IS the class choice);
    a ruined (T0) cook emits nothing;
  * the offered_choices -> apply_class_node flow advances class_path;
  * a once-per-floor ability grants a charge that the floor reset clears;
  * the passive perks that were wired into the engine (healing_received_pct,
    mp_cost_reduction, trap_sight, class save bonus) carry the expected values.
"""
import json
from pathlib import Path

import class_system as cs
import food_system as fs
from player import Player


BOSS_TROPHY_RECIPES = {
    20: 'trophy_asterion_minotaur_recipe',
    40: 'trophy_medusa_gorgon_recipe',
    60: 'trophy_fafnir_dragon_recipe',
    80: 'trophy_fenrir_wolf_recipe',
}


def _recipes():
    return json.loads(Path('data/items/recipes.json').read_text(encoding='utf-8'))


def _p(**stats):
    p = Player()
    for k, v in stats.items():
        setattr(p, k, v)
    p.known_spells = {}
    p.inventory = []
    return p


# --------------------------------------------------------------------------
# DATA: the four boss trophy recipes carry class_ascension; Abaddon does not.
# --------------------------------------------------------------------------

def test_four_boss_trophy_recipes_flag_class_ascension():
    """v2.6.4: class_ascension now lives on the OUTCOME archetype, not the
    recipe. The 4 boss trophies at floors 20/40/60/80 reference an outcome
    with class_ascension=true; Abaddon (floor 100) does not."""
    rec = _recipes()
    outcomes = fs._load_outcomes()
    for floor, rid in BOSS_TROPHY_RECIPES.items():
        assert rid in rec, f"floor {floor}: {rid} missing"
        oid = rec[rid].get('outcome_id')
        assert oid, f"{rid} has no outcome_id"
        assert outcomes.get(oid, {}).get('class_ascension') is True, \
            f"{rid} -> {oid} not flagged class_ascension"


def test_abaddon_trophy_is_not_a_class_ascension():
    rec = _recipes()
    outcomes = fs._load_outcomes()
    oid = rec['trophy_abaddon_destroyer_recipe'].get('outcome_id')
    assert outcomes.get(oid, {}).get('class_ascension') is not True


def test_asterion_is_a_trophy_with_ingredient_and_family_recipe_shape():
    """Floor-20 boss was a prime pre-integration; it is now a proper trophy so
    all four bosses use the uniform trophy_{boss}_recipe flow."""
    pc = json.loads(Path('data/items/prime_cuts.json').read_text(encoding='utf-8'))['primes']
    ast = pc['asterion_minotaur']
    assert ast['is_trophy'] is True
    assert ast['ingredient_id'] == 'asterion_minotaur_trophy'

    ing = json.loads(Path('data/items/ingredient.json').read_text(encoding='utf-8'))
    assert 'asterion_minotaur_trophy' in ing
    assert ing['asterion_minotaur_trophy']['tier_role'] == 'trophy'

    # v2.6.5: trophy recipe is 1 trophy alone (trophies are precious).
    ings = _recipes()['trophy_asterion_minotaur_recipe']['ingredients']
    assert ings == ['asterion_minotaur_trophy']


# --------------------------------------------------------------------------
# SIGNAL: food_system emits _class_ascension and suppresses permanent_power.
# --------------------------------------------------------------------------

def test_cook_emits_class_ascension_signal_on_success():
    rec = _recipes()
    for rid in BOSS_TROPHY_RECIPES.values():
        recipe = {'id': rid, **rec[rid]}
        msgs = fs._apply_recipe_outcome(_p(STR=10), recipe)
        assert '_class_ascension' in msgs, f"{rid} did not signal"


def test_ruined_cook_does_not_signal_ascension():
    rec = _recipes()
    recipe = {'id': 'trophy_fenrir_wolf_recipe', **rec['trophy_fenrir_wolf_recipe']}
    msgs = fs._apply_recipe_outcome(_p(STR=10), recipe, ruined=True)
    assert '_class_ascension' not in msgs


def test_class_ascension_cook_suppresses_permanent_power():
    """v2.6.4: Fenrir's trophy outcome carries permanent_power=plus_3_str AND
    class_ascension=true. When class_ascension fires, the perm_power is
    SKIPPED (the meal IS the class choice; the class node applies the +3)."""
    rec = _recipes()
    recipe = {'id': 'trophy_fenrir_wolf_recipe', **rec['trophy_fenrir_wolf_recipe']}
    outcome = fs._load_outcomes().get(recipe['outcome_id'], {})
    assert outcome.get('permanent_power') == 'plus_3_str'
    assert outcome.get('class_ascension') is True
    p = _p(STR=10)
    base = p.STR
    fs._apply_recipe_outcome(p, recipe)
    # stat_grant=1 (default STR) fires before the ascension return; but the
    # +3 perm_power must be skipped. STR rises by at most +1.
    assert p.STR <= base + 1
    assert p.STR < base + 3


def test_non_ascension_trophy_still_applies_permanent_power():
    """Abaddon's trophy (no ascension flag) keeps its all-stats-+1 apotheosis."""
    rec = _recipes()
    recipe = {'id': 'trophy_abaddon_destroyer_recipe', **rec['trophy_abaddon_destroyer_recipe']}
    p = _p(STR=10, CON=10, DEX=10, INT=10, WIS=10, PER=10)
    base = p.PER
    msgs = fs._apply_recipe_outcome(p, recipe)
    assert '_class_ascension' not in msgs
    assert p.PER > base   # apotheosis raised a stat that the themed grant didn't


# --------------------------------------------------------------------------
# FLOW: offered_choices -> apply_class_node advances class_path.
# --------------------------------------------------------------------------

def test_offered_then_apply_advances_class_path():
    p = _p(STR=10)
    offered = cs.offered_choices(p)
    assert 'fighter' in offered            # always available at tier 1
    assert cs.class_path(p) == []
    cs.apply_class_node(p, 'fighter')
    assert cs.class_path(p) == ['fighter']
    # tier advanced -> tier-2 nodes not authored in Phase 1 -> nothing offered
    assert cs.offered_choices(p) == []


def test_apply_grants_ability_recorded_for_power_menu():
    p = _p(STR=10)
    cs.apply_class_node(p, 'fighter')
    assert cs.has_ability(p, 'second_wind')


# --------------------------------------------------------------------------
# ABILITIES: a once-per-floor charge is grantable, spendable, and floor-reset.
# --------------------------------------------------------------------------

def test_ability_charge_grants_and_resets_per_floor():
    p = _p(STR=10)
    cs.apply_class_node(p, 'fighter')                 # grants second_wind
    assert cs.ability_charge_available(p, 'second_wind')
    assert cs.consume_ability_charge(p, 'second_wind') is True
    assert cs.ability_charge_available(p, 'second_wind') is False
    # second consume same floor fails
    assert cs.consume_ability_charge(p, 'second_wind') is False
    # floor reset re-arms it
    cs.reset_ability_charges(p)
    assert cs.ability_charge_available(p, 'second_wind') is True


def test_ability_charge_unavailable_without_the_ability():
    p = _p(STR=10)   # no class chosen
    assert cs.ability_charge_available(p, 'second_wind') is False
    assert cs.consume_ability_charge(p, 'second_wind') is False


# --------------------------------------------------------------------------
# PERKS: the values the engine hooks read.
# --------------------------------------------------------------------------

def test_cleric_healing_received_scales_restore_hp():
    p = _p(WIS=14)
    p.max_hp = 200
    p.hp = 50
    cs.apply_class_node(p, 'cleric')                  # +15% healing received
    gained = p.restore_hp(20)                         # 20 * 1.15 = 23.0 exactly
    assert gained == 23


def test_no_class_healing_bonus_is_identity():
    p = _p(WIS=14)
    p.max_hp = 100
    p.hp = 50
    assert p.restore_hp(10) == 10                     # no class -> exact heal


def test_mage_mp_cost_reduction_and_class_save_mapping():
    m = _p(INT=14)
    cs.apply_class_node(m, 'mage')
    assert cs.proficiency(m, 'mp_cost_reduction') == 1
    # class save category 'mind' maps onto the WIS save stat
    assert cs.save_bonus_for_stat(m, 'WIS') == 1
    assert cs.save_bonus_for_stat(m, 'CON') == 0


def test_fighter_body_save_maps_to_con_and_rogue_trap_sight():
    f = _p(STR=10)
    cs.apply_class_node(f, 'fighter')                 # body save
    assert cs.save_bonus_for_stat(f, 'CON') == 1
    assert cs.save_bonus_for_stat(f, 'WIS') == 0
    r = _p(DEX=14)
    cs.apply_class_node(r, 'rogue')
    assert cs.proficiency(r, 'trap_sight') == 1


def test_class_save_feeds_player_save_bonus_for():
    """End-to-end: a Cleric's spirit save shows up in Player.save_bonus_for(WIS),
    which status_effects.apply_debuff_with_save reads."""
    c = _p(WIS=14)
    base = c.save_bonus_for('WIS')
    cs.apply_class_node(c, 'cleric')                  # spirit save +1
    assert c.save_bonus_for('WIS') == base + 1
