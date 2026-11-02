"""R2393 closeout: append the round items, then fold whole blocks (R2393).

Layout canon is proven rather than assumed: the payload is serialised, passed
through state_io.canon (CRLF plus the 16-space item indent) and written with a
read-back that requires the JSON to be equal to the plan.

The fold moves the OLDEST WHOLE round blocks - a block being one or more items
that ends on its own ledger ("R<n> tokens:") line - so no round is ever split
between the live log and the archive (the open fold-block-boundary debt). Each
moved item is appended verbatim to the monthly archive and one summary line
takes its place; the summary is named "Fold R2393: ..." so it is NOT read as a
round narrative by the ledger law.

Stdlib only, ASCII source, no clock, no network.
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io as SIO  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
ARCHIVE = os.path.join(REPO, "logs", "state-log-archive-2026-11.md")
GATE = 78500
TARGET = 73500

DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\s+R(\d{3,5})\s")
TOKENS_RE = re.compile(r"^(?:\d{4}-\d{2}-\d{2}\s+)?R(\d{3,5}) tokens:")

ITEMS = [
    "2026-11-03 R2393 verification-then-product window (five-silence scan "
    "clean at open: empty git status at HEAD 3535cc1a, no .git/index.lock; "
    "LEDGER atbd_lines=0 unreplied_groups=0; DEC rows=131 tokens=86 new=0; "
    "the group orders tail 2026-11-02 11:04 already acknowledged as "
    "non-execution; benchmarks refreshed 2026-11-02 inside the seven-day "
    "gate; floor FLOOR-MET). The debt gate named CLAIM-FIRST "
    "item=reconcile-battery-R2387 carried=6 stale=yes, so the battery ran "
    "FIRST on the committed tree with zero product edits - and it earned its "
    "keep by naming two REAL birth-site defects nobody had touched. Both were "
    "repaired at their birth sites, committed ALONE as a9c946e7 before any "
    "product byte, and their gates then read clean.",

    "2026-11-03 R2393 repair one, measured not guessed: state.json carried "
    "the R2392 ledger item as \"2026-11-02 R2392 tokens: local=~38k ...\" "
    "while ledger_lines owns LEDGER_PREFIX_RE = ^R(\\d{3,5}) tokens:, so a "
    "ledger line may not carry a date prefix and round 2392 read "
    "rounds_without_ledger - four ledger suites and the closeout station went "
    "red on a tree nobody had edited. Repaired surgically: the 11-byte prefix "
    "removed from that ONE item, 80756B -> 80745B exactly predicted, CRLF "
    "count unchanged at 165, JSON payload proven equal to the plan, no temp "
    "residue; ledger_lines now reads VERDICT CLEAN with new_missing none. "
    "Repair two: qa/repin-noop-eol-dialect-live-R2388.log was written with a "
    "child CLI stdout embedded verbatim, so it carried 1 CRLF, 4 LF and 1 "
    "bare CR and the census flagged it new-dialect (class=other); normalised "
    "through run_identity.normalize (537B -> 536B predicted and measured, "
    "payload line set equal, crlf 0, bare_cr 0) and the census then read "
    "DRIFT-CLEAN flags=0 with its baseline UNTOUCHED - no waiver was added.",

    "2026-11-03 R2393 export re-derivation after the repair, measured: "
    "check_export_consistency read FAIL self_drive.log_lines_in_window stored=8 "
    "recomputed=7, because the counter counts state log items carrying a date "
    "prefix and the repaired item no longer does. The stored digit was "
    "re-written from the checker own recompute() through "
    "src/os/refresh_export_R2393.py (surgical in-place digit, 50306B before "
    "and after, every other byte kept, read-back proven) and the face then "
    "read 21/21 PASS.",

    "2026-11-03 R2393 PRODUCT: claimed state/queue/tech.md:451 prefix "
    "AC-RCDF1 (refused_check_declaration_face), criteria pinned in that row "
    "at R2392 BEFORE any code. SHIPPED src/os/refused_check_declaration_face.py "
    "plus src/os/test_refused_check_declaration_face.py: the refused --check "
    "carried the asked round live status but still answered declared_by=\"-\" "
    "while its own detail line named the boundary, so the payload and the "
    "prose disagreed. One derivation now reads the declaration own "
    "declared_by through residue_triage.load_declaration at call time and "
    "ages NOTHING (the live residue is never read there), so a declaration "
    "whose entries would raise another triage code cannot move the refusal "
    "code; residue_triage_append carries it on the refused payload. SUITE "
    "PASS 6/6, two legs identical digest A2958D41F7D143ED, three adjacent "
    "suites green (residue_triage_append 6/6, "
    "append_check_status_precedence 6/6, residue_triage 6/6), wired "
    "os-refused-check-declaration-face(6). LIVE, not a plan: --check --round "
    "R1755 --json now reads declared_by=\"R2391\" at exit 3 with the same "
    "E_RTA_UNREADABLE, where R2392 measured \"-\" (qa/"
    "refused-check-declaration-face-live-R2393.log, 1325B evidence). Board: "
    "row 451 stamped and two REAL measured gap rows seeded (runner_suite_"
    "timeout_headroom AC-RTH1..AC-RTH6 and ledger_line_shape_guard "
    "AC-LLSG1..AC-LLSG6), so the floor reads FLOOR-MET main 5/5 tech 11/10 "
    "explore 10/10.",

    "2026-11-03 R2393 battery carried, measured leg by leg, zero green claim: "
    "leg 1 qa/reconcile-all-R2393.log read 514/519 suites with 6 failed "
    "assertions (the two repaired defects); leg 2 "
    "qa/reconcile-all-R2393-retry.log read 518/519 with the ONLY red being "
    "the stale derived counter, now re-derived, and its two export suites "
    "re-ran 6/6 each; leg 3 qa/reconcile-all-R2393-retry2.log aborted on the "
    "runner per-suite 300s cap in ledger/test_apimarket_report_claims.py, "
    "which MEASURED 183.3s and 194.9s in the two earlier legs - a load "
    "artefact of a busy machine, not a code defect, and now its own seed row. "
    "No RUNNER PASS exists for this tree, so reconcile-battery-R2387 stays "
    "OPEN with the successor target 521 suites / 4102 criteria, and the "
    "R2392 row stays open as the same obligation.",

    "2026-11-03 R2393 self-heal check: BigDomain-OSLoop is still registered "
    "with LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; the registration script already passes an "
    "explicit S4U principal but needs an elevated shell and this session is "
    "unelevated, so the task definition was left untouched (hundred-and-"
    "forty-eighth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md).",

    "R2393 tokens: local=~96k api=0 api_reason=verification-then-product "
    "window dominated by three full battery legs (leg 1 red on two real "
    "birth-site defects, leg 2 red only on a derived counter, leg 3 aborted "
    "on the per-suite 300s cap under other companies load), two birth-site "
    "repairs with predicted deltas, one export re-derivation from the checker "
    "own recomputation, one product module and its six-criteria suite written "
    "to criteria pinned one round earlier, one registry wiring line, one "
    "two-leg evidence capture with three adjacent suites, one live capture "
    "through a single utf-8 LF writer, one board stamp with two measured gap "
    "rows seeded, two register rows updated without inventing a key, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]


def write_state(payload):
    text = json.dumps(payload, ensure_ascii=True, indent=2)
    text = SIO.canon(text)
    temp = STATE + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(temp, STATE)
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        written = handle.read()
    if json.loads(written) != payload:
        raise SystemExit("REFUSED: the state write moved the payload")
    return len(written.encode("utf-8"))


def block_windows(log):
    """Index just past each whole round block (a tokens line closes one)."""
    out = []
    for index, item in enumerate(log):
        if TOKENS_RE.match(item):
            out.append(index + 1)
    return out


def main(argv):
    dry = "--execute" not in argv
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        payload = json.load(handle)
    before_bytes = len(io.open(STATE, encoding="utf-8", newline="")
                      .read().encode("utf-8"))
    log = list(payload["log"])
    payload["tick"] = 2393
    payload["log"] = log + list(ITEMS)
    print("tick=%d log %d -> %d items, before_bytes=%d"
          % (payload["tick"], len(log), len(payload["log"]), before_bytes),
          flush=True)
    if dry:
        print("DRY: no byte written", flush=True)
        return 0
    size = write_state(payload)
    print("after append: %d bytes (gate %d)" % (size, GATE), flush=True)

    if size > GATE:
        # pick a whole-block window whose removal lands under TARGET
        windows = block_windows(payload["log"])
        chosen = None
        for cut in windows:
            removed = sum(len(item.encode("utf-8")) + 22
                          for item in payload["log"][:cut])
            summary_len = 200
            if size - removed + summary_len <= TARGET:
                chosen = cut
                break
        if chosen is None:
            raise SystemExit("REFUSED: no whole-block window reaches the "
                             "target; refusing rather than splitting a round")
        moved = payload["log"][:chosen]
        rest = payload["log"][chosen:]
        rounds = []
        for item in moved:
            match = TOKENS_RE.match(item)
            if match:
                rounds.append("R%s" % match.group(1))
        summary = ('Fold R2393: %d log items (rounds %s) moved verbatim into '
                   'logs/state-log-archive-2026-11.md; every round block moved '
                   'whole, ending on its own ledger line.'
                   % (len(moved), ",".join(rounds)))
        with io.open(ARCHIVE, "a", encoding="utf-8", newline="\n") as handle:
            handle.write("\n## Fold R2393\n")
            for item in moved:
                handle.write(item + "\n")
        payload["log"] = [summary] + rest
        size_after = write_state(payload)
        print("after fold: %d bytes, moved=%d rounds=%s"
              % (size_after, len(moved), ",".join(rounds)), flush=True)
        if size_after > GATE:
            raise SystemExit("REFUSED: still above the gate")

    check = SIO.report(STATE)
    print("layout crlf=%d bare_lf=%d off_indent=%d ok=%s"
          % (check["crlf"], check["bare_lf"], check["items_off_indent"],
             check["layout_ok"]), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))