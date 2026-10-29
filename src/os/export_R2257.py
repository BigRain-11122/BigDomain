# export_R2257.py - refresh the CEO-visible face for round R2257.
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

EXPORT_TS = "2026-10-29T13:51:00+08:00"
TICK = "2257"
TICK_BODY = "OSLoop 执行 tick"

DO = ("product window R2257: the R2248 d seed shipped as src/os/state_seq.py - "
      "the round sequence (the tick, the log items' own round labels and the "
      "queues' done stamps) is now a reading, so a skipped round, a reused "
      "label or a label that goes backwards can no longer hide behind a log "
      "that looks the same either way; SUITE PASS 6/6 double-run "
      "byte-identical criterion sha16 93B363F778BE65E1, five adjacent os "
      "suites green (fails=0), wired os-state-seq(6); the live gate reads "
      "SEQUENCE-OK gaps=0 repeats=0 backwards=0 tick_lead=0 over 16 distinct "
      "rounds and its first live read found 156 queue done stamps carrying no "
      "log item, which is seeded as the next real row instead of being swept")

CURRENT = ("R2257 产品窗：出货一件可跑实物——回合序列读数器 src/os/state_seq.py"
           "（tick / 日志各条自己的回合号 / 队列 done 戳三面对照）。判据 AC-SEQ1..6 "
           "先写进队列行再写代码，锚检 HEAD 零占用；套件 6/6 全绿双跑判据行逐字节"
           "同一，五个相邻套件零回归，已接线 os-state-seq(6)。活闸实况="
           "SEQUENCE-OK：16 个回合号、跨 2242..2257、缺口 0、重复 0、倒序 0、"
           "tick 与最大回合号恰好对齐（tick_lead=0）。首读即抓到真问题：156 条"
           "队列 done 戳没有对应日志行——已如实登记为下一活行，不扫掉不掩盖。")

LATEST = ("qa/state-seq-R2257-a.log 与 -b.log（各 478B，SUITE PASS 6/6 双跑"
          "逐字节同一，单写者 UTF-8 LF）；qa/regression-R2257.log（五个相邻"
          "os 套件 fails=0）；src/os/state_seq.py（产品件）；"
          "src/os/test_state_seq.py（6 判据套件）；2026-10-29 13:5x")

NEXT = ("R2258：清验证债——在已提交树上跑全量电池（zero product code changed，"
        "R2168 混合树律），随后再生套件矩阵并回读逐字节同一")

NEXT_DUE = "2026-10-30T12:00:00+08:00"

OUT = [
    "round sequence reader: the tick, the log's own round labels and the "
    "queues' done stamps compared (R2257)",
    "on",
    "R2257: src/os/state_seq.py reads the tick as an int with tick_lead = tick "
    "- largest label and fails closed (E_SEQ_BAD_STATE, exit 3) instead of "
    "fabricating one, counts only each log item's OWN round label by importing "
    "the round_evidence law rather than re-implementing it, lists gaps inside "
    "the known span only (nothing invented before the first or after the last "
    "round), and reports repeats and backwards as separate readings. Criteria "
    "AC-SEQ1..AC-SEQ6 were pinned in state/queue/tech.md as the R2248 d seed "
    "BEFORE the code, with a zero-occupancy anchor check at HEAD (E_SEQ / "
    "os-state-seq / test_state_seq rc=1). Evidence: SUITE PASS 6/6 double-run "
    "byte-identical criterion sha16 93B363F778BE65E1 (qa/state-seq-R2257-a.log "
    "and -b.log, 478B each, single writer utf-8 LF through "
    "src/os/evidence_R2257.py, never a shell redirection), five adjacent os "
    "suites green (qa/regression-R2257.log, fails=0), wired os-state-seq(6). "
    "Live reading at closeout: labels=48 distinct=16 span=2242..2257 gaps=0 "
    "repeats=0 backwards=0 tick=2257 tick_lead=0 queue_done=164 queue_only=156 "
    "verdict=SEQUENCE-OK. Honest disclosure: the first AC-SEQ4 wording (labels "
    "written more than once) was falsified by its own live gate - a round "
    "legitimately writes several items in a row, so 15 of 15 rounds flagged; "
    "the implemented law now reads a repeat as a label returning after a "
    "DIFFERENT round intervened, the suite pins both sides and no assertion "
    "was relaxed.",
]

RESULT = [
    "R2257",
    "R2257 product window: the R2248 d seed shipped as src/os/state_seq.py with "
    "AC-SEQ1..AC-SEQ6 pinned in state/queue/tech.md BEFORE the code and a "
    "zero-occupancy anchor check at HEAD. SUITE PASS 6/6 double-run "
    "byte-identical criterion sha16 93B363F778BE65E1 (qa/state-seq-R2257-a.log "
    "and -b.log, 478B each, single writer utf-8 LF through "
    "src/os/evidence_R2257.py), five adjacent os suites green "
    "(qa/regression-R2257.log, fails=0), wired os-state-seq(6). Live gate: "
    "STATE SEQUENCE labels=48 distinct=16 span=2242..2257 gaps=0 repeats=0 "
    "backwards=0 tick=2257 tick_lead=0 queue_done=164 queue_only=156 "
    "verdict=SEQUENCE-OK. First live read produced two real findings carried "
    "instead of swept: 156 queue done stamps have no log item (the log window "
    "is folded to 15 rounds) and tick_lead is 0. The AC-SEQ4 wording was "
    "corrected at the gate from 'written more than once' to 'returns after a "
    "different round intervened' - disclosed, no assertion relaxed. Tech floor "
    "refilled in the same window with one real gap row (queue_only_reconcile, "
    "AC-QOC1..6 pre-registered, five anchors zero-occupancy rc=1), gauge "
    "FLOOR-MET main 5/5 tech 10/10 explore 10/10. Register row "
    "product-face-R2257 closed, successor reconcile-battery-R2258 opened as "
    "first=yes.",
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
    face["last_artifact"] = "qa/state-seq-R2257-a.log（R2257·2026-10-29）"
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = NEXT_DUE
    if doc["outs"] and doc["outs"][0] and doc["outs"][0][0] == OUT[0]:
        doc["outs"][0] = OUT
    else:
        doc["outs"] = [OUT] + doc["outs"]
    if doc["results"] and doc["results"][0] and doc["results"][0][0] == "R2257":
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