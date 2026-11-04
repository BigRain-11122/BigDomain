"""export_R2457 - refresh docs/status-export.json for the R2457 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
one outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2457 product window on the CEO fleet order OB-20261105-003656-879: the silicon city is now "
           "openable in a browser - the read-only city HTTP face serves a shipped page at GET /city and "
           "GET /city/ (population, districts, visitors, ambient, event tail, census lookup) while "
           "/city/snapshot and /census/<id> keep their exact JSON contract")

base.LATEST = ("src/sandbox/lobby/city_view.html (6653B self-contained page, AI 生成内容 label + "
               "non-investment note verbatim, zero network references) served by "
               "src/sandbox/lobby/city.py at GET /city and GET /city/ + "
               "qa/city-view-R2457.log (SUITE PASS 6/6 twice, AC-CV1..AC-CV6, sha16 "
               "F4DA3A32459C2E32 of the served bytes; both legs ran the real server on a private port and a "
               "temp db) + src/sandbox/lobby/test_city_view.py (the proof)")

base.NEXT = ("2026-11-05/06 the owed full reconcile battery runs FIRST on the committed R2457 tree at the "
             "pre-registered 556 suites / 4312 criteria (row reconcile-battery-R2458), then the carried "
             "product-face-R2456 (tech head AC-PFKC1) or the next P-47 business face; the city page is "
             "runnable right now: python src/sandbox/lobby/server.py --city-http-port 8092 then "
             "http://127.0.0.1:8092/city/, ETA inside 48h")

base.RESULT = (
    "2026-11-05 R2457 PRODUCT window on the CEO fleet order OB-20261105-003656-879 (real output only, no "
    "new mechanism / rule / document) rather than on the debt gate named product-face-R2456: the five-"
    "silence scan HELD (git clean at HEAD 0368b20b, zero @BigDomain ledger rows, decisions new=0 against a "
    "129-token baseline over 199 rows, orders tail 2026-11-05 00:36 == last_order, benchmarks 2026-11-03 "
    "inside the seven-day gate), so no dispatch forced the choice - the internal queue head is an audit face "
    "and the standing order of the day is real output, so this window made the city viewable. SHIPPED "
    "src/sandbox/lobby/city_view.html (6653B, self-contained, zero http/https references, both standing "
    "compliance surfaces verbatim: AI 生成内容 label and the non-investment note) and one route in "
    "src/sandbox/lobby/city.py, so GET /city and GET /city/ serve that page while /city/snapshot keeps "
    "application/json and /census/<id> keeps its 200/404 contract and every non-GET stays 405. The page "
    "renders the snapshot package (population, districts_open, visitors_today, ambient, trend, event tail) "
    "and a census lookup box over the existing endpoint. EVIDENCE: test_city_view.py reads SUITE PASS 6/6 "
    "twice with identical verdict lines (AC-CV1..AC-CV6, a 200 text/html 6653B offline page, both compliance "
    "strings present, post=405 unknown=404 census=200, /city and /city/ byte-identical and equal to the file "
    "on disk sha16 F4DA3A32459C2E32, an empty city dir still serving the page with a 503 snapshot and the "
    "not-ready line, and hygiene bom=False crlf=0 ascii_src=True wired=True), qa/city-view-R2457.log written "
    "by one utf-8 LF single writer, both legs running the REAL server on a private port and a temp db so no "
    "live database was touched; the 79-criteria lobby suite stayed green (AC-S13 proofs unchanged) and the "
    "registry now reads 556 suites / 4312 criteria. Honest limits: the first suite run failed 5/6 on my own "
    "wiring assertion (registry label vs the pre-registered criterion) and the REGISTRY was renamed rather "
    "than the criterion loosened; the page needs the server because fetch has no origin under file://; no "
    "battery or matrix ran this window (the R2168 mixed-tree rule) so reconcile-battery-R2458 was registered "
    "and is owed FIRST next window; READ-ONLY observation, not repaired because the city data line owns the "
    "file: city_data/world-public.json and citizens-light.jsonl carry evidently truncated multi-byte "
    "sequences that the new page will display as-is. Two product points: after nine internal-audit windows "
    "this station now has a second CEO-openable surface, and it is the first one a person can browse."
)

base.OUTS = (
    "src/sandbox/lobby/city_view.html (the shipped page) + src/sandbox/lobby/city.py (one route) + "
    "src/sandbox/lobby/test_city_view.py (six criteria, two real-server legs) + "
    "src/sandbox/reconcile_all.py (os-lobby-city-view registered) + qa/city-view-R2457.log + "
    "docs/status-export.json + src/os/state.json + src/os/backlog.md + state/debt.md + tasks.md + "
    "heartbeat.txt + src/os/closeout_R2457.py + src/os/export_R2457.py"
)

if __name__ == "__main__":
    sys.exit(base.main())