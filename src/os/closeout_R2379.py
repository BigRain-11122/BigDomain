"""closeout_R2379 - state, board, heartbeat and export for the R2379 window.

Every derived count written here comes from check_export_consistency.recompute()
in this run; only the round label and the prose summaries are this window's own
words. The export's queue section is re-derived at write time and the published
bytes are proved by closeout_export_parity_wire before they replace the export.
The tech row and the successor seed were already landed by queue_R2379.py, so
this script does not touch them.
Dry run by default.
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
import closeout_export_parity_wire as CEPW  # noqa: E402
import queue_floor_export_face as QFE  # noqa: E402
import state_io  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")

NOW = datetime.now().replace(microsecond=0)
STAMP = NOW.strftime("%Y-%m-%dT%H:%M:%S+08:00")
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

NEW_DEC_TOKENS = []
DEC_ROWS_NOW = 131

DO = (
    "R2379 verification-then-product window: the residue batch face now names "
    "the LIVE STATUS of every residue round. The battery ran first on the "
    "committed tree (505/505 suites, criteria total 4006 exactly as "
    "pre-registered), then the queue head was claimed and "
    "residue_batch_status_face shipped - the batch CLI --check now asks it, so "
    "a --pair list is composed from one call instead of a second tool plus a "
    "guess."
)

ARTIFACT = (
    "src/os/residue_batch_status_face.py plus its six-criteria suite "
    "(qa/residue-batch-status-face-R2379.log, 1245B, two legs identical, four "
    "adjacent suites green); the live run over the real tree names 225 residue "
    "rounds with DELIVERED=205 STAMP-ONLY-OPEN=20 NO-HIT=0 and the batch "
    "--check carries those statuses, where before this window it printed no "
    "status at all."
)

NEXT = (
    "R2380: the battery on the committed R2379 tree pre-registered at 506 "
    "suites / 4012 criteria (this window own suite), then the product face at "
    "the queue head the reader names (line 426 prefix AC-FGES1). The seed this "
    "window measured is single_append_status_face (AC-SASF1..6): the batch "
    "writer now names live statuses, but the single-entry writer --check still "
    "prints none, so a one-round append costs the same refused call."
)

BACKLOG_ROW = (
    "- [x] R2379 [done 2026-11-02] residue_batch_status_face - "
    "state/queue/tech.md:425 AC-RSBF1..AC-RSBF6 delivered: the live status of "
    "every residue round is now one reading (stamp_residue's own, reached "
    "through residue_triage), the batch CLI --check asks it and names each "
    "round with its status, and a round outside the residue reads NOT-RESIDUE "
    "with its own code; the live tree reads 225 rounds DELIVERED=205 "
    "STAMP-ONLY-OPEN=20 NO-HIT=0."
)

HBT = (
    "%s R2379 verification-then-product: battery 505/505 suites green plus "
    "controls 7/7 in 1334.7s with criteria total 4006 exactly as "
    "pre-registered and four follow-up sections PASS after the designed matrix "
    "FAIL; then shipped os-residue-batch-status-face (6/6, two legs identical, "
    "four adjacent suites green) so the batch CLI finally names the live "
    "status of every residue round (live 225 rounds DELIVERED=205 "
    "STAMP-ONLY-OPEN=20), and the next measured gap (the single-entry writer "
    "still names none) is seeded with its six criteria pinned." % STAMP
)

ITEMS = [
    "2026-11-02 R2379 verification-then-product window (five-silence scan "
    "clean at open: empty git status, no .git/index.lock; scan_five_still read "
    "LEDGER atbd_lines=0 unreplied_groups=0, DEC rows=131 tokens=86 new=0, the "
    "group orders tail still the 2026-11-02 11:04 model-policy baseline "
    "already acknowledged as non-execution, and benchmarks refreshed "
    "2026-11-02 inside the seven-day gate). The debt gate named CLAIM-FIRST "
    "item=reconcile-battery-R2378, so the battery ran FIRST on the committed "
    "tree: RUNNER PASS 505/505 suites green plus reconcile controls 7/7 in "
    "1334.7s with birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 "
    "failed=0 (qa/reconcile-all-R2379.log, 812967B, single writer utf-8 LF "
    "through src/os/battery_stream.py, never a shell redirection) and criteria "
    "total 4006 EXACTLY as pre-registered, so the prediction matched the "
    "measurement with no correction and nothing to name.",
    "R2379 follow-up sections and matrix: the four sections ran through "
    "src/os/battery_followup.py and the matrix section FAILED first on the "
    "stale doc (on-disk=48299B regenerated=48405B) and did NOT rewrite it, "
    "which is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 505 suites / 4006 criteria (48405B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN 5 "
    "domains, profile --check byte-identical, census DRIFT-CLEAN) for VERDICT "
    "R2379 PASS. The evidence and the matrix were committed ALONE as a79df5b9 "
    "before any product byte changed (the R2168 mixed-tree rule).",
    "R2379 product face, the row the reader named: CLAIMED "
    "state/queue/tech.md:425 prefix AC-RSBF1 (residue_batch_status_face), "
    "whose AC-RSBF1..AC-RSBF6 were pinned INSIDE that row at R2369 BEFORE any "
    "code, after a fresh anchor check at HEAD: the five anchors hit only prose "
    "and state files (docs/status-export.json, heartbeat.txt, "
    "src/os/backlog.md, the R2369 one-off scripts, src/os/state.json, "
    "state/debt.md, state/queue/tech.md) with zero executable occupancy.",
    "R2379 the face: shipped src/os/residue_batch_status_face.py plus "
    "src/os/test_residue_batch_status_face.py. The status map IS "
    "residue_triage.live_residue - which is stamp_residue's own read validated "
    "against stamp_residue's own vocabulary - so patching either reader moves "
    "the printed statuses and no second residue scan, queue parse or stamp "
    "regex exists here; the reported vocabulary is stamp_residue.STATUSES read "
    "at call time, so a status this module has never heard of travels rather "
    "than being dropped; --check names every residue round with its live "
    "status; a round the reading does not carry reads NOT-RESIDUE with "
    "E_RSBF_NOT_RESIDUE at exit 2 rather than an invented status; exits are "
    "0/2/3/5 with a byte-stable --json over the pinned key order; and the file "
    "is pure ASCII stdlib with no clock and no network.",
    "R2379 the caller: residue_triage_append_batch.check now asks the face "
    "through a CALL-TIME import, so the batch module still loads without it "
    "and the --append path never reaches it - proved by patching the face to "
    "raise and watching plan still compose a delta while check refuses "
    "E_RTAB_BAD_STATE. Its --check line and report now carry rounds=R9002,... "
    "statuses=DELIVERED,... where the shipped module carried empty lists.",
    "R2379 evidence and board: SUITE PASS 6/6 twice with an identical "
    "criterion digest plus four adjacent suites green "
    "(qa/residue-batch-status-face-R2379.log, 1245B, legs=2 identical=True "
    "adjacent=4 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired os-residue-batch-status-face(6) so the "
    "registry reads 506 suites / 4012 criteria. LIVE, not a plan: on the real "
    "tree qa/residue-batch-status-face-live-R2379.log (1198B, crlf=0, "
    "readback True) reads the map over 225 rounds with DELIVERED=205 "
    "STAMP-ONLY-OPEN=20 NO-HIT=0, a byte-stable --json across two runs, the "
    "known round R1755 FOUND with requested_status=DELIVERED, R9999 read "
    "NOT-RESIDUE at rc=2 with E_RSBF_NOT_RESIDUE, and the batch --check "
    "carrying the statuses (carries_statuses=True). Tech row 425 stamped "
    "[done 2026-11-02 R2379] (bracket payload 20 chars inside the 60-char "
    "stamp law; queue_R2379.py predicted=measured 1482728B) and one REAL "
    "measured gap row seeded (single_append_status_face, AC-SASF1..AC-SASF6 "
    "pre-registered in that row, five anchors zero-occupancy): the batch "
    "writer names live statuses and the SINGLE-entry writer still names none, "
    "so a one-round append costs the same refused call. Gauge after the stamp "
    "and the seed reads FLOOR-MET main 5/5 tech 10/10 explore 10/10 and the "
    "reader now offers line 426 prefix AC-FGES1. Register: "
    "reconcile-battery-R2378 closed through debt_close (open 3->2, done "
    "106->107, 82094B->82097B, readback ok) and reconcile-battery-R2379 "
    "opened first=yes through debt_append at the measured successor target 506 "
    "suites / 4012 criteria (82097B->82379B, readback ok).",
    "R2379 honest disclosures: (a) the first suite run was RED on AC-RSBF4 and "
    "the red was this window own fixture: the world carried no pinned "
    "declaration, so the shipped writer refused E_RTAB_UNPINNED before the "
    "criterion could measure anything - the fixture now writes the "
    "declaration. (b) The second red was also this window own assertion: it "
    "expected statuses=- on the batch dry run, while the shipped module "
    "already fills rounds/statuses from the PAIRS on that path, so the "
    "assertion was corrected to the measured pair-driven shape and no "
    "criterion was widened. (c) NO-HIT is proved on fixtures only: the live "
    "tree carries no NO-HIT round today, and the live log says so rather than "
    "implying a live catch. (d) The face reports a status map, not a decision: "
    "the batch writer still refuses a disagreeing --pair, which is the shipped "
    "law and is untouched. (e) tasks.md was left untouched: it is the P-47 "
    "canonical board and carries no row for this tech slice. (f) This window "
    "ran past its 25-minute budget: the battery alone measured 1334.7s, and "
    "the product face was still shipped rather than deferred, because the tree "
    "was committed and clean before any product byte changed.",
    "R2379 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal but needs an elevated shell, and this session is unelevated, "
    "so the task definition was left untouched (hundred-and-thirty-fourth "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md).",
    "R2379 tokens: local=~30k api=0 api_reason=verification-then-product "
    "window - one full battery (505 suites, 1334.7s) plus its four follow-up "
    "sections and one matrix regeneration, one status face and its "
    "six-criteria suite written to criteria pinned ten rounds earlier, one "
    "caller rerouted through it at call time, one registry wiring line, one "
    "two-leg evidence capture with four adjacent suites, one live capture "
    "through a single utf-8 LF writer, one board stamp and one measured gap "
    "row seeded, one register close and one successor row opened, and the "
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
                  and row[0] == "R2379" for row in data["results"])
    if not already:
        data["outs"].append([
            "src/os/residue_batch_status_face.py", "on",
            "R2379 product: the live status of every residue round is one "
            "reading (stamp_residue's own, reached through residue_triage), the "
            "batch CLI --check asks it and names each round with its status, "
            "and a round outside the residue reads NOT-RESIDUE - the live tree "
            "reads 225 rounds DELIVERED=205 STAMP-ONLY-OPEN=20 NO-HIT=0",
        ])
    if not already:
        data["results"].append([
            "R2379",
            "verification-then-product: the battery ran first on the committed "
            "tree and read PASS 505/505 suites plus controls 7/7 in 1334.7s "
            "with criteria total 4006 exactly as pre-registered, four "
            "follow-up sections PASS after the designed matrix FAIL, evidence "
            "and matrix committed alone as a79df5b9. Then CLAIMED "
            "state/queue/tech.md:425 AC-RSBF1 residue_batch_status_face, "
            "criteria pinned there at R2369, anchors prose-only at HEAD. "
            "Shipped the face: the status map is residue_triage.live_residue "
            "over stamp_residue's own read, the vocabulary is read at call "
            "time, --check names every round with its status, a round outside "
            "the residue reads NOT-RESIDUE at exit 2, exits 0/2/3/5 with a "
            "byte-stable pinned --json, and the batch CLI --check now asks it "
            "at call time while --append never touches it. SUITE PASS 6/6 "
            "twice identical plus four adjacent suites green (1245B), wired "
            "os-residue-batch-status-face(6) so the registry reads 506/4012. "
            "LIVE: 225 rounds DELIVERED=205 STAMP-ONLY-OPEN=20 NO-HIT=0, json "
            "byte-stable, R1755 FOUND, R9999 NOT-RESIDUE, batch carries the "
            "statuses. Row stamped and one REAL measured gap seeded "
            "(single_append_status_face: the single-entry writer still names "
            "no status).",
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
    state_tick, state = close_state(execute)
    if execute:
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


if __name__ == "__main__":
    main(sys.argv[1:])