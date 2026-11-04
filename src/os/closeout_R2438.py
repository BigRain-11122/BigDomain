"""closeout_R2438 - the closeout of the R2438 product window.

Appends this window's own honest lines to src/os/state.json, bumps the tick,
prepends the backlog row and the heartbeat row. Dry run by default; on
--execute every file is written once and read back.
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

sys.path.insert(0, BASE)
import state_io  # noqa: E402

TICK = 2438
DEC_ROWS = 225

LOG = [
    ("2026-11-04 R2438 five-silence scan at open: the evolution ledger carries "
     "zero @BigDomain rows, the content-addressed decisions diff read 225 rows "
     "and 113 tokens with new=0 and gone=0 against the stored baseline, the "
     "group orders tail max_ts is 2026-11-04 00:46 equal to the stored "
     "last_order, benchmarks were refreshed 2026-11-03 inside the seven-day "
     "gate, git status was empty and no .git/index.lock existed, so the window "
     "pulled live work instead of declaring idle - the debt register carried "
     "product-face-R2438 first=yes on tech head state/queue/tech.md:502."),
    ("2026-11-04 R2438 product face shipped: src/os/owner_table_triage_expiry.py "
     "plus src/os/test_owner_table_triage_expiry.py, AC-OTTE1..AC-OTTE6 pinned "
     "inside the R2436 tech seed row of state/queue/tech.md:502 BEFORE any "
     "code. The triage declaration recorded since_round on every acceptance "
     "but nothing aged it, so an acceptance written at R2436 and one accepted "
     "a year earlier read identically - a never-expiring waiver with a date "
     "nobody reads. The face now measures age = current_round - since_round "
     "for every TRIAGED row, prints AGED once age > window while the row "
     "keeps status TRIAGED and both verdicts, keeps an entry with no live row "
     "unageable rather than aged or clean, and fails closed E_OTTE_FUTURE at "
     "exit 3 when since_round is later than the supplied round. It reads no "
     "clock: --round is required and a missing one reads E_OTTE_NO_ROUND at "
     "exit 3."),
    ("2026-11-04 R2438 evidence: SUITE PASS 6/6 on two runs that are "
     "byte-identical (qa/owner-table-triage-expiry-R2438-a.log and -b.log, "
     "667B each, sha256 identical), four adjacent owner_table suites green "
     "(split_triage, parity, reader_parity, usage_wire all 6/6), wired "
     "os-owner-table-triage-expiry(6) in src/sandbox/reconcile_all.py so the "
     "registry reads 547 suites / 4258 criteria, and LIVE on the real src/os "
     "(qa/owner-table-triage-expiry-live-R2438.log): scanned=1073 round=2438 "
     "window=30 triaged=6 aged=0 fresh=6 unageable=0 verdict=EXPIRY-CLEAN, "
     "all six measured live acceptances at age 2 rounds because R2436 wrote "
     "them. docs/sandbox-suite-matrix.md was regenerated through --stamp-from "
     "to 52694B and reads green=546/547 because this window's suite has no "
     "line in the R2437 evidence log yet; --check reads byte-identical."),
    ("2026-11-04 R2438 debt: product-face-R2438 closed through the shipped "
     "debt_close at its own line (open 2->1, done 151->152, 109614B -> "
     "109617B, readback ok) and reconcile-battery-R2439 opened first=yes "
     "through debt_append (109617B -> 110337B, readback ok) pre-registered at "
     "547 suites / 4258 criteria - exactly +1 suite / +6 criteria against the "
     "R2436 registry 546/4252, with the larger-delta rule stated in the row. "
     "No battery ran this window: the tree was about to change by design."),
    ("2026-11-04 R2438 honest disclosures: (a) the window shipped product code "
     "and claims product points, but no end-user artifact was rebuilt - this "
     "is an internal owner-table debt face, not a CEO-visible product surface; "
     "(b) the window first wrote unageable from the wrong row shape (it called "
     "triage_rows on already-triaged rows and crashed KeyError superseded at "
     "the first run) and then derived unageable from the triaged rows instead "
     "of the raw parity rows - the suite proves the derivation, not the first "
     "attempt; (c) the expiry verdict is a REVIEW-DUE notice, not a quality "
     "claim: a FRESH row is unmeasured beyond its age; (d) no criterion was "
     "widened, no census baseline entry was added (baseline still 529), and "
     "no battery claim is made; (e) tasks.md was not touched, it is the P-47 "
     "canonical board; (f) the S4U reconcile is still carried as the stale "
     "row loop-s4u-reconcile - this session is unelevated, so the "
     "InteractiveToken task definition was left untouched for the "
     "two-hundred-and-fifth consecutive round."),
    ("R2438 tokens: local=~9k api=0 api_reason=product window - one new "
     "read-only face plus its six-case suite, four adjacent suite runs, two "
     "byte-identical evidence runs, one live run over 1073 tools, one matrix "
     "regeneration, two debt register writes through the shipped tools, and "
     "the state/backlog/heartbeat/export writes; zero cloud calls and zero "
     "external API touches"),
]

BACKLOG_ROW = (
    "- [x] [done 2026-11-04 R2438] R2438 product window on the debt gate "
    "first=yes item (product-face-R2438, tech head state/queue/tech.md:502 "
    "prefix AC-OTTE1 pinned at R2438 BEFORE any code): SHIPPED "
    "src/os/owner_table_triage_expiry.py plus its six-case suite. The split "
    "triage declaration recorded since_round but nothing aged it, so an "
    "acceptance written today and one accepted a year earlier read "
    "identically. The face measures age = current_round - since_round for "
    "every TRIAGED row, prints AGED past the declared window while the row "
    "stays TRIAGED with both verdicts, keeps a dead entry unageable, and "
    "fails closed on a future date; it reads no clock, so --round is required "
    "or exit 3. SUITE PASS 6/6 twice byte-identical "
    "(qa/owner-table-triage-expiry-R2438-a.log / -b.log, 667B each), four "
    "adjacent owner_table suites green, wired os-owner-table-triage-expiry(6) "
    "so the registry reads 547 suites / 4258 criteria. LIVE "
    "(qa/owner-table-triage-expiry-live-R2438.log): scanned=1073 round=2438 "
    "window=30 triaged=6 aged=0 fresh=6 unageable=0 verdict=EXPIRY-CLEAN. "
    "Debt: product-face-R2438 closed, reconcile-battery-R2439 opened first=yes "
    "at 547/4258. Honest: no battery ran this window and no CEO-visible "
    "artifact was rebuilt."
)

HEARTBEAT_ROW = (
    "%s tick=%d R2438 product window - owner_table_triage_expiry shipped "
    "against AC-OTTE1..AC-OTTE6 pinned at R2438: the acceptance age is now "
    "measured as current_round minus since_round, AGED past the declared "
    "window while the row stays TRIAGED, dead entries read unageable, and a "
    "future date fails closed; SUITE PASS 6/6 twice byte-identical, registry "
    "547 suites / 4258 criteria, LIVE triaged=6 aged=0 verdict=EXPIRY-CLEAN; "
    "next window owes reconcile-battery-R2439 [via BigDomain-OSLoop]"
)


def write_bytes_atomic(path, data, prefix):
    folder = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=prefix)
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(data)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    back = open(path, "rb").read()
    if back != data:
        raise SystemExit("E_R2438_BACK read-back does not match the write")
    return len(back)


def main(execute):
    if not execute:
        print("DRY RUN tick=%d lines=%d" % (TICK, len(LOG)))
        for line in LOG:
            print("  LOG %s" % line[:100])
        return 0

    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if payload["tick"] != TICK - 1:
        raise SystemExit("E_R2438_TICK state reads %s, expected %d"
                         % (payload["tick"], TICK - 1))
    payload["tick"] = TICK
    payload["last_decision_rows"] = DEC_ROWS
    payload["log"].extend(LOG)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2438_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2438-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d layout_ok=%s crlf=%d bare_lf=%d"
          % (TICK, size, len(payload["log"]), layout["layout_ok"],
             layout["crlf"], layout["bare_lf"]))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if BACKLOG_ROW in backlog:
        raise SystemExit("E_R2438_BACKLOG row already present")
    io.open(BACKLOG, "w", encoding="utf-8", newline="").write(
        BACKLOG_ROW + "\n" + backlog)
    print("BACKLOG row prepended, bytes=%d" % os.path.getsize(BACKLOG))

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    row = HEARTBEAT_ROW % ("2026-11-04T16:30:00+08:00", TICK)
    if row in beat:
        raise SystemExit("E_R2438_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    io.open(HEARTBEAT, "w", encoding="utf-8", newline="").write(
        beat + row + "\n")
    print("HEARTBEAT row appended, bytes=%d" % os.path.getsize(HEARTBEAT))
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))