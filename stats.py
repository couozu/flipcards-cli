import sqlite3
import datetime

def draw_bar(val, max_val, max_width=40):
    if max_val == 0: return ""
    bar_len = int((val / max_val) * max_width)
    return "█" * bar_len

def show_stats():
    conn = sqlite3.connect('vocab.db')
    c = conn.cursor()
    c.execute("SELECT date, cards_reviewed, passive_mastered, active_mastered FROM daily_stats ORDER BY date ASC")
    rows = c.fetchall()
    
    if not rows:
        print("No stats yet!")
        return
        
    print("\\n=== LEARNING ACTIVITY (CARDS REVIEWED) ===")
    max_cards = max(r[1] for r in rows) if rows else 0
    for r in rows:
        date, cards, _, _ = r
        bar = draw_bar(cards, max_cards)
        print(f"{date} | {cards:4} {bar}")
        
    print("\\n=== VOCABULARY GROWTH (MASTERED WORDS) ===")
    max_mast = max(r[2] + r[3] for r in rows) if rows else 0
    for r in rows:
        date, _, p_mast, a_mast = r
        total = p_mast + a_mast
        bar = draw_bar(total, max_mast)
        print(f"{date} | {total:4} (P:{p_mast} A:{a_mast}) {bar}")
        
    print()

if __name__ == '__main__':
    show_stats()
