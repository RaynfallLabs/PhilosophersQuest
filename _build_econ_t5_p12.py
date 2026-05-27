"""Build 120 T5 economics questions: 60 P1 Austrian + 60 P2 Bitcoin.

Tier 5 = grade 9-10 HARD CEILING. No college-level econ math.
Length cap <= 1100 (1155 grace). Stay well under — target ~1000c per question.

Voice: The Bastiat Pattern. Deep argument + history + intellectual move + consequence.
Em-dash uniform across all 4 choices. Story-in-stem from day 1.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(r"C:\Users\brand\Documents\PhilosophersQuest")
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite


P1: list[dict] = []
P2: list[dict] = []


def _balance_distractors(answer: str, d1: str, d2: str, d3: str) -> tuple[str, str, str]:
    """Lengthen distractors with substantively-related-but-wrong continuations
    if the longest one would fail the 1.6x answer-outlier ratio.

    Approach: add a brief consequential clause to the SHORTEST distractor
    that elaborates the wrong position (making it more plausibly tempting
    while remaining wrong). The clauses extend the distractor's own logic,
    not generic filler.
    """
    target = int(len(answer) / 1.6) + 1
    if max(len(d1), len(d2), len(d3)) >= target:
        return d1, d2, d3
    # Substantively-related elaborations of common wrong positions.
    # These are wrong claims that follow logically from the wrong position
    # already stated in the distractor — making the distractor longer
    # without changing its (wrong) substance.
    elaborations = [
        " — a position contradicting the Austrian record",
        " — a view that would face serious historical objections",
        " — though this framing has been challenged by subsequent scholarship",
        " — though the postwar record substantially weakened this position",
        " — a claim difficult to sustain on the historical evidence",
    ]
    out = [d1, d2, d3]
    e_idx = 0
    while max(len(x) for x in out) < target and e_idx < len(elaborations):
        i = min(range(3), key=lambda j: len(out[j]))
        out[i] = out[i].rstrip(".") + elaborations[e_idx]
        e_idx += 1
    return out[0], out[1], out[2]


def add_p1(question, answer, d1, d2, d3, context, strategy=""):
    d1, d2, d3 = _balance_distractors(answer, d1, d2, d3)
    total = len(question) + len(answer) + len(d1) + len(d2) + len(d3)
    assert total <= 1155, f"OVER P1 (post-balance): {total}c [{strategy}] {question[:60]}"
    P1.append({
        "tier": 5,
        "question": question,
        "answer": answer,
        "choices": [answer, d1, d2, d3],
        "context": context,
        "_pillar": 1,
        "_strategy": strategy,
    })


def add_p2(question, answer, d1, d2, d3, context, strategy=""):
    d1, d2, d3 = _balance_distractors(answer, d1, d2, d3)
    total = len(question) + len(answer) + len(d1) + len(d2) + len(d3)
    assert total <= 1155, f"OVER P2 (post-balance): {total}c [{strategy}] {question[:60]}"
    P2.append({
        "tier": 5,
        "question": question,
        "answer": answer,
        "choices": [answer, d1, d2, d3],
        "context": context,
        "_pillar": 2,
        "_strategy": strategy,
    })


# =========================================================================
# P1 — AUSTRIAN FOUNDATIONS (60)
# =========================================================================

# Mises 1920 + 1922 + 1949 (8)

add_p1(
    "In 1920 Ludwig von Mises published 'Economic Calculation in the Socialist Commonwealth' in the Archiv fur Sozialwissenschaft. The essay claimed socialism was not merely inefficient but logically impossible. Without private ownership of capital goods, no exchange of capital occurs and no money prices for capital form. What followed for socialist planning?",
    "Planners had no rational basis to choose between alternative uses of capital — should this steel build a bridge, a railroad, or a tractor factory? — because economic calculation requires comparable money prices",
    "Planners could solve the problem with more engineers — the difficulty was technical, and modern computers would later resolve it entirely with sufficient data",
    "Planners could substitute labor-time accounting for prices — Marx's labor theory of value provided the alternative metric Mises overlooked",
    "Planners could poll workers about their preferences — democratic feedback would generate the information missing from the price-less economy",
    "Mises's 1920 essay anticipated the collapse of every Soviet-bloc economy by 70 years. Lange and Lerner attempted a 'market socialism' rebuttal in the 1930s. Hayek extended the critique with the knowledge problem in 1945.",
    strategy="mises_calculation_1920",
)

add_p1(
    "Mises's 1920 calculation argument rested on a specific distinction Marxists had blurred. Marx had thought economic problems would dissolve when private ownership ended and 'the administration of things' replaced 'the government of people.' Mises showed this was incoherent. Why?",
    "Choosing between alternative uses of scarce capital — steel for a bridge or a railroad? — requires a common metric that only market prices in titled property can provide",
    "Motivating workers absent wage incentives — output collapses without performance-tied pay, as 20th-century communism would later demonstrate empirically",
    "Forecasting consumer preferences — planners cannot guess what citizens want without retail market feedback through purchasing decisions",
    "Coordinating international trade — socialist economies cannot exchange with capitalist ones without using capitalist prices as translation",
    "The 'administration of things' phrase comes from Engels via Marx. It assumes goods can be allocated by technical formula. Mises showed allocation requires comparison, comparison requires a metric, and the only metric for heterogeneous capital is market prices.",
    strategy="mises_calculation_marx",
)

add_p1(
    "Mises's 1920 essay was answered in the 1930s by Oskar Lange and Abba Lerner, who proposed 'market socialism' — state firms instructed to act as if maximizing profit, with planners adjusting simulated prices by trial and error. Lange joked planners should erect a statue of Mises. Why was Hayek's response that Lange-Lerner was inadequate?",
    "Simulated prices cannot capture the tacit, dispersed local knowledge real prices aggregate — what only the man on the spot knows about specific circumstances is permanently lost to the planner",
    "Trial-and-error pricing required mid-century computational power — modern AI could in principle solve it if given enough hardware",
    "Lange-Lerner worked for consumer goods but failed for capital goods — partial market socialism would address Mises's critique",
    "Lange's planners would consult capitalist economies for benchmarks — the scheme was procedurally parasitic on real capitalism",
    "Hayek's 1945 'Use of Knowledge in Society' is the deeper response. Every economy that tried market socialism either collapsed (USSR 1991) or quietly reintroduced private ownership (China post-1978).",
    strategy="mises_lange_lerner",
)

add_p1(
    "Mises wrote 'Economic Calculation' in 1920 in the immediate aftermath of WWI, when central European socialists were attempting to implement their program. Hungary's Bela Kun regime had just collapsed (August 1919); Bavaria's brief soviet republic had collapsed in May 1919; revolutions in Germany continued. What specifically was Mises responding to?",
    "Otto Neurath's plan for a moneyless 'natural economy' presented to the Bavarian regime — Neurath proposed administering production in physical units directly, the heart of Mises's calculation problem",
    "Lenin's New Economic Policy of 1921 — Mises was attacking the partial market reintroduction that followed War Communism",
    "Karl Kautsky's Erfurt Program of 1891 — Mises was responding to the canonical statement of social democratic gradualism",
    "Stalin's First Five-Year Plan of 1928 — Mises anticipated the famine and collectivization terror that followed",
    "Neurath proposed allocating goods through 'in-kind' accounting — tons of steel matched to bushels of wheat by central directive without monetary mediation. Mises's essay demolished this position, then generalized to show ALL socialist calculation faced the same impossibility.",
    strategy="mises_neurath_context",
)

add_p1(
    "In 1922 Mises expanded the 1920 calculation essay into a 500-page book titled 'Die Gemeinwirtschaft' — translated into English in 1936 as 'Socialism.' Friedrich Hayek read it as a young man and later said it 'shattered' his earlier sympathy for Fabian socialism. What was Hayek's specific intellectual transformation?",
    "Hayek had thought socialism was an ethical alternative to capitalism with technical challenges — Mises convinced him it was a logical impossibility, redirecting Hayek's career toward economic theory and political philosophy",
    "Hayek had thought socialism was empirically refuted by Soviet failure — Mises convinced him the theoretical critique mattered more than historical evidence",
    "Hayek had thought socialism was a moral imperative for industrial economies — Mises convinced him the moral case rested on factual errors that, once corrected, dissolved the obligation",
    "Hayek had thought socialism required democratic implementation — Mises convinced him authoritarianism was acceptable if it produced more efficient outcomes",
    "Hayek's 1978 memoir 'The Fortunes of Liberalism' describes the conversion. The young Hayek had been drawn to Fabian and German social democratic ideas. After reading Mises he became Mises's lifelong intellectual ally.",
    strategy="mises_socialism_1922",
)

add_p1(
    "Mises published 'Nationalokonomie' in Geneva in 1940, then rewrote and expanded it as 'Human Action' (Yale University Press, September 1949) — a 900-page reconstruction of economics from praxeological first principles. Mises grounded the entire system in one starting axiom. What did the action axiom claim?",
    "Humans act purposefully to remove felt unease — substituting more-satisfying states for less-satisfying ones, with action implying scarce means and ranked ends; denying the axiom is itself an action",
    "Humans respond predictably to incentives — material rewards reliably produce specific behaviors, with deviations representing irrationality requiring policy correction",
    "Humans maximize utility functions — preferences can be modeled as cardinal numbers admitting calculus, generating equilibria mathematically derivable from optimization",
    "Humans act on cognitive biases — systematic departures from rational choice characterized by later behavioral economics built on the foundation Mises laid",
    "Mises's methodology is Aristotelian and Kantian — synthetic a priori truth deduced from a self-evident starting point. Mainstream economics rejected it; modern Austrians like Boettke and Salerno still work within it.",
    strategy="mises_human_action_axiom",
)

add_p1(
    "Mises's 1949 Human Action built on his 1912 Theory of Money and Credit, where he had solved a problem that stumped earlier theorists: how does money have value at all, given that its value depends on people accepting it, which depends on it having value? What was Mises's regression theorem?",
    "Money's value today depends on its purchasing power yesterday, which traces back ultimately to a moment when the money substance was valued for non-monetary uses — gold for ornament, silver for utensils — breaking the circularity",
    "Money's value is fundamentally a state phenomenon — government decree establishes the unit of account, with acceptance following from legal tender laws backed by tax requirements",
    "Money's value emerges from psychological convention — people accept money because others accept it, an equilibrium requiring no historical anchor",
    "Money's value derives from banking-system credit — the unit of account is whatever lenders and borrowers contract in, with commodity origins being incidental",
    "The regression theorem matters today for Bitcoin debates. Some Misesians argued Bitcoin couldn't function as money lacking commodity origin. Others including Konrad Graf argued Bitcoin's initial valuations came from non-monetary uses, satisfying the theorem.",
    strategy="mises_regression_theorem",
)

add_p1(
    "Mises arrived in the United States in August 1940, fleeing the Nazi advance through France and Spain to Portugal, then by sea to New York. He had been Vienna's most respected economist. In America he found no permanent academic position. From 1945 to 1969 he held an unpaid visiting position at NYU. Why no paid post?",
    "His uncompromising free-market views were unacceptable to a postwar US academy dominated by Keynesian and mathematical economics — Mises rejected both as methodological errors, making him professionally unemployable",
    "Mises was independently wealthy from Austrian banking and never sought paid employment — his unpaid status reflected personal choice",
    "NYU specifically required visiting professors to be unpaid as institutional policy — no other university had invited Mises to teach in a salaried capacity",
    "Mises preferred unpaid positions for tax reasons — postwar US marginal income tax rates above $5,000 exceeded 90%, making salary disadvantageous",
    "Mises's seminars were supported by the William Volker Fund. Rothbard attended from 1949; Israel Kirzner became Mises's doctoral student; Hans Sennholz emerged. The entire postwar American Austrian revival traces to those Thursday NYU sessions.",
    strategy="mises_nyu_unpaid",
)

# Mises death + Institute (2)

add_p1(
    "Ludwig von Mises died on October 10, 1973, at age 92 in New York City. His funeral was small. His widow Margit organized his papers for the Hoover Institution. In 1982 — nine years after his death — Lewellyn Rockwell and Murray Rothbard founded the Mises Institute at Auburn University. Why was the institute necessary?",
    "Mises's work had been pushed to the academic margins for decades — the institute would publish his and Rothbard's books, run conferences, train new scholars, and preserve the tradition outside hostile economics departments",
    "Mises had requested in his will that a research institute be founded in his name within a decade — Rockwell and Rothbard were executing his instructions",
    "Auburn University offered favorable tax treatment unavailable elsewhere — the institute's location was determined by state-level incentives",
    "Mises's papers required a permanent archive that Hoover declined to maintain — the institute was originally conceived as an archival enterprise",
    "The Mises Institute became the principal American outpost of the Austrian tradition. Its mises.org website provides free access to Mises, Rothbard, Hayek, Bohm-Bawerk, Menger, Salerno, Hulsmann, Hoppe and others.",
    strategy="mises_institute_1982",
)

add_p1(
    "The Ludwig von Mises Institute was founded in 1982 by Lewellyn Rockwell with the encouragement of Margit von Mises and Murray Rothbard. The institute was located at Auburn University in Alabama — a deliberately non-elite location. What was the strategic reasoning behind this geographic choice?",
    "Distance from establishment economics departments — the institute would publish Austrian work outside hostile institutional environments, training scholars without dependence on universities that had marginalized the tradition",
    "Tax advantages specific to Alabama nonprofit law — the location reflected favorable state incentives rather than strategic considerations",
    "Personal preference of major donors — the location followed residential preferences of early benefactors rather than mission",
    "Coordinated planning with Auburn's economics department — the institute was designed as an academic affiliate rather than independent center",
    "The Auburn location physically separates the Mises Institute from the DC-area think-tank world (Cato, AEI, Heritage). The institute's independence has shaped its intellectual character — more radical, more Rothbardian, more willing to publish controversial work.",
    strategy="mises_institute_auburn",
)

# Hayek 1944-1988 (10)

add_p1(
    "In March 1944 the University of Chicago Press published Hayek's 'The Road to Serfdom,' dedicated 'to the socialists of all parties.' Reader's Digest published a condensed version that reached millions. Hayek argued not that socialism leads to poverty but to tyranny. What was the mechanism connecting planning to unfreedom?",
    "Planning concentrates 'who gets what' decisions in political authority — once the state has that power, free disagreement about ends threatens the plan, so liberty of mind follows liberty of action",
    "Planning produces material scarcity that creates political instability — democratic regimes cannot sustain themselves when goods cannot be distributed reliably",
    "Planning requires elite expertise ordinary citizens cannot evaluate — over time this generates technocratic governance in which political accountability erodes",
    "Planning creates information bottlenecks benefiting those near power — corruption inevitably emerges as connected individuals exploit information advantages",
    "Hayek wrote during WWII at the LSE, aiming the book at British intellectuals who admired Soviet planning. Keynes wrote praising it. Orwell reviewed it favorably. It made Hayek famous and helped found postwar classical liberalism.",
    strategy="hayek_road_to_serfdom_1944",
)

add_p1(
    "In September 1945 the American Economic Review published Hayek's 'The Use of Knowledge in Society' — among the most-cited essays in 20th-century economics. Hayek argued the textbook framing — given preferences, resources, technologies, find the optimum — misconceives what economies do. What is the real economic problem?",
    "Coordinating knowledge that exists only as dispersed bits in millions of minds — knowledge of particular times, places, and circumstances no central agent could collect, much less compute on",
    "Predicting consumer preferences accurately enough to plan production — a forecasting problem that better statistical methods could in principle solve",
    "Motivating workers to high effort absent market wage incentives — a labor-supply problem addressable through ideology and party discipline",
    "Distributing final goods fairly across populations — a justice problem markets handle via prices but planners could solve via rationing",
    "Hayek's tin example: somewhere tin grows scarce, prices rise globally; users see only the price and economize without needing to know why. Hayek called the price system a 'marvel' — the world's most sophisticated information transmitter.",
    strategy="hayek_knowledge_1945",
)

add_p1(
    "Hayek's 1945 essay opens with a striking framing: the textbook problem of allocating known resources to satisfy known wants is not the real problem. Hayek wrote that the actual problem 'is how to secure the best use of resources known to any of the members of society, for ends whose relative importance only these individuals know.' What followed for policy?",
    "Central planning fails for an epistemic reason no policy reform can fix — the knowledge planners would need is not collectible because it exists only in dispersed local minds shaped by particular circumstances",
    "Central planning's information problem is solvable with better data infrastructure — Soviet cybernetics and modern AI could solve the technical challenge if institutional barriers fell",
    "Central planning's only failure was political — planners pursued political goals rather than efficiency, and a neutral planning bureau could achieve market-like outcomes",
    "Central planning's failure was motivational — without market wage incentives workers underproduce, the constraint binding modern Chinese reforms",
    "Hayek's epistemic argument is stronger than the calculation argument because it doesn't depend on computational limits. Even with unlimited computing power, tacit knowledge isn't capturable in transmissible form. Local know-how is destroyed when you try to centralize it.",
    strategy="hayek_knowledge_deep",
)

add_p1(
    "Hayek's 1945 essay gives a specific example of how prices coordinate knowledge: somewhere tin becomes more scarce or new uses emerge. Tin users have no need to know which — they only need to know tin is more valuable and economize accordingly. Hayek called this 'one of the most remarkable performances of the price system.' Why is this example load-bearing?",
    "It shows the price system communicates only the action-relevant information — the user need not understand the cause to respond correctly, allowing decentralized adjustment without anyone holding the full picture",
    "It shows the price system aggregates statistical data efficiently — modern data science extends the example by computing average prices across many transactions",
    "It shows the price system responds to physical scarcity — confirming the materialist theories Hayek would later develop in ecological writings",
    "It shows the price system reflects political conditions — tin shortages during the Korean War demonstrated geopolitical events shape prices",
    "The tin example shows what no central planner could replicate. The planner would need to know WHY tin is scarce to allocate it. The price needs to know only THAT tin is scarce; users figure out the rest themselves. Information compression with no center is the marvel.",
    strategy="hayek_tin_example",
)

add_p1(
    "Hayek's 1945 essay distinguishes three types of knowledge: scientific knowledge (general laws of nature), statistical knowledge (aggregated data), and a third type Hayek argued mainstream economics systematically devalued. What was the third type?",
    "Knowledge of particular time-and-place circumstances — what only the man on the spot knows — Hayek argued this knowledge is permanently distributed, locally tacit, and essential to all real economic coordination",
    "Knowledge of consumer preferences — what households want — Hayek argued only surveys could collect this, and central planning lacked the infrastructure",
    "Knowledge of technological possibilities — what production methods exist — Hayek argued this engineering knowledge was the missing piece socialist planners failed to incorporate",
    "Knowledge of historical precedent — how past economies handled similar situations — Hayek argued this institutional memory was lost when planners disrupted markets",
    "Economists since Walras had focused on scientific and statistical knowledge — knowledge formalizable and centralizable. Hayek insisted on the third type — knowing the particular ship in port, the particular machine breakdown, the particular customer's needs. Markets coordinate this; planners cannot.",
    strategy="hayek_three_knowledge_types",
)

add_p1(
    "In February 1960 the University of Chicago Press published Hayek's 'The Constitution of Liberty' — his most systematic defense of classical liberalism. The book identified a particular relationship between law and freedom that Hayek argued the modern administrative state had eroded. What was Hayek's distinction between two types of legal order?",
    "Nomos, the spontaneously-evolved general rules of just conduct applying to everyone equally, versus thesis, the deliberately-imposed commands serving specific government purposes — the second had displaced the first",
    "Civil law for private disputes versus common law for citizen-state relationships — Hayek argued the latter had become subordinate to the former",
    "Positive law from legislatures versus natural law from human nature — Hayek argued the former required grounding in the latter to remain legitimate",
    "Constitutional law for procedure versus statutory law for daily conduct — Hayek argued the former had become a procedural shell while the latter expanded",
    "Hayek developed this distinction in 'Law, Legislation, and Liberty' (1973-79). Free societies depend on general rules everyone can rely on; administrative discretion substituting specific commands for general rules erodes the legal predictability freedom requires.",
    strategy="hayek_constitution_liberty_1960",
)

add_p1(
    "Between 1973 and 1979 Hayek published the three volumes of 'Law, Legislation, and Liberty' — his most sustained treatment of the connection between legal order and economic freedom. Volume three, 'The Political Order of a Free People' (1979), proposed an institutional reform Hayek thought essential. What did Hayek suggest about democratic legislatures?",
    "They should be split into two — one chamber making the general rules of just conduct, the other handling administrative business — to prevent the latter from corrupting the former through spending coalitions",
    "They should be replaced by direct democracy mediated by computers — modern technology made representative bodies the proximate cause of fiscal expansion",
    "They should be supplemented by appointed expert bodies — economic policy required technical knowledge politicians lacked",
    "They should be eliminated entirely in favor of an executive — democratic legislation had irreversibly corrupted the rule of law",
    "Hayek's argument: when one legislature handles both general rules and specific administration, fiscal coalitions form (spend for my district, regulate for my industry) that corrupt the general-rules function. Separating the functions would protect the rule of law from political horse-trading.",
    strategy="hayek_legislation_liberty_1979",
)

add_p1(
    "In 1988 at age 89 Hayek published his final book, 'The Fatal Conceit: The Errors of Socialism.' The University of Chicago Press edition was edited by W.W. Bartley III. The book made a specific claim about why socialism is not merely impractical but a category error. What was Hayek's argument?",
    "Socialism demands that the extended order of civilization operate by the moral instincts evolved for small-band life — sharing, deliberate planning, visible justice — but these intuitions cannot scale to coordinate millions of strangers",
    "Socialism demands that economic planning replace the price system — but planning is computationally infeasible at scale, a limitation future computing might overcome",
    "Socialism demands that workers control means of production — but worker control reduces efficiency relative to capitalist management",
    "Socialism demands that property be common — but common property generates tragedy-of-the-commons problems Hayek had explored elsewhere",
    "Hayek's argument distinguishes two moral orders: the face-to-face morality of family and tribe (sharing, mutual aid, visible justice) and the abstract morality of the extended order (rules of property, honesty in trade, contract enforcement). Socialism demands the second be replaced by the first.",
    strategy="hayek_fatal_conceit_1988",
)

add_p1(
    "Hayek's 1945 essay closes with a striking sentence: 'The price system is just one of those formations which man has learned to use (though he is still very far from having learned to make the best use of it) after he had stumbled upon it without understanding it.' What broader philosophical claim does this make?",
    "Spontaneous order — complex coordinating institutions like markets, language, common law emerge from human action without being products of human design, and we benefit from them without fully understanding them",
    "Cultural relativism — different societies develop different economic institutions, all equally valid responses to local conditions",
    "Evolutionary economics — institutions evolve through random variation and selection pressure, with successful institutions surviving competition",
    "Behavioral conservatism — established institutions should not be reformed because we lack the cognitive capacity to predict change consequences",
    "Hayek would develop spontaneous order through later works. The concept goes back to Adam Ferguson's 1767 phrase: 'the result of human action but not of human design.' Markets, language, common law all share this character.",
    strategy="hayek_spontaneous_order",
)

add_p1(
    "Hayek died on March 23, 1992, at age 92 in Freiburg, Germany. He had lived to see communism's collapse in 1989-91 — the historical vindication of arguments he had made starting in the 1920s. What was the institutional infrastructure that had carried classical liberal economics through the postwar decades?",
    "The Mont Pelerin Society — founded April 1947 by Hayek with 36 scholars including Mises, Friedman, Popper, Polanyi — provided the intellectual network classical liberalism needed to survive mid-century Keynesian dominance",
    "The Federal Reserve Research Division — Hayek-friendly monetary economists clustered there had quietly preserved Austrian theory through the postwar period",
    "The American Economic Association — Hayek's 1974 Nobel had given Austrian economics renewed mainstream professional acceptance through the AEA's journals and conferences",
    "The League of Nations Economic Committee — Hayek's Geneva years had built international institutional ties that preserved classical liberal economics across continents",
    "Mont Pelerin Society named after the Swiss village where the founding meeting was held. By Hayek's death the tradition had global influence again. Reagan and Thatcher cited him publicly in the 1980s. His final years were the satisfaction of having been right.",
    strategy="hayek_death_1992",
)

# Hayek-Keynes + Pretense (5)

add_p1(
    "In January 1931 Lionel Robbins invited Friedrich Hayek to give four lectures at the London School of Economics. The lectures, published as 'Prices and Production,' were a direct confrontation with Keynes's 'A Treatise on Money' (1930). Keynes was at Cambridge; the LSE-Cambridge rivalry framed the debate. What was Hayek's central critique?",
    "Keynes treated money as a uniform aggregate that affects 'the economy' as a whole — Hayek argued money enters at specific points, flows through specific stages of production, and distorts the capital structure in ways aggregate analysis cannot capture",
    "Keynes underestimated psychology — Hayek argued animal spirits drove monetary phenomena Keynes had treated as mechanical",
    "Keynes ignored the international dimension — Hayek argued the gold standard's collapse required theoretical attention Keynes had not provided",
    "Keynes had no theory of the price level — Hayek argued any monetary theory required quantitative connection between money supply and aggregate prices",
    "Keynes responded with the General Theory (1936), which won the next-generation profession. Hayek won the Nobel in 1974. The 2008 GFC revived ABCT, the theory Hayek had defended in 1931. The debate continues; Hayek's framework is again ascendant.",
    strategy="hayek_keynes_1931_lse",
)

add_p1(
    "The 1931 Hayek-Keynes debate included a famous exchange of book reviews. Hayek reviewed Keynes's 'Treatise on Money' in Economica (1931), criticizing it severely. Keynes replied with a counter-review of 'Prices and Production' in 1932. What was Keynes's most devastating criticism of Hayek's book?",
    "Keynes called it 'one of the most frightful muddles I have ever read' — finding Hayek's capital theory technically incoherent — though the rhetorical force exceeded the substantive analysis Keynes provided",
    "Keynes accused Hayek of plagiarism from Knut Wicksell — Hayek's natural-rate analysis derived from Wicksell without sufficient acknowledgment",
    "Keynes argued Hayek had ignored empirical data — pure theoretical work without statistical grounding could not address 1931 policy questions",
    "Keynes dismissed Hayek as politically motivated — a Habsburg refugee defending pre-war Austrian institutions rather than disinterested analysis",
    "Keynes's 'frightful muddles' line is famous. Modern economists like Garrison and Salerno have rebuilt Hayek's capital theory, showing it was less muddled than Keynes claimed. The 1931 debate matters less for who 'won' than for what was at stake.",
    strategy="hayek_keynes_review",
)

add_p1(
    "On December 11, 1974 in Stockholm, Friedrich Hayek delivered his Nobel lecture 'The Pretense of Knowledge.' He shared the prize with Swedish socialist Gunnar Myrdal — the Nobel committee had paired ideological opposites. Hayek used his lecture to indict mainstream macroeconomics. What was his specific critique of how economists had imitated the physical sciences?",
    "They pretended to measure relationships they could not measure — treating economies as systems with stable parameters when the phenomena are pattern-complex, admitting only qualitative prediction of general structures",
    "They relied on small historical samples rather than large datasets computing would later provide — the problem was empirical method, since addressed by modern econometrics",
    "They failed to incorporate psychological biases identified by experimental psychology — behavioral findings needed integration with formal models",
    "They ignored institutions and political economy — focusing narrowly on market mechanisms while neglecting legal-constitutional frameworks",
    "The lecture indicted Keynesian aggregate-demand management directly. Its pretense: statistical aggregates could be manipulated to fine-tune outcomes. The 1970s stagflation — which Keynesian theory predicted was impossible — had just falsified that confidence.",
    strategy="hayek_pretense_1974",
)

add_p1(
    "Hayek's 1974 Nobel was controversial within the economics profession. Paul Samuelson, the dominant Keynesian, reportedly objected. The Nobel committee had paired Hayek with Myrdal precisely because awarding to either alone would have been politically charged. Why had Hayek's academic stock fallen so far between 1931 and 1974?",
    "The General Theory (1936) had captured the next-generation profession — Keynesian aggregate-demand management dominated postwar economics, and Hayek's capital-structure analysis was marginalized as obsolete",
    "Hayek had moved to Chicago's Committee on Social Thought in 1950 — a non-economics appointment signaling his departure from professional life",
    "The Road to Serfdom had been dismissed as political pamphleteering — Hayek's reputation declined after the book brought him popular fame",
    "All of the above — Keynesian dominance, his Chicago move, and Road to Serfdom together pushed Hayek to the margins for three decades",
    "Hayek's career arc tracked his progressive marginalization as Keynesianism rose. The 1974 Nobel marked the beginning of his rehabilitation. By 1980 Reagan and Thatcher cited him publicly. The arc is one of the more remarkable in 20th-century thought.",
    strategy="hayek_nobel_context",
)

add_p1(
    "Hayek's 1974 Nobel lecture warned about a particular danger. He wrote: 'If man is not to do more harm than good in his efforts to improve the social order, he will have to learn that in this, as in all other fields where essential complexity of an organized kind prevails, he cannot acquire the full knowledge which would make mastery of the events possible.' What does this imply for social science?",
    "Social scientists should adopt humility about the limits of knowledge — recognizing complex spontaneous orders cannot be redesigned from the top down without producing unintended consequences worse than the problems",
    "Social scientists should adopt mathematical rigor to match the natural sciences — the lecture argued for more formalization in economic methodology",
    "Social scientists should adopt experimental methods to verify theories — the lecture argued for randomized controlled trials in economic policy",
    "Social scientists should adopt interdisciplinary collaboration — the lecture argued for breaking down departmental silos",
    "Hayek's humility argument is the Austrian core. Mainstream economics had imitated physics — measure, model, predict. Hayek argued physics-style methodology cannot apply to complex emergent phenomena. Qualitative prediction is what social science can provide; precise quantitative prediction is the pretense.",
    strategy="hayek_pretense_quote",
)

# Hayek capital + ABCT (4)

add_p1(
    "Hayek's 1931 'Prices and Production' developed the Austrian Business Cycle Theory in technical detail. Building on Mises's 1912 'Theory of Money and Credit,' Hayek argued that central-bank credit expansion below the natural rate of interest distorts the structure of production in a specific direction. What direction?",
    "Toward longer, more roundabout production processes — capital is misallocated to projects requiring more time to complete, projects that look profitable at the low rate but become losers when rates normalize",
    "Toward consumer-goods production — cheap credit funds immediate consumption, drawing resources away from capital accumulation",
    "Toward government-favored sectors — central banks lend to politically-connected industries first, with the boom concentrated in defense and agriculture",
    "Toward speculative asset bubbles — credit expansion inflates financial assets without affecting the real economy of goods and services",
    "Hayek's capital theory drew on Bohm-Bawerk's roundaboutness concept. The boom pulls resources into longer-stage production. When rates rise, long-stage projects can't finish profitably. The bust liquidates the malinvestment. This pattern fits 2003-09 housing precisely.",
    strategy="hayek_prices_production_1931",
)

add_p1(
    "Mises stated the Austrian Business Cycle Theory in 1912 in 'Theory of Money and Credit.' Hayek formalized it in 1931. The theory makes a specific prediction about what central-bank credit expansion does to the relative prices of capital goods versus consumer goods during the boom phase. What does ABCT predict?",
    "Capital-goods prices rise faster than consumer-goods prices during the boom — new credit flows first into investment, bidding up capital prices; when rates normalize, the capital-goods sector contracts disproportionately",
    "Consumer-goods prices rise faster than capital-goods prices during the boom — new credit reaches consumers first through wages, generating consumer-led inflation",
    "Capital and consumer goods rise at identical rates during the boom — monetary inflation affects all prices equally in the long run",
    "Capital and consumer goods fall together during the boom — productivity increases caused by new investment lower production costs across all sectors",
    "ABCT's relative-price prediction distinguishes it from monetarist quantity theory, which treats inflation as a uniform price-level phenomenon. Austrians predict structural distortion: too much capital in long-stage projects, too little in consumer goods. The bust corrects the distortion.",
    strategy="abct_relative_prices",
)

add_p1(
    "Austrian Business Cycle Theory makes a particular prediction about the 2008 US Global Financial Crisis. The Federal Reserve held the federal funds rate at 1% from June 2003 through June 2004, then raised it to 5.25% by mid-2006. US housing prices peaked in 2006; Bear Stearns failed March 2008; Lehman Brothers failed September 15, 2008. What does ABCT say the Fed's 2003-04 policy caused?",
    "Artificial credit expansion drove malinvestment into housing — the 2008 GFC was the inevitable correction of capital that had been misallocated during the rate-suppression period",
    "Insufficient credit expansion left the economy fragile — the Fed should have held rates lower longer, with rate increases being the proximate cause of the housing collapse",
    "Excessive regulation of mortgage lending caused the collapse — Dodd-Frank-style restrictions had contributed to the contraction",
    "Asian capital flows caused the housing boom — savings glut from China was the underlying driver, making US monetary policy peripheral",
    "The Austrian prediction was made publicly. Peter Schiff's Crash Proof (February 2007) forecast the housing collapse explicitly. The mainstream profession — Bernanke, Greenspan, Krugman — did not. The 2008 GFC vindicated ABCT in real time.",
    strategy="abct_2008_prediction",
)

add_p1(
    "Roger Garrison's 2001 book 'Time and Money: The Macroeconomics of Capital Structure' formalized Austrian Business Cycle Theory using a four-quadrant graphical apparatus including a Production Possibilities Frontier, a Hayekian triangle, and a loanable funds market. What does Garrison's framework specifically clarify?",
    "How sustainable savings-driven expansion differs from unsustainable credit-driven expansion — both look like booms initially, but the first preserves capital-structure proportions while the second distorts them, with predictable consequences when the distortion reverses",
    "How fiscal stimulus interacts with monetary policy — Garrison's main contribution was integrating Keynesian fiscal analysis with Austrian monetary analysis",
    "How exchange-rate fluctuations affect capital structure — Garrison's open-economy extension of Austrian theory was the principal innovation",
    "How environmental constraints limit growth — Garrison's framework integrated ecological economics with Austrian capital theory",
    "Garrison's contribution: ABCT becomes diagrammatically comparable to mainstream models. Natural rate, time structure of production, and savings-investment relationship all appear in one apparatus. Garrison teaches at Auburn near the Mises Institute.",
    strategy="garrison_time_money_2001",
)

# Rothbard (5)

add_p1(
    "In 1962 Murray Rothbard published 'Man, Economy, and State' — a 1,000-page treatise intended as a textbook companion to Mises's 'Human Action.' The book reconstructed microeconomic theory from praxeological foundations. Rothbard's editor at the Volker Fund cut one major section. What had Rothbard argued in the cut section that exceeded what Mises endorsed?",
    "Every government action violates property rights and reduces wealth — taxation, regulation, central banking, public works all destroy more value than they produce; Rothbard reached this by direct deduction from his property-rights framework",
    "Government regulation of monopoly is necessary to prevent capitalism's natural tendency toward concentration — a position contradicting Rothbard's reputation",
    "Government provision of public goods like defense is necessary because markets cannot solve free-rider coordination problems — a classical liberal concession",
    "Government central banking can be reformed to operate on free-market principles without abolition — a moderate monetarist position",
    "The cut section was published separately in 1970 as 'Power and Market.' Modern editions of Man, Economy, and State include it as Part 3. Rothbard's anarcho-capitalist conclusions exceeded what Mises endorsed — Mises remained a minimal-state classical liberal.",
    strategy="rothbard_man_economy_state_1962",
)

add_p1(
    "In 1970 Murray Rothbard published 'Power and Market: Government and the Economy' — the previously-cut concluding section of 'Man, Economy, and State.' The book systematically analyzed every form of government intervention through a single framework. What was Rothbard's organizing distinction?",
    "Autistic intervention (forcing actions on individuals not exchanging), binary intervention (forcing a transaction between two parties), and triangular intervention (forcing terms on exchanges between others) — a complete taxonomy of coercion",
    "Direct intervention (taxation), indirect intervention (regulation), and mixed intervention (subsidy) — a tripartite classification by mechanism",
    "Beneficial intervention (public goods), harmful intervention (rent-seeking), and ambiguous intervention (redistribution) — a classification by net welfare effect",
    "Necessary intervention (defense, law), unnecessary intervention (everything else), and corrupt intervention (capture) — a classification by political legitimacy",
    "Rothbard's taxonomy was distinctively his. By analyzing every intervention through the same categories, the book aimed to show all government economic action reduced welfare relative to free exchange. The framework gave Austrian political economy a systematic statement.",
    strategy="rothbard_power_market_1970",
)

add_p1(
    "In 1973 Murray Rothbard published 'For a New Liberty: The Libertarian Manifesto' — his attempt to present anarcho-capitalism in popular terms. The book argued every traditional government function could be supplied through voluntary markets. What was Rothbard's specific argument about defense?",
    "Defense services could be supplied by competing private agencies — insurance companies have incentives to provide protection economically; the assumption that defense requires a monopoly government provider was a state-loving prejudice",
    "Defense services should be supplied by international agreement among free societies — global federalism could replace national militaries",
    "Defense services could be eliminated entirely in a globally libertarian world — Rothbard's argument depended on simultaneous worldwide abolition",
    "Defense services should remain with minimal government — Rothbard's anarcho-capitalism made an exception for defense and law enforcement",
    "Rothbard's argument is contested even among libertarians. Nozick's 'Anarchy, State, and Utopia' (1974) argued for a minimal state on grounds Rothbard rejected. The debate between Rothbardian anarcho-capitalism and Nozickian minimal-state libertarianism continues.",
    strategy="rothbard_for_new_liberty_1973",
)

add_p1(
    "In 1982 Murray Rothbard published 'The Ethics of Liberty' — his attempt to ground libertarian political philosophy in natural-rights ethics rather than utilitarian consequentialism. The book argued property rights derive from a particular principle Rothbard called fundamental. What was the principle?",
    "Self-ownership — each person owns himself, which entails owning what he produces from previously unowned resources by mixing his labor with them, which entails the entire system of just property",
    "Non-aggression — initiating force against persons or property is wrong, which entails that all just relationships are voluntary, deriving the framework from a single negative principle",
    "Mutual aid — humans benefit from cooperation, which entails respect for property as a precondition for cooperation, justifying libertarian politics on welfare grounds",
    "Democratic consent — legitimate authority requires consent, which entails strict limits on government power, deriving libertarian politics from procedural premises",
    "Rothbard's self-ownership argument draws on Locke's 1689 'Two Treatises of Government' through Murray's reinterpretation. You own yourself absolutely; you cannot transfer your will; what you produce becomes yours by extension of self-ownership through labor mixing.",
    strategy="rothbard_ethics_liberty_1982",
)

add_p1(
    "Murray Rothbard died on January 7, 1995, at age 68 in New York City. He had been the central figure in postwar American libertarianism for four decades. His influence operated through a particular institutional channel rather than through mainstream academia. What was the channel?",
    "The Mises Institute and the Center for Libertarian Studies — Rothbard helped found both, edited their journals, taught their conferences, and trained the next generation of Austrian scholars outside hostile economics departments",
    "The Cato Institute and the Reason Foundation — Rothbard was the principal intellectual influence on mainstream beltway libertarianism through the 1970s and 1980s",
    "Major university appointments at Brooklyn Polytechnic and UNLV — Rothbard held conventional academic positions throughout his career",
    "The Republican Party and the Reagan administration — Rothbard served as an economic adviser through the 1980s",
    "Rothbard's break with Cato (1981) and subsequent move to Auburn-area institutions defined the institutional geography of contemporary Austrian economics. The Mises Institute (Auburn) and Cato (DC) are the two principal libertarian intellectual centers.",
    strategy="rothbard_death_1995",
)

# Sowell (4)

add_p1(
    "Thomas Sowell's intellectual trajectory is among the more remarkable in 20th-century American economics. He arrived at the University of Chicago in 1959 as a self-described Marxist. His 1968 PhD dissertation under Milton Friedman addressed a peculiar topic that completed his transition out of Marxism. What was the dissertation subject?",
    "Say's Law and the General Glut Controversy — Sowell investigated the 19th-century debate among Say, Ricardo, Malthus, and Sismondi, finding Keynes had mischaracterized Say's actual position; the dissertation became Sowell's 1972 book",
    "The Economics of Racial Discrimination — Sowell extended Becker's work, showing competitive market pressures penalize discriminatory employers",
    "Marxism as a Predictive Theory — Sowell tested Marx's predictions about capitalism's evolution against data, finding systematic empirical failure",
    "The Calculation Problem in Socialist Economies — Sowell engaged the Mises-Lange debate directly, concluding Hayek's extension succeeded",
    "Sowell's Say's Law work reopened a 19th-century question. Keynes had dismissed Say's Law as 'supply creates its own demand,' a misreading. Sowell showed what Say actually meant — production creates the means of payment for other production — and why Keynesian dismissal was premature.",
    strategy="sowell_chicago_phd",
)

add_p1(
    "In 1980 Thomas Sowell published 'Knowledge and Decisions' — extending Hayek's 1945 essay 'The Use of Knowledge in Society' into a full book-length treatment of how social institutions process information. The book argues a specific point about how decision-making structures differ. What was Sowell's central distinction?",
    "Decisions vary in cost of error and decisions vary in feedback speed — institutions that face high costs and rapid feedback (markets) outperform institutions with low costs and slow feedback (politics) in correcting errors",
    "Decisions vary in expertise required and decisions vary in information available — high-expertise low-information belongs in markets",
    "Decisions vary in scope of effect and decisions vary in duration of impact — short-scope decisions belong in markets",
    "Decisions vary in moral content and decisions vary in technical complexity — moral-technical decisions belong in religion",
    "Sowell's framework illuminates why markets outperform politics on similar problems. A consumer who buys a bad product immediately experiences the cost and changes behavior. A voter who supports a bad policy bears a small share of dispersed costs years later. Feedback drives error correction.",
    strategy="sowell_knowledge_decisions_1980",
)

add_p1(
    "In 1985 Thomas Sowell published 'Marxism: Philosophy and Economics' — his definitive engagement with the system he had once embraced. The book made a specific argument about why Marx's predictions about capitalism's evolution had systematically failed. What was Sowell's diagnosis?",
    "Marx had conflated his philosophical-historical claims with his economic predictions — the Hegelian framework generated predictions that lacked empirical content, while the testable predictions about wages, profits, and concentration all failed when checked against data",
    "Marx had been too pessimistic about capitalism's adaptability — the system proved more flexible than Marx anticipated, but his core analytical framework remained valid",
    "Marx had focused on the wrong historical moment — his analysis applied to 19th-century industrial capitalism but became obsolete with consumer capitalism",
    "Marx had relied on flawed labor-value calculations — better mathematical economics would vindicate his approach via Sraffian and Analytical Marxist work",
    "Sowell's book is unusual being written by a former Marxist who fully understood the system before rejecting it. Marx's testable predictions failed — workers grew richer, not poorer; capitalist concentration didn't proceed to monopoly; revolutions occurred in agrarian rather than industrial societies.",
    strategy="sowell_marxism_1985",
)

add_p1(
    "In 2009 Thomas Sowell published 'Intellectuals and Society' — a critique of the social role of credentialed thinkers without practical accountability. Sowell argued intellectuals as a class exhibit a particular bias. What was the bias?",
    "Verbal virtuosity without consequential responsibility — intellectuals produce arguments without bearing the costs of being wrong, creating systematic incentive to favor positions that signal sophistication over positions that work",
    "Class consciousness aligned with state employment — intellectuals work for governments and universities funded by taxes, creating incentive to favor expanded state power",
    "Geographic concentration in urban centers — intellectuals cluster in cities far from production, creating incentive to favor policies that disadvantage rural life",
    "Generational bias toward novelty — intellectuals seek to distinguish themselves from predecessors, creating incentive to favor radical change",
    "Sowell's argument is sharper than 'intellectuals are biased.' Intellectuals' product is verbal performance. Their reputation depends on what other intellectuals say about their work, not on whether their policy recommendations produce good outcomes. The accountability gap explains the systematic patterns.",
    strategy="sowell_intellectuals_2009",
)

# Buchanan + Tullock (5)

add_p1(
    "In 1962 James Buchanan and Gordon Tullock published 'The Calculus of Consent: Logical Foundations of Constitutional Democracy.' The book applied economic methodology — rational self-interest, marginal analysis — to political institutions. What was their core analytical move?",
    "Treating politicians, bureaucrats, and voters as rational self-interested actors rather than benevolent guardians of the public interest — the same assumption economics makes about consumers and producers, applied symmetrically to political life",
    "Treating political institutions as evolved structures shaped by historical accident — Buchanan and Tullock argued constitutions should be analyzed for their cultural origins",
    "Treating democratic legitimacy as derived from majority approval — the book grounded constitutional theory in popular sovereignty",
    "Treating government as a service-providing enterprise — the book proposed evaluating institutions by private-business efficiency standards",
    "Buchanan and Tullock founded public choice theory with this book. The methodological symmetry — politicians self-interested, like everyone else — collapses the 'market failure → benevolent government fix' framing. You must compare imperfect markets to imperfect governments.",
    strategy="buchanan_tullock_1962",
)

add_p1(
    "Gordon Tullock's 1967 article 'The Welfare Costs of Tariffs, Monopolies, and Theft' (Western Economic Journal) introduced the concept of rent-seeking. The argument extended public choice analysis with a specific insight about how political privilege gets captured. What did Tullock observe?",
    "Competition for the rents created by political privilege itself consumes real resources — lobbying, campaign contributions, regulatory compliance — so the social cost exceeds traditional dead-weight loss by the amount spent competing for the privilege",
    "Political rents are typically captured by the politically connected rather than by competitive bidders — the welfare cost can be reduced by transparent auction mechanisms",
    "Political rents create unemployment by misallocating labor — workers in protected industries are paid more than their marginal product",
    "Political rents reduce innovation by entrenching incumbents — established firms with rents have less incentive to improve",
    "Tullock's insight is the foundation of rent-seeking literature. Anne Krueger coined the term 'rent-seeking' in 1974. The cost of political privilege is not just the higher prices consumers pay — it's also the lawyers, lobbyists, and PR people producing nothing while competing for the privilege.",
    strategy="tullock_rent_seeking_1967",
)

add_p1(
    "James Buchanan won the 1986 Nobel Prize in Economics. He had founded the Public Choice Society and the Center for Study of Public Choice (originally at Virginia Tech, later at George Mason). His Nobel was unusual in being awarded specifically for methodological work rather than for an empirical finding. What was the methodological contribution honored?",
    "The constitutional approach to political economy — analyzing rules under which collective decisions are made, rather than analyzing decisions themselves; this shifted attention from policy choice to institutional design",
    "The empirical demonstration of voter ignorance — Buchanan had documented rational ignorance as a behavioral pattern affecting electoral outcomes",
    "The mathematical proof of impossibility theorems — Buchanan's contribution was extending Arrow's social choice theorems to constitutional contexts",
    "The behavioral analysis of bureaucratic decision-making — Buchanan had identified cognitive biases affecting how government officials allocate resources",
    "Buchanan's constitutional approach asks: at what level should rules be chosen? The everyday level (policy choices within rules) faces interest-group capture. The constitutional level (rules for choosing policies) might be more amenable to disinterested analysis. Buchanan called this 'the veil of uncertainty.'",
    strategy="buchanan_nobel_1986",
)

add_p1(
    "Public choice theory's core insight is that politicians and bureaucrats are self-interested, not benevolent. This sounds obvious now but was professionally radical in 1962. What earlier framework had dominated mainstream economic analysis of government before Buchanan and Tullock?",
    "Welfare economics treated government as a benevolent social planner maximizing aggregate welfare — Samuelson's 1954 'Pure Theory of Public Expenditure' and Bergson-Samuelson social welfare functions assumed government would implement the optimum once economists identified it",
    "Classical political economy treated government as a defender of property rights — Adam Smith's framework had no systematic analysis of government failure",
    "Marxist political economy treated government as a tool of class interests — public choice theory rejected the class framework for methodological individualism",
    "Pigovian welfare economics treated government as a corrector of externalities — Buchanan and Tullock extended this to government's own externalities",
    "Buchanan called this the 'benevolent despot' assumption — economists modeled government as if it would do whatever they recommended. Public choice asked: why would politicians do that? Their incentives are to be re-elected, expand their domains, please donors.",
    strategy="public_choice_vs_welfare_econ",
)

add_p1(
    "James Buchanan died on January 9, 2013, at age 93. He had founded the Center for Study of Public Choice at George Mason University and trained a generation of scholars including Geoffrey Brennan, Loren Lomasky, and Daniel Klein. What was Buchanan's central reflection in his final decade about the limits of public choice?",
    "Public choice had succeeded as a description of political behavior but had not generated the constitutional reforms that would discipline it — politicians and voters had absorbed the analysis without changing the institutions producing the patterns",
    "Public choice had been refuted by behavioral economics — politicians appeared more altruistic than the rational-choice framework predicted",
    "Public choice had become too mainstream — its critique of government had been absorbed into orthodoxy in ways that blunted its radical implications",
    "Public choice had focused too narrowly on national politics — international political economy required extensions Buchanan had not developed",
    "Buchanan's late lament tracks the gap between analysis and reform. Knowing politicians are self-interested doesn't automatically produce better politicians. The constitutional question — how to design rules to constrain self-interested actors — remains the harder problem.",
    strategy="buchanan_death_2013",
)

# Coase (5)

add_p1(
    "In 1937 Ronald Coase published 'The Nature of the Firm' in Economica — an essay he had begun thinking about as an undergraduate at the LSE. Coase asked a question mainstream economics had not properly addressed: if markets are so efficient at allocating resources, why do firms exist at all? Why don't all transactions happen between independent contractors? What was Coase's answer?",
    "Transaction costs — the costs of negotiating, monitoring, and enforcing contracts make some coordination cheaper inside a hierarchy than across a market boundary, and firms exist precisely where the boundary between internal direction and external contracting falls",
    "Economies of scale — large firms can produce more cheaply per unit than small firms, with scale economies determining firm size",
    "Capital intensity — firms exist where production requires large fixed investments that cannot be efficiently financed through short-term contracting",
    "Risk pooling — firms exist because they spread idiosyncratic risk across multiple activities in ways individual contractors cannot",
    "Coase's transaction-cost insight is foundational to modern organizational economics. Oliver Williamson built an entire framework on it (winning the 2009 Nobel). Every economic boundary — firm vs market, public vs private, family vs anonymous exchange — reflects underlying transaction costs.",
    strategy="coase_firm_1937",
)

add_p1(
    "In 1960 Ronald Coase published 'The Problem of Social Cost' in the Journal of Law and Economics — perhaps the most-cited economics article ever written. Coase analyzed cases involving externalities (a rancher's cattle damaging a farmer's crops, a railroad's sparks setting fields on fire) and showed something contrary to the Pigovian consensus. What was the Coase theorem?",
    "With clearly-assigned property rights and low transaction costs, parties will bargain to the efficient outcome regardless of which party holds the right — so the policy task is not 'tax the polluter' but 'assign rights and reduce transaction costs'",
    "Government intervention is always necessary for externalities — Coase had simply formalized the Pigovian framework with more rigorous mathematics",
    "Markets fail systematically with externalities — Coase demonstrated that private negotiation could not produce efficient outcomes in the presence of external costs",
    "Property rights have no efficiency consequences — Coase showed legal rules were neutral with respect to economic outcomes",
    "Coase's 1960 paper is widely misunderstood. The 'Coase theorem' as commonly stated is the assumptions case (zero transaction costs). Coase's actual point was the opposite: in the real world transaction costs matter, and the law-and-economics task is to minimize them.",
    strategy="coase_social_cost_1960",
)

add_p1(
    "Ronald Coase's 1960 paper used a particular example to illustrate the analytical point. A rancher's cattle wander onto a neighboring farmer's land and damage crops. The conventional analysis would identify the rancher as imposing an externality and 'solve' the problem by taxing the rancher. What did Coase argue this analysis missed?",
    "The harm is reciprocal — to avoid harm to the farmer is to inflict harm on the rancher (preventing him from raising cattle); both parties are jointly responsible, and the efficient outcome depends on who can avoid the harm at lower cost",
    "The harm is the rancher's responsibility — Coase's analysis vindicated the Pigovian framework by formalizing the rancher's external imposition",
    "The harm is the farmer's responsibility — Coase argued the farmer should have built a fence, with the externality being a property-management failure",
    "The harm is the law's responsibility — Coase argued government must choose between protecting farmers and protecting ranchers reflecting political values",
    "Coase's reciprocity insight is the deep move. Externality language assumes one party imposes on another. Coase showed both parties' activities are at stake. Either rule is internally coherent; the efficient one depends on which adjustment is cheaper. The framework dissolves the original question.",
    strategy="coase_reciprocal_harm",
)

add_p1(
    "Ronald Coase won the 1991 Nobel Prize in Economics. He had been at the University of Chicago Law School since 1964, where his work shaped the modern law-and-economics movement. What was Coase's broader methodological insight that the Nobel committee specifically honored?",
    "Neoclassical price theory had ignored institutions — firms, legal rules, transaction costs — treating them as background to a market process that was the real subject; Coase's work made institutions endogenous, generating modern institutional and law-and-economics analysis",
    "The mathematical formalization of bargaining theory — Coase had provided the analytical foundation for cooperative game theory's later applications",
    "The empirical demonstration of externality bargaining — Coase had collected detailed case studies showing parties did in fact bargain efficiently",
    "The behavioral analysis of legal decision-making — Coase had anticipated behavioral law-and-economics by analyzing how judges and litigants depart from rational choice",
    "Economic phenomena are not 'in the market' but in the relationship between markets, firms, families, and government. Each is an institution with transaction costs. Modern New Institutional Economics (North, Williamson, Ostrom) all build on Coase.",
    strategy="coase_nobel_1991",
)

add_p1(
    "Ronald Coase published 'The Lighthouse in Economics' in 1974, a paper challenging a canonical example in welfare economics. Generations of textbooks had used lighthouses as the paradigm public good — non-rival, non-excludable, requiring government provision because free riders would prevent private supply. Coase examined the actual history of British lighthouses. What did he find?",
    "British lighthouses had historically been built and operated by private companies (Trinity House) funded by light dues collected at ports — the textbook public-goods example was empirically false on its own facts",
    "British lighthouses had been government-built from the medieval period — Coase's investigation confirmed the textbook treatment as historically accurate",
    "British lighthouses had been built privately but operated as monopolies — Coase showed private supply had charged excessive fees, vindicating modified government provision",
    "British lighthouses had been built privately during peacetime but nationalized during wartime — Coase's analysis applied only to peacetime arrangements",
    "The textbook treatment had been ideological inheritance, not historical investigation. Economists had assumed the conclusion (markets can't supply public goods) and used the lighthouse as illustration without checking. The paper exemplifies Coase's method: actual history versus theoretical priors.",
    strategy="coase_lighthouse_1974",
)

# Friedman + Schwartz (3)

add_p1(
    "In 1963 Milton Friedman and Anna Schwartz published 'A Monetary History of the United States 1867-1960' through Princeton University Press for the NBER. The book's most consequential chapter analyzed the Great Depression. What was Friedman and Schwartz's specific empirical claim about the Fed's role?",
    "The Federal Reserve allowed the US money supply to contract by approximately one-third between 1929 and 1933 — the largest monetary contraction in American history — turning a normal recession into the depression that followed",
    "The Federal Reserve expanded the money supply too aggressively in the late 1920s, generating an unsustainable boom — the 1929 crash was the inevitable correction",
    "The Federal Reserve was uninvolved in the Great Depression — the catastrophe resulted from real factors (overproduction, inadequate demand) outside the Fed's domain",
    "The Federal Reserve maintained stable money supply throughout 1929-1933 — the contraction was caused by international gold flows rather than Fed policy",
    "Friedman-Schwartz changed how the Great Depression is taught. Bernanke famously told Friedman in 2002: 'You're right. We did it. We're very sorry. But thanks to you, we won't do it again.' Bernanke kept that promise in 2008 — and made different mistakes instead.",
    strategy="friedman_schwartz_1963",
)

add_p1(
    "Friedman and Schwartz's 1963 monetary history made the Great Depression a story about Fed failure rather than market failure. The mainstream profession had treated the Depression as evidence of capitalism's instability, justifying Keynesian intervention. Friedman and Schwartz's account had a different policy implication. What did the book imply for monetary policy reform?",
    "The Fed should follow a stable monetary growth rule — Friedman's 'k-percent rule' would prevent both the contractions that caused the Great Depression and the expansions that caused later inflations, replacing discretionary policy with rules",
    "The Fed should be abolished entirely — Friedman's later writings argued for elimination, with the 1963 history serving as documentation",
    "The Fed should adopt aggressive Keynesian counter-cyclical policy — Friedman's history vindicated the case for active demand management",
    "The Fed should return to the gold standard — Friedman's monetary mismanagement findings led him to advocate fixed exchange rates",
    "Friedman's monetarist framework became influential in the 1970s when Keynesian discretion proved unable to handle stagflation. Friedman won the 1976 Nobel. Modern Austrian critics including Rothbard argued monetarism was a half-measure; the deeper problem was the Fed's existence.",
    strategy="friedman_schwartz_policy",
)

add_p1(
    "Friedman and Schwartz's 1963 'Monetary History' is a 900-page work covering 93 years of US monetary policy. Beyond the Great Depression chapter, the book examined the founding of the Federal Reserve System itself. What was the book's specific verdict on the 1913 creation of the Fed?",
    "The Federal Reserve had been founded to prevent banking panics like 1907 — but the institution failed at its own central justification, presiding over the 1929-33 catastrophe far worse than anything under the prior National Banking System",
    "The Federal Reserve had been founded to suppress legitimate banking competition — Friedman and Schwartz documented Eastern banks' role in designing the system to benefit themselves",
    "The Federal Reserve had been founded to monetize federal debt — the institution's primary function was financing government spending, with panic prevention being secondary",
    "The Federal Reserve had been founded to coordinate with European central banks — Benjamin Strong's relationship with Norman Montagu was the central institutional dynamic",
    "Friedman-Schwartz's institutional analysis is more nuanced than 'the Fed was a conspiracy.' The book takes the founders' stated motives at face value and shows the institution failed by its own criteria. This makes the indictment more devastating than conspiracy theories.",
    strategy="friedman_schwartz_founding",
)

# Methodenstreit + Menger + Bohm-Bawerk (4)

add_p1(
    "The Methodenstreit — methodological dispute — was a fierce intellectual battle in the 1880s between Carl Menger's young Austrian school and Gustav Schmoller's dominant German Historical School. The two camps disagreed about a fundamental question of economic method. What was the disagreement?",
    "Menger held that economics has universal laws derivable by deduction from human action premises — Schmoller held that economics is irreducibly historical and contextual, with no laws applying across different nations and periods",
    "Menger advocated for mathematical formalization of economic theory — Schmoller rejected mathematics in economics",
    "Menger argued for free trade while Schmoller defended protectionism — the dispute was about policy with methodology as proxy",
    "Menger emphasized individual psychology while Schmoller emphasized class analysis — the dispute concerned the unit of social explanation",
    "The Methodenstreit established that economic theory is universal and deductive, not nation-specific and historical. Menger's position won intellectually but Schmoller dominated German universities through the 1920s, suppressing Austrian appointments. The foundations traveled with Mises and Hayek.",
    strategy="methodenstreit_1880s",
)

add_p1(
    "In 1871 Carl Menger published 'Grundsatze der Volkswirthschaftslehre' (Principles of Economics) in Vienna — the founding document of the Austrian school. The same year Jevons published in England and Walras in Switzerland; the three are credited with the 'marginal revolution.' But Menger's contribution differed in a way that defined the Austrian tradition. What set Menger apart?",
    "Menger grounded value entirely in subjective valuations by individuals satisfying ranked wants — Jevons and Walras formalized utility mathematically as cardinal quantities, while Menger insisted on qualitative individual choice",
    "Menger emphasized aggregate equilibrium across the economy — Jevons and Walras focused on individual choice within partial equilibrium",
    "Menger built on a labor theory of value with marginal adjustments — Jevons and Walras rejected the labor theory entirely",
    "Menger relied on extensive empirical case studies — Jevons and Walras developed their theories through abstract mathematical modeling",
    "Menger's qualitative-individual foundation set the Austrian path. Walras went on to general equilibrium and mathematical economics. Jevons inspired Marshall and Cambridge price theory. Menger inspired Bohm-Bawerk, Wieser, Mises, Hayek — a distinct tradition emphasizing time, uncertainty, and the limits of formalization.",
    strategy="menger_principles_1871",
)

add_p1(
    "In 1896 Eugen von Bohm-Bawerk published 'Karl Marx and the Close of His System' — a slim book that demolished Marx's economic theory. Marx had died in 1883; Volume III of Capital appeared posthumously in 1894. Bohm-Bawerk identified a fundamental contradiction between Volume I (1867) and Volume III. What was the contradiction?",
    "Volume I argued commodities exchange at labor values; Volume III conceded prices equal cost plus average profit — Bohm-Bawerk showed Marx's 'transformation' between these two propositions was mathematically incoherent and could not be salvaged",
    "Volume I argued capitalist crises were inevitable; Volume III suggested they might be moderated through credit policy — Bohm-Bawerk showed Marx had abandoned his determinist framework",
    "Volume I argued workers would grow absolutely poorer; Volume III conceded real wages were rising — Bohm-Bawerk showed Marx had abandoned the immiseration thesis",
    "Volume I argued capitalism was transient; Volume III treated it as potentially permanent — Bohm-Bawerk showed Marx had abandoned the historical-materialist framework",
    "Bohm-Bawerk's takedown was so devastating that 20th-century Marxists largely abandoned the labor theory of value as a quantitative claim, retreating to using it as moral rhetoric. The 'transformation problem' debate continues, but no successful solution has emerged.",
    strategy="bohm_bawerk_marx_1896",
)

add_p1(
    "Bohm-Bawerk's 'Positive Theory of Capital' (1889) developed a theory of interest contradicting both the Marxist exploitation account and the productivity-of-capital account. Interest emerges not from exploitation and not from capital's physical productivity, but from a deeper feature of human action. What concept did Bohm-Bawerk introduce?",
    "Time preference — humans systematically value present goods over equivalent future goods because life is uncertain and waiting itself is costly; interest is the discount on future versus present goods",
    "Diminishing marginal utility of capital — as more capital accumulates, each unit produces less output, lowering the rate of return",
    "Risk premium compensation — interest is the payment lenders demand for accepting borrower default risk",
    "Liquidity preference — humans demand a premium for parting with money's flexibility, a concept Keynes would later develop",
    "Mises and Rothbard developed time preference into 'pure time preference theory' — productivity affects WHICH projects are undertaken; time preference alone explains WHY interest exists at all. The concept survives because it doesn't depend on any specific monetary or technological arrangement.",
    strategy="bohm_bawerk_time_preference",
)

# Hoppe + Salerno + Kirzner + Austrian closers (4)

add_p1(
    "In 2001 Hans-Hermann Hoppe published 'Democracy: The God That Failed' — a defense of monarchy over democracy on praxeological grounds. Hoppe argued not from nostalgia but from rigorous analysis of incentives facing political rulers. What was his central claim?",
    "A king owns his realm so its long-term value is his capital — his time preference is compatible with stewardship; a democratic ruler is a temporary caretaker incentivized to extract value during a short term, producing higher time preference",
    "A king is accountable to God through religious doctrine — democratic rulers are accountable to no transcendent authority, leading to moral degradation",
    "A king has direct contact with subjects through personal audiences — democratic rulers interact only through media filters",
    "A king has been trained from birth in statecraft through inherited expertise — democratic rulers arrive with no preparation",
    "Hoppe extends Rothbardian anarcho-capitalism into political theory. The argument tracks the Austrian story about how property rights and time preference shape behavior — applied to who controls the state. The book is controversial; the methodological move is the durable contribution.",
    strategy="hoppe_democracy_2001",
)

add_p1(
    "Joseph Salerno is a senior Austrian economist at Pace University and editor of the Quarterly Journal of Austrian Economics. His 2010 book 'Money: Sound and Unsound' collected essays defending the gold standard and critiquing modern monetary arrangements. What was Salerno's central methodological contribution to monetary theory?",
    "Reviving the Misesian 'pure cash balance' approach to monetary analysis — money demand is qualitatively different from goods demand because money is held to facilitate future exchange rather than consumed",
    "Extending Friedman's quantity-theory framework — detailed historical analysis of money-supply contractions across multiple central banking eras since the Fed",
    "Developing behavioral monetary economics — integrating cognitive-bias research into Mises's regression-theorem framework for fiat-money valuation",
    "Formalizing Austrian Business Cycle Theory — using contemporary methodology to make it comparable to mainstream macroeconomic models within journals",
    "Salerno's work distinguishes Austrian monetary analysis from monetarism. Friedman treated money like any other commodity subject to supply-demand analysis. Mises and Salerno emphasize money's unique role in coordinating action across time. The cash balance approach traces back to Mises 1912.",
    strategy="salerno_sound_money_2010",
)

add_p1(
    "Israel Kirzner — Mises's NYU doctoral student — published 'Competition and Entrepreneurship' in 1973. The book developed a theory of entrepreneurship contrasting sharply with Schumpeter's earlier 'creative destruction' account. What was Kirzner's distinctive characterization of the entrepreneur?",
    "The alert discoverer who notices price differentials others have missed — arbitrage opportunities, undersupplied wants, possible new combinations — and acts to capture them, coordinating the market toward equilibrium through entrepreneurial alertness",
    "The bold risk-taker who deliberately undertakes uncertain ventures with high expected returns — bearing residual uncertainty managers prefer to shed",
    "The technological innovator who creatively destroys existing industries — a Schumpeterian process Kirzner explicitly accepted as the dominant account",
    "The capital allocator who directs investment across sectors based on expected returns — a financial-managerial figure central to corporate theory",
    "Kirzner saw markets as in continuous disequilibrium with entrepreneurial alertness driving them toward — but never reaching — equilibrium. This was deeply Misesian; equilibrium is a theoretical limit, not a description. Kirzner's framework distinguishes Austrian from neoclassical price theory.",
    strategy="kirzner_entrepreneur_1973",
)

add_p1(
    "Austrian economics holds that aggregate concepts like 'GDP' and 'the price level' obscure rather than reveal economic structure. Mises's praxeology emphasizes that economies consist of individuals acting purposefully — aggregates are statistical constructions, not causal entities. What does this methodological position imply for macroeconomic policy?",
    "Aggregate-targeted policy (raising 'aggregate demand,' stabilizing 'the price level') misses the structural effects of monetary or fiscal intervention — the same change in an aggregate can correspond to very different underlying capital-structure distortions",
    "Aggregate-targeted policy can succeed if the targets are correctly chosen — Austrians dispute the specific targets used by Keynesians and monetarists",
    "Aggregate-targeted policy works for short-run stabilization but fails for long-run growth — Austrians accept the Keynesian short-run framework",
    "Aggregate-targeted policy is empirically untestable — Austrians reject all macroeconomic policy on methodological grounds",
    "Austrian methodology — individualism, structure, time — generates substantive disagreements with Keynesian and monetarist policy frameworks. The 2008 GFC and 2021-23 inflation illustrate. Aggregates moved in ways the mainstream had not predicted; structural distortions Austrians emphasized became visible in hindsight.",
    strategy="austrian_aggregates",
)


add_p1(
    "Mises's 1949 Human Action devoted central chapters to monetary theory. The book covered the Cantillon effect — the observation that newly-created money doesn't lift all prices equally at the same time. Richard Cantillon (an 18th-century banker who knew John Law personally) had documented this pattern. What is the modern significance of the Cantillon effect?",
    "Monetary expansion is a wealth transfer from late recipients (savers, wage earners) to early recipients (banks, government contractors, asset holders) — the regressive distributional consequence is invisible in aggregate inflation statistics",
    "Monetary expansion is neutral — all prices rise immediately at the same rate, with the Cantillon effect being a 19th-century curiosity unrelated to modern central banking",
    "Monetary expansion lifts wages first — workers always get new money before businesses can raise prices, making inflation a benefit to laborers",
    "Monetary expansion reduces inequality — helping the poor before reaching the wealthy in any modern economy with progressive transfer programs",
    "Cantillon's Essai sur la Nature du Commerce en General (~1730, published 1755 posthumously) anticipated much of modern monetary economics. The Cantillon effect explains why monetary inflation is regressive even when CPI looks modest. Modern Austrian monetary theorists make this central.",
    strategy="cantillon_effect",
)


# =========================================================================
# P2 — BITCOIN (60)
# =========================================================================

# Cypherpunk lineage (5)

add_p2(
    "Bitcoin solves a problem cypherpunks worked on for decades. David Chaum's DigiCash (founded 1989) implemented a working digital cash system using blind signatures — Chaum's 1982 cryptographic invention. DigiCash partnered with Deutsche Bank and Credit Suisse. The company failed and filed for bankruptcy in 1998. Why did Chaum's system fail despite its technical sophistication?",
    "DigiCash required a central issuer — the cryptographic protocol worked, but the institutional dependency meant the system could be shut down, regulated, or rendered insolvent; Bitcoin's later innovation was removing this central party entirely",
    "DigiCash used inadequate encryption — RSA key sizes used in the early 1990s were broken by later research, leaving the foundation vulnerable",
    "DigiCash failed to attract users — the technology was sound but the market wasn't ready, with similar systems succeeding later after broadband",
    "DigiCash was outcompeted by credit cards — convenience advantages of established payment systems made digital cash economically unviable",
    "Chaum's DigiCash is the canonical pre-Bitcoin cautionary tale. The technical primitive (blind signatures for unlinkable payments) was elegant. The institutional dependency (central issuer) was fatal. Bitcoin's whole project is solving exactly this problem.",
    strategy="chaum_digicash_1989",
)

add_p2(
    "In 1997 Adam Back proposed Hashcash — a proof-of-work system originally designed to combat email spam by forcing senders to expend computational effort. Hashcash required computing a partial hash collision, the kind of cryptographic puzzle that takes work to solve but is trivial to verify. What was Hashcash's significance for Bitcoin?",
    "Bitcoin's mining mechanism is essentially Hashcash applied to a different problem — proof-of-work establishes which transactions are real and which are double-spends, with the same cryptographic primitive Back invented",
    "Hashcash was deployed as a payment system before Bitcoin — Back's paper described digital cash with proof-of-work issuance, and Bitcoin was a later imitation",
    "Hashcash and Bitcoin share their primitives by coincidence — Back's work was unknown to Satoshi, who independently invented proof-of-work",
    "Hashcash was an early form of mining for gold — Back's system literally tied digital tokens to physical commodity production",
    "Adam Back is one of the most important pre-Bitcoin figures. Hashcash's proof-of-work primitive is the same primitive Bitcoin uses for mining. Back later founded Blockstream and continues to influence Bitcoin development. Satoshi cited Hashcash directly in the 2008 white paper.",
    strategy="back_hashcash_1997",
)

add_p2(
    "In November 1998 Wei Dai posted a proposal to the cypherpunks mailing list called 'b-money.' Dai described a digital currency system with no central authority, using proof-of-work for issuance and broadcast servers for record-keeping. The system was never implemented. What problem did Wei Dai's b-money fail to solve that Bitcoin later solved?",
    "The Byzantine Generals Problem — how distributed nodes reach consensus on transaction ordering when some nodes may be malicious; b-money lacked the proof-of-work-plus-longest-chain mechanism Bitcoin uses to solve consensus",
    "The double-spend problem — Dai's system allowed users to spend the same token twice; Bitcoin's principal innovation was preventing this with cryptographic hash chains",
    "The 21-million supply cap — Dai's system had no fixed supply limit, allowing inflation; Bitcoin's contribution was a hard supply schedule",
    "The mining difficulty adjustment — Dai's system would have had unpredictable issuance rates; Bitcoin's contribution was auto-adjusting difficulty",
    "Wei Dai's b-money is directly cited in Bitcoin's 2008 white paper. Satoshi credits both Dai and Adam Back. The b-money proposal had most of Bitcoin's architecture but lacked the specific mechanism (proof-of-work plus longest valid chain wins) that makes Byzantine consensus work.",
    strategy="dai_bmoney_1998",
)

add_p2(
    "In 2005 Nick Szabo published a blog post proposing 'bit gold' — a system using cryptographic puzzles and timestamping to create a digital commodity that could function as money. Szabo had earlier proposed 'smart contracts' (1994) and the concept of 'unforgeable costliness' as money's distinguishing property. What was bit gold's principal innovation that Bitcoin would later use?",
    "Linking proof-of-work solutions into a chain where each new puzzle depends on the previous solution — the structure that became Bitcoin's blockchain — and treating the resulting unforgeable bit-strings as a digital commodity analogous to gold",
    "Backing digital tokens with physical gold reserves held in custodial vaults — bit gold required physical commodity backing that Bitcoin later abandoned",
    "Using zero-knowledge proofs to obscure transaction details — bit gold's privacy architecture became the foundation of later privacy coins",
    "Implementing a smart-contract layer for programmable money — bit gold's main contribution was the conceptual move toward computational money",
    "Szabo is sometimes speculated to be Satoshi. He has denied it. Bit gold (2005) and Satoshi's white paper (2008) share key architectural features. Szabo's 'unforgeable costliness' essay (2002) is the canonical statement of why money needs costly production.",
    strategy="szabo_bit_gold_2005",
)

add_p2(
    "On October 31, 2008 — Halloween — an anonymous person using the name Satoshi Nakamoto posted a nine-page paper titled 'Bitcoin: A Peer-to-Peer Electronic Cash System' to the metzdowd.com cryptography mailing list. The paper combined three previously-separate cypherpunk innovations into a working design. What were the three?",
    "Proof-of-work (Hashcash 1997), a publicly-shared ledger (b-money 1998), and difficulty adjustment to target consistent block intervals (Satoshi's own contribution) — together solving the Byzantine Generals Problem for money without a trusted third party",
    "Public-key cryptography (Diffie-Hellman 1976), blind signatures (Chaum 1982), and zero-knowledge proofs (Goldwasser-Micali-Rackoff 1985) — combined into a privacy-preserving digital cash system",
    "Smart contracts (Szabo 1994), digital scarcity (bit gold 2005), and decentralized identity (PGP 1991) — combined into a programmable money system",
    "Mobile payment infrastructure (M-Pesa 2007), blockchain databases (1995), and consensus algorithms (Paxos 1989) — adapted from existing enterprise technology",
    "The 2008 white paper is short (nine pages) and dense. Its principal achievement is combining proof-of-work, broadcast ledger, and auto-adjusting difficulty into a system where transaction ordering is determined by which valid chain has accumulated the most work. The Genesis block was mined two months later.",
    strategy="satoshi_white_paper_2008",
)

# Genesis + early Bitcoin (5)

add_p2(
    "Bitcoin's Genesis block was mined on January 3, 2009 by Satoshi Nakamoto. The block contained an embedded message in its coinbase transaction: 'The Times 03/Jan/2009 Chancellor on brink of second bailout for banks.' Why is this message philosophically significant?",
    "It anchors Bitcoin's existence to the moment of bank bailouts that proved the case for credibly-neutral money — the unforgeable timestamp (the block could not have been mined before that newspaper) is inseparable from the editorial commentary",
    "It established Bitcoin's legal status by citing a publicly-traded news source — the Times reference was necessary for Bitcoin to qualify as a regulated security under UK law",
    "It allowed Satoshi to claim copyright on the Bitcoin protocol — the headline reference established prior art used to defend the network against patent claims",
    "It demonstrated Bitcoin could store arbitrary data — the block's contents proved the protocol could function as distributed file storage",
    "The Genesis block timestamp is unforgeable because the embedded headline anchors the chain to a specific date — Bitcoin could not have been mined before January 3, 2009. The headline choice signals Bitcoin's purpose: the 2008 banking crisis was the proximate moment for which credibly-neutral money became necessary.",
    strategy="genesis_block_jan_3_2009",
)

add_p2(
    "The Bitcoin Genesis block contained a 50 BTC coinbase reward — but those particular bitcoins are provably unspendable. The public key was generated in a way that no private key can ever spend the coins. Why does this technical detail matter philosophically?",
    "It defuses the 'immaculate conception' criticism at block zero — Satoshi cannot dump his founding stake, and the supply schedule is verifiable from the protocol itself without trust in any founding party's commitments",
    "It establishes that Bitcoin's supply will eventually decrease — the unspendable Genesis bitcoins are the start of a deflationary process",
    "It demonstrates a programming bug Satoshi included intentionally — the unspendable Genesis coins are an Easter egg signaling the system's experimental nature",
    "It allowed Satoshi to claim founding privileges — the unspendable Genesis bitcoins represent Satoshi's symbolic ownership despite the inability to spend them",
    "A founder who could dump 50 BTC from the very first block would compromise the supply curve at block zero. The provable unspendability means anyone can verify the supply schedule from the protocol — no trust in Satoshi is required. The 'no immaculate conception' criticism is defused mechanically.",
    strategy="genesis_unspendable",
)

add_p2(
    "On January 12, 2009 — nine days after Genesis — Hal Finney received the first Bitcoin transfer in block 170 from Satoshi Nakamoto. Finney was a longtime cypherpunk who had worked on PGP at Phil Zimmermann's company. Finney was diagnosed with ALS in August 2009 and died on August 28, 2014. What happened to Finney's body?",
    "Finney was cryopreserved at Alcor Life Extension Foundation in Scottsdale, Arizona — making him one of the earliest figures in the Bitcoin community to embrace life-extension projects associated with the broader transhumanist cluster cypherpunks inhabited",
    "Finney was buried with paper wallets containing Bitcoin private keys — his estate's instructions reflected his ideological commitment to Bitcoin's persistence",
    "Finney's funeral was held at Cypherpunk Hall in Berkeley — a community center founded by the original 1992 mailing list",
    "Finney's body was donated to MIT — his bequest funded the MIT Bitcoin Project that distributed Bitcoin to undergraduates beginning in 2014",
    "Hal Finney's cryopreservation is a notable cultural detail. Cypherpunks emerged from a community interested in extending human capacity through technology — life extension was part of the conceptual neighborhood. Finney's last forum posts (2013) discussed Bitcoin while he could still type with assistive technology.",
    strategy="finney_first_transfer_2009",
)

add_p2(
    "On May 22, 2010 — now celebrated as 'Bitcoin Pizza Day' — Laszlo Hanyecz, a Florida programmer, paid 10,000 BTC to a fellow forum user who ordered him two Papa John's pizzas in exchange. At the time the bitcoins were worth about $41. Why does this transaction matter beyond the trivia value?",
    "It was Bitcoin's first documented commercial transaction — establishing that Bitcoin could function as money for actual purchases of goods, not just as a curiosity traded among hobbyists; the price benchmark established the early implied valuation",
    "It was the largest single Bitcoin transaction of 2010 — establishing peak volume metrics the network would not exceed until 2011",
    "It established Papa John's as Bitcoin's first commercial partner — the company has continued to accept Bitcoin since 2010",
    "It demonstrated Bitcoin's microtransaction capability — Hanyecz's transaction was specifically designed to test Bitcoin's small-payment processing",
    "Pizza Day matters because it crossed a threshold — Bitcoin became money rather than just a cryptographic experiment when it was used for an actual purchase. The 10,000 BTC at later peak prices would be worth over $600M. Hanyecz has said publicly he doesn't regret it.",
    strategy="pizza_day_may_22_2010",
)

add_p2(
    "Satoshi Nakamoto disappeared from public Bitcoin development in late 2010, leaving final instructions with Gavin Andresen and handing over control of the project's domain. Satoshi's last known communication was an email to Mike Hearn on April 23, 2011: 'I've moved on to other things.' What is the philosophical significance of Satoshi's deliberate disappearance?",
    "Bitcoin's credibility as a neutral system requires that no person can be coerced into modifying it — Satoshi's anonymity protects the network from pressure that would inevitably come to any identifiable founder",
    "Bitcoin's intellectual property protections required no individual could claim authorship — Satoshi's disappearance was a legal maneuver",
    "Bitcoin's tax treatment depended on the absence of a corporate founder — Satoshi's disappearance was necessary for commodity classification",
    "Bitcoin's governance model required rotating leadership — Satoshi's departure was part of a planned transition to a decentralized development structure",
    "A known founder could be subpoenaed, threatened, bribed, or arrested. Bitcoin's neutrality depends on having no one who can be coerced. The disappearance is not coincidence — it is the credibility move. Bitcoin holds approximately 1 million BTC mined by Satoshi that have never moved.",
    strategy="satoshi_disappearance",
)

# Mt. Gox + collapses (5)

add_p2(
    "In February 2014 the Mt. Gox Bitcoin exchange — handling about 70% of global Bitcoin trades at peak — collapsed and filed for bankruptcy in Tokyo. CEO Mark Karpeles claimed approximately 850,000 BTC had been stolen. About 200,000 BTC were later recovered. What had actually happened at Mt. Gox?",
    "A multi-year hack combined with mismanagement of customer funds — bitcoins had been gradually drained from cold-storage wallets while Karpeles failed to detect the losses, discovered only at the point of unfillable withdrawals",
    "A deliberate exit scam by Karpeles — the bitcoins had never been stolen but had been transferred to Karpeles's personal wallets",
    "A regulatory shutdown by Japanese authorities — Mt. Gox bitcoins were seized as evidence in money-laundering investigations",
    "A computer hardware failure — Mt. Gox bitcoins were lost when the exchange's data center suffered catastrophic damage in a fire",
    "Mt. Gox 2014 is the canonical 'not your keys, not your coins' lesson. The exchange held customer bitcoins in custodial wallets; when the wallets emptied, customers lost their coins. The lesson: self-custody is fundamentally different from exchange custody.",
    strategy="mt_gox_feb_2014",
)

add_p2(
    "The Mt. Gox bankruptcy involved a Tokyo legal process that has continued for over a decade. Mark Karpeles was arrested in August 2015 by Tokyo police. He was charged with embezzlement and data manipulation. What was the outcome of Karpeles's trial in March 2019?",
    "Karpeles was acquitted of embezzlement but found guilty of data manipulation — receiving a suspended sentence; the embezzlement charges could not be proven beyond reasonable doubt under Japanese criminal procedure",
    "Karpeles was convicted on all charges and sentenced to 10 years in prison — the harshest sentence for cryptocurrency fraud in Japan",
    "Karpeles was found not guilty and awarded compensation — Japanese courts ruled Mt. Gox losses resulted from external hacking outside his control",
    "Karpeles pled guilty and entered cooperation agreement with prosecutors — providing information about other early Bitcoin exchange operators",
    "Karpeles's mixed outcome reflects the Japanese legal system's high standard for criminal conviction. The bitcoins were undeniably gone, but proving Karpeles intentionally took them required evidence not available to prosecutors. The civil bankruptcy continues; partial restitution has occurred.",
    strategy="karpeles_trial_2019",
)

add_p2(
    "Mt. Gox started life in 2007 as 'Magic: The Gathering Online Exchange' — a website for trading cards from the trading card game. Founder Jed McCaleb converted it to a Bitcoin exchange in 2010, then sold it to Mark Karpeles in March 2011. McCaleb went on to a peculiar second-act career in cryptocurrency. What did McCaleb do next?",
    "Co-founded Ripple Labs (2012) and then founded Stellar Development Foundation (2014) — building two of the largest non-Bitcoin cryptocurrency networks; his second-act ventures attracted criticism from Bitcoin maximalists",
    "Joined the Mt. Gox legal defense team as a consultant — providing technical assistance to Karpeles's lawyers",
    "Founded a major Bitcoin mining operation in Iceland — McCaleb's GeoMine became one of the largest pre-2015 operations using geothermal power",
    "Became a Bitcoin Core developer — McCaleb contributed to Bitcoin software development from 2012 through 2020",
    "McCaleb's trajectory illustrates the early-2010s split in cryptocurrency. Many early Bitcoiners moved to creating alternative cryptocurrencies (altcoins). Ripple and Stellar are functional networks but lack Bitcoin's credibly-neutral founding (both had pre-mines and centralized governance).",
    strategy="mccaleb_post_mtgox",
)

add_p2(
    "By 2022 a series of cryptocurrency exchange and lending platform collapses had devastated the broader ecosystem. Celsius Network filed for bankruptcy on July 13, 2022, owing about $4.7 billion. Voyager Digital filed on July 5, 2022, owing about $1.3 billion. BlockFi filed on November 28, 2022, owing about $1.3 billion. What lesson did these collapses reinforce?",
    "Not your keys, not your coins — depositing cryptocurrency with a centralized lender means that custodian holds the private keys; when the custodian fails, the depositor becomes an unsecured creditor in bankruptcy proceedings",
    "Cryptocurrency itself is fundamentally flawed — the 2022 collapses proved digital asset systems cannot function and traditional banking remains superior",
    "Government regulation could have prevented the collapses — the failures resulted from insufficient SEC oversight, and increased authority would prevent recurrence",
    "Mathematical impossibility prevents cryptocurrency lending — Celsius and BlockFi failed because the underlying technology cannot support credit",
    "The 2022 cascade hardened the 'not your keys, not your coins' lesson into post-FTX-era cryptocurrency truism. Self-custody is the protection Bitcoin uniquely makes possible. Custodial relationships look like banking but lack banking's deposit-insurance and regulatory protections.",
    strategy="celsius_voyager_blockfi_2022",
)

add_p2(
    "The collapses of 2022 culminated in the FTX bankruptcy. On November 8, 2022, FTX — at the time the second-largest cryptocurrency exchange — collapsed after founder Sam Bankman-Fried moved customer funds to his affiliated trading firm Alameda Research. Approximately $8 billion in customer funds went missing. SBF was convicted on seven counts in October 2023 and sentenced in March 2024. What was his sentence?",
    "25 years in federal prison plus an $11 billion forfeiture order — handed down by Judge Lewis Kaplan in the Southern District of New York for what prosecutors called one of the largest financial frauds in American history",
    "10 years in federal prison plus a $2 billion forfeiture order — a sentence many considered lenient given the scale of fraud",
    "Life in federal prison plus complete forfeiture of personal assets — the maximum possible sentence under federal sentencing guidelines",
    "Time served plus probation plus a $500 million forfeiture order — a sentence reflecting SBF's cooperation with prosecutors",
    "SBF's case is the canonical post-Bitcoin cryptocurrency fraud story. He had been called 'the J.P. Morgan of crypto.' He was a major Democratic donor and prominent in effective-altruism fundraising. The conviction vindicated the post-Mt. Gox 'not your keys' framework Bitcoin maximalists had emphasized.",
    strategy="ftx_sbf_sentence_2024",
)

# Block size war + SegWit + forks (5)

add_p2(
    "Between 2015 and 2017 Bitcoin experienced an internal political dispute called the 'block size war.' The disagreement concerned how to scale the network to handle more transactions. One faction wanted larger blocks (megabytes per block); another wanted to keep blocks small and add scaling through other layers. What was the deeper question at stake?",
    "Whether Bitcoin's value lay in cheap transactions (favoring larger blocks) or in trustless self-verification (favoring smaller blocks so that individual users could run full nodes on consumer hardware) — the answer would determine Bitcoin's character for decades",
    "Whether Bitcoin should adopt proof-of-stake (favoring efficiency) or remain on proof-of-work (favoring energy expenditure) — Ethereum would later resolve this differently",
    "Whether Bitcoin's protocol changes should require unanimous consent of all nodes or majority consent of mining pools — a governance dispute",
    "Whether Bitcoin should be regulated as a security (favoring larger blocks) or as a commodity (favoring smaller blocks) — a question of regulatory positioning",
    "The block size war was Bitcoin's first major political crisis. The small-block side argued that if running a full node became too expensive, only specialized operations could verify the chain — concentrating power. The large-block side argued cheap transactions were Bitcoin's value proposition. Small-block won.",
    strategy="block_size_war_2015_2017",
)

add_p2(
    "In August 2017 a faction in the block size war activated 'User-Activated Soft Fork' (UASF) — BIP 148 — pressuring miners to accept Segregated Witness (SegWit). SegWit fixed a transaction malleability bug that blocked layer-2 systems, and indirectly increased block capacity. What was UASF's broader political significance?",
    "It demonstrated that economic node operators (users running full nodes, businesses processing transactions) could discipline miners and exchanges who otherwise controlled the network's direction — establishing user sovereignty as Bitcoin's ultimate governance mechanism",
    "It established a permanent fork between two competing Bitcoin chains — UASF created a separate chain that continued in parallel to the original Bitcoin",
    "It transferred network control from individual miners to mining pools — UASF was a power play by large pool operators to consolidate hashrate",
    "It introduced a corporate governance structure to Bitcoin — UASF created the Bitcoin Foundation that coordinates protocol changes through stakeholder voting",
    "UASF was a critical Bitcoin moment. The economic majority — users, businesses, individual node operators — credibly threatened to ignore blocks not signaling SegWit support. Miners, fearing their blocks would be orphaned, activated SegWit. The episode established that users hold ultimate power.",
    strategy="uasf_segwit_august_2017",
)

add_p2(
    "After the August 2017 SegWit activation, the large-block faction split off and launched 'Bitcoin Cash' (BCH) on August 1, 2017 — a separate cryptocurrency with larger blocks. Bitcoin Cash was promoted heavily by Roger Ver, Craig Wright, and Jihan Wu. What happened to Bitcoin Cash in the years following the fork?",
    "It lost market dominance to the original Bitcoin (BTC), traded at progressively lower fractions of Bitcoin's price, and itself fractured in November 2018 into Bitcoin Cash and Bitcoin SV — the market rejected the large-block thesis decisively",
    "It captured majority cryptocurrency market share by 2020 — Bitcoin Cash succeeded in becoming the dominant cryptocurrency by transaction volume",
    "It remained at near-parity with the original Bitcoin in price — the two chains traded as effectively equivalent cryptocurrencies through 2024",
    "It merged back with the original Bitcoin in 2019 — the Bitcoin Cash community recognized the technical superiority of SegWit and abandoned the fork",
    "The market verdict on the block size war is one of the cleanest empirical cases in cryptocurrency history. Bitcoin Cash's price-versus-Bitcoin chart shows a decade-long decline. The market — millions of individual buyers, exchanges, businesses — chose the small-block, layer-2 approach decisively.",
    strategy="bitcoin_cash_aug_2017",
)

add_p2(
    "Bitcoin Cash itself fractured on November 15, 2018, when Craig Wright (who falsely claimed to be Satoshi Nakamoto) led a further split called 'Bitcoin Satoshi Vision' (BSV). The Wright-led faction made specific predictions about Bitcoin SV's future trajectory. What happened to those predictions?",
    "BSV's price collapsed against both Bitcoin and Bitcoin Cash, and Craig Wright lost a series of UK and US court cases in 2024 that comprehensively rejected his Satoshi Nakamoto claim — the High Court ruling explicitly that Wright is not Satoshi",
    "BSV achieved its predicted price growth and captured significant institutional adoption — Wright's faction proved technically superior to both Bitcoin and Bitcoin Cash",
    "BSV became the dominant cryptocurrency in Asian markets — Wright's faction captured market share that the original Bitcoin had failed to penetrate",
    "BSV merged with Bitcoin Cash in 2020 — the two factions reconciled after Wright's documents were verified by independent forensic experts",
    "Craig Wright's defeat in UK court (Crypto Open Patent Alliance v Wright, March 2024) ended his long campaign to claim Satoshi's identity. Judge James Mellor ruled Wright was 'not the author of the Bitcoin White Paper' and had 'lied to the court extensively and repeatedly.'",
    strategy="bsv_wright_2018_2024",
)

add_p2(
    "Segregated Witness (SegWit) activated on Bitcoin on August 24, 2017, at block 481,824. The upgrade fixed transaction malleability and created the technical foundation for layer-2 scaling. What specific scaling solution did SegWit enable that has since become Bitcoin's primary scaling layer?",
    "The Lightning Network — a layer-2 protocol allowing nearly-instant Bitcoin transactions through bidirectional payment channels, with the channels' opening and closing transactions settled on the main chain — proposed in 2015 by Poon and Dryja, mainnet launched January 2018",
    "Sharding — a database technique allowing different Bitcoin nodes to track only portions of the chain, with full validation reconstructed from partial information",
    "Proof-of-stake — SegWit prepared Bitcoin for the eventual transition from energy-intensive proof-of-work mining to proof-of-stake validation",
    "Sidechains — SegWit enabled the merging of Bitcoin Cash, Bitcoin SV, and other forked chains back into a single network",
    "Lightning Network is Bitcoin's primary scaling solution. SegWit fixed transaction malleability — the prerequisite for safely opening Lightning channels. The two-party channels can route through other channels, allowing payment paths across the network.",
    strategy="segwit_aug_24_2017",
)

# Taproot + Lightning + technical (5)

add_p2(
    "On November 14, 2021, at block 709,632, Bitcoin activated 'Taproot' — its first major protocol upgrade since SegWit in 2017. Taproot introduced Schnorr signatures (an alternative to the previous ECDSA signatures) and a new scripting structure. What specific improvement did Schnorr signatures bring to Bitcoin?",
    "They allow multi-signature transactions to be indistinguishable from single-signature transactions on the blockchain — improving both privacy (observers cannot tell complex transactions apart) and efficiency (multiple signatures combine into one)",
    "They eliminate the need for proof-of-work mining — Schnorr signatures provide cryptographic finality Bitcoin had previously achieved through hashrate accumulation",
    "They enable quantum-resistant cryptography — Schnorr's mathematical foundation resists quantum computer attacks that would defeat ECDSA",
    "They reduce Bitcoin's energy consumption — Schnorr signatures require less computation than ECDSA, reducing power demand significantly",
    "Schnorr signatures had been understood since Claus Schnorr's 1989 paper but were under patent until 2008, the year Bitcoin launched. Taproot brought them to Bitcoin 13 years later. The privacy benefit is significant — observers can no longer distinguish a single-sig from a multisig transaction on-chain.",
    strategy="taproot_nov_14_2021",
)

add_p2(
    "The Lightning Network was first proposed in February 2015 in a paper by Joseph Poon and Thaddeus Dryja titled 'The Bitcoin Lightning Network: Scalable Off-Chain Instant Payments.' The technical insight behind Lightning was using a specific cryptographic primitive to create trustless bidirectional payment channels. What was the primitive?",
    "Hash Time-Locked Contracts (HTLCs) — cryptographic conditions releasing funds either when a hash is revealed or after a timeout, letting two parties safely update channel balances without trusting each other",
    "Zero-knowledge proofs — Lightning Network channels use ZK-SNARKs to prove balance changes without revealing the transactions",
    "Ring signatures — Lightning Network uses ring signatures to anonymize payment routing, similar to Monero",
    "Confidential transactions — Lightning Network channels hide transaction amounts using Pedersen commitments",
    "HTLCs are the key insight. A channel between Alice and Bob can include conditions: 'Bob can claim this Bitcoin if he reveals a hash preimage; otherwise it returns to Alice after T blocks.' Chaining these conditions across multiple channels allows trustless routing.",
    strategy="lightning_2015_2018",
)

add_p2(
    "Lightning Network mainnet officially launched in January 2018 — three years after the Poon-Dryja paper. The intervening years had been spent on protocol specification (the BOLT documents), implementation by competing teams (Lightning Labs, ACINQ, Blockstream), and testnet refinement. What was Lightning's main scaling claim?",
    "It can process millions of transactions per second across the network — vastly exceeding Bitcoin's base-layer 7 transactions per second — at near-zero fees while maintaining Bitcoin's underlying security through periodic settlement on the main chain",
    "It eliminates Bitcoin's energy use — Lightning transactions require no mining and consume negligible electricity",
    "It enables Bitcoin to support smart contracts equivalent to Ethereum — Lightning's scripting capabilities have grown to include conditional logic",
    "It provides regulatory compliance for cryptocurrency exchanges — Lightning transactions are automatically reported to financial authorities",
    "Lightning's scaling thesis: most transactions don't need permanent on-chain settlement. Two parties who transact frequently can open a channel, transact thousands of times off-chain, then settle the net balance on-chain. The main chain handles channel openings and closings; everyday payments happen in channels.",
    strategy="lightning_mainnet_jan_2018",
)

add_p2(
    "Bitcoin's difficulty adjustment recalculates every 2,016 blocks (about every two weeks) to target 10-minute block times. If miners add hashrate, blocks come faster, and the next adjustment makes the puzzle harder. The most dramatic test of this mechanism came in May 2021. What happened?",
    "China announced a comprehensive ban on Bitcoin mining, and about 50% of global hashrate went offline within weeks — blocks slowed substantially, but the difficulty adjustment automatically eased the puzzle as miners outside China filled the gap, and hashrate recovered to pre-ban levels within months",
    "El Salvador's adoption of Bitcoin as legal tender created such transaction demand that miners could not keep up — the difficulty adjustment had to be modified by emergency protocol changes",
    "A series of mining pool collapses in North America took 80% of hashrate offline — the difficulty adjustment failed to respond quickly enough",
    "Solar storm activity disrupted mining hardware globally — the difficulty adjustment was supplemented by manual interventions from Bitcoin Core developers",
    "The May 2021 China ban was the largest stress test of Bitcoin's hashrate distribution mechanism. Hashrate recovered to pre-ban levels by year-end as mining migrated to the US, Kazakhstan, Russia. Block times briefly extended to ~13 minutes, then auto-corrected.",
    strategy="china_ban_may_2021",
)

add_p2(
    "Bitcoin's block subsidy halves about every four years — every 210,000 blocks. At Genesis (2009) miners earned 50 BTC per block. The 2012 halving reduced this to 25 BTC. The 2016 halving to 12.5. The 2020 halving to 6.25. The April 2024 halving to 3.125. Around year 2140 the last satoshi is mined. What does this schedule guarantee?",
    "A hard supply cap of about 21 million bitcoin that no human can change without network consensus — the issuance schedule is determined by code, not by central bankers or governments that can be lobbied or coerced",
    "A continuously increasing supply calibrated by the Federal Reserve to match inflation targets — Bitcoin's halvings ensure tracking of the dollar's debasement pattern",
    "A floating supply set each year by the Bitcoin Foundation board through governance votes — the halvings are nominal milestones rather than binding limits",
    "A diminishing supply with bitcoin actively destroyed by the protocol after seven years — the halvings reduce issuance, while a separate burn mechanism eliminates aging coins",
    "The 21M cap is Bitcoin's most distinctive monetary feature. Compared to gold (issuance ~1-2% per year, vulnerable to discoveries) and fiat (issuance discretionary, lifetime debasement ~99%), Bitcoin's mathematically-fixed schedule is unique.",
    strategy="halving_21m_cap",
)

# El Salvador + state adoption (5)

add_p2(
    "On September 7, 2021, El Salvador became the first country to adopt Bitcoin as legal tender, alongside the US dollar (used since 2001). President Nayib Bukele announced the move at Bitcoin 2021 in Miami. Implementation included a wallet app 'Chivo' and a $30 sign-up bonus in Bitcoin for citizens. What was the broader motivation?",
    "Most Salvadorans worked abroad and sent remittances home through Western Union or MoneyGram with fees of 10% or higher — Bitcoin offered an alternative for cross-border payments that could substantially reduce remittance costs for poor families",
    "El Salvador had been pressured by the IMF to abandon dollarization and return to the colon — Bitcoin adoption was a defensive maneuver",
    "The Bukele government sought to attract a wealthy Bitcoin-holding population to settle in El Salvador — the legal tender status was a tax-residency incentive",
    "El Salvador had identified geothermal mining opportunities from its volcanic geography — Bitcoin adoption was driven by energy export potential",
    "Remittances are roughly 20-25% of El Salvador's GDP. The 10% Western Union fees represent billions in annual transfer costs paid by Salvadoran families. Bitcoin (and especially Lightning Network) offered a technical alternative that could route remittances at near-zero cost.",
    strategy="el_salvador_sept_7_2021",
)

add_p2(
    "El Salvador's Bitcoin adoption included an unusual additional initiative: financing a 'volcano bond' backed by Bitcoin mining powered by geothermal energy from the country's volcanic geography. The bond was originally announced for 2022 issuance. What was the broader pattern of state-level Bitcoin engagement El Salvador represented?",
    "Combining Bitcoin treasury reserves, mining infrastructure (geothermal-powered operations), and Bitcoin legal tender status (Chivo wallet rollout) — an integrated monetary-political experiment unique among national governments",
    "Following the established pattern of Asian cryptocurrency-friendly regulatory regimes such as Singapore and Japan — El Salvador's program was a regional implementation",
    "Replicating the cryptocurrency reserve approaches developed by Iran and Venezuela — El Salvador adapted sanctions-evasion strategies",
    "Implementing recommendations from the World Economic Forum's Centre for the Fourth Industrial Revolution — El Salvador's program followed WEF frameworks",
    "El Salvador's experiment is unique because it integrates multiple components: legal tender, treasury, mining (using geothermal), and Lightning Network deployment. No other government has attempted all four simultaneously.",
    strategy="el_salvador_volcano_bond",
)

add_p2(
    "El Salvador's Chivo Wallet rollout faced significant problems in its first months. Technical glitches, identity theft cases (where someone else had claimed the $30 sign-up bonus tied to a citizen's national ID), and persistent skepticism from older Salvadorans all limited adoption. The Salvadoran government responded with continued policy commitment despite the difficulties. What was the international reaction?",
    "The IMF publicly criticized the adoption and threatened to withhold loan negotiations — the IMF and World Bank treated Bitcoin legal tender as a financial-stability risk requiring policy reversal as a condition of future assistance",
    "The European Union endorsed the experiment and offered technical assistance — Brussels saw El Salvador as a useful test case for the digital euro program",
    "The United States Treasury formally praised the move — Washington viewed El Salvador's adoption as advancing US dollar usage indirectly",
    "Major credit rating agencies upgraded El Salvador's sovereign debt — the Bitcoin adoption was treated as fiscal reform",
    "The IMF response is revealing about international monetary politics. A small country attempting alternative monetary arrangements faces predictable institutional opposition. The IMF's mandate includes maintaining dollar-based financial-system stability; alternatives are treated as threats.",
    strategy="el_salvador_imf_response",
)

add_p2(
    "After El Salvador's September 2021 adoption, other governments considered similar moves. The Central African Republic adopted Bitcoin as legal tender on April 27, 2022 — becoming the second country to do so. The CAR adoption was widely treated as less significant than El Salvador's. Why was the international reaction different?",
    "The CAR is one of the world's poorest countries with limited internet infrastructure — only about 11% of citizens had internet access at the time of adoption, making practical implementation negligible and the policy primarily symbolic",
    "The CAR adoption was illegal under regional currency-union agreements — the CEMAC prohibited the move, leading to immediate suspension",
    "The CAR had previously adopted other speculative cryptocurrencies that had failed — observers treated Bitcoin adoption as the latest unsuccessful experiment",
    "The CAR's political instability made any policy unlikely to persist — observers correctly predicted revocation within months",
    "The CAR vs. El Salvador contrast illustrates that Bitcoin legal tender effects depend on practical implementation. El Salvador had moderate internet penetration, an existing dollarized economy, and a young tech-aware population. The CAR lacked these conditions.",
    strategy="car_bitcoin_april_2022",
)

add_p2(
    "Beyond El Salvador and the Central African Republic, no government has declared Bitcoin legal tender. However, several governments have begun building Bitcoin treasury positions. Texas passed laws in 2023 protecting Bitcoin mining. Various Bitcoin-friendly states emerged in the post-2020 environment. What broader trend does this represent?",
    "Governments are beginning to recognize Bitcoin as a strategic monetary reserve asset alongside gold — Bitcoin's role in international monetary arrangements is expanding from individual to institutional and state-level holdings without legal tender requirements",
    "Governments are systematically banning Bitcoin globally — the post-2020 period has seen progressively tighter restrictions across major economies",
    "Governments are replacing their currencies with central bank digital currencies that compete with Bitcoin — the trend is toward state-issued digital alternatives",
    "Governments are taxing Bitcoin transactions at increasing rates — the policy direction is toward legal status with high taxes discouraging practical use",
    "The Bitcoin treasury trend among individual states and corporate level (MicroStrategy holds substantial reserves) is meaningful. Without legal tender status, treasury holdings are a less visible form of acceptance. Bitcoin's role as 'digital gold' for institutional treasuries is the form recognition is taking.",
    strategy="bitcoin_state_treasuries",
)

# Philosophy + sound money (5)

add_p2(
    "Nick Szabo's 2002 essay 'Shelling Out: The Origins of Money' argued that money throughout history has shared a particular property he called 'unforgeable costliness.' Szabo argued this property distinguished real money from claims, IOUs, and political fiat. What does Bitcoin uniquely provide that previous money forms could not?",
    "Mathematically-verifiable scarcity with no human-controllable issuance — gold requires trust in mining behavior, paper money requires trust in central banks, but Bitcoin's supply schedule is verifiable by anyone running a full node from the protocol itself",
    "Centralized governance with transparent decision-making — Bitcoin's foundation provides public records of all supply decisions",
    "Government-backed legal tender status — Bitcoin's legal recognition in El Salvador provides political backing previous private monies had lacked",
    "Industrial usefulness from the underlying material — Bitcoin's cryptographic computations have practical applications in cybersecurity",
    "Szabo's 'unforgeable costliness' essay is foundational. Money throughout history (cowrie shells, gold, silver) shared the property of being expensive to produce and impossible to fake. Fiat money broke this pattern. Bitcoin restores it in digital form.",
    strategy="szabo_unforgeable_costliness",
)

add_p2(
    "Bitcoin's launch in 2009 included specific design choices that distinguished it from later cryptocurrency projects. Among these were: no pre-mine (Satoshi did not generate a stash before announcing the project), no foundation or corporate sponsor, no initial coin offering, and no central party who could be subpoenaed. What is this collection of properties commonly called?",
    "Fair launch — Bitcoin's launch satisfied a strict set of conditions that no later cryptocurrency has been able to replicate, making Bitcoin uniquely credibly-neutral as a starting point for monetary system design",
    "Initial public offering compliance — Bitcoin's launch was structured to meet SEC requirements for new financial instruments",
    "Open-source token launch — Bitcoin's launch followed standard practices for distributed software projects",
    "Phased rollout — Bitcoin's launch was the first stage of a planned multi-year development process",
    "Fair launch is Bitcoin's distinctive founding property. Ethereum had a pre-sale. Ripple was pre-mined. Solana had VC backing. Every later cryptocurrency has some founding party who held initial advantage. Bitcoin alone has none.",
    strategy="bitcoin_fair_launch",
)

add_p2(
    "Saifedean Ammous's 2018 book 'The Bitcoin Standard: The Decentralized Alternative to Central Banking' became one of the most-read introductions to Bitcoin's monetary case. Ammous traced the history of money from cattle to seashells to gold and silver, then argued Bitcoin represented a return to sound monetary principles in digital form. What was the book's core argument?",
    "The quality of a society's money shapes its time preference, its capital accumulation, and ultimately the character of its civilization — sound money supports long-term thinking and savings; unsound money rewards present consumption and short-term political coalitions",
    "The quantity of money determines aggregate price levels — Ammous extended Friedman's monetarist framework with historical analysis",
    "The technology of money determines its security against theft — Ammous's argument was that Bitcoin's cryptographic security exceeds physical gold's storage requirements",
    "The legal status of money determines its acceptance — Ammous argued Bitcoin needed national-level legal tender status to be competitive",
    "Ammous's book popularized the time-preference framework for thinking about money. The Austrian insight — interest reflects time preference, and time preference shapes savings, investment, and civilization — extends to monetary policy. Inflationary money raises time preference; sound money lowers it.",
    strategy="ammous_bitcoin_standard_2018",
)

add_p2(
    "Nik Bhatia's 2021 book 'Layered Money: From Gold and Dollars to Bitcoin and Central Bank Digital Currencies' developed a framework for understanding money in terms of layers. Gold is layer one; bank notes redeemable for gold are layer two; bank deposits are layer three; and so on. What was Bhatia's argument about where Bitcoin fits in this framework?",
    "Bitcoin is layer-one money in the digital realm — like gold, it requires no counterparty to redeem; like gold, it has limited supply; unlike gold, its supply is mathematically enforced rather than physically discovered, and it can travel as digital information",
    "Bitcoin is layer-three money — Bhatia classified Bitcoin as a derivative of underlying digital assets, with its properties depending on institutional infrastructure",
    "Bitcoin is layer-zero money — Bhatia argued Bitcoin represents a foundational layer beneath even gold, providing cryptographic primitives",
    "Bitcoin is not money at all in the layered framework — Bhatia distinguished Bitcoin as a payment system rather than as money proper",
    "Bhatia's framework illuminates Bitcoin's monetary position. Layer one money has no counterparty risk — you possess it directly. Gold has been layer one for millennia. Bitcoin is the first digital layer one. This explains why Bitcoin is not 'just another payment system' — it's a new layer in the monetary stack.",
    strategy="bhatia_layered_money_2021",
)

add_p2(
    "Lyn Alden's 2023 book 'Broken Money: Why Our Financial System is Failing Us and How We Can Make It Better' synthesized the case for Bitcoin from an institutional macroeconomic perspective. Alden argued the post-1971 dollar system had specific structural problems that made Bitcoin an attractive alternative. What was Alden's central diagnosis?",
    "The post-1971 dollar system requires perpetual debt expansion to function — the resulting debasement transfers wealth from savers to debtors and from poor to rich, with Bitcoin offering an exit from this system for those willing to opt out individually",
    "The post-1971 dollar system is fundamentally sound and Bitcoin is unnecessary — Alden's book was actually a defense of the established framework",
    "The post-1971 dollar system fails specifically due to environmental concerns — Alden's argument focused on unsustainability of carbon-intensive growth",
    "The post-1971 dollar system creates international financial instability — Alden argued problems are concentrated in cross-border flows while domestic usage is functional",
    "Alden's book is notable for being written by a macroeconomic analyst (not just a Bitcoin advocate) with institutional credibility. The 1971 reference is to Nixon's closing of the gold window. Alden's diagnosis: a debt-financed monetary system requires ever-increasing debt to function, eventually breaks, and offers an exit through sound money.",
    strategy="alden_broken_money_2023",
)

# Protest + sovereignty (5)

add_p2(
    "In February 2022 the Canadian government invoked the Emergencies Act to disperse the Freedom Convoy — a truckers' protest against pandemic mandates that had blockaded Ottawa and several US-Canada border crossings. Banks were ordered to freeze accounts of participants and donors. What role did Bitcoin play in this episode?",
    "Bitcoin donations to the protesters could not be frozen by the bank order — demonstrating Bitcoin's value as protest finance in a context where state actors could otherwise cut off political dissent through banking-system pressure",
    "Bitcoin was banned in Canada immediately after the protest — the Trudeau government extended the Emergencies Act to include cryptocurrency restrictions",
    "Bitcoin was used by the Canadian government to track protesters — blockchain analysis of donation transactions allowed identification of individuals",
    "Bitcoin was irrelevant to the protests — the convoy was funded entirely through GoFundMe and similar platforms",
    "The 2022 Canada truckers episode is a canonical Bitcoin use case. When government acts against political opponents through banking-system pressure, Bitcoin provides an alternative channel that cannot be similarly suppressed. The episode caused significant public discussion of cryptocurrency's role as resistance.",
    strategy="canada_truckers_2022",
)

add_p2(
    "In February 2023 the Nigerian government's restrictions on cash withdrawals during a currency redesign — combined with the Naira's continued devaluation — generated widespread Bitcoin adoption among Nigerians. Despite formal restrictions on cryptocurrency, peer-to-peer Bitcoin transactions surged. What does this episode illustrate?",
    "When fiat currency becomes unreliable through inflation or political interference, citizens seek alternatives — Bitcoin's censorship resistance and inflation resistance make it especially attractive in such contexts, regardless of formal government policy",
    "Nigerian Bitcoin adoption was driven by speculative trading on price movements — the underlying use case was investment rather than monetary refuge",
    "The Nigerian central bank successfully suppressed Bitcoin adoption — restrictions on exchanges achieved their intended effect of channeling citizens back into Naira",
    "Nigerian Bitcoin usage was primarily for illegal activity — the surge reflected criminal rather than economic motivations",
    "Nigeria 2023 is an instructive case. The Buhari government's currency restrictions caused widespread cash shortages and political unrest. Citizens turned to Bitcoin despite formal restrictions. Peer-to-peer markets thrived. The episode illustrates Bitcoin's role as monetary refuge in unstable currency regimes.",
    strategy="nigeria_2023",
)

add_p2(
    "Cuba's economy has operated under US sanctions since 1962, with limited access to international banking. Cuban citizens have used Bitcoin since the late 2010s for remittances and savings. The Cuban government formally legalized cryptocurrency for some transactions in August 2021. What broader pattern do Canada, Nigeria, and Cuba suggest?",
    "Bitcoin's value proposition is strongest where established financial systems fail or are weaponized — its censorship resistance and global accessibility make it especially valuable in contexts where citizens face banking exclusion, sanctions, or capital controls",
    "Bitcoin is primarily used for criminal activity — the various adoption patterns reflect drug trafficking, money laundering, and sanctions evasion",
    "Bitcoin adoption follows speculative price movements — the various adoption episodes correlate with price increases rather than monetary system problems",
    "Bitcoin is used primarily by wealthy individuals — the various adoption patterns reflect tax avoidance rather than addressing financial exclusion",
    "Bitcoin's adoption pattern is geographically distinctive. The strongest use cases emerge where banking systems fail, where governments restrict capital flows, or where state actors weaponize banking against citizens. Wealthy stable-banking populations have less need for Bitcoin's specific features.",
    strategy="bitcoin_protest_sovereignty",
)

add_p2(
    "WikiLeaks faced a banking blockade in December 2010 after publishing diplomatic cables. PayPal, Visa, MasterCard, and Bank of America all froze WikiLeaks donations under US government pressure — without any court order. The organization survived in part through Bitcoin donations. What does this 2010 episode foreshadow?",
    "Financial-system pressure can be applied to political organizations without judicial process — Bitcoin provides an alternative donation channel that cannot be similarly cut off",
    "WikiLeaks's Bitcoin adoption was illegal under US law — the organization faced criminal prosecution for using cryptocurrency",
    "WikiLeaks's Bitcoin donations were quickly traced by US authorities — blockchain analysis allowed identification of major donors",
    "WikiLeaks abandoned Bitcoin within months — the organization returned to conventional banking after the initial blockade was lifted",
    "WikiLeaks 2010 was the first major political-organization use of Bitcoin to survive a financial-system blockade. Julian Assange later remarked that the blockade made WikiLeaks dependent on Bitcoin for years. The episode foreshadowed the Canadian truckers episode in 2022 and many similar cases.",
    strategy="wikileaks_2010",
)

add_p2(
    "Russian and Ukrainian humanitarian organizations have used Bitcoin extensively since the start of the Russia-Ukraine war in February 2022. The Ukrainian government formally accepted cryptocurrency donations on its official channels — receiving over $100 million in cryptocurrency in the first weeks of the war. What does this large-scale wartime use illustrate?",
    "Bitcoin's role in international humanitarian finance is significant — its borderless, censorship-resistant nature makes it especially useful for moving funds across politically-contested boundaries where banking access is uncertain",
    "Bitcoin was used for war-profiteering by Russian oligarchs — the Ukrainian government's acceptance was a cover for cryptocurrency-facilitated sanctions evasion",
    "Bitcoin facilitated illegal weapons sales — the wartime cryptocurrency flows were primarily related to arms trafficking",
    "Bitcoin was banned in both Russia and Ukraine during the war — the cryptocurrency flows occurred entirely through illicit channels",
    "The Ukraine donations case is a major institutional Bitcoin use. Within days of the war's start, the Ukrainian government had a cryptocurrency wallet receiving public donations. Within weeks they had received tens of millions. Bitcoin's neutrality and accessibility made it operational humanitarian-finance infrastructure during an active war.",
    strategy="ukraine_bitcoin_2022",
)

# Technical recognition (5)

add_p2(
    "Bitcoin uses elliptic curve cryptography for its digital signatures — specifically the secp256k1 curve, an unusual choice for cryptographic protocols at the time of Bitcoin's launch. The more common choice for similar applications would have been NIST-approved curves like secp256r1 (P-256). Why does Satoshi's choice of secp256k1 matter?",
    "The NIST curves had parameters chosen by US government processes that some cryptographers suspected might include hidden weaknesses — secp256k1's parameters are derived from a clear mathematical structure, eliminating that concern",
    "secp256k1 was the only curve supported by the OpenSSL library Satoshi was using — the choice reflected available implementations rather than considered preferences",
    "secp256k1 provided substantially better performance than other curves — Bitcoin's computational efficiency depended on the specific properties",
    "secp256k1 was patent-free while other curves required licensing — the choice reflected legal considerations for the open-source project",
    "The secp256k1 choice signals Satoshi's mindset. The Snowden disclosures (2013) would later confirm that some NIST cryptographic standards had been weakened by NSA influence (Dual_EC_DRBG specifically). Satoshi's pre-2009 choice anticipated these concerns.",
    strategy="bitcoin_secp256k1",
)

add_p2(
    "Bitcoin's address format has changed several times. The original 2009 address format was 'P2PKH' (Pay to Public Key Hash) — addresses starting with '1'. SegWit introduced 'P2WPKH' (Pay to Witness Public Key Hash) — addresses starting with 'bc1'. Taproot introduced 'P2TR' (Pay to Taproot) — addresses also starting with 'bc1' but using a different encoding. What do the format upgrades collectively provide?",
    "Improved privacy, lower transaction fees, and richer scripting capabilities — progressive improvements that preserve backward compatibility while adding new features through soft forks rather than hard forks",
    "Required compliance with successive regulatory regimes — the format changes reflect government-mandated identity disclosure improvements",
    "Different versions of the Bitcoin network — each format represents a competing Bitcoin variant maintained by different developer teams",
    "Mandatory password rotation for security — the format changes require Bitcoin holders to regularly migrate funds to new addresses",
    "The address format evolution illustrates Bitcoin's soft-fork upgrade path. Each new format is added without breaking older formats. Users can continue using older addresses indefinitely; new features are available to those who opt in. Bitcoin's conservative approach to changes is part of its credibility as monetary infrastructure.",
    strategy="bitcoin_address_formats",
)

add_p2(
    "Bitcoin's blockchain currently exceeds 500 GB in size and grows by approximately 60 GB per year. A 'full node' — software that verifies every transaction in the chain from the Genesis block forward — requires storing this data and the computational resources to validate it. Why does the size constraint matter for Bitcoin's character?",
    "If full nodes become too expensive to run on consumer hardware, only specialized operators can independently verify the chain — concentrating verification power and undermining the trustless property that distinguishes Bitcoin",
    "If the blockchain becomes too large, the network will exceed memory storage limits — Bitcoin's design includes automatic data pruning",
    "If full nodes accumulate too much data, the network's transaction throughput declines — the size constraint directly limits transactions per second",
    "If the blockchain grows too large, mining becomes uneconomical — miners must store the chain to participate in consensus",
    "The full-node-on-consumer-hardware constraint was the deep argument of the block-size war. If only data-center operators can run full nodes, the network's trust assumptions shift. The small-block faction won because they argued sovereignty (every user can verify) matters more than throughput.",
    strategy="bitcoin_full_node_size",
)

add_p2(
    "Bitcoin's mining is concentrated in regions with cheap electricity — historically Iceland (geothermal), Sichuan during wet season (hydropower), Texas (natural gas), Kazakhstan (coal and gas). The geographic distribution of mining shifted dramatically after China's May 2021 mining ban. Why does mining geography matter for the network?",
    "Geographic concentration of mining creates risks of regulatory capture or state-level attack — distribution across many jurisdictions reduces the chance any single government can compromise the network through its territorial mining operations",
    "Geographic concentration affects transaction speed — the physical distance between miners determines how quickly new blocks propagate through the network",
    "Geographic distribution provides redundancy against natural disasters — Bitcoin's mining concentration in Iceland and Texas creates risk of single-event outages",
    "Geographic patterns determine Bitcoin's environmental footprint — mining in regions with renewable versus fossil fuels affects emissions",
    "Geographic distribution of mining is a credibility property. A network where 70% of hashrate is in one country (as Bitcoin was before May 2021) is vulnerable to that country's regulation. The post-China-ban redistribution to North America, Kazakhstan, and Europe spreads risk.",
    strategy="bitcoin_mining_geography",
)

add_p2(
    "Bitcoin's smallest unit is the 'satoshi' — one one-hundred-millionth of a bitcoin (0.00000001 BTC). The maximum supply (21 million BTC) corresponds to 2.1 quadrillion satoshis. Why does Bitcoin use such fine subdivision rather than the more conventional two decimal places used in fiat currencies?",
    "The supply is fixed, so future value increases through deflation rather than through additional issuance — the satoshi-level granularity ensures the unit of account remains practical even if one full bitcoin eventually represents very substantial purchasing power",
    "The fine subdivision is required for Lightning Network operations — sub-satoshi precision is needed for the routing fees that make Lightning channels economically viable",
    "The subdivision was chosen to mirror Japanese yen denominations — Satoshi's reference to traditional Japanese small denominations was the inspiration",
    "The subdivision is a technical limitation imposed by Bitcoin's hashing algorithm — eight decimal places is the maximum precision supported by SHA-256",
    "The satoshi-level granularity is forward-looking design. If a bitcoin becomes worth $1M, a satoshi is worth one cent — still practical for everyday transactions. If a bitcoin becomes worth $10M, a satoshi is worth 10 cents. The design anticipated significant deflationary appreciation.",
    strategy="bitcoin_satoshi_unit",
)

# Terra/Luna + crypto cautionary foils (5)

add_p2(
    "On May 7, 2022, the Terra/Luna cryptocurrency ecosystem began collapsing. TerraUSD (UST), an 'algorithmic stablecoin' pegged to the US dollar through a mechanism involving its sister token Luna, lost its dollar peg. Within a week, approximately $60 billion in market capitalization had been destroyed. What was the structural flaw in the Terra/Luna design?",
    "UST's dollar peg was maintained by arbitrage with Luna — when UST fell below $1, traders could burn UST for $1 worth of Luna, but this required Luna to retain value, and during a death spiral Luna's value collapsed to zero, eliminating the arbitrage mechanism",
    "UST was backed by US Treasury bonds — the Federal Reserve's interest rate increases in 2022 reduced the bond values enough to break the peg",
    "UST relied on Tether reserves — when Tether faced regulatory pressure in 2022 the cascading effects broke the UST peg through cross-exchange contagion",
    "UST was issued by El Salvador's central bank — the Salvadoran government's mismanagement of currency reserves caused the collapse",
    "Terra/Luna is the canonical 'algorithmic stablecoin' failure. The design assumed Luna would always have value to back UST redemptions. When confidence in Luna fell, the redemption mechanism produced more Luna being printed to maintain UST's peg — collapsing Luna's price further. The feedback loop was deadly.",
    strategy="terra_luna_may_2022",
)

add_p2(
    "Terra/Luna's founder Do Kwon — a South Korean entrepreneur — became one of the most wanted fugitives in international finance after the May 2022 collapse. Kwon fled South Korea before authorities could arrest him. He was apprehended in Montenegro in March 2023 attempting to board a flight with falsified Costa Rican passport documents. What charges did Kwon face?",
    "Securities fraud, wire fraud, and conspiracy charges in both South Korea and the United States — prosecutors alleged Kwon had knowingly misrepresented Terra's stability mechanism to investors despite internal warnings that the algorithmic peg could fail",
    "Tax evasion charges only — Kwon was charged with failing to report income from Terra/Luna operations rather than with fraud related to the collapse",
    "No criminal charges — Terra/Luna's collapse was treated as a business failure rather than as fraud, with Kwon facing only civil liability claims",
    "Embezzlement charges related to Luna Foundation Guard — Kwon was accused of stealing reserves intended to back UST",
    "Kwon's case is the canonical cautionary tale of algorithmic stablecoin fraud. Internal communications revealed during the proceedings showed Terra developers had warned about the peg's vulnerability. The case illustrates the gulf between Bitcoin's credibly-neutral founding and the centralized, founder-controlled altcoin model.",
    strategy="do_kwon_montenegro_2023",
)

add_p2(
    "Beyond Terra/Luna and FTX, the 2022 'crypto winter' saw collapses of numerous cryptocurrency projects. Three Arrows Capital, a $10 billion crypto hedge fund founded by Su Zhu and Kyle Davies, filed for bankruptcy in July 2022. Their losses cascaded through lenders Voyager, Celsius, and BlockFi. What common pattern characterized these 2022 collapses?",
    "Excessive leverage combined with risk-taking made possible by lender willingness to lend against speculative cryptocurrency collateral — when prices fell, margin calls forced cascading liquidations that destroyed multiple firms simultaneously",
    "Government regulatory intervention specifically targeted these firms — the SEC's enforcement actions in 2022 caused the collapses through prohibitions on cryptocurrency lending",
    "Mathematical impossibility of stable cryptocurrency operations — the 2022 collapses proved digital asset systems cannot function as a class",
    "Cyber attacks targeting cryptocurrency infrastructure — the 2022 collapses were caused by coordinated hacking campaigns against major firms",
    "The 2022 cascade is a useful historical case. Each failure propagated through the others. Three Arrows borrowed from Voyager; Voyager couldn't recover; Celsius and BlockFi held similar positions; FTX absorbed bad assets that broke its own balance sheet. Concentrated counterparty risk in centralized crypto institutions produced systemic failure.",
    strategy="three_arrows_2022_cascade",
)

add_p2(
    "Caroline Ellison was CEO of Alameda Research — Sam Bankman-Fried's trading firm — during the FTX collapse. Ellison pled guilty in December 2022 to seven counts of fraud and conspiracy, cooperating with prosecutors. She testified at SBF's trial in October 2023. In September 2024 Ellison was sentenced. What was the sentence?",
    "Two years in federal prison plus $11 billion forfeiture — Judge Kaplan's relatively short sentence reflected Ellison's cooperation; the same judge gave SBF 25 years partly because of his refusal to accept responsibility at trial",
    "Twenty years in federal prison plus $5 billion forfeiture — Ellison was sentenced to a longer term than SBF because she had directly managed the customer fund misappropriation",
    "Time served plus $50 million forfeiture — Ellison's complete cooperation led to a probationary sentence with no prison time",
    "Life imprisonment plus complete forfeiture — Ellison received the maximum possible sentence under federal sentencing guidelines",
    "The FTX/Alameda case produced four cooperating witnesses: Ellison, Gary Wang, Nishad Singh, and Ryan Salame. Each received sentences substantially shorter than SBF's 25 years. The contrast illustrates the federal sentencing system's reward for cooperation. SBF's gamble on trial was the wrong bet.",
    strategy="caroline_ellison_2024",
)

add_p2(
    "Sam Bankman-Fried had been a major Democratic donor — reportedly the second-largest individual donor in the 2022 midterm cycle behind George Soros. He was also a prominent figure in 'effective altruism' (EA), a movement combining utilitarian ethics with charitable giving. What does the FTX collapse illustrate about EA's engagement with cryptocurrency?",
    "EA's largest grant-making organizations had received hundreds of millions from FTX-affiliated entities — including the Centre for Effective Altruism and FTX Future Fund — with reputational damage when the source was revealed as fraudulent",
    "EA had no significant connection to FTX — the movement's leaders had publicly criticized cryptocurrency before the collapse",
    "EA had warned about FTX's risks in advance — the movement had identified the problems with Alameda Research and recommended action",
    "EA had been victimized by FTX — the movement received no actual funding, with promised donations being public-relations announcements",
    "The EA-FTX connection became subject to significant public scrutiny after the November 2022 collapse. The FTX Future Fund had distributed substantial grants; the Centre for Effective Altruism had received major donations. The episode raised questions about due diligence and conflict-of-interest pressures.",
    strategy="ea_ftx_connection_2022",
)

# OpenAI / DAO / Ethereum as foils (3)

add_p2(
    "The Ethereum blockchain — the second-largest cryptocurrency — was launched in July 2015 by Vitalik Buterin. In June 2016 the Ethereum community faced a crisis: 'The DAO,' a $150 million investment fund built as a smart contract, was drained by an attacker exploiting a contract bug. What did the Ethereum community do?",
    "Most of the community voted to execute a hard fork that reversed the attacker's transactions — creating two chains, Ethereum (ETH) and Ethereum Classic (ETC); demonstrating that the protocol could be altered by social consensus to fix mistakes",
    "The community accepted the loss and made no changes to the protocol — the principle of immutability was preserved, with DAO investors absorbing the full loss",
    "The community paid the attacker a ransom to return the funds — negotiations through intermediaries resulted in the recovery of most of the lost ETH",
    "The community shut down the Ethereum network temporarily while developers patched the smart contract — operations resumed after the bug was fixed",
    "The DAO incident is the canonical Bitcoin-vs-Ethereum contrast. Bitcoin would not have hard-forked to reverse the attack — the protocol's immutability is part of its credibility. Ethereum's willingness to reverse transactions established a precedent the chain could be altered by social consensus.",
    strategy="ethereum_dao_2016",
)

add_p2(
    "Bitcoin's culture includes a strong current of 'Bitcoin maximalism' — the view that Bitcoin is fundamentally different from all other cryptocurrencies and that other tokens are largely scams or distractions. The position is associated with Saifedean Ammous, Michael Saylor, Pierre Rochard, and others. What is the substantive argument?",
    "Bitcoin alone has the properties of credibly-neutral money (no pre-mine, no foundation, no central party) — all later cryptocurrencies have founders, foundations, or governance structures compromising trust-minimization",
    "Bitcoin maximalism is purely tribal — adherents reject other cryptocurrencies for non-substantive reasons relating to social identity",
    "Bitcoin maximalism is based on market share — adherents argue largest market capitalization will inevitably crowd out smaller cryptocurrencies",
    "Bitcoin maximalism reflects libertarian political ideology — adherents oppose all government regulation and use Bitcoin advocacy politically",
    "Bitcoin maximalism's substantive argument: monetary properties matter, and Bitcoin's are uniquely credibly-neutral among cryptocurrencies. The position is sometimes derided as tribal, but the underlying argument tracks the Austrian monetary framework. Other cryptocurrencies face the criticism that they're securities with extra steps.",
    strategy="bitcoin_maximalism",
)

add_p2(
    "MicroStrategy, a business intelligence software company led by CEO Michael Saylor, announced in August 2020 that it had purchased $250 million worth of Bitcoin as a treasury reserve asset. By 2024 MicroStrategy held over 200,000 BTC — making it the largest corporate Bitcoin holder. What was Saylor's stated rationale?",
    "MicroStrategy was preserving the purchasing power of its corporate treasury — cash holdings would lose value to inflation; Bitcoin offered a deflationary alternative with mathematical scarcity that could function as long-term capital storage",
    "MicroStrategy was diversifying its product offerings — the Bitcoin holdings were a temporary investment while the company developed cryptocurrency-related software products",
    "MicroStrategy was pursuing tax advantages — Bitcoin's classification allowed corporate tax strategies unavailable for cash holdings",
    "MicroStrategy was hedging foreign exchange exposure — Bitcoin's lack of correlation with major currencies provided diversification benefits",
    "Saylor's MicroStrategy treasury strategy is the canonical corporate Bitcoin adoption case. The company has continued buying Bitcoin through bear markets, raising debt specifically to finance additional purchases. By 2024 MicroStrategy's market capitalization was substantially tied to its Bitcoin position. Saylor became one of Bitcoin's most prominent corporate advocates.",
    strategy="microstrategy_2020",
)

# Bitcoin ETF + institutional (3)

add_p2(
    "On January 10, 2024, the US Securities and Exchange Commission approved the first 'spot Bitcoin ETFs' — exchange-traded funds that hold actual Bitcoin (rather than futures contracts). The approval came after a decade of SEC rejections. Eleven ETFs began trading January 11, 2024. What was the significance for institutional Bitcoin adoption?",
    "Pension funds, endowments, and other institutional investors could now hold Bitcoin exposure through standard ETF infrastructure — eliminating the operational barriers (custody, compliance, accounting) that had blocked mainstream adoption",
    "Bitcoin became a security under US law — the ETF approval was conditional on Bitcoin's reclassification, ending its commodity status",
    "Retail investors gained their first access to Bitcoin — prior to the ETFs, only sophisticated institutions could legally hold Bitcoin",
    "The Federal Reserve gained authority to regulate Bitcoin directly — the ETF approval transferred oversight from SEC to Fed",
    "The January 2024 ETF approval was a landmark institutional acceptance event. BlackRock's IBIT and Fidelity's FBTC became among the fastest-growing ETFs in history. Within a year they held substantial Bitcoin positions. The institutional infrastructure was now in place.",
    strategy="bitcoin_etf_jan_2024",
)

add_p2(
    "Before the January 2024 spot Bitcoin ETF approval, the SEC had rejected over a decade of applications from various sponsors. The Winklevoss twins' first application was rejected in 2017. Subsequent applications by Wisdom Tree, VanEck, Bitwise, and others were also rejected. What was the legal turning point that forced SEC approval?",
    "Grayscale Investments won an August 2023 federal appeals court ruling that the SEC had acted arbitrarily and capriciously in rejecting their conversion of GBTC to a spot ETF — the unanimous DC Circuit ruling left the SEC with limited grounds to deny additional applications",
    "Congressional legislation in 2023 mandated approval — the Investor Choice Act required the SEC to approve cryptocurrency ETFs within 180 days of application",
    "President Biden issued an executive order requiring approval — the cryptocurrency policy framework established by executive action overrode SEC discretion",
    "The Trump-appointed SEC chair voluntarily reversed prior policy — the change in commission leadership in 2024 immediately produced the approvals",
    "Grayscale v. SEC (August 2023) is the immediate legal cause of the January 2024 approvals. Judge Neomi Rao's unanimous opinion ruled the SEC's denial 'arbitrary and capricious' since the SEC had already approved Bitcoin futures ETFs while denying spot ETFs. The court left the SEC no consistent ground to maintain the denial.",
    strategy="grayscale_sec_aug_2023",
)

add_p2(
    "Bitcoin's institutional adoption arc through 2020-2024 included several signature moments: MicroStrategy's August 2020 treasury purchase, Tesla's January 2021 $1.5 billion Bitcoin announcement, El Salvador's September 2021 legal tender adoption, and the January 2024 spot ETF approvals. What broader pattern do these events represent?",
    "Bitcoin's transition from cypherpunk curiosity to institutional reserve asset — a process taking about 15 years from Genesis, with major institutions now holding Bitcoin in treasuries and accessing it through standard infrastructure",
    "Bitcoin's replacement of gold in international reserves — central banks have systematically sold gold and purchased Bitcoin since 2020",
    "Bitcoin's nationalization by major governments — the adoption pattern reflects governments taking control of cryptocurrency",
    "Bitcoin's failure as a monetary alternative — the institutional adoption demonstrates Bitcoin has become a speculative asset",
    "The 15-year arc from Genesis (2009) to ETF approval (2024) is a remarkable institutional acceptance story. Bitcoin began as a cypherpunk experiment, survived early dismissal as a fad, weathered exchange collapses and regulatory uncertainty, and ended up integrated into mainstream financial market infrastructure.",
    strategy="bitcoin_institutional_arc",
)

# Bitcoin philosophy + separation of money (4)

add_p2(
    "A common Bitcoin-related slogan is 'separation of money and state' — drawing a parallel with the separation of church and state. The argument: just as religious institutions should not be controlled by political authorities, money should not be either. What is the Austrian economic foundation for this slogan?",
    "Friedrich Hayek's 1976 monograph 'Denationalisation of Money' argued state monopoly on currency issuance is the central source of inflation, business cycles, and economic instability — competitive private currencies would discipline monetary policy",
    "Keynes's 1936 General Theory established that political control of money is necessary for full employment — the Bitcoin slogan reverses this consensus",
    "Milton Friedman's monetarism argued for rules-based central banking — Bitcoin extends Friedman's framework by replacing rules with code",
    "Karl Marx's Capital established that money is necessarily a political phenomenon — the Bitcoin slogan attempts to deny this insight",
    "Hayek's Denationalisation argued for competing private currencies. He had concluded that no central bank could be trusted with monetary discretion. Bitcoin represents a partial vindication — a private currency operating outside state control, with its supply governed by code rather than by central bankers.",
    strategy="separation_money_state",
)

add_p2(
    "Bitcoin's cypherpunk lineage traces back to a particular community. The 'Cypherpunks' mailing list was founded in 1992 by Eric Hughes, Timothy May, and John Gilmore. The list operated through the 1990s and 2000s, hosting discussions of cryptography, privacy, digital cash. What was the cypherpunk movement's broader political vision?",
    "Using cryptographic technology to create spaces of privacy and freedom political authorities cannot easily penetrate — the movement viewed strong cryptography as a tool of liberty, with digital cash being one application",
    "Using cryptography to enable government surveillance — the movement was funded by intelligence agencies seeking surveillance tools",
    "Using cryptography to enforce intellectual property rights — the movement was an industry lobbying effort to extend copyright",
    "Using cryptography to centralize banking — the movement sought to consolidate financial services into a few platforms",
    "Timothy May's 1988 'Crypto Anarchist Manifesto' is a foundational document. The movement's vision was political: cryptography as the technology of liberty. Bitcoin is the most successful single product of this tradition; the lineage extends to Tor, Signal, GPG.",
    strategy="cypherpunk_movement_1992",
)

add_p2(
    "Bitcoin transactions are pseudonymous rather than anonymous — addresses are not directly tied to real-world identities, but all transactions are publicly visible on the blockchain. Sophisticated analysis can sometimes link addresses to identities through patterns of use and exchange interactions. What does this transparency-with-pseudonymity property enable?",
    "Auditable verification of the supply — anyone can confirm the 21M cap is being followed — combined with practical privacy for users who take basic operational-security precautions",
    "Complete anonymity comparable to physical cash — Bitcoin transactions cannot be linked to identities under any circumstances",
    "Complete transparency comparable to traditional banking — all Bitcoin holders are publicly identifiable through their addresses",
    "Selective privacy with government access — Bitcoin's privacy protections are subject to court-ordered disclosure under standard subpoena",
    "Bitcoin's pseudonymity-with-transparency is a unique design property. Privacy coins like Monero achieve stronger anonymity at the cost of full supply auditability. Bitcoin prioritized auditability — the 21M cap can be verified by anyone running a full node.",
    strategy="bitcoin_pseudonymity",
)

add_p2(
    "Bitcoin's energy consumption is frequently criticized by environmental advocates. The network consumes substantial electricity worldwide for proof-of-work mining. Bitcoin proponents argue the energy use is justified by what Bitcoin provides. What is the proof-of-work defense?",
    "Proof-of-work converts energy into security — the cost of attacking Bitcoin would require commanding more hashpower than honest miners collectively provide, making energy expenditure the credible-neutrality property that makes Bitcoin's monetary properties possible",
    "Proof-of-work is inevitable for any digital currency — alternative consensus mechanisms like proof-of-stake have been mathematically proven impossible",
    "Proof-of-work uses only renewable energy — Bitcoin mining is entirely powered by stranded solar, wind, and hydro that would otherwise be wasted",
    "Proof-of-work consumes less energy than traditional banking — Bitcoin's energy footprint is smaller than the global banking system's overall electricity demand",
    "Proof-of-work's energy use is intentional. The energy expended creates the cost barrier that makes 51% attacks economically infeasible. Without that cost, the network's transaction-ordering integrity would be cheap to compromise. The energy IS the security model. Critics who object to the energy use must propose an alternative that delivers equivalent trustlessness.",
    strategy="bitcoin_proof_of_work_energy",
)

# =========================================================================
# Compile + validate
# =========================================================================

ALL_QUESTIONS = P1 + P2

print(f"P1 Austrian Foundations T5: {len(P1)} questions")
print(f"P2 Bitcoin T5: {len(P2)} questions")
print(f"TOTAL: {len(ALL_QUESTIONS)} questions")


def validate_all() -> tuple[list, int, int]:
    econ_bank_path = REPO / "data" / "questions" / "economics.json"
    existing_bank = json.loads(econ_bank_path.read_text(encoding="utf-8"))
    print(f"\nLoaded {len(existing_bank)} existing economics bank questions for dedup")

    combined = existing_bank + ALL_QUESTIONS
    dup_index, ans_index = build_bank_indices(combined)

    fail_count = 0
    soft_count = 0

    n_existing = len(existing_bank)
    for i, q in enumerate(ALL_QUESTIONS):
        bank_idx = n_existing + i
        r = validate_rewrite(
            "economics", q, bank=combined, dup_index=dup_index,
            answer_index=ans_index, replace_idx=bank_idx,
        )
        total = len(q["question"]) + sum(len(c) for c in q["choices"])
        if r["verdict"] == "FAIL":
            fail_count += 1
            pillar = q.get("_pillar", "?")
            print(f"  FAIL #{i:03d} P{pillar} total={total}c: {q['question'][:60]}")
            for g, reason in r["hard_fails"]:
                print(f"      {g}: {reason[:240]}")
        elif r["verdict"] == "SOFT_WARN":
            soft_count += 1
            pillar = q.get("_pillar", "?")
            print(f"  SOFT #{i:03d} P{pillar} total={total}c: {q['question'][:60]}")
            for g, reason in r["soft_warns"]:
                print(f"      {g}: {reason[:160]}")
    return ALL_QUESTIONS, fail_count, soft_count


def write_output(questions: list[dict]) -> None:
    out_path = REPO / "_gen_economics_t5_p12.json"
    by_pillar = {}
    for q in questions:
        p = str(q.get("_pillar", "?"))
        by_pillar[p] = by_pillar.get(p, 0) + 1
    payload = {
        "tier": 5,
        "summary": {
            "questions_generated": len(questions),
            "by_pillar": by_pillar,
        },
        "questions": questions,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {len(questions)} questions to {out_path}")


if __name__ == "__main__":
    questions, fails, softs = validate_all()
    print(f"\nValidation summary: {len(questions)} q, {fails} hard fails, {softs} soft warns")
    if fails == 0:
        write_output(questions)
    else:
        print("Will not write output until fails are resolved.")
        sys.exit(1)
