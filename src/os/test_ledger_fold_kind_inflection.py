"""Fold-summary inflection suite (R2815).

Criteria AC-LKNF1..AC-LKNF6 were pre-registered in state/queue/tech.md:715
BEFORE this code existed (honesty law). That row was itself seeded by
R2581 from a measured limit, and this window re-measured it at HEAD:

  (a) "R2568 Fold of log lines 1..20 into the archive"        -> round
  (b) "2026-11-08 R2568 Fold of log lines 1..20"              -> round
  (c) "R2568 folds the block into the archive"                -> round
  (c2) "2026-11-08 R2568 folds the block into the archive"    -> round
  (d) "11/08/2026 R2568 fold of log lines 1..20"              -> other
  (e) "- R2568 fold of log lines 1..20"                       -> other

Every line that read round reported rounds_without_ledger=[2568], i.e. the
summary a fold leaves behind was counted as a round that never closed.

What this suite pins: a capitalized fold summary and the third-person
form ("folds") are summaries too; the word boundary is NOT loosened, so
"Folder of ..." and "foldsomething" stay round narratives that still
gate; every shape the R2580 and R2581 suites pinned still reads exactly
as before (taken from THOSE suites' own fixtures rather than copied); and
the live face over the real state.json log stays clean while both sibling
suites keep 6/6.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import importlib.util
import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger_lines as LL  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "ledger_lines.py")
STATE = os.path.join(BASE, "state.json")
SIBLINGS = (
    "test_ledger_fold_kind.py",
    "test_ledger_fold_kind_dateprefix.py",
)

PASSES = 0
FAILS = 0

CAP_SUMMARY = "R2568 Fold of log lines 1..20 into the archive"
DATE_CAP_SUMMARY = "2026-11-08 R2568 Fold of log lines 1..20"
THIRD = "R2568 folds the block into the archive"
DATE_THIRD = "2026-11-08 R2568 folds the block into the archive"
FOLDER = "R2568 Folder of log lines was rebuilt"
FOLD_SOMETHING = "R2568 foldsomething happened here"
MENTIONS_FOLD = "R2568 the fold disclosure shipped"


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def load_sibling(name):
    """Import a sibling suite by file name so its fixtures are the source.

    Neither sibling runs its main() at import time, so importing them is
    inert; it only makes their pinned fixture constants reachable here.
    """
    path = os.path.join(BASE, name)
    spec = importlib.util.spec_from_file_location(
        "sib_%s" % name[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    # AC-LKNF1: a CAPITALIZED fold summary is other, bare or dated, and a
    # live-shaped window built around it reports no gap.
    shaped = [
        CAP_SUMMARY,
        "2026-11-08 R2569 PRODUCT window on the tech head",
        "R2569 tokens: local=~21k api=0 api_reason=inflection round ledger",
    ]
    rep = LL.audit(shaped)
    dated = LL.audit([DATE_CAP_SUMMARY,
                      "2026-11-08 R2569 PRODUCT window on the tech head",
                      "R2569 tokens: local=~21k api=0 api_reason=dated cap "
                      "summary window"])
    check(LL.classify(CAP_SUMMARY) == "other"
          and LL.classify(DATE_CAP_SUMMARY) == "other"
          and rep["rounds_without_ledger"] == []
          and rep["ledger_without_round"] == []
          and rep["errors"] == []
          and rep["clean"] is True
          and dated["rounds_without_ledger"] == []
          and dated["clean"] is True,
          "AC-LKNF1 capitalized fold summary is other, dated or bare")

    # AC-LKNF2: the THIRD-PERSON form is a summary too, bare or dated.
    bare_third = LL.audit([THIRD])
    dated_third = LL.audit([DATE_THIRD])
    check(LL.classify(THIRD) == "other"
          and LL.classify(DATE_THIRD) == "other"
          and bare_third["rounds_without_ledger"] == []
          and bare_third["clean"] is True
          and dated_third["rounds_without_ledger"] == []
          and dated_third["clean"] is True,
          "AC-LKNF2 third-person 'folds' form is other, dated or bare")

    # AC-LKNF3: no over-swallow. The boundary is not loosened by the
    # inflection work: "Folder" and "foldsomething" stay narratives and
    # still gate, and so does a narrative that only mentions the fold.
    folder = LL.audit([FOLDER])
    something = LL.audit([FOLD_SOMETHING])
    mention = LL.audit([MENTIONS_FOLD])
    check(LL.classify(FOLDER) == "round"
          and LL.classify(FOLD_SOMETHING) == "round"
          and LL.classify(MENTIONS_FOLD) == "round"
          and folder["rounds_without_ledger"] == [2568]
          and folder["clean"] is False
          and something["rounds_without_ledger"] == [2568]
          and something["clean"] is False
          and mention["rounds_without_ledger"] == [2568]
          and mention["clean"] is False,
          "AC-LKNF3 'Folder'/'foldsomething'/mention stay round and gate")

    # AC-LKNF4: every shape the R2580 and R2581 suites pinned still reads
    # exactly as it did there - taken from THOSE suites' own fixture
    # constants, so the expectation cannot drift away from its origin.
    r2580 = load_sibling(SIBLINGS[0])
    r2581 = load_sibling(SIBLINGS[1])
    pinned = [
        (r2580.FOLD_SUMMARY, "other"),
        (r2581.ANCHORED, "other"),
        (r2581.INFLECTED, "other"),
        (r2581.DATE_FOLD, "other"),
        (r2581.DATE_INFLECTED, "other"),
        (r2581.MENTIONS_FOLD, "round"),
        (r2581.FOLDER, "round"),
        ("R2568 fold-line summary rebuilt", "other"),
    ]
    wrong = [(line, want, LL.classify(line))
             for line, want in pinned if LL.classify(line) != want]
    check(not wrong,
          "AC-LKNF4 all R2580/R2581 pinned shapes unchanged%s"
          % ("" if not wrong else " (wrong: %r)" % (wrong,)))

    # AC-LKNF5: no weakening - the bare narrative and the 'token:' typo
    # still gate, and the shipped ledger / dated-round families are
    # classified exactly as before.
    weakened = LL.audit([
        "2026-11-08 R300 (product change narrative) something happened",
        "R301 token: local=1k api=0 api_reason=typo prefix round keeps gaps",
    ])
    check(weakened["rounds_without_ledger"] == [300, 301]
          and weakened["clean"] is False
          and LL.classify("R301 tokens: local=1k api=0 api_reason=x y z")
          == "ledger"
          and LL.classify("2026-11-08 R301 PRODUCT window on the tech head")
          == "round"
          and LL.classify("carry-forward rolling line R586: folded") == "other",
          "AC-LKNF5 bare narrative, typo prefix, shipped families unchanged")

    # AC-LKNF6: the real tree reads clean on the live face, both sibling
    # suites keep their 6/6, and this module stays ASCII and network-free.
    with io.open(MODULE, "r", encoding="ascii", errors="strict") as handle:
        source = handle.read()
    net = LL.network_imports(source)
    live = LL.audit(LL.load_state_log(STATE))
    sibling_ok = True
    sibling_detail = []
    for name in SIBLINGS:
        proc = subprocess.run([sys.executable, os.path.join(BASE, name)],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              cwd=BASE)
        out = proc.stdout.decode("utf-8", "replace")
        ok = proc.returncode == 0 and "SUITE PASS 6/6 criteria" in out
        sibling_ok = sibling_ok and ok
        sibling_detail.append("%s rc=%d" % (name, proc.returncode))
    check(live["rounds_without_ledger"] == []
          and live["ledger_without_round"] == []
          and live["errors"] == []
          and live["clean"] is True
          and not net
          and sibling_ok
          and EXPECTED_CRITERIA == 6,
          "AC-LKNF6 real log clean, both siblings 6/6, ASCII, no network"
          " (%s)" % ", ".join(sibling_detail))

    print("suite: fold-summary inflection (R2815 AC-LKNF1..AC-LKNF6)")
    if FAILS:
        print("SUITE FAIL %d/%d criteria" % (PASSES, EXPECTED_CRITERIA))
        return 1
    print("SUITE PASS %d/%d criteria" % (PASSES, EXPECTED_CRITERIA))
    return 0


if __name__ == "__main__":
    sys.exit(main())
