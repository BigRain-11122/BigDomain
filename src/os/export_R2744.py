"""export_R2744 - refresh docs/status-export.json for the R2744 window.

The shipped generic driver supplies everything except this round own CEO lines,
so this driver composes the three of them from numbers THIS window read:

  a monitored wait on reconcile-battery-R2742 (leg alive at pid 64528, 253 of
  a pre-registered 676 suites PASS over 253 unique names with ZERO FAIL at
  491925B / 2998 lines, no evidence file and no closing BATTERY rc= line), and
  a second verified sweep of the debt register that closed 26 of 37 open rows
  by the R2732 three-part rule - independent readback reads rows=427,
  open 37->11, done 390->416, exactly 26 rows carrying closed=R2744 at
  240479B. The eleven rows kept open are named in the state log, not dropped.
  The registry is unmoved at 676 suites / 5032 criteria and the measured queue
  head is state/queue/tech.md:713 prefix AC-LKNF1 with claimable 10.
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

CURRENT = ("R2744 \u76d1\u63a7\u7b49\u5f85\u7a97\uff1aR2742 \u5168\u91cf\u7535"
           "\u6c60\u817f\u5b9e\u6d4b 253/676 \u5957\u4ef6\u3001\u96f6\u7ea2\u3001"
           "\u4ecd\u5728\u8dd1\uff08423 \u5957\u5f85\u8dd1\uff09\uff0c\u4ea7\u54c1"
           "\u5b57\u8282\u6309\u6df7\u5408\u6811\u5f8b\u51bb\u7ed3\uff1b\u672c\u8f6e"
           "\u628a\u503a\u52a1\u518c\u5269\u4f59 open \u884c\u6309\u4e09\u5206\u6cd5"
           "\u9010\u884c\u590d\u6838\uff0c37\u219211\uff0c26 \u884c\u95ed\u5408"
           "\uff08\u72ec\u7acb\u8bfb\u56de\u4e00\u81f4\uff09")
LATEST = ("src/os/debt.md \u590d\u6838\u5bf9\u8d26\uff08open 37\u219211\u00b7"
          "\u6070 26 \u884c\u5e26 closed=R2744\u00b7240479 \u5b57\u8282\uff09"
          "\uff0b logs/battery-R2742.stream\uff08491925 \u5b57\u8282\u00b7253/676"
          "\u00b7\u96f6\u7ea2\uff09\uff082026-11-15 \u672c\u7a97\u5b9e\u6d4b\uff09")
NEXT = ("48 \u5c0f\u65f6\u5185\uff1aR2742 \u7535\u6c60 676 \u5957\u4ef6\u8dd1\u5b8c"
        "\u540e\u6309\u8bc1\u636e\u8def\u5f84\u91c7\u7eb3\uff08\u4e0d\u91cd\u542f"
        "\u817f\uff09\uff0c\u7eff\u540e\u4fee\u5df2\u6b20\u4e5d\u7a97\u7684\u5bfc"
        "\u51fa\u94a9\u5b50\u5e76\u53d6\u961f\u5217\u5934 state/queue/tech.md:713 "
        "AC-LKNF1\uff08claimable 10\uff09\uff1b\u817f\u82e5 48h \u672a\u6536\u4ecd"
        "\u6309\u76d1\u63a7\u7a97\u7eed\u8bb0")


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
