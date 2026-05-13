---
version: 1
date: 2026-05-13
subject: geography
in_game_action: equipping armor / shields (threshold mode)
style_verdict: WONDER-DRIVEN — places as portals to amazement
---

# Subject: Geography

The geography bank teaches kids that the world is **vast, varied, and full of wonder**. Place names — Paris, Petra, Vienna, Kyoto, Iguazu, Baikal, Cusco, Marrakech — should arrive in their ears already glowing with adventure. The bank is not capitals + countries + flag-ID; it is a **guided tour of the beautiful world we live in**, where every question links a real place to a real wonder: an ancient building, a natural marvel, a cultural birthplace, an earth-process that makes a place uniquely magical.

In-game, the player answers geography questions when equipping armor or shields (threshold mode).

## 1. Timing budget

| Stat | Value |
|---|---|
| `SUBJECT_TIMER` | `('geography', (28, 1.2))` in src/player.py |
| Total timer at WIS 10 | **40s** |
| Total timer at WIS 25 | **58s** |

Generous — by design. Wonder content needs room for scene-setting; the player should read with curiosity, not panic.

## 2. Per-tier char budgets (answer-outlier rule applies)

| Tier | Hard cap | Voice |
|---|---:|---|
| T1 | ≤ 280 | Short framing + place-name + crisp wonder fact |
| T2 | ≤ 480 | One-line scene + the wonder + the place name foregrounded |
| T3 | ≤ 680 | Scene with specifics + cultural/historical/scientific context |
| T4 | ≤ 900 | Multi-sentence setup + named details + the wonder paid off |
| T5 | ≤ 1100 | Deep wonder with history + science + people + the magical specific |

## 3. The PLACE → WONDER pattern (the core voice rule)

Every question follows this shape:

> **[Place name, lightly framed]** + **[magical specific fact]** + **[question that pays off the wonder]**

Examples:

- *"Beneath the streets of Paris, the capital of France, an immense network of tunnels holds the bones of roughly six million people, moved there in the 1780s when the city's overflowing cemeteries became a public-health crisis. What are these tunnels called?"* → **The Catacombs of Paris**

- *"In the ballrooms of 1820s Vienna, a scandalous new dance scandalized polite society because couples held each other in a closed embrace and spun in fast triple-meter circles. What dance is it?"* → **The Waltz**

- *"Lake Baikal in southern Siberia, crescent-shaped between mountain ranges, holds roughly one-fifth of all the unfrozen freshwater on Earth — more than all five North American Great Lakes combined. Living in its depths is the golomyanka, a translucent fish so adapted to the cold dark that it dissolves into oil at the surface. Baikal is also the world's:"* → **Oldest lake (25+ million years old)**

The place name is **always present** and **always concrete**. The wonder is **always a real fact**, not invented atmosphere.

## 4. Stance summary

Geography is less contested than science or AI, but the bank still takes a substantive line where it matters:

| Topic | Stance |
|---|---|
| Age of Discovery / Western exploration | CELEBRATED — Magellan, Cook, Lewis & Clark, Mercator, Marco Polo as one of humanity's great chapters |
| Colonialism | HONEST — both costs (extracted labor, dislocations, plantation economies) AND benefits (legal systems, railways, end of practices like sati and foot-binding); no one-sided framing |
| Western civilization's reach | CELEBRATED — Roman roads, Christendom's spread, the global lingua franca of English |
| Climate as geography | COVERED — climate zones, monsoons, El Niño, glaciation; cataclysm-narrative avoided |
| Contested borders | NAMED honestly — Taiwan (de facto independent, PRC claim), Crimea/Donbas (Russian-controlled, internationally Ukrainian), Kashmir (split), Israel/Palestine (covered with care but without false equivalence) |
| Indigenous civilizations | CELEBRATED as full civilizations — Inca road networks, Mayan astronomy, Cahokia mound-city, Polynesian wayfinding — not condescended-to |
| Religious sites | TREATED WITH RESPECT — Mecca, Jerusalem, Bodh Gaya, Varanasi, Notre Dame, St. Peter's, Hagia Sophia, Angkor Wat — without secular dismissal |
| Soviet / Maoist legacy on geography | HONEST — Aral Sea collapse, Three Gorges costs, Great Leap famine geography, Gulag map |
| Demographics | FACTUAL — population pyramids, Japan/Korea fertility, African demographic dividend, urbanization — without taboo |

## 5. Voice rules

### Foreground the place name

A question without a recognizable place name visible in the prompt has failed the assignment. The whole point is that kids leave hearing "Petra," "Bukhara," "Cusco," "Lhasa" and feeling that those words mean something magical.

### Wonder over utility

Don't write strategic / geopolitical / chokepoint questions for this bank — those belong elsewhere if at all. Don't write "What does Singapore export?" Write "Singapore is one of only three city-states in the world, and at low tide its land borders extend by 22% as reclaimed islands appear — what process built most of modern Singapore?"

### Scene-led, never definition-led

- Bad: *"What is a fjord?"*
- Good: *"Norway's western coast is cut by deep glacier-carved inlets where the sea reaches inland for up to 200 km between near-vertical cliff walls. Sognefjord, the longest, runs deeper than the Atlantic just offshore. What is this kind of coastal feature called?"*

### Cross-link relentlessly

Place → dance, place → food, place → architecture, place → battle, place → invention, place → painter, place → poet, place → astronomical observation, place → animal, place → geological event. The web of associations IS the bank.

### Real names, real dates, real specifics

If a question mentions "in 1820s Vienna" or "Hungarian physician Ignaz Semmelweis," the date and name must be true. Fabrication poisons the magic.

### Active voice, present-tense wonder

- "The Pyramids of Giza were aligned..." — past tense fine for historical fact
- "Iguazu Falls thunders down 275 separate cataracts across the Brazil-Argentina border" — present-tense for living wonders

### No "did you know" preamble

Trust the content to land. Don't write "Did you know that..." — just lead with the wonder.

## 6. Quality gates

| Gate | Configuration |
|---|---|
| schema | required (tier, question, answer, choices×4, context) |
| length_parity | answer-outlier rule (1.6× multiplier) — same as cooking/animal/grammar/science/ai |
| length_budget | per-tier cap (280 / 480 / 680 / 900 / 1100) |
| anti_rote | NOT exempted; geography-specific extensions in v2 (TODO) |
| duplicate | 0.85 similarity threshold |

The anti-rote regex already bans `^What is the capital of`, `^Which (city\|country\|...)`, `^What (is\|does) ['"]`, `^In what year did`, `^Who (wrote\|invented\|...)`. Those are exactly the patterns this bank should never use.

Geography-specific anti-rote patterns to add in v2 (not blocking v1 release): `^What (body of water\|sea\|gulf\|strait) separates`, `^What is the (largest\|longest\|highest\|deepest)`, `^Which (river\|range\|mountain\|peak) (runs\|flows\|lies\|is)`.

## 7. Distractor design

- **Wonder facts**: distractors should be **adjacent-but-wrong real facts** — never joke options, never "a mineral / a plant / a person." For Lake Baikal "the world's oldest lake," good distractors are "the largest by surface area," "the only saltwater lake," "the only completely frozen lake." Each is plausibly something Baikal *could* be the world's, but isn't.
- **Architecture / monuments**: distractors are real adjacent structures or features. For Angkor Wat questions, distractors might reference Borobudur, Bagan, Prambanan — real adjacent answers.
- **Cultural birthplaces**: distractors are other real plausible birthplaces. For "tango originated in...", distractors are "Madrid," "Lisbon," "Havana" — places where Latin music actually has roots.
- **Earth systems**: distractors are wrong-mechanism real processes. For "Why is the Atacama the driest place on Earth?", distractors are real meteorological processes that don't apply.

## 8. Anti-patterns

- **Place-name-only questions** ("Madagascar is which kind of place?") — no wonder
- **Capital / country / flag identification** — banned by anti-rote regex
- **Strategic / geopolitical framing** ("Why does Taiwan matter for chip supply?") — wrong bank
- **Climate-alarmist framing** ("How is climate change destroying X?") — wonder over polemic
- **"All cultures equal so we won't celebrate Western achievement"** — fail; Magellan and Cook are giants
- **Tourist-brochure puffery** ("magical mystical exotic") — show the specific wonder, don't gesture
- **Made-up "facts"** — every specific must be real; check before submitting
- **Pronoun antecedents over 8 words apart** (per generate.md phrasing rules)
- **Term-before-definition** — if you introduce "polje" or "fjard," explain or scene-set first

## 9. What success looks like

- A T1 question makes a kid hear "Iceland" and learn it sits on a continental rift mid-ocean
- A T2 question makes them hear "Buenos Aires" and learn the tango was born in its dockside neighborhoods
- A T3 question makes them hear "Sahara" and learn it was savanna 6,000 years ago and may be again
- A T4 question makes them hear "Easter Island" and learn the moai walked themselves there by rocking gait
- A T5 question makes them hear "Bukhara" and learn it was the center of medieval astronomy under Ulugh Beg
- **Kids leave the bank wanting to GO somewhere — anywhere — and knowing the world is bigger and stranger and more beautiful than they thought.**
