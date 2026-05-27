"""Build _weasel_fix_economics.json — pointed-concrete closers per §15.

For each of the 53 economics questions in _weasel_economics.json, rewrite ONLY
the final question (the closer) so it asks about something SPECIFIC in the
substance. Light answer + choice adjustments allowed for parity. Run
validate_rewrite("economics", ...) against the live bank for every item.

Output: _weasel_fix_economics.json — list of {bank_idx, new: {full q obj}}.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402

WEASEL_PATH = REPO / "_weasel_economics.json"
BANK_PATH = REPO / "data" / "questions" / "economics.json"
OUT_PATH = REPO / "_weasel_fix_economics.json"


# ---------------------------------------------------------------------------
# Hand-written rewrites. Keyed by bank_idx. Each entry is the FULL new question
# object (tier preserved, stem rewritten with concrete pointed closer, answer
# and choices lightly adjusted as needed for parity; context updated only when
# the rewrite changes the recognition skill — usually unchanged).
# ---------------------------------------------------------------------------

REWRITES: dict[int, dict] = {

    # ------------------------------ T1 ------------------------------

    51: {  # Two kids trade lunches — peanut butter for ham
        "tier": 1,
        "question": "Two kids trade lunches — peanut butter for ham. Each thinks they came out ahead. Who, exactly, came out better off?",
        "answer": "Both — free trade makes each side happier",
        "choices": [
            "Both — free trade makes each side happier",
            "Only one — trade is a contest, one wins",
            "Neither — the lunches are equal in value",
            "Nobody — trading is bad without adult OK",
        ],
        "context": "Mutual gain from voluntary exchange is one of economics' great discoveries. Mises called it the basis of human cooperation. No coercion is needed.",
    },

    76: {  # Bitcoin 21M cap
        "tier": 1,
        "question": "Bitcoin's 21-million cap cannot change without consent of the whole network. Who has the authority to raise that limit?",
        "answer": "No one — the whole network must agree",
        "choices": [
            "No one — the whole network must agree",
            "The Fed — it sets US monetary policy",
            "Congress — it can vote on supply",
            "Satoshi — the inventor kept admin keys",
        ],
        "context": "The 21M cap is Bitcoin's answer to fiat debasement. No central authority can dilute the supply. The contrast with the dollar's 2020-2021 expansion is what attracted institutional buyers.",
    },

    124: {  # 1922 gold dollar vs paper dollar
        "tier": 1,
        "question": "An attic find: a 1922 gold dollar. Today it buys a steak dinner. A 1922 paper dollar buys a stick of gum. Which property of gold explains the gap?",
        "answer": "Gold cannot be printed — paper can",
        "choices": [
            "Gold cannot be printed — paper can",
            "Steaks got cheaper — faster than gum did",
            "Old paper rots faster — than old coins do",
            "Gum got bigger — over 100 years",
        ],
        "context": "The simplest lesson of sound money: when a thing cannot be created at will, it holds its value. When it can, it doesn't.",
    },

    146: {  # Zimbabwe 100T note as $20 souvenir
        "tier": 1,
        "question": "Zimbabwe's 2008 hundred-trillion note now sells as a $20 souvenir. What does that tell you about the printed bill itself?",
        "answer": "Printed money — worth less than the paper",
        "choices": [
            "Printed money — worth less than the paper",
            "Big numbers — always impress on a bill",
            "Souvenirs cost — exactly twenty dollars each",
            "Zimbabwe printed — only one of this note",
        ],
        "context": "The 100-trillion-dollar Zimbabwe note is one of the most famous artifacts of modern hyperinflation. Today it trades online for $15-30 as a collectible — far more than it was ever worth as currency.",
    },

    192: {  # 2008 Fed promise vs 2023 collapses
        "tier": 1,
        "question": "After 2008, the Fed promised no more crises. In 2023 US banks collapsed anyway. What does shielding bankers from losses do to risk-taking?",
        "answer": "Grows it — bailouts breed bigger crises",
        "choices": [
            "Grows it — bailouts breed bigger crises",
            "Shrinks it — bankers learn from mistakes",
            "Stops it — risk hits odd-numbered years",
            "Ends it — the Fed wins over time",
        ],
        "context": "Moral hazard: when actors are protected from the consequences of their bets, they take bigger bets. The 2023 collapses of Silicon Valley Bank, Signature Bank, and First Republic followed the same pattern of subsidized risk-taking that produced 2008.",
    },

    203: {  # Ben raises lemonade
        "tier": 1,
        "question": "Ben raises lemonade from 50 cents to $1. Sales halve. What happened to his total revenue?",
        "answer": "Same — half the sales at twice the price",
        "choices": [
            "Same — half the sales at twice the price",
            "Doubled — high prices pull more buyers",
            "Quadrupled — price signals a luxury good",
            "Zero — sales stop at any price hike",
        ],
        "context": "The law of demand: higher prices reduce quantity demanded. But the new price-quantity combination may produce equal or greater revenue, depending on elasticity. Sellers experiment with prices to find the right point.",
    },

    1368: {  # Rule of 72
        "tier": 1,
        "question": "Rule of 72: years to double = 72 / yearly return. A 1% account doubles in 72 years. At 3% inflation, what happens to your real wealth?",
        "answer": "Shrinks — inflation beats the 1% yield",
        "choices": [
            "Shrinks — inflation beats the 1% yield",
            "Doubles — savings always beat inflation",
            "Stays flat — banks match price changes",
            "Grows — Rule of 72 doubles real wealth",
        ],
        "context": "At 6% you double in 12 years; at 12% in 6 years; at 1% in 72 — longer than most working lives. Inflation eats real value while you wait.",
    },

    # ------------------------------ T2 ------------------------------

    371: {  # Weimar twice-a-day pay
        "tier": 2,
        "question": "At Weimar inflation's peak (autumn 1923), workers were paid TWICE A DAY to buy food before prices doubled. Wives met them at gates. Which function of money broke down FIRST?",
        "answer": "Store of value — wages held overnight lost half their purchasing power",
        "choices": [
            "Store of value — wages held overnight lost half their purchasing power",
            "Medium of exchange — Germans refused all paper notes from Jan 1923",
            "Unit of account — German shops switched fully to barter pricing first",
            "Legal tender — the mark stopped being accepted before prices moved",
        ],
        "context": "When prices double in a day, money must be spent immediately. Workers became 'rent-seekers in reverse' — racing the printing press. Savings, contracts, pensions were destroyed.",
    },

    381: {  # Zimbabwe RTGS dollar, gold-backed dollar
        "tier": 2,
        "question": "Zimbabwe launched 'RTGS dollar' 2019, then gold-backed dollar 2024. The new currency has already lost value. What does this repeat tell us about a government that previously printed itself into collapse?",
        "answer": "It will do the same again — institutional incentives outlast any single reform",
        "choices": [
            "It will do the same again — institutional incentives outlast any single reform",
            "It has learned from past mistakes — the second currency has been stable",
            "It always succeeds the second time — fresh starts solve hyperinflation",
            "It is blocked from currency issuance — the IMF stops repeat offenders",
        ],
        "context": "Zimbabwe's pattern (hyperinflation → dollarization → relaunch → reinflation) shows institutional incentives, not lessons-learned, drive currency outcomes.",
    },

    384: {  # Yugoslavia super dinar
        "tier": 2,
        "question": "Yugoslavia's hyperinflation ended Jan 1994 with a 'super dinar' pegged to the German mark. Inflation went from 313M% to near zero overnight. Which specific change ended the inflation that fast?",
        "answer": "The printing press stopped — the monetary cause was removed at the source",
        "choices": [
            "The printing press stopped — the monetary cause was removed at the source",
            "Twenty-four months elapsed — hyperinflations always self-correct on schedule",
            "The mark peg failed — pegging to a foreign currency is inherently unstable",
            "Citizens stopped spending — the freeze came from a behavioral cool-down",
        ],
        "context": "The 1994 'super dinar' stabilization is among the clearest natural experiments in monetary economics. Same country, same people — printing press stopped, inflation collapsed in days.",
    },

    410: {  # Volcker
        "tier": 2,
        "question": "During Volcker's tight-money campaign (1979-82), unemployment topped 10%, farmers protested, bankruptcies spiked. Volcker faced threats but stayed the course. What did breaking the inflation cost in the short run?",
        "answer": "A deep recession — and political risk to the chairman personally",
        "choices": [
            "A deep recession — and political risk to the chairman personally",
            "Nothing measurable — anti-inflation policy is a pure free lunch",
            "Only foreign reserves — domestic employment was untouched",
            "Long-run growth — anti-inflation policy permanently lowers GDP",
        ],
        "context": "Volcker's experience is the counterfactual to every subsequent Fed chair who lacked the spine to break inflation early.",
    },

    412: {  # TARP
        "tier": 2,
        "question": "In Oct 2008 Congress passed TARP, authorizing $700B for 'troubled assets.' Treasury Secretary Paulson told Congress: pass or face collapse. Which Rahm Emanuel phrase captured the political dynamic?",
        "answer": "Never let a crisis go to waste — crisis manufactures consent",
        "choices": [
            "Never let a crisis go to waste — crisis manufactures consent",
            "Bipartisanship is dead — TARP had unanimous support",
            "Small is beautiful — TARP was the smallest postwar bailout",
            "Slow government wins — Congress debated TARP for over a year",
        ],
        "context": "TARP passed October 2008 with limited debate. Rahm Emanuel's 'never let a crisis go to waste' captured the dynamic. The pattern repeated in 2020 with $4-5T in pandemic spending.",
    },

    447: {  # 1979 oil decontrol
        "tier": 2,
        "question": "In 1979 the US lifted oil-price controls. Production rose, drivers conserved, gas lines ended. By 1986 oil was at $10/barrel. Which fell to about $10/barrel by 1986 — the price under controls or the price after decontrol?",
        "answer": "After decontrol — free prices coordinated supply and demand into a glut",
        "choices": [
            "After decontrol — free prices coordinated supply and demand into a glut",
            "Under controls — price ceilings produced the lowest oil prices ever",
            "Neither — oil markets cannot function without government oversight",
            "Both equally — free markets and controls converge to identical prices",
        ],
        "context": "The 1979-1986 US oil-market deregulation is the practical demonstration that free prices coordinate supply and demand. By 1986 the world was awash in cheap oil.",
    },

    453: {  # Manhattan 30M journeys
        "tier": 2,
        "question": "On a Manhattan morning, 8M people make 30M journeys via subway, bus, walking, taxi, bike. No planner directs the flow. Which Hayek term names a coordinated outcome that emerges without a designer?",
        "answer": "Spontaneous order — complex coordination without central direction",
        "choices": [
            "Spontaneous order — complex coordination without central direction",
            "Centralized planning — Manhattan needs more traffic direction, not less",
            "Designed equilibrium — flow only works under a planner's blueprint",
            "Shared map — each commuter must hold an identical mental routing chart",
        ],
        "context": "Manhattan's daily transportation is one of the world's most complex spontaneous orders. MTA runs subway, taxis regulated — but routing, mode, timing, destination decisions are independent.",
    },

    454: {  # I, Pencil
        "tier": 2,
        "question": "Leonard Read's 1958 'I, Pencil' tracks a pencil to a store. Wood from Oregon; graphite from Sri Lanka; brass; rubber from Indonesia. Whose 1980 PBS series put the essay on national TV?",
        "answer": "Milton Friedman's — 'Free to Choose' featured the pencil",
        "choices": [
            "Milton Friedman's — 'Free to Choose' featured the pencil",
            "John Kenneth Galbraith's — 'The Age of Uncertainty'",
            "Paul Samuelson's — his MIT econ lectures were televised",
            "Robert Reich's — Clinton-era PBS labor specials",
        ],
        "context": "Leonard Read's *I, Pencil* (1958) is one of the most-reprinted economic essays. Milton Friedman cited it on his 1980 *Free to Choose* PBS series.",
    },

    465: {  # Schumpeter creative destruction
        "tier": 2,
        "question": "Joseph Schumpeter (1883-1950, Austrian) coined 'creative destruction.' Cars beat buggy whips; phones beat film; streaming beat video stores. What must happen to obsolete businesses for new ones to take their place?",
        "answer": "They must be allowed to fail — no new without the old going down",
        "choices": [
            "They must be allowed to fail — no new without the old going down",
            "They must be protected by government — subsidize the obsolete to keep jobs",
            "They must merge with new entrants — never close, only consolidate",
            "They must persist unchanged — progress requires no business failures at all",
        ],
        "context": "Schumpeter's *Capitalism, Socialism, and Democracy* (1942) introduced 'creative destruction.' Policies that 'protect jobs' often freeze the obsolete in place.",
    },

    468: {  # Compound interest
        "tier": 2,
        "question": "A kid saving $5/week for 50 years at 5% returns ~$35,000 — most from compounding, not contributions. Which 20th-century scientist supposedly called compound interest the 'eighth wonder of the world'?",
        "answer": "Albert Einstein — the line is widely attributed to him",
        "choices": [
            "Albert Einstein — the line is widely attributed to him",
            "Isaac Newton — though he lost a fortune in the South Sea Bubble",
            "Stephen Hawking — known for his lectures on long-horizon physics",
            "Carl Sagan — his 'billions and billions' was about cosmic compounding",
        ],
        "context": "Compound interest is the most important math concept in personal finance. Saving early and letting time work is empirically more effective than saving more later. The 'eighth wonder' line is popularly attributed to Einstein; its origin is uncertain.",
    },

    477: {  # No free lunch
        "tier": 2,
        "question": "Milton Friedman said 'no free lunch.' Heinlein coined it (1966); Friedman made it economics. Even when a benefit looks free to one party — subsidies, tariffs, money printing — who is actually paying?",
        "answer": "Someone else — taxpayers, consumers, or savers absorb the hidden cost",
        "choices": [
            "Someone else — taxpayers, consumers, or savers absorb the hidden cost",
            "Nobody at all — well-organized government produces benefits at zero cost",
            "Only restaurants — literal free lunches happen under sales promotions",
            "Future generations only — the present always gets the benefit for free",
        ],
        "context": "'No free lunch' applies to subsidies (taxpayers pay), tariffs (consumers pay), regulations (compliance), printing money (savers pay through inflation).",
    },

    # ------------------------------ T3 ------------------------------

    615: {  # Weimar + Hitler beer hall putsch
        "tier": 3,
        "question": "Weimar hyperinflation peaked October-November 1923. On November 8-9, 1923 — while the inflation raged — Hitler attempted to overthrow the Bavarian government, was arrested, served nine months, and used the trial to launch a political career. Which group's destroyed savings provided his political base in the years that followed?",
        "answer": "The middle class — pensioners and savers wiped out by money-printing",
        "choices": [
            "The middle class — pensioners and savers wiped out by money-printing",
            "Bavarian aristocrats — landed wealth was uniquely vulnerable to inflation",
            "Munich industrialists — factory owners lost their export markets first",
            "Foreign creditors — French and British bondholders pivoted to Hitler",
        ],
        "context": "The link between monetary chaos and political extremism is one of the most-discussed lessons of Weimar. Destroyed savings were political tinder the 1929 Depression then re-ignited.",
    },

    621: {  # Zimbabwe spontaneous dollarization 2009
        "tier": 3,
        "question": "By April 2009 Zimbabweans had simply stopped using the Zimbabwe dollar. Without any formal government decision, ordinary people began transacting in US dollars, rand, and pula. Shops re-priced in dollars; salaries paid in dollars. Did the dollarization come from a government decree or from spontaneous citizen choice?",
        "answer": "Spontaneous citizen choice — currency is enforced by trust, not by law",
        "choices": [
            "Spontaneous citizen choice — currency is enforced by trust, not by law",
            "Government decree — Zimbabwe formally adopted the US dollar in March 2009",
            "Gold-backed scrip — Zimbabwe issued gold-backed bonds to end the crisis",
            "Foreign intervention — South African troops imposed the rand by force",
        ],
        "context": "Spontaneous dollarization is a recurring pattern. Argentines did it. Venezuelans did it. Lebanese have done it since 2020. People prefer working money to a unit of account that loses value daily.",
    },

    628: {  # Lebanon banking 2019 haircuts
        "tier": 3,
        "question": "When Lebanon's banking system froze late 2019, depositors discovered they could not withdraw their own dollars. Banks imposed informal capital controls — 'haircuts' — meaning withdrawing $1,000 might give you $100 or less. Legally, was that $1,000 your property or the bank's?",
        "answer": "The bank's — a deposit is a loan to the bank, not stored cash",
        "choices": [
            "The bank's — a deposit is a loan to the bank, not stored cash",
            "Yours alone — Lebanese banks were uniquely corrupt and broke the law",
            "Jointly held — Lebanese depositors all got full balances back by 2021",
            "Foreign creditors' — the haircut reflected outside speculation, not deposits",
        ],
        "context": "The Lebanese collapse is one reason 'not your keys, not your coins' is a Bitcoin slogan. A claim on a bank is a claim on the bank's ability to honor it.",
    },

    636: {  # 1924 gold vs $20
        "tier": 3,
        "question": "A worker in 1924 who saved 1 oz of gold vs a worker who saved $20 (equivalent at the prewar gold price). A century later in 2024: the gold oz is worth ~$2,400; the $20 has the purchasing power of ~$0.70. Roughly how many times more purchasing power did the gold saver preserve compared to the dollar saver?",
        "answer": "About 3,400 times more — sound money preserves; fiat dilutes",
        "choices": [
            "About 3,400 times more — sound money preserves; fiat dilutes",
            "About the same — neither cash nor gold are valid savings vehicles",
            "Less, not more — gold prices today are inflated by pure speculation",
            "Equal again — dollars earn interest that exactly offsets gold's gains",
        ],
        "context": "The gold-vs-dollar comparison is one of the cleanest demonstrations of what sound money means. Simple long-term storage in a non-debasable asset preserves wealth. ($2,400 / $0.70 ≈ 3,400x.)",
    },

    645: {  # Anna Schwartz
        "tier": 3,
        "question": "Anna Schwartz was Milton Friedman's collaborator on *A Monetary History* (1963). She worked at the NBER from 1941 until her death in 2012 — 71 years at the same institution. What did Schwartz contribute that Friedman built his theory on top of?",
        "answer": "The archival monetary data — she assembled the historical record itself",
        "choices": [
            "The archival monetary data — she assembled the historical record itself",
            "Nothing technical — Friedman invited her as a publicity stunt",
            "A shared Nobel in 1976 — they were both awarded the prize jointly",
            "Media presence — she was monetarism's public face while Friedman wrote",
        ],
        "context": "Anna Schwartz is one of the unsung figures of 20th-century economics. The data Friedman analyzed was largely her work to assemble. She continued working into her 90s, publishing through 2010.",
    },

    659: {  # 2021-23 real wages
        "tier": 3,
        "question": "From 2021 to 2023, US real wages — wages adjusted for inflation — fell. Nominal wages rose, but consumer prices rose faster. By the time inflation peaked at 9.1% in June 2022, the median worker had lost real purchasing power. Who LOSES in this episode — and who GAINS?",
        "answer": "Wage-earners lose — debtors and asset-holders gain through inflation transfer",
        "choices": [
            "Wage-earners lose — debtors and asset-holders gain through inflation transfer",
            "Wage-earners gain — nominal wages always rise faster than consumer prices",
            "Everyone is unaffected — inflation has no distributional effects across households",
            "Only creditors lose — wage-earners and asset-holders are equally untouched",
        ],
        "context": "Real wages falling during inflation is the canonical demonstration of why wage-earners are particular victims of monetary expansion. The 'inflation as wage transfer' framing comes alive in episodes like 2021-23.",
    },

    672: {  # Keynesian multiplier 2009 stimulus
        "tier": 3,
        "question": "Keynesian macro promised a 'fiscal multiplier' — a dollar of government spending would produce more than a dollar of GDP through chain effects. The Obama administration projected the 2009 stimulus would keep unemployment under 8%. By October 2009 unemployment hit 10%. By how many percentage points did actual unemployment overshoot the projection?",
        "answer": "About 2 points — the real-world multiplier was well below the projection",
        "choices": [
            "About 2 points — the real-world multiplier was well below the projection",
            "Zero points — the 2009 stimulus produced exactly the predicted GDP gains",
            "Negative two points — the multiplier exceeded projection by a wide margin",
            "Unknown — no unemployment data has been collected since the stimulus",
        ],
        "context": "The 2009 stimulus is one of the largest natural experiments on Keynesian multiplier estimates ever run. Promised employment gains did not materialize. Christina Romer later acknowledged projections were too optimistic.",
    },

    680: {  # Fed dual mandate
        "tier": 3,
        "question": "The Federal Reserve has a 'dual mandate' established by Humphrey-Hawkins (1978) — to promote both 'maximum employment' and 'stable prices.' Critics argue the two goals can conflict, giving the Fed political cover for whatever policy it wanted. When inflation is high, which of the two goals does the Fed typically cite to justify keeping rates loose?",
        "answer": "Employment — discretion lets the Fed appeal to whichever goal suits",
        "choices": [
            "Employment — discretion lets the Fed appeal to whichever goal suits",
            "Stable prices — the Fed has perfectly satisfied both goals since 1978",
            "Neither — the dual mandate was invented after 2008 under Bernanke alone",
            "A Soviet directive — Humphrey-Hawkins was a covert Cold War operation",
        ],
        "context": "The dual-mandate framing is one reason the Fed faces little accountability for either goal. When inflation is high, the Fed cites employment. When unemployment is high, it cites prices. The discretion is the feature.",
    },

    698: {  # I, Pencil + Hayek
        "tier": 3,
        "question": "Leonard Read's 1958 essay 'I, Pencil' illustrates a deeper Hayekian point. No central planner coordinates the cedar growers, the graphite miners, the zinc refiners, the rubber tappers, the truckers, the factory workers. Yet the pencil emerges. Which Hayek concept names this kind of complex coordination without a designer?",
        "answer": "Spontaneous order — emerges from voluntary exchange, no central direction",
        "choices": [
            "Spontaneous order — emerges from voluntary exchange, no central direction",
            "Central planning — every step is directed by government bureaucracies",
            "Mercantilism — pencils help the country accumulate gold for trade victory",
            "Labor theory of value — pencil prices reflect labor inputs at each step",
        ],
        "context": "Spontaneous order is Hayek's central insight applied beyond markets. The pencil is the canonical teaching case. No one designed the global pencil-production system; it emerged.",
    },

    699: {  # Hayek + language spontaneous order
        "tier": 3,
        "question": "Hayek argued spontaneous order applies beyond markets. Language is a paradigm case — English emerged over centuries through the voluntary choices of millions of speakers, without any central authority designing grammar or vocabulary. Apart from markets and language, which TWO other institutions does Hayek's framework apply to?",
        "answer": "Common law and science — both evolve without a central designer",
        "choices": [
            "Common law and science — both evolve without a central designer",
            "Parliaments and academies — every functioning institution requires central design",
            "Only language — markets are unique; other institutions need central planning",
            "Nothing besides language — spontaneous order applies to linguistics only",
        ],
        "context": "Hayek's spontaneous-order framework is one of the great social-science insights. Markets, language, common law, scientific progress — all are examples of complex order without central design.",
    },

    704: {  # FDA regulatory capture PDUFA
        "tier": 3,
        "question": "The US FDA has been studied as a case of regulatory capture by the pharmaceutical industry. Officials move between FDA roles and pharma jobs. Industry funds a substantial portion of FDA's review budget through user fees (PDUFA, since 1992). What does PDUFA — the user-fee structure — do to FDA's independence from the firms it regulates?",
        "answer": "Weakens it — funder and regulator become structurally co-dependent",
        "choices": [
            "Weakens it — funder and regulator become structurally co-dependent",
            "Strengthens it — funding has no relationship to FDA decisions at all",
            "Eliminates it — FDA was created by pharma in 1962 with no public role",
            "Perfects it — user fees ensure full independence from industry influence",
        ],
        "context": "The FDA case is one of the most-studied examples of regulatory capture in action. The pattern — user fees, revolving door, mutual dependence — is repeated across SEC, FAA, FCC, and many others.",
    },

    706: {  # Paulson Geithner Powell Yellen
        "tier": 3,
        "question": "Henry Paulson (Goldman CEO → Treasury Secretary → private investor). Tim Geithner (NY Fed President → Treasury Secretary → private equity). Jay Powell (private equity → Fed Chair). Janet Yellen (Fed Chair → private speaking fees → Treasury Secretary). What is the public-choice name for this career pattern between regulator and regulated?",
        "answer": "The revolving door — public/private lines blur over a career arc",
        "choices": [
            "The revolving door — public/private lines blur over a career arc",
            "The civic ladder — officials always serve the public from any post",
            "Criminal conspiracy — every example requires criminal prosecution",
            "Career anomaly — these examples are unique exceptions to the rule",
        ],
        "context": "The revolving door is a public-choice phenomenon: regulators expect future industry jobs, so they regulate gently. Industries hire ex-regulators for relationships and inside knowledge.",
    },

    711: {  # Hayek prices encode information
        "tier": 3,
        "question": "Hayek's central insight: prices encode dispersed, tacit, local information no central planner can collect. When wheat prices rise, every farmer, baker, restaurant, and consumer adjusts — without anyone knowing why. What is the title of Hayek's 1945 paper that argued the price system solves a coordination problem no planner could solve?",
        "answer": "'The Use of Knowledge in Society' — fourteen pages, published in the AER",
        "choices": [
            "'The Use of Knowledge in Society' — fourteen pages, published in the AER",
            "'The Road to Serfdom' — Hayek's 1944 polemic against central planning",
            "'The Constitution of Liberty' — 1960 book on the legal order of freedom",
            "'Prices and Production' — 1931 work on the Austrian business-cycle theory",
        ],
        "context": "Hayek's price-signal insight is the deepest in 20th-century economics. The 'use of knowledge in society' (1945) makes the case in 14 pages. Central planning fails not because planners aren't smart — because the information they'd need is not centralizable.",
    },

    1391: {  # Mt. Gox 2014
        "tier": 3,
        "question": "On February 7, 2014, Mt. Gox — then handling 70% of Bitcoin transactions — froze withdrawals and filed bankruptcy two weeks later. About 850,000 BTC went missing. Customers who held coins on the exchange lost everything; customers who self-custodied lost nothing. What is the four-word Bitcoin slogan this episode famously taught?",
        "answer": "Not your keys, not your coins — exchanges reintroduce trust Bitcoin removed",
        "choices": [
            "Not your keys, not your coins — exchanges reintroduce trust Bitcoin removed",
            "Bitcoin is broken by design — the protocol inherits exchange risk natively",
            "Fiat is safer than crypto — Mt. Gox proved cash systems are more secure",
            "Exchanges only for serious investors — self-custody is too risky for most",
        ],
        "context": "Mt. Gox CEO Mark Karpelès was later convicted of data manipulation. The 2014 collapse foreshadowed FTX 2022 — different decade, same custodial-risk lesson. Bitcoin's self-custody design (private keys) makes exchange-bypass possible.",
    },

    # ------------------------------ T4 ------------------------------

    721: {  # Mises 1920
        "tier": 4,
        "question": "In 1920 Mises published 'Economic Calculation in the Socialist Commonwealth.' His argument: without private ownership of capital goods, no market for them exists; without that market, no money prices form; without prices, planners cannot compare alternative production methods. Mises claimed socialism is not merely inefficient — what is the stronger claim he made about it?",
        "answer": "Impossible — rational economic calculation cannot occur without price information",
        "choices": [
            "Impossible — rational economic calculation cannot occur without price information",
            "Workable with surveys — planners can substitute engineering estimates for prices",
            "More efficient than markets — coordinated production beats the waste of competition",
            "Identical to markets — Mises's 1920 paper showed both systems converge",
        ],
        "context": "The calculation debate ran for decades. Oskar Lange in the 1930s claimed planners could 'simulate' a market by trial and error. Hayek answered with the knowledge problem (1945). The 20th century settled the debate empirically.",
    },

    898: {  # Powell transitory November 2021
        "tier": 4,
        "question": "Fed Chair Powell told Congress on November 30, 2021 that 'it's probably a good time to retire' the word 'transitory' regarding inflation. By that point CPI was at 6.8% and rising. The Fed had been calling inflation transitory through most of 2021. Roughly how long had the Fed underestimated the persistence of inflation by the time Powell retired the word?",
        "answer": "About a year — credibility weakened and rule-based debate reopened",
        "choices": [
            "About a year — credibility weakened and rule-based debate reopened",
            "Zero — the Fed had perfectly predicted inflation through all of 2021",
            "Two months — a brief data-falsification episode at Treasury caused the lag",
            "Not applicable — the Fed had no legal authority over inflation in 2021",
        ],
        "context": "Major Fed forecast errors in 2021 reopened John Taylor's argument for rule-based policy. The Fed had built credibility under Volcker by being slow but reliable; the 2021 'transitory' episode undermined that within a year.",
    },

    919: {  # FDR Executive Order 6102
        "tier": 4,
        "question": "Executive Order 6102, signed by FDR on April 5, 1933, ordered Americans to surrender their gold to the Federal Reserve at $20.67 per ounce. After the surrender, Roosevelt revalued gold to $35 per ounce — a 41% devaluation of the dollar. Hoarding gold became a federal crime. What does this episode reveal about whether a politically-controlled gold standard counts as 'sound money'?",
        "answer": "It doesn't — political authority can devalue any nominally-backed currency on demand",
        "choices": [
            "It doesn't — political authority can devalue any nominally-backed currency on demand",
            "The 1933 confiscation ended democratically — institutional flexibility worked properly",
            "The order was reversed in five years — a temporary emergency measure, no precedent",
            "The Supreme Court overturned it 1935 — restoring private gold ownership entirely",
        ],
        "context": "The 1933 confiscation was nominally lifted in 1974, but the precedent stands: a government with the power to compel can override gold-backed money. This is the lesson Hayek and modern Bitcoin proponents emphasize.",
    },

    933: {  # Languages not designed
        "tier": 4,
        "question": "Human languages — Mandarin, Spanish, English, Yoruba, Hindi — were not designed by anyone. They evolved through millions of speech acts over thousands of years. Grammars are formalizations after the fact. Attempts to design 'rational' artificial languages (Esperanto, Volapük) have produced small communities but no major usage. Which sentence about top-down design vs bottom-up evolution does the historical record support?",
        "answer": "Bottom-up evolution from many decisions tends to produce more usable systems than top-down designs from a few experts widely",
        "choices": [
            "Bottom-up evolution from many decisions tends to produce more usable systems than top-down designs from a few experts widely",
            "Top-down design always produces more efficient outcomes than evolution since experts coordinate decisions across participants",
            "Natural and constructed languages are equally usable since linguistic communication is purely arbitrary convention regardless of source",
            "Esperanto became the world's most-spoken language between 1887 and 1939 demonstrating the success of rational design over evolution",
        ],
        "context": "Hayek extended his market argument: spontaneous order applies to law, language, money, and morals. Friedrich Carl von Savigny in 19th-century legal theory argued similar points. The lesson: humility about what we can centrally design.",
    },

    934: {  # Internet TCP/IP IETF
        "tier": 4,
        "question": "The Internet's underlying protocols (TCP/IP, HTTP, DNS, SMTP) were developed by working groups — the Internet Engineering Task Force (IETF) — operating by 'rough consensus and running code.' No central authority designed the Internet; no government created its standards. Yet billions of devices interoperate. What is the IETF's slogan that captured how its standards actually get adopted?",
        "answer": "'Rough consensus and running code' — voluntary standards from working users",
        "choices": [
            "'Rough consensus and running code' — voluntary standards from working users",
            "'Government certified, vendor approved' — regulation drives every protocol",
            "'DARPA approved, NSF funded' — federal contracts dictated the standards",
            "'Top-down by central authority' — a single body designed every Internet rule",
        ],
        "context": "While DARPA funded early ARPANET research, the actual protocol design and ongoing maintenance has been overwhelmingly voluntary and decentralized. The Internet is a vast natural experiment in Hayekian spontaneous order at technological scale.",
    },

    946: {  # US sugar quotas
        "tier": 4,
        "question": "US sugar quotas restrict imported sugar to maintain domestic prices at roughly 2x the world price. USDA estimates the quota costs American consumers approximately $3-4 billion annually in higher prices. About 4,500 sugar farmers benefit. Confectionery makers (Hershey, Mars) lose business and have moved some production to Mexico. Which 1965 work — by which author — explains why 4,500 organized producers beat 330 million unorganized consumers in policy fights?",
        "answer": "Mancur Olson's *The Logic of Collective Action* — concentrated benefits, diffuse costs",
        "choices": [
            "Mancur Olson's *The Logic of Collective Action* — concentrated benefits, diffuse costs",
            "John Kenneth Galbraith's *The New Industrial State* — large firms produce equal outcomes",
            "Paul Samuelson's *Economics* — sugar quotas benefit all American workers equally",
            "Milton Friedman's *Capitalism and Freedom* — measured offsets equalize the policy",
        ],
        "context": "The sugar quota is the textbook public choice example. About 4,500 producers organize to influence policy effectively; 330 million consumers each pay an extra $10/year on sugar products and can't coordinate opposition. Olson 1965 in action.",
    },

    951: {  # Uber + NYC medallions
        "tier": 4,
        "question": "Uber launched in 2009 in San Francisco. Within a decade ride-sharing had largely replaced traditional taxis in most American cities. NYC's medallion taxi system, where a medallion cost over $1 million in 2013, collapsed in value with thousands of medallion holders bankrupted. What did the $1M medallion price actually represent — a scarce commodity, or something else?",
        "answer": "A government-created scarcity rent — destroyed once technology bypassed the rule",
        "choices": [
            "A government-created scarcity rent — destroyed once technology bypassed the rule",
            "Uber operated illegally — courts shut it down across major US cities",
            "Medallions stayed worth $1M — value has held into 2024 unchanged",
            "Taxi industry adapted — service and pricing have not changed since 2009",
        ],
        "context": "Medallion holders paid for a government-created monopoly position. When technology made the regulation unenforceable, the rent disappeared. The 'unseen' cost of decades of consumer pain became visible only when ride-sharing offered the comparison.",
    },

    954: {  # Stigler + Bootleggers and Baptists
        "tier": 4,
        "question": "George Stigler observed that established firms in regulated industries often LOBBY FOR additional regulation. Regulations are expensive to comply with. Established firms can absorb the cost; new entrants cannot. Regulation becomes a barrier to entry protecting incumbents from competition. What is Bruce Yandle's 1983 phrase for the moral-campaigner + self-interested-incumbent coalition that often produces this regulation together?",
        "answer": "Bootleggers and Baptists — the moralists provide cover, the incumbents collect rent",
        "choices": [
            "Bootleggers and Baptists — the moralists provide cover, the incumbents collect rent",
            "Producers always oppose regulation — compliance costs reduce profits uniformly",
            "Regulators stay neutral — incumbent firms have no influence on policy",
            "Capture is impossible in large markets — only small industries see lobbying",
        ],
        "context": "Bruce Yandle's 'Bootleggers and Baptists' (1983) developed this analysis: moral campaigners (Baptists) and self-interested incumbents (bootleggers) often coalition for the same regulation. Prohibition produced both winners.",
    },

    1211: {  # Arthur Andersen
        "tier": 4,
        "question": "Arthur Andersen was one of the Big 5 accounting firms. Andersen audited Enron and was found guilty of obstruction in June 2002 for shredding Enron documents. The Supreme Court overturned the conviction in 2005, but the firm had collapsed. How much did Andersen earn from Enron auditing vs consulting, and what conflict did that create?",
        "answer": "$25M audit + $27M consulting — the consulting fee destroyed audit skepticism",
        "choices": [
            "$25M audit + $27M consulting — the consulting fee destroyed audit skepticism",
            "Audit-only — Andersen did no consulting work for Enron at any point",
            "Big 5 consolidation — Andersen ended for unrelated industry reasons",
            "Still active — Arthur Andersen audits major US public companies today",
        ],
        "context": "Sarbanes-Oxley 2002 created the PCAOB (Public Company Accounting Oversight Board). The Big 5 became Big 4. The structural conflict — auditors paid by the firms they audit — remains.",
    },

    1218: {  # WeWork Community-Adjusted EBITDA
        "tier": 4,
        "question": "WeWork's August 2019 S-1 introduced 'Community Adjusted EBITDA' — earnings before interest, taxes, depreciation, amortization, AND G&A, marketing, design, development, and pre-opening costs. The IPO was withdrawn; the firm went bankrupt 2023. What did each successive 'adjustment' on top of EBITDA strip out of the metric?",
        "answer": "A real business cost — each letter hides another expense from the number",
        "choices": [
            "A real business cost — each letter hides another expense from the number",
            "A GAAP requirement — Community-Adjusted EBITDA is mandated for co-working firms",
            "A VC fund standard — SoftBank invented it as a portfolio measure adopted widely",
            "A model for real estate — the industry copied it after WeWork's 2019 success",
        ],
        "context": "Charlie Munger said: 'I never look at EBITDA because I want to know about real earnings.' The IPO valuation collapsed from $47B (private) to ~$8B (target) to zero. Bankruptcy 2023.",
    },

    1264: {  # Buffett Rule
        "tier": 4,
        "question": "In 2011 Warren Buffett wrote a NYT op-ed: his effective federal tax rate (17.4%) was lower than his secretary's. Why? Most of his income was long-term capital gains and qualified dividends, taxed at 15% (max 20% now). Her income was wages, taxed at marginal 25-28%. Obama proposed the 'Buffett Rule' (min 30% on incomes >$1M); it never passed Congress. What does the tax code structurally prefer — capital income or wage income?",
        "answer": "Capital income — taxed at lower rates than labor; the preference is durable politically",
        "choices": [
            "Capital income — taxed at lower rates than labor; the preference is durable politically",
            "Wage income — Buffett's situation was a clerical error the IRS later fixed",
            "Both equally — TCJA 2017 made all wage and capital-gains rates identical",
            "Wage income — Buffett's effective rate was actually higher than his secretary's",
        ],
        "context": "Long-term capital gains have been preferentially taxed since 1921 (with brief equalizations 1986-1993). Arguments for: offsets inflation tax of unrealized gains, incentivizes long-term capital. Arguments against: regressive, distorts labor-vs-investment. Bastiat: who lobbies, who pays.",
    },

    1268: {  # TCJA 2017 charitable
        "tier": 4,
        "question": "TCJA 2017 doubled the standard deduction (single $6,350 to $12,000; married $12,700 to $24,000) AND capped SALT at $10,000. Itemizers dropped from ~30% to ~10% of filers. The share of US households claiming a charitable deduction fell from 25% to 9%. Charitable giving as a share of GDP fell measurably. From 25% to about what share of households claiming charitable deductions, after TCJA?",
        "answer": "Down to about 9% — when the itemizing incentive vanished, the giving fell",
        "choices": [
            "Down to about 9% — when the itemizing incentive vanished, the giving fell",
            "Up to about 40% — Americans became more generous after the 2017 reform",
            "Unchanged at 25% — donations are driven by faith and social motives only",
            "Down to about 22% — the drop was within statistical noise, no real effect",
        ],
        "context": "Studies after TCJA (Indiana Lilly Family School of Philanthropy 2019; Tax Policy Center 2020) documented the drop. Whether TCJA was good or bad, tax-incentive-driven donations vanished when the incentive vanished. Incentives matter, even for 'altruism.'",
    },

    1352: {  # Hurricane Andrew
        "tier": 4,
        "question": "On August 24, 1992, Hurricane Andrew hit South Florida with Category 5 winds, causing $27B in damage. Eleven US property insurers went insolvent. State Farm and Allstate sharply cut Florida policies. The Florida Hurricane Catastrophe Fund formed in 1993; state-owned Citizens Property Insurance launched 2002. When private insurers withdrew, who stepped in to fill the gap?",
        "answer": "State-run pools — the Hurricane Cat Fund and Citizens Property Insurance",
        "choices": [
            "State-run pools — the Hurricane Cat Fund and Citizens Property Insurance",
            "Federal flood insurance — Washington covers every hurricane loss anywhere",
            "Private insurers returned — Florida underwriting resumed within six months",
            "No one — no private insurer has offered Florida coverage since 1992",
        ],
        "context": "Andrew was the wake-up call for catastrophic-risk modeling. Pre-Andrew insurers underpriced hurricane risk in Florida. Post-Andrew, reinsurers (Lloyd's, Swiss Re, Munich Re) restructured pricing. The withdrawal-state intervention cycle recurs every major storm.",
    },

    1397: {  # Graham Mr Market
        "tier": 4,
        "question": "In Benjamin Graham's 1949 'The Intelligent Investor,' Chapter 8 introduces Mr. Market — a manic-depressive business partner who shows up daily quoting wildly different prices for the same business. Some days he's euphoric and quotes high; some days he's despondent and quotes low. Buffett, Graham's most famous student, calls Mr. Market his most important investing concept. How should an investor USE Mr. Market's mood swings, according to Graham?",
        "answer": "Exploit the gap — buy below intrinsic value when he panics; ignore his mood otherwise",
        "choices": [
            "Exploit the gap — buy below intrinsic value when he panics; ignore his mood otherwise",
            "Follow his quotes strictly — Mr. Market is always right by the day's end",
            "Trust the daily price — it reflects underlying business value perfectly",
            "Use technical signals — sell on euphoria, buy on despair, by chart pattern",
        ],
        "context": "Graham's distinction: a stock's price (what Mr. Market quotes) and a business's value (what the cash flows are worth) drift apart constantly. The investor exploits the gap. Buffett's 1987 Berkshire letter expanded on Mr. Market; he calls Graham's chapter 8 the most important investment writing ever.",
    },

    1403: {  # FTX collapse SBF
        "tier": 4,
        "question": "FTX collapsed November 8, 2022. Founder Sam Bankman-Fried had moved roughly $8 billion in customer crypto deposits to his trading firm Alameda Research. He had cultivated an image as the face of 'effective altruism,' donating to political campaigns (mostly Democratic) and pledging future billions to charity. He was convicted of seven counts of fraud in November 2023 and sentenced to 25 years in March 2024. How many years was Sam Bankman-Fried sentenced to — and on how many counts was he convicted?",
        "answer": "25 years — seven counts of fraud, sentenced March 2024",
        "choices": [
            "25 years — seven counts of fraud, sentenced March 2024",
            "5 years probation — three minor counts, no prison time imposed",
            "Life sentence — twenty counts, sentenced January 2023 immediately",
            "Acquitted entirely — the jury found no fraud and FTX collapsed by accident",
        ],
        "context": "SBF was a major political donor (~$40M in 2022 cycle, mostly Democratic) and EA spokesman. His parents both taught at Stanford Law. FTX's collapse exposed the gap between performed virtue and actual practice. Bitcoin's design (no central custodian) makes FTX-style collapses architecturally impossible at the protocol level.",
    },

    # ------------------------------ T5 ------------------------------

    1052: {  # Nigeria Bitcoin Feb 2023
        "tier": 5,
        "question": "In February 2023 the Nigerian government's restrictions on cash withdrawals during a currency redesign — combined with the Naira's continued devaluation — generated widespread Bitcoin adoption among Nigerians. Despite formal restrictions on cryptocurrency, peer-to-peer Bitcoin transactions surged. Which two specific Bitcoin properties were Nigerians using — censorship-resistance, programmability, anonymity, or inflation-resistance?",
        "answer": "Censorship-resistance and inflation-resistance — peer-to-peer markets no authority could close, plus protection against Naira devaluation",
        "choices": [
            "Censorship-resistance and inflation-resistance — peer-to-peer markets no authority could close, plus protection against Naira devaluation",
            "Pure speculation on price — Nigerians were betting on price movements, with no real transactions occurring at scale during the redesign episode",
            "None — the Nigerian central bank successfully suppressed Bitcoin, with exchange restrictions channeling citizens back to the Naira",
            "Anonymity for crime — the surge reflected illegal activity rather than economic refuge, primarily evading Nigerian law enforcement",
        ],
        "context": "Nigeria 2023 is an instructive case. The Buhari government's currency restrictions caused widespread cash shortages and political unrest. Citizens turned to Bitcoin despite formal restrictions. Peer-to-peer markets thrived. The episode illustrates Bitcoin's role as monetary refuge in unstable currency regimes.",
    },

    1164: {  # NYC rent control
        "tier": 5,
        "question": "New York City has had rent control or rent stabilization since 1943, originally as a wartime measure. The Rent Control Law of 1947 made it permanent. By 2024 ~half of NYC apartments are rent-stabilized. Studies (Glaeser, Diamond) find the policy reduces tenant mobility, lowers maintenance, distorts allocation, and reduces new construction. Which Swedish socialist economist said rent control is the most efficient way to destroy a city — except for bombing?",
        "answer": "Assar Lindbeck — the seen benefit (current tenants pay less) concentrates; unseen costs (future renters, supply, maintenance) spread",
        "choices": [
            "Assar Lindbeck — the seen benefit (current tenants pay less) concentrates; unseen costs (future renters, supply, maintenance) spread",
            "Paul Krugman — rent control benefits all New Yorkers equally, and every NY economist across schools supports it as good policy",
            "Joseph Stiglitz — NYC repealed rent control in 1970 and has operated under purely free-market housing ever since across all boroughs",
            "Thomas Piketty — rent control INCREASES housing supply, and NYC has the highest per-capita construction rate among major US cities",
        ],
        "context": "Assar Lindbeck (Swedish socialist economist) once said 'in many cases rent control appears to be the most efficient technique presently known to destroy a city, except for bombing.' The literature is one of the strongest cross-school consensuses in applied economics.",
    },

    1168: {  # Card-Krueger vs Neumark-Wascher
        "tier": 5,
        "question": "David Card and Alan Krueger's 1994 AER paper studied NJ's 1992 minimum wage rise ($4.25 to $5.05) versus neighboring PA. Their phone-survey method found no employment decline at fast-food restaurants. Neumark-Wascher 2000 used payroll records and found significant declines in the same data. Which data source — phone surveys or payroll records — confirmed the textbook prediction?",
        "answer": "Payroll records — Neumark and Wascher's higher-quality data found significant employment declines, the textbook prediction holds",
        "choices": [
            "Payroll records — Neumark and Wascher's higher-quality data found significant employment declines, the textbook prediction holds",
            "Phone surveys — Card-Krueger settled it for good, with all later studies confirming no employment effects from minimum-wage rises",
            "Both gave identical results — the two studies used the same data and methodology, producing uncontroversial findings ever since 1994",
            "Neither — Card-Krueger was retracted by the American Economic Review and is no longer cited in any minimum-wage academic discussion",
        ],
        "context": "Card later won the 2021 Nobel partly for the natural-experiment methodology. Neumark and Wascher's payroll-record critique is the canonical methodological rebuttal. The popular framing 'Card-Krueger settled it' is misleading; the underlying economics question remains active.",
    },

    1195: {  # CIA Samuelson overstated Soviet GDP
        "tier": 5,
        "question": "Through the Cold War, the CIA and major US economics textbooks (Samuelson's Economics) substantially overstated Soviet GDP. Samuelson's 1989 edition still predicted Soviet GDP would equal US GDP by the 2010s. The actual Soviet collapse in 1991 revealed an economy far smaller and more dysfunctional than mainstream economists had reported. Which 1920 Mises argument predicted exactly this measurement failure?",
        "answer": "The Calculation Problem — without market prices, no objective measure of aggregate output exists; CIA had to invent prices that didn't exist",
        "choices": [
            "The Calculation Problem — without market prices, no objective measure of aggregate output exists; CIA had to invent prices that didn't exist",
            "None — Samuelson's predictions were correct and Soviet GDP did equal US GDP by the 2010s, with the 1991 collapse a media exaggeration",
            "Mises was wrong — CIA estimates were accurate and the 1991 collapse was purely political, refuting the 1920 calculation argument fully",
            "Reverse — Soviet GDP was actually LARGER than US GDP, with American economists understating Soviet output throughout the Cold War",
        ],
        "context": "The mainstream profession's failure to recognize Soviet economic dysfunction is one of the great prediction failures in 20th-century economics. Soviet-era jokes ('They pretend to pay us, we pretend to work') captured the reality formal statistics couldn't. Mises had said in 1920 the measurement problem was structural.",
    },

    1276: {  # Marquette National Bank 1978
        "tier": 5,
        "question": "Until the late 1970s, most US states had usury laws capping consumer loans around 18%. In 1978 the Supreme Court ruled in Marquette National Bank v. First of Omaha that an issuer could 'export' its HOME state's rate, letting banks relocate freely. Within a decade, US card rates rose from ~12% to 18-22%+. Which two states aggressively dropped usury caps to attract bank charters?",
        "answer": "South Dakota and Delaware — both removed caps to attract banks, producing the modern 22-29% APR landscape by political choice not market evolution",
        "choices": [
            "South Dakota and Delaware — both removed caps to attract banks, producing the modern 22-29% APR landscape by political choice not market evolution",
            "California and Texas — free-market competition produced higher card rates because consumers chose to pay more for charging convenience at stores",
            "None — Marquette was reversed by the Truth in Lending Act of 1968, fully restoring state usury caps that remain in effect today across all 50 states",
            "All fifty states equally — card APRs are set directly by the Federal Reserve in monthly meetings, with no connection to state usury law or Marquette",
        ],
        "context": "Marquette is foundational in modern US consumer-credit history. South Dakota then Delaware moved aggressively to attract bank charters by removing usury caps. The resulting industry (22-29% APRs, minimum-payment math optimized for revenue) emerged from one Supreme Court ruling plus state-level rate competition.",
    },

    1278: {  # Property tax wealth tax
        "tier": 5,
        "question": "American homeowners pay property tax annually on assessed value. NJ averages ~2.2%; Texas similar. On a $400K home that's $8,800/year; over 30 years with reassessments, over $300K. A homeowner who 'owns outright' pays the state more, total, than they paid for the house. If you stop paying, the state takes the property. Who holds the senior claim — you or the state?",
        "answer": "The state — property tax is a perpetual wealth tax; the state is the silent senior landlord, and ownership is conditional on payment",
        "choices": [
            "The state — property tax is a perpetual wealth tax; the state is the silent senior landlord, and ownership is conditional on payment",
            "Neither — property tax is voluntary; homeowners can opt out by registering the home as a private trust under federal homestead protections",
            "The homeowner alone — property tax is a fair user fee for local services like schools and roads, with no wealth-tax character at all",
            "Nobody — property tax was eliminated after California's Proposition 13 in 1978, and only a few coastal states still levy it on residential property",
        ],
        "context": "Property tax has a particular Bastiat character: visible (most people know they pay it) yet psychologically invisible (assessed via bills, escrow, mortgage statements). State authority over the property is permanent and conditional on payment; the 'ownership' label is partly misleading.",
    },

}


def main() -> int:
    weasel = json.loads(WEASEL_PATH.read_text(encoding="utf-8"))
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    print(f"Loaded weasel input: {len(weasel)} items")
    print(f"Loaded bank: {len(bank)} questions")
    print()

    dup, ans = build_bank_indices(bank)

    # Sanity: every weasel item should have a rewrite
    missing = [w["bank_idx"] for w in weasel if w["bank_idx"] not in REWRITES]
    if missing:
        print(f"ERROR: {len(missing)} weasel items missing rewrites:")
        for bi in missing[:10]:
            print(f"  bank_idx={bi}")
        return 1
    print(f"All {len(weasel)} items have rewrites; running validation...")
    print()

    patches: list[dict] = []
    pass_count = 0
    soft_count = 0
    fail_records: list[dict] = []
    fail_by_gate: Counter = Counter()

    for w in weasel:
        bi = w["bank_idx"]
        new_q = REWRITES[bi]
        r = validate_rewrite(
            "economics", new_q,
            bank=bank, dup_index=dup, answer_index=ans,
            replace_idx=bi,
        )
        if r["verdict"] == "FAIL":
            for g, reason in r["hard_fails"]:
                fail_by_gate[g] += 1
            fail_records.append({
                "bank_idx": bi,
                "tier": new_q.get("tier"),
                "stem": new_q.get("question", "")[:80],
                "hard_fails": r["hard_fails"][:5],
                "soft_warns": r["soft_warns"][:3],
            })
        elif r["verdict"] == "SOFT_WARN":
            soft_count += 1
            patches.append({"bank_idx": bi, "new": new_q})
        else:
            pass_count += 1
            patches.append({"bank_idx": bi, "new": new_q})

    print(f"PASS:      {pass_count}")
    print(f"SOFT_WARN: {soft_count}")
    print(f"FAIL:      {len(fail_records)}")
    if fail_by_gate:
        print("Fails by gate:")
        for gate, count in sorted(fail_by_gate.items(), key=lambda kv: -kv[1]):
            print(f"  {gate}: {count}")
    print()

    if fail_records:
        print("=== FAIL DETAIL ===")
        for f in fail_records:
            print(f"  bank_idx={f['bank_idx']} T{f['tier']}: {f['stem']}")
            for g, reason in f["hard_fails"]:
                print(f"     [{g}] {reason}")
            print()

    OUT_PATH.write_text(json.dumps(patches, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}: {len(patches)} patches")
    return 0 if len(fail_records) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
