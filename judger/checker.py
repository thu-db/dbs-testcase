import subprocess
import re
import sys
from pathlib import Path


class PointFailed(Exception):
    pass


class CheckFailed(Exception):
    def __init__(self, msg, ans, out):
        self.msg = msg
        self.ans = ans
        self.out = out

    def __repr__(self) -> str:
        return f"CheckFailed: {self.msg}, but expected is [{self.ans}] and output is [{self.out}]"


def assert_eq(msg, ans, out):
    if ans != out:
        raise CheckFailed(msg, ans, out)


class Answer:
    class Constraint:
        pk_regex = re.compile(
            r"PRIMARY\s+KEY\s+(?P<name>\w*)\((?P<fields>\w+(?:,\s*\w+)*)\);")
        fk_regex = re.compile(
            r"FOREIGN\s+KEY\s+(?P<name>\w*)\((?P<fields>\w+(?:,\s*\w+)*)\)\s+REFERENCES\s(?P<ref_table>\w+)\((?P<ref_fields>\w+(?:,\s*\w+)*)\);")
        uk_regex = re.compile(
            r"UNIQUE\s+(?P<name>\w*)\((?P<fields>\w+(?:,\s*\w+)*)\);")
        idx_regex = re.compile(
            r"INDEX\s+(?P<name>\w*)\((?P<fields>\w+(?:,\s*\w+)*)\);")

        def __init__(self, lines) -> None:
            self.pk = None
            self.fks = []
            self.uks = []
            self.idx = []
            if lines:
                self.parse_lines(lines)

        def parse_lines(self, lines):
            for line in lines:
                if self.pk_regex.match(line):
                    m = self.pk_regex.match(line)
                    # Make sure at most one primary key
                    if self.pk is not None:
                        raise ValueError("Duplicated primary key")
                    self.pk = {
                        "name": m.group("name"),
                        "fields": m.group("fields").replace(" ", "").split(",")
                    }
                elif self.fk_regex.match(line):
                    m = self.fk_regex.match(line)
                    fields = m.group("fields").replace(" ", "").split(",")
                    ref_fields = m.group("ref_fields").replace(
                        " ", "").split(",")
                    if len(fields) != len(ref_fields):
                        raise ValueError(
                            f"{len(fields)} fields mismatches {len(ref_fields)} refer fields")
                    self.fks.append({
                        "name": m.group("name"),
                        "table": m.group("ref_table"),
                        "fields": fields,
                        "ref_fields": ref_fields,
                    })
                elif self.uk_regex.match(line):
                    m = self.uk_regex.match(line)
                    self.uks.append({
                        "name": m.group("name"),
                        "fields": m.group("fields").replace(" ", "").split(",")
                    })
                elif self.idx_regex.match(line):
                    m = self.idx_regex.match(line)
                    self.idx.append({
                        "name": m.group("name"),
                        "fields": m.group("fields").replace(" ", "").split(",")
                    })
            self.fks.sort(key=lambda e: (e["fields"], e["ref_fields"]))
            self.uks.sort(key=lambda e: e["fields"])
            self.idx.sort(key=lambda e: e["fields"])

        def check(self, other: "Answer.Constraint"):
            # check pk
            assert_eq("Check primary key existence",
                      bool(self.pk), bool(other.pk))
            if self.pk is not None:
                if self.pk["name"]:
                    assert_eq("Check primary key name",
                              self.pk["name"], other.pk["name"])
                assert_eq("Check primary key fields",
                          self.pk["fields"], other.pk["fields"])
            # check fk
            assert_eq("Check foreign keys number",
                      len(self.fks), len(other.fks))
            for fk, ofk in zip(self.fks, other.fks):
                if fk["name"]:
                    assert_eq("Check foreign key name",
                              fk["name"], ofk["name"])
                assert_eq("Check foreign key fields",
                          fk["fields"], ofk["fields"])
                assert_eq("Check foreign key table",
                          fk["table"], ofk["table"])
                assert_eq("Check foreign key refer fields",
                          fk["ref_fields"], ofk["ref_fields"])
            # check uk
            assert_eq("Check union keys number", len(self.uks), len(other.uks))
            for uk, ouk in zip(self.uks, other.uks):
                if uk["name"]:
                    assert_eq("Check union key name", uk["name"], ouk["name"])
                assert_eq("Check union key fields",
                          uk["fields"], ouk["fileds"])
            # check idx
            assert_eq("Check index number", len(self.idx), len(other.idx))
            for idx, oidx in zip(self.idx, other.idx):
                if idx["name"]:
                    assert_eq("Checker index name", idx["name"], oidx["name"])
                assert_eq("Check index fields", idx["fields"], oidx["fileds"])

    def __init__(self, lines, is_desc, colume_order, order_by, reversed_order):
        # Note: is_desc means "is description", reversed_order means "ORDER BY ... DESC"
        self.is_desc = is_desc
        self.colume_order = colume_order
        self.headers = lines[0].split(",") if lines else []
        # Ignore order key not in the output headers
        self.order_by = order_by if order_by and all(
            field in self.headers for field in order_by) else None
        self.reversed_order = reversed_order
        self.constraint = None
        if is_desc:
            if "" in lines:
                blank_line = lines.index("")
                self.constraint = Answer.Constraint(lines[blank_line + 1:])
                lines = lines[:blank_line]
            else:
                self.constraint = Answer.Constraint([])
        self.data = [
            {
                self.headers[i]: val for i, val in enumerate(line.split(','))
            } for line in lines[1:]
        ]

    def to_regular_data(self):
        regular_headers = sorted(self.headers)
        return tuple(tuple(each[h] for h in regular_headers) for each in self.data)

    def check(self, other: "Answer"):
        if self.is_desc:
            self.constraint.check(other.constraint)
        if self.colume_order:
            assert self.headers == other.headers
        assert len(self.data) == len(other.data)
        assert self.to_regular_data() == other.to_regular_data()
        if self.order_by:
            keys = [tuple(each[field] for field in self.order_by)
                    for each in other.data]
            if self.reversed_order:
                for i in range(1, len(keys)):
                    assert keys[i - 1] >= keys[i]
            else:
                for i in range(1, len(keys)):
                    assert keys[i - 1] <= keys[i]


class TestPoint:
    def __init__(self, sql, ans) -> None:
        self.sql: str = sql
        self.ans: Answer = ans


def count_n_generator(n):
    while True:
        for _ in range(n - 1):
            yield False
        yield True


class TestCase:
    def __init__(self, name, deps, score, desc, sqls) -> None:
        self.sqls = sqls
        self.test_points = []
        self.deps = deps
        self.score = score
        self.name = name
        self.desc = desc

    def load_ans(self, text: str) -> bool:
        parts = re.split(r'^@.*$', text, flags=re.MULTILINE)
        # Clear trailing lines after last @line
        parts.pop()
        if len(parts) != len(self.sqls):
            raise ValueError(
                f"ans_file has {len(parts)} parts ended by @line but in_file has {len(self.sqls)} sqls")
        '''if not (lines.count("@BEGIN") == lines.count("@END") == len(self.sqls)):
            raise ValueError(
                f'ans file has {lines.count("@BEGIN")} BEGIN, {lines.count("@END")} END when in file has {len(self.sqls)} sqls')'''
        for part, sql in zip(parts, self.sqls):
            sql: str = sql.strip()
            lines = [line.strip() for line in part.strip().splitlines()]
            is_desc = bool(re.match(r"DESC\s", sql))
            select_star = bool(re.match(r"SELECT\s", sql))
            m = re.search(
                r"ORDER\s+BY\s+([^, ]*(?:\s*,\s*[^, ]*)*)\s+(ASC|DESC)?", sql)
            order_by = m and m.group(1).replace(" ", "").split(",")
            reversed_order = m and m.group(2) == "DESC"
            self.test_points.append(TestPoint(
                sql=sql,
                ans=Answer(lines, is_desc, not select_star,
                           order_by, reversed_order),
            ))


class Checker:
    def __init__(self, cmd) -> None:
        self.cmd = cmd
        self.prog: subprocess.Popen = None
        self.cases = {}
        self.scores = 0
        self.total_scores = 0
        self.passed_cases = set()
        self.failed_cases = set()
        self.skipped_cases = set()
        # On windows kill() is exactly terminate(), so record the running states manually
        self.runnning = False
        self.start()

    def print_depends(self):
        lines = ["flowchart BT"]
        lines += list(self.cases.keys())
        for item in self.cases.values():
            for name in item.deps:
                lines.append(f"{item.name} --> {name}")
        print("\n    ".join(lines))

    def report(self):
        pass

    def read_cases(self, in_dir, ans_dir):
        in_dir = Path(in_dir)
        ans_dir = Path(ans_dir)
        for in_path in in_dir.iterdir():
            if in_path.suffix != ".sql":
                print("[WARN] Ignore non-sql file in in_dir:", in_path)
                continue
            ans_path = ans_dir / (in_path.stem + ".ans")
            if not ans_path.exists():
                print("[WARN] sql file has no ans:", in_dir)
                continue
            self.read_case(in_path, ans_path)
        print("[INFO] read", len(self.cases), "cases in total")

    def read_case(self, in_path, ans_path):
        with open(in_path) as file:
            text = file.read()
        item = TestCase(
            name=re.search(r"-- @Name: (.*)", text).group(1),
            deps=re.search(r"-- @Depends: (.*)", text).group(1).split(),
            desc=re.search(r"-- @Description: (.*)", text).group(1),
            score=int(re.search(r"-- @Score: (.*)", text).group(1)),
            sqls=re.findall(r"^[^-].*;\s*$", text, re.MULTILINE),
        )
        with open(ans_path) as file:
            text = file.read()
        try:
            item.load_ans(text)
            self.cases[item.name] = item
            self.total_scores += item.score
            print("[INFO] read", len(item.test_points),
                  "test points for", item.name)

        except Exception:
            from traceback import print_exc
            print_exc(file=sys.stdout)

    def _run_case(self, _case):
        # Restart the killed process
        if self.prog.poll():
            self.start()
        for point in _case.test_points:
            # print("[DEBUG] run sql:" point.sql)
            self.prog.stdin.write(point.sql + "\n")
            self.prog.stdin.flush()
            lines = []
            while True:
                line: str = self.prog.stdout.readline()
                if line.startswith("@"):
                    break
                # Note that readline will contains the "\n"
                lines.append(line.strip())
            # print("[DEBUG] read output", lines)
            ans: Answer = point.ans
            out = Answer(lines, ans.is_desc, ans.colume_order,
                         ans.order_by, ans.reversed_order)
            try:
                ans.check(out)
            except CheckFailed as e:
                print(repr(e))
                raise PointFailed(point.sql)
            except Exception:
                from traceback import print_exc
                print_exc(file=sys.stdout)
                raise PointFailed(point.sql)

    def run_case(self, name):
        if name in self.passed_cases:
            return True
        if name in self.failed_cases or name in self.skipped_cases:
            return False
        _case: TestCase = self.cases[name]
        for depend_case in _case.deps:
            if depend_case in self.passed_cases:
                continue
            if depend_case in self.failed_cases or depend_case in self.skipped_cases or not self.run_case(depend_case):
                self.skipped_cases.add(name)
                return False
            # run depend_case successfully: continue
        try:
            print("[INFO] Case", name, "starts")
            self._run_case(_case)
            self.scores += _case.score
            self.passed_cases.add(name)
            print("[INFO] Case", name, "passed")
            return True
        except KeyboardInterrupt:
            self.kill()
            raise
        except PointFailed as e:
            print("[ERROR] case", name, "failed because", repr(e))
            self.failed_cases.add(name)
            return False
        except Exception:
            from traceback import print_exc
            print_exc(file=sys.stdout)
            print("[CRITICAL] Meet error when running user program, try to restart...")
            if self.prog.poll():
                self.runnning = False
            self.failed_cases.add(name)
            return False

    def run(self):
        exit_counter = count_n_generator(5)
        for name in self.cases:
            self.run_case(name)
            if next(exit_counter):
                self.exit()
        return self.scores

    def start(self):
        self.prog = subprocess.Popen(self.cmd,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8')
        self.runnning = True

    def exit(self):
        try:
            self.prog.stdin.write("exit\n")
            self.prog.stdin.flush()
            # If exit can not finish in 1minutes, it will kill the process
            self.prog.wait(60)
        except (OSError, BrokenPipeError):
            pass
        except subprocess.TimeoutExpired:
            self.kill()
        self.runnning = False

    def kill(self):
        self.prog.kill()
        self.runnning = False
