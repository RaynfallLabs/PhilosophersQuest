"""Emit a human-readable ANIMAL_QUEUE_REVIEW.md in the project root from register.json.

Usage: python bankbuild/animal/_gen_review_doc.py   (run _assemble_queue.py first)
"""
import json, os, collections, re

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"
reg = json.load(open(os.path.join(ROOT, "bankbuild", "animal", "register.json"), encoding="utf-8"))
q = json.load(open(os.path.join(ROOT, "bankbuild", "animal", "_queue.json"), encoding="utf-8"))
out = os.path.join(ROOT, "ANIMAL_QUEUE_REVIEW.md")

SORDER = {"adaptation": 0, "creature": 1, "bizarre": 2, "paleo": 3, "contested": 4}
SECTION_NAME = {
    "adaptation": "Adaptation ladders — a biological theme deepened across the animals that share it",
    "creature":   "Creature ladders — one animal deepened",
    "bizarre":    "Bizarre & unusual animals",
    "paleo":      "Paleo / transitional",
    "contested":  "Contested (animal-anchored, both sides)",
}
tot_q = max(1, reg["sum_target_q"])
L = []
L.append("# Animal Bank v2 — Topic Queue for Review")
L.append("")
L.append("Ground-up rebuild under the reframed design: **pure animal-knowledge**, two ladder shapes")
L.append("(adaptation themes as the backbone + single-creature ladders), the animal always the anchor,")
L.append("one coherent wonder per rung, human drama only as a coherent animal-anchored payoff.")
L.append("Culture/myth/human-history and butchery/ingredients are OUT (moved to other tiers).")
L.append("")
L.append(f"- **Topics:** {reg['total_topics']}  |  **Estimated questions:** ~{reg['sum_target_q']}  "
         f"(live bank being replaced: 924 Q)")
L.append(f"- **Stance-relevant topics** (contested, both-sides): {reg['vision_mandated']}")
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
        L.append(f"- **{t['name']}**{vm} — {t['tier_span']} · {t['depth']} · q{t['target_q']} · "
                 f"_{t['scope'][:170]}_")
    L.append("")
open(out, "w", encoding="utf-8").write("\n".join(L))
print("wrote", out, f"({os.path.getsize(out)//1024} KB,", len(L), "lines)")
