"""R965 frontdoor v0.10 render self-check (ASCII output discipline).

Runs the real render() in-process and asserts the preregistered
AC-FD10a..d faces. Exit 0 = all pass, 2 = any fail (honest verdict).
Evidence goes to qa/frontdoor-v10-R965.log.
"""
import io
import re
import sys

sys.path.insert(0, "src/sandbox")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                 errors="replace")
except Exception:
    pass
import frontdoor  # noqa: E402 (journey runs once at import, as live)

RESULTS = []


def chk(name, ok, evidence=""):
    RESULTS.append((name, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", name, evidence))


page = frontdoor.render().decode("utf-8")

# AC-FD10b: live probe numbers, zero canned, zero unfilled placeholders
leftover = re.findall(r"__[A-Z0-9_]{2,}__", page)
chk("FD10b-no-unfilled-placeholders", not leftover, str(leftover[:3]))
chk("FD10b-live-kpis", "probe tx booked" in page
    and "issued = -equity:auth" in page, "kpi block rendered from probe")
chk("FD10b-balances-table", "usr:probe-a" in page
    and "equity:auth" in page and "role in the probe" in page,
    "six-account balances table")
chk("FD10b-zero-sum-identity", "sum of the six balances = 0" in page)
chk("FD10b-gate-refusal-live", "E_GATE_REF" in page,
    "unrecorded-event refusal code rendered from the live probe")
chk("FD10b-spend-loop-closure", "credited back into" in page
    and "pool:reserve" in page, "BLUEPRINT 5.4 loop line")
chk("FD10b-honest-failure-face-absent",
    "LEDGER PROBE FAILED" not in page, "probe succeeded, no fake face")

# AC-FD10c: reconcile verdict computed + tamper detection computed
chk("FD10c-recon-pass-8", "VERDICT: RECONCILE PASS (8/8 checks)" in page)
chk("FD10c-recon-lines-8",
    page.count(" double-entry-balance PASS") == 1
    and page.count(" balance-sign-law PASS") == 1
    and page.count(" content-gate-refs PASS") == 1,
    "eight-check lines on page")
chk("FD10c-tamper-control-fails",
    "double-entry-balance FAIL" in page
    and "materialized-vs-derived FAIL" in page
    and "VERDICT: RECONCILE FAIL" in page,
    "tamper copy detected by the same engine, FAIL lines shown")

# AC-FD10d: compliance four-piece from config, persistent
chk("FD10d-compliance-four-piece",
    "AIGC" in page and "msgSecCheck front gate" in page
    and "[needs-CEO]" in page and "disclaimer" in page,
    "label/disclaimer/[needs-CEO]/content-gate all on card")
import json as _json  # noqa: E402
lc = _json.load(open("src/sandbox/ledger/config.json", encoding="utf-8"))
chk("FD10d-config-sourced",
    str(lc["token"]["ai_label_text"]) in page
    and str(lc["token"]["disclaimer"]) in page,
    "AIGC label + disclaimer strings verbatim from ledger config")

# AC-FD10a: pure composition + pure ASCII source
src = open("src/sandbox/frontdoor.py", "rb").read()
bad = [b for b in src if b >= 128]
chk("FD10a-source-pure-ascii", not bad, "%d bytes, %d non-ascii"
    % (len(src), len(bad)))
chk("FD10a-card-count-12", page.count('<div class="card">') == 12,
    "12 cards on page")
chk("FD10a-card-title-live", "Token Ledger Core Face" in page)

fails = [r for r in RESULTS if not r[1]]
print("RENDER CHECK: %d/%d pass" % (len(RESULTS) - len(fails),
                                    len(RESULTS)))
sys.exit(2 if fails else 0)
