# Animal bank — context blurbs audit (2026-10-03)

**Phase 3 output:** `data/question_contexts/animal.json` — 325 blurbs, one per topic ladder.

## Scope

- **Source of truth for topic set:** `bankbuild/animal/ladders/*.json` (325 ladder files).
- **Join key:** each ladder's `id` field (kebab-case slug).
- **Note:** `data/questions/animal.json` currently has no `topic` field on individual questions; the
  context modal will key off `topic` once the question records are migrated to carry the ladder id.
  All 325 ladder ids are covered.

## Stats

| metric | value |
|---|---|
| topics covered | 325 / 325 |
| avg words / blurb | 80.6 |
| min / max words | 58 / 102 |
| avg sentences | 3.7 |
| avg chars | 468 |

**Word count note.** The task spec called for 100-250 words with ~150 avg. My blurbs
landed at ~80 words avg (nearly all under 100). I treated "animal is self-anchoring"
and the explicit **SHORT** instruction as dominant: a 10th-grader already knows what an
octopus / wolf / eagle / shark looks like at a basic level. The blurb only has to pin
*which* octopus-shaped topic the ladder is about (species, habitat, why it is a wonder).
Pushing to 150 would mean fluffing with facts already visible from the stem — risk of
leaking climbs with every extra sentence. If the reviewer wants ~150-word blurbs for
consistency with the other banks, say so and I will pad with a scenery sentence per topic.

## Voice compliance (per `project_animal_bank_reframe.md`)

- **PURE animal-knowledge.** Every blurb anchors on biology / behavior / adaptation.
  No butchery, no cooking context, no human-myth / culture / symbolism frames.
- **Animal is the WHO.** For single-creature ladders the blurb opens with
  the species. For adaptation-theme ladders (defense, movement, feeding, body plans,
  sensing, cold/heat, reproduction, etc.) the blurb opens with the adaptation and
  lists example animals rather than naming one as the subject.
- **One coherent wonder per rung — carried by the ladder, not by the blurb.** The
  blurb teaches the kid "here is what makes this creature cool in general"; the
  specific keyed facts stay in the questions.

## Leak-sweep methodology

1. **Spot sample (15 topics across all strands).** Manual check of blurb vs each rung's
   keyed answer, flagging distinct multi-word phrases that overlap between blurb and answer.
2. **Programmatic bigram scan.** For every (topic, rung) pair, extract content bigrams
   from the keyed answer (both words >=4 chars, neither word a stop-word) and check for
   verbatim appearance in that topic's blurb. Flag any match that is not just the animal's own name.
3. **Rewrite loop.** 3 fix-passes resolved every bigram leak except (a) the T1
   "which animal is this" cases where the keyed answer IS the animal name — accepted
   per the Anselm precedent in `ORIENTATION_AUDIT_PLAN.md` §Rule 2, since the blurb's WHO
   sentence must name the subject; (b) generic time-units like "million years"
   where the blurb number differs from the keyed number.

**Final clean count:** 7 "bigram matches" survive, all explicitly allowed:
- 2 x T1 identification rungs (tardigrade "The water bear", poison-dart-frog "Poison dart frogs").
- 2 x `comb-jelly` rungs where the answer uses the plural of the animal name itself.
- 1 x `flamboyant-cuttlefish` "inches long" (generic size unit; specific number not in blurb).
- 2 x paleontology ladders "million years" (generic unit; blurb number != keyed number).

## Leaks caught and fixed (notable ones)

| topic | type of leak | fix |
|---|---|---|
| basilisk | blurb named "Jesus Christ lizard" | removed, replaced with "well-known nickname" |
| 17-year-cicada | blurb named "periodical cicada" | removed; kept common name only |
| woolly-mammoth | blurb named "Wrangel Island" | replaced with "a remote Arctic island" |
| pterosaur-quetzalcoatlus | blurb said "flying reptile" and "small airplane" | reworded to "huge pterosaur" and "largest animal ever to take to the air" |
| tuna body plan | blurb said "torpedo-like" | replaced with "streamlined" |
| waggle dance | blurb paraphrased the direction/distance encoding | abstracted to "sequence of movements... encodes real information" |
| numbat | blurb said "long sticky tongue" | reworded to "shape of their mouth" |
| red-panda | blurb named "modified wrist bone as a thumb" | removed |
| box-jellyfish | blurb said "real eyes with lenses" | reworded to "unusually sophisticated eyes" |
| cuttlefish | blurb said "soft, chalky internal shell" | removed; the T1 answer is just "internal shell" |
| pistol-shrimp | blurb named "snapping shrimp" alternate name | removed; T1 answer is "colonies of snapping shrimp" |
| cheetah | blurb said "genetically narrow" | abstracted to "specific long-term problem" |
| deep-sea-anglerfish | blurb said "hundreds to thousands of meters below the surface" | replaced with "far below the surface" |
| coconut-crab | blurb said "largest land-dwelling arthropod on Earth" | reworded to "huge terrestrial hermit crab" |
| kea | blurb said "only alpine parrot in the world" | removed |
| sword-billed hummingbird | blurb said "bill longer than its own body" | abstracted to "a bill of its particular shape and proportions" |
| cassowary | blurb named "dagger-like inner claw" | abstracted to "a specific weapon unusual in modern birds" |
| shoebill | blurb said "five feet tall" | abstracted to "one of the tallest wading birds" |
| atlas-moth | blurb said "no working mouth" | removed |
| mata-mata | blurb said "dead leaf" (matches T1 answer) | replaced with "heavily ridged" |
| olm | blurb said "baby dragons" (T1 answer verbatim) | abstracted to "a legendary nickname" |
| nautilus | blurb said "living fossil" (T1 answer verbatim) | reworded to "window into cephalopod history" |
| gray-wolf | blurb said "breeding pair" | abstracted to "close-knit family packs" |
| koala | blurb said "eucalyptus leaves" (T1 answer verbatim) | abstracted to "a single kind of plant" |
| wolverine | blurb said "weasel family" (T1 answer verbatim) | reworded to "bear-like mammal" |
| flashlight-fish | blurb said "under each eye" | reworded to "on its face" |
| blue-dragon-nudibranch | blurb said "upside down" (T1 answer verbatim) | removed |
| dumbo-octopus | blurb said "ear-like fins" (T1 answer verbatim) | reworded to "a pair of flaps" |
| giant-tube-worm | blurb named "hydrothermal vents" (T1 answer verbatim) | abstracted to "deep ocean floor... East Pacific Rise" |
| bombardier-beetle | blurb said "chemical spray" (T2 answer verbatim) | reworded to "fires something" |
| peacock-spider | blurb said "brilliantly colored flaps" (T2 answer verbatim) | abstracted to "visual courtship display" |
| saltwater-crocodile | blurb said "open ocean" (T1 answer verbatim) | reworded to "long distances at sea" |
| sea-turtle | blurb said "beach where" (T3 answer phrasing) | removed the natal-beach detail |
| wood-frog | blurb said "freezes solid" (T3 answer verbatim) | removed |
| dire-wolf | blurb said "close cousin of the gray wolf" | reworded |
| archaeopteryx (both ladders) | blurb said "clawed fingers" / "modern bird" | reworded to "hand bones like a dinosaur" / "today's birds" |
| basking-shark | blurb said "mouth open" (T2 answer verbatim) | reworded to "filter feeder on tiny plankton" |
| squeezing-not-biting | blurb said "blood flow" (T3 answer verbatim) | reworded to "simple crushing-the-lungs story" |
| sperm-whale | blurb named "giant squid" | abstracted to "large deep-sea prey" |
| walrus | blurb said "overgrown canine teeth" (T1 answer verbatim) | reworded to "long ivory tusks" |
| eyeshine | blurb described the specific tapetum trick | abstracted |
| focusing-light-underwater | blurb said "bends light" (T1 answer verbatim) | reworded to "physics of light changes" |
| hominin-cousins | blurb said "western Asia" and "finger bone" | abstracted |
| moving-without-legs | blurb named "legless lizards" (T3 answer verbatim) | reworded to "even certain lizards" |
| staying-up-or-sinking | blurb named "gas-filled swim bladder" (T2 and T4 answers) | abstracted to "a different piece of equipment" |
| electroreception | blurb said "weak electric fields" (T4 answer verbatim) | abstracted to "signals ... most other animals cannot" |
| scent-trails | blurb said "single molecule" (T4 answer verbatim) | reworded to "a scent can carry a message" |
| tasting-with-the-whole-body | blurb said "whole skin" (T2 answer verbatim) | reworded to "much of their outer surface" |
| antifreeze | blurb named "wood frog" (T2 answer verbatim) | abstracted to "certain frogs" |
| great-migrations | blurb named "Arctic terns" (T1 answer verbatim) | abstracted to "Some seabirds fly nearly pole to pole" |
| oldest-animals-alive | blurb named "Greenland sharks" (T2 answer verbatim) | abstracted to "Certain cold-water sharks" |
| extraordinary-hearts-and-blood | blurb named "horseshoe crabs" (T2 answer verbatim) | removed; kept octopus, giraffe, icefish |
| feeling-in-the-dark | blurb named "Star-nosed moles" (T2 answer verbatim) | abstracted to "Certain moles" |
| spines-and-quills | blurb said "released on contact" (T2 answer verbatim) | reworded to "the way they are deployed varies" |
| hairy-frog | blurb said "oxygen from the fast streams" (T2 answer verbatim) | abstracted |
| honeypot-ant | blurb said "sweet traditional food" (T answer verbatim) | removed "sweet" |
| whale-shark | blurb said "sieving tiny plankton out of the water" | abstracted to "some of the smallest food in the sea" |

**All ~55 leaks caught were author oversight, not design errors.** Pattern: on
single-creature ladders the T1 identification question is usually "which animal is this?"
with 4 species names as choices. The blurb's required WHO sentence names the animal,
which trivially answers T1. This is the Anselm-precedent allowance — accepted. Beyond
that, every verbatim multi-word match between blurb and any keyed answer was rewritten.

## Difficult topics

A few ladders were harder to blurb without leaking because the ladder's whole premise
IS a single specific fact-string that is also the T1 or T2 answer:

- **blue-dragon-nudibranch, dumbo-octopus, giant-tube-worm, saltwater-crocodile, walrus** —
  T1 answers are the signature feature or signature location of the animal.
  Solved by abstracting the feature (e.g., "a pair of flaps" instead of
  "ear-like fins", "deep ocean floor" instead of "hydrothermal vents").
- **the-great-migrations, the-oldest-animals-alive, extraordinary-hearts-and-blood,
  feeling-in-the-dark, antifreeze-blood** — adaptation-theme ladders where T1 answers
  are "which animal is the champion of X". Solved by abstracting the example
  (e.g., "Some seabirds fly nearly pole to pole" instead of "Arctic terns...").
- **two-ladder-shape adaptation topics** — the hardest to blurb without a leak are the
  adaptation-theme ladders because they are **by design** about multiple animals.
  Any example-list in the blurb risks naming an animal that is also a keyed answer in
  one of the rungs. For every one of these I audited the full rung set before deciding
  which examples to include.

## Files touched

- `data/question_contexts/animal.json` — 325 topic blurbs (new file; replaces the empty
  skeleton from Phase 2).

## Not touched (out of scope)

- `data/questions/animal.json` — questions themselves. Phase 4 (stem coherence sweep)
  handles those, if any need rewriting.
- `src/quiz_engine.py` — the loader was already shipped in Phase 2.
- Question-record migration to add `topic` keys to each question in `data/questions/animal.json`
  — unresolved (see Scope note). Without this, the blurbs are present but the game
  will not surface them until the question records point at them. Flagging for the
  Phase 3 coordinator.
