"""Generate 120 fresh T1 economics questions: 40 P3 + 40 P4 + 40 P5.

Bastiat Pattern + story-in-stem from day 1. Each question self-validated
through `validate_rewrite("economics", ...)`. Rejects are listed for
inspection; passes (including SOFT_WARN) are saved to _gen_economics_t1_p345.json.

Cap: T1 ≤ 280 (hard cap 294 = 280 * 1.05). Budget is question + 4 choices only.
Distractor parity 1.30, answer outlier 1.6×, em-dash uniformity required.
"""
from __future__ import annotations

import json
from pathlib import Path

import sys
REPO = Path(__file__).resolve().parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite


# =============================================================================
# P3 — Sound Money / Hyperinflation (40)
# =============================================================================

P3_QUESTIONS: list[dict] = [
    # --- gold coin still buys food (5)
    {
        "tier": 1,
        "question": "A gold coin from 1900 still buys a nice suit today, about $1,500 worth. A 1900 dollar bill buys 3 cents now. What changed?",
        "answer": "The dollar's supply grew — gold's didn't",
        "choices": [
            "The dollar's supply grew — gold's didn't",
            "Suits got cheaper — when sewn by machine",
            "Gold gets shinier — the older it gets",
            "Old dollars expired — by federal law",
        ],
        "context": "A 1900 $20 gold piece holds value; a 1900 paper $20 has lost roughly 97% of its purchasing power. Sound money — money whose supply cannot be expanded — preserves wealth over time.",
    },
    {
        "tier": 1,
        "question": "Grandpa's 1925 silver dollar today buys a week of groceries. A 1925 paper dollar buys a candy bar. Why?",
        "answer": "Silver stays scarce — paper does not",
        "choices": [
            "Silver stays scarce — paper does not",
            "Silver dollars are magic — protected by mint",
            "Candy bars got cheaper — over 100 years",
            "Groceries got better — due to refrigeration",
        ],
        "context": "Pre-1965 US coins contained 90% silver. After 1965 the US Mint replaced silver with copper-nickel because silver's market value exceeded the coin's face value — Gresham's law in action.",
    },
    {
        "tier": 1,
        "question": "A 1913 $20 gold piece today buys about $2,000 of food. A 1913 paper $20 buys $1 of food. The Fed opened in 1913. Coincidence?",
        "answer": "No — the Fed was made to expand the dollar supply",
        "choices": [
            "No — the Fed was made to expand the dollar supply",
            "Yes — gold just got luckier in markets",
            "No — paper money is heavier than gold",
            "Yes — food got tastier in 100 years",
        ],
        "context": "The dollar has lost roughly 97% of its purchasing power since 1913, the year the Federal Reserve was created. Gold's purchasing power has held roughly steady across the same span.",
    },
    {
        "tier": 1,
        "question": "Roman soldiers in 100 AD got silver denarii. By 250 AD their coins were mostly copper. What happened?",
        "answer": "Emperors mixed in cheap metal — to pay more soldiers",
        "choices": [
            "Emperors mixed in cheap metal — to pay more soldiers",
            "Silver mines all closed — by accident in 200 AD",
            "Soldiers asked for copper — for being lighter",
            "Coins got smaller — over 150 years of wear",
        ],
        "context": "Roman currency debasement: the denarius went from ~95% silver under Augustus to under 5% by the late 3rd century. The empire's inflation crisis paralleled its political crisis.",
    },
    {
        "tier": 1,
        "question": "An attic find: a 1922 gold dollar. Today it buys a steak dinner. A 1922 paper dollar buys a stick of gum. What's the lesson?",
        "answer": "Gold cannot be printed — paper can",
        "choices": [
            "Gold cannot be printed — paper can",
            "Steaks are now cheaper — than gum was",
            "Old paper rots faster — than old coins do",
            "Gum got bigger — over 100 years",
        ],
        "context": "The simplest lesson of sound money: when a thing cannot be created at will, it holds its value. When it can, it doesn't.",
    },

    # --- dollar lost 97% since 1913 (5)
    {
        "tier": 1,
        "question": "In 1913 a US dollar bought what about 3 cents buys today. The Fed opened the same year. What did the Fed do to the dollar?",
        "answer": "Slowly expanded the supply — so each one bought less",
        "choices": [
            "Slowly expanded the supply — so each one bought less",
            "Locked it to gold — to keep it strong",
            "Made it shrink in size — over many decades",
            "Replaced it with pesos — in the 1970s",
        ],
        "context": "The dollar has lost roughly 97% of its purchasing power since the Fed was created in 1913. The institution founded to prevent panics has presided over the largest monetary debasement in US history.",
    },
    {
        "tier": 1,
        "question": "A nickel candy bar in 1913 costs about $1.75 today. The candy bar didn't change much. What did?",
        "answer": "The dollar — its supply has grown 30× since 1913",
        "choices": [
            "The dollar — its supply has grown 30× since 1913",
            "Chocolate — it now contains rare ingredients",
            "Sugar — it became more popular over time",
            "Wrappers — they got more expensive to print",
        ],
        "context": "A 1913 nickel had the purchasing power of about $1.75 today. The candy bar's real cost in labor and materials is roughly unchanged; the dollar lost roughly 97% of its value.",
    },
    {
        "tier": 1,
        "question": "Grandma says a movie ticket cost a dime in 1920. Today a ticket costs $15. The movie got 150× more expensive? Or...",
        "answer": "The dollar got 150× weaker — over 100 years",
        "choices": [
            "The dollar got 150× weaker — over 100 years",
            "Movies got 150× longer — than in the 1920s",
            "Theaters got 150× fancier — than old ones",
            "Popcorn got 150× tastier — over 100 years",
        ],
        "context": "Movie tickets in 1920 averaged about 10-15 cents. The dollar's purchasing power has dropped by roughly 95-97% over the past century. Real prices for many goods are flat in gold or silver.",
    },
    {
        "tier": 1,
        "question": "A house in 1950 cost about $8,000. The same house today costs about $400,000. Houses got 50× nicer? Or what?",
        "answer": "The dollar got weaker — so it takes more of them",
        "choices": [
            "The dollar got weaker — so it takes more of them",
            "Houses got 50× bigger — on average since 1950",
            "Wood got 50× rarer — over the past 75 years",
            "Builders got 50× slower — at building homes",
        ],
        "context": "The median US home price in 1950 was about $7,400; today it's around $400,000. Most of that gap is dollar debasement, not actual house improvement. Home prices in gold are nearly flat.",
    },
    {
        "tier": 1,
        "question": "Your great-grandpa earned $2 a day in 1920. Today $2 buys a coffee. He wasn't poor — he just earned what?",
        "answer": "A strong dollar — that bought a lot back then",
        "choices": [
            "A strong dollar — that bought a lot back then",
            "Two coffees a day — for working hard",
            "A coupon for goods — paid in scrip",
            "Half a movie ticket — for daily work",
        ],
        "context": "A 1920 dollar bought about what $15-20 buys today. A $2/day wage was solid working-class pay. The decline isn't that wages are low — it's that the dollar shrank.",
    },

    # --- what fiat means (5)
    {
        "tier": 1,
        "question": "A dollar isn't backed by gold or silver anymore. It's money because the government says so. What is this kind of money called?",
        "answer": "Fiat money — money by government decree",
        "choices": [
            "Fiat money — money by government decree",
            "Hard money — backed by real metal",
            "Commodity money — backed by goods",
            "Barter money — used in trades",
        ],
        "context": "Fiat comes from the Latin 'let it be done.' Fiat money has no commodity backing — it has value only because a government declares it legal tender. Every fiat currency in history has eventually lost most of its purchasing power.",
    },
    {
        "tier": 1,
        "question": "The word 'fiat' is Latin for 'let it be.' How does fiat money get its value?",
        "answer": "Government declares it money — and people accept it",
        "choices": [
            "Government declares it money — and people accept it",
            "It's backed by gold — locked in Fort Knox",
            "Each bill is signed — by a treasury worker",
            "It's worth a barrel of oil — at all times",
        ],
        "context": "Fiat money has value by decree, not by underlying asset. The US dollar was fully fiat after August 15, 1971, when Nixon closed the gold window.",
    },
    {
        "tier": 1,
        "question": "On August 15, 1971, the US dollar stopped being convertible to gold. After that day, the dollar was what kind of money?",
        "answer": "Fiat — valuable only because the government says so",
        "choices": [
            "Fiat — valuable only because the government says so",
            "Gold-backed — but with a hidden vault",
            "Barter — traded only for goods",
            "Commodity — backed by US oil reserves",
        ],
        "context": "Nixon's August 15, 1971 announcement ended the dollar's last formal link to gold. Since then, the US dollar has been pure fiat. Every other major currency followed.",
    },
    {
        "tier": 1,
        "question": "A dollar bill is just paper. So why does it buy a sandwich? Because the government did what?",
        "answer": "Made it legal tender — so it must be accepted for debts",
        "choices": [
            "Made it legal tender — so it must be accepted for debts",
            "Soaked the paper — in vanilla scent",
            "Printed it on linen — to make it last",
            "Made each bill — track real gold",
        ],
        "context": "Legal tender laws require creditors to accept the currency for debts. This 'forced acceptance' is what gives fiat money its baseline demand, beyond the trust that others will accept it tomorrow.",
    },
    {
        "tier": 1,
        "question": "Fiat money has no gold backing. Its value comes from one thing only. What?",
        "answer": "Trust — that others will accept it tomorrow",
        "choices": [
            "Trust — that others will accept it tomorrow",
            "A secret silver vault — under the Treasury",
            "Bonds locked away — at the Federal Reserve",
            "Each bill backed — by one ounce of cotton",
        ],
        "context": "Fiat currency's only backing is shared expectation. When trust breaks — Weimar, Zimbabwe, Venezuela — the currency dies very quickly. This is why every fiat eventually fails.",
    },

    # --- why gold lasted 2600 years (5)
    {
        "tier": 1,
        "question": "Lydians made gold coins around 600 BC. People still trade gold today, 2,600 years later. Why has gold lasted so long as money?",
        "answer": "It can't be printed — and doesn't rust or rot",
        "choices": [
            "It can't be printed — and doesn't rust or rot",
            "It's easy to chew — for travelers",
            "Kings demanded it — for taxes only",
            "It's the heaviest metal — in nature",
        ],
        "context": "Gold's properties — durable, divisible, portable (per ounce), uniform, recognizable, and scarce — make it natural money. The Lydian kingdom (~600 BC) struck the first gold coins. Gold has been money for ~2,600 years.",
    },
    {
        "tier": 1,
        "question": "Iron rusts. Salt dissolves. Cattle die. But a gold coin from 500 BC still looks new today. What makes gold good money?",
        "answer": "It lasts forever — no decay, no rust",
        "choices": [
            "It lasts forever — no decay, no rust",
            "It's hollow inside — so it's light",
            "It only comes — from one country",
            "Kings cast spells — to protect it",
        ],
        "context": "Durability is one of gold's key 'moneyness' properties. Carl Menger (1871) listed the qualities money must have: durable, divisible, portable, uniform, recognizable, scarce. Gold has all six.",
    },
    {
        "tier": 1,
        "question": "You can cut a gold bar in half. Both halves are still pure gold. Try that with a cow. Why does this matter for money?",
        "answer": "Money must divide cleanly — so trades stay fair",
        "choices": [
            "Money must divide cleanly — so trades stay fair",
            "Cows must be cut — at every market",
            "Bars are heavier — than coins on scales",
            "Gold is sticky — and easy to weigh",
        ],
        "context": "Divisibility is one of Menger's six 'moneyness' properties. A cow can't be divided into change; gold can be melted, struck, or shaved to any size. This is why livestock-money systems lose out to metal-money systems wherever both compete.",
    },
    {
        "tier": 1,
        "question": "A merchant in 1200 AD could weigh a gold coin and know its value. Sacks of grain might be moldy underneath. Why is gold easier money?",
        "answer": "Uniform and recognizable — at a glance",
        "choices": [
            "Uniform and recognizable — at a glance",
            "Sacks are heavier — than coins in baskets",
            "Grain spoils in winter — gold does not",
            "Coins ring louder — when dropped on tables",
        ],
        "context": "Recognizability and uniformity are two more of Menger's six 'moneyness' properties. Gold's universal sameness — one ounce is one ounce, anywhere — makes it ideal for trade across strangers.",
    },
    {
        "tier": 1,
        "question": "Egypt, Rome, China, India, and the New World all picked gold as money — alone. They didn't talk. Why?",
        "answer": "Gold's properties make it money — anywhere",
        "choices": [
            "Gold's properties make it money — anywhere",
            "All five civilizations — shared one king",
            "Gold smelled the same — to all of them",
            "Each region mined gold — in the same year",
        ],
        "context": "Independent civilizations across the world converged on gold (and silver) as money for the same reasons: durability, divisibility, portability, uniformity, recognizability, scarcity. The 'moneyness' properties are objective.",
    },

    # --- Weimar wheelbarrow (5)
    {
        "tier": 1,
        "question": "1923 Weimar Germany: a loaf cost 200 BILLION marks. People shopped with wheelbarrows of cash. Why?",
        "answer": "Printing marks — faster than goods were made",
        "choices": [
            "Printing marks — faster than goods were made",
            "Banning bakers — from baking any kind of bread",
            "Closing all banks — every weekday in Germany",
            "Storing bread — in distant secret warehouses",
        ],
        "context": "Weimar Germany's 1921-1923 hyperinflation peaked at an estimated 29,500% monthly inflation in October 1923. The government printed marks to pay WWI reparations and domestic bills. The currency died; the political fallout helped enable what came next.",
    },
    {
        "tier": 1,
        "question": "1923 Berlin: people burned 1,000-mark notes in stoves because firewood cost more than the cash. What does that say about the mark?",
        "answer": "It was worth less than paper — as a fuel",
        "choices": [
            "It was worth less than paper — as a fuel",
            "Marks were extra flammable — by design",
            "Wood was banned — to save the forests",
            "Stoves were heated — only on Sundays",
        ],
        "context": "The famous Weimar image: marks burned for warmth because banknotes cost less than firewood. The mark lost so much value that the paper it was printed on had more utility as fuel than as currency.",
    },
    {
        "tier": 1,
        "question": "Workers in 1923 Germany were paid TWICE A DAY so they could shop at lunch before prices doubled by dinner. What is this called?",
        "answer": "Hyperinflation — prices rising too fast to track",
        "choices": [
            "Hyperinflation — prices rising too fast to track",
            "Deflation — prices falling every hour",
            "Recession — when factories close down",
            "Tax day — when wages are doubled",
        ],
        "context": "Hyperinflation is conventionally defined as monthly inflation exceeding 50%. Weimar 1923 peaked at ~29,500%/month. Workers spent wages within hours of receiving them — by the next day the money was nearly worthless.",
    },
    {
        "tier": 1,
        "question": "A Weimar postcard from 1923 needed a stamp worth 50 BILLION marks. What had a stamp cost in 1914?",
        "answer": "About 10 pfennig — before the printing began",
        "choices": [
            "About 10 pfennig — before the printing began",
            "50 billion marks — but cheaper paper",
            "One gold coin — for normal mail",
            "Free for citizens — until 1920",
        ],
        "context": "Weimar's hyperinflation went from a 1914 postage stamp at 10 pfennig (0.10 mark) to a late-1923 stamp at 50 billion marks. The currency lost essentially all value in 9 years; most of the collapse happened in the final 12 months.",
    },
    {
        "tier": 1,
        "question": "When the German mark died in November 1923, people switched to a new currency in days. What gives any new money trust?",
        "answer": "Some real limit on supply — that people can believe",
        "choices": [
            "Some real limit on supply — that people can believe",
            "A new shape — chosen by the government",
            "Brighter paper — than the old kind",
            "Larger printing — across all bills",
        ],
        "context": "The Rentenmark (Nov 15, 1923) was nominally backed by land. The Reichsmark (1924) followed. What gave each new currency credibility was a credible commitment NOT to print like the old one. Without that commitment, trust never returns.",
    },

    # --- Zimbabwe trillion-dollar note (5)
    {
        "tier": 1,
        "question": "Zimbabwe's central bank printed a 100-TRILLION-dollar note in 2008. It bought one loaf of bread. Why?",
        "answer": "Printed too much — and trust collapsed",
        "choices": [
            "Printed too much — and trust collapsed",
            "Wheat prices rose — across all of Africa",
            "Bakers united — to charge crazy prices",
            "Bread got fancier — than ever before",
        ],
        "context": "Zimbabwe's hyperinflation peaked at an estimated 89.7 sextillion percent month-on-month in November 2008. The 100-trillion-dollar note is now sold as a souvenir. The currency was abandoned in 2009 in favor of US dollars and South African rand.",
    },
    {
        "tier": 1,
        "question": "Zimbabwe's 2008 hundred-trillion note now sells as a $20 souvenir. What's the lesson?",
        "answer": "Printed money — can be worth less than the paper",
        "choices": [
            "Printed money — can be worth less than the paper",
            "Big numbers — always look impressive on bills",
            "Souvenirs all cost — exactly twenty dollars",
            "Zimbabwe printed — only one of these notes",
        ],
        "context": "The 100-trillion-dollar Zimbabwe note is one of the most famous artifacts of modern hyperinflation. Today it trades online for $15-30 as a collectible — far more than it was ever worth as currency.",
    },
    {
        "tier": 1,
        "question": "In 2008 Zimbabwe, a single egg cost 50 BILLION Zim dollars. By 2009 the country gave up its own money. What did Zimbabweans use instead?",
        "answer": "US dollars — and South African rand",
        "choices": [
            "US dollars — and South African rand",
            "Old British pounds — sent from London",
            "Chinese yuan only — across all stores",
            "Barter for chickens — with no money",
        ],
        "context": "Zimbabwe abandoned its currency in April 2009 and adopted a multi-currency system anchored by the US dollar and South African rand. This is the typical end-game: when local fiat dies, citizens flee to harder foreign currencies.",
    },
    {
        "tier": 1,
        "question": "Mugabe's Zimbabwe printed money to pay its bills. By 2008 prices doubled every 24 hours. What was being paid for?",
        "answer": "Spending — without taxes to cover it",
        "choices": [
            "Spending — without taxes to cover it",
            "Loans from Mars — paid back monthly",
            "Trees — for an empty national park",
            "Salt deliveries — between major cities",
        ],
        "context": "Zimbabwe's hyperinflation funded patronage, military pay, and political programs the government couldn't raise through taxes. Printing money is the deficit's last resort — and historically the deadliest one for the currency.",
    },
    {
        "tier": 1,
        "question": "A photo from 2008 Zimbabwe shows a bread loaf priced at 35 MILLION Zim dollars. The next week it was 200 million. What kind of money was the Zim dollar?",
        "answer": "Fiat — and the printer wouldn't stop",
        "choices": [
            "Fiat — and the printer wouldn't stop",
            "Gold-backed — locked in deep vaults",
            "Pure silver — too heavy to spend",
            "Magic money — that grew on trees",
        ],
        "context": "Zimbabwe's currency was pure fiat. Mugabe's government used the central bank's printing press to fund spending. Hyperinflation followed within a few years. The pattern is universal: unlimited printing → unlimited collapse.",
    },

    # --- Venezuela weigh-money (5)
    {
        "tier": 1,
        "question": "By 2018, Venezuelan clerks weighed bolivar notes on scales instead of counting them. A bag of cash bought a chicken. Why?",
        "answer": "Inflation too fast — counting took too long",
        "choices": [
            "Inflation too fast — counting took too long",
            "Bolivars came in metal — too heavy to count",
            "Chickens were rare — only paid for by weight",
            "Clerks were lazy — and used scales for fun",
        ],
        "context": "Venezuelan hyperinflation reached an estimated 1.7 million percent in 2018. Counting individual notes for ordinary purchases became infeasible; weighing cash by the kilo became standard practice in many stores.",
    },
    {
        "tier": 1,
        "question": "Hugo Chavez's policies and his successor Maduro's prints destroyed the Venezuelan bolivar after 2014. What did Venezuelans switch to using?",
        "answer": "US dollars — for nearly all big purchases",
        "choices": [
            "US dollars — for nearly all big purchases",
            "Russian rubles — by personal order",
            "Spanish euros — paid in coin only",
            "Cuban pesos — accepted everywhere",
        ],
        "context": "Despite Venezuela's anti-US politics, citizens dollarized informally as the bolivar collapsed. By the late 2010s, much of Venezuela's economy ran on US dollars. The state's enemy-of-the-empire rhetoric did not save its currency.",
    },
    {
        "tier": 1,
        "question": "By 2019 Venezuela's bolivar lost most value in months. A chicken cost 14.6 MILLION bolivars. What had the government been doing?",
        "answer": "Printing bolivars — to fund socialist programs",
        "choices": [
            "Printing bolivars — to fund socialist programs",
            "Importing chickens — only from Cuba",
            "Banning all stores — from selling poultry",
            "Building a wall — around the country",
        ],
        "context": "Venezuela's hyperinflation came from years of money-printing to fund deficits, price controls that wrecked supply, and the destruction of the oil industry the country's revenue depended on. The pattern: print money, controls fail, real economy collapses.",
    },
    {
        "tier": 1,
        "question": "Venezuelan grandparents in 2019 saw life savings shrink to a few US dollars. Why call this a tax on savers?",
        "answer": "Inflation takes wealth — from saved cash",
        "choices": [
            "Inflation takes wealth — from saved cash",
            "Savers must pay — a yearly inflation fee",
            "Banks confiscated — old people's accounts",
            "Government collected — extra coin taxes",
        ],
        "context": "Inflation is a wealth transfer from savers (who hold cash and fixed-income claims) to debtors and the issuer (the state). Hyperinflation accelerates this transfer to total confiscation. Venezuelan retirees lost everything they had stored in bolivars.",
    },
    {
        "tier": 1,
        "question": "Once a country's money dies, citizens often switch to a foreign currency, gold, or barter. What does this tell us about fiat money?",
        "answer": "It needs trust — and trust can vanish overnight",
        "choices": [
            "It needs trust — and trust can vanish overnight",
            "It always wins — over gold in the end",
            "It works in storms — and during wars",
            "It's the strongest money — humans invented",
        ],
        "context": "Every dying fiat currency follows the same pattern: trust erodes, citizens flee to harder money (foreign currency, gold, dollars, lately Bitcoin), and the local currency dies. The escape valve always exists.",
    },

    # --- Argentina inflation + Bitcoin + what money does (5)
    {
        "tier": 1,
        "question": "Argentina's peso has been devalued many times since 1900. Argentines today often hide US dollars under mattresses. Why?",
        "answer": "They don't trust pesos — to hold value",
        "choices": [
            "They don't trust pesos — to hold value",
            "Dollars smell better — in Argentina",
            "Pesos are too big — to fit in mattresses",
            "Argentines collect — old US presidents",
        ],
        "context": "Argentina has gone through repeated currency collapses (1989 hyperinflation, 2001 default, 2018-23 crisis, 2024 ongoing). Argentines hold US dollars informally because the peso has lost over 99.9% of its value across multiple resets.",
    },
    {
        "tier": 1,
        "question": "On Halloween 2008, Satoshi Nakamoto posted a 9-page paper about a new kind of money. What was new?",
        "answer": "It needed no central bank — to issue or control",
        "choices": [
            "It needed no central bank — to issue or control",
            "It was made of plastic — instead of paper",
            "Each coin tracked — a specific gold bar",
            "Citizens voted — on the price each day",
        ],
        "context": "Satoshi Nakamoto's Bitcoin white paper appeared October 31, 2008, on the metzdowd.com cryptography list. The Genesis block was mined January 3, 2009. Bitcoin is the first money in history with no central issuer.",
    },
    {
        "tier": 1,
        "question": "Bitcoin can never have more than 21 million coins. The number is locked in the code. How is this different from a dollar?",
        "answer": "Dollars can be printed — Bitcoin cannot",
        "choices": [
            "Dollars can be printed — Bitcoin cannot",
            "Bitcoins are paper — but dollars are gold",
            "Dollars only work — in the United States",
            "Bitcoin must be earned — dollars are free",
        ],
        "context": "Bitcoin's hard supply cap of 21 million is enforced by every node on the network. The Fed can create dollars in unlimited quantity by keystroke. Bitcoin's monetary policy is set by code; the dollar's is set by 12 people on a committee.",
    },
    {
        "tier": 1,
        "question": "Money does 3 jobs: store of value, medium of exchange, unit of account. Which does Weimar money fail at?",
        "answer": "All three — dying money fails every job",
        "choices": [
            "All three — dying money fails every job",
            "Just storage — but still works in trades",
            "Just trade — but holds value over time",
            "Just measure — but stores and trades well",
        ],
        "context": "Money has three classical functions: store of value, medium of exchange, unit of account. Hyperinflation destroys all three: nobody saves it, transactions break, and prices change so fast they can't be compared.",
    },
    {
        "tier": 1,
        "question": "Sound money keeps its value over time. Fiat money loses value over time. Which one is better for saving for your future?",
        "answer": "Sound money — its supply can't be inflated away",
        "choices": [
            "Sound money — its supply can't be inflated away",
            "Fiat money — printed by experts in DC",
            "Both equal — they work the same",
            "Whichever's prettier — on the bill",
        ],
        "context": "Sound money (gold, silver, Bitcoin) has a fixed or hard-to-expand supply. Fiat money has unlimited supply at the discretion of issuers. Across long timeframes, sound money preserves purchasing power; fiat does not.",
    },
]


# =============================================================================
# P4 — Central Banking / Keynes critique (40)
# =============================================================================

P4_QUESTIONS: list[dict] = [
    # --- Nixon Sunday-night gold window (5)
    {
        "tier": 1,
        "question": "On Sunday night, August 15, 1971, Nixon went on TV and said the US dollar would no longer trade for gold. What did he end that day?",
        "answer": "The gold standard — for the US dollar",
        "choices": [
            "The gold standard — for the US dollar",
            "The minimum wage — across the nation",
            "TV broadcasts — on Sunday nights",
            "Gold mining — in California",
        ],
        "context": "Nixon's August 15, 1971 announcement closed the gold window — the last formal link between the US dollar and gold. Since then, every major currency in the world has been pure fiat.",
    },
    {
        "tier": 1,
        "question": "Nixon picked Sunday night to announce the gold change. Markets were closed. Why did he do it then?",
        "answer": "So traders couldn't react — until Monday morning",
        "choices": [
            "So traders couldn't react — until Monday morning",
            "Sunday was his lucky — day every week",
            "Football pre-empted — the regular news",
            "Congress only opened — on Sunday in 1971",
        ],
        "context": "Nixon chose Sunday night specifically so currency markets couldn't react before the policy was in force Monday. The maneuver locked in the change before traders could move their gold or dollars.",
    },
    {
        "tier": 1,
        "question": "Before 1971, foreign governments could trade $35 for one ounce of US gold. Nixon ended this. What did the dollar become?",
        "answer": "Pure fiat — backed only by government decree",
        "choices": [
            "Pure fiat — backed only by government decree",
            "Backed by oil — instead of gold",
            "Replaced by yen — across the world",
            "A new gold coin — minted in Texas",
        ],
        "context": "Bretton Woods (1944) had fixed the dollar at $35/oz gold and made it the world's reserve currency. Nixon's August 15, 1971 'temporary' suspension of gold convertibility became permanent. The dollar has been pure fiat ever since.",
    },
    {
        "tier": 1,
        "question": "After Nixon ended the gold dollar in 1971, US inflation surged to over 13% by 1979. The 1970s are remembered as a decade of what?",
        "answer": "High inflation — caused by unlimited dollar printing",
        "choices": [
            "High inflation — caused by unlimited dollar printing",
            "Stable prices — and easy living",
            "Low gas prices — at every pump",
            "Strong dollars — across the world",
        ],
        "context": "1970s US inflation peaked at 13.5% in 1980. Removing the gold constraint in 1971 enabled monetary expansion that hadn't been possible before. Volcker's 20% rates broke the cycle by 1982.",
    },
    {
        "tier": 1,
        "question": "Before August 15, 1971, the dollar was tied to gold for centuries through different forms. After that day, what limited the supply of dollars?",
        "answer": "Nothing — just the Fed's choices",
        "choices": [
            "Nothing — just the Fed's choices",
            "A new gold mine — opened in Alaska",
            "Each treasury bill — was real silver",
            "The US Mint — capped them yearly",
        ],
        "context": "The gold standard (in various forms) constrained the dollar from the founding through 1971. After Nixon's closure, the only constraint became the Federal Reserve's own discretion — and the Fed has expanded the money supply by orders of magnitude since.",
    },

    # --- Fed created 1913 (5)
    {
        "tier": 1,
        "question": "The US Federal Reserve was created on December 23, 1913, by an act of Congress. What does the Fed control?",
        "answer": "The supply of US dollars — and interest rates",
        "choices": [
            "The supply of US dollars — and interest rates",
            "All taxes — collected each year",
            "Every store — in the United States",
            "How much gold — is mined yearly",
        ],
        "context": "The Federal Reserve Act of 1913 was signed by President Woodrow Wilson. The Fed sets the federal funds rate, controls the money supply through open-market operations, and regulates banks. Since 1913, the dollar has lost about 97% of its purchasing power.",
    },
    {
        "tier": 1,
        "question": "Six men met secretly on Jekyll Island in 1910. They used only first names so porters wouldn't know them. What did they draft?",
        "answer": "The plan — that became the Fed in 1913",
        "choices": [
            "The plan — that became the Fed in 1913",
            "A new branch — of the US Boy Scouts",
            "A new edition — of the Boston Tea Party",
            "A secret movie — about Wall Street banks",
        ],
        "context": "The Jekyll Island meeting (November 1910) drafted the Aldrich Plan, which became (lightly modified) the Federal Reserve Act of 1913. The conspirators included Senator Aldrich, Henry Davison (JP Morgan), Paul Warburg, Frank Vanderlip, A. Piatt Andrew, and Benjamin Strong.",
    },
    {
        "tier": 1,
        "question": "The Fed was created in 1913 to prevent banking panics. In 1929 the worst banking panic in US history happened. What does this say about the Fed?",
        "answer": "It failed its main founding promise — early on",
        "choices": [
            "It failed its main founding promise — early on",
            "It saved the day — and stopped the panic",
            "It hadn't opened yet — by 1929",
            "It tried hard — but had no money",
        ],
        "context": "Friedman and Schwartz's *A Monetary History of the United States* (1963) argued the Fed didn't just fail to stop the Great Depression — the Fed *caused* it by allowing the money supply to contract by ~33% between 1929 and 1933.",
    },
    {
        "tier": 1,
        "question": "The Fed's logo says 'Federal' but it's not really a government agency. It's owned by private banks. Why might that matter?",
        "answer": "Its owners may put bank interests — over public ones",
        "choices": [
            "Its owners may put bank interests — over public ones",
            "Private logos are prettier — than federal ones",
            "It always works — for the average citizen",
            "Private banks — pay all the taxes",
        ],
        "context": "The Federal Reserve System's 12 regional banks are owned by member commercial banks. While the Board of Governors is appointed by the President, the structure creates a permanent regulatory-banking relationship that public-choice theory predicts will favor incumbent banks.",
    },
    {
        "tier": 1,
        "question": "Before the Fed opened in 1913, the dollar held value for 100 years. After the Fed, it lost 97% in 100 years. Why?",
        "answer": "The Fed could expand money — without limit",
        "choices": [
            "The Fed could expand money — without limit",
            "Smaller dollar bills — printed each year",
            "A new gold mine — under Federal Hall",
            "Silver-backed dollars — in every state",
        ],
        "context": "From 1800 to 1913 the US dollar's purchasing power was roughly flat. From 1913 to today it has fallen by about 97%. The arrival of an institution capable of unlimited monetary expansion produced unlimited monetary expansion.",
    },

    # --- why printing money raises prices (5)
    {
        "tier": 1,
        "question": "If everyone in town wakes up with double the cash, but the bakery still bakes 100 loaves, what happens to the price of bread?",
        "answer": "It rises — more money chasing the same loaves",
        "choices": [
            "It rises — more money chasing the same loaves",
            "It falls — because cash flows easier",
            "It stays the same — bread is bread",
            "Bread becomes free — for everyone",
        ],
        "context": "The basic mechanism: when the money supply rises faster than the supply of goods, the price of goods (measured in money) rises. Doubling the money without doubling the goods means roughly doubling the prices.",
    },
    {
        "tier": 1,
        "question": "A government prints lots of new money to pay for a war or program. Why does this make prices rise?",
        "answer": "More dollars chase — the same amount of stuff",
        "choices": [
            "More dollars chase — the same amount of stuff",
            "Printers run hotter — and burn the paper",
            "New bills weigh less — than old ones",
            "Treasury workers — eat more food",
        ],
        "context": "Monetary inflation: when money expands faster than goods, prices rise. This isn't psychology, it's arithmetic. The Federal Reserve expanded its balance sheet from $900B to $9T from 2008-2022; US inflation followed.",
    },
    {
        "tier": 1,
        "question": "The Federal Reserve doubled the dollars in the system between 2020 and 2022. In 2022 US inflation hit 9.1% in June. Why?",
        "answer": "More dollars chasing — the same goods raised prices",
        "choices": [
            "More dollars chasing — the same goods raised prices",
            "Russia's war — caused all the inflation",
            "People spent too much — out of habit",
            "Stores got greedy — at the same time",
        ],
        "context": "The Fed's balance sheet went from about $4T (Feb 2020) to $9T by 2022. US inflation hit 9.1% in June 2022 — the worst in 40 years. The 2021-23 inflation aged MMT poorly: when the constraint (inflation) arrived, it arrived big.",
    },
    {
        "tier": 1,
        "question": "When government prints money, the first spenders do well. By the time it reaches retirees, prices rose. What's this called?",
        "answer": "Cantillon effect — early gain, savers lose",
        "choices": [
            "Cantillon effect — early gain, savers lose",
            "Robin Hood effect — equal for all citizens",
            "Tax effect — paid by all home owners",
            "Mailman effect — slow but steady ripples",
        ],
        "context": "Richard Cantillon (18th-century banker and economist) observed that new money doesn't lift all prices equally at once. Early recipients buy at old prices; late recipients buy at new, higher prices. Monetary inflation transfers wealth from late recipients (savers, wage earners) to early ones (banks, contractors, asset holders).",
    },
    {
        "tier": 1,
        "question": "A government printing money to pay its bills is sometimes called 'taxing the savers.' Why?",
        "answer": "Their saved cash — buys less over time",
        "choices": [
            "Their saved cash — buys less over time",
            "Tax bills get bigger — every spring",
            "Banks charge them — a special fee",
            "Old savers must pay — a yearly fine",
        ],
        "context": "Inflation is a wealth transfer from savers to the issuer (the state). A retiree with $100,000 in cash sees their real wealth drop as prices rise. The state doesn't need to legislate a tax; printing money has the same effect — sometimes called the 'inflation tax.'",
    },

    # --- Milton Friedman / Capitalism & Freedom (5)
    {
        "tier": 1,
        "question": "Milton Friedman wrote 'Capitalism and Freedom' in 1962. His big idea: economic and political freedom are tied together. Why?",
        "answer": "Free markets disperse power — preventing tyranny",
        "choices": [
            "Free markets disperse power — preventing tyranny",
            "Money is fun — and creates happiness",
            "Capitalism pays — for new museums",
            "Markets only matter — in big cities",
        ],
        "context": "Milton Friedman's *Capitalism and Freedom* (1962) argued that economic freedom — voluntary exchange, private property, free markets — is a prerequisite for political freedom. Centralizing economic decisions inevitably centralizes political power. Friedman won the 1976 Nobel.",
    },
    {
        "tier": 1,
        "question": "Friedman said: 'Inflation is always and everywhere a monetary phenomenon.' What did he mean?",
        "answer": "Inflation comes from printing money — not from greedy stores",
        "choices": [
            "Inflation comes from printing money — not from greedy stores",
            "Inflation is psychological — caused by mood",
            "Inflation is the weather's fault — most years",
            "Inflation only happens — in the winter",
        ],
        "context": "Friedman's famous dictum from his monetary economics work: 'Inflation is always and everywhere a monetary phenomenon.' Rising prices come from money supply expanding faster than goods. Blaming 'corporate greed' or 'supply chains' misses the cause.",
    },
    {
        "tier": 1,
        "question": "Friedman argued that price controls — laws saying 'gas can't cost more than $1' — cause what?",
        "answer": "Shortages — sellers won't sell at the fixed price",
        "choices": [
            "Shortages — sellers won't sell at the fixed price",
            "Plenty — stores compete to lower prices",
            "Higher wages — for store cashiers",
            "Bigger stores — and longer hours",
        ],
        "context": "Friedman: 'There is one and only one way to bring on a shortage — that is to set a price below the equilibrium price.' Nixon's 1971-74 price controls produced the gas-line shortages of the 1970s. The pattern is universal.",
    },
    {
        "tier": 1,
        "question": "Milton Friedman appeared on a TV show in 1980 called 'Free to Choose.' His core message was that markets do what better than governments?",
        "answer": "Coordinate millions of people — without forcing them",
        "choices": [
            "Coordinate millions of people — without forcing them",
            "Build the tallest towers — in every city",
            "Sing on stage — at award shows",
            "Hold elections — in every county",
        ],
        "context": "*Free to Choose* (PBS, 1980) was Friedman's accessible introduction to free-market economics. Its core argument: voluntary exchange coordinates dispersed human action better than central planning, while preserving freedom.",
    },
    {
        "tier": 1,
        "question": "Friedman quipped: put the feds in charge of the Sahara Desert and in 5 years there'd be a sand shortage. The joke means what?",
        "answer": "Government runs out — even of abundant things",
        "choices": [
            "Government runs out — even of abundant things",
            "Sand is mostly needed — only in California",
            "Deserts grow more — when you water them",
            "All federal lands — have too many cacti",
        ],
        "context": "Friedman's famous wisecrack illustrates the public-choice insight: government allocation of resources tends to produce shortages even of things in abundance, because political incentives substitute for price signals. The Soviets ran out of wheat on the world's best farmland.",
    },

    # --- Volcker 20% rates 1980 (5)
    {
        "tier": 1,
        "question": "By 1980, US inflation was 13.5%. Fed chair Paul Volcker took the unusual step of raising interest rates to 20%. Why?",
        "answer": "To stop people from borrowing — so prices would fall",
        "choices": [
            "To stop people from borrowing — so prices would fall",
            "To make banks rich — for funding his career",
            "Because 20 was — his lucky number",
            "To match the inflation — and copy it",
        ],
        "context": "Paul Volcker raised the federal funds rate above 20% in mid-1981 to break the inflationary spiral of the 1970s. Borrowing slowed, the economy briefly contracted, and inflation fell from 13.5% in 1980 to 3.2% by 1983. The pain was real; the cure worked.",
    },
    {
        "tier": 1,
        "question": "Volcker's 20% rates in 1981 caused a sharp recession. Unemployment hit 10.8%. Inflation fell to 3% by 1983. What did he prove?",
        "answer": "Inflation can stop — but the cure hurts",
        "choices": [
            "Inflation can stop — but the cure hurts",
            "Inflation is permanent — once it starts",
            "Inflation only ends — when wars all do",
            "Inflation cures itself — every five years",
        ],
        "context": "Volcker's 1980-82 monetary tightening proved central banks can break inflation when committed. The cost: unemployment 10.8% (Nov 1982), the worst since the Great Depression. After Volcker, the Fed never again let inflation run that hot — until 2021-22.",
    },
    {
        "tier": 1,
        "question": "From 2008 to 2022, the Fed kept interest rates near 0%. In 2022 inflation hit 9.1%. Why did the Fed have to raise rates fast?",
        "answer": "To slow borrowing — and stop prices from rising",
        "choices": [
            "To slow borrowing — and stop prices from rising",
            "To match other countries — for fairness",
            "Because zero was — getting boring",
            "To help banks make — bigger profits",
        ],
        "context": "After 14 years of near-zero rates and trillions in QE, the Fed had to raise rates from 0% to 5.5% in 2022-2023 to address the post-COVID inflation. The Volcker playbook — but applied late and reluctantly. Asset markets shook.",
    },
    {
        "tier": 1,
        "question": "Volcker broke 1970s inflation. Greenspan, Bernanke, and Powell came after. What did they do differently?",
        "answer": "Kept rates lower — to support markets",
        "choices": [
            "Kept rates lower — to support markets",
            "Banned inflation — by federal decree",
            "Returned to gold — in the year 2000",
            "Met only on Sundays — like Nixon",
        ],
        "context": "Post-Volcker Fed chairs (Greenspan 1987-2006, Bernanke 2006-14, Yellen 2014-18, Powell 2018-) gradually lowered the policy rate ceiling and intervened more aggressively to prevent market declines. The 'Fed put' became a market expectation. ABCT predicts the cycle of bubbles that followed.",
    },
    {
        "tier": 1,
        "question": "Volcker said breaking inflation 'requires more courage than economic skill.' What did he mean?",
        "answer": "The cure is unpopular — and politicians resist it",
        "choices": [
            "The cure is unpopular — and politicians resist it",
            "Math is hard — for central bankers",
            "Skill comes naturally — to all bankers",
            "Inflation only ends — by accident",
        ],
        "context": "Volcker's tightening was politically brutal. Farmers drove tractors to Washington in protest. Builders sent him 2x4s with angry messages. The recession was severe. Most central bankers since have lacked the political will to repeat it.",
    },

    # --- what a central bank is + Keynes critique (5)
    {
        "tier": 1,
        "question": "A central bank controls a country's other banks, sets rates, and prints money. What problem does that create?",
        "answer": "One group decides — for millions of people",
        "choices": [
            "One group decides — for millions of people",
            "There's not enough banks — to go around",
            "Banks fight all day — over board policy",
            "Money becomes too easy — to print fast",
        ],
        "context": "Central banks centralize monetary decisions in a small committee. Hayek's knowledge problem applies: no group has the information needed to set interest rates better than markets would. Mises predicted the malinvestment cycles this would cause.",
    },
    {
        "tier": 1,
        "question": "Keynes said in 1936 that government spending could end recessions. Hayek asked: where does the money come from?",
        "answer": "Taxing or printing — both shift costs",
        "choices": [
            "Taxing or printing — both shift costs",
            "Special trees — that grow government cash",
            "Free money — handed out by treaty",
            "A magic vault — Keynes hid in Paris",
        ],
        "context": "Keynes's *General Theory* (1936) became the playbook for using government deficits to 'manage' recessions. Hayek's critique: every dollar the government spends is one it took from taxpayers or borrowed against the future. Bastiat's seen-and-unseen applies.",
    },
    {
        "tier": 1,
        "question": "Keynesians say: when people stop spending, government should spend more. What do Austrians say instead?",
        "answer": "Recessions clear bad investments — and must run",
        "choices": [
            "Recessions clear bad investments — and must run",
            "Recessions are caused — only by sunspots",
            "Recessions can never — be ended at all",
            "Recessions only hit — every 100 years",
        ],
        "context": "Austrian Business Cycle Theory (Mises, Hayek): cheap-credit booms generate malinvestment; the recession is the necessary correction. Trying to prevent it through more cheap credit just postpones a bigger crash. The 2008 GFC vindicated ABCT against the consensus.",
    },
    {
        "tier": 1,
        "question": "John Maynard Keynes famously said: 'In the long run, we are all dead.' What was he arguing against?",
        "answer": "Worry about future debt — from his spending plans",
        "choices": [
            "Worry about future debt — from his spending plans",
            "Long-term sports games — at the Olympics",
            "Doctors who say — to eat your vegetables",
            "Living forever — in a magical land",
        ],
        "context": "Keynes's quip dismissed long-run concerns about deficits and inflation. The line aged poorly: the US national debt passed $34 trillion in 2024. Austrians warned this would happen. The long run keeps arriving.",
    },
    {
        "tier": 1,
        "question": "A central planning committee tries to set the right interest rate for an entire country. Friedrich Hayek said this is impossible. Why?",
        "answer": "No committee has the knowledge — that prices encode",
        "choices": [
            "No committee has the knowledge — that prices encode",
            "Math is too hard — for committees",
            "They argue too much — to decide",
            "Rooms are too small — for all the data",
        ],
        "context": "Hayek's 1945 'The Use of Knowledge in Society' showed that prices encode dispersed, tacit, local knowledge no central planner can collect. Setting an interest rate by committee — the Fed's job — is exactly the activity Hayek showed cannot work as well as markets.",
    },

    # --- Friedman + 2008 + cycle recognition (5)
    {
        "tier": 1,
        "question": "The Fed kept interest rates at 1% from 2003 to 2004 — very low. Then housing prices skyrocketed. In 2008 they crashed. What does ABCT say happened?",
        "answer": "Cheap credit built a bubble — that had to burst",
        "choices": [
            "Cheap credit built a bubble — that had to burst",
            "Houses got too big — and fell over",
            "Builders forgot — to use real wood",
            "Storms in 2008 — hit every home",
        ],
        "context": "Austrian Business Cycle Theory predicts that artificially low interest rates cause businesses and consumers to invest in projects that aren't really profitable. The 2003-04 Fed easy-money policy fueled the housing bubble that collapsed in 2008. Austrians predicted this; the mainstream profession did not.",
    },
    {
        "tier": 1,
        "question": "After the 2008 crash, the Fed printed trillions to 'save' the banks. The banks were bailed out. Who paid for it?",
        "answer": "Future taxpayers and savers — through inflation",
        "choices": [
            "Future taxpayers and savers — through inflation",
            "Nobody — the Fed makes free money",
            "Each banker — out of personal pay",
            "Aliens visiting Earth — once a year",
        ],
        "context": "The 2008 bank bailouts (TARP $700B + Fed expansion to $4T) socialized losses to taxpayers and savers while protecting bondholders. 'Privatized profits, socialized losses' — the moral hazard that produced even bigger crises.",
    },
    {
        "tier": 1,
        "question": "After 2008, the Fed promised no more crises. In 2023 several US banks collapsed anyway. What's the pattern?",
        "answer": "Bailouts grow risk — and breed bigger crises",
        "choices": [
            "Bailouts grow risk — and breed bigger crises",
            "Bankers learn fast — from each mistake",
            "Crisis only hits — in odd-numbered years",
            "The Fed always wins — over enough time",
        ],
        "context": "Moral hazard: when actors are protected from the consequences of their bets, they take bigger bets. The 2023 collapses of Silicon Valley Bank, Signature Bank, and First Republic followed the same pattern of subsidized risk-taking that produced 2008.",
    },
    {
        "tier": 1,
        "question": "Every major 1900s fiat currency either died or lost most value. The dollar survived. How much has it lost since 1913?",
        "answer": "About 97% — even survivors fall a lot",
        "choices": [
            "About 97% — even survivors fall a lot",
            "Around 0% — it's stayed quite stable",
            "Roughly 5% — a normal small drop",
            "Roughly 30% — a moderate loss too",
        ],
        "context": "The US dollar has lost roughly 97% of its purchasing power since 1913. It's considered a 'success story' for fiat because it hasn't completely collapsed. Most other fiat currencies of 1913 (German mark, Russian ruble, Argentine peso) died at least once.",
    },
    {
        "tier": 1,
        "question": "Fiat money has existed in many countries for thousands of years. Across all history, what percentage of fiat currencies have died?",
        "answer": "Eventually all of them — fiat dies, sound money survives",
        "choices": [
            "Eventually all of them — fiat dies, sound money survives",
            "Just a few — most still exist today",
            "About half — and half live forever",
            "None — fiat is the strongest form",
        ],
        "context": "Across history, every fiat currency has either died completely or lost most of its value. Sound money (gold, silver) survives. The current set of fiat currencies are still in their first century — the experiment is young by historical standards. The pattern is clear.",
    },

    # --- 5 more P4: Friedman/MMT/Cantillon/quantitative easing/Greenspan put
    {
        "tier": 1,
        "question": "Milton Friedman called inflation a 'tax without legislation.' Why a tax?",
        "answer": "Government gets value — savers lose value",
        "choices": [
            "Government gets value — savers lose value",
            "Stores pay extra — to the IRS each year",
            "Inflation goes — to fund federal parks",
            "Banks collect it — and pay it to the Fed",
        ],
        "context": "Friedman: inflation acts like a tax — the state captures resources, and savers and wage earners lose purchasing power. Unlike legislated taxes, inflation needs no vote. This is one reason governments love printing money.",
    },
    {
        "tier": 1,
        "question": "MMT said a country printing money can never 'run out.' US inflation hit 9.1% in 2022 after huge printing. What did MMT miss?",
        "answer": "Inflation is the real limit — and it bites",
        "choices": [
            "Inflation is the real limit — and it bites",
            "All countries — must print more money",
            "Wars can absorb — unlimited new dollars",
            "Inflation never — hits in modern times",
        ],
        "context": "Stephanie Kelton's *The Deficit Myth* (2020) was MMT's most influential statement. Its central claim — that fiat issuers face only inflation constraints — was falsified by the 2021-23 inflation spike. The constraint arrived bigger and faster than the framework implied.",
    },
    {
        "tier": 1,
        "question": "The Fed buying $4 trillion in bonds after 2008 was called 'quantitative easing.' What did it really mean?",
        "answer": "Printing dollars — to buy bonds from banks",
        "choices": [
            "Printing dollars — to buy bonds from banks",
            "Easing rules — on grocery store credit",
            "A tax break — on student college loans",
            "A bonus check — sent to all citizens",
        ],
        "context": "Quantitative easing (QE) is the Fed creating new dollars to buy financial assets, mainly Treasury bonds and mortgage securities. The Fed's balance sheet went from $900B in 2008 to about $9T by 2022. The Cantillon effect: banks got the new money first.",
    },
    {
        "tier": 1,
        "question": "The 'Greenspan put' described Fed chair Alan Greenspan cutting rates whenever markets fell. What did markets learn from this?",
        "answer": "The Fed will rescue them — so take bigger risks",
        "choices": [
            "The Fed will rescue them — so take bigger risks",
            "The Fed loves crashes — and helps them grow",
            "Markets must invest — only in US bonds",
            "Rates always rise — when markets crash",
        ],
        "context": "Alan Greenspan (Fed chair 1987-2006) cut rates after the 1987 crash, the 1998 LTCM collapse, the 2000 dotcom bust. Markets learned: take risks, get bailed out. The 'Greenspan put' produced the moral hazard that built the 2008 GFC.",
    },
    {
        "tier": 1,
        "question": "Friedrich Hayek wrote in 1944 that central planning leads to losing freedom. The book was called what?",
        "answer": "The Road to Serfdom — a 1944 warning",
        "choices": [
            "The Road to Serfdom — a 1944 warning",
            "The Wealth of Nations — Smith's old book",
            "Das Kapital — a famous 1867 work",
            "General Theory — Keynes's 1936 book",
        ],
        "context": "Hayek's *The Road to Serfdom* (1944) argued central economic planning inevitably erodes political freedom. Planners need increasing coercion to substitute for the information they lack. The 20th century's central-planning experiments vindicated this prediction.",
    },
]


# =============================================================================
# P5 — Practical Economics (40)
# =============================================================================

P5_QUESTIONS: list[dict] = [
    # --- lemonade stand (5)
    {
        "tier": 1,
        "question": "Lily sells lemonade for 50 cents. The town forces a $3 price to 'help her.' Customers vanish. What did the law do?",
        "answer": "Set price too high — sales dropped",
        "choices": [
            "Set price too high — sales dropped",
            "Made Lily rich — overnight by force",
            "Made lemons sweeter — than before",
            "Banned other kids — from sales",
        ],
        "context": "Price floors above market price create surpluses — unsold inventory. The 'help' is visible (higher price per cup), but the unseen cost (no buyers) outweighs it. Bastiat's seen-and-unseen applies.",
    },
    {
        "tier": 1,
        "question": "Tomas sells popsicles for $1. The mayor caps the price at 25 cents to 'help the poor.' What probably happens next?",
        "answer": "Tomas stops selling — there's no profit at that price",
        "choices": [
            "Tomas stops selling — there's no profit at that price",
            "He doubles his sales — and gets rich",
            "His popsicles get bigger — overnight",
            "The mayor pays him — the difference",
        ],
        "context": "Price ceilings below market price create shortages. Sellers exit; buyers can't find supply; black markets form. The intended help (lower price) becomes harm (no popsicles available). Rent control follows the same logic.",
    },
    {
        "tier": 1,
        "question": "Maria's lemonade stand makes $20 on a hot day, $2 on a cold day. Why is the price for cold-day lemonade lower?",
        "answer": "Less demand — fewer people want it when it's cold",
        "choices": [
            "Less demand — fewer people want it when it's cold",
            "Cold lemonade weighs — less than hot",
            "Cups freeze — and lose value fast",
            "Maria is meaner — on cold days",
        ],
        "context": "Demand changes with weather, season, and circumstance. Prices reflect the meeting of supply and demand. On a hot day, demand is high; on a cold day, low. The price signal communicates the change automatically.",
    },
    {
        "tier": 1,
        "question": "Ben raises lemonade from 50 cents to $1. Sales halve. He earns the same money for half the work. What's the lesson?",
        "answer": "Higher prices — cut demand but raise revenue",
        "choices": [
            "Higher prices — cut demand but raise revenue",
            "Customers love high prices — and buy more",
            "Lemons taste better — at higher prices",
            "Sales always drop — at exactly one half",
        ],
        "context": "The law of demand: higher prices reduce quantity demanded. But the new price-quantity combination may produce equal or greater revenue, depending on elasticity. Sellers experiment with prices to find the right point.",
    },
    {
        "tier": 1,
        "question": "Sara starts a lemonade stand. Three other kids open stands on her street. Soon all four kids charge 25 cents instead of $1. What forced prices down?",
        "answer": "Competition — buyers can pick the cheapest seller",
        "choices": [
            "Competition — buyers can pick the cheapest seller",
            "All four kids — agreed on a price",
            "The town wrote — a new rule",
            "Lemons got cheaper — the same week",
        ],
        "context": "Competition disciplines prices. When sellers compete for buyers, prices fall toward the cost of production. This is why free markets generate falling real prices over time — the opposite of what monopoly or central pricing produces.",
    },

    # --- opportunity cost (5)
    {
        "tier": 1,
        "question": "Eva has $5. She can buy ice cream OR save it. If she buys ice cream, what did the choice 'cost' her?",
        "answer": "The chance to save — for something later",
        "choices": [
            "The chance to save — for something later",
            "Five whole dollars — just disappeared",
            "Nothing — money doesn't matter",
            "A whole pizza — she could have bought",
        ],
        "context": "Opportunity cost is the value of the next-best option you give up. Eva's $5 spent on ice cream means $5 not saved. Every choice carries an opportunity cost — even doing nothing has a cost (the things you could have done).",
    },
    {
        "tier": 1,
        "question": "Jose can spend Saturday playing soccer OR mowing lawns for $20. He picks soccer. What did soccer 'cost'?",
        "answer": "$20 — the money he could have earned",
        "choices": [
            "$20 — the money he could have earned",
            "Nothing — soccer is free to play",
            "His soccer cleats — wore out",
            "Twenty calories — burned playing",
        ],
        "context": "Opportunity cost includes time and forgone earnings. Jose's soccer game cost him the $20 mowing wage. This doesn't mean soccer was wrong — but it shows every choice has a true cost beyond cash spent.",
    },
    {
        "tier": 1,
        "question": "Mom takes a day off work to drive Anna to the dentist. The dentist is free, but Mom skipped a $200 work day. What was the dentist visit's TRUE cost?",
        "answer": "$200 — the wages Mom didn't earn",
        "choices": [
            "$200 — the wages Mom didn't earn",
            "$0 — the dentist was free",
            "The gas to drive — just $5",
            "Anna's lost school day — was free",
        ],
        "context": "The 'free' dentist had a real cost: Mom's foregone wages. Hidden costs are everywhere. Bastiat's seen-and-unseen: what you see is the free dentist; what you don't see is the lost income that made the visit possible.",
    },
    {
        "tier": 1,
        "question": "Tim waits 2 hours for a free hat. His friend Sara works 2 hours, earns $30, and buys 10 hats. What did Tim's 'free' hat cost?",
        "answer": "$30 — the wages he could have earned",
        "choices": [
            "$30 — the wages he could have earned",
            "Nothing at all — the hat was truly free",
            "Just patience — and a long smile",
            "Two hours — and nothing else more",
        ],
        "context": "Time is money — opportunity cost. Tim's 'free' hat cost him $30 in foregone earnings. Free things often cost more than priced things because they're paid in time, hassle, or waiting. The price isn't always the cost.",
    },
    {
        "tier": 1,
        "question": "Maya picks one of two $5 games. She picks the one with friends. What did she give up?",
        "answer": "Fun of the other game — opportunity cost",
        "choices": [
            "Fun of the other game — opportunity cost",
            "Five whole dollars — she still has them",
            "Time itself — she'd spend either way",
            "Nothing real — second choice is free",
        ],
        "context": "Opportunity cost is what you forgo. Even when the dollar cost is the same, the foregone alternative (playing the other game) is the real opportunity cost. Decisions are about trade-offs, never absolute gains.",
    },

    # --- supply and demand (5)
    {
        "tier": 1,
        "question": "It's Pokemon card trading day at school. Charizards are rare; only two kids have one. Magikarps are everywhere. Which card trades for more?",
        "answer": "Charizard — fewer exist, more kids want them",
        "choices": [
            "Charizard — fewer exist, more kids want them",
            "Magikarp — they're more common",
            "Both equal — cards are cards",
            "Whichever shines — brightest",
        ],
        "context": "Scarcity + desire = price. Charizards are scarce AND wanted; Magikarps are common AND less desired. Price reflects the meeting of supply (how much exists) and demand (how much is wanted). Markets discover this automatically.",
    },
    {
        "tier": 1,
        "question": "On Tuesday, only 5 cupcakes are at the bake sale and 50 kids want one. By Friday, there are 50 cupcakes and 5 kids interested. What changes the price?",
        "answer": "Demand vs supply — both at the same time",
        "choices": [
            "Demand vs supply — both at the same time",
            "The cupcakes — taste different",
            "Tuesdays are pricier — than Fridays",
            "Bakers raise prices — for fun",
        ],
        "context": "Price reflects the meeting of supply and demand. When demand is high relative to supply, prices rise; when supply outruns demand, prices fall. This is the basic mechanism of markets — and what central planners cannot replicate.",
    },
    {
        "tier": 1,
        "question": "A snowstorm cuts off the town. Bread runs low. A loaf that cost $3 now costs $10. Why did the price jump?",
        "answer": "Supply fell — and demand stayed the same",
        "choices": [
            "Supply fell — and demand stayed the same",
            "Bakers got greedy — overnight",
            "Snowstorms make bread — taste better",
            "Bread got heavier — in the cold",
        ],
        "context": "When supply suddenly drops while demand holds, price rises. The 'gouging' looks unfair but the price signal does crucial work: it rations limited bread to those who need it most, and signals other bakers to bring supply.",
    },
    {
        "tier": 1,
        "question": "A toy that's hard to find sells for $100 at Christmas. After Christmas, the same toy sells for $20. Why?",
        "answer": "Demand collapsed — supply caught up too",
        "choices": [
            "Demand collapsed — supply caught up too",
            "Toys age fast — and lose value",
            "Stores hate Christmas — and lower prices",
            "Kids forget toys — by January",
        ],
        "context": "Seasonal demand changes everything. Christmas spike + temporary shortage = high prices. After Christmas, demand falls and supply catches up = low prices. The price signal coordinates supply and demand over time.",
    },
    {
        "tier": 1,
        "question": "A baseball card collector wants a 1952 Mickey Mantle. Only a few hundred exist. Why is one card worth $12 million today?",
        "answer": "Tiny supply — and very strong demand",
        "choices": [
            "Tiny supply — and very strong demand",
            "Cards from 1952 — are made of gold",
            "Mickey Mantle owned — every card",
            "All baseball cards — cost $12 million",
        ],
        "context": "A near-mint 1952 Topps Mickey Mantle sold for $12.6 million in 2022. Tiny supply (only a few hundred high-grade copies exist) meets enormous demand from collectors. Scarcity + desire = price.",
    },

    # --- incentives (5)
    {
        "tier": 1,
        "question": "Mom pays Henry $5 for mowing the lawn. Suddenly Henry wants to mow every Saturday. What changed his behavior?",
        "answer": "The $5 reward — gave him an incentive",
        "choices": [
            "The $5 reward — gave him an incentive",
            "He just got happier — about grass",
            "The lawn mower — got lighter",
            "His friends — also wanted mowing",
        ],
        "context": "Incentives drive behavior. People do more of what they're rewarded for, less of what they're punished for. This is the core insight of economics. Government policy, school grades, family chores — all run on incentives, whether designers see it or not.",
    },
    {
        "tier": 1,
        "question": "Dad gives Lily $1 for every book she reads. By month two, she's read 20 books. What happens if Dad stops paying?",
        "answer": "She probably reads fewer — incentives matter",
        "choices": [
            "She probably reads fewer — incentives matter",
            "She reads even more — for fun alone",
            "She forgets — how to read",
            "She demands $10 — per book instead",
        ],
        "context": "Extrinsic rewards change behavior. Take the reward away, and behavior usually returns to baseline (sometimes lower, since the activity is now 'work'). Public-choice theory uses this to explain political behavior too.",
    },
    {
        "tier": 1,
        "question": "A grocery store fines workers $10 for being late, and rewards them $10 for being early. Which probably reduces lateness more?",
        "answer": "Both work — but together they work best",
        "choices": [
            "Both work — but together they work best",
            "Neither — workers don't care",
            "Just the fine — rewards are useless",
            "Just rewards — fines never work",
        ],
        "context": "Incentives can be positive (rewards) or negative (penalties). Both shape behavior. Used together they create a strong gradient. Bastiat: when you make something more expensive (fines for lateness), you get less of it; when you make something cheaper (rewards for early), you get more.",
    },
    {
        "tier": 1,
        "question": "A town pays parents $100 per child to plant a tree. Lots of trees get planted. The town stops the payment. What happens next year?",
        "answer": "Far fewer trees — the incentive is gone",
        "choices": [
            "Far fewer trees — the incentive is gone",
            "Even more trees — out of habit",
            "Forests grow themselves — overnight",
            "Each parent plants — exactly one more",
        ],
        "context": "Behavior shifts when incentives change. Subsidies produce more of what's subsidized; remove the subsidy, and the activity slows. Public-choice theory uses this to predict every policy program's actual effect — often very different from what was promised.",
    },
    {
        "tier": 1,
        "question": "The teacher says: 'You get bonus points for asking questions.' Suddenly the class has many questions. What worked?",
        "answer": "The incentive — bonus points changed behavior",
        "choices": [
            "The incentive — bonus points changed behavior",
            "The teacher got — more interesting",
            "Questions grew — on the walls",
            "Magic spell — was cast on the room",
        ],
        "context": "Rewards shape behavior. The classroom example is a small-scale demonstration of what economists call incentive design. Politicians use this principle constantly — tax breaks for some activities, taxes on others — usually with predictable but unintended results.",
    },

    # --- comparative advantage (5)
    {
        "tier": 1,
        "question": "Lia is fast at mowing AND raking. Sister Mae is slower at both, but slowest at mowing. Why does Lia mow while Mae rakes?",
        "answer": "Together — they finish faster than alone",
        "choices": [
            "Together — they finish faster than alone",
            "Lia must — handle all chores by herself",
            "Mae can only — do dishes inside the home",
            "They should both — try to mow first today",
        ],
        "context": "Comparative advantage (David Ricardo, 1817): even when one party is better at both tasks, both parties gain by specializing in the task where each has the lowest opportunity cost. Lia mowing + Mae raking finishes the yard faster than either doing both.",
    },
    {
        "tier": 1,
        "question": "Dad cooks faster than Mom. Mom cleans faster than Dad. Why might they each specialize instead of both doing both?",
        "answer": "Together they finish meals — faster than competing",
        "choices": [
            "Together they finish meals — faster than competing",
            "Cleaning is more fun — than cooking",
            "Dads should always — wash dishes",
            "Moms should never — pick up brooms",
        ],
        "context": "Specialization based on comparative advantage maximizes household production. Each spouse does what they're relatively better at. The same logic scales: between people, between firms, between nations. Free trade lets everyone specialize.",
    },
    {
        "tier": 1,
        "question": "England makes 10 shirts an hour. Portugal makes 5 shirts but 8 wine bottles an hour. Why might Portugal make wine and trade?",
        "answer": "Both gain — by doing what they're best at",
        "choices": [
            "Both gain — by doing what they're best at",
            "Shirts are heavier — than wine bottles",
            "England banned wine — by parliament law",
            "Portugal has no sheep — for any wool",
        ],
        "context": "Ricardo's 1817 example: even if one nation is more productive in everything, both gain from specialization based on comparative advantage. This is why free trade enriches all parties — the modern world is built on it.",
    },
    {
        "tier": 1,
        "question": "Anna is fastest at dishes AND homework help. Brother is slowest at both. Yet Anna does dishes; brother helps homework. Why?",
        "answer": "Anna's relative loss — is smaller at dishes",
        "choices": [
            "Anna's relative loss — is smaller at dishes",
            "Brothers must do — all the household tasks",
            "Anna refuses — to help in any way at all",
            "Family rules state — only girls clean dishes",
        ],
        "context": "Comparative advantage at the family level: even when one person is best at every task, dividing labor lets the household produce more total work. The cost (opportunity cost) of having Anna do everything is the unmet other needs.",
    },
    {
        "tier": 1,
        "question": "Two friends paint a fence. One's fast at the top; the other's fast at the bottom. Splitting zones works. Why?",
        "answer": "Specialization — each does what they do best",
        "choices": [
            "Specialization — each does what they do best",
            "Paint dries faster — at different speeds",
            "Top halves cost — more than bottom halves",
            "Friends always — agree on splitting chores",
        ],
        "context": "Specialization based on relative skill maximizes output. Adam Smith's pin factory (1776) showed the same principle: when workers specialize in one step, total pin production multiplies. The modern world's wealth is built on this.",
    },

    # --- prices as signals (3)
    {
        "tier": 1,
        "question": "Lemonade is 50 cents on hot days, $2 on cold days. The price tells lemonade makers what?",
        "answer": "Make more on hot days — more demand",
        "choices": [
            "Make more on hot days — more demand",
            "Cold days are easier — to make lemonade",
            "Hot days have — sneaky tax breaks",
            "Lemonade tastes — like winter",
        ],
        "context": "Prices are signals. A high price tells sellers 'more is needed here'; a low price tells them 'you've supplied enough.' Hayek's 1945 'Use of Knowledge in Society': the price system is a marvel of information coordination that no central planner can replicate.",
    },
    {
        "tier": 1,
        "question": "A new video game sells out the first day at $60. The price doesn't change. What information is the price missing?",
        "answer": "How many people wanted it — at that price",
        "choices": [
            "How many people wanted it — at that price",
            "Whether the game — is fun to play",
            "Where the players — live in town",
            "What time the store — opens daily",
        ],
        "context": "When prices don't adjust to scarcity, the information signal breaks. Stores can't tell how strongly customers wanted the game vs how many they sold. Free-floating prices encode information; fixed prices destroy it.",
    },
    {
        "tier": 1,
        "question": "After a hurricane, ice costs $20 a bag in town. Critics call it greedy. What useful work does the high price do?",
        "answer": "Calls truckers to bring more — and rations supply",
        "choices": [
            "Calls truckers to bring more — and rations supply",
            "Punishes families — for needing ice in storms",
            "Helps grocery stores — afford big yachts",
            "Encourages ice — to melt much faster",
        ],
        "context": "Price spikes after disasters look unfair but do crucial work. They (a) signal suppliers to bring more, (b) ration limited current supply to those who need it most. Anti-gouging laws prevent both signals and produce worse shortages.",
    },

    # --- profit and loss + spontaneous order (4)
    {
        "tier": 1,
        "question": "Sam opens a lemonade stand. He makes $20 in lemonade but spends $25 on lemons and sugar. What did he experience?",
        "answer": "A loss — costs higher than revenue",
        "choices": [
            "A loss — costs higher than revenue",
            "A profit — money came in",
            "A draw — break-even",
            "A bonus — extra money",
        ],
        "context": "Profit and loss tell entrepreneurs whether they're creating value. A loss means resources are being consumed faster than value is produced. Sam should change something (lower costs, raise price, find more customers) or close the stand. Loss is information.",
    },
    {
        "tier": 1,
        "question": "Lin's stand makes $100 in lemonade and costs $30 to run. She earns $70 profit. What did her profit prove?",
        "answer": "She created value — for her customers",
        "choices": [
            "She created value — for her customers",
            "She tricked her customers — out of money",
            "She got lucky — and stole the profit",
            "She makes lemons — disappear by magic",
        ],
        "context": "Profit means voluntary customers paid Lin more than the cost of her inputs. They valued the lemonade more than the money they gave her; she valued the money more than her costs. Trade is positive-sum. Profit is the signal of value creation.",
    },
    {
        "tier": 1,
        "question": "Kids cut across the park grass instead of the long path. A dirt path appears. Nobody designed it. What is this?",
        "answer": "Spontaneous order — order without a planner",
        "choices": [
            "Spontaneous order — order without a planner",
            "Vandalism — fixed by park groundskeepers",
            "An accident — that should be erased fast",
            "A government plan — done in deep secret",
        ],
        "context": "Spontaneous order (Hayek's term) is the central insight of Austrian economics. Complex order emerges from individual decisions without central planning. Languages, markets, common law, sidewalks across grass — all order without a designer.",
    },
    {
        "tier": 1,
        "question": "Nobody plans the cafeteria seating. Jocks form one table, artists another. What idea does this show?",
        "answer": "Spontaneous order — patterns without rules",
        "choices": [
            "Spontaneous order — patterns without rules",
            "Government planning — at every table",
            "Random chaos — with no real shape at all",
            "A teacher chose — every cafeteria group",
        ],
        "context": "Spontaneous order applies far beyond markets. Friend groups form, languages evolve, traffic flows — all without central direction. Hayek's key insight: complex social patterns are products of human action but not human design.",
    },

    # --- rent control + min wage kid-version (3)
    {
        "tier": 1,
        "question": "Cousin Joe can't find a city apartment — all taken. The city caps rents at $500. What did the law create?",
        "answer": "A shortage — landlords stopped building new homes",
        "choices": [
            "A shortage — landlords stopped building new homes",
            "Plenty of homes — at very low rental prices",
            "Tall buildings — popping up daily everywhere",
            "Bigger apartments — for the same monthly price",
        ],
        "context": "Rent control is the textbook case of price ceilings producing shortages. NYC has had rent control since WWII; the result is the country's worst housing shortage. Economists across schools (Friedman, Sowell, even Krugman, even Stiglitz) warn against it.",
    },
    {
        "tier": 1,
        "question": "The town raises the minimum wage from $10 to $15 to help workers. The diner's owner cuts hours from 30 a week to 20. Why?",
        "answer": "He can't afford full hours — at the higher wage",
        "choices": [
            "He can't afford full hours — at the higher wage",
            "Workers wanted fewer hours — for free",
            "The town required — fewer hours",
            "Workers got bored — and quit early",
        ],
        "context": "Minimum-wage hikes don't change what employers can afford. Common responses: fewer hours, fewer hires, automation, exit from business, higher prices. The benefit (higher hourly wage) is visible; the costs (lost hours, lost jobs) are spread thin. Bastiat's seen-and-unseen.",
    },
    {
        "tier": 1,
        "question": "When a city forces ice cream shops to pay workers $20/hour, the price of a cone goes from $3 to $5. Who really paid the higher wage?",
        "answer": "Customers — through higher cone prices",
        "choices": [
            "Customers — through higher cone prices",
            "The shop owner — out of his own pocket",
            "The federal government — paid the rest",
            "Cows — by giving more milk for free",
        ],
        "context": "Wage hikes are often passed through to prices. The visible benefit (higher hourly wage) is paid by customers (higher prices) and other workers (fewer hours, fewer jobs). The mandate doesn't conjure resources — it just shifts who pays.",
    },

    # --- 5 more P5: subsidy / sunk cost / broken window / division of labor / specialization
    {
        "tier": 1,
        "question": "The town pays $100 per fire-truck call. Suddenly people call for stuck cats and burnt toast. What happened?",
        "answer": "Subsidies — create more of what's paid for",
        "choices": [
            "Subsidies — create more of what's paid for",
            "Cats got dumber — about climbing trees",
            "Toast got worse — across the whole town",
            "Firefighters slept — through fire alarms",
        ],
        "context": "Subsidize a thing, get more of it. This basic insight applies to housing subsidies (more demand for housing), college subsidies (more demand for college), healthcare subsidies (more demand for care). Prices reflect cost; subsidies hide it.",
    },
    {
        "tier": 1,
        "question": "Sara already paid $20 for a movie ticket. The movie turns out boring. Should she stay to 'get her money's worth'?",
        "answer": "No — the $20 is spent either way",
        "choices": [
            "No — the $20 is spent either way",
            "Yes — staying earns the dollars back",
            "Yes — leaving wastes the ticket gold",
            "No — they refund unhappy customers",
        ],
        "context": "Sunk cost fallacy: money already spent cannot be recovered by enduring more bad outcomes. Sara's decision now is between (a) sitting through a boring movie, or (b) doing something better. The $20 is gone either way.",
    },
    {
        "tier": 1,
        "question": "A vandal breaks a shop window. Townsfolk say: 'Now the shopkeeper pays the glazier — that helps the economy!' What's missing?",
        "answer": "The shoes the shopkeeper — won't buy now",
        "choices": [
            "The shoes the shopkeeper — won't buy now",
            "The vandal's fine — paid to the city",
            "Glass is recycled — into new bottles",
            "The window was — about to break anyway",
        ],
        "context": "Bastiat's broken-window fallacy (1850): the visible benefit (work for the glazier) ignores the invisible loss (everything the shopkeeper would have bought instead). Destruction creates no net wealth — it just shifts spending.",
    },
    {
        "tier": 1,
        "question": "In a pin factory, one worker makes 20 pins a day alone. Ten workers, each doing one step, make 48,000 pins. Why?",
        "answer": "Division of labor — specializing multiplies output",
        "choices": [
            "Division of labor — specializing multiplies output",
            "Pins get faster — after the first thousand",
            "Workers chat less — when in small groups",
            "Factories are blessed — by an old saint",
        ],
        "context": "Adam Smith's *Wealth of Nations* (1776) opened with the pin-factory example: division of labor multiplies output enormously. Specialization is the engine of wealth — at every scale, from the household to the global economy.",
    },
    {
        "tier": 1,
        "question": "A neighborhood needs a babysitter, plumber, baker, and music teacher. Why is it better for each person to specialize?",
        "answer": "Each gets good at one thing — all benefit",
        "choices": [
            "Each gets good at one thing — all benefit",
            "Music must be played — only by experts",
            "Babies sit better — for hired help only",
            "Pipes need licenses — granted yearly only",
        ],
        "context": "Specialization based on skill produces more for everyone. Trade lets each person do what they're best at and exchange for the rest. This is the source of nearly all wealth gained since the agricultural revolution.",
    },
]


# =============================================================================
# Combine and validate
# =============================================================================

ALL_QUESTIONS = P3_QUESTIONS + P4_QUESTIONS + P5_QUESTIONS


def main() -> None:
    # Load economics bank
    bank_path = REPO / "data" / "questions" / "economics.json"
    with open(bank_path) as f:
        bank = json.load(f)

    dup_idx, ans_idx = build_bank_indices(bank)

    passes: list[dict] = []
    soft_warns: list[dict] = []
    fails: list[dict] = []

    print(f"Validating {len(ALL_QUESTIONS)} questions...")
    print(f"  P3 Sound Money: {len(P3_QUESTIONS)}")
    print(f"  P4 Central Banking: {len(P4_QUESTIONS)}")
    print(f"  P5 Practical: {len(P5_QUESTIONS)}")
    print()

    for i, q in enumerate(ALL_QUESTIONS):
        # Determine pillar (P3/P4/P5)
        if i < len(P3_QUESTIONS):
            pillar = 3
        elif i < len(P3_QUESTIONS) + len(P4_QUESTIONS):
            pillar = 4
        else:
            pillar = 5

        try:
            result = validate_rewrite(
                "economics", q,
                bank=bank, dup_index=dup_idx, answer_index=ans_idx,
                replace_idx=None,
            )
        except Exception as e:
            fails.append({
                "idx": i, "pillar": pillar, "stem": q.get("question", "")[:60],
                "exception": repr(e),
            })
            continue

        q_with_meta = dict(q)
        q_with_meta["_pillar"] = pillar
        q_with_meta["_verdict"] = result["verdict"]

        if result["verdict"] == "PASS":
            passes.append(q)
        elif result["verdict"] == "SOFT_WARN":
            soft_warns.append({
                "idx": i, "pillar": pillar,
                "stem": q.get("question", "")[:80],
                "warns": result["soft_warns"],
            })
            passes.append(q)  # Soft-warn still passes
        else:
            fails.append({
                "idx": i, "pillar": pillar,
                "stem": q.get("question", "")[:80],
                "hard_fails": result["hard_fails"],
                "soft_warns": result["soft_warns"],
            })

    print(f"PASS:      {len(passes)}")
    print(f"SOFT_WARN: {len(soft_warns)}")
    print(f"FAIL:      {len(fails)}")

    if fails:
        print("\n=== FAILURES ===")
        for f_ in fails:
            print(f"  [{f_['idx']}] P{f_.get('pillar', '?')}: {f_['stem']}")
            for gate, reason in f_.get("hard_fails", []):
                print(f"      FAIL[{gate}]: {reason}")

    if soft_warns:
        print("\n=== SOFT WARNS ===")
        for sw in soft_warns:
            print(f"  [{sw['idx']}] P{sw.get('pillar', '?')}: {sw['stem']}")
            for gate, reason in sw.get("warns", []):
                print(f"      SOFT[{gate}]: {reason}")

    # Save passes
    out_path = REPO / "_gen_economics_t1_p345.json"
    by_pillar = {3: 0, 4: 0, 5: 0}
    for q in passes:
        # Recompute pillar
        idx_global = ALL_QUESTIONS.index(q)
        if idx_global < len(P3_QUESTIONS):
            by_pillar[3] += 1
        elif idx_global < len(P3_QUESTIONS) + len(P4_QUESTIONS):
            by_pillar[4] += 1
        else:
            by_pillar[5] += 1

    out = {
        "tier": 1,
        "summary": {
            "questions_generated": len(passes),
            "by_pillar": {str(k): v for k, v in by_pillar.items()},
            "passes": len(passes) - len(soft_warns),
            "soft_warns": len(soft_warns),
            "fails": len(fails),
        },
        "questions": passes,
    }
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved {len(passes)} questions to {out_path}")


if __name__ == "__main__":
    main()
