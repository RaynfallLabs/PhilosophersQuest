"""CLI-harness audit driver for the SCIENCE bank (moral + tone).

Forks the RUBRICS from geography's _moral_audit.wf.js and _tone_audit.wf.js and rehosts them
for the Agent-tool CLI harness (no Workflow tool). Same batched pattern: one agent per BATCH
ladders, returns per-ladder verdicts.

USAGE (from the CLI orchestrator):
  python -m bankbuild.science._cli_audit prompt <moral|tone> [--batch=5] [id1 id2 ...]
      -> generates per-batch prompt files at _cli_state/audit_<rubric>_batchNNN.md and
         empty verdict files at _cli_state/audit_<rubric>_batchNNN.json (agent overwrites).
         If no ids given, audits ALL ladders in ladders/.

  python -m bankbuild.science._cli_audit aggregate <moral|tone>
      -> merges every _cli_state/audit_<rubric>_batchNNN.json, prints a summary +
         flagged list, writes _cli_state/audit_<rubric>_all.json.

The Agent prompt tells the auditor to write EXACTLY {"audits":[{...per ladder...}]} to the
paired json path. One agent = one batch.
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bank import paths  # noqa: E402

SUBJECT = "science"
P = paths(SUBJECT)
LAD = P["LAD"]
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_cli_state")
os.makedirs(STATE, exist_ok=True)


LANESTRICT_RUBRIC = """LANE-STRICT AUDIT for the SCIENCE bank. Sole question: is this ladder actually SCIENCE, or is it history/politics/law with a scientific pedigree used as a fig leaf?

A rung is SCIENCE if its ANSWER is one of:
  - a scientific mechanism, principle, or law (how something works, what the physics/biology/chemistry does)
  - an experimental method, control, measurement, calibration, or reasoning move (how we know)
  - a scientific finding, observation, dataset value, or reasoning correction (what the data showed / what the wrong theory got wrong)
  - a scientist's technique, insight, error, or specific reasoning step (the doing of science)
  - a corrected misconception with a testable/reasoned counter (science-as-self-correcting)

A rung is NOT SCIENCE (flag as lane-drift) if its ANSWER is:
  - a Holocaust/war/genocide/killing-operation fact: officials by name, killing-centre lists, death tolls used as trivia, wartime bureaucracy, chain-of-command, backdated letters, safe contents, sermons, camp code names, secret-police operations
  - a legal/court/statute fact: SCOTUS holdings, dissents, court names, agency-attorney identities, statutory ceilings, program payout totals, FOIA outcomes, congressional acts by title/section, presidential signing statements, judicial procedural details
  - a media/political-movement fact: think-tank founding stories, book titles by non-scientists, essay authors, initiative launch dates, movement code names, town names of political gatherings, membership rolls, PR statements
  - a biographical/social-history fact used as trivia: first-woman-to-X, Nobel-prize-count, address of an office, town-of-founding, membership numbers
  - an administrative fact: agency names, program totals, filing counts, department reorganizations
  - Nazi-terminology or period jargon used as the payoff: Wilde Euthanasie, Sonderbehandlung, Endloesung, Erbgesundheitsgerichte, etc.

CRITICAL: eugenics/Lysenko/Tuskegee/Guatemala/MKUltra CAN be legitimate science bank topics IF the ANSWERS are about the (bad) science: what family-pedigree charts got wrong, how Lysenko's vernalization claim broke experimentally, what a controlled trial would have shown, how a hypothesis was constructed and defended, what a correct experiment would look like. Flag when the answers are instead about killing operations, court rulings, officials, dates, addresses, and political mechanics.

For each RUNG in the ladder give a per-rung verdict (science / not-science). For the LADDER give:
  - science_rungs = count of rungs that are legitimate science
  - drift_rungs = count of rungs that are lane-drift
  - verdict = 'keep' (>= 70% science), 'trim' (mixed - keep only science rungs), or 'delete' (< 30% science - not really a science ladder)
  - recommendation = one-line rationale
  - keep_idxs = if 'trim', the list of rung indices to KEEP

Do NOT flag a ladder just because its TOPIC is stance-heavy. Flag only on the SUBSTANCE of the rungs' answers."""


MORAL_RUBRIC = """THE MORAL VISION for the SCIENCE bank (docs/quiz/moral_vision.md + bankbuild/subjects/science.json + feedback-science-voice + feedback-stance-vs-neutral). The bank is a Discovery/TEST-IT-YOURSELF wonder-tour of how humans figured things out. It is NOT neutral where moral_vision commits it, but it never WARPS a topic to force a stance. Science is a moral realist: dissent-is-the-tradition; institutional capture is nameable; scientific fraud and dark chapters (eugenics/Lysenko/Tuskegee/Guatemala) told plainly with FULL depth; vaccines SCRUTINIZED not celebrated (mechanism real, PR contested; RFK/Bhattacharya/GBD have moral weight); COVID origins/lockdowns/mandates honest; WEF/pharma/agency-capture named where evidence supports it. Score the ladder for VIOLATIONS of these:

1. §18 LANE / ADJACENCY DRIFT (moral_vision §6; SHARED_PRINCIPLES §18) -- THE #1 STRUCTURAL CHECK. This bank is about the SCIENCE: the mechanism, the discovery, the experiment, the reversal, the how-we-know. FLAG a rung whose real SUBSTANCE is an adjacent layer and whose ANSWER is not a science fact: (a) HISTORY/POLITICS -- a war/regime/treaty/electoral-politics answer keyed as the payoff (belongs to history) -> HIGH if answer IS the political fact, MEDIUM if it dominates; (b) LANE-BORDER -- an ANSWER that is a creature's biology/anatomy (animal bank), food chemistry/recipe/ingredient (cooking), a place's landscape/culture as scenery (geography), pure philosophy-of-science seminar (philosophy), pure AI content (AI bank) -> FLAG MEDIUM. Science AT a place (Krakatoa's pressure wave; the Oklo natural reactor) is FINE when the answer is the SCIENCE mechanism. Discovery stories anchored on a person are FINE.

2. VACCINE STANCE (feedback-science-voice, load-bearing). Mechanism (how a vaccine trains the immune system; adjuvants; cold-chain physics) stated as SETTLED biology is CORRECT. VIOLATION: (a) uncritical CDC/WHO/Pharma PR keyed as the whole truth ('vaccines are unequivocally safe and effective' as a stem premise); (b) safety-signal minimization keyed as fact where the actual dispute is live (VAERS underreporting; myocarditis signal in young men; the pediatric COVID risk-benefit calculus); (c) SYMMETRIC violation: outright anti-vax as fact when the mechanism/history IS settled (smallpox vaccine ended smallpox; polio dropped precipitously). The bank's voice: mechanism CELEBRATED where settled, PR SCRUTINIZED where contested; RFK/Bhattacharya/GBD are treated as serious scientists, not fringe.

3. INSTITUTIONAL CAPTURE / DISSENT-IS-THE-TRADITION (feedback-stance-vs-neutral). Named institutional capture written on the record is FACT, not conspiracy: Lysenko, replication crisis, Bem/PNAS, TNI/DGB, gain-of-function funding, EcoHealth, Fauci emails, Cochrane's Tom Jefferson on masks, the Great Barrington Declaration, RFK on autism, Bhattacharya on Stanford censorship, GBD signatories smeared. VIOLATION: (a) whitewashing named capture ('the scientific consensus is unified' where a signed dissenting document literally exists); (b) SYMMETRIC violation: manufactured-dissent framing where the science actually is settled (evolution, age of the universe, germ theory); (c) treating dissenting scientists as fringe/crank when they're serious credentialed voices.

4. DARK CHAPTERS -- FULL DEPTH, no whitewashing (moral_vision §3, §9; feedback-moral-vision-substantive). Eugenics (Buck v. Bell, Nazi Rassenhygiene, US sterilization programs, Sanger's stated views), Lysenko (starved millions to protect a bad theory), Tuskegee (40 years untreated syphilis in black men), Guatemala 1946 (US infected mental patients + prisoners with STDs), Unit 731, Willowbrook hepatitis, radiation experiments on kids, MKUltra. Full sourced fact, no scare-quoting, no both-sides-were-equally-bad flattening, no 'oh but they meant well' minimization. VIOLATION: any of the above softened. Honest telling = CORRECT.

5. COVID / PANDEMIC (feedback-stance-vs-neutral, load-bearing). Lab-leak treated as SERIOUS possibility not a debunked conspiracy (Proximal Origin was later shown to be politically constructed; Alina Chan/Baltimore/Ebright/DRASTIC did the work); lockdown harms (school closures, deaths of despair, economic destruction, missed cancer screenings) stated as real cost, not 'a small price'; vaccine mandate ethics (natural-immunity dismissal, coercion of the healthy young) presented honestly; ivermectin/HCQ meta-analyses cited without state-authority sneer; Trusted News Initiative / Twitter Files as documented information-suppression. VIOLATION: any of these swallowed by mainstream-media narrative as-fact.

6. CELEBRATED, done HONESTLY (moral_vision §1). Western scientific achievement (the Scientific Revolution, the Copernican-Kepler-Galileo-Newton chain, Faraday/Maxwell, the Michelson-Morley precision, Curie/Meitner/Feynman/Watson-Crick), the free-inquiry tradition, the culture of published-and-open peer review at its best. CELEBRATED. VIOLATION: (a) SELF-LOATHING anti-Western frame keyed as fact ('science is Eurocentric colonialism'); (b) TRIUMPHALIST puffery erasing the fraud/failure/dead-ends; both symmetric. Honest celebration with the honest costs = CORRECT.

7. NO CLIMATE ALARMISM, NO CLIMATE DENIALISM. The physics (CO2 as GHG, radiative forcing, the temperature record, ice cores, the Keeling curve, ocean acidification chemistry) is SETTLED SCIENCE stated with wonder. The POLICY and the ATTRIBUTION-OF-EVENTS layer is contested and stays neutral. VIOLATION: (a) 'climate change is destroying X' catastrophe framing as fact, a Greta-style doom-sermon, blaming a modern political side; SYMMETRICALLY (b) 'it's all a hoax / CO2 is plant food, no problem' denial keyed as fact when the physics is settled.

8. ACCURACY-STANCE / ANTI-PATTERN. Fabricated result/date/attribution keyed as fact -> HIGH; a LEGEND (Newton's apple hitting his head; Einstein failed math; the 'lone genius' myth around any discovery) keyed as settled fact -> FLAG; retracted/failed-to-replicate work keyed as still-standing -> FLAG; 'TIL: X is secretly bad/good' reveal-staging of honest history -> FLAG.

CRITICAL GUARD -- DO NOT OVER-FLAG: settled mechanism celebrated with wonder, honest dark-chapter history told plainly, vaccine mechanism as biology, dissent named as tradition, climate physics as settled science, Western achievement honestly celebrated, and TEST-IT-YOURSELF rungs (kitchen experiments, invitations to verify) are all CORRECT. Flag only genuine violations above. The #1 catches: LANE DRIFT (rule 1), VACCINE-PR UNCRITICAL (rule 2), CAPTURE-WHITEWASHING (rule 3)."""


TONE_RUBRIC = """You are reviewing a SCIENCE quiz bank a father built for HIS OWN KIDS (ages ~10-14), as a careful PARENT would. The bank is a wonder-tour of how science works: mechanism, discovery, reversal, mystery, TEST-IT-YOURSELF. It honestly covers dark chapters: eugenics, Lysenko, Tuskegee, Guatemala 1946, Unit 731, MKUltra, radiation experiments, Chernobyl, Bhopal, thalidomide, ether-frolic surgical deaths, the plague, Fleming's germs, animal experiments (Weismann's mice, Pavlov's dogs), autopsy findings. Honest science and honest history, told PLAINLY and in the THIRD person, is expected and STAYS. Flag a rung ONLY for a genuine TONE / APPROPRIATENESS problem below:

1. GRATUITOUSLY GRAPHIC / GRUESOME WORDING (the priority). Human remains, animal experiments, disease pathology, industrial deaths are real parts of science history. Stated matter-of-factly they are FINE (Tuskegee left men untreated; Willowbrook infected disabled children with hepatitis; the Radium Girls' jaws crumbled). FLAG ONLY wording that is gratuitously graphic, lingering, or nightmarish BEYOND what the science fact needs: dwelling on bodies/gore/suffering with relish, body-horror detail for its own sake. The test: would a parent wince at the WORDING, not at the FACT that thalidomide caused limb malformations? (medium; high only if genuinely gruesome for a kid).

2. SUFFERING / ATROCITY STAGED AS ENTERTAINMENT. Mentioning an atrocity as fact is OK (Unit 731 vivisection; Nazi eugenics; MKUltra dosings; Tuskegee). FLAG a rung that stages medical torture, human experimentation, or forced sterilization as a fun/cool 'did you know', treats it with relish or spectacle-appeal, uses a smug/glib voice about real suffering, OR builds an ANSWER SET that makes a kid weigh atrocities against each other to score a point. (medium; high if it treats mass suffering as entertainment).

3. CONDESCENDING / SNEERING TONE. Scientists, dissenters, ordinary people, and religious traditions must be presented STRAIGHT. FLAG a rung that mocks (a) a dissenting scientist as a crank; (b) a religious or folk-medicine tradition ('primitive belief', scare-quoted; 'people used to think'); (c) a historical figure for not knowing what we now know (Galen, Hippocrates, Aristotle sneered at rather than shown as pioneers); (d) modern non-mainstream voices (RFK, Bhattacharya, McCullough) dismissed as fringe/nut. (medium; high if it demeans a living person or living tradition). Honest disagreement, honestly stated, is CORRECT.

4. KID-APPROPRIATENESS. (a) Anything sexual, crude, or otherwise off-limits for a 10-14 kid (Sanger-style eugenic argumentation about 'unfit' reproduction stated blithely, sexually explicit historical medicine detail). (b) Gross-out overload (rot, remains, pus, disease) in gratuitously graphic lingering detail beyond the science fact. (c) Content that would frighten or disturb a child out of proportion to teaching the science (Cotard's delusion detail; horror-movie framing of a real disease). FLAG.

5. DISTURBING-OUT-OF-CONTEXT. The deck is SHUFFLED; a stem read cold should not land as menacing, gruesome, self-harm-adjacent, or creepy toward the reader in a way unrelated to teaching the science. FLAG a stem that reads wrong out of context.

CRITICAL GUARD -- DO NOT OVER-FLAG: honest dark-chapter history stated PLAINLY and in the THIRD person (Tuskegee, Guatemala, eugenics, Lysenko, Chernobyl, medical fraud), honest wonder at real achievement, matter-of-fact disease/anatomy/physics content, and TEST-IT-YOURSELF kitchen experiments are ALL EXPECTED and must STAY. You are flagging gratuitous GORE, suffering-as-fun, sneering TONE, and kid-inappropriate WORDING -- NOT subject matter. When unsure, do NOT flag. Most ladders will be clean.

For each flagged rung give idx + rule(1-5) + severity + one concrete line + a one-line fix suggestion."""


def all_ladder_ids():
    return sorted(
        os.path.splitext(os.path.basename(f))[0]
        for f in glob.glob(os.path.join(LAD, "*.json"))
    )


def read_ladder_for_audit(lid, include_context):
    d = json.load(open(os.path.join(LAD, lid + ".json"), encoding="utf-8"))
    rungs = []
    for r in d.get("rungs", []):
        rung = {
            "tier": r.get("tier"),
            "stem": r.get("stem", ""),
            "choices": r.get("choices", []),
            "answer": r.get("answer", ""),
        }
        if include_context:
            rung["context"] = r.get("context", "")
        rungs.append(rung)
    out = {"name": d.get("name", "?"), "rungs": rungs}
    if include_context:
        out["strand"] = d.get("strand")
    return out


def cmd_prompt(rubric, batch, ids):
    if rubric not in ("moral", "tone", "lanestrict"):
        print("rubric must be moral, tone, or lanestrict")
        return
    if not ids:
        ids = all_ladder_ids()

    include_context = rubric == "moral"
    if rubric == "moral":
        rubric_text = MORAL_RUBRIC
    elif rubric == "tone":
        rubric_text = TONE_RUBRIC
    else:
        rubric_text = LANESTRICT_RUBRIC
    kind = {
        "moral": "moral-vision auditor",
        "tone": "tone/appropriateness reviewer",
        "lanestrict": "lane-strict science-vs-history auditor",
    }[rubric]
    subject_frame = (
        "SCIENCE quiz bank a father is building for his kids"
        if rubric == "moral"
        else "kids' SCIENCE quiz bank"
    )
    if rubric == "lanestrict":
        schema_hint = (
            '{"audits":[{"id":"...","verdict":"keep|trim|delete",'
            '"science_rungs":N,"drift_rungs":N,"keep_idxs":[...optional...],'
            '"recommendation":"one-line"}]}'
        )
    else:
        schema_hint = (
            '{"audits":[{"id":"...","verdict":"clean|flag","worst_severity":"none|low|medium|high",'
            '"flags":[{"idx":N,"rule":"1..8" or "1..5","severity":"low|medium|high","detail":"one line"'
        )
        if rubric == "tone":
            schema_hint += ',"fix":"one-line fix"'
        schema_hint += '}],"note":"one-line summary"}]}'

    groups = [ids[i : i + batch] for i in range(0, len(ids), batch)]

    print(f"rubric={rubric} batch={batch} ladders={len(ids)} batches={len(groups)}")
    for bidx, group in enumerate(groups):
        # Build the ladder-data blob inline (no python subshells for the auditor to run).
        blocks = []
        for k, lid in enumerate(group):
            data = read_ladder_for_audit(lid, include_context)
            blocks.append(
                f'  LADDER {k + 1} (id="{lid}"):\n'
                + json.dumps(data, ensure_ascii=True, indent=1)
            )
        reads = "\n\n".join(blocks)

        prompt = (
            f"You are an INDEPENDENT {kind} for a {subject_frame}. Review {len(group)} ladders --"
            f" give EACH its own full, independent review.\n\n"
            f"STEP 1 -- LADDER DATA (already inlined below; do NOT modify):\n{reads}\n\n"
            f"{rubric_text}\n\n"
            f"Audit EVERY rung of EVERY ladder. Return one audit object PER LADDER"
            f" ({len(group)} total), each carrying its own id. worst_severity = highest among"
            f" that ladder's flags ('none' if clean); verdict = 'flag' if any high/medium else"
            f" 'clean'; note = one line. Do not skip or merge ladders.\n\n"
            f"OUTPUT: write EXACTLY this JSON to"
            f' _cli_state/audit_{rubric}_batch{bidx:03d}.json:\n'
            f"  {schema_hint}\n\n"
            f'IMPORTANT: escape embedded double-quotes as \\" or use single quotes so JSON parses.'
            f" ASCII-only."
        )

        pfile = os.path.join(STATE, f"audit_{rubric}_batch{bidx:03d}.md")
        with open(pfile, "w", encoding="utf-8") as f:
            f.write(prompt)
    print(f"wrote {len(groups)} prompt files to _cli_state/audit_{rubric}_batch*.md")
    print(
        f"outputs expected at _cli_state/audit_{rubric}_batch000.json .. batch{len(groups)-1:03d}.json"
    )


def cmd_aggregate(rubric):
    if rubric not in ("moral", "tone", "lanestrict"):
        print("rubric must be moral, tone, or lanestrict")
        return
    files = sorted(glob.glob(os.path.join(STATE, f"audit_{rubric}_batch*.json")))
    all_audits = []
    missing = 0
    for f in files:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print(f"  PARSE-FAIL {os.path.basename(f)}: {e}")
            missing += 1
            continue
        audits = d.get("audits") if isinstance(d, dict) else d
        if not audits:
            missing += 1
            continue
        all_audits.extend(audits)

    if rubric == "lanestrict":
        flagged = [a for a in all_audits if a.get("verdict") in ("trim", "delete")]
    else:
        flagged = [a for a in all_audits if a.get("verdict") == "flag"]
    outpath = os.path.join(STATE, f"audit_{rubric}_all.json")
    json.dump(
        {"rubric": rubric, "audited": len(all_audits), "flagged": len(flagged), "results": all_audits},
        open(outpath, "w", encoding="utf-8"),
        ensure_ascii=True,
        indent=1,
    )
    print(
        f"audit_{rubric}: {len(all_audits)} audited, {len(flagged)} flagged, {missing} missing/parse-fail"
    )
    print(f"wrote {outpath}")
    if flagged:
        print("\nFLAGGED LADDERS:")
        for a in flagged:
            if rubric == "lanestrict":
                sci = a.get("science_rungs", "?")
                drift = a.get("drift_rungs", "?")
                v = a.get("verdict", "?")
                print(
                    f"  [{v:>6}] {a.get('id','?')}  (science={sci} drift={drift})"
                    f"  -> {a.get('recommendation','')[:120]}"
                )
                if v == "trim":
                    print(f"      keep_idxs: {a.get('keep_idxs',[])}")
            else:
                worst = a.get("worst_severity", "?")
                n = len(a.get("flags", []))
                print(f"  [{worst:>6}] {a.get('id','?')}  ({n} flag{'s' if n != 1 else ''})")
                for fl in a.get("flags", []):
                    if fl.get("severity") in ("high", "medium"):
                        print(
                            f'      T? idx={fl.get("idx")} rule={fl.get("rule")}'
                            f' [{fl.get("severity")}]: {fl.get("detail","")[:120]}'
                        )


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "prompt":
        if len(sys.argv) < 3:
            print("usage: prompt <moral|tone> [--batch=5] [ids...]")
            return
        rubric = sys.argv[2]
        batch = 5
        ids = []
        for a in sys.argv[3:]:
            if a.startswith("--batch="):
                batch = int(a.split("=", 1)[1])
            else:
                ids.append(a)
        cmd_prompt(rubric, batch, ids)
    elif cmd == "aggregate":
        if len(sys.argv) < 3:
            print("usage: aggregate <moral|tone>")
            return
        cmd_aggregate(sys.argv[2])
    else:
        print(f"unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
