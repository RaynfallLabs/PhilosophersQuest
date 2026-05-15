---
id: fun-quirk-meta-loop-strength
dimension: fun
severity: P3
title: Quirk unlock cadence is the strongest meta-loop, but some unlock thresholds are silently un-fun
status: open
systems: [quirks, meta_progression, save_system]
when_it_hits: "Across runs — the meta-game progression curve"
evidence:
  - src/quirk_system.py:1097-1199
  - src/main.py:2702-2714
  - fun_pacing_trace.md#quirks-as-a-meta-loop
discovered: 2026-05-15
---

## The friction or flatness
Quirks are the game's strongest meta-loop. A run that unlocks a new quirk feels successful even if the player died at floor 8. The unlock screen (`w` key) shows progress toward 80+ named beats, and each unlock is a mythological / historical reference that hooks the kid into looking up "who was Cassandra?" or "what did Beowulf do?"

Most quirk thresholds are well-tuned for steady drip:
- Theseus (5 floors explored) — fires turn 200 of run 1.
- Cassandra (10 lockpick fails) — fires when the lockpick learning curve frustrates.
- Norns (20 Recall Lore uses) — fires after a player has internalized the lore loop.

But several quirks have **silently grindy thresholds** that work against the cadence:

- **Cerberus** (300 stair uses) — at ~5 stair uses per run, this needs **60 runs**. The thematic flavor (the three-headed dog guards transitions) is great, but the threshold ages out the player.
- **Buddha** (500 turns waiting near monsters) — requires the player to *intentionally do nothing*. A reasonable mythological gesture but a deeply boring action loop.
- **Ahasverus** (15000 tile moves) — pure grind. Wandering Jew is a powerful myth but the unlock is "walk a long way."
- **Caesar** (300 kills) — at ~80-150 kills per full run, this is 2-3 full deep runs.
- **Boudicca** (50 kills) — fine if you do it across runs, but kills don't accumulate across runs only progress does (`quirk_system.py`'s `quirk_progress` is on the player, written to save state).
- **Penelope** (100 successful answers in a row without a wrong one) — extraordinarily punishing under wander-spawn pressure.

The deeper issue: **some quirks "should" be celebrated mid-run revelations** ("you waited still while monsters approached — you have learned stillness, the Buddha's gift") but **end up as tracked-progress numbers that the player has no in-run feedback about.** The quirks screen shows progress, but the player has to *check it* to see — there's no in-flight celebration of "10/500 turns waited" or similar.

## When and how often it fires
- Every run for the first 20-30 runs. The unlock pace is roughly: 2-4 quirks per run early on, decaying to 1 quirk per 2-3 runs as low-hanging fruit gets picked.
- Eventually a player has unlocked maybe 40-50 quirks and the remaining 30 are mostly the high-threshold grinders.

## Suggested redirect
- **Surface micro-progress in messages**: every ~25% of progress toward a quirk threshold, emit an unobtrusive message. "You feel a faint thread of fate tightening — 25/100 mystery answers in a row." This makes the meta-loop *visible* in-run.
- **Re-tune the 5-10 highest grind thresholds** down by half. Cerberus at 150 stair uses (~30 runs) is still steep but viable. Ahasverus at 7500 tiles. Caesar at 200 kills.
- **Add a "next quirk to unlock" indicator** on the run-end screen. After death, before the highscore display, show "Your next quirk: Theseus, 80% complete. One more floor explored."
- **Reward the player on quirk unlock with a chronicle line**: the unlock should produce a `_log_chronicle` entry tied to the named myth. "Unlocked Sisyphus' Mastery. The stone rolls easier now."

## Notes
This is the strongest meta-loop in the game. The finding isn't "quirks are broken" — it's "the cadence has gaps in the high-threshold band, and the in-run feedback is thin." Spans the quirk system + the chronicle + the run-end UX. Fixing this lifts the "I want to play again" hook for the player population that's already past the easy quirks.
