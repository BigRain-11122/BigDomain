"""closeout_R2386 - state, board, debt, backlog, heartbeat and export.

The window discharged the carried battery (512/512 suites, 4048 criteria,
exactly as pre-registered) and then claimed state/queue/tech.md:434 (prefix
AC-BEPR1, the R2380 seed row), shipping src/os/bare_evidence_pile_refusal.py
plus its six-criteria suite and rerouting the follow-up matrix section through
it at call time for a bare evidence name.

Every write goes through ONE utf-8 LF writer instead of a shell redirection:
state.json through state_io.canon, the board/debt files line-space preserved,
the export through closeout_export_parity_wire.publish so this closeout is a
CLEAN current publisher by the R2384 reading. Source is ASCII, stdlib only.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402
import closeout_export_parity_wire as CEPW  # noqa: E402
import queue_floor_export_face as QFE  # noqa: E402
import state_io  # noqa: E402

EXPORT = os.path.join(REPO, "docs", "status-export.json")
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")
STATE = os.path.join(REPO, "src", "os", "state.json")
TECH = os.path.join(REPO, "state", "queue", "tech.md")
DEBT = os.path.join(REPO, "state", "debt.md")

STAMP = "2026-11-02T20:05:00+08:00"
DUE = "2026-11-04T12:00:00+08:00"
DEC_ROWS_NOW = 137
LAST_ORDER_NOW = "2026-11-02 11:04"

DO = ("R2386 verification-then-product window: the battery owed since R2385 ran "
      "first on the committed tree (RUNNER PASS 512/512 suites, controls 7/7, "
      "criteria total 4048 exactly as pre-registered), then a bare evidence "
      "filename stopped reading as 'qa' by default - the pile is measured where "
      "the file actually lives under the root, and a name that lives nowhere or "
      "in two piles now refuses instead of speaking about a pile it cannot prove.")

ARTIFACT = ("src/os/bare_evidence_pile_refusal.py plus its six-criteria suite "
            "(qa/bare-evidence-pile-refusal-R2386.log, two legs with an identical "
            "criterion digest, three adjacent suites green) and one runner wiring "
            "line; the follow-up matrix section now asks it for a bare evidence "
            "name, so the guarded pile and the matrix describe the same file "
            "(qa/bare-evidence-pile-refusal-live-R2386.log: dir=qa over 474 "
            "rounds, missing name refuses E_BEPR_NOT_FOUND at rc 2).")

NEXT = ("R2387: the battery on the committed R2386 tree, pre-registered at 513 "
        "suites / 4054 criteria, then the successor seam this window measured: "
        "the matrix section now guards the MEASURED pile but still hands the "
        "ORIGINAL evidence string to the matrix tool, so a bare name can be "
        "guarded in one pile and rendered from another when cwd is not root.")

MAIN_LINE = (
    "R2386 verification-then-product window: the carried battery owed since "
    "R2385 ran FIRST on the committed tree 84619739 with an empty git status - "
    "RUNNER PASS 512/512 suites plus controls 7/7 in 1686.5s with criteria "
    "total 4048 EXACTLY as pre-registered and TMP RECLAIM 932/932 worlds 326.59 "
    "MiB busy=0 failed=0 (qa/reconcile-all-R2386.log, 819029B, single writer "
    "utf-8 LF through src/os/battery_stream.py); the four follow-up sections ran "
    "through src/os/battery_followup.py, the matrix section FAILED first on the "
    "stale doc (on-disk=48989B regenerated=49095B) and did not rewrite it, "
    "suite_matrix regenerated docs/sandbox-suite-matrix.md to 512 suites / 4048 "
    "criteria and the re-run read all four PASS for VERDICT R2386 PASS; evidence "
    "and matrix committed alone as dec152c3 before any product byte changed (the "
    "R2168 mixed-tree rule). FIRST-ROUND STEP DISCLOSED: an earlier invocation "
    "was cancelled by the shell tool's five-minute no-output rule while the "
    "runner was buffering, which left a stray file named '--help' (removed) and "
    "one partial evidence file (deleted); the battery was then run detached and "
    "its evidence file was written from scratch, so no leg is a mixture of two "
    "runs. PRODUCT: claimed state/queue/tech.md:434 prefix AC-BEPR1 "
    "(bare_evidence_pile_refusal), criteria pinned in that row at R2380 BEFORE "
    "any code, anchors prose-only at HEAD. SHIPPED src/os/"
    "bare_evidence_pile_refusal.py plus src/os/test_bare_evidence_pile_refusal.py: "
    "a bare evidence NAME is resolved by STAT-ing it under the root (the root "
    "itself answers '.', then one-level subdirectories), two containing piles "
    "refuse as E_BEPR_AMBIGUOUS and a name that lives nowhere refuses as "
    "E_BEPR_NOT_FOUND, so no default pile is left anywhere in the derivation; a "
    "name WITH a directory part is handed to followup_guard_evidence_scope at "
    "call time, so that R2380 reading is byte-identical; the CLI asks the same "
    "question and reads the measured pile through followup_section_foreign_wire, "
    "so a bare name living in a FOREIGN-SECTION pile refuses NAMING that pile "
    "while the wire keeps exit codes 0/2/3/5 and its pinned GUARD_KEYS. The "
    "follow-up matrix section asks BEPR.is_bare at call time and derives the pile "
    "through BEPR.pile_for, refusing before any matrix byte when the name cannot "
    "be placed; the wire stays os-free because the bare test lives in the new "
    "module. SUITE PASS 6/6 twice with an identical criterion digest plus three "
    "adjacent suites green (qa/bare-evidence-pile-refusal-R2386.log, 2064B, "
    "legs=2 identical=True adjacent=3 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired os-bare-evidence-pile-refusal(6) so the "
    "registry reads 513 suites / 4054 criteria. LIVE: "
    "qa/bare-evidence-pile-refusal-live-R2386.log (662B, crlf=0, cr=0) reads "
    "dir=qa verdict=VOCABULARY-CLEAN rounds=474 rc=0 with a byte-stable --json "
    "over the seven pinned keys and a name that lives nowhere refusing "
    "E_BEPR_NOT_FOUND at rc 2 on the real tree. Row 434 stamped and one REAL "
    "measured gap seeded (matrix_evidence_pile_consistency, AC-MEPC1..AC-MEPC6 "
    "pre-registered in that row, five anchors zero-occupancy): the guard now "
    "follows the measured pile but the matrix tool is still handed the original "
    "string. Register: battery-R2385 closed, battery-R2386 opened first=yes at "
    "513 suites / 4054 criteria. Group order 2026-11-02 11:04 (bm-a memory/cleanup "
    "sweep, executed by bm-a) read and logged as NOTED, not this company's "
    "execution surface.")

DISC_LINE = (
    "R2386 honest disclosures: (a) three suite criteria were RED on their first "
    "run and all three reds were this window own fixtures, never the module: "
    "AC-BEPR1 and AC-BEPR3 built a world where the SAME bare name lived in two "
    "piles, so the correct answer was E_BEPR_AMBIGUOUS and not the pile the test "
    "expected, and AC-BEPR5 expected exit 3 from a pile holding two different "
    "round labels, which is a legitimate pile (the duplicate law keys on the R "
    "number, not the label) - it now points at a pile carrying no recognised "
    "evidence, which is the honest unreadable leg. (b) AC-BEPR1's first assertion "
    "looked for the foreign code in the text face, where the wire prints a code "
    "only for an UNREADABLE pile; the assertion now checks the verdict and the "
    "pile name the face prints, and the wire's own E_FSFW_FOREIGN_SECTION is "
    "proved through matrix_section over the same world. (c) The first wire edit "
    "imported os to test for a directory part, which the R2370 wire suite forbids "
    "by design; the test now lives in the new module as is_bare, so the wire's "
    "purity criterion stays green and its FGES derivation line is untouched. (d) "
    "The live capture's first write carried eight CRLF lines because child "
    "stdout crosses a console text-mode boundary; the file was regenerated with "
    "one transport normalisation and now reads crlf=0. (e) The AMBIGUOUS and "
    "FOREIGN refusal paths are proved on fixtures; no live refusal was "
    "manufactured on the real tree. (f) tasks.md was left untouched: it is the "
    "P-47 canonical board and carries no row for this tech slice. (g) This "
    "window ran far past its 25-minute budget: the battery alone measured "
    "1686.5s and one invocation had to be restarted after the shell tool "
    "cancelled it for silence.")

SELF_HEAL_LINE = (
    "R2386 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal but needs an elevated shell, and this session is unelevated, "
    "so the task definition was left untouched (hundred-and-forty-first "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md).")

TOKENS_LINE = (
    "R2386 tokens: local=~38k api=0 api_reason=verification-then-product window "
    "- one full battery (512 suites, 1686.5s, restarted once after a tool "
    "cancellation) plus its four follow-up sections and one matrix regeneration, "
    "one measured-pile module and its six-criteria suite written to criteria "
    "pinned six rounds earlier, the follow-up matrix section rerouted through it "
    "at call time with the R2380 derivation untouched, one registry wiring line, "
    "one two-leg evidence capture with three adjacent suites, one LF-normalised "
    "live capture on the real tree, one board stamp, one measured gap row seeded, "
    "one battery row closed and one successor row opened, and the "
    "state/debt/backlog/export/heartbeat closeout; zero cloud calls and zero "
    "external API touches")

ITEMS = [MAIN_LINE, DISC_LINE, SELF_HEAL_LINE, TOKENS_LINE]

DISCHARGED_NOTE = (
    "  DISCHARGED R2386 (line 434, AC-BEPR1..AC-BEPR6): src/os/"
    "bare_evidence_pile_refusal.py plus src/os/test_bare_evidence_pile_refusal.py "
    "shipped with the criteria pinned in this row at R2380 BEFORE the code. A "
    "bare evidence name is measured under the root by STAT (the root answers '.', "
    "then one-level subdirectories), two containing piles refuse as "
    "E_BEPR_AMBIGUOUS, a name that lives nowhere refuses as E_BEPR_NOT_FOUND, and "
    "a name that carries a directory is handed to followup_guard_evidence_scope "
    "at call time so that reading is byte-identical; the follow-up matrix section "
    "asks BEPR.is_bare and BEPR.pile_for at call time and refuses before any "
    "matrix byte when the name cannot be placed, while the wire stays os-free. "
    "SUITE PASS 6/6 twice identical plus three adjacent suites green "
    "(qa/bare-evidence-pile-refusal-R2386.log, 2064B, legs=2 identical=True "
    "adjacent=3 fails=0), wired os-bare-evidence-pile-refusal(6) so the registry "
    "reads 513 suites / 4054 criteria. LIVE: "
    "qa/bare-evidence-pile-refusal-live-R2386.log reads dir=qa "
    "verdict=VOCABULARY-CLEAN rounds=474 rc=0 with a byte-stable --json over the "
    "seven pinned keys and a name that lives nowhere refusing E_BEPR_NOT_FOUND at "
    "rc 2. One REAL measured gap seeded below: the matrix tool is still handed "
    "the ORIGINAL evidence string, so a bare name can be guarded in one pile and "
    "rendered from another when cwd is not root.")

SEED_ROW = (
    "- [ ] P2 tech seed (R2386, from this window own measured seam): "
    "`src/os/matrix_evidence_pile_consistency.py` - the matrix section now guards "
    "the pile a bare evidence name MEASUREDLY lives in, but it still passes the "
    "ORIGINAL string to the matrix tool (battery_followup.matrix_core -> "
    "suite_matrix.py --evidence <string>), so the guard can speak about one pile "
    "while the rendered doc comes from another whenever the tool's cwd is not the "
    "root. Product: the string handed to the matrix tool is derived from the "
    "measured pile (and root), so guard and tool provably read ONE file, and a "
    "caller naming a bare filename gets either both or a refusal. Criteria "
    "AC-MEPC1..AC-MEPC6 pre-registered HERE BEFORE any code: AC-MEPC1 a bare "
    "evidence name is handed to the tool as the measured pile plus the basename, "
    "and a patched derivation moves the argument the tool receives; AC-MEPC2 a "
    "name that carries a directory is handed through unchanged, byte for byte; "
    "AC-MEPC3 the tool argument of the matrix section and the pile the guard "
    "reads resolve to the SAME file under a root that is not the cwd, proved by "
    "the paths the faked call and the reader each receive; AC-MEPC4 a name that "
    "cannot be placed refuses before the tool is called at all, so no doc is "
    "rendered from a pile the guard cannot name; AC-MEPC5 the section report for "
    "an unchanged pile stays byte-identical to the R2386 reading, and the CLI "
    "exit codes 0/2/3/5 are unchanged; AC-MEPC6 pure ASCII, stdlib only, zero "
    "network and no clock, plus its own reconcile label. Five anchors "
    "zero-occupancy at HEAD 2026-11-02: matrix_evidence_pile_consistency, "
    "AC-MEPC, E_MEPC, os-matrix-evidence-pile-consistency, "
    "test_matrix_evidence_pile_consistency.")

BACKLOG_ROW = (
    "- [x] R2386 [done 2026-11-02] bare_evidence_pile_refusal - "
    "state/queue/tech.md:434 AC-BEPR1..AC-BEPR6 delivered: a bare evidence "
    "filename is no longer read as 'qa' by default - the pile is measured where "
    "the file actually lives under the root (the root itself, then one-level "
    "subdirectories), a name living in two piles refuses as E_BEPR_AMBIGUOUS and "
    "a name living nowhere refuses as E_BEPR_NOT_FOUND, while a name that carries "
    "a directory keeps the R2380 reading byte for byte; the follow-up matrix "
    "section now asks the new module for a bare name and refuses before any "
    "matrix byte when the name cannot be placed. The window also discharged the "
    "carried battery: RUNNER PASS 512/512 suites, criteria 4048 exactly as "
    "pre-registered.\n")

HEARTBEAT_ROW = (
    "%s R2386 verification-then-product: battery 512/512 suites 4048 criteria "
    "green; bare_evidence_pile_refusal shipped, live bare name derives dir=qa "
    "over 474 rounds and a missing name refuses E_BEPR_NOT_FOUND\n" % STAMP)

DEBT_CLOSE = (
    "- [x] opened=R2385 | item=reconcile-battery-R2385 | closed=R2386 | "
    "note=discharged at R2386 with zero product edits until green (the R2168 "
    "mixed-tree rule): full reconcile battery on the committed R2385 tree "
    "84619739 with an empty git status, RUNNER PASS 512/512 suites plus controls "
    "7/7 in 1686.5s with birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 "
    "failed=0, criteria total 4048 EXACTLY as pre-registered (no delta to "
    "explain), then four follow-up sections through src/os/battery_followup.py "
    "with the designed matrix FAIL and its regeneration to 49095B, VERDICT R2386 "
    "PASS; the first invocation was cancelled by the shell tool's five-minute "
    "no-output rule and restarted detached, so the evidence file was written from "
    "scratch and is not a mixture of two runs.")

DEBT_OPEN = (
    "- [ ] opened=R2386 | item=reconcile-battery-R2386 | note=the battery for the "
    "R2386 tree (513 suites / 4054 criteria expected: 512/4048 plus this window "
    "os-bare-evidence-pile-refusal suite) runs FIRST next window on the committed "
    "tree with zero product edits | first=yes")


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def close_state(execute):
    raw = read_text(STATE)
    before = len(raw.encode("utf-8"))
    data = json.loads(raw)
    if ITEMS[0][:40] in raw:
        print("STATE already carries this window, tick=%s" % data.get("tick"))
        return int(data.get("tick", 0)), data
    tick = int(data.get("tick", 0)) + 1
    data["tick"] = tick
    data["last_order"] = LAST_ORDER_NOW
    data["last_decision_rows"] = DEC_ROWS_NOW
    data["log"] = list(data["log"]) + ITEMS
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    text = state_io.canon(text)
    print("STATE tick=%d items=+%d before=%dB predicted=%dB"
          % (tick, len(ITEMS), before, len(text.encode("utf-8"))))
    if not execute:
        return tick, data
    back = write_text(STATE, text)
    if back != text:
        raise SystemExit("E_STATE readback")
    return tick, data


def stamp_board(execute):
    text = read_text(TECH)
    if "done 2026-11-02 R2386" in text:
        print("TECH already stamped")
        return
    marker = "- [ ] P2 tech seed (R2380,"
    lines = text.split("\n")
    hit = None
    for index, line in enumerate(lines):
        if line.startswith(marker):
            hit = index
            break
    if hit is None:
        raise SystemExit("E_TECH row not found")
    lines[hit] = lines[hit].replace(
        "- [ ] ", "- [x] [done 2026-11-02 R2386] ", 1)
    lines.insert(hit + 1, DISCHARGED_NOTE)
    while lines and lines[-1] == "":
        lines.pop()
    lines.append("")
    lines.append(SEED_ROW)
    lines.append("")
    new = "\n".join(lines)
    print("TECH bytes=%d->%d seed_row_appended=True"
          % (len(text.encode("utf-8")), len(new.encode("utf-8"))))
    if not execute:
        return
    write_text(TECH, new)


def close_debt(execute):
    text = read_text(DEBT)
    if "closed=R2386" in text:
        print("DEBT already closed at R2386")
        return
    old = ("- [ ] opened=R2385 | item=reconcile-battery-R2385 | note=the battery "
           "for the R2385 tree")
    lines = text.split("\n")
    hit = None
    for index, line in enumerate(lines):
        if line.startswith(old):
            hit = index
            break
    if hit is None:
        raise SystemExit("E_DEBT open row not found")
    lines[hit] = DEBT_CLOSE
    lines.append(DEBT_OPEN)
    new = "\n".join(lines) if text.endswith("\n") else "\n".join(lines) + "\n"
    if not text.endswith("\n"):
        new = "\n".join(lines) + "\n"
    print("DEBT bytes=%d->%d" % (len(text.encode("utf-8")),
                                 len(new.encode("utf-8"))))
    if not execute:
        return
    write_text(DEBT, new)


def prepend_backlog(execute):
    text = read_text(BACKLOG)
    if "R2386 [done 2026-11-02] bare_evidence_pile_refusal" in text:
        print("BACKLOG already carries the row")
        return
    new = BACKLOG_ROW + text
    print("BACKLOG bytes=%d->%d" % (len(text.encode("utf-8")),
                                    len(new.encode("utf-8"))))
    if not execute:
        return
    write_text(BACKLOG, new)


def append_heartbeat(execute):
    text = read_text(HEARTBEAT)
    if "R2386 verification-then-product" in text:
        print("HEARTBEAT already carries the row")
        return
    if not text.endswith("\n"):
        text += "\n"
    new = text + HEARTBEAT_ROW
    print("HEARTBEAT bytes=%d" % len(new.encode("utf-8")))
    if not execute:
        return
    write_text(HEARTBEAT, new)


def refresh_export(execute, state):
    data = json.loads(read_text(EXPORT))
    derived, _state, _export, _pat = CEC.recompute()
    data["export_ts"] = STAMP
    data["do"] = DO
    face = data["ceo_face"]
    face["current"] = DO
    face["latest_artifact"] = ARTIFACT
    face["last_artifact"] = ARTIFACT
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = DUE
    face["updated_at"] = STAMP
    already = any(isinstance(row, list) and len(row) >= 2
                  and row[0] == "R2386" for row in data["results"])
    if not already:
        data["outs"].append([
            "src/os/bare_evidence_pile_refusal.py", "on",
            "R2386 product: a bare evidence filename is no longer read as 'qa' - "
            "the pile is measured where the file actually lives under the root, "
            "a name living in two piles refuses as E_BEPR_AMBIGUOUS and a name "
            "living nowhere refuses as E_BEPR_NOT_FOUND, while a name carrying a "
            "directory keeps the R2380 reading byte for byte",
        ])
        data["results"].append(["R2386", MAIN_LINE])
    data["self_drive"] = {
        "window": derived["window"],
        "window_days": derived["window_days"],
        "log_lines_in_window": derived["log_lines_in_window"],
        "idle_fast_mention_lines": derived["idle_fast_mention_lines"],
        "no_pullable_mention_lines": derived["no_pullable_mention_lines"],
        "substantive_non_idle_mention_lines":
            derived["substantive_non_idle_mention_lines"],
        "proposals_total": derived["proposals_total"],
        "proposals_open": derived["proposals_open"],
        "queue_main_open": derived["queue_main_open"],
        "queue_tech_open": derived["queue_tech_open"],
        "queue_explore_open": derived["queue_explore_open"],
    }
    QFE.apply(data, REPO)
    tick = str(state.get("tick", ""))
    label = CEC._load_patterns()["tick_row_label"]
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2
                 and row[1] == label]
    if len(tick_rows) != 1:
        raise SystemExit("E_TICK_ROW count=%d" % len(tick_rows))
    tick_rows[0][0] = tick
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    print("EXPORT dry bytes=%d queue_verdict=%s"
          % (len(text.encode("utf-8")), data["queue"]["verdict"]))
    if not execute:
        return
    parity, parity_code = CEPW.publish(REPO, EXPORT, text=text)
    if parity_code != 0:
        raise SystemExit("E_EXPORT_PARITY %s" % parity["reading"])
    back = read_text(EXPORT)
    if back != text:
        raise SystemExit("E_EXPORT readback")
    print("EXPORT bytes=%d queue_verdict=%s parity=%s"
          % (len(back.encode("utf-8")), data["queue"]["verdict"],
             parity["reading"]))


def main(argv):
    execute = "--execute" in argv
    tick, state = close_state(execute)
    stamp_board(execute)
    close_debt(execute)
    prepend_backlog(execute)
    append_heartbeat(execute)
    refresh_export(execute, state)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))