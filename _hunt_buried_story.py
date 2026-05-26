"""Find buried-story candidates: substantive detail in context, dry stem+answer."""
import json
import re
from pathlib import Path

bank = json.loads(Path("data/questions/science.json").read_text(encoding="utf-8"))


def buried_story_candidate(q):
    stem = q.get("question", "") or ""
    answer = q.get("answer", "") or ""
    context = q.get("context", "") or ""

    if len(context) < 200:
        return None
    if len(context) < (len(stem) + len(answer)) * 0.9:
        return None

    stem_ans = (stem + " " + answer).lower()
    named_facts_buried = set()

    # Dollar amounts
    for m in re.finditer(r"\$[\d,.]+(?:\s*(?:million|billion|trillion|k|M|B))?", context):
        if m.group(0) not in stem and m.group(0) not in answer:
            named_facts_buried.add(m.group(0))

    # Dramatic counts
    pat = r"~?[\d,]+(?:\.\d+)?\s*(?:million|billion|thousand|paralyzed|paralysed|killed|dead|deaths|cases|years|months|weeks|days)"
    for m in re.finditer(pat, context, re.IGNORECASE):
        if m.group(0).lower() not in stem_ans:
            named_facts_buried.add(m.group(0))

    # Specific years (4-digit)
    for m in re.finditer(r"\b(19\d{2}|20\d{2})\b", context):
        if m.group(0) not in stem and m.group(0) not in answer:
            named_facts_buried.add(m.group(0))

    # Multi-word Title Case (likely names / institutions / events)
    for m in re.finditer(r"(?:[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){1,4})", context):
        phrase = m.group(0)
        if len(phrase) < 10:
            continue
        if phrase.lower() in stem_ans:
            continue
        if phrase in ("United States", "United Kingdom", "New York", "World War"):
            continue
        named_facts_buried.add(phrase)

    if len(named_facts_buried) < 3:
        return None

    generic_stem_markers = [
        "what happened", "describe", "explain", "what was", "what is the",
        "what does this", "what was the", "tell us about", "how did",
        "what's the recognition", "what does the case", "what does the episode",
    ]
    ends_generic = any(m in stem.lower() for m in generic_stem_markers)

    return {
        "tier": q.get("tier"),
        "buried_count": len(named_facts_buried),
        "generic_stem": ends_generic,
        "stem_len": len(stem),
        "ans_len": len(answer),
        "ctx_len": len(context),
    }


TOPIC_TERMS = re.compile(
    r"\b(?:"
    r"Surgisphere|Stapel|Hwang|Macchiarini|Obokata|Schon|Reinhart|Wansink|Theranos|"
    r"COVID|coronavirus|SARS-CoV-2|lab leak|Wuhan|EcoHealth|gain-of-function|"
    r"lockdown|mask mandate|Cochrane|Hanke|school clos|GBD|Great Barrington|"
    r"hydroxychloroquine|HCQ|ivermectin|remdesivir|Paxlovid|"
    r"Bhattacharya|Kulldorff|McCullough|Malone|Kory|Fauci|Collins|"
    r"Twitter Files|Murthy|Missouri|disinformation|jawboning|"
    r"Buck v\.? Bell|sterilization|eugenics|Sanger|Holmes|imbecil|"
    r"Tuskegee|Sims|Lacks|Belmont|Unit 731|T4 program|Nuremberg|"
    r"Climategate|hide the decline|East Anglia|Mann|hockey stick|"
    r"Ehrlich|Population Bomb|Simon|Borlaug|"
    r"Wegener|Marshall|Semmelweis|Lister|Margulis|Prusiner|Lavoisier|"
    r"Wakefield|Cutter|SV40|VAERS|VICP|NCVIA|VAPP|cVDPV|Maready|"
    r"Vioxx|Purdue|Sackler|opioid|"
    r"WEF|Schwab|Harari|Great Reset|Fourth Industrial"
    r")\b",
    re.IGNORECASE,
)

candidates = []
for i, q in enumerate(bank):
    text = " ".join([q.get("question", ""), q.get("answer", ""), q.get("context", "")])
    if not TOPIC_TERMS.search(text):
        continue
    c = buried_story_candidate(q)
    if c:
        c["bank_idx"] = i
        c["stem"] = q.get("question", "")[:120]
        c["answer"] = q.get("answer", "")[:120]
        candidates.append(c)

candidates.sort(key=lambda c: (-c["buried_count"], not c["generic_stem"]))

print(f"Total buried-story candidates in contested-topic questions: {len(candidates)}")
print()
print("Top 25:")
print(f'{"idx":>5} {"tier":>4} {"buried":>7} {"generic":>8} {"stem":<70}')
for c in candidates[:25]:
    print(f'{c["bank_idx"]:>5} T{c["tier"]:>3} {c["buried_count"]:>7} {str(c["generic_stem"]):>8} {c["stem"][:70]!r}')

Path("_buried_story_candidates.json").write_text(
    json.dumps(candidates, indent=2, ensure_ascii=False), encoding="utf-8"
)
print()
print(f"Full list saved to _buried_story_candidates.json")
