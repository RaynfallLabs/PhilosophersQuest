"""Read the geography queue-research workflow output, write one spec_<slug>.json per sub-strand.

Injects the fixed section/strand/kind fields (the agents omitted them) onto each returned spec.
Usage: python bankbuild/geography/_write_specs.py "<task output .output file>"
"""
import json, os, sys

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"
SD = os.path.join(ROOT, "bankbuild", "geography", "_strands")
os.makedirs(SD, exist_ok=True)

SECTIONS = ("city", "nature", "ancient", "culture", "earthsystem")

outfile = sys.argv[1] if len(sys.argv) > 1 else None
raw = json.load(open(outfile, encoding="utf-8"))


def find_substrands(o):
    """Locate the substrands array wherever the wrapper puts it."""
    if isinstance(o, dict):
        if isinstance(o.get("substrands"), list):
            return o["substrands"]
        for k in ("result", "value", "output", "data"):
            if k in o:
                v = o[k]
                if isinstance(v, str):
                    try:
                        v = json.loads(v)
                    except Exception:
                        continue
                r = find_substrands(v)
                if r is not None:
                    return r
        for v in o.values():
            r = find_substrands(v)
            if r is not None:
                return r
    return None


subs = find_substrands(raw)
if subs is None:
    print("ERROR: could not locate 'substrands' in", outfile)
    sys.exit(1)

total_specs = 0
rows = []
for ss in subs:
    slug = ss.get("slug", "unknown")
    section = ss.get("section")
    strand = ss.get("strand")
    specs = ss.get("specs") or []
    out = []
    for s in specs:
        rec = {"name": s.get("name"), "section": section, "strand": strand, "kind": "ladder",
               "scope": s.get("scope"), "tier_span": s.get("tier_span"),
               "source": s.get("source"), "framing_note": s.get("framing_note"),
               "vision_mandated": bool(s.get("vision_mandated", False)),
               "history_overlap": (s.get("history_overlap") or ""),
               "weight": s.get("weight"), "depth": s.get("depth"),
               "target_q": s.get("target_q")}
        out.append(rec)
    path = os.path.join(SD, f"spec_{slug}.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    q = sum(int(r.get("target_q") or 0) for r in out)
    total_specs += len(out)
    rows.append((section, slug, len(out), q))

print(f"wrote {len(subs)} spec files, {total_specs} topic specs total\n")
for sec in SECTIONS:
    secrows = [r for r in rows if r[0] == sec]
    if secrows:
        print(f"[{sec}]  {sum(r[2] for r in secrows)} topics / ~{sum(r[3] for r in secrows)} q")
        for _, slug, n, q in secrows:
            print(f"    {slug:34s} {n:3d} topics  ~{q:3d} q")
