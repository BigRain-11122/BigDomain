"""export_R2791 - refresh docs/status-export.json for the R2791 window.

The generic driver supplies the derived blocks; this file adds the three CEO lines
composed from numbers THIS window measured: an over-cap lobby send is REFUSED with
the server's own code E_TEXT_TOO_LONG instead of being silently truncated, the
shipped AC-S47 face was replaced to assert the refusal while keeping its
idempotency purpose, the trace page re-rendered at frames=17 refusals=6 codes=4
behind a read-only gate plus a byte-injection control, and the spec gained AC-S24
so a client can discover the refusal before meeting it.
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

CURRENT = "R2791 产品与行为修正：大厅超长发言从「静默截断」改成「明确拒绝」——4000 字送进来，服务端回 sec.reject code=E_TEXT_TOO_LONG 并载 limit/actual，不广播也不落库，idea.submit 同码同上限；理由不是口味而是平台一致性，HTTP 内容闸控制台早已对同样输入回 413；preview/lobby-session-trace.html（8347B）重渲染后读者能看到这条拒绝帧与它自己的码（frames=17 refusals=6 codes=4）；规格新增 AC-S24，判据 AC-OVL1..6 先落板后写码，大厅大套件 79/79、房选器 8/8、入口页 14/14"
LATEST = "preview/lobby-session-trace.html（8347B）+ preview/lobby-session-trace.json（8008B·双渲染逐字节同一）"
NEXT = "48 小时内：把 AC-VAC1..6 的账本对账判据补进 src/sandbox/ledger/reconcile.py，并注册 tools/lobby_session_trace.py（注册表需要携带判据的套件模块）；全量电池仍欠，须由能 supervising 4000-5900s 的窗口早发并以自身 BATTERY rc= 行采纳"


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
