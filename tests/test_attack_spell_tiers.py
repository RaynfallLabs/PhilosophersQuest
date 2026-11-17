"""Every attack spell family has a spell in every tier (Brandon, decision 14,
2026-11-16: "yes, fill the attack families"). Eleven were added: Acid Splash
and Corrosion, Breath of Boreas, Call Lightning, Life Tap, Vampiric Touch and
Enervation, Sacred Flame, Holy Bolt, Flame Strike and Judgment."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

from spells import LEARNABLE_SPELLS, REACH_SHORT, REACH_TOUCH, spell_reach  # noqa: E402

ATTACK_FAMILIES = ('fire', 'cold', 'lightning', 'force', 'acid', 'drain_life', 'smite')
NEW = ('acid_splash_spell', 'corrosion_spell', 'breath_of_boreas_spell', 'call_lightning_spell',
       'life_tap_spell', 'vampiric_touch_spell', 'enervation_spell', 'sacred_flame_spell',
       'holy_bolt_spell', 'flame_strike_spell', 'judgment_spell')
BOOKS = json.load(open(os.path.join(ROOT, 'data', 'items', 'spellbook.json'), encoding='utf-8'))


def test_every_attack_family_has_all_five_tiers():
    for fam in ATTACK_FAMILIES:
        tiers = sorted(s['tier'] for s in LEARNABLE_SPELLS.values() if s.get('spell_family') == fam)
        assert tiers == [1, 2, 3, 4, 5], (fam, tiers)


def test_every_spell_has_a_book_at_its_tiers_depth():
    by_spell = {b['spell_id']: b for b in BOOKS.values() if b.get('spell_id')}
    band = {1: 1, 2: 15, 3: 35, 4: 55, 5: 75}
    for sid in NEW:
        s = LEARNABLE_SPELLS[sid]
        book = by_spell[sid]
        assert book['tier'] == book['quiz_tier'] == s['tier'], sid
        assert book['min_level'] == band[s['tier']], sid
        assert book['mp_cost'] == s['mp_cost'] and book['spell_name'] == s['name'], sid
        assert len(book['lore']) > 120, sid


def test_the_new_spells_use_handlers_that_exist():
    src = open(os.path.join(ROOT, 'src', 'game_magic.py'), encoding='utf-8').read()
    for sid in NEW:
        assert f"effect == '{LEARNABLE_SPELLS[sid]['effect']}'" in src, sid


def test_touch_and_short_reach_follow_the_lore():
    for sid in ('life_tap_spell', 'vampiric_touch_spell', 'enervation_spell'):
        assert spell_reach(LEARNABLE_SPELLS[sid]) == REACH_TOUCH, sid
    for sid in ('acid_splash_spell', 'sacred_flame_spell'):
        assert spell_reach(LEARNABLE_SPELLS[sid]) == REACH_SHORT, sid
    for sid in ('holy_bolt_spell', 'flame_strike_spell', 'judgment_spell', 'call_lightning_spell',
                'corrosion_spell'):
        assert spell_reach(LEARNABLE_SPELLS[sid]) is None, sid


def test_a_shared_handler_names_the_spell_cast():
    """Acid Splash and Corrosion share the acid arrow's handler, Breath of
    Boreas the ice storm's: each message names the spell, not its neighbour."""
    src = open(os.path.join(ROOT, 'src', 'game_magic.py'), encoding='utf-8').read()
    assert "An acid arrow strikes" not in src
    assert 'f"Ice Storm! ' not in src
