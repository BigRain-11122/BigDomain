"""export_R2328.py - refresh the CEO-visible face (docs/status-export.json).

Derived fields come from the shipped consistency checker (F3: self_drive is
never written by hand); the three CEO lines are this round's own facts.
Appends one heartbeat row. Dry run by default; --execute writes utf-8.
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

DO = ("R2328 验证窗：在已提交的 R2327 树上补跑上一轮欠下的全量对账电池，"
      "并把电池抓到的真实缺陷修在出生站。")

CURRENT = ("R2328 验证窗交付：全量对账电池首跑红（467/471 套件，5 条断言，全在"
           "台账族），根因实测=R2327 收账把本轮台账行写成无轮次前缀的 "
           "'tokens: ...'，于是 '^R<n> tokens:' 法读不到它、覆盖律判 DIRTY；"
           "出生站修复=在原位插入 6 字节 'R2327 '（原文拼接、其余字节逐字节不变、"
           "读回验证），四件台账套件复跑 8/8 绿；已提交修复树重跑= RUNNER PASS "
           "471/471 套件（控制 7/7）827.1 秒，判据总数 3802，与预注册的 "
           "+1 套件/+6 判据（对 R2326 的 470/3796）完全一致；四段跟随检查按设计"
           "先在矩阵 FAIL、重生成 471/3802（45205B）后复跑全 PASS，VERDICT R2328 "
           "PASS。本窗零产品代码改动，0 产品分。")

LATEST = ("qa/reconcile-all-R2328-retry.log（2026-11-01·792511B·RUNNER PASS "
          "471/471·判据 3802）+ 红腿 qa/reconcile-all-R2328.log（788640B）"
          "+ docs/sandbox-suite-matrix.md（45205B·471/3802）")

NEXT = ("R2329 产品窗：认领技术队头 AC-SEPR1（stamp_exempt_prune，判据已预注册于"
        "state/queue/tech.md:382）——让盖章豁免声明可退休：按复核器自己的 MISSING "
        "与过期读数派生退休集，试跑默认、原子落地、读回验证；窗 ≤48h")

ENTRY = ("R2328 verification window: the battery the R2327 closeout deferred "
         "ran on the committed tree and its FIRST leg was red - 467/471 "
         "suites, 5 assertions, all in the ledger family - because the R2327 "
         "closeout had written its round ledger item without a round prefix, "
         "so the pinned '^R<n> tokens:' law could not see it; repaired at the "
         "birth site with a six-byte raw-text splice that leaves every other "
         "byte identical, all four ledger suites green, and the retry read "
         "RUNNER PASS 471/471 plus controls 7/7 in 827.1s with criteria total "
         "3802 exactly as pre-registered; four follow-up sections PASS after "
         "the designed matrix FAIL and its regeneration; zero product code "
         "changed.")

OUT_KEY = "qa/reconcile-all-R2328-retry.log"

HEARTBEAT_ROW = (
    "tick 2328 2026-11-01 R2328 verification window: fold 620 ran first "
    "(78496B at a 4B margin -> 67340B, 45 tokens, predicted equal to measured) "
    "and the two rounds it exposed as residue (R2312, R2314) were spliced as "
    "DELIVERED by name (192 -> 194, readback ok); the first battery was RED "
    "467/471 with 5 ledger assertions caused by the R2327 ledger item lacking "
    "its round prefix, repaired as a six-byte raw-text splice at the birth "
    "site (67340B -> 67346B) with all four ledger suites 8/8; the retry read "
    "RUNNER PASS 471/471 suites plus controls 7/7 in 827.1s, criteria total "
    "3802 exactly as pre-registered, TMP RECLAIM 932/932 worlds 326.59 MiB "
    "busy zero; four follow-up sections PASS after the designed matrix FAIL "
    "and regeneration to 471/3802 (45205B); zero product code changed.")


def stamp():
    return datetime.datetime.now().astimezone().replace(microsecond=0)


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
    if not any(row and row[0] == "R2328" for row in results):
        results.insert(0, ["R2328", ENTRY])
    data["results"] = results
    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    after = len(body.encode("utf-8"))
    print("EXPORT R2328 before=%dB after=%dB export_ts=%s window=%s lines=%s"
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
    if "tick 2328 " in beat:
        print("HEARTBEAT already carries tick 2328")
    else:
        if not beat.endswith("\n"):
            beat += "\n"
        beat += HEARTBEAT_ROW + "\n"
        with io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(beat)
        print("HEARTBEAT appended tick 2328")
    print("WROTE readback ok temp clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))