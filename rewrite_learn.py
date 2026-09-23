import re

with open('learn.py', 'r') as f:
    content = f.read()

# Add migration
migration_code = """
def check_and_migrate_db(conn):
    c = conn.cursor()
    c.execute("PRAGMA table_info(words)")
    columns = [col[1] for col in c.fetchall()]
    if "is_active_unlocked" not in columns:
        c.execute("ALTER TABLE words ADD COLUMN is_active_unlocked INTEGER DEFAULT 0")
        c.execute("ALTER TABLE words ADD COLUMN active_next_review TEXT")
        c.execute("ALTER TABLE words ADD COLUMN active_interval REAL DEFAULT 0")
        c.execute("ALTER TABLE words ADD COLUMN active_repetitions INTEGER DEFAULT 0")
        c.execute("ALTER TABLE words ADD COLUMN active_ease_factor REAL DEFAULT 2.5")
        conn.commit()
"""
content = content.replace("def update_word(", migration_code + "\ndef update_word(")

# Replace update_word
old_update = """def update_word(conn, word_id, known):
    c = conn.cursor()
    c.execute("SELECT interval, repetitions, ease_factor FROM words WHERE id = ?", (word_id,))
    interval, reps, ease = c.fetchone()
    
    if known:
        if reps == 0:
            interval = 1
        elif reps == 1:
            interval = 6
        else:
            interval = interval * ease
        reps += 1
    else:
        reps = 0
        interval = 1
        ease = max(1.3, ease - 0.2)
        
    next_review_iso = (datetime.now() + timedelta(days=interval)).isoformat()
    now_iso = datetime.now().isoformat()
    
    c.execute('''UPDATE words 
                 SET next_review = ?, interval = ?, repetitions = ?, ease_factor = ? 
                 WHERE id = ?''', (next_review_iso, interval, reps, ease, word_id))
                 
    c.execute('''INSERT INTO history (word_id, reviewed_at, result) 
                 VALUES (?, ?, ?)''', (word_id, now_iso, 'known' if known else 'unknown'))
                 
    conn.commit()"""

new_update = """def update_word(conn, word_id, known, is_active=False):
    c = conn.cursor()
    now_iso = datetime.now().isoformat()
    
    if not is_active:
        c.execute("SELECT interval, repetitions, ease_factor, is_active_unlocked FROM words WHERE id = ?", (word_id,))
        interval, reps, ease, unlocked = c.fetchone()
        
        if known:
            if reps == 0:
                interval = 1
            elif reps == 1:
                interval = 6
            else:
                interval = interval * ease
            reps += 1
        else:
            reps = 0
            interval = 1
            ease = max(1.3, ease - 0.2)
            
        next_review_iso = (datetime.now() + timedelta(days=interval)).isoformat()
        
        c.execute('''UPDATE words 
                     SET next_review = ?, interval = ?, repetitions = ?, ease_factor = ? 
                     WHERE id = ?''', (next_review_iso, interval, reps, ease, word_id))
                     
        if reps >= 3 and not unlocked:
            c.execute("UPDATE words SET is_active_unlocked = 1, active_next_review = ? WHERE id = ?", (now_iso, word_id))
    else:
        c.execute("SELECT active_interval, active_repetitions, active_ease_factor FROM words WHERE id = ?", (word_id,))
        interval, reps, ease = c.fetchone()
        
        if known:
            if reps == 0:
                interval = 1
            elif reps == 1:
                interval = 6
            else:
                interval = interval * ease
            reps += 1
        else:
            reps = 0
            interval = 1
            ease = max(1.3, ease - 0.2)
            
        next_review_iso = (datetime.now() + timedelta(days=interval)).isoformat()
        
        c.execute('''UPDATE words 
                     SET active_next_review = ?, active_interval = ?, active_repetitions = ?, active_ease_factor = ? 
                     WHERE id = ?''', (next_review_iso, interval, reps, ease, word_id))
                 
    c.execute('''INSERT INTO history (word_id, reviewed_at, result) 
                 VALUES (?, ?, ?)''', (word_id, now_iso, ('active_' if is_active else 'passive_') + ('known' if known else 'unknown')))
                 
    conn.commit()"""
content = content.replace(old_update, new_update)

# Add check_and_migrate_db call
content = content.replace("c = conn.cursor()\n    \n    while True:", "c = conn.cursor()\n    check_and_migrate_db(conn)\n    \n    while True:")

# Replace due_count query
old_due_count = """        # Get count of words due today
        c.execute("SELECT COUNT(*) FROM words WHERE next_review <= ?", (now_iso,))
        due_count = c.fetchone()[0]"""
new_due_count = """        # Get count of words due today
        c.execute('''SELECT count(*) FROM (
            SELECT id FROM words WHERE next_review <= ?
            UNION ALL
            SELECT id FROM words WHERE is_active_unlocked = 1 AND active_next_review <= ?
        )''', (now_iso, now_iso))
        due_count = c.fetchone()[0]"""
content = content.replace(old_due_count, new_due_count)

# Replace word fetch
old_fetch = """        c.execute("SELECT id, word, hint, translation FROM words WHERE next_review <= ? ORDER BY RANDOM() LIMIT 1", (now_iso,))
        word_data = c.fetchone()
        
        if not word_data:
            break
            
        word_id, word, hint, translation = word_data"""
new_fetch = """        c.execute('''
            SELECT id, word, hint, translation, 0 as is_active FROM words WHERE next_review <= ?
            UNION ALL
            SELECT id, word, hint, translation, 1 as is_active FROM words WHERE is_active_unlocked = 1 AND active_next_review <= ?
            ORDER BY RANDOM() LIMIT 1
        ''', (now_iso, now_iso))
        word_data = c.fetchone()
        
        if not word_data:
            break
            
        word_id, db_word, hint, db_translation, is_active = word_data
        front = db_translation if is_active else db_word
        back = db_word if is_active else db_translation
        mode_str = "[ACTIVE (Translate to Spanish)] " if is_active else "[PASSIVE (Translate to Russian)] "
"""
content = content.replace(old_fetch, new_fetch)

# Fix variables in display and edit
content = content.replace("word} (hint", "front} (hint")
content = content.replace("word}\\n", "front}\\n")
content = content.replace("word}  —  {translation", "front}  —  {back")

content = content.replace("Current word: {word}", "Current Spanish: {db_word}")
content = content.replace("New word (leave blank to keep '{word}')", "New Spanish (leave blank to keep '{db_word}')")

content = content.replace("Current translation: {translation}", "Current translation: {db_translation}")
content = content.replace("New translation (leave blank to keep '{translation}')", "New translation (leave blank to keep '{db_translation}')")

content = content.replace("word = new_word", "db_word = new_word")
content = content.replace("translation = new_trans", "db_translation = new_trans")

# Note we must also update front and back if edited!
content = content.replace("conn.commit()\n                print(\"\\nSaved! Press Space to show translation or continue.\")", "conn.commit()\n                front = db_translation if is_active else db_word\n                back = db_word if is_active else db_translation\n                print(\"\\nSaved! Press Space to show translation or continue.\")")

content = content.replace("conn.commit()\n                    print(f\"Saved: {translation}\")", "conn.commit()\n                    front = db_translation if is_active else db_word\n                    back = db_word if is_active else db_translation\n                    print(f\"Saved: {db_translation}\")")

# Update update_word calls
content = content.replace("update_word(conn, word_id, known=False)", "update_word(conn, word_id, known=False, is_active=bool(is_active))")
content = content.replace("update_word(conn, word_id, known=True)", "update_word(conn, word_id, known=True, is_active=bool(is_active))")

content = content.replace("{front}", "{mode_str}{front}")

with open('learn.py', 'w') as f:
    f.write(content)
