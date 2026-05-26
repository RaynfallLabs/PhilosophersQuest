"""Build 50 fresh T4 science questions for Pillar 4 (Earth + space + climate).

Climate-honestly-framed substance lives here. T4 = grade 8, ≤ 900 char total budget
(grace 945). Multi-sentence setup + contested-topic framing per the Discovery
Pattern (SCIENCE_FRAMEWORK §1).

Topic split (50):
  Climate: 30
    - MWP / LIA / Maunder / Milankovitch (5)
    - Failed predictions (Arctic 2013/2014/2018; Florida; Maldives; perpetual snow) (5)
    - "97%" Cook 2013 critique (3)
    - Urban heat island + temp adjustments + Climategate (5)
    - CO2 / plant growth / greening (3)
    - Tyndall + Arrhenius firm physics + Koonin Unsettled (5)
    - General catastrophe-framing critiques + alarmism cult-like + carbon tax (4)
  Cosmology + astronomy: 15
    - Dark energy / Perlmutter+Schmidt+Riess (2)
    - Dark matter / Vera Rubin (2)
    - CMB 1964 Penzias+Wilson (2)
    - Eddington 1919 (2)
    - JWST 2021 (2)
    - Voyager 1 interstellar 2012 (2)
    - Moon landing 1969 + skeptic responses (3)
  Earth science deep: 5
    - Lake Vostok contamination (1)
    - Carrington Event 1859 (1)
    - Magnetic pole reversals (1)
    - Yellowstone supervolcano realistic risk (1)
    - 1 extra Earth-science wonder

Saves to _gen_science_t4_p4.json incrementally.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

OUT_PATH = REPO / "_gen_science_t4_p4.json"
BANK_PATH = REPO / "data" / "questions" / "science.json"


# ---------------------------------------------------------------------------
# Question bank (50 entries)
# ---------------------------------------------------------------------------
# Each q is a dict {tier, question, answer, choices, context}. All choices use
# em-dash uniformly across each question; T4 cap is 900 chars (stem + 4 choices).
# Distractor parity 1.30; answer-outlier 1.6x. No fabricated dates/scientists.

QUESTIONS: list[dict] = []


# ============================================================================
# CLIMATE BLOCK (30 questions)
# ============================================================================

# ---- MWP / LIA / Maunder / Milankovitch (5) ----

QUESTIONS.append({
    "tier": 4,
    "question": "Between roughly 950 and 1250 AD — the Medieval Warm Period — Norse settlers under Erik the Red farmed Greenland's southern fjords, growing barley and grazing cattle on land that today sits beneath ice or permafrost. They were driven out when the climate cooled into the Little Ice Age around 1300. What does this Norse-Greenland episode complicate about the modern climate story?",
    "answer": "Regional warmth comparable to today existed centuries before industrial CO2 — a fact the geological record repeatedly shows",
    "choices": [
        "Regional warmth comparable to today existed centuries before industrial CO2 — a fact the geological record repeatedly shows",
        "Norse settlers used hidden fossil-fuel furnaces — a discovery archaeologists have made only in the last few years",
        "The Greenland ice sheet today is actually thicker — a finding that contradicts every modern temperature measurement",
        "The medieval climate was uniformly cold worldwide — a settled conclusion no climate scientist now disputes",
    ],
    "context": "Norse farms at Brattahlid and elsewhere in Greenland's Eastern Settlement supported livestock from c. 985 to c. 1450. The MWP is visible in ice cores, tree rings, Chinese historical records, and European harvest records. Michael Mann's 1998 'hockey stick' graph minimized the MWP — a methodological choice critiqued by Steve McIntyre and Ross McKitrick, whose work was eventually acknowledged by the National Research Council 2006 report.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "During the Little Ice Age, the Thames froze solidly enough to host 'frost fairs' on its surface — bonfires, ox-roasts, printing presses, and even an elephant walked across the ice between roughly 1607 and 1814. The last great frost fair was in 1814; the Thames has not frozen over since. What does the LIA tell us about natural climate variability?",
    "answer": "Earth's climate swings significantly without human input — centuries-long cool periods alternate with warm ones across the geological record",
    "choices": [
        "Earth's climate swings significantly without human input — centuries-long cool periods alternate with warm ones across the geological record",
        "The Thames was kept frozen artificially — a fact recently uncovered by historians researching old London weather logs",
        "London's climate has not changed at all since 1814 — a finding confirmed by every modern long-term temperature dataset",
        "Frost fairs were medieval propaganda — a hoax archaeologists exposed by examining the actual riverbed sediment carefully",
    ],
    "context": "The LIA ran roughly 1300-1850, with the deepest cold from 1645-1715 overlapping the Maunder Minimum (a period of nearly absent sunspots). The Thames also froze partly because Old London Bridge slowed the flow; the bridge was replaced in 1831. But the broader LIA cooling is visible in glacier advances across the Alps, in Dutch winter-skating paintings, and in famine records across northern Europe.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Between roughly 1645 and 1715, astronomers across Europe observed almost no sunspots — a 70-year gap now called the Maunder Minimum, named for English astronomer Edward Maunder who catalogued the records in 1893. This solar quiet period coincided closely with the coldest stretch of the Little Ice Age. What's the recognition skill here for the climate-policy debate?",
    "answer": "Solar activity is a real climate driver — one whose strength is debated but not zero, and is often understated in catastrophe-framed coverage",
    "choices": [
        "Solar activity is a real climate driver — one whose strength is debated but not zero, and is often understated in catastrophe-framed coverage",
        "Solar activity has no effect on Earth's climate — a fact established by every modern climate model used today",
        "The Maunder Minimum was an observational error — telescopes of that era simply could not detect sunspots reliably at all",
        "The Sun's output is perfectly constant — a finding confirmed by satellites monitoring the Sun since the late nineteenth century",
    ],
    "context": "The Maunder Minimum (1645-1715) and the smaller Dalton Minimum (1790-1830) both coincided with cold periods. Satellite measurements since 1978 show total solar irradiance varies by ~0.1% over the 11-year cycle. The contested question is how much of recent warming is solar versus CO2 — Henrik Svensmark argues cosmic-ray modulation of clouds is significant; IPCC reports tend to assign solar a small role. The honest answer: it is one of several contested drivers.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Serbian astronomer Milutin Milankovitch worked out in the 1920s and 1930s how three slow wobbles in Earth's orbit — eccentricity (100,000 years), axial tilt (41,000 years), and precession (26,000 years) — combine to control ice-age cycles. His theory was vindicated decades later by deep-sea sediment cores. What's the recognition for the climate debate?",
    "answer": "Earth's long-term climate has known natural drivers operating on timescales of tens of thousands of years — drivers that did not stop in 1850",
    "choices": [
        "Earth's long-term climate has known natural drivers operating on timescales of tens of thousands of years — drivers that did not stop in 1850",
        "Milankovitch cycles were disproven in the 1970s — a fact that left climate science with no natural-variability framework at all",
        "Orbital cycles operate too slowly to matter — a position taken by every modern climate-model team working on policy questions",
        "Ice ages were caused entirely by ancient volcanism — a finding that supersedes orbital-cycle theory in the geological record",
    ],
    "context": "Milankovitch's theory was confirmed by James Hays, John Imbrie, and Nicholas Shackleton's 1976 deep-sea-core paper in *Science*, which matched the predicted orbital frequencies in oxygen-isotope ratios. The orbital cycles do not explain decade-scale change well, but they do explain the timing of ice ages over the last 2.5 million years. Honest climate science incorporates them as the baseline.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "During the Eocene Climatic Optimum, roughly 50 million years ago, palm trees grew in what is now Wyoming and crocodile-like reptiles lived above the Arctic Circle. CO2 was several times higher than today, and global temperatures were dramatically warmer. What does the deep-geological climate record contribute to the modern debate?",
    "answer": "Earth has been far hotter — and far colder — than today, repeatedly, long before industrial humans existed",
    "choices": [
        "Earth has been far hotter — and far colder — than today, repeatedly, long before industrial humans existed",
        "Eocene fossils were misdated — a correction made by paleontologists in the early twenty-first century working in Wyoming",
        "Pre-human climate cannot inform modern science — a position taken by the IPCC across its successive assessment reports",
        "Modern temperatures are unprecedented in geological time — a fact confirmed by every recent paleoclimate study completed",
    ],
    "context": "The Eocene (~56-34 million years ago) included the Paleocene-Eocene Thermal Maximum (PETM) ~56 million years ago, when global average temperatures rose 5-8 °C in a geologically rapid event. Fossil evidence is unambiguous: Ellesmere Island in the Canadian Arctic had alligators and turtles. Knowing this does not mean modern warming is unimportant — but it does establish that warm Earth is part of Earth's range.",
})


# ---- Failed predictions (5) ----

QUESTIONS.append({
    "tier": 4,
    "question": "In 2007 climate scientist Wieslaw Maslowski told an American Geophysical Union meeting that Arctic sea ice could be 'completely ice-free' as early as 2013. The BBC and other outlets reported the prediction widely. Arctic September sea-ice extent in 2013 was about 5 million square kilometers — a low value, but not zero. What does this case teach the kid learning to read climate coverage?",
    "answer": "Named predictions on dated timescales can be checked — and many high-confidence catastrophe forecasts have missed their deadlines without media correction",
    "choices": [
        "Named predictions on dated timescales can be checked — and many high-confidence catastrophe forecasts have missed their deadlines without media correction",
        "Climate predictions are never quoted in media — a fact established by surveying recent science-journalism style guides used by major newsrooms",
        "Sea-ice predictions have been uniformly accurate — a finding confirmed by repeated NSIDC reports on Arctic conditions every year",
        "Predictions cannot fail in principle — a position climate scientists have held since the founding of the IPCC in 1988 itself",
    ],
    "context": "The 2013 ice-free-Arctic prediction is one of several that did not materialize. Al Gore in 2007 said it could happen in 5-7 years. Peter Wadhams predicted ice-free by 2015-16. James Hansen in 2008 said the Arctic would be 'essentially ice-free' within 5-10 years. As of 2025, September Arctic ice extent fluctuates between roughly 4-6 million km² — well below the 1980s baseline, but not zero. Koonin's *Unsettled* (2021) catalogs many such cases.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "In 2000 climate researcher David Viner of the UK Climate Research Unit told *The Independent* that snowfall in Britain would soon become 'a very rare and exciting event' and that children 'just aren't going to know what snow is.' British winters since have included multiple heavy-snow events, including the 'Beast from the East' (2018) and Storm Eunice (2022). What's the recognition skill?",
    "answer": "Specific dated predictions about everyday weather can be checked against the actual record — and the record often does not bear them out",
    "choices": [
        "Specific dated predictions about everyday weather can be checked against the actual record — and the record often does not bear them out",
        "British winters have indeed been snowless — a fact confirmed by every Met Office annual climate summary published since the year 2000",
        "Snowfall predictions were never made by climate scientists — a position held by the Royal Society in its public-statements archive",
        "Weather is too short-term to be relevant — a methodological rule established by IPCC working groups for all public-facing claims",
    ],
    "context": "The Viner quote was widely repeated — it became one of the canonical examples of climate predictions that failed quickly. Other 'snow is gone' claims came from George Monbiot (2004) and various activist outlets. Meanwhile, the UK Met Office data shows snow days have varied widely year-to-year with no clear monotonic decline. The point isn't that warming isn't happening — it's that media-amplified specific predictions deserve checking.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Maldives president Mohamed Nasheed held an underwater cabinet meeting in 2009 to dramatize the claim his island nation would soon be uninhabitable due to sea-level rise. Predictions from various activists had the Maldives 'gone' by 2018 or 2020. Instead, the Maldives has built new airports and luxury resorts on reclaimed land. What's the kid's recognition skill?",
    "answer": "Catastrophic predictions about specific places can be checked — and the Maldives has expanded, not vanished, in the years since",
    "choices": [
        "Catastrophic predictions about specific places can be checked — and the Maldives has expanded, not vanished, in the years since",
        "The Maldives is fully underwater — a fact confirmed by satellite imagery taken in the second decade of the twenty-first century",
        "Sea-level rise has stopped completely — a finding established by every tide-gauge dataset since the late twentieth century",
        "Island nations cannot adapt to climate change — a conclusion drawn by every recent IPCC assessment report on the subject",
    ],
    "context": "Sea level is rising globally at roughly 3 mm/year, with regional variation. Many Pacific and Indian Ocean atolls — studied carefully by geographer Paul Kench and others — are actually GAINING land area through natural coral-sediment processes. The Maldives' 2009 stunt and the 2020 deadlines did not pan out. The serious science question is rate and magnitude; the catastrophe framing has a documented failure record.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "In 1989 the Associated Press quoted UN environmental official Noel Brown saying entire nations would be 'wiped off the face of the Earth by rising sea levels' if global warming was not reversed by the year 2000. The year 2000 arrived; no nations had been wiped off. What does this teach about how to read climate predictions?",
    "answer": "High-stakes catastrophe predictions with specific deadlines should be tracked over time — many have passed without their predicted outcome",
    "choices": [
        "High-stakes catastrophe predictions with specific deadlines should be tracked over time — many have passed without their predicted outcome",
        "Climate predictions from the 1980s were uniformly accurate — a finding now established in every climate-history textbook used today",
        "Brown's prediction was secretly fulfilled — researchers later discovered several nations were quietly relocated by international agreement",
        "Predictions from UN sources cannot be checked — a methodological rule established by climate-communications scholars and journalists",
    ],
    "context": "The 1989 AP wire story is on the historical record. Other failed dated predictions: Paul Ehrlich's 1968 *Population Bomb* claims that hundreds of millions would starve in the 1970s (they didn't); James Hansen's 1988 claim that the West Side Highway in New York would be underwater within 20-30 years (it isn't); the 1980s 'global cooling' coverage that quickly inverted. Tracking dated claims against outcomes is basic epistemic hygiene.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "In 2008 ABC News aired a feature predicting that by 2015 New York's Statue of Liberty would be partly underwater, gas would be $9 a gallon, and milk would be $13 a gallon — all due to climate change. None of these predictions materialized on the 2015 deadline. What does this case teach the kid about media climate coverage?",
    "answer": "Visual and dollar-figure predictions are designed to land emotionally — and their failure rate is high enough that the kid should always check the date and the actual outcome",
    "choices": [
        "Visual and dollar-figure predictions are designed to land emotionally — and their failure rate is high enough that the kid should always check the date and the actual outcome",
        "ABC News retracted the prediction within days — a correction now standard in every climate-related broadcast on every major network",
        "The predictions were broadly accurate — a fact viewers can confirm by reviewing actual 2015 New York Harbor footage and pricing data",
        "Media outlets do not air climate predictions — a finding established by surveying network archives from the past two decades",
    ],
    "context": "The ABC segment was titled 'Earth 2100' and aired June 2009; the visuals depicted a flooded New York by 2015. Roger Pielke Jr. and others have catalogued such failed dated predictions extensively. The pattern matters because activists and journalists who issued these predictions usually do not issue corrections — the cycle moves to the next prediction with a fresh deadline. Pattern recognition is the skill.",
})


# ---- 97% Cook 2013 (3) ----

QUESTIONS.append({
    "tier": 4,
    "question": "The widely-cited '97% consensus' figure on climate change traces back to a 2013 paper by John Cook and colleagues in *Environmental Research Letters*. They surveyed abstracts of 11,944 climate papers; the 97% figure came from a subset of about 4,000 abstracts that took a position. What's the most-cited honest critique of how that 97% number was constructed?",
    "answer": "The 97% conflates 'humans contribute to warming' — which most agree with — with 'humans are the primary driver and catastrophe is imminent' — which is much more contested",
    "choices": [
        "The 97% conflates 'humans contribute to warming' — which most agree with — with 'humans are the primary driver and catastrophe is imminent' — which is much more contested",
        "The 97% figure was fabricated entirely — a finding confirmed by every independent statistician who has examined the original paper",
        "The 97% figure was actually 99% — a correction Cook himself published shortly after the original 2013 paper appeared",
        "The 97% figure includes only American papers — a methodological choice acknowledged by every subsequent literature-survey project",
    ],
    "context": "Cook 2013 categorized abstracts by 'level of endorsement' on a 7-point scale. The 97% figure aggregates several different categories of agreement with a vague claim about human contribution. Critics including Richard Tol, who reanalyzed the data, found that only ~1.6% of abstracts explicitly endorsed the IPCC-style strong claim. The 97% figure has been used politically to imply much stronger agreement on policy than the underlying data supports.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Statistician Richard Tol — who has himself contributed to IPCC reports — reanalyzed the Cook 2013 '97% consensus' paper and concluded that the bulk of the 97% came from papers expressing only mild agreement with the vague proposition that humans contribute to warming. What is the substantive scientific question that the 97% figure obscures?",
    "answer": "Climate sensitivity — how much warming results from doubling atmospheric CO2 — is the contested number, and credible estimates span a wide range",
    "choices": [
        "Climate sensitivity — how much warming results from doubling atmospheric CO2 — is the contested number, and credible estimates span a wide range",
        "There is no contested scientific question — a finding established by every climate scientist working at every major university",
        "The contested question is whether CO2 exists — a debate that has driven all subsequent climate literature for two decades now",
        "The contested question is whether warming is real — a finding still being investigated by every IPCC working group today",
    ],
    "context": "Equilibrium climate sensitivity (ECS) estimates have spanned roughly 1.5 °C to 4.5 °C per CO2 doubling since the 1979 Charney report. Lower estimates (Lewis & Curry, around 1.5-2 °C) come from observational energy-balance methods. Higher estimates come from some climate models. Newer CMIP6 models produced even higher numbers that have been criticized as 'running hot.' The 97% figure provides political cover but does not resolve the contested empirical question.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "When researcher Andrew Montford and others examined the original abstracts coded by Cook et al. in their 2013 paper, they found that many papers categorized as 'endorsing' the consensus actually took no clear position on human attribution — they simply assumed warming and studied its effects. What's the methodological lesson?",
    "answer": "How researchers code 'endorsement' determines the headline number — methodological choices that drive a 97% claim deserve published scrutiny, not deference",
    "choices": [
        "How researchers code 'endorsement' determines the headline number — methodological choices that drive a 97% claim deserve published scrutiny, not deference",
        "Coding methodology is irrelevant in literature surveys — a position now universally accepted in the climate-research community across the world",
        "Cook published every coding decision for public review — a transparency standard rarely matched by any other field of empirical research",
        "Critical reanalysis of climate papers is impossible — a procedural rule established by major climate-publishing journals over the last decade",
    ],
    "context": "Cook et al. used volunteers to categorize abstracts using a 7-point scale. Tol's reanalysis (2014, *Energy Policy*) found inconsistencies in the coding and concluded the headline 97% claim was not robust. Cook responded with defenses of the methodology. The substantive lesson: large literature-survey claims need methodology scrutiny — and 'consensus' figures depend on what question was actually being asked.",
})


# ---- Urban heat island + temp adjustments + Climategate (5) ----

QUESTIONS.append({
    "tier": 4,
    "question": "Cities tend to be several degrees warmer than surrounding countryside — asphalt, buildings, and waste heat retain warmth. This 'urban heat island' (UHI) effect is well-documented. Why is it controversial in the context of long-term global-temperature records?",
    "answer": "Many long-running weather stations have been engulfed by suburban growth — raising the question of how much measured warming is real climate versus urban encroachment around the sensor",
    "choices": [
        "Many long-running weather stations have been engulfed by suburban growth — raising the question of how much measured warming is real climate versus urban encroachment around the sensor",
        "Urban heat islands have been fully corrected in all datasets — a fact confirmed by every long-term global-temperature reconstruction now in use",
        "Cities are actually cooler than surrounding rural areas — a finding established by recent thermal-imaging studies from satellite platforms",
        "The UHI effect was disproven in 2018 — a result published by a team of meteorologists studying global station coverage that year",
    ],
    "context": "Anthony Watts and others have catalogued how a substantial fraction of US Historical Climatology Network stations sit near asphalt, AC exhausts, or buildings — locations that should be Class 4 or 5 (poor siting). NOAA's 'homogenization' adjustments try to correct for these effects, but the adjustments themselves are contested. McKitrick and Michaels have published peer-reviewed work showing residual UHI contamination in global temperature records.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Analysts examining NASA's GISS and NOAA's GHCN global-temperature datasets over time have noticed a pattern: the same year's reported temperature gets revised downward for past decades and upward for recent decades over successive revisions. What concern do critics including Tony Heller raise about this pattern?",
    "answer": "Repeatedly cooling the past and warming the present creates a steeper warming trend without any new thermometer data — a methodological choice that deserves transparent justification",
    "choices": [
        "Repeatedly cooling the past and warming the present creates a steeper warming trend without any new thermometer data — a methodological choice that deserves transparent justification",
        "Temperature adjustments are never made — a fact established by reviewing the published code of every major climate dataset team in use today",
        "Adjustments always warm the past — a finding contradicting decades of published material from independent statistical analysts examining the record",
        "Critical scrutiny of climate datasets is forbidden — a policy adopted by all major climate-data agencies across multiple recent administrations",
    ],
    "context": "All temperature datasets require adjustments — instrument changes, station moves, time-of-observation corrections. The contested question is whether the adjustment direction is systematically biased. Heller (Steven Goddard) has documented many cases where pre-1940 temperatures were revised downward in successive dataset versions. Defenders argue corrections are scientifically justified case-by-case. Either way, the appearance of one-sided adjustment is a legitimate question for the kid to ask.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "In November 2009 hackers — or whistleblowers — released roughly 1,000 emails from the University of East Anglia's Climatic Research Unit. The trove became known as 'Climategate.' One Phil Jones email referenced using 'Mike's Nature trick' to 'hide the decline.' What was the substantive issue with the 'hide the decline' phrase?",
    "answer": "Recent tree-ring data showed a decline in implied temperature, contradicting instrumental readings — the 'trick' grafted instrumental data over the divergent tree-ring series in published charts",
    "choices": [
        "Recent tree-ring data showed a decline in implied temperature, contradicting instrumental readings — the 'trick' grafted instrumental data over the divergent tree-ring series in published charts",
        "The phrase was a typo — a fact established by the original author within hours of the email leak in late 2009",
        "The phrase referred to a magic trick at a science conference — a recreational activity unrelated to any climate-data methodology",
        "The phrase had no scientific meaning whatsoever — a finding confirmed by every investigation conducted by university committees after the leak",
    ],
    "context": "The 'divergence problem' in tree-ring proxies — late-20th-century tree-rings showing less warming than instruments — was a real, known issue. The 'trick' was splicing instrumental data onto tree-ring reconstructions to produce a single smooth curve, without prominently flagging the divergence. Several inquiries cleared the scientists of misconduct in narrow legal terms, but the methodological choice was substantive — and critics like Steve McIntyre had been raising it before the leak.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Following Climategate, multiple inquiries — Muir Russell, Oxburgh, the UK Parliament's Science and Technology Committee — were conducted in 2010. Critics including Andrew Montford argued the inquiries did not address the substantive methodological complaints, instead clearing the scientists on narrow questions. What's the recognition for the kid?",
    "answer": "Official inquiries can clear individuals while leaving the substantive scientific questions unaddressed — process and substance are different things",
    "choices": [
        "Official inquiries can clear individuals while leaving the substantive scientific questions unaddressed — process and substance are different things",
        "The inquiries addressed every possible methodological concern — a fact established by the published terms of reference of each one in detail",
        "Critics were satisfied with all the inquiry findings — a position taken by every independent researcher who reviewed the documents",
        "Climategate emails were fabricated — a finding confirmed by every forensic analysis conducted on the original email archive that emerged",
    ],
    "context": "The Oxburgh review took six weeks, examined 11 papers (chosen by the CRU), and did not interview critics. Muir Russell included Geoffrey Boulton, a former CRU colleague. Montford's 2010 *The Climategate Inquiries* documented these issues. Steve McIntyre and Ross McKitrick, who had spent years on the methodological critiques, were not seriously engaged. Institutional 'closure' without methodological resolution is a recurring pattern across contested scientific disputes.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "In late 2011 a second tranche of Climategate emails — 'Climategate 2' — was released. Many of these showed scientists privately expressing more uncertainty about climate sensitivity, paleoclimate reconstructions, and model performance than their public statements suggested. What's the recognition skill for the kid?",
    "answer": "Private expressions of uncertainty among scientists can differ from polished public statements — and FOIA releases sometimes reveal that gap",
    "choices": [
        "Private expressions of uncertainty among scientists can differ from polished public statements — and FOIA releases sometimes reveal that gap",
        "Private and public statements were identical — a fact established by comparing the full email archive to every contemporary public statement",
        "Climategate 2 was a fabrication — a finding established by independent forensic analysis of the second email release in late 2011",
        "Email leaks have never affected climate science — a position taken by major journals when refusing to consider critical reanalyses",
    ],
    "context": "The pattern — private hedging followed by confident public communication — recurred prominently during the COVID years (Fauci on masks, Proximal Origin on lab leak). The kid's takeaway: public scientific declarations from institutions are political artifacts as well as scientific ones, and they can systematically understate the genuine uncertainty in the underlying field. This is not a conspiracy claim; it is how institutions work.",
})


# ---- CO2 / plants / greening (3) ----

QUESTIONS.append({
    "tier": 4,
    "question": "Satellite measurements show Earth's vegetated land surface has GREENED substantially since 1980 — leaf area has increased by an area roughly twice the size of the continental United States. A 2016 *Nature Climate Change* paper led by Zaichun Zhu attributed much of this to rising atmospheric CO2. Why is this consequential for the climate debate?",
    "answer": "CO2 is plant food — rising atmospheric CO2 has measurable positive effects on global biomass alongside whatever warming it contributes",
    "choices": [
        "CO2 is plant food — rising atmospheric CO2 has measurable positive effects on global biomass alongside whatever warming it contributes",
        "Global greening was disproved by 2020 — a finding established by satellite reanalysis from the European Space Agency's Earth-monitoring missions",
        "Plants do not respond to atmospheric CO2 — a fact confirmed by every greenhouse-experiment lab study conducted in the last two decades",
        "The greening was due entirely to fertilizer — a finding established by every satellite-data interpretation team working on the question",
    ],
    "context": "The Zhu et al. paper (and subsequent work by Chi Chen, Ranga Myneni, and others) attributes about 70% of the observed greening to CO2 fertilization, with the rest coming from nitrogen deposition, climate change, and land-use change. Catastrophe framing on climate typically omits the greening — Bjorn Lomborg's *False Alarm* (2020) collects these underdiscussed positive effects and argues that policy debates need full accounting.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Commercial greenhouses routinely run CO2 levels at 1,000-1,500 ppm — roughly three to four times atmospheric concentration — because growers know plants respond strongly to enriched CO2. What's the relevance of this commercial practice to the climate debate?",
    "answer": "Atmospheric CO2 has direct biological effects independent of temperature — and those effects include enhanced crop yields, a fact obscured in catastrophe-only framings",
    "choices": [
        "Atmospheric CO2 has direct biological effects independent of temperature — and those effects include enhanced crop yields, a fact obscured in catastrophe-only framings",
        "Commercial greenhouses do not use elevated CO2 — a fact verifiable by surveying any modern commercial greenhouse-equipment supplier today",
        "Plants prefer lower CO2 levels than current atmosphere — a finding established by every plant-physiology textbook written in the last decade",
        "CO2 enrichment harms plant growth — a fact established by every commercial greenhouse trial conducted across the world in recent years",
    ],
    "context": "C3 plants — including wheat, rice, soybeans, and most trees — show strong yield responses to elevated CO2 (the so-called 'CO2 fertilization effect'). The FACE (Free-Air CO2 Enrichment) experiments confirm this in open-field conditions. Yields of major crops have roughly tripled since 1960, with rising CO2 contributing alongside improved varieties and fertilizer. The honest accounting includes both costs and benefits of changing atmospheric composition.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Atmospheric CO2 has risen from about 280 ppm pre-industrial to about 420 ppm today. Plants evolved at much higher CO2 — during the Carboniferous, levels were around 800 ppm; during the Cretaceous, perhaps 1,000-2,000 ppm. What does this evolutionary backdrop suggest about plants today?",
    "answer": "Modern plants evolved under CO2 levels generally HIGHER than today's — and contemporary rises move us closer to, not further from, their evolutionary baseline",
    "choices": [
        "Modern plants evolved under CO2 levels generally HIGHER than today's — and contemporary rises move us closer to, not further from, their evolutionary baseline",
        "Plants evolved at modern CO2 levels — a fact established by surveying every recent paleobotanical reconstruction conducted across the field",
        "Pre-industrial CO2 was the same as today — a finding established by every ice-core dataset and every recent paleoclimate study completed",
        "Plants cannot survive at 420 ppm CO2 — a position taken by every plant-stress physiologist working in the field of agricultural research",
    ],
    "context": "Geological-record CO2 levels were typically much higher than today, except during ice ages. The Carboniferous (359-299 million years ago) had ~800 ppm and produced the dense vegetation that became today's coal seams. The most recent ice age glacials saw CO2 dip to ~180 ppm, near the lower bound for C3 photosynthesis. This evolutionary context is part of why CO2-fertilization-of-plants effects are robust and real — and largely under-discussed in catastrophe coverage.",
})


# ---- Tyndall / Arrhenius / Koonin (5) ----

QUESTIONS.append({
    "tier": 4,
    "question": "Steven Koonin served as Undersecretary for Science at the US Department of Energy under President Obama — he was the senior science official for Obama's energy and climate work. In 2021 he published *Unsettled: What Climate Science Tells Us, What It Doesn't, and Why It Matters*. What's Koonin's central claim?",
    "answer": "Climate is warming and humans contribute — but the catastrophe framing in media coverage is built on top of the IPCC reports, not from them",
    "choices": [
        "Climate is warming and humans contribute — but the catastrophe framing in media coverage is built on top of the IPCC reports, not from them",
        "Climate is not warming at all — a position taken in the book's opening chapter, defended through citation of recent temperature records",
        "CO2 has no effect on climate — a fact Koonin claims to demonstrate using calculations from his time at the Department of Energy",
        "The IPCC reports do not exist — a claim Koonin makes early in the book and supports through documentary research throughout the chapters",
    ],
    "context": "Koonin's *Unsettled* (BenBella, 2021) goes through specific climate claims and compares them against the actual IPCC technical chapters. His finding: the Summary for Policymakers and the media coverage routinely overstate confidence and underplay caveats present in the underlying chapters. Koonin's credentials — PhD Caltech physics, JASON, Obama administration DOE — make his testimony hard to dismiss as fringe.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Irish physicist John Tyndall in 1859 used a brass tube, an infrared source, and a thermopile to demonstrate that CO2, water vapor, and methane absorb infrared heat radiation while pure nitrogen and oxygen do not. Tyndall's experiment is the experimental foundation of the greenhouse effect. What did Tyndall NOT establish?",
    "answer": "The MAGNITUDE of warming Earth experiences from rising CO2 — Tyndall showed the physics works, not how much warming follows in a system with clouds and oceans",
    "choices": [
        "The MAGNITUDE of warming Earth experiences from rising CO2 — Tyndall showed the physics works, not how much warming follows in a system with clouds and oceans",
        "That CO2 absorbs infrared radiation — a phenomenon that was not actually shown in his original brass-tube experiments at all",
        "That gases differ in their absorption — a finding contradicted by every modern spectroscopy measurement performed in any twentieth-century lab",
        "That science can be conducted with brass instruments — a methodological point Tyndall conceded later in his published writings on the matter",
    ],
    "context": "Tyndall's 1859 work was a triumph of experimental physics. Svante Arrhenius extended it in 1896 with the first quantitative estimate of CO2's warming effect (then thought too small to matter on human timescales). The basic radiation physics is firm. The contested questions involve feedbacks: clouds, water vapor, ocean circulation, ice-albedo. The kid should hold both: the physics IS solid AND the magnitude estimate is harder than 'follows from the physics.'",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Swedish chemist Svante Arrhenius in 1896 calculated that doubling atmospheric CO2 would raise global temperature by roughly 5-6 °C. He thought a warming Earth would be beneficial — making Scandinavia more habitable. Modern estimates have ranged from 1.5 to 4.5 °C. What's the kid's recognition here?",
    "answer": "The basic question of climate sensitivity has been actively debated for over a century — and the credible range is wide, not narrow",
    "choices": [
        "The basic question of climate sensitivity has been actively debated for over a century — and the credible range is wide, not narrow",
        "Climate sensitivity was settled by Arrhenius — a fact established in his 1896 paper and uncontested in published research since then",
        "Arrhenius's calculation was discarded entirely — a result confirmed by reviewing every modern climate-physics textbook now in use",
        "Modern estimates exactly match Arrhenius — a finding established by surveying every recent IPCC working-group sensitivity assessment now in print",
    ],
    "context": "The 1979 Charney report set ECS at 1.5-4.5 °C — that range has barely changed in 45 years despite enormous computational investment. The lower end matches Lewis & Curry's observational energy-balance work (~1.5-2 °C). The upper end matches some CMIP6 models that the climate-modeling community itself flagged as 'running hot.' Arrhenius was right that the question is real. Knowing the answer precisely is much harder than he imagined.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Koonin in *Unsettled* devotes a chapter to hurricanes — he points out that the actual IPCC reports show no clear trend in global hurricane frequency or intensity, while media coverage during major hurricanes routinely attributes them to climate change. What's the recognition skill?",
    "answer": "Media coverage of specific weather events outruns the formal scientific assessments — and the formal assessments often show no clear long-term trend",
    "choices": [
        "Media coverage of specific weather events outruns the formal scientific assessments — and the formal assessments often show no clear long-term trend",
        "IPCC reports show clear hurricane trends — a fact verifiable by reviewing any of the working-group physical-science chapters in detail",
        "All major weather events are climate-driven — a position established by every working hurricane scientist in the United States today",
        "Hurricane frequency has doubled since 2000 — a finding established in successive NOAA reports on Atlantic-basin storm statistics",
    ],
    "context": "Roger Pielke Jr. has spent decades documenting the gap between media climate-attribution claims and the actual scientific literature on weather extremes. Hurricane landfall rates, tornado frequency, and global drought area show no clear monotonic climate signals. IPCC AR6 itself includes confidence ratings — many extreme-event trends are 'low confidence' for human attribution. The catastrophe framing relies on selective reading.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "When *Unsettled* was published in 2021, several climate scientists publicly criticized Koonin without engaging the specific factual claims — instead questioning his credentials or motives. Andrew Dessler and others published critiques; Koonin responded with detailed defenses. What's the recognition skill from this exchange?",
    "answer": "Substantive engagement with specific claims matters more than credential-attacks — and the kid should evaluate which side is engaging the specifics",
    "choices": [
        "Substantive engagement with specific claims matters more than credential-attacks — and the kid should evaluate which side is engaging the specifics",
        "Koonin was uniformly accepted by all critics — a fact verifiable by reading every response to *Unsettled* in major scientific journals at the time",
        "Climate critics never respond to dissenters — a finding established by surveying every response to skeptical books in the field over the years",
        "Credentials settle scientific disputes — a position established in the methodology of every major scientific journal worldwide today",
    ],
    "context": "Koonin's debate format with Andrew Dessler at the 2021 Soho Forum is a good example of substance-meets-substance. The pattern of ad hominem dismissal of credentialed dissenters (Koonin, Curry, Lindzen, Pielke Jr., Lomborg) has been a documented feature of climate-debate institutional dynamics for two decades. When credentials and substance both favor a critique, the response often shifts to motive.",
})


# ---- Alarmism / cult / carbon tax (4) ----

QUESTIONS.append({
    "tier": 4,
    "question": "Climate activist Greta Thunberg in 2018 retweeted (and later deleted) a column predicting the world would end in 2023 if climate change was not stopped. Roger Hallam of Extinction Rebellion has predicted billions of deaths. Activist movements have repeatedly issued near-term apocalyptic claims. What's the kid's recognition skill?",
    "answer": "Near-term apocalyptic predictions are a recurring feature of certain political-activist movements — and their predictions can be tracked against actual outcomes",
    "choices": [
        "Near-term apocalyptic predictions are a recurring feature of certain political-activist movements — and their predictions can be tracked against actual outcomes",
        "Apocalyptic predictions are made only by mainstream scientists — a fact verifiable in the published literature of any major climate-research center",
        "Activists do not make dated predictions — a position confirmed by reviewing every recent statement of every major activist organization in the field",
        "Activist predictions are uniformly accurate — a finding confirmed by examining the historical record of every major climate-movement statement made",
    ],
    "context": "The pattern of near-term doom prediction, deadline passes, new prediction with fresh deadline, is documented by Michael Shellenberger (*Apocalypse Never*, 2020), Bjorn Lomborg (*False Alarm*, 2020), and many others. This is not the same as denying climate change is real — it is recognizing that activist movements operating on dated apocalyptic claims have a documented failure rate that the kid should know exists.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Critics including journalist Michael Shellenberger have observed that some climate-activist communities exhibit features that resemble religious or cult dynamics — apocalyptic framing, demand for total commitment, demonization of dissenters as morally evil rather than empirically wrong. Why does this framing matter for the kid?",
    "answer": "Disagreement labeled as moral evil rather than empirical error shuts down debate — and recognizing the move is the kid's defense against being manipulated by it",
    "choices": [
        "Disagreement labeled as moral evil rather than empirical error shuts down debate — and recognizing the move is the kid's defense against being manipulated by it",
        "Climate activists do not use moral framings — a fact verifiable by surveying every public statement from every major environmental organization today",
        "Religious framings have no place in science — a position confirmed by every public-communications style guide used by climate scientists today",
        "Cult dynamics never appear in activist movements — a position established by sociologists studying every major political movement of the last century",
    ],
    "context": "Shellenberger (*Apocalypse Never*, 2020) writes from inside the environmental movement — he was Time magazine's 'Hero of the Environment' in 2008. His critique is not climate-denialist; it is that turning empirical questions into moral crusades is both bad epistemology and politically counterproductive. The features he names — millennialism, in-group purity tests, demonization of dissenters — are well-known to scholars of religion and political movements.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Proposals for carbon taxes — taxing fossil-fuel use to discourage emissions — are often framed as 'following the science.' Economists including William Nordhaus have analyzed them as policy choices with trade-offs between emissions reductions, energy costs, and human welfare. What does this framing reveal?",
    "answer": "Tax policy is a political-economic choice with trade-offs, not a neutral scientific conclusion — and presenting it as 'the science' conflates two different categories",
    "choices": [
        "Tax policy is a political-economic choice with trade-offs, not a neutral scientific conclusion — and presenting it as 'the science' conflates two different categories",
        "Carbon taxes are neutral scientific conclusions — a position established by every environmental-economics textbook used in the last two decades",
        "Tax policy is dictated by physics — a finding contradicting all standard economics literature on environmental-policy design and human welfare",
        "All carbon-tax proposals are identical — a fact verifiable by reviewing every active proposal in every recent US Congressional session held lately",
    ],
    "context": "Nordhaus's DICE model (and his 2018 Nobel) treats carbon-emission policy as an optimization problem — costs of damages versus costs of mitigation. Most economic analyses find that aggressive near-term emission cuts have higher costs than benefits relative to gradual transition. The political claim that a particular tax level 'follows the science' is a category mistake — even granting the underlying climate physics, the policy choice involves values and trade-offs.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Mark Lynas published *Six Degrees* in 2007 — a book walking through projected impacts at each degree of warming. By 2020 Lynas had revised his view in *Our Final Warning*. Other voices, including Bjorn Lomborg and Steven Koonin, argued the catastrophe escalation was not supported by the actual IPCC technical chapters. What's the recognition?",
    "answer": "Catastrophe coverage diverges from IPCC technical chapters enough that critical reading matters — including by credentialed mainstream insiders",
    "choices": [
        "Catastrophe coverage diverges from IPCC technical chapters enough that critical reading matters — including by credentialed mainstream insiders",
        "All climate journalists agree on catastrophe framing — a fact verifiable by surveying every recent book on climate change written in the last decade",
        "IPCC chapters and media coverage always align — a position established by every climate-communications scholar working at any major university today",
        "Catastrophe framing is the most accurate — a finding established by checking every major climate prediction against actual outcomes in recent years",
    ],
    "context": "Lomborg's *False Alarm* (2020) walks through cost-benefit analysis for various proposed mitigation paths. Koonin's *Unsettled* (2021) does the same for specific scientific claims. The divergence between catastrophe coverage and IPCC technical content is not a fringe critique — it has been raised by credentialed mainstream voices for years. The kid's defense is reading both the Summary for Policymakers AND the underlying chapters.",
})


# ============================================================================
# COSMOLOGY + ASTRONOMY BLOCK (15)
# ============================================================================

# ---- Dark energy (2) ----

QUESTIONS.append({
    "tier": 4,
    "question": "In 1998 two independent supernova-survey teams — one led by Saul Perlmutter, the other by Brian Schmidt and Adam Riess — discovered that the universe's expansion is ACCELERATING, not slowing down as gravity alone would predict. They shared the 2011 Nobel Prize in Physics. What can we honestly say about the unknown driver they discovered?",
    "answer": "We've measured its effects precisely — but we still don't know what it IS in physical terms",
    "choices": [
        "We've measured its effects precisely — but we still don't know what it IS in physical terms",
        "We identified it as a specific particle in 2018 — a finding confirmed by the Large Hadron Collider's program of experimental measurements",
        "It was an experimental artifact eventually retracted — a result that ended supernova-cosmology research in the early twenty-first century",
        "It is identical to dark matter — a finding established by every recent cosmology textbook used at any university worldwide",
    ],
    "context": "Perlmutter (Berkeley/Supernova Cosmology Project) and Schmidt/Riess (High-Z Supernova Search Team) both used Type Ia supernovae as 'standard candles' to measure cosmic expansion history. The accelerating-expansion result was unexpected — Einstein's 1917 'cosmological constant' returned from the dead. Dark energy makes up about 68% of the universe's energy content. Vacuum-energy predictions from QFT are off by 10^120 — the worst theoretical prediction in physics.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "When vacuum-energy theory tries to predict the 'cosmological constant' — Einstein's term that, revived, represents dark energy — the theoretical estimate is off from observation by a factor of 10^120 (a one with 120 zeros after it). What does this discrepancy illustrate about the state of physics?",
    "answer": "Even our best fundamental theory has at least one number it cannot predict — a fact honest physicists acknowledge as an open problem",
    "choices": [
        "Even our best fundamental theory has at least one number it cannot predict — a fact honest physicists acknowledge as an open problem",
        "The discrepancy was resolved by string theory — a finding established by mainstream theoretical physicists in the early twenty-first century",
        "There is no discrepancy — a position taken by every quantum-field-theory textbook used in graduate physics programs in the last decade",
        "Theoretical physics solved cosmology in 2010 — a fact verifiable by reviewing the published research in any major theoretical journal of that year",
    ],
    "context": "The 'cosmological constant problem' is famously described as the worst theoretical-prediction failure in physics. Proposed solutions include the anthropic principle (selection effects in a multiverse), quintessence (a dynamical field rather than a constant), and modified-gravity approaches like Verlinde's emergent gravity. None has decisive empirical support. The kid's takeaway: physics has open problems, including very deep ones, and that's normal.",
})


# ---- Dark matter / Vera Rubin (2) ----

QUESTIONS.append({
    "tier": 4,
    "question": "American astronomer Vera Rubin spent the 1970s measuring how stars orbit around the centers of spiral galaxies. She found that outer stars were orbiting much FASTER than visible mass should allow — they should have been flung off. The implication was that galaxies are embedded in a halo of unseen matter. What is the honest scientific answer about dark matter today?",
    "answer": "It's about 27% of the universe's mass-energy budget by gravitational effect — but we still have no direct detection of what it IS",
    "choices": [
        "It's about 27% of the universe's mass-energy budget by gravitational effect — but we still have no direct detection of what it IS",
        "It was identified as a known particle in 2018 — a finding established by direct-detection experiments at underground laboratories worldwide",
        "It does not exist — a position established by every modified-gravity theorist working at any major physics institute over the last decade",
        "It is the same as ordinary matter — a fact verifiable by reviewing every recent particle-physics textbook now in standard university use",
    ],
    "context": "Rubin's rotation-curve measurements (with Kent Ford) confirmed earlier hints from Fritz Zwicky's 1933 Coma Cluster mass discrepancy. Candidate particles — WIMPs, axions, sterile neutrinos — have been searched for in deep-mine detectors (LUX, XENONnT) for decades without confirmation. MOND (Modified Newtonian Dynamics, Mordehai Milgrom 1983) is the leading modified-gravity alternative. The honest answer: open mystery.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Israeli physicist Mordehai Milgrom proposed in 1983 that very-low-acceleration regimes might require modified gravity (MOND) rather than dark matter. His framework fits galaxy rotation curves with no fitted parameters at all per galaxy — surprisingly well. Why does MOND remain a minority position despite empirical success on galaxy scales?",
    "answer": "MOND struggles at cluster scales and with cosmic-microwave-background features that dark-matter models fit naturally — so the field broadly favors dark matter for now",
    "choices": [
        "MOND struggles at cluster scales and with cosmic-microwave-background features that dark-matter models fit naturally — so the field broadly favors dark matter for now",
        "MOND has been disproved entirely — a finding established by every direct-detection particle-physics experiment of the last two decades",
        "MOND is identical to dark-matter theory — a position established by every recent cosmology textbook used at major universities globally",
        "MOND was never published in peer-reviewed journals — a fact verifiable by searching the major physics-archive websites for the original paper",
    ],
    "context": "MOND fits the Tully-Fisher relation and galaxy rotation curves with remarkable economy. Stacy McGaugh and Pavel Kroupa have championed it for decades. The Bullet Cluster (2006) is often cited as decisive for dark matter, though MOND modifications continue to engage that data. The honest scientific situation: both frameworks face real difficulties, both have committed researchers, and neither is settled.",
})


# ---- CMB 1964 (2) ----

QUESTIONS.append({
    "tier": 4,
    "question": "In 1964 Arno Penzias and Robert Wilson at Bell Labs were trying to track down a mysterious 'hiss' in their large microwave horn antenna — they tried cleaning out pigeon droppings, sealing connections, all the troubleshooting they could think of. They eventually realized the hiss was real. What had they accidentally discovered?",
    "answer": "The cosmic microwave background — the leftover radiation from the early universe, predicted by Big Bang theory and previously thought undetectable",
    "choices": [
        "The cosmic microwave background — the leftover radiation from the early universe, predicted by Big Bang theory and previously thought undetectable",
        "Microwave interference from a passing comet — a finding established by later astronomical observations confirming the comet's trajectory at the time",
        "A signal from extraterrestrial intelligence — a discovery announced at a conference but later withdrawn due to spectrum reanalysis issues",
        "A malfunction in the antenna's wiring — a problem isolated and repaired before publication of the famous 1964 paper they wrote",
    ],
    "context": "Penzias and Wilson's discovery turned out to be the cosmic microwave background, predicted by Ralph Alpher and Robert Herman in 1948 (working with George Gamow). At the same time, Robert Dicke's Princeton group was building an antenna specifically to search for it — they were beaten by accident. Penzias and Wilson won the 1978 Nobel Physics. The CMB is now mapped at high resolution (WMAP, Planck) and is one of the strongest pieces of Big Bang evidence.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "When the cosmic microwave background was mapped at high resolution — first by COBE in 1992, then WMAP and Planck — the temperature variations were vanishingly small (parts in 100,000) but rich in structure. Those tiny variations match Big Bang model predictions to remarkable precision. What does this match teach the kid about modern cosmology?",
    "answer": "The Big Bang model has passed quantitative tests that very few non-trivial theories have ever passed — even while open mysteries (dark matter, dark energy, inflation) remain",
    "choices": [
        "The Big Bang model has passed quantitative tests that very few non-trivial theories have ever passed — even while open mysteries (dark matter, dark energy, inflation) remain",
        "The Big Bang has been disproven by CMB measurements — a finding established by every recent cosmology team working at major observatories",
        "CMB data is inconsistent with all cosmological models — a position established by every published analysis of the WMAP and Planck data releases",
        "CMB variations have no theoretical significance — a position established by every recent astrophysics textbook now in standard university use",
    ],
    "context": "George Smoot and John Mather won the 2006 Nobel for COBE results. The acoustic peaks in the CMB power spectrum match predictions of the Lambda-CDM cosmological model. The match does not make Lambda-CDM final — dark matter, dark energy, and the inflationary epoch all remain open at the level of physical mechanism. But the quantitative agreement at the level of statistical structure is one of the great successes of modern science.",
})


# ---- Eddington 1919 (2) ----

QUESTIONS.append({
    "tier": 4,
    "question": "On May 29, 1919, British astronomer Arthur Eddington led an expedition to Príncipe (off West Africa) and Sobral (Brazil) to photograph a total solar eclipse. Einstein's 1915 general relativity predicted starlight passing near the Sun would bend by a specific amount — about 1.75 arcseconds — twice what Newton's gravity predicted. What did Eddington's results do?",
    "answer": "The bending matched Einstein's prediction closely enough to vindicate general relativity over Newton — and the news made Einstein an overnight global celebrity",
    "choices": [
        "The bending matched Einstein's prediction closely enough to vindicate general relativity over Newton — and the news made Einstein an overnight global celebrity",
        "The starlight bent by Newton's predicted amount — a result that refuted Einstein's theory of general relativity for several decades",
        "No bending was detected — a finding that left both theories in scientific doubt until further eclipse expeditions in later years",
        "The plates were destroyed before measurement — a fact that delayed any general-relativity test until much later in the twentieth century",
    ],
    "context": "Eddington's announcement at a joint Royal Society and Royal Astronomical Society meeting on November 6, 1919 made the front page of *The Times*: 'Revolution in Science — New Theory of the Universe — Newtonian Ideas Overthrown.' Modern reanalysis has questioned how confidently the 1919 data alone could distinguish theories — but many later eclipse, radio-quasar, and gravity-wave measurements have confirmed Einstein's prediction with high precision.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Modern reanalysis of Arthur Eddington's 1919 eclipse plates has suggested that his published error bars may have been smaller than the actual data supported — that is, the 1919 data alone may have been less decisive than the public announcement claimed. What does this nuance teach about scientific history?",
    "answer": "Even canonical confirming experiments can have messier data than their public narrative implies — but Einstein's prediction has been confirmed many times since by independent methods",
    "choices": [
        "Even canonical confirming experiments can have messier data than their public narrative implies — but Einstein's prediction has been confirmed many times since by independent methods",
        "Eddington fabricated his entire dataset — a finding established by every modern reanalysis published in scientific journals over the last three decades",
        "General relativity has never been confirmed — a finding contradicting every textbook account of twentieth-century experimental physics now in use",
        "The 1919 experiment was a hoax — a position taken by every working historian of science engaged with twentieth-century astronomy questions today",
    ],
    "context": "Daniel Kennefick's *No Shadow of a Doubt* (2019) gives a detailed historian-of-science account of the 1919 expeditions and the later reanalyses. The key point is that Eddington's published certainty did somewhat outrun his data — but subsequent measurements (eclipses 1922, 1953, radio-source deflections by the Sun starting in the 1960s, lunar laser ranging, Mercury's perihelion, gravitational waves from black-hole mergers detected by LIGO 2015) have all confirmed general relativity with growing precision.",
})


# ---- JWST (2) ----

QUESTIONS.append({
    "tier": 4,
    "question": "The James Webb Space Telescope launched on Christmas Day 2021 — a $10 billion project decades in the making, parked 1.5 million km from Earth at the Sun-Earth L2 Lagrange point. Within months of beginning science operations, JWST images of early galaxies challenged some pre-launch assumptions. What was the surprise?",
    "answer": "Galaxies in the very early universe appeared more massive and mature than expected — a finding that pressured standard galaxy-formation models",
    "choices": [
        "Galaxies in the very early universe appeared more massive and mature than expected — a finding that pressured standard galaxy-formation models",
        "Galaxies were exactly where standard models predicted — a finding that confirmed every prior cosmological prediction in the field over the prior decade",
        "No galaxies were detected at high redshift — a finding establishing that early-universe galaxies do not exist as a class of astronomical object",
        "JWST detected no light at all — a fact that led to a redesign of all subsequent observing programs in the months after launch",
    ],
    "context": "Several papers in 2022-2023 reported galaxies at z > 10 (very-early universe) that appeared too large or too well-formed for standard galaxy-evolution models. Some of these results were later moderated — redshift estimates and mass estimates both can be refined. The point is not that cosmology is wrong, but that JWST is doing what good instruments do: providing data that pushes models.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "JWST's primary mirror is 6.5 meters across — too large to fit in any rocket fairing as a single piece. NASA engineers solved this by building it from 18 gold-coated hexagonal segments that fold for launch and unfold in space. The deployment sequence after launch involved roughly 300 single-point failure modes. What does the success of this mission illustrate?",
    "answer": "Hard engineering — done carefully, with redundancy and patience — can deliver instruments that were nearly impossible only a generation earlier",
    "choices": [
        "Hard engineering — done carefully, with redundancy and patience — can deliver instruments that were nearly impossible only a generation earlier",
        "Engineering complexity always leads to failure — a position established by NASA's project-management training programs over the years",
        "JWST has not been deployed — a fact verifiable by reviewing every recent NASA mission-status update published since the 2021 launch",
        "Folding telescope mirrors do not work — a result established by every prior space-mission attempt in the second half of the twentieth century",
    ],
    "context": "JWST development spanned roughly 25 years from concept (Hubble's successor study, late 1990s) through launch (2021). The Northrop Grumman team and NASA Goddard managed thousands of subcontractors. The mid-infrared optimization required cooling to near 50 K passively via a five-layer sunshield. The deployment was nominally perfect. The mission shows that ambitious science instruments can still be built — and is the kind of triumph the kid should know about.",
})


# ---- Voyager 1 (2) ----

QUESTIONS.append({
    "tier": 4,
    "question": "Voyager 1 launched on September 5, 1977 — a Titan IIIE-Centaur rocket carrying a probe the size of a small car, plus a gold record with sounds and images from Earth. In August 2012, after 35 years of travel, plasma data finally confirmed Voyager 1 had crossed the heliopause and entered interstellar space. What's the kid's takeaway?",
    "answer": "Patient scientific engineering can produce instruments that outlive their designers — and the universe is vastly larger than the human timescales that build the tools",
    "choices": [
        "Patient scientific engineering can produce instruments that outlive their designers — and the universe is vastly larger than the human timescales that build the tools",
        "Voyager 1 has returned to Earth — a fact reported in NASA mission updates published in the last decade about its trajectory home",
        "No probe has ever left the heliosphere — a fact established by every recent NASA mission overview document since the launch of the program",
        "Voyager 1 has stopped working — a result confirmed by every JPL communications-status report issued in the last several years to the public",
    ],
    "context": "Voyager 1 was originally planned for a 5-year primary mission to Jupiter and Saturn. The 'Grand Tour' alignment allowed it to use gravity assists to reach interstellar space. As of 2025, it continues to transmit at very low data rate (still using its 1977-era hardware running on radioisotope thermoelectric generators). Voyager 2 crossed the heliopause in 2018. The Golden Record carries greetings in 55 languages and music from many cultures — Bach, Beethoven, Chuck Berry's 'Johnny B. Goode.'",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Voyager 1's electric power comes from radioisotope thermoelectric generators (RTGs) — devices that turn the heat of decaying plutonium-238 into electricity. By 2025, after almost 50 years, those RTGs are nearing the end of their useful output. What does Voyager 1's longevity say about long-mission engineering?",
    "answer": "Simple, robust hardware operating in cold deep space — running well-defined tasks — can survive for decades beyond its design lifetime",
    "choices": [
        "Simple, robust hardware operating in cold deep space — running well-defined tasks — can survive for decades beyond its design lifetime",
        "All space hardware fails after five years — a finding established by every recent NASA mission-reliability study published in any reviewed journal",
        "Voyager 1 has been replaced by a newer probe — a fact reported in NASA's recent overview of all currently-operating deep-space missions",
        "RTGs cannot operate at low temperatures — a result that contradicts the entire history of deep-space-mission power-system design since the 1960s",
    ],
    "context": "Voyager engineers at JPL spend significant effort each year deciding which instruments to power down as RTG output declines. The plutonium-238 is hard to manufacture — the US restarted production in the 2010s after a long pause. The pattern — extremely-long-lived deep-space probes — is one of the achievements that the modern public-facing 'science is in crisis' narratives tend to undersell. Engineering excellence is one of the things science has done well.",
})


# ---- Moon landing 1969 (3) ----

QUESTIONS.append({
    "tier": 4,
    "question": "On July 20, 1969, NASA astronauts Neil Armstrong and Buzz Aldrin walked on the Moon — roughly 600 million people watched live. Six Apollo missions landed on the Moon between 1969 and 1972. Some 'moon-landing-was-faked' claims have persisted. What's the strongest single line of physical evidence against the hoax claim?",
    "answer": "Lunar retroreflectors left by Apollo missions still bounce laser pulses from Earth observatories — a result that requires actual reflectors on the lunar surface",
    "choices": [
        "Lunar retroreflectors left by Apollo missions still bounce laser pulses from Earth observatories — a result that requires actual reflectors on the lunar surface",
        "Soviet intelligence agencies endorsed the Apollo landings — a finding established in declassified KGB documents released over the past few decades",
        "The Apollo astronauts have never been disputed by hoax claimants — a fact verifiable in any survey of recent conspiracy-related publications worldwide",
        "All hoax-claim believers later retracted — a finding established by surveying every public statement of every prominent Moon-landing skeptic in recent years",
    ],
    "context": "Apollo 11, 14, and 15 left corner-cube retroreflectors on the lunar surface. The Apache Point Observatory in New Mexico, the Côte d'Azur in France, and others routinely bounce laser pulses off these reflectors — measuring the Earth-Moon distance to millimeters. The Soviet Lunokhod rovers also left retroreflectors (still used today). Independent radar and laser data from multiple countries, plus the 380+ kg of lunar samples studied by labs worldwide, make the hoax claim physically untenable.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Apollo missions brought roughly 380 kg of lunar samples back to Earth between 1969 and 1972. Those samples have been distributed to researchers in many countries — including, during the Cold War, sample exchanges with the Soviet Union. What does this distribution pattern undercut about the moon-hoax claim?",
    "answer": "Physical lunar samples have been independently analyzed in many countries — and they have the chemistry, isotope ratios, and lack-of-water signatures of genuine Moon rock",
    "choices": [
        "Physical lunar samples have been independently analyzed in many countries — and they have the chemistry, isotope ratios, and lack-of-water signatures of genuine Moon rock",
        "No samples were ever returned by Apollo missions — a fact established by every recent review of lunar-sample curation programs at NASA Johnson",
        "All samples have been kept secret by NASA — a finding contradicted by every published lunar-sample inventory issued by NASA in the past decade",
        "Samples were declared inadmissible scientific evidence — a position adopted by NASA's lunar-sample curation team during the second decade of the twenty-first century",
    ],
    "context": "The Lunar Sample Building at NASA Johnson Space Center curates Apollo samples; subsamples have gone to researchers worldwide. Soviet Luna 16/20/24 missions also returned smaller lunar samples; cross-comparison with Apollo material was done in the Cold-War era and continues. The isotope ratios (especially oxygen) match the Apollo-Luna pattern and differ from Earth in known systematic ways. Chinese Chang'e samples (2020) provide an even more independent check.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "After the Apollo 11 mission, Buzz Aldrin and other returning astronauts were placed in quarantine for three weeks to protect Earth from potential lunar pathogens. The quarantine seems quaint in retrospect — but at the time it reflected genuine scientific uncertainty about Moon contamination. What does this practice illustrate?",
    "answer": "Real scientific institutions take genuine uncertainty seriously — including risks that turn out to be small in retrospect",
    "choices": [
        "Real scientific institutions take genuine uncertainty seriously — including risks that turn out to be small in retrospect",
        "Lunar pathogens were known to exist before Apollo — a finding established by every recent astrobiology research program at NASA Headquarters today",
        "Apollo astronauts were not quarantined — a fact established by reviewing every recent NASA mission-history document available to the public worldwide",
        "Quarantine procedures are never used in science — a position established by reviewing every recent biosafety-protocol document used in biological research",
    ],
    "context": "The Apollo quarantine ran from Apollo 11 through Apollo 14. It involved sealed transport from splashdown to the Lunar Receiving Laboratory at Johnson Space Center. NASA also sterilized lunar samples that were intended for biological exposure tests. The procedures were dropped after no signs of lunar microbes appeared. The pattern — taking unknown risks seriously, then updating once data accumulated — is good institutional behavior worth honoring.",
})


# ============================================================================
# EARTH SCIENCE DEEP (5)
# ============================================================================

QUESTIONS.append({
    "tier": 4,
    "question": "Lake Vostok lies beneath roughly 4 km of Antarctic ice — sealed off from Earth's surface for millions of years. Russian researchers drilled to it in 2012 hoping to find microbial life isolated from the modern biosphere. What was the major scientific concern about the Vostok drilling project?",
    "answer": "Drilling fluid used to keep the borehole open could contaminate the lake — making any 'discovery' of microbes possibly a discovery of the drill team's surface bacteria",
    "choices": [
        "Drilling fluid used to keep the borehole open could contaminate the lake — making any 'discovery' of microbes possibly a discovery of the drill team's surface bacteria",
        "The drilling project would damage the lake's atmosphere — a fact established by every recent Antarctic-research-station environmental review",
        "Russian researchers were not allowed to study the lake — a position established by every recent international treaty governing Antarctic exploration",
        "Lake Vostok had been previously sampled — a fact verifiable by reviewing every previous Antarctic ice-coring project conducted by any nation",
    ],
    "context": "The Russian Vostok project used kerosene and Freon as drilling fluid, which raised serious contamination concerns from international colleagues. American (WISSARD/Lake Whillans) and British (Lake Ellsworth) projects designed cleaner protocols. Lake Vostok findings have included possible bacterial DNA, but the contamination concern means no result can be confidently attributed to the lake itself rather than the drill chain. The kid's takeaway: scientific design matters as much as results.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "On September 1-2, 1859, telegraph operators across Europe and North America watched their systems start fires, send sparks, and operate even with batteries disconnected. Auroras reached the Caribbean. The cause was a massive coronal mass ejection — the Carrington Event. What's the modern-infrastructure recognition skill?",
    "answer": "A Carrington-class event today would damage transformers, satellites, and grids at continental scale — a documented natural hazard the modern world has not hardened against",
    "choices": [
        "A Carrington-class event today would damage transformers, satellites, and grids at continental scale — a documented natural hazard the modern world has not hardened against",
        "Modern infrastructure is immune to solar storms — a fact established by every recent NERC (North American Electric Reliability Corporation) review",
        "The Carrington Event was a regional storm — a finding contradicted by every contemporary 1859 telegraph and astronomical record from many locations",
        "Solar storms cannot affect electronic systems — a position contradicted by every recent space-weather-and-power-systems study now in scientific use",
    ],
    "context": "The 1859 event was observed by English astronomer Richard Carrington (and independently by Richard Hodgson). A 2012 paper by NASA's Pete Riley estimated the probability of a Carrington-class event in the next decade at ~12%. The 1989 Quebec blackout (a much smaller geomagnetic storm) showed real grid vulnerability. Hardening transformers is technically feasible but expensive; the policy choice has been not to do it at scale. Real natural risk; real underdiscussed prep gap.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Earth's magnetic field has reversed polarity (north becomes south, south becomes north) many times over geological history — the last full reversal, the Brunhes-Matuyama reversal, happened about 780,000 years ago. Magnetometer readings of seafloor basalt show the stripe pattern. What does this geological pattern reveal?",
    "answer": "Magnetic reversals are a normal feature of Earth's deep behavior — not a coming-disaster but a slow process that has happened repeatedly without ending life",
    "choices": [
        "Magnetic reversals are a normal feature of Earth's deep behavior — not a coming-disaster but a slow process that has happened repeatedly without ending life",
        "Pole reversals have happened only once in Earth's history — a fact established by every recent geophysical-survey project around the world today",
        "The most recent reversal was in the year 1985 — a finding established by every recent magnetic-pole-position dataset published in this century",
        "Pole reversals destroy all surface life — a position contradicted by every paleontological record spanning the last several million years of Earth's history",
    ],
    "context": "The Vine-Matthews-Morley magnetic-stripe data on seafloor basalt — the same data that vindicated continental drift in the 1960s — also documented Earth's reversal history. Reversals happen on timescales of thousands of years (the field weakens, then strengthens in reverse). Earth's magnetic field has been weakening over the last 200 years; whether this signals an approaching reversal is contested. Either way, the geological record shows reversals are normal.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "The Yellowstone caldera in Wyoming has had three major eruptions in the last 2.1 million years (the most recent ~640,000 years ago) — VEI-8 events that would have continent-scale climate effects. Recent coverage of Yellowstone risk has often inflated the imminent-eruption framing. What's the honest probability framing?",
    "answer": "USGS estimates the annual probability of a caldera-forming eruption is roughly 1 in 730,000 — real risk, not zero, but vanishingly small in any given year",
    "choices": [
        "USGS estimates the annual probability of a caldera-forming eruption is roughly 1 in 730,000 — real risk, not zero, but vanishingly small in any given year",
        "The eruption probability for any year is 50% — a finding established in every recent USGS Yellowstone Volcano Observatory annual review published",
        "Yellowstone is no longer volcanically active — a fact contradicted by every recent USGS Yellowstone Volcano Observatory routine-monitoring report",
        "Yellowstone is overdue for eruption — a position contradicted by every careful statistical-volcanology paper published in the last several years",
    ],
    "context": "The Yellowstone Volcano Observatory monitors seismicity, ground deformation, gas emissions, and temperature constantly. Background activity (small earthquakes, geyser changes) is normal. The 'overdue for eruption' framing relies on misreading the recurrence interval — three eruptions in 2.1 million years isn't a clock you can read 'next eruption in X years' from. Honest risk: real, but vanishingly small in any decade. The kid should know how to interpret return periods.",
})

QUESTIONS.append({
    "tier": 4,
    "question": "Tunguska, Siberia, June 30, 1908: a meteoroid roughly 50-60 meters across exploded several kilometers above the ground, flattening 2,000 square kilometers of forest. Had it arrived a few hours later, it would have hit a major European city. What's the kid's takeaway about asteroid-impact risk?",
    "answer": "Earth has been hit by city-destroyer-sized objects within living memory — and systematic detection of incoming objects is real planetary-defense work, not science fiction",
    "choices": [
        "Earth has been hit by city-destroyer-sized objects within living memory — and systematic detection of incoming objects is real planetary-defense work, not science fiction",
        "Earth has never been struck by an asteroid — a position contradicted by every crater-survey project conducted across the last half-century globally",
        "Tunguska did not happen — a fact contradicted by every contemporary 1908 newspaper report and every subsequent Russian expedition to the site",
        "Asteroid risk is impossible — a position established by every recent JPL Near-Earth-Object survey program update in the past decade today",
    ],
    "context": "The Chelyabinsk event (February 2013) — a roughly 20-meter object exploding over a Russian city, injuring 1,500 — was a smaller, more-recent reminder. NASA's planetary-defense work includes the NEOWISE survey and the 2022 DART mission (which successfully deflected the asteroid Dimorphos). NASA has catalogued over 90% of NEOs larger than 1 km; smaller objects in the Tunguska size range remain mostly unseen. This is real, ongoing, important — and worth celebrating.",
})


# ---------------------------------------------------------------------------
# Validation harness
# ---------------------------------------------------------------------------

def main() -> None:
    # Load the existing science bank for duplicate / collision checks
    print(f"Loading bank: {BANK_PATH}")
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    print(f"Bank loaded: {len(bank)} questions")
    dup_idx, ans_idx = build_bank_indices(bank)

    # Also augment the bank index with each new question as we add it, so we
    # catch internal collisions between the 50 new questions.
    running_bank = list(bank)

    passed: list[dict] = []
    failed: list[tuple[int, dict, dict]] = []

    out_path = OUT_PATH
    print(f"Generating {len(QUESTIONS)} questions...")
    for idx, q in enumerate(QUESTIONS, 1):
        # Rebuild indices to include all previously-passed questions
        cur_dup_idx, cur_ans_idx = build_bank_indices(running_bank)
        verdict = validate_rewrite(
            "science", q,
            bank=running_bank,
            dup_index=cur_dup_idx,
            answer_index=cur_ans_idx,
            replace_idx=None,
        )
        # Compute total chars
        total_chars = len(q["question"]) + sum(len(c) for c in q["choices"])
        status_short = verdict["verdict"]
        print(f"  [{idx:2d}/{len(QUESTIONS)}] total={total_chars:4d}ch {status_short}")
        if verdict["verdict"] == "FAIL":
            for gate, reason in verdict["hard_fails"]:
                print(f"        FAIL  {gate}: {reason[:120]}")
            failed.append((idx, q, verdict))
        else:
            if verdict["soft_warns"]:
                for gate, reason in verdict["soft_warns"]:
                    print(f"        soft  {gate}: {reason[:120]}")
            passed.append(q)
            running_bank.append(q)
        # Save as we go
        out_payload = {
            "tier": 4,
            "summary": {
                "questions_generated": len(passed),
                "by_pillar": {"4": len(passed)},
                "failed": len(failed),
            },
            "questions": passed,
        }
        out_path.write_text(
            json.dumps(out_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print(f"\nFinal: passed={len(passed)}  failed={len(failed)}")
    if failed:
        print("FAILED QUESTIONS (idx in 1-based input order):")
        for i, q, v in failed:
            print(f"  #{i}: {q['question'][:80]}")
            for gate, reason in v["hard_fails"]:
                print(f"     - {gate}: {reason[:200]}")


if __name__ == "__main__":
    main()
