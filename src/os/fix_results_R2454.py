# fix_results_R2454.py - keep exactly ONE tick row (the checker law) after the
# content refresh appended a second one, then republish through the wire.
import io
import json
import os
import sys

BASE = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT = os.path.join(BASE, "docs", "status-export.json")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import closeout_export_parity_dialect_wire as CEPD  # noqa: E402

LABEL = "OSLoop \u6267\u884c tick"


def main():
    with io.open(EXPORT, "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    rows = []
    kept = 0
    for row in data.get("results") or []:
        if len(row) == 2 and row[1] == LABEL:
            continue
        rows.append(row)
    rows.append(["2454", LABEL])
    data["results"] = rows
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    report, code = CEPD.publish(os.path.dirname(EXPORT), EXPORT, text)
    print("PUBLISH verdict=%s transport=%s bytes=%d reading=%s"
          % (report["verdict"], report["transport"], report["bytes"],
             report["reading"]))
    return 0 if code == 0 else 2


if __name__ == "__main__":
    sys.exit(main())