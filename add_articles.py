import sqlite3
import google.generativeai as genai
import json
import os

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

DB_FILE = "/Users/couozu/.gemini/antigravity/scratch/spanish_learning/vocab.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

c.execute("SELECT id, word FROM words WHERE is_ignored = 0")
words = c.fetchall()

prompt = """
I have a list of Spanish words. I want you to identify which ones are NOUNS.
For all NOUNS, return a JSON object mapping the original word to the word WITH its definite article (el, la, los, las).
For words that are NOT nouns (verbs, adjectives, prepositions, phrases, pronouns), do NOT include them in the JSON.
For example, if the list is: ['perro', 'correr', 'problema', 'rapido', 'mano']
You return: {"perro": "el perro", "problema": "el problema", "mano": "la mano"}

Here are the words:
"""

word_list = [w[1] for w in words]

batch_size = 300
updated = 0

for i in range(0, len(word_list), batch_size):
    batch = word_list[i:i+batch_size]
    print(f"Processing batch {i//batch_size + 1}...")
    
    response = model.generate_content(prompt + json.dumps(batch))
    
    text = response.text
    # extract json
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
        
    try:
        mapping = json.loads(text)
        for orig, with_article in mapping.items():
            if orig != with_article:
                c.execute("UPDATE words SET word = ? WHERE word = ?", (with_article, orig))
                updated += 1
    except Exception as e:
        print("Failed to parse JSON:", text)
        print(e)

conn.commit()
conn.close()
print(f"Successfully updated {updated} nouns with their definite articles!")
