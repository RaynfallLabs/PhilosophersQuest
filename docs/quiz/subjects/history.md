---
version: 1
date: 2026-05-13
subject: history
in_game_action: equipping accessories (threshold mode)
style_verdict: STORY-DRIVEN — history as the story of humanity, moments + people as the portals
---

# Subject: History

History is the **story of humanity**. The bank teaches kids that real people faced real choices under real pressure, and that what they did shapes the world we live in. Kids should leave hearing names — **Thermopylae, Magna Carta, Trenton, Gettysburg, Solzhenitsyn, Sobieski, Wilberforce, Reagan, Sun Tzu, Akbar, Saladin** — and feel those names *mean* something.

In-game, the player answers history questions when equipping accessories (threshold mode).

## 1. Timing budget

| Stat | Value |
|---|---|
| `SUBJECT_TIMER` | `('history', (32, 1.6))` in src/player.py |
| Total timer at WIS 10 | **48s** |
| Total timer at WIS 25 | **72s** |

Generous — scaffolded story content needs room to read. Many T4/T5 questions are paragraph-length scene-setting before the question lands.

## 2. Per-tier char budgets (answer-outlier 1.6× rule applies)

| Tier | Hard cap | Voice |
|---|---:|---|
| T1 | ≤ 280 | Crisp moment + person/place + the wonder |
| T2 | ≤ 480 | One scene + named figure + the action |
| T3 | ≤ 680 | Scene + stakes + the decisive moment |
| T4 | ≤ 900 | Setup + tension + named details + payoff |
| T5 | ≤ 1100 | Deep story with pressure + moral weight + the consequence |

## 3. The PERSON/MOMENT → STORY → WONDER pattern (core voice)

Every question follows this shape:

> **[Named person OR specific moment, lightly framed]** + **[the pressure / stakes / setting]** + **[what they did or what happened]** + **[question that pays off the story]**

Examples:

- *"On Christmas night 1776, with his army nearly destroyed and enlistments expiring in a week, George Washington gave his troops the password 'Victory or Death' and led 2,400 men across the ice-choked Delaware River in a snowstorm. At dawn they attacked the Hessian garrison at Trenton. What was the result?"* → **A complete American victory — 900 Hessians captured for the loss of two American dead frozen on the march; the campaign saved the Revolution.**

- *"In 1973, exiled Soviet writer Aleksandr Solzhenitsyn smuggled out the manuscript of a three-volume work documenting the Gulag system based on 227 fellow prisoners' testimonies. He knew that if the KGB found the work, he and his family would face severe consequences. What did the book reveal?"* → **The systematic structure of Soviet political imprisonment — millions sent to camps for arbitrary or fabricated 'crimes', under conditions that killed many.**

- *"In 1784, Louis XVI appointed a Royal Commission to investigate Franz Mesmer's claim that he could heal disease by manipulating an invisible 'animal magnetism' fluid. The commission included Benjamin Franklin and Antoine Lavoisier. Their experiments — blindfolding patients, having them touch un-magnetized trees they were told were magnetized — produced a finding that became a landmark of scientific method. What did they conclude?"* → **Mesmer's effects were caused by patients' imagination and expectation, not any physical fluid — one of the first formal placebo-controlled studies.**

The named person or specific moment is **always present** and **always concrete**. The story payoff is **always a real fact**, not invented atmosphere.

## 4. Stance summary

History is the most ideological-stakes wonder subject. The bank takes substantive positions where it matters and refuses false equivalence:

| Topic | Stance |
|---|---|
| The Western tradition | TOP BILLING — Greeks → Romans → Christendom → Reformation → Scientific Revolution → Enlightenment → American Founding produced the world's most successful experiment in human liberty |
| American Founders | HONEST — flawed humans (slavery, contradictions) who built something extraordinary; 1619-project's "America founded on slavery" thesis rejected as ideological revisionism, not historical fact |
| American Revolutionary War | DEEP coverage — Washington's character + decisions, Adams' diplomacy, Franklin's genius, Hamilton's political fight, the real stakes of Trenton, Saratoga, Yorktown |
| American Civil War | DEEP coverage — Lincoln's moral clarity, the actual cause (slavery, per the Confederate states' own declarations), Union/Confederate generals' choices, Gettysburg, Appomattox, Reconstruction successes and failures |
| Slavery + Jim Crow + lynching | HONEST AS EVIL — Wilberforce, Douglass, MLK celebrated; the abolitionist tradition as a Christian achievement; civil rights movement as moral victory |
| Communist atrocities | HEAVY + HONEST — Lenin's terror, Holodomor 3.5-7M dead, Great Purge, Gulag, Mao's 30-45M dead, Cultural Revolution, Khmer Rouge killing fields, North Korea, Cuba; specific death tolls + specific perpetrators named |
| Cold War | MORAL CONFLICT — Reagan-Thatcher-John Paul II coalition celebrated; Solidarity, Sakharov, Solzhenitsyn as heroes; Berlin Wall as evil to be broken |
| WW2 | Allied victory celebrated; Holocaust documented unflinchingly; honest about Soviet role + post-war carve-up; Eastern Front scale (~27M Soviet dead, ~80% of German losses) acknowledged |
| Western imperialism | HONEST — both costs (extraction, dislocations) AND benefits (end of slave trade, end of suttee, end of foot-binding, railways, legal systems); refuses the one-sided narrative |
| Non-Western civilizations | CELEBRATED as full civilizations — Han astronomers, Tang poets, Akbar's religious tolerance, Suleiman's law, Tokugawa peace, Polynesian navigation, Mansa Musa, Ibn Battuta |
| Christianity in history | TREATED AS SUBSTANTIVE — not waved away; Augustine, Aquinas, Wilberforce, John Paul II covered as the historical forces they were |
| Identity-politics revisionism | NOT ADOPTED — Sowell, Loury, McWhorter, Hughes covered as serious voices; American Founding not framed as primarily about race/oppression |
| Recent history (post-1991) | Settled events through ~2010 covered; active politicians covered ONLY for already-settled historical actions (Reagan, Thatcher, Clinton, GW Bush ✓; current-roles Trump/Obama/Biden in current debates avoided) |

## 5. Voice rules

### Lead with the named person OR the specific moment

A question without a recognizable name or specific moment in the prompt has failed. The point is that kids leave hearing "Sobieski," "Solzhenitsyn," "Wilberforce," "Stonewall Jackson" and feeling those names matter.

### Show moral courage and moral weight

The bank's heroes (Washington crossing the Delaware, Lincoln at Gettysburg, Wilberforce against the slave trade, Solzhenitsyn against the Gulag, MLK at the Lincoln Memorial, Reagan at the Brandenburg Gate) made real choices under real pressure. Don't sanitize that. Don't preach it either — show the choice and let the kid feel its weight.

### Scene-led, never dry-date-led

- Bad: *"In what year did the Battle of Gettysburg occur?"*  (also: banned by anti-rote)
- Good: *"On July 3, 1863, after two days of inconclusive fighting near a Pennsylvania town, Robert E. Lee ordered 12,500 Confederate soldiers across an open mile of ground against the center of the Union line on Cemetery Ridge. They were torn apart by artillery and rifle fire. What is the assault called?"* → **Pickett's Charge**

### Real names, real dates, real specifics — verified

If a question names "Wilberforce" or "Sobieski" or "1683," the name and date must be true. Fabrication poisons the bank. Especially crucial because history questions often have answers that are testable.

### Active voice, story rhythm

- "Washington led 2,400 men across the ice-choked Delaware..."
- "Solzhenitsyn smuggled the manuscript out..."
- "Sobieski charged down from Kahlenberg..."

Not: "It was on Christmas night that Washington was leading men across..."

### Cross-link history → ideas, technology, culture

A question can be about the *Battle of Lepanto* AND about Cervantes losing the use of his left hand there AND about how the victory ended Ottoman naval dominance in the Mediterranean AND about the rosary devotion the victors prayed. History is a web; the bank should show the threads.

### Iconic moments span ALL of history

T4/T5 iconic-moments questions cover:
- **Scientific**: Franklin/Lavoisier debunking Mesmer 1784, Galileo's recantation, Pasteur's anthrax demo at Pouilly-le-Fort 1881, Marie Curie's notebooks (still radioactive), Watson-Crick at the Eagle pub, Apollo 11
- **Technological**: Gutenberg's press, Watt's separate condenser, Bell's first phone call, Edison's lightbulb, Wright Brothers Kitty Hawk, ENIAC, Apple I
- **Sports**: Owens Berlin 1936, Bannister 4-minute mile, Ali-Foreman Rumble in the Jungle 1974, Miracle on Ice 1980, Hulk Hogan body-slams Andre at WM3 1987, Tiger Woods 1997 Masters, MJ's last shot 1998
- **Music + culture**: Beatles on Ed Sullivan, Beethoven's 9th (deaf), Hendrix at Woodstock, Picasso's Guernica unveiling, Mozart's prodigy years, Bach's St. Matthew Passion
- **Religious**: Luther nailing 95 theses to Wittenberg door, JP2 in Poland 1979, Wesley's Aldersgate experience

### Drama of the great minds — science + math personalities (HEAVY emphasis)

The historical drama around great scientific and mathematical figures is the part of the iconic-moments pillar that often gets neglected. Cover it richly. Real rivalries, real tragedies, real triumphs. Examples:

- **Galois's duel**: Évariste Galois at 20, arrested for political activity, killed in a duel at dawn May 31, 1832 over a love affair — spent the previous night writing the foundations of group theory in margins with "I have not time" scrawled across the bottom
- **Newton vs Leibniz**: the calculus priority dispute that consumed both lifetimes; Newton chaired the Royal Society "investigation" of his own claim against Leibniz; Leibniz died alone in 1716, only his secretary at the funeral
- **Cardano vs Tartaglia**: the 1539-1545 bitter feud over the solution to the cubic equation, Tartaglia teaching Cardano under sworn secrecy, Cardano publishing anyway in *Ars Magna* 1545
- **Tycho Brahe's silver nose**: lost in a duel over a math problem 1566, replaced with silver, kept drinking on his island Uraniborg until killed by a bladder rupture from etiquette at a banquet
- **Boltzmann's tombstone**: S = k log W carved on the grave of the man whose statistical mechanics was rejected by his contemporaries; suicide in Duino, Italy, 1906
- **Cantor in the asylum**: founder of set theory, persecuted by Kronecker, repeated mental breakdowns, died of a heart attack in a sanatorium 1918
- **Turing's persecution**: broke Enigma + saved untold lives in WW2, chemically castrated 1952 for being homosexual, dead of cyanide poisoning June 7 1954 at age 41 — a half-eaten apple beside him
- **Ramanujan's letters**: a self-taught Indian clerk wrote to G.H. Hardy at Cambridge 1913 with theorems Hardy could not even understand; collaborated 1914-1919; TB took him at 32 in 1920
- **Hypatia's death**: the great mathematician of Alexandria torn apart by a Christian mob in 415 AD — the symbolic close of antique scholarship
- **Lavoisier guillotined**: father of modern chemistry, executed May 8 1794, "the Republic has no need of savants"
- **Perelman's refusals**: solved the Poincaré conjecture 2003, refused the Fields Medal 2006, refused the $1M millennium prize 2010, withdrew from mathematics entirely
- **Pascal's mystical night**: November 23, 1654, two hours of fire, sewed the parchment record into his coat — found there after his death at 39
- **Riemann at 39**: the hypothesis proposed 1859 still unsolved, the man dead of TB by 1866 in the Italian Alps
- **Nash's recovery**: paranoid schizophrenia in his 30s; recovered later; Nobel 1994; killed in a New Jersey taxi crash 2015 with his wife

These dramas humanize science and math history. Cover them with the same wonder voice — real people at real breaking points.

## 6. Quality gates

| Gate | Configuration |
|---|---|
| schema | required (tier, question, answer, choices×4, context) |
| length_parity | answer-outlier rule (1.6× multiplier) |
| length_budget | per-tier cap (280 / 480 / 680 / 900 / 1100) |
| anti_rote | NOT exempted — bans `^In what year did`, `^Who (wrote\|invented\|founded\|...)`, `^What is the capital of`, `^Which (city\|country\|...)`, `^What (is\|does) ['"]`, `^Define` |
| duplicate | 0.85 similarity threshold |

## 7. Distractor design

- **Battles**: distractors are real adjacent battles or real-but-wrong outcomes (e.g., for "Battle of Saratoga outcome," distractors include "British forces broke through to relieve Burgoyne," "Burgoyne agreed to terms allowing his army to return to England," etc. — all plausibly something that COULD have happened)
- **Figures' actions**: distractors are things real adjacent figures actually did, or plausible-but-wrong things this figure might have done
- **Communist atrocities**: distractors include the establishment-soft-pedaled version ("a regrettable but limited famine," "deaths in the low thousands") — the correct answer is the honest figure
- **Iconic moments**: distractors are real adjacent moments (e.g., for Hogan's WM3 slam, distractors are real Andre matches or real Wrestlemania III matches)

## 8. Anti-patterns

- **Dry date / who-invented framing** — banned by anti-rote regex
- **"Both sides" false-equivalence on communist atrocities** — fail; show the death toll honestly
- **1619-project framing as if neutral fact** — fail; the bank doesn't adopt it as the American founding story
- **Sanitizing slavery / Jim Crow / Holocaust / Gulag** — fail; show the evil
- **Sanitizing Founders or hero-figures into hagiography** — also fail; show Washington's slavery contradictions, Jefferson's hypocrisies, Hamilton's affair
- **Current-politics quagmires (post-2010 contested events)** — out of scope
- **Fabricated quotes or dates** — fail
- **Pronoun antecedents over 8 words apart** (per generate.md phrasing rules)
- **Term-before-definition** — if introducing "yeomanry" or "polis" or "satrap," scene-set first

## 9. What success looks like

- A T1 makes a kid hear "Trenton" and learn Washington crossed the Delaware on Christmas
- A T2 makes them hear "Sobieski" and learn his cavalry charge saved Vienna in 1683
- A T3 makes them hear "Solzhenitsyn" and understand what Gulag Archipelago was
- A T4 makes them hear "Franklin debunked Mesmer" and learn how blinded controls work
- A T5 makes them hear "Pasteur at Pouilly-le-Fort" and understand the moment vaccination became science
- **Kids leave knowing that real people made real choices under real pressure, that the Western tradition produced the freest societies in human history, that communism killed 100 million people in the 20th century, and that the world is full of moments worth knowing.**
