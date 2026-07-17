"""Emit a human-readable COOKING_QUEUE_REVIEW.md in the project root from register.json.

Usage: python bankbuild/cooking/_gen_review_doc.py   (run _assemble_queue.py first)
"""
import json, os, collections, re

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"
reg = json.load(open(os.path.join(ROOT, "bankbuild", "cooking", "register.json"), encoding="utf-8"))
q = json.load(open(os.path.join(ROOT, "bankbuild", "cooking", "_queue.json"), encoding="utf-8"))
out = os.path.join(ROOT, "COOKING_QUEUE_REVIEW.md")

SORDER = {"kitchen": 0, "ingredient": 1, "recipe": 2, "history": 3, "wonder": 4, "nutrition": 5}
SECTION_NAME = {
    "kitchen":    "In the Kitchen — technique / tools / safety, mechanism as the lens",
    "ingredient": "Ingredients — provenance: where food comes from (cuts, parts of the plant, spices)",
    "recipe":     "Recipes — dish literacy: what a classic dish is + its core technique",
    "history":    "Food history — world history through food, told for the drama",
    "wonder":     "Amazing food facts — the wonder well",
    "nutrition":  "Nutrition — what food does in your body (traditional-foods lean)",
}
tot_q = max(1, reg["sum_target_q"])
L = []
L.append("# Cooking Bank v2 — Topic Queue for Review")
L.append("")
L.append("Ground-up rebuild on the ladder pipeline. **Design (locked with Brandon):** food KNOWLEDGE + WONDER a kid can")
L.append("USE, across **six strands** — In the Kitchen, Ingredients (provenance), Recipes (dish literacy), Food History")
L.append("(drama-led), Amazing Facts, and Nutrition. Every rung's **answer is food-anchored** (SHARED_PRINCIPLES §18 — no")
L.append("bare law/policy/agency; food-driven history where the FOOD is the anchor stays). Scene-led, never definition-shell;")
L.append("invert-the-wonder (big number in the stem, the knowable thing as the answer). Nutrition **leans traditional-foods**")
L.append("(steel-man both sides, empowerment not moralizing). Prep-frame is OK (the game action is cooking); a tone audit runs at ship.")
L.append("")
L.append(f"- **Topics:** {reg['total_topics']}  |  **Estimated questions:** ~{reg['sum_target_q']}  "
         f"(live bank being replaced: 1,066 Q)")
L.append(f"- **Stance-relevant topics** (nutrition lean; full text in the appendix): {reg['vision_mandated']}")
w = collections.Counter(t['weight'] for t in q)
d = collections.Counter(t['depth'] for t in q)
L.append(f"- **Weight:** {w.get('high',0)} high / {w.get('medium',0)} medium / {w.get('low',0)} low   "
         f"**Depth:** {d.get('deep',0)} deep (10-14 rungs) / {d.get('standard',0)} standard (5-8) / {d.get('mini',0)} mini (2-3)")
L.append("- **Deduped:** 29 redundant cross-strand twins removed (kept the best-placed version of each). "
         "Full list: `bankbuild/cooking/_dedupe_log.txt`.")
L.append("- **One near-duplicate kept on purpose** (flag if you disagree): *Black pepper, the King of Spices* (Food history — "
         "the trade/exploration drama) vs *Black pepper: the king-of-spices vine* (Ingredients — the botany: pepper is a dried "
         "unripe berry). Distinct angles; will be built to different facts.")
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
L.append("---")
L.append("")
L.append("## Every strand & its topics")
L.append("")
L.append("Each line: **topic** — tier span · depth · target questions · _scope excerpt (the per-rung plan)_. "
         "⚑STANCE = nutrition-lean topic (full framing in the appendix).")
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
        L.append(f"- **{t['name']}**{vm} — {t['tier_span']} · {t['depth']} · q{t['target_q']}  \n"
                 f"  _{t['scope'][:220]}{'…' if len(t['scope'])>220 else ''}_")
    L.append("")

# ---- appendix: full scope + framing for stance topics ----
L.append("---")
L.append("")
L.append("## Appendix — stance topics in full (verify the traditional-foods lean is baked correctly)")
L.append("")
vm_topics = [t for t in q if t["vision_mandated"]]
L.append(f"{len(vm_topics)} topics carry the nutrition stance. Full scope + framing_note below so you can check the LEAN is right "
         "(steel-man both sides, lean traditional-foods, empowerment not moralizing) before build.")
L.append("")
for t in sorted(vm_topics, key=lambda x: (SORDER.get(x["section"], 9), x["strand"], x["name"])):
    L.append(f"### {t['name']}  ({t['strand']} · {t['tier_span']} · {t['depth']} · q{t['target_q']})")
    L.append(f"**Scope:** {t['scope']}")
    L.append("")
    L.append(f"**Framing:** {t['framing_note']}")
    L.append("")
open(out, "w", encoding="utf-8").write("\n".join(L))
print("wrote", out, f"({os.path.getsize(out)//1024} KB,", len(L), "lines)")
