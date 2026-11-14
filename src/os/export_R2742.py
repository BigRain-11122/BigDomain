"""export_R2742 - refresh docs/status-export.json for the R2742 window.

The shipped generic driver supplies everything except this round own CEO lines,
so this driver composes the three of them from numbers THIS window read:

  qa/export-parity-difference-order-field-R2742b.log (8139B) holds two suite
  legs with the identical digest DC582D20F8A0EA12 at SUITE PASS 6/6 each and
  three adjacent suites green at rc=0; the registry re-read BY IMPORT reads 676
  suites / 5032 criteria / 676 unique names / 676 unique paths; the matrix was
  restamped stamp-aligned to 71635B and --check reads byte-identical rc=0
  citing qa/reconcile-all-R2739.log at green=675/676; the LIVE reading on the
  real docs/status-export.json is IDENTICAL at 411953B against itself and
  ORDER-ONLY order_field=export_ts at 410805B against the same document in
  sorted key order; product-face-R2741 closed, reconcile-battery-R2742
  registered first=yes, and the measured queue head is
  state/queue/tech.md:713 prefix AC-LKNF1 with claimable 10.
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

CURRENT = ("R2742 \u4ea7\u54c1\u7a97\uff1a\u4ea4\u4ed8 src/os/export_parity_"
           "difference_order_field.py\u2014\u2014\u5f53\u952e\u5e8f\u662f\u552f"
           "\u4e00\u5dee\u5f02\u65f6\u70b9\u540d\u7b2c\u4e00\u4e2a\u79fb\u4f4d"
           "\u5b57\u6bb5\uff08\u4e24\u79cd\u987a\u5e8f\u4e92\u8bc1\u00b7\u56db"
           "\u79cd\u5f62\u5f62\u6001\uff09\uff0c\u5e76\u539f\u6837\u4fdd\u7559"
           "\u5df2\u6709\u5dee\u5f02\u5f8b\u7684\u7b54\u6848\uff1b\u5b9e\u8bc1"
           "\u4e24\u8dd1\u540c\u4e00\u6458\u8981 DC582D20F8A0EA12\u3001\u90bb"
           "\u57df 3 \u5957\u5168\u7eff\u3001\u6ce8\u518c\u8868\u6309\u5bfc\u5165 "
           "676/5032\u3001\u77e9\u9635 --check \u9000\u51fa 0")
LATEST = ("qa/export-parity-difference-order-field-R2742b.log\uff088139 \u5b57"
          "\u8282\u00b7\u4e24\u8dd1\u540c\u4e00\u6458\u8981\u00b7\u90bb\u57df 3/3"
          "\u5168\u7eff\uff09\uff0b\u91cd\u5237\u7684 docs/sandbox-suite-matrix.md"
          "\uff0871635 \u5b57\u8282\u00b7676 \u5957\u4ef6 / 5032 \u5224\u636e\u00b7"
          "--check \u9000\u51fa 0\uff09\uff082026-11-15 \u672c\u7a97\u5b9e\u6d4b"
          "\uff09")
NEXT = ("48 \u5c0f\u65f6\u5185\uff1a\u5148\u8dd1\u5168\u91cf\u7535\u6c60 676 \u5957"
        "\u4ef6\uff08debt_gate \u5df2\u5217 reconcile-battery-R2742 first=yes\uff0c"
        "\u4e0d\u8dd1\u5b8c\u4e0d\u8fdb\u4e0b\u4e00\u4e2a\u4ea7\u54c1\u5b57\u8282"
        "\uff09\uff0c\u7eff\u540e\u63d0\u5df2\u6b20\u516b\u7a97\u7684\u5bfc\u51fa"
        "\u94a9\u5b50\u4fee\u590d\uff1b\u961f\u5217\u5934\u5b9e\u6d4b\u4e3a state/"
        "queue/tech.md:713 AC-LKNF1 \u00b7 claimable 10 \u00b7 \u5730\u677f MET")


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
