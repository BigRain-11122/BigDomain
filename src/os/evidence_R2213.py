# -*- coding: utf-8 -*-
"""R2213 evidence runner: double-run the new suite and the adjacent
watch-family regressions through one utf-8 LF single writer."""
import io
import os
import subprocess
import sys

LEDGER = os.path.join("src", "sandbox", "ledger")
QA = "qa"

SUITES = [
    ("apimarket-buyerwatchmonths-R2213", "test_apimarket_buyerwatchmonths.py"),
    ("apimarket-buyerwatchmonths-R2213-b", "test_apimarket_buyerwatchmonths.py"),
]


def run_suite(name):
    proc = subprocess.run([sys.executable, name], cwd=LEDGER,
                          capture_output=True)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def write_log(tag, rc, body):
    out = os.path.join(QA, tag + ".log")
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    text = body if body.endswith("\n") else body + "\n"
    text += "RC %d\n" % rc
    with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return out


def main():
    results = []
    for tag, name in SUITES:
        rc, body = run_suite(name)
        path = write_log(tag, rc, body)
        line = body.strip().split("\n")[-1]
        results.append((tag, rc, line))
        print("%s rc=%d %s" % (tag, rc, line), flush=True)

    adjacent = [
        ("apimarket-sellerwatchmonths", "test_apimarket_sellerwatchmonths.py"),
        ("apimarket-marketwatchmonths", "test_apimarket_marketwatchmonths.py"),
        ("apimarket-categorywatchmonths",
         "test_apimarket_categorywatchmonths.py"),
        ("apimarket-watchlist", "test_apimarket_watchlist.py"),
        ("apimarket-watchconversion", "test_apimarket_watchconversion.py"),
        ("apimarket-buyerwatchcategorymix",
         "test_apimarket_buyerwatchcategorymix.py"),
    ]
    for tag, name in adjacent:
        rc, body = run_suite(name)
        last = [l for l in body.strip().split("\n") if l.startswith("SUITE")]
        print("%s rc=%d %s" % (tag, rc, last[-1] if last else "NO-SUITE"),
              flush=True)
        results.append((tag, rc, (last[-1] if last else "NO-SUITE")))

    bad = [r for r in results if r[1] != 0]
    print("TOTAL %d bad=%d" % (len(results), len(bad)), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())