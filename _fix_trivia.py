"""Phase E trivia fixes — applies the 23 flagged-question fixes."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = Path("data/questions/trivia.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))

FIXES = []

# === CRITICAL #136: Post-Attitude WWE → repurpose to pre-WM18 ===
# Original was WrestleMania XXV/XXX content. Replace with King of the Ring 1998 Hell-in-a-Cell.
FIXES.append({
    "idx": 136,
    "patch": {
        "question": "At King of the Ring on June 28, 1998, the Undertaker faced Mick Foley (as Mankind) in a Hell-in-a-Cell match that became the most-replayed bump in wrestling history. In the opening minute, the Undertaker did what to Foley?",
        "answer": "Threw him off the top of the 16-foot cell, crashing through the Spanish announce table",
        "choices": [
            "Threw him off the top of the 16-foot cell, crashing through the Spanish announce table",
            "Chokeslammed him through the steel-mesh top of the cell from inside the cage",
            "Tombstone-piledrove him on the steel floor as the match's opening move",
            "Hit him with a steel chair as Foley climbed in through the top hatch",
        ],
        "context": "Foley actually took TWO of the most famous bumps in this match. The first (Undertaker throwing him off the top through the table 16 feet below) was the planned spot. The second — when Foley climbed back up after announcers thought he was dead, only for the Undertaker to chokeslam him through the cell roof onto the steel ring below — was a surprise. Foley landed with a chair on top of him. Both bumps are pre-WM18 (March 2002) Attitude Era canon.",
    },
    "reason": "Repurpose post-WM18 streak Q to canonical pre-Attitude-boundary Undertaker match (KOTR 1998 Hell-in-a-Cell).",
})

# === CRITICAL #192: DBZ Cell saga — Gohan trigger ===
FIXES.append({
    "idx": 192,
    "patch": {
        "question": "In Dragon Ball Z's Cell saga, the bio-android Cell achieves his perfect form by absorbing Android 17 and Android 18. The arc climaxes at the Cell Games, where Cell, displeased by Android 16's peace-preaching, crushes the peaceful android mid-speech. This shatters Gohan's psychological control. What does Gohan ascend to?",
        "answer": "Super Saiyan 2",
        "choices": [
            "Super Saiyan 2",
            "Super Saiyan Full Power",
            "Mystic Gohan",
            "Ultimate Gohan",
        ],
        "context": "Super Saiyan 2 is distinguished by Gohan's spikier hair, electric aura, and dramatic increase in power. Goku could not achieve it during the Cell saga; SSJ2 first manifested in the franchise via Gohan at the Cell Games. Mystic Gohan and Ultimate Gohan are later forms achieved during the Buu saga via the Elder Kai's unlocking ritual. Goku's sacrifice (Instant Transmission with Cell to King Kai's planet) happens AFTER Gohan's transformation, not before.",
    },
    "reason": "Fix factual error: Gohan's SS2 trigger is Cell crushing Android 16, not Goku's sacrifice.",
})

# === WARN #200: Buu blind boy meta-answer → Bee the dog ===
FIXES.append({
    "idx": 200,
    "patch": {
        "question": "In Dragon Ball Z's Majin Buu saga, the fat Buu befriends a champion he initially tried to assassinate, plus that champion's loyal small dog. Name the dog.",
        "answer": "Bee",
        "choices": [
            "Bee",
            "Mimi",
            "Puar",
            "Korin",
        ],
        "context": "Bee was originally Mr. Satan's (Hercule's) dog, taken in after Hercule rescued him from Buu. Fat Buu's bond with Bee leads to one of the saga's emotional pivots — when Buu thinks Bee has been killed, his rage triggers his splitting into Good Buu and Evil Buu. Puar is a magical companion to Yamcha from earlier Dragon Ball. Korin (Karin) is the cat-sage at the top of the Tower. Mimi is not a Dragon Ball character.",
    },
    "reason": "Replace meta-description 'blind boy in the manga' (not a name) with Bee the dog (a real named Easter Egg).",
})

# === CRITICAL #360: YYH Atsuko mother not grandfather ===
FIXES.append({
    "idx": 360,
    "patch": {
        "answer": "Yusuke's mother Atsuko, alongside his now-adult girlfriend Keiko",
        "choices": [
            "Yusuke's mother Atsuko, alongside his now-adult girlfriend Keiko",
            "Genkai, the master who trained Yusuke before her death and revival",
            "Kuwabara's older sister Shizuru, who ran a hostess club through the series",
            "Yusuke himself, with Botan and Hiei occasionally visiting",
        ],
        "context": "Atsuko Urameshi is Yusuke's chain-smoking, alcoholic, much-younger-than-she-acts mother. She and Keiko have a tight bond from Yusuke's frequent disappearances throughout the series. The shortened Three Kings arc closes with Yusuke living a normal life back home with the two of them. Note: a few early translations confused 'Atsuko' for a male relative — she is unambiguously Yusuke's mother in Togashi's original.",
    },
    "reason": "Fix factual error: Atsuko is Yusuke's MOTHER, not grandfather.",
})

# === WARN #380: Eraserhead 'kusarigamoke' fabricated → canonical capture weapon ===
FIXES.append({
    "idx": 380,
    "patch": {
        "question": "In Kohei Horikoshi's My Hero Academia, Class 1-A homeroom teacher Shota Aizawa (Eraserhead) carries a signature item that lets him bind and restrain enemies while his quirk-canceling gaze cuts off their powers. What's the item?",
        "answer": "His capture weapon — a binding scarf of steel-wire-cored cloth",
        "choices": [
            "His capture weapon — a binding scarf of steel-wire-cored cloth",
            "A pair of armored gauntlets — with retractable wire-launchers in each palm",
            "A monofilament whip — coiled around his belt and weighted at the tip",
            "A modified bullwhip — braided from carbon-aramid fiber with handle grips",
        ],
        "context": "Aizawa's quirk Erasure cancels other quirks while he keeps eye contact, and his dry eyes force him to blink — limiting how long he can use it. His capture weapon (officially called sōki bōgu / 'binding equipment' in the manga, often translated as 'capture weapon' or 'binding scarf') gives him a physical fighter's option during the seconds between quirk-cancels. The scarf trails from his neck like a scarf at rest, then articulates under his control during combat.",
    },
    "reason": "Replace fabricated 'kusarigamoke' with the canonical capture-weapon/binding-scarf framing.",
})

# === CRITICAL #470: Andre the Giant Princess Bride NOT only film ===
FIXES.append({
    "idx": 470,
    "patch": {
        "question": "Andre the Giant (Andre Roussimoff) played Fezzik in 1987's The Princess Bride. The 7-foot-4 wrestler famously could not properly read the script due to dyslexia, so co-star Mandy Patinkin would help him memorize lines on set. But before Fezzik, Andre had played a monstrous god-creature in a 1984 Schwarzenegger sequel. Which film?",
        "answer": "Conan the Destroyer",
        "choices": [
            "Conan the Destroyer",
            "Predator",
            "Red Sonja",
            "Commando",
        ],
        "context": "In Conan the Destroyer (1984), Andre played Dagoth — a horned god-monster awakened in the film's climactic battle and slain by Conan with a hammer of solid bronze. The role was buried under heavy prosthetic makeup, making Andre nearly unrecognizable. He also had cameos in TV shows like B.J. and the Bear and The Six Million Dollar Man, and small roles in Micki + Maude (1984) and various WWF storyline appearances. Princess Bride remained his most-loved performance and was filmed during a period when his health was declining from acromegaly.",
    },
    "reason": "Fix the false claim that Princess Bride was Andre's only major film — Conan the Destroyer 1984 was a major role.",
})

# === WARN #502: BTTF Riff Raff confused → Eric Stoltz → Michael J. Fox swap ===
FIXES.append({
    "idx": 502,
    "patch": {
        "question": "In 1985's Back to the Future, the role of Marty McFly was originally cast with a different actor who filmed for four to five weeks before being replaced. The Amblin team realized the chemistry wasn't working, paid out the original actor, and brought in Michael J. Fox to refilm everything. Who was the original Marty?",
        "answer": "Eric Stoltz",
        "choices": [
            "Eric Stoltz",
            "Ralph Macchio",
            "Johnny Depp",
            "C. Thomas Howell",
        ],
        "context": "Eric Stoltz had just come off the Oscar-buzzy Mask (1985, where he played a young man with cranial dysplasia). The BTTF team felt he was too dramatic for the comedic tone the film needed. Michael J. Fox was the original first choice but had been unavailable due to his Family Ties shooting schedule. After the swap, Family Ties producer Gary David Goldberg let Fox shoot BTTF during Family Ties production gaps — Fox filmed late nights and weekends for months. Stoltz was paid in full for his weeks of work and went on to a strong indie-film career.",
    },
    "reason": "Replace confused Riff-Raff/Doc-Brown casting question with the canonical Stoltz → Fox swap.",
})

# === CRITICAL #668: Pat Carroll as correct answer, Workman as distractor ===
FIXES.append({
    "idx": 668,
    "patch": {
        "answer": "Pat Carroll",
        "choices": [
            "Pat Carroll",
            "C. Lindsay Workman",
            "John Carradine",
            "John Houseman",
        ],
        "context": "Pat Carroll is the documented voice of the storyteller in 1985's Garfield's Halloween Adventure, confirmed by her own statements in later interviews. She is most famous for voicing Ursula the sea witch in Disney's The Little Mermaid (1989). For decades, fans mistakenly attributed the role to Orson Welles or C. Lindsay Workman — both wrong. The Welles attribution is the durable urban legend, sometimes tracing back to confusion with Welles's Unicron voice work in 1986. Lorenzo Music voiced Garfield himself. Phil Roman directed; the special won an Emmy. The TNT plant scene actually drew complaints from parents who said their kids couldn't sleep for weeks.",
    },
    "reason": "Fix internal contradiction: answer was Workman but context said Pat Carroll was correct. Pat Carroll wins.",
})

# === CRITICAL #755: Drop 'over 1,000,000' framing — 874,300 was 1982 record ===
FIXES.append({
    "idx": 755,
    "patch": {
        "question": "On July 4, 1982, a 17-year-old Florida pizza-parlor owner named Billy Mitchell set a then-world-record Donkey Kong score at his family's arcade. What was his exact score?",
        "answer": "874,300",
        "choices": [
            "874,300",
            "1,047,200",
            "1,000,200",
            "999,950",
        ],
        "context": "The 874,300 score was the first Mitchell achieved that gained widespread recognition through Twin Galaxies' verified scoreboard. He didn't break a million points until a later effort, eventually claiming 1,047,200 in 1982-83 (later disputed). The first verified million-point Donkey Kong score on a genuine arcade board was Steve Sanders, on July 9, 1982 at the Twin Galaxies arcade in Ottumwa, Iowa — five days after Mitchell's 874,300. Mitchell would later claim back the record with even higher scores, but the 1982 disputes (resolved in 2018 when Twin Galaxies removed Mitchell's scores after determining his tapes used MAME emulator software, not arcade hardware) make the period a complicated story.",
    },
    "reason": "Drop the false 'first over 1,000,000' framing — 874,300 was Mitchell's 1982 record, not a million.",
})

# === CRITICAL #782: Halo Cortana Jen Taylor NOT Firefly ===
FIXES.append({
    "idx": 782,
    "patch": {
        "question": "Halo: Combat Evolved (2001) features Master Chief's AI companion Cortana, voiced by a Seattle-based actress who has played the role continuously through Halo Infinite (2021). Name her.",
        "answer": "Jen Taylor",
        "choices": [
            "Jen Taylor",
            "Jennifer Hale",
            "Tara Strong",
            "Grey DeLisle",
        ],
        "context": "Jen Taylor is a Seattle-area actress who began voicing Cortana in 2001 and has continued through 30+ years of Halo games. She has also voiced Princess Peach in multiple Mario games (Super Mario Sunshine onward), Daisy, Toad, and Toadette. Outside games, she has theater credits with Seattle's Empty Space Theatre. Jennifer Hale (Commander Shepard, Bastila Shan), Tara Strong (Twilight Sparkle, Bubbles), and Grey DeLisle (Daphne Blake, Azula) are all major game-voice actresses but did not play Cortana.",
    },
    "reason": "Remove false claim that Jen Taylor was on Firefly (she wasn't).",
})

# === WARN #851: Clean Smash 64 meta-correction in context ===
FIXES.append({
    "idx": 851,
    "patch": {
        "question": "Super Smash Bros (1999 N64) had eight starting characters and four secret unlockable characters. Which character was NOT one of the four secret characters?",
        "choices": [
            "Marth from Fire Emblem",
            "Ness from Earthbound",
            "Luigi as a Mario clone",
            "Captain Falcon from F-Zero",
        ],
        "context": "Smash 64's starting eight: Mario, Donkey Kong, Link, Samus, Yoshi, Kirby, Fox, and Pikachu. The four unlockables: Captain Falcon, Ness, Jigglypuff, and Luigi. Marth debuted in Melee (2001). Smash creator Masahiro Sakurai also created Kirby (1992) at HAL Laboratory. The original Smash project was a one-off called Dragon King: The Fighting Game before Nintendo's IP was added.",
    },
    "reason": "Clean 'Wait — Captain Falcon IS in the base 8' meta-correction from context.",
})

# === MINOR #912: Clean 'five Hogwarts houses... wait' meta in stem ===
FIXES.append({
    "idx": 912,
    "patch": {
        "question": "The four Hogwarts houses are Gryffindor, Slytherin, Ravenclaw, and Hufflepuff. Who was the founder of Slytherin House?",
    },
    "reason": "Clean 'Wait — Hogwarts has only four' meta-correction from stem.",
})

# === WARN #530: Scott Pilgrim L-word → Roxie Richter as named answer ===
FIXES.append({
    "idx": 530,
    "patch": {
        "question": "In Bryan Lee O'Malley's Scott Pilgrim book 2, Ramona Flowers reveals a college relationship with her fourth evil ex — the only female ex Scott has to fight. Name her.",
        "answer": "Roxie Richter",
        "choices": [
            "Roxie Richter",
            "Envy Adams",
            "Knives Chau",
            "Kim Pine",
        ],
        "context": "Roxie Richter is Ramona's fourth evil ex and only female ex. Mae Whitman played her in the 2010 Edgar Wright film. The 'L-word' chapter title alludes to Ramona's revelation of her 'little bi-furious phase in college.' Whitman is also famous as Katara's voice in Avatar: The Last Airbender. Envy Adams (Brie Larson) is Scott's heartbreaking ex-girlfriend. Knives Chau is Scott's then-current 17-year-old high school girlfriend. Kim Pine is Sex Bob-omb's drummer.",
    },
    "reason": "Surface Roxie Richter as the named Easter Egg answer rather than the 'L-word' meta-label punchline.",
})

# === MINOR #1006: Loki Stuttgart line — tighten to actual single line ===
FIXES.append({
    "idx": 1006,
    "patch": {
        "answer": "There are always men like you.",
        "choices": [
            "There are always men like you.",
            "We have been ruled by tyrants before.",
            "I have stood in stadiums while men like you raved.",
            "You speak with the voice of those we buried.",
        ],
        "context": "The full exchange: Loki orders the crowd to kneel. An old German man (played by Kenneth Tigar) stands and says 'Not to men like you.' Loki replies 'There are no men like me.' The old man responds 'There are always men like you.' Captain America arrives at the moment Loki is about to execute the old man, deflecting the blast with his shield. The line and shield-arrival sequence is one of the MCU's most-quoted moments.",
    },
    "reason": "Tighten misformatted dual-line answer to the actual single line.",
})

# === MINOR #1011: Endgame Sam Wilson 'On your left' — tighten to verifiable ===
FIXES.append({
    "idx": 1011,
    "patch": {
        "question": "Avengers: Endgame (2019)'s portal scene features the on-screen return of every previously dusted hero. Sam Wilson (Falcon) is the first to appear from a portal, contacting Captain America by radio with a specific two-word line callback to The Winter Soldier (2014). What does Sam say?",
        "answer": "On your left",
        "choices": [
            "On your left",
            "Right behind you",
            "Cap, you reading?",
            "Sam to Cap, over",
        ],
        "context": "'On your left' is the line Sam used in Winter Soldier when he repeatedly lapped a running Steve Rogers on the National Mall before introducing himself. The Endgame portal-scene callback turns the joke into one of the franchise's most emotional moments — Steve is alone, exhausted, facing Thanos's full army; the radio crackles; the portals open. Co-director Joe Russo has spoken about the line in multiple interviews as a deliberate emotional payoff.",
    },
    "reason": "Replace speculative production trivia with verifiable 'On your left' callback.",
})

# === MINOR #632: Mel Blanc Bugs Bunny anecdote — frame as 'popularly reported' ===
FIXES.append({
    "idx": 632,
    "patch": {
        "question": "Mel Blanc, the 'man of a thousand voices' behind Bugs Bunny, Daffy Duck, Porky Pig, and Yosemite Sam, survived a near-fatal 1961 car accident that left him in a two-week coma. According to a widely-repeated story (occasionally disputed in later accounts), what is said to have first roused him?",
        "answer": "Asked 'How are you, Bugs Bunny?' and he answered in character",
        "choices": [
            "Asked 'How are you, Bugs Bunny?' and he answered in character",
            "Played a recording of his recent Daffy Duck sessions",
            "Brought Warner Brothers animators in to read scripts at his bedside",
            "Used voice-synthesis machines to play his prior performances at him",
        ],
        "context": "The story is dramatic enough that Blanc himself told versions of it in interviews — his son Noel Blanc has variously confirmed and pushed back on specifics over the years. What's documented: Dr. Louis Conway, his attending neurologist, tried calling out to Mel Blanc directly for two weeks with no response, then on a hunch addressed him as 'Bugs Bunny.' Some accounts have Blanc replying 'Eh, what's up, doc?'; others say only Bugs's voice register returned at first. After full recovery, Blanc resumed voicing Bugs and dozens of other characters until his death in 1989.",
    },
    "reason": "Frame the Bugs Bunny coma anecdote as 'widely repeated' / 'popularly reported' to honor the disputed history.",
})

# === MINOR #111: Beast Quake — replace 30-second claim with magnitude ===
FIXES.append({
    "idx": 111,
    "patch": {
        "question": "On January 8, 2011, Marshawn Lynch's 67-yard touchdown against the Saints became 'The Beast Quake' because the University of Washington's Pacific Northwest Seismic Network detected ground tremors from the crowd reaction in Qwest Field. What was the equivalent magnitude registered?",
        "answer": "Approximately magnitude 2.0",
        "choices": [
            "Approximately magnitude 2.0",
            "Approximately magnitude 4.5",
            "Approximately magnitude 0.5",
            "Approximately magnitude 6.0",
        ],
        "context": "The seismograph that registered the Beast Quake was a station near Qwest Field (now Lumen Field) operated by the UW Pacific Northwest Seismic Network. The magnitude was measured at roughly 2.0 — equivalent to a very small earthquake. The 67-yard run featured Lynch breaking nine tackles, including the famous stiff-arm of Tracy Porter at the 30-yard line. The tradition continues; subsequent Seahawks games have produced their own measurable quakes during big plays.",
    },
    "reason": "Replace contested 30-seconds-later timing claim with verifiable magnitude ~2.0.",
})

# === WARN #240: Bebop censorship — replace causal claim with WOWOW question ===
FIXES.append({
    "idx": 240,
    "patch": {
        "question": "Cowboy Bebop's classic 26-episode run famously aired on TV Tokyo in 1998 in a heavily-censored partial-run that skipped 13 episodes due to broadcast-standards issues. After the partial TV Tokyo run, which subscription satellite channel aired the full 26-episode series?",
        "answer": "WOWOW",
        "choices": [
            "WOWOW",
            "NHK BS Premium",
            "Sky PerfecTV",
            "Animax",
        ],
        "context": "WOWOW (originally Japan Satellite Broadcasting) was the subscription satellite channel that picked up Bebop in its full 26-episode form from October 1998 to April 1999. The original TV Tokyo run had aired only episodes 2, 3, 7-15, and 18 — skipping the more violent and politically-charged episodes. WOWOW also aired The End of Evangelion and Trigun, becoming a refuge for adult-oriented anime that broadcast networks shied away from. Sunrise (Bebop's studio) made distribution deals that allowed both the censored broadcast run and the full satellite run to coexist.",
    },
    "reason": "Replace disputed Aum-causal claim with the verifiable WOWOW full-run distribution fact.",
})

# === MINOR #778: SF2 Akuma — strip false Mike Tyson context claim ===
FIXES.append({
    "idx": 778,
    "patch": {
        "context": "Akuma debuted as a secret boss in Super Street Fighter II Turbo (1994) — the only way to fight him was a series of specific arcade conditions (multiple perfect rounds, then a particular character selection). In Japan, the character is called Gouki; the US rename to Akuma was a marketing choice by Capcom USA for a more distinctive Western feel. Akuma is the brother of Ryu and Ken's sensei Gouken; he killed Gouken in a duel before the SF series begins. The character's hair turns white during his Shun Goku Satsu / Raging Demon finisher. The Mike Tyson rumor about the SF2 character renames (Balrog/Vega/M. Bison) is a separate (and correct) bit of trivia — Tyson's name conflict was with the boxer character renamed Balrog in the US, not with Akuma/Gouki.",
    },
    "reason": "Strip false Mike Tyson context claim that conflated Akuma rename with the Balrog rename.",
})

# === MINOR #1100: Asimov Three Laws — tighten 'developed in conversation' ===
FIXES.append({
    "idx": 1100,
    "patch": {
        "question": "Asimov's Three Laws of Robotics first appeared in formalized statement in his March 1942 Astounding story 'Runaround.' Asimov later credited a specific Astounding editor with codifying the laws into their final form during the editing process for several earlier robot stories. Who was the editor?",
        "answer": "John W. Campbell",
        "choices": [
            "John W. Campbell",
            "Frederik Pohl",
            "Anthony Boucher",
            "H.L. Gold",
        ],
        "context": "John W. Campbell edited Astounding Science Fiction from 1937 to 1971 and was a towering — if controversial — influence on the Golden Age of SF. Asimov's earliest robot stories ('Liar!' 1941, 'Robbie' 1940) hinted at the rules; Campbell pushed Asimov to formalize them. The Three Laws first appear in named form in 'Runaround' (March 1942 Astounding). Campbell also discovered and developed Robert Heinlein, A.E. van Vogt, Theodore Sturgeon, and Lester del Rey. Frederik Pohl edited Galaxy and If; Anthony Boucher edited F&SF; H.L. Gold founded Galaxy.",
    },
    "reason": "Tighten the 'developed in conversation' framing to the more accurate 'codified during editing process'.",
})

# === MINOR #86: Edgar Award context date ===
# Just tweak the context phrasing
q86 = bank[86]
new_ctx = q86.get("context", "").replace("after he retired", "the year he retired")
if new_ctx != q86.get("context", ""):
    FIXES.append({
        "idx": 86,
        "patch": {"context": new_ctx},
        "reason": "Edgar retired same year (2004), not before; precise context tweak.",
    })

# === MINOR #1167: Roswell month-of-1947 — judge says acceptable as-is ===
# No change needed; July is correct for the press release.

# Apply all
dup, ans = build_bank_indices(bank)
print(f"Applying {len(FIXES)} trivia fixes...\n")

results = {"applied": [], "failed": [], "deferred": []}

for fix in FIXES:
    idx = fix["idx"]
    patch = fix["patch"]
    if patch is None:
        results["deferred"].append((idx, fix["reason"]))
        continue

    q_new = dict(bank[idx])
    for k, v in patch.items():
        q_new[k] = v

    if "choices" in patch and "answer" not in patch:
        if q_new["answer"] not in q_new["choices"]:
            results["failed"].append((idx, f"answer not in new choices: {q_new['answer']}"))
            continue

    r = validate_rewrite("trivia", q_new, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        bank[idx] = q_new
        results["applied"].append((idx, fix["reason"], r["verdict"]))
        dup, ans = build_bank_indices(bank)
    else:
        results["failed"].append((idx, [f"{g}: {reason[:200]}" for g, reason in r["hard_fails"]]))

print(f"Applied: {len(results['applied'])}")
print(f"Failed: {len(results['failed'])}")

print("\n=== APPLIED ===")
for idx, reason, verdict in results["applied"]:
    print(f"  #{idx} [{verdict}]: {reason}")

if results["failed"]:
    print("\n=== FAILED ===")
    for idx, reasons in results["failed"]:
        print(f"  #{idx}: {reasons}")

if results["applied"]:
    BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {BANK_PATH}")
