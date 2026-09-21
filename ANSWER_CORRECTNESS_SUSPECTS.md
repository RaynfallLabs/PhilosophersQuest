# Answer-correctness suspects — full-coverage pass

Adversarial audit of every question in the 10 non-grammar banks (plus the initial 500-sample).

**Sound so far:** 1855 · **Suspect:** 20 · **Unique suspects:** 20
**Total audited:** 1875

Each suspect requires manual verification: fix the answer text (touches choices), swap answer↔distractor, or reject the flag.

---

## ai (1 suspects)

### ai #820 (T4) — wrong_attribution · medium

**Auditor:** Hinton's post-Google interviews explicitly emphasized existential/extinction risk from superintelligent AI (10-20% chance within 30 years), not primarily near-term harms; the near-term-vs-extinction contrast with Yudkowsky is inaccurate — the actual difference is that Hinton shares extinction concerns but doesn't endorse 'shut it all down'

**Stem:** In May 2023, Geoffrey Hinton (one of the three 2018 Turing Award winners for deep learning) resigned from his decade-long role at Google. He gave interviews citing concerns about AI. How are his concerns different from Eliezer Yudkowsky's 'shut it all down' framing?

**Labeled answer:** "Hinton focuses on near-term harms like disinformation, job loss, and autonomous weapons rather than Yudkowsky's extinction framing."

**Choices:**
- Hinton focuses on near-term harms like disinformation, job loss, and autonomous weapons rather than Yudkowsky's extinction framing. ← labeled
- Hinton thinks AI poses no risk and only resigned due to a personal dispute with the search team at Google.
- Hinton wants to ban every neural network globally and replace AI with rule-based symbolic systems alone.
- Hinton and Yudkowsky hold identical views, and any reported difference is a media fabrication only.

---

## economics (16 suspects)

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

### economics #2333 (T4) — off_by_number · medium

**Auditor:** US federal outlays fell from ~$92.7B (FY1945) to ~$55.2B (FY1946), about a 40% drop — 'slightly less than half' (a distractor) is right; the two-thirds figure only holds by FY1948.

**Stem:** The end of World War II is the biggest peacetime drop in federal spending ever recorded. About how much did federal spending fall from 1945 to 1946?

**Labeled answer:** 'By more than two-thirds'

**Choices:**
- By more than two-thirds ← labeled
- By about one quarter
- By about one tenth
- By slightly less than half

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

## history (1 suspects)

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
