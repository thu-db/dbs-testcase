import subprocess
import re
from pathlib import Path


class Answer:
    class Constraint:
        def __init__(self, pks, fks, uks, idx) -> None:
            self.pks = pks
            self.fks = fks
            self.uks = uks
            self.idx = idx

    def __init__(self, lines, is_desc, order_by):
        pass


class TestCase:
    def __init__(self, name, deps, score, desc, sqls) -> None:
        self.sqls = sqls
        self.deps = deps
        self.score = score
        self.name = name
        self.desc = desc


class Checker:
    def __init__(self, cmd) -> None:
        self.prog = subprocess.Popen(cmd,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8')
        self.cases = {}

    def print_depends(self):
        lines = ["flowchart BT"]
        lines += list(self.cases.keys())
        for item in self.cases.values:
            for name in item.deps:
                lines.append(f"{item.name} --> {name}")
        print("\n    ".join(lines))

    def read_cases(self, path):
        path = Path(path)

    def read_case(self, path):
        with open(path) as file:
            text = file.read()
        item = TestCase(
            name=re.search(r"-- @Name: (.*)", text).group(1),
            deps=re.search(r"-- @Depends: (.*)", text).group(1),
            desc=re.search(r"-- @Description: (.*)", text).group(1),
            score=re.search(r"-- @Score: (.*)", text).group(1),
            sqls=re.findall(r"^[^-].*;\s*$", text, re.MULTILINE),
        )
        self.cases[item.name] = item

    def run_case(self):
        sqls = []
        _ans = ""
        for sql in sqls:
            if not sql.endswith('\n'):
                sql += '\n'
            self.prog.stdin.write(sql, flush=True)

    def exit(self):
        try:
            self.prog.stdin.write("exit\n", flush=True)
            # If exit can not finish in 5minutes, it will kill the process
            self.prog.wait(300)
        except (OSError, BrokenPipeError):
            pass
        except subprocess.TimeoutExpired:
            self.prog.kill()
