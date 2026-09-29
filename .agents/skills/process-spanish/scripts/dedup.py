import sqlite3
import re

def clean_words(text):
    text = text.replace('(', '').replace(')', '')
    text = re.sub(r'[^\w\s]', ' ', text)
    words = [w.lower() for w in text.split() if w.strip()]
    return set(words)

def should_merge(w1, w2):
    s1 = clean_words(w1)
    s2 = clean_words(w2)
    if not s1 or not s2: return False
    intersection = s1.intersection(s2)
    for word in intersection:
        if len(word) > 2:
            return True
    c1 = "".join(s1)
    c2 = "".join(s2)
    if c1 in c2 or c2 in c1:
        return True
    return False

def run_dedup():
    conn = sqlite3.connect('vocab.db')
    c = conn.cursor()
    c.execute("SELECT id, word FROM spanish_words")
    spanish_words = c.fetchall()
    
    total_merged = 0
    for sp_id, sp_word in spanish_words:
        c.execute('''SELECT r.id, r.word 
                     FROM word_links wl 
                     JOIN russian_words r ON wl.russian_id = r.id 
                     WHERE wl.spanish_id = ?''', (sp_id,))
        ru_words = c.fetchall()
        
        merged = set()
        for i in range(len(ru_words)):
            if i in merged: continue
            id1, w1 = ru_words[i]
            for j in range(i+1, len(ru_words)):
                if j in merged: continue
                id2, w2 = ru_words[j]
                
                if should_merge(w1, w2):
                    if len(w1) <= len(w2):
                        target_id, source_id = id1, id2
                        merged.add(j)
                    else:
                        target_id, source_id = id2, id1
                        merged.add(i)
                        
                    print(f"Merging '{w2 if source_id == id2 else w1}' into '{w1 if target_id == id1 else w2}' (for Spanish '{sp_word}')")
                    
                    c.execute("SELECT hint FROM word_links WHERE spanish_id = ? AND russian_id = ?", (sp_id, target_id))
                    h1 = c.fetchone()
                    c.execute("SELECT hint FROM word_links WHERE spanish_id = ? AND russian_id = ?", (sp_id, source_id))
                    h2 = c.fetchone()
                    
                    hint1 = h1[0] if h1 else ""
                    hint2 = h2[0] if h2 else ""
                    
                    hints = set()
                    if hint1: hints.update([h.strip() for h in hint1.split('|')])
                    if hint2: hints.update([h.strip() for h in hint2.split('|')])
                    combined_hint = " | ".join(sorted(h for h in hints if h))
                    
                    c.execute("DELETE FROM word_links WHERE spanish_id = ? AND russian_id = ?", (sp_id, source_id))
                    c.execute("DELETE FROM word_links WHERE spanish_id = ? AND russian_id = ?", (sp_id, target_id))
                    c.execute("INSERT INTO word_links (spanish_id, russian_id, hint) VALUES (?, ?, ?)", (sp_id, target_id, combined_hint))
                    
                    c.execute("SELECT count(*) FROM word_links WHERE russian_id = ?", (source_id,))
                    if c.fetchone()[0] == 0:
                        c.execute("DELETE FROM russian_words WHERE id = ?", (source_id,))
                        
                    total_merged += 1
                    
                    if target_id == id2:
                        break
                        
    conn.commit()
    conn.close()
    print(f"Total semantic duplicates merged: {total_merged}")

if __name__ == '__main__':
    run_dedup()
