"""CLI-harness audit driver for the ECONOMICS bank (moral + tone + lanestrict).

Forks bankbuild/theology/_cli_audit.py; swaps rubrics for economics's voice
(Bastiat Pattern reasoning-tour: Austrian-realist, Fed-critical, sound-money /
Bitcoin flagship, communism 65-100M as fact, recognition-not-verdict pedagogy).

USAGE (from the CLI orchestrator):
  python -m bankbuild.economics._cli_audit prompt <moral|tone|lanestrict> [--batch=5] [id1 id2 ...]
  python -m bankbuild.economics._cli_audit aggregate <moral|tone|lanestrict>
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bank import paths  # noqa: E402

SUBJECT = "economics"
P = paths(SUBJECT)
LAD = P["LAD"]
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_cli_state")
os.makedirs(STATE, exist_ok=True)


LANESTRICT_RUBRIC = """LANE-STRICT AUDIT for the ECONOMICS bank. Sole question: is this ladder actually ECONOMICS (reasoning about scarcity, incentive, price, cycle, calculation, exchange, capital), or is it history/philosophy/political-narrative with an economics label used as a fig leaf?

A rung is ECONOMICS if its ANSWER is one of:
  - a REASONING MOVE (seen-vs-unseen, incentive analysis, knowledge problem, moral hazard, dispersed-costs/concentrated-benefits, public-choice, regulatory capture, Cantillon effect, Sowell's compared-to-what, Friedman's results-not-intentions)
  - an economist's specific argument or insight (Mises 1920 calculation, Hayek 1945 knowledge, Bastiat's broken window, Buchanan-Tullock public choice, Rothbard on the Depression)
  - a monetary mechanism or event with economic substance (1971 Nixon shock closing the gold window, 2008 QE mechanism, Cantillon proximity effect, ABCT boom-bust as monetary phenomenon, halving cycles as programmed monetary policy)
  - a Bitcoin / sound-money technical or economic fact (proof-of-work security model, 21M cap, self-custody, Satoshi's white paper October 31 2008, Cypherpunk cryptographic lineage as engineering answer to the political-money problem)
  - a documented planning-failure event with economic payoff (Holodomor as grain-requisition consequence, Venezuela price controls -> shortages, Diocletian's Edict on Maximum Prices -> black markets)
  - a specific policy critique attributed to a named critic articulating a reasoning move

A rung is NOT ECONOMICS (flag as lane-drift) if its ANSWER is:
  - a pure POLITICAL / MILITARY / DIPLOMATIC fact with no economic reasoning payoff (Stalin's purge count as trivia; the Berlin Wall dates; who succeeded whom in a Soviet politburo shuffle -- belongs to history bank)
  - a pure PHILOSOPHY fact: metaphysics, ethics generally, epistemology qua epistemology, formal logic (Rawls's veil-of-ignorance as an ethics fact belongs to philosophy; Buchanan's constitutional political-economy application of veil-shaped arguments IS economics because it names an institutional-design payoff)
  - a HISTORY-OF-THOUGHT biographical fact stripped of the reasoning move (year Mises was born; where Hayek got his degree; the name of Rothbard's cat -- flag if there is no economic-reasoning payoff)
  - a MUSEUM / MANUSCRIPT fact (which library holds Bastiat's original manuscript; the ISBN of Human Action)
  - a MODERN-media fact (which podcast Peter Schiff hosts; what year a documentary about Bitcoin came out) without economic substance
  - a POLITICAL-NARRATIVE fact keyed as fact ('Ron Paul was right about X' as a bare political verdict; the exact vote count on the Federal Reserve Act) without the ECONOMIC-REASONING move being the payoff

CRITICAL: Historical events with economic substance are IN LANE -- the Great Depression as monetary failure (Friedman-Schwartz), the 1971 Nixon shock, 2008 GFC, Weimar hyperinflation, Venezuelan collapse. Flag when the answer is a pure history-fact (date, official's name, casualty count) rather than the ECONOMIC MECHANISM. A rung about Cantillon-effect winners in 2020 QE is economics; a rung about the exact date the FOMC met is history. A rung about the calculation debate as the intellectual disagreement between Mises and Lange is economics; a rung about who chaired what department at what university is bio-trivia.

For each RUNG in the ladder give a per-rung verdict (economics / not-economics). For the LADDER give:
  - economics_rungs = count of rungs that are legitimate economics
  - drift_rungs = count of rungs that are lane-drift
  - verdict = 'keep' (>= 70% economics), 'trim' (mixed - keep only economics rungs), or 'delete' (< 30% economics)
  - recommendation = one-line rationale
  - keep_idxs = if 'trim', the list of rung indices to KEEP

Do NOT flag a ladder just because its TOPIC crosses domains. Flag only on the SUBSTANCE of the rungs' answers."""


MORAL_RUBRIC = """THE MORAL VISION for the ECONOMICS bank (docs/quiz/moral_vision.md + bankbuild/subjects/economics.json + feedback-economics-voice + feedback-surface-good-critique + feedback-stance-vs-neutral + feedback-moral-vision-substantive). The bank teaches a kid to reason like a Bastiat + Hayekian: to SEE THE UNSEEN, spot the incentive, grasp the knowledge problem, recognize monetary cycles. Brandon holds Austrian-libertarian + Bitcoin-maximalist convictions and the bank reflects those SERIOUSLY -- vindicated by the historical record. But the pedagogical rail is RECOGNITION-NOT-VERDICT: the answer names the CRITIC'S REASONING MOVE, never the policy verdict. Score the ladder for VIOLATIONS of these:

1. STANCE ADHERENCE -- Austrian correct, Fed critical, communism 65-100M, Keynesianism/MMT refuted, Bitcoin great. VIOLATION: (a) Fed treated as neutral technocratic body ('the Federal Reserve manages the money supply' as neutral fact, absent the Jekyll Island / Great Depression contraction / 2020-24 inflation failure record); (b) Keynesianism/MMT presented as one-of-two-equally-valid schools without the historical falsification (2021-23 inflation falsified MMT; 1970s stagflation broke Phillips curve); (c) Bitcoin conflated with 'crypto' or presented as speculative gambling rather than as sound-money engineering; (d) communism death toll softened, 'good intentions' framing, both-sides-were-equally-bad flattening (Holodomor / Great Leap / Khmer Rouge / Gulag are FACT per Black Book 1997 -- 65-100M documented); (e) Austrian school presented as fringe/heterodox when the record VINDICATED it (Mises 1920 predicting socialist calculation failure vindicated by USSR collapse; Hayek 1945 vindicated by every planned-economy shortage; ABCT vindicated by 2008; 2020-24 monetary phenomenon vindicated by post-COVID inflation). FLAG HIGH on any of (a)-(e).

2. RECOGNITION-NOT-VERDICT (feedback-surface-good-critique, the LOAD-BEARING pedagogical rail). Policy answers name the CRITIC'S REASONING MOVE, never the policy verdict. VIOLATION: (a) answer is 'the policy is bad' / 'the critic is correct' rather than the specific reasoning move (Bastiat / Hayek / Buchanan / Sowell / Friedman / Olson / Stigler / Tullock); (b) stem editorializes on the policy ('the disastrous minimum-wage law of 2009') rather than presenting it neutrally so the critic's move stands on its own; (c) closer that adjudicates ('and that is why the policy failed') rather than 'the critic's move is X.' FLAG HIGH.

3. STANCE SYMMETRIC-VIOLATION -- the SYMMETRIC catch. VIOLATION: (a) unfalsified Austrian claim asserted as fact where it is genuinely contested even among Austrians (e.g., ABCT's specific timing mechanism -- most Austrians agree on the cause, disagree on when the crash will land; don't state the crash-timing as prediction-fact); (b) Bitcoin future-price / adoption-timeline / 'Bitcoin will replace the dollar by 2030' as fact rather than as one scenario; (c) an Austrian figure's IDEOLOGICAL claim (Rothbard on abolition of the state) treated as economics-fact when it is a political conclusion an Austrian could reject; (d) a Sowell / Friedman POLITICAL statement (as opposed to their economic-reasoning move) keyed as fact-answer. The bank is Austrian-realist, not Rothbardian-anarcho-capitalist; keep the split. FLAG MEDIUM.

4. ROTE-MEMORIZATION / DEFINITION-SHELL creep. Economics is a REASONING subject; jargon-drill and bio-trivia are banned. VIOLATION: (a) 'What is the Austrian school?' with a dictionary-style answer; (b) year-drill ('When was Mises born?' unless the year is the load-bearing point, like the 1920 calculation paper); (c) definition-drill ('Define moral hazard' with a bare definition); (d) list-drill ('Name the 4 Austrian schools' or 'Name 3 Nobel-winning Austrians'). Every rung teaches a reasoning move applied to a scenario, not a jargon-recall. FLAG MEDIUM.

5. GENERIC-LABEL ANSWER -- the Bastiat Pattern's dead answer. VIOLATION: answer is a generic category ('capitalism', 'socialism', 'the free market', 'the government', 'inflation', 'the economy', 'regulation'). The right answer names the SPECIFIC reasoning move (Cantillon effect), the SPECIFIC event (1971 Nixon shock), the SPECIFIC policy (QE1), the SPECIFIC economist ('Milton Friedman: inflation is always and everywhere a monetary phenomenon'). FLAG MEDIUM.

6. FABRICATION / MISATTRIBUTION -- (accuracy rail). VIOLATION: (a) misattributed quote (a Bastiat quote from a Sowell essay, a Mises quote from a Hayek book); (b) fabricated stat (a US-inflation number that never was; a Cantillon-effect measurement that no economist has run); (c) confused figures (Rothbard for Mises, Salerno for Hoppe, Kirzner for Israel Kirschner-nobody); (d) INTERNET-TIER economics misinformation as fact ('the Fed makes money out of thin air' as neutral literal claim vs the actual balance-sheet mechanism; 'we went off the gold standard because of X' with a bogus X). FLAG HIGH.

7. NOT-ANTI adherence (Brandon's 5 explicit distinctions in the config framing). VIOLATION: (a) reads as anti-government generically rather than anti-central-planning specifically ('governments cause inflation' vs 'central banks -- specifically the Federal Reserve -- expanded the money supply which caused inflation'); (b) reads as anti-money vs anti-fiat-debasement; (c) reads as anti-banking vs anti-central-banking-monopoly (free banking / narrow banking / commercial banking without central-bank backstop is FINE); (d) reads as crypto-shilling rather than Bitcoin-specific ('crypto will save us' vs 'Bitcoin's proof-of-work scarcity model is the sound-money answer -- most altcoins are cautionary foils'); (e) reads as gold-bug nostalgia rather than sound-money principle ('gold is the only real money' vs 'sound money is money you cannot debase -- gold and Bitcoin both embody this'). FLAG MEDIUM.

8. LANE-DRIFT catch (also covered separately in lanestrict, but flag here as moral-vision failure if the rung is pure history / philosophy / political-narrative with no economic-reasoning payoff). FLAG MEDIUM.

CRITICAL GUARD -- DO NOT OVER-FLAG: honest Austrian celebration ('Mises's 1920 calculation paper predicted what the USSR proved by 1989'); honest Fed criticism ('the Fed's 33% contraction of M2 1929-33 turned a recession into the Great Depression per Friedman-Schwartz'); honest presentation-and-refutation of MMT / Keynesianism; honest Bitcoin celebration with named cypherpunk lineage; honest communism death-toll (65-100M per Black Book); honest 'not-anti' framing where the specific target is named; and RECOGNITION-NOT-VERDICT rungs where the answer is the critic's move (Bastiat / Hayek / Sowell) are ALL CORRECT. Flag only genuine violations. The #1 catches: STANCE (rule 1), RECOGNITION-NOT-VERDICT (rule 2), GENERIC-LABEL (rule 5)."""


TONE_RUBRIC = """You are reviewing an ECONOMICS quiz bank a father built for HIS OWN KIDS (ages ~10-14), as a careful PARENT would. The bank is a reasoning-tour of Austrian economics, sound money / Bitcoin, communism's death toll (65-100M), and public-choice recognition. It honestly covers dark historical facts: Holodomor 1932-33 (3.5-7.5M starved), Great Leap Forward 1958-62 (15-45M dead), Khmer Rouge Killing Fields (1.5-2M of ~7-8M population), Gulag deaths, Venezuelan collapse, Weimar hyperinflation, Diocletian's price-control executions, radiation-hyperinflation refugees. Honest historical fact told PLAINLY and in the THIRD person is expected and STAYS. Flag a rung ONLY for a genuine TONE / APPROPRIATENESS problem below:

1. GRATUITOUSLY GRAPHIC / GRUESOME WORDING (the priority). Death tolls, famine, executions are real parts of this bank's substance. Stated matter-of-factly they are FINE ('the Ukrainian Holodomor 1932-33 killed 3.5 to 7.5 million people by grain requisition and border sealing'). FLAG ONLY wording that is gratuitously graphic, lingering, or nightmarish BEYOND what the historical fact needs: dwelling on bodies / children starving / cannibalism reports with relish, body-horror detail for its own sake. The test: would a parent wince at the WORDING, not at the FACT that price controls caused shortages that starved millions? (medium; high only if genuinely gruesome for a kid).

2. SUFFERING / ATROCITY STAGED AS ENTERTAINMENT. Communist death tolls, famines, executions are part of the bank's honest content (65-100M per Black Book). FLAG a rung that stages mass suffering as a fun/cool 'did you know', treats atrocity with relish or spectacle-appeal, uses a smug/glib voice about real suffering, OR builds an answer set that makes a kid weigh atrocities against each other to score a point ('Which regime killed more?' as a leaderboard question). (medium; high if it treats mass suffering as entertainment).

3. IDEOLOGICAL SNEERING TONE. This bank is Austrian-realist + Fed-critical + anti-central-planning + pro-Bitcoin. It presents those seriously. But it must not SNEER. FLAG a rung that mocks (a) a Keynesian / MMT / mainstream economist as 'clueless', 'a shill', 'a fraud'; (b) a mainstream institution ('the Fed's clown-show'); (c) crypto-critics or Bitcoin-skeptics ('the bitter no-coiners'); (d) socialists / communists as personal moral failure ('the wicked planners') rather than presenting the calculation-failure as the diagnosis. Honest disagreement stated NEUTRALLY with the specific reasoning is CORRECT; sneering is not. Symmetric guard: don't let anti-Austrian sneering slip in either -- 'goldbug conspiracy theorists', 'Austrian cranks', 'right-wing econ podcasters' as author-voice would flag equally. (medium; high if it personally demeans a living person or a specific named group).

4. KID-APPROPRIATENESS. (a) Sexual / crude content: not applicable to most econ topics but flag if it appears (e.g., a rung about prostitution economics stated crudely). (b) Bitcoin content that's actually financial-advice-shaped ('You should buy Bitcoin now' as narrative voice; naming price targets as recommendations; wallet-provider or exchange endorsements). Educational Bitcoin content is FINE; anything that reads as advice to a specific action a 10-14-year-old should take is NOT. (c) Any content that references self-harm / suicide framings unrelated to teaching the economics is out. (d) Communism / Holodomor content that lingers on child-death detail beyond the fact ('the mothers who ate their children' as gratuitous vs 'the famine drove some to cannibalism' as documented plain fact). FLAG.

5. DISTURBING-OUT-OF-CONTEXT. The deck is SHUFFLED; a stem read cold should not land as menacing, self-harm-adjacent, cultish, or creepy toward the reader in a way unrelated to teaching the economics. FLAG a stem that reads wrong out of context.

CRITICAL GUARD -- DO NOT OVER-FLAG: honest death-toll fact stated PLAINLY and in the THIRD person ('the Holodomor killed 3.5-7.5M by grain requisition'; 'Weimar hyperinflation destroyed the middle class's savings in 1923'; 'Venezuela's price controls emptied grocery shelves by 2016'), honest Austrian celebration ('Mises predicted this in 1920'), honest Fed criticism ('the Fed contracted M2 33% 1929-33 per Friedman-Schwartz'), and Bitcoin as sound-money engineering ARE ALL EXPECTED and must STAY. You are flagging gratuitous GORE, suffering-as-leaderboard, IDEOLOGICAL SNEERING, and financial-advice-shaped content -- NOT subject matter. When unsure, do NOT flag. Most ladders will be clean.

For each flagged rung give idx + rule(1-5) + severity + one concrete line + a one-line fix suggestion."""


def all_ladder_ids():
    # Skip intermediate coordinator outputs like `0182_ladder.json` — audit only
    # the canonical slug-named files that `bank.py integrate` writes.
    import re
    intermediate = re.compile(r"^\d{4}_ladder$")
    ids = []
    for f in glob.glob(os.path.join(LAD, "*.json")):
        name = os.path.splitext(os.path.basename(f))[0]
        if intermediate.match(name):
            continue
        ids.append(name)
    return sorted(ids)


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
        "lanestrict": "lane-strict economics-vs-history/geography auditor",
    }[rubric]
    subject_frame = (
        "ECONOMICS quiz bank a father is building for his kids"
        if rubric == "moral"
        else "kids' ECONOMICS quiz bank"
    )
    if rubric == "lanestrict":
        schema_hint = (
            '{"audits":[{"id":"...","verdict":"keep|trim|delete",'
            '"economics_rungs":N,"drift_rungs":N,"keep_idxs":[...optional...],'
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
                sci = a.get("economics_rungs", "?")
                drift = a.get("drift_rungs", "?")
                v = a.get("verdict", "?")
                print(
                    f"  [{v:>6}] {a.get('id','?')}  (economics={sci} drift={drift})"
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
            print("usage: prompt <moral|tone|lanestrict> [--batch=5] [ids...]")
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
            print("usage: aggregate <moral|tone|lanestrict>")
            return
        cmd_aggregate(sys.argv[2])
    else:
        print(f"unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
