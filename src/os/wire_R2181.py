"""R2181: wire the seller-cohort suite into the reconcile_all runner."""

import io
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TARGET = os.path.join(BASE, "src", "sandbox", "reconcile_all.py")

ANCHOR = "    # apimarket retirement to re-listing gap"

ADD = (
    "    # apimarket monthly seller cohort - one listing event per\n"
    "    # listing row and one re-listing event per re-listing row, the\n"
    "    # cohort law (new exactly once, earliest month across the whole\n"
    "    # history), the repeat-seller law and the honest empty -\n"
    "    # criteria AC-MSC1..AC-MSC8 pre-registered in the R2181\n"
    "    # explore-queue claim row BEFORE this suite existed.\n"
    '    ("ledger-apimarket-sellercohort", os.path.join(\n'
    '        "ledger", "test_apimarket_sellercohort.py"), 8),\n'
)


def main():
    text = io.open(TARGET, encoding="utf-8").read()
    assert text.count(ANCHOR) == 1, "anchor not unique"
    assert "ledger-apimarket-sellercohort" not in text, "already wired"
    text = text.replace(ANCHOR, ADD + ANCHOR)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
    print("wired ledger-apimarket-sellercohort(8)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())