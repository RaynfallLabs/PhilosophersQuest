"""Wiring tests for artifact-specific mechanical fields.

These verify that the per-artifact mechanical fields land on the runtime objects
loaded from JSON. Per the play-test rule's exception for randomized/late-game
content, these are the substitute for play-testing rare artifact drops.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from items import load_items


def _find(items, item_id):
    for i in items:
        if getattr(i, 'id', None) == item_id:
            return i
    raise AssertionError(f"item {item_id!r} not found in loaded items")


# ---------- weapons ----------

def test_khopesh_of_anubis_kill_max_hp_grant():
    w = _find(load_items('weapon'), 'khopesh_of_anubis')
    assert w.kill_max_hp_bonus == 1
    assert w.kill_max_hp_cap == 10
    # runtime accumulator must start at 0 so the cap math works
    assert w._max_hp_granted == 0
    # it also has the legacy kill-heal field
    assert w.kill_heal_amount == 3


def test_chandrahasa_low_hp_damage_bonus_flag():
    w = _find(load_items('weapon'), 'chandrahasa')
    assert w.low_hp_damage_bonus is True


def test_amenonuhoko_aoe_slow_on_kill_flag():
    w = _find(load_items('weapon'), 'amenonuhoko')
    assert w.aoe_slow_on_kill is True


def test_green_chapel_axe_on_hit_regen():
    w = _find(load_items('weapon'), 'green_chapel_axe')
    assert w.on_hit_regen == 3


# ---------- armor ----------

def test_coat_of_cu_chulainn_berserk_fields_complete():
    a = _find(load_items('armor'), 'coat_of_cu_chulainn')
    assert a.berserk_trigger is True
    assert 0 < a.berserk_hp_threshold <= 1
    assert a.berserk_str_bonus > 0
    assert a.berserk_duration > 0
    assert a.berserk_hp_cost > 0


def test_babr_e_bayan_first_hit_absorb_flag():
    a = _find(load_items('armor'), 'babr_e_bayan')
    assert a.first_hit_absorb is True


def test_tarnhelm_invisibility_fields():
    a = _find(load_items('armor'), 'tarnhelm')
    assert a.invisibility_power is True
    assert a.invisibility_duration > 0


# ---------- shields ----------

def test_svalinn_fire_reflect():
    s = _find(load_items('shield'), 'svalinn')
    assert s.fire_reflect > 0


def test_ancile_quiz_timer_bonus():
    s = _find(load_items('shield'), 'ancile')
    assert s.quiz_timer_bonus > 0


# ---------- accessories ----------

def test_eye_of_horus_passive_regen():
    a = _find(load_items('accessory'), 'eye_of_horus')
    assert a.passive_regen == 1
    assert a.passive_regen_interval == 5


def test_draupnir_gold_multiplier():
    a = _find(load_items('accessory'), 'draupnir')
    assert a.gold_multiplier == 2.0


def test_torc_of_boudicca_surrounded_ac_bonus():
    a = _find(load_items('accessory'), 'torc_of_boudicca')
    assert a.surrounded_ac_bonus == 2


def test_jade_cicada_death_save_flag():
    a = _find(load_items('accessory'), 'jade_cicada')
    assert a.death_save is True


def test_seal_of_solomon_pacify_chance():
    a = _find(load_items('accessory'), 'seal_of_solomon')
    assert a.pacify_chance == 0.2


def test_ankh_of_isis_resurrect_on_death_flag():
    a = _find(load_items('accessory'), 'ankh_of_isis')
    assert a.resurrect_on_death is True


def test_plain_accessory_has_safe_artifact_field_defaults():
    """Non-artifact accessories must have safe zero/false defaults for the
    new fields, so the `if getattr(...) > 0` checks in main.py exclude them."""
    artifact_ids = {
        'eye_of_horus', 'draupnir', 'torc_of_boudicca',
        'jade_cicada', 'seal_of_solomon', 'ankh_of_isis',
    }
    accs = load_items('accessory')
    plain = next((a for a in accs if a.id not in artifact_ids), None)
    assert plain is not None, "expected at least one non-artifact accessory"
    assert plain.passive_regen == 0
    assert plain.passive_regen_interval == 5
    assert plain.gold_multiplier == 0.0
    assert plain.surrounded_ac_bonus == 0
    assert plain.pacify_chance == 0.0
    assert plain.death_save is False
    assert plain.resurrect_on_death is False


# ---------- carried artifacts (id-based detection) ----------

def test_palladium_loaded():
    p = _find(load_items('artifact'), 'palladium')
    assert p.id == 'palladium'


def test_tablet_of_destinies_loaded():
    t = _find(load_items('artifact'), 'tablet_of_destinies')
    assert t.id == 'tablet_of_destinies'


# ---------- pure-function: Ancile quiz timer bonus ----------

def test_player_get_quiz_extra_seconds_no_shield():
    """No shield equipped — bonus is 0 for any subject."""
    from player import Player
    p = Player.__new__(Player)
    p.shield = None
    p.quiz_timer_bonuses = {}
    for subj in ('math', 'geography', 'history', 'animal', 'cooking'):
        assert p.get_quiz_extra_seconds(subj) == 0


def test_player_get_quiz_extra_seconds_with_ancile():
    """Ancile equipped — bonus is +quiz_timer_bonus on every subject."""
    from player import Player
    p = Player.__new__(Player)
    p.quiz_timer_bonuses = {}
    ancile = _find(load_items('shield'), 'ancile')
    p.shield = ancile
    expected = ancile.quiz_timer_bonus
    for subj in ('math', 'geography', 'history', 'animal', 'cooking'):
        assert p.get_quiz_extra_seconds(subj) == expected


# ---------- quiz engine reroll flag default ----------

def test_quiz_engine_reroll_flag_default_off():
    """Tablet of Destinies sets `_reroll_flag` per quiz; default state must be falsy."""
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    assert not getattr(qe, '_reroll_flag', False)
