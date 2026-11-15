"""export_R2767 - refresh docs/status-export.json for the R2767 window.

The shipped generic driver supplies the derived blocks; this file adds only the
three CEO lines, composed from numbers THIS window measured: BD-PROP-010 sizes
coverage moved from 5 of 8 to 7 of 8 faces, the UGC face reads 9/9 and the
ledger face PASS, the negative control caught and the birth site was repaired,
and the API-market face is blocked by a pinned exact-key assertion whose line
number is carried.
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

CURRENT = ("R2767 \u4ea7\u54c1\u5207\u7247\uff1a8 \u9762\u4e2d\u7684 "
           "UGC \u5b89\u5168\u9762\u4e0e\u4ee3\u5e01\u8d26\u672c\u9762\u73b0"
           "\u5df2\u81ea\u5e26\u5c3a\u5bf8\u6ce8\u8bb0\uff08\u8986\u76d6 5/8 "
           "\u2192 7/8\uff09\uff0c\u4e14\u8be5\u6ce8\u8bb0\u88ab\u95e8\u63a7"
           "\u4f4f\u800c\u975e\u88c5\u9970\uff1aUGC \u9762 --check 9/9\uff08"
           "9079B/6326B\uff09\uff0c\u8d26\u672c\u9762 --check PASS"
           "\uff085276B/1061B\uff09")
LATEST = ("preview/ugc-gate-report.json\uff08\u65b0\u589e sizes "
          "\u5757\u00b7\u81ea\u6307\u81ea\u8eab\u5b57\u8282\u6570\uff09\uff0b"
          "preview/ledger-business-report.json\uff08\u540c\u4e0a\u00b7"
          "\u65b0\u589e\u53ea\u8bfb --check\uff09\uff0bqa/BD-PROP-010-R2767.log"
          "\uff08\u8d1f\u63a7 6/6\u00b7\u6355\u83b7\u5e76\u4fee\u590d\u4e00"
          "\u4e2a\u51fa\u751f\u5730\u7f3a\u9677\uff09")
NEXT = ("48 \u5c0f\u65f6\u5185\uff1a\u91c7\u7eb3\u672c\u7a97\u53e3\u63d0\u4ea4"
        "\u6811\u540e\u542f\u52a8\u7684 reconcile-battery-R2767 \u5168\u91cf"
        "\u7535\u6c60\uff08676 \u5957\u4ef6/5032 \u5224\u636e\uff09\uff1b\u518d"
        "\u8865 API \u5e02\u573a\u9762\u5c3a\u5bf8\u6ce8\u8bb0\uff08\u9700\u540c"
        "\u6b65\u6539 src/sandbox/ledger/test_apimarket_report_json.py:124 "
        "\u7684\u952e\u96c6\u65ad\u8a00\uff09")


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
