"""Re-derive the export's machine fields from the checker's own recompute (R2395).

The closeout wrote authored lines (do, ceo_face, outs) but copied no derived
counter because check_export_consistency.recompute returns a TUPLE of
(drive, state, derived_export, labels) rather than the counter dict, so the
copy loop silently matched nothing and the checker read W=23 against a
stored 18. This script takes the derived sections verbatim from that same
recompute - no digit is typed here - and keeps the authored CEO lines.

Stdlib only, ASCII source, no network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402

EXPORT = os.path.join(REPO, "docs", "status-export.json")


def main(argv):
    drive, _state, derived, _labels = CEC.recompute()
    with io.open(EXPORT, "r", encoding="utf-8", newline="") as handle:
        export = json.load(handle)
    for key in ("depts", "results", "queue"):
        if key in derived:
            export[key] = derived[key]
    export["self_drive"] = drive
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, indent=2, ensure_ascii=False) + "\n")
    print("export re-derived: drive=%r sections=%r"
          % (dict((k, drive.get(k)) for k in
                  ("log_lines_in_window", "queue_tech_open",
                   "substantive_non_idle_mention_lines")),
             sorted(derived)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))