import sys
import sqlite3
import re
from datetime import datetime
import os

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None
    print("Warning: deep-translator is not installed. Translations will be empty.")

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocab.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS words
                 (id INTEGER PRIMARY KEY,
                  word TEXT UNIQUE,
                  translation TEXT,
                  next_review TEXT,
                  interval REAL,
                  repetitions INTEGER,
                  ease_factor REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY,
                  word_id INTEGER,
                  reviewed_at TEXT,
                  result TEXT)''')
    conn.commit()
    return conn

def process_text(text):
    # Keep only Spanish words (latin + special characters)
    words = re.findall(r'[a-záéíóúñü]+', text.lower())
    # Filter short words
    unique_words = set(w for w in words if len(w) > 2)
    return unique_words

def add_words_to_db(words_set):
    conn = init_db()
    c = conn.cursor()
    now_iso = datetime.now().isoformat()
    
    translator = None
    if GoogleTranslator:
        translator = GoogleTranslator(source='es', target='en') # Translating to English! The user requested everything in English

    added = 0
    total = len(words_set)
    print(f"Processing {total} unique words...")
    
    for idx, w in enumerate(words_set):
        try:
            c.execute("SELECT id FROM words WHERE word = ?", (w,))
            if c.fetchone() is None:
                translation = ""
                if translator:
                    try:
                        translation = translator.translate(w)
                    except Exception as e:
                        pass
                
                c.execute('''INSERT INTO words (word, translation, next_review, interval, repetitions, ease_factor)
                             VALUES (?, ?, ?, ?, ?, ?)''',
                          (w, translation, now_iso, 0, 0, 2.5))
                added += 1
                
                if added % 10 == 0:
                    conn.commit()
                    print(f"Added {added} words...")
        except Exception as e:
            print(f"Error adding word {w}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Success. Added {added} new words to the database.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process.py <text_file_or_->")
        sys.exit(1)
        
    text = ""
    if sys.argv[1] == '-':
        text = sys.stdin.read()
    else:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text = f.read()
            
    words = process_text(text)
    add_words_to_db(words)
