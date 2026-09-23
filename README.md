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

2. **Extract Text**
   Use the `extract.py` script to get the raw text/subtitles:
   ```bash
   python extract.py /path/to/video.mkv > text.txt
   ```

3. **Process Text Contextually**
   Instead of a rigid python script, this project includes an **Antigravity Skill** (`.agents/skills/process-spanish/SKILL.md`) that teaches an AI agent how to process your vocabulary using the context of the sentence!
   
   To use it, just ask your agent (e.g., Antigravity):
   > "Hey, process the Spanish text in `text.txt` using your `process-spanish` skill. Please translate the words into **Russian** (or your preferred language)."
   
   The agent will read the text, translate the words based on their context, and safely merge them into your database (adding hints if a word has multiple meanings).

4. **Learn Words**
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
