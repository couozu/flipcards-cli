import sqlite3
import json
import os

DB_FILE = "/Users/couozu/.gemini/antigravity/scratch/spanish_learning/vocab.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# First, back up the database
import shutil
shutil.copy2(DB_FILE, DB_FILE + ".bak")
print("Created backup: vocab.db.bak")

# Load original words from JSON files, keyed by translation+hint
original_words = {}
def load_json(path):
    if not os.path.exists(path): return
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            word = item.get('word', '').strip()
            trans = item.get('translation', '').strip()
            hint = item.get('hint', '').strip()
            if word and trans:
                original_words[(trans, hint)] = word

load_json('/tmp/vocab_all.json')
load_json('/tmp/missing_vocab.json')
print(f"Loaded {len(original_words)} original words from JSON files")

# Get all current DB words
c.execute("SELECT id, word, translation, hint, is_ignored FROM words")
db_words = c.fetchall()

restored = 0
skipped = 0
for w_id, current_word, trans, hint, ignored in db_words:
    orig = original_words.get((trans, hint or ''))
    if orig and orig != current_word:
        try:
            c.execute("UPDATE words SET word = ? WHERE id = ?", (orig, w_id))
            restored += 1
        except sqlite3.IntegrityError:
            # Duplicate — this is a duplicate entry, mark it as ignored
            c.execute("UPDATE words SET is_ignored = 1 WHERE id = ?", (w_id,))
            skipped += 1

# Fix él specifically — I changed translation to just "он" earlier
c.execute("UPDATE words SET translation = 'он' WHERE id = 27")

conn.commit()

# Verify some key words
print(f"\nRestored {restored} words, skipped {skipped} duplicates")
c.execute("SELECT id, word, translation FROM words WHERE word IN ('ella', 'la', 'el', 'él') AND is_ignored = 0")
for row in c.fetchall():
    print(f"  id={row[0]}: {row[1]} — {row[2]}")

c.execute("SELECT count(*) FROM words WHERE is_ignored = 0")
print(f"\nTotal active words: {c.fetchone()[0]}")

conn.close()
