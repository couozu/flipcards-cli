import sqlite3
from datetime import datetime, timedelta
import sys
import tty
import termios
import os

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocab.db")

def get_char():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


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
    if "frequency" not in columns:
        c.execute("ALTER TABLE words ADD COLUMN frequency INTEGER DEFAULT 0")
    conn.commit()

def update_word(conn, word_id, known, is_active=False):
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
                 
    conn.commit()

def run_learning():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    check_and_migrate_db(conn)
    
    while True:
        os.system('clear')
        now_iso = datetime.now().isoformat()
        
        # Get count of words due today
        c.execute('''SELECT count(*) FROM (
            SELECT id FROM words WHERE next_review <= ?
            UNION ALL
            SELECT id FROM words WHERE is_active_unlocked = 1 AND active_next_review <= ?
        )''', (now_iso, now_iso))
        due_count = c.fetchone()[0]
        
        # Total words
        c.execute("SELECT COUNT(*) FROM words")
        total_count = c.fetchone()[0]
        
        if due_count == 0:
            print("Great! No more words to review for today.")
            print(f"Total words in database: {total_count}")
            print("Press any key to exit...")
            get_char()
            break
            
        c.execute('''
            SELECT * FROM (
                SELECT id, word, hint, translation, 0 as is_active, frequency FROM words WHERE next_review <= ?
                UNION ALL
                SELECT id, word, hint, translation, 1 as is_active, frequency FROM words WHERE is_active_unlocked = 1 AND active_next_review <= ?
            ) ORDER BY frequency DESC, RANDOM() LIMIT 1
        ''', (now_iso, now_iso))
        word_data = c.fetchone()
        
        if not word_data:
            break
            
        word_id, db_word, hint, db_translation, is_active, freq = word_data
        front = db_translation if is_active else db_word
        back = db_word if is_active else db_translation
        mode_str = "[ACTIVE (Translate to Spanish)] " if is_active else "[PASSIVE (Translate to Russian)] "

        
        print(f"Left for today: {due_count} | Total words: {total_count}")
        print("-" * 40)
        if hint:
            print(f"\n{mode_str}{front} (hint: {hint})\n")
        else:
            print(f"\n{mode_str}{front}\n")
        print("-" * 40)
        print("[Space] - Show translation | [Left/Right] - Don't know/Know | [E] - Edit | [Q] - Quit")
        
        LEFT_KEYS = set("qwertasdfgzxcvbйцукенфывапячсми")
        RIGHT_KEYS = set("yuiophjklnmнгшщзхъролджэтьбю")
        
        answered_early = False
        while True:
            ch = get_char().lower()
            if ch == ' ':
                break
            elif ch in LEFT_KEYS:
                update_word(conn, word_id, known=False, is_active=bool(is_active))
                answered_early = True
                break
            elif ch in RIGHT_KEYS:
                update_word(conn, word_id, known=True, is_active=bool(is_active))
                answered_early = True
                break
            elif ch == 'e':
                # Restore terminal to normal to accept input
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, termios.tcgetattr(sys.stdin.fileno()))
                print(f"\nCurrent Spanish: {db_word}")
                new_word = input(f"New Spanish (leave blank to keep '{db_word}'): ").strip()
                print(f"Current translation: {db_translation}")
                new_trans = input(f"New translation (leave blank to keep '{db_translation}'): ").strip()
                
                if new_word:
                    c.execute("UPDATE words SET word = ? WHERE id = ?", (new_word, word_id))
                    db_word = new_word
                if new_trans:
                    c.execute("UPDATE words SET translation = ? WHERE id = ?", (new_trans, word_id))
                    db_translation = new_trans
                conn.commit()
                front = db_translation if is_active else db_word
                back = db_word if is_active else db_translation
                print("\nSaved! Press Space to show translation or continue.")
                
            elif ch.isdigit():
                print(f"\n--- STATISTICS ---")
                print(f"Total words: {total_count}")
                print(f"Left to review today: {due_count}")
                print("Press Space to continue...")
            elif ch == 'q' or ch == '\x03': # q or Ctrl+C
                conn.close()
                return

        if answered_early:
            continue

        os.system('clear')
        print(f"Left for today: {due_count} | Total words: {total_count}")
        print("-" * 40)
        if hint:
            print(f"\n{mode_str}{front} (hint: {hint})  —  {back}\n")
        else:
            print(f"\n{mode_str}{front}  —  {back}\n")
        print("-" * 40)
        
        print("[Left Half of Keyboard] - Don't know | [Right Half] - Know | [E] - Edit | [Q] - Quit")
        
        while True:
            ch = get_char().lower()
            if ch in LEFT_KEYS:
                update_word(conn, word_id, known=False, is_active=bool(is_active))
                break
            elif ch in RIGHT_KEYS:
                update_word(conn, word_id, known=True, is_active=bool(is_active))
                break
            elif ch == 'e':
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, termios.tcgetattr(sys.stdin.fileno()))
                print(f"\nCurrent translation: {db_translation}")
                new_trans = input(f"New translation (leave blank to keep '{db_translation}'): ").strip()
                if new_trans:
                    c.execute("UPDATE words SET translation = ? WHERE id = ?", (new_trans, word_id))
                    db_translation = new_trans
                    conn.commit()
                    front = db_translation if is_active else db_word
                    back = db_word if is_active else db_translation
                    print(f"Saved: {db_translation}")
                print("[Left Half of Keyboard] - Don't know | [Right Half] - Know | [Q] - Quit")
            elif ch == 'q' or ch == '\x03':
                conn.close()
                return

if __name__ == "__main__":
    if not os.path.exists(DB_FILE):
        print("Database not found. Add words using process.py first.")
        sys.exit(1)
    try:
        run_learning()
    except KeyboardInterrupt:
        pass
