import sqlite3
import json
import os

DB_FILE = "/Users/couozu/.gemini/antigravity/scratch/spanish_learning/vocab.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

c.execute("SELECT id, word, translation, hint FROM words")
db_words = c.fetchall()

original_words = {}
def load_json(path):
    if not os.path.exists(path): return
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            word = item.get('word', '').lower().strip()
            trans = item.get('translation', '').strip()
            hint = item.get('hint', '').strip()
            if trans:
                original_words[(trans, hint)] = word

load_json('/tmp/vocab_all.json')
load_json('/tmp/missing_vocab.json')

restored = 0
for w_id, current_word, trans, hint in db_words:
    orig = original_words.get((trans, hint))
    if orig and orig != current_word:
        c.execute("UPDATE words SET word = ? WHERE id = ?", (orig, w_id))
        restored += 1

# What about the 8 imperatives I added manually?
# They are fine as they are.
# What about "él"? I changed its translation to "он". Let's fix that.
c.execute("UPDATE words SET word = 'él' WHERE id = 27")

conn.commit()
conn.close()
print(f"Restored {restored} words to their original form (removed bad articles)!")
