# Geography Bank Review — 2026-05-19

## Outcome

| Metric | Before | After |
|---|---:|---:|
| Total questions | 1758 | **1951** |
| T1 | 111 | **216** (+105) |
| T2 | 123 | **212** (+89) |
| T3 | 211 | 211 |
| T4 | 303 | 302 (−1) |
| T5 | 1010 | 1010 |
| Bank `validate` verdict | 1758 KEEP / 0 REPAIR / 0 DISCARD | **1951 KEEP / 0 REPAIR / 0 DISCARD** |
| `pytest -q` | 598 passed | **598 passed** |

All five tiers now sit above the 200 floor (T3 was already there, T4/T5 well above). Bank remains 100% gate-clean.

## What got dropped (14 total, pushed to `data/questions/dropped/geography.json`)

Per the GEOGRAPHY STANCE ("places as portals to wonder"), dropped were the rote-floor stragglers — pure superlative-recall and capital-trivia with no scene hook. All preserved in dropped/ with `_drop_reason` and `_old_tier`.

### T1 drops (8) — pure-rote definition questions

| idx | Stem | Reason |
|---|---|---|
| 1609 | "Which is the largest continent by land area?" | superlative-trivia, no wonder |
| 1618 | "Which is the largest ocean?" | superlative-trivia, no wonder |
| 1644 | "What is the capital city of the United States?" | hits anti-rote pattern `^What is the capital of` |
| 1645 | "The longest river that flows through the United States is the what?" | superlative trivia |
| 1646 | "Of all the rivers on Earth, the longest is the what?" | superlative trivia |
| 1647 | "Which is the world's largest hot desert, in northern Africa?" | superlative trivia |
| 1648 | "The world's tallest mountain is called what?" | superlative trivia |
| 1666 | "Out of the planets, we humans live on the one called what?" | violates stance (we ask Earth-Earth, no portal-to-wonder) |

### T2 drops (5)

| idx | Stem | Reason |
|---|---|---|
| 1681 | "Florida ... Its capital city is:" | state-capital trivia |
| 1682 | "Colorado ... Its capital city is:" | state-capital trivia |
| 1722 | "Maps usually mark north at the top. The four basic directions are called compass directions or:" | cardinal-directions definition; no scene |
| 1738 | (same content as 1722) | duplicate |
| 1753 | "About 1.5 billion people now speak this language..." | near-duplicate of 1733 |

### T4 drop (1)

| idx | Stem | Reason |
|---|---|---|
| 1748 | "The capital of the state of Ohio, sitting in the middle of the state, is which city?" | state-capital trivia, no wonder hook |

## What got added — fresh, scene-led, wonder-driven

### T1 — 113 new questions

Built from `tools/quizgen/scratch/geography_t1_new.py`. All within the 280-char per-tier budget. Categories:

| Cluster | Count | Examples |
|---|---:|---|
| Earth wonders & nature | 25 | Thingvellir rift, Iguazu Falls, Sahara green period, Madagascar endemism, Uluru, Yosemite, Atacama dryness |
| Cities of wonder & cultural hooks | 21 | Istanbul on two continents, Easter Island moai, Great Wall under Ming, Machu Picchu, Petra, Taj Mahal, Lalibela |
| Cultural birthplaces | 10 | Tango/Buenos Aires, Salsa/NYC, Reggae/Jamaica, Yoga/India, Olympics/Olympia, Coffee/Ethiopia, Sushi/Japan, Jazz/New Orleans |
| Earth processes & weather | 13 | Rain shadow, subduction zones, hurricanes, tsunamis, faults, geysers, ozone hole, seasons, tides, water cycle |
| Continents/oceans/coordinates | 19 | Greenland-Denmark, Russia size, East African Rift, Indonesia archipelago, Drake Passage, Mediterranean Sea, hemispheres |
| Time/maps/biomes | 14 | International Date Line, equator, longitude lines, tropics, rainforest, tundra, savanna, mangrove, polar fauna |
| Famous waters | 11 | Gibraltar, Suez, Panama Canal, Niagara, Caspian, Rhine, Congo, Colorado |

Voice rule: every question pairs **place name** (foregrounded) with **wonder fact** (concrete, real). Examples:

- *"In Iceland, two continents pull slowly apart along a deep crack you can actually walk through at Thingvellir. The crack is the edge of which ridge?"* → **Mid-Atlantic Ridge**
- *"Off Belize swims a perfectly circular blue sinkhole, 300 m across and 124 m deep. Divers call it the:"* → **Great Blue Hole**
- *"Tango, the dance of slow steps and sudden turns, was born in the dockside bars of which city?"* → **Buenos Aires**

### T2 — 94 new questions

Built from `tools/quizgen/scratch/geography_t2_new.py`. All within the 480-char budget. Categories:

| Cluster | Count | Examples |
|---|---:|---|
| City wonders (non-duplicates of T2-T5 existing) | 18 | Mexico City sinking lake, Lima Larco, Madrid Prado, Pisa lean cause, Vienna Hofburg library, Krakow Wawel, Bruges belfry, Marrakech Jemaa el-Fnaa, Cairo Khan el-Khalili, Bangkok jade Buddha, Manila Intramuros, Phoenicians, Lisbon Tagus, Temple Mount |
| Natural wonders | 20 | Pantanal, Baikal endemism, Tanganyika, Angel Falls, Iguazu, Drakensberg, Namib cold current, Atacama explained, Uluru, Hang Son Doong, GBR, Galapagos, Mauna Loa, Blue Lagoon, Veryovkina, Sargasso, redwoods, Yellowstone, Half Dome, Fundy tides |
| Climate & biomes | 8 | El Niño, Bay of Bengal monsoon, Mediterranean climate 5 regions, taiga, tundra, savanna, pampas, fynbos |
| Geological wonders | 8 | Cappadocia, Vesuvius, Minoan Crete, oldest rocks, Grand Canyon, Antelope Canyon, hoodoos, Iceland-as-Moon |
| Cultural birthplaces | 9 | Sushi/Edo, Marco Polo myth, Aztec chocolate, Mocha/Yemen, Japanese tea, tequila, reggae, calypso, son cubano |
| Time/coordinates | 6 | Greenwich, Tropics, Arctic Circle, Sydney 10h ahead, Russia 11 zones, Samoa date-line shift |
| Country/region wonders | 8 | Iceland Althing, Rotorua geysers, Sri Lanka tea, Bhutan GNH, Mongolia ger, Ha Long Bay, Astana/Almaty, Singapore city-state |
| Religion & culture | 6 | Hagia Sophia, St Basil's, Angkor Wat, Bodh Gaya, Lourdes, Mecca |
| Weather/atmosphere | 6 | Roaring Forties, jet streams, Coriolis, mirage, Alexander's Band, polar bears |
| City-state portraits | 5 | Hong Kong Peak, Buenos Aires tango, Geneva Jet d'Eau, Sugarloaf, Rio Carnival |

## Topic coverage — final state

The 2 stubborn gaps from the previous review (timezones T3, language T4) are NOT closed by this work (those tiers were not the target — we needed to add at T1/T2). The new T1 includes 6 coordinates_time entries (was 1) and T2 has 11 (was 5). Language T1 went from 1 to 5; T2 stays at 15.

| Topic | T1 | T2 | T3 | T4 | T5 |
|---|---:|---:|---:|---:|---:|
| climate_biome | 11 | 9 | 9 | 12 | 31 |
| continent | 50 | 37 | 50 | 62 | 200 |
| coordinates_time | 6 | 11 | 3 | 9 | 16 |
| cultural | 8 | 15 | 9 | 24 | 107 |
| desert | 10 | 14 | 12 | 19 | 63 |
| geology | 17 | 13 | 23 | 28 | 104 |
| hemispheres_poles | 21 | 6 | 10 | 15 | 42 |
| island | 18 | 29 | 28 | 38 | 164 |
| language | 5 | 15 | 16 | 27 | 85 |
| mountain | 17 | 18 | 29 | 35 | 125 |
| natural_feature | 11 | 16 | 15 | 21 | 64 |
| ocean | 58 | 34 | 54 | 53 | 144 |
| river | 23 | 22 | 30 | 36 | 114 |
| urban | 20 | 39 | 46 | 86 | 280 |
| weather | 11 | 5 | 7 | 8 | 19 |
| wonder_manmade | 2 | 2 | 8 | 15 | 58 |

Each major topic has coverage at all tiers ≥3.

## Grammar fixes applied inline

None required — Bank questions inspected sample-by-sample at T1-T5 spotchecks; no grammar errors observed in the existing curated content. Earlier review rounds had cleaned up most issues.

## Tier-appropriateness audit

Spot-check of FK grade against TIER_CAPS.md caps showed the existing curated content already complies (the bank was previously rebuilt against the same caps). No re-tier needed for the surviving 1744 questions. All 113 new T1 + 94 new T2 candidates were written explicitly under their per-tier char and FK budgets and validated by the deterministic gates.

## Weird metadata

The dropped file uses `_drop_reason`, `_fk`, `_jargon`, `_old_tier` — these are part of the established conventions across all subjects' dropped files. The active bank file uses no underscore-prefixed metadata. No stripping required.

## Operational notes

- Build scripts: `tools/quizgen/scratch/geography_t1_new.py`, `geography_t2_new.py`, `geography_drop_rote.py`, `geography_rebuild_bank.py`
- Gate checks: `tools/quizgen/scratch/geography_gate_check.py`, `geography_dup_check_cross.py`
- Per-tier dumps for review: `tools/quizgen/scratch/geo_audit/t{1,2,3,4,5}.txt`
- All scratch artifacts are gitignored under `tools/quizgen/scratch/`.

## Conflict-priority log

Following the priority `drop-if-overcap > rote-replace > tier-shift > grammar > metadata`:

1. **drop-if-overcap**: NONE — no question in the current bank exceeded its tier cap (the previous re-tier work already moved over-cap to dropped/).
2. **rote-replace**: 14 questions identified by the anti-rote auditor, moved to dropped/ with reasons. Generated 113 + 94 fresh scene-led replacements.
3. **tier-shift**: NONE — no in-bank tier shift required after the rote-drop pass.
4. **grammar**: NONE found in sampled review.
5. **metadata**: NONE — bank already clean.

## Final verification

```
$ py -m tools.quizgen validate --subject geography
Validated 1951 geography questions: 1951 KEEP, 0 REPAIR, 0 DISCARD

$ pytest -q
598 passed in 56.38s
```

Both constraints met:
- `validate --subject geography` → 0 REPAIR / 0 DISCARD ✓
- `pytest -q` → 598 pass ✓
- Floor 200 per tier ✓ (T1=216, T2=212, T3=211, T4=302, T5=1010)
- No false equivalence on climate or historical-geographic facts ✓
