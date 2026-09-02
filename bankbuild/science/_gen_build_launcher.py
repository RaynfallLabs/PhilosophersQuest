"""Regenerate bankbuild/science/_build.wf.js from bankbuild/subjects/science.json.

Run after any config edit so the launcher's embedded CONFIG stays in sync.
Usage: python bankbuild/science/_gen_build_launcher.py
"""
import json, os

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"
cfg = json.load(open(os.path.join(ROOT, "bankbuild", "subjects", "science.json"), encoding="utf-8"))
cfg_js = json.dumps(cfg, ensure_ascii=True, indent=1)

head = """export const meta = {
  name: 'science-build',
  description: 'Science bank build launcher: embeds the science subject config and delegates to the generic bank_pipeline for the given idxs (research -> author -> craft-judge -> adversarial-judge + gate).',
  phases: [{ title: 'Build', detail: 'delegate to bank_pipeline for the batch idxs' }],
}

const A = (typeof args === 'string') ? JSON.parse(args) : (args || {});

const CONFIG = """

tail = """;

const idxs = (Array.isArray(A.idxs) && A.idxs.length)
  ? A.idxs
  : Array.from({ length: (Number(A.count) || 3) }, (_, i) => (Number(A.start) || 0) + i);

log(`science-build: delegating ${idxs.length} idxs to bank_pipeline -> [${idxs[0]}..${idxs[idxs.length-1]}]`);
const res = await workflow(
  { scriptPath: 'C:/Users/brand/Documents/PhilosophersQuest/bankbuild/bank_pipeline.wf.js' },
  { config: CONFIG, idxs }
);
return res;
"""

out_path = os.path.join(ROOT, "bankbuild", "science", "_build.wf.js")
with open(out_path, "w", encoding="ascii", newline="\n") as f:
    f.write(head + cfg_js + tail)
raw = open(out_path, "rb").read()
bad = [b for b in raw if b > 127 or (b < 32 and b not in (9, 10))]
ok_backtick = raw.count(b"`")
print(f"wrote {out_path}  {len(raw)} bytes | non-ascii/control: {len(bad)} | backticks: {ok_backtick}")
assert ok_backtick == 2 and not bad, "generation sanity check failed"
