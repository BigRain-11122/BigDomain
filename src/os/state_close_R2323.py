"""state_close_R2323.py - append the R2323 window items through state_io.

No fold this window: the measured margin is 2599B and these four items are
written to fit under the 78500B gate, so the closeout predicts its own size
and refuses to write over the gate. Dry run by default; --execute writes.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_io  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
GATE = 78500

NARRATIVE = (
    "2026-11-01 R2323 (five-silence scan clean at open: tree clean, no lock, "
    "no unreplied ledger row, orders tail and decisions unchanged, benchmarks "
    "fresh); the R2322 battery row was done, so this window claimed the TOP "
    "deliverable tech row - the R2302 orphan_trace seed at tech.md:379, "
    "AC-OTR1..AC-OTR6 pinned in that row BEFORE the code. PRODUCT "
    "src/os/orphan_trace.py plus its suite: ORPHAN stops being a dead end - "
    "list, round and pairing come from evidence_variants, the "
    "RUNNER token and decoder from followup_history, both patched in the "
    "suite; every leg carrying a RUNNER line is named with its runner, "
    "verdict and digest, standing-in leg first in NAME order; no "
    "runner line reads NO-TRACE, an empty list reads NO-ORPHAN at exit 0, an "
    "undecodable leg refuses instead of counting as empty. SUITE PASS 6/6 "
    "twice, five adjacent os suites green, qa/orphan-trace-R2323.log 1342B, "
    "wired os-orphan-trace(6). LIVE rounds=1 legs=2 trace_exists=1: R2136 "
    "stands in through -c (RUNNER PASS) while -b reads RUNNER FAIL, so a rename "
    "recovers it. Claimable fell to 9, so one gap row was seeded "
    "(orphan_promote, AC-OTP1..AC-OTP6 pre-registered, anchors "
    "zero-occupancy), gauge FLOOR-MET 5/5 10/10 10/10. Battery carries to "
    "R2324; the next window must fold first.")

LEDGER = (
    "R2323 tokens: local=~19k api=0 api_reason=product window on the tech "
    "head - one resolver with its six pre-registered criteria and suite, one "
    "dogfooded evidence capture, one runner wiring line, one gap row seeded, "
    "the closeout; no cloud or external API calls; battery "
    "carries to R2324")

SELF_HEAL = (
    "R2323 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for lane tasks; register_loop_task.ps1 already passes an "
    "explicit S4U principal and needs an elevated shell, which this session is "
    "not, so the definition was left untouched (eighty-fifth consecutive "
    "disclosure, carried as loop-s4u-reconcile in state/debt.md).")

DISCLOSURES = (
    "R2323 honest disclosures: (a) the first suite run was red 2/6, both "
    "causes this-window defects, never criteria widened - "
    "followup_history.parse answers only the labelled form (VERDICT R<n> PASS) "
    "while the battery logs write the bare VERDICT PASS, so a local token scan "
    "was added and the shared parser still owns the RUNNER token; AC-OTR5 named "
    "the wrong world's render, fixed in the test. (b) The "
    "live legs carry no VERDICT line, so the column reads -. (c) tasks.md "
    "untouched: the P-47 board has no row here. (d) The gap "
    "seed is this window's own reading.")


def build(text):
    state = json.loads(text.decode("utf-8"))
    before = len(state["log"])
    state["tick"] = 2323
    state["log"].extend([NARRATIVE, LEDGER, SELF_HEAL, DISCLOSURES])
    ascii_only = all(byte < 0x80 for byte in text)
    body = json.dumps(state, ensure_ascii=ascii_only, indent=2)
    return before, state_io.canon(body).encode("utf-8")


def write(path, data, label):
    temp = os.path.join(os.path.dirname(path), ".%s.tmp" % label)
    with open(temp, "wb") as sink:
        sink.write(data)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, path)
    if open(path, "rb").read() != data:
        raise SystemExit("E_READBACK %s" % label)
    if os.path.exists(temp):
        raise SystemExit("E_RESIDUE %s" % label)


def main(argv):
    execute = "--execute" in argv
    raw = open(STATE, "rb").read()
    before_items, new = build(raw)
    print("LOG_ITEMS %d -> %d TICK 2323 BEFORE %dB AFTER %dB DELTA %+d "
          "GATE %d MARGIN %d"
          % (before_items, before_items + 4, len(raw), len(new),
             len(new) - len(raw), GATE, GATE - len(new)))
    if len(new) > GATE:
        raise SystemExit("E_C2323_OVER_GATE %d" % len(new))
    if not execute:
        print("DRY RUN - nothing written")
        return 0
    write(STATE, new, "state_close_R2323")
    parsed = json.loads(open(STATE, "rb").read().decode("utf-8"))
    if parsed["tick"] != 2323 or len(parsed["log"]) != before_items + 4:
        raise SystemExit("E_C2323_PARSE")
    print("WROTE %dB readback ok temp clean tick=%d log=%d"
          % (len(new), parsed["tick"], len(parsed["log"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))