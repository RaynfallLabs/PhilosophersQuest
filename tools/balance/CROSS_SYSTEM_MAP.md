# Cross-System Map — Validation List

**Built from five systems-mapper agents (2026-05-15).** Source docs in `tools/balance/systems/`. Every entry here should be **validated by the developer** before any curve work resumes. Mark each ✅ confirmed / ❌ wrong / ➕ missing.

---

## A. System inventory — the things that exist

| # | System | Primary file(s) | Role |
|---|---|---|---|
| 1 | **Cooking + Harvest** | `food_system.py`, `recipes.json`, `ingredient.json` | THE leveling system. Only scalable max-HP source. 296 ingredients, 335 compound recipes. Formula: `sqrt(min_level) × quality_mult × compound_bonus`, softcap 1000 with diminishing returns. |
| 2 | **Karma** | `npc_encounters.py`, `game_encounters.py` | -10 to +10 scoreboard. ONLY changed by NPC encounters (10/run). Funnels into L99 Judgment. |
| 3 | **Altars** (6 distinct roles) | `dungeon.py`, `boss_levels.py`, `mystery_system.py` | Generic procedural, L17 Ariadne, L37 Athena, L53 Odin, L76 Dwarven Forge, L79 Vidar, L99 Last Judgment, L100 hex-ring (×6), mystery altars (13). **NOTE: quest altars currently fixed-floor; design intent is ±3-floor randomization (matches Cow NPC pattern). See H.13.** |
| 4 | **Prayer + Theology quiz** | `game_divine.py` | Chain 0-8 threshold quiz. Cooldown 100-280 turns base. Special at L99/L100. |
| 5 | **Michael's gifts** | `npc_encounters.py:1989-2027` | 5 outcomes by karma: Sword+Scales+Paladin (10), Scales only (1-9), silence (0), locusts strengthened (-1 to -5), Abaddon empowered (-6 to -10) |
| 6 | **Seal-breaking gate** | `game_combat.py:600-610`, monsters.json | 7 seal demons on L83/85/87/89/91/93/97. All 7 must fall to access Abaddon. |
| 7 | **Boss arenas (5)** | `boss_levels.py` | Hand-crafted L20/40/60/80/100 + secret L999 Cow Level. Each has unique tile/altar layouts. |
| 8 | **Bosses (6)** | `monsters.json` | Asterion, Medusa, Fafnir, Fenrir, Abaddon, Cow King |
| 9 | **Quirk system (100 total)** | `quirk_system.py` | 71 passive/stat/timer + 29 active V-menu powers. Mythological/historical theme. |
| 10 | **Hack Reality (XYZZY)** | `main.py:2585-2655` | 5 tiers: free reveal / +5 all stats / Fenrir pet / etc. Backtick key. Per-run, not cross-run. |
| 11 | **Recall Lore** | `game_magic.py:75-146` | Trivia escalator chain → hint from `hints.json`. 203 hints across T1-T5 (16/24/47/60/56). Norns halves cooldown. |
| 12 | **Hints + Lore + Discoverability** | `data/hints.json`, item lore fields, NPC dialog, mysteries, flavor encounters | The whole discovery scaffold. |
| 13 | **Identification** | `game_magic.py` | Philosopher's Stone auto-ID, identify_sight accessories, manual philosophy quiz |
| 14 | **Pet + bonding** | `pet_system.py`, items | Soul Sphere throws, Ash Ketchum build, Sketched Pet, Ethereal Unicorn, Fenrir pet (XYZZY) |
| 15 | **Mystery system** | `mystery_system.py` | 13 mysteries, ~60% spawn per eligible floor. Includes Fisher King, Pandora (inverted), Sphinx, Mjolnir reforge |
| 16 | **NPC encounters** | `npc_encounters.py` | 10 karma encounters per run (one per 10-level block). Plus merchant, oracle, etc. |
| 17 | **Flavor encounters** | `flavor_encounters.py`, `data/flavor_encounters.json` | 97 ambient scenes (5 hardcoded + 92 JSON), ~40% spawn per non-boss floor. |
| 18 | **Bones / ghosts** | `bones.py` | 50% load chance per dungeon level. Ghost = drained player + cursed dropped gear. Loki quirk farm. |
| 19 | **Death-chase escape** | `main.py:1230-1420` | Speed escalation 50→75→100→125%, prayer-freezes Death, secret Abyss ritual kills it. |
| 20 | **Score economy** | `main.py:1479-1508` | turn×10 + max_level×1000 + kills×100 + stone_bonus 50000. 8 grade tiers F..S. |
| 21 | **Status effects** | `status_effects.py` | Buffs/debuffs/resistances. Heroism/brilliance stat-bonus lifecycle. Berserk now properly registered (Phase 2 work). |
| 22 | **Hidden levels** | `boss_levels.py` (Cow), `dungeon.py` (chambers, vaults) | Cow Level L999 + per-floor hidden chambers + 4×4 sealed vaults. |
| 23 | **Hidden characters** | `welcome_screen.py` | 26 secret builds. Includes family Easter eggs (Corwin/Cain/Fianna/Fluffs/Robyn/Dad/Titivillus). |
| 24 | **Damage types + resistances** | `combat.py`, `monster.py`, `game_magic.py` | After Phase 2C: spells properly pass types. Holy weakness, dragon_scales, ignore_resistances. |
| 25 | **Stat tracks** | `player.py` | HP/SP/MP/AC + STR/CON/DEX/INT/WIS/PER. Independent Khopesh of Anubis HP track bypasses cooking. |

---

## B. Quest layer reference per boss

### B.1 Asterion (L20) — **2 layers**

| Layer | Path | Floors | Trigger | Effect | Hint trail |
|---|---|---|---|---|---|
| 1 | Ariadne's Thread | L17 fountain → L20 | Pick up Bronze Bull, return to fountain, pour | Defangs phasing on Asterion (also leaks to vampires — Phase 2 candidate) | T1+T3+T5 explicit |
| 2 | Theseus quirk arc | passive | Explore 5 floors fully | +1 PER permanent | T5 |

### B.2 Medusa (L40) — **5 layers**

| Layer | Path | Floors | Trigger | Effect | Hint trail |
|---|---|---|---|---|---|
| 1 | Aegis mirror path | L37 Athena altar → L40 | Drop Eye of Graeae on altar → Aegis appears | Stone-gaze bounce mechanic | T4+T5 explicit |
| 2 | Blindfold path | self-blind | Status-effect blinded | Medusa cannot petrify what cannot see her | T4 *"What you cannot see cannot harm you"* |
| 3 | Arena LOS pillars | L40 arena | Hide behind pillars | Tactical kiting | T4 |
| 4 | Medusa quirk arc | passive | 5 blinded-correct quiz episodes | +2 DEX permanent | T5 |
| 5 | Petrify-on-crit weapons | items | Carry Harpe or petrify-flagged weapon | Reverses the petrify dynamic | item lore |

### B.3 Fafnir (L60) — **3 layers**

| Layer | Path | Floors | Trigger | Effect | Hint trail |
|---|---|---|---|---|---|
| 1 | Sigurd's pit ritual | L53 Odin altar → L60 | DROP Broken Gram on altar → get Sigurd's Shovel → dig pit in arena | 4× damage from in-pit position | T1+T3 |
| 2 | **Reforged Gram secret** | L53 Odin altar → L60 | THROW Broken Gram OVER altar (not drop) → Gram reforged | Tier-5 lightning blade, `ignore_resistances`, 9× max chain | **Weak — only Gungnir T5 nod** |
| 3 | Fafnir's Blood | post-kill | Drink dropped blood | Full heal + permanent fire-resist + Gram reforge hint vision | item lore (post-kill only) |

### B.4 Fenrir (L80) — **4 layers**

| Layer | Path | Floors | Trigger | Effect | Hint trail |
|---|---|---|---|---|---|
| 1 | **Gleipnir (CORE quest)** | L76 Dwarven Forge | Collect 6 impossible ingredients (cat's footstep, woman's beard, mountain root, fish breath, bird spittle, bear sinew) → forge | Power-bind Fenrir with stat-tax | T4 explicit + each ingredient names "Gleipnir" |
| 2 | **Vidar's Sandal (MEGA SECRET)** | L5-73 scraps → L79 altar | 10 leather scraps across the dungeon → assemble at altar | INSTANT KILL on chain ≥ 1 vs Fenrir | **Weak — T5 inverted hint says scraps "are not useless"** |
| 3 | ICE patches | L80 arena | Use icy tiles for kiting | Tactical | none |
| 4 | Fire weakness | direct | Any fire damage | Fenrir's fire resist is actually weakness | item lore |

### B.5 Abaddon (L100) — **6 layers**

| Layer | Path | Floors | Trigger | Effect | Hint trail |
|---|---|---|---|---|---|
| 0 | **Seven Seals (GATE)** | L83/85/87/89/91/93/97 | Kill all 7 seal demons (Amon/Buer/Mammon/Bael/Samael/Beleth/Abyzou) | Required just to reach Abaddon | Implicit (in-game messages on each break) |
| 1 | **L99 Judgment** (karma) | L99 altar | Approach altar with karma | Sword+Scales (10) / Scales (1-9) / silence (0) / locusts+ (-1..-5) / Abaddon empowered (-6..-10) | T4 Grail + T5 "three boons" |
| 2 | **L100 Six-Altar Hex Ring** | L100 arena | Pray at each altar during fight (single-use each) | Strip Abaddon resistances for `chain × 2` turns | **No T5 hint for this specific mechanic** |
| 3 | Sword of Michael | from Layer 1 | Equip and attack | ignore_resistances + 6d10 abaddon_bonus + holy 1.5× | T2+T5 mentions |
| 4 | Heavenly Host counter | from Layer 1 (Scales) | Activate V-power | Angel-per-locust counter-spawn, mutual annihilation | T5 implies |
| 5 | **The Abyss (Layer 3 / sixth boss reward)** | climb back up + 4 items | Stone + Tablet + Wrench + Shimmer + Lake of Fire scroll → kill Death entirely | Death dies, Death's Bane reward scroll drops | **Excellent** — 5+ hints across T2-T5 |

### B.6 Cow King (L30-39 secret) — **3 layers**

| Layer | Path | Trigger | Effect | Hint trail |
|---|---|---|---|---|
| 1 | Poke-cow-10x entry | Find any cow → poke 10 times | Opens portal to L999 | **None — high risk of being missed** |
| 2 | Hell Bovine pasture | combat | 40-50 mob fight, high cooking ingredient density | n/a |
| 3 | Cow King's Horns | post-kill | Equip armor | `chain_bonus +1` permanent | none |

---

## C. Cross-system interaction grid

Marked: **●** primary touch / **○** secondary touch

| ↓ touches → | Cook | Karma | Altar | Prayer | Michael | Seal | Boss | Quirk | XYZZY | Lore | Pet | Mystery | NPC | Bones |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Cooking** | — | | | | | | ● adds | ● Persephone, Tantalus | | ○ recipe hints | | | | |
| **Karma** | | — | | | ● gates | | ● Abaddon HP+50%/locust+ | ○ Loki | | ○ judgment hint | ○ unicorn flees | | ● 10 encounters | |
| **Altar** | | | — | ● | | ● Vidar/Gleipnir/Gram | ● boss quests | ● Fisher King | | ● T2 #14 | | ● 13 mystery altars | | |
| **Prayer** | | | ● | — | ● Death-freeze | | ● L100 resist-strip | ● Fisher King, Zoroaster, Solomon, Norns | | | | ● Fisher King mystery | | |
| **Michael's gifts** | | ● | | ● | — | ● Sword vs Abaddon | ● Abaddon | | | | | | ● delivery | |
| **Seal gate** | | | | | | — | ● Abaddon | | | | | | | |
| **Boss** | | ● Abaddon | ● per boss | ● Abaddon | ● Abaddon | ● Abaddon | — | ● 4 named arcs | | ● 5 popups | | | | |
| **Quirk (100)** | ● cooking quirks | ● Loki | ● Fisher King | ● 4+ prayer quirks | ● paladin title | | ● 4 boss-named arcs | — | ○ Mirror Mind triggers on ID | ● Norns/Nostradamus/Second Sight | ○ Diogenes' Lantern | ● Fisher King mystery | | |
| **XYZZY** | | | | | | | | ● Mirror Mind | — | ● 5 hints T1-T5 | ● Fenrir pet tier 5 | | | |
| **Lore + hints** | ● cooking recipe hints | ● judgment | ● altar hints | ○ | | | ● 5 popup chains | ● 12-quirk Oracle pool | ● 5 hints | — | ○ Trainer's Cap | ● mystery hints | ● karma hint | |
| **Pet** | | ● unicorn karma | | | | | | ● Trainer-related | ● Fenrir pet | ○ | — | ● Soul Sphere is mystery reward | | |
| **Mystery (13)** | | | ● 13 altars | ● Fisher King mystery | | | | ● Fisher King quirk | | ● hints | ● Soul Sphere | — | | |
| **NPC (10)** | | ● ONLY source | | | ● judgment | | ● Abaddon | | | ○ | ● merchant Soul Sphere | | — | |
| **Bones** | | | | | | | | ● Loki farm | | | | | | — |
| **Death chase** | ● cooked HP matters | | | ● Death-freeze | ● Sword still works | | ● post-Abaddon | | | ● 5 endings | | | | |
| **Damage types** | | | | | ● Sword ignore_resist | | ● bosses have resists | | | | | | | |

---

## D. The "big four" mega-secrets — confirmed details

### 1. Death-kill ritual (the invocation-tier ending)

Four items + the Stone, across the whole dungeon:

| Item | Floor band | Source |
|---|---|---|
| Abyssal Shimmer | L1-20 | Random lore-quest spawn |
| Philosopher's Wrench | L21-49 | Random lore-quest spawn |
| Scroll of the Lake of Fire | L50-79 | Random lore-quest spawn |
| Tablet of Second Death | L80-99 | Random lore-quest spawn |
| Philosopher's Stone | L100 | Abaddon drop |

**Sequence (corrected from code at `game_magic.py:1953-1979`):**
1. Carry Stone up from L100
2. Combine Stone + Tablet via Wrench → Complete Tablet of Second Death
3. Place Complete Tablet on the Abyssal Shimmer tile
4. **Lure Death onto the Shimmer tile** during the escape chase
5. Read Lake of Fire scroll while Death AND Complete Tablet are both on the Shimmer
6. Abyss opens beneath Death's feet → Death is consumed → Death's Bane scroll drops with prestige reward code

The code requires `death_monster.x == shimmer.x AND death_monster.y == shimmer.y` — so the player must position Death precisely on the ritual tile, then read the scroll from a safe distance. The chase mechanic, the ritual placement, and the scroll-read all converge on one decisive turn.

**Hint quality:** Excellent — every artifact self-narrates, Revelation 20:14 inscription tied through.

### 2. Vidar's Sandal (Fenrir alt-kill)

10 leather scraps across L5-L73. Each scrap's individual lore explicitly says it's **useless**. At L79 there is a Vidar's Altar — assembling the scraps there produces the Sandal. Equipped, on first hit vs Fenrir at chain ≥ 1 = **instant kill**.

**Hint quality:** **WEAK.** Only inverted T5 hint: *"useless scraps... not useless at all"*. No direct Vidar reference anywhere in hints.

### 3. Reforged Gram (Fafnir alt-weapon)

At L53 there is Odin's altar. The "obvious" path is to DROP the Broken Gram on the altar — you get Sigurd's Shovel (Layer 1, in-pit fight bonus). The MEGA SECRET path is to **THROW** the Broken Gram OVER the altar (using throw mechanic, not drop). On the throw arc, Gram is reforged into a Tier-5 lightning blade with `ignore_resistances` and 9× max chain — usable against Fafnir AND beyond.

**Hint quality:** **WEAK.** Only Gungnir T5 hint nods at the throw archetype. No direct hint for the throw-over mechanic.

### 4. Cow Level (Diablo II nod)

**Corrected from code at `main.py:124-129`, `game_encounters.py:38-48`:**

Not just any cow — there is a **specific `secret_cow` NPC** that spawns exactly once per run on a randomized floor (`_cow_level = randint(30, 39)`, chosen at game start). The cow:
- Is a Monster entity with `id='secret_cow'`, `name='a cow'`, symbol `C`
- Does NOT despawn (unlike other NPC encounters which can leave the level)
- Tracks pokes in `_cow_poke_count`
- Opens portal to L999 Moo Moo Farm on the 10th poke

Inside the cow level: 40-50 Hell Bovines + Cow King. Reward: Cow King's Horns (`chain_bonus +1` permanent).

**Hint quality:** **NONE.** Only T3 line about "rare creatures that appear once." A player without genre knowledge won't know to poke the specific cow they find on the random L30-39 floor.

**The randomization pattern here (random floor at game start + persistent flag + non-despawn) is exactly what the other quest altars SHOULD do but currently don't — see Section H.13.**

---

## E. The repeating boss-quest design pattern

Now that I've mapped all 5 bosses, the pattern is beautiful and consistent:

```
PREP ALTAR (3-4 floors before boss)
   ↓ ritual interaction (drop, throw, place)
QUEST ITEM (boss-killer or boss-defanger)
   ↓ equip / carry
BOSS ARENA (special tile features)
   ↓ optional arena-altar prayer (some bosses)
BOSS FIGHT (multi-phase or single)
   ↓ kill
POST-KILL DROP (final quest hint)
```

| Boss | Prep altar | Quest item | Arena altar | Post-kill |
|---|---|---|---|---|
| Asterion | L17 Ariadne fountain | Ariadne's Thread | none | — |
| Medusa | L37 Athena | Aegis / Eye of Graeae | generic nave altar (no special handler) | — |
| Fafnir | L53 Odin | Sigurd's Shovel OR Reforged Gram | none in lair | Fafnir's Blood vision |
| Fenrir | L76 Dwarven Forge + L79 Vidar | Gleipnir AND/OR Vidar's Sandal | generic Grand Hall altar | — |
| Abaddon | L99 Judgment + seal grind | Sword OR Scales of Michael | **6 hex-ring altars (special handler)** | Stone drop → Death-kill quest |

**Abaddon is unique in having a real arena-altar mechanic.** Medusa and Fenrir have altars in their arenas but they use the generic prayer handler (no boss-resist-strip equivalent). **Open design question:** should Medusa, Fafnir, Fenrir arenas have their own resist-strip altars too, or is L100 intentionally the only one?

---

## F. Critical findings — what the prior audit got wrong or missed

1. **THAC0 -16 is a DATA convention, not a code clamp.** 70 monsters share that value in JSON but no code line enforces it. Means we can introduce monsters with thac0 < -16 freely.
2. **Cooking softcap (1000) doesn't scale with floor.** The known issue — fix is one term in the cap formula.
3. **6 altars in a hex ring at L100.** The audit asked how many; the answer is six.
4. **Sword of Michael's 4× critMultiplier** stacking with 16× max chain is the numeric outlier.
5. **Karma is invisible to the player** until judgment screen. No in-game indicator.
6. **Failed L100 prayer (chain 0) still consumes an altar.** Possibly intentional stakes, possibly bug.
7. **Fisher King quirk + Fisher King mystery stack** prayer cooldown ÷4 — both intentional per code, but neither hint mentions stacking.
8. **Ariadne's Thread leaks to vampires** (Phase 2 fix pending).
9. **Pandora's Coffer is INVERTED** — failing the economics quiz is the success path.
10. **Khopesh of Anubis has an INDEPENDENT max_hp track** bypassing the cooking softcap.
11. **`get_int_quiz_bonus()` only applies to philosophy** despite docstring claiming three subjects.
12. **`HP_PER_LEVEL = 0` and `STAIR_REST_CAP_DESC = 0`** — confirms cooking is THE only scalable HP track during descent.
13. **Heavenly Host (Scales of Michael) is a separate Layer 2.5** — angel counter-spawn vs Abaddon's locusts. Missed entirely by prior audit.

---

## G. Discoverability gap inventory — secrets with WEAK or NO hint trails

| Secret | Hint quality | Risk |
|---|---|---|
| **Cow Level entry** | None | HIGH — non-genre players won't find |
| **Gram reforge (throw-over)** | Weak (Gungnir nod only) | HIGH — most spectacular weapon, near-undiscoverable |
| **Vidar's Sandal** | Weak (inverted T5) | HIGH — scrap lore says useless |
| **Flux Capacitor** | None | HIGH for non-McFly players |
| **L100 altar resist-strip** | Moderate (general altar hints) | MODERATE — specific mechanic unhinted |
| **Fisher King ×2 stacking** | None | LOW — emergent reward |
| **Hidden character UNLOCK mechanism** | None (characters hinted, unlock-method not) | MODERATE |
| **Corpse philosophy-quiz examine** | None | LOW — emerges from menu |
| **Pet system assembly** | Half-hinted across 3 T5 cues | MODERATE |
| **Karma scoreboard during play** | None | DESIGN QUESTION — should it be visible? |
| **Family character builds** | None | INTENTIONAL — personal Easter eggs |

---

## H. INCOMPLETE / orphan findings — **status after developer review**

1. ~~**"Black Stone"** referenced in audit context but absent from artifact.json~~ — **RESOLVED:** drop the reference, likely was `cursed_lodestone`.
2. ~~**Achilles build** greeting promises heel-vulnerability~~ — **DEFERRED:** secret character build polish is a follow-up task, not core gameplay.
3. **Seal artifacts** — **CONFIRMED FIX NEEDED:** they should SHATTER on Seal Demon kill with one-time flavor text (one per seal, 7 distinct). Currently sit in inventory at weight 0.1 each.
4. **Cow King story popup + chronicle entry** — **CONFIRMED FIX NEEDED:** add to `_BOSS_STORY_KEYS` and `_BOSS_CHRONICLE`. Tone: absurdist (the whole cow quest is absurd).
5. **Persephone Q6 fix** — **CONFIRMED FIX NEEDED:** Q6 grants a one-shot regeneration power use (V-menu pattern matching `atlas_burden` etc.). Independent of cooking softcap. Persephone's annual return from underworld = a one-time gift of life.
6. ~~**T2 Judgment hint says "thirtieth depth"**~~ — **DEFERRED:** full hint bank pass is a separate task after the curve is built.
7. **`get_int_quiz_bonus()` mismatch** — **CONFIRMED FIX NEEDED:** remove entirely. Vestigial half-implementation. WIS already covers timer; INT covers max MP; no duplication needed.
8. ~~**Diogenes' Lantern counter**~~ — **INTENDED:** the player isn't meant to know the counter exists. That's how the quirk works.
9. **`gain_level` potion** — **CONFIRMED FIX NEEDED:** remove entirely. Game-breaking shortcut, not lore-appropriate.
10. ~~**No L40/L60/L80 arena altar mechanics**~~ — **INTENDED:** generic altars in those arenas are level dressing only. The L100 resist-strip system is intentionally unique to Abaddon.
11. ~~**Necronomicon voice break**~~ — **INTENDED:** Evil Dead joke. Voice violation is intentional here and in similar in-jokes.
12. ~~**Duplicate hints**~~ — **DEFERRED:** full hint bank pass is a separate task.
13. **Quest altars currently fixed-floor** — **CONFIRMED FIX NEEDED:** Ariadne (L17), Eye of Graeae (L29), Athena (L37), Broken Gram (L48), Odin (L53), Dwarven Forge (L76), Vidar (L79), and the 10 leather scrap floors should all randomize within ±3 floor windows at game start (mirror the cow pattern at `main.py:129`). L99 Judgment and L100 hex ring stay fixed (day-of-reckoning).

**Active fix list (post-curve work):** items 3, 4, 5, 7, 9, 13. All deferred to after the unified curve is built — they may interact with curve tuning.

---

## I. What the agents disagreed on (worth your eye)

**Vidar's Sandal hint trail:**
- Lore agent reports a multi-link bridge: leather scraps → altar → Sandal → Fenrir (counts it as a hint trail in T5)
- Hidden agent reports no Vidar-named hint anywhere
- Both are right — the trail exists via inverted hints ("not useless at all") but it doesn't name Vidar or assemble the picture explicitly

**Boss-arena altar count:**
- Boss agent says "L40 generic nave altar" — exists but generic handler
- Divine agent says "L80 generic Grand Hall altar" — exists but generic handler
- Hidden agent confirms only L100 has the special resist-strip system

**Karma effects:**
- Boss agent: karma is one-directional input to L99
- Divine agent: karma is bidirectional — negative AND positive both have specific Abaddon-fight modifications

---

## J. Your validation list — please mark each

A quick way to validate: read sections A, B, and C and tell me:
1. **System inventory** — anything missing from A? Anything I labeled wrong?
2. **Boss quest layers** — anything missing from any of the 6 bosses in B?
3. **Cross-system grid** — anything in C that's wrong, or any cell I left blank that shouldn't be?
4. **Mega-secrets** — D should be complete; flag if I missed one
5. **Open questions in H** — pick any you want to answer now, defer the rest

Once you confirm or fill gaps, Stage 2 (the corrected unified curve) has proper grounding and we can build `tools/balance/curve.json` against a real understanding of the layered design.

---

**Source documents:**
- `tools/balance/systems/bosses_and_quests.md` (67 KB, 1426 lines)
- `tools/balance/systems/divine_systems.md` (35 KB, 825 lines)
- `tools/balance/systems/secrets_and_easter_eggs.md` (53 KB, 693 lines)
- `tools/balance/systems/progression_systems.md` (40 KB, 756 lines)
- `tools/balance/systems/lore_coverage.md` (81 KB, 742 lines)

All read-only. No code touched.
