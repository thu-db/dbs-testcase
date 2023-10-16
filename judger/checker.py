import subprocess
import re
import sys
from pathlib import Path
import os
import resource

from .testcase import TestCase, TestPoint, Answer
from .error import CheckFailed, PointFailed

class Checker:
    def __init__(self, cmd, gen_ans) -> None:
        # judgement meta
        self.gen_ans = gen_ans
        self.prog: subprocess.Popen = None
        self.cases = {}
        self.scores = 0
        self.total_scores = 0
        self.passed_cases = set()
        self.failed_cases = set()
        self.skipped_cases = set()
        
        # user program meta
        self.cmd = cmd
        self.env = dict(**os.environ, OMP_NUM_THREADS="1")
        self.memory_limit = 512 * 1024 * 1024
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
            if not self.gen_ans and not ans_path.exists():
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
        self.cases[item.name] = item
        if self.gen_ans:
            return

        with open(ans_path) as file:
            text = file.read()
        try:
            item.load_ans(text)
            self.total_scores += item.score
            print("[INFO] read", len(item.test_points),
                  "test points for", item.name)

        except Exception:
            from traceback import print_exc
            print_exc(file=sys.stdout)
            self.cases.pop(item.name)

    def _run_case(self, _case):
        # Restart the killed process
        if self.prog.poll():
            self.start()
        for point in _case.test_points:
            point: TestPoint
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
            if self.gen_ans:
                # TODO finish write ans
                print(*lines, sep='\n')
                print(f"@{point.sql}\n")
                continue
            ans: Answer = point.ans
            out = Answer(lines, ans.flags)
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
        def count_n_generator(n):
            while True:
                for _ in range(n - 1):
                    yield False
                yield True
        exit_counter = count_n_generator(5)
        for name in self.cases:
            self.run_case(name)
            if next(exit_counter):
                self.exit()
        return self.scores

    def start(self):
        def set_memory_limit():
            if sys.platform != "linux":
                return
            resource.setrlimit(resource.RLIMIT_AS, (self.memory_limit, self.memory_limit))
        self.prog = subprocess.Popen(self.cmd, encoding='utf-8', 
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     env=self.env, preexec_fn=set_memory_limit)
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
