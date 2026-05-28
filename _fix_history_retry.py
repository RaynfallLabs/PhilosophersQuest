"""Retry failed history fixes with length+collision fixes."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

bank = json.loads(Path("data/questions/history.json").read_text(encoding="utf-8"))
dup, ans = build_bank_indices(bank)

# === #487 Joan — use cross-dressing charge (Seine in idx 254) ===
q = dict(bank[487])
q["question"] = "Joan of Arc was burned alive in Rouen on May 30, 1431, at age 19. Her trial transcript shows the English-aligned court had trouble finding a charge that would stick under Church law. They convicted her of one specific religious offense — relatively minor itself but reframed as repeated heresy because she had 'relapsed.' What was the charge?"
q["answer"] = "Wearing men's clothing in defiance of Church teaching"
q["choices"] = [
    "Wearing men's clothing in defiance of Church teaching",
    "Claiming direct revelation from angels without priestly mediation",
    "Refusing to acknowledge papal authority over the King of France",
    "Marrying a French nobleman in a secret peasant ceremony",
]
q["context"] = "Joan had worn men's armor and clothing throughout her military service. When the court forced her to abjure and wear women's clothes, she did briefly — then resumed men's dress within days (under disputed circumstances, possibly to prevent assault in prison). The court ruled this made her a 'relapsed heretic,' subject to execution. Her last word at the stake, per witness chronicles, was 'Jesus.' She was canonized in 1920. The cross-dressing charge has been one of the trial's most-debated aspects ever since."
r = validate_rewrite("history", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=487)
print(f"#487: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[487] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]:
        print(f"  {g}: {reason[:150]}")

# === #84 Pickett — trim + lengthen answer ===
q = dict(bank[84])
q["question"] = "At Gettysburg on July 3, 1863, Lee ordered 12,500 men across an open mile into Union artillery. Half died or were captured in under an hour. As survivors limped back, Lee rode out to meet General Pickett directly. What did he say to him?"
q["answer"] = "It is all my fault, the fault is entirely mine"
q["choices"] = [
    "It is all my fault, the fault is entirely mine",
    "Reform your division for another counter charge",
    "We have lost a battle but not yet the war",
    "Tell your brave men their general loves them",
]
r = validate_rewrite("history", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=84)
print(f"#84: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[84] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]:
        print(f"  {g}: {reason[:150]}")

# === #91 Cuban Missile — trim ===
q = dict(bank[91])
q["question"] = "In October 1962, US spy planes spotted Soviet missiles in Cuba. After 13 days at nuclear brink, Khrushchev publicly removed them for a US no-invasion pledge. But Kennedy made a SECRET concession through a back-channel meeting between his brother and the Soviet ambassador. What did Khrushchev secretly receive?"
q["answer"] = "US removal of Jupiter missiles from Turkey"
q["choices"] = [
    "US removal of Jupiter missiles from Turkey",
    "US grain shipments to Soviet Ukraine for two years",
    "US recognition of East German diplomatic legitimacy",
    "US withdrawal of Marines from Guantanamo base",
]
r = validate_rewrite("history", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=91)
print(f"#91: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[91] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]:
        print(f"  {g}: {reason[:150]}")

# === #138 Great Leap — trim ===
q = dict(bank[138])
q["question"] = "Mao's 1958-62 industrialization campaign included a 'Four Pests' purge that destroyed sparrows nationwide. Peasants beat pots and pans to keep them airborne until they fell exhausted from the sky. What unintended catastrophe did the sparrow kill cause?"
q["answer"] = "Locusts multiplied without their predator, destroying the harvest"
q["choices"] = [
    "Locusts multiplied without their predator, destroying the harvest",
    "Rats overran cities once the sparrows no longer hunted them",
    "Songbirds went extinct, ending centuries of Chinese poetry",
    "Tourists stopped visiting Chinese gardens, ending rural tourism",
]
r = validate_rewrite("history", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=138)
print(f"#138: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[138] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]:
        print(f"  {g}: {reason[:150]}")

# === #153 Rwanda — trim ===
q = dict(bank[153])
q["question"] = "Between April and July 1994, Hutu-led Rwanda organized the massacre of 800,000 Tutsis and moderate Hutus over 100 days — most killed by neighbors with machetes. Government-aligned radio station RTLM broadcast addresses of hiding places and roadblock instructions. What word did RTLM repeatedly use for the Tutsi target?"
q["answer"] = "Inyenzi, the Kinyarwanda word for cockroaches"
q["choices"] = [
    "Inyenzi, the Kinyarwanda word for cockroaches",
    "Banyaruguru, the Kinyarwanda for foreign hillpeople",
    "Abakene, the Kinyarwanda for the lost ones",
    "Tutsiri, the Kinyarwanda for tall cattle-people",
]
r = validate_rewrite("history", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=153)
print(f"#153: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[153] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]:
        print(f"  {g}: {reason[:150]}")

# === #316 Emancipation — rephrase answer to avoid stem overlap ===
q = dict(bank[316])
q["question"] = "On January 1, 1863, Lincoln issued an executive order declaring slaves in Confederate territory legally free. The order changed the war's character from preserving the Union to also ending slavery. But the document's striking scope limitation exposed it as a war measure. Which slaves did the Proclamation NOT free?"
q["answer"] = "Those in Union border states and Union-occupied South"
q["choices"] = [
    "Those in Union border states and Union-occupied South",
    "Those whose owners had taken Confederate citizenship",
    "Those under age 16 or over age 60 years old",
    "Those in territories still organizing for statehood",
]
r = validate_rewrite("history", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=316)
print(f"#316: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[316] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]:
        print(f"  {g}: {reason[:150]}")

# === #332 9/11 — switch to FDNY 343 (avoid Let's roll collision) ===
q = dict(bank[332])
q["question"] = "On the clear morning of September 11, 2001, 19 al-Qaeda hijackers crashed four jetliners — two into the WTC towers, one into the Pentagon, one into a Pennsylvania field. When the towers collapsed, a specific number of New York City firefighters died — the largest single-day loss for any American fire department in history. How many FDNY firefighters were killed?"
q["answer"] = "343"
q["choices"] = ["343", "198", "512", "107"]
r = validate_rewrite("history", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=332)
print(f"#332: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[332] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]:
        print(f"  {g}: {reason[:150]}")

# === #341 Tet — trim, remove em-dash ===
q = dict(bank[341])
q["question"] = "On January 30-31, 1968, North Vietnamese and Viet Cong forces attacked 100+ South Vietnamese cities during the Tet ceasefire, including a Viet Cong squad that briefly occupied the US embassy in Saigon. On February 27, CBS anchor Walter Cronkite editorialized that the war was 'mired in stalemate.' What did LBJ reportedly say in the White House?"
q["answer"] = "If I have lost Cronkite, I have lost middle America"
q["choices"] = [
    "If I have lost Cronkite, I have lost middle America",
    "Bring me McNamara, my generals must be replaced",
    "Get me Westmoreland on the phone, this needs answers",
    "Find me a Democrat who can win this war by November",
]
r = validate_rewrite("history", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=341)
print(f"#341: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[341] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]:
        print(f"  {g}: {reason[:150]}")

# === #367 Salamis — trim ===
q = dict(bank[367])
q["question"] = "In September 480 BC, with Athens evacuated and the Persian fleet of 1,200 ships hunting a smaller Greek fleet (~370 ships), Themistocles tricked Xerxes by sending his slave Sicinnus with a false message to the Persian camp. What did Sicinnus tell Xerxes?"
q["answer"] = "The Greeks were terrified and about to flee"
q["choices"] = [
    "The Greeks were terrified and about to flee",
    "The Greek fleet had split into three squadrons",
    "Athens was burning, Greek admirals were arguing",
    "Secret Greek allies of Persia would betray the fleet",
]
r = validate_rewrite("history", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=367)
print(f"#367: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[367] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]:
        print(f"  {g}: {reason[:150]}")

Path("data/questions/history.json").write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("\nWrote bank")
