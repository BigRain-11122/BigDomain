"""export_R2323.py - refresh the CEO-visible face (docs/status-export.json).

Every derived field comes from the live files: self_drive is recomputed by the
shipped consistency checker (F3: never written by hand), the queue counts come
from that same recomputation, and the three CEO lines are the round's own
facts. Newest entries go first in outs/results, as the file already does.

Also appends this window's heartbeat row (one line per tick).

Dry run by default; --execute writes utf-8.
"""

import datetime
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_export_consistency as CEC  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

DO = ("R2323 产品窗：ORPHAN 证据不再读成同一种死路——一个只读解析器把每个孤儿轮次"
      "的变体腿打开，读出各自的 RUNNER/VERDICT 行，指明哪条腿能顶替正名腿。")

CURRENT = ("R2323 交付 src/os/orphan_trace.py + 其套件：孤儿轮次的清单、轮次与腿配对"
           "全部问 evidence_variants，RUNNER 令牌与解码阶梯问 followup_history（套件逐项"
           "打桩证明无第二份实现）；每条带 RUNNER 行的腿都被点名并给出自己的 RUNNER "
           "令牌、VERDICT 令牌与摘要，按名序第一条为顶替腿；一条 RUNNER 都没有读 "
           "NO-TRACE，空清单读 NO-ORPHAN 导 0，无法解码的腿直接拒绝而不是当成空腿。"
           "SUITE PASS 6/6 两轮一致，五套相邻 os 套件同绿，wired os-orphan-trace(6)。"
           "实况：rounds=1 legs=2 trace_exists=1，R2136 由 reconcile-all-R2136c.log"
           "（RUNNER PASS）顶替，-b 读 RUNNER FAIL，即改个名就能收回该轮次。")

LATEST = ("qa/orphan-trace-R2323.log（2026-11-01，1342B）+ "
          "src/os/orphan_trace.py + src/os/test_orphan_trace.py")

NEXT = ("R2324 验证轮：在已提交的 R2323 树上跑全量对账电池并重生成矩阵，预注册目标 "
        "469 套件 / 3790 判据（对 R2322 的 468/3784 恰 +1 套件 / +6 判据）；"
        "电池通过后回到技术队头 line 380（AC-FRH1 followup_retry_history）——窗口 ≤48h")

ENTRY = ("R2323 product window: orphan_trace shipped with its six pre-registered "
         "criteria pinned in the tech row at state/queue/tech.md:379 BEFORE the "
         "code - one read-only resolver, one suite, one dogfooded evidence "
         "capture (two identical legs plus five adjacent suites green), one "
         "runner wiring line, two this-window defects caught before any "
         "evidence and fixed without widening a criterion, one tech row closed "
         "with one successor seed holding the tech floor at 10, and zero cloud "
         "or external API calls.")

OUT_KEY = "src/os/orphan_trace.py"

HEARTBEAT_ROW = (
    "tick 2323 2026-11-01 R2323 product window: ORPHAN evidence stops being a "
    "dead end - src/os/orphan_trace.py resolves every orphan round from "
    "evidence_variants against its own variant legs, naming every leg that "
    "carries a RUNNER line with its runner token, verdict token and digest and "
    "the first such leg in name order as the standing-in leg, reading NO-TRACE "
    "when no leg carries one, NO-ORPHAN over an empty list, and refusing an "
    "undecodable leg instead of counting it as empty. Live: R2136 stands in "
    "through reconcile-all-R2136c.log (RUNNER PASS) while -b reads RUNNER FAIL. "
    "SUITE PASS 6/6 twice, five adjacent os suites green, evidence 1342B, wired "
    "os-orphan-trace(6); tech claimable refilled to 10 with the orphan_promote "
    "seed.")


def stamp():
    now = datetime.datetime.now().astimezone()
    return now.replace(microsecond=0)


def main(argv):
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    derived, state, _export, pat = CEC.recompute()
    tick = state.get("tick")
    now = stamp()
    before = len(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    data["export_ts"] = now.isoformat()
    data["do"] = DO
    face = data.get("ceo_face") or {}
    face["current"] = CURRENT
    face["latest_artifact"] = LATEST
    face["last_artifact"] = "qa/orphan-trace-R2323.log"
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = (now + datetime.timedelta(hours=48)).isoformat()
    data["ceo_face"] = face
    drive = data.get("self_drive") or {}
    for key in ("window", "window_days", "log_lines_in_window",
                "idle_fast_mention_lines", "no_pullable_mention_lines",
                "substantive_non_idle_mention_lines", "proposals_total",
                "proposals_open", "queue_main_open", "queue_tech_open",
                "queue_explore_open"):
        if key in derived:
            drive[key] = derived[key]
    data["self_drive"] = drive
    outs = data.get("outs") or []
    if not any(row and row[0] == OUT_KEY for row in outs):
        outs.insert(0, [OUT_KEY, "on", ENTRY])
    data["outs"] = outs
    results = data.get("results") or []
    label = pat["tick_row_label"]
    for row in results:
        if isinstance(row, list) and len(row) >= 2 and row[1] == label:
            row[0] = str(tick)
    if not any(row and row[0] == "R2323" for row in results):
        results.insert(0, ["R2323", ENTRY])
    data["results"] = results
    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    after = len(body.encode("utf-8"))
    print("EXPORT R2323 before=%dB after=%dB export_ts=%s window=%s lines=%s"
          % (before, after, data["export_ts"], drive.get("window"),
             drive.get("log_lines_in_window")))
    if "--execute" not in argv:
        print("DRY RUN - wrote nothing")
        return 0
    temp = EXPORT + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    os.replace(temp, EXPORT)
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != body:
        print("E_READBACK")
        return 3
    if os.path.exists(temp):
        print("E_RESIDUE")
        return 3
    with io.open(HEARTBEAT, "r", encoding="utf-8") as handle:
        beat = handle.read()
    if "tick 2323 " in beat:
        print("HEARTBEAT already carries tick 2323")
    else:
        if not beat.endswith("\n"):
            beat += "\n"
        beat += HEARTBEAT_ROW + "\n"
        with io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(beat)
        print("HEARTBEAT appended tick 2323")
    print("WROTE readback ok temp clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))