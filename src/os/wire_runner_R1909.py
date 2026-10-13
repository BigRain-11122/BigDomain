# -*- coding: utf-8 -*-
"""R1909: wire the lifecycletracepersist suite tuple into the
reconcile_all.py SUITES registry (idempotent)."""
import io

P = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain\src\sandbox\reconcile_all.py"
LABEL = "ledger-apidev-lifecycletracepersist"

with io.open(P, encoding="ascii") as h:
    src = h.read()
if LABEL in src:
    print("runner row already wired - skipped")
    raise SystemExit(0)
anchor = ('    ("ledger-apidev-rejecttallpersist", os.path.join(\n'
          '        "ledger", "test_apidev_rejecttallpersist.py"), 7),\n'
          ']')
comment = (
    "    # R1909 apidev lifecycle_trace windowed read"
    " cross-restart\n"
    "    # persistence suite: the pinned active middle key (one"
    " real\n"
    "    # October rotate_in row) plus a lone terminal-revoked"
    " key;\n"
    "    # full-envelope byte-replay across the three-piece"
    " close/reopen,\n"
    "    # one November rotation on the pinned key recalculates"
    " the\n"
    "    # default full-trail read zero-cache while the October"
    " windowed\n"
    "    # read freezes at the trail block (full-derived key"
    " facts\n"
    "    # re-derive, the R1875 window-lens law), lone-e keeps"
    " the\n"
    "    # full-envelope freeze, third-instance identity;"
    " pure-read\n"
    "    # law + hygiene (AC-TRW8..AC-TRW14 pre-registered in\n"
    "    # state/queue/tech.md)\n")
new = (anchor[:-2]
       + comment
       + '    ("' + LABEL + '", os.path.join(\n'
       + '        "ledger",'
       + ' "test_apidev_lifecycletracepersist.py"), 7),\n'
       + ']')
assert src.count(anchor) == 1, "anchor not unique"
src = src.replace(anchor, new)
with io.open(P, "w", encoding="ascii", newline="") as h:
    h.write(src)
print("runner row wired: %s (SUITES 150->151)" % LABEL)
