from argparse import ArgumentParser
from pathlib import Path
from os import environ

from judger import Checker


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("-i", "--in_dir", type=Path, default=Path("./in"))
    parser.add_argument("-a", "--ans_dir", type=Path, default=Path("./ans"))
    parser.add_argument("--std", action="store_true",
                        help="use it to generate ans with std program")
    parser.add_argument("--graph", action="store_true", help="print mermaid graph and exit")
    parser.add_argument("cmd", nargs="+", help="commands to run user program")
    parser.add_argument("-f", "--flags", nargs="*", help="flags to enable these testcases")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.std:
        environ["PYTHONPATH"] = environ.get("PYTHONPATH", "") + ":."
    checker = Checker(args.cmd, args.std, args.flags)
    checker.read_cases(args.in_dir, args.ans_dir)
    if args.graph:
        checker.print_depends()
    else:
        checker.run()
        checker.report()
