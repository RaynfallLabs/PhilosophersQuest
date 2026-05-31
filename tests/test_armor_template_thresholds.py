"""Verify every armor template has an explicit equip_threshold matching
its armor_class_tier (light=1, medium=2, heavy=3), and that
instantiate_armor() honors it.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


EXPECTED = {'light': 1, 'medium': 2, 'heavy': 3}


def _templates():
    out = {}
    for path in glob.glob(str(ROOT / "data" / "templates" / "armor" / "*.json")):
        name = os.path.basename(path)[:-5]
        with open(path, encoding='utf-8') as f:
            out[name] = json.load(f)
    return out


def test_every_armor_template_has_equip_threshold():
    """No template missing the field — even future additions must opt in."""
    templates = _templates()
    missing = [name for name, t in templates.items() if 'equip_threshold' not in t]
    assert not missing, f"Missing equip_threshold: {missing}"


def test_every_template_threshold_matches_class_tier():
    """light=1, medium=2, heavy=3 — uniform across the bank."""
    templates = _templates()
    mismatches = []
    for name, t in templates.items():
        tier = t.get('armor_class_tier')
        if tier not in EXPECTED:
            mismatches.append(f"{name}: unknown armor_class_tier={tier!r}")
            continue
        expected = EXPECTED[tier]
        actual = t.get('equip_threshold')
        if actual != expected:
            mismatches.append(
                f"{name} ({tier}): expected {expected}, got {actual}")
    assert not mismatches, "\n".join(mismatches)


def test_total_templates_covered():
    """34 templates total; mismatch means a new file or rename slipped in."""
    templates = _templates()
    assert len(templates) >= 30, f"Suspiciously few templates: {len(templates)}"


def test_class_tier_distribution():
    """Sanity-check the light/medium/heavy distribution didn't drift."""
    templates = _templates()
    by_tier = {'light': 0, 'medium': 0, 'heavy': 0}
    for t in templates.values():
        by_tier[t['armor_class_tier']] = by_tier.get(t['armor_class_tier'], 0) + 1
    assert by_tier['light'] >= 8
    assert by_tier['medium'] >= 8
    assert by_tier['heavy'] >= 8


# ---------------------------------------------------------------------------
# Behavior: instantiate_armor honors the template threshold
# ---------------------------------------------------------------------------

def test_instantiate_armor_uses_template_threshold_light():
    from items import instantiate_armor
    # leather (light) + leather material — any T1 combo
    armor = instantiate_armor('leather', 'leather')
    assert armor.equip_threshold == 1


def test_instantiate_armor_uses_template_threshold_medium():
    from items import instantiate_armor
    # ringmail (medium) + ring_iron material
    armor = instantiate_armor('ringmail', 'ring_iron')
    assert armor.equip_threshold == 2


def test_instantiate_armor_uses_template_threshold_heavy():
    from items import instantiate_armor
    # plate (heavy) + damascus_steel material
    armor = instantiate_armor('plate', 'damascus_steel')
    assert armor.equip_threshold == 3


def test_instantiate_armor_heavy_at_high_tier_keeps_threshold():
    """Materials drive tier (power), templates drive threshold (complexity).
    A primordial_stone plate is T5 but still threshold 3.
    """
    from items import instantiate_armor
    armor = instantiate_armor('plate', 'primordial_stone_armor')
    assert armor.equip_threshold == 3
    assert armor.tier >= 4  # primordial_stone peak_floor 94 → t5
