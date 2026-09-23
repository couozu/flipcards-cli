import sqlite3

DB_FILE = "/Users/couozu/.gemini/antigravity/scratch/spanish_learning/vocab.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

c.execute("SELECT id, word FROM words WHERE is_ignored = 0")
words = c.fetchall()

updated = 0
for w_id, word in words:
    if " " in word: continue # Skip phrases
    
    # Simple heuristic
    # masculine exceptions
    masc_exc = ["problema", "dia", "día", "mapa", "planeta", "idioma", "sistema", "programa", "agua", "tema", "clima"]
    fem_exc = ["mano", "foto", "moto", "radio"]
    
    article = None
    if word in masc_exc:
        article = "el"
    elif word in fem_exc:
        article = "la"
    elif word.endswith("o"):
        article = "el"
    elif word.endswith("a"):
        article = "la"
    elif word.endswith("ción") or word.endswith("sión") or word.endswith("dad") or word.endswith("tad") or word.endswith("tud") or word.endswith("umbre"):
        article = "la"
    elif word.endswith("or") or word.endswith("aje") or word.endswith("án") or word.endswith("ambre"):
        article = "el"
    
    if article:
        new_word = f"{article} {word}"
        c.execute("UPDATE words SET word = ? WHERE id = ?", (new_word, w_id))
        updated += 1

conn.commit()
conn.close()
print(f"Heuristically added articles to {updated} nouns!")
