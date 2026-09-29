import sys
import unittest.mock
import learn

# Simulate pressing Space then K then Q
keys = [' ', 'k', 'q']
def mock_get_char():
    if keys:
        return keys.pop(0)
    return 'q'

with unittest.mock.patch('learn.get_char', side_effect=mock_get_char):
    with unittest.mock.patch('os.system') as mock_os:
        try:
            learn.run_learning()
            print("TEST SUCCESS: Run learning loop completed without exceptions.")
        except Exception as e:
            print(f"TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
