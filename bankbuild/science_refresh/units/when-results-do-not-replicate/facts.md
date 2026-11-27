# When Results Do Not Replicate (T5, 9th grade, method strand, stance unit)

Sources were read on 2026-11-27. Grokipedia first; Wikipedia, the primary
paper or a careful secondary source for anything a student could be taught
wrong. The old-bank topics ioannidis-counts-the-false-positives,
only-36-of-100, p-hacking-and-the-garden-of-forking-paths,
diederik-stapel-caught-by-his-own-students,
jan-hendrik-sch-n-the-noise-that-was-too-identical and
peer-review-is-a-smell-test-not-a-truth-detector were read for leads only;
every fact used here was sourced again. Pharma funding, regulatory capture,
the COVID cases (Surgisphere) and vaccines are left out by the brief.

## John Ioannidis, 2005: why many findings are false

F1. John P. A. Ioannidis, a physician-scientist, published "Why Most Published Research Findings Are False" in PLoS Medicine 2(8): e124 on 30 August 2005. He then chaired the Department of Hygiene and Epidemiology at the University of Ioannina medical school (1999-2010), with an adjunct post at Tufts, and moved to Stanford in 2010. Its summary: "Simulations show that for most study designs and settings, it is more likely for a research claim to be false than true," and "for many current scientific fields, claimed research findings may often be simply accurate measures of the prevailing bias." It is the most cited and downloaded paper in PLoS Medicine's history (Grokipedia).
    https://grokipedia.com/page/Why_Most_Published_Research_Findings_Are_False ; https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.0020124 ; https://grokipedia.com/page/John_Ioannidis

F2. His six corollaries (verbatim, PLoS Medicine 2005): research findings are less likely to be true (1) "The smaller the studies conducted in a scientific field"; (2) "The smaller the effect sizes in a scientific field"; (3) "The greater the number and the lesser the selection of tested relationships in a scientific field"; (4) "The greater the flexibility in designs, definitions, outcomes, and analytical modes"; (5) "The greater the financial and other interests and prejudices"; (6) "The hotter a scientific field (with more scientific teams involved)". Corollary 1's reason: power falls with sample size, and "the PPV for a true research finding decreases as power decreases." Corollary 2: smoking's effects on cancer (relative risks of about 3 to 20) are large; genetic risk factors for complex diseases (about 1.1 to 1.5) are small and harder to detect.
    https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.0020124 ; https://en.wikipedia.org/wiki/Why_Most_Published_Research_Findings_Are_False

F3. The model: the chance that a claimed finding is true (positive predictive value, PPV) depends on R, the ratio of true to false ideas tested, on power (1 - beta) and on the significance level alpha (usually 0.05): PPV = (1 - beta)R / (R - betaR + alpha). "A research finding is thus more likely true than false if (1 - beta)R > alpha." So when few of the ideas tested are true (small R), most "significant" findings are false even with a fair test. Worked example for the unit (my arithmetic on his formula, easy-in-head): 100 ideas, 1 true; a test that passes the true one and about 1 in 20 false ones passes about 5 of the 99 false ideas, so about 5 of every 6 passes are false (PPV = (1/99)/(1/99 + 0.05) = about 0.17). His own Box 1: 100,000 gene variants tested for schizophrenia, about 10 truly linked.
    https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.0020124 ; https://grokipedia.com/page/Why_Most_Published_Research_Findings_Are_False

F4. His remedies ("How Can We Improve the Situation?"): "Better powered evidence, e.g., large studies or low-bias meta-analyses, may help"; "upfront registration of studies"; "What matters is the totality of the evidence." He did not argue that research should be ignored; the paper blames chance and bias, not chiefly fraud.
    https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.0020124 ; https://grokipedia.com/page/Why_Most_Published_Research_Findings_Are_False

F5. The critics (steel-man of the other side): Steven Goodman and Sander Greenland (2007) found "several weaknesses" in the model and rejected the claim that he had "proved" most findings false, while agreeing with his recommendations; Ioannidis replied the same year. Leah Jager and Jeffrey Leek (Biostatistics, 2014) called the model based on "justifiable but arbitrary assumptions rather than empirical data" and estimated the false-positive rate in biomedical studies at "around 14%, not over 50%". How large the share of false findings is remains argued; that many are false is not.
    https://en.wikipedia.org/wiki/Why_Most_Published_Research_Findings_Are_False ; https://grokipedia.com/page/Why_Most_Published_Research_Findings_Are_False

## Small studies: low power

F6. Katherine Button, John Ioannidis, Claire Mokrysz, Brian Nosek, Jonathan Flint, Emma Robinson and Marcus Munafo, "Power failure: why small sample size undermines the reliability of neuroscience", Nature Reviews Neuroscience 14: 365-376, May 2013. From 49 neuroscience meta-analyses of 2011 (over 730 studies) they estimated the median statistical power (the chance of detecting a real effect of the size sought) at 21 percent. "Low statistical power (because of low sample size of studies, small effects or both) negatively affects the likelihood that a nominally statistically significant finding actually reflects a true effect." A later reanalysis (Nord and colleagues) found power varied widely, with many studies adequately powered.
    https://bps.org.uk/research-digest/serious-power-failure-threatens-entire-field-neuroscience ; https://research-information.bris.ac.uk/en/publications/power-failure-why-small-sample-size-undermines-the-reliability-of/ ; https://neuroscience.cam.ac.uk/publications/powerup-a-reanalysis-of-power-failure-in-neuroscience-using-mixture-modeling

## The Open Science Collaboration, 2015

F7. Brian Nosek of the University of Virginia (co-founder of the Center for Open Science, 2013) started the Reproducibility Project: Psychology in November 2011. About 270 researchers (Science News "270"; Grokipedia "over 270") repeated 100 studies published in 2008 in Psychological Science, the Journal of Personality and Social Psychology and the Journal of Experimental Psychology: Learning, Memory, and Cognition, consulting the original authors. Published as Open Science Collaboration, "Estimating the reproducibility of psychological science", Science 349(6251): aac4716, 28 August 2015.
    https://grokipedia.com/page/Reproducibility_Project ; https://en.wikipedia.org/wiki/Reproducibility_Project ; https://www.sciencenews.org/?p=18686 ; https://bps.org.uk/research-digest/what-happened-when-psychologists-tried-replicate-100-previously-published-findings

F8. The result: 97 percent of the originals (97 of 100) had significant results; 36 percent of the replications did. EXACT COUNT: "Only 35 of 97 reports of statistically significant results" were replicated (Science News, 27 August 2015), 35/97 = 36 percent; the popular "36 of 100" is a rounding of this. The mean effect size of the replications (r = 0.197) was about half that of the originals (r = 0.403). Cognitive psychology replicated about 50 percent (21 of 42), social psychology about 25 percent (14 of 55).
    https://www.sciencenews.org/?p=18686 ; https://grokipedia.com/page/Reproducibility_Project ; https://bps.org.uk/research-digest/what-happened-when-psychologists-tried-replicate-100-previously-published-findings

F9. What the count does not show: Nosek's team "can't say whether nonreproduced results represented illusory effects" or genuine effects that were missed; failures might also reflect unnoticed differences between original and repeat (Science News). "Just because a finding doesn't replicate doesn't mean the original result was false" (The Psychologist, BPS, 2015). A Science editor said the outcome does not speak directly to the validity or falsity of the theories tested.
    https://www.sciencenews.org/?p=18686 ; https://bps.org.uk/research-digest/what-happened-when-psychologists-tried-replicate-100-previously-published-findings

## p-hacking: many tries on one set of data

F10. Joseph Simmons, Leif Nelson and Uri Simonsohn, "False-Positive Psychology: Undisclosed Flexibility in Data Collection and Analysis Allows Presenting Anything as Significant", Psychological Science 22(11), 2011. Twenty University of Pennsylvania undergraduates heard either the Beatles' "When I'm Sixty-Four" or "Kalimba", then gave their birth dates; controlling for father's age, the Beatles listeners were "nearly a year-and-a-half younger" (adjusted mean 20.1 against 21.5 years). They ran it "to demonstrate a serious flaw in the usual way that behavioral science data are collected and reported" (APS, 2011); Simmons: "We just wanted to show, with sort of a ridiculous example, that it's not hard to run studies and find crazy things" (Penn Gazette, 2012). The data were real; the practices were common ones: choosing the control variable after the data were in, adding participants until the result was significant, testing several conditions and dropping some.
    https://www.psychologicalscience.org/news/were-only-human/scientific-freedom-and-the-fountain-of-youth.html ; https://thepenngazette.com/lies-damn-lies-and-experimental-research-statistics/ ; https://newsroom.haas.berkeley.edu/magazine/fall-2019/duped-by-data/

F11. Their simulations: four such common choices combined gave a false-positive rate of 60.7 percent (Grokipedia; Penn Gazette "61 percent"), against the nominal 5 percent. Grokipedia defines data dredging (p-hacking) as "conducting multiple unplanned statistical analyses on a dataset"; the term was popularised by their 2011 paper (sources differ on who coined it, so the questions do not ask). At the usual line, 20 independent tests of false ideas give on average 1 false positive by chance alone.
    https://grokipedia.com/page/Data_dredging ; https://thepenngazette.com/lies-damn-lies-and-experimental-research-statistics/

## The garden of forking paths

F12. Andrew Gelman (statistician, Columbia University) and Eric Loken, "The garden of forking paths: Why multiple comparisons can be a problem, even when there is no 'fishing expedition' or 'p-hacking' and the research hypothesis was posited ahead of time" (14 November 2013); also "The Statistical Crisis in Science", American Scientist 102 (2014). "The problem is there can be a large number of potential comparisons when the details of data analysis are highly contingent on data, without the researcher having to perform any conscious procedure of fishing or examining multiple p-values." It can happen "implicitly" to researchers who "only make a single comparison" and evaluate their data once (Wikipedia). Remedies: prespecify the analysis (preregistration), out-of-sample testing on fresh data, multiverse analysis.
    https://en.wikipedia.org/wiki/Forking_paths_problem ; https://forrt.org/glossary/english/garden_of_forking_paths/ ; https://grokipedia.com/page/Data_dredging

## The file drawer

F13. Robert Rosenthal, a psychologist, named "The 'file drawer problem' and tolerance for null results" (Psychological Bulletin 86(3): 638-641, 1979): in its extreme form, "journals are filled with the 5% of the studies that show Type I errors" while file drawers hold the rest, the studies with nonsignificant results (quoted by Word Spy and by Scargle 1999; the original page was not reached). Publication bias is the "selective publication of research studies based on the direction or strength of their findings" (Grokipedia).
    https://grokipedia.com/page/Publication_bias ; https://en.wikipedia.org/wiki/Publication_bias ; https://wordspy.com/words/file-drawer-effect

F14. Annie Franco, Neil Malhotra and Gabor Simonovits, "Publication bias in the social sciences: Unlocking the file drawer", Science 345(6203), 19 September 2014. They followed the experiments run through TESS (Time-sharing Experiments for the Social Sciences, a peer-reviewed, National Science Foundation-funded program) from 2002 to 2012: 249 studies, 221 analysed. "Nearly 65 percent of the studies with null findings were not only not published, but never even written up." Published: over 60 percent of strong results, 50 percent of mixed, 20 percent of null. Strong results were 40 percentage points more likely to be published and 60 points more likely to be written up than null ones. Reasons: "Some anticipated the rejection of such papers while others simply lost interest" (Stanford GSB, 2014). They called for pre-registration and registries of unpublished work.
    https://www.gsb.stanford.edu/insights/neil-malhotra-why-no-news-still-important-news-research ; https://phys.org/news/2014-08-lack-published-null-result-papers.html ; https://www.bitss.org/education/mooc-parent-page/week-2-publication-bias/detecting-and-reducing-publication-bias/publication-bias-in-the-social-sciences/

## Bem's precognition paper and the repeat no journal would review

F15. Daryl Bem of Cornell University published "Feeling the Future: Experimental Evidence for Anomalous Retroactive Influences on Cognition and Affect" in the Journal of Personality and Social Psychology in 2011: nine experiments (Grokipedia: over 1,000 Cornell undergraduates; eight of nine significant) offered as evidence of precognition, sensing the future.
    https://grokipedia.com/page/Daryl_Bem ; https://en.wikipedia.org/wiki/Daryl_Bem

F16. Stuart Ritchie (Edinburgh), Richard Wiseman (Hertfordshire) and Chris French (Goldsmiths) made "three pre-registered independent attempts to exactly replicate" Bem's "retroactive facilitation of recall" experiment, 50 participants in each lab (a power analysis called for at least 41), with Bem's own computer program and 48-word list (five words changed for UK participants). "All three replication attempts failed to produce significant effects (combined n = 150; combined p = .83, one-tailed)." PLoS ONE 7(3): e33423, 14 March 2012.
    https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0033423 ; https://www.sciencedaily.com/releases/2012/03/120315094737.htm

F17. The Journal of Personality and Social Psychology rejected their paper. French: "Our submission was rejected without being sent for peer review," "on the basis that the journal has a policy of not publishing replications" (University of Hertfordshire release, ScienceDaily, 15 March 2012). Wikipedia: JPSP, Science Brevia and Psychological Science each rejected it because it was a replication. Later in 2012 Jeff Galak, Robyn LeBoeuf, Leif Nelson and Joseph Simmons published seven failed replications (3,289 participants) in the same journal (Wikipedia; Grokipedia). A 2023 preregistered replication designed with ESP proponents also found no evidence of precognition (Wikipedia).
    https://www.sciencedaily.com/releases/2012/03/120315094737.htm ; https://en.wikipedia.org/wiki/Daryl_Bem ; https://grokipedia.com/page/Daryl_Bem

## Peer review and what it can check

F18. Peer reviewers "scrutinize a research manuscript for methodological soundness, factual accuracy, originality, and contribution to knowledge"; they evaluate manuscripts "without access to laboratory protocols or independent replication", relying on "self-reported materials without mandatory raw data audits or forensic checks"; peer review "frequently fail[s] to identify errors, fraudulent data fabrication, or plagiarism before publication" (Grokipedia). The Schon case prompted debate over whether peer review should be expected to detect deliberate fraud (Wikipedia). MISCONCEPTION: that reviewers check the raw data or repeat the experiment.
    https://grokipedia.com/page/Scholarly_peer_review ; https://en.wikipedia.org/wiki/Schön_scandal

## Diederik Stapel

F19. Diederik Stapel, a Dutch social psychologist (professor at Groningen from 2000, at Tilburg University from 2006, later dean there), invented data for years; he said the data came from contacts in schools, and when asked for those contacts he said the schools did not exist (Wikipedia). He designed whole studies, invented the data and handed the data files to students and colleagues to analyse.
    https://grokipedia.com/page/Diederik_Stapel ; https://en.wikipedia.org/wiki/Diederik_Stapel

F20. Who caught him: "In late August, three young researchers under Stapel's supervision had found irregularities in published data" and notified the department head (Ewen Callaway, Nature, 1 November 2011); Grokipedia: "three young researchers formally alerted the department head, Prof. Marcel Zeelenberg." Tilburg suspended him on 7 September 2011. Not peer reviewers, not a failed replication, not an editor.
    https://www.scientificamerican.com/article/massive-fraud-uncovered-in-work/ ; https://grokipedia.com/page/Diederik_Stapel ; https://en.wikipedia.org/wiki/Diederik_Stapel

F21. The committees (Levelt at Tilburg, Noort at Groningen, Drenth at Amsterdam): interim report 31 October 2011 (at least 30 fake papers); final report "Flawed Science", 28 November 2012: 55 publications. Retraction Watch counted 58 retractions by December 2015. The interim report found that in his data "effects were large; missing data and outliers were rare; and hypotheses were rarely refuted"; Pim Levelt: "We see that the scientific checks and balances process has failed at several levels"; journals "did not question the omission of details about where the data came from" (Callaway, 2011). The committees found he acted alone. (Figure conflicts: 30 interim, 55 final, 58 retractions; the questions say only "dozens".)
    https://www.scientificamerican.com/article/massive-fraud-uncovered-in-work/ ; https://en.wikipedia.org/wiki/Diederik_Stapel ; https://grokipedia.com/page/Diederik_Stapel

## Jan Hendrik Schon

F22. Jan Hendrik Schon, a physicist hired by Bell Labs (Lucent Technologies) in late 1997, reported organic-semiconductor results, including superconductivity, lasers and a molecular-scale transistor, in Science and Nature. In 2001 he was an author on "an average of one newly published research paper every eight days" (Wikipedia). "No other group reproduced them" (Wikipedia); Grokipedia: millions spent on "unsuccessful replication attempts worldwide".
    https://en.wikipedia.org/wiki/Schön_scandal ; https://grokipedia.com/page/Schön_scandal

F23. How he was caught (2002): Julia Hsu and Lynn Loo first noticed duplicated data on 19 April 2002 while working on a patent (Wikipedia). Lydia Sohn, then at Princeton, was asked to look at two of his figures and found that two experiments at very different temperatures had identical noise; she said noise "should never overlap one another, noise simply can't reproduce" (BBC Horizon, quoted by Wikipedia). When Nature's editors raised it, Schon said he had "accidentally submitted the same graph twice." Paul McEuen of Cornell found the same noise in a third experiment and sent six examples to the authors and the editors of Science and Nature; Lucent began an investigation in May 2002. SOURCE CONFLICT: the brief and many retellings credit Sohn and McEuen with exposing him; Wikipedia says Hsu and Loo noticed duplication first. The question says only that Sohn saw the matching noise, which every account agrees on.
    https://en.wikipedia.org/wiki/Schön_scandal ; https://en.wikipedia.org/wiki/Lydia_Sohn ; https://grokipedia.com/page/Schön_scandal

F24. The Beasley committee (chair Malcolm Beasley of Stanford) reported on 25 September 2002 (Grokipedia also gives 26 September): misconduct in 16 of 24 allegations; whole data sets reused across experiments; some graphs said to be data were generated from mathematical functions; Schon kept no laboratory notebooks, his raw data files had been erased (he blamed limited disk space) and samples were discarded or damaged. Co-authors were cleared of misconduct. Retractions followed in Science, Nature, Physical Review and other journals (Wikipedia: Science 8 + 2, Nature 7, Physical Review 6); the University of Konstanz revoked his doctorate in 2004.
    https://en.wikipedia.org/wiki/Schön_scandal ; https://grokipedia.com/page/Schön_scandal

F25. Noise in a measurement is the small random fluctuation present in every real reading; because it is random, two separate measurements never share the same noise, so identical noise in two graphs means one set of data was used twice (Sohn, F23; Beasley, F24). MISCONCEPTION: that the same instrument, or the same day, gives the same noise.
    https://en.wikipedia.org/wiki/Lydia_Sohn ; https://en.wikipedia.org/wiki/Schön_scandal

## The cures: registered reports and their evidence

F26. Registered reports: a study's question, methods and analysis plan are peer reviewed before the data are collected (Stage 1); if accepted ("in-principle acceptance"), the journal commits to publish the finished study "whatever the results, provided the approved protocol is followed" (Grokipedia); Stage 2 checks that the plan was kept. Christopher Chambers (Cardiff University) introduced the format at the journal Cortex in 2013 ("Registered Reports: A new publishing initiative at Cortex", Cortex 49: 609-610). More than 300 journals offer it (Grokipedia, Center for Open Science list). It differs from preregistration alone, which is not peer reviewed and does not commit a journal to publish.
    https://grokipedia.com/page/Registered_report ; https://en.wikipedia.org/wiki/Registered_report ; https://blogs.lse.ac.uk/impactofsocialsciences/2013/09/24/registered-reports-countering-publication-bias/

F27. Anne Scheel, Mitchell Schijen and Daniel Lakens, "An Excess of Positive Results: Comparing the Standard Psychology Literature With Registered Reports", Advances in Methods and Practices in Psychological Science 4(2), 2021: for the first hypothesis of each paper, "96% positive results in standard reports, but only 44% positive results in Registered Reports" (146 of 152 against 31 of 71; all published psychology registered reports to November 2018). The gap stayed large without the direct replications (96 against 50 percent). "This large gap suggests that psychologists underreport negative results"; they note the study did not directly test whether registered reports reduce bias.
    https://research.tue.nl/en/publications/an-excess-of-positive-results-comparing-the-standard-psychology-l/ ; https://grokipedia.com/page/Registered_report ; https://en.wikipedia.org/wiki/Registered_report

F28. The wider record: a 2016 Nature survey of more than 1,500 scientists found over 70 percent had tried and failed to reproduce another researcher's experiments (Grokipedia, Replication crisis). Wikipedia: replication failures "reflect the normal operation of science", a mechanism by which unsupported hypotheses are eliminated, though it "often functions slowly and inconsistently".
    https://grokipedia.com/page/Replication_crisis ; https://en.wikipedia.org/wiki/Replication_crisis

## Misconceptions a 9th-grader brings (for honest wrong choices)

- A result that passes the 1-in-20 line is 95 percent sure to be true, so only 1 in 20 published findings is false (F3, F6).
- A larger effect is needed only for drama; small studies are just as trustworthy if they pass (F6).
- A failed repeat proves the original was false (F9).
- The replication crisis is mostly fraud (F4, F10: chance and common, honest practices).
- Running only one test means there is no many-tries problem (F12).
- Null results go unpublished mainly because journals reject them (F14: most were never written up).
- Peer reviewers check the raw data or repeat the experiment (F18).
- The same machine or the same day gives the same noise (F25).

## Left out (could not be pinned down, or another lane)

- Who coined "p-hacking" (sources differ: Haas says Nelson and colleagues, 2011).
- The Borges origin of the "garden of forking paths" name (not confirmed in any source read).
- Uri Simonsohn's "Just Post It" cases (Smeesters, Sanna): accounts of data access conflict (Simonsohn against Richard Gill).
- Begley and Ellis (Amgen), Bayer, Turner 2008 (antidepressant trials), Surgisphere, Wakefield, Hwang: pharma, COVID or vaccine lanes the brief leaves out.
- Gilbert, King, Pettigrew and Wilson's 2016 critique of the 2015 project: not found in Grokipedia or Wikipedia in the parts read.
