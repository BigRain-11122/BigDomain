"""R2325 closeout: queue row, successor seed, debt, state, export, heartbeat.

This window shipped the followup retry history: the aggregate the house prints
now judges every round by its LAST leg, so a round recovered by a green retry
stops counting as red (live at R2303 the aggregate read rounds=427 red=412
with four retried rounds; this window's live read is rounds=438 green=20
retried=6 recovered=5 unfixed=413 regressed=0).

ASCII source; the Chinese CEO face lives in docs/status-export.json.

Usage: python src/os/closeout_R2325.py
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
    "2026-11-01 R2325 product window (five-silence scan clean at open: empty "
    "git status --short and no index.lock; decisions.md carried 84 non-empty "
    "rows equal to the stored baseline (no new decision row was presented to "
    "the gate this window); the group ledger carries the same three @BigDomain "
    "patrol rows already paid off, the last one P-20261026-0930 acked at R2311, "
    "with zero unreplied numbered handoffs; the group orders tail is unchanged "
    "at the 2026-11-01 10:4x baseline R2321 acked by number as non-execution; "
    "benchmarks refreshed 2026-11-01 inside the seven-day gate). The P1 "
    "canonical rows stay blocked-on-CEO, the weekly proposal duty is met by "
    "BD-PROP-005, the floors read FLOOR-MET main 5/5 tech 10/10 explore 10/10, "
    "and the debt gate named exactly one first=yes row (product-face-R2324), so "
    "this window claimed the TOP deliverable tech row named by the board: "
    "state/queue/tech.md:380 prefix AC-FRH1, the R2303 followup_retry_history "
    "seed whose AC-FRH1..AC-FRH6 criteria were pinned INSIDE that row BEFORE the "
    "code (re-read, not re-run). PRODUCT: src/os/followup_retry_history.py plus "
    "src/os/test_followup_retry_history.py - the house aggregate "
    "(followup_history --history) still judged every round from its canonical "
    "leg alone, so the four rounds a green retry had repaired were counted red "
    "and the aggregate could never read ALL-GREEN (live at R2303: rounds=427 "
    "red=412 with four retried rounds). The new reading is one pass over the "
    "whole directory whose per-round verdict and leg order are ASKED of "
    "followup_retry_legs (a patched joiner moves it - the suite proves it by "
    "replacing FR.history), splitting every round into four disjoint classes: "
    "green (canonical PASS, last PASS), recovered (canonical not PASS, last "
    "PASS), unfixed (canonical not PASS, last not PASS) and regressed "
    "(canonical PASS, last not PASS - reported instead of folded into green), "
    "with recovered + unfixed PARTITIONING the rounds whose canonical leg is not "
    "PASS and a count self-check that refuses E_FRH_COUNT if they ever stop "
    "partitioning. A round with no retry leg keeps exactly the followup_history "
    "reading (inherited, asserted key by key), and the naming law is asked of "
    "retry_naming so an orphan retry leg - invisible to the canonical-only "
    "collector - is REFUSED E_FRTL_ORPHAN_RETRY at exit 3 instead of dropping "
    "out of the counts. SUITE PASS 6/6 twice with an identical criterion digest, "
    "four adjacent followup suites green (retry_legs 6/6, history 7/7, "
    "retry_naming 9/9, evidence_variants 6/6), qa/followup-retry-history-"
    "R2325.log 1338B as one utf-8 LF single writer through the evidence_capture "
    "callable, one runner wiring line (os-followup-retry-history, 6). LIVE ON "
    "THE REAL PILE: rounds=438 green=20 retried=6 recovered=5 unfixed=413 "
    "regressed=0 verdict=HISTORY-DEBT - and the five recovered rounds are named "
    "(R2277, R2289, R2299, R2318, R2320), which is exactly the reading the "
    "canonical-only aggregate could never produce. One tech row closed; "
    "claimable tech falls 10 -> 9, so ONE real gap row was seeded from this "
    "window's own measurement (followup_incomplete_cause, AC-FIC1..AC-FIC6 "
    "pre-registered, five anchors git grep -F zero-occupancy)."
)

TOKENS_LOG = (
    "R2325 tokens: local=~17k api=0 api_reason=product window on the tech head - "
    "one aggregate reader with its six pre-registered criteria and its suite "
    "(green after two this-window defects were corrected against the measured "
    "truth, one of them a real gap the criterion exposed), one dogfooded "
    "evidence capture (two legs identical, four adjacent suites green), one live "
    "reading of the whole 438-round pile, one runner wiring line, one queue "
    "close and one real gap row seeded through the anchor check, one waterline "
    "fold, and the debt/state/export/heartbeat/board closeout; zero cloud calls "
    "and zero external API touches; the battery carries to R2326"
)

SELF_HEAL = (
    "R2325 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply it, and this "
    "session runs unelevated, so the definition of the loop hosting this window "
    "was left untouched. Open local-lane item for an elevated window "
    "(eighty-seventh consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

HONEST = (
    "R2325 honest disclosures: (a) the first suite run was red 4/6 and BOTH "
    "causes were this-window defects, never a criterion widened: AC-FRH3 "
    "expected canonical_verdict INCOMPLETE for a log whose RUNNER line says FAIL "
    "while its sections are absent, and the reader honestly reports FAIL as the "
    "canonical verdict with the round still INCOMPLETE - the assertion now names "
    "the measured truth; (b) AC-FRH4 was the other red and it was a REAL gap the "
    "criterion caught in the module: followup_history.collect enumerates "
    "CANONICAL names only, so an orphan retry leg was invisible to the aggregate "
    "and would have been silently dropped - the module now scans the evidence "
    "directory for retry-named files, asks retry_naming which of them are retry "
    "legs and which stem each belongs to, and hands the stem to "
    "followup_retry_legs.leg_names, which raises E_FRTL_ORPHAN_RETRY; the fix is "
    "in the module, not the test. (c) The `regressed` class is an ADDITION, not a "
    "widened criterion: AC-FRH2's partition is asserted exactly over the "
    "canonical-not-PASS set, and a round whose canonical PASSed but whose last "
    "leg went red is reported separately rather than quietly folded into green "
    "or into unfixed. (d) The live reading is 413 unfixed and that is disclosed "
    "as the honest size of the pile, not as a defect of this reader: most of "
    "those logs predate the SECTION ritual and read INCOMPLETE by law - which is "
    "precisely the gap the successor seed is written from. (e) The full "
    "reconcile battery did NOT run here (the R2168 mixed-tree rule keeps it on a "
    "committed tree), so the successor carries it with the pre-registered target "
    "of 471 suites / 3802 criteria - exactly +1 suite / +6 criteria against "
    "R2324 (470/3796) from this window's own os-followup-retry-history suite. "
    "(f) tasks.md was left untouched: it is the P-47 canonical board and carries "
    "no row for this tech slice, disclosed rather than silently skipped."
)

EXPORT_DO = (
    "R2325 产品窗：让「本司跟进聚合」按最后一腿判读。R2303 的 joiners 只修了单轮读，"
    "而厂里真正打印的 aggregate 仍按 canonical 腿判每一轮——被绿色 retry 修好的轮次"
    "永远计红（R2303 实测 rounds=427 red=412，其中 4 轮有 retry）。本轮交付 "
    "src/os/followup_retry_history.py：整目录一遍读，每轮判读与腿序全部问 "
    "followup_retry_legs，分成 green / recovered / unfixed / regressed 四类互斥，"
    "recovered + unfixed 恰好划分 canonical 未 PASS 的轮次，并带自检（不再划分即拒"
    "E_FRH_COUNT）；无 retry 的轮次逐键等同于 followup_history 的读解；孤儿 retry "
    "（canonical 已不在）经命名律发现后拒绝 E_FRTL_ORPHAN_RETRY，不再从计数里消失。"
)

EXPORT_CURRENT = (
    "R2325 产品窗完成：跟进聚合最后一腿判读 src/os/followup_retry_history.py 落盘并"
    "接线，套件 6/6 双腿全绿、四套相邻跟进套件同时绿，证据 "
    "qa/followup-retry-history-R2325.log（1338B）。真实全堆实测：rounds=438 "
    "green=20 retried=6 recovered=5 unfixed=413 regressed=0，verdict=HISTORY-DEBT"
    "——五轮被 retry 修复（R2277/R2289/R2299/R2318/R2320）现已点名可见。技术队列"
    "可认领 9，已从本轮自身读数补种一条真缺口行（followup_incomplete_cause）。"
)

EXPORT_ARTIFACT = (
    "src/os/followup_retry_history.py（+ 测试套件 6 判据）与 "
    "qa/followup-retry-history-R2325.log（1338B·双腿一致·四套相邻全绿），2026-11-01"
)

EXPORT_NEXT = (
    "R2326 验证轮：在已提交树上跑全量对账电池（预注册目标 471 套件 / 3802 判据 = "
    "相对 R2324 的 470/3796 恰好 +1 套件 / +6 判据），矩阵重生成后四段随访必须全 "
    "PASS；随访后回产品面，接技术队头新种子 followup_incomplete_cause（把「为什么"
    "是 INCOMPLETE」从一句状态变成分类读数）"
)

BOARD_DONE = (
    " [done 2026-11-01 R2325 - the aggregate finally reads the retry family: "
    "src/os/followup_retry_history.py classifies every round into green / "
    "recovered / unfixed / regressed from the LAST leg while the reading and the "
    "leg order are asked of followup_retry_legs, recovered + unfixed partition "
    "the canonical-not-PASS set with a counting self-check (E_FRH_COUNT), a "
    "canonical-only round keeps the followup_history reading key by key, and an "
    "orphan retry leg is refused E_FRTL_ORPHAN_RETRY at exit 3 instead of "
    "vanishing from the counts (the naming law asked of retry_naming). SUITE "
    "PASS 6/6 twice, four adjacent followup suites green, evidence "
    "qa/followup-retry-history-R2325.log 1338B through the evidence_capture "
    "callable, one runner wiring line os-followup-retry-history(6). LIVE: "
    "rounds=438 green=20 retried=6 recovered=5 unfixed=413 regressed=0 "
    "verdict=HISTORY-DEBT with the five recovered rounds named. Claimable tech "
    "10 -> 9, so one real gap row (followup_incomplete_cause, AC-FIC1..AC-FIC6 "
    "pre-registered, five anchors zero-occupancy) holds the floor]"
)

BOARD_TOP = (
    "- [ ] R2326 first item: THE BATTERY ON THE COMMITTED TREE, zero product "
    "edits until green (the R2168 mixed-tree rule). R2325 changed src/os "
    "(followup_retry_history.py, test_followup_retry_history.py, "
    "src/sandbox/reconcile_all.py, closeout_R2325.py), closed one tech row and "
    "seeded one, and folded state.json, so the pre-registered target is 471 "
    "suites / 3802 criteria - exactly +1 suite / +6 criteria against R2324 "
    "(470/3796) from the os-followup-retry-history suite, and any larger delta "
    "must be named rather than swept. Run the full battery on the committed tree "
    "with an empty git status, then all four follow-up sections AFTER "
    "regenerating the matrix (the FAIL-then-PASS order is designed), and on "
    "green go back to the product face the queue head names: the "
    "followup_incomplete_cause seed (AC-FIC1..AC-FIC6 pinned in that row) turns "
    "'why is this round INCOMPLETE' into a classification - legacy logs that "
    "predate the SECTION ritual, logs with no VERDICT line, and logs with "
    "sections genuinely missing currently read identically. Also open and "
    "needing an ELEVATED shell: BigDomain-OSLoop reads "
    "LogonType=InteractiveToken (eighty-seventh consecutive disclosure; carried "
    "as loop-s4u-reconcile in state/debt.md). Also still unshipped and named: "
    "the R2310 seed residue_triage_append, because every fold that archives a "
    "round whose stamp sits on an open row recreates residue, and the repair has "
    "been spliced by hand four times.\n"
)

SEED_ROW = (
    "- [ ] P2 tech seed (R2325, from this window own live reading): "
    "`src/os/followup_incomplete_cause.py` - followup_retry_history now names "
    "which rounds are unfixed (live: 413 of 438), but every one of them reads "
    "the same word. The measured truth at R2325 is that at least three different "
    "things land in INCOMPLETE: a legacy log that predates the SECTION ritual "
    "and can never carry sections, a log with no VERDICT line at all, and a log "
    "whose follow-up genuinely ran but lost a section. Those are different "
    "debts, and today they are indistinguishable. Product: one reader whose "
    "cause verdict is derived from the log itself - LEGACY-DIALECT (sections and "
    "VERDICT both absent, with the round range named), NO-VERDICT (sections "
    "present, no VERDICT line), MISSING-SECTION (a VERDICT line exists but named "
    "sections are ABSENT, listing them), and COMPLETE (nothing absent) - so the "
    "aggregate can be split into debt that will never heal by re-reading and "
    "debt a rerun would fix. Criteria prefix AC-FIC1..AC-FIC6 pre-registered "
    "HERE BEFORE any code: AC-FIC1 the absent-section and verdict readings are "
    "asked of followup_history and a patched parser flows straight through; "
    "AC-FIC2 the four causes are disjoint and every round lands in exactly one; "
    "AC-FIC3 the cause is derived from the log alone - no clock, no round-number "
    "threshold baked in; AC-FIC4 an unreadable or absent log still refuses at "
    "exit 3 with its own code and never reads COMPLETE; AC-FIC5 read-only with "
    "the tree digest identical before and after, CLI 0 when every round is "
    "COMPLETE, 2 when any round is not, 5 on bad flags, byte-stable --json over "
    "pinned keys; AC-FIC6 pure-ASCII source, stdlib only, zero network, plus its "
    "own reconcile label. Anchor check at HEAD 2026-11-01: "
    "followup_incomplete_cause, AC-FIC, E_FIC, test_followup_incomplete_cause "
    "and os-followup-incomplete-cause were all git grep -F zero-occupancy rc=1."
)


def write_text(path, text):
    data = text.encode("utf-8")
    temp = path + ".r2325-tmp"
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
        if line.startswith("- [ ] P2 tech seed (R2303,") \
                and "followup_retry_history.py" in line:
            target = index
            break
    if target is None:
        print("queue: row already closed")
        return
    lines[target] = lines[target].replace(
        "- [ ] ", "- [x] [done 2026-11-01 R2325] ", 1) + BOARD_DONE
    write_text(TECH, nl.join(lines))
    print("queue: tech row 380 closed")


def seed_queue_row():
    with io.open(TECH, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "followup_incomplete_cause.py" in text:
        print("queue: seed already present")
        return
    nl = "\r\n" if "\r\n" in text else "\n"
    if not text.endswith(nl):
        text += nl
    write_text(TECH, text + SEED_ROW.replace("\n", nl) + nl)
    print("queue: followup_incomplete_cause seed appended")


def close_debt_row():
    with io.open(DEBT, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    target = None
    for index, line in enumerate(lines):
        if line.startswith("- [ ] opened=R2324 | item=product-face-R2324"):
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
    lines[target] = ("- [x] %s | %s | closed=R2325 | note=%s"
                     % (opened, item, note))
    write_text(DEBT, nl.join(lines))
    print("debt: product-face-R2324 closed at R2325")


def open_debt_row():
    note = (
        "R2325 closeout: the aggregate reader shipped and the live pile now "
        "reads 438 rounds with 20 green, 6 retried, 5 recovered, 413 unfixed and "
        "0 regressed, so the rounds a green retry had repaired are named instead "
        "of counted red. The next window runs the battery the R2168 mixed-tree "
        "rule defers on the committed R2325 tree with the pre-registered target "
        "of 471 suites and 3802 criteria, then takes the product face the queue "
        "head names (followup_incomplete_cause). Carry also the R2310 seed "
        "residue_triage_append, because every fold that archives a round whose "
        "stamp sits on an open row recreates residue and the repair has been "
        "spliced by hand four times (R2318, R2320, R2322, R2324 measured none)."
    )
    existing = io.open(DEBT, "r", encoding="utf-8").read()
    if "item=product-face-R2326" in existing:
        print("debt: product-face-R2326 already open")
        return
    report = DA.append_row(ROOT, "R2325", "product-face-R2326", note,
                           first="yes", execute=True)
    print("debt: product-face-R2326 appended (%sB -> %sB, wrote=%r)"
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
        summary = ("Fold R2325: log lines 3..%d (whole round blocks) moved "
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
    report = SF.fold(ROOT, "R2325", 620, 3, end, summary, reserve=delta,
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
    if state["tick"] == 2325:
        print("state: already at tick 2325")
        return
    trial = json.loads(json.dumps(state))
    trial["tick"] = 2325
    trial["log"].extend([ROUND_LOG, TOKENS_LOG, SELF_HEAL, HONEST])
    rendered = json.dumps(trial, ensure_ascii=False, indent=2) + "\n"
    delta = len(rendered.replace("\n", "\r\n").encode("utf-8")) - \
        os.path.getsize(STATE)
    maybe_fold(state, delta)
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = 2325
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
        "src/os/followup_retry_history.py",
        "on",
        "R2325 产品窗：跟进聚合不再只按 canonical 腿判读。整目录一遍读，按最后一腿"
        "把每轮分成 green / recovered / unfixed / regressed 四类互斥，recovered + "
        "unfixed 恰好划分 canonical 未 PASS 的轮次并带自检；无 retry 的轮次逐键等"
        "同旧读解；孤儿 retry 被发现即拒绝而不是从计数里消失。套件 6/6 双腿一致＋"
        "四套相邻全绿；真实全堆实测 rounds=438 green=20 retried=6 recovered=5 "
        "unfixed=413 regressed=0，五轮被 retry 修复的轮次已点名。",
    ])
    export["results"].insert(0, [
        "R2325",
        "product window: src/os/followup_retry_history.py with its six "
        "pre-registered criteria, one runner wiring line, one evidence capture "
        "(qa/followup-retry-history-R2325.log 1338B, two identical legs plus "
        "four adjacent followup suites green) and one live reading over 438 "
        "rounds that names the five recovered rounds; one tech row closed and "
        "one real gap row seeded, because claimable fell 10 -> 9.",
    ])
    derived, _state, _export, _pat = CEC.recompute()
    export["self_drive"] = derived
    tick_label = json.loads(io.open(
        os.path.join(BASE, "export_consistency_patterns.json"),
        encoding="utf-8").read())["tick_row_label"]
    for row in export.get("results", []):
        if isinstance(row, list) and len(row) >= 2 and row[1] == tick_label:
            row[0] = "2325"
    raw = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    write_text(EXPORT, raw)
    print("export: refreshed, self_drive recomputed (%d keys)" % len(derived))


def update_heartbeat():
    line = ("tick 2325 2026-11-01 R2325 product window: the aggression of the "
            "follow-up aggregate is gone - src/os/followup_retry_history.py "
            "judges every round by its LAST leg and splits the pile into green / "
            "recovered / unfixed / regressed, with recovered + unfixed "
            "partitioning the rounds whose canonical leg is not PASS and a "
            "counting self-check that refuses E_FRH_COUNT if they stop doing so; "
            "an orphan retry leg is refused E_FRTL_ORPHAN_RETRY instead of "
            "vanishing. Suite 6/6 twice plus four adjacent followup suites green "
            "(qa/followup-retry-history-R2325.log 1338B). LIVE: rounds=438 "
            "green=20 retried=6 recovered=5 unfixed=413 regressed=0 "
            "verdict=HISTORY-DEBT with R2277/R2289/R2299/R2318/R2320 named as "
            "recovered. One tech row closed, one real gap row seeded "
            "(followup_incomplete_cause); the battery carries to R2326 with a "
            "pre-registered 471 suites / 3802 criteria.\n")
    with io.open(HEART, "r", encoding="utf-8") as handle:
        text = handle.read()
    if not text.endswith("\n"):
        text += "\n"
    write_text(HEART, text + line)
    print("heartbeat: appended tick 2325")


def update_board():
    with io.open(BOARD, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    if text.startswith("- [ ] R2325 first item") or \
            text.startswith("- [x] R2324 first item"):
        print("board: already closed")
        return
    if not text.startswith("- [ ] R2324 first item"):
        raise SystemExit("E_CLOSE_BOARD_TOP")
    first_end = text.index(nl)
    closed = "- [x]" + text[len("- [ ]"):first_end]
    text = closed + text[first_end:]
    text = BOARD_TOP.replace("\n", nl) + text
    write_text(BOARD, text)
    print("board: R2324 row closed, R2325 first item inserted")


def main():
    close_queue_row()
    seed_queue_row()
    close_debt_row()
    open_debt_row()
    append_state()
    update_export()
    update_heartbeat()
    update_board()


if __name__ == "__main__":
    main()