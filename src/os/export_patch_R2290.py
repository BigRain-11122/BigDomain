import io
import json
import os
from datetime import datetime, timedelta, timezone

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
now = datetime.now(timezone(timedelta(hours=8))).replace(microsecond=0)
iso = now.isoformat()
due = (now + timedelta(hours=48)).isoformat()

patch = {
    "export_ts": iso,
    "do": ("product window on the debt register first item: "
           "src/os/debt_item_unique.py and its suite turn 'is this item "
           "carried by more than one register row' into a reading, with the "
           "row law imported from debt_register and live debt carried twice "
           "separated from history kept twice"),
    "current": (
        "R2290 产品窗：债务登记簿 first=yes 点名的队头 state/queue/tech.md:357"
        "（前缀 AC-DIU1，AC-DIU1..AC-DIU6 判据已先于代码钉在该行）已认领并交付。"
        "新件 src/os/debt_item_unique.py + src/os/test_debt_item_unique.py："
        "「同一 item 是否被多行承载」此前无人问——登记簿只查行形与唯一 first，"
        "活册里 reconcile-battery-and-matrix 就挂在两行完成行上，"
        "「登记簿对这个 item 怎么说」取决于读者拿的是哪一行，debt_close 的"
        " ALREADY-DONE 与 AMBIGUOUS 两种拒绝还可能对同一个名字同时成立。"
        "读取器把行律从 debt_register 导入（套件打补丁 parse 证明不是二次实现），"
        "每个重复项连同其全部行（状态/开启/关闭/行号）一并报出，并在类别上分离："
        "组内任一开放行=DUP-OPEN（同一活债记两次），全为完成行=DUP-DONE"
        "（历史存两次），判决从不合并。实测 DEBT ITEM UNIQUE rows=41 "
        "duplicate_items=1 dup_open=0 dup_done=1 verdict=DUPLICATES；"
        "套件 SUITE PASS 6/6 双跑判据行同一（digest B9C7FE01D456C65B）。"),
    "latest_artifact": (
        "qa/debt-item-unique-R2290.log（@EVIDENCE_BYTES@，单写者 utf-8 LF，"
        "经 src/os/evidence_capture.py 双跑同判据，同批五个债务/队列邻域套件"
        "全绿）+ 新件 src/os/debt_item_unique.py、src/os/test_debt_item_unique.py；"
        "收口折叠 fold 598（日志 60→57 项，state 75777B，水面线 78500B 下留 2723B）；"
        "导出时间 " + iso[:16].replace("T", " ") + " +08:00"),
    "next_milestone": (
        "R2291 验证窗：在已提交树上跑全量 reconcile 电池（登记簿登记时预注册预期为"
        " 451 套件 / 3682 判据，即较 R2289 的 450/3676 恰 +1 套件 / +6 判据），"
        "随后四段跟进（矩阵再生+回读、指纹链、runner profile、writer census）；"
        "矩阵段会先在过期文档上 FAIL 且不得改写它，重新生成后再跑是设计顺序。"
        "截止 " + due[:16].replace("T", " ") + " +08:00（48 小时内）。"),
    "next_milestone_due": due,
    "drop_labels": [],
    "results": [
        "R2290",
        ("R2290 product window on the debt register first item "
         "(product-face-R2290): claimed the tech head the reader named, the "
         "R2274 debt_item_unique seed at state/queue/tech.md:357 prefix "
         "AC-DIU1, its AC-DIU1..AC-DIU6 criteria already pinned in that row "
         "BEFORE the code, after a fresh zero-occupancy anchor check at HEAD "
         "(E_DIU, os-debt-item-unique, test_debt_item_unique and "
         "debt_item_unique were git grep -F rc 1; every hit was prose). "
         "PRODUCT: src/os/debt_item_unique.py plus "
         "src/os/test_debt_item_unique.py. debt_register checks each row "
         "shape and allows at most one open first=yes but never asks whether "
         "an ITEM repeats, so the live register carries "
         "reconcile-battery-and-matrix on duplicate rows and a reader had to "
         "guess which duplicate answered for the item; debt_close's own "
         "ALREADY-DONE and AMBIGUOUS refusals could both fire for one name. "
         "The reader takes the row law from debt_register (parse asked, "
         "never re-implemented, proven by patching parse so a renamed item "
         "flows straight through), reports every duplicate with every one of "
         "its rows (state, opened, closed, line), and separates the two "
         "classes on whether any row is still open: any open row reads "
         "DUP-OPEN (live debt tracked twice), an all-done group reads "
         "DUP-DONE (history kept twice), and the verdict never merges them. "
         "UNIQUE is honest at exit 0, EMPTY at exit 0, and an absent, "
         "unreadable or malformed register fails closed at exit 3 with its "
         "own code rather than reading UNIQUE; the reader writes nothing and "
         "reads no clock. SUITE PASS 6/6 double-run identical criterion "
         "digest B9C7FE01D456C65B (qa/debt-item-unique-R2290.log, 1535B, "
         "single writer utf-8 LF through the R2261 evidence_capture "
         "callable, five adjacent debt and queue suites green in the same "
         "capture), wired os-debt-item-unique(6). LIVE: DEBT ITEM UNIQUE "
         "rows=41 duplicate_items=1 dup_open=0 dup_done=1 "
         "verdict=DUPLICATES - the duplicate is reconcile-battery-and-matrix "
         "on two done rows, exactly the case the seed was found from. The "
         "claim left tech claimable at 10 against its floor of 10, so no gap "
         "row was due and the gauge closed FLOOR-MET main 5/5 tech 10/10 "
         "explore 10/10. CLOSEOUT DEFECT FOUND AND REPAIRED: the append "
         "crossed the waterline, and the first fold window (1..3) split the "
         "R2270 block - its narrative and ledger went to the archive while "
         "its self-heal line stayed live, so ledger_lines read "
         "rounds_without_ledger=2270 and four ledger suites went red (7/8, "
         "6/8, 7/8). Reverted byte-exact from logs/state-preop-R2290.bak "
         "with the archive trimmed back to 4908578B, then refolded as fold "
         "598 over the whole block (lines 1..4) with all 565 window tokens "
         "covered; predicted_eq_actual true, state 74605B then 75777B after "
         "the disclosure item, all four ledger suites 8/8 and the live gate "
         "VERDICT CLEAN. The first attempt also derived a bogus fold number "
         "from a byte count (78496); the repair reads real archive headers "
         "instead (597 -> 598). Honest score: 2 product points; the battery "
         "carries to R2291 as the register successor row."),
    ],
}

path = os.path.join(ROOT, "state", "export_patch_R2290.json")
body = json.dumps(patch, ensure_ascii=False, sort_keys=False, indent=2) + "\n"
io.open(path, "wb").write(body.encode("utf-8"))
back = json.loads(io.open(path, "rb").read().decode("utf-8"))
assert back["export_ts"] == iso and back["results"][0] == "R2290"
print("patch written: %s (%d bytes)" % (path, len(body.encode("utf-8"))))
print("export_ts=%s due=%s" % (iso, due))