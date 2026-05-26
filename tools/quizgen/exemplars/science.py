"""Science bank voice anchors (30 exemplars).

These 30 questions are the voice rule made concrete — what the Discovery
Pattern looks like in actual question form. Six anchors per tier, each
anchor hitting a specific role in the framework:

  Per tier (T1-T5):
    P1  Physics — Discovery / mechanism
    P2  Chemistry — Discovery / mechanism
    P3  Biology — Discovery / Reversal / mechanism
    P4  Earth+space — Discovery / Mystery
    P5  History+ethics+contested — Reversal / Mystery / substance
    SIG  Signature wonder (named figure + dramatic moment) — picks any pillar

All exemplars are gate-validated and serve as anchors for bulk-gen agents
when they ask "what does a good X tier Y science question look like?"

See `proposals/v2_audit/SCIENCE_FRAMEWORK.md` for the Discovery Pattern
and `proposals/v2_audit/SCIENCE_TEMPLATES.md` for stem patterns.
"""
from __future__ import annotations

# Each exemplar carries: tier, question, answer, choices, context.
# We avoid `_pillar` / `_strategy` metadata at this layer — those belong
# in generation logs, not the bank.

EXEMPLARS: list[dict] = [
    # =========================================================================
    # T1 — grade 5 — symbol-led / kid-visual / single-fact wonder
    # =========================================================================

    # T1-P1 Physics — Mechanism (drop-test)
    {
        "tier": 1,
        "question": "Drop a feather and a small rock from the same height on Earth. Which hits the floor first, and why?",
        "answer": "The rock, because air slows the feather down",
        "choices": [
            "The rock, because air slows the feather down",
            "The feather, since light things fall faster",
            "Both at once, since air has no effect",
            "Neither, since gravity ignores feathers",
        ],
        "context": "In a vacuum (no air), all objects fall at the same rate, as Apollo 15 astronauts demonstrated on the Moon by dropping a hammer and a feather together in 1971.",
    },

    # T1-P2 Chemistry — Symbol-by-vivid-example
    {
        "tier": 1,
        "question": "Gold doesn't tarnish — old gold coins pulled up from sunken ships come up shiny after centuries. What's the chemical symbol for gold?",
        "answer": "Au",
        "choices": ["Au", "Go", "Gd", "Ag"],
        "context": "Au comes from the Latin 'aurum.' Au is gold; Ag (Latin 'argentum') is silver; Gd is gadolinium. Gold's chemical resistance to corrosion is why it's used in old coinage, electronics, and dental work.",
    },

    # T1-P3 Biology — Named-discovery primer (Jenner)
    {
        "tier": 1,
        "question": "English doctor Edward Jenner noticed that milkmaids who caught cowpox did NOT get the deadly disease smallpox. What did he invent?",
        "answer": "The world's first vaccine",
        "choices": [
            "The world's first vaccine",
            "A milk-based medicine for cows",
            "A cosmetic cream from cowpox",
            "A milk-delivery business",
        ],
        "context": "In 1796 Edward Jenner inoculated 8-year-old James Phipps with cowpox material, then exposed him to smallpox — Phipps didn't get sick. The word 'vaccine' comes from 'vacca,' Latin for cow.",
    },

    # T1-P4 Earth+space — Counter-intuitive primer (sky color)
    {
        "tier": 1,
        "question": "Red and blue PAINT make purple. What color do red and blue LIGHT make when shone on a white wall?",
        "answer": "A pinkish magenta color",
        "choices": [
            "A pinkish magenta color",
            "Purple, exactly like the paint",
            "Black, the colors cancel out",
            "Green, the opposite of red-blue",
        ],
        "context": "Paint is 'subtractive' — pigments absorb wavelengths, so mixing them removes light. Light is 'additive' — colors add up to brighter. Red + blue light = magenta. Red + green = yellow. All three = white.",
    },

    # T1-P5 History+ethics — Named figure (Curie)
    {
        "tier": 1,
        "question": "Marie Curie won Nobel Prizes in TWO different sciences. What did she discover that made both possible?",
        "answer": "Polonium and radium, two radioactive elements",
        "choices": [
            "Polonium and radium, two radioactive elements",
            "The chemical symbols for gold and silver",
            "The basic shape of every cell in the body",
            "The reason iron is attracted to magnets",
        ],
        "context": "Marie Curie won Physics 1903 (with Pierre Curie and Henri Becquerel) for radioactivity and Chemistry 1911 (alone) for polonium and radium. She named polonium after Poland, her homeland. She is the only person ever Nobel'd in two different sciences.",
    },

    # T1-SIG signature wonder — Tadpole
    {
        "tier": 1,
        "question": "Frogs and salamanders start their lives in water with little tails, breathing like fish. What do we call this in-between baby form before it grows legs?",
        "answer": "A tadpole",
        "choices": [
            "A tadpole",
            "A larva-bug",
            "A guppy-frog",
            "A water-lizard",
        ],
        "context": "A tadpole is the larval stage of frogs and toads — it has gills, a tail, and lives in water. Over weeks, it grows back legs, then front legs, absorbs its tail, develops lungs, and eventually hops out as a young frog. This transformation is called metamorphosis.",
    },

    # =========================================================================
    # T2 — grade 6 — one-line scene + question, named figures introduce
    # =========================================================================

    # T2-P1 Physics — Discovery moment (Galileo pendulum)
    {
        "tier": 2,
        "question": "Walking past a Padua cathedral around 1583, the 19-year-old Galileo timed his own pulse against the swing of a hanging lamp. What pattern did he notice about how the lamp swung?",
        "answer": "Its period depended on its length, not on how heavy or how far it swung",
        "choices": [
            "Its period depended on its length, not on how heavy or how far it swung",
            "Its period got faster every minute as the chain warmed up over time",
            "Its period changed depending on the time of day and outdoor weather",
            "Its period was different for each viewer because it depended on how you looked at it",
        ],
        "context": "Galileo Galilei, then a medical student in Pisa, used his own pulse as a clock. He realized the pendulum's period (one full swing) depended on its length — the basis for accurate clocks. Christian Huygens built the first practical pendulum clock in 1656.",
    },

    # T2-P2 Chemistry — Real-application (smallpox eradication)
    {
        "tier": 2,
        "question": "Smallpox killed roughly 300 million people in the 20th century alone. In 1980 the World Health Organization announced something no other infectious disease has ever achieved. What?",
        "answer": "Smallpox had been eradicated, no longer circulating anywhere",
        "choices": [
            "Smallpox had been eradicated, no longer circulating anywhere",
            "Smallpox had been declared a fictional disease of medieval doctors",
            "Smallpox had been moved entirely into the world's oceans for storage",
            "Smallpox had been renamed to remove the stigma of an old disease term",
        ],
        "context": "The WHO smallpox eradication program ran 1967-1980. The last natural case was Ali Maow Maalin in Somalia, October 1977. WHO formally declared eradication May 8, 1980 — one of humanity's greatest public-health achievements. The virus exists only in two known secured laboratories.",
    },

    # T2-P3 Biology — Vivid mechanism (Mendel)
    {
        "tier": 2,
        "question": "In the 1860s Austrian monk Gregor Mendel grew around 28,000 pea plants and counted their traits for eight years. What rule did he find about how traits pass to offspring?",
        "answer": "Traits come in pairs, one can mask the other, but both are passed on",
        "choices": [
            "Traits come in pairs, one can mask the other, but both are passed on",
            "Children always look like the parent they spend the most time with",
            "Traits average out, so tall and short parents have a medium-height child",
            "Traits change randomly every generation with no inherited pattern at all",
        ],
        "context": "Mendel's 1866 paper described what we now call dominant and recessive alleles. The scientific community ignored his work for 34 years. It was rediscovered around 1900 by Hugo de Vries, Carl Correns, and Erich von Tschermak working independently — by then Mendel was long dead.",
    },

    # T2-P4 Earth+space — Reversal primer (Semmelweis)
    {
        "tier": 2,
        "question": "In 1847 Hungarian doctor Ignaz Semmelweis showed that doctors washing hands with chlorinated lime cut maternity-ward deaths from ~18% to ~1%. How did the Vienna medical establishment respond?",
        "answer": "They mocked him, and he was institutionalized and died in an asylum",
        "choices": [
            "They mocked him, and he was institutionalized and died in an asylum",
            "They adopted hand-washing across every hospital in Europe within months",
            "They awarded him the first medical Nobel Prize for the discovery",
            "They renamed the hospital after him and built a statue while he lived",
        ],
        "context": "Semmelweis was correct, but he couldn't explain WHY hand-washing worked — germ theory came decades later from Pasteur and Koch. Without a mechanism, his statistical evidence was rejected. He died in 1865, possibly from sepsis after being beaten by asylum guards. Vindicated posthumously when Lister extended his work to surgical antisepsis.",
    },

    # T2-P5 History+ethics — Reversal primer (Wegener)
    {
        "tier": 2,
        "question": "Alfred Wegener proposed in 1912 that Earth's continents had once been joined and slowly drifted apart. How long did mainstream geology reject his idea?",
        "answer": "About 50 years, until seafloor spreading evidence vindicated him in the 1960s",
        "choices": [
            "About 50 years, until seafloor spreading evidence vindicated him in the 1960s",
            "Just a few months, since the idea was quickly accepted in his own lifetime",
            "It was never accepted, and modern science still rejects continental drift",
            "His idea was classified by the German military for several decades",
        ],
        "context": "Wegener noted the South American and African coastlines fit together, matching fossils and rock types on both sides. He lacked a mechanism for how continents could move, and geologists rejected the idea as 'a delusion.' Harry Hess's seafloor-spreading proposal (1962) and the Vine-Matthews-Morley magnetic-stripe data finally vindicated him — by then he had been dead 30 years.",
    },

    # T2-SIG signature wonder — Marshall H. pylori
    {
        "tier": 2,
        "question": "In 1984 Australian gastroenterologist Barry Marshall, frustrated that no one believed his theory, drank a beaker of *H. pylori* bacteria himself. He developed gastritis within days. What had medicine previously taught about stomach ulcers?",
        "answer": "Ulcers were caused by stress and spicy food, not bacteria",
        "choices": [
            "Ulcers were caused by stress and spicy food, not bacteria",
            "Ulcers were caused by drinking too much water with meals",
            "Ulcers were known to be bacterial, but no one wanted to treat them",
            "Ulcers were considered purely imaginary by medical authorities",
        ],
        "context": "Marshall and Robin Warren identified *Helicobacter pylori* in ulcer biopsies in 1982. Mainstream medicine refused to consider a bacterial cause — stomach acid 'obviously' killed bacteria. Marshall drank the H. pylori culture, developed gastritis, then cured himself with antibiotics. Vindicated; he and Warren won the 2005 Nobel in Medicine.",
    },

    # =========================================================================
    # T3 — grade 7 — scene + science/history with consequence, reversals
    # =========================================================================

    # T3-P1 Physics — Mechanism (greenhouse effect physics)
    {
        "tier": 3,
        "question": "John Tyndall in 1859 used a brass tube and an infrared source to show that CO2 absorbs heat radiation — the physical basis of the greenhouse effect. The basic physics is firmly established. Why does that NOT settle the climate-policy debate?",
        "answer": "Knowing CO2 absorbs IR doesn't tell us the MAGNITUDE of warming, feedback effects, or what humans should do about it",
        "choices": [
            "Knowing CO2 absorbs IR doesn't tell us the MAGNITUDE of warming, feedback effects, or what humans should do about it",
            "Tyndall's experiment was never reproduced and modern physicists now reject it entirely",
            "CO2 absorbs IR only at certain seasons, making the original measurement meaningless",
            "The brass tube was contaminated, so the 1859 result was an experimental artifact",
        ],
        "context": "Svante Arrhenius extended Tyndall's work in 1896, calculating CO2's warming effect. The basic physics is firm. Contested questions: how much warming per doubling of CO2 (the 'climate sensitivity'), how cloud feedbacks work, what role solar/orbital cycles play, and what policy response makes sense. Settled physics ≠ settled policy.",
    },

    # T3-P2 Chemistry — Discovery + mechanism (DNA double helix)
    {
        "tier": 3,
        "question": "In 1953 James Watson, Francis Crick, and Rosalind Franklin's X-ray Photo 51 revealed DNA's structure: two strands wound into a double helix, with A always pairing with T and G with C. Why does that complementary pairing matter for what DNA does?",
        "answer": "Each strand serves as a template, so DNA can be copied exactly when a cell divides",
        "choices": [
            "Each strand serves as a template, so DNA can be copied exactly when a cell divides",
            "The helix shape lets the molecule store more atoms by weight than any other shape",
            "The pairing is coincidence with no role in copying, since DNA copies separately",
            "The pairing prevents damage from the cell's normal chemical reactions",
        ],
        "context": "Watson and Crick published their helix paper in *Nature* April 25, 1953. Franklin's Photo 51 (taken by her PhD student Raymond Gosling) was shown to Watson by Maurice Wilkins without her knowledge. Franklin died of ovarian cancer in 1958; the 1962 Nobel went only to Watson, Crick, and Wilkins (Nobels exclude posthumous awards).",
    },

    # T3-P3 Biology — Reversal full-arc (Marshall H. pylori)
    {
        "tier": 3,
        "question": "In 1984 Barry Marshall drank a beaker of *H. pylori* bacteria to prove his theory that ulcers were bacterial, not stress-caused. He developed gastritis within days, then cured himself with antibiotics. What's the broader lesson about scientific consensus?",
        "answer": "Consensus can be wrong, and an outsider's experiment can overturn decades of accepted teaching",
        "choices": [
            "Consensus can be wrong, and an outsider's experiment can overturn decades of accepted teaching",
            "Outsiders are usually wrong, and consensus among credentialed experts should not be challenged",
            "Self-experimentation is now banned in medicine and Marshall's result was therefore retracted",
            "Bacteria cause every disease, so consensus around viral causes was simply forgotten by error",
        ],
        "context": "Marshall and Warren identified *Helicobacter pylori* in ulcer biopsies in 1982. The medical mainstream refused to consider a bacterial cause — stomach acid 'obviously' killed bacteria. After self-experimentation and additional studies, they won the 2005 Nobel in Medicine. Ulcers are now routinely cured with antibiotics — a treatment unimaginable under the old stress-and-spicy-food consensus.",
    },

    # T3-P4 Earth+space — Mystery framing (dark matter)
    {
        "tier": 3,
        "question": "Galaxy rotation curves show outer stars orbiting at speeds that should fling them off — unless something invisible is holding them with gravity. Vera Rubin's measurements in the 1970s made this hard to ignore. What can we honestly say about dark matter today?",
        "answer": "It's about 27% of the universe's energy content by mass, but we have no direct detection of what it actually IS",
        "choices": [
            "It's about 27% of the universe's energy content by mass, but we have no direct detection of what it actually IS",
            "It was identified in 2018 as a specific particle and the puzzle has now been formally solved",
            "It does not exist; Rubin's measurements were retracted and modern physics rejects dark matter entirely",
            "It is exactly the same as normal matter, just colored differently and hidden behind nearby stars",
        ],
        "context": "Vera Rubin's rotation-curve measurements (1970s) showed galaxies should fly apart without additional unseen mass. Many candidate particles have been proposed (WIMPs, axions, sterile neutrinos), but no direct detection has succeeded as of the mid-2020s. Some physicists prefer modified gravity (MOND) instead. This is one of the genuine open mysteries.",
    },

    # T3-P5 History+ethics — Establishment-failure (Wegener duration)
    {
        "tier": 3,
        "question": "Alfred Wegener's 1912 continental drift hypothesis was rejected by mainstream geology for half a century. What specifically vindicated him in the 1960s?",
        "answer": "Seafloor spreading and the symmetric magnetic stripe patterns across mid-ocean ridges",
        "choices": [
            "Seafloor spreading and the symmetric magnetic stripe patterns across mid-ocean ridges",
            "Direct GPS measurements of continents drifting in real time, invented in 1962",
            "The discovery of a previously unknown ancient supercontinent in Antarctica",
            "Submarine cables broken by continental movement at predictable times each year",
        ],
        "context": "Harry Hess proposed seafloor spreading in 1962. Vine, Matthews, and Morley (1963) showed magnetic-stripe patterns on the seafloor recorded reversals of Earth's magnetic field as new ocean crust formed at the ridges — a moving conveyor belt. The pattern matched on both sides of the ridge, symmetrically, exactly as continental drift would predict. Wegener had been dead 30 years.",
    },

    # T3-SIG signature wonder — Borlaug
    {
        "tier": 3,
        "question": "Norman Borlaug spent 30 years developing dwarf wheat varieties resistant to rust disease. Mexico, India, Pakistan adopted them; harvests doubled or tripled. Population biologists estimate his work has prevented mass starvation on what scale?",
        "answer": "About one billion lives saved through increased grain production",
        "choices": [
            "About one billion lives saved through increased grain production",
            "Around ten thousand lives saved in a few specific Mexican villages",
            "Around fifty thousand lives saved among professional Olympic athletes",
            "Around two thousand lives saved at specific Norwegian research stations",
        ],
        "context": "Borlaug's dwarf wheat work in Mexico (1944-1960s) tripled Mexican yields, then spread to India and Pakistan, averting predicted famines. The 'Green Revolution' transformed global food security. Borlaug won the 1970 Nobel Peace Prize. He worked into his nineties, advocating for African agriculture and pushing back against organic-only orthodoxy that he saw as a luxury First Worlders could not afford to impose on poor nations.",
    },

    # =========================================================================
    # T4 — grade 8 — multi-sentence setup + contested-topic substance
    # =========================================================================

    # T4-P1 Physics — Failed prediction (Arctic ice)
    {
        "tier": 4,
        "question": "In 2007 former Vice President Al Gore predicted Arctic sea ice would be 'completely gone' in 5-7 years. In 2008 the BBC reported NSIDC scientists predicting an ice-free summer Arctic by 2013. Arctic September ice extent in 2013 was roughly 5 million square kilometers — not zero, not even close to a record low. What's the recognition for the kid reading future climate predictions?",
        "answer": "Specific named predictions can be checked against the record, and many high-confidence catastrophe predictions have not been confirmed when their deadlines arrived",
        "choices": [
            "Specific named predictions can be checked against the record, and many high-confidence catastrophe predictions have not been confirmed when their deadlines arrived",
            "Predictions about climate are inherently unfalsifiable and should never be challenged or verified by anyone",
            "Predictions about climate that fail are always retracted and corrected, so checking them is unnecessary",
            "Predictions about climate are only meaningful when issued by elected officials such as government leaders",
        ],
        "context": "Multiple specific Arctic ice-free predictions (2008, 2013, 2018) have failed. This does not mean climate isn't changing — it has been. It does mean that high-confidence catastrophe predictions on short timescales have a documented failure rate. Koonin's *Unsettled* (2021) collects many such cases and argues media coverage routinely overstates IPCC-report confidence.",
    },

    # T4-P2 Chemistry — Open question + bounds (abiogenesis)
    {
        "tier": 4,
        "question": "We can observe that life on Earth started at least 3.5 billion years ago — stromatolite fossils prove it. We do NOT know how. Four serious hypotheses compete: RNA-world, metabolism-first, hydrothermal-vent, and panspermia. What's the honest answer about abiogenesis?",
        "answer": "Abiogenesis is unsolved, with multiple plausible mechanisms and no decisive evidence",
        "choices": [
            "Abiogenesis is unsolved, with multiple plausible mechanisms and no decisive evidence",
            "Abiogenesis was solved by Stanley Miller's 1953 experiment, which produced living cells",
            "Abiogenesis is known to have happened once at a deep-sea vent in the Atlantic Ocean",
            "Abiogenesis has been declared unscientific by the National Academy of Sciences",
        ],
        "context": "Stanley Miller's 1953 experiment produced amino acids (the building blocks), not cells. RNA-world says self-replicating RNA preceded DNA + proteins. Metabolism-first says simple chemistry networks came first. Hydrothermal vents may have provided gradients of energy. Panspermia (life seeded from elsewhere) just pushes the question off Earth. Honest science: we don't know yet.",
    },

    # T4-P3 Biology — Contested-topic substance (1986 NCVIA)
    {
        "tier": 4,
        "question": "Congress passed the National Childhood Vaccine Injury Act in 1986, creating the Vaccine Injury Compensation Program and shielding manufacturers from most lawsuits over childhood vaccine injuries. The CDC schedule has grown from about 11 doses by age 6 in 1986 to 70+ by age 18 today. What's the structural concern critics name about the 1986 framework?",
        "answer": "Removing manufacturer liability changes incentives, since companies cannot be sued the way other drug makers can",
        "choices": [
            "Removing manufacturer liability changes incentives, since companies cannot be sued the way other drug makers can",
            "Vaccines were declared exempt from medical-ethics review by Congress with no remaining oversight at all",
            "The 1986 law made vaccines free for all children regardless of income or insurance coverage status",
            "The 1986 law specifically banned any future scientific research into vaccine safety questions",
        ],
        "context": "Pre-1986 vaccine-injury lawsuits had threatened manufacturer participation in the childhood vaccine market. The 1986 NCVIA shielded manufacturers, created VICP as a no-fault compensation system, and routed claims through a federal claims court. Critics including Robert F. Kennedy Jr. and attorney Aaron Siri argue the liability shield combined with mandate pressure weakens the normal market discipline of liability litigation. The schedule expansion is documented in CDC's published childhood immunization schedules.",
    },

    # T4-P4 Earth+space — Mechanism + history (lab leak hypothesis)
    {
        "tier": 4,
        "question": "The 'Proximal Origin' paper (Andersen et al., Nature Medicine, March 2020) declared SARS-CoV-2's origin almost certainly natural and dismissed lab leak. FOIA'd Slack messages later revealed authors PRIVATELY suspected lab leak even as they publicly dismissed it. By 2023, FBI and DOE publicly favored lab leak. What does this case illustrate?",
        "answer": "Public scientific declarations can diverge from what scientists privately think, shaped by political or institutional pressure",
        "choices": [
            "Public scientific declarations can diverge from what scientists privately think, shaped by political or institutional pressure",
            "The FBI and Department of Energy are not scientific agencies and their assessments should be discounted entirely as outsiders",
            "Lab leak has been definitively disproven by later independent studies and the Proximal Origin authors were entirely correct",
            "Slack messages obtained through FOIA are inadmissible as evidence of scientific dishonesty in any court of law",
        ],
        "context": "The Proximal Origin authors included Kristian Andersen, Eddie Holmes, and Robert Garry. The FOIA'd Slack messages and emails (released 2023) showed the authors discussing lab leak as plausible while drafting public statements that called it implausible. The paper was widely cited to label lab-leak claims 'misinformation' throughout 2020-2022. The 2023 FBI and DOE assessments did not change the COVID public-health response but changed the epistemic landscape.",
    },

    # T4-P5 History+ethics — Establishment-failure deep (Great Barrington Declaration)
    {
        "tier": 4,
        "question": "In October 2020, three epidemiologists from Stanford, Harvard, and Oxford published the Great Barrington Declaration calling for focused protection of the vulnerable rather than population-wide lockdowns. FOIA'd emails later showed NIH director Francis Collins privately called for 'a quick and devastating takedown.' What does this case illustrate?",
        "answer": "Institutional pressure can suppress credentialed scientific dissent, even from top-university researchers",
        "choices": [
            "Institutional pressure can suppress credentialed scientific dissent, even from top-university researchers",
            "The Great Barrington Declaration was withdrawn by its authors a few days after publication",
            "The signatories were not actually credentialed and were correctly dismissed by reviewers",
            "The Collins emails were never published or verified by any independent reporting source",
        ],
        "context": "Jay Bhattacharya (Stanford), Martin Kulldorff (Harvard), and Sunetra Gupta (Oxford) drafted the Declaration at the American Institute for Economic Research. FOIA-released emails (House Judiciary 2023) showed Collins emailing Anthony Fauci about the 'quick and devastating takedown' on October 8, 2020. Bhattacharya was confirmed as NIH director under the Trump administration in 2025, a vindication on the institutional stage.",
    },

    # T4-SIG signature wonder — Fleming penicillin
    {
        "tier": 4,
        "question": "In September 1928 Scottish bacteriologist Alexander Fleming returned to his lab at St Mary's Hospital after a vacation. He noticed something growing on one of his accidentally-contaminated petri dishes — a mold that had killed the staphylococcus bacteria around it. What did he name the antibiotic substance the mold produced?",
        "answer": "Penicillin — and his accidental discovery launched the antibiotic era of medicine",
        "choices": [
            "Penicillin — and his accidental discovery launched the antibiotic era of medicine",
            "Staphilicide — named after the bacteria it killed in his lab dishes",
            "Aspirin — a compound rediscovered later by a separate research team",
            "Quinine — already known but Fleming gave it the new modern name",
        ],
        "context": "Fleming's 1928 contaminated dish came from *Penicillium notatum* spores. He published in 1929 but couldn't isolate the active compound at useful scale. Howard Florey and Ernst Chain at Oxford did the hard chemistry in 1940-41. Norman Heatley scaled production. By D-Day 1944 mass-produced penicillin was saving Allied soldiers. Fleming, Florey, and Chain shared the 1945 Nobel Medicine.",
    },

    # =========================================================================
    # T5 — grade 9-10 HARD CEILING — deep history + paradox + establishment-failure
    # =========================================================================

    # T5-P1 Physics — Open question + bounds (consciousness hard problem)
    {
        "tier": 5,
        "question": "Consciousness — the felt experience of being someone — has no agreed mechanism in physics, biology, or neuroscience. Philosopher David Chalmers calls this the 'hard problem': we can explain CORRELATES (which neurons fire when you see red) but not the EXPERIENCE itself. What is the honest scientific answer about consciousness as of the mid-2020s?",
        "answer": "We don't know, with multiple serious frameworks but no decisive empirical evidence for any of them",
        "choices": [
            "We don't know, with multiple serious frameworks but no decisive empirical evidence for any of them",
            "Consciousness was solved in 2018 by a research team at MIT, and is now considered a closed scientific problem",
            "Consciousness has been declared a non-question by the philosophy community and is no longer studied at all",
            "Consciousness is identical to information processing, so every computer is conscious at some basic level",
        ],
        "context": "Giulio Tononi's Integrated Information Theory (IIT) measures consciousness via 'phi.' Bernard Baars's Global Workspace Theory locates consciousness in cross-brain broadcasting. Panpsychism (held by Galen Strawson, Philip Goff) treats consciousness as fundamental. Illusionism (Daniel Dennett, Keith Frankish) treats the 'felt experience' as itself an illusion. None has decisive empirical traction. Chalmers coined 'hard problem' in 1995.",
    },

    # T5-P2 Chemistry — Replication crisis substance (Ioannidis)
    {
        "tier": 5,
        "question": "John Ioannidis published 'Why Most Published Research Findings Are False' in PLOS Medicine in 2005, applying Bayesian reasoning to prior probabilities, statistical power, and bias. The Open Science Collaboration's 2015 reproducibility project found only about 36% of psychology studies replicated. What's the recognition skill for the kid reading a 'new study shows X' headline?",
        "answer": "A single published finding is weak evidence on its own, and replication plus effect-size matter more than the headline",
        "choices": [
            "A single published finding is weak evidence on its own, and replication plus effect-size matter more than the headline",
            "Any study published in a top journal can be safely treated as established science by readers and reporters alike",
            "Modern statistical methods guarantee reliability of every published finding without any need for replication",
            "Replication is impossible by design because every experiment is unique and cannot ever be repeated",
        ],
        "context": "The replication crisis is most severe in social psychology, with biomedical and pharmacology also affected. Pre-registration (declaring hypotheses and analyses before data collection) and the Many Labs replication projects have raised the bar. Notable failures: ego depletion, power-pose effect, Stapel fabrications (50+ retractions, 2011). Notable retractions: Surgisphere HCQ studies in The Lancet and NEJM, retracted within weeks of publication in 2020.",
    },

    # T5-P3 Biology — Eugenics history (Buck v. Bell)
    {
        "tier": 5,
        "question": "In 1927 the US Supreme Court ruled 8-1 in Buck v. Bell that compulsory sterilization of the 'feeble-minded' was constitutional. Justice Oliver Wendell Holmes wrote 'three generations of imbeciles are enough.' Carrie Buck's IQ testing was later shown to have been rigged for the case. The decision has never been formally overturned. What's the warning about science and state power?",
        "answer": "Scientific framing can lend constitutional cover to coercion, and discredited science can remain legally binding for decades",
        "choices": [
            "Scientific framing can lend constitutional cover to coercion, and discredited science can remain legally binding for decades",
            "The Supreme Court always rules correctly on scientific matters, so Buck v. Bell must in fact be a sound ruling",
            "Compulsory sterilization was outlawed by the 1950s and the Buck v. Bell precedent now has no current legal effect",
            "Eugenics was a fringe European movement that never had any influence on US law or American medical institutions",
        ],
        "context": "By 1927 Indiana had passed the first compulsory sterilization law (1907). California sterilized 20,000+ people by the 1960s. The Cold Spring Harbor Eugenics Record Office (Charles Davenport, Harry Laughlin) was funded by Carnegie and Rockefeller. Madison Grant's *The Passing of the Great Race* (1916) was called 'my bible' by Hitler. The Nazi T4 program (1939-41) explicitly modeled American precedent. The Nuremberg Code (1947) established voluntary consent as foundational. Buck v. Bell has never been overturned.",
    },

    # T5-P4 Earth+space — Mystery + bounds (dark energy)
    {
        "tier": 5,
        "question": "In 1998 two independent supernova-survey teams led by Saul Perlmutter, Brian Schmidt, and Adam Riess found the universe's expansion is ACCELERATING, not decelerating as gravity alone would predict. The unknown driver was named 'dark energy' and constitutes about 68% of the universe's energy content. What can we honestly say about dark energy in the mid-2020s?",
        "answer": "We've measured its effects precisely, but we still don't know what it IS in physical terms",
        "choices": [
            "We've measured its effects precisely, but we still don't know what it IS in physical terms",
            "Dark energy was identified as a specific known elementary particle, confirmed at CERN in 2018",
            "Dark energy was an experimental artifact that has since been refuted and is no longer a research topic",
            "Dark energy is identical to dark matter and the two are simply different names for one substance",
        ],
        "context": "Perlmutter, Schmidt, and Riess shared the 2011 Nobel in Physics for the discovery. Vacuum energy from quantum field theory predicts a cosmological constant 10^120 times larger than what we observe — the worst theoretical prediction in physics. Alternative explanations include quintessence (a dynamical field), modified gravity, or selection effects from cosmic inhomogeneities. None has decisive support. Dark energy and dark matter are separate phenomena.",
    },

    # T5-P5 History+ethics — WEF / transhumanism substance
    {
        "tier": 5,
        "question": "Yuval Noah Harari, historian and frequent World Economic Forum speaker, has publicly stated humans are now 'hackable animals' and that 'free will is over.' Klaus Schwab's Fourth Industrial Revolution (2016) and COVID-19: The Great Reset (2020) frame technological transformation as inevitable and globally coordinated. What's the recognition skill for the kid reading WEF programmatic statements?",
        "answer": "Framing a tech-political agenda as inevitable progress naturalizes it instead of examining it as a program",
        "choices": [
            "Framing a tech-political agenda as inevitable progress naturalizes it instead of examining it as a program",
            "Public statements by WEF speakers should be treated as the binding official policy of every member nation",
            "The 'hackable animals' line was never said by Harari and was fabricated by his political opponents abroad",
            "Schwab's books are works of fiction not intended to describe any actual program or policy direction",
        ],
        "context": "Harari has said the 'hackable animals' line in WEF panels and interviews. Schwab co-founded the WEF in 1971 and has run it since. The Great Reset (2020, with Thierry Malleret) explicitly framed COVID-19 as 'an opportunity' for sweeping economic-social transformation. Critics including Whitney Webb, Iain Davis, and others have documented the network's stated agenda. The recognition skill is not 'WEF is evil-controlling-everything' but rather 'inevitability framing is itself a rhetorical move worth naming.'",
    },

    # T5-SIG signature wonder — Eddington 1919 eclipse
    {
        "tier": 5,
        "question": "On May 29, 1919, British astronomer Arthur Eddington led an expedition to Príncipe (off West Africa) and Sobral (Brazil) to photograph a total solar eclipse. Einstein's 1915 general relativity predicted that gravity would bend starlight passing near the Sun by a specific amount — about 1.75 arcseconds. Newton's theory predicted half that. What did Eddington's measurements show, and what did the result do to physics?",
        "answer": "The starlight bent by approximately Einstein's predicted amount, vindicating general relativity over Newtonian gravity and making Einstein a global celebrity overnight",
        "choices": [
            "The starlight bent by approximately Einstein's predicted amount, vindicating general relativity over Newtonian gravity and making Einstein a global celebrity overnight",
            "The starlight didn't bend at all, refuting both Einstein and Newton equally and leaving physics in disarray",
            "The starlight bent by exactly Newton's predicted amount, refuting Einstein's theory of general relativity",
            "The eclipse photographs were destroyed in transit and the experiment had to be redone in 1922",
        ],
        "context": "Eddington's results were announced at a joint Royal Society and Royal Astronomical Society meeting on November 6, 1919. *The Times* of London ran the headline 'Revolution in Science — New Theory of the Universe — Newtonian Ideas Overthrown.' Modern reanalysis of the original Eddington plates has questioned how confidently the 1919 data alone could distinguish the two theories — but many later eclipses and radio-telescope measurements (especially of quasars) have confirmed Einstein's prediction with high precision.",
    },
]


__all__ = ["EXEMPLARS"]
