# state_closeout_R2094.py - closeout writer for round R2094.
# Applies the state tick + two log lines, flips the claimed explore
# row to done and prepends the backlog done row. All CJK payloads
# live in the UTF-8 data file closeout_R2094.json (encoding law);
# this source is pure ASCII.
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(ROOT, ".codely-cli", "tmp", "closeout_R2094.json")
STATE = os.path.join(ROOT, "src", "os", "state.json")
QUEUE = os.path.join(ROOT, "state", "queue", "explore.md")
BOARD = os.path.join(ROOT, "src", "os", "backlog.md")


def read(path):
    return io.open(path, encoding="utf-8").read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def main():
    data = json.loads(read(DATA))

    st = json.loads(read(STATE))
    assert st["tick"] == 2093, "unexpected tick %r" % st["tick"]
    st["tick"] = 2094
    assert "R2094" not in st["log"][-1]
    st["log"].append(data["log_round"])
    st["log"].append(data["log_tokens"])
    write(STATE, json.dumps(st, ensure_ascii=False, indent=2) + "\n")

    q = read(QUEUE)
    head = "- [ ] P3 explore \u81ea\u8865\u79cd\u5e76\u540c\u7a97\u8ba4\u9886\uff08R2094\uff09"
    idx = q.find(head)
    assert idx >= 0, "claimed explore row not found"
    end = q.find("\n", idx)
    line = q[idx:end]
    q = (q[:idx] + "- [x]" + line[5:] + data["explore_done"]
         + q[end:])
    write(QUEUE, q)

    b = read(BOARD)
    marker = "- [x] P3 explore \u81ea\u8865\u79cd\u5e76\u540c\u7a97\u8ba4\u9886\uff08R2093\uff09"
    pos = b.find(marker)
    assert pos > 0, "R2093 backlog row not found"
    b = b[:pos] + data["backlog_row"] + b[pos:]
    write(BOARD, b)
    print("closeout written tick=2094")
    print("state bytes=%d" % os.path.getsize(STATE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())