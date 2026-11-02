"""R2399 measurement: every src/os tool where the two readers disagree.

Read-only. Prints one line per disagreement so the seeded successor row is
measured rather than guessed.
"""

import glob
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import owner_table_parity as OTP  # noqa: E402
import owner_table_usage_wire as OUTW  # noqa: E402


def main():
    rows = []
    for path in sorted(glob.glob(os.path.join(BASE, "*.py"))):
        if os.path.basename(path).startswith("test_"):
            continue
        law = OTP.audit(path)
        wire = OUTW.audit(path)
        if law is None or wire is None:
            continue
        if law["verdict"] != wire["verdict"]:
            rows.append((os.path.basename(path), law["verdict"],
                         wire["verdict"],
                         ",".join(law["missing_in_parser"]) or "-"))
    print("DISAGREEMENTS count=%d" % len(rows))
    for name, law_verdict, wire_verdict, missing in rows:
        print("  %s law=%s wire=%s law_missing_in_parser=[%s]"
              % (name, law_verdict, wire_verdict, missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())