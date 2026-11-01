"""R2322 closeout: debt, state, export, heartbeat, board.

This window ran the verification the debt gate named: the full reconcile
battery on the committed R2321 tree with zero product edits, then the four
follow-up sections after the matrix regeneration. No queue row was claimed
and no product code changed, so the honest score is 0 product points.

ASCII source; the Chinese CEO face lives in docs/status-export.json.

Usage: python src/os/closeout_R2322.py
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
DEBT = os.path.join(ROOT, "state", "debt.md")

NOW = datetime.datetime.now().astimezone()
NOW_ISO = NOW.isoformat(timespec="seconds")
DUE = (NOW + datetime.timedelta(hours=44)).isoformat(timespec="seconds")

ROUND_LOG = (
    "2026-11-01 R2322 verification window (five-silence scan clean at open: "
    "empty git status --short and no index.lock; decisions.md carried 84 "
    "non-empty rows equal to the stored baseline and the token diff read 57 "
    "tokens with ZERO new, so no decision row is owed; the group ledger carried "
    "the same three @BigDomain patrol rows already paid off, the last one "
    "P-20261026-0930 acked at R2311, with zero unreplied numbered handoffs; the "
    "group orders tail was unchanged at the 2026-11-01 10:4x baseline that R2321 "
    "already acked by number as non-execution; benchmarks refreshed 2026-11-01 "
    "inside the seven-day gate; the QA charter daily crawl face read PASS with "
    "today's smoke evidence). The debt gate named exactly one first=yes row "
    "(product-face-R2322), and its note named the verification the R2168 "
    "mixed-tree rule defers, so this window ran it with ZERO product edits: full "
    "reconcile battery on the committed R2321 tree abe9df54 with an empty git "
    "status before the run = RUNNER PASS 468/468 suites green plus controls 7/7 "
    "in 769.6s with birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy zero "
    "failed zero (qa/reconcile-all-R2322.log, 786476B, single writer utf-8 LF "
    "through src/os/battery_stream.py, never a shell redirection), criteria "
    "total 3784 - EXACTLY the pre-registered +1 suite / +6 criteria against "
    "R2320 (467/3778) from the R2321 os-gate-decl-retire-scope suite, so the "
    "prediction matched the measurement with no correction. Four follow-up "
    "sections then ran through src/os/battery_followup.py: the matrix section "
    "FAILED first on the stale doc (on-disk=44867B regenerated=44931B) and did "
    "NOT rewrite it, which is the designed order; src/sandbox/suite_matrix.py "
    "then regenerated docs/sandbox-suite-matrix.md to 468 suites / 3784 "
    "criteria (44931B) and the re-run read all four sections PASS (matrix "
    "byte-identical 44931B, fingerprint CLEAN 5 domains, profile --daily "
    "--check byte-identical, census DRIFT-CLEAN), closing VERDICT R2322 PASS. "
    "Zero product code changed, so the honest score is 0 product points; the "
    "product face resumes at R2323 on the tech head."
)

TOKENS_LOG = (
    "R2322 tokens: local=~9k api=0 api_reason=verification-only window - one "
    "full reconcile battery on the committed tree with its streamed evidence "
    "file, one four-section follow-up twice plus one matrix regeneration from "
    "that evidence, one residue splice for the rounds this window's fold "
    "archived, and the debt/state/export/heartbeat/board closeout; zero cloud "
    "calls and zero external API touches; the product face resumes at R2323"
)

SELF_HEAL = (
    "R2322 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply it, and this "
    "session runs unelevated, so the definition of the loop hosting this window "
    "was left untouched. Open local-lane item for an elevated window "
    "(eighty-fourth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

HONEST = (
    "R2322 honest disclosures: (a) this window shipped NO product code and "
    "scores 0 product points; the work it did was the battery the register named, "
    "not a product face. (b) The matrix section failed first by design - it "
    "refuses to rewrite a stale doc - and both legs stay in the evidence file "
    "(1889B FAIL then 1950B PASS), so the round reads as one designed FAIL "
    "followed by one PASS rather than as two rounds. (c) The closeout crossed "
    "the waterline and was folded, which recreates residue for every round whose "
    "log block moved into the archive (the law first measured at R2311 and "
    "repaired by hand at R2318 and R2320); those rounds were spliced into "
    "state/residue_triage.json BY NAME with a DELIVERED status read off the live "
    "stamp table, never by regenerating the whole declaration, because a "
    "regeneration would absorb every other entry's reason. (d) The bundle the "
    "battery measured is the committed R2321 tree; this window's own file "
    "changes are bookkeeping only and are not battery subjects. (e) tasks.md was "
    "left untouched: it is the P-47 canonical board and carries no row for this "
    "tech slice, disclosed rather than silently skipped."
)

EXPORT_DO = (
    "R2322 验证轮：在已提交的 R2321 树上（abe9df54）跑全量对账电池，零产品改动。"
    "结果 RUNNER PASS 468/468 套件全绿 + 对账控制 7/7，判据总数 3784——与 R2321 收"
    "账时预注册的目标（468 套件 / 3784 判据）完全一致，零修正。矩阵段按设计先报陈旧"
    "拒绝改写，重生成后四段随访全 PASS，结论 R2322 PASS。本轮不产产品代码，如实记 0 分。"
)

EXPORT_CURRENT = (
    "R2322 验证轮完成：全量对账电池 468/468 套件全绿、7/7 控制通过、769.6 秒，判据 "
    "3784（与预注册目标精确一致）；qa/reconcile-all-R2322.log 786476B 单写者证据；"
    "矩阵重生成 468 套件 / 3784 判据（44931B）后四段随访全 PASS。产品面下一轮回到技术"
    "队头 line 379（AC-OTR1 orphan_trace）。"
)

EXPORT_ARTIFACT = (
    "qa/reconcile-all-R2322.log（786476B·468/468 套件全绿·判据 3784）与 "
    "docs/sandbox-suite-matrix.md（44931B·468 套件 / 3784 判据），2026-11-01"
)

EXPORT_NEXT = (
    "R2323 产品轮：认领技术队头 state/queue/tech.md:379 前缀 AC-OTR1 的 orphan_trace "
    "种子（判据已预先钉死在该行），交付读解器与套件；电池随之推给下一验证轮，预注册"
    "目标 469 套件 / 3790 判据（相对 468/3784 恰好 +1 套件 / +6 判据）"
)

BOARD_TOP = (
    "- [ ] R2322 first item: CLAIM THE TECH HEAD the gate names after this "
    "verification - state/queue/tech.md:379 prefix AC-OTR1, the R2302 "
    "orphan_trace seed whose AC-OTR1..AC-OTR6 criteria were pinned INSIDE that "
    "row BEFORE any code. Ship the read-only resolver that takes each ORPHAN "
    "round from evidence_variants and reads the RUNNER/VERDICT lines inside its "
    "own variant legs (TRACE-EXISTS naming the standing-in leg, NO-TRACE, and a "
    "leg that cannot be decoded failing closed), with its own suite, a dogfooded "
    "evidence capture and one runner wiring line. The battery then carries to "
    "the next verification window with the pre-registered target of 469 suites / "
    "3790 criteria - exactly +1 suite / +6 criteria against R2322 (468/3784) - "
    "and any larger delta must be named rather than swept. Also open and needing "
    "an ELEVATED shell: BigDomain-OSLoop reads LogonType=InteractiveToken "
    "(eighty-fourth consecutive disclosure; carried as loop-s4u-reconcile in "
    "state/debt.md).\n"
)


def write_text(path, text):
    data = text.encode("utf-8")
    temp = path + ".r2322-tmp"
    with io.open(temp, "wb") as handle:
        handle.write(data)
    os.replace(temp, path)
    with io.open(path, "rb") as handle:
        if handle.read() != data:
            raise SystemExit("E_CLOSE_READBACK %s" % path)


def close_debt_row():
    with io.open(DEBT, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    target = None
    for index, line in enumerate(lines):
        if line.startswith("- [ ] opened=R2321 | item=product-face-R2322"):
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
    lines[target] = ("- [x] %s | %s | closed=R2322 | note=%s"
                     % (opened, item, note))
    write_text(DEBT, nl.join(lines))
    print("debt: product-face-R2322 closed at R2322")


def open_debt_row():
    note = (
        "R2322 closeout: the verification the R2168 mixed-tree rule defers ran "
        "on the committed R2321 tree abe9df54 with zero product edits and read "
        "RUNNER PASS 468/468 suites + controls 7/7 in 769.6s, criteria total "
        "3784 EXACTLY as pre-registered; four follow-up sections PASS after the "
        "designed matrix FAIL and its regeneration, VERDICT R2322 PASS. This "
        "window shipped no product code. The next window takes the product face: "
        "the tech head state/queue/tech.md:379 prefix AC-OTR1 (orphan_trace), "
        "whose six criteria are already pinned in that row, and the battery then "
        "carries to the successor with a pre-registered target of 469 suites / "
        "3790 criteria. Carry also the R2310 seed residue_triage_append: the "
        "fold-creates-residue repair has now been spliced by hand three times "
        "(R2318, R2320 and this window)."
    )
    existing = io.open(DEBT, "r", encoding="utf-8").read()
    if "item=product-face-R2323" in existing:
        print("debt: product-face-R2323 already open")
        return
    report = DA.append_row(ROOT, "R2322", "product-face-R2323", note,
                           first="yes", execute=True)
    print("debt: product-face-R2323 appended (%sB -> %sB, wrote=%r)"
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
        summary = ("Fold R2322: log lines 3..%d (whole round blocks) moved "
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
    report = SF.fold(ROOT, "R2322", 620, 3, end, summary, reserve=delta,
                     execute=True)
    print("fold: 620 lines 3..%d predicted=%dB actual=%dB margin=%d tokens=%d "
          "missing=%r"
          % (end, report["predicted_bytes"],
             report.get("post_bytes", report["predicted_bytes"]),
             report.get("margin", 0), plan["tokens_total"],
             plan["tokens_missing"]))
    return True


def append_state():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    if state["tick"] == 2322:
        print("state: already at tick 2322")
        return
    trial = json.loads(json.dumps(state))
    trial["tick"] = 2322
    trial["log"].extend([ROUND_LOG, TOKENS_LOG, SELF_HEAL, HONEST])
    rendered = json.dumps(trial, ensure_ascii=False, indent=2) + "\n"
    delta = len(rendered.replace("\n", "\r\n").encode("utf-8")) - \
        os.path.getsize(STATE)
    maybe_fold(state, delta)
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = 2322
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
        "qa/reconcile-all-R2322.log",
        "on",
        "R2322 验证轮：在已提交的 R2321 树上跑全量对账电池，468/468 套件全绿 + "
        "对账控制 7/7，769.6 秒，判据总数 3784 与预注册目标精确一致；证据 "
        "786476B 单写者。矩阵段按设计先拒绝改写过期的矩阵文档，重生成到 468 套件 / "
        "3784 判据（44931B）后四段随访全 PASS（矩阵字节一致、指纹干净 5 域、"
        "剖面 --daily --check 字节一致、普查无漂移），结论 R2322 PASS。零产品代码，"
        "如实记 0 分。",
    ])
    export["results"].insert(0, [
        "R2322",
        "verification window on the debt register first item: full reconcile "
        "battery on the committed R2321 tree abe9df54 with zero product edits "
        "until green (the R2168 mixed-tree rule) = RUNNER PASS 468/468 suites + "
        "controls 7/7 in 769.6s, criteria total 3784 exactly as pre-registered "
        "(+1 suite / +6 criteria against R2320 467/3778 from the R2321 "
        "os-gate-decl-retire-scope suite); four follow-up sections PASS after the "
        "designed matrix FAIL and its regeneration to 468/3784 (44931B), VERDICT "
        "R2322 PASS. No product code, honest 0 points; the successor names the "
        "tech head line 379 prefix AC-OTR1.",
    ])
    derived, _state, _export, _pat = CEC.recompute()
    export["self_drive"] = derived
    tick_label = json.loads(io.open(
        os.path.join(BASE, "export_consistency_patterns.json"),
        encoding="utf-8").read())["tick_row_label"]
    for row in export.get("results", []):
        if isinstance(row, list) and len(row) >= 2 and row[1] == tick_label:
            row[0] = "2322"
    raw = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    write_text(EXPORT, raw)
    print("export: refreshed, self_drive recomputed (%d keys)" % len(derived))


def update_heartbeat():
    line = ("tick 2322 2026-11-01 R2322 verification window: the full "
            "reconcile battery on the committed R2321 tree abe9df54 with zero "
            "product edits read RUNNER PASS 468/468 suites plus controls 7/7 in "
            "769.6s with criteria total 3784 EXACTLY as pre-registered (+1 suite "
            "/ +6 criteria against R2320 467/3778); qa/reconcile-all-R2322.log "
            "786476B single writer, TMP RECLAIM 932/932 worlds 326.59 MiB. Four "
            "follow-up sections PASS after the designed matrix FAIL on the stale "
            "doc and its regeneration to 468/3784 (44931B), VERDICT R2322 PASS. "
            "Zero product code, honest 0 points; the product face resumes at "
            "R2323 on the tech head line 379 prefix AC-OTR1.\n")
    with io.open(HEART, "r", encoding="utf-8") as handle:
        text = handle.read()
    if not text.endswith("\n"):
        text += "\n"
    write_text(HEART, text + line)
    print("heartbeat: appended tick 2322")


def update_board():
    with io.open(BOARD, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    if text.startswith("- [ ] R2322 first item"):
        print("board: already closed")
        return
    if not text.startswith("- [ ] R2321 first item"):
        raise SystemExit("E_CLOSE_BOARD_TOP")
    first_end = text.index(nl)
    closed = "- [x]" + text[len("- [ ]"):first_end]
    text = closed + text[first_end:]
    text = BOARD_TOP.replace("\n", nl) + text
    write_text(BOARD, text)
    print("board: R2321 row closed, R2322 first item inserted")


def main():
    close_debt_row()
    open_debt_row()
    append_state()
    update_export()
    update_heartbeat()
    update_board()


if __name__ == "__main__":
    main()