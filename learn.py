
import sys
import tty
import termios

import subprocess
import threading
import queue

speech_queue = queue.Queue()
current_speech_proc = None

def speech_worker():
    global current_speech_proc
    while True:
        text = speech_queue.get()
        if text is None:
            break
        if current_speech_proc and current_speech_proc.poll() is None:
            try:
                current_speech_proc.terminate()
                current_speech_proc.wait(timeout=0.1)
            except:
                pass
            
        try:
            current_speech_proc = subprocess.Popen(["say", "-v", "Paulina", text], stderr=subprocess.DEVNULL)
        except:
            try:
                current_speech_proc = subprocess.Popen(["say", text], stderr=subprocess.DEVNULL)
            except:
                pass

speech_thread = threading.Thread(target=speech_worker, daemon=True)
speech_thread.start()

def speak(text):
    while not speech_queue.empty():
        try: speech_queue.get_nowait()
        except: pass
    speech_queue.put(text)

def get_char():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x1b':  # Arrow keys or escape sequences
            ch += sys.stdin.read(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch
import sqlite3
import random
import os
import sys
import time
import termios
import tty
from datetime import datetime, timedelta
import logging

DB_FILE = 'vocab.db'
REVIEW_INTERVAL_HOURS = 12

logging.basicConfig(filename='app.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


def format_time(seconds):
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds//60}m {seconds%60}s"
    else:
        return f"{seconds//3600}h {(seconds%3600)//60}m"

def init_db(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    time_spent_seconds INTEGER DEFAULT 0,
                    cards_reviewed INTEGER DEFAULT 0,
                    passive_mastered INTEGER DEFAULT 0,
                    active_mastered INTEGER DEFAULT 0
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY,
                    word_id INTEGER,
                    is_active INTEGER,
                    timestamp TEXT,
                    action TEXT
                 )''')
    conn.commit()

def record_time_spent(conn, delta_seconds):
    if delta_seconds <= 0 or delta_seconds > 300: 
        delta_seconds = min(delta_seconds, 60)
    
    c = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT OR IGNORE INTO daily_stats (date) VALUES (?)", (today_str,))
    c.execute("UPDATE daily_stats SET time_spent_seconds = time_spent_seconds + ?, cards_reviewed = cards_reviewed + 1 WHERE date = ?", (delta_seconds, today_str))
    conn.commit()

def get_stats_header(conn, due_passive, due_active):
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
    
    c.execute("SELECT COUNT(*) FROM spanish_words")
    total_active_vocab = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM spanish_words WHERE passive_ignored = 1 OR repetitions >= 3")
    passive_mastered = c.fetchone()[0]
    
    c.execute('''SELECT COUNT(*) FROM russian_words r 
                 WHERE active_ignored = 1 OR 
                 (active_repetitions >= 3 AND NOT EXISTS (
                     SELECT 1 FROM word_links wl JOIN spanish_words s ON wl.spanish_id = s.id 
                     WHERE wl.russian_id = r.id AND s.repetitions < 3 AND s.passive_ignored = 0
                 ))''')
    active_mastered = c.fetchone()[0]
    
    c.execute("UPDATE daily_stats SET passive_mastered = ?, active_mastered = ? WHERE date = ?", (passive_mastered, active_mastered, today_str))
    conn.commit()
    
    current_time = datetime.now().strftime("%H:%M")
    return f"{current_time} | Pend: {due_passive}p/{due_active}a | Dom: {passive_mastered}p/{active_mastered}a | Hoy: {today_cards}({format_time(today_time)}) | Tot: {total_cards}({format_time(total_time)}) | BD: {total_active_vocab}" 

def get_word_details(conn, word_id, is_active):
    c = conn.cursor()
    if is_active:
        c.execute("SELECT word, active_repetitions FROM russian_words WHERE id = ?", (word_id,))
        prompt, reps = c.fetchone()
        streak = f" [{reps}]" if reps > 0 else ""
        prompt = f"{prompt}{streak}"
        c.execute("""SELECT s.word, s.article, wl.hint 
                     FROM word_links wl 
                     JOIN spanish_words s ON wl.spanish_id = s.id 
                     WHERE wl.russian_id = ?""", (word_id,))
        answers = c.fetchall()
        
        front = prompt
        if len(answers) == 1:
            sp, art, hint = answers[0]
            word_str = f"{art} {sp}" if art else sp
            back = f"{word_str} (hint: {hint})" if hint else word_str
        else:
            parts = []
            for i, (sp, art, hint) in enumerate(answers, 1):
                word_str = f"{art} {sp}" if art else sp
                parts.append(f"{i}. {word_str} (hint: {hint})" if hint else f"{i}. {word_str}")
            back = "  ".join(parts)
        return front, back, "", answers[0][0] if answers else ""
    else:
        c.execute("SELECT word, article, frequency, repetitions FROM spanish_words WHERE id = ?", (word_id,))
        sp, art, freq, reps = c.fetchone()
        streak = f" [{reps}]" if reps > 0 else ""
        prompt = f"{sp}{streak}"
        
        c.execute("""SELECT r.word, wl.hint 
                     FROM word_links wl 
                     JOIN russian_words r ON wl.russian_id = r.id 
                     WHERE wl.spanish_id = ?""", (word_id,))
        answers = c.fetchall()
        
        front = prompt
        if len(answers) == 1:
            ru, hint = answers[0]
            back = f"{ru} (hint: {hint})" if hint else ru
        else:
            parts = []
            for i, (ru, hint) in enumerate(answers, 1):
                parts.append(f"{i}. {ru} (hint: {hint})" if hint else f"{i}. {ru}")
            back = "  ".join(parts)
            
        if art:
            back += f" ({art})"
            
        return front, back, "", sp

def undo_last_action(conn, undo_stack):
    c = conn.cursor()
    c.execute("SELECT id, state_json FROM history WHERE state_json IS NOT NULL ORDER BY timestamp DESC LIMIT 1")
    row = c.fetchone()
    if not row:
        return None, None
        
    hist_id, state_json = row
    import json
    last_state = json.loads(state_json)
    
    word_id = last_state.pop('id')
    is_active = last_state.pop('is_active_mode')
    
    table = "russian_words" if is_active else "spanish_words"
    cols = list(last_state.keys())
    placeholders = ", ".join([f"{col} = ?" for col in cols])
    values = list(last_state.values())
    values.append(word_id)
    
    c.execute(f"UPDATE {table} SET {placeholders} WHERE id = ?", values)
    c.execute("DELETE FROM history WHERE id = ?", (hist_id,))
    
    from datetime import datetime
    today_str = datetime.now().strftime("%Y-%m-%d")
    c.execute("UPDATE daily_stats SET cards_reviewed = max(0, cards_reviewed - 1) WHERE date = ?", (today_str,))
    conn.commit()
    return word_id, is_active
    return word_id, is_active

import json
def save_state_for_undo(conn, word_id, is_active, undo_stack):
    c = conn.cursor()
    table = "russian_words" if is_active else "spanish_words"
    c.execute(f"SELECT * FROM {table} WHERE id = ?", (word_id,))
    row = c.fetchone()
    col_names = [description[0] for description in c.description]
    state_dict = dict(zip(col_names, row))
    state_dict['is_active_mode'] = is_active
    
    # Save to persistent history table
    state_json = json.dumps(state_dict)
    c.execute("INSERT INTO history (word_id, is_active, timestamp, action, state_json) VALUES (?, ?, datetime('now'), 'update', ?)",
              (word_id, is_active, state_json))
    conn.commit()


def get_next_review_time(days_ahead):
    from datetime import timezone, timedelta
    now_utc = datetime.now(timezone.utc)
    if now_utc.hour < 3:
        current_logical_day = now_utc.date() - timedelta(days=1)
    else:
        current_logical_day = now_utc.date()
        
    target_date = current_logical_day + timedelta(days=days_ahead)
    target_dt = datetime(target_date.year, target_date.month, target_date.day, 3, 0, 0, tzinfo=timezone.utc)
    target_local = target_dt.astimezone()
    return target_local.replace(tzinfo=None)

def update_word(conn, word_id, known, is_active=False):
    c = conn.cursor()
    now = datetime.now().replace(microsecond=0)
    
    if is_active:
        c.execute("SELECT active_interval, active_repetitions, active_ease_factor FROM russian_words WHERE id = ?", (word_id,))
        interval, reps, ease = c.fetchone()
    else:
        c.execute("SELECT interval, repetitions, ease_factor FROM spanish_words WHERE id = ?", (word_id,))
        interval, reps, ease = c.fetchone()
        
    if known:
        if reps == 0:
            days_ahead = 1
        elif reps == 1:
            days_ahead = 1
        else:
            days_ahead = 2
            
        reps += 1
        next_review = get_next_review_time(days_ahead)
    else:
        reps = 0
        ease = max(1.3, ease - 0.2)
        next_review = now  # due immediately
        
    action = 'active_known' if (is_active and known) else 'active_unknown' if is_active else 'passive_known' if known else 'passive_unknown'
    
    if is_active:
        ignored = 1 if reps >= 3 else 0
        c.execute('''UPDATE russian_words 
                     SET active_next_review = ?, active_interval = ?, active_repetitions = ?, active_ease_factor = ?, active_last_review = ?, active_ignored = ?
                     WHERE id = ?''', (next_review.isoformat(), 0, reps, ease, now.isoformat(), ignored, word_id))
    else:
        ignored = 1 if reps >= 3 else 0
        c.execute('''UPDATE spanish_words 
                     SET next_review = ?, interval = ?, repetitions = ?, ease_factor = ?, last_review = ?, passive_ignored = ?
                     WHERE id = ?''', (next_review.isoformat(), 0, reps, ease, now.isoformat(), ignored, word_id))
        
        if ignored == 1:
            delay_iso = get_next_review_time(1).isoformat()
            c.execute("""
                UPDATE russian_words 
                SET active_next_review = ?
                WHERE id IN (SELECT russian_id FROM word_links WHERE spanish_id = ?)
                  AND (active_next_review IS NULL OR active_next_review < ?)
            """, (delay_iso, word_id, delay_iso))
                     
    c.execute("INSERT INTO history (word_id, is_active, timestamp, action) VALUES (?, ?, ?, ?)", (word_id, is_active, now.isoformat(), action))
    conn.commit()

def show_exit_screen(conn, ended_early=False):
    import stats
    os.system('clear')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM spanish_words")
    total_count = c.fetchone()[0]
    
    if ended_early:
        print("\nSesión terminada.")
    else:
        print("\n" + "=" * 40)
        print("¡Genial! No hay más palabras por repasar hoy.")
        print(f"Total de palabras en la base de datos: {total_count}")
        
    # We don't print exact next due time here since it's a bit complex with two tables, but let's just do a simple min
    c.execute("SELECT MIN(next_review) FROM spanish_words WHERE passive_ignored = 0")
    min_p = c.fetchone()[0]
    c.execute('''SELECT MIN(active_next_review) FROM russian_words r 
                 WHERE active_ignored = 0 AND NOT EXISTS (
                     SELECT 1 FROM word_links wl JOIN spanish_words s ON wl.spanish_id = s.id 
                     WHERE wl.russian_id = r.id AND s.repetitions < 3 AND s.passive_ignored = 0
                 )''')
    min_a = c.fetchone()[0]
    times = []
    if min_p: times.append(min_p)
    if min_a: times.append(min_a)
    if times:
        next_time_iso = min(times)
        next_dt = datetime.fromisoformat(next_time_iso)
        now_dt = datetime.now()
        if next_dt.date() == now_dt.date():
            time_str = f"today at {next_dt.strftime('%H:%M')}"
        elif (next_dt.date() - now_dt.date()).days == 1:
            time_str = f"tomorrow at {next_dt.strftime('%H:%M')}"
        else:
            time_str = next_dt.strftime('%Y-%m-%d %H:%M')
        print(f"\nLa próxima tarjeta pendiente es: {time_str}")
        
    stats.show_stats()

def run_learning():

    conn = sqlite3.connect('vocab_test.db' if 'test_all.py' in sys.argv[0] else 'vocab.db')
    undo_stack = []
    force_next_word = None
    
    while True:
        os.system('clear')
        now = datetime.now().replace(microsecond=0).isoformat().replace('T', ' ')
        now_t = now.replace(' ', 'T')
        
        c = conn.cursor()
        c.execute('''
            SELECT id, 1 as is_active, 0 as frequency 
            FROM russian_words 
            WHERE active_ignored = 0 
            AND (active_next_review IS NULL OR active_next_review <= ?)
            AND NOT EXISTS (
                SELECT 1 FROM word_links wl JOIN spanish_words s ON wl.spanish_id = s.id 
                WHERE wl.russian_id = russian_words.id AND s.repetitions < 3 AND s.passive_ignored = 0
            )
        ''', (now_t,))
        active_due = c.fetchall()
        
        c.execute('''
            SELECT id, 0 as is_active, frequency
            FROM spanish_words 
            WHERE passive_ignored = 0 AND next_review <= ?
        ''', (now_t,))
        passive_due = c.fetchall()
        
        due_active = len(active_due)
        due_passive = len(passive_due)
        all_due = active_due + passive_due
        
        if not all_due:
            get_stats_header(conn, due_passive, due_active)
            show_exit_screen(conn, ended_early=False)
            conn.close()
            return
            
        if force_next_word:
            match = next((r for r in all_due if int(r[0]) == int(force_next_word[0]) and bool(r[1]) == bool(force_next_word[1])), None)
            if match:
                selected_row = match
            else:
                weights = [row[2] + 1 for row in all_due]
                selected_row = random.choices(all_due, weights=weights, k=1)[0]
            force_next_word = None
        else:
            active_due = [row for row in all_due if row[1] == 1]
            if active_due:
                weights = [row[2] + 1 for row in active_due]
                selected_row = random.choices(active_due, weights=weights, k=1)[0]
            else:
                weights = [row[2] + 1 for row in all_due]
                selected_row = random.choices(all_due, weights=weights, k=1)[0]

        word_id, is_active, freq = selected_row
        
        front, back, extra_info, sp_word = get_word_details(conn, word_id, is_active)
        
        # We must call get_stats_header to update daily_stats BEFORE drawing
        header = get_stats_header(conn, due_passive, due_active)
        
        print(header)
        print("-" * 40)
        print(f"\n{front}\n")
        print("-" * 40)
        print("[Space] - Ver traducción | [K] - Lo sé | [D] - Borrar | [<-] Deshacer | [Q] - Salir")
        
        if not is_active and sp_word:
            speak(sp_word)
        
        card_start_time = time.time()
        
        answered_early = False
        while True:
            ch = get_char().lower()
            if ch == ' ':
                break
            elif ch in ('k', 'л'):
                save_state_for_undo(conn, word_id, is_active, undo_stack)
                update_word(conn, word_id, known=True, is_active=bool(is_active))
                record_time_spent(conn, int(time.time() - card_start_time))
                answered_early = True
                break
            elif ch in ('d', 'в'):
                save_state_for_undo(conn, word_id, is_active, undo_stack)
                table = "russian_words" if is_active else "spanish_words"
                col = "active_ignored" if is_active else "passive_ignored"
                c.execute(f"UPDATE {table} SET {col} = 1 WHERE id = ?", (word_id,))
                if not is_active:
                    delay_iso = get_next_review_time(1).isoformat()
                    c.execute("""
                        UPDATE russian_words 
                        SET active_next_review = ?
                        WHERE id IN (SELECT russian_id FROM word_links WHERE spanish_id = ?)
                          AND (active_next_review IS NULL OR active_next_review < ?)
                    """, (delay_iso, word_id, delay_iso))
                conn.commit()
                # Update daily_stats to reflect this deletion right away so exit screen is correct
                get_stats_header(conn, due_passive, due_active)
                answered_early = True
                break
            elif ch in ('\x7f', '\x08', 'u', 'г') or (ch.startswith('\x1b') and ch.endswith('d')):
                undone_id, undone_active = undo_last_action(conn, undo_stack)
                if undone_id:
                    force_next_word = (undone_id, undone_active)
                    print("\n¡Deshecho con éxito! Recargando...")
                    time.sleep(0.5)
                    answered_early = True
                    break
            elif ch in ('q', 'й', '\x03'):
                # Crucial bug fix: update stats one last time before exiting!
                get_stats_header(conn, due_passive, due_active)
                show_exit_screen(conn, ended_early=True)
                conn.close()
                return
                
        if answered_early:
            continue
            
        os.system('clear')
        print(get_stats_header(conn, due_passive, due_active))
        print("-" * 40)
        print(f"\n{front}  —  {back}\n")
        print("-" * 40)
        print("[Space] - No lo sé | [K] - Lo sé | [D] - Borrar | [E] - Editar | [<-] Deshacer | [Q] - Salir")
        
        if is_active and sp_word:
            speak(sp_word)
            
        while True:
            ch = get_char().lower()
            if ch == ' ':
                save_state_for_undo(conn, word_id, is_active, undo_stack)
                update_word(conn, word_id, known=False, is_active=bool(is_active))
                record_time_spent(conn, int(time.time() - card_start_time))
                break
            elif ch in ('k', 'л'):
                save_state_for_undo(conn, word_id, is_active, undo_stack)
                update_word(conn, word_id, known=True, is_active=bool(is_active))
                record_time_spent(conn, int(time.time() - card_start_time))
                break
            elif ch in ('d', 'в'):
                save_state_for_undo(conn, word_id, is_active, undo_stack)
                table = "russian_words" if is_active else "spanish_words"
                col = "active_ignored" if is_active else "passive_ignored"
                c.execute(f"UPDATE {table} SET {col} = 1 WHERE id = ?", (word_id,))
                if not is_active:
                    delay_iso = get_next_review_time(1).isoformat()
                    c.execute("""
                        UPDATE russian_words 
                        SET active_next_review = ?
                        WHERE id IN (SELECT russian_id FROM word_links WHERE spanish_id = ?)
                          AND (active_next_review IS NULL OR active_next_review < ?)
                    """, (delay_iso, word_id, delay_iso))
                conn.commit()
                # Update daily_stats to reflect this deletion right away
                get_stats_header(conn, due_passive, due_active)
                break
            elif ch in ('\x7f', '\x08', 'u', 'г') or (ch.startswith('\x1b') and ch.endswith('d')):
                undone_id, undone_active = undo_last_action(conn, undo_stack)
                if undone_id:
                    force_next_word = (undone_id, undone_active)
                    print("\n¡Deshecho con éxito! Recargando...")
                    time.sleep(0.5)
                    break
            elif ch in ('e', 'у'):
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, termios.tcgetattr(sys.stdin.fileno()))
                print(f"\nMapeo de traducción actual: {back}")
                print("Nota: En el nuevo sistema, para editar con seguridad, usa SQLite o pídeselo al asistente.")
                print("[Space] - No lo sé | [K] - Lo sé | [D] - Borrar | [<-] Deshacer")
            elif ch in ('q', 'й', '\x03'):
                get_stats_header(conn, due_passive, due_active)
                show_exit_screen(conn, ended_early=True)
                conn.close()
                return

if __name__ == "__main__":
    run_learning()

def get_next_due_time_str(conn):
    c = conn.cursor()
    c.execute("SELECT MIN(next_review) FROM spanish_words WHERE passive_ignored = 0")
    min_p = c.fetchone()[0]
    c.execute('''SELECT MIN(active_next_review) FROM russian_words r 
                 WHERE active_ignored = 0 AND NOT EXISTS (
                     SELECT 1 FROM word_links wl JOIN spanish_words s ON wl.spanish_id = s.id 
                     WHERE wl.russian_id = r.id AND s.repetitions < 3 AND s.passive_ignored = 0
                 )''')
    min_a = c.fetchone()[0]
    times = []
    if min_p: times.append(min_p)
    if min_a: times.append(min_a)
    if times:
        next_time_iso = min(times)
        next_dt = datetime.fromisoformat(next_time_iso)
        now_dt = datetime.now()
        
        diff = next_dt - now_dt
        hours, remainder = divmod(diff.total_seconds(), 3600)
        minutes, _ = divmod(remainder, 60)
        
        countdown = f"in {int(hours)}h {int(minutes)}m" if hours > 0 or minutes > 0 else "very soon"
        
        if next_dt.date() == now_dt.date():
            date_str = f"hoy a las {next_dt.strftime('%H:%M')}"
        elif (next_dt.date() - now_dt.date()).days == 1:
            date_str = f"mañana a las {next_dt.strftime('%H:%M')}"
        else:
            date_str = next_dt.strftime('%Y-%m-%d %H:%M')
            
        return f"{date_str} ({countdown})"
    return "No hay más tarjetas"
