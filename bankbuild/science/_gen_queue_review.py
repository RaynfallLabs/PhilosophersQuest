"""Render SCIENCE_QUEUE_REVIEW.md (project root) from bankbuild/science/register.json.

Brandon's queue-review gate (PIPELINE 9.2): every topic with its essence, per-strand rollups,
vision/stance topics highlighted, sister-overlap flags summarized, near-dup + dedup outcomes noted.
Re-runnable (run AFTER queue_dedup_apply so the doc reflects the final queue).

Usage: python bankbuild/science/_gen_queue_review.py
"""
import json, os, re, sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"
REG = os.path.join(ROOT, "bankbuild", "science", "register.json")
QUEUE = os.path.join(ROOT, "bankbuild", "science", "_queue.json")
OUT = os.path.join(ROOT, "SCIENCE_QUEUE_REVIEW.md")

SECTION_TITLE = {
    "physics":    "PHYSICS -- motion, energy, light, quantum, atoms (told by the experiments)",
    "chemistry":  "CHEMISTRY -- element hunters, bonds, reactions, materials & the prepared mind",
    "life":       "LIFE & MEDICINE -- cells, DNA, evolution, the body, germs, vaccines-scrutinized",
    "earthspace": "EARTH & SPACE -- deep time, honest climate, the mapped heavens (mechanism, not place)",
    "howscience": "HOW SCIENCE WORKS -- method, dissent, frauds, dark chapters, contested (heaviest)",
}
SECTION_ORDER = ["physics", "chemistry", "life", "earthspace", "howscience"]


def essence(scope, n=200):
    """First sentence-ish of the scope, cleaned."""
    s = re.sub(r"\s+", " ", scope or "").strip()
    cut = s.find(" T1:")
    if 0 < cut < n:
        s = s[:cut]
    return (s[: n - 1] + "\u2026") if len(s) > n else s


reg = json.load(open(REG, encoding="utf-8"))
queue = json.load(open(QUEUE, encoding="utf-8"))
live_ids = {t["id"] for t in queue}
live_q = sum(t["target_q"] for t in queue)
live_vm = sum(1 for t in queue if t.get("vision_mandated"))
live_ov = sum(1 for t in queue if (t.get("history_overlap") or "").strip())

lines = []
lines.append("# SCIENCE BANK v2 -- TOPIC QUEUE REVIEW")
lines.append("")
lines.append(f"**{len(queue)} topic ladders / ~{live_q} estimated questions** after semantic dedup "
             f"(445 researched, 36 same-fact twins dropped; geography shipped 405 / 3,216 for scale). "
             f"{live_vm} stance topics (vision_mandated); "
             f"{live_ov} carry a sister-bank lane flag (guard notes, not dups).")
lines.append("")
lines.append("Voice: Discovery Pattern (how we KNOW) + the test-it-yourself soul. "
             "Review for: (1) topics to CUT (weak/dull/wrong-bank), (2) anything MISSING, "
             "(3) stance topics framed wrong, (4) the overall size call.")
lines.append("")

secmap = {}
for st in reg["strands"]:
    secmap.setdefault(st["section"], []).append(st)

for sec in SECTION_ORDER:
    sts = secmap.get(sec, [])
    if not sts:
        continue
    n_top = sum(s["count"] for s in sts)
    n_q = sum(s["sum_target_q"] for s in sts)
    lines.append(f"## {SECTION_TITLE.get(sec, sec)}  \u2014  {n_top} topics / ~{n_q} q")
    lines.append("")
    for st in sts:
        lines.append(f"### {st['strand']}  ({st['count']} topics / ~{st['sum_target_q']} q)")
        lines.append("")
        for t in st["topics"]:
            if t["id"] not in live_ids:
                continue  # dropped by dedup apply
            flags = []
            if t.get("vision_mandated"):
                flags.append("**STANCE**")
            if t.get("depth") == "deep":
                flags.append("deep")
            if t.get("weight") == "low":
                flags.append("low-wt")
            fl = (" [" + ", ".join(flags) + "]") if flags else ""
            lines.append(f"- **{t['name']}** ({t['tier_span']}, ~{t['target_q']}q){fl}  ")
            lines.append(f"  {essence(t.get('scope'))}")
            ov = (t.get("history_overlap") or "").strip()
            if ov:
                ov1 = re.sub(r"\s+", " ", ov)
                lines.append(f"  *lane:* {ov1[:180]}{'\u2026' if len(ov1) > 180 else ''}")
        lines.append("")

open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print(f"wrote {OUT}")
print(f"sections: {len(secmap)}  strands: {len(reg['strands'])}  topics in doc: "
      f"{sum(1 for st in reg['strands'] for t in st['topics'] if t['id'] in live_ids)} (of {reg['total_topics']} in register)")
