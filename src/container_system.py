"""
Container / lockpicking system.

Flow:
  attempt_lockpick(player, container, quiz_engine, dungeon, monsters, callback)
    → starts economics threshold quiz
    → on success: opens container, generates loot, returns items + gold
    → on failure: triggers trap (first failure only), damages lockpick,
                  30% chance to alert nearby monsters

Mimic check:
  check_for_mimic(player, container, monsters)
    → if container.is_mimic: spawns mimic monster, returns True
    → else: returns False
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
      status: 'no_lockpick' | 'opened' | 'failed'
      loot:   list of Item instances (empty on failure)
      gold:   int (0 on failure)
      messages: list of (text, type) pairs
    """
    charges = getattr(player, 'lockpick_charges', 0)
    if charges <= 0:
        on_complete({'status': 'no_lockpick', 'loot': [], 'gold': 0,
                     'messages': [('You have no lockpick charges!', 'warning')]})
        return

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
    )


def check_for_mimic(player, container, monsters) -> bool:
    """
    Attack a container to check for a mimic.
    If it is a mimic, spawn the mimic monster and return True.
    Returns False if it's a normal container.
    """
    if not container.is_mimic:
        return False

    _spawn_mimic(container, monsters)
    return True


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _handle_success(player, container, dungeon, on_complete):
    messages = []

    # Consume one lockpick charge
    player.lockpick_charges = max(0, player.lockpick_charges - 1)
    remaining = player.lockpick_charges
    messages.append((f'Pick used. {remaining} charge{"s" if remaining != 1 else ""} remaining.', 'info'))

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

    # Consume one lockpick charge on failure
    player.lockpick_charges = max(0, player.lockpick_charges - 1)
    remaining = player.lockpick_charges
    messages.append((f'Pick damaged. {remaining} charge{"s" if remaining != 1 else ""} remaining.', 'info'))

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
    effect_ch  = float(trap.get('effect_chance', 0.5))

    if effect and random.random() < effect_ch:
        applied = player.add_effect(effect, effect_dur)
        if applied:
            messages.append((f'You are {effect}!', 'danger'))


def _alert_nearby(player, dungeon, monsters) -> bool:
    """Wake up monsters within 8 tiles. Returns True if any were alerted."""
    from status_effects import apply_effect
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
# allowed, and whether legendary (containerLootTier='legendary') items can appear.
_TIER_LOOT_CFG: dict[int, dict] = {
    1: {'classes': ['weapon', 'armor', 'ammo'],
        'max_tier': 2, 'legendary': False},
    2: {'classes': ['weapon', 'armor', 'ammo', 'accessory'],
        'max_tier': 3, 'legendary': False},
    3: {'classes': ['weapon', 'armor', 'accessory', 'scroll', 'wand'],
        'max_tier': 4, 'legendary': False},
    4: {'classes': ['weapon', 'armor', 'accessory', 'scroll', 'wand'],
        'max_tier': 5, 'legendary': False},
    5: {'classes': ['weapon', 'armor', 'accessory', 'scroll', 'wand'],
        'max_tier': 5, 'legendary': True},
}


def _item_tier(item) -> int:
    """Return the effective quiz/difficulty tier of an item (1–5)."""
    return int(getattr(item, 'quiz_tier',
               getattr(item, 'tier', 1)))


def _generate_loot(container, dungeon_level: int) -> list:
    """
    Pick 1+ items whose tier and class match the container's tier.
    Higher-tier containers draw from more categories, allow higher-tier
    items, and bias toward the best items in the pool.
    """
    import copy
    from items import load_items

    container_tier = max(1, min(5, getattr(container, 'tier', 1)))
    cfg = _TIER_LOOT_CFG[container_tier]

    pool = []
    for cls_name in cfg['classes']:
        try:
            for item in load_items(cls_name):
                itier = _item_tier(item)
                # Skip items above the allowed tier ceiling
                if itier > cfg['max_tier']:
                    continue
                # Legendary items only in tier-5 containers
                if getattr(item, 'container_loot_tier', 'common') == 'legendary' \
                        and not cfg['legendary']:
                    continue
                # Must have spawned by this dungeon level
                if item.min_level > max(1, dungeon_level):
                    continue
                pool.append(item)
        except FileNotFoundError:
            pass

    if not pool:
        return []

    # Bias toward higher-tier items in higher-tier containers (weight by tier²)
    if container_tier >= 3:
        weights = [_item_tier(i) ** 2 for i in pool]
    else:
        weights = [1] * len(pool)

    def pick_one():
        return copy.copy(random.choices(pool, weights=weights, k=1)[0])

    chosen = [pick_one()]
    chance = container.extra_item_chance
    while chance > 0.05 and random.random() < chance:
        chosen.append(pick_one())
        chance *= 0.40

    return chosen


def _spawn_mimic(container, monsters: list):
    """Replace a mimic container with a live mimic monster."""
    import json, os
    from monster import Monster

    from paths import data_path
    monsters_path = data_path('data', 'monsters.json')
    with open(monsters_path, encoding='utf-8') as f:
        all_defs = json.load(f)

    defn = all_defs.get('mimic')
    if defn is None:
        return

    mimic = Monster({**defn, 'id': 'mimic'}, container.x, container.y)
    monsters.append(mimic)
