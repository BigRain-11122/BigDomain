"""R2212 self_drive refresh after the duplicate cleanup: recompute the
canonical caliber against the current state and flush it into the export."""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src", "os"))

import check_export_consistency as C   # noqa: E402

P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")


def main():
    derived, state, export, pat = C.recompute()
    export["self_drive"].update(derived)
    label = pat["tick_row_label"]
    for row in export["results"]:
        if isinstance(row, list) and len(row) >= 2 and row[1] == label:
            row[0] = str(state["tick"])
    with io.open(P_EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, indent=1, ensure_ascii=False)
                     + "\n")
    print("self_drive flushed: %s" % json.dumps(derived, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())