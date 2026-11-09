"""test_export_R2431_health_verdict - the six criteria for one-word health.

Criteria AC-EDSW1..AC-EDSW6 were pinned inside the R2595 tech seed row of
state/queue/tech.md:630 BEFORE this code existed.

What this proves: the export driver's health term used to compare the document
with a SECOND recompute taken after the write, so any writer that appended one
state log line in between made a healthy refresh read ok=False. The term now
records the block once, stamps it into the document, and names the two causes
apart: a document rewritten by someone else after the write keeps today's
refusal, while a document that honestly carries write-time truth is called
DRIFT-UNDER-WRITE. The byte count the run prints is proved against the file on
disk in the same breath, and one refresh emits exactly one verdict word.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import export_R2431 as ER  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "export_R2431.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-export-driver-health-verdict"
WIRED_EXPECT = ('"os-export-driver-health-verdict",')
WORDS = (ER.DOC_DOCTORED, ER.DRIFT_UNDER_WRITE, ER.SIZE_MISMATCH,
         ER.CHECK_MISMATCH, ER.VERDICT_PASS)

A = {"window": 7, "log_lines_in_window": 10}
B = {"window": 7, "log_lines_in_window": 11}

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def read(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def ac_edsw1():
    """AC-EDSW1 a block that moved with the LOG is its own word."""
    drift = ER.classify(A, dict(A), dict(B), True, 10, 10)
    stable = ER.classify(A, dict(A), dict(A), True, 10, 10)
    check(drift == ER.DRIFT_UNDER_WRITE and stable == ER.VERDICT_PASS,
          "AC-EDSW1 a block that moved because the LOG moved reads "
          "DRIFT-UNDER-WRITE (%r) while a still tree reads PASS (%r)"
          % (drift, stable))


def ac_edsw2():
    """AC-EDSW2 a doctored document keeps today's refusal byte for byte."""
    doctored = ER.classify(dict(B), dict(A), dict(A), True, 10, 10)
    doctored_drift = ER.classify(dict(B), dict(A), dict(B), True, 10, 10)
    refused = (ER.DOC_DOCTORED not in ER.HEALTHY
               and ER.DRIFT_UNDER_WRITE in ER.HEALTHY
               and doctored == ER.DOC_DOCTORED
               and doctored_drift == ER.DOC_DOCTORED)
    source = read(MODULE)
    kept = 'sys.stdout.write("RESULTS rows=%d outs=%d tick=%s bytes=%d ' \
           'queue=%s "' in source
    check(refused and kept,
          "AC-EDSW2 a document whose block no longer matches the stamp reads "
          "DOC-DOCTORED (%r) even when the tree also moved (%r), stays out of "
          "HEALTHY, and the RESULTS line it refused with is unchanged (%r)"
          % (doctored, doctored_drift, kept))


def ac_edsw3():
    """AC-EDSW3 queue_bytes is proved against the file on disk."""
    mismatch = ER.classify(A, dict(A), dict(A), True, 10, 11)
    agree = ER.classify(A, dict(A), dict(A), True, 11, 11)
    source = read(MODULE)
    names = ("disk_bytes = os.path.getsize(EXPORT)" in source
             and 'VERDICT %s queue_bytes=%s disk_bytes=%d' in source)
    check(mismatch == ER.SIZE_MISMATCH and agree == ER.VERDICT_PASS and names,
          "AC-EDSW3 a printed byte count that differs from the disk reads "
          "SIZE-MISMATCH (%r) and the pair is named in the verdict line (%r)"
          % (mismatch, names))


def ac_edsw4():
    """AC-EDSW4 two moves in one call still yield one word, one write."""
    source = read(MODULE)
    reads = source.count("= self_drive()")
    publishes = source.count("EDQF.publish(")
    verdict_sites = source.count('"VERDICT ')
    words = set()
    for back, write, fresh in ((A, A, A), (A, A, B), (B, A, A),
                               (A, A, B)):
        words.add(ER.classify(dict(back), dict(write), dict(fresh),
                              True, 5, 5))
        words.add(ER.classify(dict(back), dict(write), dict(fresh),
                              False, 5, 5))
        words.add(ER.classify(dict(back), dict(write), dict(fresh),
                              True, 5, 6))
    ok = (reads == 2 and publishes == 1 and verdict_sites == 1
          and words and words <= set(WORDS) and len(words) > 1)
    if not ok:
        print("  measured: reads=%d publishes=%d sites=%d words=%r"
              % (reads, publishes, verdict_sites, sorted(words)), flush=True)
    check(ok, "AC-EDSW4 exactly two tree reads (one stamped, one at verdict), "
              "one publish, one verdict site, every outcome a single word")


def ac_edsw5():
    """AC-EDSW5 every R2595 term survives beside the new ones."""
    source = read(MODULE)
    terms = {
        "tick_row": 'and str(r[0]) == tick for r in back["results"]',
        "outs": 'back["outs"][0] == latest',
        "ceo_latest": 'back["ceo_face"]["latest_artifact"] == latest',
        "ceo_current": 'back["ceo_face"]["current"] == current',
        "ceo_next": 'back["ceo_face"]["next_milestone"] == milestone',
        "stamp": 'back["export_ts"] == STAMP',
        "self_drive": 'back["self_drive"] == at_write',
        "fresh": "fresh = self_drive()",
        "gate": 'proof.get("gate") == "CURRENT"',
    }
    missing = sorted(name for name, text in terms.items() if text not in source)
    check(not missing,
          "AC-EDSW5 the eight R2595 terms plus the fresh read all survive "
          "(missing=%r)" % (missing,))


def ac_edsw6():
    """AC-EDSW6 pure ASCII, stdlib only, zero network, own label and suite."""
    source = read(MODULE)
    ascii_ok = all(ord(ch) < 128 for ch in source)
    net_ok = not any(token in source for token in
                     ("urllib", "requests", "socket", "http.client"))
    imports = sorted(set(line.split()[1].split(".")[0]
                         for line in source.split("\n")
                         if line.startswith("import ")))
    # A sibling module in this same directory is this project's own code, not
    # a third-party dependency; stdlib-only forbids those, not our own files.
    stdlib = all(name in sys.stdlib_module_names
                 or os.path.exists(os.path.join(BASE, name + ".py"))
                 for name in imports)
    runner = read(RUNNER)
    wired = WIRED_EXPECT in runner and LABEL in runner
    ok = ascii_ok and net_ok and stdlib and wired
    if not ok:
        print("  measured: ascii=%r net=%r stdlib=%r imports=%r wired=%r"
              % (ascii_ok, net_ok, stdlib, imports, wired), flush=True)
    check(ok, "AC-EDSW6 pure ASCII, stdlib only, zero network, own reconcile "
              "label and own suite")


def main():
    print("SUITE export_R2431_health_verdict (R2596) criteria=%d"
          % EXPECTED_CRITERIA, flush=True)
    for name, fn in (("AC-EDSW1", ac_edsw1), ("AC-EDSW2", ac_edsw2),
                     ("AC-EDSW3", ac_edsw3), ("AC-EDSW4", ac_edsw4),
                     ("AC-EDSW5", ac_edsw5), ("AC-EDSW6", ac_edsw6)):
        fn()
    total = PASSES + FAILS
    if FAILS == 0 and PASSES == EXPECTED_CRITERIA:
        print("SUITE PASS %d/%d" % (PASSES, EXPECTED_CRITERIA), flush=True)
        return 0
    print("SUITE FAIL %d/%d" % (PASSES, total), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())