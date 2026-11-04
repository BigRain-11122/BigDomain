"""R2437 closeout: the state append, the backlog row and the heartbeat row.

This window ADOPTED a R2437 battery that a crashed window had already run to a
finished verdict: the evidence log, the regenerated matrix and the debt rows
were on disk while state.json still read tick 2436 and no closeout byte had been
written. Every claim below was re-measured on the working tree before it was
recorded; nothing is copied from the dead window's intent.

Ordering is the law the R2433 red taught: the state append runs FIRST, and the
export refresh (export_R2437.main) runs only after it, because a self_drive
count sampled before its own append is stale the moment the append lands.

The state file is written through state_io.canon, the shipped layout law, so the
CRLF / two-space top level / sixteen-space log item canon cannot drift; the
pipeline was first proved to reproduce the live file byte for byte.
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(BASE, "state.json")
BACKLOG = os.path.join(BASE, "backlog.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")

sys.path.insert(0, BASE)
import state_io  # noqa: E402

TICK = 2437
NOW = "2026-11-04T16:00:00+08:00"

LOG = [
    ("2026-11-04 R2437 an ADOPTED window, disclosed rather than dressed up: "
     "the round opened on a DIRTY tree at HEAD f12e2add carrying untracked "
     "qa/reconcile-all-R2437.log (850070B, last written 10:47:25) plus "
     "modified docs/sandbox-suite-matrix.md and state/debt.md, while "
     "src/os/state.json still read tick 2436 and the export still carried its "
     "10:17:33 stamp - so a R2437 window had run the battery to a FINISHED "
     "verdict and died before any closeout byte was written. Nothing was "
     "accepted on trust: the log was measured to carry RUNNER PASS (546/546 "
     "suites green, reconcile controls 7/7, 981.2s) with 'expected criteria "
     "total=4252', which is exactly the target pre-registered at the R2436 "
     "closeout, the designed matrix FAIL on the stale 52596B doc followed by "
     "its regeneration and VERDICT R2437 PASS failing=none with SECTION "
     "fingerprint CLEAN domains=5 / profile byte-identical / census "
     "DRIFT-CLEAN, and suite_matrix --check re-read on this working tree "
     "answers byte-identical 52591B / 546 suites / 4252 criteria at exit 0. "
     "Adoption was gated on liveness, not optimism: no battery python process "
     "was alive and no .git/index.lock existed."),
    ("2026-11-04 R2437 five-silence scan at open: the content-addressed "
     "decisions diff read 225 rows and 113 tokens with new=0 and gone=0 "
     "against the stored 113-token baseline, the group orders tail max_ts is "
     "2026-11-04 00:46, equal to the stored last_order, so nothing dispatches "
     "this company, benchmarks were refreshed 2026-11-03 inside the seven-day "
     "gate, the evolution ledger carries zero @BigDomain rows, and the queue "
     "gauge reads FLOOR-MET main 5/5 tech 10/10 explore 10/10."),
    ("2026-11-04 R2437 BIRTH-SITE repair of the debt register, disclosed: the "
     "crashed window had opened a successor row named reconcile-battery-R2437 "
     "carrying the SAME 546 suites / 4252 criteria target as the battery it "
     "had just closed, which would have spent the next window re-walking an "
     "unchanged tree and produced no product for the second window running. "
     "This window changed no product src byte, so no successor battery is "
     "owed; that row was converted IN PLACE at its own position (the register "
     "stays at exactly one first=yes and its dialect untouched) into "
     "product-face-R2438, naming the tech head state/queue/tech.md:502 "
     "src/os/owner_table_triage_expiry.py - the declaration records "
     "since_round on every entry but nothing ages it, so an acceptance from "
     "today and one accepted a year earlier read identically. The register now "
     "reads open=2 done=151 with one open first=yes row."),
    ("2026-11-04 R2437 honest disclosures: (a) this window shipped ZERO "
     "product code and claims zero product points - its work was verification "
     "proof plus a register repair; (b) the largest single fact of this "
     "window is that a PREVIOUS window's evidence was adopted rather than "
     "re-run, so the honest statement is 'measured and verified', not 'run by "
     "me', and the distinction is stated here rather than smoothed over; (c) "
     "no criterion was widened, no census baseline entry was added, the "
     "baseline still reads 529 and the census read DRIFT-CLEAN on its own; "
     "(d) tasks.md was not touched, it is the P-47 canonical board and "
     "carries no row for a verification window; (e) the dead window's own "
     "log line was never written, so the R2437 record in state.json begins "
     "with this line and nothing before it is reconstructed from memory."),
    ("R2437 tokens: local=~6k api=0 api_reason=verification window - the "
     "crashed window's battery evidence re-measured on the working tree "
     "(verdict, criteria total, matrix byte-identity, census, fingerprint, "
     "profile) rather than re-run, one birth-site repair of a self-referential "
     "successor battery row in the debt register, one adopted closeout through "
     "the canonical state writer with a byte-exact round trip proved first, and "
     "the state/backlog/heartbeat/export writes; zero product code shipped, "
     "zero cloud calls and zero external API touches"),
    ("2026-11-04 R2437 self-heal check: BigDomain-OSLoop still exists and its "
     "Principal.LogonType reads InteractiveToken, which the 2026-09-29 machine "
     "law forbids for every lane task; src/os/register_loop_task.ps1 passes an "
     "explicit S4U principal and needs an elevated shell while this session is "
     "unelevated, so the definition was left untouched again (two-hundred-and-"
     "fourth consecutive disclosure, carried as the stale row "
     "loop-s4u-reconcile)."),
]

BACKLOG_ROW = (
    "- [x] [done 2026-11-04 R2437] R2437 verification window, ADOPTED and "
    "disclosed: a crashed R2437 window had already run the battery on the "
    "committed R2436 tree to RUNNER PASS 546/546 suites at exactly the "
    "pre-registered 4252 criteria and regenerated the matrix to 52591B with "
    "an at-open suite_matrix --check reading byte-identical at exit 0, while "
    "state/export/backlog were never written; the evidence was re-measured "
    "here (not re-run) and no live writer held the tree. Also repaired at its "
    "birth site a self-referential successor row the dead window had written "
    "(reconcile-battery-R2437 pointing at the same target as the battery it "
    "just closed, which would have spent the next window re-walking an "
    "unchanged tree); the register now carries product-face-R2438 first=yes "
    "on tech head state/queue/tech.md:502 owner_table_triage_expiry.py. Zero "
    "product code, zero product points."
)

HEARTBEAT_ROW = (
    "%s tick=%d R2437 verification window (ADOPTED, disclosed) - a crashed "
    "window had already run the battery on the committed R2436 tree to RUNNER "
    "PASS 546/546 suites at exactly the pre-registered 4252 criteria, "
    "regenerated the matrix to 52591B and closed reconcile-battery-R2436, but "
    "wrote no state/export/backlog byte; this window re-measured every claim on "
    "the working tree instead of re-running it, repaired at birth the "
    "self-referential successor row the dead window left (product-face-R2438 "
    "now names tech head state/queue/tech.md:502 owner_table_triage_expiry), "
    "and completed the closeout through the canonical state writer with a "
    "byte-exact round trip proved first; registry unchanged at 546 suites / "
    "4252 criteria, zero product points claimed" % (NOW, TICK)
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
        raise SystemExit("E_R2437_BACK read-back does not match the write")
    return len(back)


def main():
    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if payload["tick"] != TICK - 1:
        raise SystemExit("E_R2437_TICK state reads %s, expected %d"
                         % (payload["tick"], TICK - 1))
    payload["tick"] = TICK
    payload["last_decision_rows"] = 225
    payload["log"].extend(LOG)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2437_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2437-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d layout_ok=%s crlf=%d bare_lf=%d"
          % (TICK, size, len(payload["log"]), layout["layout_ok"],
             layout["crlf"], layout["bare_lf"]))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if BACKLOG_ROW in backlog:
        raise SystemExit("E_R2437_BACKLOG row already present")
    io.open(BACKLOG, "w", encoding="utf-8", newline="").write(
        BACKLOG_ROW + "\n" + backlog)
    print("BACKLOG row prepended, bytes=%d"
          % os.path.getsize(BACKLOG))

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    if HEARTBEAT_ROW in beat:
        raise SystemExit("E_R2437_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    io.open(HEARTBEAT, "w", encoding="utf-8", newline="").write(
        beat + HEARTBEAT_ROW + "\n")
    print("HEARTBEAT row appended, bytes=%d"
          % os.path.getsize(HEARTBEAT))
    return 0


if __name__ == "__main__":
    sys.exit(main())