"""R2321 closeout: queue row, debt, state, export, heartbeat, board.

This window shipped the product face the debt gate named: the retirement
scope reading, so a declared blocker whose row was COMPLETED can finally be
retired while a matched OPEN or GATED row keeps refusing by level.

ASCII source; the Chinese CEO face lives in docs/status-export.json.

Usage: python src/os/closeout_R2321.py
"""

import datetime
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402
import debt_append as DA  # noqa: E402
import state_fold as SF  # noqa: E402
import state_io as SIO  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEART = os.path.join(ROOT, "heartbeat.txt")
BOARD = os.path.join(ROOT, "src", "os", "backlog.md")
TECH = os.path.join(ROOT, "state", "queue", "tech.md")
DEBT = os.path.join(ROOT, "state", "debt.md")

NOW = datetime.datetime.now().astimezone()
NOW_ISO = NOW.isoformat(timespec="seconds")
DUE = (NOW + datetime.timedelta(hours=44)).isoformat(timespec="seconds")

ROUND_LOG = (
    "2026-11-01 R2321 product window (five-silence scan clean at open: empty "
    "git status --short and no index.lock; decisions.md carried 84 non-empty "
    "rows equal to the stored baseline and the token diff read 57 tokens with "
    "ZERO new, so no decision row is owed; the group ledger carried the same "
    "three @BigDomain patrol rows already paid off, the last one P-20261026-0930 "
    "acked at R2311, with zero unreplied numbered handoffs; the group orders "
    "tail carried ONE new line dated 2026-11-01 10:4x, the fleet model and "
    "execution policy order OB-20261101-104744-MODELPOLICY-IGNITE, which names "
    "bm-a/bm-b/bm-c/bm-m machine lanes and no BigDomain execution surface, so it "
    "is acknowledged here by number as non-execution for this company; "
    "benchmarks refreshed 2026-11-01 inside the seven-day gate; the QA charter "
    "daily crawl face was already PASS with today's smoke evidence). The P1 "
    "canonical rows stay blocked-on-CEO, the weekly proposal duty is met by "
    "BD-PROP-005, the floors read FLOOR-MET main 5/5 tech 11/10 explore 10/10, "
    "and the debt gate named exactly one first=yes row (product-face-R2321), so "
    "this window claimed the TOP deliverable tech row: state/queue/tech.md:378 "
    "prefix AC-GDRTS1, the R2319 gate_decl_retire_scope seed whose "
    "AC-GDRTS1..AC-GDRTS6 criteria were already pinned INSIDE that row BEFORE "
    "the code (recorded in that row, re-read not re-run). PRODUCT: "
    "src/os/gate_decl_retire_scope.py plus src/os/test_gate_decl_retire_scope.py "
    "- the retire wire refused every MATCHED identity, so a declared blocker "
    "whose row was COMPLETED could never be retired: AC-GDRTW3 had measured the "
    "gated fixture and the done fixture refusing identically, while "
    "gate_decl_retire would legitimately offer both once machine_gate reads them "
    "INERT. The new reader maps one identity reading to a scope verdict: a "
    "matched DONE row is RETIRE-ALLOWED and reaches gate_decl_retire.plan, a "
    "matched OPEN or GATED row is RETIRE-REFUSED before any byte with its level "
    "in the detail, AMBIGUOUS keeps refusing with every carrier named, and "
    "UNMATCHED keeps reaching the plan. Both laws are imported, never "
    "re-implemented: the suite patches GDI.resolve, GDI.rows and GDRT.retire in "
    "turn and watches the verdict move, and proves no second queue scan exists "
    "in the source. SUITE PASS 6/6 twice with an identical criterion digest "
    "5A79F29593F8BC33, four adjacent gate suites green (retire 6/6, "
    "retire_wire 6/6, identity 6/6, append 6/6), qa/gate-decl-retire-scope-"
    "R2321.log 1324B as one utf-8 LF single writer through the evidence_capture "
    "callable, one runner wiring line. LIVE READING OF THE REAL DECLARATION: the "
    "single declared identity '-#02878cdc' resolves MATCHED at level open on "
    "line 41, so the new scope reading REFUSES it E_GDRTS_MATCHED at exit 2 "
    "naming the level, and state/machine_gates.json stays 427B / sha256-16 "
    "10EF269E byte-identical - the honest negative case, with the positive done "
    "case proven on fixture worlds. One tech row closed; claimable tech reads 10 "
    "against a floor of 10 with NO successor seed, because the claim landed "
    "exactly on the floor rather than below it."
)

TOKENS_LOG = (
    "R2321 tokens: local=~15k api=0 api_reason=product window on the debt "
    "register first item - one scope reader module with its six pre-registered "
    "criteria and its suite (green after one this-window test assertion was "
    "corrected against the measured truth), one dogfooded evidence capture (two "
    "legs identical, four adjacent suites green), two live CLI readings of the "
    "real declaration with the file proved byte-identical, one runner wiring "
    "line, one queue close through the shipped law, one debt close and one "
    "register append, and the state/export/heartbeat/board closeout; zero cloud "
    "calls and zero external API touches; the battery carries to R2322"
)

SELF_HEAL = (
    "R2321 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply it, and this "
    "session runs unelevated, so the definition of the loop hosting this window "
    "was left untouched. Open local-lane item for an elevated window "
    "(eighty-third consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

HONEST = (
    "R2321 honest disclosures: (a) the first suite run was red on AC-GDRTS4 "
    "alone, and the red was a this-window TEST assertion, never the module: the "
    "criterion asserted the fixture prefixes 'AC-GAT1' and 'AC-DON1' would appear "
    "in the surviving declaration, but a row's identity renders as '-#<digest>' "
    "under machine_gate.identity_of when its criteria prefix does not parse, so "
    "the honest assertion is on the DECLARED identity strings; the criterion was "
    "corrected to name GATED_ID and MISSING_ID present and DONE_ID absent, and "
    "no criterion was widened or dropped. (b) The live reading is a refusal by "
    "design and is disclosed as such: the only declared identity sits on an OPEN "
    "row, so no honest done-row retirement can be performed live and the "
    "positive path is proven on fixture worlds instead. (c) The debt register "
    "reports the carried loop-s4u-reconcile row as stale (carried=90) before "
    "this window's close; it still needs an elevated shell and was not touched. "
    "(d) The full reconcile battery did NOT run here (the R2168 mixed-tree rule "
    "keeps it on a committed tree), so the successor carries it with the "
    "pre-registered target of 468 suites / 3784 criteria - exactly +1 suite / +6 "
    "criteria against R2320 (467/3778) from this window's own "
    "os-gate-decl-retire-scope suite. (e) tasks.md was left untouched: it is the "
    "P-47 canonical board and carries no row for this tech slice, disclosed "
    "rather than silently skipped. (f) No successor seed was added: the tech "
    "claimable count falls 11 -> 10, which is exactly the floor, so seeding "
    "'to be safe' would be filler rather than answering a measured gap."
)

EXPORT_DO = (
    "R2321 产品窗：给门声明退役一个「作用域」判读。R2319 的退役接线对一切 MATCHED "
    "身份一律拒绝，于是一个「载体行已经完成」的声明条目永远退不掉（AC-GDRTW3 实测："
    "gated 夹具与 done 夹具的拒绝完全一致）。本轮交付 src/os/gate_decl_retire_scope.py："
    "把身份读面的一次读解映射成作用域判定——载体行是 done 的 MATCHED 才进退役规划，"
    "open / gated 的 MATCHED 在动任何字节之前拒绝并点名层级，AMBIGUOUS 继续拒绝并点"
    "名全部承载行，UNMATCHED 继续进规划。层级与计划调用都是导入而非复制。"
)

EXPORT_CURRENT = (
    "R2321 产品窗完成：门声明退役作用域 src/os/gate_decl_retire_scope.py 落盘并接线，"
    "套件 6/6 双腿全绿（判据摘要 5A79F29593F8BC33 一致）、四套相邻门套件同时绿，证据 "
    "qa/gate-decl-retire-scope-R2321.log（1324B）。活声明实测：唯一声明身份 "
    "'-#02878cdc' 落在 line 41 的 open 行，作用域判定如实拒绝 E_GDRTS_MATCHED 并点名 "
    "level open，machine_gates.json 保持 427B 字节不变。技术队列可认领 10（地板 10）。"
)

EXPORT_ARTIFACT = (
    "src/os/gate_decl_retire_scope.py（+ 测试套件 6 判据）与 "
    "qa/gate-decl-retire-scope-R2321.log（1324B·双腿一致·四套相邻全绿），2026-11-01"
)

EXPORT_NEXT = (
    "R2322 验证轮：在已提交树上跑全量对账电池（预注册目标 468 套件 / 3784 判据 = "
    "相对 R2320 的 467/3778 恰好 +1 套件 / +6 判据），矩阵重生成后四段随访必须全 PASS；"
    "随访后回产品面，接技术队头现役种子"
)

BOARD_DONE = (
    " [done 2026-11-01 R2321 - the retirement scope reading: "
    "src/os/gate_decl_retire_scope.py maps one identity reading onto a scope "
    "verdict, so a matched DONE row finally reaches gate_decl_retire.plan while a "
    "matched OPEN or GATED row refuses before any byte with its level named, "
    "AMBIGUOUS keeps refusing with every carrier and UNMATCHED keeps planning; "
    "the row level is imported from gate_decl_identity.rows and the plan call "
    "from gate_decl_retire (the suite patches GDI.resolve, GDI.rows and "
    "GDRT.retire in turn) and no second queue scan exists. SUITE PASS 6/6 twice "
    "with an identical criterion digest 5A79F29593F8BC33, four adjacent gate "
    "suites green, evidence qa/gate-decl-retire-scope-R2321.log 1324B through the "
    "evidence_capture callable, one runner wiring line. LIVE: the only declared "
    "identity '-#02878cdc' sits on an OPEN row and is REFUSED E_GDRTS_MATCHED at "
    "exit 2 naming level open, with state/machine_gates.json byte-identical at "
    "427B / sha256-16 10EF269E. Claimable tech 11 -> 10 is exactly the floor, so "
    "no successor seed was added]"
)

BOARD_TOP = (
    "- [ ] R2321 first item: THE BATTERY ON THE COMMITTED TREE, zero product "
    "edits until green (the R2168 mixed-tree rule). R2321 changed src/os "
    "(gate_decl_retire_scope.py, test_gate_decl_retire_scope.py, "
    "src/sandbox/reconcile_all.py), so the pre-registered target is 468 suites / "
    "3784 criteria - exactly +1 suite / +6 criteria against R2320 (467/3778) "
    "from the os-gate-decl-retire-scope suite, and any larger delta must be named "
    "rather than swept. Run the full battery on the committed tree with an empty "
    "git status, then all four follow-up sections AFTER regenerating the matrix "
    "(the FAIL-then-PASS order is designed), and on green go back to the product "
    "face the queue head names. Also open and needing an ELEVATED shell: "
    "BigDomain-OSLoop reads LogonType=InteractiveToken (eighty-third consecutive "
    "disclosure; carried as loop-s4u-reconcile in state/debt.md).\n"
)


def write_text(path, text):
    data = text.encode("utf-8")
    temp = path + ".r2321-tmp"
    with io.open(temp, "wb") as handle:
        handle.write(data)
    os.replace(temp, path)
    with io.open(path, "rb") as handle:
        if handle.read() != data:
            raise SystemExit("E_CLOSE_READBACK %s" % path)


def close_queue_row():
    with io.open(TECH, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    target = None
    for index, line in enumerate(lines):
        if line.startswith("- [ ] P2 tech seed (R2319,") \
                and "gate_decl_retire_scope.py" in line:
            target = index
            break
    if target is None:
        print("queue: row already closed")
        return
    lines[target] = lines[target].replace(
        "- [ ] ", "- [x] [done 2026-11-01 R2321] ", 1) + BOARD_DONE
    write_text(TECH, nl.join(lines))
    print("queue: tech row 378 closed, no successor seed (floor reached)")


def close_debt_row():
    with io.open(DEBT, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    target = None
    for index, line in enumerate(lines):
        if line.startswith("- [ ] opened=R2320 | item=product-face-R2321"):
            target = index
            break
    if target is None:
        print("debt: row already closed")
        return
    parts = [part for part in lines[target][len("- [ ] "):].split(" | ") if part]
    opened = parts[0]
    item = parts[1]
    note = ""
    for part in parts[2:]:
        if part.startswith("note="):
            note = part[len("note="):]
    lines[target] = ("- [x] %s | %s | closed=R2321 | note=%s"
                     % (opened, item, note))
    write_text(DEBT, nl.join(lines))
    print("debt: product-face-R2321 closed at R2321")


def open_debt_row():
    note = (
        "R2321 closeout: the scope reader shipped and the live reading is the "
        "honest negative case ('-#02878cdc' sits on an OPEN row and is refused "
        "E_GDRTS_MATCHED at exit 2 naming level open, with the declaration "
        "byte-identical at 427B), so the positive done-row path is proven on "
        "fixture worlds only. The next window runs the battery the R2168 "
        "mixed-tree rule defers on the committed R2321 tree with the "
        "pre-registered target of 468 suites / 3784 criteria, then takes the "
        "product face the queue head names. Carry also the R2310 seed "
        "residue_triage_append, because the fold-creates-residue repair has now "
        "been spliced by hand twice (R2318 and R2320) and a third fold in this "
        "window's own closeout will make it three."
    )
    existing = io.open(DEBT, "r", encoding="utf-8").read()
    if "item=product-face-R2322" in existing:
        print("debt: product-face-R2322 already open")
        return
    report = DA.append_row(ROOT, "R2321", "product-face-R2322", note,
                           first="yes", execute=True)
    print("debt: product-face-R2322 appended (%sB -> %sB, wrote=%r)"
          % (report.get("before_bytes"), report.get("predicted_bytes"),
             report.get("wrote")))


def block_ends(state):
    starts = []
    for index, item in enumerate(state["log"], 1):
        if re.match(r"^(\d{4}-\d{2}-\d{2} )?R\d+ ", item):
            starts.append(index)
    ends = [start - 1 for start in starts[1:]]
    ends.append(len(state["log"]))
    return [end for end in ends if end >= 3]


def maybe_fold(state, delta):
    raw = open(STATE, "rb").read()
    disk = len(raw)
    if disk + delta <= SF.GATE - 1500:
        print("fold: not due (%dB + %dB against gate %d)"
              % (disk, delta, SF.GATE))
        return False
    chosen = None
    for end in block_ends(state):
        window = state["log"][2:end]
        tokens = set()
        for line in window:
            tokens |= set(SF.PAT.findall(line))
        summary = ("Fold R2321: log lines 3..%d (whole round blocks) moved "
                   "verbatim to the archive; window tokens: %s"
                   % (end, " ".join(sorted(tokens))))
        plan, _text = SF.plan_fold(raw, state, 3, end, summary,
                                   reserve=delta, gate=SF.GATE)
        if plan["gate_ok"] and plan["margin"] - delta >= 1500:
            chosen = (end, summary, plan)
            break
    if chosen is None:
        raise SystemExit("E_CLOSE_NO_FOLD_WINDOW")
    end, summary, plan = chosen
    report = SF.fold(ROOT, "R2321", 619, 3, end, summary, reserve=delta,
                     execute=True)
    print("fold: 619 lines 3..%d predicted=%dB actual=%dB margin=%d tokens=%d "
          "missing=%r"
          % (end, report["predicted_bytes"],
             report.get("post_bytes", report["predicted_bytes"]),
             report.get("margin", 0), plan["tokens_total"],
             plan["tokens_missing"]))
    return True


def append_state():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    if state["tick"] == 2321:
        print("state: already at tick 2321")
        return
    trial = json.loads(json.dumps(state))
    trial["tick"] = 2321
    trial["log"].extend([ROUND_LOG, TOKENS_LOG, SELF_HEAL, HONEST])
    rendered = json.dumps(trial, ensure_ascii=False, indent=2) + "\n"
    delta = len(rendered.replace("\n", "\r\n").encode("utf-8")) - \
        os.path.getsize(STATE)
    maybe_fold(state, delta)
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = 2321
    state["log"].extend([ROUND_LOG, TOKENS_LOG, SELF_HEAL, HONEST])
    raw = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    write_text(STATE, raw.replace("\n", "\r\n"))
    SIO.fix(STATE, execute=True)
    report = SIO.report(STATE)
    if not report["layout_ok"]:
        raise SystemExit("E_CLOSE_LAYOUT %r" % report)
    print("state: tick=%d log=%d bytes=%d CANON-CLEAN"
          % (state["tick"], len(state["log"]), report["bytes"]))


def update_export():
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
        "src/os/gate_decl_retire_scope.py",
        "on",
        "R2321 产品窗：门声明退役现在先读作用域。一个载体行已完成的声明条目终于"
        "可以退役——载体行是 done 的 MATCHED 进退役规划，open / gated 的 MATCHED "
        "在动任何字节之前拒绝并点名层级，AMBIGUOUS 继续拒绝并点名全部承载行，"
        "UNMATCHED 继续进规划。套件 6/6 双腿一致（摘要 5A79F29593F8BC33）＋四套"
        "相邻门套件全绿；活声明实测 '-#02878cdc' 落在 open 行，如实拒绝 "
        "E_GDRTS_MATCHED（退出码 2）且声明文件 427B 字节不变。",
    ])
    export["results"].insert(0, [
        "R2321",
        "product window: src/os/gate_decl_retire_scope.py with its six "
        "pre-registered criteria, one runner wiring line, one evidence capture "
        "(qa/gate-decl-retire-scope-R2321.log 1324B, two identical legs plus four "
        "adjacent suites green) and one live reading that keeps the real "
        "declaration byte-identical at 427B; one tech row closed and no successor "
        "seed, because claimable falls 11 -> 10 which is exactly the floor.",
    ])
    derived, _state, _export, _pat = CEC.recompute()
    export["self_drive"] = derived
    tick_label = json.loads(io.open(
        os.path.join(BASE, "export_consistency_patterns.json"),
        encoding="utf-8").read())["tick_row_label"]
    for row in export.get("results", []):
        if isinstance(row, list) and len(row) >= 2 and row[1] == tick_label:
            row[0] = "2321"
    raw = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    write_text(EXPORT, raw)
    print("export: refreshed, self_drive recomputed (%d keys)" % len(derived))


def update_heartbeat():
    line = ("tick 2321 2026-11-01 R2321 product window: the gate declaration "
            "retirement now reads a SCOPE before it plans - "
            "src/os/gate_decl_retire_scope.py lets a matched DONE row reach "
            "gate_decl_retire while a matched OPEN or GATED row refuses before any "
            "byte with its level named, AMBIGUOUS keeps every carrier and "
            "UNMATCHED keeps planning; suite 6/6 twice with an identical "
            "criterion digest 5A79F29593F8BC33 plus four adjacent gate suites "
            "green (qa/gate-decl-retire-scope-R2321.log 1324B). LIVE: "
            "'-#02878cdc' sits on an OPEN row and is REFUSED E_GDRTS_MATCHED at "
            "exit 2 naming level open, with state/machine_gates.json "
            "byte-identical at 427B / sha256-16 10EF269E. One tech row closed, no "
            "successor seed (claimable 11 -> 10 is exactly the floor); the battery "
            "carries to R2322 with a pre-registered 468 suites / 3784 criteria.\n")
    with io.open(HEART, "r", encoding="utf-8") as handle:
        text = handle.read()
    if not text.endswith("\n"):
        text += "\n"
    write_text(HEART, text + line)
    print("heartbeat: appended tick 2321")


def update_board():
    with io.open(BOARD, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    if text.startswith("- [ ] R2321 first item"):
        print("board: already closed")
        return
    if not text.startswith("- [ ] R2320 first item"):
        raise SystemExit("E_CLOSE_BOARD_TOP")
    first_end = text.index(nl)
    closed = "- [x]" + text[len("- [ ]"):first_end]
    text = closed + text[first_end:]
    text = BOARD_TOP.replace("\n", nl) + text
    write_text(BOARD, text)
    print("board: R2320 row closed, R2321 first item inserted")


def main():
    close_queue_row()
    close_debt_row()
    open_debt_row()
    append_state()
    update_export()
    update_heartbeat()
    update_board()


if __name__ == "__main__":
    main()