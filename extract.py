import sys
import os
import subprocess
import re

def extract_text(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext in ['.mp4', '.mkv', '.avi']:
        print(f"Пытаюсь извлечь субтитры из {filepath} (требуется ffmpeg)...")
        try:
            # Ищем испанские субтитры
            probe_result = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "s", "-show_entries", "stream=index:stream_tags=language", "-of", "csv=p=0", filepath],
                capture_output=True, text=True
            )
            
            stream_index = "0:s:0" # По умолчанию первый
            if probe_result.returncode == 0:
                lines = probe_result.stdout.strip().split('\n')
                # Формат вывода ffprobe: 3,rus \n 4,eng \n 8,spa
                # Нам нужен порядковый номер потока среди субтитров
                sub_count = 0
                for line in lines:
                    if not line: continue
                    parts = line.split(',')
                    if len(parts) >= 2 and ('spa' in parts[1].lower() or 'es' in parts[1].lower()):
                        stream_index = f"0:s:{sub_count}"
                        print(f"Найдены испанские субтитры (поток {stream_index})", file=sys.stderr)
                        break
                    sub_count += 1
            
            result = subprocess.run(
                ["ffmpeg", "-i", filepath, "-map", stream_index, "-f", "srt", "-"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                text = result.stdout
                # Очищаем srt от таймкодов и HTML тегов
                text = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', text)
                text = re.sub(r'<[^>]+>', '', text)
                return text
            else:
                print(f"Ошибка ffmpeg или в видео нет встроенных субтитров. Вывод: {result.stderr}")
                return ""
        except FileNotFoundError:
            print("ffmpeg не установлен. Установите его: brew install ffmpeg")
            return ""
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            return ""
            
    elif ext == '.pdf':
        try:
            import PyPDF2
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                return text
        except ImportError:
            print("PyPDF2 не установлен. Запустите в окружении с нужными зависимостями.")
            return ""
            
    elif ext in ['.txt', '.srt']:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
            
    else:
        print(f"Формат файла {ext} не поддерживается для извлечения текста.")
        return ""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python extract.py <путь_к_файлу>")
        sys.exit(1)
        
    text = extract_text(sys.argv[1])
    if text:
        print(text)
