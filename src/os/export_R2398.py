"""R2398 export results/outs row: append this round's result face and artifact.

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
    "2026-11-03 R2398 product face: CLAIMED state/queue/tech.md:458 prefix "
    "AC-DWPP1 (declaration_writer_dialect_preservation), criteria pinned in "
    "that row at R2389 before any code. SHIPPED "
    "src/os/declaration_writer_dialect_preservation.py plus its six-criteria "
    "suite: a writer that actually CHANGES a declaration now keeps that "
    "declaration's own line endings instead of converting every line to LF - "
    "the dialect is the shared law's answer at CALL time, an LF declaration "
    "gets exactly today's bytes, a CRLF declaration is spliced on "
    "universal-newline text and re-rendered as CRLF so every untouched line is "
    "byte-identical, and a MIXED declaration refuses rather than having a "
    "transport chosen for it. All four writers (single append, batch append, "
    "head renew, entry retire) ask it at one call site each. SUITE PASS 6/6 "
    "twice with an identical criterion digest plus three adjacent suites green "
    "(qa/declaration-writer-dialect-preservation-R2398.log, 1354B, legs=2 "
    "identical=True adjacent=3 fails=0), wired "
    "os-declaration-writer-dialect-preservation(6) so the registry reads 524 "
    "suites / 4120 criteria. Two defects measured and repaired at birth: a "
    "CRLF declaration could not be appended to at all before this window "
    "(compose's pinned closer is an LF layout, so it read E_RTA_BAD_SHAPE), and "
    "the batch writer shipped before the NOOP law and asked no comparison at "
    "all. LIVE: the real 68838B declaration reads dialect=LF preserved=yes and "
    "the real head renew reads NOOP with nothing written. No battery ran: "
    "reconcile-battery-R2394 stays OPEN at 524 suites / 4120 criteria.")

OUTS = ("src/os/declaration_writer_dialect_preservation.py plus its "
        "six-criteria suite (qa/declaration-writer-dialect-preservation"
        "-R2398.log, qa/declaration-writer-dialect-preservation-live"
        "-R2398.log)")


def main():
    data = json.load(io.open(EXPORT, encoding="utf-8"))
    rows = data.get("results") or []
    if rows and str(rows[0][0]) == "2398":
        sys.stdout.write("E_RESULTS: a 2398 row already exists\n")
        return 2
    rows.insert(0, ["2398", RESULT])
    data["results"] = rows
    outs = data.get("outs") or []
    if not outs or outs[0] != OUTS:
        outs.insert(0, OUTS)
    data["outs"] = outs
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    handle, tmp = tempfile.mkstemp(dir=os.path.dirname(EXPORT),
                                   prefix=".dwpp-", suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as sink:
        sink.write(text)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(tmp, EXPORT)
    back = json.load(io.open(EXPORT, encoding="utf-8"))
    if str(back["results"][0][0]) != "2398" or back["outs"][0] != OUTS:
        sys.stdout.write("E_RESULTS: read-back differs\n")
        return 2
    sys.stdout.write("RESULTS rows=%d outs=%d bytes=%d\n"
                     % (len(back["results"]), len(back["outs"]),
                        os.path.getsize(EXPORT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())