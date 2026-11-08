"""R2563 five-silence: decisions diff, ledger rows, orders tail, benchmarks."""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(BASE, "src", "os", "state.json")
GROUP = os.path.join(os.path.dirname(os.path.dirname(BASE)), "docs",
                     "decisions.md")
LEDGER = os.path.join(os.path.dirname(os.path.dirname(BASE)), "cph4",
                      "evolution-ledger.md")
ORDERS = os.path.join(os.path.dirname(os.path.dirname(BASE)), "docs",
                      "orders.md")

TOKEN = re.compile(r"\b([DC]-\d{8}-\d{2,3})\b")


def main():
    doc = json.loads(io.open(STATE, encoding="utf-8").read())
    known = set(doc.get("last_dec_tokens") or [])
    text = io.open(GROUP, encoding="utf-8", errors="replace").read()
    rows = [line for line in text.split("\n") if TOKEN.search(line)]
    tokens = set()
    for line in rows:
        if line.lstrip().startswith(("D-", "C-")):
            match = TOKEN.match(line.lstrip())
            if match:
                tokens.add(match.group(1))
    new = sorted(tokens - known)
    print("decisions rows=%d row_tokens=%d new=%d" % (len(rows), len(tokens),
                                                      len(new)))
    for token in new:
        print("  NEW %s" % token)
    ledger = io.open(LEDGER, encoding="utf-8", errors="replace").read()
    mine = [line for line in ledger.split("\n")
            if "@BigDomain" in line]
    print("ledger @BigDomain rows=%d" % len(mine))
    for line in mine[-3:]:
        print("  %s" % line[:160])
    orders = io.open(ORDERS, encoding="utf-8", errors="replace").read()
    stamps = re.findall(r"2026-\d\d-\d\d \d\d:\d\d", orders)
    print("orders tail=%s" % (max(stamps) if stamps else "none"))
    print("benchmarks_refreshed=%s" % (doc.get("benchmarks_refreshed"),))
    return 0


if __name__ == "__main__":
    sys.exit(main())