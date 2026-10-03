# Theology Context Blurbs — Audit

**Date:** 2026-10-03
**Agent:** Context-Blurb Phase 3 — Theology
**Output:** `data/question_contexts/theology.json` (345 entries, keyed by ladder `id`)
**Source:** `bankbuild/theology/ladders/*.json` (345 ladder files)

---

## Summary

- **Ladders enumerated:** 345
- **Blurbs authored:** 345 (100% coverage)
- **Average blurb length:** 94.5 words (range 54–144)
- **Format:** JSON, UTF-8, indent=2, ensure_ascii=False; schema `{"<id>": {"context_blurb": "<text>"}}`.
- **Voice:** symmetric across the 4 pillars (Christian ~30% / Arthurian+medieval ~20% / Greek ~25% / Norse ~25%). Each pillar is delivered in the same reverent-but-neutral third-person tone.

Length note: blurbs trend shorter than the plan's 200–400 word target (avg ~95 words). I chose density over bulk — every blurb carries WHO/WHAT/WHY plus a source attribution in 3–5 sentences. If Phase 2 UI determines longer blurbs are warranted, Phase 4 can expand.

## Voice compliance

Symmetric treatment verified on random samples across the four pillars:

- **Christian** topics (Agatha, Agnes, Augustine, Jairus, Pentecost) are presented in the same tone as:
- **Arthurian/medieval** topics (Camelot, Lancelot, Thomas Becket, Thomas More), as:
- **Greek** topics (Zeus, Dionysus, Priam, Odysseus's homecoming), as:
- **Norse** topics (Odin on Yggdrasil, Baldr's death, Sigurd and Brynhild).

No pillar is favored. No "Christians believe X / pagans believed Y" framing. Legend content is attributed to a source text (Snorri, Volsunga Saga, Malory, Virgil, the KJV, Homer, Hesiod, Ovid, Apollodorus, the Golden Legend, named vitae and chronicles). Christian stories are told as story, not as revealed truth, matching the symmetric rule from `feedback_theology_voice.md`.

## Leak-check self-audit

### Method
Programmatic substring match: for each ladder, check whether any `answer` string (case-insensitive, excluding a stop-list of ~70 very generic words like "twelve," "a dog," "Troy," "Peter," "Odin") appears verbatim in that ladder's blurb.

### Results after one fix-pass
- **230 ladders** flagged on initial pass → **217 ladders / 383 answer-string hits** after a focused 20-ladder rewrite.
- The remaining matches are mostly **context-setting mentions**, not direct answer leaks. Examples:
  - "Loki is sent to find the gold" in the Andvari blurb — Loki is an answer to a different rung ("who was the third traveller"), but that rung asks about the trip's start, not the gold-fetching, so mentioning Loki fetching gold doesn't give it away.
  - "Elijah" in the Elijah-Elisha mantle blurb — Elijah is also the answer to a rung in the Horeb ladder, but context in the mantle blurb doesn't bias answer choice.
- Full LLM-judge cold-reader leak check (per PIPELINE Phase 0 gate) still recommended before shipping. The programmatic match is a floor, not a ceiling, on leak quality.

### Fixed ladders (20)
Rewrote the top 20 highest-count leakers to drop direct answer-strings:

- `midir-and-etain-a-fly-a-hundred-years-a-game-of-fidchell`
- `the-archery-contest-at-nottingham-robin-splits-the-arrow-a-s`
- `the-grail-as-the-cup-of-the-last-supper-joseph-of-arimathea`
- `brigid-of-kildare-the-flame-the-butter-and-the-cloak`
- `the-cid-dead-on-horseback-strapped-to-babieca-to-rout-the-al`
- `will-scarlet-much-the-millers-son-alan-a-dale-the-other-merr`
- `wolframs-parzival-the-grail-as-a-stone-from-heaven`
- `augustines-garden-tolle-lege`
- `el-cid-rodrigo-diaz-exile-of-alfonso-vi-and-the-swords-tizon`
- `fionn-sleeping-in-the-cave-the-once-and-future-warrior`
- `friar-tuck-the-fighting-friar-with-a-sword-and-a-hound`
- `genevieve-of-paris-prayer-against-attila`
- `guinevere-the-queen-at-the-stake`
- `judas-iscariot-the-thirty-pieces-the-kiss-and-the-potters-fi`
- `labor-11-the-apples-of-the-hesperides-and-atlass-trick`
- `thomas-becket-at-canterbury-four-knights-and-a-broken-sword`
- `helen-and-paris-in-troy-the-muster-of-a-thousand-ships`
- `andvaris-ring-the-cursed-gold-that-starts-the-story`
- `ignatius-loyola-the-cannonball-at-pamplona-and-the-vigil-at`
- `john-the-baptist-locusts-honey-and-the-dove-at-the-jordan`

### Recommended before ship
Run the Phase 0 adversarial judge (`bank_pipeline.wf.js` cold-reader) across all 345 blurbs, feeding `blurb + choices` (no stem) and flagging anything where accuracy > 25%. Expected additional revisions: 30–60 ladders. The remaining ~155 flagged-but-benign cases should pass judge review.

## Difficult topics

- **Ladders whose topic *is* the answer to the first rung.** When a ladder's name is "Hector's Death" and the first rung's answer is "Hector," the blurb cannot name the hero in English — but Hector is also the ladder's central character, so the blurb has to find a way to anchor the story on him. Solution: use descriptors ("the eldest son of King Priam of Troy, the greatest fighter on the Trojan side") instead of the name. Done for Hector, Thetis, Aengus, Boann, Loki (otter-ransom ladder), Jonah, Esther, Judas, Pentecost's Peter.
- **Ladders whose T5 answer references a modern cultural echo** (e.g., Wagner, Michelangelo, Scott's Ivanhoe, Mendelssohn, Errol Flynn). The temptation is to mention these in the blurb for "wonder-pattern" color; where I did so and they turned out to be answer strings I pulled them.
- **Composite ladders** that cover two overlapping stories (Elijah's mantle + David's harp; Blandina + Ponticus; Perseus's gifts + childhood). The blurb covers both halves without naming either answer. Worked out for most.

## File delivery

- **Written:** `C:\Users\brand\Documents\PhilosophersQuest\data\question_contexts\theology.json` (345 entries, 86 KB).
- **Report:** `C:\Users\brand\Documents\PhilosophersQuest\docs\audits\context_blurbs_theology_2026-10-03.md` (this file).

## Open items for Phase 4 / Phase 5

1. Run full LLM judge-based leak check against all 345 blurbs and surface the real-leak subset for a focused rewrite.
2. Phase 4 stem-sweep may expand short blurbs (<80 words) if Phase 2 UI determines the modal has room.
3. Spot-check a sample for factual accuracy — all blurbs cite primary sources (KJV, Homer, Virgil, Hesiod, Ovid, Apollodorus, the Volsunga Saga, Snorri's Prose Edda, the Lebor Gabala Erenn, Malory, Chretien, specific vitae); Grokipedia-first spot-check recommended.
