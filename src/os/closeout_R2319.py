"""R2319 closeout: queue row, successor seed, debt, state, export, heartbeat.

This window shipped the product face the debt gate named: the retirement
writer now asks the identity reader first, so a declared identity that a live
row still carries can no longer be retired out from under the declaration.

ASCII source; the Chinese CEO face lives in docs/status-export.json.

Usage: python src/os/closeout_R2319.py
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
    "2026-11-01 R2319 product window (five-silence scan clean at open: empty "
    "git status --short and no index.lock; decisions.md carried 84 non-empty "
    "rows equal to the stored baseline and the token diff read 57 tokens with "
    "ZERO new, so no decision row is owed; the group ledger carried the same "
    "three @BigDomain patrol rows already paid off, the last one P-20261026-0930 "
    "acked at R2311, with zero unreplied numbered handoffs; the group orders "
    "tail was unchanged at the 2026-10-31 18:23 baseline; benchmarks refreshed "
    "2026-10-29 inside the seven-day gate). The P1 canonical rows stay "
    "blocked-on-CEO, the weekly proposal duty is met by BD-PROP-005, the floors "
    "read FLOOR-MET main 5/5 tech 11/10 explore 10/10, and the debt gate named "
    "exactly one first=yes row (product-face-R2319), so this window claimed the "
    "TOP deliverable tech row: state/queue/tech.md:377 prefix AC-GDRTW1, the "
    "R2317 gate_decl_retire_wire seed whose AC-GDRTW1..AC-GDRTW6 criteria were "
    "already pinned INSIDE that row BEFORE the code (fresh zero-occupancy anchor "
    "check at HEAD 2026-11-01: gate_decl_retire_wire / AC-GDRTW / E_GDRTW / "
    "os-gate-decl-retire-wire / test_gate_decl_retire_wire hit only the seed "
    "text, the board, state.json, state/debt.md, status-export.json and two "
    "closeout helpers, with no product code path). PRODUCT: "
    "src/os/gate_decl_retire_wire.py plus src/os/test_gate_decl_retire_wire.py - "
    "the retirement writer stops asking only machine_gate's candidate reading, "
    "which never sees a row that carries no criteria prefix, and asks the "
    "identity reader first: only an UNMATCHED identity reaches "
    "gate_decl_retire's plan, while MATCHED and AMBIGUOUS refuse before any byte "
    "with the reader state and every carrier line named - the same shape "
    "gate_decl_identity_wire already gives the append path. Both laws are "
    "imported, never re-implemented: the suite patches GDI.resolve, GDRT.retire "
    "and GDI.rows in turn and watches the verdict move, and proves no second "
    "queue scan exists in the source. SUITE PASS 6/6 twice with an identical "
    "criterion digest, four adjacent gate suites green (identity_wire 6/6, "
    "retire 6/6, identity 6/6, append 6/6), qa/gate-decl-retire-wire-R2319.log "
    "1279B as one utf-8 LF single writer through the evidence_capture callable, "
    "one runner wiring line. LIVE READING OF THE REAL DECLARATION (the exact "
    "finding R2317 measured): gate_decl_retire_wire.py --identity '-#02878cdc' "
    "now REFUSES E_GDRTW_MATCHED at exit 2 with 'one row carries this identity' "
    "instead of planning declarations 1->0, and state/machine_gates.json stays "
    "427B / sha256-16 10EF269E863896CE byte-identical (qa/gate-decl-retire-"
    "wire-live-R2319.log). One tech row closed, one successor seed added with "
    "zero-occupancy anchors, claimable stays 11 against a floor of 10."
)

TOKENS_LOG = (
    "R2319 tokens: local=~17k api=0 api_reason=product window on the debt "
    "register first item - one wire module with its six pre-registered criteria "
    "and its suite (green after three this-window test defects were corrected "
    "against the measured truth), one dogfooded evidence capture (two legs "
    "identical, four adjacent suites green), two live CLI readings of the real "
    "declaration with the file proved byte-identical, one runner wiring line, "
    "one queue close and one successor seed through the shipped queue law, one "
    "debt close and one register append, and the state/export/heartbeat/board "
    "closeout; zero cloud calls and zero external API touches; the battery "
    "carries to R2320"
)

SELF_HEAL = (
    "R2319 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply it, and this "
    "session runs unelevated, so the definition of the loop hosting this window "
    "was left untouched. Open local-lane item for an elevated window "
    "(eighty-first consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

HONEST = (
    "R2319 honest disclosures: (a) the first suite run was red 3/6 and all "
    "three reds were this-window TEST defects, never a criterion widened: "
    "AC-GDRTW1 expected the rows-patch leg to land on a wire refusal, but with "
    "GDI.rows emptied the wire correctly steps aside and gate_decl_retire's own "
    "still-blocked law answers instead, which is the stronger proof that the "
    "rows import moved the verdict and the assertion now names that code; "
    "AC-GDRTW4 compared two different operations because the direct leg called "
    "GDRT.retire without execute=True, so the twin world legitimately stayed at "
    "two entries; AC-GDRTW6 read red because the runner label was not yet "
    "wired, and the wiring landed before the green run. (b) The live reading is "
    "a refusal by design and is disclosed as such: every entry in the real "
    "declaration currently resolves MATCHED, so no honest retirement can be "
    "performed live and the positive path is proven on fixture worlds instead. "
    "(c) That refusal is also this window's real finding and the successor "
    "seed: a completed row still carries its identity, so a MATCHED blanket "
    "refusal now blocks the legitimate retirement of a discharged blocker - the "
    "next wire has to read row LEVEL (done vs open/gated), which AC-GDRTW3 "
    "measured: the gated and done fixtures both read MATCHED and both refused "
    "identically. (d) The full reconcile battery did NOT run here (the R2168 "
    "mixed-tree rule keeps it on a committed tree), so the successor carries it "
    "with the pre-registered target of 467 suites / 3778 criteria - exactly +1 "
    "suite / +6 criteria against R2318 (466/3772) from this window's own "
    "os-gate-decl-retire-wire suite. (e) tasks.md was left untouched: it is the "
    "P-47 canonical board and carries no row for this tech slice, disclosed "
    "rather than silently skipped."
)

EXPORT_DO = (
    "R2319 产品窗：把门声明的退役写手接到身份读面上。R2317 实测过一处缺口——"
    "退役写手只问 machine_gate 的候选面，而候选面只看可认领行，于是一个「行还在、"
    "但不带判据前缀」的声明条目会读成 INERT 并被规划退役，尽管它仍是事实。本轮交付 "
    "src/os/gate_decl_retire_wire.py：先问身份读面，只有 UNMATCHED 才进退役规划，"
    "MATCHED / AMBIGUOUS 在动任何字节之前拒绝并点名读面状态与全部承载行。两条法都"
    "是导入而非复制，套件通过分别打桩读面与退役计划证明这一点，并证明源码里没有第二"
    "个队列扫描。"
)

EXPORT_CURRENT = (
    "R2319 产品窗完成：门声明退役接线 src/os/gate_decl_retire_wire.py 落盘并接线，"
    "套件 6/6 双腿全绿（判据摘要一致）、四套相邻门套件同时绿，证据 "
    "qa/gate-decl-retire-wire-R2319.log（1279B）。活声明实测：对 "
    "'-#02878cdc' 由 R2317 的「规划退役 1→0」变成「拒绝 MATCHED、退出码 2」，"
    "state/machine_gates.json 保持 427B 字节不变。技术队列可认领 11（地板 10）。"
)

EXPORT_ARTIFACT = (
    "src/os/gate_decl_retire_wire.py（+ 测试套件 6 判据）与 "
    "qa/gate-decl-retire-wire-R2319.log（1279B·双腿一致·四套相邻全绿），2026-11-01"
)

EXPORT_NEXT = (
    "R2320 验证轮：在已提交树上跑全量对账电池（预注册目标 467 套件 / 3778 判据 = "
    "相对 R2318 的 466/3772 恰好 +1 套件 / +6 判据），矩阵重生成后四段随访必须全 "
    "PASS；随访后回产品面，接后继种子 src/os/gate_decl_retire_scope.py"
)

BOARD_DONE = (
    " [done 2026-11-01 R2319 - the retirement writer asks the identity reader "
    "first: src/os/gate_decl_retire_wire.py resolves the identity through "
    "gate_decl_identity's rows and resolve imports and only an UNMATCHED identity "
    "reaches gate_decl_retire's plan, while MATCHED and AMBIGUOUS refuse before "
    "any byte with the reader state and every carrier line named; both laws are "
    "imported (the suite patches GDI.resolve, GDRT.retire and GDI.rows in turn) "
    "and no second queue scan exists. SUITE PASS 6/6 twice with an identical "
    "criterion digest, four adjacent gate suites green, evidence "
    "qa/gate-decl-retire-wire-R2319.log 1279B through the evidence_capture "
    "callable, one runner wiring line. LIVE: '-#02878cdc' now reads REFUSED "
    "E_GDRTW_MATCHED at exit 2 instead of PLANNED 1->0, with "
    "state/machine_gates.json byte-identical at 427B / sha256-16 10EF269E863896CE "
    "(qa/gate-decl-retire-wire-live-R2319.log). One successor seed added; "
    "claimable tech stays 11 against a floor of 10]"
)

BOARD_TOP = (
    "- [ ] R2319 first item: THE BATTERY ON THE COMMITTED TREE, zero product "
    "edits until green (the R2168 mixed-tree rule). R2319 changed src/os "
    "(gate_decl_retire_wire.py, test_gate_decl_retire_wire.py, "
    "src/sandbox/reconcile_all.py) and never ran a whole-registry pass, so the "
    "pre-registered target is 467 suites / 3778 criteria - exactly +1 suite / +6 "
    "criteria against R2318 (466/3772), and any larger delta must be named "
    "rather than swept. Run the full battery on the committed tree with an empty "
    "git status, keep both evidence legs, then run all four follow-up sections "
    "AFTER regenerating the matrix (the FAIL-then-PASS order is designed), and "
    "on green go back to the product face the queue head names: the "
    "gate_decl_retire_scope seed at the tech head, whose criteria are pinned "
    "inside that row BEFORE any code. Also open and needing an ELEVATED shell: "
    "BigDomain-OSLoop reads LogonType=InteractiveToken (eighty-first consecutive "
    "disclosure; carried as loop-s4u-reconcile in state/debt.md).\n"
)

SUCCESSOR = (
    "- [ ] P2 tech seed (R2319, from this window own measured finding): "
    "`src/os/gate_decl_retire_scope.py` - the retire wire now refuses every "
    "MATCHED identity, so a declared blocker whose row was COMPLETED can never "
    "be retired: gate_decl_identity reads MATCHED at every row level, and "
    "AC-GDRTW3 measured that the gated fixture and the done fixture refuse "
    "identically, while gate_decl_retire would legitimately offer both once "
    "machine_gate reads them INERT. The declaration therefore rots in the "
    "opposite direction from the one R2317 named. One reader that hands the "
    "retire plan a scope verdict instead of a bare MATCHED: a matched row at "
    "level done reaches gate_decl_retire.plan, a matched row at level open or "
    "gated refuses before any byte with the level named, AMBIGUOUS keeps "
    "refusing and UNMATCHED keeps reaching the plan. The row level is imported "
    "from gate_decl_identity.rows, never re-scanned. Criteria prefix "
    "AC-GDRTS1..AC-GDRTS6 pre-registered HERE BEFORE any code: AC-GDRTS1 the row "
    "level is imported from gate_decl_identity.rows and the plan call from "
    "gate_decl_retire, never re-implemented, proven by patching each and "
    "watching the verdict move; AC-GDRTS2 a MATCHED identity whose carrier row "
    "is level done reaches the plan and performs the retirement, while a MATCHED "
    "identity on an open or gated row refuses before any byte with the level in "
    "the detail; AC-GDRTS3 AMBIGUOUS still refuses with every carrier named and "
    "UNMATCHED still reaches the plan, so the new scope reading widens nothing; "
    "AC-GDRTS4 the success path is byte-identical to calling "
    "gate_decl_retire.retire directly on an identical twin world, with every "
    "surviving entry byte-intact; AC-GDRTS5 CLI exits 0 planned, 2 refused, 3 "
    "missing or unreadable, 5 bad flags, with a byte-stable --json over pinned "
    "keys; AC-GDRTS6 pure ASCII source, stdlib only, no network, no clock, plus "
    "its own reconcile label.\n"
)


def write_text(path, text):
    data = text.encode("utf-8")
    temp = path + ".r2319-tmp"
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
        if line.startswith("- [ ] P2 tech seed (R2317,") \
                and "gate_decl_retire_wire.py" in line:
            target = index
            break
    if target is None:
        raise SystemExit("E_CLOSE_ROW_NOT_FOUND")
    closed = lines[target].replace(
        "- [ ] ", "- [x] [done 2026-11-01 R2319] ", 1) + BOARD_DONE
    lines[target] = closed
    insert_at = len(lines)
    while insert_at > 0 and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines.insert(insert_at, SUCCESSOR.rstrip(nl).replace("\n", nl))
    write_text(TECH, nl.join(lines))
    print("queue: tech row 377 closed, one successor seed added")


def close_debt_row():
    with io.open(DEBT, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    target = None
    for index, line in enumerate(lines):
        if line.startswith("- [ ] opened=R2318 | item=product-face-R2319"):
            target = index
            break
    if target is None:
        raise SystemExit("E_CLOSE_DEBT_ROW_NOT_FOUND")
    row = lines[target]
    body = row[len("- [ ] "):]
    parts = [part for part in body.split(" | ") if part]
    opened = parts[0]
    item = parts[1]
    note = ""
    for part in parts[2:]:
        if part.startswith("note="):
            note = part[len("note="):]
    lines[target] = ("- [x] %s | %s | closed=R2319 | note=%s"
                     % (opened, item, note))
    write_text(DEBT, nl.join(lines))
    print("debt: product-face-R2319 closed at R2319")


def open_debt_row():
    note = (
        "R2319 closeout: the retire wire shipped and the live reading proves the "
        "fix ('-#02878cdc' now REFUSED E_GDRTW_MATCHED at exit 2 with the "
        "declaration byte-identical at 427B), so the next window runs the battery "
        "the R2168 mixed-tree rule defers, then takes the product face the queue "
        "head already names: state/queue/tech.md prefix AC-GDRTS1, the "
        "gate_decl_retire_scope seed, whose criteria are pinned inside that row "
        "BEFORE any code. The scope reading exists because this window measured "
        "its opposite: a matched DONE row refuses exactly like a matched OPEN row, "
        "so a discharged blocker can never be retired."
    )
    report = DA.append_row(ROOT, "R2319", "product-face-R2320", note,
                           first="yes", execute=True)
    print("debt: %s appended (%dB -> %dB, wrote=%r)"
          % (report.get("item", "product-face-R2320"),
             report.get("before_bytes"), report.get("predicted_bytes"),
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
        summary = ("Fold R2319: log lines 3..%d (whole round blocks) moved "
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
    report = SF.fold(ROOT, "R2319", 617, 3, end, summary, reserve=delta,
                     execute=True)
    print("fold: 617 lines 3..%d predicted=%dB actual=%dB margin=%d tokens=%d "
          "missing=%r"
          % (end, report["predicted_bytes"],
             report.get("post_bytes", report["predicted_bytes"]),
             report.get("margin", 0), plan["tokens_total"],
             plan["tokens_missing"]))
    return True


def append_state():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    trial = json.loads(json.dumps(state))
    trial["tick"] = 2319
    trial["log"].extend([ROUND_LOG, TOKENS_LOG, SELF_HEAL, HONEST])
    rendered = json.dumps(trial, ensure_ascii=False, indent=2) + "\n"
    delta = len(rendered.replace("\n", "\r\n").encode("utf-8")) - \
        os.path.getsize(STATE)
    maybe_fold(state, delta)
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = 2319
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
        "src/os/gate_decl_retire_wire.py",
        "on",
        "R2319 product window: the gate declaration retirement writer now asks "
        "the identity reader before it plans, so an identity a live row still "
        "carries can no longer be retired out from under the declaration. Only "
        "an UNMATCHED identity reaches gate_decl_retire's plan; MATCHED and "
        "AMBIGUOUS refuse before any byte with the reader state and every carrier "
        "line named. Suite 6/6 twice with an identical criterion digest and four "
        "adjacent gate suites green; live reading '-#02878cdc' REFUSED "
        "E_GDRTW_MATCHED at exit 2 with the declaration byte-identical at 427B.",
    ])
    export["results"].insert(0, [
        "R2319",
        "product window: src/os/gate_decl_retire_wire.py with its six "
        "pre-registered criteria, one runner wiring line, one evidence capture "
        "(qa/gate-decl-retire-wire-R2319.log 1279B, two identical legs plus four "
        "adjacent suites green) and one live reading of the real declaration "
        "that turned R2317's PLANNED 1->0 into a refusal with the file unchanged; "
        "one tech row closed, one successor seed (gate_decl_retire_scope) added, "
        "claimable tech stays 11 against a floor of 10.",
    ])
    derived, _state, _export, _pat = CEC.recompute()
    export["self_drive"] = derived
    tick_label = json.loads(io.open(
        os.path.join(BASE, "export_consistency_patterns.json"),
        encoding="utf-8").read())["tick_row_label"]
    for row in export.get("results", []):
        if isinstance(row, list) and len(row) >= 2 and row[1] == tick_label:
            row[0] = "2319"
    raw = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    write_text(EXPORT, raw)
    print("export: refreshed, self_drive recomputed (%d keys)" % len(derived))


def update_heartbeat():
    line = ("tick 2319 2026-11-01 R2319 product window: the gate declaration "
            "retirement writer now asks the identity reader first - "
            "src/os/gate_decl_retire_wire.py resolves the identity through "
            "gate_decl_identity and only an UNMATCHED identity reaches "
            "gate_decl_retire, while MATCHED and AMBIGUOUS refuse before any byte "
            "with the reader state and every carrier line named; suite 6/6 twice "
            "with an identical criterion digest plus four adjacent gate suites "
            "green (qa/gate-decl-retire-wire-R2319.log 1279B). LIVE: "
            "'-#02878cdc' now reads REFUSED E_GDRTW_MATCHED at exit 2 instead of "
            "PLANNED 1->0, and state/machine_gates.json stays byte-identical at "
            "427B / sha256-16 10EF269E863896CE. One tech row closed, one "
            "successor seed added (gate_decl_retire_scope), claimable tech stays "
            "11 against a floor of 10; the battery carries to R2320 with a "
            "pre-registered 467 suites / 3778 criteria.\n")
    with io.open(HEART, "r", encoding="utf-8") as handle:
        text = handle.read()
    if not text.endswith("\n"):
        text += "\n"
    write_text(HEART, text + line)
    print("heartbeat: appended tick 2319")


def update_board():
    with io.open(BOARD, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    if not text.startswith("- [ ] R2318 first item"):
        raise SystemExit("E_CLOSE_BOARD_TOP")
    first_end = text.index(nl)
    head = text[:first_end]
    rest = text[first_end:]
    closed = "- [x]" + head[len("- [ ]"):]
    text = closed + rest
    text = BOARD_TOP.replace("\n", nl) + text
    write_text(BOARD, text)
    print("board: R2318 row closed, R2319 first item inserted")


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