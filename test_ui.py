import sqlite3
from learn import get_word_details
conn = sqlite3.connect('vocab.db')
c = conn.cursor()
c.execute("SELECT id FROM russian_words WHERE word = 'история'")
word_id = c.fetchone()[0]
print(get_word_details(conn, word_id, is_active=True))
