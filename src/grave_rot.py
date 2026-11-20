"""Grave Rot: a sickness that stops the wound closing (AI-1, grave_rot,
2026-11-19).

`diseased` cost the hero a point of STR or CON about one bite in three
and no health, and was gone in 4-8 turns; on a monster it ticked 0.4% of
its health a turn. The rubric told data writers it ticked 2% a turn.

Lore and AD&D: disease is the wound that will not heal (mummy rot: no
healing until it is cured; the ghoul's grave-filth; the plague). Now:

  * on the hero: while diseased his wounds do not mend by rest (natural
    regeneration stops, main._tick_hp_regen) and every heal does half
    (Player.restore_hp); the stat sap stays. A disease a monster gives
    lingers: its kind's own `effect_duration` x linger (10), at most the
    engine's cap on a status (60 turns), so a rat's bite is short and a
    mummy's long, and it reaches the next fight;
  * on a monster (a wand of disease, the hero's plague): it loses a share
    of its health every turn (poison's rate) and cannot regenerate while it
    lasts (a sick troll does not mend).

Cured by a Potion of Cure Disease, the Mercy prayer at a chain of 4, the
physician's Cure, the poison_resist and drain_resist statuses (which block
it), a fountain's best water. Pure module.
"""
from __future__ import annotations

import kind_data

ENABLED = True          # the simulator's ai_rot knob (0 = the old rule)


def rules() -> dict:
    return kind_data.rules('grave_rot')


def linger(duration: int) -> int:
    """How long a monster's disease lasts on the hero."""
    if not ENABLED:
        return int(duration)
    from status_effects import MAX_EFFECT_DURATION
    r = rules()
    cap = min(int(r.get('cap', MAX_EFFECT_DURATION)), MAX_EFFECT_DURATION)
    return max(1, min(cap, int(duration) * int(r.get('linger', 10))))


def sick(player) -> bool:
    has = getattr(player, 'has_effect', None)
    return bool(ENABLED and has is not None and has('diseased'))


def blocks_regen(player) -> bool:
    """No mending by rest while the sickness is in the wound."""
    return sick(player)


def heal_amount(player, amount: int) -> int:
    """What a heal of ``amount`` gives a sick hero: half (at least 1)."""
    if amount > 0 and sick(player):
        return max(1, int(amount) // 2)
    return amount


def monster_tick(m, poison_divisor: int, rng=None) -> None:
    """One turn of a disease on a monster (Monster.tick_effects)."""
    import random
    rng = rng or random
    if not ENABLED:
        if rng.random() < 0.08:                    # the old rule
            m.take_damage(max(1, m.max_hp // 20))
        return
    m.take_damage(max(1, m.max_hp // m._dot_divisor(poison_divisor)))


def blocks_monster_regen(m) -> bool:
    return bool(ENABLED and m.has_effect('diseased'))
