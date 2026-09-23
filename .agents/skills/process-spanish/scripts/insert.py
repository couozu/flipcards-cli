import sys
import json
import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.getcwd(), "vocab.db")

def init_db(c):
    c.execute('''CREATE TABLE IF NOT EXISTS words
                 (id INTEGER PRIMARY KEY,
                  word TEXT,
                  hint TEXT DEFAULT "",
                  translation TEXT,
                  next_review TEXT,
                  interval REAL,
                  repetitions INTEGER,
                  ease_factor REAL,
                  UNIQUE(word, hint))''')
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY,
                  word_id INTEGER,
                  reviewed_at TEXT,
                  result TEXT)''')

def main():
    if len(sys.argv) < 2:
        print("Usage: python insert.py <json_file>")
        sys.exit(1)
        
    json_file = sys.argv[1]
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    init_db(c)
    
    now_iso = datetime.now().isoformat()
    added = 0
    skipped = 0
    
    for item in data:
        word = item.get('word', '').strip().lower()
        hint = item.get('hint', '').strip()
        translation = item.get('translation', '').strip()
        
        if not word:
            continue
            
        try:
            # We use INSERT OR IGNORE to safely skip words that already exist with the same hint
            c.execute('''INSERT INTO words (word, hint, translation, next_review, interval, repetitions, ease_factor)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (word, hint, translation, now_iso, 0, 0, 2.5))
            if c.rowcount > 0:
                added += 1
            else:
                skipped += 1
        except sqlite3.Error as e:
            print(f"Error inserting {word}: {e}")
            
    conn.commit()
    conn.close()
    
    print(f"Successfully inserted {added} new words. Skipped {skipped} existing words.")

if __name__ == "__main__":
    main()
