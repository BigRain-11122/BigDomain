"""closeout_R2329 - the accepted-stamp declaration learns to shrink.

Claims tech queue line 382 (AC-SEPR1..AC-SEPR6, the R2307 seed row, criteria
pinned inside that row BEFORE the code), runs the ritual once through
evidence_capture and prints the live reading on the real declaration.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import evidence_capture as EVC  # noqa: E402
import stamp_exempt_prune as SPR  # noqa: E402

ROUND = "R2329"
SUITE = "src/os/test_stamp_exempt_prune.py"
EVIDENCE = "qa/stamp-exempt-prune-R2329.log"
ADJACENT = [
    "src/os/test_stamp_exempt_append.py",
    "src/os/test_stamp_exempt_review.py",
    "src/os/test_queue_done_stamp.py",
    "src/os/test_queue_done_stamp_exempt.py",
]


def main():
    report = EVC.capture(ROOT, ROUND, SUITE, adjacent=ADJACENT,
                         evidence=EVIDENCE)
    sys.stdout.write(report["verdict"] + "\n")
    sys.stdout.write("evidence=%s bytes=%d identical=%s\n"
                     % (report["evidence"], report["bytes"],
                        report["identical"]))
    for row in report["adjacent"]:
        sys.stdout.write("adjacent %s rc=%d %s\n"
                         % (row["name"], row["rc"], row["suite_line"]))
    live = SPR.plan(ROOT, 2329, execute=False)
    sys.stdout.write(SPR.one_line(live) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())