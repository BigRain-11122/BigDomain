"""R2317 closeout: queue row, successor seed, state, export, heartbeat, board.

ASCII source; the Chinese CEO face lives in the JSON data file.

Usage: python src/os/closeout_R2317.py
"""

import datetime
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402
import state_io as SIO  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEART = os.path.join(ROOT, "heartbeat.txt")
BOARD = os.path.join(ROOT, "src", "os", "backlog.md")
QUEUE = os.path.join(ROOT, "state", "queue", "tech.md")

NOW = datetime.datetime.now().astimezone()
NOW_ISO = NOW.isoformat(timespec="seconds")
DUE = (NOW + datetime.timedelta(hours=48)).isoformat(timespec="seconds")

DONE_STAMP = "[done 2026-11-01 R2317]"

ROW_RESULT = (
    " " + DONE_STAMP + " CLAIMED this row after a fresh zero-occupancy anchor "
    "check at HEAD (the five anchors hit only the seed text and the R2312/R2316 "
    "closeout helpers, no product code path). DELIVERED: "
    "src/os/gate_decl_retire.py plus src/os/test_gate_decl_retire.py, wired "
    "os-gate-decl-retire(6). An identity that is not declared is refused "
    "(E_GDRT_UNDECLARED) and an entry the live machine_gate reading still "
    "reports as BLOCKED is refused (E_GDRT_STILL_BLOCKED) naming the field and "
    "the row line, both BEFORE any byte changes; the surviving entries are "
    "spliced out as text so each stays byte-intact, the post is re-parsed "
    "through machine_gate.read_declaration_text and must carry exactly one "
    "fewer entry with the removed identity absent, the plan is a dry run that "
    "writes nothing and reports before/after bytes plus the removed index, and "
    "execute performs one atomic os.replace with a read-back byte proof and no "
    "temp residue. SUITE PASS 6/6 twice with an identical criterion digest, "
    "four adjacent gate/queue suites green in the same capture, "
    "qa/gate-decl-retire-R2317.log 1245B as one utf-8 LF single writer through "
    "the evidence_capture callable. LIVE: the declared docker entry '-#02878cdc' "
    "reads PLANNED (declarations 1->0, bytes 427->222) and was NOT executed, "
    "disclosed as the finding below; an undeclared identity refuses E_GDRT_"
    "UNDECLARED at exit 2 and state/machine_gates.json stays byte-identical."
)

ROW_SEED = (
    "- [ ] P2 tech seed (R2317, from this window own live finding): "
    "`src/os/gate_decl_retire_wire.py` - the retire writer asks machine_gate's "
    "candidate reading, which only ever sees CLAIMABLE rows, so a declared "
    "entry whose row exists but carries no criteria prefix is INERT and can be "
    "retired while it is still the truth. Measured this window: the live docker "
    "entry '-#02878cdc' reads PLANNED for retirement (declarations 1->0) even "
    "though gate_decl_identity reports that same identity MATCHED at line 41. "
    "One wire that makes the retire writer ask gate_decl_identity FIRST, so "
    "UNMATCHED stays retirable, MATCHED and AMBIGUOUS refuse before any byte "
    "with the reader state and every carrier line named, and only an UNMATCHED "
    "identity reaches gate_decl_retire.plan - the same shape gate_decl_"
    "identity_wire already gives the append path. Criteria prefix AC-GDRTW1.."
    "AC-GDRTW6 pre-registered HERE BEFORE any code: AC-GDRTW1 the identity "
    "reading is imported from gate_decl_identity and the plan call from "
    "gate_decl_retire, never re-implemented, proven by patching each and "
    "watching the verdict move; AC-GDRTW2 MATCHED and AMBIGUOUS refuse before "
    "any byte with the reader state and every carrier line in the detail, while "
    "UNMATCHED alone reaches the plan; AC-GDRTW3 the refusal is the reader own "
    "state, never a widened identity rule, and a MATCHED identity that is not "
    "claimable still refuses; AC-GDRTW4 the success path is byte-identical to "
    "calling gate_decl_retire.plan directly; AC-GDRTW5 CLI exits 0 planned, 2 "
    "refused, 3 missing or unreadable, 5 bad flags, with a byte-stable --json "
    "over pinned keys; AC-GDRTW6 pure ASCII source, stdlib only, no network, no "
    "clock, plus its own reconcile label."
)

ROUND_LOG = (
    "2026-11-01 R2317 product window (five-silence scan clean at open: empty "
    "git status --short and no index.lock; decisions.md carried 84 non-empty "
    "rows equal to the stored baseline and the token diff read 57 tokens with "
    "ZERO new, so no decision row is owed; the group ledger carried the same "
    "three @BigDomain patrol rows already paid off, the last one P-20261026-0930 "
    "acked at R2311, with zero unreplied numbered handoffs; the group orders "
    "tail was unchanged at the 2026-10-31 18:23 baseline; benchmarks refreshed "
    "2026-10-29 inside the seven-day gate). P1 canonical rows stay blocked-on-CEO, "
    "the weekly proposal duty is met by BD-PROP-005, the floors read FLOOR-MET "
    "main 5/5 tech 11/10 explore 10/10, and the debt gate named exactly one "
    "first=yes row (product-face-R2317), so this window claimed the TOP "
    "deliverable tech row: state/queue/tech.md:376 prefix AC-GDRT1, the R2312 "
    "gate_decl_retire seed whose AC-GDRT1..AC-GDRT6 criteria were already pinned "
    "INSIDE that row BEFORE the code (fresh zero-occupancy anchor check at HEAD "
    "2026-11-01: gate_decl_retire / AC-GDRT / E_GDRT / os-gate-decl-retire / "
    "test_gate_decl_retire hit only the seed text and the R2312/R2316 closeout "
    "helpers, with no product code path). PRODUCT: src/os/gate_decl_retire.py "
    "plus src/os/test_gate_decl_retire.py - the declaration can now lose an entry "
    "as well as gain one. Before this window the only writer was gate_decl_append, "
    "so a completed row left its blocker declared forever and every retirement was "
    "a hand edit of a 427B JSON; the writer refuses an undeclared identity and an "
    "entry the live machine_gate reading still blocks BEFORE any byte changes, "
    "splices the entry out as text so every surviving entry stays byte-intact, "
    "re-parses the post through machine_gate.read_declaration_text requiring "
    "exactly one fewer entry and no trace of the removed identity, reports "
    "before/after bytes and the removed index as a dry run by default, and on "
    "execute performs one atomic os.replace with a read-back byte proof and no "
    "temp residue. The shape law is imported (entry keys, declaration keys and "
    "post reader from machine_gate; the live block reading is machine_gate.gate "
    "itself; the array span is gate_decl_append.array_span, so the file keeps one "
    "array law) and the suite proves each seam by patching it. SUITE PASS 6/6 on "
    "the first run, twice with an identical criterion digest, four adjacent "
    "gate/queue suites green in the same capture (machine_gate, gate_decl_append, "
    "gate_drift, queue_head), qa/gate-decl-retire-R2317.log 1245B as one utf-8 LF "
    "single writer through the evidence_capture callable, wired "
    "os-gate-decl-retire(6). LIVE: the declared docker entry '-#02878cdc' reads "
    "PLANNED (declarations 1->0, bytes 427->222, exit 0) and was NOT executed, "
    "and an undeclared identity refuses E_GDRT_UNDECLARED at exit 2, with "
    "state/machine_gates.json proved byte-identical afterwards. One tech row "
    "closed and one successor seed added (gate_decl_retire_wire, "
    "AC-GDRTW1..AC-GDRTW6), so claimable stays 11."
)

TOKENS_LOG = (
    "R2317 tokens: local=~21k api=0 api_reason=product window on the debt "
    "register first item - one writer module with its six pre-registered "
    "criteria and its suite green on the first run, one dogfooded evidence "
    "capture (two legs identical, four adjacent suites green), two live CLI "
    "readings of the real declaration with the file proved byte-identical, one "
    "runner wiring line, one queue close and one successor seed through the "
    "shipped queue law, one waterline fold, one write-canon repair and the "
    "state/export/heartbeat/board closeout; zero cloud calls and zero external "
    "API touches; the battery carries to R2318"
)

SELF_HEAL = (
    "R2317 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply it, and this "
    "session runs unelevated, so the definition of the loop hosting this window "
    "was left untouched. Open local-lane item for an elevated window "
    "(seventy-eighth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

HONEST = (
    "R2317 honest disclosures: (a) the LIVE reading is a finding and not a "
    "green claim: the declared docker entry '-#02878cdc' reads PLANNED for "
    "retirement because machine_gate only ever reports a CLAIMABLE row as "
    "BLOCKED, and the live docker row carries no criteria prefix so it is never "
    "a candidate - the declaration is INERT by that law while gate_decl_identity "
    "reports the same identity MATCHED at line 41 (the R2314 asymmetry). The "
    "writer is honest to its pre-registered criterion (it asks machine_gate) and "
    "the entry was NOT retired; the gap is the successor seed, not a defect "
    "swept under a plan. (b) state.json was found off the write canon at open "
    "(74802B, crlf=0, 67 bare LF, 57 log items off the 16-space indent, left by "
    "the R2316 closeout) and was repaired through state_io --fix BEFORE any "
    "append: 75553B CANON-CLEAN with the JSON payload proved equal. (c) The "
    "fold ran before the append because the closeout would have crossed the "
    "78500B waterline at margin 2947B: fold 616 over log lines 2..8 (the whole "
    "R2302 and R2303 blocks, never the line-1 fold marker, whose token list "
    "would otherwise have to be re-named) with 8 window tokens covered, "
    "predicted 67870B equal to measured 67870B, margin 10630B, archive appendix "
    "verbatim and pre-op sha16 51e6048fabeb8efd. (d) The full reconcile battery "
    "did NOT run here (the R2168 mixed-tree rule keeps it on a committed tree), "
    "so it is the R2318 first item with the pre-registered target of +1 suite / "
    "+6 criteria against R2316. (e) tasks.md was left untouched: it is the "
    "P-47 canonical board and carries no row for this tech slice, disclosed "
    "rather than silently skipped. (f) queue_row --check and queue_done_stamp "
    "--check still read GATE-DEBT and DONE-STAMP-DEBT over the legacy rows that "
    "predate those laws; this window's own closed row carries a dated window "
    "stamp and lands on the ok side, so the debt is inherited and named, not "
    "added."
)

EXPORT_DO = (
    "R2317 产品轮：门声明终于可退役。state/machine_gates.json 此前只能加条目"
    "（gate_decl_append）、永远不能减，行完成后阻塞项永久留在声明里只读 INERT，"
    "退役只能手改 JSON。本轮交付 src/os/gate_decl_retire.py + 套件（6 判据预注册"
    "于队列行、先于代码）：未声明身份与仍在阻塞的条目都在动任何字节之前被拒；"
    "存活条目按文本切出、逐字节不动；写回前重解析并要求恰好少一条且被删身份消失；"
    "默认干跑只报前后字节与删除下标，执行时一次原子替换 + 回读字节证明 + 零临时残留。"
    "实测：真实声明里 docker 条目读 PLANNED（1→0 条、427→222 字节），本轮未执行；"
    "未声明身份被拒 E_GDRT_UNDECLARED；声明文件事后逐字节未变。"
)

EXPORT_CURRENT = (
    "R2317 产品轮完成：门声明退役写入器上线，套件 6/6 双跑判据行同一、四邻域门/队列"
    "套件同捕获全绿，证据 qa/gate-decl-retire-R2317.log（1245B 单写者 utf-8 LF）；"
    "真实声明未被改动（干跑），环境面未变：orders 尾 2026-10-31 18:23、decisions 无新行、"
    "台账开项仍只剩 S4U 重注册一项（需提权窗口）；队列关一条、补一条后继种子，"
    "技术队列可认领仍 11（地板 10）。"
)

EXPORT_ARTIFACT = (
    "src/os/gate_decl_retire.py + src/os/test_gate_decl_retire.py + "
    "qa/gate-decl-retire-R2317.log（1245B·6/6 双跑同一 + 4 邻域全绿），2026-11-01"
)

EXPORT_NEXT = (
    "R2318 先跑提交树上的全量对账电池（R2168 混合树律·本窗改动必须先落库），"
    "预注册目标=相对 R2316 增 1 套件 / 6 判据；随后按债务闸与队列头取门声明退役接线"
    "（AC-GDRTW1..6 pre-registered）"
)

BOARD_TOP = (
    "- [ ] R2317 first item: THE BATTERY ON THE COMMITTED TREE, zero product "
    "edits until green (the R2168 mixed-tree rule). R2317 changed src/os "
    "(gate_decl_retire.py, test_gate_decl_retire.py, wire_R2317.py, "
    "fold_R2317.py), one runner entry, the tech queue (one row closed and one "
    "successor seed added), state.json (canon repair plus fold 616), the export, "
    "the heartbeat and the board, so run the full reconcile battery with an "
    "empty git status before the run, expecting exactly +1 suite / +6 criteria "
    "against R2316 from this window os-gate-decl-retire suite - measure it and "
    "disclose any delta that does not resolve to a named suite. Then the four "
    "follow-up sections through src/os/battery_followup.py: the matrix section "
    "will FAIL first on the stale doc and must NOT rewrite it, so regenerate "
    "with src/sandbox/suite_matrix.py and re-run. After that re-read the product "
    "face live: `python src/os/gate_decl_retire.py --identity '-#02878cdc'` must "
    "still read PLANNED with the declaration byte-identical (the wire seed "
    "AC-GDRTW1 explains why PLANNED is the honest reading), and read the seeded "
    "row with `python src/os/queue_head.py --head tech` rather than trusting "
    "this line. Also open and needing an ELEVATED shell: BigDomain-OSLoop reads "
    "LogonType=InteractiveToken (seventy-ninth consecutive disclosure; carried "
    "as loop-s4u-reconcile in state/debt.md).\n"
)


def write_text(path, text):
    """Atomic utf-8 write with a read-back proof."""
    data = text.encode("utf-8")
    temp = path + ".r2317-tmp"
    with io.open(temp, "wb") as handle:
        handle.write(data)
    os.replace(temp, path)
    with io.open(path, "rb") as handle:
        if handle.read() != data:
            raise SystemExit("E_CLOSE_READBACK %s" % path)


def close_queue_row():
    """Flip the claimed row to done and insert the successor seed after it."""
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    target = None
    for index, line in enumerate(lines):
        if line.startswith("- [ ] P2 tech seed (R2312") \
                and "gate_decl_retire.py" in line:
            target = index
            break
    if target is None:
        raise SystemExit("E_CLOSE_NO_ROW")
    row = lines[target]
    if not row.startswith("- [ ] "):
        raise SystemExit("E_CLOSE_BAD_ROW")
    closed = "- [x] " + DONE_STAMP + row[len("- [ ] "):] + ROW_RESULT
    lines[target] = closed
    lines.insert(target + 1, ROW_SEED)
    write_text(QUEUE, nl.join(lines))
    print("queue: closed line %d, seeded line %d" % (target + 1, target + 2))


def append_state():
    """Append the four log items and bump the tick through the canon writer."""
    with io.open(STATE, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    data["tick"] = 2317
    data["log"].extend([ROUND_LOG, TOKENS_LOG, SELF_HEAL, HONEST])
    raw = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    write_text(STATE, raw.replace("\n", "\r\n"))
    SIO.fix(STATE, execute=True)
    report = SIO.report(STATE)
    if not report["layout_ok"]:
        raise SystemExit("E_CLOSE_LAYOUT %r" % report)
    print("state: tick=%d log=%d bytes=%d CANON-CLEAN"
          % (data["tick"], len(data["log"]), report["bytes"]))


def update_export():
    """Refresh the CEO-visible face and recompute self_drive from live data."""
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        export = json.load(handle)
    export["export_ts"] = NOW_ISO
    export["do"] = EXPORT_DO
    face = export["ceo_face"]
    face["current"] = EXPORT_CURRENT
    face["latest_artifact"] = EXPORT_ARTIFACT
    face["last_artifact"] = EXPORT_ARTIFACT
    face["next_milestone"] = EXPORT_NEXT
    face["next_milestone_due"] = DUE
    export["outs"].insert(0, [
        "qa/gate-decl-retire-R2317.log",
        "on",
        "R2317 product face shipped: the gate declaration can finally lose an "
        "entry. gate_decl_retire imports machine_gate's entry keys, declaration "
        "keys, post reader and live block reading plus gate_decl_append's array "
        "span, refuses an undeclared identity and a still-blocking entry before "
        "any byte changes, splices the entry out as text so every surviving "
        "entry stays byte-intact, re-parses requiring exactly one fewer entry, "
        "and is a dry run by default with one atomic replace, a read-back byte "
        "proof and no temp residue; suite 6/6 twice with four adjacent gate/queue "
        "suites green (1245B, one utf-8 LF single writer). LIVE: the docker "
        "entry reads PLANNED (1->0, 427->222 bytes) and was NOT executed because "
        "machine_gate only reports CLAIMABLE rows as blocking - the honest "
        "asymmetry that seeded gate_decl_retire_wire (AC-GDRTW1..AC-GDRTW6).",
    ])
    export["results"].insert(0, [
        "R2317",
        "product window on the debt register first item: state/machine_gates.json "
        "had a reader, a drift reader and an append writer but no way to lose an "
        "entry, so a completed row's blocker stayed declared forever and every "
        "retirement was a hand edit; the new writer refuses an undeclared "
        "identity and an entry the live reading still blocks before any byte, "
        "splices as text with survivors byte-intact, re-parses to exactly one "
        "fewer entry, and lands one atomic replace with a read-back proof; suite "
        "6/6 twice plus four adjacent suites green, live reading PLANNED on the "
        "real declaration with the file proved byte-identical and one successor "
        "seed added; state.json canon drift from R2316 repaired through state_io "
        "and fold 616 ran before the append (67870B predicted equal to measured)",
    ])
    derived, _state, _export, _pat = CEC.recompute()
    export["self_drive"] = derived
    raw = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    write_text(EXPORT, raw)
    print("export: refreshed, self_drive recomputed (%d keys)" % len(derived))


def update_heartbeat():
    """Append one tick line."""
    line = ("tick 2317 2026-11-01 R2317 product window: the gate declaration can "
            "finally lose an entry - src/os/gate_decl_retire.py refuses an "
            "undeclared identity and a still-blocking entry before any byte, "
            "splices one entry out as text with every survivor byte-intact, "
            "re-parses to exactly one fewer entry, and is a dry run by default "
            "with one atomic replace and a read-back proof; SUITE PASS 6/6 twice "
            "with four adjacent gate/queue suites green (qa/gate-decl-retire-"
            "R2317.log 1245B, one utf-8 LF single writer), wired "
            "os-gate-decl-retire(6). LIVE: the real docker entry reads PLANNED "
            "(1->0, 427->222) and was NOT executed - machine_gate only reports "
            "CLAIMABLE rows as blocking, which seeded gate_decl_retire_wire. "
            "state.json canon drift from R2316 was repaired through state_io "
            "(75553B CANON-CLEAN) and fold 616 moved the R2302+R2303 blocks "
            "(67870B predicted equal to measured); the battery carries to R2318.\n")
    with io.open(HEART, "r", encoding="utf-8") as handle:
        text = handle.read()
    if not text.endswith("\n"):
        text += "\n"
    write_text(HEART, text + line)
    print("heartbeat: appended tick 2317")


def update_board():
    """Insert the next first item at the top of the claim board."""
    with io.open(BOARD, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    row = BOARD_TOP.replace("\n", nl)
    if not text.startswith("- [ ] R2317 first item"):
        text = row + text
    write_text(BOARD, text)
    print("board: top item inserted")


def main():
    close_queue_row()
    append_state()
    update_export()
    update_heartbeat()
    update_board()


if __name__ == "__main__":
    main()