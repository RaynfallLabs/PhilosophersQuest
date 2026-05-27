"""Find weasel-closer stems across science + economics banks.

The pattern: stem ends with abstract meta-question instead of pointed
concrete one. "What's the recognition?" / "What's the takeaway?" /
"What does this illustrate?" / "What's the substance?" — all weasel
closers.
"""
import json
import re
from pathlib import Path

WEASEL_PATTERNS = [
    r"[Ww]hat'?s the recognition\??$",
    r"[Ww]hat'?s the recognition skill\??$",
    r"[Ww]hat'?s the takeaway\??$",
    r"[Ww]hat'?s the substance\??$",
    r"[Ww]hat'?s the lesson\??$",
    r"[Ww]hat'?s the pattern\??$",
    r"[Ww]hat'?s the connection\??$",
    r"[Ww]hat'?s the (structural|deeper) recognition\??$",
    r"[Ww]hat'?s the kid'?s takeaway\??$",
    r"[Ww]hat does this (case|episode|story|case study|incident) illustrate\??$",
    r"[Ww]hat does this case (illustrate|show|teach)\??$",
    r"[Ww]hat does this illustrate\??$",
    r"[Ww]hat does this (case|incident|episode) (illustrate|show|teach)\??$",
    r"[Ww]hat does this teach\??$",
    r"[Ww]hat does this episode show\??$",
    r"[Ww]hat does this period demonstrate\??$",
    r"[Ww]hat does this case demonstrate\??$",
    r"[Ww]hat does this show\??$",
    r"[Ww]hat does this prove\??$",
    r"[Ww]hat does this reveal\??$",
    r"[Ww]hat does this case reveal\??$",
    r"[Ww]hat'?s the recognition for[^?]+\??$",
    r"[Ww]hat'?s the recognition here[^?]*\??$",
    r"[Ww]hy does this matter\??$",
    r"[Ww]hat'?s the deeper (lesson|point|recognition)\??$",
    r"[Ww]hat'?s the moral\??$",
]

WEASEL_RE = re.compile("|".join(WEASEL_PATTERNS))


def hunt(bank_name: str):
    bank = json.loads(Path(f"data/questions/{bank_name}.json").read_text(encoding="utf-8"))
    hits = []
    for i, q in enumerate(bank):
        stem = q.get("question", "")
        if WEASEL_RE.search(stem.rstrip()):
            hits.append((i, q.get("tier"), stem))
    print(f"\n=== {bank_name}.json — {len(bank)} questions ===")
    print(f"  weasel-closer hits: {len(hits)}")
    print()
    for i, tier, stem in hits[:30]:
        # show the last ~80 chars of the stem to see the weasel closer
        tail = stem.rstrip()[-100:]
        print(f"  bank#{i:4d} T{tier}: ...{tail}")
    if len(hits) > 30:
        print(f"  ... and {len(hits) - 30} more")
    return hits


sci_hits = hunt("science")
econ_hits = hunt("economics")
print()
print(f"TOTAL: {len(sci_hits)} science + {len(econ_hits)} economics = {len(sci_hits) + len(econ_hits)}")
