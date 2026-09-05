# Theology bank v2 — strand research prompt template

You are researching topics for the THEOLOGY bank rebuild for Philosopher's Quest — a wonder-driven, story-led kids' quiz bank about Western mythological + legendary heritage.

## Your job

Produce a JSON array of ~15-25 topic entries for the strand named below. Each entry is a ladder topic that will later be built into a 5-rung ladder (T1-T5, one cool named beat per rung). Write the entries to:

  `bankbuild/theology/_strands/spec_{STRAND_ID}.json`

## Voice + stance (READ CAREFULLY — this is a Kids Bank)

- The bank is Wonder Pattern, story-led. The most memorable question reveals the most specific cool fact about a story kids should know.
- Brandon is NOT Christian. The bank explicitly does NOT promote Christianity as metaphysically true. All four pillars (Christian / Greek / Norse / Western-mythology) sit on the SAME PLANE with the SAME narrative voice.
- **Symmetric-voice test**: if you write a Christian story with "fulfilled the prophecy" or "the Lord", DROP those framings. The same story told about Odin or Cuchulainn would sound weird with that language. Use plain narrative: "Jesus", "Paul", "the bishop Polycarp", "the crowd at Smyrna".
- No smug atheist voice ("primitive belief", "people used to think", scare-quoted God). No smug believer voice ("and that's why X is true").
- STORY, not doctrine. Not author-attribution. Not comparative religion.
- Answer hierarchy: NAMED THINGS > VIVID ACTIONS > OBJECTS > NUMBERS > GENERIC LABELS (banned).

## Sourcing rule (per pipeline)

- **Grokipedia FIRST** (grokipedia.com). If Grokipedia returns 403 to fetch, USE THE BROWSER directly.
- Wikipedia SECOND (only when Grokipedia lacks depth).
- Primary sources when available (Snorri's Prose Edda, Hesiod's Theogony, Homer, the Gospels, Táin Bó Cúailnge Recension I, Malory's Le Morte d'Arthur, Chrétien de Troyes, the Song of Roland, Robin Hood ballads, saint Acta Martyrum).

## Topic entry schema (JSON per topic)

```json
{
  "name": "One-line topic title (e.g. 'Polycarp of Smyrna: eighty and six years')",
  "section": "christian" | "greek" | "norse" | "western_myth",
  "strand": "the strand name (short label)",
  "kind": "ladder",
  "scope": "A 350-500 word narrative that maps T1..T5 rungs and lists further beats. T1: opening scene, easy named recognition. T2: the specific act/quote/object. T3: the deeper story beat. T4: the pointed detail (a named artifact, a specific line, a specific location). T5: the payoff / civilizational-mythic weight OR the honest complication. Then 2-4 'Further rungs:' beats that expand the ladder if depth permits. NAME THE NAMED THINGS: quotes verbatim (with source), artifacts, epithets, locations, specific people involved. Where a myth has variants (Grail across Chretien/Malory/Wolfram), name the version and its source.",
  "tier_span": "T1-T5",
  "source": "Comma-separated primary + secondary citations. Grokipedia first ('read via browser' if 403), then Wikipedia, then primary sources. Cite the ACTUAL passage: e.g. 'Snorri Sturluson, Prose Edda, Skaldskaparmal 42 -- the making of Mjolnir by Sindri and Brokkr'. Named specifics only — never vague 'various sources'.",
  "framing_note": "Voice + accuracy rails. State the DINNER TEST payoff (which rung is the wait-what?). State the DISTRACTOR MINE (which adjacent-but-wrong real figures/objects populate the wrong choices). State the ANTI-RESTATEMENT rail (the stem sets the SCENE, never contains the answer's noun before the choices). State the SYMMETRIC-VOICE check for Christian stories (would this land the same way told about Odin or Cuchulainn?). Call out any HISTORICAL vs LEGENDARY distinction that must be honest (Excalibur = pure legend; Beowulf = 8-11th c. Anglo-Saxon poem; Cuchulainn = 7-11th c. Ulster Cycle manuscripts).",
  "vision_mandated": false,
  "history_overlap": "Note overlap with sister banks. HISTORY owns actual wars/empires/kings-as-heads-of-state -- theology owns the STORIES that survived (e.g. Roland at Roncesvalles as chanson, not military history). GEOGRAPHY owns sacred sites as PLACES -- theology owns what HAPPENED at them in story (Ararat as place = geography; the Ark landing on Ararat = theology). PHILOSOPHY owns moral reasoning -- theology owns moral reasoning INSIDE a story (Job's argument WITH God = theology; the problem of evil as a reasoning move = philosophy). If there's a candidate overlap, key different facts here vs the sister bank.",
  "weight": "high" | "medium",
  "depth": "deep" | "shallow",
  "target_q": 5-12
}
```

## Special rules for this strand

**{STRAND_SPECIFIC_INSTRUCTIONS}**

## Deliverable

Write the JSON array to `bankbuild/theology/_strands/spec_{STRAND_ID}.json`. Print `WROTE spec_{STRAND_ID}.json (N topics)` when done.
