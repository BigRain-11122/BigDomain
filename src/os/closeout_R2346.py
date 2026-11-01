"""closeout_R2346 - append this window round to state.json (R2346).

The figures written here are the ones measured this window, not estimates: the
battery verdict and its pre-registered target, the product face and its
evidence, the queue claim and its refill, the register close and the successor
row it opened, and the live read-only reading of the real declaration.

State text is edited in place on its own canon (CRLF, 16-space log items) and
then passed through state_io.canon with a read-back proof. Dry run by default;
--execute writes. Pure ASCII source, stdlib only.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
EVIDENCE = os.path.join(ROOT, "qa", "stamp-exempt-guard-R2346.log")
BATTERY = os.path.join(ROOT, "qa", "reconcile-all-R2346.log")

TICK = 2346
STAMP = "2026-11-01T21:37:57+08:00"
HEARTBEAT_LINE = (
    "R2346: battery on the committed R2345 tree read RUNNER PASS 480/480 "
    "suites plus controls 7/7 in 875.4s with criteria total 3856 exactly as "
    "pre-registered, four follow-up sections PASS after the designed matrix "
    "FAIL and its regeneration to 45956B; then stamp_exempt_guard shipped - "
    "a plan pins the digest it read, an execute refuses E_SEG_STALE before "
    "any byte, and both declaration writers now share that one callable, "
    "suite 6/6 twice identical, live declaration pins at 397D3C1C71E149DB "
    "over 79026 bytes with the prune dry run carrying the same digest\n"
)

sys.path.insert(0, BASE)
import state_io as SIO  # noqa: E402


ROUND_LINE = (
    "2026-11-01 R2346 verification-then-product window (five-silence scan "
    "clean at open: empty git status --short and no .git/index.lock; BOTH "
    "decision readers agree on zero new rows over 65 live tokens - the python "
    "twin reads DEC rows=101 tokens=65 new=0 and the PowerShell gate reads "
    "PASS rows=134 known_tokens=65 row_owner_tokens=54; the evolution ledger "
    "reads atbd_lines=0 unreplied_groups=0; the group orders tail is unchanged "
    "at the 2026-11-01 10:4x baseline already acked as non-execution; "
    "benchmarks refreshed 2026-11-01, inside the seven-day gate). FIRST ITEM, "
    "the debt gate carried: THE BATTERY ON THE COMMITTED R2345 TREE 47712e43 "
    "with an empty git status before the run (the R2168 mixed-tree rule) and "
    "the census re-read first as DRIFT-CLEAN at files=2315 tee=1786 "
    "baselined=529 flags=0, pre-registered at 480 suites / 3856 criteria - "
    "exactly +1 suite / +6 criteria against R2344 (479/3850) from the new "
    "os-review-window-history suite. MEASURED: RUNNER PASS 480/480 suites "
    "green plus controls 7/7 in 875.4s with birth-site TMP RECLAIM 932/932 "
    "worlds 326.59 MiB busy=0 failed=0 (qa/reconcile-all-R2346.log, 794072B, "
    "single writer utf-8 LF through src/os/battery_stream.py), criteria total "
    "3856 - the prediction matched the measurement with no correction and no "
    "swept delta. Four follow-up sections through src/os/battery_followup.py "
    "ran in their pinned order: matrix FAILED first on the stale shipped doc "
    "(on-disk=45769B regenerated=45956B) and did NOT rewrite it, which is the "
    "designed order; src/sandbox/suite_matrix.py then regenerated "
    "docs/sandbox-suite-matrix.md to 480 suites / 3856 criteria (45956B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN "
    "5 domains, profile --daily --check byte-identical, census DRIFT-CLEAN), "
    "closing VERDICT R2346 PASS. PRODUCT: claimed the queue head the reader "
    "named, state/queue/tech.md:392 prefix AC-SEG1 (stamp_exempt_guard), whose "
    "AC-SEG1..AC-SEG6 were pinned INSIDE that row at R2329 BEFORE any code. "
    "The row own zero-occupancy claim was RE-MEASURED at HEAD instead of "
    "trusted: the five names hit ten paths and every one is prose or state "
    "(src/os/backlog.md, src/os/export_lines_R2329.json, "
    "src/os/state_close_R2329.py, src/os/state.json, state/queue/tech.md), "
    "with ZERO executable occupancy. DELIVERED src/os/stamp_exempt_guard.py "
    "plus src/os/test_stamp_exempt_guard.py: pin(text) is the digest and byte "
    "count a plan records; commit(path, pin, payload) re-reads the file, "
    "refuses E_SEG_STALE when the digest moved and does so BEFORE creating a "
    "temp file, then performs the single atomic replace with its read-back and "
    "a residue proof; an unpinned commit refuses rather than writing blind. "
    "Both writers now import that one callable - SEPA.SEG is SPR.SEG, neither "
    "writer carries an os.replace call of its own any more, and an executed "
    "append and an executed prune each route through the same function object "
    "(the suite proves all three by identity, by source and by a patched "
    "counter). Their plans now also carry source_digest and source_bytes. "
    "SUITE PASS 6/6 twice with identical legs through evidence_capture "
    "(qa/stamp-exempt-guard-R2346.log, 2198B, single utf-8 LF writer) with "
    "three adjacent suites green (stamp_exempt_append 6/6, "
    "stamp_exempt_prune 6/6, stamp_exempt_review), wired "
    "os-stamp-exempt-guard(6). LIVE read-only reading, not a plan: the real "
    "declaration state/queue/stamp_exempt.json pins at digest "
    "397D3C1C71E149DB over 79026 bytes, SEG.read_pin agrees with SEG.pin, the "
    "prune dry run carries the SAME digest (verdict=PLAN retire=1 wrote=no) "
    "and the file was proven byte-untouched. Board: the claim closed the row "
    "and one real gap row was seeded (stamp_exempt_seed_guard_wire, "
    "AC-SGS1..AC-SGS6 pre-registered) from a measured finding - the R2280 seed "
    "generator is the THIRD writer of that declaration and still writes it "
    "straight through one io.open(path, w) with no pin, no digest and no "
    "atomic replace, so the guard now covers two of three writers; FLOOR-MET "
    "5/5 10/10 10/10 and the head moved to tech.md:393 AC-RAP1."
)

TOKENS_LINE = (
    "R2346 tokens: local=~30k api=0 api_reason=verification-then-product "
    "window - one full reconcile battery (480 suites, 3856 criteria, 875.4s) "
    "with its streamed evidence file, one four-section follow-up run plus one "
    "matrix regeneration and the closing re-run, one guard module with its six "
    "pre-registered criteria and its suite (green on the fourth run after this "
    "window own fixture permutations were corrected, the criteria never "
    "widened), one dogfooded evidence capture with three adjacent suites, one "
    "live read-only reading of the real declaration, one runner wiring line, "
    "one queue close with one real gap row seeded, one debt row closed and one "
    "successor opened, and the state/export/heartbeat/board closeout; zero "
    "cloud calls and zero external API touches"
)

SELF_HEAL = (
    "R2346 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(hundred-and-sixth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

DECISION_LINE = (
    "R2346 decision gate (D-20260930-19 step 2): the content-addressed diff of "
    "the group decisions.md against the stored baseline read NO new tokens, "
    "confirmed by BOTH readers after the R2344 repair (python twin: DEC "
    "rows=101 tokens=65 new=0; PowerShell gate: DEC PASS rows=134 "
    "known_tokens=65 row_owner_tokens=54), and the evolution ledger carries no "
    "@BigDomain row, so nothing was executed, rejected or acknowledged this "
    "window and the baseline is unchanged."
)

DISCLOSURES = (
    "R2346 honest disclosures: (a) the first battery launch was piped through "
    "a truncating selector, produced no output for five minutes and was "
    "cancelled by the shell guard; the surviving python processes were "
    "inspected by command line and NONE of them was the battery, and no "
    "evidence file existed, so nothing is claimed from the dead run (the R2211 "
    "and R2343 trap re-proven for the third time, and the rerun was done "
    "without a pipe). (b) An earlier probe ran reconcile_all.py with --help, "
    "which the runner does not support: it wrote a stray untracked file named "
    "'--help' (13859B) in the repo root, which was deleted before anything "
    "was committed - disclosed rather than silently swept. (c) The guard suite "
    "was red twice before green and BOTH reds were this window own fixtures: "
    "AC-SEG5 first counted an 'os.replace' inside each writer's COMMENT as a "
    "copied call, so the check now ignores comment lines and the two comments "
    "were reworded to name the guard; AC-SEG6 first banned the bare token "
    "'socket' and tripped on this module's own docstring sentence 'opens no "
    "socket', so the docstring was reworded. No criterion was widened: the "
    "identity, source and counter assertions AC-SEG5 makes are unchanged. (d) "
    "AC-SEG5's prune leg is proved by EXECUTING a real prune in a fixture world "
    "with a patched commit counter, not by reading the source alone, and the "
    "fresh-names anchor check behind it was re-measured (all five names hit "
    "prose and state only). (e) The stale refusal is proven on two routes: "
    "through the writer, by handing it a plan pinned at T0 after the file "
    "moved at T1, and straight at commit with a pin that no longer matches; an "
    "empty pin also refuses, because a commit without a pin is exactly the "
    "defect this face exists to prevent. (f) One writer suite needed a fixture "
    "line, not a criterion change: AC-SAP6's import allowlist bans unknown "
    "modules and this window's legitimate new house import "
    "(stamp_exempt_guard) was added to it with the reason spelled out in "
    "place. (g) tasks.md was left untouched: it is the P-47 canonical board "
    "and carries no row for this tech slice, disclosed rather than silently "
    "skipped. (h) state.json measured 71480B at open and needs no fold; this "
    "closeout appends five items to a 71480B file, well under the 78500B gate."
)


def items():
    return [ROUND_LINE, TOKENS_LINE, SELF_HEAL, DECISION_LINE, DISCLOSURES]


def bump(text):
    """Edit the live state text in place: tick, then five log items appended."""
    old_tick = '"tick": %d,' % (TICK - 1)
    if text.count(old_tick) != 1:
        raise SystemExit("E_CLOSE_TICK: expected exactly one %r" % old_tick)
    text = text.replace(old_tick, '"tick": %d,' % TICK)
    head, tail = text.rsplit("\r\n  ]\r\n}\r\n", 1)
    if tail.strip():
        raise SystemExit("E_CLOSE_TAIL: unexpected tail %r" % tail[:40])
    pieces = []
    for item in items():
        body = json.dumps(item, ensure_ascii=True)
        pieces.append("\r\n                " + body)
    # the previous last item and this batch are joined by a comma
    if not head.rstrip().endswith(","):
        head = head.rstrip() + ","
    return head + ",".join(pieces) + "\r\n  ]\r\n}\r\n"


def main(argv):
    execute = "--execute" in argv
    with open(STATE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    new_text = bump(text)
    before = json.loads(text)
    after = json.loads(new_text)
    same = all(after[key] == before[key] for key in before
               if key not in ("log", "tick"))
    grew = len(after["log"]) == len(before["log"]) + len(items())
    canon = SIO.canon(new_text)
    print("CLOSEOUT R2346 tick=%d items=%d log=%d->%d fields_same=%s "
          "canon_bytes=%d"
          % (after["tick"], len(items()), len(before["log"]), len(after["log"]),
             same, len(canon.encode("utf-8"))))
    if not (same and grew and after["tick"] == TICK):
        print("E_CLOSE_SHAPE: refusing to write")
        return 2
    if not execute:
        print("DRY RUN: pass --execute to write")
        return 0
    # state_io.write_canon is a REPAIR writer (it refuses any payload change by
    # design), so this append writes its own canon text atomically and then
    # proves the layout with the same module's canon check.
    if SIO.canon(canon) != canon:
        print("E_CLOSE_CANON: the text is not in the state canon")
        return 2
    temp = STATE + ".closeout-tmp"
    with open(temp, "wb") as handle:
        handle.write(canon.encode("utf-8"))
    os.replace(temp, STATE)
    written = len(canon.encode("utf-8"))
    print("WROTE %s bytes=%d" % (STATE, written))
    with open(STATE, "rb") as handle:
        back = handle.read()
    ok = back.decode("utf-8") == canon and json.loads(back.decode("utf-8"))["tick"] == TICK
    print("READBACK ok=%s bytes=%d" % (ok, len(back)))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))