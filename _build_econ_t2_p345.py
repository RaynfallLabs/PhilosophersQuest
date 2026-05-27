"""Generate 120 fresh T2 economics questions: P3 (40) + P4 (45) + P5 (35).

Voice: Bastiat Pattern. T2 cap 480, hard cap 504. Em-dash uniform.
Target: stem ~150-200, choices ~50-75, total ~400-490.
Saves to _gen_economics_t2_p345.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

D = "—"  # em-dash


def q(tier: int, pillar: str, question: str, answer: str, distractors: list[str], context: str) -> dict:
    choices = [answer] + distractors
    has_dash = [D in c for c in choices]
    assert all(has_dash) or not any(has_dash), f"dash parity: {has_dash} :: {choices}"
    total = len(question) + sum(len(c) for c in choices)
    assert total <= 504, f"budget {total} > 504 :: {question[:60]}"
    return {
        "tier": tier,
        "pillar": pillar,
        "question": question,
        "answer": answer,
        "choices": choices,
        "context": context,
    }


# =========================================================================
# P3 SOUND MONEY + HYPERINFLATION (40)
# =========================================================================

P3 = [
    # --- Classical / ancient (6) ---
    q(2, "3",
      f"Around 600 BC Lydia (modern Turkey) struck the first coins from electrum, a gold-silver alloy. King Croesus later refined them into pure gold and silver. What did stamped coins solve?",
      f"The weigh-and-test step on every trade {D} a stamped unit ended weighing per trade",
      [
          f"Royal budget shortfalls instantly {D} kings could mint wealth",
          f"Tax collection without record keeping {D} ended state scribes",
          f"Religious sacrifice rituals at temples {D} ended grain worship",
      ],
      "Lydian electrum coinage (~600 BC) is the canonical 'invention of money' moment. Croesus refined it to pure-metal bimetallic standard."),

    q(2, "3",
      f"Under Augustus the denarius was ~95% silver. By Gallienus (260-268 AD) it was ~5% silver with copper wash. What was Rome doing to its money?",
      f"Debasement {D} mixing cheap metal so the state could mint more coins",
      [
          f"Honest measurement {D} honest content reporting",
          f"Technological progress {D} more efficient minting",
          f"Standard banking {D} a routine currency update",
      ],
      "Roman denarius debasement funded military campaigns. Diocletian's 301 AD price-controls edict made price-fixing a death-penalty crime — and still failed."),

    q(2, "3",
      f"From 1870 to 1914 major economies linked currencies to gold. Pound, dollar, franc, mark each redeemed for set metal amounts. What is this period called?",
      f"The classical gold standard {D} the high-water mark for international sound money",
      [
          f"The Bretton Woods era {D} when dollar as reserve currency",
          f"The fiat consensus {D} when commodity-backing ended",
          f"The mercantile period {D} when gold-hoarding mercantilism",
      ],
      "Classical gold standard (~1870-1914) saw stable prices and minimal inflation. WWI broke it; governments suspended convertibility to print money."),

    q(2, "3",
      f"In 1717 the British Master of the Mint set gold at 3 pounds 17 shillings 10½ pence per ounce, a rate nearly fixed for 200 years. Who was the Master?",
      f"Isaac Newton {D} the physicist who ran the Royal Mint for 30 years",
      [
          f"Adam Smith {D} Scottish economist of 1776",
          f"David Ricardo {D} comparative-advantage stockbroker 1817",
          f"John Maynard Keynes {D} General-Theory Cambridge economist 1936",
      ],
      "Newton served as Warden then Master of the Mint from 1696 to 1727. His 1717 gold price locked Britain to a de facto gold standard until 1931."),

    q(2, "3",
      f"In 1933 FDR signed EO 6102, forcing citizens to turn in gold at $20.67/oz. Months later the official price jumped to $35. What had Roosevelt done?",
      f"Confiscated private gold and devalued the dollar against it {D} a stealth wealth transfer",
      [
          f"Returned gold to citizens at a higher market price {D} a public transfer",
          f"Linked the dollar more strictly to gold than before {D} hardening discipline",
          f"Ended all government holdings of gold entirely {D} privatizing reserves",
      ],
      "EO 6102 (April 5, 1933) made private gold ownership a crime; citizens paid $20.67/oz, then FDR set the new price at $35/oz — a 40% dollar devaluation. Order lasted until 1974."),

    q(2, "3",
      f"From 1933 to 1974, US citizens couldn't legally own monetary gold {D} a 41-year ban under FDR's order. Ford restored the right in 1974. Why did the ban last so long?",
      f"Private gold competes with paper dollars as savings {D} citizens preferring gold weakens fiat",
      [
          f"Gold mining was an environmental hazard for decades {D} environmental policy",
          f"The Treasury needed all gold for industrial uses {D} strategic resource",
          f"Gold was reclassified as defense material like uranium {D} a security listing",
      ],
      "Citizens regained gold ownership in 1974, three years AFTER Nixon closed the gold window. By then, gold could not redeem dollars — it no longer threatened the fiat dollar."),

    # --- Bretton Woods / Nixon (5) ---
    q(2, "3",
      f"In July 1944 delegates from 44 Allied nations met at Bretton Woods, NH. Foreign currencies pegged to the dollar; dollars redeemed for gold at $35/oz. What did they create?",
      f"The Bretton Woods system {D} a gold-exchange standard with the dollar at the center",
      [
          f"The European Monetary Union {D} the 1999 euro",
          f"The General Agreement on Tariffs and Trade {D} a 1947 trade-cutting deal",
          f"The Smithsonian Agreement {D} 1971 fixed-rate revival",
      ],
      "Bretton Woods (July 1944) was negotiated by Harry Dexter White (US) and Keynes (UK). The dollar became global reserve. Collapsed in 1971."),

    q(2, "3",
      f"On Sun Aug 15, 1971, Nixon announced the US would no longer redeem dollars for gold. He called it temporary. Why pick Sunday night?",
      f"So global currency markets couldn't trade against the dollar before Monday {D} deliberate lockout",
      [
          f"The Federal Reserve board only meets on Sundays {D} so orders happen then",
          f"Gold trading naturally pauses on the Sabbath {D} markets already closed",
          f"The Treasury secretary requested a weekend rollout {D} routine administration",
      ],
      "Nixon's Aug 15, 1971 TV address closed the gold window. Sunday night meant Asia and Europe opened Monday into fait accompli."),

    q(2, "3",
      f"Nixon's 1971 closing of the gold window included a 90-day wage-price freeze, 10% import surcharge, and broken Bretton Woods. Treasury Secretary Connally told critics:",
      f"'The dollar is our currency, but it's your problem' {D} a candid statement of dollar hegemony",
      [
          f"'Gold is a barbarous relic' {D} a 1920s Keynes quote",
          f"'A central bank must serve only the people' {D} 1913 Fed slogan",
          f"'Free trade requires fixed exchange rates' {D} 1944 Bretton Woods talking point",
      ],
      "Connally's quip captured post-1971 reality: foreign dollar holders held a claim on more dollars. The dollar's reserve status rested on US power."),

    q(2, "3",
      f"Between 1971 and 1980, gold rose from $35/oz to about $850/oz {D} a roughly 24-fold increase. What does this measure?",
      f"A decade of pure-fiat inflation after the gold anchor was cut {D} sound money revaluing fiat",
      [
          f"A speculative gold bubble unrelated to monetary policy {D} investor mania",
          f"The natural result of new gold mining technology {D} a supply effect",
          f"Federal Reserve gold-price manipulation to favor industry {D} hidden subsidy",
      ],
      "1970s Great Inflation (CPI peaked at 14.8% in March 1980) and the gold spike are two sides of the same story: dollars printed faster than goods produced, and gold measured the debasement."),

    q(2, "3",
      f"From 1944 to 1971, gold traded at $35/oz. By 2024 it traded over $2,000. What does this comparison show?",
      f"A gold-tied dollar held value; a free-of-gold dollar lost most of it {D} sound outperforms fiat",
      [
          f"Gold mining became more efficient between 1971 and 2024 {D} supply explanation",
          f"The 1971 closing caused a one-time correction with no later weakness {D} orderly transition",
          f"Fed management kept the dollar strong against gold long-term {D} policy success",
      ],
      "The gold/dollar ratio is the cleanest long-run measure of dollar debasement: $35 (1971) to $2,000+ (2024) means the dollar has lost ~98% of purchasing power against gold."),

    # --- Weimar (5) ---
    q(2, "3",
      f"By Nov 1923 Weimar, a loaf of bread cost ~200 billion marks. People wheelbarrowed notes and burned them for heat. What had Germany done?",
      f"Printed marks for reparations and costs faster than goods were produced {D} fiat collapse",
      [
          f"Imposed a gold standard that raised bread prices artificially {D} backing failure",
          f"Restricted bread supply by law to ration food during famine {D} a deliberate restriction",
          f"Banned paper money for any food transactions {D} a payment ban",
      ],
      "Weimar hyperinflation (1921-1923) peaked at ~29,500% monthly inflation in October 1923. Eventually denominations reached 100-trillion-mark notes."),

    q(2, "3",
      f"At Weimar inflation's peak (autumn 1923), workers were paid TWICE A DAY to buy food before prices doubled. Wives met them at gates. What does this show?",
      f"Money lost its function as store of value first, then as unit of account {D} commerce broke down",
      [
          f"Weimar workers were unusually well-paid for the era {D} a prosperity sign",
          f"Banks closed at noon, so a midday wage was logistical {D} routine schedule",
          f"Twice-a-day pay was a German tradition predating inflation {D} unrelated custom",
      ],
      "When prices double in a day, money must be spent immediately. Workers became 'rent-seekers in reverse' — racing the printing press. Savings, contracts, pensions were destroyed."),

    q(2, "3",
      f"In Nov 1923 Weimar introduced the Rentenmark backed by farmland. One replaced one TRILLION papermarks. Hyperinflation stopped overnight. What does that prove?",
      f"Hyperinflation ends when the printing press credibly stops {D} monetary, not 'economic'",
      [
          f"Mortgage-backed money is the only stable form a currency can take {D} a permanent rule",
          f"Germans lost faith in paper but trusted handwriting {D} a cultural quirk",
          f"Hyperinflations end automatically after exactly 30 months {D} a natural cycle",
      ],
      "The Rentenmark (Nov 15, 1923) showed hyperinflation ends with monetary discipline. The damage was already done — middle-class savings wiped out."),

    q(2, "3",
      f"During Weimar hyperinflation, visitors with dollars found Germany absurdly cheap, buying hotels with pocket change. What mechanism is this?",
      f"Hyperinflation transfers wealth, failing-currency to hard-money {D} a wealth siphon",
      [
          f"Hyperinflation creates equal opportunity for all participants {D} a level playing field",
          f"Hyperinflation benefits domestic savers globally {D} an inverted savings boost",
          f"Hyperinflation lowers prices through more efficient production {D} a productivity gain",
      ],
      "Cantillon effect at scale: failing-currency holders lose; hard-currency holders win. The transfer of German wealth to foreign buyers (1922-23) became a political flashpoint."),

    q(2, "3",
      f"Weimar hyperinflation destroyed middle-class savings {D} pensions, insurance, bonds. Decades of saving became pennies. What political consequence followed?",
      f"A wounded middle class lost faith in liberal democracy {D} hyperinflation's longest shadow",
      [
          f"The middle class quickly switched to dollars and stayed stable {D} a smooth recovery",
          f"Hyperinflation boosted middle-class confidence in Weimar institutions {D} a confidence boost",
          f"German savers moved into government bonds and were protected fully {D} a clean escape",
      ],
      "Stefan Zweig wrote that the destruction of German savings did more lasting damage than the war itself. The middle class found institutions had quietly stolen everything."),

    # --- Hungarian pengo (3) ---
    q(2, "3",
      f"Hungary's 1945-46 hyperinflation was history's largest, prices doubling every 15 hours. The central bank issued a 100-QUINTILLION pengo note. What was the currency?",
      f"The pengo {D} replaced August 1946 by the forint, still in use today",
      [
          f"The deutschmark {D} replaced in 1923 Rentenmark",
          f"The leu {D} the Romanian currency its own postwar inflation",
          f"The koruna {D} Czechoslovak 1919-1990s",
      ],
      "Hungarian pengo hyperinflation (1945-46) peaked at ~41,900,000,000,000,000% monthly inflation (July 1946). Forint replaced it on August 1, 1946 at 1 forint = 400 octillion pengo."),

    q(2, "3",
      f"During Hungary's 1946 hyperinflation, the largest banknote ever (never circulated) was 1-SEXTILLION-pengo {D} (21 zeros). What's the irony of the biggest banknote?",
      f"It represented worthlessness {D} bigger the number, less the unit could buy",
      [
          f"It was the most valuable note ever held by one person {D} representing real wealth",
          f"It was the most counterfeited note in modern history {D} for its complex design",
          f"It paid for an entire Budapest mansion in one transaction {D} a real-estate sale",
      ],
      "The sextillion-pengo note (1946) was prepared but never released because the forint replaced the pengo first. Enormous denominations mark collapse, not wealth."),

    q(2, "3",
      f"Hungary's 1946 pengo collapse came from Soviet occupation, reparations, and printing. By summer 1946 the pengo was worth ~10^-20 of 1945 value. What replaced it?",
      f"The forint {D} introduced August 1, 1946 at one forint per 400 octillion pengo",
      [
          f"The US dollar {D} adopted by Hungary under postwar Marshall Plan agreement",
          f"The Soviet ruble {D} imposed on all USSR satellite states by 1946 mandate",
          f"The euro {D} a pan-European currency was created in 1946 to prevent inflation",
      ],
      "The 1946 forint stabilized Hungary's currency for the postwar Soviet bloc era. It remains the currency. Hyperinflation ends when the printing press as tax stops."),

    # --- Zimbabwe (4) ---
    q(2, "3",
      f"Zimbabwe printed a 100-trillion-dollar note in Jan 2009 {D} $100,000,000,000,000. When printed, it bought about one loaf of bread. What had Zimbabwe been doing?",
      f"Funding government deficits by printing money {D} fiat collapse when politicians can",
      [
          f"Trading bread directly for diamonds against neighbors {D} an exotic scheme",
          f"Adopting the US dollar early to stabilize {D} successful prevention",
          f"Refusing to print money, causing scarcity of goods {D} deflationary collapse",
      ],
      "Zimbabwe's hyperinflation under Mugabe (peak 89.7 sextillion percent month-on-month in Nov 2008) came from farm seizures and money-printing. The Zimbabwe dollar was abandoned April 2009."),

    q(2, "3",
      f"Zimbabwe's hyperinflation peaked at 89.7 sextillion% in Nov 2008. After abandoning the currency in April 2009, what did citizens use?",
      f"US dollars and South African rand {D} foreign hard currencies as money",
      [
          f"A new gold-backed Zimbabwe currency issued the same month {D} a monetary fix",
          f"Direct barter only, no currency used in transactions {D} primitive trade",
          f"Bitcoin, widely adopted across Zimbabwe by 2009 {D} an early crypto market",
      ],
      "From 2009-2019 Zimbabwe ran a 'multicurrency' regime with US dollar dominant. The government then re-launched its own currency, which started inflating again."),

    q(2, "3",
      f"Collectors sell the famous Zimbabwe 100-trillion note on eBay for $50-$100. The face value in 2009 was about a loaf of bread. What does this contrast show?",
      f"Scarcity determines value, not printed denomination {D} the lesson at the heart of sound money",
      [
          f"Banknotes retain value because they're objects too {D} a floor under fiat money",
          f"Collectors are irrational and overpay for worthless paper {D} a market failure",
          f"Zimbabwe recovered by 2010 making the notes precious {D} a recovery story",
      ],
      "Pre-collapse, the printing press destroyed any value the note's denomination implied. Post-collapse, the central bank stopped printing — artificial scarcity returned some collector value."),

    q(2, "3",
      f"Zimbabwe launched 'RTGS dollar' 2019, then gold-backed dollar 2024. The new currency has already lost value. What's the pattern?",
      f"A government that printed itself into collapse will do it again {D} fiat predictability",
      [
          f"Zimbabwe's central bank has learned from past mistakes {D} reform succeeded",
          f"Gold-backed currencies are inherently unstable by design {D} the 2024 currency proves it",
          f"The IMF blocks former hyperinflation states from currency {D} enforced rule",
      ],
      "Zimbabwe's pattern (hyperinflation → dollarization → relaunch → reinflation) shows institutional incentives, not lessons-learned, drive currency outcomes."),

    # --- Yugoslav dinar (3) ---
    q(2, "3",
      f"From 1992-94 Yugoslavia's hyperinflation peaked at 313M% in Jan 1994. The bank printed a 500-billion-dinar note. Why does monetary collapse track political collapse?",
      f"Governments under stress reach for the press {D} fiat is the last resort of failing states",
      [
          f"Wars destroy money-printing equipment, causing price changes {D} a logistics issue",
          f"Political collapse reduces production faster than money supply grows {D} supply problem",
          f"Hyperinflations happen randomly with no link to politics {D} pure coincidence",
      ],
      "Yugoslav dinar hyperinflation (1992-94) peaked at 313,000,000% monthly inflation. The 'super dinar' replaced it in January 1994."),

    q(2, "3",
      f"During Yugoslavia's 1993-94 hyperinflation, Belgrade shopkeepers changed prices THREE TIMES A DAY. People raced to spend dinars before meals. What is this behavior called?",
      f"Money refusing to function as store of value {D} the 'flight from money' that defines hyperinflation",
      [
          f"Rational saving behavior under expected inflation {D} prudent planning",
          f"Government-mandated price discipline to slow rate hikes {D} a regulatory technique",
          f"A cultural preference for fresh food driving small purchases {D} unrelated to inflation",
      ],
      "When inflation runs hot, holding money for a day means losing purchasing power. Velocity skyrockets, which itself accelerates inflation."),

    q(2, "3",
      f"Yugoslavia's hyperinflation ended Jan 1994 with a 'super dinar' pegged to the German mark. Inflation went from 313M% to near zero overnight. What's the lesson?",
      f"Hyperinflation ends when the printing stops, not when prices drop {D} the cause is monetary",
      [
          f"Hyperinflation ends naturally after 24 months {D} a self-correcting cycle",
          f"Pegging to a foreign currency always fails {D} pegs are unstable",
          f"Citizens drop out of the economy until inflation cools {D} a behavioral cycle",
      ],
      "The 1994 'super dinar' stabilization is among the clearest natural experiments in monetary economics. Same country, same people — printing press stopped, inflation collapsed in days."),

    # --- Venezuela / Argentina / Lebanon (5) ---
    q(2, "3",
      f"Venezuela's bolívar lost 99.99%+ from 2017-2023 under Maduro, peaking at ~1M% in 2018. Citizens dropped it for dollars, gold, and bitcoin. What had the government done?",
      f"Funded social programs by printing as oil revenues collapsed {D} fiat-collapse playbook",
      [
          f"Pegged the bolívar to gold and ran out of reserves {D} a gold-standard failure",
          f"Adopted the US dollar voluntarily early in the cycle {D} successful prevention",
          f"Banned all government spending to fight inflation {D} an austerity story",
      ],
      "Venezuelan hyperinflation peaked around 130,060% in 2018 (IMF estimate). By 2023 most transactions had unofficially dollarized."),

    q(2, "3",
      f"By 2019 Venezuela had hyperinflation, 7M+ emigrants, collapsed ration cards. Many adopted bitcoin and dollars. Why does sound money matter most when government fails?",
      f"Sound money survives political collapse {D} fiat is only as good as its issuer",
      [
          f"Sound money lets governments tax more in crisis {D} a state-strengthening tool",
          f"Sound money requires a working central bank {D} a state-dependent technology",
          f"Sound money only works in stable wealthy democracies {D} an inverse-need rule",
      ],
      "Venezuelan adoption of bitcoin (LocalBitcoins P2P volumes peaked 2019-2020) and dollars made the country a real-world case for sound money's role during collapse."),

    q(2, "3",
      f"Argentina has had recurring hyperinflation since the 1970s. By 2023 inflation hit 211%. Javier Milei (2023) campaigned with a chainsaw against the central bank. What school does Milei cite?",
      f"The Austrian school {D} Mises, Hayek, Rothbard, and Argentine Austrians",
      [
          f"Keynesian macroeconomics {D} the dominant postwar US and UK framework",
          f"Marxist economics {D} the school dominant in Soviet and Maoist planning",
          f"Modern Monetary Theory {D} Stephanie Kelton's 2020 book framework",
      ],
      "Milei's 2023 campaign repeatedly cited Mises, Hayek, Rothbard, and Murray Rothbard's anarcho-capitalism. He proposed closing the Argentine central bank and dollarizing."),

    q(2, "3",
      f"Lebanon's pound lost 98%+ from 2019-23 after the central bank's peg collapsed. ATMs gave worthless bundles. What had Lebanon's central bank been doing?",
      f"Running a fixed-peg scheme funded by depositor money like a Ponzi {D} the peg held until it didn't",
      [
          f"Adopting bitcoin too early and losing reserves to volatility {D} crypto-experiment failure",
          f"Refusing all foreign aid out of national pride {D} isolation story",
          f"Letting the currency float freely against the dollar {D} a market-based approach",
      ],
      "Lebanon's central bank ran a Ponzi-like 'financial engineering' scheme: paying high interest on lira deposits using new foreign deposits, then defaulting in 2019."),

    q(2, "3",
      f"Lebanon's 2019-2023 collapse limited withdrawals; ATMs ran dry; the lira lost 98%. The government refused to devalue or default. What happened to ordinary savings?",
      f"Trapped in failing banks, paid in worthless lira {D} silent confiscation through inflation",
      [
          f"Insured by an international guarantor {D} a successful safety net",
          f"Restored automatically when the currency stabilized in 2023 {D} clean recovery",
          f"Returned in US dollars under a special IMF program {D} an international rescue",
      ],
      "Lebanon's 'lirafication' of US dollar deposits at fictional exchange rates is a textbook case: a central-bank crisis becomes a depositor crisis. Cyprus 2013 and Argentina 2001 had similar patterns."),

    # --- Assignats / Continental / Confederate (5) ---
    q(2, "3",
      f"During the French Revolution (1789-1796), the new government issued 'assignats' backed by confiscated church lands. Presses ran; prices soared. By 1796 assignats were worthless. What was the lesson?",
      f"Backing doesn't restrain over-issuing governments {D} only honest issuers honor it",
      [
          f"Land-backed currencies are more stable than gold {D} a permanent rule",
          f"The assignat was a success inspiring central banks {D} a positive legacy",
          f"Paper money fails in revolutions, works in democracies {D} a regime-type rule",
      ],
      "Assignats (1789-1796) are the textbook case of paper-money over-issue under political pressure. Andrew Dickson White's 1896 essay 'Fiat Money Inflation in France' is the canonical short history."),

    q(2, "3",
      f"During the American Revolution, the Continental Congress printed 'Continentals' to fund the war. By 1781 one was worth ~1/40 silver dollar. What phrase entered English?",
      f"'Not worth a Continental' {D} meaning utterly worthless, lasting over a century",
      [
          f"'Worth its weight in gold' {D} the original Revolutionary expression",
          f"'A penny saved is a penny earned' {D} Franklin's Continental phrase",
          f"'In God we trust' {D} a Continental Congress paper-money slogan",
      ],
      "The Continental's collapse (1775-1781) entered American folk wisdom. The Founders' subsequent monetary caution (Article I Section 10 forbade state paper money) traces here."),

    q(2, "3",
      f"The Confederacy printed money for the Civil War. By 1865 the dollar was worth ~0.5 cents in gold {D} a 99.5% loss. What does this say about war-finance?",
      f"Wartime governments reach for the printing press {D} fiat as short-term tax",
      [
          f"Confederate currency destroyed by Union spies {D} a sabotage story",
          f"Confederacy currency was gold-backed, lost via mining {D} a supply story",
          f"Civil-war currencies always recover postwar {D} a postwar restoration",
      ],
      "The Confederate dollar's collapse parallels the Continental's a century earlier and Weimar's a half-century later. Unable to tax, the CSA paid by printing."),

    q(2, "3",
      f"The Union also printed money during the Civil War {D} the 'greenbacks,' for green ink. Greenbacks lost value vs gold but recovered, returning to par by 1879. Why did greenbacks survive while Confederate didn't?",
      f"The Union won and could credibly redeem greenbacks later {D} backing is issuer's future",
      [
          f"Union greenbacks were printed on better paper {D} a durability story",
          f"Greenbacks were backed by western silver {D} a commodity-backed currency",
          f"Confederate notes were declared illegal in 1862 {D} a legal coup",
      ],
      "The Union greenback's recovery (Resumption Act 1875, par restored 1879) vs Confederate collapse: fiat value is the market's estimate of an issuer's future commitment."),

    q(2, "3",
      f"Across centuries: Roman 200+; Continental 6; assignat 7; Confederate 4; Weimar 5; Zimbabwe a decade; Venezuela ongoing. What pattern emerges?",
      f"Every fiat currency in history has eventually been debased or replaced {D} the record is uniform",
      [
          f"Roughly half of fiat currencies have held value over centuries {D} a mixed record",
          f"Only revolutionary or wartime currencies have collapsed {D} a special-conditions rule",
          f"Modern central banks have ended the cycle since 1971 {D} a permanent achievement",
      ],
      "Voltaire's reported aphorism: 'paper money eventually returns to its intrinsic value — zero.' The question for modern fiat is not 'whether' but 'when.'"),

    # --- Bitcoin as modern sound money (3) ---
    q(2, "3",
      f"Bitcoin's supply is in code: 50 BTC/block at 2009 launch, halving every 210K blocks, reaching ~21M by 2140. Compare to dollars (Fed) or gold (mining tech). What is unique?",
      f"Programmatically scarce {D} the supply curve is enforced by code, not any institution",
      [
          f"Centrally managed by the Bitcoin Foundation {D} a board votes annually",
          f"Linked to gold by an automated formula {D} digital gold standard",
          f"Adjusted each year to match global inflation rates {D} inflation-tracking currency",
      ],
      "Bitcoin's 21M cap is enforced by every node running the protocol. Changing it would require near-universal consensus of an adversarial decentralized network — historically impossible."),

    q(2, "3",
      f"Sound-money advocates note gold's 'monetary metal' problems: hard to divide, verify, transport. A scarce alternative was needed. What did Bitcoin solve gold couldn't?",
      f"Digital portability, instant verification, perfect divisibility {D} digital sound money",
      [
          f"Government acceptance for tax payment {D} feature gold lacks",
          f"Inflation-adjusted yields competing with bonds {D} a return-generating asset",
          f"Industrial uses in electronics that gold lacks {D} industrial-demand source",
      ],
      "Bitcoin: scarcity (21M cap), portability (sent globally in minutes), divisibility (1 sat = 0.00000001 BTC), verifiability (any node checks). Addresses gold's practical weaknesses."),

    q(2, "3",
      f"On Sept 7, 2021 El Salvador's Bukele made bitcoin legal tender. The IMF condemned the policy. Why is sound money politically threatening?",
      f"It removes silent taxation through inflation {D} a leash on printing",
      [
          f"It exposes corruption via public transactions {D} a transparency feature",
          f"It causes recessions through deflation {D} a deflationary catastrophe",
          f"It enriches central banks at citizens' expense {D} inversion of usual concern",
      ],
      "El Salvador's bitcoin adoption (Sept 7, 2021) was the first nation-state recognition. IMF opposition reflects the threat sound money poses to inflation-financing of deficits."),

    # --- Wrap-up / meta (2) ---
    q(2, "3",
      f"In 1976 Hayek's 'Denationalisation of Money' argued the government currency monopoly causes instability. He proposed competing private currencies. What did Hayek argue?",
      f"Money should be produced competitively by private issuers {D} free currency market",
      [
          f"Gold should be the only legal currency {D} a single-commodity system",
          f"Central banks should target 2% inflation {D} modern targeting framework",
          f"Money is a state creation, can't exist privately {D} chartalist theory",
      ],
      "Hayek's *Denationalisation of Money* (1976) bridges the gold standard's collapse and Bitcoin's emergence. Bitcoin is closer to that vision than anything before it."),
]

assert len(P3) == 40, f"P3 count {len(P3)}"


# =========================================================================
# P4 CENTRAL BANKING + KEYNES/MMT CRITIQUE (45)
# =========================================================================

P4 = [
    # --- Jekyll Island + Fed creation (5) ---
    q(2, "4",
      f"In Nov 1910, six men boarded a private rail car at Hoboken, NJ for Jekyll Island, Georgia. Aldrich (Senator), Davison (JP Morgan), Warburg (Kuhn Loeb) used only first names. What did they draft?",
      f"The Aldrich Plan {D} the blueprint that became the Federal Reserve Act of 1913",
      [
          f"The Glass-Steagall Act {D} the 1933 law separating commercial and investment banking",
          f"The Bretton Woods Agreement {D} the 1944 postwar deal fixing exchange rates",
          f"The Sherman Antitrust Act {D} the 1890 law breaking up industrial trusts",
      ],
      "Jekyll Island (November 1910) is the founding moment of modern US central-banking. G. Edward Griffin's *The Creature from Jekyll Island* (1994) is the canonical popular account."),

    q(2, "4",
      f"On Dec 23, 1913 Woodrow Wilson signed the Federal Reserve Act {D} two days before Christmas, many Senators gone. Why does the timing matter to historians?",
      f"It eased passage of a controversial bill {D} thin Congress + recess reduced opposition",
      [
          f"Christmas legislation was traditionally most carefully debated {D} December was a serious month",
          f"Wilson acted before Christmas under wartime emergency {D} the US was already in WWI",
          f"It was the same day the gold standard was suspended {D} a coordinated monetary reset",
      ],
      "The Dec 23, 1913 signing has long been cited by critics. Congress was thin; opposition disorganized. 'Public agency' framing helped the banker-friendly design pass."),

    q(2, "4",
      f"The Fed has 12 regional Reserve Banks owned by member commercial banks, overseen by a Washington Board appointed by the President. Why does this hybrid structure matter?",
      f"Public-private hybrid {D} the Fed escapes democratic oversight AND market competition",
      [
          f"Guarantees the Fed makes no policy errors {D} regional diversity removes bias entirely",
          f"Makes Fed governors elected officials {D} a clean democratic structure",
          f"Privatizes the Fed with no government oversight {D} a pure-market arrangement",
      ],
      "The Fed's structure gives it patronage protections of a state agency AND institutional-capture risks of a private cartel. Rothbard's critique focused on this hybrid."),

    q(2, "4",
      f"The Fed's 'dual mandate' (Humphrey-Hawkins 1978) pursues maximum employment AND stable prices. Critics note these goals can conflict. What's the structural problem?",
      f"Rising inflation with employment forces the Fed to violate one mandate {D} conflict is built in",
      [
          f"The two goals always move together so no conflicts arise {D} a frictionless setup",
          f"Other central banks have similar mandates that work perfectly {D} a tested arrangement",
          f"The mandate explicitly prioritizes employment over prices {D} a clear ranking",
      ],
      "Conflict was most visible 2021-22: as inflation hit 9.1%, the Fed delayed raising rates because the labor market was 'tight.' By March 2022 inflation was entrenched."),

    q(2, "4",
      f"From 1933 to 1974, US citizens couldn't legally own monetary gold {D} a 41-year ban under FDR's EO 6102. Ford restored the right in 1974. Why did the ban last so long?",
      f"Private gold competes with paper dollars as savings {D} citizens preferring gold weakens fiat",
      [
          f"Gold mining was an environmental hazard for decades {D} environmental policy",
          f"The Treasury needed all gold for industrial uses {D} strategic resource",
          f"Gold was reclassified as defense material like uranium {D} a security classification",
      ],
      "Citizens regained gold rights three years AFTER Nixon closed the gold window. By then, gold couldn't redeem dollars — it no longer threatened the fiat dollar."),

    # --- Fed + Great Depression (5) ---
    q(2, "4",
      f"In 1963 Milton Friedman and Anna Schwartz published 'A Monetary History of the United States 1867-1960.' Their finding: the Fed CAUSED the Great Depression by letting money supply contract 1929-33. By how much?",
      f"About one-third (33%) {D} the largest US monetary contraction",
      [
          f"About one percent (1%) {D} routine seasonal variation",
          f"About one-tenth of one percent (0.1%) {D} statistical noise",
          f"About one half of one percent (0.5%) {D} less than supply grew in 1929",
      ],
      "Friedman + Schwartz (1963) reframed Great Depression historiography. The Fed, created 1913 to prevent panics, presided over the worst banking collapse."),

    q(2, "4",
      f"At Friedman's 2002 90th birthday, Fed Governor Bernanke admitted: 'Regarding the Great Depression, you're right, we did it. We're very sorry.' What was Bernanke conceding?",
      f"Fed caused the Depression by letting money supply collapse {D} the Friedman thesis",
      [
          f"Fed was correct to contract money in 1929-33 {D} validating policy",
          f"Depression caused by Hoover's tariff policy {D} blame Smoot-Hawley",
          f"Central banks have no influence on panics {D} denying monetary causation",
      ],
      "Bernanke's 2002 admission was as close to an official Fed mea culpa as exists. The institution created to prevent panics caused the worst one. The same Bernanke chaired the Fed in 2008."),

    q(2, "4",
      f"Between 1929-33, 9,000+ US banks failed with depositor savings. The 1913 Fed was created to prevent panics. What does this gap illustrate?",
      f"Crisis-prevention institutions can become the cause {D} mission vs outcome",
      [
          f"Banking panics are inevitable; no policy could prevent them {D} a denial of causation",
          f"The 1913 Fed Act was correct; 1929 crisis was external {D} a clean exoneration",
          f"Depositors caused their own losses by withdrawing in 1929 {D} a customer-fault analysis",
      ],
      "The Fed's 1929-33 failure is the central case study in institutional-capture-wearing-public-clothing. Purpose, authority, resources — and the worst banking panic in US history."),

    q(2, "4",
      f"Responding to the 1933 banking collapse, Congress passed Glass-Steagall, separating commercial banking from investment banking. The act stayed until 1999. What was its insight?",
      f"Mixing deposits with speculation risks taxpayer-backed gambling {D} separation of functions",
      [
          f"Investment banking is more profitable separated {D} a profitability argument",
          f"Commercial banks should be banned from business loans {D} a lending restriction",
          f"All banks should be Fed-nationalized {D} a state-banking model",
      ],
      "Glass-Steagall (1933) and its 1999 repeal (Gramm-Leach-Bliley Act) bracket the modern banking story. Critics link the 1999 repeal to the 2008 financial crisis."),

    q(2, "4",
      f"Rothbard's 'America's Great Depression' (1963) argued the 1920s boom was itself caused by Fed credit expansion, so the 1929 crash was the inevitable correction. What Austrian framework did he apply?",
      f"Austrian Business Cycle Theory {D} central-bank credit expansion creates booms that must bust",
      [
          f"Keynesian aggregate demand theory {D} New-Deal framework dominant from 1933",
          f"Monetarist quantity theory {D} the Friedman framework on money supply",
          f"Marxist crisis theory {D} capitalism's internal contradictions cause collapse",
      ],
      "Rothbard's *America's Great Depression* (1963) appeared the same year as Friedman + Schwartz's *Monetary History*. Both blamed the Fed, but Rothbard went further: the boom itself was the Fed's doing."),

    # --- Volcker era (3) ---
    q(2, "4",
      f"Paul Volcker became Fed Chairman in August 1979 facing 12%+ inflation. He raised the fed funds rate to nearly 20% by 1981, triggering recession. By 1983 inflation dropped to 3%. What does this demonstrate?",
      f"High rates can break inflation {D} when the central bank chooses, it can",
      [
          f"Inflation always falls on its own without action {D} self-correcting",
          f"Recessions cause inflation rather than the reverse {D} reverse causation",
          f"Inflation cannot be controlled below 5% in modern economies {D} a permanent floor",
      ],
      "Volcker's 1979-82 anti-inflation campaign is the cleanest postwar case of central-bank discipline breaking entrenched inflation. The cost was the 1981-82 recession (peak unemployment 10.8%)."),

    q(2, "4",
      f"Paul Volcker reportedly carried a card listing his 1979 salary ($60,662) and what it would buy in earlier years. Why would the Fed Chairman track his salary against inflation?",
      f"To stay viscerally aware of what inflation steals from wage earners {D} a memory device about human cost",
      [
          f"To negotiate his own pay raises with the Fed Board annually {D} routine HR",
          f"To prove inflation does not exist and was media invention {D} inflation denial",
          f"To compare with other central bankers' international salaries {D} benchmarking",
      ],
      "Volcker's salary card (told in *Keeping At It*) became a symbol of personal seriousness about price stability. He saw inflation as theft from workers."),

    q(2, "4",
      f"During Volcker's tight-money campaign (1979-82), unemployment topped 10%, farmers protested, bankruptcies spiked. Volcker faced threats but stayed the course. What's the lesson?",
      f"Breaking inflation is costly; requires a banker who absorbs the politics {D} discipline has a price",
      [
          f"Anti-inflation policy is painless and produces only benefits {D} a free-lunch policy",
          f"Anti-inflation policy only succeeds during economic booms {D} timing requirement",
          f"Anti-inflation policy maximizes employment long-run {D} no trade-off",
      ],
      "Volcker's experience is the counterfactual to every subsequent Fed chair who lacked the spine to break inflation early."),

    # --- 2008 GFC + bailouts (5) ---
    q(2, "4",
      f"On Sept 15, 2008 Lehman Brothers filed the largest ever {D} $619B in debts. Bear Stearns bailed in March; AIG the day after. Why was 'too big to fail' the lesson?",
      f"Banks learned risk-taking would be socialized {D} built-in moral hazard",
      [
          f"Banks learned shareholders would absorb losses {D} clean accountability",
          f"Federal regulators stopped tolerating risky behavior afterward {D} reform success",
          f"Lehman's bankruptcy ended bailouts entirely under law {D} precedent against rescue",
      ],
      "TARP (October 2008, $700B), AIG bailout ($182B), Fed emergency lending, ZIRP, QE — transferred losses from financial institutions to taxpayers, savers, and future generations."),

    q(2, "4",
      f"In Oct 2008 Congress passed TARP, authorizing $700B for 'troubled assets.' Treasury Secretary Paulson told Congress: pass or face collapse. What does this illustrate?",
      f"Crisis manufactures consent for unthinkable measures {D} use the moment",
      [
          f"Bailouts had unanimous bipartisan support across both parties {D} smooth consensus",
          f"TARP was the smallest bailout in postwar history {D} modest intervention",
          f"Congress carefully debated TARP for over a year before passing {D} deliberation",
      ],
      "TARP passed October 2008 with limited debate. Rahm Emanuel's 'never let a crisis go to waste' captured the dynamic. The pattern repeated in 2020 with $4-5T in pandemic spending."),

    q(2, "4",
      f"After 2008 the Fed launched 'QE': large-scale Treasury and mortgage purchases via new bank reserves. The Fed's balance sheet grew from ~$900B (2008) to over $4T by 2014. What is QE economically?",
      f"Money creation aimed at financial markets {D} reserves buy bonds, lifting asset prices",
      [
          f"Direct stimulus payments sent to American households {D} a fiscal transfer",
          f"Tax cuts financed by reduced government spending {D} supply-side policy",
          f"International currency support coordinated abroad {D} an exchange-rate move",
      ],
      "QE inflates asset prices (Cantillon effect: those holding stocks and houses gain; wage earners and savers lose) while officially seeking 'employment' and 'price stability.'"),

    q(2, "4",
      f"ZIRP ran Dec 2008 to Dec 2015 {D} seven years of near-zero fed funds rate. Austrian critics argued this was the canonical ABCT setup. What did they predict?",
      f"Malinvestment in rate-sensitive sectors busting at normalization {D} ABCT applied",
      [
          f"Permanent prosperity with no future correction {D} a free-lunch policy",
          f"Immediate deflation rather than later inflation {D} a deflationary spiral",
          f"Bond market collapse within six months {D} near-term crisis",
      ],
      "Post-2015 normalization produced the December 2018 stock-market drop. Then COVID shattered the trajectory in March 2020."),

    q(2, "4",
      f"From 2008-2020 the Fed held rates at or near 0% for most of 12 years. March 2020 saw rates back at zero with massive new QE. What does a 12-year zero-rate policy do structurally?",
      f"Distorts capital toward cheap-credit beneficiaries {D} Cantillon asset inflation",
      [
          f"Distributes wealth equally to all {D} level playing field",
          f"Punishes asset holders, rewards wage earners {D} a redistributive policy",
          f"No effect on economic structure {D} neutral policy",
      ],
      "Twelve years of zero rates produced rising asset prices, debt-financed buybacks, suppressed bond yields driving savers into riskier assets. Post-2020 inflation was the eventual correction."),

    # --- 2020 pandemic + inflation (5) ---
    q(2, "4",
      f"March 2020: Fed cut rates to near zero, opened lending facilities, resumed QE. Congress passed CARES Act ($2.2T) and follow-ups (~$5T total). What did this combination produce by 2022?",
      f"Highest inflation since the early 1980s {D} 9.1% CPI in June 2022, as monetary theory predicted",
      [
          f"Stable prices and the smoothest recovery since WWII {D} textbook crisis response",
          f"Persistent deflation through 2023 {D} falling prices",
          f"No measurable change in inflation through 2022 {D} no inflation effect",
      ],
      "US CPI inflation hit 9.1% year-on-year in June 2022 — the highest since November 1981. Larry Summers had warned in February 2021."),

    q(2, "4",
      f"In Feb 2021 Larry Summers warned in the Washington Post that the $1.9T American Rescue Plan would cause inflation 'of a kind we have not seen in a generation.' MMT advocates dismissed him. Who was right?",
      f"Summers right {D} US inflation hit 9.1% in June 2022, the magnitude he warned about",
      [
          f"The MMT advocates were right {D} stayed below 3%",
          f"Both were wrong {D} severe deflation occurred",
          f"Neither addressed the actual cause {D} Ukraine-caused inflation",
      ],
      "Summers' February 2021 column has aged extraordinarily well. The 2021-22 inflation was the cleanest natural experiment in post-Keynesian monetary economics."),

    q(2, "4",
      f"During 2021-22 the Fed called inflation 'transitory' before pivoting to aggressive hikes from March 2022. Fed funds rate climbed from 0.25% to 5.5% by 2023. What did 'transitory' get wrong?",
      f"Inflation persisted because money creation was real {D} cause was monetary",
      [
          f"Inflation was transitory; media caused panic {D} media-perception problem",
          f"Inflation persistence came from Ukraine invasion {D} geopolitical cause",
          f"Political pressure forced hikes, not data {D} political pressure",
      ],
      "Fed Chair Powell described 2021 inflation as 'transitory' through most of 2021, then retired the word in November 2021. The delayed pivot likely worsened the eventual inflation."),

    q(2, "4",
      f"From March 2022 to July 2023 the Fed raised rates 0.25% to 5.5% in the fastest cycle since Volcker. The pace caused Silicon Valley Bank to fail (March 2023). What does this connect?",
      f"Easy money creates fragility, exposed when policy tightens {D} bust reveals boom's distortions",
      [
          f"Higher rates create banks, lower dissolve {D} reverse causation",
          f"Bank failures unrelated to monetary policy {D} unrelated events",
          f"SVB failed for reasons unrelated to the Fed {D} management failure",
      ],
      "SVB's failure (March 10, 2023) traced to long-duration Treasury holdings purchased during ZIRP that lost mark-to-market value when rates rose. Signature and First Republic followed."),

    q(2, "4",
      f"Post-pandemic US debt rose from ~$23T (end 2019) to over $35T by 2024 {D} a $12T increase in five years. Interest now exceeds the defense budget. What's the structural problem?",
      f"Compounding interest is the largest item {D} the math of debt service grows without bound",
      [
          f"Higher debt grows the economy more {D} Keynesian expansion",
          f"Interest payments don't affect growth {D} neutrality",
          f"Debt service paid only when Fed authorizes {D} discretionary",
      ],
      "US net interest payments on federal debt crossed $1 trillion annually in 2024 — more than total defense spending. The fiscal trajectory becomes the monetary problem."),

    # --- Keynes + General Theory (5) ---
    q(2, "4",
      f"Keynes's 1936 'The General Theory' reshaped postwar Anglo-American economics and justified decades of deficit spending. What was Keynes's central argument?",
      f"Government should run deficits to boost demand {D} the 'stimulus' framework",
      [
          f"Government should cut spending, raise taxes {D} opposite of Keynes",
          f"All recessions are monetary, central-bank only {D} monetarist framework",
          f"Recessions must run their course {D} do-nothing",
      ],
      "Keynes's *General Theory* (1936) introduced aggregate demand, the multiplier, the marginal propensity to consume, animal spirits, and the liquidity trap. Its policy implication became postwar consensus."),

    q(2, "4",
      f"Responding to Keynes 1936, Austrians (Mises 1912, Hayek 1931) argued cycles are monetary, not psychological. What did Austrians critique about 'animal spirits' framing?",
      f"It treated investor mood as the cause when artificial credit expansion was the actual cause {D} wrong diagnosis",
      [
          f"It correctly identified all causes of business cycles {D} Austrians embraced mood",
          f"It blamed bank lending instead of psychology {D} misreading Keynes",
          f"It treated the gold standard as the source of cycles {D} a different mechanism",
      ],
      "Keynes's 'animal spirits' replaces monetary causes with psychological ones. If cycles are mood-driven, the cure is government spending; if monetary, the cure is sound money."),

    q(2, "4",
      f"Keynes's famous quip: 'In the long run we are all dead.' Critics see this as the core of policies producing short-term benefits and long-term costs. What's the Austrian counter?",
      f"Long-run, the same people who benefit short-term are alive paying costs {D} the future arrives",
      [
          f"Austrians agree long-run effects are negligible {D} alignment with Keynes",
          f"Austrians say long-run positive when short-run negative {D} inversion",
          f"Austrians treat 'long run' as a meaningless concept {D} a denial of long-run effects",
      ],
      "Keynes died in 1946; many policies he influenced kept compounding for decades. Henry Hazlitt argued long-run analysis is what economic reasoning requires."),

    q(2, "4",
      f"Keynes's 1919 'Economic Consequences of the Peace' predicted Versailles reparations would destabilize Europe. He was vindicated. What does this say about his track record?",
      f"Sharp on diagnosis (1919); his 1936 deficit prescription is contested {D} not all survives",
      [
          f"Keynes was always wrong about everything {D} blanket dismissal",
          f"Keynes was always right about everything {D} blanket endorsement",
          f"Keynes was wrong in 1919 but right in 1936 {D} inversion of the historical record",
      ],
      "Keynes's 1919 essay correctly predicted Weimar instability. His 1923 *Tract on Monetary Reform* had sharp inflation insights. The 1936 *General Theory* is contested."),

    q(2, "4",
      f"In 1931 LSE invited Hayek to give four lectures challenging Keynes at Cambridge. The debate became one of 20th-century econ's most-cited rivalries. What was the methodological difference?",
      f"Hayek: capital has structure; Keynes: output is aggregate {D} structure vs aggregate",
      [
          f"Hayek favored deficits; Keynes opposed {D} inversion of their actual positions",
          f"They agreed on policy but disagreed on math {D} non-substantive disagreement",
          f"Hayek said cycles are random; Keynes said they follow patterns {D} inverted reading",
      ],
      "Hayek's LSE lectures became *Prices and Production* (1931). The Austrian-Keynesian methodological divide — capital structure vs aggregate demand — remains the central dispute."),

    # --- MMT (5) ---
    q(2, "4",
      f"Kelton's 2020 'The Deficit Myth' became MMT's most influential popular statement. Core claim: a government issuing its own currency can't 'run out of money.' What's the implicit policy implication?",
      f"Government can finance programs without budget worry {D} 'deficits don't matter'",
      [
          f"Government should run balanced budgets {D} opposite of MMT",
          f"Government should cut spending to lows {D} budget austerity",
          f"Government funds only military via deficits {D} defense-only exception",
      ],
      "Kelton's *Deficit Myth* (2020) catalyzed MMT's mainstream moment. The 2021-23 inflation followed the largest peacetime deficit spending in US history."),

    q(2, "4",
      f"MMT's formal theory acknowledges that inflation is the real constraint on deficit spending {D} a government can print money until prices rise. The 2021-2023 US inflation hit 9.1%. What did that period demonstrate?",
      f"The constraint arrived larger and faster {D} MMT's stance was falsified",
      [
          f"MMT confirmed since inflation came down {D} MMT success",
          f"MMT is wartime only; peacetime data irrelevant {D} scope limitation",
          f"MMT confirmed: no government ran out {D} literal defense",
      ],
      "MMT's formal text acknowledges inflation; political deployment downplayed it. 2021-23 showed the constraint arrives larger, faster, stickier than advocates suggested."),

    q(2, "4",
      f"In 2020-21 MMT advocates argued pandemic deficits wouldn't cause inflation. Summers, Blanchard, Rogoff (establishment, not Austrian) warned of inflation risk. Who was vindicated?",
      f"Summers, Blanchard, Rogoff {D} the inflation arrived as warned at the predicted magnitude",
      [
          f"The MMT advocates {D} inflation stayed below 3% in 2021-22 as predicted",
          f"Both groups were equally wrong {D} Ukraine-caused 2022",
          f"Neither group has been vindicated {D} data is unclear",
      ],
      "The 2021 prediction race was unusually clean. Summers (Feb 2021), Blanchard (Feb 2021), and Rogoff publicly warned. The 2022 9.1% CPI peak settled it."),

    q(2, "4",
      f"MMT founder Warren Mosler proposed an 'Employer of Last Resort' (ELR): the government offers anyone a guaranteed set-wage job. What's the Austrian critique?",
      f"It removes labor-market price signals {D} government sets wages instead of letting markets discover them",
      [
          f"It costs too much to administer {D} budget overhead concern",
          f"It works in theory but only in monarchies {D} political-system limit",
          f"It would reduce unemployment to zero permanently {D} success claim",
      ],
      "Austrian critique of ELR: a guaranteed-job-at-set-wage distorts labor markets, removes wage-discovery, anchors wages to government, creates dependency."),

    q(2, "4",
      f"MMT's Kelton predicted in March 2021 stimulus would NOT cause inflation {D} she pushed for $1.9T+ in spending. By June 2022 US inflation hit 9.1%. What does this tell us?",
      f"Formal theory survives; political deployment falsified {D} the bill came due",
      [
          f"MMT's formal theory was falsified and is no longer taught {D} academic-status claim",
          f"MMT's predictions were perfectly accurate throughout 2021-2023 {D} defense of MMT",
          f"MMT was never tested in 2021-23 because the stimulus was too small {D} scope defense",
      ],
      "MMT advocacy in 2020-2021 lined up with peak political demand for unlimited stimulus. The 2021-23 inflation put the framework's policy enthusiasm to the test."),

    # --- Hayek-Keynes + Austrian-defense (5) ---
    q(2, "4",
      f"Hayek's 1944 'Road to Serfdom' said central planning drifts toward authoritarianism, coercing to substitute for missing information. What was Hayek's prediction?",
      f"Central planning ends in coercion {D} calculation argument's conclusion",
      [
          f"Central planning succeeds in democracies, fails in monarchies {D} regime-type limit",
          f"Central planning works with PhD planners {D} expertise defense",
          f"Central planning beats markets {D} pro-planning claim",
      ],
      "*The Road to Serfdom* (1944) was Hayek's most influential popular work. A warning to British and American audiences about WWII-era central planning bleeding into the postwar period."),

    q(2, "4",
      f"Hayek won the 1974 Nobel in Economics with Gunnar Myrdal {D} a deliberately ideologically-balanced choice. What did Hayek's Nobel lecture argue mainstream economics had become?",
      f"Pretense of scientific precision via math {D} 'the pretense of knowledge'",
      [
          f"Too humble about its own predictive power {D} too humble on models",
          f"Correctly grounded in mathematical methods from physics {D} defending econometrics",
          f"Properly skeptical of free-market arguments {D} endorsing intervention",
      ],
      "Hayek's 1974 Nobel lecture 'The Pretence of Knowledge' is one of the most influential brief critiques ever delivered. Mainstream economics had adopted physics-envy without underlying regularities."),

    q(2, "4",
      f"Mises left Vienna 1934 ahead of the Nazis, taught Geneva, came to US 1940. He held an unpaid NYU position 1945-69. Why did the most influential Austrian never hold a paid US academic post?",
      f"Free-market views unacceptable to Keynesian postwar academy {D} institutional capture",
      [
          f"Mises was independently wealthy and preferred unpaid work {D} personal preference",
          f"Mises spoke poor English throughout his US career {D} language barrier",
          f"NYU was the only school considering Austrian economics {D} single-institution claim",
      ],
      "Mises's NYU appointment was funded externally (Volker Fund and others). The Austrian school survived via FEE 1946, Mises Institute 1982 Auburn, GMU's Austrian program."),

    q(2, "4",
      f"Murray Rothbard (1926-1995) wrote 'America's Great Depression' (1963), 'Man, Economy, and State' (1962), and other Austrian classics. He attended Mises's NYU seminars. What was Rothbard's distinctive contribution?",
      f"Synthesized Austrian econ with libertarian philosophy {D} the anarcho-capitalist tradition",
      [
          f"Embraced Keynesian deficit spending later {D} abandoning Austrian tradition",
          f"Nationalize banks under central-bank control {D} state-banking position",
          f"Founded modern econometrics {D} methodological contribution",
      ],
      "Rothbard's synthesis (Austrian economics + libertarian political philosophy + revisionist history) defined the late-20th-century Austrian revival."),

    q(2, "4",
      f"Sowell (b. 1930) studied under Milton Friedman at Chicago. His 'Basic Economics' (2000) and 'Knowledge and Decisions' (1980) are among the most-read econ texts. What's distinctive about Sowell?",
      f"Applies Hayek's knowledge problem to policy {D} Austrian method",
      [
          f"Defends central planning as optimal {D} Soviet-style planning",
          f"Argues prices don't convey information {D} denying Hayek",
          f"Treats markets as unfair to participants {D} market critique",
      ],
      "Sowell extends the Austrian tradition into accessible popular writing. *Basic Economics* applies Hayekian reasoning where mainstream economics defaults to intervention."),

    # --- QE + monetary policy mechanics (5) ---
    q(2, "4",
      f"QE is how the Fed creates money to buy Treasury bonds and mortgage securities. It pays by crediting bank reserves {D} essentially typing numbers in a computer. What does QE actually do?",
      f"Expands money supply, lowers long rates via bond bidding {D} monetary expansion",
      [
          f"Sells Treasury gold to fund spending {D} commodity-sale",
          f"Collects financial-firm taxes for redistribution {D} a transfer scheme",
          f"No money-supply effect since reserves stay at Fed {D} 'reserves aren't money' defense",
      ],
      "QE is the modern technical name for 'monetizing the debt' — central-bank money creation to absorb government bond issuance."),

    q(2, "4",
      f"The Fed's balance sheet grew from ~$900B (2008) to over $9T peak (2022) {D} tenfold in 14 years. The previous 95 years (1913-2008) saw slower growth. What does this rate change indicate?",
      f"Regime shift: emergency to standard practice {D} QE became normal",
      [
          f"Return to gold-standard discipline {D} inversion of the actual trend",
          f"Smaller than 1929-1933 contraction {D} wrong-direction comparison",
          f"Coincidence with Fed's 100th anniversary {D} unrelated milestone",
      ],
      "The Fed's balance-sheet trajectory (2008-2022) marks the most dramatic central-bank intervention in modern history. Emergency tools became normal tools."),

    q(2, "4",
      f"In 2008 the Fed began paying interest on excess reserves (IOER) to commercial banks. Critics said this incentivized holding reserves over lending. What did IOER allow the Fed to do?",
      f"Expand QE without immediate inflation by paying banks to hold reserves {D} delayed inflation",
      [
          f"Eliminate inflation by paying banks never to lend {D} no-inflation policy",
          f"Force banks to lend regardless of conditions {D} inversion of the policy",
          f"Tax reserves to fund social programs {D} revenue raising",
      ],
      "IOER (now IORB) is a key mechanic of modern monetary policy. It lets the Fed expand its balance sheet without expanding lending. When that money moves, inflation can follow."),

    q(2, "4",
      f"In 2008 the Fed coordinated with ECB, BoE, BoJ, SNB to lower rates together. By 2020 most major central banks ran similar QE. What is this called?",
      f"Synchronized global monetary policy {D} synchronized debasement",
      [
          f"Competitive devaluation {D} each acting alone",
          f"Return to gold via international agreement {D} commodity backing return",
          f"Privatization of central-bank functions {D} free-market revolution",
      ],
      "Post-2008 global coordination kept inflation low for years: when everyone debases together, no currency falls vs the others. 2021-23 broke this pattern."),

    q(2, "4",
      f"In 2009 the Fed began publishing the FOMC 'dot plot' (each governor's rate forecast). What does the dot plot really show?",
      f"Fed governors disagree on rate path {D} contested expert judgment",
      [
          f"Fed has perfect future foresight {D} predictive certainty",
          f"Fed always agrees internally {D} unanimity claim",
          f"FOMC decisions are external {D} institutional claim",
      ],
      "The Fed's 2021 dot plot projections (low rates through 2023) were grossly wrong by 2023. A cautionary case about the limits of expert forecasting."),

    # --- CBDCs / future (2) ---
    q(2, "4",
      f"After 2008 central banks discussed central bank digital currencies (CBDCs) {D} programmable government-issued digital money. China launched e-CNY (2020); ECB preparing a digital euro. What do CBDCs share with cash that bitcoin doesn't?",
      f"Direct central-bank issuance {D} issuer-level control",
      [
          f"Hard supply cap in code {D} inversion of how CBDCs actually work",
          f"Anonymous transactions {D} opposite of CBDC intent",
          f"Independence from government {D} inversion of how CBDCs are structured",
      ],
      "CBDCs are central-bank money in digital form. They differ from cash in being programmable (potential expiration, spending restrictions) and surveillable."),

    q(2, "4",
      f"In 2021 the Fed published 'Money and Payments' surveying CBDC options. It raised privacy and surveillance questions. What was NOT promised?",
      f"US CBDC preserving cash privacy {D} unguaranteed privacy",
      [
          f"US CBDC offering no privacy {D} no-privacy commitment",
          f"US CBDC replacing bitcoin {D} displacement promise",
          f"Fed not pursuing CBDC {D} digital-currency renunciation",
      ],
      "The 2021 Fed CBDC paper was carefully ambiguous about privacy. Default CBDC architecture includes transaction-level visibility to the central bank."),
]

assert len(P4) == 45, f"P4 count {len(P4)}"


# =========================================================================
# P5 PRACTICAL ECONOMICS (35)
# =========================================================================

P5 = [
    # --- Supply and demand (5) ---
    q(2, "5",
      f"A band announces a stadium concert. Face value $80. Capacity 50,000; demand 500,000. Scalpers resell for $400. What does the resale market reveal?",
      f"The face value was below the market-clearing price {D} demand > supply at $80",
      [
          f"The face value was correctly set; resale price proves irrationality {D} market-failure",
          f"Scalpers create demand by raising prices {D} resale creates the gap",
          f"The concert venue was the wrong size for the demand {D} venue-sizing",
      ],
      "Concert ticket scalping is the textbook case of underpriced face-value tickets meeting reality. 'Fair price' is whatever clears the market. Banning scalping moves rationing to nonprice methods."),

    q(2, "5",
      f"Nike releases a limited-edition sneaker at $200. Sells out in an hour. Resale: $1,500 days later. Why does the resale price differ from retail by 7.5x?",
      f"Retail was below the market-clearing price {D} Nike chose hype-creating scarcity over revenue",
      [
          f"The resale price proves the original $200 was correct {D} market-failure",
          f"The sneaker's resale value is set by Nike marketing directly {D} corporate control",
          f"Resellers can charge any price they want regardless of demand {D} price-setting power",
      ],
      "Sneaker reselling demonstrates price-as-information. Nike's $200 retail creates scarcity, publicity, rewards core customers. Resale discovers the real market-clearing price."),

    q(2, "5",
      f"After Hurricane Katrina (2005), New Orleans generators and water tripled in price. Politicians called it 'price gouging.' Economists defended the rises. Why?",
      f"Higher prices ration scarce supply AND signal entrepreneurs to bring more in {D} prices do double duty",
      [
          f"Higher prices punish storm victims for living in a hurricane zone {D} moral deterrent",
          f"Higher prices have no effect on supply or demand {D} price-mechanism denial",
          f"Higher prices guarantee no shortages will ever occur {D} absolute claim",
      ],
      "Hurricane price-spike economics is one of the cleanest seen-vs-unseen lessons. Seen: higher prices. Unseen: rationing limits hoarding, supply expands quickly."),

    q(2, "5",
      f"In 1973 OPEC cut production and embargoed the US, oil going from $3 to $12/barrel. Nixon imposed price controls on gasoline. What did the controls create?",
      f"Long gas lines, fuel shortages, and odd/even-day rationing {D} non-price rationing",
      [
          f"Cheap gasoline for everyone with no shortages {D} price-control success",
          f"A sudden surplus of gasoline available at stations {D} inversion of what happened",
          f"Immediate restoration of pre-1973 oil prices globally {D} price restoration",
      ],
      "The 1973-74 US gas lines are the canonical case of price-control consequences. Rationing fell to non-price methods (waiting, hoarding)."),

    q(2, "5",
      f"In 1979 the US lifted oil-price controls. Production rose, drivers conserved, gas lines ended. By 1986 oil was at $10/barrel. What does this show?",
      f"Free prices solve the same problems controls create {D} signals work",
      [
          f"Government must always control prices to prevent shortages {D} inversion of the lesson",
          f"Oil markets cannot function without government oversight {D} regulatory dependence",
          f"Free markets always produce shortages and lines {D} market-failure narrative",
      ],
      "The 1979-1986 US oil-market deregulation is the practical demonstration that free prices coordinate supply and demand. By 1986 the world was awash in cheap oil."),

    # --- Marginal analysis + incentives (4) ---
    q(2, "5",
      f"A kid has eaten three cookies; the fourth feels full; fifth excessive. Willingness to pay for more decreases. What concept describes this?",
      f"Diminishing marginal utility {D} each unit gives less satisfaction",
      [
          f"Linear marginal utility {D} each cookie same satisfaction",
          f"Increasing marginal utility {D} each cookie tastes better",
          f"Negative absolute utility {D} always negative satisfaction",
      ],
      "Diminishing marginal utility is foundational in economics. Carl Menger (Austrian founder, 1840-1921) was one of three independent discoverers in 1871."),

    q(2, "5",
      f"A factory produces 100 widgets at $5 profit each. Adding a 101st: marginal cost $4; marginal revenue $6. Should the owner make the 101st widget?",
      f"Yes {D} marginal revenue ($6) exceeds marginal cost ($4), so adds $2 profit",
      [
          f"No {D} average profit per widget is $5 so the new worse-margin widget hurts overall {D} averaged confusion",
          f"Maybe {D} the decision depends on union rules not on cost and revenue {D} a non-economic factor",
          f"No {D} marginal analysis is not a real economic concept and should be ignored {D} a denial",
      ],
      "Marginal analysis is the workhorse of economic decision-making. The owner cares whether ONE MORE unit adds more revenue than cost. Apply at the margin, not the average."),

    q(2, "5",
      f"A college student choosing to study Saturday or play video games faces a real economic question even with no money. What economic concept applies?",
      f"Opportunity cost {D} next-best alternative foregone",
      [
          f"Sunk cost {D} an already-paid cost {D} different concept",
          f"Marginal benefit {D} value of next unit {D} partial overlap",
          f"Public goods {D} jointly-consumed good {D} unrelated concept",
      ],
      "Opportunity cost is among the most important and most undertaught economic concepts. There's no free Saturday."),

    q(2, "5",
      f"A teacher offers a $50 prize to whichever of two students scores higher next week. Both study harder. Why does this work?",
      f"Incentives shape behavior {D} incentives drive behavior",
      [
          f"Cash payments are illegal at most schools and the offer was theoretical {D} legal technicality",
          f"Incentives have no effect on behavior {D} a denial",
          f"Both students would study equally hard with or without the prize {D} inversion",
      ],
      "The economist's first question is always: 'what incentives does this create?' Steven Levitt's *Freakonomics* (2005) made it accessible."),

    # --- Spontaneous order (3) ---
    q(2, "5",
      f"Hayek's insight: complex orders emerge from local interactions with no designer. A store has fresh February tomatoes via thousands acting independently. What's this called?",
      f"Spontaneous order {D} emergent coordination no planner",
      [
          f"Central planning {D} planner-set arrangement",
          f"Random allocation {D} chance distribution",
          f"Market failure {D} coordination breakdown",
      ],
      "Hayek's *Individualism and Economic Order* (1948) introduced spontaneous order. The concept extends beyond economics: language, common law, science emerge without central direction."),

    q(2, "5",
      f"On a Manhattan morning, 8M people make 30M journeys via subway, bus, walking, taxi, bike. No planner directs the flow. What does this illustrate?",
      f"Decentralized decisions coordinate outcomes no planner could match {D} urban-scale spontaneous order",
      [
          f"NY needs more central traffic-direction than any city {D} planning success",
          f"Traffic flow cannot exceed any planner's design without chaos {D} planner dependence",
          f"Traffic only works when each commuter holds an identical map {D} uniform-info claim",
      ],
      "Manhattan's daily transportation is one of the world's most complex spontaneous orders. MTA runs subway, taxis regulated — but routing, mode, timing, destination decisions are independent."),

    q(2, "5",
      f"Leonard Read's 1958 'I, Pencil' tracks a pencil to a store. Wood from Oregon; graphite from Sri Lanka; brass; rubber from Indonesia. Thousands coordinate to make one. What's the lesson?",
      f"No one knows how to make a pencil; pencils get made {D} markets coordinate knowledge",
      [
          f"Pencils are centrally planned globally {D} inversion of the actual story",
          f"Pencils could be made by one craftsman alone {D} denying supply-chain",
          f"Pencil production requires extensive UN coordination {D} centralized claim",
      ],
      "Leonard Read's *I, Pencil* (1958) is one of the most-reprinted economic essays. Milton Friedman cited it on his 1980 *Free to Choose* PBS series."),

    # --- Public choice basics (4) ---
    q(2, "5",
      f"Buchanan and Tullock's 1962 'The Calculus of Consent' said politicians, bureaucrats, voters aren't more public-spirited than those they regulate. What field did they found?",
      f"Public choice theory {D} econ analysis of politics",
      [
          f"Behavioral economics {D} biases in decisions {D} unrelated field",
          f"Welfare economics {D} aggregate utility math {D} different concept",
          f"Game theory {D} strategic analysis {D} partial overlap",
      ],
      "Buchanan won the 1986 Nobel for public choice. The field's central move — extending self-interest analysis to political actors — collapses the 'market failure leads to government fix' framework."),

    q(2, "5",
      f"US sugar producers benefit from sugar quotas {D} billions in revenue. Consumers each pay a few dollars more per year. Who is more politically organized?",
      f"Concentrated producers {D} concentrated vs dispersed politics",
      [
          f"The dispersed many (consumers) {D} consumers have more stake {D} inversion",
          f"Both groups are equally organized politically {D} a denial of asymmetry",
          f"Neither group cares enough to organize politically {D} denies the politics exists",
      ],
      "Sugar quotas (still in force, costing consumers billions annually) are the canonical case of concentrated benefits vs dispersed costs."),

    q(2, "5",
      f"Politicians claim policies 'serve the common good.' Public choice tells us to ask a different question first. What is it?",
      f"Whose specific interests does this policy serve, and at whose expense? {D} no policy benefits all equally",
      [
          f"How effectively does this policy serve every American? {D} uncritical acceptance",
          f"How many votes will this policy win in the next election? {D} purely electoral",
          f"What did Adam Smith say about this policy in 1776? {D} appeal to authority",
      ],
      "Public choice theory's first question: cui bono — who benefits, who pays? The 'common good' framing usually conceals concentrated beneficiaries."),

    q(2, "5",
      f"The ICC (1887) was within a decade captured by the railroads it was meant to oversee, enforcing cartel pricing. What's this called?",
      f"Regulatory capture {D} industries co-opt regulators",
      [
          f"Successful consumer protection {D} agency worked as designed",
          f"Industry rebellion against regulation {D} industry defied rules",
          f"Bureaucratic incompetence {D} agency couldn't do its job",
      ],
      "The ICC (1887, abolished 1995) is the textbook case of regulatory capture. Gabriel Kolko's *Triumph of Conservatism* (1963) documented how Progressive-era regulation was often welcomed by the regulated."),

    # --- Rent control / min wage (3) ---
    q(2, "5",
      f"A city sets strict rent control: existing rents rise 1%/year while neighborhood rents rise 5%. Existing tenants visibly benefit. What unseen costs does Bastiat's method tell us to look for?",
      f"Less building, less maintenance, tenant lock-in {D} unseen spread",
      [
          f"No real costs exist {D} pure landlord-tenant transfer {D} a no-cost claim",
          f"Higher-quality construction follows rent control {D} inversion of the actual effect",
          f"The federal government compensates landlords for losses {D} subsidy defense",
      ],
      "Economists across schools (Friedman, Sowell, Krugman, Stiglitz) have warned strict rent controls reduce housing supply. Textbook seen-vs-unseen."),

    q(2, "5",
      f"A minimum-wage law raises the floor from $10 to $15. Workers who keep jobs at the new wage benefit visibly. What workers does Bastiat's method tell us to look for next?",
      f"Hour-cut, laid-off, or unhirable workers at the higher minimum {D} the priced-out",
      [
          f"Workers who immediately get promotions to manager-level positions {D} inversion",
          f"Federal regulators enforcing the law {D} a tangential effect",
          f"Workers in foreign countries whose wages also rise as a result {D} an irrelevant effect",
      ],
      "Minimum-wage debates often focus only on workers who keep jobs at the higher wage. The 'unseen' workers — priced out, can't get a first job, hours cut — are the harder-to-count loss."),

    q(2, "5",
      f"Some economists (David Card) argue minimum-wage hikes don't reduce employment as predicted. The Austrian / classical response notes one thing about most such studies. What?",
      f"Short-run measurements missing long-run automation substitution {D} dynamics matter",
      [
          f"They're falsified by all available data {D} a denial of observation",
          f"They prove minimum wage has no effect on anything {D} over-strong reading",
          f"Consistent with Keynesian demand theory {D} theoretical alignment",
      ],
      "David Card + Alan Krueger's 1994 New Jersey-Pennsylvania study argued for limited employment effects. Critics note short time horizons, narrow industry focus, missed long-run substitution."),

    # --- Trade + comparative advantage (3) ---
    q(2, "5",
      f"Ricardo's 1817 Portugal-England wine-cloth example: both gain by specializing even when one is more efficient at both. What did Ricardo establish?",
      f"Comparative advantage {D} trade helps both, comparative",
      [
          f"Absolute advantage {D} absolute-only trade {D} different concept",
          f"Mercantilism {D} export max, import min {D} the doctrine Ricardo refuted",
          f"Tariff protection {D} raise barriers to help producers {D} the opposite",
      ],
      "Ricardo's *On the Principles of Political Economy and Taxation* (1817) introduced comparative advantage. Opportunity cost matters, not absolute productivity."),

    q(2, "5",
      f"In 1930 the US passed Smoot-Hawley, raising tariffs on 20,000+ imports. Others retaliated. Global trade collapsed ~65% 1929-1934. What did Smoot-Hawley contribute to?",
      f"Deepening the Great Depression {D} worsened the catastrophe",
      [
          f"Ending the Great Depression {D} tariffs protected industry",
          f"A boom in US manufacturing through the early 1930s {D} tariff-success story",
          f"Stabilizing global trade through enforced bilateral deals {D} alternative history",
      ],
      "Smoot-Hawley (signed June 17, 1930) is the textbook case of tariff-driven trade collapse. Over 1,000 economists signed a public petition urging Hoover to veto."),

    q(2, "5",
      f"Modern trade-protection invokes 'protecting American jobs.' Public choice and comparative advantage together suggest one move. What?",
      f"Identify the specific jobs being protected and the broader costs of protecting them {D} concentrated vs dispersed",
      [
          f"Always raise tariffs to protect all American jobs equally {D} tariff maximization",
          f"Always cut tariffs to zero immediately {D} fixed prescription",
          f"Tariffs and trade have no effect on jobs in either direction {D} denial of any link",
      ],
      "Bastiat's seen-vs-unseen applied to trade: seen is the protected industry; unseen is everyone paying higher prices, exporters facing retaliation."),

    # --- Entrepreneur / innovation (3) ---
    q(2, "5",
      f"Joseph Schumpeter (1883-1950, Austrian) coined 'creative destruction.' Cars beat buggy whips; phones beat film; streaming beat video stores. What's the lesson?",
      f"Economic progress requires obsolete businesses to fail {D} no new without old",
      [
          f"Government must protect obsolete industries from change {D} the opposite of the lesson",
          f"Creative destruction is a recent phenomenon in tech only {D} a scope-limitation",
          f"Economic progress can occur without any business failures {D} denying trade-off",
      ],
      "Schumpeter's *Capitalism, Socialism, and Democracy* (1942) introduced 'creative destruction.' Policies that 'protect jobs' often freeze the obsolete in place."),

    q(2, "5",
      f"Israel Kirzner (an Austrian who studied under Mises) emphasized the entrepreneur's distinctive economic role. What does the entrepreneur do that worker, investor, and manager don't?",
      f"Discovers profit opportunities others have missed {D} alertness to market gaps",
      [
          f"Provides labor in exchange for hourly wages {D} the worker role",
          f"Provides capital in exchange for interest payments {D} the investor role",
          f"Manages existing operations efficiently {D} the manager role",
      ],
      "Kirzner's *Competition and Entrepreneurship* (1973) distinguished entrepreneurial function from labor/capital/management. The entrepreneur spots opportunities."),

    q(2, "5",
      f"Steve Jobs returned to near-bankrupt Apple in 1997. He cut hundreds of products and focused on iMac, iPod, iPhone. Apple became one of the most valuable companies. What did Jobs do?",
      f"Entrepreneurial coordination toward unrecognized opportunities {D} the Kirznerian role",
      [
          f"Standard manager oversight of routine operations {D} the manager function",
          f"Labor as a salaried executive of a public company {D} the worker function",
          f"Passive capital investor providing financing {D} the capitalist function",
      ],
      "Jobs's return to Apple (1997-2011) combined technologies, designs, partnerships, and capital toward products consumers didn't know they wanted."),

    # --- Intertemporal choice + savings (3) ---
    q(2, "5",
      f"A kid saving $5/week for 50 years at 5% returns ~$35,000 {D} most from compounding, not contributions. What does this illustrate?",
      f"The 8th wonder of the world (Einstein) {D} compound interest engine",
      [
          f"Simple interest matches compound returns {D} denying compounding",
          f"Stock returns always beat bonds by exactly 5% {D} unrelated claim",
          f"Bonds lose value over decades {D} inversion of typical outcomes",
      ],
      "Compound interest is the most important math concept in personal finance. Saving early and letting time work is empirically more effective than saving more later."),

    q(2, "5",
      f"Inflation at 3%/year: a dollar buys ~75 cents in 10 years. At 7%/year (post-2020): ~50 cents. What does inflation do to dollar savers?",
      f"Imposes a hidden tax on saved purchasing power {D} inflation transfers savers to issuers",
      [
          f"Rewards savers by automatically increasing nominal dollar amounts {D} inversion of the effect",
          f"Has no effect on purchasing power if wages keep up {D} wage-indexation defense",
          f"Creates new wealth for everyone equally across the economy {D} denying Cantillon",
      ],
      "Inflation is the regressive wealth-transfer Bastiat would spot instantly. Seen: nominal dollar amounts. Unseen: their purchasing power erodes."),

    q(2, "5",
      f"A person can borrow at 6% for a car or save at 5% in a bond. Opportunity cost matters: borrowing pays interest; saving foregoes. What's the economic concept?",
      f"Time preference {D} present-vs-future trade-off",
      [
          f"Marginal cost {D} marginal unit cost {D} unrelated concept",
          f"Public choice {D} econ of politics {D} unrelated concept",
          f"Spontaneous order {D} emergent coordination {D} unrelated concept",
      ],
      "Time preference is foundational to Austrian capital theory (Eugen von Böhm-Bawerk's *Capital and Interest* in three volumes 1884-1909)."),

    # --- More practical (3) ---
    q(2, "5",
      f"A teen sees identical shoes at two stores: $60 vs $80. Same brand, same model, same condition. The teen drives to the cheaper store. What economic concept did the teen use?",
      f"Arbitrage {D} choosing low when the same good has two prices",
      [
          f"Public choice {D} economic analysis of political incentives {D} unrelated",
          f"Aggregate demand {D} total spending on goods and services {D} unrelated",
          f"Marginal product {D} output from one more unit of input {D} unrelated",
      ],
      "Arbitrage drives prices toward consistency across markets. In well-functioning markets, identical goods converge in price; persistent gaps signal frictions (transport, taxes, regulation)."),

    q(2, "5",
      f"A small bakery raises bread prices from $4 to $5. Customers grumble but most keep buying because the alternative bakery is across town. The owner's revenue rises despite some lost sales. What concept describes this?",
      f"Inelastic demand {D} quantity demanded falls only a little when price rises",
      [
          f"Elastic demand {D} quantity falls sharply with any price rise {D} the opposite case",
          f"Zero demand {D} no one buys at any price {D} not applicable here",
          f"Infinite demand {D} unlimited buying regardless of price {D} not applicable here",
      ],
      "Demand elasticity measures responsiveness of quantity to price. Bread is fairly inelastic (necessity); luxury items are more elastic. Inelasticity gives producers more pricing power."),

    q(2, "5",
      f"In 2008 US housing crashed; in March 2020 stocks crashed before rallying. Investors who panicked at the bottom locked in losses; those who held recovered. What concept does this show?",
      f"The danger of selling at the bottom {D} crashes feel permanent but markets historically recover",
      [
          f"Markets always go up forever with no risk {D} too optimistic",
          f"Markets always go down forever with no recovery {D} too pessimistic",
          f"Government always rescues investors in crashes {D} sometimes, not always",
      ],
      "Behavioral finance research (Kahneman, Thaler, Shiller) shows investors systematically buy high and sell low. Long-term wealth-building requires resisting the urge to panic at market bottoms."),

    # --- Meta + sums (4) ---
    q(2, "5",
      f"Across these concepts (prices, opportunity cost, public choice, spontaneous order, comparative advantage), what's the unifying insight?",
      f"Economic systems coordinate dispersed information no individual could possess {D} the Hayekian thread",
      [
          f"Economic systems are best designed by experts using sophisticated math {D} a different framework",
          f"Economic systems are random and cannot be analyzed at all {D} denial of analytical economics",
          f"Economic systems work the same way as physics systems {D} methodology equivalence",
      ],
      "The Hayekian thread — that prices encode dispersed knowledge no individual possesses — connects supply/demand, marginal analysis, time preference, public choice, spontaneous order."),

    q(2, "5",
      f"Bastiat's 1850 'Seen and Not Seen' uses a broken window. Seen: glazier's work. Unseen: everything else the shopkeeper would have bought. What broader method does this teach?",
      f"Always look for second-order effects, trade-offs, costs not in the immediate picture {D} economic thinking",
      [
          f"Always count only the visible effects of a policy {D} opposite of Bastiat",
          f"Always defer to expert opinion on economic policy {D} appeal to authority",
          f"Always support free-trade agreements without analysis {D} fixed prescription",
      ],
      "Bastiat's method (see what's not visible) is the bank's signature voice. It applies to every policy question."),

    q(2, "5",
      f"Free-market economists (Sowell, Hayek, Friedman, Mises) keep returning to one core question on any policy. What is it?",
      f"What do people do when they're free to choose? {D} revealed preferences are data",
      [
          f"What do politicians prefer at the moment? {D} deferral to authority",
          f"What do mathematical models predict aggregate outcomes? {D} model-centric approach",
          f"What does academic consensus say about the policy? {D} an appeal to authority",
      ],
      "Free-market economists trust revealed preferences over stated preferences. Policy respecting revealed preferences tends to outperform."),

    q(2, "5",
      f"Milton Friedman said 'no free lunch.' Heinlein coined it (1966); Friedman made it economics. What's the lesson?",
      f"Every benefit has a cost {D} someone pays even if hidden",
      [
          f"Government can produce benefits at zero cost when properly organized {D} inversion of the lesson",
          f"Lunches at restaurants are free under certain promotional conditions {D} literal reading",
          f"Some benefits in economics are genuinely costless to all parties involved {D} a denial",
      ],
      "'No free lunch' applies to subsidies (taxpayers pay), tariffs (consumers pay), regulations (compliance), printing money (savers pay through inflation)."),
]

assert len(P5) == 35, f"P5 count {len(P5)}"


# =========================================================================
# Combine + validate
# =========================================================================

ALL = P3 + P4 + P5
assert len(ALL) == 120, f"total count {len(ALL)}"


def main() -> None:
    bank_path = REPO / "data" / "questions" / "economics.json"
    raw = json.loads(bank_path.read_text(encoding="utf-8"))
    bank = raw.get("questions", raw) if isinstance(raw, dict) else raw
    print(f"Loaded bank: {len(bank)} questions")

    dup_idx, ans_idx = build_bank_indices(bank)

    valid_questions = []
    failures: list[tuple[int, str, list]] = []
    soft_warns_log: list[tuple[int, str, list]] = []

    for i, q_dict in enumerate(ALL):
        pillar = q_dict.get("pillar", "?")
        q_clean = {k: v for k, v in q_dict.items() if k != "pillar"}

        result = validate_rewrite(
            "economics", q_clean,
            bank=bank,
            dup_index=dup_idx,
            answer_index=ans_idx,
            replace_idx=None,
        )

        if result["verdict"] == "FAIL":
            failures.append((i, pillar, result["hard_fails"]))
            print(f"  [{i:3d}] P{pillar} FAIL: {result['hard_fails']}")
            print(f"       stem: {q_dict['question'][:80]!r}")
        elif result["verdict"] == "SOFT_WARN":
            soft_warns_log.append((i, pillar, result["soft_warns"]))
            valid_questions.append(q_dict)
        else:
            valid_questions.append(q_dict)

    print(f"\nValidation: {len(valid_questions)} passed, {len(failures)} failed, {len(soft_warns_log)} soft-warnings")

    from collections import Counter
    by_pillar = Counter(q["pillar"] for q in valid_questions)
    print(f"By pillar: {dict(by_pillar)}")

    output_questions = []
    for q in valid_questions:
        out = {k: v for k, v in q.items() if k != "pillar"}
        output_questions.append(out)

    output = {
        "tier": 2,
        "summary": {
            "questions_generated": len(output_questions),
            "by_pillar": {str(k): v for k, v in sorted(by_pillar.items())},
            "soft_warnings": len(soft_warns_log),
            "failures": len(failures),
        },
        "questions": output_questions,
    }

    out_path = REPO / "_gen_economics_t2_p345.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {out_path}")

    if failures:
        print("\n--- FAILURE DETAILS (first 30) ---")
        for idx, pillar, fails in failures[:30]:
            print(f"  [{idx}] P{pillar}: {fails}")
    if soft_warns_log:
        print(f"\n--- SOFT WARN COUNT: {len(soft_warns_log)} ---")
        for idx, pillar, warns in soft_warns_log[:10]:
            print(f"  [{idx}] P{pillar}: {warns}")


if __name__ == "__main__":
    main()
