import shutil
import datetime
import os
import sys

def backup_db(db_path='vocab.db', dest_dir='backups'):
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} not found.")
        return
        
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(dest_dir, f'vocab_backup_{timestamp}.db')
    
    shutil.copy2(db_path, backup_file)
    print(f"✅ База данных успешно сохранена в: {backup_file}")
    
    # Оставляем только 10 последних бэкапов в этой папке, чтобы не мусорить
    backups = sorted([os.path.join(dest_dir, f) for f in os.listdir(dest_dir) if f.startswith('vocab_backup_') and f.endswith('.db')])
    while len(backups) > 10:
        oldest = backups.pop(0)
        os.remove(oldest)
        print(f"Удален старый бэкап: {oldest}")

if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else 'backups'
    backup_db(dest_dir=dest)
