"""R2415 closeout: a product window that shipped the declared-package join.

Every number below is this window's own measurement, not a prediction: the
suite legs, the adjacent count, the live reading, the registry total and the
two queue/debt reads all come from commands that ran.

Writes, in this order, each step proving its own predicted size:

1. src/os/state.json through the layout law (tick 2415, seven items, and the
   two decision tokens that the content-addressed diff surfaced this window),
2. docs/status-export.json (the CEO-visible three lines and derived counters),
3. src/os/backlog.md (one delivered row),
4. heartbeat.txt.
"""

import io
import json
import os

import state_io

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(SRC)
STATE = os.path.join(SRC, "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
BACKLOG = os.path.join(SRC, "os", "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
PATTERNS = os.path.join(SRC, "os", "export_consistency_patterns.json")
DEBT = os.path.join(ROOT, "state", "debt.md")

ROUND = 2415
STAMP = "2026-11-03T16:20:00+08:00"

NEW_TOKENS = ("D-20261025-06", "D-20261025-18")
TOKEN_ANCHOR = '    "D-20261024-13",\r\n'

DEBT_MARKER = "closed=R2415"

LOG_ITEMS = [
    "2026-11-03 R2415 five-silence scan at open: git status empty at HEAD "
    "d8550019 with no .git/index.lock; the evolution ledger carries no "
    "@BigDomain row (zero unreplied); the content-addressed decisions diff "
    "read 208 rows and 105 tokens with two NEW tokens, D-20261025-06 and "
    "D-20261025-18, both of which the diff located inside the body of "
    "D-20261103-17 as numbered REFERENCES rather than as decision rows, so "
    "they were known, not dispatched (recorded in the baseline, nothing "
    "executed); benchmarks refreshed 2026-11-03 inside the seven-day gate; "
    "the group orders.md tail currently ends with merge-conflict residue "
    "lines (>>>>>>> d2a66071 / >>>>>>> Stashed changes) in a file this "
    "company may not write, disclosed rather than touched.",

    "2026-11-03 R2415 the debt gate named CLAIM-FIRST item=product-face-R2415 "
    "and the tech head reader read state/queue/tech.md:482 prefix AC-PRPI1 "
    "(claimable=11, floors main 5/5 tech 11/10 explore 10/10), whose six "
    "criteria had been pinned at R2402 BEFORE any code, so that row was "
    "claimed.",

    "2026-11-03 R2415 product face shipped: "
    "src/os/publish_relative_package_identity.py plus "
    "src/os/test_publish_relative_package_identity.py. ONE added notion - the "
    "caller-DECLARED package - joins the relative module text that "
    "relative_import_publish_binding already names (a lone dot is the package, "
    "a dot plus a tail is package.tail, two dots drop one package segment), "
    "after which the PARENT law's own classify_line is asked at CALL time with "
    "the joined text, so the call reads WIRE when the join is the wire module "
    "and FOREIGN otherwise. There is still exactly one publish classifier in "
    "the tree: this file adds a join and no parser.",

    "2026-11-03 R2415 evidence: SUITE PASS criteria=6 passes=6 fails=0 twice "
    "with an identical criterion digest plus three adjacent suites green "
    "(qa/publish-relative-package-identity-R2415.log, 1310B, legs=2 "
    "identical=True adjacent=3 fails=0), wired "
    "os-publish-relative-package-identity(6) in src/sandbox/reconcile_all.py "
    "so the registry now reads 535 suites / 4186 criteria.",

    "2026-11-03 R2415 live reading, not a plan: "
    "qa/publish-relative-package-identity-live-R2415.log (2580B) reads the "
    "REAL src/os tree as WIRE 11 publishers over 1143 scanned files with "
    "relative=0 both with and without a declared package; the same relative "
    "fixture reads WIRE module=mypkg.wire under --package mypkg --wire "
    "mypkg.wire and FOREIGN at exit 2 when the wire is left at the default; "
    "the parent law reads that fixture RELATIVE at exit 2; a two-dot climb "
    "refuses E_PRPI_CANNOT_JOIN at exit 2 naming package and module text; and "
    "a bad declaration refuses E_PRPI_BAD_PACKAGE at exit 5.",

    "2026-11-03 R2415 honest disclosures: (a) NO reconcile battery ran this "
    "window - the tree changed by design, so the battery belongs to the "
    "committed head and reconcile-battery-R2415 was registered first=yes with "
    "the measured target 535 suites / 4186 criteria; (b) the debt register "
    "still carries the stale row loop-s4u-reconcile (184 windows) and the "
    "matrix-stamp-compare row measured at R2414, neither discharged here; "
    "(c) one real gap was MEASURED, not guessed, and seeded as "
    "relative_module_existence_face: `from .nosuchmodule import publish` under "
    "--package mypkg joins to mypkg.nosuchmodule and reads FOREIGN at exit 2 "
    "although no such module exists, so a typo and a foreign wire read "
    "identically; AC-RMEF1..AC-RMEF6 are pinned in that row BEFORE any code; "
    "(d) tasks.md was not touched - its P1 rows remain blocked-on-CEO and its "
    "on-disk encoding is not plain UTF-8; (e) the group orders.md tail carries "
    "merge-conflict residue that this company may not repair.",

    "2026-11-03 R2415 self-heal check: BigDomain-OSLoop is still registered "
    "with LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 passes an "
    "explicit S4U principal but needs an elevated shell and this session is "
    "unelevated, so the task definition was left untouched "
    "(hundred-and-seventieth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md).",

    "R2415 tokens: local=~30k api=0 api_reason=product window - one product "
    "module and its six-criteria suite written against criteria pinned at "
    "R2402, two full suite legs with an identical digest plus three adjacent "
    "suites, one live capture over the real tree and four fixtures, one "
    "runner wiring line, one queue row stamped plus one measured gap row "
    "seeded, one debt row closed and one successor registered, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]

EXPORT_DO = (
    "R2415 product: publish_relative_package_identity joins a caller-declared "
    "package onto the relative publish module and the parent law's own "
    "classifier then reads WIRE or FOREIGN; an unjoinable declaration refuses "
    "by name, and with no package every reading is the parent's own byte for "
    "byte"
)
EXPORT_ARTIFACT = (
    "src/os/publish_relative_package_identity.py + "
    "qa/publish-relative-package-identity-R2415.log (1310B, legs=2 "
    "identical=True) + qa/publish-relative-package-identity-live-R2415.log "
    "(2580B)"
)
EXPORT_MILESTONE = (
    "reconcile-battery-R2415: one green RUNNER PASS over the 535 suites / "
    "4186 criteria on the committed tree, then the four follow-up sections"
)
EXPORT_DUE = "2026-11-04T23:00:00+08:00"

BACKLOG_ROW = (
    "- [x] [done 2026-11-03 R2415] R2415 product window: "
    "publish_relative_package_identity - the relative binding named the "
    "relative module text but reads one file on its own, so an in-package "
    "publisher spelled `from .wire import publish` stayed RELATIVE. SHIPPED "
    "src/os/publish_relative_package_identity.py plus its six-criteria suite: "
    "ONE added notion (the caller-DECLARED package) joins `.` to the package, "
    "`.M` to package.M and drops one package segment per extra leading dot, "
    "after which the PARENT law's classify_line is asked at CALL time with the "
    "joined text and the call reads WIRE or FOREIGN like any absolute one; no "
    "package keeps the parent's RELATIVE reading byte for byte, proved by "
    "comparing every row and every audit count with "
    "relative_import_publish_binding on the same tree. Two refusals name the "
    "declaration instead of inventing a module: E_PRPI_BAD_PACKAGE at exit 5 "
    "and E_PRPI_CANNOT_JOIN (verdict REFUSED at exit 2). SUITE PASS 6/6 twice "
    "with an identical digest plus three adjacent suites green "
    "(qa/publish-relative-package-identity-R2415.log, 1310B, legs=2 "
    "identical=True adjacent=3 fails=0), wired "
    "os-publish-relative-package-identity(6) so the registry reads 535 suites "
    "/ 4186 criteria. LIVE: the real src/os reads WIRE 11 publishers / 1143 "
    "scanned / relative=0 with and without a package, the fixture reads WIRE "
    "module=mypkg.wire and FOREIGN at exit 2 against the default wire, a "
    "two-dot climb refuses E_PRPI_CANNOT_JOIN, and a bad package refuses at "
    "exit 5. One measured gap seeded: relative_module_existence_face "
    "(AC-RMEF1..AC-RMEF6) - a join with no module behind it still reads "
    "FOREIGN. No battery ran: reconcile-battery-R2415 is registered first=yes "
    "at the same 535 suites / 4186 criteria.\n"
)


def _read(path, encoding="utf-8", newline=None):
    with io.open(path, "r", encoding=encoding, newline=newline) as handle:
        return handle.read()


def _write(path, text, newline=""):
    with io.open(path, "w", encoding="utf-8", newline=newline) as handle:
        handle.write(text)


def step_debt():
    text = _read(DEBT, newline="")
    if DEBT_MARKER in text and "item=product-face-R2415" in text:
        print("debt row already closed for R2415")
        return
    raise SystemExit("E_C2415_DEBT: product-face-R2415 is not closed")


def step_state():
    text = state_io.decode(state_io.read_raw(STATE))
    crlf = text.count("\r\n")
    if crlf == 0 or text.count("\n") != crlf:
        raise SystemExit("E_C2415_STATE_NOT_CRLF")
    state = json.loads(text)
    live = sum(1 for item in LOG_ITEMS if item in text)
    if state["tick"] == ROUND and live == len(LOG_ITEMS):
        print("state already at tick=%d with all %d items, nothing to do"
              % (ROUND, len(LOG_ITEMS)))
        return state
    if live:
        raise SystemExit("E_C2415_ITEM_PARTIAL: %d/%d" % (live, len(LOG_ITEMS)))
    if state["tick"] != ROUND - 1:
        raise SystemExit("E_C2415_TICK: %r" % (state["tick"],))
    old_tick = '"tick": %d,' % state["tick"]
    if text.count(old_tick) != 1:
        raise SystemExit("E_C2415_TICK_TEXT")
    text = text.replace(old_tick, '"tick": %d,' % ROUND)
    missing = [token for token in NEW_TOKENS
               if token not in state["last_dec_tokens"]]
    if missing:
        if text.count(TOKEN_ANCHOR) != 1:
            raise SystemExit("E_C2415_TOKEN_ANCHOR")
        addition = "".join('    "%s",\r\n' % token for token in missing)
        text = text.replace(TOKEN_ANCHOR, TOKEN_ANCHOR + addition)
    closer = '"\r\n  ]\r\n}\r\n'
    if not text.endswith(closer):
        raise SystemExit("E_C2415_CLOSER")
    block = ",\r\n".join(
        " " * 16 + json.dumps(item, ensure_ascii=False) for item in LOG_ITEMS)
    text = text[: -len(closer)] + '",\r\n' + block + "\r\n  ]\r\n}\r\n"
    layout = state_io.layout(text)
    if not layout["layout_ok"]:
        raise SystemExit("E_C2415_LAYOUT: %r" % (layout,))
    parsed = json.loads(text)
    if parsed["tick"] != ROUND:
        raise SystemExit("E_C2415_TICK_READBACK")
    if not set(NEW_TOKENS).issubset(set(parsed["last_dec_tokens"])):
        raise SystemExit("E_C2415_TOKEN_READBACK")
    before = len(state_io.read_raw(STATE))
    temp = STATE + ".tmp"
    _write(temp, text)
    os.replace(temp, STATE)
    after_text = state_io.decode(state_io.read_raw(STATE))
    if after_text != text:
        raise SystemExit("E_C2415_STATE_READBACK")
    if os.path.exists(temp):
        raise SystemExit("E_C2415_TEMP_RESIDUE")
    after = len(state_io.read_raw(STATE))
    print("state %dB -> %dB tick=%d log_items=%d tokens=%d layout_ok"
          % (before, after, ROUND, len(parsed["log"]),
             len(parsed["last_dec_tokens"])))
    return parsed


def step_export(state):
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
    results = [row for row in export["results"]
               if str(row[0]) != str(ROUND)]
    results.insert(0, [str(ROUND), EXPORT_DO])
    labelled = [row for row in results if len(row) >= 2 and row[1] == label]
    if not labelled:
        results.insert(0, [str(ROUND), label])
    else:
        for row in labelled:
            row[0] = str(ROUND)
    export["results"] = results
    outs = [item for item in export["outs"]
            if "publish-relative-package-identity" not in str(item)]
    outs.insert(0, EXPORT_ARTIFACT)
    export["outs"] = outs
    drive = export["self_drive"]
    import check_export_consistency
    derived = check_export_consistency.recompute()[0]
    drive["log_lines_in_window"] = derived["log_lines_in_window"]
    drive["substantive_non_idle_mention_lines"] = \
        derived["substantive_non_idle_mention_lines"]
    import queue_floor
    gauge = queue_floor.gauge(ROOT)
    fresh = {row["queue"]: row for row in gauge["queues"]}
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
    print("export refreshed %dB tick_rows=%d"
          % (len(text.encode("utf-8")), len(labelled) or 1))


def step_backlog():
    text = _read(BACKLOG)
    if BACKLOG_ROW in text:
        print("backlog row already present")
        return
    if not text.endswith("\n"):
        text += "\n"
    _write(BACKLOG, text + BACKLOG_ROW, newline="\n")
    print("backlog appended %dB" % len(BACKLOG_ROW.encode("utf-8")))


def step_heartbeat():
    line = ("2026-11-03T16:20:00+08:00 tick=2415 R2415 product window - "
            "publish_relative_package_identity ships the declared-package join "
            "for relative publish imports, suite 6/6 twice identical with "
            "three adjacent green, real src/os reads WIRE 11/1143 "
            "relative=0, one measured gap seeded")
    text = _read(HEARTBEAT)
    if line in text:
        print("heartbeat line already present")
        return
    if not text.endswith("\n"):
        text += "\n"
    _write(HEARTBEAT, text + line + "\n", newline="\n")
    print("heartbeat appended")


def main():
    step_debt()
    state = step_state()
    step_export(state)
    step_backlog()
    step_heartbeat()


if __name__ == "__main__":
    main()