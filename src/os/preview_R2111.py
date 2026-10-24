"""R2111 preview writer: render the settlement report (with the new
Refund register section) from the deterministic demo world into
preview/apimarket-report-refunds.{html,json}.

The world is seeded by apimarket_report.seed_demo with pinned clocks,
so the artifacts are reproducible: a second run replays byte-identical
files (the suite's AC-AMRR7 determinism face proves the same law).
"""

import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
LEDGER = os.path.join(BASE, "src", "sandbox", "ledger")
LOBBY = os.path.join(BASE, "src", "sandbox", "lobby")
for path in (LEDGER, LOBBY):
    if path not in sys.path:
        sys.path.insert(0, path)

import apimarket_report as R  # noqa: E402


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-preview-refunds-")
    db = os.path.join(tmp, "ledger.db")
    out_html = os.path.join(BASE, "preview", "apimarket-report-refunds.html")
    out_json = os.path.join(BASE, "preview", "apimarket-report-refunds.json")
    try:
        led, mtr, dk, am = R.build_stack(db)
        try:
            R.seed_demo(am, led, dk)
        finally:
            am.close()
            dk.close()
            mtr.close()
            led.close()
        R.main(["--db", db, "--out", out_html, "--json-out", out_json])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("PASS preview %s (%d bytes) + %s (%d bytes)"
          % (os.path.relpath(out_html, BASE),
             os.path.getsize(out_html),
             os.path.relpath(out_json, BASE),
             os.path.getsize(out_json)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())