"""closeout_R2384 - live capture, board, state, heartbeat and export.

The window claimed state/queue/tech.md:431 (prefix AC-EPPG1, the R2378 seed row)
and shipped src/os/export_publish_path_guard.py plus its six-criteria suite. This
script does the rest of the round in one place so every write goes through ONE
utf-8 LF writer instead of a shell redirection:

  STEP 1..7  the live capture in qa/export-publish-path-guard-live-R2384.log
  BOARD      stamp tech row 431 and seed the successor seam the capture measures
  STATE      tick +1, this window's log items, the two decision baselines
  EXPORT     refreshed through closeout_export_parity_wire.publish, so this
             closeout is a CLEAN current publisher by its own new reading

Source is ASCII, stdlib only, zero network.
"""

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402
import closeout_export_parity_wire as CEPW  # noqa: E402
import export_publish_path_guard as EPPG  # noqa: E402
import queue_floor_export_face as QFE  # noqa: E402
import state_io  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
TECH = os.path.join(REPO, "state", "queue", "tech.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
QA = os.path.join(REPO, "qa")
LIVE_LOG = os.path.join(QA, "export-publish-path-guard-live-R2384.log")

STAMP = "2026-11-02T18:05:00+08:00"
DUE = "2026-11-04T23:59:59+08:00"
MODULE = os.path.join(BASE, "export_publish_path_guard.py")

DO = (
    "R2384 product window: the export's own write path is finally a reading. "
    "export_publish_path_guard walks a tree, decides which scripts belong to "
    "the CURRENT publishing path (does the script ask queue_floor_export_face, "
    "the module that owns the current shape) and names every one of those that "
    "writes docs/status-export.json itself instead of handing the bytes to "
    "closeout_export_parity_wire.publish. On the real tree it reads BYPASS over "
    "5 offenders against 7 clean, so the bypass is measured rather than assumed."
)

ARTIFACT = (
    "src/os/export_publish_path_guard.py plus its six-criteria suite "
    "(qa/export-publish-path-guard-R2384.log, two legs with an identical "
    "criterion digest, three adjacent suites green) and one runner wiring line; "
    "the live capture reads 1018 scripts walked, 143 publishers, 12 on the "
    "current path, 5 offenders named with file and line and 131 historical "
    "fossils counted but not accused "
    "(qa/export-publish-path-guard-live-R2384.log)."
)

NEXT = (
    "R2385: the battery on the committed R2384 tree, pre-registered at 511 "
    "suites / 4042 criteria, then the successor seam this window's own live "
    "capture measures: a script that hands the export to ANOTHER module's "
    "publish still reads CLEAN, so the call is not yet proven to be the proven "
    "wire."
)

BOARD_STAMP_FROM = "- [ ] P2 tech seed (R2378, from this window own measured gap):"
BOARD_STAMP_TO = (
    "- [x] [done 2026-11-02 R2384] P2 tech seed (R2378, from this window own "
    "measured gap):"
)

SEED_ROW = (
    "- [ ] P2 tech seed (R2384, from this window own measured seam): "
    "`src/os/export_publish_wire_identity.py` - the guard now names every "
    "CURRENT publisher that writes the export itself, and its routed side reads "
    "any `.publish(..., EXPORT, ...)` as the proven path. Measured in this "
    "window's live capture STEP7: a fixture that hands the export to a "
    "different module's publish call reads CLEAN, so a script can satisfy the "
    "guard while never touching closeout_export_parity_wire. Product: one "
    "reading that resolves the callee of a publish call against the wire that "
    "actually proves the bytes, so routed means routed-by-the-wire. Criteria "
    "AC-EPWI1..AC-EPWI6 pre-registered HERE BEFORE any code: AC-EPWI1 the "
    "identity reading names, per routed script, the module its publish call "
    "resolves to; AC-EPWI2 a publish to the parity wire reads WIRE and a "
    "publish to any other module reads FOREIGN, naming both; AC-EPWI3 a script "
    "with no routed publish reads NO-PUBLISH rather than WIRE by accident; "
    "AC-EPWI4 the reading is derived from the import lines and the call line "
    "together, so renaming the import but not the call (or the reverse) reads "
    "UNRESOLVED instead of guessing; AC-EPWI5 exit 0 = WIRE, 2 = FOREIGN or "
    "UNRESOLVED, 3 = missing root, 5 = bad flags, byte-stable --json over "
    "pinned keys; AC-EPWI6 no write, no clock, ASCII stdlib only, own reconcile "
    "label. Five anchors zero-occupancy at HEAD 2026-11-02: "
    "export_publish_wire_identity, AC-EPWI, E_EPWI, "
    "os-export-publish-wire-identity, test_export_publish_wire_identity."
)

ITEMS = [
    "2026-11-02 R2384 product window (five-silence scan clean at open: empty "
    "git status at HEAD 504eda6b, no .git/index.lock; scan_five_still read "
    "LEDGER atbd_lines=0 unreplied_groups=0, DEC rows=137 tokens=86 new=0, the "
    "group orders tail still the 2026-11-02 11:04 model-policy baseline already "
    "acknowledged as non-execution, and benchmarks refreshed 2026-11-02 inside "
    "the seven-day gate). The debt gate named CLAIM-FIRST "
    "item=reconcile-battery-R2383 (510 suites / 4036 criteria expected) and the "
    "product-first law outranked it: this window took the product face and the "
    "battery row stays OPEN with its measured target named, because a window "
    "that does not run a battery cannot close its row.",

    "R2384 product face, the row the reader named: CLAIMED "
    "state/queue/tech.md:431 prefix AC-EPPG1 (export_publish_path_guard), whose "
    "AC-EPPG1..AC-EPPG6 were pinned INSIDE that row at R2378 BEFORE any code, "
    "after a fresh anchor check at HEAD: the five anchors hit only prose and "
    "state files with zero executable occupancy.",

    "R2384 the guard: shipped src/os/export_publish_path_guard.py plus "
    "src/os/test_export_publish_path_guard.py. The scope is deliberately narrow, "
    "because a wide one would be noise: the repository carries 131 one-off "
    "historical scripts that wrote whatever the export shape was at their round, "
    "and those are reported as `historical` and never accused. A script belongs "
    "to the CURRENT path when it asks queue_floor_export_face (a --owner flag, "
    "not a filename list); within that path a script that names the export in a "
    "write primitive reads BYPASS with its file and line, and a script whose "
    "publishes all go through a publish call carrying the export reads CLEAN. A "
    "two-step handle write is caught at the open() line that names the export. "
    "The file is pure ASCII stdlib, writes nothing and reads no clock.",

    "R2384 evidence and board: SUITE PASS 6/6 twice with an identical criterion "
    "digest plus three adjacent suites green (qa/export-publish-path-guard-R2384.log, "
    "1663B, legs=2 identical=True adjacent=3 fails=0, single writer utf-8 LF "
    "through src/os/evidence_capture.py), wired os-export-publish-path-guard(6) "
    "so the registry reads 511 suites / 4042 criteria. LIVE, not a plan: on the "
    "real src/os tree qa/export-publish-path-guard-live-R2384.log reads "
    "verdict=BYPASS over 1018 scripts with 143 publishers, 12 on the current "
    "path, 7 clean (closeout_R2377..R2383, all of which hand their bytes to the "
    "parity wire) and 5 offenders named by file and line "
    "(closeout_R2374.py:411, closeout_R2375.py:375, closeout_R2376.py:376, "
    "export_R2368.py:139, export_R2373.py:149) plus 131 historical. Tech row "
    "431 stamped [done 2026-11-02 R2384] and one REAL measured gap row seeded "
    "(export_publish_wire_identity, AC-EPWI1..AC-EPWI6 pre-registered in that "
    "row, five anchors zero-occupancy): a fixture that hands the export to a "
    "different module's publish call still reads CLEAN.",

    "R2384 honest disclosures: (a) the first law was too wide - it accused all "
    "143 publishers including 131 fossils from 2019-era rounds - and it was "
    "narrowed to the current publishing path BEFORE any evidence was captured, "
    "with the historical class kept visible rather than deleted, so the gauge "
    "can be green without hiding them. (b) AC-EPPG3's first assertion banned "
    "every `.write(` and therefore flagged the CLI's own sys.stdout.write; the "
    "assertion now compares the whole tree before and after two audits and bans "
    "only non-console writes and any file opened for writing - no criterion was "
    "widened. (c) The battery the debt gate named did NOT run this window: the "
    "product-first law outranked it and the register row stays OPEN at 510 "
    "suites / 4036 criteria, disclosed rather than closed. (d) The window "
    "overran its 25-minute budget, stated plainly. (e) tasks.md was left "
    "untouched: it is the P-47 canonical board and carries no row for this tech "
    "slice.",

    "R2384 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal but needs an elevated shell, and this session is unelevated, "
    "so the task definition was left untouched (hundred-and-thirty-ninth "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md).",

    "R2384 tokens: local=~22k api=0 api_reason=product window - one guard and "
    "its six-criteria suite written to criteria pinned six rounds earlier, one "
    "law narrowed after a measured over-broad first reading, one registry wiring "
    "line, one two-leg evidence capture with three adjacent suites, one seven-step "
    "live capture over 1018 scripts through a single utf-8 LF writer, one board "
    "stamp and one measured gap row seeded, and the state/backlog/export/heartbeat "
    "closeout; zero cloud calls and zero external API touches",
]

BACKLOG_ROW = (
    "- [x] R2384 [done 2026-11-02] export_publish_path_guard - "
    "state/queue/tech.md:431 AC-EPPG1..AC-EPPG6 delivered: every script that "
    "belongs to the current export publishing path is now read, and each one "
    "that names docs/status-export.json in a write primitive is named BYPASS "
    "with its file and line while a script whose publishes all go through a "
    "publish call reads CLEAN; old one-off scripts are historical, not "
    "offenders. The live reading over src/os is BYPASS with 5 offenders "
    "(closeout_R2374/75/76, export_R2368/73) against 7 clean (R2377..R2383)."
)

HBT = "2026-11-02T18:05:00+08:00 R2384 product: export_publish_path_guard reads BYPASS over 1018 scripts (5 offenders, 7 clean, 131 historical)"

NEW_DEC_TOKENS = ()
DEC_ROWS_NOW = 137


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def digest(root, limit=None):
    """sha256 over every file path and its bytes, the write-nothing proof."""
    out = hashlib.sha256()
    count = 0
    for base, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(base, name)
            out.update(os.path.relpath(path, root).replace(os.sep, "/")
                       .encode("utf-8"))
            out.update(b"\0")
            with io.open(path, "rb") as handle:
                out.update(handle.read())
            out.update(b"\0")
            count += 1
            if limit is not None and count >= limit:
                return out.hexdigest(), count
    return out.hexdigest(), count


def run_module(argv):
    done = subprocess.run([sys.executable, MODULE] + argv,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (done.returncode,
            done.stdout.decode("utf-8", "replace"),
            done.stderr.decode("utf-8", "replace"))


BYPASS_FIXTURE = '''"""A current publisher that writes the export itself."""

import os

import queue_floor_export_face as QFE

EXPORT = os.path.join("docs", "status-export.json")


def wiki(path, text):
    return None


def publish(data):
    QFE.apply(data, ".")
    wiki(EXPORT, "{}")
'''

ROUTED_FIXTURE = '''"""The same publisher, routed through the parity wire."""

import os

import closeout_export_parity_wire as CEPW
import queue_floor_export_face as QFE

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
    return CEPW.publish(".", EXPORT, text="{}")
'''

FOREIGN_FIXTURE = '''"""A current publisher that hands the export to some other publish."""

import os

import queue_floor_export_face as QFE
import some_other_module

EXPORT = os.path.join("docs", "status-export.json")


def publish(data):
    QFE.apply(data, ".")
    return some_other_module.publish(".", EXPORT, text="{}")
'''


def fixture_world(scripts):
    root = tempfile.mkdtemp(prefix="eppg-live-")
    for name, text in scripts:
        write_text(os.path.join(root, name), text)
    return root


def live_capture(execute):
    lines = []
    add = lines.append
    add("EXPORT PUBLISH PATH GUARD LIVE CAPTURE R2384")
    add("root=%s" % os.path.join(REPO, "src", "os"))
    add("")

    before, files = digest(os.path.join(REPO, "src", "os"), limit=None)
    add("STEP1 write-nothing baseline files=%d digest=%s" % (files, before[:16]))

    report, code = EPPG.audit(os.path.join(REPO, "src", "os"))
    add("STEP2 real tree verdict=%s rc=%d scanned=%d publishers=%d current=%d "
        "historical=%d" % (report["verdict"], code, report["scanned"],
                           len(report["publishers"]),
                           len(report["clean"]) + len(report["offenders"]),
                           len(report["historical"])))
    for row in report["detail"]:
        add("  BYPASS %s:%d %s" % (row["path"], row["line"], row["text"]))
    add("  CLEAN %s" % ",".join(report["clean"]))

    world = fixture_world([("bypass_copy.py", BYPASS_FIXTURE),
                           ("routed_copy.py", ROUTED_FIXTURE)])
    fixture, fixture_code = EPPG.audit(world)
    add("STEP3 routed copy verdict=%s rc=%d offenders=%s clean=%s" % (
        fixture["verdict"], fixture_code,
        ",".join(fixture["offenders"]) or "(none)",
        ",".join(fixture["clean"]) or "(none)"))

    rc_a, out_a, _ = run_module(["--check", "--root",
                                 os.path.join(REPO, "src", "os"), "--json"])
    rc_b, out_b, _ = run_module(["--check", "--root",
                                 os.path.join(REPO, "src", "os"), "--json"])
    add("STEP4 json byte-stable=%s rc=%d/%d bytes=%d" % (
        out_a == out_b, rc_a, rc_b, len(out_a.encode("utf-8"))))

    rc_missing, _, err_missing = run_module(
        ["--check", "--root", os.path.join(world, "nope")])
    rc_flags, _, err_flags = run_module(["--check", "--root", world, "--bogus"])
    add("STEP5 missing-root rc=%d %s" % (rc_missing, err_missing.strip()))
    add("STEP6 bad-flags rc=%d %s" % (rc_flags, err_flags.strip()))

    foreign = fixture_world([("foreign_writer.py", FOREIGN_FIXTURE)])
    foreign_report, foreign_code = EPPG.audit(foreign)
    add("STEP7 foreign publish verdict=%s rc=%d offenders=%s clean=%s "
        "(the seeded seam: a publish to another module reads CLEAN)" % (
            foreign_report["verdict"], foreign_code,
            ",".join(foreign_report["offenders"]) or "(none)",
            ",".join(foreign_report["clean"]) or "(none)"))

    after, files_after = digest(os.path.join(REPO, "src", "os"), limit=None)
    add("STEP8 write-nothing after files=%d digest=%s identical=%s" % (
        files_after, after[:16], before == after))
    add("VERDICT LIVE-BYPASS-MEASURED offenders=%d clean=%d historical=%d" % (
        len(report["offenders"]), len(report["clean"]),
        len(report["historical"])))

    shutil.rmtree(world, ignore_errors=True)
    shutil.rmtree(foreign, ignore_errors=True)

    text = "\n".join(lines) + "\n"
    if not os.path.isdir(QA):
        os.makedirs(QA)
    if execute:
        back = write_text(LIVE_LOG, text)
        if back != text:
            raise SystemExit("E_LIVE readback")
        print("LIVE bytes=%d" % len(back.encode("utf-8")))
    else:
        print("LIVE dry run bytes=%d" % len(text.encode("utf-8")))
    for line in lines:
        print("  " + line)


def stamp_board(execute):
    text = read_text(TECH)
    if BOARD_STAMP_TO in text:
        print("BOARD already stamped")
    else:
        if text.count(BOARD_STAMP_FROM) != 1:
            raise SystemExit("E_BOARD_STAMP count=%d"
                             % text.count(BOARD_STAMP_FROM))
        text = text.replace(BOARD_STAMP_FROM, BOARD_STAMP_TO, 1)
        if execute:
            back = write_text(TECH, text)
            if back != text:
                raise SystemExit("E_BOARD readback")
            print("BOARD stamped row 431")
    if "export_publish_wire_identity" in text:
        print("BOARD already carries the seed")
        return
    if not text.endswith("\n"):
        text += "\n"
    text = text + SEED_ROW + "\n"
    if execute:
        back = write_text(TECH, text)
        if back != text:
            raise SystemExit("E_SEED readback")
        print("BOARD seed bytes=%d" % len(back.encode("utf-8")))


def prepend_backlog(execute):
    text = read_text(BACKLOG)
    if BACKLOG_ROW[:60] in text:
        print("BACKLOG already carries this row")
        return
    if execute:
        back = write_text(BACKLOG, BACKLOG_ROW + "\n" + text)
        if not back.startswith(BACKLOG_ROW):
            raise SystemExit("E_BACKLOG readback")
        print("BACKLOG bytes=%d" % len(back.encode("utf-8")))


def append_heartbeat(execute):
    text = read_text(HEARTBEAT)
    if HBT[:40] in text:
        print("HEARTBEAT already carries this row")
        return
    if text and not text.endswith("\n"):
        text += "\n"
    if execute:
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
    data["last_order"] = "2026-11-01 10:4x"
    data["benchmarks_refreshed"] = "2026-11-02"
    data["last_decision_rows"] = DEC_ROWS_NOW
    data["log"] = list(data["log"]) + ITEMS
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    text = state_io.canon(text)
    print("STATE tick=%d items=+%d rows=%d before=%dB predicted=%dB"
          % (tick, len(ITEMS), DEC_ROWS_NOW, before, len(text.encode("utf-8"))))
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
                  and row[0] == "R2384" for row in data["results"])
    if not already:
        data["outs"].append([
            "src/os/export_publish_path_guard.py", "on",
            "R2384 product: every script on the current export publishing path "
            "is now read - the ones that write docs/status-export.json "
            "themselves are named BYPASS with file and line, the ones that hand "
            "their bytes to the parity wire read CLEAN, and 2019-era one-offs "
            "are reported as historical instead of accused",
        ])
    if not already:
        data["results"].append([
            "R2384",
            "product window: the debt gate named reconcile-battery-R2383 and "
            "the product-first law outranked it, so the row stays OPEN at 510 "
            "suites / 4036 criteria and the product face shipped instead. "
            "CLAIMED state/queue/tech.md:431 AC-EPPG1 export_publish_path_guard, "
            "criteria pinned there at R2378, anchors prose-only at HEAD. The "
            "law was narrowed once, before any evidence, after a measured "
            "over-broad first reading accused 131 historical scripts. SUITE "
            "PASS 6/6 twice identical plus three adjacent suites green "
            "(1663B), wired os-export-publish-path-guard(6) so the registry "
            "reads 511/4042. LIVE over 1018 scripts: BYPASS with 5 offenders "
            "(closeout_R2374:411, closeout_R2375:375, closeout_R2376:376, "
            "export_R2368:139, export_R2373:149) against 7 clean "
            "(closeout_R2377..R2383). Row stamped and one REAL measured gap "
            "seeded (export_publish_wire_identity: a publish to another "
            "module still reads CLEAN).",
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
    live_capture(execute)
    stamp_board(execute)
    state_tick, state = close_state(execute)
    if execute:
        prepend_backlog(execute)
        append_heartbeat(execute)
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