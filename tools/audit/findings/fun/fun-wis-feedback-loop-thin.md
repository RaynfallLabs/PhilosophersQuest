---
id: fun-wis-feedback-loop-thin
dimension: fun
severity: P3
title: WIS stat advertises a quiz-timer bonus but the per-point value (+0.8-1.7s per subject) is too granular to feel
status: open
systems: [stats, quiz_timer, character_growth]
when_it_hits: "Every quiz — but especially apparent when comparing same-build outcomes across runs"
evidence:
  - src/player.py:12-30
  - src/player.py:291-296
  - src/main.py:2171-2178
  - fun_pacing_trace.md#foundational-tempos
discovered: 2026-05-15
---

## The friction or flatness
The WIS stat is one of six core stats and the only one that directly affects quiz interaction. Per `SUBJECT_TIMER` (`player.py:12-30`), each subject has a `(base_seconds, wis_scale)` pair. For example:

- Math: 8 + WIS × 0.8 → WIS 10 = 16s, WIS 15 = 20s (+4s)
- Theology: 48 + WIS × 1.7 → WIS 10 = 65s, WIS 15 = 74s (+9s)

A WIS increase of +5 points (a significant investment, several cooked stat-boost meals worth) adds roughly +4 to +9 seconds *per question* depending on the subject. This is real time but **subjectively imperceptible** mid-quiz — when you're staring at a question with 16 seconds on the clock, knowing it was previously 12 seconds doesn't change the experience much.

Compare to other stats whose effects are vivid:
- **STR** → +5 carry capacity per point. Player feels this immediately (can pick up more, fewer "too heavy" warnings).
- **CON** → +1 max HP per point. Numbers grow on the sidebar.
- **DEX** → +1 AC per 2 points. Monsters miss noticeably more often.
- **INT** → +1 max MP per point, plus magic damage scaling.
- **PER** → +1 sight radius per 2 points. The map opens up *visibly*.

**WIS's reward — slightly longer to read — is the only one that's invisible to the player.** It manifests only as "I had a tiny bit more time on that question I just answered." There's no UI counter, no animated improvement, no sidebar number that visibly grows.

Additionally: WIS unlocks the **L30+ BUC auto-reveal at WIS 14** (`main.py:2171-2178`). This is a great threshold reward — but it fires *once* per item pickup and is silent until the player hits the threshold. A player who has WIS 13 doesn't know they're one stat point from a major QoL bump.

WIS is also the stat the game's *theming* hammers hardest — the entire game is about wisdom. The mythological inner-meaning is rich. But the mechanical pull is thin: stat-boost-from-cooking is random, and a player can't *choose* WIS without sacrificing other progress.

## When and how often it fires
- Every run. Every quiz answer is shaped by WIS. But the *feedback* on WIS investment is silent.
- Players who push WIS via cooking won't *feel* the payoff per point. Most will switch to other stats by L30.

## Suggested redirect
- **Sidebar WIS indicator**: show current quiz timer at the top of the sidebar, with WIS contribution explicitly broken out: "Quiz timer: 16s (base 8s + WIS 10 × 0.8 = 16s)." Players see the math at a glance.
- **Threshold rewards beyond BUC auto-reveal**: WIS 12 = "your wisdom helps you sense hidden corridors" (passive search bonus). WIS 14 = BUC auto-reveal at L30+. WIS 16 = "you hear monsters before you see them" (warning radius +2). WIS 18 = "the gods are pleased; +1 chain on every prayer."
- **WIS-themed encounter or quirk gates**: NPC dialogue branches that only fire at WIS ≥ N, unlocking knowledge tier rewards.
- **Visual: timer bar gets a faint "WIS glow"** at high WIS values — purely aesthetic, but communicates "you have time, you are wise."

## Notes
This isn't a balance issue — WIS *works* mechanically. It's a feedback-loop issue: the most thematically loaded stat in the game has the weakest visible reward. Spans stats + quiz timer + sidebar UX + character growth.
