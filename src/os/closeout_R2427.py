"""R2427 closeout: state tick, log lines, export face, backlog, heartbeat."""
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
STAMP = "2026-11-04T07:05:00+08:00"
ROUND = 2427
GATE = 78500
RESERVE = 6000

LINES = [
    "2026-11-04 R2427 verification window (five-silence scan clean at open: "
    "git status empty with no .git/index.lock; the evolution ledger carries "
    "zero @BigDomain rows; the content-addressed decisions diff read 208 lines "
    "and 105 tokens with new=0 against the stored baseline, so the 208-vs-157 "
    "row gap is a row-counting dialect and not a dispatch; the group orders "
    "tail max_ts is still the 2026-11-04 00:46 OB-20261104-004657-271 fleet "
    "line already judged not-this-company; benchmarks refreshed 2026-11-03 "
    "inside the seven-day gate; queue floor FLOOR-MET main 5/5 tech 10/10 "
    "explore 10/10). The debt gate named CLAIM-FIRST item="
    "reconcile-battery-R2427 opened=R2426 carried=1 open=3 first=1 at the "
    "pre-registered 541 suites / 4222 criteria, so the battery ran FIRST on "
    "the committed R2426 tree with zero product edits (the R2168 mixed-tree "
    "rule).",
    "2026-11-04 R2427 the battery read RUNNER PASS 541/541 suites green with "
    "reconcile controls 7/7 in 948.0s and criteria total 4222 EXACTLY as "
    "pre-registered (qa/reconcile-all-R2427.log, 842kB, single-writer utf-8 "
    "LF through the runner own Tee), TMP RECLAIM candidates=932 removed=932 "
    "busy=0 failed=0 reclaimed=326.59 MiB. The four follow-up sections then "
    "ran in the designed order and produced the designed first red instead of "
    "a pass: SECTION matrix FAIL at on-disk=52001B against regenerated=52086B "
    "and the section wrote no byte, fingerprint CLEAN domains=5, profile "
    "byte-identical, census DRIFT-CLEAN, VERDICT R2427 FAIL failing=matrix "
    "appended (1889B, eol_ok=True). docs/sandbox-suite-matrix.md was then "
    "regenerated from THAT green evidence through suite_matrix --stamp-from "
    "so the render is stamp-aligned to the doc it is compared with, "
    "suite_matrix --check read byte-identical at 52086B / 541 suites / 4222 "
    "criteria, and the re-run read all four sections PASS for VERDICT R2427 "
    "PASS failing=none (1950B appended).",
    "2026-11-04 R2427 debt register, both rows closed and one successor "
    "appended through their shipped CLIs with readback=ok: reconcile-battery-"
    "R2427 closed at its predicted 104802B -> 104805B, and the sixteen-window "
    "open stale-suite-matrix-copy was closed at 104805B -> 104809B AND "
    "actually discharged - docs/suite-matrix.md was a 34452B 2026-10-27 "
    "render of the same generator (352 suites) whose only live references "
    "were its own debt row and its own backlog note, so it was removed with "
    "git rm and git ls-files now reads zero for that path; the canonical "
    "docs/sandbox-suite-matrix.md is the only matrix document in the tree. "
    "The successor product-face-R2428 was appended first=yes at 104809B -> "
    "105512B naming the tech head the queue reader names - state/queue/"
    "tech.md:491 prefix AC-PICBC1, comma_binding_consumer_wire with "
    "AC-PICBC1..AC-PICBC6 pinned at R2426 BEFORE any code.",
    "2026-11-04 R2427 honest disclosures: (a) this window shipped ZERO "
    "product code and claims zero product points - the battery consumed the "
    "window, exactly as the carried row said it would; (b) an operator error "
    "was caught and repaired on the spot: `python src/sandbox/reconcile_all.py "
    "--help` was run to read usage, the runner takes a bare evidence path and "
    "has no --help flag, so it began a foreground battery and wrote a file "
    "literally named `--help` in the repo root - the pipe closed on the "
    "truncated output, no python process survived (verified by process id), "
    "the stray file was deleted (git status back to empty) and the real "
    "battery was then launched detached with its own evidence path; (c) the "
    "round overran the 25 minute budget because the battery alone takes "
    "948s, and the product face it was meant to be followed by is carried to "
    "R2428 rather than half-built.",
    "R2427 tokens: local=~19k api=0 api_reason=verification window - one "
    "detached full battery with its own evidence log, one matrix regeneration "
    "with a stamp-aligned compare, two follow-up runs, two debt closes and "
    "one debt append through the shipped CLIs, one stale tracked document "
    "removed, and the state/export/backlog/heartbeat closeout; zero cloud "
    "calls and zero external API touches",
]

EXPORT_DO = (
    "R2427 verification window: the carried battery ran FIRST on the "
    "committed R2426 tree and read RUNNER PASS 541/541 suites plus controls "
    "7/7 in 948.0s at criteria total 4222 exactly as pre-registered, the "
    "matrix section caught its designed stale-doc red without writing, the "
    "canonical matrix was regenerated to 52086B and all four sections then "
    "read PASS for VERDICT R2427 PASS; the sixteen-window stale "
    "docs/suite-matrix.md duplicate was removed and the successor product "
    "face registered"
)
EXPORT_ARTIFACT = (
    "qa/reconcile-all-R2427.log (RUNNER PASS 541/541, criteria 4222, "
    "948.0s) + docs/sandbox-suite-matrix.md regenerated 52086B at 541 suites "
    "/ 4222 criteria (byte-identical on --check) + debt register at 105512B "
    "with reconcile-battery-R2427 and stale-suite-matrix-copy closed"
)
EXPORT_MILESTONE = (
    "product face on the tech queue head state/queue/tech.md:491 prefix "
    "AC-PICBC1 (comma_binding_consumer_wire, AC-PICBC1..AC-PICBC6 pinned at "
    "R2426): the comma-aware binding table must reach the identity path so a "
    "comma-list publisher is named WIRE or FOREIGN with its module instead of "
    "UNRESOLVED, while every script without a comma list keeps its identity "
    "row byte for byte"
)
EXPORT_DUE = "2026-11-05T22:00:00+08:00"

BACKLOG_ROWS = [
    "- [x] [done 2026-11-04 R2427] R2427 verification window: the debt gate "
    "named CLAIM-FIRST item=reconcile-battery-R2427 at the pre-registered 541 "
    "suites / 4222 criteria, so the battery ran FIRST on the committed R2426 "
    "tree with zero product edits and read RUNNER PASS 541/541 suites plus "
    "controls 7/7 in 948.0s at criteria total 4222 EXACTLY as pre-registered "
    "(qa/reconcile-all-R2427.log, TMP RECLAIM 932/932). The four follow-up "
    "sections reproduced the designed first red - SECTION matrix FAIL at "
    "on-disk=52001B against regenerated=52086B with no rewrite - after which "
    "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from that "
    "green evidence (52086B, --check byte-identical) and the re-run read all "
    "four PASS for VERDICT R2427 PASS. Debt: reconcile-battery-R2427 closed "
    "at its predicted 104802B -> 104805B and the open stale-suite-matrix-copy "
    "closed at 104805B -> 104809B and discharged for real - docs/"
    "suite-matrix.md, a 34452B 2026-10-27 render with no live consumer, was "
    "removed (git ls-files reads zero), leaving docs/sandbox-suite-matrix.md "
    "the only matrix doc. Successor product-face-R2428 appended first=yes "
    "(104809B -> 105512B) naming tech.md:491 AC-PICBC1 "
    "comma_binding_consumer_wire with its six criteria pre-registered at "
    "R2426. Zero product code shipped this window and none is claimed, "
    "honestly 0 product points.\n",
    "- [ ] [carried 2026-11-04 R2427] R2428 first item: the product face the "
    "debt register names, state/queue/tech.md:491 prefix AC-PICBC1 "
    "(comma_binding_consumer_wire, AC-PICBC1..AC-PICBC6 pinned at R2426 "
    "before any code) - the comma-aware binding table must reach the identity "
    "path while every non-comma script keeps its identity row byte for byte. "
    "Still carried and needing an ELEVATED shell: BigDomain-OSLoop reads "
    "LogonType=InteractiveToken (state/debt.md row loop-s4u-reconcile), which "
    "the 2026-09-29 machine law forbids for every lane task.\n",
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
    state["last_decision_rows"] = 208
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
            if "reconcile-all-R2427" not in str(item)]
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
    line = ("2026-11-04T07:05:00+08:00 tick=2427 R2427 verification window - "
            "battery RUNNER PASS 541/541 suites plus controls 7/7 in 948.0s at "
            "criteria 4222 exactly as pre-registered, matrix regenerated to "
            "52086B and four sections PASS for VERDICT R2427 PASS, battery and "
            "stale-suite-matrix-copy rows closed, successor "
            "product-face-R2428 registered first=yes")
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