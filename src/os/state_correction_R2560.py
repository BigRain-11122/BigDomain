"""R2560 correction append: state what the interrupted attempt had committed.

Reading HEAD showed that commit 79a51c5b already restored the matrix document
provenance line at its birth site and already committed the red leg, so the
window log line that called that repair this window own work overstated it.
The correction is APPENDED rather than edited into the earlier line.
"""

import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINE = (
    "2026-11-08 R2560 MEASURED CORRECTION, appended rather than edited into "
    "the row above, because reading HEAD is what surfaced it: commit 79a51c5b "
    "already carries the provenance repair (its subject reads 'Restore the "
    "matrix doc provenance line at its birth site (R2559 regenerated without "
    "--stamp-from, so doc_faces read None and two suites went red); generator "
    "--stamp-from, --check byte-identical, both suites 6/6 alone, red leg "
    "kept'), so THE BIRTH-SITE REPAIR AND THE RED LEG LANDED IN THAT COMMIT "
    "FROM THE INTERRUPTED ATTEMPT, NOT IN THIS WINDOW. What this window "
    "actually did to the document is RE-DERIVE it from its own green leg: "
    "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from "
    "qa/reconcile-all-R2560.log (59313 bytes, 609 suites / 4630 criteria, "
    "green=609/609 self-describing) with --check reading byte-identical at "
    "rc=0, which is why the diff touches 1096 timing cells while the header "
    "keeps both its generation command and its --stamp-from line. The dry-run "
    "FAIL at equal byte counts (59313 vs 59313) is the honest signature of "
    "that difference in CONTENT rather than a size drift. The window also "
    "DELETED the untracked export driver the interrupted attempt left behind "
    "(src/os/export_refresh_R2560.py) instead of reusing it, because that "
    "driver hardcoded a red-leg recount and a retry narrative this window did "
    "not perform; the export was refreshed by src/os/export_R2560.py from "
    "measured values. Two stray files created by my own mistyped flags "
    "(--only, --filter) were deleted before the commit rather than staged."
)


def main():
    raw = io.open(PATH, "rb").read()
    doc = json.loads(raw.decode("utf-8"))
    if json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8") != raw:
        print("REFUSE: round-trip not byte-identical")
        return 2
    if doc["tick"] != 2560:
        print("REFUSE: tick is %s" % doc["tick"])
        return 2
    if any("R2560 MEASURED CORRECTION" in x for x in doc["log"]):
        print("REFUSE: correction already present")
        return 2
    doc["log"].append(LINE)
    out = json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8")
    io.open(PATH, "wb").write(out)
    back = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    ok = back["log"][-1].startswith("2026-11-08 R2560 MEASURED CORRECTION")
    print("STATE log_lines=%d bytes=%d ok=%s" % (len(back["log"]), len(out), ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())