"""export_R2324.py - refresh the CEO-visible face (docs/status-export.json).

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

DO = ("R2324 验证窗：清掉 R2323 产品窗欠下的验证账——先在已提交树上把状态文件的水位线折叠"
      "（78481B → 71311B，余量 7189B），再跑全量对账电池，最后回读产品面实况。")

CURRENT = ("R2324 验证窗交付：折叠 619 + 全量对账电池 RUNNER PASS 469/469 套件（控制 7/7）"
           "791.9 秒，判据总数 3790 与预注册完全一致（对 R2322 468/3784 为 +1 套件 / +6 判据），"
           "四段跟随检查在矩阵先按设计 FAIL 后重生成再复跑，全部 PASS，VERDICT R2324 PASS；"
           "实况回读 orphan_trace --trace = rounds=1 legs=2 trace_exists=1 verdict=TRACE-FOUND，"
           "R2136 由 -c 腿顶替。本窗零产品代码改动，0 产品分。")

LATEST = ("qa/reconcile-all-R2324.log（2026-11-01·786983B·RUNNER PASS 469/469·"
          "判据 3790）+ docs/sandbox-suite-matrix.md（45005B·469/3790）")

NEXT = ("R2325 产品窗：认领技术队头 state/queue/tech.md:380（AC-FRH1 "
        "followup_retry_history），判据已预注册于该行；随后电池目标预注册为 "
        "470 套件 / 3796 判据——窗 ≤48h")

ENTRY = ("R2324 verification window: fold 619 moved the R2309 and R2310 whole "
         "round blocks into the archive at a 19B margin (78481B -> 71311B), the "
         "full reconcile battery on the committed fold tree read RUNNER PASS "
         "469/469 suites plus controls 7/7 in 791.9s with criteria total 3790 "
         "exactly as pre-registered, four follow-up sections PASS after the "
         "designed matrix FAIL and its regeneration, and the live product read "
         "TRACE-FOUND with R2136 standing in through its -c leg; zero product "
         "code changed.")

OUT_KEY = "qa/reconcile-all-R2324.log"

HEARTBEAT_ROW = (
    "tick 2324 2026-11-01 R2324 verification window: the waterline fold ran "
    "first (78481B -> 71311B, margin 7189B, archive prefix intact, 7 window "
    "tokens covered) and created NO live residue, so the speculative "
    "declaration splice was reverted; the full reconcile battery on the "
    "committed fold tree read RUNNER PASS 469/469 suites plus controls 7/7 in "
    "791.9s with criteria total 3790 exactly as pre-registered (+1 suite / +6 "
    "criteria against R2322 from the R2323 os-orphan-trace suite), TMP RECLAIM "
    "932/932 worlds 326.59 MiB busy zero; four follow-up sections PASS after "
    "the designed matrix FAIL and its regeneration to 469/3790 (45005B); live "
    "reading orphan_trace --trace = rounds=1 legs=2 trace_exists=1 "
    "verdict=TRACE-FOUND with R2136 standing in through reconcile-all-R2136c.log.")


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
    face["last_artifact"] = "qa/reconcile-all-R2324.log"
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
    if not any(row and row[0] == "R2324" for row in results):
        results.insert(0, ["R2324", ENTRY])
    data["results"] = results
    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    after = len(body.encode("utf-8"))
    print("EXPORT R2324 before=%dB after=%dB export_ts=%s window=%s lines=%s"
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
    if "tick 2324 " in beat:
        print("HEARTBEAT already carries tick 2324")
    else:
        if not beat.endswith("\n"):
            beat += "\n"
        beat += HEARTBEAT_ROW + "\n"
        with io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(beat)
        print("HEARTBEAT appended tick 2324")
    print("WROTE readback ok temp clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))