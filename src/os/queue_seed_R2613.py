"""R2613 seed: ONE tech row measuring the birth site the R2612 red named.

MEASURED at R2612 on this tree: the only failing suite in the owed battery
was ledger-apimarket-reportclaims exit=124 pass-lines=0 criteria=8 600.2s,
i.e. the per-suite cap, not an assertion. A bounded 70s re-probe printed
AC-AMCLM1..AC-AMCLM7 PASS in under a second and then stopped inside
AC-AMCLM8 check_regression, which nests three child suites in sequence.

MEASURED at R2613 by running each nested child standalone on the SAME
loaded tree (the owed battery leg was live): test_apimarket_report.py 11.1s
rc=0, test_apimarket_report_json.py 16.4s rc=0, and
test_apimarket_report_refundregister.py did not finish inside the first
minute. All three children are ALREADY battery rows of their own
(ledger-apimarket-report 9, ledger-apimarket-reportjson 8,
ledger-apimarket-refundregister 8 with a declared 900s override), so the
nesting re-runs work the battery already pays for.

Every number printed here is read from the files on disk.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
ANCHOR = "- [ ] P2 tech seed (R2608,"

SEED = (
    "- [ ] P2 tech seed (R2613, from the battery red R2612 named): "
    "`src/sandbox/ledger/test_apimarket_report_claims.py` AC-AMCLM8 nested a "
    "heavyweight child - MEASURED this window on the loaded tree: "
    "check_regression spawns test_apimarket_report.py (11.1s rc=0), "
    "test_apimarket_report_json.py (16.4s rc=0) and "
    "test_apimarket_report_refundregister.py (still running past 60s), and "
    "all THREE are already battery rows of their own, so the nesting re-runs "
    "work the battery already pays for and the parent row lost the 600s cap "
    "at R2612 (exit=124 pass-lines=0 600.2s). Criteria AC-AMCF1..AC-AMCF6 "
    "pinned HERE BEFORE any code: AC-AMCF1 the nesting is bounded - the "
    "regression check spawns ONLY children measured under a declared cheap "
    "bound and NEVER the heavy refund-register suite, asserted by reading "
    "this suite own source at call time; AC-AMCF2 the heavy coverage MOVED, "
    "it was not dropped - the same check reads the SHIPPED registry at call "
    "time and requires a row labelled `ledger-apimarket-refundregister` "
    "pointing at that file with the file on disk; AC-AMCF3 the two cheap "
    "children still RUN for real and their return codes are still asserted "
    "0 from subprocess output rather than cached; AC-AMCF4 this suite own "
    "wiring is unchanged - `ledger-apimarket-reportclaims` still registered "
    "at this file with 8 criteria; AC-AMCF5 fail-closed - an unreadable "
    "registry or a missing heavy row makes AC-AMCLM8 FAIL naming the reason, "
    "proved on a doctored registry world, never a silent pass; AC-AMCF6 the "
    "suite measures its OWN wall time, prints it and asserts it stays under "
    "a declared bound well inside the 600s cap, so the starvation cannot "
    "come back unnoticed.\n"
)


def main():
    text = io.open(QUEUE, "r", encoding="utf-8").read()
    if "AC-AMCF1" in text:
        raise SystemExit("already seeded")
    lines = text.splitlines(True)
    at = None
    for index, line in enumerate(lines):
        if line.startswith(ANCHOR):
            at = index
            break
    if at is None:
        raise SystemExit("anchor row not found: %s" % ANCHOR[:40])
    before = len(text.encode("utf-8"))
    lines.insert(at, SEED)
    out = "".join(lines)
    after = len(out.encode("utf-8"))
    io.open(QUEUE, "w", encoding="utf-8", newline="").write(out)
    back = io.open(QUEUE, "r", encoding="utf-8").read()
    print("inserted at line %d, bytes %d -> %d, readback_ok=%s"
          % (at + 1, before, after, "AC-AMCF1" in back))
    return 0


if __name__ == "__main__":
    sys.exit(main())