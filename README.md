# Flipcards CLI (Spanish Learning)

A command-line prototype for learning Spanish words using a Spaced Repetition System (SRS).

## Requirements

- Python 3
- `ffmpeg` (for extracting subtitles from video files). Install on macOS: `brew install ffmpeg`

## How to use

1. **Activate the virtual environment**
   First, navigate to the project directory and activate the virtual environment (dependencies are already installed):
   ```bash
   source venv/bin/activate
   ```

2. **Extract text (Step 1)**
   The `extract.py` script extracts text from `.srt`, `.txt`, `.pdf`, and video files (if they have embedded subtitles).
   ```bash
   python extract.py /path/to/video.mkv > text.txt
   ```

3. **Process text and add to DB (Step 2)**
   The `process.py` script takes the text, extracts unique Spanish words, translates them to Russian (via Google Translate), and adds them to the local SQLite database `vocab.db`.
   ```bash
   python process.py text.txt
   ```
   *Pro tip:* You can combine steps 1 and 2 without creating a temporary file:
   ```bash
   python extract.py /path/to/video.mkv | python process.py -
   ```

4. **Learn words (Step 3)**
   The `learn.py` script runs the terminal UI for practicing words.
   ```bash
   python learn.py
   ```
   **Controls:**
   - `Space` - Show translation
   - `Any digit (0-9)` - Show statistics (total words in DB, words left for today)
   - `Any key on the LEFT half of the keyboard` - **Don't know** (resets progress, word will be shown again tomorrow)
   - `Any key on the RIGHT half of the keyboard` - **Know** (word is delayed based on the SRS algorithm)
   - `Q` - Quit
