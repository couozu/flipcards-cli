import sqlite3

def show_stats():
    conn = sqlite3.connect('vocab.db')
    c = conn.cursor()
    c.execute("SELECT date, passive_mastered, active_mastered FROM daily_stats ORDER BY date ASC")
    rows = c.fetchall()
    
    if not rows:
        print("No stats yet!")
        return
        
    print("\n=== VOCABULARY GROWTH (MASTERED WORDS) ===")
    print("Legend: ▓ = Passive, █ = Active\n")
    
    max_mast = max(r[1] + r[2] for r in rows) if rows else 0
    max_width = 40
    
    for r in rows:
        date, p_mast, a_mast = r
        total = p_mast + a_mast
        if max_mast == 0:
            bar = ""
        else:
            p_len = int((p_mast / max_mast) * max_width)
            a_len = int((a_mast / max_mast) * max_width)
            bar = "▓" * p_len + "█" * a_len
            
        print(f"{date} | Tot:{total:<4} (P:{p_mast:<3} A:{a_mast:<3}) {bar}")
        
    print()

if __name__ == '__main__':
    show_stats()
