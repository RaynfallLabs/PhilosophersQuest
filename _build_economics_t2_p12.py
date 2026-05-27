"""Build 120 fresh Tier-2 economics questions: 60 P1 Austrian + 60 P2 Bitcoin.

Voice: The Bastiat Pattern — one scene + named figure + the action/argument.
Stance: Austrian school CORRECT. Bitcoin GREAT HUMAN ACHIEVEMENT.
Story-in-stem from day 1. Em-dash uniform across all 4 choices in each question
(either ALL four have a dash, or NONE do — skim-tell guard).

T2 cap: 480 chars total. Asserted <= 475 with safety buffer.
Output: _gen_economics_t2_p12.json with summary + questions.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402


QUESTIONS: list[dict] = []


def q(pillar: int, strategy: str, question: str, answer: str, distractors: list[str], context: str) -> None:
    """Append a question, asserting T2 budget."""
    assert len(distractors) == 3, f"need 3 distractors, got {len(distractors)} ({strategy})"
    total = len(question) + len(answer) + sum(len(d) for d in distractors)
    assert total <= 475, f"OVER BUDGET T2 ({strategy}): {total} chars"
    QUESTIONS.append({
        "tier": 2,
        "question": question,
        "answer": answer,
        "choices": [answer] + distractors,
        "context": context,
        "_pillar": pillar,
        "_strategy": strategy,
    })


# ============================================================================
# PILLAR 1 — AUSTRIAN FOUNDATIONS (60 questions)
# ============================================================================

# --- Carl Menger and the 1871 founding (5) ---

q(1, "menger_1871_principles",
    "In 1871 a 31-year-old Vienna journalist named Carl Menger published a slim book that launched what came to be called the Austrian school of economics. What was the book titled in English?",
    "Principles of Economics, founding the Austrian school",
    [
        "The Wealth of Nations, the famous Smith treatise of 1776",
        "Das Kapital, the major Marxist work first published in 1867",
        "The General Theory, the foundational Keynesian text of 1936",
    ],
    "Menger's 'Grundsatze der Volkswirthschaftslehre' (1871) overturned the classical labor theory of value. Jevons in England and Walras in Switzerland reached related marginal-utility ideas the same decade — the 'marginal revolution' of 1871-74.")

q(1, "menger_subjective_value",
    "Carl Menger's 1871 Principles of Economics overturned an older idea about where value comes from. The classicals had said it came from labor hours or production cost. Where did Menger argue value actually lives?",
    "In the subjective preferences of individuals ranking their ends",
    [
        "In the average number of work hours required to produce the good",
        "In the historical cost of capital that was invested in the good",
        "In the aggregate equilibrium of nationwide supply and demand",
    ],
    "Menger's subjective-value insight is the Austrian school's founding move. Value isn't 'in' a thing; it's a relationship between a person's goals and the thing's ability to serve those goals. This dissolves Marx's labor-theory and reorients economics around human action.")

q(1, "menger_diamond_water_paradox",
    "Classical economists were stumped by a puzzle: water is essential to life but cheap, diamonds are useless but expensive. In 1871 Carl Menger solved the paradox cleanly. What concept did he introduce?",
    "Marginal utility, the value of one more unit at the margin",
    [
        "Average utility, the mean satisfaction of all consumers added up",
        "Aggregate utility, the total social welfare from the good in sum",
        "Intrinsic utility, the inherent worth a good has on its own",
    ],
    "An extra diamond matters more than an extra glass from a lake — that's the marginal insight. Menger, Jevons (England), and Walras (Switzerland) each reached this around 1871. The marginal revolution unified the price puzzle classical economics couldn't crack.")

q(1, "menger_methodenstreit_debate",
    "In the 1880s Carl Menger fought a long public debate against the German Historical School, who said economics should just collect historical data. What did Menger insist economics also needed?",
    "Universal logical principles deduced from human action itself",
    [
        "Government-funded statistical bureaus to gather all the data",
        "Complete mathematical models with equations for every market",
        "Laboratory-style experiments to test economic theories rigorously",
    ],
    "The Methodenstreit ('method dispute') pitted Menger against Gustav Schmoller's German Historical School. Menger insisted economics had laws (like value, exchange, prices) that could be derived from the fact of human action, not just induced from data. The dispute defined the Austrian method.")

q(1, "bohm_bawerk_capital_interest",
    "Carl Menger's most famous student was Eugen von Bohm-Bawerk, who in the 1880s wrote a massive work explaining interest and capital. What did Bohm-Bawerk argue interest fundamentally is?",
    "The price of time, reflecting that present goods are valued above future ones",
    [
        "Exploitation of workers by employers who paid less than the labor value",
        "A reward central banks pay savers for parking money in their vaults",
        "An arbitrary social custom with no real economic function behind it",
    ],
    "Bohm-Bawerk's 'Capital and Interest' (1884) and 'Positive Theory of Capital' (1889) refuted Marx's exploitation theory of profit. Interest exists because people prefer present goods to future goods — time preference, the foundation of Austrian capital theory.")

# --- Ludwig von Mises 1920 calculation problem (5) ---

q(1, "mises_1920_calculation_essay",
    "In 1920 Ludwig von Mises published a 36-page essay arguing socialism was not merely inefficient but IMPOSSIBLE. What was the essay titled in English translation?",
    "Economic Calculation in the Socialist Commonwealth",
    [
        "The Communist Manifesto, the founding socialist statement of 1848",
        "The Road to Serfdom, the famous critique of central planning",
        "Capitalism and Freedom, the Friedman classic published in 1962",
    ],
    "Mises's 1920 essay (in German: 'Die Wirtschaftsrechnung im sozialistischen Gemeinwesen') is the foundational refutation of central planning. Without private capital, no prices for capital goods; without prices, no rational allocation. The 20th-century record vindicated it.")

q(1, "mises_calculation_no_prices",
    "Ludwig von Mises in 1920 said socialist planners could never run an economy rationally. His argument: without private ownership of factories and machines, something essential vanishes. What vanishes?",
    "Market prices for capital goods, which planners need for any calculation",
    [
        "Workers' willingness to do the actual labor in those factories",
        "The technical engineering blueprints required for mass production",
        "Political support among the population for the socialist system",
    ],
    "Mises's calculation argument: a socialist commonwealth has no markets for capital goods (steel, oil, machinery), so no prices form. Without prices, planners can't compare 'is it better to make 1000 tractors or 5000 plows from this steel?' The result is shortages, famines, gulags.")

q(1, "mises_1922_socialism_book",
    "Two years after his 1920 calculation essay, Ludwig von Mises expanded it into a full book arguing socialism would fail in every form. What was the book called?",
    "Socialism, an Economic and Sociological Analysis",
    [
        "Marxism Decoded, the popular polemic of the same year",
        "Soviet Economics, the field handbook for Russian planners",
        "The Capitalist Manifesto, the foundational pro-market book",
    ],
    "Mises's 'Die Gemeinwirtschaft' (1922; English 'Socialism' 1936) extended the calculation argument to syndicalism, guild socialism, Christian socialism, and other variants. The book convinced a generation of European socialists — including F.A. Hayek — to abandon socialism.")

q(1, "mises_kreis_seminar_vienna",
    "Through the 1920s Ludwig von Mises ran a private seminar in his Vienna chamber-of-commerce office. Famous attendees included Friedrich Hayek, Fritz Machlup, and Oskar Morgenstern. What was the seminar called in German?",
    "The Kreis, German for 'the circle' meeting Fridays at his office",
    [
        "The Verein, German for the official union or league",
        "The Bund, German for the political alliance or association",
        "The Reich, German for the empire or governing realm",
    ],
    "Mises's Privatseminar (the Kreis, 1920-1934) was the intellectual center of interwar Austrian economics. Met every other Friday in Mises's Chamber of Commerce office. Nazi annexation in 1938 scattered the group; Mises fled to Geneva, then America in 1940.")

q(1, "mises_human_action_1949",
    "Ludwig von Mises wrote his magnum opus in English from his New York exile. Published by Yale University Press in 1949, the 900-page treatise founded what Mises called 'praxeology.' What is the book titled?",
    "Human Action, A Treatise on Economics",
    [
        "The Wealth of Nations, the 1776 economic classic by Adam Smith",
        "Capitalism and Freedom, the 1962 Friedman bestseller",
        "Principles of Economics, the founding 1871 Menger text",
    ],
    "Mises wrote 'Nationalokonomie' (1940) in German first while in Geneva; 'Human Action' (1949) was the expanded English version. The book treats economics as a deductive science based on the logic of purposeful action — the praxeological method.")

# --- Friedrich Hayek (8) ---

q(1, "hayek_lse_1931_lectures",
    "In 1931 the London School of Economics invited a young Austrian economist named Friedrich Hayek to give four lectures challenging the work of John Maynard Keynes at Cambridge. What did Hayek's lectures become as a book?",
    "Prices and Production, his 1931 capital-theory critique",
    [
        "The General Theory, the famous Keynesian work of 1936",
        "Wealth of Nations, the Adam Smith classic from 1776",
        "Free to Choose, the Friedman bestseller from the year 1980",
    ],
    "Hayek's 1931 LSE lectures — published as 'Prices and Production' — argued Keynes ignored the structure of capital. Money flows through specific stages of production, not as a single aggregate. The lectures launched the great Hayek-Keynes debate of the 1930s.")

q(1, "hayek_road_to_serfdom_1944",
    "In 1944 Friedrich Hayek published a short book warning that central planning of the economy leads toward political tyranny. Reader's Digest condensed it; it became a worldwide bestseller. What is the book called?",
    "The Road to Serfdom, his 1944 warning against central planning",
    [
        "The Communist Manifesto, the founding text by Marx and Engels",
        "The General Theory, the famous economic treatise by Keynes",
        "Atlas Shrugged, the famous novel by Ayn Rand in 1957",
    ],
    "Hayek's 'Road to Serfdom' (1944) was written for British readers during WWII as a warning that the postwar planned-economy enthusiasm could end in totalitarian rule. Churchill cited it. Reader's Digest condensed it in 1945. Hayek dedicated it 'to the socialists of all parties.'")

q(1, "hayek_1945_knowledge_paper",
    "Friedrich Hayek's most-cited essay appeared in the American Economic Review in September 1945. It argued the central economic problem is using knowledge no individual has. What is the paper's exact title?",
    "The Use of Knowledge in Society, his 1945 dispersed-knowledge paper",
    [
        "The Wealth of Nations, the founding classic by Adam Smith",
        "The Road to Serfdom, his 1944 anti-planning book",
        "Prices and Production, his earlier LSE lectures of 1931",
    ],
    "Hayek's 1945 essay is the canonical statement of the knowledge problem. Prices encode dispersed, tacit, local information no central planner can collect. The price system is, in Hayek's phrase, 'a marvel.' The essay is one of the most-cited in 20th-century economics.")

q(1, "hayek_price_signal",
    "Friedrich Hayek's central insight, for which he won the 1974 Nobel: no single mind can know all prices, needs, and shortages of millions of people across an economy. What does the job for us automatically?",
    "The price system, signaling scarcity and abundance everywhere",
    [
        "A large super-computer kept running by the federal government",
        "A team of experienced experts voting on prices every week",
        "Three or four big companies coordinating to set the prices",
    ],
    "Hayek argued prices are signals. A tin shortage in Malaysia raises the global tin price; producers respond; consumers economize; substitutes get developed. Nobody designed this. The result coordinates the actions of millions of strangers across the globe.")

q(1, "hayek_spontaneous_order",
    "Friedrich Hayek's name for the way markets, language, and common law all emerge over time without any central designer was a Latin phrase meaning 'order that grew.' What is the concept called?",
    "Spontaneous order, the result of human action but not design",
    [
        "Central planning, the result of state coordination from above",
        "Mercantilism, the doctrine of trade controlled by the state",
        "Statism, the political doctrine of expansive government power",
    ],
    "Hayek borrowed the phrase 'spontaneous order' from Adam Ferguson (1767): 'the result of human action, but not the execution of any human design.' The price system, common law, the English language, science itself — all emerge from individual actions without anyone planning the whole.")

q(1, "hayek_1974_nobel",
    "In 1974 Friedrich Hayek became the first Austrian-school economist to win the Nobel Prize in Economics. The committee paired him with an unlikely co-winner. Who was it?",
    "Gunnar Myrdal, a Swedish socialist with opposing views",
    [
        "Milton Friedman, his Chicago-school ally from the United States",
        "Ludwig von Mises, his teacher who had died the year before",
        "Murray Rothbard, his American Austrian-school colleague",
    ],
    "Hayek and Myrdal shared the 1974 Nobel. Hayek had been a 'forgotten' economist for decades while Keynesianism dominated. The 1970s stagflation discredited Keynesian models, and the Nobel committee paired Hayek (free markets) with Myrdal (socialist) to signal balance. Friedman won in 1976.")

q(1, "hayek_constitution_of_liberty",
    "In 1960 Friedrich Hayek published a major work defending free institutions, the rule of law, and limited government against postwar enthusiasm for planning. What was the book called?",
    "The Constitution of Liberty, his 1960 philosophical treatise",
    [
        "Democracy in America, the famous study by Tocqueville",
        "Liberalism, the foundational text by Ludwig von Mises",
        "Capitalism and Freedom, the popular Milton Friedman book",
    ],
    "Hayek's 'Constitution of Liberty' (1960) and later 'Law, Legislation, and Liberty' (3 vols, 1973-79) extended his economic arguments to politics and law. Margaret Thatcher famously slammed a copy on a table at a Conservative Party meeting and said 'this is what we believe.'")

q(1, "hayek_business_cycle_abct",
    "Friedrich Hayek's 1931 Prices and Production introduced the Austrian Business Cycle Theory, building on Ludwig von Mises's 1912 work. The theory says artificial credit expansion causes which pattern?",
    "Boom in the wrong industries, then bust when rates normalize",
    [
        "Steady growth in all industries that lasts indefinitely with no bust",
        "A short recession followed by a permanent prosperity afterward",
        "Random unpredictable cycles unrelated to any monetary policy",
    ],
    "Austrian Business Cycle Theory: central banks set rates below the natural rate, businesses invest in projects that look profitable at the low rate but become losers when rates rise. The 2008 housing bust was the cleanest modern case — Fed at 1% from 2003-04.")

# --- Murray Rothbard (5) ---

q(1, "rothbard_1962_man_economy_state",
    "In 1962 the American economist Murray Rothbard published a massive systematic treatise extending Ludwig von Mises's Human Action into a complete picture of the market economy. What was Rothbard's book called?",
    "Man, Economy, and State, his 1962 comprehensive treatise",
    [
        "Wealth of Nations, the founding Adam Smith book of 1776",
        "Principles of Economics, the founding Menger book of 1871",
        "Human Action, the founding Mises book of the year 1949",
    ],
    "Rothbard's 'Man, Economy, and State' (1962) is the most systematic statement of Misesian economics. He wrote it as a textbook expansion of Human Action for the William Volker Fund. The companion volume 'Power and Market' (1970) covers state intervention.")

q(1, "rothbard_living_room_seminar",
    "Through the 1970s and 1980s the American economist Murray Rothbard ran an Austrian seminar in his New York apartment. Students drove in from across the country. What did Rothbard's New York gatherings produce?",
    "A generation of Austrian-school economists who carried his work forward",
    [
        "A failed political party that lost every election it entered easily",
        "A literary movement focused on writing novels of social criticism",
        "A religious revival movement among American academic economists",
    ],
    "Rothbard's apartment seminars (and later Auburn, Alabama gatherings at the Mises Institute founded 1982) trained Joseph Salerno, Walter Block, Hans-Hermann Hoppe, Jorg Guido Hulsmann, and many others. The contemporary Austrian revival traces directly to these private circles.")

q(1, "rothbard_america_great_depression",
    "Murray Rothbard's 1963 book applied Austrian Business Cycle Theory to the 1929 crash and the 1930s. The argument: the Fed's 1920s credit expansion caused the boom that had to crash. What is the book called?",
    "America's Great Depression, his 1963 ABCT analysis of the 1930s",
    [
        "A Monetary History, the famous Friedman-Schwartz book of 1963",
        "The Great Crash, the Galbraith popular history book of 1955",
        "Capitalism and Freedom, the Milton Friedman bestseller of 1962",
    ],
    "Rothbard's 'America's Great Depression' (1963) blames the 1920s Fed-fueled credit boom (cheap money to help postwar Britain) for the malinvestment that crashed in 1929. Hoover's interventions (not laissez-faire) then deepened and lengthened the depression.")

q(1, "rothbard_for_a_new_liberty",
    "In 1973 Murray Rothbard published a popular statement of his libertarian political philosophy, applying Austrian economics to law, defense, money, and education. What did he title the book?",
    "For a New Liberty, his 1973 libertarian manifesto",
    [
        "The Road to Serfdom, the famous earlier Hayek work of 1944",
        "Atlas Shrugged, the Ayn Rand novel published in 1957",
        "The Communist Manifesto, the famous Marx-Engels text of 1848",
    ],
    "Rothbard's 'For a New Liberty' (1973) is the most-read introduction to libertarian thought from the Austrian tradition. He argued markets handle nearly every social problem better than the state; central banks, public schools, and standing armies were among his targets.")

q(1, "rothbard_mises_institute_1982",
    "Two years before Murray Rothbard's death, the Mises Institute was founded at Auburn, Alabama by Llewellyn Rockwell with Ron Paul, Henry Hazlitt, and Margit von Mises on the board. What year?",
    "1982, with Rothbard as academic vice president",
    [
        "1932, decades earlier when Mises was still in Vienna seminar",
        "1962, when Rothbard's Man Economy State was first published",
        "2002, decades after Rothbard had already passed away peacefully",
    ],
    "The Ludwig von Mises Institute was founded in 1982 in Auburn, Alabama. Murray Rothbard served as academic vice president until his death in 1995. The Institute is the leading scholarly center for contemporary Austrian economics, publishing the Quarterly Journal of Austrian Economics.")

# --- Thomas Sowell (5) ---

q(1, "sowell_basic_economics_book",
    "The American economist Thomas Sowell wrote a popular textbook explaining markets, prices, and trade without using a single graph or equation. The book has gone through five editions since 2000. What is it called?",
    "Basic Economics, A Common Sense Guide to the Economy",
    [
        "The General Theory, the famous Keynesian work from the year 1936",
        "The Wealth of Nations, the founding 1776 Adam Smith classic",
        "Free to Choose, the famous Milton Friedman PBS-tied book of 1980",
    ],
    "Thomas Sowell's 'Basic Economics' (first edition 2000, fifth 2014) is one of the most-read introductions to economic reasoning. Sowell deliberately uses no equations or graphs, only verbal arguments — accessible to anyone willing to think carefully.")

q(1, "sowell_marxist_to_chicago",
    "Thomas Sowell entered Howard University as a young Marxist in the 1950s. He transferred to Harvard, got his PhD from the University of Chicago, and along the way changed his mind. What changed him?",
    "A summer job in 1960 showing him how government really worked up close",
    [
        "Reading the works of Karl Marx more carefully convinced him of socialism",
        "A youth program from the Communist Party reinforced his commitments",
        "Direct lobbying from Ayn Rand changed his political philosophy",
    ],
    "Sowell has often told the story: as a young Marxist economist he took a summer job at the US Department of Labor researching the minimum wage. The data and the bureaucratic incentives he observed broke his faith in government action. He became a leading critic of progressive policy.")

q(1, "sowell_knowledge_and_decisions",
    "Thomas Sowell's 1980 book extended Friedrich Hayek's 1945 knowledge-problem paper into a full theory of how different institutions handle dispersed information. What did Sowell title the book?",
    "Knowledge and Decisions, his 1980 extension of Hayek's argument",
    [
        "Basic Economics, his common-sense market textbook from 2000 first",
        "Capitalism and Freedom, the Milton Friedman classic of 1962",
        "Free to Choose, the famous Milton Friedman PBS-companion of 1980",
    ],
    "Sowell's 'Knowledge and Decisions' (1980) compares market and political institutions on how each handles knowledge dispersed across society. The book was the work Sowell himself considered his most important contribution. Hayek wrote that it 'redoes Hayek for our generation.'")

q(1, "sowell_ethnic_america",
    "Thomas Sowell's 1981 book traced economic histories of nine American ethnic groups, arguing different groups rose differently because of skills, work patterns, and timing — not because of government programs. What is the book called?",
    "Ethnic America, his 1981 comparative-group economic history",
    [
        "Wealth of Nations, the founding Adam Smith book of 1776 again",
        "Capitalism and Freedom, the famous Milton Friedman classic",
        "The Bell Curve, the later book by Murray and Herrnstein",
    ],
    "Sowell's 'Ethnic America' (1981) traced the rise of Irish, Italian, Jewish, German, Chinese, Japanese, Mexican, Black, and Puerto Rican populations in America. He argued cultural variables — work, education, family — explain outcomes better than the discrimination-centered models common in academic sociology.")

q(1, "sowell_visions_conflict",
    "Thomas Sowell's 1987 book argues that political disagreements come less from facts than from two fundamental 'visions': one sees humans as fixed and constrained, the other as perfectible by experts. What is the book called?",
    "A Conflict of Visions, his 1987 framing of left-right disputes",
    [
        "Capitalism and Freedom, the famous Friedman classic from 1962",
        "The General Theory, the famous Keynesian work from 1936",
        "The Road to Serfdom, the famous earlier Hayek book of 1944",
    ],
    "Sowell's 'A Conflict of Visions' (1987) names the constrained vision (Smith, Burke, Hayek, Sowell) versus the unconstrained vision (Rousseau, Godwin, Condorcet, modern progressive thought). The book is one of the clearest available statements of the deep root of left-right division.")

# --- Milton Friedman (5) ---

q(1, "friedman_1976_nobel",
    "Milton Friedman, the Chicago-school economist who defended free markets and stable money, won the Nobel Prize in Economics in what year?",
    "1976, two years after his ally Friedrich Hayek won it",
    [
        "1986, the same year as Buchanan won the same Nobel award",
        "1966, before he had really established his American reputation",
        "1996, just a decade before his death from heart failure",
    ],
    "Friedman won the 1976 Nobel for his monetary work — 'A Monetary History' (1963 with Anna Schwartz) had reshaped how the Great Depression was understood. Hayek had won in 1974; the back-to-back awards marked a Keynesian-orthodoxy retreat.")

q(1, "friedman_free_to_choose_1980",
    "In 1980 Milton Friedman and his wife Rose Friedman starred in a ten-part PBS television series defending free markets against government planning. The companion book was a bestseller. What were the series and book called?",
    "Free to Choose, the 1980 ten-part PBS series with companion book",
    [
        "Capitalism and Freedom, the earlier 1962 Friedman book",
        "The Road to Serfdom, the 1944 Hayek classic anti-planning book",
        "Wealth of Nations, the 1776 Adam Smith founding economic text",
    ],
    "'Free to Choose' (PBS, 1980; book by Friedman + Rose Friedman, 1980) was the most-viewed economic program in American television history. The book was a #1 bestseller for five weeks. The series shaped the Reagan-Thatcher era's intellectual climate.")

q(1, "friedman_schwartz_1963_monetary_history",
    "In 1963 Milton Friedman and Anna Schwartz published a monumental study of US monetary policy. Their argument: the Federal Reserve caused the Great Depression by letting the money supply collapse. What is the book called?",
    "A Monetary History of the United States, 1867 to 1960",
    [
        "Free to Choose, the famous later PBS-companion book of 1980",
        "Capitalism and Freedom, the Friedman policy classic from 1962",
        "Lombard Street, the British 1873 Bagehot banking treatise",
    ],
    "Friedman and Schwartz's 'A Monetary History' (1963) showed the US money supply contracted by about one-third between 1929 and 1933. The Fed, founded 1913 to prevent panics, presided over the largest monetary contraction in US history. Bernanke later said: 'we did it.'")

q(1, "friedman_permanent_income",
    "Milton Friedman's 1957 book introduced an idea that broke a key Keynesian assumption about consumption. People plan spending based on expected lifetime income, not just current paychecks. What is this called?",
    "The permanent income hypothesis, his 1957 consumption theory",
    [
        "The marginal propensity to consume, the original Keynesian framing",
        "The paradox of thrift, the standard Keynesian saving-paradox claim",
        "The accelerator theory, the standard Keynesian investment framing",
    ],
    "Friedman's 'A Theory of the Consumption Function' (1957) showed people smooth consumption across expected lifetime income. This refuted the simple Keynesian multiplier: temporary stimulus checks won't boost spending much if households see them as one-time. The 2008 + 2020 stimulus rounds vindicated Friedman.")

q(1, "friedman_inflation_monetary",
    "Milton Friedman's most-quoted sentence summarizes the core monetarist position in one line. It locates the cause of rising prices in one specific source. What is the famous Friedman line?",
    "Inflation is always and everywhere a monetary phenomenon",
    [
        "Inflation is always caused by trade unions pushing wages too high quickly",
        "Inflation is always caused by big corporations grabbing more profit margin",
        "Inflation is always caused by greedy consumers refusing to save enough",
    ],
    "Friedman's monetarism: 'inflation is always and everywhere a monetary phenomenon, in the sense that it is and can be produced only by a more rapid increase in the quantity of money than in output.' The 2021-23 US inflation arrived after the M2 money supply grew about 40% in 2020-21.")

# --- Buchanan + Tullock public choice (5) ---

q(1, "buchanan_tullock_1962_calculus",
    "In 1962 James Buchanan and Gordon Tullock published a book applying economic methods to political decision-making. Their central claim: politicians, voters, and bureaucrats are self-interested too. What is the book called?",
    "The Calculus of Consent, their 1962 founding public-choice book",
    [
        "The Wealth of Nations, the founding Adam Smith book of 1776",
        "The General Theory, the famous 1936 Keynesian treatise",
        "Capitalism and Freedom, the popular Milton Friedman 1962 book",
    ],
    "Buchanan and Tullock's 'The Calculus of Consent' (1962) founded the field of public choice. The book collapsed the 'market failure → benevolent government fixes it' framing by treating government actors as self-interested too. Buchanan won the 1986 Nobel for this work.")

q(1, "buchanan_1986_nobel_public_choice",
    "Public choice theory was honored when its leading exponent won the Nobel Prize in Economics in 1986. Which of the two co-founders received the prize?",
    "James Buchanan, who developed the constitutional-economics branch",
    [
        "Gordon Tullock, who developed the rent-seeking analytical framework",
        "Milton Friedman, who had won his Nobel ten years earlier in 1976",
        "Friedrich Hayek, who had won his Nobel twelve years earlier in 1974",
    ],
    "Buchanan won the 1986 Nobel 'for his development of the contractual and constitutional bases for the theory of economic and political decision-making.' Tullock never won, despite his foundational rent-seeking paper — a long-running irritation in the public-choice community.")

q(1, "tullock_1967_rent_seeking",
    "Gordon Tullock's 1967 paper introduced an idea now central to political economy: firms spend real resources competing for government privileges rather than producing things. What is this competition called?",
    "Rent-seeking, the social waste of competing for political privilege",
    [
        "Price gouging, the standard term for raising prices in shortages",
        "Monopolistic competition, the standard term for differentiated products",
        "Free riding, the standard term for benefiting without contributing",
    ],
    "Tullock's 1967 paper 'The Welfare Costs of Tariffs, Monopolies, and Theft' coined what Anne Krueger (1974) later named 'rent-seeking.' Real resources spent lobbying for licensing privileges or import protection are pure social waste — neither produced nor consumed, just dissipated.")

q(1, "buchanan_regulatory_capture",
    "Public-choice theorists describe a recurring pattern where regulatory agencies, over time, come to serve the very industries they were created to regulate. What is this pattern called?",
    "Regulatory capture, when the watchdog ends up working for the watched",
    [
        "Pareto improvement, the technical term for a win-win economic change",
        "Coase bargaining, the way private parties settle externality problems",
        "Walrasian equilibrium, the standard theoretical market-clearing model",
    ],
    "George Stigler's 1971 paper 'The Theory of Economic Regulation' formalized regulatory capture, but the public-choice framing made it canonical. Banks capture banking regulators; pharmaceutical firms capture the FDA; broadcasters capture the FCC. The revolving door is the mechanism.")

q(1, "tullock_political_failure",
    "Once Buchanan and Tullock's public-choice analysis shows politicians and bureaucrats are self-interested, an older argument collapses. Which familiar political argument no longer works automatically?",
    "Market failure means government must step in and solve the problem",
    [
        "Voluntary trade between two consenting parties benefits both of them",
        "Free markets coordinate millions of strangers through price signals",
        "Adam Smith argued the division of labor increases overall productivity",
    ],
    "Once politics is self-interested, the 'market failure → government fix' argument collapses. You must compare imperfect markets to imperfect governments. Public choice shows the government side often performs worse — capture, rent-seeking, electoral cycles distort outcomes.")

# --- Bastiat (8) ---

q(1, "bastiat_1850_law",
    "The French economist Frederic Bastiat died in December 1850 at age 49 from tuberculosis, having published his most famous pamphlet that same year. The pamphlet defended individual rights against state plunder. What was it titled?",
    "The Law, his short 1850 pamphlet on rights and the state",
    [
        "Wealth of Nations, the Adam Smith classic from way back in 1776",
        "The Communist Manifesto, by Marx and Engels in February 1848",
        "Das Kapital, the volume one of Karl Marx published in 1867",
    ],
    "Bastiat's 'La Loi' ('The Law,' 1850) is one of the clearest popular defenses of property rights ever written. The state, Bastiat argues, exists to defend life, liberty, and property — not to redistribute. 'Legal plunder' (welfare, subsidies, tariffs) corrupts the law's purpose.")

q(1, "bastiat_seen_unseen",
    "In 1850 Frederic Bastiat published a short essay distinguishing what economic policies visibly accomplish from what they invisibly cost. The essay opens with a broken window in a shop. What is the title?",
    "That Which Is Seen and That Which Is Not Seen, his 1850 essay",
    [
        "The Wealth of Nations, the founding Adam Smith book of 1776",
        "The General Theory, the famous Keynesian work of the year 1936",
        "The Road to Serfdom, the famous Hayek book of the year 1944",
    ],
    "Bastiat's 'Ce qu'on voit et ce qu'on ne voit pas' (1850) is the foundational lesson of folk economics. Twelve short examples (broken window, demobilized soldier, taxes, subsidies, intermediaries, trade restrictions) each contrast the visible benefit with the hidden cost. The method underlies all serious economic reasoning.")

q(1, "bastiat_broken_window_fallacy",
    "Frederic Bastiat in 1850 imagined a shopkeeper whose son smashed a pane. A bystander said 'good — now the glazier gets work and buys bread!' What did Bastiat say the bystander missed?",
    "What the shopkeeper would have bought instead with that money",
    [
        "How much the glazier was charging the shopkeeper for the work",
        "Whether the glazier was a relative of the careless little boy",
        "How long the shopkeeper had to wait for the new glass installed",
    ],
    "Bastiat's broken-window fallacy is the foundational seen-and-unseen example. The glazier's work (seen) is paid for by what the shopkeeper would have bought otherwise (unseen). Destruction is never net wealth-creation; the unseen cost is real. Keynesian 'stimulus' arguments often replay this fallacy.")

q(1, "bastiat_candle_makers_1845",
    "In 1845 Frederic Bastiat wrote a satirical petition from French candle-makers complaining about unfair foreign competition from a rival lighting source and asking government to block it. What was the rival source?",
    "The Sun, whose free light Bastiat said should be blocked by law",
    [
        "Whale oil, the standard lamp fuel imported from American whalers",
        "Coal gas, the standard street-lighting fuel of British cities",
        "Petroleum oil, then beginning to be refined in the American West",
    ],
    "Bastiat's 'Petition of the Candle Makers' (1845) asks Parliament to require closing all shutters, blinds, and windows to block sunlight, so candle-makers can compete fairly. The satire skewers protectionist tariff arguments by extending them to their absurd conclusion.")

q(1, "bastiat_negative_railway",
    "Frederic Bastiat once mocked a politician who proposed deliberately breaking a long railway line at every town to force travelers to stop, eat, sleep, and spend money. What did Bastiat call this idea?",
    "The Negative Railway, where every break creates new local jobs",
    [
        "The Positive Tariff, the proper way to protect industry from imports",
        "The Forward Plan, the polite name for government spending stimulus",
        "The General Pause, the polite name for shutting down trade entirely",
    ],
    "Bastiat's 'negative railway' satire mocks the protectionist logic that obstacles create wealth. A railway works because it eliminates obstacles; deliberately adding obstacles destroys value. Modern stimulus rhetoric ('breaking windows boosts spending') often replays the same error.")

q(1, "bastiat_economic_sophisms",
    "Beyond the broken-window essay, Frederic Bastiat published two volumes of short pieces in 1845 and 1848 demolishing popular fallacies about trade, money, and labor. What did he title the series?",
    "Economic Sophisms, his 1845-1848 series of folk-economics critiques",
    [
        "The Wealth of Nations, the famous Adam Smith book of 1776",
        "Principles of Economics, the founding Menger work of 1871",
        "Capitalism and Freedom, the Milton Friedman classic of 1962",
    ],
    "Bastiat's 'Sophismes Economiques' (1845 + 1848) is the great folk-economics-demolition project. Each chapter takes a familiar protectionist or interventionist argument and dismantles it cleanly. Murray Rothbard called Bastiat 'the greatest writer of economic journalism in human history.'")

q(1, "bastiat_legal_plunder",
    "Frederic Bastiat in his 1850 pamphlet The Law described the moment when the legal system itself becomes a tool for taking from some to give to others. What did he call this perversion?",
    "Legal plunder, when the state takes by law what would be theft otherwise",
    [
        "Honest taxation, the proper means of funding necessary government",
        "Voluntary exchange, the basis of all mutually beneficial trade",
        "Spontaneous order, the way markets coordinate without planning",
    ],
    "Bastiat's 'legal plunder' is the law as instrument of redistribution: 'See if the law takes from some persons what belongs to them, and gives it to other persons to whom it does not belong.' Welfare, tariffs, subsidies, and farm price supports all fit Bastiat's criterion.")

q(1, "bastiat_state_definition",
    "Frederic Bastiat summarized in one line the political fantasy he saw spreading in 1848 Paris. The line defines what the state had become for his contemporaries. What was Bastiat's definition?",
    "That great fiction by which everyone tries to live at others' expense",
    [
        "A wise neutral arbiter resolving disputes between citizens fairly",
        "The collective will of the people expressed through their legislators",
        "A benevolent expert body managing questions outside party politics",
    ],
    "Bastiat's 'l'Etat, c'est la grande fiction a travers laquelle tout le monde s'efforce de vivre aux depens de tout le monde' (1848) is one of the most-quoted lines in classical liberalism. Public choice theory (Buchanan-Tullock 1962) is the formal economic statement of Bastiat's insight.")

# --- Coase (4) ---

q(1, "coase_1960_social_cost",
    "In 1960 the British economist Ronald Coase published a paper overturning the standard treatment of negative externalities like factory pollution. He argued property rights matter more than government taxes. What is the paper called?",
    "The Problem of Social Cost, his 1960 externality paper",
    [
        "The Use of Knowledge in Society, the famous Hayek paper of 1945",
        "The Calculus of Consent, the Buchanan and Tullock book of 1962",
        "Economic Calculation, the famous founding Mises essay of 1920",
    ],
    "Coase's 'The Problem of Social Cost' (1960, Journal of Law and Economics) is the most-cited economics paper ever published. His insight: with clear property rights and low transaction costs, private parties can bargain to efficient solutions for externalities without government intervention.")

q(1, "coase_theorem_property",
    "Ronald Coase's 1960 paper showed that with clear property rights and low transaction costs, two parties facing pollution will negotiate the same efficient outcome no matter who holds the right. What is this called?",
    "The Coase theorem, his property-rights resolution of externalities",
    [
        "The Pareto improvement, the technical term for win-win change",
        "The Walrasian equilibrium, the standard general-equilibrium concept",
        "The Nash equilibrium, the famous game-theoretic stability concept",
    ],
    "The Coase theorem: under clear property rights and low transaction costs, externalities resolve efficiently through private bargaining. The textbook example: cattle rancher and corn farmer settle a fence dispute by trading rights — no Pigouvian tax needed. The key Austrian-friendly conclusion: define rights, then trade.")

q(1, "coase_1991_nobel",
    "Ronald Coase won the Nobel Prize in Economics for his work on property rights, transaction costs, and the firm. In what year?",
    "1991, late in his life at age eighty-one",
    [
        "1971, just before Nixon ended the gold standard",
        "1951, decades earlier as he was just establishing himself",
        "2001, very near the end of his long career at Chicago",
    ],
    "Coase won the 1991 Nobel 'for his discovery and clarification of the significance of transaction costs and property rights for the institutional structure and functioning of the economy.' He published 'The Nature of the Firm' in 1937 and 'The Problem of Social Cost' in 1960 — patient work rewarded decades later.")

q(1, "coase_nature_of_the_firm",
    "Ronald Coase's first famous paper, written as an undergraduate visiting the US, asked a basic question economists had ignored: why do firms exist at all, instead of every transaction being market-based? What was the 1937 paper called?",
    "The Nature of the Firm, his 1937 transaction-cost paper",
    [
        "The General Theory, the famous Keynesian work of the year 1936",
        "Principles of Economics, the founding Menger work of 1871",
        "The Wealth of Nations, the founding Adam Smith work of 1776",
    ],
    "Coase's 'The Nature of the Firm' (Economica, 1937) argued firms exist because using markets has transaction costs — finding prices, negotiating contracts, enforcing terms. Inside a firm, you give orders. The boundary between firm and market is set where transaction costs equal management costs.")

# --- Adam Smith and Ricardo (4) ---

q(1, "smith_1776_wealth_nations",
    "In 1776, the same year America declared independence, a Scottish moral philosopher published a thousand-page book founding modern economics. What was the book called?",
    "An Inquiry into the Nature and Causes of the Wealth of Nations",
    [
        "Principles of Economics, the founding Carl Menger book of 1871",
        "Capitalism and Freedom, the Milton Friedman classic from 1962",
        "Das Kapital, the volume one of Karl Marx published in 1867",
    ],
    "Adam Smith's 'Wealth of Nations' (1776) is the founding work of classical economics. The Austrian school built on Smith but corrected him (subjective value instead of labor theory; entrepreneurial discovery instead of equilibrium). Smith remains a vital ancestor of free-market thought.")

q(1, "smith_pin_factory_division",
    "Adam Smith's opening chapter of Wealth of Nations (1776) described eighteen trades involved in making a pin. One worker alone barely made a pin a day; ten working together made thousands. What principle was Smith illustrating?",
    "The division of labor, which dramatically raises productivity",
    [
        "The labor theory of value, which says cost equals labor hours",
        "Marginal utility, the value of one more unit at the margin",
        "The Coase theorem, on resolving externalities by private bargain",
    ],
    "Smith's pin factory shows how specialization (one worker draws the wire, one cuts it, one points it...) multiplies output. The Wealth of Nations opens with this example because Smith saw the division of labor — enabled by trade and markets — as the foundation of national prosperity.")

q(1, "ricardo_1817_comparative_advantage",
    "In 1817 the English economist David Ricardo wrote about Portugal and England trading wine and cloth. Even when Portugal made both more efficiently, both gained by specializing. What did Ricardo establish?",
    "Comparative advantage, where trade benefits both even if one is better",
    [
        "Absolute advantage, where trade benefits only the cheaper producer",
        "Mercantilism, the doctrine that one country gains when another loses",
        "The labor theory, where value equals labor hours embodied in goods",
    ],
    "Ricardo's 'On the Principles of Political Economy and Taxation' (1817) introduced comparative advantage. Even if Portugal is better at both wine AND cloth, opportunity cost matters: each country specializes in what it gives up the least to produce, then trades. The case for free trade.")

q(1, "ricardo_corn_laws_repeal",
    "David Ricardo's economic arguments became the intellectual basis for repealing Britain's tariffs on imported grain. Despite landowner opposition, Parliament repealed the tariffs in 1846. What were the tariffs called?",
    "The Corn Laws, which kept grain expensive to protect landowners",
    [
        "The Stamp Act, the colonial tax that helped trigger the Revolution",
        "The Tariff of Abominations, the 1828 American protective tariff",
        "The Smoot-Hawley Tariff, the disastrous American tariff of 1930",
    ],
    "Britain's Corn Laws (1815-1846) protected domestic landowners by taxing imported grain, raising bread prices for workers. Ricardo's comparative-advantage argument armed the Anti-Corn-Law League (Cobden, Bright) intellectually. Prime Minister Peel repealed them in 1846 — a major free-trade victory.")

# --- Core Austrian concepts (5) ---

q(1, "subjective_value_concept",
    "The Austrian school is built on a foundational idea about where economic value comes from. Two people facing the same apple don't necessarily value it the same. What is this concept called?",
    "Subjective value, where each individual ranks goods by personal goals",
    [
        "Objective value, where each good has an inherent worth set by science",
        "Labor value, where each good's value equals labor hours used up",
        "Cost value, where each good's value equals the historical cost of production",
    ],
    "Subjective value (Menger 1871) is the Austrian school's foundational move. There's no 'value' in a thing waiting to be measured; value lives in the mind of an individual ranking that thing against alternatives. The diamond-water paradox dissolves because each person ranks differently.")

q(1, "time_preference_interest",
    "Austrian capital theory rests on a basic fact about human choice: when offered a thousand dollars today versus a thousand a year from now, most people pick today. What is this preference called?",
    "Time preference, the reason interest exists at all",
    [
        "Risk aversion, the standard preference for certainty over gambles",
        "Loss aversion, the behavioral pattern of preferring not to lose",
        "Discounting bias, the irrational tendency to ignore the future",
    ],
    "Time preference (Bohm-Bawerk 1884) is the foundation of Austrian interest theory. Interest is the price of time. Higher time preference (impatience) means higher rates. The interest rate signals how much consumers value present versus future goods — distorting it (Fed at 1%) causes ABCT-style cycles.")

q(1, "capital_structure_concept",
    "Austrian economists stress that 'capital' is not one big aggregate (K in textbooks). Steel, drill presses, half-finished cars, and lumber are not interchangeable. What is the Austrian concept?",
    "The structure of capital, with heterogeneous stages of production",
    [
        "The aggregate of capital, where K is a single homogeneous quantity",
        "The stock of capital, measured in dollars across the whole economy",
        "The flow of capital, measured as one-year inputs into production",
    ],
    "Austrian capital theory (Bohm-Bawerk, Hayek's Prices and Production 1931) treats capital as a structured, time-staged process. Cheap credit can lengthen the structure (boom in higher-order goods) until rates rise and the structure can't be completed (bust). This is the engine of ABCT.")

q(1, "entrepreneur_discovery",
    "Israel Kirzner's contribution to Austrian thought (especially his 1973 book) emphasized one specific role in markets that mainstream economics had ignored. What role did Kirzner highlight?",
    "The entrepreneur, who notices profit opportunities others missed",
    [
        "The bureaucrat, who fairly administers regulations across markets",
        "The central planner, who allocates resources for the whole economy",
        "The labor union, which negotiates wages above the market clearing level",
    ],
    "Kirzner's 'Competition and Entrepreneurship' (1973) extended Mises's emphasis on the entrepreneur as discoverer of profit opportunities. Mainstream models assume equilibrium with all profit opportunities already exhausted. Real markets are constantly disequilibrium being closed by entrepreneurial alertness.")

q(1, "praxeology_method",
    "Ludwig von Mises in Human Action (1949) named the method by which Austrian economics derives its conclusions from a single starting point: the fact that humans act purposefully to achieve goals. What is this method called?",
    "Praxeology, the deductive logic of human action",
    [
        "Econometrics, the standard statistical-modeling approach to economics",
        "Behavioral economics, the standard psychology-influenced approach",
        "Mathematical economics, the standard equation-based modeling method",
    ],
    "Praxeology (Greek 'praxis' = action) is Mises's method: starting from the axiom 'humans act,' deduce economic propositions logically. Demand curves slope down because choice ranks ends. The method is a priori, not empirical — closer to geometry than to physics.")

q(1, "mises_1912_money_credit",
    "Before his 1920 calculation essay, Ludwig von Mises wrote a young economist's book on monetary theory in 1912. The work introduced the regression theorem and an early version of business cycle theory. What was the book titled?",
    "The Theory of Money and Credit, his 1912 monetary treatise",
    [
        "Wealth of Nations, the founding Adam Smith book of 1776 era",
        "The General Theory, the famous Keynesian work of the year 1936",
        "Principles of Economics, the founding Carl Menger work of 1871",
    ],
    "Mises's 'Theorie des Geldes und der Umlaufsmittel' (1912; English 1934) applied Mengerian marginal utility to money. The regression theorem traces money's exchange value back through history to a commodity origin. The book contained the first statement of what became Austrian Business Cycle Theory (developed further by Hayek in 1931).")

# ============================================================================
# PILLAR 2 — BITCOIN (60 questions)
# ============================================================================

# --- Cypherpunk predecessors (8) ---

q(2, "hashcash_1997_adam_back",
    "In 1997 a British cryptographer named Adam Back invented a proof-of-work system to fight email spam. Each email had to compute a small puzzle that cost the sender time but cost the receiver almost nothing to check. What did Back call this?",
    "Hashcash, his 1997 proof-of-work anti-spam system",
    [
        "Bitcoin, the much later digital cash system from October 2008",
        "PGP, the famous Zimmermann encryption tool released in 1991",
        "DigiCash, the Chaum digital-cash startup founded in 1989",
    ],
    "Adam Back's Hashcash (1997) was one of Bitcoin's direct technical ancestors. Satoshi's 2008 white paper cites Hashcash for proof-of-work. The basic idea: require a small computational cost to send a message, making mass spam expensive but legitimate use cheap.")

q(2, "wei_dai_b_money_1998",
    "In 1998 the cryptographer Wei Dai posted a proposal to the cypherpunks mailing list describing 'a scheme for a group of untraceable digital pseudonyms to pay each other with money.' What did Dai call the scheme?",
    "b-money, his 1998 proposal for decentralized digital cash",
    [
        "Bitcoin, the actual digital-cash system invented a decade later",
        "Bit gold, the Nick Szabo proposal from much later, in 2005",
        "Hashcash, the Adam Back proof-of-work system from 1997",
    ],
    "Wei Dai's 'b-money' (1998) is named in the opening citation of Satoshi's 2008 white paper. The scheme proposed a broadcast network where servers maintained balances. It never launched, but the design pointed straight at Bitcoin a decade later.")

q(2, "szabo_bit_gold_2005",
    "In 2005 the legal scholar and cryptographer Nick Szabo published a proposal for unforgeable, scarce digital tokens generated by solving cryptographic puzzles. What did Szabo call his proposal?",
    "Bit gold, his 2005 proposal for proof-of-work digital scarcity",
    [
        "Bitcoin, the very similar digital cash system launched in 2009",
        "b-money, the earlier Wei Dai proposal from 1998 cypherpunks list",
        "DigiCash, the earlier Chaum company founded back in 1989",
    ],
    "Szabo's 'bit gold' (2005 blog post) proposed timestamped proof-of-work chains that would create scarce digital tokens. The similarities to Bitcoin are striking enough that some have speculated Szabo IS Satoshi (he denies it). Bit gold never launched; Bitcoin three years later did.")

q(2, "cypherpunks_mailing_list_1992",
    "A mailing list founded in 1992 by Eric Hughes, Tim May, and John Gilmore became the home for cryptography activists. Members took a name combining cyber and a famous outlaw aesthetic. What were they called?",
    "Cypherpunks, founded as a private mailing list in 1992",
    [
        "Hackers, the older general term for computer enthusiasts overall",
        "Crackers, the term for those who broke into computer systems then",
        "Phreakers, the term for those who broke into phone systems then",
    ],
    "The cypherpunks list (1992-2010s) was the proving ground for cryptographic ideas Bitcoin would use. Members included Hal Finney, Adam Back, Wei Dai, Nick Szabo, Julian Assange, Phil Zimmermann, and (under a pseudonym) Satoshi Nakamoto. The 'cypher' is cipher; the 'punk' is the DIY anti-authoritarian ethic.")

q(2, "zimmermann_pgp_1991",
    "In 1991 the American programmer Phil Zimmermann released free email-encryption software to defeat government surveillance. The US government investigated him for arms export violations from 1993 to 1996. What did Zimmermann call his software?",
    "PGP, standing for Pretty Good Privacy",
    [
        "PKI, standing for Public Key Infrastructure",
        "SSL, standing for Secure Sockets Layer protocol",
        "SSH, standing for Secure Shell remote-login protocol",
    ],
    "Phil Zimmermann's PGP (1991) put strong public-key cryptography in ordinary users' hands. The Clinton-era US government investigated him for 'munitions export' (cryptography was classified as a weapon). The case dropped in 1996; PGP became standard. The cypherpunk lineage runs straight from Zimmermann to Satoshi.")

q(2, "cypherpunk_manifesto_1993",
    "In 1993 Eric Hughes published a short manifesto on the cypherpunks list that became the movement's defining document. The opening line said privacy was necessary for an open society in the electronic age. What was the document called?",
    "A Cypherpunk's Manifesto, by Eric Hughes in March 1993",
    [
        "The Communist Manifesto, the founding Marx-Engels text of 1848",
        "The Crypto Anarchist Manifesto, by Tim May in 1988",
        "The Declaration of Independence of Cyberspace, by Barlow in 1996",
    ],
    "Hughes's 1993 manifesto: 'Privacy is necessary for an open society in the electronic age... We cannot expect governments, corporations, or other large, faceless organizations to grant us privacy out of their beneficence. We must defend our own privacy if we expect to have any.' The Bitcoin ethos starts here.")

q(2, "sha256_hash_function",
    "Bitcoin uses a specific cryptographic hash function, designed by the US National Security Agency and published in 2001, to secure its blockchain. The function takes any input and produces a fixed-length 256-bit fingerprint. What is the function called?",
    "SHA-256, the Secure Hash Algorithm published in 2001",
    [
        "MD5, the older Rivest-designed hash function from 1991",
        "AES, the Advanced Encryption Standard published in 2001",
        "RSA, the Rivest-Shamir-Adleman public-key system of 1977",
    ],
    "SHA-256 (Secure Hash Algorithm, 256-bit) is the workhorse of Bitcoin. Each block's header is hashed by SHA-256; mining means finding an input whose SHA-256 output has enough leading zeros. The NSA-designed function has resisted attack for over two decades — Bitcoin's security stands on it.")

q(2, "proof_of_work_purpose",
    "Bitcoin requires miners to compute a costly cryptographic puzzle to add new blocks. The puzzle is asymmetric: hard to solve, easy to verify. Why does Bitcoin demand this 'wasteful' work?",
    "To make rewriting history expensive, securing the chain against attackers",
    [
        "To consume electricity for environmental reasons unrelated to the chain",
        "To raise the price of bitcoin by making each token harder to mine",
        "To enrich miners by giving them work nobody else can perform online",
    ],
    "Proof-of-work makes attacking Bitcoin economically irrational. To rewrite history, an attacker must outwork the rest of the network — currently requiring billions of dollars in electricity and hardware. The 'wasted' energy is the cost of buying credibly-neutral, tamper-evident global consensus.")

# --- Satoshi white paper + Genesis (8) ---

q(2, "satoshi_halloween_2008_paper",
    "On October 31, 2008, an anonymous person calling themselves Satoshi Nakamoto posted a nine-page paper to a small cryptography mailing list. What was the paper titled?",
    "Bitcoin, A Peer-to-Peer Electronic Cash System",
    [
        "Web 3.0, A Decentralized Internet for the Next Generation",
        "Smart Contracts, the New Way to Trade Online Securely",
        "Cryptography Today, A Survey of Modern Methods in Detail",
    ],
    "Satoshi's 2008 white paper was posted to the metzdowd.com cryptography list on Halloween 2008. Nine pages. No PhD pedigree, no institutional affiliation. The paper described how to solve the double-spend problem without a central authority — Bitcoin's founding document.")

q(2, "satoshi_metzdowd_cryptography_list",
    "Satoshi Nakamoto did not publish his October 2008 white paper in an academic journal or at a conference. He posted it to a small mailing list where cypherpunks discussed cryptography. What was the list?",
    "The metzdowd.com cryptography mailing list, on Halloween 2008",
    [
        "The New York Times technology section, online version that year",
        "Slashdot, the major tech-news aggregator of the late 2000s",
        "The MIT computer-science department mailing list internally",
    ],
    "Satoshi posted the white paper to the metzdowd.com 'Cryptography' list (run by Perry Metzger). The first replies were polite but skeptical — most respondents thought the project would fail. James Donald's first response highlighted scaling concerns Bitcoin still wrestles with today.")

q(2, "genesis_block_january_3_2009",
    "The first block of the Bitcoin blockchain was mined by Satoshi himself, kicking off the network. The block contains a hidden message in its coinbase field. When was the Genesis block mined?",
    "January 3, 2009, by Satoshi himself with the embedded Times headline",
    [
        "October 31, 2008, the same day the Bitcoin white paper appeared online",
        "December 31, 2008, on New Year's Eve before the millennium decade ended",
        "May 22, 2010, the same day as the first commercial Bitcoin transaction",
    ],
    "The Genesis block (block 0) was mined on January 3, 2009. Its embedded coinbase message ('The Times 03/Jan/2009 Chancellor on brink of second bailout for banks') timestamps the chain and signals Bitcoin's purpose. The 50 BTC reward is provably unspendable — no one ever has private key for the Genesis output.")

q(2, "genesis_times_headline_embedded",
    "The Bitcoin Genesis block's coinbase field contains a 50-byte text message. Satoshi chose a specific London newspaper headline from the day before the block. What did the embedded message say?",
    "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks",
    [
        "The Sun 03/Jan/2009 Bitcoin launches today as digital cash everywhere",
        "The Guardian 03/Jan/2009 Brown announces new printing press for pounds",
        "The Daily Mail 03/Jan/2009 Massive run on banks expected this weekend",
    ],
    "The Times of London headline (03/Jan/2009, page 1) was about Alistair Darling considering a second bailout for British banks. Satoshi embedded it in the Genesis block to timestamp the chain AND to comment on the bank-bailout context Bitcoin was designed to make unnecessary. The message is unforgeable: you can't pre-mine a headline.")

q(2, "genesis_unspendable_50_btc",
    "The Bitcoin Genesis block mined January 3, 2009 carries a 50 BTC reward. Unlike every later block, no one can ever spend those 50 coins. Why?",
    "Satoshi never added the Genesis output to the chain's spendable database",
    [
        "Satoshi lost the private key to the Genesis address very soon after launch",
        "The protocol explicitly bans spending Block-zero outputs forever from launch",
        "The Genesis coins were burned by the network on their first anniversary in 2010",
    ],
    "The Genesis block's 50 BTC are provably unspendable due to a quirk in early Bitcoin code: the Genesis output never appears in the UTXO set, the database tracking spendable coins. Whether bug or feature, the result is the same — no founder gets free coins from block zero. The supply curve is provably accurate from day one.")

q(2, "hal_finney_first_recipient",
    "Eleven days after Bitcoin launched, on January 12, 2009, Satoshi sent the first-ever person-to-person Bitcoin transfer. Who was the recipient who received those 10 BTC in block 170?",
    "Hal Finney, a cypherpunk and PGP developer at PGP Corporation",
    [
        "Adam Back, the British inventor of Hashcash back in 1997",
        "Nick Szabo, the legal scholar who proposed Bit gold in 2005",
        "Wei Dai, the cryptographer who proposed b-money in 1998",
    ],
    "Hal Finney was the second person to run the Bitcoin software. Satoshi sent him 10 BTC on January 12, 2009 (block 170) — the first transaction. Finney was diagnosed with ALS later that year and died in 2014. His final tweet from August 2013 was 'Running bitcoin' from many years earlier.")

q(2, "satoshi_disappeared_2010",
    "After about two years of active development and forum posting, Satoshi Nakamoto handed control of the Bitcoin code to Gavin Andresen and disappeared. About when did Satoshi vanish?",
    "Around April 2011, with a final email saying he had moved on to other things",
    [
        "Around January 2009, immediately after launching the Genesis block",
        "Around January 2017, after Bitcoin's first big run to 1000 dollars",
        "Around November 2022, immediately after the collapse of FTX exchange",
    ],
    "Satoshi's last forum post was December 12, 2010; his final emails to Gavin Andresen and Mike Hearn came in April 2011. The final email: 'I've moved on to other things. It's in good hands with Gavin and everyone.' Satoshi held over 1 million BTC; none have ever been spent. The identity remains unknown.")

q(2, "satoshi_identity_unknown",
    "The person behind the pseudonym Satoshi Nakamoto has never been identified. Many candidates have been proposed and denied (Finney, Szabo, Back, Wright). What is the verified state of Satoshi's identity?",
    "Unknown, and likely to remain unknown by Satoshi's deliberate design",
    [
        "Confirmed as Hal Finney, who admitted it before dying in 2014 from ALS",
        "Confirmed as Craig Wright, by a UK court ruling in spring of 2024",
        "Confirmed as Nick Szabo, by linguistic analysis of mailing-list posts",
    ],
    "Satoshi's identity remains unknown. The 2024 UK COPA v. Wright ruling explicitly found Craig Wright is NOT Satoshi (he had been claiming to be). The mystery is by design: Bitcoin's neutrality requires no founder-figure to capture. As long as the coins don't move, the design holds.")

# --- Pizza Day + early commerce (4) ---

q(2, "pizza_day_may_22_2010",
    "On May 22, 2010, the Florida programmer Laszlo Hanyecz paid 10,000 BTC for two Papa John's pizzas. It was the first known real-world commercial Bitcoin transaction. What is this date now called?",
    "Bitcoin Pizza Day, celebrated every May 22 by the Bitcoin community",
    [
        "Bitcoin Genesis Day, the anniversary of the very first block ever mined",
        "Bitcoin Halving Day, the anniversary of the first miner reward halving",
        "Bitcoin Whitepaper Day, celebrating the very first technical document",
    ],
    "Bitcoin Pizza Day (May 22, 2010) commemorates Laszlo's 10,000 BTC trade for two pizzas — about $41 worth of pizza at the time. At the November 2021 peak ($69K), those 10,000 BTC were worth ~$690 million. The story is the canonical 'first real-world Bitcoin transaction' anecdote.")

q(2, "pizza_10000_btc_value",
    "On May 22, 2010, Laszlo Hanyecz paid 10,000 BTC for two pizzas worth about 41 dollars. Bitcoin's price has risen substantially since then. At Bitcoin's November 2021 all-time high of about $69,000, what were those 10,000 BTC worth?",
    "Around 690 million dollars, an enormous valuation",
    [
        "Around 690 thousand dollars, much less impressive than 690 million",
        "Around 69 million dollars, much less impressive than 690 million",
        "Around 6.9 billion dollars, much more than the actual peak value",
    ],
    "At Bitcoin's November 2021 ATH of about $69,000, those 10,000 BTC were worth around $690 million. Laszlo has said he doesn't regret the trade — he was paying to demonstrate Bitcoin could be used as money at all. Without him, somebody else would have done the first commerce.")

q(2, "silk_road_marketplace",
    "From 2011 through 2013, Bitcoin's main public use was a dark-web marketplace called Silk Road, run by Ross Ulbricht (aka 'Dread Pirate Roberts'). What did the FBI do in October 2013?",
    "Seized the site and arrested Ulbricht in a San Francisco public library",
    [
        "Bought all available bitcoin from the site and recovered customer money",
        "Negotiated with Ulbricht to allow Silk Road to continue under regulation",
        "Forced Bitcoin's developers to delete the marketplace from the network",
    ],
    "FBI agents arrested Ross Ulbricht in San Francisco's Glen Park library on October 1, 2013, with his laptop open and logged in as Dread Pirate Roberts. Ulbricht received life without parole in 2015 (Trump pardoned him January 2025). The case is part of Bitcoin's history but doesn't define it.")

q(2, "first_bitcoin_exchange",
    "Bitcoin needed exchanges so people could trade dollars and other currencies for BTC. The first major exchange launched in 2010 and grew from a card-trading site. What was the exchange called?",
    "Mt. Gox, originally an online card-trading platform",
    [
        "Coinbase, the major American exchange founded much later in the year 2012",
        "Binance, the major Chinese exchange founded years later in 2017",
        "Kraken, the major American exchange founded years later in 2011",
    ],
    "Mt. Gox ('Magic: The Gathering Online Exchange') started as a card-trading site, was bought by Jed McCaleb in 2007, and pivoted to Bitcoin in 2010. By 2013 Mt. Gox handled about 70% of all Bitcoin transactions. It collapsed February 2014, losing 850,000 BTC — the canonical 'not your keys, not your coins' lesson.")

# --- Mt. Gox + exchange custody risk (4) ---

q(2, "mt_gox_collapse_feb_2014",
    "In February 2014 the world's largest Bitcoin exchange suspended withdrawals and then filed for bankruptcy. About how many bitcoin had it lost over time?",
    "About 850,000 BTC, lost over years to theft and mismanagement",
    [
        "About 8,500 BTC, a minor loss for the exchange operationally",
        "About 85 BTC, a barely noticeable accounting error",
        "About 8.5 million BTC, more BTC than have ever existed in total supply",
    ],
    "Mt. Gox collapsed in February 2014 after losing approximately 850,000 BTC (then ~$450M, today billions). Combination of hacks, mismanagement, and possibly insider theft. The bankruptcy proceedings continued for over a decade; partial recovery distributions to customers began in 2024. Founder Mark Karpeles ultimately got a suspended sentence.")

q(2, "not_your_keys_not_your_coins",
    "After Mt. Gox 2014, Quadriga 2019, Celsius 2022, Voyager 2022, BlockFi 2022, and FTX 2022 all collapsed losing customer funds, the Bitcoin community has a popular saying that captures the lesson. What is the saying?",
    "Not your keys, not your coins, meaning self-custody is essential",
    [
        "Buy low, sell high, the universal investment maxim",
        "Trust but verify, the Reagan-era nuclear-arms control catchphrase",
        "Be your own bank, the popular fintech-startup marketing slogan",
    ],
    "'Not your keys, not your coins' is the Bitcoin folk wisdom about exchange custody risk. If a third party (exchange, custodian, lender) holds your private keys, they can lose them, steal them, or be ordered to seize them. Self-custody — holding your own keys — is what Bitcoin was designed to enable.")

q(2, "self_custody_hardware_wallet",
    "Bitcoiners following the 'not your keys' principle store coins themselves rather than on exchanges. The standard tool is a physical device that signs transactions offline. What is it called?",
    "A hardware wallet, a device that holds keys offline and signs transactions",
    [
        "A bank vault, the traditional physical-storage method for gold and cash",
        "A safe deposit box, the bank-rented storage container for valuables",
        "A USB drive, an ordinary storage device that any computer can read",
    ],
    "Hardware wallets (Trezor 2014, Ledger 2014, ColdCard, Foundation Passport) hold the private keys in a secure chip, never exposing them to internet-connected computers. The user signs transactions on the device, then broadcasts them. The standard self-custody tool — a $50-200 alternative to trusting an exchange.")

q(2, "ftx_collapse_nov_2022",
    "On November 8, 2022, the second-largest crypto exchange collapsed after founder Sam Bankman-Fried was caught moving customer funds to his trading firm Alameda Research. About how much was missing?",
    "About 8 billion dollars in customer funds were missing and unaccounted",
    [
        "About 8 million dollars in customer funds, a relatively small problem",
        "About 80 trillion dollars, far more than the total world money supply",
        "About 800 billion dollars, more than the entire crypto market value",
    ],
    "FTX collapsed November 8-11, 2022 after CoinDesk leaked Alameda's balance sheet. About $8 billion in customer funds had been misappropriated. SBF was convicted March 2024 on seven federal counts and sentenced to 25 years. He was a major Democratic donor and prominent 'effective altruism' fundraiser; the case exemplifies exchange-custody risk Bitcoin was designed to eliminate.")

# --- Block-size war + SegWit + Taproot (5) ---

q(2, "block_size_war_2015_2017",
    "From 2015 through 2017, Bitcoin's community fought a major civil war over a technical question: should the 1MB block-size limit be raised to allow more transactions per block? What is this period called?",
    "The Block Size War, the major 2015-2017 governance debate",
    [
        "The Bitcoin Civil War, the term for an unrelated technical dispute",
        "The Halving Crisis, when miners feared the 2016 reward halving badly",
        "The Mt Gox Wars, the period after the February 2014 exchange collapse",
    ],
    "The Block Size War (2015-2017) pitted big-blockers (Roger Ver, Jihan Wu, the New York Agreement) against small-blockers (Adam Back, Wladimir van der Laan, Greg Maxwell). The dispute was settled in August 2017: small-block side won, big-block side hard-forked off as Bitcoin Cash (BCH).")

q(2, "segwit_activation_2017",
    "In August 2017 a major Bitcoin protocol upgrade activated, restructuring how transaction data is stored in blocks and enabling later upgrades like the Lightning Network. What was this upgrade called?",
    "SegWit, short for Segregated Witness, activated August 2017",
    [
        "Taproot, the major later upgrade activated in November of 2021",
        "Schnorr Sigs, the signature scheme deployed years later in 2021",
        "Bitcoin Cash, the contentious fork that split off in August 2017",
    ],
    "SegWit (Segregated Witness, BIP 141) activated at block 481824 on August 24, 2017. It moved signature data outside the main block, effectively raising block capacity. The activation was the small-block victory in the block-size war; the big-block faction forked off as Bitcoin Cash on August 1.")

q(2, "bitcoin_cash_fork_2017",
    "On August 1, 2017, the losing side in Bitcoin's block-size war forked off and created a separate cryptocurrency with larger blocks. What did the forked coin call itself?",
    "Bitcoin Cash, abbreviated BCH, with eight-megabyte blocks",
    [
        "Bitcoin SV, the abbreviation for Satoshi Vision, the much later 2018 fork",
        "Litecoin, the older Charlie Lee silver-to-Bitcoin's-gold coin from 2011",
        "Ethereum, the much larger smart-contract platform launched in 2015",
    ],
    "Bitcoin Cash (BCH) forked from Bitcoin on August 1, 2017 at block 478558. Big-blocker advocates (Roger Ver) claimed BCH was 'the real Bitcoin.' Market judgment over time has been decisive: BCH trades at single-digit percentages of BTC's price. A further BCH split in 2018 produced Bitcoin SV (Craig Wright's fork).")

q(2, "taproot_activation_nov_2021",
    "In November 2021 Bitcoin received its most significant protocol upgrade since SegWit, adding improved signature schemes, better privacy for complex spending conditions, and enabling smarter contracts. What was the upgrade called?",
    "Taproot, activated November 2021 at block 709632",
    [
        "SegWit, the earlier major upgrade from August in the year 2017",
        "Lightning, the second-layer payment protocol launched separately",
        "Ordinals, the inscription protocol introduced in early 2023 instead",
    ],
    "Taproot (BIPs 340, 341, 342) activated November 14, 2021 at block 709632. It introduced Schnorr signatures (replacing ECDSA), Merklized Abstract Syntax Trees (privacy for complex contracts), and Tapscript. Taproot enabled later innovations like Ordinals (early 2023) and improved Lightning capacity.")

q(2, "lightning_network_purpose",
    "Bitcoin's main chain handles only about 7 transactions per second. A second-layer protocol launched on mainnet in 2018 enables instant, cheap, off-chain payments while keeping Bitcoin's security. What is it called?",
    "Lightning Network, the second-layer payment protocol since 2018",
    [
        "Ethereum, the separate smart-contract blockchain since 2015 instead",
        "Stellar, the separate Jed McCaleb payments network from 2014",
        "Polygon, the separate Ethereum scaling network from later, 2019",
    ],
    "Lightning Network (Joseph Poon + Thaddeus Dryja white paper 2016, mainnet 2018) lets users open payment channels and transact instantly off-chain, settling only the opening and closing on the main chain. El Salvador's adoption (2021) and Strike's adoption (2020+) brought Lightning to retail.")

# --- El Salvador + adoption (3) ---

q(2, "el_salvador_legal_tender_2021",
    "On September 7, 2021, a Central American country became the first nation to make Bitcoin official legal tender alongside its existing currency. The president pushed the law through in June 2021. Which country?",
    "El Salvador, with President Nayib Bukele leading the move",
    [
        "Costa Rica, the much larger and more developed neighbor of the same region",
        "Honduras, the smaller and poorer neighbor directly to the north",
        "Guatemala, the larger and more populous neighbor to the northwest",
    ],
    "El Salvador's Bitcoin Law passed June 8, 2021; Bitcoin became legal tender September 7, 2021. President Nayib Bukele led the move. The country uses the US dollar as its main currency; Bitcoin is the second legal currency. The Chivo wallet was launched, then largely abandoned; Bitcoin City and bond plans evolved over time.")

q(2, "bukele_strategic_reserve",
    "President Nayib Bukele of El Salvador began buying Bitcoin for his country's treasury in 2021, often announcing the purchases on Twitter or X. What does El Salvador call its accumulated Bitcoin?",
    "A strategic reserve, used as part of national treasury holdings",
    [
        "A speculative bet, that El Salvador openly acknowledges may fail",
        "A required tax, that El Salvadoran citizens must pay annually",
        "A foreign aid, donated to El Salvador by the United States quietly",
    ],
    "El Salvador's bitcoin holdings (about 6,000+ BTC by 2024) are treated as a strategic reserve. Bukele has been pilloried in Western financial media for the policy. By late 2024, the position was deeply profitable. The IMF pushed back hard on the policy as a condition for loans.")

q(2, "central_african_republic_2022",
    "El Salvador wasn't the only country to make Bitcoin legal tender. In April 2022 a second nation followed — though it later reversed the decision. Which country was the second adopter?",
    "The Central African Republic, briefly legal tender in 2022",
    [
        "Nigeria, the much larger West African economy with many BTC users",
        "Kenya, the East African economy famous for mobile-payment M-Pesa",
        "South Africa, the major continental economy with extensive trading",
    ],
    "The Central African Republic made Bitcoin legal tender in April 2022 under President Faustin-Archange Touadera. The law was reversed in March 2023 under international pressure. CAR was the second country to adopt Bitcoin as legal tender; the first to revoke it.")

# --- Halvings + 21M cap (5) ---

q(2, "halving_schedule_4_years",
    "Bitcoin's block subsidy — the new bitcoin given to miners for each block — is cut in half on a predictable schedule built into the protocol. Roughly how often does this happen?",
    "Roughly every four years, after every 210,000 blocks are mined",
    [
        "Every single year, on the anniversary of the Genesis block in January",
        "Every twenty years, a much longer cycle than four years",
        "Every six months, much more frequently than four years generally",
    ],
    "Bitcoin's halving is built into the protocol. Every 210,000 blocks (~4 years at 10-minute average), the block subsidy halves. Halvings have happened in 2012 (50→25), 2016 (25→12.5), 2020 (12.5→6.25), 2024 (6.25→3.125). The schedule continues until roughly 2140, when the last satoshi is mined.")

q(2, "halving_history_dates",
    "Bitcoin has experienced four block-reward halvings since launch. The first cut the subsidy from 50 BTC to 25 BTC per block. In what year did the first halving occur?",
    "2012, when the reward went from 50 BTC to 25 BTC per block",
    [
        "2009, when Bitcoin first launched in January at the Genesis block",
        "2017, the same year as SegWit was activated on the network",
        "2021, the same year as Taproot was activated on the network",
    ],
    "Halving 1: November 28, 2012 (block 210000, 50→25 BTC). Halving 2: July 9, 2016 (block 420000, 25→12.5). Halving 3: May 11, 2020 (block 630000, 12.5→6.25). Halving 4: April 19, 2024 (block 840000, 6.25→3.125). Each historically preceded an upward price cycle, though correlation is not causation.")

q(2, "21_million_cap_concept",
    "Bitcoin's supply schedule has a famous hard ceiling built into the protocol. No matter how much demand exists, no more than this many bitcoin can ever exist. How many is the cap?",
    "Twenty-one million bitcoin, an absolute hard cap by protocol design",
    [
        "Twenty-one billion bitcoin, a much larger and less famous cap",
        "Two million bitcoin, much smaller than the actual famous cap",
        "Two hundred ten million bitcoin, much larger than the actual cap",
    ],
    "Bitcoin's 21 million cap is mathematical, not policy. The schedule (50 BTC/block, halving every 210K blocks) converges to ~20,999,999.9769 BTC. The last satoshi will be mined around 2140. Changing the cap would require near-unanimous consensus on a hard fork — economically impossible because every holder would oppose dilution.")

q(2, "satoshi_unit_definition",
    "Bitcoin can be divided into smaller units; the smallest unit is named after Bitcoin's anonymous founder. One bitcoin equals 100 million of these tiny units. What is the smallest unit called?",
    "A satoshi, with one bitcoin equaling 100 million satoshis",
    [
        "A wei, the smallest unit on the Ethereum smart-contract platform instead",
        "A bit, which is actually a million satoshis, not the smallest unit",
        "A microbitcoin, which equals one hundred satoshis, not just one",
    ],
    "The satoshi (sat) is Bitcoin's smallest unit. 1 BTC = 100,000,000 satoshis. The unit is named after Satoshi Nakamoto. At a BTC price of $100,000, one satoshi equals $0.001. The granularity ensures Bitcoin can serve commerce even at very high prices per BTC.")

q(2, "halving_2024_event",
    "Bitcoin's fourth halving occurred at block 840,000. The miner reward dropped from 6.25 BTC per block to 3.125 BTC per block. About when did this happen?",
    "April 2024, the most recent halving in Bitcoin's history",
    [
        "April 2020, the previous halving, before the most recent one",
        "April 2016, two halvings before the most recent one",
        "April 2028, projected to be the next future halving",
    ],
    "The fourth halving happened April 19, 2024 at block 840000, dropping subsidy from 6.25 BTC to 3.125 BTC. Halvings historically precede rising price cycles as new supply tightens. By the 2028 halving, daily new supply will be just 450 BTC — less than the daily Bitcoin ETF inflows of 2024.")

# --- Difficulty + 10-min block time (3) ---

q(2, "difficulty_adjustment_2016_blocks",
    "Bitcoin's protocol automatically recalculates how hard the mining puzzle is, to keep blocks coming at a steady average pace. How often does the difficulty adjustment happen?",
    "Every 2016 blocks, which is roughly every two weeks on average",
    [
        "Every block, recalculated continuously by the network instantly each time",
        "Every 100 blocks, much more frequently than the actual two-week period",
        "Every 210,000 blocks, the same schedule as the four-year halvings",
    ],
    "Bitcoin's difficulty adjustment recalibrates every 2016 blocks (about two weeks at the 10-minute target). If hashrate has gone up, blocks came faster than 10 minutes; difficulty rises. If hashrate dropped, blocks came slower; difficulty falls. The adjustment keeps the issuance schedule predictable regardless of miner participation.")

q(2, "ten_minute_block_target",
    "Bitcoin aims to add a new block to its chain at a steady average rate. The interval is short enough for practical use but long enough for global propagation. What is the target block time?",
    "About ten minutes per block on average across the network",
    [
        "About one second per block, far too fast for global network propagation",
        "About one hour per block, far slower than the actual average target time",
        "About one full day per block, far slower than the actual average target",
    ],
    "Bitcoin's 10-minute average block time is a balance: long enough for blocks to propagate to nodes worldwide before the next one is mined (avoiding 'orphan blocks'), short enough for practical confirmations. The difficulty adjustment every 2016 blocks targets this average.")

q(2, "china_mining_ban_may_2021",
    "In May 2021 a major government banned Bitcoin mining. About 50% of global hashrate went offline; blocks slowed; the next difficulty adjustment made the puzzle easier; miners elsewhere filled the gap. Which country?",
    "China, in May 2021, by order of the Beijing government",
    [
        "Russia, which actually expanded its mining industry significantly in 2021",
        "The United States, where mining remained legal nationwide in 2021",
        "Iran, where mining also actually remained legal in 2021 too",
    ],
    "China's May 2021 mining ban was Bitcoin's biggest stress test. Half the hashrate offline; the network kept running; blocks slowed temporarily then resumed pace after the next difficulty adjustment. Mining migrated to the US (now the largest mining country), Kazakhstan, Russia, Canada. Antifragility passed the test.")

# --- Wallets + cold storage (4) ---

q(2, "seed_phrase_12_24_words",
    "Bitcoin wallets back up private keys as a sequence of English words from a 2048-word list. The standard length for serious holders is twelve or twenty-four words. What is this backup sequence called?",
    "A seed phrase, also called a mnemonic phrase, twelve or twenty-four words",
    [
        "An IBAN number, the standard banking identifier code worldwide",
        "A PIN code, four to eight numeric digits like a debit card PIN",
        "A pass phrase, an ordinary English sentence chosen by the user freely",
    ],
    "BIP-39 (Bitcoin Improvement Proposal 39) defines the seed-phrase standard. 12 words = 128-bit security; 24 words = 256-bit security (overkill but standard). The wordlist is fixed; phrase order matters. Backing up the seed (and ONLY the seed) restores any Bitcoin held by that wallet on any compatible device.")

q(2, "cold_storage_concept",
    "Bitcoin self-custody best practice involves keeping the private keys completely offline, away from any internet-connected device. What is this storage approach called?",
    "Cold storage, the term for offline private-key storage methods",
    [
        "Hot storage, where keys are online and accessible to anyone immediately",
        "Custodial storage, where a regulated third party holds the keys for you",
        "Exchange storage, where a major exchange holds the customer's coins",
    ],
    "Cold storage keeps private keys disconnected from the internet. Methods include hardware wallets, air-gapped computers, or paper wallets stored in safes. The hot/cold distinction matters: an online (hot) wallet faces remote attack; cold storage requires physical access. Most large self-custodians use cold storage for the bulk of holdings.")

q(2, "hardware_wallet_devices",
    "The standard tool for Bitcoin self-custody is a dedicated device that signs transactions while keeping private keys in a secure chip. Major brands include Ledger and Trezor. What category is this?",
    "Hardware wallets, dedicated devices for offline transaction signing",
    [
        "Software wallets, ordinary mobile or desktop apps that run on computers",
        "Web wallets, hosted services that run inside a browser like a website",
        "Exchange wallets, third-party services like Coinbase or Binance accounts",
    ],
    "Hardware wallets (Trezor 2014, Ledger 2014, ColdCard, Foundation Passport, BitBox02) are the standard self-custody tool. The device holds the seed and signs transactions; the connected computer never sees the private keys. Cost $50-200 — far cheaper than the lessons of an exchange hack.")

q(2, "not_your_keys_again",
    "Compared to leaving bitcoin on an exchange (Mt Gox 2014, Celsius 2022, FTX 2022), running your own hardware wallet has a key benefit. What is the main advantage?",
    "Nobody else can lose, steal, freeze, or be ordered to seize your bitcoin",
    [
        "Hardware wallets earn interest from staking, unlike exchange-held coins",
        "Hardware wallets get government insurance up to 250,000 dollars per device",
        "Hardware wallets allow trading bitcoin at far better prices than exchanges",
    ],
    "Self-custody removes counterparty risk. With your own hardware wallet, no exchange hack, no exchange bankruptcy, no court order can take your coins. The trade-off: you must protect your seed phrase. Losing the seed = losing the coins; nobody can recover for you. Self-custody requires discipline.")

# --- Real proof-of-work + mining (5) ---

q(2, "miner_block_reward",
    "When a miner successfully adds a new block to the Bitcoin chain, they receive two kinds of rewards combined. What are these two reward sources?",
    "The block subsidy in new bitcoin, plus transaction fees from the block",
    [
        "A fixed government payment in dollars, plus environmental subsidies",
        "Equity in the Bitcoin Foundation, plus voting rights for new proposals",
        "Free electricity from the network, plus a fixed bonus from the protocol",
    ],
    "Miner reward = block subsidy (decreasing per halving) + transaction fees paid by senders. As the subsidy approaches zero (around 2140), fees will become the primary miner incentive. The fee market is already significant after halvings; large fees during 2021 Ordinals spikes demonstrated the fee-only model is viable.")

q(2, "miner_competition_purpose",
    "Many miners compete simultaneously to add the next Bitcoin block. Only one wins each round (about every 10 minutes globally). Why does this competitive structure matter?",
    "It makes any one miner unable to censor or rewrite history alone",
    [
        "It generates jobs for miners, which is the main purpose of the system",
        "It produces heat that warms buildings, the main use case for mining",
        "It uses electricity inefficiently on purpose for fairness reasons alone",
    ],
    "Mining decentralization is the security model. No single miner can choose which transactions to include or rewrite history without controlling more than half the network's hashrate (a '51% attack'). The current network hashrate makes such an attack economically irrational — billions in hardware + electricity for an attack the market would reject.")

q(2, "asic_specialized_hardware",
    "Mining Bitcoin profitably today requires specialized hardware that does nothing but compute SHA-256 hashes very fast. Ordinary CPUs and GPUs are obsolete for Bitcoin mining. What is this hardware called?",
    "ASICs, or Application-Specific Integrated Circuits",
    [
        "GPUs, or Graphics Processing Units, the older mining hardware approach",
        "CPUs, or Central Processing Units, the original computer chips of 2009",
        "FPGAs, or Field-Programmable Gate Arrays, a brief 2011 mining transition",
    ],
    "Bitcoin mining hardware evolution: CPUs (2009-2010), GPUs (2010-2012), FPGAs (2011-2013), then ASICs (2013-present). Modern Bitcoin ASICs do one thing only: SHA-256 hashing, extremely fast and energy-efficient compared to general-purpose chips. Major ASIC makers: Bitmain (China, Antminer), MicroBT (China, Whatsminer).")

q(2, "hashrate_security_concept",
    "Bitcoin's security against attack is measured by the total computing power devoted to mining across the entire network. What is this combined computing power called?",
    "Hashrate, measured in hashes per second across all mining hardware",
    [
        "Throughput, measured in transactions per second on the network",
        "Bandwidth, measured in megabytes per second of network traffic",
        "Latency, measured in milliseconds between distant network nodes",
    ],
    "Bitcoin's network hashrate is the global SHA-256 computation rate, measured in hashes per second (H/s). Current network hashrate exceeds 500 exahashes per second (5×10^20 H/s). To attack the network ('51% attack'), an adversary would need to outwork everyone combined — economically prohibitive at current scale.")

q(2, "energy_use_argument",
    "Critics of Bitcoin sometimes point to its high electricity consumption as a problem. Bitcoin advocates respond with what is the core argument about the energy use?",
    "The energy buys global consensus on money without trusting any institution",
    [
        "Energy use is illusory and Bitcoin actually consumes no electricity at all",
        "Bitcoin runs on solar power exclusively, so the energy use is irrelevant",
        "The argument is dishonest because Bitcoin uses less power than browsing email",
    ],
    "Bitcoin's energy use is real and is the cost of buying credibly-neutral global monetary consensus without trusting any institution. Compared to gold mining (energy-intensive), the banking system (data centers, branches, cars driven to ATMs, currency printing), and gold security, Bitcoin's energy cost is real but defensible — it's the cost of the security model.")

# --- Bitcoin distinct from crypto (3) ---

q(2, "bitcoin_vs_crypto",
    "Bitcoiners often insist Bitcoin is distinct from 'crypto' (the broader cryptocurrency category). What is the key feature that distinguishes Bitcoin from nearly all other cryptocurrencies?",
    "No founder pre-mine and no central foundation controlling the protocol",
    [
        "Bitcoin has a much larger maximum supply than any other cryptocurrency",
        "Bitcoin transactions are completely anonymous compared to all others",
        "Bitcoin has a single CEO who personally manages the entire network",
    ],
    "Bitcoin is distinct: no founder pre-mine (Genesis 50 BTC unspendable), no central foundation, no token sale, no insider allocations. Nearly every other cryptocurrency has founder/team allocations, foundation control, or both. The credibly-neutral fair launch is what makes Bitcoin sound money in a way Ethereum, Solana, and the rest aren't.")

q(2, "ethereum_dao_2016",
    "In June 2016 a smart-contract project on Ethereum was exploited, losing $50 million in Ether. Ethereum's developers responded by hard-forking the chain to reverse the theft. What was the project called?",
    "The DAO, a Decentralized Autonomous Organization, was hacked in 2016",
    [
        "Mt. Gox, the much earlier Bitcoin exchange that collapsed in 2014",
        "FTX, the much later cryptocurrency exchange that collapsed in 2022",
        "Silk Road, the dark-web marketplace seized by the FBI in October 2013",
    ],
    "The DAO hack (June 17, 2016) on Ethereum led to a hard fork July 20, 2016 that 'undid' the theft. The minority that refused to fork became Ethereum Classic (ETC). The episode revealed Ethereum's governance can override contract outcomes — the opposite of Bitcoin's immutability. Bitcoiners cite this as why Bitcoin and 'crypto' are different.")

q(2, "terra_luna_collapse_2022",
    "In May 2022 a major algorithmic stablecoin and its sister token lost essentially all value in a week, wiping out about $60 billion. The system depended on a circular minting scheme. What were the tokens called?",
    "Terra and Luna, the algorithmic stablecoin pair that collapsed",
    [
        "Tether and Ether, the dollar stablecoin and Ethereum native token",
        "Bitcoin and Bitcoin Cash, the original coin and its 2017 hard fork",
        "Solana and Cardano, two large competing smart-contract platforms",
    ],
    "Terra/Luna collapsed May 9-13, 2022, losing about $60 billion. The TerraUSD (UST) algorithmic stablecoin was supposed to maintain a $1 peg via a mint-and-burn relationship with Luna. When confidence broke, a 'death spiral' destroyed both. Founder Do Kwon fled to Montenegro, was eventually extradited. The episode is part of why Bitcoin maximalists distinguish Bitcoin from 'crypto.'")

# --- Additional Bitcoin topics (8) ---

q(2, "bitcoin_first_price_2010",
    "In July 2010 Bitcoin reached parity with the US dollar — one bitcoin equaled one cent for a brief moment, then began to climb. Mt. Gox listed it for trade. About what was Bitcoin's first market price?",
    "About 0.008 dollars per coin in July 2010 on Mt. Gox at launch",
    [
        "About 1000 dollars per coin in 2010, the same as the late-2013 peak",
        "About 100 dollars per coin in 2010, the same as the mid-2013 levels",
        "About 10 dollars per coin in 2010, the same as the early-2012 levels",
    ],
    "Bitcoin's earliest market prices were measured in fractions of a cent. By February 2011 it hit parity with the dollar; April 2011 brought $1. The first major bull market peaked at $32 in June 2011 before crashing to $2. Each cycle has been dramatic.")

q(2, "bitcoin_white_paper_pages",
    "Satoshi Nakamoto's October 2008 white paper that introduced Bitcoin to the world was a remarkably short document for inventing a new monetary system. About how long was the paper?",
    "Nine pages including references and abstract, surprisingly short",
    [
        "Five hundred pages including dense mathematical proofs throughout",
        "One hundred pages of technical specifications for the system",
        "Forty pages, similar in length to the bigger academic papers",
    ],
    "Satoshi's white paper is nine pages including the abstract, eight sections, references, and a single technical diagram. The paper is famously concise — most academic crypto papers run 20-40 pages. Satoshi's clarity may have helped Bitcoin spread; the paper is still the easiest entry point to understanding the protocol.")

q(2, "first_known_btc_purchase_pizza",
    "Before Bitcoin Pizza Day in May 2010, there had been miner-to-miner transfers but no real-world commercial transactions for goods. What did Laszlo Hanyecz buy with 10,000 BTC on May 22, 2010?",
    "Two large pizzas delivered to his Florida home by a fellow Bitcoin user",
    [
        "A new car shipped to him cross-country from another Bitcoin enthusiast",
        "A small house in Florida from a private seller who took the bitcoin",
        "A diamond engagement ring from a jewelry store that accepted bitcoin",
    ],
    "Laszlo's May 22, 2010 trade was for two Papa John's pizzas. He posted on the bitcointalk forum offering 10,000 BTC for two pizzas; a London user named jercos took the deal, ordered the pizzas online, and had them delivered. The transaction is commemorated annually as Bitcoin Pizza Day.")

q(2, "bitcoin_2017_first_peak",
    "Bitcoin had its first major bull run reaching widespread public awareness in late 2017. The price ran from about $1,000 in January 2017 to nearly $20,000 in December. What followed in 2018?",
    "A long bear market that dropped Bitcoin's price to about $3,200",
    [
        "A short pause before the price doubled again the following spring",
        "An immediate run back to new highs by the next January in 2018",
        "A government ban in every G20 country effective in early 2018",
    ],
    "Bitcoin's December 2017 peak of nearly $20K was followed by a brutal 2018 bear market. Price dropped to about $3,200 by December 2018 — roughly 84% from the peak. Bitcoin recovered: $69K peak November 2021, then bear to $16K in 2022, then over $100K by 2024-25. Each cycle higher than the last.")

q(2, "first_bitcoin_etf_jan_2024",
    "In January 2024 the US SEC approved the first spot Bitcoin exchange-traded funds (ETFs), letting ordinary investors buy Bitcoin exposure through a regular brokerage account. Which firm's filing led the approval announcement?",
    "BlackRock, with iShares Bitcoin Trust receiving approval same day",
    [
        "FTX, which had collapsed back in November 2022 under fraud",
        "Coinbase, which is an exchange rather than a fund issuer",
        "Tesla, which holds Bitcoin on its balance sheet but is not an issuer",
    ],
    "The SEC approved 11 spot Bitcoin ETFs on January 10, 2024, including BlackRock's iShares Bitcoin Trust (IBIT). BlackRock had been pursuing the approval since mid-2023 with a CEO endorsement from Larry Fink. The 2024 ETF inflows reshaped Bitcoin's market structure — ETFs absorbed daily issuance many times over.")

q(2, "michael_saylor_microstrategy_2020",
    "In August 2020 a Nasdaq-listed software company began converting its corporate treasury from cash to Bitcoin, citing dollar debasement. The CEO became a leading public advocate for Bitcoin. Which company?",
    "MicroStrategy, with CEO Michael Saylor leading the conversion",
    [
        "Tesla, with CEO Elon Musk leading a brief Bitcoin treasury experiment",
        "Square, with CEO Jack Dorsey doing a one-time smaller Bitcoin purchase",
        "PayPal, the payments giant that briefly accepted Bitcoin in 2020",
    ],
    "MicroStrategy (renamed simply 'Strategy' in 2025) began buying Bitcoin in August 2020 with an initial $250M purchase. By 2025 the company held over 400,000 BTC, having issued debt and equity specifically to buy more. Michael Saylor became a prominent public spokesperson for Bitcoin as superior corporate treasury reserves.")

q(2, "wei_dai_b_money_citation",
    "Wei Dai's 1998 b-money proposal predates Bitcoin by ten years and is cited in Satoshi's 2008 white paper. The proposal had two versions, one practical and one theoretical. What was the b-money protocol meant to provide?",
    "Anonymous untraceable digital cash backed by computational work",
    [
        "A government-controlled digital currency backed by a Treasury",
        "A bank-issued credit system competing with American Express",
        "An advertising-funded free-payments app for the early-web era",
    ],
    "Wei Dai posted b-money to the cypherpunks mailing list in November 1998. The first version used a global ledger maintained by all servers; the second used a more practical scheme with a select set of servers. Neither launched. Satoshi's 2008 paper cites b-money as a key intellectual ancestor of Bitcoin.")

q(2, "bitcoin_uses_open_source",
    "Bitcoin's software is freely available, anyone can read and modify the source code, and no company owns it. Many developers have contributed over the years. What licensing model does Bitcoin Core use?",
    "Open-source under the MIT License, free to use and modify",
    [
        "Proprietary, owned by the Bitcoin Foundation and tightly licensed",
        "Patent-protected, owned by Satoshi Nakamoto and still enforced",
        "Government-licensed, requiring approval from the US Treasury Department",
    ],
    "Bitcoin Core (the reference Bitcoin software) is released under the MIT License — anyone can use, modify, or redistribute the code. The licensing aligns with Bitcoin's permissionless ethos: no gatekeepers, no central authority. Many alternative implementations exist (Bitcoin Knots, btcd) that interoperate with Bitcoin Core nodes on the same network.")


# ============================================================================
# VALIDATION
# ============================================================================

if __name__ == "__main__":
    pillar_counts = {p: sum(1 for q in QUESTIONS if q.get("_pillar") == p) for p in (1, 2)}
    print(f"Loaded {len(QUESTIONS)} questions across pillars: {pillar_counts}")

    clean = [{k: v for k, v in q.items() if not k.startswith("_")} for q in QUESTIONS]
    dup, ans = build_bank_indices(clean)

    fails = 0
    softs = 0
    surviving = []
    for i, qd in enumerate(clean):
        total = len(qd["question"]) + sum(len(c) for c in qd["choices"])
        r = validate_rewrite("economics", qd, bank=clean, dup_index=dup, answer_index=ans, replace_idx=i)
        if r["verdict"] == "FAIL":
            fails += 1
            orig = QUESTIONS[i]
            qtext = qd["question"][:70].encode("ascii", "replace").decode("ascii")
            print(f"  FAIL #{i} (P{orig.get('_pillar')}, total={total}c): {qtext}")
            for g, reason in r["hard_fails"]:
                print(f"    {g}: {reason[:200]}")
        else:
            if r["verdict"] == "SOFT_WARN":
                softs += 1
            surviving.append(QUESTIONS[i])

    print(f"\n{len(QUESTIONS)} loaded, {fails} hard fails, {softs} soft warns, {len(surviving)} surviving")

    if fails == 0:
        out_questions = [{k: v for k, v in q.items() if not k.startswith("_")} for q in surviving]
        out = {
            "tier": 2,
            "summary": {
                "questions_generated": len(out_questions),
                "by_pillar": {
                    "1": sum(1 for q in surviving if q.get("_pillar") == 1),
                    "2": sum(1 for q in surviving if q.get("_pillar") == 2),
                },
                "voice": "Bastiat Pattern - one scene + named figure + the action/argument. Story-in-stem from day 1. T2 P1 covers Austrian founders (Menger 1871, Mises 1920 calculation, Hayek-Keynes 1931 LSE, Road to Serfdom 1944, 1945 knowledge paper, Rothbard 1962 Man Economy State, Sowell journey, Friedman 1976 Nobel + Free to Choose, Buchanan-Tullock 1962, Coase 1960/1991, Bastiat 1850 Law + Seen/Unseen + 1845 candle-makers, Smith pin factory 1776, Ricardo 1817). T2 P2 covers cypherpunk lineage (Hashcash 1997, b-money 1998, bit gold 2005, PGP 1991, cypherpunk manifesto 1993, SHA-256), Satoshi (Halloween 2008 paper, metzdowd list, Genesis block Jan 3 2009 + Times headline + unspendable 50 BTC, Hal Finney first transfer Jan 12 2009), Pizza Day May 22 2010, Mt Gox collapse Feb 2014 (850K BTC), block-size war 2015-17, SegWit Aug 2017, Bitcoin Cash fork, Taproot Nov 2021, Lightning, El Salvador Sept 7 2021, halvings 2012/16/20/24, 21M cap, satoshi unit, difficulty 2016-block adjust, 10-min target, China ban May 2021, wallets/seed phrase/cold storage/hardware wallets, ASICs, hashrate, Bitcoin-vs-crypto distinction (DAO 2016, Terra/Luna May 2022, FTX Nov 2022).",
                "constraints": {
                    "char_cap": "stem + 4 choices <= 480 (grace 504); asserted <= 475 build-time",
                    "length_parity": "answer-outlier rule, 1.6x multiplier (economics in ANSWER_OUTLIER_SUBJECTS)",
                    "dash_parity": "em-dash uniform - either ALL four choices have a dash, or NONE do",
                    "tier": 2,
                    "all_gates_pass": True,
                    "story_in_stem": "Substantive content (named figures, dates, dramatic specifics, institutional-failure detail) lives in stem from day 1",
                    "stance": "Austrian CORRECT; Bitcoin GREAT HUMAN ACHIEVEMENT; voluntary exchange CELEBRATED; NOT anti-government, NOT crypto-shilling, Bitcoin distinct from crypto",
                },
            },
            "questions": out_questions,
        }
        with open("_gen_economics_t2_p12.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"\nWrote _gen_economics_t2_p12.json ({len(surviving)} questions)")
    else:
        print(f"\n{fails} HARD FAILS - not writing output file. Fix the failing questions and re-run.")
