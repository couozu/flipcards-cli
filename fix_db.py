import sqlite3
from datetime import datetime, timedelta

DB_FILE = "/Users/couozu/.gemini/antigravity/scratch/spanish_learning/vocab.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Get max reviewed_at for each word (passive only)
c.execute('''
    SELECT word_id, MAX(reviewed_at)
    FROM history
    WHERE result LIKE 'passive_%' OR result IN ('known', 'unknown')
    GROUP BY word_id
''')
last_reviews = dict(c.fetchall())

c.execute("SELECT id, interval FROM words WHERE interval > 0")
words_with_interval = c.fetchall()

restored = 0
for word_id, interval in words_with_interval:
    if word_id in last_reviews:
        try:
            last_date = datetime.fromisoformat(last_reviews[word_id])
            next_date = last_date + timedelta(days=interval)
            c.execute("UPDATE words SET next_review = ? WHERE id = ?", (next_date.isoformat(), word_id))
            restored += 1
        except Exception as e:
            print(f"Error on {word_id}: {e}")

conn.commit()
conn.close()
print(f"Restored next_review for {restored} cards that were pushed to the future!")
