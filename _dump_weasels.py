"""Dump weasel-closer questions for agent rewriting."""
import json
import re
from pathlib import Path

WEASEL_RE = re.compile(
    r"(?:[Ww]hat'?s the (?:recognition|takeaway|substance|lesson|pattern|connection|moral|kid'?s takeaway|recognition skill|recognition for|deeper (?:lesson|point|recognition)|structural recognition)\??$"
    r"|[Ww]hat does this (?:illustrate|case illustrate|case show|case teach|case reveal|episode illustrate|episode show|story illustrate|case study illustrate|incident illustrate|incident show|show|prove|reveal|teach|period demonstrate|case demonstrate)\??$"
    r"|[Ww]hy does this matter\??$)"
)

for bank_name in ("ai", "animal", "cooking", "economics", "geography", "science"):
    bank = json.loads(Path(f"data/questions/{bank_name}.json").read_text(encoding="utf-8"))
    hits = []
    for i, q in enumerate(bank):
        if WEASEL_RE.search(q.get("question", "")):
            hits.append({
                "bank_idx": i,
                "tier": q.get("tier"),
                "question": q.get("question", ""),
                "answer": q.get("answer", ""),
                "choices": q.get("choices", []),
                "context": q.get("context", ""),
            })
    Path(f"_weasel_{bank_name}.json").write_text(
        json.dumps(hits, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"{bank_name}: wrote _weasel_{bank_name}.json with {len(hits)} questions")
