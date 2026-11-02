"""R2397 export results/outs row: append this round's result face and artifact.

Read-only except for docs/status-export.json, written once atomically.
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(REPO, "docs", "status-export.json")

RESULT = (
    "2026-11-03 R2397 product face: CLAIMED state/queue/tech.md:457 prefix "
    "AC-RWPC1 (review_window_guard_parity_consumer_wire), criteria pinned in "
    "that row at R2387 before any code. SHIPPED "
    "src/os/review_window_guard_parity_consumer_wire.py plus its six-criteria "
    "suite: the blind-agreement reading is asked at CALL time from the path "
    "that ages entries, a split refuses E_RWPC_SPLIT naming both faces' codes, "
    "a blind agreement refuses E_RWPC_UNKNOWN naming the ignorant side(s), and "
    "an informed agreement refuses nothing so exempt_review "
    "--window-from-declaration reads the same window and the same report as "
    "before. SUITE PASS 6/6 twice identical plus three adjacent suites green "
    "(qa/review-window-guard-parity-consumer-wire-R2397.log, 3005B), wired "
    "os-review-window-guard-parity-consumer-wire(6) so the registry reads 523 "
    "suites / 4114 criteria. LIVE: the real tree reads WINDOW-CLEAN "
    "parity=PARITY-AGREES window=100 and a fixture neither face can read "
    "refuses E_RWPC_UNKNOWN at exit 2. No battery ran: "
    "reconcile-battery-R2394 stays OPEN at 523 suites / 4114 criteria.")

OUTS = ("src/os/review_window_guard_parity_consumer_wire.py plus its "
        "six-criteria suite (qa/review-window-guard-parity-consumer-wire"
        "-R2397.log, qa/review-window-guard-parity-consumer-wire-live"
        "-R2397.log)")


def main():
    data = json.load(io.open(EXPORT, encoding="utf-8"))
    rows = data.get("results") or []
    if rows and str(rows[0][0]) == "2397":
        sys.stdout.write("E_RESULTS: a 2397 row already exists\n")
        return 2
    rows.insert(0, ["2397", RESULT])
    data["results"] = rows
    outs = data.get("outs") or []
    if not outs or outs[0] != OUTS:
        outs.insert(0, OUTS)
    data["outs"] = outs
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    handle, tmp = tempfile.mkstemp(dir=os.path.dirname(EXPORT),
                                   prefix=".rwpc-", suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as sink:
        sink.write(text)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(tmp, EXPORT)
    back = json.load(io.open(EXPORT, encoding="utf-8"))
    if str(back["results"][0][0]) != "2397" or back["outs"][0] != OUTS:
        sys.stdout.write("E_RESULTS: read-back differs\n")
        return 2
    sys.stdout.write("RESULTS rows=%d outs=%d bytes=%d\n"
                     % (len(back["results"]), len(back["outs"]),
                        os.path.getsize(EXPORT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())