"""R2223 export refresh: merge this round payload into
docs/status-export.json and recompute the self_drive derived face with the
checker caliber (F3: derived counters come from the checker). The Chinese
payload lives in r2223_export_payload.json; this source stays pure ASCII.
"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
PAYLOAD = os.path.join(BASE, "r2223_export_payload.json")

if BASE not in sys.path:
    sys.path.insert(0, BASE)
import check_export_consistency as C  # noqa: E402

EXPORT_TS = "2026-10-29T03:05:00+08:00"


def main():
    with io.open(PAYLOAD, "rb") as handle:
        payload = json.loads(handle.read().decode("utf-8"))
    with io.open(EXPORT, "rb") as handle:
        data = json.loads(handle.read().decode("utf-8"))
    data["export_ts"] = EXPORT_TS
    data["do"] = payload["out_name"]
    data["ceo_face"] = dict(payload["ceo_face"])
    data["outs"].append([payload["out_name"], "on", payload["out_text"]])
    data["results"].append(["R2223", payload["result_text"]])
    label = C._load_patterns()["tick_row_label"]
    state = json.loads(io.open(C.P_STATE, "rb").read().decode("utf-8"))
    tick = str(state["tick"])
    hit = 0
    for row in data["results"]:
        if isinstance(row, list) and len(row) >= 2 and row[1] == label:
            row[0] = tick
            hit += 1
    if hit != 1:
        raise SystemExit("tick row count %d" % hit)
    out = json.dumps(data, ensure_ascii=False, indent=2)
    with io.open(EXPORT, "wb") as handle:
        handle.write((out + "\n").encode("utf-8"))
    derived, _state, _export, _pat = C.recompute()
    with io.open(EXPORT, "rb") as handle:
        fresh = json.loads(handle.read().decode("utf-8"))
    fresh["self_drive"] = dict(derived)
    with io.open(EXPORT, "wb") as handle:
        handle.write((json.dumps(fresh, ensure_ascii=False, indent=2)
                      + "\n").encode("utf-8"))
    print("export_ts=%s tick=%s outs=%d results=%d self_drive=%d"
          % (EXPORT_TS, tick, len(fresh["outs"]),
             len(fresh["results"]), len(fresh["self_drive"])))


if __name__ == "__main__":
    main()