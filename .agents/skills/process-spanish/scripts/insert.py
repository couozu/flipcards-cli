import sys
import json
import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.getcwd(), "vocab.db")

def init_db(c):
    # Just to be safe, though learn.py handles full schema creation
    pass

def main():
    if len(sys.argv) < 2:
        print("Usage: python insert.py <json_file>")
        sys.exit(1)
        
    json_file = sys.argv[1]
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    now_iso = datetime.now().isoformat()
    added_sp = 0
    added_ru = 0
    added_links = 0
    
    for item in data:
        word = item.get('word', '').strip().lower()
        hint = item.get('hint', '').strip()
        translation = item.get('translation', '').strip().lower()
        
        if not word or not translation:
            continue
            
        # Spanish word
        c.execute("SELECT id FROM spanish_words WHERE word = ?", (word,))
        row = c.fetchone()
        if not row:
            c.execute('''INSERT INTO spanish_words (word, next_review, interval, repetitions, ease_factor, passive_ignored)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (word, now_iso, 0, 0, 2.5, 0))
            sp_id = c.lastrowid
            added_sp += 1
        else:
            sp_id = row[0]
            
        # Russian word
        c.execute("SELECT id FROM russian_words WHERE word = ?", (translation,))
        row = c.fetchone()
        if not row:
            c.execute('''INSERT INTO russian_words (word, active_next_review, active_interval, active_repetitions, active_ease_factor, active_ignored)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (translation, now_iso, 0, 0, 2.5, 0))
            ru_id = c.lastrowid
            added_ru += 1
        else:
            ru_id = row[0]
            
        # Link
        try:
            c.execute("INSERT OR IGNORE INTO word_links (spanish_id, russian_id, hint) VALUES (?, ?, ?)",
                      (sp_id, ru_id, hint))
            if c.rowcount > 0:
                added_links += 1
        except sqlite3.Error as e:
            print(f"Error inserting link for {word}: {e}")
            
    conn.commit()
    conn.close()
    
    print(f"Successfully inserted {added_sp} new Spanish words, {added_ru} new Russian words, and {added_links} new links.")

if __name__ == "__main__":
    main()

    import dedup
    dedup.run_dedup()
