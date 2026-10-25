"""R2118 preview writer: render the settlement report (with the new
open-questions section) from the deterministic demo world into
preview/apimarket-report-questions.{html,json}.

The world is seeded by apimarket_report.seed_demo with pinned clocks
and the Q&A rows are stamped from one fixed instant, so a second run
replays byte-identical files.
"""

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

import apimarket as A         # noqa: E402
import apimarket_report as R  # noqa: E402


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-preview-questions-")
    db = os.path.join(tmp, "ledger.db")
    out_html = os.path.join(BASE, "preview",
                            "apimarket-report-questions.html")
    out_json = os.path.join(BASE, "preview",
                            "apimarket-report-questions.json")
    try:
        led, mtr, dk, am = R.build_stack(db)
        try:
            world = R.seed_demo(am, led, dk)
            listing = world["listings"]
            original = A._now_utc
            A._now_utc = lambda: "2026-10-20T12:00:00Z"
            try:
                q1 = am.ask_question(
                    "usr:bob", listing[0],
                    "does the risk scan support batch calls?")
                am.ask_question(
                    "usr:carol", listing[0],
                    "is there a sample response payload?")
                am.ask_question(
                    "usr:erin", listing[2],
                    "how fresh is the chart render cache?")
                am.answer_question(
                    "usr:dana", q1["question_id"],
                    "yes, up to 500 calls per batch")
            finally:
                A._now_utc = original
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