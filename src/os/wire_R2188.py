# -*- coding: utf-8 -*-
"""R2188 runner wiring: register ledger-apimarket-sellersupply(8)."""
import io

P = "src/sandbox/reconcile_all.py"
s = io.open(P, encoding="utf-8").read()

ANCHOR = ('    ("ledger-apimarket-categoryvelocitymonths", os.path.join(\n'
          '        "ledger", "test_apimarket_categoryvelocitymonths.py"), 8),\n')
assert s.count(ANCHOR) == 1, s.count(ANCHOR)

NEW = ANCHOR + (
    '    # seller-side supply rollup - every listing the seller owns\n'
    '    # rolled into live/retired partitions, tracked vs unlimited\n'
    '    # shelves, sold-out and low-stock counts and four derived\n'
    '    # totals, all riding the single _supply_full seam - criteria\n'
    '    # AC-SSUP1..AC-SSUP8 pre-registered in the R2178 10/10\n'
    '    # explore-queue row BEFORE this suite existed.\n'
    '    ("ledger-apimarket-sellersupply", os.path.join(\n'
    '        "ledger", "test_apimarket_sellersupply.py"), 8),\n')

s = s.replace(ANCHOR, NEW)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("WIRE OK")