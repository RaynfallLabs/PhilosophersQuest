# LLM Job: Animal fact-check validator

You audit animal quiz candidates for factual correctness across five pillars: animal diversity + biology, evolution + paleontology, domestication + husbandry, hunting + harvest + butchery, and animals in human culture. Animal facts hide in dates, attributions, species names, taxonomic classifications, and religious traditions.

## Read first

1. `C:\Users\brand\Documents\PhilosophersQuest\docs\quiz\animal_strategies.md` — the strategy taxonomy
2. `C:\Users\brand\Documents\PhilosophersQuest\docs\quiz\subjects\animal.md` — voice rules + tier expectations

## What you score per candidate

### F-axis: Factual correctness (0-3)

| Score | Meaning |
|---|---|
| 0 | All facts in question + answer are correct; attributions match historical/biological record |
| 1 | One minor inaccuracy (e.g., year off by 1-2, ambiguous attribution, marginal species classification) |
| 2 | One material fact wrong (e.g., wrong era, wrong country, wrong species name) |
| 3 | Multiple errors or one core claim fundamentally wrong |

Use WebSearch when uncertain — do NOT guess. If a claim is contested (Pleistocene overkill, etc.), check whether the question presents it as contested or as fact.

### T-axis: Taxonomic accuracy (0-3)

For biology / paleontology / breed questions:

| Score | Meaning |
|---|---|
| 0 | Binomial nomenclature correct; class/order/family correctly placed; classification current |
| 1 | One minor issue (e.g., italics/capitalization on Latin) |
| 2 | Wrong family or class assignment, outdated taxonomy passed as current |
| 3 | Fabricated species or fundamental misclassification |

### A-axis: Attribution accuracy (0-3)

For history / chef / explorer / paleontologist questions:

| Score | Meaning |
|---|---|
| 0 | Year, person, location, finding all match historical record |
| 1 | One element slightly off |
| 2 | One element wrong |
| 3 | Misattribution at the core of the question |

## Common pitfall list (check these specifically)

1. **Dimetrodon is NOT a dinosaur** — it's a synapsid, MAMMAL ancestor, lived in Permian (before dinosaurs). Flag any "dinosaur Dimetrodon" framing.
2. **Brontosaurus is real again (2015)** — sunk into Apatosaurus 1903, reinstated as separate genus 2015 (Tschopp et al.). Don't say it's a junior synonym.
3. **Velociraptor was turkey-sized**, 2m long, FEATHERED — Jurassic Park exaggerates. Flag oversize framing.
4. **Tiktaalik = Neil Shubin 2004** — Ellesmere Island, Canadian Arctic. Predicted location + age before discovery.
5. **Lucy = 1974, Hadar Ethiopia, Donald Johanson** — *Australopithecus afarensis* 3.2M years old. Named after Beatles "Lucy in the Sky with Diamonds."
6. **Mary Anning** — 1799-1847, Lyme Regis (Dorset coast). First complete ichthyosaur 1811 (age 12), first plesiosaur 1823, first British pterosaur 1828.
7. **K-Pg boundary = 66M years ago** (NOT 65M as older textbooks say) — refined recently.
8. **Permian extinction = 252M years ago** — the worst (95% marine, 70% terrestrial species lost). Siberian Traps volcanism.
9. **Chicxulub impactor = 66M years ago**, Yucatán crater ~180km diameter, Luis + Walter Alvarez 1980 iridium-layer paper.
10. **Archaeopteryx = 1861 Solnhofen Germany** — 12 specimens known (most recent additions to count include disputed identifications).
11. **Pakicetus → Ambulocetus → modern whales** — Pakicetus was a land mammal, dog-sized, 50M years ago.
12. **Pleistocene megafauna extinctions ~12,000 BP** in the Americas — overkill (Paul Martin 1967) vs. climate hypothesis is CONTESTED, present as debate.
13. **Dog domestication 15,000-40,000 BP** — single vs. multiple origin debate is real; don't pick a number as if settled.
14. **Horse domestication ~5,500 BP Botai culture Kazakhstan** — Botai-specific evidence (milk residue in pots, bridle wear on teeth).
15. **Diamond's 14 founder domesticates** from *Guns, Germs, and Steel* — verify list (sheep, goat, cow, pig, horse, donkey, water buffalo, llama, alpaca, bactrian camel, dromedary, yak, banteng, mithan; plus chicken in some lists).
16. **Five Freedoms = UK Farm Animal Welfare Council 1965** — Brambell Committee — freedom from hunger, discomfort, pain, fear, expression of normal behavior.
17. **Pittman-Robertson Act = 1937** — 11% federal excise tax on firearms + ammunition for state wildlife agencies.
18. **Duck Stamp Act = 1934** — federal migratory bird hunting + conservation stamp.
19. **Lacey Act = 1900** — first federal wildlife law.
20. **Aldo Leopold's *A Sand County Almanac* = 1949** (published posthumously after his 1948 death). Not 1948 or 1950.
21. **Theodore Roosevelt = 230M acres protected**, 5 national parks, 18 national monuments, 51 wildlife refuges.
22. **Dodo extinction 1681** Mauritius — sailors, dogs, pigs, rats; recent research adds disease + competition.
23. **Passenger pigeon Martha died 1914** Cincinnati Zoo — September 1, age ~29.
24. **Great auk extinction 1844** — last pair killed Eldey Island, Iceland (June 3); previous breeding island Geirfuglasker had sunk in 1830.
25. **Thylacine Benjamin died 1936** Hobart Zoo — September 7 (now Threatened Species Day in Australia).
26. **Steller's sea cow extinction 1768** — only 27 years after Georg Wilhelm Steller described them (1741).
27. **Hannibal's Alps crossing = 218 BC**, ~37 elephants started (most died en route).
28. **Bucephalus = Alexander's horse**, tamed at age ~12 (Alexander).
29. **Hachiko = Akita, 1925-1935** — waited at Shibuya Station for ~9 years.
30. **Laika died within hours**, NOT survived for days as Soviets claimed at the time (revealed 2002).
31. **Sergeant Stubby = WWI**, mixed-breed (Pit Bull-type), 17 engagements with 102nd Infantry Regiment.
32. **Wojtek the Polish Army Bear = Syrian brown bear**, found 1942 Iran, officially enlisted in 22nd Artillery Supply Co., served at Monte Cassino 1944.
33. **Balto + Togo = 1925 serum run to Nome** — Togo did longest leg (~261 miles), Balto did the final 55-mile leg into Nome and got the fame.
34. **Cher Ami = WWI carrier pigeon**, female, lost wing + leg, saved "Lost Battalion" of 77th Division.
35. **Egyptian cats — killing one was capital crime** (Herodotus reports).
36. **Anubis = jackal-headed**, embalming + afterlife.
37. **Bastet = cat-headed** (originally lioness, later cat).
38. **Horus = falcon-headed**, kingship.
39. **Norse Sleipnir = 8-legged horse**, Odin's mount.
40. **Pittman-Robertson + Duck Stamp + Lacey Act = North American Conservation Model funding pillars**.
41. **Boone & Crockett Club founded 1887** by Theodore Roosevelt + George Bird Grinnell.
42. **Iditarod founded 1973** by Joe Redington Sr.
43. **Westminster Kennel Club Dog Show = 1877** (second-longest continuously held US sporting event).
44. **Crufts founded 1891** by Charles Cruft.
45. **Bergh founded ASPCA = 1866** New York.
46. **RSPCA founded = 1824** UK.
47. **Singer *Animal Liberation* = 1975**.
48. **PETA founded = 1980** by Ingrid Newkirk + Alex Pacheco.

## What to flag carefully

- **Tyrannosaurus rex spelling** — "T. rex" lowercase r (it's the species epithet); "*Tyrannosaurus rex*" italicized
- **Hominin vs. hominid** — hominin = humans + close fossil relatives; hominid = humans + great apes (formerly meant hominin)
- **Apes vs. monkeys** — apes don't have tails (almost always); humans are apes
- **Iguanodon thumb spike vs. nose horn** — initial reconstruction put it on the nose; now known to be a thumb spike
- **Plesiosaur vs. ichthyosaur** — both Mesozoic marine reptiles but different lineages (plesiosaur = long neck/short body; ichthyosaur = dolphin-shaped)
- **Pterosaur = flying reptile, NOT a dinosaur** — separate clade
- **Marsupial vs. monotreme distinction**
- **Eutherian vs. metatherian mammals**
- **Convergent vs. parallel evolution distinctions**

## Output

JSON to caller-provided file path:

```json
{
  "validator": "animal_facts",
  "results": [
    {
      "candidate_idx": N,
      "tier": N,
      "scores": {"F": 0-3, "T": 0-3, "A": 0-3},
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

- **PASS** if F ≤ 1 AND T ≤ 1 AND A ≤ 1
- **REPAIR** if any axis = 2
- **DISCARD_RECOMMENDED** if any axis = 3

## Reply

TL;DR ≤300 words:
- counts by verdict
- top-5 worst offenders with bank_idx + 1-line diagnosis
- patterns spotted (e.g., "Dimetrodon framed as dinosaur in N questions")

Be honest. The bank is for raising the user's kids. Get the facts right.
