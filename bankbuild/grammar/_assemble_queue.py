"""Assemble the per-slice spec files into register.json + _queue.json for the grammar bank v2.

Reads bankbuild/grammar/_strands/spec_*.json (each a JSON array of topic-ladder specs), adds a unique
`id` slug from each topic name, validates required fields, resolves exact-slug collisions (keep earlier),
flags near-duplicate topic names for review, priority-sorts (weight high>med>low, then depth
deep>standard>mini), groups by `section` (punctuation|homophones_confusables|agreement|
sentence_structure|usage_register|wordplay_advanced), and writes both files
with coverage stats. Re-runnable.

Usage: python bankbuild/grammar/_assemble_queue.py
"""
import json, os, re, collections, sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"
SD    = os.path.join(ROOT, "bankbuild", "grammar", "_strands")
QUEUE = os.path.join(ROOT, "bankbuild", "grammar", "_queue.json")
REG   = os.path.join(ROOT, "bankbuild", "grammar", "register.json")

REQ = ["name", "section", "strand", "kind", "scope", "tier_span", "source", "framing_note",
       "vision_mandated", "weight", "depth", "target_q"]
WORDER = {"high": 0, "medium": 1, "low": 2}
DORDER = {"deep": 0, "standard": 1, "mini": 2, "shallow": 1}
SORDER = {"punctuation": 0, "homophones_confusables": 1, "agreement": 2,
          "sentence_structure": 3, "usage_register": 4, "wordplay_advanced": 5}
SECTION_NAME = {
    "punctuation":            "Punctuation (commas -- vocative + Oxford + splice; semicolons; apostrophes; dashes; quotation marks)",
    "homophones_confusables": "Homophones + confusables (your/you're, there/their/they're, its/it's, affect/effect, then/than, lose/loose, accept/except, complement/compliment)",
    "agreement":              "Agreement (subject-verb; pronoun-antecedent; collective + measurement subjects)",
    "sentence_structure":     "Sentence structure (fragments, run-ons, comma splices, parallel structure, garden-path, misplaced/dangling modifiers)",
    "usage_register":         "Usage + register (literally, ironic, less/fewer, may/might, active vs passive, wordy vs concise, tense/mood consistency)",
    "wordplay_advanced":      "Wordplay + etymology + advanced cases (chiasmus, zeugma, malapropism, spoonerism, buffalo construction, Eats Shoots and Leaves)",
}
STOP = set("the a an of and or to in on at by for is as vs its s with from".split())


def slug(s):
    s = s.lower().replace("&", "and").replace("'", "").replace("’", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60].strip("-")


def toks(name):
    return set(t for t in re.findall(r"[a-z0-9]+", name.lower()) if t not in STOP and len(t) > 2)


spec_files = sorted(fn for fn in os.listdir(SD) if re.match(r"spec_.*\.json$", fn))

topics, seen_slugs = [], {}
collisions, missing, all_named = [], [], []
for fn in spec_files:
    arr = json.load(open(os.path.join(SD, fn), encoding="utf-8"))
    for t in arr:
        miss = [k for k in REQ if k not in t or t[k] in (None, "")]
        if "target_q" in t and isinstance(t["target_q"], (int, float)) and t["target_q"] <= 0:
            miss.append("target_q<=0")
        if t.get("section") not in SORDER:
            miss.append("bad-section")
        if miss:
            missing.append((fn, t.get("name", "?"), miss)); continue
        sid = slug(t["name"])
        if sid in seen_slugs:
            collisions.append((sid, t["name"], t["strand"], seen_slugs[sid])); continue
        seen_slugs[sid] = t["strand"]
        rec = {"id": sid, "name": t["name"], "section": t["section"], "strand": t["strand"],
               "kind": "ladder", "scope": t["scope"], "tier_span": t["tier_span"],
               "source": t["source"], "framing_note": t["framing_note"],
               "vision_mandated": bool(t["vision_mandated"]),
               "history_overlap": (t.get("history_overlap") or ""),
               "weight": t["weight"], "depth": t["depth"], "target_q": int(t["target_q"])}
        topics.append(rec)
        all_named.append((sid, t["name"], t["strand"], toks(t["name"])))

order = sorted(topics, key=lambda r: (WORDER.get(r["weight"], 9), DORDER.get(r["depth"], 9),
                                      SORDER.get(r["section"], 9), r["strand"], r["name"]))

nd = []
for i in range(len(all_named)):
    for j in range(i + 1, len(all_named)):
        a, b = all_named[i], all_named[j]
        if a[0] == b[0] or not (a[3] and b[3]):
            continue
        inter = a[3] & b[3]
        if not inter:
            continue
        jac = len(inter) / len(a[3] | b[3])
        if jac >= 0.5 or (len(a[3]) >= 2 and a[3] <= b[3]) or (len(b[3]) >= 2 and b[3] <= a[3]):
            nd.append((round(jac, 2), a[1], a[2], "||", b[1], b[2]))

strand_map = collections.OrderedDict()
for r in sorted(topics, key=lambda x: (SORDER.get(x["section"], 9), x["strand"], x["name"])):
    strand_map.setdefault((r["section"], r["strand"]), []).append(r)
reg_strands = [{"section": sec, "strand": s, "count": len(ts),
                "sum_target_q": sum(t["target_q"] for t in ts), "topics": ts}
               for (sec, s), ts in strand_map.items()]

json.dump(order, open(QUEUE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
reg = {"subject": "grammar", "total_topics": len(topics),
       "sum_target_q": sum(r["target_q"] for r in topics),
       "vision_mandated": sum(1 for r in topics if r["vision_mandated"]),
       "history_overlap_flagged": sum(1 for r in topics if r["history_overlap"]),
       "strands": reg_strands}
json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"SPEC FILES: {len(spec_files)} -> {spec_files}")
print(f"TOPICS: {len(topics)}   SUM target_q (est questions): {reg['sum_target_q']}   "
      f"vision_mandated: {reg['vision_mandated']}   sister-overlap flagged: {reg['history_overlap_flagged']}")
print(f"missing/bad topics dropped: {len(missing)}  | exact-slug collisions dropped: {len(collisions)}")
for fn, nm, mm in missing[:40]:
    print("   MISSING", fn, "|", nm, mm)
for sid, nm, st, first in collisions[:40]:
    print(f"   COLLISION '{nm}' ({st}) dup of slug in [{first}] -> dropped")
print("\nWEIGHT:", dict(collections.Counter(r["weight"] for r in topics)),
      " DEPTH:", dict(collections.Counter(r["depth"] for r in topics)))
tspan = collections.Counter()
for r in topics:
    mm = re.findall(r"T(\d)", r["tier_span"])
    if mm:
        for tt in range(int(mm[0]), int(mm[-1]) + 1):
            tspan[tt] += 1
print("TIER coverage (topics whose span includes Tn):", dict(sorted(tspan.items())))
print("\nBY SECTION (topics / est-questions):")
tot_q = max(1, reg["sum_target_q"])
sec = collections.OrderedDict()
for r in topics:
    sec.setdefault(r["section"], [0, 0])
    sec[r["section"]][0] += 1; sec[r["section"]][1] += r["target_q"]
for k in sorted(sec, key=lambda x: SORDER.get(x, 9)):
    c, qq = sec[k]
    print(f"   {c:3d} top / {qq:4d} q ({100*qq//tot_q:2d}%)  {k:13s} {SECTION_NAME.get(k,'')}")
print(f"\nSISTER-OVERLAP flagged topics (review before build): {reg['history_overlap_flagged']}")
for r in topics:
    if r["history_overlap"]:
        print(f"    {r['id']:40s} -> {r['history_overlap']}")
print(f"\nNEAR-DUP topic names (review, NOT auto-dropped): {len(nd)}")
for x in sorted(nd, reverse=True)[:30]:
    print("   ", x)
