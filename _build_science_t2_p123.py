"""Build 140 Tier-2 science questions for Pillars 1+2+3.

T2 = grade 6. One-line scene + question. Named figures introduce.
Length cap <= 480 (grace 504). Per SCIENCE_FRAMEWORK + SCIENCE_TEMPLATES (2026-05-26).

Discovery Pattern (controlling voice rule): every question lands on one of
  DISCOVERY > REVERSAL > MYSTERY > MECHANISM recognition.

T2 favors Discovery + Mechanism; reversal primers appear here.

Pillars:
  P1 Physics      (50) — Newton, Galileo, Maxwell, Tycho/Kepler, conservation,
                         Boyle, Archimedes, Pascal, Bernoulli, thermo,
                         Hubble, Penzias+Wilson
  P2 Chemistry    (40) — Dalton, Mendeleev, noble gases, alkalis, halogens,
                         isotopes, bonds, pH, equations, combustion,
                         Lavoisier, Kekule
  P3 Biology      (50) — cell theory, prok/euk, mitochondria/Margulis,
                         Mendel/Punnett, photosynthesis, Darwin/Wallace,
                         food chains, germ theory, Jenner/Pasteur/Salk/Sabin,
                         Hilleman, smallpox 1980, Semmelweis, Marshall
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(r"C:\Users\brand\Documents\PhilosophersQuest")
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

P1: list[dict] = []
P2: list[dict] = []
P3: list[dict] = []


# ===========================================================================
# P1 PHYSICS (50)
# ===========================================================================

# --- Newton (3 laws, gravity, Principia 1687) — 6 ---

P1.append({
    "tier": 2,
    "question": "In 1687 Isaac Newton published the *Principia*. His first law overturned an ancient assumption about motion. What does it say about objects with no forces acting on them?",
    "answer": "They keep moving in a straight line at constant speed forever — rest is not natural",
    "choices": [
        "They keep moving in a straight line at constant speed forever — rest is not natural",
        "They slowly curve toward heavier — nearby objects through built-in cosmic attraction",
        "They gradually come to rest — because motion is a temporary state in nature",
        "They speed up over time as their — inner energy works its way to the surface",
    ],
    "context": "Newton's first law (inertia) replaced the Aristotelian idea that rest is the natural state. Galileo had reached this conclusion first; Newton stated it formally in 1687. The Principia (full title: Philosophiae Naturalis Principia Mathematica) launched modern physics.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Isaac Newton's second law of motion, written F = ma, links three quantities. If you push the same shopping cart twice as hard, what happens to its acceleration?",
    "answer": "It doubles — acceleration is force divided by mass, so more force means more acceleration",
    "choices": [
        "It doubles — acceleration is force divided by mass, so more force means more acceleration",
        "It halves — pushing harder makes the cart resist by becoming twice as heavy",
        "It stays the same — acceleration is set by the cart, not by how you push",
        "It quadruples — every doubling of force gives four times the acceleration in real motion",
    ],
    "context": "Newton's second law (1687) ties force, mass, and acceleration into one equation. Same mass + double the force = double the acceleration. Same force + double the mass = half the acceleration. The law is foundational to engineering, ballistics, and orbital mechanics.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Newton's third law states that every action has an equal and opposite reaction. When you jump off a small boat onto a dock, what does the boat do?",
    "answer": "It scoots backward — your push forward gets a matching push back on the boat",
    "choices": [
        "It scoots backward — your push forward gets a matching push back on the boat",
        "It rises slightly — your jump lifts the boat up by the amount you weigh",
        "It stays exactly still — the water absorbs all the force from your jump",
        "It spins in place — the action and reaction cancel out into rotation",
    ],
    "context": "Newton's third law (1687) explains rockets, swimming, walking, and recoil. Forces always come in equal-and-opposite pairs acting on two different objects. A jumping rocket pushes hot gas down; the gas pushes the rocket up. You push the ground back; the ground pushes you forward.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Newton's law of universal gravitation says every mass attracts every other mass. The pull depends on their masses and the distance between them. What happens to the force if you double the distance?",
    "answer": "It drops to one-quarter — gravity weakens with the square of the distance",
    "choices": [
        "It drops to one-quarter — gravity weakens with the square of the distance",
        "It drops to one-half — gravity weakens in direct proportion to distance",
        "It stays the same — distance has no effect, only masses matter for the force",
        "It doubles — gravity strengthens as objects move farther apart in space",
    ],
    "context": "Newton's inverse-square law of gravitation (1687) extended Kepler's planetary laws to all matter. Double the distance, quarter the force. Triple it, force drops to one-ninth. The same law that pulls an apple from a tree also keeps the Moon orbiting Earth — a unification Newton called 'one of the wonders of nature.'",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "A famous story claims Isaac Newton was inspired by a falling apple in his mother's orchard around 1666. What was Newton's deep insight about that apple?",
    "answer": "The same force pulling the apple down was reaching out to hold the Moon in orbit",
    "choices": [
        "The same force pulling the apple down was reaching out to hold the Moon in orbit",
        "The apple was unusually heavy, which led him to study the mass of fruit in general",
        "The apple's color showed it was ripe, which started his interest in optics and light",
        "The apple bounced upward briefly, suggesting an unknown anti-gravity force in nature",
    ],
    "context": "Newton spent 1665-66 at his family farm during a plague year — his 'annus mirabilis' (miracle year). He developed calculus, the laws of motion, and universal gravitation during this period. The story of the apple was recounted by Newton to William Stukeley in 1726 and survives in Stukeley's memoir.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Newton spent a decade on the *Principia*, published 1687. What problem did Newton solve that Kepler had only described?",
    "answer": "Why planets follow elliptical orbits — gravity as a universal inverse-square force",
    "choices": [
        "Why planets follow elliptical orbits — gravity as a universal inverse-square force",
        "Why the Earth is round — by carefully measuring how shadows fall at noon each year",
        "Why stars appear to twinkle — by tracking light through layers of Earth's atmosphere",
        "Why iron is magnetic — by aligning Earth's field with the iron core deep underground",
    ],
    "context": "Halley (of comet fame) personally funded the Principia's printing because the Royal Society had blown its budget on a fish book. Newton derived Kepler's three laws of planetary motion from his single inverse-square law of gravitation — the first mathematical unification of celestial and terrestrial physics.",
    "_pillar": 1,
})

# --- Galileo (pendulum, falling bodies, telescope 1609) — 6 ---

P1.append({
    "tier": 2,
    "question": "Around 1583 the 19-year-old Galileo Galilei timed the swing of a hanging lamp in a Padua cathedral using his own pulse as a clock. What rule did he find?",
    "answer": "A pendulum's period depends on its length, not on how heavy the weight is",
    "choices": [
        "A pendulum's period depends on its length, not on how heavy the weight is",
        "A pendulum's period depends on the weight, not on the length of the string at all",
        "A pendulum's period changes every hour because air pressure varies inside buildings",
        "A pendulum's period speeds up as the room warms during religious services daily",
    ],
    "context": "Galileo Galilei was a medical student at the University of Pisa. He used his pulse because reliable mechanical clocks didn't yet exist. His pendulum observation later led Christiaan Huygens to invent the first practical pendulum clock in 1656 — revolutionary timekeeping accuracy for the era.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Around 1589 Galileo reportedly dropped two unequal balls from the Leaning Tower of Pisa, testing Aristotle's claim that heavier things fall faster. What did he find?",
    "answer": "Both balls hit the ground at almost the same time — weight doesn't change how fast things fall",
    "choices": [
        "Both balls hit the ground at almost the same time — weight doesn't change how fast things fall",
        "The heavier ball hit first by a wide margin — confirming what Aristotle had taught",
        "Neither ball hit the ground — they both floated in the air for several seconds",
        "The lighter ball hit first by a wide margin — proving heavier things drag in the air",
    ],
    "context": "Whether Galileo did the Pisa demonstration is debated by historians; his student Vincenzo Viviani told the story decades later. Galileo certainly did roll balls down inclined planes and time them, finding all objects accelerate at the same rate regardless of weight. Apollo 15 astronaut David Scott confirmed this on the airless Moon in 1971 with a hammer and a feather.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "In late 1609 Galileo Galilei built his own version of a new instrument from the Netherlands, pointed it at the sky, and made discoveries nobody had ever seen. What was the instrument?",
    "answer": "The telescope — Galileo's improved version magnified objects about 20 times",
    "choices": [
        "The telescope — Galileo's improved version magnified objects about 20 times",
        "The microscope — Galileo turned it on living cells in pond water samples",
        "The barometer — Galileo measured atmospheric pressure changes on different days",
        "The thermometer — Galileo recorded daily temperature changes in his garden",
    ],
    "context": "Hans Lippershey filed a patent for a 'kijker' (telescope) in 1608 in the Netherlands. Galileo built improved versions in mid-1609, eventually reaching about 20x magnification. He pointed it at the sky in late 1609 and within months discovered Jupiter's four large moons, mountains on our Moon, and the phases of Venus — undermining the Earth-centered view of the universe.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "In January 1610 Galileo Galilei pointed his telescope at Jupiter and saw something that contradicted the idea that everything orbits Earth. What did he find?",
    "answer": "Four moons clearly orbiting Jupiter — not everything orbits Earth after all",
    "choices": [
        "Four moons clearly orbiting Jupiter — not everything orbits Earth after all",
        "A pair of rings around Jupiter — proving the planet had its own atmosphere",
        "A single moon shaped like a triangle — a previously unknown geometric form",
        "A glowing red ocean on Jupiter's surface — evidence that life could exist there",
    ],
    "context": "Galileo first observed Io, Europa, Ganymede, and Callisto on January 7, 1610, publishing his Sidereus Nuncius ('Starry Messenger') in March of that year. The Galilean moons orbiting Jupiter were devastating to the Earth-centered Ptolemaic system — they showed that at least some bodies in the heavens orbit something other than Earth.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Galileo Galilei observed the planet Venus through his telescope in 1610 and noticed something Aristotle's Earth-centered model could not explain. What did he see?",
    "answer": "Venus showed full phases like the Moon — proving it orbits the Sun, not the Earth",
    "choices": [
        "Venus showed full phases like the Moon — proving it orbits the Sun, not the Earth",
        "Venus showed a smooth red color — proving its surface was fully covered in ice",
        "Venus had two visible moons of its own — much like Jupiter has its own moons",
        "Venus glowed in the daytime — showing it must produce its own internal light",
    ],
    "context": "In a Sun-centered system, Venus can show a complete cycle of phases — full, gibbous, half, crescent, new — because it orbits the Sun inside Earth's orbit. In an Earth-centered system, Venus could never show a full phase. Galileo's 1610-11 observations were powerful evidence for Copernicus's heliocentric model.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "In 1633 the Roman Inquisition tried Galileo for supporting the idea that Earth moves around the Sun. He was forced to publicly recant. What is he said to have muttered after recanting?",
    "answer": "'And yet it moves' — referring to the Earth, said quietly under his breath",
    "choices": [
        "'And yet it moves' — referring to the Earth, said quietly under his breath",
        "'And yet it shines' — referring to the Sun, in a defiant final whisper",
        "'And yet it falls' — referring to a heavy stone, before walking out alone",
        "'And yet it bends' — referring to light through his telescope's curved lens",
    ],
    "context": "The phrase 'Eppur si muove' is famous but possibly apocryphal — first attributed to Galileo a century after his death. He was condemned for 'vehement suspicion of heresy' in 1633 and held under house arrest until his death in 1642. The Catholic Church formally apologized to Galileo in 1992 under Pope John Paul II.",
    "_pillar": 1,
})

# --- Maxwell (E+M unified 1865) — 4 ---

P1.append({
    "tier": 2,
    "question": "In 1865 Scottish physicist James Clerk Maxwell published a set of four equations that combined two forces previously thought separate. What did Maxwell's equations unify?",
    "answer": "Electricity and magnetism — and they revealed that light is an electromagnetic wave",
    "choices": [
        "Electricity and magnetism — and they revealed that light is an electromagnetic wave",
        "Gravity and magnetism — and they revealed why magnets always point toward Earth",
        "Heat and electricity — and they revealed why hot wires shine with a red glow",
        "Sound and magnetism — and they revealed why bells ring when struck with iron",
    ],
    "context": "Maxwell's 1865 paper 'A Dynamical Theory of the Electromagnetic Field' showed that electricity, magnetism, and light are all expressions of one underlying electromagnetic force. The equations also predicted radio waves, microwaves, and X-rays — all parts of the electromagnetic spectrum, all moving at the speed of light.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Maxwell's 1865 equations gave a specific speed for electromagnetic waves. What did the number turn out to be?",
    "answer": "The calculated wave speed matched the measured speed of light — light is an electromagnetic wave",
    "choices": [
        "The calculated wave speed matched the measured speed of light — light is an electromagnetic wave",
        "The calculated wave speed matched the speed of sound — light is a fast pressure wave",
        "The calculated wave speed was zero — electromagnetic waves cannot travel through space",
        "The calculated wave speed matched a comet's orbit — comets are electromagnetic in nature",
    ],
    "context": "Maxwell computed the speed of an electromagnetic disturbance from his equations: about 300,000 km/s. Hippolyte Fizeau and Léon Foucault had measured the speed of light to be roughly that same value. Maxwell wrote that the agreement 'seems to show that light and magnetism are affections of the same substance.' Heinrich Hertz confirmed Maxwell's predictions experimentally in 1887.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "After Maxwell's 1865 work, German physicist Heinrich Hertz tested it. In 1887 his lab produced and detected something that confirmed Maxwell's predictions. What?",
    "answer": "Radio waves — produced by a spark and detected across the room with a wire loop",
    "choices": [
        "Radio waves — produced by a spark and detected across the room with a wire loop",
        "X-rays — produced by sunlight passed through a thick chunk of clear quartz",
        "Sound waves — produced from electrical sparks and detected by a tuning fork",
        "Microwaves — produced by a heated iron bar and detected by a kettle of water",
    ],
    "context": "Hertz's 1887 experiment generated radio waves with a spark gap and detected them with a loop antenna meters away. He had no idea what they would be good for — when asked he said they were 'nothing, I guess.' Within 15 years, Marconi was sending wireless telegraph signals across the Atlantic. The unit of frequency (Hertz, Hz) is named for him.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "James Clerk Maxwell died in 1879 at age 48, long before relativity. Albert Einstein later kept Maxwell's photograph on his study wall. Why did Einstein consider Maxwell's work foundational?",
    "answer": "His equations were the starting point — they led to Einstein's special relativity",
    "choices": [
        "His equations were the starting point — they led to Einstein's special relativity",
        "His equations described iron magnets — but only at very cold temperatures",
        "His equations had been disproved by 1900 — Einstein had to rebuild them",
        "His equations explained chemical reactions — inside ordinary batteries",
    ],
    "context": "Maxwell's equations require that the speed of light is the same in all reference frames — a result inconsistent with classical mechanics. Einstein took this seriously, and the 1905 special relativity paper was titled 'On the Electrodynamics of Moving Bodies.' Einstein once said: 'I stand on the shoulders of Maxwell.'",
    "_pillar": 1,
})

# --- Tycho Brahe + Kepler — 4 ---

P1.append({
    "tier": 2,
    "question": "Danish astronomer Tycho Brahe spent decades making precise naked-eye planetary observations. In a 1566 duel, what did he lose that he later wore a metal replacement for?",
    "answer": "Part of his nose — replaced with a brass or silver prosthetic he wore for life",
    "choices": [
        "Part of his nose — replaced with a brass or silver prosthetic he wore for life",
        "Part of his right ear — replaced with a carved wooden ear he wore in public",
        "Two of his front teeth — replaced with carved ivory teeth held by gold wires",
        "His left eye — replaced with a polished glass eye made by a Venetian craftsman",
    ],
    "context": "Tycho Brahe lost part of his nose in a 1566 sword duel with another Danish nobleman over a mathematical disagreement. He wore a prosthetic — possibly brass with a copper/silver alloy mix for the visible part — for the rest of his life. When his body was exhumed in 2010, traces of brass were found around his nasal cavity.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Tycho Brahe died in 1601 and left his planetary data to his assistant. After years working through it, the assistant discovered something stunning about the orbit of Mars. Who was he?",
    "answer": "Johannes Kepler — and he discovered that Mars's orbit is an ellipse, not a circle",
    "choices": [
        "Johannes Kepler — and he discovered that Mars's orbit is an ellipse, not a circle",
        "Galileo Galilei — and he discovered that Mars orbits Jupiter rather than the Sun",
        "Christiaan Huygens — and he discovered that Mars has two small irregular moons",
        "Isaac Newton — and he discovered that Mars's orbit is a perfect circle after all",
    ],
    "context": "Kepler joined Tycho Brahe in Prague in 1600. Tycho died unexpectedly in 1601, possibly from a burst bladder. Kepler took years to fit Mars's orbit, finally discovering in 1605 it was an ellipse with the Sun at one focus — the first of his three laws of planetary motion, published in Astronomia Nova (1609).",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Johannes Kepler's first law of planetary motion (1609) overturned an assumption that had been held for 2,000 years since Aristotle. What did Kepler discover that planetary orbits are NOT?",
    "answer": "They are not perfect circles — they are ellipses with the Sun at one focus",
    "choices": [
        "They are not perfect circles — they are ellipses with the Sun at one focus",
        "They are not closed loops — they spiral outward away from the Sun each year",
        "They are not in a plane — they twist into three-dimensional cones around the Sun",
        "They are not steady — they zigzag back and forth from week to week unpredictably",
    ],
    "context": "Plato, Aristotle, Ptolemy, and Copernicus all assumed planetary orbits were perfect circles, sometimes with circles-on-circles ('epicycles') to fix the data. Kepler discovered that Mars's orbit is an ellipse. His three laws (1609, 1619) described HOW planets move; Newton (1687) explained WHY using universal gravitation.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Kepler's third law (1619) relates each planet's orbital period to its distance from the Sun. What's the simple version of that relationship?",
    "answer": "Planets farther from the Sun take much longer to complete one orbit — distance and period are linked",
    "choices": [
        "Planets farther from the Sun take much longer to complete one orbit — distance and period are linked",
        "All planets take exactly one year to orbit the Sun — distance doesn't change the period",
        "Planets closer to the Sun take longer to orbit — gravity slows them down near the Sun",
        "Planet orbits depend on size — bigger planets always take longer regardless of distance",
    ],
    "context": "Kepler's third law: T² ∝ a³, where T is the orbital period and a is the average distance from the Sun. Mercury (close) takes 88 days; Neptune (far) takes 165 years. The exact relationship lets astronomers calculate the mass of any star with an orbiting planet. Kepler called it the 'Harmonic Law' in his book *Harmonices Mundi* (Harmonies of the World, 1619).",
    "_pillar": 1,
})

# --- Conservation laws — 4 ---

P1.append({
    "tier": 2,
    "question": "Throw a tennis ball straight up. As it rises, it slows down. At the very top of its flight, it stops for an instant. Where did all its motion energy go while it was rising?",
    "answer": "Into stored gravitational energy — height above the ground stores energy",
    "choices": [
        "Into stored gravitational energy — height above the ground stores energy",
        "Into heat — friction with the air warms the ball as it rises in the sky",
        "Into a sound wave — every moving ball emits a low-frequency hum inaudible to us",
        "Into nothing — the energy disappears and reappears when the ball falls back down",
    ],
    "context": "Conservation of energy is one of the deepest principles in physics. Kinetic energy (motion) converts to potential energy (height) and back. A small amount is lost to air drag as heat. The total is conserved. Hermann von Helmholtz formalized energy conservation in 1847. Emmy Noether proved (1918) that every conservation law corresponds to a symmetry in nature.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "A billiard cue ball strikes a stationary red ball directly. The cue ball stops; the red ball rolls off at the cue ball's original speed. What physical quantity has been transferred?",
    "answer": "Momentum — the product of mass and velocity, conserved in a clean collision",
    "choices": [
        "Momentum — the product of mass and velocity, conserved in a clean collision",
        "Energy — but only the type that comes from the green felt under the balls",
        "Mass — the cue ball gave a tiny bit of its weight directly to the red ball",
        "Magnetism — the iron in the balls transfers naturally on every clean contact",
    ],
    "context": "Conservation of momentum (mass × velocity) was first stated clearly by John Wallis (1670). In a clean two-ball collision of equal masses, momentum can transfer completely. The principle explains rocket propulsion, recoil in guns, and Newton's cradle. Like energy conservation, momentum conservation is tied to a symmetry — in this case, the symmetry of space under translation.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "When you rub your hands together hard, they warm up. The kinetic energy of your moving hands hasn't vanished — it has changed form. Into what?",
    "answer": "Heat — the random kinetic energy of molecules in your skin and the air",
    "choices": [
        "Heat — the random kinetic energy of molecules in your skin and the air",
        "Sound — but at a pitch too low for human ears to pick up at the time",
        "Magnetism — your hands briefly become weak magnets while you rub them",
        "Static electricity — entirely, even on hot humid days when none builds up",
    ],
    "context": "James Prescott Joule (1845) measured the mechanical equivalent of heat by stirring water with paddle wheels and tracking the temperature rise. His work cemented the idea that heat is a form of energy. The unit of energy (the joule, J) is named for him. Friction always converts ordered motion to disordered thermal motion — never the reverse spontaneously.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "A roller coaster car at the top of a 30-meter hill has stored potential energy. Ignoring friction, what determines the car's speed at the bottom?",
    "answer": "Only the height it dropped — not its mass, not the track shape, not its starting speed at rest",
    "choices": [
        "Only the height it dropped — not its mass, not the track shape, not its starting speed at rest",
        "Only the mass of the car — heavier cars always reach a higher speed at the bottom",
        "Only the shape of the track — twisty paths add speed because of the extra turns",
        "Only the time it took — slower descents always end at a higher speed at the bottom",
    ],
    "context": "Energy conservation: mgh (gravitational potential energy) = ½mv² (kinetic energy). The mass cancels on both sides, so the bottom speed depends only on the height. This is why a feather and a bowling ball reach the same speed falling in vacuum — and why all skiers on a frictionless slope would reach the bottom going equally fast regardless of weight.",
    "_pillar": 1,
})

# --- Boyle's law — 2 ---

P1.append({
    "tier": 2,
    "question": "In 1662 Irish chemist Robert Boyle showed: squeeze a gas into half its volume at steady temperature, and something happens to its pressure. What?",
    "answer": "The pressure doubles — pressure and volume are inversely linked at constant temperature",
    "choices": [
        "The pressure doubles — pressure and volume are inversely linked at constant temperature",
        "The pressure halves — squeezing a gas always makes it press back less on the walls",
        "The pressure stays the same — volume changes never affect pressure if the gas is sealed",
        "The pressure becomes zero — squeezed gases cease to exert any pressure at all",
    ],
    "context": "Boyle's law (1662): P × V = constant at fixed temperature. Robert Boyle is often called the father of modern chemistry. He published *The Sceptical Chymist* (1661), distinguishing chemistry from alchemy. His careful experiments with gases and his insistence on reproducible results set the standard for the scientific method.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "You pump air into a bicycle tire and notice the pump's metal cylinder gets noticeably warm. What's happening at the molecule level?",
    "answer": "Compressing the air speeds up its molecules, raising the temperature inside the pump",
    "choices": [
        "Compressing the air speeds up its molecules, raising the temperature inside the pump",
        "Magnetic friction in the pump's piston produces heat from passing iron filings",
        "The tire warms first and conducts heat back into the pump through the air hose",
        "The pump generates its own internal electric current that heats the metal walls",
    ],
    "context": "Compression heating: doing mechanical work on a gas increases the average kinetic energy of its molecules — that's what temperature measures. Diesel engines exploit this: air is compressed so much it heats enough to ignite fuel without a spark plug. The same physics warms the air at the bottom of a deep mine — and chills it in a refrigerator's expansion valve.",
    "_pillar": 1,
})

# --- Archimedes (Eureka) — 2 ---

P1.append({
    "tier": 2,
    "question": "Greek mathematician Archimedes (around 250 BC) was asked by King Hiero of Syracuse to test if a goldsmith's crown was pure gold. Where did Archimedes have his insight?",
    "answer": "In a bath — water spilled over and he saw he could measure volume by displacement",
    "choices": [
        "In a bath — water spilled over and he saw he could measure volume by displacement",
        "In a temple — he saw a priest weighing offerings on a balance during a ceremony",
        "On a beach — he watched ships float higher with empty holds than with full ones",
        "In a market — he noticed a vegetable seller balancing produce against stones",
    ],
    "context": "The story has Archimedes leaping from the bath and running naked through the streets shouting 'Eureka!' (Greek for 'I have found it!'). He realized that an object's volume equals the volume of water it displaces. A crown made of pure gold of a given weight should displace less water than the same weight of a gold/silver mix, since silver is less dense. The story is from Vitruvius, written 200 years later.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Archimedes's principle (around 250 BC) explains why a steel cargo ship floats but a steel marble sinks. What does the principle actually say?",
    "answer": "An object in water is pushed up by a force — equal to the weight of water it displaces",
    "choices": [
        "An object in water is pushed up by a force — equal to the weight of water it displaces",
        "An object in water is pushed up by a force — equal to its own weight in the air",
        "An object in water sinks if it weighs anything — only massless things ever float",
        "An object in water rises if its color is light — and sinks if its color is dark",
    ],
    "context": "A steel ship's hull displaces a huge volume of water — much more than the ship weighs — so the buoyant force exceeds its weight and it floats. A steel marble displaces only its own volume of water (much less than its weight), so it sinks. This same principle lets balloons rise in air, submarines submerge by taking on water as ballast, and fish adjust depth using gas-filled swim bladders.",
    "_pillar": 1,
})

# --- Pascal (pressure) — 2 ---

P1.append({
    "tier": 2,
    "question": "French scientist Blaise Pascal showed in the 1640s that liquids in a closed system carry pressure in a useful way. What's the practical rule?",
    "answer": "Pressure applied anywhere in a confined liquid is transmitted unchanged throughout",
    "choices": [
        "Pressure applied anywhere in a confined liquid is transmitted unchanged throughout",
        "Pressure applied to a liquid stays only in the place where it was applied first",
        "Pressure applied to a liquid only travels downward toward the bottom of the container",
        "Pressure applied to a liquid bounces back to its source within a few seconds always",
    ],
    "context": "Pascal's principle is the basis of hydraulic systems: a small force on a small piston produces a large force on a large piston through a connected fluid. Car brakes, dental chairs, garage lifts, and earthmovers all use this. Pascal also showed (via his brother-in-law Florin Périer in 1648) that atmospheric pressure drops with altitude — barometer mercury falls as you climb a mountain.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "A hydraulic car jack lets one person lift a 2,000-kg car by pushing a small handle. What scientific principle, named after a French scientist, makes this possible?",
    "answer": "Pascal's principle — small force on a small piston becomes large force on a large piston",
    "choices": [
        "Pascal's principle — small force on a small piston becomes large force on a large piston",
        "Pascal's principle — adding warm water to the jack reduces the weight of the car",
        "Pascal's principle — magnetic fields in steel allow heavy things to lift themselves",
        "Pascal's principle — friction between rubber and asphalt reduces the car's mass",
    ],
    "context": "Blaise Pascal (1623-1662) was a child prodigy who proved theorems in geometry by age 16 and built a working mechanical calculator at 19. His pressure work in the 1640s was foundational. He died at 39 after years of poor health, leaving the unfinished Pensées (Thoughts) — a celebrated work of Christian philosophy.",
    "_pillar": 1,
})

# --- Bernoulli (lift) — 2 ---

P1.append({
    "tier": 2,
    "question": "Swiss mathematician Daniel Bernoulli, in his 1738 book *Hydrodynamica*, described a property of moving fluids that helps explain why airplanes can fly. What's the key idea?",
    "answer": "Faster-moving fluid exerts lower pressure than slower-moving fluid alongside it",
    "choices": [
        "Faster-moving fluid exerts lower pressure than slower-moving fluid alongside it",
        "Faster-moving fluid exerts higher pressure than slower-moving fluid alongside it",
        "Moving fluids exert exactly the same pressure as still fluids at all flow speeds",
        "Moving fluids exert pressure only on the bottom surfaces of objects passing through",
    ],
    "context": "Bernoulli's principle: in steady fluid flow, faster flow corresponds to lower pressure. Airplane wings are shaped so air moves faster over the top than the bottom, creating a pressure difference that lifts the plane. The same principle explains why a roof can be ripped off a house in high winds (fast wind above, normal pressure inside), and why a curveball curves.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Hold two strips of paper a few centimeters apart and blow hard between them. What does the paper do, and why?",
    "answer": "The strips move toward each other — fast-moving air between them has lower pressure",
    "choices": [
        "The strips move toward each other — fast-moving air between them has lower pressure",
        "The strips move apart from each other — your breath pushes them outward in opposite ways",
        "The strips stay perfectly still — blowing between them has no measurable physical effect",
        "The strips drop straight down — fast air removes lift and makes them too heavy to hold",
    ],
    "context": "Bernoulli's principle at home: the fast air you blow between the strips has lower pressure than the still air on the outside. Higher pressure outside pushes the strips together. This is the same physics that lifts wings, makes shower curtains pull inward when the shower runs, and makes Frisbees fly.",
    "_pillar": 1,
})

# --- Thermodynamics 1st + 2nd laws — 4 ---

P1.append({
    "tier": 2,
    "question": "The first law of thermodynamics is sometimes called the law of conservation of energy. What's the simplest version of what it says?",
    "answer": "Energy cannot be created or destroyed — only converted from one form to another",
    "choices": [
        "Energy cannot be created or destroyed — only converted from one form to another",
        "Energy can be created freely if you have — the right machine that runs on no fuel",
        "Energy slowly disappears over time — which is why all systems eventually stop moving",
        "Energy doubles whenever heat is added — since heat is the strongest form of energy",
    ],
    "context": "The first law was developed by Julius von Mayer, James Prescott Joule, and Hermann von Helmholtz in the 1840s. It rules out perpetual motion machines of the 'first kind' (machines that produce energy from nothing). All energy converters — engines, cells, muscles — must follow it.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "The second law of thermodynamics introduced a quantity called entropy, which always tends to increase over time. What's the everyday meaning?",
    "answer": "Disorder tends to grow over time in any closed system on its own",
    "choices": [
        "Disorder tends to grow over time in any closed system on its own",
        "Energy always concentrates itself in one place over time without any outside help",
        "Order spontaneously builds up over time without any input of work from outside",
        "Temperature stays exactly constant in every closed system regardless of time",
    ],
    "context": "Rudolf Clausius coined 'entropy' in 1865 and stated the second law as 'the entropy of the universe tends to a maximum.' Hot coffee cools to room temperature, never the reverse. A scrambled egg doesn't unscramble. Sand castles erode; they don't self-assemble. Life maintains internal order only by exporting greater disorder to the environment.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Heat from a hot cup of coffee always flows into the cooler air around it — never the other way. This one-way behavior of heat flow is captured in which law of physics?",
    "answer": "The second law of thermodynamics — heat naturally flows from hot to cold",
    "choices": [
        "The second law of thermodynamics — heat naturally flows from hot to cold",
        "The second law of thermodynamics — heat naturally flows from cold to hot",
        "The first law of thermodynamics — energy can move only in straight lines forever",
        "Newton's first law of motion — heat is itself a slow-moving object in a straight line",
    ],
    "context": "The second law has multiple equivalent formulations. Clausius (1850): heat does not spontaneously flow from a cooler body to a hotter one. Kelvin-Planck: no heat engine can convert all its absorbed heat into work. Boltzmann statistical version: systems evolve toward more probable (higher-entropy) states. All three are mathematically equivalent.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Many inventors have claimed to build a machine that runs forever without fuel, producing more energy than it uses. Mainstream physics rejects every such claim. Why?",
    "answer": "They would violate thermodynamics' first or second law — both very well tested",
    "choices": [
        "They would violate thermodynamics' first or second law — both very well tested",
        "They would violate Newton's third law of motion — every action needs a reaction",
        "They would violate Boyle's gas law — which forbids machines that contain sealed gases",
        "They would violate Snell's law — light from such machines cannot reflect off surfaces",
    ],
    "context": "Perpetual motion machines of the 'first kind' violate energy conservation (first law). Machines of the 'second kind' would extract heat from a single reservoir and convert it fully into work — violating the second law. The US Patent Office has refused to consider perpetual-motion patent applications since 1911 unless a working model is provided.",
    "_pillar": 1,
})

# --- Hubble (galaxies receding 1929) — 3 ---

P1.append({
    "tier": 2,
    "question": "In 1929 American astronomer Edwin Hubble published measurements of distant galaxies showing something startling about the universe. What did he find?",
    "answer": "The galaxies are moving away from us, and the farther ones are moving faster",
    "choices": [
        "The galaxies are moving away from us, and the farther ones are moving faster",
        "The galaxies are moving toward us, and they will all collide with us in a billion years",
        "The galaxies are perfectly still, with only the planets in them spinning around the Sun",
        "The galaxies are arranged in a perfect ring around our Milky Way at one fixed distance",
    ],
    "context": "Hubble used the 100-inch telescope at Mount Wilson Observatory. His 1929 paper showed a linear relationship between a galaxy's distance and its recession speed — what we now call Hubble's law. The discovery was crucial evidence for an expanding universe, supporting Georges Lemaître's 1927 'primeval atom' model — what we now call the Big Bang.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "In 1927 Belgian priest Georges Lemaître proposed the universe began from a 'primeval atom' and has been expanding ever since. Fred Hoyle mocked the idea with what catchy phrase that became its name?",
    "answer": "'The Big Bang' — coined as mockery, kept as the standard term",
    "choices": [
        "'The Big Bang' — coined as mockery, kept as the standard term",
        "'The Great Flash' — a name used briefly but dropped after a few years",
        "'The Cosmic Pop' — never widely adopted in any astronomy textbook",
        "'The Universal Burst' — abandoned after astronomers found it too dramatic",
    ],
    "context": "Lemaître's expanding-universe paper appeared in 1927. Hoyle preferred a 'steady state' model with new matter created continuously to keep cosmic density constant. He called the rival model 'this big bang idea' on BBC radio in 1949 — meaning to mock it. The name stuck even after the discovery of the cosmic microwave background (1964) decisively favored the Big Bang.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "When astronomers look at light from a galaxy moving away from us, the light is stretched into longer wavelengths. What's this effect called?",
    "answer": "Redshift — the light shifts toward the red end of the spectrum",
    "choices": [
        "Redshift — the light shifts toward the red end of the spectrum",
        "Blueshift — light from receding galaxies always shifts toward the blue end",
        "Greenshift — light from very distant galaxies takes on a faint green color",
        "Whiteshift — light becomes a featureless white as galaxies move away over time",
    ],
    "context": "Redshift was the key tool in Hubble's 1929 work. Light from galaxies moving away is stretched (longer wavelength, redder); light from galaxies moving toward us is compressed (shorter wavelength, bluer). The same effect makes a passing ambulance siren change pitch — Christian Doppler described it in 1842 for sound waves. Hippolyte Fizeau extended it to light in 1848.",
    "_pillar": 1,
})

# --- Penzias + Wilson CMB 1964 — 3 ---

P1.append({
    "tier": 2,
    "question": "In 1964 two Bell Labs engineers, Arno Penzias and Robert Wilson, were testing a radio antenna and kept picking up a faint hiss they couldn't get rid of. What was the source?",
    "answer": "The cosmic microwave background — leftover radiation from the early hot universe",
    "choices": [
        "The cosmic microwave background — leftover radiation from the early hot universe",
        "Pigeons nesting inside the antenna — the dust they kicked up made the hiss",
        "Soviet radar interference — picked up across the Atlantic Ocean on certain days",
        "A failing connector in the antenna's wiring — replaced and the hiss went away",
    ],
    "context": "Penzias and Wilson did eliminate pigeon droppings from the antenna (it turned out not to be the cause). The hiss came from every direction in the sky equally — and matched a prediction made by Robert Dicke's group at Princeton, just down the road. The signal was the afterglow of the Big Bang, redshifted from infrared (when it was emitted ~380,000 years after the Big Bang) into microwaves today.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "The cosmic microwave background — the radio hiss Penzias and Wilson detected in 1964 — is sometimes called the 'oldest light in the universe.' How old, roughly, is the light we measure today?",
    "answer": "About 13.8 billion years old — released ~380,000 years after the Big Bang",
    "choices": [
        "About 13.8 billion years old — released ~380,000 years after the Big Bang",
        "About 4.5 billion years old — released around the time the Sun first formed",
        "About 10,000 years old — released around the time of the earliest human civilizations",
        "About 100 years old — released by Earth's first powerful radio broadcasts",
    ],
    "context": "The cosmic microwave background was released when the universe cooled enough (~380,000 years post-Big Bang) for electrons to combine with protons into neutral hydrogen, allowing light to travel freely. That light has been redshifting and cooling for 13.8 billion years to reach us as microwave radiation today, with a temperature of about 2.73 K. Penzias and Wilson shared the 1978 Nobel in Physics.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "After Penzias and Wilson detected the cosmic microwave background in 1964, satellites mapped it in detail. The COBE map of 1992 revealed something key about the early universe. What?",
    "answer": "Tiny temperature variations — the seeds of all later galaxies and clusters",
    "choices": [
        "Tiny temperature variations — the seeds of all later galaxies and clusters",
        "A perfectly smooth uniform glow — proving the early universe had no structure at all",
        "Bright spots on Earth's side of the sky — evidence of Earth's special location",
        "Sharp boundaries between regions — like a giant cosmic checkerboard pattern",
    ],
    "context": "The COBE (Cosmic Background Explorer) satellite, led by George Smoot and John Mather, found temperature differences of about one part in 100,000 across the CMB. Those tiny variations gravitationally amplified over billions of years into the structure of galaxies and clusters we see today. Smoot and Mather won the 2006 Nobel in Physics. WMAP (2003) and Planck (2013) gave even finer maps.",
    "_pillar": 1,
})

# --- P1 extras / kinematics + waves + sound — 8 ---

P1.append({
    "tier": 2,
    "question": "When you ride in an elevator that suddenly starts going up, you briefly feel heavier. When it suddenly stops, you feel lighter. Which of Newton's laws best explains why?",
    "answer": "His second law — your apparent weight depends on the elevator's acceleration",
    "choices": [
        "His second law — your apparent weight depends on the elevator's acceleration",
        "His first law — moving elevators are always lighter than still ones",
        "His third law — every elevator pushes back on the person inside it",
        "His law of gravity — gravity changes inside any moving metal box",
    ],
    "context": "Apparent weight is the normal force from the floor. When the elevator accelerates upward, the floor must push harder than your weight to both support and accelerate you — you feel heavier. When it decelerates, the floor pushes less hard — you feel lighter. Free-falling elevators (or astronauts in orbit) experience zero apparent weight.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "A passenger jet takes off, climbs to cruising altitude, and flies steadily at 900 km/h. While it's flying steadily at constant speed and altitude, what's the net force on the airplane?",
    "answer": "Zero — at constant velocity all the forces (thrust, drag, lift, weight) cancel out",
    "choices": [
        "Zero — at constant velocity all the forces (thrust, drag, lift, weight) cancel out",
        "Forward only — the engine's thrust is the only force the plane experiences",
        "Backward only — air drag is the only force acting once the plane reaches cruise",
        "Downward only — gravity is the only force on a steadily flying jet in the sky",
    ],
    "context": "Newton's first and second laws: at constant velocity, acceleration is zero, so the net force is zero. In level cruise, thrust = drag and lift = weight. The plane keeps moving forward because nothing is slowing it down (drag is balanced by thrust), not because the engine is constantly 'pushing' against some natural tendency to stop.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "An ambulance with its siren on drives past you. As it approaches, the siren sounds higher in pitch. As it drives away, the pitch drops. What's this effect called?",
    "answer": "The Doppler effect — wave frequency changes when the source moves relative to you",
    "choices": [
        "The Doppler effect — wave frequency changes when the source moves relative to you",
        "The Newton effect — siren frequency depends only on ambulance engine speed",
        "The Bernoulli effect — fast air around the siren changes the pitch you hear",
        "The Maxwell effect — electromagnetic waves shift only at very high speeds in vacuum",
    ],
    "context": "Christian Doppler described the effect for sound and light in 1842. As the source approaches, each wave crest is emitted from a slightly closer position, packing the waves closer together (higher frequency). As it recedes, waves spread out (lower frequency). The effect explains galaxy redshifts, weather radar, fetal heart-rate monitors, and police speed traps.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Lightning and thunder happen at the same moment, but you see the lightning flash before you hear the thunder rumble. Why is that?",
    "answer": "Light travels much faster than sound — light is nearly instantaneous; sound takes time",
    "choices": [
        "Light travels much faster than sound — light is nearly instantaneous; sound takes time",
        "Sound travels much faster than light — but only on humid summer afternoons",
        "Lightning happens first by a few seconds — thunder only forms after the bolt ends",
        "Your ears process more slowly than your eyes — but the signals arrive together",
    ],
    "context": "Light travels at about 300,000 km/s. Sound in air travels at about 0.34 km/s — roughly a million times slower. The familiar rule: count seconds between flash and thunder, divide by 3 for the lightning's distance in kilometers (or by 5 for miles). Five seconds = roughly one mile away.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Why is the daytime sky blue?",
    "answer": "Air molecules scatter shorter blue wavelengths of sunlight more than longer red ones",
    "choices": [
        "Air molecules scatter shorter blue wavelengths of sunlight more than longer red ones",
        "Air molecules absorb red light from the Sun and re-emit it back into outer space",
        "The oceans reflect their color onto the sky, giving it a permanent blue tint above",
        "The Sun itself emits more blue light than any other color throughout the day",
    ],
    "context": "Rayleigh scattering, named for Lord Rayleigh (John William Strutt) who explained it in 1871: shorter wavelengths scatter more strongly off air molecules. Blue light bounces around the atmosphere, reaching your eyes from all directions — the sky looks blue. At sunset, light travels through more atmosphere, and most of the blue has been scattered out — you see the longer red and orange that remain.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "A guitar string vibrates back and forth in the air. The sound reaches your ear as a wave. What does the wave actually travel through?",
    "answer": "Air molecules pushing on neighboring molecules — sound is a pressure wave",
    "choices": [
        "Air molecules pushing on neighboring molecules — sound is a pressure wave",
        "Empty space directly — sound travels just like light through any vacuum",
        "Electromagnetic vibrations in the air — same as radio waves and visible light",
        "Tiny invisible strings — one for each note, stretched between the source and ear",
    ],
    "context": "Sound is a mechanical wave — vibrating molecules pass energy to their neighbors as pressure pulses. That's why sound needs a medium (air, water, metal) and can't cross empty space. In space, no one really can hear you scream. The astronaut microphone-in-helmet sound effects in space movies are dramatic license, not physics.",
    "_pillar": 1,
})

# --- P1 wrap-up: misc cosmology/forces — 2 ---

P1.append({
    "tier": 2,
    "question": "The Sun emits energy steadily through a process going on in its core. What's that energy-releasing process called?",
    "answer": "Nuclear fusion — hydrogen atoms fuse into helium, releasing energy as light",
    "choices": [
        "Nuclear fusion — hydrogen atoms fuse into helium, releasing energy as light",
        "Combustion — the Sun burns oxygen and carbon like a giant chemical fire",
        "Friction — the Sun's surface layers rub together, producing heat and light",
        "Electromagnetic induction — the Sun's spinning iron core powers everything",
    ],
    "context": "Hans Bethe worked out the nuclear-fusion proton-proton chain in 1939, explaining how the Sun and other main-sequence stars produce energy. In the core, four hydrogen nuclei fuse over many steps into one helium nucleus. The helium weighs slightly less than the four hydrogens — the missing mass becomes energy via E = mc². The Sun has been doing this for 4.6 billion years.",
    "_pillar": 1,
})

P1.append({
    "tier": 2,
    "question": "Albert Einstein's 1905 paper on relativity included a famous equation relating mass and energy. What does E = mc² mean in plain English?",
    "answer": "A small amount of mass — can be converted into a huge amount of energy",
    "choices": [
        "A small amount of mass — can be converted into a huge amount of energy",
        "Mass and energy are completely separate — they never interchange in any way",
        "Energy can be created from nothing — using ordinary chemical reactions",
        "Mass and speed are the same thing — light only moves at one fixed mass",
    ],
    "context": "E = mc² (E equals m times c squared, where c is the speed of light, ~300,000 km/s). Because c² is enormous, even a small mass corresponds to vast energy. The equation explains why nuclear fission and fusion release so much energy (a tiny mass deficit times c²) and is foundational to all modern physics — from the Sun's energy to medical PET scans.",
    "_pillar": 1,
})

# Quick sanity: should now have 50 P1
assert len(P1) == 50, f"P1 expected 50, got {len(P1)}"


# ===========================================================================
# P2 CHEMISTRY (40)
# ===========================================================================

# --- Dalton (atoms) — 4 ---

P2.append({
    "tier": 2,
    "question": "In 1808 English chemist John Dalton published a theory that revolutionized chemistry. What did Dalton claim was the basic unit that all matter is made of?",
    "answer": "Atoms — tiny indivisible particles, with each element having its own kind",
    "choices": [
        "Atoms — tiny indivisible particles, with each element having its own kind",
        "The four classical elements: earth — air, fire, and water in different mixes",
        "A single substance called phlogiston — released when anything burns or rusts",
        "Liquid droplets — every solid is just a frozen pattern of these droplets",
    ],
    "context": "John Dalton (1766-1844) was a Quaker schoolteacher with an early scientific obsession. His 1808 'New System of Chemical Philosophy' proposed atoms as small, indestructible, distinct for each element, and combining in fixed ratios. Some details were later revised — atoms turned out to have substructure — but the core idea remains foundational.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "John Dalton noticed that elements always combine in fixed whole-number ratios. Water is always H₂O — never H₁.₅O. What did this whole-number pattern strongly suggest to Dalton in 1808?",
    "answer": "Matter must be made of discrete units (atoms) that combine in fixed counts",
    "choices": [
        "Matter must be made of discrete units (atoms) that combine in fixed counts",
        "Water can only form in specific buckets with measured volumes inside them",
        "Chemical bonds happen only on specific days of the lunar calendar each month",
        "Oxygen and hydrogen exist only in the upper atmosphere of Earth at all times",
    ],
    "context": "Dalton's law of multiple proportions: when two elements combine in different ratios to form different compounds, the ratios are always small whole numbers. Carbon and oxygen form CO (1:1) and CO₂ (1:2), never CO₁.₅. This whole-number behavior was strong evidence for the atom — chemistry was happening one tiny unit at a time.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "In 1911 Rutherford fired alpha particles at a thin metal sheet. Most went through, but a few bounced back. What did Rutherford famously say about the result?",
    "answer": "It was 'as if you had fired a 15-inch shell at tissue paper and it came back at you'",
    "choices": [
        "It was 'as if you had fired a 15-inch shell at tissue paper and it came back at you'",
        "It was 'just what every careful scientist had predicted for many decades'",
        "It was 'proof that the entire experiment had been done backwards'",
        "It was 'a sign that gold leaf cannot be used in any future experiment'",
    ],
    "context": "Rutherford was firing alpha particles (helium nuclei) at gold foil. Most went straight through (atoms are mostly empty space), but a small fraction bounced backward — they had hit something tiny but very dense. Rutherford realized atoms have a small dense nucleus, replacing J.J. Thomson's 'plum pudding' atomic model. The discovery launched modern atomic physics.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Atoms have three main types of particles: protons, neutrons, and electrons. Which two live in the nucleus together, and which one orbits around it?",
    "answer": "Protons and neutrons live in the nucleus; electrons orbit around it",
    "choices": [
        "Protons and neutrons live in the nucleus; electrons orbit around it",
        "Electrons and neutrons live in the nucleus; protons orbit around it",
        "Protons and electrons live in the nucleus; neutrons orbit around it",
        "All three particles live in the nucleus; nothing orbits around an atom",
    ],
    "context": "Protons carry positive charge, electrons carry equal negative charge, neutrons are neutral. The proton was identified by Rutherford (1917). The neutron was discovered by James Chadwick in 1932 — explaining why atoms weigh more than their proton count alone. Electrons (J.J. Thomson, 1897) are about 1/1836 the mass of a proton.",
    "_pillar": 2,
})

# --- Mendeleev (1869, predicted gaps) + periodic table — 4 ---

P2.append({
    "tier": 2,
    "question": "In 1869 Russian chemist Dmitri Mendeleev arranged the known chemical elements into a table that showed repeating patterns. What did he do that proved his table wasn't arbitrary?",
    "answer": "He left gaps and predicted properties of undiscovered elements that were later found",
    "choices": [
        "He left gaps and predicted properties of undiscovered elements that were later found",
        "He filled every cell with one of the four classical elements rearranged",
        "He listed only the metals because non-metals weren't recognized in his day",
        "He measured each element's price and arranged them from cheapest to costliest",
    ],
    "context": "Mendeleev's 1869 periodic table grouped elements with similar chemical behavior into columns. He left blanks for predicted elements — eka-aluminum, eka-silicon, eka-boron — with detailed predictions for their atomic masses, densities, melting points. Gallium (1875), scandium (1879), and germanium (1886) were discovered and matched his predictions almost exactly. The predictions vindicated the periodic law.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "The vertical columns in the periodic table are called 'groups,' and elements in the same group behave similarly because of something they share. What is it?",
    "answer": "The same number of electrons in their outermost shell — driving chemical behavior",
    "choices": [
        "The same number of electrons in their outermost shell — driving chemical behavior",
        "The same total number of electrons — in every atom of the element",
        "The same atomic mass — heavier and lighter atoms always cluster in columns",
        "The same color in their solid form — visible patterns across each group",
    ],
    "context": "Mendeleev's 1869 table grouped elements by chemical behavior without knowing the electron explanation. Niels Bohr's atomic model (1913) and quantum mechanics (1920s) showed why: elements in the same column have the same outer-shell electron count. That outer shell determines how an atom bonds with others.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "A periodic table can have over 118 elements today, but only about 90 occur naturally on Earth. Where did the rest come from?",
    "answer": "They were made in laboratories or nuclear reactors — usually only briefly stable",
    "choices": [
        "They were made in laboratories or nuclear reactors — usually only briefly stable",
        "They were brought back from the Moon — by Apollo astronauts during landings",
        "They were discovered inside ancient meteorites collected — from Antarctic ice",
        "They were synthesized only — in volcanic ash from major eruptions on Earth",
    ],
    "context": "Elements 1-94 occur in nature (some only in trace amounts). Elements 95 and above are synthetic — created by smashing nuclei together in particle accelerators. Many last only milliseconds before decaying. Oganesson (element 118, named for Yuri Oganessian) was first synthesized in 2002 at Dubna, Russia. The Cold War-era 'transuranium element race' was fierce.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Dmitri Mendeleev arranged elements primarily by what property in his 1869 table?",
    "answer": "By atomic weight, while keeping elements with similar chemistry in the same column",
    "choices": [
        "By atomic weight, while keeping elements with similar chemistry in the same column",
        "By alphabetical order of their Latin names, regardless of chemical behavior",
        "By their date of discovery, from the oldest element in column one onwards",
        "By their cost per kilogram, with the most precious metals on the right side",
    ],
    "context": "Mendeleev's 1869 table ordered elements by atomic weight, but he was willing to break that order to keep chemically-similar elements aligned (tellurium and iodine, for example). The modern table orders by atomic NUMBER (proton count), discovered by Henry Moseley in 1913 — which resolved the few cases where atomic weight ordering conflicted with chemical behavior.",
    "_pillar": 2,
})

# --- Noble gases — 2 ---

P2.append({
    "tier": 2,
    "question": "The far right column of the periodic table holds the noble gases — helium, neon, argon, krypton, xenon, radon. What makes these gases 'noble'?",
    "answer": "They rarely react with other elements — their outer electron shells are full",
    "choices": [
        "They rarely react with other elements — their outer electron shells are full",
        "They are the most expensive gases — only royal courts could afford them",
        "They are the heaviest gases — heavier than any metal in solid form",
        "They are the brightest gases — they emit white light when at room temperature",
    ],
    "context": "Noble gases were called 'noble' by analogy with noble metals — aloof, not deigning to react. Helium, neon, argon, krypton, xenon, and radon all have completely full outer electron shells (2 for helium, 8 for the others), making them chemically unreactive. They were discovered late (1894-1898) precisely because they don't form compounds. Neon glows orange-red in sign tubes; argon fills incandescent bulbs.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Helium was first detected by analyzing light from the Sun during a solar eclipse in 1868 — a quarter century before anyone found it on Earth. How was this distant element identified?",
    "answer": "By a yellow spectral line in sunlight not matching any known element on Earth",
    "choices": [
        "By a yellow spectral line in sunlight not matching any known element on Earth",
        "By measuring the Sun's exact total weight against an unknown extra amount",
        "By the way it glowed pale green when photographed from a balloon at altitude",
        "By a chunk that fell to Earth from the Sun in a meteor shower of 1868 AD",
    ],
    "context": "French astronomer Jules Janssen and English astronomer Norman Lockyer independently noticed a new yellow line (587.49 nm) in the spectrum of the August 1868 solar eclipse. Lockyer named the new element helium from the Greek 'helios' (Sun). It wasn't isolated on Earth until 1895 by William Ramsay. Today helium is essential for MRI machines, balloons, and cryogenics.",
    "_pillar": 2,
})

# --- Alkali metals — 2 ---

P2.append({
    "tier": 2,
    "question": "The first column of the periodic table (lithium, sodium, potassium, rubidium, cesium) holds the alkali metals. What dramatic reaction happens when one of these is dropped in water?",
    "answer": "It reacts vigorously, often producing hydrogen gas that can ignite or explode",
    "choices": [
        "It reacts vigorously, often producing hydrogen gas that can ignite or explode",
        "It sinks slowly to the bottom and dissolves into harmless table salt over time",
        "It floats on top and forms a thin shiny film, then nothing else happens at all",
        "It freezes the surrounding water instantly into a solid block of clear ice",
    ],
    "context": "Alkali metals have one electron in their outermost shell, eager to give it up. With water: sodium fizzes, potassium ignites in a lilac flame, rubidium and cesium explode on contact. The reactions produce metal hydroxide (base) and hydrogen gas. The further down the column, the more violent the reaction. These metals are so reactive they're stored under oil to keep air and moisture away.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Sodium on its own ignites in water. Chlorine is a poisonous yellow-green gas. How can their combination (table salt, NaCl) be safe to eat?",
    "answer": "When they bond as ions — both lose their dangerous chemistry, forming stable salt",
    "choices": [
        "When they bond as ions — both lose their dangerous chemistry, forming stable salt",
        "Sodium and chlorine are still dangerous — table salt is just consumed quickly",
        "Salt is mostly clean water — only a small amount of sodium chloride is present",
        "Heat from cooking destroys both elements — leaving only a chemical name behind",
    ],
    "context": "Sodium gives up its single outer electron to chlorine, becoming Na⁺. Chlorine accepts that electron, becoming Cl⁻. Their opposite charges attract, forming the ionic NaCl crystal. The dangerous chemistry of pure sodium (eager to react) and pure chlorine (eager to grab electrons) is satisfied — both ions now have stable noble-gas electron configurations. Compounds can behave radically different from their elements.",
    "_pillar": 2,
})

# --- Halogens — 2 ---

P2.append({
    "tier": 2,
    "question": "The second-from-right column of the periodic table holds the halogens — fluorine, chlorine, bromine, iodine, astatine. What property do they share?",
    "answer": "They all have seven electrons in their outer shell and react eagerly to gain one more",
    "choices": [
        "They all have seven electrons in their outer shell and react eagerly to gain one more",
        "They are all bright metals that conduct electricity better than copper at room temperature",
        "They are all heavy gases that combine quickly to form noble gases like neon",
        "They all have only one electron in their outer shell and lose it during reactions",
    ],
    "context": "Halogens need just one more electron to complete their outer shell, making them highly reactive. Fluorine is the most reactive element on the periodic table; it attacks almost everything. Chlorine was used in pools and as a war gas in WWI. Iodine is essential in human nutrition (thyroid hormones). Bromine smells acrid. Astatine is so radioactive it barely exists.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Iodine is added to most table salt as 'iodized salt.' Why is small amounts of iodine added to common salt?",
    "answer": "To prevent thyroid problems — the body needs iodine to make thyroid hormones",
    "choices": [
        "To prevent thyroid problems — the body needs iodine to make thyroid hormones",
        "To preserve the salt longer on store shelves — and slow down spoilage of crystals",
        "To make salt heavier so packages weigh the same on hot — and cold days alike",
        "To give salt its bright white color — without iodine it would appear gray",
    ],
    "context": "Iodine deficiency causes goiter (swollen thyroid) and can stunt brain development in children. Switzerland began iodizing salt in 1922; the US followed in 1924. The intervention has prevented millions of cases of intellectual disability worldwide and is one of the cheapest public-health success stories. About one teaspoon of iodine over a lifetime is enough.",
    "_pillar": 2,
})

# --- Isotopes (C-14 dating) — 2 ---

P2.append({
    "tier": 2,
    "question": "Atoms of the same element can come in different versions called isotopes. What's the same and what's different between two isotopes?",
    "answer": "Same number of protons, different number of neutrons in the nucleus",
    "choices": [
        "Same number of protons, different number of neutrons in the nucleus",
        "Same number of electrons, different number of protons inside the atom",
        "Same chemical name but completely different chemical reactions with everything",
        "Same color in their solid form but different temperature at which they melt",
    ],
    "context": "Every element is defined by its proton count (atomic number). Isotopes have the same number of protons but different numbers of neutrons. Hydrogen-1 (no neutrons), Hydrogen-2 'deuterium' (one neutron), Hydrogen-3 'tritium' (two neutrons). Most elements have multiple stable isotopes. Some isotopes are radioactive and decay over time — useful as clocks and tracers.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "In 1949 American chemist Willard Libby developed a method to date once-living things up to about 50,000 years old. What isotope did he use?",
    "answer": "Carbon-14 — a radioactive form of carbon with a half-life of about 5,730 years",
    "choices": [
        "Carbon-14 — a radioactive form of carbon with a half-life of about 5,730 years",
        "Uranium-238 — a heavy isotope only useful for dating ancient rocks billions of years old",
        "Lead-206 — used to date the age of metal coins from medieval European mints",
        "Gold-197 — measured in tree rings to date ancient forests from each century",
    ],
    "context": "Carbon-14 is produced in the upper atmosphere by cosmic rays hitting nitrogen. Living things take it in along with normal carbon-12. After death, intake stops and the C-14 decays at a steady rate. Measuring the remaining C-14 fraction tells you when the organism died. Libby won the 1960 Nobel in Chemistry. The method is reliable for 50,000-year-old samples, then becomes too noisy as too little C-14 remains.",
    "_pillar": 2,
})

# --- Bonds (ionic, covalent) — 4 ---

P2.append({
    "tier": 2,
    "question": "Sodium gives its outer electron to chlorine in table salt (NaCl). The two oppositely charged ions then stick together. What's this type of chemical bond called?",
    "answer": "An ionic bond — electrons are transferred and the resulting ions attract by opposite charge",
    "choices": [
        "An ionic bond — electrons are transferred and the resulting ions attract by opposite charge",
        "A covalent bond — electrons are shared evenly between two atoms in equal pairs",
        "A metallic bond — electrons flow freely among many atoms in a metal lattice",
        "A hydrogen bond — water molecules link weakly through their hydrogen and oxygen atoms",
    ],
    "context": "Ionic bonds form when one atom gives up electrons (becoming positive) and another accepts them (becoming negative). The opposite charges attract. Common ionic compounds: NaCl (salt), CaCl₂, MgO. Ionic compounds typically have high melting points, dissolve in water, and conduct electricity when dissolved or molten.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "In water (H₂O), the hydrogen and oxygen atoms SHARE pairs of electrons rather than transferring them outright. What's this type of bond called?",
    "answer": "A covalent bond — atoms share electron pairs to complete their outer shells",
    "choices": [
        "A covalent bond — atoms share electron pairs to complete their outer shells",
        "An ionic bond — one atom takes electrons completely from the other partner",
        "A metallic bond — electrons drift freely through a sea of positive ions",
        "A magnetic bond — atoms align their magnetic fields and lock together",
    ],
    "context": "Covalent bonds are most common in living chemistry. Carbon-hydrogen bonds in fuels and organic molecules, the H-O-H bonds in water, the double bond in CO₂ — all covalent. Sharing electrons lets each atom 'count' the shared pair toward its own outer shell, achieving stability. Covalent compounds usually have lower melting points than ionic ones.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Diamond and graphite (pencil lead) are both made entirely of carbon atoms. Why does diamond cut glass while graphite slides off the page in soft layers?",
    "answer": "Because the carbon atoms are bonded in different patterns — networks versus loose sheets",
    "choices": [
        "Because the carbon atoms are bonded in different patterns — networks versus loose sheets",
        "Because diamond contains hidden iron — and graphite contains hidden lead",
        "Because diamond comes from volcanoes — and graphite from underground rivers",
        "Because graphite has fewer electrons — in each carbon atom than diamond has",
    ],
    "context": "Diamond: each carbon bonded to four neighbors in a rigid 3D tetrahedral lattice — extreme hardness. Graphite: carbon bonded in flat hexagonal sheets, with weak forces between sheets — sheets slide easily, explaining graphite's lubricating and writing properties. Same element, radically different bonding. Buckminsterfullerene (C₆₀, 'buckyballs', 1985) is yet another carbon form.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Why does ice float on liquid water? Most solids sink in their own liquid — but water is special.",
    "answer": "Hydrogen bonds force water molecules into an open lattice when frozen — less dense",
    "choices": [
        "Hydrogen bonds force water molecules into an open lattice when frozen — less dense",
        "Ice traps air bubbles inside — making it lighter than liquid water in every case",
        "Cold makes all solids float — every frozen liquid floats on its warmer form",
        "Ice and water have different chemical formulas — ice is actually carbon-based",
    ],
    "context": "Liquid water molecules are constantly jostling and hydrogen-bonding briefly. When water freezes, the hydrogen bonds lock molecules into a rigid hexagonal lattice with a lot of empty space — ice is about 9% less dense than liquid water. This anomaly is critical for life on Earth: ice forms a floating insulating layer on lakes and oceans, letting aquatic life survive winter underneath.",
    "_pillar": 2,
})

# --- pH scale — 2 ---

P2.append({
    "tier": 2,
    "question": "The pH scale, invented by Danish chemist S. P. L. Sørensen in 1909, measures how acidic or basic a solution is. What does a pH of 7 mean?",
    "answer": "The solution is neutral — like pure water at room temperature",
    "choices": [
        "The solution is neutral — like pure water at room temperature",
        "The solution is highly acidic — like stomach acid in human digestion",
        "The solution is highly basic — like household bleach or strong lye solutions",
        "The solution is too dilute to test — readings start only at pH 10 and above",
    ],
    "context": "pH scale runs 0-14. 0-6 is acidic, 7 is neutral, 8-14 is basic. Each step is a factor of 10. Stomach acid: pH ~1.5. Lemon juice: ~2. Coffee: ~5. Pure water: 7. Sea water: ~8. Baking soda: ~9. Bleach: ~13. Lye: 14. The 'p' in pH likely stands for 'potenz' (power); H stands for hydrogen (it measures hydrogen ion concentration).",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "When you mix an acid (like vinegar) with a base (like baking soda), bubbling happens and the solution becomes more neutral. What's this called?",
    "answer": "A neutralization reaction — acid plus base makes water plus a salt",
    "choices": [
        "A neutralization reaction — acid plus base makes water plus a salt",
        "A combustion reaction — vinegar and baking soda burn each other at room temperature",
        "An electromagnetic reaction — the two solutions create a small electric current together",
        "An evaporation reaction — both the acid and the base disappear into water vapor",
    ],
    "context": "Acid (H⁺) + base (OH⁻) → water + salt. The bubbling in vinegar + baking soda is CO₂ gas escaping (acetic acid + sodium bicarbonate → water + sodium acetate + carbon dioxide). The same chemistry powers fire extinguishers, antacids (for stomach acid), and the volcano demonstration in elementary schools.",
    "_pillar": 2,
})

# --- Balanced equations / combustion — 4 ---

P2.append({
    "tier": 2,
    "question": "Chemical equations must be balanced — the same number of each atom must appear on both sides. Why does this rule exist?",
    "answer": "Atoms can't be created or destroyed in a chemical reaction — only rearranged",
    "choices": [
        "Atoms can't be created or destroyed in a chemical reaction — only rearranged",
        "Equations are balanced for visual neatness — the chemistry would also work unbalanced",
        "Balanced equations are required only in advanced research papers — not in classrooms",
        "Only positive numbers fit chemical equations — balancing keeps every count positive",
    ],
    "context": "Conservation of mass: Antoine Lavoisier showed in the 1770s-80s that the total mass before and after a reaction is constant. Atoms simply rearrange. Methane burning: CH₄ + 2 O₂ → CO₂ + 2 H₂O. Left side: 1 C, 4 H, 4 O. Right side: 1 C, 4 H, 4 O. Balanced. Chemistry obeys atom-counting.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "A candle burns in oxygen and produces carbon dioxide, water vapor, and heat. The candle gets shorter as it burns. What happens to the mass of the wax that disappeared?",
    "answer": "It became CO₂ and water vapor that drifted away as gases — total mass is unchanged",
    "choices": [
        "It became CO₂ and water vapor that drifted away as gases — total mass is unchanged",
        "It was destroyed by the flame — wax loses mass when it burns into nothing at all",
        "It evaporated into pure carbon — leaving black soot floating up into the air above",
        "It was converted to energy and heat — weighing nothing afterwards in the room",
    ],
    "context": "Lavoisier's conservation of mass: weigh the candle plus the air before, weigh the gases and any leftover candle after, and they're equal. The wax molecules (long hydrocarbon chains) combine with oxygen to form CO₂ and H₂O, which drift up as the candle's mass leaves as gas. A burning candle in a sealed jar shows this — once the oxygen is used up, the candle goes out.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Combustion (burning) requires three things, sometimes called the 'fire triangle.' What are the three?",
    "answer": "Fuel, oxygen, and heat — these three together start any combustion reaction",
    "choices": [
        "Fuel, oxygen, and heat — these three together start any combustion reaction",
        "Wood, water, and wind — the three traditional firefighting tools used worldwide",
        "Charcoal, salt, and sand — the three components of any safe campfire setup",
        "Iron, copper, and sulfur — the three metals that catch fire most often in air",
    ],
    "context": "Fire triangle: remove any side and the fire goes out. Water cools (removes heat). Smothering (a blanket on a small fire) cuts off oxygen. Removing nearby fuel stops the spread. The fourth element sometimes added is the chemical chain reaction itself — modern dry chemical extinguishers work partly by interrupting the radical chain reactions inside the flame.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Methane (natural gas, CH₄) burns in oxygen to produce carbon dioxide and water. What's the balanced equation for this reaction?",
    "answer": "CH₄ + 2 O₂ → CO₂ + 2 H₂O",
    "choices": [
        "CH₄ + 2 O₂ → CO₂ + 2 H₂O",
        "CH₄ + O₂ → CO₂ + H₂O",
        "CH₄ + 3 O₂ → 2 CO₂ + 4 H₂O",
        "2 CH₄ + O₂ → 2 CO₂ + H₂O",
    ],
    "context": "Balanced methane combustion: 1 carbon on each side, 4 hydrogens on each side (4 in CH₄, and 2 × 2 = 4 in H₂O), 4 oxygens on each side (2 × 2 = 4 in 2 O₂, and 2 + 2 = 4 in CO₂ + 2 H₂O). Natural-gas appliances rely on this reaction. Incomplete combustion (not enough oxygen) makes carbon monoxide (CO) — odorless and deadly.",
    "_pillar": 2,
})

# --- Lavoisier — 4 ---

P2.append({
    "tier": 2,
    "question": "In the 1770s and 80s, French chemist Antoine Lavoisier overturned the dominant 'phlogiston' theory of combustion. What did he show was really happening when things burn?",
    "answer": "They combine with oxygen from the air — gaining mass, not losing 'phlogiston'",
    "choices": [
        "They combine with oxygen from the air — gaining mass, not losing 'phlogiston'",
        "They release ancient stored fire from inside — called phlogiston, into the room",
        "They give off magnetism — which used to be called fire by older chemists",
        "They expel small amounts of gold — which is why metals tarnish over time",
    ],
    "context": "Phlogiston theory held that combustible materials contained a substance called 'phlogiston' released during burning. Lavoisier weighed reactions carefully and showed metals GAINED mass when they rusted — they had absorbed oxygen, not released phlogiston. His careful weighing also established conservation of mass. He named oxygen and hydrogen and is widely considered the founder of modern chemistry.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Antoine Lavoisier, called the father of modern chemistry, met a sudden end during the French Revolution. What happened to him in 1794?",
    "answer": "He was guillotined during the Reign of Terror — France 'had no need of geniuses'",
    "choices": [
        "He was guillotined during the Reign of Terror — France 'had no need of geniuses'",
        "He died peacefully — in retirement on his country estate writing memoirs",
        "He was lost at sea on an — expedition collecting specimens off the coast of Brazil",
        "He drowned crossing the English Channel fleeing to safety — in nearby England",
    ],
    "context": "Lavoisier was a tax collector ('Ferme Générale') as well as a scientist — and tax collectors were hated. He was guillotined on May 8, 1794. Mathematician Joseph-Louis Lagrange said: 'It took them only an instant to cut off that head, and a hundred years will not suffice to produce another like it.' Lavoisier was 50. His 1789 Traité élémentaire de chimie had founded modern chemistry only five years before.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Antoine Lavoisier and his wife Marie-Anne worked as a scientific team. What unusual role did Marie-Anne play in his chemistry?",
    "answer": "She kept careful experimental records, translated foreign work, and illustrated his books",
    "choices": [
        "She kept careful experimental records, translated foreign work, and illustrated his books",
        "She secretly took credit for everything by publishing under her husband's name",
        "She refused to enter his lab, preferring her separate work on French royal embroidery",
        "She managed the family farm and never engaged with his scientific work at all",
    ],
    "context": "Marie-Anne Paulze Lavoisier (1758-1836) translated Joseph Priestley's English chemistry into French for her husband, drew the technical figures in his Traité (some still reproduced in modern textbooks), and ran salon discussions of his ideas. After Antoine's execution, she fought for years to preserve and publish his unfinished work. She is one of the first women in the historical record as a recognized scientific collaborator.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Lavoisier discovered that water (long considered an element) is actually a compound of two simpler elements. What two elements is water made of?",
    "answer": "Hydrogen and oxygen — Lavoisier named both elements in the 1780s",
    "choices": [
        "Hydrogen and oxygen — Lavoisier named both elements in the 1780s",
        "Carbon and hydrogen — water shares its composition with sugar in this way",
        "Nitrogen and oxygen — the same two elements that make up most of the atmosphere",
        "Salt and ice — a frozen mixture of these gives liquid water its essential parts",
    ],
    "context": "Henry Cavendish discovered (1766-1781) that mixing hydrogen and oxygen and igniting them produced water. Lavoisier confirmed it and gave the elements their modern names: 'hydrogen' (Greek 'water-former') and 'oxygen' (Greek 'acid-former' — a small misnomer; not all acids contain oxygen). The discovery that water is a compound made the four-element theory (earth/air/fire/water) untenable.",
    "_pillar": 2,
})

# --- Kekulé (benzene ring dream) — 3 ---

P2.append({
    "tier": 2,
    "question": "In 1865 German chemist August Kekulé reported a dream that inspired him to solve a major chemistry puzzle. What did he see in the dream?",
    "answer": "A snake biting its own tail — leading him to propose the ring structure of benzene",
    "choices": [
        "A snake biting its own tail — leading him to propose the ring structure of benzene",
        "A row of soldiers marching in line — leading him to propose long carbon chains",
        "A flock of birds in formation — leading him to propose triangle structures of molecules",
        "A burning candle in a forest — leading him to propose how combustion works at all",
    ],
    "context": "August Kekulé had struggled with benzene (C₆H₆) — its chemistry didn't match any obvious chain. He reported dreaming of an ouroboros (snake eating its tail) and waking to propose benzene as a six-carbon ring with alternating single and double bonds. Some historians question whether the dream story is embellished; the ring structure was correct. Benzene's ring is foundational to all of aromatic chemistry.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Once August Kekulé proposed benzene's ring structure in 1865, organic chemistry exploded. Why was the ring structure so important?",
    "answer": "Many molecules — sugars, dyes, drugs, plastics — are built around aromatic rings",
    "choices": [
        "Many molecules — sugars, dyes, drugs, plastics — are built around aromatic rings",
        "Rings were the only structures allowed in organic molecules — chains were banned",
        "The ring was made of pure iron — every benzene molecule contains hidden metal",
        "Rings are the simplest possible molecules — anything else is too complex to exist",
    ],
    "context": "Benzene's six-carbon aromatic ring turned out to be a central scaffold in chemistry. Aspirin, TNT, polystyrene, paracetamol, vanillin, the dyes that founded the German chemical industry — all contain aromatic rings. The 1860s discovery of ring structure launched modern organic chemistry as an industrial discipline.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Benzene (C₆H₆) is one of the building blocks of organic chemistry. How are its six carbon atoms arranged in space?",
    "answer": "In a flat hexagonal ring, with alternating single and double bonds between carbons",
    "choices": [
        "In a flat hexagonal ring, with alternating single and double bonds between carbons",
        "In a straight chain six carbons long, with hydrogen atoms hanging off each one",
        "In a tightly wound ball, like a tiny atomic version of a soccer ball shape",
        "In a long cone shape, with the carbons stacked one on top of the next vertically",
    ],
    "context": "Kekulé's 1865 ring structure with alternating double bonds was later refined: benzene's electrons are actually 'delocalized' across the whole ring, giving extra stability ('aromatic'). The classic drawing of a hexagon with a circle inside represents this. The ring's stability makes benzene-based compounds last well — and made aromatic-ring synthesis the foundation of the modern pharmaceutical industry.",
    "_pillar": 2,
})

# --- P2 grab-bag: catalysts, states, solubility — 7 ---

P2.append({
    "tier": 2,
    "question": "A chemical that speeds up a reaction without being used up itself is called a catalyst. Catalytic converters in modern cars contain platinum and palladium. What do they help do?",
    "answer": "Convert toxic exhaust gases into less harmful CO₂, water, and nitrogen",
    "choices": [
        "Convert toxic exhaust gases into less harmful CO₂, water, and nitrogen",
        "Convert gasoline into more efficient fuel as the engine runs each minute",
        "Convert engine heat back into electricity for the car's battery in motion",
        "Convert engine sound into silence, working only on the noisiest exhaust gases",
    ],
    "context": "Catalytic converters (introduced in US cars in 1975) reduce three big pollutants: carbon monoxide (CO) is oxidized to CO₂; unburned hydrocarbons are oxidized to CO₂ and water; nitrogen oxides (NO, NO₂) are reduced to N₂. Platinum, palladium, and rhodium serve as catalysts. The technology cut urban air pollution dramatically — one of the underappreciated public-health wins of the late 20th century.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Water can exist as solid (ice), liquid, or gas (water vapor). What's it called when ice goes directly to vapor without first melting to liquid?",
    "answer": "Sublimation — solid to gas directly, skipping the liquid phase",
    "choices": [
        "Sublimation — solid to gas directly, skipping the liquid phase",
        "Evaporation — but happening more slowly than usual without any liquid",
        "Condensation — solid pulls vapor out of the air on cold dry days",
        "Crystallization — forming new ice crystals from gaseous water in the air",
    ],
    "context": "Sublimation is what makes dry ice (frozen CO₂) 'smoke' as it warms — it goes straight from solid to gas at room temperature. Snow on a dry, windy day can slowly sublimate. Mothballs (naphthalene) sublimate, giving them their smell. Freeze-drying coffee uses sublimation under vacuum.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Why does sugar dissolve in water but vegetable oil does not?",
    "answer": "Water dissolves polar substances; oil is nonpolar, so it doesn't mix with water",
    "choices": [
        "Water dissolves polar substances; oil is nonpolar, so it doesn't mix with water",
        "Sugar is light enough to float in water; oil is too dense to mix with water",
        "Sugar is solid and oil is liquid; only solids dissolve in liquids by general rule",
        "Sugar contains hidden alcohol; oil contains hidden iron, which water cannot dissolve",
    ],
    "context": "'Like dissolves like.' Water (H₂O) is a polar molecule — its oxygen end is slightly negative, its hydrogen ends slightly positive. Sugar (sucrose) has many polar -OH groups and dissolves easily. Oil molecules are long nonpolar hydrocarbon chains — they have no charged sites for water to attach to. Soaps work as bridges: one end is polar (binds water), the other nonpolar (binds oil).",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "When you open a can of soda, bubbles fizz up. What gas is escaping from the liquid?",
    "answer": "Carbon dioxide — dissolved under pressure in the sealed can, escaping when opened",
    "choices": [
        "Carbon dioxide — dissolved under pressure in the sealed can, escaping when opened",
        "Oxygen — added to drinks to make them more refreshing on hot summer days",
        "Hydrogen — fizzy drinks naturally produce hydrogen at room temperature inside cans",
        "Helium — used to give sodas their light feel against the tongue when sipped",
    ],
    "context": "Carbonated beverages are saturated with CO₂ under pressure. When you open the can, the pressure drops; CO₂ comes out of solution as bubbles. Joseph Priestley invented carbonated water in 1767. Henry's law (1803) says the amount of gas dissolved in a liquid is proportional to the gas's pressure above the liquid. Warm soda fizzes less because gas is less soluble at higher temperatures.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Marie Curie and her husband Pierre Curie spent years processing tons of pitchblende (uranium ore) to isolate just tiny amounts of two new elements. What was special about both new elements?",
    "answer": "They were radioactive — emitting energetic particles and rays from their nuclei",
    "choices": [
        "They were radioactive — emitting energetic particles and rays from their nuclei",
        "They were magnetic — attracting iron filings from rocks in any direction",
        "They were edible — used in tiny amounts as medicines for stomach problems",
        "They were liquid at room temperature — flowing like mercury in their pure form",
    ],
    "context": "Marie Curie coined the term 'radioactivity.' She and Pierre isolated polonium (1898, named after her native Poland) and radium (1898). Both elements glowed faintly in the dark from their radiation. Marie carried test tubes of radium in her pockets, not knowing the danger. She died of aplastic anemia in 1934, likely from radiation exposure. Her lab notebooks are still radioactive and stored in lead-lined boxes.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "About 78% of Earth's atmosphere is nitrogen gas (N₂). Yet plants need nitrogen badly and can't use the N₂ in the air directly. Why not?",
    "answer": "The triple bond in N₂ is extremely strong — special bacteria or industrial methods are needed",
    "choices": [
        "The triple bond in N₂ is extremely strong — special bacteria or industrial methods are needed",
        "Atmospheric nitrogen sits too high up — plants only reach the lowest layer of air",
        "Plants have evolved to ignore nitrogen — and use only carbon dioxide for all their needs",
        "Plant roots are too small to capture nitrogen — only larger animals like cattle can use it",
    ],
    "context": "The N≡N triple bond is one of the strongest in chemistry — 945 kJ/mol. Most life can't break it. Nitrogen-fixing bacteria in legume root nodules (and lightning's high-temperature reactions) convert N₂ to usable ammonia (NH₃). The Haber-Bosch process (Germany, 1910) industrially fixes nitrogen — fertilizers from this process now feed about half of humanity.",
    "_pillar": 2,
})

P2.append({
    "tier": 2,
    "question": "Henry Cavendish in 1766 isolated a colorless gas lighter than air that burned with a pale blue flame. He called it 'inflammable air.' What gas was he describing?",
    "answer": "Hydrogen — lightest of all elements, burning to make water",
    "choices": [
        "Hydrogen — lightest of all elements, burning to make water",
        "Helium — used to fill modern toy balloons that float up",
        "Methane — released from swamps and the digestion of cattle in fields",
        "Ozone — found high in the atmosphere shielding Earth from ultraviolet rays",
    ],
    "context": "Cavendish produced hydrogen by reacting acids with metals. He showed it burns in oxygen to produce water — a discovery that helped Lavoisier prove water was not an element. Lavoisier named the gas 'hydrogène' (water-former). Today hydrogen is used in rocket fuel, ammonia synthesis, and is being explored as a potential clean fuel. About 75% of the visible mass of the universe is hydrogen.",
    "_pillar": 2,
})

# Sanity check
assert len(P2) == 40, f"P2 expected 40, got {len(P2)}"


# ===========================================================================
# P3 BIOLOGY (50)
# ===========================================================================

# --- Cell theory (Schwann + Schleiden + Virchow) — 4 ---

P3.append({
    "tier": 2,
    "question": "In the 1830s German scientists Matthias Schleiden (a botanist) and Theodor Schwann (a zoologist) brought together what's now called cell theory. What was their main claim?",
    "answer": "All plants and all animals are made up of tiny units called cells",
    "choices": [
        "All plants and all animals are made up of tiny units called cells",
        "Only plants are made of cells; animals are made of solid flowing fluids",
        "Only animals are made of cells; plants are made of woven plant fibers alone",
        "Cells exist only in microscopic creatures; bigger animals are smooth tissue",
    ],
    "context": "Robert Hooke first saw and named 'cells' in cork (1665), comparing them to monk's rooms. Schleiden (1838) extended cells to plants generally; Schwann (1839) to animals. The third pillar (cells come only from cells) was added by Rudolf Virchow in 1855 with the Latin motto 'omnis cellula e cellula' — laying microbial-disease theory's groundwork.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "In 1855 German pathologist Rudolf Virchow completed cell theory with a third claim that overturned the old idea of 'spontaneous generation.' What did he add in Latin: 'omnis cellula e cellula'?",
    "answer": "Every cell comes from another cell — life always begets life",
    "choices": [
        "Every cell comes from another cell — life always begets life",
        "Every cell can form from non-living mud given enough warmth — and time",
        "Every cell contains a tiny new mind — once it grows past a certain size",
        "Every cell sleeps for thousands of — years before opening for the first time",
    ],
    "context": "Spontaneous generation was the ancient idea that life arises freely from non-life: maggots from rotting meat, mice from dirty rags. Virchow's 1855 'omnis cellula e cellula' completed cell theory: cells reproduce. Combined with Pasteur's later swan-neck flask experiments, the doctrine of spontaneous generation was put to rest by the 1860s.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "The first person known to have seen and named 'cells' was English scientist Robert Hooke in 1665. What was he looking at through his microscope when he made the discovery?",
    "answer": "A thin slice of cork — the dead plant-cell walls reminded him of monk's rooms",
    "choices": [
        "A thin slice of cork — the dead plant-cell walls reminded him of monk's rooms",
        "A drop of pond water — full of swimming bacteria and protists",
        "A piece of human skin — peeled off his own finger for the experiment",
        "A drop of his own blood — viewed in a series of laboratory microscope tests",
    ],
    "context": "Hooke's 1665 *Micrographia* described and illustrated his cork observation: tiny boxes he called 'cells' (Latin 'cella,' a small room) by analogy with monk's cells. The boxes he saw were actually just the cell walls — the cork tissue was dead. Living cells with their internal structures wouldn't be seen clearly until Antonie van Leeuwenhoek's improved microscopes a few years later.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Antonie van Leeuwenhoek, a Dutch fabric merchant in the 1670s, ground his own lenses and built microscopes more powerful than his peers. What did he discover that no one had ever seen?",
    "answer": "Single-celled microscopic life he called 'animalcules' — bacteria and protists",
    "choices": [
        "Single-celled microscopic life he called 'animalcules' — bacteria and protists",
        "The smallest atoms of every element — two centuries before Dalton's work",
        "The structure of DNA — three centuries before Watson and Crick found it",
        "The pattern of cosmic background radiation — in a small dish of pond water",
    ],
    "context": "Van Leeuwenhoek's hand-ground lenses reached over 250x magnification — far beyond what compound microscopes of the era could match. He saw bacteria in tooth scrapings, sperm cells, blood cells, and protists swimming in pond water. He sent meticulous letters to the Royal Society describing his 'animalcules' — opening the entire microbial world to science.",
    "_pillar": 3,
})

# --- Prokaryotes vs eukaryotes — 2 ---

P3.append({
    "tier": 2,
    "question": "Cells come in two big types. The simpler kind (bacteria, archaea) lack a nucleus. The complex kind (plants, animals, fungi) have a nucleus. What are the two types called?",
    "answer": "Prokaryotes (no nucleus) and eukaryotes (true nucleus) — the two basic cell types",
    "choices": [
        "Prokaryotes (no nucleus) and eukaryotes (true nucleus) — the two basic cell types",
        "Microbes (no nucleus) and macrobes (true nucleus) — older terms still in use today",
        "Singletons (no nucleus) and multipliers (true nucleus) — about cell division speed",
        "Animals (no nucleus) and plants (true nucleus) — referring only to large organisms",
    ],
    "context": "Prokaryote ('before nucleus') and eukaryote ('true nucleus') were the two basic cell types proposed by Edouard Chatton in 1925 and entrenched by Roger Stanier in the 1960s. Prokaryotes (bacteria, archaea) dominate by sheer count and biomass; eukaryotes are larger, more complex, and include all multicellular life. Eukaryotes arose probably 1.5-2 billion years ago.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "A bacterial cell (prokaryote) is typically how much smaller than a plant or animal cell (eukaryote)?",
    "answer": "About 10 to 100 times smaller in diameter — and 1,000 to a million times smaller in volume",
    "choices": [
        "About 10 to 100 times smaller in diameter — and 1,000 to a million times smaller in volume",
        "About the same size — only the internal structure differs between the two types",
        "Twice as large — bacteria are bigger but simpler than plant or animal cells",
        "Ten thousand times larger — bacteria are some of the biggest cells in nature",
    ],
    "context": "Typical bacterial cell: 1-2 micrometers. Typical animal/plant cell: 10-100 micrometers. The volume scales as the cube of the diameter, so the difference in volume is huge. Eukaryotes have many internal compartments (organelles, nucleus, ER, Golgi) that prokaryotes lack — and they need the extra room.",
    "_pillar": 3,
})

# --- Mitochondria + Lynn Margulis endosymbiotic theory — 3 ---

P3.append({
    "tier": 2,
    "question": "Mitochondria — the 'powerhouses' of plant and animal cells — have their own DNA and divide independently. In 1967 Lynn Margulis proposed an explanation. What was it?",
    "answer": "Mitochondria descend from ancient bacteria — engulfed by larger cells long ago",
    "choices": [
        "Mitochondria descend from ancient bacteria — engulfed by larger cells long ago",
        "Mitochondria are tiny computers — built by the cell to run chemical processes",
        "Mitochondria are broken-off nucleus pieces — they later gained new functions",
        "Mitochondria are old virus remnants — that infected our deepest ancestor",
    ],
    "context": "Lynn Margulis's 1967 paper 'On the Origin of Mitosing Cells' proposed endosymbiotic theory: mitochondria and chloroplasts were once free-living bacteria that took up residence inside larger cells, becoming permanent symbiotic partners. The idea was rejected by mainstream biology for years; Margulis was told her work was 'crap.' DNA sequencing in the 1980s confirmed her — both organelles' DNA matches bacterial DNA.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Plant cells contain another organelle that, like mitochondria, has its own DNA and ribosomes. What organelle, and what does it do for the plant?",
    "answer": "Chloroplasts — they capture sunlight and use it to make sugars",
    "choices": [
        "Chloroplasts — they capture sunlight and use it to make sugars",
        "Lysosomes — they break down old cell parts and dispose of cellular trash",
        "Centrioles — they organize the structures cells use to divide their nuclei",
        "Vacuoles — they store water and pressure the cell to keep it firm and rigid",
    ],
    "context": "Like mitochondria, chloroplasts descend from once-free-living bacteria — in this case, cyanobacteria-like organisms — engulfed by an ancestral cell roughly 1.5 billion years ago (Margulis's endosymbiotic theory again). Their internal membranes hold the chlorophyll molecules that absorb light, driving photosynthesis. Plant cells typically contain dozens to hundreds of chloroplasts.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "When Lynn Margulis first published her endosymbiotic theory in 1967, mainstream biology rejected it for years. What kind of evidence finally convinced most biologists she was right?",
    "answer": "DNA sequencing in the 1980s showed mitochondrial DNA looks like bacterial DNA",
    "choices": [
        "DNA sequencing in the 1980s showed mitochondrial DNA looks like bacterial DNA",
        "A new theoretical proof in pure mathematics showed the theory must be correct",
        "Margulis herself bred mice that had no mitochondria, proving her case in lab work",
        "Photographs taken in 1985 captured the moment a bacterium became a mitochondrion",
    ],
    "context": "Margulis's 1967 paper was rejected by about 15 journals before being published. Critics found the idea bizarre. But when DNA sequencing matured, mitochondrial and chloroplast DNA was found to closely resemble bacterial DNA — same circular shape, similar genes, prokaryote-style ribosomes. The evidence vindicated Margulis. She remained an outsider on many topics throughout her career, dying in 2011.",
    "_pillar": 3,
})

# --- Mendel + Punnett squares + dominant/recessive — 5 ---

P3.append({
    "tier": 2,
    "question": "Austrian monk Gregor Mendel grew about 28,000 pea plants over eight years in his Brno monastery garden, tracking seven traits across generations. What general rule did he find?",
    "answer": "Traits come in pairs; one can mask the other (dominant/recessive); both are still passed on",
    "choices": [
        "Traits come in pairs; one can mask the other (dominant/recessive); both are still passed on",
        "Children always look like the parent they spend the most time with after birth",
        "Traits blend together so two pure parents always produce mixed offspring later",
        "Traits change randomly each generation with no inherited pattern at all",
    ],
    "context": "Mendel's experiments in the 1860s established the foundation of genetics. He chose peas because they have many easy-to-track traits and can self-pollinate. His 1866 paper laid out dominant/recessive traits and statistical ratios — work the scientific world ignored for 34 years. Rediscovered around 1900 by Hugo de Vries, Carl Correns, and Erich von Tschermak working independently.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "A 'Punnett square' is a simple grid biology students use to predict offspring traits. Who developed it, and what does it show?",
    "answer": "Reginald Punnett (around 1905) — it shows all combinations of parent alleles in offspring",
    "choices": [
        "Reginald Punnett (around 1905) — it shows all combinations of parent alleles in offspring",
        "Gregor Mendel himself — he invented it for his original pea plant experiments",
        "Charles Darwin — he used it to track survival rates in his evolution research",
        "Marie Curie — she designed it to track which children inherited her medical condition",
    ],
    "context": "Punnett's square is a teaching tool: cross two parents, list each parent's alleles along the edges of a grid, and the cells show possible offspring combinations. Reginald Punnett (1875-1967) worked at Cambridge with William Bateson. They coined the word 'genetics' in 1905. Punnett squares clearly illustrate Mendelian inheritance, dominant/recessive patterns, and probability ratios for kids.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "If a person has two genes for eye color (one from each parent) and brown is dominant over blue, what does the child of two brown-eyed parents possibly look like?",
    "answer": "Brown-eyed most likely — but could be blue if both parents carry a hidden blue gene",
    "choices": [
        "Brown-eyed most likely — but could be blue if both parents carry a hidden blue gene",
        "Brown-eyed always — two brown parents can never have a blue-eyed child",
        "Blue-eyed always — recessive genes win when both parents share traits",
        "Green-eyed always — combining two browns produces a third color in any pairing",
    ],
    "context": "Eye color is more complex than a simple two-allele model in real biology — multiple genes are involved. But for a single-gene Mendelian trait with brown (B) dominant over blue (b): two carrier parents (Bb × Bb) have a 1/4 chance of producing a blue-eyed (bb) child. The two dominant alleles in the parents mask the recessive ones — but the recessive alleles can pair up in the next generation.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "When Gregor Mendel submitted his 1866 paper on pea plants to a respected journal, what happened?",
    "answer": "It was published but mostly ignored — rediscovered only 34 years later",
    "choices": [
        "It was published but mostly ignored — rediscovered only 34 years later",
        "It was rejected as too radical — and Mendel was banned from the journal forever",
        "It was reprinted — in over 20 languages within a year of original publication",
        "It won the Nobel Prize — in Medicine despite the prize not existing then yet",
    ],
    "context": "Mendel's paper appeared in the Proceedings of the Brünn Natural History Society — read by few, cited by fewer. He sent reprints to leading biologists, including Charles Darwin (who reportedly never opened the pages). Mendel later became abbot of his monastery and stopped doing research. He died in 1884. His work was rediscovered in 1900 by Hugo de Vries, Carl Correns, and Erich von Tschermak working independently.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "In January 1900 three European botanists — Hugo de Vries (Netherlands), Carl Correns (Germany), and Erich von Tschermak (Austria) — independently rediscovered and confirmed work done decades earlier. Whose work were they rediscovering?",
    "answer": "Gregor Mendel's 1866 pea-plant inheritance experiments",
    "choices": [
        "Gregor Mendel's 1866 pea-plant inheritance experiments",
        "Charles Darwin's notebooks from his Beagle voyage to the Galápagos in 1835",
        "Louis Pasteur's swan-neck flask experiments from the 1860s",
        "Alfred Russel Wallace's island-biogeography survey of Malaysian forest",
    ],
    "context": "All three botanists came to similar laws of inheritance — and all found that Mendel had reported the same results 34 years earlier. They credited Mendel, founding modern genetics. The credit-giving was unusual; many scientists in their position would have downplayed Mendel's priority. De Vries had also independently developed mutation theory.",
    "_pillar": 3,
})

# --- Photosynthesis equation — 3 ---

P3.append({
    "tier": 2,
    "question": "Plants absorb light energy from the Sun and use it to make food. What's the basic chemical equation for photosynthesis?",
    "answer": "6 CO₂ + 6 H₂O + light → C₆H₁₂O₆ (glucose) + 6 O₂",
    "choices": [
        "6 CO₂ + 6 H₂O + light → C₆H₁₂O₆ (glucose) + 6 O₂",
        "C₆H₁₂O₆ + 6 O₂ + light → 6 CO₂ + 6 H₂O",
        "6 H₂O + light → 6 O₂ + 6 hydrogen gas plus some heat",
        "CO₂ + H₂O → C₂H₂O₂ + chlorophyll under green sunlight only",
    ],
    "context": "Photosynthesis: six carbon-dioxide molecules + six water molecules + light → one glucose sugar + six oxygen gas. The light is absorbed by chlorophyll inside chloroplasts. The oxygen we breathe is a 'waste product' of this reaction. The reverse reaction is respiration: glucose + oxygen → CO₂ + water + energy (what your mitochondria do all day).",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "All the oxygen in Earth's atmosphere today comes from photosynthesis. Before about 2.4 billion years ago, Earth's atmosphere had almost no free oxygen. What event changed this?",
    "answer": "The 'Great Oxygenation Event' — cyanobacteria evolved photosynthesis and filled the atmosphere",
    "choices": [
        "The 'Great Oxygenation Event' — cyanobacteria evolved photosynthesis and filled the atmosphere",
        "A massive comet impact added oxygen — to Earth's atmosphere all at once",
        "Volcanic eruptions released oxygen trapped — in rocks from Earth's molten interior",
        "Aliens visited Earth — and adjusted the atmosphere for the planet to host life",
    ],
    "context": "The Great Oxygenation Event (~2.4 billion years ago) was caused by photosynthesizing cyanobacteria — the first organisms to release oxygen as a waste product. Most life at the time was anaerobic; the oxygen was toxic to many of them — one of history's largest mass extinctions. The oxygen-rich atmosphere then enabled the evolution of larger, more energy-hungry organisms — eventually including all multicellular animals.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Chlorophyll is the molecule plants use to absorb sunlight. It absorbs red and blue light strongly. What color does it reflect, giving plants their characteristic color?",
    "answer": "Green — chlorophyll reflects the green wavelengths of sunlight it cannot use as efficiently",
    "choices": [
        "Green — chlorophyll reflects the green wavelengths of sunlight it cannot use as efficiently",
        "Red — chlorophyll only absorbs the green and blue wavelengths in sunlight",
        "Blue — chlorophyll reflects mostly blue from the daytime sky in summer",
        "White — chlorophyll reflects all visible wavelengths equally year-round",
    ],
    "context": "Plants look green because chlorophyll absorbs red and blue light from the Sun and reflects green light back to your eyes. Why? Not perfectly known — green absorption would seem more energy-efficient, and biologists debate the evolutionary path. In fall, chlorophyll breaks down in leaves of deciduous trees, revealing the carotenoid and anthocyanin pigments underneath (yellow, orange, red).",
    "_pillar": 3,
})

# --- Darwin (HMS Beagle 1831-36, Origin 1859, finches) + Wallace — 6 ---

P3.append({
    "tier": 2,
    "question": "From 1831 to 1836 young naturalist Charles Darwin sailed around the world on HMS Beagle. What did the journey help him later develop?",
    "answer": "His theory of evolution by natural selection",
    "choices": [
        "His theory of evolution by natural selection",
        "His theory of how Earth's continents fit together like a puzzle",
        "His theory of disease caused by tiny invisible germs in water and food",
        "His theory of gravity holding planets in their orbits around the Sun",
    ],
    "context": "Darwin was 22 when the Beagle sailed in 1831. He spent five years collecting specimens and observations in South America, the Galápagos Islands, Australia, and elsewhere. The patterns he saw — variation within species, adaptation to local environments, fossil sequences — became the basis of his theory, published 23 years later in *On the Origin of Species* (1859).",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "On the Galápagos Islands in 1835, Darwin noticed that finches on different islands had different beak shapes — thin for insects, thick for seeds. What did he eventually realize?",
    "answer": "Each beak shape was adapted to local food — populations had changed over generations",
    "choices": [
        "Each beak shape was adapted to local food — populations had changed over generations",
        "Each island had received finches from a different continent — in past centuries",
        "Each beak shape changed during the bird's individual lifetime — by stretching",
        "Each finch chose its preferred beak — shape consciously when it was born",
    ],
    "context": "Darwin's Galápagos finches (about 15 species) are now textbook examples of adaptive radiation: a single ancestral species spreading across new habitats and diverging as different populations adapted to different niches. Darwin himself didn't make much of the finches initially — ornithologist John Gould helped him recognize their importance after the return. Peter and Rosemary Grant tracked these finches in the 20th century, showing evolution happening within their lifetimes.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "In 1859 Charles Darwin published *On the Origin of Species*, laying out his theory of evolution. What's the basic mechanism Darwin proposed?",
    "answer": "Natural selection — heritable variation + differential reproduction → species change over time",
    "choices": [
        "Natural selection — heritable variation + differential reproduction → species change over time",
        "Selective breeding by humans — Darwin claimed all wild species were created by farmers",
        "Inheritance of traits acquired in life — giraffes stretch their necks and pass that on",
        "Acts of will — every species changed itself by deciding to look a certain way",
    ],
    "context": "Darwin's three premises: (1) Individuals vary. (2) Variations are heritable. (3) More offspring are born than can survive. From these: traits helping survival/reproduction spread; others fade. The result over time is what Darwin called 'descent with modification.' He carefully avoided the word 'evolution' for years — it implied progress; selection is just differential reproduction.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Darwin had sat on his theory of evolution for ~20 years when in 1858 he received a letter from another naturalist in the Malay Archipelago describing almost the same theory. Who was he?",
    "answer": "Alfred Russel Wallace — sending his independent version of natural selection from Indonesia",
    "choices": [
        "Alfred Russel Wallace — sending his independent version of natural selection from Indonesia",
        "Louis Pasteur — sending his work on germ theory from Paris",
        "Gregor Mendel — sending his work on pea plant inheritance from Brno",
        "Thomas Huxley — sending his work on human anatomy from London",
    ],
    "context": "Alfred Russel Wallace sent his 'Ternate Paper' to Darwin in 1858 after a malaria-induced insight on Ternate Island. Darwin's friends arranged for a joint presentation at the Linnean Society on July 1, 1858 — both papers were read together. Darwin rushed *Origin of Species* into print the next year. Wallace remained generous in giving Darwin priority and called the theory 'Darwinism.'",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Alfred Russel Wallace was as much an evolutionary co-discoverer as Darwin — he had the insight independently. Why is Wallace less famous than Darwin today?",
    "answer": "Darwin had developed the idea longer with more evidence — and published the major book",
    "choices": [
        "Darwin had developed the idea longer with more evidence — and published the major book",
        "Wallace never published anything about evolution — only Darwin wrote it up",
        "Wallace's idea was disproved soon after he proposed it — in mid-1858",
        "Wallace gave up biology — and became a financial advisor to wealthy people",
    ],
    "context": "Wallace's 1858 paper was a few pages; Darwin's 1859 *Origin* was a 500-page book backed by 20+ years of evidence. Wallace also moved on to other interests — biogeography (the 'Wallace Line' separating Asian and Australian faunas), social reform, and (for the worse) spiritualism in his later years. Wallace generously called the theory 'Darwinism' to the end of his life.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "What does the famous phrase 'survival of the fittest,' often associated with Darwin, actually mean?",
    "answer": "Best-suited-to-environment, not strongest — organisms that fit their niche reproduce more",
    "choices": [
        "Best-suited-to-environment, not strongest — organisms that fit their niche reproduce more",
        "Strongest physically — only the most muscular organisms survive in nature",
        "Largest — only the biggest creatures pass on traits to the next generation",
        "Smartest — only the most intelligent organisms in any species survive over time",
    ],
    "context": "'Survival of the fittest' was coined by Herbert Spencer, not Darwin (Darwin adopted it cautiously in later editions). 'Fit' meant 'well-adapted to environment' — a small fast mouse may be fitter than a strong slow one in a forest with hawks. The phrase has been misused to argue Social Darwinism — Darwin himself rejected applying biological selection to human social systems.",
    "_pillar": 3,
})

# --- Food chains, ecosystems — 3 ---

P3.append({
    "tier": 2,
    "question": "A food chain runs: grass → grasshopper → mouse → snake → hawk. What's the grass called at the base of this chain?",
    "answer": "A producer — it captures sunlight and makes food via photosynthesis",
    "choices": [
        "A producer — it captures sunlight and makes food via photosynthesis",
        "A consumer — it eats sunshine directly without converting it first",
        "A decomposer — it breaks down dead matter from the previous chain",
        "A predator — it hunts insects and small animals at night actively",
    ],
    "context": "Ecologists split organisms by their role: producers (autotrophs — plants, algae, some bacteria) make their own food from sunlight or chemistry; consumers (heterotrophs — animals) eat other organisms; decomposers (bacteria, fungi) recycle nutrients from dead matter. Each link in a food chain loses about 90% of available energy as heat — so chains rarely have more than 4-5 links.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "British botanist Arthur Tansley coined the word 'ecosystem' in 1935. What problem with earlier biology did he want to fix?",
    "answer": "Biologists had been studying organisms apart — missing their interactions with environment",
    "choices": [
        "Biologists had been studying organisms apart — missing their interactions with environment",
        "Biologists had been confused — about whether plants or animals came first historically",
        "Biologists had been ignoring fossils — focusing only on currently living organisms",
        "Biologists had been classifying species — incorrectly using the older Linnean system",
    ],
    "context": "Tansley's 1935 ecosystem concept unified the biotic (living) and abiotic (non-living) parts of nature — soil, water, weather, organisms — into single interacting systems. The word combined 'ecological' and 'system.' His framework became central to ecology, conservation, and (later) environmental science. Eugene Odum's 1953 textbook *Fundamentals of Ecology* popularized the approach.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Decomposers — bacteria and fungi — play a crucial role in any ecosystem. What do they do that keeps the whole food web running?",
    "answer": "They break down dead organisms, returning nutrients to soil for producers to use",
    "choices": [
        "They break down dead organisms, returning nutrients to soil for producers to use",
        "They build new organisms from raw nutrients in the soil and sunlight directly",
        "They prevent predators from eating their prey, balancing each food chain over time",
        "They cool the planet by absorbing carbon dioxide and locking it away in soil",
    ],
    "context": "Without decomposers, dead plants and animals would pile up forever and the nutrients (nitrogen, phosphorus, carbon) locked inside them would be unavailable for new growth. Decomposers complete the nutrient cycles — the dead are recycled into building blocks for the living. Decomposition is one of the least visible but most important functions in nature.",
    "_pillar": 3,
})

# --- Germ theory (Pasteur + Koch) — 4 ---

P3.append({
    "tier": 2,
    "question": "French chemist Louis Pasteur showed in the 1860s that microorganisms cause spoilage and disease — not 'spontaneous generation.' What clever experiment proved his case?",
    "answer": "He boiled broth in flasks with curved 'swan-neck' tubes — broth stayed clear for years",
    "choices": [
        "He boiled broth in flasks with curved 'swan-neck' tubes — broth stayed clear for years",
        "He bred mice in sealed sterile rooms — and showed no germs reached them in time",
        "He grew bacteria — in pure metallic gold to show they did not need any food source",
        "He froze water samples — from rivers to crystals to capture the germ life inside",
    ],
    "context": "Pasteur's 1862 swan-neck flasks let air in but trapped dust and bacteria in the curved neck. Sterilized broth in straight-neck flasks went cloudy with growth; broth in swan-neck flasks stayed clear indefinitely. When he broke a swan neck off, the corresponding flask quickly went cloudy. Proof: microorganisms come from microorganisms, not from broth itself. End of spontaneous generation.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "In the 1880s Robert Koch developed strict rules for proving a specific microbe causes a disease, still taught as 'Koch's postulates.' What's the basic idea?",
    "answer": "Isolate the microbe — grow it pure, infect a healthy host, then re-isolate the same",
    "choices": [
        "Isolate the microbe — grow it pure, infect a healthy host, then re-isolate the same",
        "Test microbes against many treatments — use only the ones that work in animals first",
        "Vote among colleagues — to decide which microbe is the most likely cause of an illness",
        "Wait for one outbreak in a thousand cases — and study only that single rare outbreak",
    ],
    "context": "Koch's four postulates (1884): (1) the microbe must be present in all cases of the disease; (2) the microbe must be isolated and grown in pure culture; (3) the cultured microbe must cause the disease when given to a healthy host; (4) the microbe must be re-isolated from the new host. Koch identified the bacteria causing anthrax (1876), tuberculosis (1882), and cholera (1884). He won the 1905 Nobel in Medicine.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Robert Koch identified the bacterium causing one of history's deadliest diseases in 1882 — a disease that had killed roughly one in seven people in Europe in the 1800s. What disease?",
    "answer": "Tuberculosis — caused by Mycobacterium tuberculosis",
    "choices": [
        "Tuberculosis — caused by Mycobacterium tuberculosis",
        "Polio — but Koch found a virus rather than a bacterium for the disease",
        "Influenza — caused by what we now know is a flu virus",
        "Common cold — caused by a wide variety of mild upper respiratory viruses",
    ],
    "context": "Koch announced his discovery of *Mycobacterium tuberculosis* on March 24, 1882. TB ('consumption') was killing roughly one in seven Europeans. The bacterium was hard to find — it's small, slow-growing, and stains poorly with then-standard methods. Koch developed new staining techniques to spot it. World TB Day is March 24 each year, commemorating his announcement. TB is still one of the world's deadliest infectious diseases.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Why is pasteurization — heating milk to a specific temperature for a specific time — important?",
    "answer": "It kills harmful bacteria like Salmonella and TB without destroying the milk's quality",
    "choices": [
        "It kills harmful bacteria like Salmonella and TB without destroying the milk's quality",
        "It evaporates excess water from milk to reduce shipping weight to grocery stores",
        "It magnetizes the iron in milk to make it more digestible for older children",
        "It removes the natural sugar (lactose) from milk so anyone can drink it safely",
    ],
    "context": "Pasteurization is named for Louis Pasteur, who developed it to preserve wine and beer in the 1860s. Modern milk pasteurization (typically 72°C for 15 seconds) kills *Mycobacterium tuberculosis* (cattle can give humans TB through unpasteurized milk), *Salmonella*, *Listeria*, *E. coli*, *Brucella*, and *Campylobacter*. Pasteurization has prevented countless cases of food-borne disease since standardized in the early 1900s.",
    "_pillar": 3,
})

# --- Jenner cowpox 1796 — 1 ---

P3.append({
    "tier": 2,
    "question": "In 1796 Edward Jenner inoculated 8-year-old James Phipps with material from a milkmaid's cowpox sore, then exposed him to smallpox. Phipps didn't get sick. What had Jenner just done?",
    "answer": "Performed the first deliberate vaccination — using cowpox to protect against smallpox",
    "choices": [
        "Performed the first deliberate vaccination — using cowpox to protect against smallpox",
        "Performed the first deliberate gene therapy — by exchanging the boy's cells",
        "Performed the first deliberate surgery — by removing the cowpox blister entirely",
        "Performed the first deliberate antibiotic test — using cow tissue as a medicine",
    ],
    "context": "Jenner had noticed that milkmaids who caught cowpox (a mild disease from cows) seemed not to get smallpox (the deadly human version). His 1796 experiment with Phipps confirmed it. The word 'vaccine' comes from 'vacca,' Latin for cow. Jenner's discovery launched modern immunization. Smallpox would eventually be eradicated worldwide in 1980 — the only human disease ever eliminated.",
    "_pillar": 3,
})

# --- Pasteur rabies 1885 — 1 ---

P3.append({
    "tier": 2,
    "question": "In July 1885 Louis Pasteur used his experimental rabies treatment on a real patient for the first time. Who was the patient, and what was the situation?",
    "answer": "Nine-year-old Joseph Meister, bitten 14 times by a rabid dog — and Meister survived",
    "choices": [
        "Nine-year-old Joseph Meister, bitten 14 times by a rabid dog — and Meister survived",
        "An elderly French chemist — infected during a lab accident with his own samples",
        "A wealthy Parisian baroness — bitten by her pet dog at her country estate",
        "Pasteur himself — who tested the vaccine on his own arm to prove safety to others",
    ],
    "context": "Joseph Meister had been mauled by a rabid dog in Alsace. Without treatment, he would almost certainly die. Pasteur's vaccine — weakened rabies virus from desiccated infected rabbit spinal cords — was untested in humans. Pasteur gave it anyway over 13 days. Meister survived and lived to age 64. He worked the rest of his life as the gatekeeper at the Pasteur Institute, founded with funds raised after the rabies success.",
    "_pillar": 3,
})

# --- Salk polio 1955 — 2 ---

P3.append({
    "tier": 2,
    "question": "In 1955 American medical researcher Jonas Salk announced a vaccine against a disease that had been paralyzing thousands of American children each year. What disease?",
    "answer": "Polio — once a major cause of childhood paralysis and death in the United States",
    "choices": [
        "Polio — once a major cause of childhood paralysis and death in the United States",
        "Measles — Maurice Hilleman's vaccine came out a decade later in 1963",
        "Whooping cough — for which the first vaccines had been used since the 1920s",
        "Yellow fever — for which Max Theiler had already developed a vaccine in 1937",
    ],
    "context": "Polio epidemics peaked in the US in 1952 with about 58,000 cases. Salk's killed-virus vaccine, announced April 12, 1955, was a triumph. Within a few years, US polio cases dropped by 85-90%. Salk famously refused to patent the vaccine — when asked by Edward R. Murrow who held the patent, he said: 'Well, the people, I would say. There is no patent. Could you patent the sun?'",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Jonas Salk's polio vaccine (1955) used killed virus injected by needle. A few years later Albert Sabin developed a different version. What was different about Sabin's vaccine (1962)?",
    "answer": "It used weakened-but-live virus taken orally — usually on a sugar cube",
    "choices": [
        "It used weakened-but-live virus taken orally — usually on a sugar cube",
        "It used killed virus injected into the arm — just like the Salk version",
        "It used a synthetic chemical compound — made entirely without any virus material",
        "It used purified salt water injected — into the spine to trigger immunity",
    ],
    "context": "Albert Sabin's oral polio vaccine was easier to give (no needle), cheaper, and conferred some intestinal immunity that Salk's didn't. It was used worldwide for global eradication campaigns. Polio cases dropped from hundreds of thousands per year globally in the 1980s to about a dozen wild-type cases in 2023. The disease persists in pockets of Pakistan and Afghanistan.",
    "_pillar": 3,
})

# --- Hilleman 40 vaccines — 2 ---

P3.append({
    "tier": 2,
    "question": "American microbiologist Maurice Hilleman has been called 'the most successful vaccinologist in history.' How many vaccines did he develop or contribute to over his career?",
    "answer": "Over 40 vaccines — including measles, mumps, rubella, hepatitis A and B, and chickenpox",
    "choices": [
        "Over 40 vaccines — including measles, mumps, rubella, hepatitis A and B, and chickenpox",
        "Exactly 4 vaccines — all of them targeting tropical mosquito-borne diseases",
        "Around 80 vaccines — half against animal diseases on commercial farms",
        "Around 2 vaccines — one against polio and one against measles together",
    ],
    "context": "Maurice Hilleman (1919-2005) worked at Merck for 47 years. His 40+ vaccines include the eight commonly given to American kids today. Estimated lives saved: roughly 8 million per year. When his own daughter Jeryl Lynn caught the mumps in 1963, he swabbed her throat, isolated the virus, and used it to develop the mumps vaccine in 1967 — still in use today. Despite his impact, he stayed largely out of the spotlight.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Maurice Hilleman's mumps vaccine has an unusual origin. The strain it's based on came from where?",
    "answer": "His own 5-year-old daughter Jeryl Lynn's throat when she caught mumps in 1963",
    "choices": [
        "His own 5-year-old daughter Jeryl Lynn's throat when she caught mumps in 1963",
        "A monkey at the Bronx Zoo that had been observed coughing in a strange way",
        "A patient in his own hospital who refused to give consent to use her samples",
        "A lab-engineered strain Hilleman built from scratch in 1965 using gene editing tools",
    ],
    "context": "Hilleman's daughter Jeryl Lynn caught mumps on a Sunday in 1963. Hilleman drove to his lab, swabbed her throat, and isolated the virus. He weakened the virus through repeated culturing and tested it as a vaccine. The 'Jeryl Lynn strain' has been used in every US mumps vaccine ever since. Jeryl Lynn herself became a microbiologist as an adult.",
    "_pillar": 3,
})

# --- Smallpox eradication 1980 — 1 ---

P3.append({
    "tier": 2,
    "question": "Smallpox killed roughly 300 million people in the 20th century alone. On May 8, 1980 the World Health Organization announced something no other infectious disease has ever achieved. What?",
    "answer": "Smallpox had been eradicated — no longer circulating naturally anywhere on Earth",
    "choices": [
        "Smallpox had been eradicated — no longer circulating naturally anywhere on Earth",
        "Smallpox had been declared a fictional disease made up — by medieval doctors",
        "Smallpox had been moved entirely into — the world's deep oceans for safe storage",
        "Smallpox had been renamed to remove — the stigma of an older disease label",
    ],
    "context": "The WHO Smallpox Eradication Program ran 1967-1980 under D.A. Henderson's leadership. The last natural case was Ali Maow Maalin in Somalia, October 1977. WHO formally declared eradication May 8, 1980 — one of humanity's greatest public-health achievements. The virus now exists only in two secured laboratories (CDC Atlanta and VECTOR in Russia), and even that is controversial.",
    "_pillar": 3,
})

# --- Semmelweis 1847 (rejected) — 1 ---

P3.append({
    "tier": 2,
    "question": "In 1847 Hungarian doctor Ignaz Semmelweis showed that doctors washing hands with chlorinated lime cut maternity-ward deaths from about 18% to 1%. How did the Vienna medical establishment respond?",
    "answer": "They mocked him — he was eventually institutionalized and died in an asylum",
    "choices": [
        "They mocked him — he was eventually institutionalized and died in an asylum",
        "They adopted hand-washing across every — European hospital within a few months",
        "They awarded him the first medical — Nobel Prize given for the discovery",
        "They renamed the hospital after him — and built a statue while he was alive",
    ],
    "context": "Semmelweis was correct, but he couldn't explain WHY hand-washing worked — germ theory came decades later from Pasteur and Koch. Without a mechanism, his statistical evidence was rejected. He died in 1865 at age 47, possibly from sepsis after being beaten by asylum guards. Vindicated posthumously when Lister extended his work to surgical antisepsis in the 1860s.",
    "_pillar": 3,
})

# --- Marshall 1984 H. pylori — 1 ---

P3.append({
    "tier": 2,
    "question": "In 1984 Australian gastroenterologist Barry Marshall, frustrated nobody believed him, drank a beaker of *H. pylori* and developed gastritis within days. What had medicine previously taught about stomach ulcers?",
    "answer": "Ulcers were caused by stress and spicy food — not by bacteria",
    "choices": [
        "Ulcers were caused by stress and spicy food — not by bacteria",
        "Ulcers were caused — by drinking too much water with meals each day",
        "Ulcers were known to be bacterial — but no one wanted to treat them with drugs",
        "Ulcers were considered entirely imaginary — by all major medical authorities",
    ],
    "context": "Marshall and Robin Warren identified *Helicobacter pylori* in ulcer biopsies in 1982. Mainstream medicine refused — stomach acid 'obviously' killed bacteria. Marshall drank the H. pylori culture, developed gastritis, then cured himself with antibiotics. Vindicated; he and Warren won the 2005 Nobel in Medicine. Ulcers are now routinely cured with a brief antibiotic course — unimaginable under the old stress-and-spicy-food consensus.",
    "_pillar": 3,
})

# --- Misc P3 grab-bag (DNA, mitosis, blood, classification, viruses) — 14 to reach 50 ---

P3.append({
    "tier": 2,
    "question": "Every living thing carries instructions in molecules of DNA. What does the abbreviation DNA stand for?",
    "answer": "Deoxyribonucleic acid",
    "choices": [
        "Deoxyribonucleic acid",
        "Dynamic nuclear arrangement",
        "Double nucleotide assembly",
        "Direct nuclear analyzer",
    ],
    "context": "Deoxyribonucleic acid (DNA) is a long molecule shaped like a twisted ladder ('double helix') — first described by James Watson, Francis Crick, and Rosalind Franklin in 1953. The 'rungs' are pairs of bases: A pairs with T, G pairs with C. The sequence of bases is the genetic code. Every cell in your body contains about 2 meters of DNA folded into a microscopic nucleus.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "When a body cell divides into two identical cells (for growth and repair), what's the process called?",
    "answer": "Mitosis — one cell divides into two cells with identical chromosomes",
    "choices": [
        "Mitosis — one cell divides into two cells with identical chromosomes",
        "Meiosis — one cell divides into four cells with half the usual chromosomes",
        "Osmosis — water moves across a membrane from low to high concentration",
        "Photosynthesis — sugar is made from sunlight by green leaves of plants",
    ],
    "context": "Mitosis is the normal cell division for growth and tissue repair: one parent cell duplicates its chromosomes and divides into two genetically identical daughter cells. Meiosis is the special cell division that makes sex cells (sperm and eggs) — one cell becomes four, each with half the chromosomes, ready to combine with another sex cell at fertilization.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Human blood has cells with different jobs. Red blood cells carry oxygen using what iron-containing protein?",
    "answer": "Hemoglobin — it binds oxygen in the lungs and releases it in tissues",
    "choices": [
        "Hemoglobin — it binds oxygen in the lungs and releases it in tissues",
        "Insulin — it controls how cells take in sugar from the blood for energy",
        "Keratin — the protein that gives strength to hair, nails, and outer skin",
        "Collagen — the protein that holds together skin and connective tissue",
    ],
    "context": "Hemoglobin (in red blood cells) carries oxygen from the lungs to the rest of the body. Each hemoglobin molecule has four heme groups, each containing an iron atom that binds an O₂ molecule. The bright red color of arterial blood is oxygenated hemoglobin; the darker red of venous blood is hemoglobin that has released its oxygen. Carbon monoxide poisoning works by binding hemoglobin more tightly than oxygen does.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Carl Linnaeus, an 18th-century Swedish botanist, created the system biologists still use to name species. What's that system called?",
    "answer": "Binomial nomenclature — every species gets a two-part Latin name (Genus species)",
    "choices": [
        "Binomial nomenclature — every species gets a two-part Latin name (Genus species)",
        "Trinomial nomenclature — every species gets a three-part name with a habitat tag",
        "Numerical nomenclature — species are assigned a unique number from 1 upward",
        "Local naming — every region of Earth uses different names for the same species",
    ],
    "context": "Linnaeus's *Systema Naturae* (10th edition, 1758) standardized biological naming. Every species gets a two-part Latin name: humans are *Homo sapiens* (genus *Homo*, species *sapiens*). The two-name system replaced earlier long descriptive Latin phrases. Linnaeus also organized organisms into a hierarchy (kingdom, class, order, family, genus, species) that still structures biological classification.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Viruses are smaller than bacteria and have no cells. They consist mostly of genetic material wrapped in a protein coat. Are viruses considered alive?",
    "answer": "It depends on the definition — viruses need a host cell to reproduce",
    "choices": [
        "It depends on the definition — viruses need a host cell to reproduce",
        "Yes — they are clearly alive in every standard biological framework",
        "Yes — every virus reproduces independently outside any host's body",
        "No — they have been formally classified by every textbook as non-living",
    ],
    "context": "Viruses are at the boundary of life: they have genetic material (DNA or RNA) and can evolve, but they can't reproduce without taking over a host cell's machinery. They have no metabolism on their own. Many biologists call them 'replicating chemicals' rather than organisms. Dmitri Ivanovsky first identified a virus (tobacco mosaic) in 1892 by filtering out bacteria and finding that what remained could still infect.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Sharks are NOT mammals, fish, or reptiles — they belong to a separate class. What class are sharks part of?",
    "answer": "Cartilaginous fish (Chondrichthyes) — their skeletons are flexible cartilage, not bone",
    "choices": [
        "Cartilaginous fish (Chondrichthyes) — their skeletons are flexible cartilage, not bone",
        "Bony fish (Osteichthyes) — the same class as cod, tuna, and salmon",
        "Mammals — they breathe air and give birth to live young like dolphins do",
        "Reptiles — they are cold-blooded and lay eggs in sand on tropical beaches",
    ],
    "context": "Sharks, rays, and skates are cartilaginous fish — their skeletons are made of cartilage, not bone. The class diverged from bony fish about 400 million years ago. Sharks predate trees, dinosaurs, and Mt. Everest. Cartilage doesn't fossilize well, so much of their evolutionary record comes from teeth. Many shark species give birth to live young (viviparous) — but they are not mammals.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Humans, dogs, whales, and bats all share the same five-finger forelimb pattern — though hands, paws, flippers, and wings look different. What's this evidence called?",
    "answer": "Homologous structures — common ancestry showing in shared body plans",
    "choices": [
        "Homologous structures — common ancestry showing in shared body plans",
        "Analogous structures — completely different ancestry showing in shared body plans",
        "Vestigial structures — useless leftovers from species that disappeared in the past",
        "Convergent structures — adapted to similar environments but with no shared ancestry",
    ],
    "context": "Homology — same underlying structure, different surface appearance — is one of the strongest pieces of evidence for evolution. The five-bone forelimb pattern (humerus, radius, ulna, carpals, digits) appears in every mammal because mammals share a common ancestor that had it. Analogous structures (insect wings vs. bird wings) developed independently and don't have shared deep structure — convergent evolution from different starting points.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Honey bees do a special 'waggle dance' inside the hive after finding food. The Austrian biologist Karl von Frisch decoded the dance in the 1940s. What does the dance communicate?",
    "answer": "The direction and distance to food sources outside the hive",
    "choices": [
        "The direction and distance to food sources outside the hive",
        "The colors of the flowers the dancing bee just visited a short time ago",
        "The hive's current temperature compared to the surrounding outside air temperature",
        "The number of bees that have died over the previous day's flying activity",
    ],
    "context": "Karl von Frisch's 1940s research showed that returning forager bees dance on the vertical comb. The angle from vertical signals direction relative to the Sun; the duration of the 'waggle' phase signals distance. Other bees decode the dance and fly straight to the food source. Von Frisch won the 1973 Nobel in Medicine with Konrad Lorenz and Niko Tinbergen for animal-behavior research.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Each fall, monarch butterflies fly thousands of miles from Canada to specific forests in central Mexico. The strange part: no individual makes the round trip. How do they find the same trees?",
    "answer": "It takes 3-4 generations to complete the journey — navigation is somehow inherited",
    "choices": [
        "It takes 3-4 generations to complete the journey — navigation is somehow inherited",
        "Each individual butterfly remembers — its own grandparents' specific routes",
        "Mexican farmers raise them in fall — and ship them by truck to northern fields",
        "The Mexican forests release a chemical — scent strong enough to reach Canada",
    ],
    "context": "Monarchs make a 3,000-4,000 mile migration. The butterflies that arrive at the Mexican oyamel fir forests in November aren't the ones that left there in March — they're great-grandchildren of those butterflies. How they navigate to forests they've never seen is still not fully understood. They use the Sun, possibly Earth's magnetic field, and an internal clock — but the inheritance mechanism remains a partial mystery.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "When you exercise hard, your muscles burn. Long blamed on lactic acid, recent research has revised the story. What's now better understood about muscle fatigue?",
    "answer": "Lactate itself is a fuel, not the cause of burn — the burn comes from accompanying acid buildup",
    "choices": [
        "Lactate itself is a fuel, not the cause of burn — the burn comes from accompanying acid buildup",
        "Muscles burn — because they catch a small literal fire during heavy exercise",
        "The burn is caused entirely — by sugar molecules pressing against muscle walls",
        "The burn happens only in young athletes — older athletes never feel it",
    ],
    "context": "For decades, lactic acid buildup was blamed for muscle burn. Modern biochemistry (much of it from George Brooks at Berkeley) shows lactate (the salt form of lactic acid) is actually a USEFUL metabolic fuel — muscles, heart, and brain can burn it. The 'burn' from hard exercise comes more from accompanying acidic conditions and metabolite accumulation than lactate itself. The old textbooks were wrong on this for a long time.",
    "_pillar": 3,
})

P3.append({
    "tier": 2,
    "question": "Snakes shed their skin periodically as they grow. Why do they do this?",
    "answer": "Skin doesn't grow like ours — so they must molt off the old outer layer entirely",
    "choices": [
        "Skin doesn't grow like ours — so they must molt off the old outer layer entirely",
        "Snakes shed skin to advertise their — fitness to potential mates each year",
        "Snake skin builds up too much heat in the summer — molting is for cooling",
        "Snakes molt only when wounded — healthy snakes keep the same skin for life",
    ],
    "context": "Snake skin is keratin scales fused into a continuous outer layer. The layer doesn't grow with the snake. As the snake grows, it forms a new larger layer beneath, then sheds the old one in a single piece, often eyelids included. Younger snakes molt more frequently. The process is called ecdysis. Insects, crustaceans, and other arthropods molt too — for the same reason: a rigid exoskeleton can't grow with them.",
    "_pillar": 3,
})

# Sanity check
assert len(P3) == 50, f"P3 expected 50, got {len(P3)}"


# Combine
ALL_QUESTIONS = P1 + P2 + P3
assert len(ALL_QUESTIONS) == 140, f"total expected 140, got {len(ALL_QUESTIONS)}"


# ===========================================================================
# Validation
# ===========================================================================

def validate_all() -> tuple[list, int, int]:
    """Validate against the science bank + our own batch.
    Returns: (questions_list, fail_count, soft_warn_count)
    """
    science_bank_path = REPO / "data" / "questions" / "science.json"
    existing_bank = json.loads(science_bank_path.read_text(encoding="utf-8"))
    print(f"\nLoaded {len(existing_bank)} existing science questions for dedup")

    combined = existing_bank + ALL_QUESTIONS
    dup_index, ans_index = build_bank_indices(combined)

    fail_count = 0
    soft_count = 0
    fails: list[tuple[int, dict, list]] = []

    n_existing = len(existing_bank)
    for i, q in enumerate(ALL_QUESTIONS):
        bank_idx = n_existing + i
        r = validate_rewrite(
            "science", q, bank=combined, dup_index=dup_index,
            answer_index=ans_index, replace_idx=bank_idx,
        )
        total = len(q["question"]) + sum(len(c) for c in q["choices"])
        if r["verdict"] == "FAIL":
            fail_count += 1
            fails.append((i, q, r["hard_fails"]))
            print(f"  FAIL #{i:03d} T{q['tier']} total={total}c: {q['question'][:60]}")
            for g, reason in r["hard_fails"]:
                print(f"      {g}: {reason[:200]}")
        elif r["verdict"] == "SOFT_WARN":
            soft_count += 1
            print(f"  SOFT #{i:03d} T{q['tier']} total={total}c: {q['question'][:60]}")
            for g, reason in r["soft_warns"]:
                print(f"      {g}: {reason[:160]}")
    return ALL_QUESTIONS, fail_count, soft_count


def write_output(questions: list[dict]) -> None:
    out_path = REPO / "_gen_science_t2_p123.json"
    # Strip private metadata before writing
    cleaned = []
    for q in questions:
        cleaned.append({
            "tier": q["tier"],
            "question": q["question"],
            "answer": q["answer"],
            "choices": q["choices"],
            "context": q["context"],
        })
    output = {
        "tier": 2,
        "summary": {
            "questions_generated": len(cleaned),
            "by_pillar": {"1": len(P1), "2": len(P2), "3": len(P3)},
        },
        "questions": cleaned,
    }
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {len(cleaned)} questions to {out_path}")


if __name__ == "__main__":
    questions, fails, softs = validate_all()
    print(f"\nValidation summary: {len(questions)} q, {fails} hard fails, {softs} soft warns")
    if fails == 0:
        write_output(questions)
    else:
        print("Will not write output until fails are resolved.")
