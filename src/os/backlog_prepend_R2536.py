"""R2536 backlog prepend: one done row, proved by read-back.

Idempotent: refuses to prepend twice. Writes once through one atomic replace
and keeps the file LF (it is LF today and must stay LF).
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "backlog.md")

DONE = (
    "- [x] [done 2026-11-07 R2536] R2536 VERIFICATION window on the battery "
    "the register owed (reconcile-battery-R2535, pre-registered 597 suites / "
    "4558 criteria, re-measured by importing reconcile_all.SUITES before the "
    "launch and matching byte for byte). Five-silence scan clean at HEAD "
    "428bbdcd (git status empty, no index.lock, zero @BigDomain ledger rows, "
    "content-addressed decisions diff two tokens over the stored 174-token "
    "baseline D-20260930-18 and D-20261024-13 both inline references inside "
    "older rows prose so acknowledged by union, group orders tail a fleet "
    "audio closeout for bm-a/bm-b/bm-c node lanes so noted not executed, "
    "benchmarks 2026-11-03 inside the seven-day gate); the gate read "
    "CLAIM-FIRST item=reconcile-battery-R2535 first=1 at 16 open rows, so the "
    "battery ran before any product byte per the R2168 mixed-tree rule. "
    "BATTERY GREEN: qa/reconcile-all-R2536.log 935285B, RUNNER PASS "
    "(597/597 suites green, reconcile controls 7/7, 1448.8s), zero FAIL suite "
    "rows, and the runner own summary line reports expected criteria "
    "total=4558 so the registered and measured numbers agree on both axes; "
    "two FAIL lines inside the log are FIXTURE expectations that PASS at "
    "exit=2 with the failures named, and the R-D2/R-D3 rows are CEO physical "
    "item boundaries rather than suite failures. FOLLOW-UP in the designed "
    "order: matrix FAILED FIRST on a stale doc by design (on-disk=57572B "
    "regenerated=57573B, no byte written), then fingerprint PASS CLEAN "
    "domains=5, profile PASS byte-identical, census PASS DRIFT-CLEAN; the doc "
    "was regenerated stamp-aligned through suite_matrix.py --stamp-from to "
    "57573 bytes at 597 suites / 4558 criteria with green honestly 597/597 "
    "self-describing from this round own evidence, --check read "
    "byte-identical, and the four sections re-ran for VERDICT R2536 PASS "
    "failing=none (appended 1950B, eol_ok=True). DEBT through the shipped "
    "writers: reconcile-battery-R2535 closed (line 267, open 16->15, done "
    "234->235, 164023B -> 164026B, readback ok); NO successor battery is owed "
    "because the registry did not move, so the NEXT window owes a PRODUCT "
    "face - product-face-R2536 appended first=yes naming state/queue/tech.md:"
    "573 prefix AC-PNKB1 probe_seam_nested_key_binding_scope whose six "
    "criteria were pinned in that row at R2535 BEFORE any code (164026B -> "
    "164331B, readback ok). HONEST: zero product points, nothing a CEO could "
    "open was built; the battery ran 1448.8s past the 25 minute budget and "
    "the red leg rule forbids a partial claim; one AUTOMATIC CANCEL of a "
    "silent poll loop was measured and the detached battery was unaffected so "
    "no duplicate run exists; a first followup call with --round R2536 was "
    "refused E_BFU_BAD_ARGS before any section ran and the integer form was "
    "used; Docker absent; the real 19.9 debit and the real msgSecCheck still "
    "wait on CEO physical items; tasks.md untouched; the S4U lane reconcile "
    "still needs an ELEVATED shell; no fold was due at open."
)


def main():
    raw = open(PATH, "rb").read()
    eol = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8")
    if "R2536 VERIFICATION window" in text:
        print("NOOP already prepended")
        return 0
    before = len(raw)
    payload = DONE + eol + text
    predicted = len(payload.encode("utf-8"))
    print("backlog before=%d predicted=%d delta=%d"
          % (before, predicted, predicted - before))
    with io.open(PATH, "wb") as handle:
        handle.write(payload.encode("utf-8"))
    back_raw = open(PATH, "rb").read()
    back = back_raw.decode("utf-8").split(eol)
    ok = (len(back_raw) == predicted
          and back[0].startswith("- [x] [done 2026-11-07 R2536]"))
    print("backlog %s measured=%d readback=%s"
          % ("OK" if ok else "FAIL", len(back_raw), "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())