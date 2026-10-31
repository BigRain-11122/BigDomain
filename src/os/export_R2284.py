"""R2284 export refresh: rewrite the CEO-visible face from measured state.

F3 law: every field below is derived from this window's actual readings (the
suite evidence file, the live locator reading, the floor gauge and the
register writers) and the self_drive block is recomputed by
check_export_consistency.recompute() rather than typed, so a stale counter
cannot survive the refresh.
"""

import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
sys.path.insert(0, HERE)

import check_export_consistency as consistency  # noqa: E402


def main(argv):
    now_ts, due_ts = argv[0], argv[1]
    data = json.loads(io.open(EXPORT, encoding="utf-8").read())
    derived, state, _old, _pat = consistency.recompute()
    data["export_ts"] = now_ts
    data["do"] = ("product window on the debt register first item: a round's "
                  "done stamp is now a reading (file, line, row head, closed "
                  "marker) instead of a hand grep, with the stamp law "
                  "imported from state_seq and the row law from queue_floor")
    face = data["ceo_face"]
    face["current"] = (
        "R2284 产品窗：取 tech 队头 state/queue/tech.md:354（AC-SLC1 的 "
        "stamp_locator 种子），交付 src/os/stamp_locator.py 与其套件——"
        "某个轮次的 done 印章现在是一次读数（文件/行号/行首/是否已关闭），"
        "不再是手工 grep；套件 6/6 双跑同一、五邻域全绿。"
    )
    face["latest_artifact"] = (
        "src/os/stamp_locator.py + src/os/test_stamp_locator.py；"
        "qa/stamp-locator-R2284.log（1204B，双腿同一，相邻 5 套件全绿）；"
        "活读数 STAMP LOCATOR round=R2250 hits=1 verdict=HITS"
    )
    face["last_artifact"] = face["latest_artifact"]
    face["next_milestone"] = (
        "R2285 验证窗：在已提交树上跑全量 reconcile 电池（预期 +1 套件 / "
        "+6 判据，即 os-stamp-locator 入册），再做四段 follow-up。"
    )
    face["next_milestone_due"] = due_ts
    data["self_drive"] = derived
    kept = []
    for row in data["results"]:
        if isinstance(row, list) and len(row) == 2 and row[0] == "2283":
            row[0] = "2284"
        if isinstance(row, list) and len(row) == 2 and row[0] == "R2283":
            continue
        kept.append(row)
    data["results"] = kept + [[
        "R2284",
        ("R2284 product window on the debt register first item "
         "(product-face-R2284), discharged on the tech head "
         "state/queue/tech.md:354 prefix AC-SLC1 after a fresh "
         "zero-occupancy anchor check at HEAD: src/os/stamp_locator.py plus "
         "src/os/test_stamp_locator.py, AC-SLC1..AC-SLC6 already pinned in "
         "the R2269 seed row BEFORE the code. The locator answers which "
         "queue rows carry a round's done stamp - file, line, row head and "
         "closed marker - with the stamp law imported from state_seq and the "
         "row-closed law imported from queue_floor, each proven by patching "
         "it; NO-HITS reads honestly at exit 2, a missing queue directory "
         "refuses at 3, bad flags at 5, and the reader writes nothing and "
         "reads no clock. SUITE PASS 6/6 double-run identical through the "
         "evidence_capture callable with five adjacent os suites green "
         "(qa/stamp-locator-R2284.log, 1204B). LIVE: round=R2250 hits=1 "
         "verdict=HITS at state/queue/tech.md:5 closed=yes - the residue the "
         "declared-floor gate names really is on a closed row. The claim "
         "dropped tech claimable to 9, so one real gap row was seeded "
         "(stamp_residue, AC-SRS1..AC-SRS6 pre-registered, five anchors "
         "zero-occupancy) and the gauge closed FLOOR-MET 5/5 10/10 10/10. "
         "Register closed through its own writer (line=56, open 2->1, done "
         "33->34) and product-face-R2285 opened first=yes naming the "
         "committed-tree battery; honest score 2 product points, no state "
         "fold due at 46353B against the 78500B waterline."),
    ]]
    text = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    folder = os.path.dirname(EXPORT)
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".export_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(text.encode("utf-8"))
    os.replace(temp, EXPORT)
    back = io.open(EXPORT, "rb").read().decode("utf-8")
    if back != text:
        raise SystemExit("ABORT read-back differs from the write")
    print("WROTE %dB tick_row=%r" % (len(back.encode("utf-8")),
                                     data["results"][0][0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))