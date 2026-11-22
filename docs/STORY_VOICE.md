# The story voice

**Ruling (Brandon, 2026-11-21):** "I want it to be more like high fantasy story telling, not whatever AI 'impact writing' you've been using. This should be true for all story items, including intro and finale, as well as lore entries... Journal entries should be brief and short, notes an adventurer leaves for himself."

The quiz banks keep their own voice (`docs/quiz/HOUSE_VOICE.md`). This file governs the intro, boss tales and endings, the Road and every other encounter, lore entries, short flavour lines, and the Journal.

The reference text is `Game._STORY_CONTENT` in `src/main.py`.

## Two voices

1. **The teller of the tale** speaks everywhere but the Journal. He tells an old tale beside a fire: unhurried, grave, warm, in love with names, lineages and places.
2. **The adventurer** writes the Journal, hurriedly, for his own eyes.

## The teller of the tale

- **Tell it, do not punch it.** Use whole sentences that carry the story forward, joined by "and", "for", "until", "yet", "so that". Vary their length, and let the long ones breathe.
- **Say what happened and why.** The reader should never have to work out an event from a hint or a wink.
- **End on the consequence**, what came of it or where it leads, inside a full sentence.
- **An older diction, easily read by a 15-year-old:** "the folk of Amber", "in the elder days", "he would not be comforted". No "thee" or "thou" except from a speaker who would truly use them, and never more than a touch of inversion.
- **Speech belongs to the speaker.** Lords, saints and spirits speak in full and courteous sentences. Plain folk speak plainly and warmly, but still in sentences. A goblin may keep his broken speech.
- **Lore is a legend retold.** Open on the person, the creature or the age, not on a citation ("In Irish belief..."). Say who made or bore the thing and what befell him. A source may be named as a teller ("the old poets tell").
- **Tense.** Lore and tales are in the past. An encounter keeps the present and "you", because the choice is still to be made.

## Never

| The tic | Example, as it was | In place of it |
|---|---|---|
| The clincher: a short last line for effect | "He ran faster." / "It works once." | End the telling, with the fact inside a sentence |
| Fragments and drumbeats | "Descend. Claim the Stone." | "Go down with a stout heart... and win the Stone" |
| The negation reveal | "Not from monsters. Not from darkness." | Say what was so |
| The inverted echo | "But you are not no one." / "He knows you are lying, and you know he knows." | Say it once |
| The lone line for drama | "You ran." | A paragraph that tells it |
| The stated theme | "It is a statement about the nature of wisdom itself" | Let the deed show it |
| The wink, the deadpan | "and they are not interested in the lesson" | Tell what the guards did |
| The camera | "His hands won't stop shaking. He stares at his hands." | "He trembles as he lifts his face to you" |
| The aphorism as a hint | "Up is not always away." | A plain hint, gently put |
| A double dash for a beat | "Death writhes -- and is consumed." | A comma, or "and" |

## The Journal

A note the adventurer leaves for himself, to be understood a week later.

- **Aim at 25 to 70 characters, and never over 100.** One or two clipped clauses.
- **Who, what, and what is still to do:** "Fed Pell, a deserter. His company is trapped in the granary below."
- Drop "I" where it can go. Keep every name, place, debt, promise and clue that matters later.
- A bare "Must", "Owe" or "Beware" note is good. No jokes, no feelings explained, no morals, no scene, no closing quip.
- The lint still holds (`chronicle.lint`): no digits, floor numbers, game terms, stat names, exclamation marks, ellipses or double dashes.

## What a rewrite never changes

- Facts, names, outcomes, promises, clues and the mechanics a line gives away (a weakness, "works once").
- `{placeholders}`, and any sentence the code or the validator matches (an option's `warning` must appear in its scene's text).
- Plain mechanical text: What It Does, tells' counters, labels, help. These stay plain and short.
- They and them are plural only. Every individual is he, she or it.
- The easter eggs' own jokes and speakers (songs, the Duck, quoted films).
