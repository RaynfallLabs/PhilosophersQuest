---
id: code-spell-wand-kills-skip-quirks
dimension: code
severity: P2
title: Wand/spell/AOE kills do not call `qs.on_kill` — most kill-counter quirks unreachable for caster builds
status: open
systems: [quirks, magic, combat]
evidence:
  - src/game_combat.py:1224 — melee callback calls `_qs_rng.on_kill(...)` (ranged)
  - src/game_combat.py:1333 — melee callback calls `_qs_kill.on_kill(...)` (melee)
  - src/game_magic.py:466,480,497,519,538,547,556,568,639,677,686,696,818,828,877,897,916,970,1005,1127,1142,1265,1335,1343,1361,1406,1427,1449,1458,1507,1519,1527,1837,1863,1915 — 35+ wand/spell kill sites call `_on_monster_killed(target)` but NOT `qs.on_kill(...)`
  - src/game_combat.py:1293 — Vidar's Sandal calls `_qs_kill.on_monster_killed(monster.kind)` — but `on_monster_killed` is NOT defined on QuirkSystem (only `on_kill` is)
  - src/quirk_system.py:463-577 — `on_kill` is the canonical hook; tracks Musashi, Valkyrie, Beowulf, Gawain, Cu Chulainn, Kali, Thor, Athena, Caesar, Boudicca, Spartacus, Leonidas, Battle Trance, Death Wish, Life Drain, War Cry (~15 quirks)
verified: true
discovered: 2026-05-15
---

## What's wrong
The quirk system has a per-kill hook `QuirkSystem.on_kill(monster_kind, chain_score, ranged, unarmed, hp_pct_before, is_feared)` that drives ~15 named quirks. It is called correctly from the melee and ranged combat callbacks in `game_combat.py`, but **every wand, spell, and AOE kill path in `game_magic.py` skips it.**

That means a player who specialises in casting Fireball, Meteor, Disintegrate, or any wand effect never accumulates progress toward:
- Musashi (chain-1 kills)
- Valkyrie (25 ranged kills) — partial: bow shots count, wand zaps don't
- Beowulf (10 unarmed wins) — N/A
- Gawain (low-HP kill wins)
- Cu Chulainn (kills while feared)
- Kali (100 kills of same kind)
- Thor (30 combats same weapon) — N/A
- Athena (50 monster types seen) — partial (uses `known_monster_ids` directly, may still update)
- Caesar (300 kills in one run)
- Boudicca (50 kills below 40% HP)
- Spartacus (20 kills while debuffed)
- Leonidas (kill on 30 distinct floors)
- Battle Trance (200 kills)
- Death Wish (kill at ≤10% HP × 10)
- Life Drain (kill at ≤15% HP × 25)
- War Cry (kill while feared × 15)

For a player who builds around science/grammar/philosophy spells, ~15 of the ~80 quirks become unreachable. Combined with `code-quirk-on-quiz-complete-never-called`, the caster build loses access to Apollo + ~15 kill quirks.

Additionally, `game_combat.py:1293` calls `_qs_kill.on_monster_killed(monster.kind)` — but `QuirkSystem` has no method named `on_monster_killed`. Only `on_kill` exists. This raises AttributeError at runtime (silenced by the global `try/except` wrap in `main.main()`'s game loop). The Vidar's Sandal instant-kill of Fenrir thus produces a stack trace but works for the kill itself.

## How to reproduce / where it fires
**Spell kill missing quirk tracking:**
1. Cast Fireball that kills a monster.
2. `_apply_spell_effect` → `mass_fire` → `m.take_damage(scaled)` → `_on_monster_killed(m)`.
3. No `qs.on_kill(m.kind, chain_score, ranged=True, ...)` is fired.
4. Kali counter `kali_kills` stays at 0 for that monster kind.

**Vidar AttributeError:**
1. Equip Vidar's Sandal in inventory.
2. Enter combat with Fenrir, chain ≥ 1.
3. `_callback` at `game_combat.py:1277-1295` instantly kills Fenrir and calls `_qs_kill.on_monster_killed('fenrir_wolf')`.
4. `QuirkSystem` has no `on_monster_killed` method → AttributeError → caught at `main.py:4032`, "Error: ..." in message log.

## Suggested fix
Two fixes needed:

**Fix 1 — Centralise the quirk hook inside `_on_monster_killed`** so every kill path benefits:

```python
# game_combat.py:579 (inside _on_monster_killed)
def _on_monster_killed(self, monster, *, chain_score=0, ranged=False, unarmed=False,
                      hp_pct_before=None, is_feared=False):
    self.level_mgr.monsters_killed += 1
    ...
    qs = getattr(self, 'quirk_system', None)
    if qs:
        qs.on_kill(
            monster_kind=monster.kind,
            chain_score=chain_score,
            ranged=ranged,
            unarmed=unarmed,
            hp_pct_before=hp_pct_before if hp_pct_before is not None
                          else self.player.hp / max(1, self.player.max_hp),
            is_feared=self.player.has_effect('feared'),
        )
```

Then remove the redundant `qs.on_kill(...)` blocks at `game_combat.py:1224` and `1333`. Spell/wand call sites at `game_magic.py:466` etc. continue to call `_on_monster_killed(target)` and the quirk hook fires automatically.

**Fix 2 — Rename the broken call.** Change `game_combat.py:1293`:
```python
_qs_kill.on_monster_killed(monster.kind)
```
to:
```python
_qs_kill.on_kill(
    monster_kind=monster.kind, chain_score=1, ranged=False,
    unarmed=False, hp_pct_before=getattr(self, '_combat_hp_pct_before', 1.0),
    is_feared=self.player.has_effect('feared'),
)
```
or simply delete the line if Fix 1 is applied (the `_on_monster_killed` call earlier on line 1290 already triggers the hook).

## Notes
The exception swallowing at `main.py:4032` is masking the Vidar AttributeError — it shows up in the message log as `Error: ...` and aborts the rest of `_advance_turn` (no monster turn that round). Players who triggered the Fenrir instant-kill probably noticed the visible error but couldn't diagnose it.
