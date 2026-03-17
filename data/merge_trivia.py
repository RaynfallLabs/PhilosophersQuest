import json

with open('data/questions/trivia.json', encoding='utf-8') as f:
    existing = json.load(f)

with open('data/trivia_new_questions.json', encoding='utf-8') as f:
    new_qs = json.load(f)

valid = []
skipped = 0
for q in new_qs:
    if not q.get('question') or not q.get('answer'):
        skipped += 1
        continue
    if len(q.get('choices', [])) != 4:
        skipped += 1
        continue
    if q['answer'] not in q['choices']:
        skipped += 1
        continue
    valid.append(q)

combined = existing + valid

texts = [q.get('question', '').lower().strip() for q in combined]
dupes = len(texts) - len(set(texts))
raw = json.dumps(combined, ensure_ascii=False)
bad = sum(1 for c in raw if ord(c) > 127)

print(f'Existing: {len(existing)} | New valid: {len(valid)} | Skipped: {skipped}')
print(f'Combined: {len(combined)} | Dupes: {dupes} | Non-ASCII: {bad}')

with open('data/questions/trivia.json', 'w', encoding='utf-8') as f:
    json.dump(combined, f, indent=2, ensure_ascii=False)
print('Saved.')
