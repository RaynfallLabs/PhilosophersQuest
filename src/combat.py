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
        # Musashi quirk: chain-1 uses 2nd multiplier instead of weakest
        if chain == 1 and getattr(player, 'quirk_progress', {}).get('musashi_active'):
            mult = multipliers[min(1, len(multipliers) - 1)]

        # Damage type advantage vs monster resistances/weaknesses
        dtype_mult = 1.0
        if weapon:
            dtype_mult = _damage_multiplier(weapon.damage_types, monster)

        # Shield bypass: ignore_shield weapons deal full damage through monster's shielded effect
        if not (weapon and weapon.ignore_shield):
            if monster.has_effect('shielded'):
                dtype_mult *= 0.5

        # Critical hit: if weapon has crit_multiplier and chain hits max, apply bonus
        crit = False
        if weapon and weapon.crit_multiplier > 1.0:
            max_c = weapon.max_chain_length or len(weapon.chain_multipliers)
            if chain >= max_c:
                mult *= weapon.crit_multiplier
                crit = True

        # Beowulf quirk: unarmed attacks deal +5 base damage
        if weapon is None:
            unarmed_bonus = getattr(player, 'quirk_progress', {}).get('beowulf_unarmed_bonus', 0)
            base += unarmed_bonus

        # Weakened status: halve base damage before multipliers
        if getattr(player, 'status_effects', {}).get('weakened', 0):
            base = max(1, base // 2)

        str_factor = 1.0 + max(0, player.STR - 10) * 0.03
        damage = max(1, int((base + enchant + ammo_bonus) * mult * dtype_mult * str_factor))
        actual = monster.take_damage(damage)

        # Stun mechanic (staves only, or any weapon with stunChance > 0)
        stunned = False
        if weapon and weapon.stun_chance > 0 and actual > 0:
            if random.random() < weapon.stun_chance:
                # Monster makes a resistance roll: bigger monsters resist more.
                # threshold = hp/300 clamped [0.05, 0.95]; roll must BEAT threshold to stun.
                # e.g. 30 HP -> 90% chance, 150 HP -> 50%, 300 HP+ -> 5%
                resist_threshold = min(0.95, max(0.05, monster.max_hp / 300.0))
                if random.random() > resist_threshold:
                    current = monster.status_effects.get('paralyzed', 0)
                    monster.status_effects['paralyzed'] = max(current, 2)
                    stunned = True

        # Bleed mechanic
        if weapon and weapon.bleed_chance > 0 and actual > 0:
            if random.random() < weapon.bleed_chance:
                monster.status_effects['bleeding'] = monster.status_effects.get('bleeding', 0) + 3

        # Knockback mechanic (handled by caller via return value; flag via on_complete extra)
        knocked = False
        if weapon and weapon.knockback and actual > 0:
            knocked = True

        on_complete(actual, monster.is_dead(), chain, stunned=stunned, knocked=knocked, crit=crit)

    # Jormungandr quirk: +1 max chain for repeatedly-equipped weapon
    _max_chain = weapon.max_chain_length if weapon else None
    if _max_chain and weapon:
        if getattr(player, 'quirk_progress', {}).get('jormungandr_weapon_id') == weapon.id:
            _max_chain += 1

    quiz_engine.start_quiz(
        mode='chain',
        subject='math',
        tier=weapon.quiz_tier if weapon else 1,
        callback=_callback,
        max_chain=_max_chain,
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
        extra_seconds=getattr(player, 'get_quiz_extra_seconds', lambda s: 0)('math'),
    )


def apply_knockback(player, monster, dungeon, monsters=None):
    """Push monster one tile away from the player. No-ops if tile is blocked or occupied."""
    dx = monster.x - player.x
    dy = monster.y - player.y
    # Normalize to direction
    nx = (1 if dx > 0 else -1) if dx != 0 else 0
    ny = (1 if dy > 0 else -1) if dy != 0 else 0
    tx, ty = monster.x + nx, monster.y + ny
    if not dungeon.is_walkable(tx, ty):
        return
    if monsters and any(m is not monster and m.alive and m.x == tx and m.y == ty
                        for m in monsters):
        return
    monster.x, monster.y = tx, ty


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
    reach = weapon.reach + max(0, player.PER - 10) // 3
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
