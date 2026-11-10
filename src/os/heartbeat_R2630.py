"""heartbeat_R2630 - append this round own line to the heartbeat face."""

import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(BASE, "heartbeat.txt")

LINE = (
    "2026-11-11 07:0x R2630 product window: suite-matrix table membership "
    "decided by the separator a header carries, not by a digit in its first "
    "cell (malformed non-numeric row now -1 instead of -643), suite 6/6 twice "
    "plus six adjacent matrix suites, registry 644/4840, matrix doc 65817B "
    "byte-identical, board 653 closed and AC-EDMJ1 seeded, next = "
    "reconcile-battery-R2630 at 644/4840\n"
)


def main():
    raw = open(P, "rb").read()
    text = raw.decode("utf-8")
    if not text.endswith("\n"):
        text += "\n"
    text += LINE
    with open(P, "wb") as fh:
        fh.write(text.encode("utf-8"))
    back = open(P, "rb").read()
    print("heartbeat bytes", len(back), "lines", back.count(b"\n"),
          "crlf", back.count(b"\r\n"), "appended", LINE.encode("utf-8") in back)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
