import sys
if __name__ == "__main__":
    print("start", file=sys.stderr, flush=True)
    for i in range(50):
        print(input())
