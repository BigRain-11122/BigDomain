"""export_R2740 - refresh docs/status-export.json for the R2740 window.

The shipped generic driver supplies everything except this round's own CEO
lines, so this driver composes the three of them from numbers THIS window read.

Numbers behind the three lines (all measured in R2739):
  qa/reconcile-all-R2737.log reads 1249289B, 671 of 675 suite rows PASS,
  671 unique names, 4 FAIL rows, criteria 5000 of the expected 5026, no BOM,
  zero CRLF, zero lone CR, zero NUL, tail RUNNER FAIL (5 failed assertions) +
  BATTERY rc=1 3963.7s - so the leg CLOSED RED and was NOT adopted green;
  its four red rows are exactly the four whose birth sites R2738 repaired
  MID-LEG (os-state-io, os-status-export-writer-dialect-wire,
  os-queue-floor-export-face, os-export-consistency-queue-face), re-run GREEN
  on the repaired tree at R2738 (8/8, 6/6, 6/6, 15/15); the registry was
  re-measured BY IMPORT at 675 suites / 5026 criteria / 675 names / 675 paths;
  the successor leg was launched at pid 64724 on the committed tree and a
  second launch was refused with E_LAUNCH_PID_EXISTS; and a read-only census
  over 474 state-writing scripts found exactly 1 canonical-writer consumer,
  8 bare json.dump callers and 464 neither.
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

CURRENT = ("R2740 \u76d1\u89c6\u7b49\u5f85\u7a97\uff1aR2739 \u7ee7\u4efb\u7535\u6c60\u4ecd\u5728\u8dd1\uff08\u5b9e\u6d4b 282/675 \u5957\u4ef6\u3001\u96f6\u5931\u8d25\u3001\u7d2f\u8ba1\u5957\u4ef6\u65f6\u95f4 707.6 \u79d2\uff09\uff0c\u6309\u5176\u81ea\u8eab\u5b57\u8282\u63a8\u7b97 ETA 00:45-01:20\uff0c\u8d85\u51fa\u672c\u7a97 25 \u5206\u949f\uff0c\u6545\u53ea\u76d1\u89c6\u4e0d\u91c7\u7eb3\uff1b\u9876\u884c\u6307\u4ee4\u5df2\u8865\u5b9e\u6d4b\u72b6\u6001\u4e0e\u91c7\u7eb3\u95f8\u95e8")
LATEST = ("src/os/backlog.md \u9876\u884c\u5b9e\u6d4b\u6807\u6ce8\uff08\u5957\u4ef6\u8ba1\u6570 282/675\u3001\u96f6\u5931\u8d25\u3001ETA 00:45-01:20\u3001\u91c7\u7eb3\u95f8\u9010\u9879\u5217\u51fa\u3001\u6b20\u8d26\u9500\u8d26\u547d\u4ee4\u5177\u540d\uff09\uff082026-11-14 23:5x \u672c\u7a97\u5b9e\u6d4b\uff09")
NEXT = ("24h \u5185\uff1a\u6309\u8bc1\u636e\u8def\u5f84 qa/reconcile-all-R2739.log \u6536\u517b\u7535\u6c60\uff08675 \u5957\u4ef6\uff0f5026 \u5224\u636e\uff0c\u7eff\u5219\u91cd\u5237\u77e9\u9635\u3001\u8dd1 R2614 \u5199\u654f\u96c6\u3001\u7ed3\u6e05 reconcile-battery-R2733\uff09\uff1b\u968f\u540e\u9996\u4e2a\u975e\u7535\u6c60\u7a97\u4fee\u5df2\u6b20\u516b\u7a97\u7684\u5bfc\u51fa\u94a9\u5b50 export_R2431.py \u4e0e\u516b\u4e2a\u88f8 json.dump \u5199\u76d8\u70b9")


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
