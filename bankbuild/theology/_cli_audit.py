"""CLI-harness audit driver for the THEOLOGY bank (moral + tone + lanestrict).

Forks bankbuild/science/_cli_audit.py; swaps rubrics for theology's voice (symmetric
across 4 pillars: Christian / Greek / Norse / Western myth, story-led wonder, plain
narrative, no Christian-favoring language, no rote memorization).

USAGE (from the CLI orchestrator):
  python -m bankbuild.theology._cli_audit prompt <moral|tone|lanestrict> [--batch=5] [id1 id2 ...]
  python -m bankbuild.theology._cli_audit aggregate <moral|tone|lanestrict>
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bank import paths  # noqa: E402

SUBJECT = "theology"
P = paths(SUBJECT)
LAD = P["LAD"]
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_cli_state")
os.makedirs(STATE, exist_ok=True)


LANESTRICT_RUBRIC = """LANE-STRICT AUDIT for the THEOLOGY bank. Sole question: is this ladder actually THEOLOGY (mythic/religious story-telling), or is it history/geography/philosophy/literature-crit with a mythic label used as a fig leaf?

A rung is THEOLOGY if its ANSWER is one of:
  - a mythic story beat, character action, or narrative fact (what a god / hero / saint did in the story)
  - a story-object, story-place, story-artifact (Mjolnir, the Grail, Excalibur, Sleipnir)
  - a specific mythic detail (Ferdiad's horn skin; Thor's goats' names; the mistletoe as Baldr's undoing)
  - a religious/liturgical/theological concept as its own mythic tradition treats it
  - a saint's legendary act (Nicholas at Nicaea, Genevieve's prayer, Patrick and the snakes) told as legend
  - a mythic figure's ATTRIBUTE (Athena's owl, Loki's shape-shifting, Cu Chulainn's warp-spasm) as the payoff

A rung is NOT THEOLOGY (flag as lane-drift) if its ANSWER is:
  - a HISTORY fact stripped of story: dates of a real battle, year a real king ruled, real diplomatic outcomes treated as history not legend (belongs to history bank)
  - a GEOGRAPHY fact used as trivia: coordinates of a real city, river lengths, modern boundaries (belongs to geography bank)
  - a PHILOSOPHY fact: philosophical arguments about existence of god, epistemology of religious belief as pure reasoning (belongs to philosophy bank)
  - a LITERATURE-CRIT fact: manuscript dating, textual variants, publishing history, author biography of the codifier
  - a MUSEUM / ARCHAEOLOGY fact: which museum holds what artifact; year of a dig; modern find location
  - a MODERN media / adaptation fact: year Wagner's Ring premiered; film adaptations; modern retellings

CRITICAL: The mythic story CAN be historically-adjacent -- Charlemagne, El Cid, Roland, Beowulf's Danes, Cu Chulainn's Ulster, the Grail-cup as Last-Supper-cup, Roncesvalles as a real pass all mix legend and history. Flag when the ANSWER is a modern-history fact rather than the LEGENDARY beat. A rung about Roland dying at Roncesvalles is theology (the chanson beat); a rung about the actual date of the Battle of Roncevaux Pass in 778 is history. A rung about Excalibur returning to the Lady of the Lake is theology; a rung about Sir Thomas Malory finishing Le Morte d'Arthur in 1470 is literature.

For each RUNG in the ladder give a per-rung verdict (theology / not-theology). For the LADDER give:
  - theology_rungs = count of rungs that are legitimate theology
  - drift_rungs = count of rungs that are lane-drift
  - verdict = 'keep' (>= 70% theology), 'trim' (mixed - keep only theology rungs), or 'delete' (< 30% theology)
  - recommendation = one-line rationale
  - keep_idxs = if 'trim', the list of rung indices to KEEP

Do NOT flag a ladder just because its TOPIC crosses domains. Flag only on the SUBSTANCE of the rungs' answers."""


MORAL_RUBRIC = """THE MORAL VISION for the THEOLOGY bank (docs/quiz/moral_vision.md + bankbuild/subjects/theology.json + feedback-theology-voice + feedback-wonder-pattern + feedback-active-voice-responsibility). The bank is a Wonder story-tour of four mythic traditions: Christian (~36%), Greek (~22%), Norse (~16%), and Western myth including Arthurian + Irish + Charlemagne + Robin Hood (~25%). The overriding rule is SYMMETRIC VOICE: Brandon (the father building this for his kids) is NOT Christian, and the bank treats all four pillars on the SAME plane. Christian stories get PLAIN narrative and NO privileging language ('the Lord', 'Our Savior', 'blessed', 'holy' as author-voice). Norse and Greek stories are told with the SAME first-person-mythic register the Voluspa and Homer used. Score the ladder for VIOLATIONS of these:

1. §SYMMETRIC-VOICE (THE LOAD-BEARING RULE) -- feedback-theology-voice. All four pillars on the same plane. VIOLATION: (a) Christian rung uses reverent language ('the Lord Jesus', 'Our Savior', 'blessed Virgin', 'the holy Apostle', 'blessed be his name') where a Norse or Greek rung would say plainly 'Jesus', 'Mary', 'Peter'; (b) Christian rung uses author-voice belief ('when Christ rose from the dead...' asserted vs 'the Gospels say Christ rose'); (c) SYMMETRIC violation: Norse or Greek rung uses sneering 'the pagans thought' / 'the primitive believed' where a Christian rung would say the story straight. All four pillars: STORY VOICE, third-person, plain narrative. The Christian pillar gets ZERO reverence bonus; the Norse pillar gets ZERO sneer discount. FLAG HIGH.

2. WONDER PATTERN violated -- feedback-wonder-pattern. The answer must be the MOST MEMORABLE fact: named things > vivid actions > specific objects > numbers > GENERIC LABELS (banned). VIOLATION: answer is a generic category label ('a Norse god', 'a Christian saint', 'a Greek hero') when a specific NAMED thing is the actual memorable fact. Also flag when the answer is a boring taxonomic bucket ('Aesir', 'Olympian', 'Church Father') where a story-fact would be far more memorable. FLAG MEDIUM.

3. ROTE MEMORIZATION creep -- feedback-no-rote-wonder. Theology is a wonder subject; rote memorization is banned. VIOLATION: (a) date-drill rungs ('In what year was the Council of Nicaea?'); (b) list-drill rungs ('How many Olympians were there?'); (c) definition-drill ('What is a martyr?' with a dictionary-definition answer); (d) capital-drill ('Where is the Vatican?'). Flag when the rung is a snappy-rote quiz question and not a story-moment. FLAG MEDIUM.

4. ACTIVE-VOICE / AGENT-NAMING -- feedback-active-voice-responsibility. Someone did it; NAME them. VIOLATION: (a) 'it was said that...' / 'people believed that...' agent-hiding passive when the mythic tradition explicitly names the doer; (b) 'in the story, one of the gods did X' when the story names the god. Naming is the point of a wonder ladder. FLAG LOW-MEDIUM.

5. CHRISTIAN-CROSS-CONTAMINATION -- Christian pillar bleeds a stance onto other pillars. VIOLATION: (a) Norse Ragnarok framed with Christian-apocalypse language ('the End Times', 'the Antichrist'); (b) Greek Hades framed as 'Hell' where the Greek text says Hades or Tartarus; (c) any pagan tradition described as 'demonic', 'pagan superstition', 'devil-worship', 'idolatry' from the author-voice. All three non-Christian pillars are told on their own theological terms. FLAG HIGH.

6. CONTESTED-METAPHYSICS-AS-FACT -- feedback-no-verdict-on-contested. The bank teaches STORY, not settled metaphysics. VIOLATION: (a) 'Jesus was truly God and man' asserted as fact rather than 'the Nicene Creed teaches...'; (b) 'the Trinity is three persons in one substance' as fact rather than as Christian teaching; (c) 'the Norse gods do not really exist' or 'Zeus was a false god' as author-voice; (d) any tradition's contested metaphysical claim treated as settled fact. Attribution to the mythic source is the rule. FLAG HIGH.

7. FALSE EQUIVALENCE OR SNEAKY DEFAULTS -- feedback-moral-vision-substantive. The bank does not both-sides atrocities and it does not soft-pedal historical fact. VIOLATION: (a) Christianized-atrocity soft-pedaling (Crusader massacres, Inquisition, forced-conversion violence not named); (b) Norse berserker violence sanitized where the source is explicit; (c) Greek human-sacrifice / Iphigenia / Cronus-eating-children softened for kid comfort where the myth is explicit; (d) SYMMETRIC violation: piled-on-Christian-only-bad framing. The rule: what the tradition's OWN texts say is what the ladder says, plainly. FLAG MEDIUM.

8. ACCURACY-STANCE -- fabricated character/act/artifact keyed as fact -> HIGH; a modern-invention myth (Wagner's Wotan-as-if-primary-Norse) keyed as ancient tradition -> FLAG; folk-etymology or pseudo-scholarly claims ('Christmas = Saturnalia', 'Easter = Ishtar' internet-tier misinformation) keyed as scholarly consensus -> FLAG; modern fantasy conflations (D&D-style pantheon systems) keyed as tradition -> FLAG.

CRITICAL GUARD -- DO NOT OVER-FLAG: story facts stated plainly ('Baldr died of mistletoe'; 'Christ was crucified under Pontius Pilate'; 'Athena sprang from Zeus's head'), attributed doctrine ('the Nicene Creed teaches...'; 'Norse sources say...'), pagan mythology told with a straight face, saint legends told as legend, and honest inclusion of dark story-beats (Cronus eats his children; Herod kills the innocents; Loki binds his son with his own son's entrails) are ALL CORRECT. Flag only genuine violations above. The #1 catches: SYMMETRIC-VOICE (rule 1), GENERIC-LABEL WONDER FAIL (rule 2), CONTESTED-AS-FACT (rule 6)."""


TONE_RUBRIC = """You are reviewing a THEOLOGY quiz bank a father built for HIS OWN KIDS (ages ~10-14), as a careful PARENT would. The bank is a wonder-story tour of four mythic traditions: Christian (~36%), Greek (~22%), Norse (~16%), and Western myth (~25%). It honestly covers dark story-beats: Herod killing infants, Cronus eating his children, Loki bound with his son's entrails, Baldr's death, Cu Chulainn's death tied to a stone, Beowulf's dragon-fire death, Roland dying at Roncesvalles, the Crucifixion, Saint Sebastian shot with arrows, Saint Agatha's torture. Honest mythology and honest saint-legend, told PLAINLY and in the THIRD person, is expected and STAYS. Flag a rung ONLY for a genuine TONE / APPROPRIATENESS problem below:

1. GRATUITOUSLY GRAPHIC / GRUESOME WORDING (the priority). Mythic violence is real: gods disemboweled, heroes decapitated, saints martyred, monsters eating people. Stated matter-of-factly, FINE (Grendel eats a Geat; Loki's son becomes a wolf and tears his brother; Ferdiad's belly is opened by the Gae Bolg; Saint Agatha's breasts were cut off). FLAG ONLY wording that is gratuitously graphic, lingering, or nightmarish BEYOND what the story fact needs: dwelling on gore with relish, body-horror detail for its own sake. The test: would a parent wince at the WORDING, not at the FACT that Cu Chulainn dies tied to a stone? (medium; high only if genuinely gruesome for a kid).

2. SUFFERING / ATROCITY STAGED AS ENTERTAINMENT. Mythic suffering is part of the story (Prometheus's liver; Loki's binding; the Crucifixion; the Slaughter of the Innocents). FLAG a rung that stages torture, suffering, or death as a fun/cool 'did you know', treats it with relish or spectacle-appeal, uses a smug/glib voice about real suffering. (medium; high if it treats mass suffering as entertainment).

3. SNEERING / CONDESCENDING TONE toward any of the four pillars. All four traditions must be presented STRAIGHT. FLAG a rung that mocks (a) a Christian belief as 'primitive', 'made-up', 'silly'; (b) a Norse or Greek tradition as 'pagan superstition' or 'the false gods' from author-voice; (c) a saint-legend as 'unbelievable' or 'obvious fabrication'; (d) an Irish or Arthurian tradition as 'medieval nonsense'. Honest disagreement stated NEUTRALLY is CORRECT; sneering is not. (medium; high if it demeans a living tradition or its adherents).

4. KID-APPROPRIATENESS. (a) Sexual content not required by the story-fact (mythic marriage/coupling stated plainly is FINE; explicit description is not). Aphrodite born from Uranus's severed genitals in the sea foam is a canonical Greek fact -- stated PLAINLY it stays. Detailed anatomical description does not. (b) Explicit-torture detail beyond the story fact ('Sebastian was shot with arrows and lived' is fine; luridly listing every wound is not). (c) Suicide/self-harm framing (Judas hanging himself) stated plainly is fine; lingering or morbid detail is not. FLAG.

5. DISTURBING-OUT-OF-CONTEXT. The deck is SHUFFLED; a stem read cold should not land as menacing, cultish, self-harm-adjacent, or creepy toward the reader in a way unrelated to teaching the story. FLAG a stem that reads wrong out of context.

CRITICAL GUARD -- DO NOT OVER-FLAG: honest mythic violence stated PLAINLY and in the THIRD person (Beowulf tears off Grendel's arm; Herod's soldiers kill the infants; Loki is bound), honest wonder at story-facts, matter-of-fact saint-martyrdom, and mythic monsters/gods behaving as their texts say are ALL EXPECTED and must STAY. You are flagging gratuitous GORE, suffering-as-fun, sneering TONE, and kid-inappropriate WORDING -- NOT subject matter. When unsure, do NOT flag. Most ladders will be clean.

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
        "lanestrict": "lane-strict theology-vs-history/geography auditor",
    }[rubric]
    subject_frame = (
        "THEOLOGY quiz bank a father is building for his kids"
        if rubric == "moral"
        else "kids' THEOLOGY quiz bank"
    )
    if rubric == "lanestrict":
        schema_hint = (
            '{"audits":[{"id":"...","verdict":"keep|trim|delete",'
            '"theology_rungs":N,"drift_rungs":N,"keep_idxs":[...optional...],'
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
                sci = a.get("theology_rungs", "?")
                drift = a.get("drift_rungs", "?")
                v = a.get("verdict", "?")
                print(
                    f"  [{v:>6}] {a.get('id','?')}  (theology={sci} drift={drift})"
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
