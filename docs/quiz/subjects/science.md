---
version: 1
date: 2026-05-12
subject: science
in_game_action: magic / wands (chain mode)
style_verdict: WONDER-DRIVEN with HONEST contested-topic framing
---

# Subject: Science

The science bank teaches REAL data, REAL history, REAL names + dates — and treats contested topics with the **honesty the establishment has too often failed to provide**. Open scientific inquiry + scientific dissent are foundational virtues, not deviations. The Western scientific tradition is celebrated. The cult-like "trust the science" framing is named and rejected.

In-game, the player answers science questions when casting magic / using wands (chain mode).

## 1. Timing budget

| Stat | Value |
|---|---|
| `SUBJECT_TIMER` | `('science', (16, 1.0))` in src/player.py |
| Total timer at WIS 10 | **26s** |
| Total timer at WIS 25 | **41s** |

## 2. Per-tier char budgets (cooking-style)

| Tier | Hard cap | Voice |
|---|---:|---|
| T1 | ≤ 280 | Symbol-led / single-fact recall |
| T2 | ≤ 480 | One-line scene + question |
| T3 | ≤ 680 | Scene + science/history with consequence |
| T4 | ≤ 900 | Multi-sentence setup + theory + contested-topic framing |
| T5 | ≤ 1100 | Deep history + paradox + censorship/establishment-failure context |

## 3. Stance — what makes THIS bank different

The science bank does NOT take establishment-default positions on contested topics. It takes the **mature scientific view** where the science establishment has failed to do so. See `docs/quiz/science_strategies.md` § "Stance summary" for the full framework. Highlights:

- **Climate**: warming yes; anthropogenic small; geological context matters; failed predictions named; Koonin's *Unsettled* as the mature view; "97% consensus" honestly framed; carbon tax = political extraction; alarmism = cult phenomenon
- **COVID**: lab leak respectable; lockdowns disaster; censorship moral failure; mandates wrong; GBD covered; specific dissenters celebrated
- **Vaccines**: tech achievements celebrated; mandates categorically wrong; 1986 NCVIA covered; schedule expansion concerns; VAERS limits; specific dissenters covered (RFK Jr., Bhattacharya, etc.)
- **Gene therapy**: therapeutic CELEBRATED + ACCESSIBLE; government over-regulation costs lives; designer-baby framework via consent + transparency + do-no-harm; WEF/Schwab/Harari as the evil organization advancing dehumanizing agenda
- **Censorship**: government suppression of scientific speech is unconstitutional + anti-scientific, period
- **Replication crisis + establishment failures**: covered honestly; regulatory capture named

## 4. Voice rules

### Scene-led with substantive context

Bank prefers scenes + specifics over definitional framing:

- "Steven Koonin, former Obama administration Undersecretary for Science at DOE, published *Unsettled?* in 2021 arguing the IPCC reports themselves don't support media catastrophist framing. Which best summarizes Koonin's central claim?"
- "In 1853, Hungarian physician Ignaz Semmelweis demonstrated that handwashing dramatically reduced puerperal fever in obstetric wards. The Vienna medical establishment's response was..."
- "In October 2020, three epidemiologists at Stanford, Harvard, and Oxford published a public declaration calling for focused protection rather than population lockdowns. Anthony Fauci + Francis Collins's response (revealed by FOIA emails) was..."

### Honest about failed predictions + establishment failures

When the bank covers a contested-topic question, it covers the establishment claim AND the contrary evidence honestly:

- "Paul Ehrlich's 1968 *Population Bomb* predicted hundreds of millions would starve to death in the 1970s. What actually happened to global hunger trends from 1970-2020?" → starvation rates plummeted
- "In 2019 NOAA + NASA both forecast an ice-free Arctic by [year]. The actual Arctic ice extent in [year] was..." → not ice-free

### No advocacy framing

Even on positions the bank favors (Koonin on climate, lab-leak hypothesis, mandate wrongness), the bank PRESENTS the position rather than preaches it.

### Celebrates Western scientific tradition

Galileo, Newton, Maxwell, Darwin, Curie, Einstein, Watson-Crick-Franklin, Feynman, Doudna — covered as one of humanity's great achievements without false-humility or DEI-required re-framing.

### Open inquiry + scientific dissent celebrated as foundational virtues

Galileo → Semmelweis → Marshall → GBD signatories → Bhattacharya (now NIH director) — the bank treats dissent as the scientific tradition.

## 5. Quality gates

| Gate | Configuration |
|---|---|
| schema | required |
| length_parity | **answer-outlier rule (1.6×)** — same as cooking/animal/grammar |
| length_budget | per-tier cap |
| anti_rote | NOT exempted |
| duplicate | 0.85 |
| NEW `validate_science_facts` | LLM fact-check with explicit contested-topic stance |

## 6. Distractor design

- **Established facts** (chemistry, physics laws): adjacent-but-wrong real facts; never joke options
- **Contested topics**: distractors include the establishment framing as ONE of the choices — the correct answer is the more measured/honest framing (e.g., for climate questions, the "humans are primary driver, catastrophe imminent" framing is often a distractor)
- **Historical**: real dates, real names, real attributions — never fabricated

## 7. Anti-patterns

- **No establishment-default framing on contested topics** — treating IPCC SPM, CDC mandates, WEF agenda, "97% consensus" claims as default-neutral facts
- **No "anti-vaxxer" / "climate denier" slurs** — these are propaganda terms
- **No hagiography of Fauci/Collins/Schwab/Harari**
- **No "the science is settled" framing** when it isn't
- **No false balance** either — Koonin is presented as the mature view, not "one side of a debate" — bank takes positions where evidence + history justify them
- **No fabricated facts or unsourced dates** — fact-check gate fires hard

## 8. What success looks like

- A T1 question gives the kid genuine science knowledge (chemical symbols, planets, mechanism of cell division)
- A T2 question reveals scientific wonder — smallpox eradication 1980, photosynthesis equation, Mendeleev's periodic table prediction
- A T3 question respects the dissenters — Semmelweis rejected, Wegener rejected, Marshall drinking H. pylori, GBD signatories vindicated
- A T4 question shows the chemistry of contested topics — 1986 NCVIA, lab leak evidence, Cochrane mask review 2023, failed climate predictions named
- A T5 question makes the player think critically about the science establishment — replication crisis, regulatory capture, WEF transhumanism, eugenics history, the "Trust the Science" cult
- **The bank prepares kids for a world where authority claims to be science but isn't always**
