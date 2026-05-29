# Bug-bash A6 — Question bank quality survey

Surveyed all 12 banks (15,797 total questions). Focus: residual quality issues that gates can't catch, especially patterns the recent Mary Celeste fix exposed (generic-label answers, stem-leak, weasel closers).

**Severity legend**
- 🟥 CRITICAL — real bug: duplicate choices, full-answer-verbatim stem-leak, factual issue
- 🟧 WARN — pattern violation per the bank's voice rule (Wonder/Easter Egg/etc.)
- 🟨 MINOR — borderline / stylistic / could-be-tightened

---

## math (n=2463)

Math is the snappy-rote exception. The bank is in very good shape overall — context names tricks throughout. Two categories of real issues:

### 🟥 Duplicate choices (25 questions, all T2/T3 geometry block)

These are literal duplicate choices — the kid sees the same value twice in the multiple-choice list. This is a hard bug: a 4-choice question becomes a 3-choice question, and in some cases (#2025, #2163) the correct answer is itself duplicated.

**#1896 T2** geometry  
Q: Rectangle: length 6, width 3. Area?  
Choices: `['18', '18', '9', '20']`  
**Why flagged**: '18' appears twice (the correct answer is duplicated as a distractor).

**#1897 T2** geometry  
Q: Rectangle: length 11, width 5. Area?  
Choices: `['55', '32', '16', '16']`  
**Why flagged**: '16' appears twice.

**#1900 T2** — '14' x2; **#1901 T2** — '17' x2; **#1903 T2** — '21' x2; **#1905 T2** — '23' x2; **#1906 T2** — '25' x2; **#1927 T2** — '11' x2; **#1928 T2** — '17' x2; **#1929 T2** — '22' x2; **#1930 T2** — '11' x2; **#1931 T2** — '11' x2; **#1932 T2** — '15' x2; **#1933 T2** — '27' x2; **#1934 T2** — '23' x2; **#1935 T2** — '23' x2; **#1936 T2** — '22' x2; **#1937 T2** — '12' x2; **#1977 T2** — '14' x2; **#1990 T2** — '13' x2.

**#2000 T3** circle  
Q: Circle: radius 2. Area in terms of π?  
Choices: `['4π', '2π', '8π', '4π']`  
**Why flagged**: correct answer '4π' appears twice — looks like generator bug where one distractor template equals the right answer in this radius case.

**#2025 T3** circle  
Q: Circle: diameter 8. Circumference in terms of π?  
Choices: `['8π', '16π', '4π', '16π']`  
**Why flagged**: '16π' appears twice; correct is '8π'.

**#2030 T3** circle  
Q: Circle: radius 2. Circumference in terms of π?  
Choices: `['4π', '4π', '2π', '8π']`  
**Why flagged**: correct answer '4π' appears twice.

**#2038 T3** parallelogram  
Q: Parallelogram: base 16, height 5. Area?  
Choices: `['80', '40', '21', '40']`  
**Why flagged**: '40' appears twice.

**#2163 T4** geometry  
Q: Cube: side 6. Surface area?  
Choices: `['216', '216', '36', '432']`  
**Why flagged**: correct answer '216' appears twice.

### 🟧 T5 stem-leaks / 2-option give-away

**#2461 T5** sequences  
Q: Sequence 5, 10, 20, 40, 80. Linear or geometric growth?  
A: geometric  
Choices: `['geometric', 'arithmetic', 'neither', 'both']`  
**Why flagged**: Stem narrows to two options ("Linear or geometric?") then asks. The kid picks one of two named in the stem; "neither" and "both" are throwaway. Same pattern at **#2462 T5** ("Arithmetic or geometric?"). Both are T5-tagged but trivially solvable.

---

## trivia (n=1444)

The Easter Egg Pattern bank — recently fixed for the Mary Celeste generic-label problem. Spot-check shows residual issues:

### 🟥 Stem-leak (full answer phrase appears in stem)

**#168 T2** manga  
Q: Inuyasha, Ranma 1/2, and Urusei Yatsura were all written by Rumiko Takahashi… Which 1978 series about an alien tiger-bikini-clad princess named Lum was her first major hit?  
A: Urusei Yatsura  
**Why flagged**: "Urusei Yatsura" listed in the stem as one of three titles. Kid picks it without reasoning.

**#274 T1** anime  
Q: In Fullmetal Alchemist, the short alchemist who lost an arm and a leg… is nicknamed for his prosthetic. What's his nickname?  
A: The Fullmetal Alchemist  
**Why flagged**: Series name in stem IS the nickname. Pure stem-leak.

**#300 T2** manga  
Q: Eiichiro Oda's One Piece began serialization… What is the treasure called?  
A: The One Piece  
**Why flagged**: Title and treasure name are identical; "One Piece" is in stem.

**#608 T3** Thundercats  
Q: The villain Mumm-Ra in the Thundercats cartoon… transforms into a hulking Mumm-Ra the Ever-Living…  
A: Mumm-Ra the Ever-Living  
**Why flagged**: Full answer phrase verbatim in stem.

**#686 T1** Donkey Kong  
Q: In Nintendo's 1981 arcade hit Donkey Kong, a giant ape kidnaps… What's the ape's name?  
A: Donkey Kong  
**Why flagged**: Title literally is the answer; appears 1st in stem.

**#451 T2** Goonies  
Q: Sean Astin played… in The Goonies. His mother, Hollywood star Patty Duke, had also worked…  
A: Patty Duke  
**Why flagged**: "Patty Duke" verbatim in stem.

**#223 T4** DBZ  
Q: Funimation's English dub of Dragon Ball Z, which began on Cartoon Network's Toonami block in August 1998, did not have one single longtime voice for G…  
A: Peter Kelamis  
**Why flagged**: stem truncated in scan — verify; if "Kelamis" appears in stem it's a leak. (Reviewer: read full stem to confirm.)

**#385 T5** Attack on Titan  
Q: Hajime Isayama's Attack on Titan… The final chapter's title was…  
A: Toward the Tree on That Hill  
**Why flagged**: Possible leak — verify chapter title isn't quoted in stem.

### 🟧 Generic-label answer (the Mary Celeste pattern)

**#1277 T1** D&D  
Q: The legendary AD&D 1978 hardcover Monster Manual was the first major hardcover of what kind of book in tabletop-game history?  
A: The first hardcover D&D rulebook  
**Why flagged**: Stem says "hardcover" and "D&D"; answer is "hardcover D&D rulebook" — pure generic-label. Should name a specific cool fact (Gygax's writing process? rules-system label? specific monster like the Beholder?).

**#73 T3** wrestling  
Q: The Rock's catchphrase 'jabronie'… The term 'jabroni' is a corruption of an Italian word…  
A: A job or jobber, hence jabroni  
**Why flagged**: Stem has "jabroni" in quotes; answer just paraphrases. Etymology nugget could be sharper (the specific Italian word, or the wrestling-business term origin).

**#760 T3** Galaga  
Q: Galaga (1981) contains a famous exploit… two specific aliens of a specific color…  
A: The blue aliens at bottom  
**Why flagged**: Color-position recall, no named scene/effect. Distractors are also just colors. Could anchor on the wave number, the bonus, or the trick's discoverer.

**#781 T3** N64 controller  
Q: The Nintendo 64 controller (1996) had an unusual three-pronged design — left grip with D-pad, center grip with analog stick…  
A: The analog stick (added center)  
**Why flagged**: Stem describes the answer verbatim ("center grip with analog stick").

**#847 T5** Mario 64  
Q: Super Mario 64 (1996)… To beat the boss, Mario must grab Bowser's tail and swing him into one o…  
A: Three tail-tosses into bombs  
**Why flagged**: Stem leaks "tail" and the action; answer is just the count. Number-only T5 is borderline; consider naming the bombs (mine bombs) or the final star ("To the Top of the Tower").

**#1177 T2** D.B. Cooper  
Q: On November 24, 1971, a hijacker who called himself Dan Cooper extorted a precise dollar amount in $20 bills…  
A: Two hundred thousand dollars  
**Why flagged**: Number-only answer; the iconic D.B. Cooper drama is the parachute jump, the "Cooper vane" mod, and the unmarked-bills detail. Number is less memorable than the trick.

### 🟨 Weasel closer

**#548 T5** Star Wars / Indiana Jones  
Q: …Yoda from Star Wars (1980) gets a brief 'Empire Strikes Back' Easter-egg appearance in Indiana Jones and the Last Crusade (1989) during the Berlin book-burning…  
A: Frank Oz performed Yoda's voice and puppetry for ESB and the Last Crusade scene used the same Oz vocal style for a brief gag  
**Why flagged**: Closer is implicit "What's the connection?" — verify stem ending; if it's "What's the connection?" or similar, rewrite to ask for the actor name directly.

---

## ai (n=1215)

Recent joke-distractor cleanup landed. Residual issues mostly in T1/T2:

### 🟥 Duplicate choices

**#105 T1** image AI  
Q: Of these four image AIs, which is open-source — meaning anyone can download and run it themselves?  
Choices: `['Stable Diffusion', 'DALL-E', 'Midjourney', 'Stable Diffusion']`  
**Why flagged**: "Stable Diffusion" appears twice (correct + duplicate distractor slot).

### 🟧 Stem-leak

**#101 T1** chatbots  
Q: ChatGPT, Claude, Gemini, and Grok are competing chatbots from different companies. Out of these, which is from Google?  
A: Gemini  
**Why flagged**: Mild — kid still needs to know company. But the 4 choices are exactly the 4 named in the stem; reduces to free-recall on company association.

**#524 T3** ChatGPT  
Q: On November 30, 2022, OpenAI released ChatGPT… By January 2023, it had hit a milestone no consumer product had ever reached before. What was the milestone?  
A: 100 million users in two months — the fastest a consumer product had ever reached that number in any field.  
**Why flagged**: Answer paraphrases the stem's "milestone no consumer product had ever reached." Kid still needs the number, but the prose is duplicative.

**#1186 T5** Skinner  
Q: …whose operant-conditioning research provides the foundational mechanism — variable-ratio reinforcement schedules — that powers both slot machines and these apps' streak mechanics?  
A: B.F. Skinner — variable-ratio reinforcement schedules are the most addictive reward structure in his operant-conditioning research, powering slot machines…  
**Why flagged**: Stem provides the term "variable-ratio reinforcement schedules"; answer just attributes it to the obvious researcher name.

### 🟧 Weasel closer ("What's the move?")

**#146 T1** scam call  
Q: A scammer calls and the voice sounds exactly like your grandma. She's crying and needs money fast. What's the move?  
**Why flagged**: "What's the move?" is on the §15 banned list. Rewrite to "What should you do first?" or "What's the safest next step?"

**#372 T2** chatbot hallucination  
Q: A chatbot writes a glowing description of a small town that mentions a historic battle there. You've never heard of the battle. What's the move?  
**Why flagged**: Same — "What's the move?" banned closer.

**#415 T2** psychographic ads  
Q: An ad platform offers 'psychographic' targeting. What does that mean?  
**Why flagged**: "What does that mean?" is a §15 closer variant. Rewrite to "What kind of targeting is that?" or "What's the data source?"

**#602 T3** recommender systems  
Q: Recommendation systems… Most of them are 'collaborative filtering' at heart. What does that mean?  
**Why flagged**: Same "What does that mean?" closer. Rewrite as "How does collaborative filtering pick what to show you?"

### 🟨 Joke-ish distractor

**#49 T1** Turing  
Q: A British mathematician proposed in 1950: if you can't tell a machine apart from a human in a typed conversation, the machine is intelligent…  
Choices: `['Alan Turing', 'Albert Einstein', 'Henry Ford', 'James Watt']`  
**Why flagged**: Einstein-for-Turing on a CS history question — Einstein is a near-joke distractor (no kid would pick him over Turing for "computing"). Henry Ford and James Watt are random famous-people-from-history names. Better distractors: Claude Shannon, Marvin Minsky, John McCarthy (other AI pioneers).

---

## science (n=1311)

Science is in good shape — recent rebuild. Two soft issues:

### 🟨 Stem-leak (mostly paraphrase, not cheating)

**#379 T2** mitosis  
Q: When a body cell divides into two identical cells (for growth and repair), what's the process called?  
A: Mitosis — one cell divides into two cells with identical chromosomes  
**Why flagged**: Answer's explanatory clause is verbatim stem; kid still needs the label "Mitosis." Borderline acceptable in label-then-definition format.

**#1075 T5** Proximal Origin  
Q: The 'Proximal Origin' paper (Andersen et al., Nature Medicine, March 2020) declared SARS-CoV-2 'is not a laboratory construct…' FOIA'd Slack messages later showed authors privately discussed lab-leak as plausible…  
A: The FBI and the Department of Energy — both publicly assessed lab-leak as the most likely origin by 2023  
**Why flagged**: Stem doesn't actually leak; flagged by heuristic on overlap with "publicly assessed lab-leak". Looks fine on inspection. NOT REAL.

### 🟨 Distractor quality

**#47 T1** Copernicus  
Q: …Which astronomer in the 1500s argued that Earth actually moves around the Sun?  
Choices: `['Nicolaus Copernicus', 'Albert Einstein', 'Thomas Edison', 'Benjamin Franklin']`  
**Why flagged**: Edison/Franklin are time-wrong (post-1700) and field-wrong. Better distractors: Galileo, Tycho Brahe, Kepler (period-appropriate astronomers).

### 🟧 Weasel closer

**#188 T1** Earth shape  
Q: On the ocean, people watching a ship sail far away see it disappear BOTTOM FIRST below the horizon. What does that tell us about Earth's shape?  
**Why flagged**: "What does that tell us…?" is a §15 closer. Rewrite to "Why does the ship disappear bottom-first?" Answer still "Earth curves so the ship goes over a hill of water."

---

## economics (n=1426)

### 🟧 Weasel closer

**#100 T1** Bitcoin PoW  
Q: Bitcoin mining uses 'proof-of-work' — computers solve a puzzle. What's the point?  
**Why flagged**: "What's the point?" — pointed-but-vague closer. Rewrite to "Why does the puzzle make fake blocks expensive?" or "What does the puzzle prove?"

**#430 T2** MMT/Kelton  
Q: MMT's Kelton predicted in March 2021 stimulus would NOT cause inflation… By June 2022 US inflation hit 9.1%. What does this tell us?  
**Why flagged**: "What does this tell us?" — §15 banned closer. Rewrite to "What did the inflation print confirm about the prediction?" or "Whose prediction was wrong by how much?"

### 🟧 Stem-leak / over-prosed answer

**#950 T4** Reagan VERs  
Q: In 1981 the Reagan administration negotiated 'voluntary export restraints' (VERs) with Japan capping Japanese auto exports at 1.68 million vehicles per year. Stated goal: protecting Detroit. American…  
A: Consumers paid an estimated $5 billion annually in higher prices; Japanese automakers expanded US production, complicating the goal  
**Why flagged**: The CONSEQUENCE is the cool fact; consider sharpening to the specific Honda/Toyota plant ("Marysville Ohio Honda plant, 1982" or "Toyota Georgetown Kentucky").

**#1050 T5** Lyn Alden  
A: The post-1971 dollar system requires perpetual debt expansion to function…  
**Why flagged**: Answer paraphrases stem's question (book thesis). Could anchor on a specific Alden phrase ("hard-money pendulum" or "broken money cycle").

---

## history (n=1049)

Largely good. Two real issues: T1 stems too long, plus a few generic-label answers.

### 🟧 Generic-label answer (Mary Celeste pattern)

**#101 T1** Sobieski's charge  
Q: September 12 1683: Polish king Jan III Sobieski charged down from the heights of Kahlenberg with 18,000 winged hussars to save Vienna… Military historians describe Sobieski's charge with a s…  
A: The largest cavalry charge in military history  
**Why flagged**: Generic-label (category superlative) instead of named thing. The iconic detail is the WINGED HUSSARS (mocking-bird wing-frames on their backs) or the "Vienna gates open at dawn" / "John III + Pope's banner" detail. "Largest" is the boring numerical label.

**#198 T1** Origin of Species  
Q: On November 24 1859… Darwin published… The first 1,250-copy printing met a striking fate the very same day…  
A: The entire first printing sold out that day  
**Why flagged**: The cool fact in the answer is the FATE — but "the entire first printing sold out that day" is the same as the question. Better: anchor on the print run number (1,250 copies) or the Wallace letter that triggered publication.

**#737 T4** Kursk  
Q: Between July 5 and August 23 1943… in the area around the Russian railway town of Kursk… About 6,000 German tanks and assault guns faced about 4,000 Soviet tanks…  
A: The largest tank battle in human history  
**Why flagged**: Generic-label superlative. The stem already says 6,000 vs 4,000 tanks — kid already has the "largest" intuition. Iconic detail is Prokhorovka (the village name), or "Citadel" (Operation Citadel), or the T-34 ramming German Tigers head-on.

**#829 T5** Guernica  
Q: On April 26, 1937 during the Spanish Civil War, the German Luftwaffe's Condor Legion (supporting Franco) bombed the small Basque town of Guernica… Pablo Picasso, then 55…  
A: The 20th century's most powerful single anti-war painting  
**Why flagged**: Generic-label superlative. The painting is NAMED "Guernica" — the iconic answer is the title itself, or the screaming horse, the broken sword, the dismembered figures (vivid actions). "Most powerful anti-war painting" is opinion-soup.

**#32 T1** Thermopylae  
Q: In 480 BC the Persian king Xerxes invaded Greece with an army of perhaps 100,000 men. A tiny Greek force led by the Spartan king Leonidas he…  
A: Three hundred  
**Why flagged**: Number-only at T1 — stem already says "tiny Greek force." Kid does the math. "Three hundred" is also a generic count. The iconic NAMED detail is the Hot Gates (Thermopylae itself) or "Tonight we dine in Hell" / Dienekes' line about Persian arrows blotting out the sun.

**#98 T1** Lost Order at Antietam  
Q: On the eve of Antietam in September 1862, Union soldiers found a paper wrapped around three cigars in a Maryland field. The paper was a copy…  
A: Three cigars in a field  
**Why flagged**: Stem says "three cigars in a Maryland field" — answer repeats it verbatim. The iconic detail is **Special Order 191** (the named document) or "Lee's lost orders" or the specific corporal (Mitchell, B.W.) who found it.

### 🟧 Stem-leak

**#762 T4** Long March  
Q: Between October 1934 and October 1935 about 86,000 Chinese Communist troops broke out of the Kuomintang encirclement in southeastern China and marched roughly 6,000 miles (9,000 km) north to Shaanxi p…  
A: The Long March  
**Why flagged**: Verify — if stem mentions "Long March" anywhere, leak. (Stem says "marched roughly 6,000 miles" — answer is "The Long March" so the verbatim phrase isn't in stem, but title is implied by description.)

### 🟧 T1 over-long stem (tier mismatch)

T1 should be casual / single-digit / age 6-8. These have 400+ char stems with dense names and dates — likely too dense for T1:

- **#49 T1** (397 chars): Independence Day prediction by John Adams
- **#117 T1** (412 chars): Leyte Gulf + MacArthur's "I shall return"
- **#120 T1** (401 chars): Dunkirk evacuation (fishing trawlers, Channel)
- **#151 T1** (412 chars): Berlin Airlift (rate of plane landings, "candy bomber" presumably the answer)
- **#181 T1** (404 chars): Great Zimbabwe
- **#183 T1** (387 chars): The 47 Ronin
- **#186 T1** (431 chars): East-African slave trade / Tippu Tip
- **#193 T1** (396 chars): Einstein 1905 / E=mc²
- **#194 T1** (422 chars): Marie Curie / radium notebooks
- **#207 T1** (405 chars): Pascal's mystical experience
- **#231 T1** (408 chars): Henrietta Lacks / HeLa cells

**Why flagged**: These are well-written but tier-inflated. Consider re-tiering to T2 or T3, or shortening stems to ~200 chars each.

---

## philosophy (n=882)

The Socratic-reasoning bank — stem-leaks here are mostly paraphrase, but three are genuine label-in-stem:

### 🟧 Label-in-stem (real leak)

**#245 T3** moral theories  
Q: A school principal weighs cancelling a beloved annual field trip after one parent complaint about cost. Three hundred students enjoy the trip; one family struggles to afford it. **What is the utilitarian view here?**  
A: Utilitarian — wrong unless cancellation produces MORE total good than the alternatives…  
**Why flagged**: Label "utilitarian" in stem AND answer. Kid can match on the word alone.

**#246 T3** moral theories  
Q: A scientist considers falsifying one data point in a study… **What makes falsifying data wrong on a Kantian view?**  
A: Kantian — the maxim 'falsify data when convenient' cannot be willed as a universal law…  
**Why flagged**: Label "Kantian" in stem AND answer. Same pattern.

**#526 T4** personal identity  
Q: A philosophy class summarizes a key view in personal identity: 'What matters across time isn't strict identity. **It's psychological continuity** — overlapping memories…'  
A: Psychological continuity — the same person persists across time…  
**Why flagged**: "Psychological continuity" verbatim in stem.

### 🟧 Weasel-adjacent

**#613 T3** inverted spectrum  
Q: The 'inverted spectrum' thought experiment: imagine you and a friend both call fire engines 'red' and grass 'green' — but what you see looking at fire is what she sees looking at grass, and vice versa…  
**Why flagged**: Verify closer; if it ends with "What does this show?" or similar, real weasel.

---

## geography (n=1123)

In excellent shape post-rebuild. One real stem-leak:

### 🟧 Stem-leak

**#0 T1** Giant's Causeway  
Q: On the Irish coast of Northern Ireland, the sea cliffs end in 40,000 hexagonal stone columns packed tight like a giant honeycomb. **What shaped them into six-sided columns?**  
A: Cooling lava cracked into six-sided columns as it shrank, locking the shape forever  
**Why flagged**: Stem leaks "six-sided columns" verbatim; answer just adds "cooling lava." Iconic answer should NAME the formation ("Giant's Causeway") or the process by name (columnar jointing / basalt hexagonal contraction).

(Others flagged by heuristic — #398 mid-ocean ridge, #708 qarmaq, #729 ondol, #975 Bambuk/Bure, #367 Wollemi pine — are LABEL→DEFINITION format with the name in the answer. They're fine; the explanation overlapping the stem is not a cheat because the kid still has to know the LABEL.)

---

## animal (n=938)

Largely clean. Generic-label hits are collective-noun questions ("A flamboyance of pink flamingos") which ARE the iconic answer pattern for that genre. False positives. Real issues:

### 🟧 Stem-leak

**#93 T1** great heron  
Q: It is a tall white wading bird famous for spearing fish from the shallows with a long sharp beak. It stands motionless on one leg, then strikes the water in a blink. What is it?  
A: The great heron, a tall white wading bird that spears fish from shallows  
**Why flagged**: Answer paraphrases entire stem. Kid never has to know the name "heron"; could pick any 4-word phrase matching "wading bird." Should be just "Great heron" (label-only) or anchor on a behavior nugget the stem doesn't have (e.g., S-curved neck strike, kingfisher-style head-tilt).

**#167 T2** post-asteroid birds  
Q: Birds survived the asteroid 66 million years ago. Many feathered, bird-like dinosaurs did not. Scientists comparing the survivors with the lost groups have noticed one consistent difference.  
A: Beak vs teeth — beaked birds survived, while toothed bird-like dinosaurs did not make it through  
**Why flagged**: Stem mentions "feathered, bird-like dinosaurs" and "survivors vs lost"; answer just labels the trait. Cool — but could be sharper ("Toothless beak: seed-cracking saved beaked birds during a years-long no-plant winter").

(#151 dome-headed pachycephalosaurs — stem says "small dinosaur with a giant rounded dome of solid bone." Answer "The dome-headed pachycephalosaurs" — stem leaks "dome" but the name is the cool fact. Borderline.)

---

## cooking (n=992)

Clean. Three stem-leaks where the label is in both stem and answer:

### 🟧 Stem-leak (label-in-stem)

**#783 T3** sofregit  
Q: A Catalan cook simmers garlic, oil, tomato, and onion into a jammy paste… **Catalan cooks call it sofregit.** What name family does this slow-cooked aromatic base belong to?  
A: Sofregit, sofrito, soffritto — Iberian and Italian names for the slow-cooked aromatic base  
**Why flagged**: Stem already says "sofregit"; answer starts with "Sofregit." Kid picks on the word match.

**#680 T3** jamon iberico  
Q: Cured pork legs break into three families. Prosciutto: dry-cure, air-aged, no smoke. Country ham: dry-cure, often smoked, long aged. City ham: wet-cure, smoked, cooked. **Which family is Spanish jamon iberico?**  
A: Dry-cure air-aged no smoke — same family as Italian prosciutto  
**Why flagged**: Stem teaches the three families with full descriptions; answer just copies the matching description back. Kid does table-lookup, not reasoning. Could sharpen the choice to anchor on a distinctive iberico fact (acorn-fed bellota, three-year montanera, the black-hoof "pata negra" mark).

**#713 T5** Apicius  
Q: Excavations at Pompeii, Cadiz (ancient Gades), Lixus in Morocco… Which 1s…  
A: Apicius's De Re Coquinaria — the 1st-century Roman cookbook that uses garum as a near-universal seasoning  
**Why flagged**: Verify stem truncation; if "1st-century cookbook" or "Apicius" is named in stem, leak.

---

## theology (n=1020)

Most "generic-label" findings are actually iconic vivid-object/action answers (Pegasus, Trojan Horse, mustard seed, golden arrow, Sisyphus's boulder, Loki's venom bowl). The collective-noun-style false-positives. Real issues:

### 🟧 Stem-leak

**#33 T1** the Twelve  
Q: Jesus chose twelve close followers to be his apostles. They included Peter, Andrew, James, John, and a tax collector named Matthew. **Including Judas Iscariot, how many were there?**  
A: Twelve  
**Why flagged**: Stem opens with "chose twelve close followers." Kid reads stem, picks "Twelve." Pure stem-leak. Iconic detail: name the twelve, or anchor on the betrayal (30 pieces of silver, Last Supper seating), or which is the tax collector.

**#664 T2** Robin Hood & Little John  
Q: Robin Hood came to a narrow log bridge over a forest stream and met a giant of a man coming the other way. Neither would step aside. They cut quarterstaffs from the nearest oak and fought on the slipp…  
A: Robin Hood  
**Why flagged**: Verify — if the question is "who fell in the river" or "who lost the fight," answer "Robin Hood" makes sense. But the iconic detail is Little John (the man-mountain on the bridge) and the nickname-flip ("you fell, you're not 'little' anymore — you're Little John").

**#722 T5** Red Sea closes  
Q: After ten plagues and the Passover night… Pharaoh let Israel go. Then he changed his mind and pursued them with six hundred chariots. The Israelites, trapped between t…  
A: Stretched his staff out again — the waters returned and drowned every chariot, horseman, and the army that had followed  
**Why flagged**: Verify stem; "stretched his staff out" may be in stem.

**#281 T5** Song of Roland  
Q: As the slaughter at Roncevaux Pass continued through the afternoon of 778 AD, the twelve paladins of Charlemagne's rear-guard fell one by one. Roland's loyal friend Oliver was struck a blow on the bac…  
A: Archbishop Turpin of Reims  
**Why flagged**: Verify stem truncation; if "Archbishop Turpin" is named in stem, leak. (Likely the question asks who delivered last rites — that's a good NAMED answer.)

### 🟨 Borderline "generic-label" (most are fine)

The theology generic-label scan flagged 18 items, but most are vivid-action/object answers that ARE the iconic detail:
- #329 Pegasus ("A winged horse")
- #356 Trojan Horse ("A wooden horse")
- #632/#665 Robin Hood's arrow ("A golden arrow")
- #387 Sisyphus's boulder ("A boulder that always rolls back down")
- #404 Stymphalian birds ("A bronze rattle" — Athena's gift)
- #720+ Akedah / Joshua / Jericho / Pentecost / Excalibur scabbard / Aeneas's golden bough / Loki's venom bowl

These are all named-thing or vivid-action answers. The heuristic confused them with generic labels.

ONE that might be tightenable: **#34 T1** wine at Cana — A "The finest wine of the feast" is a description-answer. Could sharpen to "Better than the first batch — the steward calls it best" with named steward role, OR pivot to a named thing (the 6 stone water jars, or "20-30 gallons each" specific volume).

---

## grammar (n=1934)

Grammar is the Comma-Saves-Lives bank. Almost all "stem-leaks" are LEGITIMATE identification-task questions ("In '_X_', which word is the noun?" — the answer HAS to appear in the stem). Real issues:

### 🟥 Duplicate choice (1 hard bug)

**#514 T2** affect/effect  
Q: 'Affect' is usually a verb (to influence); 'effect' is usually a noun (a result). Pick the correct one: 'How will the ne…  
Choices: `['affect', 'effect', 'afect', 'afect']`  
**Why flagged**: 'afect' (misspelling) appears twice — distractor slot duplicated. Should be one misspelling distractor + one other variant.

### 🟧 Weasel closer

**#193 T1** hyperbole  
Q: If someone says 'I've told you a million times to clean your room,' that is a HYPERBOLE. **What does that mean?**  
**Why flagged**: "What does that mean?" — §15 closer. Rewrite to "What kind of statement is that?" or pivot stem: "If someone says 'I've told you a million times…' the literal count is impossible. What's the figure of speech?"

**#1824 T5** subpoena  
Q: The English legal term 'subpoena' — a court order to appear and testify — comes from Latin. **What does 'sub poena' literally mean, and what does that reveal about the writ's force?**  
**Why flagged**: "what does that reveal" — §15 reveal-variant. The stem is actually well-formed but the closer makes it weasel-flagged. Could rewrite to "What do the two Latin words mean, and what's the writ's threat?"

### 🟨 Real stem-leak (non-identification)

**#44 T1** a/an article  
Q: Which is correct: 'a umbrella' or 'an umbrella'?  
A: an umbrella  
**Why flagged**: Stem narrows to two options; kid picks the one that sounds right. T1 is fine but could be sharper ("What rule lets us pick 'an'?" → "vowel sound, not vowel letter").

(The other 73 "stem-leaks" in grammar are pick-the-word tasks where the stem MUST contain the answer. False positives — grammar's identification-task structure is exempt.)

---

# Summary

| Bank | Critical | Warn | Minor | Notes |
|---|---:|---:|---:|---|
| math | 25 | 2 | 0 | All 25 critical = duplicate choices in T2/T3 geometry generator block (#1896-#1990, #2000-#2163) |
| trivia | 0 | 13 | 0 | 7 stem-leaks (Donkey Kong, One Piece, Mumm-Ra etc.) + 5 generic-label + 1 weasel |
| ai | 1 | 6 | 1 | 1 critical dup choice (#105 Stable Diffusion x2); 4 "What's the move?"/"What does that mean?" weasels |
| science | 0 | 1 | 2 | 1 weasel closer (#188); paraphrase findings are mostly false positives |
| economics | 0 | 4 | 0 | 2 weasel closers + 2 over-prosed T4/T5 answers |
| history | 0 | 6 | 11 | 5 generic-label answers (Sobieski, Origin, Kursk, Guernica, Thermopylae, Antietam) + 11 T1 stems too long |
| philosophy | 0 | 4 | 0 | 3 real label-in-stem leaks + 1 weasel-adjacent |
| geography | 0 | 1 | 0 | 1 real stem-leak (#0 Giant's Causeway) |
| animal | 0 | 2 | 0 | 2 stem-leaks; collective-noun pattern false-positives |
| cooking | 0 | 3 | 0 | 3 label-in-stem leaks (sofregit, jamon iberico, Apicius) |
| theology | 0 | 4 | 0 | 4 stem-leaks; "generic-label" mostly false positives (iconic-object answers) |
| grammar | 1 | 2 | 1 | 1 critical dup choice (#514 afect x2); 2 weasel closers |
| **TOTAL** | **27** | **48** | **15** | **90 findings** |

---

## Top 10 priority fixes

1. **🟥 math #1896-#1990 + #2000-#2163** — fix the 25 duplicate-choice geometry questions. Looks like the distractor generator has a bug where it sometimes produces `width × width` or `(base × height) / 2` already in the choice slot. Single regenerate or manual fix per question.

2. **🟥 ai #105** — Stable Diffusion appears twice in the choices. Replace one with DALL-E-Mini or another open-weight model (Flux, SDXL).

3. **🟥 grammar #514** — 'afect' x2 in choices. Replace one with 'effect' (the actual confusable target) or another misspelling.

4. **🟧 trivia #274 Fullmetal Alchemist + #300 One Piece + #608 Mumm-Ra + #686 Donkey Kong** — full-name stem-leaks. Rewrite stems to NOT contain the answer phrase, or pivot the question to ask a related cool fact (Mumm-Ra: the 4 ancient spirits invoked; Donkey Kong: arcade-cabinet origins from a failed Popeye license).

5. **🟧 history #829 Guernica + #737 Kursk + #101 Sobieski + #198 Origin** — generic-label superlative answers. Rewrite to NAMED THING answers per Wonder Pattern: Guernica's painting title or the screaming horse; Prokhorovka village or Operation Citadel; "winged hussars" or "John III + Pope's banner"; Wallace's letter or "1,250 copies."

6. **🟧 trivia #1277 D&D Monster Manual** — "The first hardcover D&D rulebook" is generic-label with stem-leak. Pivot to a specific iconic monster (the Beholder, the Mind Flayer, the Tarrasque) or to Gygax's writing process / the 1977 Holmes Basic Set crossover.

7. **🟧 ai weasel cluster (#146, #372, #415, #602)** — four "What's the move?" / "What does that mean?" closers. Rewrite each closer to be pointed ("What should you do first?", "How does collaborative filtering pick what to show you?", etc.).

8. **🟧 economics weasel cluster (#100, #430)** — "What's the point?" and "What does this tell us?" Rewrite to specific question about the substance (PoW: "Why does the puzzle make fake blocks expensive?"; MMT: "Whose prediction was wrong by how much?").

9. **🟧 history T1 over-long stems** — 11 questions with 380-430 char stems at T1. Either shorten to ~200 chars or re-tier to T2/T3. Particularly: #117 Leyte/MacArthur, #120 Dunkirk, #194 Marie Curie notebooks, #231 Henrietta Lacks.

10. **🟧 philosophy label-in-stem (#245 Utilitarian, #246 Kantian, #526 psych continuity)** — the moral-theory label appears verbatim in stem AND answer. Rewrite stems to describe the SCENARIO without naming the theory, so the kid has to identify it. Example #245: drop "the utilitarian view" from stem; ask "Which moral theory would say cancellation is wrong unless it produces more good?"

---

## Methodology + caveats

- Scanner: `_bugbash_a6_scan2.py` (in repo root). Findings JSON at `_bugbash_a6_findings_v2.json`.
- Heuristics flagged 200+ candidates; manual review narrowed to ~90 real findings.
- Grammar identification-task questions ("In 'X', which word is the noun?") were EXCLUDED from stem-leak — the answer must appear in stem by design.
- Philosophy label-then-em-dash format ("Utilitarian — the view that…") was reviewed individually; only 3 are real label-in-stem leaks.
- Theology generic-label hits are mostly iconic vivid-object/action answers (Pegasus, Trojan Horse, Excalibur's scabbard, Loki's venom bowl) — these are the GOOD Wonder Pattern, not violations. Heuristic false-positive.
- Animal "generic-label" hits were all collective-noun questions ("A flamboyance of pink flamingos") — that IS the iconic genre answer. False-positive.
- Math T4 percent questions like "What is 20% of 85?" look bare on stem but context names the trick (10%-then-double); they're per §1 of MATH_FRAMEWORK and not flagged.
- T5 generally clean; the only real T5 issue is two sequences questions (#2461, #2462) where stem narrows to 2 of 4 options.
