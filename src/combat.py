import random
from dice import roll

# Shares, not floor multipliers (floor_curve: LORE, NOT FLOOR).
RANGED_STAT_SHARE = 0.03      # of a bow's own base, per four points of PER / STR over 10
LAST_STAND_SHARE = 0.15       # Helm of Leonidas, below a fifth of health
ENCIRCLED_SHARE = 0.04        # Cuirass of Hannibal, per adjacent enemy when surrounded
GROWING_SHARE = 0.02          # Caliburn: of its forged base, each time it grows
from geom import is_at_tile

# Fallback multipliers used when the player has no weapon equipped.
# Bare-hand chain table. Caps at the universal 5-chain like every common
# template; values are deliberately weaker than the weakest template
# (shortsword peak 2.0x) so unarmed combat is the LAST resort, not a
# stronger alternative. Was incorrectly 8-entry with 5.0x peak — caused
# unarmed players to out-chain wielded weapons. Fixed 2026-05-19.
_DEFAULT_MULTIPLIERS = [0.3, 0.5, 0.7, 0.9, 1.2]


# ---------------------------------------------------------------------------
# Weapon class-mechanic display info
# ---------------------------------------------------------------------------
# Maps a weapon's `class_mechanic` id -> (short name, plain-English description).
# Surfaced in the Kit screen (name only) and the Examine panel (name + desc) so
# players can see what their weapon actually does. Both common weapons (mechanic
# applied from their class template) and uniques carry `class_mechanic`, so this
# single map serves every weapon. Descriptions authored from the weapon
# templates' `class_mechanic_desc`; kept ASCII-clean for safe rendering.
CLASS_MECHANIC_INFO = {
    'backstab':                ('Backstab',
        'x2 damage if the target is unaware of you.'),
    'bleed_at_max':            ('Bleed',
        'On chain rung 3+, inflicts bleeding (1d4/turn for 3 turns).'),
    'cleave_at_max':           ('Cleave',
        'At max chain, on a kill: cleave damage to one adjacent foe.'),
    'cleave_at_max_plus_bleed':('Cleave + Bleed',
        'At max chain: cleave one adjacent foe and apply bleed (1d6/turn for 3).'),
    'concussion_at_max':       ('Concussion',
        'At max chain: 35% chance to confuse the target for 2 turns. Cheap, '
        'abundant, and never breaks on harvest.'),
    'defensive_parry':         ('Parry',
        'At max chain: gain +2 AC for 2 turns -- the staff turns each riposte '
        'into shelter.'),
    'finesse_dex':             ('Finesse',
        'Uses DEX instead of STR for the damage bonus.'),
    'free_stones':             ('Free Stones',
        'At max chain: 25% chance to ricochet to an adjacent enemy. Ammo is '
        'weightless and gathered automatically.'),
    'ignores_all_armor':       ('Armor-Piercing',
        'Ignores ALL armor AC. Single-shot reload; the slowest weapon.'),
    'ignores_half_armor':      ('Half Armor-Pierce',
        'Ignores half of the target armor AC. Single-shot reload between volleys.'),
    'ignores_shield':          ('Shield-Bypass',
        'Ignores the shield AC bonus -- the flail wraps around defenses.'),
    'master_strike':           ('Master Strike',
        'At chain 3+, every hit treats the target AC as 1 lower -- the '
        'longsword Meisterhau.'),
    'quick_riposte':           ('Riposte',
        'At max chain: if struck in melee next turn, free counter-attack at '
        '0.85x damage.'),
    'rapid_shot_at_max':       ('Rapid Shot',
        'At max chain: fire a follow-up arrow at half damage on the same target.'),
    'reach_2':                 ('Reach 2',
        'Strike foes 2 tiles away; at max chain, hits all enemies in the line.'),
    'str_bonus_range_7':       ('Range 7 (STR)',
        'Range 7 tiles; adds your STR modifier to the damage.'),
    'stun_at_max':             ('Stun',
        'On chain rung 3+, 20% chance to stun for 1 turn.'),
    'stun_knockdown_at_max':   ('Stun + Knockdown',
        'At chain rung 4+: stun and knock down (the target loses 2 turns).'),
    'versatile':               ('Versatile',
        '+20% damage when wielded two-handed (no shield).'),
    'anti_heavy_at_max':       ('Anti-Armor',
        'At max chain: +50% damage vs heavy-armored monsters.'),
    'armor_pierce_at_max':     ('Pierce at Max',
        "At max chain, ignores 50% of the target's armor."),
    # Unique-only mechanics (no class template -- carried by specific artifacts).
    'guaranteed_hit':          ('Never Miss',
        'The weapon never misses -- even a failed quiz still lands a minimum hit.'),
    'returning_blow':          ('Returning Blow',
        'At max chain the blow rebounds on you for half damage -- swing too '
        'hard and you pay the price.'),
}


def class_mechanic_info(mech_id):
    """Return (short_name, description) for a weapon class-mechanic id.

    Falls back to a humanized id with an empty description for any mechanic not
    in the table, so a weapon's signature ability never renders blank. Returns
    None only for a falsy id.
    """
    if not mech_id:
        return None
    info = CLASS_MECHANIC_INFO.get(mech_id)
    if info:
        return info
    name = mech_id.replace('_at_max', '').replace('_', ' ').title()
    return (name, '')


def _tag_match(monster, tag: str) -> bool:
    """True if `tag` is in the monster's tags (or matches its kind)."""
    if tag == 'all':
        return True
    mtags = set(getattr(monster, 'tags', []))
    if tag in mtags:
        return True
    return getattr(monster, 'kind', '') == tag


# ---------------------------------------------------------------------------
# Chain combat v2 (v2.14.0): per-class chain-special dispatch
# ---------------------------------------------------------------------------
# Universal 5/10/15/20 chain thresholds fire class-specific effects.
# See docs/design/weapon_specials_v2_14.md for the full table + design intent.
# Highest-threshold wins — chain 20 does NOT stack with chain 15 effects.
# ---------------------------------------------------------------------------

def _chain_special_tier(chain: int) -> int:
    """Return the highest chain-special threshold this chain qualifies for.
    0 if below 5 (no special)."""
    if chain >= 20:
        return 20
    if chain >= 15:
        return 15
    if chain >= 10:
        return 10
    if chain >= 5:
        return 5
    return 0


def _weapon_key(weapon) -> str:
    """Return the class key used for chain-special dispatch. Distinguishes
    2H from 1H variants of the same base class (sword/axe/blunt). Falls back
    to 'fist' for unarmed.

    Common material x template weapons carry `weapon_class` values that don't
    match the specials-table keys 1:1: mace / warhammer / flail / club / maul /
    quarterstaff all use `weapon_class='blunt'`, and glaive uses
    `weapon_class='polearm'`. Without the aliases below every common
    hafted-blunt weapon (mace, warhammer, maul, ...) got ZERO chain specials
    because it fell through to a `blunt` key with no entry in
    _apply_chain_class_post_damage. Fixed 2026-09-13 (v2.15.0).
    """
    if weapon is None:
        return 'fist'
    wc = (getattr(weapon, 'weapon_class', 'fist') or 'fist').lower()
    two_handed = bool(getattr(weapon, 'two_handed', False))
    # Weapon id is `<material>_<template_id>` for common weapons; uniques set
    # their own id. Used to distinguish blunt subtypes (quarterstaff -> staff).
    wid = (getattr(weapon, 'id', '') or '').lower()
    name = (getattr(weapon, 'name', '') or '').lower()

    # ---- SWORDS ------------------------------------------------------------
    if wc == 'sword':
        return '2h_sword' if two_handed else 'sword'
    if wc == 'zweihander':
        return '2h_sword'
    # Scimitar & morningstar fold under 1h_sword / mace for specials by design.
    if wc == 'scimitar':
        return 'sword'
    if wc == 'morningstar':
        return 'mace'

    # ---- AXES --------------------------------------------------------------
    if wc == 'axe':
        return '2h_axe' if two_handed else 'axe'

    # ---- BLUNT (mace / warhammer / flail / club / maul / quarterstaff) -----
    # All the common hafted-blunt templates share `weapon_class='blunt'`.
    # Disambiguate by hands + template identity so each routes to the right
    # entry in the specials ladder.
    if wc == 'blunt':
        # Quarterstaff -> staff (the wandering monk's reach-2 haft). Detect
        # by id/name so it also catches uniques that borrow the shape.
        if 'quarterstaff' in wid or wid.endswith('staff') or 'staff' in name:
            return 'staff'
        if two_handed:
            # 2H blunt hafted weapon (maul, great-hammer): area-stun ladder.
            return '2h_warhammer'
        # 1H blunt (mace, warhammer, flail, club) -> mace ladder.
        return 'mace'
    # Explicit weapon_class aliases (uniques and hand-authored data may set
    # these directly rather than the collapsed 'blunt' class).
    if wc == 'warhammer':
        return '2h_warhammer' if two_handed else 'mace'
    if wc == 'club':
        return 'mace'
    if wc == 'flail':
        return 'mace'
    if wc == 'hammer':
        return '2h_warhammer' if two_handed else 'mace'
    if wc == 'maul':
        return '2h_warhammer'
    if wc == 'staff':
        return 'staff'

    # ---- POLEARMS (glaive / halberd / spear) -------------------------------
    if wc == 'polearm':
        # Only glaive currently uses `weapon_class='polearm'` as a template;
        # uniques set `class='halberd'` / `class='spear'` directly. Route by
        # id/name so a future halberd template also lands correctly.
        if 'halberd' in wid or 'halberd' in name:
            return 'halberd'
        if 'spear' in wid or 'spear' in name:
            return 'spear'
        # Default polearm -> glaive (sweeping arc ladder).
        return 'glaive'
    if wc == 'halberd':
        return 'halberd'
    if wc == 'spear':
        return 'spear'
    if wc == 'glaive':
        return 'glaive'

    # ---- RANGED ------------------------------------------------------------
    # Templates use explicit weapon_class 'bow' / 'crossbow' / 'sling', so
    # those fall through to `return wc` below. 'ranged' is a legacy catch-all
    # that some old uniques used; split it by ammo type.
    if wc == 'ranged':
        ammo_type = (getattr(weapon, 'requires_ammo', '') or '').lower()
        if 'bolt' in ammo_type:
            return 'crossbow'
        if getattr(weapon, 'infinite_ammo', False):
            return 'sling'
        return 'bow'

    # ---- DAGGER / BOW / CROSSBOW / SLING / FIST / etc. --------------------
    # These map 1:1 already.
    return wc


# Which class + chain-tier combos should bypass damage reduction on this hit
# (before dragon_scales, before shielded's 0.5x, resistance clamped to >= 1.0).
_BYPASS_DR_TIERS = {
    'sword':     {10, 15, 20},     # 1h sword: master strike (C10), blade_flow-driven at 15/20
    '1h_sword':  {10, 15, 20},     # alias if the key generator ever produces it
    'spear':     {10, 15, 20},     # pierce through armor
    'bow':       {15, 20},         # piercing shot
    'crossbow':  {5, 10, 15, 20},  # bolts always punch through
    'mace':      {20},             # shattering blow
    'halberd':   set(),            # halberd C20 keeps sunder, does NOT bypass DR (design pass)
}


def _chain_pre_damage(weapon, chain: int) -> tuple[float, bool]:
    """Pre-damage class chain special: (damage multiplier, bypasses damage
    reduction?). Bow C20 hits the vitals for x2; the tiers in
    _BYPASS_DR_TIERS punch through shields, scales and resistances.
    Changes nothing: strike_damage sets the one-shot _chain_bypass_dr flag
    itself on a real blow, and the Strike Now preview asks the same."""
    tier = _chain_special_tier(chain)
    if tier == 0:
        return 1.0, False
    key = _weapon_key(weapon)
    bypass = tier in _BYPASS_DR_TIERS.get(key, ())
    return (2.0 if key == 'bow' and tier == 20 else 1.0), bypass


def _dice_mean(notation: str) -> int:
    """Average of a dice string ('2d6+3' -> 10), for the preview."""
    import re as _re
    m = _re.fullmatch(r'(\d*)d(\d+)([+-]\d+)?', str(notation).strip().lower().replace(' ', ''))
    if not m:
        return roll(notation)
    n = int(m.group(1) or 1)
    sides = int(m.group(2))
    return int(round(n * (sides + 1) / 2.0)) + int(m.group(3) or 0)


# --- Post-damage class-chain-special applications ---------------------------
# Each entry is a callable (player, monster, weapon, chain, monsters, dungeon)
# invoked AFTER the hit's damage lands on the primary target. It applies
# statuses to the target, AoE damage to nearby monsters, and player buffs
# per the design doc's class ladder.
# ---------------------------------------------------------------------------

def _max_status(monster, effect: str, duration: int):
    """Apply a status, taking the max of any existing duration. A stun or
    other hold on a named foe goes through its cap and post-hold grace
    (Monster.hold, call 12)."""
    if monster is None or not monster.alive:
        return
    if hasattr(monster, 'hold'):
        monster.hold(effect, duration)
        return
    cur = int(monster.status_effects.get(effect, 0) or 0)
    monster.status_effects[effect] = max(cur, int(duration))


def _adjacent_monsters(player, monsters, radius: int = 1, exclude=None):
    """Return alive monsters within Chebyshev `radius` of the player,
    excluding the given monster and non-alive."""
    px, py = player.x, player.y
    out = []
    for m in monsters or []:
        if not getattr(m, 'alive', False):
            continue
        if exclude is not None and m is exclude:
            continue
        if abs(m.x - px) <= radius and abs(m.y - py) <= radius \
                and not (m.x == px and m.y == py):
            out.append(m)
    return out


def _player_max_status(player, effect: str, duration: int):
    """Apply a player-side status, keeping the max duration."""
    cur = int(player.status_effects.get(effect, 0) or 0)
    player.status_effects[effect] = max(cur, int(duration))


def _player_stack(player, effect: str, add_stacks: int):
    """Add stacks to a stack-consumed player buff (blade_flow). Ceiling at 10
    stacks to prevent runaway."""
    cur = int(player.status_effects.get(effect, 0) or 0)
    player.status_effects[effect] = min(10, cur + int(add_stacks))


def _apply_chain_class_post_damage(player, monster, weapon, chain: int,
                                    monsters, dungeon, actual: int) -> dict:
    """Post-damage hook. Applies primary-target statuses, AoE damage/statuses,
    and player buffs per the class chain-special ladder. Returns a dict of
    side-effects the on_complete callback can surface:
      {'aoe_hits': [(monster, dmg), ...], 'aoe_status': [effect_name],
       'special_msg': str or None}
    Called only when the strike actually connected (chain >= 1); safe to
    call with chain < 5 (no-ops).
    """
    result = {'aoe_hits': [], 'aoe_status': [], 'special_msg': None}
    tier = _chain_special_tier(chain)
    if tier == 0:
        return result
    key = _weapon_key(weapon)

    # Cached primary damage for AoE falloff (0.4x-0.7x of primary is common).
    def _aoe_dmg(mult: float) -> int:
        return max(1, int(actual * mult))

    # -----------------------------------------------------------------
    # FIST — pressure points, chi
    # -----------------------------------------------------------------
    if key == 'fist':
        if tier == 5:
            _max_status(monster, 'slowed', 2)
        elif tier == 10:
            _max_status(monster, 'sundered', 3)
        elif tier == 15:
            _max_status(monster, 'deep_wound', 3)
            _max_status(monster, 'bleeding', 5)
        elif tier == 20:
            _max_status(monster, 'stunned', 3)
            _max_status(monster, 'deep_wound', 5)
            _max_status(monster, 'bleeding', 8)
        return result

    # -----------------------------------------------------------------
    # RAPIER — setup + counterstrike
    # -----------------------------------------------------------------
    if key == 'rapier':
        if tier == 5:
            _max_status(monster, 'bleeding', 3)
        elif tier == 10:
            _max_status(monster, 'sundered', 3)
            _max_status(monster, 'bleeding', 5)
        elif tier == 15:
            _max_status(monster, 'sundered', 5)
            _max_status(monster, 'bleeding', 8)
            _player_max_status(player, 'melee_dmg_reduction', 2)
        elif tier == 20:
            _max_status(monster, 'sundered', 8)
            _max_status(monster, 'bleeding', 10)
            _player_max_status(player, 'melee_dmg_reduction', 4)
        return result

    # -----------------------------------------------------------------
    # STAFF — trip + self-sustain
    # -----------------------------------------------------------------
    if key == 'staff':
        if tier == 5:
            _max_status(monster, 'slowed', 2)
        elif tier == 10:
            for m in _adjacent_monsters(player, monsters):
                _max_status(m, 'slowed', 2)
        elif tier == 15:
            _player_max_status(player, 'melee_dmg_reduction', 3)
            player.hp = min(player.max_hp, player.hp + max(1, player.max_hp // 7))  # ~15%
        elif tier == 20:
            for m in _adjacent_monsters(player, monsters):
                _max_status(m, 'slowed', 3)
            _player_max_status(player, 'melee_dmg_reduction', 3)
            player.hp = min(player.max_hp, player.hp + max(1, player.max_hp // 7))
            player.mp = min(player.max_mp, player.mp + max(1, player.max_mp // 10))
        return result

    # -----------------------------------------------------------------
    # DAGGER — DoT stacker
    # -----------------------------------------------------------------
    if key == 'dagger':
        if tier == 5:
            _max_status(monster, 'bleeding', 4)
        elif tier == 10:
            _max_status(monster, 'deep_wound', 3)
        elif tier == 15:
            _max_status(monster, 'poisoned', 6)
            _max_status(monster, 'bleeding', 6)
        elif tier == 20:
            _max_status(monster, 'ruptured', 5)
            _max_status(monster, 'poisoned', 8)
            _max_status(monster, 'bleeding', 10)
        return result

    # -----------------------------------------------------------------
    # 1H SWORD — reliability, blade_flow
    # -----------------------------------------------------------------
    if key == 'sword':
        if tier == 5:
            _max_status(monster, 'bleeding', 3)
        # tier 10: bypass DR handled pre-damage — nothing to add here.
        elif tier == 15:
            _player_stack(player, 'blade_flow', 3)
            _player_max_status(player, 'melee_dmg_reduction', 3)
        elif tier == 20:
            _player_stack(player, 'blade_flow', 4)
            _player_max_status(player, 'melee_dmg_reduction', 3)
        return result

    # -----------------------------------------------------------------
    # BOW — precision, eye-shot, vitals
    # -----------------------------------------------------------------
    if key == 'bow':
        if tier == 5:
            _max_status(monster, 'bleeding', 3)
        elif tier == 10:
            _max_status(monster, 'blinded', 4)
        elif tier == 20:
            _max_status(monster, 'blinded', 6)
            _max_status(monster, 'bleeding', 8)
        # tier 15 and 20 also bypass DR (handled pre-damage). tier 20 hits
        # vitals for x2 damage (also handled pre-damage).
        return result

    # -----------------------------------------------------------------
    # 1H AXE — bleed + broken limb + cleave
    # -----------------------------------------------------------------
    if key == 'axe':
        if tier == 5:
            _max_status(monster, 'bleeding', 4)
        elif tier == 10:
            _max_status(monster, 'sundered', 3)
        elif tier == 15:
            adj = _adjacent_monsters(player, monsters, exclude=monster)
            if adj:
                target = adj[0]
                d = _aoe_dmg(0.5)
                target.take_damage(d)
                result['aoe_hits'].append((target, d))
                _max_status(target, 'bleeding', 4)
            _max_status(monster, 'bleeding', 4)
        elif tier == 20:
            adj = _adjacent_monsters(player, monsters, exclude=monster)
            hits = 0
            for m in adj:
                d = _aoe_dmg(0.5)
                m.take_damage(d)
                result['aoe_hits'].append((m, d))
                _max_status(m, 'bleeding', 8)
                _max_status(m, 'sundered', 5)
                hits += 1
            _max_status(monster, 'bleeding', 8)
            _max_status(monster, 'sundered', 5)
            regen_pct = min(15, hits * 5)
            if regen_pct > 0:
                player.hp = min(player.max_hp,
                                player.hp + max(1, player.max_hp * regen_pct // 100))
        return result

    # -----------------------------------------------------------------
    # MACE — armor_crack, stun
    # -----------------------------------------------------------------
    if key == 'mace':
        import random as _rng
        if tier == 5:
            if _rng.random() < 0.40:
                _max_status(monster, 'stunned', 1)
        elif tier == 10:
            _max_status(monster, 'armor_crack', 5)
        elif tier == 15:
            _max_status(monster, 'stunned', 2)
            _max_status(monster, 'armor_crack', 8)
        elif tier == 20:
            _max_status(monster, 'stunned', 3)
            _max_status(monster, 'armor_crack', 10)
            # bypass_dr handled pre-damage for tier 20
        return result

    # -----------------------------------------------------------------
    # 2H WARHAMMER — area stun
    # -----------------------------------------------------------------
    if key == '2h_warhammer':
        if tier == 5:
            _max_status(monster, 'stunned', 2)
        elif tier == 10:
            _max_status(monster, 'stunned', 3)
            for m in _adjacent_monsters(player, monsters, exclude=monster):
                _max_status(m, 'stunned', 1)
        elif tier == 15:
            for m in _adjacent_monsters(player, monsters, radius=2):
                _max_status(m, 'stunned', 1)
                _max_status(m, 'armor_crack', 5)
        elif tier == 20:
            for m in _adjacent_monsters(player, monsters, radius=2):
                _max_status(m, 'stunned', 1)
                _max_status(m, 'armor_crack', 5)
                d = _aoe_dmg(0.4)
                if m is not monster:
                    m.take_damage(d)
                    result['aoe_hits'].append((m, d))
        return result

    # -----------------------------------------------------------------
    # SPEAR — pierce, impale
    # -----------------------------------------------------------------
    if key == 'spear':
        if tier == 5:
            _max_status(monster, 'bleeding', 3)
        elif tier == 15 or tier == 20:
            # Pierce logic: hit tile behind target (in line from player -> target)
            dx = 0 if monster.x == player.x else (1 if monster.x > player.x else -1)
            dy = 0 if monster.y == player.y else (1 if monster.y > player.y else -1)
            reach = 1 if tier == 15 else 2
            for step in range(1, reach + 1):
                bx, by = monster.x + dx * step, monster.y + dy * step
                for m in monsters or []:
                    if (getattr(m, 'alive', False) and m.x == bx and m.y == by
                            and m is not monster):
                        falloff = 0.6 if tier == 15 else 0.5
                        d = _aoe_dmg(falloff)
                        m.take_damage(d)
                        result['aoe_hits'].append((m, d))
                        _max_status(m, 'bleeding', 8 if tier == 20 else 5)
                        break
            _max_status(monster, 'bleeding', 8 if tier == 20 else 5)
            if tier == 20:
                _max_status(monster, 'impaled', 3)
        return result

    # -----------------------------------------------------------------
    # HALBERD — line pierce + sunder
    # -----------------------------------------------------------------
    if key == 'halberd':
        if tier == 5:
            _max_status(monster, 'bleeding', 3)
        elif tier == 10:
            _max_status(monster, 'sundered', 2)
            _max_status(monster, 'bleeding', 5)
        elif tier == 15 or tier == 20:
            dx = 0 if monster.x == player.x else (1 if monster.x > player.x else -1)
            dy = 0 if monster.y == player.y else (1 if monster.y > player.y else -1)
            reach = 1 if tier == 15 else 2
            for step in range(1, reach + 1):
                bx, by = monster.x + dx * step, monster.y + dy * step
                for m in monsters or []:
                    if getattr(m, 'alive', False) and m.x == bx and m.y == by \
                            and m is not monster:
                        d = _aoe_dmg(0.6)
                        m.take_damage(d)
                        result['aoe_hits'].append((m, d))
                        _max_status(m, 'bleeding', 5 if tier == 15 else 8)
                        _max_status(m, 'sundered', 3 if tier == 15 else 5)
                        break
            _max_status(monster, 'bleeding', 5 if tier == 15 else 8)
            _max_status(monster, 'sundered', 3 if tier == 15 else 5)
        return result

    # -----------------------------------------------------------------
    # GLAIVE — sweeping arc + bleed field
    # -----------------------------------------------------------------
    if key == 'glaive':
        if tier == 5:
            adj = _adjacent_monsters(player, monsters, exclude=monster)
            if adj:
                d = _aoe_dmg(0.7)
                adj[0].take_damage(d)
                result['aoe_hits'].append((adj[0], d))
        elif tier == 10:
            for m in _adjacent_monsters(player, monsters, exclude=monster)[:2]:
                d = _aoe_dmg(0.6)
                m.take_damage(d)
                result['aoe_hits'].append((m, d))
                _max_status(m, 'bleeding', 3)
            _max_status(monster, 'bleeding', 3)
        elif tier == 15:
            for m in _adjacent_monsters(player, monsters, radius=2, exclude=monster):
                d = _aoe_dmg(0.5)
                m.take_damage(d)
                result['aoe_hits'].append((m, d))
                _max_status(m, 'bleeding', 5)
            _max_status(monster, 'bleeding', 5)
        elif tier == 20:
            for m in _adjacent_monsters(player, monsters, radius=2, exclude=monster):
                d = _aoe_dmg(0.5)
                m.take_damage(d)
                result['aoe_hits'].append((m, d))
                _max_status(m, 'bleeding', 8)
                _max_status(m, 'slowed', 3)
            _max_status(monster, 'bleeding', 8)
            _max_status(monster, 'slowed', 3)
        return result

    # -----------------------------------------------------------------
    # 2H SWORD — cinematic sweep
    # -----------------------------------------------------------------
    if key == '2h_sword':
        if tier == 5:
            adj = _adjacent_monsters(player, monsters, exclude=monster)
            if adj:
                d = _aoe_dmg(0.7)
                adj[0].take_damage(d)
                result['aoe_hits'].append((adj[0], d))
        elif tier == 10:
            for m in _adjacent_monsters(player, monsters, exclude=monster)[:2]:
                d = _aoe_dmg(0.6)
                m.take_damage(d)
                result['aoe_hits'].append((m, d))
        elif tier == 15:
            for m in _adjacent_monsters(player, monsters, exclude=monster):
                d = _aoe_dmg(0.5)
                m.take_damage(d)
                result['aoe_hits'].append((m, d))
                _max_status(m, 'bleeding', 4)
            _max_status(monster, 'bleeding', 4)
        elif tier == 20:
            for m in _adjacent_monsters(player, monsters, radius=2, exclude=monster):
                d = _aoe_dmg(0.5)
                m.take_damage(d)
                result['aoe_hits'].append((m, d))
                _max_status(m, 'bleeding', 8)
            _max_status(monster, 'bleeding', 8)
            _player_stack(player, 'blade_flow', 3)
        return result

    # -----------------------------------------------------------------
    # 2H AXE — brutal cleave + kill-chain
    # -----------------------------------------------------------------
    if key == '2h_axe':
        if tier == 5:
            adj = _adjacent_monsters(player, monsters, exclude=monster)
            if adj:
                d = _aoe_dmg(0.7)
                adj[0].take_damage(d)
                result['aoe_hits'].append((adj[0], d))
            _max_status(monster, 'bleeding', 4)
        elif tier == 10:
            for m in _adjacent_monsters(player, monsters, exclude=monster)[:2]:
                d = _aoe_dmg(0.6)
                m.take_damage(d)
                result['aoe_hits'].append((m, d))
                _max_status(m, 'bleeding', 4)
            _max_status(monster, 'bleeding', 4)
            _max_status(monster, 'sundered', 3)
        elif tier == 15:
            for m in _adjacent_monsters(player, monsters, exclude=monster):
                d = _aoe_dmg(0.5)
                m.take_damage(d)
                result['aoe_hits'].append((m, d))
                _max_status(m, 'bleeding', 6)
                _max_status(m, 'sundered', 5)
            _max_status(monster, 'bleeding', 6)
            _max_status(monster, 'sundered', 5)
        elif tier == 20:
            hits = 0
            for m in _adjacent_monsters(player, monsters, exclude=monster):
                d = _aoe_dmg(0.6)
                m.take_damage(d)
                result['aoe_hits'].append((m, d))
                _max_status(m, 'bleeding', 10)
                _max_status(m, 'sundered', 8)
                hits += 1
            _max_status(monster, 'bleeding', 10)
            _max_status(monster, 'sundered', 8)
            regen_pct = min(15, (hits + 1) * 5)  # primary + adj hits
            player.hp = min(player.max_hp,
                            player.hp + max(1, player.max_hp * regen_pct // 100))
        return result

    # -----------------------------------------------------------------
    # CROSSBOW — armor-punching bolt
    # -----------------------------------------------------------------
    if key == 'crossbow':
        if tier == 10:
            _max_status(monster, 'slowed', 3)
        elif tier == 15:
            # Skip next 3 reloads by setting a counter the reload check reads.
            player._crossbow_skip_reloads = int(getattr(player, '_crossbow_skip_reloads', 0) or 0) + 3
        elif tier == 20:
            _max_status(monster, 'slowed', 3)
            # Ballista: bolt continues through target in the same line up to 5 tiles.
            dx = 0 if monster.x == player.x else (1 if monster.x > player.x else -1)
            dy = 0 if monster.y == player.y else (1 if monster.y > player.y else -1)
            for step in range(1, 6):
                bx, by = monster.x + dx * step, monster.y + dy * step
                for m in monsters or []:
                    if getattr(m, 'alive', False) and m.x == bx and m.y == by \
                            and m is not monster:
                        d = _aoe_dmg(0.7)
                        m.take_damage(d)
                        result['aoe_hits'].append((m, d))
                        _max_status(m, 'slowed', 3)
                        break
        # tier 5, 10 also bypass DR via _BYPASS_DR_TIERS.
        return result

    # -----------------------------------------------------------------
    # SLING — ricochet + shatter
    # -----------------------------------------------------------------
    if key == 'sling':
        import random as _rng
        if tier == 5:
            adj = _adjacent_monsters(monster, monsters, exclude=monster)
            if adj and _rng.random() < 0.25:
                d = _aoe_dmg(0.5)
                adj[0].take_damage(d)
                result['aoe_hits'].append((adj[0], d))
        elif tier == 10:
            adj = _adjacent_monsters(monster, monsters, exclude=monster)
            if adj:
                d = _aoe_dmg(0.5)
                adj[0].take_damage(d)
                result['aoe_hits'].append((adj[0], d))
            _max_status(monster, 'stunned', 1)
        elif tier == 15:
            _max_status(monster, 'stunned', 2)
            _max_status(monster, 'slowed', 2)
        elif tier == 20:
            for m in _adjacent_monsters(player, monsters, radius=3, exclude=monster):
                d = _aoe_dmg(0.5)
                m.take_damage(d)
                result['aoe_hits'].append((m, d))
                _max_status(m, 'stunned', 1)
            _max_status(monster, 'stunned', 1)
        return result

    return result


# Harpe (scimitar): petrify_on_crit was moved to chain-15 petrify.
# Handled inline in the sword-key block above via a per-weapon flag check.



# --- Material effective_against / vulnerabilities lookup ---------------------
# Cached once. Populated lazily on first call. Generalizes the old hardcoded
# "silver vs undead, iron vs fey" rules into a data-driven system: every
# material in data/materials/weapons/*.json declares effective_against (tags
# the wielder hits +50%) and vulnerabilities (tags the wielder TAKES extra
# damage from). Gap 4.
_MATERIAL_EFFECTIVE_AGAINST: dict[str, set] = {}
_MATERIAL_VULNERABILITIES:   dict[str, set] = {}


def _load_material_tags() -> None:
    """Read all weapon-capable materials and build the effective/vulnerable maps."""
    if _MATERIAL_EFFECTIVE_AGAINST:
        return  # already loaded
    import json
    import os
    from paths import data_path
    mat_dir = data_path('data', 'materials', 'weapons')
    if not os.path.isdir(mat_dir):
        return
    for fn in os.listdir(mat_dir):
        if not fn.endswith('.json'):
            continue
        with open(os.path.join(mat_dir, fn), encoding='utf-8') as f:
            m = json.load(f)
        mid = m.get('id') or os.path.splitext(fn)[0]
        _MATERIAL_EFFECTIVE_AGAINST[mid] = set(m.get('effective_against', []))
        _MATERIAL_VULNERABILITIES[mid]   = set(m.get('vulnerabilities', []))


# The weapon-material bonus (effective_against: silver vs undead, cold iron
# vs fey and demons...) is applied in weapon_type_multiplier, through the
# material id each common weapon carries in damage_types. (A second copy of
# it here, _material_effective_multiplier, was never called; removed in bug
# bash 4, call 14.)

# Damage taken through a weapon-material vulnerability (call 14).
MATERIAL_VULNERABLE_MULT = 1.25

# What the hit message says when it applies, by the tag that matched.
_VULNERABLE_NOTES = {
    'demon': "Your {mat} draws its fury!",
    'fire': "The flames catch your {mat}!",
    'acid': "The acid eats into your {mat}!",
    'holy': "Holy light sears your {mat}!",
}


def material_vulnerability(player, attack_tags) -> tuple[float, str]:
    """(multiplier, note) for a blow on a player whose wielded weapon's
    material is vulnerable to it. ``attack_tags`` are the attacker's tags
    plus the attack's damage type.

    The materials say it in data/materials/weapons/*.json `vulnerabilities`:
    cold iron draws a demon's fury, wood and leather catch fire, rawhide
    rots in acid, the void-touched metal burns in holy light. Wielding one
    (melee or the readied ranged weapon) makes such a blow land
    MATERIAL_VULNERABLE_MULT as hard. The list was loaded and never read
    until call 14."""
    tags = {str(t) for t in (attack_tags or ()) if t}
    if not tags:
        return 1.0, ''
    _load_material_tags()
    for slot in (getattr(player, 'weapon', None), getattr(player, 'ranged_weapon', None)):
        if slot is None:
            continue
        mat = str(getattr(slot, 'material', '') or '')
        vuln = set(_MATERIAL_VULNERABILITIES.get(mat, ()))
        vuln |= set(getattr(slot, 'vulnerabilities', None) or ())
        hit = sorted(vuln & tags)
        if hit:
            mat_name = mat.replace('_', ' ')
            note = _VULNERABLE_NOTES.get(hit[0], "Your {mat} weapon is a weakness here!")
            return MATERIAL_VULNERABLE_MULT, note.format(mat=mat_name)
    return 1.0, ''


# Tag/name heuristics used by warhammer's anti_heavy_at_max bonus.
_HEAVY_ARMORED_TAGS = {'construct', 'dragon'}
_HEAVY_ARMORED_NAME_HINTS = (
    'knight', 'paladin', 'samurai', 'cataphract', 'sentinel',
    'guard', 'plate', 'golem', 'juggernaut',
)


def _is_heavy_armored(monster) -> bool:
    """True for monsters whose defining trait is heavy plate / hide armor.
    Used by anti_heavy_at_max (warhammer) and as a proxy where no AC stat exists."""
    tags = set(getattr(monster, 'tags', []))
    if tags & _HEAVY_ARMORED_TAGS:
        return True
    name = (getattr(monster, 'name', '') or '').lower()
    return any(hint in name for hint in _HEAVY_ARMORED_NAME_HINTS)


# Damage type advantage/disadvantage vs monster flags.
# Monster defn can set 'resistances': ['slash'] or 'weaknesses': ['pierce']
# Melee damage multiplier against a scaled dragon when striking up from a
# pit (the scales themselves do not apply at all from there).
PIT_BELLY_MULT = 1.25


def _damage_multiplier(damage_types: list[str], monster) -> float:
    """Return 0.5 for resistance, 1.5 for weakness, 1.0 otherwise.
    If weapon has multiple types, pick the best result across all types.

    Material effective_against now drives this via data (see _load_material_tags).
    The legacy hardcoded silver/iron rules are kept as a safety net for monsters
    whose data files predate the material system."""
    _load_material_tags()
    resistances = getattr(monster, 'resistances', [])
    weaknesses  = list(getattr(monster, 'weaknesses', []))
    tags = set(getattr(monster, 'tags', []))
    # Data-driven material bonuses (silver vs undead, cold_iron vs fey, etc.)
    for dt in damage_types:
        eff = _MATERIAL_EFFECTIVE_AGAINST.get(dt)
        if eff and (eff & tags) and dt not in weaknesses:
            weaknesses.append(dt)
    # Legacy hardcoded fallbacks (kept for safety while the new data lands)
    if 'undead' in tags or 'demon' in tags:
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


RESISTED = 0.5        # a blow of a kind the creature shrugs off
WEAK_TO = 1.5         # a blow of a kind, or a metal, it cannot bear


def weapon_type_multiplier(weapon, monster, blessed: bool | None = None) -> tuple[float, float]:
    """How a weapon's FORM and its SUBSTANCE each meet a monster: (form,
    substance). Multiply them for the whole effect.

    FORM is how the weapon wounds: its own damage types (slash, pierce,
    blunt, and for some named weapons fire, holy and the like). A blade that
    can cut or thrust uses whichever serves better, so the best of its own
    types counts: 0.5 if the creature resists every one, 1.5 if it is weak
    to any.

    SUBSTANCE is what the weapon is made of, and whether it is blessed:
    silver, iron, cold iron, holy. It is worth 1.5 against a creature that
    cannot bear it and is otherwise 1. It never makes a blow weaker.

    These used to be one list with the best multiplier winning. The material
    is never a resistance, so it always scored 1.0 and outvoted the form: in
    60,465 weapon-and-monster pairs not one blow was ever resisted, and the
    87 monsters written to shrug off a cut, a thrust or a crushing blow
    never did. A skeleton now really is hard to stab and easy to smash."""
    _load_material_tags()
    resistances = set(getattr(monster, 'resistances', None) or ())
    weaknesses = set(getattr(monster, 'weaknesses', None) or ())
    tags = set(getattr(monster, 'tags', None) or ())

    if weapon is None:
        own = ['blunt']                      # a fist
    else:
        own = [t for t in (getattr(weapon, 'damage_types', None) or []) if t]
        if len(own) > 1:
            own = [t for t in own if t != 'physical'] or own
    form = 1.0
    if own:
        scores = []
        for t in own:
            eff = _MATERIAL_EFFECTIVE_AGAINST.get(t)
            if t in weaknesses or (eff and (eff & tags)):
                scores.append(WEAK_TO)
            elif t in resistances:
                scores.append(RESISTED)
            else:
                scores.append(1.0)
        form = max(scores)

    substance = 1.0
    if weapon is not None:
        made_of = []
        mat = str(getattr(weapon, 'material', '') or '').lower()
        if mat and mat not in own:
            made_of.append(mat)
        if blessed is None:
            blessed = getattr(weapon, 'buc', 'uncursed') == 'blessed'
        if blessed and 'holy' not in own:
            made_of.append('holy')
        legacy = set()
        if 'undead' in tags or 'demon' in tags:
            legacy.add('silver')
        if 'fey' in tags:
            legacy.add('iron')
        for sub in made_of:
            eff = _MATERIAL_EFFECTIVE_AGAINST.get(sub)
            if sub in weaknesses or sub in legacy or (eff and (eff & tags)):
                substance = WEAK_TO
                break
    return form, substance


def effective_chain(player, monster, weapon, score: int, consume: bool = True) -> int:
    """The chain a blow lands at: the quiz score plus every head start the
    gear, quirks and passives give. 0 is a miss.

    One function for the real blow (consume=True: one-shot carries and
    saves are spent) and the combat strip's "Strike Now" preview
    (consume=False: nothing is spent), so the two always agree (call 13)."""
    chain = score

    # Cow King's Horns (or any armor with chain_bonus): free chain head start
    # Only on an attack that lands: added to a chain of 0 it turned every
    # wrong first answer into a hit, and combat never does a sum for you.
    if score >= 1:
        for slot in getattr(player, 'armor_slots', []):
            if slot and getattr(slot, 'chain_bonus', 0):
                chain += slot.chain_bonus
        # Chain-equip passive attack_chain_cap_bonus (Ring of Gawain,
        # Torque of Lugh). It raised a chain cap no weapon has any more.
        try:
            from chain_passives import get_attack_chain_cap_bonus
            chain += int(get_attack_chain_cap_bonus(player) or 0)
        except ImportError:
            pass

    # Parashu (engine wave 3): chain_no_reset_on_tag carry. After a kill
    # of a matching-tag target, the next attack starts at the same
    # chain rung instead of restarting. Consumed immediately so a
    # second attack restarts normally.
    _carry = int(getattr(player, '_chain_carry', 0) or 0)
    if _carry > 0:
        chain += _carry
        if consume:
            player._chain_carry = 0

    # Jormungandr quirk: with the weapon the quirk was earned on, any
    # attack that lands at all counts as one link longer. (The old
    # reward raised a chain CAP that common weapons no longer have.)
    if (score >= 1 and weapon is not None
            and getattr(player, 'quirk_progress', {}).get('jormungandr_weapon_id')
            == getattr(weapon, 'id', None)):
        chain += 1

    # Glamdring: Foe-Hammer's signature glow. Against any goblin/orc-
    # tagged enemy, +1 chain rung head start while equipped. Per audit
    # 2026-05-30 — the `glows_near_orcs` JSON flag was previously inert.
    # Lore: "the sword preempts — the wielder gets +2 initiative."
    if weapon and getattr(weapon, 'glows_near_orcs', False):
        if _tag_match(monster, 'goblin') or _tag_match(monster, 'orc'):
            chain += 1

    # Fail-not: Tristan's bow given by Morgan le Fay — never misses.
    # Chain 0 is promoted to chain 1 (minimum hit) so a missed quiz still lands.
    if chain == 0 and weapon and getattr(weapon, 'class_mechanic', '') == 'guaranteed_hit':
        chain = 1
    # Gungnir: "the spear has never missed." Per audit 2026-05-30 — the
    # `cannot_miss` data flag previously had no consumer. Same chain 0 -> 1
    # promotion as guaranteed_hit but driven from the weapon's JSON.
    if chain == 0 and weapon and getattr(weapon, 'cannot_miss', False):
        chain = 1

    # Fail-not (engine wave 3): cannot_miss_before_player_takes_damage.
    # The Tristan-knot vow holds until the player takes a hit this combat.
    # Once the combat tracker says the player has been hurt, the spell
    # falters and misses can land normally. See _combat_player_taken_damage
    # marker (set by player.take_damage hook below).
    if (chain == 0 and weapon and getattr(weapon, 'cannot_miss_before_hurt', False)
            and not getattr(player, '_combat_player_taken_damage', False)):
        chain = 1

    # Hrunting (engine wave 3): one_shot_chain_save_per_floor. The poem's
    # promise: "never failed any man who grasped it." Once per floor,
    # demote a chain-0 (miss) into chain-1 (light hit). After the save
    # is spent, normal misses resume. Player-level marker
    # `_hrunting_save_used` is reset on every floor in main._change_level.
    if (chain == 0 and weapon and getattr(weapon, 'one_shot_chain_save_per_floor', False)
            and not getattr(player, '_hrunting_save_used', False)):
        if consume:
            player._hrunting_save_used = True
        chain = 1

    # Harpe (engine wave 3): skip_chain_warmup_vs_tag. Against matching-
    # tag enemies, the chain auto-completes the warm-up — start at rung 2
    # instead of rung 1. The blade that knows the monster.
    _skip_warmup = getattr(weapon, 'skip_chain_warmup_vs_tag', None) or []
    if _skip_warmup and chain >= 1:
        for _tg in _skip_warmup:
            if _tag_match(monster, _tg):
                chain += 1
                break

    # Skofnung (engine wave 3): chain_bonus_on_low_hp_window. When the
    # player has just dropped below 50% HP, the next attack adds N chain
    # rungs (one of the twelve berserkers takes over). Tracker
    # `_skofnung_low_hp_pending` is set by player.take_damage when the
    # threshold is crossed, and consumed here.
    _skofnung_bonus = int(getattr(weapon, 'chain_bonus_on_low_hp_window', 0) or 0)
    if (_skofnung_bonus > 0 and chain >= 1
            and getattr(player, '_skofnung_low_hp_pending', False)):
        chain += _skofnung_bonus
        if consume:
            player._skofnung_low_hp_pending = False
    return chain


_WIELDED = object()     # strike_damage: "the weapon in the slot that attacks"


def strike_damage(player, monster, chain: int, *, ranged: bool = False, ammo=None,
                  consume: bool = False, dice=None, weapon=_WIELDED) -> int:
    """The damage one blow at ``chain`` does to ``monster`` before
    Monster.take_damage: base, Strength, blessing, ammo, chain, form and
    substance, class mechanics, hero passives, shields, scales, wards and
    every gear bonus.

    This is the ONE damage calculation. player_attack calls it for the real
    blow (consume=True: one-shot buffs such as Empower, blade flow and the
    once-a-floor charges are spent, and dice are rolled). The combat strip
    calls it for its "Strike Now N Damage" preview (consume=False: nothing
    is spent; dice count as their average). Before call 13 the strip did
    its own sum and left out Strength, blessings, shields and scales."""
    if weapon is _WIELDED:
        weapon = player.ranged_weapon if ranged else player.weapon
    is_ranged = bool(ranged)
    if dice is None:
        dice = roll if consume else _dice_mean
    if chain < 1:
        return 0
    # Base damage: new integer field preferred over legacy dice string.
    # Unarmed (fist) uses the chain combat v2 STR-scaled base: 2 × (1 + STR/10)
    # above 10 STR. STR 10 = 2, STR 15 = 3, STR 20 = 4. Intentionally weak —
    # this is the "you dropped your weapon" fallback, not an alternative build.
    # (A real, small number: fists are fists on any floor.)
    if weapon and weapon.base_damage:
        base = weapon.base_damage
    elif weapon and weapon.damage:
        base = dice(weapon.damage)
    else:
        base = max(1, round(2 * (1 + max(0, player.STR - 10) / 10.0)))

    # Ranged stat bonuses (chain combat v2). Per-hit additive on the base
    # BEFORE material/chain scaling. Bow/sling get STR + PER at /4;
    # crossbow gets PER only (it fires like a machine, arm strength doesn't
    # help). Applies only to actual ranged shots so melee
    # attacks are unaffected.
    if is_ranged:
        _wc = getattr(weapon, 'weapon_class', '') if weapon else ''
        # A share of the weapon's own base: RANGED_STAT_SHARE for every
        # four points of the stat above 10.
        _own = int(base)
        # At least one point a step, so the bonus exists on a small bow too.
        for _step in ((max(0, (player.PER - 10) // 4),)
                      + ((max(0, (player.STR - 10) // 4),) if _wc != 'crossbow' else ())):
            if _step:
                base += max(_step, int(round(_own * RANGED_STAT_SHARE * _step)))

    # Weakened / frozen: halve player attack damage. Both effects
    # describe "attack damage halved" / "encased in ice." Previously
    # NEITHER was wired for the player — applied by 30+ monsters but
    # did nothing.
    if player.has_effect('weakened') or player.has_effect('frozen'):
        base = max(1, base // 2)

    # Ammo damage bonus (ranged shots only)
    ammo_bonus  = int(ammo.damage_bonus) if ammo else 0      # real numbers, data/items/ammo.json
    enchant     = weapon.enchant_bonus if weapon else 0
    # Chain combat v2: polynomial `mult = chain ** chain_exponent` when the
    # weapon opts in; otherwise fall back to the legacy per-rung array.
    # Uniques keep their handcrafted `chain_multipliers`; new common templates
    # ship `chain_exponent` (default 1.15). Unarmed (fist) also uses the
    # polynomial at 1.15 — the base damage is already floored low.
    _chain_exp = getattr(weapon, 'chain_exponent', None) if weapon else 1.15
    if _chain_exp and _chain_exp > 0:
        mult = float(chain) ** float(_chain_exp)
        multipliers = None  # signals "polynomial path" to blocks below
    else:
        multipliers = weapon.chain_multipliers if weapon else _DEFAULT_MULTIPLIERS
        mult        = multipliers[min(chain - 1, len(multipliers) - 1)]

    # Musashi quirk: an attack that ends on a chain of exactly 1 deals
    # double damage ("one cut is enough"). It used to swap in the 2nd
    # entry of the legacy multiplier array, which did nothing at all on
    # the polynomial-chain weapons every common weapon now is.
    if chain == 1 and getattr(player, 'quirk_progress', {}).get('musashi_active'):
        mult *= 2.0

    # Chain combat v2 (v2.14.0): pre-damage per-class chain-special hooks.
    # Sets `player._chain_bypass_dr` when the special calls for it (only
    # on the real blow; the preview keeps it local), and returns any
    # per-hit damage multiplier (Bow C20 vitals x2). Runs before shielded /
    # dragon_scales checks so the bypass takes effect.
    _pre_mult, _pre_bypass = _chain_pre_damage(weapon, chain)
    mult *= _pre_mult
    if _pre_bypass and consume:
        player._chain_bypass_dr = True

    # Atalanta's Bow: first_blood_bonus — at chain 1 against a target
    # that has not yet taken damage this combat (HP at max), +50%
    # damage. The Calydonian-Boar opener — first arrow rewarded.
    # Per audit 2026-05-30 (data flag was previously inert).
    if (chain == 1 and weapon and getattr(weapon, 'first_blood_bonus', False)
            and monster.hp >= monster.max_hp):
        mult *= 1.5

    # Damage type advantage vs monster resistances/weaknesses
    # Gram (reforged) ignores all resistances
    _ignores_res = bool(weapon and getattr(weapon, 'ignore_resistances', False))
    # The weapon's form (cut, thrust, crush) and its substance (silver,
    # iron, blessed) each meet the monster: see weapon_type_multiplier.
    # Bare hands crush.
    _form_mult, _subst_mult = weapon_type_multiplier(weapon, monster)
    # Gram and the Sword of Michael ignore RESISTANCES; a weakness
    # still counts.
    if _ignores_res:
        _form_mult = max(1.0, _form_mult)
    dtype_mult = _form_mult * _subst_mult

    # Weapon-side effective_against array. Per audit 2026-05-30 — many
    # uniques (Zulfiqar, Vel of Murugan, Spear of Longinus, Mjolnir,
    # Dawnbreaker, Gungnir, Fragarach, Skofnung, Gilgamesh's Axe,
    # Shamshir) declared per-weapon anti-tag arrays that the engine
    # ignored (only material.effective_against was read). Boost
    # damage 1.5x when the target matches any declared tag.
    # Per-weapon effective_against: ONLY for UNIQUE weapons' explicit anti-tag
    # arrays (Zulfiqar, Mjolnir, Dawnbreaker...). A COMPOSITIONAL weapon
    # inherits effective_against from its MATERIAL (instantiate_weapon copies
    # it), but the material is already added to damage_types above, so
    # _damage_multiplier ALREADY applied that bonus -- counting it again here
    # double-dipped it. A yew crossbow vs a fey Satyr did 1.5 x 1.5 = 2.25x:
    # a 7-base chain-5 shot hit for 41 instead of ~28. (2026-06-07 ranged fix;
    # gated at the use-site so it also corrects weapons already in saves.)
    if weapon and getattr(weapon, 'is_unique', False):
        _weapon_anti = getattr(weapon, 'effective_against', None) or []
        if _weapon_anti and (set(getattr(monster, 'tags', [])) & set(_weapon_anti)):
            dtype_mult *= 1.5
    if weapon:
        # Anduril-style numeric undead_multiplier (legacy `undead_bonus`
        # JSON field): applies as a flat 1.5x against undead when set > 1.
        _und_mult = float(getattr(weapon, 'undead_multiplier', 1.0) or 1.0)
        if _und_mult > 1.0 and _tag_match(monster, 'undead'):
            dtype_mult *= 1.5

    # Akinakes of Acrisius: prophecy_blade. At first equip the blade
    # declared a random tag (stored on player._prophecy_target_tag).
    # That tag's monsters take +50% damage from the Akinakes for the
    # rest of the run. Per audit 2026-05-30 — the JSON flag was inert.
    if weapon and getattr(weapon, 'prophecy_blade', False):
        _proph = getattr(player, '_prophecy_target_tag', None)
        if _proph and _tag_match(monster, _proph):
            dtype_mult *= 1.5

    # Mistilteinn (engine wave 3): damage_double_vs_resistant_at_max.
    # At max chain, against ANY target with resistances, double damage.
    # Baldur's flaw: protected against everything except the small thing.
    if weapon and getattr(weapon, 'damage_double_vs_resistant_at_max', False):
        _maxc = weapon.max_chain_length or len(weapon.chain_multipliers)
        if chain >= _maxc and getattr(monster, 'resistances', None):
            dtype_mult *= 2.0

    # Robin Hood's Longbow (engine wave 3): stealth_damage_bonus.
    # Striking from invisibility/stealth: +X% damage. Stored as
    # fractional multiplier (0.5 = +50%).
    _sb = float(getattr(weapon, 'stealth_damage_bonus', 0.0) or 0.0) if weapon else 0.0
    if _sb > 0 and player.has_effect('invisible'):
        dtype_mult *= 1.0 + _sb

    # Kusanagi (engine wave 3): surrounded_proc_bonus. When 3+ enemies
    # are adjacent to the player, +25% damage. Chain combat v2 (v2.14.0):
    # rewired from "force crit" to flat multiplier since crit was retired
    # (chain IS the crit). Feel is the same — surround-the-warrior payoff.
    if weapon and getattr(weapon, 'surrounded_proc_bonus', False):
        _adj = 0
        try:
            _mons = getattr(player, '_combat_monsters_ref', None) or []
            for _m in _mons:
                if _m.alive and abs(_m.x - player.x) <= 1 and abs(_m.y - player.y) <= 1 \
                        and not (_m.x == player.x and _m.y == player.y):
                    _adj += 1
        except Exception:
            _adj = 0
        if _adj >= 3:
            mult *= 1.25

    # Oathkeeper (engine wave 3): adjacent_pet_damage_bonus.
    # When ANY pet is within 1 tile of the player, multiply damage.
    # Lore: care for what walks beside you.
    _ap_bonus = float(getattr(weapon, 'adjacent_pet_damage_bonus', 0.0) or 0.0) \
        if weapon else 0.0
    if _ap_bonus > 0:
        _pets = getattr(player, '_combat_pets_ref', None) or []
        for _p in _pets:
            if (getattr(_p, 'alive', False)
                    and abs(_p.x - player.x) <= 1 and abs(_p.y - player.y) <= 1):
                dtype_mult *= 1.0 + _ap_bonus
                break

    # Shield bypass: ignore_shield weapons deal full damage through monster's shielded effect.
    # Chain combat v2 (v2.14.0): also bypassed when the player has a `blade_flow`
    # stack or a `_chain_bypass_dr` flag set by the class-chain-special pre-damage
    # dispatch (spear/1h_sword/bow/crossbow/mace at threshold). Those consumers are
    # decremented below; the "already going to bypass" check just probes here.
    _bf_probe = int(player.status_effects.get('blade_flow', 0) or 0) > 0
    _cb_probe = bool(getattr(player, '_chain_bypass_dr', False)) or _pre_bypass
    _shield_bypass = (weapon and weapon.ignore_shield) or _bf_probe or _cb_probe
    if not _shield_bypass:
        if monster.has_effect('shielded'):
            dtype_mult *= 0.5

    # Chain combat v2 (v2.14.0): crit is retired. Chain IS the crit —
    # the polynomial ladder handles the "big number" reward directly.
    # The `crit` boolean is kept for on_complete kwargs so callers that
    # branch on it still compile; it now stays False everywhere. Harpe's
    # petrify moved to the class-chain-special dispatch below (petrifies
    # at chain 15 via a per-weapon flag). Soul Reaver's next-hit-auto-crit
    # rewired to a `blade_flow` player stack down at growth_on_innocent_kill.
    # (player_attack's callback keeps crit = False for on_complete.)

    # Pre-damage class-mechanic multipliers. Apply to mult before damage
    # is rolled. Several mechanics fire ONLY at max chain (the chain-5
    # payoff identity); some fire on every hit (versatile, master_strike).
    _pre_mech = getattr(weapon, 'class_mechanic', None) if weapon else None
    if _pre_mech and weapon:
        _max_c = weapon.max_chain_length or len(weapon.chain_multipliers)
        _at_max = chain >= _max_c

        # versatile (bastard_sword) — +20% damage when wielded 2H (no shield).
        # Fires on EVERY hit, not just max chain.
        if _pre_mech == 'versatile' and player.shield is None:
            mult *= 1.20

        # master_strike (longsword) — the Meisterhau. At chain 3+, +15%
        # damage representing the diagonal cut that defeats defensive guards.
        if _pre_mech == 'master_strike' and chain >= 3:
            mult *= 1.15

        # str_bonus_range_7 (composite_bow) — the laminated horn+sinew+wood
        # stack requires real bow-arm strength to fully draw. Each STR
        # point above 10 adds 5% to damage. Ranged shots only (ammo present).
        # Per user 2026-05-30: this mechanic was declared in the template
        # but never wired — composite bows behaved identically to longbows.
        if _pre_mech == 'str_bonus_range_7' and is_ranged:
            mult *= 1.0 + max(0, (player.STR - 10) * 0.05)

        # AT-MAX-CHAIN damage multipliers
        if _at_max:
            if _pre_mech == 'anti_heavy_at_max' and _is_heavy_armored(monster):
                mult *= 1.5
            elif _pre_mech == 'armor_pierce_at_max':
                mult *= 1.35
            elif _pre_mech == 'ignores_all_armor':
                # heavy_crossbow signature — the bolt goes through as if
                # the creature did not resist a thrust at all. (This also
                # multiplied the blow by the same factor again, which
                # would have doubled it; no blow was ever resisted, so it
                # never showed.)
                if _form_mult < 1.0:
                    dtype_mult /= _form_mult
                    _form_mult = 1.0
            elif _pre_mech == 'ignores_half_armor':
                # light_crossbow — halve the resistance penalty
                if _form_mult < 1.0:
                    _half = (_form_mult + 1.0) / 2.0
                    dtype_mult *= _half / _form_mult
                    _form_mult = _half

    # Beowulf quirk: unarmed attacks deal +5 base damage
    if weapon is None:
        unarmed_bonus = getattr(player, 'quirk_progress', {}).get('beowulf_unarmed_bonus', 0)
        base += int(unarmed_bonus)

    # (Weakened is applied once, with frozen, near the top of this
    # function. A second halving here used to quarter the damage.)

    # Hero passive: Will to Power — +30% damage when below 30% HP.
    hero_passives = getattr(player, 'hero_passives', set())
    if 'will_to_power' in hero_passives and player.max_hp > 0 and \
            player.hp <= player.max_hp * 0.3:
        mult *= 1.3
    # Hero passive: Witcher Mutations — +20% damage vs monsters (all).
    if 'witcher_mutations' in hero_passives:
        mult *= 1.2
    # Hero passive: Niten Ichi-Ryū (Musashi) — +15% damage when a melee
    # weapon is equipped. Musashi ships longsword + shortsword (both melee);
    # Player has no distinct `melee_weapon` slot, and the `ranged_weapon`
    # slot only accepts ammo-requiring weapons, so the old
    # weapon+ranged_weapon gate never fired for his kit. Gate now on
    # "a non-ammo weapon in the primary slot" — preserves the two-swords
    # fantasy for any melee loadout.
    _mw = getattr(player, 'weapon', None)
    if 'niten_ichi_ryu' in hero_passives and _mw is not None and \
            not getattr(_mw, 'requires_ammo', False):
        mult *= 1.15
    # Hero buff: crit_buff (Joan of Arc's Standard / Ash's She-Bitch) — next attack crits
    if getattr(player, 'status_effects', {}).get('crit_buff', 0) > 0:
        mult *= 1.5
        # consume one charge by reducing duration; if it reaches 0, status fades naturally
        if consume:
            player.status_effects['crit_buff'] = max(0, player.status_effects['crit_buff'] - 1)
    # Hero buff: berserk — flat +30% damage while active
    if getattr(player, 'status_effects', {}).get('berserk', 0) > 0:
        mult *= 1.3

    # BUC weapon bonus: blessed +1, cursed -1
    buc_bonus = 0
    if weapon:
        wbuc = getattr(weapon, 'buc', 'uncursed')
        if wbuc == 'blessed':
            buc_bonus = 1
        elif wbuc == 'cursed':
            # Hero passive: Diogenes' Cynic Detachment — cursed items don't penalize.
            if 'cynic_detachment' not in getattr(player, 'hero_passives', set()):
                buc_bonus = -1

    # Chandrahasa: bonus damage when player HP is low
    low_hp_mult = 1.0
    if weapon and getattr(weapon, 'low_hp_damage_bonus', False) and player.max_hp > 0:
        hp_pct = player.hp / player.max_hp
        if hp_pct < 0.5:
            low_hp_mult = 1.0 + (0.5 - hp_pct) * 2.0  # up to 2x at 0% HP

    # Decision D4 (2026-10-06): ranged is a specialist's tool. Measured:
    # a bow's base equals a blade's of the same material, a floor yields
    # about 15 shots against the 30 or so attacks it takes to clear, and
    # a shot gets no Strength multiplier, so a Strength build's blade
    # out-hits its bow by up to two thirds. That is the intended shape
    # (first strike and safety, paid for in ammunition and damage); do
    # not add a stat multiplier here.
    # STR scales MELEE damage only. RANGED shots scale on PER (the base
    # bonus added above) -- applying str_factor to ranged too made bows and
    # crossbows double-dip on STR *and* PER, the persistent "ranged hits way
    # too hard" bug. (The composite_bow keeps its own intentional draw-weight
    # STR mechanic, str_bonus_range_7, applied separately to `mult`.)
    str_factor = 1.0 if is_ranged else 1.0 + max(0, player.STR - 10) * 0.03

    # Chain combat v2 (v2.14.0): when the player is in "bypass DR" mode
    # (blade_flow buff or chain-special one-shot flag), clamp dtype_mult
    # up to at least 1.0 so resistances stop cutting damage. Weaknesses
    # (dtype_mult > 1.0) survive untouched — you still hit fire-vulnerable
    # things extra hard with a fire-tagged weapon.
    if (_bf_probe or _cb_probe) and _form_mult < 1.0:
        dtype_mult /= _form_mult             # the resistance alone is undone
        _form_mult = 1.0

    # round (not int-truncate): chain damage gradient must survive at
    # low base values. With int(), iron sword base=1 gave 1,1,1,1,2
    # across chain levels — invisible progression. round() preserves
    # the half-step damage differences that the chain ladder is designed
    # to deliver.
    damage = max(1, round((base + enchant + ammo_bonus + buc_bonus) * mult * dtype_mult * str_factor * low_hp_mult))

    # Empower spell: 3x damage on next hit, then clears
    if player.has_effect('empowered'):
        damage *= 3
        if consume:
            player.status_effects.pop('empowered', None)

    # Chain combat v2 (v2.14.0): mace / warhammer `armor_crack` and the
    # dagger-hemorrhage `deep_wound` both amp incoming damage by +25%.
    # They can stack additively (a mace strike into an axe target etc.);
    # cap the combined boost at +50% so a lucky stack isn't runaway.
    _amp = 0.0
    if monster.has_effect('armor_crack'):
        _amp += 0.25
    if monster.has_effect('deep_wound'):
        _amp += 0.25
    if _amp > 0:
        damage = int(damage * (1.0 + min(0.50, _amp)))

    # Chain combat v2: `blade_flow` player buff — the next N attacks bypass
    # damage reduction (dragon_scales, shielded, resistances). Consumes one
    # stack per attack. Set by 1h Sword C15/C20, 2h Sword C20, and Soul
    # Reaver's growth_on_innocent_kill.
    _bf_stacks = int(player.status_effects.get('blade_flow', 0) or 0)
    _blade_flow_bypass = _bf_stacks > 0
    if _blade_flow_bypass and consume:
        player.status_effects['blade_flow'] = _bf_stacks - 1
        if player.status_effects['blade_flow'] <= 0:
            player.status_effects.pop('blade_flow', None)

    # Chain combat v2: per-hit chain-special "bypass DR" flag set by
    # pre-damage class specials (e.g. crossbow chain 5, 1h sword chain 10,
    # spear chain 10+, mace chain 20, bow chain 15+). One-shot side channel.
    _chain_bypass = bool(getattr(player, '_chain_bypass_dr', False)) or _pre_bypass
    if _chain_bypass and consume:
        player._chain_bypass_dr = False  # consume immediately

    _skip_dr = (
        getattr(weapon, 'ignore_resistances', False)
        or _blade_flow_bypass
        or _chain_bypass
    )

    # Dragon scales: massive damage reduction (bypassed by ignore_resistances,
    # blade_flow, chain-special bypass flag, or player in pit)
    # From a pit the player strikes the unarmoured belly: the scales do
    # not apply at all and the blow lands half again as hard. This holds
    # for scale-ignoring weapons too (reforged Gram in the pit is the
    # best case, as in the saga). The old rule was x4 against x0.2, a
    # twenty-fold swing that would have ended Fafnir in one or two hits
    # had the pit status ever lasted long enough to use.
    # The belly strike is a blade driven upward at arm's length: MELEE
    # only. An archer in a pit is still shooting at scales (and would
    # otherwise be completely safe while doing full damage).
    dragon_scales = getattr(monster, 'dragon_scales', 0)
    # The _belly_strike / _ward_blocked / struck_from_the_pit notes are for
    # the messages after a REAL blow: the preview leaves them alone.
    _notes = {}
    # A damage ward (Abaddon): the same fraction-absorbed rule as scales,
    # with no pit to get under it. Holy fire from the floor-100 altars
    # strips it for a while; a weapon that ignores resistances ignores it.
    damage_ward = float(getattr(monster, 'damage_ward', 0.0) or 0.0)
    _notes['_ward_blocked'] = False
    _notes['_belly_strike'] = False
    if damage_ward > 0 and not _skip_dr:
        damage = max(1, int(damage * (1.0 - damage_ward)))
        _notes['_ward_blocked'] = True
    if dragon_scales > 0:
        if player.has_effect('in_pit') and not is_ranged:
            damage = int(damage * PIT_BELLY_MULT)
            _notes['_belly_strike'] = True
            _notes['struck_from_the_pit'] = True     # remembered: boons.solved_quest
        elif not _skip_dr:
            damage = max(1, int(damage * (1.0 - dragon_scales)))
    if consume:
        for _k, _v in _notes.items():
            setattr(player, _k, _v)

    # Sword of Michael vs Abaddon: bonus holy damage
    if weapon and getattr(weapon, 'abaddon_bonus_damage', '') and monster.kind == 'abaddon_destroyer':
        bonus = dice(weapon.abaddon_bonus_damage)       # real dice, weapon.json
        damage += bonus

    # Spear of Lugh (engine wave 4): damage_bonus_vs_gaze. Multiplies
    # damage against any monster with a gaze attack mechanic — Balor's
    # eye, the basilisk's stare, Medusa's petrifaction. Detection via
    # gaze_paralyze attr (Medusa-style) OR any attack with 'gaze' in
    # its type/name string.
    _lugh_mult = float(getattr(weapon, 'damage_bonus_vs_gaze', 0.0) or 0.0) if weapon else 0.0
    if _lugh_mult > 0:
        _has_gaze = False
        if int(getattr(monster, 'gaze_paralyze', 0) or 0) > 0:
            _has_gaze = True
        else:
            for _atk in getattr(monster, 'attacks', []) or []:
                _atk_str = str(_atk.get('type', '') or '') + ' ' + str(_atk.get('name', '') or '')
                if 'gaze' in _atk_str.lower():
                    _has_gaze = True
                    break
        if _has_gaze:
            damage = max(1, int(damage * (1.0 + _lugh_mult)))

    # Per-tag bonus damage dice (Anduril +1d8 vs undead, Glamdring vs
    # goblin, Cadmus vs dragon, Meleager vs beast, etc.). Each entry
    # in weapon.bonus_damage_vs_tag is rolled and added when the target
    # carries the matching tag. Generalizes abaddon_bonus_damage above.
    # Per audit 2026-05-30 — the *_bonus_damage JSON keys had no
    # consumer; this revives ~10 weapons' anti-tag dice.
    _tag_bonuses = getattr(weapon, 'bonus_damage_vs_tag', None) if weapon else None
    if _tag_bonuses:
        for _bt_tag, _bt_dice in _tag_bonuses.items():
            if _tag_match(monster, _bt_tag):
                try:
                    damage += dice(_bt_dice)             # real dice, weapon.json
                except Exception:
                    from game_log import log_error
                    log_error('combat._callback: recovered from an error')

    # Chain-equip passive: death_omen_mark (Cloak of the Morrigan T5).
    # +25% damage against the floor's highest-level monster.
    if getattr(player, '_death_omen_target', None) is monster:
        damage = int(damage * 1.25)

    # Helm of Leonidas (last_stand_bonus): LAST_STAND_SHARE more damage
    # while at <20% HP.
    try:
        from armor_procs import player_has_armor_proc
        if player.hp > 0 and player.max_hp > 0 and \
                player.hp / player.max_hp < 0.20 and \
                player_has_armor_proc(player, 'last_stand_bonus'):
            damage += max(1, int(round(damage * LAST_STAND_SHARE)))
    except ImportError:
        pass

    # Cuirass of Hannibal (cannae_encirclement): ENCIRCLED_SHARE more damage per adjacent
    # *other* enemy when surrounded by 3 or more. Bug-bash fix aac:
    # gate to melee only (no `ammo`) and exclude the target monster
    # itself from the adjacency count.
    if not is_ranged:
        try:
            from armor_procs import player_has_armor_proc as _pap
            if _pap(player, 'cannae_encirclement'):
                _mons_cc = getattr(player, '_combat_monsters_ref', None) or []
                _adj = 0
                for _mm in _mons_cc:
                    if not getattr(_mm, 'alive', False):
                        continue
                    if _mm is monster:
                        continue
                    if abs(_mm.x - player.x) <= 1 and abs(_mm.y - player.y) <= 1 \
                            and not (_mm.x == player.x and _mm.y == player.y):
                        _adj += 1
                if _adj >= 3:
                    damage += max(1, int(round(damage * ENCIRCLED_SHARE * _adj)))
        except ImportError:
            pass

    # Lorica Hamata of Caesar (et_tu_charge): +50% damage against the
    # marked first-attacker.
    if getattr(player, '_et_tu_target', None) is monster:
        damage = int(damage * 1.50)

    # Hippolyta girdle (amazon_charge): if armed (3+ straight-line moves),
    # next melee +50%. Consumed on hit.
    if getattr(player, '_amazon_charge_armed', False) and not is_ranged:
        damage = int(damage * 1.50)
        if consume:
            player._amazon_charge_armed = False
            player._straight_line_steps = 0

    # Dragonslayer Ring (monster_tag_chain_bonus): a per-tag damage bonus
    # against monsters carrying the matching tag.
    try:
        mtags = set(getattr(monster, 'tags', []) or [])
        for _acc in getattr(player, 'equipped_accessories', ()) or ():
            _tag_table = getattr(_acc, 'monster_tag_chain_bonus', {}) or {}
            for _tag, _bonus in _tag_table.items():
                if _tag in mtags:
                    damage = int(damage * (1.0 + float(_bonus) * 0.10))
    except AttributeError:
        pass

    # Bracers of Arjuna (gita_focus): first ranged attack per floor gets a
    # flat +50% damage. Chain combat v2 (v2.14.0): was "crits" via
    # crit_multiplier; retired to a straight 1.5x since crit is gone.
    if is_ranged:
        try:
            from armor_procs import consume_floor_charge, is_charge_available
            if (consume_floor_charge(player, 'gita_focus') if consume
                    else is_charge_available(player, 'gita_focus')):
                damage = int(damage * 1.5)
        except ImportError:
            pass

    # Backstab (dagger): at max chain against a target that does not know
    # you are there, the same blow lands twice. It used to be a second
    # take_damage after the first, and the first had already woken a
    # sleeping target, so a sleeper was never backstabbed.
    if _pre_mech == 'backstab' and weapon and             chain >= (weapon.max_chain_length or len(weapon.chain_multipliers)):
        if (monster.has_effect('sleeping')
                or (getattr(monster, 'ai_pattern', '') == 'ambush'
                    and not getattr(monster, '_aware', False))):
            damage *= 2
    return damage


def _rapid_shot_followup(weapon, chain: int, first: int) -> int:
    """Shortbow Rapid Shot: at max chain a second arrow follows the first
    into the same target for half its damage (0 when it does not fire)."""
    if (weapon is None or getattr(weapon, 'class_mechanic', None) != 'rapid_shot_at_max'
            or chain < (weapon.max_chain_length or len(weapon.chain_multipliers))):
        return 0
    return max(1, first // 2)


def strike_preview(player, monster, score: int, *, ranged: bool = False, ammo=None,
                   weapon=_WIELDED) -> int:
    """What pressing Strike Now at quiz chain ``score`` deals to the target:
    the same effective_chain + strike_damage the blow runs (nothing spent,
    dice at their average), plus a Rapid Shot follow-up arrow when the
    first does not kill. The combat strip shows this number (call 13)."""
    if weapon is _WIELDED:
        weapon = player.ranged_weapon if ranged else player.weapon
    chain = effective_chain(player, monster, weapon, score, consume=False)
    if chain < 1:
        return 0
    dmg = strike_damage(player, monster, chain, ranged=ranged, ammo=ammo,
                        consume=False, weapon=weapon)
    if monster.hp > dmg:
        dmg += _rapid_shot_followup(weapon, chain, dmg)
    return dmg


def player_attack(player, monster, quiz_engine, on_complete, ammo=None,
                  ranged=None):
    """
    Start a math chain quiz for the player attacking a monster.

    on_complete(damage: int, killed: bool, chain: int) is called when the quiz ends.
    Chain 0 (first answer wrong) = MISS (0 damage).
    Uses weapon's base_damage (int) or falls back to rolling weapon.damage (dice string).
    Applies enchant_bonus, ammo damage_bonus, damage type multipliers, and stun chance on hit.
    ammo: optional Ammo item whose damage_bonus is added to base damage.
    """
    # ``ranged`` says which weapon slot is attacking. It defaults to "is
    # there ammo?" for old callers, but infinite-ammo weapons (slings) fire
    # with ammo=None and must still be resolved as ranged.
    is_ranged = bool(ammo) if ranged is None else bool(ranged)
    weapon = player.ranged_weapon if is_ranged else player.weapon

    def _callback(result):
        chain = effective_chain(player, monster, weapon, result.score, consume=True)

        # Cursed weapon backlash on miss (Tyrfing).
        # Floor at 0 so the player.hp value stays non-negative — downstream
        # code (HUD bars, low-HP buff triggers, is_dead checks) all assume
        # hp >= 0. See bug-bash A7-6.
        if chain == 0:
            if weapon and getattr(weapon, 'cursed_miss_backlash', 0) > 0:
                player.hp = max(0, player.hp - weapon.cursed_miss_backlash)
            # Damoclean counter resets on any miss
            if weapon and getattr(weapon, 'damoclean_counter_threshold', 0) > 0:
                weapon._damoclean_consecutive = 0
            on_complete(0, monster.is_dead(), chain)
            return

        if monster.is_dead():
            on_complete(0, True, chain)
            return


        # The one damage calculation (shared with the combat strip preview).
        damage = strike_damage(player, monster, chain, ranged=is_ranged, ammo=ammo,
                               consume=True, weapon=weapon)
        crit = False      # retired: chain IS the crit (kept for on_complete)

        actual = monster.take_damage(damage)

        # Chain combat v2 (v2.14.0): dispatch per-class chain specials at
        # rung thresholds 5 / 10 / 15 / 20. Applies target statuses, AoE damage,
        # and player buffs per the design doc. AoE hits accumulate into
        # `_chain_aoe_hits` and are exposed via on_complete kwargs so the
        # ranged/melee callers can surface a message.
        _chain_special_result = _apply_chain_class_post_damage(
            player, monster, weapon, chain,
            monsters=getattr(player, '_combat_monsters_ref', None),
            dungeon=None,
            actual=actual,
        )
        _chain_aoe_hits = _chain_special_result.get('aoe_hits', [])

        # Harpe (formerly petrify_on_crit): now fires at chain 15+, applies
        # petrifying 3t. The crit path is gone but the "sickle of the gorgon"
        # identity holds — snake-cutter freezes flesh once the chain matures.
        # C03: bosses, mini-bosses, seal demons, encounter NPCs and
        # outsized foes are far too powerful to petrify, the same rule the
        # wand of stoning follows; petrifying running out KILLS outright, so
        # the direct write used to end any boss two turns later.
        _harpe_stones = False
        if weapon and getattr(weapon, 'petrify_on_crit', False) and chain >= 15:
            from game_magic import _is_big_foe
            if not _is_big_foe(monster):
                _harpe_stones = True
                _cur_pet = int(monster.status_effects.get('petrifying', 0) or 0)
                monster.status_effects['petrifying'] = max(_cur_pet, 3)

        # Sword of Michael (holy_smite_message): when a holy weapon hits a
        # demon/undead/evil-tagged target, surface a dramatic line. This is
        # FLAIR, not damage — the bonus damage is computed above. The line
        # makes the climax FEEL like the angelic blade striking down evil.
        if weapon and getattr(weapon, 'holy_smite_message', False) and actual > 0:
            _gref = getattr(player, '_combat_game_ref', None)
            if _gref is not None:
                _mtags = set(getattr(monster, 'tags', []) or [])
                _is_evil = bool(_mtags & {'demon', 'undead', 'evil'})
                if _is_evil:
                    _mname = getattr(monster, 'name', 'the foe')
                    if monster.kind == 'abaddon_destroyer':
                        _gref.add_message(
                            "The flame of Michael BLAZES! The blade falls upon "
                            "the Destroyer like the wrath of Heaven!",
                            'success')
                    elif monster.is_dead():
                        _gref.add_message(
                            f"Heaven's fire ends the {_mname}. The blade glows brighter.",
                            'success')
                    else:
                        _gref.add_message(
                            f"Holy fire scours the {_mname}!", 'success')

        # Bracers of Cu Chulainn (riastrad_echo): every 3rd hit applies bleed.
        # Counter is on the player; the warp-spasm rises with each strike.
        try:
            from armor_procs import player_has_armor_proc as _pap2
            if actual > 0 and _pap2(player, 'riastrad_echo'):
                player._riastrad_hits = int(getattr(player, '_riastrad_hits', 0)) + 1
                if player._riastrad_hits >= 3:
                    player._riastrad_hits = 0
                    monster.add_effect('bleeding', 5)
        except ImportError:
            pass

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

        # Freeze proc (Aiglos: Gil-galad's spear). Per audit 2026-05-30 —
        # freeze_chance was declared on the unique but had no consumer.
        # Applies 'frozen' status (skip-turn) on a successful hit.
        if weapon and getattr(weapon, 'freeze_chance', 0) > 0 and actual > 0:
            if random.random() < weapon.freeze_chance:
                monster.add_effect('frozen', 3)

        # Weapon-side effects block: {status, effect_chance, effect_duration}.
        # Per audit 2026-05-30 — items.py previously loaded this only on the
        # Accessory class, so the headline status delivery on four quest
        # mythics (vulcans_brand, wendigo_fang, echidna_fang,
        # hunt_captains_sword) was silently dead. Now fires on hit.
        _wfx = getattr(weapon, 'effects', None) if weapon else None
        if _wfx and actual > 0:
            _wfx_status = _wfx.get('status')
            _wfx_chance = float(_wfx.get('effect_chance', 0.0) or 0.0)
            _wfx_dur = int(_wfx.get('effect_duration', 3) or 3)
            if _wfx_status and _wfx_chance > 0 and random.random() < _wfx_chance:
                _wfx_current = monster.status_effects.get(_wfx_status, 0)
                monster.status_effects[_wfx_status] = max(_wfx_current, _wfx_dur)

        # Gae Dearg (engine wave 3): apply_heal_block_chance. The Red Spear's
        # wounds don't heal — apply heal_blocked to target on hit. Default
        # duration 10 turns per the lore.
        _hb_chance = float(getattr(weapon, 'apply_heal_block_chance', 0.0) or 0.0) \
            if weapon else 0.0
        if _hb_chance > 0 and actual > 0 and random.random() < _hb_chance:
            cur = monster.status_effects.get('heal_blocked', 0)
            monster.status_effects['heal_blocked'] = max(cur, 10)

        # Sword of Damocles (engine wave 3): damoclean_counter increment.
        # Counter tracks consecutive successful chain hits. When it crosses
        # the threshold, the NEXT chain-1 attack auto-kills a non-boss
        # target. We track via runtime weapon attribute _damoclean_consecutive.
        _dc_thresh = int(getattr(weapon, 'damoclean_counter_threshold', 0) or 0) if weapon else 0
        if _dc_thresh > 0 and actual > 0:
            # If we're spending an auto-kill this turn (chain==1 + counter ready)
            # the resolution happens lower in `damoclean_check`. Counter still
            # increments per hit.
            weapon._damoclean_consecutive = getattr(weapon, '_damoclean_consecutive', 0) + 1

        # Penitent's Blade (engine wave 3): kill_count_karma_adjust. Every N
        # kills with this weapon, karma improves by +1 (capped at 0 — the
        # blade balances the ledger but can't redeem you). Tracker lives on
        # the weapon.
        _kc_every = int(getattr(weapon, 'kill_count_karma_adjust', 0) or 0) if weapon else 0
        if _kc_every > 0 and monster.is_dead():
            weapon._karma_kill_tally = getattr(weapon, '_karma_kill_tally', 0) + 1
            if weapon._karma_kill_tally % _kc_every == 0:
                # Look up the game via the side-channel ref; fall back if not set.
                _g = getattr(player, '_combat_game_ref', None)
                if _g is not None:
                    # kind 'recovery': only below zero, never above it.
                    import karma as _karma
                    _karma.adjust(_g, 1, kind='recovery', source='penitents_blade')

        # Parashu (engine wave 3): chain_no_reset_on_tag. When killing a
        # matching-tag target, mark the player so the next attack starts at
        # the same chain rung instead of from 1. Combat-side reads
        # _chain_carry to bump chain at the START of the next quiz, but the
        # carry only persists turn-to-turn so it's safe to set here.
        _chain_no_reset = getattr(weapon, 'chain_no_reset_on_tag', None) or [] \
            if weapon else []
        if _chain_no_reset and monster.is_dead():
            for _tg in _chain_no_reset:
                if _tag_match(monster, _tg):
                    player._chain_carry = chain
                    break

        # Meleager's Boar-Spear (engine wave 3): reveal_tag_on_chain_5_kill.
        # At max chain kill of a matching tag, all visible (within sight)
        # matching-tag monsters become marked for the next 5 turns via a
        # player-level set keyed by id.
        _rtag = getattr(weapon, 'reveal_tag_on_chain_5_kill', None) or [] \
            if weapon else []
        if _rtag and monster.is_dead() and weapon:
            _maxc_r = weapon.max_chain_length or len(weapon.chain_multipliers)
            if chain >= _maxc_r:
                for _tg in _rtag:
                    if _tag_match(monster, _tg):
                        _mons_ref = getattr(player, '_combat_monsters_ref', None) or []
                        _marked = getattr(player, '_revealed_tag_ids', set()) or set()
                        for _m in _mons_ref:
                            if _m.alive and any(_tag_match(_m, t) for t in _rtag):
                                _marked.add(id(_m))
                        player._revealed_tag_ids = _marked
                        player._revealed_tag_turns_left = 5
                        break

        # Sword of Damocles (engine wave 3) — auto-kill resolution.
        # If counter reached threshold AND this hit was chain-1 against a
        # non-boss, the blade falls. The counter resets after firing.
        if (weapon and _dc_thresh > 0 and chain == 1 and actual > 0
                and not monster.is_dead()
                and getattr(weapon, '_damoclean_consecutive', 0) >= _dc_thresh
                and 'boss' not in set(getattr(monster, 'tags', []))
                # C04: the gate bosses, seal demons and mini-bosses carry
                # flags, not a 'boss' tag, so the blade one-shot Abaddon.
                and not monster._is_named_foe()):
            extra = max(1, monster.hp)  # finish the job
            extra = monster.take_damage(extra, 'physical')
            actual += extra
            weapon._damoclean_consecutive = 0

        # Curtana (engine wave 4): spare_kill_chance. On a strike that
        # WOULD kill the target, chance to spare instead — leave the
        # monster at 1 HP, grant the player +1 max HP up to the per-floor
        # cap. The Sword of Mercy. Pre-check that the hit would have
        # killed by reading monster.hp BEFORE this resolution — already
        # actual >= monster.hp_before_hit, so check is_dead() post-hit.
        _sp_ch = float(getattr(weapon, 'spare_kill_chance', 0.0) or 0.0) if weapon else 0.0
        if (_sp_ch > 0 and monster.is_dead() and actual > 0
                and random.random() < _sp_ch):
            _per_floor_cap = int(getattr(weapon, 'spare_kill_max_hp_per_floor', 5) or 5)
            _already = int(getattr(weapon, '_spare_kill_floor_hp', 0) or 0)
            if _already < _per_floor_cap:
                # Restore monster to 1 HP and mark it for fleeing-tendency
                monster.hp = 1
                monster.alive = True
                player.max_hp += 1
                player.hp = min(player.max_hp, player.hp + 1)
                weapon._spare_kill_floor_hp = _already + 1
                # Marker for game_combat to print "You spared the foe."
                player._spared_this_attack = True

        # Mjolnir (engine wave 4): chain_lightning_at_chain_n. At chain
        # >= from_chain, splash damage to N adjacent enemies of the
        # primary target. Uses _combat_monsters_ref.
        _cl = getattr(weapon, 'chain_lightning_at_chain_n', None) if weapon else None
        if _cl and actual > 0 and chain >= int(_cl.get('from_chain', 999) or 999):
            _splash_pct = float(_cl.get('splash_pct', 0.5) or 0.5)
            _max_targets = int(_cl.get('max_targets', 1) or 1)
            _splash_dmg = max(1, int(damage * _splash_pct))
            _hit = 0
            _mons_ref = getattr(player, '_combat_monsters_ref', None) or []
            for _m in _mons_ref:
                if _hit >= _max_targets:
                    break
                if (_m is not monster and getattr(_m, 'alive', False)
                        and abs(_m.x - monster.x) <= 1 and abs(_m.y - monster.y) <= 1):
                    _m.take_damage(_splash_dmg, 'lightning')
                    _hit += 1

        # Zulfiqar (engine wave 4): every_hit_secondary_target. Bifurcated
        # tip — every successful hit deals splash damage to one adjacent
        # enemy of the primary target.
        _eh = getattr(weapon, 'every_hit_secondary_target', None) if weapon else None
        if _eh and actual > 0:
            _eh_pct = float(_eh.get('splash_pct', 0.5) or 0.5)
            _eh_range = int(_eh.get('range_tiles', 1) or 1)
            _eh_dmg = max(1, int(damage * _eh_pct))
            _mons_ref = getattr(player, '_combat_monsters_ref', None) or []
            for _m in _mons_ref:
                if (_m is not monster and getattr(_m, 'alive', False)
                        and abs(_m.x - monster.x) <= _eh_range
                        and abs(_m.y - monster.y) <= _eh_range):
                    _m.take_damage(_eh_dmg, 'physical')
                    break  # one adjacent foe per hit

        # Gandiva (engine wave 4): multi_arrow_at_chain_5. At max chain
        # (ranged shots only — gated by `ammo` arg), hit up to N other
        # visible monsters for fractional damage. The hundred-string
        # volley.
        _ma = getattr(weapon, 'multi_arrow_at_chain_5', None) if weapon else None
        if _ma and is_ranged and actual > 0:
            _maxc_ma = weapon.max_chain_length or len(weapon.chain_multipliers)
            if chain >= _maxc_ma:
                _ma_targets = int(_ma.get('targets', 3) or 3)
                _ma_pct = float(_ma.get('damage_per', 0.5) or 0.5)
                _ma_dmg = max(1, int(damage * _ma_pct))
                _hit_ma = 0
                _mons_ref = getattr(player, '_combat_monsters_ref', None) or []
                # Closest-first ordering for narrative satisfaction.
                _sorted = sorted(
                    [m for m in _mons_ref
                     if m is not monster and getattr(m, 'alive', False)],
                    key=lambda m: abs(m.x - player.x) + abs(m.y - player.y),
                )
                for _m in _sorted:
                    if _hit_ma >= _ma_targets:
                        break
                    _m.take_damage(_ma_dmg, 'pierce')
                    _hit_ma += 1

        # Rod of Moses (engine wave 4): chain_tier_status_table. The Ten
        # Plagues by rung — at chain >= key, apply the matching status
        # to the target. Keys are stringified ints (JSON convention).
        _ctst = getattr(weapon, 'chain_tier_status_table', None) if weapon else None
        if _ctst and actual > 0:
            for _key, _entry in _ctst.items():
                try:
                    _need = int(_key)
                except (TypeError, ValueError):
                    continue
                if chain >= _need and isinstance(_entry, dict):
                    _st = _entry.get('status')
                    _dur = int(_entry.get('duration', 3) or 3)
                    if _st:
                        _cur = monster.status_effects.get(_st, 0)
                        monster.status_effects[_st] = max(_cur, _dur)

        # Laevateinn (engine wave 4): boss_doom_dot_at_chain_5. At max
        # chain hit on a boss-tagged target, apply doom_dot status. The
        # status duration encodes the fraction of max-HP/turn — see
        # main turn-tick.
        _bd = getattr(weapon, 'boss_doom_dot_at_chain_5', None) if weapon else None
        if _bd and actual > 0:
            _maxc_bd = weapon.max_chain_length or len(weapon.chain_multipliers)
            _mon_tags = set(getattr(monster, 'tags', []))
            if chain >= _maxc_bd and ('boss' in _mon_tags or getattr(monster, 'is_boss', False)):
                _pct = float(_bd.get('pct_max_hp_per_turn', 0.05) or 0.05)
                _dur = int(_bd.get('duration', 30) or 30)
                # Encode pct in a side-channel on the monster so the tick
                # knows how much to deal. Avoid mutating the status dict.
                monster._doom_dot_pct = _pct
                cur = monster.status_effects.get('doom_dot', 0)
                monster.status_effects['doom_dot'] = max(cur, _dur)

        # Spear of Longinus (engine wave 4): weep_heal_on_kill_scaled.
        # On kill, heal player by (target.max_hp * scale) HP. Charlemagne's
        # spear weeps for the wounds it deals.
        _wh = float(getattr(weapon, 'weep_heal_on_kill_scaled', 0.0) or 0.0) \
            if weapon else 0.0
        if _wh > 0 and monster.is_dead():
            _gain = max(1, int(getattr(monster, 'max_hp', 0) * _wh))
            player.restore_hp(_gain)

        # Sudarshana (engine wave 4): return_to_hand_ward. On chain-5 kill,
        # set player flag — the NEXT monster attack on the player will
        # miss outright (consumed by monster.attack).
        if (weapon and getattr(weapon, 'return_to_hand_ward', False)
                and monster.is_dead()):
            _maxc_rh = weapon.max_chain_length or len(weapon.chain_multipliers)
            if chain >= _maxc_rh:
                player._return_to_hand_active = True

        # Soul Reaver (engine wave 4): growth_on_innocent_kill. Killing a
        # non-hostile NPC (hostile=False / friendly tag / npc tag) grants the
        # player a `blade_flow` stack — the next attack bypasses damage
        # reduction. Chain combat v2 (v2.14.0): rewired from "next hit
        # auto-crit" since crit is retired.
        _mon_tags_inn = set(getattr(monster, 'tags', []))
        _is_innocent = (
            not getattr(monster, 'hostile', True)
            or 'npc' in _mon_tags_inn
            or 'friendly' in _mon_tags_inn
            or 'civilian' in _mon_tags_inn
        )
        if (weapon and getattr(weapon, 'growth_on_innocent_kill', False)
                and monster.is_dead() and _is_innocent):
            _cur_bf = int(player.status_effects.get('blade_flow', 0) or 0)
            player.status_effects['blade_flow'] = _cur_bf + 1

        # Ring of Gyges (gyges_invisible_attack_karma): attacking an NPC
        # while invisible costs -2 karma. The just-man-when-unseen test.
        # Bug-bash fix aac: only fire on an actual hit (actual > 0) — a
        # whiffed swing doesn't reveal moral character.
        if actual > 0 and _is_innocent and getattr(player, 'has_effect', None) and player.has_effect('invisible'):
            for _acc in getattr(player, 'equipped_accessories', ()) or ():
                if getattr(_acc, 'gyges_invisible_attack_karma', False):
                    _g = getattr(player, '_combat_game_ref', None)
                    if _g is not None:
                        import karma as _karma
                        _karma.adjust(_g, -2, kind='cruelty', source='ring_of_gyges')
                        import deeds as _deeds
                        _deeds.note(_g, 'wrong.ring_of_gyges', source='ring_of_gyges',
                                    tags=['vice:cruelty'])
                    break

        # Echidna's Fang (engine wave 4): random_status_from_pool. On hit,
        # roll the chance and apply a random status from the pool.
        _rsp = getattr(weapon, 'random_status_from_pool', None) if weapon else None
        if _rsp and actual > 0:
            _rsp_chance = float(_rsp.get('chance', 0.0) or 0.0)
            _rsp_pool = list(_rsp.get('pool', []) or [])
            _rsp_dur = int(_rsp.get('duration', 5) or 5)
            if _rsp_pool and random.random() < _rsp_chance:
                _pick = random.choice(_rsp_pool)
                _cur_p = monster.status_effects.get(_pick, 0)
                monster.status_effects[_pick] = max(_cur_p, _rsp_dur)

        # Cadmus / Vel / Shamshir (engine wave 4): summon_after_kill_with_tag.
        # On kill matching a tag, set side-channel marker for game_combat
        # to spawn an ally pet. Done as a marker (not direct spawn) because
        # combat.py is leaf and doesn't import pet system.
        _su = getattr(weapon, 'summon_after_kill_with_tag', None) if weapon else None
        if _su and monster.is_dead():
            _su_tag = _su.get('tag', '')
            _su_chance = float(_su.get('chance', 1.0) or 1.0)
            if _su_tag and _tag_match(monster, _su_tag) and random.random() < _su_chance:
                player._pending_summon = {
                    'duration_turns': int(_su.get('duration_turns', 5) or 5),
                    'max_hp_pct': float(_su.get('max_hp_pct', 0.5) or 0.5),
                    'spawn_at': (monster.x, monster.y),
                }

        # Lifesteal mechanic (Soul Reaver)
        healed = False
        lifesteal_pct = float(getattr(weapon, 'lifesteal_percent', 0) or 0)
        # Blood Archon trophy: +5% lifesteal on melee, with or without a
        # weapon. The trophy set this attribute but nothing read it.
        if not is_ranged:
            lifesteal_pct += float(
                getattr(player, '_blood_archon_lifesteal', 0) or 0)
        if lifesteal_pct > 0 and actual > 0:
            heal = max(1, int(actual * lifesteal_pct))
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
                # It grows by GROWING_SHARE of the base it was forged with.
                if not getattr(weapon, '_forged_base', 0):
                    weapon._forged_base = int(weapon.base_damage)
                weapon.base_damage += max(1, int(round(weapon._forged_base * GROWING_SHARE)))

        # Kill max HP bonus (Khopesh of Anubis)
        if monster.is_dead() and weapon and getattr(weapon, 'kill_max_hp_bonus', 0) > 0:
            granted = getattr(weapon, '_max_hp_granted', 0)
            cap = getattr(weapon, 'kill_max_hp_cap', 10)
            if granted < cap:
                bonus = min(weapon.kill_max_hp_bonus, cap - granted)
                player.max_hp += bonus
                player.hp += bonus
                weapon._max_hp_granted = granted + bonus

        # Knockback mechanic (handled by caller via return value; flag via on_complete extra)
        knocked = False
        if weapon and weapon.knockback and actual > 0:
            knocked = True

        # Harpe petrifies at chain 15+ (see above). This flag drives the
        # "is turning to stone!" log line; it used to test the retired
        # `crit`, which is always False, so the line never appeared.
        petrified = bool(_harpe_stones and actual > 0)

        # ---------------------------------------------------------------
        # Class mechanics — fire from template-driven class_mechanic tags
        # (Gap 3). Most check on a successful hit; some on kill or max chain.
        # Heavy weapons rely on these for their "max chain payoff" identity.
        # ---------------------------------------------------------------
        class_mech = getattr(weapon, 'class_mechanic', None) if weapon else None
        if class_mech and actual > 0:
            max_c = (weapon.max_chain_length
                     or len(weapon.chain_multipliers)) if weapon else 5
            at_max = chain >= max_c
            # ---- ALL class-mechanic specials fire at MAX CHAIN ONLY ----
            # (Per developer design call: chain length uniform at 5, all specials
            # gated on max chain regardless of weapon class.)

            # Bleed at max (battleaxe, great_axe via cleave_at_max_plus_bleed)
            if class_mech in ('bleed_at_max', 'cleave_at_max_plus_bleed') and at_max:
                monster.add_effect('bleeding', 4)

            # Stun at max (mace, warhammer-anti-heavy variant, maul)
            if class_mech in ('stun_at_max', 'stun_knockdown_at_max') and at_max:
                # Maul's stun-knockdown is the harder variant (more powerful stun)
                if class_mech == 'stun_knockdown_at_max':
                    resist_thr = min(0.90, max(0.10, monster.max_hp / 250.0))
                    if random.random() > resist_thr:
                        monster.add_effect('paralyzed', 3)
                        stunned = True
                    knocked = True
                else:
                    resist_thr = min(0.95, max(0.05, monster.max_hp / 300.0))
                    if random.random() > resist_thr:
                        monster.add_effect('paralyzed', 2)
                        stunned = True

            # Backstab (dagger, x2 at max chain on an unaware target) is part
            # of strike_damage, so the Strike Now preview shows it too.

            # Disarm at max (scimitar, quarterstaff's reach_disarm)
            if class_mech in ('disarm_at_max', 'reach_disarm') and at_max:
                if random.random() < 0.30:
                    monster.add_effect('paralyzed', 1)

            # Concussion at max (club) — heavy skull blow rattles the brain
            if class_mech == 'concussion_at_max' and at_max:
                if random.random() < 0.35:
                    monster.add_effect('confused', 2)
                    confused = True

            # Quick riposte (shortsword) — arms a counter-attack for next turn
            if class_mech == 'quick_riposte' and at_max:
                player.add_effect('riposte_armed', 2)

            # Returning blow (Green Chapel Axe) — beheading-game contract: max-chain
            # blows return to the wielder for half damage. The Green Knight survives
            # decapitation; the bearer pays the price for swinging too hard.
            if class_mech == 'returning_blow' and at_max:
                backlash = max(1, actual // 2)
                player.hp = max(0, player.hp - backlash)

            # Defensive parry (quarterstaff) — at max chain, gain +2 AC for 2
            # turns. The quarterstaff's defensive identity: master fighters
            # used it to time strikes from a position of safety.
            if class_mech == 'defensive_parry' and at_max:
                cur = player.status_effects.get('parry_armed', 0)
                player.status_effects['parry_armed'] = max(cur, 2)

            # Rapid shot (shortbow) — at max chain, fire a second arrow at the
            # same target for half damage. Mongol horse-archer signature speed.
            if class_mech == 'rapid_shot_at_max' and at_max and not monster.is_dead():
                followup = _rapid_shot_followup(weapon, chain, actual)
                extra = monster.take_damage(followup)
                actual += extra

        # Cleave: max-chain kill triggers AOE to adjacent monsters
        # (greatsword cleave_at_max / great_axe cleave_at_max_plus_bleed)
        _cleave_mech = class_mech in ('cleave_at_max', 'cleave_at_max_plus_bleed')
        _cleave_eligible = _cleave_mech and weapon and chain >= (
            weapon.max_chain_length or len(weapon.chain_multipliers))
        if monster.is_dead() and _cleave_eligible:
            cleave_dmg = max(1, int(actual * 0.5))
            # The adjacent-monster lookup happens at the caller's level (game_combat
            # has the monster list); signal via on_complete kwarg.
            # Caller checks 'cleave_dmg' to apply AoE.
            on_complete(actual, monster.is_dead(), chain, stunned=stunned, knocked=knocked,
                        crit=crit, poisoned=poisoned, burned=burned, confused=confused,
                        petrified=petrified, healed=healed, cleave_dmg=cleave_dmg)
            return

        # Sling ricochet: at max chain, 25% chance to bounce for second hit
        # on a monster adjacent to the original target. Caller handles adjacency.
        _ricochet_dmg = 0
        if class_mech == 'free_stones' and weapon and chain >= (
                weapon.max_chain_length or len(weapon.chain_multipliers)):
            if random.random() < 0.25 and actual > 0:
                _ricochet_dmg = max(1, int(actual * 0.6))
        if _ricochet_dmg:
            on_complete(actual, monster.is_dead(), chain, stunned=stunned, knocked=knocked,
                        crit=crit, poisoned=poisoned, burned=burned, confused=confused,
                        petrified=petrified, healed=healed, ricochet_dmg=_ricochet_dmg)
            return

        on_complete(actual, monster.is_dead(), chain, stunned=stunned, knocked=knocked, crit=crit,
                    poisoned=poisoned, burned=burned, confused=confused, petrified=petrified, healed=healed)

    # Chain combat v2 (v2.15.0): weapons that opt into the polynomial path
    # (`chain_exponent` set) run the chain UNCAPPED here -- it ends on a wrong
    # answer, the timer, or the player pressing SPACE. This unlocks the
    # C10/C15/C20 class-ladder specials in `_apply_chain_class_post_damage`
    # (they used to be dead code because every common template's
    # `chain_multipliers` array capped max_chain at 3-6). Uniques that keep
    # the legacy per-rung array still cap at the array length as before.
    # Unarmed also runs the polynomial at exponent 1.15 (see line 1008), so
    # it belongs on the uncapped path too. Was mistakenly on the array path
    # and capping at 5 — fixed 2026-10-03 after playtest.
    if weapon is None or getattr(weapon, 'chain_exponent', None):
        _max_chain = None  # polynomial path: uncapped, ends on wrong / timer / SPACE
    else:
        _max_chain = weapon.max_chain_length
    # Jormungandr quirk: +1 max chain for repeatedly-equipped weapon
    if _max_chain and weapon:
        if getattr(player, 'quirk_progress', {}).get('jormungandr_weapon_id') == weapon.id:
            _max_chain += 1
    # Chain-equip passive: attack_chain_cap_bonus (Ring of Gawain etc.).
    # Skipped on the polynomial path -- the bonus would only raise a cap that
    # isn't there.
    try:
        from chain_passives import get_attack_chain_cap_bonus
        if _max_chain is not None:
            _max_chain += get_attack_chain_cap_bonus(player)
    except ImportError:
        pass

    # Legacy array-chain uniques can have a finite _max_chain here. Per
    # CHAIN_EFFECTS_PLAN Phase 0 (2026-10-03) they inherit the default
    # `celebrate_on_max=False`, so hitting the array's chain-5 ceiling no
    # longer fires the full-screen MAX CHAIN takeover — Phase 1's per-
    # answer effects provide in-combat feedback instead.
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
    if monsters and any(m is not monster and m.alive and is_at_tile(m, tx, ty)
                        for m in monsters):
        return
    monster.x, monster.y = tx, ty


def can_melee_attack(player, monster) -> bool:
    """Return True if the player's equipped weapon can reach the monster."""
    weapon = player.weapon
    reach = weapon.reach if weapon else 1
    # Ruyi Jingu Bang (engine wave 4): chain_modulated_reach. The cudgel
    # GROWS with the chain. For targeting purposes we use the MAXIMUM
    # reach the weapon could achieve (top entry in the table). Damage
    # ladder still scales per-attack normally.
    _cmr = getattr(weapon, 'chain_modulated_reach', None) if weapon else None
    if _cmr:
        try:
            _max_extension = max(int(v) for v in _cmr.values())
            reach = max(reach, _max_extension)
        except (TypeError, ValueError):
            pass
    if reach < 15:  # melee or polearm
        dx = abs(player.x - monster.x)
        dy = abs(player.y - monster.y)
        return dx <= reach and dy <= reach and not (dx == 0 and dy == 0)
    return False  # ranged weapons handled separately


def can_ranged_attack(player, monster, dungeon) -> bool:
    """Return True if the player can fire a ranged shot at this monster — has
    the weapon, has ammo, and the monster is within reach. Per user 2026-05-30:
    LINE OF SIGHT is NO LONGER required. The player may shoot into darkness or
    down a corridor they can't see; the projectile traces and hits the first
    obstacle along the path. Path-resolution happens at fire time inside
    _confirm_ranged_target (game_combat.py), not here.
    """
    weapon = player.ranged_weapon
    if not weapon or not weapon.requires_ammo:
        return False
    reach = weapon.reach + max(0, player.PER - 10) // 3
    dx = abs(player.x - monster.x)
    dy = abs(player.y - monster.y)
    dist = max(dx, dy)
    if dist > reach:
        return False
    # Check ammo in inventory (skip for infinite-ammo weapons — sling/stones)
    if not getattr(weapon, 'infinite_ammo', False):
        ammo_type = weapon.requires_ammo
        has_ammo = any(
            getattr(i, 'ammo_type', None) == ammo_type
            for i in player.inventory
        )
        if not has_ammo:
            return False
    return True


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
