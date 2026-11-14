"""export_R2741 - refresh docs/status-export.json for the R2741 window.

The shipped generic driver supplies everything except this round own CEO
lines, so this driver composes the three of them from numbers THIS window
read, not from the round it inherited.

Numbers behind the three lines (all measured in R2741):
  qa/reconcile-all-R2739.log reads 1248602B, 675 of 675 suite rows PASS with
  675 unique names, ZERO FAIL, every row carrying criteria and an independent
  recount summing to exactly 5026, no BOM, zero CRLF, zero lone CR, zero NUL,
  tail RUNNER PASS plus BATTERY rc=0 4986.6s, and the registry re-read BY
  IMPORT at 675 suites / 5026 criteria / 675 names / 675 paths with the
  evidence name set equal to the registry name set; the pid chain was gone by
  kernel probe before any byte was read; suite_matrix --check first read rc=2
  on a stale evidence face and then PASS byte-identical at 71510B after a
  stamp-aligned regeneration; the R2614 fifteen-suite set read 15/15 green on
  the FINAL committed tree 87abb6e7 (qa/write-sensitive-R2739.log, 14036B);
  battery_followup appended VERDICT battery-R2739 PASS; reconcile-battery-R2733
  closed open 36 to 35; and product-face-R2741 was registered first=yes on the
  queue head state/queue/tech.md:703 prefix AC-DFOB1 with claimable 11.
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

CURRENT = ("R2741 \u91c7\u7eb3\u7a97\uff1aR2739 \u7ee7\u4efb\u7535\u6c60\u6309\u8bc1\u636e\u8def\u5f84\u91c7\u7eb3\u4e3a\u7eff\uff08\u5b9e\u6d4b 1248602 \u5b57\u8282\u3001675/675 \u5957\u4ef6\u5168\u7eff\u3001675 \u4e2a\u552f\u4e00\u5957\u4ef6\u540d\u3001\u96f6\u5931\u8d25\u3001\u72ec\u7acb\u590d\u7b97\u5224\u636e\u6070\u5024 5026\u3001\u6ce8\u518c\u8868\u6309\u5bfc\u5165 675/5026/675/675\u3001BATTERY rc=0 4986.6 \u79d2\uff09\uff0c\u672a\u91cd\u542f\u4e14\u672a\u80cc\u79bb\u5b57\u8282\u8bfb\uff1b\u77e9\u9635\u91cd\u5237\u540e --check \u9000\u51fa 0\uff0c\u5199\u654f\u96c6 15/15 \u5168\u7eff\uff0c\u5df2\u7ed3\u6e05 battery \u6b20\u8d26\u4e14\u65b0\u5f00 ACS \u4ea7\u54c1\u9762\u6b20\u8d26")
LATEST = ("qa/reconcile-all-R2739.log\uff081248602 \u5b57\u8282\u00b7675 \u5957\u4ef6\u5168\u7eff\u00b75026 \u5224\u636e\uff09\uff0b\u91cd\u5237\u7684 docs/sandbox-suite-matrix.md\uff0871510 \u5b57\u8282\u00b7--check \u9000\u51fa 0\uff09\uff0bqa/write-sensitive-R2739.log\uff0815/15 \u5168\u7eff\u00b714036 \u5b57\u8282\uff09\uff082026-11-15 01:0x \u672c\u7a97\u5b9e\u6d4b\uff09")
NEXT = ("48 \u5c0f\u65f6\u5185\uff1a\u961f\u5217\u5934 state/queue/tech.md:703 AC-DFOB1 \u4ea7\u54c1\u9762\uff08src/os/export_parity_difference_order_field.py\uff1a\u952e\u5e8f\u4e0d\u540c\u65f6\u987b\u70b9\u540d ORDER \u5b57\u6bb5\u800c\u975e\u53ea\u7b54 bytes\uff09\uff1b\u5176\u540e\u4fee\u5df2\u6b20\u516b\u7a97\u7684\u5bfc\u51fa\u94a9\u5b50 src/os/export_R2431.py\uff08DO/LATEST/NEXT/OUTS \u5e38\u91cf\u5df2\u4e0d\u88ab main() \u8bfb\u53d6\uff09")


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
