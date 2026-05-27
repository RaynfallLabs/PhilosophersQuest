"""Build 35 supplemental economics questions on Accounting + Cash Flow + Fraud Recognition.

Tier distribution: T1=2, T2=4, T3=8, T4=12, T5=9.

Voice rule: Bastiat Pattern (proposals/v2_audit/ECONOMICS_FRAMEWORK.md §1) +
§14 story-in-stem.  No dry definitional content — every question reveals an
unseen distinction (cash flow vs profit), an incentive (depreciation as
government-permitted timing trick), or a fraud-recognition skill (Enron,
Madoff, Theranos, Wirecard, WorldCom, Carillion).

Hard caps: T1=280, T2=480, T3=680, T4=900, T5=1100 (total stem+4 choices).

Save-as-you-go: validates each q() against pipeline + economics gates and
appends to _gen_economics_supp_finlit_accounting.json after every block.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

OUT = REPO / "_gen_economics_supp_finlit_accounting.json"
BANK_PATH = REPO / "data" / "questions" / "economics.json"

TIER_CAPS = {1: 280, 2: 480, 3: 680, 4: 900, 5: 1100}

QUESTIONS: list[dict] = []
ERRORS: list[str] = []


def _has_any_dash(s: str) -> bool:
    return ("—" in s) or ("–" in s) or (" -- " in s)


def q(tier: int, pillar: str, strategy: str, question: str, answer: str,
      d1: str, d2: str, d3: str, context: str) -> None:
    choices = [answer, d1, d2, d3]
    total = len(question) + sum(len(c) for c in choices)
    cap = TIER_CAPS[tier]
    if total > cap:
        ERRORS.append(f"T{tier} BUDGET {total}/{cap} ({strategy})")
        return
    ds_lens = [len(d1), len(d2), len(d3)]
    a_len = len(answer)
    if a_len > max(ds_lens) * 1.6:
        ERRORS.append(f"T{tier} PARITY-LONG ans={a_len} max_d={max(ds_lens)} ({strategy})")
        return
    if a_len * 1.6 < min(ds_lens):
        ERRORS.append(f"T{tier} PARITY-SHORT ans={a_len} min_d={min(ds_lens)} ({strategy})")
        return
    dash_flags = [_has_any_dash(c) for c in choices]
    if any(dash_flags) and not all(dash_flags):
        ERRORS.append(f"T{tier} DASH-MIX ({strategy}): {dash_flags}")
        return
    QUESTIONS.append({
        "tier": tier,
        "topic_cell": pillar,
        "question": question,
        "answer": answer,
        "choices": choices,
        "context": context,
        "_meta": {"strategy": strategy, "strategy_pillar": pillar},
    })


# ============================================================================
# T1 — grade 5 — 2 questions, cap 280
# ============================================================================

# T1 #1 — cash flow vs profit (the Bastiat distinction at the company level)
q(1, "accounting_cash_flow", "cash_flow_vs_profit_primer",
  "A bakery sold $50,000 of cakes this month on credit. Bills came due. What ran out?",
  "Cash, even though profit looked great",
  "Profit, since the cakes were sold",
  "Customers, who all stopped buying",
  "Flour, because supplies ran out",
  "A profitable business can die from running out of cash. Profit is on paper (sales minus expenses); cash is money actually in the bank. Many failed businesses had a great income statement.")

# T1 #2 — three statements primer
q(1, "accounting_statements", "three_statements_primer",
  "Three financial reports show what a company earned, what it owns, and how cash moved. The first is called what?",
  "The income statement",
  "The phone book",
  "The sales catalog",
  "The yearly calendar",
  "The three financial statements show different angles: income statement (profit), balance sheet (assets vs liabilities), cash flow statement (cash moves).")


# ============================================================================
# T2 — grade 6 — 4 questions, cap 480
# ============================================================================

# T2 #1 — accounts receivable
q(2, "accounting_cash_flow", "accounts_receivable_risk",
  "A landscaping owner sees sales growing every month, but the bank balance shrinks. Customers pay 60 days late. What is happening?",
  "Accounts receivable is growing faster than cash gets collected",
  "The company is losing money on every landscaping invoice it sends",
  "Summer customers always pay in cash and never in checks",
  "Lawn equipment depreciates faster than any landscaper can earn",
  "Accounts receivable (AR) is money customers owe but haven't paid. AR sits on the balance sheet as an asset, not cash. Growing AR + stagnant cash = selling but not collecting.")

# T2 #2 — accounts payable as free loan
q(2, "accounting_cash_flow", "accounts_payable_strategic",
  "A hardware store buys $20,000 of inventory on 60-day terms in March. The bills are due in May, but goods sell now. What's the advantage?",
  "An interest-free loan from the suppliers for 60 days",
  "A federal tax credit for buying on extended payment terms",
  "Free legal protection from any lawsuits during the window",
  "A bank guarantee against any unsold goods after the period",
  "Accounts payable (AP) is money owed to vendors. Strategic AP management is effectively an interest-free loan from suppliers — pay later, sell now.")

# T2 #3 — accounting equation primer
q(2, "accounting_basics", "accounting_equation_primer",
  "A pizza shop has $100K of equipment, owes $40K on a loan, and the owner put in $60K. The numbers fit one equation that ALWAYS holds. What is it?",
  "Assets equal liabilities plus equity, here $100K = $40K + $60K",
  "Revenue equals expenses plus profit, the bedrock of all retail",
  "Cash equals inventory plus loans, the small-business growth rule",
  "Sales equal taxes plus owner salary, in any small business model",
  "The accounting equation Assets = Liabilities + Equity is the foundation of every balance sheet. If it doesn't balance, someone made a mistake or is lying.")

# T2 #4 — depreciation primer
q(2, "accounting_cash_flow", "depreciation_primer",
  "A trucking company buys a $50,000 truck. The IRS won't let it deduct the full $50K this year. Instead, the cost spreads over the truck's useful life. What's this called?",
  "Depreciation, spreading cost across the truck's useful life",
  "Amortization, the rule for buildings spread over decades",
  "Inflation, the erosion of the truck price over the years",
  "Capitalization, issuing stock equal to the truck purchase",
  "Depreciation matches the truck's cost to the years it actually produces revenue. It's a non-cash expense — it reduces taxable income without reducing actual cash this year.")


# ============================================================================
# T3 — grade 7 — 8 questions, cap 680
# ============================================================================

# T3 #1 — cash flow vs profit deeper
q(3, "accounting_cash_flow", "cash_flow_vs_profit_deeper",
  "A growing software startup booked $2M revenue and $400K profit on paper in 2023. By December the bank held $30K and payroll was due January 5. How can a profitable company run out of cash?",
  "Growth ties cash up in receivables and inventory faster than profit appears",
  "The IRS demanded quarterly tax payments equal to all reported profit",
  "Software startups never generate cash since digital goods have no real value",
  "Profit and cash flow always match under GAAP, so the situation is impossible",
  "This is the Bastiat distinction at the company level. The seen is the great income statement; the unseen is cash tied up in receivables and capex. Many failed companies had record profit the month they died.")

# T3 #2 — EBITDA "earnings before bad stuff"
q(3, "accounting_cash_flow", "ebitda_munger_critique",
  "Wall Street loves EBITDA — Earnings Before Interest, Taxes, Depreciation, Amortization. Charlie Munger called it 'bullshit earnings.' Why the skepticism?",
  "Depreciation is real, since trucks and machines must be replaced",
  "EBITDA was banned by the SEC after Enron, so no firm uses it now",
  "EBITDA includes only manufacturing and excludes all service firms",
  "EBITDA equals net income exactly and adds no extra information",
  "EBITDA can mislead because depreciation IS a real cost — the truck wears out. Companies that brag about EBITDA growth often have terrible cash flow.")

# T3 #3 — amortization for intangibles
q(3, "accounting_basics", "amortization_intangibles",
  "When a firm buys a patent for $10M, the IRS spreads the cost over the patent's useful life. Same as depreciation, but for intangibles. What's this called, and what changed in 2001?",
  "Amortization; goodwill rules changed under FASB 142 to impairment testing",
  "Capitalization; goodwill rules required forty-year linear spreading by law",
  "Depreciation; goodwill rules matched office buildings under the IRS code",
  "Deduction; goodwill became immediately deductible in the year purchased",
  "Amortization applies to intangibles (patents, software, goodwill). FASB Statement 142 in 2001 changed goodwill from routine amortization to annual impairment testing.")

# T3 #4 — Madoff Ponzi the tell
q(3, "fraud_recognition", "madoff_ponzi_tell",
  "Bernie Madoff returned about 10% per year — every year, regardless of whether markets crashed or boomed — for at least 17 years. What was the Ponzi tell?",
  "Consistent returns regardless of market conditions, mathematically impossible",
  "Returns were too low, since Ponzi schemes always promise above 50% annually",
  "Restricted to one ethnic community, supposedly the universal Ponzi marker",
  "Filed taxes incorrectly, since the IRS catches all Ponzi frauds through audits",
  "Harry Markopolos's 2005 SEC memo 'The World's Largest Hedge Fund is a Fraud' showed the smoothness was mathematically impossible. The SEC ignored him. ~$65B notional, ~$20B real losses.")

# T3 #5 — Theranos VC due diligence failure
q(3, "fraud_recognition", "theranos_vc_dd_failure",
  "Elizabeth Holmes claimed her Edison machine could run hundreds of blood tests from a fingerprick drop. Walgreens deployed 41 wellness centers in 2013. WSJ's John Carreyrou exposed it Oct 15, 2015. What did VCs miss?",
  "The technology was physically impossible, since fingerprick samples are too small",
  "The Edison worked, but Holmes diverted profits and defrauded the company's owners",
  "Foreign export rules blocked sales, ruining a real medical-device company at scale",
  "Quest Diagnostics ran the same tests, so investors lost to ordinary competition",
  "VCs treated Theranos like software — disrupt fast, fix later. But hematology is physics: fingerprick blood is ~30 microliters; many panels need 0.5+ mL. Holmes was convicted Jan 2022.")

# T3 #6 — GAAP vs non-GAAP earnings
q(3, "accounting_basics", "gaap_vs_non_gaap_recognition",
  "US public firms report under GAAP, but many also publish 'adjusted' or 'pro forma' earnings stripping out 'non-recurring' items. Why are investors warned to compare carefully?",
  "The gap between GAAP and non-GAAP is sometimes the entire fraud",
  "Non-GAAP numbers receive more careful audit than the standard GAAP filings",
  "GAAP excludes all litigation under SEC rule; non-GAAP is more conservative",
  "Both numbers are mathematically identical so the comparison is meaningless",
  "Adjusted earnings often exclude stock-based comp, restructuring, and impairments — all real recurring costs. Munger's 'bullshit earnings' critique applies. WeWork's 2019 S-1 was a famous case.")

# T3 #7 — depreciation as government-permitted timing trick
q(3, "accounting_cash_flow", "depreciation_timing_trick",
  "The 2017 Tax Cuts and Jobs Act let businesses expense 100% of equipment in year one instead of spreading the deduction. Cash didn't change — only WHEN the deduction hit. What's the incentive game?",
  "Accelerated depreciation defers taxes; Congress uses it to steer capex timing",
  "Accelerated depreciation increases total tax over the life of the equipment",
  "Accelerated depreciation has no real effect on cash flow at any point",
  "Accelerated depreciation was banned by Sarbanes-Oxley in 2002 entirely",
  "Section 179 + bonus depreciation are government levers — incentives Congress builds into the tax code to steer capex toward chosen years. The mechanism is hidden inside an obscure tax line.")

# T3 #8 — AR risk as audit red flag
q(3, "fraud_recognition", "ar_dso_audit_red_flag",
  "Auditors watch 'days sales outstanding' (DSO) — how long customers take to pay. If DSO jumps from 45 days to 90 days while revenue stays flat, what does the auditor suspect?",
  "Either real distress, OR fake sales booked to inflate revenue figures",
  "Customers switched to crypto and accounting software can't process it",
  "DSO varies seasonally, so the metric tells the auditor exactly nothing",
  "Rising DSO indicates rising profitability through extended payment terms",
  "Rising DSO with flat revenue is a classic fraud-detection red flag. Could be loose credit, distressed customers, OR channel stuffing — booking fake sales to inflate revenue.")


# ============================================================================
# T4 — grade 8 — 12 questions, cap 900
# ============================================================================

# T4 #1 — Enron 2001 + special-purpose entities
q(4, "fraud_recognition", "enron_spe_2001",
  "Enron CFO Andy Fastow created special-purpose entities (SPEs) — off-balance-sheet partnerships named for Star Wars characters: Chewco, JEDI, LJM1, LJM2 — that hid losses and inflated reported earnings. Enron filed bankruptcy December 2, 2001. What was the structural trick?",
  "SPEs let Enron move debt off the balance sheet while keeping the revenue, so the company looked profitable and lightly-leveraged when in fact it was insolvent",
  "SPEs were legitimate and Enron used them correctly; the bankruptcy resulted from California energy-market changes rather than any accounting trick at the company",
  "SPEs let Enron pay less tax to the IRS, but the actual financial position was sound until management lost faith in the company's own near-term prospects",
  "SPEs were created by Sarbanes-Oxley in 2002 specifically to let firms hide debt; Enron only used the standard structure available to every American firm",
  "Sherron Watkins's August 2001 memo to Ken Lay warned of accounting collapse. Skilling: 24 years (later reduced). Fastow: 6 years. Lay died before sentencing. Sarbanes-Oxley July 2002 was the response.")

# T4 #2 — Andersen collapse + Big 5 to Big 4
q(4, "fraud_recognition", "arthur_andersen_collapse",
  "Arthur Andersen was one of the Big 5 accounting firms. Andersen audited Enron and was found guilty of obstruction in June 2002 for shredding Enron documents. The Supreme Court overturned the conviction in 2005, but the firm had collapsed. What does this teach?",
  "Auditors of fraud are often part of the problem, since Andersen earned $25M auditing Enron plus $27M consulting, a conflict that destroyed skepticism",
  "Arthur Andersen was innocent and did no wrong in the Enron account or other major client engagements, but the prosecution killed it before vindication arrived",
  "The Big 5 became Big 4 from routine industry consolidation unrelated to Enron or to any concerns about audit-firm independence under US securities laws",
  "Arthur Andersen survived the Enron case and still audits major US public companies today, having recovered fully from the early 2000s adverse publicity",
  "Sarbanes-Oxley 2002 created the PCAOB (Public Company Accounting Oversight Board). The Big 5 became Big 4. The structural conflict — auditors paid by the firms they audit — remains.")

# T4 #3 — Madoff Markopolos arc
q(4, "fraud_recognition", "madoff_markopolos_arc",
  "Harry Markopolos was a Boston quant. In 2000 his boss asked him to replicate Madoff's strategy. After four hours of math, Markopolos concluded the returns were impossible. He sent the SEC five formal complaints from 2000-2008 with 29 red flags. The SEC ignored him. Why?",
  "Madoff was NASDAQ chairman 1990-93 and a major figure, so capture and personal-network deference let the SEC discount outside mathematical analysis",
  "Markopolos was a crackpot whose earlier complaints had all proven baseless, so the SEC reasonably ignored his 2005 memo as just another spurious accusation",
  "The SEC lacked authority to investigate hedge funds before Dodd-Frank in 2010, so no investigation of Madoff was legally possible during this regulatory period",
  "Markopolos refused to share his analysis with the SEC, leaving the agency no way to evaluate his claims without access to the underlying work he had done",
  "Madoff confessed Dec 10, 2008; arrested Dec 11. Sentenced 150 years June 29, 2009. Died in prison April 2021. Markopolos's *No One Would Listen* (2010) documents the regulatory failure.")

# T4 #4 — Theranos Carreyrou
q(4, "fraud_recognition", "theranos_carreyrou_arc",
  "John Carreyrou of the WSJ investigated Theranos after a tip from pathologist Adam Clapper. Holmes had raised $945M at $9B; her board: Kissinger, Mattis, Shultz. The article published Oct 15, 2015. What had Carreyrou discovered?",
  "Theranos was running most tests on standard Siemens machines, diluting fingerprick samples, while the Edison itself almost never worked as Holmes had publicly claimed",
  "Theranos's technology worked but the FDA blocked rollout for political not scientific reasons; the fraud was regulatory rather than technical at the device level",
  "Theranos was profitable but concealed payments to its celebrity directors, which Carreyrou exposed as a board-compensation rather than a medical-device technology fraud",
  "Theranos had been hacked by foreign state actors who stole the technology and were running counterfeit machines, which is what the Carreyrou article exposed in October",
  "Walgreens shut centers 2016. Theranos dissolved 2018. Holmes convicted Jan 3, 2022 (11 years). Balwani: 13 years. Tyler Shultz (George's grandson) and Erika Cheung were the inside whistleblowers.")

# T4 #5 — WorldCom 2002
q(4, "fraud_recognition", "worldcom_2002",
  "WorldCom was the second-largest US long-distance carrier. In June 2002 internal auditor Cynthia Cooper found $3.8B of operating expenses had been improperly capitalized — treated as long-term assets to depreciate, not current expenses. Total fraud: $11B. Lesson?",
  "Every decade has its fraud, and the trick is often simple, since moving expenses to assets makes the income statement look healthier without changing real operations",
  "WorldCom was a victim of changing telecom rules and the accounting issues were a minor side issue unrelated to the underlying business problems at the time",
  "WorldCom's bankruptcy was caused by stock market panic rather than accounting fraud, and Bernie Ebbers was unfairly prosecuted after the macro deterioration of 2002",
  "WorldCom was actually profitable but the SEC misread its accounting under new post-Enron regulations, leading to a wrongful conviction of an innocent CEO",
  "WorldCom's collapse + Enron drove Sarbanes-Oxley July 30, 2002. Bernie Ebbers got 25 years. Cynthia Cooper was Time's 2002 Person of the Year alongside Sherron Watkins (Enron) and Coleen Rowley (FBI).")

# T4 #6 — Carillion 2018
q(4, "fraud_recognition", "carillion_2018",
  "Carillion was the UK government's biggest construction contractor. KPMG audited it. On January 15, 2018, Carillion collapsed with about $7B of undisclosed liabilities. 43,000 employees were affected. Pension deficit: ~$2.5B. What does Carillion illustrate?",
  "Government contracts can mask insolvency for years, and Big-4 audits can fail to catch growing liabilities when the auditor has many parallel commercial ties",
  "Carillion was profitable and collapsed because Brexit suddenly raised material costs in 2018, an unforeseeable external shock no audit firm could have anticipated",
  "Carillion had no accounting issues at all, since the collapse was caused entirely by sudden changes in UK government procurement after the 2017 general election",
  "Carillion was a small regional firm and the collapse had limited impact on the UK economy, affecting only construction workers in a few northern English towns",
  "Parliament's May 2018 report called Carillion's directors 'self-pitying and self-justifying' and KPMG's audit 'complicit.' UK FRC fined KPMG £14.4M in 2022. Big-4 audit reform debate intensified.")

# T4 #7 — three statements deep
q(4, "accounting_statements", "three_statements_deep",
  "Three statements describe a business. Income statement: revenue minus expenses. Balance sheet: assets minus liabilities at one moment. Cash flow statement: how cash moved. Why need all three?",
  "Each tells something different, since a firm can show paper profit and zero cash, or great assets and growing debt, or cash from selling assets while losing money",
  "The three always tell exactly the same story, so reading any one is sufficient for complete understanding of a firm's financial condition under modern accounting rules",
  "Income statement and cash flow statement are identical under GAAP, conveying identical information; the balance sheet alone adds independent information to the analysis",
  "Public companies file only the balance sheet under SEC rules; income statement and cash flow statement are internal documents unavailable to outside investors directly",
  "Reading all three is the foundation of honest financial analysis. The cash flow statement was added by FASB Statement 95 in 1987 because income statements alone hid too many cash troubles.")

# T4 #8 — accounting equation deep
q(4, "accounting_basics", "pacioli_equation_deep",
  "Luca Pacioli, a friend of Leonardo da Vinci, published 'Summa de Arithmetica' in Venice in 1494. Its section on double-entry bookkeeping is foundational. Why does Assets = Liabilities + Equity matter for fraud detection?",
  "If a balance sheet doesn't balance, someone is lying or made a mistake; the equation is a mathematical identity that catches forced numbers when an auditor checks the ledger",
  "The equation only applies to businesses founded after 1990; older firms use a different equation that does not require any balance sheet to balance arithmetically",
  "Modern accounting under GAAP replaced Pacioli's equation with a more flexible identity not requiring balance sheets to balance, freeing firms from outdated restrictions",
  "The equation requires only assets and liabilities to sum to the same number; equity is a separate calculation that has no relationship to the rest of the balance sheet",
  "Pacioli's *Summa* was printed two years after Columbus's voyage. The double-entry system spread through European merchant networks and made modern capitalism's record-keeping possible.")

# T4 #9 — EBITDA distortion deep
q(4, "accounting_cash_flow", "wework_community_ebitda",
  "WeWork's August 2019 S-1 introduced 'Community Adjusted EBITDA' — earnings before interest, taxes, depreciation, amortization, AND G&A, marketing, design, development, and pre-opening costs. The IPO was withdrawn; the firm went bankrupt 2023. What does this reveal?",
  "Each adjustment strips a real cost; adding letters to EBITDA hides more expenses, until the metric measures nothing the business actually does at all",
  "Community Adjusted EBITDA is the GAAP-required measure for co-working firms; the IPO withdrawal came from unrelated governance concerns over voting structures",
  "Community Adjusted EBITDA was invented by SoftBank as a measure of long-term portfolio performance and is now standard in venture capital fund accounting",
  "Community Adjusted EBITDA was a positive innovation that became a model for the real-estate industry following WeWork's success in the second half of 2019",
  "Charlie Munger said: 'I never look at EBITDA because I want to know about real earnings.' The IPO valuation collapsed from $47B (private) to ~$8B (target) to zero. Bankruptcy 2023.")

# T4 #10 — AP as supplier loan deep
q(4, "accounting_cash_flow", "walmart_negative_working_capital",
  "Walmart and Amazon run 'negative working capital' — they collect cash from customers BEFORE paying suppliers. Walmart's accounts payable consistently exceed inventory plus receivables. Suppliers effectively fund Walmart. What principle is at work?",
  "Large buyers have leverage to demand long payment terms, getting an interest-free working-capital loan that smaller competitors cannot match, locking in dominance",
  "Walmart actually pays suppliers in advance under standard retail terms, and the negative working capital in filings is an accounting artifact unrelated to reality",
  "Negative working capital indicates Walmart is in financial distress and unable to fund operations, which is why the firm is expected to fail in the next downturn",
  "Negative working capital results from Walmart selling on consignment with no actual ownership of inventory displayed, so the firm carries no real economic risk on sales",
  "The lever — buyer power demanding long supplier terms — is rarely discussed in retail-investor materials but explains why scale matters in low-margin retail. Suppliers compete to win shelf space.")

# T4 #11 — Sarbanes-Oxley 2002
q(4, "fraud_recognition", "sox_2002_response",
  "After Enron (Dec 2001) and WorldCom (June 2002), Congress passed Sarbanes-Oxley on July 30, 2002. It created the PCAOB, required CEO/CFO certification of financials, and Section 404 mandated internal-control attestation. What did SOX try to fix?",
  "Auditors are paid by the firms they audit, a conflict that the PCAOB and CEO certification requirements were designed to discipline through outside checks",
  "Sarbanes-Oxley made all accounting fraud impossible going forward, which is why no major US accounting fraud has been discovered or prosecuted in any decade since",
  "Sarbanes-Oxley required public firms to use only PCAOB-employed auditors, replacing private firms with a new federal agency that hired all auditors directly under it",
  "Sarbanes-Oxley required US firms to operate at break-even with no retained earnings, removing the incentive for fraud through enforced redistribution to shareholders",
  "SOX didn't eliminate fraud — see Madoff 2008, Wirecard 2020 — but raised the bar. Critics argue compliance costs hit small public companies hardest and accelerated private-equity buyouts of public firms.")

# T4 #12 — depreciation Section 179 incentive deep
q(4, "accounting_cash_flow", "depreciation_section_179_deep",
  "Section 179 lets small businesses expense up to $1.16M (2023) of equipment in year one. The 2017 TCJA added 100% bonus depreciation, phasing down. None reduce TOTAL lifetime tax — only WHEN the deduction hits. Why does Congress care about timing?",
  "Accelerated depreciation creates immediate cash incentives for businesses to buy now, letting Congress steer investment without direct subsidy in the tax code",
  "Section 179 and bonus depreciation are drafting accidents with no economic effect; the total tax liability over the asset's life is identical to ordinary depreciation",
  "Accelerated depreciation was a one-time Reagan-era provision Congress hasn't used since 1981; references in modern tax law are obsolete provisions awaiting repeal",
  "Congress uses Section 179 to discourage small business equipment purchases by raising compliance costs, freeing capital for larger corporate purchases via other rules",
  "The Cantillon principle applies — early recipients of the deferred-tax benefit are businesses with strong cash flow and tax-planning capacity. The benefit is real but distributed unevenly.")


# ============================================================================
# T5 — grade 9-10 hard ceiling — 9 questions, cap 1100
# ============================================================================

# T5 #1 — Wirecard 2020
q(5, "fraud_recognition", "wirecard_2020",
  "Wirecard was Germany's 'fintech darling' — added to the DAX 30 in 2018 with a market cap above Deutsche Bank's. EY audited for over a decade. FT journalist Dan McCrum had reported irregularities since 2015; BaFin investigated McCrum rather than Wirecard. On June 18, 2020, Wirecard admitted that €1.9B claimed in Philippine bank trustee accounts did not exist. What does Wirecard demonstrate?",
  "When even Big-4 auditors can be fooled, and regulators side with the company against journalists, the weaknesses are systemic; cash confirmations should have caught it",
  "Wirecard was a legitimate firm brought down by short-seller manipulation in the financial press, with the Philippine cash existing as claimed and the FT reporting being unfounded",
  "Wirecard's collapse was caused entirely by COVID-19 disruption to global payment processing in spring 2020, and the missing €1.9B was an accounting artifact of pandemic conditions",
  "Wirecard's accounting was accurate but the firm was a victim of regulatory failure in Singapore, where the accounts were actually held, rather than in Germany where headquartered",
  "EY paid €100M+ settlement in 2024. BaFin head Felix Hufeld resigned. COO Jan Marsalek's whereabouts (probably Moscow) remain unresolved. McCrum's *Money Men* (2022) is the canonical account.")

# T5 #2 — Enron SPE deep
q(5, "fraud_recognition", "enron_spe_chewco_ljm",
  "Enron CFO Andy Fastow's SPEs had Star Wars names — Chewco (1997), JEDI, LJM1, LJM2 (1999) — and passed GAAP's '3% outside equity' test. They let Enron move losing assets off the books while booking gains. Sherron Watkins's August 2001 memo to Ken Lay warned the firm would 'implode.' Bankruptcy Dec 2, 2001. Lesson?",
  "Fraud can be technically legal at one layer while still being fraud at the business layer; Enron's SPEs passed GAAP rules but Enron itself bore the real risk, making the off-balance-sheet treatment a fiction",
  "Enron's SPEs were illegal GAAP violations any first-year student could spot, so the fraud's persistence was entirely due to incompetent SEC staff failing to read the company's annual filings carefully",
  "Enron's SPEs were perfectly legal; the bankruptcy came from California energy deregulation that destroyed the main business, with accounting issues being a minor concern at the actual time",
  "Enron's SPEs were a governance model later firms emulated; the bankruptcy was caused by short-seller market manipulation rather than by anything actually wrong with the SPE structures used",
  "Skilling: 24 years (reduced to 14, released 2019). Fastow: 6 years (cooperated). Lay died July 5, 2006 awaiting sentencing. Bethany McLean's March 2001 Fortune piece 'Is Enron Overpriced?' was the first major skeptic article.")

# T5 #3 — Madoff 47-year arc
q(5, "fraud_recognition", "madoff_47_year_arc",
  "Bernie Madoff's Ponzi ran at least 17 years (proven), possibly 47 (disputed). Peak: ~$65B notional, ~$20B losses. Returns averaged 10-12% with extraordinarily smooth equity curves. The SEC dismissed Markopolos's complaints in 2000, 2001, 2005, 2007, 2008. Madoff confessed Dec 10, 2008 only after the crash drained cash. What does it reveal about regulator capture?",
  "Madoff was NASDAQ chairman (1990-93), an SEC advisory member, and a major political donor; regulators couldn't imagine a respected insider was a fraudster, so they investigated his accusers instead",
  "Madoff's scheme was undetectable by any rational analysis, so the SEC's failure was inevitable and reflects no broader pattern about vulnerability to high-status fraud in finance",
  "Madoff's scheme would have been caught much earlier under modern Dodd-Frank rules (2010), which closed the regulatory gaps that let the fraud continue for as long as it did",
  "Madoff's scheme operated outside SEC jurisdiction since hedge funds were exempt from SEC oversight at the time, so the agency had no power to investigate his advisory business",
  "Sentenced 150 years June 29, 2009. Died April 14, 2021, age 82. Son Mark Madoff hanged himself Dec 11, 2010 (anniversary of arrest). The Madoff Recovery Initiative has clawed back ~$14B.")

# T5 #4 — Theranos VC due diligence deep
q(5, "fraud_recognition", "theranos_vc_dd_deep",
  "Theranos raised $945M at a $9B peak. Investors: Draper, Ellison, Murdoch ($125M lost), the Waltons, DeVos, Carlos Slim. Board: Kissinger, Mattis, Shultz, Perry, Nunn — none with medical-device expertise. No tier-one VC (Sequoia, Kleiner, Benchmark, Andreessen) invested — they spotted the physical impossibility. Why did sophisticated investors miss it?",
  "Famous board members substituted for technical due diligence; Kissinger doesn't audit blood machines, and Theranos investors trusted social proof rather than asking practicing hematologists",
  "Tier-one VCs missed Theranos because they had ethical objections to medical-device investing rather than because they identified the physical impossibility at the heart of the central claim",
  "Theranos technology worked in early demos but degraded from manufacturing issues, which sophisticated VCs had no way to predict during their due diligence before the Walgreens rollout",
  "Theranos's investors all bought in late after Walgreens deployed centers; early investors who did proper due diligence had already exited successfully before public technology problems",
  "Holmes: convicted Jan 3, 2022 (4 counts). Sentenced 11 years 3 months Nov 18, 2022. Balwani: 13 years. George Shultz (who defended Holmes against own grandson Tyler) died Feb 2021. Carreyrou's *Bad Blood* (2018) is canonical.")

# T5 #5 — GAAP vs non-GAAP earnings arc
q(5, "accounting_basics", "gaap_vs_non_gaap_arc",
  "FASB has overseen GAAP since 1973. The SEC requires GAAP filings, but since the late 1990s firms also report 'non-GAAP' earnings stripping items management calls 'non-recurring.' Reg G (2003) requires reconciliation but doesn't ban it. By 2015 S&P 500 non-GAAP ran ~25% above GAAP. What does the gap reveal?",
  "The gap is sometimes the entire fraud; Munger called it 'bullshit earnings'; the costs stripped (stock-based comp, restructuring, impairments) are real costs that recur every year despite being labeled non-recurring",
  "Non-GAAP earnings give a more accurate picture of business performance, which is why sophisticated investors rely on them rather than GAAP when making investment decisions in equity markets",
  "The gap reflects GAAP's inadequacy for modern intangible-heavy businesses, and FASB has been working to align GAAP with non-GAAP measures over the past two decades through ongoing standards-setting",
  "The gap is purely a result of stock-based comp under FASB 123R (2006), and would close completely if that single rule were repealed under future FASB updates to the standards-setting process",
  "WeWork's 'Community Adjusted EBITDA' (2019) was the reductio ad absurdum — once you adjust EBITDA itself, the metric measures nothing. Stock-based comp is the largest single category of non-GAAP adjustment for tech firms.")

# T5 #6 — Carillion + Big 4 audit reform
q(5, "fraud_recognition", "carillion_big4_reform",
  "Carillion's January 15, 2018 collapse exposed UK Big-4 problems. KPMG audited since 1999 — 19 years no rotation. The UK FRC fined KPMG £14.4M in May 2022. The Brydon Review (2019), Kingman (2018), and CMA study (2018-19) all recommended audit-firm rotation, audit-only firms, and joint audit. Why have reforms moved slowly?",
  "The Big 4 lobby against structural reform; audit is bundled with profitable consulting, and breaking the bundle cuts Big-4 profitability while politicians depend on Big-4 advice on the reforms themselves",
  "Reforms haven't moved because UK press and parliament have not been concerned about Carillion's collapse or about KPMG's role in failing to detect the company's substantial undisclosed liabilities",
  "Reforms are already fully implemented in the UK, including mandatory audit-firm rotation every five years and complete separation of audit from consulting across all Big-4 firms since 2019",
  "The Brydon, Kingman, and CMA reviews concluded no structural reform was needed and the Carillion case was an isolated incident not reflective of broader problems in the UK Big-4 audit market",
  "The structural conflict — auditors paid by the companies they audit, with consulting fees often exceeding audit fees — exists in the US (PCAOB-overseen) and globally. Carillion's lessons remain only partly absorbed.")

# T5 #7 — Bernie Ebbers + WorldCom deep
q(5, "fraud_recognition", "worldcom_ebbers_deep",
  "Bernard Ebbers grew WorldCom from a Mississippi reseller to the second-largest US carrier via 65+ deals, peaking at $37B with 1998 MCI. Internal auditor Cooper investigated March 2002. She found $3.8B of operating expenses improperly capitalized — moved to the balance sheet as assets. Lesson?",
  "Accounting fraud doesn't need complex SPEs; a simple reclassification (expense to asset) hides billions, transforming the income statement instantly while the balance-sheet impact buries among long-term assets",
  "WorldCom's fraud was vastly more sophisticated than Enron's and required tools not previously available to corporate finance, which is why no comparable fraud has been detected since the 2002 SEC probe",
  "WorldCom wasn't actually fraudulent, since the SEC misapplied a standard to a legitimate decision; Bernie Ebbers was wrongfully convicted in a post-Enron politically motivated prosecution from the agency",
  "WorldCom's collapse was caused by the dot-com bubble not fraud; the $11B figure is an artifact of post-collapse forensic accounting miscategorizing routine telecom charges from operations",
  "Ebbers: 25 years July 13, 2005. Died Feb 2, 2020, age 78. Cynthia Cooper's *Extraordinary Circumstances* (2008) is the insider account. Time's Persons of the Year 2002: Cooper, Watkins, Rowley. SOX July 30, 2002 was the response.")

# T5 #8 — depreciation Cantillon
q(5, "accounting_cash_flow", "depreciation_cantillon_deep",
  "Section 179 lets small businesses expense up to $1.16M (2023) of equipment in year one. The 2017 TCJA added 100% bonus depreciation, phasing down: 80% (2023), 60% (2024), 40% (2025), 20% (2026), zero (2027). None reduce lifetime tax — only timing. Why does Congress care?",
  "Time value of money, since a deduction today is worth more than the same deduction spread across five years; Congress uses timing levers to steer capex without using obvious direct subsidies",
  "Congress includes accelerated depreciation to reduce the workload of IRS auditors, who would otherwise monitor each year's portion of multi-year depreciation across millions of small businesses every tax year",
  "Accelerated depreciation has no economic effect since rational businesses are indifferent between immediate and deferred deductions; Congress includes the provisions for political-appearance reasons unrelated to tax",
  "Section 179 is a vestigial provision from World War II rules not updated since 1945, and contemporary references to it reflect oversight in legislative housekeeping rather than active policy",
  "The Cantillon principle applies — businesses with tax-planning capacity and strong year-end cash flow capture the timing benefits while smaller competitors don't optimize. Each TCJA phase-down year creates a 'use it now' incentive.")

# T5 #9 — Pacioli + double-entry foundation
q(5, "accounting_basics", "pacioli_double_entry_foundation",
  "Franciscan friar Luca Pacioli, friend of Leonardo da Vinci (he taught Leonardo math in Milan ~1496-99), published 'Summa de Arithmetica' in Venice 1494 — two years after Columbus. Its double-entry section documented Venetian merchant practice from the 13th-14th centuries. Why does it matter today?",
  "It creates a mathematical identity (every debit has an equal credit; assets equal liabilities plus equity) that catches errors and forces consistency; without it the scale of modern capitalism was impossible",
  "Double-entry was rendered obsolete by modern computer accounting in the 1980s, and references in current accounting textbooks are artifacts kept for cultural reasons rather than practical importance",
  "Double-entry is a uniquely Italian practice never adopted outside southern Europe; modern accounting in the US and UK uses a different framework descended from Anglo-Saxon merchant traditions",
  "Double-entry was a minor administrative practice with no significant impact on European commerce or capitalism, and attention to Pacioli reflects 19th-century romanticization rather than real contribution",
  "Werner Sombart called double-entry one of 'the most beautiful inventions of the human mind.' Max Weber linked it to rational capitalism. Joseph Schumpeter called it capitalism's defining intellectual technology. 530 years of unbroken use.")


# ============================================================================
# Save + validate
# ============================================================================

def main():
    if ERRORS:
        print(f"[FAIL] {len(ERRORS)} drafting errors caught at q() time:")
        for e in ERRORS:
            print(f"  {e}")
        sys.exit(1)

    print(f"[OK] {len(QUESTIONS)} questions passed initial budget/parity/dash checks")

    # Load bank for dup/collision indices
    with open(BANK_PATH, encoding="utf-8") as f:
        bank = json.load(f)
    print(f"[OK] loaded {len(bank)} existing economics questions")

    dup_idx, ans_idx = build_bank_indices(bank)

    # Validate each question through the full gate pipeline
    failed = []
    soft = []
    for i, qd in enumerate(QUESTIONS):
        # Strip our _meta + topic_cell before validation (not part of the schema)
        clean = {k: v for k, v in qd.items() if k in ("tier", "question", "answer", "choices", "context")}
        verdict = validate_rewrite("economics", clean, bank=bank, dup_index=dup_idx,
                                   answer_index=ans_idx, replace_idx=None)
        if verdict["verdict"] == "FAIL":
            failed.append((i, qd["_meta"]["strategy"], verdict["hard_fails"]))
        elif verdict["verdict"] == "SOFT_WARN":
            soft.append((i, qd["_meta"]["strategy"], verdict["soft_warns"]))

    if failed:
        print(f"\n[FAIL] {len(failed)} hard-fail validations:")
        for idx, strat, fails in failed:
            print(f"  T{QUESTIONS[idx]['tier']} #{idx} {strat}: {fails}")

    if soft:
        print(f"\n[SOFT] {len(soft)} soft-warn validations:")
        for idx, strat, warns in soft:
            print(f"  T{QUESTIONS[idx]['tier']} #{idx} {strat}: {warns}")

    # Tier distribution check
    by_tier = {}
    for qd in QUESTIONS:
        by_tier[qd["tier"]] = by_tier.get(qd["tier"], 0) + 1
    print(f"\n[INFO] Tier distribution: {dict(sorted(by_tier.items()))}")

    # Write output (always — even if some fail, so we can inspect)
    output = {
        "tier_distribution": "T1=2, T2=4, T3=8, T4=12, T5=9",
        "summary": {"questions_generated": len(QUESTIONS),
                    "hard_fails": len(failed),
                    "soft_warns": len(soft)},
        "questions": QUESTIONS,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n[WROTE] {OUT}")

    if failed:
        sys.exit(2)


if __name__ == "__main__":
    main()
