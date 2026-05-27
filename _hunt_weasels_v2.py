"""Expanded weasel hunt — catches the jargon-substituted variants and
intervening-clause forms my first regex missed.

User flag: my first weasel-purge missed:
- "What's the smart move?" / "What's the right move?" — same pattern with "move"
- "What's the structural problem?" / "What's the broader recognition?" — same with adjectives
- "What does the case illustrate about X?" — intervening clause beat the closer regex
- "What does it reveal about X?" / "What does the timing reveal?" — same trick
- "What was the giveaway?" / "What's the Ponzi tell?" — jargon nouns
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

WEASEL_V2_PATTERNS = [
    # Original v1 weasels (re-included so we get a complete count)
    r"[Ww]hat'?s the (recognition|takeaway|substance|lesson|pattern|connection|moral|kid'?s takeaway|recognition skill|recognition for|deeper (?:lesson|point|recognition)|structural recognition)\??$",
    r"[Ww]hat does this (illustrate|case illustrate|case show|case teach|case reveal|episode illustrate|episode show|story illustrate|case study illustrate|incident illustrate|incident show|show|prove|reveal|teach|period demonstrate|case demonstrate)\??$",
    r"[Ww]hy does this matter\??$",
    # v2: jargon-substituted noun
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
    r"[Ww]hat'?s the \w+ problem\??$",
    r"[Ww]hat'?s the \w+ giveaway\??$",
    r"[Ww]hat (was|is) the giveaway\??$",
    r"[Ww]hat'?s the (deeper|broader|structural|underlying|honest|key|specific) \w+\??$",
    r"[Ww]hat'?s the (deeper|broader|structural|underlying|honest|key|specific) (recognition|lesson|warning|implication|insight|point|move)\??$",
    r"[Ww]hat does that suggest\??$",
    r"[Ww]hat'?s the (deeper )?warning\??$",
    r"[Ww]hat'?s the catch\??$",
    r"[Ww]hat'?s the implication\??$",
    r"[Ww]hat'?s the unifying insight\??$",
    r"[Ww]hat recognition skill[^?]+\??$",
    # v3: intervening clause between "case/it/this/the X" and the meta-verb
    r"[Ww]hat does (the case|the episode|the story|the incident|the timing|the period|it|that) (illustrate|show|reveal|teach|prove|demonstrate|suggest|tell us|expose)[^?]*\??$",
    r"[Ww]hat does (this case|this episode|this story|this incident|this period) (illustrate|show|reveal|teach|prove|demonstrate|suggest|tell us|expose)[^?]*\??$",
    # v4: "What was the X" with abstract noun (similar to "What's the X" weasels)
    r"[Ww]hat was the (giveaway|tell|red flag|catch|implication|warning|recognition|takeaway|broader \w+)\??$",
]

WEASEL_V2_RE = re.compile("|".join(WEASEL_V2_PATTERNS))

# Banks touched in this session
SESSION_BANKS = ["ai", "animal", "cooking", "economics", "geography", "science"]

print(f"{'bank':<12} {'size':>6} {'weasels':>8}")
print("-" * 30)
total = 0
by_bank: dict[str, list] = {}
for bank_name in SESSION_BANKS:
    bank = json.loads(Path(f"data/questions/{bank_name}.json").read_text(encoding="utf-8"))
    hits = []
    for i, q in enumerate(bank):
        if WEASEL_V2_RE.search(q.get("question", "").rstrip()):
            hits.append(i)
    by_bank[bank_name] = hits
    total += len(hits)
    print(f"{bank_name:<12} {len(bank):>6} {len(hits):>8}")
print(f"{'TOTAL':<12} {' ':>6} {total:>8}")
print()

print("=== Samples of newly-found weasels ===")
for bank_name in SESSION_BANKS:
    if not by_bank[bank_name]:
        continue
    bank = json.loads(Path(f"data/questions/{bank_name}.json").read_text(encoding="utf-8"))
    print(f"\n--- {bank_name} ({len(by_bank[bank_name])} hits) ---")
    for idx in by_bank[bank_name][:8]:
        stem = bank[idx]["question"].rstrip()
        tail = stem[-110:]
        print(f"  bank#{idx} T{bank[idx]['tier']}: ...{tail}")

# Dump hits for downstream rewrite
out = {}
for bank_name, hits in by_bank.items():
    bank = json.loads(Path(f"data/questions/{bank_name}.json").read_text(encoding="utf-8"))
    out[bank_name] = [
        {
            "bank_idx": i,
            "tier": bank[i]["tier"],
            "question": bank[i]["question"],
            "answer": bank[i]["answer"],
            "choices": bank[i]["choices"],
            "context": bank[i].get("context", ""),
        }
        for i in hits
    ]
Path("_weasels_v2.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nWrote _weasels_v2.json")
