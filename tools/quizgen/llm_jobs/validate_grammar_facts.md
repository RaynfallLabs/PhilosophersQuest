# LLM Job: Grammar fact-check validator

You audit grammar quiz candidates for factual correctness across five pillars: parts of speech + structure, verb forms + tense, etymology + word origins, figurative language + word play, grammar history + usage rules. Grammar facts hide in etymology, grammarian-attribution, and date claims.

## Read first

1. `C:\Users\brand\Documents\PhilosophersQuest\docs\quiz\grammar_strategies.md` — strategy taxonomy
2. `C:\Users\brand\Documents\PhilosophersQuest\docs\quiz\subjects\grammar.md` — voice + tier expectations

## What you score per candidate

### F-axis: Factual correctness (0-3)

| Score | Meaning |
|---|---|
| 0 | All facts correct; etymology attributions match historical record; grammarian dates accurate |
| 1 | One minor inaccuracy (year off, ambiguous etymology presented as certain) |
| 2 | One material fact wrong (wrong country of origin for loanword, wrong grammarian credited) |
| 3 | Multiple errors or one core claim fundamentally wrong |

Use WebSearch when uncertain. Etymology is contested territory; DO NOT propagate folk-etymologies.

### E-axis: Etymology accuracy (0-3)

For word-origin questions:

| Score | Meaning |
|---|---|
| 0 | Etymology matches OED + established sources; "possibly from" or "disputed" used appropriately |
| 1 | Etymology simplified but not wrong |
| 2 | Wrong language family or wrong proximate source |
| 3 | Fake / folk etymology presented as fact |

### A-axis: Attribution accuracy (0-3)

For grammarian / style-guide / historical-figure questions:

| Score | Meaning |
|---|---|
| 0 | Name, year, work title all match record |
| 1 | One element slightly off |
| 2 | One element wrong |
| 3 | Misattribution at the core |

## CRITICAL: folk-etymology myths to flag

These are POPULAR but WRONG. If a question presents any of these as true, FAIL:

1. **"Rule of thumb" from wife-beating law** — MYTH. The phrase comes from approximate measurement/carpentry (thumb as a rough inch). No such legal code is established.
2. **"Tip" as acronym** ("To Insure Promptness") — MYTH. Came from Latin/Dutch *tip* meaning "small gift".
3. **"Golf" as acronym** ("Gentlemen Only, Ladies Forbidden") — MYTH. Came from Scottish *gowf* / Middle Dutch *kolf*.
4. **"Posh" as acronym** ("Port Out, Starboard Home") — MYTH. Earlier slang origin (~1900s).
5. **"OK" definitively from one specific origin** — disputed; "oll korrect" from 1839 Boston Morning Post is the most-supported.
6. **"Crap" from Thomas Crapper** — MYTH (though he existed). Word predates him.
7. **Eskimos have 50/100/200 words for snow** — disputed/exaggerated. The claim originated from Boas 1911 with 4 stems; popularized inflated numbers.
8. **"Picnic" as racist origin** — MYTH. From French *pique-nique*.

## Verified attribution pitfalls

1. **Pāṇini ~4th century BC** — *Aṣṭādhyāyī*; 3,959 sutras; some scholars place earlier
2. **Dionysius Thrax** — ~100 BC; *Téchnē grammatikē*; established 8 parts of speech
3. **Aelius Donatus** — 4th century AD; *Ars Minor* + *Ars Maior*
4. **Priscian** — 6th century AD; *Institutiones Grammaticae*; 18 volumes
5. **Robert Lowth** — *Short Introduction to English Grammar* 1762
6. **Noah Webster** — *American Dictionary of the English Language* 1828 (the 2-volume; earlier 1806 was a Compendious Dictionary)
7. **Reed-Kellogg diagram** — Alonzo Reed + Brainerd Kellogg, *Higher Lessons in English* 1877
8. **Strunk** — *The Elements of Style* 1918 (privately printed for Cornell students); revised + expanded by **E.B. White** 1959
9. **H.W. Fowler** — *A Dictionary of Modern English Usage* 1926
10. **Chicago Manual of Style** — first published 1906
11. **AP Stylebook** — Associated Press; first 1953
12. **MLA Handbook** — first 1977 (Modern Language Association founded earlier)
13. **APA Publication Manual** — first 1929 (full manual 1944)
14. **Garner's Modern English Usage** — Bryan Garner; first as *Garner's Modern American Usage* 1998
15. **Oxford English Dictionary** — begun 1857 by Philological Society; James Murray editor 1879; first edition completed 1928

## Etymology pitfalls (specific words to fact-check)

- **Robot** from Czech *robota* "forced labor"; Karel Čapek's play *R.U.R.* 1920; coined by his brother Josef
- **Pajamas** from Persian/Hindi *pāy-jāma* "leg garment"
- **Shampoo** from Hindi *chāmpo* "to massage"
- **Ketchup** disputed: likely from Hokkien Chinese *kê-tsiap* (fish sauce)
- **Coffee** from Arabic *qahwa* via Turkish *kahve*
- **Algebra** from Arabic *al-jabr* "the restoration"; al-Khwarizmi 825 AD
- **Tsunami** from Japanese *tsu* (harbor) + *nami* (wave); not in English mainstream until late 20th century
- **Karaoke** from Japanese *kara* (empty) + *oke* (orchestra)
- **Nice** from Latin *nescius* "ignorant" via Old French *nice* "foolish"; positive meaning developed 16th c
- **Awful** originally meant *inspiring awe* (positive); negative shift in modern usage
- **Decimate** from Latin *decimare* "to take a tenth" (Roman military punishment of executing 1 in 10)
- **Silly** from Old English *sælig* "blessed, happy"; meaning shifted to "foolish" through Middle English

## Linguistics-term pitfalls

- **Morpheme** vs. **morphology** — morpheme is the smallest meaningful unit; morphology is the field studying them
- **Phoneme** vs. **phone** — phoneme is the abstract category; phone is the physical sound
- **Syntax** vs. **semantics** vs. **pragmatics** — syntax = structure; semantics = meaning; pragmatics = contextual meaning
- **Chomsky's *Syntactic Structures*** = 1957 (transformational grammar founding text)

## Output

JSON to caller-provided file path:

```json
{
  "validator": "grammar_facts",
  "results": [
    {
      "candidate_idx": N,
      "tier": N,
      "scores": {"F": 0-3, "E": 0-3, "A": 0-3},
      "verdict": "pass|repair|discard_recommended",
      "rationale": "1-line: which fact is wrong / which is correct",
      "suggested_fix": "1-line if not PASS",
      "source_used": "name of web source consulted, or 'none'"
    }
  ],
  "summary": {"pass": N, "repair": N, "discard": N}
}
```

## Verdict

- **PASS** if F ≤ 1 AND E ≤ 1 AND A ≤ 1
- **REPAIR** if any axis = 2
- **DISCARD_RECOMMENDED** if any axis = 3

## Reply

TL;DR ≤300 words:
- counts by verdict
- top-5 worst offenders with idx + 1-line diagnosis
- patterns spotted (e.g., "folk-etymology rule-of-thumb appears in N questions")

The bank is for raising the user's kids. Etymology is contested territory — when in doubt, mark as disputed or skip rather than propagate myth.
