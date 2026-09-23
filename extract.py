import sys
import os
import subprocess
import re

def extract_text(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext in ['.mp4', '.mkv', '.avi']:
        print(f"Trying to extract subtitles from {filepath} (requires ffmpeg)...", file=sys.stderr)
        try:
            # Look for Spanish subtitles
            probe_result = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "s", "-show_entries", "stream=index:stream_tags=language", "-of", "csv=p=0", filepath],
                capture_output=True, text=True
            )
            
            stream_index = "0:s:0" # Default to first
            if probe_result.returncode == 0:
                lines = probe_result.stdout.strip().split('\n')
                sub_count = 0
                for line in lines:
                    if not line: continue
                    parts = line.split(',')
                    if len(parts) >= 2 and ('spa' in parts[1].lower() or 'es' in parts[1].lower()):
                        stream_index = f"0:s:{sub_count}"
                        print(f"Found Spanish subtitles (stream {stream_index})", file=sys.stderr)
                        break
                    sub_count += 1
            
            result = subprocess.run(
                ["ffmpeg", "-i", filepath, "-map", stream_index, "-f", "srt", "-"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                text = result.stdout
                # Clean up srt timecodes and HTML tags
                text = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', text)
                text = re.sub(r'<[^>]+>', '', text)
                return text
            else:
                print(f"ffmpeg error or no embedded subtitles. Output: {result.stderr}", file=sys.stderr)
                return ""
        except FileNotFoundError:
            print("ffmpeg is not installed. Install it via: brew install ffmpeg", file=sys.stderr)
            return ""
        except Exception as e:
            print(f"Unknown error: {e}", file=sys.stderr)
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
            print("PyPDF2 is not installed. Run in an environment with the correct dependencies.", file=sys.stderr)
            return ""
            
    elif ext in ['.txt', '.srt']:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
            
    else:
        print(f"File format {ext} is not supported for text extraction.", file=sys.stderr)
        return ""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract.py <filepath>", file=sys.stderr)
        sys.exit(1)
        
    text = extract_text(sys.argv[1])
    if text:
        print(text)
