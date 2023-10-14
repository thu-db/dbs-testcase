from argparse import ArgumentParser
from pathlib import Path

from checker import Checker

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("-i", "--in_dir", type=Path, default=Path("./in"))
    parser.add_argument("-a", "--ans_dir", type=Path, default=Path("./ans"))
    parser.add_argument("cmd", nargs="+", help="commands to run user program")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    checker = Checker(args.cmd)
    checker.read_cases(args.in_dir, args.ans_dir)
    checker.print_depends()
    scores = checker.run()
    checker.exit()
    print(f"scores: {scores} / {checker.total_scores}")
