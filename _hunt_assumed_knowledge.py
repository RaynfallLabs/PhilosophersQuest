"""Hunt for two failure modes:
1. Weasel closers I missed (different jargon-y forms of the same pattern)
2. Questions that assume technical knowledge in the closer without defining it in the stem

The Madoff question is the canonical case:
- "What's the Ponzi tell?" assumes you know what a Ponzi scheme is, who Ponzi was, what a 'tell' means
- Stem mentions Madoff but doesn't define what a Ponzi scheme IS
- Closer uses jargon ("tell") that's poker terminology
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# Weasel-shaped closers I missed (new variants)
NEW_WEASELS = [
    r"[Ww]hat'?s the \w+ tell\??$",
    r"[Ww]hat'?s the \w+ pattern\??$",
    r"[Ww]hat'?s the \w+ red flag\??$",
    r"[Ww]hat'?s the \w+ recognition\??$",
    r"[Ww]hat'?s the \w+ skill\??$",
    r"[Ww]hat'?s the \w+ check\??$",
    r"[Ww]hat'?s the \w+ trick\??$",
    r"[Ww]hat'?s the \w+ play\??$",
    r"[Ww]hat'?s the \w+ move\??$",
    r"[Ww]hat'?s the \w+ insight\??$",
    r"[Ww]hat does that suggest\??$",
    r"[Ww]hat'?s the (deeper )?warning\??$",
    r"[Ww]hat'?s the catch\??$",
    r"[Ww]hat'?s the implication\??$",
    r"[Ww]hat'?s the structural \w+\??$",
    r"[Ww]hat'?s the underlying \w+\??$",
]

# Jargon terms that should be DEFINED in stem before being used in closer
# (the closer uses this term — was it explained in the stem?)
JARGON_TERMS = [
    "Ponzi", "moral hazard", "adverse selection", "Cantillon", "ABCT",
    "tax wedge", "regulatory capture", "rent-seeking", "moral hazard",
    "knowledge problem", "calculation problem", "praxeology",
    "comparative advantage", "absolute advantage", "marginal utility",
    "subjective value", "elasticity", "monopsony", "monopoly",
    "oligopoly", "rent-seeking", "QE", "ZIRP", "NIRP", "MMT",
    "fiat", "specie", "seigniorage",
]

WEASEL_RE = re.compile("|".join(NEW_WEASELS))


def analyze_question(q):
    """Return (issues, severity) for a question."""
    issues = []
    stem = q.get("question", "")
    answer = q.get("answer", "")
    stem_stripped = stem.rstrip()

    # 1. Weasel-shaped closer (new variants)
    if WEASEL_RE.search(stem_stripped):
        m = WEASEL_RE.search(stem_stripped)
        issues.append(("WEASEL", m.group(0)))

    # 2. Jargon in closer not defined in stem
    # Get the last 80 chars (the closer) and check for jargon
    closer = stem_stripped[-100:]
    earlier = stem_stripped[:-100]
    for term in JARGON_TERMS:
        if re.search(rf"\b{term}\b", closer, re.IGNORECASE):
            # Check if it's defined in the earlier stem
            if not re.search(rf"\b{term}\b", earlier, re.IGNORECASE):
                # Term appears in closer but not in earlier stem — assumed knowledge
                issues.append(("ASSUMED_JARGON", term))
                break

    return issues


hit_total = 0
for f in sorted(Path("data/questions").glob("*.json")):
    if "backup" in f.name or f.stem == "dropped":
        continue
    try:
        bank = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        continue
    if not isinstance(bank, list):
        continue
    issues_by_type = {"WEASEL": [], "ASSUMED_JARGON": []}
    for i, q in enumerate(bank):
        if not isinstance(q, dict):
            continue
        issues = analyze_question(q)
        for kind, detail in issues:
            issues_by_type[kind].append((i, q.get("tier"), detail, q.get("question", "")))
    n_weasel = len(issues_by_type["WEASEL"])
    n_assumed = len(issues_by_type["ASSUMED_JARGON"])
    if n_weasel + n_assumed > 0:
        print(f"\n=== {f.stem} ===")
        print(f"  WEASEL closer:     {n_weasel}")
        print(f"  ASSUMED jargon:    {n_assumed}")
        for i, tier, term, stem in issues_by_type["WEASEL"][:5]:
            tail = stem.rstrip()[-100:]
            print(f"  WEASEL bank#{i} T{tier}: '...{tail}'")
        for i, tier, term, stem in issues_by_type["ASSUMED_JARGON"][:5]:
            tail = stem.rstrip()[-100:]
            print(f"  ASSUMED bank#{i} T{tier} ({term}): '...{tail}'")
        hit_total += n_weasel + n_assumed

print(f"\n=== TOTAL ISSUES: {hit_total} ===")
