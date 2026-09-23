import sqlite3

DB_FILE = "/Users/couozu/.gemini/antigravity/scratch/spanish_learning/vocab.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Find all words that still have "el " or "la " prefix
# and strip the article — these are leftovers from the bad heuristic
c.execute("SELECT id, word FROM words WHERE (word LIKE 'el %' OR word LIKE 'la %') AND is_ignored = 0")
rows = c.fetchall()

fixed = 0
for w_id, word in rows:
    # Strip the article prefix
    if word.startswith("el "):
        original = word[3:]
    elif word.startswith("la "):
        original = word[3:]
    else:
        continue
    
    try:
        c.execute("UPDATE words SET word = ? WHERE id = ?", (original, w_id))
        fixed += 1
    except sqlite3.IntegrityError:
        # duplicate after stripping — ignore this one
        c.execute("UPDATE words SET is_ignored = 1 WHERE id = ?", (w_id,))
        fixed += 1

conn.commit()
print(f"Fixed {fixed} remaining words with bad article prefixes")

# Verify
c.execute("SELECT count(*) FROM words WHERE (word LIKE 'el %' OR word LIKE 'la %') AND is_ignored = 0")
print(f"Remaining words with 'el '/'la ' prefix: {c.fetchone()[0]}")

c.execute("SELECT count(*) FROM words WHERE is_ignored = 0")
print(f"Total active words: {c.fetchone()[0]}")

conn.close()
