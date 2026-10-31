"""R2289 export refresh: rewrite the CEO-visible face from measured state.

F3 law: every field below is derived from this window's actual readings (the
shipped retry evidence file, the suite result and the live history reading),
never typed twice. The Chinese face text lives in a JSON data file, so this
script itself stays pure ASCII. The self_drive block is recomputed by
check_export_consistency.recompute() rather than transcribed.
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
sys.path.insert(0, HERE)

import check_export_consistency as consistency  # noqa: E402

TICK = "2289"
EVIDENCE = os.path.join(ROOT, "qa", "reconcile-all-R2289-retry.log")


def main(argv):
    data_path = argv[0]
    execute = "--execute" in argv
    patch = json.loads(io.open(data_path, encoding="utf-8").read())
    data = json.loads(io.open(EXPORT, encoding="utf-8").read())
    derived, state, _old, _pat = consistency.recompute()
    ev_bytes = os.path.getsize(EVIDENCE)

    data["export_ts"] = patch["export_ts"]
    data["do"] = patch["do"]
    face = data["ceo_face"]
    face["current"] = patch["current"]
    face["latest_artifact"] = patch["latest_artifact"].replace(
        "@EVIDENCE_BYTES@", "%dB" % ev_bytes)
    face["last_artifact"] = face["latest_artifact"]
    face["next_milestone"] = patch["next_milestone"]
    face["next_milestone_due"] = patch["next_milestone_due"]
    data["self_drive"] = derived

    label, text = patch["results"]
    kept = []
    for row in data["results"]:
        if not (isinstance(row, list) and len(row) == 2):
            kept.append(row)
            continue
        name = row[0]
        if name.isdigit():
            row[0] = TICK
            kept.append(row)
            continue
        if name in patch["drop_labels"]:
            continue
        kept.append(row)
    data["results"] = kept + [[label, text]]

    body = json.dumps(data, ensure_ascii=False, sort_keys=False) + "\n"
    raw = body.encode("utf-8")
    print("EXPORT evidence=%dB results=%d export_ts=%s"
          % (ev_bytes, len(data["results"]), data["export_ts"]))
    print("EXPORT self_drive=%r" % (derived,))
    if not execute:
        print("EXPORT mode=dry-run bytes=%d" % len(raw))
        return 0
    with io.open(EXPORT, "wb") as handle:
        handle.write(raw)
    with io.open(EXPORT, "rb") as handle:
        back = handle.read()
    if back != raw:
        raise SystemExit("REFUSE: export read-back differs")
    check = json.loads(back.decode("utf-8"))
    if check["export_ts"] != patch["export_ts"] or check["results"][-1][0] != label:
        raise SystemExit("REFUSE: export payload does not round-trip")
    print("EXPORT mode=execute bytes=%d readback=ok" % len(back))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))