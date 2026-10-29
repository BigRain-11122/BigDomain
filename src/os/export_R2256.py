# export_R2256.py - refresh the CEO-visible face for round R2256.
# Round-derived values only (F3 law: nothing hardcoded that the state
# does not already say). Pure stdlib, pure ASCII source.
import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "docs", "status-export.json")
sys.path.insert(0, os.path.join(ROOT, "src", "os"))

EXPORT_TS = "2026-10-29T21:40:00+08:00"
TICK = "2256"
TICK_BODY = "OSLoop 执行 tick"

DO = ("verification window R2256: the full reconcile battery and the "
      "suite-matrix regeneration re-proven on the committed tree with zero "
      "product code changed - RUNNER PASS 432/432 suites plus controls 7/7 "
      "in 852.6s, birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy=0 "
      "failed=0, matrix 432 suites / 3570 criteria read back byte-identical, "
      "fingerprint CLEAN over 5 domains, runner profile PASS, writer census "
      "DRIFT-CLEAN files=2196 flags=0; the R2255 round-evidence suite is now "
      "covered by the whole battery")

CURRENT = ("R2256 验证窗：R2255 新写的回合证据读数已由全量电池覆盖。实况=432/432 "
           "套件全绿 + 控制面 7/7，判据总数 3570（比 R2254 多 1 套件 6 判据，正是 "
           "R2255 那条新套件入册），出生站清理 932/932 世界回收 326.57 MiB，套件矩阵 "
           "432/3570 回读逐字节同一，指纹五域 CLEAN，写者普查 DRIFT-CLEAN。本轮零产品"
           "代码改动，是一轮只买回确定性的 0 分验证窗。")

LATEST = ("qa/reconcile-all-R2256.log（765306B，单写者 UTF-8 LF，含电池四段 "
          "follow-up 与 VERDICT PASS）；docs/sandbox-suite-matrix.md（42046B，"
          "432 套件 / 3570 判据，green=432/432）；src/os/battery_followup_R2256.py"
          "（新四段助手）；2026-10-29 21:4x")

NEXT = ("R2257：回到产品面——认领 tech 队头真活行，判据先写进队列行再写代码，"
        "出货一件可跑实物（预计 25 分钟内单面带套件与双跑证据）")

NEXT_DUE = "2026-10-30T12:00:00+08:00"

OUT = [
    "full reconcile battery and suite-matrix regeneration re-proven on the "
    "committed tree (R2256)",
    "on",
    "R2256: the register row that R2255 opened as first=yes is closed on the "
    "committed tree with zero product code changed (the R2168 mixed-tree "
    "rule). Full reconcile battery RUNNER PASS 432/432 suites green plus "
    "reconcile controls 7/7 in 852.6s with birth-site TMP RECLAIM 932/932 "
    "worlds 326.57 MiB busy=0 failed=0 (qa/reconcile-all-R2256.log, 765306B "
    "at RUNNER close, single-writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection), expected criteria "
    "total=3570. Four post-battery sections then all PASS through the new "
    "single-writer helper src/os/battery_followup_R2256.py: matrix "
    "regenerated to 432 suites / 3570 criteria and read back byte-identical "
    "(docs/sandbox-suite-matrix.md, 42046B, green=432/432), fingerprint "
    "chain CLEAN over 5 domains, runner profile --daily --check PASS "
    "byte-identical, writer census re-frozen then DRIFT-CLEAN files=2196 "
    "tee=1667 baselined=529 disappeared=0 flags=0, VERDICT PASS. The "
    "deltas against R2254 (431 suites / 3564 criteria) are +1 suite and +6 "
    "criteria, exactly the R2255 os-round-evidence suite joining the "
    "registry, so the newest slice is covered by the whole battery and not "
    "only by its own suite plus neighbours. Honest score: a 0-point "
    "verification window.",
]

RESULT = [
    "R2256",
    "R2256 verification window on the committed tree: RUNNER PASS 432/432 "
    "suites green plus controls 7/7 in 852.6s with birth-site TMP RECLAIM "
    "932/932 worlds 326.57 MiB busy=0 failed=0 (single-writer utf-8 LF "
    "through battery_stream.py), expected criteria total=3570; four "
    "follow-up sections all PASS via src/os/battery_followup_R2256.py - "
    "matrix 432 suites / 3570 criteria read back byte-identical (42046B, "
    "green=432/432), fingerprint CLEAN 5 domains, runner profile --daily "
    "--check PASS byte-identical, writer census re-frozen then DRIFT-CLEAN "
    "files=2196 tee=1667 baselined=529 flags=0. The +1 suite / +6 criteria "
    "against R2254 is exactly the R2255 os-round-evidence suite joining the "
    "registry. Register row reconcile-battery-R2256 closed, successor "
    "product-face-R2257 opened as first=yes. Zero product code changed: a "
    "0-point verification window.",
]


def load():
    with io.open(PATH, encoding="utf-8") as handle:
        return json.load(handle)


def store(doc):
    body = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    with io.open(PATH, "wb") as handle:
        handle.write(body.encode("utf-8"))
    return len(body.encode("utf-8"))


def main():
    doc = load()
    doc["export_ts"] = EXPORT_TS
    doc["do"] = DO
    face = doc["ceo_face"]
    face["current"] = CURRENT
    face["latest_artifact"] = LATEST
    face["last_artifact"] = "qa/reconcile-all-R2256.log（R2256·2026-10-29）"
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = NEXT_DUE
    if doc["outs"] and doc["outs"][0] and doc["outs"][0][0] == OUT[0]:
        doc["outs"][0] = OUT
    else:
        doc["outs"] = [OUT] + doc["outs"]
    if doc["results"] and doc["results"][0] and doc["results"][0][0] == "R2256":
        doc["results"][0] = RESULT
    else:
        doc["results"] = [RESULT] + doc["results"]
    # the tick row is identified by its body, never by its label (R2248b):
    # refuse unless exactly one row carries the pinned body.
    tick_rows = [r for r in doc["results"] if len(r) > 1 and r[1] == TICK_BODY]
    if len(tick_rows) != 1:
        print("E_EXP_TICK_ROWS %d" % len(tick_rows))
        return 3
    tick_rows[0][0] = TICK
    store(doc)

    # second pass: the self_drive counters are derived from the state log,
    # so they are read back through the checker's own recompute instead of
    # being incremented by hand.
    import check_export_consistency as cec
    derived, state, export, info = cec.recompute()
    doc = load()
    sd = doc.get("self_drive")
    if sd is None:
        print("E_EXP_NO_SELF_DRIVE")
        return 3
    sd.update(derived)
    size = store(doc)
    print("EXPORT OK bytes=%d outs=%d results=%d self_drive=%s"
          % (size, len(doc["outs"]), len(doc["results"]),
             json.dumps(derived, sort_keys=True)))
    return 0


if __name__ == "__main__":
    sys.exit(main())