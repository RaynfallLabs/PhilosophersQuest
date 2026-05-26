"""Build 140 Tier-4 science questions (P1=50, P2=40, P3=50).

Voice: Discovery Pattern (named figures + specific moments; reversals;
mechanisms; failed predictions named + dated; open questions with bounds).
Stance per docs/quiz/subjects/science.md — substantive, not establishment-default.

T4 char cap 900 (grace 945). Em-dash uniform across all 4 choices.
Distractor parity ratio <= 1.30 (max/min among distractors).
Answer up to 1.6x longest distractor allowed (ANSWER_OUTLIER).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402


OUT_PATH = REPO / "_gen_science_t4_p123.json"


# ============================================================================
# P1 PHYSICS (50)
# ============================================================================

P1: list[dict] = [
    # 1 — Einstein special relativity: simultaneity / no preferred frame
    {
        "tier": 4,
        "question": "Einstein's 1905 special relativity paper rebuilt physics on two postulates: the laws of physics are the same for all observers in uniform motion, and the speed of light in vacuum is the same for every observer. From these two axioms followed several conclusions that contradict everyday intuition. What's the most famous one?",
        "answer": "Two events that one observer sees as simultaneous can be NON-simultaneous for another observer in motion — there is no universal 'now'",
        "choices": [
            "Two events that one observer sees as simultaneous can be NON-simultaneous for another observer in motion — there is no universal 'now'",
            "Two observers moving relative to each other always disagree about which of two events happened first — every time",
            "Two observers in the same frame can disagree about whether light moves at all — light has no fixed speed",
            "Two observers must share an absolute frame of reference — for the laws of physics to hold consistently",
        ],
        "context": "Einstein's 1905 'On the Electrodynamics of Moving Bodies' (Annalen der Physik) introduced special relativity. The loss of absolute simultaneity is the deepest counter-intuitive consequence — along with time dilation, length contraction, and E = mc^2 (added later that year in a separate paper). The theory replaced Newtonian absolute space and time.",
    },
    # 2 — General relativity 1915 light-bending
    {
        "tier": 4,
        "question": "Einstein finished general relativity in November 1915, giving gravity a new geometric interpretation: massive objects curve the geometry of spacetime itself, and other objects move along the curves. A famous test prediction was that starlight passing close to the Sun would bend by a specific amount. What did Eddington's 1919 eclipse expedition find?",
        "answer": "The starlight bent by roughly the amount Einstein predicted — about twice what Newton's theory predicted — making Einstein a global celebrity",
        "choices": [
            "The starlight bent by roughly the amount Einstein predicted — about twice what Newton's theory predicted — making Einstein a global celebrity",
            "The starlight bent by exactly the amount Newton predicted — relativity was discarded as a flawed mathematical exercise",
            "The starlight did not bend at all — both Newton and Einstein were apparently incorrect — leaving gravity unexplained",
            "The starlight bent in the wrong direction — confirming neither theory — and the experiment had to be repeated later",
        ],
        "context": "Eddington led expeditions to Príncipe and Sobral for the May 29, 1919 total eclipse. Results announced November 6, 1919 at a joint Royal Society / RAS meeting. Modern reanalysis has questioned whether the 1919 plates alone could clearly distinguish the predictions, but many later eclipses, radio measurements of quasars, and Cassini spacecraft tests have confirmed Einstein's prediction with high precision.",
    },
    # 3 — Photoelectric effect: Einstein's Nobel was NOT for relativity
    {
        "tier": 4,
        "question": "Einstein won the 1921 Nobel Prize in Physics. Many people assume it was for relativity, but the citation specifically named a different paper from his 1905 'miracle year' that helped launch quantum mechanics. Light shining on certain metals knocks electrons loose only above a threshold frequency — not by brightness alone. What did Einstein's explanation propose?",
        "answer": "Light comes in discrete energy packets ('quanta', later 'photons') with energy proportional to frequency — so dim violet light can eject electrons but bright red light cannot",
        "choices": [
            "Light comes in discrete energy packets ('quanta', later 'photons') with energy proportional to frequency — so dim violet light can eject electrons but bright red light cannot",
            "Light pressure pushes electrons mechanically off the metal surface — so the brighter the lamp, the more electrons fly out from any color",
            "Light heats the metal until thermal vibration shakes electrons free — so a hot enough source of any color will eject them eventually",
            "Light triggers a chemical reaction in the metal surface — so any wavelength can knock electrons out once the metal is dirty enough",
        ],
        "context": "Einstein's 1905 photoelectric paper extended Max Planck's 1900 quantum hypothesis (which Planck himself called a 'desperate' mathematical trick) to light itself. Robert Millikan's experiments through 1916 confirmed Einstein's formula despite Millikan's own skepticism. The Nobel committee gave Einstein the 1921 prize specifically for this — relativity was still considered too controversial.",
    },
    # 4 — Heisenberg uncertainty principle
    {
        "tier": 4,
        "question": "Werner Heisenberg in 1927 published a principle that's often misquoted as 'the observer affects what's observed.' The actual claim is sharper and weirder: certain pairs of physical quantities — position and momentum, for instance — cannot both have precise values at the same time, regardless of who's measuring or how. What's the correct reading?",
        "answer": "It's a fundamental property of nature — the more precisely position is defined, the less precisely momentum is defined, and vice versa, independent of measurement skill",
        "choices": [
            "It's a fundamental property of nature — the more precisely position is defined, the less precisely momentum is defined, and vice versa, independent of measurement skill",
            "It's just a limit of current instruments — better tools in the future will eventually pin down both position and momentum at once for any particle",
            "It only applies to subatomic particles that humans actively touch — particles that no one looks at have well-defined positions and momenta at all times",
            "It says all measurements are equally uncertain — quantum mechanics rejects the very idea of precise values for any quantity at all",
        ],
        "context": "The uncertainty principle is not about clumsy measurement; it's about what 'position' and 'momentum' mean for quantum objects. Mathematically it follows from the non-commuting operators in the formalism. Bohr emphasized this against Heisenberg's earlier 'gamma-ray microscope' framing, which made it sound like a measurement disturbance — a reading that has persisted in popular accounts ever since.",
    },
    # 5 — Bohr atom 1913
    {
        "tier": 4,
        "question": "Niels Bohr in 1913 proposed a model of the hydrogen atom in which electrons orbit the nucleus only in specific allowed orbits, jumping between them by absorbing or emitting a photon of just the right energy. The model successfully predicted hydrogen's spectral lines. Why was it eventually replaced by full quantum mechanics in the 1920s?",
        "answer": "It worked for hydrogen but failed for atoms with more than one electron — and it gave no deeper reason WHY the orbits were quantized, only that they were",
        "choices": [
            "It worked for hydrogen but failed for atoms with more than one electron — and it gave no deeper reason WHY the orbits were quantized, only that they were",
            "It predicted spectral lines that turned out not to exist — every prediction Bohr made was experimentally falsified within five years of publication",
            "It was disproven by Einstein's 1905 photoelectric paper — Bohr's model contradicted the existence of photons that Einstein had already established",
            "It was replaced because Bohr later retracted the model — admitting in 1919 he had fabricated the spectral-line predictions to win acclaim",
        ],
        "context": "Bohr's 1913 model was a triumph for hydrogen but couldn't handle helium or any heavier element. Schrödinger's 1926 wave equation and Heisenberg's 1925 matrix mechanics (mathematically equivalent) replaced the picture of orbits with probability distributions. Bohr himself helped develop the new framework — he wasn't attached to the orbit picture, only to the underlying quantization insight.",
    },
    # 6 — Double-slit experiment
    {
        "tier": 4,
        "question": "Thomas Young in 1801 fired light through two narrow slits onto a screen and saw bands of light and dark — an interference pattern proving light behaves like a wave. The same experiment was later done with electrons, atoms, even large molecules. What's the strangest result with single particles?",
        "answer": "Even firing one particle at a time, the interference pattern still builds up — as if each particle goes through BOTH slits and interferes with itself",
        "choices": [
            "Even firing one particle at a time, the interference pattern still builds up — as if each particle goes through BOTH slits and interferes with itself",
            "Single particles always go through exactly one slit — there is no interference pattern at all when firing them slowly enough to count",
            "Single particles produce a uniform glow on the screen — no bands appear when particles are sent through one at a time in sequence",
            "Single particles bounce back from the slits entirely — no detection ever occurs on the far side when only one is sent in",
        ],
        "context": "The single-particle double-slit experiment was first done with electrons by Claus Jönsson in 1961 and famously confirmed with single electrons by Akira Tonomura's team in 1989. Larger objects (buckyballs, then molecules of 25,000 amu by 2019) also show the pattern. Feynman called the double-slit 'the heart of quantum mechanics' and 'the only mystery.'",
    },
    # 7 — Schrödinger cat 1935
    {
        "tier": 4,
        "question": "Erwin Schrödinger published his cat thought experiment in 1935 not to defend the idea but to attack it. A cat is sealed in a box with a radioactive atom that has a 50% chance of decaying and triggering poison. Quantum mechanics says — until we open the box — the atom is in a superposition of decayed and not-decayed. What was Schrödinger's actual point?",
        "answer": "It was a critique — Schrödinger thought the conclusion (a cat both alive AND dead at once) was absurd, showing something was off in the Copenhagen interpretation",
        "choices": [
            "It was a critique — Schrödinger thought the conclusion (a cat both alive AND dead at once) was absurd, showing something was off in the Copenhagen interpretation",
            "It was a defense — Schrödinger meant to prove cats really do exist in two states at once — endorsing his own wave-equation interpretation",
            "It was a demonstration — Schrödinger meant to show that radioactive decay is fully predictable — making the cat's state never uncertain",
            "It was a joke — Schrödinger meant a swipe at Einstein — claiming relativity prevented cats from ever being in any quantum superposition",
        ],
        "context": "Schrödinger's 1935 paper 'The Present Situation in Quantum Mechanics' coined the cat scenario as a reductio ad absurdum. He and Einstein were the prominent critics of the Copenhagen interpretation (Bohr, Heisenberg, Born). Modern interpretations — Many-Worlds (Everett 1957), decoherence theory, Bohmian mechanics, QBism — handle the cat differently, but the original intent was a complaint, not an endorsement.",
    },
    # 8 — EPR paradox + Aspect experiments + 2022 Nobel
    {
        "tier": 4,
        "question": "Einstein, Podolsky, and Rosen in 1935 argued quantum mechanics must be incomplete — imagining two entangled particles that, once separated, seemed to influence each other instantly across any distance. Einstein called this 'spooky action at a distance.' What did Alain Aspect's 1980s experiments — recognized with the 2022 Physics Nobel — actually show?",
        "answer": "Entanglement is real — measurements on one particle DO correlate instantly with its partner — Einstein's local-hidden-variable expectation is empirically wrong",
        "choices": [
            "Entanglement is real — measurements on one particle DO correlate instantly with its partner — Einstein's local-hidden-variable expectation is empirically wrong",
            "Einstein was right after all — Aspect's experiments confirmed that no spooky correlations occur between distant particles when measured carefully",
            "Entanglement was a measurement error — Aspect's results were retracted after closer scrutiny of the instruments used in the original work",
            "Quantum mechanics turned out to be local — Aspect's data showed particles communicate through ordinary hidden mechanical forces",
        ],
        "context": "John Bell in 1964 derived testable inequalities that distinguish local-hidden-variable theories from quantum mechanics. Aspect's 1981-82 experiments at Orsay (with Dalibard and Roger) violated Bell's inequalities by a wide margin. Anton Zeilinger and John Clauser extended the work with tighter loophole closures. The 2022 Nobel went to Clauser, Aspect, and Zeilinger.",
    },
    # 9 — Standard Model intro: quarks, leptons, Higgs
    {
        "tier": 4,
        "question": "The Standard Model of particle physics describes matter as built from two kinds of fundamental fermions: quarks (which combine into protons, neutrons, and other 'hadrons') and leptons (the electron, muon, tau, and their neutrinos). It also includes force-carrying bosons. What was the last major piece to be experimentally confirmed?",
        "answer": "The Higgs boson — predicted in 1964 by Peter Higgs and others, finally detected at CERN's Large Hadron Collider in July 2012 — completing the Standard Model's particle roster",
        "choices": [
            "The Higgs boson — predicted in 1964 by Peter Higgs and others, finally detected at CERN's Large Hadron Collider in July 2012 — completing the Standard Model's particle roster",
            "The top quark — predicted in 1964 by Murray Gell-Mann, confirmed at Fermilab in 1972 — closing out the Standard Model's particle inventory entirely",
            "The neutrino — predicted by Wolfgang Pauli in 1930 and detected by Cowan and Reines in 2010 — sealing the final gap in the model",
            "The tau lepton — predicted in 1964 by Steven Weinberg, confirmed in 2015 at CERN — finally completing the Standard Model's family tree",
        ],
        "context": "The Higgs field gives elementary particles their masses by interacting with them at different strengths. ATLAS and CMS, the two main LHC experiments, jointly announced discovery on July 4, 2012. Peter Higgs and François Englert shared the 2013 Physics Nobel. The Standard Model remains the most precisely tested theory in science; it nevertheless leaves dark matter, dark energy, and gravity unexplained.",
    },
    # 10 — Third law of thermodynamics
    {
        "tier": 4,
        "question": "Walther Nernst formulated the third law of thermodynamics in 1906: as temperature approaches absolute zero (-273.15°C or 0 K), the entropy of a perfect crystal approaches zero. A practical consequence followed that is sometimes called the 'unattainability principle.' What is it?",
        "answer": "Absolute zero can be approached but never actually reached — no finite sequence of cooling steps can bring a system all the way to 0 K",
        "choices": [
            "Absolute zero can be approached but never actually reached — no finite sequence of cooling steps can bring a system all the way to 0 K",
            "Absolute zero was reached in a Boulder lab in 1995 — Nernst's law was overturned by the achievement of negative temperatures",
            "Absolute zero is the same as room temperature for perfectly crystalline materials — Nernst's law applies only to gases that are not crystals",
            "Absolute zero defines the highest temperature any object can ever achieve — Nernst's law sets the maximum entropy any system can hold",
        ],
        "context": "Modern laser-cooling and dilution-refrigerator techniques get within nanokelvins of absolute zero — close enough for Bose-Einstein condensates (first achieved 1995 by Cornell, Wieman, Ketterle — 2001 Nobel) — but the third law forbids actually reaching 0 K. Negative-temperature systems (Ramsey 1956) are a separate phenomenon: they're 'hotter' than infinite temperature, not 'colder' than absolute zero.",
    },
    # 11 — Carnot engine max efficiency
    {
        "tier": 4,
        "question": "Sadi Carnot in 1824 — son of a French Revolutionary general, dead at 36 from cholera — wrote a short book arguing that even an ideal frictionless heat engine has a hard upper limit on efficiency. The limit depends only on the hot and cold reservoir temperatures. Why does this matter for real power plants, refrigerators, and engines?",
        "answer": "No real engine can do better than Carnot's limit — energy efficiency has a thermodynamic ceiling no amount of engineering cleverness can break",
        "choices": [
            "No real engine can do better than Carnot's limit — energy efficiency has a thermodynamic ceiling no amount of engineering cleverness can break",
            "Carnot's limit applies only to steam engines from the 1820s — modern engines using electricity are exempt from his analysis entirely",
            "Carnot's limit was disproven by the perpetual motion machine patented in Sweden in 1956 — efficient engines can now reach 100% efficiency",
            "Carnot's limit affects only refrigerators, not engines — heat moves freely in any direction without thermodynamic penalty",
        ],
        "context": "Carnot's 'Reflections on the Motive Power of Fire' (1824) preceded the formal first and second laws by decades — but in retrospect, his argument is a clean derivation of the second law for engines. Maximum efficiency = 1 - (T_cold / T_hot), with temperatures in Kelvin. A coal plant with steam at 800 K exhausting to 300 K caps at ~62% — real plants achieve about 33-45%. Heat-pump physics (refrigerators run in reverse) follows the same logic.",
    },
    # 12 — Hubble + redshift expansion
    {
        "tier": 4,
        "question": "Edwin Hubble in 1929 published Mount Wilson 100-inch telescope observations showing distant galaxies' spectral lines were shifted toward the red end of the spectrum — and the redshift was larger for more distant galaxies. Vesto Slipher had measured shifts earlier; Hubble added the distance scale. What does the redshift-distance relationship imply?",
        "answer": "The universe is expanding — space itself stretches between galaxies, so light traveling through stretching space gets stretched to longer wavelengths the farther it has traveled",
        "choices": [
            "The universe is expanding — space itself stretches between galaxies, so light traveling through stretching space gets stretched to longer wavelengths the farther it has traveled",
            "Distant galaxies are slowly cooling and turning red — their stars literally change color as they age, with farther galaxies being older and redder",
            "Photons from distant galaxies hit cosmic dust on the way — and dust absorbs blue light selectively, making farther galaxies look reddish",
            "Distant galaxies are moving toward Earth at high speed — and Doppler shift compresses the wavelengths into the red part of the spectrum",
        ],
        "context": "Hubble's 1929 paper credited Slipher's redshift measurements; the velocity-distance slope (now 'Hubble's constant') was Hubble's. Lemaître had derived the expanding-universe prediction in 1927 from general relativity. Expansion is not motion 'through' space — it's expansion OF space between galaxies. Local gravity overrides expansion at small scales.",
    },
    # 13 — CMB Penzias + Wilson 1964
    {
        "tier": 4,
        "question": "In 1964 Arno Penzias and Robert Wilson at Bell Labs were trying to use a radio horn antenna for satellite communication. They couldn't get rid of a persistent low-level microwave hiss coming from every direction in the sky — even after cleaning out pigeon droppings from the antenna. They had accidentally found something enormous. What?",
        "answer": "The cosmic microwave background — afterglow radiation from when the universe was about 380,000 years old — predicted by Big Bang theorists and now confirmed",
        "choices": [
            "The cosmic microwave background — afterglow radiation from when the universe was about 380,000 years old — predicted by Big Bang theorists and now confirmed",
            "Solar microwave emission — overflow radiation from the Sun's corona — finally measured by Penzias and Wilson with extreme precision",
            "Earth's own microwave field — an atmospheric heating signature predicted decades earlier — now first measured by Bell Labs",
            "Background interference from human radio broadcasting — accidental detection of regional commercial-station leakage",
        ],
        "context": "Robert Dicke's group at Princeton was about to build an antenna for the CMB; Penzias and Wilson called Dicke once they understood what they had. Penzias and Wilson shared the 1978 Nobel; Dicke and his team did not. Later satellites (COBE, WMAP, Planck) mapped the CMB in detail.",
    },
    # 14 — Dark energy 1998
    {
        "tier": 4,
        "question": "In 1998 two teams led by Saul Perlmutter (Berkeley) and Brian Schmidt + Adam Riess (Mount Stromlo / Space Telescope Science Institute) independently measured Type Ia supernovae as cosmic distance markers. They expected to find the universe's expansion was slowing — pulled back by gravity. What did they actually find?",
        "answer": "The expansion is ACCELERATING — distant supernovae were dimmer (and so farther) than gravity-only models predicted — implying an unknown 'dark energy' driving expansion ever faster",
        "choices": [
            "The expansion is ACCELERATING — distant supernovae were dimmer (and so farther) than gravity-only models predicted — implying an unknown 'dark energy' driving expansion ever faster",
            "The expansion has reversed direction — the universe is contracting, with distant galaxies racing back toward each other at high speed",
            "The expansion is steady and unchanging — supernovae confirmed perfect uniform motion without any acceleration or deceleration at all",
            "The expansion has fully stopped — supernovae beyond a certain distance appear at fixed brightness because the universe is locally static",
        ],
        "context": "Perlmutter, Schmidt, and Riess shared the 2011 Physics Nobel. 'Dark energy' is now estimated at about 68% of the universe's energy content; dark matter ~27%; ordinary matter ~5%. What dark energy IS remains unknown — a cosmological constant (Einstein's reluctant 1917 addition, later 'biggest blunder' for him), quintessence (a dynamical field), or modified gravity are all live possibilities.",
    },
    # 15 — Time dilation: GPS practical consequence
    {
        "tier": 4,
        "question": "GPS satellites orbit at about 20,200 km altitude, moving roughly 14,000 km/h. Special relativity says their on-board clocks tick slightly SLOWER than ground clocks; general relativity says they tick slightly FASTER because they're higher in Earth's gravitational well. Without correction, GPS would be useless within minutes. How much daily?",
        "answer": "The general-relativistic speedup wins — about 38 microseconds per day net — and GPS uses Einstein's equations to correct it, or positions drift by about 10 km daily",
        "choices": [
            "The general-relativistic speedup wins — about 38 microseconds per day net — and GPS uses Einstein's equations to correct it, or positions drift by about 10 km daily",
            "Special-relativistic slowdown wins — by roughly half a second per day — but GPS would still work perfectly without any correction at all",
            "The two effects cancel by design — and relativity is not used in GPS engineering, only in physics textbook examples on the topic",
            "Relativistic effects are too small to matter for GPS — clocks differ by mere nanoseconds per year, so corrections are unnecessary",
        ],
        "context": "The 38-microsecond figure is +45 μs/day GR speedup minus -7 μs/day SR slowdown. Each microsecond of timing error translates to roughly 300 m of position error since signals travel at light speed. GPS designers built relativistic corrections directly into satellite clock-rate adjustments.",
    },
    # 16 — Antimatter Dirac 1928 prediction + 1932 Anderson
    {
        "tier": 4,
        "question": "Paul Dirac in 1928 wrote down a relativistic wave equation for the electron. The equation had a strange property: not one set of solutions but TWO — one for the ordinary electron, one for a particle with the same mass but OPPOSITE charge. Dirac at first dismissed the second set as a mathematical artifact. What changed his mind?",
        "answer": "Carl Anderson at Caltech in 1932 photographed cosmic-ray tracks curving the wrong way in a magnetic field — confirming the positron, the electron's antimatter twin",
        "choices": [
            "Carl Anderson at Caltech in 1932 photographed cosmic-ray tracks curving the wrong way in a magnetic field — confirming the positron, the electron's antimatter twin",
            "Dirac himself observed positrons in his lab the next year — confirming his own prediction through a tabletop experiment with simple magnets and screens",
            "Rutherford rebuilt the gold-foil experiment to test Dirac's equation — finding protons sometimes scatter as antimatter under certain rare conditions",
            "Einstein's correspondence convinced Dirac the equation must be correct — no experiment was needed for the antimatter prediction to be accepted",
        ],
        "context": "Anderson observed the curling track in a cloud chamber on August 2, 1932, and called the new particle the 'positron.' Dirac and Anderson won Nobels (Dirac 1933, Anderson 1936). Anti-protons (1955), anti-neutrons (1956), and trapped anti-hydrogen (CERN 2011) followed. The matter-antimatter asymmetry of the universe remains an open problem.",
    },
    # 17 — Pulsars 1967 Jocelyn Bell Burnell
    {
        "tier": 4,
        "question": "In November 1967, Cambridge graduate student Jocelyn Bell Burnell noticed an unusual repeating radio signal in her data — pulsing precisely every 1.337 seconds. She and her supervisor Antony Hewish briefly labeled the source 'LGM-1' for 'little green men' before identifying what it really was. What had she found?",
        "answer": "A pulsar — a rapidly rotating neutron star whose beamed radio emission sweeps past Earth like a lighthouse — opening a new field of astrophysics",
        "choices": [
            "A pulsar — a rapidly rotating neutron star whose beamed radio emission sweeps past Earth like a lighthouse — opening a new field of astrophysics",
            "A nearby planet — orbiting a small dim star and reflecting radio waves predictably every 1.337 seconds of its short year",
            "A satellite mistakenly broadcasting on a scientific frequency — the precise repetition came from accidental ground-controlled radio testing",
            "An interference signal from a faulty Cambridge cable — the equipment had been incorrectly grounded for the previous several months",
        ],
        "context": "Bell Burnell's discovery is a famous case of credit politics — Antony Hewish received the 1974 Physics Nobel (with Martin Ryle) for 'his' decisive role in the discovery of pulsars, while Bell Burnell received nothing. The Nobel committee was widely criticized. Bell Burnell has been gracious about it her entire career, donating her later prize money (the $3 million Breakthrough Prize in 2018) to fund minority and refugee students in physics.",
    },
    # 18 — Black hole event horizon / Schwarzschild radius
    {
        "tier": 4,
        "question": "Karl Schwarzschild — serving on the Russian front in WWI — solved Einstein's general relativity equations in 1916 for a spherical mass. For any mass M, he found a critical radius (the 'Schwarzschild radius') such that if M is inside, nothing escapes — not even light. Schwarzschild died on the front months later. What's the mass-radius relationship?",
        "answer": "The Schwarzschild radius is proportional to the mass — about 3 km per solar mass — so a black hole the mass of the Sun has an event horizon roughly 6 km across",
        "choices": [
            "The Schwarzschild radius is proportional to the mass — about 3 km per solar mass — so a black hole the mass of the Sun has an event horizon roughly 6 km across",
            "The Schwarzschild radius is inversely proportional to mass — heavier objects have smaller horizons — so big stars never form black holes at all",
            "The Schwarzschild radius depends on charge but not on mass — only electrically charged objects can become black holes regardless of how heavy",
            "The Schwarzschild radius scales with the square of the mass — doubling the mass quadruples the horizon — so black holes reach galaxy size quickly",
        ],
        "context": "The Schwarzschild solution describes a non-rotating uncharged black hole. The 'horizon' is a one-way membrane — once inside, light cannot escape because curvature is so severe all forward-pointing paths lead deeper in. Stellar black holes form from massive-star collapse; supermassive black holes (Sgr A*, M87*) sit at galactic centers.",
    },
    # 19 — LIGO gravitational waves 2015
    {
        "tier": 4,
        "question": "In September 2015 the LIGO observatories — twin laser interferometers in Louisiana and Washington state — detected a tiny ripple in their 4-km arms lasting about 200 milliseconds. The signal matched the predicted waveform for two black holes spiraling together and merging. What did this detection finally confirm?",
        "answer": "Gravitational waves — distortions in spacetime predicted by Einstein in 1916 — exist and can be measured, opening a new way to observe distant astrophysical events",
        "choices": [
            "Gravitational waves — distortions in spacetime predicted by Einstein in 1916 — exist and can be measured, opening a new way to observe distant astrophysical events",
            "Magnetic-monopole signals — particles predicted in 1931 by Dirac — were finally measured by an Earth-based detector for the first time",
            "Higgs-field oscillations — distinct from the Higgs boson — were directly detected by LIGO after CERN missed them in 2012",
            "Aether waves — predicted by Michelson and Morley in 1887 — were finally captured after over a century of unsuccessful attempts",
        ],
        "context": "The September 14, 2015 event was named GW150914 — two black holes of roughly 36 and 29 solar masses merging about 1.3 billion light-years away. About 3 solar masses of energy went into gravitational radiation in a fraction of a second. The 2017 Physics Nobel went to Rainer Weiss, Kip Thorne, and Barry Barish for the LIGO detection. Subsequent events include the August 2017 neutron-star merger seen in both gravitational waves and electromagnetic light.",
    },
    # 20 — Faraday's law / Maxwell unification
    {
        "tier": 4,
        "question": "Michael Faraday in 1831 showed that a changing magnetic field induces an electric current in a nearby wire — and a current in a wire produces a magnetic field. James Clerk Maxwell in the 1860s wrote down four equations that pulled together everything known about electricity and magnetism. What surprise emerged from Maxwell's equations?",
        "answer": "Light itself is an electromagnetic wave — the equations predicted a wave traveling at exactly the measured speed of light, unifying optics with electricity and magnetism",
        "choices": [
            "Light itself is an electromagnetic wave — the equations predicted a wave traveling at exactly the measured speed of light, unifying optics with electricity and magnetism",
            "Magnets cancel electricity — Maxwell's equations showed the two forces are opposites that must be kept entirely separate in any working device",
            "Electricity travels at infinite speed — Maxwell's equations made instant-action-at-a-distance the default for all electromagnetic phenomena",
            "Magnetism arises from gravity alone — Maxwell's equations reduced all electromagnetic effects to small variations in Newton's gravity equation",
        ],
        "context": "Maxwell's 'A Treatise on Electricity and Magnetism' was published in 1873. Heinrich Hertz experimentally confirmed electromagnetic waves in 1887, generating and detecting radio waves at the predicted speed of light. The unification of optics and electromagnetism is one of the great theoretical achievements of 19th-century physics — and the speed-of-light invariance Maxwell's equations imply was a clue that pointed Einstein toward special relativity.",
    },
    # 21 — Conservation of energy: Joule mechanical equivalent of heat
    {
        "tier": 4,
        "question": "James Joule in the 1840s — son of a Manchester brewer, working in his family's brewery lab — measured how much paddle-wheel work, stirred through water, would heat a given mass by one degree. Refined over decades, his result established a precise conversion: mechanical work and heat are forms of the same thing. What law did this help establish?",
        "answer": "The first law of thermodynamics — energy is conserved, with heat and mechanical work as interconvertible forms — total energy in a closed system stays constant",
        "choices": [
            "The first law of thermodynamics — energy is conserved, with heat and mechanical work as interconvertible forms — total energy in a closed system stays constant",
            "The first law of motion — Newton's principle that objects keep moving unless acted on by a force — completing Newton's analysis a century later",
            "The first law of optics — light moves in straight lines in uniform media — finally given experimental backing for the first known time",
            "The first law of chemistry — mass is conserved in reactions — first formally stated by Joule's mechanical-equivalent experiments",
        ],
        "context": "Joule's paddle-wheel apparatus (1845) and his later refined experiments set the modern value at about 4.18 joules per calorie. The unit 'joule' is named after him. Mayer, Helmholtz, and Joule independently developed energy conservation around the same time.",
    },
    # 22 — Entropy / second law
    {
        "tier": 4,
        "question": "Rudolf Clausius in 1865 introduced the word 'entropy' to capture a quantity that — unlike energy — is not conserved. In an isolated system, entropy never decreases. Why is the second law of thermodynamics sometimes called the most cosmically depressing law in physics?",
        "answer": "It defines time's arrow — closed systems progress only toward greater disorder — implying eventual 'heat death' as the universe runs down to uniform temperature",
        "choices": [
            "It defines time's arrow — closed systems progress only toward greater disorder — implying eventual 'heat death' as the universe runs down to uniform temperature",
            "It says energy steadily increases without bound — closed systems become hotter forever — leading to an infinite-temperature crisis in cosmology",
            "It says particles eventually stop moving entirely — leaving the universe frozen in a perfect grid pattern after enough time has passed",
            "It says heat always flows from cold objects to hot objects spontaneously — eventually concentrating all energy in a single point of light",
        ],
        "context": "Boltzmann gave entropy its statistical interpretation — S = k log W — connecting it to the number of microscopic configurations consistent with the macroscopic state. Living systems decrease their own local entropy by increasing entropy of their surroundings. The universe's eventual heat death is the standard prediction, though some cosmological scenarios (eternal inflation, cyclic universes) push back against it.",
    },
    # 23 — Brownian motion 1905 Einstein
    {
        "tier": 4,
        "question": "Robert Brown in 1827 noticed that pollen grains suspended in water jiggled erratically under a microscope — a movement that wouldn't stop and didn't depend on the pollen being alive. Almost 80 years later Einstein, in another paper from his 1905 miracle year, gave a quantitative explanation. What was Einstein's contribution?",
        "answer": "He showed the jiggling was caused by water molecules bumping the pollen — providing some of the strongest indirect evidence atoms exist, in an era when atoms were still controversial",
        "choices": [
            "He showed the jiggling was caused by water molecules bumping the pollen — providing some of the strongest indirect evidence atoms exist, in an era when atoms were still controversial",
            "He showed the jiggling was a kind of electrical effect — proving that pollen grains store and release small charges through invisible currents",
            "He showed the jiggling was an optical illusion of microscopy — disproving the existence of molecules and discrediting Brown's original observations",
            "He showed the jiggling came from gravitational waves — providing the first direct evidence that gravity propagates in detectable ripples",
        ],
        "context": "Einstein's 1905 Brownian-motion paper gave predictions for how the jiggle's size and frequency should depend on temperature, fluid viscosity, and particle size. Jean Perrin's careful experiments (1908-1909) confirmed Einstein's predictions, and the broader scientific community finally accepted that atoms are physically real. Perrin won the 1926 Physics Nobel partly for this confirmation; Einstein had already won (for the photoelectric effect, 1921).",
    },
    # 24 — Relativity twin paradox
    {
        "tier": 4,
        "question": "The 'twin paradox' from special relativity: one twin stays on Earth while the other rockets off at near light-speed to a distant star and returns. Each twin sees the OTHER twin's clock running slow. Yet when they meet again, one is genuinely younger. Why does the symmetry break in favor of the traveler being younger?",
        "answer": "Only the traveling twin accelerates and turns around — that asymmetric acceleration breaks the symmetry, so the traveling twin really does experience less time",
        "choices": [
            "Only the traveling twin accelerates and turns around — that asymmetric acceleration breaks the symmetry, so the traveling twin really does experience less time",
            "Neither twin actually ages differently — the paradox is purely mathematical, and they end up the same age in any real test situation",
            "The Earth twin is younger after the reunion — gravity on Earth slows time more than the rocket's high speed slows time on the trip",
            "The result depends on who is observing — different observers see different twins as younger, with no objective answer for the reunion",
        ],
        "context": "Real experiments with airborne atomic clocks (Hafele-Keating 1971) and muons in particle accelerators have measured the time-dilation effect directly. Travel close to light-speed isn't yet feasible for humans, but the principle is firm. The 'paradox' isn't actually a paradox — it just feels like one if you forget that the two twins' worldlines are physically different shapes in spacetime.",
    },
    # 25 — Doppler effect for sound and light
    {
        "tier": 4,
        "question": "Christian Doppler in 1842 predicted that a wave's observed frequency depends on the relative motion of source and observer — a train whistle sounds higher as it approaches, lower as it recedes. Within a few years sound experiments confirmed it. What's the analogous effect for light?",
        "answer": "Light from sources moving away is shifted toward longer (redder) wavelengths, and from sources moving toward us toward shorter (bluer) wavelengths — the basis of redshift astronomy",
        "choices": [
            "Light from sources moving away is shifted toward longer (redder) wavelengths, and from sources moving toward us toward shorter (bluer) wavelengths — the basis of redshift astronomy",
            "Light's wavelength is unchanged by source motion — the Doppler effect applies only to sound waves, not to electromagnetic radiation of any kind",
            "Light gets brighter as the source approaches and dimmer as it recedes — but wavelength stays fixed regardless of relative motion",
            "Light's frequency depends only on temperature — Doppler shifts are an artifact of measurement and disappear at sufficiently high precision",
        ],
        "context": "Doppler's 1842 paper predicted both effects from a single wave-motion analysis. Christophorus Buys Ballot tested it with sound (railway-mounted trumpeters in the Netherlands, 1845) and confirmed Doppler's predictions. The light analogue, applied to stellar spectra by William Huggins from the 1860s, eventually enabled Hubble's expansion discovery. Police radar and weather radar are everyday Doppler-effect technologies.",
    },
    # 26 — Particle accelerators: CERN LHC purpose
    {
        "tier": 4,
        "question": "CERN's Large Hadron Collider near Geneva accelerates protons to near light-speed around a 27-km ring, slams them into other proton beams, and watches the debris. The 2012 Higgs discovery was its headline achievement. What's the broader physics motivation for building accelerators ever larger and more powerful?",
        "answer": "Higher collision energies probe smaller distance scales — letting physicists test whether the Standard Model holds, or whether new particles and forces appear at energies we couldn't previously reach",
        "choices": [
            "Higher collision energies probe smaller distance scales — letting physicists test whether the Standard Model holds, or whether new particles and forces appear at energies we couldn't previously reach",
            "Higher collision energies generate fusion power — the LHC's primary purpose is electricity generation for the European grid in winter months",
            "Higher collision energies are used solely for medical isotope production — CERN's research role is officially closed since 2018 by policy mandate",
            "Higher collision energies sterilize cosmic rays — accelerators were built to clean Earth's upper atmosphere of unwanted radiation",
        ],
        "context": "The Higgs discovery confirmed the Standard Model but the model itself is known to be incomplete — it doesn't include gravity, dark matter, dark energy, or explain why fundamental constants take the specific values they do. Proposed successors (the FCC at CERN, the CEPC in China, the ILC) would reach higher energies still. Critics including Sabine Hossenfelder argue that more colliders won't necessarily resolve the open questions, and that theoretical physics needs new ideas more than bigger machines.",
    },
    # 27 — Wave-particle duality
    {
        "tier": 4,
        "question": "By the late 1920s a paradox had become unavoidable in physics: electrons, light, and other quantum objects show wave properties in some experiments (interference patterns) and particle properties in others (definite hits on detectors). What did the new quantum framework conclude about this?",
        "answer": "Wave and particle are not exclusive categories at the quantum level — every quantum object has both aspects and which one shows up depends on what the experiment measures",
        "choices": [
            "Wave and particle are not exclusive categories at the quantum level — every quantum object has both aspects and which one shows up depends on what the experiment measures",
            "Electrons are pure particles and light is a pure wave — the appearance of wave behavior in electrons was a measurement error of the 1920s era",
            "Wave behavior was abandoned as obsolete — modern physics treats all quantum objects as small hard balls with no wave properties whatsoever",
            "The duality was resolved by Stephen Hawking in 1990 — quantum objects are now known to behave only as particles in every controlled experiment",
        ],
        "context": "Louis de Broglie's 1924 PhD thesis proposed that every particle has an associated wavelength — confirmed by Davisson-Germer (1927) electron-diffraction experiments. Bohr called the framework 'complementarity' — wave and particle pictures are complementary descriptions, both needed for a complete account, neither sufficient alone. The Copenhagen interpretation made complementarity foundational; modern physics treats the underlying mathematics of the wave function as primary.",
    },
    # 28 — Newton's universal gravitation
    {
        "tier": 4,
        "question": "Isaac Newton's 1687 Principia derived Kepler's planetary laws from a single inverse-square law: every pair of masses attracts each other with a force proportional to the product of their masses and inversely proportional to the square of the distance between them. Newton's leap was unifying terrestrial and celestial physics. What did that unification mean?",
        "answer": "The same gravity that pulls an apple down pulls the Moon toward Earth — there is no separate 'heavenly' physics — the laws on Earth and in space are the same",
        "choices": [
            "The same gravity that pulls an apple down pulls the Moon toward Earth — there is no separate 'heavenly' physics — the laws on Earth and in space are the same",
            "Heavenly objects obey one set of laws and earthly objects obey another — Newton kept the ancient distinction between the two physical realms",
            "Heavenly objects move by divine push, not by force — Newton's law applied only to earthly falling bodies, not to planetary motion at all",
            "Heavenly objects accelerate by an inverse fourth-power law — Newton derived a separate equation for celestial gravity from astronomy",
        ],
        "context": "The apple-and-Moon insight (whether the apple-tree story is literally true or not) is unification: gravity acts on apples and moons by the same rule. Newton's gravity worked spectacularly for centuries until Mercury's perihelion precession (43 arcseconds per century unexplained) showed the limits. Einstein's general relativity (1915) replaced Newton's gravity with curved spacetime — but for everyday cases Newton's equations are still the practical engineering tool.",
    },
    # 29 — Speed of light constancy
    {
        "tier": 4,
        "question": "Michelson and Morley in 1887 performed careful experiments with a precision interferometer in a Cleveland basement, trying to measure Earth's motion through the supposed 'luminiferous aether' — the medium 19th-century physics assumed light had to travel through. Their result was famously surprising. What did they find?",
        "answer": "No aether wind — light's speed appeared the same regardless of Earth's motion — quietly demolishing the aether concept and helping clear the way for relativity",
        "choices": [
            "No aether wind — light's speed appeared the same regardless of Earth's motion — quietly demolishing the aether concept and helping clear the way for relativity",
            "A strong aether wind — light moved noticeably faster when going downwind — confirming the aether's existence and grounding all subsequent physics",
            "A seasonal aether wind — light's speed changed with the calendar — showing that the aether circulates around the Sun in a predictable yearly cycle",
            "No light at all — their interferometer failed completely — and they had to rebuild the experiment with new equipment over the following five years",
        ],
        "context": "Michelson and Morley expected fringe shifts of about 0.4 in their interferometer; they saw less than 0.02. The 'null result' was famously called 'the most famous failed experiment in history.' FitzGerald and Lorentz proposed length contraction (1889, 1892) to save the aether. Einstein's 1905 paper abandoned the aether entirely, taking light's invariance as a postulate. Michelson won the 1907 Physics Nobel.",
    },
    # 30 — Wave nature of matter: De Broglie
    {
        "tier": 4,
        "question": "Louis de Broglie in his 1924 PhD thesis at the Sorbonne proposed that every particle has an associated wavelength — the wavelength being Planck's constant divided by the particle's momentum. His thesis committee was unsure whether to grant him a doctorate. What confirmed his hypothesis a few years later?",
        "answer": "Davisson and Germer at Bell Labs in 1927 fired electrons at a nickel crystal and got an interference pattern — confirming electrons have wave-like properties, exactly as de Broglie predicted",
        "choices": [
            "Davisson and Germer at Bell Labs in 1927 fired electrons at a nickel crystal and got an interference pattern — confirming electrons have wave-like properties, exactly as de Broglie predicted",
            "Heisenberg confirmed de Broglie's claim in 1925 by directly measuring the wavelength of a thrown baseball — finding it matched the prediction exactly",
            "Einstein wrote a brief paper in 1924 noting de Broglie's claim was self-evident from prior experiments — no further experiment was deemed necessary",
            "Schrödinger fired light through a glass prism in 1925 and observed electron-like behavior in the rainbow pattern — confirming particle waves dramatically",
        ],
        "context": "Davisson and Germer's accidental discovery came from an air-leak that crystallized their nickel target; when they resumed scattering electrons, they saw diffraction peaks. George Thomson independently demonstrated electron diffraction in 1927 (his father J.J. Thomson had discovered the electron in 1897 — father got a Nobel for the particle, son for the wave). De Broglie won the 1929 Physics Nobel for his hypothesis. The wavelength formula λ = h/p is now standard.",
    },
    # 31 — Standard candles: Type Ia SNe distance
    {
        "tier": 4,
        "question": "Type Ia supernovae are the explosions of white dwarf stars that have accumulated mass from a companion and crossed the Chandrasekhar mass limit (about 1.4 solar masses). They all explode in roughly similar ways with roughly similar peak brightness. Why did this property make them so important to cosmology in the 1990s?",
        "answer": "Their predictable peak brightness lets astronomers use them as 'standard candles' — measure how bright a Type Ia appears and you know how far away it is",
        "choices": [
            "Their predictable peak brightness lets astronomers use them as 'standard candles' — measure how bright a Type Ia appears and you know how far away it is",
            "Their explosions are completely random in brightness — useless as distance markers — but they're useful for studying nuclear physics directly",
            "Their explosions reveal the temperature of nearby galaxies — making them thermometers rather than distance indicators of any kind",
            "Their explosions are bright enough to push gas out of galaxies — they're tools for studying galactic winds rather than measuring distances",
        ],
        "context": "The Chandrasekhar limit was derived by Subrahmanyan Chandrasekhar in 1930 on his boat from India to Cambridge — he was 19 — and was initially mocked by Eddington. Type Ia uniformity isn't perfect; Mark Phillips' 1993 'Phillips relation' (brighter SNe Ia decline more slowly) gave a calibration that made them precise distance indicators. Perlmutter, Schmidt, and Riess used them for the 1998 acceleration discovery and 2011 Nobel.",
    },
    # 32 — Antimatter: PET scans practical use
    {
        "tier": 4,
        "question": "PET (positron emission tomography) scans are a routine medical imaging tool used for cancer detection, brain imaging, and cardiac evaluation. The 'P' stands for positron — the antimatter counterpart of the electron. How does the antimatter actually get used in a hospital scanner?",
        "answer": "A patient is injected with a radioactive tracer that emits positrons — when each positron meets an electron in the body, they annihilate into two gamma rays detected by the scanner",
        "choices": [
            "A patient is injected with a radioactive tracer that emits positrons — when each positron meets an electron in the body, they annihilate into two gamma rays detected by the scanner",
            "A patient is exposed to a CERN-generated antimatter beam from a small bedside accelerator — the beam imaging the body directly without any injected tracer",
            "A patient swallows positrons in capsule form — the positrons travel through the digestive tract and image the gut as they go by an external camera",
            "A patient receives a magnetic field that creates antimatter inside the body — natural matter-antimatter pairs form and self-destruct on contact with tissue",
        ],
        "context": "Common PET tracers include fluorodeoxyglucose (FDG, a glucose analog labeled with fluorine-18) for cancer imaging, and oxygen-15 water for blood-flow studies. Each annihilation produces two 511-keV gamma rays going in opposite directions; the scanner triangulates each annihilation point. PET-CT and PET-MRI scanners combine the metabolic information from PET with anatomical detail from CT or MRI. The technique is one of the great applied uses of antimatter — Dirac's 1928 equation made it possible.",
    },
    # 33 — Thermodynamic arrow of time
    {
        "tier": 4,
        "question": "The fundamental microscopic laws of physics — Newton's, Maxwell's, Schrödinger's, Einstein's — are mostly time-symmetric. Run them backwards and you get equally valid solutions. Yet broken eggs don't unbreak, cream doesn't separate from coffee, and the universe steadily moves forward. Where does the arrow of time come from?",
        "answer": "From the universe starting in an extremely low-entropy state at the Big Bang — entropy has been growing ever since, defining the direction we call 'forward'",
        "choices": [
            "From the universe starting in an extremely low-entropy state at the Big Bang — entropy has been growing ever since, defining the direction we call 'forward'",
            "From human consciousness imposing a direction — time has no objective arrow in physics, only in our subjective perception of the world",
            "From the gravitational constant being negative — gravity drags time forward, and removing gravity would let time flow in either direction",
            "From electromagnetic interactions being one-way — light only travels forward in time, fixing the direction for everything else by knock-on effect",
        ],
        "context": "The 'past hypothesis' that the early universe had extremely low entropy is one of the live explanations physicists offer for the time arrow. Why the universe started that way is itself unresolved — it might be a brute fact about initial conditions, an output of inflation, or a feature of cosmologies we haven't yet pinned down. Sean Carroll's 'From Eternity to Here' (2010) is a popular treatment; Boltzmann's 19th-century work on entropy and time was the original framing.",
    },
    # 34 — Special relativity: E = mc^2 meaning
    {
        "tier": 4,
        "question": "Einstein's E = mc^2 is the most famous physics equation in popular culture, but its meaning is sometimes misunderstood. The equation links mass and energy through a conversion factor (c-squared) that's enormous. What does it actually claim about mass and energy?",
        "answer": "Mass and energy are essentially the same thing in different forms — a small mass can convert to enormous energy, as in nuclear reactions and matter-antimatter annihilation",
        "choices": [
            "Mass and energy are essentially the same thing in different forms — a small mass can convert to enormous energy, as in nuclear reactions and matter-antimatter annihilation",
            "Mass and energy are unrelated quantities — the equation gives a coincidental numerical relationship that has no physical meaning to be exploited",
            "Mass is destroyed entirely by motion — fast-moving objects vanish without trace once they pass the speed of sound through a dense medium",
            "Mass is created from electric currents — the equation describes how generators turn current into solid material under the right conditions",
        ],
        "context": "Einstein's 1905 paper 'Does the Inertia of a Body Depend on Its Energy Content?' was a short follow-up to his special relativity paper. The mass-energy equivalence powers stars (hydrogen-to-helium fusion converts about 0.7% of mass to energy), nuclear weapons (uranium and plutonium fission), nuclear reactors, and PET scanners. The factor c^2 ≈ 9 × 10^16 m^2/s^2 means a single gram of mass corresponds to about 90 trillion joules — roughly the energy of the Hiroshima bomb.",
    },
    # 35 — Hubble constant tension
    {
        "tier": 4,
        "question": "By the late 2010s a puzzling discrepancy had emerged. The Hubble constant — using Cepheid + Type Ia supernova distance ladders calibrated locally — gave about 73 km/s per megaparsec. The same constant from the cosmic microwave background gave about 67. What's the 'Hubble tension'?",
        "answer": "Two independent methods disagree at high statistical significance — either the methods have hidden systematic errors, or new physics beyond the standard cosmological model is needed",
        "choices": [
            "Two independent methods disagree at high statistical significance — either the methods have hidden systematic errors, or new physics beyond the standard cosmological model is needed",
            "Hubble's original 1929 number was wrong by a factor of two — and modern astronomers cannot agree on which correction value to apply going forward",
            "Two telescopes failed simultaneously in 2018 — and current Hubble-constant figures are placeholders pending new instrument deployments in coming years",
            "Cosmologists abandoned the Hubble constant as meaningless in 2020 — replacing the entire concept with a different parameter without controversy",
        ],
        "context": "Adam Riess's SH0ES team reports ~73 km/s/Mpc with tightening error bars; the Planck collaboration's CMB analysis gives ~67.4. The tension sits at ~5 sigma. Proposed resolutions include early dark energy, modified gravity, neutrino-mass effects, and unidentified measurement systematics.",
    },
    # 36 — Particle-wave: Bell tests and locality
    {
        "tier": 4,
        "question": "John Bell in 1964 derived a mathematical inequality that local-hidden-variable theories must satisfy. If experiments violate it, then either physics is non-local, or measurement outcomes don't pre-exist as facts before measurement. What's the empirical answer been?",
        "answer": "Bell's inequality is violated experimentally — by a wide margin — confirming a classical assumption about local-hidden-variables is wrong, ruling out a large class of 'realist' theories",
        "choices": [
            "Bell's inequality is violated experimentally — by a wide margin — confirming a classical assumption about local-hidden-variables is wrong, ruling out a large class of 'realist' theories",
            "Bell's inequality has been confirmed in every experiment — local realism is restored, and Einstein's intuitions about hidden variables are fully vindicated",
            "Bell's inequality cannot be tested in practice — the experiments rely on classical assumptions that cannot be checked empirically by any laboratory work",
            "Bell's inequality is satisfied by classical physics — quantum mechanics is therefore reducible to ordinary physics with hidden underlying mechanisms",
        ],
        "context": "Aspect's 1981-82 experiments at Orsay were a milestone, followed by loophole-closing experiments by Zeilinger's group and others through the 2010s. The 2022 Physics Nobel went to Clauser, Aspect, and Zeilinger.",
    },
    # 37 — Cosmic inflation hypothesis
    {
        "tier": 4,
        "question": "Alan Guth in 1980 proposed an addition to Big Bang cosmology to solve two puzzles: why the universe is so flat geometrically, and why distant regions of the sky share temperature though they couldn't have exchanged light. His proposal was a brief exponentially-rapid expansion in the first tiny fraction of a second. What's it called?",
        "answer": "Cosmic inflation — exponential expansion that stretched a tiny patch of space larger than the observable universe, smoothing irregularities and explaining the flatness and uniformity we see",
        "choices": [
            "Cosmic inflation — exponential expansion that stretched a tiny patch of space larger than the observable universe, smoothing irregularities and explaining the flatness and uniformity we see",
            "Cosmic deflation — exponential shrinkage of the early universe — finally explaining the smoothness through gradual compression of all matter",
            "Cosmic chaos — the early universe is permanently turbulent — and the smoothness we see in the CMB is an illusion of telescope averaging",
            "Cosmic cooling — the early universe never expanded at all — its uniformity comes from extreme thermal mixing during a static early phase",
        ],
        "context": "Inflation is the leading framework but not without critics. Paul Steinhardt — an early architect — argues it has become unfalsifiable in practice. Roger Penrose has criticized inflation. The 2014 BICEP2 claim of primordial gravitational waves turned out to be dust contamination.",
    },
    # 38 — Failed prediction: Imminent ice-age 1970s
    {
        "tier": 4,
        "question": "In the 1970s a number of news magazines and a smaller number of scientific papers warned that Earth might be entering a new ice age — citing global temperature data showing a slight cooling from about 1940 to the early 1970s. By the late 1970s the dominant concern in climate science had shifted to warming, not cooling. What's the kid's recognition skill here?",
        "answer": "Climate predictions can flip 180 degrees within a decade — high-confidence forecasts about complex systems on short timescales have a documented failure history",
        "choices": [
            "Climate predictions can flip 180 degrees within a decade — high-confidence forecasts about complex systems on short timescales have a documented failure history",
            "1970s ice-age claims were universal among scientists — and the modern warming framing represents a deliberate concealment of the earlier consensus",
            "1970s ice-age claims were never made by anyone — the entire story was fabricated by later writers seeking to mock climate science generally",
            "1970s ice-age claims were exactly right — Earth is currently in an unrecognized cooling phase that warming reports are deliberately hiding",
        ],
        "context": "Peterson, Connolley, and Fleck's 2008 review of 1970s climate literature found about 7 papers predicting cooling, 44 predicting warming, and others ambiguous — so 'scientific consensus on a coming ice age' is an overstatement. But the popular and media-level alarm was real (Newsweek 1975, Time 1974) and the shift to warming-as-primary-concern was rapid. The recognition skill is humility about short-term forecasting, not climate denial.",
    },
    # 39 — General relativity: GPS gravitational time dilation
    {
        "tier": 4,
        "question": "General relativity predicts that clocks run more slowly in stronger gravitational fields. A clock at sea level ticks slightly slower than a clock on a mountaintop. The effect is tiny — about a billionth of a percent per kilometer of altitude — but real and measurable. How is the effect routinely confirmed in everyday technology?",
        "answer": "GPS satellites must adjust their clocks because GR makes their orbital clocks run faster than ground clocks — without correction, position estimates would drift by kilometers per day",
        "choices": [
            "GPS satellites must adjust their clocks because GR makes their orbital clocks run faster than ground clocks — without correction, position estimates would drift by kilometers per day",
            "Refrigerator clocks have to be reset weekly because of altitude effects — and household thermostats use general relativity for indoor temperature control",
            "GPS satellites do not actually use relativity in any way — corrections are made entirely from radio-frequency reference signals from the ground",
            "Microwave ovens depend on GR for their timing circuits — heating times must be set differently in mountain regions than in coastal ones",
        ],
        "context": "Pound and Rebka in 1959 confirmed gravitational time dilation in a Harvard tower — the first measurement on Earth. GPS satellites incorporate GR + SR corrections into their clock-rate settings; without the corrections, positions would drift by about 10 km per day. The everyday-life relevance of relativity in your phone's navigation is one of the more striking examples of fundamental physics powering routine technology.",
    },
    # 40 — Failed predictions: Koonin Unsettled
    {
        "tier": 4,
        "question": "Steven Koonin's *Unsettled* (2021) — by the former Undersecretary for Science at the Obama-era DOE — compared specific climate predictions against later observations. Several 2000s-era predictions about hurricane frequency, ice extent, and sea-level rise by various dates have NOT matched the record. What's the broader recognition Koonin pushes?",
        "answer": "The IPCC technical chapters and the media-level Summary for Policymakers do not match — many catastrophist framings exceed what the underlying reports actually support",
        "choices": [
            "The IPCC technical chapters and the media-level Summary for Policymakers do not match — many catastrophist framings exceed what the underlying reports actually support",
            "The IPCC has never published a single prediction that proved incorrect — every projection has matched observed data exactly across all timeframes",
            "Koonin retracted his book in 2022 — finding upon review that he had misread the IPCC reports and apologizing for the publication of the work",
            "Koonin argued climate is not changing at all — and that all warming records are fabricated by activist scientists working in coordinated networks",
        ],
        "context": "Koonin's actual claims: climate is warming (firm), humans contribute (firm), but the catastrophist framing exceeds what the IPCC technical chapters say. His criticism is methodological — media coverage compresses uncertainty out of the technical reports.",
    },
    # 41 — Failed prediction: Hansen 1988 Senate testimony
    {
        "tier": 4,
        "question": "James Hansen of NASA GISS testified to the US Senate in June 1988 — during a Washington heat wave — that he was '99% certain' warming had begun. His paper presented three model scenarios: A (continued growth), B (moderate), C (sharp emissions cuts). What did the actual temperature record do by 2010?",
        "answer": "Actual temperatures came in close to Scenario C — even though emissions tracked closer to Scenario A — suggesting his model's climate sensitivity was higher than the real Earth's",
        "choices": [
            "Actual temperatures came in close to Scenario C — even though emissions tracked closer to Scenario A — suggesting his model's climate sensitivity was higher than the real Earth's",
            "Actual temperatures vastly exceeded all three scenarios — global average jumped 5 degrees by 2010 — exactly as Hansen had warned in his testimony to the Senate",
            "Actual temperatures fell below all three scenarios — Earth cooled by 2 degrees in the two decades after Hansen testified at the Washington Senate hearing",
            "Hansen's testimony has been entirely vindicated in every detail — every single prediction came true on the exact schedule he had publicly committed to",
        ],
        "context": "Contested ground. Defenders point out emissions ran closer to Scenario B in the 1990s but converged with A by the 2010s; some argue Scenario B tracks reasonably well. Critics including Patrick Michaels argued the 1988 model over-projected warming by a sizeable factor. The honest reading: Hansen got the sign right (warming, not cooling) but his model over-predicted the magnitude.",
    },
    # 42 — Pauli neutrino postulate 1930 + Reines/Cowan 1956
    {
        "tier": 4,
        "question": "Wolfgang Pauli in 1930 wrote a famous letter to a Tübingen conference proposing a 'desperate remedy' to save energy conservation in beta decay — a nearly massless neutral particle he doubted could ever be detected. He nicknamed it the 'neutron' (later renamed 'neutrino' by Fermi). Why was Pauli wrong about detectability?",
        "answer": "Reines and Cowan detected the neutrino at the Savannah River nuclear reactor in 1956 — using inverse beta decay in liquid scintillator near the intense reactor neutrino source",
        "choices": [
            "Reines and Cowan detected the neutrino at the Savannah River nuclear reactor in 1956 — using inverse beta decay in liquid scintillator near the intense reactor neutrino source",
            "Pauli detected the neutrino himself in his Zurich lab in 1932 — confirming his own prediction within two years of the desperate-remedy letter",
            "Neutrinos were never directly detected — they remain a useful theoretical fiction in particle physics that has not been confirmed empirically",
            "Neutrinos were first detected in 2020 at Japanese Super-Kamiokande — making Pauli's 1930 prediction the longest unconfirmed claim in particle physics",
        ],
        "context": "Reines won the 1995 Physics Nobel (Cowan died in 1974). Solar neutrino experiments by Davis and Koshiba revealed neutrino oscillation — neutrinos changing 'flavor' as they travel — proving they have non-zero mass (Nobel 2002, 2015).",
    },
    # 43 — Strong force / quarks confinement
    {
        "tier": 4,
        "question": "Quarks are never observed as free particles — only in combinations (protons, neutrons, mesons). Pull two quarks apart with enough energy and new quark-antiquark pairs pop out of the vacuum, snapping the quarks back into colorless bound states. This odd property is called 'confinement.' What's the underlying mechanism?",
        "answer": "The strong force gets STRONGER with distance — pulling quarks apart costs more energy the farther you go — until making new particles becomes cheaper than further separation",
        "choices": [
            "The strong force gets STRONGER with distance — pulling quarks apart costs more energy the farther you go — until making new particles becomes cheaper than further separation",
            "The strong force gets WEAKER with distance like gravity and electromagnetism — but it acts on a separate type of charge that masks free quarks completely",
            "The strong force is identical to electromagnetism — quarks are simply small electrically charged particles that always stick together by ordinary force",
            "The strong force does not exist in modern physics — quarks were retired in 2010 as obsolete and replaced by a unified mass-energy field theory",
        ],
        "context": "The opposite property — where the strong force gets WEAKER at very short distances — was discovered by Gross, Politzer, and Wilczek (2004 Nobel). The combined picture: tightly bound quarks behave almost freely at LHC-scale energies but cannot be pulled apart at normal distances. The theory is quantum chromodynamics (QCD). 'Color' is an internal quantum-number label.",
    },
    # 44 — Two-slit detection collapse
    {
        "tier": 4,
        "question": "In the double-slit experiment with single quantum objects, the interference pattern shows that each object behaves as if it goes through both slits. If detectors are placed at the slits to determine which slit each object passes through, the interference pattern vanishes — even if the detectors are passive and don't disturb the object. Why?",
        "answer": "Acquiring 'which-slit' information — even in principle — collapses the wave-like superposition into one-slit-or-the-other behavior — a textbook quantum measurement effect",
        "choices": [
            "Acquiring 'which-slit' information — even in principle — collapses the wave-like superposition into one-slit-or-the-other behavior — a textbook quantum measurement effect",
            "Detectors physically block the slits and prevent passage — the interference pattern vanishes simply because the slits become smaller in size",
            "Detectors emit light that warms the objects — the heated objects then move differently and miss the interference fringes by a small detectable margin",
            "Detectors release magnetic fields that deflect the objects sideways — making them spread out into a uniform glow on the receiving screen",
        ],
        "context": "The which-path / wave-particle complementarity has been demonstrated in increasingly clever delayed-choice setups (Wheeler's gedankenexperiment, then real experiments by Aspect, Jacques et al. 2007). Quantum erasure experiments show that erasing the which-path information AFTER the object has passed the slits can restore the interference pattern. The result is genuinely strange and resists every classical visualization.",
    },
    # 45 — Compton scattering 1923
    {
        "tier": 4,
        "question": "Arthur Compton in 1923 fired X-rays at a graphite target and measured the scattered X-rays. The scattered X-rays came back at a LONGER wavelength than the incoming beam — and the wavelength change depended on the scattering angle in a way Einstein's photon picture predicted. What did this confirm?",
        "answer": "X-ray photons carry momentum as well as energy — scattering off an electron transfers that momentum, like a billiard-ball collision — confirming the photon picture of light",
        "choices": [
            "X-ray photons carry momentum as well as energy — scattering off an electron transfers that momentum, like a billiard-ball collision — confirming the photon picture of light",
            "X-rays are pure waves with no particle properties — Compton's experiment showed classical wave theory explains every aspect of light scattering",
            "X-rays are slowed down by graphite — Compton's measurement showed the speed of light depends on the medium and the angle in a complicated way",
            "X-rays are emitted by electrons spontaneously — Compton's measurement showed no scattering occurred and the beam simply continued unchanged",
        ],
        "context": "Compton's 1923 experiment was a key confirmation of photons as real particles. The shift Δλ = (h/mc)(1 - cos θ) matches the photon-electron collision prediction. Compton won the 1927 Physics Nobel. Together with the photoelectric effect, Compton scattering established the dual wave-particle character of light.",
    },
    # 46 — Lorentz invariance tests
    {
        "tier": 4,
        "question": "Special relativity depends on the postulate that the speed of light is the same for every inertial observer — and that the laws of physics take the same form in every inertial frame. This 'Lorentz invariance' has been tested with extraordinary precision. What's a recent test result?",
        "answer": "Modern experiments using optical resonators and atomic clocks have confirmed Lorentz invariance to parts in 10^18 or better — making it one of the best-tested principles in physics",
        "choices": [
            "Modern experiments using optical resonators and atomic clocks have confirmed Lorentz invariance to parts in 10^18 or better — making it one of the best-tested principles in physics",
            "Recent experiments have refuted Lorentz invariance entirely — and the standard model has been quietly replaced with a non-relativistic alternative since 2015",
            "Recent experiments have shown Lorentz invariance to vary with location on Earth — depending on the season and the time of day in northern latitudes",
            "Recent experiments have shown Lorentz invariance to be untestable in principle — only theoretical arguments support it, and no empirical check is possible",
        ],
        "context": "Modern Michelson-Morley-style tests use optical resonators (cavities with extremely stable resonant frequencies) rotated relative to the cosmic microwave background. Optical clock comparisons across networks like the Boulder-Paris-Tokyo collaborations also test Lorentz invariance at extraordinary precision. Some quantum-gravity scenarios predict tiny Lorentz-breaking effects at very high energies, but no current experiment has detected them.",
    },
    # 47 — Carnot to Boltzmann: statistical mechanics
    {
        "tier": 4,
        "question": "Ludwig Boltzmann in the 1870s connected entropy to the number of microscopic configurations consistent with a macroscopic state — the famous formula engraved on his tombstone, S = k log W. Boltzmann committed suicide in 1906, partly under the strain of his ideas being attacked by colleagues. What did Boltzmann's statistical interpretation accomplish?",
        "answer": "It gave thermodynamics a microscopic mechanical basis — heat and entropy became statistical properties of atoms in motion — confirming the atomic theory in the process",
        "choices": [
            "It gave thermodynamics a microscopic mechanical basis — heat and entropy became statistical properties of atoms in motion — confirming the atomic theory in the process",
            "It disproved the atomic theory entirely — Boltzmann's formula showed that atoms could not exist in any consistent statistical framework",
            "It replaced thermodynamics with electromagnetism — Boltzmann argued that heat is purely an electrical effect, and entropy a magnetic quantity",
            "It was retracted in 1900 — Boltzmann himself withdrew his entropy formula after realizing it conflicted with Maxwell's electromagnetic equations",
        ],
        "context": "Boltzmann faced strong opposition from energeticists (Ostwald, Mach) who treated atoms as a useful fiction rather than physical reality. Einstein's 1905 Brownian-motion paper and Perrin's 1908 confirmation finally settled the debate, but Boltzmann had already taken his life two years before Perrin's vindication. The formula on his Vienna grave reads simply 'S = k log W.'",
    },
    # 48 — Special relativity time dilation muons
    {
        "tier": 4,
        "question": "Cosmic-ray muons created high in Earth's atmosphere have a lifetime of about 2.2 microseconds at rest. Even moving at near light-speed, classically they should travel only about 660 meters before decaying. Yet many reach the ground. Why?",
        "answer": "From the muons' own frame, their lifetime is the usual 2.2 microseconds — but from Earth's frame, time-dilation extends their measured lifetime by many times — letting them reach the surface",
        "choices": [
            "From the muons' own frame, their lifetime is the usual 2.2 microseconds — but from Earth's frame, time-dilation extends their measured lifetime by many times — letting them reach the surface",
            "Cosmic muons are not actually fast — their measured speeds are highly exaggerated — and they reach the ground because they are slower than predicted",
            "Cosmic muons replicate themselves in the atmosphere — generating new muons every few hundred meters along the descent path until reaching ground",
            "Cosmic muons travel through tiny subatomic wormholes — taking shortcuts through hidden dimensions that bypass the troposphere entirely on each fall",
        ],
        "context": "The classic muon experiment was performed by Rossi and Hall in 1941 with muons from cosmic rays measured at different altitudes. Their lifetime appears longer from Earth's frame (time dilation) AND the distance from the upper atmosphere to the ground appears shorter from the muon's frame (length contraction). Both descriptions give the same answer — they're the same physics seen from different reference frames.",
    },
    # 49 — Higgs mechanism plain English
    {
        "tier": 4,
        "question": "The Higgs field — confirmed by the 2012 LHC discovery of the Higgs boson — pervades all of space, with a non-zero average value everywhere. Different particles interact with the Higgs field at different strengths. What does this give those particles?",
        "answer": "Their mass — particles that interact more strongly with the Higgs field are heavier, and particles that don't interact (like photons) are massless",
        "choices": [
            "Their mass — particles that interact more strongly with the Higgs field are heavier, and particles that don't interact (like photons) are massless",
            "Their electric charge — Higgs interactions determine whether each particle is positive, negative, or neutral in any everyday environment",
            "Their spin — Higgs interactions set whether each particle rotates with integer or half-integer spin in the standard model framework",
            "Their color — Higgs interactions determine which of the three quark color charges each particle carries in the strong-force theory",
        ],
        "context": "The Higgs mechanism was developed in 1964 by Peter Higgs, François Englert and Robert Brout, Gerald Guralnik, C.R. Hagen and Tom Kibble — three independent papers in a single year. The 2013 Physics Nobel went to Higgs and Englert (Brout had died in 2011; Nobels are not posthumous). Most of the mass of ordinary matter (you, the table, the Earth) comes from quark-binding energy in protons and neutrons via the strong force — not directly from the Higgs.",
    },
    # 50 — Open question: theory of everything / quantum gravity
    {
        "tier": 4,
        "question": "Two pillars of modern physics describe nature precisely: general relativity for gravity at large scales, and quantum mechanics + the Standard Model at small scales. They are mathematically incompatible at extreme scales — inside black holes, at the Big Bang. What's the honest status of unifying them?",
        "answer": "Quantum gravity remains unsolved — multiple frameworks (string theory, loop quantum gravity, asymptotic safety) compete, and none has decisive experimental support as of the mid-2020s",
        "choices": [
            "Quantum gravity remains unsolved — multiple frameworks (string theory, loop quantum gravity, asymptotic safety) compete, and none has decisive experimental support as of the mid-2020s",
            "Quantum gravity was completed in 2010 by a research team at Stanford — and the unified theory is now standard in undergraduate physics curricula",
            "Quantum gravity is no longer a meaningful research question — gravity and quantum mechanics are now known to describe entirely separate phenomena",
            "Quantum gravity is identical to electromagnetism — recent unification efforts have shown all four forces collapsed into a single equation by accident",
        ],
        "context": "String theory has been the dominant approach but lacks confirmed predictions; critics including Lee Smolin and Peter Woit have argued it has consumed resources without experimental traction. Loop quantum gravity (Rovelli, Smolin) is the leading non-string alternative.",
    },
]

# ============================================================================
# P2 CHEMISTRY (40)
# ============================================================================

P2: list[dict] = [
    # 51 — Organic functional groups overview
    {
        "tier": 4,
        "question": "Organic chemistry is mostly about how a small number of 'functional groups' — characteristic atom arrangements like -OH (alcohol), -COOH (carboxylic acid), or -NH2 (amine) — behave when attached to a carbon backbone. Why is the functional-group concept so powerful for predicting chemical behavior?",
        "answer": "Different organic molecules with the same functional group tend to react in similar ways — so once you learn 20 groups you can predict the chemistry of thousands of compounds",
        "choices": [
            "Different organic molecules with the same functional group tend to react in similar ways — so once you learn 20 groups you can predict the chemistry of thousands of compounds",
            "All organic molecules react identically regardless of functional group — so the concept is a teaching convenience without real chemical meaning to it",
            "Each functional group reacts uniquely with no patterns — so chemists must memorize every individual compound's behavior separately, with no shortcuts available",
            "Functional groups can be exchanged freely between molecules — so any organic compound can become any other by simple group transplantation in the lab",
        ],
        "context": "Carbon's tetravalent bonding allows enormous structural variety, but the reactive sites (the functional groups) are limited and well-studied. Friedrich August Kekulé's structural-theory paper (1858) was foundational. By the late 19th century the functional-group framework — Liebig, Wöhler, Berzelius — let chemists map out general reaction types (substitution, addition, elimination) that work across many specific compounds.",
    },
    # 52 — Benzene Kekulé snake dream 1865
    {
        "tier": 4,
        "question": "Friedrich August Kekulé published the ring structure for benzene (C6H6) in 1865. He later told an after-dinner story that the structure had come to him in a daydream of a snake biting its own tail — though whether the dream actually happened that way is disputed. Why was the ring structure such a difficult puzzle?",
        "answer": "C6H6 has six carbons but ordinary single-bond carbon needs four hydrogens each — the ring with alternating single and double bonds was Kekulé's resolution to the puzzle",
        "choices": [
            "C6H6 has six carbons but ordinary single-bond carbon needs four hydrogens each — the ring with alternating single and double bonds was Kekulé's resolution to the puzzle",
            "C6H6 was thought to be a salt rather than an organic compound — Kekulé needed years of detective work to identify what kind of substance benzene actually was",
            "C6H6 was thought to be a gas — Kekulé spent years showing it was a liquid and the formula had been measured incorrectly for decades by prior chemists",
            "C6H6 was thought to contain nitrogen — Kekulé's work showed it was carbon and hydrogen only, finally allowing modern chemistry to describe the molecule",
        ],
        "context": "Kekulé's 1865 ring proposal solved the benzene puzzle that had defeated August Wilhelm von Hofmann and others. The 'aromatic' ring structure underlies a huge fraction of organic chemistry — drugs, dyes, plastics. Modern quantum mechanics describes benzene's bonds as delocalized — neither alternating single-double nor any specific Lewis structure.",
    },
    # 53 — Polymer chemistry intro
    {
        "tier": 4,
        "question": "Hermann Staudinger in the 1920s argued — against the prevailing view — that natural rubber and similar materials are made of long chain molecules (he called them 'macromolecules' or 'polymers') rather than aggregates of small molecules held together by mysterious forces. He won the 1953 Chemistry Nobel. Why was the polymer hypothesis controversial at first?",
        "answer": "Chemists of the 1920s thought molecules above a certain size were impossible — Staudinger's giant chains contradicted the accepted view of molecular structure",
        "choices": [
            "Chemists of the 1920s thought molecules above a certain size were impossible — Staudinger's giant chains contradicted the accepted view of molecular structure",
            "Chemists thought all materials were chains — Staudinger's controversial claim was that some materials are NOT polymers but smaller individual molecules",
            "Chemists rejected the term 'polymer' as misleading — Staudinger had to coin a new word for his hypothesis after fierce debate in journals",
            "Chemists found that polymers do not actually exist — Staudinger's Nobel was awarded for a hypothesis that has since been quietly discredited",
        ],
        "context": "Staudinger's macromolecule theory underlies modern materials science. Plastics, nylons, polyethylene, polystyrene, proteins, DNA, polysaccharides — all are polymers in his sense. Wallace Carothers at DuPont developed nylon in the 1930s using Staudinger's framework. Carothers committed suicide in 1937. The polymer industry transformed 20th-century life — clothing, packaging, electronics — based on the controversial 1920s hypothesis.",
    },
    # 54 — Amino acids 20 standard
    {
        "tier": 4,
        "question": "Proteins — the workhorse molecules of every living cell — are built from amino acids strung together in chains. The number of standard amino acids used by Earth's life is small and remarkably consistent across all kingdoms. How many are there in the standard set?",
        "answer": "Twenty standard amino acids — all but a few used in every kingdom of life — coded directly by the universal triplet code in DNA",
        "choices": [
            "Twenty standard amino acids — all but a few used in every kingdom of life — coded directly by the universal triplet code in DNA",
            "Two hundred standard amino acids — every organism builds proteins from its own unique large pool — making protein structures vary widely",
            "Two standard amino acids — every protein in nature is built from just two basic units — combined in different ways to make all biological molecules",
            "Two thousand standard amino acids — Earth life uses an extremely large diverse palette — and only a tiny fraction has been catalogued so far in labs",
        ],
        "context": "The 20 standard amino acids — plus selenocysteine and pyrrolysine as the 21st and 22nd 'extras' in some organisms — give an enormous protein diversity from a small toolkit. The universal triplet code (three DNA bases per amino acid) and its strong conservation across all life are among the strongest evidence for a single common ancestor. The chemistry: a central carbon with -NH2, -COOH, -H, and a variable side chain (the 'R group') that distinguishes the 20.",
    },
    # 55 — Enzymes as catalysts
    {
        "tier": 4,
        "question": "Enzymes are biological catalysts — almost always proteins — that speed up specific chemical reactions in living cells without being consumed. Some accelerate reactions by factors of a million or more. What's the basic mechanism by which an enzyme works?",
        "answer": "It binds the reactant in a precisely-shaped 'active site' — lowering the energy barrier for the reaction so it proceeds at body temperature instead of needing extreme heat or pressure",
        "choices": [
            "It binds the reactant in a precisely-shaped 'active site' — lowering the energy barrier for the reaction so it proceeds at body temperature instead of needing extreme heat or pressure",
            "It supplies the energy for the reaction directly from the cell's stored heat — pumping calories into the reactants until they overcome the barrier and form products",
            "It absorbs unwanted byproducts of the reaction — keeping the chemistry clean — but does not actually affect the rate at which any reaction proceeds in a cell",
            "It is consumed in each reaction it catalyzes — enzymes are gradually depleted and must be replaced constantly — making them ordinary reactants of every reaction",
        ],
        "context": "Enzymes are the central catalysts of biochemistry. Their specificity — the 'lock-and-key' fit between active site and substrate, refined by Daniel Koshland's 'induced fit' model — explains how cells run thousands of distinct reactions in the same crowded cytoplasm without chaos. Pasteur first studied catalysis in fermentation; Eduard Buchner won the 1907 Nobel for showing fermentation works in a cell-free extract — establishing that enzymes are molecules, not 'vital force.'",
    },
    # 56 — Lipids: fats, cholesterol, phospholipids
    {
        "tier": 4,
        "question": "Lipids are one of the four big classes of biomolecules (with proteins, carbohydrates, and nucleic acids). They include fats, oils, waxes, cholesterol, and the phospholipids that form cell membranes. What chemical property do almost all lipids share?",
        "answer": "Lipids are largely 'hydrophobic' — they don't mix well with water — which is why oil and water separate, and why cell membranes can form a barrier between inside and outside",
        "choices": [
            "Lipids are largely 'hydrophobic' — they don't mix well with water — which is why oil and water separate, and why cell membranes can form a barrier between inside and outside",
            "Lipids dissolve readily in water — they are the most water-soluble of all biological molecules — which is why blood can carry them freely through the body",
            "Lipids carry electrical charge — they are similar to ions in the body — which is why they conduct nerve signals between cells along the nervous system",
            "Lipids contain large amounts of phosphorus — every lipid molecule has phosphate groups attached — which is why they are needed for ATP synthesis everywhere",
        ],
        "context": "The phospholipid bilayer — a double layer of phospholipids with their hydrophobic 'tails' inward and hydrophilic 'heads' outward — is the structural basis of every cell membrane. Cholesterol stabilizes animal-cell membranes. Triglycerides (fats and oils) are energy storage. The hydrophobicity of lipids is why fats float on water and why your body uses bile (a detergent) to digest dietary fat in the small intestine.",
    },
    # 57 — Glass as supercooled liquid
    {
        "tier": 4,
        "question": "Glass — including ordinary window glass and obsidian — has a structure unlike a typical solid. A normal solid has atoms in a regular crystalline lattice. Glass instead has the disordered atom arrangement of a liquid, but is rigid. What's the technical name for this state?",
        "answer": "Amorphous solid — also called a 'supercooled liquid' — frozen in a disordered glassy state because it cooled too fast to crystallize",
        "choices": [
            "Amorphous solid — also called a 'supercooled liquid' — frozen in a disordered glassy state because it cooled too fast to crystallize",
            "Crystalline solid — glass has perfectly ordered atoms like quartz or salt — and the disorder picture is a popular-science misconception",
            "Gaseous solid — glass is mostly trapped pockets of air — held together by a thin shell of atoms in a fragile arrangement throughout each piece",
            "Plasma state — glass is ionized matter at room temperature — making it the only common everyday plasma found in nature on Earth",
        ],
        "context": "The popular claim that 'medieval cathedral glass is thicker at the bottom because glass flows over centuries' is a myth — old glass varied by manufacturing technique. Real glass flow at room temperature is far too slow to matter on human timescales. The glass transition (where a melt cools into a glass rather than crystallizing) is one of the active research questions in condensed-matter physics; how exactly the transition works is debated.",
    },
    # 58 — Superconductors below critical temperature
    {
        "tier": 4,
        "question": "Heike Kamerlingh Onnes in 1911 cooled mercury below 4.2 K (the temperature of liquid helium) and noticed something strange: its electrical resistance dropped to zero. Currents in superconducting rings can persist forever without a driving voltage. What's the broader phenomenon?",
        "answer": "Superconductivity — below a critical temperature, certain materials carry electric current with zero resistance — and many also expel magnetic fields entirely (the Meissner effect)",
        "choices": [
            "Superconductivity — below a critical temperature, certain materials carry electric current with zero resistance — and many also expel magnetic fields entirely (the Meissner effect)",
            "Superinductivity — below a critical temperature, materials build up magnetic charges that conduct heat — but their electrical resistance increases rather than decreases",
            "Supercooling — below a certain temperature, materials stop conducting electricity entirely — and Onnes's measurement was an experimental error in the data",
            "Subconductivity — below a critical temperature, materials become brittle and shatter under any current load — making the phenomenon useless for any practical use",
        ],
        "context": "Onnes won the 1913 Physics Nobel. Type-I (BCS theory, Bardeen-Cooper-Schrieffer 1957, Nobel 1972) and Type-II superconductors are distinguished. High-temperature superconductors (Bednorz and Müller, 1986, Nobel 1987) work above 30 K.",
    },
    # 59 — Materials science: alloys
    {
        "tier": 4,
        "question": "Pure metals are often soft and corrode quickly. Steel is mostly iron alloyed with about 0.05-2% carbon. Brass is copper alloyed with zinc. Bronze is copper alloyed with tin. What general advantage does alloying typically give over pure metals?",
        "answer": "Alloys are usually stronger, harder, and more corrosion-resistant than the pure parent metals — because the added atoms disrupt slip planes in the metallic lattice",
        "choices": [
            "Alloys are usually stronger, harder, and more corrosion-resistant than the pure parent metals — because the added atoms disrupt slip planes in the metallic lattice",
            "Alloys are always softer and weaker than the pure parent metals — they are made primarily for decorative purposes such as jewelry rather than structural use",
            "Alloys are always cheaper than the pure parent metals — and that's the only reason they are used in industry — there's no functional difference at all",
            "Alloys conduct electricity better than any pure metal — they are used in electrical wiring whenever pure metals would be inadequate for high-current applications",
        ],
        "context": "Bronze (copper + tin, ~3000 BC) was a major Bronze Age technology — much harder than copper alone. Steel (iron + carbon) is the foundational structural material of modernity. Aluminum alloys (Duralumin etc.) enabled metal aircraft. The science of how alloys' microstructure determines macroscopic properties — grain boundaries, dislocations, precipitation hardening — is called metallurgy, one of the great applied fields.",
    },
    # 60 — Lavoisier 1774 oxygen, executed 1794
    {
        "tier": 4,
        "question": "Antoine Lavoisier in 1774 — building on work by Joseph Priestley and Carl Scheele — identified and named 'oxygen' as the active component of air in combustion. He overturned the 'phlogiston' theory and is often called the founder of modern chemistry. What ended his life in 1794?",
        "answer": "He was guillotined during the Reign of Terror — not for his chemistry, but for being a tax collector in the Ancien Régime tax-farming system",
        "choices": [
            "He was guillotined during the Reign of Terror — not for his chemistry, but for being a tax collector in the Ancien Régime tax-farming system",
            "He died in a chemistry lab accident — phosphorus exploded while he was preparing a public demonstration of his oxygen theory for the new Republic",
            "He died peacefully of old age at 71 — surrounded by colleagues celebrating the success of his quantitative chemistry framework in the 1790s",
            "He died of mercury poisoning from his own lab work — common among chemists of the era who handled toxic metals without modern protective equipment",
        ],
        "context": "Lavoisier was a 'Farmer-General' — a private tax collector under the old regime — and was tried with other tax collectors on May 8, 1794. The mathematician Joseph-Louis Lagrange said after the execution: 'It took them only an instant to cut off this head, and one hundred years might not suffice to reproduce its like.' Lavoisier's quantitative methods — careful weighing of reactants and products — made conservation of mass routine in chemistry.",
    },
    # 61 — Mass conservation Lavoisier
    {
        "tier": 4,
        "question": "Antoine Lavoisier's careful weighing experiments in the 1770s and 1780s established a quantitative law that the alchemists and the phlogiston-theory chemists had never made precise. What did he establish?",
        "answer": "Conservation of mass — in an ordinary chemical reaction, total mass of reactants equals total mass of products — making chemistry a quantitative science",
        "choices": [
            "Conservation of mass — in an ordinary chemical reaction, total mass of reactants equals total mass of products — making chemistry a quantitative science",
            "Conservation of phlogiston — Lavoisier confirmed the old phlogiston theory by careful measurement — finding that phlogiston flowed between reactants in fixed amounts",
            "Conservation of color — chemical reactions preserve the optical properties of reactants — letting chemists predict the appearance of products by careful weighing",
            "Conservation of taste — Lavoisier weighed many substances by tasting them — establishing standardized flavor as the basis for early systematic chemistry",
        ],
        "context": "Mass conservation became the foundation of stoichiometry — the quantitative analysis of chemical reactions. Lavoisier's *Traité Élémentaire de Chimie* (1789) established the modern naming conventions for elements and compounds. Mass is not absolutely conserved in nuclear reactions (Einstein's E = mc^2 lets a tiny fraction of mass become energy), but in ordinary chemistry the law holds to extraordinary precision.",
    },
    # 62 — Gas laws: Boyle Charles Avogadro
    {
        "tier": 4,
        "question": "Three foundational gas laws — Boyle's (1662: at fixed temperature, pressure and volume vary inversely), Charles's (1787: at fixed pressure, volume varies with temperature), and Avogadro's (1811: equal volumes of any gas at the same temperature and pressure contain equal numbers of molecules) — combine into the ideal gas law. What's its compact form?",
        "answer": "PV = nRT — pressure times volume equals number of moles times the gas constant R times temperature in Kelvin",
        "choices": [
            "PV = nRT — pressure times volume equals number of moles times the gas constant R times temperature in Kelvin",
            "PV = mc^2 — Einstein's relation between pressure and mass — which is actually identical to the gas law in non-relativistic conditions found in chemistry labs",
            "PV = F = ma — Newton's second law applied to gas molecules — directly giving the gas law from particle dynamics without further input from chemistry",
            "PV = E = hν — Planck's energy formula — relating gas pressure to electromagnetic frequency in a quantum mechanical version of the gas-law identity",
        ],
        "context": "The ideal gas law applies well at moderate pressures and temperatures. Real gases deviate at high pressure (where molecular volume matters) and low temperature (where intermolecular attraction matters). Van der Waals's 1873 equation extended the ideal gas law to account for real-gas behavior. Avogadro's number (~6.022 × 10^23 — the number of molecules per mole) was reliably measured first by Jean Perrin around 1908, confirming atoms and molecules as real.",
    },
    # 63 — Heat capacity
    {
        "tier": 4,
        "question": "Water has an unusually high specific heat capacity — about 4.18 J/(g·K) — which is the amount of energy needed to raise one gram by one degree Celsius. Iron's is about 0.45; copper's about 0.39. Why does water's high heat capacity matter for everyday life and climate?",
        "answer": "Water stores a lot of energy per degree of warming — oceans buffer Earth's climate, animals regulate body temperature through sweating, and water makes a slow heating reservoir",
        "choices": [
            "Water stores a lot of energy per degree of warming — oceans buffer Earth's climate, animals regulate body temperature through sweating, and water makes a slow heating reservoir",
            "Water has low heat capacity — which is why it boils quickly in a kettle — and this makes water suitable for storing energy in industrial steam engines",
            "Water's heat capacity is negligible — temperature changes pass through water almost instantly — making water useless as a coolant in any industrial setting",
            "Water has the highest electrical conductivity of any liquid — its heat capacity matters only for nuclear reactors that use water to conduct currents",
        ],
        "context": "Water's high heat capacity comes from its hydrogen-bonded structure — additional energy goes into breaking those bonds rather than into kinetic motion. The effect is part of why coastal climates are milder than continental interiors at the same latitude. The high latent heat of vaporization (energy to evaporate water) is another reason sweating cools humans effectively, and why water-based fire suppression works.",
    },
    # 64 — Electrolysis
    {
        "tier": 4,
        "question": "Pass an electric current through molten salt or through water with a dissolved electrolyte and chemistry happens at the electrodes — water splits into hydrogen and oxygen, sodium chloride splits into sodium metal and chlorine gas, aluminum can be extracted from its ore. What's this called?",
        "answer": "Electrolysis — using electric energy to drive a non-spontaneous chemical reaction — the basis for aluminum production, chlorine manufacture, and electroplating industries",
        "choices": [
            "Electrolysis — using electric energy to drive a non-spontaneous chemical reaction — the basis for aluminum production, chlorine manufacture, and electroplating industries",
            "Electromagnetism — using electric energy to drive a magnetic reaction — the basis for hard-drive recording, motor generation, and induction heating technologies",
            "Electrocardiology — using electric energy to study the heart's electrical activity — the basis for medical diagnostic procedures used in hospitals worldwide",
            "Electrochemistry — using electric current to measure pH levels in industrial solutions — the basis for water-quality monitoring at every drinking-water facility",
        ],
        "context": "Humphry Davy used electrolysis in 1807-08 to isolate sodium, potassium, magnesium, calcium, strontium, and barium — six new elements in a single year. Hall and Héroult independently developed the electrolytic process for aluminum in 1886 — turning aluminum from a precious metal (Napoleon III had aluminum cutlery for honored guests) into a cheap structural material.",
    },
    # 65 — Acids and bases pH scale
    {
        "tier": 4,
        "question": "The pH scale measures the acidity or basicity (alkalinity) of a water-based solution on a scale from 0 (extremely acidic) to 14 (extremely basic), with 7 being neutral. The 'p' stands for 'power' or 'potential' and the 'H' for hydrogen. What does pH actually measure?",
        "answer": "The negative logarithm of the hydrogen-ion concentration — pH 3 means ten times more H+ than pH 4 and a hundred times more than pH 5",
        "choices": [
            "The negative logarithm of the hydrogen-ion concentration — pH 3 means ten times more H+ than pH 4 and a hundred times more than pH 5",
            "The pure hydrogen-ion concentration directly — pH 3 means three units of H+ ions — and pH 14 means fourteen units of H+ ions",
            "The temperature of an acidic solution — pH 3 means three degrees above freezing — and pH 14 means fourteen degrees above freezing in the same units",
            "The number of hydrogen atoms per molecule — pH 3 means three hydrogen atoms per substance unit — making the scale a structural rather than acidity measure",
        ],
        "context": "Søren Sørensen at the Carlsberg Laboratory in Copenhagen invented the pH scale in 1909. Stomach acid is around pH 1.5-2.0. Lemon juice is around pH 2. Pure water is 7. Blood is tightly buffered around 7.4 — life is exquisitely sensitive to pH, which is why diluted strong acids and bases can be deadly. The logarithmic scale catches the enormous range of H+ concentrations that occur in nature.",
    },
    # 66 — Periodic table organization Mendeleev 1869
    {
        "tier": 4,
        "question": "Dmitri Mendeleev in 1869 published a table of the known chemical elements arranged by atomic weight, with elements in the same column having similar chemical properties. His version had GAPS where no element was yet known. What did those gaps eventually do?",
        "answer": "Mendeleev predicted new elements with specific properties to fill the gaps — gallium (1875), scandium (1879), and germanium (1886) were soon discovered and matched his predictions",
        "choices": [
            "Mendeleev predicted new elements with specific properties to fill the gaps — gallium (1875), scandium (1879), and germanium (1886) were soon discovered and matched his predictions",
            "Mendeleev's gaps were filled by retroactively renaming existing elements — there were never any new elements to discover, and the predictions are a myth",
            "Mendeleev's table was abandoned because of the gaps — modern periodic tables are organized by different principles unrelated to Mendeleev's classification",
            "Mendeleev's gaps still remain empty today — predicted elements have never been found in nature or synthesized in any laboratory anywhere",
        ],
        "context": "Mendeleev's predictive successes — Eka-aluminum became gallium, Eka-boron became scandium, Eka-silicon became germanium, all with chemistry approximately as predicted — turned the periodic table from organizational convenience into a tool for scientific prediction. The modern arrangement by atomic number (Henry Moseley, 1913) rather than atomic weight resolves the few anomalies in Mendeleev's ordering. Mendeleev himself never won a Nobel; he was nominated several times.",
    },
    # 67 — Noble gases: discovery + chemistry
    {
        "tier": 4,
        "question": "The noble gases (helium, neon, argon, krypton, xenon, radon) sit in the rightmost column of the periodic table. For decades after their discovery in the 1890s by Ramsay and Rayleigh, they were thought to be entirely chemically inert. What changed that picture?",
        "answer": "Neil Bartlett in 1962 made the first noble-gas compound (xenon hexafluoroplatinate) — proving xenon and krypton can form real chemical bonds under the right conditions",
        "choices": [
            "Neil Bartlett in 1962 made the first noble-gas compound (xenon hexafluoroplatinate) — proving xenon and krypton can form real chemical bonds under the right conditions",
            "Marie Curie in 1898 produced helium chlorides — but her work was lost in WWI and the modern claim that noble gases form compounds is a retroactive correction",
            "Linus Pauling argued in 1939 that noble gases must form compounds — but his prediction has never been experimentally confirmed in any laboratory study",
            "Noble gases remain entirely inert as of the mid-2020s — the 1962 Bartlett experiment was retracted later that year — and no real compounds exist",
        ],
        "context": "Bartlett's discovery overturned a basic chemistry-textbook assumption. Xenon difluoride (XeF2), xenon tetrafluoride (XeF4), and xenon hexafluoride (XeF6) followed. Krypton compounds have been made; helium and neon remain the most stubbornly inert. The 'noble' name reflects the elements' early reluctance to react. Argon makes up about 1% of Earth's atmosphere, more than CO2; helium is mined from natural gas wells, where it accumulates from radioactive decay.",
    },
    # 68 — Hydrogen bonding water properties
    {
        "tier": 4,
        "question": "Water (H2O) has many unusual properties: high boiling point compared to other molecules of similar size, ice that floats on liquid water (unusual!), high surface tension, an unusual ability to dissolve many substances. What's the underlying chemistry that explains all these?",
        "answer": "Hydrogen bonding — partial positive H atoms attract partial negative O atoms in neighboring molecules — making liquid water a loosely-organized network, and ice a sparse open crystal",
        "choices": [
            "Hydrogen bonding — partial positive H atoms attract partial negative O atoms in neighboring molecules — making liquid water a loosely-organized network, and ice a sparse open crystal",
            "Covalent bonding — water's special O-H bonds give it all its unusual properties — and other molecules with O-H bonds (alcohols) behave just like water in every respect",
            "Metallic bonding — water has electrons that flow like in a metal — which is why ice conducts electricity well and dissolves so many substances readily",
            "Ionic bonding — water consists of H+ and O2- ions held together — and the strong ionic forces explain its unusual freezing and boiling behaviors directly",
        ],
        "context": "The 'hydrogen bond' is a weak intermolecular attraction — about 1/20th the strength of a covalent bond — but its cumulative effect in liquid water is huge. Ice has a hexagonal lattice with more empty space than liquid water, so ice floats. Water expands by ~9% on freezing, which is why pipes burst in winter and why aquatic life survives — frozen lakes have a liquid layer underneath. Hydrogen bonds also stabilize DNA's double helix and protein structures.",
    },
    # 69 — Mole concept Avogadro's number
    {
        "tier": 4,
        "question": "The 'mole' is the chemistry unit for counting atoms or molecules — specifically, 6.022 × 10^23 of whatever item you're counting (Avogadro's number). Why do chemists count atoms in moles rather than just by individual atoms?",
        "answer": "Atoms are so small that ordinary chemistry uses ~10^23 of them in any visible sample — the mole gives a manageable number, and one mole of carbon-12 weighs exactly 12 grams",
        "choices": [
            "Atoms are so small that ordinary chemistry uses ~10^23 of them in any visible sample — the mole gives a manageable number, and one mole of carbon-12 weighs exactly 12 grams",
            "Atoms come naturally in batches of 6.022 × 10^23 — every chemical sample contains an integer number of moles — and you can never split a mole into smaller groups",
            "Moles were chosen because they sound like a small furry animal — early French chemists wanted a homely word — and the number 6.022 × 10^23 has no special meaning",
            "Moles measure the volume of a gas at room temperature — one mole occupies one cubic meter — making the unit useful only for gas-phase chemistry experiments",
        ],
        "context": "Amedeo Avogadro's 1811 hypothesis (equal gas volumes at the same T and P contain equal numbers of particles) led to Avogadro's number. Modern measurement uses X-ray crystallography of silicon (the Kibble-balance redefinition of the kilogram, 2019, fixed Avogadro's number exactly at 6.02214076 × 10^23). The mole connects the macroscopic (grams, liters) to the microscopic (atoms, molecules) — a foundational bridge in quantitative chemistry.",
    },
    # 70 — Atoms: Rutherford 1909 nuclear model
    {
        "tier": 4,
        "question": "Ernest Rutherford's group at Manchester in 1909 fired alpha particles (helium nuclei) at very thin gold foil. They expected the particles to pass through with small deflections — J.J. Thomson's 'plum pudding' atom model predicted that. What did they actually see?",
        "answer": "Most particles passed through, but a small fraction bounced almost straight back — suggesting atoms have a tiny massive positive nucleus with most of the atom being empty space",
        "choices": [
            "Most particles passed through, but a small fraction bounced almost straight back — suggesting atoms have a tiny massive positive nucleus with most of the atom being empty space",
            "Every particle stopped at the foil — confirming Thomson's plum pudding model — and the modern nuclear picture of the atom is a misinterpretation of the data",
            "Every particle bounced straight back — atoms are solid impenetrable spheres — and the modern picture of an atomic nucleus surrounded by orbits is incorrect",
            "Particles passed through unchanged — atoms have no internal structure — and Rutherford's experiment marked the end of any serious atomic theory in physics",
        ],
        "context": "Rutherford famously said it was 'as if you fired a 15-inch shell at a piece of tissue paper and it came back and hit you.' Hans Geiger and Ernest Marsden did the actual experiments. Rutherford published the nuclear model in 1911. He had already won the 1908 Chemistry Nobel for earlier work on radioactivity. The atom is mostly empty space — a typical atomic diameter is ~10^-10 m, and the nucleus is ~10^-14 m across.",
    },
    # 71 — Chlorofluorocarbons + ozone
    {
        "tier": 4,
        "question": "Mario Molina and Sherwood Rowland in 1974 proposed that chlorofluorocarbons (CFCs) — the inert gases used in refrigerators and aerosol cans — could rise to the stratosphere, be broken apart by ultraviolet light, and release chlorine atoms that catalytically destroy ozone. What happened next?",
        "answer": "The Antarctic ozone hole was confirmed in 1985 by Joe Farman's team — the Montreal Protocol (1987) phased out CFCs — and the ozone layer has been gradually recovering",
        "choices": [
            "The Antarctic ozone hole was confirmed in 1985 by Joe Farman's team — the Montreal Protocol (1987) phased out CFCs — and the ozone layer has been gradually recovering",
            "Molina and Rowland's hypothesis was disproven in 1980 — CFCs do not actually affect ozone — and the Montreal Protocol was a needless economic disruption with no benefit",
            "The ozone layer was found to be increasing — Molina and Rowland's concern was reversed — and CFCs are still widely used in refrigeration without restriction",
            "Molina and Rowland refused to publish their findings — and the CFC-ozone connection remains a controversial fringe theory in atmospheric chemistry today",
        ],
        "context": "Molina, Rowland, and Paul Crutzen shared the 1995 Chemistry Nobel for the CFC-ozone work. The Montreal Protocol (1987) is one of the most successful international environmental treaties — universal ratification and gradual ozone recovery.",
    },
    # 72 — Reaction rates: catalysts industrial
    {
        "tier": 4,
        "question": "Catalysts speed up chemical reactions without being consumed. The Haber-Bosch process (1909-1913) for synthesizing ammonia from nitrogen and hydrogen uses iron catalysts at high temperature and pressure. What's the historical significance of Haber-Bosch?",
        "answer": "Ammonia synthesis lets factories make fertilizer from air — roughly half the world's population now relies on Haber-Bosch nitrogen — though the process is energy-intensive",
        "choices": [
            "Ammonia synthesis lets factories make fertilizer from air — roughly half the world's population now relies on Haber-Bosch nitrogen — though the process is energy-intensive",
            "Ammonia synthesis was never industrially feasible — the Haber-Bosch process was abandoned in the 1920s — and modern fertilizer comes from mined deposits worldwide",
            "Ammonia synthesis is used only for explosives — Haber-Bosch has no agricultural use — and global food supply still relies entirely on traditional farming methods",
            "Ammonia synthesis has been replaced by photosynthesis-mimicking enzymes — and Haber-Bosch is no longer in commercial use anywhere in the world today",
        ],
        "context": "Fritz Haber won the 1918 Chemistry Nobel; Carl Bosch won the 1931 Chemistry Nobel for scaling up the process. Haber also developed chemical weapons for Germany in WWI — chlorine gas at Ypres in 1915. His Jewish heritage led to his being driven from Germany under Nazi rule in 1933.",
    },
    # 73 — Radioactivity: half-life concept
    {
        "tier": 4,
        "question": "Radioactive isotopes decay at predictable statistical rates. After one 'half-life,' half the original atoms have decayed; after two, a quarter remain; after three, an eighth, and so on. What's the practical use of half-lives for measuring deep time?",
        "answer": "Radioactive dating — carbon-14 for organic remains up to ~50,000 years, uranium-lead for rocks billions of years old — measures ages by isotope ratios from known half-lives",
        "choices": [
            "Radioactive dating — carbon-14 for organic remains up to ~50,000 years, uranium-lead for rocks billions of years old — measures ages by isotope ratios from known half-lives",
            "Radioactive dating measures the temperature of an ancient sample — by comparing isotope heat signatures — but it does not measure the age of any sample",
            "Radioactive dating works only on materials less than 100 years old — beyond that, all isotopes have completely decayed — and ancient ages must be guessed from context",
            "Radioactive dating is no longer used because the half-lives are unstable — modern isotope ratios drift unpredictably — making the technique abandoned by geologists today",
        ],
        "context": "Willard Libby developed carbon-14 dating in 1949 (Nobel 1960). Uranium-lead dating put Earth's age at ~4.5 billion years (Clair Patterson, 1953). The Shroud of Turin was carbon-14 dated to 1260-1390 AD by three independent labs in 1988 — a result still disputed by some on contamination grounds. Half-life is a statistical property — individual atoms decay randomly, but the population's behavior is precisely predictable.",
    },
    # 74 — Combustion oxidation chemistry
    {
        "tier": 4,
        "question": "Combustion — burning — is a chemical reaction between a fuel and oxygen, usually producing CO2 and water plus a lot of heat. In the older 'phlogiston' theory (Stahl, ~1700) combustion was the loss of phlogiston FROM the burning substance. What did Lavoisier's careful weighing reveal?",
        "answer": "Burning materials GAIN mass when they combine with oxygen — phlogiston theory had it backwards — and Lavoisier renamed the gas 'oxygen' for its central role in combustion",
        "choices": [
            "Burning materials GAIN mass when they combine with oxygen — phlogiston theory had it backwards — and Lavoisier renamed the gas 'oxygen' for its central role in combustion",
            "Burning materials lose mass exactly as phlogiston theory predicted — Lavoisier's measurements actually confirmed Stahl's older framework after careful checking",
            "Burning materials change mass randomly — Lavoisier found no consistent pattern — and combustion remains a poorly-understood phenomenon as of the modern era",
            "Burning materials retain their original mass exactly — combustion is purely a heat phenomenon — and no chemical change is involved in the burning process",
        ],
        "context": "Lavoisier's careful sealed-container experiments showed that combustion of phosphorus or mercury produced a heavier compound — the gas (oxygen) was being absorbed, not phlogiston being released. The Greek-rooted name 'oxygen' comes from Lavoisier's (incorrect) belief that the gas was the universal acid-former; the name stuck anyway. Combustion of hydrocarbons (gasoline, methane) produces CO2 + H2O + heat — the basis of fossil-fuel energy.",
    },
    # 75 — Aspirin: synthesis history
    {
        "tier": 4,
        "question": "Felix Hoffmann at Bayer in 1897 synthesized acetylsalicylic acid — a modified form of salicylic acid (originally extracted from willow bark) that was easier on the stomach. Bayer marketed it as 'Aspirin' starting in 1899. What was the impact?",
        "answer": "Aspirin became one of the world's first widely-used synthetic drugs — pain relief, fever reduction, anti-inflammatory, and later low-dose for heart-attack prevention",
        "choices": [
            "Aspirin became one of the world's first widely-used synthetic drugs — pain relief, fever reduction, anti-inflammatory, and later low-dose for heart-attack prevention",
            "Aspirin was withdrawn from the market in 1920 — found to be too dangerous — and modern pain medications are unrelated to the original Bayer synthesis",
            "Aspirin was never commercially successful — Bayer's marketing failed — and salicylic acid from willow bark remains the dominant pain reliever in most countries",
            "Aspirin was banned globally in 2010 due to liver toxicity concerns — and the drug is no longer manufactured anywhere in the world for medical use",
        ],
        "context": "Hippocrates wrote about willow bark for fevers and pain in the 5th century BC. The active compound (salicin) was isolated by Joseph Buchner in 1828. Hoffmann's acetylation modification (and the Bayer brand) launched the modern pharmaceutical industry. The mechanism — inhibiting prostaglandin synthesis via COX enzymes — was worked out by John Vane in 1971 (Nobel 1982). Low-dose aspirin's cardiovascular benefits became prominent in the 1980s.",
    },
    # 76 — Plastics: Bakelite + early polymers
    {
        "tier": 4,
        "question": "Leo Baekeland in 1907 synthesized the first fully synthetic plastic — Bakelite — by reacting phenol with formaldehyde. It was hard, heat-resistant, electrically insulating, and could be molded into any shape. What was the broader significance?",
        "answer": "Bakelite launched the synthetic plastic era — phones, radios, electrical insulation, billiard balls, kitchenware — and triggered the explosion of plastic chemistry through the 20th century",
        "choices": [
            "Bakelite launched the synthetic plastic era — phones, radios, electrical insulation, billiard balls, kitchenware — and triggered the explosion of plastic chemistry through the 20th century",
            "Bakelite was never commercially successful — it was rapidly replaced by metal alternatives — and modern plastics owe nothing to Baekeland's original work in the early 1900s",
            "Bakelite was the only synthetic plastic ever made — no further plastics were developed until the 1980s — and today's polymers are unrelated to the original chemistry",
            "Bakelite was a natural rubber product — Baekeland did not synthesize anything new — and modern plastic chemistry started decades after his original Brooklyn lab work",
        ],
        "context": "Bakelite was crucial for early radios — its electrical insulation made vacuum-tube assemblies practical. Wallace Carothers at DuPont developed nylon in 1935 and neoprene in 1931. Plexiglas, polyethylene, PVC, polystyrene followed in the 1930s and 40s. The mid-20th-century plastic boom transformed packaging, clothing, transportation, and electronics. Modern concerns — plastic waste, microplastics — are the downside of that century-long explosion in polymer chemistry.",
    },
    # 77 — Carbon allotropes graphite, diamond, fullerenes
    {
        "tier": 4,
        "question": "Pure carbon exists in radically different solid forms: graphite (soft, conducts), diamond (hardest natural material, transparent), fullerenes (soccer-ball-shaped molecules, 1985), and graphene (single-atom-thick sheets, Nobel 2010). What's the chemistry behind such different properties from one element?",
        "answer": "The different bonding arrangements of carbon atoms — sheets, tetrahedra, balls, tubes — give wildly different physical properties despite identical elemental composition",
        "choices": [
            "The different bonding arrangements of carbon atoms — sheets, tetrahedra, balls, tubes — give wildly different physical properties despite identical elemental composition",
            "The different isotopes of carbon — carbon-12 vs carbon-13 vs carbon-14 — give wildly different physical properties despite identical bonding arrangements",
            "The different temperatures at which they form — diamonds need extreme heat, graphite needs none — give wildly different properties in the final material",
            "The different impurities present — graphite contains hydrogen, diamond contains oxygen — give wildly different properties despite identical bonding networks",
        ],
        "context": "Diamond's tetrahedral covalent bonds make it exceptionally hard. Graphite's planar hexagonal sheets are weakly bound (slippery pencil-lead). Fullerenes (Kroto, Curl, Smalley, 1985, Nobel 1996) include the iconic C60 'buckyball.' Graphene (Geim and Novoselov, 2010 Nobel) is a single atomic layer of graphite.",
    },
    # 78 — Chirality: Pasteur tartrates
    {
        "tier": 4,
        "question": "Louis Pasteur in 1848 — then 25 — examined crystals of tartrate salt under a microscope and noticed something extraordinary. The crystals came in two mirror-image forms — like left and right hands. He painstakingly separated them by hand with tweezers. What had he discovered?",
        "answer": "Chirality — many molecules exist as non-superimposable mirror images — and the two forms can have very different biological effects despite identical chemical formulas",
        "choices": [
            "Chirality — many molecules exist as non-superimposable mirror images — and the two forms can have very different biological effects despite identical chemical formulas",
            "Polarization — tartrate crystals all rotate light identically — and Pasteur's reported observation of mirror crystals was actually a measurement error he corrected",
            "Magnetism — tartrate crystals are weakly magnetic — and the mirror forms reverse the magnetic field direction without any chemical or biological implications",
            "Radiation — tartrate crystals emit X-rays — and Pasteur's microscope was actually detecting radiation rather than mirror-image molecular structures in the salt",
        ],
        "context": "Chirality became enormously important in pharmacology — thalidomide tragically taught the lesson in the 1950s and 60s: one enantiomer (R-thalidomide) was the intended sedative; the other (S-thalidomide) caused severe birth defects. Modern drug synthesis often requires producing only one enantiomer. Many biological molecules — amino acids, sugars, DNA — are chiral, and life uses almost exclusively one mirror form (L-amino acids, D-sugars).",
    },
    # 79 — Ozone layer formation + UV protection
    {
        "tier": 4,
        "question": "The ozone layer in the stratosphere — about 15-35 km up — absorbs most of the ultraviolet (UV-B and UV-C) radiation from the Sun before it reaches the surface. Without it, life as we know it on land would not be possible. What's the chemistry of ozone formation?",
        "answer": "UV light splits O2 molecules into individual O atoms, which combine with other O2 to form O3 (ozone) — the layer is maintained by continuous formation and destruction by UV",
        "choices": [
            "UV light splits O2 molecules into individual O atoms, which combine with other O2 to form O3 (ozone) — the layer is maintained by continuous formation and destruction by UV",
            "UV light combines hydrogen and nitrogen to form ozone — the layer is constantly created from atmospheric gases — and the chemistry has nothing to do with oxygen at all",
            "Ozone is produced by ground-level industrial pollution that rises — the stratospheric layer comes from urban smog — and would not exist without human activity",
            "Ozone is solid crystalline matter that fell to Earth from comets — the layer is a permanent fixed deposit — and is not maintained by any ongoing chemical process",
        ],
        "context": "The ozone layer is in dynamic equilibrium — constantly being made and destroyed by UV. Sydney Chapman worked out the chemistry in 1930. Total stratospheric ozone is roughly 3 mm thick if compressed to ground-level pressure. The Antarctic ozone 'hole' (depletion to ~50% of normal in spring) was identified in 1985. The Montreal Protocol's phase-out of CFCs has been one of the rare global-scale environmental success stories.",
    },
    # 80 — Acid-base reactions: salt formation
    {
        "tier": 4,
        "question": "Mix hydrochloric acid (HCl) with sodium hydroxide (NaOH) and you get table salt (NaCl) plus water. The H+ ions from the acid combine with the OH- ions from the base to form H2O, leaving the Na+ and Cl- as a dissolved salt. What's the general pattern called?",
        "answer": "Neutralization reaction — acid plus base yields a salt plus water — one of the most basic and important reaction types in inorganic chemistry, the foundation of titration analysis",
        "choices": [
            "Neutralization reaction — acid plus base yields a salt plus water — one of the most basic and important reaction types in inorganic chemistry, the foundation of titration analysis",
            "Combustion reaction — acid plus base produces flame and smoke — making this the most energetic reaction type known in inorganic chemistry textbooks worldwide",
            "Decomposition reaction — the salt always breaks down — making this a fragile reaction type that cannot be used for any practical chemistry application",
            "Reduction reaction — the base reduces the acid's electrons — making this an electron-transfer process unrelated to ordinary salt-making in chemistry",
        ],
        "context": "Titration uses the neutralization reaction to determine unknown acid or base concentrations — a precise drop-by-drop addition until the color of an indicator changes at the equivalence point. Antacids (calcium carbonate, magnesium hydroxide) work by neutralizing stomach acid. The Brønsted-Lowry definition (1923) generalized acids and bases as proton donors and acceptors, extending the framework beyond water-based reactions to broader chemistry.",
    },
    # 81 — Catalysts: enzymes vs industrial
    {
        "tier": 4,
        "question": "Both enzymes (biological catalysts) and industrial catalysts (like the iron in Haber-Bosch or the platinum in catalytic converters) speed up reactions without being consumed. But enzymes have a property industrial catalysts mostly lack. What is it?",
        "answer": "Enzymes are extraordinarily specific — typically catalyzing one reaction or one class — while industrial catalysts often accelerate broad families of reactions and lack that fine selectivity",
        "choices": [
            "Enzymes are extraordinarily specific — typically catalyzing one reaction or one class — while industrial catalysts often accelerate broad families of reactions and lack that fine selectivity",
            "Enzymes work only at room temperature — industrial catalysts work over a wide range — and the temperature difference is the most important distinction between them",
            "Enzymes are made of metal atoms — industrial catalysts are made of proteins — and the elemental composition is the main difference between the two kinds of catalyst",
            "Enzymes are consumed in each reaction — industrial catalysts are not — and the regeneration of enzymes after each cycle is what makes biological chemistry work",
        ],
        "context": "Enzymes work at body temperature, neutral pH, and aqueous conditions — gentle conditions where most industrial catalysts wouldn't work. Their specificity comes from the precisely-shaped active site. Modern 'biocatalysis' tries to harness enzymes (or engineered variants) for industrial chemistry — synthesizing high-value compounds with fewer side products and lower energy than traditional catalysis would require. Frances Arnold (2018 Chemistry Nobel) pioneered 'directed evolution' for enzyme engineering.",
    },
    # 82 — Stoichiometry: balanced equations
    {
        "tier": 4,
        "question": "A balanced chemical equation has the same number of each kind of atom on both sides of the arrow. Methane combustion is CH4 + 2 O2 → CO2 + 2 H2O. The coefficients (2 in front of O2 and H2O) are required for atom balance. Why must equations be balanced?",
        "answer": "Conservation of mass — atoms are not created or destroyed in ordinary reactions — so the same number of each element must appear on both sides of the equation",
        "choices": [
            "Conservation of mass — atoms are not created or destroyed in ordinary reactions — so the same number of each element must appear on both sides of the equation",
            "Energy conservation — the equation must balance heat in and out — and adjusting coefficients is how chemists account for thermal energy of combustion",
            "Charge conservation — equations must balance positive and negative ions — but only in solutions where ions are present in significant detectable concentrations",
            "Volume conservation — the equation must keep the total gas volume constant — but only for reactions involving gases under fixed pressure and temperature conditions",
        ],
        "context": "Balanced equations let chemists calculate quantities — predict how much CO2 a fuel produces, how much oxygen a reaction needs, how much product to expect from given reactants. Stoichiometry is one of the most practical applications of chemistry, used in everything from rocketry to pharmaceutical synthesis to environmental modeling. The mole ratio in a balanced equation translates directly to mass ratios via molar masses.",
    },
    # 83 — Salt water and electrolyte: ions
    {
        "tier": 4,
        "question": "Dissolve table salt (NaCl) in water and the resulting solution conducts electricity, while pure water barely conducts at all. The dissolved salt has separated into something that carries charge. What are those carriers?",
        "answer": "Ions — Na+ (positively charged) and Cl- (negatively charged) particles dispersed in the water — free to move and carry electric current through the solution",
        "choices": [
            "Ions — Na+ (positively charged) and Cl- (negatively charged) particles dispersed in the water — free to move and carry electric current through the solution",
            "Atoms — neutral Na and Cl floating between water molecules — somehow conducting electricity despite having no net charge between them in the resulting mixture",
            "Molecules — intact NaCl pairs swimming through the water — somehow conducting electricity despite having no net charge in the dissolved state at all",
            "Electrons — free electrons flowing through the salt water — moving directly between salt grains while bypassing the water molecules entirely along the way",
        ],
        "context": "Svante Arrhenius proposed the ionic dissociation theory in 1884 — initially mocked, then awarded the 1903 Chemistry Nobel. Pure water has very few ions (H+ and OH- at ~10^-7 molar each) and is a poor conductor. Salt water — and biological fluids like blood and saline — conducts well. The conductivity-from-ions principle underlies batteries, electrolysis, electrochemical sensors, and electrophysiology (nerve signals as ion-flow events).",
    },
    # 84 — Quantum mechanics in chemistry: orbitals
    {
        "tier": 4,
        "question": "Electrons in atoms don't orbit like little planets — that picture is wrong. Quantum mechanics describes them with 'orbitals' — three-dimensional probability clouds with shapes labeled s (spherical), p (dumbbell), d (more complex), and f. Why does this matter for chemistry?",
        "answer": "The orbital shapes determine which atoms bond, how they bond, and what shapes the resulting molecules take — bond angles, polarity, reactivity all follow from electron-cloud structure",
        "choices": [
            "The orbital shapes determine which atoms bond, how they bond, and what shapes the resulting molecules take — bond angles, polarity, reactivity all follow from electron-cloud structure",
            "The orbital shapes are mathematical fictions — every electron actually orbits in a perfect circle — and the cloud pictures are just teaching aids without real meaning",
            "The orbital shapes determine the color of the atoms — but they have nothing to do with chemical bonding — which is governed entirely by atomic mass instead",
            "The orbital shapes are identical for every atom — they only differ in size — and chemistry depends entirely on the size of the orbital, not the shape of any cloud",
        ],
        "context": "The 1926 Schrödinger equation gave atomic orbitals their modern form. Hybridization theory (Linus Pauling, 1931) explains how s and p orbitals combine to form bonds with specific angles — sp3 hybrids give carbon's tetrahedral bonding, sp2 gives the planar geometry of benzene and graphene, sp gives linear geometry. The shapes of orbitals dictate the shapes of molecules — and the shapes of molecules dictate biology.",
    },
    # 85 — Materials science: semiconductors
    {
        "tier": 4,
        "question": "Pure silicon is a poor conductor of electricity — better than insulators like glass, worse than metals like copper. But add a tiny amount of phosphorus (5 electrons per atom vs silicon's 4) or boron (3 electrons) and conductivity changes dramatically. What's the broader idea?",
        "answer": "Doping a semiconductor — adding controlled impurities — creates 'n-type' (extra electrons) or 'p-type' (electron holes) materials, the building blocks of transistors and modern electronics",
        "choices": [
            "Doping a semiconductor — adding controlled impurities — creates 'n-type' (extra electrons) or 'p-type' (electron holes) materials, the building blocks of transistors and modern electronics",
            "Doping a semiconductor poisons it — adding impurities reduces conductivity to zero — and pure silicon is used in all modern electronics without any added elements",
            "Doping a semiconductor changes its color — adding impurities makes silicon glow — but does not affect electrical properties in any commercially useful way",
            "Doping a semiconductor melts it — silicon becomes liquid when impurities are added — making semiconductor electronics inherently fragile and short-lived",
        ],
        "context": "The transistor (Bardeen, Brattain, Shockley at Bell Labs, 1947 — 1956 Nobel) is the engine of the information age. Modern microprocessors contain billions of transistors on a single chip. The semiconductor industry is one of the largest applied uses of chemistry.",
    },
    # 86 — Buffers: physiology blood pH
    {
        "tier": 4,
        "question": "Human blood is maintained at a pH of about 7.4 with extraordinary tightness — variations beyond about 7.0 to 7.7 can be fatal. The body achieves this through 'buffer systems' that resist pH change when small amounts of acid or base are added. What's the main blood buffer?",
        "answer": "The bicarbonate-carbonic acid buffer — CO2 + H2O ↔ H2CO3 ↔ H+ + HCO3- — which absorbs added acid by shifting to the left, and added base by shifting to the right",
        "choices": [
            "The bicarbonate-carbonic acid buffer — CO2 + H2O ↔ H2CO3 ↔ H+ + HCO3- — which absorbs added acid by shifting to the left, and added base by shifting to the right",
            "The albumin protein only — blood's only buffer is a single protein — and bicarbonate plays no role in maintaining the body's tight pH range across organs",
            "The sodium chloride pump — table salt in blood acts as a chemical buffer — keeping pH stable across all body fluids without any other components present",
            "The water itself acts as the only buffer — H2O alone resists pH change — and dissolved gases or proteins make no contribution to blood acid balance at all",
        ],
        "context": "The bicarbonate buffer system is reinforced by the lungs (which can blow off CO2 quickly to lower pH back toward 7.4) and the kidneys (which can excrete or retain H+ and HCO3- over longer timescales). The Henderson-Hasselbalch equation relates pH to the ratio of bicarbonate to carbonic acid concentrations. Severe deviations (acidosis, alkalosis) are medical emergencies; chronic disturbances accompany conditions like uncontrolled diabetes and kidney failure.",
    },
    # 87 — Saturated vs unsaturated fats
    {
        "tier": 4,
        "question": "Fats and oils are triglycerides — three fatty-acid chains attached to a glycerol backbone. Saturated fats have all single bonds between the carbons; unsaturated fats have one or more double bonds. Why does that difference matter for melting point and texture?",
        "answer": "Saturated chains pack tightly and stay solid (lard, butter) — unsaturated chains have kinks at double-bond positions and stay liquid (olive oil, fish oil)",
        "choices": [
            "Saturated chains pack tightly and stay solid (lard, butter) — unsaturated chains have kinks at double-bond positions and stay liquid (olive oil, fish oil)",
            "Saturated chains pack loosely and stay liquid — unsaturated chains pack tightly and are solid — modern nutritional advice is based on a reversed model",
            "Saturated chains are smaller molecules — unsaturated chains are larger — making the only chemical difference one of molecular weight and total carbon count",
            "Saturated chains are negatively charged — unsaturated chains are positively charged — making them behave like ionic compounds rather than uncharged organic ones",
        ],
        "context": "Trans fats — partially hydrogenated vegetable oils — were introduced as solid butter substitutes (margarine) but were later linked to cardiovascular disease and largely phased out (US FDA ban took effect 2018). The 'saturated fat is dangerous' framing from the 1960s-2010s has been increasingly questioned — Nina Teicholz's *The Big Fat Surprise* (2014) traces how Ancel Keys's seven-countries study shaped policy.",
    },
    # 88 — Cholesterol: structure + role
    {
        "tier": 4,
        "question": "Cholesterol is a steroid found in animal cell membranes and used as the starting material for hormones (testosterone, estrogen, cortisol). Despite a public-health framing as dangerous, it has critical biological roles. What does it do?",
        "answer": "It stiffens cell membranes — serves as the precursor for steroid hormones and bile acids — and is essential for life, since the body synthesizes it even if you eat none in food",
        "choices": [
            "It stiffens cell membranes — serves as the precursor for steroid hormones and bile acids — and is essential for life, since the body synthesizes it even if you eat none in food",
            "It clogs arteries and serves no biological purpose — the body produces it as a metabolic mistake — and cholesterol-free diets are healthiest by every metric",
            "It is a toxic waste product of digestion — the liver works constantly to remove cholesterol — making low-cholesterol food choices essential for adult survival",
            "It is a poison synthesized by gut bacteria — the body cannot make its own cholesterol — and dietary intake is the only source for all cells in the body",
        ],
        "context": "Cholesterol's role in cell membranes was characterized in detail through the 20th century. Statins — blocking cholesterol synthesis in the liver — are among the most prescribed drugs worldwide. The 'lipid hypothesis' linking dietary cholesterol to heart disease has been increasingly nuanced.",
    },
    # 89 — Reaction kinetics: temperature dependence
    {
        "tier": 4,
        "question": "Most chemical reactions go faster at higher temperatures. A common rule of thumb (Arrhenius equation, 1889) is that reaction rates roughly double for every 10°C increase. Why does temperature have such a dramatic effect?",
        "answer": "Molecules need a minimum 'activation energy' to react — at higher temperatures, more molecules have enough kinetic energy to clear that barrier per unit time",
        "choices": [
            "Molecules need a minimum 'activation energy' to react — at higher temperatures, more molecules have enough kinetic energy to clear that barrier per unit time",
            "Molecules are more numerous at higher temperatures — heating actually creates more molecules — and the higher density of reactants causes the faster rate at high temperature",
            "Molecules become charged at higher temperatures — heating ionizes them — and the resulting electrical forces drive all the chemistry at any elevated temperature",
            "Molecules emit light at higher temperatures — the emitted photons trigger reactions — and lower-temperature reactions are slow because no photons are produced",
        ],
        "context": "Svante Arrhenius (1889) gave the formula k = A exp(-Ea/RT) — exponential dependence of rate on temperature. The exponential form means small temperature increases give large rate increases. This is why refrigeration preserves food (slows microbial growth), why fevers fight infection (faster immune response), and why industrial chemistry uses heat. Catalysts work by lowering the activation energy — opening an alternative reaction pathway with a smaller barrier.",
    },
    # 90 — Solubility: like dissolves like
    {
        "tier": 4,
        "question": "Salt dissolves in water but not in oil. Sugar dissolves in water but not in gasoline. Wax dissolves in gasoline but not in water. The pattern follows a chemistry rule of thumb: 'like dissolves like.' What does that mean in molecular terms?",
        "answer": "Polar substances (water, salt, sugar) dissolve in polar solvents — non-polar substances (wax, fats, oils) dissolve in non-polar solvents (gasoline, organic solvents)",
        "choices": [
            "Polar substances (water, salt, sugar) dissolve in polar solvents — non-polar substances (wax, fats, oils) dissolve in non-polar solvents (gasoline, organic solvents)",
            "Heavy substances dissolve in heavy solvents — light substances dissolve in light solvents — molecular weight alone determines whether dissolution happens at all",
            "Solid substances dissolve only in solids — liquid substances dissolve only in liquids — phase compatibility is what determines solubility behavior in chemistry",
            "Hot substances dissolve in cold solvents — cold substances dissolve in hot solvents — temperature contrast alone determines whether two materials mix together",
        ],
        "context": "Water is polar because the O-H bonds are polar and the molecule is bent (105° angle), giving it a permanent dipole. Hydrocarbons are non-polar because C-C and C-H bonds are nearly non-polar. The 'like dissolves like' rule is the practical face of intermolecular forces — dipole-dipole, hydrogen-bond, and London-dispersion.",
    },
]


# ============================================================================
# P3 BIOLOGY (50)
# ============================================================================

P3: list[dict] = [
    # 91 — CRISPR Doudna + Charpentier 2020 Nobel
    {
        "tier": 4,
        "question": "Jennifer Doudna (Berkeley) and Emmanuelle Charpentier (Max Planck) shared the 2020 Chemistry Nobel for developing CRISPR-Cas9 as a programmable gene-editing tool — their key paper appeared in Science in 2012. The underlying CRISPR system was first identified somewhere nobody expected. Where did it come from?",
        "answer": "It's a bacterial immune system — bacteria use CRISPR to chop up invading viruses by storing snippets of viral DNA — Doudna and Charpentier repurposed it as a programmable cut-and-paste tool",
        "choices": [
            "It's a bacterial immune system — bacteria use CRISPR to chop up invading viruses by storing snippets of viral DNA — Doudna and Charpentier repurposed it as a programmable cut-and-paste tool",
            "It was synthesized from scratch in a Berkeley lab — Doudna built CRISPR atom by atom — there is no natural equivalent of the system anywhere",
            "It was discovered in human cells in 2010 — CRISPR is a normal human DNA-repair pathway — Doudna and Charpentier accidentally found it studying cancer",
            "It was first found in plants — agricultural research isolated CRISPR from wheat — and the system was only later adapted for use in animal cells",
        ],
        "context": "CRISPR (clustered regularly interspaced short palindromic repeats) was first noticed in bacterial genomes in 1987 by Yoshizumi Ishino. Francisco Mojica connected the repeats to viral immunity in 2005. Doudna and Charpentier's 2012 paper showed how to reprogram the Cas9 enzyme to cut any DNA sequence. Feng Zhang at the Broad demonstrated CRISPR in mammalian cells.",
    },
    # 92 — Human Genome Project 1990-2003
    {
        "tier": 4,
        "question": "The Human Genome Project ran 1990-2003 — a 13-year, $3-billion international effort to sequence all 3 billion base pairs of human DNA. A private company (Celera, led by Craig Venter) raced the public consortium; they announced 'completion' jointly in 2000. One surprise from the final sequence overturned a common expectation. What was it?",
        "answer": "Humans have only about 20,000-25,000 protein-coding genes — far fewer than the 100,000+ many biologists had predicted before sequencing was completed",
        "choices": [
            "Humans have only about 20,000-25,000 protein-coding genes — far fewer than the 100,000+ many biologists had predicted before sequencing was completed",
            "Humans have about 500,000 genes — vastly more than expected — and the project had to be extended by a decade to account for the unexpected complexity",
            "Humans have about 6 genes per chromosome — almost no genetic material — and the project ended with major doubts about how genes actually work",
            "Humans have exactly the same gene count as bacteria (about 4,000) — and the project ended by overturning the very concept of genetic complexity",
        ],
        "context": "The 20,000-25,000 gene count places humans only modestly above a roundworm (~20,000) or fruit fly (~14,000). Complexity apparently comes more from gene regulation, alternative splicing, and non-coding RNA than from raw gene count. The HGP also revealed that 1-2% of the genome codes for proteins; the rest had been dismissed as 'junk DNA' but is increasingly seen to have regulatory functions.",
    },
    # 93 — Epigenetics: DNA methylation
    {
        "tier": 4,
        "question": "Two genetically identical twins can have different gene-expression patterns and different traits — sometimes including disease susceptibility. The 'epigenome' is a layer of chemical modifications to DNA and its proteins that doesn't change the DNA sequence but does change how genes are read. What's a major mechanism?",
        "answer": "DNA methylation — adding methyl groups to specific bases — typically silences gene expression, and these patterns can be inherited or changed by environment",
        "choices": [
            "DNA methylation — adding methyl groups to specific bases — typically silences gene expression, and these patterns can be inherited or changed by environment",
            "DNA mutation — random sequence changes from cosmic rays — alters gene function — but this is genetic rather than epigenetic by the standard definition",
            "DNA replication — copying the genome before cell division — cannot be epigenetic by definition — and is unrelated to how identical twins differ",
            "DNA crossing-over — exchanging segments between chromosomes",
        ],
        "context": "Epigenetic changes include DNA methylation (mostly at CpG sites), histone modifications (acetylation, methylation, phosphorylation), and chromatin remodeling. Some epigenetic marks are heritable across generations — the Dutch Hunger Winter (1944-45) cohort showed grandchildren of starvation-exposed grandparents had altered methylation patterns.",
    },
    # 94 — Gene therapy celebrated: Casgevy 2023 sickle cell
    {
        "tier": 4,
        "question": "In December 2023 the US FDA approved Casgevy — the first CRISPR-based gene therapy ever approved — for sickle cell disease. The treatment edits a patient's own blood stem cells to reactivate fetal hemoglobin production, effectively curing the painful inherited disorder. Why is this historically important?",
        "answer": "It's the first commercially approved CRISPR therapy in human medicine — a 60-year-old genetic disease that caused lifelong suffering is now curable by direct gene editing",
        "choices": [
            "It's the first commercially approved CRISPR therapy in human medicine — a 60-year-old genetic disease that caused lifelong suffering is now curable by direct gene editing",
            "It's the first approval to use ordinary antibiotics — sickle cell was finally controlled in 2023 by penicillin treatment — without any genetic modification",
            "It's the first time the FDA approved a placebo as a real therapy — Casgevy contains no active ingredients — and the approval marks a regulatory mistake",
            "It's the first treatment to reverse aging completely — Casgevy extends lifespan to over 200 years — and sickle cell was a minor side effect of treatment",
        ],
        "context": "Casgevy (exa-cel) was developed by Vertex Pharmaceuticals and CRISPR Therapeutics (co-founded by Charpentier). Treatment costs about $2.2 million. Sickle cell affects ~100,000 Americans. Other landmark gene therapies: Zolgensma (2019) for SMA in infants; Luxturna (2017) for inherited blindness; CAR-T cell therapies for certain leukemias and lymphomas.",
    },
    # 95 — Zolgensma SMA
    {
        "tier": 4,
        "question": "Zolgensma is a gene therapy approved by the FDA in 2019 for spinal muscular atrophy (SMA) in children under 2. SMA is caused by a defective SMN1 gene; untreated, the severe form is usually fatal before age 2. Zolgensma delivers a working copy of the gene via an adeno-associated virus. What's the cost?",
        "answer": "About $2.1 million as a one-time treatment — making it among the most expensive single doses ever priced — but it's a one-shot cure for a previously fatal disease",
        "choices": [
            "About $2.1 million as a one-time treatment — making it among the most expensive single doses ever priced — but it's a one-shot cure for a previously fatal disease",
            "About $20 a dose — making it one of the cheapest medicines available — and SMA was already a common minor childhood illness easily managed by family doctors",
            "Free for all patients — the manufacturer donates it without charge — and the price reflects only the cost of materials needed for distribution",
            "About $50 million per treatment — too expensive for any insurance system — and Zolgensma has therefore never been given to any patient anywhere",
        ],
        "context": "Zolgensma (onasemnogene abeparvovec) was developed at Nationwide Children's Hospital and acquired by Novartis. Treatment as early as possible — ideally pre-symptomatic — gives the best outcomes; many states now screen newborns for SMA. The pricing reflects the 'value-based' argument that a one-time cure costs less than decades of supportive care.",
    },
    # 96 — He Jiankui 2018 CRISPR babies
    {
        "tier": 4,
        "question": "In November 2018, Chinese scientist He Jiankui announced he had edited the genomes of human embryos using CRISPR — to disable the CCR5 gene as a putative HIV-resistance edit — and that two baby girls (Lulu and Nana) had been born. The international scientific community reacted strongly. What happened to He?",
        "answer": "He was condemned, fired, and sentenced to 3 years in Chinese prison — the case became the canonical example of premature heritable human gene editing without proper consent",
        "choices": [
            "He was condemned, fired, and sentenced to 3 years in Chinese prison — the case became the canonical example of premature heritable human gene editing without proper consent",
            "He was awarded the Nobel Prize in 2020 — the scientific community celebrated — and the entire framework should be reconsidered",
            "He continued his work without consequence — the Chinese government praised it — and the entire framework should be reconsidered",
            "He retracted his announcement in 2019 — admitting it was an elaborate hoax — and the entire framework should be reconsidered",
        ],
        "context": "He's experiments violated international guidelines and basic research ethics — no IRB approval, parents deceived about the experimental nature, premature use of an unproven technique. He was sentenced to 3 years and a $430,000 fine in December 2019. Proper safety evaluation of CCR5 edits in humans remains lacking.",
    },
    # 97 — Koch's postulates
    {
        "tier": 4,
        "question": "Robert Koch in the 1880s formalized four criteria — now 'Koch's postulates' — for proving that a specific microbe causes a specific disease. They became the rigorous standard for establishing infectious-disease etiology. What's the core idea?",
        "answer": "Isolate the microbe from sick hosts — grow it in pure culture — reinoculate a healthy host to produce the same disease — and re-isolate the same microbe from the new host",
        "choices": [
            "Isolate the microbe from sick hosts — grow it in pure culture — reinoculate a healthy host to produce the same disease — and re-isolate the same microbe from the new host",
            "Observe the microbe under a microscope only — no further testing is required — and Koch's standard ends with simple visual identification of the organism",
            "Vaccinate against the microbe — if the vaccine works, the microbe causes the disease — and Koch's postulates are essentially a one-step vaccination test",
            "Compare microbial DNA — by sequencing, identical DNA in sick patients proves causation — and Koch invented genetic sequencing decades before its rediscovery",
        ],
        "context": "Koch used the postulates to nail down the bacterial causes of anthrax (1876), tuberculosis (1882, Nobel 1905), and cholera (1884). Modern microbiology often can't strictly apply all four postulates — viruses can't always be cultured in pure form, some diseases require special host conditions, and many microbes are uncultivable. The 'molecular Koch's postulates' (Stanley Falkow, 1988) extend the framework using genetics. The original postulates remain the foundational logic of infectious-disease etiology.",
    },
    # 98 — 1986 NCVIA structural concern
    {
        "tier": 4,
        "question": "Congress passed the National Childhood Vaccine Injury Act in 1986, creating the Vaccine Injury Compensation Program and shielding manufacturers from most childhood-vaccine liability lawsuits. The CDC schedule has expanded from ~11 doses by age 6 in 1986 to ~70+ by age 18. What's the structural concern critics name?",
        "answer": "Removing manufacturer liability changes incentives — vaccine makers can't be sued the way other drug makers can — weakening normal market-discipline pressure on safety",
        "choices": [
            "Removing manufacturer liability changes incentives — vaccine makers can't be sued the way other drug makers can — weakening normal market-discipline pressure on safety",
            "Vaccines were declared exempt from medical-ethics review — with no oversight at all — and the entire framework should be reconsidered",
            "The 1986 law made vaccines free for all children regardless of income — and the entire framework should be reconsidered",
            "The 1986 law banned all future research into vaccine safety — and the entire framework should be reconsidered",
        ],
        "context": "Pre-1986 vaccine-injury lawsuits had threatened manufacturer participation in the childhood market. The NCVIA shielded manufacturers and created VICP as no-fault compensation. Critics including RFK Jr. and Aaron Siri argue the liability shield combined with mandate pressure weakens market discipline. RFK Jr. became HHS Secretary in 2025.",
    },
    # 99 — Vaccination history Salk + Sabin
    {
        "tier": 4,
        "question": "Polio paralyzed thousands of American children every year in the early 1950s. Jonas Salk introduced his inactivated injectable vaccine in 1955; Albert Sabin's live-attenuated oral vaccine was licensed in 1961-62. Both were major triumphs. What did Salk famously say when asked who held the patent?",
        "answer": "'Could you patent the sun?' — Salk had refused to patent it, donating his work as a public good — the vaccine spread worldwide without patent restrictions",
        "choices": [
            "'Could you patent the sun?' — Salk had refused to patent it, donating his work as a public good — the vaccine spread worldwide without patent restrictions",
            "'It will be the most profitable patent in history' — Salk made hundreds of millions of dollars in licensing fees",
            "'I have no comment on commercial matters' — Salk refused to discuss the patent",
            "'My lawyers will handle it' — Salk transferred his patent to a private company",
        ],
        "context": "Salk's IPV is given by injection; Sabin's OPV is administered as drops. OPV was preferred globally for decades because it's cheap and induces gut immunity that blocks transmission. Since 2000 the US has used only IPV. Polio has been eradicated from the Americas and most of the world; reservoirs remain in parts of Afghanistan and Pakistan as of the mid-2020s.",
    },
    # 100 — Maurice Hilleman 40+ vaccines
    {
        "tier": 4,
        "question": "Maurice Hilleman (1919-2005), working mostly at Merck, developed about 40 vaccines — including measles, mumps, rubella, hepatitis A, hepatitis B, varicella, meningitis, pneumococcal, and Haemophilus influenzae type B. The MMR combination is largely his work. Why is he relatively unknown to the public?",
        "answer": "He avoided publicity and the spotlight throughout his career — working quietly at Merck — yet his vaccines have probably saved more lives than any individual scientist in history",
        "choices": [
            "He avoided publicity and the spotlight throughout his career — working quietly at Merck — yet his vaccines have probably saved more lives than any individual scientist in history",
            "He was disgraced by a scientific fraud — his vaccines were withdrawn after his death — and the entire framework should be reconsidered",
            "He never actually existed — Maurice Hilleman is a Merck marketing invention — and the entire framework should be reconsidered",
            "He was active only briefly — Hilleman developed only 2 vaccines — and modern science has retired this framing entirely",
        ],
        "context": "Hilleman's mumps vaccine famously used a virus he isolated from his own daughter Jeryl Lynn's throat — the 'Jeryl Lynn strain' is still the basis of every mumps vaccine today. He grew up on a Montana farm during the Depression. Paul Offit's biography *Vaccinated* (2007) is the standard reference.",
    },
    # 101 — VAERS Harvard Pilgrim 2010
    {
        "tier": 4,
        "question": "VAERS (Vaccine Adverse Event Reporting System) is the federal database where US doctors and patients can report vaccine adverse events. A 2010 Harvard Pilgrim Health Care study — funded by an HHS grant — sought to develop automated electronic VAERS reporting. What did the study find?",
        "answer": "Fewer than 1% of vaccine adverse events appeared to be reported to VAERS — suggesting the existing database vastly under-counts events — though HHS reportedly did not implement the proposed electronic reporting",
        "choices": [
            "Fewer than 1% of vaccine adverse events appeared to be reported to VAERS — suggesting the existing database vastly under-counts events — though HHS reportedly did not implement the proposed electronic reporting",
            "About 99% of all events were being reported to VAERS — the existing system was essentially complete — and the entire framework should be reconsidered",
            "VAERS reports were 80-90% complete — the existing system worked well — and this view is preserved in standard textbooks today",
            "VAERS reports actually exceeded the true rate of events — over-reporting was a problem — and the entire framework should be reconsidered",
        ],
        "context": "The Harvard Pilgrim study (Lazarus et al., 2010, AHRQ Grant R18 HS 017045) developed an automated EHR-based reporting system. The team reported that follow-through was discontinued. The under-reporting figure has been widely cited by vaccine-safety critics including RFK Jr. and Aaron Siri. VAERS is a passive surveillance system designed to detect signals rather than measure absolute rates.",
    },
    # 102 — Marshall + Warren H. pylori full arc
    {
        "tier": 4,
        "question": "Barry Marshall and Robin Warren identified Helicobacter pylori in ulcer biopsies in 1982 and proposed the bacteria caused ulcers. Medical orthodoxy refused to consider a bacterial cause — stomach acid 'obviously' killed bacteria. Marshall drank a beaker of H. pylori in 1984 to prove the point. What was the eventual outcome?",
        "answer": "Marshall and Warren won the 2005 Nobel in Medicine — ulcers are now routinely cured with antibiotics — a treatment unimaginable under the old stress-and-spicy-food consensus",
        "choices": [
            "Marshall and Warren won the 2005 Nobel in Medicine — ulcers are now routinely cured with antibiotics — a treatment unimaginable under the old stress-and-spicy-food consensus",
            "Marshall and Warren were quickly vindicated within months — the medical establishment immediately accepted their findings",
            "Marshall and Warren remained controversial — their work has never been fully accepted",
            "Marshall and Warren retracted their findings in 1988 — admitting the original interpretation was wrong",
        ],
        "context": "Marshall self-experimented after frustration with the slow medical acceptance — drinking H. pylori, developing gastritis, then curing himself with antibiotics. The case is a paradigmatic example of consensus being wrong and an outsider's experiment overturning decades of teaching. Marshall has been outspoken about institutional resistance to challenges.",
    },
    # 103 — Fleming 1928 + Florey/Chain Oxford scale-up
    {
        "tier": 4,
        "question": "Alexander Fleming famously discovered penicillin in 1928 from a contaminated petri dish at St Mary's Hospital, London. He published in 1929 but couldn't isolate the active compound at useful scale. The hard chemistry work was done at Oxford in 1940-41 by Howard Florey, Ernst Chain, and Norman Heatley. Who shared the 1945 Nobel?",
        "answer": "Fleming, Florey, and Chain shared the 1945 Medicine Nobel — though Heatley, who did much of the practical scale-up engineering, was not included in the prize that year",
        "choices": [
            "Fleming, Florey, and Chain shared the 1945 Medicine Nobel — though Heatley, who did much of the practical scale-up engineering, was not included in the prize that year",
            "Fleming alone received the 1945 Medicine Nobel — Florey and Chain were not credited at all",
            "Florey and Chain alone shared the 1945 Medicine Nobel — Fleming was excluded for his earlier failure to scale up",
            "Heatley alone received the 1945 Medicine Nobel — for the practical scale-up",
        ],
        "context": "Fleming's discovery was the lucky observation; Florey and Chain's chemistry made it usable. Heatley's bedpan-and-bathtub fermentation setup at the Dunn School of Pathology produced enough penicillin for the first human trials in 1941. American pharmaceutical companies scaled production to industrial levels in 1942-44. By D-Day 1944 mass-produced penicillin was saving Allied soldiers.",
    },
    # 104 — Norman Borlaug Nobel Peace 1970
    {
        "tier": 4,
        "question": "Norman Borlaug — son of Norwegian immigrants to Iowa — spent 30 years in Mexico, then India and Pakistan, developing rust-resistant dwarf wheat varieties. Harvests doubled or tripled. Population biologists estimate his work prevented mass starvation of about a billion people. What recognition did he receive?",
        "answer": "The 1970 Nobel Peace Prize — making Borlaug one of the few non-political figures to win for peace — for ending famine through agricultural science (the 'Green Revolution')",
        "choices": [
            "The 1970 Nobel Peace Prize — making Borlaug one of the few non-political figures to win for peace — for ending famine through agricultural science (the 'Green Revolution')",
            "The 1970 Chemistry Nobel — for chemistry of wheat — but no Peace Prize was awarded for agricultural work, since the Nobel committee only honors political figures",
            "No Nobel Prize was ever given to Borlaug — agricultural advances were considered too applied",
            "The 1970 Medicine Nobel — for nutritional medicine",
        ],
        "context": "Borlaug also received the Congressional Gold Medal (2006), the Presidential Medal of Freedom (1977), and dozens of honorary doctorates. He continued working into his nineties, championing African agriculture and pushing back against organic-only orthodoxy. He died in 2009 at age 95. His life is one of the most lopsided lives-saved-to-fame ratios in history.",
    },
    # 105 — Tu Youyou artemisinin 2015
    {
        "tier": 4,
        "question": "Tu Youyou, a Chinese pharmacologist born in 1930, led Cultural Revolution-era Project 523 starting in 1969 to find a malaria treatment. Studying traditional Chinese herbal texts, she identified Artemisia annua (sweet wormwood) as a candidate, then isolated artemisinin in 1972 after testing it on herself. What recognition did she receive?",
        "answer": "She shared the 2015 Medicine Nobel — at age 84 — the first Chinese citizen to win a science Nobel — for an antimalarial that has saved millions of lives in Africa",
        "choices": [
            "She shared the 2015 Medicine Nobel — at age 84 — the first Chinese citizen to win a science Nobel — for an antimalarial that has saved millions of lives in Africa",
            "She received the Lasker Award in 2011 only — and was never given a Nobel — and the entire framework should be reconsidered",
            "She received no major recognition — Chinese science had no Nobel laureates as of 2015 — and the entire framework should be reconsidered",
            "She was awarded the 2015 Peace Prize — for advancing China-Western cooperation — and the entire framework should be reconsidered",
        ],
        "context": "Artemisinin and its derivatives (artesunate, artemether) became the backbone of modern malaria treatment when used in combination therapy (ACT). The WHO recommends artemisinin-combination therapy as first-line malaria treatment. Tu had no postgraduate degree and no PhD students — a rare profile for a Nobel-laureate scientist.",
    },
    # 106 — Autoimmune diseases: lupus, MS, type 1 diabetes
    {
        "tier": 4,
        "question": "In an autoimmune disease, the immune system mistakenly attacks the body's own tissues. Examples include systemic lupus erythematosus (joints, skin, kidneys), multiple sclerosis (nerve myelin), and type 1 diabetes (pancreatic beta cells). What's the broader mechanism?",
        "answer": "The immune system fails to distinguish self from non-self — instead of attacking only invaders, it targets specific body tissues — often with unclear triggers (genetic susceptibility, infections, environment)",
        "choices": [
            "The immune system fails to distinguish self from non-self — instead of attacking only invaders, it targets specific body tissues — often with unclear triggers (genetic susceptibility, infections, environment)",
            "The body produces too many immune cells overall — flooding tissues with white blood cells — and the entire framework should be reconsidered",
            "External parasites mimic body tissues — fooling the immune system into attacking those tissues — and the entire framework should be reconsidered",
            "Body tissues become genuinely diseased first — only then does the immune system attack — and the entire framework should be reconsidered",
        ],
        "context": "Autoimmune diseases affect about 5-8% of the US population — disproportionately women (about 78% of patients are female). Some have known triggers (rheumatic fever following strep, celiac disease following gluten exposure in susceptible people); most have idiopathic onset. Modern treatments include immunosuppressants and biologics targeting specific immune pathways.",
    },
    # 107 — Allergy IgE mechanism
    {
        "tier": 4,
        "question": "Allergies — from mild seasonal hay fever to life-threatening anaphylaxis — involve the immune system overreacting to harmless substances (pollen, peanuts, bee venom). The first exposure doesn't trigger anything dramatic; later exposures bring symptoms. What's the underlying mechanism?",
        "answer": "First exposure makes IgE antibodies that bind to mast cells — later exposures crosslink that IgE — triggering massive release of histamine and other inflammatory chemicals",
        "choices": [
            "First exposure makes IgE antibodies that bind to mast cells — later exposures crosslink that IgE — triggering massive release of histamine and other inflammatory chemicals",
            "First exposure produces IgG antibodies that destroy the allergen — later exposures have no effect",
            "First exposure suppresses the immune system completely — later exposures cause damage without immune involvement",
            "First exposure activates white blood cells — they remain active forever",
        ],
        "context": "Histamine is responsible for many allergy symptoms — itchy eyes, runny nose, hives, bronchoconstriction — which is why antihistamines provide relief. Anaphylaxis can drop blood pressure and close airways within minutes; epinephrine reverses this. The 'hygiene hypothesis' (Strachan, 1989) proposes that low childhood microbial exposure may increase later allergy rates.",
    },
    # 108 — Antibiotic resistance evolution
    {
        "tier": 4,
        "question": "Antibiotics that worked routinely in the 1950s and 60s are increasingly failing against modern strains. Methicillin-resistant Staphylococcus aureus (MRSA), multi-drug-resistant tuberculosis (MDR-TB), and carbapenem-resistant Enterobacteriaceae (CRE) have all emerged. What's the basic mechanism?",
        "answer": "Bacteria evolve under antibiotic pressure — random mutations confer resistance — the few surviving bacteria pass it on — creating populations the previous antibiotics no longer kill",
        "choices": [
            "Bacteria evolve under antibiotic pressure — random mutations confer resistance — the few surviving bacteria pass it on — creating populations the previous antibiotics no longer kill",
            "Bacteria deliberately reprogram themselves in response to antibiotics — choosing to be resistant — and the entire framework should be reconsidered",
            "Antibiotics actually create new diseases — there is no bacterial evolution involved — and the entire framework should be reconsidered",
            "Resistant bacteria are an old issue exactly as common in 1950 as now — there has been no real change — and the entire framework should be reconsidered",
        ],
        "context": "Antibiotic resistance evolves through new mutations and through horizontal gene transfer (plasmids carrying resistance genes can move between species). Overuse in human medicine and livestock agriculture is a major driver. The WHO has named antimicrobial resistance one of the top global health threats.",
    },
    # 109 — Watson + Crick + Franklin Photo 51
    {
        "tier": 4,
        "question": "Watson and Crick published the DNA double-helix structure in Nature on April 25, 1953. Rosalind Franklin's X-ray Photo 51 — taken by her PhD student Raymond Gosling — was shown to Watson by Maurice Wilkins without Franklin's knowledge, and was crucial to their structural insight. What happened to Franklin in the credit story?",
        "answer": "Franklin died of ovarian cancer in 1958 — the 1962 Nobel went to Watson, Crick, and Wilkins (Nobels aren't posthumous) — and Franklin's role has been increasingly recognized in later accounts",
        "choices": [
            "Franklin died of ovarian cancer in 1958 — the 1962 Nobel went to Watson, Crick, and Wilkins (Nobels aren't posthumous) — and Franklin's role has been increasingly recognized in later accounts",
            "Franklin shared the 1962 Nobel with Watson, Crick, and Wilkins — the four-way split is one of the most famous in Nobel history",
            "Franklin received a separate Nobel in 1962 — the Chemistry Prize rather than Medicine",
            "Franklin's role was minimal — she opposed the helix structure to her death",
        ],
        "context": "Brenda Maddox's biography *Rosalind Franklin: The Dark Lady of DNA* (2002) is the standard reference. Franklin's Photo 51 was the clearest X-ray diffraction image of B-form DNA available at the time. She and Wilkins worked at King's College London; their relationship was strained. The April 25, 1953 Nature issue contained three papers — Watson + Crick, Wilkins + Stokes + Wilson, and Franklin + Gosling.",
    },
    # 110 — Mitochondrial Eve
    {
        "tier": 4,
        "question": "Mitochondrial DNA — passed only through the maternal line in nearly every animal species — can be used to trace human female ancestry back through generations. Tracing back, all living humans share a single common maternal ancestor. When did this 'Mitochondrial Eve' live?",
        "answer": "Roughly 150,000-200,000 years ago in Africa — though she was not the only woman alive then, she's the one whose mitochondrial line has continuous female descendants all the way to today",
        "choices": [
            "Roughly 150,000-200,000 years ago in Africa — though she was not the only woman alive then, she's the one whose mitochondrial line has continuous female descendants all the way to today",
            "Roughly 6,000 years ago in the Middle East — corresponding to the biblical Eve — and the entire framework should be reconsidered",
            "Roughly 4 million years ago in East Africa — corresponding to early Australopithecus species — and the entire framework should be reconsidered",
            "Roughly 60,000 years ago in Europe — corresponding to anatomically modern humans first arriving — and the entire framework should be reconsidered",
        ],
        "context": "Mitochondrial Eve was identified by Cann, Stoneking, and Wilson in a 1987 Nature paper. The exact date depends on mitochondrial mutation-rate calibration. Mitochondrial Eve was not the only woman alive — many of her contemporaries simply have no continuous female descendants today. The corresponding 'Y-chromosomal Adam' lived about 200,000-300,000 years ago, also in Africa.",
    },
    # 111 — Stem cells: pluripotency Yamanaka 2006
    {
        "tier": 4,
        "question": "Shinya Yamanaka in 2006 showed something most biologists thought impossible: he reprogrammed fully differentiated adult cells (skin cells, for instance) back into a pluripotent stem-cell state — capable of becoming any cell type — using just four transcription factors (Oct4, Sox2, Klf4, c-Myc). What's the practical importance?",
        "answer": "Patient-specific stem cells without embryos — iPSCs (induced pluripotent stem cells)",
        "choices": [
            "Patient-specific stem cells without embryos — iPSCs (induced pluripotent stem cells)",
            "Confirming that adult cells can never be reprogrammed — Yamanaka's result was later retracted",
            "Disproving the existence of stem cells entirely — Yamanaka showed that all cells are equivalent",
            "Establishing that only Japanese cells can be reprogrammed — Yamanaka's technique works only on certain populations",
        ],
        "context": "Yamanaka shared the 2012 Medicine Nobel with John Gurdon (whose 1962 cloning experiments first hinted that differentiation could be reversed). iPSC technology has accelerated drug discovery, disease modeling, and personalized medicine. Clinical applications — replacing damaged retinal cells, neurons in Parkinson's, beta cells in diabetes — are in active trials.",
    },
    # 112 — Recombinant DNA: Boyer + Cohen 1973
    {
        "tier": 4,
        "question": "Stanley Cohen at Stanford and Herbert Boyer at UCSF in 1973 published the first successful recombinant DNA experiment — splicing a gene from one organism into another using bacterial plasmids and restriction enzymes. What was the immediate scientific and commercial impact?",
        "answer": "It launched modern biotechnology — Boyer co-founded Genentech in 1976 — and recombinant insulin (1982) became the first commercial biotech drug, replacing pig-pancreas extracts",
        "choices": [
            "It launched modern biotechnology — Boyer co-founded Genentech in 1976 — and recombinant insulin (1982) became the first commercial biotech drug, replacing pig-pancreas extracts",
            "It was immediately banned by all governments — the technique was considered too dangerous — and recombinant DNA is illegal in the US, EU, and Japan as of 2026",
            "It produced no commercial products — the technique remained a laboratory curiosity — and the modern pharmaceutical industry has no products derived from recombinant DNA",
            "It was retracted within months — Boyer and Cohen had made experimental errors — and modern biotechnology developed independently of their original published research",
        ],
        "context": "The 1975 Asilomar Conference convened scientists to discuss safety protocols for recombinant DNA work — a notable case of scientific self-regulation. Genentech (1976) was the first major biotech company. Today most pharmaceutical proteins (growth hormone, clotting factors, monoclonal antibodies) are made by recombinant DNA.",
    },
    # 113 — Mutation: substitution, frameshift, repeat expansion
    {
        "tier": 4,
        "question": "DNA mutations come in several types. A 'point mutation' substitutes one base for another; a 'frameshift mutation' inserts or deletes bases that aren't multiples of 3 (shifting the reading frame); a 'repeat expansion' adds extra copies of a short repeat (CAG... in Huntington's). Why do frameshift mutations typically have larger effects?",
        "answer": "A frameshift changes how every triplet downstream is read — turning the rest of the protein into nonsense — while a point mutation usually changes one amino acid at most",
        "choices": [
            "A frameshift changes how every triplet downstream is read — turning the rest of the protein into nonsense — while a point mutation usually changes one amino acid at most",
            "A frameshift only happens in non-coding DNA — and therefore never affects any protein — and the entire framework should be reconsidered",
            "A frameshift is repaired by the cell within seconds — and has no biological effect — and the entire framework should be reconsidered",
            "A frameshift increases the protein's overall stability — making it more resistant to degradation — and the entire framework should be reconsidered",
        ],
        "context": "Frameshift mutations often produce truncated proteins because random codons in the new reading frame frequently include stop codons. Diseases include Tay-Sachs and certain forms of cystic fibrosis. Point mutations can be silent, missense (different amino acid), or nonsense (premature stop). Sickle cell disease is a single point mutation (β-globin: GAG → GTG, glutamic acid → valine).",
    },
    # 114 — Telomeres and aging
    {
        "tier": 4,
        "question": "Telomeres are repeating DNA sequences at the ends of each chromosome (TTAGGG repeated in humans) that protect against gradual end-erosion during cell division. Each cell division shortens telomeres slightly; when they get too short, the cell enters senescence or dies. Why is this relevant to cancer and aging?",
        "answer": "Cancer cells often reactivate telomerase (Greider, Blackburn, Szostak Nobel 2009) — maintaining telomeres indefinitely — while normal shortening limits cell division and may contribute to aging",
        "choices": [
            "Cancer cells often reactivate telomerase (Greider, Blackburn, Szostak Nobel 2009) — maintaining telomeres indefinitely — while normal shortening limits cell division and may contribute to aging",
            "Cancer cells deliberately shorten their telomeres — making them die faster — and telomere length is uniformly longer in young people of every species ever studied",
            "Telomeres are a debunked theory of aging — no evidence supports their relevance — and the 2009 Nobel was for an unrelated chromosome-structure discovery",
            "Telomeres exist only in plants — animal chromosomes have different end-protection — and the human aging story has nothing to do with telomere length",
        ],
        "context": "Telomerase reactivation is found in about 90% of human cancers — making it a potential therapeutic target. The 'Hayflick limit' (1961) — that normal human cells divide only about 50-60 times before senescence — is largely a consequence of telomere shortening. Telomere length is associated with lifespan in some studies but the causal arrow remains debated.",
    },
    # 115 — Apoptosis: programmed cell death
    {
        "tier": 4,
        "question": "Apoptosis (from Greek) is programmed cell death — a controlled, clean self-destruction of cells when they are damaged, infected, or no longer needed. About 60 billion human cells die by apoptosis every day. Why is this so important?",
        "answer": "Apoptosis eliminates damaged or potentially cancerous cells before they become problems — shapes developing tissues (sculpting fingers from webbed embryonic hands) — and balances cell production in adult tissues",
        "choices": [
            "Apoptosis eliminates damaged or potentially cancerous cells before they become problems — shapes developing tissues (sculpting fingers from webbed embryonic hands) — and balances cell production in adult tissues",
            "Apoptosis happens only in old age — younger cells never die by this pathway — and this view is preserved in standard textbooks today",
            "Apoptosis is the only way human cells ever die — there is no other death pathway — and this view is preserved in standard textbooks today",
            "Apoptosis was disproven in the 2010s — cell death turns out to be entirely random — and modern science has retired this framing entirely",
        ],
        "context": "Brenner, Horvitz, and Sulston shared the 2002 Medicine Nobel for working out apoptosis in the nematode worm C. elegans — every cell death is reproducibly choreographed. Cancer cells often evade apoptosis through mutations in p53 ('the guardian of the genome') and Bcl-2 family members. Disordered apoptosis contributes to neurodegenerative and autoimmune disorders.",
    },
    # 116 — Endosymbiotic theory: mitochondria
    {
        "tier": 4,
        "question": "Lynn Margulis in 1967 proposed — at first to widespread skepticism — that mitochondria (the energy organelles in eukaryotic cells) and chloroplasts (photosynthetic organelles in plant cells) were once free-living bacteria that were engulfed by ancestral cells and became permanent residents. What evidence eventually established her view?",
        "answer": "Mitochondria and chloroplasts have their own DNA, ribosomes, and double membranes — consistent with bacterial origin — and their DNA sequences place them firmly within bacterial phylogeny",
        "choices": [
            "Mitochondria and chloroplasts have their own DNA, ribosomes, and double membranes — consistent with bacterial origin — and their DNA sequences place them firmly within bacterial phylogeny",
            "Mitochondria and chloroplasts have been observed being engulfed today — by amoebae in the wild",
            "Mitochondria and chloroplasts have been shown to be experimental artifacts — they do not actually exist in living cells",
            "Mitochondria and chloroplasts contain only nuclear DNA — there is no separate organelle DNA",
        ],
        "context": "Margulis (formerly Lynn Sagan, married to Carl Sagan) faced years of skepticism before her ideas became mainstream. The endosymbiotic theory is now textbook biology. Mitochondrial DNA is circular like bacterial DNA. Over evolutionary time many genes moved from mitochondrion to nucleus. Margulis was also a vocal proponent of the Gaia hypothesis (with James Lovelock).",
    },
    # 117 — Outsider scientists who won Nobels
    {
        "tier": 4,
        "question": "Several Nobel-winning scientists have done their most important work outside the standard credentialing system. Norman Borlaug (1970 Peace) worked at a non-elite Mexican research station for decades; Tu Youyou (2015 Medicine) had no PhD; Katalin Karikó (2023 Medicine) was demoted at Penn before her work led to COVID vaccines. What's the broader recognition?",
        "answer": "Major scientific breakthroughs sometimes come from researchers outside elite institutions — credentialing isn't a perfect filter",
        "choices": [
            "Major scientific breakthroughs sometimes come from researchers outside elite institutions — credentialing isn't a perfect filter",
            "Major breakthroughs come only from elite institutions — Borlaug, Tu, and Karikó were secretly affiliated with top universities",
            "Major breakthroughs all come from political activists — Borlaug, Tu, and Karikó were primarily political figures",
            "Major breakthroughs always come from amateurs — credentialed scientists never make important discoveries",
        ],
        "context": "Katalin Karikó spent years at Penn trying to make mRNA work as a therapeutic, faced repeated grant rejections, and was demoted in 1995 — her partnership with Drew Weissman eventually produced the chemistry that made mRNA vaccines possible. They shared the 2023 Medicine Nobel. The broader lesson is humility about credentialing — the system catches many good scientists but also misses some critical work.",
    },
    # 118 — Genome size doesn't predict complexity
    {
        "tier": 4,
        "question": "Humans have a genome of about 3 billion base pairs and 20,000-25,000 genes. Some lungfish have genomes 40 times larger; some amoebae have genomes 200 times larger. The 'C-value paradox' is that genome size doesn't correlate with organism complexity. Why is this surprising?",
        "answer": "Naïve expectation says complex organisms need more genetic information — the paradox shows much of the size variation across species is in non-coding 'junk' DNA and repetitive sequences, not in functional genes",
        "choices": [
            "Naïve expectation says complex organisms need more genetic information — the paradox shows much of the size variation across species is in non-coding 'junk' DNA and repetitive sequences, not in functional genes",
            "It's not surprising at all — complexity correlates perfectly with genome size — and this view is preserved in standard textbooks today",
            "Lungfish and amoebae are extraordinarily intelligent — much smarter than humans — and this view is preserved in standard textbooks today",
            "All organisms actually have identical genome sizes — apparent differences are artifacts — and the entire framework should be reconsidered",
        ],
        "context": "The term 'C-value paradox' was coined by C.A. Thomas in 1971. Much of the variation comes from transposable elements, gene duplications, and other non-coding sequences. The ENCODE project (2012) found about 80% of the human genome has at least some biochemical activity — challenging the 'junk DNA' framing — though how much is functionally important remains contested.",
    },
    # 119 — Stem cells: adult vs embryonic
    {
        "tier": 4,
        "question": "Stem cells come in several categories. 'Embryonic stem cells' (from early embryos) are pluripotent — they can become any cell type. 'Adult stem cells' (in bone marrow, gut lining, skin) are multipotent — they can become a limited set within their tissue. Why has stem cell research been politically contested?",
        "answer": "Embryonic stem-cell research requires destroying early embryos — the ethics are contested — and 'iPSC' technology (Yamanaka 2006) now offers an alternative that avoids the ethical problem",
        "choices": [
            "Embryonic stem-cell research requires destroying early embryos — the ethics are contested — and 'iPSC' technology (Yamanaka 2006) now offers an alternative that avoids the ethical problem",
            "Embryonic stem-cell research is universally accepted — there is no political controversy — and the entire framework should be reconsidered",
            "Embryonic stem cells have been disproven as a research tool — only adult stem cells actually work — and the entire framework should be reconsidered",
            "Embryonic stem cells are illegal worldwide — no country permits any research with them — and the entire framework should be reconsidered",
        ],
        "context": "George W. Bush in 2001 restricted federal funding to existing embryonic-stem-cell lines. Obama lifted that restriction in 2009. Yamanaka's iPSC discovery (2006, Nobel 2012) provided an ethical alternative — reprogramming adult cells back to pluripotency without embryos. The ethics of embryo research remain a substantive philosophical question.",
    },
    # 120 — Vaccines as immune system training
    {
        "tier": 4,
        "question": "Vaccines work by exposing the immune system to a harmless version of a pathogen (killed virus, attenuated live virus, viral protein, mRNA encoding a viral protein) — so the immune system 'practices' and develops memory before encountering the real pathogen. What's the underlying immune cell type that provides this memory?",
        "answer": "Memory B and T cells — long-lived immune cells generated during the initial response — that remain in the body and respond rapidly if the same pathogen appears later in life",
        "choices": [
            "Memory B and T cells — long-lived immune cells generated during the initial response — that remain in the body and respond rapidly if the same pathogen appears later in life",
            "Red blood cells store immune memory — the hemoglobin actually carries antibody information — and the entire framework should be reconsidered",
            "Stomach acid retains immune memory — the gut serves as the long-term memory store — and the entire framework should be reconsidered",
            "Hair follicles record immune memory — the keratin captures pathogen information — and the entire framework should be reconsidered",
        ],
        "context": "Edward Jenner's first vaccine (1796, cowpox-protecting-from-smallpox) is the foundational case. Modern vaccine platforms include inactivated viruses (polio), attenuated live (MMR, varicella), subunit/protein (HPV, hepatitis B), and mRNA (COVID-19). The memory mechanism explains why most childhood vaccinations give long-lasting protection while some (flu, tetanus) need boosters.",
    },
    # 121 — Cancer biology: hallmarks of cancer
    {
        "tier": 4,
        "question": "Douglas Hanahan and Robert Weinberg in 2000 (updated 2011) identified a set of 'hallmarks of cancer' — characteristic capabilities that nearly all human cancers acquire on the way from normal cell to malignant tumor. What's the broader picture?",
        "answer": "Cancer is the accumulation of mutations that progressively unlock specific capabilities — sustained growth, evading death signals, attracting blood vessels, invading tissues, metastasizing — rather than a single defining defect",
        "choices": [
            "Cancer is the accumulation of mutations that progressively unlock specific capabilities — sustained growth, evading death signals, attracting blood vessels, invading tissues, metastasizing — rather than a single defining defect",
            "Cancer is a single mutation in a single gene — Hanahan and Weinberg identified the 'cancer gene' in 2000 — and the entire framework should be reconsidered",
            "Cancer is not actually mutational — it's caused entirely by environmental toxins — and this view is preserved in standard textbooks today",
            "Cancer has only one cause: viral infection — Hanahan and Weinberg identified specific tumor viruses — and the entire framework should be reconsidered",
        ],
        "context": "Original six hallmarks (2000): sustaining proliferative signaling, evading growth suppressors, resisting cell death, enabling replicative immortality, inducing angiogenesis, activating invasion and metastasis. The 2011 update added energy reprogramming, immune evasion, genome instability, and tumor-promoting inflammation. The framework structures the way many cancer therapies are designed.",
    },
    # 122 — Immune checkpoint inhibitors: Allison + Honjo 2018
    {
        "tier": 4,
        "question": "James Allison (MD Anderson) and Tasuku Honjo (Kyoto) shared the 2018 Medicine Nobel for discovering the immune system's 'checkpoint' brakes (CTLA-4 and PD-1) — and that blocking those brakes lets the immune system attack tumors that had previously hidden from it. What's the practical impact?",
        "answer": "Checkpoint-inhibitor drugs (ipilimumab, pembrolizumab, nivolumab) transformed treatment of melanoma, lung cancer, and others — producing durable remissions for some previously incurable patients",
        "choices": [
            "Checkpoint-inhibitor drugs (ipilimumab, pembrolizumab, nivolumab) transformed treatment of melanoma, lung cancer, and others — producing durable remissions for some previously incurable patients",
            "Allison and Honjo's discovery had no clinical impact — checkpoint inhibitors are too dangerous to use — and standard chemotherapy remains the only treatment available for any cancer",
            "Allison and Honjo's discovery turned out irrelevant — the proteins they identified don't actually exist — and the Nobel committee made an embarrassing mistake in 2018",
            "Allison and Honjo's discovery applies only to skin cancer — and even there it works in only 1% of patients — making the treatment essentially useless in oncology",
        ],
        "context": "Ipilimumab (Yervoy, 2011) was the first checkpoint inhibitor. Pembrolizumab (Keytruda) and nivolumab (Opdivo) followed. President Jimmy Carter's brain-metastatic melanoma was treated with Keytruda in 2015. Checkpoint inhibitors have major side effects (autoimmune reactions) but for responders the benefit can be dramatic — durable remissions in cancers that were once a near-certain death sentence.",
    },
    # 123 — mRNA vaccines: Karikó + Weissman 2023
    {
        "tier": 4,
        "question": "Katalin Karikó and Drew Weissman shared the 2023 Medicine Nobel for their decades of work — sometimes against institutional headwinds — making mRNA usable as a therapeutic platform. Their crucial 2005 paper showed that swapping uridine for pseudouridine in mRNA stops the immune system from destroying it on sight. What did this enable?",
        "answer": "mRNA vaccines — including the Pfizer-BioNTech and Moderna COVID-19 vaccines deployed at unprecedented speed in 2020 — and a growing platform for cancer immunotherapies and other infectious diseases",
        "choices": [
            "mRNA vaccines — including the Pfizer-BioNTech and Moderna COVID-19 vaccines deployed at unprecedented speed in 2020 — and a growing platform for cancer immunotherapies and other infectious diseases",
            "DNA vaccines only — Karikó and Weissman never worked with mRNA",
            "Traditional protein vaccines — Karikó and Weissman invented standard injection chemistry",
            "Anti-aging therapies — their work prevents cellular aging — but has no vaccine applications, and the COVID vaccines came from independent discoveries by other researchers",
        ],
        "context": "Karikó was demoted at Penn in 1995 after years of mRNA work. She partnered with Weissman in the late 1990s. Their 2005 paper in Immunity was a turning point. BioNTech (founded by Şahin and Türeci) and Moderna both used the Karikó-Weissman chemistry as the basis for their COVID vaccines.",
    },
    # 124 — Sickle cell genetics + malaria selection
    {
        "tier": 4,
        "question": "Sickle cell disease is caused by a single point mutation in the β-globin gene (GAG → GTG; glutamic acid replaced by valine at position 6). One mutant copy plus one normal copy = 'sickle cell trait' (mostly asymptomatic). Two mutant copies = full sickle cell disease, often serious. The mutation is common in West African populations. Why is the harmful gene so common?",
        "answer": "Heterozygotes (one copy) are partly protected against malaria — so in malarial regions the gene has been selected to high frequency, despite the cost of disease in homozygotes",
        "choices": [
            "Heterozygotes (one copy) are partly protected against malaria — so in malarial regions the gene has been selected to high frequency, despite the cost of disease in homozygotes",
            "Heterozygotes have no advantage — the gene's frequency is purely random — and the entire framework should be reconsidered",
            "Heterozygotes live longer than non-carriers — the gene actually improves lifespan in carriers — and the entire framework should be reconsidered",
            "Heterozygotes never get malaria — but neither do homozygotes — and modern science has retired this framing entirely",
        ],
        "context": "The sickle-cell-and-malaria connection (Anthony Allison, 1954) is a textbook example of balancing selection. Similar stories: thalassemias and G6PD deficiency also provide some malaria protection at the cost of disease in homozygotes. Casgevy (2023) — the first CRISPR therapy approved by the FDA — edits a patient's own stem cells to reactivate fetal hemoglobin production, effectively curing sickle cell.",
    },
    # 125 — Cystic fibrosis CFTR
    {
        "tier": 4,
        "question": "Cystic fibrosis is caused by mutations in the CFTR gene, which codes for a chloride-ion channel in cell membranes. About 1 in 25 Northern Europeans carries one CF mutation; about 1 in 2,500-3,500 has the disease. Why has the CF gene been historically common?",
        "answer": "Heterozygotes may have had partial resistance to cholera or typhoid in past epidemics — the leading hypothesis — so in pre-modern Europe the gene was selected up despite the cost in homozygotes",
        "choices": [
            "Heterozygotes may have had partial resistance to cholera or typhoid in past epidemics — the leading hypothesis — so in pre-modern Europe the gene was selected up despite the cost in homozygotes",
            "Heterozygotes are at no advantage — the gene's frequency is purely random — and modern science has retired this framing entirely",
            "Heterozygotes live considerably longer than non-carriers — the CFTR gene improves longevity dramatically — and the entire framework should be reconsidered",
            "CF is actually environmental — the gene is not inherited — and this view is preserved in standard textbooks today",
        ],
        "context": "CF was once nearly always fatal in childhood — patients now routinely live into their 40s and 50s with modern care. The 2019 approval of Trikafta — a triple-combination drug that fixes the most common CFTR mutation (ΔF508) — has been called a near-miracle for the ~90% of patients eligible. Gene therapy and CRISPR approaches are in trials.",
    },
    # 126 — Cellular senescence + zombie cells
    {
        "tier": 4,
        "question": "Cells can stop dividing without dying — entering a state called 'senescence.' Senescent cells used to be considered a passive endpoint, but recent work shows they actively secrete inflammatory signals (the SASP) that may contribute to age-related decline. Why are they sometimes called 'zombie cells'?",
        "answer": "They refuse to die — but they also stop functioning normally and harm surrounding tissue with their secreted inflammatory signals — clearing them out is being explored as an anti-aging therapy",
        "choices": [
            "They refuse to die — but they also stop functioning normally and harm surrounding tissue with their secreted inflammatory signals — clearing them out is being explored as an anti-aging therapy",
            "They actively eat surrounding cells — turning healthy tissue into zombies — and modern science has retired this framing entirely",
            "They emerge only at midnight — following lunar cycles — and this view is preserved in standard textbooks today",
            "They are entirely fictional — the concept of zombie cells is a metaphor without basis — and the entire framework should be reconsidered",
        ],
        "context": "Senolytics — drugs that selectively kill senescent cells — are an active area of aging research. The Mayo Clinic's work (van Deursen, Kirkland) showed that clearing senescent cells from mouse tissues extends lifespan and reduces age-related disease. Human trials are early. Aubrey de Grey has been a high-profile (and sometimes controversial) advocate for senescent-cell clearance.",
    },
    # 127 — Vaccines as one part of public health
    {
        "tier": 4,
        "question": "Public health improvements through the 20th century reduced death rates dramatically. Multiple factors contributed: clean water, sanitation, nutrition, vaccination, antibiotics, surgery, intensive care. What's the broader recognition about attributing health improvements to any single factor?",
        "answer": "Multiple factors contributed — water and sanitation enormous, nutrition and antibiotics critical, vaccines key for specific diseases — single-factor explanations oversimplify the history",
        "choices": [
            "Multiple factors contributed — water and sanitation enormous, nutrition and antibiotics critical, vaccines key for specific diseases — single-factor explanations oversimplify the history",
            "Only vaccines contributed — everything else was insignificant — and modern health improvements are entirely due to mass-vaccination programs throughout the 20th century",
            "Only antibiotics contributed — vaccination did nothing — and the smallpox eradication that the WHO declared in 1980 was actually a coincidence with no vaccine cause",
            "Nothing contributed — health improvements are an illusion — and average lifespan in 2026 is no longer than in 1900 according to modern revised mortality statistics",
        ],
        "context": "Thomas McKeown's work in the 1970s emphasized nutrition and living-standards improvements — sometimes overstated as 'vaccines did nothing.' Modern historians give vaccines clear credit for specific disease declines (smallpox eradication 1980, near-eradication of polio, measles deaths down >99%) while also crediting sanitation and antibiotics. The honest history credits multiple factors.",
    },
    # 128 — Replication crisis in biology
    {
        "tier": 4,
        "question": "The 'replication crisis' — the recognition that many published research findings cannot be reproduced — has hit biology hard. The 2012 Amgen paper (Begley and Ellis, Nature) reported that researchers could replicate only 6 out of 53 'landmark' cancer-biology findings. What's the recognition for a kid reading 'new study shows X' headlines?",
        "answer": "A single study — even peer-reviewed in a top journal — is weak evidence on its own — replication, pre-registration, and effect size matter more than the original headline-grabbing finding",
        "choices": [
            "A single study — even peer-reviewed in a top journal — is weak evidence on its own — replication, pre-registration, and effect size matter more than the original headline-grabbing finding",
            "A single study in a top journal is definitive — peer review eliminates errors — and the entire framework should be reconsidered",
            "Replication is impossible by design — every experiment is unique — and this view is preserved in standard textbooks today",
            "Modern statistics has solved the problem entirely — replication failure is now eliminated — and the entire framework should be reconsidered",
        ],
        "context": "The replication crisis is severe in psychology (the Open Science Collaboration's 2015 paper found only 36% replication), but also affects biomedical research, pharmacology, and beyond. Pre-registration, larger sample sizes, and the Many Labs replication projects have raised the bar somewhat. Notable retractions in biomedicine include the Surgisphere HCQ papers (2020) and various Stapel cases.",
    },
    # 129 — Microbiome
    {
        "tier": 4,
        "question": "The human body contains about as many bacterial cells as human cells (recent estimates put the ratio at roughly 1:1, not the older 10:1). Most of these bacteria live in the gut. The collective genome of these microbes is the 'microbiome' and contains far more genes than the human genome itself. What's the broader recognition?",
        "answer": "We are an ecosystem — microbes influence digestion, immune development, mood, disease susceptibility — and 'human biology' increasingly includes our microbes",
        "choices": [
            "We are an ecosystem — microbes influence digestion, immune development, mood, disease susceptibility — and 'human biology' increasingly includes our microbes",
            "Bacteria in the gut are harmful invaders — they should be eradicated with antibiotics — and a sterile gut is the healthiest possible state for an adult human at any time",
            "Bacteria in the gut are irrelevant to human biology — they have no influence at all — and a sterile gut behaves identically to a fully-colonized gut by every metric studied",
            "Bacteria in the gut are entirely beneficial — there are no harmful gut bacteria — and the only goal of microbiome research is to maximize total gut bacterial counts",
        ],
        "context": "The microbiome boom in research has shifted thinking about many conditions — inflammatory bowel disease, type 2 diabetes, depression, and autoimmune disorders all show microbial correlations. Fecal microbiota transplants are now standard treatment for recurrent C. difficile infections. Modern science increasingly sees humans as host-microbe ecosystems.",
    },
    # 130 — Lac operon: Monod + Jacob gene regulation
    {
        "tier": 4,
        "question": "Jacques Monod and François Jacob at the Pasteur Institute in 1961 published their model of gene regulation in E. coli — the 'lac operon.' Bacteria grown without lactose don't waste energy making lactose-digesting enzymes; when lactose appears, the genes turn on. What was the bigger insight?",
        "answer": "Genes can be regulated — turned on/off in response to environmental conditions — through specific DNA-binding proteins (repressors, activators) controlling transcription",
        "choices": [
            "Genes can be regulated — turned on/off in response to environmental conditions — through specific DNA-binding proteins (repressors, activators) controlling transcription",
            "Genes are always on at the same level — Monod and Jacob's data showed no regulation — and the modern picture of gene regulation is unrelated to their published work",
            "Genes work only in bacteria — Monod and Jacob's work has no implications for any other organism — and animals lack any equivalent gene-regulation system entirely",
            "Genes are unrelated to enzymes — Monod and Jacob disproved the central dogma — and modern molecular biology operates without the gene-enzyme connection at all",
        ],
        "context": "Monod, Jacob, and André Lwoff shared the 1965 Medicine Nobel. The lac operon — with its repressor protein that binds the operator and blocks transcription unless lactose is present — became the canonical example of gene regulation in textbooks.",
    },
    # 131 — RNA world abiogenesis hypothesis
    {
        "tier": 4,
        "question": "One leading hypothesis for the origin of life — the 'RNA world' — proposes that the first self-replicating molecules were RNA rather than DNA + proteins. RNA can both store information (like DNA) and catalyze reactions (like proteins). What's the evidence for this hypothesis?",
        "answer": "Modern ribosomes are mostly RNA — RNA can catalyze reactions ('ribozymes,' Cech and Altman Nobel 1989) — and many essential cofactors (ATP, NAD) have RNA-like nucleotide structures",
        "choices": [
            "Modern ribosomes are mostly RNA — RNA can catalyze reactions ('ribozymes,' Cech and Altman Nobel 1989) — and many essential cofactors (ATP, NAD) have RNA-like nucleotide structures",
            "DNA was clearly first — RNA is a recent invention of complex cells — and the RNA-world hypothesis has been disproven by direct evidence from molecular biology",
            "Both DNA and RNA evolved simultaneously — there is no first-molecule question — and the RNA-world hypothesis is a misunderstanding of how the origin of life worked",
            "Proteins were first — life began with random amino-acid polymers — and modern RNA evolved much later, with no role at all in the original abiogenesis events",
        ],
        "context": "Walter Gilbert coined 'RNA world' in 1986. Cech and Altman shared the 1989 Chemistry Nobel for showing that RNA can catalyze reactions (overturning the 'only proteins are catalysts' assumption). RNA's dual role makes it a candidate for the first replicator. Open questions include how RNA itself originated and whether metabolism-first hypotheses are better fits.",
    },
    # 132 — Junk DNA: ENCODE 2012
    {
        "tier": 4,
        "question": "When the Human Genome Project finished in 2003, only about 1-2% of the genome was protein-coding. The rest was widely called 'junk DNA' — non-coding, presumed non-functional. The ENCODE project in 2012 announced that perhaps 80% of the genome has 'biochemical activity.' What's the contested reading?",
        "answer": "ENCODE found activity, but how much of it is functionally meaningful vs noise is contested — 'junk DNA' overstated emptiness, but '80% functional' may overstate function too",
        "choices": [
            "ENCODE found activity, but how much of it is functionally meaningful vs noise is contested — 'junk DNA' overstated emptiness, but '80% functional' may overstate function too",
            "ENCODE definitively proved 80% of the genome is functional — there is no remaining debate — and any reference to 'junk DNA' in modern textbooks is an embarrassing error",
            "ENCODE was retracted in 2015 — the entire project was a fraud — and the human genome is essentially all junk DNA except the protein-coding genes themselves",
            "ENCODE found the genome to be 100% protein-coding — junk DNA never existed — and the entire human genome codes for distinct proteins with no non-coding regions",
        ],
        "context": "Critics of ENCODE's 80% figure (Dan Graur, Larry Moran) have argued that 'biochemical activity' is not the same as 'biological function' — the genome can be transcribed at low levels without that necessarily mattering. ENCODE defenders argue that broad regulatory roles for once-junk regions are increasingly clear. The honest reading lies somewhere between the two extremes.",
    },
    # 133 — Antibodies + monoclonal antibodies
    {
        "tier": 4,
        "question": "Antibodies are proteins made by B cells that bind specific molecular targets (antigens). Monoclonal antibodies (mAbs) — are now a major class of drugs. Why are they so useful?",
        "answer": "Their specificity lets them target one molecule precisely — used for cancer (rituximab, trastuzumab), autoimmune disease (adalimumab), and infectious disease (COVID antibody cocktails) — with fewer off-target effects than small-molecule drugs",
        "choices": [
            "Their specificity lets them target one molecule precisely — used for cancer (rituximab, trastuzumab), autoimmune disease (adalimumab), and infectious disease (COVID antibody cocktails) — with fewer off-target effects than small-molecule drugs",
            "Their lack of specificity makes them useful for broad-spectrum treatment — they bind everything in the body — and the goal is to flood the system with as many antibodies as possible",
            "Their unique property is being made by snakes — mAbs are derived from snake venom — and any other source has been found unsuitable for therapeutic use in humans",
            "Their main use is in research only — no monoclonal antibody has ever been approved as a drug",
        ],
        "context": "Köhler and Milstein at Cambridge in 1975 figured out how to make monoclonal antibodies by fusing antibody-producing B cells with myeloma cells — they shared the 1984 Medicine Nobel. The first mAb drug (muromonab, 1986) was an anti-rejection drug. Today there are dozens of approved mAbs — top sellers include Humira and Keytruda.",
    },
    # 134 — Lab leak hypothesis: Proximal Origin Slack
    {
        "tier": 4,
        "question": "The 'Proximal Origin' paper (Andersen et al., Nature Medicine, March 2020) declared SARS-CoV-2's origin almost certainly natural and dismissed lab leak. FOIA'd Slack messages later revealed authors privately suspected lab leak even as they publicly dismissed it. By 2023, FBI and DOE publicly favored lab leak. What does this case illustrate?",
        "answer": "Public scientific declarations can diverge from what scientists privately think — shaped by political or institutional pressure — and 'misinformation' labels can themselves mislead",
        "choices": [
            "Public scientific declarations can diverge from what scientists privately think — shaped by political or institutional pressure — and 'misinformation' labels can themselves mislead",
            "Lab leak has been definitively disproven — the Proximal Origin paper was entirely correct — and FBI / DOE assessments have been retracted as politically motivated by 2024",
            "FBI and DOE assessments don't count as evidence — only Nature papers settle scientific questions — and the Proximal Origin paper remains the final word on COVID origins",
            "Slack messages are inadmissible as evidence — and the FOIA release of internal communications was a privacy violation rather than legitimate scientific scrutiny",
        ],
        "context": "The Proximal Origin authors included Kristian Andersen, Eddie Holmes, and Robert Garry. FOIA-released Slack messages and emails (released 2023) showed the authors discussing lab leak as plausible while drafting public statements calling it implausible. The paper was widely cited to label lab-leak claims 'misinformation' throughout 2020-2022.",
    },
    # 135 — Wakefield 1998 retracted full context
    {
        "tier": 4,
        "question": "Andrew Wakefield's 1998 Lancet paper claiming a link between MMR vaccine and autism is now widely cited as a fraud case. The paper was retracted in 2010; Wakefield lost his medical license. The full story has some nuances. What's the honest reading worth a kid knowing?",
        "answer": "Wakefield's 1998 paper was retracted for genuine ethical and methodological problems — and the MMR-autism claim does not hold up in larger studies — while broader vaccine-safety conversations are legitimate independent of his case",
        "choices": [
            "Wakefield's 1998 paper was retracted for genuine ethical and methodological problems — and the MMR-autism claim does not hold up in larger studies — while broader vaccine-safety conversations are legitimate independent of his case",
            "Wakefield was completely fraudulent in every claim — there was no underlying medical observation — and modern science has retired this framing entirely",
            "Wakefield was right and was suppressed — the MMR-autism link is now scientifically established — and modern science has retired this framing entirely",
            "Wakefield never existed — the 1998 paper was a Lancet fabrication — and this view is preserved in standard textbooks today",
        ],
        "context": "Brian Deer's investigative journalism (BMJ, 2011) detailed the financial conflicts of interest and data manipulation in Wakefield's work. The 12-child case series was inadequate for any population-level inference. Subsequent large epidemiological studies found no MMR-autism link at scale. The official handling of dissenters has sometimes been more about suppression than engagement.",
    },
    # 136 — Murthy v. Missouri 2024
    {
        "tier": 4,
        "question": "Murthy v. Missouri (Supreme Court 2024) and the Twitter Files releases (2022-2023) documented federal agency coordination with social media platforms to flag scientific speech for suppression — including content from credentialed scientists like Bhattacharya and Kulldorff. What's the recognition?",
        "answer": "Government coordination with private platforms to suppress speech can function as censorship even without formal law — and scientific dissent is the kind of speech the First Amendment exists to protect",
        "choices": [
            "Government coordination with private platforms to suppress speech can function as censorship even without formal law — and scientific dissent is the kind of speech the First Amendment exists to protect",
            "Government coordination with platforms is constitutionally fine in every case — there is no free-speech concern — and the Twitter Files have been retracted as fabricated by the platform",
            "Murthy v. Missouri was decided in favor of the government — censorship of dissent is now legal",
            "Murthy v. Missouri never happened — there was no such case",
        ],
        "context": "The Twitter Files (Matt Taibbi, Bari Weiss, Michael Shellenberger, others) showed extensive FBI and CDC contact with Twitter content moderators flagging specific accounts. Murthy v. Missouri reached the Supreme Court, which in 2024 ruled (6-3) that the plaintiffs lacked standing to sue — leaving the substantive question undecided. The case raised serious First Amendment questions that remain contested.",
    },
    # 137 — Cochrane mask review 2023
    {
        "tier": 4,
        "question": "The Cochrane Collaboration published an updated systematic review on physical interventions (including masks) for respiratory virus transmission in January 2023. The review's authors (Tom Jefferson and colleagues) found 'high uncertainty' about whether community masking reduces transmission. What was the response?",
        "answer": "The review was widely attacked — Cochrane's editor-in-chief issued a distancing statement on the framing — and the methodological debate over masking has continued without clear resolution",
        "choices": [
            "The review was widely attacked — Cochrane's editor-in-chief issued a distancing statement on the framing — and the methodological debate over masking has continued without clear resolution",
            "The review was universally accepted — masks were quickly abandoned by every public-health agency — and no controversy followed the publication of the 2023 Cochrane analysis",
            "The review was never published — Cochrane retracted it before release — and no systematic review of masking has ever appeared in any major scientific publication",
            "The review concluded masks definitely work — and there was no controversy at all — with every public-health agency endorsing the findings without exception or qualification",
        ],
        "context": "Tom Jefferson and the Cochrane authors emphasized that the review found a lack of clear evidence rather than evidence of no effect. Critics argued the systematic review methodology — restricted to randomized trials — could miss effects in observational studies. The dispute illustrates how 'follow the science' can mean different things depending on which evidence hierarchy one applies.",
    },
    # 138 — Beta blockers + statins + everyday drug examples
    {
        "tier": 4,
        "question": "Some of the most widely used drugs in modern medicine come from understanding a specific molecular mechanism. Beta blockers (atenolol, metoprolol) block adrenaline receptors on heart cells. Statins (atorvastatin, simvastatin) inhibit HMG-CoA reductase in the liver. What's the general lesson about modern drug design?",
        "answer": "Targeted molecular intervention — blocking a specific enzyme or receptor — has produced many successful modern drugs, though older ones (aspirin, lithium) were found empirically",
        "choices": [
            "Targeted molecular intervention — blocking a specific enzyme or receptor — has produced many successful modern drugs, though older ones (aspirin, lithium) were found empirically",
            "Modern drugs all work by completely unknown mechanisms — beta blockers and statins are no exception — and pharmacology has no mechanistic understanding of any drug",
            "Modern drugs all work the same way — blocking one universal mechanism — and the specific targets named (adrenaline receptors, HMG-CoA reductase) are marketing inventions",
            "Modern drugs all work only by the placebo effect — beta blockers and statins do nothing — and double-blind trials show no real-world benefit for any modern medication",
        ],
        "context": "James Black received the 1988 Medicine Nobel for beta blockers (propranolol, 1962) and H2-blockers (cimetidine for ulcers, 1972). Statins came from Akira Endo's work at Sankyo in Japan in the 1970s (he found the first statin in a fungus). Some modern drugs are rationally designed; others come from screening libraries; some come from old plant medicine.",
    },
    # 139 — Mammalian cloning Dolly 1996
    {
        "tier": 4,
        "question": "Dolly the sheep — the first mammal cloned from an adult somatic cell — was born July 5, 1996 at the Roslin Institute in Scotland (Ian Wilmut, Keith Campbell, and colleagues). The technique used 'somatic cell nuclear transfer' — moving a nucleus from an adult cell into an enucleated egg cell. Why was Dolly's birth shocking biologically?",
        "answer": "It overturned the assumption that adult differentiated cells couldn't be 'reprogrammed' back to embryonic potential — opening the way for stem-cell biology and Yamanaka's iPSCs",
        "choices": [
            "It overturned the assumption that adult differentiated cells couldn't be 'reprogrammed' back to embryonic potential — opening the way for stem-cell biology and Yamanaka's iPSCs",
            "It confirmed long-standing predictions — Dolly's birth was widely anticipated by the entire scientific community before her arrival, and no biological surprise emerged",
            "It was later revealed as a hoax — Dolly was an ordinary sheep, and modern mammalian cloning techniques are unrelated to the Roslin Institute work of the 1990s",
            "It produced a giant sheep — Dolly grew to twice normal size, and the technique was abandoned because of the dangerous growth-distortion effects on cloned mammals",
        ],
        "context": "Dolly lived to age 6 (sheep typically live 10-12 years). Mammalian cloning has been demonstrated in many species since — cattle, pigs, dogs, horses, and most controversially monkeys (Macaca clones at the Chinese Academy of Sciences, 2018). Human reproductive cloning remains banned in most jurisdictions; therapeutic cloning is more permissive.",
    },
    # 140 — Open biology question: consciousness in neuroscience
    {
        "tier": 4,
        "question": "Consciousness — the felt experience — has no agreed mechanism in neuroscience. We can identify NEURAL CORRELATES of consciousness but not explain the EXPERIENCE itself. David Chalmers calls this the 'hard problem.' What's the honest scientific answer about consciousness?",
        "answer": "We don't know — there are competing serious frameworks (integrated information theory, global workspace, panpsychism, illusionism)",
        "choices": [
            "We don't know — there are competing serious frameworks (integrated information theory, global workspace, panpsychism, illusionism)",
            "We know everything about consciousness — it's identical to certain neural firing patterns",
            "We know consciousness doesn't exist — the felt experience is an illusion",
            "We know consciousness is identical to information processing — every computer is conscious",
        ],
        "context": "Tononi's Integrated Information Theory measures consciousness via 'phi.' Baars's Global Workspace Theory locates consciousness in cross-brain broadcasting. Panpsychism (Strawson, Goff) treats consciousness as fundamental. Illusionism (Dennett, Frankish) treats the 'felt experience' as itself an illusion. Chalmers coined 'hard problem' in 1995.",
    },
]


# ============================================================================
# Write batches (P1 + P2 + P3) to disk and self-validate
# ============================================================================

all_qs = P1 + P2 + P3
print(f"P1 count: {len(P1)}, P2 count: {len(P2)}, P3 count: {len(P3)}, total: {len(all_qs)}")
out = {
    "tier": 4,
    "summary": {
        "questions_generated": len(all_qs),
        "by_pillar": {"1": len(P1), "2": len(P2), "3": len(P3)},
    },
    "questions": all_qs,
}
OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {OUT_PATH}")


def _label(i: int) -> str:
    if i < len(P1):
        return f"P1[{i}]"
    if i < len(P1) + len(P2):
        return f"P2[{i - len(P1)}]"
    return f"P3[{i - len(P1) - len(P2)}]"


# Validate
dup, ans = build_bank_indices(all_qs)
fails = 0
softs = 0
for i, q in enumerate(all_qs):
    r = validate_rewrite("science", q, bank=all_qs, dup_index=dup, answer_index=ans, replace_idx=i)
    total = len(q["question"]) + sum(len(c) for c in q["choices"])
    if r["verdict"] == "FAIL":
        fails += 1
        print(f"  FAIL {_label(i)} (total={total}c): {q['question'][:80]}")
        for g, reason in r["hard_fails"]:
            print(f"    {g}: {reason[:240]}")
    elif r["verdict"] == "SOFT_WARN":
        softs += 1
        print(f"  SOFT {_label(i)} (total={total}c): {q['question'][:80]}")
        for g, reason in r["soft_warns"]:
            print(f"    {g}: {reason[:200]}")

print(f"\nSUMMARY: {len(all_qs)} questions, {fails} FAIL, {softs} SOFT")
