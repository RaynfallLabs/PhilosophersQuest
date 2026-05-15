---
id: voice-status-effect-expire-flat
dimension: voice
severity: P2
title: Status-effect expire and DOT messages are functional but generic; one tier below the body-aware chronicle
status: open
systems: [status_effects.py, game_combat.py (combat log adjacent)]
evidence:
  - src/status_effects.py:235 — "'teleportitis': ('The teleportation urge fades.', 'info')"
  - src/status_effects.py:240 — "'telepathy': ('Your telepathy fades.', 'info')"
  - src/status_effects.py:241 — "'warning': ('Your danger sense fades.', 'info')"
  - src/status_effects.py:226 — "'confused': ('Your mind sharpens. Confusion gone.', 'info')"
  - src/status_effects.py:357 — "messages.append(('The doom curse gnaws at your life force!', 'danger'))"
  - src/status_effects.py:339-347 (petrify, well-done counterexample) — "'Your limbs are rigid -- death is moments away!'", "'Your skin is hardening into stone!'", "'You feel yourself stiffening...'"
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

The `_EXPIRE_MSGS` dict at `status_effects.py:222-272` carries ~45 expire messages. Most are dry-functional: "Your telepathy fades.", "Your danger sense fades.", "Your spell turning aura dissipates.", "Your reflective aura fades." These work as bookkeeping but read as system notifications. They are some of the most-frequent player-facing strings in the game — every time a 10–30 turn effect runs out, one of these fires.

The DOT messages have similar drift: "The poison burns through you!", "You are bleeding!", "You are on fire!" — better than the expire pool but still inconsistent. The petrify progression (`status_effects.py:339-347`) is the model: three staged messages with mounting horror ("...stiffening" → "...skin is hardening into stone" → "...limbs are rigid — death is moments away"). That's the register the rest of this surface should match.

## Why it breaks the register

The chronicle voice samples are body-aware: "I felt it before I saw it.", "The silence afterwards was the loudest thing I've ever heard.", "I died. I felt it — the cold, the nothing. Then warmth." Status effects are *also* body experiences — a poison wearing off, regen kicking in, blindness lifting. The register has been demonstrated to be writeable; the surface just hasn't been brought up to it.

Compare two adjacent expire messages:
- `'cursed': ('The curse lifts.', 'success')` — fine, terse, in voice.
- `'displacement': ('Your displacement aura fades.', 'info')` — RPG-statblock with the word "aura" doing tutorial labor.

The disparity tells the player different writers wrote different effects.

## Suggested rewrite direction

Targeted rewrite of the flattest ~15 expire entries. Examples:

- `displacement` → "The world stops blurring around you."
- `telepathy` → "The minds nearby go quiet again."
- `warning` → "Your skin stops prickling. The dungeon is just stone again."
- `searching` → "You stop noticing the cracks in the walls."
- `clairvoyant` → "The far rooms slip back into darkness."
- `reflecting` → "The shimmer over your skin settles."
- `phasing` → "You feel the wall when you brush it."
- `spell_turning` → "Spells will land again now."

Same length budget, same trigger; just body-aware verbs in place of "aura fades" / "X gone." This brings the surface to ~4/5 without expanding any string.

## Notes

`status_effects.py:339-347` (petrify) and `status_effects.py:325-328` (disease + STR/CON drain) are the in-house examples to imitate. Voice is achievable here — it's been done in the same file.
