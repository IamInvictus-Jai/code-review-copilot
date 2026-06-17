import unittest
from app.utils.diff_parser import annotate_diff

class TestDiffParser(unittest.TestCase):
    def test_annotate_diff_simple(self):
        raw_diff = (
            "+++ b/file.txt\n"
            "@@ -1,3 +1,4 @@\n"
            "  line1\n"
            "- old line\n"
            "+ new line\n"
            "  line3"
        )
        expected = (
            "+++ b/file.txt\n"
            "@@ -1,3 +1,4 @@\n"
            "[1]   line1\n"
            "- old line\n"
            "[2] + new line\n"
            "[3]   line3"
        )
        self.assertEqual(annotate_diff(raw_diff), expected)

    def test_annotate_diff_no_hunk_match(self):
        raw_diff = "random text"
        self.assertEqual(annotate_diff(raw_diff), "random text")

    def test_annotate_diff_empty(self):
        self.assertEqual(annotate_diff(""), "")

if __name__ == "__main__":
    unittest.main()
