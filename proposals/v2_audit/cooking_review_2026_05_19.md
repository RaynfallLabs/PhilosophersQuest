# Cooking Quiz Bank — Quality Review

**Date**: 2026-05-19
**Bank**: `data/questions/cooking.json`
**Reviewer**: Claude (Opus 4.7), no subagents

## Summary

Cooking bank went from **1,097 questions** (218/140/147/191/401) to **1,203 questions** (216/200/200/200/387). All five gates clean. All 598 pytest tests pass. The bulk of the work was repairing a contiguous block of corruption (i=440-487 in the input file) where the choices arrays had been swapped across questions, then growing T2-T4 to the 200/tier floor with scene-led wonder-driven content across the five pillars.

## Inputs

- Starting bank: 1,097 questions (T1=218, T2=140, T3=147, T4=191, T5=401)
- Floor target: 200/tier for T2-T4 (T1 and T5 already above)
- Validation baseline: 1,097 KEEP / 0 REPAIR / 0 DISCARD (gates were passing the corruption)

## Key Findings

### 1. Choice-array corruption in i=440-487

A contiguous block of 29 questions had their `answer` and `choices` arrays scrambled across neighboring questions. The choices belonged to *other* questions while the stems remained intact. Examples:

- **i=440**: stem about cooking a roux dark → answer "Tempering it" (wrong; should describe deeper flavor / weaker thickening)
- **i=442**: stem about safest chicken-cutting board sequence → answer "The dissolved starch helps the sauce cling and emulsify with the oil" (this was i=441's answer, copy-pasted)
- **i=454**: stem about how white bread differs from brown rice → answer "Calcium element" (the choices contained mineral names that don't fit the question at all)
- **i=466**: stem about Kansas City BBQ → answer "Coffee drink"
- **i=468**: stem about a Japanese sushi knife → answer "Tea leaves"
- **i=470**: stem about Ethiopian injera → answer "Vanilla pods"
- **i=484**: stem about Western wedding cake tiers → answer "Coal, shortbread, and whisky (and ideally tall and dark-haired)"
- **i=485**: stem about bride+groom cutting cake → answer "Bacon and cabbage — corned beef is an Irish-American adaptation"

The pattern suggests a serialization bug during some prior generation step shifted the choices/answer pairs by a few positions across this contiguous range. The questions themselves were good ideas; the choices were unrecoverable. **All 29 dropped to `dropped/cooking.json` with `_dropped_reason`**.

### 2. One additional answer-echoes-question bug

- **i=246**: "To clean narrow vessels like blender jars and sippy cups, what tool is needed?" → answer "Narrow vessels like blender jars" (the answer is the subject of the question, not a tool name). Dropped.

### 3. Total dropped: 30

| i | Tier | Reason (one-line) |
|---|---|---|
| 246 | 2 | answer echoes the question subject |
| 440 | 3 | roux-dark → "Tempering it" |
| 442 | 4 | chicken board safety → pasta-water answer |
| 452 | 4 | beans+rice complete protein → "Lactobacillus and Bifidobacterium" |
| 454 | 5 | white bread differs → "Calcium element" |
| 455 | 1 | "Made with whole grains" label → "Straining out the whey" |
| 456 | 4 | raw milk debate → "Iron absorption from the plant source" |
| 457 | 3 | lunchbox missing → "minimally processed traditionally consumed fats" |
| 459 | 5 | bone broth → "Potential carcinogens" |
| 460 | 5 | cooked spinach iron → "green or colorful vegetable" |
| 461 | 5 | five mother sauces → "Providing vitamin C... scurvy" |
| 462 | 5 | Sichuan tongue tingle → "Calorie density" |
| 463 | 4 | Thai four tastes → "The margarine spread" |
| 466 | 4 | Kansas City BBQ → "Coffee drink" |
| 468 | 5 | sushi knife → "Tea leaves" |
| 469 | 5 | Spanish tapas → "Pasta existed in Italy before Marco Polo" |
| 470 | 3 | Ethiopian injera → "Vanilla pods" |
| 471 | 3 | Lebanese pomegranate molasses → "Tell me what you eat..." |
| 472 | 2 | Indian ghee → "A.B. Boulanger's Paris shop" |
| 473 | 5 | Levantine za'atar → "Slow Food movement" |
| 474 | 1 | Sandwich Earl → "Fannie Farmer in 1896" |
| 475 | 5 | Kaldi coffee legend → "The Joy of Cooking" |
| 477 | 5 | Pasteur 1864 → "Bread for the masses" |
| 478 | 3 | Marco Polo pasta → "1621 in Plymouth" |
| 481 | 5 | formal dinner host etiquette → "Long life and longevity" |
| 483 | 5 | Italian wedding sugared almonds → "Haggis as the centerpiece" |
| 484 | 2 | Western wedding cake tiers → "Coal, shortbread, whisky" |
| 485 | 4 | bride+groom cake → "Bacon and cabbage" |
| 486 | 5 | Irish wake → "Dessert, coffee, and a digestif" |
| 487 | 5 | French meal end → "Halva and baba ganoush" |

## Wonder Rewrites

Per the discipline of the cooking bank, **the broken questions were NOT salvaged with new choices**. Instead the slots were filled by entirely new scene-led, wonder-driven generation. Many of the broken topics (Marco Polo pasta myth, Pasteur, Earl of Sandwich, wedding cake tiers, Italian almonds) are already covered well elsewhere in the bank (i=144, i=125-127, i=144, i=166-167, i=185-186, i=475 has working coffee origin at i=763 etc.), so the topical losses are minimal.

## Generated Content

Generated **136 new questions** (T2 +63, T3 +58, T4 +15) to bring all three tiers to the 200 floor. Each generated set was deliberately balanced across the cooking spec's 5 pillars: techniques, ingredients, dishes, safety, dining/cultural.

### T2 generations (63 questions)

**Techniques (15)**: claw grip, mise en place, crowded-pan steam-instead-of-sear, flour scoop-vs-spoon, oil-butter combination, butter glaze, blanch-and-shock, reduction, room-temperature eggs, mashed-potato gluey overworking, baking soda in tomato sauce, dice, chiffonade, room-temperature steak rest, gluten kneading

**Ingredients (15)**: dried herb volatility loss, vine-ripened tomato flavor, kosher salt vs. table salt by volume, butter softening, baking-powder vs. soda+acid substitution, neutral oil for searing, vanilla bean vs. extract, honey crystallization is normal, Parmigiano-Reggiano, basil flavor compound (anethole), saffron from crocus, brown vs. white sugar (molasses), Dutch-process vs. natural cocoa, cake vs. bread flour protein, fresh vs. powdered ginger

**Dishes (15)**: Bolognese (on tagliatelle), tacos, phở, Sunday roast, croissant, sushi, baklava, paella, gołąbki (cabbage rolls), marinara, gumbo, biryani, borscht, tagine, chimichurri

**Safety (9)**: slimy deli meat, raw flour E. coli risk, lasagna in warm oven overnight, raw-chicken board reuse, rotisserie chicken left in warm car, 165°F leftover reheat, post-sneeze hand washing, "sell-by" vs. taste, "off" smell on ground beef

**Dining/cultural (9)**: outside-in fork sequence, 1621 Plymouth menu, Anna Maria Russell + 1840 afternoon tea, digestivo, Shabbat challah, Lunar New Year yu = surplus, Día de los Muertos ofrenda, BMW (bread-meal-water) place setting, parallel fork-knife = "finished"

### T3 generations (58 questions)

**Techniques (13)**: hooch on sourdough starter, tempering eggs into custard, carryover cooking, mirepoix, dry-brining for crust, cold butter for flaky crust, burn-care running water, lamination, pâte à choux + steam, cream of tartar / acid stabilizing whipped cream, chocolate Form V crystals, pyrolysis vs. caramelization threshold, roux color → thickening tradeoff

**Ingredients (13)**: NOVA-4 ultra-processed classification, sugar balancing tomato acid, nixtamalization, lacto-fermentation Lactobacillus, yogurt marinade mild acid, cilantro-vs-coriander same plant, copper bowl egg whites (ovotransferrin), whole-wheat bran cuts gluten, capsaicin oil-soluble, lemon juice + apple browning enzyme, EVOO vs. "light" olive oil, salt suppresses bitter, red wine alcohol retention

**Dishes (13)**: Bolognese on tagliatelle, bouillabaisse, Spanish sopa de ajo, mapo tofu, dolsot bibimbap stone pot, Filipino adobo, Thai tom kha gai, jollof rice, Greek moussaka, Brazilian feijoada, Peruvian ceviche, Ethiopian injera, Roman carbonara (no cream)

**Safety (9)**: fridge organization (raw chicken bottom), Listeria + pregnancy, turkey thaw 24h/4-5lb, mayo Salmonella after open, raw egg internal Salmonella, home canning + botulism, buffet danger zone 140°F, raw-shellfish cross-contamination, hot-day 1-hour rule

**Dining/cultural (10)**: Easter colombe dove bread, three-tier wedding cake tradition, galette des rois Epiphany king, medieval salt cellar above/below, Spanish sobremesa, Catholic Lent Friday meat abstinence, high tea vs. afternoon tea (class), Diwali festival of lights, dim sum Cantonese yum cha, Mexican quinceañera Aztec-Catholic fusion

### T4 generations (15 questions)

**History + dining-cultural focus (per cooking.md T4 profile)**:
- Service à la russe 1810 (Kurakin in Paris)
- Brigade de cuisine (Escoffier)
- Maillard 1912 paper
- Carême's four mother sauces → Escoffier's five (sauce tomate added)
- Grand couvert at Versailles (Louis XIV)
- Medieval trenchers as alms
- Victorian etiquette codes as social sorting
- Harry + Meghan 2018 lemon-elderflower cake break
- British Sunday roast and church-time alignment
- Lincoln + Sarah Hale + 1863 Thanksgiving proclamation
- Catholic Friday-fast theology (penance)
- Italian-American "Feast of Seven Fishes" symbolism
- Italian-immigrant "gravy" naming
- French cheese-before-dessert sequence logic
- Le Cordon Bleu name origin (Order of Holy Spirit blue ribbon)

## Grammar fixes

No standalone grammar fixes were applied — the bank was already well-edited. The corruption was structural, not grammatical.

## Weird metadata

None found. All questions in the active bank had only `tier`, `question`, `answer`, `choices`, `context`. The dropped file has `_dropped_reason` for the 30 newly dropped.

## Final Distribution

| Tier | Count | Target | Status |
|---|---:|---:|---|
| T1 | 216 | 200+ | OK |
| T2 | 200 | 200 | EXACT |
| T3 | 200 | 200 | EXACT |
| T4 | 200 | 200 | EXACT |
| T5 | 387 | 200+ | OK |
| **Total** | **1,203** | — | — |

## Topic Pillar Map (primary pillar)

| Tier | techniques | ingredients | dishes | safety | dining | other |
|---|---:|---:|---:|---:|---:|---:|
| T1 | 53 | 59 | 44 | 27 | 23 | 10 |
| T2 | 63 | 59 | 21 | 20 | 31 | 6 |
| T3 | 48 | 54 | 26 | 30 | 32 | 10 |
| T4 | 57 | 55 | 11 | 25 | 46 | 6 |
| T5 | 85 | 118 | 37 | 39 | 95 | 13 |

All pillars represented at every tier. T4 dishes is the thinnest cell at 11 — but that's an artifact of T4 being predominantly historical/chemistry-driven per the spec.

## Validation + Tests

```
$ py -m tools.quizgen validate --subject cooking
Validated 1203 cooking questions: 1203 KEEP, 0 REPAIR, 0 DISCARD
Top failure modes:

$ pytest tests/ -q
598 passed in 57.26s
```

## Conflict Priority Notes

Per spec: drop-if-overcap > rote-replace > tier-shift > grammar > metadata. The dominant action this pass was **drop-the-corruption-and-replace-with-fresh**. No tier shifts were needed (FK + jargon already in-band for every kept question). No rote rewrites were needed beyond what the existing bank already had. No metadata cleanup needed.

## Scripts (gitignored)

- `tools/quizgen/scratch/cooking_audit_baseline.py` — FK + jargon + pillar audit
- `tools/quizgen/scratch/cooking_find_rote.py` — regex shell detector
- `tools/quizgen/scratch/cooking_find_semantic_mismatches.py` — keyword-overlap detector (noisy)
- `tools/quizgen/scratch/cooking_find_mismatches.py` — choices-vs-answer schema check
- `tools/quizgen/scratch/cooking_broken_qs.py` — context-keyword heuristic
- `tools/quizgen/scratch/cooking_drop_broken.py` — drop the 30 broken Qs to dropped/
- `tools/quizgen/scratch/cooking_new_t2.py` — generate 63 T2 questions
- `tools/quizgen/scratch/cooking_new_t3.py` — generate 58 T3 questions
- `tools/quizgen/scratch/cooking_new_t4.py` — generate 15 T4 questions

## Files Changed

- `data/questions/cooking.json` — 1,097 → 1,203 questions (30 dropped, 136 new)
- `data/questions/dropped/cooking.json` — 1,511 → 1,541 (30 newly tagged with reason)
- `proposals/v2_audit/cooking_review_2026_05_19.md` — this report
