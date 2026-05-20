# Theology Quiz Bank Quality Review — 2026-05-19

## Summary

Cleaned 239 non-Christian / pantheon items out of the active bank per the
Christian-Crusader framework (no Zeus / Odin / Ra / Muhammad / Buddha / Hindu
deities in active theology), then generated 429 new scene-led Christian
questions to bring every tier T1-T4 above the 200 floor.

| Tier | Pre-audit | Post-cleanup | Net new generated | Final active |
| ---- | --------: | -----------: | ----------------: | -----------: |
| T1   |       101 |           82 |              +138 |          220 |
| T2   |       102 |           82 |             +132* |          214 |
| T3   |       155 |          116 |               +96 |          212 |
| T4   |       194 |          146 |               +63 |          209 |
| T5   |       363 |          250 |                +0 |          250 |
| **Total** | **915** | **676** | **+429** | **1105** |

\*T2 generated as 97 (main batch) + 35 (supplement) to clear the floor.

`py -m tools.quizgen validate --subject theology` -> 1105 KEEP, 0 REPAIR, 0 DISCARD.
`pytest -q` -> 598 passed.

## 1. Pantheon / other-religion cleanup (235 + 4 items)

The bank had absorbed substantial non-Christian religious content from earlier
generation rounds — Greek / Norse / Egyptian myth, Islam, Hinduism / Buddhism,
Sikhism, Babylonian religion, Polynesian myth, modern cults (Aum Shinrikyo,
Jonestown). Per the Christian-Crusader stance in MEMORY.md, this content
belongs in `dropped/` and should not appear as active theology questions.

I built a precise regex detector that flagged 235 items on the first pass
plus 4 stragglers on a second pass. The detector was deliberately careful to
preserve legitimate Christian items that *mention* other religions in passing
(Paul preaching at the Areopagus, Hagar the Egyptian, Juan Diego converting
the Aztec lands, the Crusades, Augustine's Manichaean backstory, Rosa Parks
the Methodist civil-rights activist).

False-positive allowlist applied:

- `#52, #568, #711, #767`  — Paul's Areopagus sermon (Acts 17)
- `#121`  — Hagar the Egyptian handmaid (Genesis 16/21)
- `#264`  — Juan Diego and Our Lady of Guadalupe (1531)
- `#476, #700, #775`  — First and Fourth Crusades
- `#578`  — Aquinas's Five Ways (context mentions Avicenna)
- `#619`  — Rosa Parks
- `#740`  — Passover and Exodus (Pharaoh as historical setting)
- `#773`  — Augustine's conversion from Manichaeism

Drop counts by tier:

| Tier | Pantheon drops |
| ---- | -------------: |
| T1   |             19 |
| T2   |             20 |
| T3   |             41 |
| T4   |             48 |
| T5   |            111 |
| **Total** |    **239** |

Total dropped file is now 1933 entries (up from 1694).

## 2. Generated content (429 new Christian items)

All new content is scene-led following the established T1-T4 style:
"A reluctant prophet fled God's command to preach to Nineveh and was swallowed
by a great fish for three days. Who was he?"

Tier-budget targets per `tools/quizgen/deterministic/length_budget.py`:

- T1: 280 chars target (294 hard cap)
- T2: 480 chars (504)
- T3: 680 chars (714)
- T4: 900 chars (945)

Every generated item double-asserts budget AND length-parity on creation
(answer not >1.6× longest distractor, not <shortest/1.6).

### T1 (+138 items)

Famous-stories layer: Genesis creation, Eden, Noah, Abraham,
Moses and the plagues, Joshua and Jericho, Samson, David and Goliath,
Solomon, Elijah on Carmel, Daniel in the lions' den, Jonah and the fish,
Christmas (Magi, Bethlehem, Mary), Jesus's miracles (feeding 5000, walking on
water, blind man healed, Lazarus, calming the storm), parables (Good
Samaritan, Prodigal Son, Sower), Passion (Last Supper, Gethsemane, Pilate,
Calvary, the empty tomb), Pentecost, Saul's conversion, Patrick of Ireland,
Francis of Assisi, the 95 Theses, John Wesley, C. S. Lewis.

### T2 (+132 items)

Less-famous OT (Hagar, Abraham bargaining for Sodom, Jacob wrestling at the
Jabbok, the bronze serpent, the Shema, the Akedah-binding context); NT
expanded (Mary's Magnificat, Simeon's Nunc Dimittis, the Holy Innocents,
Cana, Mark 5 bleeding woman, the prodigal son detail, John 13 foot-washing,
the Emmaus road); early church (Polycarp, Tertullian, Augustine's Confessions);
medieval (Anselm, Aquinas, Francis, Catherine of Siena); Reformation (Luther's
Wartburg, Calvin's Geneva, Knox's galley years, Cranmer's death); modern
(Wilberforce/Newton, Damien of Molokai, C. S. Lewis's conversion, Bonhoeffer's
prison, Mother Teresa, MLK, Billy Graham); core doctrine and liturgy (Apostles'
Creed, Trinity, sacraments, Lent, Eucharist meaning).

### T3 (+96 items)

Deeper OT (Melchizedek, Hagar's well, Abraham at Sodom's gate, the Akedah,
Jacob and Esau, Joseph's silver cup, Korah's rebellion, Achan, Deborah and
Jael, Jephthah's daughter, Saul and the witch of Endor, the Shunammite,
Isaiah 53, Jonah's storm); NT expansion (the salt of the earth, the
unmerciful servant, the rich young ruler, the sinful woman anointing Jesus's
feet, Jesus weeping over Jerusalem, the Areopagus sermon detail, Eutychus
falling from the window, Paul's shipwreck at Malta, the armour of God);
patristic (Justin Martyr's Dialogue with Trypho, the Cappadocian Fathers,
John Chrysostom's exile, Augustine's tolle lege); medieval (Anselm's
ontological argument, Aquinas's design argument, Julian of Norwich,
Catherine of Siena, Joan of Arc); Reformation (Tetzel, Diet of Worms,
Calvin's Institutes); modern (Carey in India, Hudson Taylor, Barth's
Barmen, Bonhoeffer's last words); worship and devotion (rosary, liturgical
colors, Jesus Prayer, Maundy Thursday, hymn history).

### T4 (+63 items)

Most theologically dense layer: Genesis 22 Akedah, Jacob wrestling, Joseph's
silver cup test, golden calf and the Levites, the bronze serpent and Hezekiah
breaking it, Achan in the Valley of Achor, Jael and Sisera, Jephthah's vow,
Solomon's 1000 wives and Ashtoreth / Milcom / Chemosh, Ahab and Naboth,
the Shunammite resurrection, Isaiah 53's "with his stripes", Daniel 9
seventy weeks, Ezekiel 1 living creatures, Jonah cast overboard, the third
temptation, the pure in heart, fasting properly, the rich young ruler,
the visitation in the hill country, Lazarus and the rich man, Dismas the
penitent thief, Jesus's high priestly prayer; Romans 3 hilasterion / mercy
seat, Romans 9-11 doxology, 1 Corinthians 15 swallowing of death, Ephesians 2:10
workmanship, Philippians 4:13 contentment, Colossians 1 hymn, Hebrews 7
Melchizedek priesthood, 1 Peter 2:24 bearing sins, Revelation 5 Lion-Lamb;
Edict of Milan, Constantinople 381 creed, Patrick's Confessio, Benedict's
Rule and ora et labora, Augustine of Canterbury, the 1054 Schism trigger;
Anabaptist baptisms, Luther's Greek text source, Ignatius's Spiritual
Exercises, Wesley/Whitefield split; Carey's languages, Hudson Taylor, Charles
Simeon, Barth's first move, Rahner's anonymous Christianity, Bonhoeffer's
last words, John Paul II's Polish masses; doctrinal density (Trinity essential
vs personal attributes, Chalcedon's hypostatic union, pre-Lent Septuagesima,
cardinal vs theological virtues, just-war criteria, seven deadly sins, the
icons controversy).

## 3. Topic coverage post-cleanup

Christian-only clusters in the active bank:

| Topic        | T1  | T2  | T3  | T4  | T5  | Total |
| ------------ | --: | --: | --: | --: | --: | ----: |
| OT           | 126 | 141 | 117 | 132 | 123 |  639  |
| NT           |  86 |  66 |  76 |  60 |  93 |  381  |
| Medieval     |   3 |   2 |   7 |   5 |   8 |   25  |
| Early Church |   3 |   2 |   5 |   2 |  12 |   24  |
| Reformation  |   1 |   1 |   2 |   4 |   3 |   11  |
| Modern       |   1 |   1 |   1 |   1 |   3 |    7  |
| Doctrine     |   0 |   1 |   0 |   0 |   1 |    2  |
| Apologetics  |   0 |   0 |   0 |   0 |   0 |    0  |
| Ethics       |   0 |   0 |   1 |   2 |   2 |    5  |
| Other        |   0 |   0 |   3 |   3 |   5 |   11  |

**Limitations of topic auto-classifier**: the OT/NT classifier eats most
items as soon as a biblical name appears. Many T3-T4 items I generated under
"Doctrine" or "Apologetics" pillars get classified as NT because they cite
Romans or Hebrews. So the bare counts above understate the doctrinal /
apologetics coverage. Each tier T1-T4 has solid coverage of: OT story,
NT story, early church, Reformation, modern Christianity.

## 4. Grammar / metadata

- Bank uses em-dash (U+2014) throughout; console encoding renders these as ? but the file is clean UTF-8.
- No double-space, missing punctuation, or weird metadata fields found.
- All entries use the canonical schema `{tier, question, answer, choices, context}`. New items conform exactly.

## 5. Stance / theology verification

- **Single God / Christian Trinity**: dominant. No pantheon residue remains in the active bank.
- **Killing monsters is righteous**: the bank doesn't speak directly to this gameplay rule but treats the Christian moral life as the orienting frame; nothing here contradicts the crusader framework.
- **No comparative-religion equivalence**: 239 items moved to dropped/. The active bank treats Christianity as true, doctrine as serious, the church's story as a real history.
- **Famous Bible stories at T1-T2**: Adam/Eve, Noah, Abraham, Moses, plagues, David, Daniel, Jonah, Christmas, Easter, Pentecost, Acts, key parables — all covered at the entry tiers.
- **Doctrinal depth at T3-T4**: Trinity, Incarnation, Atonement (Romans 3:25 hilasterion / mercy seat at T4), justification by faith (Ephesians 2:8-9), Nicaea / Chalcedon, the 1054 Schism, Anselm and Aquinas's God-arguments.
- **No sacrifice / no fasting as gameplay**: confirmed. Items mention Lenten fasting as historical/devotional context only (T2-T3); player gameplay is not touched.

## 6. Generation logs (saved offline)

Per the rebuild-discipline rule, generator scripts live in `tools/quizgen/scratch/`:

- `_theology_audit_classify.py` — initial topic / pantheon scan
- `_theology_audit_dump_full.py`, `_theology_audit_v2.py` — refinement to filter false positives
- `_theology_make_drop_list_v2.py` — precise drop-list builder (235 items)
- `_theology_drop_indices.json` — JSON list of indices dropped
- `_theology_apply_drops.py`, `_theology_apply_extra_drops.py` — apply the drops
- `_theology_gen_t1.py`, `_theology_gen_t2.py`, `_theology_gen_t2_supp.py`, `_theology_gen_t3.py`, `_theology_gen_t4.py` — generators (q() helper with double-assert on budget and parity)
- `_theology_t{1..4}_new.json`, `_theology_t2_supp.json` — generated batches
- `_theology_apply_new.py` — final merge into active bank
- `_theology_coverage_now.py` — post-merge coverage check

## 7. Conflict-priority outcomes

Per the operational priority spec:

1. **Drop-if-overcap**: none required (no FK>10 items remained in the active bank to drop on top of pantheon).
2. **Pantheon-residue (drop)**: 235 + 4 items moved to `dropped/`.
3. **Rote-replace**: not significant — the existing bank was already scene-led.
4. **Tier-shift**: not used. The cleanup left every tier short of the floor; generation filled tiers in place rather than redistributing.
5. **Grammar**: no fixes needed.
6. **Metadata**: no fixes needed.

## 8. Final state

- Active `data/questions/theology.json`: 1105 entries, all KEEP via the 5 gates.
- Dropped `data/questions/dropped/theology.json`: 1933 entries (preserved for future reference but never loaded by the game).
- `pytest -q`: 598 passed, 58.9 s.
