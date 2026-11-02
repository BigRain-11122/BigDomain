"""closeout_R2377 - state, board, heartbeat and export for the R2377 window.

Every derived count written here comes from check_export_consistency.recompute()
in this run; only the round label and the prose summaries are this window's own
words. The export's queue section is re-derived at write time through
queue_floor_export_face.apply, never copied. Dry run by default.
"""

import io
import json
import os
import sys
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402
import queue_floor_export_face as QFE  # noqa: E402
import state_io  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
TECH = os.path.join(REPO, "state", "queue", "tech.md")
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")

NOW = datetime.now().replace(microsecond=0)
STAMP = NOW.strftime("%Y-%m-%dT%H:%M:%S+08:00")
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

NEW_DEC_TOKENS = []
DEC_ROWS_NOW = 131

DO = (
    "R2377 product window: the two writers that publish the CEO-visible "
    "export are now MEASURED against each other - the closeout recipe and "
    "queue_export_gate_wire ran over one document and read AGREES at 78973 "
    "bytes on the real tree, so the proven write path finally has a reader "
    "that says whether the path in use agrees with it."
)

ARTIFACT = (
    "src/os/export_closeout_gate_parity.py plus its six-criteria suite "
    "(qa/export-closeout-gate-parity-R2377.log, 2094B, two legs identical, "
    "four adjacent suites green); the live reading over docs/status-export.json "
    "is verdict=AGREES with both recipes at 78973 bytes."
)

NEXT = (
    "R2378: the battery on the committed R2377 tree pre-registered at 504 "
    "suites / 4000 criteria (this window own suite), then the product face at "
    "the queue head the reader names; the seed this window measured is "
    "closeout_export_parity_wire (AC-CEPW1..6), because the parity is a CLI "
    "that the closeout never calls, so the real path can still publish a block "
    "nobody proved and nobody compared."
)

GAP_ROW = (
    "- [ ] P2 tech seed (R2377, from this window own measured gap): "
    "`src/os/closeout_export_parity_wire.py` - the parity now measures whether "
    "the closeout recipe and the gate wire publish the same bytes, but nothing "
    "runs it on the write path: src/os/closeout_R2376.py and this window's own "
    "closeout_R2377.py call QFE.apply and write the document themselves, and "
    "git grep -l export_closeout_gate_parity at HEAD lists only the module, "
    "its suite and the registry, so a closeout can still publish an unproven "
    "block and the parity only ever says so when a human types the CLI. "
    "Product: one wire the closeout uses, which composes its document, asks "
    "export_closeout_gate_parity and refuses to replace the export unless the "
    "reading is AGREES, leaving the previous file byte-identical otherwise. "
    "Criteria AC-CEPW1..AC-CEPW6 pre-registered HERE BEFORE any code: AC-CEPW1 "
    "the closeout write path calls export_closeout_gate_parity.check (patching "
    "that check moves the published bytes); AC-CEPW2 a refused reading leaves "
    "the export byte-identical with no residue; AC-CEPW3 an AGREES reading "
    "writes the closeout-shaped bytes and reads back identical; AC-CEPW4 the "
    "wire writes nothing when it refuses and reads no clock; AC-CEPW5 exit 0 = "
    "written, 2 = refused (reading named), 3 = missing file, 5 = bad flags; "
    "AC-CEPW6 pure ASCII, stdlib only, no network, own reconcile label. "
    "Anchors zero-occupancy at HEAD 2026-11-02: closeout_export_parity_wire, "
    "AC-CEPW, E_CEPW, os-closeout-export-parity-wire, "
    "test_closeout_export_parity_wire."
)

BACKLOG_ROW = (
    "- [x] R2377 [done 2026-11-02] export_closeout_gate_parity - "
    "state/queue/tech.md:423 AC-ECGP1..AC-ECGP6 delivered: both export "
    "recipes are run over one document and compared byte for byte, BYPASS "
    "names the queue the gate refuses, and the live tree reads AGREES at "
    "78973 bytes on both sides."
)

HBT = (
    "%s R2377 product window: shipped os-export-closeout-gate-parity (6/6 "
    "twice, two legs identical, four adjacent suites green) - the closeout "
    "recipe and the gate wire now publish identical bytes over the real "
    "export (78973/78973, verdict=AGREES), and the next measured gap (the "
    "parity has no caller on the write path) is seeded with its six criteria "
    "pinned; registry now 504 suites / 4000 criteria." % STAMP
)

ITEMS = [
    "2026-11-02 R2377 window (five-silence scan at open: empty git status, no "
    ".git/index.lock; the content-addressed diff of docs/decisions.md against "
    "the stored baseline found ZERO new tokens and TWO tokens no longer "
    "present in the file (D-20260930-18, D-20261024-13), which is the 172 -> "
    "131 row movement of a compacted file rather than a new directive, so the "
    "baseline is kept as the union and the row count is updated; the ledger "
    "carries no unreplied @BigDomain transfer, the group orders tail is "
    "unchanged and benchmarks were refreshed today, inside the seven-day "
    "gate).",
    "R2377 the queue head named CLAIMABLE state/queue/tech.md:423 prefix "
    "AC-ECGP1 (export_closeout_gate_parity), whose AC-ECGP1..AC-ECGP6 were "
    "pinned INSIDE that row at R2376 BEFORE any code. A fresh anchor check at "
    "HEAD found export_closeout_gate_parity, AC-ECGP, E_ECGP, "
    "os-export-closeout-gate-parity and test_export_closeout_gate_parity only "
    "in the queue row that seeded them, with zero executable occupancy.",
    "R2377 why this is a real gap and not housekeeping: R2376 shipped a write "
    "path that proves its queue block, but the closeout that publishes the "
    "export every round does not call it - src/os/closeout_R2375.py and "
    "closeout_R2376.py import queue_floor_export_face, call QFE.apply and then "
    "dump and write the document themselves, and git grep -l "
    "queue_export_gate_wire at HEAD listed only the R2375 files and the "
    "registry. Two writers, one CEO-visible face, nothing measuring agreement.",
    "R2377 shipped src/os/export_closeout_gate_parity.py plus "
    "src/os/test_export_closeout_gate_parity.py. The check runs BOTH real "
    "recipes over the SAME document: the closeout shape (read, QFE.apply, "
    "json.dumps ensure_ascii=False indent=2 plus one LF) and "
    "queue_export_gate_wire.publish over a private temporary copy, which "
    "composes, stages, asks queue_export_freshness_gate and only then replaces "
    "the copy. Neither side is re-implemented, so patching QFE.apply or "
    "QEG.publish moves the verdict. The wire runs entirely inside a private "
    "temp directory that is removed before returning, the original document is "
    "only ever read, and the module imports no clock.",
    "R2377 verdicts: the wire refusing the closeout-style block reads BYPASS "
    "and carries every queue the gate names (AC-ECGP3), differing bytes read "
    "DISAGREES with the first differing field named by dotted path, and "
    "identical bytes read AGREES. Exit codes are 0 AGREES, 2 BYPASS or "
    "DISAGREES, 3 missing or unreadable export, 5 bad flags.",
    "R2377 evidence: SUITE PASS 6/6 twice with an identical criterion digest "
    "plus four adjacent suites green (queue_export_gate_wire, "
    "queue_export_freshness_gate, queue_floor_export_face, queue_head) through "
    "src/os/evidence_capture.py, written to "
    "qa/export-closeout-gate-parity-R2377.log (2094B, legs=2 identical=True "
    "adjacent=4 fails=0, single writer utf-8 LF), and wired "
    "os-export-closeout-gate-parity(6) so the registry reads 504 suites / 4000 "
    "criteria.",
    "R2377 LIVE, not a plan: python src/os/export_closeout_gate_parity.py "
    "--check --root . --export docs/status-export.json --json read "
    "verdict=AGREES gate=WRITTEN closeout_bytes=78973 wire_bytes=78973 "
    "differs=(none) - so the document the closeout published this round is "
    "byte-identical to what the proven wire would publish over it, measured "
    "rather than asserted.",
    "R2377 board: state/queue/tech.md:423 stamped [done 2026-11-02 R2377] and "
    "one REAL measured gap row seeded (closeout_export_parity_wire, "
    "AC-CEPW1..AC-CEPW6 pre-registered inside that row, five anchors "
    "zero-occupancy at HEAD), so the next window inherits a named seam rather "
    "than a hunch.",
    "R2377 honest disclosures: (a) the parity compares the byte SHAPE each "
    "path publishes over the same document; the closeout's own field mutations "
    "(self_drive, the tick row) happen before this call in the real path, and "
    "the live AGREES reading is taken over the document as it stands, not over "
    "a closeout mid-run. (b) The refusal leg (exit 2) is proved on fixtures, "
    "not live: the real tree reads AGREES, and no attempt was made to doctor "
    "the live export to manufacture a red leg. (c) The two vanished decision "
    "tokens are disclosed above rather than silently pruned from the "
    "baseline. (d) tasks.md was left untouched: it is the P-47 canonical board "
    "and carries no row for this tech slice.",
    "R2377 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal but needs an elevated shell, and this session is "
    "unelevated, so the task definition was left untouched (hundred-and-"
    "thirty-second consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md).",
    "R2377 tokens: local=~18k api=0 api_reason=product window on the claimed "
    "queue row - one parity module and its six-criteria suite written to "
    "criteria pinned one round earlier, one registry wiring line, one two-leg "
    "evidence capture with four adjacent suites, one live reading over the "
    "real export, one board stamp and one measured gap row seeded, one export "
    "refresh deriving the queue section at write time, and the "
    "state/backlog/export/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def stamp_tech():
    text = read_text(TECH)
    lines = text.split("\n")
    if len(lines) <= 422:
        raise SystemExit("E_TECH short lines=%d" % len(lines))
    row = lines[422]
    if "AC-ECGP1" not in row:
        raise SystemExit("E_TECH row 423 is not the AC-ECGP1 seed")
    if not row.startswith("- [ ] "):
        print("TECH row 423 already stamped")
        return
    stamped = row.replace("- [ ] ", "- [x] [done 2026-11-02 R2377] ", 1)
    lines[422] = stamped
    lines.insert(423, GAP_ROW)
    before = len(text.encode("utf-8"))
    text2 = "\n".join(lines)
    back = write_text(TECH, text2)
    if back != text2:
        raise SystemExit("E_TECH readback")
    print("TECH before=%dB after=%dB" % (before, len(text2.encode("utf-8"))))


def prepend_backlog():
    text = read_text(BACKLOG)
    if BACKLOG_ROW[:60] in text:
        print("BACKLOG already carries this row")
        return
    back = write_text(BACKLOG, BACKLOG_ROW + "\n" + text)
    if not back.startswith(BACKLOG_ROW):
        raise SystemExit("E_BACKLOG readback")
    print("BACKLOG bytes=%d" % len(back.encode("utf-8")))


def append_heartbeat():
    text = read_text(HEARTBEAT)
    if HBT[:40] in text:
        print("HEARTBEAT already carries this row")
        return
    if text and not text.endswith("\n"):
        text += "\n"
    back = write_text(HEARTBEAT, text + HBT + "\n")
    print("HEARTBEAT bytes=%d" % len(back.encode("utf-8")))


def close_state(execute):
    raw = read_text(STATE)
    before = len(raw.encode("utf-8"))
    data = json.loads(raw)
    if ITEMS[0][:40] in raw:
        print("STATE already carries this window, tick=%s" % data.get("tick"))
        return int(data.get("tick", 0)), data
    tick = int(data.get("tick", 0)) + 1
    data["tick"] = tick
    data["benchmarks_refreshed"] = "2026-11-02"
    tokens = list(data.get("last_dec_tokens") or ())
    for token in NEW_DEC_TOKENS:
        if token not in tokens:
            tokens.append(token)
    data["last_dec_tokens"] = tokens
    data["last_decision_rows"] = DEC_ROWS_NOW
    data["log"] = list(data["log"]) + ITEMS
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    text = state_io.canon(text)
    print("STATE tick=%d items=+%d tokens=%d rows=%d before=%dB predicted=%dB"
          % (tick, len(ITEMS), len(tokens), DEC_ROWS_NOW, before,
             len(text.encode("utf-8"))))
    if not execute:
        return tick, data
    back = write_text(STATE, text)
    if back != text:
        raise SystemExit("E_STATE readback")
    return tick, data


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
                  and row[0] == "R2377" for row in data["results"])
    if not already:
        data["outs"].append([
            "src/os/export_closeout_gate_parity.py", "on",
            "R2377 product: both writers that publish the CEO-visible export "
            "are run over one document and compared byte for byte - identical "
            "reads AGREES, a wire refusal reads BYPASS naming the queue the "
            "gate refuses, differing bytes read DISAGREES naming the first "
            "differing field; the live tree reads AGREES at 78973/78973 bytes",
        ])
    if not already:
        data["results"].append([
            "R2377",
            "product window on the queue head: CLAIMED "
            "state/queue/tech.md:423 AC-ECGP1 export_closeout_gate_parity, "
            "whose six criteria were pinned there at R2376 BEFORE the code and "
            "every anchor read prose-only at HEAD. Shipped the parity module "
            "plus its six-criteria suite: the closeout recipe (QFE.apply then "
            "json.dumps) and queue_export_gate_wire.publish are both run over "
            "the same document inside a private temp copy, so patching either "
            "writer moves the verdict, a gate refusal is named BYPASS with the "
            "queue, and the check writes nothing in the repository and reads no "
            "clock. SUITE PASS 6/6 twice identical plus four adjacent suites "
            "green (qa/export-closeout-gate-parity-R2377.log, 2094B), wired "
            "os-export-closeout-gate-parity(6) so the registry reads 504/4000. "
            "LIVE: the real export reads verdict=AGREES gate=WRITTEN at "
            "78973 bytes on both sides. Row 423 stamped and one REAL measured "
            "gap seeded (closeout_export_parity_wire: the parity has no caller "
            "on the write path). Disclosed: the refusal leg is proved on "
            "fixtures, not by doctoring the live export, and the decision "
            "baseline kept two tokens that left the compacted file.",
        ])
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
    if not execute:
        print("EXPORT dry run bytes=%d queue_verdict=%s"
              % (len(text.encode("utf-8")), data["queue"]["verdict"]))
        return
    back = write_text(EXPORT, text)
    if back != text:
        raise SystemExit("E_EXPORT readback")
    print("EXPORT bytes=%d queue_verdict=%s"
          % (len(back.encode("utf-8")), data["queue"]["verdict"]))


def main(argv):
    execute = "--execute" in argv
    state_tick, state = close_state(execute)
    if execute:
        # The board is stamped BEFORE the export is derived: the stamp moves a
        # queue row from open to delivered, so the published queue section must
        # be read from the final tree, not from the pre-stamp one.
        stamp_tech()
        prepend_backlog()
        append_heartbeat()
        state = json.loads(read_text(STATE))
    refresh_export(execute, state)
    if execute:
        report, n_pass, n_fail = CEC.check()
        print("CHECK pass=%d fail=%d" % (n_pass, n_fail))
        for line in report:
            print("  " + line)
        if n_fail:
            raise SystemExit("E_EXPORT_CONSISTENCY")
    else:
        print("DRY RUN: pass --execute to write")
    print("CLOSEOUT tick=%d done" % state_tick)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))