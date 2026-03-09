import random
from dice import roll

# Fallback multipliers used when the player has no weapon equipped.
_DEFAULT_MULTIPLIERS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]

# Damage type advantage/disadvantage vs monster flags.
# Monster defn can set 'resistances': ['slash'] or 'weaknesses': ['pierce']
def _damage_multiplier(damage_types: list[str], monster) -> float:
    """Return 0.5 for resistance, 1.5 for weakness, 1.0 otherwise.
    If weapon has multiple types, pick the best result across all types."""
    resistances = getattr(monster, 'resistances', [])
    weaknesses  = getattr(monster, 'weaknesses', [])
    mults = []
    for dt in damage_types:
        if dt in weaknesses:
            mults.append(1.5)
        elif dt in resistances:
            mults.append(0.5)
        else:
            mults.append(1.0)
    return max(mults) if mults else 1.0


def player_attack(player, monster, quiz_engine, on_complete, ammo=None):
    """
    Start a math chain quiz for the player attacking a monster.

    on_complete(damage: int, killed: bool, chain: int) is called when the quiz ends.
    Chain 0 (first answer wrong) = MISS (0 damage).
    Uses weapon's base_damage (int) or falls back to rolling weapon.damage (dice string).
    Applies enchant_bonus, ammo damage_bonus, damage type multipliers, and stun chance on hit.
    ammo: optional Ammo item whose damage_bonus is added to base damage.
    """
    weapon = player.weapon

    def _callback(result):
        chain = result.score
        if chain == 0 or monster.is_dead():
            on_complete(0, monster.is_dead(), chain)
            return

        # Base damage: new integer field preferred over legacy dice string
        if weapon and weapon.base_damage:
            base = weapon.base_damage
        elif weapon and weapon.damage:
            base = roll(weapon.damage)
        else:
            base = roll('1d4')

        # Ammo damage bonus (ranged shots only)
        ammo_bonus  = ammo.damage_bonus if ammo else 0
        enchant     = weapon.enchant_bonus if weapon else 0
        multipliers = weapon.chain_multipliers if weapon else _DEFAULT_MULTIPLIERS
        mult        = multipliers[min(chain - 1, len(multipliers) - 1)]

        # Damage type advantage vs monster resistances/weaknesses
        dtype_mult = 1.0
        if weapon:
            dtype_mult = _damage_multiplier(weapon.damage_types, monster)

        damage = max(1, int((base + enchant + ammo_bonus) * mult * dtype_mult))
        actual = monster.take_damage(damage)

        # Stun mechanic (staves only, or any weapon with stunChance > 0)
        stunned = False
        if weapon and weapon.stun_chance > 0 and actual > 0:
            if random.random() < weapon.stun_chance:
                # Monster makes a resistance roll (CON-like — use max_hp as proxy)
                resist_threshold = max(0.1, 1.0 - (monster.max_hp / 200.0))
                if random.random() > resist_threshold:
                    # Stun: refresh rather than stack
                    current = monster.status_effects.get('paralyzed', 0)
                    monster.status_effects['paralyzed'] = max(current, 2)
                    stunned = True

        on_complete(actual, monster.is_dead(), chain, stunned=stunned)

    quiz_engine.start_quiz(
        mode='chain',
        subject='math',
        tier=weapon.quiz_tier if weapon else 1,
        callback=_callback,
        max_chain=weapon.max_chain_length if weapon else None,
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
    )


def can_melee_attack(player, monster) -> bool:
    """Return True if the player's equipped weapon can reach the monster."""
    weapon = player.weapon
    reach = weapon.reach if weapon else 1
    if reach < 15:  # melee or polearm
        dx = abs(player.x - monster.x)
        dy = abs(player.y - monster.y)
        return dx <= reach and dy <= reach and not (dx == 0 and dy == 0)
    return False  # ranged weapons handled separately


def can_ranged_attack(player, monster, dungeon) -> bool:
    """Return True if the player has a ranged weapon, ammo, and line of sight."""
    weapon = player.weapon
    if not weapon or not weapon.requires_ammo:
        return False
    reach = weapon.reach
    dx = abs(player.x - monster.x)
    dy = abs(player.y - monster.y)
    dist = max(dx, dy)
    if dist > reach:
        return False
    # Check ammo in inventory
    ammo_type = weapon.requires_ammo
    has_ammo = any(
        getattr(i, 'ammo_type', None) == ammo_type
        for i in player.inventory
    )
    if not has_ammo:
        return False
    # Line of sight: check no solid tiles block the path (Bresenham)
    return _line_of_sight(player.x, player.y, monster.x, monster.y, dungeon)


def _line_of_sight(x0, y0, x1, y1, dungeon) -> bool:
    """Bresenham line-of-sight check. Returns True if path is clear."""
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x1 > x0 else -1
    sy = 1 if y1 > y0 else -1
    err = dx - dy
    cx, cy = x0, y0
    while True:
        if (cx, cy) != (x0, y0) and (cx, cy) != (x1, y1):
            if not dungeon.is_walkable(cx, cy):
                return False
        if cx == x1 and cy == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            cx += sx
        if e2 < dx:
            err += dx
            cy += sy
    return True
