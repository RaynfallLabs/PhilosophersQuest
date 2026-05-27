"""Dump remaining v3 weasels for the rewrite agent."""
import json
import re
from pathlib import Path

WEASEL_V3 = re.compile(
    r"(?:[Ww]hat'?s the (?:recognition|takeaway|substance|lesson|pattern|connection|moral|kid'?s takeaway|recognition skill|recognition for|deeper (?:lesson|point|recognition)|structural recognition|smart move|right move|broader \w+|deeper \w+|structural \w+|underlying \w+|honest \w+|key \w+|specific \w+|unifying insight|\w+ tell|\w+ pattern|\w+ red flag|\w+ skill|\w+ check|\w+ move|\w+ insight|\w+ problem|\w+ giveaway)\??$"
    r"|[Ww]hat does this (?:illustrate|case illustrate|show|prove|reveal|teach|demonstrate)\??$"
    r"|[Ww]hat does (?:the case|the episode|the story|the incident|the timing|it|that) (?:illustrate|show|reveal|teach|prove|demonstrate|suggest|tell us|expose)[^?]*\??$"
    r"|[Ww]hat does the \w+ (?:illustrate|show|reveal|teach|prove|demonstrate|expose)[^?]*\??$"
    r"|[Ww]hy does this matter\??$"
    r"|[Ww]hat (?:was|is) the giveaway\??$"
    r"|[Ww]hat does that suggest\??$"
    r"|[Ww]hat'?s the catch\??$"
    r")"
)

# Manual false-positive guard: skip questions where the weasel form actually
# asks about something concrete (e.g., "what does that reveal about Earth's
# shape" or "what does that reveal about the writ's force" — both pointed)
TRUE_WEASEL_HINT_RE = re.compile(
    r"(?:What does (?:this|the case|the episode|it|that) (?:illustrate|case illustrate|show|prove|reveal|teach|demonstrate|expose|suggest|tell us)\??$|"
    r"What'?s the (?:recognition|takeaway|substance|lesson|pattern|connection|moral|recognition skill|broader \w+|structural \w+|underlying \w+|honest \w+|catch|giveaway|tell|red flag)\??$|"
    r"What does the \w+ (?:illustrate|show|reveal|teach|prove|demonstrate|expose)\??$)"
)

all_hits = {}
for f in sorted(Path("data/questions").glob("*.json")):
    if "backup" in f.name:
        continue
    bank = json.loads(f.read_text(encoding="utf-8"))
    if not isinstance(bank, list):
        continue
    hits = []
    for i, q in enumerate(bank):
        if not isinstance(q, dict):
            continue
        stem = q.get("question", "").rstrip()
        if not WEASEL_V3.search(stem):
            continue
        # If the regex match ends in a clearly-pointed phrase like
        # "about Earth's shape" or "about the writ's force", it's a
        # pointed question — skip it.
        m = WEASEL_V3.search(stem)
        matched = m.group(0)
        # Heuristic: matched closer is a TRUE weasel if it ends with a
        # generic vague form (no "about X-specific-noun" pointed cap)
        # Easiest cut: skip questions where the matched portion ends
        # with " about " + Capital-letter-or-' (specific) — that means
        # it actually points at something.
        if re.search(r"\babout\b\s+(?:[A-Z']|the\s+\w+'s\s+\w+)", matched):
            continue
        hits.append({
            "bank_idx": i,
            "tier": q["tier"],
            "question": q["question"],
            "answer": q["answer"],
            "choices": q["choices"],
            "context": q.get("context", ""),
        })
    if hits:
        all_hits[f.stem] = hits
        print(f"  {f.stem}: {len(hits)}")

Path("_weasels_v3.json").write_text(
    json.dumps(all_hits, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
print(f"\nWrote _weasels_v3.json with {sum(len(v) for v in all_hits.values())} hits across {len(all_hits)} banks")
