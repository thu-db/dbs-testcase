class PointFailed(Exception):
    pass


class CheckFailed(Exception):
    def __init__(self, msg, ans, out):
        self.msg = msg
        self.ans = ans
        self.out = out

    def __repr__(self) -> str:
        return f"CheckFailed: {self.msg}, but expected is [{self.ans}] and output is [{self.out}]"


class TimeLimitExceeded(Exception):
    pass


class InitTimeout(Exception):
    pass


def assert_eq(msg, ans, out):
    if ans != out:
        raise CheckFailed(msg, ans, out)
