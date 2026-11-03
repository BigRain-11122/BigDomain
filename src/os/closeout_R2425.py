"""R2425 closeout: state tick, log lines, export face, backlog, heartbeat."""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
STATE = os.path.join(SRC, "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
PATTERNS = os.path.join(SRC, "export_consistency_patterns.json")
BACKLOG = os.path.join(SRC, "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
STAMP = "2026-11-04T04:54:06+08:00"
ROUND = 2425
GATE = 78500
RESERVE = 6000

LINES = [
    "2026-11-04 R2425 verification window (five-silence scan clean at open: git status empty at HEAD 6be56640 with no .git/index.lock; the whole-file search of the evolution ledger for @BigDomain returns 0 rows; the content-addressed decisions diff read 157 rows and 105 tokens with new=0 against the stored baseline; the group orders tail max_ts is the 2026-11-04 00:46 OB-20261104-004657-271 de-AI face/voice line already judged not-this-company at R2421, so the baseline stands; benchmarks refreshed 2026-11-03 inside the seven-day gate; queue floor FLOOR-MET main 5/5 tech 10/10 explore 10/10 with tech head line 490 prefix AC-PICBW1 claimable=10). The debt gate named CLAIM-FIRST item=reconcile-battery-R2425 with a pre-registered target of 540 suites / 4216 criteria, so the battery ran FIRST on the committed tree with zero product edits.",
    "2026-11-04 R2425 the battery matched its prediction to the unit: python src/os/battery_stream.py --evidence qa/reconcile-all-R2425.log read RUNNER PASS (540/540 suites green, reconcile controls 7/7, 942.7s) and the matrix regeneration measured 540 suites / 4216 criteria - the pre-registered number exactly - plus TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 MiB; the evidence file is 845614B written by the shipped streamer.",
    "2026-11-04 R2425 the four follow-up sections produced the designed first FAIL and then a green verdict: leg1 VERDICT FAIL failing=matrix at on-disk=51924B against regenerated=52001B (the shipped doc was the R2423 render and did not rewrite itself), src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md to 52001B at 540 suites / 4216 criteria with --check reading byte-identical, and the re-run read VERDICT R2425 PASS failing=none (matrix byte-identical 52001B, fingerprint CLEAN domains=5, profile byte-identical, census DRIFT-CLEAN). Both legs stay appended in the evidence tail (1889B FAIL then 1950B PASS, eol_ok=True).",
    "2026-11-04 R2425 debt register after this window: open=3 done=138. reconcile-battery-R2425 was closed through the shipped debt_close at its predicted 103680B -> 103683B (measured exactly, readback=ok) and ONE leader row product-face-R2426 was appended first=yes through the shipped debt_append at its predicted 103683B -> 104274B (readback=ok), naming the next window a product face on the tech head state/queue/tech.md:490 prefix AC-PICBW1 whose AC-PICBW1..AC-PICBW6 were pinned at R2424 before any code. No successor battery was registered: no product and no registry byte changed (this window's only src write is the one-off closeout_R2425.py, which is registered as no suite and moves no suite or criteria count), so the R2168 mixed-tree rule does not fire. Remaining open: loop-s4u-reconcile and stale-suite-matrix-copy, neither discharged here.",
    "2026-11-04 R2425 honest disclosures: (a) this window shipped ZERO product code and scores 0 product points, deliberately - the R2168 mixed-tree rule makes a product edit inside a verification window invalidate the measurement the window exists to produce, and the only src write here is the unregistered one-off closeout_R2425.py; (b) the battery was launched detached through Start-Process and the first poll was cancelled by the shell no-output rule at the five-minute gate, so the process was verified ALIVE by process id (51496, created 04:35:02) before polling continued and no second launch happened; (c) the window ran past its 25-minute budget - the battery alone cost 942.7s plus the regeneration and re-run legs - named rather than hidden; (d) tasks.md was not touched, it is the P-47 canonical board and carries no row for this verification window; (e) the two stale rows loop-s4u-reconcile and stale-suite-matrix-copy were NOT discharged here.",
    "R2425 tokens: local=~15k api=0 api_reason=verification window - one full battery on the committed tree at a pre-registered target that matched exactly (540 suites / 4216 criteria), four follow-up sections with one intended matrix FAIL traced to a genuinely stale document and one green verdict after regenerating it, one debt row closed and one leader row opened through their shipped CLIs, and the state/export/backlog/heartbeat closeout; zero product code shipped, zero cloud calls and zero external API touches",
    "2026-11-04 R2425 self-heal check: BigDomain-OSLoop exists and its Principal.LogonType still reads Interactive, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 passes an explicit S4U principal and needs an elevated shell while this session is unelevated, so the definition was left untouched again (hundred-and-ninety-fifth consecutive disclosure, carried as the stale row loop-s4u-reconcile).",
]

EXPORT_DO = (
    "R2425 verification window: the full reconcile battery on the committed "
    "R2424 tree read RUNNER PASS 540/540 suites plus controls 7/7 in 942.7s at "
    "the pre-registered 540 suites / 4216 criteria measured exactly, then all "
    "four follow-up sections PASS after regenerating the matrix doc to 52001B"
)
EXPORT_ARTIFACT = (
    "qa/reconcile-all-R2425.log (845614B, RUNNER PASS 540/540, criteria 4216) "
    "+ docs/sandbox-suite-matrix.md regenerated to 52001B, 540 suites / 4216 "
    "criteria, --check byte-identical"
)
EXPORT_MILESTONE = (
    "product face on the tech head state/queue/tech.md:490 prefix AC-PICBW1 "
    "(comma_binding_wire, AC-PICBW1..AC-PICBW6 pinned at R2424): the reading "
    "NAMES the dropped import part while the receiver table still drops it, so "
    "callee_of on a comma list returns module \"\" and the identity reading "
    "answers UNRESOLVED for a publisher a bare call would resolve"
)
EXPORT_DUE = "2026-11-05T22:00:00+08:00"

BACKLOG_ROWS = [
    "- [x] [done 2026-11-04 R2425] R2425 verification window: the debt gate "
    "named CLAIM-FIRST item=reconcile-battery-R2425 (first=yes, carried=1), so "
    "the battery ran FIRST on the committed 6be56640 tree with zero product "
    "edits and read RUNNER PASS 540/540 suites plus controls 7/7 in 942.7s "
    "with the criteria total measuring 4216 - the pre-registered number to the "
    "unit (qa/reconcile-all-R2425.log, 845614B, TMP RECLAIM 932/932, 326.59 "
    "MiB reclaimed). The four follow-up sections then read VERDICT FAIL "
    "failing=matrix at on-disk=51924B against regenerated=52001B because the "
    "shipped doc was still the R2423 render; docs/sandbox-suite-matrix.md was "
    "regenerated to 52001B at 540 suites / 4216 criteria with suite_matrix "
    "--check byte-identical, and the re-run read all four sections PASS "
    "(matrix byte-identical 52001B, fingerprint CLEAN domains=5, profile "
    "byte-identical, census DRIFT-CLEAN) for VERDICT R2425 PASS failing=none. "
    "Register: reconcile-battery-R2425 closed through debt_close at its "
    "predicted 103680B -> 103683B (measured exactly, readback=ok) and NO "
    "successor battery was registered because no product and no registry byte "
    "changed (the only src write is the unregistered one-off "
    "closeout_R2425.py), so the gate owed a leader and product-face-R2426 was "
    "appended first=yes "
    "through debt_append (103683B -> 104274B, readback=ok). Zero product code "
    "shipped, honestly 0 product points. Disclosed rather than swept: the "
    "detached battery's first poll was cancelled at the five-minute no-output "
    "gate and the process was verified ALIVE by process id afterwards.\n",
    "- [ ] [carried 2026-11-04 R2425] R2426 first item: PRODUCT face on the "
    "tech head state/queue/tech.md:490 prefix AC-PICBW1 (comma_binding_wire), "
    "whose AC-PICBW1..AC-PICBW6 were pinned at R2424 before any code. No "
    "battery is owed at open - the R2425 battery is green on the current tree - "
    "but any src/ byte this window changes re-arms the R2168 rule for R2427 at "
    "the then-measured registry target. Still carried and needing an ELEVATED "
    "shell: BigDomain-OSLoop reads LogonType=InteractiveToken (state/debt.md "
    "row loop-s4u-reconcile); stale-suite-matrix-copy also remains open.\n",
]


def _read(path, newline=None):
    with io.open(path, "r", encoding="utf-8", newline=newline) as handle:
        return handle.read()


def _write(path, text, newline=""):
    with io.open(path, "w", encoding="utf-8", newline=newline) as handle:
        handle.write(text)


def step_state():
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    import state_io
    state = json.loads(_read(STATE))
    before = state["tick"]
    state["tick"] = before + 1
    state["last_order"] = "2026-11-04 00:46"
    state["last_decision_rows"] = 157
    state["benchmarks_refreshed"] = "2026-11-03"
    state["log"].extend(LINES)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = STATE + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, STATE)
    back = json.loads(_read(STATE))
    if back["tick"] != state["tick"] or len(back["log"]) != len(state["log"]):
        raise SystemExit("E_CLOSEOUT_READBACK")
    size = os.path.getsize(STATE)
    print("state tick %d -> %d lines=%d bytes=%d"
          % (before, state["tick"], len(state["log"]), size))
    if size > GATE - RESERVE:
        print("WARNING state above gate-reserve, a fold window is due")


def step_export():
    patterns = json.loads(_read(PATTERNS))
    label = patterns["tick_row_label"]
    export = json.loads(_read(EXPORT))
    export["export_ts"] = STAMP
    export["do"] = EXPORT_DO
    face = export["ceo_face"]
    face["current"] = EXPORT_DO
    face["latest_artifact"] = EXPORT_ARTIFACT
    face["last_artifact"] = EXPORT_ARTIFACT
    face["next_milestone"] = EXPORT_MILESTONE
    face["next_milestone_due"] = EXPORT_DUE
    face["updated_at"] = STAMP
    results = [row for row in export["results"] if str(row[0]) != str(ROUND)]
    results.insert(0, [str(ROUND), EXPORT_DO])
    labelled = [row for row in results if len(row) >= 2 and row[1] == label]
    if not labelled:
        results.insert(0, [str(ROUND), label])
    else:
        for row in labelled:
            row[0] = str(ROUND)
    export["results"] = results
    outs = [item for item in export["outs"]
            if "plain_import_comma_binding" not in str(item)]
    outs.insert(0, EXPORT_ARTIFACT)
    export["outs"] = outs
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    import check_export_consistency
    derived = check_export_consistency.recompute()[0]
    drive = export["self_drive"]
    drive["log_lines_in_window"] = derived["log_lines_in_window"]
    drive["substantive_non_idle_mention_lines"] = \
        derived["substantive_non_idle_mention_lines"]
    import queue_floor
    gauge = queue_floor.gauge(ROOT)
    fresh = dict((row["queue"], row) for row in gauge["queues"])
    for row in export["queue"]["queues"]:
        live_row = fresh.get(row.get("queue"))
        if not live_row:
            continue
        for key, value in live_row.items():
            row[key] = value
    export["queue"]["floors"] = gauge["floors"]
    export["queue"]["verdict"] = gauge["verdict"]
    text = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    _write(EXPORT, text, newline="\n")
    print("export refreshed %dB queues=%s"
          % (len(text.encode("utf-8")), gauge["verdict"]))


def step_backlog():
    text = _read(BACKLOG)
    added = 0
    for row in BACKLOG_ROWS:
        head = row.split("] ")[0] + "]"
        if head in text and row.split(": ")[0][:60] in text:
            continue
        if not text.endswith("\n"):
            text += "\n"
        text += row
        added += 1
    _write(BACKLOG, text, newline="\n")
    print("backlog rows added=%d bytes=%d"
          % (added, len(text.encode("utf-8"))))


def step_heartbeat():
    line = ("2026-11-04T04:54:06+08:00 tick=2425 R2425 verification window - "
            "battery RUNNER PASS 540/540 suites plus controls 7/7 in 942.7s at "
            "the pre-registered 540 suites / 4216 criteria measured exactly, "
            "four follow-up sections PASS after the matrix doc was regenerated "
            "to 52001B, battery row closed and product-face-R2426 opened")
    text = _read(HEARTBEAT)
    if line in text:
        print("heartbeat line already present")
        return
    if not text.endswith("\n"):
        text += "\n"
    _write(HEARTBEAT, text + line + "\n", newline="\n")
    print("heartbeat appended")


if __name__ == "__main__":
    step_state()
    step_export()
    step_backlog()
    step_heartbeat()