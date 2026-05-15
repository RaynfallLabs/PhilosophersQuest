---
id: voice-death-screen-cowardice-punches-down
dimension: voice
severity: P1
title: Death screen labels the player a coward after the story popup did the moral work
status: open
systems: [game_render.py (_draw_death_screen), main.py (_STORY_CONTENT)]
evidence:
  - src/game_render.py:2562-2564 — "if self.defeat_reason == 'fled': title_text = 'YOU FLED THE DUNGEON'; sub_text = 'Your quest ends in cowardice.'"
  - src/main.py:3475-3496 (exit_without_stone story popup) — "You ran. Not from monsters. Not from darkness. Not even from death. You ran from the people who needed you most... The village of Amber will not see another spring. You were not overcome by the dungeon. You overcame yourself -- and chose retreat."
discovered: 2026-05-15
---

## The voice clash, spoiler, or flatness

When the player ascends from L1 without the Stone, the flow is: (a) the `exit_without_stone` story popup displays — a beautifully written paragraph that names the moral cost without flinching but also without contempt; (b) the popup is dismissed; (c) the death screen appears, with the title "YOU FLED THE DUNGEON" and the subtitle "Your quest ends in cowardice."

The subtitle is in tonal collision with the story popup. The popup just spent 14 lines doing the moral work with grave, parental seriousness ("You overcame yourself -- and chose retreat"). The death-screen subtitle then summarizes the verdict as "cowardice" — a single labelling word that does what the popup carefully refused to do: name the player rather than the act.

## Why it breaks the register

CONTEXT.md §10 / voice.md severity guide make the encouraging-on-failure rule explicit: "voice that would embarrass a parent showing the game to a kid" is P1. The game is being built for the developer's kids. Calling a 9-year-old who couldn't finish the dungeon a coward — after a 14-line moral lesson already landed — is exactly the failure mode the rubric calls out.

The story popup is the model. It treats the player as a person who made a hard choice with consequences. The death-screen subtitle treats them as a defective player who lost. Two different voices, fired in sequence, on the same event. The geek-dad register is the popup; the subtitle is a Vice City game-over.

The two other death-reason subtitles are correct by comparison:
- `'starved'` → "Hunger claimed you on level {level}." (matter-of-fact, in voice)
- `'died'` → "Slain on dungeon level {level}." (matter-of-fact, in voice)

Only `'fled'` editorializes.

## Suggested rewrite direction

Match the other two subtitles' register — neutral statement of fact. Examples:
- "You climbed back out empty-handed."
- "You returned without the Stone."
- "The quest is incomplete."

The story popup already carries the moral weight; the subtitle's job is to file the run.

## Notes

This is the single most user-facing voice violation found in the audit — the death screen is one of the most-watched screens in any roguelike. Fix removes one line.
