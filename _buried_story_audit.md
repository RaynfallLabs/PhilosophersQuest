# Science buried-story audit

All 106 heuristic-flagged candidates classified KEEP vs REWRITE.

## Summary

- **KEEP**: 90 (heuristic over-flagged — stems already carry the story)
- **REWRITE**: 16 (the dramatic substance was buried in context)

## Classification reasoning principles

- KEEP: stem already names a real person + dates + dramatic numbers; answer carries the recognition skill or the specific fact.
- REWRITE: stem is generic 'what does this illustrate / what's the recognition' while the dramatic specifics (named figure, dollar amount, body count, dated event, quoted phrase) live in `context` — invisible during live play.

## Per-candidate decisions

- ✓ **[000] bank_idx=987 t4** (897 chars, score=11, generic_stem=False) — **KEEP**: T4 dates + body count in stem; answer carries names
- ✏ **[001] bank_idx=729 t3** (613 chars, score=9, generic_stem=False) — **REWRITE**: KKK 1926 + Negro Project + 2020 name removal buried; stem can carry
- ✏ **[002] bank_idx=767 t3** (632 chars, score=9, generic_stem=False) — **REWRITE**: Bhattacharya/Kulldorff/Prasad/Makary named only in context; should be in stem
- ✓ **[003] bank_idx=1227 t5** (792 chars, score=8, generic_stem=True) — **KEEP**: stem already carries Laughlin 1922 + Heidelberg 1936 + 1933 Nazi law
- ✓ **[004] bank_idx=749 t3** (644 chars, score=8, generic_stem=False) — **KEEP**: Andersen et al. Nature Med Mar 2020 in stem; FOIA reveal in answer
- ✏ **[005] bank_idx=964 t4** (833 chars, score=8, generic_stem=False) — **REWRITE**: Feb 1 2020 Fauci/Farrar teleconference + 2-yr misinformation labeling buried
- ✓ **[006] bank_idx=1214 t5** (1025 chars, score=8, generic_stem=False) — **KEEP**: near cap; Theranos + $9B + Carreyrou 2015 in stem
- ✓ **[007] bank_idx=1222 t5** (886 chars, score=8, generic_stem=False) — **KEEP**: Indiana 1907 + Dr Sharp + unauthorized in stem
- ✓ **[008] bank_idx=733 t3** (628 chars, score=7, generic_stem=True) — **KEEP**: Tuskegee dates + Alabama + subjects in stem
- ✓ **[009] bank_idx=910 t4** (864 chars, score=7, generic_stem=True) — **KEEP**: 1989 AP + Noel Brown + 2000 deadline in stem
- ✓ **[010] bank_idx=732 t3** (496 chars, score=7, generic_stem=False) — **KEEP**: Nuremberg 1947 + Doctors Trial in stem
- ✓ **[011] bank_idx=735 t3** (604 chars, score=7, generic_stem=False) — **KEEP**: recall-mode question; not buried-story pattern
- ✓ **[012] bank_idx=869 t4** (850 chars, score=7, generic_stem=False) — **KEEP**: Salk 1955 + "patent the sun?" in stem; scrutinized list in answer
- ✓ **[013] bank_idx=1236 t5** (796 chars, score=7, generic_stem=False) — **KEEP**: IHS + 1976 GAO + Pinkerton-Uri in stem
- ✓ **[014] bank_idx=1245 t5** (706 chars, score=7, generic_stem=False) — **KEEP**: Prasad + UCSF + named work in stem
- ✓ **[015] bank_idx=1309 t5** (835 chars, score=7, generic_stem=False) — **KEEP**: list-as-answer at T5 is appropriate format
- ✓ **[016] bank_idx=452 t2** (484 chars, score=6, generic_stem=True) — **KEEP**: T2 at cap; recognition skill OK; cannot expand
- ✏ **[017] bank_idx=736 t3** (646 chars, score=6, generic_stem=True) — **REWRITE**: Ioannidis 2005 paper title + Open Sci Collab 36% buried
- ✓ **[018] bank_idx=1261 t5** (855 chars, score=6, generic_stem=True) — **KEEP**: Gupta named in stem
- ✓ **[019] bank_idx=413 t2** (283 chars, score=6, generic_stem=False) — **KEEP**: T2 recall date question
- ✓ **[020] bank_idx=726 t3** (608 chars, score=6, generic_stem=False) — **KEEP**: Indiana 1907 + funding names in stem and answer
- ✏ **[021] bank_idx=741 t3** (543 chars, score=6, generic_stem=False) — **REWRITE**: GBD author names (Bhattacharya/Kulldorff/Gupta) + 60k signers buried
- ✓ **[022] bank_idx=766 t3** (620 chars, score=6, generic_stem=False) — **KEEP**: generic recognition; minimal buried drama
- ✓ **[023] bank_idx=981 t4** (934 chars, score=6, generic_stem=False) — **KEEP**: Indiana 1907 + targets in stem
- ✓ **[024] bank_idx=984 t4** (872 chars, score=6, generic_stem=False) — **KEEP**: Sanger + Negro Project + quotes in stem and answer
- ✓ **[025] bank_idx=1235 t5** (719 chars, score=6, generic_stem=False) — **KEEP**: recall-mode foundational doc
- ✓ **[026] bank_idx=1242 t5** (795 chars, score=6, generic_stem=False) — **KEEP**: Twitter Files + Musk + 2022-2023 in stem; named scientists in answer
- ✓ **[027] bank_idx=918 t4** (902 chars, score=5, generic_stem=True) — **KEEP**: inquiries + Montford in stem; recognition skill in answer
- ✓ **[028] bank_idx=720 t3** (601 chars, score=5, generic_stem=False) — **KEEP**: Borlaug + countries + 1960s in stem
- ✓ **[029] bank_idx=952 t4** (714 chars, score=5, generic_stem=False) — **KEEP**: Hanke-Herby-Jonung 2022 + 0.2% in stem
- ✏ **[030] bank_idx=976 t4** (897 chars, score=5, generic_stem=False) — **REWRITE**: WHO 2019 pandemic docs + Imperial College prior position buried
- ✓ **[031] bank_idx=983 t4** (921 chars, score=5, generic_stem=False) — **KEEP**: California 1909 + 20k + 1970s + targets in stem
- ✓ **[032] bank_idx=990 t4** (927 chars, score=5, generic_stem=False) — **KEEP**: at near-cap; Johnson-Reed named in answer
- ✓ **[033] bank_idx=999 t4** (945 chars, score=5, generic_stem=False) — **KEEP**: at cap; substance carried in stem + answer
- ✓ **[034] bank_idx=1223 t5** (787 chars, score=5, generic_stem=False) — **KEEP**: California program scale + duration in stem
- ✓ **[035] bank_idx=1226 t5** (754 chars, score=5, generic_stem=False) — **KEEP**: Davenport + Laughlin + 1924 Act + ERO 1910 all in stem
- ✓ **[036] bank_idx=1231 t5** (826 chars, score=5, generic_stem=False) — **KEEP**: Unit 731 + dates + experiments + Ishii in stem
- ✓ **[037] bank_idx=1234 t5** (877 chars, score=5, generic_stem=False) — **KEEP**: Lacks + 1951 + HeLa + Salk + family unaware in stem
- ✏ **[038] bank_idx=1279 t5** (949 chars, score=5, generic_stem=False) — **REWRITE**: Susan Reverby Wellesley 2005 discovery + Obama 2010 apology buried
- ✓ **[039] bank_idx=1290 t1** (269 chars, score=5, generic_stem=False) — **KEEP**: T1 tight; Siri + 75 years + Pittman well-distributed
- ✓ **[040] bank_idx=731 t3** (595 chars, score=4, generic_stem=True) — **KEEP**: Grant book + Hitler letter in stem; quote in answer
- ✏ **[041] bank_idx=737 t3** (587 chars, score=4, generic_stem=True) — **REWRITE**: hotel-room fabrication + Levelt investigation buried; cinematic
- ✓ **[042] bank_idx=1121 t5** (1143 chars, score=4, generic_stem=True) — **KEEP**: near hard cap; GBD + Collins quote in stem; vindication in answer
- ✓ **[043] bank_idx=1213 t5** (809 chars, score=4, generic_stem=True) — **KEEP**: Wansink + Cornell + named studies + blog reveal in stem
- ✓ **[044] bank_idx=1240 t5** (775 chars, score=4, generic_stem=True) — **KEEP**: Cochrane + 2023 + Jefferson + 78 RCTs in stem
- ✏ **[045] bank_idx=1246 t5** (736 chars, score=4, generic_stem=True) — **REWRITE**: Joe Rogan #1757 + Neil Young Spotify protest is the cinematic moment, buried
- ✓ **[046] bank_idx=1260 t5** (770 chars, score=4, generic_stem=True) — **KEEP**: Kulldorff + Harvard + scan statistic in stem
- ✓ **[047] bank_idx=1284 t5** (877 chars, score=4, generic_stem=True) — **KEEP**: FBI + DOE 2023 assessments + timeline in stem
- ✓ **[048] bank_idx=374 t2** (421 chars, score=4, generic_stem=False) — **KEEP**: Hilleman + 40 vaccines + tape released 2007 in stem
- ✓ **[049] bank_idx=392 t2** (364 chars, score=4, generic_stem=False) — **KEEP**: Wegener + Pangaea recall
- ✓ **[050] bank_idx=414 t2** (360 chars, score=4, generic_stem=False) — **KEEP**: Collins recall
- ✓ **[051] bank_idx=462 t2** (410 chars, score=4, generic_stem=False) — **KEEP**: Buck v Bell + Holmes ruling in stem
- ✓ **[052] bank_idx=463 t2** (399 chars, score=4, generic_stem=False) — **KEEP**: Indiana 1907 + targets recall
- ✓ **[053] bank_idx=728 t3** (550 chars, score=4, generic_stem=False) — **KEEP**: California program + duration + targets in stem
- ✓ **[054] bank_idx=730 t3** (584 chars, score=4, generic_stem=False) — **KEEP**: ERO + dates + Long Island in stem
- ✓ **[055] bank_idx=734 t3** (668 chars, score=4, generic_stem=False) — **KEEP**: Lacks + 1951 + HeLa in stem
- ✓ **[056] bank_idx=743 t3** (571 chars, score=4, generic_stem=False) — **KEEP**: Bhattacharya + 2025 NIH director + Stanford background
- ✓ **[057] bank_idx=748 t3** (651 chars, score=4, generic_stem=False) — **KEEP**: MWP + LIA + Mann hockey stick + criticism in stem
- ✏ **[058] bank_idx=753 t3** (595 chars, score=4, generic_stem=False) — **REWRITE**: 2022 NAEP largest decline + Sweden comparison + GBD prediction buried
- ✓ **[059] bank_idx=870 t4** (854 chars, score=4, generic_stem=False) — **KEEP**: Hilleman + 40 vaccines + named products in stem
- ✓ **[060] bank_idx=979 t4** (917 chars, score=4, generic_stem=False) — **KEEP**: VICP + 1986 NCVIA in stem; named tax in context fine
- ✏ **[061] bank_idx=1018 t4** (858 chars, score=4, generic_stem=False) — **REWRITE**: "hide the decline" phrase + FOIA evasion in context — the cinematic moment
- ✓ **[062] bank_idx=1211 t5** (836 chars, score=4, generic_stem=False) — **KEEP**: Schon + Bell Labs + paper-every-8-days in stem
- ✓ **[063] bank_idx=1217 t5** (947 chars, score=4, generic_stem=False) — **KEEP**: fix template done correctly — WHO suspension in answer
- ✓ **[064] bank_idx=1224 t5** (689 chars, score=4, generic_stem=False) — **KEEP**: NC program + dates + Black-women targeting in stem
- ✓ **[065] bank_idx=1241 t5** (736 chars, score=4, generic_stem=False) — **KEEP**: Murthy v Missouri + Missouri v Biden in stem
- ✓ **[066] bank_idx=1276 t5** (958 chars, score=4, generic_stem=False) — **KEEP**: Purdue + Sackler + $11B + OxyContin dates in stem
- ✓ **[067] bank_idx=1289 t1** (269 chars, score=4, generic_stem=False) — **KEEP**: T1 recall
- ✓ **[068] bank_idx=1291 t2** (480 chars, score=4, generic_stem=False) — **KEEP**: Hilleman + 2005 tape T2 recall
- ✓ **[069] bank_idx=1301 t4** (760 chars, score=4, generic_stem=False) — **KEEP**: NCVIA + VICP + Siri named in stem
- ✓ **[070] bank_idx=249 t1** (280 chars, score=3, generic_stem=True) — **KEEP**: T1 at cap; Wegener drift efficient
- ✓ **[071] bank_idx=466 t2** (402 chars, score=3, generic_stem=True) — **KEEP**: FBI + DOE 2023 lab origin in stem
- ✓ **[072] bank_idx=480 t2** (478 chars, score=3, generic_stem=True) — **KEEP**: T2 at cap; Ioannidis + 2005 + Bayesian in stem
- ✓ **[073] bank_idx=742 t3** (546 chars, score=3, generic_stem=True) — **KEEP**: Collins quote in answer; FOIA email in stem
- ✓ **[074] bank_idx=744 t3** (613 chars, score=3, generic_stem=True) — **KEEP**: Kulldorff + Harvard + scan statistic in stem
- ✓ **[075] bank_idx=751 t3** (613 chars, score=3, generic_stem=True) — **KEEP**: Cochrane + 2023 + Jefferson in stem
- ✓ **[076] bank_idx=975 t4** (913 chars, score=3, generic_stem=True) — **KEEP**: near cap; recognition skill appropriate at T4
- ✓ **[077] bank_idx=988 t4** (929 chars, score=3, generic_stem=True) — **KEEP**: fix template done correctly — Tuskegee in stem, Heller in answer
- ✓ **[078] bank_idx=989 t4** (916 chars, score=3, generic_stem=True) — **KEEP**: near cap; Doctors Trial + Code in stem
- ✓ **[079] bank_idx=1228 t5** (826 chars, score=3, generic_stem=True) — **KEEP**: Grant + book + Hitler quote + Act in stem
- ✓ **[080] bank_idx=1243 t5** (819 chars, score=3, generic_stem=True) — **KEEP**: Siri + 75 yrs + Pittman in stem
- ✓ **[081] bank_idx=1247 t5** (1021 chars, score=3, generic_stem=True) — **KEEP**: Kory + Marik + FLCCC + Sentara consequence in stem
- ✓ **[082] bank_idx=328 t2** (455 chars, score=3, generic_stem=False) — **KEEP**: Lavoisier + Marie-Anne recall T2
- ✓ **[083] bank_idx=377 t2** (492 chars, score=3, generic_stem=False) — **KEEP**: Marshall + 1984 + drinking H. pylori in stem
- ✓ **[084] bank_idx=442 t2** (384 chars, score=3, generic_stem=False) — **KEEP**: Galileo 1610 + 4 moons recall
- ✓ **[085] bank_idx=458 t2** (319 chars, score=3, generic_stem=False) — **KEEP**: Borlaug + Nobel recall
- ✓ **[086] bank_idx=467 t2** (485 chars, score=3, generic_stem=False) — **KEEP**: Wakefield + 1998 + retraction in stem; nuanced answer
- ✏ **[087] bank_idx=479 t2** (429 chars, score=3, generic_stem=False) — **REWRITE**: 2015 OSC + 36% + named failed effects (ego depletion, power pose) buried
- ✓ **[088] bank_idx=488 t2** (461 chars, score=3, generic_stem=False) — **KEEP**: Pasteur + Koch + 1860s in stem
- ✓ **[089] bank_idx=653 t3** (603 chars, score=3, generic_stem=False) — **KEEP**: Wegener + 1912 + bulge/notch in stem
- ✓ **[090] bank_idx=719 t3** (628 chars, score=3, generic_stem=False) — **KEEP**: Margulis + 1967 + mitochondria origin in stem
- ✏ **[091] bank_idx=768 t3** (642 chars, score=3, generic_stem=False) — **REWRITE**: Alito dissent quote buried; cinematic for First Amendment recognition
- ✓ **[092] bank_idx=953 t4** (814 chars, score=3, generic_stem=False) — **KEEP**: Sweden + 2023 + excess mortality in stem
- ✏ **[093] bank_idx=958 t4** (826 chars, score=3, generic_stem=False) — **REWRITE**: Nuremberg Code 1947 + Doctors Trial + Helsinki 1964 buried; central to recognition
- ✓ **[094] bank_idx=966 t4** (893 chars, score=3, generic_stem=False) — **KEEP**: WIV + EcoHealth + NIH in stem
- ✓ **[095] bank_idx=968 t4** (932 chars, score=3, generic_stem=False) — **KEEP**: GoF + 2014-2017 + P3CO in stem
- ✏ **[096] bank_idx=970 t4** (825 chars, score=3, generic_stem=False) — **REWRITE**: Nicholas Wade essay + McNeil/Eban journalism buried; the named figures who changed policy
- ✓ **[097] bank_idx=973 t4** (833 chars, score=3, generic_stem=False) — **KEEP**: Collins + Oct 4 2020 in stem; quote in answer
- ✓ **[098] bank_idx=1002 t4** (834 chars, score=3, generic_stem=False) — **KEEP**: Stanford VP + 2020-2022 in stem; "true content" reveal in answer
- ✓ **[099] bank_idx=1155 t5** (1138 chars, score=3, generic_stem=False) — **KEEP**: near hard cap; Purdue + 800k + Sacklers in stem
- ✓ **[100] bank_idx=1229 t5** (912 chars, score=3, generic_stem=False) — **KEEP**: Sanger + 1939 letter + Gamble in stem; quote in answer
- ✏ **[101] bank_idx=1233 t5** (783 chars, score=3, generic_stem=False) — **REWRITE**: Anarcha + Betsey + Lucy by name + 2018 Central Park statue removal buried
- ✓ **[102] bank_idx=1252 t5** (796 chars, score=3, generic_stem=False) — **KEEP**: Schwab + Great Reset 2020 in stem
- ✓ **[103] bank_idx=1254 t5** (911 chars, score=3, generic_stem=False) — **KEEP**: GoF + 2014/2017 + COVID context in stem
- ✓ **[104] bank_idx=1306 t5** (831 chars, score=3, generic_stem=False) — **KEEP**: all 7 dissidents named in stem; recognition in answer
- ✓ **[105] bank_idx=1310 t5** (953 chars, score=3, generic_stem=False) — **KEEP**: Bhattacharya arc + pattern in stem

## Rewrites (16 entries — all gate-validated)

### bank_idx 479 (T2)

- chars: 457/480 (target), grace 504
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: Beginning around 2010, several large research efforts tried to replicate famous findings in psychology and biomedicine. What did these efforts often find?
>
> ANS:  Many famous results failed to replicate when independent labs tried again
>
> CTX:  The 'replication crisis' is the recognition that many published findings — especially in social psychology, but also in cancer biology and pharmacology — don't replicate when independent labs try them. The 2015 Open Science Collaboration replication of 100 psychology studies found only ~36% replicated cleanly. Famous failed replications include ego…

**After** — story in stem, recognition in answer:

> STEM: The 2015 Open Science Collaboration tried to redo 100 famous psychology studies — including ego depletion and the power-pose effect. Only ~36% replicated cleanly. What did the effort find?
>
> ANS:  Many famous results failed — single studies are weaker than headlines suggest
>
> CTX:  The 'replication crisis' anchored on Ioannidis's 2005 PLOS Medicine paper. Causes include p-hacking, publication bias, small samples, and outright fraud (Stapel, ~50 retractions). The field adopted pre-registration in response.

### bank_idx 729 (T3)

- chars: 649/680 (target), grace 714
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: Margaret Sanger, founder of what would become Planned Parenthood, was a prominent eugenicist who wrote and spoke about race and reproductive policy in the 1910s-1930s. What's her own most direct statement people often point to?
>
> ANS:  Her writings called for limiting reproduction by people she described as 'human weeds', and 'morons'
>
> CTX:  Sanger's *The Pivot of Civilization* (1922) and her writings in *Birth Control Review* explicitly endorsed eugenic goals. She opened the first US birth-control clinic in Brooklyn (1916) and later founded what became Planned Parenthood. She lectured to the Ku Klux Klan in 1926. The 'Negro Project' (1939) was framed in her own letters as needing Blac…

**After** — story in stem, recognition in answer:

> STEM: Margaret Sanger founded what became Planned Parenthood, lectured a Ku Klux Klan women's auxiliary in 1926, and ran a 'Negro Project' (1939) framed in her letters as needing Black ministers to prevent the 'exterminate the Negro population' perception. Planned Parenthood removed her name in 2020. What's her best-known eugenic phrase?
>
> ANS:  'Human weeds' — she wrote of limiting reproduction by those she so described
>
> CTX:  Sanger's *Pivot of Civilization* (1922) endorsed eugenic goals explicitly. The December 10, 1939 letter to Clarence Gamble framed the Black ministers' role. Planned Parenthood's 2020 disavowal acknowledged what historians had long documented.

### bank_idx 736 (T3)

- chars: 675/680 (target), grace 714
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: A 'replication crisis' was named after researchers tried to redo many published studies and found most could not be repeated. What's the recognition skill for a teenager reading 'NEW STUDY SHOWS X' headlines?
>
> ANS:  Wait for replication — a single finding is weak evidence, no matter the journal or how confident the headline sounds
>
> CTX:  The 'replication crisis' was anchored by John Ioannidis's 2005 paper 'Why Most Published Research Findings Are False,' the Open Science Collaboration's 2015 attempt to replicate 100 psychology studies (only ~36% replicated), and dramatic individual cases like Stapel (50+ retractions, 2011). Pre-registration of hypotheses, larger sample sizes, open …

**After** — story in stem, recognition in answer:

> STEM: Ioannidis's 2005 PLOS Medicine paper 'Why Most Published Research Findings Are False' lit the fuse — and the 2015 Open Science Collaboration's attempt to replicate 100 psychology studies got only ~36% replicating cleanly. What's the recognition skill for a teen reading 'NEW STUDY SHOWS X' headlines?
>
> ANS:  Wait for replication — a single finding is weak evidence regardless of journal prestige
>
> CTX:  Famous failed replications include ego depletion, power-pose, and many priming results. Stapel's case (50+ retractions, 2011) is the canonical fabrication example. Pre-registration and registered reports were field responses.

### bank_idx 737 (T3)

- chars: 632/680 (target), grace 714
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: Diederik Stapel was a star Dutch social psychologist at Tilburg University whose work appeared in *Science* and major journals. In 2011 his career imploded. What happened?
>
> ANS:  He confessed to fabricating data in dozens of papers — over 50 of his published works were eventually retracted
>
> CTX:  Three of Stapel's junior researchers reported irregularities in 2011. An investigation led by Willem Levelt found he had been fabricating data for years — sometimes just making up numbers in his hotel room before showing them to graduate students. Over 50 of his papers were retracted by 2024. The case became a foundational example of how prestigiou…

**After** — story in stem, recognition in answer:

> STEM: Star Dutch social psychologist Diederik Stapel (Tilburg University, papers in *Science*) was found in 2011 to have been making up numbers in his hotel room before showing them to graduate students. What was the final accounting?
>
> ANS:  Over 50 of his papers were retracted — prestigious journals and peer review had not caught years of fabrication
>
> CTX:  The Levelt investigation followed reports by three junior researchers. Stapel's memoir 'Faking Science' (2014) is a firsthand account. The case became foundational in showing how prestige + top-journal placement + peer review can fail to detect outright fabrication.

### bank_idx 741 (T3)

- chars: 628/680 (target), grace 714
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: In October 2020 three epidemiologists from Stanford, Harvard, and Oxford published the Great Barrington Declaration. What did it actually propose?
>
> ANS:  'Focused protection' of vulnerable people while letting younger — and healthier populations resume normal life
>
> CTX:  Jay Bhattacharya (Stanford epidemiologist, MD/PhD), Martin Kulldorff (Harvard biostatistician), and Sunetra Gupta (Oxford epidemiologist) wrote the Declaration at the American Institute for Economic Research. It argued lockdowns caused unequal harm — protecting older laptop-class workers while displacing harm onto younger working-class and Third Wo…

**After** — story in stem, recognition in answer:

> STEM: On October 4, 2020, Jay Bhattacharya (Stanford), Martin Kulldorff (Harvard), and Sunetra Gupta (Oxford) published the Great Barrington Declaration. Over 60,000 doctors and scientists signed within months. What did the Declaration actually propose?
>
> ANS:  'Focused protection' of the vulnerable — letting younger, healthier populations resume normal life
>
> CTX:  The Declaration argued lockdowns caused unequal harm — protecting older laptop-class workers while displacing harm onto younger working-class and Third World populations. Within four days, NIH director Francis Collins emailed Anthony Fauci calling for a 'quick and devastating takedown.'

### bank_idx 753 (T3)

- chars: 644/680 (target), grace 714
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: School closures during 2020-2021 were a major component of the pandemic response. What does the bulk of subsequent evidence show about their effects on children?
>
> ANS:  Substantial learning loss, mental-health harm, and developmental setbacks, with lasting effects worst for poor and minority children
>
> CTX:  The 2022 NAEP ('Nation's Report Card') showed the largest declines in reading and math scores in the assessment's history. Studies from Stanford's CREDO, Harvard's Strategic Data Project, and McKinsey documented major learning losses concentrated in poorer and minority districts where school closures lasted longest. Sweden, which kept lower-grade s…

**After** — story in stem, recognition in answer:

> STEM: The 2022 NAEP showed the largest declines in reading and math scores in the assessment's history — concentrated in poorer and minority districts where closures lasted longest. Sweden, which kept under-16 schools open, showed smaller losses. What's the recognition?
>
> ANS:  Substantial learning loss and mental-health harm — worst for poor and minority kids, as GBD warned
>
> CTX:  Studies from Stanford's CREDO, Harvard's Strategic Data Project, and McKinsey documented the disparate impact. Sweden's policy choice provided a real comparison case.

### bank_idx 767 (T3)

- chars: 663/680 (target), grace 714
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: Twitter Files releases starting in late 2022 documented federal agency contacts with social media platforms during 2020-2022. What kind of scientific speech was suppressed under these contacts?
>
> ANS:  Discussion of lab leak, COVID treatments — vaccine side effects, and the Great Barrington Declaration were all flagged
>
> CTX:  The Twitter Files (Matt Taibbi, Bari Weiss, Michael Shellenberger, and others starting in November 2022) showed FBI, CDC, and other federal agencies routinely flagging accounts for suppression. Topics included natural-immunity discussions, vaccine adverse-event reports, lab-leak speculation, school-closure critiques, and Great Barrington Declaratio…

**After** — story in stem, recognition in answer:

> STEM: The Twitter Files (starting November 2022) showed FBI and CDC officials flagging specific accounts — including Stanford's Jay Bhattacharya, Harvard's Martin Kulldorff, and Johns Hopkins's Marty Makary. What kind of scientific speech got targeted?
>
> ANS:  Lab leak, vaccine adverse events, and the Great Barrington Declaration — credentialed dissent on public health
>
> CTX:  The Files documented 'visibility filtering' and direct takedown requests. *Murthy v. Missouri* (2024) ruled on standing rather than the First Amendment merits.

### bank_idx 768 (T3)

- chars: 671/680 (target), grace 714
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: The Murthy v. Missouri case in 2024 reached the US Supreme Court on the question of federal-government coordination with social-media platforms to suppress speech. What did the court ultimately rule?
>
> ANS:  The court ruled 6-3 that plaintiffs lacked standing, not reaching the underlying First Amendment question on the merits
>
> CTX:  *Murthy v. Missouri* (originally *Missouri v. Biden*) was filed by Missouri and Louisiana state attorneys general plus individual plaintiffs including Bhattacharya and Kulldorff. The 5th Circuit had ruled against the government. The Supreme Court (June 2024, Barrett writing for the majority) ruled 6-3 that plaintiffs lacked Article III standing — n…

**After** — story in stem, recognition in answer:

> STEM: In June 2024 the Supreme Court ruled 6-3 in *Murthy v. Missouri* that plaintiffs lacked standing — not reaching the First Amendment merits. Justice Alito's dissent called it 'one of the most important free speech cases to reach this Court in years.' Practical effect?
>
> ANS:  The federal-platform coordination record stayed in the docket — the constitutional question remains live
>
> CTX:  Originally *Missouri v. Biden*, filed by Missouri and Louisiana state AGs plus individual plaintiffs Bhattacharya and Kulldorff. The Fifth Circuit had ruled against the government on the merits.

### bank_idx 958 (T4)

- chars: 868/900 (target), grace 945
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: Vaccine mandates during 2021-2022 — imposed by federal agencies, employers, universities, and the military — required individuals to accept a specific medical intervention as a condition of work, school, or travel. From a medical-ethics standpoint, what's the central objection?
>
> ANS:  Informed consent and bodily autonomy are foundational principles codified in the Nuremberg Code, and coerced medical interventions violate them
>
> CTX:  The Nuremberg Code (1947) was drafted after the Doctors' Trial of Nazi physicians and established that voluntary consent of the human subject is absolutely essential. The Declaration of Helsinki (1964) extended these principles. Coercive vaccine mandates — lose your job, lose access to school, lose travel — are coercion even if the substance itself…

**After** — story in stem, recognition in answer:

> STEM: The Nuremberg Code of 1947 — drafted after the Doctors' Trial of Nazi physicians who had conducted lethal experiments — opens: 'The voluntary consent of the human subject is absolutely essential.' Vaccine mandates during 2021-2022 required accepting a specific medical intervention as a condition of work, school, or travel. What's the medical-ethics objection?
>
> ANS:  Coerced medical interventions violate voluntary informed consent — codified in the Nuremberg Code and the 1964 Declaration of Helsinki
>
> CTX:  Coercive mandates — lose your job, lose school access, lose travel — are coercion even if the substance is beneficial. Reasonable people can disagree about underlying risk-benefit. The objection to mandates is about the structure of coercion, not the science of the vaccines themselves.

### bank_idx 964 (T4)

- chars: 800/900 (target), grace 945
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: The Proximal Origin of SARS-CoV-2 paper (Andersen et al., Nature Medicine, March 2020) declared a natural origin and dismissed lab leak. FOIA'd Slack messages later showed the authors had been privately uncertain. What did those messages reveal?
>
> ANS:  The authors discussed lab-leak plausibility in real time even as they drafted the public dismissal, so public certainty didn't match private uncertainty
>
> CTX:  Kristian Andersen, Eddie Holmes, Robert Garry, and co-authors published 'Proximal Origin' in Nature Medicine on March 17, 2020. The paper was widely cited to call lab-leak claims 'misinformation.' House Oversight Committee FOIA releases (2023) showed Andersen and others discussing lab-leak plausibility on Slack the same week they were drafting the …

**After** — story in stem, recognition in answer:

> STEM: On February 1, 2020, Anthony Fauci and Jeremy Farrar held a teleconference where engineering of SARS-CoV-2 was deemed concerning enough to warrant a coordinated response. Six weeks later Andersen, Holmes, and Garry published 'The Proximal Origin of SARS-CoV-2' in *Nature Medicine* declaring natural origin. FOIA'd Slack messages later revealed what?
>
> ANS:  The authors were discussing lab-leak plausibility on Slack the same week — private uncertainty did not match published certainty
>
> CTX:  The paper was cited for over two years to label lab-leak claims 'misinformation.' House Oversight Committee FOIA releases (2023) showed Andersen and others discussing lab-leak plausibility in real time.

### bank_idx 970 (T4)

- chars: 816/900 (target), grace 945
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: In May 2021 — over a year into the pandemic — Facebook quietly changed its content-moderation policy to stop removing posts that claimed COVID-19 was a 'man-made virus.' Why did the policy change?
>
> ANS:  Lab leak no longer met any reasonable definition of misinformation once intelligence agencies and major journalists were openly investigating it
>
> CTX:  Facebook's January 2021 policy had explicitly listed 'COVID-19 is man-made or manufactured' among claims subject to removal. In May 2021, after Nicholas Wade's widely-read essay and growing journalist coverage (Donald McNeil Jr., Katherine Eban), Facebook reversed course. The shift acknowledged what was already true: the lab-leak hypothesis had nev…

**After** — story in stem, recognition in answer:

> STEM: Facebook's January 2021 policy explicitly listed 'COVID-19 is man-made' among claims subject to removal. In May 2021, after Nicholas Wade's essay 'Origin of COVID' and growing reporting by Donald McNeil Jr. and Katherine Eban, Facebook quietly reversed the policy. What did the reversal acknowledge?
>
> ANS:  Lab leak had never been a fringe conspiracy theory — the label was a political artifact, withdrawn once respected journalists made the labeling cost too high
>
> CTX:  Wade's essay (Bulletin of the Atomic Scientists, May 2021) walked through the documentary case for taking lab leak seriously. The intelligence-agency assessments (FBI 2023, DOE 2023) later moved in the same direction.

### bank_idx 976 (T4)

- chars: 883/900 (target), grace 945
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: The focused-protection approach the Great Barrington Declaration proposed in October 2020 was essentially what mainstream pandemic-response planning had recommended for decades — protect the vulnerable, let lower-risk groups develop natural immunity. Why was it treated as radical in 2020?
>
> ANS:  Institutional commitment to lockdown was deep enough that the previously conventional view had to be redescribed as fringe to protect the new policy
>
> CTX:  WHO pandemic-planning documents from 2019 explicitly recommended against population-wide lockdowns and against general school closures. The Imperial College team itself had previously published similar guidance. The shift to 'lockdown is the only ethical response' in March 2020 was a policy choice, not a scientific necessity. Once the institutions …

**After** — story in stem, recognition in answer:

> STEM: WHO pandemic-planning documents from 2019 explicitly recommended against population-wide lockdowns and against general school closures. Imperial College had published similar guidance. By October 2020 the Great Barrington Declaration (proposing focused protection) was attacked as fringe. Why was the previously conventional view redescribed as radical?
>
> ANS:  Institutional commitment to lockdown ran too deep — the previously conventional view had to be redescribed as fringe to protect the new policy
>
> CTX:  The shift to 'lockdown is the only ethical response' in March 2020 was a policy choice, not a scientific necessity. Critics including Donald McNeil Jr., Matt Taibbi, and Jay Bhattacharya documented the pattern.

### bank_idx 1018 (T4)

- chars: 896/900 (target), grace 945
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: Climategate (2009) involved the public release of emails from the Climatic Research Unit at the University of East Anglia. What did the emails reveal about scientific practice in the field?
>
> ANS:  Discussion of how to handle inconvenient data, exclude critics from journals, and frame uncertainty in policy-friendly ways, internal candor not matching public certainty
>
> CTX:  The November 2009 release of CRU emails included phrases like 'hide the decline' (referring to specific paleoclimate data handling), discussion of journals to exclude critics from, and FOIA-evasion remarks. Multiple subsequent inquiries (Muir Russell, Penn State, Independent Climate Change Email Review) found no scientific fraud but did identify is…

**After** — story in stem, recognition in answer:

> STEM: In November 2009 emails from the Climatic Research Unit at the University of East Anglia were released to the public. They included the phrase 'hide the decline' (a paleoclimate data-handling choice), discussions of journals to exclude critics from, and FOIA-evasion remarks. What did the emails reveal about scientific practice?
>
> ANS:  Internal candor handled inconvenient data, excluded critics from journals, and framed uncertainty — in ways public statements of confidence did not show
>
> CTX:  Multiple inquiries (Muir Russell, Penn State, Independent Climate Change Email Review) found no scientific fraud but did identify issues with FOIA compliance, openness, and treatment of critics.

### bank_idx 1233 (T5)

- chars: 1040/1100 (target), grace 1155
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: J. Marion Sims, often called the 'father of modern gynecology,' developed his surgical techniques for vesicovaginal fistula in the 1840s by operating repeatedly on enslaved women in Alabama. He performed one operation on a woman named Anarcha 30 times without anesthesia. What's the honest historical recognition?
>
> ANS:  Foundational techniques in a medical specialty were developed through experimentation on people who had no legal or actual capacity to refuse
>
> CTX:  Anarcha (subjected to 30 operations), Betsey, and Lucy are the named enslaved women on whom Sims developed his fistula repair. He claimed in his autobiography that anesthesia (ether, available from 1846) was unsuitable for the procedure; his contemporary white patients later received anesthesia. The New York statue of Sims in Central Park was remov…

**After** — story in stem, recognition in answer:

> STEM: Three enslaved women — Anarcha (subjected to 30 operations without anesthesia), Betsey, and Lucy — were the patients on whom J. Marion Sims developed his vesicovaginal fistula surgical technique in 1840s Alabama. His contemporary white patients later received ether anesthesia. In 2018, after years of advocacy, his statue was removed from Central Park. What's the honest recognition?
>
> ANS:  Foundational gynecological techniques came from experimentation on people who had no capacity to refuse — the discoveries are real and the methods were grievously wrong
>
> CTX:  Sims claimed in his autobiography that anesthesia (ether, available from 1846) was unsuitable for the procedure; his white patients later received it. The naming question — does honoring a discoverer require silence about the methods — is one of the bank's substantive cases.

### bank_idx 1246 (T5)

- chars: 1047/1100 (target), grace 1155
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: Robert Malone helped develop the mRNA-lipid-nanoparticle delivery technology in the late 1980s. In 2021 he publicly questioned the COVID mRNA vaccine rollout's risk-benefit analysis for young healthy adults. What happened to him on major social platforms?
>
> ANS:  He was suspended from Twitter (later reinstated), demonetized on YouTube, and his interview with Joe Rogan triggered a major Spotify controversy
>
> CTX:  Malone's December 2021 interview on the Joe Rogan Experience (episode #1757) triggered Neil Young's protest withdrawal from Spotify in January 2022; Spotify added 'COVID-19 advisory notices' to certain episodes. Malone's broader argument — that the risk-benefit calculation for healthy young adults differed from that for elderly high-risk population…

**After** — story in stem, recognition in answer:

> STEM: Robert Malone helped develop mRNA lipid-nanoparticle delivery in the late 1980s (US patents 1989-1991). In December 2021 his three-hour interview on Joe Rogan Experience #1757 questioned the COVID mRNA vaccine rollout's risk-benefit for young healthy adults. Within weeks Neil Young withdrew his catalog from Spotify in protest. What was the major-platform response to a credentialed mRNA pioneer raising safety questions?
>
> ANS:  Suspended from Twitter (later reinstated), demonetized on YouTube; Spotify added 'COVID-19 advisory notices' to specific episodes rather than remove them
>
> CTX:  Malone's broader argument — that risk-benefit for healthy young adults differed from that for elderly high-risk populations — has been at least partially vindicated by subsequent data on myocarditis (Tracy Beth Hoeg) and on the trial limitations the FDA's released Pfizer documents revealed.

### bank_idx 1279 (T5)

- chars: 1055/1100 (target), grace 1155
- verdict: **PASS**

**Before** — buried-story pattern:

> STEM: The Tuskegee Syphilis Study (1932-1972) is the canonical American medical-ethics atrocity case. Less discussed is the Guatemala syphilis study (1946-1948), conducted by some of the same US Public Health Service researchers. What did the Guatemala study do?
>
> ANS:  Researchers deliberately infected Guatemalan prisoners, soldiers, and psychiatric patients with syphilis and gonorrhea to study transmission and treatment, with no informed consent
>
> CTX:  Susan Reverby, a Wellesley historian, discovered the records of the Guatemala study in 2005 while researching Tuskegee. Her 2010 paper made the case public. President Obama formally apologized to Guatemala in October 2010. Researchers deliberately exposed about 1,300 subjects to syphilis (often via direct inoculation of bacteria on abrasions or gen…

**After** — story in stem, recognition in answer:

> STEM: In 2005 Wellesley historian Susan Reverby found archived records: between 1946 and 1948, US Public Health Service researcher John Cutler (later a Tuskegee investigator) deliberately infected roughly 1,300 Guatemalan prisoners, soldiers, and psychiatric patients with syphilis and gonorrhea — often by inoculating bacteria onto abrasions or genital surfaces. President Obama formally apologized to Guatemala in October 2010. What does this case reveal?
>
> ANS:  Tuskegee was a pattern, not an aberration — the same USPHS network ran nonconsensual disease-exposure studies on poor and powerless populations for decades
>
> CTX:  Reverby's 2010 paper made the case public. The Guatemala case sits with Tuskegee (1932-1972), Sims's enslaved-women surgeries, the Henrietta Lacks case, and the Belmont Report (1979) as foundational US medical-ethics history.

## Patch artifact

- Patch file: `_buried_story_patch.json` (16 rewrites)
- Each entry: `{"find_substring": <unique fragment from old stem>, "new": {full question}}`

Apply with: scan each bank entry; if any one has `find_substring` in its `question`, swap the whole record for `new`.
