"""CLI harness that re-hosts the bank pipeline WITHOUT the Workflow tool.

Byte-identical prompts to bankbuild/bank_pipeline.wf.js.  Each stage's prompt is written to a file;
the orchestrator (Claude) launches an Agent that reads the prompt, does the work, and writes the
result as JSON to a paired file.  This module wraps the Python side: prompt generation, mechGate,
and final wf-style output assembly for `bank.py integrate`.

USAGE (from the CLI orchestrator):
  python -m bankbuild.theology._cli_harness prompt_research     <idx>
  python -m bankbuild.theology._cli_harness prompt_author       <idx>
  python -m bankbuild.theology._cli_harness prompt_craft_judge  <idx>
  python -m bankbuild.theology._cli_harness prompt_adv_judge    <idx>
  python -m bankbuild.theology._cli_harness prompt_revise       <idx>  (auto-detects which stage)
  python -m bankbuild.theology._cli_harness prompt_coordinator  <idx1> [<idx2> ...]  (batch research+author+self-audit prompt)
  python -m bankbuild.theology._cli_harness mechgate            <idx>  (writes gate_flags.json)
  python -m bankbuild.theology._cli_harness apply_drops         <idx1> [<idx2> ...]  (drop still-flagged rungs from latest ladder + verdicts)
  python -m bankbuild.theology._cli_harness state               <idx>  (dump what stages have run)
  python -m bankbuild.theology._cli_harness finalize <idx1> [<idx2> ...]  (writes wf-style output)
"""
import json, os, sys, re, time

ROOT = r"C:\Users\brand\Documents\PhilosophersQuest"
sys.path.insert(0, os.path.join(ROOT, "bankbuild"))
from tellgate import gate as _tellgate_gate  # noqa: E402

SUBJECT = "theology"
CFG_PATH   = os.path.join(ROOT, "bankbuild", "subjects", "theology.json")
QUEUE_PATH = os.path.join(ROOT, "bankbuild", "theology", "_queue.json")
STATE_DIR  = os.path.join(ROOT, "bankbuild", "theology", "_cli_state")
os.makedirs(STATE_DIR, exist_ok=True)

# ---- config ----
CFG   = json.load(open(CFG_PATH, encoding="utf-8"))
VOICE = CFG.get("voice_rule", "")
FRAMING = CFG.get("framing", "")
TIERNOTE = CFG.get("tier_note", "")

# ---- state files (per-idx) ----
def state(idx, name): return os.path.join(STATE_DIR, f"{idx:04d}_{name}.json")
def prompt_file(idx, name): return os.path.join(STATE_DIR, f"{idx:04d}_{name}_prompt.md")

def _write_prompt(idx, name, prompt):
    p = prompt_file(idx, name)
    open(p, "w", encoding="utf-8", newline="\n").write(prompt)
    return p

def load_topic(idx):
    q = json.load(open(QUEUE_PATH, encoding="utf-8"))
    return q[idx]

# ============================================================================
# RULES prefix -- byte-identical to bank_pipeline.wf.js so future prompt-cache
# hits work if/when they're available.  If a rule needs changing, change BOTH
# this string and bankbuild/bank_pipeline.wf.js in the same commit.
# ============================================================================
def rules_prefix():
    return f"""THE BANK: a {SUBJECT} quiz bank a father is building for HIS OWN KIDS. {TIERNOTE}

CONTROLLING VOICE (the soul of THIS subject's answers):
{VOICE}

THE CRAFT RULES (each a hard requirement; a rung breaking ANY is FLAGGED):
1. LEAD WITH THE SUBJECT. Never open a stem on a dangling pronoun/possessive ("At her trial...", "When he...") before the named subject appears. The deck is SHUFFLED + timed -- the stem must parse in ONE forward pass; a player cannot re-read. Lead with the named subject, or a self-standing scene with no dangling reference.
2. CHOICE-FORMAT PARITY. All four choices structurally parallel -- similar length, same name-count, same grammatical shape. The answer must NEVER be the structural odd-one-out (the only dual-named, the only long one, the only full sentence, the only one with a date/number). No skim-tell.
3. NO LEXICAL/CATEGORY TELEGRAPH. No stem word that hands over the answer: not the answer's key noun, not a category word only the answer matches ("tree" when only the answer is a tree), not a verb revealing the mechanism ("sent an armorer to DIG for it" -> "buried"), not a tone-word matching only the answer. THREE recurring high-severity leaks to kill: (i) RESTATEMENT -- the answer must not restate a discriminating clause the stem already gave (stem "buried in the grandest tomb, beside William Pitt" -> answer "Westminster Abbey, beside William Pitt" is just an echo); (ii) TOPIC-NAME MATCH -- the answer must not be the topic's own name, a word from the topic title, or a name just taught in a lower rung (a "Ghana Empire" answer in a Ghana topic is pure name-matching); (iii) LONE STEM-ANCHOR -- the answer must not be the only choice tied to anything in the stem while the three distractors float free. The player must KNOW the answer, not deduce it from a stem word.
4. ECONOMY. Cut superlatives/qualifiers that add nothing ("her MOST FAMOUS sword" when she has one famous sword -> "her sword").
5. NO FALSE-FRIEND VOCAB. Don't use a word in an archaic/technical sense whose common MODERN meaning differs (medieval "doctors" = theologians reads as physicians to a kid; "clerk", "want" = lack, "suffer" = allow, "corn" = grain). Use the plain word.
6. TWO QUESTION SHAPES, NEVER THE COY HEDGE. Either (A) general stem + the ANSWER carries the full specific payoff, or (B) specific stem + a POINTED sub-question. NEVER the evasive middle that narrates the SHAPE of the answer ("something that would happen to her... naming WHERE it would strike").
7. DON'T FORCE A STORY/SCENARIO. If the scene-setting is awkward or the setup telegraphs the answer, the fact may not earn a rung -- pick a better fact. Don't cram a narrative around a fact until it reads wrong.
8. SCENE-SETTING MUST ORIENT. Locate the reader: who/what the subject is, what's at stake, why this moment matters -- not just name it.
9. EARN THE PAYOFF. When the answer's impressiveness depends on context (who the adversary was, why a detail is remarkable), BUILD that context into the stem so the answer LANDS. Don't assume the reader supplies the stakes.
10. THE ANSWER MUST ITSELF BE THE PAYOFF the controlling voice prizes (a wonder, a punchline, a recognition -- per the voice above), never a dead label/insignificant name. If the answer would be a dead name, FLIP: make the memorable THING the answer and the name supporting color. Fewer great rungs beat filler.
11. PAY OFF THE TEASE. If the stem promises a beat ("what he did NEXT made his name"), the ANSWER must deliver exactly that beat -- don't tease an action then ask a vaguer question with a label answer.
12. ACTIVE VOICE / ASSIGN RESPONSIBILITY. When a person did something -- especially to someone, or a wrong -- write it ACTIVE and NAME the actor ("her jailers took her clothes", not "her clothes had been taken"). Responsibility is core to the moral voice.
13. NO LOGICAL TELEGRAPH. Distractors must not be self-eliminating against a stem premise. Every distractor must be a live, plausible option given everything the stem says. ENUMERATION is the sharpest form: if the stem LISTS items that match the distractors, the answer becomes the only un-listed option (stem names "eternal law, human law, and divine law" -> "natural law" is the only choice the stem didn't name). Never enumerate the distractors in the stem.
14. STORY-IN-STEM + POINTED CLOSER + TEACH-BEFORE-TEST. Substantive content (named figures, dramatic specifics) lives in the STEM, not buried in context (context shows only on a wrong answer / review). The closing question must be POINTED + CONCRETE about something specific -- never a weasel closer ("what's the takeaway/lesson/significance/pattern?"). Don't assume a technical term the bank should be teaching -- introduce it inline or it is flagged.

VALUES: never impose a verdict on a genuinely contested moral/political/metaphysical question -- attribute the claim to a person ("X testified", "Y argued"), present competing views, do not adjudicate. {FRAMING}

LADDER STRUCTURE: one FACT per rung (a fact spent as stem scenery can't be a payoff again). Rungs slotted by CONCEPTUAL difficulty, roughly balanced across the tier_span with a real T1-T2 base. SELF-CONTAINED: each stem stands alone (full name on first reference, anchored scene) -- a kid hitting any rung cold can read it. DOWNWARD-ONLY scaffold: a stem may assume lower-tier facts but never reveal a same-or-higher-tier rung's answer. LEGEND labeled as legend.

FACTUAL INTEGRITY (non-negotiable -- this is for real children): every keyed answer must trace to the sourced fact sheet. NOTHING fabricated. If a fact isn't in the sheet, don't use it. Disputed/legendary facts are framed as legend or testimony."""

# ============================================================================
# schemas -- described inline in each prompt; every stage writes its result as
# JSON matching one of these shapes.
# ============================================================================
RESEARCH_SCHEMA = """{
  "topic_name": "<echo the topic's name>",
  "status": "ok" | "thin",
  "facts": [
    { "fact": "<one specific fact, ~1 sentence>",
      "source": "<real URL or named primary source you ACTUALLY consulted>",
      "difficulty": "easy" | "med" | "hard",
      "legend": true | false,
      "confidence": "high" | "medium" | "low" }
  ]
}"""

LADDER_SCHEMA = """{
  "rungs": [
    { "tier": 1..5,
      "stem": "<the question stem>",
      "choices": ["<A>", "<B>", "<C>", "<D>"],     # exactly 4
      "answer": "<must equal one of the four choices verbatim>",
      "context": "<post-answer enrichment + sources>",
      "legend": true | false }
  ]
}"""

VERDICTS_SCHEMA = """{
  "ladder_ok": true | false,
  "verdicts": [
    { "tier": <n>, "idx": <position in ladder>,
      "verdict": "keep" | "flag",
      "severity": "high" | "medium" | "low" | "none",
      "rules_flagged": ["rule 3 (restatement)", ...],
      "primary_flaw": "<one line>",
      "fix": "<concrete>" }
  ]
}"""

# ============================================================================
# stage prompts -- lifted verbatim (minus JS interpolation) from bank_pipeline.wf.js
# ============================================================================
def _read_topic_line(idx):
    return (f"STEP 1 -- read your topic spec (Python, do not modify): "
            f"`python -c \"import json;print(json.dumps(json.load(open(r'{QUEUE_PATH}',encoding='utf-8'))[{idx}]))\"`")

def _output_line(path):
    return (f"\n\n===== OUTPUT INSTRUCTIONS =====\n"
            f"Write your result as a single JSON object matching the schema above to this exact path:\n"
            f"  {path}\n"
            f"Use the Write tool.  ASCII-only JSON, no code fences, no prose outside the file.\n"
            f"After writing, reply with a one-line confirmation: `WROTE <basename>`.")

def prompt_research(idx):
    topic = load_topic(idx)
    out = state(idx, "research")
    body = f"""You are the RESEARCH stage of a {SUBJECT} quiz bank a father is building for HIS OWN KIDS. Accuracy is sacred.
{_read_topic_line(idx)}
It prints {{name, scope, framing_note, tier_span, depth, target_q, source}}. Non-ASCII appears as \\uXXXX escapes. Echo `name` back as `topic_name`.
STEP 2 -- use WebSearch/WebFetch on REAL sources to gather the most memorable, specific, RETELLABLE facts that fit this subject's controlling voice: named things, vivid actions, real quotes, striking specifics, primary-source human detail. Gather MORE than needed (about target_q + 5 gems) so the author can choose.
SOURCE PRIORITY (required): check **Grokipedia (grokipedia.com) FIRST** for every fact -- it is the primary, most-trusted reference; consult it before Wikipedia and prefer it whenever both cover a fact. Then corroborate and supplement with Wikipedia and other reputable primary sources. Cite the Grokipedia URL when it is your source.
For each fact: fact, source (a real URL/named primary source you ACTUALLY found), difficulty (easy=T1 .. hard=T5), legend (bool), confidence.
ANTI-HALLUCINATION (non-negotiable): every fact MUST trace to a real source you found. Do NOT invent or pad from memory. If you can't research to depth, set status='thin' and return only what you verified. Better thin than fabricated.

===== OUTPUT SCHEMA =====
{RESEARCH_SCHEMA}
{_output_line(out)}
"""
    return _write_prompt(idx, "research", body), out

def prompt_author(idx):
    topic = load_topic(idx)
    name = topic["name"]
    research = json.load(open(state(idx, "research"), encoding="utf-8"))
    out = state(idx, "ladder_v1")
    body = f"""{rules_prefix()}

=== AUTHOR STAGE ===
You are the AUTHOR of a {SUBJECT} quiz bank for a father's kids, applying EVERY rule above. Turn the SOURCED fact sheet into a voice-driven ladder for "{name}".
{_read_topic_line(idx)}
Use framing_note for stance/voice; depth sets length (deep = 10-15 rungs, standard = 3-5, mini = 1-3 standalone gems); author about target_q rungs across the tier_span.
SOURCED FACT SHEET -- use ONLY these facts, nothing from memory:
{json.dumps(research.get("facts", []))}

Author the ladder: pick the BEST gems, ONE fact per rung, slot by conceptual difficulty across the tier_span with a REAL T1-T2 base (~30%+). Each rung: tier, EXACTLY 4 choices, answer (== one choice verbatim), context (post-answer enrichment + the source), legend bool. If a fact can't make a clean rung, drop it.

FINAL SELF-AUDIT -- run on EVERY rung BEFORE returning; fix or drop any failure. Be ruthless:
1. PARITY: all 4 choices alike in length, name-count, grammar? Answer not the only long/dual-named/full-sentence/oddly-precise-number one?
2. STEM LEAK: any stem word hand over the answer (key noun; a category only it fits; a closing verb that pre-announces the answer type)? ALSO: does the answer RESTATE a clause already in the stem, or is it the TOPIC'S OWN NAME / a word just taught (name-matching)? Both are leaks -- re-key or reword.
3. LOGICAL ELIMINATION: every distractor stays LIVE? (a) stem negates/kills none; (b) CATEGORY MATCH -- if the stem names a category the answer belongs to, all four choices fit it; (c) no visual/mechanism description matching only the answer; (d) EFFECT/GOAL MATCH -- stem doesn't state the outcome only the answer achieves; (e) ENUMERATION -- stem doesn't LIST items matching the distractors, leaving the answer the only un-listed one. Fix by making distractors share the answer's category/effect or removing the cue.
4. CLOSER: final question POINTED + CONCRETE, never a weasel.
5. SCAFFOLD: does this rung STATE a number/name/fact another rung ASKS as its answer? Remove the leak.
Return ONLY rungs that pass all five.

===== OUTPUT SCHEMA =====
{LADDER_SCHEMA}
{_output_line(out)}
"""
    return _write_prompt(idx, "author", body), out

def _current_ladder_path(idx):
    """Return the newest ladder file for this idx (v1, v2, or v3)."""
    for name in ("ladder_v3", "ladder_v2", "ladder_v1"):
        p = state(idx, name)
        if os.path.exists(p): return p
    return None

def prompt_craft_judge(idx):
    topic = load_topic(idx)
    name = topic["name"]
    research = json.load(open(state(idx, "research"), encoding="utf-8"))
    ladder_p = _current_ladder_path(idx)
    ladder = json.load(open(ladder_p, encoding="utf-8"))
    out = state(idx, "verdicts_craft")
    body = f"""{rules_prefix()}

=== CRAFT JUDGE ===
You are the CRAFT JUDGE -- the last line of defense before these questions reach a child. Be STRICT; flag anything that breaks a rule above or isn't sourced. Topic: "{name}".
SOURCED FACTS (the ONLY allowed basis for any answer): {json.dumps(research.get("facts", []))}
LADDER TO JUDGE (idx = position in this array): {json.dumps(ladder.get("rungs", []))}
For EACH rung: verdict 'keep' or 'flag'. If flag: rules_flagged (rule numbers/labels), primary_flaw (one line), fix (concrete). ALSO fact-check: if the keyed answer is NOT supported by the sourced facts, FLAG ("factual integrity").
SEVERITY (every rung; 'none' for keeps). ALWAYS-HIGH: a factual error, a dead-name answer, an agent-hiding passive, a weasel closer, a contested-verdict imposed as fact, a restatement/topic-name/enumeration leak, OR a label/name/date answer under a payoff-carrying stem. Otherwise the EXPLOIT TEST: could a smart kid who never studied this RELIABLY pick the answer from the telegraph alone? YES -> MEDIUM; a stretch -> LOW.
Set ladder_ok = true ONLY if NO rung is flagged HIGH or MEDIUM (a couple LOW notes ok).

===== OUTPUT SCHEMA =====
{VERDICTS_SCHEMA}
{_output_line(out)}
"""
    return _write_prompt(idx, "craft_judge", body), out

def prompt_adv_judge(idx):
    topic = load_topic(idx)
    name = topic["name"]
    research = json.load(open(state(idx, "research"), encoding="utf-8"))
    ladder_p = _current_ladder_path(idx)
    ladder = json.load(open(ladder_p, encoding="utf-8"))
    # run mechGate on the current ladder
    gate_flags = mechgate_for(ladder.get("rungs", []))
    json.dump(gate_flags, open(state(idx, "gate_flags"), "w", encoding="utf-8"), indent=1)
    out = state(idx, "verdicts_adv")
    gate_line = (f"A DETERMINISTIC mechanical scanner already flagged these (verify each -- it is ~76% precise, so CONFIRM a real leak or clear it as a false positive on a legitimately vivid/named answer):\n{json.dumps(gate_flags)}"
                 if gate_flags else
                 "The mechanical scanner found nothing -- still hunt the SEMANTIC tells it cannot see.")
    body = f"""{rules_prefix()}

=== INDEPENDENT ADVERSARIAL RE-JUDGE ===
You are an INDEPENDENT, SKEPTICAL auditor. This {SUBJECT} ladder ALREADY PASSED a craft judge -- your job is to catch what that judge MISSED. Assume nothing is good; do not rubber-stamp. Topic: "{name}".
SOURCED FACTS: {json.dumps(research.get("facts", []))}
LADDER (idx = position): {json.dumps(ladder.get("rungs", []))}
{gate_line}
Hunt especially the tells a lenient judge waves through: RESTATEMENT (answer echoes a stem clause), ENUMERATION (stem lists the distractors), CATEGORY-MATCH (only the answer fits a category the stem names), EFFECT/GOAL-MATCH, Drama-Available (a label/number answer under a vivid stem), dead-name answers, weasel closers, agent-hiding passive, and any unsourced/false fact.
For EACH rung: verdict 'keep' or 'flag'; if flag: severity (high/medium/low) + rules_flagged + primary_flaw + fix. Be the adversary the first judge wasn't. ladder_ok = true ONLY if nothing is HIGH or MEDIUM.

===== OUTPUT SCHEMA =====
{VERDICTS_SCHEMA}
{_output_line(out)}
"""
    return _write_prompt(idx, "adv_judge", body), out

def prompt_revise(idx, kind):
    """kind is 'craft' or 'adv' -- picks which verdicts file to fold in, and where to write the revised ladder."""
    topic = load_topic(idx)
    name = topic["name"]
    research = json.load(open(state(idx, "research"), encoding="utf-8"))
    ladder_p = _current_ladder_path(idx)
    ladder = json.load(open(ladder_p, encoding="utf-8"))
    if kind == "craft":
        verdicts = json.load(open(state(idx, "verdicts_craft"), encoding="utf-8"))
        # write to ladder_v2 (post-craft-judge)
        out = state(idx, "ladder_v2")
    elif kind == "adv":
        verdicts = json.load(open(state(idx, "verdicts_adv"), encoding="utf-8"))
        # write to ladder_v3 (post-adv-judge)
        out = state(idx, "ladder_v3")
    else:
        raise ValueError(f"bad kind {kind}")
    flags = [v for v in verdicts.get("verdicts", []) if v.get("verdict") == "flag" and v.get("severity") in ("high", "medium")]
    body = f"""{rules_prefix()}

=== SURGICAL REVISE ===
Revise this {SUBJECT} ladder for "{name}", applying the rules above + the given fixes, using ONLY the sourced facts. Fix ONLY the flagged rungs; leave the others byte-identical.
SOURCED FACTS: {json.dumps(research.get("facts", []))}
CURRENT LADDER: {json.dumps(ladder.get("rungs", []))}
FLAGS TO FIX: {json.dumps(flags)}
Return the FULL ladder (the flagged rungs fixed, answer still == one of its 4 choices), leaving unflagged rungs byte-identical.
If a flagged rung CANNOT be cleanly fixed from the sourced facts -- a fabricated/unsupported claim with no good alternative, or a telegraph that only disappears by gutting the rung -- DROP that rung entirely rather than ship it flawed; returning FEWER rungs is correct. NEVER keep a rung with a known fabricated fact.
IMPORTANT: re-audit the WHOLE ladder against the rules + five-point self-audit, not only the listed flags -- a fix must not leave a sibling telegraph or introduce a new one (don't make the new answer the only long choice; don't seed the answer word in the stem).

===== OUTPUT SCHEMA =====
{LADDER_SCHEMA}
{_output_line(out)}
"""
    stage_name = "revise_craft" if kind == "craft" else "revise_adv"
    return _write_prompt(idx, stage_name, body), out

# ============================================================================
# COORDINATOR prompt -- one agent does research + author + self-critique + revise for N topics
# ============================================================================
def prompt_coordinator(idxs):
    """Build one big prompt telling an agent to run the research + author + self-audit pipeline
    for each idx in `idxs` (sequentially inside its own context), writing per-topic ladder_v1.json
    files.  Uses the SAME RULES prefix as the individual stages, so future prompt-cache hits work.

    The coordinator does NOT do the adversarial-judge pass -- that must run in a separate fresh
    subagent per topic to preserve the "independent adversary" quality property.
    """
    topics = [(i, load_topic(i)) for i in idxs]
    # write the per-topic research + author output paths so the agent knows exactly where to write
    plan_rows = []
    for i, t in topics:
        plan_rows.append({
            "idx": i,
            "name": t["name"],
            "scope": t["scope"],
            "framing_note": t["framing_note"],
            "tier_span": t["tier_span"],
            "depth": t["depth"],
            "target_q": t["target_q"],
            "research_out": state(i, "research"),
            "ladder_out":   state(i, "ladder_v1"),
        })
    plan = json.dumps(plan_rows, indent=1)
    out = os.path.join(STATE_DIR, f"coordinator_batch_{int(time.time())}.md")
    body = f"""{rules_prefix()}

=== BATCH COORDINATOR ===
You own the RESEARCH + AUTHOR + STRICT SELF-CRITIQUE + REVISE-UNTIL-CLEAN pipeline for a batch of
{len(idxs)} {SUBJECT} topics.  You do this SEQUENTIALLY in your own context (do NOT try to spawn
subagents; work through each topic yourself with WebSearch/WebFetch/Read/Write).  A separate
adversarial judge will run after you return -- your job is to hand over ladders that are already
as clean as strict self-critique can make them.

=== BATCH PLAN ===
{plan}

=== FOR EACH TOPIC (in order), DO THIS ===

STEP 1  RESEARCH (WebSearch + WebFetch):
  - Use REAL sources.  **Grokipedia (grokipedia.com) FIRST** for every fact -- prefer it whenever
    it covers a fact, then corroborate with Wikipedia and other reputable primary sources.
  - Gather about `target_q + 5` gems -- specific, memorable, RETELLABLE facts (named things, vivid
    actions, real quotes, primary-source detail).  Better THIN than fabricated.
  - Write the fact sheet to the `research_out` path (Write tool), matching this schema:
{RESEARCH_SCHEMA}

STEP 2  AUTHOR the ladder from ONLY those sourced facts:
  - ~`target_q` rungs across the `tier_span`, real T1-T2 base (~30%+).
  - Each rung: tier, EXACTLY 4 choices, answer verbatim == one choice, context, legend bool.
  - Follow the CONTROLLING VOICE and all 14 craft rules above.

STEP 3  STRICT FIVE-POINT SELF-AUDIT on EVERY rung, iterate up to 2 revise passes:
  1. PARITY: all 4 choices alike in length, name-count, grammar?  Answer not the odd-one-out?
  2. STEM LEAK: any stem word hand over the answer?  RESTATEMENT (answer echoes a stem clause)?
     TOPIC-NAME MATCH (answer is the topic's own name)?
  3. LOGICAL ELIMINATION: every distractor stays LIVE?  No SELF-ELIMINATION, no CATEGORY-MATCH,
     no EFFECT/GOAL-MATCH, no ENUMERATION (stem listing items that match distractors).
  4. CLOSER: final question POINTED + CONCRETE, never a weasel ("what's the takeaway?").
  5. SCAFFOLD: no rung STATES a number/name/fact another rung ASKS as its answer.
  Fix or DROP any rung that can't pass all five.  Fewer clean rungs beat filler.
  Also apply the DETERMINISTIC MECHANICAL GATE mentally: if the answer is a short LABEL, check
  no distinctive answer word ≥6 chars appears in the stem AND in no distractor; check the answer
  text does not appear verbatim inside the stem.

STEP 4  Write the final ladder JSON to the `ladder_out` path (Write tool), matching:
{LADDER_SCHEMA}

=== HARD REQUIREMENTS ===
- Do NOT skip topics.  If web research is thin for one, write a `status:'thin'` research file and
  skip the author step for that topic (the adversarial phase will treat it as needs_review).
- Do NOT fabricate facts.  Every keyed answer must trace to your sourced fact sheet.
- Do NOT copy facts between topics.
- ASCII-only in every JSON file.  No prose outside the file bodies.

=== WHEN YOU FINISH ===
Reply with one line per topic in this exact form:
  `OK <idx> <n_rungs>`     -- topic authored, N rungs
  `THIN <idx>`             -- research was thin, no author attempted
Then a final `DONE` line.
"""
    open(out, "w", encoding="utf-8", newline="\n").write(body)
    return out

# ============================================================================
# apply_drops -- deterministic drop of still-flagged rungs after Pass B round 2
# (mirrors the drop rule from bankbuild/_detell.wf.js).  Reads the latest verdicts_adv.json,
# drops rungs still flagged high/medium from the latest ladder file, marks adv verdicts as clean.
# ============================================================================
def apply_drops(idxs):
    for idx in idxs:
        ladder_p = _current_ladder_path(idx)
        adv_p = state(idx, "verdicts_adv")
        if not (ladder_p and os.path.exists(adv_p)):
            print(f"  idx {idx}: SKIP (no ladder or no adv verdicts)"); continue
        ladder = json.load(open(ladder_p, encoding="utf-8"))
        adv = json.load(open(adv_p, encoding="utf-8"))
        flags = [v for v in adv.get("verdicts", []) if v.get("verdict") == "flag" and v.get("severity") in ("high", "medium")]
        drop = sorted({f["idx"] for f in flags}, reverse=True)
        rungs = ladder.get("rungs", [])
        for d in drop:
            if 0 <= d < len(rungs):
                rungs.pop(d)
        json.dump({"rungs": rungs}, open(ladder_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump({"ladder_ok": True, "verdicts": [{"tier": r["tier"], "idx": j, "verdict": "keep", "severity": "none",
                                                     "rules_flagged": [], "primary_flaw": "", "fix": ""}
                                                    for j, r in enumerate(rungs)]},
                  open(adv_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  idx {idx}: dropped {len(drop)} at {drop} -> {len(rungs)} rungs final")

# ============================================================================
# mechGate (Python)
# ============================================================================
def mechgate_for(rungs):
    """Return a list of gate flags for these rungs, in the wf-style shape."""
    out = []
    for i, r in enumerate(rungs or []):
        for f in _tellgate_gate(r):
            out.append({
                "tier": r.get("tier"), "idx": i,
                "pattern": f["pattern"], "flaw": f["detail"],
            })
    return out

# ============================================================================
# state introspection + finalization
# ============================================================================
def dump_state(idx):
    files = sorted(os.path.basename(p) for p in os.listdir(STATE_DIR) if p.startswith(f"{idx:04d}_") and p.endswith(".json"))
    print(f"idx {idx} state files: {len(files)}")
    for f in files:
        p = os.path.join(STATE_DIR, f)
        try:
            j = json.load(open(p, encoding="utf-8"))
            n = "?"
            if isinstance(j, dict):
                if "facts" in j: n = f"{len(j['facts'])} facts (status={j.get('status')})"
                elif "rungs" in j: n = f"{len(j['rungs'])} rungs"
                elif "verdicts" in j:
                    fl = [v for v in j["verdicts"] if v.get("verdict") == "flag"]
                    hi = [v for v in fl if v.get("severity") == "high"]
                    md = [v for v in fl if v.get("severity") == "medium"]
                    n = f"{len(j['verdicts'])} verdicts ({len(hi)} high, {len(md)} medium)"
            elif isinstance(j, list): n = f"{len(j)} items"
            print(f"  {f}  ->  {n}")
        except Exception as e:
            print(f"  {f}  ->  ERROR {e}")

def _final_status(idx):
    """Compute status/notes/unresolved from the highest-numbered ladder + latest adv verdicts.
    Rules (mirror bank_pipeline.wf.js buildLadder):
      - status='passed'          if adv judge has 0 high + 0 medium
      - status='needs_review'    otherwise (with unresolved flags summarised)
      - status='error'           if research is thin or ladder is empty
    """
    research_p = state(idx, "research")
    if not os.path.exists(research_p):
        return {"status": "error", "unresolved": ["no-research"], "notes": [], "rounds": 0, "rungs": []}
    research = json.load(open(research_p, encoding="utf-8"))
    if research.get("status") == "thin" or len(research.get("facts", [])) < 2:
        return {"status": "needs_review", "unresolved": ["thin-research"], "notes": [], "rounds": 0, "rungs": []}
    ladder_p = _current_ladder_path(idx)
    if not ladder_p:
        return {"status": "needs_review", "unresolved": ["author-failed"], "notes": [], "rounds": 0, "rungs": []}
    ladder = json.load(open(ladder_p, encoding="utf-8"))
    rungs = ladder.get("rungs", [])
    if not rungs:
        return {"status": "needs_review", "unresolved": ["empty-ladder"], "notes": [], "rounds": 0, "rungs": []}
    # count how many revise stages happened
    rounds = sum(1 for name in ("ladder_v2", "ladder_v3") if os.path.exists(state(idx, name)))
    rounds += 1  # +1 for the primary judge pass
    adv_p = state(idx, "verdicts_adv")
    if not os.path.exists(adv_p):
        # adv judge didn't run yet
        return {"status": "needs_review", "unresolved": ["adv-judge-not-run"], "notes": [], "rounds": rounds, "rungs": rungs}
    adv = json.load(open(adv_p, encoding="utf-8"))
    flags = [v for v in adv.get("verdicts", []) if v.get("verdict") == "flag"]
    high = [v for v in flags if v.get("severity") == "high"]
    med  = [v for v in flags if v.get("severity") == "medium"]
    low  = [v for v in flags if v.get("severity") == "low"]
    if not high and not med:
        return {"status": "passed", "unresolved": [],
                "notes": [f"T{v.get('tier')}(low):{v.get('primary_flaw')}" for v in low],
                "rounds": rounds, "rungs": rungs}
    return {"status": "needs_review",
            "unresolved": [f"T{v.get('tier')}({v.get('severity')}):{v.get('primary_flaw')}" for v in high + med],
            "notes": [], "rounds": rounds, "rungs": rungs}

def finalize(idxs):
    """Write the wf-style output JSON that bank.py integrate expects."""
    results = []
    for idx in idxs:
        topic = load_topic(idx)
        research_p = state(idx, "research")
        sources = []
        if os.path.exists(research_p):
            r = json.load(open(research_p, encoding="utf-8"))
            sources = list({f["source"] for f in r.get("facts", []) if f.get("source")})[:12]
        st = _final_status(idx)
        results.append({
            "idx": idx,
            "name": topic["name"],
            "status": st["status"],
            "ladder": {"rungs": st["rungs"]},
            "n_rungs": len(st["rungs"]),
            "rounds": st["rounds"],
            "unresolved": st["unresolved"],
            "notes": st["notes"],
            "sources": sources,
        })
    wrapper = {
        "subject": SUBJECT,
        "start": min(idxs), "count": len(idxs),
        "results": results,
    }
    ts = int(time.time())
    out = os.path.join(STATE_DIR, f"cli_batch_{ts}.json")
    json.dump(wrapper, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = sum(1 for r in results if r["status"] == "passed")
    nr = sum(1 for r in results if r["status"] == "needs_review")
    print(f"WROTE {out}")
    print(f"batch: {ok} passed, {nr} needs_review, of {len(idxs)}")
    for r in results:
        print(f"  idx {r['idx']:3d}: {r['status']:14s} rungs={r['n_rungs']:2d}  {r['name'][:52]}")
    # Auto-integrate against the theology subject so we never accidentally point
    # bank.py integrate at the wrong queue (idx collides across subjects).
    import subprocess
    print(f"--- auto-integrating against {SUBJECT} ---")
    subprocess.run(["python", "-m", "bankbuild.bank", "integrate", out, f"--subject={SUBJECT}"], check=True)

# ============================================================================
# CLI
# ============================================================================
def _print_prompt_path(prompt_p, out_p):
    print(f"PROMPT_FILE: {prompt_p}")
    print(f"OUTPUT_FILE: {out_p}")

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "prompt_research":
        _print_prompt_path(*prompt_research(int(sys.argv[2])))
    elif cmd == "prompt_author":
        _print_prompt_path(*prompt_author(int(sys.argv[2])))
    elif cmd == "prompt_craft_judge":
        _print_prompt_path(*prompt_craft_judge(int(sys.argv[2])))
    elif cmd == "prompt_adv_judge":
        _print_prompt_path(*prompt_adv_judge(int(sys.argv[2])))
    elif cmd == "prompt_revise_craft":
        _print_prompt_path(*prompt_revise(int(sys.argv[2]), "craft"))
    elif cmd == "prompt_revise_adv":
        _print_prompt_path(*prompt_revise(int(sys.argv[2]), "adv"))
    elif cmd == "prompt_coordinator":
        p = prompt_coordinator([int(x) for x in sys.argv[2:]])
        print(f"PROMPT_FILE: {p}")
    elif cmd == "apply_drops":
        apply_drops([int(x) for x in sys.argv[2:]])
    elif cmd == "mechgate":
        idx = int(sys.argv[2])
        ladder = json.load(open(_current_ladder_path(idx), encoding="utf-8"))
        f = mechgate_for(ladder.get("rungs", []))
        p = state(idx, "gate_flags")
        json.dump(f, open(p, "w", encoding="utf-8"), indent=1)
        print(f"WROTE {p}  ({len(f)} flags)")
    elif cmd == "state":
        dump_state(int(sys.argv[2]))
    elif cmd == "finalize":
        finalize([int(x) for x in sys.argv[2:]])
    else:
        print(f"unknown command: {cmd}"); print(__doc__); sys.exit(1)

if __name__ == "__main__":
    main()
