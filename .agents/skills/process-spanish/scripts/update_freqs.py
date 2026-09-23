import json
import sqlite3
import re
from collections import Counter
import sys
import os

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "vocab.db")

def main():
    if len(sys.argv) < 3:
        print("Usage: python update_freqs.py <source_text_file> <json_file>")
        sys.exit(1)
        
    text_file = sys.argv[1]
    json_file = sys.argv[2]
    
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read().lower()

    words_in_text = re.findall(r'[a-záéíóúñü]+', text)
    counts = Counter(words_in_text)
    
    word_to_raw = {}
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            word = item.get('word', '').lower().strip()
            if not word: continue
            raws = item.get('raw_words', [])
            cleaned_raws = set()
            for r in raws:
                cleaned = re.findall(r'[a-záéíóúñü]+', r.lower())
                cleaned_raws.update(cleaned)
            if word not in word_to_raw:
                word_to_raw[word] = set()
            word_to_raw[word].update(cleaned_raws)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Ensure column exists
    c.execute("PRAGMA table_info(words)")
    columns = [col[1] for col in c.fetchall()]
    if "frequency" not in columns:
        c.execute("ALTER TABLE words ADD COLUMN frequency INTEGER DEFAULT 0")

    updated = 0
    for word, raws in word_to_raw.items():
        freq = 0
        for r in raws:
            freq += counts.get(r, 0)
        if word not in raws:
            freq += counts.get(word, 0)
            
        if freq > 0:
            # We add to the existing frequency so it's cumulative across episodes!
            c.execute("UPDATE words SET frequency = frequency + ? WHERE word = ?", (freq, word))
            updated += 1

    conn.commit()
    conn.close()
    print(f"Updated frequencies for {updated} words based on the text.")

if __name__ == "__main__":
    main()
