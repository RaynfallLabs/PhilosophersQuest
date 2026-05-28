"""Phase E history fixes — batch 1: criticals + generic-label conversions."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = Path("data/questions/history.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))

FIXES = []

# === CRITICAL #498: 'Mary had a little lamb' is 5 words, not 4 ===
FIXES.append({
    "idx": 498,
    "patch": {
        "question": bank[498]["question"].replace("four words", "the opening line").replace("What four words", "What were the words"),
    },
    "reason": "Fix factual error: 'Mary had a little lamb' is 5 words not 4.",
})

# === CRITICAL #719: Honecker/Husák/Zhivkov never shot — replace distractors ===
FIXES.append({
    "idx": 719,
    "patch": {
        "choices": [
            "Nicolae Ceaușescu of Romania — shot December 25 1989",
            "Erich Honecker of East Germany — deposed October 1989, died in Chile 1994",
            "Gustáv Husák of Czechoslovakia — resigned December 1989, died of natural causes 1991",
            "Todor Zhivkov of Bulgaria — resigned November 1989, tried for embezzlement, died 1998",
        ],
    },
    "reason": "Fix distractors falsely claiming Honecker/Husák/Zhivkov were shot in Dec 1989. None were.",
})

# === CRITICAL #59: Pearl Harbor 'day of infamy' Drama-Available → FDR pencil edit ===
FIXES.append({
    "idx": 59,
    "patch": {
        "question": "Within hours of the Japanese attack on Pearl Harbor, Franklin Roosevelt sat down to dictate his war-message speech. Looking at the typed first draft, he crossed out a single phrase with a pencil and wrote the word above it that became the day's nickname forever after. What was the original typed phrase Roosevelt struck?",
        "answer": "world history",
        "choices": [
            "world history",
            "great evil",
            "American sorrow",
            "naval shame",
        ],
        "context": "The typed first draft of Roosevelt's December 8, 1941 speech to Congress read: 'a date which will live in world history.' FDR crossed out 'world history' and wrote 'infamy' in pencil — creating the line: 'a date which will live in infamy.' The original typed draft with the pencil edit survives in the FDR Presidential Library in Hyde Park, NY. The Japanese attack on December 7, 1941 killed 2,403 Americans and destroyed or damaged 19 ships. The speech was delivered the next morning; the Senate voted 82-0 and the House 388-1 (Jeannette Rankin of Montana, the same pacifist who had voted against WWI, cast the lone no vote).",
    },
    "reason": "Replace bare 'Dec 7 1941' date-recall with FDR's iconic pencil edit (changing 'world history' to 'infamy').",
})

# === CRITICAL #487: Joan Rouen Drama-Available → ashes-into-Seine ===
FIXES.append({
    "idx": 487,
    "patch": {
        "question": "Joan of Arc was an illiterate peasant girl from Domrémy who at 17 convinced the French dauphin Charles to give her command of an army. She broke the English siege of Orléans in May 1429 and saw Charles crowned at Reims that July. Captured by Burgundians and sold to the English, she was burned alive in Rouen's market square on May 30, 1431, at age 19. The English took an unusual step afterward — specifically to prevent French Catholics from collecting her remains as relics. What did they do?",
        "answer": "Threw her ashes into the Seine River",
        "choices": [
            "Threw her ashes into the Seine River",
            "Buried the ashes at a secret location in northern England",
            "Sealed the ashes in lead casket and shipped them to London",
            "Mixed the ashes into the foundation mortar of Rouen Cathedral",
        ],
        "context": "By dispersing Joan's ashes in flowing water, the English denied French Catholics any physical relic of the girl who had crowned their king. Joan was 19 when she died. According to chronicler accounts, her last word was 'Jesus' as the flames rose. She was retried, exonerated, and canonized in 1456; formally declared a saint in 1920 by Pope Benedict XV. Her trial transcript survives and is one of the most detailed records of any medieval life.",
    },
    "reason": "Joan Drama-Available canonical fix: surface the ashes-in-Seine specific cool fact.",
})

# === GENERIC LABEL #49: Independence Day → John Adams predicted July 2 ===
FIXES.append({
    "idx": 49,
    "patch": {
        "question": "On a hot July day in Philadelphia in 1776, the Continental Congress voted for independence from Great Britain and then spent two days debating the wording of the Declaration. John Adams wrote his wife Abigail predicting that one specific date would be celebrated forever as American Independence Day with bonfires and bells. He was wrong by two days. Which date did Adams expect to be the holiday?",
        "answer": "July 2",
        "choices": [
            "July 2",
            "July 4",
            "August 1",
            "June 14",
        ],
        "context": "Adams wrote: 'The Second Day of July 1776, will be the most memorable Epocha, in the History of America... It ought to be solemnized with Pomp and Parade, with Shews, Games, Sports, Guns, Bells, Bonfires and Illuminations from one End of this Continent to the other from this Time forward forever more.' He was right about the celebrations and wrong about the date — Americans came to celebrate July 4 (when the Declaration's wording was adopted), not July 2 (when the vote for independence happened). Thomas Jefferson, the Declaration's principal author, was 33 years old.",
    },
    "reason": "Convert bare-date answer to Adams's famously-wrong prediction of July 2 as the holiday.",
})

# === GENERIC LABEL #84: Pickett's Charge → Lee's apology to Pickett ===
FIXES.append({
    "idx": 84,
    "patch": {
        "question": "On the afternoon of July 3, 1863, in the last desperate Confederate attack at Gettysburg, Pennsylvania, General Robert E. Lee ordered about 12,500 Confederate soldiers across an open mile of ground straight into the center of the Union line. Half were killed, wounded, or captured in less than an hour. As the survivors stumbled back toward Confederate lines, Lee rode out to meet them. What did he say directly to General George Pickett?",
        "answer": "It is all my fault",
        "choices": [
            "It is all my fault",
            "Reform your division for another charge",
            "We have lost the battle but not the war",
            "Tell the men their general loves them",
        ],
        "context": "Lee's full reported line was: 'It is all my fault. Your men did all that men could do. The fault is entirely mine.' When Pickett went to organize his shattered division for a counterattack against an expected Union pursuit, Lee said the famous line: 'General Pickett, see to your division.' Pickett replied: 'General Lee, I have no division.' His three brigade commanders were all dead; over 60% of his men were casualties. Pickett never forgave Lee, and the two men barely spoke for the rest of their lives.",
    },
    "reason": "Convert Pickett's-Charge-label answer to Lee's 'It is all my fault' apology.",
})

# === GENERIC LABEL #91: Cuban Missile Crisis → secret Turkey trade ===
FIXES.append({
    "idx": 91,
    "patch": {
        "question": "In October 1962, American spy planes photographed Soviet missile sites being built in Cuba — 90 miles from Florida. For 13 tense days, President Kennedy and Soviet leader Khrushchev faced each other on the brink of nuclear war. Khrushchev publicly agreed to withdraw the Cuban missiles in exchange for a US promise not to invade Cuba. But Kennedy also made a SECRET concession in a back-channel meeting between Robert Kennedy and Soviet ambassador Dobrynin. What did Khrushchev secretly receive?",
        "answer": "US removal of Jupiter missiles from Turkey",
        "choices": [
            "US removal of Jupiter missiles from Turkey",
            "US grain shipments to Soviet Ukraine for two years",
            "US recognition of East German diplomatic legitimacy",
            "US withdrawal of Marines from the Guantanamo base",
        ],
        "context": "The Turkish Jupiter missiles were already obsolete and Kennedy had been planning to remove them anyway. The secret was insisted on by Kennedy because publicly trading missiles would have looked like American weakness. Khrushchev kept the secret too — Soviet documents declassified in the 1990s confirmed the deal. The 13 days lasted from October 16 (when Kennedy was shown the U-2 photos) to October 28 (when Khrushchev announced the public withdrawal terms on Moscow radio).",
    },
    "reason": "Convert Cuban-Missile-Crisis label answer to the secret Turkish-missile back-channel deal.",
})

# === GENERIC LABEL #128: Six-Day War → Operation Focus codename ===
FIXES.append({
    "idx": 128,
    "patch": {
        "question": "In June 1967, Israel — surrounded by Arab armies threatening invasion — launched a surprise pre-emptive air strike that destroyed the Egyptian, Syrian, and Jordanian air forces on the ground in the first three hours of the war. Without enemy air cover, Arab ground armies were overrun in six days. What was the Israeli code name for the opening air strike?",
        "answer": "Operation Focus",
        "choices": [
            "Operation Focus",
            "Operation Lightning",
            "Operation Cyclone",
            "Operation Sandstorm",
        ],
        "context": "Operation Focus (in Hebrew: 'Moked,' מבצע מוקד) launched at 7:45 AM on June 5, 1967. Almost every Israeli combat plane was airborne; only 12 jets remained to defend Israel. The strike destroyed 452 Egyptian aircraft on the ground in three hours and 416 total Arab planes by day's end. In six days, Israel captured the Sinai Peninsula and Gaza Strip from Egypt, the West Bank and East Jerusalem from Jordan, and the Golan Heights from Syria. The Old City of Jerusalem fell to Israeli paratroopers on June 7 — the first Jewish control of the city in 1,900 years.",
    },
    "reason": "Convert Six-Day-War label answer to Operation Focus codename.",
})

# === GENERIC LABEL #129: Inchon → Operation Chromite + tide window ===
FIXES.append({
    "idx": 129,
    "patch": {
        "question": "On September 15, 1950, three months into the Korean War, U.N. forces under American General Douglas MacArthur launched a daring amphibious landing far behind North Korean lines at a difficult port with 30-foot tides that gave landing craft only a 4-hour window per day. Most of MacArthur's staff opposed the plan as too risky. What was the code name for the landing operation?",
        "answer": "Operation Chromite",
        "choices": [
            "Operation Chromite",
            "Operation Hammer",
            "Operation Tidewall",
            "Operation Stranglehold",
        ],
        "context": "Operation Chromite landed at Inchon, South Korea — the impossible-tides port near Seoul. MacArthur correctly judged the surprise would shatter the North Korean army stretched along the Pusan Perimeter at the southern tip. Within two weeks, U.N. forces had recaptured Seoul and were pursuing the North Koreans across the 38th parallel. Inchon was MacArthur's last great strategic triumph; his subsequent push north toward the Yalu River triggered Chinese intervention and a long, grinding war.",
    },
    "reason": "Convert Inchon place-name answer to Operation Chromite code name + tide-window context.",
})

# === GENERIC LABEL #138: Great Leap Forward → four-pests / locusts ===
FIXES.append({
    "idx": 138,
    "patch": {
        "question": "From 1958 to 1962, Mao Zedong launched a campaign to industrialize China overnight using mass peasant labor — backyard furnaces, mass irrigation projects, and forced grain collection. The campaign included a 'Four Pests' purge that destroyed sparrows across China. What unintended catastrophe did the sparrow kill cause?",
        "answer": "Locusts and other crop-eating insects multiplied, destroying the grain harvest",
        "choices": [
            "Locusts and other crop-eating insects multiplied, destroying the grain harvest",
            "Rats overran the cities once the sparrows could no longer hunt them",
            "Songbirds went extinct in China, ending centuries of poetic tradition",
            "Tourists stopped visiting Chinese gardens, collapsing rural tourism revenue",
        ],
        "context": "Sparrows had been listed among the 'Four Pests' (along with flies, mosquitoes, and rats). Chinese peasants beat pots and pans to keep sparrows from landing until they fell exhausted from the sky. The kill removed a major predator of crop-eating insects. The resulting locust swarms — combined with backyard furnaces destroying farm tools to make worthless steel, and forced grain quotas that left peasants with nothing to eat — produced a famine that killed an estimated 30 to 45 million people. Mao was forced to step back from day-to-day governance until launching the Cultural Revolution in 1966.",
    },
    "reason": "Convert Great-Leap-Forward label answer to the four-pests sparrow → locust catastrophe.",
})

# === GENERIC LABEL #153: Rwandan Genocide → Inyenzi 'cockroaches' radio ===
FIXES.append({
    "idx": 153,
    "patch": {
        "question": "Between April and July 1994, the ethnic-majority Hutu government of the central African nation of Rwanda organized the massacre of about 800,000 ethnic-minority Tutsis and moderate Hutus over about 100 days — most killed with machetes by neighbors. A government-aligned radio station, RTLM, played a critical role broadcasting incitement and naming specific Tutsi targets by location. What word did RTLM repeatedly call the Tutsi target population?",
        "answer": "Inyenzi — Kinyarwanda for 'cockroaches'",
        "choices": [
            "Inyenzi — Kinyarwanda for 'cockroaches'",
            "Banyaruguru — Kinyarwanda for 'foreigners from the hills'",
            "Abakene — Kinyarwanda for 'the lost ones of history'",
            "Tutsiri — Kinyarwanda for 'tall-people of the cattle'",
        ],
        "context": "RTLM (Radio-Télévision Libre des Mille Collines) broadcast Hutu Power propaganda from July 1993 onward, dehumanizing Tutsis as 'inyenzi' (cockroaches) to be exterminated. During the genocide, RTLM broadcast specific addresses where Tutsis were hiding, names of people to kill, and roadblock instructions. Three of its leaders — Ferdinand Nahimana, Hassan Ngeze, and Jean-Bosco Barayagwiza — were convicted of incitement to genocide by the International Criminal Tribunal for Rwanda. The genocide was halted in July 1994 when the Rwandan Patriotic Front (Tutsi-led rebel army under Paul Kagame) captured Kigali.",
    },
    "reason": "Convert Rwandan-Genocide label answer to the RTLM 'inyenzi' cockroach term.",
})

# === GENERIC LABEL #308: Alamo → Travis line in sand / Bowie sickbed ===
FIXES.append({
    "idx": 308,
    "patch": {
        "question": "From February 23 to March 6, 1836, about 200 Texan defenders held a fortified Spanish mission in San Antonio against Antonio López de Santa Anna's much larger Mexican army. On March 3, three days before the final assault, commander William Travis drew a line in the sand with his sword and asked anyone willing to stay and die for Texas to cross it. How many of the men crossed Travis's line?",
        "answer": "All but one — Moses Rose, who left over the wall that night",
        "choices": [
            "All but one — Moses Rose, who left over the wall that night",
            "About half — the unmarried men, while families chose to surrender",
            "Roughly two-thirds — most settlers stayed, most volunteer soldiers left",
            "Around twenty — the rest accepted Santa Anna's amnesty offer",
        ],
        "context": "Travis's line is a story attested by Louis 'Moses' Rose himself, who left the Alamo on the night of March 3-4 by climbing the wall — the only defender who did not cross. He reported the line story to the family that sheltered him; their son later published it in 1873. All other defenders died on March 6 when Mexican forces breached the walls before dawn. Davy Crockett and his Tennessee volunteers, James Bowie (fighting from his sickbed with his huge knife), and Travis all died. Sam Houston defeated Santa Anna at San Jacinto six weeks later, the men shouting 'Remember the Alamo!'",
    },
    "reason": "Convert Alamo place-name answer to Travis's line-in-the-sand + Moses Rose cool fact.",
})

# === GENERIC LABEL #316: Emancipation Proclamation → scope limitation ===
FIXES.append({
    "idx": 316,
    "patch": {
        "question": "On January 1, 1863, President Abraham Lincoln issued an executive order declaring enslaved people in Confederate-controlled territory legally free. The order changed the war's character from preserving the Union to also ending slavery — and prevented Britain and France from recognizing the Confederacy. But the document's striking scope limitation exposed its purpose as a war measure. Which enslaved people did the order NOT free?",
        "answer": "Enslaved people in Union border states and Union-held Southern territory",
        "choices": [
            "Enslaved people in Union border states and Union-held Southern territory",
            "Enslaved people whose owners had taken Confederate citizenship",
            "Enslaved people younger than 16 or older than 60 years old",
            "Enslaved people in territories still organizing for statehood",
        ],
        "context": "The Proclamation freed slaves only in areas Lincoln's federal government could not actually reach — making it more a war strategy than a humanitarian act. Border-state slaves (Kentucky, Missouri, Maryland, Delaware) and slaves in Union-occupied Southern territories (parts of Tennessee, Louisiana, Virginia) were exempted to keep border-state loyalty. Slavery did not end formally until the Thirteenth Amendment was ratified December 6, 1865 — after Lincoln's assassination. The Proclamation was issued five days after the Confederate defeat at Antietam (the bloodiest day in American history) gave Lincoln the political cover to issue it.",
    },
    "reason": "Convert Emancipation-Proclamation label to the strategic scope-limitation cool fact.",
})

# === GENERIC LABEL #326: Brown v Board → 9-0 unanimity ===
FIXES.append({
    "idx": 326,
    "patch": {
        "question": "On May 17, 1954, the US Supreme Court overturned the 1896 Plessy v. Ferguson 'separate but equal' doctrine, ruling racially segregated public schools unconstitutional. Chief Justice Earl Warren spent months strategically delaying the decision to achieve one specific outcome. What vote count did Warren achieve?",
        "answer": "9-0 unanimous, with every Southern justice on board",
        "choices": [
            "9-0 unanimous, with every Southern justice on board",
            "6-3 with two Southern dissents",
            "7-2 with Warren and Frankfurter dissenting on enforcement",
            "5-4 along party lines, with Eisenhower's appointee deciding",
        ],
        "context": "Warren considered a divided decision politically explosive — any dissent would have given segregationists a banner to rally around. He delayed the ruling from December 1952 until May 1954 to bring along holdout justices, including Stanley Reed of Kentucky (the last vote, finally persuaded that day). The unanimous decision famously declared 'separate educational facilities are inherently unequal.' Implementation was deliberately slow — Brown II (1955) ordered desegregation 'with all deliberate speed,' a phrase that gave segregationists decades of delay. The named plaintiff was third-grader Linda Brown of Topeka, Kansas.",
    },
    "reason": "Convert Brown-v-Board case-name to the 9-0 unanimity cool fact.",
})

# === GENERIC LABEL #332: 9/11 → Flight 93 'Let's roll' ===
FIXES.append({
    "idx": 332,
    "patch": {
        "question": "On the clear morning of September 11, 2001, 19 hijackers from al-Qaeda took control of four passenger airliners. Two struck the World Trade Center; one struck the Pentagon. On Flight 93, after passengers learned from cell phones what was happening on the other planes, several decided to fight back. Software-executive Todd Beamer's GTE airphone call ended with the Lord's Prayer and a two-word phrase that became the moment's iconic slogan. What were Beamer's last words?",
        "answer": "Let's roll",
        "choices": [
            "Let's roll",
            "Time to go",
            "Now or never",
            "Watch the door",
        ],
        "context": "Todd Beamer was 32, on a business trip from New Jersey to San Francisco. His call to GTE airphone supervisor Lisa Jefferson lasted 13 minutes. After exchanging information about the hijackers (one with a red box claiming to be a bomb), Beamer recited the Lord's Prayer with Jefferson, then said: 'Are you guys ready? Okay. Let's roll.' Flight 93 crashed in a Pennsylvania field at 10:03 AM, killing all 44 aboard but failing to reach its target (believed to be the US Capitol). President Bush quoted Beamer's words in his speech to a joint session of Congress on September 20, 2001.",
    },
    "reason": "Convert bin-Laden common-knowledge to Flight 93 'Let's roll' Tier-1 cool fact.",
})

# === GENERIC LABEL #341: Tet Offensive → Cronkite 'lost middle America' ===
FIXES.append({
    "idx": 341,
    "patch": {
        "question": "On January 30-31, 1968 — during the Tet (lunar new year) ceasefire — communist North Vietnamese and Viet Cong forces launched simultaneous attacks on over 100 cities and military bases in South Vietnam, including a Viet Cong squad that briefly occupied the US embassy in Saigon. Though the offensive was a tactical defeat for the communists, it shattered American confidence that the war was being won. On February 27, 1968, CBS anchor Walter Cronkite editorialized that the war was 'mired in stalemate.' Watching from the White House, what did Lyndon Johnson reportedly say?",
        "answer": "If I've lost Cronkite, I've lost middle America",
        "choices": [
            "If I've lost Cronkite, I've lost middle America",
            "Bring me McNamara — I want my generals replaced",
            "Get me Westmoreland on the phone, this needs answers",
            "Find me a Democrat who can win this war by November",
        ],
        "context": "Cronkite, the most-trusted man in America, delivered his editorial after returning from a reporting trip to Vietnam. LBJ announced a month later (March 31, 1968) that he would not seek re-election. The Tet Offensive cost the Viet Cong nearly all their infiltrated forces — they never recovered as a fighting force — but the political effect in America was decisive. The phrase 'If I've lost Cronkite' has been disputed (some staffers say LBJ said 'middle America' / 'Mr. Average Citizen' / 'this war'), but the substance is documented: LBJ knew the war's political support had collapsed.",
    },
    "reason": "Convert Tet-Offensive label to Cronkite 'lost middle America' iconic moment.",
})

# === GENERIC LABEL #367: Salamis → Sicinnus slave message ===
FIXES.append({
    "idx": 367,
    "patch": {
        "question": "In September 480 BC, with Athens evacuated and the Persian fleet of about 1,200 ships hunting the smaller Greek fleet (~370 ships), Athenian commander Themistocles tricked the Persians into entering a narrow strait where their numbers became a disadvantage. He sent a Greek slave with a false message to King Xerxes. What did the slave Sicinnus tell Xerxes?",
        "answer": "That the Greeks were terrified and about to flee, so Xerxes must trap them",
        "choices": [
            "That the Greeks were terrified and about to flee, so Xerxes must trap them",
            "That the Greek fleet had already split into three squadrons heading home",
            "That Athens was burning and the Greek admirals were arguing about surrender",
            "That secret Greek allies of Persia would betray the fleet during the battle",
        ],
        "context": "Sicinnus, Themistocles's slave (himself the tutor of Themistocles's children), reached the Persian camp at night and delivered the message that the Greek fleet was about to scatter and flee. Xerxes ordered his fleet into the narrow strait of Salamis to block the escape — exactly what Themistocles wanted. In the cramped channel, the Persian ships could not maneuver, were hit broadside by Greek triremes, and were destroyed. Xerxes watched from a throne on Mount Aigaleos. Within a year, Persia gave up the invasion of Greece. The story is told by Herodotus.",
    },
    "reason": "Convert Salamis place-name to Sicinnus slave-message ploy.",
})

# === GENERIC LABEL #396: Chernobyl → Forsmark Sweden first detection ===
FIXES.append({
    "idx": 396,
    "patch": {
        "question": "On April 26, 1986, Reactor No. 4 at a Soviet nuclear power plant in Ukraine exploded during a botched safety test, releasing the largest atmospheric release of radioactive material in human history. The Soviet government tried to suppress the news. Two days later, alarms went off at a nuclear plant in another country — workers initially thought their own plant had leaked, then realized the radiation was blowing in from elsewhere. At which foreign plant was the disaster first detected?",
        "answer": "Forsmark Nuclear Power Plant in Sweden",
        "choices": [
            "Forsmark Nuclear Power Plant in Sweden",
            "Loviisa Nuclear Power Plant in Finland",
            "Olkiluoto Nuclear Power Plant in Finland",
            "Greifswald Nuclear Power Plant in East Germany",
        ],
        "context": "On the morning of April 28, 1986, a Forsmark worker stepping into a radiation monitor set off alarms — he was contaminated. After hours of internal checking, Forsmark's engineers determined the radiation was on workers' clothing (from outside) and traced atmospheric measurements pointing east-southeast — toward Soviet territory. Sweden contacted Moscow demanding answers. The Soviet government issued a brief acknowledgment the same evening. The plume eventually crossed most of Europe. Reactor No. 4 of the Chernobyl Nuclear Power Plant near Pripyat, Ukrainian SSR was the source. The April 26 explosion killed 2 workers immediately; 30+ first responders and operators died of acute radiation poisoning within months. Long-term cancer-attributable deaths are estimated at 4,000 to 60,000+ across Europe.",
    },
    "reason": "Convert Chernobyl place-name to the Forsmark Sweden first-detection cool fact.",
})


# Apply all
dup, ans = build_bank_indices(bank)
print(f"Applying {len(FIXES)} history fixes (batch 1)...\n")

results = {"applied": [], "failed": []}

for fix in FIXES:
    idx = fix["idx"]
    patch = fix["patch"]
    q_new = dict(bank[idx])
    for k, v in patch.items():
        q_new[k] = v

    r = validate_rewrite("history", q_new, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
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
