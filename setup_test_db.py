import sqlite3
import os
from datetime import datetime

TEST_DB = "vocab_test.db"

if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

conn = sqlite3.connect(TEST_DB)
c = conn.cursor()

# 1. Create schema
c.executescript('''
CREATE TABLE daily_stats (
    date TEXT PRIMARY KEY,
    time_spent_seconds INTEGER DEFAULT 0,
    cards_reviewed INTEGER DEFAULT 0,
    passive_mastered INTEGER DEFAULT 0,
    active_mastered INTEGER DEFAULT 0
);
CREATE TABLE history (
    id INTEGER PRIMARY KEY,
    word_id INTEGER,
    is_active INTEGER,
    timestamp TEXT,
    action TEXT
);
CREATE TABLE spanish_words (
    id INTEGER PRIMARY KEY,
    word TEXT UNIQUE,
    article TEXT DEFAULT '',
    frequency INTEGER DEFAULT 0,
    next_review TEXT,
    interval REAL,
    repetitions INTEGER,
    ease_factor REAL,
    last_review TEXT,
    passive_ignored INTEGER DEFAULT 0
);
CREATE TABLE russian_words (
    id INTEGER PRIMARY KEY,
    word TEXT UNIQUE,
    active_next_review TEXT,
    active_interval REAL DEFAULT 0,
    active_repetitions INTEGER DEFAULT 0,
    active_ease_factor REAL DEFAULT 2.5,
    active_last_review TEXT,
    is_active_unlocked INTEGER DEFAULT 0,
    active_ignored INTEGER DEFAULT 0
);
CREATE TABLE word_links (
    spanish_id INTEGER,
    russian_id INTEGER,
    hint TEXT DEFAULT '',
    PRIMARY KEY (spanish_id, russian_id, hint),
    FOREIGN KEY(spanish_id) REFERENCES spanish_words(id),
    FOREIGN KEY(russian_id) REFERENCES russian_words(id)
);
''')

# 2. Insert dummy data
now_iso = datetime.now().isoformat()

# Insert Spanish words
spanish = [
    ("gato", "el", 100),
    ("perro", "el", 200),
    ("venir", "", 300),
    ("llegar", "", 150)
]

for w, art, freq in spanish:
    c.execute("INSERT INTO spanish_words (word, article, frequency, next_review, interval, repetitions, ease_factor) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (w, art, freq, now_iso, 0, 0, 2.5))

# Insert Russian words
russian = [
    "кот",
    "собака",
    "приходить",
    "приезжать"
]

for w in russian:
    c.execute("INSERT INTO russian_words (word, active_next_review, active_interval, active_repetitions, active_ease_factor) VALUES (?, ?, ?, ?, ?)",
              (w, now_iso, 0, 0, 2.5))

# Insert Links
links = [
    (1, 1, "мяукает"),  # gato -> кот
    (2, 2, "лает"),     # perro -> собака
    (3, 3, "¡Venga!"),  # venir -> приходить
    (4, 3, "на поезде") # llegar -> приходить
]

for sp, ru, hint in links:
    c.execute("INSERT INTO word_links (spanish_id, russian_id, hint) VALUES (?, ?, ?)", (sp, ru, hint))

conn.commit()
conn.close()

print(f"Created independent test database: {TEST_DB} with dummy data.")
