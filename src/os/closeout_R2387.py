"""closeout_R2387 - state, board, debt, backlog, heartbeat and export.

The window discharged the carried battery (513/513 suites, 4054 criteria,
exactly as pre-registered) and then claimed state/queue/tech.md:439 (prefix
AC-RWGB1, the R2381 seed row), shipping
src/os/review_window_guard_parity_blind_agreement.py plus its six-criteria
suite, so an agreement reached only because NEITHER face could read the
review-window declaration is no longer reported as a green.

Every write goes through ONE utf-8 LF writer instead of a shell redirection:
state.json through state_io.canon, the export through
closeout_export_parity_wire.publish so this closeout is a CLEAN current
publisher by the R2384 reading. Source is ASCII, stdlib only.
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

STAMP = "2026-11-02T20:25:00+08:00"
DUE = "2026-11-04T12:00:00+08:00"
DEC_ROWS_NOW = 172
LAST_ORDER_NOW = "2026-11-02 11:04"

DO = ("R2387 verification-then-product window: the battery owed since R2386 ran "
      "first on the committed tree (RUNNER PASS 513/513 suites, controls 7/7, "
      "criteria total 4054 exactly as pre-registered), then the review-window "
      "parity stopped reporting a blind agreement as a green - a pair that "
      "agrees only because neither side could read the declaration now reads "
      "PARITY-UNKNOWN naming both codes, while every informed reading keeps the "
      "parity's own words byte for byte.")

ARTIFACT = ("src/os/review_window_guard_parity_blind_agreement.py plus its "
            "six-criteria suite (qa/review-window-guard-parity-blind-agreement-"
            "R2387.log, two legs with an identical criterion digest, three "
            "adjacent review-window suites green) and one runner wiring line; "
            "the live capture reads the real tree PARITY-AGREES ignorance=none "
            "window=100 with a byte-stable --json over the nine pinned keys, and "
            "a fixture declaration neither face can read reads PARITY-UNKNOWN "
            "ignorance=both at rc 1 (qa/review-window-guard-parity-blind-"
            "agreement-live-R2387.log).")

NEXT = ("R2388: the battery on the committed R2387 tree, pre-registered at 514 "
        "suites / 4060 criteria, then the successor seam this window measured: "
        "NO product path ever asks the parity (git grep finds RWGP. only in its "
        "own suite), so neither a split nor a blind agreement refuses anything "
        "an operator walks.")

MAIN_LINE = (
    "R2387 verification-then-product window: the carried battery owed since "
    "R2386 ran FIRST on the committed tree with an empty git status - RUNNER "
    "PASS 513/513 suites plus controls 7/7 in 1317.7s with criteria total 4054 "
    "EXACTLY as pre-registered and TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 "
    "failed=0 (qa/reconcile-all-R2387.log, 820179B, single writer utf-8 LF "
    "through src/os/battery_stream.py, never a shell redirection); the four "
    "follow-up sections ran through src/os/battery_followup.py, the matrix "
    "section FAILED first on the stale doc (on-disk=49095B regenerated=49188B) "
    "and did not rewrite it, suite_matrix regenerated "
    "docs/sandbox-suite-matrix.md to 513 suites / 4054 criteria and the re-run "
    "read all four PASS for VERDICT R2387 PASS; evidence and matrix committed "
    "ALONE as bba99b85 before any product byte changed (the R2168 mixed-tree "
    "rule). PRODUCT: claimed state/queue/tech.md:439 prefix AC-RWGB1 "
    "(review_window_guard_parity_blind_agreement), criteria pinned in that row "
    "at R2381 BEFORE any code, anchors prose-only at HEAD (that row, "
    "src/os/closeout_R2381.py, src/os/state.json, zero hits under src/*.py in "
    "the parity naming). SHIPPED src/os/"
    "review_window_guard_parity_blind_agreement.py plus its six-criteria suite: "
    "the shipped parity is imported and asked at CALL time, so patching its "
    "check moves this reading and no second rewind comparison, declarations "
    "reader or row parser is written here; a side that answered 'I could not "
    "judge' is named as an ignorance (the argument face's own UNKNOWN word is "
    "taken from that face's vocabulary at call time rather than restated) and a "
    "pair that agrees only because nobody could judge reads PARITY-UNKNOWN with "
    "both carried codes - never AGREES; a genuine two-sided rewind, a clean or "
    "merely moved list, and a deliberately UNPINNED list keep PARITY-AGREES and "
    "keep the parity's eight fields byte for byte; a real split still reads "
    "PARITY-DISAGREES naming both codes and outranks an ignorance instead of "
    "being swallowed by it; the CLI adds exactly one exit code (1 for UNKNOWN) "
    "to 0/2/3/5 and the JSON adds exactly one key, ignorance, after the eight "
    "pinned ones. SUITE PASS 6/6 twice with an identical criterion digest plus "
    "three adjacent review-window suites green "
    "(qa/review-window-guard-parity-blind-agreement-R2387.log, 3803B, legs=2 "
    "identical=True adjacent=3 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired "
    "os-review-window-guard-parity-blind-agreement(6) so the registry reads 514 "
    "suites / 4060 criteria. LIVE, not a plan: "
    "qa/review-window-guard-parity-blind-agreement-live-R2387.log (529B, "
    "crlf=0, lf=6) reads the real tree verdict=PARITY-AGREES rewind=no "
    "window=100 declared=WINDOW argument=ARGUMENT-CLEAN agrees=yes "
    "ignorance=none with a byte-stable --json over the nine pinned keys, and a "
    "fixture declaration neither face can read reads PARITY-UNKNOWN "
    "ignorance=both declared=E_RWW_UNREADABLE argument=ARGUMENT-UNKNOWN at rc 1 "
    "where the shipped parity still reads PARITY-AGREES. Tech row 439 stamped "
    "[done 2026-11-02 R2387] through src/os/board_R2387.py (payload 23 chars "
    "inside the 60-char stamp law, 1027173 -> 1030136 chars with readback ok) "
    "and one REAL measured gap row seeded (parity_consumer_wire, "
    "AC-RWPC1..AC-RWPC6 pre-registered in that row, five anchors zero-"
    "occupancy): git grep proves RWGP. has ZERO non-test hits under src/, so "
    "the reading refuses nothing an operator walks. Gauge after the stamp and "
    "the seed reads claimable=10 tech (FLOOR-MET) and the reader now offers line "
    "442 prefix AC-RNED1. Register: reconcile-battery-R2386 closed through "
    "debt_close (line=158, open 3->2, done 114->115, 84810B->84813B, readback "
    "ok) and reconcile-battery-R2387 opened first=yes through debt_append at the "
    "measured successor target 514 suites / 4060 criteria (84813B->85099B, "
    "readback ok). Five-silence scan at open read LEDGER with zero @BigDomain "
    "lines, DEC tokens 86 with new=0 and gone=0 over the stored baseline (row "
    "count 137 -> 172 is formatting movement, not a directive), the group "
    "orders tail still the 2026-11-02 11:04 model-policy baseline already "
    "acknowledged as non-execution, and benchmarks refreshed 2026-11-02 inside "
    "the seven-day gate.")

DISC_LINE = (
    "R2387 honest disclosures: (a) AC-RWGB1 was RED on its first run and the "
    "red was this window own assertion, never the module: it expected the "
    "argument side's code to start with E_RWAG, while the shipped argument "
    "guard legitimately carries the history code through its own mapping as "
    "E_RWW_UNREADABLE and words the refusal with ARGUMENT-UNKNOWN; the "
    "assertion now pins the measured pair (that face's own UNKNOWN word plus "
    "the carried code) and no criterion was widened. (b) The value of this "
    "window rests on a gap MEASURED at R2381 and re-measured here: the shipped "
    "parity reads PARITY-AGREES on the same unreadable world, which the suite "
    "asserts side by side so the improvement is named rather than claimed. (c) "
    "The UNKNOWN path is proved on a FIXTURE, not live: the real tree carries a "
    "readable declaration, so the live log says AGREES with ignorance=none and "
    "does not imply a live catch. (d) The ignorance classification keys on "
    "refusal-code SUFFIXES plus that face's UNKNOWN word, which is honest about "
    "what it has seen and blind to a future unreadable code that ends "
    "differently - reported here rather than hidden. (e) The board stamp and "
    "the seed row were landed by src/os/board_R2387.py rather than by hand, and "
    "the register rows through the shipped debt_close/debt_append CLIs, so this "
    "closeout only writes state, backlog, heartbeat and the export. (f) "
    "tasks.md was left untouched: it is the P-47 canonical board and carries no "
    "row for this tech slice. (g) This window ran past its 25-minute budget: "
    "the battery alone measured 1317.7s, and the product face was still shipped "
    "rather than deferred, because the evidence tree was committed and clean "
    "before any product byte changed.")

SELF_HEAL_LINE = (
    "R2387 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal but needs an elevated shell, and this session is unelevated, "
    "so the task definition was left untouched (hundred-and-forty-second "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md).")

TOKENS_LINE = (
    "R2387 tokens: local=~24k api=0 api_reason=verification-then-product window "
    "- one full battery (513 suites, 1317.7s, launched detached after the "
    "five-minute no-output trap) plus its four follow-up sections and one matrix "
    "regeneration, one blind-agreement face and its six-criteria suite written "
    "to criteria pinned six rounds earlier, one registry wiring line, one "
    "two-leg evidence capture with three adjacent suites, one five-step live "
    "capture through a single utf-8 LF writer, one board stamp and one measured "
    "gap row seeded through a round helper, one register row closed and one "
    "successor row opened through the shipped CLIs, and the "
    "state/backlog/export/heartbeat closeout; zero cloud calls and zero external "
    "API touches")

ITEMS = [MAIN_LINE, DISC_LINE, SELF_HEAL_LINE, TOKENS_LINE]

BACKLOG_ROW = (
    "- [x] R2387 [done 2026-11-02] review_window_guard_parity_blind_agreement - "
    "state/queue/tech.md:439 AC-RWGB1..AC-RWGB6 delivered: the review-window "
    "parity compared two rewind booleans, so a pair that agreed only because "
    "NEITHER face could read the declaration read PARITY-AGREES - a green over "
    "exactly the file that would break both paths. The shipped parity is now "
    "asked at call time and its answer is classified: an ignorant side is named "
    "(that face's own UNKNOWN word taken from its vocabulary, not restated) and "
    "the pair reads PARITY-UNKNOWN naming both carried codes at exit 1, a real "
    "split still reads PARITY-DISAGREES and outranks an ignorance, and every "
    "informed reading keeps the parity's eight fields byte for byte. The window "
    "also discharged the carried battery: RUNNER PASS 513/513 suites, criteria "
    "4054 exactly as pre-registered.\n")

HEARTBEAT_ROW = (
    "%s R2387 verification-then-product: battery 513/513 suites 4054 criteria "
    "green; review_window_guard_parity_blind_agreement shipped, live tree reads "
    "PARITY-AGREES ignorance=none while a fixture neither face can read now "
    "reads PARITY-UNKNOWN at rc 1\n" % STAMP)


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
    if "done 2026-11-02 R2387" in text:
        print("TECH already stamped by board_R2387.py")
        return
    raise SystemExit("E_TECH stamp missing: board_R2387.py must run first")


def close_debt(execute):
    text = read_text(DEBT)
    if "item=reconcile-battery-R2387" in text:
        print("DEBT already carries the R2387 rows via the shipped CLIs")
        return
    raise SystemExit("E_DEBT register not updated")


def prepend_backlog(execute):
    text = read_text(BACKLOG)
    if "R2387 [done 2026-11-02] review_window_guard_parity_blind_agreement" \
            in text:
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
    if "R2387 verification-then-product" in text:
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
                  and row[0] == "R2387" for row in data["results"])
    if not already:
        data["outs"].append([
            "src/os/review_window_guard_parity_blind_agreement.py", "on",
            "R2387 product: the review-window parity no longer reports a blind "
            "agreement as a green - a pair that agrees only because neither "
            "face could read the declaration reads PARITY-UNKNOWN naming both "
            "carried codes at exit 1, while every informed reading keeps the "
            "parity's own eight fields byte for byte",
        ])
        data["results"].append(["R2387", MAIN_LINE])
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