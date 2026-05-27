"""Hunt for Christian-doctrinal drift in the theology bank.

Per user direction (2026-05-27): user is NOT Christian; bank does NOT
promote Christianity as true. All four traditions told straight on the
same plane.

This script scans every theology question's stem + answer + choices +
context for the banned framings codified in THEOLOGY_FRAMEWORK.md §5:
- Christian-doctrinal: "fulfilled prophecy", "the Lord" (devotional),
  "Our Lord", "the Savior", "the true God", "the risen Christ",
  "the resurrected Lord", "as Scripture teaches", "Scripture reveals"
- Smug atheist: "ancient peoples ignorantly believed", "primitive
  belief", "sky-god myth"
- Smug believer: "the false gods of", "pagan superstition"

Output: _christian_drift_candidates.json — list of flagged questions
with bank_idx + matched phrase + question preview, for the rewrite
agent.

Edge cases tolerated (NOT flagged):
- "the LORD" / "the Lord" in direct Bible quotation contexts where it's
  the standard scholarly small-caps rendering of YHWH (NIV/ESV/Hebrew-
  Bible convention)
- "Resurrection" / "Pentecost" / "Last Supper" as story-event proper
  nouns (parallel to Ragnarok / Birth of Athena — these capitalize
  story events across all traditions)
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# Banned phrases (case-insensitive) — these are devotional drift, not
# story-event names
BANNED_PHRASES = [
    # Christian-doctrinal devotional framing
    r"\bfulfilled the prophecy\b",
    r"\bfulfilled prophecy\b",
    r"\bfulfilled Zechariah\b",
    r"\bfulfilled Isaiah\b",
    r"\bfulfilled Daniel\b",
    r"\bfulfilled (?:the )?words? of\b",
    r"\bOur Lord\b",
    r"\bthe Savior\b",
    r"\bthe true God\b",
    r"\bthe one true (?:God|faith|religion)\b",
    r"\bthe risen Christ\b",
    r"\bthe resurrected (?:Lord|Christ)\b",
    r"\brisen Lord\b",
    r"\bas Scripture teaches\b",
    r"\bScripture (?:reveals|teaches|tells us|shows)\b",
    r"\bthe real (?:account|story|truth) of\b",
    r"\bthe historical truth (?:of|about)\b",
    # Smug atheist
    r"\bancient peoples? ignorantly believed\b",
    r"\bprimitive (?:Hebrew|Norse|Greek|Egyptian) (?:myth|belief|tale)\b",
    r"\bsky[- ]?(?:god|fairy|wizard)\b",
    # Smug believer
    r"\bthe false gods? of\b",
    r"\bpagan (?:superstition|nonsense|error)\b",
    r"\bheathen (?:superstition|nonsense)\b",
    # Devotional verbs that imply truth-claim
    r"\b(?:our|the) (?:redemption|salvation)\b",
]

BANNED_RE = re.compile("|".join(BANNED_PHRASES), re.IGNORECASE)

# Exception: "the LORD" in quoted Hebrew Bible passages is the standard
# scholarly rendering of YHWH (small caps). We tolerate it.
LORD_QUOTE_PATTERN = re.compile(r'["\'][^"\']{0,200}\b(?:the LORD|the Lord)\b[^"\']{0,200}["\']')

bank_path = Path("data/questions/theology.json")
bank = json.loads(bank_path.read_text(encoding="utf-8"))
print(f"Scanning {len(bank)} theology questions for Christian-doctrinal drift...\n")

hits = []
for i, q in enumerate(bank):
    fields = {
        "stem": q.get("question", ""),
        "answer": q.get("answer", ""),
        "context": q.get("context", ""),
    }
    for j, c in enumerate(q.get("choices", [])):
        fields[f"choice_{j}"] = c if isinstance(c, str) else ""

    matched = []
    for field_name, text in fields.items():
        if not text:
            continue
        for m in BANNED_RE.finditer(text):
            matched_text = m.group(0)
            # Check if it's in a quoted Bible passage
            if matched_text.lower() in ("the lord", "the lord."):
                if LORD_QUOTE_PATTERN.search(text):
                    continue  # tolerate quoted passages
            matched.append({
                "field": field_name,
                "phrase": matched_text,
                "context_around": text[max(0, m.start()-50):m.end()+50],
            })

    if matched:
        hits.append({
            "bank_idx": i,
            "tier": q.get("tier"),
            "stem_preview": q.get("question", "")[:100],
            "answer": q.get("answer", "")[:80],
            "matches": matched,
        })

# Tier histogram
tier_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
for h in hits:
    t = h["tier"]
    if t in tier_counts:
        tier_counts[t] += 1

print(f"=== {len(hits)} Christian-doctrinal drift candidates ===\n")
print("Per tier:")
for t, c in tier_counts.items():
    print(f"  T{t}: {c}")
print()

# Phrase histogram
phrase_counts = {}
for h in hits:
    for m in h["matches"]:
        p = m["phrase"].lower()
        phrase_counts[p] = phrase_counts.get(p, 0) + 1

print("Top phrases:")
for p, c in sorted(phrase_counts.items(), key=lambda kv: -kv[1])[:15]:
    print(f"  {p!r}: {c}")

# Save to file
out_path = Path("_christian_drift_candidates.json")
out_path.write_text(json.dumps(hits, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nWrote {out_path} with {len(hits)} candidates")

# Sample for human eyeball
print("\n=== First 5 hits ===")
for h in hits[:5]:
    print(f"\n#{h['bank_idx']} T{h['tier']}: {h['stem_preview']}...")
    for m in h["matches"][:2]:
        print(f"  [{m['field']}] {m['phrase']!r}: ...{m['context_around']}...")
