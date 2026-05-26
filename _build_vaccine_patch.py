"""Build vaccine audit patch for the science bank.

Classifies all 115 vaccine-related hits into KEEP / REWRITE / REPLACE,
emits rewrites + drops + adds, and validates every output via
validate_rewrite(). Writes:
  - _vaccine_patch.json: the operations (find_substring / _drop / _add)
  - _vaccine_audit.md:   classification trail with reasoning

Tight per-tier total budgets (Q + 4 choices):
  T1=294  T2=504  T3=714  T4=945  T5=1155

Stance preamble (project instructions):
  - This is NOT anti-vax. Immune-system mechanism is honored.
  - INSTITUTIONAL behavior is scrutinized — liability shield,
    schedule expansion, VAERS, censorship of dissidents.
  - Distinguish scientific METHOD from institutional CAPTURE.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

# ----------------------------------------------------------------------
# Load data
# ----------------------------------------------------------------------

with open(REPO / "_vaccine_hits.json", encoding="utf-8") as f:
    HITS = json.load(f)

with open(REPO / "data" / "questions" / "science.json", encoding="utf-8") as f:
    BANK = json.load(f)

HITS_BY_IDX = {h["bank_idx"]: h for h in HITS}


# ----------------------------------------------------------------------
# Classification (preserve KEEP defs identical to v1)
# ----------------------------------------------------------------------

CLASSIFY = [
    (212, "KEEP", "Jenner observation milkmaid/cowpox — historical mechanism, not causal claim."),
    (213, "REWRITE", "Phipps 1796 — adds modern-ethics nuance to celebrated 'first vaccine' framing."),
    (214, "KEEP", "Etymology vacca/cow — pure etymology, no PR-template framing."),
    (215, "REWRITE", "Smallpox 1980 — honors event but flags it's used as PR template for all vaccines."),
    (216, "REWRITE", "Salk 1955 — adds Greenberg 1962 definitional-reclassification context."),
    (217, "KEEP", "Salk patent — historical-personal, not vaccine causation."),
    (218, "REPLACE", "Sabin oral on sugar — replace with VAPP-aware framing."),
    (220, "KEEP", "Semmelweis — dissent recognition, not vaccines."),
    (226, "KEEP", "Pasteur germ theory — not vaccines."),
    (227, "KEEP", "Pasteurization — food preservation."),
    (228, "KEEP", "Swan-neck flasks — abiogenesis."),
    (229, "REWRITE", "Pasteur rabies — adds lab-notebook corner-cutting note."),
    (243, "KEEP", "Pasteur disproves spontaneous generation."),
    (248, "KEEP", "FDR's polio — biographical."),

    (341, "KEEP", "Virchow cell theory."),
    (353, "KEEP", "Mendel rediscovery."),
    (360, "KEEP", "Darwin/Wallace."),
    (366, "KEEP", "Swan-neck flasks."),
    (368, "KEEP", "Koch TB 1882."),
    (369, "KEEP", "Pasteurization mechanism."),
    (370, "REWRITE", "Jenner 1796 — flags 'first vaccine' overgeneralization."),
    (371, "KEEP", "Pasteur rabies historical narrative."),
    (372, "REWRITE", "Salk 1955 — adds Greenberg context."),
    (373, "REWRITE", "Salk vs Sabin — adds VAPP context."),
    (374, "REWRITE", "Hilleman — adds SV40 posthumous acknowledgment."),
    (375, "KEEP", "Jeryl Lynn strain."),
    (376, "KEEP", "Semmelweis."),
    (446, "KEEP", "Darwin/Wallace."),
    (452, "KEEP", "Marshall self-experimentation."),
    (467, "REWRITE", "Wakefield retraction — adds broader-conversation legitimacy."),
    (469, "KEEP", "Penicillin / Florey & Chain — not vaccines."),
    (470, "KEEP", "Salk no patent."),
    (471, "REWRITE", "Jenner — adds variolation pre-history."),
    (472, "KEEP", "Swan-neck flasks."),
    (473, "KEEP", "Lister carbolic — not vaccines."),
    (488, "KEEP", "Germ theory transition."),

    (607, "KEEP", "Wallace/Darwin."),
    (613, "KEEP", "Pasteur germ theory."),
    (615, "KEEP", "Pasteur swan-neck."),
    (616, "REWRITE", "Jenner — adds variolation pre-history."),
    (617, "KEEP", "Pasteur post-exposure rabies mechanism."),
    (618, "REWRITE", "Salk vs Sabin IPV/OPV — adds VAPP/cVDPV."),
    (619, "KEEP", "MMR diseases factual."),
    (621, "KEEP", "Semmelweis dissent."),
    (630, "KEEP", "Natural immunity definition — pre-2020 immunology."),
    (633, "KEEP", "Vaccine types factual — mechanism honored."),
    (710, "KEEP", "Darwin/Wallace."),
    (717, "KEEP", "Lister antisepsis."),
    (741, "KEEP", "GBD Oct 2020 — dissent recognition."),
    (742, "KEEP", "Collins 'devastating takedown' — dissent recognition."),
    (743, "KEEP", "Bhattacharya credentials/NIH."),
    (744, "KEEP", "Kulldorff removed from advisory."),
    (754, "KEEP", "1986 NCVIA — honest."),
    (755, "KEEP", "Schedule expansion."),
    (756, "KEEP", "Smallpox last case factual."),
    (757, "KEEP", "Salk no patent."),
    (760, "KEEP", "Swan-neck flasks."),
    (766, "KEEP", "Gain-of-function — institutional critique."),
    (767, "KEEP", "Twitter Files — censorship recognition."),
    (768, "KEEP", "Murthy v Missouri."),
    (769, "KEEP", "VAERS Harvard Pilgrim 2010 — honest."),
    (770, "KEEP", "Wakefield nuance."),

    (826, "KEEP", "Enzymes — biochem."),
    (849, "KEEP", "Pasteur chirality — chemistry."),
    (869, "REWRITE", "Salk + Sabin patent — adds full accounting."),
    (870, "REWRITE", "Hilleman — adds SV40 context."),
    (871, "KEEP", "VAERS Harvard Pilgrim — honest."),
    (889, "REWRITE", "Vaccine memory mechanism — distinguishes proven mechanism from overstated causal claims."),
    (896, "KEEP", "lac operon."),
    (899, "KEEP", "Wakefield broader nuance."),
    (900, "KEEP", "Murthy v Missouri + Twitter Files."),
    (957, "KEEP", "Natural immunity pre-2020."),
    (960, "KEEP", "VAERS under-reporting honest."),
    (968, "KEEP", "Gain-of-function pause honest."),
    (972, "KEEP", "GBD credentials honest."),
    (974, "KEEP", "Bhattacharya vindication."),
    (975, "KEEP", "Stanford harassment of Bhattacharya."),
    (976, "KEEP", "Focused protection was conventional."),
    (977, "KEEP", "1986 NCVIA structural critique."),
    (978, "KEEP", "Schedule expansion 11→70."),
    (979, "KEEP", "VICP $5B+ payouts."),
    (980, "KEEP", "RFK Jr. actual position."),
    (996, "KEEP", "Autism rate rise + researchers labeled."),
    (997, "KEEP", "Peer review fraud cases."),
    (1001, "KEEP", "Dissent pattern Galileo/Semmelweis/Marshall/Bhattacharya."),
    (1003, "KEEP", "Malone deplatforming."),
    (1004, "KEEP", "Kory/Marik institutional response."),
    (1020, "KEEP", "Karikó/Weissman mRNA Nobel."),

    (1093, "KEEP", "Homochirality — chemistry."),
    (1104, "KEEP", "Thalidomide — drug safety."),
    (1117, "KEEP", "VAERS Harvard Pilgrim honest."),
    (1118, "KEEP", "Schedule expansion + gap honest."),
    (1119, "KEEP", "Wakefield balanced framing."),
    (1120, "KEEP", "RFK Jr. position honest."),
    (1121, "KEEP", "GBD + Collins emails + Bhattacharya NIH."),
    (1123, "KEEP", "Kulldorff outbreak detection method."),
    (1124, "KEEP", "McCullough ABIM action."),
    (1125, "KEEP", "Smallpox eradication — already honest."),
    (1127, "KEEP", "Semmelweis rejection."),
    (1128, "KEEP", "Margulis endosymbiosis."),
    (1132, "KEEP", "Humoral theory overturn."),
    (1234, "KEEP", "Henrietta Lacks dual recognition."),
    (1242, "KEEP", "Twitter Files COVID moderation."),
    (1243, "KEEP", "Aaron Siri Pfizer FOIA 75-year — explicit ask."),
    (1244, "KEEP", "GBD Collins emails + Bhattacharya."),
    (1246, "KEEP", "Malone Twitter."),
    (1247, "KEEP", "Kory/Marik hospital privileges."),
    (1248, "KEEP", "RFK Jr. Real Anthony Fauci sources."),
    (1254, "KEEP", "Gain-of-function structural."),
    (1260, "KEEP", "Kulldorff Mass General Brigham."),
    (1262, "KEEP", "McCullough AJM 2020."),
    (1269, "KEEP", "CHD deplatforming."),
    (1270, "KEEP", "Aaron Siri FOIA litigation."),
    (1274, "KEEP", "ACIP conflicts of interest."),
    (1285, "KEEP", "Wakefield + institutional response."),
]

classified_idx = {row[0] for row in CLASSIFY}
hit_idx = {h["bank_idx"] for h in HITS}
missing = hit_idx - classified_idx
extra = classified_idx - hit_idx
assert not missing, f"Unclassified hits: {sorted(missing)}"
assert not extra, f"Extra classifications: {sorted(extra)}"


# ----------------------------------------------------------------------
# REWRITES — tighter, em-dash everywhere, fit budget
# Choice-shape parity rule: ALL choices have em-dash OR NONE.
# I use ALL-em-dash since each choice naturally has the "X — Y" form.
# ----------------------------------------------------------------------

REWRITES: dict[int, dict] = {}

# bank_idx 213 — T1 cap 294 — Phipps 1796 ethics nuance
REWRITES[213] = {
    "tier": 1,
    "question": "Jenner gave 8-year-old Phipps cowpox in 1796, then exposed him to smallpox. By today's rules?",
    "answer": "No board — would approve such a trial today",
    "choices": [
        "No board — would approve such a trial today",
        "Routine — every hospital runs it yearly",
        "Retracted — Phipps died, the paper was pulled",
        "Approved — Jenner met every 1796 FDA rule",
    ],
    "context": "Phipps survived; the cowpox observation was real biology. The story is honored AND the modern Nuremberg Code (1947) would not allow deliberately exposing a healthy child to smallpox today."
}

# bank_idx 215 — T1 — Smallpox 1980 with PR-template caveat
REWRITES[215] = {
    "tier": 1,
    "question": "In 1980 the WHO declared smallpox eradicated. What's the catch when this one win is used as the model for ALL vaccines?",
    "answer": "ONE — smallpox is the only one ever eradicated",
    "choices": [
        "ONE — smallpox is the only one ever eradicated",
        "ALL — every disease has been eradicated since",
        "FAKE — the WHO made up the whole declaration",
        "REGRET — the WHO plans to undo the call",
    ],
    "context": "Smallpox eradication is real and the vaccine contributed substantially. It's the ONLY human disease ever eradicated. The PR move uses this one case as the template for every later vaccine."
}

# bank_idx 216 — T1 — Salk 1955 with Greenberg context
REWRITES[216] = {
    "tier": 1,
    "question": "Right after Salk's 1955 polio vaccine, the way US doctors COUNTED polio cases changed. How?",
    "answer": "Stricter — fewer paralysis cases counted as polio",
    "choices": [
        "Stricter — fewer paralysis cases counted as polio",
        "Looser — far more cases now counted as polio",
        "Stopped — the US no longer tracked polio at all",
        "Renamed — every polio case was added to measles",
    ],
    "context": "UNC biostatistician Bernard Greenberg testified to Congress in 1962 that post-1955 paralytic polio required 60-day persistent paralysis; aseptic meningitis, Coxsackievirus, echovirus and Guillain-Barre were reclassified out. The drop is partly real, partly accounting."
}

# bank_idx 229 — T1 — Pasteur rabies + lab notebook
REWRITES[229] = {
    "tier": 1,
    "question": "Pasteur saved Joseph Meister with his 1885 rabies vaccine. What did Pasteur's private notebooks later reveal?",
    "answer": "Cut corners — methods his papers had hidden",
    "choices": [
        "Cut corners — methods his papers had hidden",
        "Never happened — Meister died as a baby",
        "Used cowpox — not rabies — in the shot",
        "Won a Nobel — for chemistry that year",
    ],
    "context": "Pasteur's notebooks (released 1971; studied by Gerald Geison) showed Meister got a different version from what Pasteur said publicly. Meister survived and lived to 64. Even celebrated heroes cut corners modern peer review would catch."
}

# bank_idx 218 — T1 — Sabin oral with VAPP (REPLACE)
REWRITES[218] = {
    "tier": 1,
    "question": "Sabin's 1961 polio vaccine used LIVE weakened virus on a sugar cube. What did the ads not mention?",
    "answer": "Reverts — the live virus can mutate back to paralysis",
    "choices": [
        "Reverts — the live virus can mutate back to paralysis",
        "Sweet — the sugar cube was the real cure all along",
        "Growth — kids on it grew quickly for two years",
        "Two cures — it cured polio and the common cold",
    ],
    "context": "VAPP (vaccine-associated paralytic polio) is rare but real — the live virus reverts. Circulating vaccine-derived polio (cVDPV) outbreaks in undervaccinated populations have in some years exceeded wild polio. The US switched to IPV in 2000 partly for this."
}

# bank_idx 370 — T2 — Jenner 'first vaccine' overgeneralization
REWRITES[370] = {
    "tier": 2,
    "question": "Edward Jenner's 1796 cowpox-for-smallpox experiment gets called 'the first vaccine.' What's the catch in treating it as the template for ALL later vaccines?",
    "answer": "Cowpox vs smallpox is a SPECIAL biological case — not the universal template",
    "choices": [
        "Cowpox vs smallpox is a SPECIAL biological case — not the universal template",
        "Jenner never did the experiment — the whole story was fabricated",
        "Phipps caught smallpox and died — modern schools suppress the story",
        "Cowpox and smallpox are unrelated — the experiment proved nothing",
    ],
    "context": "Cowpox and smallpox are closely related orthopoxviruses — cross-protection between them is a genuine and unusual biological fact. Most later vaccines train adaptive immunity for the same pathogen via attenuated/killed/subunit antigen exposure. The mechanism of immune training is real; the universal-template framing overstates what one observation supports."
}

# bank_idx 372 — T2 — Salk 1955 + Greenberg
REWRITES[372] = {
    "tier": 2,
    "question": "In April 1955 Jonas Salk's polio vaccine was announced safe and effective. UNC biostatistician Bernard Greenberg testified to Congress in 1962 about what?",
    "answer": "Definitional reclassification — case-counting changed after 1955 beyond the vaccine effect",
    "choices": [
        "Definitional reclassification — case-counting changed after 1955 beyond the vaccine effect",
        "Vaccine had no effect at all — every count change is PR fabrication",
        "Polio is identical to influenza — never a separate disease",
        "Vaccine should be celebrated — and no testimony ever happened",
    ],
    "context": "Salk's vaccine reduced paralytic polio — that's real. Greenberg's 1962 testimony documented that post-1955 the case definition required 60-day persistent paralysis and reclassified aseptic meningitis, Coxsackievirus, echovirus, and Guillain-Barre OUT of the polio count. Both pieces belong in honest history."
}

# bank_idx 373 — T2 — Salk vs Sabin + VAPP
REWRITES[373] = {
    "tier": 2,
    "question": "Salk's polio vaccine (1955) used killed virus by injection. Sabin's later vaccine (1961) used LIVE attenuated virus by mouth. The trade-off of the live version is what?",
    "answer": "VAPP — rare reversion to a paralyzing form, vaccine-associated paralytic polio",
    "choices": [
        "VAPP — rare reversion to a paralyzing form, vaccine-associated paralytic polio",
        "Cure-all — Sabin's vaccine treats polio and the common cold together",
        "Inert — Sabin's formulation has no biological effect on the immune system",
        "Allergy — every Sabin recipient develops lifelong milk intolerance",
    ],
    "context": "Sabin's OPV was cheaper, easier to give in mass campaigns, and gave intestinal immunity Salk's didn't. The trade-off: VAPP, where the weakened virus reverts to virulence. Circulating vaccine-derived polio (cVDPV) outbreaks in undervaccinated populations have in some years exceeded wild polio. WHO is shifting toward IPV."
}

# bank_idx 374 — T2 — Hilleman + SV40
REWRITES[374] = {
    "tier": 2,
    "question": "Maurice Hilleman developed about 40 vaccines at Merck. In an interview taped before his 2005 death (released publicly in 2007), he acknowledged what?",
    "answer": "SV40 — polio vaccines 1955-1963 carried a monkey virus, about 100M Americans exposed",
    "choices": [
        "SV40 — polio vaccines 1955-1963 carried a monkey virus, about 100M Americans exposed",
        "Fabrication — he never actually developed any vaccine at Merck",
        "Mass swap — all 40 of his vaccines were placebo with no biology",
        "AIDS origin — he invented HIV in a 1978 hepatitis vaccine batch",
    ],
    "context": "Hilleman's vaccines saved lives — that's real. The taped interview (surfaced in the 2007 documentary 'In Lies We Trust') had Hilleman acknowledging that polio vaccines made in rhesus monkey kidney cells 1955-1963 carried simian virus 40 (SV40); about 100 million Americans were exposed. See Bookchin and Schumacher, 'The Virus and the Vaccine' (2004)."
}

# bank_idx 467 — T2 — Wakefield retraction + broader legitimacy
REWRITES[467] = {
    "tier": 2,
    "question": "Andrew Wakefield's 1998 Lancet MMR-autism paper was partially retracted in 2004 and fully retracted in 2010. What's the more accurate accounting beyond 'fraud, case closed'?",
    "answer": "Real methodology problems — AND broader vaccine-safety questions remain legitimate independent of his case",
    "choices": [
        "Real methodology problems — AND broader vaccine-safety questions remain legitimate independent of his case",
        "Wakefield right on everything — paper now the gold standard for safety",
        "Identical to other papers — the retraction was routine procedure",
        "No safety conversation exists — and the Wakefield episode never occurred",
    ],
    "context": "Brian Deer's investigation (Sunday Times then BMJ 2011) documented patient-selection problems and undisclosed conflicts. The MMR-autism causal claim doesn't hold up in larger studies. Separately, Wakefield's GI observations have been replicated independently. The retraction is used as a discussion-ender to dismiss subsequent credentialed vaccine-safety inquiry; that's a separable move."
}

# bank_idx 471 — T2 — Jenner + variolation pre-history
REWRITES[471] = {
    "tier": 2,
    "question": "Edward Jenner's 1796 cowpox experiment gets called 'the first vaccine.' What's the older worldwide history the label buries?",
    "answer": "Variolation — mild smallpox itself was used in China, Africa, India, Ottoman Turkey for centuries",
    "choices": [
        "Variolation — mild smallpox itself was used in China, Africa, India, Ottoman Turkey for centuries",
        "Universal first — Jenner was the very first human to think about disease prevention",
        "Disease was unknown — Jenner discovered smallpox itself in 1796",
        "All vaccines must use cowpox — Jenner's exact technique is unchanged today",
    ],
    "context": "Variolation (deliberately exposing healthy people to mild smallpox material) was widely practiced in China by the 16th century, in West Africa, India, and Ottoman Turkey before reaching Britain in 1721 via Lady Mary Wortley Montagu. Jenner's cowpox version was safer. The 'first vaccine' label hides both the older non-European tradition and the special-case nature of cowpox-for-smallpox."
}

# bank_idx 616 — T3 — Jenner + variolation
REWRITES[616] = {
    "tier": 3,
    "question": "Edward Jenner inoculated 8-year-old James Phipps with cowpox in 1796, then exposed him to smallpox. He coined 'vaccination' from Latin 'vacca' (cow). What's the older tradition the 'first vaccine' label tends to bury?",
    "answer": "Variolation — using mild smallpox itself, practiced for centuries in China, India, Africa, and Ottoman Turkey before reaching Britain in 1721",
    "choices": [
        "Variolation — using mild smallpox itself, practiced for centuries in China, India, Africa, and Ottoman Turkey before reaching Britain in 1721",
        "Egyptian vaccines — used in ancient Egypt and rediscovered by Jenner after thousands of years lost to history",
        "Roman horsepox program — a national vaccine program Jenner copied directly in 1796 without acknowledgment",
        "Bacterial flu shots — used widely in 1500s Germany, renamed by Jenner to take the credit",
    ],
    "context": "Variolation was real and well-documented in 16th-century China, West Africa, India, and Ottoman Turkey. Lady Mary Wortley Montagu brought it from Constantinople to Britain in 1721. Jenner's cowpox version was safer than variolating with actual smallpox. The 'first vaccine' label hides both the older tradition AND the special-case biology of cowpox-for-smallpox cross-protection."
}

# bank_idx 618 — T3 — Salk/Sabin IPV/OPV + VAPP/cVDPV
REWRITES[618] = {
    "tier": 3,
    "question": "Salk's inactivated polio vaccine (IPV, 1955) is given by injection. Sabin's oral polio vaccine (OPV, 1962) used live attenuated virus on a sugar cube. The US switched back to IPV-only in 2000. What drove the switch?",
    "answer": "VAPP and cVDPV — live attenuated virus reverts to virulence, and circulating vaccine-derived polio exceeds wild polio in some years",
    "choices": [
        "VAPP and cVDPV — live attenuated virus reverts to virulence, and circulating vaccine-derived polio exceeds wild polio in some years",
        "Pure cost-cutting — the CDC switched because IPV was cheaper, never mind the disease itself",
        "Both withdrawn — the US has used no polio vaccine of any kind since 1995 anywhere",
        "Sabin retracted — his vaccine was sugar alone, with no biological component at all",
    ],
    "context": "OPV was cheaper and gave intestinal immunity IPV didn't — that's why it was preferred for global campaigns. The trade-off: VAPP (vaccine-associated paralytic polio) is rare but real, and circulating vaccine-derived polio (cVDPV) outbreaks in undervaccinated populations have in some years exceeded wild polio. The 2000 US switch back to IPV-only reflects honest accounting of that risk."
}

# bank_idx 869 — T4 — Salk + Sabin full accounting
REWRITES[869] = {
    "tier": 4,
    "question": "Jonas Salk's polio vaccine (1955) was a real achievement; Salk refused to patent it, telling Ed Murrow 'could you patent the sun?' What does honest accounting alongside that personal generosity require?",
    "answer": "Acknowledging Cutter 1955, SV40 contamination 1955-1963, Greenberg's 1962 definitional reclassification, and VAPP — alongside the real reduction in paralytic cases",
    "choices": [
        "Acknowledging Cutter 1955, SV40 contamination 1955-1963, Greenberg's 1962 definitional reclassification, and VAPP — alongside the real reduction in paralytic cases",
        "Treating the 1955 announcement as having closed every subsequent question — with no complications worth a kid knowing about during any of their formal schooling",
        "Concluding that polio never existed — and the 20th-century epidemic was a PR fabrication invented to sell a vaccine that did absolutely nothing for paralytic disease",
        "Patenting all subsequent vaccines for maximum profit — exactly the opposite of what Salk personally did with his polio vaccine after the 1955 trial announcement",
    ],
    "context": "Cutter Labs' 1955 Salk vaccine was inadequately inactivated; approximately 200 children paralyzed and 10 died (Paul Offit, 'The Cutter Incident,' 2005). SV40 contamination 1955-1963 (Bookchin and Schumacher 2004) was acknowledged on tape by Hilleman before his 2005 death. UNC biostatistician Bernard Greenberg's 1962 Congressional testimony documented post-1955 case-definition narrowing. VAPP/cVDPV from Sabin's oral vaccine are documented and ongoing. Honor Salk's act AND the full story."
}

# bank_idx 870 — T4 — Hilleman + SV40 acknowledgment
REWRITES[870] = {
    "tier": 4,
    "question": "Maurice Hilleman (1919-2005) developed about 40 vaccines at Merck — including MMR, hep A and B, varicella. In a videotaped interview surfaced shortly before his death, he acknowledged something public messaging had hidden. What?",
    "answer": "Salk and Sabin polio vaccines 1955-1963 had been contaminated with SV40 from rhesus monkey kidney cell culture — about 100 million Americans were exposed",
    "choices": [
        "Salk and Sabin polio vaccines 1955-1963 had been contaminated with SV40 from rhesus monkey kidney cell culture — about 100 million Americans were exposed",
        "He had never developed any vaccine — his entire Merck career had been a public-relations fabrication invented to sell unrelated pharmaceutical products to consumers",
        "All forty Merck vaccines were perfectly identical — repackaged versions of Jenner's 1796 cowpox technique with no biological variation across the pathogens involved",
        "He personally invented HIV in 1978 — and the AIDS epidemic traces directly to a single contaminated batch of his hepatitis vaccine from that year",
    ],
    "context": "Hilleman's career produced vaccines that have saved lives — real achievement. The taped interview surfaced in the 2007 documentary 'In Lies We Trust' had Hilleman acknowledging that polio vaccines made in rhesus monkey kidney cells 1955-1963 carried simian virus 40 (SV40) contamination, and that approximately 100 million Americans were exposed. CDC has acknowledged the contamination while disputing the cancer link (mesothelioma, brain tumors). See Bookchin and Schumacher, 'The Virus and the Vaccine' (2004)."
}

# bank_idx 889 — T4 — vaccine memory mechanism + recognition skill
REWRITES[889] = {
    "tier": 4,
    "question": "Vaccines train the immune system via attenuated/killed/subunit antigen exposure — memory B and T cells then respond fast on real infection. The mechanism is proven cell biology. What's the recognition skill BEYOND naming the mechanism?",
    "answer": "Distinguish mechanism — adaptive immunity is real — from overstated causal claims like 'vaccine eliminated polio' that compress reclassification, sanitation, and other factors",
    "choices": [
        "Distinguish mechanism — adaptive immunity is real — from overstated causal claims like 'vaccine eliminated polio' that compress reclassification, sanitation, and other factors",
        "Memorize the slogan — 'TRUST THE SCIENCE' substitutes appeal-to-authority for the placebo-controlled trials dissident researchers ask institutions to produce",
        "Accept identical — vaccine development is 200 years of applying Jenner's exact cowpox method with no biological variation across the many pathogens",
        "Reject the mechanism — dismiss adaptive immunity as pharmaceutical-industry PR with no underlying scientific basis at any level whatsoever",
    ],
    "context": "Adaptive immunity is proven cell biology: antigen exposure trains memory B cells (antibody production) and T cells (cellular response) so the system responds faster on re-exposure. The mechanism is honored. The recognition skill is distinguishing proven mechanism from causal claims about specific outcomes — Greenberg's 1962 polio definitional change, sanitation, the sanitation paradox — that have layered together."
}


# ----------------------------------------------------------------------
# NEW QUESTIONS (additive) — tight to budget, em-dash all choices
# ----------------------------------------------------------------------

NEW_QUESTIONS: list[dict] = []

# --- T1 (5) cap=294 ---
NEW_QUESTIONS.append({
    "tier": 1,
    "question": "In April 1955 Cutter Labs put out Salk polio vaccine that wasn't fully killed. What happened?",
    "answer": "200 paralyzed — 10 died, the Cutter Incident",
    "choices": [
        "200 paralyzed — 10 died, the Cutter Incident",
        "Cured polio — in one shot, Cutter got an award",
        "Cutter ran out — gave kids sugar water instead",
        "Cutter tried milk — kids said it tasted bad",
    ],
    "context": "The Cutter Incident (April-May 1955) is documented in Paul Offit's 'The Cutter Incident' (2005). Cutter Labs' batches of the Salk vaccine were not fully inactivated. About 200 paralyzed, 10 died, ~40,000 had abortive polio."
})

NEW_QUESTIONS.append({
    "tier": 1,
    "question": "Polio vaccines 1955-1963 grew in monkey kidney cells. A virus called SV40 came along. How many Americans got exposed?",
    "answer": "~100 million — Hilleman confirmed it on tape",
    "choices": [
        "~100 million — Hilleman confirmed it on tape",
        "About a dozen — Pasteur Institute lab workers",
        "Exactly zero — the cells were never used",
        "Maybe fifty — French chemistry students",
    ],
    "context": "SV40 contaminated polio vaccines made in rhesus monkey kidney cell culture 1955-1963. About 100M Americans exposed. Bookchin and Schumacher, 'The Virus and the Vaccine' (2004). Hilleman acknowledged it on tape, released after his 2005 death."
})

NEW_QUESTIONS.append({
    "tier": 1,
    "question": "VAERS is the US system where doctors report possible vaccine side effects. A 2010 Harvard Pilgrim study found what?",
    "answer": "Under 1% — of events ever get reported to VAERS",
    "choices": [
        "Under 1% — of events ever get reported to VAERS",
        "Over 100 — reports per actual adverse event",
        "Full 100% — VAERS captures every reaction",
        "Each report — judged by a federal panel first",
    ],
    "context": "Harvard Pilgrim Health Care study (Lazarus et al., 2010, AHRQ Grant R18 HS 017045) estimated fewer than 1% of vaccine adverse events reach VAERS. The system is voluntary and passive. The follow-on electronic-reporting project was not implemented."
})

NEW_QUESTIONS.append({
    "tier": 1,
    "question": "In 1986 Congress passed NCVIA. What did it do to how vaccine makers can be sued?",
    "answer": "Shielded — child-injury suits go to federal court",
    "choices": [
        "Shielded — child-injury suits go to federal court",
        "Opened up — unlimited lawsuits in every state",
        "Banned — every vaccine pulled from market 5 years",
        "Forced — makers had to publish secret formulas",
    ],
    "context": "The National Childhood Vaccine Injury Act of 1986 routed most childhood vaccine injury claims through the no-fault VICP, funded by a 75-cent-per-dose tax. Cumulative payouts exceed $5 billion. Critics including attorney Aaron Siri and RFK Jr. argue the shield removes ordinary market discipline."
})

NEW_QUESTIONS.append({
    "tier": 1,
    "question": "Aaron Siri sued the FDA for Pfizer COVID vaccine safety papers. How long did FDA ask the court to take?",
    "answer": "75 years — Judge Pittman called it 'unreasonable'",
    "choices": [
        "75 years — Judge Pittman called it 'unreasonable'",
        "75 days — judge agreed and FDA met it",
        "Two weeks — FDA finished and got an award",
        "Six months — the standard FOIA timeline",
    ],
    "context": "Public Health and Medical Professionals for Transparency v. FDA (N.D. Tex. 2022). Aaron Siri's PHMPT filed a 2021 FOIA request for ~450,000 pages. FDA proposed 500 pages per month — 75 years. Judge Mark Pittman ordered ~55,000 pages per month."
})

# --- T2 (5) cap=504 ---
NEW_QUESTIONS.append({
    "tier": 2,
    "question": "Maurice Hilleman developed about 40 vaccines at Merck. Late in life he sat for an interview released after his 2005 death. What did the tape reveal that public messaging hadn't?",
    "answer": "SV40 — polio vaccines 1955-1963 carried a monkey virus, about 100 million Americans exposed",
    "choices": [
        "SV40 — polio vaccines 1955-1963 carried a monkey virus, about 100 million Americans exposed",
        "Fabrication — he never developed any vaccine and his Merck career was invented",
        "Identical mass — all 40 vaccines were placebo with no biological effect",
        "AIDS origin — he invented HIV in a 1978 hepatitis vaccine batch",
    ],
    "context": "Hilleman's vaccines saved lives — real history. The taped interview surfaced in the 2007 documentary 'In Lies We Trust' had Hilleman acknowledging polio vaccines made in rhesus monkey kidney cells 1955-1963 carried SV40, and that about 100 million Americans were exposed. CDC acknowledges contamination; cancer link disputed. See Bookchin and Schumacher (2004)."
})

NEW_QUESTIONS.append({
    "tier": 2,
    "question": "Forrest Maready's 2018 book 'The Moth in the Iron Lung' presents a major correlation that mainstream polio history misses. What's the correlation?",
    "answer": "Paralysis counts — tracked DDT and lead-arsenate pesticide spraying timing closely",
    "choices": [
        "Paralysis counts — tracked DDT and lead-arsenate pesticide spraying timing closely",
        "Polio was influenza — and was never a separate viral disease at all",
        "Cause was wiring — household electrical wiring caused all 1950s paralysis",
        "Vaccine cured colds — and that's why polio counts dropped post-1955",
    ],
    "context": "Maready, 'The Moth in the Iron Lung' (2018), documents temporal correlation between DDT and lead-arsenate pesticide spraying and paralytic case counts. The public-health establishment rejects the causal claim; the data is real and reproducible from public records. The bank covers this as a serious contested hypothesis, not woo — the correlation deserves engagement."
})

NEW_QUESTIONS.append({
    "tier": 2,
    "question": "Polio was a 20th-century epidemic. Before about 1890 it was rare and mild. Mainstream epidemiology acknowledges a paradox about its emergence. What is it?",
    "answer": "Sanitation paradox — polio emerged AS sanitation improved, delaying first infection to a more vulnerable age",
    "choices": [
        "Sanitation paradox — polio emerged AS sanitation improved, delaying first infection to a more vulnerable age",
        "Sanitation made it worse — dirty conditions directly caused polio to spread widely",
        "Always same level — the 20th-century rise is a statistical fabrication of 1955",
        "Polio was chickenpox — and the separate disease was invented by drug companies",
    ],
    "context": "Pre-sanitation, infants encountered poliovirus while still carrying maternal antibodies and got mild or asymptomatic infection with lifelong protection. As sanitation improved, first infection shifted to older children whose maternal protection was gone — producing more severe paralytic disease. The mainstream sanitation-paradox acknowledgment sits alongside the standard 'vaccine eliminated polio' framing."
})

NEW_QUESTIONS.append({
    "tier": 2,
    "question": "Iron-lung images became powerful symbols of polio in the 1940s-50s — used heavily in vaccine-campaign messaging. What's the data on how often paralytic polio actually needed an iron lung?",
    "answer": "Only 0.5-1% — of paralytic polio cases needed respiratory support",
    "choices": [
        "Only 0.5-1% — of paralytic polio cases needed respiratory support",
        "Roughly 90% — every infected child went on an iron lung for a year",
        "All cases needed — permanent iron-lung confinement with no other option",
        "Never used at all — photos were fabricated for the 1955 vaccine launch",
    ],
    "context": "Iron lungs (negative-pressure ventilators) were real and used for the small subset of paralytic polio cases involving bulbar paralysis — roughly 0.5 to 1 percent of paralytic cases. March of Dimes and other campaigns highlighted the most severe presentation. The imagery and the proportion are both documented; honor real disease AND iconography that ran ahead of the typical case."
})

NEW_QUESTIONS.append({
    "tier": 2,
    "question": "Sabin's oral polio vaccine uses LIVE attenuated virus. In some countries, in some recent years, what's been documented about virus circulating from vaccinated kids?",
    "answer": "cVDPV — vaccine-derived polio outbreaks have exceeded wild polio in some years",
    "choices": [
        "cVDPV — vaccine-derived polio outbreaks have exceeded wild polio in some years",
        "Total vanish — the live virus never produces any further infection at all",
        "Cures colds — the live virus is now used to treat the common cold worldwide",
        "Killed only — Sabin's vaccine never contained any live virus at any time",
    ],
    "context": "Circulating vaccine-derived poliovirus (cVDPV) is documented in WHO surveillance reports. The live virus shed by vaccinated kids can mutate back to virulence in undervaccinated populations and cause new paralytic cases. In some recent years cVDPV cases exceeded wild polio. WHO has been transitioning toward IPV. US switched to IPV-only in 2000."
})

# --- T3 (5) cap=714 ---
NEW_QUESTIONS.append({
    "tier": 3,
    "question": "UNC biostatistician Bernard Greenberg testified to a 1962 Congressional committee about how US doctors had been counting paralytic polio cases. What changed in 1955 that affected the count?",
    "answer": "Case definition tightened — 60-day persistent paralysis required, and aseptic meningitis, Coxsackievirus, echovirus, and Guillain-Barre were reclassified out",
    "choices": [
        "Case definition tightened — 60-day persistent paralysis required, and aseptic meningitis, Coxsackievirus, echovirus, and Guillain-Barre were reclassified out",
        "Definition loosened — any sore arm now counted as a polio case for political reasons in every state",
        "Counting stopped — the US stopped tracking polio entirely in 1955 with no surveillance since then",
        "Renamed measles — every polio case was added to the federal measles total without documentation",
    ],
    "context": "Greenberg's 1962 Intensive Immunization Programs hearings testimony documented post-1955 narrowing of the paralytic-polio case definition. Required persistent paralysis was extended from 24 hours to 60 days. Aseptic meningitis, Coxsackievirus, echovirus, and Guillain-Barre were reclassified out. The drop in 'polio' after 1955 partly reflects a real Salk effect AND partly the new accounting."
})

NEW_QUESTIONS.append({
    "tier": 3,
    "question": "Robert Malone helped pioneer the lipid-nanoparticle mRNA delivery technology in the late 1980s. On December 29, 2021 he was banned from Twitter for COVID-related posts. What's the structural recognition?",
    "answer": "Credentialed expertise — was not a shield against deplatforming when views ran against official messaging",
    "choices": [
        "Credentialed expertise — was not a shield against deplatforming when views ran against official messaging",
        "Only uncredentialed banned — Twitter only suspended people without any medical training, with no exceptions",
        "No mRNA connection — Malone had never had any connection to mRNA technology in any way",
        "Independent review — Twitter consulted outside reviewers for every individual suspension decision",
    ],
    "context": "Malone holds early lipid-nanoparticle mRNA-delivery patents from his 1989-91 work. His Twitter ban (December 29, 2021) followed an appearance on Joe Rogan's podcast. His specific factual claims were a mix of well-supported, contested, and probably wrong — like most public-figure commentary in a crisis. The point: the institutional response was deplatforming rather than engagement, and credentialed expertise didn't protect him."
})

NEW_QUESTIONS.append({
    "tier": 3,
    "question": "Children's Health Defense, founded by RFK Jr. in 2018, is a major organization litigating vaccine policy. Facebook and Instagram deplatformed it in 2022. What's the recognition?",
    "answer": "Platform exclusion — during active phases of policy debate is itself a speech-control mechanism, distinct from any specific group's merits",
    "choices": [
        "Platform exclusion — during active phases of policy debate is itself a speech-control mechanism, distinct from any specific group's merits",
        "Required hosting — platforms are legally required to host every advocacy group and CHD was reinstated within days of the action",
        "No effect at all — platforms have no impact on any organization's reach because alternative channels remain fully open",
        "Identical standards — platforms apply the same standards to every advocacy group on every contested issue at all times",
    ],
    "context": "CHD deplatforming preceded Bhattacharya's NIH confirmation by about three years. The pediatric mRNA vaccine debate was active during the deplatforming period. Whether one agrees with CHD's specific positions, the documented pattern — major-platform exclusion during active phases of contested policy debate — is one mechanism by which speech-control infrastructure shapes political outcomes. Murthy v Missouri (2024) reached the Supreme Court on related state-action questions."
})

NEW_QUESTIONS.append({
    "tier": 3,
    "question": "The cultural slogan 'TRUST THE SCIENCE' rose to prominence in the COVID era. What's the difference between the slogan and the actual scientific virtues it claims to invoke?",
    "answer": "Real virtues — open inquiry, falsifiability, transparent data, dissent-tolerance — substituted with appeal-to-authority by the slogan",
    "choices": [
        "Real virtues — open inquiry, falsifiability, transparent data, dissent-tolerance — substituted with appeal-to-authority by the slogan",
        "Slogan and virtues identical — using 'TRUST THE SCIENCE' has always been equivalent to practicing rigorous open inquiry everywhere",
        "Ignore all dissent — real scientific virtue requires ignoring criticism, and the slogan correctly captures that principle",
        "Method has no virtues — 'TRUST THE SCIENCE' itself is the entire content of scientific method as Popper understood it",
    ],
    "context": "Open inquiry, falsifiability (Popper), transparent data, replicability, and tolerance of dissent are the actual virtues of scientific method. 'TRUST THE SCIENCE' as deployed during COVID functioned as appeal-to-authority and discussion-ender, especially against credentialed dissenters like Bhattacharya, Kulldorff, Malone, McCullough, and Kory. The slogan and the virtues point in opposite directions: real virtue invites questions; the slogan shuts them down."
})

NEW_QUESTIONS.append({
    "tier": 3,
    "question": "Aaron Siri's firm Siri & Glimstad litigated the 2022 Pfizer FOIA case against the FDA. The agency requested 75 years to release the documents; Judge Mark Pittman ordered them released in 8 months. What does the case illustrate?",
    "answer": "Transparency requires litigation — agencies prefer secrecy, and FOIA's promise depends on persistent attorneys willing to enforce it",
    "choices": [
        "Transparency requires litigation — agencies prefer secrecy, and FOIA's promise depends on persistent attorneys willing to enforce it",
        "Automatic release — federal agencies release every safety record without any legal pressure required from outside parties",
        "Banned disclosure — federal agencies are legally prohibited from releasing safety records under any circumstances",
        "Always lose fast — federal agencies always lose FOIA cases quickly with no litigation needed for any disclosure",
    ],
    "context": "Public Health and Medical Professionals for Transparency v. FDA (N.D. Tex. 2022). The released Pfizer trial documents, V-safe data, and VAERS records — much of the most useful public safety information on COVID vaccines came from FOIA litigation. The structural recognition: 'transparency by default' is rarely how agencies behave; transparency happens when courts order it and lawyers persist."
})

# --- T4 (4) cap=945 ---
NEW_QUESTIONS.append({
    "tier": 4,
    "question": "The 1986 NCVIA shielded vaccine manufacturers from most lawsuits over childhood vaccine injuries, routing claims through VICP. What's the structural critique attorney Aaron Siri and others have made?",
    "answer": "Liability is market discipline — removing ordinary tort exposure from vaccines changes manufacturer incentives in ways no clinical trial result shows",
    "choices": [
        "Liability is market discipline — removing ordinary tort exposure from vaccines changes manufacturer incentives in ways no clinical trial result shows",
        "No critique exists — the 1986 framework has been universally endorsed by every credentialed researcher in the US since its passage in 1986",
        "Act was repealed in 2010 — by a unanimous Congressional vote, leaving no liability shield for any pharmaceutical manufacturer anywhere",
        "Children only — the critique applies only to childhood vaccines, and adult vaccines remain fully subject to ordinary tort law in every state",
    ],
    "context": "Cumulative VICP payouts exceed $5 billion since 1988, funded by a 75-cent-per-dose excise tax. Pre-1986 vaccine product-liability suits were threatening US manufacturer participation — a real public-health concern that motivated NCVIA. The structural consequence remains: vaccine manufacturer liability exposure differs from every other drug-maker's. Tort liability is a quiet but powerful market discipline; removing it leaves quality assurance to regulatory review alone."
})

NEW_QUESTIONS.append({
    "tier": 4,
    "question": "The CDC childhood vaccine schedule held about 11 doses by age 6 in 1986. By 2024 it holds roughly 70+ doses by age 18 across about 16 vaccines. What's the methodological gap Bhattacharya, Kulldorff, and RFK Jr. have named?",
    "answer": "No combined-schedule trial — each vaccine is tested separately, leaving cumulative interaction effects unstudied at schedule level",
    "choices": [
        "No combined-schedule trial — each vaccine is tested separately, leaving cumulative interaction effects unstudied at schedule level",
        "Trial done fifty times — the full combined schedule has been tested in over fifty placebo-controlled randomized trials with no effects observed",
        "Schedule unchanged — the modern 2024 schedule has exactly the same vaccines as the 1986 schedule with no additions of any kind",
        "Trials are illegal — no country anywhere has legal authority to conduct a combined-schedule trial for any reason at any time",
    ],
    "context": "Each individual vaccine has typically been tested before licensing — that's real. The question of cumulative interaction across the full schedule is less well-studied. A randomized placebo-controlled trial of the full schedule would be considered unethical (withholding vaccines). Observational studies face confounding. The methodological gap is structural and acknowledged by careful researchers; whether you draw safety conclusions from it depends on broader epistemic moves."
})

NEW_QUESTIONS.append({
    "tier": 4,
    "question": "Aluminum adjuvants are added to many non-live vaccines to enhance immune response. They've been used since the 1920s. What's the open methodological question critics including RFK Jr. have raised?",
    "answer": "Cumulative-load gap — cumulative aluminum exposure across the full childhood schedule is not studied at schedule level",
    "choices": [
        "Cumulative-load gap — cumulative aluminum exposure across the full childhood schedule is not studied at schedule level",
        "Never used at all — aluminum adjuvants are not in any vaccine, and their inclusion is a 2015 activist fabrication",
        "In every vaccine — aluminum is in literally every modern vaccine with no aluminum-free vaccine produced for any disease",
        "Tested hundred times — cumulative aluminum dose has been tested in over 100 placebo-controlled trials with no effects",
    ],
    "context": "Aluminum salts (aluminum hydroxide, aluminum phosphate) are the most common vaccine adjuvants. Individual-dose safety has been studied. Cumulative aluminum exposure across the full childhood schedule is less well-studied at schedule level. Pharmacokinetics — how injected aluminum distributes, accumulates, and clears — are partly characterized at individual-dose level but with less data at the schedule level. The methodological question is open."
})

NEW_QUESTIONS.append({
    "tier": 4,
    "question": "RFK Jr. founded Children's Health Defense in 2018 and authored 'The Real Anthony Fauci' in 2021. He served as US HHS Secretary from 2025. What's his recurring substantive ask of public-health institutions?",
    "answer": "'Show me the science' — specifically gold-standard double-blind placebo-controlled trials for vaccines on the childhood schedule",
    "choices": [
        "'Show me the science' — specifically gold-standard double-blind placebo-controlled trials for vaccines on the childhood schedule",
        "'Ban all vaccines' — a position he has consistently held in every public speech since the start of his political career in environmental advocacy",
        "'Trust the science' — a position he has held unchanged in every speech of his political career and never modified for any policy reason",
        "'Stop all research' — a position he has advanced in Congressional testimony since the very beginning of his political work in environmental law",
    ],
    "context": "Kennedy's recurring substantive call has been for placebo-controlled safety testing, repeal of the 1986 liability shield, restored informed-consent protections, and independent review of the childhood schedule. He explicitly disclaims the 'anti-vaccine' label, supports the smallpox eradication, and acknowledges individual vaccines while challenging others. The 'anti-vaxxer' slur flattens a substantive policy position into a label to avoid engaging with it."
})

NEW_QUESTIONS.append({
    "tier": 4,
    "question": "Forrest Maready's 2018 book 'The Moth in the Iron Lung' presents temporal correlation between paralysis case counts and pesticide spraying in the 1940s-50s. How should an honest reader of contested scientific hypotheses engage with it?",
    "answer": "Serious contested hypothesis — examine the correlation data, weigh it against the standard story, avoid both reflexive dismissal and uncritical acceptance",
    "choices": [
        "Serious contested hypothesis — examine the correlation data, weigh it against the standard story, avoid both reflexive dismissal and uncritical acceptance",
        "Unquestionable truth — reject every aspect of the standard polio-vaccine causal story without further examination of any data",
        "Fringe nonsense — dismiss without engaging with the actual data Maready presents or any of the historical record of pesticide use",
        "Polio never existed — and the 20th-century epidemic was a public-relations fabrication invented in 1955 with no biological reality",
    ],
    "context": "Maready, 'The Moth in the Iron Lung' (2018), documents temporal correlation between DDT and lead-arsenate spraying and paralytic case counts. The mainstream rejects the causal claim. The correlation data is real and reproducible from public records. The bank covers this as a serious contested hypothesis — neither woo nor settled. The sanitation paradox (polio emerged AS sanitation improved) is a separate mainstream-acknowledged data point pointing in a related direction."
})

# --- T5 (5) cap=1155 ---
NEW_QUESTIONS.append({
    "tier": 5,
    "question": "Bhattacharya, Kulldorff, Malone, McCullough, Kory, Marik, RFK Jr. The 'anti-science' label is used to dismiss them. What's the one trait the label fails to capture?",
    "answer": "Each is credentialed — and their substantive call has been for stronger gold-standard scientific rigor: placebo-controlled trials, transparent data, repealed liability shield, dissent tolerance",
    "choices": [
        "Each is credentialed — and their substantive call has been for stronger gold-standard scientific rigor: placebo-controlled trials, transparent data, repealed liability shield, dissent tolerance",
        "Each is uncredentialed — with no formal scientific training at all, working outside any major academic institution at the time of their pandemic-era statements",
        "Each invented a pathogen — and the institutional pushback they faced was a direct response to public-health threats from their own active research programs",
        "Each has identical politics — and they have always agreed on every specific claim across the entire history of their public engagement with every COVID question",
    ],
    "context": "Bhattacharya: Stanford School of Medicine, MD/PhD, hundreds of papers, now NIH Director. Kulldorff: Harvard biostatistician, invented the spatial scan statistic. Malone: pioneer of lipid-nanoparticle mRNA delivery, 1989-91 patents. McCullough: cardiologist with thousands of citations. Kory: pulmonologist, former associate chief of critical care at UW. Marik: leading sepsis researcher (HAT protocol). Their recurring substantive ask is for gold-standard rigor — the rigor institutions claim to have but substitute PR for."
})

NEW_QUESTIONS.append({
    "tier": 5,
    "question": "The dissident scientists during the COVID era repeatedly called for institutional commitments the public-health establishment was unwilling to make. What were the actual asks?",
    "answer": "Placebo-controlled trials — for vaccines on the schedule, transparent VAERS data, repeal of 1986 liability shield, independent review of the schedule, lifted censorship of credentialed researchers",
    "choices": [
        "Placebo-controlled trials — for vaccines on the schedule, transparent VAERS data, repeal of 1986 liability shield, independent review of the schedule, lifted censorship of credentialed researchers",
        "Ban all vaccines — immediate worldwide ban on every form of vaccination, a position none of the named researchers has actually advocated in any public speech",
        "Mandatory daily shots — for every person on Earth, the opposite of what every credentialed dissident researcher has actually called for in any of their public-facing career work",
        "Shut down research — a position contradicted by the existence of the dissidents' own active research programs and ongoing publications during the pandemic and after",
    ],
    "context": "The recurring ask has been more rigor, not less. RFK Jr.'s 'show me the science.' Bhattacharya's GBD applied conventional pre-COVID public-health science to focused protection. Kulldorff's biostatistical critiques are rigorous. The asks: gold-standard double-blind placebo-controlled trials for the childhood schedule, transparent VAERS data, repeal of the 1986 liability shield, independent ACIP review, lifted censorship. The recognition skill: who in this controversy is actually asking for scientific virtue?"
})

NEW_QUESTIONS.append({
    "tier": 5,
    "question": "The institutional behavior around vaccines during the COVID era — censoring credentialed dissenters, using 'anti-vaxxer' as a slur, treating contested claims as 'misinformation' — has a specific epistemological irony. What's the irony?",
    "answer": "Behaviors were anti-scientific — open inquiry, dissent-tolerance, falsifiability, transparent data are the actual scientific virtues, and institutions violated them while accusing the dissenters of doing so",
    "choices": [
        "Behaviors were anti-scientific — open inquiry, dissent-tolerance, falsifiability, transparent data are the actual scientific virtues, and institutions violated them while accusing the dissenters of doing so",
        "No irony at all — institutions always behaved with maximum scientific virtue and credentialed dissenters always failed to meet foundational standards of open inquiry in every field",
        "Dissenters anti-vaccine — and institutions correctly identified them as opposed to all forms of vaccine technology regardless of any of their actual substantive policy positions",
        "Correct enforcement — institutions correctly enforced scientific consensus, and credentialed dissenters operated outside legitimate boundaries of every established scientific institution",
    ],
    "context": "Scientific method is open inquiry, falsifiability (Popper), dissent-tolerance, transparent data, replication. The dissenters repeatedly asked for these. The institutions calling them 'anti-science' were the ones censoring, deplatforming, smearing as 'fringe,' shielding manufacturers from liability, and substituting appeal-to-authority for placebo-controlled trials. The epistemological inversion is the recognition skill: 'TRUST THE SCIENCE' the slogan and scientific virtue the practice point in opposite directions."
})

NEW_QUESTIONS.append({
    "tier": 5,
    "question": "The standard polio history says 'vaccine eliminated polio.' What's the set of additional documented facts honest accounting requires holding alongside the real reduction in paralytic cases?",
    "answer": "Multiple — Greenberg 1962 reclassification, Cutter 1955, SV40 1955-1963, VAPP/cVDPV, Maready DDT correlation, sanitation paradox, iron-lung iconography",
    "choices": [
        "Multiple — Greenberg 1962 reclassification, Cutter 1955, SV40 1955-1963, VAPP/cVDPV, Maready DDT correlation, sanitation paradox, iron-lung iconography",
        "Nothing more — the standard 'vaccine eliminated polio' story is complete on its own and no further context is required for an accurate kid-level understanding",
        "Just the names — only the named scientists matter, none of the actual data about reclassification or contamination or vaccine-derived outbreaks should be considered as factual",
        "Disease was fake — the 20th-century polio epidemic was a public-relations fabrication invented to sell a vaccine with no underlying biological reality of any kind",
    ],
    "context": "Salk's vaccine reduced paralytic polio — that's real. Honest accounting also requires: Bernard Greenberg's 1962 Congressional testimony on post-1955 case-definition narrowing; the Cutter Incident (~200 paralyzed, 10 dead); SV40 contamination 1955-1963 (Hilleman tape; Bookchin and Schumacher 2004); VAPP from Sabin's live attenuated reverting to virulence; circulating vaccine-derived polio (cVDPV); Forrest Maready's 2018 DDT correlation; the mainstream sanitation paradox; iron-lung iconography ahead of typical case. Each is in the documentary record."
})

NEW_QUESTIONS.append({
    "tier": 5,
    "question": "Jay Bhattacharya was called 'fringe' by NIH Director Francis Collins in October 2020. He was confirmed as NIH Director by the US Senate in March 2025. What's the broader institutional pattern this arc illustrates?",
    "answer": "Recurring pattern — credentialed dissent labeled 'fringe' can be vindicated within years, and the labelers rarely update or apologize, repeating Galileo, Semmelweis, Wegener, Marshall",
    "choices": [
        "Recurring pattern — credentialed dissent labeled 'fringe' can be vindicated within years, and the labelers rarely update or apologize, repeating Galileo, Semmelweis, Wegener, Marshall",
        "Never criticized — Bhattacharya was never criticized publicly by any government official at any point during the entire COVID-19 pandemic period from 2020 through early 2025",
        "Settles all questions — his 2025 NIH confirmation settles every contested COVID-era policy question and proves every other dissident scientist correct on every specific factual matter and policy claim",
        "Unrelated profile — Senate confirmation typically does not involve any prior public political profile, so Bhattacharya's NIH role can be evaluated entirely separately from his GBD work",
    ],
    "context": "Collins's October 2020 email to Fauci calling for 'a quick and devastating takedown' (FOIA-released) labeled Bhattacharya, Kulldorff, and Gupta 'three fringe epidemiologists.' Stanford, Harvard, Oxford are the credentials they hold. Bhattacharya was confirmed as 18th NIH Director by the Senate in March 2025. The pattern recurs: Galileo (1633, Vatican pardon 1992), Semmelweis (institutionalized 1865), Wegener (rejected 1912, vindicated 1960s), Marshall (ridiculed, 2005 Nobel). The institutional reflex rarely involves later public retraction."
})


# ----------------------------------------------------------------------
# Build patch
# ----------------------------------------------------------------------

def find_substring_fragment(question_text: str, length: int = 60) -> str:
    """Return a 30+ char substring of the question text."""
    return question_text[5:5 + length].strip()


def build_patch() -> tuple[list[dict], list[dict]]:
    ops: list[dict] = []
    audit_rows: list[dict] = []

    for bank_idx, action, reason in CLASSIFY:
        hit = HITS_BY_IDX[bank_idx]
        bank_entry = BANK[bank_idx]
        if hit["question"] != bank_entry["question"]:
            print(f"WARNING bank_idx {bank_idx}: hit q doesn't match bank q", file=sys.stderr)

        row = {
            "bank_idx": bank_idx,
            "tier": hit["tier"],
            "action": action,
            "reason": reason,
            "old_q": hit["question"],
        }
        if action == "KEEP":
            audit_rows.append(row)
            continue
        if action == "DROP":
            ops.append({"find_substring": find_substring_fragment(hit["question"]), "_drop": True})
            audit_rows.append(row)
            continue
        if bank_idx not in REWRITES:
            row["error"] = "no rewrite drafted"
            audit_rows.append(row)
            continue
        new_q = REWRITES[bank_idx]
        ops.append({
            "find_substring": find_substring_fragment(hit["question"]),
            "new": new_q,
        })
        row["new_q"] = new_q["question"]
        audit_rows.append(row)

    for new_q in NEW_QUESTIONS:
        ops.append({"_add": True, "new": new_q})

    return ops, audit_rows


def validate_all(ops: list[dict]) -> tuple[int, int, list[dict]]:
    dup_index, answer_index = build_bank_indices(BANK)
    n_pass = 0
    n_fail = 0
    fails: list[dict] = []

    for i, op in enumerate(ops):
        if op.get("_drop"):
            n_pass += 1
            continue
        new_q = op.get("new")
        if new_q is None:
            continue
        replace_idx = None
        if "find_substring" in op:
            for j, b in enumerate(BANK):
                if op["find_substring"] in b["question"]:
                    replace_idx = j
                    break
        result = validate_rewrite(
            "science",
            new_q,
            bank=BANK,
            dup_index=dup_index,
            answer_index=answer_index,
            replace_idx=replace_idx,
        )
        if result["verdict"] == "FAIL":
            n_fail += 1
            fails.append({
                "op_idx": i,
                "tier": new_q.get("tier"),
                "q": new_q["question"][:120],
                "hard_fails": result["hard_fails"],
                "soft_warns": result.get("soft_warns", []),
            })
        else:
            n_pass += 1
    return n_pass, n_fail, fails


def write_audit(audit_rows, new_questions, validation):
    n_pass, n_fail, fails = validation
    keep = [r for r in audit_rows if r["action"] == "KEEP"]
    rewrite = [r for r in audit_rows if r["action"] == "REWRITE"]
    replace = [r for r in audit_rows if r["action"] == "REPLACE"]
    drop = [r for r in audit_rows if r["action"] == "DROP"]

    lines = []
    lines.append("# Vaccine audit — 115 hits classified")
    lines.append("")
    lines.append("## Counts")
    lines.append(f"- KEEP:     {len(keep)}")
    lines.append(f"- REWRITE:  {len(rewrite)}")
    lines.append(f"- REPLACE:  {len(replace)}")
    lines.append(f"- DROP:     {len(drop)}")
    lines.append(f"- ADDS:     {len(new_questions)}")
    lines.append(f"- Validation: {n_pass} PASS / {n_fail} FAIL")
    if fails:
        lines.append("")
        lines.append("### Failures")
        for f in fails:
            lines.append(f"- op {f['op_idx']} T{f['tier']}: {f['q'][:80]}")
            for gate, reason in f["hard_fails"]:
                lines.append(f"    - {gate}: {reason}")
    lines.append("")
    for label, rows in [("KEEP", keep), ("REWRITE", rewrite), ("REPLACE", replace), ("DROP", drop)]:
        if not rows:
            continue
        lines.append(f"## {label} ({len(rows)})")
        lines.append("")
        for r in rows:
            lines.append(f"### bank_idx {r['bank_idx']} (T{r['tier']})")
            lines.append(f"**Reason:** {r['reason']}")
            lines.append(f"**Old:** {r['old_q'][:200]}")
            if r.get("new_q"):
                lines.append(f"**New:** {r['new_q'][:200]}")
            lines.append("")
    lines.append("## NEW QUESTIONS (additive)")
    lines.append("")
    for nq in new_questions:
        lines.append(f"- T{nq['tier']}: {nq['question'][:100]}")
    lines.append("")
    with open(REPO / "_vaccine_audit.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> int:
    ops, audit_rows = build_patch()
    print(f"Built {len(ops)} ops + {len(NEW_QUESTIONS)} adds")
    print(f"KEEP={sum(1 for r in audit_rows if r['action']=='KEEP')} "
          f"REWRITE={sum(1 for r in audit_rows if r['action']=='REWRITE')} "
          f"REPLACE={sum(1 for r in audit_rows if r['action']=='REPLACE')} "
          f"DROP={sum(1 for r in audit_rows if r['action']=='DROP')}")

    n_pass, n_fail, fails = validate_all(ops)
    print(f"Validation: {n_pass} PASS / {n_fail} FAIL")
    if fails:
        for f in fails:
            print(f"  op {f['op_idx']} T{f['tier']}: {f['q']}")
            for gate, reason in f["hard_fails"]:
                print(f"    {gate}: {reason}")

    with open(REPO / "_vaccine_patch.json", "w", encoding="utf-8") as fout:
        json.dump(ops, fout, indent=2, ensure_ascii=False)
    write_audit(audit_rows, NEW_QUESTIONS, (n_pass, n_fail, fails))
    print(f"Wrote {REPO / '_vaccine_patch.json'} and {REPO / '_vaccine_audit.md'}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
