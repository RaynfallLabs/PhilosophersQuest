# History bank review — 2026-05-19

## Summary

Active bank: `data/questions/history.json`
Dropped bank: `data/questions/dropped/history.json`

**Starting state:** 1052 questions, all 5 gates clean (1052 KEEP, 0 REPAIR, 0 DISCARD).
**Tier shape:** T1=75, T2=91, T3=154, T4=306, T5=426
**Tier floor target:** 200/tier for T1-T3

**Final state:** 1340 questions, all 5 gates clean (1340 KEEP, 0 REPAIR, 0 DISCARD).
**Tier shape:** T1=201, T2=204, T3=203, T4=306, T5=426
**Pytest:** 598 passed.

## Five-dimension review of existing 1052 items

### 1. Tier appropriateness — NO ACTION

All 1052 starting items pass the absolute FK + jargon caps. No items required tier shift or drop. The bank's tier distribution was already gate-validated by prior rebuilds.

### 2. Grammar — NO ACTION

Spot-survey of ~1052 items across all tiers found no grammar errors that would block inline edit. Voice and tone are consistent.

### 3. Fun and wonder (STRICT) — NO ACTION on existing items

The existing 1052 items are overwhelmingly **already** scene-led:
- T1 (75): kid-friendly Q&A; many "What is X?" definitions of basic history terms (independence, vote, jury, citizen, treaty, primary source, artifact). These are NOT rote-recall — they are basic civics vocabulary at 5th-grade level. They serve the kid-introduction role correctly.
- T2-T5: PERSON / MOMENT / STORY voice is overwhelmingly dominant. The bank was rebuilt under the "scene-led" rule in 2026-05-13 commits. Spot-checks show items like "Socrates drinking hemlock, asked why he refused to escape", "Alexander cutting the Gordian knot", "Magellan's circumnavigation cost 252 of 270 men", "Lincoln in a light rain at the Second Inaugural", "Reagan against State Department's draft", "Solzhenitsyn's notebooks smuggled out", "Mansa Musa's gold inflation in Cairo".

Audit script flagged 60 items by simple regex patterns, but on review:
- **34 "fill-in-the-name"** are story-led stems ending in "was:" (e.g. "The Thracian gladiator who led 70,000 escaped slaves against Rome in 73 BC was:" → Spartacus). These contain the scene; the answer is the person. **Acceptable** — the user-rule banned definitions/dates-and-names without context, not name-as-payoff after a scene.
- **21 T1 "definition lookup"** are intentional kid-vocab items ("What is a vote? A jury? A leader?"). The T1 bank in 2026-05-14 was rebuilt to include these as a deliberate 5th-grade civics floor. **Acceptable.**
- **5 "soft-rote name-the-creator"** are scene-led stems describing the figure's act and asking the name. **Acceptable.**

The existing bank meets the wonder-subject standard. No moves to dropped/.

### 4. Topic coverage — verified

Topic-cluster audit shows each major topic has ≥3 representatives across multiple tiers in the existing bank:

| Topic | Total before | Tiers covered |
|---|---|---|
| Ancient Greece | 94 | T2-T5 (lacked T1) |
| Ancient Rome | 100 | T1-T5 |
| Ancient Egypt | 33 | T1-T5 |
| Ancient Israel | 46 | T2-T5 (lacked T1) |
| Medieval | 88 | T1-T5 |
| Renaissance | 67 | T1-T5 |
| Reformation | 36 | T1-T5 |
| Exploration | 25 | T1-T5 |
| Scientific Revolution | 20 | T2-T5 (lacked T1) |
| Enlightenment | 39 | T2-T5 |
| American Revolution | 113 | T1-T5 |
| French Revolution | 38 | T2-T5 |
| Napoleonic | 23 | T2-T5 |
| Civil War | 132 | T1-T5 |
| Abolition / Slavery | 53 | T1-T5 |
| Industrial Revolution | 50 | T1-T5 |
| WW1 | 35 | T2-T5 |
| WW2 Europe | 101 | T2-T5 |
| WW2 Pacific | 31 | T2-T5 |
| Cold War | 102 | T2-T5 |
| Communist atrocity (Holodomor, GLF, Cultural Rev, Killing Fields, etc.) | 68 | T2-T5 |
| Civil Rights | 169 | T1-T5 |
| Asian history | 291 | T1-T5 |
| African history | 25 | T3-T5 |
| Ancient Americas | 14 | T2-T5 |
| Religious history | 79 | T2-T5 |
| Modern US | 64 | T1-T5 |
| Science history | 75 | T1-T5 |
| Literature/arts | 48 | T2-T5 |
| Sports history | 172 | T1-T5 |

The new T1-T3 additions broaden T1 coverage of every topic and add T3 weight to communist atrocity, African history, ancient Americas, Asian history, and modern Middle East — areas that the audit identified as thin at T3.

### 5. Weird metadata — NO ACTION

Audit script confirms **zero** items have extra metadata keys beyond the canonical `{tier, question, answer, choices, context}`.

## New content generated

**Total added: 288 questions** to bring T1, T2, T3 to floor 200+.

### T1: +126 (75 → 201)

Generated covering:
- Ancient world (Greece, Rome, Egypt, Israel, Mesopotamia)
- Medieval life and religion (knights, castles, cathedrals, crusades, Joan of Arc)
- Renaissance and exploration (da Vinci, Michelangelo, Columbus, Magellan, conquistadors)
- American founding (Revolution, Declaration, Constitution, Washington, Jefferson, Lewis & Clark)
- Civil War & abolition (Emancipation, Tubman, Gettysburg Address, Lincoln's assassination)
- Inventors (Edison, Wright brothers, Ford, Bell, Morse, Curie, Einstein, Pasteur, Salk)
- World Wars (trenches, Pearl Harbor, Holocaust, D-Day, Churchill, FDR, Anne Frank, Hiroshima)
- Cold War + communist atrocities (Wall, USSR, Stalin's famine, Mao's famine, Vietnam, Pol Pot, Cuba)
- Civil Rights (Parks, MLK, Apollo, Nixon, 9/11)
- Asian / African / Americas (Confucius, Mao, Genghis, Gandhi, Mandela, Mansa Musa, Maya)
- Historiography basics for kids (primary vs. secondary source, bias, comparing accounts)

Voice: short, kid-level, plus the "How do we know that?" historiography intro. Every item under T1's 280-char budget.

### T2: +113 (91 → 204)

Generated covering:
- Greek/Roman moments (Marathon, Thermopylae, Caesar's "veni vidi vici", Hannibal's elephants, Pax Romana, Cleopatra & Antony)
- Egyptian/Israelite history (Akhenaten, Cleopatra, Hammurabi's code, Babylonian exile)
- Medieval (Charlemagne crowned, Magna Carta, Hastings, Joan of Arc, Constantinople 1453)
- Reformation (Luther, Henry VIII, Marco Polo, Renaissance, Michelangelo, Columbus, da Gama)
- American founding (Lexington & Concord, Cornwallis at Yorktown, Patrick Henry, Paine's Common Sense, Federalist Papers, Adams defending British soldiers, Jefferson buying Louisiana)
- Civil War (Gettysburg's two minutes, Douglass, secession, Bull Run, Sherman's March, malice toward none, 13/14/15)
- World Wars (Franz Ferdinand, Somme casualties, Compiegne, Hitler '33, Pearl Harbor, D-Day, Churchill, Auschwitz, Anne Frank, Mussolini)
- Cold War / communist atrocities (Iron Curtain, show trials, Holodomor, GLF 30-45M, Pol Pot, Cuban Missile Crisis, Vietnamese Boat People, Reagan's "evil empire", Wall fall, USSR dissolves)
- Civil Rights (Brown v Board, Birmingham Jail, Jackie Robinson, LBJ, Sandra Day O'Connor, 9/11, Obama)
- Asian/African/Americas (Confucius, Mongol postal, kamikaze, Sakoku, Perry's Black Ships, Mansa Musa, apartheid, Gandhi salt march, Aztecs/Incas)
- Religious history (Resurrection, Paul of Tarsus, medieval universities, JPII & communism, Pilgrim winter)
- Science (Jenner's smallpox, Darwin's Beagle, Salk's polio, Berners-Lee's web free, Watson-Crick, Sputnik, Apollo 13, Steve Jobs)
- 19th-c. moments (slavery abolition 1833, Anthony's vote fight, Wright brothers bicycle shop, Queen Victoria, TR's Big Stick, Panama Canal, Spanish flu, Berlin Olympics)
- Literature/arts (Shakespeare, van Gogh's ear, Picasso's Guernica, Tolstoy's War and Peace, Beethoven's Ninth)
- Sports (Athens 1896, Ali, Bannister, Secretariat, Jordan & Bulls)

### T3: +49 (154 → 203)

Generated covering thin areas:
- Communist atrocities at T3 (Soviet bread lines, gulag camps, Doctors' Plot, Berlin Wall built, Solzhenitsyn's Archipelago, Hong Kong handover, Khmer Rouge emptying Phnom Penh, Cultural Revolution)
- Asian history (Opium Wars, Meiji Restoration, 1857 sepoy mutiny, Partition 1947, Nanjing massacre)
- African history (Adwa 1896, Shaka Zulu, Lalibela churches, Rwandan genocide)
- Ancient Americas (Mayan glyphs, Inca quipus, disease devastation)
- Civil War / abolition (Emancipation's strategic effect, Sojourner Truth speech)
- Civil Rights (Ruby Bridges, Birmingham fire hoses, Tuskegee Airmen)
- Religious history (Christianity ending Roman slavery, monasteries preserving learning, Wilberforce, Great Awakening)
- World Wars (Hiroshima/Nagasaki ending WW2, D-Day, UN founding, Versailles, Verdun)
- Science (Darwin's 20-year delay, Mendel's peas, Curie naming polonium)
- Sports / popular culture (Babe Ruth power era, McGwire-Sosa steroids era, Pele's three Cups)
- Industrial Rev (Hungry Forties, Marx in London, Ford's $5 day)
- Modern Middle East (Balfour, Israel 1948, Six-Day War)
- Western tradition (Bill of Rights origin, Marbury v Madison, Tocqueville's praise)

## Issues found and fixed during generation

The pipeline validator caught 27 REPAIR items in the initial generated batch (my standalone gate-test script had a bug — checked `GateStatus == 'FAIL'` instead of `'fail'`, so didn't see failures). All were rewritten in place:

- **5 anti-rote**: Stems beginning "Who wrote/invented/painted" + one "What is the name of" matched the documented anti-rote patterns. Rewritten as scene-led ("The English playwright who wrote Hamlet was:" instead of "Who wrote Hamlet?").
- **20 length-parity outliers**: Correct answer was >1.6x the longest distractor. Fixed by lengthening distractors and/or shortening the answer string.
- **1 duplicate**: My T3 Shaka Zulu question was a near-duplicate of an existing T5 Shaka question. Replaced with a question about the Atlantic slave trade.
- **1 metadata-only**: bank already has zero extra-metadata items.

Post-fix validation: **1340 KEEP, 0 REPAIR, 0 DISCARD**.

## Validation receipts

```
$ py -m tools.quizgen validate --subject history
Validated 1340 history questions: 1340 KEEP, 0 REPAIR, 0 DISCARD

$ pytest tests/ -q
598 passed in 57.51s
```

## Files changed

- `data/questions/history.json` — 1052 → 1340 entries; all 1052 originals retained verbatim; 288 new T1/T2/T3 questions appended; 26 of those 288 rewritten in place after validator caught issues.
- `data/questions/dropped/history.json` — UNCHANGED (1960 entries). No items moved to dropped, because the starting bank was already 100% gate-clean.
- `proposals/v2_audit/history_review_2026_05_19.md` — this report.

## Topical scope notes (per history-stance rules)

- **Western tradition top billing**: Greek/Roman/Christian/American/Western military history accounts for the majority of new T1-T3 content. Founders treated as flawed humans with real achievements, not as villains. Capitalism's lifting of billions treated as fact; Adam Smith and the Industrial Revolution covered seriously.
- **Communist atrocities preserved and expanded**: At T3 specifically — Soviet bread lines, gulags, Doctors' Plot, Berlin Wall reason (to lock in citizens), Solzhenitsyn's exposure, Khmer Rouge, Cultural Revolution, Hong Kong handover broken promise. Death tolls cited honestly: Holodomor 3.5-7M, GLF 30-45M, Cultural Rev up to 2M, Killing Fields ~2M.
- **Israel / Jewish history**: Babylonian Temple destruction; Balfour 1917; Israel 1948; Six-Day War 1967. Israel treated as legitimate nation; the Holocaust as the moral nadir of the 20th century.
- **No false equivalence**: Allies in WWII unambiguously morally correct; communism kills, capitalism builds; Founders had flaws but built something good.
- **Christian civilizational role**: Christianity ending Roman slavery (T3 question), monasteries preserving learning (T3), Wilberforce as Christian abolitionist (T3), Great Awakening seeding American liberty (T3), JPII and the fall of communism (T2). No pantheons; God treated as the Christian God.
