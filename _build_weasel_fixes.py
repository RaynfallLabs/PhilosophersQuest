"""Build per-subject weasel-closer fix patches with full gate validation.

Reads `_weasel_<subject>.json`, applies hand-crafted pointed/concrete closer
rewrites for each question, validates each rewrite through the universal
validation harness, and writes `_weasel_fix_<subject>.json` per subject.

Each rewrite is a complete new question object — stem + answer + choices +
context — to keep the patch self-contained for the applier.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite


def load_bank(subject: str) -> list[dict]:
    return json.loads((REPO / f"data/questions/{subject}.json").read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------
# SCIENCE rewrites (19)
# ----------------------------------------------------------------------------
SCIENCE_REWRITES: dict[int, dict] = {

    740: {  # Surgisphere — already the canonical exemplar pre-pivot; needs concrete closer
        "tier": 3,
        "question": "A May 2020 Lancet study from Surgisphere claimed hydroxychloroquine raised COVID death rates. WHO suspended its global HCQ trial within days. Both Lancet and NEJM retracted the papers within weeks: Surgisphere had no database. Which body suspended its global HCQ trial within days based on the Lancet finding?",
        "answer": "The WHO — its Solidarity trial's HCQ arm halted before the data was even verified",
        "choices": [
            "The WHO — its Solidarity trial's HCQ arm halted before the data was even verified",
            "The FDA — a US-only emergency revocation while every other country kept testing HCQ openly",
            "The CDC — a domestic recommendation change with no impact on any international clinical trial",
            "The NIH — a US-only research suspension that left WHO and European trials proceeding normally",
        ],
        "context": "Mehra et al. published in The Lancet (May 22, 2020) and NEJM (May 1, 2020). WHO suspended its Solidarity HCQ arm based on the Lancet finding; multiple national health agencies halted use. James Watson (Australia), Andrew Wang, and 200+ co-signatories demanded data verification. Surgisphere — a Chicago company with few employees and no track record — couldn't produce its claimed multinational hospital database. Both papers retracted June 4, 2020.",
    },

    753: {  # 2022 NAEP learning loss
        "tier": 3,
        "question": "The 2022 NAEP showed the largest declines in reading and math scores in the assessment's history — concentrated in poorer and minority districts where closures lasted longest. Sweden, which kept under-16 schools open, showed smaller losses. Which US student groups suffered the largest NAEP declines?",
        "answer": "Poor and minority students — exactly the groups GBD warned would be hit hardest by long closures",
        "choices": [
            "Poor and minority students — exactly the groups GBD warned would be hit hardest by long closures",
            "Wealthy suburban students — whose home tutors widened the closure-era gap most across all districts",
            "Students in every demographic equally — the NAEP collapse was uniform with no district-level pattern",
            "Rural students only — urban districts using remote learning matched in-person achievement easily",
        ],
        "context": "Studies from Stanford's CREDO, Harvard's Strategic Data Project, and McKinsey documented the disparate impact. Sweden's policy choice provided a real comparison case. The Great Barrington Declaration (Bhattacharya, Kulldorff, Gupta, Oct 2020) had specifically warned that extended closures would harm the poor and minorities most.",
    },

    900: {  # Murthy v Missouri / Twitter Files
        "tier": 4,
        "question": "Murthy v. Missouri (Supreme Court 2024) and the Twitter Files releases (2022-2023) documented federal agency coordination with social media platforms to flag scientific speech for suppression — including content from credentialed scientists like Bhattacharya and Kulldorff. Which two federal agencies appeared most often in the Twitter Files as flagging accounts to moderators?",
        "answer": "The FBI and the CDC — direct contact with Twitter content moderators flagging named accounts for action",
        "choices": [
            "The FBI and the CDC — direct contact with Twitter content moderators flagging named accounts for action",
            "The IRS and the SEC — financial-fraud referrals that triggered all the scientific-account suspensions noted",
            "The EPA and the FDA — environmental and pharmaceutical complaints driving every flagged-account decision",
            "The DOJ and the Treasury — criminal indictments that forced the suspension of every credentialed scientist",
        ],
        "context": "The Twitter Files (Matt Taibbi, Bari Weiss, Michael Shellenberger, others) showed extensive FBI and CDC contact with Twitter content moderators flagging specific accounts. Murthy v. Missouri reached the Supreme Court, which in 2024 ruled (6-3) that the plaintiffs lacked standing to sue — leaving the substantive question undecided. The case raised serious First Amendment questions that remain contested.",
    },

    908: {  # Viner snow prediction
        "tier": 4,
        "question": "In 2000 climate researcher David Viner of the UK Climate Research Unit told The Independent that snowfall in Britain would soon become 'a very rare and exciting event' and that children 'just aren't going to know what snow is.' British winters since have included multiple heavy-snow events. Which 2018 cold-snap event punctured the 'snowless Britain' prediction most visibly?",
        "answer": "The Beast from the East — Siberian-air cold snap that buried Britain in snow for over a week",
        "choices": [
            "The Beast from the East — Siberian-air cold snap that buried Britain in snow for over a week",
            "The Atlantic Heat Dome — a tropical-air event that proved Viner's snow prediction was exactly right",
            "Hurricane Ophelia — a tropical Atlantic storm causing zero snow anywhere within the British Isles",
            "The Saharan Plume — a North African dust event with no snowfall in any part of the United Kingdom",
        ],
        "context": "The Viner quote was widely repeated — it became one of the canonical examples of climate predictions that failed quickly. Other 'snow is gone' claims came from George Monbiot (2004) and various activist outlets. The 'Beast from the East' (2018) and Storm Eunice (2022) both produced heavy snowfall. Meanwhile, the UK Met Office data shows snow days have varied widely year-to-year with no clear monotonic decline. The point isn't that warming isn't happening — it's that media-amplified specific predictions deserve checking.",
    },

    926: {  # Koonin / hurricanes
        "tier": 4,
        "question": "Koonin in Unsettled devotes a chapter to hurricanes — he points out that the actual IPCC reports show no clear trend in global hurricane frequency or intensity, while media coverage during major hurricanes routinely attributes them to climate change. Who has spent decades documenting the gap between media climate-attribution claims and the IPCC's actual technical chapters?",
        "answer": "Roger Pielke Jr. — decades of work showing media attribution outruns formal IPCC confidence ratings",
        "choices": [
            "Roger Pielke Jr. — decades of work showing media attribution outruns formal IPCC confidence ratings",
            "Naomi Oreskes — the standard reference on disinformation and the institutional skeptic ecosystem",
            "Michael Mann — primary modeler whose hockey-stick reconstruction defined modern IPCC framing",
            "James Hansen — NASA scientist whose 1988 Senate testimony launched the entire climate research field",
        ],
        "context": "Roger Pielke Jr. has spent decades documenting the gap between media climate-attribution claims and the actual scientific literature on weather extremes. Hurricane landfall rates, tornado frequency, and global drought area show no clear monotonic climate signals. IPCC AR6 itself includes confidence ratings — many extreme-event trends are 'low confidence' for human attribution. The catastrophe framing relies on selective reading.",
    },

    931: {  # Lynas Six Degrees / Lomborg / Koonin
        "tier": 4,
        "question": "Mark Lynas published Six Degrees in 2007 — a book walking through projected impacts at each degree of warming. By 2020 Lynas had revised his view in Our Final Warning. Other voices, including Bjorn Lomborg and Steven Koonin, argued the catastrophe escalation was not supported by the actual IPCC technical chapters. Which 2021 Koonin book specifically argues the catastrophe coverage diverges from IPCC technical content?",
        "answer": "Unsettled — Koonin's chapter-by-chapter walkthrough of where media framing breaks from IPCC working-group findings",
        "choices": [
            "Unsettled — Koonin's chapter-by-chapter walkthrough of where media framing breaks from IPCC working-group findings",
            "Our Final Warning — Lynas's revised escalation written years before Koonin's involvement in the debate",
            "False Alarm — Lomborg's cost-benefit treatment of mitigation paths under various climate scenarios",
            "Merchants of Doubt — Oreskes's history of the funded skeptic ecosystem and its institutional reach",
        ],
        "context": "Lomborg's False Alarm (2020) walks through cost-benefit analysis for various proposed mitigation paths. Koonin's Unsettled (2021) does the same for specific scientific claims. The divergence between catastrophe coverage and IPCC technical content is not a fringe critique — it has been raised by credentialed mainstream voices for years. The kid's defense is reading both the Summary for Policymakers AND the underlying chapters.",
    },

    942: {  # Voyager 1
        "tier": 4,
        "question": "Voyager 1 launched on September 5, 1977 — a Titan IIIE-Centaur rocket carrying a probe the size of a small car, plus a gold record with sounds and images from Earth. In August 2012, after 35 years of travel, plasma data finally confirmed Voyager 1 had crossed the heliopause and entered interstellar space. What rock-and-roll song did Carl Sagan's committee include on the Voyager Golden Record?",
        "answer": "Chuck Berry's 'Johnny B. Goode' — picked by Sagan's team to represent rock and roll to anyone who finds it",
        "choices": [
            "Chuck Berry's 'Johnny B. Goode' — picked by Sagan's team to represent rock and roll to anyone who finds it",
            "Elvis Presley's 'Hound Dog' — chosen for the same reason but rejected at the final committee meeting late",
            "The Beatles' 'Here Comes the Sun' — added at the urging of NASA mission control's audio committee chair",
            "Bob Dylan's 'Blowin' in the Wind' — included as a representative of American protest music for the record",
        ],
        "context": "Voyager 1 was originally planned for a 5-year primary mission to Jupiter and Saturn. The 'Grand Tour' alignment allowed it to use gravity assists to reach interstellar space. As of 2025, it continues to transmit at very low data rate (still using its 1977-era hardware running on radioisotope thermoelectric generators). Voyager 2 crossed the heliopause in 2018. The Golden Record carries greetings in 55 languages and music from many cultures — Bach, Beethoven, Chuck Berry's 'Johnny B. Goode.'",
    },

    1021: {  # Salem hypothesis
        "tier": 4,
        "question": "The 'Salem hypothesis' — popularized in 1980s skeptic communities — claimed that creationism was disproportionately attractive to engineers. The underlying Pew survey data on professional creationism beliefs across STEM fields tells a different story. Whose 1980s online posts gave the 'Salem hypothesis' its name?",
        "answer": "Bruce Salem — whose Usenet posts coined the engineer-creationist claim later disproven by Pew data",
        "choices": [
            "Bruce Salem — whose Usenet posts coined the engineer-creationist claim later disproven by Pew data",
            "Salem Kirban — fundamentalist author whose 1970s prophecy books predated the actual hypothesis name",
            "Salem Witch Trials historians — whose work on 17th-century theology shaped the term but not the data",
            "Salem Massachusetts Pew chapter — whose 1985 community survey of engineers launched the discussion",
        ],
        "context": "The 'Salem hypothesis' is named for Bruce Salem, who proposed in 1980s-era online discussion that engineers seemed overrepresented in creationist circles. Actual Pew and other survey data show variation by specific discipline (biologists differ from chemists differ from engineers), by question wording (literal six-day creation vs guided-evolution vs theistic-evolution all get different responses), and by country. The broader recognition: glib claims about 'what scientists believe' usually reduce complicated empirical questions to a sound-bite that serves the speaker's argument better than it tracks reality.",
    },

    1075: {  # Proximal Origin paper
        "tier": 5,
        "question": "The 'Proximal Origin' paper (Andersen et al., Nature Medicine, March 2020) declared SARS-CoV-2 'is not a laboratory construct or a purposefully manipulated virus.' FOIA'd Slack messages later showed authors privately discussed lab-leak as plausible while drafting the public dismissal. Which two US agencies by 2023 publicly assessed lab-leak as the most likely origin of SARS-CoV-2?",
        "answer": "The FBI and the Department of Energy — both publicly assessed lab-leak as the most likely origin by 2023",
        "choices": [
            "The FBI and the Department of Energy — both publicly assessed lab-leak as the most likely origin by 2023",
            "The CIA and the State Department — both formally ruled out lab-leak in joint 2022 assessments released",
            "The Pentagon and the NSA — both classified all origin assessments and released no public statement at all",
            "The CDC and the NIH — both publicly endorsed Proximal Origin's natural-origin conclusion without revision",
        ],
        "context": "The Proximal Origin authors included Kristian Andersen, Eddie Holmes, and Robert Garry. The FOIA'd Slack messages and emails (released 2023) showed the authors discussing lab leak as plausible while drafting public statements that called it implausible. The paper was widely cited to label lab-leak claims 'misinformation' throughout 2020-2022. By 2023, FBI and DOE publicly favored lab-leak as the most likely origin.",
    },

    1118: {  # CDC vaccine schedule expansion
        "tier": 5,
        "question": "The CDC childhood vaccine schedule has expanded substantially over four decades. In 1986, children received about 11 doses by age 6. By 2024, children are recommended to receive 70+ doses by age 18 across roughly 16 different vaccines. Approximately how many doses did the 1986 schedule call for by age 6, before the expansion?",
        "answer": "About 11 doses — by age 6, compared to the 70+ doses by age 18 in the current 2024 schedule",
        "choices": [
            "About 11 doses — by age 6, compared to the 70+ doses by age 18 in the current 2024 schedule",
            "About 50 doses — by age 6, making the 2024 schedule only a slight expansion over the early framework",
            "About 70 doses — by age 6, matching the current schedule and showing essentially no expansion since 1986",
            "About 2 doses — by age 6, with virtually no childhood vaccination program prior to the 1986 NCVIA act",
        ],
        "context": "Each individual vaccine has typically been tested before licensing, but the question of cumulative interaction across the schedule is less well-studied. A randomized trial comparing the full schedule against any alternative would be considered unethical (it would require withholding vaccines). Observational studies face significant confounding. RFK Jr. and others have made the 'no placebo-controlled schedule trial' point as a structural critique that the science deserves better than dismissal. The 1986 NCVIA created the manufacturer liability shield that critics argue removed normal market accountability.",
    },

    1123: {  # Martin Kulldorff
        "tier": 5,
        "question": "Martin Kulldorff was a Harvard Medical School biostatistician who co-developed SaTScan — the standard disease-surveillance method US public health authorities use to detect outbreaks. After signing the Great Barrington Declaration, he was removed from the CDC's ACIP Vaccine Safety Subgroup and lost his Harvard position. What is the name of the outbreak-detection method Kulldorff co-developed and that the very agencies sanctioning him still use?",
        "answer": "SaTScan — the space-time scan statistic, still in use at CDC and state public-health agencies today",
        "choices": [
            "SaTScan — the space-time scan statistic, still in use at CDC and state public-health agencies today",
            "OpenSAFELY — the UK platform NHS used for COVID studies but never adopted in the US for surveillance",
            "WHONET — antimicrobial-resistance tracker maintained by the WHO with no role in US outbreak detection",
            "EpiInfo — a different CDC data tool from the 1990s for case-report entry, not space-time surveillance",
        ],
        "context": "Kulldorff developed the SaTScan space-time scan statistic widely used in disease-surveillance work. He served on the FDA's Vaccines and Related Biological Products Advisory Committee and the CDC's ACIP Vaccine Safety Subgroup. After the GBD, he was removed from the ACIP subgroup and lost his Harvard position. The case is one of the cleanest examples of how publicly questioning policy during COVID could result in professional consequences even for credentialed researchers.",
    },

    1124: {  # Peter McCullough
        "tier": 5,
        "question": "Peter McCullough is a cardiologist who chaired the Truth for Health Foundation's COVID treatment committee and published over 50 COVID-related papers — many on early-treatment protocols. Which medical board moved to revoke his certifications using vague 'misinformation' charges?",
        "answer": "The American Board of Internal Medicine — moved to revoke McCullough's certifications, citing 'misinformation'",
        "choices": [
            "The American Board of Internal Medicine — moved to revoke McCullough's certifications, citing 'misinformation'",
            "The American Medical Association — a membership group with no certifying authority over any physician",
            "The World Medical Association — an international NGO that holds no US licensing or board authority",
            "The Mayo Clinic Internal Review Board — McCullough's local hospital, with no national board involvement",
        ],
        "context": "The ABIM and Texas Medical Board both moved against McCullough. Similar actions affected Pierre Kory, Ryan Cole, and other dissenting physicians. The legal questions remain ongoing — some board actions have been challenged in court, and several have been blocked or reversed. The pattern is a generalizable one: professional certifying organizations gained new power during COVID to discipline dissent on policy questions framed as 'misinformation,' and have been slow to update as the underlying claims have been re-evaluated.",
    },

    1131: {  # MRSA / antibiotic resistance
        "tier": 5,
        "question": "Methicillin-resistant Staphylococcus aureus (MRSA) emerged in the 1960s, just years after methicillin itself was introduced. By the 2000s, MRSA had become a major hospital and community pathogen. Why have major pharmaceutical companies exited antibiotic R&D despite the resistance crisis?",
        "answer": "Antibiotics are held in reserve to delay resistance — low sales volume can't recoup development costs",
        "choices": [
            "Antibiotics are held in reserve to delay resistance — low sales volume can't recoup development costs",
            "Antibiotic patents now expire in months — making FDA approval an automatic loss for any developer",
            "All new antibiotic candidates have been banned — outlawed by FDA rulings issued in the early 2010s",
            "Bacteria stopped evolving resistance after 2010 — making new antibiotic R&D unnecessary in clinical care",
        ],
        "context": "Antibiotic R&D is structurally unprofitable for pharmaceutical companies: any new antibiotic is held in reserve to delay resistance, which means low sales volume, which means insufficient return on the development cost. Many large pharma firms have shut down their antibiotic divisions. The result is a real public-health crisis that does not fit standard market incentives. Government push-and-pull initiatives (BARDA, GAIN Act, AMR Action Fund) have had limited success. The recognition skill: market failure is real here.",
    },

    1133: {  # diet-heart hypothesis / Ancel Keys
        "tier": 5,
        "question": "The 'diet-heart hypothesis' — that saturated fat and cholesterol cause heart disease — dominated US nutrition policy from the 1970s through the 2010s. Whose Seven Countries Study became its foundation, and what selection-bias critique has been leveled against him?",
        "answer": "Ancel Keys — critics show he excluded countries whose data did not fit his saturated-fat hypothesis",
        "choices": [
            "Ancel Keys — critics show he excluded countries whose data did not fit his saturated-fat hypothesis",
            "Robert Atkins — whose 1972 low-carb diet book became the actual basis of all federal nutrition policy",
            "Linus Pauling — whose vitamin C work was reframed by the USDA as the diet-heart hypothesis foundation",
            "Nathan Pritikin — whose 1980 program was unrelated to Keys but is often confused with the Seven Countries",
        ],
        "context": "Ancel Keys's Seven Countries Study has been criticized for selection bias (Keys reportedly excluded countries that did not fit his hypothesis). The Minnesota Coronary Experiment (1968-1973) was a randomized trial that failed to show benefit from reducing saturated fat — and was not published for over 40 years. Nina Teicholz's The Big Fat Surprise (2014) made the historical case. The current mainstream nutrition view is much more cautious about saturated-fat alarmism than the 1980s version was, though not yet converged.",
    },

    1137: {  # Wright Brothers / Kitty Hawk
        "tier": 5,
        "question": "The Wright Brothers' first powered flight was at Kitty Hawk, North Carolina, on December 17, 1903. The biology of flight had been studied for centuries by then — birds, bats, insects all fly. Yet ornithologists in the late 1800s widely believed powered human flight was impossible. What specific engineering innovation did the Wrights add that bird-flight observation had not pointed to?",
        "answer": "Three-axis control — independent pitch, roll, and yaw via wing-warping plus rear rudder",
        "choices": [
            "Three-axis control — independent pitch, roll, and yaw via wing-warping plus rear rudder",
            "The internal combustion engine — invented from scratch by the Wright Brothers on their workbench",
            "Lighter-than-air gas filling — derived from bird-bone observation and applied to their wing structure",
            "Flapping wings — copied directly from albatross flight after years of ornithological field study",
        ],
        "context": "Sir George Cayley laid the engineering principles for fixed-wing aircraft in 1799 — over a century before the Wrights. Otto Lilienthal flew gliders in the 1890s and was killed in one in 1896. Samuel Pierpont Langley, secretary of the Smithsonian Institution, tried to build powered aircraft and failed. The Wrights' contribution was three-axis control. Biological flight uses flapping wings; aircraft use fixed wings with separate engines. The recognition skill: nature has not always shown us all the engineering options.",
    },

    1154: {  # amyloid hypothesis / Lesné
        "tier": 5,
        "question": "The amyloid hypothesis of Alzheimer's disease — that beta-amyloid plaques cause the cognitive decline — has dominated the field since the late 1980s. Over $1 billion has been spent on amyloid-clearing drugs with disappointing results. Whose 2022 Science investigation raised serious concerns about possible image manipulation in the foundational Lesné et al. papers?",
        "answer": "Charles Piller — the 2022 Science investigation flagged probable Western-blot image manipulation in Lesné et al.",
        "choices": [
            "Charles Piller — the 2022 Science investigation flagged probable Western-blot image manipulation in Lesné et al.",
            "Sylvain Lesné — the Minnesota researcher whose own retraction notice triggered the field's revision in 2022",
            "Karen Ashe — the senior coauthor who in 2022 published a public defense of the original images herself",
            "John Ioannidis — whose 2005 paper on false research findings is unrelated to Alzheimer's-specific work",
        ],
        "context": "A 2022 Science investigation by Charles Piller raised serious concerns about possible image manipulation in foundational amyloid-hypothesis papers (Lesné et al.). The amyloid hypothesis is not dead, but the assumption that clearing amyloid would automatically reverse cognition has been undermined by negative trial after negative trial. Alternative hypotheses (tau, neuroinflammation, infectious, vascular) have gained more attention. The recognition skill: when a major field-defining hypothesis fails to translate to working drugs for decades, the hypothesis itself may need revision.",
    },

    1279: {  # Guatemala syphilis study
        "tier": 5,
        "question": "In 2005 Wellesley historian Susan Reverby found archived records: between 1946 and 1948, US Public Health Service researcher John Cutler (later a Tuskegee investigator) deliberately infected roughly 1,300 Guatemalan prisoners, soldiers, and psychiatric patients with syphilis and gonorrhea — often by inoculating bacteria onto abrasions or genital surfaces. Which later US President formally apologized to Guatemala in October 2010 after the records came to light?",
        "answer": "Barack Obama — formally apologized to Guatemala in October 2010 after Reverby's archive work made it public",
        "choices": [
            "Barack Obama — formally apologized to Guatemala in October 2010 after Reverby's archive work made it public",
            "George W. Bush — issued the formal apology in 2007 right after Reverby's papers first reached the State Dept",
            "Bill Clinton — apologized in his 1997 Tuskegee speech, which also covered the Guatemala study findings",
            "Jimmy Carter — apologized in his 1980 human-rights speech, which named the Guatemala USPHS study openly",
        ],
        "context": "Reverby's 2010 paper made the case public. The Guatemala case sits with Tuskegee (1932-1972), Sims's enslaved-women surgeries, the Henrietta Lacks case, and the Belmont Report (1979) as foundational US medical-ethics history.",
    },

    1297: {  # Robert Malone
        "tier": 3,
        "question": "Robert Malone helped pioneer the lipid-nanoparticle mRNA delivery technology in the late 1980s. On December 29, 2021 he was banned from Twitter for COVID-related posts. Whose podcast had Malone appeared on just before the December 2021 Twitter ban took effect?",
        "answer": "Joe Rogan's — the December 2021 appearance preceded the Twitter ban by days, drawing further scrutiny",
        "choices": [
            "Joe Rogan's — the December 2021 appearance preceded the Twitter ban by days, drawing further scrutiny",
            "Lex Fridman's — a long-form interview that drew no platform response from Twitter or other platforms",
            "Ben Shapiro's — a Daily Wire interview unrelated to Malone's mRNA history or COVID-related concerns",
            "Tucker Carlson's — a Fox News appearance during 2020 that preceded all of his mRNA-related statements",
        ],
        "context": "Malone holds early lipid-nanoparticle mRNA-delivery patents from his 1989-91 work. His Twitter ban (December 29, 2021) followed an appearance on Joe Rogan's podcast. His specific factual claims were a mix of well-supported, contested, and probably wrong — like most public-figure commentary in a crisis. The point: the institutional response was deplatforming rather than engagement, and credentialed expertise didn't protect him.",
    },

    1298: {  # Children's Health Defense
        "tier": 3,
        "question": "Children's Health Defense, founded by RFK Jr. in 2018, is a major organization litigating vaccine policy. In 2022, two major Meta-owned platforms deplatformed it during active phases of pediatric mRNA debate. Which two Meta platforms deplatformed Children's Health Defense in 2022?",
        "answer": "Facebook and Instagram — both Meta platforms deplatformed CHD in 2022 during active pediatric-mRNA debate",
        "choices": [
            "Facebook and Instagram — both Meta platforms deplatformed CHD in 2022 during active pediatric-mRNA debate",
            "Twitter and YouTube — the two non-Meta platforms instead, while Facebook left CHD's account fully active",
            "TikTok and Snapchat — youth platforms that took action while Facebook chose not to restrict CHD's reach",
            "Reddit and LinkedIn — discussion platforms that suspended CHD while leaving its Facebook page running",
        ],
        "context": "CHD deplatforming preceded Bhattacharya's NIH confirmation by about three years. The pediatric mRNA vaccine debate was active during the deplatforming period. Whether one agrees with CHD's specific positions, the documented pattern — major-platform exclusion during active phases of contested policy debate — is one mechanism by which speech-control infrastructure shapes political outcomes. Murthy v Missouri (2024) reached the Supreme Court on related state-action questions.",
    },
}


# ----------------------------------------------------------------------------
# ANIMAL rewrites (8)
# ----------------------------------------------------------------------------
ANIMAL_REWRITES: dict[int, dict] = {

    316: {  # Peppered moth — industrial melanism
        "tier": 4,
        "question": "Peppered moth populations in industrial Britain shifted from mostly light-bodied to mostly dark-bodied during the 1800s as soot blackened trees. They shifted back as air pollution declined. Which specific evolutionary mechanism explains the rapid back-and-forth color shift?",
        "answer": "Directional selection on a heritable color variant — soot-darkened trees favored dark moths",
        "choices": [
            "Directional selection on a heritable color variant — soot-darkened trees favored dark moths",
            "Lamarckian inheritance of acquired soot stains — moth bodies darkened by direct exposure to coal smoke",
            "Random genetic drift in small isolated patches — chance fixation of dark variants in forest fragments",
            "A founder effect from a single dark mutant — one moth's lineage swept industrial areas of all Britain",
        ],
        "context": "Peppered moth (Biston betularia) industrial melanism is the textbook case. Kettlewell's 1950s experiments, criticized then revalidated by Cook et al. (2012), Majerus (2012). The genetic basis is a transposable element in the cortex gene.",
    },

    612: {  # Luna moth tails
        "tier": 2,
        "question": "Luna moths have long twisted tails on their hind wings. When bats hunt them by echolocation, the clicks hit the tails instead of the body. Which function do the spinning tails perform during a bat strike?",
        "answer": "Acoustic decoys — sonar reflects off the spinning tails more strongly than off the body",
        "choices": [
            "Acoustic decoys — sonar reflects off the spinning tails more strongly than off the body",
            "Small gliders — they slow the moth enough that the diving bat overshoots its strike",
            "Sonar jammers — emitting a high-frequency click that confuses the bat's echolocation",
            "Chemical decoys — a sticky scent on the tails draws bats away from the moth's body",
        ],
        "context": "Barber et al. (PNAS, 2015) showed luna moth tails confuse bat echolocation — the spinning tails reflect a stronger signal than the body, drawing the strike away. Acoustic decoy evolved.",
    },

    645: {  # Darwin / Madagascar orchid / Xanthopan
        "tier": 3,
        "question": "Darwin saw a Madagascar orchid with a 30-cm nectar tube. He predicted a hawkmoth with a tongue of matching length must exist. Decades after his death, the moth was found. What is the predicted moth's name — chosen specifically to honor Darwin's foresight?",
        "answer": "Xanthopan morganii praedicta — the 'praedicta' epithet honors Darwin's prediction of its existence",
        "choices": [
            "Xanthopan morganii praedicta — the 'praedicta' epithet honors Darwin's prediction of its existence",
            "Macroglossum darwinii — a smaller hummingbird hawkmoth named for Darwin but with a short tongue",
            "Manduca sexta angraeci — the tomato hornworm relative, never predicted to live in Madagascar at all",
            "Sphinx ligustri madagascariensis — the privet hawkmoth subspecies with no role in the Darwin prediction",
        ],
        "context": "Xanthopan morganii praedicta — named for Darwin's prediction. Pollinator of Angraecum sesquipedale, the Madagascar star orchid. Coevolution of corolla tube length and proboscis length. Wallace also predicted it.",
    },

    697: {  # Octopus / vertebrate eyes
        "tier": 5,
        "question": "Octopus and vertebrate camera-type eyes are remarkably similar but evolved independently from a last common ancestor with no eye. Vertebrate retinas have a blind spot because nerves pass in front of photoreceptors. Cephalopod retinas do not. Which retinal feature do vertebrates have that cephalopods lack — the visible signature of the independent origin?",
        "answer": "A blind spot — vertebrate nerves exit through the retina; cephalopod nerves exit behind, leaving no gap",
        "choices": [
            "A blind spot — vertebrate nerves exit through the retina; cephalopod nerves exit behind, leaving no gap",
            "A pupil that contracts to a slit — octopus pupils are W-shaped while vertebrate pupils are simple holes",
            "A spherical crystalline lens — octopus lenses use a graded index instead, so they have no spherical version",
            "A rear-facing photoreceptor layer — octopus retinas have a forward-facing layer instead of vertebrate flip",
        ],
        "context": "Octopus camera-eye: photoreceptors face the light, retinal nerves exit behind. Vertebrate camera-eye: photoreceptors face away from light, nerves exit through the retina creating a blind spot. Same engineering, different developmental solutions. Conway Morris's Life's Solution discusses this; a textbook exemplar of imperfect convergence.",
    },

    740: {  # Dolphins
        "tier": 1,
        "question": "Dolphins sometimes push injured pod-mates up to the surface. Which class of animal are dolphins, and why is surfacing life-or-death?",
        "answer": "Mammals — they breathe air with lungs and would drown if held below the surface",
        "choices": [
            "Mammals — they breathe air with lungs and would drown if held below the surface",
            "Fish with lungs — air-breathing but also extracting oxygen through their gill slits",
            "Amphibians — breathing through skin but needing surface air for an extra boost",
            "Reptiles — lung-breathers with slow hearts that sleep face-down for long stretches",
        ],
        "context": "Dolphins, whales, and porpoises are mammals — they breathe air. If hurt and unable to swim, they drown. Pod-mates lifting an injured dolphin to breathe is well documented.",
    },

    741: {  # Orca wave-washing
        "tier": 1,
        "question": "Off Antarctica, orca pods swim in formation and lift a wave together that washes a seal off a floating ice chunk. Which behavior does this prove orcas are capable of?",
        "answer": "Coordinated planned hunting — each whale knows its part of the wave and times its swim",
        "choices": [
            "Coordinated planned hunting — each whale knows its part of the wave and times its swim",
            "Random play behavior — the seal getting knocked off is just an accidental coincidence",
            "Mating display — only adult males perform the wave maneuver as a courtship show",
            "Curious exploration — orcas push waves at icebergs to see what falls off the top",
        ],
        "context": "'Wave-washing' is documented in transient (mammal-eating) orcas off Antarctica. The whales swim in formation, lift a wave together, and hit the floe — practiced, taught to young.",
    },

    760: {  # African wild dogs / sneezing votes
        "tier": 2,
        "question": "African wild dogs (Lycaon pictus) 'vote' before a hunt. The pack 'sneezes' to signal whether to set off. More sneezes mean a hunt is more likely. Which scientific term best fits the sneeze-tallying behavior?",
        "answer": "Quorum decision-making — the pack aggregates each dog's sneeze into a single hunt-or-rest call",
        "choices": [
            "Quorum decision-making — the pack aggregates each dog's sneeze into a single hunt-or-rest call",
            "Pure reflex sneezing — the sneezes are an involuntary nasal reaction with no role in hunt timing",
            "Alpha-only command — only the lead pair's sneeze actually triggers the hunt to start at all",
            "Predator-alarm call — sneezes warn of danger and humans mistake the warning for a vote signal",
        ],
        "context": "Walker et al. (2017) showed African wild dogs (Lycaon pictus) sneeze to vote on whether to start a hunt. The threshold is lower if a dominant dog has already sneezed — but lower-ranked dogs do influence the call.",
    },

    933: {  # Coral snakes / vipers / front fangs
        "tier": 5,
        "question": "Coral snakes (elapid, neurotoxic, fixed front fangs) and viperids (rattlesnakes, hemotoxic, hinged front fangs) have totally different venoms and totally different fang mechanics. Phylogenetic studies (Vonk et al., Nature 2008) show front-fang systems evolved twice independently. How many times have front-fang systems independently evolved in snakes?",
        "answer": "Twice — once in viperids (hinged) and once in elapids (fixed), each via a different developmental route",
        "choices": [
            "Twice — once in viperids (hinged) and once in elapids (fixed), each via a different developmental route",
            "Once — front fangs are the ancestral snake state and most snake lineages have since lost them entirely",
            "Three times — independently in viperids, elapids, and the colubrid rear-fanged lineage as well evolved",
            "Zero times — all front-fang snakes share one continuous lineage and the 'twice' claim is a misreading",
        ],
        "context": "Vonk et al. (Nature, 2008) and others show front-fang systems evolved twice in snakes — once in viperids (hinged), once in elapids (fixed). Convergent on the same adaptive solution: fast strike, efficient venom delivery. Different developmental routes, similar engineering.",
    },
}


# ----------------------------------------------------------------------------
# COOKING rewrites (4)
# ----------------------------------------------------------------------------
COOKING_REWRITES: dict[int, dict] = {

    347: {  # American Thanksgiving menu
        "tier": 5,
        "question": "American Thanksgiving has a fixed menu (turkey, stuffing, cranberry sauce, mashed potato, pumpkin pie) that feels timeless. Most was assembled in the 1800s; the 1621 Plymouth feast had wildfowl and venison. Which 19th-century magazine editor campaigned for years to nationalize Thanksgiving and fix the menu?",
        "answer": "Sarah Josepha Hale — Godey's Lady's Book editor; her 17-year campaign convinced Lincoln to nationalize it",
        "choices": [
            "Sarah Josepha Hale — Godey's Lady's Book editor; her 17-year campaign convinced Lincoln to nationalize it",
            "Fannie Farmer — Boston Cooking School Cook Book author who codified American measurements but not the menu",
            "Julia Child — whose Mastering the Art of French Cooking established the holiday menu in mid-20th century",
            "Amelia Simmons — author of 1796 American Cookery, the first US cookbook published after independence",
        ],
        "context": "The Thanksgiving menu was assembled in the Lincoln era and Victorian magazines (Sarah Josepha Hale, Godey's Lady's Book). The 1621 Plymouth feast had wildfowl, venison, corn porridge. The 'timeless' menu is a 19th-century construction. The broader lesson: culinary tradition is often a recent construction projected backward - true of Italian tomato cuisine, French haute cuisine, American regional dishes.",
    },

    682: {  # Lardo di Colonnata
        "tier": 3,
        "question": "In the marble-quarry village of Colonnata in Tuscany, an ancient tradition packs slabs of pure pork back-fat in marble basins with sea salt, garlic, rosemary, and herbs. Which material is the curing vessel made from — and why does its source matter to the dish's identity?",
        "answer": "Marble — the same Carrara marble quarried by the workers, who cured the fat in offcut basins underground",
        "choices": [
            "Marble — the same Carrara marble quarried by the workers, who cured the fat in offcut basins underground",
            "Volcanic basalt — the dark stone of the Tuscan hills, traditional for olive presses but not for any lardo",
            "Slate slabs — the Ligurian roofing material brought up by carts but never used in Colonnata's curing",
            "Terracotta jars — fired clay vessels common across Tuscany but not associated with the Colonnata trade",
        ],
        "context": "Lardo di Colonnata IGP: pure pork back-fat cured in marble basins with sea salt, garlic, rosemary, pepper, herbs. Tradition dates to medieval marble quarries. Fat as finished delicacy. The marble basins (conche) are quarry-worker offcuts — the dish is inseparable from the labor that built it.",
    },

    713: {  # Roman garum
        "tier": 5,
        "question": "Excavations at Pompeii, Cadiz (ancient Gades), Lixus in Morocco, and other Roman ports uncovered garum factories — stone vats where small fish lacto-fermented in salt for months. The factories shipped amphorae of the salty sauce empire-wide. Which 1st-century Roman cookbook calls for garum as a staple seasoning on nearly every page?",
        "answer": "Apicius's De Re Coquinaria — the 1st-century Roman cookbook that uses garum as a near-universal seasoning",
        "choices": [
            "Apicius's De Re Coquinaria — the 1st-century Roman cookbook that uses garum as a near-universal seasoning",
            "Cato's De Agri Cultura — the agricultural manual full of farm-economy notes but no fish-sauce recipe at all",
            "Pliny's Natural History — the encyclopedia mentioning food but containing no actual cooking recipe content",
            "Columella's De Re Rustica — the agricultural treatise on estate management but with no kitchen recipes",
        ],
        "context": "Roman garum was industrial-scale fermented fish sauce. Factories at Pompeii, Cadiz (Garum Sociorum, the brand), Lixus, Tingis, Baelo Claudia — large stone vats, amphorae shipping across the empire. Apicius's De Re Coquinaria cites it constantly. Modern relatives: Southeast Asian fish sauce, colatura.",
    },

    732: {  # Pacific Northwest salmon
        "tier": 5,
        "question": "Pacific Northwest Native peoples — Chinook, Coast Salish, Tlingit, Haida — built civilizations partly on salmon preservation. Salmon was caught in fish weirs in summer, smoked on cedar racks over slow alder fires for days, stored for winter. Which wood smoke do these traditions use for the long slow smoking of salmon?",
        "answer": "Alder — burns slow, throws clean light smoke; the dominant wood for traditional cedar-rack salmon smoking",
        "choices": [
            "Alder — burns slow, throws clean light smoke; the dominant wood for traditional cedar-rack salmon smoking",
            "Hickory — the dominant Southern barbecue wood, used heavily in the Carolinas but not in the Pacific NW",
            "Mesquite — the Southwestern desert wood preferred in Texas barbecue but not native to Northwest coasts",
            "Applewood — the orchard wood typical of New England smokehouses with no role in salmon-smoking tradition",
        ],
        "context": "Pacific Northwest Native peoples (Chinook, Coast Salish, Tlingit, Haida, Kwakwaka'wakw, Nuu-chah-nulth) built dense, settled, hierarchical civilizations on salmon-preservation backbone. Cedar smoking racks, fish weirs, smokehouses, dugout canoes. Pre-contact caloric load: ~300-500 lb salmon/person/year. Potlatch economies, cedar architecture. Alder is the traditional smoking wood.",
    },
}


# ----------------------------------------------------------------------------
# GEOGRAPHY rewrites (9)
# ----------------------------------------------------------------------------
GEOGRAPHY_REWRITES: dict[int, dict] = {

    864: {  # St Thomas Christians / Malabar
        "tier": 4,
        "question": "Along India's Malabar coast, Syrian-rite Christian communities trace their founding to the Apostle Thomas (~52 AD). When Portuguese missionaries arrived in 1498, they found organized Indian Christian churches using Syriac liturgy. Which Persia-based church sent the bishops via Indian Ocean monsoon trade for over a millennium before the Portuguese arrived?",
        "answer": "The Church of the East — the 'Nestorian' Persian church sent bishops via the monsoon trade for 1,000+ years",
        "choices": [
            "The Church of the East — the 'Nestorian' Persian church sent bishops via the monsoon trade for 1,000+ years",
            "The Ethiopian Tewahedo Church — Aksumite missionaries from the Ge'ez-speaking Christian kingdom of Africa",
            "The Roman Catholic Church — direct Latin missions sent under papal authority before any Portuguese arrival",
            "The Byzantine Patriarchate — Greek-rite envoys dispatched from Constantinople during the Macedonian era",
        ],
        "context": "St Thomas Christians (Nasrani) of Kerala trace their origins to the Apostle Thomas's 52 AD mission to Muziris (modern Kodungallur). Documentation grows from the 4th century onward, with the Church of the East (Nestorian, based in Persia) sending bishops via Indian Ocean monsoon trade. By 1498 when Vasco da Gama landed at Calicut, an organized community of ~200,000 Syrian-rite Christians existed across the Malabar coast. Portuguese efforts to Latinize them (Synod of Diamper, 1599) provoked the 1653 Coonan Cross Oath schism. Today the community includes Syro-Malabar Catholic, Syro-Malankara Catholic, Malankara Orthodox, Mar Thoma Syrian, and several other branches.",
    },

    904: {  # Vatican II
        "tier": 5,
        "question": "Vatican II (1962-65) transformed Catholic worship: vernacular liturgy replacing universal Latin; renewed biblical scholarship; revised ecumenical relations; Gaudium et Spes engaging modernity. Which Latin American theological movement emerged from the 1968 Medellín bishops' conference applying Vatican II to local poverty?",
        "answer": "Liberation theology — Gutiérrez's 'preferential option for the poor' systematized at Medellín CELAM II (1968)",
        "choices": [
            "Liberation theology — Gutiérrez's 'preferential option for the poor' systematized at Medellín CELAM II (1968)",
            "Pentecostal renewal — the Assemblies of God revival that swept Brazil and Chile in the same decade exactly",
            "Vatican traditionalism — the Lefebvrist movement rejecting Vatican II changes and demanding the Latin Mass",
            "Marian devotion — the Guadalupe-centered renewal movement that displaced Vatican II reforms in the region",
        ],
        "context": "Vatican II (Second Vatican Council, 1962-65, John XXIII opened it; Paul VI closed it) produced 16 documents reshaping Catholic worship, scholarship, ecumenism, and engagement with modernity. The vernacular liturgy (replacing Latin) was the most visible change; biblical scholarship and ecumenical openness were equally important. Regional impact varied: Latin America produced liberation theology (Gutierrez, Boff, Sobrino); Africa developed Africanized liturgy and the African Synod (1994); Western Catholic Mass attendance dropped sharply; Indian and East Asian Catholicism remained more conservative. The Council's interpretation ('hermeneutic of rupture' vs 'hermeneutic of reform' — Benedict XVI's terms) remains contested.",
    },

    905: {  # Liberation theology / Ratzinger
        "tier": 5,
        "question": "Latin American liberation theology emerged from the 1968 Medellín bishops' conference. Gustavo Gutiérrez's A Theology of Liberation (1971) systematized 'God's preferential option for the poor.' Which Vatican cardinal — later Pope Benedict XVI — issued the 1984 and 1986 instructions warning against Marxist categories in the movement?",
        "answer": "Joseph Ratzinger — CDF prefect, his 1984 and 1986 instructions warned against Marxist political categories",
        "choices": [
            "Joseph Ratzinger — CDF prefect, his 1984 and 1986 instructions warned against Marxist political categories",
            "Jorge Bergoglio — later Pope Francis, whose Argentine Jesuit background actually fully embraced the movement",
            "Carlo Maria Martini — Milan archbishop whose Jesuit progressive identity defined the European reception of it",
            "Angelo Sodano — Vatican Secretary of State whose Chilean diplomatic role focused the response to Pinochet",
        ],
        "context": "Liberation theology developed from the 1968 Medellín Conference of Latin American Catholic bishops (CELAM II) applying Vatican II's preferential option for the poor to Latin American conditions. Gustavo Gutierrez's A Theology of Liberation (1971) synthesized the framework; Leonardo Boff (Brazilian Franciscan), Jon Sobrino (Salvadoran Jesuit), Juan Luis Segundo (Uruguayan Jesuit) developed it. Cardinal Joseph Ratzinger's 1984 and 1986 CDF instructions (later Pope Benedict XVI) warned against Marxist political categories but affirmed the legitimate concern for the poor. Pope Francis (Jorge Bergoglio, Argentine Jesuit, elected 2013) has been more sympathetic, while Pentecostal growth in Latin America has shifted the broader religious geography.",
    },

    908: {  # Iran 1979 / velayat-e faqih
        "tier": 5,
        "question": "Iran's 1979 Revolution overthrew the Pahlavi Shah and established the Shia Islamic Republic under Khomeini's velayat-e faqih (Guardianship of the Jurist) doctrine. What does 'velayat-e faqih' mean in plain terms, and where did Khomeini develop the doctrine in exile?",
        "answer": "'Rule by the senior jurist' — Khomeini developed the doctrine in his Najaf exile lectures (Islamic Government, 1970)",
        "choices": [
            "'Rule by the senior jurist' — Khomeini developed the doctrine in his Najaf exile lectures (Islamic Government, 1970)",
            "'Return of the Twelfth Imam' — the medieval Twelver position that Khomeini's 1979 movement also fully embraced",
            "'Sovereignty of the Iranian people' — a republican doctrine drawn from the French Revolution, not Shia tradition",
            "'Authority of the Saudi king' — a Sunni Wahhabi doctrine adapted by Khomeini after his exile in Saudi Arabia",
        ],
        "context": "Khomeini's velayat-e faqih doctrine (developed in his Najaf exile lectures published as Islamic Government, 1970) was a radical innovation in Twelver Shia political theory. The traditional Shia position held that legitimate political authority awaited the return of the Twelfth Imam; Khomeini argued senior jurists could exercise comprehensive political authority in the meantime. The 1979 Revolution overthrew Shah Mohammad Reza Pahlavi and established the Islamic Republic with the Supreme Leader (Khomeini, then Khamenei from 1989) holding final authority over Parliament and President. The Iran-Iraq War (1980-88), Hezbollah's founding (1982), and Iranian regional religious-political projection since have institutionalized the Shia-revolutionary geography.",
    },

    912: {  # Lebanon civil war / confessionalism
        "tier": 5,
        "question": "The Lebanese Civil War (1975-90) killed ~150,000 in a country with 18 officially recognized confessional groups: Maronite, Greek Orthodox, Sunni, Shia, Druze, and more. The 1989 Taif Agreement preserved the 1943 National Pact's confessional allocation. Under the 1943 National Pact, which three Lebanese top offices are reserved for the Maronite, Sunni, and Shia communities respectively?",
        "answer": "President (Maronite), Prime Minister (Sunni), Speaker of Parliament (Shia) — fixed by the 1943 National Pact",
        "choices": [
            "President (Maronite), Prime Minister (Sunni), Speaker of Parliament (Shia) — fixed by the 1943 National Pact",
            "President (Sunni), Prime Minister (Shia), Speaker of Parliament (Maronite) — rotation rule changed at Taif",
            "President (Shia), Prime Minister (Maronite), Speaker of Parliament (Druze) — drawn from French Mandate rules",
            "President (Druze), Prime Minister (Greek Orthodox), Speaker of Parliament (Sunni) — Ottoman millet inheritance",
        ],
        "context": "Lebanon's National Pact (1943) allocated political power confessionally: President Maronite, Prime Minister Sunni, Speaker of Parliament Shia, parliamentary seats 6:5 Christian-Muslim. The Civil War (1975-90) was triggered by sectarian-political instability — Palestinian refugees (post-1948 and post-1967), Maronite-Palestinian conflict, Syrian intervention (1976), Israeli invasion (1982), Hezbollah's emergence (1982), the Sabra and Shatila massacre (1982). The Taif Agreement (1989) preserved confessional power-sharing but recalibrated the ratios (parliament now 5:5). Lebanon's sectarian system is a major case study for religious-political institutional design. Robert Fisk's Pity the Nation (1990) is a major account.",
    },

    913: {  # South Sudan 2011
        "tier": 5,
        "question": "South Sudan voted overwhelmingly (98.83%) to secede from Sudan in the 2011 referendum, becoming the world's newest internationally recognized state. The Christian-majority south had fought two civil wars (1955-72 and 1983-2005) against the Muslim-majority north. Which Sudanese president imposed sharia law in 1983, triggering the second civil war?",
        "answer": "Gaafar Nimeiry — his September 1983 imposition of sharia law triggered the Second Sudanese Civil War",
        "choices": [
            "Gaafar Nimeiry — his September 1983 imposition of sharia law triggered the Second Sudanese Civil War",
            "Omar al-Bashir — whose 1989 Islamist coup came years after the war had already restarted entirely",
            "Hassan al-Turabi — National Islamic Front leader but never himself the head of the Sudanese state",
            "Salva Kiir — the southern leader who became the first president of independent South Sudan post-2011",
        ],
        "context": "Sudan's two civil wars (First, 1955-72; Second, 1983-2005) pitted the Arab-Muslim north (Khartoum government) against the African-Christian-Animist south. The 1983 imposition of sharia law (Nimeiry) and the 1989 Islamist coup (Bashir) intensified the conflict; the National Islamic Front's Hassan al-Turabi argued for Islamic statehood. The 2005 Comprehensive Peace Agreement gave the south autonomy and a referendum option; the 2011 referendum (98.83% for secession) created South Sudan. Religious-ethnic boundaries that British colonial administration had largely respected, then Sudanese independence (1956) had forcibly integrated, reasserted themselves geographically. The Darfur conflict (2003-) added a further religious-ethnic dimension.",
    },

    918: {  # Lausanne 1923 population exchange
        "tier": 5,
        "question": "The 1923 Lausanne Convention compulsorily exchanged populations: ~1.2 million Greek Orthodox were transferred from Anatolia to Greece, ~400,000 Muslims from Greece to Turkey. The exchange was defined by religion, not language. Which two communities were SPECIFICALLY EXEMPTED from the Lausanne population exchange?",
        "answer": "Constantinople's Greek Orthodox and Western Thrace's Muslims — the only two communities exempted from the swap",
        "choices": [
            "Constantinople's Greek Orthodox and Western Thrace's Muslims — the only two communities exempted from the swap",
            "Smyrna's Armenians and Cyprus's Greeks — both exempted under separate British protectorate guarantees in 1922",
            "Salonika's Sephardic Jews and Crete's Muslims — exempted in side-agreements signed years before the Convention",
            "Karamanlides Christians and Pontic Greeks — both fully exempted on linguistic grounds despite being Orthodox",
        ],
        "context": "The Convention Concerning the Exchange of Greek and Turkish Populations (Lausanne, January 1923) followed the 1919-22 Greco-Turkish War. The treaty defined population categories by religion: Greek Orthodox in Anatolia (including Turkish-speaking Karamanlides) sent to Greece; Muslims in Greece (including Greek-speaking Cretan Muslims) sent to Turkey. Only Constantinople's Greek Orthodox and Western Thrace's Muslims were exempted. ~1.2 million Anatolian Greeks were displaced; ~400,000 Greek Muslims went the other way. The Lausanne precedent shaped 20th-century thinking about partitioned religious-ethnic populations (India 1947, Israel-Palestine 1948, Bosnia 1990s).",
    },

    921: {  # Thich Nhat Hanh / Plum Village
        "tier": 5,
        "question": "During the Vietnam War (1955-75), monk Thich Nhat Hanh founded Engaged Buddhism, applying Buddhist meditation to social action. Exiled in 1966, he lived in France until returning to Vietnam in 2018. In which region of France did Thich Nhat Hanh establish his Engaged-Buddhism monastic center in 1982?",
        "answer": "Southwestern France — Plum Village (Village des Pruniers) in the Dordogne became the center of Engaged Buddhism",
        "choices": [
            "Southwestern France — Plum Village (Village des Pruniers) in the Dordogne became the center of Engaged Buddhism",
            "Eastern Switzerland — a Zen monastery in the Alps that Thich Nhat Hanh founded for European retreatants",
            "Northern California — Spirit Rock and the Insight Meditation Society lineage that he established personally",
            "Central Vermont — Karmê Chöling and the Shambhala lineage that he founded with Chögyam Trungpa in 1970",
        ],
        "context": "Thich Nhat Hanh (1926-2022, Vietnamese Zen monk and peace activist) founded the Order of Interbeing (1966) and the broader Engaged Buddhism movement, applying mindfulness and Buddhist ethics to social conditions during the Vietnam War. Exiled in 1966 after meeting Martin Luther King (who nominated him for the 1967 Nobel Peace Prize), he established Plum Village in southwestern France (1982) as the center for Engaged Buddhism in the West. His ~100 books, especially The Miracle of Mindfulness (1975) and Being Peace (1987), shaped the contemporary Western mindfulness movement (Jon Kabat-Zinn's MBSR program built on his teachings). He returned to Vietnam in 2018.",
    },

    975: {  # Mansa Musa / 1324 Hajj
        "tier": 2,
        "question": "In 1324, Mali ruler Mansa Musa made Hajj to Mecca with 60,000 men and 100 camels of gold. The gold he gave away in Cairo crashed gold prices there for over a decade. Which two West African goldfields supplied much of Mali's gold?",
        "answer": "Bambuk and Bure — the two West African goldfields supplying much of the Old World's gold",
        "choices": [
            "Bambuk and Bure — the two West African goldfields supplying much of the Old World's gold",
            "Witwatersrand and Kimberley — South African mines unknown until European discovery centuries later",
            "Sutter's Mill and Comstock Lode — American Western strikes from the 1840s, long after Mali's era",
            "Klondike and Yukon — late 1800s Canadian gold rushes unrelated to West African medieval geography",
        ],
        "context": "Mansa Musa's 1324 Hajj is the canonical demonstration of Mali's wealth. The Bambuk and Bure goldfields supplied much of Old World gold. Mali under Musa was probably the wealthiest state on Earth — a substantive African civilizational achievement.",
    },
}


# ----------------------------------------------------------------------------
# Build & validate
# ----------------------------------------------------------------------------
def write_patch(subject: str, rewrites: dict[int, dict]) -> dict:
    bank = load_bank(subject)
    dup_idx, ans_idx = build_bank_indices(bank)
    patches: list[dict] = []
    results: dict[str, list] = {"PASS": [], "SOFT_WARN": [], "FAIL": []}
    skipped: list[tuple[int, str]] = []
    for bank_idx, new_q in rewrites.items():
        # Sanity: bank index must exist
        if bank_idx >= len(bank):
            skipped.append((bank_idx, f"bank_idx {bank_idx} out of range (bank size {len(bank)})"))
            continue
        old_q = bank[bank_idx]
        # Carry forward bank-housekeeping fields not in the rewrite (id, subject, etc.)
        merged = dict(old_q)
        merged.update(new_q)
        report = validate_rewrite(
            subject,
            merged,
            bank=bank,
            dup_index=dup_idx,
            answer_index=ans_idx,
            replace_idx=bank_idx,
        )
        verdict = report["verdict"]
        results[verdict].append((bank_idx, report))
        if verdict == "FAIL":
            skipped.append((bank_idx, "; ".join(f"{g}: {r}" for g, r in report["hard_fails"])))
            continue
        patches.append({"bank_idx": bank_idx, "new": merged})
    out_path = REPO / f"_weasel_fix_{subject}.json"
    out_path.write_text(json.dumps(patches, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "subject": subject,
        "input_count": len(rewrites),
        "output_count": len(patches),
        "PASS": len(results["PASS"]),
        "SOFT_WARN": len(results["SOFT_WARN"]),
        "FAIL": len(results["FAIL"]),
        "skipped": skipped,
        "results": results,
    }


if __name__ == "__main__":
    summary = []
    for subject, rewrites in [
        ("science", SCIENCE_REWRITES),
        ("animal", ANIMAL_REWRITES),
        ("cooking", COOKING_REWRITES),
        ("geography", GEOGRAPHY_REWRITES),
    ]:
        print(f"\n=== {subject} ===")
        rep = write_patch(subject, rewrites)
        print(f"  input:  {rep['input_count']}")
        print(f"  PASS:   {rep['PASS']}")
        print(f"  SOFT:   {rep['SOFT_WARN']}")
        print(f"  FAIL:   {rep['FAIL']}")
        if rep["skipped"]:
            print("  skipped:")
            for bi, reason in rep["skipped"]:
                print(f"    #{bi}: {reason}")
        # Detail soft warns
        for bi, r in rep["results"]["SOFT_WARN"]:
            print(f"  SOFT #{bi}: {'; '.join(f'{g}: {x}' for g, x in r['soft_warns'])}")
        # Detail hard fails for diagnostic
        for bi, r in rep["results"]["FAIL"]:
            print(f"  FAIL #{bi}: {'; '.join(f'{g}: {x}' for g, x in r['hard_fails'])}")
        summary.append(rep)

    print("\n=== TOTAL ===")
    print(f"  PASS:  {sum(s['PASS'] for s in summary)}")
    print(f"  SOFT:  {sum(s['SOFT_WARN'] for s in summary)}")
    print(f"  FAIL:  {sum(s['FAIL'] for s in summary)}")
