# Theology Bank v2 — Queue Review

**Ship target**: v2.7.0 (replaces the current 1,320-Q theology bank)
**Voice**: Wonder Pattern, story-led, symmetric across all four pillars (no Christian-favoring framing)
**Estimated build cost**: ~358 topics × 6-9 agent messages/topic ≈ **2,500-3,200 Opus messages**
**Files**: `bankbuild/theology/_queue.json`, `register.json`, 16 spec files in `_strands/`

---

## Question shares vs your target

You asked for **40 / 20 / 20 / 20** (Christian / Greek / Norse / western myth).

The research assembled to this:

| Pillar        | Topics | Est. Q | **Share** | Target | Delta |
|---------------|-------:|-------:|----------:|-------:|------:|
| Christian     | 138    | 1,301  | **34%**   | 40%    | **-6pp** |
| Greek         | 73     | 803    | **21%**   | 20%    | +1pp |
| Norse         | 61     | 686    | **18%**   | 20%    | -2pp |
| Western myth  | 86     | 946    | **25%**   | 20%    | **+5pp** |
| **TOTAL**     | 358    | **3,736** | | | |

Two things drift off:
- **Christian is 6pp light** (research came in at 6 strands × ~23 topics avg; target 40% would want ~150 topics)
- **Western myth is 5pp heavy** (4 sub-strands ×~21 topics each; Ireland alone is 2 strands = 44 topics, which is what pushes it above target)

Also: **~3,700 Q is ABOVE your 2,500-3,000 target range** — cut potential is real.

## Three ways to true up the shares

### Option A — accept as-is (34/21/18/25, ~3,700 Q)
Ship the imbalance. You get the full Irish-mythology depth (Tuatha Dé + Cúchulainn + Fianna all at full weight), full Beowulf/Volsung/Ragnarok, full Charlemagne/Roland/El Cid — but Christianity ends up 34% instead of 40%. Bank is larger than target.

### Option B — trim western myth to hit 40/20/20/20 (**recommended**)
Drop ~14 lower-priority topics from western myth strands (~150 Q), keeps ~3,580 total, gets Christian to ~36% (still not 40 but closer). To *actually* hit 40%, we'd need to drop 40+ western myth topics — which would gut Robin Hood or Tuatha or Cúchulainn as a strand. **My recommendation is a light trim (~10-15 topics from Robin Hood/medieval-legend, which is our lowest-fidelity strand because Faust/Wilhelm Tell/Melusine are more literature than myth) and accept 36-37% Christian.**

### Option C — add a P1.5 Christian batch (+40 topics, keeps ~3,700 total)
Add another Christian strand: e.g. **"Old Testament wonder-stories"** (Job's whirlwind, Ezekiel's wheels, Isaiah's coal, Daniel in the lions' den at depth, Elisha's floating axe-head, Balaam's donkey) OR **"Reformation + heretics"** (Luther nailing 95 theses, Zwingli, Calvin at Geneva, Cathars + Albigensian, Waldensians, Wycliffe's Lollards). Bank grows to ~4,100 Q. Hits 40% clean.

## Cross-strand dedup risk

Not yet run — the research prompts had distinct coverage but the following are worth checking:
- **Loki appears in TWO Norse strands** (Aesir-gods "Baldr's death via Loki + mistletoe" vs Loki-tricks "Loki fathers Baldr's death via mistletoe") — likely a real dup
- **Ragnarok mentions Odin/Fenrir + Thor/Jormungandr** which also live in the Aesir-gods strand (Odin at the well, Thor fishing) — probably DIFFERENT beats (Ragnarok = death, Aesir = life) but worth verifying
- **Cattle Raid of Cooley + Táin** — one topic covers both in the Cuchulainn strand
- **Beowulf ×3** (Grendel, Grendel's mother, dragon-and-Wiglaf) — three separate topics with distinct rungs, not dup risk

If we hold on ship, I can run the sharded dedup pass (5 agents: 4 within-section + 1 cross-section) to catch same-fact clusters before build. That saves ~10-20 wasted topic builds.

## Vision-mandated / stance-flagged topics

Only **3 vision_mandated** (topics where the framing MUST enforce a moral-vision rail — e.g. the Book of Joshua/conquest question, the treatment of the Pythia at Delphi, the honest paganism of Ragnarok). Compared to science (which had 40+ vision_mandated for pharma/climate/vaccine), theology is a lower-stance-load bank — story-first, moral-vision-second, because the Wonder Pattern picks up the load.

## Sister-bank overlap flags

353 of 358 topics (99%) carry `history_overlap` notes distinguishing theology's story-fact from history/geography/philosophy's version of the same figure — that's expected and correct (Roland at Roncesvalles is history AND chanson; Jerusalem is a place AND the setting of Pentecost).

---

## What I need from you

1. **Rebalance choice**: A (accept), B (trim western myth, recommended), or C (add Christian).
2. **Dedup**: run the sharded dedup pass before build (adds ~5 more Opus agent calls) or trust strand separation and go straight to build?
3. **Total ceiling**: if you want to STRICTLY cap at 3,000 Q, we should trim (Option B hard-trim) — otherwise the bank ships at whatever the shares land at.

Once you decide, I run any trims / dedup, then the batched build kicks off (this is the ~2,500-message stretch; will take a full day at 3-concurrent Opus).

---

## POST-TRIM + POST-DEDUP FINAL NUMBERS

You chose **B** (light trim) + **Yes** (dedup). Both executed:

**Trim** (Robin Hood/medieval-legend): dropped Siegfried (duplicate of Norse Sigurd/Volsung), Melusine, Tam Lin, William Tell, Doctor Faustus — 5 topics / 52 Q.

**Sharded dedup** (4 within-section + 1 cross-section, all Opus):
- Christian: 0 dups (clean)
- Greek: 1 dup (Atlas-holding-sky duplicated with the Hesperides labor — kept the labor)
- **Norse: 7 dups** (Loki-tricks strand duplicated 7 Aesir-gods topics: Baldr, Sleipnir origin, Idunn, Thrymskvida, Mead of Poetry, Gleipnir/Tyr, Skidbladnir+Gullinbursti — kept the Loki-tricks placements which frame the making-of)
- Western myth: 0 dups (clean; borderline pairs like two Morrigan topics, Camelot vs Round-Table Fellowship, four Grail-arc lenses all judged distinct-facts)
- Cross-section: 0 dups (Christian Brigid vs Tuatha Brigid = different scopes; Grail-cup vs Last-Supper cup = same object different tradition, both belong)

**Final queue**: **345 topics / 3,591 Q**

| Pillar        | Topics | Est. Q | **Share** | Target |
|---------------|-------:|-------:|----------:|-------:|
| Christian     | 138    | 1,301  | **36%**   | 40% (-4pp) |
| Greek         | 72     | 792    | **22%**   | 20% (+2pp) |
| Norse         | 54     | 604    | **17%**   | 20% (-3pp) |
| Western myth  | 81     | 894    | **25%**   | 20% (+5pp) |

The trim+dedup narrowed the drift (Christian 34→36; western myth 25→25) but Christian is still 4pp under target. To close that gap you can:

**(i) Accept 36/22/17/25 and go to build now** (recommended — the shares are reasonable, the pillars all have meaningful weight, and the bank size 3,591 is comparable to science's shipped 3,682).

**(ii) Add a P1.5 Christian expansion strand** (~30 topics, +300 Q, bank grows to ~3,900): candidates are (a) OT wonder-stories at depth (Job's whirlwind, Ezekiel's wheels/dry bones, Isaiah's coal, Balaam's donkey, Elisha's floating axe-head), (b) Reformation + heretics (Luther/95 Theses, Cathars, Waldensians, Wycliffe, Zwingli, Calvin at Geneva), or (c) Church history — councils, martyrs, and schisms (Nicaea + Arius, Chalcedon, iconoclasts, Byzantine Iconoclasm, the Great Schism of 1054, Photius). This hits 40% clean.

**(iii) Deeper trim of western myth** — cut 15 more topics (Cúchulainn from 22→15, Tuatha from 21→17): brings western myth to ~20% but costs Irish-mythology depth. Not recommended given Brandon's earlier "40/20/20 + 20% Irish/English" call — the whole point of that 20% was to include Cúchulainn/Fianna.

