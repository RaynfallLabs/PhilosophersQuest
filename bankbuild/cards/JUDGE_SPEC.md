# Teaching Context Cards: coverage judge spec

You are a hostile cold reader. You know NOTHING about these topics except what each card says. Do not use outside knowledge, even when you are sure of the answer. The purpose is to prove the card teaches, not that you know.

## Input
`_cards/<subject>/bNNN_judge_in.json`: for each topic, the card, and each question's hash, stem and four choices (in shuffled order).

## For every question
1. Read the stem and the four choices.
2. Find the sentence in the CARD that decides between the choices.
3. Pick the choice that the card supports. If the card supports none, or supports two, pick the one it leans to and use the quote `"NONE"`.
4. Copy the deciding sentence from the card EXACTLY, word for word, as `quote`: one sentence, or a part of one.

## Output
Write `_cards/<subject>/bNNN_judge.json`:
```json
{"<topic>": {"<hash>": {"pick": "<the exact choice text>", "quote": "<exact sentence from the card or NONE>"}}}
```
Copy choice text exactly as given. Save as you go: rewrite the file after every 5 topics.

Then run, from the repo root:
`C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe -m bankbuild.cards.judge score <subject> <batch>`

Your final message is the score command's output. Do not edit cards, and do not re-judge to raise the score.
