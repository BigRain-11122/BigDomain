"""R2320 closeout: debt row, successor debt row, state, export, heartbeat.

This window was the verification window the R2319 closeout named first=yes:
the battery ran on the committed tree, found exactly one red suite, and the
red was repaired at its birth site (a fold-created residue round with no
triage entry). No product code shipped, so the product face the queue head
names carries to R2321 with its criteria already pinned in the row.

ASCII source; the Chinese CEO face lives in docs/status-export.json.

Usage: python src/os/closeout_R2320.py
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
    "2026-11-01 R2320 verification window (five-silence scan clean at open: "
    "empty git status --short and no index.lock; decisions.md carried 84 "
    "non-empty rows equal to the stored baseline and the token diff read 57 "
    "tokens with ZERO new, so no decision row is owed; the group ledger carried "
    "the same three @BigDomain patrol rows already paid off, the last one "
    "P-20261026-0930 acked at R2311, with zero unreplied numbered handoffs; the "
    "group orders tail was unchanged at the 2026-10-31 18:23 baseline; "
    "benchmarks refreshed 2026-10-29 inside the seven-day gate but the QA "
    "charter daily crawl face was FLAGGED with no smoke evidence for the day). "
    "The debt gate named product-face-R2320 first=yes and the R2319 closeout "
    "had already written what it owed: run the battery the R2168 mixed-tree "
    "rule defers, on the committed tree, with the pre-registered target of 467 "
    "suites / 3778 criteria. THIS WINDOW INHERITED THREE LEGS, not one. Leg 1 "
    "(qa/reconcile-all-R2320.log, committed with the R2319 fold 618 in "
    "652a7f59): RUNNER FAIL, 4 failed assertions on the pre-fold tree. Leg 2 "
    "(qa/reconcile-all-R2320-retry.log, reached this window untracked): RUNNER "
    "FAIL on the post-fold committed tree with 2 failed assertions, exactly one "
    "suite red - os-residue-triage AC-RTR6, live reading residue=190 "
    "triaged=189 untriaged=1. ROOT CAUSE, measured not guessed: the R2319 fold "
    "618 moved the R2305 log block into the archive, so R2305 stopped matching "
    "the live log and came back as residue with no triage entry - the known "
    "fold-creates-residue law first measured at R2311 and repaired the same way "
    "at R2318 for R2302/R2303. REPAIR AT THE BIRTH SITE, committed alone as "
    "26eecc98: src/os/closeout_R2320.py splices ONE entry for R2305 into "
    "state/residue_triage.json by name, 33107B -> 33490B with the predicted "
    "delta equal to the write, one atomic replace, a read-back byte proof and "
    "no temp residue, and it deliberately does NOT regenerate the declaration "
    "through closeout_R2310.py because a regeneration would absorb every other "
    "entry's reason - which is exactly the risk the R2310 seed names. The suite "
    "then read SUITE PASS 6/6 with the live verdict TRIAGED residue=[] triaged="
    "190 untriaged=0. Leg 3 is the honest one: qa/reconcile-all-R2320-retry2.log "
    "789696B sha16 fef565e4620c6ba9, ONE writer, RUNNER PASS (467/467 suites "
    "green, reconcile controls 7/7, 900.3s) with criteria total 3778 - exactly "
    "the pre-registered +1 suite / +6 criteria over R2318 (466/3772), no "
    "correction needed - and TMP RECLAIM candidates=932 removed=932 busy=0 "
    "failed=0 reclaimed=326.59 MiB. Four follow-up sections ran in the designed "
    "FAIL-then-PASS order: matrix refused the stale doc (on-disk 44771B vs "
    "regenerated 44867B) and wrote nothing, src/sandbox/suite_matrix.py "
    "regenerated docs/sandbox-suite-matrix.md to 44867B / 467 suites / 3778 "
    "criteria, and the re-run read matrix byte-identical, fingerprint CLEAN, "
    "profile byte-identical, census DRIFT-CLEAN -> VERDICT retry2 PASS. The QA "
    "charter daily crawl face was served in the same window: one new primary "
    "source read directly (openstd.samr.gov.cn registry row: GB 45438-2025 is a "
    "MANDATORY national standard, status in force, published 2025-02-28, "
    "implemented 2025-09-01), the benchmarks update record appended, the signal "
    "written into the wall as W36 with its consumer named, and the day's smoke "
    "evidence rendered from the real log (qa/smoke-R2320.log 2913B, "
    "qa/smoke-R2320.png 860x959). Zero product code changed, so this window "
    "honestly scores 0 product points and the product face carries to R2321."
)

TOKENS_LOG = (
    "R2320 tokens: local=~24k api=0 api_reason=verification-and-repair window "
    "- three full reconcile batteries on disk (the inherited red leg, the "
    "inherited retry, and one clean re-run after a two-writer collision forced "
    "a discard), one birth-site residue repair with a predicted byte delta and a "
    "read-back proof, one single-suite re-run, one four-section follow-up twice "
    "plus one matrix regeneration, one official registry page read and its "
    "records, one smoke evidence render, and the state/export/heartbeat/board "
    "closeout; zero cloud calls and one external read-only page fetch; the "
    "product face resumes at R2321"
)

SELF_HEAL = (
    "R2320 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply it, and this "
    "session runs unelevated, so the definition of the loop hosting this window "
    "was left untouched. Open local-lane item for an elevated window "
    "(eighty-second consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

HONEST = (
    "R2320 honest disclosures: (a) the window inherited red legs rather than "
    "producing them, and it says so: leg 1 was committed by the previous window "
    "and leg 2 was left untracked on disk, so the count of battery runs on "
    "disk is three while this window launched only two. (b) One of those two "
    "launches is deliberately NOT published as evidence: two writers opened the "
    "same evidence file (455 suite notes with 6 duplicated labels and a summary "
    "that disagreed with the note count), so the file was deleted and the run "
    "re-done with a single writer - a corrupt log is worse than a missing one "
    "and the runner cannot detect a second writer. (c) The repair is "
    "bookkeeping, not product: the declaration grew 189 -> 190 entries on a "
    "live DELIVERED reading (state/queue/tech.md:369 carries the CLOSED "
    "review_window_decl row), with the predicted byte delta matching the write "
    "and a read-back proof. (d) The residue class is a REPEATING law, not a "
    "one-off: every fold that archives a round's log block recreates residue for "
    "that round, and the fix has now been applied by hand twice (R2318, R2320). "
    "The R2310 seed residue_triage_append exists for exactly this and stays "
    "unshipped, so the next fold will need the same manual splice - named here "
    "rather than quietly repeated. (e) This window shipped no product code and "
    "scored 0 product points; the tech queue was not touched, so claimable "
    "stays 11 against its floor of 10. (f) tasks.md was left untouched: it is "
    "the P-47 canonical board and carries no row for this tech slice, disclosed "
    "rather than silently skipped."
)

EXPORT_DO = (
    "R2320 验证窗：把 R2319 交给本轮的全量对账电池在已提交树上跑完，并把红腿修在"
    "出生地。前窗遗留两条红腿（4 条断言失败与 2 条断言失败），本轮读出唯一真实"
    "根因——R2319 的 fold 618 把 R2305 的日志块移进归档，该轮因此重新变成「有戳无"
    "日志行」的残留项且没有分诊条目。修复按名补一条分诊条目（33107B → 33490B，预测"
    "字节与实际一致，原子替换+回读证明，不留临时文件），并刻意不重生成整份声明，"
    "因为重生成会把其它条目的理由一并吞掉。修完复跑电池一次性全绿。"
)

EXPORT_CURRENT = (
    "R2320 验证窗完成：全量对账电池在已提交树上 467/467 套件全绿（对账控制项 7/7，"
    "900.3 秒），判据总量 3778 = 预注册目标，与 R2318 的 466/3772 恰好 +1 套件 / "
    "+6 判据；四段随访全 PASS（矩阵重生成 44867B 后逐字节一致、指纹 CLEAN、"
    "profile 逐字节一致、census DRIFT-CLEAN）。残留分诊修复后 6/6 绿、活读 TRIAGED。"
    "同日 QA 每日爬取面已补：官方登记行直读确认 GB 45438-2025 为强制国标且现行。"
)

EXPORT_ARTIFACT = (
    "qa/reconcile-all-R2320-retry2.log（789696B·sha16 fef565e4620c6ba9·RUNNER PASS "
    "467/467·criteria 3778）与 qa/smoke-R2320.log + qa/smoke-R2320.png（当日爬取"
    "证据），2026-11-01"
)

EXPORT_NEXT = (
    "R2321 产品窗：接技术队头 state/queue/tech.md 的 AC-GDRTS1 种子 "
    "src/os/gate_decl_retire_scope.py——让退役计划先读行级作用域（done 才可退，"
    "open/gated 拒绝），判据 AC-GDRTS1..6 已在行内预注册"
)

BOARD_TOP = (
    "- [ ] R2320 first item: THE PRODUCT FACE THE QUEUE HEAD NAMES, after the "
    "battery is green. The R2320 window ran the battery on the committed tree "
    "(467/467 green, criteria 3778) and repaired the one red suite at its birth "
    "site, but shipped no product code, so the face carries here: "
    "state/queue/tech.md prefix AC-GDRTS1, the R2319 seed "
    "src/os/gate_decl_retire_scope.py, whose AC-GDRTS1..AC-GDRTS6 criteria are "
    "pinned inside that row BEFORE any code. Also open and needing an ELEVATED "
    "shell: BigDomain-OSLoop reads LogonType=InteractiveToken (eighty-second "
    "consecutive disclosure; carried as loop-s4u-reconcile in state/debt.md). "
    "Also named and unshipped: the R2310 seed residue_triage_append, because "
    "every fold that archives a round's log block recreates residue for that "
    "round and the fix has now been spliced by hand twice.\n"
)


def write_text(path, text):
    data = text.encode("utf-8")
    temp = path + ".r2320-tmp"
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
        if line.startswith("- [ ] opened=R2319 | item=product-face-R2320"):
            target = index
            break
    if target is None:
        raise SystemExit("E_CLOSE_DEBT_ROW_NOT_FOUND")
    body = lines[target][len("- [ ] "):]
    parts = [part for part in body.split(" | ") if part]
    opened = parts[0]
    item = parts[1]
    note = ""
    for part in parts[2:]:
        if part.startswith("note="):
            note = part[len("note="):]
    note += (
        " Discharged at R2320: the battery ran on the committed repair tree and "
        "read RUNNER PASS 467/467 suites plus controls 7/7 in 900.3s with "
        "criteria 3778 exactly as pre-registered; the one red suite the inherited "
        "retry carried (os-residue-triage AC-RTR6, residue=190 triaged=189) was "
        "the fold-creates-residue law from the R2319 fold 618 and was repaired by "
        "splicing R2305 into the declaration by name (33107B -> 33490B, predicted "
        "equal to measured); all four follow-up sections PASS after the matrix "
        "regeneration."
    )
    lines[target] = ("- [x] %s | %s | closed=R2320 | note=%s"
                     % (opened, item, note))
    write_text(DEBT, nl.join(lines))
    print("debt: product-face-R2320 closed at R2320")


def open_debt_row():
    note = (
        "R2320 closeout: the verification window is discharged and no product "
        "code shipped, so the face the queue head already names carries here - "
        "state/queue/tech.md prefix AC-GDRTS1, the gate_decl_retire_scope seed, "
        "whose criteria are pinned inside that row BEFORE any code. The scope "
        "reading exists because R2319 measured its opposite: a matched DONE row "
        "refuses exactly like a matched OPEN row, so a discharged blocker can "
        "never be retired. Carry also: the R2310 seed residue_triage_append, "
        "because the fold-creates-residue repair has now been spliced by hand "
        "twice (R2318 and R2320)."
    )
    report = DA.append_row(ROOT, "R2320", "product-face-R2321", note,
                           first="yes", execute=True)
    print("debt: %s appended (%dB -> %dB, wrote=%r)"
          % (report.get("item", "product-face-R2321"),
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
        summary = ("Fold R2320: log lines 3..%d (whole round blocks) moved "
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
    report = SF.fold(ROOT, "R2320", 619, 3, end, summary, reserve=delta,
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
    trial = json.loads(json.dumps(state))
    trial["tick"] = 2320
    trial["benchmarks_refreshed"] = "2026-11-01"
    trial["log"].extend([ROUND_LOG, TOKENS_LOG, SELF_HEAL, HONEST])
    rendered = json.dumps(trial, ensure_ascii=False, indent=2) + "\n"
    delta = len(rendered.replace("\n", "\r\n").encode("utf-8")) - \
        os.path.getsize(STATE)
    maybe_fold(state, delta)
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = 2320
    state["benchmarks_refreshed"] = "2026-11-01"
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
        "qa/reconcile-all-R2320-retry2.log",
        "on",
        "R2320 verification window: the full reconcile battery on the committed "
        "tree reads 467/467 suites green with controls 7/7 in 900.3s and criteria "
        "3778, exactly the pre-registered +1 suite / +6 criteria over R2318; the "
        "one red suite the inherited retry carried was the fold-creates-residue "
        "law and was repaired at its birth site by splicing R2305 into the "
        "residue declaration by name (33107B -> 33490B, predicted equal to "
        "measured, read-back proof).",
    ])
    export["results"].insert(0, [
        "R2320",
        "verification window: three battery legs on disk (two inherited red, one "
        "clean re-run after a two-writer collision was discarded), one birth-site "
        "residue repair committed alone, one single-suite re-run, four follow-up "
        "sections PASS after the matrix regeneration to 44867B / 467 suites / "
        "3778 criteria, plus the day's QA crawl round served with one new primary "
        "source (GB 45438-2025 mandatory, in force) and its smoke evidence; zero "
        "product code changed, so the product face carries to R2321.",
    ])
    derived, _state, _export, _pat = CEC.recompute()
    export["self_drive"] = derived
    tick_label = json.loads(io.open(
        os.path.join(BASE, "export_consistency_patterns.json"),
        encoding="utf-8").read())["tick_row_label"]
    for row in export.get("results", []):
        if isinstance(row, list) and len(row) >= 2 and row[1] == tick_label:
            row[0] = "2320"
    raw = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    write_text(EXPORT, raw)
    print("export: refreshed, self_drive recomputed (%d keys)" % len(derived))


def update_heartbeat():
    line = ("tick 2320 2026-11-01 R2320 verification window: the battery on the "
            "committed tree reads RUNNER PASS 467/467 suites plus controls 7/7 in "
            "900.3s with criteria total 3778 exactly as pre-registered (qa/"
            "reconcile-all-R2320-retry2.log 789696B sha16 fef565e4620c6ba9); the "
            "one red suite the inherited retry carried (os-residue-triage AC-RTR6 "
            "residue=190 triaged=189) was the fold-creates-residue law from the "
            "R2319 fold 618 and was repaired at its birth site by splicing R2305 "
            "into the residue declaration by name (33107B -> 33490B, predicted "
            "equal to measured, read-back proof, no temp residue) - committed "
            "alone as 26eecc98 - after which the suite reads 6/6 with verdict "
            "TRIAGED; four follow-up sections PASS after the matrix regeneration "
            "to 44867B / 467 suites / 3778 criteria. Zero product code changed, "
            "so the product face (tech head AC-GDRTS1 gate_decl_retire_scope) "
            "carries to R2321.\n")
    with io.open(HEART, "r", encoding="utf-8") as handle:
        text = handle.read()
    if not text.endswith("\n"):
        text += "\n"
    write_text(HEART, text + line)
    print("heartbeat: appended tick 2320")


def update_board():
    with io.open(BOARD, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    if not text.startswith("- [ ] R2319 first item"):
        raise SystemExit("E_CLOSE_BOARD_TOP")
    first_end = text.index(nl)
    head = text[:first_end]
    rest = text[first_end:]
    closed = "- [x]" + head[len("- [ ]"):]
    text = closed + rest
    text = BOARD_TOP.replace("\n", nl) + text
    write_text(BOARD, text)
    print("board: R2319 row closed, R2320 first item inserted")


def main():
    close_debt_row()
    open_debt_row()
    append_state()
    update_export()
    update_heartbeat()
    update_board()


if __name__ == "__main__":
    main()