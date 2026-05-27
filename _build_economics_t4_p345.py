"""Build 120 fresh Tier-4 economics questions across P3/P4/P5.

  P3 Sound Money + Hyperinflation: 42
  P4 Central Banking + Keynes/MMT critique: 43
  P5 Practical Economics: 35

Voice rule: Bastiat Pattern (proposals/v2_audit/ECONOMICS_FRAMEWORK.md §1).
T4 cap 900 chars total (stem + 4 choices). Grace 945. Dash uniformity required.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

OUT = REPO / "_gen_economics_t4_p345.json"
BANK_PATH = REPO / "data" / "questions" / "economics.json"

QUESTIONS: list[dict] = []
ERRORS: list[str] = []


def _has_any_dash(s: str) -> bool:
    return ("—" in s) or ("–" in s) or (" -- " in s)


def q(pillar: str, strategy: str, question: str, answer: str, d1: str, d2: str, d3: str, context: str) -> None:
    choices = [answer, d1, d2, d3]
    total = len(question) + sum(len(c) for c in choices)
    if total > 900:
        ERRORS.append(f"BUDGET {total} ({strategy})")
        return
    ds_lens = [len(d1), len(d2), len(d3)]
    a_len = len(answer)
    if a_len > max(ds_lens) * 1.6:
        ERRORS.append(f"PARITY-LONG ans={a_len} max_d={max(ds_lens)} ({strategy})")
        return
    if a_len * 1.6 < min(ds_lens):
        ERRORS.append(f"PARITY-SHORT ans={a_len} min_d={min(ds_lens)} ({strategy})")
        return
    dash_flags = [_has_any_dash(c) for c in choices]
    if any(dash_flags) and not all(dash_flags):
        ERRORS.append(f"DASH-MIX ({strategy}): {dash_flags}")
        return
    QUESTIONS.append({
        "tier": 4,
        "topic_cell": pillar,
        "question": question,
        "answer": answer,
        "choices": choices,
        "context": context,
        "_meta": {"strategy": strategy, "strategy_pillar": pillar},
    })


# ============================================================================
# P3 SOUND MONEY + HYPERINFLATION (42 questions)
# ============================================================================

q("sound_money_history", "weimar_papermark_peak_1923",
  "Weimar Germany's hyperinflation peaked November 1923. A dollar traded for 4.2 trillion marks. Wages were paid twice daily — afternoon money was worth less than morning. Workers carried earnings in wheelbarrows. What ended the inflation that month?",
  "The Rentenmark replaced the papermark on Nov 15, backed by a notional land mortgage, and printing stopped",
  "France withdrew Ruhr occupation forces, and German industrial output recovered with no currency change",
  "Versailles reparations were canceled by the Allies, removing the underlying political pressure on Berlin",
  "The League of Nations shipped gold to Berlin, and prices stabilized within a single trading week",
  "Schacht's Rentenmark issuance on November 15, 1923 ended the inflation by halting printing. The trillion-to-one ratio cleared the slate. Reparations were renegotiated separately via the Dawes Plan in 1924.")

q("sound_money_history", "weimar_havenstein_printing",
  "Rudolf Havenstein, Reichsbank president from 1908 until his death in November 1923, bragged in summer 1923 about expanding printing capacity. 132 printing companies and 1,783 presses ran around the clock. What did Havenstein insist caused the inflation?",
  "Balance of payments and reparations demands, not the Reichsbank's own runaway monetary expansion",
  "Excess wage demands by German unions, not central bank decisions about money supply expansion",
  "Speculative attacks by Anglo-American hedge funds, not Reichsbank coordinated note issuance policies",
  "Hoarding of bread by Bavarian farmers, not the central bank's accelerating production of currency",
  "Havenstein's denial that printing causes inflation is the canonical case of central-bank epistemic capture. He died Nov 20, 1923; Schacht stabilized the currency within days.")

q("sound_money_history", "weimar_wheelbarrow_burn_marks",
  "By autumn 1923 in Berlin, mark notes were used as wallpaper, lit as kindling, and given to children as blocks. A single egg cost 80 billion marks. The famous photograph of a woman feeding bills into her stove was a literal cost calculation. What was the calculation?",
  "Banknotes had become cheaper per gram than firewood, so burning currency for heat was rational",
  "She was protesting Versailles by destroying her savings as a public symbolic act of defiance",
  "Marks burned hotter than wood pulp due to ink content, producing higher temperatures per unit",
  "She was destroying counterfeit notes seized by police during a raid on her neighborhood",
  "The economic decision encoded in the photograph: when money loses value faster than goods, the public flees money for any tangible substitute, including burning it.")

q("sound_money_history", "weimar_political_aftermath",
  "The 1923 hyperinflation destroyed German middle-class savings in months. Bonds, insurance, pensions, and bank deposits were wiped to almost nothing. Hitler's Beer Hall Putsch attempt occurred November 8-9, 1923, in Munich during the peak. What did Bresciani-Turroni (1937) emphasize?",
  "Destroying a property-owning middle class left the population susceptible to political extremism promising order",
  "The hyperinflation directly funded Hitler's NSDAP coffers since printed marks were channeled to the party",
  "Hitler personally argued for the Rentenmark stabilization in November 1923 as his first national position",
  "Reichsbank gold reserves were transferred to NSDAP control during the putsch, financing later expansion",
  "Bresciani-Turroni's *Economics of Inflation* (1937) is the canonical study. Destruction of savings removed buffers against radical politics; it loaded the gun without firing it.")

q("sound_money_history", "hungarian_pengo_peak_july_1946",
  "Hungary's pengo hyperinflation of 1945-46 set the all-time world record. By July 1946 prices doubled every 15 hours. The largest banknote printed was the 100 quintillion pengo note (1 followed by 20 zeros). What replaced the pengo on August 1, 1946?",
  "The forint, issued at 400 octillion pengo to one forint, backed by gold reserves and stabilization aid",
  "The Hungarian zloty, issued at parity with the Polish currency under Soviet bloc monetary coordination",
  "The Reichsmark zone was extended into Hungary at the rate of the occupied Austrian zone of the period",
  "The pre-war pengo was restored at face value after a thousand-to-one currency revaluation policy",
  "The forint was introduced August 1, 1946, at the world-record exchange ratio. Peak monthly inflation hit 4.19 quintillion percent — surpassing Weimar, Zimbabwe, and Yugoslavia.")

q("sound_money_history", "hungarian_adopengo_index",
  "By spring 1946 the pengo had collapsed so completely that Hungary invented a parallel unit called the adopengo (tax-pengo) for collecting state revenue. Its value was recalculated daily against the pengo. What did this indexing expose?",
  "Money cannot function as a unit of account when inflation exceeds daily doubling, forcing an internal alternative",
  "The National Bank discovered a new method for stabilizing currency through dual-track indexation widely",
  "Soviet occupation mandated daily-adjusted currency to prevent black-market exchanges with US dollars",
  "Hyperinflation can be solved internally without abandoning the underlying currency through accounting",
  "Money's three functions (exchange, unit of account, store of value) collapse in sequence. The adopengo proved the pengo had ceased functioning as a unit of account, the final stage before abandonment.")

q("sound_money_history", "zimbabwe_100tn_print_jan_2009",
  "Zimbabwe's Reserve Bank under Gideon Gono printed the 100-trillion-dollar note in January 2009. By the time printing finished, the bill bought one loaf of bread. Peak monthly inflation hit 89.7 sextillion percent in November 2008. What did Zimbabwe do in April 2009?",
  "Abandoned its own currency entirely; let US dollars, South African rand, and Botswana pula be legal tender",
  "Issued a 1000-trillion-dollar note backed by Victoria Falls bonds, restoring confidence in weeks",
  "Pegged the Zimbabwe dollar to the Chinese yuan at a fixed daily rate set by the People's Bank",
  "Restarted gold mining as national priority and backed each note with ounces from the Great Dyke",
  "Zimbabwe officially dollarized in April 2009. A new Zimbabwe dollar reappeared briefly in 2019 then collapsed. ZiG launched April 2024 also struggled. Fiat dies historically without exception.")

q("sound_money_history", "zimbabwe_gono_quotes",
  "Gideon Gono, Zimbabwe's central bank governor 2003-2013, wrote a 2008 book defending the policy. He blamed foreign sanctions, drought, and global capitalism for inflation — never the printing presses he authorized. What did the historical record actually show?",
  "Mugabe's land reform destroyed exports while Gono printed to fund deficits, and the printing caused inflation",
  "European Union sanctions caused the entire inflation episode, exactly as Gono had publicly explained",
  "Southern African drought reduced food production enough to explain hundred-trillion-percent inflation",
  "Global capitalism's natural cycles produced the inflation, as Gono argued in his book and conferences",
  "Cantillon effect at extreme: the regime printed to pay soldiers, officials, and loyalists. Inflation transferred wealth from savers (late) to insiders (early) before total collapse.")

q("sound_money_history", "venezuela_bolivar_soberano_2018",
  "Venezuela under Maduro hit hyperinflation in late 2017. In August 2018 the government issued the bolívar soberano, knocking five zeros off the old bolívar. By 2021 they knocked six more zeros off. What did Mises 1920 predict about regimes like this?",
  "Without market prices under expropriation, no rational allocation is possible and shortages must follow",
  "Currency redenomination always succeeds at stopping inflation when accompanied by political commitment",
  "Socialist regimes outperform capitalist ones in output per capita, as Maduro's economic team argued",
  "Hyperinflation is a Western media fabrication; citizens' purchasing power improved via state subsidies",
  "Mises 1920 'Economic Calculation in the Socialist Commonwealth' predicted this trajectory. Expropriation removed price signals needed for calculation; hyperinflation completed what nationalization began.")

q("sound_money_history", "venezuela_dollarization_de_facto",
  "By 2020-2021 Venezuela was de facto dollarized. About 60-70% of transactions used US dollars. Maduro himself admitted in November 2019 that dollarization had become 'an escape valve' for the economy. What does this concession illustrate?",
  "Citizens abandon a hyperinflating currency before the government does, voting with their wallets against the regime",
  "Dollarization always restores price stability immediately once a government announces a switch from local",
  "The Federal Reserve provides direct subsidies to dollarizing countries through bilateral swap lines worldwide",
  "Hyperinflation is reversible if a central bank simply prints fewer notes for one calendar quarter ever",
  "Hayek's *Denationalisation of Money* (1976) argued for currency competition. Venezuelans showed in practice: given the option, people choose better money. The bolívar lost the competition.")

q("sound_money_history", "lebanon_pound_collapse_2020",
  "Lebanon's pound was pegged to the dollar at 1507 LBP for 23 years. In October 2019 protests erupted; in March 2020 Lebanon defaulted on sovereign debt. By 2023 the pound traded around 90,000 LBP per dollar — a 98% collapse in three years. What was the mechanism?",
  "Banque du Liban ran a Ponzi-style scheme paying high interest with new deposits until fresh dollars stopped",
  "An earthquake in Beirut in October 2019 caused the entire currency collapse with no policy errors involved",
  "Saudi Arabia withdrew dollar reserves in a single day in 2020, triggering a one-time liquidity crisis",
  "The COVID pandemic alone explains the entire Lebanese collapse since monetary authorities ran sound policy",
  "Lebanon depended on dollar inflows from diaspora and oil-state deposits. Riad Salameh's central bank used new deposits to pay returns on old. The Aug 4, 2020 Beirut port blast accelerated but did not cause collapse.")

q("sound_money_history", "argentina_milei_election_dec_2023",
  "Argentina hit 211% annual inflation by December 2023. Voters elected Javier Milei, a libertarian anarcho-capitalist economist, as president on Dec 10, 2023. Milei brought a chainsaw to rallies symbolizing state spending cuts. What was the IMF's posture?",
  "Supportive of rapid devaluation and spending cuts, since deficits and money printing had caused the inflation",
  "Hostile to cuts since IMF orthodoxy favored gradualism and broad social-spending preservation continued",
  "Indifferent to Argentine policy since the country had already exited the IMF program in 2022 entirely",
  "Critical of dollarization plans since gradualist gold-backed reform was the only sustainable path possible",
  "Milei's first year saw inflation falling from the December 2023 peak as deficit spending was cut. The IMF welcomed shock therapy. Legitimacy came from voter pain at the gradualist alternative.")

q("sound_money_history", "argentina_inflation_recurrent_history",
  "Argentina suffered hyperinflation in 1989-90 (over 3000% peak), the late 1970s, and again in the 2020s. The country adopted a hard dollar peg in 1991 (Convertibility Plan) that worked until the 2001-02 crisis broke it. What does this repeated pattern teach?",
  "Pegs collapse when domestic political authorities retain power to break them; only structural constraints work",
  "Argentina's pattern proves any monetary regime can produce hyperinflation given enough time across history",
  "Currency boards always fail within ten years, as the 1991-2001 Argentine experience clearly demonstrates",
  "Argentine geographic position makes monetary stability impossible due to commodity export dependence widely",
  "Hayek and Selgin argued for genuine institutional constraint. Every restraint that can be undone politically eventually is. Dollarization removes the option; a currency board does not.")

q("sound_money_history", "yugoslav_dinar_1994_peak",
  "Federal Republic of Yugoslavia experienced one of history's worst hyperinflations 1992-January 1994. Monthly inflation peaked at 313 million percent in January 1994. Slobodan Milošević used printing to fund Balkan war operations. What ended it?",
  "Dragoslav Avramović introduced the new dinar pegged to the deutsche mark on January 24, 1994, and printing stopped",
  "NATO bombing of Belgrade in January 1994 destroyed the printing facility, ending hyperinflation through loss",
  "The European Central Bank assumed authority over Yugoslav policy in early 1994, replacing the dinar with euro",
  "Russian Federation sent gold reserves to Belgrade for currency backing under treaty by Yeltsin and Milošević",
  "The 'super dinar' stabilization of January 24, 1994 worked because the central bank stopped printing. Avramović became known as 'Super Grandpa.' Hyperinflation ends when printing stops.")

q("sound_money_history", "continental_currency_collapse_1779",
  "Continental Congress issued paper money called Continentals starting June 1775 to fund the Revolutionary War. By 1779 a Continental dollar was worth about 1/40 of face value in silver. The phrase 'not worth a Continental' entered American English. What did this produce in the Constitution?",
  "The clause forbidding states from issuing bills of credit (Art I sec 10), reflecting founders' direct experience",
  "The provision establishing the Federal Reserve System for managing future monetary policy through experts",
  "The requirement that all federal taxes be paid in gold rather than silver, designed by Hamilton at convention",
  "The clause permitting unlimited state currency issuance, designed to allow flexible regional responses",
  "Constitution's monetary clauses reflect founders' bitter experience with Continental inflation. Hamilton's 1791 Mint Act anchored the dollar in silver and gold; that lasted until the Civil War.")

q("sound_money_history", "french_assignats_1796_collapse",
  "Revolutionary France issued paper money called assignats starting December 1789. Officially backed by confiscated Church lands. The Assembly promised assignats would be retired as land was sold. By 1796 over 45 billion circulated, worth perhaps 1% of face value. What happened to the 'backing'?",
  "Successive governments issued assignats far in excess of available land, and printing replaced retirement",
  "Foreign powers seized the French church lands during the war, removing the assignat backing entirely",
  "The land sold below estimated value because French peasants refused to bid in revolutionary markets",
  "The Catholic Church successfully sued in revolutionary courts to recover its lands on legal grounds",
  "Andrew Dickson White's *Fiat Money Inflation in France* (1896) is the canonical history. Each successive issue diluted the 'backing' to fiction. The mandat territorial that replaced it collapsed faster.")

q("sound_money_history", "john_law_mississippi_1720_crash",
  "John Law, a Scottish gambler and financier, persuaded the French regent in 1716 to establish the Banque Générale, the first central bank in France. By 1719 his Mississippi Company stock had risen tenfold. By December 1720 the system had crashed. What was the mechanism?",
  "Law printed banknotes to buy Mississippi Company shares, inflating prices that justified more issuance",
  "Mississippi Company gold mines were nationalized by the regent in 1720, removing the asset backing",
  "British East India Company spies poisoned Law's reputation in Paris, causing investor flight in 1720",
  "A massive Mississippi River flood in 1719 destroyed company operations in Louisiana, ending the business",
  "Law's scheme is the first modern fiat-money-asset-inflation cycle. Note issuance fed share prices fed note issuance. Richard Cantillon knew Law personally and described the pattern that bears his name.")

q("sound_money_history", "roman_denarius_silver_decline",
  "The Roman denarius began under Augustus around 27 BC at about 95% silver content. Under Nero (54-68 AD) silver dropped to roughly 90%. Under Gallienus (253-268 AD) the denarius was about 5% silver — bronze with a silver wash. Prices in Rome rose dramatically. What was the driver?",
  "Emperors funded military campaigns and grain doles by reducing silver content rather than raising taxes",
  "Silver mines in Spain were exhausted by the 3rd century AD, forcing emperors to use bronze regardless",
  "Christianity's spread reduced commercial exchange, lowering silver demand and producing apparent debasement",
  "Trade with India and China drained silver out of Rome at constant coin weight, with no actual debasement",
  "Diocletian's Edict on Maximum Prices (301 AD) tried price controls; they failed. The pattern: debasement leads to price spikes leads to controls leads to black markets leads to instability.")

q("sound_money_history", "bretton_woods_keynes_vs_white",
  "At the Bretton Woods conference (July 1-22, 1944), 730 delegates from 44 Allied nations negotiated the postwar monetary order. Keynes (Britain) proposed an international clearing union and a synthetic currency called the bancor. Harry Dexter White (US Treasury) proposed a dollar-centered system backed by gold. Who won?",
  "White — the dollar became reserve currency at $35/oz, with other currencies pegged to the dollar",
  "Keynes — the bancor became the international reserve currency from 1944 through Nixon's gold close",
  "Both — plans were combined into a hybrid system with IMF using SDRs as primary reserve from start",
  "Neither — the conference ended without agreement, and bilateral arrangements governed postwar trade",
  "White's victory reflected US economic dominance — the US held about two-thirds of world gold reserves in 1944. White was later credibly accused of being a Soviet agent; he died days after testifying before HUAC.")

q("sound_money_history", "nixon_august_15_1971_deep",
  "Nixon's August 15, 1971 announcement closing the gold window was developed at Camp David Aug 13-15. The plan included wage and price controls plus a 10% import surcharge. Treasury Secretary Connally said: 'It's our currency but your problem.' What was the immediate Monday reaction?",
  "Foreign currencies floated higher against the dollar; the world entered a fiat regime that has continued since",
  "Gold prices fell sharply as markets assumed Nixon would soon reverse course and restore convertibility",
  "European nations refused dollars for the following week and demanded immediate redemption in gold instead",
  "Stock markets closed across Europe for three weeks until Bretton Woods was officially terminated by treaty",
  "The 1971 'Nixon shock' ended any link between major currencies and gold. The Smithsonian Agreement (Dec 1971) tried a new fixed-rate system; it collapsed by 1973. Pure fiat began; 1970s inflation reached 13.5%.")

q("sound_money_history", "classical_gold_standard_1870_1914",
  "The classical gold standard ran from roughly 1870 to August 1914 — almost half a century of stable prices, free capital flows, and convertibility. Britain, France, Germany, the US fixed currencies to gold. WWI broke it as belligerents suspended convertibility. What about interwar restoration?",
  "Britain returned to gold in 1925 at prewar parity; the resulting deflation contributed to depression and abandonment in 1931",
  "The interwar gold standard worked smoothly until 1939 and ended only because of the outbreak of WWII",
  "The League of Nations enforced a uniform global gold standard from 1920 through 1939 with no deviation",
  "Interwar gold was replaced by a sterling currency bloc that operated successfully through the Depression",
  "Keynes's 1925 pamphlet *The Economic Consequences of Mr. Churchill* argued the 1925 parity was overvalued. Britain left gold September 21, 1931. The US suspended convertibility April 1933.")

q("sound_money_history", "saifedean_bitcoin_standard_2018",
  "Saifedean Ammous's *The Bitcoin Standard* (2018) became the most-cited Austrian case for Bitcoin as the modern sound-money answer. Ammous argues sound money is characterized by 'stock-to-flow' — existing supply over annual new supply. Gold's S2F is about 60. What is Bitcoin's after 2024 halving?",
  "About 120, making Bitcoin the highest stock-to-flow asset in history, roughly twice gold's ratio going forward",
  "About 20, making Bitcoin only one-third as scarce as gold by the standard commodity economics measurement",
  "About 5, making Bitcoin roughly equivalent to industrial copper in monetary scarcity by Austrian theory",
  "About 1, meaning new Bitcoin supply roughly equals existing stock annually, similar to most fiat currencies",
  "After April 2024 halving Bitcoin's annual issuance dropped to about 0.85% of existing supply, pushing stock-to-flow above 100 and toward 120. The 21M cap is hard. Programmatic scarcity is the sound-money answer.")

q("sound_money_history", "lyn_alden_broken_money_2023",
  "Lyn Alden's *Broken Money* (2023) traces monetary technology from shells through gold, fiat, and Bitcoin. Central thesis: money is a technology, and technologies improve. Alden argues 20th-century fiat was a regression because settlement got centralized when gold left. What does Bitcoin restore?",
  "Settlement assurance without trusted intermediaries, bearer money in digital form, settling globally in minutes",
  "Convertibility into physical gold on demand at a fixed exchange rate set by treaty between sovereign nations",
  "The gold standard exactly as practiced from 1870 to 1914 between the major industrial economies at parity",
  "Central-bank-issued reserve currency status for the US dollar through digital integration with Fed notes",
  "Alden's argument: 1971 fiat happened because settlement requires either a physical thing (gold) or a network. Pre-internet networks were too slow. Bitcoin is the bearer-asset network gold couldn't be globally.")

q("sound_money_history", "jeff_booth_price_of_tomorrow_2020",
  "Jeff Booth's *The Price of Tomorrow* (2020) argues that technology is inherently deflationary — it makes things cheaper, faster, better. Central banks fight this deflation by inflating, creating distortions benefiting asset-holders. What does Booth recommend?",
  "Allow technological deflation to deliver lower prices to consumers instead of inflating to mask productivity gains",
  "Raise the inflation target above 2% to fully absorb deflationary pressure from artificial intelligence widely",
  "Implement universal basic income funded by central-bank printing to redistribute gains from automation broadly",
  "Ban automation in core industries to preserve wage levels and prevent deflationary pressure from disrupting policy",
  "Booth's argument intersects with Bitcoin economics: programmatic supply caps let prices reflect productivity gains. Hayek would recognize the move. The 2% inflation target is a 1990s New Zealand artifact.")

q("sound_money_history", "stock_to_flow_gold_vs_fiat",
  "Stock-to-flow is the standard Austrian measure of monetary scarcity: existing supply divided by annual new supply. Above-ground gold grows about 1.5% per year (ratio about 60). Silver adds about 7% per year (ratio near 22). What is the central monetary problem with fiat under this measure?",
  "Central banks can expand supply at will, so fiat stock-to-flow approaches zero whenever political incentives push",
  "Fiat currencies have a fixed stock-to-flow ratio of approximately 100, making them more scarce than gold widely",
  "Fiat stock-to-flow rises during recessions as banks reduce lending, making fiat naturally counter-cyclical reserve",
  "The stock-to-flow concept does not apply to fiat money since paper currency is not mined ever in production",
  "The discretionary power of central banks is the structural defect. Even nominally 'tight' policy can be reversed at the next meeting. Hayek's *Denationalisation of Money* argued for currency competition to remove this.")

q("sound_money_history", "weimar_vs_zimbabwe_speed",
  "Comparing peak monthly rates: Hungary (Jul 1946) hit 4.19 quintillion percent, Zimbabwe (Nov 2008) hit 89.7 sextillion percent, Yugoslavia (Jan 1994) hit 313 million percent, Weimar (Oct 1923) hit 29,500 percent. What does the consistency of mechanism demonstrate?",
  "Every case involved a government printing to fund deficits beyond its capacity to tax, validating Mises's 1912 theory",
  "Each hyperinflation had a unique cause specific to that country's political conditions, with no shared mechanism",
  "Hyperinflations only occur in defeated nations after losing wars, since the four cases all followed catastrophes",
  "Hyperinflation requires both printing and trade-war conditions simultaneously, conditions absent from modern economies",
  "Mises's *Theory of Money and Credit* (1912) provided the framework. The empirical record vindicated it. When the cost of taxing exceeds the political cost of printing, governments print.")

q("sound_money_history", "argentina_alfonsin_1989_3079_percent",
  "Argentina under Raúl Alfonsín hit 3,079% annual inflation in 1989, peak monthly inflation 197%. Alfonsín left office five months early. Menem took office July 1989 and implemented the Convertibility Plan (1991), pegging the peso to the dollar at 1:1. What did the peg accomplish 1991-2001?",
  "Inflation fell from triple-digit annual rates to single digits within two years, demonstrating peg credibility worked",
  "Argentina experienced fifteen years of stable currency before joining the dollar bloc voluntarily under Kirchner",
  "The Convertibility Plan failed within six months when the peso depreciated 50% in October 1991 against dollars",
  "Argentine inflation actually rose during the 1990s as the peg pushed import prices higher across the decade",
  "Menem and Cavallo's plan worked initially because it removed central bank discretion. When the political will to maintain it failed in 2001-02, the peg broke. Constraints work only as long as politics allows.")

q("sound_money_history", "maria_theresa_thaler_endurance",
  "The Maria Theresa thaler was first minted in Austria in 1741. The 1780-dated version was so trusted in trade across the Arab world, East Africa, and Asia that countries kept minting that exact design for centuries after her death. Italy minted them through 1937. What made this coin durable?",
  "Exact silver content (23.39 grams of 833 fineness) maintained over centuries by every mint, a recognized standard",
  "Religious endorsement by the Vatican gave the coin legal-tender status across the Catholic world for centuries",
  "Magnetic properties of the silver-alloy mixture allowed verification with a simple compass test in Africa",
  "Maria Theresa's personal signature on each coin authenticated value, and her family signed replacement issues",
  "Sound money worked because silver content was known and consistent. People in Yemen, Ethiopia, and Oman trusted the coin because it actually contained the silver claimed. Every fiat named has collapsed since 1937.")

q("sound_money_history", "mises_crackup_boom_concept",
  "Mises coined the German term *Katastrophenhausse* — 'crack-up boom' — for the final stage of fiat collapse. As citizens lose confidence, they spend as fast as possible on real goods, briefly making the economy look booming. Mises argued this is the LAST stage before breakdown. What's the signature?",
  "Velocity of money rises dramatically as citizens spend instantly; prices rise faster than supply expansion implies",
  "Velocity of money falls to historic lows as citizens save aggressively in anticipation of price stability returning",
  "Real GDP growth accelerates as the productive economy expands under the influence of monetary stimulus widely",
  "Bond yields fall sharply as investors trust the currency more during the final phase of hyperinflation overall",
  "Mises's *Human Action* (1949) develops the concept. Weimar 1923, Hungary 1946, Zimbabwe 2008 all show this signature. The 'velocity explosion' distinguishes hyperinflation from ordinary inflation in pure monetary theory.")

q("sound_money_history", "bitcoin_2024_halving_post_supply",
  "Bitcoin's fourth halving occurred April 19, 2024, at block 840,000. The block subsidy fell from 6.25 BTC to 3.125 BTC. New annual issuance dropped to about 164,250 BTC per year against an existing supply of roughly 19.7 million. What is the new annual issuance rate compared to gold's 1.5%?",
  "About 0.85%, below gold's 1.5%, making Bitcoin demonstrably scarcer than gold by annual new supply",
  "About 3.0%, still twice gold's rate, meaning Bitcoin remains less scarce than gold for at least a decade",
  "About 5.0%, making Bitcoin similar to silver in monetary scarcity but less scarce than gold currently",
  "About 15%, far above gold's rate, since difficulty adjustments allow more rapid issuance during expansion",
  "Each halving cuts annual issuance roughly in half. The 2024 halving pushed Bitcoin past gold in scarcity metrics. The 2028 halving will halve again. By 2032 Bitcoin issuance will be roughly 0.2% annually.")

q("sound_money_history", "bitcoin_genesis_text_jan_3",
  "Bitcoin's Genesis block was mined January 3, 2009 by Satoshi. Embedded in the coinbase parameter: 'The Times 03/Jan/2009 Chancellor on brink of second bailout for banks.' Satoshi never spent the 50 BTC reward from this block. What does the unspent reward establish?",
  "Satoshi's commitment to Bitcoin's supply schedule, no pre-mine, defusing immaculate-conception critique at block zero",
  "A bug in the original code prevented Satoshi from spending the block as a technical oversight in implementation",
  "Bitcoin's protocol automatically destroys the Genesis block reward after one thousand blocks per design rule",
  "The 50 BTC was spent by Hal Finney on January 12, 2009 in the first peer-to-peer transaction in history",
  "Genesis block reward is technically unspendable due to how Satoshi structured the coinbase output. The 'first transaction' (Block 170, Jan 12, 2009) was Satoshi to Hal Finney with 10 BTC from a later block.")

q("sound_money_history", "mises_theory_money_credit_1912",
  "Mises's *The Theory of Money and Credit* (1912), published when he was 31, extended marginal utility theory to money for the first time. His key contribution: the regression theorem, tracing money's purchasing power back through time to a pre-monetary commodity origin. Why does this matter for Bitcoin?",
  "Defenders argue early miners' willingness to acquire it for expected future monetary use satisfies regression",
  "Mises explicitly endorsed Bitcoin in 1912 as the inevitable end-state of monetary evolution under his theory",
  "The regression theorem proves Bitcoin cannot be money since it lacks any prior non-monetary commodity backing",
  "Mises argued any potential digital money would require state issuance to give it initial value through tender",
  "Whether Bitcoin satisfies the regression theorem is debated within Austrian economics. Rothbard and Hülsmann interpreted regression to require commodity backing; Konrad Graf argued network effects supply equivalent.")

q("sound_money_history", "hayek_denationalisation_money_1976",
  "Hayek's *Denationalisation of Money* (1976) proposed ending government monopoly on currency issuance. Hayek envisioned private banks issuing competing currencies, with users choosing whichever best held value. He won the Nobel in 1974. What is Bitcoin's relation to Hayek's proposal?",
  "Bitcoin is one realization, a non-government money users choose voluntarily, competing against fiat without state",
  "Bitcoin contradicts Hayek because Hayek argued competing currencies should be issued by chartered banks ever",
  "Hayek explicitly rejected digital money in 1976, predicting that all sound money would require commodity backing",
  "Bitcoin is fully Hayekian because the Bitcoin Foundation issues new coins coordinated with central banks worldwide",
  "Hayek argued no theoretical reason competing currencies needed to be traditional-bank-issued — only that users be free to choose. The 2024 Bitcoin ETF approvals brought it into mainstream financial infrastructure.")

q("sound_money_history", "greshams_law_modern_application",
  "Gresham's law — 'bad money drives out good' — was named after Sir Thomas Gresham (1519-1579), adviser to Elizabeth I. The principle works under legal tender laws: government forces parity between coins of different metal content, citizens spend the debased coins and hoard the better. What's the modern fiat-Bitcoin analog?",
  "Citizens spend depreciating fiat for daily transactions while accumulating Bitcoin as long-term savings widely",
  "CBDCs have eliminated Gresham's law by making all money perfectly equivalent through standardization across",
  "Gresham's law no longer applies because legal-tender enforcement has been removed across all jurisdictions",
  "Citizens spend Bitcoin for purchases while saving fiat as the long-term store of value reversing Gresham",
  "Without legal-tender requirements, citizens can choose. With legal force (taxes paid in fiat, salaries in fiat), Gresham's pattern emerges: spend the worse, save the better.")

q("sound_money_history", "el_salvador_bitcoin_legal_tender",
  "El Salvador became the first nation to make Bitcoin legal tender on September 7, 2021 under Bukele. The Chivo wallet was launched alongside. Bukele's government acquired thousands of Bitcoin for the national treasury. By late 2024 Bitcoin had massively outperformed dollar reserves. What did this demonstrate?",
  "A sovereign nation could opt out of dollar reserves and accumulate Bitcoin, outperforming conventional management",
  "Bitcoin adoption requires complete abandonment of the dollar within six months, since dual systems are impossible",
  "El Salvador's experiment failed within one year as Bitcoin volatility made the strategy untenable for treasury",
  "The IMF forced El Salvador to abandon Bitcoin within eighteen months as a condition of development assistance",
  "Bukele's Bitcoin strategy showed small nations can hedge against dollar debasement. The IMF criticized but could not stop. Argentina's Milei expressed interest. The precedent matters more than any single year's returns.")

q("sound_money_history", "mt_gox_2014_collapse",
  "Mt. Gox, founded 2010 in Tokyo, handled about 70% of all Bitcoin transactions globally by early 2014. On February 24, 2014, the exchange halted withdrawals; on February 28 it filed for bankruptcy. About 850,000 Bitcoin (worth ~$450M then, billions today) had disappeared. What did this illustrate?",
  "Custody of Bitcoin on an exchange is custody of an IOU and not Bitcoin itself, so not your keys not your coins applies",
  "Bitcoin's blockchain failed to record the lost transactions, demonstrating a protocol vulnerability since corrected widely",
  "Mt. Gox proved Bitcoin is inherently fraudulent at the protocol level, with no exchange capable of safe operation under conditions",
  "Japanese regulators caused the collapse through excessive oversight, demonstrating why regulations harm innovation in the sector",
  "Mt. Gox is the canonical exchange-custody disaster. Mark Karpelès was eventually convicted of falsifying records. The maxim 'not your keys, not your coins' became the cypherpunk catechism after this event.")

q("sound_money_history", "ftx_collapse_nov_2022",
  "FTX collapsed November 2022 — second-largest crypto exchange globally. Founder Sam Bankman-Fried had moved customer funds to his trading firm Alameda Research. About $8 billion in customer money went missing. SBF was a major Democratic donor and effective altruism grant-maker. He got 25 years in 2024. What did FTX confirm?",
  "Centralized exchanges require trust Bitcoin's self-custody model was designed to eliminate, regardless of politics",
  "Crypto exchanges with celebrity political connections are inherently safer than those without such connections",
  "Effective altruism as a movement guarantees ethical conduct in financial intermediaries through its philosophy",
  "FTX proved that all cryptocurrency is fraudulent, including Bitcoin itself, since no digital asset is safe",
  "FTX was Mt. Gox repeated, larger. Bankman-Fried's pre-collapse congressional testimony about needed crypto regulations illustrated regulatory capture in real time. Self-custody and audited reserves remain the answer.")

q("sound_money_history", "terra_luna_collapse_may_2022",
  "Terra/Luna collapsed in May 2022, wiping out about $60 billion within a week. TerraUSD 'algorithmic stablecoin' was supposed to maintain a $1 peg through a mint-and-burn mechanism with Luna. When the peg broke May 7-13, the system entered a death spiral. Do Kwon was arrested in Montenegro. What did this illustrate?",
  "Algorithmic mechanisms cannot maintain a peg without sufficient collateral, regardless of mathematical sophistication",
  "Algorithmic stablecoins are the most reliable cryptocurrency since they remove human discretion from the system",
  "TerraUSD was restored to its peg within one month and continues operating as a stable token in major exchanges",
  "Do Kwon was exonerated of all charges after a 2023 audit demonstrated the protocol functioned as designed",
  "Terra/Luna joined Mt. Gox and FTX in cautionary tales separating Bitcoin from 'crypto.' Actual decentralized scarcity (Bitcoin) is one thing; complex algorithmic schemes promising it synthetically is another.")

q("sound_money_history", "german_mark_4_2_trillion_per_dollar",
  "By November 15, 1923 the US dollar exchanged for 4.2 trillion German marks. The mark had been at 4.2 per dollar before WWI. That same day Schacht began the Rentenmark stabilization. What ratio set the Rentenmark to old marks?",
  "One Rentenmark equaled one trillion papermarks, restoring a working medium of exchange overnight after years",
  "One Rentenmark equaled one papermark at face value, requiring no conversion and operating parallel only",
  "One Rentenmark equaled one hundred papermarks, an intermediate conversion preserving partial purchasing power",
  "One Rentenmark equaled one million papermarks, the standard postwar currency replacement ratio across Europe",
  "The trillion-to-one ratio cleared the slate without formal repudiation. The Rentenmark was a fiction — the 'mortgage on German land' that backed it was never enforceable — but the printing pause made it work.")

q("sound_money_history", "bitcoin_pizza_may_22_2010",
  "On May 22, 2010, Florida programmer Laszlo Hanyecz paid 10,000 Bitcoin for two Papa John's pizzas — the first known commercial Bitcoin transaction. At late-2024 Bitcoin prices, those pizzas would be worth hundreds of millions. Bitcoin Pizza Day is celebrated May 22. What does the transaction symbolize?",
  "Bitcoin's transition from theoretical concept to actual exchange medium, demonstrating the network functioned",
  "Bitcoin's failure as a currency since the buyer lost enormous value by spending coins that later appreciated",
  "Bitcoin Pizza Day was invented in 2015 as a marketing gimmick with no actual transaction occurring in 2010",
  "Bitcoin became a currency only after major exchanges launched in 2013, with no real transactions before then",
  "Pizza Day is the canonical example of Bitcoin establishing real-world utility. The hindsight 'loss' to Hanyecz is irrelevant — without early transactions like his, Bitcoin would never have built network effects.")

q("sound_money_history", "hashcash_1997_proof_of_work",
  "Adam Back, a British cryptographer, published 'Hashcash' in 1997 as an anti-spam technique. The idea: require email senders to perform a small computational task before sending, making bulk spam expensive. Hashcash introduced 'proof of work' to cryptography. Satoshi cited Back's paper in 2008. What did Bitcoin add?",
  "A publicly-shared ledger and difficulty adjustment, solving the double-spend problem proof-of-work alone could not",
  "Stronger cryptographic primitives that replaced the hash function Back had used in his 1997 anti-spam paper",
  "Government regulation of the proof-of-work mechanism, which Back's original design operated without oversight",
  "A weaker proof-of-work design that uses less energy than Back's original 1997 protocol while preserving the goal",
  "Bitcoin combined proof-of-work (Back 1997), public ledger ideas (Wei Dai's b-money 1998), and digital-cash concepts. Satoshi's contribution: integrating them with difficulty adjustment to produce decentralized consensus.")

q("sound_money_history", "chinese_paper_money_yuan_dynasty",
  "China invented paper money during the Tang Dynasty (~700 AD) and used it under the Song (960-1279) and Yuan (1271-1368). The Yuan dynasty's Chao currency suffered massive inflation that contributed to dynastic collapse. Marco Polo described Chinese paper money in awe around 1295. What pattern repeated?",
  "Initial discipline gave way to overprinting as governments funded military campaigns and palace expenses widely",
  "Paper money operated stably across all Chinese dynasties from 700 AD through 1949 without major inflation",
  "Chinese paper money was always backed by silver reserves that prevented any inflation throughout the era",
  "Marco Polo's account was fabricated and no paper money actually circulated in Yuan Dynasty China during travels",
  "Paper money's history in China shows the universal pattern: initial discipline → fiscal pressure → overissuance → inflation → repudiation. The Ming dynasty abandoned paper money entirely and used silver bullion.")

# ============================================================================
# P4 CENTRAL BANKING + KEYNES/MMT CRITIQUE (43 questions)
# ============================================================================

q("central_banking_critique", "jekyll_island_six_men_named",
  "The November 1910 Jekyll Island meeting brought six men in a private rail car at Hoboken, NJ: Senator Aldrich (R-RI), Henry Davison of J.P. Morgan, Paul Warburg of Kuhn Loeb, Frank Vanderlip of National City Bank, A. Piatt Andrew of Treasury, and Benjamin Strong. They used only first names. What was their task?",
  "Drafting the blueprint that became the Federal Reserve Act of 1913, structured to look public while bank-controlled",
  "Negotiating US entry into the Bank for International Settlements, not established for another two decades",
  "Planning the dissolution of the Standard Oil Trust, ordered broken up by the Supreme Court in 1911 decision",
  "Designing the Federal Deposit Insurance Corporation not created until the Glass-Steagall Act of 1933 under FDR",
  "Aldrich's brother-in-law was John D. Rockefeller Jr. The Aldrich Plan, after Aldrich's name became toxic, was repackaged as Glass-Owen and signed by Wilson December 23, 1913. G. Edward Griffin's *The Creature from Jekyll Island* is canonical.")

q("central_banking_critique", "paul_warburg_jekyll_role",
  "Paul Warburg, German-born banker who emigrated in 1902, was the technical architect of the Federal Reserve structure designed at Jekyll Island. His brother Max ran M.M. Warburg in Hamburg. Warburg wrote on central banking under pseudonyms before Jekyll. What did Warburg publicly deny for nearly 20 years?",
  "That the Jekyll Island meeting had occurred at all, even though participants gradually confirmed attendance later",
  "That he had ever met Senator Aldrich personally, despite their service together on the Monetary Commission",
  "That central banks should have any function beyond emergency liquidity to commercial banks during crises",
  "That the Federal Reserve Act represented any departure from the gold standard, despite the actual provisions",
  "Frank Vanderlip wrote about the meeting in 1935 in *The Saturday Evening Post*. Warburg's *The Federal Reserve System* (1930) acknowledged certain meetings but downplayed their secrecy. The denial pattern is itself history.")

q("central_banking_critique", "aldrich_plan_to_glass_owen",
  "Senator Aldrich's name had become politically toxic after the 1910 elections and the Pujo Committee hearings on the Money Trust (1912). The Aldrich Plan was repackaged as Glass-Owen and signed by Wilson on December 23, 1913. What was the practical difference between Aldrich Plan and Glass-Owen?",
  "Essentially cosmetic, since Glass-Owen created twelve regional Federal Reserve Banks instead of one central bank",
  "Glass-Owen was a complete departure from Aldrich and established a publicly-controlled central bank without banks",
  "Glass-Owen reduced the proposed money supply expansion by 90% compared to the Aldrich Plan original design",
  "Glass-Owen replaced the central bank with Federal Treasury notes issued directly without commercial bank input",
  "Murray Rothbard's *The Case Against the Fed* (1994) and Thomas DiLorenzo's *Hamilton's Curse* (2008) document the Aldrich-to-Glass-Owen continuity. The marketing changed; the institutional design remained.")

q("central_banking_critique", "federal_reserve_act_signature_dec_23_1913",
  "President Wilson signed the Federal Reserve Act on December 23, 1913 — two days before Christmas, with many Congress members already departed. Senator Aldrich had retired in 1911. The Federal Reserve opened November 16, 1914. Wilson reportedly later said: 'I have unwittingly ruined my country.' What was he lamenting?",
  "Signing a bill that put US monetary policy in private bankers' hands under cover of public legitimacy",
  "Pushing for US entry into WWI in 1917, which his economic advisors had warned would cause fiscal damage",
  "Reducing the federal tariff schedule in 1913, which his treasury officials had warned would damage manufacturing",
  "Allowing the women's suffrage movement to gain momentum during his administration, which he had opposed",
  "The Wilson quote is reported in *William G. McAdoo* by John Broesamle (1973). McAdoo was Wilson's Treasury Secretary and son-in-law. The quote captures the founders'-experience problem: sold public, structured private.")

q("central_banking_critique", "benjamin_strong_ny_fed",
  "Benjamin Strong became first president of the Federal Reserve Bank of New York in 1914 and dominated the system until his death in October 1928. Strong worked closely with Bank of England governor Montagu Norman through the 1920s, coordinating policy to help Britain return to gold at prewar parity. Result?",
  "The easy money the Fed extended to support sterling helped fuel the bubble that produced the 1929 crash",
  "Strong's policies stabilized international currency markets so well that 1929 was caused by unrelated events",
  "Strong's coordination with Norman directly prevented the Great Depression from beginning, before successors",
  "Strong actually opposed the gold standard return and worked secretly to prevent the 1925 British decision",
  "Murray Rothbard's *America's Great Depression* (1963) details Strong's role in inflating the late-1920s boom. The Fed had been chartered to prevent panics; its first major test produced the worst banking panic in US history.")

q("central_banking_critique", "friedman_schwartz_monetary_history_1963",
  "Friedman and Schwartz published *A Monetary History of the United States, 1867-1960* in 1963. Their argument: the Fed allowed the money supply to contract by about 33% between 1929 and 1933. Friedman summarized: 'The Great Depression was produced by government mismanagement.' What was Friedman's recommendation?",
  "A constant-money-growth rule of about 3% annually, removing Fed discretion that had failed catastrophically",
  "Complete abolition of the Federal Reserve, returning the US to a pure gold standard with private bank notes",
  "Doubling the Federal Reserve's mandate to include employment maximization alongside price stability widely",
  "Empowering the Federal Reserve to act discretionarily during all financial crises with no rule constraint",
  "Friedman's monetarist k-percent rule was a constraint on discretion, not Austrian elimination of central banking. Bernanke apologized to Friedman at his 90th birthday in 2002 — before printing aggressively in 2008.")

q("central_banking_critique", "bernanke_apology_friedman_2002",
  "Ben Bernanke, then a Fed Governor, spoke at Milton Friedman's 90th birthday in November 2002: 'Regarding the Great Depression, you're right, we did it. We're very sorry. But thanks to you, we won't do it again.' Six years later Bernanke was Fed Chair during 2008. What did 'won't do it again' mean to Bernanke?",
  "Aggressive monetary expansion to prevent any deflation, leading directly to QE programs from 2008 onward",
  "Refusing to print money under any economic conditions, returning to strict gold-standard discipline of 1971",
  "Complete elimination of the Federal Reserve, transferring monetary authority to the Treasury under Congress",
  "Pegging the dollar to the British pound at a fixed rate, restoring the 1944 Bretton Woods arrangement again",
  "Bernanke read Friedman's lesson as 'don't allow the money supply to contract.' Austrians read the same history as 'don't centrally manage money at all.' The 2008-2014 QE programs were Bernanke's application.")

q("central_banking_critique", "volcker_appointed_august_1979",
  "Paul Volcker was appointed Fed Chair August 6, 1979 with inflation at 11.3% and rising. Volcker, 6'7\" and stern, broke with prior practice and targeted money-supply growth directly, allowing interest rates to find whatever level was needed. The federal funds rate peaked above 20% in 1981. What was the result by 1984?",
  "Inflation fell to about 3.7%, demonstrating that determined central-bank action can break expectations at cost",
  "Inflation rose to 18%, demonstrating that high interest rates intensify rather than reduce inflation widely",
  "The US dollar collapsed against the deutsche mark by 80%, requiring the 1985 Plaza Accord to coordinate",
  "The Federal Reserve was placed under direct White House control, removing operational independence in 1984",
  "Volcker's 'October Massacre' (Oct 6, 1979) when the Fed shifted to money-supply targeting is the canonical example of central-bank credibility restored through pain. The 'Volcker Recession' bottomed November 1982.")

q("central_banking_critique", "volcker_political_pressure_carter_reagan",
  "Volcker's high-interest-rate policy generated enormous political pressure. Homebuilders mailed coffins of 2x4 lumber to the Fed. Farmers blocked Fed headquarters with tractors. Reagan reportedly said in 1981: 'I just couldn't ask Paul Volcker to step down.' What does this reveal about Fed 'independence'?",
  "Independence works when the political class accepts short-term pain for credible disinflation, requiring backing",
  "Fed independence is legally absolute and political pressure has no effect on monetary policy decisions ever",
  "Volcker actually capitulated to Carter and Reagan pressure, lowering rates whenever displeasure was expressed",
  "The 1979-87 episode proves Fed chairs are completely insulated from political consequences regardless of policy",
  "The Volcker episode is the strongest case for institutional independence and reveals what independence requires. Without Reagan's tolerance, the inflation fight would have failed. Post-Volcker chairs have rarely faced equivalent pressure.")

q("central_banking_critique", "bear_stearns_march_2008_jpm",
  "Bear Stearns, the fifth-largest US investment bank, collapsed over the weekend of March 14-16, 2008. The Fed coordinated with JPMorgan to acquire Bear at $2 per share (later $10), down from $172 in early 2007. The Fed provided a $29 billion loan to JPMorgan. What new principle did this establish?",
  "The Fed would provide direct lending to non-bank financial firms, expanding lender-of-last-resort beyond banks",
  "Investment banks were legally classified as commercial banks subject to identical regulatory oversight in March",
  "The Federal Deposit Insurance Corporation began insuring investment bank accounts up to one million per account",
  "Bear Stearns was nationalized by the US Treasury rather than rescued by the Federal Reserve in a transfer",
  "The Bear Stearns rescue expanded Fed authority to non-bank institutions. The Fed had no statutory authority — it invoked Section 13(3) of the Federal Reserve Act emergency provisions for the first time since the 1930s.")

q("central_banking_critique", "lehman_sept_15_2008",
  "Lehman Brothers filed for Chapter 11 bankruptcy on September 15, 2008, the largest bankruptcy in US history at $639 billion in assets. Paulson and Bernanke chose NOT to rescue Lehman, after rescuing Bear Stearns in March. The decision triggered global panic. What was the official reason for letting Lehman fail?",
  "No legal authority and no willing private acquirer, though critics note other rescues happened anyway widely",
  "Lehman had committed actual fraud unlike Bear Stearns, making rescue legally impossible under securities law",
  "The Treasury preferred to rescue Lehman but the Fed unilaterally vetoed the action against Paulson's view",
  "European regulators refused to allow Barclays to acquire Lehman, removing the only viable private rescue",
  "Paulson and Bernanke later disagreed about why Lehman failed. The decision triggered panic that led to TARP. Critics argue the inconsistency (rescue Bear, kill Lehman, rescue AIG) revealed bailouts as discretionary.")

q("central_banking_critique", "aig_bailout_sept_2008",
  "AIG, the world's largest insurance company, was rescued by the Fed on September 16, 2008 — the day after Lehman failed. The initial rescue was $85 billion, eventually growing to $182 billion. AIG had written massive credit default swaps that would have cascaded. What was the controversial element of the wind-down?",
  "Counterparties including Goldman Sachs received 100 cents on the dollar from AIG positions while taxpayer-funded",
  "AIG executives were criminally prosecuted in 2009 for pre-crisis behavior, with all bonuses returned to Treasury",
  "The Federal Reserve sold AIG's profitable insurance divisions to Berkshire Hathaway in early 2009 cheaply",
  "AIG was nationalized through direct stock purchase by the US Treasury and remained government-owned widely",
  "Goldman Sachs received $12.9 billion via AIG counterparty payments at par. Henry Paulson had been Goldman CEO before becoming Treasury Secretary. AIG payments became Exhibit A for 'crony capitalism' critiques.")

q("central_banking_critique", "tarp_700_billion_oct_2008",
  "The Emergency Economic Stabilization Act of 2008, signed October 3, 2008, created TARP authorizing $700 billion. Congress initially rejected the bill on September 29, 2008, causing the Dow to drop 778 points. The revised bill passed days later. What did actual TARP funds primarily go toward?",
  "Direct capital injections into the major banks rather than the originally-proposed purchase of troubled assets",
  "Purchase of mortgage-backed securities from homeowners directly, restructuring loans of fifty million families",
  "Establishment of a new government-owned bank to compete with private commercial banks under Congressional control",
  "Reimbursement of insurance policy claims for retirement accounts that had lost value during the financial crisis",
  "Paulson pivoted from asset purchases to capital injections, partly because asset purchases would have required pricing the toxic assets — exposing how worthless many were. Citigroup and Bank of America used TARP capital.")

q("central_banking_critique", "qe1_nov_2008_treasuries_mbs",
  "QE1 was announced November 25, 2008, after the federal funds rate had been cut effectively to zero. The Fed bought $600 billion in MBS, later expanded to $1.25 trillion in MBS plus $300 billion in Treasuries. The Fed's balance sheet grew from $900 billion to $2.2 trillion. What did QE1 aim to do?",
  "Push down longer-term interest rates by absorbing safe assets, forcing investors into riskier assets widely",
  "Pay off the national debt by purchasing Treasury bonds and forgiving them through Federal Reserve accounting",
  "Distribute cash directly to American households through stimulus checks coordinated between Fed and the IRS",
  "Replace gold reserves in the US Treasury with mortgage-backed securities as the new dollar backing arrangement",
  "Bernanke had argued for this approach in his academic work on Japan's lost decade. Austrians argued the Fed was inflating a new bubble (asset prices) to mask the previous bubble's collapse rather than allowing adjustment.")

q("central_banking_critique", "qe2_nov_2010_600bn",
  "QE2 was announced November 3, 2010 — $600 billion in Treasury purchases over eight months. The economy was technically out of recession (since June 2009) but unemployment was still 9.7%. QE2 was unusual because it occurred outside an immediate crisis. What did critics like Stanford's John Taylor argue?",
  "It risked future inflation while distorting asset prices, since the underlying problem was structural debt overhang",
  "It was insufficient and the Fed should have bought ten trillion dollars instead to end unemployment in twelve months",
  "It was the only realistic policy option since no fiscal alternatives existed under late-2010 political conditions",
  "It successfully ended the financial crisis within six months and produced full employment by mid-2011 widely",
  "Taylor's 'Taylor Rule' (1993) prescribed Fed rate-setting via a formula linking inflation and output gaps. QE policies deviated from rule-based discipline. The Fed under Bernanke/Yellen/Powell has rarely returned to rules.")

q("central_banking_critique", "qe3_sept_2012_open_ended",
  "QE3 was announced September 13, 2012 — open-ended at $40 billion per month in MBS purchases, later expanded to $85 billion/month. No announced end date. The program tapered in 2014 and ended October 2014. By that point the Fed's balance sheet had reached $4.5 trillion. What new framework did this represent?",
  "Commitment device promising continued purchases until labor-market conditions were met, embedding reversal risk",
  "Direct printing of money to fund the federal government's budget deficits through a Treasury-Fed arrangement",
  "Replacement of the Federal Reserve's interest-rate target with a fixed exchange-rate peg to gold at a level",
  "Establishment of negative interest rates for the first time in US history with rates below zero across the curve",
  "The 'forward guidance' element became the new monetary instrument. Bernanke's strategy: tell markets the Fed would remain accommodative for an extended period. Critics noted this made Fed exit potentially destabilizing.")

q("central_banking_critique", "covid_march_2020_emergency_cuts",
  "Between March 3 and March 15, 2020, the Fed cut the federal funds rate from 1.5-1.75% to 0-0.25% in two emergency actions, restarted QE at $700 billion (later open-ended), launched a Commercial Paper Facility, and announced unlimited Treasury and MBS purchases. Balance sheet grew from $4.2T to $7T by June 2020. Fiscal response?",
  "About $4-5 trillion across CARES, supplements, and the 2021 Rescue Plan, the largest peacetime expansion in US history",
  "About $400 billion in targeted relief, with most spending postponed for two years through legislative delays",
  "Approximately $50 billion through standard unemployment insurance extensions, with no major new program created",
  "Approximately $20 trillion in direct cash transfers, exceeding the pre-pandemic US GDP within a single fiscal year",
  "Combined 2020-21 monetary + fiscal response was unprecedented. Larry Summers warned February 2021 it would cause inflation. The 2021-22 inflation was the consequence. MMT advocacy treated risk as overstated; data settled the debate.")

q("central_banking_critique", "cares_act_march_2020_speed",
  "CARES Act was signed March 27, 2020 — two weeks after pandemic emergency. At $2.2 trillion, it was the largest single fiscal bill in US history then. Direct payments of $1,200 per adult plus expanded unemployment arrived in weeks. PPP loaned $669 billion to businesses. What economic effect did transfer speed have?",
  "Personal savings rose dramatically (33% peak April 2020) since recipients couldn't spend on closed services widely",
  "Personal savings fell to historic lows immediately as Americans spent every dollar within twenty-four hours",
  "GDP collapsed by 50% across the second quarter of 2020 despite the fiscal injection, demonstrating futility",
  "Inflation began immediately in March 2020 and reached double digits by June of that year validating fears",
  "Cantillon effect operated visibly: first recipients (banks, contractors, PPP businesses) bought assets at old prices. By the time the money rippled out (2021-22), prices had risen. Inequality widened despite egalitarian framings.")

q("central_banking_critique", "cpi_peak_9_1_june_2022",
  "US CPI inflation peaked at 9.1% year-over-year in June 2022, the highest since 1981. Gasoline averaged $5.00 per gallon nationally that month. Used car prices had risen 45% from late 2019. Larry Summers warned in a February 2021 op-ed that the stimulus would cause inflation. Summers had been considered out of touch then. What did the peak vindicate?",
  "Quantity-theory predictions that monetary expansion of the 2020-21 magnitude would cause inflation with a one-year lag",
  "Modern Monetary Theory's central claim that government deficits do not cause inflation under any conditions",
  "The transitory-inflation framework as articulated by Treasury Secretary Yellen and Powell throughout 2021 entirely",
  "The 1970s 'cost-push' theory that inflation comes from supply shocks rather than monetary policy from central banks",
  "The 'transitory' framing from Powell, Yellen, and most mainstream commentary in 2021 was wrong. Summers and the small group warning about overheating were vindicated. 2021-22 is the strongest recent test of monetary explanations.")

q("central_banking_critique", "powell_transitory_walkback_nov_2021",
  "Fed Chair Powell told Congress on November 30, 2021 that 'it's probably a good time to retire' the word 'transitory' regarding inflation. By that point CPI was at 6.8% and rising. The Fed had been calling inflation transitory through most of 2021. The shift in language preceded the rate-hike cycle of March 2022. What does this reveal?",
  "The Fed underestimated inflation persistence by roughly a year, weakening credibility and reopening rule-based debate",
  "The Fed had perfectly predicted inflation throughout 2021 and the word change was purely strategic communication choice",
  "The Fed was misled by intentional Treasury falsification of consumer price data discovered and corrected later",
  "The Federal Reserve had no legal mandate to address inflation in 2021 and the change reflected new authority",
  "Major Fed forecast errors in 2021 reopened John Taylor's argument for rule-based policy. The Fed had built credibility under Volcker by being slow but reliable; the 2021 'transitory' episode undermined that within a year.")

q("central_banking_critique", "kelton_deficit_myth_2020",
  "Stephanie Kelton's *The Deficit Myth* (2020) became MMT's most-cited popular text, debuting at #4 on the NYT bestseller list. Kelton, an economist at Stony Brook and former Senate Budget Committee adviser to Bernie Sanders, argued the US — issuing its own currency — cannot 'run out of money.' What constraint did Kelton acknowledge?",
  "Inflation — Kelton conceded deficit spending can cause inflation when productive capacity is reached, downplayed though",
  "Foreign exchange — Kelton argued the dollar would collapse if US deficits exceeded twenty percent of GDP yearly",
  "Interest rates — Kelton argued bond markets would punish excessive deficits through rates above ten percent",
  "Capital flight — Kelton argued American billionaires would emigrate if deficits exceeded World War Two figures",
  "Kelton's text acknowledges inflation as the binding constraint. The 2021-22 inflation became the test case. MMT advocates argued post-hoc the inflation came from other factors; Summers and conventional economists had predicted it.")

q("central_banking_critique", "mmt_falsification_2021_22",
  "MMT's central political deployment in 2020-21 was: deficits don't matter unless inflation appears, so spend freely until inflation arrives. The 2021-22 inflation arrived larger, faster, and more persistent than MMT advocates had predicted. By mid-2022 the political momentum for MMT had collapsed. What did this demonstrate?",
  "MMT made empirical claims about when inflation would appear at what magnitude; those claims failed against 2021-22 evidence",
  "MMT successfully predicted 2021-22 inflation and the policy response, vindicating the theory completely in real-time conditions",
  "MMT is not falsifiable as a framework since proponents always point to new conditions exempting it from contradictions",
  "MMT's 2021-22 predictions cannot be evaluated because the necessary economic data has not yet been published widely",
  "Kelton and other advocates argued post-hoc the 2021-22 inflation came from supply shocks, not deficits. Conventional Quantity Theory response: large monetary expansion produces inflation with a lag. The simpler explanation won.")

q("central_banking_critique", "keynes_general_theory_1936_animal_spirits",
  "Keynes's *The General Theory of Employment, Interest and Money* (1936) introduced 'animal spirits' — non-rational drivers of business investment decisions. Keynes argued that during recessions, animal spirits would be depressed and investment would fall below what equilibrium analysis would predict. What did Keynes recommend?",
  "Government deficit spending to replace private investment when animal spirits are depressed, regardless of productivity",
  "Restoration of the gold standard to discipline private investment decisions through credible long-term currency stability",
  "Direct central planning of all major investment decisions through a national commission, removing private allocation",
  "Voluntary unemployment insurance to allow workers time to find optimal jobs without disturbing labor equilibrium widely",
  "Keynes famously suggested in *General Theory* (Ch. 16) that burying bottles of money and digging them up would be productive 'on principles of laissez-faire.' The practical implication was deficit spending during downturns.")

q("central_banking_critique", "keynes_paradox_of_thrift",
  "Keynes argued in *The General Theory* (1936) for the 'paradox of thrift': if individuals all decide to save more during a recession, aggregate demand falls and the recession worsens. Individually-virtuous behavior became collectively-destructive in Keynes's framework. Policy implication: government deficit spending. Austrian response?",
  "Saving funds productive investment via voluntary lending; depressing saving through artificial credit distorts capital",
  "Saving was actually impossible in 1936 due to gold standard restrictions on private wealth accumulation widely",
  "Saving and investment were perfectly correlated in 1936 making the paradox empirically meaningless in practice",
  "Saving requires the existence of fiat currency to function so the paradox cannot operate under any gold regime",
  "Hayek's response (in the 1931-32 debate and after): saving doesn't disappear, it becomes lendable funds at the natural interest rate. Government deficits crowd out this saving and substitute political allocation for market allocation.")

q("central_banking_critique", "hayek_keynes_1931_lse_lectures",
  "In January-February 1931, Hayek gave four lectures at the LSE published as *Prices and Production* (1931). The lectures were a direct intellectual challenge to Keynes's *Treatise on Money* (1930). Hayek argued Keynes had ignored the structure of capital. Keynes assigned Piero Sraffa to write a critical review. What was the outcome?",
  "Keynes's *General Theory* (1936) supplanted Hayek in the mainstream for decades, even though Hayek won the analytical exchange",
  "Hayek and Keynes published a joint book in 1934 reconciling their positions which founded postwar Cambridge synthesis",
  "The London School of Economics fired Hayek in 1931 for his criticism of Keynes, ending Austrian economics in Britain",
  "Keynes publicly acknowledged Hayek's superiority in 1934 and withdrew *The Treatise on Money* from publication entirely",
  "The mainstream profession adopted Keynesianism through the 1940s-1970s. Hayek's *Road to Serfdom* (1944) won general attention but his economic-theory work was marginalized until 1970s stagflation crisis.")

q("central_banking_critique", "hayek_keynes_1944_polite_relations",
  "Despite their public intellectual war, Hayek and Keynes remained polite personally. During WWII, Keynes at the British Treasury helped Hayek obtain rooms at King's College, Cambridge after LSE was evacuated. Keynes read Hayek's *Road to Serfdom* (1944) and wrote calling it 'a grand book.' What did Keynes agree with?",
  "Hayek's argument that planning had destructive political consequences, though Keynes thought modest planning could work",
  "Hayek's complete rejection of all central planning under any economic conditions including wartime armaments production",
  "Hayek's critique of *The Treatise on Money* (1930), which Keynes publicly retracted in his August 1944 letter to Hayek",
  "Hayek's gold-standard advocacy, which Keynes had opposed but came to embrace in his Bretton Woods proposals later",
  "Keynes's 1944 letter is in Bruce Caldwell's *Hayek: A Life 1899-1950* (2022). Keynes believed *good* planners would avoid totalitarian drift. Hayek argued no planner could remain virtuous because knowledge problems force coercion.")

q("central_banking_critique", "phillips_curve_breakdown_1970s",
  "The Phillips curve, named for A.W. Phillips's 1958 paper, claimed an inverse relationship between unemployment and inflation. Higher inflation reduced unemployment; higher unemployment reduced inflation. Through the 1960s policy was built on this trade-off. What happened in the 1970s that destroyed the framework?",
  "Stagflation arrived as simultaneous high inflation AND high unemployment, falsifying the predicted inverse relationship as Friedman foretold",
  "The Phillips curve relationship became stronger in the 1970s as central banks gained tools to fine-tune the trade-off widely",
  "Phillips's original 1958 paper was discovered to have used fraudulent data, retracted by the journal Economica in 1973",
  "OPEC oil embargoes restored the Phillips curve in the 1970s by demonstrating the trade-off through energy prices",
  "Milton Friedman's 1968 AEA presidential address ('The Role of Monetary Policy') had warned the apparent Phillips trade-off would break down once inflation expectations adjusted. The 1970s vindicated this prediction completely.")

q("central_banking_critique", "lucas_critique_1976_general",
  "Robert Lucas's 1976 paper ('Econometric Policy Evaluation: A Critique') argued that the parameters of econometric models change when policy changes. If the Fed targets the Phillips curve, the trade-off itself shifts as private actors update expectations. Lucas won the 1995 Nobel. What broader implication does it have?",
  "Rules-based commitment may produce better outcomes than discretionary fine-tuning, since rules anchor expectations widely",
  "Central banks should hire more econometricians since the Lucas critique pointed to a need for more sophisticated models",
  "The Lucas critique was disproven by 1990s monetary policy success demonstrating that discretionary action can work",
  "Lucas argued for replacing the Federal Reserve with a fixed money-growth rule of three percent annually as policy",
  "The Lucas critique influenced rule-based proposals (Friedman's k-percent rule, Taylor's rule). Practice has largely ignored these; the Fed has remained discretionary. 2021-22 inflation reopened the rule-versus-discretion debate.")

q("central_banking_critique", "fiscal_multiplier_2008_2020",
  "Keynesian theory assumes a 'fiscal multiplier' — that government spending generates more than one dollar of GDP per dollar spent. The 2009 ARRA ($787B) was justified with multiplier estimates of 1.5+. The 2020 CARES Act ($2.2T) made similar assumptions. Robert Barro's 2010 analysis estimated the actual multiplier at 0.4-0.7. What does this imply?",
  "Government spending crowds out private activity rather than expanding total output, producing less GDP per dollar",
  "Government spending always produces a multiplier above 1.5 in any developed economy validating Keynesian models widely",
  "The multiplier estimate of 0.4-0.7 was incorrect per subsequent IMF analysis finding actual multipliers of 2.0-3.0",
  "Multipliers are irrelevant to policy since fiscal stimulus operates through different channels than the GDP framework",
  "Barro and John Taylor have argued the apparent stimulus effect was largely accounting (government spending counted as GDP) rather than economic. Multiplier estimates below 1 imply fiscal stimulus is net contractionary on private activity.")

q("central_banking_critique", "ricardian_equivalence_1817",
  "David Ricardo proposed in 1817 (and Robert Barro formalized in 1974) that if government spends today through borrowing, rational citizens anticipate future taxes to repay the debt and save accordingly. 'Ricardian equivalence' implies fiscal stimulus has limited effect because households offset government dissaving. What did 2008-2020 reveal?",
  "Personal saving rates rose substantially during stimulus periods (33% in April 2020), partly consistent with Ricardian effects",
  "Personal saving rates fell to record lows during all stimulus periods demonstrating Ricardian equivalence had no support",
  "Personal saving rates remained perfectly constant during stimulus periods indicating no household response to deficits",
  "Personal saving rates correlated with stock market prices rather than government deficits indicating no Ricardian effect",
  "Ricardian equivalence is rarely 'pure' in practice — some households are liquidity-constrained, some are short-sighted. But the high 2020 saving rate is consistent with substantial Ricardian effects in the broader population.")

q("central_banking_critique", "cbdc_china_e_cny_2022",
  "China's digital yuan (e-CNY) entered pilot use in 2020 and was rolled out in major cities by 2022. Unlike commercial cryptocurrencies, the e-CNY is issued and controlled directly by the People's Bank of China. Every transaction is visible to the state. What surveillance capability does a CBDC provide that physical cash does not?",
  "Complete real-time visibility of every transaction including amount, parties, location, with ability to freeze accounts",
  "The ability to issue currency to citizens directly without involving commercial banks, a capability already present",
  "The ability to set negative interest rates on commercial bank deposits, a capability central banks already use",
  "The ability to pay interest on retail deposits at the central bank, similar to existing Treasury bill yields",
  "The surveillance capability of CBDCs is the structural feature distinguishing them from cash. Hayek argued in *Denationalisation of Money* (1976) that the cost of monetary monopoly is precisely this kind of state power.")

q("central_banking_critique", "fomc_voting_structure",
  "The Federal Open Market Committee (FOMC) sets US monetary policy. It has twelve voting members: the seven Fed Board governors (14-year terms), the New York Fed President (permanent vote), and four of eleven other regional Fed Bank presidents on rotation. Regional presidents are selected by their bank directors. What does this structure encode?",
  "Commercial banks have direct input into selecting regional Fed presidents, who then vote on national policy alongside governors",
  "The President of the United States has complete authority over FOMC voting through executive orders overriding the Board",
  "Congress selects all twelve FOMC members through a public auction process held every other year in even cycles",
  "The FOMC is purely advisory and its votes have no legal effect on monetary policy decisions made by Treasury widely",
  "Regional Fed Bank presidents' commercial-bank-influenced selection is documented in the Federal Reserve Act. Critics call this 'banker control' of the central bank; defenders call it 'regional expertise.' Jekyll-Island compromise.")

q("central_banking_critique", "fed_balance_sheet_2024_status",
  "The Federal Reserve's balance sheet peaked above $8.9 trillion in April 2022, after the COVID expansion. The Fed began 'quantitative tightening' in mid-2022 — letting maturing securities roll off without replacement. By late 2024 the balance sheet had fallen to about $7 trillion. What is the pre-2008 'normal' size for comparison?",
  "About $900 billion in 2007, meaning the Fed's balance sheet is still roughly 8 times its pre-crisis size after years",
  "About $9 trillion in 2007, meaning the Fed's balance sheet has actually shrunk substantially in real terms since",
  "About $4 trillion in 2007, meaning current balance sheet is roughly the same size in nominal terms as pre-Bernanke",
  "Approximately $50 billion in 2007, meaning the Fed's balance sheet has grown more than one thousand times since",
  "The pre-2008 norm of around $900B has effectively been abandoned. The Fed has not committed to returning to pre-crisis size and discusses 'ample reserves' regimes that institutionalize a permanently larger balance sheet.")

q("central_banking_critique", "powell_appointed_2018_renominated_2022",
  "Jerome Powell was appointed Fed Chair by Trump in 2018, replacing Yellen. Biden renominated Powell in 2021 and the Senate confirmed him to a second term in May 2022. This bipartisan continuation was unusual — modern presidents typically replace Fed chairs from the opposing party. What does this continuity suggest?",
  "The Powell reappointment signaled continuity of the post-2008 monetary regime regardless of which party controls",
  "The reappointment proved the Federal Reserve operates with complete independence from political pressure entirely",
  "Biden was forced to reappoint Powell because no other qualified candidate existed in the Federal Reserve System",
  "Powell threatened to publish internal Fed documents if not reappointed, forcing Biden's hand under Wall Street pressure",
  "Senator Elizabeth Warren opposed Powell from the left; Austrian-leaning critics opposed him for different reasons. Bipartisan support for institutional continuity is part of what Austrians call 'capture' — consensus across parties.")

q("central_banking_critique", "first_bank_us_1791_jefferson",
  "Alexander Hamilton, first Treasury Secretary, persuaded Congress in 1791 to charter the First Bank of the United States — a 20-year charter for a privately-owned central bank with the federal government as the largest shareholder. Jefferson opposed it, calling central banking 'more dangerous than standing armies.' What happened to the First Bank?",
  "Its charter expired in 1811 and was not renewed by a single vote in the Senate, ending the first US experiment",
  "It was nationalized by Jefferson during his presidency in 1803 and absorbed into the Treasury Department under Congress",
  "It became the foundation of the modern Federal Reserve through continuous operation from 1791 to 1913 under renewals",
  "It was destroyed in the War of 1812 when British forces burned Washington and damaged the bank vault beyond repair",
  "The Second Bank of the US was chartered in 1816 (20-year charter). Andrew Jackson vetoed renewal in 1832, ending the Second Bank in 1836. The US operated without a central bank for 77 years until the 1913 Fed.")

q("central_banking_critique", "andrew_jackson_bank_war_1832",
  "President Andrew Jackson vetoed recharter of the Second Bank of the United States in July 1832, calling it 'dangerous to our liberties.' The 'Bank War' became a major political conflict. Jackson moved federal deposits out in 1833. The Bank's president Nicholas Biddle deliberately contracted credit to cause a recession. What did Biddle's threat reveal?",
  "A private central bank could deliberately damage the economy to force political concessions, validating Jackson's concern",
  "Central banks always cooperate with elected presidents during emergencies, demonstrating safe institutional position widely",
  "The Second Bank had no power to affect economic conditions and Jackson's concerns were politically motivated fabrications",
  "Biddle's actions during the 1834 recession ended Jackson's presidency by causing his impeachment over policy widely",
  "Murray Rothbard's *The Mystery of Banking* (1983) and Thomas DiLorenzo's *Hamilton's Curse* (2008) detail the Jackson-Biddle conflict. The episode is the strongest pre-1913 example of central-bank-versus-democracy tension that motivated later Fed design.")

q("central_banking_critique", "independent_treasury_1846_1913",
  "After the Second Bank's expiration (1836), the US operated under various banking arrangements until 1846 when President Polk established the Independent Treasury system. Under this system the federal government kept its own funds in 'sub-treasuries' rather than depositing them in banks. It operated until the Federal Reserve was created in 1913. What did this 67-year experiment demonstrate?",
  "The United States could function without a central bank, with the government keeping deposits separate from banks",
  "The Independent Treasury caused continuous economic collapse from 1846 to 1913 validating the need for the Fed widely",
  "The system was abandoned within five years of establishment due to its operational failure with deposits returning",
  "Independent Treasury operations were transferred to England under treaty in 1860 with the Bank of England managing",
  "The 1846-1913 period included real disturbances (Panics of 1857, 1873, 1893, 1907) but also rapid economic growth and rising living standards. The argument that 'banking panics' justified the Fed was made selectively.")

q("central_banking_critique", "panic_of_1907_pretext",
  "The Panic of 1907 was triggered by a failed attempt to corner the United Copper Company stock. The panic spread to banks associated with the speculators. J.P. Morgan personally organized a private rescue, locking bankers in his library until they pledged support. The panic was politically influential. What did Morgan's response prove to reform advocates?",
  "Private cooperation could end panics but was inadequate as a permanent system, motivating proposals for a central bank",
  "Central banking was unnecessary since Morgan had personally proven a private banker could resolve any panic without",
  "The US dollar should be replaced by a private currency issued by major Wall Street banks under British coordination",
  "Federal regulation of all banking was the only solution, leading directly to passage of Glass-Steagall in 1933",
  "The Aldrich-Vreeland Act (May 1908) created the National Monetary Commission, which traveled to Europe studying central banks and ultimately recommended the structure that became the Fed. The 1907 panic was the political pretext.")

q("central_banking_critique", "aldrich_vreeland_act_1908",
  "The Aldrich-Vreeland Act of May 1908 was a direct response to the Panic of 1907. The Act authorized emergency currency issuance and — more importantly — created the National Monetary Commission, chaired by Senator Aldrich. The Commission spent two years and over $200,000 traveling to Europe to study central banks. What did the Commission produce in 1910?",
  "The Aldrich Plan, drafted at the secret Jekyll Island meeting in November 1910, the blueprint for the 1913 Federal Reserve Act",
  "A comprehensive monetary history of the United States that documented every bank panic from 1789 through 1907 in volumes",
  "A proposed constitutional amendment requiring the United States to return to bimetallism with both silver and gold backing",
  "A series of recommendations for state-level banking regulation that were adopted by all forty-eight states 1911-1915",
  "The Commission's official report (1912) made the case for a central bank using European examples. The actual blueprint was drafted secretly at Jekyll Island the year before the report's release. The 'study' was political cover.")

q("central_banking_critique", "great_depression_unemployment_25_percent",
  "US unemployment rose from about 3% in 1929 to a peak of about 25% in 1933 — one in four Americans willing to work could not find a job. The Dow Jones fell from 381 in September 1929 to 41 in July 1932, an 89% decline. About 9,000 banks failed between 1930 and 1933. Friedman and Schwartz argued the Fed could have prevented this. What was their specific recommendation in retrospect?",
  "The Fed should have acted as lender of last resort and expanded the money supply during the 1930-33 banking panics",
  "The Fed should have raised interest rates aggressively during 1930-33 to attract foreign capital and stabilize banking",
  "The Fed should have been abolished in 1929 immediately after the crash, returning the United States to gold standard",
  "The Fed should have implemented exchange controls preventing capital flight which would have stabilized banking widely",
  "Friedman's monetarist critique: the Fed had the tools but failed to use them. Austrian critique: the Fed's prior easy-money policies (1920s) caused the bubble that crashed in 1929. Both critiques agree the Fed was the problem.")

q("central_banking_critique", "fdr_gold_confiscation_1933",
  "Executive Order 6102, signed by FDR on April 5, 1933, ordered Americans to surrender their gold to the Federal Reserve at $20.67 per ounce. After the surrender, Roosevelt revalued gold to $35 per ounce — a 41% devaluation of the dollar. Hoarding gold became a federal crime. What does this episode illustrate?",
  "Even nominally gold-backed currencies can be devalued by political authorities; genuine sound money requires unalterable constraints",
  "The American gold standard ended in 1933 voluntarily through democratic process demonstrating the institutional flexibility widely",
  "Gold confiscation was a temporary emergency measure that was reversed within five years as the economy recovered fully",
  "Roosevelt's gold confiscation was overturned by the Supreme Court in 1935 restoring private gold ownership entirely",
  "The 1933 confiscation was nominally lifted in 1974, but the precedent stands: a government with the power to compel can override gold-backed money. This is the lesson Hayek and modern Bitcoin proponents emphasize.")

q("central_banking_critique", "interest_on_reserves_2008",
  "In October 2008 the Federal Reserve began paying interest on bank reserves held at the Fed (IOER, later renamed IORB). Previously banks held reserves at zero interest. The policy allowed the Fed to expand its balance sheet through QE without flooding the economy with excess reserves. What broader consequence did paying-interest-on-reserves create?",
  "Banks could profitably park money at the Fed rather than lending to businesses, partially explaining weak credit growth",
  "Banks were forced to expand lending dramatically to compete with Fed payments, producing immediate 2009 credit growth",
  "The Federal Reserve became the largest lender to small businesses through reserve-payment arbitrage, replacing banks",
  "The policy was reversed within six months when it became clear it harmed recovery, returning to zero-interest reserves",
  "IOER changed the structural relationship between Fed policy and bank behavior. The 'ample reserves' regime that emerged after 2008 institutionalized this. Austrian critique: paying banks not to lend during a recession is the wrong incentive.")

q("central_banking_critique", "repo_market_crisis_sept_2019",
  "On September 17, 2019, the overnight repo market — where banks lend to each other — saw rates spike from about 2% to almost 10% in a single day. The Federal Reserve had to intervene with emergency lending of about $75 billion overnight. The intervention continued for months. What did this episode reveal about post-2008 financial architecture?",
  "The expanded post-2008 system requires continuous central-bank backstopping even during calm, indicating structural fragility",
  "The Federal Reserve's role had been successfully reduced after 2008 and the September 2019 spike was a one-time event",
  "Bank reserves were too high in September 2019 and the Fed needed to drain liquidity rather than add it to the system",
  "The September 2019 episode was caused by foreign central banks dumping US Treasury bonds in coordination with China",
  "The September 2019 repo crisis preceded the March 2020 pandemic intervention. Critics argued the system had become structurally dependent on continuous Fed support. The 'ample reserves' regime institutionalized emergency policy.")

# ============================================================================
# P5 PRACTICAL ECONOMICS (35 questions)
# ============================================================================

q("practical_economics", "smoot_hawley_june_1930",
  "The Smoot-Hawley Tariff Act was signed by Hoover on June 17, 1930, raising US import duties on over 20,000 goods to their highest levels in a century. Over 1,000 economists signed a public letter urging Hoover to veto. The stock market had crashed in October 1929; the Great Depression had begun. What was the international response?",
  "Foreign countries retaliated with their own tariffs; world trade fell about 65% between 1929 and 1934 deepening Depression",
  "Foreign countries expanded trade with the United States despite higher tariffs since American demand remained strong widely",
  "Foreign countries appealed Smoot-Hawley to the WTO which ordered its repeal within twenty-four months of passage",
  "Foreign countries imposed import tariffs only on luxury goods from the US leaving manufactured exports unaffected widely",
  "Smoot-Hawley is the canonical example of how protectionism deepens recessions. World trade fell from $5.3B (1929) to $1.8B (1934). Bastiat: visible 'protected American jobs' versus invisible collapse of export markets and consumer welfare.")

q("practical_economics", "smoot_hawley_consumer_cost",
  "Smoot-Hawley raised the average tariff on dutiable goods to about 60% by 1932. American consumers paid higher prices on tariffed imports. American exporters lost foreign markets as other countries retaliated. American workers in export industries lost jobs. What did Bastiat's broken-window analysis predict about this kind of policy?",
  "Visible benefit to protected industries would be smaller than invisible costs across consumers, exporters, and unemployment",
  "Protected industries would prosper indefinitely validating mercantilist trade policy and creating a stronger manufacturing base",
  "Consumer prices would fall as protected industries expanded production demonstrating tariffs benefit all participants widely",
  "Foreign nations would unilaterally lower their tariffs in response since US protectionism would force quality competition",
  "Smoot-Hawley vindicates Bastiat. The 'seen' was concentrated lobbying-active interests; the 'unseen' was diffuse consumer and exporter pain. Henry Hazlitt's *Economics in One Lesson* (1946) used tariffs as the central example.")

q("practical_economics", "nyc_rent_control_history",
  "New York City introduced rent controls during WWII under the federal Emergency Price Control Act of 1942. Unlike most jurisdictions, NYC kept controls after the war. The 1969 Rent Stabilization Law expanded controls. About one million NYC apartments remain under some form of price regulation today. What does the long-term evidence show?",
  "Severe shortage of available rental units, dramatically reduced new construction, and rationing by waiting lists not prices",
  "Abundant new construction and falling rents over the past fifty years demonstrating rent control produces affordability widely",
  "No measurable effect on housing supply or quality since rent control affects only nominal prices without changing behavior",
  "Higher housing quality across the city since landlords compete more vigorously when prices cannot rise above caps widely",
  "Edward Glaeser's *Triumph of the City* (2011) and Sowell's *Basic Economics* document NYC's pattern. Bastiat: lower controlled rent (seen) for current tenants comes at the cost of unbuilt apartments and reduced labor mobility (unseen).")

q("practical_economics", "san_francisco_prop_h_1979",
  "San Francisco passed Proposition H in November 1979, establishing strict rent control for most multi-family buildings constructed before June 1979. Stanford economists Diamond, McQuade, and Qian published a 2019 paper studying SF's rent control. They found rent control reduced rental housing supply by 15%. What was the net welfare effect?",
  "Welfare gain for incumbent tenants benefiting from below-market rent offset by larger welfare loss to future displaced tenants",
  "Net welfare gain for all city residents proven by the rising population of San Francisco throughout the four decades after",
  "No welfare effect detected since the study's methodology was discredited by subsequent academic critiques published in 2020",
  "Net welfare loss equal to the entire municipal budget of San Francisco for the period from 1979 through the most recent year",
  "The Diamond et al. (2019) paper appeared in *American Economic Review*. It quantified what Friedman, Sowell, and even Krugman (in a 2000 NYT op-ed) had warned about. The seen benefit was real; the unseen costs were larger.")

q("practical_economics", "sweden_rent_control_queue",
  "Sweden has the most extensive rent control system in Europe. Stockholm rental waitlists average 9+ years for an inner-city apartment; some take 25+ years to obtain through the queue. Subletting from queue-recipients to actual renters is illegal but common. What does this illustrate about rent control's seen-versus-unseen costs?",
  "Below-market rent (seen) creates a parallel black market and dramatic mismatches between who needs and who occupies housing",
  "Long queues prove that Stockholm has the most successful housing policy in Europe with subsidized rent benefits flowing widely",
  "Sweden's system demonstrates that rent control works well when administered by experienced socialist governments validating the model",
  "Stockholm's housing problems result from cold weather rather than rent control since other Nordic countries have similar climates",
  "The Swedish case is a useful comparison to Tokyo, where minimal housing regulation has produced relatively affordable housing in one of the world's largest cities. Property rights and supply elasticity matter; price controls do not.")

q("practical_economics", "card_krueger_1994_controversy",
  "Card and Krueger published a 1994 *American Economic Review* paper studying New Jersey's 1992 minimum wage increase. Their employment surveys showed no negative employment effect — possibly even a positive effect. The finding contradicted standard supply-and-demand predictions. The paper contributed to Card's 2021 Nobel Prize. What was the critical response?",
  "Neumark-Wascher's 2000 reanalysis used administrative payroll data rather than surveys and found the predicted negative effects",
  "All subsequent studies confirmed Card-Krueger's finding and the consensus shifted permanently to support minimum wage increases widely",
  "Card and Krueger retracted the 1994 paper in 1998 after a series of methodological errors were uncovered by graduate students",
  "The Card-Krueger finding only applied to teenagers and was confirmed for adult workers in a series of follow-up studies later",
  "The Card-Krueger paper kicked off a long debate. Even if some minimum wage increases have small employment effects, the seen-versus-unseen analysis still applies: workers priced out of entry-level jobs versus those who keep their jobs.")

q("practical_economics", "seattle_2017_jardim_study",
  "Seattle raised its minimum wage to $13 in 2016 and $15 in 2017. The University of Washington commissioned a study by Jardim et al. using detailed Seattle payroll data — not surveys. Their 2017 NBER paper found that the wage increase reduced hours worked by low-wage workers enough to LOWER total earnings. What was the policy implication?",
  "Higher wages priced some workers out of the market with lost work hours exceeding the gain from higher hourly pay for the rest",
  "The minimum wage increase substantially raised total earnings for low-wage workers in Seattle exactly as progressive models predicted",
  "The study found no measurable effect of the wage increase on low-wage workers' total earnings validating the case for increases",
  "Seattle's economy collapsed after the wage increase with citywide unemployment rising to twenty-five percent within twelve months",
  "The Jardim et al. (2017) study used a much richer dataset than Card-Krueger. Some workers benefited; others lost more in hours than they gained. Bastiat: visible higher hourly wage versus invisible cuts in hours and entry opportunities.")

q("practical_economics", "ricardo_1817_portugal_england_deep",
  "David Ricardo's 1817 *On the Principles of Political Economy and Taxation* introduced comparative advantage with a Portugal-England thought experiment. Ricardo posited that Portugal could produce both wine and cloth with less labor than England, but Portugal's wine production was even MORE efficient than its cloth. What did Ricardo demonstrate?",
  "Even when one country has absolute advantage in both goods, both gain from specializing where opportunity cost is lower",
  "Free trade always benefits the country with absolute advantage in production but the partner country always loses widely",
  "Comparative advantage applies only between developed economies since underdeveloped nations cannot benefit from specialization",
  "Ricardo's theory was disproven by the 19th-century industrial revolution which demonstrated protectionism produces faster growth",
  "Ricardo's insight remains one of economics' most counterintuitive: trade benefits even unilaterally less-productive partners. Paul Samuelson called comparative advantage the only economic principle that is both true and non-trivial.")

q("practical_economics", "ricardian_intellectual_property",
  "Ricardo's comparative advantage applied to physical goods in 1817. The 21st-century analog applies to intellectual production: countries with different educational systems, regulatory environments, and capital stocks have different comparative advantages in software, pharmaceuticals, films, semiconductors. What does Ricardo suggest about 'reshore everything' policies?",
  "Reshoring all production sacrifices comparative-advantage gains across industries, reducing total wealth for political appearance",
  "Reshoring always strengthens national economies by capturing every stage of value-added production within domestic boundaries",
  "Comparative advantage applies only to agricultural goods and not to manufactured or service-sector products in modern markets",
  "Ricardo's theory was developed for the gold standard era and does not apply to modern fiat-currency economies under floating rates",
  "Modern restatement: opportunity cost still matters. Even when reshoring would 'protect' visible domestic industries, the invisible costs (higher prices, less innovation, foreign retaliation) typically exceed the gains.")

q("practical_economics", "leonard_read_i_pencil_1958",
  "Leonard Read wrote 'I, Pencil' in 1958, published by the Foundation for Economic Education. The essay is a first-person narrative from a pencil's perspective explaining its own creation. No single person on earth knows how to make a pencil: cedar from California, graphite from Sri Lanka, rubber from Indonesia. What did Read intend to illustrate?",
  "Spontaneous order, with millions producing pencils without any central plan, coordinated by prices that encode dispersed knowledge",
  "The pencil industry has been captured by a monopoly that controls all aspects of pencil production globally through cartel",
  "Modern manufacturing requires extensive government regulation to ensure quality, safety, and fair labor practices in supply chains",
  "Pencil production should be reshored to the United States through trade restrictions since current supply chains are inefficient",
  "Milton Friedman highlighted 'I, Pencil' in his 1980 *Free to Choose* TV series. The essay is the modern restatement of Smith's invisible hand and Hayek's knowledge problem in one accessible parable.")

q("practical_economics", "common_law_spontaneous_order",
  "Hayek's spontaneous order extends beyond markets. English common law developed for centuries through case-by-case judicial decisions without any central legislature designing it. Judges responded to disputes; precedents accumulated. What does Hayek's framework say about deliberately replacing common law with comprehensive legislative codes?",
  "Risks substituting a designer's limited knowledge for centuries of accumulated case-by-case judgments, producing rigid law",
  "Always produces superior legal results since legislative codes can be rationally designed by trained experts from first principles",
  "Has no effect on legal outcomes since the same principles emerge from either common law or legislative codes under any conditions",
  "Is required for modern economies since common law cannot accommodate technological change or financial innovation widely",
  "Hayek's *Law, Legislation and Liberty* (1973-79, three volumes) develops this argument. Bruno Leoni's *Freedom and the Law* (1961) anticipated parts. Spontaneous order is accumulated experience versus a single designer's limited view.")

q("practical_economics", "language_spontaneous_order",
  "Human languages — Mandarin, Spanish, English, Yoruba, Hindi — were not designed by anyone. They evolved through millions of speech acts over thousands of years. Grammars are formalizations after the fact. Attempts to design 'rational' artificial languages (Esperanto, Volapük) have produced small communities but no major usage. What does this teach?",
  "Bottom-up evolution from many decisions tends to produce more usable systems than top-down designs from a few experts widely",
  "Top-down design always produces more efficient outcomes than evolution since experts coordinate decisions across participants",
  "Natural and constructed languages are equally usable since linguistic communication is purely arbitrary convention regardless of source",
  "Esperanto became the world's most-spoken language between 1887 and 1939 demonstrating the success of rational design over evolution",
  "Hayek extended his market argument: spontaneous order applies to law, language, money, and morals. Friedrich Carl von Savigny in 19th-century legal theory argued similar points. The lesson: humility about what we can centrally design.")

q("practical_economics", "internet_protocols_voluntary",
  "The Internet's underlying protocols (TCP/IP, HTTP, DNS, SMTP) were developed by working groups — the Internet Engineering Task Force (IETF) — operating by 'rough consensus and running code.' No central authority designed the Internet; no government created its standards. Yet billions of devices interoperate. What does this illustrate?",
  "Voluntary standards developed by participants who use them produce more robust systems than top-down regulation imposed widely",
  "Government regulation is required for technological standards even when initial development happened through voluntary working groups",
  "The Internet succeeded only because the US government funded its initial development through DARPA validating federal research support",
  "Internet protocols would have been better if designed by a single central authority since the current system has interoperability problems",
  "While DARPA funded early ARPANET research, the actual protocol design and ongoing maintenance has been overwhelmingly voluntary and decentralized. The Internet is a vast natural experiment in Hayekian spontaneous order at technological scale.")

q("practical_economics", "buchanan_tullock_calculus_consent_deep",
  "Buchanan and Tullock's *The Calculus of Consent* (1962) applied economic methodology — rational self-interest, marginal analysis — to political institutions. Their key insight: political actors are not benevolent guardians; they pursue their own interests. The book founded 'public choice theory.' Buchanan won the 1986 Nobel. What was the intellectual impact?",
  "Reframing the 'market failure leads to government fix' argument to require comparing imperfect markets to imperfect governments",
  "Establishing the dominance of Keynesian economics in American universities through the next four decades after publication widely",
  "Discrediting the entire field of welfare economics which has since been abandoned by all major university programs in economics",
  "Demonstrating that representative democracy always produces optimal economic outcomes when politicians are properly motivated widely",
  "Public choice has been called 'politics without romance' — the political analogue of the economic-calculation revolution. The framework dissolves many traditional pro-intervention arguments by removing the unstated assumption of benevolence.")

q("practical_economics", "buchanan_constitutional_economics",
  "Buchanan's later work developed 'constitutional economics' — the study of rules that constrain political decision-making. His insight: if politicians are self-interested, what matters is designing better constraints. Constitutions, balanced-budget amendments, term limits all reduce self-interest's room. What does this share with Hayek?",
  "Both emphasized rules over discretion recognizing that discretionary power tends to be used in self-interested ways over time",
  "Both believed virtuous individuals in positions of power produce better outcomes than rule-based constraints under any conditions",
  "Both rejected the idea that economic institutions matter to outcomes focusing entirely on personal character of decision-makers",
  "Both supported direct democracy through citizen referendums on every major decision rejecting representative democracy entirely",
  "Buchanan and Hayek converged on rules-versus-discretion. The k-percent rule, balanced-budget amendments, term limits, and Bill of Rights all reflect this framework. The 2008-2024 Fed's reliance on discretion is what both critique.")

q("practical_economics", "stigler_1971_theory_economic_regulation",
  "George Stigler's 1971 paper 'The Theory of Economic Regulation' established the concept of 'regulatory capture' — the tendency for regulators to come to serve the interests of the industries they regulate rather than the public interest. Stigler won the 1982 Nobel partly for this work. What is the mechanism Stigler identified?",
  "Concentrated benefits create strong lobbying incentives; diffuse costs create weak ones, so regulators serve concentrated interests",
  "Regulatory agencies hire only employees who previously worked for the regulated industries creating direct conflict by design",
  "Politicians appoint corrupt regulators in exchange for campaign contributions, the entire mechanism operating through quid-pro-quo",
  "Regulated firms threaten the personal safety of regulators who comply with industry demands out of fear rather than reason",
  "Stigler's mechanism is structural rather than personal. Mancur Olson's *Logic of Collective Action* (1965) supplies the underlying analysis: small groups with concentrated interests organize more effectively than large groups with diffuse interests.")

q("practical_economics", "tullock_1967_rent_seeking",
  "Gordon Tullock published 'The Welfare Costs of Tariffs, Monopolies, and Theft' in 1967, introducing what became known as 'rent-seeking analysis.' Tullock's insight: traditional analysis measured only the 'deadweight loss' from monopoly. But firms spend real resources competing for monopoly privileges — lobbying, lawyers, contributions. What did this imply?",
  "Real cost of monopoly privilege equals deadweight loss PLUS the value of all resources spent competing for the privilege",
  "Monopoly privileges produce no real welfare cost since competition among firms for the privilege ensures the most efficient wins",
  "Lobbying expenditure is a transfer rather than a cost since the money paid to lobbyists is then spent productively elsewhere",
  "Anne Krueger's later work proved Tullock's analysis was wrong about the rent-seeking cost which is actually much smaller than DWL",
  "Anne Krueger's 1974 paper 'The Political Economy of the Rent-Seeking Society' coined the term and extended Tullock's analysis. Combined deadweight + rent-seeking welfare loss can be very large — sometimes a substantial fraction of GDP.")

q("practical_economics", "cronyism_vs_free_market",
  "Critics of 'capitalism' often point to corporate influence on government, bailouts of failing firms, and politically-connected billionaires becoming wealthier as the economy worsens for ordinary workers. These critics conclude 'capitalism doesn't work.' What is the public-choice / Austrian response?",
  "Critics conflate two different systems: what they describe is cronyism (politically-allocated rents), not free-market competition",
  "Accept the criticism as correct and advocate for replacing capitalism with central economic planning under democratic supervision",
  "Argue that corporate influence on government is necessary for economic growth since well-connected firms create more jobs than others",
  "Maintain that no real distinction exists between free markets and cronyism since both produce concentration of wealth in firms",
  "The distinction between free-market capitalism and crony-corporate cooperation with government is central. Bastiat's broken-window applies: bailouts produce unseen costs (taxpayer losses, signal corruption, moral hazard) exceeding seen benefits.")

q("practical_economics", "black_markets_bastiat_lesson",
  "Black markets emerge whenever a government prohibits voluntary exchanges that participants value. US alcohol Prohibition (1920-33), Soviet bread queues, Venezuelan dollar trading, online drug markets, Cuban cigar smuggling. Each prohibition creates a parallel illegal market. What is Bastiat's framework for understanding this pattern?",
  "Visible prohibition does not eliminate the underlying demand; it shifts activity into a parallel market with worse outcomes for all",
  "Prohibition always eliminates the prohibited activity completely when enforcement is sufficient with no parallel market emerging",
  "Black markets are caused by foreign infiltration of national economies rather than by domestic price controls or product prohibitions",
  "The existence of black markets proves that all voluntary exchange is illegitimate and should be replaced with state-allocated rations",
  "Bastiat's framework applies to every prohibition. The 'seen' benefit is the official prohibition; the 'unseen' costs include violence, corruption, quality decline, and consumer pain. Prohibition's track record is the strongest empirical case.")

q("practical_economics", "broken_window_stimulus_framing",
  "After Hurricane Katrina (2005), some commentators argued destruction would 'stimulate' the economy as rebuilding occurred. After 9/11, similar arguments appeared. The reasoning: construction firms get work, suppliers sell materials, workers earn wages. What does Bastiat's broken-window analysis say?",
  "Destruction does not create wealth: resources used for rebuilding could have built new things, so society is poorer by what was lost overall",
  "Destruction creates economic stimulus equal to the value destroyed, validating the popular framing that disasters benefit the economy widely",
  "Destruction reduces unemployment but has no effect on total wealth, since reconstruction labor would have been unemployed otherwise overall",
  "Bastiat's analysis applies only to small-scale destruction like single windows, not to large-scale events like hurricanes affecting regions",
  "The Bastiat broken-window framework is the cleanest economic lesson. After Katrina, Paul Krugman wrote a NYT column arguing the destruction might be net stimulus. Henry Hazlitt and free-market economists pointed out this was the fallacy.")

q("practical_economics", "war_economy_stimulus_fallacy",
  "Some economists argued in the late 1930s that WWII ended the Great Depression by stimulating economic activity through military spending and mass employment. Others including Hazlitt and Robert Higgs argued this was the broken-window fallacy at large scale. What does Higgs's *Depression, War, and Cold War* (2006) document?",
  "GDP statistics overstated wartime prosperity since military production counted, but consumer goods were rationed and real standards fell",
  "WWII military spending unquestionably ended the Great Depression by providing fiscal stimulus that no peacetime program had delivered",
  "The Great Depression actually intensified during World War II with US GDP falling by twenty percent between 1942 and 1944 despite spending",
  "WWII spending raised consumer living standards above prewar levels demonstrating that deficit spending raises welfare during war widely",
  "Higgs's empirical work shows real prosperity arrived after the war (1946 onward) as wartime controls were lifted and civilian production resumed. The 'wartime stimulus' is a statistical artifact of counting military production as GDP.")

q("practical_economics", "agricultural_subsidies_seen_unseen",
  "US agricultural subsidies cost taxpayers tens of billions annually. Defenders argue subsidies preserve family farms, protect food security, and stabilize rural communities. Critics argue subsidies benefit large agribusiness, raise consumer food prices, and harm developing-country farmers. How does Bastiat's framework analyze this debate?",
  "Visible benefits to subsidy recipients are real, but the larger invisible costs (taxpayer, food prices, foreign farmers) exceed them",
  "Agricultural subsidies always produce net economic benefits because food security is the most important economic concern in any economy",
  "Agricultural subsidies have no measurable economic effects since the costs and benefits exactly cancel out across all participants widely",
  "Agricultural subsidies should be tripled to ensure food security since the current level is too low to maintain the rural way of life",
  "The 'seen' beneficiaries are concentrated and politically active. The 'unseen' costs are diffuse and politically weak. Public choice theory predicts concentrated benefits + diffuse costs = persistent rent-seeking.")

q("practical_economics", "occupational_licensing_seen_unseen",
  "About 25% of US workers need an occupational license to legally work — up from about 5% in the 1950s. Hair braiders, florists, manicurists, and interior designers in many states require hundreds of hours of training and state certification. Sociologist Morris Kleiner documents the spread. Who benefits, and who pays?",
  "Existing practitioners benefit by restricting entry; consumers pay through higher prices and reduced availability without quality gains",
  "Consumers benefit from licensing through guaranteed service quality with the visible costs of higher prices outweighed by safety enforcement",
  "No party benefits or loses since occupational licensing has no measurable economic effects on practitioners or consumers in any market",
  "Licensed practitioners always offer higher quality services than unlicensed competitors in every empirical study over the past decades",
  "Kleiner's research and Institute for Justice litigation document how licensing operates as classic rent-seeking. The 'public protection' framing is the seen justification; reduced economic mobility and higher consumer costs without quality gains is unseen.")

q("practical_economics", "auto_industry_bailout_2009",
  "The Obama administration bailed out GM and Chrysler in 2009 with about $80 billion in federal funds. Both companies emerged from managed bankruptcy with substantially reduced obligations to creditors. Critics including Senator McConnell argued the bailouts were unprecedented interventions in private bankruptcies. What does seen-versus-unseen analysis say?",
  "Saved jobs at GM and Chrysler were visible; the foregone restructuring (jobs shifting to Ford and Toyota US plants) was the unseen cost",
  "The 2009 bailouts unambiguously benefited the entire US economy by preventing a complete collapse of the auto industry that depression",
  "The 2009 bailouts had no measurable economic effects since the auto industry would have recovered identically through normal bankruptcy",
  "The bailouts harmed competing companies (Ford, Toyota's US plants) through restricting their growth opportunities while propping up rivals",
  "Ford famously declined federal money and managed through the recession on its own. The Bastiat analysis: 'saved' GM jobs are seen and counted; auto industry restructuring that would have transferred work to better-run firms is unseen.")

q("practical_economics", "sugar_quotas_consumer_cost",
  "US sugar quotas restrict imported sugar to maintain domestic prices at roughly 2x the world price. USDA estimates the quota costs American consumers approximately $3-4 billion annually in higher prices. About 4,500 sugar farmers benefit. Confectionery makers (Hershey, Mars) lose business and have moved some production to Mexico. What does this illustrate?",
  "Highly concentrated benefits to a small group create strong lobby; widely diffused costs to millions of consumers fail to organize",
  "Sugar quotas benefit all American workers equally by protecting a key domestic industry that supports manufacturing employment widely",
  "Sugar quotas have no measurable economic effects because consumer adjustments offset the policy through substitution toward sweeteners",
  "Sugar quotas should be expanded to all agricultural commodities to protect more American workers from foreign competition immediately",
  "The sugar quota is the textbook public choice example. About 4,500 producers organize to influence policy effectively; 330 million consumers each pay an extra $10/year on sugar products and can't coordinate opposition. Olson 1965 in action.")

q("practical_economics", "moral_hazard_too_big_to_fail",
  "After the 2008 bailouts of Bear Stearns, AIG, Citigroup, Bank of America, and Goldman Sachs through TARP, many critics argued the rescues created 'moral hazard' — expectations of future bailouts would encourage banks to take more risk, since losses would be socialized while gains remained private. What does the subsequent record show?",
  "The largest banks grew substantially as a percentage of US banking assets after 2008, validating concerns about reinforcing too-big-to-fail",
  "The largest banks shrank substantially as a percentage of US banking assets after 2008 validating regulators' claims that Dodd-Frank ended it",
  "US banking concentration remained perfectly constant between 2008 and 2024 with no measurable effect from any post-crisis regulatory changes",
  "Smaller community banks completely replaced the major investment banks by 2015 ending all concerns about banking concentration risks fully",
  "The top five US banks hold a substantially larger share of US banking assets in 2024 than they did in 2008. Moral hazard concerns are validated. The Mises lesson: bailouts produce more bailouts.")

q("practical_economics", "education_cost_inflation_subsidy",
  "US higher education tuition has grown by about 1200% since 1980 while CPI has roughly tripled. Federal student loan programs expanded substantially over this period. Bennett Hypothesis (William Bennett, 1987): subsidies enable higher tuition. What does Bastiat's framework suggest?",
  "Subsidies to demand allow producers to raise prices, so visible benefit (affordability) hides the unseen cost (tuition captures aid)",
  "Federal subsidies kept tuition prices stable by funding institutional growth that scaled with demand throughout 1980-2024 nationally",
  "The relationship between subsidies and tuition is purely coincidental since higher education prices follow inflation indices in all economies",
  "Federal subsidies should be tripled to lower tuition costs further by enabling universities to expand capacity through additional funding",
  "The Bennett Hypothesis has substantial empirical support. New York Fed research (2015) and other studies document that increases in federal student aid are associated with tuition increases. Subsidy capture is a classic unseen cost.")

q("practical_economics", "housing_subsidy_capture",
  "Federal housing assistance (Section 8 vouchers, mortgage interest deductions, FHA loans) costs hundreds of billions. Yet US housing affordability has worsened in major metros. Demand-side subsidies in markets with restricted supply tend to raise prices rather than expand consumption. What does this suggest?",
  "Supply restrictions (zoning, review, land-use controls) must be fixed for subsidies to lower prices; demand subsidies capitalize into prices",
  "Federal housing subsidies have made housing dramatically more affordable across all US metros with measurable price decreases since 1970",
  "Housing markets respond differently than other markets to subsidies, with prices falling in response to demand support consistently widely",
  "All US housing problems result from insufficient federal funding, requiring at least a tripling of current subsidy programs in the decade",
  "Edward Glaeser's research and the YIMBY movement converge on this analysis. Bastiat: visible subsidy benefit is captured by sellers in supply-restricted markets, leaving consumers no better off.")

q("practical_economics", "import_quotas_japan_autos_1981",
  "In 1981 the Reagan administration negotiated 'voluntary export restraints' (VERs) with Japan capping Japanese auto exports at 1.68 million vehicles per year. Stated goal: protecting Detroit. American consumers paid higher prices. Japanese automakers responded by building US plants (Honda Marysville 1982, Nissan Smyrna 1983). What was the long-run effect?",
  "Consumers paid an estimated $5 billion annually in higher prices; Japanese automakers expanded US production, complicating the goal",
  "Detroit automakers gained permanent market share and the Japanese auto industry never recovered from the 1981 restraints in the decade",
  "American consumers benefited from substantially lower auto prices throughout the 1980s due to the increased competition created by quotas",
  "The quotas were lifted within six months due to consumer pressure ending the policy before any measurable economic effects could occur",
  "Robert Crandall's research at Brookings documented the consumer cost. The 'protected' US auto industry continued losing market share. Bastiat: visible Detroit jobs versus invisible higher consumer prices and lost export jobs.")

q("practical_economics", "uber_rideshare_disruption_2010s",
  "Uber launched in 2009 in San Francisco. Within a decade ride-sharing had largely replaced traditional taxis in most American cities. NYC's medallion taxi system, where a medallion cost over $1 million in 2013, collapsed in value with thousands of medallion holders bankrupted. What does this illustrate?",
  "Government-created barriers to entry created artificial scarcity rents (taxi medallions), destroyed when technology enabled regulatory bypass",
  "Uber and Lyft were illegal across all major American cities and have been progressively shut down by court orders throughout the years",
  "New York taxi medallions remain worth approximately one million dollars each as of 2024 demonstrating the durability of regulatory rents",
  "The traditional taxi industry adapted successfully to ride-sharing competition with no major changes in service quality or pricing entirely",
  "Medallion holders paid for a government-created monopoly position. When technology made the regulation unenforceable, the rent disappeared. The 'unseen' cost of decades of consumer pain became visible only when ride-sharing offered the comparison.")

q("practical_economics", "broken_window_postpandemic_2021",
  "After COVID-19 lockdowns ended in 2021, some commentators argued the resulting 'reopening boom' demonstrated the lockdowns themselves had been economically beneficial — pent-up demand was being released, GDP was growing rapidly, stocks were rising. What does Bastiat's broken-window analysis say about 'lockdowns produced growth' framing?",
  "Recovery from forced contraction is not the same as economic gain; the visible reopening growth masks the real losses sustained earlier",
  "Lockdowns unambiguously caused the strong post-2021 economic growth, validating government intervention as a productive economic policy widely",
  "The 2021 economic recovery was caused entirely by federal fiscal stimulus with no relationship to the timing of lockdown policies or removal",
  "Lockdowns had no measurable economic effects since the COVID virus would have caused identical economic contraction in any voluntary-response",
  "Broken-window applies: smashing the window (or locking down) and then 'repairing' the damage (reopening) does not produce wealth. The 'reopening boom' simply restored some of what had been destroyed during the closure period.")

q("practical_economics", "inflation_as_tax_savers_cantillon",
  "Inflation transfers wealth from cash holders and savers to those who first receive newly-printed money. Wage-earners see salaries lag rising prices. Retirees on fixed incomes lose purchasing power. Asset owners generally benefit. This is the Cantillon effect at scale. What does this reveal about fiscal policy?",
  "Deficit spending funded by money creation operates as a hidden tax on savers and wage-earners, transferring resources to early recipients",
  "Inflation affects all economic participants equally and uniformly with no measurable wealth transfer between income or asset classes ever",
  "Inflation primarily benefits wage-earners and retirees through automatic cost-of-living adjustments that fully offset all price increases widely",
  "Modern central banks have entirely eliminated the Cantillon effect through technological improvements in monetary policy implementation since",
  "The 2020-22 inflation episode produced widening inequality precisely because asset-holders saw nominal gains while wage-earners saw real losses. Bastiat-style: visible 'stimulus' benefited some while invisible costs were borne by others.")

q("practical_economics", "regulation_as_barrier_to_entry",
  "George Stigler observed that established firms in regulated industries often LOBBY FOR additional regulation. Regulations are expensive to comply with. Established firms can absorb the cost; new entrants cannot. Regulation becomes a barrier to entry protecting incumbents from competition. What does this illustrate?",
  "Regulation can serve the regulated industry rather than the public, reversing the conventional framing that regulation protects consumers",
  "Established firms always oppose regulation since compliance costs reduce profits making industry-supported regulation contradictory in markets",
  "Regulation never serves industry interests since regulators are always neutral arbiters between consumers and firms in any developed economy",
  "Regulatory capture only applies to small industries with concentrated firms not to large industries with many competing firms in markets",
  "Bruce Yandle's 'Bootleggers and Baptists' (1983) developed this analysis: moral campaigners (Baptists) and self-interested incumbents (bootleggers) often coalition for the same regulation. Prohibition produced both winners.")

q("practical_economics", "tragedy_of_commons_property_rights",
  "Garrett Hardin's 1968 'Tragedy of the Commons' argued unowned common resources tend to be overused: each user has incentive to take more, since the cost is shared and the benefit is private. Hardin used grazing land as his canonical example. What is the standard Austrian/property-rights solution to commons problems?",
  "Establish secure property rights, so owners have incentive to maintain the resource by bearing costs of overuse and capturing benefits",
  "Establish government regulation of every common resource with detailed rules about acceptable use enforced by federal agencies with budgets",
  "Establish public ownership of all natural resources through nationalization which has historically produced superior conservation outcomes",
  "Establish religious prohibitions against overuse which is the only effective method humans have ever developed to prevent commons tragedies",
  "Elinor Ostrom won the 2009 Nobel partly for showing that local institutions can manage commons without formal property rights or government enforcement. The deeper lesson: incentive structures matter more than the specific institutional form.")

q("practical_economics", "tariffs_who_pays_2018_2024",
  "Trade economists Casselman, Tankersley, and others studying the 2018-2024 US tariffs on Chinese goods found that the tariffs were primarily paid by US importers and US consumers, not by Chinese exporters. Studies by Amiti, Redding, Weinstein (2019) and Fajgelbaum et al. (2020) reached similar findings. What does Bastiat's analysis predict?",
  "Tariffs operate as taxes on the importing country's own consumers, with the seen 'protection' delivering an unseen cost to households",
  "Tariffs always benefit the imposing country by extracting revenue from foreign exporters, who cannot pass costs back to consumers",
  "Tariffs have no measurable effect on prices in modern economies due to substitution effects across global supply chains and markets",
  "Tariffs raise wages in protected industries by enough to offset higher consumer prices, producing net gains in the imposing country",
  "Bastiat anticipated this pattern in 1850. Modern empirical work confirms it. The 'seen' is the protected industry; the 'unseen' includes consumer cost, retaliation against exporters, and the loss of efficiency from misallocated production.")


# ============================================================================
# Save + report
# ============================================================================

def save() -> None:
    OUT.write_text(json.dumps({
        "tier": 4,
        "summary": {
            "questions_generated": len(QUESTIONS),
            "by_pillar": {
                "3": sum(1 for q in QUESTIONS if q.get("topic_cell") == "sound_money_history"),
                "4": sum(1 for q in QUESTIONS if q.get("topic_cell") == "central_banking_critique"),
                "5": sum(1 for q in QUESTIONS if q.get("topic_cell") == "practical_economics"),
            },
        },
        "questions": [
            {
                "tier": q["tier"],
                "question": q["question"],
                "answer": q["answer"],
                "choices": q["choices"],
                "context": q["context"],
                "_meta": q.get("_meta", {}),
            }
            for q in QUESTIONS
        ],
    }, indent=2, ensure_ascii=False), encoding="utf-8")


def report() -> None:
    print(f"Generated: {len(QUESTIONS)}")
    print(f"  P3 sound_money_history: {sum(1 for q in QUESTIONS if q['topic_cell'] == 'sound_money_history')}")
    print(f"  P4 central_banking_critique: {sum(1 for q in QUESTIONS if q['topic_cell'] == 'central_banking_critique')}")
    print(f"  P5 practical_economics: {sum(1 for q in QUESTIONS if q['topic_cell'] == 'practical_economics')}")
    if ERRORS:
        print(f"\nLOCAL ERRORS ({len(ERRORS)}):")
        for e in ERRORS[:30]:
            print(f"  {e}")
    else:
        print("LOCAL ASSERTS: ALL CLEAN")


def validate_all() -> None:
    print("\nValidating against gates...")
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    dup_idx, ans_idx = build_bank_indices(bank)
    pass_n = soft_n = fail_n = 0
    fail_details: list[str] = []
    for i, q_obj in enumerate(QUESTIONS):
        clean = {k: q_obj[k] for k in ("tier", "question", "answer", "choices", "context")}
        r = validate_rewrite("economics", clean, bank=bank, dup_index=dup_idx, answer_index=ans_idx, replace_idx=None)
        if r["verdict"] == "PASS":
            pass_n += 1
        elif r["verdict"] == "SOFT_WARN":
            soft_n += 1
            soft_msgs = "; ".join(f"{g}: {m}" for g, m in r["soft_warns"])
            print(f"  [{i}] SOFT: {q_obj['question'][:60]}... | {soft_msgs}")
        else:
            fail_n += 1
            hard_msgs = "; ".join(f"{g}: {m}" for g, m in r["hard_fails"])
            fail_details.append(f"  [{i}] FAIL: {q_obj['question'][:80]}... | {hard_msgs}")
    print(f"\nValidation: PASS={pass_n}  SOFT={soft_n}  FAIL={fail_n}")
    if fail_details:
        print("\nFAILURES:")
        for f in fail_details:
            print(f)


if __name__ == "__main__":
    report()
    save()
    validate_all()
