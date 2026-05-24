# History Bank Framework (2026-05-24)

> This doc is subordinate to `docs/quiz/moral_vision.md` (the bank's soul, supreme authority) and `proposals/v2_audit/SHARED_PRINCIPLES.md` (cross-subject universal rules). Both override anything here. Read them FIRST.

History is the **story of humanity**. The bank teaches kids that real people faced real choices under real pressure, and that what they did shapes the world we live in. Kids should leave hearing names — **Thermopylae, Magna Carta, Trenton, Gettysburg, Solzhenitsyn, Sobieski, Wilberforce, Reagan, Brunelleschi, Akbar, Saladin, Galois** — and feel those names *mean* something.

In-game: history questions trigger when equipping accessories (threshold mode). Subject timer 50s @ WIS 10 (base 34 + WIS·1.6 per `src/player.py:23`).

## Core principle

A 5th–10th grader should leave this bank with:
- **Memorable details on the tip of their tongue** — "Victory or Death," the herringbone brick pattern of Brunelleschi's dome, "I have not time" scrawled in Galois's margins, Walter Duranty's privately-conceded 10 million dead. The cool fact is what they OWN.
- **Western tradition as a real human achievement** — Athens → Rome → Christendom → Reformation → Scientific Revolution → Enlightenment → American Founding as a single unbroken inheritance worth knowing
- **American story deep** — Washington's character + decisions, Lincoln's moral clarity, the actual cause of the Civil War (slavery, per the Confederate states' own declarations), the abolitionist tradition as a Christian achievement, the civil rights movement as moral victory
- **20th-century communist atrocities honestly counted** — Holodomor 3.5–7M, Great Leap 30–45M, Khmer Rouge 2M, Gulag scope, Walter Duranty's *New York Times* cover-up explicitly named; specific perpetrators identified; no false equivalence
- **The Cold War as moral conflict** — Reagan-Thatcher-John Paul II coalition celebrated; Solidarity, Sakharov, Solzhenitsyn as heroes; the Berlin Wall as an evil that needed breaking
- **Non-Western civilizations on their own terms** — Han astronomers, Tang poets, Mughal architecture, Mansa Musa's pilgrimage, Polynesian wayfinding, the Aztec calendar — substantive civilizations with their own achievements, NOT exotic foils
- **Honest record of pre-modern brutality** — Aztec mass sacrifice (Templo Mayor 1487, 20,000–80,000 in four days), Iroquois/Plains torture rituals, Dahomey + Benin human-sacrifice altars, internal African slave trade, Hindu suttee, Chinese foot-binding, Thuggee strangulation, Fijian cannibalism — stated as fact, paired with the named Western interventions that ended them (Wilberforce, William Carey, Las Casas, William Bentinck, the Royal Navy West Africa Squadron)
- **Western art + architecture + music traced through the ages** — Parthenon, Hagia Sophia, Chartres, Brunelleschi's dome, Sistine ceiling, Bach, Beethoven's deaf-premiere of the 9th, Stravinsky's *Rite of Spring* riot — the great structures and statues and paintings and cathedrals as inheritance worth celebrating
- **Drama of the great minds** — Galois's duel-night margins, Hypatia torn apart 415 AD, Pascal's mystical night sewn into his coat, Newton-Leibniz priority dispute, Tycho's silver nose, Boltzmann's tombstone, Turing's apple, Ramanujan's letters, Perelman's refusals — the human at the breaking point across every tier

## What this framework forbids

1. **Dry date / who-invented framing** — banned by anti_rote regex. `^In what year did`, `^Who (wrote|invented|painted|composed|founded|tutored|discovered)`, `^What is the capital of`, `^Which (city|country|...)`, `^What (is|does) ['"]`, `^Define` all rejected at the pipeline gate. Per `feedback_no_rote_wonder`.
2. **"Both sides" false-equivalence on communist atrocities** — fail. Show the death toll honestly. Walter Duranty's *NYT* cover-up is named; the Holodomor's 3.5–7M is stated; Mao's 30–45M is stated.
3. **1619-project framing as if neutral historical fact** — fail. The American Founding was about natural rights and self-government, not primarily about slavery; the bank does not adopt the reframe as the founding story.
4. **Sanitizing slavery / Jim Crow / Holocaust / Gulag / Aztec sacrifice / Plains torture** — fail. Show the evil. Honest history requires the practices stated plainly, not euphemized.
5. **Sanitizing Founders or hero-figures into hagiography** — also fail. Show Washington's slavery contradictions, Jefferson's hypocrisies, Hamilton's affair, the Founders as flawed humans who built something extraordinary.
6. **Current-politics quagmires (post-~2010 contested events)** — out of scope. Settled events through ~2010 are fine; active politicians in current debates are not. ChatGPT 2022 and Mandela's death 2013 in scope (historical fact, not political debate).
7. **Fabricated quotes, dates, or facts** — fail. If the question names "Wilberforce" or "1683" or "Galois May 31 1832," the name and date must be true. Real specifics only.
8. **Anti-anti-white framing** — banned per moral_vision §9. Honest history of Western failures (slavery, religious wars, colonialism) is REQUIRED; inherent-condemnation framings ("whiteness as evil") are banned. Apply the same standard symmetrically — no group is inherently morally superior or inferior.
9. **Punchline-as-distractor** — no joke wrong answers. Every distractor is a real adjacent fact or a real plausible mistake.

## What this framework REQUIRES

1. **The cool fact is the answer.** This is the controlling rule. The stem gives MINIMUM scene-setting + the dramatic stakes / impact. The question asks for the wondrous specific. The answer IS the cool fact. The kid produces the memorable detail by picking it against plausible distractors — that's where the learning happens. See "Voice rules" below for the worked Brunelleschi example showing one historical figure supporting five different cool-fact-is-answer questions.

2. **Named person OR specific moment in every stem.** No abstract framing. The strategy doc's PERSON/MOMENT → STORY → WONDER pattern. A stem without a recognizable name or specific datable moment has failed.

3. **Story-led, scene-set, impact stated.** The stem opens with the scene + the named figure, includes the dramatic stakes ("with his army nearly destroyed and enlistments expiring"), and the impact ("the complete dawn victory saved the Revolution") — then narrows to the specific question. Reasonable storytelling beats compression; if avg stem length runs long, the subject timer can be tuned (currently 50s @ WIS 10).

4. **Real specifics — names, dates, places, quotes — verified.** History questions can be testably wrong. Fabrication poisons the bank. If a question names "Sobieski 1683 Vienna," the name + year + place must be true. Real quotes only.

5. **Steelman distractors.** Every wrong choice is a real adjacent fact or a plausible misremembering. Battle distractors are real adjacent battles. Figure-action distractors are things real adjacent figures actually did. Communist-atrocity distractors include establishment-soft-pedaled figures ("about half a million") so the kid picks the honest number.

6. **Scenery consistency across all fields** (SHARED_PRINCIPLES §6). If the stem sets a scene in canonical historical scenery (knight, monastery, Sobieski's hussars, Continental Army camp), the answer + every distractor + context maintain that scenery. No half-applied upgrades.

## Where philosopher / explorer / dates / capital names belong

**In the `context` field.** Always. Context is uncapped (SHARED_PRINCIPLES §9) — teaching depth allowed there. Stems never rely on knowing dates as the test; dates appear in stems only when they're an integral part of the named moment ("Christmas night 1776," "May 31 1832 dawn duel").

## The five tiers

### T1 — 5th grade (10–11)
- **Scope**: vivid wonder moments a kid can picture. Washington's "Victory or Death" password. Archimedes' "don't disturb my circles." Joan of Arc burned at 19. Sobieski's cavalry saving Vienna.
- **Voice**: "Did you know?" energy. Concrete scene + named figure + the memorable detail.
- **Drama-of-minds at T1 is welcome** — Archimedes' last words, Galileo "*Eppur si muove*," Newton struck by an apple in plague year 1666, Tycho's silver nose. These are kid-accessible wonder hooks.
- **Form**: total budget ≤ 500 chars (stem + 4 choices). Context uncapped.

### T2 — 6th grade (11–12)
- **Scope**: one scene + named figure + the action. Caesar crossing the Rubicon "*alea iacta est*." Luther's 95 theses at Wittenberg October 31 1517. Pascal's mystical night November 23 1654.
- **Voice**: scene-led story. Introduces "republic," "covenant," "monastery" with brief inline meaning.
- **Form**: ≤ 620 chars.

### T3 — 7th grade (12–13)
- **Scope**: scene + stakes + the decisive moment. Pickett's Charge on July 3 1863. Brunelleschi's egg demonstration to the panel of judges. Solzhenitsyn smuggling chapters out chapter by chapter.
- **Voice**: scientific-historical vocabulary with inline def. Specialist terms ("samizdat," "investiture," "satrap") defined on first use.
- **Form**: ≤ 770 chars.

### T4 — 8th grade (13–14)
- **Scope**: multi-sentence setup + named details + payoff. Holodomor mechanics (grain quotas tripled, borders sealed). Cardano-Tartaglia cubic-equation feud. Sobieski's hussars charging down Kahlenberg. Lavoisier guillotined "the Republic has no need of *savants*."
- **Voice**: scientist + historian register. Substantive details that make the moment land.
- **Form**: ≤ 900 chars.

### T5 — 9–10th grade (14–16)
- **Scope**: deep story with moral weight + consequence. The Gulag Archipelago's 18M-passed-through scope from Solzhenitsyn's 227 prisoner testimonies. Pol Pot's Year Zero evacuation of Phnom Penh. The Reagan-Thatcher-JP2 coalition that bankrupted the Soviets. Galois the night before his duel.
- **Voice**: analyst-grade with substantive depth. Real moral weight without preachiness.
- **Form**: ≤ 1100 chars.

## Six pillars

| # | Pillar | Weight | Heaviest tiers |
|---|---|---|---|
| 1 | **Western tradition unbroken** (Greeks → Industrial Revolution; institutions + ideas + art + music + architecture) | HEAVIEST | T1–T4 |
| 2 | **The American story** (Revolutionary War deep, Founders, Civil War deep, through ~2010) | HEAVY | All tiers |
| 3 | **Great battles + world military history** (story-led generals + decisive moments + consequences) | Medium | T2–T4 |
| 4 | **20th-century truth-telling — communist atrocities + Cold War** | HEAVY (by design) | T3–T5 |
| 5 | **Non-Western civilizations on their own terms + honest pre-modern brutality** | Substantive | T2–T5 |
| 6 | **Iconic moments + drama of the great minds** | HEAVY emphasis | ALL tiers |

See `HISTORY_TEMPLATES.md` §2 for the topic breakdown within each pillar.

## Substantive moral vision

### 1. The Western tradition is a real human achievement (moral_vision §3.4, §3.6)
Top billing. Greeks (Marathon, Thermopylae, Socratic method, Aristotle), Rome (Cincinnatus, Caesar, Roman law, Cicero), Christendom (Augustine, Aquinas, monasticism, Magna Carta, Gothic cathedrals), Reformation (Luther's 95 theses, Calvin's Geneva), Scientific Revolution (Newton, Galileo, Kepler — all believers per the historical record), Enlightenment (Locke, Smith, Burke), American Founding. The bank treats this as the inheritance it is.

**Western art + architecture + music threaded through every tier**: Parthenon (Phidias) and Doric/Ionic/Corinthian orders; Roman Pantheon's still-standing concrete dome; Hagia Sophia 532–537 (Justinian: "Solomon, I have outdone thee"); Chartres' rose windows; Brunelleschi's dome 1436 (4M bricks, herringbone, no scaffolding from below); Michelangelo's Sistine ceiling + David; Bernini's *Ecstasy of St. Teresa*; Vermeer; Rembrandt; Bach (*St. Matthew Passion* forgotten 1727 then revived by 20-year-old Mendelssohn 1829); Mozart's *Requiem* unfinished; Beethoven's deaf 9th-symphony premiere 1824; Wagner's *Ring*; Stravinsky's *Rite of Spring* riot 1913.

### 2. The American story honestly (moral_vision §3.6)
American Founders were flawed humans who built something extraordinary. Revolutionary War deep — Washington's character, Trenton + Princeton, Saratoga, Valley Forge + von Steuben, Yorktown's "world turned upside down." Constitutional Convention 1787. Civil War deep — Lincoln's moral clarity, Antietam, Vicksburg, Gettysburg + Pickett's Charge + Lincoln's 272-word address, Appomattox. Civil rights movement as moral victory — Douglass, Tubman, MLK Letter from Birmingham. American failures stated plainly (slavery, Trail of Tears, Jim Crow, Japanese-American internment, Tuskegee) — not theatricalized.

### 3. Communist atrocities honestly counted (moral_vision §3.1, §3.5)
This pillar is HEAVY by design. Specific death tolls. Specific perpetrators. No false equivalence.
- **Holodomor 1932–33**: 3.5–7M Ukrainians; collectivization tripled grain quotas; borders sealed; villagers caught eating dropped grain shot. **Walter Duranty's *NYT* cover-up explicitly named** — won the 1932 Pulitzer for "exaggerated or malignant propaganda" reporting while privately conceding to the British embassy "perhaps 10 million" had died. Pulitzer never revoked. Gareth Jones broke the story honestly and was murdered in Mongolia 1935.
- **Great Purge 1936–38**: Yezhovshchina; show trials; NKVD quotas; Tukhachevsky + Red Army decapitation; Katyn Forest 22,000 Polish officers murdered.
- **Great Leap Forward 1958–62**: 30–45M dead; backyard furnaces; four-pests campaign; grain quotas during famine.
- **Cultural Revolution 1966–76**: Red Guards; "four olds"; intellectuals to the countryside.
- **Khmer Rouge 1975–79**: 2M dead; Year Zero evacuation of Phnom Penh; Tuol Sleng (S-21); Killing Fields.
- **Gulag**: Solzhenitsyn's 227-prisoner *Gulag Archipelago* documenting 18M passed through; Magadan, Kolyma, Vorkuta, Solovki; Solzhenitsyn arrested 1945, *One Day in the Life of Ivan Denisovich* 1962, exiled 1974.
- **Other**: Castro's La Cabaña executions; Che killed Bolivia 1967; North Korean *kwan-li-so* camps; NK Arduous March famine; Ethiopia's Red Terror; Tibet invasion 1950; **Tiananmen Square June 4 1989 + Tank Man**.

### 4. Cold War as moral conflict (moral_vision §3.4)
The Reagan-Thatcher-John Paul II coalition celebrated. JP2's June 1979 Warsaw homily ("Be not afraid") as the spark of Solidarity. Reagan's 1983 "Evil Empire" speech. Reagan at Brandenburg June 12 1987 ("tear down this wall"). Berlin Wall falls November 9 1989. Solzhenitsyn, Sakharov, Wałęsa, Havel as heroes. The Soviet collapse December 25 1991.

### 5. Honest record of pre-modern brutality (moral_vision §3.7, §4)
Stated as fact, not theatricalized, paired with the named Western interventions that ended each practice. NO "savages" framing; NO sensationalism; NO condescension. The historical record is the argument.
- **Aztec mass human sacrifice**: Templo Mayor dedication 1487 — 20,000–80,000 in four days per Spanish and Aztec sources; obsidian-knife heart extraction; flayed-skin ritual of Xipe Totec. Ended by Spanish conquest + Las Casas + the Salamanca School's natural-rights theology (Vitoria, Suárez).
- **Plains + Iroquois ritual torture of captives**: days-long burnings; Cynthia Ann Parker's captivity (mother of Quanah); Comanche torture of Texas settlers.
- **Dahomey + Benin human sacrifice**: Benin's bronze altars piled with skulls at the 1897 British Punitive Expedition; Dahomey's annual customs killings.
- **Internal African slave trade**: Africans selling Africans to coastal kingdoms (Asante, Dahomey) for centuries before Atlantic trade; Tippu Tip's Zanzibar-end network operating into the 1890s. **Suppressed by Royal Navy West Africa Squadron 1808–1860s** and Livingstone's documentation.
- **Hindu suttee (widow-burning)**: real and widespread. **Lord William Bentinck banned it 1829** under William Carey's pressure.
- **Chinese foot-binding**: 1,000-year practice crippling tens of millions of women. **Ended by Western missionary + Chinese reformer collaboration**.
- **Thuggee strangulation cult, India**: possibly 2M murders over centuries. **Suppressed by William Sleeman + the British 1830s–40s**.
- **Fijian ritual cannibalism**: until Christianization mid-1800s ("Cannibal Isles" was a literal description).

### 6. Non-Western civilizations on their own terms (moral_vision §4)
Substantive coverage, NOT exotic foils. Han astronomers; Tang Chang'an as world's largest city; Song printing + gunpowder; Mongol postal system + Pax Mongolica; Ming Zheng He's treasure fleets; Mansa Musa's 1324 Hajj inflating Egypt's gold supply; Mali's University of Sankore at Timbuktu; Mughal Akbar's Sulh-i-kul religious tolerance; Taj Mahal; Tokugawa peace; Aztec calendar + Tenochtitlán on a lake; Inca road network 40,000 km + terraced agriculture; Polynesian wayfinding by stars + wave patterns; Great Zimbabwe's stone city; Lalibela's churches carved below ground.

**Islamic Golden Age covered but not over-weighted.** Mohammed's hijra 622, Abbasid Baghdad's House of Wisdom translation movement, al-Khwarizmi's algebra, Ibn Sina's *Canon*, Ibn al-Haytham's optics, Ibn Khaldun's *Muqaddimah*, Mansa Musa. **The decline thread is part of honest history**: al-Ghazali's *Incoherence of the Philosophers* (~1100) helped close the golden age's rationalist tradition; Mongol destruction of Baghdad 1258 ended the House of Wisdom; subsequent orthodoxy hardening prevented the recovery the West achieved through its own Renaissance and Scientific Revolution. The pattern (religious orthodoxy stifling inquiry) is stated as historical fact, not editorialized.

### 7. Drama of the great minds — across ALL tiers
Per the strategy doc: this is HEAVY emphasis. The drama is the part of the iconic-moments pillar most often neglected — the human at the breaking point, the night before the duel, the priority dispute that ate two lifetimes. Cover at every tier:
- **T1**: Archimedes' "don't disturb my circles" / Newton's apple in plague year 1666 / Tycho's silver nose
- **T2**: Galileo's "*Eppur si muove*" / Pascal sewing his mystical night into his coat / Lavoisier guillotined
- **T3**: Newton-Leibniz priority dispute / Hypatia torn apart 415 / Boltzmann's tombstone S = k log W
- **T4**: Cardano-Tartaglia cubic feud / Cantor in the asylum / Turing's apple
- **T5**: Galois the night before the duel / Ramanujan's letters to Hardy / Perelman refusing the Fields Medal + $1M / Lise Meitner overlooked at the 1944 Nobel

## Stance preserved (carry forward, do not relitigate)

- Western tradition top billing (§3.4, §3.6)
- American Founders as flawed but extraordinary (§3.6) — 1619-project reframe NOT adopted
- Communist atrocities heavy + honest with specific death tolls (§3.1)
- Cold War as moral conflict — Reagan + Thatcher + JP2 celebrated
- WW2 Allied victory celebrated; Holocaust documented unflinchingly; honest about Soviet role + post-war carve-up
- Christianity in history TREATED AS SUBSTANTIVE force — Augustine, Aquinas, Wilberforce, JP2 as the historical agents they were
- Sowell-Loury-McWhorter-Hughes-Steele as serious voices (§3.5)
- Honest record of pre-modern brutality (§3.7) paired with the Western interventions that ended each practice
- Western art + architecture + music celebrated as inheritance
- Drama of the great minds at every tier
- Recent history through ~2010; active politicians in current debates out
- Sports OUT of scope for history (handled in trivia per user direction 2026-05-24)

## How to use this framework

Future bank rebuilds: read this document FIRST. Then `HISTORY_TEMPLATES.md` for concrete patterns. Then the moral vision memories. If a pass produces dry-date trivia, sanitized-Founders hagiography, false-equivalence on communist atrocities, anti-anti-white framing, generic identification questions with cool facts stuffed in the stem, or any of the §1 forbidden anti-patterns — the pass is wrong on the framework, not just on the templates.
