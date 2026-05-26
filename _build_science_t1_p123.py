"""Generate 140 fresh Tier-1 (grade 5) science questions.

Voice rule: The Discovery Pattern. T1 is symbol-led / kid-visual / named-discovery
primer territory. See proposals/v2_audit/SCIENCE_FRAMEWORK.md §1, SCIENCE_TEMPLATES.md
§1.T1, tools/quizgen/exemplars/science.py.

Distribution:
  P1 Physics   : 50
  P2 Chemistry : 40
  P3 Biology   : 50
  Total        : 140

Constraints:
  - T1 char cap 280 total (stem + 4 choices); grace 294.
  - em-dash uniform across all 4 choices (all or none).
  - distractor parity 1.30 max/min ratio (cooking-style answer-outlier rule
    applies — answer up to 1.6x longest distractor allowed).
  - no fabricated dates / journals / scientists.
  - no anti-dissent slurs ("denier", "anti-vaxxer", "conspiracy theorist").
  - no anthropomorphizing nature ("evolution wants") without scare quotes.

Output: _gen_science_t1_p123.json (canonical).

Wrapper schema:
  {"tier": 1, "summary": {...}, "questions": [...]}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402


# ============================================================================
# PILLAR 1 — PHYSICS (50)
# motion, forces, magnets, light, sound, gravity, friction, simple machines,
# energy, temperature, density, balance
# ============================================================================

P1 = []

# --- Gravity / falling bodies / motion (10) ---

P1.append({
    "tier": 1,
    "question": "If you let go of a ball in mid-air, which way does it fall, and why?",
    "answer": "Down, because Earth's gravity pulls it toward the ground",
    "choices": [
        "Down, because Earth's gravity pulls it toward the ground",
        "Sideways, because the air is always pushing it east",
        "Up, since light things rise and heavy things stay",
        "Nowhere, since a ball with no hand stays in place",
    ],
    "context": "Gravity is the pull every chunk of matter has on every other chunk. The Earth's huge mass pulls everything near its surface toward its center, which we feel as 'down.'",
    "_pillar": 1,
    "_strategy": "gravity_basics",
})

P1.append({
    "tier": 1,
    "question": "Apollo 15 astronaut David Scott dropped a hammer and a feather together on the Moon. Which hit first?",
    "answer": "Both at once, since the Moon has no air",
    "choices": [
        "Both at once, since the Moon has no air",
        "The hammer, because hammers always fall faster",
        "The feather, because feathers float in vacuums",
        "Neither, since gravity doesn't work on the Moon",
    ],
    "context": "In 1971 David Scott dropped a hammer and a falcon feather on the Moon to show Galileo was right: without air, all things fall together. The Moon has gravity (about 1/6 of Earth's), just no air.",
    "_pillar": 1,
    "_strategy": "moon_drop_apollo15",
})

P1.append({
    "tier": 1,
    "question": "A skateboard at rest will stay at rest unless something pushes or pulls it. Who first wrote down this 'law of inertia'?",
    "answer": "Isaac Newton, in his laws of motion",
    "choices": [
        "Isaac Newton, in his laws of motion",
        "Marie Curie, in her work on radium",
        "Charles Darwin, in his book about finches",
        "Benjamin Franklin, in his kite experiment",
    ],
    "context": "Isaac Newton's first law (1687, in his *Principia*) says objects keep doing what they're doing unless a force acts on them. Galileo glimpsed the same idea earlier; Newton wrote the math.",
    "_pillar": 1,
    "_strategy": "newton_first_law",
})

P1.append({
    "tier": 1,
    "question": "A ball rolls farther on a smooth floor than on thick carpet. What force slows the ball on the carpet?",
    "answer": "Friction between the ball and the carpet fibers",
    "choices": [
        "Friction between the ball and the carpet fibers",
        "Gravity pulling the ball backward toward you",
        "Magnetism between the ball and the floor",
        "Air pressure from the ceiling pressing down",
    ],
    "context": "Friction is the force two surfaces make when they slide past each other. Rough surfaces (carpet) have more friction than smooth ones (polished floor), so things stop quicker.",
    "_pillar": 1,
    "_strategy": "friction_basic",
})

P1.append({
    "tier": 1,
    "question": "When you push someone on a swing, the swing pushes back on your hand. This 'every action has an equal and opposite reaction' rule is whose law?",
    "answer": "Newton's third law of motion",
    "choices": [
        "Newton's third law of motion",
        "Galileo's swinging-lamp law",
        "Einstein's law of relativity",
        "Curie's law of radioactivity",
    ],
    "context": "Newton's three laws (1687) describe how forces work. The third says forces always come in pairs — if you push the wall, the wall pushes you back exactly as hard.",
    "_pillar": 1,
    "_strategy": "newton_third_law",
})

P1.append({
    "tier": 1,
    "question": "A toy car needs a harder push to start moving than a tennis ball. What's the word for 'how much stuff is in an object'?",
    "answer": "Mass",
    "choices": ["Mass", "Color", "Sound", "Shadow"],
    "context": "Mass is the amount of matter in something, measured in grams or kilograms. More mass means more inertia — the car resists changing motion more than the tennis ball does.",
    "_pillar": 1,
    "_strategy": "mass_definition",
})

P1.append({
    "tier": 1,
    "question": "On a slide you speed up as you go down. Where does your new motion energy come from?",
    "answer": "From the height, stored as gravity energy",
    "choices": [
        "From the height, stored as gravity energy",
        "From the slide growing warmer during the day",
        "From the air pushing you forward as you go",
        "From sunlight shining down on your shoulders",
    ],
    "context": "Anything raised up has gravitational potential energy. As you slide down, that stored energy turns into motion energy (kinetic energy). Roller coasters work the same way.",
    "_pillar": 1,
    "_strategy": "potential_to_kinetic",
})

P1.append({
    "tier": 1,
    "question": "You drop a heavy rock and a small pebble at the same time off a wall. Ignoring air, what happens?",
    "answer": "They hit the ground at the same time",
    "choices": [
        "They hit the ground at the same time",
        "The heavy rock hits much earlier than the pebble",
        "The pebble hits much earlier than the heavy rock",
        "They both float in the air for a long while",
    ],
    "context": "Galileo argued in the late 1500s that gravity gives every object the same downward acceleration. Heavier doesn't mean faster falling — heavier just means more force is needed to lift it.",
    "_pillar": 1,
    "_strategy": "galileo_falling_bodies",
})

P1.append({
    "tier": 1,
    "question": "What keeps the Moon circling around Earth instead of flying off into space?",
    "answer": "Earth's gravity, which constantly pulls the Moon toward it",
    "choices": [
        "Earth's gravity, which constantly pulls the Moon toward it",
        "A long invisible chain that connects them",
        "Air pressure, which forms a wall above our sky",
        "Magnets in Earth's core that grip the Moon",
    ],
    "context": "Gravity acts across empty space. The Moon is moving sideways fast enough that Earth's gravity bends its path into a loop instead of pulling it down. Same reason satellites orbit.",
    "_pillar": 1,
    "_strategy": "orbit_gravity",
})

P1.append({
    "tier": 1,
    "question": "A bowling ball is harder to push than a soccer ball. The 'pull of Earth's gravity' on each ball is called its what?",
    "answer": "Weight",
    "choices": ["Weight", "Length", "Volume", "Color"],
    "context": "Weight is the force of gravity on an object. On the Moon you would weigh about 1/6 of your Earth weight, but your mass (the stuff in you) would be the same.",
    "_pillar": 1,
    "_strategy": "weight_vs_mass",
})

# --- Magnets (5) ---

P1.append({
    "tier": 1,
    "question": "Which of these will a fridge magnet stick to?",
    "answer": "A steel paperclip",
    "choices": [
        "A steel paperclip",
        "A glass marble",
        "A wooden pencil",
        "A piece of paper",
    ],
    "context": "Magnets pull on iron, nickel, and cobalt. Steel is mostly iron, so it sticks. Glass, wood, plastic, and paper have no magnetic pull.",
    "_pillar": 1,
    "_strategy": "magnet_what_sticks",
})

P1.append({
    "tier": 1,
    "question": "Bring two bar magnets near each other so two north ends face. What happens?",
    "answer": "They push each other apart",
    "choices": [
        "They push each other apart",
        "They snap together strongly",
        "They turn into one bigger magnet",
        "They lose their power forever",
    ],
    "context": "Magnets have two poles, north and south. Like poles (N-N or S-S) repel. Opposite poles (N-S) attract. Same rule as static charges.",
    "_pillar": 1,
    "_strategy": "magnet_poles",
})

P1.append({
    "tier": 1,
    "question": "A compass needle always lines up pointing roughly north. Why?",
    "answer": "Earth itself acts like a giant magnet",
    "choices": [
        "Earth itself acts like a giant magnet",
        "The needle is always heavier on the north end",
        "Bright sunlight pulls the needle north each day",
        "The north pole of the sky has a hidden magnet",
    ],
    "context": "Earth's molten iron core creates a magnetic field around the whole planet. The little magnet inside a compass swings to line up with it — north on the compass points to magnetic north.",
    "_pillar": 1,
    "_strategy": "earth_magnetic_field",
})

P1.append({
    "tier": 1,
    "question": "Sprinkle iron filings on paper above a bar magnet. The filings line up in curved lines. What do these lines show?",
    "answer": "The shape of the magnet's invisible magnetic field",
    "choices": [
        "The shape of the magnet's invisible magnetic field",
        "The path that light takes through the paper",
        "Sound waves moving through the iron filings",
        "Random patterns with no real meaning at all",
    ],
    "context": "A magnetic field is the region around a magnet where its force reaches. Iron filings make the field visible by lining up along its 'field lines' — you can see them loop from north pole to south.",
    "_pillar": 1,
    "_strategy": "magnetic_field_lines",
})

P1.append({
    "tier": 1,
    "question": "What happens if you cut a bar magnet in half across the middle?",
    "answer": "You get two smaller magnets, each with its own north and south",
    "choices": [
        "You get two smaller magnets, each with its own north and south",
        "You get one half with only north, and one with only south",
        "You get two pieces of metal that are no longer magnetic",
        "You get a magnet that pulls only wood and plastic",
    ],
    "context": "There is no such thing as just a north pole or just a south pole. Cut a magnet in half and you get two complete magnets. Cut those, and you get four. All the way down to atoms.",
    "_pillar": 1,
    "_strategy": "magnet_cut_in_half",
})

# --- Light (8) ---

P1.append({
    "tier": 1,
    "question": "Shine white sunlight through a glass prism. What do you see come out the other side?",
    "answer": "A rainbow of colors, from red to violet",
    "choices": [
        "A rainbow of colors, from red to violet",
        "A brighter beam of pure white light",
        "A beam of black light with no color",
        "A beam that bends but stays bright white",
    ],
    "context": "White light is a mix of every color. A prism bends each color by a slightly different amount, spreading them apart. Isaac Newton showed this with a prism in his bedroom in the 1660s.",
    "_pillar": 1,
    "_strategy": "prism_white_light",
})

P1.append({
    "tier": 1,
    "question": "Why do we see a rainbow in the sky after rain on a sunny day?",
    "answer": "Tiny raindrops act like prisms, splitting sunlight into colors",
    "choices": [
        "Tiny raindrops act like prisms, splitting sunlight into colors",
        "The clouds paint the colors onto the sky as they pass",
        "The Sun changes colors when it gets wet from rain",
        "Birds flying through the air bend the light around",
    ],
    "context": "Each falling raindrop bends and reflects sunlight, splitting it into the rainbow's seven traditional colors: red, orange, yellow, green, blue, indigo, violet. A rainbow is always opposite the sun.",
    "_pillar": 1,
    "_strategy": "rainbow_explanation",
})

P1.append({
    "tier": 1,
    "question": "Why is the sky blue during the day?",
    "answer": "Tiny molecules in the air scatter blue light more than other colors",
    "choices": [
        "Tiny molecules in the air scatter blue light more than other colors",
        "The ocean reflects up onto the air above it",
        "The Sun shines blue light, while the Moon shines white",
        "Blue paint mixed with the clouds when Earth formed",
    ],
    "context": "Sunlight hits gas molecules in the atmosphere. Blue light has shorter waves and bounces around much more than red, filling the sky with scattered blue. This is called Rayleigh scattering.",
    "_pillar": 1,
    "_strategy": "blue_sky_rayleigh",
})

P1.append({
    "tier": 1,
    "question": "Why do sunsets often look red or orange?",
    "answer": "At sunset, light passes through more air, and most blue has been scattered away",
    "choices": [
        "At sunset, light passes through more air, and most blue has been scattered away",
        "The Sun is touching the ocean and gets warmer",
        "Clouds turn into glowing fire each evening",
        "The Sun changes color when it gets sleepy at night",
    ],
    "context": "When the Sun sits near the horizon, its light travels through a longer stretch of atmosphere. Blue scatters out long before the light reaches you, leaving the warm reds and oranges.",
    "_pillar": 1,
    "_strategy": "red_sunset",
})

P1.append({
    "tier": 1,
    "question": "Stand a pencil in a clear glass of water. The pencil looks bent at the surface. Why?",
    "answer": "Light bends when it moves between air and water",
    "choices": [
        "Light bends when it moves between air and water",
        "The water actually breaks the pencil in half",
        "Your eyes get blurry in the bright kitchen",
        "Water adds an invisible curve to the pencil",
    ],
    "context": "Light slows down going from air into water and changes direction a little. This bending of light is called refraction. Eye glasses and camera lenses work the same way.",
    "_pillar": 1,
    "_strategy": "refraction_pencil",
})

P1.append({
    "tier": 1,
    "question": "Why do you see your face in a flat mirror?",
    "answer": "The smooth mirror reflects light bouncing off your face back to your eyes",
    "choices": [
        "The smooth mirror reflects light bouncing off your face back to your eyes",
        "The mirror remembers what your face looked like yesterday",
        "There is a tiny camera taking your photo behind the glass",
        "Mirrors make their own version of you to copy what you do",
    ],
    "context": "Light bouncing off your face hits the mirror's smooth back and bounces straight back. Your eyes pick up the bounced light and see a 'flipped' copy of you — your right hand looks like its left.",
    "_pillar": 1,
    "_strategy": "mirror_reflection",
})

P1.append({
    "tier": 1,
    "question": "How fast does light travel through empty space?",
    "answer": "About 300,000 kilometers per second, the fastest thing in nature",
    "choices": [
        "About 300,000 kilometers per second, the fastest thing in nature",
        "About the same speed as a fast jet airplane in flight",
        "About 100 meters per second, faster than a runner",
        "Just slightly faster than the speed of sound in air",
    ],
    "context": "Light's speed in a vacuum is roughly 300,000 km/s (about 186,000 miles per second). It takes about 8 minutes for sunlight to reach Earth from the Sun. Einstein showed nothing can go faster.",
    "_pillar": 1,
    "_strategy": "speed_of_light",
})

P1.append({
    "tier": 1,
    "question": "A flashlight makes a sharp shadow when you point it at your hand. What is a shadow?",
    "answer": "The dark area where your hand blocks the light from reaching the wall",
    "choices": [
        "The dark area where your hand blocks the light from reaching the wall",
        "A copy of your hand made out of black smoke and dust",
        "A reflection of your hand from the floor below",
        "A tiny twin of you that follows you around",
    ],
    "context": "Light travels in straight lines from a source. When something solid blocks those lines, the area behind it gets no light — that dark patch is the shadow. Move the light and the shadow moves with it.",
    "_pillar": 1,
    "_strategy": "shadow_basics",
})

# --- Sound (5) ---

P1.append({
    "tier": 1,
    "question": "When you bang a drum, you can feel the drum-skin vibrating. Sound is made by what?",
    "answer": "Vibrations that travel as waves through the air",
    "choices": [
        "Vibrations that travel as waves through the air",
        "Tiny flashes of light leaving the drum",
        "Smoke rising from inside the drum",
        "Magnetism pulled out of the drum-skin",
    ],
    "context": "All sound starts with something shaking. The shake pushes air molecules in waves that reach your eardrum, which shakes too. Your brain reads those shakes as sound.",
    "_pillar": 1,
    "_strategy": "sound_vibrations",
})

P1.append({
    "tier": 1,
    "question": "In a thunderstorm you see the lightning a few seconds before you hear the thunder. Why?",
    "answer": "Light travels much faster through air than sound does",
    "choices": [
        "Light travels much faster through air than sound does",
        "Thunder is shy and waits before speaking",
        "The lightning is much closer to you than the thunder",
        "Sound takes a different route through the clouds",
    ],
    "context": "Light moves at about 300,000 km/s; sound at only about 340 m/s in air. For every 3 seconds between flash and rumble, the storm is about 1 km away. They actually happen at the same time.",
    "_pillar": 1,
    "_strategy": "thunder_lightning_delay",
})

P1.append({
    "tier": 1,
    "question": "Can sound travel through outer space, where there is no air?",
    "answer": "No, because sound needs something like air or water to travel through",
    "choices": [
        "No, because sound needs something like air or water to travel through",
        "Yes, sound travels through space the same as light does",
        "Only if it is very loud, like a giant explosion",
        "Only on Tuesdays, when space is more open",
    ],
    "context": "Sound is a wave through matter — air, water, even steel. Space between planets is nearly empty, so there's nothing to wave. Movie space-explosions with booms? Not realistic.",
    "_pillar": 1,
    "_strategy": "no_sound_in_space",
})

P1.append({
    "tier": 1,
    "question": "A police siren sounds higher in pitch as it speeds toward you and lower as it speeds away. What's this effect called?",
    "answer": "The Doppler effect",
    "choices": [
        "The Doppler effect",
        "The Newton effect",
        "The Einstein effect",
        "The Edison effect",
    ],
    "context": "Christian Doppler explained it in 1842. Sound waves get squished in front of a moving source (higher pitch) and stretched behind (lower pitch). Astronomers use the same idea for light from moving galaxies.",
    "_pillar": 1,
    "_strategy": "doppler_effect_siren",
})

P1.append({
    "tier": 1,
    "question": "What makes a whistle sound higher than a foghorn?",
    "answer": "Its sound waves shake the air faster, more times each second",
    "choices": [
        "Its sound waves shake the air faster, more times each second",
        "The whistle is much bigger and heavier than the foghorn",
        "The whistle uses light air, while a foghorn uses heavy air",
        "The whistle is always closer to your ear than a foghorn is",
    ],
    "context": "Pitch comes from frequency — how many vibrations per second. Higher frequency = higher pitch. We measure it in hertz (Hz). Healthy human ears hear roughly 20 to 20,000 Hz.",
    "_pillar": 1,
    "_strategy": "pitch_frequency",
})

# --- Simple machines (6) ---

P1.append({
    "tier": 1,
    "question": "A seesaw on a playground is the simplest example of what kind of simple machine?",
    "answer": "A lever",
    "choices": ["A lever", "A pulley", "A wedge", "A screw"],
    "context": "A lever is a bar that turns on a fixed point called a fulcrum. Push one side down, the other rises. Crowbars, shovels, scissors, and your forearm at the elbow are all levers.",
    "_pillar": 1,
    "_strategy": "lever_seesaw",
})

P1.append({
    "tier": 1,
    "question": "A flagpole has a rope and a small grooved wheel at the top so you can raise the flag by pulling down. What simple machine is the wheel?",
    "answer": "A pulley",
    "choices": ["A pulley", "A lever", "A screw", "A wedge"],
    "context": "A pulley is a wheel with a rope grooved across it. It changes the direction of a force — pull down, the load goes up. Add more pulleys and the same load needs less force.",
    "_pillar": 1,
    "_strategy": "pulley_flagpole",
})

P1.append({
    "tier": 1,
    "question": "A ramp lets you push a heavy box up to a truck instead of lifting it straight up. What simple machine is a ramp?",
    "answer": "An inclined plane",
    "choices": [
        "An inclined plane",
        "A pulley",
        "A wedge",
        "A wheel-and-axle",
    ],
    "context": "An inclined plane (a ramp) lowers the force you need by stretching the work over a longer distance. Ancient Egyptians used long ramps to push stones up for the pyramids.",
    "_pillar": 1,
    "_strategy": "inclined_plane_ramp",
})

P1.append({
    "tier": 1,
    "question": "An axe blade splits wood by pushing it apart. The axe head is shaped like what simple machine?",
    "answer": "A wedge",
    "choices": ["A wedge", "A pulley", "A lever", "A screw"],
    "context": "A wedge is two inclined planes joined back-to-back. As it's driven in, it forces two surfaces apart. Knives, nails, chisels, and the front of a snowplow all work as wedges.",
    "_pillar": 1,
    "_strategy": "wedge_axe",
})

P1.append({
    "tier": 1,
    "question": "A jar lid spirals around when you twist it. The threads on the lid form what simple machine?",
    "answer": "A screw",
    "choices": ["A screw", "A wedge", "A pulley", "A lever"],
    "context": "A screw is an inclined plane wrapped around a cylinder. Every turn pulls the screw a little deeper. Jar lids, drill bits, and the lift in a corkscrew all use the screw.",
    "_pillar": 1,
    "_strategy": "screw_jar_lid",
})

P1.append({
    "tier": 1,
    "question": "A door knob turns a small bar to slide a bolt back. What kind of simple machine combines a big wheel with a small axle?",
    "answer": "A wheel-and-axle",
    "choices": [
        "A wheel-and-axle",
        "An inclined plane",
        "A wedge",
        "A lever-and-fulcrum",
    ],
    "context": "Turn the big wheel (the knob) by a small force, and the small axle turns with much more twisting strength. Screwdrivers, steering wheels, and faucet handles all use this trick.",
    "_pillar": 1,
    "_strategy": "wheel_and_axle_doorknob",
})

# --- Energy / temperature / heat (8) ---

P1.append({
    "tier": 1,
    "question": "When you rub your hands together fast on a cold day, your hands warm up. The motion energy turned into what?",
    "answer": "Heat energy",
    "choices": [
        "Heat energy",
        "Sound energy",
        "Light energy",
        "Electrical energy",
    ],
    "context": "Friction between your skin turns motion into heat. Energy can change form (motion to heat, heat to motion, light to heat) but is never created or destroyed. That's the law of conservation of energy.",
    "_pillar": 1,
    "_strategy": "friction_to_heat",
})

P1.append({
    "tier": 1,
    "question": "An ice cube melts on a warm counter. Heat moves from where to where?",
    "answer": "From the warm counter into the cold ice",
    "choices": [
        "From the warm counter into the cold ice",
        "From the cold ice into the warm counter",
        "From the ice into the room's lightbulb",
        "Heat does not move from one to the other",
    ],
    "context": "Heat always flows from hotter to colder. Once the ice cube and the counter reach the same temperature, the flow stops. The ice melts because energy enters the ice's molecules.",
    "_pillar": 1,
    "_strategy": "heat_flow_direction",
})

P1.append({
    "tier": 1,
    "question": "A solar panel turns sunlight into electricity. What kind of energy does the Sun deliver to the panel?",
    "answer": "Light energy",
    "choices": [
        "Light energy",
        "Sound energy",
        "Magnetic energy",
        "Chemical energy",
    ],
    "context": "Sunlight is a flow of light energy (and a bit of heat). Solar panels turn light directly into an electric current using thin layers of silicon. Plants do something similar with chlorophyll.",
    "_pillar": 1,
    "_strategy": "solar_energy",
})

P1.append({
    "tier": 1,
    "question": "A stretched rubber band has stored-up energy. When you let go, that stored energy turns into what?",
    "answer": "Motion energy, as the rubber band snaps back",
    "choices": [
        "Motion energy, as the rubber band snaps back",
        "Sound energy, but no movement at all",
        "Light energy, making the room slightly brighter",
        "No energy, since stretching just wastes it",
    ],
    "context": "A stretched or squeezed material holds 'elastic potential energy.' Release it and that energy becomes motion. Bows, slingshots, and trampolines all use this idea.",
    "_pillar": 1,
    "_strategy": "elastic_potential_energy",
})

P1.append({
    "tier": 1,
    "question": "A fresh battery stores what kind of energy until you use it?",
    "answer": "Chemical energy, which becomes electrical energy in use",
    "choices": [
        "Chemical energy, which becomes electrical energy in use",
        "Heat energy, which is why batteries always feel warm",
        "Light energy, stored from sitting in bright sunlight",
        "Sound energy, hidden inside until you shake them",
    ],
    "context": "Inside a battery, chemicals react and release electrons. Those electrons flow through a wire as electricity. When the chemicals are used up, the battery is 'dead' — energy spent.",
    "_pillar": 1,
    "_strategy": "battery_chemical_energy",
})

P1.append({
    "tier": 1,
    "question": "Water freezes into ice at what temperature on the Celsius scale?",
    "answer": "0 degrees Celsius",
    "choices": [
        "0 degrees Celsius",
        "100 degrees Celsius",
        "32 degrees Celsius",
        "-50 degrees Celsius",
    ],
    "context": "Anders Celsius designed his scale so water freezes at 0 and boils at 100 at sea-level air pressure. On the Fahrenheit scale, those points are 32 and 212.",
    "_pillar": 1,
    "_strategy": "freezing_point_celsius",
})

P1.append({
    "tier": 1,
    "question": "Water boils into steam at what temperature on the Celsius scale (at sea level)?",
    "answer": "100 degrees Celsius",
    "choices": [
        "100 degrees Celsius",
        "0 degrees Celsius",
        "212 degrees Celsius",
        "50 degrees Celsius",
    ],
    "context": "At normal sea-level air pressure, water boils at 100 C. Up a high mountain, where the air pushes down less, water boils at lower temperatures — so pasta cooks slower at altitude.",
    "_pillar": 1,
    "_strategy": "boiling_point_celsius",
})

P1.append({
    "tier": 1,
    "question": "A metal spoon left in a hot bowl of soup gets warm at the handle, even though only the bottom is in soup. What's this called?",
    "answer": "Conduction — heat traveling through the solid metal",
    "choices": [
        "Conduction — heat traveling through the solid metal",
        "Reflection — heat bouncing off the spoon",
        "Filtering — heat passing through tiny holes",
        "Magnetism — heat pulled by metal",
    ],
    "context": "In conduction, fast-moving molecules in the hot part of an object bump their neighbors, passing energy along. Metals are good conductors of heat; wood and plastic are poor conductors.",
    "_pillar": 1,
    "_strategy": "conduction_spoon",
})

# --- Density / balance / floating (5) ---

P1.append({
    "tier": 1,
    "question": "Drop same-size steel and wooden balls into water. Steel sinks; wood floats. Why?",
    "answer": "Steel is denser than water; wood is less dense",
    "choices": [
        "Steel is denser than water; wood is less dense",
        "Steel is colder, so water rejects it on touch",
        "Wood is magical and cannot sink in any water",
        "Steel and wood weigh exactly the same on Earth",
    ],
    "context": "Density is mass packed into a space. Less dense than water = floats. More dense = sinks. A steel ship floats because the overall shape (with air inside) is less dense than water.",
    "_pillar": 1,
    "_strategy": "density_floating",
})

P1.append({
    "tier": 1,
    "question": "Archimedes is said to have leapt from his bath shouting 'Eureka!' What had he realized?",
    "answer": "A thing in water pushes aside its own volume",
    "choices": [
        "A thing in water pushes aside its own volume",
        "Water boils faster when you yell at it loudly",
        "Heavy things always float and light ones sink",
        "Earth orbits the brightest stars at night",
    ],
    "context": "Around 250 BC Archimedes was asked to check if a king's crown was solid gold. He realized you could measure the crown's volume by how much water it pushes out — and from that, its density.",
    "_pillar": 1,
    "_strategy": "archimedes_eureka",
})

P1.append({
    "tier": 1,
    "question": "Two kids balance a seesaw; the smaller one sits farther from the middle. The lever lesson is?",
    "answer": "Distance from the center can make up for weight",
    "choices": [
        "Distance from the center can make up for weight",
        "The smaller kid has a hidden battery helping out",
        "Levers always lift no matter where you sit on one",
        "The smaller kid weighs more than the larger one",
    ],
    "context": "On a lever, weight x distance from the fulcrum has to match on both sides for balance. That's why a small person far from the middle can lift a big person sitting close in.",
    "_pillar": 1,
    "_strategy": "lever_balance",
})

P1.append({
    "tier": 1,
    "question": "A hot-air balloon floats up into the sky. Why?",
    "answer": "Warm air inside the balloon is less dense than the cool air around it",
    "choices": [
        "Warm air inside the balloon is less dense than the cool air around it",
        "The balloon is filled with smoke that lifts everything up",
        "Strong winds always push balloons upward in summer",
        "The Sun pulls hot-air balloons up like a magnet",
    ],
    "context": "Heat makes air molecules spread out — same air, more spread out = less dense. The lighter warm air rises, the cooler dense air sinks. That's also why hot air near a radiator drifts up.",
    "_pillar": 1,
    "_strategy": "hot_air_balloon",
})

P1.append({
    "tier": 1,
    "question": "Why does a giant cruise ship made of heavy steel float on water?",
    "answer": "Its overall shape, with lots of air inside, is less dense than water",
    "choices": [
        "Its overall shape, with lots of air inside, is less dense than water",
        "Ocean water is much heavier than ordinary fresh water",
        "Cruise ships have hidden engines that lift them up",
        "Steel becomes lighter as soon as it touches the sea",
    ],
    "context": "Density is mass divided by volume. A solid steel cube sinks, but a steel ship shaped with hollow rooms inside spreads the same steel over much more volume — average density drops below water's.",
    "_pillar": 1,
    "_strategy": "ship_floats_density",
})

# --- Earth-and-space-adjacent physics (3) ---

P1.append({
    "tier": 1,
    "question": "Long ago, people thought the Sun moved around Earth. Which astronomer in the 1500s argued that Earth actually moves around the Sun?",
    "answer": "Nicolaus Copernicus",
    "choices": [
        "Nicolaus Copernicus",
        "Albert Einstein",
        "Thomas Edison",
        "Benjamin Franklin",
    ],
    "context": "Copernicus wrote *On the Revolutions of the Heavenly Spheres* in 1543. His sun-centered model was developed further by Kepler and Galileo, and confirmed by careful observations over the next century.",
    "_pillar": 1,
    "_strategy": "copernicus_heliocentric",
})

P1.append({
    "tier": 1,
    "question": "Roughly how long does it take Earth to spin around once on its axis?",
    "answer": "About 24 hours, which is one day",
    "choices": [
        "About 24 hours, which is one day",
        "About 30 days, which is one month",
        "About 1 year, which is one orbit",
        "About 60 seconds, which is one minute",
    ],
    "context": "Earth's spin is what makes the Sun rise and set. One full spin = one day. Earth also takes about 365 days to circle the Sun, which is one year.",
    "_pillar": 1,
    "_strategy": "earth_rotation_day",
})

P1.append({
    "tier": 1,
    "question": "Why are summer days warmer than winter days where you live?",
    "answer": "Earth is tilted, so in summer your part faces the Sun more directly",
    "choices": [
        "Earth is tilted, so in summer your part faces the Sun more directly",
        "Earth gets much closer to the Sun in summer than winter",
        "The Sun burns hotter on summer days than on winter days",
        "Clouds always block the Sun more in the winter months",
    ],
    "context": "Earth's axis is tilted about 23.5 degrees. In your summer, your hemisphere leans toward the Sun — more direct light, longer days, warmer weather. In winter, it leans away.",
    "_pillar": 1,
    "_strategy": "seasons_tilt",
})


# ============================================================================
# PILLAR 2 — CHEMISTRY (40)
# Mixing, dissolving, states of matter, rusting, burning, taste,
# element symbols (gold/silver/iron/oxygen), acid-base basics, smells
# ============================================================================

P2 = []

# --- States of matter (5) ---

P2.append({
    "tier": 1,
    "question": "Water can be ice, liquid water, or steam. What are these three forms called?",
    "answer": "Solid, liquid, and gas — three states of matter",
    "choices": [
        "Solid, liquid, and gas — three states of matter",
        "Cold, cool, and warm — three temperatures",
        "Hard, soft, and bouncy — three textures",
        "Heavy, medium, and light — three weights",
    ],
    "context": "The same molecules (H2O) make all three. In a solid (ice), molecules sit in a tight pattern. In a liquid, they slide around. In a gas (steam), they fly free.",
    "_pillar": 2,
    "_strategy": "three_states_of_matter",
})

P2.append({
    "tier": 1,
    "question": "An ice cube melts on the kitchen counter. What change is happening to the water molecules?",
    "answer": "They speed up and break out of their solid pattern",
    "choices": [
        "They speed up and break out of their solid pattern",
        "They get larger and turn into new kinds of atoms",
        "They split into smaller, simpler molecules",
        "They disappear, since water vanishes when it melts",
    ],
    "context": "Heat is extra energy of motion. Add enough and ice's neat crystal pattern falls apart — the water becomes liquid. Add more and you get gas. The molecules don't change, just how they move.",
    "_pillar": 2,
    "_strategy": "melting_molecules",
})

P2.append({
    "tier": 1,
    "question": "A puddle in the driveway slowly disappears on a warm day. Where does the water go?",
    "answer": "It evaporates into the air as invisible water vapor",
    "choices": [
        "It evaporates into the air as invisible water vapor",
        "It soaks into your shoes and stays trapped there",
        "It turns into a new substance, no longer water",
        "It sinks straight down and freezes underground",
    ],
    "context": "Even below the boiling point, fastest water molecules can escape the liquid into the air. The puddle gets smaller. Later that vapor may join clouds and fall as rain — the water cycle.",
    "_pillar": 2,
    "_strategy": "evaporation_puddle",
})

P2.append({
    "tier": 1,
    "question": "A bathroom mirror fogs up during a hot shower. Where does the water on the mirror come from?",
    "answer": "Water vapor in warm air condenses on the cool mirror",
    "choices": [
        "Water vapor in warm air condenses on the cool mirror",
        "The mirror itself makes water when it gets warm",
        "Steam pipes in the wall leak straight onto it",
        "The mirror grows water from tiny seeds in glass",
    ],
    "context": "Hot shower water evaporates into the air. When warm, moist air touches the cool mirror, the water vapor slows down and turns back to liquid. That's condensation — the opposite of evaporation.",
    "_pillar": 2,
    "_strategy": "condensation_mirror",
})

P2.append({
    "tier": 1,
    "question": "Dry ice is a strange solid that doesn't melt — it goes straight from solid to gas. What ordinary substance is dry ice made of?",
    "answer": "Frozen carbon dioxide",
    "choices": [
        "Frozen carbon dioxide",
        "Frozen pure water, but harder",
        "Frozen pieces of fluffy snow",
        "Frozen blocks of helium gas",
    ],
    "context": "Dry ice is solid CO2 at about -78 C. At room temperature it 'sublimates' — turns straight into a gas with no liquid in between. The fog from dry ice is real water vapor pulled out of the air.",
    "_pillar": 2,
    "_strategy": "dry_ice_sublimation",
})

# --- Element symbols (8) ---

P2.append({
    "tier": 1,
    "question": "Gold doesn't tarnish — old gold coins pulled from sunken ships come up shiny. What's the chemical symbol for gold?",
    "answer": "Au",
    "choices": ["Au", "Go", "Gd", "Gl"],
    "context": "Au comes from Latin 'aurum,' meaning shining dawn. Gold resists rust and tarnish, which is why it has been used for coins, jewelry, and electronics contacts for thousands of years.",
    "_pillar": 2,
    "_strategy": "gold_symbol_au",
})

P2.append({
    "tier": 1,
    "question": "A polished silver spoon eventually goes dark and dull. What's the chemical symbol for silver?",
    "answer": "Ag",
    "choices": ["Ag", "Si", "Sl", "Sv"],
    "context": "Ag comes from Latin 'argentum.' Silver is the best conductor of electricity of any metal but tarnishes when sulfur in the air combines with it to make black silver sulfide.",
    "_pillar": 2,
    "_strategy": "silver_symbol_ag",
})

P2.append({
    "tier": 1,
    "question": "An iron nail left outside gets red-brown rust on it. What's the chemical symbol for iron?",
    "answer": "Fe",
    "choices": ["Fe", "Ir", "In", "Io"],
    "context": "Fe comes from Latin 'ferrum,' meaning iron. Iron is the main ingredient in steel and in your red blood cells, where it carries oxygen.",
    "_pillar": 2,
    "_strategy": "iron_symbol_fe",
})

P2.append({
    "tier": 1,
    "question": "Without this element, no fire burns and no animal breathes. Which element are we talking about, and what's its symbol?",
    "answer": "Oxygen — symbol O",
    "choices": [
        "Oxygen — symbol O",
        "Helium — symbol He",
        "Argon — symbol Ar",
        "Carbon — symbol C",
    ],
    "context": "Oxygen is element number 8. About 21% of the air you breathe is oxygen gas (O2). Plants release it during photosynthesis. Antoine Lavoisier gave it its modern name in the 1770s.",
    "_pillar": 2,
    "_strategy": "oxygen_symbol_O",
})

P2.append({
    "tier": 1,
    "question": "The lightest element, the most common in the universe, is hydrogen. What's its chemical symbol?",
    "answer": "H, for element number one",
    "choices": [
        "H, for element number one",
        "He, the symbol for helium",
        "Hd, a symbol that isn't used",
        "Hy, the old Greek word root",
    ],
    "context": "Hydrogen is element number 1 — just one proton, one electron. Stars are mostly hydrogen, fusing into helium. Water (H2O) has two hydrogens for every oxygen.",
    "_pillar": 2,
    "_strategy": "hydrogen_symbol_H",
})

P2.append({
    "tier": 1,
    "question": "Party balloons that float up are filled with what light gas, symbol He?",
    "answer": "Helium",
    "choices": [
        "Helium",
        "Hydrogen",
        "Heavium",
        "Helonite",
    ],
    "context": "Helium is the second-lightest element, after hydrogen. It does not burn, so it is safer than hydrogen for balloons. Most helium on Earth comes from natural gas wells, where it builds up underground.",
    "_pillar": 2,
    "_strategy": "helium_balloons",
})

P2.append({
    "tier": 1,
    "question": "Table salt is made of sodium and chlorine joined together. What's sodium's chemical symbol?",
    "answer": "Na",
    "choices": ["Na", "So", "Sd", "Sa"],
    "context": "Na comes from Latin 'natrium.' Sodium by itself is a soft silver metal that explodes in water — but joined to chlorine it makes harmless salt (NaCl), which you eat every day.",
    "_pillar": 2,
    "_strategy": "sodium_symbol_na",
})

P2.append({
    "tier": 1,
    "question": "Old thermometers had a silvery liquid metal that rolled into little balls when spilled. Its symbol is Hg. What's it called?",
    "answer": "Mercury",
    "choices": [
        "Mercury",
        "Magnesium",
        "Manganese",
        "Mendelevium",
    ],
    "context": "Hg comes from Latin 'hydrargyrum,' meaning liquid silver. Mercury is the only metal that's liquid at room temperature. It is also toxic, so modern thermometers usually use red-colored alcohol instead.",
    "_pillar": 2,
    "_strategy": "mercury_symbol_hg",
})

# --- Atoms / elements basics (4) ---

P2.append({
    "tier": 1,
    "question": "Everything around you is made of tiny building blocks too small to see. What are they called?",
    "answer": "Atoms",
    "choices": ["Atoms", "Cells", "Crystals", "Sparks"],
    "context": "Atoms are the smallest pieces of an element. They join together in different ways to make all the materials in the world — water, air, rocks, trees, you.",
    "_pillar": 2,
    "_strategy": "what_is_atom",
})

P2.append({
    "tier": 1,
    "question": "A water molecule is written H2O. What does the H2O mean?",
    "answer": "Two hydrogen atoms joined to one oxygen atom",
    "choices": [
        "Two hydrogen atoms joined to one oxygen atom",
        "Twenty hydrogen atoms with no oxygen at all",
        "Half hydrogen and half oxygen, all mixed up",
        "One H followed by one O, in random order",
    ],
    "context": "A molecule is a group of atoms bonded together. H2O is the recipe for water: 2 hydrogens + 1 oxygen. Every drop of water you drink is made of trillions and trillions of H2O molecules.",
    "_pillar": 2,
    "_strategy": "h2o_meaning",
})

P2.append({
    "tier": 1,
    "question": "A big chart on every science classroom wall lists all the known elements in rows and columns. What's it called?",
    "answer": "The periodic table",
    "choices": [
        "The periodic table",
        "The molecular map",
        "The atomic almanac",
        "The chemical chart of life",
    ],
    "context": "Dmitri Mendeleev arranged the elements in 1869 by their atomic weight and chemical properties. His table even left gaps for elements not yet found — and most of those gaps were later filled in.",
    "_pillar": 2,
    "_strategy": "periodic_table_intro",
})

P2.append({
    "tier": 1,
    "question": "Inside an atom, what sits at the very center?",
    "answer": "A nucleus made of protons and neutrons",
    "choices": [
        "A nucleus made of protons and neutrons",
        "A tiny ball of pure shiny gold dust",
        "A small picture of the whole atom",
        "Nothing at all, since atoms are empty",
    ],
    "context": "An atom has a tiny dense nucleus (protons + neutrons) in the middle, with electrons buzzing around the outside. Protons carry positive charge, electrons negative. Same numbers usually balance out.",
    "_pillar": 2,
    "_strategy": "atomic_nucleus",
})

# --- Mixing / dissolving (5) ---

P2.append({
    "tier": 1,
    "question": "Stir a spoonful of sugar into warm water and the sugar disappears. Where did the sugar go?",
    "answer": "It dissolved, breaking apart into the water",
    "choices": [
        "It dissolved, breaking apart into the water",
        "It turned into pure energy and floated away",
        "It vanished forever and will never return",
        "It changed into salt and sank to the bottom",
    ],
    "context": "Dissolving spreads the sugar molecules through the water. You can't see them anymore, but they're still there — taste it, and you'll know. Boil the water away and the sugar reappears.",
    "_pillar": 2,
    "_strategy": "dissolving_sugar",
})

P2.append({
    "tier": 1,
    "question": "Pour oil into a glass of water. The oil floats on top and refuses to mix. Why?",
    "answer": "Water and oil simply do not dissolve in each other",
    "choices": [
        "Water and oil simply do not dissolve in each other",
        "Oil is heavier than water, so it sinks to the floor",
        "Oil reacts with water and explodes on first contact",
        "The glass is dirty and is keeping the two apart",
    ],
    "context": "Water molecules pull on each other strongly. Oil molecules don't fit into that pull, so they stay separate. Soap can join the two by sticking to both — that's how soap cleans greasy plates.",
    "_pillar": 2,
    "_strategy": "oil_water_unmixed",
})

P2.append({
    "tier": 1,
    "question": "A mixture of sand and water is easy to separate. How could you get the sand back out?",
    "answer": "Pour the mixture through a filter, like a paper coffee filter",
    "choices": [
        "Pour the mixture through a filter, like a paper coffee filter",
        "Add salt until the sand turns into liquid too",
        "Stir very fast and the sand will become water",
        "Heat the water until the sand changes into oxygen",
    ],
    "context": "Sand doesn't dissolve in water — the grains are too big. A filter traps the sand on top and lets the water through. Boiling would leave the sand behind too, since water evaporates and sand doesn't.",
    "_pillar": 2,
    "_strategy": "filtering_sand_water",
})

P2.append({
    "tier": 1,
    "question": "Stir salt into water, then boil all the water away. What's left behind in the pot?",
    "answer": "The salt, in a thin white crust",
    "choices": [
        "The salt, in a thin white crust",
        "Nothing, since salt also boils away",
        "Pure sugar in the bottom of the pot",
        "A small puddle of pure clean water",
    ],
    "context": "Water has a much lower boiling point than salt. When you heat salt-water, only the water becomes steam. Salt stays behind as a solid. That's how sea-salt is made by evaporating ocean water.",
    "_pillar": 2,
    "_strategy": "evaporating_salt_water",
})

P2.append({
    "tier": 1,
    "question": "Why do sugar crystals dissolve faster in hot tea than in cold tea?",
    "answer": "Hot water molecules move faster, breaking the sugar apart sooner",
    "choices": [
        "Hot water molecules move faster, breaking the sugar apart sooner",
        "Hot tea has more sugar inside it to start with",
        "Cold tea makes sugar grow into larger crystals",
        "Sugar refuses to dissolve in any cold liquid at all",
    ],
    "context": "Higher temperature = faster-moving molecules. Hot water molecules bash into sugar harder and more often, pulling the sugar apart and spreading it through the drink quickly.",
    "_pillar": 2,
    "_strategy": "hot_water_dissolves_faster",
})

# --- Rusting / burning / chemical change (6) ---

P2.append({
    "tier": 1,
    "question": "An iron bike left in the rain grows orange-brown crust. What's happening to the iron?",
    "answer": "It is rusting, joining with oxygen and water",
    "choices": [
        "It is rusting, joining with oxygen and water",
        "It is dirty from the dust that lands on it",
        "Sunlight is staining the iron a new color",
        "The metal is melting at room temperature",
    ],
    "context": "Rust is iron oxide. When iron meets oxygen and water for long enough, the atoms combine to make a new flaky material. That's a chemical change — different stuff than what you started with.",
    "_pillar": 2,
    "_strategy": "rusting_iron",
})

P2.append({
    "tier": 1,
    "question": "Burning a log is what kind of change?",
    "answer": "A chemical change, because new substances are made",
    "choices": [
        "A chemical change, because new substances are made",
        "A physical change, since nothing new is made",
        "Neither, since burning isn't really a change",
        "A magnetic change, since fire pulls on iron",
    ],
    "context": "Burning a log makes ash, smoke, and gases like carbon dioxide and water vapor — things that weren't there before. New substances mean a chemical change. Melting ice, by contrast, is a physical change.",
    "_pillar": 2,
    "_strategy": "burning_chemical_change",
})

P2.append({
    "tier": 1,
    "question": "What gas does a candle flame need from the air to keep burning?",
    "answer": "Oxygen, the gas we breathe in",
    "choices": [
        "Oxygen, the gas we breathe in",
        "Helium, the lightweight balloon gas",
        "Argon, an unreactive party gas",
        "Nitrogen, the main gas in our air",
    ],
    "context": "A flame is wax combining quickly with oxygen, giving off heat and light. Put a glass jar over a candle and once the oxygen inside is used up, the flame goes out — even with wax left.",
    "_pillar": 2,
    "_strategy": "fire_needs_oxygen",
})

P2.append({
    "tier": 1,
    "question": "Why does pouring water on a small campfire put it out?",
    "answer": "Water cools the wood and cuts off oxygen from the fire",
    "choices": [
        "Water cools the wood and cuts off oxygen from the fire",
        "Water is afraid of fire, so the fire gives up",
        "Water adds extra fuel, so the fire shrinks itself",
        "Water turns into rocks that smother the flame",
    ],
    "context": "A fire needs three things: fuel, oxygen, and heat. Water steals heat as it boils and blocks oxygen from reaching the fuel. Take any one of the three away and the fire dies.",
    "_pillar": 2,
    "_strategy": "fire_triangle",
})

P2.append({
    "tier": 1,
    "question": "Cut a fresh apple in half and leave it for an hour. The cut sides turn brown. What caused that?",
    "answer": "Oxygen in the air reacting with chemicals in the apple",
    "choices": [
        "Oxygen in the air reacting with chemicals in the apple",
        "The apple bleeding because it was hurt",
        "The light alone has darkened the apple",
        "A coating of brown sugar already inside it",
    ],
    "context": "When you cut an apple, oxygen meets enzymes in its flesh and starts a slow chemical change called oxidation. Lemon juice slows the browning — its acid blocks the enzyme.",
    "_pillar": 2,
    "_strategy": "apple_browning",
})

P2.append({
    "tier": 1,
    "question": "A loaf of fresh bread left out for a week grows fuzzy green-and-black spots. What are those spots?",
    "answer": "Mold, a tiny living fungus growing on the bread",
    "choices": [
        "Mold, a tiny living fungus growing on the bread",
        "A new color the bread chose by itself",
        "Plain dust from the kitchen settling on top",
        "The bread fading from sunlight over time",
    ],
    "context": "Mold spores are floating in air all the time. They land on bread (or fruit, or old food), grow, and digest the bread — leaving behind fuzzy patches. Refrigeration slows it; freezing stops it.",
    "_pillar": 2,
    "_strategy": "bread_mold",
})

# --- Acids and bases / taste (5) ---

P2.append({
    "tier": 1,
    "question": "Lemon juice and vinegar are both sour. Sour foods like these are usually what?",
    "answer": "Acids",
    "choices": [
        "Acids",
        "Bases",
        "Salts",
        "Pure water",
    ],
    "context": "Sour taste comes from acids — citric acid in lemons, acetic acid in vinegar. Acids release hydrogen particles in water. Soaps and baking soda are the opposite: bases (also called alkalis).",
    "_pillar": 2,
    "_strategy": "sour_means_acid",
})

P2.append({
    "tier": 1,
    "question": "A scale from 0 to 14 tells us how acidic or basic something is. What's it called?",
    "answer": "The pH scale",
    "choices": [
        "The pH scale",
        "The HQ scale",
        "The OK scale",
        "The Mz scale",
    ],
    "context": "On the pH scale, 7 is neutral (pure water). Below 7 is acidic — lemon juice is around 2, stomach acid near 1. Above 7 is basic — baking soda about 9, household ammonia about 11.",
    "_pillar": 2,
    "_strategy": "ph_scale_intro",
})

P2.append({
    "tier": 1,
    "question": "Mix baking soda with vinegar and the mixture fizzes and bubbles. What gas is being made?",
    "answer": "Carbon dioxide gas, the same gas in fizzy soda",
    "choices": [
        "Carbon dioxide gas, the same gas in fizzy soda",
        "Pure oxygen of the kind that animals breathe in",
        "Hot smoke of the kind a burning fire makes",
        "Boiling steam of the kind a kettle puts out",
    ],
    "context": "Vinegar (an acid) and baking soda (a base) react. They make water, a salt, and carbon dioxide gas — the same gas in fizzy soda and the bubbles of bread dough. This is a classic kitchen volcano.",
    "_pillar": 2,
    "_strategy": "baking_soda_vinegar",
})

P2.append({
    "tier": 1,
    "question": "Your tongue has bumps that pick up tastes. Roughly how many basic tastes can humans recognize?",
    "answer": "Five — sweet, sour, salty, bitter, and savory (umami)",
    "choices": [
        "Five — sweet, sour, salty, bitter, and savory (umami)",
        "Just two — sweet and sour, nothing else",
        "Hundreds — one for each food you've ever eaten",
        "None — taste is actually all in your imagination",
    ],
    "context": "For a long time scientists said there were four basic tastes. Japanese chemist Kikunae Ikeda identified a fifth in 1908: umami, the savory taste of broth and parmesan. Most flavor we sense is actually smell.",
    "_pillar": 2,
    "_strategy": "five_basic_tastes",
})

P2.append({
    "tier": 1,
    "question": "When you have a stuffy nose from a cold, food often tastes bland. Why?",
    "answer": "Most flavor comes from smell, and a blocked nose can't smell well",
    "choices": [
        "Most flavor comes from smell, and a blocked nose can't smell well",
        "Cold germs eat the flavor out of the food first",
        "The mouth shuts off taste buds when you're sick",
        "Sick people lose their hunger and forget how to taste",
    ],
    "context": "Your tongue picks up about five basic tastes; your nose picks up thousands of smells. Together they make 'flavor.' Pinch your nose and bite an apple — it tastes a lot like an onion or a potato.",
    "_pillar": 2,
    "_strategy": "smell_makes_flavor",
})

# --- Smells / matter properties (4) ---

P2.append({
    "tier": 1,
    "question": "Cookies baking in the oven smell good across the house. What is actually reaching your nose?",
    "answer": "Tiny molecules of the cookie floating in the air",
    "choices": [
        "Tiny molecules of the cookie floating in the air",
        "A magic invisible ray sent out by warm food",
        "Sound waves from the oven shaped like cookies",
        "Light bouncing from the cookies into your nose",
    ],
    "context": "Heat speeds up molecules in food, and the lightest ones break free into the air. They drift everywhere and your nose picks them up. That's why a hot pizza smells stronger than a cold one.",
    "_pillar": 2,
    "_strategy": "smell_is_molecules",
})

P2.append({
    "tier": 1,
    "question": "A block of ice and a cup of water have the same mass. Which takes up more space?",
    "answer": "The ice, since frozen water is less dense than liquid",
    "choices": [
        "The ice, since frozen water is less dense than liquid",
        "The water, because liquids always take more room",
        "They take up exactly the same amount of space",
        "Neither, because both shrink down to almost nothing",
    ],
    "context": "Water is unusual: it expands when it freezes. That's why ice cubes float in your drink, and why pipes can crack in winter. Most other substances shrink when they go from liquid to solid.",
    "_pillar": 2,
    "_strategy": "ice_less_dense_than_water",
})

P2.append({
    "tier": 1,
    "question": "Crack a glow stick and the inside lights up without any electricity or fire. What's making the glow?",
    "answer": "A chemical reaction between two chemicals inside the stick",
    "choices": [
        "A chemical reaction between two chemicals inside the stick",
        "A tiny lightbulb hidden at one end of the stick",
        "Sunlight stored from earlier in the day",
        "A piece of glowing magnet sealed inside",
    ],
    "context": "Bending the glow stick breaks an inner tube. Two chemicals mix, react, and release energy as light — without any heat. Fireflies use a similar chemical trick called bioluminescence.",
    "_pillar": 2,
    "_strategy": "glow_stick_chemistry",
})

P2.append({
    "tier": 1,
    "question": "A diamond is one of the hardest materials on Earth. What element are diamonds made of?",
    "answer": "Carbon",
    "choices": [
        "Carbon",
        "Iron",
        "Gold",
        "Silver",
    ],
    "context": "Diamonds are pure carbon, with atoms locked in a 3D pattern under enormous pressure deep underground. Pencil 'lead' is also pure carbon — same atoms, different pattern (graphite), much softer.",
    "_pillar": 2,
    "_strategy": "diamond_is_carbon",
})

# --- Carbon dioxide / air composition (3) ---

P2.append({
    "tier": 1,
    "question": "The air you breathe is mostly which gas?",
    "answer": "Nitrogen",
    "choices": [
        "Nitrogen",
        "Oxygen",
        "Hydrogen",
        "Carbon dioxide",
    ],
    "context": "Earth's atmosphere is about 78% nitrogen, 21% oxygen, with small amounts of argon, carbon dioxide, and water vapor. Our bodies use only the oxygen — the nitrogen passes through unchanged.",
    "_pillar": 2,
    "_strategy": "air_mostly_nitrogen",
})

P2.append({
    "tier": 1,
    "question": "Open a warm soda and it goes flat very fast. Why?",
    "answer": "Carbon dioxide leaves warm liquid faster than cold",
    "choices": [
        "Carbon dioxide leaves warm liquid faster than cold",
        "The soda gets quieter in warm air and stops fizzing",
        "Warm sodas turn into different drinks altogether",
        "Sugar in the soda eats the bubbles when it warms",
    ],
    "context": "Cold liquids hold dissolved gas better than warm ones. Warm soda gives up its CO2 quickly into the air — gone within minutes. Soda is bottled cold and under pressure so the gas stays trapped.",
    "_pillar": 2,
    "_strategy": "warm_soda_flat",
})

P2.append({
    "tier": 1,
    "question": "You breathe in oxygen. What gas do you mostly breathe OUT?",
    "answer": "Carbon dioxide, a waste gas from your cells",
    "choices": [
        "Carbon dioxide, a waste gas from your cells",
        "Pure helium, a very light party balloon gas",
        "Hydrogen, the lightest element of all in air",
        "Methane, the gas that comes from old swamps",
    ],
    "context": "Your cells use oxygen to release energy from food and make carbon dioxide as a waste gas. Blood carries the CO2 back to your lungs and you breathe it out. Plants then turn it back into oxygen.",
    "_pillar": 2,
    "_strategy": "breathe_out_co2",
})


# ============================================================================
# PILLAR 3 — BIOLOGY (50)
# Cells, DNA basics, plants (photosynthesis), ecology (predator-prey, food
# chain), anatomy basics, life cycles (tadpole/butterfly), animal facts
# ============================================================================

P3 = []

# --- Cells (5) ---

P3.append({
    "tier": 1,
    "question": "Every plant and animal is built out of tiny living building blocks. What are they called?",
    "answer": "Cells",
    "choices": ["Cells", "Atoms", "Crystals", "Pixels"],
    "context": "Cells are the smallest units of life. A blue whale has trillions; a tiny moss has fewer. They were first seen in 1665 when Robert Hooke looked at a slice of cork through a microscope.",
    "_pillar": 3,
    "_strategy": "cells_building_blocks",
})

P3.append({
    "tier": 1,
    "question": "English scientist Robert Hooke first used the word 'cell' in 1665 when he looked at something through an early microscope. What was he looking at?",
    "answer": "Thin slices of cork from a tree",
    "choices": [
        "Thin slices of cork from a tree",
        "Drops of milk under a hot lamp",
        "Sand grains from a sea shore",
        "Pieces of his own fingernail",
    ],
    "context": "Hooke saw small empty rooms in cork that reminded him of monks' rooms — 'cells' in Latin. He published the drawings in *Micrographia* in 1665, the first famous microscope book.",
    "_pillar": 3,
    "_strategy": "hooke_cork_cells",
})

P3.append({
    "tier": 1,
    "question": "Inside almost every animal cell is a small round center that holds the cell's DNA. What's it called?",
    "answer": "The nucleus",
    "choices": [
        "The nucleus",
        "The shell",
        "The leaflet",
        "The seedling",
    ],
    "context": "The nucleus is the cell's control room. It holds DNA, the instruction book for building proteins. Bacteria have no nucleus — their DNA floats freely inside the cell.",
    "_pillar": 3,
    "_strategy": "nucleus_in_cell",
})

P3.append({
    "tier": 1,
    "question": "Plants and animal cells both have an outer skin that lets things in and out. What's this skin called?",
    "answer": "The cell membrane",
    "choices": [
        "The cell membrane",
        "The cell skeleton",
        "The cell stomach",
        "The cell pillow",
    ],
    "context": "The cell membrane is a thin layer that decides what passes in (food, oxygen) and what passes out (waste). Plant cells also have a stiff outer cell wall just outside the membrane.",
    "_pillar": 3,
    "_strategy": "cell_membrane",
})

P3.append({
    "tier": 1,
    "question": "A single bacterium is alive — it eats, grows, and copies itself. How many cells is one bacterium made of?",
    "answer": "One single cell that does everything",
    "choices": [
        "One single cell that does everything",
        "About ten cells working in a team",
        "About a hundred cells in a tiny ball",
        "About a thousand cells in a chain",
    ],
    "context": "Bacteria are 'unicellular' — one cell does everything. Bigger living things are 'multicellular' and have many specialized cell types. The total bacteria on Earth easily outnumber every other living thing.",
    "_pillar": 3,
    "_strategy": "bacterium_one_cell",
})

# --- DNA / inheritance (5) ---

P3.append({
    "tier": 1,
    "question": "Inside every cell is a long, twisted ladder-shaped molecule that carries the instructions for the whole body. What's it called?",
    "answer": "DNA",
    "choices": [
        "DNA",
        "RNA-snake",
        "BLT",
        "LCD",
    ],
    "context": "DNA stands for deoxyribonucleic acid. James Watson, Francis Crick, and Rosalind Franklin showed in 1953 that DNA is shaped like a double helix — two strands twisted around each other.",
    "_pillar": 3,
    "_strategy": "dna_in_every_cell",
})

P3.append({
    "tier": 1,
    "question": "DNA is shaped like a twisted ladder. What name do scientists give that shape?",
    "answer": "A double helix",
    "choices": [
        "A double helix",
        "A square crystal",
        "A flat ribbon",
        "A spinning top",
    ],
    "context": "Two long strands of DNA twist around each other. The 'rungs' of the ladder are pairs of chemical bases (A with T, G with C). Photo 51, an X-ray image by Rosalind Franklin, showed the helix shape.",
    "_pillar": 3,
    "_strategy": "double_helix_shape",
})

P3.append({
    "tier": 1,
    "question": "Why do kids often look a little like their parents?",
    "answer": "Kids inherit half their DNA from each parent",
    "choices": [
        "Kids inherit half their DNA from each parent",
        "Kids decide who to look like when they're born",
        "Living near each other slowly changes their faces",
        "Photos of the family slowly print onto a baby's face",
    ],
    "context": "Each parent gives half of their DNA to their child. That DNA shapes eye color, hair texture, height tendencies, and more. Mendel worked out the basic rules with pea plants in the 1860s.",
    "_pillar": 3,
    "_strategy": "inheritance_dna",
})

P3.append({
    "tier": 1,
    "question": "An Austrian monk named Gregor Mendel found the first rules of inheritance in the 1860s. What did he grow in his monastery garden?",
    "answer": "Pea plants",
    "choices": [
        "Pea plants",
        "Sunflowers",
        "Apple trees",
        "Tomato vines",
    ],
    "context": "Mendel grew thousands of pea plants and tracked which traits (tall/short, smooth/wrinkled) passed to the next generation. His 1866 paper was ignored for over 30 years before being rediscovered.",
    "_pillar": 3,
    "_strategy": "mendel_pea_plants",
})

P3.append({
    "tier": 1,
    "question": "DNA's twisted-ladder shape was figured out in 1953 by three scientists. One of them is well known for her X-ray photo called Photo 51. Who was she?",
    "answer": "Rosalind Franklin",
    "choices": [
        "Rosalind Franklin",
        "Marie Curie",
        "Florence Nightingale",
        "Jane Goodall",
    ],
    "context": "Franklin's X-ray crystal images of DNA were essential evidence. She died of cancer in 1958, four years before the Nobel Prize for the discovery went to Watson, Crick, and Wilkins.",
    "_pillar": 3,
    "_strategy": "rosalind_franklin_photo51",
})

# --- Plants / photosynthesis (7) ---

P3.append({
    "tier": 1,
    "question": "Plants make their own food using sunlight, water, and a gas pulled in from the air. Which gas is it?",
    "answer": "Carbon dioxide, the same gas we exhale",
    "choices": [
        "Carbon dioxide, the same gas we exhale",
        "Oxygen, the same gas that we breathe in",
        "Helium, the gas inside floating balloons",
        "Hydrogen, the lightest element of all",
    ],
    "context": "Plants pull carbon dioxide from the air through tiny pores in their leaves. Combined with water and sunlight, they make sugar to live on, and release oxygen back into the air.",
    "_pillar": 3,
    "_strategy": "plants_use_co2",
})

P3.append({
    "tier": 1,
    "question": "The big word for how plants make their own food from sunlight, water, and carbon dioxide is what?",
    "answer": "Photosynthesis",
    "choices": [
        "Photosynthesis",
        "Telephotosis",
        "Aerodynamis",
        "Pollinosis",
    ],
    "context": "Photosynthesis means 'putting together with light.' Plants use the green pigment chlorophyll to capture sunlight energy, then build sugar from CO2 and water. Almost all life depends on this trick.",
    "_pillar": 3,
    "_strategy": "photosynthesis_word",
})

P3.append({
    "tier": 1,
    "question": "Plants are green because of a special pigment inside their leaves. What's it called?",
    "answer": "Chlorophyll",
    "choices": [
        "Chlorophyll",
        "Plantoflavin",
        "Greentinin",
        "Leafocyte",
    ],
    "context": "Chlorophyll absorbs red and blue light for photosynthesis and reflects green light — which is why leaves look green. In autumn, chlorophyll breaks down and other pigments (yellow, orange, red) show through.",
    "_pillar": 3,
    "_strategy": "chlorophyll_green",
})

P3.append({
    "tier": 1,
    "question": "Photosynthesis releases one gas into the air that almost every animal must breathe. Which gas?",
    "answer": "Oxygen, the gas plants give back to us",
    "choices": [
        "Oxygen, the gas plants give back to us",
        "Nitrogen, the gas that makes up most air",
        "Helium, the gas that lifts party balloons",
        "Argon, an unreactive gas in our atmosphere",
    ],
    "context": "Photosynthesis is the reason Earth's atmosphere has lots of oxygen. Long ago, single-celled cyanobacteria began making oxygen, and the whole planet's air changed over millions of years.",
    "_pillar": 3,
    "_strategy": "plants_make_oxygen",
})

P3.append({
    "tier": 1,
    "question": "A sunflower turns its head to face the Sun across the day. Plants growing toward light is called what?",
    "answer": "Phototropism",
    "choices": [
        "Phototropism",
        "Photosynthesis",
        "Pollination",
        "Pollination-time",
    ],
    "context": "Plants don't have eyes, but they sense light direction. Cells on the shaded side grow a little faster, bending the stem toward the Sun. Roots show the opposite — they grow away from light.",
    "_pillar": 3,
    "_strategy": "phototropism_sunflowers",
})

P3.append({
    "tier": 1,
    "question": "A new plant grows out of a seed. What part of the seed comes out of the ground first?",
    "answer": "The root, growing down into the soil",
    "choices": [
        "The root, growing down into the soil",
        "The leaves, before any roots at all",
        "The flower, with no roots or stem",
        "The seed coat, peeled off in one piece",
    ],
    "context": "When a seed soaks up water, the root pushes out first — anchoring the plant and reaching for water. Then a tiny shoot pushes up and unfolds into leaves. Tropism guides each in the right direction.",
    "_pillar": 3,
    "_strategy": "seed_germination_root_first",
})

P3.append({
    "tier": 1,
    "question": "Bees fly from flower to flower drinking nectar. How does that help the flowers?",
    "answer": "Bees carry pollen between flowers, helping seeds form",
    "choices": [
        "Bees carry pollen between flowers, helping seeds form",
        "Bees scare mice away from the garden each day",
        "Bees water the plants by dripping nectar back",
        "Bees cool the flowers by flapping their wings",
    ],
    "context": "Pollen is plant 'dust' that has to reach another flower to make a seed. Bees pick up pollen on their fuzzy bodies as they sip. Bats, butterflies, and even some hummingbirds are pollinators too.",
    "_pillar": 3,
    "_strategy": "bees_pollination",
})

# --- Life cycles (5) ---

P3.append({
    "tier": 1,
    "question": "Frogs and salamanders start their lives in water with little tails, breathing like fish. What's that in-between baby form called?",
    "answer": "A tadpole",
    "choices": [
        "A tadpole",
        "A larva-bug",
        "A guppy-frog",
        "A water-lizard",
    ],
    "context": "A tadpole has gills, a tail, and lives underwater. Over weeks it grows back legs, then front legs, absorbs its tail, develops lungs, and hops out as a small frog. This big change is called metamorphosis.",
    "_pillar": 3,
    "_strategy": "tadpole_frog_lifecycle",
})

P3.append({
    "tier": 1,
    "question": "A caterpillar wraps itself in a hard case and a few weeks later a butterfly comes out. What's the resting case called?",
    "answer": "A chrysalis",
    "choices": [
        "A chrysalis",
        "A scaffold",
        "A pebble",
        "A jellybead",
    ],
    "context": "Inside the chrysalis, the caterpillar's body breaks down and rebuilds into a butterfly. Moths spin silky cases called cocoons. Both are part of 'complete metamorphosis,' shared by many insects.",
    "_pillar": 3,
    "_strategy": "chrysalis_butterfly",
})

P3.append({
    "tier": 1,
    "question": "A baby chicken pecks its way out of what?",
    "answer": "An egg, laid by its mother hen",
    "choices": [
        "An egg, laid by its mother hen",
        "A wet leaf on the ground",
        "A small underground tunnel",
        "A piece of bread from the farmer",
    ],
    "context": "Hens lay eggs with everything a chick needs — yolk for food, white for cushioning, shell for protection. The chick uses a tiny 'egg tooth' to break out after about 21 days of warmth.",
    "_pillar": 3,
    "_strategy": "chick_hatches_egg",
})

P3.append({
    "tier": 1,
    "question": "Salmon are born in freshwater rivers, swim to the ocean to grow up, and return to the same rivers to lay eggs. What's a salmon's journey back to where it was born called?",
    "answer": "Migration",
    "choices": [
        "Migration",
        "Hibernation",
        "Photosynthesis",
        "Fermentation",
    ],
    "context": "Salmon use Earth's magnetic field and smell to find their home river — sometimes traveling thousands of miles. After laying eggs they usually die. Their bodies feed the forest around the river.",
    "_pillar": 3,
    "_strategy": "salmon_migration",
})

P3.append({
    "tier": 1,
    "question": "A bear sleeps deeply through the cold of winter, eating very little. What's this long winter sleep called?",
    "answer": "Hibernation",
    "choices": [
        "Hibernation",
        "Migration",
        "Pollination",
        "Vibration",
    ],
    "context": "True hibernators slow their heartbeat and breathing dramatically. Bears do a lighter version called torpor — easier to wake from. Hibernation helps animals survive seasons when food is scarce.",
    "_pillar": 3,
    "_strategy": "bear_hibernation",
})

# --- Food chains / ecology (8) ---

P3.append({
    "tier": 1,
    "question": "Grass is eaten by a rabbit; the rabbit is eaten by a fox. The grass-rabbit-fox sequence is an example of a what?",
    "answer": "A food chain",
    "choices": [
        "A food chain",
        "A water cycle",
        "A wind pattern",
        "A weather forecast",
    ],
    "context": "A food chain shows who eats whom. The Sun feeds plants, plants feed plant-eaters (like rabbits), plant-eaters feed meat-eaters (like foxes). Each link passes energy up.",
    "_pillar": 3,
    "_strategy": "food_chain_basics",
})

P3.append({
    "tier": 1,
    "question": "Animals that hunt and eat other animals are called what?",
    "answer": "Predators",
    "choices": [
        "Predators",
        "Producers",
        "Pollinators",
        "Pretenders",
    ],
    "context": "Wolves, eagles, sharks, and lions are predators. The animals they hunt are called prey. Predators help keep prey populations from growing too large and stripping their habitat bare.",
    "_pillar": 3,
    "_strategy": "predators",
})

P3.append({
    "tier": 1,
    "question": "Rabbits, deer, and zebras are eaten by larger animals. Plant-eating animals are called what?",
    "answer": "Herbivores",
    "choices": [
        "Herbivores",
        "Carnivores",
        "Insectivores",
        "Detectives",
    ],
    "context": "An herbivore eats only plants. A carnivore eats meat. An omnivore eats both — humans, bears, and raccoons are omnivores. The Latin 'herba' means grass or plant.",
    "_pillar": 3,
    "_strategy": "herbivores",
})

P3.append({
    "tier": 1,
    "question": "A lion eats only meat. Meat-eating animals are called what?",
    "answer": "Carnivores",
    "choices": [
        "Carnivores",
        "Herbivores",
        "Omnivores",
        "Detrivores",
    ],
    "context": "The Latin word 'carne' means meat. Lions, sharks, wolves, eagles, and crocodiles are carnivores. Their teeth and claws are usually built for catching and tearing food.",
    "_pillar": 3,
    "_strategy": "carnivores",
})

P3.append({
    "tier": 1,
    "question": "A bear eats fish, berries, honey, and even small mammals. Animals that eat both plants and meat are called what?",
    "answer": "Omnivores",
    "choices": [
        "Omnivores",
        "Carnivores",
        "Herbivores",
        "Insectivores",
    ],
    "context": "The Latin 'omni' means all. Humans, bears, pigs, raccoons, and crows are omnivores. Eating both kinds of food helps when the seasons change what's available.",
    "_pillar": 3,
    "_strategy": "omnivores",
})

P3.append({
    "tier": 1,
    "question": "At the very base of most food chains is something that makes its own food using sunlight. What is it?",
    "answer": "Plants",
    "choices": ["Plants", "Wolves", "Hawks", "Eagles"],
    "context": "Plants (and a few bacteria) are 'producers' — they make food from sunlight, water, and CO2. Almost every other living thing eats producers, or eats something else that ate producers.",
    "_pillar": 3,
    "_strategy": "producers_plants",
})

P3.append({
    "tier": 1,
    "question": "When a dead tree slowly rots, who breaks it down so its bits return to the soil?",
    "answer": "Decomposers, like fungi and bacteria",
    "choices": [
        "Decomposers, like fungi and bacteria",
        "Larger trees, growing roots into it",
        "The wind, blowing it into dust",
        "Birds, which carry every piece away",
    ],
    "context": "Decomposers recycle dead plants and animals into nutrients that living plants can use again. Without them the world would pile up with dead matter. Mushrooms, molds, worms, and many bacteria do the job.",
    "_pillar": 3,
    "_strategy": "decomposers_fungi",
})

P3.append({
    "tier": 1,
    "question": "All the living and non-living things in one area — plants, animals, soil, water, sunlight — together make up what?",
    "answer": "An ecosystem",
    "choices": [
        "An ecosystem",
        "An algorithm",
        "An anatomy",
        "A galaxy",
    ],
    "context": "A pond, a forest, a coral reef, even a backyard garden are ecosystems. Change one part and the others react — fewer wolves can mean too many deer, too few plants, and unhappy songbirds.",
    "_pillar": 3,
    "_strategy": "ecosystem_definition",
})

# --- Anatomy basics (8) ---

P3.append({
    "tier": 1,
    "question": "Your heart's job is to pump what around your body day and night?",
    "answer": "Blood",
    "choices": [
        "Blood",
        "Bone",
        "Air",
        "Bile",
    ],
    "context": "Your heart is a muscular pump. It sends blood to your lungs to pick up oxygen, then around your body to deliver oxygen and food. A typical kid's heart beats about 80-100 times a minute.",
    "_pillar": 3,
    "_strategy": "heart_pumps_blood",
})

P3.append({
    "tier": 1,
    "question": "When you breathe in, what gas from the air do your lungs hand to your blood?",
    "answer": "Oxygen, picked up by red blood cells",
    "choices": [
        "Oxygen, picked up by red blood cells",
        "Helium, of the kind in floating balloons",
        "Argon, an unreactive gas in our atmosphere",
        "Methane, the gas from swamps and cow burps",
    ],
    "context": "Your lungs have millions of tiny air sacs called alveoli. Oxygen passes through their walls into blood, while carbon dioxide passes back out into the lungs to be breathed away.",
    "_pillar": 3,
    "_strategy": "lungs_take_in_oxygen",
})

P3.append({
    "tier": 1,
    "question": "What organ uses electrical signals to control your thoughts, movements, and dreams?",
    "answer": "The brain",
    "choices": [
        "The brain",
        "The kidney",
        "The stomach",
        "The thumb",
    ],
    "context": "The human brain has roughly 86 billion nerve cells (neurons). They send tiny electric pulses to each other through long fibers called axons. The brain also runs heartbeat, breathing, and balance.",
    "_pillar": 3,
    "_strategy": "brain_runs_body",
})

P3.append({
    "tier": 1,
    "question": "What organ on your face picks up the smells in your kitchen?",
    "answer": "The nose",
    "choices": [
        "The nose",
        "The ear",
        "The eye",
        "The elbow",
    ],
    "context": "Inside the top of your nose are millions of tiny smell receptor cells. Each can detect specific molecules. A typical human can recognize thousands of distinct odors; dogs can detect far more.",
    "_pillar": 3,
    "_strategy": "nose_smells",
})

P3.append({
    "tier": 1,
    "question": "Your skeleton holds up your body. About how many bones does a typical adult human have?",
    "answer": "About 206 bones",
    "choices": [
        "About 206 bones",
        "About 10 bones",
        "About 1,000 bones",
        "About 1 million bones",
    ],
    "context": "Babies are born with about 270 small bones, but many fuse together as they grow. Adults end up with around 206. The smallest bones are in your inner ear; the longest is your thigh bone (femur).",
    "_pillar": 3,
    "_strategy": "human_206_bones",
})

P3.append({
    "tier": 1,
    "question": "How do muscles actually do their work?",
    "answer": "By squeezing tighter, then relaxing, which pulls on bones",
    "choices": [
        "By squeezing tighter, then relaxing, which pulls on bones",
        "By pushing on bones to make them move forward",
        "By growing longer until they touch the next bone",
        "By sending light into nerves to signal motion",
    ],
    "context": "Muscles can only pull, not push. They come in pairs across joints — when one pulls, the other relaxes. That's why your arm bends when biceps tighten and straightens when triceps tighten.",
    "_pillar": 3,
    "_strategy": "muscles_pull",
})

P3.append({
    "tier": 1,
    "question": "What organ is the largest in your body and protects everything inside?",
    "answer": "The skin",
    "choices": [
        "The skin",
        "The brain",
        "The liver",
        "The heart",
    ],
    "context": "Skin keeps germs out, water in, and helps you sense the world. An adult's skin has a total area of about 2 square meters. It's the largest organ — even though we usually only think of organs as on the inside.",
    "_pillar": 3,
    "_strategy": "skin_largest_organ",
})

P3.append({
    "tier": 1,
    "question": "Inside the middle of your bones is a soft red tissue that makes new blood cells. What's it called?",
    "answer": "Bone marrow",
    "choices": [
        "Bone marrow",
        "Bone bristle",
        "Bone moss",
        "Bone foam",
    ],
    "context": "Bone marrow makes the red cells that carry oxygen, the white cells that fight germs, and the platelets that close wounds. People with certain blood diseases sometimes receive a bone-marrow transplant.",
    "_pillar": 3,
    "_strategy": "bone_marrow",
})

# --- Animal facts that wonder (12) ---

P3.append({
    "tier": 1,
    "question": "A blue whale is the largest animal that has ever lived on Earth. Its heart is roughly the size of what?",
    "answer": "A small car",
    "choices": [
        "A small car",
        "A walnut",
        "A penny",
        "A grain of rice",
    ],
    "context": "A blue whale's heart can weigh about 180 kg (400 pounds) and beat as slow as twice per minute when the whale is diving. The whole whale can be 30 meters long — longer than a basketball court.",
    "_pillar": 3,
    "_strategy": "blue_whale_heart_car_sized",
})

P3.append({
    "tier": 1,
    "question": "An octopus is famous for having how many hearts?",
    "answer": "Three hearts",
    "choices": [
        "Three hearts",
        "One heart",
        "Ten hearts",
        "Twenty hearts",
    ],
    "context": "Two of the octopus's hearts pump blood through the gills; the third pumps it around the rest of the body. Its blood is bluish because it uses copper, not iron, to carry oxygen.",
    "_pillar": 3,
    "_strategy": "octopus_three_hearts",
})

P3.append({
    "tier": 1,
    "question": "A starfish that loses an arm can do something amazing. What?",
    "answer": "It can slowly grow the lost arm back",
    "choices": [
        "It can slowly grow the lost arm back",
        "It can change colors to hide its missing arm",
        "It can fly briefly above the water surface",
        "It can swap arms with another starfish",
    ],
    "context": "Starfish regenerate arms over months. In some species, even a single severed arm can grow a whole new starfish if a chunk of the central disc stays attached. Geckos do something similar with tails.",
    "_pillar": 3,
    "_strategy": "starfish_regrow_arm",
})

P3.append({
    "tier": 1,
    "question": "Why does a chameleon really change skin color?",
    "answer": "To show mood and temperature to other chameleons",
    "choices": [
        "To show mood and temperature to other chameleons",
        "Only to hide perfectly from any predator nearby",
        "To match the color of the food it just ate",
        "To turn invisible against any background at all",
    ],
    "context": "Color shift in chameleons is mostly for showing anger, courting a mate, or warming up. Camouflage helps too, but they don't actually become invisible — they have a normal 'resting' color.",
    "_pillar": 3,
    "_strategy": "chameleon_color_signals",
})

P3.append({
    "tier": 1,
    "question": "A bat flying in the dark sends out sounds and listens for the echoes to find bugs. What's this skill called?",
    "answer": "Echolocation",
    "choices": [
        "Echolocation",
        "Hibernation",
        "Photosynthesis",
        "Migration",
    ],
    "context": "Most bats make high-pitched clicks (too high for human ears) and read the echoes that bounce back to map their surroundings. Dolphins and toothed whales use echolocation in water for the same purpose.",
    "_pillar": 3,
    "_strategy": "bat_echolocation",
})

P3.append({
    "tier": 1,
    "question": "A honeybee that finds a great flower patch tells the rest of the hive about it by doing what?",
    "answer": "A waggle dance, wiggling in patterns to share direction and distance",
    "choices": [
        "A waggle dance, wiggling in patterns to share direction and distance",
        "Roaring loudly until the others fly out to look",
        "Painting an arrow on the hive with pollen",
        "Carrying every bee one by one to the flower",
    ],
    "context": "Austrian scientist Karl von Frisch decoded the waggle dance in the 1940s and won a Nobel Prize for it in 1973. The angle of the dance shows direction from the Sun; the wiggle length shows distance.",
    "_pillar": 3,
    "_strategy": "bee_waggle_dance",
})

P3.append({
    "tier": 1,
    "question": "An African elephant carries the biggest brain of any land animal. About how big is it?",
    "answer": "About 5 kilograms, three times a human brain",
    "choices": [
        "About 5 kilograms, three times a human brain",
        "About 50 grams, the size of a strawberry",
        "About 100 kilograms, the size of a person",
        "About 1 milligram, the size of a sand grain",
    ],
    "context": "Elephants have impressive memories, can recognize themselves in mirrors, and grieve their dead. Even so, brain-to-body ratio matters too — humans have a much higher ratio.",
    "_pillar": 3,
    "_strategy": "elephant_brain_size",
})

P3.append({
    "tier": 1,
    "question": "A peregrine falcon dives to catch other birds. How fast can it go in a steep dive?",
    "answer": "Over 300 kilometers per hour, the fastest animal in the world",
    "choices": [
        "Over 300 kilometers per hour, the fastest animal in the world",
        "About the same as a running squirrel",
        "About 30 kilometers per hour, like a bike",
        "Slower than a person riding a skateboard",
    ],
    "context": "Peregrine falcons fold their wings and dive — what's called a 'stoop' — striking prey with a closed fist of talons. Top recorded speeds are about 389 km/h (242 mph). They live on every continent except Antarctica.",
    "_pillar": 3,
    "_strategy": "peregrine_fastest",
})

P3.append({
    "tier": 1,
    "question": "Honeybees do something surprising over winter to keep their hive warm. What?",
    "answer": "They huddle in a tight ball and shiver to make heat",
    "choices": [
        "They huddle in a tight ball and shiver to make heat",
        "They light tiny fires inside the hive",
        "They sleep underground until spring",
        "They each grow thick fur for the winter",
    ],
    "context": "A winter bee cluster keeps the queen near 35 C even when it's freezing outside. Bees take turns rotating from the warm middle to the colder outer layer. They eat stored honey for fuel.",
    "_pillar": 3,
    "_strategy": "bees_winter_cluster",
})

P3.append({
    "tier": 1,
    "question": "Penguins live in the cold, mostly in the southern half of the world. What can penguins NOT do that most birds can?",
    "answer": "Fly through the air",
    "choices": [
        "Fly through the air",
        "Lay eggs on land",
        "Stand upright on two feet",
        "Eat fish from the water",
    ],
    "context": "Penguins are excellent swimmers — their wings have evolved into flippers. They can stay underwater for several minutes and dive deep for fish. But on land they waddle, and they cannot take off into the sky.",
    "_pillar": 3,
    "_strategy": "penguins_no_fly",
})

P3.append({
    "tier": 1,
    "question": "Monarch butterflies from the US and Canada fly an amazing distance each fall. Where to?",
    "answer": "Forests in central Mexico, thousands of km away",
    "choices": [
        "Forests in central Mexico, thousands of km away",
        "Just to the next backyard down the street",
        "The South Pole, near the emperor penguins",
        "The Moon, returning back a week later",
    ],
    "context": "Monarchs that never made the trip somehow find the same Mexican fir forests their great-grandparents wintered in. Scientists are still working out how. The migration covers up to 4,800 km (3,000 mi).",
    "_pillar": 3,
    "_strategy": "monarch_migration",
})

P3.append({
    "tier": 1,
    "question": "A spider's web is made of silk. Where does the silk come from?",
    "answer": "From special glands inside the spider's body",
    "choices": [
        "From special glands inside the spider's body",
        "From the trees it crawls on each day",
        "From the leftover food it eats at night",
        "From the rain water that falls on it",
    ],
    "context": "Spider silk comes out as liquid through tiny nozzles called spinnerets at the back of the spider, then hardens in air. Some silk is sticky for catching bugs; some is strong as a guide thread.",
    "_pillar": 3,
    "_strategy": "spider_silk_glands",
})


# ============================================================================
# Combine + validate
# ============================================================================

ALL = P1 + P2 + P3

OUTPUT_PATH = REPO / "_gen_science_t1_p123.json"


def main():
    print(f"Generated: {len(ALL)} total | P1={len(P1)} P2={len(P2)} P3={len(P3)}")
    # Validate self-consistency over generated set
    dup, ans = build_bank_indices(ALL)
    pass_count = 0
    soft_count = 0
    fail_records = []
    soft_records = []
    for i, q in enumerate(ALL):
        r = validate_rewrite(
            "science", q,
            bank=ALL, dup_index=dup, answer_index=ans, replace_idx=i,
        )
        if r["verdict"] == "PASS":
            pass_count += 1
        elif r["verdict"] == "SOFT_WARN":
            soft_count += 1
            soft_records.append((i, q.get("answer","")[:50], r["soft_warns"]))
        else:
            fail_records.append((i, q.get("question","")[:80], r["hard_fails"]))

    print(f"PASS={pass_count} SOFT_WARN={soft_count} FAIL={len(fail_records)}")
    if fail_records:
        print("=== FAILURES ===")
        for idx, qs, hf in fail_records[:50]:
            print(f"  [{idx}] {qs}")
            for gate, reason in hf:
                print(f"    -> {gate}: {reason}")
    if soft_records:
        print("=== SOFT WARNS ===")
        for idx, ans_text, sw in soft_records[:20]:
            print(f"  [{idx}] {ans_text}")
            for gate, reason in sw:
                print(f"    -> {gate}: {reason}")

    # Save unconditionally; user requested save-as-you-go canonical output
    wrapper = {
        "tier": 1,
        "summary": {
            "questions_generated": len(ALL),
            "by_pillar": {"1": len(P1), "2": len(P2), "3": len(P3)},
            "validation": {
                "PASS": pass_count,
                "SOFT_WARN": soft_count,
                "FAIL": len(fail_records),
            },
        },
        "questions": ALL,
    }
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(wrapper, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUTPUT_PATH}")
    return 0 if not fail_records else 1


if __name__ == "__main__":
    sys.exit(main())
