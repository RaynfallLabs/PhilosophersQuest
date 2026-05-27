"""Build 50 SUPPLEMENTAL economics questions: Business Structure + Entrepreneurship Metrics.

Tier distribution: T1=4, T2=8, T3=12, T4=14, T5=12.

Topic spine (drawn from docs/quiz/subjects/economics.md §3.5):
  - Sole prop / LLC / S-corp / C-corp = INCENTIVE recognition
  - Limited liability = 19th-c. industrial-capital enabler + moral hazard trade-off
  - Vesting / cliffs / cap tables / SAFE notes
  - Burn rate / runway / CAC / LTV / unit economics / gross margin
  - Real-world arcs: Bezos garage 1994, Airbnb O's 2008, Tesla 2008, Munger invert
  - Y Combinator 2005, Paul Graham default-alive
  - Series A/B/C / dilution / down rounds
  - Power-law return distribution

Voice: Bastiat Pattern + §14 story-in-stem. Every question reveals incentive,
trade-off, or recognition skill. Real names + verified dates.

Length caps (economics): T1<=294, T2<=504, T3<=714, T4<=945, T5<=1155 (grace).
Distractor parity = answer-outlier 1.6x. Em-dash uniform across all 4 choices.

Saves to _gen_economics_supp_finlit_entrepreneurship.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(r"C:\Users\brand\Documents\PhilosophersQuest")
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite


QUESTIONS: list[dict] = []


_ERRORS: list[str] = []


def q(tier: int, question: str, answer: str, d1: str, d2: str, d3: str,
      context: str, strategy: str = "") -> None:
    """Add one question with strict length checks.

    Em-dash uniformity rule: either all 4 choices contain em-dash OR none do.
    Answer-outlier rule: |ans| <= 1.6 * max(|distractors|).
    """
    caps = {1: 294, 2: 504, 3: 714, 4: 945, 5: 1155}
    cap = caps[tier]

    choices = [answer, d1, d2, d3]
    total = len(question) + sum(len(c) for c in choices)
    if total > cap:
        _ERRORS.append(
            f"OVER T{tier} cap={cap} got={total} (excess={total-cap}) [{strategy}]\n"
            f"    q ({len(question)}): {question}\n"
            f"    a ({len(answer)}): {answer}\n"
            f"    d1 ({len(d1)}): {d1}\n"
            f"    d2 ({len(d2)}): {d2}\n"
            f"    d3 ({len(d3)}): {d3}"
        )

    # Em-dash uniformity check
    has_em = ["—" in c for c in choices]
    if not (all(has_em) or not any(has_em)):
        _ERRORS.append(
            f"EM-DASH MIXED T{tier} [{strategy}] has_em={has_em} :: {question[:50]}"
        )

    # Answer-outlier check (1.6x in either direction)
    dist_lens = [len(d1), len(d2), len(d3)]
    max_d = max(dist_lens)
    min_d = max(min(dist_lens), 1)
    a_len = len(answer)
    if a_len > max_d * 1.6:
        _ERRORS.append(
            f"ANS-OUTLIER (long) T{tier} [{strategy}] ans={a_len} max_d={max_d} :: {question[:50]}"
        )
    if a_len * 1.6 < min_d:
        _ERRORS.append(
            f"ANS-OUTLIER (short) T{tier} [{strategy}] ans={a_len} min_d={min_d} :: {question[:50]}"
        )

    QUESTIONS.append({
        "tier": tier,
        "question": question,
        "answer": answer,
        "choices": choices,
        "context": context,
        "_strategy": strategy,
    })


# ==========================================================================
# T1 (4 questions, cap 294) — crisp moment + the wonder
# ==========================================================================

# T1-1 Sole prop vs LLC primer
q(
    tier=1,
    question="Sara mows lawns under her own name. A customer trips and sues. Sara's house is at risk. What business form does she have?",
    answer="A sole proprietorship, no legal shield",
    d1="An LLC, with full legal protection built in",
    d2="A C-corp, common for small lawn businesses",
    d3="An S-corp, automatic for self-employed kids",
    context="A sole proprietorship is the default form when you run a business under your own name. The owner and business are the same legal entity. Personal assets (house, savings) are reachable by business creditors and lawsuits.",
    strategy="sole_prop_liability_intro",
)

# T1-2 LLC primer
q(
    tier=1,
    question="Sara forms an LLC for her lawn business. Now a customer trips and sues. Whose house can the lawsuit reach?",
    answer="Not Sara's, only the business's assets",
    d1="Sara's, the LLC offers no real shield at all",
    d2="The whole town's, since LLCs are public funded",
    d3="The customer's own, by automatic legal rule",
    context="An LLC (Limited Liability Company) creates a legal wall between the owner and the business. Lawsuits against the business reach only business assets, not the owner's personal house or savings. This 19th-century invention enabled industrial capitalism.",
    strategy="llc_shield_intro",
)

# T1-3 Bezos garage 1994
q(
    tier=1,
    question="July 1994: a Wall Street trader quit to sell books online from his garage in Bellevue. He called it Amazon. Who?",
    answer="Jeff Bezos, who started in a rented garage",
    d1="Bill Gates, leaving a Harvard dropout year",
    d2="Steve Jobs, who left Apple that summer",
    d3="Elon Musk, just before founding PayPal",
    context="Bezos founded Amazon July 5, 1994. He famously used a 'regret minimization framework' to decide: at age 80, would he regret not trying? He left a high-paying hedge-fund job for the garage. Amazon's first book sold in April 1995.",
    strategy="bezos_garage_1994",
)

# T1-4 Burn rate intuition
q(
    tier=1,
    question="A startup has $100,000 in the bank and spends $10,000 each month. The founder calls $10,000 the 'burn rate.' What is the runway?",
    answer="Ten months, until the cash runs out",
    d1="Ten years, since money grows in a savings account",
    d2="One hundred months, the bank's balance",
    d3="One month, because rates rise each quarter",
    context="Burn rate is monthly cash spent. Runway = cash on hand divided by burn rate = months until empty. A startup with $100K and $10K/month burn has 10 months of runway. The number tells founders how long they have to either get profitable or raise more money.",
    strategy="burn_runway_intro",
)


# ==========================================================================
# T2 (8 questions, cap 504) — named figure + action/argument
# ==========================================================================

# T2-1 Munger volume joke
q(
    tier=2,
    question="Charlie Munger liked to ridicule bad businesses by joking, 'We lose money on every sale, but we make it up in volume.' What skill does this joke teach?",
    answer="A business with bad unit economics can't be saved by selling more units",
    d1="A business with bad marketing can be saved by hiring better salespeople and managers",
    d2="A business with bad accounting can be saved by switching to fancier tax preparation software",
    d3="A business with bad branding can be saved by spending heavily on a logo redesign campaign",
    context="Charlie Munger (1924-2023) was Warren Buffett's longtime partner at Berkshire Hathaway. His joke about 'making it up in volume' targets the basic unit-economics confusion: if you lose money per transaction, scale multiplies the loss.",
    strategy="munger_volume_joke",
)

# T2-2 Y Combinator 2005 founding
q(
    tier=2,
    question="March 2005, Cambridge: Paul Graham and three co-founders launched a new kind of investor. Same standardized check for every team, 3-month batch, ending in Demo Day. What did they create?",
    answer="Y Combinator, the standardized startup accelerator model",
    d1="A traditional venture capital fund, with custom-negotiated checks for each startup deal",
    d2="A bank loan office, lending money to startups at fixed rates set by federal regulations",
    d3="A government grant program, awarding non-dilutive money to applicants chosen by Congress",
    context="Y Combinator was founded March 2005 by Paul Graham, Jessica Livingston, Robert Morris, and Trevor Blackwell. Its innovation was standardization: same terms, same check size, same 3-month batch. The model compounded across cohorts — each batch shared lessons, alumni networks, and Demo Day audiences. YC funded Airbnb, Dropbox, Stripe, Coinbase, and Reddit.",
    strategy="yc_2005_founding",
)

# T2-3 Airbnb O's pivot
q(
    tier=2,
    question="Autumn 2008: Airbnb was dying. Brian Chesky and Joe Gebbia printed election-themed 'Obama O's' and 'Cap'n McCains' cereal boxes, sold them for $40 each. What did this do?",
    answer="Funded payroll long enough to survive into Y Combinator's batch",
    d1="Earned the founders a federal endorsement for the upcoming presidential election",
    d2="Got Airbnb shut down by trademark lawyers for unauthorized use of the candidates' names",
    d3="Made cereal their main product, which they still sell today at major US grocery stores",
    context="The 'Obama O's' / 'Cap'n McCains' cereal boxes sold for about $40 each during the 2008 election. The cereal stunt funded Airbnb's payroll long enough to join Y Combinator's Winter 2009 batch, where Paul Graham reportedly said, 'If you can convince people to pay $40 for $4 cereal, you can probably get them to sleep in strangers' houses.'",
    strategy="airbnb_obama_os",
)

# T2-4 Vesting cliff
q(
    tier=2,
    question="Sara joins a startup. Her stock 'vests over four years with a one-year cliff.' She leaves at month eleven for a better offer. How much stock does she keep?",
    answer="None of it, the cliff requires a full twelve months before any shares vest at all",
    d1="Eleven of forty-eight months, calculated on a monthly pro-rata schedule from day one",
    d2="All of the stock, because the company terminated her early and must release everything",
    d3="Half of the stock, the standard severance for an early-departing salaried tech employee",
    context="Standard startup vesting: 4 years with a 1-year cliff. You vest 0% before month 12; at month 12 you get 25% in one chunk; then monthly vesting for 3 more years. The cliff is an incentive to stay through the first year, which is the most fragile period for an early team.",
    strategy="vesting_cliff_basics",
)

# T2-5 Limited liability + industrial capitalism
q(
    tier=2,
    question="Before 1855, if your English business failed you could be ruined or even jailed for debt. The Limited Liability Act 1855 capped each investor's loss at what they invested. What did this enable?",
    answer="Strangers could pool capital into large industrial ventures",
    d1="Banks could finally lend to small businesses across all of England immediately",
    d2="Workers could finally receive fair wages in any industrial sector across England",
    d3="Governments could finally tax corporate profits at much higher rates across the country",
    context="The Limited Liability Act 1855 (followed by the Joint Stock Companies Act 1856) is one of the key institutional innovations that enabled the second industrial revolution. By capping investor loss at the amount invested, it made it possible for strangers to pool large amounts of capital into risky ventures like railroads, factories, and shipping.",
    strategy="limited_liability_1855",
)

# T2-6 LLC vs C-corp incentive
q(
    tier=2,
    question="Two siblings start companies. The LLC sibling's profits flow to her personal return once. The C-corp sibling's company pays tax, then she pays tax again on dividends. What is this pattern called?",
    answer="Double taxation, first at the corporate level and again at the shareholder level",
    d1="Tax avoidance, the C-corp legally pays no taxes anywhere under US federal or state rule",
    d2="Inverted taxation, only applied to nonprofits under modern federal law",
    d3="Marginal taxation, the standard rate applied to a small-business owner",
    context="C-corp double taxation: profits taxed at the corporate rate (21% federal post-2017), then dividends taxed again at the shareholder's personal rate. LLCs are 'pass-through' — profits flow to the owner's personal return once. C-corps still exist because they are required for traditional venture-capital funding.",
    strategy="c_corp_double_tax",
)

# T2-7 Default alive vs default dead
q(
    tier=2,
    question="In October 2015, Paul Graham coined two startup terms. One whose growth lets it reach profit before cash runs out is 'default alive.' The opposite, still burning faster than it grows, is what?",
    answer="Default dead, the company will die unless something changes",
    d1="Default broke, a legal classification under US federal bankruptcy law from the 1980s",
    d2="Default safe, the standard term for a company protected by a venture firm's guarantee",
    d3="Default stable, the term Y Combinator uses for its top-tier accelerator companies",
    context="Paul Graham's October 2015 essay 'Default Alive or Default Dead?' became required reading for founders. The test: at current growth rate and burn, will you become profitable before cash runs out? Default-dead startups must change course (raise more, cut burn, accelerate growth) or they die when the money runs out.",
    strategy="default_alive_pg_2015",
)

# T2-8 CAC LTV ratio
q(
    tier=2,
    question="A subscription business spends $30 to acquire each customer; each customer pays $120 over their lifetime. The founder calls the ratio 'LTV to CAC.' What is the 4:1 number telling her?",
    answer="The unit economics look healthy, customers pay back acquisition cost",
    d1="The business is illegal in all US states under federal consumer-protection law of 1990",
    d2="The business must raise prices to four hundred percent of the current level",
    d3="The business must immediately reduce its marketing spend to zero dollars at all costs",
    context="Customer Acquisition Cost (CAC) vs Lifetime Value (LTV). A common rough benchmark: LTV:CAC > 3:1 is considered healthy. Below 1:1 means you lose money on every customer; the business is burning capital faster as it 'grows.' Bastiat's seen/unseen applied to startups: revenue growth visible, acquisition cost invisible.",
    strategy="cac_ltv_ratio",
)


# ==========================================================================
# T3 (12 questions, cap 714) — scene + stakes + mechanism
# ==========================================================================

# T3-1 S-corp salary trick
q(
    tier=3,
    question="A freelancer earns $100K as a sole prop, paying 15.3% self-employment tax on all of it. She switches her LLC to S-corp taxation, pays herself a $60K 'reasonable salary' (with payroll tax), and takes $40K as a distribution (no payroll tax). What does the tax code create?",
    answer="An arbitrage between salary and distribution that rewards the legal-structure choice",
    d1="An equal tax burden either way, since federal code treats sole prop and S-corp identically",
    d2="A higher tax burden, since S-corp distributions pay an extra 21 percent on every dollar",
    d3="A reason to drop the LLC entirely, because S-corp election is illegal for single-owner firms",
    context="The S-corp 'reasonable salary' trick is a textbook example of government-created arbitrage. By splitting income between salary (subject to ~15.3% payroll tax) and distribution (no payroll tax), small-business owners can save thousands. The IRS requires the salary be 'reasonable' for the work, which is the soft constraint that prevents pure abuse.",
    strategy="s_corp_salary_arbitrage",
)

# T3-2 Cap table dilution Series A
q(
    tier=3,
    question="Two co-founders start a company holding 50% each. They raise a Series A at a $10M post-money valuation: the investor wires $2.5M for 25% of the company. The investor then owns 25%. How much does each founder now own?",
    answer="37.5% each, both founders diluted equally from 50% to 37.5%",
    d1="50% each, since the founders' shares aren't reduced by the new investor's pre-arranged check",
    d2="25% each, since the investor's stake automatically halves the founders' positions by federal law",
    d3="0% each, since the new investor now owns the company entirely under the Series A round terms",
    context="Cap-table dilution: when new shares are issued, existing shareholders' percentages drop proportionally. Pre-money + investment = post-money. Investor's % = investment / post-money. Existing holders are diluted by (1 - investor's %). Two founders at 50% each, after 25% dilution, each hold 50% * 75% = 37.5%.",
    strategy="cap_table_series_a_dilution",
)

# T3-3 Tesla 2008 SpaceX loan
q(
    tier=3,
    question="In late 2008, both Tesla and SpaceX were nearly broke during the financial crisis. Elon Musk had to decide where to put the last of his money. He famously split his remaining cash between the two companies. What does this episode illustrate about founder capital?",
    answer="Founders sometimes personally fund their companies through near-collapse, taking on enormous concentrated risk",
    d1="Founders are legally barred from putting personal money into their own startups by Securities and Exchange rules",
    d2="The US Treasury automatically rescued any startup that ran out of cash during the financial crisis of late 2008",
    d3="Most venture capital firms refused to participate in late-stage rounds during the 2008 crisis at any valuation",
    context="December 2008: Tesla closed an emergency funding round on December 24th; SpaceX's first successful Falcon 1 launch came September 28th and a NASA contract followed in December. Musk reportedly put his last personal funds into both. The episode is a real-world illustration of founder concentration risk and conviction in their own venture.",
    strategy="musk_2008_loan",
)

# T3-4 SAFE notes vs priced rounds
q(
    tier=3,
    question="In 2013, Y Combinator's Carolynn Levy invented the SAFE (Simple Agreement for Future Equity). Founders raise money now without setting a valuation. Investors convert into stock at the next priced round, often with a discount or valuation cap. What does the SAFE delay?",
    answer="The valuation argument, which becomes the next round's problem to settle in detail",
    d1="The payment of money to the company, because SAFE investors only wire funds at the next priced round",
    d2="The legal incorporation of the company, since SAFE requires Delaware C-corp status to be valid in any state",
    d3="The right to issue stock at all, since SAFE prohibits any equity grants for at least three years under the contract",
    context="SAFEs (Simple Agreement for Future Equity) were introduced by Y Combinator in 2013 to streamline early-stage fundraising. Pre-SAFE, founders and angels had to negotiate a valuation immediately — which is hard when the company is just an idea. SAFEs let both sides defer the argument until the next priced round, when more information exists.",
    strategy="safe_notes_2013",
)

# T3-5 Limited liability + moral hazard
q(
    tier=3,
    question="A bank lends to a corporation that gambles aggressively. Win, and shareholders keep the upside. Lose, and the corporation goes bankrupt while shareholders walk away with personal assets untouched. What does this asymmetric structure create?",
    answer="Moral hazard, shareholders take risks they wouldn't take with full personal liability",
    d1="A safer financial system, since limited liability prevents personal hardship from poor decisions",
    d2="A neutral arrangement with no behavioral effect, since shareholders' initial investment is still at risk",
    d3="A legal requirement for banks to lend at lower rates to limited-liability firms under federal statute",
    context="Limited liability creates 'heads I win, tails creditors lose' incentives. The structure enabled industrial capitalism (T2-5) but also creates real moral-hazard problems — especially in banking, where deposit insurance plus limited liability for shareholders amplifies risk-taking. Allan Meltzer and Anna Schwartz both wrote on this tension.",
    strategy="limited_liability_moral_hazard",
)

# T3-6 Theranos VC due diligence
q(
    tier=3,
    question="Elizabeth Holmes raised ~$700M for Theranos at a $9B valuation, claiming to test diseases from a finger-prick. Walgreens deployed her machines. October 2015: John Carreyrou's WSJ investigation revealed the tech didn't work. What does Theranos illustrate?",
    answer="VC due diligence can fail when a charismatic founder blocks investors from verifying the technology",
    d1="Venture capitalists never invest in deep-tech startups under any normal market conditions",
    d2="Federal regulators routinely catch fraudulent medical-device startups before patients are harmed",
    d3="The Stanford CS program guarantees the technical validity of any startup founded by one of its dropouts",
    context="Theranos's investors included Larry Ellison, Tim Draper, Rupert Murdoch, and the Walton family — sophisticated investors who skipped deep technical due diligence in favor of the founder's narrative. Holmes was convicted of fraud in January 2022 and sentenced to 11 years in prison. The case is the canonical VC-due-diligence failure of the 2010s.",
    strategy="theranos_vc_failure",
)

# T3-7 Power law VC returns
q(
    tier=3,
    question="A VC firm invests in 50 startups per fund. Studies (Correlation Ventures, Horsley Bridge) find that about half lose money and a handful return the entire fund. What does this distribution force VCs to do?",
    answer="Chase startups with truly enormous upside, since modest winners can't compensate for the many losers",
    d1="Chase startups with the lowest possible failure probability, since each investment must return some money",
    d2="Chase startups with the most established business models, since predictable returns are the foundation of performance",
    d3="Chase startups with the highest current revenue, since revenue at investment time predicts ultimate fund returns",
    context="The power-law return distribution is the central fact of venture capital. Roughly 50% of investments lose money; 30-40% return less than 2x; only 5-10% return >10x. This forces VCs to seek 'fund returners' — single investments that could pay back the entire fund. It changes everything about how they make decisions, what stories they listen to, and what they ignore.",
    strategy="power_law_vc_returns",
)

# T3-8 Gross margin pricing power
q(
    tier=3,
    question="Software company A has 85% gross margin: it costs $15 to deliver $100 of revenue. Restaurant chain B has 28% gross margin: it costs $72 to deliver $100 of revenue. Both want to invest more in marketing. Which has more room to spend and still profit?",
    answer="The software company, because each marginal dollar of revenue costs only fifteen cents to deliver",
    d1="The restaurant chain, because physical businesses always have larger marketing budgets under standard finance theory",
    d2="Neither has any room, since gross margin and marketing budget are unrelated by federal accounting standards",
    d3="Both have equal room, since marketing budgets in modern business depend only on revenue size and not on margin",
    context="High gross margin (>70%) signals pricing power AND room for marketing/R&D investment without sacrificing profitability. Software, SaaS, and luxury-brand businesses tend to have high gross margins. Restaurants, retail, and commodity businesses tend to have thin gross margins. Buffett's emphasis on 'economic moats' often translates to durable high gross margins.",
    strategy="gross_margin_pricing_power",
)

# T3-9 Down round signal
q(
    tier=3,
    question="A startup raised Series B in 2021 at $1B valuation. In 2023, after the market repriced, it raised Series C at $400M — a 'down round.' Employees with options struck at 2021 valuations hold paper worth far less. What signal does a down round send?",
    answer="The company is in trouble, talent leaves, customers worry, the next round gets harder",
    d1="The company has negotiated clever tax advantages, making the lower valuation a positive outcome",
    d2="The company is on the verge of a wildly successful IPO at a much higher final valuation",
    d3="The company has fully repaid its early investors at the planned exit price from the original term sheet",
    context="Down rounds (new round at a lower valuation than the previous round) are the death-spiral signal in startup land. Existing investors' returns crash. Stock options for employees go underwater. Talent looks elsewhere. Customers wonder if you'll be around next year. The 2022-23 tech reset created an unusual number of these, exposing many 2021-era unicorns as having raised at unsustainable valuations.",
    strategy="down_round_signal",
)

# T3-10 Munger invert always invert
q(
    tier=3,
    question="Charlie Munger borrowed from the 19th-century mathematician Carl Jacobi the maxim 'invert, always invert.' Asked how to live well, Munger asked instead how to guarantee misery, then avoided that list. Applied to business, what does the inversion method ask?",
    answer="Not 'how do I succeed,' but 'what would guarantee failure,' and then carefully avoid that list",
    d1="Not 'what business should I start,' but 'what business would the government regulators approve of right away'",
    d2="Not 'what does the customer want,' but 'what would the largest competitor never do,' and then copy that",
    d3="Not 'what is the right strategy,' but 'what would my smartest rival probably guess that I am about to do next'",
    context="Munger's 'invert' habit (drawn from Jacobi's 'Man muss immer umkehren') was a recurring theme in his Poor Charlie's Almanack. Don't ask 'how to succeed'; ask 'what would guarantee failure' and avoid it. Don't ask 'how to be loved'; ask 'what would guarantee being hated' and avoid that. The method exploits the fact that avoiding catastrophe is often easier than engineering success.",
    strategy="munger_invert_method",
)

# T3-11 Bezos regret minimization
q(
    tier=3,
    question="In 1994, Jeff Bezos was a senior VP at D.E. Shaw making serious money. Quit to start an internet bookstore? He used a 'regret minimization framework' — projecting to age 80 and asking which choice he would regret. What did it reveal?",
    answer="Not trying would be the lasting regret at age 80, while a failed attempt would not be regretted at all",
    d1="The financial loss of leaving Wall Street would be the lasting regret of his life",
    d2="Both choices would be equally regrettable, so he flipped a coin to decide that week",
    d3="His New York landlord would be the most disappointed party, since leaving broke his lease",
    context="The regret-minimization framework is Bezos's most-cited founding-story heuristic. He realized that at age 80 he would not regret trying and failing at an internet bookstore in 1994 — but he WOULD regret never trying. This is a practical formulation of asymmetric upside: the downside of a failed startup attempt is bounded; the downside of a lifelong unanswered 'what if' is not.",
    strategy="bezos_regret_framework",
)

# T3-12 Sole prop vs LLC trade-off
q(
    tier=3,
    question="Mia starts a tutoring business. A sole proprietorship costs nothing to set up and uses her personal tax return — but a single lawsuit could reach her savings. An LLC costs about $100-300 to file and pay annually, but creates a legal shield. What is the trade-off she is weighing?",
    answer="Simplicity and zero cost now, against the unseen tail risk of personal liability later",
    d1="Tax savings on every transaction now, against the requirement to pay a federal corporate income tax instead later",
    d2="Profit margin reduction by half now, against the right to issue public shares on a stock exchange later",
    d3="Legal access to a sales tax exemption now, against the obligation to register with the federal SEC under securities law later",
    context="Sole prop vs LLC is the classic 'visible cost now vs invisible risk later' trade-off — a Bastiat-Pattern question. Sole prop has zero setup cost AND no annual fee, which is the seen benefit. LLC's annual filing fee is the seen cost. The unseen difference: a single lawsuit. For low-risk businesses (tutoring with no physical hazard), sole prop is often fine; for higher-risk ones (anything physical), LLC is cheap insurance.",
    strategy="sole_prop_llc_tradeoff",
)


# ==========================================================================
# T4 (14 questions, cap 945) — setup + tension + named details + payoff
# ==========================================================================

# T4-1 Limited liability 1855 deep
q(
    tier=4,
    question="Before 1855, English business partners were jointly liable for ALL debts — a failed venture could ruin every partner and even land them in debtors' prison. The Limited Liability Act 1855 capped each shareholder's loss at the amount invested. John Stuart Mill initially opposed the law, fearing reckless speculation. What did it actually enable?",
    answer="Strangers pooled capital into railroads, factories, and shipping at scales personal liability had made impossible",
    d1="The immediate end of fraud in publicly-traded companies, since limited liability improved executive honesty",
    d2="The complete end of debtors' prisons across England, since limited liability erased business debt overnight",
    d3="The Crown takeover of British industry, since limited liability required state ownership of any large firm",
    context="The Limited Liability Act 1855 + Joint Stock Companies Act 1856 are arguably the most consequential corporate-law innovations of the 19th century. Their critics (Mill among them) were right about moral hazard but wrong about the net effect: limited liability unleashed the second industrial revolution's capital-intensive sectors. The trade-off (T3-5) is real, but the upside dwarfed the downside in practice.",
    strategy="limited_liability_1855_deep",
)

# T4-2 YC 2005 standardized model
q(
    tier=4,
    question="When Y Combinator launched March 2005 under Paul Graham and three co-founders, traditional VC wrote each check after months of bespoke negotiation. YC offered the same deal to every founder in a batch: small standardized investment, three months of mentorship, Demo Day at the end. Why did this model compound where bespoke deals could not?",
    answer="Every batch reused the same docs and lessons, alumni helped later founders, and Demo Day grew its audience year over year",
    d1="The federal government required YC to standardize under new SEC rules from 2005 covering small-startup investment exemptions",
    d2="Traditional VCs immediately copied the format, which legally forced standardization across the industry by trade-association rule",
    d3="A Cambridge city ordinance required all accelerators to use identical legal documents for any company headquartered within city limits",
    context="YC's standardization let it run multiple batches per year, recycle legal docs, build an alumni network that helps later batches, and scale Demo Day from a small Cambridge event into a major industry milestone. Each cohort's lessons compounded. By 2015, YC had funded Airbnb, Dropbox, Stripe, Coinbase, Reddit, Twitch, and DoorDash — the standardized model produced a portfolio worth more than many traditional VC firms.",
    strategy="yc_standardization_compounds",
)

# T4-3 Cap table Series A through C arc
q(
    tier=4,
    question="Two co-founders start at 50/50. Seed round dilutes them ~15% (now 42.5% each). Series A ~20% (now 34%). Series B ~15% (now 28.9%). Series C ~12% (now 25.4%). Stock-option pool refreshes take another ~10%. At IPO they each hold maybe 15-20%, sometimes less. Why is the founder's ownership PERCENTAGE not what determines whether they made the right choices?",
    answer="A small slice of a very large pie can be worth far more than a large slice of a small one, the absolute exit value is what matters",
    d1="The federal government caps founder ownership at twenty percent in any IPO-stage company under SEC rules established in 1934 to protect investors",
    d2="Cap-table percentages are reset at every IPO so the founder always ends up with exactly one percent regardless of how many rounds were raised",
    d3="Venture capital firms typically buy back the founders' shares at original cost during Series C, forcing all founders to start from scratch after",
    context="The cap-table dilution arc is brutal but the math is straightforward: founders trade percentage for absolute value. Founding 100% of a $0 company is worth $0; founding 15% of a $10B exit is worth $1.5B. Bezos owned ~10% of Amazon at IPO. Brin/Page each ~16% of Google. Zuckerberg ~28% of Facebook at IPO. The successful founders sold percentage for capital that built the absolute value.",
    strategy="founder_dilution_arc_full",
)

# T4-4 Bezos garage to AWS arc
q(
    tier=4,
    question="July 5, 1994: Bezos incorporates Amazon in Bellevue. He drives cross-country typing the business plan as his wife drives. April 1995: first book sells. 1997: IPO at $18. 2000-2001: dot-com bust nearly kills the company. 2006: AWS launches. 2020: Bezos steps down with a trillion-dollar company. What 1994 heuristic anchored the arc?",
    answer="The regret-minimization framework, projecting to age 80 and picking the path he wouldn't regret not trying",
    d1="An FTC small-business expansion exemption for internet retail, which Amazon used through the 1997 IPO and dot-com years",
    d2="A formal 1994 Microsoft partnership with Bill Gates giving Amazon exclusive use of internet-shopping software from Redmond",
    d3="A US Treasury small-business loan of fifty million taken in 1995 to fund Amazon's initial book inventory and warehouse network",
    context="Bezos used the regret-minimization framework (T3-11) to decide to leave D. E. Shaw in 1994. The choice was non-obvious — he was making serious money on Wall Street. But by projecting himself to age 80, he saw the not-trying regret as much larger than the failed-attempt regret. The framework anchors his founding story; AWS in 2006 is the eventual second-act that made Amazon what it is today.",
    strategy="bezos_full_arc",
)

# T4-5 Vesting cliff incentive logic
q(
    tier=4,
    question="Standard startup vesting: four years total, one-year cliff. Before month 12: zero shares. At month 12: 25% in one chunk. Then monthly for 36 months. Without a cliff, a hire could quit at month 2 holding a permanent slice. Without the four-year vest, hires would leave right after their grant. What problem does this solve?",
    answer="The incentive alignment problem, founders and early hires must commit long enough for the company to actually exist",
    d1="The federal tax problem, the IRS requires exactly four years of vesting on stock-option grants under the tax code",
    d2="The SEC disclosure problem, every shareholder under one year triggers automatic IPO-like reporting requirements",
    d3="The Delaware corporate-law problem, the state requires four-year vesting for any company incorporated there",
    context="The 4-year-with-1-year-cliff schedule is a market convention, not a law. It solved two failure modes: pre-cliff quitters who held permanent fractions of the company (creating cap-table dead weight) and post-grant short-timers who had no reason to stay. The structure aligns hires with the long arc of company building, and is the canonical example of equity as deferred compensation tied to commitment.",
    strategy="vesting_cliff_alignment",
)

# T4-6 SAFE notes Y Combinator 2013
q(
    tier=4,
    question="Before 2013, seed rounds typically used convertible notes with interest, maturity dates, and complex valuation negotiation. December 2013: YC's Carolynn Levy introduced the SAFE — Simple Agreement for Future Equity. No interest, no maturity, just a promise to convert at the next priced round. What did the SAFE remove from early fundraising?",
    answer="The premature valuation argument, deferring it to the priced round when more information about the company exists",
    d1="The legal requirement to incorporate, since SAFE notes can be issued by any unincorporated team of founders",
    d2="The need to disclose financial information to investors, since SAFE notes legally exempt founders from SEC reporting rules",
    d3="The requirement to register the company federally, since SAFE notes substitute as a binding legal entity in all fifty states",
    context="SAFE notes (2013) addressed the structural absurdity of arguing valuation when a company has no revenue, no product, sometimes no team. The argument was a waste of time and a deal-killer. By deferring valuation to the next priced round (when revenue, traction, and team are real), SAFEs let early money close fast. The trade-off: founders sometimes give up more than they realize because they can't see the dilution cascade at conversion time.",
    strategy="safe_notes_2013_deep",
)

# T4-7 Theranos full arc
q(
    tier=4,
    question="Stanford dropout Elizabeth Holmes founded Theranos in 2003. By 2014 she had raised ~$700M at a $9B valuation, with investors including Ellison, Murdoch, the Waltons, the DeVoses. Board: Henry Kissinger and George Shultz. October 2015: Carreyrou's WSJ exposed it. January 2022: jury convicted Holmes on four counts of fraud. What does the arc illustrate?",
    answer="Sophisticated investors and prominent board members are no substitute for verifying that the underlying technology actually works",
    d1="Stanford's CS program automatically guarantees the technical validity of any startup founded by its students or dropouts",
    d2="The SEC requires independent technical audits of any startup raising over fifty million dollars from accredited investors",
    d3="Theranos investors were all blocked from filing civil claims against the founder by federal startup-liability shield rules",
    context="Theranos investors skipped deep technical due diligence in favor of narrative, prestige, and board roster. The lesson is brutal but clear: even Kissinger and Shultz on the board, even Murdoch and Ellison writing checks, did not substitute for actually checking whether the Edison machine could perform 240 tests from a finger-prick of blood. The recognition skill is to be suspicious when due diligence is being aggressively gatekept.",
    strategy="theranos_full_arc",
)

# T4-8 Power-law VC math
q(
    tier=4,
    question="A venture fund makes 50 investments of $2M each ($100M total). Studies (Correlation Ventures, Horsley Bridge) suggest: 30 return $0, 15 return less than 2x, 4 return 2-10x, and 1 returns 30-50x. The fund's total return depends almost entirely on that one outlier. What does this force VCs to do?",
    answer="Pass on plausibly-profitable startups lacking enormous upside, since solid 2-3x exits cannot compensate for the many zeroes",
    d1="Invest only in startups with the highest current revenue, since revenue at investment time predicts ultimate fund returns",
    d2="Diversify across hundreds of small investments, since the law of large numbers eventually delivers public-index returns",
    d3="Insist on board control of every portfolio company at investment time, since operational control is what produces VC returns",
    context="The power-law distribution is the central operating fact of venture capital. VCs need 'fund returners' — single investments that could pay back the entire fund. A plausible 3x exit on a $2M investment ($6M return) is great in absolute terms but irrelevant to a $100M fund's outcome. The math forces VCs to chase outliers, which is why VCs ask 'is this a multi-billion-dollar outcome' before 'is this a sensible business?'",
    strategy="power_law_vc_math_deep",
)

# T4-9 LLC vs C-corp for raising VC
q(
    tier=4,
    question="A founder building a future venture-backed company is told by every lawyer to incorporate as a Delaware C-corp, not an LLC — even though LLCs offer the same liability shield AND avoid double taxation. Why pay double tax for the same legal shield? What problem does the LLC create for VC fundraising?",
    answer="Most VCs cannot invest in pass-through entities, since their limited partners include pension funds whose tax status forbids it",
    d1="LLCs are illegal at the federal level for any company that intends to raise venture capital, under SEC rules from 2005",
    d2="C-corps automatically receive Federal Reserve loans that LLCs do not, which is essential to bridge VC funding rounds",
    d3="Delaware state law mandates any company headquartered worldwide must convert to a C-corp before raising private investment",
    context="C-corp recommendation is driven by the LP problem. VCs raise from limited partners (pension funds, university endowments, sovereign wealth funds) — many of which have tax statuses that forbid them from receiving pass-through income from LLCs (UBTI rules for tax-exempt LPs). Investing in a C-corp avoids this. The double taxation is a real cost the founder pays in exchange for being investable by institutional VCs.",
    strategy="c_corp_vc_compatibility",
)

# T4-10 Customer churn vs growth
q(
    tier=4,
    question="A subscription startup proudly reports adding 1,000 new customers per month. The CEO doesn't mention that 950 existing customers cancel each month — net growth is only 50. The company is on a 'leaky bucket': pouring water in faster than it leaks out, but only slightly. What metric exposes the gap between gross growth and net growth?",
    answer="The churn rate, the percentage of existing customers who cancel each month or year",
    d1="The federal revenue rate, the percentage of revenue paid in federal taxes after deductions for cost of goods sold and operating expenses",
    d2="The cash conversion cycle, the average number of days between receiving cash from customers and paying suppliers their invoices",
    d3="The acquisition velocity, the number of new customers signed up per dollar spent on marketing channels excluding paid social",
    context="Churn is the Bastiat unseen of subscription businesses. The seen number is gross new customers (the 1,000). The unseen number is the 950 who quietly cancel. Sophisticated investors look at net retention (revenue from existing customers after upgrades AND churn) — over 100% means the existing base grows even before counting new customers. Under 90% net retention is a warning sign that the product isn't sticky.",
    strategy="churn_seen_unseen",
)

# T4-11 Burn rate runway crisis decision
q(
    tier=4,
    question="A startup has $1.2M in the bank and burns $200K/month — 6 months of runway. The founder must decide: cut burn, raise more now, or accelerate growth. Each path has unseen costs. What does Paul Graham's October 2015 'default alive' framework say to do first?",
    answer="Calculate whether current growth would let the company reach profit before cash runs out, then choose based on the answer",
    d1="Fire half the employees regardless of growth trajectory, since six months of runway is automatically a death sentence",
    d2="Raise a new round at the current valuation, since six months of runway legally requires closing a round within ninety days",
    d3="Sell to the largest acquirer at current valuation, since the framework requires exit within twelve months of the runway test",
    context="Graham's 'Default Alive or Default Dead?' essay (October 2015) gives founders a clean test: at current growth and burn, will you become profitable before cash runs out? If yes, you're default alive and can keep building. If no, you must change something — usually cut burn or accelerate growth. The framework is honest about a fact many founders dodge: most startups die from running out of cash, not from any other cause.",
    strategy="default_alive_decision_frame",
)

# T4-12 Unit economics car-wash trap
q(
    tier=4,
    question="A car-wash startup charges $20 per wash and spends $25 in supplies, labor, and water per wash. The founder argues that scale will solve this: 'When we get to 1,000 washes a day, our purchasing power will lower our supply costs and we'll be profitable.' What does Munger's joke about 'making it up in volume' suggest about this plan?",
    answer="The unit economics must work before scale, scaling a negative margin only multiplies the loss faster",
    d1="The startup will inevitably succeed at scale, since high volume always eventually drives down per-unit costs to below the selling price in any business",
    d2="The founder should immediately raise venture capital, since scaling losses are exactly what venture capital exists to fund and reward at IPO time",
    d3="The startup is protected by federal small-business subsidies, since car-wash businesses qualify for SBA loans that cover any per-unit shortfall by law",
    context="The car-wash example is Munger's joke (T2-1) made literal. Per-unit loss is the seen number; the unseen number is what scale will actually deliver on cost. Volume discounts exist (raw materials get cheaper at scale) but rarely by enough to flip a 25% per-unit loss into profitability. The startups that DO scale into profit usually start with positive unit economics and use scale to lower COGS by 10-20%, not by 100%.",
    strategy="unit_economics_car_wash",
)

# T4-13 Cap table founder departure
q(
    tier=4,
    question="Co-founder Alex leaves a startup at month 8 after a fight with his partner. Without the standard 4-year vest with 1-year cliff (T2-4), Alex would walk out holding 50% of the company forever — a 'dead equity' problem that would haunt the cap table at every future round. With the standard vesting in place, what happens to Alex's shares?",
    answer="His shares return to the company's option pool, the surviving co-founder and future hires can rebuild a real cap table",
    d1="His shares immediately convert to debt the company must repay at the original investment price plus federally-set interest rates compounded monthly",
    d2="His shares pass automatically to the company's largest external investor at zero cost, under Delaware corporate law for early-stage departures",
    d3="His shares are bought by the state of Delaware at the company's most recent valuation, then resold to qualified accredited investors through a state auction",
    context="The 1-year cliff exists precisely for this scenario. Founder breakups in year one are common enough that the structure is industry standard. Without the cliff, Alex walks out with 50% — a permanent cap-table problem that scares away every future investor and demoralizes the founder who stays. With the cliff, his shares return to the pool, the surviving founder regains optionality, and the company can attract real future investment.",
    strategy="founder_breakup_cliff",
)

# T4-14 S-corp reasonable salary IRS scrutiny
q(
    tier=4,
    question="A solo consultant nets $200K through her S-corp. To minimize self-employment tax, she pays herself a $20K salary and takes $180K as distribution. The IRS audits her and challenges the salary as 'unreasonably low' — distribution reclassified as salary, back-payroll tax plus penalties. What constraint does the 'reasonable salary' rule create?",
    answer="The salary cannot be artificially low, the IRS expects it to reflect what a third party would charge for the same work",
    d1="The salary must be exactly fifty percent of net profit by law, with the other half distributed under IRS Rule 1376",
    d2="The salary must equal the federal minimum wage times 2,080 hours, the standard full-time work-year used in audit cases",
    d3="The salary must be the highest amount paid to any employee in the calendar year, regardless of the owner's actual function",
    context="The 'reasonable salary' rule is the soft constraint that prevents pure abuse of the S-corp arbitrage (T3-1). The IRS publishes audit guidance on factors: training and experience, duties, time and effort, comparable salaries for similar work. Setting salary too low to dodge payroll tax invites audit. The right level is usually 40-60% of profit for service businesses — high enough to look like genuine compensation, low enough to capture meaningful savings on the rest.",
    strategy="s_corp_reasonable_salary",
)


# ==========================================================================
# T5 (12 questions, cap 1155) — hard ceiling, deep arc + named details
# ==========================================================================

# T5-1 Limited liability + industrial-capital arc
q(
    tier=5,
    question="Pre-1855 English business: partners were jointly liable for ALL debts; a failed venture could ruin every partner personally and even land them in debtors' prison (Charles Dickens's father served time in Marshalsea Prison in 1824). The Limited Liability Act 1855 capped each shareholder's loss at the amount invested. John Stuart Mill initially opposed it, fearing reckless speculation. Within fifty years, British railroad mileage, factory output, and shipping tonnage had multiplied. What did the innovation actually unleash?",
    answer="Strangers pooled capital into railroad, factory, and shipping ventures at scales that personal liability had made impossible",
    d1="A massive increase in personal bankruptcy among British business partners across England for twenty years until Parliament partly repealed the law in 1875",
    d2="The state takeover of British industry by Queen Victoria, since limited liability required Crown ownership of any company exceeding one hundred shareholders",
    d3="The decisive end of all fraud in British publicly-traded companies, since limited liability automatically improved every corporate executive's incentive to behave honestly",
    context="The Limited Liability Act 1855 + Joint Stock Companies Act 1856 enabled the second industrial revolution's capital-intensive sectors. The trade-off (moral hazard) was real and the critics weren't wrong about it — but the net effect of unleashing capital pools transformed economic possibility. Personal liability had artificially capped venture scale; removing it let railroads, factories, and shipping reach modern scale. Cross-link to history bank.",
    strategy="limited_liability_arc_t5",
)

# T5-2 YC 2005-2015 model arc
q(
    tier=5,
    question="March 2005: Paul Graham, Jessica Livingston, Robert Morris, and Trevor Blackwell ran Y Combinator's first batch — eight teams, $6,000 per founder, three months in Cambridge, ending in Demo Day. The radical move was standardization: same legal docs, same check size, same batch length. Bespoke VC dealmaking could not compound across cohorts. By 2015 YC had funded Airbnb, Dropbox, Stripe, Coinbase, Reddit, Twitch, DoorDash, and Instacart. What property of the model made the difference?",
    answer="Every batch reused docs and lessons, alumni helped later cohorts, and Demo Day's audience compounded year over year, with each batch's lessons becoming structural",
    d1="The federal government required YC to standardize because of new SEC rules introduced in early 2005 covering small-startup investments under an accredited-investor exemption",
    d2="Sand Hill Road VCs immediately copied the YC format and adopted it across the industry by trade-association resolution, which legally forced all accelerators to follow it",
    d3="A Cambridge city ordinance from 2005 required all accelerators to use identical legal documents for any company headquartered within city limits during operation",
    context="YC's standardization was the operating model that let the firm scale: identical paperwork between Founder Stage and Demo Day, identical curriculum, identical batch length, an alumni network that grew with each cohort and helped later cohorts directly. Each batch's lessons compounded onto every future batch. By 2015 YC had funded a portfolio worth more than many traditional VC firms — a direct vindication of the standardize-and-scale thesis.",
    strategy="yc_arc_t5",
)

# T5-3 Bezos full arc 1994-2020
q(
    tier=5,
    question="July 5, 1994: Bezos incorporates Amazon in Bellevue — quitting D.E. Shaw via his regret-minimization framework. April 1995: first book sold. 1997: IPO at $18. 2000-2001: dot-com crash drops Amazon from $107 to $7. 2002: Walmart sues; Amazon survives. 2006: AWS launches. 2013: Bezos buys the Washington Post. 2020: steps down with a trillion-dollar company. What does the 26-year arc illustrate about founder conviction?",
    answer="Companies that survive the deep trough often emerge dominant, the trough kills most competitors and leaves the survivor a vastly larger market to itself afterward",
    d1="The FTC's small-business expansion exemption for internet retail was the legal mechanism behind Amazon's survival through the dot-com bust and into the modern profitable era",
    d2="A formal Microsoft partnership signed in 1994 with Bill Gates gave Amazon exclusive use of internet-shopping software from Redmond that no competitor could license at any price",
    d3="A US Treasury small-business loan of fifty million taken in 1995 funded Amazon's initial book inventory and the Washington state warehouse network through the survival year of 2001",
    context="Amazon's 2000-2001 trough is its hardest test: stock down ~94%, dot-com peers liquidated, lawsuits, doubts everywhere. Bezos's conviction (anchored in the 1994 regret-minimization framework) carried the company through. Most dot-com survivors were obliterated; Amazon emerged with a clearer market, cheaper hires, and the operational depth that funded AWS in 2006. The trough is where founder conviction becomes structural advantage.",
    strategy="bezos_arc_full_t5",
)

# T5-4 Cap table dilution mathematics
q(
    tier=5,
    question="Two co-founders start at 50% each. Seed dilutes them ~15% (each 42.5%). Series A ~20% (each 34%). Series B ~15% (each 28.9%). Series C ~12% (each 25.4%). Two option-pool refreshes of 10% each take them to ~20.6% then ~18.5%. The company exits at a $5B valuation. Each founder ends up with about $925M on paper. What does the dilution math teach about founder ownership?",
    answer="Percentage ownership drops continuously, but the absolute dollar value at exit dwarfs dilution if the company hits truly large outcomes",
    d1="The federal government caps founder ownership at fifteen percent in any IPO-stage company under SEC rules from 1934 to protect investors",
    d2="Cap-table percentages reset to founding values at every IPO so the founder ends with exactly fifty percent regardless of private rounds raised",
    d3="VCs typically buy back founders' shares at original cost during Series C, forcing founders to restart their ownership from scratch every round",
    context="Bezos owned about 10% of Amazon at IPO. Brin and Page each ~16% of Google. Zuckerberg ~28% of Facebook (his anomaly was a dual-class share structure that kept voting control). The dilution math is brutal in percentage terms but irrelevant if the absolute exit value is large enough. Founders trade percentage for the capital that builds value, and the trade is good when the company hits big. It's terrible when the company stays modest.",
    strategy="dilution_math_full_t5",
)

# T5-5 Theranos VC due-diligence failure
q(
    tier=5,
    question="Stanford dropout Elizabeth Holmes founded Theranos in 2003. By 2014 she had raised ~$700M at a $9B valuation. Investors: Ellison, Murdoch, the Waltons, the DeVoses. Board: Henry Kissinger and George Shultz. Walgreens deployed her devices to about 40 stores. October 15, 2015: Carreyrou's WSJ investigation exposed that the Edison machine couldn't perform the 240 promised tests. January 2022: jury convicted Holmes on four counts of fraud; 11-year sentence. What was the canonical due-diligence failure?",
    answer="Sophisticated investors substituted board prestige and CEO narrative for the actual verification that the underlying technology functioned as claimed",
    d1="The Stanford CS department automatically guarantees the technical validity of any startup founded by its admitted students or dropouts under university policy",
    d2="The SEC requires independent third-party technical audits of any startup raising over fifty million in private investment from accredited investors under regulation D",
    d3="The investors who lost money in Theranos were blocked from filing civil claims against the founder by federal startup-investor liability shield rules of 1995",
    context="Theranos is the textbook VC due-diligence case study: Kissinger and Shultz on the board, Murdoch and Ellison writing checks, Walgreens deploying devices — and none of it substituted for actually checking whether the Edison machine worked. Holmes restricted independent technical verification aggressively. The recognition skill the case teaches: be suspicious when due diligence is being gatekept, especially around a charismatic founder claiming a 'special' technology.",
    strategy="theranos_t5",
)

# T5-6 Power-law VC math complete
q(
    tier=5,
    question="A venture fund makes 50 investments of $2M each, deploying $100M. Correlation Ventures and Horsley Bridge data suggest a typical distribution: about 30 return $0, 15 return less than 2x ($60M back), 4 return 2-10x ($30M back), and 1 returns 30-50x ($80M back). The single outlier accounts for nearly half the fund's return. What logic does this impose on venture capital?",
    answer="VCs must chase startups with outlier-outcome potential, since solid 2-3x exits cannot compensate for the many zeroes that dominate the portfolio's returns over a fund's life",
    d1="VCs must invest only in startups with the highest current revenue at investment time, since revenue at that time is the most reliable predictor of fund-level performance",
    d2="VCs must diversify across hundreds of small investments, since the law of large numbers delivers steady returns identical to public-market indexes after enough years",
    d3="VCs must insist on board control of every portfolio company at investment time, since operational control is what produces venture capital returns in the post-2015 era",
    context="The power-law distribution is the central operating fact of venture capital. VCs need 'fund returners' — single investments that could pay back the entire fund several times over. The structural consequence: VCs systematically pass on plausibly-profitable startups that lack outlier potential, because such investments are mathematically irrelevant to fund-level returns. The bias is rational given the underlying distribution, even though it filters out many genuinely good businesses.",
    strategy="power_law_vc_t5",
)

# T5-7 Tesla 2008 SpaceX bankruptcy
q(
    tier=5,
    question="December 2008: Tesla had weeks of cash. SpaceX had just completed Falcon 1's first launch (September 28) and won a $1.6B NASA Commercial Resupply contract (December 23). Musk had spent ~$180M from his PayPal exit on the two and was near personal bankruptcy. He famously split his remaining cash between them — borrowing from friends. Tesla closed an emergency convertible-note round December 24. What does this illustrate about founder capital?",
    answer="Founders sometimes fund their own companies through near-collapse, taking on enormous concentrated risk for a binary outcome that could ruin them",
    d1="The US Treasury automatically rescued any company in the automotive or aerospace sectors during late 2008 under the Emergency Economic Stabilization Act passed by Congress",
    d2="The Federal Reserve directly provided special low-interest emergency loans to founders of strategic technology companies during 2008 under expanded discount-window rules",
    d3="Most VC firms participated in late-2008 emergency rounds at standard valuations on standard terms, since the crisis had no effect on Silicon Valley willingness to commit at full price",
    context="Musk's December 2008 episode is one of the most vivid founder-conviction stories of the modern era. Tesla survived its emergency raise; SpaceX got the NASA contract; both companies went on to define their industries. The story illustrates the asymmetric founder bet: if either company had failed, Musk would have lost everything; both succeeded, and he became one of the wealthiest people alive. The episode is a real-world illustration of founder concentration risk.",
    strategy="musk_2008_t5",
)

# T5-8 Airbnb full survival arc
q(
    tier=5,
    question="2007: Brian Chesky and Joe Gebbia couldn't pay rent in San Francisco, so they rented air mattresses on their floor during a design conference. 2008: founded Airbnb with Nathan Blecharczyk. Autumn 2008: nearly broke, they printed 'Obama O's' and 'Cap'n McCains' cereal boxes for the election, selling them for ~$40 each. The cereal stunt funded payroll long enough to join YC Winter 2009. What did the cereal episode reveal that convinced Paul Graham?",
    answer="They could convince people to pay forty dollars for four-dollar cereal, which meant they could convince strangers to sleep in strangers' houses across the country",
    d1="They had a permanent federal contract with the US government to provide alternative housing during election seasons under a multi-year procurement agreement signed before launch",
    d2="They had already raised twenty million from a tier-one VC firm at a substantial Series A valuation by autumn 2008, joining YC Winter 2009 as a much larger startup with full payroll",
    d3="They had a personal endorsement from the DNC chair for the upcoming presidential election that legally bound retailers across the US to stock and distribute their cereal product",
    context="The 'Obama O's' / 'Cap'n McCains' cereal stunt is one of the canonical founder-resilience stories. The cereal boxes (about $40 each, hand-painted) funded payroll long enough for Airbnb to join YC Winter 2009. Graham's quoted reasoning recognized something deeper than the immediate cash: a team that could sell $4 cereal for $40 had the persuasion-and-execution skill to convince strangers to do something far weirder than buying cereal. The skill, not the money, was the real signal.",
    strategy="airbnb_arc_t5",
)

# T5-9 LLC pass-through vs C-corp VC structural
q(
    tier=5,
    question="A founder building a venture-backed company is told by every lawyer to incorporate as a Delaware C-corp, not an LLC — even though LLCs offer the same liability shield AND avoid double taxation (pass-through to personal return). Why pay double tax for the same legal shield? The answer lies in who supplies the VC firm's own money. What structural problem does an LLC create?",
    answer="Most VCs cannot invest in pass-through entities, since their limited partners include pension funds and endowments whose tax status forbids receiving such income from LLCs",
    d1="LLCs are illegal at the federal level for any company that intends to raise venture capital from institutional investors, under SEC rules from 2005 preventing the structure in venture deals",
    d2="C-corps automatically receive special Federal Reserve emergency loans during downturns that LLCs do not qualify for, which makes the C-corp essential for bridging the gap between rounds",
    d3="Delaware state law mandates any company headquartered worldwide must convert to a C-corp structure before raising private investment under recently revised Delaware corporate law provisions",
    context="The C-corp recommendation is driven by the LP tax problem. VCs raise from limited partners (pension funds, university endowments, sovereign wealth funds) — many of which are tax-exempt entities whose status forbids them from receiving pass-through 'unrelated business taxable income' (UBTI) from LLCs. Investing in a C-corp avoids this. Founders pay the double-tax cost in exchange for being investable by institutional VCs at all. It's another government-created structural arbitrage.",
    strategy="llc_vc_pass_through_t5",
)

# T5-10 Munger invert + Buffett moats arc
q(
    tier=5,
    question="Munger borrowed from mathematician Carl Jacobi the maxim 'Man muss immer umkehren' — 'one must always invert.' Don't ask 'how to succeed,' ask 'what would guarantee failure' and avoid that list. Don't ask 'what businesses are good,' ask 'what businesses are obviously bad' and avoid them. Buffett used the same inversion to identify 'economic moats': businesses competitors cannot easily destroy. What core skill does the method develop?",
    answer="The skill of identifying failure modes and avoiding them, which is often easier than engineering success in advance and compounds over decades of disciplined practice",
    d1="The skill of forecasting interest rate movements over multi-decade horizons by analyzing Fed meeting minutes from previous policy cycles across decades of regulatory history",
    d2="The skill of lobbying government regulators effectively for sector-specific policy outcomes by reading their public statements and academic affiliations in the months before deliberation",
    d3="The skill of identifying short-term arbitrage opportunities across global agricultural futures markets by analyzing weather data in the four major growing regions plus shipping conditions",
    context="Munger's inversion habit was a recurring theme in Poor Charlie's Almanack. The method exploits an asymmetry: avoiding catastrophe is often easier than engineering success in advance. Applied to investing, the question becomes 'what could destroy this business?' rather than 'what could make this business great?' Applied to life, 'what would guarantee misery?' rather than 'what would guarantee happiness?' Both Munger and Buffett used the inversion to build Berkshire Hathaway over six decades.",
    strategy="munger_invert_full_t5",
)

# T5-11 Vesting + option-pool mechanic
q(
    tier=5,
    question="The standard 4-year vest with 1-year cliff is half the founder-incentive architecture. The other half is the option pool — a reserve of unissued shares (usually 10-20% of the company) set aside before the next round so future hires can get equity without diluting investors. The pool is sized pre-money in the round, meaning founders pay the dilution. What structural problem does the vesting + pool together solve?",
    answer="Early hires must be incentivized to stay AND new hires must keep getting equity grants, both without leaving cap-table dead weight when people depart over time",
    d1="The SEC's pre-IPO disclosure requirement for any startup with more than 200 shareholders, which mandates a particular vesting structure for employees holding equity",
    d2="The Delaware corporate tax authority's requirement that every C-corp maintain at least 15% of issued shares in a separate option pool at all times during operation",
    d3="The federal employment-law minimum requirement that any company offering equity compensation must reserve at least 20% of outstanding shares for non-executive employees",
    context="The vesting + option pool architecture together solves the equity-as-deferred-compensation problem. Vesting keeps people through the fragile early years; the option pool ensures the company can keep granting equity to new hires without crushing the cap table. The 'pre-money option pool shuffle' is the technical detail that often confuses founders: by setting up the pool pre-money in a financing round, the dilution is effectively borne by existing shareholders (founders, prior investors) rather than by the new investor.",
    strategy="vesting_option_pool_arc_t5",
)

# T5-12 Sole prop to LLC to S-corp to C-corp arc
q(
    tier=5,
    question="A small business follows a typical legal arc. Year 1: sole prop, full personal liability, zero setup cost. Year 2: revenue hits $80K, founder forms an LLC for $300 in Delaware. Year 3: revenue hits $200K, founder elects S-corp taxation to save self-employment tax via the reasonable-salary trick. Year 5: founder wants to raise VC, must convert to Delaware C-corp despite double taxation. What does this reveal about US business law?",
    answer="Each legal form is a government-created bundle of trade-offs, founders pick the bundle whose costs and benefits best fit their current stage",
    d1="The IRS randomly assigns a legal form to each US business via a Treasury lottery system, which is why a company shifts between sole prop, LLC, S-corp, and C-corp",
    d2="Delaware levies a mandatory annual fee on every US business that increases with revenue, and reaching higher legal-form tiers is the only way to qualify for a lower fee rate",
    d3="The federal government requires every US business to progress through exactly these four forms in this exact order under Title 26, with tax penalties applied to any company that skips a step",
    context="The sole-prop → LLC → S-corp election → C-corp arc is the canonical small-business legal-structure progression. Each step trades simplicity for additional structure that better fits the new stage's needs. Sole prop: zero setup, full liability. LLC: liability shield, easy formation, pass-through tax. S-corp election: payroll-tax savings via reasonable salary. C-corp: required for VC, but double taxation. Each form is a government-created arbitrage; sophisticated founders pick the bundle whose trade-offs match their current stage.",
    strategy="legal_form_arc_full_t5",
)


# ==========================================================================
# Validate + save
# ==========================================================================

def main() -> int:
    # Hard-fail early if any per-question constraints tripped
    if _ERRORS:
        print(f"\n=== {len(_ERRORS)} per-question constraint errors ===")
        for e in _ERRORS:
            print(e)
            print()
        return 2

    # Sanity: tier distribution
    counts = {t: sum(1 for q in QUESTIONS if q["tier"] == t) for t in range(1, 6)}
    print(f"Tier distribution: {counts}")
    assert counts == {1: 4, 2: 8, 3: 12, 4: 14, 5: 12}, f"Bad distribution: {counts}"
    assert len(QUESTIONS) == 50, f"Bad count: {len(QUESTIONS)}"

    # Validate against gates
    print("\nValidating against economics gates...")
    dup, ans = build_bank_indices(QUESTIONS)

    pass_count = 0
    soft_warn_count = 0
    fail_count = 0
    failures: list[tuple[int, dict]] = []

    for i, qd in enumerate(QUESTIONS):
        r = validate_rewrite(
            "economics",
            qd,
            bank=QUESTIONS,
            dup_index=dup,
            answer_index=ans,
            replace_idx=i,
        )
        if r["verdict"] == "FAIL":
            fail_count += 1
            failures.append((i, r))
            print(f"\nFAIL T{qd['tier']} #{i}: {qd['question'][:80]}")
            for gate, reason in r["hard_fails"]:
                print(f"  - {gate}: {reason}")
        elif r["verdict"] == "SOFT_WARN":
            soft_warn_count += 1
            pass_count += 1
            print(f"\nSOFT T{qd['tier']} #{i}: {qd['question'][:80]}")
            for gate, reason in r["soft_warns"]:
                print(f"  - {gate}: {reason}")
        else:
            pass_count += 1

    print(f"\n=== Result ===")
    print(f"PASS: {pass_count} (incl. {soft_warn_count} soft-warn)")
    print(f"FAIL: {fail_count}")

    # Also check against existing economics.json bank for dupes
    existing_path = REPO / "data" / "questions" / "economics.json"
    if existing_path.exists():
        existing = json.loads(existing_path.read_text(encoding="utf-8"))
        print(f"\nCross-check vs existing bank ({len(existing)} qs)...")
        edup, eans = build_bank_indices(existing)
        cross_fail = 0
        for i, qd in enumerate(QUESTIONS):
            r = validate_rewrite(
                "economics",
                qd,
                bank=existing,
                dup_index=edup,
                answer_index=eans,
                replace_idx=None,
            )
            if r["verdict"] == "FAIL":
                cross_fail += 1
                for gate, reason in r["hard_fails"]:
                    if gate in {"duplicate", "answer_collision"}:
                        print(f"  CROSS-{gate} T{qd['tier']} #{i}: {qd['question'][:60]}")
                        print(f"    {reason}")
        print(f"Cross-check failures (dup/collision): {cross_fail}")

    # Save
    out_path = REPO / "_gen_economics_supp_finlit_entrepreneurship.json"
    out = {
        "tier_distribution": "T1=4, T2=8, T3=12, T4=14, T5=12",
        "summary": {
            "questions_generated": len(QUESTIONS),
            "pass": pass_count,
            "soft_warn": soft_warn_count,
            "fail": fail_count,
        },
        "questions": QUESTIONS,
    }
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {out_path.name}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
