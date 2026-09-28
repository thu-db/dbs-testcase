import unittest
from pathlib import Path

from judger.error import CheckFailed
from judger.testcase import Answer, TestCase, TestPoint


class OrderByTests(unittest.TestCase):
    def test_order_by_before_semicolon_is_detected(self):
        for sql, fields, descending in (
            ("SELECT * FROM T ORDER BY id;", ["id"], False),
            ("SELECT * FROM T ORDER BY id DESC;", ["id"], True),
            ("SELECT * FROM T ORDER BY id, value ASC;", ["id", "value"], False),
            ("SELECT * FROM T ORDER BY id LIMIT 2;", ["id"], False),
        ):
            with self.subTest(sql=sql):
                flags = TestPoint.generate_flags(sql)
                self.assertEqual(flags.order_by, fields)
                self.assertEqual(flags.reversed_order, descending)

    def test_existing_ascending_case_rejects_reordered_rows(self):
        root = Path(__file__).resolve().parents[1]
        case = TestCase.from_file(
            root / "in/12-query-order.sql",
            root / "ans/12-query-order.ans",
            False,
        )
        point = next(
            point for point in case.test_points
            if point.sql == "SELECT * FROM NATION ORDER BY N_REGIONKEY;"
        )
        expected = point.ans
        lines = [",".join(expected.headers)] + [",".join(row) for row in expected.data]
        expected.check(Answer(lines, point.flags))
        lines[1], lines[-1] = lines[-1], lines[1]
        with self.assertRaises((AssertionError, CheckFailed)):
            expected.check(Answer(lines, point.flags))

    def test_qualified_headers_cannot_disable_order_check(self):
        root = Path(__file__).resolve().parents[1]
        case = TestCase.from_file(
            root / "in/12-query-order.sql",
            root / "ans/12-query-order.ans",
            False,
        )
        point = next(
            point for point in case.test_points
            if point.sql == "SELECT * FROM NATION ORDER BY N_REGIONKEY DESC;"
        )
        expected = point.ans
        lines = [",".join(f"NATION.{header}" for header in expected.headers)]
        lines.extend(",".join(row) for row in expected.data)
        expected.check(Answer(lines, point.flags))
        lines[1], lines[-1] = lines[-1], lines[1]
        with self.assertRaises((AssertionError, CheckFailed)):
            expected.check(Answer(lines, point.flags))

if __name__ == "__main__":
    unittest.main()
