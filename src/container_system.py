"""
Container / lockpicking system.

Flow:
  attempt_lockpick(player, container, quiz_engine, dungeon, monsters, callback)
    -> starts economics threshold quiz
    -> on success: opens container, generates loot, returns items + gold
    -> on failure: triggers trap (first failure only), damages lockpick,
                  30% chance to alert nearby monsters

Mimic check:
  Handled directly in main.py via _spawn_mimic(container, monsters)
"""

import random

from dice import roll


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def attempt_lockpick(player, container, quiz_engine, dungeon, monsters, on_complete):
    """
    Start an Economics threshold quiz to open *container*.

    on_complete({'status': str, 'loot': list, 'gold': int, 'messages': list[tuple]})
      status: 'opened' | 'failed'
      loot:   list of Item instances (empty on failure)
      gold:   int (0 on failure)
      messages: list of (text, type) pairs

    The Master Lockpick is a permanent inventory item; no charges to track.
    """
    def _callback(result):
        if result.success:
            _handle_success(player, container, dungeon, on_complete)
        else:
            _handle_failure(player, container, dungeon, monsters, on_complete)

    quiz_engine.start_quiz(
        mode='threshold',
        subject='economics',
        tier=container.tier,
        callback=_callback,
        threshold=container.quiz_threshold,
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
        extra_seconds=getattr(player, 'get_quiz_extra_seconds', lambda s: 0)('economics'),
        base_seconds=player.get_quiz_timer('economics'),
    )



# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _handle_success(player, container, dungeon, on_complete):
    messages = []
    container.opened = True

    gold = random.randint(container.gold[0], container.gold[1])
    loot = _generate_loot(container, dungeon.level)

    messages.insert(0, ('The lock clicks open!', 'success'))
    if gold:
        messages.append((f'You find {gold} gold coins!', 'loot'))

    on_complete({'status': 'opened', 'loot': loot, 'gold': gold, 'messages': messages})


def _handle_failure(player, container, dungeon, monsters, on_complete):
    messages = [('The lock resists your attempt.', 'warning')]

    # Trap: triggers only on first failure
    if container.trapped and not container.trap_triggered:
        container.trap_triggered = True
        _trigger_trap(player, container.trap, messages)

    # 30% chance to alert nearby monsters
    if random.random() < 0.30:
        alerted = _alert_nearby(player, dungeon, monsters)
        if alerted:
            messages.append(('The scraping noise alerts nearby monsters!', 'danger'))

    on_complete({'status': 'failed', 'loot': [], 'gold': 0, 'messages': messages})


def _trigger_trap(player, trap: dict, messages: list):
    """Apply trap damage and optional status effect to the player."""
    dmg_roll = trap.get('damage', '0')
    raw_dmg  = roll(dmg_roll) if dmg_roll != '0' else 0
    actual   = player.take_damage(raw_dmg, 'physical') if raw_dmg else 0

    messages.append((trap.get('message', 'A trap triggers!'), 'danger'))
    if actual:
        messages.append((f'You take {actual} damage!', 'danger'))

    effect     = trap.get('effect')
    effect_dur = int(trap.get('effect_duration', 5))

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


# Per container tier: which item categories to draw from, max quiz tier
# allowed, whether legendary-flagged items appear, AND the per-item-pick chance
# that a named unique replaces the regular loot pick (escalating with tier).
# Uniques mostly enter the game through chests now — floor drops are 1-in-25.
_TIER_LOOT_CFG: dict[int, dict] = {
    1: {'classes': ['weapon', 'armor', 'ammo', 'potion'],
        'max_tier': 2, 'legendary': False, 'unique_chance': 0.00},
    2: {'classes': ['weapon', 'armor', 'ammo', 'accessory', 'shield', 'potion'],
        'max_tier': 3, 'legendary': False, 'unique_chance': 0.02},
    3: {'classes': ['weapon', 'armor', 'accessory', 'shield', 'potion', 'scroll', 'wand'],
        'max_tier': 4, 'legendary': False, 'unique_chance': 0.08},
    4: {'classes': ['weapon', 'armor', 'accessory', 'shield', 'potion', 'scroll', 'wand', 'spellbook'],
        'max_tier': 5, 'legendary': False, 'unique_chance': 0.20},
    5: {'classes': ['weapon', 'armor', 'accessory', 'shield', 'potion', 'scroll', 'wand', 'spellbook'],
        'max_tier': 5, 'legendary': True,  'unique_chance': 0.40},
}


def _item_tier(item) -> int:
    """Return the effective quiz/difficulty tier of an item (1-5)."""
    return int(getattr(item, 'quiz_tier',
               getattr(item, 'tier', 1)))


def _generate_loot(container, dungeon_level: int) -> list:
    """
    Pick 1+ items whose tier and class match the container's tier.
    Higher-tier containers draw from more categories, allow higher-tier
    items, and bias toward the best items in the pool.

    Chests give loot from up to 10 levels ahead of floor spawns — the
    bonus scales with container tier (T1: +2, T2: +4, T3: +6, T4: +8, T5: +10).
    """
    import copy
    from items import load_items

    container_tier = max(1, min(5, getattr(container, 'tier', 1)))
    cfg = _TIER_LOOT_CFG[container_tier]

    # Chest bonus: items can come from ahead of the current dungeon level
    level_bonus = container_tier * 2  # T1: +2, T2: +4, ... T5: +10
    effective_level = dungeon_level + level_bonus

    pool = []
    unique_pool = []   # named uniques eligible at this level
    for cls_name in cfg['classes']:
        try:
            for item in load_items(cls_name):
                itier = _item_tier(item)
                if itier > cfg['max_tier']:
                    continue
                if getattr(item, 'container_loot_tier', 'common') == 'legendary' \
                        and not cfg['legendary']:
                    continue
                if item.min_level > max(1, effective_level):
                    continue
                if getattr(item, 'is_unique', False):
                    # Floor-spawn uniques (those carrying peak_floor) — gated
                    # by bell-curve relevance to the effective chest level
                    unique_pool.append(item)
                else:
                    pool.append(item)
        except FileNotFoundError:
            pass

    # weapon/armor/shield commons are template-instantiated, not in the JSON
    # uniques files. Inject a few template-rolled samples per class so chests
    # don't fall through to unique_pool when the JSON-derived common pool is
    # empty for those categories.
    from items import (pick_random_weapon_for_floor,
                        pick_random_armor_for_floor,
                        pick_random_shield_for_floor)
    samples_per_class = max(2, container_tier + 1)
    for cls_name in cfg['classes']:
        if cls_name == 'weapon':
            for _ in range(samples_per_class):
                w = pick_random_weapon_for_floor(effective_level, random)
                if w is not None:
                    pool.append(w)
        elif cls_name == 'armor':
            for _ in range(samples_per_class):
                a = pick_random_armor_for_floor(effective_level, random)
                if a is not None:
                    pool.append(a)
        elif cls_name == 'shield':
            for _ in range(samples_per_class):
                s = pick_random_shield_for_floor(effective_level, random)
                if s is not None:
                    pool.append(s)

    if not pool and not unique_pool:
        return []

    # Bias toward higher-tier items — weight by tier squared, scaled by container tier
    weights = [max(1, _item_tier(i) ** 2) if container_tier >= 3
               else max(1, _item_tier(i)) for i in pool] if pool else []

    unique_chance = cfg.get('unique_chance', 0.0)

    def pick_one():
        # Per-pick coin flip: roll a unique if eligible + lucky
        if unique_pool and random.random() < unique_chance:
            return copy.copy(random.choice(unique_pool))
        if pool:
            return copy.copy(random.choices(pool, weights=weights, k=1)[0])
        # No common pool — guaranteed unique
        return copy.copy(random.choice(unique_pool))

    chosen = [pick_one()]
    chance = container.extra_item_chance
    while chance > 0.05 and random.random() < chance:
        chosen.append(pick_one())
        chance *= 0.40

    return chosen


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
