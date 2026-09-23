import sqlite3

DB_FILE = "/Users/couozu/.gemini/antigravity/scratch/spanish_learning/vocab.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# First, lock everything and reset active fields
c.execute("UPDATE words SET is_active_unlocked = 0, active_next_review = NULL, active_interval = 0, active_repetitions = 0, active_ease_factor = 2.5")

# Find words that SHOULD be unlocked (reps >= 3)
c.execute("SELECT id FROM words WHERE repetitions >= 3")
unlocked_words = [row[0] for row in c.fetchall()]

# Unlock them
for w_id in unlocked_words:
    c.execute("UPDATE words SET is_active_unlocked = 1, active_next_review = '2020-01-01' WHERE id = ?", (w_id,))

# Now, restore active_next_review for words that were ACTUALLY reviewed actively
c.execute('''
    SELECT word_id, MAX(reviewed_at)
    FROM history
    WHERE result LIKE 'active_%'
    GROUP BY word_id
''')
active_last_reviews = dict(c.fetchall())

c.execute("SELECT id, active_interval FROM words WHERE is_active_unlocked = 1 AND active_interval > 0")
for w_id, a_int in c.fetchall():
    if w_id in active_last_reviews:
        from datetime import datetime, timedelta
        last_date = datetime.fromisoformat(active_last_reviews[w_id])
        next_date = last_date + timedelta(days=a_int)
        c.execute("UPDATE words SET active_next_review = ? WHERE id = ?", (next_date.isoformat(), w_id))

conn.commit()
conn.close()
print("Restored active unlock state!")
