"""Fold-summary date-prefix and inflection suite (R2581).

Criteria AC-LKND1..AC-LKND6 were pre-registered in state/queue/tech.md:626
BEFORE this code existed (honesty law).

What this proves: R2580 shipped a word-bounded fold-summary guard, but it
was anchored at the line start and knew only the bare "fold" inflection.
Two real summary shapes therefore fell back to the narrative pattern and
re-opened the exact gap R2580 closed - a summary stamped with the date the
fold ran ("2026-11-08 R2568 fold of log lines ...") and the past-tense
form ("R2568 folded the block into the archive"). This suite pins that
both now read other, that nothing is over-swallowed (a narrative that
merely mentions the fold later in the line still gates), that the
word-boundary contract is unchanged, that no shipped family was weakened,
and that the real state.json log still reads clean while the R2580 suite
keeps its 6/6.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

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
SIBLING = os.path.join(BASE, "test_ledger_fold_kind.py")

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


DATE_FOLD = ("2026-11-08 R2568 fold of log lines 1..20 into the archive; "
             "all 138 tokens preserved verbatim in this line: AC-DSRC1")
INFLECTED = "R2568 folded the block into the archive"
DATE_INFLECTED = "2026-11-08 R2568 folded the block into the archive"
ANCHORED = "R2568 fold of log lines 1..20 into the archive"
FOLDER = "R2568 folder of log lines was rebuilt"
MENTIONS_FOLD = "R2568 the fold disclosure shipped"


def main():
    # AC-LKND1: a DATE-PREFIXED fold summary is other, and the live window
    # shape that motivated the seed reads clean instead of reporting a gap.
    shaped = [
        DATE_FOLD,
        "2026-11-08 R2569 PRODUCT window on the tech head",
        "R2569 tokens: local=~22k api=0 api_reason=product window ledger line",
    ]
    rep = LL.audit(shaped)
    check(LL.classify(DATE_FOLD) == "other"
          and rep["rounds_without_ledger"] == []
          and rep["ledger_without_round"] == []
          and rep["errors"] == []
          and rep["clean"] is True,
          "AC-LKND1 date-prefixed fold summary is other and leaves no gap")

    # AC-LKND2: the INFLECTED past-tense form is a summary too, with and
    # without the date prefix, and it leaves no gap either.
    bare = LL.audit([INFLECTED,
                     "2026-11-08 R2569 PRODUCT window on the tech head",
                     "R2569 tokens: local=~9k api=0 api_reason=verification"])
    dated = LL.audit([DATE_INFLECTED,
                      "2026-11-08 R2569 PRODUCT window on the tech head",
                      "R2569 tokens: local=~9k api=0 api_reason=verification"])
    check(LL.classify(INFLECTED) == "other"
          and LL.classify(DATE_INFLECTED) == "other"
          and bare["clean"] is True
          and dated["clean"] is True
          and bare["rounds_without_ledger"] == []
          and dated["rounds_without_ledger"] == [],
          "AC-LKND2 inflected 'folded' form is other, dated or bare")

    # AC-LKND3: no over-swallow. A genuine narrative that only MENTIONS the
    # fold later in the line stays a round narrative and still gates.
    mention = LL.audit([MENTIONS_FOLD])
    dated_mention = LL.audit(["2026-11-08 " + MENTIONS_FOLD])
    check(LL.classify(MENTIONS_FOLD) == "round"
          and LL.classify("2026-11-08 " + MENTIONS_FOLD) == "round"
          and mention["rounds_without_ledger"] == [2568]
          and mention["clean"] is False
          and dated_mention["rounds_without_ledger"] == [2568]
          and dated_mention["clean"] is False,
          "AC-LKND3 a narrative merely mentioning the fold still gates")

    # AC-LKND4: the word-boundary contract is unchanged - "folder" is not a
    # summary while the anchored summary still is, dated or not.
    folder = LL.audit([FOLDER])
    check(LL.classify(FOLDER) == "round"
          and LL.classify("2026-11-08 " + FOLDER) == "round"
          and folder["rounds_without_ledger"] == [2568]
          and folder["clean"] is False
          and LL.classify(ANCHORED) == "other"
          and LL.classify("R2568 fold-line summary rebuilt") == "other",
          "AC-LKND4 'folder' stays round, anchored summaries stay other")

    # AC-LKND5: no weakening - the bare narrative and the 'token:' typo
    # still gate, and the shipped ledger and dated-round families are
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
          "AC-LKND5 bare narrative, typo prefix and shipped families unchanged")

    # AC-LKND6: the real tree reads clean on the live face, the R2580 suite
    # keeps its 6/6, and this module is ASCII and network-free.
    with io.open(MODULE, "r", encoding="ascii", errors="strict") as handle:
        source = handle.read()
    net = LL.network_imports(source)
    live = LL.audit(LL.load_state_log(STATE))
    sibling = subprocess.run([sys.executable, SIBLING],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             cwd=BASE)
    sibling_out = sibling.stdout.decode("utf-8", "replace")
    check(live["rounds_without_ledger"] == []
          and live["ledger_without_round"] == []
          and live["errors"] == []
          and live["clean"] is True
          and not net
          and sibling.returncode == 0
          and "SUITE PASS 6/6 criteria" in sibling_out
          and EXPECTED_CRITERIA == 6,
          "AC-LKND6 real log clean, R2580 suite still 6/6, ASCII, no network")

    print("suite: fold-summary date-prefix and inflection "
          "(R2581 AC-LKND1..AC-LKND6)")
    if FAILS:
        print("SUITE FAIL %d/%d criteria" % (PASSES, EXPECTED_CRITERIA))
        return 1
    print("SUITE PASS %d/%d criteria" % (PASSES, EXPECTED_CRITERIA))
    return 0


if __name__ == "__main__":
    sys.exit(main())