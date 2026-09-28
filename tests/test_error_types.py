import unittest
from pathlib import Path

from judger.error import CheckFailed
from judger.testcase import Answer, TestCase


class ErrorTypeTests(unittest.TestCase):
    def test_existing_date_error_rejects_duplicate_error(self):
        root = Path(__file__).resolve().parents[1]
        case = TestCase.from_file(
            root / "in/13-date.sql",
            root / "ans/13-date.ans",
            False,
        )
        point = next(point for point in case.test_points if point.ans.headers == ["!ERROR"])
        point.ans.check(Answer(["!ERROR", "date"], point.flags))
        with self.assertRaises(CheckFailed):
            point.ans.check(Answer(["!ERROR", "duplicate"], point.flags))


if __name__ == "__main__":
    unittest.main()
