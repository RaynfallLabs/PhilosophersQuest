# Deterministic pipeline report — philosophy

- Run started: `2026-05-11T05:42:23.829803+00:00`
- moral_vision.md SHA: `7c6894d71c58`
- Questions evaluated: **615**

## Verdict distribution (deterministic-only)

| Verdict | Count | % |
|---|---:|---:|
| KEEP | 136 | 22.1% |
| REPAIR | 479 | 77.9% |
| DISCARD | 0 | 0.0% |

## Gate-by-gate fail counts

| Gate | Fails | % of n |
|---|---:|---:|
| length_parity | 340 | 55.3% |
| anti_rote | 194 | 31.5% |
| length_budget | 98 | 15.9% |
| duplicate | 34 | 5.5% |

## Verdict by tier

| Tier | n | KEEP | REPAIR | DISCARD |
|---|---:|---:|---:|---:|
| 1 | 73 | 18 | 55 | 0 |
| 2 | 158 | 43 | 115 | 0 |
| 3 | 176 | 41 | 135 | 0 |
| 4 | 133 | 29 | 104 | 0 |
| 5 | 75 | 5 | 70 | 0 |

## Failure modes per tier

### Tier 1

- length_parity: 51 fails
- anti_rote: 10 fails
- length_budget: 3 fails
- duplicate: 1 fails

### Tier 2

- length_parity: 78 fails
- anti_rote: 48 fails
- length_budget: 21 fails
- duplicate: 11 fails

### Tier 3

- length_parity: 91 fails
- anti_rote: 61 fails
- length_budget: 39 fails
- duplicate: 12 fails

### Tier 4

- length_parity: 61 fails
- anti_rote: 57 fails
- duplicate: 8 fails
- length_budget: 8 fails

### Tier 5

- length_parity: 59 fails
- length_budget: 27 fails
- anti_rote: 18 fails
- duplicate: 2 fails

## Per-question detail (failed only)

_479 questions with at least one failed gate._

| Idx | Tier | Verdict | Failed gates | Preview |
|---|---|---|---|---|
| 0 | 2 | REPAIR | length_parity | Socrates never lectured or wrote textbooks. Instead, he would approach strangers... |
| 1 | 1 | REPAIR | length_parity | Who was the tutor of Alexander the Great? |
| 3 | 2 | REPAIR | length_parity | What was Socrates's most famous philosophical claim? |
| 6 | 2 | REPAIR | length_parity | Confucianism emphasizes 'ren' as the highest virtue. What does 'ren' mean? |
| 7 | 3 | REPAIR | length_parity | Plato argued the soul survives death because it knows eternal truths before birt... |
| 12 | 2 | REPAIR | length_parity | Heraclitus said 'You cannot step in the same river twice.' What philosophical cl... |
| 14 | 2 | REPAIR | length_parity | Plato argued that physical objects around us — tables, trees, beautiful things —... |
| 17 | 1 | REPAIR | anti_rote | What does 'ethics' study? |
| 18 | 2 | REPAIR | length_parity | What branch of philosophy deals with the study of knowledge? |
| 21 | 2 | REPAIR | length_parity | Berkeley argued that a tree you are not looking at does not actually exist at th... |
| 24 | 2 | REPAIR | length_parity | Epicurus taught that the goal of life is pleasure — but his idea of the highest ... |
| 25 | 3 | REPAIR | length_parity | Who was Confucius's most influential follower who extended his teachings? |
| 27 | 3 | REPAIR | length_parity | Which philosopher wrote 'On the Nature of Things', describing a world of atoms? |
| 30 | 1 | REPAIR | length_parity | Which philosopher said 'In the beginning was the Word'? |
| 31 | 1 | REPAIR | anti_rote | What is 'Plato's cave' an allegory for? |
| 36 | 2 | REPAIR | length_parity | What is a 'syllogism'? |
| 37 | 2 | REPAIR | length_parity, length_budget | The Stoic philosopher Epictetus was born a slave and spent his life in chains. Y... |
| 39 | 2 | REPAIR | length_parity, anti_rote, duplicate | What is the 'social contract' theory about? |
| 40 | 2 | REPAIR | length_parity | Kant believed there is one moral test that settles any ethical question. Before ... |
| 41 | 2 | REPAIR | length_parity | When Nietzsche wrote 'God is dead,' he was not celebrating. He was sounding an a... |
| 42 | 2 | REPAIR | length_parity, anti_rote, duplicate | What does 'skepticism' mean in philosophy? |
| 43 | 2 | REPAIR | length_parity, length_budget | Locke argued that when a government fails to protect citizens' natural rights, c... |
| 44 | 2 | REPAIR | length_parity, length_budget | Jeremy Bentham argued that every moral decision should be made by a single calcu... |
| 45 | 2 | REPAIR | length_parity, length_budget | John Stuart Mill agreed with Bentham that the goal of morality is maximizing hap... |
| 46 | 2 | REPAIR | length_parity, length_budget | Diogenes of Sinope was the ancient world's most famous philosopher-provocateur. ... |
| 47 | 2 | REPAIR | anti_rote | What is 'Zeno's paradox' about? |
| 48 | 2 | REPAIR | anti_rote | What is the 'problem of evil' in philosophy? |
| 49 | 2 | REPAIR | length_parity | Locke argued that the human mind at birth is a blank slate — completely empty of... |
| 50 | 2 | REPAIR | length_parity | What did John Locke believe people are born with? |
| 51 | 3 | REPAIR | length_budget | Marx claimed to have taken Hegel's dialectic and turned it 'right side up.' What... |
| 52 | 2 | REPAIR | length_parity, anti_rote | What is 'deontological ethics'? |
| 54 | 2 | REPAIR | anti_rote | What is 'Occam's Razor'? |
| 55 | 2 | REPAIR | anti_rote | Who wrote 'The Art of War', a strategic philosophical text on conflict and tacti... |
| 57 | 2 | REPAIR | length_parity | Descartes argued that your idea of a perfect, infinite God cannot possibly have ... |
| 58 | 2 | REPAIR | length_parity, length_budget | Francis Bacon argued that human minds are naturally corrupted by four types of s... |
| 59 | 2 | REPAIR | anti_rote | What does 'a posteriori' mean in philosophy? |
| 60 | 2 | REPAIR | length_parity | Nietzsche's 'will to power' is often misunderstood as a desire to dominate other... |
| 61 | 2 | REPAIR | anti_rote | What is the 'prisoner's dilemma'? |
| 63 | 2 | REPAIR | anti_rote | What is 'nihilism'? |
| 64 | 2 | REPAIR | anti_rote | What is the 'veil of ignorance' in political philosophy? |
| 65 | 2 | REPAIR | length_parity | Rawls argued that some inequalities in a just society are acceptable — but only ... |
| 66 | 2 | REPAIR | length_parity, length_budget | Marx argued that all of history is the story of class struggle — owners against ... |
| 68 | 2 | REPAIR | length_parity | Kant argued that moral duty requires treating persons as ends in themselves, nev... |
| 71 | 2 | REPAIR | anti_rote | Who wrote 'Discourses' and taught that only virtue is truly good? |
| 72 | 2 | REPAIR | anti_rote, duplicate | What is 'epistemology'? |
| 73 | 3 | REPAIR | anti_rote | What is the 'brain in a vat' thought experiment designed to question? |
| 74 | 3 | REPAIR | length_parity, length_budget | Descartes tried to doubt absolutely everything — he even imagined that an all-po... |
| 76 | 3 | REPAIR | anti_rote | What is the 'problem of other minds'? |
| 77 | 3 | REPAIR | length_parity, length_budget | Kant claimed that you never perceive reality as it actually is — only as filtere... |
| 78 | 3 | REPAIR | length_parity | Who is most associated with virtue ethics in ancient Greece? |
| 79 | 3 | REPAIR | length_parity, length_budget | Bentham said all pleasures are equal — if you get equal pleasure from reading Sh... |
| 80 | 2 | REPAIR | length_parity, anti_rote, duplicate | What is 'moral relativism'? |
| 81 | 3 | REPAIR | length_parity, length_budget | Hegel argued that ideas, cultures, and consciousness itself develop through a sp... |
| 82 | 3 | REPAIR | length_parity, length_budget | Nietzsche wrote: 'What does not kill me makes me stronger.' He did not mean this... |
| 83 | 3 | REPAIR | length_parity, anti_rote | What is the 'Chinese Room' thought experiment? |
| 84 | 3 | REPAIR | length_parity, length_budget | John Searle imagined a person locked in a room who receives Chinese symbols thro... |
| 85 | 2 | REPAIR | length_parity, anti_rote | What is 'solipsism'? |
| 86 | 3 | REPAIR | length_parity | Heidegger argued that Western philosophy had spent 2,500 years asking the wrong ... |
| 87 | 2 | REPAIR | anti_rote, duplicate | What is 'absurdism' in philosophy? |
| 88 | 3 | REPAIR | length_parity, anti_rote | What does 'free will' mean in philosophy? |
| 89 | 2 | REPAIR | length_parity, anti_rote, duplicate | What is 'determinism'? |
| 90 | 3 | REPAIR | length_parity, length_budget | Simone de Beauvoir argued that 'woman' is not a natural category — it is a const... |
| 91 | 3 | REPAIR | length_parity, length_budget | Nietzsche's Zarathustra announces that 'God is dead' and challenges humanity to ... |
| 92 | 3 | REPAIR | length_parity | The American pragmatist philosophers made a radical claim about truth that most ... |
| 93 | 3 | REPAIR | length_budget | Isaiah Berlin distinguished 'negative liberty' (freedom from interference) from ... |
| 95 | 3 | REPAIR | length_parity, length_budget | Spinoza argued that God and Nature are two names for the same single infinite su... |
| 96 | 3 | REPAIR | length_budget | The early Wittgenstein argued that language has a hard outer limit: it can only ... |
| 97 | 3 | REPAIR | length_parity, length_budget | Hume pointed out a logical gap that has troubled moral philosophers ever since: ... |
| 98 | 3 | REPAIR | length_parity, anti_rote, duplicate | What is the 'Gettier problem'? |
| 99 | 3 | REPAIR | anti_rote | What does 'teleology' mean? |
| 100 | 3 | REPAIR | length_parity, length_budget | Locke argued that you acquire ownership of unowned land or resources by mixing y... |
| 101 | 3 | REPAIR | length_parity | Aquinas argued that you do not need scripture or revelation to know the differen... |
| 102 | 3 | REPAIR | length_parity, length_budget | Descartes concluded that his mind and his body are completely different kinds of... |
| 103 | 3 | REPAIR | anti_rote | What is 'moral absolutism'? |
| 104 | 3 | REPAIR | length_budget | Nietzsche proposed imagining that you will live your exact life over and over ag... |
| 105 | 2 | REPAIR | anti_rote | What is 'social constructivism'? |
| 106 | 3 | REPAIR | length_parity, length_budget | Darwin's theory of evolution forced a specific philosophical revolution that wen... |
| 107 | 3 | REPAIR | anti_rote | What is 'epistemic justification'? |
| 109 | 1 | REPAIR | length_parity, anti_rote | What is 'metaphysics'? |
| 110 | 4 | REPAIR | length_parity | David Chalmers argued that explaining how the brain produces behavior — however ... |
| 111 | 3 | REPAIR | anti_rote, duplicate | What is 'qualia' in philosophy of mind? |
| 112 | 3 | REPAIR | anti_rote | What is 'physicalism'? |
| 113 | 3 | REPAIR | length_parity, anti_rote, duplicate | What is 'idealism' in philosophy? |
| 116 | 3 | REPAIR | length_parity | What is Rawls's 'difference principle'? |
| 117 | 4 | REPAIR | anti_rote | What is 'compatibilism' in philosophy? |
| 118 | 3 | REPAIR | anti_rote | What is the 'mind-body problem'? |
| 119 | 4 | REPAIR | anti_rote | What is 'eliminative materialism'? |
| 120 | 4 | REPAIR | length_parity | The Churchlands argued that beliefs, desires, and memories are like 'phlogiston'... |
| 121 | 4 | REPAIR | length_parity | Clive Bell argued that the subject matter of a painting is entirely irrelevant t... |
| 122 | 4 | REPAIR | length_parity | In Hegel's master-slave dialectic, two people fight to the death for recognition... |
| 123 | 3 | REPAIR | anti_rote | What is 'intersubjectivity'? |
| 124 | 3 | REPAIR | length_parity | Rousseau argued that human beings are naturally good but corrupted by civilizati... |
| 125 | 4 | REPAIR | length_parity | Isaiah Berlin warned that 'positive liberty' — freedom to achieve your true pote... |
| 126 | 3 | REPAIR | length_parity, anti_rote | What is 'negative liberty'? |
| 127 | 3 | REPAIR | anti_rote | What is 'positive liberty'? |
| 128 | 3 | REPAIR | anti_rote | What is 'communitarianism'? |
| 129 | 3 | REPAIR | length_parity, anti_rote, duplicate | What is 'formal logic'? |
| 130 | 4 | REPAIR | length_parity | Before Frege, logic could handle arguments like 'All men are mortal; Socrates is... |
| 132 | 4 | REPAIR | length_parity, anti_rote | What is 'modus ponens'? |
| 133 | 4 | REPAIR | length_parity | When you call both a fire truck and a stop sign 'red,' you are using one word fo... |

_(showing first 100 of 479 failures; full data in report.json)_
