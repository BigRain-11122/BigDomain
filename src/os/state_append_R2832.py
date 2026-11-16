"""R2832 closeout: append the window log rows and bump the tick.

The board head MAIN this window was "the durable guard the shape still
owed": R2831 repaired three live lines but shipped no detector, so the
only thing that asked the round-main shape was a ValueError raised at read
time - and it detected by crashing. This window ships the law as a library
function with its own gate and turns that crash into a stated code.
Writes through state_io.write_document, the canonical writer.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

STATE = os.path.join(HERE, "state.json")

ROWS = [
    "2026-11-16 R2832 PRODUCT+ENGINEERING: the round-main shape now has a "
    "detector that reddens instead of crashing, and the crash it replaced is "
    "closed as a named code. ledger_lines.check_round_main_shape() asks the law "
    "of the NEWEST round only - newest by round number, never by position - and "
    "returns a verdict with a code (E_RMS_NO_DATE / E_RMS_NO_ROUND), never an "
    "exception; the shipped CLI gained --round-main and reads exactly one line "
    "('ROUND-MAIN OK 2831' on the real tree, rc=0). AC-RMS1..AC-RMS6 were pinned "
    "in the R2832 backlog row BEFORE the code, and the pre-code control was "
    "measured: the same command read 'E_LGR_BAD_ARGS: unknown flag --round-main' "
    "rc=2. One wording was refined at code time and is stated rather than "
    "smoothed: the pinned text said the newest round's round line must match the "
    "dated shape, but a round legitimately writes undated sub-lines (disclosures, "
    "group scans, notes) under its dated main line, so the shipped law asks the "
    "round for AT LEAST ONE dated main line - any round with zero dated mains "
    "still reddens, so the measured R2831 failure (14 live lines, none anchored) "
    "is still caught, while a healthy tree no longer would be.",
    "2026-11-16 R2832 the crash class closed at its birth site: "
    "check_export_consistency.recompute() raised a bare "
    "ValueError('no date prefixes found in state log') when the live log lost its "
    "prefixes, and the three queue-face suites that import it died on a traceback "
    "instead of reading a verdict. It now raises AnchorError('E_EC_NO_DATE_ANCHOR') "
    "carrying the newest round number and the first 40 characters of that line, and "
    "check() turns it into ONE FAIL row naming the code and still counts it in "
    "n_fail, so the exit code is 2 - a shape failure of the log reported as a "
    "verdict. Measured both ways in a private world with the shipped functions "
    "stubbed: before, the failure escaped as an uncaught ValueError; after, "
    "check() returned FAIL anchor E_EC_NO_DATE_ANCHOR with n_fail=1.",
    "R2832 GROUP SCAN (content-addressed, read before any work): the shipped "
    "scanner read atbd_lines=0 unreplied_groups=0, so no @BigDomain ledger dispatch "
    "row is owed; the decisions face read rows=223 tokens=100 new=0, so no new "
    "decision arrived this window; the group orders tail is still the 2026-11-14 "
    "main-control block against the 01:3x baseline; benchmarks_refreshed 2026-11-16 "
    "sits inside the seven-day gate; git status was clean with no index.lock. Board "
    "head at open was the R2831 next-window item (1), the owed durable guard.",
    "R2832 regression read after the change, one batch: os-ledger-lines 8/8, "
    "os-ledger-line-shape-guard 6/6, os-export-consistency-queue-face 15/15, "
    "os-export-driver-queue-face 6/6, os-queue-floor-export-face 6/6, "
    "os-status-export-writer-dialect-wire 6/6, os-state-fold 6/6, "
    "check_export_consistency SUMMARY pass=21 fail=0 VERDICT PASS, "
    "os-queue-floor 8/8, os-queue-floor-decl 6/6 verdict=AGREES, and the new "
    "os-ledger-round-main-shape 6/6. Registry 700 suites / 5311 criteria (+1/+6), "
    "docs/sandbox-suite-matrix.md regenerated through the shipped --write face to "
    "73652B / 700 rows and re-read DOC-CURRENT under --check.",
    "R2832 honest disclosures: (a) ZERO new payment capability - a buyer still "
    "cannot pay, because no merchant id, server, domain, filing+ICP or miniprogram "
    "appid+secret has arrived; what this round bought is that a class of red which "
    "has already struck once (R2831) can no longer arrive as a traceback; (b) the "
    "guard was proven in a private world, not by breaking the real tree - the real "
    "tree reads OK 2831 and I deliberately did not strip a live prefix to watch it "
    "redden; (c) nothing yet CALLS --round-main from the closeout path, so a future "
    "window can still append an undated main line and only the suite will catch it "
    "next leg - wiring it into the append vehicle is carried, not done; (d) the "
    "suite's own read of the registry is a regex over reconcile_all.py, so a "
    "reformatting of SUITES could redden it cosmetically; (e) still owed: the os- "
    "family leg stands at 160 of 274 suites (114 unrun), 539 of 700 registry suites "
    "remain unrun, the shard offset/resume slice is still the named carrier blocker; "
    "(f) carried unchanged: outs as a 37-entry unmaintained list, 7 tool faces with "
    "no battery row, AC-VAC1..6, the AC-LKNF1 queue head, the R2778 stand on the "
    "Network Data Security Regulation, the 13 BOM-less UTF-16 evidence files, the "
    "dead src/os/export_R2431.py hook, the 18 BOM-carrying historical scripts, and "
    "the generic state appender this repo still lacks (this window used a per-round "
    "script, as its predecessors did); (g) tasks.md untouched - it is the P-47 "
    "canonical board; (h) Docker absent on this host; (i) BigDomain-OSLoop still "
    "reads InteractiveToken and needs an ELEVATED shell for its S4U re-registration.",
    "R2832 tokens: local=~26k api=0 api_reason=one five-silence scan through the "
    "shipped scanner, one board/state read, one ledger and one consistency module "
    "read at their birth sites, one pin row committed before any code, one pre-code "
    "control measured red, one library function plus one CLI gate, one named "
    "AnchorError replacing a bare ValueError with its FAIL row, one new suite at six "
    "criteria plus one registry row, two suite runs (one red on its own stderr "
    "assertion and repaired at the birth site), one ten-suite regression batch, one "
    "matrix regeneration and check, and the state/board/export closeout; zero cloud "
    "calls and zero external API touches",
]


def main():
    raw = state_io.read_raw(STATE)
    payload = state_io.parse(state_io.decode(raw))
    for row in ROWS:
        if row in payload["log"]:
            continue
        payload["log"].append(row)
    payload["tick"] = int(payload.get("tick", 0)) + 1
    result = state_io.write_document(STATE, payload)
    print("STATE tick=%d log=%d written=%dB" % (
        payload["tick"], len(payload["log"]), result["written"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
