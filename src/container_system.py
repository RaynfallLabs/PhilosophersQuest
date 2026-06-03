"""
Container / lockpicking system.

Flow (post-2026-05-19 template rebuild):
  attempt_lockpick(player, container, quiz_engine, dungeon, monsters, callback)
    -> starts an Economics ESCALATOR_CHAIN quiz starting at container.quiz_tier.
    -> on chain >= 1: chest opens, generates loot via template, returns items + gold
    -> on chain == 0: chest opens visually but yields NO loot; trap fires if present;
                      no retry — chest is marked opened.

  Chain curve scales rare/unique odds AND item count:
      chain 1 (Pried)         0.25x rare, 1 item
      chain 2 (Cracked)       0.50x rare, 2 items
      chain 3 (Opened)        1.00x rare, 2-3 items   (baseline; matches template rare%)
      chain 4 (Picked clean)  1.50x rare, 3 items
      chain 5 (Master thief)  2.00x rare, 3-4 items + 1 guaranteed bonus common

Mimic check:
  Handled directly in main.py via _spawn_mimic(container, monsters)
"""

import copy
import random

from dice import roll, roll_duration


# ---------------------------------------------------------------------------
# Chain → loot curve (escalator-chain Economics)
# ---------------------------------------------------------------------------

CHAIN_RARE_MULT: dict[int, float] = {
    0: 0.0,
    1: 0.25,
    2: 0.50,
    3: 1.00,
    4: 1.50,
    5: 2.00,
}

# Per chain rung: minimum and maximum loot slot count. Chain 5 also gets +1
# bonus item, added on top of whatever sample falls in the (min,max) range.
CHAIN_ITEM_COUNT: dict[int, tuple[int, int]] = {
    0: (0, 0),
    1: (1, 1),
    2: (2, 2),
    3: (2, 3),
    4: (3, 3),
    5: (3, 4),
}

# Labels that describe the chain rung — surfaced in messages and tests.
CHAIN_LABELS: dict[int, str] = {
    0: 'Failed',
    1: 'Pried',
    2: 'Cracked',
    3: 'Opened',
    4: 'Picked clean',
    5: 'Master thief',
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def attempt_lockpick(player, container, quiz_engine, dungeon, monsters, on_complete):
    """
    Start an Economics escalator-chain quiz to open *container*.

    on_complete({'status': str, 'loot': list, 'gold': int, 'messages': list[tuple]})
      status: 'opened' (always — chain 0 yields opened-but-empty)
      loot:   list of Item instances (empty when chain 0)
      gold:   int (0 when chain 0)
      messages: list of (text, type) pairs

    The Master Lockpick is a permanent inventory item; no charges to track.
    """
    def _callback(result):
        # In escalator-chain mode, `result.score` carries the peak chain
        # length reached. After a wrong answer the engine resets `.chain`
        # back to 0, so score is the correct field to read for the loot
        # curve. Clamp to 0..5 (engine caps at max_chain=5 above).
        chain = int(getattr(result, 'score', 0))
        chain = max(0, min(5, chain))
        if chain == 0:
            _handle_failure(player, container, dungeon, monsters, on_complete)
        else:
            _handle_success(player, container, dungeon, chain, on_complete)

    # Escalator-chain ALWAYS starts at T1 and ramps T1→T5 from there. The
    # legacy `quiz_tier`/`tier` field on containers was a difficulty knob
    # for the OLD threshold-mode design; passing it through here makes the
    # FIRST question be a T4/T5 question. (Same bug fixed for harvest in
    # food_system.py — bug bash 2026-06-01.)
    quiz_engine.start_quiz(
        mode='escalator_chain',
        subject='economics',
        tier=1,
        callback=_callback,
        max_chain=5,
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
        extra_seconds=getattr(player, 'get_quiz_extra_seconds', lambda s: 0)('economics'),
        base_seconds=player.get_quiz_timer('economics'),
    )



# ---------------------------------------------------------------------------
# Outcome handlers
# ---------------------------------------------------------------------------

def _handle_success(player, container, dungeon, chain: int, on_complete):
    messages = []
    container.opened = True

    # Reset gold_bonus accumulator before loot generation populates it
    container._gold_bonus_accum = 0

    # Gold scales softly with chain — chain 5 gives the top of range; chain 1
    # gives the bottom. Stay within the template's gold_range either way.
    gmin, gmax = (container.gold[0], container.gold[1]) if container.gold else (0, 0)
    if gmax > 0:
        # Bias the roll by chain: chain 1 = min, chain 5 = max, chain 3 = mid.
        bias = (chain - 1) / 4.0  # 0..1 across chain 1..5
        bias = max(0.0, min(1.0, bias))
        lo = int(gmin + (gmax - gmin) * max(0.0, bias - 0.25))
        hi = int(gmin + (gmax - gmin) * min(1.0, bias + 0.25))
        gold = random.randint(min(lo, hi), max(lo, hi)) if hi >= lo else gmin
    else:
        gold = 0

    loot = _generate_loot_from_template(container, dungeon.level, chain)

    # Roll-up any gold_bonus slots that fired during loot generation
    gold += int(getattr(container, '_gold_bonus_accum', 0))

    # Lead message reflects the chain rung
    label = CHAIN_LABELS.get(chain, 'Opened')
    if chain >= 4:
        messages.insert(0, (f'{label}! The lock yields gracefully.', 'success'))
    else:
        messages.insert(0, ('The lock clicks open!', 'success'))
    if gold:
        messages.append((f'You find {gold} gold coins!', 'loot'))

    on_complete({'status': 'opened', 'loot': loot, 'gold': gold,
                 'messages': messages, 'chain': chain})


def _handle_failure(player, container, dungeon, monsters, on_complete):
    """Chain 0: chest visually opens but yields no loot. Trap fires if present."""
    messages = [('You fumble the lock -- the chest pops open, empty.', 'warning')]
    container.opened = True

    # Trap: triggers on the empty open if present
    if container.trapped and not container.trap_triggered:
        container.trap_triggered = True
        _trigger_trap(player, container.trap, messages)

    # 30% chance to alert nearby monsters (scraping noise)
    if random.random() < 0.30:
        alerted = _alert_nearby(player, dungeon, monsters)
        if alerted:
            messages.append(('The scraping noise alerts nearby monsters!', 'danger'))

    on_complete({'status': 'opened', 'loot': [], 'gold': 0,
                 'messages': messages, 'chain': 0})


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


def _generate_loot_from_template(container, dungeon_level: int, chain: int) -> list:
    """Generate loot for a chest using its template + the player's chain rung.

    Chain 0 is handled by _handle_failure (returns []). chain 1..5 lands here.
    """
    from items import get_chest_template, add_gold_to_tile  # noqa: F401  (kept for import-side-effect parity)
    if chain <= 0:
        return []
    template_id = getattr(container, 'template_id', '')
    template = get_chest_template(template_id) if template_id else None
    if not template:
        # No template — legacy fallback: empty loot. The 12-template rebuild
        # is the intended path; legacy containers should never reach here.
        return []

    rng = random
    level_cap = _floor_level_cap(container, dungeon_level)

    # Pre-build pools per chest open (template categories often overlap)
    common_pool  = _build_common_pool(template, level_cap)
    unique_pool  = _build_unique_pool(template, level_cap)

    # Item count for this chain rung
    cmin, cmax = CHAIN_ITEM_COUNT.get(chain, (1, 1))
    n_items = rng.randint(cmin, cmax)

    # Effective rare chance, scaled by chain rung. SINGLE roll per chest:
    # the chest is one lottery ticket. If rare_roll succeeds, ONE slot of
    # the chest becomes a unique; otherwise all slots are commons. This
    # bounds endgame uniques (target ~17/run at chain 3) and makes the
    # "I got a unique!" moment discrete and exciting for players.
    base_rare = float(template.get('rare_chance_chain3', 0.0))
    rare_mult = CHAIN_RARE_MULT.get(chain, 1.0)
    eff_rare  = min(1.0, base_rare * rare_mult)

    # Chain 5: one bonus item, guaranteed common (never the rare slot)
    bonus_slots = 1 if chain == 5 else 0
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
