# Circuits, Motors and Generators (T5, 9th grade, physical strand, map line G9.P4)

Sources were read on 2026-11-26. Grokipedia first; a second source is given
for anything a student could be taught wrong. The old-bank topics
faraday-the-bookbinders-apprentice, the-same-machine-run-backwards-motor-and-generator
and ohm-and-the-book-called-a-web-of-naked-fancies were quarried for leads
only; every fact used here was sourced again, and where the sources disagree
the disagreement is noted and the unsure detail is left out of the questions.
Arithmetic is kept to doubling and halving, done in the head (formula work is
the maths bank's).

Ground already keyed lower down, so not re-asked here: a closed loop, the
switch, a break stops the current, copper and plastic, the battery as source,
tap water, the bird on a wire (T1 electric-circuits); a motor turns electrical
energy into motion and turbines drive generators (T1 energy-changes-form);
charges, the compass, Gilbert, Oersted's needle, the electromagnet and the
maglock (T4 fields-pushes-and-pulls-without-touching).

## Series and parallel circuits

F1. In a series circuit the parts are joined end to end along one path, so the current has only one route and is the same through every part; the total voltage is divided among them; "a failure in one element breaks the entire circuit." Traditional strings of holiday lights were wired in series, so "the failure of one bulb interrupts current flow to the entire chain"; that design has been phased out in modern sets (Grokipedia). OpenStax: "The same current flows through each resistor in series"; series resistors "do not get the total source voltage, but divide it."
    https://grokipedia.com/page/Series_and_parallel_circuits ; https://openstax.org/books/college-physics-2e/pages/21-1-resistors-in-series-and-parallel

F2. In a parallel circuit the parts are joined across the same two points, making separate branches; each branch gets the same voltage, the full voltage of the source, and the total current divides among the branches. "If one appliance fails or is unplugged, the others continue to receive full voltage and operate normally" (Grokipedia). OpenStax: "Each resistor in parallel has the same full voltage of the source applied to it."
    https://grokipedia.com/page/Series_and_parallel_circuits ; https://openstax.org/books/college-physics-2e/pages/21-1-resistors-in-series-and-parallel

F3. Reasoning from F1 and F2 for three identical bulbs on one battery: only if all three are on separate branches (all in parallel) does every bulb have its own path, so that unscrewing any one leaves the other two lit. With two in series and the third on a branch of its own, unscrewing one of the pair puts out its partner; with two side by side in parallel and the third in series with them, unscrewing the third puts out all three; with all three in series, any one out puts out all.
    (derived from F1 and F2)

F4. House and car wiring are parallel. OpenStax: a car's headlights, radio and other devices are "wired in parallel, so that they utilize the full voltage of the source and can operate completely independently. The same is true in your house, or any building." Grokipedia: household "outlets are wired in parallel to provide the standard line voltage" so that devices can be used "independently."
    https://openstax.org/books/college-physics-2e/pages/21-1-resistors-in-series-and-parallel ; https://grokipedia.com/page/Series_and_parallel_circuits

F5. Adding branches in parallel lowers the total resistance and raises the current drawn from the source: "more current flows from the source than would flow for any of them individually, and so the total resistance is lower" (OpenStax); "Connecting resistors in parallel reduces the overall equivalent resistance below that of any individual resistor" (Grokipedia). So a house with more things switched on draws more current in all, not less.
    https://openstax.org/books/college-physics-2e/pages/21-1-resistors-in-series-and-parallel ; https://grokipedia.com/page/Series_and_parallel_circuits

## Current, voltage and resistance in words

F6. Electric current is the flow of charge: "the rate at which charge passes through a given point." Its unit is the ampere, "equivalent to one coulomb of charge per second." It is measured with an ammeter, connected in series "to ensure the full current passes through the device" (Grokipedia).
    https://grokipedia.com/page/Electric_current

F7. Current is not used up going round a circuit: "The current in a series circuit is the same everywhere," and an ammeter "measures the current flowing through it without affecting the current" (Oak National Academy). OpenStax: in a simple circuit "the same q flows through each" part. What a bulb takes from the circuit is energy: electric power is "the rate at which electrical energy is transferred within an electric circuit" (Grokipedia), measured in watts, one joule per second. MISCONCEPTION: "Pupils often hold a consumption model of electric current, believing it is used up in a circuit" (Oak National Academy).
    https://www.thenational.academy/teachers/programmes/science-secondary-ks3/units/series-circuits/lessons/measuring-electric-current ; https://openstax.org/books/college-physics-2e/pages/20-2-ohms-law-resistance-and-simple-circuits ; https://grokipedia.com/page/Electric_power

F8. Voltage is the push that drives a current, measured in volts: "Voltage is similar to fluid pressure. The voltage source is like a pump, creating a pressure difference, causing current" (OpenStax). Batteries, generators and wall outlets are "voltage sources" (OpenStax). MISCONCEPTION: students treat a battery as "a constant source of current," and "often assign the properties of current to voltage and/or resistance" (Engelhardt and Beichner, DIRECT study).
    https://openstax.org/books/college-physics-2e/pages/20-2-ohms-law-resistance-and-simple-circuits ; https://arxiv.org/abs/physics/0304040

F9. Resistance is "the opposition to the flow of electric current through a material"; it is measured in ohms, and "1 Ω equals 1 volt per ampere" (Grokipedia). A wire's resistance is "directly proportional to its length" and "inversely proportional to the cylinder's cross-sectional area" (OpenStax), so a longer wire of the same metal has more resistance and a thicker one less. (Grokipedia's resistance page agrees that doubling the length doubles the resistance; its line on doubling the diameter "halves" the resistance is wrong, since four times the area gives a quarter, so it is not used.)
    https://grokipedia.com/page/Electrical_resistance_and_conductance ; https://openstax.org/books/college-physics-2e/pages/20-3-resistance-and-resistivity

F10. Ohm's law in words: the current through a conductor is directly proportional to the voltage across it, and goes down as the resistance goes up (V = IR; I = V/R; current in amperes, voltage in volts, resistance in ohms). So twice the push through the same wire gives twice the current. It is "an empirical law like that for friction," "an experimentally observed phenomenon"; it holds for "ohmic" substances such as copper and aluminium and "is not universally valid" (OpenStax); it "does not hold for nonohmic devices like diodes or filament lamps" (Grokipedia).
    https://grokipedia.com/page/Ohm's_law ; https://en.wikipedia.org/wiki/Ohm%27s_law ; https://openstax.org/books/college-physics-2e/pages/20-2-ohms-law-resistance-and-simple-circuits

F11. Two bulbs on the same voltage: comparing a 25-watt and a 60-watt bulb made for 120 volts, "Since both operate on the same voltage, the 60-W bulb must draw more current to have a greater power rating. Thus the 60-W bulb's resistance must be lower than that of a 25-W bulb"; "the lower the resistance connected to a given voltage source, the greater the power delivered" (OpenStax). MISCONCEPTION: that the brighter bulb, glowing harder, must have the greater resistance.
    https://openstax.org/books/college-physics-2e/pages/20-4-electric-power-and-energy

## Georg Ohm and his book (1825-1841)

F12. Georg Simon Ohm taught mathematics and physics at the Jesuit Gymnasium in Cologne from 1817 (Grokipedia; Wikipedia gives the offer as 11 September 1817). Using apparatus he built himself, he measured how the current in wires changed with their length; Grokipedia says he "systematically varied wire parameters, including length, thickness, and material." He read the current from the turn of a magnetic needle hung over the wire, on a Coulomb torsion balance (Encyclopedia.com, Dictionary of Scientific Biography; Uni Flensburg).
    https://grokipedia.com/page/Georg_Ohm ; https://grokipedia.com/page/Ohm's_law ; https://en.wikipedia.org/wiki/Georg_Ohm ; https://www.encyclopedia.com/people/science-and-technology/physics-biographies/georg-simon-ohm

F13. Ohm's first source, a voltaic pile, gave readings that drifted (its "polarization caused inconsistent results," Grokipedia); in 1826, at Johann Poggendorff's suggestion (DSB), he switched to a copper-and-bismuth thermocouple, which "provided a more stable voltage source" (Wikipedia). Its two junctions sat in "a mixture of ice and water" and in "water brought to a boil with a burner"; "This ensures a fixed temperature difference and thus a fixed voltage" (Uni Flensburg). Its push was "exactly proportional to the temperature difference at its end points" (DSB).
    https://grokipedia.com/page/Georg_Ohm ; https://en.wikipedia.org/wiki/Ohm%27s_law ; https://www.uni-flensburg.de/en/working-group-physics/histolab/thematical-subsections/electricity/ohms-torsion-balance ; https://www.encyclopedia.com/people/science-and-technology/physics-biographies/georg-simon-ohm

F14. Ohm published his results in 1827 as the book Die galvanische Kette, mathematisch bearbeitet ("The galvanic circuit investigated mathematically"), drawing on Joseph Fourier's mathematics of heat flowing along a bar (Wikipedia; Grokipedia).
    https://en.wikipedia.org/wiki/Ohm%27s_law ; https://grokipedia.com/page/Georg_Ohm ; https://en.wikipedia.org/wiki/Georg_Ohm

F15. The reception: "coldly received" (Wikipedia, Georg Ohm); "greeted with some appreciation but largely with indifference and with some hostility," "largely because the majority of German physicists in 1827 represented a soon-to-be-superseded nonmathematical approach to physics"; his chief Berlin adversaries, Johannes Schulze of the ministry of education and the physicist Georg Friedrich Pohl, were followers of Hegel and of Naturphilosophie (DSB). Grokipedia: "the mathematical approach was criticized as overly abstract"; MacTutor: he "was not really successful in convincing the older German physicists that the mathematical approach was the right one." Critics called the work "a web of naked fancies" (Wikipedia, Ohm's law; Grokipedia). Who first wrote the phrase is unclear (Grokipedia names Schweigger; the DSB names Schweigger only as the editor who printed Ohm's papers), so no critic is named in the questions. Wikipedia also quotes a minister calling him unworthy to teach science; that line is not used.
    https://en.wikipedia.org/wiki/Georg_Ohm ; https://www.encyclopedia.com/people/science-and-technology/physics-biographies/georg-simon-ohm ; https://grokipedia.com/page/Ohm's_law ; https://mathshistory.st-andrews.ac.uk/Biographies/Ohm/ ; https://en.wikipedia.org/wiki/Ohm%27s_law ; https://grokipedia.com/page/Georg_Ohm

F16. How the law won: Gustav Fechner, in 1831, "subjected it to rigorous experimental testing (and confirmation)" in his Massbestimmungen über die galvanische Kette; Heinrich Lenz used it in his first paper on induction (1832), and Gauss and Weber in 1832-1833 (DSB). The Royal Society gave Ohm its Copley Medal in 1841 (Grokipedia; Wikipedia; MacTutor; the DSB dates it 30 November 1841). He became professor of physics at Munich in 1852 and died in 1854 (Grokipedia). The unit of resistance, the ohm, was adopted in 1881 by the International Electrical Congress in Paris (Grokipedia). By the 1850s "Ohm's law was widely known and considered proved" (Wikipedia).
    https://www.encyclopedia.com/people/science-and-technology/physics-biographies/georg-simon-ohm ; https://grokipedia.com/page/Georg_Ohm ; https://en.wikipedia.org/wiki/Ohm%27s_law ; https://mathshistory.st-andrews.ac.uk/Biographies/Ohm/

## Michael Faraday, the bookbinder's apprentice (1791-1813)

F17. Michael Faraday was born on 22 September 1791 at Newington Butts; his father James was a blacksmith; he learned "the basics of reading, writing, and arithmetic" at a Sunday school (Grokipedia); Wikipedia: "only the most basic school education." In 1805, at 14, he began a seven-year apprenticeship to George Riebau, a London bookbinder and bookseller of Blandford Street (Grokipedia; Wikipedia). (Faraday himself wrote that he entered the shop "at the age of 13": he began there as an errand boy before the apprenticeship; the questions say fourteen, the apprenticeship's age.)
    https://grokipedia.com/page/Michael_Faraday ; https://en.wikipedia.org/wiki/Michael_Faraday ; https://epsilon.ac.uk/view/faraday/letters/Faraday3519

F18. Faraday read the books in the shop. In a letter to Arthur-Auguste De La Rive of 2 October 1858 he wrote that the Encyclopaedia Britannica gave him "my first notions of Electricity" and that "Mrs. Marcets conversations on chemistry ... gave me my foundation in that science"; that he tested the book by "such little experiments as I could find means to perform"; "I could trust a fact,- but always cross examined an assertion"; and that when the experiments agreed with the book he felt he had "got hold of an anchor in chemical knowledge." Grokipedia and Wikipedia also name Jane Marcet's Conversations on Chemistry as the book that drew him to chemistry.
    https://epsilon.ac.uk/view/faraday/letters/Faraday3519 ; https://grokipedia.com/page/Michael_Faraday ; https://en.wikipedia.org/wiki/Michael_Faraday

F19. In 1812, aged 20, Faraday attended lectures by Humphry Davy at the Royal Institution; William Dance gave him many of the tickets. He sent Davy a book of about 300 pages based on his notes (Wikipedia: 300; Grokipedia: a 313-page notebook "he later bound and presented to Davy" with "a letter seeking employment"), and "Davy's reply was immediate, kind, and favourable." After Davy hurt his eyes in an accident with nitrogen trichloride and the assistant John Payne was dismissed, Faraday was appointed chemical assistant at the Royal Institution on 1 March 1813.
    https://en.wikipedia.org/wiki/Michael_Faraday ; https://grokipedia.com/page/Michael_Faraday

## Faraday's motor (1821)

F20. On 3 September 1821, in the Royal Institution's basement laboratory, Faraday made "a wire carrying an electric current move around a magnet," which he called "electromagnetic rotations." His notebook for 4 September describes "A deep basin with a bit of wax at bottom and then filled with mercury" with "a magnet stuck upright in wax so that pole just above surface of mercury"; the wire dipped into the mercury, and he "got the revolution of the wire round the pole of the magnet." The Royal Institution calls it "the world's first electric motor," the first time continuous mechanical movement was made from electricity. Grokipedia: the wire rotated around the magnet, "producing continuous circular motion"; the homopolar motor "represents the world's first electric motor." Mercury, a liquid metal, carried the current while letting the wire move.
    https://www.rigb.org/explore-science/explore/blog/birth-electric-motion ; https://grokipedia.com/page/Homopolar_motor ; https://grokipedia.com/page/Michael_Faraday ; https://en.wikipedia.org/wiki/Michael_Faraday

F21. Faraday was accused of plagiarising William Hyde Wollaston, who had tried and failed to make a current produce rotation; Davy said in March 1823 that Wollaston had made "the first suggestion of electro-magnetic rotation" (Lancaster Davy Notebooks Project; Royal Institution; Wikipedia: Davy and Wollaston "tried but failed to design an electric motor").
    https://wp.lancs.ac.uk/davynotebooks/?p=414 ; https://www.rigb.org/explore-science/explore/blog/birth-electric-motion ; https://en.wikipedia.org/wiki/Michael_Faraday

F22. How a motor works: a magnetic field pushes on a wire carrying a current, and the force is "perpendicular to both the direction of current flow and the magnetic field" (Grokipedia, Homopolar motor), so the wire is pushed sideways, not pulled toward the magnet; that sideways push is why Faraday's wire went round and round. In an ordinary motor the push turns a coil (the armature), and a commutator reverses the current "as the armature turns through half a rotation" "to keep the magnetic torque unidirectional" (Grokipedia, Electric motor). Moritz Jacobi built the first practical rotating motor (1834) and Thomas Davenport patented a direct-current motor in 1837 (Grokipedia).
    https://grokipedia.com/page/Homopolar_motor ; https://grokipedia.com/page/Electric_motor

## Faraday's induction (1831)

F23. On 29 August 1831 Faraday wound two separate coils of insulated copper wire on opposite sides of an iron ring. One was joined to a battery; the other ran to a galvanometer, "an electromechanical instrument designed to detect and measure small electric currents." "Upon completing or breaking the battery circuit, Faraday observed transient deflections"; "no effect occurred during steady current flow" (Grokipedia, Electromagnetic induction); breaking the circuit "caused a deflection in the opposite direction" (Grokipedia, Faraday's law). OpenStax, describing the same arrangement: a current each time the switch is closed, the other way each time it is opened, and "if the switch remains closed or open for any length of time, there is no current through the galvanometer." Faraday's earlier attempts "using static magnets or steady electric currents yielded no results" (Grokipedia, Faraday's law).
    https://grokipedia.com/page/Electromagnetic_induction ; https://grokipedia.com/page/Faraday's_law_of_induction ; https://grokipedia.com/page/Michael_Faraday ; https://openstax.org/books/college-physics-2e/pages/23-1-induced-emf-and-magnetic-flux ; https://grokipedia.com/page/Galvanometer

F24. Later in 1831 Faraday pushed a bar magnet into, and drew it out of, a coil of wire joined to a galvanometer (Grokipedia, Michael Faraday: "inserting and withdrawing a bar magnet from a coil of wire connected to a galvanometer"); the deflections were "proportional to the speed of motion," and "induction depended on the rate of magnetic field variation rather than absolute proximity" (Grokipedia, Electromagnetic induction). OpenStax: an emf is induced when the magnet is pushed in and out; reversing the motion reverses it; "there is no emf when the magnet is stationary relative to the coil" ("The galvanometer needle does not deflect"); "The same results are produced if the coil is moved rather than the magnet"; "The faster the motion, the greater the emf." Wikipedia: moving the loop over a stationary magnet also made a current.
    https://grokipedia.com/page/Michael_Faraday ; https://grokipedia.com/page/Electromagnetic_induction ; https://openstax.org/books/college-physics-2e/pages/23-1-induced-emf-and-magnetic-flux ; https://en.wikipedia.org/wiki/Michael_Faraday

F25. The principle: "a time-varying magnetic field induces an electromotive force" (Grokipedia, Michael Faraday); "The current is a result of an emf induced by a changing magnetic field" (OpenStax); "a changing magnetic field produces an electric field" (Wikipedia). A steady field induces nothing (Grokipedia, Electromagnetic induction). A magnet at rest still has its field all the time; MISCONCEPTION: that a magnet beside a coil, or a steady current next door, ought to give a steady current.
    https://grokipedia.com/page/Michael_Faraday ; https://openstax.org/books/college-physics-2e/pages/23-1-induced-emf-and-magnetic-flux ; https://en.wikipedia.org/wiki/Michael_Faraday ; https://grokipedia.com/page/Electromagnetic_induction

F26. Joseph Henry, at the Albany Academy, observed induction independently; his results were published in 1832, and credit generally goes to Faraday (Grokipedia, Faraday's law; Grokipedia, Electromagnetic induction).
    https://grokipedia.com/page/Faraday's_law_of_induction ; https://grokipedia.com/page/Electromagnetic_induction

F27. Lenz's law (Heinrich Lenz, 1834): "an induced current flows in such a direction as to oppose the change in magnetic flux that causes it"; if it reinforced the change, energy could be had without input, so the opposition is conservation of energy at work (Grokipedia, Electromagnetic induction; Grokipedia, Faraday's law).
    https://grokipedia.com/page/Electromagnetic_induction ; https://grokipedia.com/page/Faraday's_law_of_induction

## Generators, and the same machine run the other way

F28. In October 1831 Faraday spun a copper disc on an axle between the poles of a horseshoe magnet (the Faraday disc, a homopolar generator) (Grokipedia, Michael Faraday); "it produced a steady current" (Grokipedia, Electromagnetic induction), "the first instance of sustained electrical generation from rotary motion" (Grokipedia, Electric generator). (Grokipedia's pages differ on the exact day, so no day is used.)
    https://grokipedia.com/page/Michael_Faraday ; https://grokipedia.com/page/Electromagnetic_induction ; https://grokipedia.com/page/Electric_generator

F29. A generator "converts mechanical energy into electrical energy" by induction; "The induction of voltage requires relative motion between a conductor and a magnetic field"; in a power station, turbines driven by "steam, water, wind, or combustion gases" spin the rotor inside the fixed windings of the stator (Grokipedia, Electric generator).
    https://grokipedia.com/page/Electric_generator

F30. Motor and generator are one machine run two ways. In 1873, at an industrial exposition in Vienna, Zénobe Gramme's partner Hippolyte Fontaine "carelessly connected the terminals of a Gramme machine to another dynamo which was producing electricity," and "its shaft began to spin" (Wikipedia, Gramme machine). Grokipedia: Fontaine "accidentally connected two machines via a long cable," the second "approximately 500 meters away," which ran as a motor driving a water pump, revealing "the device's reversible functionality." The Gramme machine was a direct-current dynamo invented by Gramme in 1871 (Grokipedia).
    https://en.wikipedia.org/wiki/Gramme_machine ; https://grokipedia.com/page/Gramme_machine ; https://en.wikipedia.org/wiki/Z%C3%A9nobe_Gramme

F31. Regenerative braking "slows a moving vehicle or object by converting its kinetic energy into electrical energy" by "reversing the function of the electric motor to act as a generator" (Grokipedia); "effectively turning the traction motor into an electric generator," and in battery-electric and hybrid cars the energy is "stored chemically in a battery" (Wikipedia). Friction brakes turn the energy of motion into heat (Grokipedia) and are still needed, since regeneration fades at low speed (Grokipedia: "typically below 5-10 km/h") and "is not by itself sufficient as the sole means of safely bringing a vehicle to a standstill" (Wikipedia). Frank J. Sprague introduced regenerative braking in 1886 (Grokipedia; Wikipedia).
    https://grokipedia.com/page/Regenerative_braking ; https://en.wikipedia.org/wiki/Regenerative_braking

## Misconceptions a 9th-grader brings (for honest wrong choices)

- Current is used up by a bulb, so less comes out than goes in (F7: the same current everywhere in a series loop; the bulb takes energy, not charge).
- A battery gives a fixed current whatever is joined to it (F8).
- The brighter bulb has the greater resistance (F11: on the same voltage it has less).
- Parallel branches share the supply's voltage, as series parts do (F1, F2).
- More things switched on in a house means less current drawn (F5: more).
- A magnet resting in a coil, or a steady current in the next coil, makes a current (F23, F24, F25).
- A magnet has a field only while it moves (F25: a still magnet's field is always there).
- Motors and generators are different machines (F30, F31).
- A magnet attracts a current-carrying wire toward itself, so the wire would stick to it (F22: the push is sideways).

## Left out (could not be pinned down or out of scope)

- Who first called Ohm's book "a web of naked fancies" (F15), and the minister's "heresies" remark.
- The page count of Faraday's notes for Davy (300, 313 and 386 are all given), and the number of Davy lectures he heard.
- The exact day of Faraday's disc and magnet-in-coil experiments (Grokipedia's pages differ).
- Wollaston's exact expectation (a wire turning on its own axis is reported only in a book abstract).
- Transformers, alternating current and the Faraday cage are outside this unit.

## Added in the revision (2026-11-26)

F32. "A web of naked fancies" was one review's phrase, in one Berlin journal: Popular Science Monthly (vol. 83, 1913), giving H. W. Dove's account, says that "in the Berlin Jahrbucher fur wissenschaftliche Kritik, Ohm's theory was named a web of naked fancies," "which could never find the semblance of support from even the most superficial observation of facts." The reviewer is not named there (the fact-check notes G. F. Pohl's 1828 review appeared in that journal; likely but not documented), so no critic is named in the questions.
    https://en.wikisource.org/wiki/Page:Popular_Science_Monthly_Volume_83.djvu/616 ; https://en.wikipedia.org/wiki/Ohm%27s_law

F33. Ohm's own results had the current fall as the test wire grew longer: his data "could be modeled through the equation" x = a/(b + l), where "x was the reading from the galvanometer, l was the length of the test conductor," a depended on the thermocouple's temperature and b was "a constant of the entire setup" (Wikipedia, Ohm's law). With F9 (resistance grows with length, falls with thickness), at the same push a longer wire of one metal carries less current, and a shorter or thicker one more.
    https://en.wikipedia.org/wiki/Ohm%27s_law

F34. The Faraday disc: "The first electromagnetic generator, the Faraday disk, was invented in 1831 by British scientist Michael Faraday": "a copper disc rotating between the poles of a horseshoe magnet", with a "sliding spring contact"; it "produced a small DC voltage" (Wikipedia, Electric generator; electrostatic generators came earlier, so "electromagnetic"). Grokipedia (Electric generator): a copper disc between the poles of a horseshoe magnet, with brushes to the axle and the disc's edge, "producing a continuous direct current (DC) that could be measured with a galvanometer", "the first instance of sustained electrical generation from rotary motion". Grokipedia (Homopolar generator): Faraday's diary entry of 28 October 1831; sliding contacts at the axis and the rim led to a galvanometer; a continuous direct current, no commutator. The current flows while the copper moves through the field (F29: induction "requires relative motion between a conductor and a magnetic field"); the magnet stands still.
    https://en.wikipedia.org/wiki/Electric_generator ; https://grokipedia.com/page/Electric_generator ; https://grokipedia.com/page/Homopolar_generator ; https://grokipedia.com/page/Michael_Faraday

F35. Faraday's 1821 rotation was the first electromagnetic motor, not the first motor of any kind: "The first electric motors were simple electrostatic devices" described by Andrew Gordon and Benjamin Franklin in the 1740s and 1750s, and Wikipedia captions Faraday's experiment "the first demonstration of the conversion of electrical energy into motion" by electromagnetism (Wikipedia, Electric motor); the Royal Institution calls it the first electric motor and the first continuous movement made from electricity (F20). Most motors, not all, turn on the push between currents and fields: Grokipedia (Electric motor) gives "the torque produced by the interaction between electric currents and magnetic fields", but switched reluctance motors "operate on the principle of variable magnetic reluctance" and piezoelectric motors work "without magnetic fields".
    https://en.wikipedia.org/wiki/Electric_motor ; https://grokipedia.com/page/Electric_motor ; https://www.rigb.org/explore-science/explore/blog/birth-electric-motion

F36. Fontaine showed reversibility rather than discovering it first: Wikipedia (Electric motor) gives "the reversibility of the electric machine, which was announced by Siemens in 1867 and observed by Pacinotti in 1869", and Gramme demonstrated it at the 1873 Vienna World's Fair by connecting two DC machines, one as generator and one as motor (F30: Fontaine's accidental connection there).
    https://en.wikipedia.org/wiki/Electric_motor ; https://en.wikipedia.org/wiki/Gramme_machine
