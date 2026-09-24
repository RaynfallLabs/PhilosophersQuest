# Answer-correctness suspects — full-coverage pass

Adversarial audit of every question in the 10 non-grammar banks (plus the initial 500-sample).

**Sound so far:** 18703 · **Suspect:** 72 · **Unique suspects:** 72
**Total audited:** 18775

Each suspect requires manual verification: fix the answer text (touches choices), swap answer↔distractor, or reject the flag.

---

## ai (4 suspects)

### ai #542 (T3) — wrong_answer · medium

**Auditor:** Answer says Hinton's concerns are near-term ONLY, 'not' Yudkowsky's 'AI wipes out humanity' framing — but Hinton explicitly voiced existential-risk concerns in 2023 (NYT/Guardian: humans becoming the 'second most intelligent species,' 'it's not inconceivable' AI wipes us out). The real Hinton/Yudkowsky difference is prescription (Hinton doesn't advocate a shutdown), not that Hinton lacks existential worry.

**Stem:** In May 2023, Geoffrey Hinton left Google over worries about AI safety. He is sometimes called the 'godfather of deep learning.' How are his stated concerns different from Eliezer Yudkowsky's 'shut it all down' view?

**Labeled answer:** "Hinton's concerns are near-term harms like disinformation, autonomous weapons, and job displacement, not Yudkowsky's 'AI wipes out humanity' framing."

**Choices:**
- Hinton's concerns are near-term harms like disinformation, autonomous weapons, and job displacement, not Yudkowsky's 'AI wipes out humanity' framing. ← labeled
- Hinton thinks AI poses no real risk and critics are exaggerating; he resigned for unrelated personal reasons.
- Hinton wants to ban all neural networks globally and rewrite AI using only formal symbolic logic systems.
- Hinton and Yudkowsky hold identical views; the 'difference' is a media invention with no real substance.

### ai #820 (T4) — wrong_attribution · medium

**Auditor:** Hinton's post-Google interviews explicitly emphasized existential/extinction risk from superintelligent AI (10-20% chance within 30 years), not primarily near-term harms; the near-term-vs-extinction contrast with Yudkowsky is inaccurate — the actual difference is that Hinton shares extinction concerns but doesn't endorse 'shut it all down'

**Stem:** In May 2023, Geoffrey Hinton (one of the three 2018 Turing Award winners for deep learning) resigned from his decade-long role at Google. He gave interviews citing concerns about AI. How are his concerns different from Eliezer Yudkowsky's 'shut it all down' framing?

**Labeled answer:** "Hinton focuses on near-term harms like disinformation, job loss, and autonomous weapons rather than Yudkowsky's extinction framing."

**Choices:**
- Hinton focuses on near-term harms like disinformation, job loss, and autonomous weapons rather than Yudkowsky's extinction framing. ← labeled
- Hinton thinks AI poses no risk and only resigned due to a personal dispute with the search team at Google.
- Hinton wants to ban every neural network globally and replace AI with rule-based symbolic systems alone.
- Hinton and Yudkowsky hold identical views, and any reported difference is a media fabrication only.

### ai #823 (T4) — wrong_attribution · high

**Auditor:** Eliezer Yudkowsky did NOT sign the FLI 'Pause Giant AI Experiments' letter; he published a Time op-ed on 2023-03-29 explaining he refused to sign because a six-month pause was insufficient (he wanted a full shutdown). Musk, Wozniak, and Bengio did sign.

**Stem:** In March 2023, weeks after ChatGPT-4 stunned the world, the Future of Life Institute (a nonprofit focused on existential risk, co-founded by MIT physicist Max Tegmark) published an open letter titled 'Pause Giant AI Experiments.' It called for a six-month moratorium on training any AI system more powerful than GPT-4. Thousands signed it. Which of the well-known signers do people still remember most?

**Labeled answer:** 'Elon Musk, Steve Wozniak, Yoshua Bengio, and Eliezer Yudkowsky among many others.'

**Choices:**
- Elon Musk, Steve Wozniak, Yoshua Bengio, and Eliezer Yudkowsky among many others. ← labeled
- Sam Altman, Dario Amodei, Demis Hassabis, and Sundar Pichai signing together as a CEO group.
- Mark Zuckerberg, Tim Cook, Satya Nadella, and Jensen Huang signed it as Big Tech CEOs.
- Joe Biden, Xi Jinping, Emmanuel Macron, and Volodymyr Zelensky signing as world leaders.

### ai #973 (T4) — wrong_attribution · high

**Auditor:** Hinton left Google in 2023 explicitly to warn about extinction/existential risk and signed the May 2023 CAIS statement listing AI extinction alongside pandemics and nuclear war; describing his concerns as 'near-term harms, not extinction' misrepresents him. He's closer to Yudkowsky's camp on x-risk than to Gebru's near-term-harms camp.

**Stem:** People lump Yann LeCun (Meta's chief AI scientist), Eliezer Yudkowsky (Machine Intelligence Research Institute), and Geoffrey Hinton (once at Google) together as 'AI researchers' talking about risk. But their views are quite different. Which summary is the most accurate?

**Labeled answer:** "LeCun rejects existential-risk framings as overblown; Yudkowsky thinks frontier AI should be shut down; Hinton's concerns are near-term harms, not extinction"

**Choices:**
- LeCun rejects existential-risk framings as overblown; Yudkowsky thinks frontier AI should be shut down; Hinton's concerns are near-term harms, not extinction ← labeled
- All three hold identical views and have signed every public AI-risk statement together since 2019
- All three deny any AI risk exists and have publicly stated AI is harmless in every recent interview
- All three founded Anthropic together in 2021 and share the same official corporate safety position

---

## animal (7 suspects)

### animal #126 (T3) — dual_correct · medium

**Auditor:** For Argentinosaurus, size estimates typically DO rely on scaling from a more complete close relative (e.g., Saltasaurus, Rapetosaurus) for body proportions, since only a few bones exist — so choice B (relative's complete skeleton) is arguably as correct as the labeled A.

**Stem:** Argentinosaurus was a colossal long-necked plant-eating dinosaur that lumbered across South America about 95 million years ago. It stretched roughly 30 to 35 meters from snout to tail-tip — one of the largest animals that ever walked on land. But paleontologists have never dug up a whole skeleton. All they have are a few pieces: some huge vertebrae, a shin bone, a rib. How did they figure out its total length from so little?

**Labeled answer:** 'They scaled up its whole body from a handful of its own bones'

**Choices:**
- They scaled up its whole body from a handful of its own bones ← labeled
- They scaled it up from a close relative's complete skeleton
- They measured the stride length in a fossil trackway
- They compared it to the largest living whale

### animal #191 (T3) — wrong_answer · low

**Auditor:** MBARI's 2008 finding (Robison & Reisenbichler) is that the barreleye's eyes rotate independently within the fluid-filled dome to look forward; the fish does not need to roll its body from horizontal to vertical to swing the eyes forward.

**Stem:** Scientists at MBARI (the Monterey Bay Aquarium Research Institute) found that a barreleye cannot just swivel its eyes forward on their own. Its eyes reach the forward-pointing position only when the fish itself makes one specific move. What must the barreleye do to swing them forward?

**Labeled answer:** 'Roll its whole body from horizontal to vertical'

**Choices:**
- Roll its whole body from horizontal to vertical ← labeled
- Beat its tail hard three times
- Drift into a shaft of brighter light
- Press its snout against the prey

### animal #568 (T4) — off_by_number · medium

**Auditor:** Stem asks bite force 'at the very tip' per Anderson & Westneat 2007; the paper reports ~4,414 N at the fang tip and ~5,363 N at the blade edge (posterior). The labeled 5,300 N corresponds to the blade edge, not the tip; the distractor '~4,400 N' matches the tip figure.

**Stem:** A great white shark bites at roughly 4,000 newtons — bone-cracking force. When researchers Anderson and Westneat modelled Dunkleosteus in 2007, they found it concentrated an even fiercer force at the very tip of its bony blade. How hard did that blade tip bite?

**Labeled answer:** 'About 5,300 newtons'

**Choices:**
- About 5,300 newtons ← labeled
- About 4,400 newtons
- About 2,500 newtons
- About 8,000 newtons

### animal #847 (T5) — wrong_answer · low

**Auditor:** Riftia hemoglobin's sulfide-binding site is now attributed to free cysteine residues (Zal 1998, Bailly 2003), not zinc; zinc is present but its sulfide-binding role has been superseded.

**Stem:** The giant tube worm's blood must hold deadly vent sulfide without being poisoned. The trick: built into its hemoglobin are atoms of a plain metal most of us know only as a mineral in our diet, and the sulfide clips harmlessly onto those atoms. Which everyday metal does this life-saving job?

**Labeled answer:** 'Zinc'

**Choices:**
- Zinc ← labeled
- Copper
- Silver
- Calcium

### animal #1234 (T4) — off_by_number · medium

**Auditor:** The ~5% figure is the survival-to-adulthood rate for leafy sea dragons, not the egg-to-hatching rate; brooded eggs on the male's tail typically hatch at much higher rates (roughly 60-95%).

**Stem:** Off the shores of southern Australia drifts the leafy sea dragon, a slow-moving cousin of the seahorse whose body sprouts leaf-shaped flaps for camouflage. As with seahorses, it is the father who carries the eggs. A male can carry roughly 250 developing eggs on his tail, each one turning bright pink and pulling oxygen straight from his brood patch. Yet the open ocean is brutal on the tiny young. About how many of those eggs actually survive all the way to hatching?

**Labeled answer:** 'Around 5 in every 100'

**Choices:**
- Around 5 in every 100 ← labeled
- Around half
- Around 9 in every 10
- Nearly all of them

### animal #1915 (T2) — dual_correct · medium

**Auditor:** A sloth on land moves ~1.8-2.4 m/min; belly-wriggling (army crawl) at even a very leisurely pace outpaces that too, so 'Wriggling forward on the belly' is also true.

**Stem:** Guinness World Records has crowned the three-toed sloth of Central and South America as the slowest mammal on Earth. On the ground, this shaggy, tree-loving animal creeps along at just 1.8 to 2.4 meters a minute — barely faster than a slow drift. Sloths are so slow they climb down from their rainforest tree only about once a week, just to poop. Which of these ways of moving across the floor would let a person out-crawl a three-toed sloth?

**Labeled answer:** 'Crawling on hands and knees'

**Choices:**
- Crawling on hands and knees ← labeled
- Wriggling forward on the belly
- Scooting along seated on the hips
- Rolling sideways over and over

### animal #2197 (T4) — wrong_answer · medium

**Auditor:** The well-known 2013 Alaska rockfish (Henry Liebman's Sitka catch) was aged at ~200 years via otoliths, matching the size-based estimate — not revealed to be 'only 64 years'. No prominent 2013 Alaskan rockfish case matches the 64-year narrative.

**Stem:** In 2013, an enormous rockfish was pulled from deep Alaskan water, and, judging just by its huge size, biologists at first guessed it might be around 200 years old — nearly a record for its kind. Then they carefully removed its otoliths — the tiny growth-ringed ear stones inside its skull — split them open, and counted the rings under a microscope. The rings told a very different story. How old was the fish really?

**Labeled answer:** 'Only 64 years'

**Choices:**
- Only 64 years ← labeled
- Exactly 200 years
- Over 400 years
- Just 12 years

---

## economics (35 suspects)

### economics #35 (T3) — wrong_attribution · high

**Auditor:** Hal Finney's RPOW is from 2004, not ~1998; the canonical 1998 PoW-based digital-money pair with Wei Dai's b-money is Nick Szabo's bit gold. RPOW is also not in Bitcoin's 2008 white paper references (which cite b-money and Hashcash, not RPOW).

**Stem:** In 1997 the British cypherpunk Adam Back released Hashcash, which forced computers to burn a bit of real energy to send a message. His idea spread fast on cypherpunk mailing lists -- a scattered group of programmers dreaming up digital cash without banks. Around 1998, two of those builders each designed a digital-money system that leaned directly on Hashcash-style proof-of-work. A decade later, Bitcoin's 2008 white paper would build on both of their designs. Which two builders were they?

**Labeled answer:** 'Wei Dai (b-money) and Hal Finney (RPOW)'

**Choices:**
- Wei Dai (b-money) and Hal Finney (RPOW) ← labeled
- David Chaum (DigiCash) and Nick Szabo (bit gold)
- Phil Zimmermann (PGP) and Eric Hughes (remailers)
- Tim May (crypto anarchy) and John Gilmore (toad.com)

### economics #98 (T5) — wrong_answer · low

**Auditor:** Bhagwati's 1982 JPE paper is titled 'Directly Unproductive, Profit-seeking (DUP) Activities' — the standard acronym is DUP, not DUPS; author/year/concept are otherwise correct

**Stem:** Krueger's 1974 paper is one of the most-cited economics articles ever published. It gave the profession a standard name for a specific structural problem that shows up in every state-led economy. Which follow-on concept did later economists build directly on her work?

**Labeled answer:** "Bhagwati's directly-unproductive-profit-seeking (DUPS, 1982)"

**Choices:**
- Bhagwati's directly-unproductive-profit-seeking (DUPS, 1982) ← labeled
- Solow's growth residual (1957)
- Akerlof's lemons (1970)
- Coase's transaction costs (1937)

### economics #105 (T5) — wrong_attribution · low

**Auditor:** De Jasay 'spent his working life at a Normandy wine business' — actually he worked ~15 years in Paris banking then retired to a small farm in Normandy in 1979 as an independent scholar; Normandy is cider/calvados country and 'wine business' is a documented mischaracterization.

**Stem:** Anthony de Jasay, born in Hungary in 1925, fled communism after World War II and eventually settled in France. He went on to become one of the most cited libertarian thinkers of the late 20th century, writing books like 'The State' that shaped political philosophy worldwide. Yet one fact about his everyday career sets him apart from almost every other big name in that tradition — where most were tenured professors at famous universities, de Jasay took a very different path. What was it?

**Labeled answer:** 'He never held a permanent academic post; he spent his working life at a Normandy wine business'

**Choices:**
- He never held a permanent academic post; he spent his working life at a Normandy wine business ← labeled
- He served as prime minister of Hungary from 1990 to 1994
- He co-authored 'Capitalism and Freedom' with Milton Friedman
- He founded the Chicago School of Economics

### economics #229 (T3) — wrong_attribution · medium

**Auditor:** The 1927 Long Island meeting was attended by Norman, Schacht, and Charles Rist (Deputy Governor, Banque de France) representing Moreau — Emile Moreau himself did NOT attend.

**Stem:** In July 1927 Benjamin Strong, head of the Federal Reserve Bank of New York, hosted a secret meeting on Long Island with three foreign central bankers. Days later the Fed cut its discount rate — the rate it charges when banks borrow from it — from 4% to 3.5%. The cut was meant to help Europe defend the gold standard. Which three foreign central bankers attended?

**Labeled answer:** 'Montagu Norman of Britain, Emile Moreau of France, and Hjalmar Schacht of Germany'

**Choices:**
- Montagu Norman of Britain, Emile Moreau of France, and Hjalmar Schacht of Germany ← labeled
- John Maynard Keynes of Britain, Rene Coty of France, and Konrad Adenauer of Germany
- Winston Churchill of Britain, Georges Clemenceau of France, and Otto von Bismarck of Germany
- Nicholas Biddle of Britain, Charles de Gaulle of France, and Otto von Habsburg of Germany

### economics #318 (T5) — wrong_attribution · medium

**Auditor:** The four-word French tag 'Destruction n'est pas profit' is not a known Bastiat quotation and doesn't appear as the close of the broken-window section in 'Ce qu'on voit et ce qu'on ne voit pas' — the essay's broken-window section closes with a discussion of the shoes/repair trade-off, not a compressed four-word aphorism.

**Stem:** In 1850 the French economist Frederic Bastiat opened his essay 'That Which Is Seen and That Which Is Not Seen' with the story of a shopkeeper's son breaking a window. Bystanders comforted the shopkeeper by pointing out the glazier would now be paid — supposedly boosting the economy. Bastiat's broken-window section closes with a compressed four-word refutation, in French, of every later 'disaster-as-stimulus' claim. Which four words?

**Labeled answer:** "'Destruction n'est pas profit'"

**Choices:**
- 'Destruction n'est pas profit' ← labeled
- 'Luxe n'est pas richesse'
- 'Spoliation n'est pas industrie'
- 'Echange n'est pas vol'

### economics #544 (T3) — wrong_attribution · medium

**Auditor:** The 'colored labor... demoralize wage rates' framing is most famously associated with Rep. Clayton Allgood of Alabama (the 'cheap colored labor... in competition with white labor' floor speech), not co-sponsor Robert Bacon of NY; Bacon's own floor remarks about the Alabama contractor at the Northport VA hospital used different phrasing ('bootleg labor,' workers housed 'like cattle,' 'below the local prevailing rate')

**Stem:** During the 1931 House of Representatives debate on the Davis-Bacon Act -- the federal law requiring union-scale wages on government construction -- Congressman Robert Bacon of New York, the bill's co-sponsor, spelled out his explicit motive for excluding lower-wage migrant workers from federal building sites. His words later became infamous in histories of the law. Which line did Bacon speak on the House floor?

**Labeled answer:** 'Colored labor is being brought in to demoralize wage rates'

**Choices:**
- Colored labor is being brought in to demoralize wage rates ← labeled
- The southern states must build their own hospitals
- Union labor is the only safe federal contractor
- Immigration must be halted for national security

### economics #616 (T3) — off_by_number · low

**Auditor:** Standard scholarship holds the edict became unenforceable within roughly a year (Lactantius) and was effectively defunct by Diocletian's abdication in 305 AD; 'about a decade' overstates the timeline, and 'about a year' is the more defensible option among the choices.

**Stem:** The Roman Christian writer Lactantius, who lived through Diocletian's persecution of Christians, later wrote a book called On the Deaths of the Persecutors describing how Diocletian's 301 AD price edict actually played out. Goods vanished from open markets, black markets grew, and executions piled up. Roughly how long after the edict was issued did the government quietly drop it?

**Labeled answer:** 'About a decade'

**Choices:**
- About a decade ← labeled
- About a century
- About a year
- About a millennium

### economics #778 (T3) — off_by_number · medium

**Auditor:** Gold seizure at $20.67 then revaluation to $35 gives Treasury profit of ~41% of new price or ~69% of seizure price; dollar's gold weight cut 23.22->13.71 grains = ~41% reduction. Neither matches the labeled 'roughly 77%'.

**Stem:** In January 1934 President Franklin Roosevelt used the new Gold Reserve Act to cut the dollar's official gold weight nearly in half. Because the government had just seized private gold at the old price of $20.67 an ounce, and then set the new price at $35 an ounce, wealth shifted from ordinary savers who had been holding the metal to the US Treasury. About how much of those savers' buying power was moved?

**Labeled answer:** 'Roughly 77% of the purchasing power of savers who had held gold'

**Choices:**
- Roughly 77% of the purchasing power of savers who had held gold ← labeled
- Roughly 15%
- Roughly 5%
- Roughly 200%

### economics #790 (T4) — wrong_answer · medium

**Auditor:** William McChesney Martin Sr. was not the first governor of the Federal Reserve Bank of St. Louis; Rolla Wells was (1914-1919), followed by David C. Biggs (1919-1928). Martin Sr. was the Federal Reserve Agent / Chairman of the Board 1914-1928, then the third Governor from 1929-1941.

**Stem:** William McChesney Martin Jr. led the Federal Reserve as chairman from 1951 to 1970 — the longest run in Fed history. His father, William McChesney Martin Sr., had already held a specific earlier position inside the Federal Reserve System, making the Martins one of very few father-son central-banker pairs in US history. What was the father's role?

**Labeled answer:** 'First governor of the Federal Reserve Bank of St. Louis'

**Choices:**
- First governor of the Federal Reserve Bank of St. Louis ← labeled
- First chairman of the Federal Reserve Board
- First governor of the Federal Reserve Bank of New York
- First president of the Federal Reserve Bank of Boston

### economics #871 (T5) — wrong_answer · medium

**Auditor:** Chile in 1973 was NOT the poorest South American economy (Bolivia and Paraguay had markedly lower GDP per capita; Chile was middle-tier); it later rose to among the highest, but 'poorest to richest' overstates the starting point.

**Stem:** Chile's economic story runs from 1973, when General Augusto Pinochet's coup ended democracy, through the Chicago Boys' free-market reforms of the late 1970s, past the October 1988 plebiscite that voted Pinochet out, and on into the 2010s under a series of elected governments. Economists often cite this whole stretch as a real-world natural experiment in what happens when a poor country switches to market rules. Which one-sentence summary is most accurate to that record?

**Labeled answer:** 'Chile went from poorest to richest South American economy while eventually returning to peaceful democracy'

**Choices:**
- Chile went from poorest to richest South American economy while eventually returning to peaceful democracy ← labeled
- Chile remained the poorest South American economy throughout the entire period
- Chile experienced total economic collapse and mass emigration
- Chile abandoned all market reforms within five years of democratization

### economics #911 (T5) — wrong_attribution · low

**Auditor:** Machlup's formal Vienna dissertation supervisor (Doktorvater) is generally recorded as Friedrich von Wieser, not Mises; Mises was his private-seminar mentor. Sources conflict — worth human check.

**Stem:** In 1923 the young Fritz Machlup earned his doctorate at the University of Vienna. His advisor was the founding figure of the whole Austrian tradition — the economist who in 1920 had famously argued that a socialist state cannot rationally plan an economy, because without real market prices its planners have no way to compare costs. Who supervised the 1923 thesis?

**Labeled answer:** 'Ludwig von Mises'

**Choices:**
- Ludwig von Mises ← labeled
- Carl Menger
- Eugen von Bohm-Bawerk
- Friedrich von Wieser

### economics #1012 (T5) — wrong_attribution · medium

**Auditor:** Joseph Salerno (Mises Institute, Rothbardian) is generally aligned with Hoppe, not a critic of his anti-democratic conclusion; the pair typically cited alongside Boettke is Steven Horwitz or Christopher Coyne (GMU side), not Salerno

**Stem:** Hans-Hermann Hoppe's Democracy: The God That Failed split the Austrian school — the tradition of Carl Menger, Ludwig von Mises, Murray Rothbard, and Friedrich Hayek that stresses market prices and individual choice. Two Austrians accept much of Hoppe's incentive analysis of politicians but reject his anti-democratic conclusion. Which pair is most often cited?

**Labeled answer:** 'Peter Boettke and Joseph Salerno'

**Choices:**
- Peter Boettke and Joseph Salerno ← labeled
- Milton Friedman and Anna Schwartz
- Paul Krugman and Joseph Stiglitz
- Larry Summers and Jason Furman

### economics #1137 (T3) — off_by_number · low

**Auditor:** Mississippi Company shares peaked closer to ~18,000 livres in early 1720 (some sources cite 10,000-15,000 range late 1719); 10,000 is a mid-run figure, not the peak

**Stem:** In 1716 the Scottish theorist John Law convinced the French regent to let him print paper money and run the Louisiana trading company — the Mississippi Company. Between 1719 and early 1720 shares in the company rose from about 500 livres each to a peak that made the whole scheme famous across Europe. Roughly what peak price did the shares reach?

**Labeled answer:** 'About 10,000 livres per share'

**Choices:**
- About 10,000 livres per share ← labeled
- About 1,000 livres per share
- About 100,000 livres per share
- About 3,000 livres per share

### economics #1326 (T5) — wrong_attribution · low

**Auditor:** The 2004 Scholar's Edition of Man, Economy, and State (with Power and Market) is commonly credited as edited/introduced by Joseph Stromberg, not Joseph Salerno; Salerno contributed but is not the usually-cited editor. Human should verify against the actual title page.

**Stem:** Murray Rothbard was an American Austrian-school economist. His 1962 treatise Man, Economy, and State was cut before publication, and the removed section came out as a separate book, Power and Market, in 1970. In 2004 the Ludwig von Mises Institute finally reunited both parts into one 1,500-page Scholar's Edition — the volume Rothbard had wanted in the first place. Which longtime Rothbard student edited it?

**Labeled answer:** 'Joseph Salerno'

**Choices:**
- Joseph Salerno ← labeled
- Milton Friedman
- Israel Kirzner
- James Buchanan

### economics #1391 (T4) — off_by_number · low

**Auditor:** Friedman & Schwartz's Monetary History Aug-1929-to-Mar-1933 M1 figures are approximately $26.4B to $19.4B (about -27%); M2 approx $46.4B to $30.4B (about -35%). The stated $26.6B to $17.3B end-value does not match either standard series.

**Stem:** The common account of the Great Depression in 1963 was that markets had collapsed of their own accord and government had arrived to rescue what was left. Friedman and Anna Schwartz answered it with a measurement of the American money stock between August 1929 and March 1933. What had happened to it?

**Labeled answer:** 'It fell by about a third, from $26.6 billion to $17.3 billion'

**Choices:**
- It fell by about a third, from $26.6 billion to $17.3 billion ← labeled
- It rose by about a fifth, from $26.6 billion to $32.1 billion
- It held almost flat, moving from $26.6 billion to $26.1 billion
- It fell by about a twentieth, from $26.6 billion to $25.2 billion

### economics #1428 (T5) — wrong_attribution · low

**Auditor:** Mises's canonical short label rejecting a stable middle path is 'middle-of-the-road' (Mittelweg) or 'third way'; 'a third system' isn't a recognized Misesian label.

**Stem:** By the 1930s Ludwig von Mises had argued for a decade that the mixed economy is unstable. It must either move back toward markets or forward to full state control. He used one short label to reject the idea that a real middle path exists at all. Which label?

**Labeled answer:** 'A third system'

**Choices:**
- A third system ← labeled
- A guided economy
- Managed capitalism
- The mixed economy

### economics #1567 (T1) — wrong_attribution · medium

**Auditor:** Mises's 1920 argument is canonically 'the economic calculation problem'; 'the knowledge problem' is Hayek's later (1945) reformulation — the same bank credits Hayek for that shift in index 1571.

**Stem:** In 1920 the Austrian economist Ludwig von Mises published a big claim. A country where the government owns every factory and farm cannot know how much of each thing to make. Without free market prices to reveal what buyers actually want, the planners are guessing in the dark. What is this idea called?

**Labeled answer:** 'The knowledge problem'

**Choices:**
- The knowledge problem ← labeled
- The paperwork problem
- The weather problem
- The population problem

### economics #1659 (T5) — dual_correct · high

**Auditor:** Stem asks 'which is not Buchanan's, but belongs to a different figure'; both 'There are no solutions, only trade-offs (Sowell)' and 'The logic of collective action (Olson)' are labeled as belonging to non-Buchanan figures, so both choices satisfy the criterion.

**Stem:** 'Politics without romance' is the American economist James Buchanan's own three-word slogan for the whole discipline of public-choice economics, which studies how politicians and government officials respond to incentives. Below are four short slogans linked to public-choice or Chicago-school thinkers. Which one is not Buchanan's, but belongs to a different figure?

**Labeled answer:** 'There are no solutions, only trade-offs (Sowell)'

**Choices:**
- There are no solutions, only trade-offs (Sowell) ← labeled
- Politics without romance (Buchanan)
- The logic of collective action (Olson)
- Government-failure symmetry (Buchanan)

### economics #1788 (T4) — off_by_number · medium

**Auditor:** S&P 500 from QE2 announcement close Nov 3 2010 (~1198) to June 30 2011 (~1320) rose about 10%, not 24%; the 24% figure comes from measuring from the August 2010 Jackson Hole preview, not the announcement window the stem specifies.

**Stem:** The Fed's QE2 program -- creating new dollars to buy US government bonds -- ran from its November 2010 announcement to its June 2011 conclusion. The Irish-French economist Richard Cantillon warned in the 1700s that new money helps whoever gets it first before prices rise. That 'Cantillon-effect' payoff of QE2 was visible on stock-market tapes during those seven months. What did the S&P 500 index of big US companies do over that window?

**Labeled answer:** 'Rose approximately 24 percent'

**Choices:**
- Rose approximately 24 percent ← labeled
- Fell approximately 5 percent
- Rose approximately 5 percent
- Stayed roughly flat

### economics #1819 (T3) — wrong_attribution · medium

**Auditor:** Standard consensus for pre-2008 mortgage-supervision blame centers on the Fed (Greenspan), OCC, and OTS (WaMu/IndyMac/Countrywide/AIG); the FDIC under Sheila Bair actually raised early warnings and is not typically lumped in as the captured pair. 'OCC + FDIC' is not the most-blamed pair.

**Stem:** In the years before the 2008 financial crash, two US federal bank agencies were supposed to watch how safely American banks were making home loans. Both missed the enormous risks piling up in mortgage-backed securities. Later Congressional investigations found their staff regularly rotated between the agencies and the banks they were supposed to police — the so-called 'revolving door.' Which pair of agencies gets the most blame?

**Labeled answer:** 'The Office of the Comptroller of the Currency and the FDIC'

**Choices:**
- The Office of the Comptroller of the Currency and the FDIC ← labeled
- The Federal Reserve and the Treasury Department
- The Securities and Exchange Commission and the CFTC
- The Consumer Financial Protection Bureau and HUD

### economics #1869 (T4) — wrong_answer · low

**Auditor:** The Mises Institute's lifetime-achievement award Ron Paul received (2004) was the Gary G. Schlarbaum Prize, not a 'Rothbard Medal of Freedom' — that award name does not appear to correspond to a real Mises Institute honor.

**Stem:** The Mises Institute in Auburn, Alabama, is the leading center of Austrian-school economics in the United States. Its highest honor is named for Murray Rothbard, the Austrian economist who was a close personal friend of the Texas congressman Ron Paul. In 2011 the institute gave Ron Paul this top award for his lifelong defense of sound money and free markets. Which award did he receive?

**Labeled answer:** 'The Rothbard Medal of Freedom'

**Choices:**
- The Rothbard Medal of Freedom ← labeled
- The Hayek Prize
- The Menger Medal
- The Mises Freedom Award

### economics #1912 (T3) — off_by_number · low

**Auditor:** Grullon, Larkin & Michaely (RFS 2019) report the U.S. listed-firm count fell from ~7,322 (1996) to ~3,671 (2016); 'About 4,300' overshoots Grullon's own figure — the distractor 'About 3,100' is actually closer to the paper's 3,671.

**Stem:** About 7,300 US companies were listed on public stock markets in 1996. Twenty years later many were gone — bought up in mergers, taken private by buyout firms, or simply delisted. The economist Gustavo Grullon and his co-authors published a widely cited study measuring the drop and warning that American industries were becoming much more concentrated. About how many US-listed companies were left by 2016, per the Grullon study?

**Labeled answer:** 'About 4,300'

**Choices:**
- About 4,300 ← labeled
- About 6,800
- About 3,100
- About 5,700

### economics #2001 (T4) — wrong_answer · medium

**Auditor:** Chile's 1981 AFP reform (DL 3500) required all new entrants to use the private system and let existing active workers choose; the standard exclusions were the armed forces and those already receiving pensions, not 'those within five years of retirement'. Piñera has repeatedly stressed that all existing workers were given the choice.

**Stem:** In May 1981 Chile became the first country to let workers leave the state pension. They could send ten percent of their wages into a private retirement account instead. Jose Pinera, the labor minister, made the switch optional for those in the old plan. But one group was barred from switching. Which workers could not switch?

**Labeled answer:** 'Those within five years of retirement'

**Choices:**
- Those within five years of retirement ← labeled
- Those earning below the national minimum wage
- Those who had contributed for fewer than ten years
- Those working for more than one employer at a time

### economics #2052 (T2) — wrong_attribution · low

**Auditor:** I cannot verify Sowell uses an 'Easter egg hunt' image in Vision of the Anointed for the 'solutions sit waiting to be picked up' picture; the well-known metaphor for that mindset is the streetlamp/drunkard search, which is also a listed distractor. Possibly misattributed.

**Stem:** In The Vision of the Anointed (1995), Thomas Sowell mocks the picture that smart planners carry around. On their view, every hard problem has an answer sitting somewhere, and policy just has to go get it. Sowell drew that picture with one homely image. Which image?

**Labeled answer:** 'Eggs laid out for children at an Easter hunt'

**Choices:**
- Eggs laid out for children at an Easter hunt ← labeled
- Keys lost somewhere under a lit street lamp
- Weeds pulled one by one from a long border
- Coins shaken loose from a locked money box

### economics #2083 (T3) — wrong_answer · medium

**Auditor:** Answer claims USSR 'killed the most people of any communist state', but the Black Book's own figures put China at ~65M vs USSR ~20M; USSR chapter is longest because the USSR was the founding/longest-lasting regime with the most extensive archives, not because it had the highest death toll.

**Stem:** When French historian Stephane Courtois edited The Black Book of Communism in 1997, he pulled together chapters by many European scholars. Each chapter tallied the deaths under one communist government -- the USSR, China, Cambodia, North Korea, Ethiopia, Vietnam, and others. Of every chapter in the book, the one on the Soviet Union was by far the longest. Why was the Soviet chapter the longest?

**Labeled answer:** 'The Soviet system lasted the longest and killed the most people of any communist state'

**Choices:**
- The Soviet system lasted the longest and killed the most people of any communist state ← labeled
- The Soviet Union was the only communist country in the book
- The chapter was longest because Russian is harder to translate
- The other communist countries had lost most of their records

### economics #2240 (T2) — off_by_number · low

**Auditor:** S&P 500 rose from 2237 (Mar 23, 2020 low) to ~4793 (Dec 27, 2021 peak) — that is ~114%, not 'about 90 percent'; 90% would be ~4250. Closest among the four choices but the labeled figure is materially off.

**Stem:** When the COVID-19 pandemic hit in March 2020, US stocks crashed as businesses shut down. The S&P 500 index, which tracks America's 500 largest companies, hit a low on March 23, 2020. Then the Federal Reserve pumped trillions of new dollars into the economy through emergency programs, and stock prices rocketed upward. The S&P 500 peaked in December 2021. About what percent did it rise from that pandemic low to that peak?

**Labeled answer:** 'About 90 percent'

**Choices:**
- About 90 percent ← labeled
- About 30 percent
- About 200 percent
- About 15 percent

### economics #2333 (T4) — off_by_number · medium

**Auditor:** US federal outlays fell from ~$92.7B (FY1945) to ~$55.2B (FY1946), about a 40% drop — 'slightly less than half' (a distractor) is right; the two-thirds figure only holds by FY1948.

**Stem:** The end of World War II is the biggest peacetime drop in federal spending ever recorded. About how much did federal spending fall from 1945 to 1946?

**Labeled answer:** 'By more than two-thirds'

**Choices:**
- By more than two-thirds ← labeled
- By about one quarter
- By about one tenth
- By slightly less than half

### economics #2499 (T4) — wrong_answer · medium

**Auditor:** The Fed's official 2% inflation target since 2012 is measured by headline PCE, not core PCE; core PCE is a supplementary near-term indicator but not the target index in the FOMC's Statement on Longer-Run Goals.

**Stem:** The Federal Reserve — America's central bank — publicly aims for 2 percent yearly inflation. But 'inflation' can mean many things: housing prices, stock prices, the M2 money supply, or the price of the groceries a family actually buys. The Fed chose one specific consumer index and has steered policy by it since 2012. It excludes wild food and energy swings and reflects what US households really spend. Which measure does the Fed track for its 2 percent target?

**Labeled answer:** 'The core PCE price index'

**Choices:**
- The core PCE price index ← labeled
- The Case-Shiller housing price index
- The S&P 500 total return
- The M2 money supply

### economics #2764 (T3) — wrong_attribution · low

**Auditor:** The candlemakers' petition's chain-of-jobs joke (tallow, whaling, forests, shipping) is standardly labeled the 'employment' or 'job-creation' argument for tariffs, not the 'multiplier' argument (which in economics specifically denotes Keynesian fiscal spillovers). None of the other listed choices is a better fit, but the labeled answer's term is nonstandard.

**Stem:** In 1845 the French economist Frederic Bastiat wrote a joke petition, supposedly from the candlemakers of France, begging the government to block out the sun so people would have to burn candles all day. The petition then lists every job that would supposedly grow: more tallow farms, more whaling fleets, more forests, more shipping. This chain-of-benefits joke mocks which real argument for tariffs?

**Labeled answer:** 'The multiplier argument for tariffs'

**Choices:**
- The multiplier argument for tariffs ← labeled
- The infant-industry argument for tariffs
- The national-defense argument for tariffs
- The reciprocity argument for tariffs

### economics #2766 (T4) — dual_correct · medium

**Auditor:** In Free to Choose (Ch. 2), Friedman explicitly frames trade as 'imports are the benefit, exports are the cost' — so choice C (imports treated as threat, exports as benefit) is also a defensible reading of what pair Friedman contrasted using the candlemakers. The labeled A (abundance/scarcity) is fine, but C is arguably also correct.

**Stem:** In his 1980 book Free to Choose, Milton Friedman used Bastiat's candlemakers' petition to attack a common trade argument. Friedman said any claim that treats one thing as a threat and its opposite as a benefit deserves the candlemakers' test. Which pair did his argument contrast?

**Labeled answer:** 'Abundance treated as a threat, scarcity treated as a benefit'

**Choices:**
- Abundance treated as a threat, scarcity treated as a benefit ← labeled
- Consumption treated as a threat, saving treated as a benefit
- Imports treated as a threat, exports treated as a benefit
- Immigration treated as a threat, emigration treated as a benefit

### economics #2963 (T4) — off_by_number · low

**Auditor:** Mises was born Sept 29, 1881; arrived NJ Aug 2, 1940. He was 58 (turned 59 that Sept), not 'fifty-nine'. The 'no US chair' part is correct.

**Stem:** When Ludwig von Mises, the leader of the Austrian School of economics, stepped off the ship in New Jersey on August 2, 1940, he had already fled Vienna and then Geneva ahead of the Nazi advance. Many economists ranked him among the greatest minds of his time. American universities knew his name. How old was he then, and what US university chair awaited him?

**Labeled answer:** 'Fifty-nine, and no American university offered him a paid chair for the rest of his life'

**Choices:**
- Fifty-nine, and no American university offered him a paid chair for the rest of his life ← labeled
- Forty-four, and a full Harvard professorship awaited him
- Sixty-seven, and a Yale endowed chair had been arranged in advance
- Fifty-two, and a Chicago professorship followed within the year

### economics #3043 (T3) — dual_correct · medium

**Auditor:** Krueger's 1974 paper 'The Political Economy of the Rent-Seeking Society' quantified rent-seeking in both India AND Turkey; Turkey as distractor is also a valid answer.

**Stem:** In 1974 the American economist Anne Krueger took Gordon Tullock's 1967 idea about wasted lobbying effort and tested it on one big developing country. She showed how the country's government import licenses were worth huge sums, and how firms spent nearly as much money on lobbying, gifts, and paperwork to win the licenses as the licenses were themselves worth. Which country did Krueger study?

**Labeled answer:** 'India'

**Choices:**
- India ← labeled
- Brazil
- Turkey
- Egypt

### economics #3062 (T5) — wrong_answer · medium

**Auditor:** The 2014 Farm Bill created the 'Margin Protection Program for Dairy' (MPP-Dairy); it was the 2018 Farm Bill that renamed/reformed it into the Dairy Margin Coverage (DMC). Strictly, DMC is a 2018 label.

**Stem:** By 2014, the US government had been buying up surplus milk under the 1949 Agricultural Act for 65 years. The 2014 Farm Bill kept dairy farmers protected above market prices, but replaced the old direct-purchase machinery with a new insurance-style mechanism that paid farmers whenever their profit margin -- milk price minus feed cost -- dropped below a chosen level. What did the 2014 Farm Bill replace the older program with?

**Labeled answer:** 'The Dairy Margin Coverage (DMC) system'

**Choices:**
- The Dairy Margin Coverage (DMC) system ← labeled
- A federal ban on all dairy subsidies
- A privatized dairy futures exchange
- A European-Union-style quota auction

### economics #3066 (T2) — off_by_number · medium

**Auditor:** 130,000% is the Venezuelan Central Bank's (BCV) retroactive figure for 2018; the IMF's widely cited 2018 projection was ~1,000,000% (October 2018 WEO put it at ~1,370,000%). Closest listed option would be ~3,000,000%/yr.

**Stem:** By 2018 Venezuela's economy was in freefall. Years of Chavez and Maduro's price controls, oil-industry seizures, and money-printing had unleashed hyperinflation on the same scale as Weimar Germany in 1923, when Germans burned marks in their stoves for heat. That year the International Monetary Fund (IMF) released its official estimate of Venezuela's yearly inflation rate. About how high did the IMF say prices were rising?

**Labeled answer:** 'About 130,000% per year'

**Choices:**
- About 130,000% per year ← labeled
- About 500% per year
- About 25% per year
- About 3,000,000% per year

### economics #3218 (T3) — off_by_number · medium

**Auditor:** The widely reported June 2015 RBZ demonetisation rate was Z$35 quadrillion = US$1 (with balances up to Z$175 quadrillion receiving a flat US$5). '175 quadrillion for one US dollar' conflates the balance threshold with the per-dollar rate.

**Stem:** By 2009 Zimbabwe's own currency, the Zimbabwe dollar, had been destroyed by years of runaway money-printing under President Robert Mugabe. People had already stopped using it for daily shopping, but old leftover balances still sat frozen in bank accounts. In June 2015 the Reserve Bank of Zimbabwe formally killed the Zimbabwe dollar. It offered to swap those remaining bank balances for US dollars at a single blunt exchange rate. What was that rate?

**Labeled answer:** '175 quadrillion Zimbabwe dollars for one US dollar'

**Choices:**
- 175 quadrillion Zimbabwe dollars for one US dollar ← labeled
- 1 billion Zimbabwe dollars for one US dollar
- 10 trillion Zimbabwe dollars for one US dollar
- 1 million Zimbabwe dollars for one US dollar

---

## geography (1 suspects)

### geography #2732 (T4) — wrong_answer · medium

**Auditor:** Atlantis II Deep muds are standardly characterized as richest in zinc, copper, and silver (with lead and gold); cobalt is present only in trace amounts, not a headline metal — the labeled triple 'copper, cobalt, and zinc' substitutes cobalt for silver.

**Stem:** Two kilometers down in the Red Sea lies the Atlantis II Deep. Its water is about 68 C, and it is so salt-choked that nothing can live in it. Yet mining companies dream about it, because the mud there holds the richest known hoard of dissolved metals anywhere on the ocean floor, packed about a thousand times denser than in seawater. Which three valuable metals is it richest in?

**Labeled answer:** 'copper, cobalt, and zinc'

**Choices:**
- copper, cobalt, and zinc ← labeled
- gold, silver, and platinum
- iron, nickel, and lead
- tin, mercury, and manganese

---

## history (12 suspects)

### history #753 (T5) — wrong_attribution · medium

**Auditor:** The 'condemned man calmly shouted his own firing-squad commands' story is traditionally attributed to Cornelio Rojas (Batista's national police chief, executed Jan 1959 at Santa Clara — 'Muchachos, fuego!'), not to Jesús Sosa Blanco, whose fame rests on the Havana Sports Palace show trial before his La Cabaña execution.

**Stem:** Jesús Sosa Blanco, a major under the ousted dictator Batista, was condemned to die before a firing squad at the La Cabaña fortress in Havana for scores of killings. As the squad took aim, Sosa Blanco did something that stunned the men sent to shoot him. What did he do?

**Labeled answer:** 'He shouted the squad\'s own commands at them — "Atención! Apunte! Fuego!" — ordering his own death'

**Choices:**
- He shouted the squad's own commands at them — "Atención! Apunte! Fuego!" — ordering his own death ← labeled
- He fell to his knees and begged the young soldiers to spare his life
- He read aloud a list of judges he swore would die after him
- He stayed silent and refused the blindfold the guards offered him

### history #2511 (T5) — wrong_answer · medium

**Auditor:** Sailing west means you experience one FEWER day than the stationary world — the crew's log was BEHIND local (Wed vs. Thu), which is standardly described as 'lost a day,' not 'gained a day.' Pigafetta and Wikipedia both phrase this as the crew having lost a day.

**Stem:** When the Victoria reached the Cape Verde islands in July 1522, the crew got a shock. Their ship's logbook, kept faithfully every single day for three years, said it was Wednesday — but every local insisted it was Thursday. The sailors had stumbled onto the first real-world proof of an idea we still use today. What had happened?

**Labeled answer:** 'By always sailing west they had gained a whole day'

**Choices:**
- By always sailing west they had gained a whole day ← labeled
- Their calendar had skipped a leap year at sea
- A storm had knocked out two days of records
- They had crossed the equator one time too many

### history #2729 (T5) — dual_correct · medium

**Auditor:** Both 'still classified secrets' and 'revealing them would expose the broken codes' are correct; the second is arguably the more specific/informative reason for classification.

**Stem:** The top-secret Venona project decoded intercepted Soviet cables. It named Julius Rosenberg in 21 messages under the codenames ANTENNA and LIBERAL, and it showed that he really did run a spy ring. Yet prosecutors never used a single one of these cables against him in court. Why were the decoded cables kept out of Rosenberg's trial?

**Labeled answer:** 'The cables were still classified secrets'

**Choices:**
- The cables were still classified secrets ← labeled
- Revealing them would expose the broken codes
- The cables named only his codename
- The code-breakers refused to testify

### history #3083 (T4) — wrong_answer · medium

**Auditor:** Pausanias (5.11.10) records that OIL was used in front of Zeus at Olympia (damp climate), while WATER was used in front of Athena Parthenos on the Athenian Acropolis (dry climate) — the answer appears to swap the two.

**Stem:** Inside Athens' great temple of Athena towered Phidias' statue of the goddess: about forty feet tall, sheathed in ivory and over a ton of gold. On the floor right in front of her, Phidias kept a shallow pool of one liquid, both to protect the ivory and to mirror her image. What filled the pool?

**Labeled answer:** 'olive oil'

**Choices:**
- olive oil ← labeled
- fresh spring water
- sweet wine
- scented perfume

### history #3893 (T5) — off_by_number · medium

**Auditor:** Stem's own numbers (1,500+ sailors dead vs ~150,000 freed) give a ratio of ~1:100, matching distractor 'one sailor dead for every hundred slaves freed', not the labeled 1:9. Standard historical citation (~1,587 sailors / 150,000 freed) is also ~1:95, not 1:9.

**Stem:** Hunting slave ships was deadly work, and not only for the captives. Across half a century chasing slavers off the African coast, the Royal Navy's West Africa Squadron lost more than 1,500 of its own sailors, most of them to tropical disease rather than enemy fire. Contemporaries summed up the human cost of the campaign with a single grim ratio, comparing sailors lost to Africans freed. What was that ratio?

**Labeled answer:** 'One sailor dead for every nine slaves freed'

**Choices:**
- One sailor dead for every nine slaves freed ← labeled
- One sailor dead for every slave freed
- One sailor dead for every hundred slaves freed
- One sailor dead for every thousand slaves freed

### history #4145 (T3) — off_by_number · medium

**Auditor:** Traditional hadith (Sahih al-Bukhari 4265) has Khalid ibn al-Walid saying NINE swords broke in his hand at Mu'tah, not eight.

**Stem:** The Arab general Khalid ibn al-Walid was remembered as never losing a battle in his whole life, and he earned the title 'Sayf Allah' — the Sword of Allah. Legend says the name came from a furious fight at Mu'tah where he held the line so hard that something happened to his weapons. What did he do?

**Labeled answer:** 'He broke eight swords in his hands'

**Choices:**
- He broke eight swords in his hands ← labeled
- He fought on after losing both eyes
- He held the bridge entirely alone
- He slew the enemy king in single combat

### history #4348 (T3) — off_by_number · medium

**Auditor:** Solzhenitsyn was released from Ekibastuz camp in February 1953 (approx Feb 9-13); Stalin died March 5, 1953. The two dates are close but not the 'exact same day' — this is a widely repeated but likely inaccurate coincidence claim.

**Stem:** The Russian writer Aleksandr Solzhenitsyn spent eight years in Joseph Stalin's Soviet labor camps for writing private letters that mocked Stalin. In 1953, he was finally released and walked out of the camps a free man. By a strange stroke of luck, his very first day of freedom fell on the exact same day as one enormous event. What event was it?

**Labeled answer:** 'The day Stalin died'

**Choices:**
- The day Stalin died ← labeled
- The end of the Second World War
- The launch of the first Sputnik
- The outbreak of the Korean War

### history #4405 (T3) — dual_correct · low

**Auditor:** Hunayn ibn Ishaq's famous refusal cited both his religion AND his profession; the labeled 'oath as physician' is right, but distractor 4 'poisoning dishonored the calling of a healer' captures essentially the same professional-ethics reason and could also be scored correct.

**Stem:** In 9th-century Baghdad, Caliph al-Mutawakkil summoned the great Christian scholar-physician Hunayn ibn Ishaq, translator of the Greek doctor Galen, and offered him lavish rewards to brew a poison for an enemy of the court. Hunayn flatly refused -- and was thrown into prison for a whole year to change his mind. What reason did Hunayn give for saying no?

**Labeled answer:** 'His oath as a physician bound him to heal, never to harm'

**Choices:**
- His oath as a physician bound him to heal, never to harm ← labeled
- His faith forbade him to take any human life
- He had sworn that same healer's oath to the enemy too
- He held that poisoning dishonored the calling of a healer

### history #4590 (T3) — off_by_number · low

**Auditor:** El Manati rubber balls dated ~1700 BC vs first Olympics 776 BC = ~924 years, which is NOT 'over a thousand years'; it's under. Answer is directionally right but numerically off.

**Stem:** The Mesoamerican ball game was played with a solid rubber ball roughly a foot across, weighing up to nine pounds. The oldest such rubber balls ever recovered were pulled from a sacrificial bog at El Manati in Mexico. They date to about 1700 BC. Compared to the first Greek Olympic Games, how old does that make this contest?

**Labeled answer:** 'Older than the first Olympics by over a thousand years'

**Choices:**
- Older than the first Olympics by over a thousand years ← labeled
- Older than the first Olympics by about fifty years
- Younger than the first Olympics by a few centuries
- Played at the very same time as the first Olympics

### history #4642 (T4) — wrong_attribution · medium

**Auditor:** Mainstream account identifies the ill delegate whose absence killed Jefferson's 1784 anti-slavery clause as John Beatty of New Jersey (leaving NJ unable to cast a state vote), not James Monroe of Virginia; Jefferson later wrote 'the voice of a single individual...' referring to the NJ delegate.

**Stem:** In 1784 — three years before the famous Northwest Ordinance ever passed — the Virginian statesman Thomas Jefferson wrote a bold plan to ban slavery from every western United States territory after the year 1800. His plan lost by a single vote in Congress. Why was that one deciding vote never cast?

**Labeled answer:** 'A Virginia delegate, James Monroe, lay sick in bed and missed the vote'

**Choices:**
- A Virginia delegate, James Monroe, lay sick in bed and missed the vote ← labeled
- Jefferson withdrew his own plan at the last moment to save it for later
- A messenger lost the only signed copy on the road to Congress
- Southern delegates walked out before the count could be taken

### history #4972 (T5) — off_by_number · low

**Auditor:** Wrights found Smeaton coefficient should be ~0.0033 vs the accepted 0.005 — that's a factor of ~1.5, i.e. 'off by about half,' not 'nearly a factor of two'.

**Stem:** While building the airplane, the Wright brothers checked a number called the Smeaton coefficient, a constant that everyone calculating lift and air pressure had trusted for more than a century. When they measured it themselves in their wind tunnel, they found the long-accepted value was badly off. By how much was this century-old constant wrong?

**Labeled answer:** 'Off by nearly a factor of two'

**Choices:**
- Off by nearly a factor of two ← labeled
- Off by less than one percent
- Off by exactly ten times
- Off by a factor of a thousand

### history #5042 (T2) — wrong_attribution · medium

**Auditor:** The famous annual 'whole town gathers to replaster' festival (Crepissage) is at the Great Mosque of Djenne, not Timbuktu's Djinguereber Mosque; Djinguereber is also mud-built and periodically maintained but lacks the iconic single-day town-wide festival described.

**Stem:** In the West African city of Timbuktu on the southern edge of the Sahara stands the Djinguereber Mosque, first built in 1327 — almost 700 years old. It is made of mud, straw, and palm wood, with no stone at all in the walls. Once a year, when the short rainy season ends, the whole town gathers around it and does one thing together, or the desert rains would slowly melt it back into the ground. What does the whole town do?

**Labeled answer:** 'replaster it by hand from top to bottom'

**Choices:**
- replaster it by hand from top to bottom ← labeled
- raise wooden roofs over its open courts
- dig new channels to carry the rain off
- hang woven mats along its outer walls

---

## philosophy (4 suspects)

### philosophy #1271 (T4) — dual_correct · medium

**Auditor:** Labeled answer (sampling frame: car/phone owners) is a real cause of Literary Digest failure, but distractor 2 (non-response bias — only the eager few mailed ballots back) is also a well-documented cause; Squire (1988) argues non-response was the larger factor.

**Stem:** In 1936 a big magazine mailed ten million ballots and got over two million back. It said Alf Landon would beat Franklin Roosevelt. Roosevelt then won every state but two. A young pollster named George Gallup asked only fifty thousand people, and he called it right. Why did the huge sample fail so badly?

**Labeled answer:** 'Its ballots went only to car and telephone owners, the well-off who leaned against Roosevelt'

**Choices:**
- Its ballots went only to car and telephone owners, the well-off who leaned against Roosevelt ← labeled
- Its tally counted only the eager few who bothered to mail a ballot back, a self-picked slice of the nation
- Its readers deliberately lied on the ballots they returned in order to embarrass the magazine they disliked
- Its young rival George Gallup had merely guessed luckily, as any small poll sometimes happens to do

### philosophy #2032 (T5) — dual_correct · medium

**Auditor:** Choice B (calm/contentment untouchable by tyrant) is also a canonical Epictetus teaching alongside the labeled answer (moral character untouchable); both are things the tyrant cannot reach on Epictetus's view.

**Stem:** A cruel tyrant drags a man before him in chains and gloats that he now holds the man's fate entirely in his hands, free to ruin the prisoner however he pleases. The ancient Roman Stoic teacher Epictetus, once a slave himself, would answer that the tyrant, for all his power, has overreached. There is one thing about this chained man that no chain and no executioner can ever reach. What is it?

**Labeled answer:** "Whether he turns into a worse man -- that descent is his alone to make, not the tyrant's"

**Choices:**
- Whether he turns into a worse man -- that descent is his alone to make, not the tyrant's ← labeled
- Whether he keeps his calm and contentment -- that peace is his to hold, not the tyrant's
- Whether his body lives to see another dawn -- that breath is his to keep, not the tyrant's
- Whether he holds his rank and good name -- that standing is his to keep, not the tyrant's

### philosophy #2682 (T2) — wrong_answer · medium

**Auditor:** The answer 'calm, mild people content with an ordinary life' matches Nietzsche's despised Last Man archetype (Zarathustra's prologue), not his ideal of secretly-strong. Nietzsche's sublimated noble type is self-mastered but never 'content with an ordinary life'.

**Stem:** The 19th-century German philosopher Friedrich Nietzsche surprised his readers by claiming that real strength could live in a kind of person almost nobody would call powerful. Which sort of person did Nietzsche single out as secretly strong?

**Labeled answer:** 'Calm, mild people content with an ordinary life'

**Choices:**
- Calm, mild people content with an ordinary life ← labeled
- Bold rebels who openly defy the crowd
- Restless strivers who can never sit still
- Hardened people who have suffered terribly

### philosophy #2828 (T3) — dual_correct · low

**Auditor:** Xunzi's actual textual answer in Tianlun is 'it would have rained anyway' (matches choice C: 'The rain was always coming, and the prayer merely lets people feel they had caused it'); labeled A ('no care for us, so the rain falls for no reason at all') captures the metaphysical framework but C more directly answers the stem's 'why did it rain?'

**Stem:** In ancient China, the Confucian philosopher Xunzi thought Heaven was not a personal god watching over people but simply the plain workings of Nature — the sky, the seasons, the weather, uncaring. To shake his students, he asked a blunt question about prayer: you pray for rain, and it rains, so why did it rain? His startling answer explained why he thought fixing human nature was entirely up to people.

**Labeled answer:** 'Because the sky is just plain Nature with no care for us, so the rain falls for no reason at all'

**Choices:**
- Because the sky is just plain Nature with no care for us, so the rain falls for no reason at all ← labeled
- Because Heaven heard the prayer and rewarded the faithful, which proves the cosmos cares for the good
- Because the rain was always coming, and the prayer merely lets people feel they had caused it
- Because the ritual of prayer itself stirs the clouds, which is exactly why ritual must never be skipped

---

## science (8 suspects)

### science #1428 (T4) — wrong_attribution · low

**Auditor:** Denys transfused the 15-year-old boy with lamb/sheep blood, but Antoine Mauroy received calf's blood in the fatal case; the stem's 'same trick' framing plus 'a lamb's' answer conflates the two - calf blood is the historically accurate blood for the Mauroy death.

**Stem:** The very first attempt to put one creature's blood into another began in Paris on 15 June 1667. A young physician named Jean-Baptiste Denys transfused a 15-year-old boy with the blood of another creature, and the boy survived. Later Denys tried the same trick on a man named Antoine Mauroy; Mauroy died. Whose blood had Denys been using?

**Labeled answer:** "a lamb's"

**Choices:**
- a lamb's ← labeled
- a horse's
- a dog's
- another man's

### science #1731 (T3) — off_by_number · medium

**Auditor:** Farman/Gardiner/Shanklin 1985 Nature paper reported October ozone at Halley Bay falling from ~320 DU baseline to ~200 DU by 1984 -- roughly a 40 percent drop (paper's own phrasing: 'almost halved'). The 'up to 70 percent' figure came from later years, not this paper.

**Stem:** A station on the Antarctic coast had been tracking ozone since the 1950s, and October levels kept falling. In 1985 three British scientists published the numbers in the journal Nature. How big a drop did their paper report over Antarctica each southern spring?

**Labeled answer:** 'up to 70 percent of the ozone column'

**Choices:**
- up to 30 percent of the ozone column
- up to 50 percent of the ozone column
- up to 70 percent of the ozone column ← labeled
- up to 95 percent of the ozone column

### science #2815 (T4) — wrong_answer · low

**Auditor:** Richard Herrick died in 1963; the cause most consistently reported is a recurrence of his original kidney disease (glomerulonephritis) in the transplanted kidney, not simple heart failure. 'Rejection of the transplanted kidney' distractor is also arguably closer than the labeled answer.

**Stem:** In 1954, in Boston, the American surgeon Joseph Murray took a healthy kidney from Ronald Herrick and stitched it into his identical twin brother Richard, whose own kidneys had failed. Because the brothers shared every gene, Richard's body did not attack the graft — the world's first lasting organ transplant. Richard lived about eight more years, married one of his hospital nurses, and fathered two children. When he died in March 1963, what killed him?

**Labeled answer:** 'Heart failure'

**Choices:**
- Heart failure ← labeled
- Rejection of the transplanted kidney
- Pneumonia caught from his brother
- A stroke during a second operation

### science #2844 (T4) — wrong_answer · medium

**Auditor:** NRC 2006 report on strip-bark bristlecones named CO2 fertilization (per Graybill and Idso 1993) as the non-climatic factor potentially fattening recent rings, not nitrogen deposition; nitrogen is not the standard bristlecone-strip-bark alternative.

**Stem:** The US National Research Council panel that reported in June 2006 handed the critics a second point, about one kind of tree in the network. A strip-bark bristlecone pine is an ancient tree whose trunk is mostly dead, with a single surviving ribbon of living bark still laying down a ring each year; such samples 'should be avoided' for temperature reconstructions, the panel wrote. It then named something besides warmth that may be fattening their recent rings. What was it?

**Labeled answer:** 'Nitrogen from human sources settling out of the air'

**Choices:**
- Nitrogen from human sources settling out of the air ← labeled
- Desert dust settling on the slopes and feeding the soil
- Deeper winter snowpack lasting later into the spring
- Less competition as neighbouring old trees died back

### science #3093 (T3) — off_by_number · medium

**Auditor:** LeMay's canonical response to the jet-stream problem was switching to LOW-altitude (about 5,000-9,000 ft) night incendiary raids starting March 9-10, 1945; '25,000 ft' is not the standard historical figure and would still put B-29s inside the jet stream.

**Stem:** In late 1944 American B-29 crews arrived over Japan planning to bomb from 30,000 ft. At that altitude they suddenly found themselves flying inside winds of 200-300 mph -- Oishi's river, unknown to them. Under full throttle some aircraft made almost no ground speed at all and bombs missed by miles. General Curtis LeMay's response was to change ONE thing about how the B-29s flew. What did he change?

**Labeled answer:** 'he lowered their bombing altitude to about 25,000 ft'

**Choices:**
- he lowered their bombing altitude to about 25,000 ft ← labeled
- he grounded the daylight raids in favour of night bombing
- he ordered new heavier propellers fitted to every airframe
- he pulled the fleet back to India and cancelled the campaign

### science #3283 (T1) — off_by_number · medium

**Auditor:** Paleogeographic reconstructions place Ellesmere Island at approximately 10-15 degrees SOUTH of the paleoequator during the Late Devonian (~375 Ma); Shubin himself describes the Tiktaalik site as being near the equator, not at 30 degrees north.

**Stem:** Neil Shubin's team dug Tiktaalik out of bare tundra on southern Ellesmere Island, more than 700 miles north of the Arctic Circle, with firearms kept close for polar bears. But continents move. Where on the globe did that ground sit when Tiktaalik was alive?

**Labeled answer:** 'about 30 degrees north, the subtropical belt'

**Choices:**
- about 30 degrees north, the subtropical belt ← labeled
- about 10 degrees north, deep in the tropics
- about 60 degrees north, the cool northern belt
- about 30 degrees south, the southern subtropics

### science #3391 (T2) — wrong_answer · medium

**Auditor:** Frederick II's main practical reason for backing Tycho was astrology/horoscopes for the royal family (Tycho cast them for the king's sons), not star charts for ship navigation; celestial-navigation-driven royal observatories (Greenwich, Paris) came a century later.

**Stem:** Before big grants and government science, astronomers had to lean on rich patrons. In 1576, King Frederick II of Denmark gave the astronomer Tycho Brahe a whole island in the Oresund. He paid to build a fortress-observatory on it. What was the king's main practical reason for spending a fortune on stargazing?

**Labeled answer:** 'Accurate star charts for ship navigation'

**Choices:**
- Accurate star charts for ship navigation ← labeled
- To predict the weather two years ahead
- To find gold and silver deposits underground
- To keep track of daylight saving time

### science #3496 (T2) — dual_correct · medium

**Auditor:** '6,4,2' is a valid falsifying test of the '+2' candidate, but '50,60,70' also violates the '+2' candidate while staying increasing; a 'yes' on 50,60,70 would immediately refute '+2', making it arguably a stronger test of that specific candidate rule.

**Stem:** The 2-4-6 game was invented by the British psychologist Peter Wason. In it, he gives you a starting triple like 2, 4, 6 that fits his secret rule, and lets you propose new triples of three numbers. He tells you yes or no each time, and your job is to guess the rule. Suppose you have decided your candidate rule is 'add two each time.' All four triples below are legal to try. Which is the strongest next test of that candidate rule?

**Labeled answer:** '6, 4, 2'

**Choices:**
- 6, 4, 2 ← labeled
- 12, 14, 16
- 1, 3, 5
- 50, 60, 70

---

## trivia (1 suspects)

### trivia #668 (T5) — wrong_answer · medium

**Auditor:** The spooky storyteller (old sailor/ghost pirate) in Garfield's Halloween Adventure (1985) is voiced by C. Lindsay Workman, not Pat Carroll. C. Lindsay Workman is the distractor and is the actual correct answer; Pat Carroll (Ursula in The Little Mermaid) was not in this special.

**Stem:** The spooky storyteller in Garfield's Halloween Adventure from 1985 has been misnamed for years. Fans online often guess Orson Welles, Vincent Price, or Boris Karloff. Karloff died in 1969, so that guess is wrong. The real voice was a working actor with hundreds of small roles. Who was it?

**Labeled answer:** 'Pat Carroll'

**Choices:**
- Pat Carroll ← labeled
- C. Lindsay Workman
- John Carradine
- John Houseman

---
