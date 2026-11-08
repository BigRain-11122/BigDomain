"""Append the R2579 push/export line to src/os/state.json in place."""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-08 R2579 push and export: git push origin main SUCCEEDED this window (a4da456a..d1ae5944 main -> main) and git rev-parse read HEAD equal to origin/main at d1ae5944 with an empty git status after the commit, so the whole window is delivered and nothing is left staged; this line lands in the follow-up commit it describes. The export was refreshed AFTER the state appends and after both folds through this round own driver src/os/export_R2579.py to 395254 bytes at tick 2579 with queue=CURRENT and queue_drifted=(none), and check_export_consistency read pass=21 fail=0 VERDICT PASS with the three CEO lines derived rather than typed; state_fold --check also read FOLD-CLEAR at 73240B against the 78500B gate with margin 5260 and 67 log lines. The debt gate now names reconcile-battery-R2579 first=yes at the pre-registered 619 suites / 4690 criteria, so the next window owes that battery on this committed tree before any further product byte, and the product face behind it is tech line 615 prefix AC-PNAM1. logs/ is gitignored in this repository, so the fold archive copy stays on disk as evidence without being staged.",
]


def main():
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    data = json.loads(text)
    if json.dumps(data, ensure_ascii=False, indent=1) != text:
        sys.stdout.write("E_APPEND_ROUNDTRIP: layout is not indent=1\n")
        return 2
    data["log"].extend(LINES)
    out = json.dumps(data, ensure_ascii=False, indent=1)
    io.open(PATH, "wb").write(out.encode("utf-8"))
    back = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    sys.stdout.write("APPENDED bytes %d -> %d log_lines=%d ok=%s\n" % (
        len(raw), len(out.encode("utf-8")), len(back["log"]),
        back["log"][-1].startswith("2026-11-08 R2579 push and export:")))
    return 0


if __name__ == "__main__":
    sys.exit(main())