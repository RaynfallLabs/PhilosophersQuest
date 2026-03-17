"""
Restore original trivia, remove unwanted franchises, keep the rest.
New questions will be added by a separate agent.
"""
import json, re

with open('data/trivia_original_backup.json', encoding='utf-8') as f:
    qs = json.load(f)

# Franchises to remove (keywords matched against question text, case-insensitive)
REMOVE_KEYWORDS = [
    'tarzan',
    "bug's life", 'a bug\'s life', "bug's life",
    'treasure planet',
    'gargoyles',
    'adventure time', 'finn and jake', 'ice king', 'marceline',
    "foster's home", "foster's", 'imaginary friends', 'bloo', 'mac and bloo',
    'ed edd', 'ed, edd', 'eddy',
    'gumball', 'amazing world of gumball',
    'courage the cowardly', 'courage the dog',
    'samurai jack',
    'chowder',
    'regular show', 'mordecai and rigby',
    'dexter\'s lab', "dexter's laboratory",
    'cow and chicken',
    'grim adventures', 'billy and mandy', 'grim reaper',
    'hollow knight', 'hallownest',
]

def should_remove(q):
    text = (q.get('question', '') + ' ' + q.get('answer', '') + ' ' + ' '.join(q.get('choices', []))).lower()
    for kw in REMOVE_KEYWORDS:
        if kw in text:
            return True
    return False

kept = [q for q in qs if not should_remove(q)]
removed = len(qs) - len(kept)

print(f'Original: {len(qs)} questions')
print(f'Removed:  {removed} questions (unwanted franchises)')
print(f'Kept:     {len(kept)} questions')

with open('data/questions/trivia.json', 'w', encoding='utf-8') as f:
    json.dump(kept, f, indent=2, ensure_ascii=False)

print('Saved to data/questions/trivia.json')
