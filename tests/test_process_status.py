import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from judger.checker import Checker


class ProcessStatusTests(unittest.TestCase):
    def test_failed_init_is_rejected(self):
        checker = Checker([sys.executable, "-c", "import sys; sys.exit(7)"], False, [], None)
        with self.assertRaises(subprocess.CalledProcessError) as error:
            checker.init()
        self.assertEqual(error.exception.returncode, 7)

    def test_run_ci_propagates_runner_crash(self):
        runner = Path(__file__).resolve().parents[1] / "run-ci.py"
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "testcase.yml").write_text(
                "compile:\n  commands: /bin/true\nrun:\n  commands: ./missing-dbms\n  flags: []\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(runner)], cwd=directory,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("FileNotFoundError", result.stderr)


if __name__ == "__main__":
    unittest.main()
