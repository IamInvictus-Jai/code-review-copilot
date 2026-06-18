import os
import sys
import types
import unittest
import tempfile
import json
import logging


def _stub_heavy_deps():
    """Stub out modules that require langchain/chromadb before importing history."""
    fake_chroma = types.ModuleType("app.services.chroma")
    fake_chroma.learn_convention = lambda rule, repo: None
    sys.modules.setdefault("app.services.chroma", fake_chroma)

    # Stub google.generativeai so history.py's top-level import doesn't fail
    fake_genai = types.ModuleType("google.generativeai")
    fake_genai.configure = lambda **kwargs: None
    fake_genai.GenerativeModel = lambda *args, **kwargs: None
    sys.modules.setdefault("google", types.ModuleType("google"))
    sys.modules.setdefault("google.generativeai", fake_genai)

    # Stub github (PyGitHub) top-level import used in history.py
    fake_github_mod = types.ModuleType("github")
    fake_github_mod.Github = lambda *args, **kwargs: None
    sys.modules.setdefault("github", fake_github_mod)


_stub_heavy_deps()

# Now it is safe to import the module under test
from app.services import history  # noqa: E402


class HistoryHasBeenProcessedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.tmp.close()
        self._orig = history.TRACKING_FILE
        history.TRACKING_FILE = self.tmp.name
        logging.getLogger().setLevel(logging.CRITICAL)

    def tearDown(self):
        history.TRACKING_FILE = self._orig
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    # ------------------------------------------------------------------
    # has_been_processed – missing file
    # ------------------------------------------------------------------
    def test_returns_false_when_tracking_file_missing(self):
        os.remove(history.TRACKING_FILE)
        self.assertFalse(history.has_been_processed("owner/repo"))

    # ------------------------------------------------------------------
    # has_been_processed – corrupted JSON
    # ------------------------------------------------------------------
    def test_returns_false_and_does_not_raise_on_corrupted_json(self):
        with open(history.TRACKING_FILE, "w") as f:
            f.write("{this is not valid json")
        # Must not raise; must return False
        self.assertFalse(history.has_been_processed("owner/repo"))

    # ------------------------------------------------------------------
    # has_been_processed – non-list JSON (e.g. dict)
    # ------------------------------------------------------------------
    def test_returns_false_when_tracking_file_contains_non_list(self):
        with open(history.TRACKING_FILE, "w") as f:
            json.dump({"owner/repo": True}, f)
        self.assertFalse(history.has_been_processed("owner/repo"))

    # ------------------------------------------------------------------
    # has_been_processed – repo present / absent
    # ------------------------------------------------------------------
    def test_returns_true_when_repo_is_tracked(self):
        with open(history.TRACKING_FILE, "w") as f:
            json.dump(["other/repo", "owner/repo"], f)
        self.assertTrue(history.has_been_processed("owner/repo"))

    def test_returns_false_when_repo_is_not_tracked(self):
        with open(history.TRACKING_FILE, "w") as f:
            json.dump(["other/repo"], f)
        self.assertFalse(history.has_been_processed("owner/repo"))


class HistoryMarkAsProcessedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.tmp.close()
        self._orig = history.TRACKING_FILE
        history.TRACKING_FILE = self.tmp.name
        logging.getLogger().setLevel(logging.CRITICAL)

    def tearDown(self):
        history.TRACKING_FILE = self._orig
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def _read(self):
        with open(history.TRACKING_FILE, "r") as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # mark_as_processed – missing tracking file
    # ------------------------------------------------------------------
    def test_creates_tracking_file_when_missing(self):
        os.remove(history.TRACKING_FILE)
        history.mark_as_processed("owner/repo")
        self.assertTrue(os.path.exists(history.TRACKING_FILE))
        self.assertEqual(self._read(), ["owner/repo"])

    # ------------------------------------------------------------------
    # mark_as_processed – corrupted JSON
    # ------------------------------------------------------------------
    def test_resets_and_writes_repo_on_corrupted_json(self):
        with open(history.TRACKING_FILE, "w") as f:
            f.write("{corrupted!")
        history.mark_as_processed("owner/repo")
        self.assertEqual(self._read(), ["owner/repo"])

    # ------------------------------------------------------------------
    # mark_as_processed – non-list JSON
    # ------------------------------------------------------------------
    def test_resets_and_writes_repo_when_tracking_file_is_non_list(self):
        with open(history.TRACKING_FILE, "w") as f:
            json.dump({"existing": "data"}, f)
        history.mark_as_processed("owner/repo")
        self.assertEqual(self._read(), ["owner/repo"])

    # ------------------------------------------------------------------
    # mark_as_processed – normal append behaviour
    # ------------------------------------------------------------------
    def test_appends_new_repo_to_existing_list(self):
        with open(history.TRACKING_FILE, "w") as f:
            json.dump(["first/repo"], f)
        history.mark_as_processed("second/repo")
        self.assertEqual(self._read(), ["first/repo", "second/repo"])

    # ------------------------------------------------------------------
    # mark_as_processed – idempotency
    # ------------------------------------------------------------------
    def test_does_not_duplicate_already_tracked_repo(self):
        with open(history.TRACKING_FILE, "w") as f:
            json.dump(["owner/repo"], f)
        history.mark_as_processed("owner/repo")
        self.assertEqual(self._read(), ["owner/repo"])


if __name__ == "__main__":
    unittest.main()
