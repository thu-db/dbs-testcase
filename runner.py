from argparse import ArgumentParser

from checker import Checker

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("cmd", nargs="+", help="commands to run user program")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    try:
        for i in range(1000000):
            if prog.poll() is not None:
                break
            try:
                prog.stdin.write(f"hello world {i}\n")
                prog.stdin.flush()
            except OSError as e:
                # Windows won't response on `proc.poll()`, it raises OSError 22 instead
                if e.errno == 22:
                    break
            print(prog.poll())
            print(prog.returncode)
            print("read:", prog.stdout.readline())
    except KeyboardInterrupt:
        pass
    finally:
        print.kill()
