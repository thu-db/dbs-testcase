import subprocess
import re
from pathlib import Path


class Answer:
    class Constraint:
        pk_regex = re.compile(r"PRIMARY\s+KEY\s+(?P<name>\w*)\((?P<fields>\w+(?:,\s*\w+)*)\);")
        fk_regex = re.compile(r"FOREIGN\s+KEY\s+(?P<name>\w*)\((?P<fields>\w+(?:,\s*\w+)*)\)\s+REFERENCES\s(?P<ref_table>\w+)\((?P<ref_fields>\w+(?:,\s*\w+)*)\);")
        uk_regex = re.compile(r"UNIQUE\s+(?P<name>\w*)\((?P<fields>\w+(?:,\s*\w+)*)\);")
        idx_regex = re.compile(r"INDEX\s+(?P<name>\w*)\((?P<fields>\w+(?:,\s*\w+)*)\);")
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
                    ref_fields = m.group("ref_fields").replace(" ", "").split(",")
                    if len(fields) != len(ref_fields):
                        raise ValueError(f"{len(fields)} fields mismatches {len(ref_fields)} refer fields")
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
            assert not ((self.pk is None) ^ (other.pk is None))
            if self.pk is not None:
                if self.pk["name"]:
                    assert self.pk["name"] == other.pk["name"]
                assert self.pk["fields"] == other.pk["fields"]
            # check fk
            assert len(self.fks) == len(other.fks)
            for i in range(len(self.fks)):
                if self.fks[i]["name"]:
                    assert self.fks[i]["name"] == other.fks[i]["name"]
                assert self.fks[i]["fields"] == other.fks[i]["fileds"]
                assert self.fks[i]["ref_fields"] == other.fks[i]["ref_fields"]
            # check uk
            assert len(self.uks) == len(other.uks)
            for i in range(len(self.uks)):
                if self.uks[i]["name"]:
                    assert self.uks[i]["name"] == other.uks[i]["name"]
                assert self.uks[i]["fields"] == other.uks[i]["fileds"]
            # check idx
            assert len(self.idx) == len(other.idx)
            for i in range(len(self.idx)):
                if self.idx[i]["name"]:
                    assert self.idx[i]["name"] == other.idx[i]["name"]
                assert self.idx[i]["fields"] == other.idx[i]["fileds"]

    def __init__(self, lines, is_desc, colume_order, order_by, asc):
        # Note: is_desc means "is description", asc means "ascend"
        self.is_desc = is_desc
        self.colume_order = colume_order
        self.headers = lines[0].split(",") if lines else []
        # Ignore order key not in the output headers
        self.order_by = order_by if order_by and all(field in self.headers for field in order_by) else None
        self.asc = asc
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
            keys = [tuple(each[field] for field in self.order_by) for each in other.data]
            if self.asc:
                for i in range(1, len(keys)):
                    assert keys[i - 1] <= keys[i]
            else:
                for i in range(1, len(keys)):
                    assert keys[i - 1] >= keys[i]


class TestPoint:
    def __init__(self, sql, ans) -> None:
        self.sql: str = sql
        self.ans: Answer = ans


class TestCase:
    def __init__(self, name, deps, score, desc, sqls) -> None:
        self.sqls = sqls
        self.test_points = []
        self.deps = deps
        self.score = score
        self.name = name
        self.desc = desc
    
    def load_ans(self, text: str) -> bool:
        lines = [l.strip() for l in text.splitlines()]
        if not (lines.count("@BEGIN") == lines.count("@END") == len(self.sqls)):
            raise ValueError(f'ans file has {lines.count("@BEGIN")} BEGIN, {lines.count("@END")} END when in file has {len(self.sqls)} sqls')
        for i in range(len(self.sqls)):
            begin = lines.index("@BEGIN")
            end = lines.index("@END")
            ans_lines = lines[begin + 1: end]
            is_desc = False
            select_star = False
            order_by = None
            asc = False
            for line in lines[:begin]:
                if line == "@DESC":
                    is_desc = True
                elif line == "@STAR":
                    select_star = True
                elif line.startswith("@ORDER "):
                    order_by = line.split()[1:]
                elif line == "@ASC":
                    asc = True
            self.test_points.append(TestPoint(
                sql=self.sqls[i],
                ans=Answer(ans_lines, is_desc, not select_star, order_by, asc),
            ))
            lines = lines[end + 1:]


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
        self.start()

    def print_depends(self):
        lines = ["flowchart BT"]
        lines += list(self.cases.keys())
        for item in self.cases.values():
            for name in item.deps:
                lines.append(f"{item.name} --> {name}")
        print("\n    ".join(lines))

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
            print("read", len(item.test_points), "test points for", item.name)
        except Exception:
            from traceback import print_exc
            print_exc()
    
    def _run_case(self, _case):
        for point in _case.test_points:
            self.prog.stdin.write(point.sql + "\n", flush=True)
            lines = []
            while True:
                line: str = self.prog.stdout.readline()
                if line.startswith("@"):
                    break
                lines.append(line)
            ans: Answer = point.ans
            out = Answer(lines, ans.is_desc, ans.colume_order, ans.order_by)
            ans.check(out)

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
            self._run_case(_case)
            self.scores += _case.score
            self.passed_cases.add(name)
            return True
        except Exception:
            from traceback import print_exc
            print_exc()
            self.failed_cases.add(name)
            return False

    def run(self):
        print(self.cases)
        for name in self.cases:
            self.run_case(name)
        return self.scores

    def start(self):
        self.prog = subprocess.Popen(self.cmd,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8')

    def exit(self):
        try:
            self.prog.stdin.write("exit\n", flush=True)
            # If exit can not finish in 1minutes, it will kill the process
            self.prog.wait(60)
        except (OSError, BrokenPipeError):
            pass
        except subprocess.TimeoutExpired:
            self.kill()
    
    def kill(self):
        self.prog.kill()
