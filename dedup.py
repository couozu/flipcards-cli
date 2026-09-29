import sqlite3

def merge_same_links():
    conn = sqlite3.connect('vocab.db')
    c = conn.cursor()
    c.execute("SELECT spanish_id, russian_id, COUNT(*) as c FROM word_links GROUP BY spanish_id, russian_id HAVING c > 1")
    dupes = c.fetchall()
    
    merged_count = 0
    for sp_id, ru_id, _ in dupes:
        c.execute("SELECT hint FROM word_links WHERE spanish_id = ? AND russian_id = ?", (sp_id, ru_id))
        hints = [h[0] for h in c.fetchall() if h[0]]
        
        # Combine unique hints
        combined_hint = " | ".join(sorted(set(hints)))
        
        c.execute("DELETE FROM word_links WHERE spanish_id = ? AND russian_id = ?", (sp_id, ru_id))
        c.execute("INSERT INTO word_links (spanish_id, russian_id, hint) VALUES (?, ?, ?)", (sp_id, ru_id, combined_hint))
        merged_count += 1
        
    conn.commit()
    conn.close()
    print(f"Merged {merged_count} same-word links.")

if __name__ == '__main__':
    merge_same_links()
