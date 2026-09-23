import sqlite3
import os
import sys
import tty
import termios
import select
from datetime import datetime, timedelta
import random
import time

DB_FILE = "/Users/couozu/.gemini/antigravity/scratch/spanish_learning/vocab.db"

def get_char():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            if select.select([sys.stdin], [], [], 0.05)[0]:
                ch += sys.stdin.read(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def format_time(seconds):
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds//60}m {seconds%60}s"
    else:
        return f"{seconds//3600}h {(seconds%3600)//60}m"

def check_and_migrate_db(conn):
    c = conn.cursor()
    # Ensure stats table exists
    c.execute('''CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    time_spent_seconds INTEGER DEFAULT 0,
                    cards_reviewed INTEGER DEFAULT 0
                 )''')
                 
    # Migrate is_ignored to passive/active_ignored
    try:
        c.execute("ALTER TABLE words ADD COLUMN passive_ignored INTEGER DEFAULT 0")
        c.execute("ALTER TABLE words ADD COLUMN active_ignored INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Columns probably already exist
        
    # Check if is_ignored still exists and migrate data if we haven't
    c.execute("PRAGMA table_info(words)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'is_ignored' in columns:
        # Check if we need to migrate
        c.execute("SELECT COUNT(*) FROM words WHERE is_ignored = 1")
        if c.fetchone()[0] > 0:
            c.execute("UPDATE words SET passive_ignored = 1, active_ignored = 1 WHERE is_ignored = 1")
            c.execute("UPDATE words SET is_ignored = 0 WHERE is_ignored = 1") # Clear it out so we don't re-migrate
            
    conn.commit()

def record_time_spent(conn, delta_seconds):
    if delta_seconds <= 0 or delta_seconds > 300: 
        # Ignore if negative or if they left it open for > 5 mins without answering
        delta_seconds = min(delta_seconds, 60) # cap at 60s for idle
    
    c = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT OR IGNORE INTO daily_stats (date) VALUES (?)", (today_str,))
    c.execute("UPDATE daily_stats SET time_spent_seconds = time_spent_seconds + ?, cards_reviewed = cards_reviewed + 1 WHERE date = ?", (delta_seconds, today_str))
    conn.commit()

def show_stats(conn):
    os.system('clear')
    c = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    c.execute("SELECT SUM(time_spent_seconds), SUM(cards_reviewed) FROM daily_stats")
    total_time, total_cards = c.fetchone()
    total_time = total_time or 0
    total_cards = total_cards or 0
    
    c.execute("SELECT time_spent_seconds, cards_reviewed FROM daily_stats WHERE date = ?", (today_str,))
    today_row = c.fetchone()
    today_time = today_row[0] if today_row else 0
    today_cards = today_row[1] if today_row else 0
    
    c.execute("SELECT COUNT(*) FROM words WHERE passive_ignored = 0")
    total_active_vocab = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM words WHERE passive_ignored = 1 OR repetitions >= 3")
    passive_mastered = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM words WHERE is_active_unlocked = 1 AND (active_ignored = 1 OR active_repetitions >= 3)")
    active_mastered = c.fetchone()[0]
    
    print("\n--- 📊 STATISTICS ---\n")
    print(f"Total Words in DB: {total_active_vocab}")
    print(f"Mastered (Passive): {passive_mastered} words")
    print(f"Mastered (Active):  {active_mastered} words")
    print("-" * 30)
    print(f"Cards Reviewed Today: {today_cards}")
    print(f"Time Spent Today:     {format_time(today_time)}")
    print("-" * 30)
    print(f"Total Cards Reviewed: {total_cards}")
    print(f"Total Time Spent:     {format_time(total_time)}")
    print("\nPress [Space] to continue...")
    while True:
        if get_char() == ' ':
            break

def undo_last_action(conn, undo_stack):
    if not undo_stack:
        return None, None
        
    last_state = undo_stack.pop()
    word_id = last_state.pop('id')
    is_active = last_state.pop('__is_active', False)
    
    c = conn.cursor()
    # Restore the row
    cols = list(last_state.keys())
    placeholders = ", ".join([f"{col} = ?" for col in cols])
    values = list(last_state.values())
    values.append(word_id)
    
    c.execute(f"UPDATE words SET {placeholders} WHERE id = ?", values)
    
    # Remove the latest history entry for this word
    c.execute("DELETE FROM history WHERE id = (SELECT MAX(id) FROM history WHERE word_id = ?)", (word_id,))
    
    # We could also subtract time from daily_stats, but it's minor. We'll decrement card count.
    today_str = datetime.now().strftime("%Y-%m-%d")
    c.execute("UPDATE daily_stats SET cards_reviewed = max(0, cards_reviewed - 1) WHERE date = ?", (today_str,))
    
    conn.commit()
    return word_id, is_active

def save_state_for_undo(conn, word_id, is_active, undo_stack):
    c = conn.cursor()
    c.execute("SELECT * FROM words WHERE id = ?", (word_id,))
    row = c.fetchone()
    col_names = [description[0] for description in c.description]
    row_dict = dict(zip(col_names, row))
    row_dict['__is_active'] = is_active
    undo_stack.append(row_dict)

def update_word(conn, word_id, known, is_active=False):
    c = conn.cursor()
    now = datetime.now()
    
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
            if reps >= 3:
                unlocked = 1
        else:
            reps = 0
            interval = 0 # 0 means it stays due today!
            ease = max(1.3, ease - 0.2)
            
        next_review = now + timedelta(days=interval)
        
        c.execute('''UPDATE words 
                     SET next_review = ?, interval = ?, repetitions = ?, ease_factor = ?, is_active_unlocked = ? 
                     WHERE id = ?''', (next_review.isoformat(), interval, reps, ease, unlocked, word_id))
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
            interval = 0 # 0 means it stays due today!
            ease = max(1.3, ease - 0.2)
            
        next_review = now + timedelta(days=interval)
        
        c.execute('''UPDATE words 
                     SET active_next_review = ?, active_interval = ?, active_repetitions = ?, active_ease_factor = ? 
                     WHERE id = ?''', (next_review.isoformat(), interval, reps, ease, word_id))
                 
    c.execute('''INSERT INTO history (word_id, reviewed_at, result) 
                 VALUES (?, ?, ?)''', (word_id, now.isoformat(), ('active_' if is_active else 'passive_') + ('known' if known else 'unknown')))
                 
    conn.commit()

def run_learning():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    check_and_migrate_db(conn)
    
    undo_stack = []
    force_next_word = None
    
    while True:
        os.system('clear')
        now_iso = datetime.now().isoformat()
        
        # Get count of words due today
        c.execute('''SELECT count(*) FROM (
            SELECT id FROM words WHERE next_review <= ? AND passive_ignored = 0
            UNION ALL
            SELECT id FROM words WHERE is_active_unlocked = 1 AND active_next_review <= ? AND active_ignored = 0
        )''', (now_iso, now_iso))
        due_count = c.fetchone()[0]
        
        # Total words
        c.execute("SELECT COUNT(*) FROM words WHERE passive_ignored = 0")
        total_count = c.fetchone()[0]
        
        if due_count == 0:
            print("Great! No more words to review for today.")
            print(f"Total words in database: {total_count}")
            print("Press any key to exit...")
            get_char()
            break
            
        c.execute('''
            SELECT id, word, hint, translation, 0 as is_active, frequency, article FROM words WHERE next_review <= ? AND passive_ignored = 0
            UNION ALL
            SELECT id, word, hint, translation, 1 as is_active, frequency, article FROM words WHERE is_active_unlocked = 1 AND active_next_review <= ? AND active_ignored = 0
        ''', (now_iso, now_iso))
        
        all_due = c.fetchall()
        if not all_due:
            break
            
        if force_next_word:
            # find it in all_due
            match = next((r for r in all_due if r[0] == force_next_word[0] and bool(r[4]) == force_next_word[1]), None)
            if match:
                selected_row = match
            else:
                # Fallback if not found (shouldn't happen)
                weights = [row[5] + 1 for row in all_due]
                selected_row = random.choices(all_due, weights=weights, k=1)[0]
            force_next_word = None
        else:
            weights = [row[5] + 1 for row in all_due]
            selected_row = random.choices(all_due, weights=weights, k=1)[0]

            

        
        word_id, db_word, hint, db_translation, is_active, freq, article = selected_row
        
        russian_side = f"{db_translation} (hint: {hint})" if hint else db_translation
        spanish_with_article = f"{article} {db_word}" if article else db_word
        
        front = russian_side if is_active else db_word
        back = spanish_with_article if is_active else russian_side
        
        # FRONT SCREEN
        print(f"Left for today: {due_count} | Total words: {total_count}")
        print("-" * 40)
        print(f"\n{front}\n")
        print("-" * 40)
        print("[Space] - Show translation | [D] - Delete | [0-9] - Stats | [<-] Undo | [Q] - Quit")
        
        card_start_time = time.time()
        
        answered_early = False
        while True:
            ch = get_char().lower()
            if ch == ' ':
                break
            elif ch == 'd':
                save_state_for_undo(conn, word_id, is_active, undo_stack)
                col = "active_ignored" if is_active else "passive_ignored"
                c.execute(f"UPDATE words SET {col} = 1 WHERE id = ?", (word_id,))
                conn.commit()
                answered_early = True
                break
            elif ch.isdigit():
                show_stats(conn)
                answered_early = True
                break
            elif ch == '\x1b[d': # Left Arrow
                undone_id, undone_active = undo_last_action(conn, undo_stack)
                if undone_id:
                    force_next_word = (undone_id, undone_active)
                    print("\nUndo successful! Reloading...")
                    time.sleep(0.5)
                answered_early = True
                break
            elif ch == 'q' or ch == '\x03':
                conn.close()
                return

        if answered_early:
            continue

        # BACK SCREEN
        os.system('clear')
        print(f"Left for today: {due_count} | Total words: {total_count}")
        print("-" * 40)
        if is_active:
            print(f"\n{front}  —  {back}\n")
        else:
            article_tag = f" ({article})" if article else ""
            print(f"\n{front}  —  {back}{article_tag}\n")
        print("-" * 40)
        
        print("[Space] - Don't know | [K] - Know | [D] - Delete | [E] - Edit | [0-9] - Stats | [<-] Undo | [Q] Quit")
        
        while True:
            ch = get_char().lower()
            if ch == ' ': # Space = Don't Know
                save_state_for_undo(conn, word_id, is_active, undo_stack)
                update_word(conn, word_id, known=False, is_active=bool(is_active))
                record_time_spent(conn, int(time.time() - card_start_time))
                break
            elif ch == 'k': # K = Know
                save_state_for_undo(conn, word_id, is_active, undo_stack)
                update_word(conn, word_id, known=True, is_active=bool(is_active))
                record_time_spent(conn, int(time.time() - card_start_time))
                break
            elif ch == 'd':
                save_state_for_undo(conn, word_id, is_active, undo_stack)
                col = "active_ignored" if is_active else "passive_ignored"
                c.execute(f"UPDATE words SET {col} = 1 WHERE id = ?", (word_id,))
                conn.commit()
                break
            elif ch == '\x1b[d': # Left Arrow
                undone_id, undone_active = undo_last_action(conn, undo_stack)
                if undone_id:
                    force_next_word = (undone_id, undone_active)
                    print("\nUndo successful! Reloading...")
                    time.sleep(0.5)
                break
            elif ch.isdigit():
                show_stats(conn)
                break
            elif ch == 'e':
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, termios.tcgetattr(sys.stdin.fileno()))
                print(f"\nCurrent translation: {db_translation}")
                new_trans = input(f"New translation (leave blank to keep '{db_translation}'): ").strip()
                if new_trans:
                    save_state_for_undo(conn, word_id, is_active, undo_stack)
                    c.execute("UPDATE words SET translation = ? WHERE id = ?", (new_trans, word_id))
                    db_translation = new_trans
                    conn.commit()
                    russian_side = f"{db_translation} (hint: {hint})" if hint else db_translation
                    spanish_side = db_word
                    front = russian_side if is_active else spanish_side
                    back = spanish_side if is_active else russian_side
                    print(f"Saved: {db_translation}")
                print("[Space] - Don't know | [K] - Know | [D] - Delete | [<-] Undo")
                # Return terminal to raw mode (handled by next get_char)
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
