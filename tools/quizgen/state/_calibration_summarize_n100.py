"""Compact summary table per question, plus aggregate gate-by-gate stats."""
import json
from pathlib import Path

J = Path(r"C:\Users\brand\Documents\PhilosophersQuest\tools\quizgen\state\_calibration_sample_n100.json")
recs = json.loads(J.read_text(encoding="utf-8"))

print(f"Total: {len(recs)}")
print(f"Tiers: {sorted({r['tier'] for r in recs})}")
print()

# Print one-line summary per record for review
print(f"{'#':>3} {'T':>1} {'idx':>4} {'A1':>3} {'A2':>3} {'A3':>3} {'A4n':>4} {'A4o':>4} {'Q':<70}")
for i, r in enumerate(recs):
    g = r["gates"]
    short_q = r["question"][:70]
    print(f"{i+1:>3} {r['tier']:>1} {r['idx']:>4} "
          f"{'P' if g['A1_schema_ok'] else 'F':>3} "
          f"{'P' if g['A2_parity_ok'] else 'F':>3} "
          f"{'P' if g['A3_cost_ok'] else 'F':>3} "
          f"{'P' if g['A4_rote_ok_patched'] else 'F':>4} "
          f"{'P' if g['A4_rote_ok_old'] else 'F':>4} "
          f"{short_q!r}")

print()
# Aggregate
total = len(recs)
fA1 = sum(1 for r in recs if not r["gates"]["A1_schema_ok"])
fA2 = sum(1 for r in recs if not r["gates"]["A2_parity_ok"])
fA3 = sum(1 for r in recs if not r["gates"]["A3_cost_ok"])
fA4_new = sum(1 for r in recs if not r["gates"]["A4_rote_ok_patched"])
fA4_old = sum(1 for r in recs if not r["gates"]["A4_rote_ok_old"])

print(f"\n--- Deterministic fail rates (n={total}) ---")
print(f"A1 schema:      {fA1}/{total} = {fA1*100/total:.0f}%")
print(f"A2 parity:      {fA2}/{total} = {fA2*100/total:.0f}%")
print(f"A3 cost cap:    {fA3}/{total} = {fA3*100/total:.0f}%")
print(f"A4 patched:     {fA4_new}/{total} = {fA4_new*100/total:.0f}%")
print(f"A4 old:         {fA4_old}/{total} = {fA4_old*100/total:.0f}%")
