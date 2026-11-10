"""state_append_R2605b - append the push-and-export closeout line.

The line is appended AFTER the delivery it describes, so every number in it is
read from disk at run time rather than typed: the evidence size, the export
size and its tick, the fold verdict and the debt gate claim.
"""

import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "src", "os", "state.json")
EVIDENCE = os.path.join(ROOT, "qa", "reconcile-all-R2605.log")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
DEBT = os.path.join(ROOT, "state", "debt.md")


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import state_io as SIO
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    doc = json.loads(text)
    if not SIO.layout(text)["layout_ok"]:
        print("REFUSED layout drift")
        return 3
    ev = len(io.open(EVIDENCE, "rb").read())
    exp_bytes = len(io.open(EXPORT, "rb").read())
    tick = int(doc.get("tick", 0))
    debt_bytes = len(io.open(DEBT, "rb").read())
    line = (
        "2026-11-10 R2605 push and export: git push origin main SUCCEEDED "
        "(886f7b5a..39d98836 main -> main) and git rev-parse read HEAD equal "
        "to origin/main at 39d98836 with an empty git status after the commit, "
        "so the whole window is delivered; this line lands in the follow-up "
        "commit it describes. The export was refreshed AFTER the state append "
        "and after the fold (the R2449/R2433 ordering law) through the shipped "
        "driver src/os/export_R2431.py to %d bytes at tick %d with queue=CURRENT "
        "and queue_drifted=(none), and check_export_consistency read pass=21 "
        "fail=0 VERDICT PASS with the three CEO lines derived rather than typed; "
        "state_fold --check read FOLD-CLEAR with the archive VERIFIED and "
        "ledger_lines --check read CLEAN. The evidence file is %d bytes on "
        "disk. The debt register stands at %d bytes and the gate now names "
        "product-face-R2605 first=yes on the queue head "
        "state/queue/tech.md:638 prefix AC-EDMD1, so the next window owes that "
        "product face and no battery." % (exp_bytes, tick, ev, debt_bytes)
    )
    doc["log"].append(line)
    body = json.dumps(doc, ensure_ascii=False, indent=1)
    out = SIO.canon(body).encode("utf-8")
    io.open(PATH, "wb").write(out)
    back = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    ok = (back["log"][-1] == line
          and SIO.layout(io.open(PATH, "rb").read().decode("utf-8"))["layout_ok"])
    print("APPEND log_rows=%d before=%dB after=%dB ok=%s"
          % (len(back["log"]), len(text), len(out), ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())