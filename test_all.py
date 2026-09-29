import sys
import os
import sqlite3
import unittest.mock
import learn

# 1. Use the separate test DB
TEST_DB = "vocab_test.db"
if not os.path.exists(TEST_DB):
    os.system("python3 setup_test_db.py")

# We no longer copy the real DB! We use the isolated dummy DB.
learn.DB_FILE = TEST_DB

# 2. Sequence of keys to simulate a full session:
keys = [
    ' ', 'k',  # Card 1: Know
    'd',       # Card 2: Delete
    ' ', 'u',  # Card 3: Show, then Undo the previous action
    'e', ' ', 'd', # Card 3 again: Edit, Show, Delete
    'q'        # Card 4: Quit
]

def mock_get_char():
    if keys:
        return keys.pop(0)
    return 'q'

def mock_input(prompt):
    return ""

print(f"Running comprehensive integration test on independent '{TEST_DB}'...")

with unittest.mock.patch('learn.get_char', side_effect=mock_get_char):
    with unittest.mock.patch('builtins.input', side_effect=mock_input):
        with unittest.mock.patch('os.system'):
            try:
                learn.run_learning()
                print("\\nTEST SUCCESS: All scenarios executed safely!")
            except Exception as e:
                print(f"\\nTEST FAILED: {e}")
                import traceback
                traceback.print_exc()

# We don't delete the test DB at the end so it can be inspected if needed.
# But we can reset its state for the next run by calling setup_test_db.py
os.system("python3 setup_test_db.py > /dev/null")
