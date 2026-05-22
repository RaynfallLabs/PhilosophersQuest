# Animal Bank Question Templates (Source of Truth)

This document is the **recipe** every animal question is built from. `ANIMAL_FRAMEWORK.md` is the philosophy (the "why"); this document is the mechanics (the "how"). If a generated question doesn't match a pattern here, it isn't shipped.

The chain of authority:
1. The user's stance (in conversation + memory entries) — highest authority
2. `ANIMAL_FRAMEWORK.md` — long-form principles
3. **`ANIMAL_TEMPLATES.md` (this doc)** — concrete patterns generators must conform to
4. Generator scripts

Generators do not invent patterns. They instantiate patterns from this doc.

---

## 1. Core principles

- The bank teaches **fact + wonder**, not name-recall or definition lookup.
- Latin names belong in the **context field**, never as the test.
- Choices must be **parallel in shape** — if one is a single noun, all four are; if one is "Action — explanation," all four are.
- The stem must contain a **forcing constraint** that rules out 3 of 4 choices.
- The bank does NOT moralize at the player about meat-eating, hunting, animal husbandry, or other legitimate Western traditions. Substantive moral content at T4-T5 anchors the kid in the Roosevelt/Leopold/Aquinas stewardship tradition.
- Subject identifier stays `animal` for code stability.

## 2. The 8 topics

| Topic | What it teaches | Target weight |
|---|---|---|
| **Mammals** | Adaptations, behavior, big cats, ungulates, marine mammals | ~18% |
| **Birds & flight** | Migration, song, beak specialization, plumage, raptors | ~14% |
| **Reptiles & amphibians** | Cold-blooded wonders, venom, regeneration, metamorphosis | ~10% |
| **Fish & ocean life** | Deep sea, coral reefs, sharks, cephalopods, electric fish | ~12% |
| **Invertebrates** | Insects, spiders, mollusks, crustaceans — alien biology | ~16% |
| **Dinosaurs & extinct** | Mesozoic life, ice-age megafauna, transitional fossils | ~10% |
| **Ecosystems & ecology** | Biomes, food webs, trophic cascades, symbiosis | ~12% |
| **Human-animal relations** | Domestication, hunting tradition, conservation Western model, mythology, working animals | ~8% |

## 3. The 5 tiers — register progression

| Tier | Reading age | Voice | Scene material |
|---|---|---|---|
| **T1** | 10-11 (5th gr) | "Did you know?" wonder. Concrete, no Latin in stem. | Surprising senses, unusual hunting/defense, unexpected colors, beak/foot/skin specialization |
| **T2** | 11-12 (6th gr) | Short narrative + fact. "Predator", "prey", "habitat" OK. | Specific adaptations, mating displays, mimicry, defense mechanisms |
| **T3** | 12-13 (7th gr) | Wondrous observer + naturalist vocab ("niche", "biome", "trophic", "symbiosis") | Mutualism, trophic cascades, keystone species, convergent evolution, extremophiles |
| **T4** | 13-14 (8th gr) | Scientist-grade. "Selection pressure", "fitness", "exaptation" w/ inline def | Evolutionary mechanisms, conservation case studies, intro to stewardship tradition |
| **T5** | 14-16 (9-10th gr) | Naturalist + ethicist. Specialist OK w/ inline def. | Deep ecology, animal cognition, niche specialist facts, Western stewardship moral framework |

### Vocabulary policy

Specialist terms (phylogenetics, eusociality, exaptation, kin selection) can appear at T4-T5 with inline parenthetical or context-derived definition. Common biology vocab (predator, prey, niche, biome, trophic) becomes free at T2+. Latin / scientific names never appear in stems — context only.

## 4. Stem patterns by question shape

Each pattern below works across topics. Generators choose the right pattern for the cell's wonder hook.

### A. Wonder-fact recognition

Stem describes a bizarre real behavior, capability, or feature. Question asks which specific fact/number/species/explanation is true.

> *"A mantis shrimp's hammer-claw strikes prey faster than what?"*
> Choices: "A .22 bullet leaving the barrel" / "A peregrine in a stoop" / "A frog's tongue strike" / "Lightning across an open sky"

T-range: T1-T5. The most common pattern; the bank's spine.

### B. Common-knowledge flip

Stem assumes a common-knowledge fact, then asks the question the kid hasn't thought to ask.

> *"Zebras have black-and-white stripes. What color is their base coat under the stripes?"*
> Choices: "Black — the white is a pattern over dark skin" / "White — the black stripes are pigment" / "Brown — both stripe colors are overlay" / "Pink — the stripes are an optical effect"

T-range: T1-T3. Great hook; powerful pedagogy.

### C. Adaptation-why

Stem gives an animal in an environment with a specific trait. Question asks which selective pressure produced it.

> *"Why does the arctic fox grow a thick white winter coat and shed to a brown summer coat?"*
> Choices: camouflage tracking seasonal prey availability / thermoregulation only / mating display / metabolic-disease prevention

T-range: T2-T5. Teaches the environment→pressure→trait chain.

### D. Identify-by-trait

Stem gives a bundle of unusual traits. Question asks what species or group fits.

> *"It has three hearts, blue blood, eight arms, can solve mazes, and can change skin color to match a checkerboard floor. What is it?"*
> Choices: octopus / cuttlefish / mantis shrimp / chameleon

T-range: T1-T5. Forces the player to integrate facts.

### E. Ecosystem role / trophic cascade

Stem describes an ecosystem and a perturbation. Question asks what cascade follows.

> *"Wolves were removed from Yellowstone for 70 years. Elk populations rose without predation. Which downstream effect followed?"*
> Choices: aspen and willow regeneration declined as elk overgrazed / coyote populations collapsed without wolf scavenging / beaver dams expanded / grizzly diet shifted toward salmon

T-range: T3-T5. Trophic cascade / keystone species content.

### F. Comparative wonder

Two species both share a feature, but only one [distinguishing detail].

> *"Bats and dolphins both echolocate. Only one uses what specific mechanism for the click?"*
> Choices: melon organ focusing sound through fatty tissue / vocal cord vibration / vibration of the swim bladder / wing-membrane resonance

T-range: T2-T5. Teaches convergent evolution + species specificity.

### G. Behavioral why

Stem describes a strange behavior. Question asks the function or selective explanation.

> *"Why do octopuses sometimes punch fish that aren't even their prey?"*
> Choices: hunting cooperation gone wrong (the fish stole earlier) / pure aggression with no function / play behavior with no function / territorial display

T-range: T2-T5.

### H. Cultural / moral / historical (T4-T5 only)

Western stewardship tradition, conservation history, working-animal partnerships, mythology.

> *"Theodore Roosevelt's North American Model of Wildlife Conservation rests on what funding mechanism?"*
> Choices: excise tax on hunters' and anglers' equipment (Pittman-Robertson 1937 / Dingell-Johnson 1950) / general taxation / private donation only / international treaty

T-range: T4-T5. Substantive moral vision content (see ANIMAL_FRAMEWORK.md §6).

### I. Group / baby name (NON-obvious only)

A group / baby name question is acceptable ONLY when the name is non-obvious. Generators must check the answer is NOT in the toddler-banned list (see §7).

> *"A group of starlings flying in a coordinated dance through the evening sky is called what?"*
> Choices: murmuration / flock / swarm / congregation

T-range: T1-T3.

---

## 5. Choice structures by question type

The defining rule: **all four choices have the same shape**.

### 5.1 Fact-recognition / wonder-fact / identify-by-trait

Every choice is a short specific noun or noun phrase. No "X — explanation" structure.

- Correct: a real true thing
- Distractors: 3 plausible-wrong things (real other species / real other behaviors / real other numbers that don't fit)

### 5.2 Adaptation-why / behavioral-why

Every choice is a short explanation phrase. Parallel grammar.

- Correct: the actual selective explanation
- Distractors: other functions / no-function readings / wrong-function readings

### 5.3 Ecosystem / trophic cascade

Every choice is "[Cascade direction] — [specific outcome]" or simple cascade-statement.

- Correct: the documented downstream effect
- Distractors: plausible-but-wrong cascade variants

### 5.4 Comparative wonder

Every choice is "[Feature] — [details]" or simple feature-statement.

- Correct: the distinguishing feature
- Distractors: real features of other systems

### 5.5 Cultural / moral / historical

Every choice is "[Position name] — [claim]" parallel to philosophy's §5.6.

For moral-vision T4-T5 questions, use the same recognition-of-the-move pedagogy as philosophy: identify the framework, not declare verdicts. Western stewardship tradition is the substantive correct view where applicable.

---

## 6. Length envelopes

| Tier | Stem ≤ | Each choice ≤ | Context ≤ |
|---|---:|---:|---:|
| T1 | 200 | 90 | 200 |
| T2 | 240 | 110 | 240 |
| T3 | 280 | 130 | 300 |
| T4 | 320 | 160 | 360 |
| T5 | 360 | 180 | 420 |

**Length-parity rule**: longest/shortest choice ratio ≤ 1.30, max deviation ≤ 15%.

These are MAXIMUMS — median should sit at 60-70% of cap.

## 7. Anti-patterns (banned)

### 7.1 Stem anti-patterns

- *"What is a [obvious animal description] called?"* — toddler common-name lookup
- *"What does [biology term] mean?"* — vocabulary
- *"In what year did [species] go extinct?"* — pure date recall
- *"What is the Latin name for [common animal]?"* — naming trivia
- *"The [breed] is classified in which AKC group?"* — kennel-club categorization
- *"Cher Ami / Sergeant Stubby / Mister Ed was the animal of?"* — pure name-lookup. Use the story; make the conclusion the answer.
- *"Is it wrong to [legitimate human-animal practice]?"* — moralizing
- *"Just spot it"* / *"Which one is it?"* — kindergarten phrasing

### 7.2 Toddler-banned common names (specific list)

Group / baby names BANNED at any tier:

| Banned answer | Banned because |
|---|---|
| zebra | "Striped African horse" — toddler-obvious |
| giraffe | "Long-necked African mammal" — toddler-obvious |
| lion | "King of the jungle" — toddler-obvious |
| elephant | "Long-trunk African / Asian mammal" — toddler-obvious |
| kangaroo | "Pouched Australian hopper" — toddler-obvious |
| penguin | "Black-and-white Antarctic flightless bird" — toddler-obvious |
| pack (of wolves) | obvious |
| herd (of cattle/sheep/horses) | obvious |
| school (of fish) | obvious |
| flock (of birds, generic) | obvious — but *murmuration* of starlings, *parliament* of owls are FINE |
| swarm (of bees) | obvious |
| colony (of ants) | obvious |
| calf, kitten, puppy, foal, lamb, kid (goat), chick, duckling, gosling, piglet | obvious baby names |

Group / baby names ALLOWED (wonder material):

- *Murder* of crows, *unkindness* of ravens, *parliament* of owls, *exaltation* of larks, *murmuration* of starlings, *siege* of cranes
- *Embarrassment* of pandas, *prickle* of porcupines, *crash* of rhinos, *tower* of giraffes, *dazzle* of zebras
- *Bloom* / *smack* of jellyfish, *kaleidoscope* of butterflies, *cloud* of bats, *pod* of dolphins/whales (borderline — depends on tier)
- *Kit* (beaver, skunk, fox, ferret), *porcupette*, *joey* (kangaroo, koala, possum), *puggle* (echidna, platypus), *eyas* (hawk), *whelp* (seal), *fawn* (deer — borderline, kids may know)

### 7.3 Choice anti-patterns

- Only correct answer has the precise number / Latin name / date (citation skim-tell carried from philosophy)
- Distractors are obviously wrong ("a unicorn", "a magic frog") — banned. Distractors must be real animals or real biology.
- One choice is conspicuously longer
- Distractors with content not introduced in the stem

### 7.4 Context anti-patterns

- Naming an animal with no real anchor ("scientists say X" without source)
- Context shorter than 60 chars at T3+ (context teaches)
- Context that just repeats the answer
- Authoring metadata leaks (template section refs, pattern names, tier labels) — caught by `context_no_meta_references` gate

## 8. Structural gates

### 8.1 Deterministic + heuristic gates

Carried from philosophy where applicable, plus animal-specific additions:

| Gate | Check |
|---|---|
| **schema** | Required fields present, types correct |
| **length_budget** | Per-tier caps respected |
| **length_parity** | Max/min ratio ≤ 1.30, max dev ≤ 15% |
| **duplicate** | No exact stem duplicates |
| **choice_shape_parity** | All 4 choices share shape (all noun-phrase, all "X — Y", etc.) |
| **anti_pattern_clear** | No banned phrasings from §7.1 |
| **no_toddler_recall** | NEW — stem doesn't ask for an answer in the toddler-banned list |
| **wonder_bias_check** | NEW — T1-T3 stems must include behavior verb, adaptation, specific number, or non-obvious feature; pure noun-definition questions flagged |
| **forcing_constraint** | Stem includes detail that picks out one correct answer |
| **stem_pattern_match** | Stem matches one of the approved patterns in §4 |
| **register_consistency** | Vocab tier matches between stem and choices |
| **context_no_meta_references** | No template-section refs, pattern names, tier labels in context |

### 8.2 Judgment gates (Opus subagent)

| Gate | Check |
|---|---|
| **factual_accuracy** | The named species × trait × claim is actually true biology. Critical gate for this bank. |
| **distractor_coherence** | Each distractor's text matches its labeled concept (no "octopus — has fur") |
| **distractor_plausibility** | Each distractor is a real animal / real fact, not absurd ("a magic frog") |
| **single_defensible_answer** | Only one choice fits the scenario's forcing constraint |
| **wonder_present** | The question reveals something surprising/bizarre/wonderful, not a definition lookup |

## 9. Example bank (the "good looks like this" reference)

Per philosophy precedent, the repo will carry ~40 user-approved exemplars (1 per topic × tier cell). Generators consult these when picking phrasings. New samples must be visually consistent with the exemplars at their tier.

## 10. Workflow rule (sample-before-scale)

Every bulk-generation batch ≤ 50 questions stops here:

1. Generate N candidates per cell.
2. Pass them through all deterministic gates + the 5 judgment gates.
3. Show the user ~5 random samples per topic.
4. User: yes / no / "fix this specific thing."
5. If yes → commit, move to next batch.
6. If no → fix and re-sample.

**No batch is merged without user yes-on-samples.**

## 11. What this document does NOT do

- Doesn't promise subjective elegance — still human judgment.
- Doesn't replace ANIMAL_FRAMEWORK.md — mechanics on top of philosophy.
- Doesn't enforce wonder perfectly — wonder check is heuristic; final judgment is human.

What it DOES promise: structural failures (toddler-level questions, name-recall, animal-rights moralizing, mundane framings, factually wrong claims) become catchable BEFORE the bank touches user-visible play.
