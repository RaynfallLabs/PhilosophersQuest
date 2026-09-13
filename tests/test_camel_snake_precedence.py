"""camelCase-vs-snake_case load-precedence guard (v2.15.0).

Background (audit v2.14.1): several `items.py` fields historically had TWIN
JSON keys — one camelCase (older canon) and one snake_case (newer rebase).
The `.get()` fallback chain in `items.py` used to prefer camelCase first,
so newer snake-case rebases were silently ignored on any entry that still
carried the stale camel field. Chandrahas base_damage=14 was overridden by
baseDamage=32; Punch-in-the-Face base_damage=35 was overridden by baseDamage
=9999. This test suite pins the new invariant: snake_case wins.

Two guards:
  1. `items.py` source guard — every twin-field `.get()` chain must list
     snake_case first (no `defn.get('camelCase', defn.get('snake_case', …))`).
  2. Data guard — every JSON entry with both keys must have the SAME value
     for both. If they diverge, the rebase silently didn't land.
"""
import inspect
import json
import os
import re

import pytest

import items


# ---------------------------------------------------------------------------
# Known twin field pairs. Keep this in sync with items.py; anything with a
# camel/snake variant should live here.
# ---------------------------------------------------------------------------
KNOWN_TWINS = [
    ('baseDamage', 'base_damage'),
    ('chainMultipliers', 'chain_multipliers'),
    ('chainExponent', 'chain_exponent'),
    ('damageTypes', 'damage_types'),
    ('twoHanded', 'two_handed'),
    ('stunChance', 'stun_chance'),
    ('bleedChance', 'bleed_chance'),
    ('ignoreShield', 'ignore_shield'),
    ('critMultiplier', 'crit_multiplier'),
    ('requiresAmmo', 'requires_ammo'),
    ('infiniteAmmo', 'infinite_ammo'),
    ('floorSpawnWeight', 'floor_spawn_weight'),
    ('containerLootTier', 'container_loot_tier'),
    ('enchantBonus', 'enchant_bonus'),
    ('poisonChance', 'poison_chance'),
    ('burnChance', 'burn_chance'),
    ('confuseChance', 'confuse_chance'),
    ('lifestealPercent', 'lifesteal_percent'),
    ('cursedMissBacklash', 'cursed_miss_backlash'),
    ('petrifyOnCrit', 'petrify_on_crit'),
    ('counterAttackChance', 'counter_attack_chance'),
    ('killHealAmount', 'kill_heal_amount'),
    ('growingPower', 'growing_power'),
    ('killsToGrow', 'kills_to_grow'),
    ('onEquipStatus', 'on_equip_status'),
    ('freezeChance', 'freeze_chance'),
    ('mathTier', 'quiz_tier'),
    ('maxChainLength', 'max_chain_length'),
]

# Every camelCase key we consider "a camel-case twin" for the source guard.
CAMEL_KEYS = {cam for cam, _ in KNOWN_TWINS}


@pytest.fixture(scope='module')
def items_source():
    return inspect.getsource(items)


def test_no_camel_first_twin_get_in_items_py(items_source):
    """items.py must never lead a `.get()` chain with a camelCase twin.

    Pattern caught: `defn.get('camelCase', ...)` where `camelCase` is a known
    twin AND is the OUTER key (not a fallback nested inside another .get).
    The correct form is `defn.get('snake_case', defn.get('camelCase', ...))`.
    """
    # Collapse whitespace so multi-line `.get(\n    'key', ...)` reads as one line.
    flat = re.sub(r"\s+", " ", items_source)
    # match `defn.get('camelCase'` — we only care about outer-position matches.
    pattern = re.compile(r"defn\.get\(\s*['\"]([a-z][a-zA-Z]*[A-Z][a-zA-Z]*)['\"]")
    violations = []
    for match in pattern.finditer(flat):
        key = match.group(1)
        if key not in CAMEL_KEYS:
            continue
        # Look back a few chars: if the character just before `defn.get(` is `,`
        # or `(`, this .get is a nested fallback ARGUMENT to another .get — that
        # is the allowed position for the camel key. If the preceding non-space
        # character is `=` (assignment), the camel is the OUTER (leading) key,
        # which is exactly the bug we want to catch.
        i = match.start() - 1
        while i >= 0 and flat[i] == ' ':
            i -= 1
        prev = flat[i] if i >= 0 else ''
        if prev in (',', '('):
            continue  # nested fallback — OK
        # Find the enclosing source line for the report.
        # Recover the original line by searching the raw source for a unique window.
        window = flat[match.start():match.start() + 40]
        # Best-effort: strip to just the key for a searchable literal.
        marker = f"defn.get('{key}'"
        lineno = None
        for i2, line in enumerate(items_source.splitlines(), start=1):
            if marker in line.replace('"', "'"):
                lineno = i2
                break
        violations.append((lineno, key, window))
    if violations:
        msg = "camelCase-first .get() on twin field(s):\n" + "\n".join(
            f"  items.py:{ln}  key={k!r}  |  {w}"
            for ln, k, w in violations
        )
        pytest.fail(msg)


def _iter_item_entries():
    """Yield (filename, key_or_index, entry_dict) for every item entry."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'items')
    for fname in sorted(os.listdir(data_dir)):
        if not fname.endswith('.json'):
            continue
        path = os.path.join(data_dir, fname)
        with open(path, encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                continue
        if isinstance(data, dict):
            for key, entry in data.items():
                if isinstance(entry, dict):
                    yield fname, key, entry
        elif isinstance(data, list):
            for i, entry in enumerate(data):
                if isinstance(entry, dict):
                    yield fname, i, entry


@pytest.mark.parametrize('camel,snake', KNOWN_TWINS)
def test_twin_field_values_agree(camel, snake):
    """When an item JSON entry carries BOTH twin keys, values must agree.

    Snake_case is authoritative (rebase scripts wrote snake); a divergence
    means the older camel value is stale and would win under the OLD .get()
    precedence — the bug this whole change fixes.
    """
    divergences = []
    for fname, key, entry in _iter_item_entries():
        if camel in entry and snake in entry and entry[camel] != entry[snake]:
            name = entry.get('name', key)
            divergences.append(
                f"  {fname} :: {name}  {camel}={entry[camel]!r}  {snake}={entry[snake]!r}"
            )
    if divergences:
        pytest.fail(
            f"{camel}/{snake} divergence in {len(divergences)} entries "
            f"(snake is authoritative — set camel to match):\n"
            + "\n".join(divergences[:20])
            + ("\n  ... (truncated)" if len(divergences) > 20 else "")
        )


def test_items_module_loads():
    """Sanity: items module and its subclass table import cleanly."""
    assert hasattr(items, 'Weapon')
    assert hasattr(items, 'Armor')
    assert hasattr(items, 'Shield')
    assert hasattr(items, 'Accessory')
