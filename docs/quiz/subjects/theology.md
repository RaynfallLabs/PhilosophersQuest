---
version: 1
date: 2026-05-13
subject: theology
in_game_action: praying (threshold mode)
style_verdict: CIVILIZATIONAL + MYTHOLOGICAL — sacred traditions as story, history, and shaping force
---

# Subject: Theology + Mythology

The bank covers **theology and mythology together** because the line between them is artificial. Christianity, Norse religion, Greek religion, and the world's other major faiths and mythological traditions are all serious attempts by humans to make sense of the cosmos, the divine, and the moral order. The bank teaches kids about these traditions as the **rich, story-saturated, civilization-shaping forces they are** — without privileging any one as metaphysically true.

In-game, the player answers theology questions when praying (threshold mode).

## 1. Timing budget

| Stat | Value |
|---|---|
| `SUBJECT_TIMER` | `('theology', (48, 1.7))` in src/player.py |
| Total timer at WIS 10 | **65s** |
| Total timer at WIS 25 | **91s** |

Most generous timer in the game — by design. Theology + mythology questions carry dense scaffolded narrative and need room to read.

## 2. Per-tier char budgets (answer-outlier 1.6× rule applies)

| Tier | Hard cap | Voice |
|---|---:|---|
| T1 | ≤ 280 | Crisp moment + named figure or god + the wonder |
| T2 | ≤ 480 | One scene + named figure + the action / doctrine |
| T3 | ≤ 680 | Scene + stakes + theological / mythological meaning |
| T4 | ≤ 900 | Setup + narrative + named details + payoff |
| T5 | ≤ 1100 | Deep story / doctrine with civilizational weight or mythological depth |

## 3. Stance — what makes THIS bank different

Christianity gets **top billing** (3/8 of the bank) because of its **civilizational impact** — the morality, philosophy, institutions, and intellectual frameworks that built the modern world. NOT because it is privileged as metaphysically true.

Greek mythology + religion (2/8) and Norse mythology + religion (2/8) get **strong coverage** — these are the two richest mythological traditions in the Western imagination, and kids should hear "Odin" and "Athena" and feel those names mean something.

Other major world religions + world mythologies (1/8) — Judaism (post-biblical), Islam, Buddhism, Hinduism, Egyptian, Mesopotamian, Aztec, Celtic, Japanese Shinto, African — get respectful but lighter coverage.

The bank treats every tradition with the **same intellectual honesty**: celebrate what's celebratable, name what's evil, never adopt one tradition's perspective as if it were neutral fact.

### Stance table

| Topic | Stance |
|---|---|
| Christianity's civilizational impact | TOP BILLING — built Western moral framework, universities, hospitals, abolitionism, modern human rights, scientific method (per the Western Christian tradition), individual conscience |
| Resurrection + central Christian doctrines | Covered as what Christianity teaches, not as historical fact-claim privileged by the bank |
| Catholic Church earthly power | HONEST — Inquisition (Spanish + Roman), indulgence sales, Borgia papacy, Galileo trial, papal politics, abuses of confession + sacramental power |
| Catholic monastic + intellectual tradition | CELEBRATED — Benedictine learning, cathedrals, illuminated manuscripts, Aquinas, Hildegard, John of the Cross, Teresa of Avila |
| Reformation | CENTRAL inflection point — Luther/Calvin/Wesley/Tyndale/Knox; rise of vernacular Bible, religious freedom, individual conscience; honest about wars of religion (~8M dead in Thirty Years War alone) and witch trials in both Protestant + Catholic lands |
| Crusades | HONEST — both the original defensive response to Islamic conquest AND the atrocities (Jewish massacres of 1096, sack of Constantinople 1204, fourth Crusade abuses) |
| Witch trials + sectarian abuses | HONEST AS EVIL — Salem 1692, German + Scottish witch panics, Anabaptist persecution, Catholic-Protestant massacres |
| American religious history | COVERED — Puritan founding, First + Second Great Awakenings, abolitionist Christianity, civil rights Christianity, modern evangelicalism |
| Norse mythology | CELEBRATED as rich storytelling tradition — Eddas, sagas, runes, religious practices honestly (blot rituals, ritual slavery, raiding ethics) |
| Greek mythology | CELEBRATED as rich storytelling tradition — Homer, Hesiod, mysteries (Eleusinian, Orphic, Dionysian), oracles; honest about pederasty in religious contexts + slavery integral to polis worship |
| Other ancient mythologies | CELEBRATED on their own terms — Egyptian death cult sophistication, Mesopotamian Gilgamesh themes, Aztec cosmology; honest about Aztec mass human sacrifice (~20,000/year at peak), Carthaginian child sacrifice |
| Islam | HONEST DUAL FRAME — Golden Age (House of Wisdom, al-Khwarizmi, Avicenna, Averroes, Ibn al-Haytham, Mansa Musa) genuinely CELEBRATED; honest about how al-Ghazali's anti-rationalism + Asharite dominance + religious authoritarianism closed off the flowering; modern Islamist regimes (Iran 1979, Taliban, ISIS, Boko Haram) named as destructive |
| Judaism | RESPECTED — Talmudic learning, prophetic tradition, Holocaust memory, modern Israel; covered as the parent tradition of Christianity |
| Buddhism | RESPECTED — Four Noble Truths, schools, key figures; honest about sectarian violence in Sri Lanka + Myanmar + Tibet's pre-1950 theocratic society |
| Hinduism | RESPECTED — Vedas, Upanishads, Bhagavad Gita, deities; honest about caste system, sati (until British abolition 1829), modern reform tradition (Vivekananda, Gandhi) |
| Confucianism + Taoism | RESPECTED — covered as practical/philosophical traditions |
| New religious movements / cults | HONEST — Jonestown, Heaven's Gate, Branch Davidians, Aum Shinrikyo as cult abuses |

## 4. Voice rules

### Same wonder voice as geography + history

PERSON / MOMENT / DOCTRINE / DEITY → STORY → WONDER. Lead with a named figure or specific moment. Show the stakes. Pay off the question.

### Civilizational framing, not truth-claim framing

For Christianity: cover Augustine's conversion in the Milanese garden as a *foundational moment in Western interiority and autobiographical literature*. Not "the moment Christian truth dawned on him." Cover the Resurrection as "what Christianity teaches" (the central event the tradition rests on), not "what really happened." Cover doctrines as *the doctrine the tradition holds*.

### Abuses covered with the same care as triumphs

The Inquisition is not waved away. The Borgia papacy is named. The Salem witch trials are covered for what they were. The Crusades are covered honestly — including both the original defensive response to Islamic conquest AND the atrocities. The Reformation is celebrated as civilizational inflection AND honest about the wars of religion that followed.

### Mythological richness

Norse + Greek mythology covered as the **rich storytelling traditions** they are. Odin hanging 9 nights on Yggdrasil for the runes — that's a story worth telling at full wonder. Persephone's pomegranate seeds. Loki tied beneath the venom-dripping snake. Tyr losing his hand to bind Fenrir. Heracles' 12 labors. Pandora's jar (not box). Cover with the same energy as a great geography wonder.

### Honest about ancient practices

Pederasty in Greek religion (Zeus + Ganymede, the eromenos tradition). Slavery integral to Greek + Roman + Norse societies. Norse human sacrifice at Uppsala. Aztec mass sacrifice on the Templo Mayor. Carthaginian tophet child sacrifice. Roman gladiatorial games as religious ritual. Cover honestly — what happened, why it happened, what we make of it now.

### Real names, real dates, real specifics

Augustine 386 AD garden conversion (*Confessions* Book 8). Luther's 95 Theses October 31, 1517. Council of Nicaea 325 AD. Augustine of Hippo's death 430 AD. The Edict of Milan 313 AD. The Synod of Whitby 664 AD. Aquinas declining to finish the *Summa* after his Dec 6 1273 mystical experience. Knox confronting Mary Queen of Scots. Bonhoeffer hanged at Flossenbürg April 9, 1945.

### Active voice, story rhythm

- "Augustine heard a child's voice say *tolle lege*..."
- "Luther nailed the 95 Theses to the door of All Saints' Church..."
- "Odin hung from Yggdrasil for nine nights..."
- "Heracles cleansed the Augean stables in a single day..."

## 5. Quality gates

| Gate | Configuration |
|---|---|
| schema | required |
| length_parity | answer-outlier rule (1.6× multiplier) |
| length_budget | per-tier cap (280 / 480 / 680 / 900 / 1100) |
| anti_rote | NOT exempted — bans `^What (is\|does) ['"]`, `^What is the capital of`, `^Which (city\|country\|...)`, `^In what year did`, `^Who (wrote\|invented\|founded\|...)`, `^How many ... (are there\|exist)`, `^Define` |
| duplicate | 0.85 similarity threshold |

## 6. Distractor design

- **Doctrines + theology**: distractors are other real doctrines from adjacent traditions (e.g., for "what is the Trinity," distractors might be Modalism, Arianism, Unitarianism — all real positions that real people have held)
- **Bible narratives**: distractors are real adjacent biblical events
- **Greek/Norse myth**: distractors are other real myths or real adjacent gods (e.g., for "who is the trickster god," distractors include other real tricksters: Hermes, Loki, Coyote, Anansi — but the right answer is contextual)
- **Church history**: distractors are real adjacent events or real figures
- **Islam Golden Age**: distractors are real adjacent scholars (al-Kindi, al-Razi, al-Battani, al-Haytham all real and adjacent)

## 7. Anti-patterns

- **Dry "who founded X" / "in what year" framing** — banned by anti-rote regex
- **Sanitizing Catholic Church abuses** — fail; Inquisition + indulgences + Borgia papacy covered honestly
- **Sanitizing Norse slavery + raiding** — fail; cover honestly
- **Sanitizing Aztec mass human sacrifice** — fail; ~20,000/year at peak
- **Privileging Christian truth-claims as fact** — fail; covered as doctrine + civilizational force
- **Treating Islam as monolithic** — fail; Golden Age genuinely celebrated, modern Islamism honestly named
- **Treating all religions as "equally valid social constructs"** — fail; lacks substance; bank takes seriously each tradition's claims about itself
- **Hostile secular sneering at any tradition** — fail; bank covers all traditions seriously
- **Modern political-religious figures in current controversies** — out of scope; recent events through ~2010 only
- **Pronoun antecedents over 8 words apart**
- **Term-before-definition** — if introducing "transubstantiation" or "blot" or "ahimsa", scene-set first

## 8. What success looks like

- A T1 makes a kid hear "Yggdrasil" and learn it's the cosmic ash tree holding the Nine Worlds
- A T2 makes them hear "Augustine" and learn about the garden conversion that founded Western autobiography
- A T3 makes them hear "Nicaea 325" and learn Constantine convened the council that produced the Nicene Creed
- A T4 makes them hear "the Inquisition" and understand what it actually was — when, where, who, and how it ended
- A T5 makes them hear "al-Ghazali" and understand the substantive intellectual move that closed the Islamic Golden Age
- **Kids leave the bank understanding that humans across cultures have built rich, story-saturated traditions to make sense of the divine and the moral order; that Christianity built the modern Western world (with both its glories AND its abuses); that mythology is not children's stories but the deep imagination of civilizations; and that every great religious tradition contains both heroic moral achievement and serious moral failure.**
