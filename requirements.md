# Spanish Flashcards CLI - Requirements & Specifications

## Core Purpose
A terminal-based flashcard application (Spaced Repetition System) specifically designed for learning Spanish vocabulary extracted from media (subtitles). It operates entirely locally using SQLite and a Python CLI.

## Card Types & Modes
The app supports two learning directions for each word:
1. **Passive Review (Spanish -> Russian):**
   - Front: Spanish word (with definite article visually stripped if present).
   - Back: Russian translation + hint + original Spanish word (with article).
2. **Active Review (Russian -> Spanish):**
   - Front: Russian translation + hint.
   - Back: Spanish word (with article).
   - *Unlock Condition:* A word's active card is unlocked automatically only when its passive card reaches `repetitions >= 3`.

## Spaced Repetition Algorithm (SM-2 based)
Each word has independent scheduling for its Passive and Active states:
- `interval`: Days until next review.
- `repetitions`: Consecutive correct answers.
- `ease_factor`: Multiplier for interval growth (starts at 2.5).

**Grading Logic:**
- **Known (Pass):** 
  - If reps == 0: interval = 1
  - If reps == 1: interval = 6
  - If reps > 1: interval = interval * ease_factor
  - reps += 1
- **Unknown (Fail):**
  - **CRITICAL:** interval = 0 (Must remain in the queue for today until passed).
  - reps = 0
  - ease_factor = max(1.3, ease_factor - 0.2)

## UI & Controls
- **Card Front (Question):**
  - `[Space]`: Show translation (flip to back).
  - `[D]`: Ignore/Delete card in the *current mode only* (Passive or Active).
  - `[0-9]`: Show statistics screen.
  - `[Left Arrow]`: Undo the last review action.
  - `[Q]`: Quit.
- **Card Back (Answer):**
  - `[Space]`: Grade as "Don't Know" (Fail).
  - `[K]`: Grade as "Know" (Pass).
  - `[D]`: Ignore/Delete card in current mode.
  - `[E]`: Edit the Russian translation.
  - `[0-9]`: Show statistics screen.
  - `[Left Arrow]`: Undo the last review action.
  - `[Q]`: Quit.

## Ignore / Delete Logic
- Deletions are scoped to the mode. Pressing `D` on a Passive card ignores it for Passive review forever. Pressing `D` on an Active card ignores it for Active review forever. 

## Statistics & Tracking
- **Time Tracking:** The app tracks the total time spent in the program across all sessions, and the time spent today.
- **Card Tracking:** Tracks the number of cards reviewed today.
- **Vocabulary Mastery:**
  - *Securely in Passive Vocab:* `passive_ignored = 1` OR `passive_repetitions >= 3`.
  - *Securely in Active Vocab:* `active_ignored = 1` OR `active_repetitions >= 3`.
  - Words can fluctuate in and out of mastery if they are failed (repetitions reset to 0).

## Queue Selection
- Words due for review (`next_review <= now`) are fetched.
- **Weighted Randomness:** Instead of strict ordering, due words are selected randomly, weighted by their occurrence `frequency` in the source text. Higher frequency words appear more often but not exclusively.

## Vocabulary Extraction Rules (SKILL.md)
When parsing new texts:
- Lemmatize strictly (infinitive verbs, singular masculine adjectives, singular nouns).
- Do NOT include proper names (people, places, brands).
- Do NOT include standalone numbers or units (dos, 92, km/h).
- Do NOT add definite articles (el/la) to nouns in the extraction phase (handled manually if needed).
