"""R2140 export refresh: merge the round payload into
docs/status-export.json (F3: derived counters come from the checker).

ASCII source, stdlib only, no network.
"""

import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
PAYLOAD = os.path.join(BASE, "r2140_export_payload.json")


def main():
    with io.open(PAYLOAD, "rb") as handle:
        pay = json.loads(handle.read().decode("utf-8"))
    with io.open(EXPORT, "rb") as handle:
        raw = handle.read().decode("utf-8")
    data = json.loads(raw)
    data["export_ts"] = pay["export_ts"]
    data["ceo_face"].update(pay["ceo_face"])
    data["outs"].append(pay["outs_entry"])
    data["results"].append(pay["results_entry"])
    data["self_drive"].update(pay["self_drive"])
    out = json.dumps(data, ensure_ascii=False, indent=2)
    with io.open(EXPORT, "wb") as handle:
        handle.write((out + "\n").encode("utf-8"))
    print("export_ts=%s outs=%d results=%d"
          % (data["export_ts"], len(data["outs"]), len(data["results"])))


if __name__ == "__main__":
    main()