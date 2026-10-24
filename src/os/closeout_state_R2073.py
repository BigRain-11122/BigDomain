"""R2073 state closeout: bump tick, append the round narrative
and the token ledger line, preserve the file's EOL and layout.
Pure ASCII source; the narrative text is data carried verbatim."""

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.normpath(os.path.join(HERE, "..", "..", "src", "os",
                                      "state.json"))

ROUND = (
    "2026-10-24 R2073 (P3 explore-queue FIFO head after the tech heads"
    " stayed non-claimable: docker-compose environment-gated, logs"
    " toolkit delivered across the AC-LT1..LT25 slices, member refunded"
    " gated on a product read-face need, suite-matrix live-mtime"
    " delivered through R1967; seed = the R2045 month-boundary suite) -"
    " the apimarket developer sales board three-month purchase straddle"
    " window. Five-silence scan clean: decisions.md 223 rows with zero"
    " new content-addressed tokens against the baseline, ledger zero new"
    " @BigDomain rows, group orders baseline unchanged at 2026-10-24"
    " 06:5x, benchmarks refreshed 2026-10-20 (inside 7 days), tree"
    " clean, no index.lock. Claimed the explore row with"
    " AC-AMSTR1..AMSTR7 pre-registered in the queue row BEFORE the"
    " suite existed (AC-AMSTR prefix and the"
    " ledger-apimarket-devboardmonthstraddle label both git-grep"
    " zero-occupancy, rc=1). Delivered"
    " src/sandbox/ledger/test_apimarket_devboardmonth_straddlepersist.py:"
    " the loaded three-month world (dana OCT+NOV listings, erin OCT"
    " listing, six purchases stamped at month-start and month-end"
    " seconds) pins the exact boundary-second law (2026-10-31T23:59:59Z"
    " is OCT, 2026-11-01T00:00:00Z is NOV, same for NOV/DEC, each side"
    " counted exactly once), three-window zero-permeation (the OCT"
    " snapshot taken between the OCT and NOV records stays byte-frozen"
    " after both later months accumulate, NOV frozen through DEC), the"
    " DEC third-month purchase face (a DEC purchase on an OCT listing and"
    " on a NOV listing shows purchase aggregates on zero listing_count"
    " rows), three-month conservation (OCT 17 + NOV 30 + DEC 27 == 74"
    " lifetime, per developer too, with the three month purchase-id sets"
    " disjoint and their union exactly the market rows), the dense"
    " ever-listed row set on every window, three-instance restart"
    " byte-identity, and the fourteen-form bad-window gate family"
    " answering E_AM_BAD_WINDOW before any read on the LOADED world with"
    " the market digests and ledger_tx set constant. SUITE PASS 7/7"
    " double-run identical (stdout sha16 cdfec06003c4b596); wired"
    " reconcile_all ledger-apimarket-devboardmonthstraddle(7) -> RUNNER"
    " PASS 281/281 suites + controls 7/7 219.9s; suite-matrix 281 suites"
    " / 2354 criteria --check byte-identical; evidence"
    " qa/api-str-straddle-R2073.log (tee dialect, crlf=0). Note: the"
    " three-month arithmetic on the OCT row keeps erin's OCT sale in the"
    " OCT window while dana's OCT listing is also sold in NOV, which is"
    " the dual-family law read from both directions in one run.")

TOKENS = ("R2073 tokens: local=~110k api=0 api_reason=five-silence scan"
          " + three-month straddle suite 7/7 double-run + battery 281/281"
          " + matrix regen/check + evidence log + state/export closeout,"
          " zero cloud calls")


def js(value):
    return json.dumps(value, ensure_ascii=False)


with io.open(STATE, "r", encoding="utf-8", newline="") as f:
    text = f.read()

NL = "\r\n" if text.count("\r\n") > text.count("\n") / 2 else "\n"

text, n = re.subn(r'"tick": \d+', '"tick": 2073', text, count=1)
if n != 1:
    sys.exit("FATAL: tick anchor %d" % n)

tail = re.search(r"\r?\n(\s*)\]\r?\n\}\s*$", text)
if tail is None:
    sys.exit("FATAL: log tail anchor not found")

body = text[:tail.start()]
last = re.search(r"\r?\n(\s*)\"(?:[^\"\\\\]|\\\\.)*\"\s*$", body)
if last is None:
    sys.exit("FATAL: last log line anchor not found")
indent = last.group(1)
prev = body[:last.start()].rstrip()
if not prev.endswith(","):
    prev = prev + "," + NL + indent
text = (prev + NL + js(ROUND) + "," + NL + indent + js(TOKENS) + NL
        + tail.group(1) + "]" + NL + "}" + NL)

doc = json.loads(text)
if doc["tick"] != 2073:
    sys.exit("FATAL: tick not 2073")
if doc["log"][-1] != TOKENS or doc["log"][-2] != ROUND:
    sys.exit("FATAL: appended log lines not in place")

with io.open(STATE, "w", encoding="utf-8", newline="") as f:
    f.write(text)
print("STATE-OK tick=2073 log=%d bytes=%d nl=%r"
      % (len(doc["log"]), len(text.encode("utf-8")), NL))