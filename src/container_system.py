"""
Container / lockpicking system.

Flow (v2.6.6 lockpick v3, 2026-09-03):
  attempt_lockpick(player, container, quiz_engine, dungeon, monsters, callback)
    -> starts an Economics THRESHOLD quiz (1 Q at container.quiz_tier).
    -> on success: chest opens, generates full loot table (3-4 items + bonus +
                   rare_chance x 2), returns items + gold.
    -> on failure: no loot, trap fires at CHEST tier (not floor tier -- bug
                   fixed pre-v2.6.6). Chest is marked opened.

Rationale: match the harvest/cook/identify v3 pattern (one question, binary
outcome). Prior chain-scaled loot rewarded chain length; the failure mode
was empty-chest-plus-maybe-trap. Under v3, success = the full authored
haul; failure = a real trap consequence. Traps live in data/chest_traps.json
and are picked by chest tier. See PLAYABILITY_PASS_AUDIT.md.

Mimic check:
  Handled directly in main.py via _spawn_mimic(container, monsters)
"""

import copy
import json
import os
import random

from dice import roll, roll_duration


# ---------------------------------------------------------------------------
# Loot curve — post-v2.6.6: success is single-outcome (matches old chain-5)
# ---------------------------------------------------------------------------

# Full-success item count: 3-4 real slots + 1 guaranteed bonus common
# (matches the old chain-5 "Master Thief" tier -- see PLAYABILITY_PASS_AUDIT.md).
FULL_ITEM_COUNT: tuple[int, int] = (3, 4)
FULL_BONUS_SLOTS: int = 1

# Rare (unique) chance multiplier vs the JSON `rare_chance_chain3` baseline.
# Matches the old chain-5 multiplier so a successful pick yields the full
# authored rare rate.
FULL_RARE_MULT: float = 2.0


# ---------------------------------------------------------------------------
# Trap pool -- loaded from data/chest_traps.json (v2.6.6+)
# ---------------------------------------------------------------------------

_TRAP_POOL_CACHE: dict[int, list[dict]] | None = None


def _load_trap_pool() -> dict[int, list[dict]]:
    """Load traps_by_tier from data/chest_traps.json. Cached."""
    global _TRAP_POOL_CACHE
    if _TRAP_POOL_CACHE is None:
        from paths import data_path
        p = data_path('data', 'chest_traps.json')
        with open(p, encoding='utf-8') as f:
            raw = json.load(f).get('traps_by_tier', {})
        _TRAP_POOL_CACHE = {int(k): v for k, v in raw.items()}
    return _TRAP_POOL_CACHE


def pick_trap_for_chest(container, rng=None) -> dict:
    """Pick a random trap keyed by CHEST tier (not floor tier).

    v2.6.6 fix: pre-v2.6.6 code in dungeon.py used floor tier, so a T1
    chest at floor 50 got a T3 trap. The chest's own tier now drives
    severity.
    """
    rng = rng or random
    tier = max(1, min(5, int(getattr(container, 'tier', 1))))
    pool = _load_trap_pool().get(tier) or _load_trap_pool().get(1) or []
    if not pool:
        return {}
    return dict(rng.choice(pool))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def attempt_lockpick(player, container, quiz_engine, dungeon, monsters, on_complete):
    """v2.6.6 lockpick v3: ONE economics question at container.quiz_tier.

    on_complete({'status': str, 'loot': list, 'gold': int, 'messages': list[tuple]})
      status: 'opened' (always -- one attempt per chest)
      loot:   list of Item instances (populated on success, [] on failure)
      gold:   int
      messages: list of (text, type) pairs

    Right -> the chest yields its full authored haul (3-4 items + bonus common
             + rare_chance x 2). Gold rolls at the top of the range.
    Wrong -> no loot. A trap fires, keyed by chest.tier (see chest_traps.json).
             Chest is marked opened -- no retry, the chest itself is the cost.
    """
    def _callback(result):
        if getattr(result, 'success', False):
            _handle_success(player, container, dungeon, on_complete)
        else:
            _handle_failure(player, container, dungeon, monsters, on_complete)

    quiz_engine.start_quiz(
        mode='threshold',
        subject='economics',
        tier=max(1, int(getattr(container, 'quiz_tier', 1) or 1)),
        callback=_callback,
        threshold=1,
        total_qs=1,
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
        extra_seconds=getattr(player, 'get_quiz_extra_seconds', lambda s: 0)('economics'),
        base_seconds=player.get_quiz_timer('economics'),
    )



# ---------------------------------------------------------------------------
# Outcome handlers
# ---------------------------------------------------------------------------

def _handle_success(player, container, dungeon, on_complete):
    """v2.6.6: success = the chest's full authored haul.
    Gold rolls at the TOP of the range (you did it right)."""
    messages = []
    container.opened = True
    container._gold_bonus_accum = 0

    gmin, gmax = (container.gold[0], container.gold[1]) if container.gold else (0, 0)
    if gmax > 0:
        # Full success gets the top of the range (with a small floor at
        # 70% for variance). Bias upward, unlike the old chain-scaled bias.
        lo = int(gmin + (gmax - gmin) * 0.7)
        gold = random.randint(lo, gmax)
    else:
        gold = 0

    loot = _generate_loot_from_template(container, dungeon.level)
    gold += int(getattr(container, '_gold_bonus_accum', 0))

    messages.insert(0, ('The lock yields! You crack the chest.', 'success'))
    if gold:
        messages.append((f'You find {gold} gold coins!', 'loot'))

    on_complete({'status': 'opened', 'loot': loot, 'gold': gold,
                 'messages': messages})


def _handle_failure(player, container, dungeon, monsters, on_complete):
    """v2.6.6: failure fires a trap at the CHEST's tier (not the floor tier).
    Chest is marked opened -- the chest itself is the cost."""
    messages = [('You fumble the lock -- the chest snaps shut.', 'warning')]
    container.opened = True

    # v2.6.6: universal fail-trap. Pick a trap keyed to CHEST tier.
    trap = pick_trap_for_chest(container)
    if trap:
        _trigger_trap(player, trap, messages)

    # Scraping-noise alert (unchanged from prior)
    if random.random() < 0.30:
        alerted = _alert_nearby(player, dungeon, monsters)
        if alerted:
            messages.append(('The scraping noise alerts nearby monsters!', 'danger'))

    on_complete({'status': 'opened', 'loot': [], 'gold': 0,
                 'messages': messages})


def _trigger_trap(player, trap: dict, messages: list):
    """Apply trap damage and optional status effect to the player."""
    dmg_roll = trap.get('damage', '0')
    raw_dmg  = roll(dmg_roll) if dmg_roll != '0' else 0
    actual   = player.take_damage(raw_dmg, 'physical') if raw_dmg else 0

    messages.append((trap.get('message', 'A trap triggers!'), 'danger'))
    if actual:
        messages.append((f'You take {actual} damage!', 'danger'))

    effect     = trap.get('effect')
    effect_dur = roll_duration(trap.get('effect_duration', 5))

    if effect:
        applied = player.add_effect(effect, effect_dur)
        if applied:
            messages.append((f"You are {effect.replace('_', ' ')}!", 'danger'))
        else:
            messages.append((f"You resist the {effect.replace('_', ' ')} effect!", 'info'))


def _alert_nearby(player, dungeon, monsters) -> bool:
    """Wake up monsters within 8 tiles. Returns True if any were alerted."""
    alerted = False
    px, py  = player.x, player.y
    for m in monsters:
        if not m.alive:
            continue
        if abs(m.x - px) <= 8 and abs(m.y - py) <= 8:
            if m.ai_pattern in ('sessile',):
                m.ai_pattern = 'aggressive'
                alerted = True
    return alerted


# ---------------------------------------------------------------------------
# Loot generation — template-driven
# ---------------------------------------------------------------------------

# Mapping from template loot-table category to (load_items class, common_filter)
# 'magic' = wand+scroll+spellbook combo (template flag); 'gear' = weapon+armor+shield combo.
_COMMON_CATEGORIES: dict[str, list[str]] = {
    'potion':         ['potion'],
    'scroll':         ['scroll'],
    'wand':           ['wand'],
    'spellbook':      ['spellbook'],
    'accessory':      ['accessory'],
    'ammo':           ['ammo'],
    'ingredient':     ['ingredient'],
    'artifact':       ['artifact'],
    'magic':          ['wand', 'scroll', 'spellbook'],
    # Gear bucket: weapon + armor + shield (all common, instantiated below)
    'gear':           ['weapon_common', 'armor_common', 'shield_common'],
}


def _floor_level_cap(container, dungeon_level: int) -> int:
    """Chest sees a small amount of floors ahead of the player. Kept modest
    since CHAIN is the new dial — chest_tier scales the lookahead bonus."""
    chest_tier = max(1, min(5, int(getattr(container, 'tier', 1))))
    return dungeon_level + chest_tier * 2


def _pull_common_gear(category: str, level_cap: int, rng) -> object | None:
    """Instantiate a common gear item for one of the gear categories."""
    from items import (pick_random_weapon_for_floor, pick_random_armor_for_floor,
                       pick_random_shield_for_floor)
    if category == 'weapon_common':
        return pick_random_weapon_for_floor(level_cap, rng)
    if category == 'armor_common':
        return pick_random_armor_for_floor(level_cap, rng)
    if category == 'shield_common':
        return pick_random_shield_for_floor(level_cap, rng)
    return None


def _build_common_pool(template: dict, level_cap: int) -> list:
    """Build a pool of NON-UNIQUE items eligible for this chest's loot.
    Gear (weapon/armor/shield) is template+material rolled at draw-time, not
    pooled here — those categories are handled by _pull_common_gear."""
    from items import load_items
    pool: list = []
    for raw_cat in template.get('loot_table', {}):
        if raw_cat in ('gold_bonus',):
            continue
        sub_cats: list[str] = []
        if raw_cat in _COMMON_CATEGORIES:
            sub_cats = _COMMON_CATEGORIES[raw_cat]
        elif raw_cat in ('weapon_common', 'armor_common', 'shield_common'):
            sub_cats = [raw_cat]
        else:
            # Unknown category — try loading directly (in case JSON adds new ones)
            sub_cats = [raw_cat]
        for sc in sub_cats:
            if sc in ('weapon_common', 'armor_common', 'shield_common'):
                continue  # handled by _pull_common_gear at draw-time
            try:
                for it in load_items(sc):
                    if getattr(it, 'is_unique', False):
                        continue
                    if it.min_level > level_cap:
                        continue
                    # Only terrain-FORAGED ingredients (tier_role 'dungeon')
                    # belong in chests -- apothecary herbs, cave mushrooms, etc.
                    # Monster-derived ingredients (family/prime/trophy) come
                    # ONLY from harvesting corpses, never from loot -- the same
                    # rule the floor-spawn path enforces (dungeon.py).
                    if sc == 'ingredient' and getattr(it, 'tier_role', '') != 'dungeon':
                        continue
                    pool.append(it)
            except (FileNotFoundError, KeyError):
                pass
    return pool


def _build_unique_pool(template: dict, level_cap: int) -> list:
    """Build a pool of UNIQUE items appropriate to this template's category mix."""
    from items import load_items
    # Map loot-table categories to the unique item classes that could fit.
    # Gear categories => weapon/armor/shield uniques. Magic => wand/scroll/spellbook.
    cat_classes: dict[str, list[str]] = {
        'weapon_common':  ['weapon'],
        'armor_common':   ['armor'],
        'shield_common':  ['shield'],
        'gear':           ['weapon', 'armor', 'shield'],
        'magic':          ['wand', 'scroll', 'spellbook'],
        'accessory':      ['accessory'],
        'wand':           ['wand'],
        'scroll':         ['scroll'],
        'spellbook':      ['spellbook'],
        'potion':         ['potion'],
        'ingredient':     ['ingredient'],
        'artifact':       ['artifact', 'accessory'],   # artifacts overlap accessories
        'ammo':           ['ammo'],
    }
    classes: set[str] = set()
    for raw_cat in template.get('loot_table', {}):
        if raw_cat == 'gold_bonus':
            continue
        for cls_name in cat_classes.get(raw_cat, []):
            classes.add(cls_name)
    pool: list = []
    for cls_name in classes:
        try:
            for it in load_items(cls_name):
                if not getattr(it, 'is_unique', False):
                    continue
                if it.min_level > level_cap:
                    continue
                # Defensive: never let a monster-derived ingredient (prime/
                # trophy) reach chest loot via the unique path either.
                if cls_name == 'ingredient' and getattr(it, 'tier_role', '') != 'dungeon':
                    continue
                pool.append(it)
        except (FileNotFoundError, KeyError):
            pass
    return pool


def _weighted_pick_category(loot_table: dict, rng) -> str:
    """Pick a loot-table category using its weight."""
    cats = list(loot_table.items())
    if not cats:
        return ''
    total = sum(max(0, w) for _, w in cats)
    if total <= 0:
        return cats[0][0]
    r = rng.random() * total
    cum = 0.0
    for cat, w in cats:
        cum += max(0, w)
        if r <= cum:
            return cat
    return cats[-1][0]


def _pull_common_from_category(category: str, common_pool: list, level_cap: int, rng) -> object | None:
    """Draw a common item for the given loot-table category."""
    # Gear categories are instantiated, not pooled
    if category in ('weapon_common', 'armor_common', 'shield_common'):
        return _pull_common_gear(category, level_cap, rng)
    # 'gear' = weighted gear instantiation
    if category == 'gear':
        sub = rng.choice(['weapon_common', 'armor_common', 'shield_common'])
        return _pull_common_gear(sub, level_cap, rng)
    # For pool-backed categories, filter pool by item_class
    sub_cats = _COMMON_CATEGORIES.get(category, [category])
    # Exclude gear sub-cats from pool filter (already handled)
    sub_cats = [sc for sc in sub_cats if sc not in ('weapon_common', 'armor_common', 'shield_common')]
    if not sub_cats:
        return None
    eligible = [it for it in common_pool
                if getattr(it, 'item_class', '') in sub_cats]
    if not eligible:
        return None
    return copy.copy(rng.choice(eligible))


def _pull_unique_from_category(category: str, unique_pool: list, rng) -> object | None:
    """Draw a unique item compatible with the given loot-table category."""
    cat_classes: dict[str, set[str]] = {
        'weapon_common':  {'weapon'},
        'armor_common':   {'armor'},
        'shield_common':  {'shield'},
        'gear':           {'weapon', 'armor', 'shield'},
        'magic':          {'wand', 'scroll', 'spellbook'},
        'accessory':      {'accessory'},
        'wand':           {'wand'},
        'scroll':         {'scroll'},
        'spellbook':      {'spellbook'},
        'potion':         {'potion'},
        'ingredient':     {'ingredient'},
        'artifact':       {'artifact', 'accessory'},
        'ammo':           {'ammo'},
    }
    classes = cat_classes.get(category, set())
    if not classes:
        return None
    eligible = [it for it in unique_pool
                if getattr(it, 'item_class', '') in classes]
    if not eligible:
        return None
    return copy.copy(rng.choice(eligible))


def _generate_loot_from_template(container, dungeon_level: int) -> list:
    """v2.6.6: generate the chest's full authored loot on successful pick.

    Item count = FULL_ITEM_COUNT (3-4 items) + FULL_BONUS_SLOTS (1 bonus common).
    Rare (unique) chance = template.rare_chance_chain3 * FULL_RARE_MULT (2x)
    -- matches the pre-v2.6.6 chain-5 "Master Thief" reward tier.
    """
    from items import get_chest_template, add_gold_to_tile  # noqa: F401  (kept for import-side-effect parity)
    template_id = getattr(container, 'template_id', '')
    template = get_chest_template(template_id) if template_id else None
    if not template:
        return []

    rng = random
    level_cap = _floor_level_cap(container, dungeon_level)

    common_pool = _build_common_pool(template, level_cap)
    unique_pool = _build_unique_pool(template, level_cap)

    cmin, cmax = FULL_ITEM_COUNT
    n_items = rng.randint(cmin, cmax)

    base_rare = float(template.get('rare_chance_chain3', 0.0))
    eff_rare = min(1.0, base_rare * FULL_RARE_MULT)

    bonus_slots = FULL_BONUS_SLOTS
    total_slots = n_items + bonus_slots

    loot: list = []
    loot_table = template.get('loot_table', {})

    # Decide UP FRONT whether this chest carries a unique, and which slot it
    # occupies. Bonus slot is always common — only the "real" slots are
    # eligible for the unique.
    rare_slot_index = -1
    if unique_pool and rng.random() < eff_rare and n_items > 0:
        rare_slot_index = rng.randrange(n_items)

    def draw_common() -> object | None:
        category = _weighted_pick_category(loot_table, rng)
        if not category:
            return None
        if category == 'gold_bonus':
            extra = rng.randint(1, 10) * max(1, dungeon_level)
            container._gold_bonus_accum = getattr(container, '_gold_bonus_accum', 0) + extra
            return None
        return _pull_common_from_category(category, common_pool, level_cap, rng)

    def draw_unique() -> object | None:
        # Pick a category from the loot table that has a unique counterpart
        category = _weighted_pick_category(loot_table, rng)
        if not category or category == 'gold_bonus':
            return None
        it = _pull_unique_from_category(category, unique_pool, rng)
        if it is not None:
            return it
        # No unique in that category — try a free pick from the unique_pool
        if unique_pool:
            return copy.copy(rng.choice(unique_pool))
        return None

    for i in range(n_items):
        if i == rare_slot_index:
            it = draw_unique()
            # Fall through to common if no unique materialized
            if it is None:
                it = draw_common()
        else:
            it = draw_common()
        if it is not None:
            loot.append(it)

    for _ in range(bonus_slots):
        it = draw_common()
        if it is not None:
            loot.append(it)

    # If template has pre_identified=True (merchant_strongbox), identify all loot
    if template.get('pre_identified'):
        for it in loot:
            if hasattr(it, 'identified'):
                it.identified = True
            if hasattr(it, 'id_level'):
                it.id_level = 5
            if hasattr(it, 'buc_known'):
                it.buc_known = True

    return loot


# ---------------------------------------------------------------------------
# Mimic spawn (unchanged — kept here for module locality)
# ---------------------------------------------------------------------------

def _spawn_mimic(container, monsters: list, dungeon_level: int = 1):
    """Replace a mimic container with a level-appropriate mimic monster.
    Spans the whole floor curve — mid/late game uses the new mimic-AI
    monsters added in the 2026 monster expansion."""
    import json
    from monster import Monster

    from paths import data_path
    monsters_path = data_path('data', 'monsters.json')
    with open(monsters_path, encoding='utf-8') as f:
        all_defs = json.load(f)

    # Tiered mimic by depth — each band has a distinct visual+threat profile
    if dungeon_level >= 80:
        mid = 'abyssal_mimic'      # F75 peak — endgame
    elif dungeon_level >= 60:
        mid = 'gilded_mimic'       # F66 peak (new) — high-mid, paralyzing maw
    elif dungeon_level >= 45:
        mid = 'lurking_horror'     # F55 peak (new) — late-mid, mimic-AI horror
    elif dungeon_level >= 25:
        mid = 'greater_mimic'      # F35 peak — mid
    else:
        mid = 'mimic'              # F8 peak — early

    defn = all_defs.get(mid) or all_defs.get('mimic')
    if defn is None:
        return None

    mimic = Monster({**defn, 'id': mid}, container.x, container.y)
    monsters.append(mimic)
    return mimic
