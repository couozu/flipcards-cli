---
name: process-spanish
description: >-
  Use this skill when the user asks to process a Spanish text or subtitle file to extract vocabulary for their flashcards database (vocab.db).
---

# Process Spanish Subtitles and Text

This skill instructs you on how to extract vocabulary from a Spanish text file, translate it contextually, and insert it into the user's Spaced Repetition database.

## Steps

1. **Clarify Language Preference**
   If the user has not specified a target translation language in their prompt, ask them what language they want the Spanish words translated into before proceeding.

2. **Read the Source Text**
   Use your file reading tools to read the provided text or subtitle file. 

3. **Extract and Translate Contextually (with Lemmatization)**
   Analyze the text. Extract all unique Spanish words. **CRITICAL: You must lemmatize the words before adding them:**
   - Verbs must be converted to their **infinitive** form (e.g. `comen` -> `comer`, `verás` -> `ver`).
   - Adjectives must be converted to **masculine, singular** form (e.g. `chiquitas` -> `chiquito`).
   - Nouns must be converted to **singular** form AND MUST include their definite article (el/la) to indicate gender (e.g. `las tonterías` -> `la tontería`, `problema` -> `el problema`).
   
   Translate each lemmatized word into the user's preferred target language **based on the context** of the sentence it appeared in. 
   - *Handling Clashes/Homonyms*: If the exact same lemmatized Spanish word appears in multiple different contexts with completely different meanings (e.g., "banco" as a financial bank vs "banco" as a park bench), create separate entries for each meaning and provide a short `hint` in English or the target language to distinguish them (e.g. `hint: финансовое учреждение`). If there is only one meaning, leave the hint empty (`""`).

4. **Prepare JSON Data**
   Format your extracted vocabulary into a JSON array of objects. Each object must have:
   - `word` (string): The Spanish word.
   - `translation` (string): The contextual translation.
   - `hint` (string): A short hint if there is a clash, otherwise `""`.

5. **Insert into Database**
   Write the JSON array to a temporary file (e.g. `/tmp/vocab.json`), and then use the helper script to safely insert it into the SQLite database:
   ```bash
   python .agents/skills/process-spanish/scripts/insert.py /tmp/vocab.json
   ```
   *Note: The helper script automatically handles duplicates and diffs against the existing database, so you don't need to worry about over-writing progress.*

   After insertion, you must calculate and save the frequencies of the words so that the flashcards can prioritize the most common words:
   ```bash
   python .agents/skills/process-spanish/scripts/update_freqs.py /path/to/source.txt /tmp/vocab.json
   ```

6. **Validation (Completeness Check)**
   After inserting the words, you must verify that no words were accidentally skipped (as LLMs sometimes drop words when processing large texts).
   - Write a quick python script to extract all raw unique Spanish words from the source text using a simple regex (e.g. `re.findall(r'[a-záéíóúñü]+', text.lower())`).
   - Query `vocab.db` to get all words currently in the database.
   - For any raw words from the text that do not seem to have a corresponding lemma in the database, do a second pass to translate and insert those missing words!

7. **Report**
   Tell the user how many words were successfully processed and added, and suggest they run `python learn.py` to practice!
