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
    weaknesses  = list(getattr(monster, 'weaknesses', []))
    # Systemic material bonuses based on monster tags
    tags = getattr(monster, 'tags', [])
    if any(t in ('undead', 'demon') for t in tags):
        if 'silver' not in weaknesses:
            weaknesses.append('silver')
    if 'fey' in tags:
        if 'iron' not in weaknesses:
            weaknesses.append('iron')
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
    weapon = player.ranged_weapon if ammo else player.weapon

    def _callback(result):
        chain = result.score

        # Cow King's Horns (or any armor with chain_bonus): free chain head start
        for slot in getattr(player, 'armor_slots', []):
            if slot and getattr(slot, 'chain_bonus', 0):
                chain += slot.chain_bonus

        # Cursed weapon backlash on miss (Tyrfing)
        if chain == 0:
            if weapon and getattr(weapon, 'cursed_miss_backlash', 0) > 0:
                player.hp -= weapon.cursed_miss_backlash
            on_complete(0, monster.is_dead(), chain)
            return

        if monster.is_dead():
            on_complete(0, True, chain)
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
        # Gram (reforged) ignores all resistances
        dtype_mult = 1.0
        if weapon and getattr(weapon, 'ignore_resistances', False):
            dtype_mult = 1.0  # bypass all resistance/weakness checks
        elif weapon:
            # Include weapon material as a damage type so iron weapons
            # trigger "iron" weakness on fey creatures, etc.
            dtypes = list(weapon.damage_types)
            mat = getattr(weapon, 'material', '').lower()
            if mat and mat not in dtypes:
                dtypes.append(mat)
            # Blessed weapons deal holy damage (effective vs undead/demons)
            if getattr(weapon, 'buc', 'uncursed') == 'blessed' and 'holy' not in dtypes:
                dtypes.append('holy')
            dtype_mult = _damage_multiplier(dtypes, monster)

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
                # Petrify on crit (Harpe)
                if weapon.petrify_on_crit:
                    current_pet = monster.status_effects.get('petrifying', 0)
                    monster.status_effects['petrifying'] = max(current_pet, 3)

        # Beowulf quirk: unarmed attacks deal +5 base damage
        if weapon is None:
            unarmed_bonus = getattr(player, 'quirk_progress', {}).get('beowulf_unarmed_bonus', 0)
            base += unarmed_bonus

        # Weakened status: halve base damage before multipliers
        if getattr(player, 'status_effects', {}).get('weakened', 0):
            base = max(1, base // 2)

        # BUC weapon bonus: blessed +1, cursed -1
        buc_bonus = 0
        if weapon:
            wbuc = getattr(weapon, 'buc', 'uncursed')
            if wbuc == 'blessed':
                buc_bonus = 1
            elif wbuc == 'cursed':
                buc_bonus = -1

        str_factor = 1.0 + max(0, player.STR - 10) * 0.03
        damage = max(1, int((base + enchant + ammo_bonus + buc_bonus) * mult * dtype_mult * str_factor))

        # Empower spell: 3x damage on next hit, then clears
        if player.has_effect('empowered'):
            damage *= 3
            player.status_effects.pop('empowered', None)

        # Dragon scales: massive damage reduction (bypassed by ignore_resistances or player in pit)
        dragon_scales = getattr(monster, 'dragon_scales', 0)
        if dragon_scales > 0 and not getattr(weapon, 'ignore_resistances', False):
            if player.has_effect('in_pit'):
                damage = damage * 4  # devastating underbelly strike from below!
            else:
                damage = max(1, int(damage * (1.0 - dragon_scales)))

        # Sword of Michael vs Abaddon: bonus holy damage
        if weapon and getattr(weapon, 'abaddon_bonus_damage', '') and monster.kind == 'abaddon_destroyer':
            from dice import roll as _ab_roll
            bonus = _ab_roll(weapon.abaddon_bonus_damage)
            damage += bonus

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
                    monster.add_effect('paralyzed', 2)
                    stunned = True

        # Bleed mechanic
        if weapon and weapon.bleed_chance > 0 and actual > 0:
            if random.random() < weapon.bleed_chance:
                monster.add_effect('bleeding', 3)

        # Poison mechanic
        poisoned = False
        if weapon and getattr(weapon, 'poison_chance', 0) > 0 and actual > 0:
            if random.random() < weapon.poison_chance:
                monster.add_effect('poisoned', 5)
                poisoned = True

        # Burn mechanic
        burned = False
        if weapon and getattr(weapon, 'burn_chance', 0) > 0 and actual > 0:
            if random.random() < weapon.burn_chance:
                monster.add_effect('burning', 4)
                burned = True

        # Confuse mechanic (Thyrsus-style)
        confused = False
        if weapon and getattr(weapon, 'confuse_chance', 0) > 0 and actual > 0:
            if random.random() < weapon.confuse_chance:
                monster.add_effect('confused', 4)
                confused = True

        # Lifesteal mechanic (Soul Reaver)
        healed = False
        if weapon and getattr(weapon, 'lifesteal_percent', 0) > 0 and actual > 0:
            heal = max(1, int(actual * weapon.lifesteal_percent))
            player.hp = min(player.max_hp, player.hp + heal)
            healed = True

        # Kill heal mechanic (Excalibur, Achilles's Spear)
        if monster.is_dead() and weapon and getattr(weapon, 'kill_heal_amount', 0) > 0:
            player.hp = min(player.max_hp, player.hp + weapon.kill_heal_amount)
            healed = True

        # Growing power mechanic (Caliburn)
        if monster.is_dead() and weapon and getattr(weapon, 'growing_power', False):
            weapon.kill_count = getattr(weapon, 'kill_count', 0) + 1
            if weapon.kill_count % weapon.kills_to_grow == 0:
                weapon.base_damage += 1

        # Knockback mechanic (handled by caller via return value; flag via on_complete extra)
        knocked = False
        if weapon and weapon.knockback and actual > 0:
            knocked = True

        petrified = crit and weapon and getattr(weapon, 'petrify_on_crit', False)
        on_complete(actual, monster.is_dead(), chain, stunned=stunned, knocked=knocked, crit=crit,
                    poisoned=poisoned, burned=burned, confused=confused, petrified=petrified, healed=healed)

    # Jormungandr quirk: +1 max chain for repeatedly-equipped weapon
    _max_chain = weapon.max_chain_length if weapon else len(_DEFAULT_MULTIPLIERS)
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
        base_seconds=player.get_quiz_timer('math'),
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
    weapon = player.ranged_weapon
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
    """Bresenham line-of-sight check with corner-cutting prevention.
    Returns True if path is clear (no walls, doors, or obstacles)."""
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x1 > x0 else -1
    sy = 1 if y1 > y0 else -1
    err = dx - dy
    cx, cy = x0, y0
    while True:
        if cx == x1 and cy == y1:
            break
        e2 = 2 * err
        step_x = e2 > -dy
        step_y = e2 < dx
        if step_x and step_y:
            # Diagonal step: check BOTH adjacent tiles to prevent corner-cutting.
            # An arrow can't pass through a diagonal gap between two walls.
            adj_x_blocked = not dungeon.is_walkable(cx + sx, cy)
            adj_y_blocked = not dungeon.is_walkable(cx, cy + sy)
            if adj_x_blocked and adj_y_blocked:
                return False  # both corners blocked — no passage
        if step_x:
            err -= dy
            cx += sx
        if step_y:
            err += dx
            cy += sy
        # Check the tile we moved to (skip origin and target)
        if (cx, cy) != (x1, y1):
            if not dungeon.is_walkable(cx, cy):
                return False
    return True


def get_line_tiles(x0, y0, x1, y1) -> list[tuple[int, int]]:
    """Return all tiles on the Bresenham line from (x0,y0) to (x1,y1), excluding origin."""
    tiles = []
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x1 > x0 else -1
    sy = 1 if y1 > y0 else -1
    err = dx - dy
    cx, cy = x0, y0
    while True:
        if cx == x1 and cy == y1:
            if (cx, cy) not in tiles:
                tiles.append((cx, cy))
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            cx += sx
        if e2 < dx:
            err += dx
            cy += sy
        if (cx, cy) != (x0, y0) and (cx, cy) not in tiles:
            tiles.append((cx, cy))
    return tiles


def get_cone_tiles(x0, y0, x1, y1, max_range=6) -> set[tuple[int, int]]:
    """Return tiles in a cone from (x0,y0) in the direction of (x1,y1).

    The cone EXTENDS PAST the target to max_range — fire doesn't stop at
    the first thing it hits. The direction is determined by the target, but
    the cone continues through and beyond it.

    Widening with distance:
      - Distance 1-2: just the center line (width 1)
      - Distance 3-4: center + 1 perpendicular on each side (width 3)
      - Distance 5+:  center + 2 perpendicular on each side (width 5)
    Origin tile is excluded.
    """
    dx, dy = x1 - x0, y1 - y0
    dist = max(abs(dx), abs(dy))
    if dist == 0:
        return set()

    # Calculate direction and perpendicular vectors
    length = (dx * dx + dy * dy) ** 0.5
    if length == 0:
        return set()
    dir_x = dx / length
    dir_y = dy / length
    perp_x = -dir_y
    perp_y = dir_x

    # Extend the line PAST the target to max_range by projecting further
    # along the same direction
    far_x = x0 + round(dir_x * max_range)
    far_y = y0 + round(dir_y * max_range)
    line = get_line_tiles(x0, y0, far_x, far_y)

    result = set()
    for i, (tx, ty) in enumerate(line):
        tile_dist = i + 1
        if tile_dist > max_range:
            break
        result.add((tx, ty))

        # Determine spread at this distance
        if tile_dist >= 5:
            spread = 2
        elif tile_dist >= 3:
            spread = 1
        else:
            spread = 0

        for s in range(1, spread + 1):
            result.add((tx + round(perp_x * s), ty + round(perp_y * s)))
            result.add((tx - round(perp_x * s), ty - round(perp_y * s)))

    return result
