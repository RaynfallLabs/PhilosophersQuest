"""Build Wonder Pattern audit candidate files for any subject.

Runs 5 scans:
  - drama_available: stem has drama keywords + question asks venue/date/label
  - magnitude_pick: "how many" question with numeric distractors
  - generic_label: answer is a place/date/battle-name (Tier-5 banned)
  - single_word_distinction: all 4 choices differ by ~1 word
  - paraphrased_distractor: distractor overlaps answer heavily

Writes:
  _audit_<subject>_t1.json
  _audit_<subject>_t23.json
  _audit_<subject>_t45.json

Each agent gets ONE shard.

Run: py tools/quizgen/scratch/_build_audit_candidates.py <subject>
     OR: py tools/quizgen/scratch/_build_audit_candidates.py all
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent

DRAMA = re.compile(
    r"\b(burned|killed|murdered|crucified|guillotined|hanged|stabbed|shot|drowned|tortured|"
    r"fled|suicide|died|dying|massacred|sacked|ambushed|surrender(?:ed)?|kissed?|crown(?:ed)?|"
    r"coup|treason|martyr|exile|exiled|escaped|sniper|cannon|sword|knife|poison|asp|cobra|"
    r"fire|blood(?:y)?|prayer|last word|final word|ashes|tomb|grave|throne|abdicated|witch|"
    r"stake|gibbet|gallows|scaffold|skull|skulls?|drag(?:ged)?|trample(?:d)?|chains?|prison(?:er)?)\b",
    re.I,
)

WEAK_Q = re.compile(
    r"\b(Where (?:was|did|is)|When (?:was|did|is)|"
    r"What (?:is|was) (?:the |this )?(battle|war|treaty|building|tower|temple|palace|fortress|"
    r"river|city|country|place|empire|kingdom|book|movement|period|era|painting|sculpture|opera|play) called|"
    r"What is (?:it|this) called|In what year|How many years (?:ago|did)|"
    r"What is the name|What was the name|"
    r"Which (?:city|country|nation|state|place|region|river|mountain|island|continent|battle|year))\b",
    re.I,
)

HOW_MANY = re.compile(
    r"\b(How many|about how many|approximately how many|roughly how many|"
    r"what fraction|what percentage|how much|how long did|how long was|how big)\b",
    re.I,
)

PLACE_LIKE = re.compile(r"^[A-Z][a-z]+(?:,?\s+[A-Z][a-z]+)*(?:,?\s+[A-Z]{2})?\s*(?:\(|$|\.)", re.I)
DATE_LIKE = re.compile(r"^(In |About |The )?\d{3,4}(?:\s*(?:BC|AD|BCE|CE))?(?:\s|\.|$)", re.I)
BATTLE_NAME_LIKE = re.compile(r"^The Battle of |^Battle of |^The (?:War|Treaty|Siege) of", re.I)


def num_distractors(q):
    chs = q.get("choices", [])
    return len(chs) == 4 and all(re.search(r"\d", c) for c in chs)


def all_share_words(q):
    chs = q.get("choices", [])
    if len(chs) != 4:
        return False
    tokens = [c.lower().split() for c in chs]
    if min(len(t) for t in tokens) < 3:
        return False
    common = set(tokens[0])
    for t in tokens[1:]:
        common &= set(t)
    avg = sum(len(t) for t in tokens) / 4
    return len(common) / avg >= 0.6


def paraphrased_distractor(q):
    ans = q.get("answer", "").lower().split()
    if len(ans) < 3:
        return False
    ans_set = set(ans)
    for c in q.get("choices", []):
        if c == q.get("answer"):
            continue
        c_set = set(c.lower().split())
        overlap = len(ans_set & c_set) / max(len(ans_set | c_set), 1)
        if overlap > 0.5:
            return True
    return False


def scan_subject(subject: str) -> dict:
    p = REPO / "data" / "questions" / f"{subject}.json"
    if not p.exists():
        print(f"  {subject}: NO BANK FILE")
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))

    flagged = {
        "drama_available": [],
        "magnitude_pick": [],
        "generic_label": [],
        "single_word_distinction": [],
        "paraphrased_distractor": [],
    }

    for q in d:
        qs = q.get("question", "")
        ans = q.get("answer", "")
        if DRAMA.search(qs) and WEAK_Q.search(qs):
            flagged["drama_available"].append(q)
        if HOW_MANY.search(qs) and num_distractors(q):
            flagged["magnitude_pick"].append(q)
        if (PLACE_LIKE.match(ans) or DATE_LIKE.match(ans) or BATTLE_NAME_LIKE.match(ans)) and len(ans.split()) <= 5:
            flagged["generic_label"].append(q)
        if all_share_words(q):
            flagged["single_word_distinction"].append(q)
        if paraphrased_distractor(q):
            flagged["paraphrased_distractor"].append(q)

    # dedupe by question-prefix
    unique: dict[str, dict] = {}
    for bucket in flagged.values():
        for q in bucket:
            unique[q.get("question", "")[:80]] = q

    cand = list(unique.values())

    # Split by tier
    t1 = [q for q in cand if q.get("tier") == 1]
    t23 = [q for q in cand if q.get("tier") in (2, 3)]
    t45 = [q for q in cand if q.get("tier") in (4, 5)]

    (REPO / f"_audit_{subject}_t1.json").write_text(json.dumps(t1, indent=2, ensure_ascii=False), encoding="utf-8")
    (REPO / f"_audit_{subject}_t23.json").write_text(json.dumps(t23, indent=2, ensure_ascii=False), encoding="utf-8")
    (REPO / f"_audit_{subject}_t45.json").write_text(json.dumps(t45, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"  {subject}: {len(d)} total, {len(cand)} unique candidates -> T1={len(t1)}, T2+T3={len(t23)}, T4+T5={len(t45)}")
    print(f"    by flag: drama={len(flagged['drama_available'])}, mag={len(flagged['magnitude_pick'])}, label={len(flagged['generic_label'])}, single={len(flagged['single_word_distinction'])}, para={len(flagged['paraphrased_distractor'])}")
    return {
        "subject": subject,
        "total": len(d),
        "unique": len(cand),
        "by_tier_split": {"t1": len(t1), "t23": len(t23), "t45": len(t45)},
        "by_flag": {k: len(v) for k, v in flagged.items()},
    }


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: py _build_audit_candidates.py <subject>|all")
        return 1
    targets = ["philosophy", "cooking", "animal", "geography"] if args[0] == "all" else args
    print("Scanning:")
    summary = []
    for s in targets:
        result = scan_subject(s)
        if result:
            summary.append(result)
    print()
    print("Summary:")
    for s in summary:
        print(f"  {s['subject']}: {s['unique']}/{s['total']} flagged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
