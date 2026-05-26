"""Economics bank voice anchors (30 exemplars).

These 30 questions are the Bastiat Pattern made concrete. Six per tier:

  P1 Austrian Foundations
  P2 Bitcoin
  P3 Sound Money + Hyperinflation
  P4 Central Banking + Keynes/MMT Critique
  P5 Practical Economics
  SIG Signature wonder

See `proposals/v2_audit/ECONOMICS_FRAMEWORK.md` + `_TEMPLATES.md`.
"""
from __future__ import annotations

EXEMPLARS: list[dict] = [
    # =========================================================================
    # T1 — grade 5 — crisp moment + named figure + the wonder (cap 280)
    # =========================================================================

    # T1-P1 Austrian — Bastiat broken window primer
    {
        "tier": 1,
        "question": "A kid breaks a bakery window. 'Now the baker pays the glazier, everyone wins!' What did the neighbor miss?",
        "answer": "What the baker would have spent on shoes",
        "choices": [
            "What the baker would have spent on shoes",
            "Nothing, broken windows help everyone",
            "The glazier was the kid's parent",
            "The kid was punished, so no one wins",
        ],
        "context": "Frederic Bastiat's broken-window fallacy (1850) is the foundational lesson of folk economics. The seen benefit (glazier's work) is real, but the unseen cost (everything else the baker would have bought) is larger.",
    },

    # T1-P2 Bitcoin — Halloween 2008 primer
    {
        "tier": 1,
        "question": "On Halloween 2008, an anonymous person named Satoshi Nakamoto posted a nine-page paper online. What had he invented?",
        "answer": "Bitcoin, digital money needing no central issuer",
        "choices": [
            "Bitcoin, digital money needing no central issuer",
            "A new credit card system for online stores",
            "An online video game called Halloween Coin",
            "A spreadsheet program for tracking candy stash",
        ],
        "context": "Satoshi Nakamoto's white paper appeared October 31, 2008, on the metzdowd.com cryptography list. The Genesis block was mined January 3, 2009. The identity of Satoshi remains unknown.",
    },

    # T1-P3 Sound money — gold coin in attic
    {
        "tier": 1,
        "question": "An old gold coin still buys about the same food today as 100 years ago. A US dollar from 100 years ago buys about 3 cents' worth. Why?",
        "answer": "Gold can't be printed, dollars can",
        "choices": [
            "Gold can't be printed, dollars can",
            "Gold is heavier than paper, so worth more",
            "Old dollars were declared illegal in 1971",
            "Antique coins lose value the older they get",
        ],
        "context": "Sound money holds value because its supply can't be inflated. Fiat currencies dilute over time as governments expand the money supply, transferring wealth from savers to debtors.",
    },

    # T1-P4 Central banking — Nixon Sunday-night
    {
        "tier": 1,
        "question": "On August 15, 1971, Nixon went on TV Sunday night and said dollars no longer traded for gold. Why Sunday?",
        "answer": "So markets couldn't react until Monday",
        "choices": [
            "So markets couldn't react until Monday",
            "Gold was being mined on weekends in 1971",
            "Because Nixon liked Sunday-night football",
            "Congress only voted on Sundays in the 1970s",
        ],
        "context": "Nixon's August 15, 1971 announcement closed the gold window — the last formal link between the US dollar and gold. He chose Sunday night so currency markets couldn't react before the policy was in force.",
    },

    # T1-P5 Practical — lemonade stand
    {
        "tier": 1,
        "question": "A town law raises lemonade to $2 to help kids earn more. Customers stop buying. What did the law do?",
        "answer": "Set the price too high, so sales dropped",
        "choices": [
            "Set the price too high, so sales dropped",
            "Made the kids automatically rich and happy",
            "Made lemons grow faster on the trees there",
            "Forced all kids to switch to selling iced tea",
        ],
        "context": "Price controls don't change supply and demand. A price floor above the market price creates surpluses (unsold inventory); a price ceiling below the market price creates shortages.",
    },

    # T1-SIG signature — Hayek knowledge problem primer
    {
        "tier": 1,
        "question": "Hayek's Nobel-winning idea: no one knows all prices and needs of millions at once. What solves this naturally?",
        "answer": "The price system, signaling what's scarce",
        "choices": [
            "The price system, signaling what's scarce",
            "A large computer kept running in DC daily",
            "A team of experts who vote on prices weekly",
            "Three big companies setting every price",
        ],
        "context": "Hayek's 1945 paper 'The Use of Knowledge in Society' is one of the most-cited essays in economics. Prices encode dispersed, tacit, local information no central planner can collect.",
    },

    # =========================================================================
    # T2 — grade 6 — one scene + named figure + action/argument (cap 480)
    # =========================================================================

    # T2-P1 Austrian — Hayek vs Keynes 1931
    {
        "tier": 2,
        "question": "In 1931 the London School of Economics invited Friedrich Hayek to give four lectures challenging John Maynard Keynes at Cambridge. What did Hayek's lectures argue Keynes missed about money?",
        "answer": "Money flows through specific stages of production, not as one aggregate",
        "choices": [
            "Money flows through specific stages of production, not as one aggregate",
            "Money is purely psychological and resists any kind of economic analysis",
            "Money is mostly irrelevant; only government fiscal policy actually matters",
            "Money should be replaced by direct barter between individual citizens",
        ],
        "context": "Hayek's LSE lectures became 'Prices and Production' (1931). The Austrian-Keynesian debate at LSE that year is one of the most-cited intellectual confrontations in 20th-century economics.",
    },

    # T2-P2 Bitcoin — Genesis block Times headline
    {
        "tier": 2,
        "question": "Bitcoin's first block, mined January 3, 2009, contained a hidden message from Satoshi: 'The Times 03/Jan/2009 Chancellor on brink of second bailout for banks.' Why include that headline?",
        "answer": "To timestamp the chain AND comment on the bailouts Bitcoin was made unnecessary by",
        "choices": [
            "To timestamp the chain AND comment on the bailouts Bitcoin was made unnecessary by",
            "Because the London Times paid Satoshi a small advertising fee for the message",
            "Because the Chancellor of the Exchequer was personally Satoshi Nakamoto's cousin",
            "Because Bitcoin's protocol requires every block to cite a newspaper headline",
        ],
        "context": "The Genesis block coinbase contains the *Times* (UK) headline from January 3, 2009, about UK bank bailouts. The choice anchors Bitcoin to its founding moment AND signals its purpose.",
    },

    # T2-P3 Sound money — Weimar hyperinflation
    {
        "tier": 2,
        "question": "In 1923 Weimar Germany, a loaf of bread cost about 200 billion marks. People burned mark notes for heat because banknotes were cheaper than firewood. What had Germany been doing?",
        "answer": "Printing money for reparations faster than goods were produced",
        "choices": [
            "Printing money for reparations faster than goods were produced",
            "Building too many factories that produced too much bread",
            "Restricting bread supply by law to make goods expensive",
            "Banning the use of paper money for any food transactions",
        ],
        "context": "Weimar Germany's 1921-1923 hyperinflation peaked at an estimated 29,500% monthly inflation. The political instability that followed was a precondition for what came next in German politics.",
    },

    # T2-P4 Central banking — public choice intro
    {
        "tier": 2,
        "question": "James Buchanan and Gordon Tullock published 'The Calculus of Consent' in 1962. Their core idea: politicians and bureaucrats pursue their own interests, not 'the public good.' What is this field called?",
        "answer": "Public choice theory, economics applied to politics",
        "choices": [
            "Public choice theory, economics applied to politics",
            "Behavioral economics, applied to consumer retail decisions",
            "Welfare economics, the study of aggregate happiness",
            "Monetary economics, the study of central-bank decisions",
        ],
        "context": "Buchanan won the 1986 Nobel for this work. The field collapses the 'market failure → benevolent government fixes it' framing by treating government actors as self-interested too.",
    },

    # T2-P5 Practical — comparative advantage Ricardo
    {
        "tier": 2,
        "question": "In 1817 David Ricardo published a thought experiment about Portugal and England making wine and cloth. Even when Portugal could produce both more efficiently, both countries gain by specializing. What did Ricardo establish?",
        "answer": "Comparative advantage, trade helps both even when one is better at all things",
        "choices": [
            "Comparative advantage, trade helps both even when one is better at all things",
            "Absolute advantage, trade only helps countries that produce cheapest",
            "Mercantilism, the country with most gold reserves always wins out",
            "Tariff doctrine, raising trade barriers helps the home country prosper",
        ],
        "context": "Ricardo's 'On the Principles of Political Economy and Taxation' (1817) introduced comparative advantage. The insight: opportunity cost matters, not absolute productivity.",
    },

    # T2-SIG signature — Mises 1920 calculation problem
    {
        "tier": 2,
        "question": "In 1920 Ludwig von Mises argued socialism wasn't merely inefficient but IMPOSSIBLE. Without private ownership of capital goods, there are no market prices. What did Mises say socialist planners couldn't do?",
        "answer": "Allocate resources rationally, since no prices means no economic calculation",
        "choices": [
            "Allocate resources rationally, since no prices means no economic calculation",
            "Pay workers their fair wages, because socialism requires complex math",
            "Trade with capitalist nations, since socialist currency wasn't accepted",
            "Run elections successfully, because socialist parties had low turnout",
        ],
        "context": "Mises's 1920 'Economic Calculation in the Socialist Commonwealth' is one of the most consequential economic essays. The historical record of 20th-century communism vindicated his prediction.",
    },

    # =========================================================================
    # T3 — grade 7 — scene + stakes + economic mechanism or moment (cap 680)
    # =========================================================================

    # T3-P1 Austrian — ABCT cycle
    {
        "tier": 3,
        "question": "Austrian Business Cycle Theory predicts that artificially low interest rates set by a central bank cause businesses to invest in projects that look profitable at the low rate but lose money when rates rise. The Fed held its rate at 1% from June 2003 to June 2004. What boom does ABCT cleanest explain?",
        "answer": "The 2008 US housing bubble, sparked by ultra-low Fed rates, ending in the worst crisis since the 1930s",
        "choices": [
            "The 2008 US housing bubble, sparked by ultra-low Fed rates, ending in the worst crisis since the 1930s",
            "The 1929 stock market crash, which Austrians believe was caused entirely by US tariff policy that year",
            "The 1973 oil crisis, resulting from OPEC supply restrictions with no monetary cause whatsoever to it",
            "The 2020 pandemic recession, driven solely by viral biology rather than monetary expansion in 2019",
        ],
        "context": "ABCT was first stated by Mises (1912 *Theory of Money and Credit*) and refined by Hayek (*Prices and Production*, 1931). The theory predicted the 2008 GFC; the mainstream profession did not.",
    },

    # T3-P2 Bitcoin — halving + 21M cap
    {
        "tier": 3,
        "question": "Bitcoin's block subsidy halves about every 4 years (every 210,000 blocks). At Genesis 2009, miners got 50 BTC per block; in 2024 they got 3.125. Around year 2140 the last satoshi is mined. What does this schedule guarantee?",
        "answer": "A hard supply cap of about 21 million bitcoin that no human can change without network consensus",
        "choices": [
            "A hard supply cap of about 21 million bitcoin that no human can change without network consensus",
            "A continuously increasing supply, calibrated by the Federal Reserve to match inflation targets",
            "A floating supply, set each year by the Bitcoin Foundation board through governance votes",
            "A diminishing supply, with bitcoin actively destroyed by the protocol after seven years",
        ],
        "context": "Bitcoin halvings: 2012 (50→25), 2016 (25→12.5), 2020 (12.5→6.25), 2024 (6.25→3.125). Supply is above 19.5M of the ~21M cap as of 2024.",
    },

    # T3-P3 Sound money — Cantillon effect
    {
        "tier": 3,
        "question": "18th-century banker Richard Cantillon observed that newly-printed money doesn't lift all prices equally. First recipients buy at OLD prices; by the time money ripples out, prices have risen. Why does this matter today?",
        "answer": "Monetary expansion transfers wealth from late recipients (savers, wages) to early recipients (banks, contractors, asset holders)",
        "choices": [
            "Monetary expansion transfers wealth from late recipients (savers, wages) to early recipients (banks, contractors, asset holders)",
            "Monetary expansion is neutral, all prices rise immediately at exactly the same rate everywhere in the economy at once",
            "Monetary expansion lifts wages first, since workers always get the new money before businesses can raise their prices",
            "Monetary expansion always reduces inequality by helping the poor before reaching the wealthy in any modern economy",
        ],
        "context": "Cantillon's *Essai sur la Nature du Commerce en Général* (~1730, published 1755 posthumously) anticipated much of modern monetary economics. The Cantillon effect explains why monetary inflation is regressive even when CPI looks modest.",
    },

    # T3-P4 Central banking — Friedman + Schwartz
    {
        "tier": 3,
        "question": "Milton Friedman and Anna Schwartz published 'A Monetary History of the United States 1867-1960' in 1963. Their argument: the Federal Reserve didn't just fail to stop the Great Depression, the Fed CAUSED it by allowing the money supply to contract sharply between 1929 and 1933. By how much did the money supply fall?",
        "answer": "About one-third (33%) over those four years, the largest monetary contraction in US history",
        "choices": [
            "About one-third (33%) over those four years, the largest monetary contraction in US history",
            "About one percent (1%) over those four years, a normal seasonal variation in money supply",
            "About a hundredth of one percent over those years, well within historical statistical error",
            "About one half of one percent over those years, less than the supply grew in 1929 alone",
        ],
        "context": "Friedman + Schwartz changed how the Great Depression is taught. The institution founded in 1913 to prevent banking panics presided over the worst banking collapse and economic catastrophe in US history.",
    },

    # T3-P5 Practical — minimum wage seen/unseen
    {
        "tier": 3,
        "question": "A minimum-wage law raises the hourly minimum from $10 to $15. Workers earning $10 who keep their jobs benefit visibly. What does Bastiat's method tell us to look for next?",
        "answer": "The workers whose hours got cut, who got laid off, or who couldn't get hired at the higher minimum",
        "choices": [
            "The workers whose hours got cut, who got laid off, or who couldn't get hired at the higher minimum",
            "The workers who started celebrating immediately when the law was signed since they kept their jobs",
            "The federal regulators enforcing the law, since their pay also rises with the new legal minimum wage",
            "The taxes on tips that workers must now pay since their hourly wage just rose by 50 percent quickly",
        ],
        "context": "Minimum-wage debates often focus only on workers who keep their jobs at the higher wage. The 'unseen' workers — those priced out of the market, those who can't get a first job, those whose hours are cut — are the harder-to-count loss.",
    },

    # T3-SIG signature — FTX collapse Nov 2022
    {
        "tier": 3,
        "question": "November 8, 2022: FTX (then the second-largest crypto exchange) collapsed after founder Sam Bankman-Fried moved customer funds to his trading firm Alameda. About $8B went missing. SBF got 25 years in 2024. What does this illustrate about Bitcoin's design?",
        "answer": "Not your keys, not your coins, exchanges require trust Bitcoin was designed to eliminate",
        "choices": [
            "Not your keys, not your coins, exchanges require trust Bitcoin was designed to eliminate",
            "All crypto is fraudulent, FTX proved no digital asset can ever be trusted at all",
            "FTX was run correctly, the missing funds were caused by media-driven panic selling",
            "Centralized exchanges always succeed, short-term volatility is the only real risk",
        ],
        "context": "FTX's collapse exposed billions in customer fund misappropriation. SBF was a major Democratic donor and prominent in 'effective altruism' fundraising. The case is the canonical example of exchange-custody risk that Bitcoin's self-custody model eliminates.",
    },

    # =========================================================================
    # T4 — grade 8 — setup + tension + named details + payoff (cap 900)
    # =========================================================================

    # T4-P1 Austrian — Mises NYU unpaid
    {
        "tier": 4,
        "question": "Ludwig von Mises left Vienna in 1934 ahead of the Nazi threat, taught briefly in Geneva, then came to the United States in 1940. From 1945 to 1969 he held an unpaid visiting position at NYU. Murray Rothbard attended his seminars there. Mises died October 10, 1973, at age 92. Why did the most influential Austrian economist of the 20th century never hold a paid US academic position?",
        "answer": "His uncompromising free-market views were unacceptable to a postwar US academy dominated by Keynesian and mathematical economics",
        "choices": [
            "His uncompromising free-market views were unacceptable to a postwar US academy dominated by Keynesian and mathematical economics",
            "Mises preferred unpaid positions for tax reasons since postwar income above $5,000 was taxed at over 90 percent in the USA",
            "NYU was the only US university Mises would teach at because of his personal friendship with the university president of the time",
            "Mises was independently wealthy from family banking in Austria and never needed paid academic employment in his entire lifetime",
        ],
        "context": "Hayek faced similar professional headwinds in the postwar Anglosphere. The Austrian school survived the mid-century via private institutes (Mises Institute founded 1982 at Auburn) and a handful of independent scholars. The contemporary revival owes much to that infrastructure.",
    },

    # T4-P2 Bitcoin — difficulty adjustment + China ban
    {
        "tier": 4,
        "question": "Bitcoin's difficulty adjusts every 2016 blocks (~2 weeks) to target 10-minute blocks. May 2021 China banned Bitcoin mining and ~50% of global hashrate went offline. Blocks slowed; the next adjustment made the puzzle easier; miners outside China filled the gap. Why is this mechanism essential?",
        "answer": "It guarantees the issuance schedule (21M cap, halvings every 210K blocks) regardless of hashrate; supply is set by code, not humans",
        "choices": [
            "It guarantees the issuance schedule (21M cap, halvings every 210K blocks) regardless of hashrate; supply is set by code, not humans",
            "It lets the Bitcoin Foundation manually adjust rewards each quarter based on global energy prices and political conditions abroad",
            "It enables core developers to slow or accelerate Bitcoin's inflation rate based on their economic forecasts for the coming year",
            "It permits major exchanges like Coinbase to vote on whether the next block subsidy should be larger or smaller in real-time response",
        ],
        "context": "The May 2021 China mining ban was the largest stress test of Bitcoin's hashrate distribution. Hashrate recovered to pre-ban levels within months as mining migrated to the US, Kazakhstan, Russia, and elsewhere. The difficulty mechanism functioned exactly as designed.",
    },

    # T4-P3 Sound money — Zimbabwe 100 trillion note
    {
        "tier": 4,
        "question": "Zimbabwe's central bank issued a 100-TRILLION-dollar note in January 2009. By the time the note was printed, it bought about a single loaf of bread. The currency was abandoned in April 2009; Zimbabweans began using US dollars and South African rand. What does this illustrate about fiat money?",
        "answer": "A government that can print money will eventually print too much when politically pressured, fiat currencies die historically without exception",
        "choices": [
            "A government that can print money will eventually print too much when politically pressured, fiat currencies die historically without exception",
            "Zimbabwe's case was unique to its 2008 climate conditions and crop failures, and has no broader monetary implications for any other country",
            "Zimbabwe demonstrated that hyperinflation is impossible in the modern monetary era since central banks can simply revalue currencies overnight",
            "Zimbabwe's 100-trillion note was the largest stable currency unit ever issued and is still widely used across the country today regularly",
        ],
        "context": "Zimbabwe's hyperinflation peaked at an estimated 89.7 sextillion percent month-on-month in November 2008. Other major hyperinflations: Weimar 1923, Hungarian pengo 1946 (largest in history), Yugoslav dinar 1993-94, Venezuela 2017+, Argentina recurrent.",
    },

    # T4-P4 Central banking — Jekyll Island 1910
    {
        "tier": 4,
        "question": "In November 1910, six men boarded a private rail car at Hoboken, New Jersey, bound for Jekyll Island off Georgia. The participants (Senator Nelson Aldrich, JP Morgan banker Henry Davison, Paul Warburg of Kuhn Loeb, Frank Vanderlip of National City Bank, A. Piatt Andrew of the Treasury, plus Benjamin Strong) used only first names to keep the meeting secret from porters and reporters. What did they draft?",
        "answer": "The Aldrich Plan, the blueprint that became the Federal Reserve Act of 1913",
        "choices": [
            "The Aldrich Plan, the blueprint that became the Federal Reserve Act of 1913",
            "The Glass-Steagall Act, separating commercial and investment banking by law in the year 1933 nationwide",
            "The Bretton Woods Agreement, fixing exchange rates to the dollar starting 1944 after the world war ended",
            "The Sherman Antitrust Act, breaking up monopolies passed by Congress in the year 1890 during Harrison's term",
        ],
        "context": "Jekyll Island 1910 is the founding moment of the modern US central-banking arrangement. Conspirators framed the Fed as a public agency despite its private-bank design. G. Edward Griffin's *The Creature from Jekyll Island* (1994) is the canonical popular account.",
    },

    # T4-P5 Practical — rent control unseen consequences
    {
        "tier": 4,
        "question": "NYC has had some form of rent control since WWII. Economists across schools (Friedman, Sowell, Krugman, even Stiglitz) warned that strict rent controls reduce housing supply. Yet rent control stays popular because the BENEFIT (lower rent for current tenants) is visible while the COSTS spread thin and delayed. What are the costs?",
        "answer": "Reduced new construction, lower maintenance on controlled units, tenant lock-in reducing labor mobility, worse market next year",
        "choices": [
            "Reduced new construction, lower maintenance on controlled units, tenant lock-in reducing labor mobility, worse market next year",
            "There are no real costs since rent control is purely a redistribution from landlords to tenants with no broader market effects",
            "Main cost is more paperwork tracking tenants, slightly reducing overall rental supply by a small percentage each year",
            "Cost is the federal government paying landlords directly for the difference between controlled and market rent monthly",
        ],
        "context": "The economics of rent control is one of the clearest cases where the Bastiat method matters. Current tenants benefit visibly; future tenants, future construction, and labor markets pay the unseen cost.",
    },

    # T4-SIG signature — Black Book communism
    {
        "tier": 4,
        "question": "The Black Book of Communism (1997) estimated communist regimes killed about 65-100 million people in the 20th century: USSR ~20M (gulag, Holodomor), China ~65M (Great Leap famine, Cultural Revolution), Cambodia ~2M (Khmer Rouge), plus North Korea, Vietnam, Cuba, Ethiopia. Mises had predicted this in 1920. What was his explanation?",
        "answer": "Without private capital, no prices form; without prices, no rational allocation; shortages result, enforced by political violence",
        "choices": [
            "Without private capital, no prices form; without prices, no rational allocation; shortages result, enforced by political violence",
            "Communist regimes were always run by mentally unstable individuals; the high death toll resulted entirely from leader personality defects",
            "Communist regimes pursued ethnic policies as their primary goal; the economic system was secondary to their racial-political objectives",
            "Communist regimes failed because citizens refused to work hard enough; the bureaucracies functioned correctly given the labor inputs",
        ],
        "context": "Mises 1920 'Economic Calculation in the Socialist Commonwealth' predicted the 20th century before it happened. The Black Book of Communism (Courtois et al. 1997) tallies the human cost. Cross-link to history bank.",
    },

    # =========================================================================
    # T5 — grade 9-10 HARD CEILING (cap 1100)
    # =========================================================================

    # T5-P1 Austrian — Hayek 1945 knowledge problem deep
    {
        "tier": 5,
        "question": "Hayek's 1945 American Economic Review paper 'The Use of Knowledge in Society' is among the most-cited in economics. Its argument: the problem isn't how to allocate given resources, it's how to use knowledge no individual possesses. Prices encode dispersed, tacit, local information no planner can collect. What political conclusion follows?",
        "answer": "Central planning fails not because planners aren't smart enough, but because the information they'd need doesn't exist centralizably; the failure is epistemic",
        "choices": [
            "Central planning fails not because planners aren't smart enough, but because the information they'd need doesn't exist centralizably; the failure is epistemic",
            "Central planning is possible in principle but requires more powerful computers; modern AI could in theory implement Soviet-style planning if given enough hardware",
            "Hayek argued markets fail in coordination problems and government intervention is required to solve information-aggregation difficulties markets can't handle alone",
            "Hayek's paper was retracted in the 1960s after Soviet economists demonstrated empirically that central planning matched market output for industrial production stats",
        ],
        "context": "Hayek's 1945 essay is the canonical statement of the knowledge problem. Mises had made the related calculation argument in 1920. Together these refute central planning as an epistemological matter, not just a practical one.",
    },

    # T5-P2 Bitcoin — cypherpunk lineage to Bitcoin
    {
        "tier": 5,
        "question": "Bitcoin solves a problem cypherpunks worked on for decades. Chaum's DigiCash (1989) failed needing a central issuer. Back's Hashcash (1997) introduced proof-of-work. Dai's b-money (1998) and Szabo's bit gold (2005) couldn't solve double-spend. Satoshi 2008 combined proof-of-work + shared ledger + difficulty adjustment. Why is the Genesis block's 'Chancellor on brink' headline significant?",
        "answer": "It anchors Bitcoin to the bank-bailout moment that proved the case for credibly-neutral money; the timestamp and the editorial commentary are inseparable",
        "choices": [
            "It anchors Bitcoin to the bank-bailout moment that proved the case for credibly-neutral money; the timestamp and the editorial commentary are inseparable",
            "It allowed Satoshi to claim copyright on Bitcoin since the headline appeared in a public newspaper he had licensed for blockchain use before launch",
            "It established that Bitcoin was created in the UK rather than elsewhere since The Times is a British newspaper and cited a UK chancellor specifically",
            "It demonstrated the protocol's ability to store news headlines as a primary use case, with the financial functions being a secondary feature",
        ],
        "context": "The cypherpunk mailing list (1992-2010s) and predecessors developed many cryptographic primitives Bitcoin uses. The Genesis block timestamp is unforgeable because the embedded headline anchors the chain to a specific date in published news.",
    },

    # T5-P3 Sound money — sound-money arc + Bitcoin
    {
        "tier": 5,
        "question": "From Lydian electrum ~600 BC, money was historically gold or silver, commodity-backed for ~2,600 years. The classical gold standard (~1870-1914) was the high-water mark for international sound money. WWI broke it; Bretton Woods (1944-71) reattached the dollar to gold. Nixon closed the gold window Aug 15, 1971. Since then, no major currency is backed by anything but trust. What does Bitcoin (2009-) represent?",
        "answer": "The first credibly-neutral, programmatically-scarce, no-issuer money, sound money returned in digital form with mathematical scarcity",
        "choices": [
            "The first credibly-neutral, programmatically-scarce, no-issuer money, sound money returned in digital form with mathematical scarcity",
            "A short-lived speculative bubble ending in 2014 with the Mt. Gox collapse, with no lasting historical significance for the sound-money debate",
            "An updated version of the gold standard requiring governments to vote on the supply curve every four years under G7 treaty arrangements",
            "A central-bank-issued digital currency designed by the Federal Reserve to replace the paper dollar by the year 2030 in coordination with G7 banks",
        ],
        "context": "The arc Lydian → classical gold → Bretton Woods → 1971 Nixon → ~50 years pure fiat → Bitcoin 2009 → present is the long-frame sound-money story. Saifedean Ammous's *The Bitcoin Standard* (2018) and Nik Bhatia's *Layered Money* (2021) are canonical popular references.",
    },

    # T5-P4 Central banking — MMT falsified by 2021-23 inflation
    {
        "tier": 5,
        "question": "Stephanie Kelton's The Deficit Myth (2020) was MMT's most influential statement. Core claim: a government issuing its own currency can't 'run out of money'; deficits are constrained only by inflation. 2021-23 US inflation hit 9.1% (June 2022 peak) after $4-5T pandemic deficit spending. Larry Summers warned Feb 2021 it would cause inflation. He was right. What did 2021-23 demonstrate?",
        "answer": "When MMT's acknowledged constraint (inflation) arrived, it was larger, faster, and more persistent than the framework implied, falsifying its policy implications in real time",
        "choices": [
            "When MMT's acknowledged constraint (inflation) arrived, it was larger, faster, and more persistent than the framework implied, falsifying its policy implications in real time",
            "MMT's central claim was confirmed since inflation was brought back down to 3% by 2023, showing the framework works with proper interest-rate management at the central bank",
            "2021-23 inflation had nothing to do with monetary or fiscal policy; it was caused entirely by supply-chain disruptions from the COVID pandemic with no link to deficits",
            "MMT's central claim was always about wartime economies specifically; peacetime spending falls outside the theory's stated domain so 2021 is irrelevant to it",
        ],
        "context": "Kelton's *Deficit Myth* is honest about the inflation constraint in its formal pages, but the political deployment of MMT systematically downplayed the constraint. The 2021-23 inflation aged the popular MMT case poorly.",
    },

    # T5-P5 Practical — public choice deep + capture
    {
        "tier": 5,
        "question": "Buchanan and Tullock's The Calculus of Consent (1962) applied economic methodology (rational self-interest, marginal analysis) to politics. Conclusion: politicians, bureaucrats, and voters are self-interested, not benevolent guardians. Tullock's later rent-seeking work (1967) quantified the social cost. Buchanan won the 1986 Nobel. Why is this load-bearing for economics?",
        "answer": "Once politics is self-interested, the 'market failure leads to government fix' argument collapses; you must compare imperfect markets to imperfect governments, and the government side often performs worse",
        "choices": [
            "Once politics is self-interested, the 'market failure leads to government fix' argument collapses; you must compare imperfect markets to imperfect governments, and the government side often performs worse",
            "Buchanan and Tullock proved all government intervention is unnecessary because markets always self-correct without delay or external assistance under any conditions",
            "Public choice theory was refuted in the 1990s when Clinton-administration policies showed benevolent government intervention can solve market failures successfully",
            "The theory only applies to authoritarian regimes; democratic governments are exempt because voter accountability disciplines politicians in every electoral cycle",
        ],
        "context": "Public choice theory unifies many strands of the bank's substantive stance. Regulatory capture, rent-seeking, the revolving door, the political incentives of central bankers, all become legible once you stop assuming benevolence on the government side.",
    },

    # T5-SIG signature — Hayek + Mises + the 20th century
    {
        "tier": 5,
        "question": "The 20th century ran a vast natural experiment on Mises's 1920 prediction. USSR (1922-91), Mao's China (1949-76), Khmer Rouge Cambodia (1975-79), North Korea, Cuba, Eastern Europe all attempted central planning. The Black Book of Communism (1997) tallies ~65-100M deaths. Hayek said this would happen in 1944's Road to Serfdom. What did he add to Mises?",
        "answer": "The problem isn't just calculation impossibility; planners must increasingly substitute coercion for the information they can't collect, ending in totalitarian rule",
        "choices": [
            "The problem isn't just calculation impossibility; planners must increasingly substitute coercion for the information they can't collect, ending in totalitarian rule",
            "Hayek agreed calculation was impossible but argued political resolve and organization could overcome the practical obstacles to central planning if planners worked harder",
            "Hayek's argument was about voter turnout and electoral participation rather than economic calculation or central planning in the form Mises had described in 1920",
            "Hayek said central planning succeeds when planners are highly educated; 20th-century failures resulted from insufficient PhD economists in government roles overseeing",
        ],
        "context": "*The Road to Serfdom* (1944) and 'The Use of Knowledge in Society' (1945) were Hayek's twin contributions in two consecutive years. Mises had supplied the economic-calculation argument in 1920; Hayek added the epistemic argument AND the political-philosophy argument tracing central planning's drift toward authoritarian rule.",
    },
]


__all__ = ["EXEMPLARS"]
