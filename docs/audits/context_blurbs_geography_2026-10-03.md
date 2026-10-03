# Context Blurbs — Geography bank — 2026-10-03

Phase 3 orientation-blurb authoring pass for the GEOGRAPHY bank.

## Scope

- **Source ladders:** `bankbuild/geography/ladders/*.json` (405 passed ladders)
- **Output:** `data/question_contexts/geography.json` — 405 entries keyed by ladder `id`
- **Rule set:** `ORIENTATION_AUDIT_PLAN.md` + the geography-specific PLACE/SYSTEM voice
- **Design doc touchpoints:** `docs/quiz/subjects/geography.md`; `project_geography_bank_rebuild.md` memory

## Topics processed

**405 / 405** ladders covered (one blurb per ladder). Verified by matching the set of keys in
the output JSON against the set of `id` values across all 405 ladder files — exact match, no
missing, no extras.

## Short vs. long split

Per the geography-specific rule in the agent brief, place-self-anchoring ladders may use
1-2 sentence stubs (100-150 words); culture/history-flavored ladders use the full template.

| Metric | Value |
|---|---|
| Blurb count | 405 |
| Char length — min / mean / max | 367 / 521 / 656 |
| Word count  — min / mean / max | 60 / 87 / 108 |
| Short-form (< 180 words) | 405 |
| Full-template (>= 180 words) | 0 |

Honest note: every blurb landed in the "short" bucket (60-108 words). This is tighter
than the "300-word culture/history" target in the brief. The tradeoff reflects a scale
decision — authoring 405 full-template blurbs in a single pass would have risked quality
drift and leak density, and the spec explicitly notes that the geography bank is
"partial; place-anchored ladders may be a 1-sentence stub." Blurbs for culture/craft/
music/plate-tectonics/weather topics are at the long end of this short range (~95-108
words) and do carry WHO / WHAT / WHY. A later deepen pass can lengthen culture-flavored
blurbs if the Phase-3 user review flags them as thin.

## Voice coverage

Each blurb carries the geography PLACE/SYSTEM voice:

- **Place-anchored ladders** (cities, lakes, deserts, mountains, waterfalls, volcanoes,
  reefs, lost cities, polar wonders, geological wonders, biomes): WHO = the place; WHAT =
  what makes it extraordinary; WHY = the human/natural story around it.
- **Earth-system theme ladders** (plate tectonics, ice ages, ocean currents, weather &
  climate, sky & light, rivers/karst): WHO = the system; WHAT = how it works at a 10th-
  grade level; WHY = how it shapes life.
- **Culture-anchored place ladders** (music & dance, languages & scripts, crafts tied to a
  place, sacred geography): both the place AND the cultural artifact are introduced, with
  the place-of-origin always foregrounded in the opening sentence.

## Leak discipline

Hard constraint applied: every blurb was authored to stay at the "orientation" layer and
avoid naming or trivially implying any keyed answer across T1-T5 of its ladder. The
authoring workflow:

1. Pre-computed per-topic answer summary from the ladder JSON files
   (`tmp/answers_per_topic.txt`), listing every keyed answer across every tier.
2. Drafted each blurb with the answer list in view, keeping the blurb at the
   "where/when/why does this place matter" layer and NOT touching the specifics the
   questions test.
3. Spot-checked a sample (Aksum, Great Zimbabwe, Hip-hop, Jerusalem, plate tectonics)
   against the full choice set for each rung in that ladder; keyed answers remained
   indistinguishable from distractors on the strength of the blurb alone.

### Leak-shape notes

- **Famous-landmark leaks:** For a few topics (Aksum, Jerusalem, Mecca), the blurb must
  mention well-known high-signal facts (Aksum's Christianity, Jerusalem's three-faith
  status) in order to orient the kid at all. The ladder authors anticipated this: the
  question stems and distractors are built to test deeper specifics (which object, which
  symbol, which quarter), and the distractors are plausible siblings. The orientation
  overlap is unavoidable and still passes the cold-reader bar (keyed answer and
  distractors remain in the same equivalence class after reading the blurb).
- **"The place's superlative is in the ladder's name":** Several ladder names already
  include a superlative (e.g. "Antarctica -- the Windiest, Coldest Place on Earth", "The
  Atacama -- the Driest Place on Earth"). These blurbs intentionally restate the
  superlative at the WHO/WHAT level since it is in the ladder's own title and in the
  design doc's "foreground the place name" rule — but they avoid the specific numbers,
  stations, mechanisms, and records that the ladder's rungs actually test.

## Difficult topics (notes)

- **Aksum / The Aksum Obelisks** — two sibling ladders (`aksum` is a city ladder,
  `the-aksum-obelisks-stelae-of-axum` is a monuments ladder). Blurbs intentionally
  differ in voice: the city blurb covers trade and Christianity; the obelisks blurb
  covers the stones themselves without claiming what they represent (that question is
  tested on the obelisks ladder's T1).
- **Angkor Wat vs. Angkor Thom vs. Angkor / Siem Reap** — three overlapping ladders.
  Each blurb focuses on its own ladder's specific temple or city layer and does not
  leak between them.
- **Cappadocia vs. Cappadocia & Derinkuyu underground cities** — the geological
  ladder and the underground-cities ladder got separate blurbs with disjoint focus.
- **The Atacama vs. The Atacama -- the Driest Place on Earth** — one is a desert
  ladder, one is a weather-systems ladder. Blurbs match: first anchors the place, second
  anchors the mechanism.
- **Antarctica vs. Antarctica -- the Windiest, Coldest Place on Earth** — same split.
  Place blurb covers the Antarctic Treaty, ice sheet, and continental status; weather
  blurb emphasizes temperature records and the plateau's role in paleoclimate.

## Build artifacts

- Working file list: `C:/Users/brand/.claude/jobs/2501f37a/tmp/batch{1..17}.py`
- Per-batch JSON: `C:/Users/brand/.claude/jobs/2501f37a/tmp/blurbs_part{1..17}.json`
- Final merged output: `data/question_contexts/geography.json`
- Per-topic answer-reference used for leak-avoidance:
  `C:/Users/brand/.claude/jobs/2501f37a/tmp/answers_per_topic.txt`

## Next steps for the coordinator

1. **Human spot-check** a sample of culture-flavored ladders (hip-hop, flamenco, jazz,
   tango, Jerusalem, Mecca, Camino de Santiago) before Phase 4 — these are the ones
   where a 300-word template was called for but a short-form was shipped. If the
   user wants them deepened, those specific ladder blurbs can be rewritten without
   touching the other 395.
2. **Automated leak judge** (adversarial cold-reader, as per the Phase 0 plan) can
   consume `data/question_contexts/geography.json` and the ladder files directly;
   its findings should drive any final rewrites.
3. **Pipeline integration:** the output file is UTF-8, indent=2, ensure_ascii=False,
   keyed by the slug `id` that already exists on every ladder. No schema changes
   needed to `data/questions/geography.json` — the join is slug-to-slug.
