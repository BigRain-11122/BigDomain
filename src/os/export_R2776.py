"""export_R2776 - refresh docs/status-export.json for the R2776 window.

The shipped generic driver supplies the derived blocks; this file adds only
the three CEO lines, composed from numbers THIS window measured: the live
battery R2775 carried exactly one red suite, reconcile-daily-census, whose
cd7 read exit=2 drift. The drifting artifact was a UTF-16LE+BOM/CRLF evidence
log left by PowerShell redirection; it was archived byte-for-byte and
re-encoded to UTF-8/LF with the text proven identical, after which
census --check reads flags=0 DRIFT-CLEAN and the suite reads 8/8 live.
"""

import datetime
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import export_driver_queue_face as EDQF  # noqa: E402
import check_export_consistency as cec  # noqa: E402
from export_R2431 import tick_label  # noqa: E402

EXPORT = os.path.join(REPO, "docs", "status-export.json")
STATE = os.path.join(BASE, "state.json")
TZ = datetime.timezone(datetime.timedelta(hours=8))
STAMP = datetime.datetime.now(TZ).replace(microsecond=0).isoformat()

CURRENT = "R2776 \u4ea7\u54c1\u5207\u7247\uff1a\u6d3b\u7535\u6c60 R2775 \u91cc\u552f\u4e00\u7684\u7ea2\u706f\u5957\u4ef6 reconcile-daily-census \u4fee\u5728\u51fa\u751f\u5730\u2014\u2014qa/index-newest-band-R2775.log \u5b9e\u4e3a UTF-16LE+BOM/CRLF \u65b9\u8a00\uff08PowerShell \u91cd\u5b9a\u5411\u9ed8\u8ba4\u53e3\u5f84\uff09\uff0c\u5f52\u6863\u539f\u5b57\u8282\u540e\u8f6c UTF-8/LF\uff081032B\u2192509B\u00b7\u6587\u672c\u9010\u5b57\u7b49\u4ef7\uff09\uff0ccensus --check flags=0 DRIFT-CLEAN\uff0c\u5957\u4ef6 8/8\uff08cd7 exit=0 \u771f\u8dd1\u6d3b\u6811\uff09"
LATEST = "qa/index-newest-band-R2775.log\uff08\u65b9\u8a00\u4fee\u590d\u540e 509B\u00b7UTF-8/LF\uff09\uff0blogs/qa-encoding-preop-R2775/index-newest-band-R2775.log.utf16le\uff08\u539f\u5b57\u8282 1032B \u7559\u8bc1\uff09"
NEXT = "48 \u5c0f\u65f6\u5185\uff1a\u6309\u81ea\u8eab\u95ed\u5408 BATTERY rc= \u884c\u91c7\u7eb3 reconcile-battery-R2775\uff08676 \u5957/5032 \u5224\u636e\u00b7\u672c\u7a97\u5173\u95ed\u65f6\u4ecd alive\uff1b\u6d41\u4e2d 1 \u6761 FAIL \u884c\u5373\u672c\u7a97\u5df2\u4fee\u7684 census \u5957\u4ef6\uff09\uff0c\u5e76\u5728\u6700\u7ec8\u63d0\u4ea4\u6811\u4e0a\u91cd\u8dd1 census \u5bb6\u65cf\u4e0e export \u961f\u5217"


def due():
    return (datetime.datetime.now(TZ)
            + datetime.timedelta(hours=48)).replace(microsecond=0).isoformat()


def main():
    state = json.load(io.open(STATE, encoding="utf-8"))
    data = json.load(io.open(EXPORT, encoding="utf-8"))
    tick = str(state["tick"])
    label = tick_label()
    rows = data.get("results") or []
    stamped = [r for r in rows if isinstance(r, list) and len(r) >= 2
               and r[1] == label]
    if len(stamped) != 1:
        sys.stdout.write("E_EXP expected exactly 1 tick row, found %d\n"
                         % len(stamped))
        return 2
    stamped[0][0] = tick
    data["results"] = rows
    outs = data.get("outs") or []
    if not outs or outs[0] != LATEST:
        outs.insert(0, LATEST)
    data["outs"] = outs
    data["export_ts"] = STAMP
    data["do"] = CURRENT
    ceo = data.get("ceo_face") or {}
    ceo["current"] = CURRENT
    ceo["latest_artifact"] = LATEST
    ceo["last_artifact"] = LATEST
    ceo["next_milestone"] = NEXT
    ceo["next_milestone_due"] = due()
    ceo["updated_at"] = STAMP
    data["ceo_face"] = ceo
    at_write = cec.recompute()[0]
    data["self_drive"] = {
        "window": at_write["window"],
        "window_days": at_write["window_days"],
        "log_lines_in_window": at_write["log_lines_in_window"],
        "idle_fast_mention_lines": at_write["idle_fast_mention_lines"],
        "no_pullable_mention_lines": at_write["no_pullable_mention_lines"],
        "substantive_non_idle_mention_lines":
            at_write["substantive_non_idle_mention_lines"],
        "proposals_total": at_write["proposals_total"],
        "proposals_open": at_write["proposals_open"],
        "queue_main_open": at_write["queue_main_open"],
        "queue_tech_open": at_write["queue_tech_open"],
        "queue_explore_open": at_write["queue_explore_open"],
    }
    try:
        EDQF.refresh(data, REPO)
    except EDQF.ExportDriverQueueFaceError as exc:
        sys.stdout.write("E_EXP queue face unreadable %s\n" % exc)
        return 2
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    try:
        proof = EDQF.publish(REPO, EXPORT, text)
    except EDQF.ExportDriverQueueFaceError as exc:
        sys.stdout.write("QUEUE FACE REFUSED %s\n" % exc)
        return 2
    back = json.load(io.open(EXPORT, encoding="utf-8"))
    ok = (back["ceo_face"]["latest_artifact"] == LATEST
          and back["ceo_face"]["current"] == CURRENT
          and back["ceo_face"]["next_milestone"] == NEXT
          and back["export_ts"] == STAMP
          and back["outs"][0] == LATEST
          and any(isinstance(r, list) and len(r) >= 2 and r[1] == label
                  and str(r[0]) == tick for r in back["results"])
          and back["self_drive"] == data["self_drive"])
    sys.stdout.write("WROTE rows=%d outs=%d tick=%s queue=%s queue_bytes=%s "
                     "ok=%s\n"
                     % (len(back["results"]), len(back["outs"]), tick,
                        proof.get("gate"), proof.get("bytes"), ok))
    return 0 if ok and proof.get("gate") == "CURRENT" else 2


if __name__ == "__main__":
    sys.exit(main())
