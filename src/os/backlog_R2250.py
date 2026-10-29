# backlog_R2250.py - closeout writer for the R2250 window.
# Touches only the four bookkeeping faces and never re-serialises a file it
# does not have to: the queue row advances in place, backlog.md gains one
# done row at the top, state/debt.md gets the battery row that this window
# opens, and state.json takes the tick plus three log lines at the tail of
# its log array (payload edited, layout left exactly as it sits on disk).
import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
QUEUE = os.path.join(ROOT, "state", "queue", "tech.md")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
DEBT = os.path.join(ROOT, "state", "debt.md")
STATE = os.path.join(ROOT, "src", "os", "state.json")

ROUND = "R2250"
TICK = 2250

DELIVERY = (
    " [done 2026-10-29 R2250] delivered: src/os/export_freshness.py - the "
    "time axis of the CEO-visible face as a reading. assess() judges only "
    "what no other checker did: age against the 24h freshness gate and the "
    "announced milestone against the 48h window, with the clock injected by "
    "the caller so a reading is reproducible. Four exhaustive verdicts "
    "(FRESH / STALE-FACE / STALE-WINDOW / UNVERIFIABLE-WINDOW); a face that "
    "publishes no next_milestone_due reads as an honest unknown with its own "
    "exit code rather than as a fabricated pass. Shape and derivation stay "
    "with check_export_consistency, so this window added no second wheel: "
    "the consistency checker was re-run green (exit 0) after the change. "
    "Stamps without a UTC offset are refused (E_EXP_BAD_TS) instead of "
    "assumed local, because the face is written by different writers across "
    "the day. Evidence: SUITE PASS 6/6 double-run byte-identical criterion "
    "sha16 6B9DC44593508471 (qa/export-freshness-R2250-a.log / -b.log, 466B "
    "each, single writer utf-8 LF through src/os/evidence_R2250.py, never a "
    "shell redirection), five adjacent os suites green (qa/"
    "regression-R2250.log, 4878B); wired os-export-freshness(6) in "
    "src/sandbox/reconcile_all.py. Live reading at the R2249 face was "
    "verdict=UNVERIFIABLE-WINDOW age=0.3h (no due stamp published); this "
    "window's export refresh publishes next_milestone_due so the gate now "
    "reads FRESH. Honest debt: the full reconcile battery and the "
    "suite-matrix regeneration are the R2251 first item (the R2168 "
    "mixed-tree rule) and are registered in state/debt.md."
)

BACKLOG_ROW = (
    "- [x] [done 2026-10-29 R2250] P2 tech head claim (R2240 d seed; criteria "
    "AC-EXP1..AC-EXP6 were pre-registered in that queue row BEFORE the code; "
    "anchor check at HEAD 2026-10-29: export_freshness, "
    "check_export_freshness, test_export_freshness, ledger-export-freshness "
    "and os-export-freshness were git grep -F zero-occupancy rc=1, while the "
    "AC-EXP prefix appears only in qa evidence of an unrelated "
    "export-persist suite and the delivered block above discloses every "
    "criterion as written to the pre-registered intent):" + DELIVERY + "\n"
)

DEBT_ROW = (
    "- [ ] opened=R2250 | item=reconcile-battery-and-matrix | "
    "note=R2250 changed src/os (export_freshness.py, "
    "test_export_freshness.py, evidence_R2250.py), src/sandbox/reconcile_all.py "
    "and two queue files; the battery and the matrix regeneration must run on "
    "the committed tree (the R2168 mixed-tree rule) | first=yes\n"
)

SELF_HEAL = (
    "%s self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply it, and "
    "this session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(twentieth consecutive disclosure, registered as the stale row "
    "loop-s4u-reconcile in state/debt.md)." % ROUND
)

LOG_LINES = [
    "2026-10-29 R2250 (five-silence scan clean at open: decisions.md carries "
    "283 non-empty rows and 190 content-addressed D/C tokens with ZERO "
    "additions against the stored 190-token baseline, so zero domain action; "
    "the group ledger holds the same three @BigDomain patrol rows already "
    "paid off with zero unreplied; the group orders tail is unchanged at the "
    "2026-10-29 02:1x CEO-PROXY event round R2.48 already consumed in R2226; "
    "benchmarks refreshed 2026-10-29 inside the seven-day gate; tree clean, "
    "no index.lock) - the P1 canonical rows stay blocked-on-CEO, the weekly "
    "proposal duty is met by BD-PROP-005, the queue gauge read main 5/5 "
    "tech 10/10 explore 10/10 FLOOR-MET, so this window claimed the P2 tech "
    "head. Product: src/os/export_freshness.py, the time gate the R2240-d "
    "seed asked for. Pain: docs/status-export.json is the only surface the "
    "CEO reads, and the round book requires three lines with a milestone "
    "inside 48h, but every existing check was about shape and derivation - a "
    "perfectly shaped face two days old passed, and so did a milestone "
    "announced three weeks out. The new module judges only time: the age "
    "against a 24h gate and the announced milestone against a 48h window, "
    "with the clock injected so a reading is reproducible and a missing due "
    "stamp reported as an honest unknown (exit 4) instead of a fabricated "
    "pass. Verdicts are four and exhaustive, stamps without a UTC offset are "
    "refused rather than assumed local, and check_export_consistency keeps "
    "shape and derivation so the two checkers are complements. Disclosed "
    "overlap: AC-EXP1's three-line contract is read here too, but this "
    "module adds the window judgement that the consistency checker does not "
    "make. First suite run was green 6/6, evidence double-run byte-identical "
    "sha16 6B9DC44593508471, five adjacent os suites green, consistency "
    "checker re-run exit 0 after the change.",
    "%s tokens: local=~22k api=0 api_reason=product window on the P2 tech head "
    "- one time-gate module with its six pre-registered criteria, one "
    "single-writer double-run evidence pair, five adjacent os regressions, one "
    "consistency re-run proving no second wheel, one runner wiring line, and "
    "the queue/backlog/debt/state/export closeout; zero cloud calls and zero "
    "external API touches; the reconcile battery and the matrix regeneration "
    "are deferred to R2251 and registered in state/debt.md" % ROUND,
    SELF_HEAL,
]


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def claim_queue_row():
    text = read_text(QUEUE)
    marker = "- [ ] P2 tech seed (R2240 d): status-export freshness gate"
    if text.count(marker) != 1:
        raise SystemExit("queue anchor not unique (%d)" % text.count(marker))
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if line.startswith(marker):
            lines[index] = ("- [x] [done 2026-10-29 R2250] P2 tech head claim "
                            "(R2240 d seed): status-export freshness gate"
                            + line[len(marker):] + DELIVERY)
            break
    write_text(QUEUE, "\n".join(lines))
    return "queue row claimed"


def prepend_backlog():
    text = read_text(BACKLOG)
    write_text(BACKLOG, BACKLOG_ROW + text)
    return "backlog row prepended"


def open_debt_rows():
    text = read_text(DEBT)
    old = ("note=BigDomain-OSLoop principal reads InteractiveToken, which the "
           "2026-09-29 machine law forbids for lane tasks; repair needs an "
           "elevated shell (nineteenth consecutive disclosure at R2249) | "
           "first=no")
    new = ("note=BigDomain-OSLoop principal reads InteractiveToken, which the "
           "2026-09-29 machine law forbids for lane tasks; repair needs an "
           "elevated shell (twentieth consecutive disclosure at R2250) | "
           "first=no")
    if text.count(old) != 1:
        raise SystemExit("debt anchor not unique (%d)" % text.count(old))
    text = text.replace(old, new, 1)
    marker = "## Open\n\n"
    if text.count(marker) != 1:
        raise SystemExit("debt open-section anchor not unique")
    text = text.replace(marker, marker + DEBT_ROW, 1)
    write_text(DEBT, text)
    return "debt row opened"


def advance_state():
    text = read_text(STATE)
    eol = "\r\n" if "\r\n" in text else "\n"
    tick_old = '"tick": %d,' % (TICK - 1)
    if text.count(tick_old) != 1:
        raise SystemExit("tick anchor not unique (%d)" % text.count(tick_old))
    text = text.replace(tick_old, '"tick": %d,' % TICK, 1)
    indent = " " * 16
    tail = eol + "  ]" + eol + "}"
    if text.count(tail) != 1:
        raise SystemExit("log tail anchor not unique (%d)" % text.count(tail))
    block = ""
    for line in LOG_LINES:
        block += "," + eol + indent + json.dumps(line, ensure_ascii=True)
    text = text.replace(tail, block + tail, 1)
    payload = json.loads(text)
    assert payload["tick"] == TICK
    assert payload["log"][-1] == SELF_HEAL
    write_text(STATE, text)
    return "state tick=%d log=%d bytes=%d" % (TICK, len(payload["log"]),
                                              len(text.encode("utf-8")))


def main():
    print(claim_queue_row())
    print(prepend_backlog())
    print(open_debt_rows())
    print(advance_state())
    return 0


if __name__ == "__main__":
    sys.exit(main())