# -*- coding: utf-8 -*-
"""R2188 export repair: derive self_drive through the consistency
checker's own canonical recompute (single source of truth, F3 law),
restore the OSLoop tick row the checker requires, and stop the round
label from piling up inside the 'do' line."""
import io
import json
import os
import re
import sys

BASE = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_export_consistency as C  # noqa: E402 (canonical caliber)

EXPORT = C.P_EXPORT


def main():
    derived, state, export, pat = C.recompute()
    export["self_drive"] = derived

    tick = str(state.get("tick"))
    label = pat["tick_row_label"]
    results = export["results"]
    keep = [r for r in results
            if not (isinstance(r, list) and len(r) >= 2 and r[1] == label)]
    keep.insert(0, [tick, label,
                    "R2188 closed: counters machine-derived from"
                    " src/os/state.json and the queue/proposal faces"])
    export["results"] = keep

    do = export.get("do", "")
    do = re.sub(r"^(R\d+ )+", "", do).strip()
    export["do"] = "R2188 " + do

    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, ensure_ascii=False, indent=2))
        handle.write("\n")
    print("tick_row", keep[0][0], "self_drive", derived)


if __name__ == "__main__":
    main()