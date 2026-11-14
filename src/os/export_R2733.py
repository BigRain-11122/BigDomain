"""export_R2733 - refresh docs/status-export.json for the R2733 window.

The shipped generic driver supplies everything except this round's own CEO
lines, so this driver composes the three of them from numbers THIS window read
and lets the same machinery publish: the tick row is stamped, the queue face
is gated, and the single publish call proves the bytes.

Numbers behind the three lines (all measured in R2733):
  live binding reading scanned=2265 bound=21 unbound=1 out_of_scope=2238
  unparsed=12, the single UNBOUND row closeout_R2385.py:159 first_field
  export_ts, the evidence file at 2951 bytes with two identical legs and five
  green adjacent suites, the registry by import at 675 suites / 5026 criteria,
  and reconcile-battery-R2733 registered first=yes at that same target.
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
STAMP = datetime.datetime.now(
    datetime.timezone(datetime.timedelta(hours=8))).replace(
        microsecond=0).isoformat()

CURRENT = (
    "R2733 产品窗：把 closeout_export_parity_wire 的调用方集合在调用时用 AST "
    "从树上派生并逐个判绑定——真实树 2265 个文件里 22 个真调用、21 个 BOUND、"
    "1 个 UNBOUND（closeout_R2385.py:159·首个不同字段 export_ts），另 12 个"
    "无法解析的文件被点名而非吞掉；同一批如果用正则扫会读出 52 处/32 文件，"
    "因为其中大半只是印在字符串里的示例行")
LATEST = (
    "src/os/closeout_export_parity_wire_binding_consumer.py ＋六判据套件全绿"
    "（qa/closeout-export-parity-wire-binding-consumer-R2733.log·2026-11-14·"
    "2951B·两次跑同 digest E038F813·相邻 5 套件绿）")
NEXT = (
    "下一窗：先按证据路径 qa/reconcile-all-R2733.log 验收预注册 675 套件/"
    "5026 判据的全量电池（已按 R2168 混合树律登记 first=yes），绿后跑写敏感集与"
    "四段 followup、重压矩阵并关债，再开队头 tech.md:703 AC-DFOB1——只换了键序的"
    "文档会被旧法报成 shape word bytes，运维看不出到底哪个字段不同")


def due():
    return (datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8)))
        + datetime.timedelta(hours=48)).replace(microsecond=0).isoformat()


def main():
    state = json.load(io.open(STATE, encoding="utf-8"))
    data = json.load(io.open(EXPORT, encoding="utf-8"))
    tick = str(state["tick"])
    rows = data.get("results") or []
    label = tick_label()
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
          and back["ceo_face"]["next_milestone_due"] == ceo["next_milestone_due"]
          and back["ceo_face"]["updated_at"] == STAMP
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
