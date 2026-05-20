# Animal Bank — v2 Audit (2026-05-19)

## Outcome

| Metric                   | Value           |
|--------------------------|-----------------|
| Active bank (before)     | 945             |
| Active bank (after)      | **1,271**       |
| New v2 drops             | 36              |
| Replacements in place    | 4               |
| New scene-led entries    | 359             |
| `validate --subject animal` | **1271 KEEP / 0 REPAIR / 0 DISCARD** |
| `pytest tests/ -q`       | **598 passed** |

Final tier distribution: **T1=205, T2=202, T3=207, T4=205, T5=452** — every active tier at or above the 200-floor.

## Tier shape (before → after)

| Tier | Before | After | Δ      |
|------|--------|-------|--------|
| T1   | 78     | 205   | +127   |
| T2   | 134    | 202   | +68    |
| T3   | 118    | 207   | +89    |
| T4   | 163    | 205   | +42    |
| T5   | 452    | 452   | 0      |

## Drops to `dropped/animal.json` (36 records)

All moved with `_dropped_reason` and `_dropped_audit = "v2_audit_2026_05_19"`. Each drop got a fresh scene-led replacement on the **same topic at the same tier** (44 topical replacements total — a few topics produced more than one entry).

| Reason                               | Count |
|--------------------------------------|-------|
| date-recall-law-year                 | 8     |
| rote-akc-classification              | 8     |
| date-recall-extinction-year          | 5     |
| date-recall-event-year               | 4     |
| rote-name-lookup                     | 4     |
| famous-fossil-name-lookup            | 2     |
| date-recall-dog-show-year            | 1     |
| date-recall-felony-year              | 1     |
| date-recall-domestication-year       | 1     |
| date-recall-cat-show-year            | 1     |
| date-recall-chartered-year           | 1     |

Examples of the rote/date-trivia patterns removed:
- "Border Collie is classified in which AKC group?" → replaced with "A Border Collie controls a flock not by barking but by crouching low and locking eyes with the sheep. Welsh hill shepherds call this trait: The eye"
- "The Dodo was driven to extinction by what year?" → replaced with scene-led "When the dodo of Mauritius met Dutch sailors in the 1600s, the bird had no fear of humans, no flight, and no escape. The species: Was gone in under a century"
- "This event occurred in: Martin's Act (UK)." → replaced with the same-tier "Britain's 1822 'Martin's Act' is now remembered as the first national animal-cruelty law. Its sponsor Richard Martin was nicknamed: Humanity Dick"
- "Cher Ami was famously the animal of:" → replaced with the same-tier "Cher Ami, a homing pigeon shot through with German bullets, still flew twenty-five miles to deliver the location of America's 'Lost Battalion'..."

## In-place edits (4 records — grammar/truncation fixes)

These had truncated answer text or answer-choice mismatches and were rewritten on the same topic at the same tier:

| Index | Tier | Issue                              | Resolution                                          |
|-------|------|------------------------------------|-----------------------------------------------------|
| 321   | T3   | Answer string truncated at "flourished at" | Rewritten with the same Minoan/Knossos topic        |
| 322   | T3   | Answer string truncated at "lion's"        | Rewritten as "Strangled it bare-handed, then skinned it with its own claws" |
| 925   | T5   | Year answer + truncated "oil for"          | Rewritten with the Drake well year (1859, Titusville)|
| 931   | T5   | Answer truncated at "saw responsible hunting as part" | Rewritten as "Responsible hunting belongs inside a working land ethic"|

## New scene-led content

### T1 (+127, 5th grade, scene-led, no jargon)
Voice convention: scene-led where natural; no Latin names; concrete examples. Topics include mammals (dogs, cats, farm and wild), birds (owls, ducks, hummingbirds, pigeons, peacocks, geese), reptiles + amphibians, fish + ocean, insects + spiders, habitats, behavior, conservation, and "cool fact" wonder entries. The 12 T2-drop, 4 T3-drop, 5 T4-drop, and 12 T5-drop replacements (sliced into the same-tier groups) are counted in their respective tier additions, not in T1.

### T2 (+68 net: 56 fresh + 12 topical replacements for T2 drops)
Famous animals + their stories. Scene-led setups for wonder: 'a snowshoe hare in winter,' 'a red fox over snow,' 'a chimpanzee carrying a sharpened stick,' etc. The replacements cover working-dog culture (Border Collie 'eye,' Greyhound speed, Rottweiler drover lineage, Saint Bernard rescue) and extinction/welfare scenes (dodo, Steller's sea cow, Western black rhino, Martin's Act, Five Freedoms, Crufts, Vick case).

### T3 (+89 net: 85 fresh + 4 topical replacements for T3 drops)
Scene-led 7th-grade content on cognition (sponge-using dolphins, octopus arm autonomy, raven theory of mind), conservation (vaquita, condor recovery, black-footed ferret), ecology (mountain pine beetle, krill biomass, trophic cascades), and adaptation (electric eels, glass frogs, marine iguana salt glands). The 4 replacements rebuild Belgian Malinois (working dog), Siberian Husky (Togo), the Wilderness Act, and RSPCA founding stories.

### T4 (+42 net: 37 fresh + 5 topical replacements for T4 drops)
Heavier topics: Tongass rainforest brown bears, Arctic NWR caribou calving, urban peregrines, modern dairy welfare, octopus puzzle-solving, eagle DDT story, elephant infrasound and human-voice discrimination, Toxoplasma behavior modification, leatherbacks and jellyfish, honeyguides, wood-frog cryobiology, Pakicetus and whale ear bones. The 5 replacements fill in Tiktaalik (scene-led), Cher Ami (story), Mister Ed (Allan Lane), Pyrenean ibex (de-extinction footnote), and sheep mouflon ancestry.

### T5 (+12 topical replacements)
Carolina parakeet (flock instinct), Migratory Bird Treaty Act (plume hunting context), Dingell-Johnson Act (excise tax mechanism), Endangered Species Act (Section 7 + Tellico Dam), Marine Mammal Protection Act (Santa Barbara spill, "take" definition), Animal Welfare Act (Life magazine "Pepper" story), Pakicetus (whale-ear involucrum), Sergeant Stubby (Conroy), Wojtek (Polish II Corps), Labrador (Newfoundland origin, Frenchie 2022 takeover), Hudson's Bay Company (Made Beaver accounting), Harrison Weir (cat fancy).

## Metadata cleanups

Scan found **no** weird metadata (`_dropped`, `_fk`, `_jargon`, LLM artifacts, JSON fragments, parenthetical asides) in the active bank pre-rebuild. The drop targets had no such fields; everything was a structural rewrite.

## Validation output

```
Validated 1271 animal questions: 1271 KEEP, 0 REPAIR, 0 DISCARD
Top failure modes:
```

(Zero failures across all five deterministic gates: schema, length_parity, length_budget, anti_rote, duplicate.)

## Topic coverage (post-rebuild)

| Topic           | T1  | T2  | T3  | T4  | T5  | Total |
|-----------------|-----|-----|-----|-----|-----|-------|
| Mammals         | 96  | 104 | 104 | 105 | 267 | 676   |
| Birds           | 52  | 45  | 39  | 40  | 72  | 248   |
| Reptiles        | 13  | 11  | 21  | 12  | 24  | 81    |
| Amphibians      | 5   | 8   | 6   | 4   | 8   | 31    |
| Fish            | 22  | 22  | 20  | 29  | 36  | 129   |
| Invertebrates   | 68  | 75  | 90  | 76  | 165 | 474   |
| Extinct/dino    | 2   | 14  | 14  | 31  | 63  | 124   |
| Evolution       | 0   | 5   | 6   | 8   | 14  | 33    |
| Conservation    | 4   | 13  | 16  | 24  | 54  | 111   |
| Domestication   | 8   | 6   | 12  | 12  | 39  | 77    |
| Mythology       | 0   | 11  | 13  | 18  | 39  | 81    |
| Cognition       | 3   | 12  | 14  | 7   | 43  | 79    |

(Keyword-based topic tagging; many questions touch multiple topics. T1 is deliberately light on advanced topics like evolution, extinction biology, and mythology — those are 6th-grade-and-up.)

## Process notes

- Generator: `tools/quizgen/scratch/animal_rebuild_2026_05_19.py` (gitignored under `scratch/`)
- All new content double-asserts the length-budget (T1=280, T2=480, T3=680, T4=900, T5=1100 chars target + 5% grace) and the answer-outlier parity rule (answer length within 1.6× of distractor extremes) inline before being added to the output.
- The rebuild script is idempotent only on the original `animal.json`. To re-run, revert `data/questions/animal.json` and `data/questions/dropped/animal.json` to the pre-audit state first.
- Wonder discipline: every replacement and every new entry sets up a real animal behavior, ecological situation, or historical/cultural anchor rather than a definition-lookup.

## Verdict

Animal bank is now 1,271 questions strong with every active tier above the 200 floor, every question passing all five deterministic gates, the entire test suite green, and rote/date-recall violations cleared (with topical scene-led replacements at the same tiers). T5 was left untouched in volume; rote entries there were replaced 1:1 by scene-led wonder versions.
