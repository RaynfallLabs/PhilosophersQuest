"""Runtime HUD data helpers.

The drawing layer should stay boring: it receives already-filtered rows with
display-safe labels, status text, and rarity colors. Keeping this logic pure
also lets tests verify identification and spawn-depth coloring without Pygame.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

from game_helpers import fix_name_case


RED = (255, 70, 80)
NEUTRAL = (226, 218, 190)
GREEN = (70, 255, 118)


@dataclass(frozen=True)
class ContextRow:
    label: str
    meta: str
    color: tuple[int, int, int]
    distance: int


@dataclass(frozen=True)
class PowerRow:
    label: str
    status: str
    state: str  # ready | cooldown | uses


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def spawn_fit_score(dungeon_level: int, peak_floor: int, spread: int = 10,
                    *, kind: str) -> float:
    """Return -1..1 where positive is good for the player.

    Items: above-depth treasure is good, stale low-depth loot is bad.
    Monsters: above-depth enemies are bad, stale weak enemies are good.
    """
    if not peak_floor:
        return 0.0
    scale = max(4.0, min(18.0, float(spread or 10)))
    score = (float(peak_floor) - float(dungeon_level)) / scale
    if kind == "monster":
        score = -score
    if not isfinite(score):
        return 0.0
    return max(-1.0, min(1.0, score))


def spawn_fit_color(dungeon_level: int, peak_floor: int, spread: int = 10,
                    *, kind: str) -> tuple[int, int, int]:
    score = spawn_fit_score(dungeon_level, peak_floor, spread, kind=kind)
    if score < 0:
        return _mix(NEUTRAL, RED, -score)
    return _mix(NEUTRAL, GREEN, score)


def item_known_to_player(player, item) -> bool:
    if not hasattr(item, "identified"):
        return True
    try:
        if bool(getattr(item, "identified", False)):
            return True
    except Exception:
        pass
    knows = getattr(player, "knows_item_type", None)
    if callable(knows):
        try:
            return bool(knows(item))
        except Exception:
            return False
    return getattr(item, "id", None) in getattr(player, "known_item_ids", set())


def hud_item_name(player, item, *, include_count: bool = False) -> str:
    known = item_known_to_player(player, item)
    raw = getattr(item, "name", "item") if known else getattr(item, "unidentified_name", getattr(item, "name", "item"))
    base = fix_name_case(str(raw))
    buc = getattr(item, "buc", "uncursed")
    if getattr(item, "buc_known", False) and buc != "uncursed":
        base = f"{{{buc}}} {base}"
    count = int(getattr(item, "count", 1) or 1)
    if include_count and count > 1:
        return f"{base} x{count}"
    return base


def _distance(player, obj) -> int:
    return abs(int(getattr(obj, "x", 0)) - int(getattr(player, "x", 0))) + \
        abs(int(getattr(obj, "y", 0)) - int(getattr(player, "y", 0)))


def _distance_label(dist: int) -> str:
    return "here" if dist <= 0 else f"{dist}t"


def _monster_visible(monster, visible: set[tuple[int, int]]) -> bool:
    fw, fh = getattr(monster, "footprint", (1, 1))
    try:
        fw, fh = int(fw), int(fh)
    except Exception:
        fw, fh = 1, 1
    x, y = int(getattr(monster, "x", 0)), int(getattr(monster, "y", 0))
    for dy in range(max(1, fh)):
        for dx in range(max(1, fw)):
            if (x + dx, y + dy) in visible:
                return True
    return False


def visible_context_rows(player, monsters: Iterable, ground_items: Iterable,
                         visible: set[tuple[int, int]], dungeon_level: int,
                         *, max_monsters: int = 6, max_items: int = 6
                         ) -> tuple[list[ContextRow], list[ContextRow]]:
    monster_rows: list[ContextRow] = []
    item_rows: list[ContextRow] = []

    for monster in monsters:
        if not getattr(monster, "alive", False):
            continue
        if getattr(monster, "is_allied", False):
            continue
        if not _monster_visible(monster, visible):
            continue
        dist = _distance(player, monster)
        peak = int(getattr(monster, "peak_floor", 0) or getattr(monster, "min_level", 0) or 0)
        spread = int(getattr(monster, "spread", 10) or 10)
        monster_rows.append(ContextRow(
            fix_name_case(str(getattr(monster, "name", getattr(monster, "kind", "monster")))),
            _distance_label(dist),
            spawn_fit_color(dungeon_level, peak, spread, kind="monster"),
            dist,
        ))

    for item in ground_items:
        if (int(getattr(item, "x", 0)), int(getattr(item, "y", 0))) not in visible:
            continue
        dist = _distance(player, item)
        peak = int(getattr(item, "peak_floor", 0) or getattr(item, "min_level", 0) or 0)
        spread = int(getattr(item, "spread", 10) or 10)
        item_rows.append(ContextRow(
            hud_item_name(player, item, include_count=True),
            _distance_label(dist),
            spawn_fit_color(dungeon_level, peak, spread, kind="item"),
            dist,
        ))

    monster_rows.sort(key=lambda row: (row.distance, row.label))
    item_rows.sort(key=lambda row: (row.distance, row.label))
    return monster_rows[:max_monsters], item_rows[:max_items]


def _cooldown_row(label: str, cooldown: int) -> PowerRow:
    cd = int(cooldown or 0)
    return PowerRow(label, "ready" if cd <= 0 else f"{cd}t",
                    "ready" if cd <= 0 else "cooldown")


def active_power_rows(player, *, secret_build: dict | None = None,
                      heavenly_host_active: bool = False) -> list[PowerRow]:
    rows: list[PowerRow] = [
        _cooldown_row("Prayer", getattr(player, "prayer_cooldown", 0)),
        _cooldown_row("Recall Lore", getattr(player, "recall_lore_cooldown", 0)),
    ]
    if (getattr(player, "hack_reality_count", 0) > 0
            or getattr(player, "hack_reality_cooldown", 0) > 0
            or getattr(player, "hack_tiers_claimed", set())):
        rows.append(_cooldown_row("Hack Reality", getattr(player, "hack_reality_cooldown", 0)))

    try:
        from quirk_system import _ACTIVE_POWER_DEFS
    except Exception:
        _ACTIVE_POWER_DEFS = {}
    unlocked = getattr(player, "unlocked_quirks", set()) or set()
    uses = getattr(player, "power_uses", {}) or {}
    cooldowns = getattr(player, "power_cooldowns", {}) or {}
    for pid, pdef in _ACTIVE_POWER_DEFS.items():
        if pid not in unlocked:
            continue
        label = pdef.get("label", pid.replace("_", " ").title())
        if int(pdef.get("uses", 0) or 0) > 0:
            remaining = int(uses.get(pid, 0) or 0)
            if remaining > 0:
                rows.append(PowerRow(label, f"{remaining} use" + ("" if remaining == 1 else "s"), "uses"))
        else:
            rows.append(_cooldown_row(label, int(cooldowns.get(pid, 0) or 0)))

    inventory = list(getattr(player, "inventory", []) or [])
    if any(getattr(item, "id", "") == "charmander_stuffie" for item in inventory):
        rows.append(_cooldown_row("Fire Breath", int(cooldowns.get("stuffie_fire_breath", 0) or 0)))
    if any(getattr(item, "id", "") == "dreamspun_sketchbook" for item in inventory):
        rows.append(_cooldown_row("Manifest", int(cooldowns.get("sketch_manifest", 0) or 0)))
    if any(getattr(item, "id", "") == "gleipnir" for item in inventory):
        rows.append(PowerRow("Bind Odinkiller", "ready", "ready"))
    if (any(getattr(item, "id", "") == "scales_of_michael" for item in inventory)
            and not heavenly_host_active):
        rows.append(PowerRow("Heavenly Host", "1 use", "uses"))

    if (secret_build or {}).get("_elder_blood"):
        for pid, label in [("elder_blink", "Blink"), ("elder_charge", "Charge"), ("elder_scream", "Scream")]:
            rows.append(_cooldown_row(label, int(cooldowns.get(pid, 0) or 0)))

    for special in getattr(player, "hero_specials", []) or []:
        sid = special.get("id")
        if sid:
            cd = int(getattr(player, "hero_special_cooldowns", {}).get(sid, 0) or 0)
            rows.append(_cooldown_row(str(special.get("name", sid)), cd))

    for armor in getattr(player, "armor_slots", []) or []:
        if armor and getattr(armor, "seven_league_step", False):
            if not getattr(player, "_seven_league_used_this_floor", False):
                rows.append(PowerRow("Seven-League Step", "1 use", "uses"))
            break
    for armor in getattr(player, "armor_slots", []) or []:
        if armor and getattr(armor, "gold_offering", False):
            if not getattr(player, "_gold_offering_used_this_floor", False):
                rows.append(PowerRow("Gilgamesh's Bribe", "1 use", "uses"))
            break

    for acc in getattr(player, "equipped_accessories", []) or []:
        charges = int(getattr(acc, "charges", 0) or 0)
        if getattr(acc, "use_charged", False) and charges > 0:
            aid = getattr(acc, "id", "")
            if aid == "lyre_of_orpheus":
                label = "Play the Lyre"
            elif aid == "hand_of_glory":
                label = "Light the Hand"
            else:
                label = hud_item_name(player, acc)
            rows.append(PowerRow(label, f"{charges} charge" + ("" if charges == 1 else "s"), "uses"))

    try:
        import class_system as _cs
    except Exception:
        _cs = None
    class_defs = {
        "second_wind": "Second Wind",
        "arcane_recovery": "Arcane Recovery",
        "evasion": "Evasion",
        "turn_undead": "Turn Undead",
    }
    if _cs is not None:
        for ability_id in getattr(player, "class_abilities", []) or []:
            label = class_defs.get(ability_id)
            if label and _cs.ability_charge_available(player, ability_id):
                rows.append(PowerRow(label, "1 use", "uses"))
    return rows
