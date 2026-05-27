"""Generate 120 fresh Tier-3 economics questions (P3/P4/P5).

T3 hard cap: question + 4 choices <= 680 chars (grace 714). Target ~620.
Em-dash uniform. Story-in-stem from day 1. NOT anti-government.
ANSWER_OUTLIER 1.6x rule.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402

P3: list[dict] = []
P4: list[dict] = []
P5: list[dict] = []
OVER_BUDGET: list = []


def q(pillar_list: list[dict], strategy: str, question: str, answer: str,
      ch2: str, ch3: str, ch4: str, context: str) -> None:
    total = len(question) + len(answer) + len(ch2) + len(ch3) + len(ch4)
    if total > 680:
        OVER_BUDGET.append((strategy, total, question[:60]))
    pillar_list.append({
        "tier": 3,
        "question": question,
        "answer": answer,
        "choices": [answer, ch2, ch3, ch4],
        "context": context,
        "_strategy": strategy,
        "_pillar": 3 if pillar_list is P3 else 4 if pillar_list is P4 else 5,
    })


# =========================================================================
# PILLAR 3 — SOUND MONEY + HYPERINFLATION (40)
# =========================================================================

# --- Cantillon / John Law (4) ---

q(P3, "cantillon_john_law",
   "Richard Cantillon was a banker who knew John Law personally — the Scot whose paper-money Mississippi Company collapsed in France in 1720. Cantillon noticed something deep about how new money spread. What did he see?",
   "First receivers buy at OLD prices — late receivers face risen prices and lose",
   "All prices rose immediately at the same rate across the entire economy",
   "New money lifted wages first, so the poor benefited before merchants",
   "New money had no price effect — the collapse was foreign-exchange driven",
   "Cantillon's *Essai sur la Nature du Commerce* (~1730, published 1755) is the first systematic monetary economics. The Cantillon effect names a permanent feature of monetary inflation.")

q(P3, "cantillon_modern_qe",
   "When a modern central bank does 'quantitative easing,' new money flows first to primary-dealer banks, then to stocks and real estate, only later to consumer prices. Richard Cantillon predicted this in the 1700s. Why does the ORDER matter?",
   "Asset holders sell at lifted prices before wage earners see inflation — savers and workers taxed silently",
   "Asset holders see no benefit until consumer prices already adjusted — QE is a uniform delayed lift",
   "Consumer goods rise first because food and energy are most monetarily sensitive",
   "Central banks route new money to wage earners first to ensure broad-based growth",
   "The Cantillon effect explains why post-2008 QE coincided with massive stock and real-estate gains before CPI inflation appeared. The wealth transfer was real even when CPI looked tame.")

q(P3, "john_law_mississippi",
   "John Law fled to France after killing a man in a duel. By 1716 he had convinced the regent to back paper money with Mississippi Company shares — Louisiana land France could not develop. The bubble crashed 1720. What's the canonical lesson?",
   "Paper money on speculative promises always inflates and collapses — France avoided paper for 80 years",
   "Law's system was sound but sabotaged by political enemies who triggered collapse",
   "The bubble was caused by Dutch tulip speculation, not monetary policy at all",
   "Law's system worked perfectly — the canonical example of successful paper money",
   "Law's collapse left France traumatized by paper money for generations. Cantillon watched from inside and wrote the first systematic critique. Every later fiat collapse rhymes with this one.")

q(P3, "cantillon_recognition",
   "A homeowner 'gains' $100,000 over five years of low Fed rates. A renter watches rent and food climb while wages stagnate. Both are seeing the SAME phenomenon from opposite sides. What is it?",
   "The Cantillon effect — monetary expansion lifts assets before wages, helping owners and hurting renters",
   "Normal market growth from population pressure unrelated to monetary policy at all",
   "Supply shortages — building costs raised houses while labor shortages drove food",
   "Pure psychology — homeowners feel rich, renters feel poor, for unrelated reasons",
   "The Cantillon effect (named for the 18th-century banker) is the broken-window analysis applied to central banking. The 'wealth effect' is real and also a wealth transfer.")

# --- Gold standard 1870-1914 (3) ---

q(P3, "classical_gold_standard",
   "From 1870-1914, Britain, France, Germany, the US, and dozens of others fixed their currencies to specific weights of gold. International trade settled smoothly; long-run inflation was near zero. The British pound bought about the same goods in 1914 as 1870. What ended it?",
   "World War I — every belligerent suspended gold convertibility to print for the war",
   "The 1929 crash — bankers blamed gold and abandoned it in one coordinated action",
   "The 1944 Bretton Woods Conference voted unanimously to replace gold with pure paper",
   "Discovery of California and South Africa gold — supply tripled, breaking the math",
   "The classical gold standard (1870-1914) is the high-water mark for international sound money. Suspended for WWI, partially restored in the 1920s, broken by the Depression, ended entirely by Nixon in 1971.")

q(P3, "gold_standard_stability",
   "Under the classical gold standard (~1870-1914), Britain's price level was about the SAME in 1914 as in 1870. The dollar held similar purchasing power across the same decades. What constraint produced this stability?",
   "Money supply tied to a physical metal whose extraction was slow — governments could not just print",
   "Active inflation-targeting at the Bank of England kept prices flat for 44 years",
   "Wage and price controls by Parliament held the price level constant through the period",
   "Population growth happened to offset money-supply growth by statistical coincidence",
   "Gold's scarcity is the feature. The constraint that frustrated activist policymakers — you cannot print gold — protected savers and wage-earners for 44 years.")

q(P3, "churchill_1925",
   "After WWI, Britain returned to gold in 1925 at the prewar parity. Churchill (then Chancellor) later called it his worst mistake. Keynes attacked the move in *The Economic Consequences of Mr. Churchill* (1925). Why was it botched?",
   "Britain returned at the OLD parity even though it had inflated during the war — deflation crushed exports",
   "Britain returned at a lower parity but France and US conspired to undermine the pound",
   "Britain returned to gold but the Bank of England forgot to update its ratios",
   "Britain returned only on paper — the actual reserves had been spent during the war",
   "The 1925 return is the canonical case of monetary policy ignoring real adjustment. Even Mises and Hayek agreed Churchill should have devalued first, then resumed convertibility.")

# --- Bretton Woods (3) ---

q(P3, "bretton_woods_1944",
   "July 1944: 730 delegates from 44 Allied nations met at the Mount Washington Hotel in Bretton Woods, NH, while WWII raged. Keynes led the British delegation; Harry Dexter White led the American. What postwar monetary system did they design?",
   "Currencies pegged to the US dollar, dollar convertible to gold at $35/oz — a gold-exchange standard",
   "Fully floating exchange rates with no fixed reference between any currencies at all",
   "Return to the classical 1870-1914 gold standard with every country directly convertible",
   "A global currency called 'bancor' issued by an international bank — Keynes's preferred plan",
   "Bretton Woods created the IMF, the World Bank, and the dollar-gold anchor. Keynes wanted the bancor; the US insisted on the dollar's central role and won. The system lasted until 1971.")

q(P3, "bretton_woods_keynes_white",
   "At Bretton Woods (1944), Keynes wanted an international clearing union with a synthetic currency called the 'bancor' that no single nation controlled. Harry Dexter White wanted the dollar at the center. Why did White's plan win?",
   "The US held ~2/3 of the world's monetary gold and was funding the Allied war — it had leverage",
   "Keynes's bancor was mathematically impossible and was rejected by every other delegation",
   "White's plan was secretly identical to Keynes's — the debate was a public-relations exercise",
   "Keynes withdrew his proposal after Friedman and Hayek persuaded him the bancor would fail",
   "Bretton Woods is a study in postwar power. The US had the gold, the troops, the productive base. Keynes had the better-designed proposal in some ways but the worse hand at the table.")

q(P3, "bretton_woods_collapse_1971",
   "By the late 1960s, foreign central banks held more dollar claims than the US had gold to redeem. France's de Gaulle aggressively converted dollars to gold (1965+); Britain followed. Vietnam and Great Society strained the system. What did Nixon do August 15, 1971?",
   "Suspended dollar-gold convertibility for foreign governments — closing the gold window",
   "Doubled the gold price overnight from $35 to $70, restoring international confidence",
   "Sent Marines to seize French gold reserves to force de Gaulle to stop redemption",
   "Tied the dollar to a basket including yen and Deutschmark, abandoning gold entirely",
   "Bretton Woods ended August 15, 1971. Nixon called it 'temporary'; it has lasted 50+ years. The post-1971 era is when fiat went global.")

# --- Nixon Aug 15 1971 (4) ---

q(P3, "nixon_aug_15_1971",
   "Sunday evening August 15, 1971: Nixon preempted *Bonanza* on TV. He announced wage-price controls, a 10% import surcharge, and suspension of dollar-gold convertibility for foreign governments. What did the announcement permanently change?",
   "International money became pure fiat for the first time in 2,500 years — no major currency redeemable",
   "International money reverted briefly to barter — currencies stopped until the Smithsonian Agreement",
   "International money unified under a single global IMF currency — the SDR replaced national units",
   "International money began floating immediately, designed in consultation with the Austrian school",
   "August 15, 1971 is the most consequential date in modern monetary history. Saifedean Ammous's *Bitcoin Standard* (2018) treats this as the canonical break.")

q(P3, "nixon_connally",
   "Treasury Secretary John Connally, sent to a 1971 G10 meeting to manage international fallout from the gold-window closing, told European counterparts something memorably blunt. What did he say?",
   "'The dollar is our currency, but it's your problem' — capturing the post-Bretton-Woods asymmetry",
   "'We will return to gold within two years' — a promise to France and Germany during the meeting",
   "'The era of national currencies is over' — predicting a world unified under the dollar",
   "'Gold is a barbarous relic' — directly quoting Keynes's 1924 formulation against gold",
   "Connally's quip captured something true: foreign holders of dollars were holding an asset whose supply the US now controlled with no external constraint.")

q(P3, "nixon_wage_price_controls",
   "Nixon's August 15, 1971 announcement included wage-price controls. The idea: freeze prices to prevent inflation that closing the gold window would obviously cause. What happened over the next two years?",
   "Shortages of beef, fuel, lumber emerged as ceilings made production unprofitable — dropped 1973",
   "Inflation was held under 2 percent for the full decade through careful enforcement",
   "Wages and prices both fell over the next two years as controls produced deflation",
   "Controls were never enforced because no inflation appeared after closing the gold window",
   "Wage-price controls fail every time. Diocletian's Edict on Maximum Prices (301 AD) is the canonical ancient case. Nixon's 1971-73 attempt is the canonical modern case.")

q(P3, "post_1971_inflation",
   "Post-gold-window, US inflation moved from ~4% in 1971 to a peak of 14.8% in March 1980. Two oil crises, wage-price spirals, a 'misery index' politicians invented to measure the landscape. What's the deep cause?",
   "Dollar lost its commodity anchor — Fed expanded money supply faster than goods were produced",
   "OPEC's 1973 oil embargo was the sole cause, independent of US monetary policy in this period",
   "Union wage-push pressure caused the inflation independently of central-bank actions",
   "Population growth outran productivity — a demographic phenomenon unrelated to the gold window",
   "The 1970s inflation is the cleanest experiment for the proposition that fiat tends to inflate. The decade ended only when Volcker raised rates to 20% in 1980-81.")

# --- Weimar 1923 (4) ---

q(P3, "weimar_1923_peak",
   "November 1923 Weimar Germany: the exchange rate hit 4.2 TRILLION marks per US dollar. Bread cost ~200 billion marks. Workers were paid daily. Some Berliners burned mark notes for heat. What caused this?",
   "Reichsbank printed marks to fund reparations and deficits — supply outpaced goods, more printing",
   "The Treaty of Versailles required Germany to inflate its currency a fixed percentage quarterly",
   "France seized German printing presses in 1923 and ran them at maximum speed deliberately",
   "A fungus destroyed German wheat in 1923 and bread scarcity was the entire cause",
   "Weimar 1923 peaked at ~29,500% monthly inflation in October. Stabilized with the Rentenmark, backed by mortgages. The political fallout from the destroyed middle class is part of the precondition for what came next.")

q(P3, "weimar_savings",
   "Weimar hyperinflation (1921-23) destroyed the savings of the German middle class. Pensions, insurance, bank deposits became worthless within months. Workers paid off mortgages in worthless marks. Who was hit hardest?",
   "Savers, pensioners, middle class holding mark assets — debtors and asset-holders escaped",
   "Wage earners — wages adjusted upward faster than prices throughout the period entirely",
   "Foreign creditors — Germany paid all WWI reparations in worthless marks to foreign banks",
   "Industrialists — Krupp, Thyssen lost physical capital in 1923 and could not rebuild later",
   "Inflation is a wealth transfer from creditors to debtors and from savers to spenders. Weimar 1923 ran the experiment at maximum intensity.")

q(P3, "weimar_versailles",
   "Weimar's 1921-23 hyperinflation is sometimes blamed entirely on Versailles reparations. The actual story: reparations created a fiscal hole, but printing presses turned a fiscal hole into a monetary catastrophe. What did the government do?",
   "Used printed money to buy foreign currency to pay reparations — Reichsbank monetized the deficit",
   "Refused reparations and distributed the money to German citizens as direct stimulus instead",
   "Maintained gold convertibility through the period — gold was the mechanism transmitting inflation",
   "Allowed a private bank cartel to issue marks independent of the Reichsbank's careful policy",
   "Reparations alone could have been paid through taxation or recession. The choice to monetize — print money to pay it — is what produced hyperinflation. The deep cause is the choice to inflate.")

q(P3, "weimar_political",
   "Weimar hyperinflation peaked October-November 1923. On November 8-9, 1923 — while the inflation raged — Hitler attempted to overthrow the Bavarian government, was arrested, served nine months, and used the trial to launch a political career. What's the connection?",
   "Destroyed middle class, ruined pensioners, population radicalized by chaos — political tinder",
   "The hyperinflation had nothing to do with political instability — it was a pure monetary phenomenon",
   "Hitler personally caused the hyperinflation through his Bavarian political operations during 1923",
   "The government engineered the hyperinflation to provoke a crisis justifying constitutional suspension",
   "The link between monetary chaos and political extremism is one of the most-discussed lessons of Weimar. Destroyed savings were political tinder the 1929 Depression then re-ignited.")

# --- Hungarian pengo 1946 (3) ---

q(P3, "hungarian_pengo",
   "The Hungarian pengo holds the all-time hyperinflation record. By July 1946 prices were doubling every 15 hours. The government issued a 100-quintillion-pengo note (1 followed by 20 zeros). Daily inflation peaked at ~207%. What ended it?",
   "August 1946 introduction of the forint — backed by gold and managed under Allied supervision",
   "An emergency loan from the US and UK that backed the pengo with foreign currency reserves",
   "A political revolution that established a new government opposed to printing — inflation stopped",
   "A spontaneous Hungarian shift to barter exclusively for all transactions in 1946 nationwide",
   "Hungary 1945-46 is the most extreme hyperinflation on record. Stabilization required a new currency, not a reform. The forint (Aug 1 1946) remains Hungary's currency.")

q(P3, "hungarian_doubling",
   "By July 1946 in Hungary, prices were doubling every 15 hours. A worker paid in the morning had to spend the wage by lunch. Shops re-priced multiple times daily. What was monthly inflation?",
   "About 4.19 x 10^16 percent — roughly 41,900 trillion percent per month, the all-time record",
   "About 29,500 percent — slightly higher than Weimar Germany's 1923 peak in October",
   "About 1,000 percent — high but consistent with Argentina's worst hyperinflations",
   "About 89.7 sextillion percent — the figure later associated with Zimbabwe 2008",
   "Hungary 1946 eclipses every other on record. Doubling-every-15-hours produces astronomical compounded monthly rates. Postwar Hungary's fiscal hole was filled by printing.")

q(P3, "hungarian_denomination",
   "At the height of Hungarian hyperinflation in 1946, the central bank printed banknotes with denominations reading like astronomical numbers. The largest ever circulated was a 100-quintillion-pengo note. How many zeros is that?",
   "Twenty zeros after the 1 — the highest face value of any banknote in paper-currency history",
   "Fifteen zeros after the 1 — exceeded later by Zimbabwe and Venezuela hyperinflations",
   "Ten zeros after the 1 — similar in scale to Weimar Germany's largest 1923 notes",
   "Five zeros after the 1 — a normal large denomination in any major country today",
   "100 quintillion = 10^20. The note bought essentially nothing by the time it was printed. The pattern repeats across hyperinflations: as the unit collapses, denominations race upward.")

# --- Zimbabwe 100T 2009 (3) ---

q(P3, "zimbabwe_100_trillion",
   "January 16, 2009: Zimbabwe's central bank issued a 100-TRILLION-dollar note. By printing-press time it bought ~one loaf of bread. By April 2009 the Zimbabwe dollar was abandoned; people used US dollars and rand. Who was president?",
   "Robert Mugabe — president 1980-2017, whose land reform and printing drove the hyperinflation",
   "Joshua Nkomo — former rebel leader who became president of Zimbabwe in 2008",
   "Morgan Tsvangirai — opposition leader who briefly held the presidency in 2009",
   "Ian Smith — the white-minority Rhodesian leader, who returned to power in 2008",
   "Mugabe ruled 1980-2017. Land reform after 2000 destroyed agriculture; the fiscal hole was monetized; hyperinflation followed. Peak: ~89.7 sextillion percent November 2008.")

q(P3, "zimbabwe_peak",
   "Zimbabwe's hyperinflation peaked in November 2008. Official statistics stopped publishing in July 2008 because rates changed too fast to measure. Economist Steve Hanke later calculated using rand exchange rates. What did he find?",
   "~89.7 sextillion percent month-on-month — the second-worst hyperinflation after Hungary 1946",
   "~29,500 percent month-on-month — matching the Weimar Germany peak of October 1923 exactly",
   "~4.19 quadrillion percent month-on-month — exceeding Hungary's 1946 record by a wide margin",
   "~1,000 percent month-on-month — high but within range of historical hyperinflations of the era",
   "Hanke's measurement puts Zimbabwe November 2008 just below Hungary 1946 (the all-time record). Zimbabweans abandoned the local currency for foreign substitutes.")

q(P3, "zimbabwe_dollarization",
   "By April 2009 Zimbabweans had simply stopped using the Zimbabwe dollar. Without any formal government decision, ordinary people began transacting in US dollars, rand, and pula. Shops re-priced in dollars; salaries paid in dollars. What's the recognition?",
   "A currency without trust cannot be enforced by law — when fiat loses value, people switch",
   "Currency substitution requires government coordination — Zimbabwe formally adopted the dollar",
   "Hyperinflations always end with gold-backed scrip — Zimbabwe issued gold-backed bonds in 2009",
   "Hyperinflations cannot end without external military intervention from a foreign power",
   "Spontaneous dollarization is a recurring pattern. Argentines did it. Venezuelans did it. Lebanese have done it since 2020. People prefer working money to a unit of account that loses value daily.")

# --- Argentina (3) ---

q(P3, "argentina_recurrent",
   "Argentina has had major monetary collapses in 1975, 1989-90, 2001-02, and 2018+. The 1989 episode saw prices rise ~5,000% in a year; 2018+ brought inflation over 100% annually by 2022. The peso has been replaced multiple times. What pattern emerges?",
   "Recurring fiscal deficits + monetization + currency controls produces recurring crises — same mistakes",
   "Argentina is uniquely cursed by geography — climate and resources make stable money impossible",
   "Argentina has had a single hyperinflation continuously ongoing since 1900 with no interruption",
   "Argentina's problems are entirely caused by external speculators and US interest-rate policy",
   "Argentina is the canonical 'recurring soft hyperinflation' case. Deficits + monetization + depreciation + controls fail + dollar substitution + new currency or program — and the cycle repeats.")

q(P3, "argentina_milei",
   "December 2023: Javier Milei was inaugurated president of Argentina. A self-described libertarian and Austrian-school economist, he wielded a chainsaw at rallies as a symbol of cutting government. Annual inflation was 211% in December 2023. What did he do first?",
   "Cut the fiscal deficit through massive spending reductions and removed dozens of price controls",
   "Pegged the peso to the US dollar at the prewar rate and announced full dollarization within 90 days",
   "Borrowed an emergency $50 billion package from the IMF to fund continued deficit spending",
   "Banned all foreign exchange transactions and required Argentines to use only the peso domestically",
   "Milei's program is the closest thing to an Austrian-school austerity test in modern history. By late 2024 monthly inflation had dropped below 3%. The medium-term outcome is still unfolding.")

q(P3, "argentina_blue_dollar",
   "Argentines have for decades worked around exchange controls using a parallel market called 'the blue dollar' — buying USD in cash through unofficial dealers at rates often 50-100% above the official rate. Why does it exist?",
   "The government imposes capital and currency controls — Argentines convert to USD outside official channels",
   "The blue dollar is a state-licensed parallel market run by the central bank for hard-currency industries",
   "The blue dollar is a digital cryptocurrency unique to Argentina, created by the government in 2010",
   "The blue dollar reflects only the price of imported goods — unrelated to broader exchange dynamics",
   "When a government bans buying dollars at the official rate, a parallel market forms. The premium measures how much trust the official rate has lost.")

# --- Venezuela (2) ---

q(P3, "venezuela_2017",
   "By 2018 Venezuela's annual inflation was estimated at 1.7 million percent. Stores re-priced multiple times daily. Workers were paid in eggs because the bolivar was worthless. Chavez (1999-2013) and Maduro produced the collapse. What was the mechanism?",
   "Massive deficit spending funded by printing + collapsing oil production from nationalized PDVSA",
   "Foreign sanctions alone caused the entire hyperinflation — without them, growth would have been rapid",
   "A US covert operation deliberately printed counterfeit bolivars at industrial scale from 2014 onward",
   "A series of agricultural failures unrelated to monetary policy caused all the price spikes documented",
   "Venezuela's hyperinflation peaked at ~65,000% in 2018 and continued for years. The country has the world's largest proven oil reserves but production collapsed. ~7 million Venezuelans have left since 2014.")

q(P3, "venezuela_oil_curse",
   "Venezuela in 1998 had higher GDP per capita than most Latin American neighbors and was a major oil exporter. By 2018 it was experiencing the worst peacetime collapse since the 1930s. PDVSA production fell from 3.5M b/d to under 800K. What happened?",
   "Chavez nationalized industries and fired PDVSA experts, then Maduro funded deficits by printing",
   "Natural disasters and earthquakes destroyed Venezuelan oil infrastructure across regions for 15 years",
   "US sanctions imposed in 1999 immediately prevented Venezuela from selling oil for two decades",
   "OPEC quotas forced Venezuela to reduce production every year — a regulatory rather than domestic choice",
   "The Venezuelan case combines bad monetary policy with bad industrial policy. Technical knowledge needed to operate a national oil industry was destroyed when experienced engineers were fired.")

# --- Lebanon 2020+ (2) ---

q(P3, "lebanon_2020",
   "Lebanon's pound was pegged to the US dollar at 1,507:1 from 1997. In late 2019 the central-bank Ponzi structure of Lebanese banking became unsustainable. By 2023 the parallel rate was over 100,000 pounds/dollar. Depositors could not withdraw dollars. What happened?",
   "Banks took dollar deposits and loaned them to the central bank, which spent them — gone when redeemed",
   "Lebanon successfully transitioned to a new currency in 2020 through central-bank-and-IMF coordination",
   "An earthquake destroyed Beirut's banking infrastructure and forced abandonment of the dollar peg",
   "The peg held throughout — the inflation in Western media is an Israeli intelligence operation",
   "Lebanon's collapse is one of the worst peacetime economic crises per the World Bank. The 2020 Beirut port explosion accelerated. Depositors lost the bulk of their savings.")

q(P3, "lebanon_haircut",
   "When Lebanon's banking system froze late 2019, depositors discovered they could not withdraw their own dollars. Banks imposed informal capital controls — 'haircuts' — meaning withdrawing $1,000 might give you $100 or less. What's the recognition?",
   "Bank deposits are loans to the bank — when bank loans go bad, your deposit is unsafe",
   "Lebanese banks were uniquely corrupt — the haircut episode has no parallel in modern banking",
   "Capital controls are always temporary — Lebanese depositors all received their full balances by 2021",
   "The Lebanese crisis was external speculation, unrelated to Lebanon's banking system structure itself",
   "The Lebanese collapse is one reason 'not your keys, not your coins' is a Bitcoin slogan. A claim on a bank is a claim on the bank's ability to honor it.")

# --- Yugoslav 1993 (1) ---

q(P3, "yugoslav_dinar",
   "Yugoslavia's 1993-94 dinar hyperinflation reached an estimated 313 million percent in January 1994 — about 65% PER DAY. Slobodan Milosevic's government funded the wars of Yugoslav succession by printing the dinar at industrial scale. What ended it?",
   "Introduction of the new dinar in January 1994 pegged to the Deutschmark — a fresh unit of account",
   "NATO military intervention that physically seized Yugoslav printing presses in late 1993 to halt it",
   "Yugoslavia returned to the gold standard at the prewar parity in 1994 — gradual stabilization",
   "The dinar continued at this rate through the 1990s with no successful stabilization attempted",
   "Yugoslavia 1993-94 was one of the worst hyperinflations on record and one of the most political — Milosevic's wars required money the productive economy could not provide.")

# --- Continental + Roman denarius (2) ---

q(P3, "continental_currency",
   "During the American Revolution the Continental Congress had no power to tax. It funded the war by issuing paper currency called the Continental. By 1781 the Continental had lost essentially all value — giving 'not worth a Continental.' How much was printed?",
   "Over $240 million between 1775-1779 — by war's end they traded at ~1/1000th of face value",
   "Exactly $10 million in Continentals backed by gold reserves shipped from France during the war",
   "Only small amounts — the inflation was caused entirely by British counterfeiting operations",
   "Continentals backed by tobacco and rice — agricultural backing held them at full face value",
   "The Continental's collapse is why the Constitution restricted state currency issuance. 'Not worth a Continental' entered American English. The lesson did not last — Civil War greenbacks followed.")

q(P3, "roman_denarius",
   "The Roman denarius — standard silver coin — was ~95% silver under Augustus (30 BC). By Aurelian (270 AD) the same nominally-named coin was ~5% silver. Diocletian's Edict on Maximum Prices (301 AD) tried to fight the inflation. What happened?",
   "Emperors funded military spending by reducing silver content — same name, less metal, inflated",
   "Rome ran out of silver entirely by 100 AD — the denarius was copper-tin alloy through the period",
   "Silver content was constant — the inflation Diocletian noted was caused by foreign exchange",
   "Emperors deliberately increased silver content over time to make the denarius more valuable",
   "Roman coin debasement is the canonical ancient case of monetary inflation. Same number of denarii but less silver meant more money chasing same goods. Diocletian's price controls failed.")

# --- Bitcoin as digital sound money (3) ---

q(P3, "ammous_bitcoin_standard",
   "Saifedean Ammous, a Lebanese-American economist, published *The Bitcoin Standard* in 2018. The book sold over 1 million copies, was translated into 38 languages, and became the most influential popular case for Bitcoin as monetary technology. What's the argument?",
   "Bitcoin's math scarcity (21M cap) + credibly-neutral issuance make it the soundest money ever",
   "Bitcoin is interesting but inferior to a return to the classical gold standard via treaty",
   "Bitcoin is transitional — to be replaced within the decade by central-bank digital currencies",
   "Bitcoin is a speculative asset with no monetary role — governments should adopt crypto tax regimes",
   "Ammous brought the sound-money / Austrian-school argument into the Bitcoin conversation in book form. The book's stance: scarcity is a feature, not a bug.")

q(P3, "alden_broken_money",
   "Lyn Alden — macro analyst and engineer by training — published *Broken Money* in 2023. The book examines money from cowrie shells through Bitcoin through one frame: money is the asset with the lowest 'stock-to-flow' inflation. What does Bitcoin represent?",
   "First money in history with mathematically-fixed maximum supply — highest stock-to-flow ever",
   "A passing curiosity to be replaced by central-bank digital currencies within two decades",
   "A return to the medieval system of localized commodity money with no broader significance",
   "A theoretical construct never actually implemented — best understood as a thought experiment",
   "Alden's *Broken Money* (2023) became one of the most-cited modern works on money. Her engineer's framing — money as the asset with the lowest issuance rate — sharpens the case for Bitcoin.")

q(P3, "stock_to_flow",
   "Sound-money analysts use 'stock-to-flow' — total existing supply / annual new supply. Gold ~60. Silver ~22. Wheat under 1. Bitcoin ~120 after the 2024 halving. What does a high stock-to-flow indicate?",
   "Difficulty inflating the supply — high stock-to-flow resists debasement, historically the preferred metals",
   "Easy inflation of supply — high stock-to-flow means producers can easily double the existing stock",
   "Population growth rates — stock-to-flow is a demographic metric for agricultural societies",
   "Interest rate volatility — stock-to-flow correlates with central-bank policy-rate variability",
   "Stock-to-flow is one of Ammous's central concepts in *The Bitcoin Standard*. Gold's high stock-to-flow is why it served as money for thousands of years. Bitcoin's growing stock-to-flow as halvings progress is the math behind the orange coin's monetary thesis.")

# --- Sound money + dollar purchasing power (3) ---

q(P3, "dollar_1913",
   "The Federal Reserve was created in 1913. According to the BLS, a dollar in 1913 has the purchasing power of about $0.03 in 2024 — about 97% of the dollar's value has been lost since the Fed's founding. What does this represent?",
   "A household saving in dollars for 100 years would have lost almost all real wealth",
   "A household saving in dollars for 100 years would have multiplied real wealth by 33x",
   "The 97% loss is a statistical illusion produced by mismeasurement — dollars actually gained value",
   "The 97% loss is concentrated in post-2020 — the dollar held its value through the 20th century",
   "The dollar's century-long depreciation is the deepest illustration of why the Fed's track record matters. The institution founded to provide stable money presided over the largest peacetime depreciation.")

q(P3, "gold_vs_fiat_savings",
   "A worker in 1924 who saved 1 oz of gold vs a worker who saved $20 (equivalent at the prewar gold price). A century later in 2024: the gold oz is worth ~$2,400; the $20 has the purchasing power of ~$0.70. What does this illustrate?",
   "Sound money (gold) preserves purchasing power; fiat dilution destroys real savings in the unit",
   "Workers in 1924 should have invested in stocks — neither cash nor gold are valid savings vehicles",
   "Gold prices today are inflated by speculation — gold also lost real value over the century",
   "The comparison is misleading because dollars earn interest in bank accounts and gold does not",
   "The gold-vs-dollar comparison is one of the cleanest demonstrations of what sound money means. Simple long-term storage in a non-debasable asset preserves wealth.")

q(P3, "monetary_dilution",
   "When the Fed's balance sheet expands from $800B (2008) to $9T (2022), the new dollars don't appear from nowhere — they're created and used. What does this mean for someone holding existing dollars?",
   "Their savings are diluted — more dollars chasing same goods means each dollar buys less",
   "Their savings appreciate — Fed expansion lifts all dollar holders' wealth proportionally and equally",
   "Their savings are unaffected — Fed balance-sheet expansion has no impact on purchasing power",
   "Their savings are doubled — Fed expansion means each existing dollar represents a larger share",
   "Monetary expansion dilutes existing claims on the same pool of goods. The Cantillon effect determines who benefits; everyone else loses purchasing power in proportion to how late they receive new money.")


# =========================================================================
# PILLAR 4 — CENTRAL BANKING + KEYNES/MMT CRITIQUE (45)
# =========================================================================

# --- Jekyll Island (4) ---

q(P4, "jekyll_island_six_men",
   "November 1910: Senator Nelson Aldrich, JP Morgan banker Henry Davison, Paul Warburg, Frank Vanderlip of National City Bank, A. Piatt Andrew of Treasury, and Benjamin Strong boarded a private rail car at Hoboken, NJ. They headed to Jekyll Island, using only first names. Why the secrecy?",
   "Public opinion was hostile to banker influence — a known meeting would have triggered populist opposition",
   "The participants were under federal indictment for antitrust violations and feared arrest if tracked",
   "Jekyll Island was a Spanish enclave outside US jurisdiction — needed to avoid State Department customs",
   "The participants were planning stock manipulation — first names to avoid SEC investigator evidence",
   "Jekyll Island 1910 is the founding moment of US central banking. Participants represented ~25% of the world's wealth. Their draft — the Aldrich Plan — became (lightly modified) the Federal Reserve Act of 1913.")

q(P4, "aldrich_plan",
   "The Jekyll Island meeting (November 1910) drafted a proposal that became known as the Aldrich Plan. It went to Congress in 1912 and was rejected — Senator Aldrich was too closely identified with Wall Street. The plan was revised and reintroduced. What did it become?",
   "The Federal Reserve Act of 1913 — passed December 22, signed by Wilson December 23, 1913",
   "The Glass-Steagall Banking Act of 1933 — separating commercial from investment banking after the crash",
   "The Bretton Woods Agreement of 1944 — establishing the postwar international monetary system",
   "The Sherman Antitrust Act of 1890 — breaking up monopolies and trusts during the Progressive era",
   "The Aldrich Plan and Federal Reserve Act share ~90% of their structure. The political relabeling — calling it a public Federal Reserve System rather than a private central bank — was the trick that got it passed.")

q(P4, "griffin_jekyll",
   "G. Edward Griffin's 1994 book *The Creature from Jekyll Island: A Second Look at the Federal Reserve* became the canonical popular account of the Fed's origins. It documents the 1910 meeting in detail. What's the core argument?",
   "The Fed combines private cartel benefit with public-agency legitimacy — designed that way at Jekyll Island",
   "The Fed is a benign public agency mistakenly criticized by populists who don't understand it",
   "The Fed was created by Karl Marx as a Communist Party operation controlled by Soviet intelligence",
   "The Fed has no relationship to the Jekyll Island events — the link is a fabrication invented by Griffin",
   "Griffin's book is the most-read popular history of the Federal Reserve. Even academic critics treat it seriously. Murray Rothbard's *The Case Against the Fed* (1994) is the academic version of the same critique.")

q(P4, "fed_act_dec_23_1913",
   "President Woodrow Wilson signed the Federal Reserve Act into law on December 23, 1913 — two days before Christmas. The bill had passed the Senate three days earlier with much of the chamber departed for holiday recess. What was the result?",
   "Twelve regional Fed Banks under a Washington Board of Governors — hybrid public-private cartel design",
   "A single nationalized central bank fully owned by the Treasury and reporting to the President",
   "A purely private bank with no government oversight — reporting only to its private shareholders",
   "A consortium of state-chartered banks with no federal authority — state-level oversight only",
   "The Federal Reserve combines 12 regional banks (owned by member banks) with a Washington Board (appointed by President). Neither fully public nor fully private — and that ambiguity has insulated it.")

# --- Friedman + Schwartz 1963 (4) ---

q(P4, "friedman_schwartz",
   "Milton Friedman and Anna Schwartz published *A Monetary History of the United States 1867-1960* in 1963. The book is one of the most influential economics works of the 20th century. Its argument about the Great Depression changed how it is taught. What did they argue?",
   "The Fed CAUSED the Great Depression by letting the money supply contract ~33% between 1929 and 1933",
   "The Fed heroically prevented an even worse depression through expansionary policy that was too small",
   "The Great Depression was caused by gold standard alone — would have been mild had Fed abandoned it",
   "The Great Depression was caused by tariff policy — Fed actions during 1929-33 were irrelevant",
   "Friedman + Schwartz changed how the Great Depression is taught. Mainstream economics now accepts the Fed allowed the contraction. Austrians go further: the Fed's expansionary 1920s policy CAUSED the 1929 bubble.")

q(P4, "fed_great_contraction",
   "Between 1929-1933, the US money supply (M2) fell from ~$46B to ~$30B — a contraction of ~33%. Bank failures wiped out depositor savings; the Fed did not act as lender of last resort. Friedman and Schwartz (1963) called this the Great Contraction. What's the institutional irony?",
   "The Fed was created in 1913 to prevent banking panics — its first major test produced the worst collapse",
   "The Fed was created in 1913 specifically to cause banking panics — 1929-33 was the founding purpose",
   "The Fed was created in 1913 with no specific purpose — it just happened to exist when 1929-33 occurred",
   "The Fed was created in 1933 in response to the panic — no role in the contraction that preceded",
   "The Fed's track record from founding through the Great Depression is central evidence the institution does not deliver what its founders promised. Even mainstream defenders accept this finding.")

q(P4, "friedman_monetarism",
   "Milton Friedman led what became known as the Chicago school or monetarism — the view that monetary policy mattered enormously and the Fed's discretion was the problem. Friedman favored a steady 3-5% money growth rule. What was his slogan?",
   "'Inflation is always and everywhere a monetary phenomenon' — money supply drives the price level",
   "'Markets are always wrong about inflation' — central-bank expertise is essential to modern policy",
   "'Inflation is caused by aggregate demand' — fiscal policy is the only meaningful tool available",
   "'Inflation is a tax voluntarily chosen by the public' — voter preferences determine the price level",
   "Friedman's framing crystallized the monetarist position. He differed from Austrians on details but agreed monetary policy was central. His 1976 Nobel honored work that included a deep critique of Keynesian.")

q(P4, "anna_schwartz",
   "Anna Schwartz was Milton Friedman's collaborator on *A Monetary History* (1963). She worked at the NBER from 1941 until her death in 2012 — 71 years at the same institution. What's the recognition?",
   "Schwartz did the heavy archival work — dug out monetary data and built the historical record",
   "Schwartz was a sociologist with no economic training whom Friedman invited as a publicity stunt",
   "Schwartz received the Nobel jointly with Friedman in 1976 for the Great Depression and Contraction",
   "Schwartz was the public face of monetarism in the media throughout the 1970s while Friedman hid",
   "Anna Schwartz is one of the unsung figures of 20th-century economics. The data Friedman analyzed was largely her work to assemble. She continued working into her 90s, publishing through 2010.")

# --- Volcker 1979-87 (4) ---

q(P4, "volcker_1979",
   "By 1979 US inflation was running over 11% annually. Jimmy Carter appointed Paul Volcker as Fed Chairman. Volcker — 6'7' tall, cigar-chewing, famously stubborn — had been President of the NY Fed. What broke the 1970s inflation?",
   "Raised the fed funds rate to ~20% by mid-1981 — engineering a deep recession to crush inflation",
   "Lowered interest rates to zero and printed money aggressively — a fully expansionary policy",
   "Implemented wage and price controls backed by Federal Reserve regulatory authority over wages",
   "Devalued the dollar against gold by 50 percent overnight — restoring partial gold convertibility",
   "Volcker's 1979-87 tenure is the canonical case of a Fed Chairman doing the politically painful work of stopping inflation. The 1981-82 recession was severe — unemployment hit 10.8%. But the inflation broke.")

q(P4, "volcker_recession",
   "Volcker's high-rate policy in 1981-82 produced a severe recession. Fed funds peaked at ~20% in June 1981. Prime hit 21.5%. Unemployment rose to 10.8% by November 1982 — the highest since the Great Depression. What did Volcker do politically?",
   "Took the heat — farmers drove tractors into Washington, builders sent 'STOP THE FED' two-by-fours",
   "Apologized to Congress repeatedly and lowered rates immediately when faced with political opposition",
   "Blamed the recession entirely on Carter administration fiscal policies and absolved the Federal Reserve",
   "Resigned the chairmanship in protest after Congress moved to override Fed policy through new legislation",
   "Volcker's willingness to absorb political pain to break inflation is part of why he's remembered as one of the great Fed chairmen. The political conditions that produced his tenure have not quite recurred.")

q(P4, "volcker_reagan",
   "Volcker was appointed by Jimmy Carter (1979) and reappointed by Ronald Reagan (1983). Reagan campaigned on sound money; Volcker had been the unpopular face of rate hikes. Why did Reagan reappoint him?",
   "Volcker's policy was working — inflation had fallen from over 13% to under 4% by 1983",
   "Reagan was forced by Congress through legislation mandating Fed Chair continuity in office",
   "Reagan reappointed Volcker as humiliation — Volcker had become a Democratic political liability",
   "Reagan personally negotiated for months before Volcker agreed to cut interest rates to zero in 1984",
   "Volcker served until 1987, when Reagan replaced him with Alan Greenspan. The Volcker-to-Greenspan handoff is when the Fed's culture began drifting toward 'we can fine-tune everything' confidence.")

q(P4, "volcker_austrian_reading",
   "The Volcker disinflation (1979-83) is the only successful peacetime stopping of a major inflation in modern US history. The Fed created the inflation through accommodation in the 1970s and broke it through high rates. What's the Austrian reading?",
   "Central banks CAN break inflation when they choose — the question is whether they WILL given incentives",
   "Central banks are the only institutions capable of managing inflation — gold could never have done it",
   "Central banks always break inflation immediately when needed — Volcker was the normal pattern",
   "Central banks cannot break inflation — the 1970s ended due to demographic shifts unrelated to policy",
   "The Austrian reading: Volcker showed central banks CAN do the right thing but rarely WILL, because political pain falls on them while benefits diffuse. Post-Volcker, the Fed reverted to easier money.")

# --- 2008 bailouts (4) ---

q(P4, "tarp_2008",
   "October 3, 2008: President George W. Bush signed the Emergency Economic Stabilization Act, authorizing the Treasury to purchase up to $700 billion in 'troubled assets' from financial institutions. The program became TARP. What did Austrians flag?",
   "Socialized losses from bad housing bets — taxpayers underwrote downside of voluntary risk-taking",
   "Privatized gains for financial institutions through asset purchases later sold back at a loss",
   "Required all participating institutions to liquidate at fair market value — forced losses on banks",
   "Created a 5-year freeze on all bank executive compensation across the US financial sector",
   "TARP is the canonical 'too big to fail' moment. The moral hazard — banks taking risk knowing they'd be bailed out — is the precise dynamic Austrians had warned about.")

q(P4, "lehman_sept_2008",
   "September 15, 2008: Lehman Brothers — the fourth-largest US investment bank, founded in 1850 — filed for bankruptcy. Treasury Secretary Henry Paulson refused to bail it out. The global financial system seized up; AIG was bailed out two days later. What was revealed?",
   "Bear Stearns (March) rescued; Lehman (Sept) not; AIG (Sept) yes — case-by-case political discretion",
   "All financial institutions in 2008 were treated identically — no political discretion was exercised",
   "Lehman was rescued through a secret backdoor channel — the bankruptcy was a PR exercise only",
   "The 2008 bailouts followed a written rulebook published in 2007 — Paulson had no discretion",
   "The 2008 bailouts exposed the case-by-case nature of regulatory decisions. Why Bear Stearns but not Lehman? The questions have no rules-based answers. The decisions were discretionary.")

q(P4, "revolving_door_treasury",
   "Henry Paulson — Treasury Secretary during 2008 — had been CEO of Goldman Sachs (1999-2006). Successor Tim Geithner had been President of the NY Fed, the regulator of Wall Street banks. Both then moved back to senior finance roles. What's this pattern called?",
   "The revolving door — officials move between regulator and regulated, blurring public/private lines",
   "Public service rotation — a healthy system in which financial professionals occasionally serve in government",
   "Regulatory specialization — modern requirement that regulators have decades of industry experience",
   "Bipartisan continuity — design of the Fed system that requires alternating Republican/Democratic Chairs",
   "The revolving door is a public-choice phenomenon: regulators expect future industry jobs, so they regulate gently. Industries hire ex-regulators for relationships and inside knowledge.")

q(P4, "qe_eras",
   "After the 2008 crisis, the Fed launched 'quantitative easing' — programs (QE1 Nov 2008, QE2 Nov 2010, QE3 Sept 2012) that purchased Treasury bonds and mortgage-backed securities. The Fed's balance sheet rose from ~$900B in 2008 to over $4T by 2014. What did QE do?",
   "Raised asset prices — Cantillon-effect benefit went first to asset holders, CPI stayed quiet until 2021",
   "Stimulated the broad real economy uniformly — every sector saw matching gains with no distributional split",
   "Failed entirely to affect any asset prices — QE's effect on markets was statistically zero throughout",
   "Caused immediate consumer-price inflation of 10% annually from 2009 — inflation began at QE1's announcement",
   "QE's first-order effect was to raise asset prices, benefiting asset holders. CPI inflation arrived later, when supply shocks + monetary expansion combined in 2021-23. The Cantillon split was sharp.")

# --- 2020 emergency Fed (4) ---

q(P4, "fed_2020",
   "March 2020 brought the largest peacetime monetary expansion in US history. The Fed's balance sheet went from ~$4.2T in early March to ~$7T by June. The government enacted CARES ($2.2T) and subsequent packages totaling ~$4-5T in pandemic spending. What did Austrians predict?",
   "Significant CPI inflation would arrive once supply shocks eased and new money chased available goods",
   "No inflation would arrive — monetary expansion under fiat has no relationship to consumer prices",
   "Hyperinflation immediately in 2020 with prices doubling within months of the stimulus checks",
   "Deflation would arrive — the pandemic represented a productivity boom that would lower prices",
   "Larry Summers (a Democrat, not an Austrian) warned February 2021 that spring 2021 stimulus would cause inflation. He was right. The Fed dismissed the warning as 'transitory.' The 2021-23 inflation was the empirical falsification.")

q(P4, "cares_2_2t",
   "The CARES Act, signed March 27, 2020, was a $2.2 trillion package — at the time the largest single stimulus in US history. It included $1,200 direct payments, expanded unemployment, and $500 billion in business loans. What was the immediate monetary effect?",
   "M2 money supply grew ~26% in 2020 — the fastest annual money-supply growth since World War II",
   "M2 money supply was unchanged — spending was funded entirely by existing Treasury balances",
   "M2 money supply contracted — lockdowns reduced economic activity enough to overcome stimulus effects",
   "M2 money supply grew about 2% — a perfectly normal annual increase within historical bands",
   "M2 grew 26% in 2020 — largest annual money-supply expansion in postwar US history. Austrians had predicted such expansions would produce CPI inflation. The 2021-23 inflation was the predicted outcome.")

q(P4, "fed_balance_4_to_9t",
   "Before 2008, the Fed's balance sheet held ~$800B in assets — almost entirely Treasury securities. By 2008-14, QE took it to $4.5T. The 2020 pandemic took it to ~$9T by 2022. What's the broader recognition?",
   "Fed has bought ~$8T in financial assets in 14 years — creating new dollars from nothing to lift prices",
   "Fed has reduced its balance sheet from $800B to roughly zero — current holdings are essentially nil",
   "Fed's balance sheet is irrelevant to monetary outcomes — asset purchases have no economic effect",
   "Fed's balance sheet is funded entirely by taxpayer revenues — every dollar offset by tax collection",
   "The post-2008 Fed has been a serial asset-purchaser at scales the original 1913 Act did not contemplate. 'Temporary emergency' programs have become permanent. Cantillon-effect distributional consequences accumulate.")

q(P4, "powell_transitory",
   "Throughout 2021, Fed Chair Jay Powell repeatedly used the word 'transitory' to describe rising inflation. By November 2021, with CPI inflation at 6.8%, he formally retired the term. Inflation peaked at 9.1% in June 2022. What did the framing reveal?",
   "Fed had no early-warning system distinct from supply-chain narratives — caught flat-footed by inflation",
   "Fed had perfectly accurate forecasts and 'transitory' was a deliberate misdirection for strategic reasons",
   "Fed deliberately under-predicted to maintain low rates that benefited Treasury debt-service costs",
   "Fed has no role in managing inflation — its decisions are statistically uncorrelated with prices",
   "Powell's 'transitory' framing aged poorly. The Fed had to raise rates aggressively in 2022-23. The episode illustrates institutional miscalibration: the Fed gets things wrong, then has to correct.")

# --- Post-2020 inflation 9.1% June 2022 (3) ---

q(P4, "june_2022_9_1",
   "US CPI inflation peaked at 9.1% year-over-year in June 2022 — highest since November 1981. Gasoline averaged over $5/gallon. Food up double digits. What did Larry Summers say in February 2021 that became famous?",
   "Warned the $1.9T American Rescue Plan was the 'least responsible' macro policy in 40 years",
   "Endorsed the American Rescue Plan as exactly right and dismissed inflation concerns throughout 2021-22",
   "Resigned his Harvard professorship in 2021 to protest the American Rescue Plan in writing",
   "Suggested the American Rescue Plan was too small by 50% and proposed an additional $4 trillion in 2021",
   "Summers's February 2021 warning is one of the most-cited cases of a mainstream Keynesian getting it right when the consensus got it wrong. The Fed and Treasury dismissed his concerns. Even Krugman has since admitted the mistake.")

q(P4, "real_wages_2022",
   "From 2021 to 2023, US real wages — wages adjusted for inflation — fell. Nominal wages rose, but consumer prices rose faster. By the time inflation peaked at 9.1% in June 2022, the median worker had lost real purchasing power. What does this illustrate?",
   "Inflation is a wealth transfer from wage-earners (whose income lags) to debtors and asset-holders",
   "Inflation is a wealth transfer toward wage-earners — their nominal wages always rise faster than prices",
   "Inflation has no distributional effects — every household experiences the same purchasing-power outcome",
   "Inflation transfers wealth only from creditors to debtors — wage-earners and assets are unaffected",
   "Real wages falling during inflation is the canonical demonstration of why wage-earners are particular victims of monetary expansion. The 'inflation as wage transfer' framing comes alive in episodes like 2021-23.")

q(P4, "supply_chain_vs_monetary",
   "Some economists in 2021-22 argued the inflation was caused entirely by supply-chain disruptions and would resolve itself. Others (Austrians, Summers, monetarists) argued it was monetary. By 2023, supply chains had largely normalized but inflation persisted. What did the data show?",
   "Supply-chain effects were real but secondary — the monetary component required aggressive Fed rate hikes",
   "Supply-chain disruptions were the entire cause — inflation fell automatically to zero by mid-2022",
   "Supply chains had nothing to do with it — the 2021-23 episode was a pure monetary phenomenon",
   "Supply chains caused 100% of inflation and monetary policy was perfectly accommodative throughout",
   "The 2021-23 episode demonstrated both supply shocks AND monetary expansion contributed. The mainstream profession's failure to acknowledge the monetary side — until the rate hikes began — is part of the miscalibration story.")

# --- MMT (Kelton 2020) + falsified (4) ---

q(P4, "kelton_deficit_myth",
   "Stephanie Kelton's *The Deficit Myth* was published June 2020 and became the most-influential popular statement of MMT. The core claim: a government issuing its own currency cannot 'run out' of money. Deficits constrained only by inflation. What happened next?",
   "2021-23 inflation arrived — larger, faster, more persistent than MMT implied — falsifying its policy",
   "MMT was vindicated by the absence of inflation following pandemic-era stimulus funded by MMT principles",
   "MMT became standard Federal Reserve doctrine after 2020 — basis of all US monetary policy decisions",
   "MMT was repealed by Congress in 2022 through legislation banning MMT principles in federal budgeting",
   "Kelton's *Deficit Myth* arrived just as the largest peacetime monetary-fiscal experiment was beginning. The book was the popular case; the 2021-23 inflation was the empirical reply.")

q(P4, "mmt_inflation_constraint",
   "MMT acknowledges in its formal pages that government spending under a fiat currency is constrained by inflation. But its popular deployment by Kelton and Sanders staffers tended to minimize the constraint. What did 2021-23 reveal?",
   "When the constraint arrived, it was larger and harder to control than MMT had implied — costs not zero",
   "MMT's inflation constraint was perfectly calibrated — 2021-23 matched MMT's predictions exactly",
   "MMT had no inflation constraint at all — was unaffected by 2021-23 events in any theoretical way",
   "The 2021-23 inflation was unrelated to fiscal policy and had no implications for MMT framework",
   "MMT's formal pages and political deployment diverged sharply. The political version sold deficit spending as nearly costless; the inflation showed costs were not zero. The empirical disconfirmation weakened its momentum.")

q(P4, "summers_feb_2021",
   "Larry Summers — Harvard economist, former Treasury Secretary, lifelong Keynesian — published a February 2021 Washington Post op-ed warning the $1.9T American Rescue Plan would 'set off inflationary pressures of a kind we have not seen in a generation.' He was largely ignored. What happened?",
   "Inflation rose from ~1.4% in January 2021 to 9.1% by June 2022 — Summers substantially correct",
   "Inflation remained at the 2 percent target throughout — Summers's warnings proved incorrect entirely",
   "Summers's warnings caused a market panic in February 2021 that ended inflation before it began",
   "Inflation rose temporarily to about 3% — Summers's warnings were correctly dismissed as overblown",
   "Summers's 2021 warning is the canonical case of a mainstream economist getting it right. Krugman has acknowledged Summers was correct. The episode chipped at credibility of the 'inflation is no longer a risk' framework.")

q(P4, "mmt_origin",
   "Modern Monetary Theory traces intellectual roots back to chartalism (Knapp 1905) and Abba Lerner's 'functional finance' (1943). Modern advocates (Mosler, Wray, Kelton, Mitchell) developed it from the 1990s. What's the central methodological move?",
   "Treating consolidated government-plus-central-bank as a single entity — collapsing fiscal/monetary line",
   "Treating the Federal Reserve as fully independent — deficits have no relationship to monetary policy",
   "Treating taxation as the only source of government revenue — printing is constitutionally forbidden",
   "Treating gold reserves as the basis of all government spending — fiat currency has no role in MMT",
   "MMT's consolidation of fiscal and monetary policy is its most distinctive analytical move. Critics say it elides distinctions; defenders say it captures political-economic reality. The 2021-23 inflation became the empirical referee.")

# --- Keynes General Theory 1936 (4) ---

q(P4, "keynes_1936",
   "John Maynard Keynes published *The General Theory of Employment, Interest and Money* in February 1936, in the middle of the Great Depression. The book reshaped macroeconomics for the next 50 years. What was its central policy claim?",
   "Government should run deficits during recessions to stimulate aggregate demand — displacing classical balance",
   "Government should always balance its budget — the position of the Austrian school Keynes was challenging",
   "Government should issue a perpetual currency unbacked by gold — position later adopted at Bretton Woods",
   "Government should never intervene in markets under any conditions — position later adopted by Reagan",
   "Keynes's *General Theory* (1936) became the most influential economics work of the 20th century. The framework dominated until stagflation in the 1970s exposed its limits. The post-1970s revival has the same core.")

q(P4, "keynes_animal_spirits",
   "Keynes argued in *The General Theory* (1936) that business investment depended on more than rational calculation. He coined a phrase for the psychological factor — the optimism or pessimism driving investors' willingness to commit. What was the phrase?",
   "'Animal spirits' — gut-feel optimism Keynes argued drove investment, requiring government management",
   "'Rational expectations' — cold, calculating assessment Keynes argued always dominated investment decisions",
   "'Liquidity preference' — Keynes's framework for monetary economics, refuted by Friedman's quantity theory",
   "'Aggregate demand' — Keynes's macro concept, separate from his work on business investment decisions",
   "Keynes's 'animal spirits' has had a long life in popular economics. Implication: markets are emotionally driven and need government stabilization. Austrians counter: interventions designed to 'stabilize' usually destabilize.")

q(P4, "keynes_long_run",
   "Keynes dismissed the classical view that the economy would self-correct over time with one sharp aphorism. The phrase has been quoted, attacked, and defended for nearly a century. What did he say?",
   "'In the long run we are all dead' — justifying short-term intervention at the cost of long-term stability",
   "'In the long run, markets are always right' — Keynes's defense of laissez-faire against intervention",
   "'In the long run, the gold standard always returns' — optimistic view of the inevitability of sound money",
   "'In the long run, government deficits self-finance' — Keynes's MMT-anticipating view of fiscal policy",
   "Keynes's 'long run' line is one of the most-cited (and disputed) aphorisms. Critics: justifies short-term thinking. Defenders: appropriate response to deflationary panic during the Depression.")

q(P4, "hayek_keynes_1931",
   "In 1931 the London School of Economics invited Friedrich Hayek (32) to give four lectures challenging John Maynard Keynes (at Cambridge, 48). The lectures became *Prices and Production* (1931) — the Austrian critique of Keynes's *Treatise on Money* (1930). Central point?",
   "Money flows through specific stages of production — Keynes's aggregate framework missed capital structure",
   "Money is irrelevant to economic activity — Hayek argued monetary policy could never affect production",
   "Money should be replaced entirely by barter — Hayek called for the elimination of all paper currency",
   "Money is purely psychological — Hayek argued outcomes depended on subjective sentiment alone",
   "The Hayek-Keynes LSE 1931 debate is one of the most-cited intellectual confrontations in 20th-century economics. Hayek lost the political battle (Keynesianism dominated postwar policy); the empirical record since has been mixed.")

# --- Phillips curve + breakdown (3) ---

q(P4, "phillips_curve",
   "In 1958, New Zealand economist A.W. Phillips published a paper finding a statistical relationship in UK data back to 1861: when unemployment was low, wage inflation tended high; when unemployment high, wage inflation low. The 'Phillips curve' became central to Keynesian policy. What did it imply?",
   "Policymakers could trade inflation for unemployment — accept inflation to get lower unemployment",
   "Inflation and unemployment were mathematically identical — a deep impossibility for macroeconomics",
   "Inflation always equaled unemployment — both derived from the same underlying labor-market measure",
   "Inflation could never coexist with unemployment — stagflation in the 1970s was therefore impossible",
   "The Phillips curve dominated US macro policy in the 1960s. The 1970s — inflation AND unemployment rose together (stagflation) — empirically broke the simple version. The framework's collapse opened the door to monetarism.")

q(P4, "stagflation",
   "Throughout the 1970s, the US experienced rising inflation AND rising unemployment simultaneously — a combination the simple Phillips curve said could not happen. By 1980, inflation peaked at 14.8% and unemployment was over 7%. What did 'stagflation' reveal?",
   "The Phillips curve was correlation, not mechanism — once inflation expectations adjusted, the tradeoff vanished",
   "The Phillips curve was a perfectly accurate causal relationship — 1970s data was misreported by the BLS",
   "Stagflation was caused entirely by demographic shifts unrelated to inflation or unemployment policy",
   "Stagflation was a temporary anomaly that disappeared by 1973 — the Phillips curve was substantially restored",
   "Stagflation in the 1970s was the canonical empirical refutation of the simple Phillips curve. Friedman and Phelps (late 1960s) had predicted exactly this on theoretical grounds — once people expected inflation, the unemployment 'benefit' would disappear.")

q(P4, "friedman_phelps",
   "Milton Friedman (1968 AEA Presidential Address) and Edmund Phelps (1967) independently argued the apparent Phillips-curve tradeoff would disappear once inflation expectations adjusted. Their prediction: persistent attempts to exploit the tradeoff would produce stagflation. The 1970s vindicated them. What did they call this?",
   "'Natural rate of unemployment' — equilibrium rate monetary policy cannot push below without inflation",
   "'Liquidity trap' — monetary policy becomes ineffective at zero rates regardless of expectations",
   "'Animal spirits' — investor psychology drives unemployment independent of inflation expectations",
   "'Time inconsistency' — policymakers honor inflation promises in the long run regardless of pressure",
   "Friedman's 1968 'Role of Monetary Policy' address is one of the great moments in macroeconomic history — a prediction made in advance that the data then confirmed. The 1976 Nobel honored work that included this.")

# --- Multiplier failures (3) ---

q(P4, "multiplier_2009",
   "Keynesian macro promised a 'fiscal multiplier' — a dollar of government spending would produce more than a dollar of GDP through chain effects. The Obama administration projected the 2009 stimulus would keep unemployment under 8%. By October 2009 unemployment hit 10%. What's the recognition?",
   "Real-world multipliers came in well below projections — policy promises not borne out empirically",
   "Real-world multipliers came in exactly as projected — the 2009 stimulus produced predicted GDP gains",
   "Real-world multipliers exceeded the projections — stimulus was so successful the recession would have ended",
   "Real-world multipliers were never measured for the 2009 stimulus — no data has been collected since",
   "The 2009 stimulus is one of the largest natural experiments on Keynesian multiplier estimates ever run. Promised employment gains did not materialize. Christina Romer later acknowledged projections were too optimistic.")

q(P4, "ricardian_equivalence",
   "Robert Barro (Harvard) revived a 19th-century argument by David Ricardo: if households expect to be taxed in the future to pay off today's deficit-financed spending, they save the stimulus check rather than spend it. Multipliers fall toward zero. What's this called?",
   "Ricardian equivalence — households see through deficit financing and adjust savings, offsetting stimulus",
   "Keynesian equivalence — households spend every stimulus check immediately, multiplier always = 2.5",
   "Mundell-Tobin equivalence — exchange rates adjust to offset fiscal stimulus in any open economy",
   "Lucas equivalence — supply-side responses fully offset any demand-side stimulus in equilibrium",
   "Ricardian equivalence in pure form is unlikely (households don't perfectly anticipate) but the partial version — households save more during deficit-financed stimulus — has substantial empirical support.")

q(P4, "broken_window_gov",
   "Bastiat's broken-window argument generalizes to government spending: the visible benefit (workers employed by the program) is real, but the invisible cost (everything those resources would have done in private hands) is the larger figure. What does this imply?",
   "Net effects depend on whether government allocation beats private allocation — usually it does not",
   "Government spending is always net-positive — Bastiat was wrong about government in particular",
   "Bastiat applies only to physical destruction — borrowed-money spending is fundamentally different",
   "Government spending has no opportunity cost — Keynesian aggregate-demand has proven this since 1936",
   "The Bastiat-to-government-spending generalization is the foundation of the Austrian critique of fiscal stimulus. The seen jobs are real; the unseen jobs that would have existed without the borrowing and taxation are the harder-to-count loss.")

# --- Greenspan + Bernanke (4) ---

q(P4, "greenspan_1987_2006",
   "Alan Greenspan succeeded Volcker as Fed Chairman in August 1987 and served until January 2006 — the second-longest tenure in Fed history. Greenspan was widely credited with managing the 1987 crash, the 1990s expansion, and the dot-com bust. What did Austrians flag?",
   "Greenspan held rates artificially low after each crisis — creating the next bubble instead of correction",
   "Greenspan ran perfectly Austrian monetary policy — praised in Mises Institute publications",
   "Greenspan returned the dollar to gold convertibility through executive Fed decisions during 1999-2001",
   "Greenspan resigned in protest of the 2001 Bush tax cuts — his Fed legacy was condemned by all schools",
   "Greenspan's 'Maestro' reputation cracked after the 2008 GFC. He admitted partial error in 2008 Congressional testimony. Austrian critique: the Greenspan put created moral hazard and inflated successive bubbles.")

q(P4, "greenspan_put",
   "Markets developed a name for Alan Greenspan's pattern of cutting interest rates after every market drop — providing implicit insurance to risk-takers. What was it called?",
   "The 'Greenspan put' — implicit insurance to risk-takers, reducing speculation costs and feeding bubbles",
   "The 'Greenspan tax' — explicit taxation of financial transactions imposed by Fed authority in 1995",
   "The 'Greenspan gold standard' — formal return to gold convertibility under his chairmanship via executive order",
   "The 'Greenspan moratorium' — temporary freeze on all Fed asset purchases imposed throughout his term",
   "The 'Greenspan put' is one of the most-cited concepts in post-1990s monetary economics. The pattern continued under Bernanke ('Bernanke put'), Yellen, and Powell — each cycle brought a larger Fed intervention.")

q(P4, "bernanke_great_moderation",
   "Ben Bernanke (Fed Chair 2006-14) coined 'the Great Moderation' to describe what he saw as a permanent reduction in macroeconomic volatility from ~1985 onward. He attributed it partly to better Fed policy. The phrase aged badly. Why?",
   "The 2008 GFC arrived two years into Bernanke's chairmanship — falsifying the moderation framing",
   "The phrase was retired immediately because economists rejected it as logically incoherent in 2006-07",
   "The Great Moderation was permanent and continues today — 2008 was an isolated supply-shock event",
   "Bernanke later won the Nobel for inventing the Great Moderation — now universally accepted",
   "Bernanke won the 2022 Nobel for his earlier scholarly work on the 1930s banking system. The Great Moderation phrase is now a teaching example of overconfidence preceding crisis.")

q(P4, "bernanke_helicopter",
   "Ben Bernanke earned 'Helicopter Ben' for a 2002 speech discussing Milton Friedman's hypothetical of using a helicopter to drop money on the public if needed to fight deflation. What did Bernanke argue could prevent another Depression?",
   "Aggressive Fed asset purchases — the playbook he executed with QE1, QE2, QE3 after 2008",
   "Direct mailing of cash to all American citizens — the helicopter metaphor was literal in his proposal",
   "Aggressive Fed interest-rate cuts to negative territory — Bernanke advocated rates well below zero",
   "Aggressive gold-buying by the Federal Reserve — Bernanke's plan called for accumulating world gold reserves",
   "Bernanke's 2002 'Deflation' speech laid the intellectual groundwork for QE. Austrian view: helicopter money is Cantillon-effect on steroids — concentrates wealth-transfer effects rather than addressing the underlying capital-misallocation problem.")

# --- Public choice & central banking (3) ---

q(P4, "fed_independence_critique",
   "The Fed is officially 'independent of the government' — Congress cannot override its policy decisions in real time. Defenders cite this independence as crucial. Public-choice critics argue the independence is partial and self-serving. What's the critique?",
   "Independent regulators face minimal democratic accountability while still being captured by industry",
   "Independence is mathematically perfect — the Fed faces no political pressure of any kind from any source",
   "Independence means the Fed serves only its private shareholders, bearing no relationship to public policy",
   "Independence is the only reason the Fed exists at all — without it, the institution would have no purpose",
   "Fed independence is contested between defenders (shields policy from political pressure) and critics (shields regulator from accountability while leaving Wall Street capture intact). Public-choice predicts the latter.")

q(P4, "fed_dual_mandate",
   "The Federal Reserve has a 'dual mandate' established by Humphrey-Hawkins (1978) — to promote both 'maximum employment' and 'stable prices.' Critics argue the two goals can conflict, giving the Fed political cover for whatever policy it wanted. What's the recognition?",
   "Dual mandates let regulators justify any policy by appealing to one goal — a feature for discretion",
   "Dual mandates are mathematically optimal — the Fed has perfectly satisfied both goals since 1978",
   "Dual mandates are a recent invention of post-2008 Fed — no role in monetary policy before Bernanke",
   "Dual mandates are a Soviet invention adopted by the Fed in 1978 as part of a covert Cold War operation",
   "The dual-mandate framing is one reason the Fed faces little accountability for either goal. When inflation is high, the Fed cites employment. When unemployment is high, it cites prices. The discretion is the feature.")

q(P4, "rothbard_case_against_fed",
   "Murray Rothbard's 1994 *The Case Against the Fed* argues central banking is fundamentally political — it serves financial-political interests rather than the public. He documents the lobbying that shaped the 1913 Act. What's the broader Austrian critique?",
   "Central banking centralizes monetary decisions — concentrating wealth-transfer power in unelected hands",
   "Central banking is fundamentally technocratic — Austrians defend central banks against populist criticism",
   "Central banking is a Soviet invention — should be replaced by government-issued unbacked paper currencies",
   "Central banking is the only legitimate form of monetary policy — Austrians supported the 1913 Act",
   "Rothbard's *Case Against the Fed* is one of the most-cited popular Austrian works on monetary institutions. The book documents the lobbying networks and policy choices that founded the modern central-banking arrangement.")


# =========================================================================
# PILLAR 5 — PRACTICAL ECONOMICS (35)
# =========================================================================

# --- Tariffs Smoot-Hawley 1930 (3) ---

q(P5, "smoot_hawley_1930",
   "June 17, 1930: President Herbert Hoover signed the Smoot-Hawley Tariff Act, raising US tariffs to historic highs on over 20,000 imported goods. Over 1,000 economists signed a petition begging Hoover to veto it. He signed anyway. What followed?",
   "World trade collapsed ~65% from 1929 to 1934 as countries retaliated — deepening the Depression",
   "World trade boomed about 65 percent as other countries adopted similar policies — an immediate success",
   "World trade was unaffected — the tariff had no measurable consequences for international flows",
   "World trade shifted to bilateral barter — the tariff successfully removed money from international trade",
   "Smoot-Hawley is the canonical case of trade-policy disaster. Hoover signed; retaliation followed; trade collapsed; the Depression deepened. Modern protectionists rarely cite the episode.")

q(P5, "petition_1000_economists",
   "In May 1930, over 1,000 American economists signed a petition opposing the Smoot-Hawley tariff bill. The petition warned of retaliation, higher consumer prices, and damage to international relations. Hoover signed anyway on June 17. What does the episode illustrate?",
   "Economic consensus can be remarkably solid AND remarkably ignored — political incentives override expert advice",
   "Economic consensus was wrong about Smoot-Hawley — the tariff turned out to be excellent policy",
   "There was no actual consensus among economists in 1930 — the petition was a small minority view",
   "Hoover signed the tariff specifically because the economists demanded that he sign it — misread by history",
   "The 1,000-economist petition is the rare case where the profession was unified on a policy question and the politicians ignored them. Concentrated interests lobby effectively; diffuse interests do not.")

q(P5, "tariffs_seen_unseen",
   "Tariffs visibly protect specific domestic industries — steel workers keep jobs when steel imports are taxed. But Bastiat's method asks: what's the unseen cost? What does the framework reveal?",
   "Higher consumer prices, retaliation against exporters, plus unseen industries that don't form",
   "Tariffs have no unseen costs — the visible benefit to protected industries is the entire effect",
   "Tariffs are paid entirely by foreign producers — domestic consumers never bear any tariff cost",
   "Tariffs benefit consumers by lowering prices — protected industries charge less due to insulation",
   "The Bastiat-to-tariff generalization is one of the cleanest applications of the seen-vs-unseen method. The steel jobs are visible; the consumer-price increases are diffuse but real; the retaliation losses are spread.")

# --- Bastiat Candle Makers 1845 (2) ---

q(P5, "candle_makers",
   "Frederic Bastiat's 1845 satirical essay 'Petition of the Candle Makers' is a masterpiece of economic satire. He has French candle makers petition the government for protection against an 'unfair competitor' that floods the market with light at zero cost. Who is the competitor?",
   "The Sun — candle makers demand the government order all shutters closed during daylight hours",
   "Norwegian whale-oil producers — subsidized competition undercutting the French candle market",
   "British coal-gas lamp manufacturers — protest the importation of cheaper British illumination",
   "American kerosene producers — complain about cheap American imports from the new petroleum industry",
   "Bastiat's 'Petition of the Candle Makers' reduces protectionist arguments to absurdity by applying them consistently. If we should block cheap foreign goods to protect jobs, we should block free sunlight. The reductio is still cited 180 years later.")

q(P5, "bastiat_method",
   "Frederic Bastiat (1801-1850) was a French economist whose career spanned the French liberal revival. His *Economic Sophisms* (1845) and *That Which Is Seen and That Which Is Not Seen* (1850) are masterpieces of accessible political economy. He died at 49. What's his most lasting contribution?",
   "The seen-vs-unseen method — count visible AND invisible consequences of any policy",
   "The theory of comparative advantage — developed independently of Ricardo in the 1840s",
   "The labor theory of value — refined classical labor theory with utility considerations",
   "The general-equilibrium framework — anticipated Walras's later work by formalizing market clearing",
   "Bastiat's seen-vs-unseen method is the foundational lesson of folk economics. It teaches a habit of mind — count what doesn't happen because the policy happened — that any 12-year-old can learn.")

# --- Rent control (4) ---

q(P5, "nyc_rent_control",
   "New York City has had some form of rent control since WWII. The original 1943 federal rent controls became permanent state and city programs after the war. Apartments built before 1947 (and others under various rules) remain regulated. What do economists across schools agree about?",
   "Strict rent controls reduce new construction and lower maintenance — even Krugman and Stiglitz accept this",
   "Strict rent controls increase new construction by giving renters more spending power — broad agreement",
   "There is no consensus on rent control — the question is too politically charged for the profession",
   "Strict rent controls have no measurable effects on housing supply — pure transfers from landlords",
   "Rent control is the rare case of economic-profession consensus across schools (Friedman, Sowell, Krugman, Stiglitz). The 'seen' benefit (lower rent for current tenants) is real. The 'unseen' cost accumulates.")

q(P5, "sweden_lindbeck",
   "Assar Lindbeck (Swedish economist, longtime chair of the Nobel committee for economics) famously wrote: 'next to bombing, rent control seems in many cases to be the most efficient technique so far known for destroying cities.' What was he referring to?",
   "Stockholm's strict rent-control regime — apartment shortages, decade-long waiting lists",
   "His personal preference for purely free markets — the quote was a metaphor with no real referent",
   "His critique of the Swedish welfare state — the quote was about taxation, not rent control",
   "His criticism of American urban-renewal programs — directed at US cities, not European housing",
   "Lindbeck's 'next to bombing' quote is one of the most-cited critiques of rent control. Stockholm has had multi-year waiting lists for regulated apartments — sometimes a decade or longer.")

q(P5, "san_francisco_rent_control",
   "San Francisco passed rent-control measures in 1979 covering most buildings built before that year. Researchers Diamond, McQuade, and Qian (Stanford, 2019) studied the effects using a quasi-experimental design comparing rent-controlled and non-controlled units. What did they find?",
   "Rent control benefited tenants in regulated units but reduced overall housing supply ~15%",
   "Rent control had no measurable effects on housing supply or tenant outcomes — statistically irrelevant",
   "Rent control increased housing supply by about 15% — landlords built more apartments to escape stock",
   "Rent control caused San Francisco rents to fall to half their previous level — clear-cut benefit overall",
   "The Diamond/McQuade/Qian (2019) study is one of the cleanest empirical demonstrations of rent control's mixed effects. Existing tenants benefited; future tenants paid through restricted supply.")

q(P5, "tenant_lock_in",
   "A renter in a rent-controlled NYC apartment paying $1,200/month for a unit that would rent for $3,500 in the unregulated market faces a strong incentive to stay — even after a job opens up in another city. What's this called?",
   "Tenant lock-in — labor mobility falls, the economy becomes less flexible due to suboptimal job stays",
   "Tenant freedom — labor mobility rises because workers no longer worry about rent increases moving",
   "Tenant subsidy — no broader effects, just a transfer from landlord to tenant with no labor consequences",
   "Tenant churn — mobility rises because workers move out of regulated apartments more frequently",
   "Tenant lock-in is one of the less-visible costs of strict rent control. The visible benefit (current tenant pays less) coexists with reduced labor mobility, suboptimal job matches, and a city that doesn't grow.")

# --- Minimum wage (3) ---

q(P5, "minimum_wage_seattle",
   "Seattle passed a 2014 ordinance raising the minimum wage to $15/hour in stages. University of Washington researchers (Jardim et al., 2018) studied the effects using high-quality state administrative data on hours and earnings. What did they find at $13/hour?",
   "Total hours by low-wage workers fell ~9% — wages up but hours down, smaller net earnings than expected",
   "Total hours by low-wage workers rose about 9 percent — higher wage attracted more workers without cuts",
   "Total hours by low-wage workers was unchanged — wage had no impact on hours allocation either way",
   "Total hours by low-wage workers doubled — higher wage caused a massive expansion of employment",
   "The Jardim et al. (2018) Seattle study is one of the highest-quality minimum-wage studies ever conducted, using state administrative data on individual workers. The finding fits the standard supply-and-demand prediction.")

q(P5, "minimum_wage_first_job",
   "A minimum wage above the market clearing wage prices some workers out of the market entirely. Which workers are most affected by this 'unseen' cost?",
   "Young workers, low-skilled, minorities trying to get a first job — those without justifying experience",
   "Senior executives at large corporations — minimum wage affects their compensation packages and bonuses",
   "Government employees — federal workers pegged to private-sector minimum levels by collective bargaining",
   "Foreign workers in their home countries — US minimum wage affects sweatshop pay internationally",
   "First-job effects are the canonical 'unseen' cost of minimum wage. The worker who could have learned skills on a $9 job that no longer exists at $15 doesn't appear in any statistic.")

q(P5, "card_krueger",
   "David Card and Alan Krueger's 1994 New Jersey-Pennsylvania study found that a New Jersey minimum-wage hike did NOT reduce fast-food employment. The paper helped launch a wave of 'minimum wage doesn't hurt employment' research. What did Neumark and Wascher document?",
   "Card-Krueger's data came from phone surveys; Neumark-Wascher used payroll records and found cuts",
   "Card-Krueger's data was perfect and Neumark-Wascher's re-analysis confirmed all original findings",
   "Card-Krueger's data was on retail not fast food — the comparison was inappropriate for either side",
   "Card-Krueger's data was anecdotal — the entire minimum-wage literature was retracted in 1997",
   "The Card-Krueger / Neumark-Wascher dispute is one of the great methodological debates in labor economics. The higher-quality administrative-data studies (like Seattle 2018) tend to find the predicted employment effects.")

# --- Comparative advantage Ricardo + modern (3) ---

q(P5, "ricardo_1817",
   "David Ricardo's 1817 *On the Principles of Political Economy and Taxation* introduced a thought experiment: Portugal and England both produce wine and cloth. Portugal can produce both more efficiently than England in absolute terms. Yet both gain by specializing and trading. What's the concept?",
   "Comparative advantage — opportunity cost matters more than absolute productivity; specialize relatively",
   "Absolute advantage — only the country with absolute productivity gains from trade in this example",
   "Mercantilism — country accumulating most gold wins, so Portugal should refuse to trade with England",
   "Autarky — both countries are better off not trading and producing only what they need domestically",
   "Ricardo's comparative advantage is one of the most counterintuitive results in economics. The 'opportunity cost' framing is the key — even if you're worse at both, you're 'less worse' at one.")

q(P5, "comparative_advantage_modern",
   "China can produce both textiles and computers more cheaply than the United States in absolute terms. Yet both countries gain by China specializing in textiles and the US specializing in higher-end goods. Why?",
   "Opportunity cost — US labor making textiles can produce more value in higher-end goods instead",
   "Absolute cost — the United States cannot compete with China in any industry, so specialization fails",
   "Tariff cost — only countries with high tariffs gain from trade, so the US must impose tariffs",
   "Production cost — countries with cheaper labor always lose from trade, so China should refuse to export",
   "Comparative advantage is a permanent feature of international trade. Even when one country is more productive in everything, opportunity cost creates gains from specialization.")

q(P5, "protectionism_modern",
   "Modern protectionist arguments often claim domestic industries need protection from low-wage foreign competition. But the comparative-advantage framework asks: protection from what, exactly? What does the framework reveal?",
   "Lower foreign wages reflect lower foreign productivity — protection costs consumers and other industries",
   "Lower foreign wages reflect foreign exploitation — protection always benefits domestic consumers",
   "Lower foreign wages have no productivity relationship — modern trade economics abandoned Ricardo",
   "Lower foreign wages are caused by US tariff policy — protection eliminates the wage gap via equalization",
   "The comparative-advantage framework explains why protectionist arguments based on 'cheap foreign labor' miss the deeper point. Wage levels track productivity levels; productivity differences create gains from trade.")

# --- I, Pencil (Leonard Read 1958) + spontaneous order (4) ---

q(P5, "leonard_read",
   "In 1958, Leonard Read published a short essay called 'I, Pencil' — written in the voice of a pencil explaining its own creation. The essay traces the materials (cedar from Oregon, graphite from Ceylon, zinc, copper, rubber). What does the pencil say no one knows how to do?",
   "Make a pencil from scratch — no person knows how to coordinate the millions of decisions involved",
   "Predict the future price of cedar wood — no forecaster has called the cedar futures market correctly",
   "Manufacture a perfect graphite mixture — no chemist has reproduced the Ceylon-graphite formula",
   "Cut cedar wood into perfect strips — no machine can produce the precision needed for a pencil",
   "'I, Pencil' is the most-read popularization of Hayek's knowledge problem. The complex coordination required to make one pencil — across countries, languages, millions of individuals — emerges from the price system without anyone planning.")

q(P5, "spontaneous_order_pencil",
   "Leonard Read's 1958 essay 'I, Pencil' illustrates a deeper Hayekian point. No central planner coordinates the cedar growers, the graphite miners, the zinc refiners, the rubber tappers, the truckers, the factory workers. Yet the pencil emerges. What does this illustrate?",
   "Spontaneous order — complex coordination emerges from voluntary exchange without central direction",
   "Central planning — every step of pencil production is carefully directed by government bureaucracies",
   "Mercantilism — the country producing the most pencils accumulates the most gold for trade victory",
   "Marxism — pencil production demonstrates the labor theory of value with prices reflecting labor inputs",
   "Spontaneous order is Hayek's central insight applied beyond markets. The pencil is the canonical teaching case. No one designed the global pencil-production system; it emerged.")

q(P5, "spontaneous_order_language",
   "Hayek argued spontaneous order applies beyond markets. Language is a paradigm case — English emerged over centuries through the voluntary choices of millions of speakers, without any central authority designing grammar or vocabulary. What does this illustrate?",
   "Complex coordination emerges from decentralized voluntary action — applies to language, law, science",
   "Language requires central authority — every functioning language has a formal Academie approving words",
   "Language is unique — only language emerges spontaneously; all other institutions require central planning",
   "Language is impossible to study scientifically — spontaneous order applies to markets only, not linguistics",
   "Hayek's spontaneous-order framework is one of the great social-science insights. Markets, language, common law, scientific progress — all are examples of complex order without central design.")

q(P5, "common_law_spontaneous",
   "English common law emerged over centuries through case-by-case decisions by judges following precedent. Property law, contract law, tort law — none was designed by a single legislator. It emerged from accumulated judicial decisions. What does Hayek's framework say?",
   "Common law is another example of spontaneous order — complex working rules without any single designer",
   "Common law is central planning in disguise — judges are government officials and decisions are top-down",
   "Common law is inferior to statutory codes — only legislatures produce frameworks that work effectively",
   "Common law is unique to England — no other legal tradition exhibits any form of spontaneous order at all",
   "Hayek's view of common law (*Law, Legislation and Liberty* 1973-79) treats it as a spontaneous-order system. The framework explains why common-law jurisdictions tend toward more flexible, evolving rules.")

# --- Public choice 1962 (3) ---

q(P5, "buchanan_tullock_1962",
   "In 1962, James Buchanan and Gordon Tullock published *The Calculus of Consent: Logical Foundations of Constitutional Democracy*. The book applied economic methodology — rational self-interest, marginal analysis — to politics. What was the core insight?",
   "Politicians, bureaucrats, and voters are self-interested actors, not benevolent guardians of public interest",
   "Politicians, bureaucrats, and voters are perfectly benevolent — political decisions always reflect public interest",
   "Politicians, bureaucrats, and voters cannot be modeled by economics — political science requires different methodology",
   "Politicians, bureaucrats, and voters always make identical decisions — no meaningful difference exists",
   "The Calculus of Consent (1962) founded the field of public-choice economics. Buchanan won the 1986 Nobel. The framework collapses the 'market failure → benevolent government fix' narrative.")

q(P5, "tullock_rent_seeking",
   "Gordon Tullock's 1967 paper 'The Welfare Costs of Tariffs, Monopolies, and Theft' introduced a concept central to public-choice economics. Resources spent competing for political privileges — lobbying, campaign donations, regulatory capture — are pure waste from a social standpoint. What did he name this?",
   "Rent-seeking — social cost of resources spent competing for political privilege rather than producing",
   "Trade-blocking — the social cost of tariffs imposed by foreign governments preventing US exports globally",
   "Tax-shifting — the social cost of tax incidence falling on different parties than the statutory taxpayer",
   "Price-controlling — the social cost of government-imposed price ceilings on staple goods in modern economies",
   "Tullock's rent-seeking concept is one of the most influential ideas in modern political economy. The lobbying expenditures, the campaign donations, the regulatory-arbitrage industries — all are pure social waste.")

q(P5, "buchanan_nobel",
   "James Buchanan won the 1986 Nobel Prize in Economics. The citation honored his work in public-choice theory and constitutional economics. What's the broader significance Buchanan's framework has for the rest of economics?",
   "Once politics is self-interested, 'market failure → government fix' collapses — compare imperfect to imperfect",
   "Once politics is self-interested, government becomes the only solution to market failures — supports activism",
   "Once politics is self-interested, public-choice theory becomes irrelevant — Buchanan was a temporary fad",
   "Once politics is self-interested, all of economics is overthrown — Buchanan refutes the entire field",
   "Buchanan's framework is load-bearing for the entire Austrian / public-choice critique of activist government. Without it, the standard 'market failure → regulate' move proceeds unchecked.")

# --- Regulatory capture (3) ---

q(P5, "stigler_capture",
   "George Stigler (Chicago economist, 1982 Nobel) published 'The Theory of Economic Regulation' in 1971. He argued that regulatory agencies tend to be 'captured' by the industries they regulate — over time, the regulator works for the regulated. What's the mechanism?",
   "Industries have concentrated interest in regulatory outcomes; consumers have diffuse interest — concentrated wins",
   "Regulators are universally corrupt and accept bribes directly — capture happens through illegal payments",
   "Regulators are uniformly incompetent — capture is the result of regulators not understanding the industries",
   "Regulators are perfectly captured at the moment they take office — no time-dependent mechanism in capture",
   "Stigler's capture theory is foundational public-choice economics. The mechanism — concentrated benefits versus diffuse costs — generalizes broadly. Regulators interact daily with the regulated; consumers interact with regulators essentially never.")

q(P5, "fda_capture",
   "The US FDA has been studied as a case of regulatory capture by the pharmaceutical industry. Officials move between FDA roles and pharma jobs. Industry funds a substantial portion of FDA's review budget through user fees (PDUFA, since 1992). What's the recognition?",
   "FDA incentives align with industry over time — without explicit corruption, regulator and regulated serve each other",
   "FDA is perfectly independent of pharmaceutical companies — funding has no relationship to decisions",
   "FDA was created by pharmaceutical companies in 1962 — public-interest framing is a complete fabrication",
   "FDA serves consumers perfectly — user-fee structure ensures full independence from industry influence",
   "The FDA case is one of the most-studied examples of regulatory capture in action. The pattern — user fees, revolving door, mutual dependence — is repeated across SEC, FAA, FCC, and many others.")

q(P5, "sec_wall_street",
   "The SEC regulates Wall Street. Studies of SEC enforcement find a pattern: SEC staff routinely move to Wall Street jobs after their SEC tenure. Aggressive prosecution against firms that might be future employers is rare. What's this an example of?",
   "Regulatory capture through the revolving door — career incentives produce gentle regulation without corruption",
   "Regulatory excellence — the SEC's careful approach reflects sophisticated understanding of complex markets",
   "Regulatory independence — SEC has no relationship to Wall Street firms; the door is a statistical illusion",
   "Regulatory abundance — the SEC enforces too many rules and the door reflects industry frustration",
   "The SEC-Wall-Street revolving door is one of the canonical examples of regulatory capture through career incentives. The mechanism does not require corruption — just rational career planning by individual regulators.")

# --- Revolving door (2) ---

q(P5, "revolving_door",
   "Henry Paulson (Goldman CEO → Treasury Secretary → private investor). Tim Geithner (NY Fed President → Treasury Secretary → private equity). Jay Powell (private equity → Fed Chair). Janet Yellen (Fed Chair → private speaking fees → Treasury Secretary). What's the pattern?",
   "Senior officials routinely move between regulator and regulated — blurring public/private lines over careers",
   "Senior officials always work for the public throughout — speaking fees have no impact on public service",
   "Senior officials are uniformly corrupt — the revolving door is a criminal conspiracy requiring prosecution",
   "Senior officials never return to the private sector — examples cited are unique exceptions to the rule",
   "The revolving door is a public-choice phenomenon: regulators expect future industry jobs, so they regulate gently. Industries hire ex-regulators for relationships and inside knowledge.")

q(P5, "lobbying_dc",
   "Washington DC has over 12,000 registered lobbyists and many more unregistered. Industries facing significant federal regulation — finance, pharma, defense, energy, healthcare — maintain large lobbying operations. What does Tullock's rent-seeking framework say?",
   "Lobbying expenditures are pure social waste — resources competing for privilege rather than producing",
   "Lobbying expenditures are pure social benefit — resources informing legislators improve public policy",
   "Lobbying expenditures are net-zero — every dollar by industry offset by consumer-protection groups in DC",
   "Lobbying expenditures cannot be measured — entirely hidden, no scholar has produced a credible estimate",
   "Tullock's rent-seeking framework treats lobbying as social waste. Resources that could produce goods are instead consumed competing for political privilege. The lobbying industry's size measures how much government has to give away.")

# --- Rent-seeking concept (2) ---

q(P5, "rent_seeking_canonical",
   "Gordon Tullock introduced 'rent-seeking' in his 1967 paper. The term refers to resources spent competing for politically-granted privileges rather than for productively-created value. What's the canonical example?",
   "Lobbying for a tariff that protects your industry — resources to gain political privilege not produce",
   "Investing in research and development — Tullock argued R&D was rent-seeking because of patents",
   "Building a factory to lower production costs — Tullock argued cost-cutting was rent-seeking",
   "Saving money in a high-yield account — Tullock argued any capital return was rent-seeking passive income",
   "Rent-seeking is a key public-choice concept. The canonical examples — lobbying for tariffs, licenses, monopolies, regulatory privileges — are cases where social cost exceeds private gain.")

q(P5, "occupational_licensing",
   "Hairdressers in some US states need 1,500+ hours of training to be licensed. Florists in Louisiana needed a license until 2012. Interior designers in some states need extensive licensing. What does the rent-seeking framework say?",
   "Existing licensed practitioners benefit from reduced competition — 'safety' usually covers protectionism",
   "Public safety requires extensive licensing of all professions — more hours required, safer the public",
   "Licensing has no economic effects — requirements are informational and have no impact on supply",
   "Licensing benefits consumers exclusively — higher prices from restricted supply offset by quality gains",
   "Occupational-licensing rent-seeking has been studied extensively. The 'public safety' framing rarely holds up to scrutiny. The actual function is restricting entry to protect incumbents.")

# --- Additional Practical (4) ---

q(P5, "price_signal_shortage",
   "A price ceiling set below the market clearing price creates shortages — quantity demanded exceeds supply. The 1973 US gas-line crisis (long lines at gas stations) is the canonical example. What policy caused it?",
   "Federal price controls on gasoline holding the price BELOW market — buyers chased limited supply",
   "OPEC's embargo alone caused the lines — there was no US federal policy involvement at all",
   "American oil refiners deliberately shut down in 1973 to inflate prices — a private-sector decision",
   "Federal price controls on gasoline holding the price ABOVE market — buyers had no incentive to purchase",
   "The 1973 gas lines are the canonical case of price-ceiling-caused shortage. Set the price below market and demand outruns supply. The lines were the seen cost; the unbuilt refineries were the unseen cost.")

q(P5, "price_signal_hayek",
   "Hayek's central insight: prices encode dispersed, tacit, local information no central planner can collect. When wheat prices rise, every farmer, baker, restaurant, and consumer adjusts — without anyone knowing why. What does this show?",
   "Price system is the world's information system — solves coordination problems no planner could solve",
   "Price system is irrelevant to coordination — central planners with enough computing power could replicate",
   "Price system causes coordination failures — markets always need government intervention to function",
   "Price system exists only because of government — without state enforcement, no price could ever form",
   "Hayek's price-signal insight is the deepest in 20th-century economics. The 'use of knowledge in society' (1945) makes the case in 14 pages. Central planning fails not because planners aren't smart — because the information they'd need is not centralizable.")

q(P5, "opportunity_cost",
   "Every choice has an opportunity cost — the value of the next-best alternative foregone. A college student who studies on a Friday night gives up whatever else she might have done. What does this concept reveal?",
   "Real cost is what you give up to get something — not the dollar price, which can mislead about sacrifice",
   "Real cost is always the dollar price — opportunity cost is theoretical, no relevance to actual decisions",
   "Real cost varies by jurisdiction — opportunity cost is calculated differently in different countries",
   "Real cost is determined by government regulators — opportunity cost is set by official policy",
   "Opportunity cost is one of economics' most useful concepts. The 'true' cost of any action is what you give up to do it. The Bastiat method applied to individual decisions.")

q(P5, "sowell_and_then_what",
   "Thomas Sowell — economist, columnist, longtime Hoover Institution fellow — wrote *Basic Economics* (2000, 6 editions through 2023) explicitly for non-economists. His central methodological framing comes from a question. What does Sowell ask repeatedly?",
   "'And then what?' — pushing past visible first-order effects to unseen second- and third-order consequences",
   "'Why is this?' — pushing for underlying cause of any observed outcome through systematic causal analysis",
   "'Who pays?' — pushing for identification of the specific party bearing cost of any economic decision",
   "'How much?' — pushing for quantification of every economic claim through rigorous statistical methods",
   "Sowell's 'and then what?' is the Bastiat seen-vs-unseen method in conversational form. The question pushes past the visible first-order effect (more pay for workers!) to second- and third-order effects (fewer hours, layoffs, automation, no first jobs).")


# ============================================================================
# COMBINE + VALIDATE
# ============================================================================

ALL = P3 + P4 + P5


def main():
    print(f"Generated: P3={len(P3)}, P4={len(P4)}, P5={len(P5)}, total={len(ALL)}")
    expected = {3: 40, 4: 45, 5: 35}
    actual = {3: len(P3), 4: len(P4), 5: len(P5)}
    print(f"Expected: {expected}")
    print(f"Actual:   {actual}")

    if OVER_BUDGET:
        print(f"\n=== OVER BUDGET ({len(OVER_BUDGET)}) ===")
        for s, t, qq in OVER_BUDGET:
            print(f"  {t}c {s}")
        print()

    # Load existing economics bank
    with open(REPO / "data" / "questions" / "economics.json", "r", encoding="utf-8") as f:
        existing_bank = json.load(f)
    print(f"Existing bank: {len(existing_bank)} questions")

    combined = existing_bank + ALL
    dup, ans = build_bank_indices(combined)

    fails: list = []
    softs: list = []
    passes = 0
    for i, q in enumerate(ALL):
        replace_idx = len(existing_bank) + i
        r = validate_rewrite(
            "economics", q, bank=combined, dup_index=dup, answer_index=ans,
            replace_idx=replace_idx,
        )
        total = len(q["question"]) + sum(len(c) for c in q["choices"])
        if r["verdict"] == "FAIL":
            fails.append((i, q, r, total))
        elif r["verdict"] == "SOFT_WARN":
            softs.append((i, q, r, total))
        else:
            passes += 1

    print()
    print(f"PASS: {passes}")
    print(f"SOFT_WARN: {len(softs)}")
    print(f"FAIL: {len(fails)}")
    print()
    if fails:
        print("=" * 60)
        print("FAILURES:")
        print("=" * 60)
        for i, q, r, total in fails[:50]:
            print(f"\n[{i}] Pillar {q['_pillar']}, total={total}c, strategy={q.get('_strategy', '')}")
            print(f"  Q: {q['question'][:100]}")
            for g, reason in r["hard_fails"]:
                print(f"  FAIL {g}: {reason[:200]}")
    if softs:
        print()
        print("=" * 60)
        print("SOFT WARNS:")
        print("=" * 60)
        for i, q, r, total in softs[:50]:
            print(f"\n[{i}] Pillar {q['_pillar']}, total={total}c, strategy={q.get('_strategy', '')}")
            print(f"  Q: {q['question'][:100]}")
            for g, reason in r["soft_warns"]:
                print(f"  SOFT {g}: {reason[:200]}")

    out_questions = []
    for q in ALL:
        out_q = {k: v for k, v in q.items() if not k.startswith("_")}
        out_questions.append(out_q)

    out = {
        "tier": 3,
        "summary": {
            "questions_generated": len(ALL),
            "by_pillar": {"3": len(P3), "4": len(P4), "5": len(P5)},
            "pass": passes,
            "soft_warn": len(softs),
            "fail": len(fails),
        },
        "questions": out_questions,
    }

    out_path = REPO / "_gen_economics_t3_p345.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {len(ALL)} questions to {out_path}")
    return len(fails)


if __name__ == "__main__":
    sys.exit(main())
