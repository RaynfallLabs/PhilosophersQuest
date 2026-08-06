"""Emit a human-readable GEOGRAPHY_QUEUE_REVIEW.md in the project root from register.json.

Usage: python bankbuild/geography/_gen_review_doc.py   (run _assemble_queue.py first)
"""
import json, os, collections, re, sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"
reg = json.load(open(os.path.join(ROOT, "bankbuild", "geography", "register.json"), encoding="utf-8"))
q = json.load(open(os.path.join(ROOT, "bankbuild", "geography", "_queue.json"), encoding="utf-8"))
out = os.path.join(ROOT, "GEOGRAPHY_QUEUE_REVIEW.md")

SORDER = {"city": 0, "nature": 1, "ancient": 2, "culture": 3, "earthsystem": 4}
SECTION_NAME = {
    "city":        "Cities of wonder — one city deepened (architecture, hidden marvels, culture born there)",
    "nature":      "Natural wonders — one waterfall / lake / mountain / desert / coast / landscape deepened",
    "ancient":     "Ancient marvels & lost civilizations — place-wonder (history-bank overlap flagged)",
    "culture":     "Cultural birthplaces — a dance / craft / script born in a place (NON-food)",
    "earthsystem": "Magical earth systems — one process deepened ACROSS the places that show it (theme ladders)",
}
tot_q = max(1, reg["sum_target_q"])
L = []
L.append("# Geography Bank v2 — Topic Queue for Review")
L.append("")
L.append("Ground-up rebuild under the confirmed design: **PLACE → WONDER**, place-anchored lane,")
L.append("two ladder shapes (place ladders + earth-system theme ladders as the backbone), the PLACE")
L.append("always the anchor, one coherent wonder per rung. Food origins → cooking bank; an animal's")
L.append("biology → animal bank; ancient sites kept as place-wonder with history-bank overlap flagged.")
L.append("")
L.append(f"- **Topics:** {reg['total_topics']}  |  **Estimated questions:** ~{reg['sum_target_q']}  "
         f"(live bank being replaced: 1,123 Q)")
L.append(f"- **Stance-relevant topics** (⚑ vision-mandated): {reg['vision_mandated']}")
L.append(f"- **History-overlap flagged** (review before build): {reg.get('history_overlap_flagged', 0)}")
w = collections.Counter(t['weight'] for t in q)
d = collections.Counter(t['depth'] for t in q)
L.append(f"- **Weight:** {w.get('high',0)} high / {w.get('medium',0)} medium / {w.get('low',0)} low   "
         f"**Depth:** {d.get('deep',0)} deep / {d.get('standard',0)} standard / {d.get('mini',0)} mini")
L.append("")
L.append("## Coverage by section")
L.append("")
L.append("| Section | Topics | Est. Q | % |")
L.append("|---|--:|--:|--:|")
sec = collections.OrderedDict()
for s in reg["strands"]:
    sec.setdefault(s["section"], [0, 0])
    sec[s["section"]][0] += s["count"]; sec[s["section"]][1] += s["sum_target_q"]
for k in sorted(sec, key=lambda x: SORDER.get(x, 9)):
    c, qq = sec[k]
    L.append(f"| {SECTION_NAME.get(k, k)} | {c} | {qq} | {100*qq//tot_q}% |")
L.append("")
tspan = collections.Counter()
for t in q:
    mm = re.findall(r"T(\d)", t["tier_span"])
    if mm:
        for tt in range(int(mm[0]), int(mm[-1]) + 1):
            tspan[tt] += 1
L.append("**Tier coverage** (topics whose span includes each tier): "
         + ", ".join(f"T{k}={v}" for k, v in sorted(tspan.items())))
L.append("")
# history-overlap review block
flagged = [t for t in q if t.get("history_overlap")]
if flagged:
    L.append("## ⚠ History-bank overlap flagged (decide keep-as-place-wonder vs drop)")
    L.append("")
    for t in flagged:
        L.append(f"- **{t['name']}** ({t['section']}) — {t['history_overlap']}")
    L.append("")
L.append("## Every strand & its topics")
L.append("")
cur = None
for s in sorted(reg["strands"], key=lambda x: (SORDER.get(x["section"], 9), x["strand"])):
    if s["section"] != cur:
        cur = s["section"]
        L.append(f"# {SECTION_NAME.get(cur, cur)}")
        L.append("")
    L.append(f"### {s['strand']}  *( {s['count']} topics · ~{s['sum_target_q']} q )*")
    for t in s["topics"]:
        vm = " ⚑STANCE" if t["vision_mandated"] else ""
        ho = " ⚠HIST" if t.get("history_overlap") else ""
        L.append(f"- **{t['name']}**{vm}{ho} — {t['tier_span']} · {t['depth']} · q{t['target_q']} · "
                 f"_{t['scope'][:170]}_")
    L.append("")
open(out, "w", encoding="utf-8").write("\n".join(L))
print("wrote", out, f"({os.path.getsize(out)//1024} KB,", len(L), "lines)")
