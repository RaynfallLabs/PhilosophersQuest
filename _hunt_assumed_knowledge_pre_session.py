"""Quick §16 sweep on the pre-session-rebuilt banks (grammar, history,
math, philosophy, theology, trivia).

For each bank, scan for jargon terms used in 3+ questions but with no
foundational question that teaches the term. This is a heuristic — it
flags candidates for human review, doesn't auto-judge.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# Subject-specific jargon terms to check
# Each is something a kid would need TAUGHT (not common-knowledge)
SUBJECT_JARGON = {
    "grammar": [
        "subjunctive", "gerund", "participle", "infinitive",
        "conditional", "perfect tense", "passive voice",
        "deixis", "anaphora", "cataphora", "etymology",
    ],
    "history": [
        "interregnum", "thalassocracy", "feudalism", "indulgences",
        "consul", "tribune", "Magna Carta", "Reichstag", "Politburo",
        "Comintern", "writ of habeas corpus",
    ],
    "math": [
        "irrational", "transcendental", "axiom", "lemma",
        "Pythagoras", "Euclidean", "non-Euclidean", "calculus",
        "topology", "derivative", "integral", "infinity",
    ],
    "philosophy": [
        "categorical imperative", "utilitarian", "veil of ignorance",
        "trolley problem", "Pareto", "naturalistic fallacy",
        "hard problem", "qualia", "noumenon", "phenomenon",
        "tabula rasa", "social contract", "state of nature",
        "Socratic method",
    ],
    "theology": [
        "soteriology", "eschatology", "exegesis", "hermeneutics",
        "Pentateuch", "synoptic", "apocrypha", "Magisterium",
        "Eucharist", "sacrament", "atonement",
    ],
    "trivia": [],  # too broad to audit
}

for subject, terms in SUBJECT_JARGON.items():
    if not terms:
        continue
    bank = json.loads(Path(f"data/questions/{subject}.json").read_text(encoding="utf-8"))
    print(f"\n=== {subject} ({len(bank)} questions) ===")
    for term in terms:
        # Count uses in stem
        pat = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        # Stem uses (potentially assumes knowledge)
        stem_uses = sum(1 for q in bank if pat.search(q.get("question", "")))
        # Answer uses (likely teaches by being the answer)
        answer_uses = sum(1 for q in bank if pat.search(q.get("answer", "")))
        # Direct definitional pattern in any question: "term means X" / "X is called term" / etc.
        def_pattern = re.compile(
            rf"(?:term|name|word)\s+(?:for\s+)?[\"']?\b{re.escape(term)}\b|"
            rf"\b{re.escape(term)}\b\s+(?:means|refers to|is the name|is called|is the term|is defined as|stands for)",
            re.IGNORECASE,
        )
        def_uses = sum(1 for q in bank if def_pattern.search(q.get("question", "") + " " + q.get("answer", "")))

        verdict = "OK" if (stem_uses == 0 or answer_uses + def_uses >= 1) else "MAYBE-ASSUMED"
        if stem_uses >= 3 or (stem_uses > 0 and answer_uses + def_uses == 0):
            print(f"  [{verdict:>14}] {term:<30} stem_uses={stem_uses}, answer_uses={answer_uses}, def_uses={def_uses}")
