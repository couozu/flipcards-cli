import os
import sqlite3
import random
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import learn

app = Flask(__name__)
DB_FILE = 'vocab.db'

# Use learn.py's highly optimized queue
learn.speech_thread  # ensure it's alive

undo_stack = []
forced_next_card = None

def get_next_card():
    global forced_next_card
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if forced_next_card:
        word_id, is_active = forced_next_card
        forced_next_card = None
        
        if not is_active:
            c.execute('''SELECT s.id, r.id, s.word, r.word, wl.hint 
                         FROM spanish_words s JOIN word_links wl ON s.id = wl.spanish_id 
                         JOIN russian_words r ON wl.russian_id = r.id WHERE s.id = ? LIMIT 1''', (word_id,))
        else:
            c.execute('''SELECT s.id, r.id, s.word, r.word, wl.hint 
                         FROM russian_words r JOIN word_links wl ON r.id = wl.russian_id 
                         JOIN spanish_words s ON wl.spanish_id = s.id WHERE r.id = ? LIMIT 1''', (word_id,))
        row = c.fetchone()
        if row:
            sp_id, ru_id, sp_text, ru_text, hints = row
            front, back, _, sp_word = learn.get_word_details(conn, word_id, is_active)
            
            image_url = None
            if not is_active:
                c.execute("SELECT image_url FROM spanish_words WHERE id = ?", (word_id,))
                img_row = c.fetchone()
                if img_row and img_row[0]: image_url = img_row[0]
                
            stats_str = learn.get_stats_header(conn, 0, 0)
            stats_str = stats_str.split("\n")[0].strip() if "\n" in stats_str else stats_str
            
            return {
                "card": {
                    "id": word_id, "is_active": is_active, "front": front, "back": back,
                    "sp_word": sp_word, "image_url": image_url,
                    "sp_id": sp_id, "ru_id": ru_id, "sp_text": sp_text, "ru_text": ru_text, "hints": hints
                },
                "stats": stats_str,
                "done": False
            }
    
    now = datetime.now().replace(microsecond=0).isoformat().replace('T', ' ')
    now_t = now.replace(' ', 'T')
    
    # Get Active Due
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
    
    # Get Passive Due
    c.execute('''
        SELECT id, 0 as is_active, frequency
        FROM spanish_words 
        WHERE passive_ignored = 0 AND next_review <= ?
    ''', (now_t,))
    passive_due = c.fetchall()
    
    all_due = active_due + passive_due
    due_active = len(active_due)
    due_passive = len(passive_due)
    
    if not all_due:
        stats = learn.get_stats_header(conn, 0, 0)
        conn.close()
        return {"done": True, "stats": stats}
        
    # Prioritize active
    active_due_only = [row for row in all_due if row[1] == 1]
    if active_due_only:
        weights = [row[2] + 1 for row in active_due_only]
        selected_row = random.choices(active_due_only, weights=weights, k=1)[0]
    else:
        weights = [row[2] + 1 for row in all_due]
        selected_row = random.choices(all_due, weights=weights, k=1)[0]
        
    word_id, is_active, freq = selected_row
    
    # Get details
    # Get word details and raw words
    c = conn.cursor()
    if not is_active:
        c.execute('''SELECT s.id, r.id, s.word, r.word, wl.hint 
                     FROM spanish_words s JOIN word_links wl ON s.id = wl.spanish_id 
                     JOIN russian_words r ON wl.russian_id = r.id WHERE s.id = ? LIMIT 1''', (word_id,))
    else:
        c.execute('''SELECT s.id, r.id, s.word, r.word, wl.hint 
                     FROM russian_words r JOIN word_links wl ON r.id = wl.russian_id 
                     JOIN spanish_words s ON wl.spanish_id = s.id WHERE r.id = ? LIMIT 1''', (word_id,))
    row = c.fetchone()
    if row:
        sp_id, ru_id, sp_text, ru_text, hints = row
    else:
        sp_id, ru_id, sp_text, ru_text, hints = 0, 0, "", "", ""
        
    front, back, _, sp_word = learn.get_word_details(conn, word_id, is_active)
    
    # Get image url (only for passive cards, as requested by user)
    image_url = None
    if not is_active:
        c.execute("SELECT image_url FROM spanish_words WHERE id = ?", (word_id,))
        row = c.fetchone()
        if row and row[0]:
            image_url = row[0]
            
    stats = learn.get_stats_header(conn, due_passive, due_active)
    conn.close()
    
    return {
        "done": False,
        "stats": stats,
        "card": {
            "id": word_id,
            "is_active": is_active,
            "front": front,
            "back": back,
            "sp_word": sp_word,
            "image_url": image_url,
            "sp_id": sp_id,
            "ru_id": ru_id,
            "sp_text": sp_text,
            "ru_text": ru_text,
            "hints": hints
        }
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/next", methods=["GET"])
def api_next():
    return jsonify(get_next_card())

@app.route("/api/action", methods=["POST"])
def api_action():
    data = request.json
    action = data.get("action")
    word_id = data.get("id")
    is_active = data.get("is_active")
    time_spent = data.get("time_spent", 0)
    
    conn = sqlite3.connect(DB_FILE)
    
    global forced_next_card
    if action == 'undo':
        undid = learn.undo_last_action(conn, undo_stack)
        if undid[0]:
            forced_next_card = undid
    elif action in ('k', 'space', 'd'):
        learn.save_state_for_undo(conn, word_id, is_active, undo_stack)
        
        if action == 'k':
            learn.update_word(conn, word_id, known=True, is_active=is_active)
            learn.record_time_spent(conn, time_spent)
        elif action == 'space':
            learn.update_word(conn, word_id, known=False, is_active=is_active)
            learn.record_time_spent(conn, time_spent)
        elif action == 'd':
            table = "russian_words" if is_active else "spanish_words"
            col = "active_ignored" if is_active else "passive_ignored"
            conn.execute(f"UPDATE {table} SET {col} = 1 WHERE id = ?", (word_id,))
            if not is_active:
                delay_iso = learn.get_next_review_time(1).isoformat()
                conn.execute("""
                    UPDATE russian_words 
                    SET active_next_review = ?
                    WHERE id IN (SELECT russian_id FROM word_links WHERE spanish_id = ?)
                      AND (active_next_review IS NULL OR active_next_review < ?)
                """, (delay_iso, word_id, delay_iso))
            conn.commit()
            
    conn.close()
    return jsonify(get_next_card())

@app.route("/api/speak", methods=["POST"])
def api_speak():
    text = request.json.get("text")
    if text:
        learn.speak(text)
    return jsonify({"status": "ok"})

import shutil
from flask import send_from_directory

@app.route("/api/image", methods=["POST"])
def api_image():
    data = request.json
    word_id = data.get("id")
    url = data.get("url")
    
    # Handle local files
    if url.startswith("/") or url.startswith("file://") or url.startswith("~"):
        local_path = url.replace("file://", "").strip()
        local_path = os.path.expanduser(local_path)
        
        if os.path.exists(local_path):
            os.makedirs("static/images", exist_ok=True)
            ext = os.path.splitext(local_path)[1]
            if not ext: ext = ".jpg"
            new_filename = f"word_{word_id}{ext}"
            new_path = os.path.join("static/images", new_filename)
            shutil.copy2(local_path, new_path)
            import time
            url = f"/static/images/{new_filename}?t={int(time.time())}"
            
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE spanish_words SET image_url = ? WHERE id = ?", (url, word_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "url": url})

@app.route("/api/upload", methods=["POST"])
def api_upload():
    file = request.files.get("file")
    word_id = request.form.get("id")
    
    if file and word_id:
        os.makedirs("static/images", exist_ok=True)
        ext = os.path.splitext(file.filename)[1]
        if not ext: ext = ".jpg"
        new_filename = f"word_{word_id}{ext}"
        new_path = os.path.join("static/images", new_filename)
        
        file.save(new_path)
        import time
        url = f"/static/images/{new_filename}?t={int(time.time())}"
        
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE spanish_words SET image_url = ? WHERE id = ?", (url, word_id))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "ok", "url": url})
    return jsonify({"status": "error"}), 400

@app.route("/api/edit", methods=["POST"])
def api_edit():
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    sp_id = data.get("sp_id")
    ru_id = data.get("ru_id")
    new_sp = data.get("sp_text")
    new_ru = data.get("ru_text")
    new_hints = data.get("hints")
    
    if sp_id and new_sp:
        c.execute("UPDATE spanish_words SET word = ? WHERE id = ?", (new_sp, sp_id))
    if ru_id and new_ru:
        c.execute("UPDATE russian_words SET word = ? WHERE id = ?", (new_ru, ru_id))
    if sp_id and ru_id:
        c.execute("UPDATE word_links SET hint = ? WHERE spanish_id = ? AND russian_id = ?", (new_hints, sp_id, ru_id))
        
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True, port=5001)
