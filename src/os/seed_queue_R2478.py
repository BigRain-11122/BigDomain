"""R2478 seed: append ONE tech queue row with criteria pinned BEFORE the
code, for the per-suite timeout cap defect this window measured (the third
casualty of the flat 300s cap: R2393 leg 3, R2466 leg 2, R2478 leg 1).

Writes only state/queue/tech.md, appends one line, utf-8 LF, and reads the
file back to prove the row landed exactly once.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BASE)
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

ROW = (
    "- [ ] P2 tech seed (R2478, from this window own measured limit): "
    "`src/os/runner_suite_timeout_cap.py` - MEASURED this window the battery "
    "lost ledger-apimarket-reportclaims to its flat 300s per-suite cap at "
    "300.1s (leg 1 red) while the same suite passes 8/8 alone in 198s, and "
    "the shipped headroom reader already reads BAND at 232.2s / 268.1s / "
    "300.1s for three ledger suites, so the cap has no load headroom left and "
    "R2393 leg 3 and R2466 leg 2 are the same casualty. The fix must land "
    "with these criteria pinned BEFORE the code, because the deployed "
    "os-runner-suite-timeout-headroom fixture pins the 300s default as a "
    "reading and a bare cap raise would silently make that instrument lie. "
    "AC-RSC1 the runner carries exactly ONE named cap constant and the "
    "headroom reader's default cap is READ from that source, proved by "
    "patching the constant in a fixture world and watching the default move "
    "with no second literal anywhere in src. "
    "AC-RSC2 a declared per-suite override is honoured and every undeclared "
    "suite keeps the global cap, proved through the runner's own run_cmd "
    "seam with a fixture suite that outlives a tiny cap and an undeclared "
    "neighbour that does not. "
    "AC-RSC3 the deployed reading does not regress: all six AC-RTH criteria "
    "stay green unchanged, including the 194.9s BAND-HIT fixture, so the fix "
    "cannot buy headroom by widening the instrument. "
    "AC-RSC4 at the repaired cap the three measured slow suites read "
    "COMFORTABLE from this window own evidence while a synthetic outlier "
    "still reads BAND, so the band keeps naming real risk. "
    "AC-RSC5 the timeout still records ONE failed suite carrying its child "
    "lines and never aborts the whole run, and the summary line states which "
    "cap actually ran so an operator can read it without the source. "
    "AC-RSC6 hygiene and registration: pure ASCII stdlib module, no clock, "
    "no network, exactly one new registry row runner-suite-timeout-cap(6), "
    "and the runner argument-guard plus timeout-headroom suites stay green."
)


def main():
    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    before = len(text.splitlines())
    if "runner_suite_timeout_cap" in text:
        print("REFUSED already seeded")
        return 2
    body = text
    if not body.endswith("\n"):
        body += "\n"
    body += ROW + "\n"
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    back = open(QUEUE, "rb").read().decode("utf-8")
    after = len(back.splitlines())
    ok = (back.count("runner_suite_timeout_cap") == 1 and after == before + 1
          and back.endswith("\n") and "\r" not in back)
    print("SEED lines %d->%d once=%s lf_only=%s"
          % (before, after, back.count("runner_suite_timeout_cap") == 1,
             "\r" not in back))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())