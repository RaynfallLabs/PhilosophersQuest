"""Build 70 T4 science P5 (History+ethics+contested) questions — bank rebuild.

Tier 4 = 8th grade. Multi-sentence setup + named figures + contested-topic
substance. Length cap 900 total (grace 945). Per SCIENCE_FRAMEWORK §1
Discovery Pattern + SCIENCE_TEMPLATES §1.T4.

Discipline (after first-pass gate failures):
  - NO em-dashes inside any choice — keeps choice_shape_parity uniform "plain"
  - Distractor parity ~1.30 max/min ratio
  - Answer length ~ longest distractor (well under 1.6x outlier threshold)
  - Em-dashes ARE fine in stem and context (they're not on the parity gate)

Self-validates each question with validate_rewrite("science", ...).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(r"C:\Users\brand\Documents\PhilosophersQuest")
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402


Q: list[dict] = []


# ===========================================================================
# COVID / LOCKDOWNS (12)
# ===========================================================================

Q.append({
    "tier": 4,
    "question": "In 2022 a meta-analysis by Hanke, Herby, and Jonung at Johns Hopkins reviewed lockdown studies and found COVID-era stringent lockdowns reduced mortality by roughly 0.2%, far below the catastrophic projections that justified them. What does the finding suggest about the policy?",
    "answer": "The mortality benefit was small and the collateral costs to economy, schooling, and mental health were not seriously weighed",
    "choices": [
        "The mortality benefit was small and the collateral costs to economy, schooling, and mental health were not seriously weighed",
        "The mortality benefit was overwhelming and concerns about collateral damage were always unfounded by any measure",
        "Lockdowns were never actually implemented anywhere on a scale that any study could possibly measure",
        "Lockdown effects can never be studied since no real comparison populations exist anywhere in the world",
    ],
    "context": "Steve Hanke, Lars Jonung, and Jonas Herby published their meta-analysis through Johns Hopkins. Reviewing dozens of empirical studies, they found stringent lockdown policies reduced COVID-19 mortality by only about 0.2% on average. The implication: the trade-off was not a wash but a clear net loss when measured against documented harms — bankruptcies, mental-health crisis, missed cancer screenings, learning loss. Whether you accept their exact estimate or not, the question of whether lockdown costs were honestly weighed against benefits was substantially suppressed during 2020-2021.",
})

Q.append({
    "tier": 4,
    "question": "Sweden during COVID-19 declined to impose general lockdowns or mass school closures, relying on voluntary distancing and protection of nursing homes. By 2023, Sweden's excess mortality across the pandemic period sat roughly at the European average — lower than many lockdown countries. What does that comparison illustrate?",
    "answer": "The lighter-touch approach produced outcomes comparable to or better than heavy lockdown without the educational and economic destruction",
    "choices": [
        "The lighter-touch approach produced outcomes comparable to or better than heavy lockdown without the educational and economic destruction",
        "Sweden was catastrophically worse than every other country and is now studied as a kind of permanent public-health warning",
        "Sweden's pandemic approach was identical to the heavy lockdown policies adopted across the rest of Europe and Asia",
        "Sweden's pandemic data has never been published anywhere and cannot be compared internationally with any other country",
    ],
    "context": "Sweden's chief epidemiologist Anders Tegnell argued lockdowns were unsustainable. Sweden kept schools open for under-16s throughout 2020, kept most workplaces and restaurants open, and focused on protecting elder-care residents (where early failures occurred and were openly acknowledged). By OECD excess-mortality measures across 2020-2022, Sweden was mid-pack in Europe and ahead of many heavy-lockdown countries. The example matters because it provides a real comparison case rather than a thought experiment about what would have happened without intervention.",
})

Q.append({
    "tier": 4,
    "question": "School closures during 2020-2021 are now widely recognized — even by establishment public-health institutions — as having caused severe learning loss and mental-health damage in children. What was the documented harm pattern?",
    "answer": "Major learning loss especially among low-income kids plus documented surges in adolescent depression and self-harm that have not recovered",
    "choices": [
        "Major learning loss especially among low-income kids plus documented surges in adolescent depression and self-harm that have not recovered",
        "Zero measurable harm appeared anywhere in any country that closed schools during the broader COVID-19 pandemic response years",
        "Children mostly showed improved test scores after extended remote learning and recovered emotionally within several weeks of resuming",
        "School closure data was never actually collected and remains entirely unknown to any public-health researchers working today",
    ],
    "context": "NAEP scores in the US, PIRLS reading scores internationally, and similar measures across Europe documented dramatic learning losses concentrated in the lowest-income students. The CDC's own data showed teen-girl suicide attempts rose sharply 2020-2021. Children faced near-zero personal risk from COVID-19 itself; the harm came from the policy response. School closure was a choice made by adults bearing little of the cost, imposed on children bearing almost all of it. The Great Barrington Declaration warned of exactly this in October 2020.",
})

Q.append({
    "tier": 4,
    "question": "Imperial College London's epidemiological modeling, led by Neil Ferguson, produced the March 2020 projection of 2.2 million US deaths absent lockdowns — a figure that drove early policy. Critics note Ferguson's modeling group has a 25-year track record. What does that record show?",
    "answer": "Repeated dramatic overestimates in foot-and-mouth, swine flu, and mad-cow modeling that did not match real outcomes",
    "choices": [
        "Repeated dramatic overestimates in foot-and-mouth, swine flu, and mad-cow modeling that did not match real outcomes",
        "A consistent record of accurate predictions across every modeled outbreak since the year 2000 in nearly every country",
        "Models that intentionally underestimated risks to reassure the public during scares about a coming disease event",
        "No prior modeling work whatsoever, since the COVID-19 pandemic was the group's first public-health modeling exercise",
    ],
    "context": "Ferguson's 2001 model for UK foot-and-mouth led to mass culling of healthy animals. His 2005 bird-flu projection (150 million deaths) was off by orders of magnitude. His 2009 swine-flu model overstated severity. His mad-cow projections similarly overshot. None of this proves any specific later model wrong, but a 25-year pattern of high-side errors is the relevant context for treating any one projection as decisive policy input — context establishment coverage of the March 2020 model largely omitted.",
})

Q.append({
    "tier": 4,
    "question": "The Cochrane Library — the gold standard for evidence-based medicine — published an updated review of physical interventions in January 2023 (Jefferson et al.). On mask mandates in community settings, the review's main conclusion was striking. What did it find?",
    "answer": "No clear evidence that mask mandates reduced respiratory-virus transmission in community settings under randomized trials",
    "choices": [
        "No clear evidence that mask mandates reduced respiratory-virus transmission in community settings under randomized trials",
        "Mask mandates dramatically reduced viral transmission across every randomized community trial Cochrane was able to consider",
        "Mask mandates were not part of the review at all, and Cochrane has no public position on the question",
        "The review concluded that masks must be worn by all adults outdoors at all times in every public setting",
    ],
    "context": "The Cochrane review on physical interventions covered randomized controlled trials. Tom Jefferson, the senior author, was clear in interviews that the pooled RCT evidence did not support a population-level effect from mask mandates. The New York Times solicited a clarifying statement from Cochrane's editor that softened the public framing — itself a small case study in how 'consensus' messages are constructed downstream of evidence. The review didn't say masks cannot work for individuals in clinical settings — it said the population-level mandate evidence wasn't there.",
})

Q.append({
    "tier": 4,
    "question": "Before 2020, immunology had a well-established understanding of post-infection immunity — that recovery from a viral illness typically conferred meaningful protection against reinfection. During COVID-19 this understanding was repeatedly downplayed by public-health officials. What was the recognition skill?",
    "answer": "Natural immunity from prior infection was well-established science before 2020, and treating it as fringe was a departure from immunology",
    "choices": [
        "Natural immunity from prior infection was well-established science before 2020, and treating it as fringe was a departure from immunology",
        "Natural immunity to viral illness was discovered for the very first time during the COVID-19 pandemic by Pfizer researchers in 2021",
        "Natural immunity to any viral illness was conclusively disproven during 2020 by federal health officials in major peer-reviewed studies",
        "Natural immunity was never claimed by any medical researcher anywhere prior to the COVID-19 pandemic and has no scientific basis",
    ],
    "context": "Standard immunology textbooks taught post-infection immunity for measles, mumps, chickenpox, and many other pathogens long before 2020. A 2021 Israeli study (Gazit et al.) and later confirmations showed prior COVID-19 infection conferred protection comparable to or exceeding vaccination. Yet CDC and many state policies treated unvaccinated previously-infected people as no different from never-infected. The recognition: when long-established science gets suddenly redescribed as fringe, ask whether the policy needed that redescription to hold together.",
})

Q.append({
    "tier": 4,
    "question": "Vaccine mandates during 2021-2022 — imposed by federal agencies, employers, universities, and the military — required individuals to accept a specific medical intervention as a condition of work, school, or travel. From a medical-ethics standpoint, what's the central objection?",
    "answer": "Informed consent and bodily autonomy are foundational principles codified in the Nuremberg Code, and coerced medical interventions violate them",
    "choices": [
        "Informed consent and bodily autonomy are foundational principles codified in the Nuremberg Code, and coerced medical interventions violate them",
        "Bodily autonomy in medical ethics applies only to elective surgeries and has no actual relevance to any vaccine policy questions whatsoever",
        "The Nuremberg Code applies only to formal medical research and was formally repealed by the World Health Organization back in 2002",
        "Vaccine mandates are universally required by every infectious-disease textbook ever published in any country regardless of policy debate",
    ],
    "context": "The Nuremberg Code (1947) was drafted after the Doctors' Trial of Nazi physicians and established that voluntary consent of the human subject is absolutely essential. The Declaration of Helsinki (1964) extended these principles. Coercive vaccine mandates — lose your job, lose access to school, lose travel — are coercion even if the substance itself is beneficial. Reasonable people can disagree about the underlying medical risk-benefit. The ethical objection to mandates is about the structure of coercion, not the science of the vaccines themselves.",
})

Q.append({
    "tier": 4,
    "question": "President Biden's September 2021 OSHA emergency temporary standard required private employers with 100+ employees to mandate vaccination or weekly testing. The Supreme Court blocked the rule in January 2022 in NFIB v. OSHA. What was the legal reasoning?",
    "answer": "OSHA regulates workplace hazards specific to work, and COVID-19 is a general health risk, not a uniquely workplace-derived danger",
    "choices": [
        "OSHA regulates workplace hazards specific to work, and COVID-19 is a general health risk, not a uniquely workplace-derived danger",
        "The Supreme Court ruled that vaccine mandates of any kind are always unconstitutional regardless of which federal agency tries to issue them",
        "The Supreme Court ruled that the federal OSHA agency does not exist as a legitimate part of the executive branch any longer",
        "The Supreme Court ruled the mandate was scientifically perfectly sound but issued the wrong fine amount under enforcement guidelines",
    ],
    "context": "NFIB v. OSHA (595 U.S. ___, 2022) held the mandate exceeded OSHA's authority. The Court reasoned that OSHA's mission is workplace-specific hazards (chemical exposure, machine guards) rather than general public-health concerns. The companion case Biden v. Missouri allowed a narrower CMS mandate for federally-funded healthcare workers to proceed. The ruling did not say vaccines were bad or good — it said federal-agency authority has limits and that a general public-health concern cannot be regulated under the label of workplace safety. Separation of powers, even during a crisis.",
})

Q.append({
    "tier": 4,
    "question": "VAERS — the Vaccine Adverse Event Reporting System — is the US passive-surveillance database for post-vaccination adverse events. A 2010 Harvard Pilgrim study estimated VAERS captures fewer than 1% of actual adverse events. What's the implication for reading VAERS numbers?",
    "answer": "The reported VAERS numbers are floor estimates rather than ceiling estimates, so actual adverse-event rates run higher than the database shows",
    "choices": [
        "The reported VAERS numbers are floor estimates rather than ceiling estimates, so actual adverse-event rates run higher than the database shows",
        "VAERS automatically captures every single adverse event with perfect accuracy, and the surveillance database is complete by deliberate federal design",
        "VAERS reports are routinely fabricated by activists, and the database should probably be deleted entirely to prevent ongoing public confusion",
        "VAERS captures only the most minor reactions to vaccines and is forbidden from ever recording any serious post-vaccination event of any kind",
    ],
    "context": "The 2010 Harvard Pilgrim Health Care study, funded by the Agency for Healthcare Research and Quality (AHRQ), found that fewer than 1% of vaccine adverse events were being reported through VAERS. The system is passive — it relies on patients, doctors, and pharmacists choosing to file a report. Under-reporting is structural. The recognition is not that VAERS reports prove causation (they don't, on their own) but that they're a signal floor, not a ceiling. Treating raw VAERS counts as fringe noise misreads the design of the system.",
})

Q.append({
    "tier": 4,
    "question": "In late 2024 and early 2025, the Cleveland Clinic published a series of large employee-cohort studies on COVID-19 booster effectiveness, led by Dr. Nabin Shrestha and colleagues. What pattern did the data show?",
    "answer": "Higher numbers of prior vaccine doses correlated with higher subsequent COVID-19 infection rates, an unexpected finding the agencies were slow to engage",
    "choices": [
        "Higher numbers of prior vaccine doses correlated with higher subsequent COVID-19 infection rates, an unexpected finding the agencies were slow to engage",
        "Higher numbers of prior vaccine doses correlated with perfect immunity in every single employee cohort the team studied across multiple seasons",
        "The Cleveland Clinic has never studied vaccine effectiveness in any employee cohort and the cited research is simply fabricated by online critics",
        "Cleveland Clinic data showed boosters had absolutely no measurable effect of any kind on infection rates within the employee population over time",
    ],
    "context": "Cleveland Clinic's employee cohort studies (Shrestha et al., published as preprints and in peer-reviewed journals) reported a positive association between prior dose count and subsequent infection. The finding is observational and may reflect behavior (more-vaccinated people testing more, exposure patterns), waning effectiveness, or other factors. The point isn't that the study proves any particular conclusion — it's that establishment health agencies were reluctant to engage with data that complicated the booster narrative, even from one of the country's most respected medical institutions.",
})

Q.append({
    "tier": 4,
    "question": "The 'asymptomatic spread' framing — that healthy-feeling people were major drivers of COVID-19 transmission — was central to early lockdown justifications. The actual evidence on asymptomatic transmission was always weaker than the messaging. What did the WHO's Maria Van Kerkhove say in June 2020?",
    "answer": "She said asymptomatic transmission appeared 'very rare,' a statement WHO walked back within 24 hours under apparent pressure",
    "choices": [
        "She said asymptomatic transmission appeared 'very rare,' a statement WHO walked back within 24 hours under apparent pressure",
        "She said asymptomatic transmission was confirmed by WHO as the dominant pathway for COVID-19 viral spread across every region of the world",
        "She publicly said the World Health Organization has never published any guidance or commentary about respiratory virus transmission patterns at all",
        "She publicly insisted that asymptomatic individuals are completely unable to ever test positive on any kind of PCR test or rapid antigen test",
    ],
    "context": "On June 8, 2020, WHO's Maria Van Kerkhove said in a press briefing that asymptomatic transmission 'appears to be rare.' Within 24 hours, WHO issued clarifying statements walking the comment back. The recognition skill is not that asymptomatic spread is zero (it isn't) — it's that the certainty of the public messaging exceeded what the underlying evidence supported, and that walking back inconvenient statements is itself a pattern worth noticing in pandemic-era public-health communication.",
})

Q.append({
    "tier": 4,
    "question": "During 2020-2021, US public-health agencies repeatedly cited 'cases' (positive PCR tests) as the primary pandemic metric — even when many positives were in asymptomatic or mildly symptomatic people. What was the critique of case-counting as the headline number?",
    "answer": "Test positivity scales with testing volume and sensitivity, so using raw cases as severity metric mixed real illness with incidental detection",
    "choices": [
        "Test positivity scales with testing volume and sensitivity, so using raw cases as severity metric mixed real illness with incidental detection",
        "Test positivity is a fixed natural constant of the underlying virus that never changes with testing patterns or sensitivity of the diagnostic tools",
        "Cases were widely understood to be the only meaningful pandemic metric, and absolutely no critique of case-counting was ever offered by any researcher",
        "Cases dramatically under-counted everything because diagnostic tests were entirely unavailable to the public across nearly all of the pandemic period",
    ],
    "context": "PCR tests amplify viral RNA fragments — at high cycle thresholds (Ct values), the test can detect dead virus or fragments from past infection rather than active infectious illness. Combined with mass testing of asymptomatic people, 'cases' became a number that scaled partly with testing infrastructure rather than purely with disease prevalence. Hospitalization and excess-mortality data — harder to manipulate by testing volume — were lower-priority in much public messaging despite being more directly connected to actual disease burden. Headline metric choice is a soft form of policy framing.",
})


# ===========================================================================
# LAB LEAK (8)
# ===========================================================================

Q.append({
    "tier": 4,
    "question": "The Proximal Origin of SARS-CoV-2 paper (Andersen et al., Nature Medicine, March 2020) declared a natural origin and dismissed lab leak. FOIA'd Slack messages later showed the authors had been privately uncertain. What did those messages reveal?",
    "answer": "The authors discussed lab-leak plausibility in real time even as they drafted the public dismissal, so public certainty didn't match private uncertainty",
    "choices": [
        "The authors discussed lab-leak plausibility in real time even as they drafted the public dismissal, so public certainty didn't match private uncertainty",
        "The authors were entirely unanimous on natural origin throughout the entire drafting process and recorded no internal doubts at any point in the discussion",
        "No Slack messages from the Proximal Origin authors have ever been actually released to anyone, and those alleged FOIA records do not exist",
        "The Slack messages plainly confirmed that lab leak was decisively ruled out by a single careful experimental result conducted at the lab itself",
    ],
    "context": "Kristian Andersen, Eddie Holmes, Robert Garry, and co-authors published 'Proximal Origin' in Nature Medicine on March 17, 2020. The paper was widely cited to call lab-leak claims 'misinformation.' House Oversight Committee FOIA releases (2023) showed Andersen and others discussing lab-leak plausibility on Slack the same week they were drafting the public dismissal. The February 1, 2020 internal teleconference with Anthony Fauci and Jeremy Farrar framed engineering as concerning enough to need a coordinated response. The public document didn't reflect the private deliberation.",
})

Q.append({
    "tier": 4,
    "question": "By 2023, two major US intelligence agencies had publicly assessed COVID-19's origin in ways that contradicted the 2020 natural-origin consensus message. Which agencies, and what did they conclude?",
    "answer": "The FBI with moderate confidence and the Department of Energy with low confidence both publicly leaned toward a lab-related incident at the WIV",
    "choices": [
        "The FBI with moderate confidence and the Department of Energy with low confidence both publicly leaned toward a lab-related incident at the WIV",
        "All US intelligence agencies unanimously confirmed wet-market natural origin with very high confidence by mid-2023 in their published assessments to Congress",
        "No US agency has ever publicly commented on COVID-19 origins, and the entire question still remains sealed under federal national security executive order",
        "The CIA along with the NSA both publicly confirmed extraterrestrial origin for the virus and ruled out terrestrial sources entirely in their joint statement",
    ],
    "context": "FBI Director Christopher Wray confirmed in February 2023 that the Bureau had assessed with 'moderate confidence' that COVID-19 likely originated from a lab incident. The Department of Energy reached a similar conclusion at 'low confidence.' Other agencies (CIA, ODNI) remained split or favored zoonotic origin. The intelligence community's split assessments by 2023 stood in stark contrast to the unified 'lab leak is conspiracy theory' framing of 2020-2021, when the hypothesis was being actively suppressed on social media as misinformation.",
})

Q.append({
    "tier": 4,
    "question": "The Wuhan Institute of Virology (WIV) had been conducting coronavirus research — including gain-of-function research on bat coronaviruses — with funding routed partly through EcoHealth Alliance and the US National Institutes of Health. What does that funding chain imply?",
    "answer": "US federal money was directly upstream of the research lab at the center of the origin debate, which created a material conflict for US officials",
    "choices": [
        "US federal money was directly upstream of the research lab at the center of the origin debate, which created a material conflict for US officials",
        "US federal funding stopped flowing to all foreign coronavirus research labs in the year 2014 by an act of Congress that closed the entire pathway permanently",
        "EcoHealth Alliance has zero documented connection to WIV in any year and never funded any research at all at that particular Chinese institute under any grant",
        "WIV research was entirely funded by private Canadian foundations and government agencies with no US involvement of any kind at any point in the history of the lab",
    ],
    "context": "Peter Daszak's EcoHealth Alliance subgranted NIH funding to the Wuhan Institute of Virology for coronavirus research, including chimeric-virus work. This was disclosed publicly through Congressional testimony and FOIA records. Anthony Fauci's NIAID was a primary funder. Daszak was also a member of the early WHO-China origin investigation team. Critics argued the structural conflict — US officials assessing the origin of a virus from a lab they funded — undermined the credibility of dismissals of the lab-leak hypothesis. EcoHealth Alliance was eventually debarred from federal funding in 2024.",
})

Q.append({
    "tier": 4,
    "question": "SARS-CoV-2's spike protein contains a 'furin cleavage site' — a short sequence unusual among the closest known relatives of the virus. What is the significance of that feature for the origin question?",
    "answer": "The site is biologically functional and unusual in this lineage, consistent with either rare natural recombination or engineering, and not assumed natural",
    "choices": [
        "The site is biologically functional and unusual in this lineage, consistent with either rare natural recombination or engineering, and not assumed natural",
        "The furin cleavage site is a totally common shared feature of every bat coronavirus ever sequenced anywhere on the planet by any research group in any decade",
        "The site is biologically inert and has no actual relevance whatsoever to transmissibility or to any origin debate among the world's leading virologists today",
        "The site was clearly added to the SARS-CoV-2 virus only after the broader pandemic began, and the feature is therefore a recent laboratory artifact alone",
    ],
    "context": "The furin cleavage site in the SARS-CoV-2 spike enables efficient cleavage by furin, which broadens cell-type tropism and is a known virulence factor. None of the closest known sarbecoviruses to SARS-CoV-2 carry this feature, making it unusual within the lineage. Gain-of-function research has historically inserted furin sites into related viruses to study pathogenesis. The site doesn't prove lab origin — natural recombination could in principle produce it — but it also doesn't rule out engineering, and treating it as routine was a soft framing that biased the discussion.",
})

Q.append({
    "tier": 4,
    "question": "Gain-of-function research — modifying viruses to study their potential transmissibility or pathogenicity — was subject to a US funding pause from 2014 to 2017 under President Obama, then resumed under the HHS P3CO framework. What does that history say?",
    "answer": "The risks of gain-of-function research were officially recognized enough to pause federal funding, so the real question is who reviews it and how transparently",
    "choices": [
        "The risks of gain-of-function research were officially recognized enough to pause federal funding, so the real question is who reviews it and how transparently",
        "Gain-of-function research has never actually been considered risky by any US government agency or any other scientific body, and there was never any kind of federal funding pause on the topic",
        "Gain-of-function research is currently banned worldwide by a binding international treaty that all nations including China and Russia have already signed and ratified",
        "Gain-of-function research is identical to ordinary standard microbiology lab work and has no special review requirements anywhere in the entire United States system",
    ],
    "context": "The October 2014 US pause followed accidental anthrax and smallpox exposures at federal labs plus growing concern about H5N1 transmissibility studies. The 2017 P3CO framework was supposed to add review for high-risk projects. Critics including Richard Ebright (Rutgers) and Marc Lipsitch (Harvard) argued P3CO review was opaque and unevenly applied — including for EcoHealth-funded WIV work. The structural concern is reviewer transparency, not whether the scientists working on these problems are well-intentioned.",
})

Q.append({
    "tier": 4,
    "question": "Senator Rand Paul's hearings in 2021 and 2022 publicly questioned Anthony Fauci about gain-of-function research at the Wuhan Institute of Virology. Fauci's responses turned on a specific definitional move. What was that move?",
    "answer": "Fauci denied funding gain-of-function under NIH's narrow technical category while the work matched the broader scientific meaning of the term",
    "choices": [
        "Fauci denied funding gain-of-function under NIH's narrow technical category while the work matched the broader scientific meaning of the term",
        "Fauci openly admitted on the very first day of the hearing that he had personally directed engineering of SARS-CoV-2 at the Wuhan Institute of Virology from his office at the NIAID",
        "Fauci flatly refused to testify in person before any Senate committee and was eventually held in formal contempt of Congress at the close of the entire 2021 hearing process",
        "Fauci's full testimony to the Senate committee was promptly sealed by a federal court order and has remained entirely unavailable to the American public ever since the date",
    ],
    "context": "The hearings hinged on a definitional gap. NIH's P3CO framework uses a narrow technical definition; scientists generally use a broader one covering any enhancement of transmissibility or pathogenicity. Fauci consistently said NIH had not funded 'gain-of-function research' under the narrow framework, while critics (Richard Ebright, Bryce Nickels) argued the WIV work plainly met the broader definition. The recognition: when a public official denies something under a narrow internal definition while the broader common meaning applies, the denial is technically true and substantively misleading.",
})

Q.append({
    "tier": 4,
    "question": "In May 2021 — over a year into the pandemic — Facebook quietly changed its content-moderation policy to stop removing posts that claimed COVID-19 was a 'man-made virus.' Why did the policy change?",
    "answer": "Lab leak no longer met any reasonable definition of misinformation once intelligence agencies and major journalists were openly investigating it",
    "choices": [
        "Lab leak no longer met any reasonable definition of misinformation once intelligence agencies and major journalists were openly investigating it",
        "Facebook quietly discovered that the original removal policy had simply been a typo in the rulebook and had never been intended to ban any of that content at all",
        "Facebook adopted the entire policy change purely because of various unrelated software bugs internal to the moderation system that just happened to hit in May 2021",
        "Facebook reversed the policy only because it had originally been imposed on the company by an early 2021 court order that was struck down on appeal shortly after",
    ],
    "context": "Facebook's January 2021 policy had explicitly listed 'COVID-19 is man-made or manufactured' among claims subject to removal. In May 2021, after Nicholas Wade's widely-read essay and growing journalist coverage (Donald McNeil Jr., Katherine Eban), Facebook reversed course. The shift acknowledged what was already true: the lab-leak hypothesis had never been a fringe conspiracy theory. It was being labeled one. When the labeling cost became too high — when respected journalists were taking the question seriously — the label was withdrawn. The label was a political artifact, not a scientific assessment.",
})

Q.append({
    "tier": 4,
    "question": "In May 2024, EcoHealth Alliance was formally debarred from receiving US federal funding. The Health and Human Services memorandum cited specific documented failures. What were the issues?",
    "answer": "Failure to provide grant-required risk-monitoring reports on bat coronavirus research and failure to report potential gain-of-function experiments at the WIV",
    "choices": [
        "Failure to provide grant-required risk-monitoring reports on bat coronavirus research and failure to report potential gain-of-function experiments at the WIV",
        "EcoHealth Alliance was debarred only for completely unrelated tax-filing issues with the Internal Revenue Service that came to light early in the calendar year 2024",
        "EcoHealth Alliance was debarred specifically because Peter Daszak had personally created the original SARS-CoV-2 virus alone using equipment in his Manhattan office",
        "EcoHealth Alliance was never debarred at any time, and the organization currently remains in good standing with all relevant federal funders across the United States",
    ],
    "context": "HHS issued the debarment memorandum in May 2024, citing failure to file required progress reports, failure to ensure WIV compliance with grant terms, and other documentary lapses. The debarment was procedural — it did not adjudicate origin-of-COVID directly — but it established that the institutional record-keeping problems critics had been pointing to since 2020 were real and serious enough for federal action. Daszak's role on the early WHO-China origin team becomes a different kind of question with the debarment on record.",
})


# ===========================================================================
# GBD / BHATTACHARYA (5)
# ===========================================================================

Q.append({
    "tier": 4,
    "question": "In October 2020 three epidemiologists drafted the Great Barrington Declaration calling for 'focused protection' of the vulnerable rather than population lockdown. They worked at top universities — Stanford, Harvard, Oxford. What were their names?",
    "answer": "Jay Bhattacharya of Stanford, Martin Kulldorff of Harvard, and Sunetra Gupta of Oxford, drafted at the American Institute for Economic Research",
    "choices": [
        "Jay Bhattacharya of Stanford, Martin Kulldorff of Harvard, and Sunetra Gupta of Oxford, drafted at the American Institute for Economic Research",
        "Three anonymous researchers from a small fringe Florida policy think-tank with no credentialed academic expertise in epidemiology or public health between them",
        "Three retired physicians with no recent academic appointments at any major university anywhere in the world during the years leading up to the COVID-19 pandemic",
        "Three economists with no public-health backgrounds at all and who had never published any work on epidemiology in any peer-reviewed scientific journal before",
    ],
    "context": "Bhattacharya is a Stanford health-policy professor with a medical degree and economics PhD; he ran the Stanford Center on Demography and Economics of Health and Aging. Kulldorff was a Harvard biostatistician known for SaTScan disease cluster analysis. Gupta is the Oxford theoretical-epidemiology chair. The three were among the most-cited epidemiology researchers in the world. The focused-protection approach the GBD proposed was conventional pre-2020 public-health thinking applied to COVID-19. Reframing them as outsiders was a rhetorical move, not a scientific one.",
})

Q.append({
    "tier": 4,
    "question": "Within four days of the Great Barrington Declaration's October 4, 2020 publication, NIH Director Francis Collins emailed Anthony Fauci with specific instructions about how to respond. What did Collins write?",
    "answer": "That a 'quick and devastating published takedown' of the GBD's 'premises' was needed and should appear in public soon",
    "choices": [
        "That a 'quick and devastating published takedown' of the GBD's 'premises' was needed and should appear in public soon",
        "That the GBD signatories should be invited to brief the White House Coronavirus Task Force on focused-protection strategy at the earliest possible opportunity that week",
        "That the GBD's focused-protection approach should be adopted as official US policy immediately at all federal agencies with relevant statutory authority over public health",
        "That no response of any kind was needed because the Great Barrington Declaration document would likely be ignored anyway by the broader medical and scientific communities",
    ],
    "context": "The October 8, 2020 Collins-to-Fauci email was released through House Judiciary Committee FOIA. Collins, then NIH director, characterized the GBD signatories as 'fringe epidemiologists' and called for the public takedown. Within days, op-eds appeared from establishment voices echoing Collins's framing. The leak transformed how the GBD episode is understood — it was no longer 'fringe scientists got argued down on the merits' but 'credentialed dissent got organizationally suppressed from the top of US public health.' Collins's later public reflections (October 2023) include partial acknowledgment that his response was wrong.",
})

Q.append({
    "tier": 4,
    "question": "Jay Bhattacharya — the lead Stanford signatory of the Great Barrington Declaration who was publicly attacked as 'fringe' in 2020 — was confirmed as Director of the National Institutes of Health in 2025. What does the trajectory illustrate?",
    "answer": "Dissent that gets labeled 'fringe' by the establishment can be vindicated within a few years, and the labelers don't usually update their own framing",
    "choices": [
        "Dissent that gets labeled 'fringe' by the establishment can be vindicated within a few years, and the labelers don't usually update their own framing",
        "Bhattacharya was never criticized publicly by anyone connected to the federal government in any role during the entire period of the COVID-19 pandemic from any party",
        "Bhattacharya was not confirmed as NIH director and the position remains unfilled with no nominee under consideration by the Senate as of early 2025 going forward",
        "Bhattacharya's eventual confirmation as NIH director proves that all of the public-health decisions made during 2020 and 2021 were obviously scientifically correct by hindsight",
    ],
    "context": "Bhattacharya was confirmed by the Senate as NIH director under the second Trump administration in 2025. The trajectory matters precisely because the institutional pattern repeats — Semmelweis institutionalized then vindicated, Wegener mocked then vindicated, Marshall ridiculed then Nobeled, Bhattacharya 'fringe-labeled' then NIH directorship. The institutional reflex to label dissent rarely involves later public retraction. The recognition skill for the kid is to slow down when 'fringe' is used as a discussion-ender.",
})

Q.append({
    "tier": 4,
    "question": "Stanford's medical-school environment in 2020-2021 became openly hostile to Jay Bhattacharya, with colleagues organizing against him and university communications attacking the GBD position. What does the case illustrate about academic freedom?",
    "answer": "Institutional norms of academic freedom can collapse rapidly when political pressure aligns against a faculty member's substantive view",
    "choices": [
        "Institutional norms of academic freedom can collapse rapidly when political pressure aligns against a faculty member's substantive view",
        "Stanford University fully protected Jay Bhattacharya from start to finish and never permitted any internal faculty opposition to his publicly expressed views on focused protection at any time",
        "Academic freedom in higher education applies only to non-medical disciplines and never extends to any public-health research at any university anywhere in the United States",
        "Bhattacharya was hired by Stanford only in 2024 after the pandemic was over and faced no opposition at all during the entire long active period of the pandemic from anyone",
    ],
    "context": "Stanford colleagues organized petitions, the Stanford Daily ran hostile pieces, and university communications distanced the school from Bhattacharya's views. Bhattacharya later detailed the harassment in podcast interviews and Congressional testimony. The point isn't that universities should ban criticism of faculty — they shouldn't — but that the 2020-2021 episode showed how thin the academic-freedom protections actually were when a credentialed researcher took a publicly unpopular substantive position. The Foundation for Individual Rights and Expression (FIRE) documented similar patterns across many institutions.",
})

Q.append({
    "tier": 4,
    "question": "The focused-protection approach the Great Barrington Declaration proposed in October 2020 was essentially what mainstream pandemic-response planning had recommended for decades — protect the vulnerable, let lower-risk groups develop natural immunity. Why was it treated as radical in 2020?",
    "answer": "Institutional commitment to lockdown was deep enough that the previously conventional view had to be redescribed as fringe to protect the new policy",
    "choices": [
        "Institutional commitment to lockdown was deep enough that the previously conventional view had to be redescribed as fringe to protect the new policy",
        "Focused protection was a novel idea invented from scratch by the GBD authors in 2020 and had never been proposed in any prior pandemic-response document",
        "Focused protection had been thoroughly scientifically discredited by every single pandemic-planning document ever produced before the calendar year 2019 began",
        "Focused protection was secretly identical to extreme mass population lockdown and was simply renamed by the GBD authors as a kind of branding exercise",
    ],
    "context": "WHO pandemic-planning documents from 2019 explicitly recommended against population-wide lockdowns and against general school closures. The Imperial College team itself had previously published similar guidance. The shift to 'lockdown is the only ethical response' in March 2020 was a policy choice, not a scientific necessity. Once the institutions had committed to it, the previously-mainstream alternative had to be re-described as dangerous to maintain coherence — a pattern critics including Donald McNeil Jr., Matt Taibbi, and Jay Bhattacharya have documented.",
})


# ===========================================================================
# 1986 NCVIA + VAERS (4)
# ===========================================================================

Q.append({
    "tier": 4,
    "question": "The National Childhood Vaccine Injury Act of 1986 (NCVIA) shielded vaccine manufacturers from most civil lawsuits over vaccine injuries, routing claims through a no-fault federal program (VICP). What was the practical effect on manufacturers' liability?",
    "answer": "Liability for childhood vaccine injuries was largely removed from civil tort law, where ordinary product-liability incentives apply to drug makers",
    "choices": [
        "Liability for childhood vaccine injuries was largely removed from civil tort law, where ordinary product-liability incentives apply to drug makers",
        "Vaccine manufacturers became uniquely exposed to tort liability beyond every other US industry overnight under the framework set by the 1986 law passed by Congress that fall",
        "Vaccine manufacturers were required by the 1986 NCVIA to fund unlimited individual victim compensation programs run privately by each manufacturer for any covered injury",
        "Vaccine manufacturers were entirely federally banned from selling any vaccines whatsoever after the 1986 law passed Congress and was signed into law later that same year",
    ],
    "context": "Pre-1986 product-liability suits had become large enough that some manufacturers were exiting the childhood vaccine market — a real public-health concern that justified the original NCVIA framework. The structural consequence: vaccine manufacturers' product-liability exposure differs from other drug makers. Critics including attorney Aaron Siri argue that ordinary tort liability is a quiet but powerful market discipline. Removing that incentive leaves quality assurance to regulatory review alone, which is a weaker check.",
})

Q.append({
    "tier": 4,
    "question": "The CDC childhood immunization schedule has expanded considerably since the 1986 National Childhood Vaccine Injury Act passed. What's the rough scale of expansion from 1986 to today?",
    "answer": "From roughly 11 doses by age 6 in 1986 to about 70+ doses by age 18 today, with limited cumulative pre-licensure safety study of the combined modern schedule",
    "choices": [
        "From roughly 11 doses by age 6 in 1986 to about 70+ doses by age 18 today, with limited cumulative pre-licensure safety study of the combined modern schedule",
        "The CDC childhood vaccine schedule has remained completely and entirely unchanged since the 1986 National Childhood Vaccine Injury Act was passed and continues at the original level",
        "The CDC childhood vaccine schedule has been substantially reduced by more than half since 1986 due to the documented eradication of various childhood diseases in the United States",
        "The CDC childhood vaccine schedule is set in a binding international treaty signed by every nation and is identical in every developed country worldwide regardless of local policy",
    ],
    "context": "The CDC schedule has added hepatitis B (at birth), Hib, pneumococcal, rotavirus, hepatitis A, varicella, HPV, meningococcal, and seasonal flu and COVID-19 since 1986. Each individual vaccine is tested separately in pre-licensure trials. The combined cumulative effect of the full modern schedule on infant and child development has not been studied with placebo-controlled trial design. This is a methodological observation, not a claim that vaccines cause specific harms. Asking the question gets called 'anti-vaccine' rather than answered.",
})

Q.append({
    "tier": 4,
    "question": "The Vaccine Injury Compensation Program (VICP), created by the 1986 NCVIA, has paid out billions of dollars to families of vaccine-injured children since its inception. What does the payment record tell us?",
    "answer": "Vaccine injuries do occur at rates significant enough to require a federal compensation fund, so they are not the one-in-a-million events public messaging suggests",
    "choices": [
        "Vaccine injuries do occur at rates significant enough to require a federal compensation fund, so they are not the one-in-a-million events public messaging suggests",
        "VICP has never paid any compensation at all to any family since its creation in 1986 due to strict scientific review that ruled out vaccine causation in every single one of the filed cases",
        "VICP payments serve as definitive proof that vaccines cause every chronic disease found in any modern American children today regardless of family medical history or context",
        "VICP was repealed by Congress in 2010 and no further compensation has been paid to any vaccine-injured family at all since that year regardless of the documented circumstances of any case",
    ],
    "context": "Cumulative VICP awards exceed $5 billion since 1988. The program's design favors claims that match a pre-approved injury table; off-table claims face higher evidentiary bars. The 'one-in-a-million' framing common in vaccine-promotion messaging does not match the federal program's actual settlement record. Payments are funded by a small per-dose excise tax on vaccines. Public health messaging that minimizes vaccine injuries as vanishingly rare is in tension with the federal compensation framework's own scale.",
})

Q.append({
    "tier": 4,
    "question": "Robert F. Kennedy Jr., now serving as Secretary of Health and Human Services, has been one of the most prominent public critics of the modern vaccine schedule. Establishment voices have labeled him 'anti-vaccine.' What is his actual position?",
    "answer": "He calls for stronger vaccine safety testing, restored manufacturer liability, and stronger informed-consent protection rather than for a ban on any vaccines",
    "choices": [
        "He calls for stronger vaccine safety testing, restored manufacturer liability, and stronger informed-consent protection rather than for a ban on any vaccines",
        "He has publicly and repeatedly called for an immediate worldwide ban on all forms of vaccines for all human populations of every age starting from his very first public speech",
        "He has no published views at all on the topic of vaccines and has never spoken about vaccines or vaccine policy at any public event or in any of his many books and articles",
        "He fully endorses the current CDC childhood vaccine schedule in its entirety without any reservation about any specific vaccine on the schedule and has done so in every recent interview",
    ],
    "context": "Kennedy's Children's Health Defense and his books document his view as substantive vaccine-safety reform, not abolition. He has supported individual vaccines (some smallpox vaccines, some yellow-fever vaccines) while criticizing others. The 'anti-vaxxer' label flattens a substantive position into a slur to avoid engaging with it — exactly the pattern the science.md stance document names as the failure mode. Whether you agree with Kennedy or not, the recognition skill is to read what someone actually says.",
})


# ===========================================================================
# EUGENICS HISTORY (10)
# ===========================================================================

Q.append({
    "tier": 4,
    "question": "In 1907 Indiana passed the world's first compulsory sterilization law, allowing state institutions to sterilize the 'feeble-minded,' 'imbeciles,' and 'criminals.' What does the date matter for understanding the eugenics movement?",
    "answer": "American eugenics was established by state law decades before Nazi Germany, making it a homegrown US movement that influenced rather than borrowed from Europe",
    "choices": [
        "American eugenics was established by state law decades before Nazi Germany, making it a homegrown US movement that influenced rather than borrowed from Europe",
        "American eugenics began in 1945 in California as a direct response to the end of the Second World War and the news of Nazi atrocities published in the major US newspapers that year",
        "American eugenics simply never existed as any kind of organized movement in any of the United States at any point during the twentieth century according to the historical record",
        "American eugenics was imported wholesale from Nazi Germany in the late 1930s by US researchers traveling abroad and had no significant American intellectual roots before that imported decade",
    ],
    "context": "Indiana's 1907 law (Indiana Code 16-37-1) explicitly authorized compulsory sterilization. By 1931, 31 US states had passed similar laws. California became the most aggressive practitioner, performing over 20,000 sterilizations by the 1960s. The chronology matters: the Nazi T4 program (1939-1945) drew from American precedent, not the other way around. American eugenicists like Madison Grant and Harry Laughlin were openly celebrated in Nazi Germany. Reckoning with the American origin of state-coerced eugenics is harder for the establishment than treating it as a uniquely-European pathology.",
})

Q.append({
    "tier": 4,
    "question": "Justice Oliver Wendell Holmes Jr. wrote the 8-1 majority opinion in Buck v. Bell (1927), upholding Virginia's compulsory sterilization law. What was his most-quoted phrase from the opinion?",
    "answer": "'Three generations of imbeciles are enough,' a sentence that has never been formally retracted by the United States Supreme Court",
    "choices": [
        "'Three generations of imbeciles are enough,' a sentence that has never been formally retracted by the United States Supreme Court",
        "'No state may interfere with bodily autonomy without due process of law,' a strong privacy ruling that became the cornerstone of later judicial reproductive doctrine",
        "'Sterilization is constitutionally prohibited in all of the American states,' a categorical bar on the practice nationwide in every jurisdiction starting in 1927",
        "'The whole matter is left entirely to Congress to decide for itself,' declining to rule on the constitutional question at all in any direction either way under the framework",
    ],
    "context": "Holmes's opinion in Buck v. Bell (274 U.S. 200) is widely regarded as one of the worst Supreme Court rulings ever issued. The phrase 'three generations of imbeciles are enough' is among the most-cited examples of judicial cruelty in American history. Carrie Buck was not actually 'feeble-minded' — later analysis revealed she had been raped and her child Vivian (Holmes's third 'imbecile generation') had normal intelligence. Buck v. Bell has been narrowed by later rulings but has never been formally overturned. The legal precedent technically remains good law.",
})

Q.append({
    "tier": 4,
    "question": "California's eugenic sterilization program — running from 1909 through the late 1970s — was the most aggressive in the United States, with over 20,000 documented procedures. Who did the program disproportionately target?",
    "answer": "Mexican-American women, the poor, those committed to mental institutions, and those labeled 'sexually delinquent,' falling heavily on women and minorities",
    "choices": [
        "Mexican-American women, the poor, those committed to mental institutions, and those labeled 'sexually delinquent,' falling heavily on women and minorities",
        "Wealthy white men who had been deemed mentally superior under the prevailing eugenic framework adopted by the California state board of medical advisors after the close of World War One",
        "Soldiers wounded in combat at home or overseas, who were sterilized as a matter of policy to prevent passing on what were thought to be inherited combat injuries from a war",
        "Foreign-born scientists who voluntarily immigrated to California for university research jobs in the 1920s and 1930s and were sterilized at the request of the federal immigration authorities",
    ],
    "context": "Historian Alexandra Minna Stern's *Eugenic Nation* (2005) documented the racial and class pattern in California's program. Mexican-American and African-American women were targeted at rates well above their population share. The program continued sterilizing women in state-run institutions through the 1970s — within living memory. California formally apologized in 2003 and approved a reparations program in 2021. The case is a reminder that 'eugenics' was not just a theoretical movement but a concrete state program against vulnerable women within most current adults' lifetimes.",
})

Q.append({
    "tier": 4,
    "question": "Margaret Sanger, founder of Planned Parenthood, was explicitly committed to eugenic principles in her published writings. What documented position did Sanger hold?",
    "answer": "She wrote of preventing the births of those she termed 'human weeds' and ran a 'Negro Project' aimed at reducing Black births specifically in the US South",
    "choices": [
        "She wrote of preventing the births of those she termed 'human weeds' and ran a 'Negro Project' aimed at reducing Black births specifically in the US South",
        "She publicly opposed every conceivable form of eugenics throughout her entire long career and never associated herself with the international eugenics movement in any of her speeches",
        "She advocated unrestricted population growth and opposed any form of contraception or family planning whatsoever in any of her published writings or speeches she ever delivered in public",
        "She published only on the demographics of Asian-American populations in the western United States and never wrote about any other ethnic or racial group of any kind in any of her writings",
    ],
    "context": "Sanger's *The Pivot of Civilization* (1922) and *Woman and the New Race* (1920) explicitly discussed eugenic motivations for birth control. The Negro Project she ran in the late 1930s aimed at reducing African-American births in the South, working through Black ministers and physicians to provide cover. Sanger spoke to a Ku Klux Klan women's auxiliary in 1926. Planned Parenthood removed her name from its highest honor in 2020. The case isn't about discrediting birth-control access — it's about honesty regarding the eugenic intellectual roots of the organized US birth-control movement.",
})

Q.append({
    "tier": 4,
    "question": "The Cold Spring Harbor Eugenics Record Office, run by Charles Davenport and Harry Laughlin from 1910 to 1939, was the intellectual headquarters of American eugenics. What major funders supported the institution?",
    "answer": "The Carnegie Institution and the Rockefeller Foundation, two of the largest mainstream philanthropic establishments of the early twentieth century in America",
    "choices": [
        "The Carnegie Institution and the Rockefeller Foundation, two of the largest mainstream philanthropic establishments of the early twentieth century in America",
        "Small fringe political organizations of the era with no documented connection to any of the mainstream American academic or philanthropic institutions throughout this period",
        "Direct federal appropriations from the US Congress only, and no private foundation or university funding ever supported the Cold Spring Harbor office during its existence",
        "Soviet government research grants funneled through European banks, with absolutely no American philanthropic or government funding ever supporting the institution at any point",
    ],
    "context": "Carnegie Institution funded the Eugenics Record Office from 1910; the Rockefeller Foundation funded German eugenic research institutes (Kaiser Wilhelm Institute for Anthropology, Human Heredity, and Eugenics) into the 1930s. American eugenics was not a fringe movement housed in disreputable institutions — it was a mainstream-funded, Ivy-League-connected enterprise. Harvard, Yale, Columbia all had eugenics-affiliated faculty. The recognition skill is that prestigious institutional sponsorship is not by itself evidence that a movement is good.",
})

Q.append({
    "tier": 4,
    "question": "Madison Grant's *The Passing of the Great Race* (1916) was a foundational eugenicist text dividing Europeans into racial hierarchies. What did Adolf Hitler later say about the book?",
    "answer": "He called the book 'my bible' in correspondence with Grant, a direct ideological transmission from American eugenics into Nazi race policy",
    "choices": [
        "He called the book 'my bible' in correspondence with Grant, a direct ideological transmission from American eugenics into Nazi race policy",
        "He publicly denounced the book on multiple occasions in the late 1930s and explicitly rejected the entire framework of American eugenic thought in his major recorded speeches",
        "He never actually read any of Madison Grant's books, and Grant's published work has no documented historical connection to Nazi ideology of any kind despite scholarly claims",
        "He worked privately with Madison Grant to translate the book into German against the wishes of Grant's American publisher during a series of secret private letters between the two men",
    ],
    "context": "Hitler's reported praise of *Passing of the Great Race* is documented in multiple sources including Hitler biographer Ian Kershaw. Madison Grant — a New York lawyer and conservationist who founded the Bronx Zoo — was central to American immigration-restriction politics in the 1920s and helped pass the 1924 Johnson-Reed Act, which dramatically restricted immigration from southern and eastern Europe. The intellectual chain from American eugenics through immigration restriction to Nazi race ideology is documented and unflattering — and is rarely included in standard American history curricula.",
})

Q.append({
    "tier": 4,
    "question": "The Nazi 'Aktion T4' program — running from 1939 to 1941 in its formal phase — murdered over 70,000 disabled people in Germany and occupied territories. What does the T4 program owe to American precedent?",
    "answer": "American compulsory-sterilization laws and writings of US eugenicists like Madison Grant and Harry Laughlin were cited as models by Nazi planners",
    "choices": [
        "American compulsory-sterilization laws and writings of US eugenicists like Madison Grant and Harry Laughlin were cited as models by Nazi planners",
        "The Aktion T4 program was conceived entirely independently by Nazi planners with absolutely no reference whatsoever to any American eugenic precedent or US sterilization laws of any era",
        "Aktion T4 was actually imported wholesale into Germany from Soviet sterilization programs of the early 1930s and had no documented American influence at any stage of the German planning",
        "Aktion T4 had no precedent anywhere in any country at any time in history and was a uniquely Nazi German creation with no documented antecedents in any foreign or domestic policy",
    ],
    "context": "Edwin Black's *War Against the Weak* (2003) documents the citation chain in detail. Harry Laughlin's 'Model Eugenical Sterilization Law' (1922) was used as a template for Nazi Germany's 1933 Law for the Prevention of Hereditarily Diseased Offspring. Nazi propaganda films explicitly referenced California's sterilization program. Laughlin received an honorary degree from the University of Heidelberg in 1936. The T4 program escalated from sterilization to murder. The Nuremberg Code (1947), written after the postwar Doctors' Trial, established voluntary consent as the foundation of medical ethics.",
})

Q.append({
    "tier": 4,
    "question": "The Tuskegee syphilis study ran from 1932 to 1972 under the US Public Health Service, deliberately withholding effective treatment from poor Black men with syphilis to observe disease progression. How did the study end?",
    "answer": "Associated Press reporter Jean Heller broke the story in 1972, and the study had been hidden in plain sight, published in medical journals for decades",
    "choices": [
        "Associated Press reporter Jean Heller broke the story in 1972, and the study had been hidden in plain sight, published in medical journals for decades",
        "The Tuskegee syphilis study ended in the year 1947 immediately after the Nuremberg Code was drafted by the postwar military tribunal judges in occupied West Germany following the doctors' trial",
        "The Tuskegee syphilis study was always public knowledge throughout its long history, and every one of the men involved in the study gave full informed consent in writing throughout",
        "The Tuskegee syphilis study was a controlled clinical trial of penicillin as a syphilis treatment, and the study formally ended when penicillin proved effective in clinical trials in 1947",
    ],
    "context": "The Tuskegee study tracked roughly 600 Black men in Macon County, Alabama — 399 with syphilis, 201 controls. Effective penicillin treatment became available in 1947 and was withheld. Study findings were published openly in medical journals throughout — peer reviewers, journal editors, and US public-health officials all saw the data. None raised the ethical issue effectively until Peter Buxtun, a USPHS employee, leaked to AP reporter Jean Heller in 1972. The study ended only when public scrutiny made continuation impossible. Peer review did not save the men in the study.",
})

Q.append({
    "tier": 4,
    "question": "The Nuremberg Code of 1947 — drafted after the postwar Doctors' Trial of Nazi physicians who had conducted lethal experiments on prisoners — established foundational principles for medical research ethics. What is the Nuremberg Code's first principle?",
    "answer": "The voluntary consent of the human subject is absolutely essential, establishing informed consent as the foundation of modern medical research ethics",
    "choices": [
        "The voluntary consent of the human subject is absolutely essential, establishing informed consent as the foundation of modern medical research ethics",
        "The needs of the state must always override individual consent for the greater good of the broader population, especially during any declared medical emergency at any level",
        "Medical research may proceed without subject consent if any government health agency formally certifies in writing that the proposed research is necessary for public welfare",
        "Subject consent is merely a routine courtesy that researchers may extend to participants in any clinical study but it is not actually legally required of any subject today",
    ],
    "context": "The Nuremberg Code's ten principles begin with the absolute primacy of voluntary informed consent. The Doctors' Trial (1946-47) at Nuremberg tried 23 Nazi physicians and officials; 16 were convicted, 7 executed. The Code emerged directly from that proceeding. The 1964 Declaration of Helsinki built on it. Modern medical-ethics frameworks all trace back to this 1947 foundation. The principle was deliberately written as absolute — without exception for emergencies, governmental authority, or claimed public benefit. Modern departures from that absoluteness require honest argument.",
})

Q.append({
    "tier": 4,
    "question": "American eugenic ideas continued to influence US policy for decades after Buck v. Bell. Beyond compulsory sterilization, what major area of US law was shaped by eugenic ideology in the 1920s?",
    "answer": "Immigration restriction, with the 1924 Johnson-Reed Act drawing on eugenic arguments about 'racial stock' to bar most immigration from southern and eastern Europe",
    "choices": [
        "Immigration restriction, with the 1924 Johnson-Reed Act drawing on eugenic arguments about 'racial stock' to bar most immigration from southern and eastern Europe",
        "Anti-trust law in general, with the 1890 Sherman Anti-Trust Act being framed almost entirely by various eugenic policy concerns of the era that were not widely known at the time of its passage",
        "Highway construction across America, with the 1956 Interstate Highway Act being justified almost entirely by various eugenic arguments about racial geography that were standard at the time",
        "Federal banking regulation across the country, with the 1933 Glass-Steagall Act drawing exclusively on various eugenic theories about racial and ethnic groups in the banking industry of the time",
    ],
    "context": "The 1924 Immigration Act (Johnson-Reed) used national-origin quotas calibrated to the 1890 census, dramatically restricting Italian, Polish, Russian, Greek, and Jewish immigration. Senate hearings cited Madison Grant's *Passing of the Great Race* and Harry Laughlin's expert testimony on 'racial degeneration.' The 1924 Act remained in force until 1965. The eugenic framing was openly used at the time — only later was it laundered into 'national security' or 'wage protection' framing for retrospective respectability. Naming the eugenic origin of this law is part of honest American history.",
})


# ===========================================================================
# REPLICATION CRISIS (8)
# ===========================================================================

Q.append({
    "tier": 4,
    "question": "John Ioannidis published 'Why Most Published Research Findings Are False' in PLOS Medicine in 2005, becoming one of the most-cited papers in modern science. What was Ioannidis's core argument?",
    "answer": "Most published findings have weak prior plausibility, modest effect sizes, low statistical power, and bias, making them more likely false on Bayesian grounds",
    "choices": [
        "Most published findings have weak prior plausibility, modest effect sizes, low statistical power, and bias, making them more likely false on Bayesian grounds",
        "All published scientific findings are by definition correct because the peer review system across every major journal in every relevant academic discipline catches every possible error",
        "Published findings in modern journals are sometimes a little inaccurate but only in marginal subfields like nutrition science or social psychology where standards are known to be lower than elsewhere",
        "Scientific publication as a general practice should be abandoned because none of the findings can ever be trusted by any reader at any time under any circumstances in the modern academic world",
    ],
    "context": "Ioannidis combined four ideas: (1) the base rate of true hypotheses in a field is often low, (2) statistical power is often low, (3) bias and questionable research practices nudge results toward 'positive,' (4) multiple analyses on the same data inflate false-positive rates. Combined, these produce literatures where the published positive findings are disproportionately wrong. The argument is mathematically straightforward. The 2015 Open Science Collaboration psychology replication project (~36% rate) made it empirically concrete.",
})

Q.append({
    "tier": 4,
    "question": "The Open Science Collaboration's 2015 'Estimating the Reproducibility of Psychological Science' replication project attempted to reproduce 100 prominent psychology findings. What was the result of that effort?",
    "answer": "Only about 36% of the original studies replicated at the original effect size, a major empirical confirmation of the replication crisis claim",
    "choices": [
        "Only about 36% of the original studies replicated at the original effect size, a major empirical confirmation of the replication crisis claim",
        "All 100 of the original studies replicated cleanly and the project confirmed the broad reliability of mainstream contemporary psychology research in journals",
        "The Open Science Collaboration project was quietly withdrawn before formal publication and no findings from this large-scale project were ever released publicly",
        "The original studies under review were too varied across different psychology subfields for any kind of meaningful replication assessment to be conducted at all",
    ],
    "context": "The OSC project, led by Brian Nosek and dozens of collaborating labs, published in Science in 2015. The 36% replication rate at original effect size — with average replication effects roughly half the original size — was a quantitative shock to the field. Subsequent replication projects in cancer biology, economics, and social science have shown similar or worse rates. The crisis is real, concentrated in specific subfields (social psychology especially), and structural — not the fault of a few bad actors but the predictable consequence of incentive structures around publication, novelty, and statistical significance.",
})

Q.append({
    "tier": 4,
    "question": "In June 2020, The Lancet and the New England Journal of Medicine retracted prominent COVID-19 studies on hydroxychloroquine within weeks of publication. What was the source of the problem?",
    "answer": "The studies relied on data from Surgisphere, a small company whose underlying records could not be verified by the journals or by independent reviewers",
    "choices": [
        "The studies relied on data from Surgisphere, a small company whose underlying records could not be verified by the journals or by independent reviewers",
        "The studies were always entirely scientifically correct but were retracted by both journals under intense political pressure from large pharmaceutical drug manufacturers that wanted them suppressed",
        "The retractions were entirely procedural and routine in nature, and the underlying data from the studies has since been fully validated by every subsequent independent replication attempt",
        "No retractions ever actually occurred at either journal and the original Surgisphere-based studies still remain freely available online in their original published peer-reviewed form to the present day",
    ],
    "context": "Mehra et al. published large 'observational studies' showing HCQ harm in The Lancet (May 2020) and NEJM (May 2020). The studies cited data from Surgisphere, a Chicago company purporting to have a global hospital network database. Investigative work by The Guardian, James Watson and 200 co-signatories, and others raised basic problems — Surgisphere had almost no employees, its data could not be audited, and its CEO's claimed credentials did not check out. The Lancet retracted on June 4, 2020; NEJM on June 13. Major peer-review failures during a public-health emergency.",
})

Q.append({
    "tier": 4,
    "question": "Diederik Stapel was a Dutch social-psychology professor whose 2011 fall from grace involved one of the largest fraud cases in modern science. What was the scale of Stapel's fraud?",
    "answer": "Over 50 retracted papers across his career, with fabricated data that had passed peer review and shaped sub-fields of social psychology",
    "choices": [
        "Over 50 retracted papers across his career, with fabricated data that had passed peer review and shaped sub-fields of social psychology",
        "A single retracted paper that was quickly caught by automated software within days of its first publication in a single journal in 2011 with little damage to the field",
        "No retractions whatsoever, and the entire set of allegations against Diederik Stapel was fully investigated by his university and the social psychologist was completely cleared by an academic committee",
        "Two retracted papers, both involving only minor coding errors in supplementary statistical material rather than any kind of data fabrication on the part of the professor at any time",
    ],
    "context": "Diederik Stapel was head of social-psychology research at Tilburg University. Whistleblowers in his group reported in 2011 that his data was fabricated. The Levelt Committee report found extensive fabrication across his career. Over 50 papers were eventually retracted. The case illustrates two things: peer review does not catch fabricated data when the experimental design is plausible and the results are publishable; and frauds at this scale shape literatures (other researchers cite, build on, and meta-analyze the fabricated work for years before retraction). Stapel was not a fringe outsider — he was an award-winning insider.",
})

Q.append({
    "tier": 4,
    "question": "'P-hacking' is a documented practice in academic research where investigators run many analyses on a dataset and report only those that reach statistical significance. What's the consequence for the literature?",
    "answer": "The published 'significant' findings are inflated false positives, since running many analyses guarantees some will hit p less than 0.05 by chance",
    "choices": [
        "The published 'significant' findings are inflated false positives, since running many analyses guarantees some will hit p less than 0.05 by chance",
        "P-hacking has been formally proven to be statistically impossible by leading academic statisticians and is therefore not actually occurring in any real research today",
        "P-hacking actually strengthens scientific findings overall by checking results from many different analytical angles for solid reliability before any final publication",
        "The practice of p-hacking is openly endorsed by every major statistical journal worldwide as the established gold-standard analytical approach to empirical research",
    ],
    "context": "Joseph Simmons, Leif Nelson, and Uri Simonsohn's 2011 paper 'False-Positive Psychology' showed how p-hacking and 'researcher degrees of freedom' inflate published false-positive rates. Pre-registration — declaring hypotheses and analyses before collecting data — partially addresses the problem. The replication crisis is in significant part a p-hacking crisis. The phrase 'we found significant effects' is much weaker evidence than naive readers assume because it doesn't account for the many analyses that were tried and not reported.",
})

Q.append({
    "tier": 4,
    "question": "Andrew Wakefield's 1998 Lancet paper proposing a link between the MMR vaccine and autism was retracted in 2010 after Brian Deer's investigation revealed extensive misconduct. But the broader question of autism causation has gotten worse in a specific way since then. What?",
    "answer": "Autism diagnosis rates have continued rising sharply with no agreed mechanistic explanation, and serious researchers asking the question are still labeled anti-vaccine",
    "choices": [
        "Autism diagnosis rates have continued rising sharply with no agreed mechanistic explanation, and serious researchers asking the question are still labeled anti-vaccine",
        "Diagnosed autism rates in American children have declined steadily since the Wakefield Lancet paper was officially retracted in early 2010 and remain low to today",
        "Childhood autism in the US has been clinically determined to be caused entirely by genetic factors with no environmental contribution, conclusion universally agreed in research",
        "Autism diagnosis rates in the United States have been completely stable for the past century across every region and every demographic group without any change at all",
    ],
    "context": "CDC data shows autism diagnosis rates rose from roughly 1 in 150 in 2000 to roughly 1 in 36 in 2020. Some portion of the rise is from expanded diagnostic criteria and broader screening, but the magnitude exceeds what diagnostic-broadening alone can explain. The pre-2020 research literature on possible environmental contributions — vaccine schedule, glyphosate, acetaminophen, prenatal exposures — was thin and underfunded. Wakefield's discredited paper is often used as a discussion-ender that prevents engagement with the actual rising-prevalence puzzle.",
})

Q.append({
    "tier": 4,
    "question": "Peer review is widely treated as the seal of scientific reliability. The actual track record of peer review in catching major frauds is much weaker than the framing suggests. What is the case for skepticism?",
    "answer": "Surgisphere, Stapel, Wakefield, Hendrik Schön, and Hwang Woo-suk all passed peer review at top journals before being caught by independent investigation",
    "choices": [
        "Surgisphere, Stapel, Wakefield, Hendrik Schön, and Hwang Woo-suk all passed peer review at top journals before being caught by independent investigation",
        "Peer review has perfectly caught every major scientific fraud in the modern era without exception in every relevant field across all subspecialties of every science",
        "Peer review is a fairly recent academic invention from the year 2010 or so and has essentially no historical track record from which any general conclusion could be drawn",
        "Peer review is universally rejected by every major journal worldwide, and academic journals now publish all submitted papers without any review by any outside scholar",
    ],
    "context": "Major retracted frauds in the 2000s-2020s — Hendrik Schön's physics fraud, Hwang Woo-suk's stem-cell fraud, Diederik Stapel's psychology fabrications, Surgisphere's COVID-era falsifications, Wakefield's MMR paper — all passed peer review at top journals. Reviewers checked the writing, the logic, and the statistics presented; they could not detect that the underlying data was fabricated. Peer review is a useful first filter but it is not a guarantee. Real reliability comes from replication, data sharing, and independent investigation.",
})

Q.append({
    "tier": 4,
    "question": "Publication bias — the tendency for journals to publish positive findings while leaving null results in researchers' file drawers — distorts scientific literatures in a predictable direction. What's the practical consequence?",
    "answer": "Published records over-represent 'effects exist' and under-represent 'we looked and found nothing,' biasing meta-analyses systematically upward",
    "choices": [
        "Published records over-represent 'effects exist' and under-represent 'we looked and found nothing,' biasing meta-analyses systematically upward",
        "Publication bias has been completely and permanently eliminated by recent mandatory pre-registration of every empirical study by every working scientist today",
        "Publication bias only affects studies in the social-science disciplines and has absolutely no measurable impact on any of the medical research literatures published",
        "Publication bias actually works in reverse from the usual claim, and null results in modern publishing are vastly over-published relative to any positive finding",
    ],
    "context": "Robert Rosenthal's 1979 'file drawer problem' formalized the issue. Researchers tend to write up and submit positive results; reviewers and editors prefer novel positive findings; null results sit in file drawers. The published record is thus a biased sample of all research conducted. Meta-analyses that pool only published studies systematically overstate effect sizes. Funnel-plot analysis and registered-report formats partially address this, but the underlying incentive structure remains. Trial registries help in medicine but enforcement is partial.",
})


# ===========================================================================
# CENSORSHIP / DISSENT (7)
# ===========================================================================

Q.append({
    "tier": 4,
    "question": "The Twitter Files — internal Twitter documents released by Elon Musk to a group of journalists starting in December 2022 — documented federal-agency coordination with the platform on content moderation. What did the documents show?",
    "answer": "Federal agencies including the FBI flagged specific scientific and political accounts for restriction in a coordinated state action shaping platform decisions",
    "choices": [
        "Federal agencies including the FBI flagged specific scientific and political accounts for restriction in a coordinated state action shaping platform decisions",
        "Twitter operated entirely on its own without any documented government contact whatsoever throughout the entire long 2020-2022 period of pandemic-era content moderation discussions",
        "The Twitter Files documents released to selected journalists were widely shown to be entirely fabricated, and no real journalist ever reviewed them after Musk's purported release event",
        "Twitter content moderation worked identically across every user account regardless of any external request from any government agency or any private actor at any time in the platform's history",
    ],
    "context": "The Twitter Files were released across multiple installments by Matt Taibbi, Bari Weiss, Michael Shellenberger, David Zweig, Lee Fang, and others in late 2022 and 2023. The documents showed extensive contact between Twitter's trust-and-safety team and federal agencies (FBI, DHS, CDC) regarding content flagged for moderation. Whether this constitutes 'jawboning' or unconstitutional state action depends on legal and factual specifics that later cases addressed. But the basic factual record — that government agencies coordinated with social-media platforms on content decisions — moved from 'conspiracy theory' to documented history with the file releases.",
})

Q.append({
    "tier": 4,
    "question": "Murthy v. Missouri reached the US Supreme Court in 2024. The case challenged federal-agency coordination with social-media platforms to suppress speech. How did the Court rule?",
    "answer": "It ruled the plaintiffs lacked standing, declining to reach the merits of whether the documented coordination was actually unconstitutional",
    "choices": [
        "It ruled the plaintiffs lacked standing, declining to reach the merits of whether the documented coordination was actually unconstitutional",
        "It ruled unanimously and broadly that any federal government coordination with private social-media platforms on content moderation is always perfectly fine",
        "It ruled that federal agencies must coordinate extensively with major social media platforms on content moderation as a matter of explicit federal statutory duty",
        "It ruled that the entire case had never been properly filed under federal procedural rules and refused to consider any aspect of the legal dispute at all",
    ],
    "context": "Murthy v. Missouri (originally Missouri v. Biden) reached SCOTUS in 2024 as a 6-3 standing ruling. Justice Barrett's majority opinion held the plaintiffs had not shown a sufficiently direct connection between specific government communications and specific platform actions against them. The dissent (Alito, Thomas, Gorsuch) argued the documented coordination was extensive enough to confer standing and likely violated the First Amendment. The ruling sidestepped rather than resolved the central question — and the documented coordination itself remains a matter of historical record.",
})

Q.append({
    "tier": 4,
    "question": "The pattern of suppressing scientific dissent has a long history. Galileo, Semmelweis, Marshall, and Bhattacharya all share a specific institutional pattern. What is it?",
    "answer": "Credentialed researchers offering correct or partially-correct dissenting views were institutionally punished by contemporaries before later being vindicated",
    "choices": [
        "Credentialed researchers offering correct or partially-correct dissenting views were institutionally punished by contemporaries before later being vindicated",
        "All four of these well-known scientific researchers were entirely uncredentialed amateurs working completely outside any major institution at the time of their initial publications in any field",
        "All four of the named researchers were eventually proven to be completely wrong by all of the later peer-reviewed research findings published in any major scientific journal across the world",
        "All four of the named scientific researchers worked in the same century in the same European country and pursued the same field of inquiry as one another during their working lives there",
    ],
    "context": "Galileo (heliocentrism) was placed under house arrest after the 1633 Inquisition trial. Semmelweis (hand-washing) was institutionalized after years of being mocked, and likely died from sepsis at the hands of asylum guards. Marshall (H. pylori causing ulcers) was ridiculed for over a decade before drinking the bacteria. Bhattacharya (focused protection on COVID) was labeled 'fringe' by NIH director Francis Collins and subjected to organized academic harassment. Each was substantially or wholly correct. The institutional pattern is not 'science self-corrects quickly' — it's 'science self-corrects, eventually, after the dissenter is broken.'",
})

Q.append({
    "tier": 4,
    "question": "Stanford's Virality Project — running 2020-2022 — was a public-private partnership flagging COVID-related social-media content for platforms to review. What kinds of content did it flag?",
    "answer": "Both false claims and 'true content that may fuel hesitancy,' meaning factually accurate information could be flagged if it raised questions about official policy",
    "choices": [
        "Both false claims and 'true content that may fuel hesitancy,' meaning factually accurate information could be flagged if it raised questions about official policy",
        "Only blatantly fabricated images and clearly fictional written claims with no factual basis were ever flagged by the Stanford Virality Project under its guidelines",
        "Only content originating from known foreign-intelligence accounts independently identified by United States national security services in open-source briefings",
        "Only commercial spam advertising and obvious financial scams unrelated to any health discussion or to any public-policy debate during the entire pandemic-era period",
    ],
    "context": "The Virality Project, based at the Stanford Internet Observatory, partnered with Twitter, Facebook, Google, and others on COVID content moderation. Released documents (via the Twitter Files and Congressional investigations) showed the project's flagging criteria explicitly included 'true content that could fuel hesitancy' — for instance, accurate reports of post-vaccination adverse events. The recognition skill: content moderation framed as fighting 'misinformation' was operating on a definition that included accurate information when it cut against the policy frame.",
})

Q.append({
    "tier": 4,
    "question": "Robert Malone, a credentialed virologist who held early mRNA platform patents, was banned from Twitter on December 29, 2021 for COVID-related posts. What does the Malone case illustrate?",
    "answer": "Credentialed expertise was not a protection against platform deplatforming when the views ran against official messaging during the COVID-19 pandemic period",
    "choices": [
        "Credentialed expertise was not a protection against platform deplatforming when the views ran against official messaging during the COVID-19 pandemic period",
        "Twitter only ever banned people with no formal medical or scientific credentials of any kind throughout the entire pandemic period in any of its content-moderation decisions across the platform",
        "Robert Malone has actually never had any documented connection at all to mRNA vaccine technology or to any of the related foundational delivery research areas in any country during his career",
        "Robert Malone's Twitter account was suspended only after he was officially and publicly determined by US intelligence services to be a known foreign intelligence asset working against US interests",
    ],
    "context": "Malone holds early patents on lipid-nanoparticle mRNA delivery technology from his work in the 1980s. His Twitter ban followed an appearance on Joe Rogan's podcast where he discussed adverse events and policy concerns. The factual claims he made were a mix of well-supported, contested, and probably-wrong — like most public-figure commentary during an unfolding crisis. The point isn't that Malone was right about everything (he wasn't) but that the response to his disagreement was deplatforming rather than engagement.",
})

Q.append({
    "tier": 4,
    "question": "Pierre Kory and Paul Marik — practicing critical-care physicians — formed the Front Line COVID-19 Critical Care Alliance (FLCCC) in 2020 to share clinical protocols, including ivermectin use. What was the institutional response?",
    "answer": "Both physicians faced credential challenges and were professionally marginalized despite years of relevant clinical experience and academic appointments",
    "choices": [
        "Both physicians faced credential challenges and were professionally marginalized despite years of relevant clinical experience and academic appointments",
        "Both physicians received the highest possible presidential civilian awards for their clinical work during the COVID-19 pandemic in a White House ceremony in 2021",
        "Both physicians had absolutely no medical credentials of any kind and were practicing medicine without any valid medical license in any US state during the pandemic",
        "Both physicians were uniformly praised throughout the pandemic by their professional associations and hospital systems for clinical protocols they developed and shared",
    ],
    "context": "Paul Marik had been a leading sepsis researcher at Eastern Virginia Medical School. Pierre Kory was a board-certified pulmonologist and former associate chief of critical care at the University of Wisconsin. The institutional response to their ivermectin advocacy included loss of hospital privileges, professional-board investigations, and public attacks. Whether ivermectin was efficacious against COVID-19 is contested in the literature — the meta-analyses split. The point about Kory and Marik is procedural: credentialed clinicians offering off-label protocols were institutionally punished rather than engaged with on the merits.",
})

Q.append({
    "tier": 4,
    "question": "The 'misinformation' label became a powerful tool for content moderation during 2020-2022. What's the basic structural problem with treating 'misinformation' as a discussion-ender rather than a starting point?",
    "answer": "The label gets applied by interested parties and tags factual claims as false based on policy alignment rather than careful evidentiary review",
    "choices": [
        "The label gets applied by interested parties and tags factual claims as false based on policy alignment rather than careful evidentiary review",
        "The misinformation label as deployed has a precise scientific definition that all reasonable researchers in the field absolutely fully agree upon without any remaining controversy",
        "The misinformation label as deployed has no structural problems whatsoever and accurately identifies every kind of false claim with perfect precision in every published case",
        "The misinformation label is purely descriptive in nature and carries no real-world consequences whatsoever for any user receiving the label on any social media post or platform",
    ],
    "context": "The lab-leak hypothesis was labeled misinformation in 2020-2021 and is now an active intelligence-community working hypothesis. The Hunter Biden laptop story was labeled misinformation in 2020 and is now confirmed authentic. Cochrane mask review skepticism was labeled misinformation and is consistent with the published Cochrane review. The pattern: 'misinformation' labels track political and institutional alignment, not the underlying evidentiary status of claims. Noticing this is part of intellectual hygiene.",
})


# ===========================================================================
# GENE THERAPY CELEBRATED + REGULATORY FAILURE (8)
# ===========================================================================

Q.append({
    "tier": 4,
    "question": "Casgevy (exagamglogene autotemcel) became the first CRISPR-based gene therapy approved by the FDA in December 2023. What disease does it treat, and how?",
    "answer": "Sickle cell disease, by using CRISPR-Cas9 to edit a patient's own bone-marrow stem cells to produce fetal hemoglobin, bypassing the sickle defect",
    "choices": [
        "Sickle cell disease, by using CRISPR-Cas9 to edit a patient's own bone-marrow stem cells to produce fetal hemoglobin, bypassing the sickle defect",
        "Common chronic headaches treated by topically applying a CRISPR enzyme directly to the patient's scalp once a week on demand at home in clinic-supervised therapy sessions over a period of months",
        "Type 2 diabetes treated by editing the gut microbiome of the affected patient through an oral CRISPR-loaded probiotic supplement taken once daily for the rest of the patient's life ongoing",
        "Common-cold infections treated by editing the patient's nasal mucosal cells with a CRISPR formulation before each annual winter cold season to protect them throughout the year ahead",
    ],
    "context": "Casgevy, developed by Vertex Pharmaceuticals and CRISPR Therapeutics, harvests autologous hematopoietic stem cells, edits the BCL11A gene with CRISPR-Cas9 to reactivate fetal hemoglobin production, and reinfuses the edited cells. In trials, the great majority of treated patients have remained free of vaso-occlusive crises for years. Sickle cell disease, affecting roughly 100,000 Americans (predominantly of African descent), is a debilitating and painful disease without good treatments before this. Casgevy is one of the most striking direct benefits of CRISPR technology in medicine to date.",
})

Q.append({
    "tier": 4,
    "question": "Zolgensma (onasemnogene abeparvovec) is a gene-therapy treatment for spinal muscular atrophy (SMA), approved by the FDA in 2019. What does it do, and why does early administration matter?",
    "answer": "It delivers a working SMN1 gene via an adeno-associated virus, and earlier infant administration prevents the irreversible motor-neuron loss SMA causes",
    "choices": [
        "It delivers a working SMN1 gene via an adeno-associated virus, and earlier infant administration prevents the irreversible motor-neuron loss SMA causes",
        "It removes excess protein from the patient's bloodstream and works equally well at any age of treatment without regard to the long-term progression of the underlying neurological condition under therapy",
        "It is a small daily oral pill taken by mouth twice each day and is administered to teenagers and young adults showing the very first SMA symptoms in early adulthood according to clinical guidelines",
        "It is a topical cream that is applied directly to the patient's skin on the upper arm once each week and treats the visible symptoms of SMA without addressing any of the underlying genetic disease",
    ],
    "context": "SMA type 1 — without treatment — typically kills affected children before age two from progressive motor-neuron death and respiratory failure. Zolgensma, developed by AveXis (now Novartis Gene Therapies), is a one-time infusion delivering an SMN1 gene through an AAV9 vector. Newborn screening has expanded; presymptomatic treatment yields dramatically better outcomes than symptomatic treatment, because motor neurons already lost cannot be regrown. The list price ($2.1 million) makes Zolgensma controversial as policy — but for treated infants, it has shifted SMA type 1 from a uniformly fatal disease to a survivable one.",
})

Q.append({
    "tier": 4,
    "question": "Luxturna (voretigene neparvovec) became the first FDA-approved gene therapy for a hereditary disease in December 2017. What condition does Luxturna treat?",
    "answer": "Leber's congenital amaurosis, a form of inherited childhood blindness from RPE65 mutations, treated by delivering a functional gene to retinal cells",
    "choices": [
        "Leber's congenital amaurosis, a form of inherited childhood blindness from RPE65 mutations, treated by delivering a functional gene to retinal cells",
        "Adult-onset cataracts, treated by injecting a small dose of viral preparation directly into the lens of the affected eye during a brief outpatient ophthalmologist office procedure on the day of treatment",
        "Common red-green color blindness in children and young adults, treated by applying simple topical eye drops to the surface of the eye each evening for a period of at least six full continuous months",
        "Untreated chronic glaucoma in older adults, treated by taking a single small oral pill by mouth twice each day for the rest of life and supplemented by periodic ophthalmologist visits annually",
    ],
    "context": "Luxturna, developed by Spark Therapeutics, uses an adeno-associated virus to deliver a working RPE65 gene to retinal pigment-epithelium cells. Patients with biallelic RPE65 mutations — a form of Leber's congenital amaurosis or retinitis pigmentosa — can recover meaningful visual function after the subretinal injection. The approval was historically significant: the first FDA-approved gene therapy targeting a specific hereditary disease in the United States. Visual recovery isn't complete and the long-term durability of the treatment is still being established. But for previously-untreatable congenital blindness, even partial recovery is a remarkable outcome.",
})

Q.append({
    "tier": 4,
    "question": "CAR-T cell therapy — engineering a patient's own T cells to recognize and kill their cancer — has produced durable remissions in blood cancers that previously meant death sentences. What's the basic mechanism?",
    "answer": "T cells are removed from the patient, engineered to express a chimeric antigen receptor targeting a tumor marker like CD19, expanded, then reinfused",
    "choices": [
        "T cells are removed from the patient, engineered to express a chimeric antigen receptor targeting a tumor marker like CD19, expanded, then reinfused",
        "Cancer patients simply swallow a small daily CAR-T pill by mouth that automatically distributes itself to any cancerous cells found throughout the body without intervention",
        "T cells are not actually involved in CAR-T therapy at all, since CAR-T is a radiation-based external-beam therapy that does not use any cellular engineering at any stage",
        "CAR-T therapy uses pooled T cells from a donor's blood bank sample and works completely without any genetic modification at all of any cells being used in the treatment",
    ],
    "context": "Kymriah (tisagenlecleucel, Novartis, 2017) and Yescarta (axicabtagene ciloleucel, Kite/Gilead, 2017) were the first FDA-approved CAR-T therapies. They target CD19, a marker expressed on B-cell malignancies including acute lymphoblastic leukemia (ALL) and certain lymphomas. Carl June at Penn led foundational clinical work, including the 2011 case of Emily Whitehead — a pediatric leukemia patient who became the first child treated with CAR-T and has remained in remission for over a decade. Cytokine release syndrome is a serious side effect. Targeted molecular oncology made real.",
})

Q.append({
    "tier": 4,
    "question": "The Right to Try Act of 2018 — signed by President Trump — provided a federal pathway for terminally ill patients to access experimental treatments outside FDA's expanded-access program. What was the underlying concern?",
    "answer": "FDA expanded-access delays were costing dying patients their last chance, and federal Right to Try gave a more direct route around that bottleneck",
    "choices": [
        "FDA expanded-access delays were costing dying patients their last chance, and federal Right to Try gave a more direct route around that bottleneck",
        "Right to Try expanded the formal regulatory authority of the FDA over experimental treatments and slowed the introduction of new experimental therapies at every stage",
        "Right to Try is actually only a state-level law in Texas and has no federal authorization at all under federal law, and the federal program simply does not exist",
        "Right to Try requires any terminally ill patient to live for an additional five years from the date of diagnosis before they may apply for experimental access to treatment",
    ],
    "context": "Right to Try state laws began passing in 2014; the federal law in 2018. The argument: for patients with terminal illness and limited options, the FDA's risk-benefit calculus is different — the risk floor is dying, so even uncertain treatments have a different calculation. Critics argued the FDA expanded-access program already worked for the cases this would help. The deeper point: regulatory caution that's reasonable for healthy populations becomes cruel for terminal patients. The trade-off between caution and patient autonomy is a real policy question.",
})

Q.append({
    "tier": 4,
    "question": "He Jiankui, a Chinese scientist, announced in November 2018 that he had used CRISPR to edit the genomes of human embryos that became living babies (the 'CRISPR babies'). What was the international scientific reaction?",
    "answer": "Near-universal condemnation, since the work lacked proper consent and medical justification and had safety risks that should have ruled out human trials",
    "choices": [
        "Near-universal condemnation, since the work lacked proper consent and medical justification and had safety risks that should have ruled out human trials",
        "Near-universal celebration as a major scientific breakthrough that opened a new and promising medical era of clinical applications for gene editing as a viable therapy",
        "Indifference, since the international scientific community made no public statements at all about the announcement at any time despite the wide reporting in journals",
        "Active formal sponsorship of follow-up clinical trials by various major Western research institutions across the US and the European Union in 2019 following the announcement",
    ],
    "context": "He Jiankui used CRISPR-Cas9 to edit the CCR5 gene in embryos, claiming HIV resistance. Twin girls were born in 2018; a third child in 2019. The proper consent and the medical justification were both inadequate; off-target effects of CRISPR editing in embryos are not well characterized; and germline editing affects all descendants without their consent. He was sentenced to three years in prison by Chinese authorities. The condemnation was about specific procedural and ethical failures, not a categorical rejection of all germline editing.",
})

Q.append({
    "tier": 4,
    "question": "FDA approval timelines for new drugs in the US run a median of about 12 years from initial discovery to market, driving high costs and limiting patient access. Critics including economist Alex Tabarrok argue the framework has a specific blind spot. What is it?",
    "answer": "Deaths from drugs delayed are invisible while deaths from drugs approved that prove harmful are visible, biasing regulatory weighting toward over-caution",
    "choices": [
        "Deaths from drugs delayed are invisible while deaths from drugs approved that prove harmful are visible, biasing regulatory weighting toward over-caution",
        "Current FDA approval timelines for new drugs are universally regarded as too short and approvals are happening too quickly with inadequate clinical safety review at every stage",
        "All FDA drug approvals are essentially random in their timing and outcome and have no systematic bias toward either eventual approval or eventual rejection of any product",
        "Current FDA approval timelines apply only to imported drugs from overseas, and drugs that have been developed entirely within the United States have no federal review process",
    ],
    "context": "The Tabarrok-Klein 'Type I vs Type II error' analysis: approving a harmful drug creates identifiable victims (you can name the patients), while delaying a beneficial drug creates statistical deaths (the people who'd have lived had it been available earlier are not named). FDA reviewers face career consequences for the first failure mode and not for the second — even though the second often involves far more lost life. The argument is not that all regulation is bad but that the asymmetric incentive structure systematically biases toward excessive caution against approvals.",
})

Q.append({
    "tier": 4,
    "question": "Beta thalassemia is an inherited blood disorder requiring regular transfusions for survival. The same Casgevy (CRISPR-based) treatment approved for sickle cell in 2023 was also approved for beta thalassemia in 2024. What does the approval pattern suggest?",
    "answer": "CRISPR therapy is becoming a platform technology where the same editing approach addresses different specific genetic diseases that share common pathways",
    "choices": [
        "CRISPR therapy is becoming a platform technology where the same editing approach addresses different specific genetic diseases that share common pathways",
        "CRISPR gene editing can only ever address one single specific inherited disease at a time and the FDA approval of Casgevy for beta thalassemia in 2024 was a regulatory mistake",
        "Casgevy was quietly withdrawn from any clinical use in sickle cell disease in early 2024 before being reapproved for use in beta thalassemia patients later that year",
        "Beta thalassemia has actually no known genetic basis of any kind and was not the legitimate target of any approval action for Casgevy from the FDA in 2024 or any year",
    ],
    "context": "The Casgevy approach edits BCL11A to reactivate fetal hemoglobin (HbF) production — and HbF compensates for both sickle hemoglobin (in sickle cell disease) and absent/reduced beta-globin (in beta thalassemia). One molecular intervention addresses two distinct hereditary diseases sharing a downstream physiological dependency. This is what 'platform technology' looks like in practice. The same engineering scaffolds could in principle be retargeted to other genetic diseases. Therapeutic gene editing has been promised for decades; Casgevy is the form it has actually taken.",
})


# ===========================================================================
# COMBINED / WRAP (8 questions to reach 70)
# ===========================================================================

Q.append({
    "tier": 4,
    "question": "Anthony Fauci's early-pandemic email correspondence, FOIA'd by BuzzFeed News and The Washington Post in 2021, revealed a specific gap between private and public statements on mask wearing. What did the emails show?",
    "answer": "He privately acknowledged that store-bought masks were not effective at blocking viral particles even as he publicly recommended them to the population",
    "choices": [
        "He privately acknowledged that store-bought masks were not effective at blocking viral particles even as he publicly recommended them to the population",
        "His private email statements and his public statements were perfectly aligned and remained completely identical to one another at every point during the entire pandemic",
        "He was never actually the subject of any FOIA request from any news organization at any point during the entire pandemic period and no emails have ever been released",
        "His private emails actually showed that he privately opposed all forms of public-health intervention of any kind from January 2020 onward regardless of public-health rationale",
    ],
    "context": "A February 5, 2020 email from Fauci to Sylvia Burwell read 'typical mask you buy in the drug store is not really effective in keeping out virus.' Yet by April 2020 the public messaging had shifted toward mass mask wearing. The emails were obtained by BuzzFeed News and The Washington Post in summer 2021. Fauci has argued the public messaging shifted because new evidence emerged about asymptomatic transmission. Critics argue the private acknowledgment of mask limitations should have been honestly communicated to the public from the start.",
})

Q.append({
    "tier": 4,
    "question": "Lysenkoism — Trofim Lysenko's anti-Mendelian genetics imposed by Stalin on Soviet biology from the 1930s through 1964 — is the canonical 20th-century example of politics destroying a scientific field. What was the cost?",
    "answer": "Soviet biology was set back by decades, leading geneticists were imprisoned or executed, and famines were worsened by failed agricultural prescriptions",
    "choices": [
        "Soviet biology was set back by decades, leading geneticists were imprisoned or executed, and famines were worsened by failed agricultural prescriptions",
        "Soviet biology was substantially strengthened by Lysenkoism and led every relevant field of agricultural and crop science by 1950 due to original Lysenkoist innovation",
        "Lysenkoism is a totally fabricated historical episode that did not actually occur in any meaningful form in any of the official records of the Soviet Union during its existence",
        "Lysenkoism only ever affected the field of Soviet metallurgy and the production of certain rare alloys, and had no effect on any biological or agricultural research at all",
    ],
    "context": "Lysenko rejected Mendelian genetics in favor of an inheritance-of-acquired-characteristics framework aligned with Soviet ideology. Stalin elevated him; Nikolai Vavilov, the world-leading geneticist who chaired the Soviet Academy of Agricultural Sciences, was arrested in 1940 and died in prison in 1943. Genetics research was officially banned 1948-1964. Crop failures from Lysenko-prescribed practices contributed to famines. The case is a documented warning that political pressure on a scientific field can persist for decades and cost millions of lives.",
})

Q.append({
    "tier": 4,
    "question": "The Sokal Hoax (1996) involved physicist Alan Sokal submitting a deliberately nonsensical postmodern-physics paper to the journal Social Text, which accepted and published it. What did the case illustrate?",
    "answer": "A prestigious humanities journal published gibberish dressed in the field's preferred vocabulary, so peer review can fail when reviewers value style over substance",
    "choices": [
        "A prestigious humanities journal published gibberish dressed in the field's preferred vocabulary, so peer review can fail when reviewers value style over substance",
        "Social Text successfully identified the planned Sokal hoax in advance of accepting the paper and refused to publish the submission after a careful review of its claims",
        "Alan Sokal's submitted paper was a genuine and important physics contribution and was correctly accepted by the journal under its standard editorial review of any submission",
        "The entire Sokal Hoax episode never actually occurred at any time in academic publishing and Alan Sokal is a purely fictional character invented for a 1990s campus satire",
    ],
    "context": "Sokal's 'Transgressing the Boundaries: Toward a Transformative Hermeneutics of Quantum Gravity' appeared in Social Text in spring 1996. He revealed the hoax in Lingua Franca the same day. The paper combined real-physics jargon with fashionable postmodern-theory phrasing in ways no editor with physics literacy would have published. The case became a touchstone in debates about academic standards in fields where claims are evaluated by stylistic fit rather than empirical rigor. The 2018 'Grievance Studies' affair (Lindsay, Boghossian, Pluckrose) revived the pattern.",
})

Q.append({
    "tier": 4,
    "question": "The 1996 IPCC Second Assessment Report's chapter on detection-attribution of climate change underwent a documented post-peer-review edit that strengthened its conclusions. What was the change?",
    "answer": "Chapter 8's qualifying caveats about the strength of the human-fingerprint evidence were removed after the peer review process had completed",
    "choices": [
        "Chapter 8's qualifying caveats about the strength of the human-fingerprint evidence were removed after the peer review process had completed",
        "The IPCC Second Assessment Report Chapter 8 conclusions were extensively strengthened with additional qualifying caveats added after the formal peer review process had completed",
        "The IPCC Second Assessment Report Chapter 8 was deleted in its entirety from the final published report just before publication due to overlapping concerns from within the working group",
        "The IPCC Second Assessment Report Chapter 8 received no edits of any kind between formal peer review and the final published version, and the text remained completely identical at every stage",
    ],
    "context": "Frederick Seitz (former NAS president) raised this concern in a 1996 Wall Street Journal piece titled 'A Major Deception on Global Warming.' Ben Santer, the chapter's lead author, defended the changes as standard editorial response to peer-review comments — though the timing and direction of the edits became contested. The episode is not the central evidence on climate change one way or another. It's a case study in how report-writing in policy-relevant science is itself a political process, with framing choices debated by participants even when the underlying physics is firm.",
})

Q.append({
    "tier": 4,
    "question": "Climategate (2009) involved the public release of emails from the Climatic Research Unit at the University of East Anglia. What did the emails reveal about scientific practice in the field?",
    "answer": "Discussion of how to handle inconvenient data, exclude critics from journals, and frame uncertainty in policy-friendly ways, internal candor not matching public certainty",
    "choices": [
        "Discussion of how to handle inconvenient data, exclude critics from journals, and frame uncertainty in policy-friendly ways, internal candor not matching public certainty",
        "Nothing whatsoever of substance was shown in any of the released emails, since all the emails were trivial scheduling correspondence between busy researchers",
        "Definitive confirmation that all climate scientists working in the field agreed on every detail of the underlying climate science and never had any technical disagreements",
        "Substantial documentary evidence that climate change is in fact a hoax fabricated by university researchers, a position no serious analysis or formal inquiry has supported",
    ],
    "context": "The November 2009 release of CRU emails included phrases like 'hide the decline' (referring to specific paleoclimate data handling), discussion of journals to exclude critics from, and FOIA-evasion remarks. Multiple subsequent inquiries (Muir Russell, Penn State, Independent Climate Change Email Review) found no scientific fraud but did identify issues with FOIA compliance, openness, and treatment of critics. The emails illustrate the gap between internal scientific candor and public certainty. They didn't disprove climate change. They did reveal the difference between 'we're confident' and 'public statements of confidence are tightly managed.'",
})

Q.append({
    "tier": 4,
    "question": "DDT was banned by EPA Administrator William Ruckelshaus in 1972, against the recommendations of EPA's own administrative law judge after extensive hearings. What was the documented cost of the ban?",
    "answer": "Millions of subsequent malaria deaths in Africa as countries lost access to effective vector control, a tradeoff rarely included in environmental retrospectives",
    "choices": [
        "Millions of subsequent malaria deaths in Africa as countries lost access to effective vector control, a tradeoff rarely included in environmental retrospectives",
        "DDT as a pesticide and as a public-health vector-control tool was beneficial in every single one of its uses and the documented 1972 ban produced no measurable consequences anywhere",
        "DDT continues to be very widely used across nearly all agricultural settings throughout the United States today as a standard pesticide despite the claim that DDT was banned in 1972",
        "DDT has never been used as a vector-control agent for the control of malaria transmission in any country in any region of the world at any time in the history of the pesticide industry",
    ],
    "context": "The 1972 hearing examiner Edmund Sweeney concluded DDT was 'not a carcinogenic, mutagenic, or teratogenic hazard to man' and recommended continued availability with restrictions. Ruckelshaus banned all US uses anyway. The ban influenced international policy through WHO and aid agencies, even though indoor residual spraying for malaria control was operationally distinct from US agricultural use. African public-health researchers like Donald Roberts have documented the resulting cost. Reckoning with the trade-off — and with the case that Rachel Carson's *Silent Spring* (1962) influence went beyond what the science supported — is part of honest environmental history.",
})

Q.append({
    "tier": 4,
    "question": "The mRNA platform behind the 2020 COVID-19 vaccines wasn't new technology; it had been in academic and industrial development for decades. Who is most associated with the foundational decades of mRNA research?",
    "answer": "Katalin Karikó and Drew Weissman, whose modified-nucleoside work in 2005 made therapeutic mRNA viable, and both shared the 2023 Nobel in Medicine",
    "choices": [
        "Katalin Karikó and Drew Weissman, whose modified-nucleoside work in 2005 made therapeutic mRNA viable, and both shared the 2023 Nobel in Medicine",
        "Anthony Fauci alone, who personally synthesized the very first messenger RNA molecule used in any of the COVID-19 vaccines in 1995 at his NIH laboratory bench",
        "Two anonymous researchers whose names and identities and academic affiliations have never been publicly disclosed by the NIH or any other federal agency or major university",
        "Robert Malone alone, who is now widely officially recognized in major mainstream scientific publications as the sole inventor of every part of the modern mRNA platform technology",
    ],
    "context": "Katalin Karikó's decades of mRNA research were poorly funded; she was demoted at Penn in the 1990s for failing to win grants. Her 2005 PNAS paper with Drew Weissman showed pseudouridine-modified mRNA could evade innate immune triggering — solving a fundamental problem. Their work made the COVID-19 vaccines possible. Robert Malone holds early lipid-nanoparticle mRNA-delivery patents from 1989-91 work and contributed importantly to the field. Both lines of credit are real and not mutually exclusive — though the public discourse has sometimes treated them as zero-sum.",
})

Q.append({
    "tier": 4,
    "question": "The Salem hypothesis — popularized in skeptic communities — claimed that creationism was disproportionately attractive to engineers. The underlying data on professional creationism beliefs across STEM fields tells a different story. What's the recognition skill?",
    "answer": "Bumper-sticker claims about who believes what in science often don't survive checking, since beliefs vary by discipline, sub-discipline, and survey wording",
    "choices": [
        "Bumper-sticker claims about who believes what in science often don't survive checking, since beliefs vary by discipline, sub-discipline, and survey wording",
        "All credentialed scientists working in every imaginable field hold absolutely identical views on every relevant religious question across all countries on Earth",
        "Survey research on the religious beliefs of working scientists is statistically completely impossible to conduct and has never been attempted by any survey research organization",
        "Engineers as a group were definitively proven to be the most thoroughly secular professional field of any kind by a single major Pew Research opinion survey back in 2010",
    ],
    "context": "The 'Salem hypothesis' is named for Bruce Salem, who proposed in 1980s-era online discussion that engineers seemed overrepresented in creationist circles. Actual Pew and other survey data show variation by specific discipline (biologists differ from chemists differ from engineers), by question wording (literal six-day creation vs guided-evolution vs theistic-evolution all get different responses), and by country. The broader recognition: glib claims about 'what scientists believe' usually reduce complicated empirical questions to a sound-bite that serves the speaker's argument better than it tracks reality.",
})


# ===========================================================================
# VALIDATE EVERY QUESTION
# ===========================================================================

def _post_strip(q: dict) -> dict:
    return {k: v for k, v in q.items() if not k.startswith("_")}


def main() -> int:
    import json as _json
    bank_path = REPO / "data" / "questions" / "science.json"
    bank = _json.loads(bank_path.read_text(encoding="utf-8"))
    dup_index, ans_index = build_bank_indices(bank)

    out: list[dict] = []
    passes = 0
    soft = 0
    fails: list[tuple[int, dict, dict]] = []
    for i, q in enumerate(Q):
        clean = _post_strip(q)
        # Check em-dash uniformity across choices (should all be plain — no em-dashes inside choices)
        dashes = [(" — " in c or " – " in c) for c in clean["choices"]]
        if any(dashes):
            print(f"  [{i}] WARN em-dashes present in some choices: {dashes}: {clean['question'][:80]}")
        # Distractor parity 1.30 ratio (task constraint, beyond gate)
        dists = [c for c in clean["choices"] if c != clean["answer"]]
        if len(dists) == 3:
            dlens = [len(d) for d in dists]
            mx, mn = max(dlens), max(min(dlens), 1)
            ratio = mx / mn
            if ratio > 1.30:
                print(f"  [{i}] WARN distractor parity ratio={ratio:.2f} (lens={dlens}): {clean['question'][:80]}")
        # Validate against pipeline
        res = validate_rewrite("science", clean, bank=bank, dup_index=dup_index, answer_index=ans_index, replace_idx=None)
        if res["verdict"] == "PASS":
            passes += 1
            out.append(clean)
        elif res["verdict"] == "SOFT_WARN":
            soft += 1
            out.append(clean)
            for g, r in res["soft_warns"]:
                print(f"  [{i}] SOFT {g}: {r[:140]}")
        else:
            fails.append((i, clean, res))
            for g, r in res["hard_fails"]:
                print(f"  [{i}] FAIL {g}: {r[:200]}")
            print(f"      Q: {clean['question'][:120]}")

    print()
    print(f"Total drafted: {len(Q)}")
    print(f"  PASS: {passes}")
    print(f"  SOFT_WARN: {soft}")
    print(f"  FAIL: {len(fails)}")
    print(f"  KEPT: {len(out)}")

    out_path = REPO / "_gen_science_t4_p5.json"
    payload = {
        "tier": 4,
        "summary": {
            "questions_generated": len(out),
            "by_pillar": {"5": len(out)},
        },
        "questions": out,
    }
    out_path.write_text(_json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote: {out_path}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
