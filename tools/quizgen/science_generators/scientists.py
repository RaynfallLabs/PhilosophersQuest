"""Famous scientists → discovery / contribution attribution."""
from __future__ import annotations

from tools.quizgen.science_generators.common import make_question


# (scientist, contribution, year_or_period, ctx)
SCIENTISTS = [
    ("Isaac Newton", "Laws of motion + universal gravitation", "1687", "*Principia Mathematica* — foundational classical mechanics."),
    ("Albert Einstein", "Theory of relativity", "1905 + 1915", "Special (1905) + general (1915)."),
    ("Charles Darwin", "Theory of natural selection", "1859", "*On the Origin of Species*."),
    ("Gregor Mendel", "Laws of genetic inheritance", "1866", "Pea plant experiments; ignored until 1900."),
    ("Marie Curie", "Radioactivity + polonium + radium", "1898-1911", "Only person Nobel'd in two sciences (Physics 1903, Chemistry 1911)."),
    ("James Clerk Maxwell", "Equations unifying electricity, magnetism, light", "1865", "Foundation of classical electromagnetism."),
    ("Galileo Galilei", "Telescopic astronomy + falling bodies", "1609-1610", "Found Jupiter's moons + Venus phases."),
    ("Johannes Kepler", "Three laws of planetary motion", "1609-1619", "Ellipses + equal areas + T²∝a³."),
    ("Nicolaus Copernicus", "Heliocentric model of solar system", "1543", "*De Revolutionibus Orbium Coelestium*."),
    ("Dmitri Mendeleev", "Periodic table of elements", "1869", "Predicted undiscovered elements via gaps."),
    ("Antoine Lavoisier", "Founder of modern chemistry", "1789", "*Traité élémentaire de chimie*; guillotined 1794."),
    ("Louis Pasteur", "Germ theory + first rabies vaccine", "1860s-1885", "Vaccination + pasteurization."),
    ("Robert Koch", "Koch's postulates + anthrax + TB + cholera bacteria", "1876-1890", "Founded medical bacteriology."),
    ("Edward Jenner", "First successful vaccination (smallpox)", "1796", "Cowpox protects against smallpox."),
    ("Jonas Salk", "Inactivated polio vaccine", "1955", "Refused to patent it."),
    ("Albert Sabin", "Oral live attenuated polio vaccine", "1962", "Easier to administer than Salk's."),
    ("Maurice Hilleman", "Developed 40+ vaccines including MMR + hepatitis B", "1950s-1990s", "Considered the most prolific vaccine developer in history."),
    ("Norman Borlaug", "Green Revolution wheat varieties", "1940s-1970s", "1970 Nobel Peace; estimated 1 billion lives saved."),
    ("Tu Youyou", "Discovery of artemisinin (antimalarial)", "1972", "2015 Nobel; from ancient Chinese medical text."),
    ("Barry Marshall", "H. pylori causes peptic ulcers (not stress)", "1984", "2005 Nobel; drank H. pylori to prove it."),
    ("James Watson + Francis Crick", "DNA double-helix structure", "1953", "Photo 51 by Rosalind Franklin was essential."),
    ("Rosalind Franklin", "X-ray crystallography of DNA (Photo 51)", "1952", "Died 1958 before 1962 Nobel; Nobel excludes posthumous."),
    ("Jennifer Doudna + Emmanuelle Charpentier", "CRISPR-Cas9 gene editing", "2012", "2020 Nobel in Chemistry."),
    ("Richard Feynman", "Quantum electrodynamics (QED)", "1965 Nobel", "Feynman diagrams; Manhattan Project; Challenger O-ring."),
    ("Alfred Wegener", "Continental drift hypothesis", "1912", "Rejected for 50 years; vindicated by 1960s seafloor data."),
    ("Lynn Margulis", "Endosymbiotic theory of mitochondria", "1967", "Initially rejected; now standard biology."),
    ("Ignaz Semmelweis", "Handwashing reduces obstetric fever", "1847", "Rejected by Vienna establishment; institutionalized 1865."),
    ("Edwin Hubble", "Universe is expanding", "1929", "Galaxies receding; faster the farther."),
    ("Niels Bohr", "Atomic model with quantized electron orbits", "1913", "1922 Nobel; Copenhagen Interpretation of quantum mechanics."),
    ("Werner Heisenberg", "Uncertainty principle", "1927", "Δx · Δp ≥ ℏ/2."),
    ("Erwin Schrödinger", "Wave equation of quantum mechanics", "1926", "1933 Nobel; Schrödinger's cat 1935."),
    ("Max Planck", "Quantization of energy (quanta)", "1900", "Started quantum mechanics; 1918 Nobel."),
    ("Michael Faraday", "Electromagnetic induction + electrolysis", "1831", "Self-taught; Royal Institution."),
    ("John Dalton", "Atomic theory", "1803", "Modern atomic theory of matter."),
    ("J.J. Thomson", "Electron discovery", "1897", "Cathode ray tubes; 1906 Nobel."),
    ("Ernest Rutherford", "Atomic nucleus + gold foil experiment", "1911", "1908 Nobel for radioactivity."),
    ("Steven Koonin", "Climate skepticism + nuance from IPCC reports", "2021", "*Unsettled?*; former Obama administration DOE Undersecretary for Science."),
    ("Jay Bhattacharya", "Great Barrington Declaration co-author + NIH Director (2025-)", "2020", "Stanford epidemiologist; was targeted as 'fringe' by Collins/Fauci."),
    ("Martin Kulldorff", "Great Barrington Declaration co-author", "2020", "Harvard biostatistician at the time; fired from Mass General over vaccine-mandate dissent."),
    ("Robert Malone", "Early mRNA pioneer + later vaccine-mandate critic", "1989", "Worked on early mRNA technology; deplatformed during COVID for dissent."),
    ("John Ioannidis", "Why Most Published Research Findings Are False", "2005", "Foundational replication-crisis paper; Stanford."),
]


def generate_scientist_to_contribution() -> list[dict]:
    """T2-T3: scientist → contribution."""
    out = []
    all_contributions = [c for _, c, _, _ in SCIENTISTS]
    for sci, contribution, year, ctx in SCIENTISTS:
        distractors = [c for c in all_contributions if c != contribution][:3]
        out.append(make_question(
            tier=2, topic_cell="history",
            strategy="scientist_to_contribution", pillar="history_ethics",
            question=f"{sci} is best known for:",
            answer=contribution, distractors=distractors,
            context=f"{year}. {ctx}",
        ))
    return out


def generate_contribution_to_scientist() -> list[dict]:
    """T2-T3: contribution → scientist."""
    out = []
    all_scientists = [s for s, _, _, _ in SCIENTISTS]
    for sci, contribution, year, ctx in SCIENTISTS:
        distractors = [s for s in all_scientists if s != sci][:3]
        out.append(make_question(
            tier=2, topic_cell="history",
            strategy="contribution_to_scientist", pillar="history_ethics",
            question=f"The scientific contribution '{contribution}' is associated with:",
            answer=sci, distractors=distractors,
            context=f"{year}. {ctx}",
        ))
    return out


def generate_all_scientists() -> list[dict]:
    return generate_scientist_to_contribution() + generate_contribution_to_scientist()


if __name__ == "__main__":
    qs = generate_all_scientists()
    print(f"Generated {len(qs)} scientist questions")
