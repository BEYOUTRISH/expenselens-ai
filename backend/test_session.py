"""Test persistent session store."""
import sys
sys.path.insert(0, ".")
import pandas as pd
from app.core.session_store import save_session, get_session, session_exists, delete_session, list_sessions

df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
save_session("test-session", {"df": df, "name": "test"})
loaded = get_session("test-session")
assert loaded["name"] == "test", "Name mismatch"
assert len(loaded["df"]) == 3, "DF rows mismatch"
assert session_exists("test-session"), "Should exist"
print(f"Loaded session: name={loaded['name']}, df_rows={len(loaded['df'])}")

delete_session("test-session")
assert not session_exists("test-session"), "Should be deleted"
print("Delete OK")
print("SESSION STORE: ALL TESTS PASSED")
