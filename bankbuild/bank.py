"""Integration harness for the overnight history bank rebuild.

Modes:
  integrate <workflow_output.json>  -- checkpoint passed ladders + record needs_review, update manifest
  merge                             -- flatten all passed checkpoints -> data/questions/history_v2.json (staging)
  status                            -- print manifest summary
  promote                           -- back up history.json, swap in history_v2.json (FINAL step only)

Per-topic checkpoint: bankbuild/history/ladders/<id>.json  (passed)
                      bankbuild/history/needs_review/<id>.json
Manifest: bankbuild/history/manifest.json  -- resume backbone + dashboard.
The live data/questions/history.json is NOT touched until `promote`.
"""
import json, os, sys, shutil, time

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"
BH = os.path.join(ROOT, "bankbuild", "history")
LAD = os.path.join(BH, "ladders")
NR = os.path.join(BH, "needs_review")
MAN = os.path.join(BH, "manifest.json")
QUEUE = os.path.join(BH, "_queue.json")
HIST = os.path.join(ROOT, "data", "questions", "history.json")
HIST_V2 = os.path.join(ROOT, "data", "questions", "history_v2.json")

for d in (LAD, NR):
    os.makedirs(d, exist_ok=True)


def jload(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default


def jdump(o, p):
    json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=True, indent=1)


def load_manifest():
    return jload(MAN, {})


def valid_rung(r):
    return (isinstance(r.get("choices"), list) and len(r["choices"]) == 4
            and r.get("answer") in r["choices"]
            and isinstance(r.get("stem"), str) and len(r["stem"]) > 10
            and isinstance(r.get("tier"), (int, float)))


def extract_results(wrapper):
    # workflow output file is {summary, result, ...}; result is {start,count,results}
    res = wrapper.get("result", wrapper) if isinstance(wrapper, dict) else wrapper
    if isinstance(res, str):
        res = json.loads(res)
    if isinstance(res, dict) and "results" in res:
        return res["results"]
    if isinstance(res, list):
        return res
    return []


def cmd_integrate(outfile):
    wrapper = jload(outfile)
    if wrapper is None:
        print("ERROR: cannot read", outfile); return
    results = extract_results(wrapper)
    queue = jload(QUEUE, [])
    man = load_manifest()
    n_pass = n_nr = n_bad = 0
    for r in results:
        if not r or "idx" not in r:
            continue
        idx = r["idx"]
        meta = queue[idx] if 0 <= idx < len(queue) else {}
        tid = meta.get("id", f"idx-{idx}")
        name = r.get("name") or meta.get("name", tid)
        rungs = (r.get("ladder") or {}).get("rungs", []) or []
        bad = [i for i, rg in enumerate(rungs) if not valid_rung(rg)]
        status = r.get("status")
        rec = {"id": tid, "name": name, "strand": meta.get("strand"), "idx": idx,
               "status": status, "n_rungs": len(rungs), "rounds": r.get("rounds", 0),
               "weight": meta.get("weight"), "depth": meta.get("depth"),
               "tier_span": meta.get("tier_span"), "sources": r.get("sources", []),
               "unresolved": r.get("unresolved", []), "invalid_rungs": bad,
               "ts": int(time.time())}
        if status == "passed" and rungs and not bad:
            jdump({**rec, "rungs": rungs}, os.path.join(LAD, tid + ".json"))
            man[tid] = {k: rec[k] for k in ("status", "n_rungs", "rounds", "idx", "name", "strand", "weight", "depth", "ts")}
            n_pass += 1
        else:
            eff = "needs_review" if status == "passed" and bad else (status or "error")
            jdump({**rec, "status": eff, "rungs": rungs}, os.path.join(NR, tid + ".json"))
            man[tid] = {"status": eff, "n_rungs": len(rungs), "rounds": r.get("rounds", 0),
                        "idx": idx, "name": name, "strand": meta.get("strand"),
                        "weight": meta.get("weight"), "depth": meta.get("depth"),
                        "unresolved": r.get("unresolved", [])[:4], "invalid_rungs": bad, "ts": int(time.time())}
            if status == "passed" and bad:
                n_bad += 1
            else:
                n_nr += 1
    jdump(man, MAN)
    print(f"integrated: {n_pass} passed, {n_nr} needs_review, {n_bad} passed-but-invalid(->review). manifest: {len(man)} topics total.")


def cmd_merge():
    bank, topics = [], 0
    for fn in sorted(os.listdir(LAD)):
        if not fn.endswith(".json"):
            continue
        d = jload(os.path.join(LAD, fn))
        if not d or not d.get("rungs"):
            continue
        topics += 1
        for rg in d["rungs"]:
            if not valid_rung(rg):
                continue
            ctx = rg.get("context", "")
            if rg.get("legend") and "legend" not in ctx.lower():
                ctx = (ctx + "  (Legend.)").strip()
            bank.append({"tier": int(rg["tier"]), "question": rg["stem"],
                         "answer": rg["answer"], "choices": rg["choices"], "context": ctx})
    jdump(bank, HIST_V2)
    from collections import Counter
    print(f"merged {topics} topics -> {len(bank)} questions -> {HIST_V2}")
    print("  tier dist:", dict(sorted(Counter(q["tier"] for q in bank).items())))


def cmd_status():
    man = load_manifest()
    from collections import Counter
    by = Counter(v["status"] for v in man.values())
    rungs = sum(v.get("n_rungs", 0) for v in man.values() if v["status"] == "passed")
    print(f"manifest: {len(man)} topics | {dict(by)} | passed rungs: {rungs}")
    nr = [v for v in man.values() if v["status"] != "passed"]
    if nr:
        print("needs_review/other:")
        for v in nr[:30]:
            print(f"   {v['status']:<13} {v.get('name','?')[:46]:<46} {v.get('unresolved',[])}")


def cmd_promote():
    if not os.path.exists(HIST_V2):
        print("no history_v2.json to promote"); return
    v2 = jload(HIST_V2, [])
    bak = os.path.join(ROOT, "data", "questions", "history_pre_v2_backup.json")
    if os.path.exists(HIST) and not os.path.exists(bak):
        shutil.copy2(HIST, bak)
        print("backed up original ->", bak)
    shutil.copy2(HIST_V2, HIST)
    print(f"PROMOTED {len(v2)} questions -> {HIST} (live bank).")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "integrate":
        cmd_integrate(sys.argv[2])
    elif cmd == "merge":
        cmd_merge()
    elif cmd == "status":
        cmd_status()
    elif cmd == "promote":
        cmd_promote()
    else:
        print("unknown:", cmd)
