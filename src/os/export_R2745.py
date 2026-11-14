"""export_R2745 - refresh docs/status-export.json for the R2745 window.

The shipped generic driver supplies everything except this round own CEO lines,
so this driver composes the three of them from numbers THIS window read: a
monitored wait on reconcile-battery-R2742 whose leg is still alive at pid 64528
(644 of a pre-registered 676 suites, 32 ahead, five red rows), and the measured
repair of those five red rows - the R2742 closeout never wrote its tokens line,
so five ledger suites read red on the real tree; the line was restored through
the canonical writer at its own chronological position with an api_reason that
says R2745 reconstructed it, and all five suites re-ran green.
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

CURRENT = ("R2745 \u76d1\u63a7\u7b49\u5f85\u7a97\uff0b\u5b9e\u6d4b\u4fee\u590d"
           "\uff1aR2742 \u5168\u91cf\u7535\u6c60\u817f\u5b9e\u6d4b 644/676"
           "\u3001\u4ecd\u5728\u8dd1\uff0832 \u5957\u5f85\u8dd1\uff09\uff0c"
           "\u4ea7\u54c1\u5b57\u8282\u6309\u6df7\u5408\u6811\u5f8b\u51bb\u7ed3"
           "\uff1b\u672c\u8f6e\u67e5\u660e 5 \u7ea2\u540c\u4e00\u51fa\u751f\u5730"
           "\uff1dR2742 \u6536\u53e3\u6f0f\u5199\u5176\u8d26\u76ee\u884c\uff0c"
           "\u6309\u89c4\u8303\u5199\u5165\u5668\u5728\u5176\u81ea\u8eab\u65f6\u5e8f"
           "\u4f4d\u7f6e\u8865\u56de\u5e76\u5982\u5b9e\u6807\u6ce8\u4e3a\u91cd"
           "\u5efa\uff0c5 \u5957\u4ef6\u5728\u4fee\u597d\u7684\u771f\u6811\u4e0a"
           "\u91cd\u8dd1\u5168\u7eff\uff088/8\u00b78/8\u00b78/8\u00b76/6\u00b7"
           "6/6\uff09")
LATEST = ("src/os/state_append_R2745.py \u8865\u56de R2742 \u8d26\u76ee\u884c\uff0b"
          "5 \u5957\u4ef6\u91cd\u8dd1\u5168\u7eff\uff0b logs/battery-R2742.stream"
          "\uff081091967 \u5b57\u8282\u00b7644/676\u00b75 \u7ea2\u5df2\u67e5\u660e"
          "\u51fa\u751f\u5730\uff09\uff082026-11-15 \u672c\u7a97\u5b9e\u6d4b\uff09")
NEXT = ("48 \u5c0f\u65f6\u5185\uff1aR2742 \u7535\u6c60 676 \u5957\u4ef6\u8dd1\u5b8c"
        "\u540e\u6309\u8bc1\u636e\u8def\u5f84\u91c7\u7eb3\uff08\u4e0d\u91cd\u542f"
        "\u817f\uff09\uff0c\u7eff\u540e\u4fee\u5df2\u6b20\u5341\u7a97\u7684\u5bfc"
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
