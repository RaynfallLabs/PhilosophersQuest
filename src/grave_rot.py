"""Grave Rot: a sickness that stops the wound closing (AI-1, grave_rot,
2026-11-19).

`diseased` cost the hero a point of STR or CON about one bite in three
and no health, and was gone in 4-8 turns; on a monster it ticked 0.4% of
its health a turn. The rubric told data writers it ticked 2% a turn.

Lore and AD&D: disease is the wound that will not heal (mummy rot: no
healing until it is cured; the ghoul's grave-filth; the plague). Now:

  * on the hero: while diseased his wounds do not mend by rest (natural
    regeneration stops, main._tick_hp_regen) and every heal that goes through
    Player.restore_hp (potions, wands, spells, prayers, meals) does half
    (Player.restore_hp); the stat sap stays. How long a monster's disease
    lasts is the kind's own: its rider's `effect_duration`, times its
    `disease_linger` where its lore makes the sickness one that lingers
    (mummy rot 10, the plague-bringers 4-8; a rat's bite or a zombie's claw
    keeps its own few turns), at most the engine's cap on a status (60);
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


def linger(m, duration: int) -> int:
    """How long a monster's disease lasts on the hero: its own turns, times
    its kind's `disease_linger` (1 unless its lore says the sickness
    lingers), at most the cap."""
    if not ENABLED:
        return int(duration)
    from status_effects import MAX_EFFECT_DURATION
    r = rules()
    cap = min(int(r.get('cap', MAX_EFFECT_DURATION)), MAX_EFFECT_DURATION)
    times = 1 if kind_data.named(m) else int(
        kind_data.field(m, 'disease_linger', r.get('default_linger', 1)) or 1)
    return max(1, min(cap, int(duration) * max(1, times)))


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


# ---------------------------------------------------------------------------
# A heal's line says what was healed: restore_hp gives less than it was
# asked for to a sick hero, to one whose wounds will not close and to one
# who had few to close.
# ---------------------------------------------------------------------------

def _blocked(player) -> bool:
    has = getattr(player, 'has_effect', None)
    return bool(has is not None and has('heal_blocked'))


def told(player, got: int, line: str) -> str:
    """A heal's ``line``, its {n} the health really gained."""
    if got > 0:
        return line.replace('{n}', str(got))
    return "Your wounds refuse to close." if _blocked(player) else "You have no wounds to close."


def whole(player, line: str) -> str:
    """A ``line`` that calls the hero whole, said only when he is."""
    if player.hp >= player.max_hp:
        return line
    if _blocked(player):
        return "Your wounds refuse to close."
    if sick(player):
        return "Your wounds close only part of the way: you are Diseased."
    return "Your wounds close only part of the way."


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
