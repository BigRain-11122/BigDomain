"""closeout_R2385 - export, backlog and heartbeat for the R2385 window.

The window ran the carried battery (511/511, 4042 criteria) and then claimed
state/queue/tech.md:433 (prefix AC-SASF1, the R2379 seed row), shipping
src/os/single_append_status_face.py plus its six-criteria suite and rerouting
residue_triage_append.py --check through it.

Board and state were landed by direct edits this window (disclosed in the log);
this script does the remaining writes so each goes through ONE utf-8 LF writer
instead of a shell redirection:

  EXPORT     refreshed through closeout_export_parity_wire.publish, so this
             closeout is a CLEAN current publisher by the R2384 reading
  BACKLOG    one row prepended for this window
  HEARTBEAT  one row appended

Source is ASCII, stdlib only, zero network.
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

EXPORT = os.path.join(REPO, "docs", "status-export.json")
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")
STATE = os.path.join(REPO, "src", "os", "state.json")

STAMP = "2026-11-02T18:49:50+08:00"
DUE = "2026-11-04T12:00:00+08:00"

DO = ("R2385 verification-then-product window: the battery owed since R2384 ran "
      "first on the committed tree and came back RUNNER PASS 511/511 suites "
      "with controls 7/7 and criteria total 4042 exactly as pre-registered, "
      "then the single-entry residue writer finally names the live status of "
      "the round a --append is about - the batch CLI stopped costing a refused "
      "call at R2379, and the single CLI still did.")

ARTIFACT = ("src/os/single_append_status_face.py plus its six-criteria suite "
            "(qa/single-append-status-face-R2385.log, two legs with an "
            "identical criterion digest, three adjacent residue suites green) "
            "and one runner wiring line; the single writer --check now prints "
            "status=<live> where it printed status=- before this window "
            "(qa/single-append-status-face-live-R2385.log).")

NEXT = ("R2386: the battery on the committed R2385 tree, pre-registered at 512 "
        "suites / 4048 criteria, then the successor seam this window measured: "
        "the status face is asked AFTER the triage read, so exactly when that "
        "read refuses (E_RTA_UNREADABLE on a round below declared_by) the "
        "operator still gets no status at all.")

BACKLOG_ROW = (
    "- [x] R2385 [done 2026-11-02] single_append_status_face - "
    "state/queue/tech.md:433 AC-SASF1..AC-SASF6 delivered: the single-entry "
    "residue writer's --check now names the asked round WITH the live status "
    "the batch face reports, so one call composes a single --append; a round "
    "the live residue does not carry reads NOT-RESIDUE with E_SASF_NOT_RESIDUE, "
    "and every append refusal code and printed line is untouched because the "
    "--append path never asks the face. The window also discharged the carried "
    "battery: RUNNER PASS 511/511 suites, criteria 4042 exactly as "
    "pre-registered.\n")

HEARTBEAT_ROW = (
    "%s R2385 verification-then-product: battery 511/511 suites 4042 criteria "
    "green; single_append_status_face shipped, live --check names "
    "status=NOT-RESIDUE / DELIVERED\n" % STAMP)


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


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
                  and row[0] == "R2385" for row in data["results"])
    if not already:
        data["outs"].append([
            "src/os/single_append_status_face.py", "on",
            "R2385 product: the single-entry residue writer --check now names "
            "the asked round with the live status the batch face reports, and "
            "a round outside the live residue reads NOT-RESIDUE with its own "
            "code instead of an invented status",
        ])
        data["results"].append([
            "R2385",
            "verification-then-product window: the carried battery owed since "
            "R2384 ran FIRST on the committed tree - RUNNER PASS 511/511 suites "
            "plus controls 7/7 in 1237.8s with criteria total 4042 exactly as "
            "pre-registered and TMP RECLAIM 932/932, four follow-up sections "
            "PASS after the designed matrix FAIL and its regeneration to "
            "48989B, evidence and matrix committed alone as 94b01774. CLAIMED "
            "state/queue/tech.md:433 AC-SASF1 single_append_status_face, "
            "criteria pinned there at R2379, anchors prose-only at HEAD. SUITE "
            "PASS 6/6 twice identical plus three adjacent residue suites green "
            "(1233B), wired os-single-append-status-face(6) so the registry "
            "reads 512/4048. LIVE: the face reads R1755 DELIVERED FOUND at rc "
            "0 and R2384 NOT-RESIDUE at rc 2, the single writer prints "
            "status=NOT-RESIDUE where it printed status=-, and the pre-existing "
            "E_RTA_UNREADABLE past-round refusal is byte-identical. Rows stamped "
            "and one REAL measured gap seeded (append_check_status_precedence: "
            "the face is asked after the triage read, so a refused round still "
            "gets no status). Two battery rows closed against the one run and "
            "the successor opened at 512/4048.",
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


def prepend_backlog(execute):
    text = read_text(BACKLOG)
    if "R2385 [done 2026-11-02] single_append_status_face" in text:
        print("BACKLOG already carries the row")
        return
    new = BACKLOG_ROW + text
    if not execute:
        print("BACKLOG dry run bytes=%d->%d"
              % (len(text.encode("utf-8")), len(new.encode("utf-8"))))
        return
    write_text(BACKLOG, new)
    print("BACKLOG bytes=%d" % len(new.encode("utf-8")))


def append_heartbeat(execute):
    text = read_text(HEARTBEAT)
    if "R2385 verification-then-product" in text:
        print("HEARTBEAT already carries the row")
        return
    if not text.endswith("\n"):
        text += "\n"
    new = text + HEARTBEAT_ROW
    if not execute:
        print("HEARTBEAT dry run bytes=%d->%d"
              % (len(text.encode("utf-8")), len(new.encode("utf-8"))))
        return
    write_text(HEARTBEAT, new)
    print("HEARTBEAT bytes=%d" % len(new.encode("utf-8")))


def main(argv):
    execute = "--execute" in argv
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    refresh_export(execute, state)
    prepend_backlog(execute)
    append_heartbeat(execute)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))