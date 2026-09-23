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

def update_word(conn, word_id, known):
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
                 
    conn.commit()

def run_learning():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    while True:
        os.system('clear')
        now_iso = datetime.now().isoformat()
        
        # Get count of words due today
        c.execute("SELECT COUNT(*) FROM words WHERE next_review <= ?", (now_iso,))
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
            
        c.execute("SELECT id, word, translation FROM words WHERE next_review <= ? ORDER BY next_review ASC LIMIT 1", (now_iso,))
        word_data = c.fetchone()
        
        if not word_data:
            break
            
        word_id, word, translation = word_data
        
        print(f"Left for today: {due_count} | Total words: {total_count}")
        print("-" * 40)
        print(f"\nWord: {word.upper()}\n")
        print("-" * 40)
        print("[Space] - Show translation | [Any Digit] - Statistics | [Q] - Quit")
        
        while True:
            ch = get_char().lower()
            if ch == ' ':
                break
            elif ch.isdigit():
                print(f"\n--- STATISTICS ---")
                print(f"Total words: {total_count}")
                print(f"Left to review today: {due_count}")
                print("Press Space to continue...")
            elif ch == 'q' or ch == '\x03': # q or Ctrl+C
                conn.close()
                return

        print(f"\nTranslation: {translation}\n")
        print("[Left Half of Keyboard] - Don't know | [Right Half] - Know | [Q] - Quit")
        
        LEFT_KEYS = set("qwertasdfgzxcvbйцукенфывапячсми")
        RIGHT_KEYS = set("yuiophjklnmнгшщзхъролджэтьбю")

        while True:
            ch = get_char().lower()
            if ch in LEFT_KEYS:
                update_word(conn, word_id, known=False)
                break
            elif ch in RIGHT_KEYS:
                update_word(conn, word_id, known=True)
                break
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
