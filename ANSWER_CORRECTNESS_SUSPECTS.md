# Answer-correctness suspects — v2.17.9

Adversarial audit of 500 randomly-sampled questions from the 10 non-grammar banks tested whether the labeled correct answer is factually correct given the stem.

**Sample:** 500 (50 / bank, seed 20260921). **Verdicts:** 493 sound, **7 suspect** (below).

These require manual review because fixing them changes the choices array (byte-identical rule broken). For each: read the stem, verify against sources, and choose one of:
- **Fix answer text** (rewrite the correct answer + maybe one distractor)
- **Swap** (a distractor is actually correct — promote it, demote the current answer)
- **Reject flag** (auditor was wrong; leave as is)

---

## economics #318 (T5) — wrong_attribution · confidence medium

**Auditor:** The four-word French tag 'Destruction n'est pas profit' is not a known Bastiat quotation and doesn't appear as the close of the broken-window section in 'Ce qu'on voit et ce qu'on ne voit pas' — the essay's broken-window section closes with a discussion of the shoes/repair trade-off, not a compressed four-word aphorism.

**Stem:** In 1850 the French economist Frederic Bastiat opened his essay 'That Which Is Seen and That Which Is Not Seen' with the story of a shopkeeper's son breaking a window. Bystanders comforted the shopkeeper by pointing out the glazier would now be paid — supposedly boosting the economy. Bastiat's broken-window section closes with a compressed four-word refutation, in French, of every later 'disaster-as-stimulus' claim. Which four words?

**Labeled answer:** "'Destruction n'est pas profit'"

**Choices:**
- 'Destruction n'est pas profit' ← labeled
- 'Luxe n'est pas richesse'
- 'Spoliation n'est pas industrie'
- 'Echange n'est pas vol'

---

## economics #1428 (T5) — wrong_attribution · confidence low

**Auditor:** Mises's canonical short label rejecting a stable middle path is 'middle-of-the-road' (Mittelweg) or 'third way'; 'a third system' isn't a recognized Misesian label.

**Stem:** By the 1930s Ludwig von Mises had argued for a decade that the mixed economy is unstable. It must either move back toward markets or forward to full state control. He used one short label to reject the idea that a real middle path exists at all. Which label?

**Labeled answer:** 'A third system'

**Choices:**
- A third system ← labeled
- A guided economy
- Managed capitalism
- The mixed economy

---

## economics #2333 (T4) — off_by_number · confidence medium

**Auditor:** US federal outlays fell from ~$92.7B (FY1945) to ~$55.2B (FY1946), about a 40% drop — 'slightly less than half' (a distractor) is right; the two-thirds figure only holds by FY1948.

**Stem:** The end of World War II is the biggest peacetime drop in federal spending ever recorded. About how much did federal spending fall from 1945 to 1946?

**Labeled answer:** 'By more than two-thirds'

**Choices:**
- By more than two-thirds ← labeled
- By about one quarter
- By about one tenth
- By slightly less than half

---

## history #5042 (T2) — wrong_attribution · confidence medium

**Auditor:** The famous annual 'whole town gathers to replaster' festival (Crepissage) is at the Great Mosque of Djenne, not Timbuktu's Djinguereber Mosque; Djinguereber is also mud-built and periodically maintained but lacks the iconic single-day town-wide festival described.

**Stem:** In the West African city of Timbuktu on the southern edge of the Sahara stands the Djinguereber Mosque, first built in 1327 — almost 700 years old. It is made of mud, straw, and palm wood, with no stone at all in the walls. Once a year, when the short rainy season ends, the whole town gathers around it and does one thing together, or the desert rains would slowly melt it back into the ground. What does the whole town do?

**Labeled answer:** 'replaster it by hand from top to bottom'

**Choices:**
- replaster it by hand from top to bottom ← labeled
- raise wooden roofs over its open courts
- dig new channels to carry the rain off
- hang woven mats along its outer walls

---

## ai #820 (T4) — wrong_attribution · confidence medium

**Auditor:** Hinton's post-Google interviews explicitly emphasized existential/extinction risk from superintelligent AI (10-20% chance within 30 years), not primarily near-term harms; the near-term-vs-extinction contrast with Yudkowsky is inaccurate — the actual difference is that Hinton shares extinction concerns but doesn't endorse 'shut it all down'

**Stem:** In May 2023, Geoffrey Hinton (one of the three 2018 Turing Award winners for deep learning) resigned from his decade-long role at Google. He gave interviews citing concerns about AI. How are his concerns different from Eliezer Yudkowsky's 'shut it all down' framing?

**Labeled answer:** "Hinton focuses on near-term harms like disinformation, job loss, and autonomous weapons rather than Yudkowsky's extinction framing."

**Choices:**
- Hinton focuses on near-term harms like disinformation, job loss, and autonomous weapons rather than Yudkowsky's extinction framing. ← labeled
- Hinton thinks AI poses no risk and only resigned due to a personal dispute with the search team at Google.
- Hinton wants to ban every neural network globally and replace AI with rule-based symbolic systems alone.
- Hinton and Yudkowsky hold identical views, and any reported difference is a media fabrication only.

---

## geography #2732 (T4) — wrong_answer · confidence medium

**Auditor:** Atlantis II Deep muds are standardly characterized as richest in zinc, copper, and silver (with lead and gold); cobalt is present only in trace amounts, not a headline metal — the labeled triple 'copper, cobalt, and zinc' substitutes cobalt for silver.

**Stem:** Two kilometers down in the Red Sea lies the Atlantis II Deep. Its water is about 68 C, and it is so salt-choked that nothing can live in it. Yet mining companies dream about it, because the mud there holds the richest known hoard of dissolved metals anywhere on the ocean floor, packed about a thousand times denser than in seawater. Which three valuable metals is it richest in?

**Labeled answer:** 'copper, cobalt, and zinc'

**Choices:**
- copper, cobalt, and zinc ← labeled
- gold, silver, and platinum
- iron, nickel, and lead
- tin, mercury, and manganese

---

## trivia #668 (T5) — wrong_answer · confidence medium

**Auditor:** The spooky storyteller (old sailor/ghost pirate) in Garfield's Halloween Adventure (1985) is voiced by C. Lindsay Workman, not Pat Carroll. C. Lindsay Workman is the distractor and is the actual correct answer; Pat Carroll (Ursula in The Little Mermaid) was not in this special.

**Stem:** The spooky storyteller in Garfield's Halloween Adventure from 1985 has been misnamed for years. Fans online often guess Orson Welles, Vincent Price, or Boris Karloff. Karloff died in 1969, so that guess is wrong. The real voice was a working actor with hundreds of small roles. Who was it?

**Labeled answer:** 'Pat Carroll'

**Choices:**
- Pat Carroll ← labeled
- C. Lindsay Workman
- John Carradine
- John Houseman

---
