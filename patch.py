import re

with open('learn.py', 'r') as f:
    content = f.read()

if 'import random' not in content:
    content = content.replace('import sys', 'import sys\nimport random')

old_query = """        c.execute('''
            SELECT * FROM (
                SELECT id, word, hint, translation, 0 as is_active, frequency FROM words WHERE next_review <= ? AND is_ignored = 0
                UNION ALL
                SELECT id, word, hint, translation, 1 as is_active, frequency FROM words WHERE is_active_unlocked = 1 AND active_next_review <= ? AND is_ignored = 0
            ) ORDER BY frequency DESC, RANDOM() LIMIT 1
        ''', (now_iso, now_iso))
        word_data = c.fetchone()
        
        if not word_data:
            break
            
        word_id, db_word, hint, db_translation, is_active, freq = word_data"""

new_query = """        c.execute('''
            SELECT id, word, hint, translation, 0 as is_active, frequency FROM words WHERE next_review <= ? AND is_ignored = 0
            UNION ALL
            SELECT id, word, hint, translation, 1 as is_active, frequency FROM words WHERE is_active_unlocked = 1 AND active_next_review <= ? AND is_ignored = 0
        ''', (now_iso, now_iso))
        
        all_due = c.fetchall()
        if not all_due:
            break
            
        # Frequency is index 5
        weights = [row[5] + 1 for row in all_due]
        selected_row = random.choices(all_due, weights=weights, k=1)[0]
        
        word_id, db_word, hint, db_translation, is_active, freq = selected_row"""

content = content.replace(old_query, new_query)

with open('learn.py', 'w') as f:
    f.write(content)
