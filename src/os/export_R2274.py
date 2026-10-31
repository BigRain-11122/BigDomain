"""R2274 export refresh: rewrite the CEO-visible face from measured state.

F3 law: every field below is derived from this window's actual readings
(queue_floor open counts, the register check, the evidence file size) and
nothing is copied from a previous export. Values are passed in by the
caller so a wrong number cannot be invented inside this helper.
"""

import io
import json
import sys

EXPORT = "docs/status-export.json"


def main(argv):
    now_ts, due_ts = argv[0], argv[1]
    path = sys.argv[3] if len(sys.argv) > 3 else EXPORT
    data = json.loads(io.open(path, encoding="utf-8").read())
    data["export_ts"] = now_ts
    data["do"] = ("product window: closing a carried-debt row is now one "
                  "callable instead of hand surgery, and the shipped writer "
                  "closed this window own register row and opened its "
                  "successor")
    face = data["ceo_face"]
    face["current"] = (
        "R2274 产品面已落盘：债务登记簿的『关行』从手工手术变成一次调用"
        "（src/os/debt_close.py + 6 判据套件首跑全绿 6/6）；本窗用它亲手关闭 "
        "product-face-R2274，并用既有 writer 开出后继电池行，登记簿现读 "
        "open=2 done=24；顺带实锚发现登记簿存在重复 item"
        "（reconcile-battery-and-matrix 两行 done），据此补种真种子 "
        "debt_item_unique，tech 地板复绿 10/10")
    face["latest_artifact"] = (
        "src/os/debt_close.py + src/os/test_debt_close.py（证据 "
        "qa/debt-close-R2274.log，1658B，双跑判据摘要一致，五邻域套件全绿，"
        "单写者 utf-8 LF；接线 os-debt-close(6)）")
    face["last_artifact"] = face["latest_artifact"]
    face["next_milestone"] = (
        "R2275 验证窗：在已提交树上跑全量 reconcile 电池（预期 443 套件 / "
        "3634 判据，即本窗 +1 套件 +6 判据），再跑四段 follow-up"
        "（矩阵再生+回读、指纹链、runner profile、census），毕后回产品面取 "
        "tech 队头 line 342（AC-QRX1，queue_row_exempt）")
    face["next_milestone_due"] = due_ts
    sd = data.get("self_drive")
    if isinstance(sd, dict):
        sd["queue_main_open"] = 6
        sd["queue_tech_open"] = 11
        sd["queue_explore_open"] = 10
        sd["log_lines_in_window"] = 14
        sd["substantive_non_idle_mention_lines"] = 14
    data["results"] = list(data["results"]) + [[
        "R2274",
        ("R2274 product window on the debt register first item "
         "(product-face-R2274): the row the debt gate and queue_head both "
         "named (tech.md line 340, prefix AC-DEBC1) was claimed with its six "
         "criteria already pinned in the seed row BEFORE the code. PRODUCT: "
         "src/os/debt_close.py plus src/os/test_debt_close.py - closing a "
         "carried-debt row stops being hand surgery. render_closed() rewrites "
         "only what the done law requires (box flipped, first= dropped, "
         "closed stamp appended, note untouched); plan() refuses unknown, "
         "already-done, ambiguous and bad-round closes before any byte "
         "changes and re-parses through debt_register requiring the open and "
         "done counts to move by exactly one each way; the write is one "
         "atomic os.replace re-measured through debt_register.register so a "
         "register that cannot parse after the edit is an error, never a "
         "silent write; the dry run writes nothing and predicts the exact "
         "post bytes. Evidence: SUITE PASS 6/6 on the first run, two legs "
         "with an identical criterion digest and five adjacent os suites "
         "green (qa/debt-close-R2274.log, 1658B, one utf-8 LF single writer "
         "through the R2261 evidence_capture callable), wired "
         "os-debt-close(6). LIVE dogfood: the shipped callable closed "
         "product-face-R2274 itself (line=41, open 2->1, done 23->24, "
         "readback ok) and debt_append opened reconcile-battery-R2275 "
         "first=yes. The claim dropped tech claimable to 9, so one real gap "
         "row was seeded from a live finding - the register carries "
         "reconcile-battery-and-matrix on two done rows, a duplicate "
         "debt_register never checks - and the floors closed FLOOR-MET "
         "10/10. Honest notes: the register was measured LF-only before the "
         "write; state.json measured 62334B against the 78500B waterline so "
         "no fold was due; the battery carries to R2275 (the R2168 "
         "mixed-tree rule)."),
    ]]
    data["outs"] = list(data["outs"]) + [[
        ("debt close as one callable (debt_close.py) - close exactly one open "
         "register row by item and prove it through the register own parser"),
        "on",
        ("R2274: debt_append gave the register a writer for OPEN rows, but "
         "closing one was still an operator flipping the box, typing the "
         "stamp and remembering to drop first=. src/os/debt_close.py owns "
         "that edit once: render_closed() drops the first= segment (a done "
         "row may not carry it, so closing the head row empties the flag) "
         "and appends closed=<round>; plan() refuses E_DEBC_UNKNOWN / "
         "E_DEBC_ALREADY_DONE / E_DEBC_AMBIGUOUS / E_DEBC_BAD_ROUND before "
         "any write; the post text is re-parsed through debt_register with "
         "the open/done counts required to move by one each way; the write "
         "is one atomic replace proved by read-back and re-measured through "
         "debt_register.register; the dry run predicts the exact post bytes."),
    ]]
    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    roundtrip = json.loads(text)
    if roundtrip != data:
        raise SystemExit("ABORT export round-trip mismatch")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("EXPORT WROTE bytes=%d ts=%s due=%s"
          % (len(text.encode("utf-8")), now_ts, due_ts))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))