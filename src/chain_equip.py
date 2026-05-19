"""Chain-equip mechanic for legendary unique armor / shields / accessories.

Per the legendary-uniques design (2026-05-18):

  - Most uniques use flat threshold equip + passive bonuses (the default).
  - A small subset of lore-rich pieces (~15 armor/shield, ~9 accessory) use
    chain-equip: equipping triggers an escalator-chain or chain-mode quiz
    instead of threshold. The CHAIN REACHED determines which tier of bonus
    the item grants (1-5).
  - Fresh quiz every equip — no sticky state.
  - JSON shape on the unique:
      "equip_chain_mode": "escalator" | "chain"
      "equip_chain_subject": "geography" | "history" | "math" | ...  (optional)
      "tier_bonuses": {
          "1": {"ac_bonus": 3},
          "2": {"ac_bonus": 4, "resistance_fear": 1},
          ...
      }

This module owns:
  - subject defaulting per item slot
  - applying tier_bonuses[achieved_tier] to the player at equip-time
  - reverting on unequip
  - recognized bonus keys: ac_bonus, resistance_<type>, stat_bonus_<STAT>,
    passive_<flag>, status_<name>, regen_bonus

Other bonus keys are stored verbatim on the item for use-site queries.
"""

from items import Accessory, Armor, Shield


# Default quiz subject per slot family. Overridable via equip_chain_subject.
SLOT_DEFAULT_SUBJECT = {
    'shield': 'geography',
    'head': 'geography',
    'body': 'geography',
    'arms': 'geography',
    'hands': 'geography',
    'legs': 'geography',
    'feet': 'geography',
    'cloak': 'geography',
    'shirt': 'geography',
    'ring': 'history',
    'amulet': 'history',
    'accessory': 'history',
}

# Recognized stat names (for stat_bonus_* keys)
STAT_NAMES = ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER')


def is_chain_equip(item) -> bool:
    """True if the item uses chain-equip (vs flat threshold)."""
    return bool(getattr(item, 'equip_chain_mode', '')) and bool(
        getattr(item, 'tier_bonuses', None))


def get_chain_subject(item) -> str:
    """Quiz subject for this item's chain-equip. Item override > slot default."""
    s = getattr(item, 'equip_chain_subject', '')
    if s:
        return s
    slot = getattr(item, 'slot', '')
    return SLOT_DEFAULT_SUBJECT.get(slot, 'geography')


def get_chain_mode(item) -> str:
    """'escalator' or 'chain'."""
    return getattr(item, 'equip_chain_mode', '')


def get_tier_bonuses(item, tier: int) -> dict:
    """Bonuses for a specific chain rung reached (1-5). Empty dict if no match.

    Item.tier_bonuses keys may be int or str — accept both.
    """
    bonuses = getattr(item, 'tier_bonuses', {}) or {}
    if not bonuses:
        return {}
    if tier <= 0:
        return {}
    return bonuses.get(tier, bonuses.get(str(tier), {})) or {}


def apply_tier_bonuses(player, item, tier: int) -> None:
    """Apply this item's tier_bonuses[tier] to the player + override item fields.

    Mutates player AC/resistance/stat state. Stores tier on item.achieved_tier so
    revert_tier_bonuses can undo on unequip.

    Bonus keys handled here (others stored verbatim on item for use-site):
      ac_bonus           - override item.ac_bonus
      resistance_<type>  - add to player.damage_resistances[type]
      stat_bonus_<STAT>  - player.apply_stat_bonus(STAT, value)
      regen_bonus        - player.regen_bonus += value
      passive_<flag>     - set item._chain_passives[flag] = value (use-site queries)
      status_<name>      - add status to player when equipped
    """
    item.achieved_tier = int(tier)
    bonuses = get_tier_bonuses(item, tier)
    if not bonuses:
        return

    # Stash baseline for revert
    if not hasattr(item, '_chain_baseline'):
        item._chain_baseline = {
            'ac_bonus': getattr(item, 'ac_bonus', 0),
        }
    item._chain_passives = {}
    item._chain_resistances = {}
    item._chain_stat_bonuses = {}
    item._chain_regen = 0
    item._chain_statuses = []

    for key, value in bonuses.items():
        if key == 'ac_bonus':
            # Override (not stack) — tier_bonuses ac_bonus is the FULL ac at this tier
            item.ac_bonus = int(value)
        elif key.startswith('resistance_'):
            rtype = key[len('resistance_'):]
            current = player.damage_resistances.get(rtype, 0) if hasattr(player, 'damage_resistances') else 0
            if hasattr(player, 'damage_resistances'):
                player.damage_resistances[rtype] = current + int(value)
                item._chain_resistances[rtype] = int(value)
        elif key.startswith('stat_bonus_'):
            stat = key[len('stat_bonus_'):]
            if stat in STAT_NAMES:
                player.apply_stat_bonus(stat, int(value))
                item._chain_stat_bonuses[stat] = int(value)
        elif key == 'regen_bonus':
            cur = getattr(player, 'regen_bonus', 0)
            player.regen_bonus = cur + int(value)
            item._chain_regen = int(value)
        elif key.startswith('passive_'):
            flag = key[len('passive_'):]
            item._chain_passives[flag] = value
            # Stat-like passives that need to mutate player state on equip.
            # (Keeping the flag in _chain_passives too lets lookup helpers
            # surface them in tooltips and tests.)
            if flag in ('mp_bonus', 'max_mp_bonus'):
                bonus = int(value)
                player.max_mp = getattr(player, 'max_mp', 0) + bonus
                player.mp = min(getattr(player, 'mp', 0) + bonus,
                                player.max_mp)
                item._chain_mp_bonus = bonus
        elif key.startswith('status_'):
            status_name = key[len('status_'):]
            duration = int(value) if isinstance(value, (int, float)) else 1
            player.status_effects[status_name] = max(
                player.status_effects.get(status_name, 0), duration)
            item._chain_statuses.append(status_name)
        else:
            # Unknown key — stash on item for use-site queries
            item._chain_passives[key] = value


def revert_tier_bonuses(player, item) -> None:
    """Undo the player-side effects of apply_tier_bonuses. Item-side fields
    (ac_bonus override, _chain_passives) reset to baseline.

    Safe to call even if no chain bonuses were applied.
    """
    baseline = getattr(item, '_chain_baseline', None)
    if baseline:
        item.ac_bonus = baseline.get('ac_bonus', getattr(item, 'ac_bonus', 0))

    # Revert resistances
    for rtype, val in getattr(item, '_chain_resistances', {}).items():
        if hasattr(player, 'damage_resistances'):
            current = player.damage_resistances.get(rtype, 0)
            new = current - int(val)
            if new <= 0:
                player.damage_resistances.pop(rtype, None)
            else:
                player.damage_resistances[rtype] = new

    # Revert stat bonuses
    for stat, val in getattr(item, '_chain_stat_bonuses', {}).items():
        if stat in STAT_NAMES:
            player.apply_stat_bonus(stat, -int(val))

    # Revert regen
    regen = getattr(item, '_chain_regen', 0)
    if regen and hasattr(player, 'regen_bonus'):
        player.regen_bonus -= regen

    # Revert mp_bonus / max_mp_bonus
    mp_bonus = getattr(item, '_chain_mp_bonus', 0)
    if mp_bonus and hasattr(player, 'max_mp'):
        player.max_mp = max(0, player.max_mp - mp_bonus)
        player.mp = min(player.mp, player.max_mp)
        item._chain_mp_bonus = 0

    # Drop statuses
    for status_name in getattr(item, '_chain_statuses', []):
        player.status_effects.pop(status_name, None)

    # Clear runtime tracking
    item.achieved_tier = 0
    item._chain_passives = {}
    item._chain_resistances = {}
    item._chain_stat_bonuses = {}
    item._chain_regen = 0
    item._chain_statuses = []
