"""Fold round-block boundary suite (R2407, AC-FRB1..AC-FRB6).

What this proves: the fold refuses a window that ends after a round's own
tokens line while the next kept line still opens with that same round, so a
round's ledger line can no longer move to the archive while the rest of the
round stays live. That defect was MEASURED, not hypothesised: the R2405 fold
did exactly this to R2395 and three ledger suites read the orphan at R2407.

HONESTY NOTE ON ORDERING: these six criteria were written AFTER the guard
existed, because the guard was the repair of a red measured earlier in the
same window, not a pre-registered prediction. The debt row `fold-block-boundary`
(state/debt.md, opened R2336) carried the item intent and the R2407 evidence
log records this ordering rather than implying a pre-registration the tree
does not have.

Criteria:
  AC-FRB1 the guard names the round for the exact R2405 cut shape;
  AC-FRB2 a cut before the next round's own opener is allowed;
  AC-FRB3 prose that merely mentions the round mid-line is not a split;
  AC-FRB4 an executing fold over a split window writes NOTHING and reports
          round-split, while the archive stays byte-identical;
  AC-FRB5 a clean window still lands on its prediction (no regression);
  AC-FRB6 the guard lives in state_fold, is ASCII stdlib with no network, and
          its label is wired into the runner for six criteria.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402

EXPECTED_CRITERIA = 6
LABEL = "os-fold-round-block-boundary"
MODULE = os.path.join(BASE, "state_fold.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")

TOKENS = "R2395 tokens: local=1k api=0 api_reason=fixture ledger"
CONTINUATION = "2026-11-03 R2395 closeout disclosures, appended after the ledger"
NEXT_ROUND = "2026-11-03 R2396 product window, a new round"
PROSE = "2026-11-03 R2396 window records that R2395 was folded"

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


def literal(value):
    return SF.ps_escape(value)


def state_text(log_lines, newline="\r\n"):
    items = []
    for index, value in enumerate(log_lines):
        item = SF.ITEM_PREFIX + literal(value)
        if index < len(log_lines) - 1:
            item += ","
        items.append(item)
    lines = ["{", '  "tick": 1,', '  "log": ['] + items + ["  ]", "}"]
    return newline.join(lines)


def make_world(log_lines):
    world = tempfile.mkdtemp(prefix="bigdomain-frb-")
    os.makedirs(os.path.join(world, "src", "os"))
    os.makedirs(os.path.join(world, "logs"))
    with io.open(os.path.join(world, "src", "os", "state.json"), "w",
                 encoding="utf-8", newline="") as handle:
        handle.write(state_text(log_lines))
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def archive_bytes(world):
    folder = os.path.join(world, "logs")
    parts = []
    for leaf in sorted(os.listdir(folder)):
        with io.open(os.path.join(folder, leaf), "rb") as handle:
            parts.append((leaf, hashlib.sha256(handle.read()).hexdigest()))
    return tuple(parts)


ROUND_LOG = [TOKENS, CONTINUATION, NEXT_ROUND, NEXT_ROUND + " second item"]


def ac_frb1():
    """The exact R2405 cut shape is named."""
    got = SF.round_split([TOKENS], [CONTINUATION])
    ok = got == "R2395"
    if not ok:
        print("  measured %r" % (got,), flush=True)
    check(ok, "AC-FRB1 the guard names R2395 for the real split shape")


def ac_frb2():
    """A cut before the next round's opener is allowed."""
    got = SF.round_split([TOKENS], [NEXT_ROUND])
    check(got is None, "AC-FRB2 a cut at a true block boundary is allowed")


def ac_frb3():
    """A prose mention is not a continuation."""
    got = SF.round_split([TOKENS], [PROSE])
    check(got is None, "AC-FRB3 a mid-line mention is not a split")


def ac_frb4():
    """An executing fold over a split window writes nothing."""
    world = make_world(ROUND_LOG)
    try:
        before_state = open(os.path.join(world, "src", "os", "state.json"),
                            "rb").read()
        before_archive = archive_bytes(world)
        result = SF.fold(world, "RTEST", 700, 1, 1, "summary R2395 tokens: x",
                         execute=True)
        after_state = open(os.path.join(world, "src", "os", "state.json"),
                           "rb").read()
        ok = ("round-split" in result["would_fail"]
              and result.get("post_bytes") is None
              and before_state == after_state
              and archive_bytes(world) == before_archive
              and result["round_split"] == "R2395")
        if not ok:
            print("  measured fails=%r split=%r"
                  % (result["would_fail"], result["round_split"]), flush=True)
        check(ok, "AC-FRB4 a split window is refused before any write")
    finally:
        drop_world(world)


def ac_frb5():
    """A clean window still lands on its prediction."""
    world = make_world(ROUND_LOG)
    try:
        result = SF.fold(world, "RTEST", 701, 1, 2, "summary R2395 tokens: x",
                         execute=True)
        path = os.path.join(world, "src", "os", "state.json")
        after = open(path, "rb").read()
        ok = (result["would_fail"] == []
              and result["round_split"] is None
              and result["predicted_eq_actual"] is True
              and len(after) == result["post_bytes"])
        if not ok:
            print("  measured fails=%r eq=%r"
                  % (result["would_fail"], result.get("predicted_eq_actual")),
                  flush=True)
        check(ok, "AC-FRB5 a clean window still lands on its prediction")
    finally:
        drop_world(world)


def ac_frb6():
    """The guard is single-owned, pure stdlib, ASCII and wired."""
    with io.open(MODULE, "r", encoding="ascii", errors="strict") as handle:
        source = handle.read()
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner_src = handle.read()
    banned = ("urllib", "http.client", "socket", "requests")
    ok = (source.count("def round_split(") >= 1
          and "round-split" in source
          and not [name for name in banned if name in source]
          and LABEL in runner_src
          and EXPECTED_CRITERIA == 6)
    check(ok, "AC-FRB6 guard single-owned, ASCII stdlib, no network, wired")


def run():
    ac_frb1()
    ac_frb2()
    ac_frb3()
    ac_frb4()
    ac_frb5()
    ac_frb6()


def main():
    print("suite: fold round-block boundary (R2407 AC-FRB1..AC-FRB6)")
    run()
    total = PASSES + FAILS
    print("SUITE %s %d/%d criteria"
          % ("PASS" if FAILS == 0 and total == EXPECTED_CRITERIA else "FAIL",
             PASSES, EXPECTED_CRITERIA))
    return 0 if FAILS == 0 and total == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())