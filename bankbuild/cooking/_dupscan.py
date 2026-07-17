"""Question-level near-duplicate scan/dedup for the staged cooking bank.

The queue dedup only caught token-similar TOPIC NAMES; semantically overlapping ladders can still
ask the SAME FACT twice. This scans the merged bank for near-duplicate QUESTIONS and drops the
redundant twin (keeping the one with the richer context).

Calibrated on the real bank: genuine twins sit at stem-sim ~0.42-0.50, so THRESH=0.42, and a pair
only counts as the same FACT if the ANSWERS match too (jaccard >= 0.30, or one answer's tokens are a
subset of the other's, or one raw answer string contains the other -- that last case catches
degenerate answers like 'A, D, E, and K' whose content tokens vanish).

Re-run after any re-merge. Usage: python bankbuild/cooking/_dupscan.py [--apply]
"""
import json, re, sys, collections

BANK = r"C:\Users\brand\Documents\PhilosophersQuest\data\questions\cooking_v2.json"
APPLY = "--apply" in sys.argv
THRESH = 0.42

STOP = set("""a an the of to in on at by for and or but nor so yet as if it its is are was were be been being he she they them his her
their our your my we you i me us him who whom whose which what that this these those with from into onto over under above below between
among through during before after while until since not no only just very more most much many few some any all each every both either
neither did do does done has have had having will would shall should can could may might must than then thus also too about around near
upon out off down up away back when where why how here there now today never always often one two three four five six seven eight nine
ten first second third last next cook cooks cooking food""".split())


def toks(s):
    return set(w for w in re.findall(r"[a-z][a-z\-']+", (s or "").lower()) if w not in STOP and len(w) > 2)


def jac(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def same_fact(bank, sig, i, j):
    ai, aj = sig[i][1], sig[j][1]
    if jac(ai, aj) >= 0.30:
        return True
    if ai and aj and (ai <= aj or aj <= ai):
        return True
    ra = re.sub(r"[^a-z]", "", bank[i]["answer"].lower())
    rb = re.sub(r"[^a-z]", "", bank[j]["answer"].lower())
    return bool(ra and rb and (ra in rb or rb in ra))


bank = json.load(open(BANK, encoding="utf-8"))
sig = [(toks(q["question"]) | toks(q["answer"]), toks(q["answer"])) for q in bank]

inv = collections.defaultdict(list)
for i, (s, a) in enumerate(sig):
    for w in s:
        inv[w].append(i)
common = {w for w, l in inv.items() if len(l) > 220}
cand = set()
for w, lst in inv.items():
    if w in common or len(lst) < 2:
        continue
    for x in range(len(lst)):
        for y in range(x + 1, len(lst)):
            cand.add((lst[x], lst[y]))

pairs = sorted(((jac(sig[i][0], sig[j][0]), i, j) for i, j in cand if jac(sig[i][0], sig[j][0]) >= THRESH), reverse=True)

drop, kept = set(), []
for s, i, j in pairs:
    if not same_fact(bank, sig, i, j):
        kept.append((round(s, 2), bank[i]["answer"][:38], "||", bank[j]["answer"][:38]))
        continue
    if i in drop or j in drop:
        continue
    d = j if len(bank[i].get("context", "")) >= len(bank[j].get("context", "")) else i
    drop.add(d)
    print(f"DROP idx{d} (sim={s:.2f}) T{bank[d]['tier']} ans={bank[d]['answer'][:50]!r}")

print()
print("KEPT (similar stems, different facts):")
for k in kept:
    print("  ", k)
print(f"\nTOTAL DROPPED: {len(drop)} of {len(bank)}")

if APPLY:
    out = [q for i, q in enumerate(bank) if i not in drop]
    json.dump(out, open(BANK, "w", encoding="utf-8"), ensure_ascii=True, indent=1)
    t = collections.Counter(q["tier"] for q in out)
    print(f"APPLIED -> {len(out)} questions | tiers: {dict(sorted(t.items()))}")
else:
    print("(dry run -- pass --apply to remove)")
