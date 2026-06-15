"""Subject-agnostic integration harness for bank rebuilds (default subject: history).

Usage:  python bankbuild/bank.py <mode> [args] [--subject=NAME]
Modes:
  integrate <workflow_output.json>  -- checkpoint passed ladders + record needs_review, update manifest
  merge                             -- flatten passed checkpoints -> data/questions/<subject>_v2.json (staging)
  status                            -- print manifest summary
  gate                              -- run the deterministic mechanical-tell gate over the staged bank
  promote                           -- back up <subject>.json, swap in <subject>_v2.json (runs gate first; FINAL step)

Per-subject layout (convention):  bankbuild/<subject>/ladders/<id>.json  (passed)
                                  bankbuild/<subject>/needs_review/<id>.json
                                  bankbuild/<subject>/manifest.json
The live data/questions/<subject>.json is NOT touched until `promote`.
"""
import json, os, sys, shutil, time

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"


def paths(subject):
    bh = os.path.join(ROOT, "bankbuild", subject)
    P = dict(
        subject=subject, BH=bh,
        LAD=os.path.join(bh, "ladders"), NR=os.path.join(bh, "needs_review"),
        MAN=os.path.join(bh, "manifest.json"), QUEUE=os.path.join(bh, "_queue.json"),
        HIST=os.path.join(ROOT, "data", "questions", subject + ".json"),
        HIST_V2=os.path.join(ROOT, "data", "questions", subject + "_v2.json"),
        BAK=os.path.join(ROOT, "data", "questions", subject + "_pre_v2_backup.json"),
    )
    for d in (P["LAD"], P["NR"]):
        os.makedirs(d, exist_ok=True)
    return P


def jload(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default


def jdump(o, p):
    json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=True, indent=1)


def valid_rung(r):
    return (isinstance(r.get("choices"), list) and len(r["choices"]) == 4
            and r.get("answer") in r["choices"]
            and isinstance(r.get("stem"), str) and len(r["stem"]) > 10
            and isinstance(r.get("tier"), (int, float)))


def extract_results(wrapper):
    res = wrapper.get("result", wrapper) if isinstance(wrapper, dict) else wrapper
    if isinstance(res, str):
        res = json.loads(res)
    if isinstance(res, dict) and "results" in res:
        return res["results"]
    if isinstance(res, list):
        return res
    return []


def cmd_integrate(P, outfile):
    wrapper = jload(outfile)
    if wrapper is None:
        print("ERROR: cannot read", outfile); return
    results = extract_results(wrapper)
    queue = jload(P["QUEUE"], [])
    man = jload(P["MAN"], {})
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
            jdump({**rec, "rungs": rungs}, os.path.join(P["LAD"], tid + ".json"))
            man[tid] = {k: rec[k] for k in ("status", "n_rungs", "rounds", "idx", "name", "strand", "weight", "depth", "ts")}
            n_pass += 1
        else:
            eff = "needs_review" if status == "passed" and bad else (status or "error")
            jdump({**rec, "status": eff, "rungs": rungs}, os.path.join(P["NR"], tid + ".json"))
            man[tid] = {"status": eff, "n_rungs": len(rungs), "rounds": r.get("rounds", 0),
                        "idx": idx, "name": name, "strand": meta.get("strand"),
                        "weight": meta.get("weight"), "depth": meta.get("depth"),
                        "unresolved": r.get("unresolved", [])[:4], "invalid_rungs": bad, "ts": int(time.time())}
            if status == "passed" and bad:
                n_bad += 1
            else:
                n_nr += 1
    jdump(man, P["MAN"])
    print(f"integrated: {n_pass} passed, {n_nr} needs_review, {n_bad} passed-but-invalid(->review). manifest: {len(man)} topics total.")


def cmd_merge(P):
    bank, topics = [], 0
    for fn in sorted(os.listdir(P["LAD"])):
        if not fn.endswith(".json"):
            continue
        d = jload(os.path.join(P["LAD"], fn))
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
    jdump(bank, P["HIST_V2"])
    from collections import Counter
    print(f"merged {topics} topics -> {len(bank)} questions -> {P['HIST_V2']}")
    print("  tier dist:", dict(sorted(Counter(q["tier"] for q in bank).items())))


def cmd_status(P):
    man = jload(P["MAN"], {})
    from collections import Counter
    by = Counter(v["status"] for v in man.values())
    rungs = sum(v.get("n_rungs", 0) for v in man.values() if v["status"] == "passed")
    print(f"[{P['subject']}] manifest: {len(man)} topics | {dict(by)} | passed rungs: {rungs}")
    nr = [v for v in man.values() if v["status"] != "passed"]
    if nr:
        print("needs_review/other:")
        for v in nr[:30]:
            print(f"   {v['status']:<13} {v.get('name','?')[:46]:<46} {v.get('unresolved',[])}")


def run_gate(path):
    """Deterministic mechanical-tell scan of a staged bank; returns flagged count (None on error)."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from tellgate import gate
        bank = jload(path, [])
        flagged = [i for i, q in enumerate(bank) if gate(q)]
        return len(flagged), len(bank)
    except Exception as e:
        print("  [gate] skipped:", e); return None, 0


def cmd_gate(P):
    n, total = run_gate(P["HIST_V2"])
    if n is None:
        return
    print(f"[{P['subject']}] gate: {n}/{total} questions carry a mechanical-tell flag "
          f"({100*n//max(1,total)}%). detail: python bankbuild/tellgate.py bank \"{P['HIST_V2']}\"")


def cmd_promote(P):
    if not os.path.exists(P["HIST_V2"]):
        print("no", os.path.basename(P["HIST_V2"]), "to promote"); return
    n, total = run_gate(P["HIST_V2"])
    if n is not None:
        if n:
            print(f"  [gate] {n}/{total} mechanical-tell flags in the staged bank "
                  f"(review: python bankbuild/tellgate.py bank \"{P['HIST_V2']}\"). Promoting anyway.")
        else:
            print(f"  [gate] clean: 0 mechanical-tell flags in {total} questions.")
    v2 = jload(P["HIST_V2"], [])
    if os.path.exists(P["HIST"]) and not os.path.exists(P["BAK"]):
        shutil.copy2(P["HIST"], P["BAK"])
        print("backed up original ->", P["BAK"])
    shutil.copy2(P["HIST_V2"], P["HIST"])
    print(f"PROMOTED {len(v2)} questions -> {P['HIST']} (live bank).")


if __name__ == "__main__":
    argv = sys.argv[1:]
    subject = "history"
    rest = []
    for a in argv:
        if a.startswith("--subject="):
            subject = a.split("=", 1)[1]
        else:
            rest.append(a)
    mode = rest[0] if rest else "status"
    P = paths(subject)
    if mode == "integrate":
        cmd_integrate(P, rest[1])
    elif mode == "merge":
        cmd_merge(P)
    elif mode == "status":
        cmd_status(P)
    elif mode == "gate":
        cmd_gate(P)
    elif mode == "promote":
        cmd_promote(P)
    else:
        print("unknown:", mode)
