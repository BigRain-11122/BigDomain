"""export_R2326.py - refresh the CEO-visible face (docs/status-export.json).

Derived fields come from the shipped consistency checker (F3: self_drive is
never written by hand), the queue counts from that same recomputation, and the
three CEO lines are this round's own facts. Appends one heartbeat row.

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

DO = ("R2326 验证窗：在已提交的 R2325 树上跑全量对账电池（零产品改动），"
      "核销上一轮产品交付的验证账，并把预注册基线的标号误差当场披露。")

CURRENT = ("R2326 验证窗交付：全量对账电池 RUNNER PASS 470/470 套件（控制 7/7）"
           "839.6 秒，判据总数 3796；四段跟随检查按设计先在矩阵 FAIL、"
           "重生成后再复跑全部 PASS，VERDICT R2326 PASS。预注册 471/3802 "
           "与实际 470/3796 差 −1 套件/−6 判据，已定位为台账把 R2325 之后的"
           "状态误标成 R2324（R2324 自身日志实为 469/3790），故对真实基线"
           "恰为 +1/+6，无未解差值。本窗零产品代码改动，0 产品分。")

LATEST = ("qa/reconcile-all-R2326.log（2026-11-01·787466B·RUNNER PASS 470/470·"
          "判据 3796）+ docs/sandbox-suite-matrix.md（45098B·470/3796）")

NEXT = ("R2327 产品窗：认领技术队头 AC-RWW1（review_window_wire，判据已预注册于"
        "state/queue/tech.md:381）——让 exempt_review 的窗口从声明读取并拒绝"
        "UNPINNED/DRIFT；窗 ≤48h")

ENTRY = ("R2326 verification window: the full reconcile battery on the "
         "committed R2325 tree read RUNNER PASS 470/470 suites plus controls "
         "7/7 in 839.6s with criteria total 3796; the pre-registered 471/3802 "
         "was reconciled by a named correction (the board's parenthetical "
         "baseline mislabelled the post-R2325 state as R2324, whose own log "
         "reads 469/3790, so the measured delta is exactly +1 suite / +6 "
         "criteria from os-followup-retry-history); four follow-up sections "
         "PASS after the designed matrix FAIL and its regeneration; zero "
         "product code changed.")

OUT_KEY = "qa/reconcile-all-R2326.log"

HEARTBEAT_ROW = (
    "tick 2326 2026-11-01 R2326 verification window: full reconcile battery on "
    "the committed R2325 tree read RUNNER PASS 470/470 suites plus controls 7/7 "
    "in 839.6s, criteria total 3796, TMP RECLAIM 932/932 worlds 326.59 MiB busy "
    "zero; the pre-registered 471/3802 differed by -1 suite / -6 criteria and "
    "the cause was named rather than swept (the board's baseline mislabelled "
    "the post-R2325 state as R2324; R2324's own log reads 469/3790, so the "
    "measured delta is exactly +1/+6 from os-followup-retry-history); four "
    "follow-up sections PASS after the designed matrix FAIL and regeneration to "
    "470/3796 (45098B); zero product code changed.")


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
    face["last_artifact"] = OUT_KEY
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
    if not any(row and row[0] == "R2326" for row in results):
        results.insert(0, ["R2326", ENTRY])
    data["results"] = results
    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    after = len(body.encode("utf-8"))
    print("EXPORT R2326 before=%dB after=%dB export_ts=%s window=%s lines=%s"
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
    if "tick 2326 " in beat:
        print("HEARTBEAT already carries tick 2326")
    else:
        if not beat.endswith("\n"):
            beat += "\n"
        beat += HEARTBEAT_ROW + "\n"
        with io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(beat)
        print("HEARTBEAT appended tick 2326")
    print("WROTE readback ok temp clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))