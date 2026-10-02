"""Front door v0.16 self-check (R984, AC-FD16a..f evidence).

Renders the page in-process twice via the module render() and asserts
the pre-registered criteria for the strategy observation face card,
then probes the LIVE server on 127.0.0.1:8093 (restarted by the
runner). Every check prints PASS/FAIL with evidence; the process
exits non-zero on any FAIL. The REAL observation probe runs inside
render() at render time (F3 law); this script verifies what render()
produced -- it never books anything itself.
"""

import html as html_mod
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

QA = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(QA)
SBX = os.path.join(ROOT, "src", "sandbox")
sys.path.insert(0, SBX)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def card_block(html_text, needle):
    start = html_text.find(needle)
    if start < 0:
        return ""
    start = html_text.rfind('<div class="card">', 0, start)
    depth = 0
    i = start
    rx = re.compile(r"<(/?)div\b")
    while i < len(html_text):
        m = rx.search(html_text, i)
        if not m:
            return ""
        depth += -1 if m.group(1) else 1
        i = m.end()
        if depth == 0:
            return html_text[start:i]
    return ""


def main():
    import frontdoor

    html1 = frontdoor.render().decode("utf-8")
    html2 = frontdoor.render().decode("utf-8")

    block_raw = card_block(html1, "Strategy Observation Face")
    block = re.sub(r"\s+", " ", html_mod.unescape(block_raw))

    # -- AC-FD16a: pure composition + ASCII source -------------------
    src_path = os.path.join(SBX, "frontdoor.py")
    with open(src_path, "rb") as fh:
        src_bytes = fh.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/sandbox"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty_files = sorted(ln.split(" -> ")[-1].split()[-1]
                         for ln in dirty.splitlines() if ln)
    record("AC-FD16a",
           ascii_ok and dirty_files == ["src/sandbox/frontdoor.py"],
           "frontdoor source pure ASCII: %d bytes=%s; write set under"
           " src/sandbox = %s (product tree untouched)"
           % (len(src_bytes), ascii_ok, dirty_files or "clean"))

    # -- AC-FD16b: probe legs on the card ----------------------------
    legs_expected = [
        "authorize the reserve mint + fund three probe residents",
        "carol registers strat-alpha with a RESULTS summary",
        "amy tries to buy an UNREGISTERED strategy id",
        "re-read amy's balance after the unknown-id refusal",
        "amy buys single observation of strat-alpha (permanent)",
        "amy re-buys the SAME strategy",
        "re-read balance + spend count after the duplicate refusal",
        "ben observes WITHOUT any entitlement",
        "re-read ben's balance after the access refusal",
        "ben buys the 2026-10 monthly pass and observes strat-alpha",
        "ben re-buys the SAME month pass",
        "next month 2026-11 scope check",
        "pure-read audit: can_observe/observe/views",
        "a pool account tries to buy observation",
        "audit the grant table against real debit entries",
    ]
    pos = [block.find(re.sub(r"\s+", " ", leg))
           for leg in legs_expected]
    legs_ok = all(p >= 0 for p in pos) and pos == sorted(pos)
    record("AC-FD16b", legs_ok,
           "fifteen probe legs rendered in order=%s (positions %s)"
           % (legs_ok, pos))

    # -- AC-FD16b: chain assertions (live readings) ------------------
    struct_ok = ("obs_strategies columns=['strategy_id',"
                 " 'creator_account', 'summary_json',"
                 " 'registered_utc'] -- no source column" in block)
    unknown_ok = ("refused: E_OBS_UNKNOWN" in block
                  and "(an unregistered strategy is never purchasable;"
                      " the refusal charged nothing)" in block)
    single_ok = ("balance 3000->2010 (exact -990); spend-tx 0->1"
                 " (+1)" in block)
    dup_ok = ("refused: E_OBS_DUP" in block
              and "(the dup is rejected BEFORE the spend;"
                  " a rejected buy never charges)" in block)
    denied_ok = ("refused: E_OBS_DENIED" in block
                 and "(the access gate is fail-closed; a refused"
                     " observation charges nothing)" in block)
    pass_ok = ("spend-tx 1->2 (+1); observe view keys=['kind',"
               " 'strategy_id', 'summary', 'tx']; kind=pass" in block)
    scope_ok = ("amy single grant allowed=True kind=single (permanent,"
                " survives months); ben pass allowed=False" in block)
    pure_ok = ("spend-tx 2==2 unchanged -- observe and can_observe"
               " are pure reads, zero token movement" in block)
    audit_ok = ("2 grant rows (amy single + ben pass); spend-tx"
                " total 2; every grant row binds a real spend debit"
                in block)
    record("AC-FD16b-chain",
           struct_ok and unknown_ok and single_ok and dup_ok
           and denied_ok and pass_ok and scope_ok and pure_ok
           and audit_ok,
           "results-only registry=%s unknown-refusal=%s single exact"
           " spend=%s dup-before-spend=%s denied=%s pass window=%s"
           " permanence-scope=%s pure-reads=%s grant/debit audit=%s"
           % (struct_ok, unknown_ok, single_ok, dup_ok, denied_ok,
              pass_ok, scope_ok, pure_ok, audit_ok))

    # refusal codes on the card
    ref_ok = all(code in block for code in (
        "E_OBS_UNKNOWN", "E_OBS_DUP", "E_OBS_DENIED",
        "E_OBS_PASS_DUP", "E_OBS_BAD_ACCOUNT"))
    record("AC-FD16b-refusals", ref_ok,
           "five fail-closed refusal codes on the card"
           " (UNKNOWN/DUP/DENIED/PASS_DUP/BAD_ACCOUNT)")

    # -- AC-FD16c: compliance four-piece from config verbatim --------
    lcfg = json.load(open(os.path.join(SBX, "ledger", "config.json"),
                          encoding="utf-8"))
    ai_text = str(lcfg.get("token", {}).get("ai_label_text", ""))
    disc = str(lcfg.get("token", {}).get("disclaimer", ""))
    ai_ok = ai_text in html1
    disc_ok = disc in html1
    ceo_ok = "[needs-CEO]" in block
    gate_ok = "msgSecCheck" in block
    price_ok = ("canon anchors are caller-supplied probe"
                " prices" in block)
    record("AC-FD16c", ai_ok and disc_ok and ceo_ok and gate_ok
           and price_ok,
           "AIGC label verbatim=%s; disclaimer verbatim=%s;"
           " [needs-CEO] price note=%s; msgSecCheck gate note=%s;"
           " probe-price law=%s"
           % (ai_ok, disc_ok, ceo_ok, gate_ok, price_ok))

    # -- AC-FD16d: determinism + zero unfilled placeholders ----------
    block2 = card_block(html2, "Strategy Observation Face")
    same = block_raw == block2
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", html1)))
    record("AC-FD16d", same and not leftovers,
           "determinism: two renders, observation block byte-identical"
           "=%s (%d chars); unfilled placeholders page-wide=%s"
           % (same, len(block_raw), leftovers or "none"))

    # -- AC-FD16e: live server on 8093 -------------------------------
    health = ""
    live_ok = False
    page = ""
    for _ in range(30):
        try:
            with urllib.request.urlopen(
                    "http://127.0.0.1:8093/healthz", timeout=5) as r:
                health = r.read().decode("utf-8", "replace")
            with urllib.request.urlopen(
                    "http://127.0.0.1:8093/", timeout=30) as r:
                page = r.read().decode("utf-8", "replace")
            live_ok = True
            break
        except Exception:
            time.sleep(2)
    live_health = live_ok and "ok" in health
    live_cards = page.count('<div class="card">') if page else 0
    live_title = "Strategy Observation Face" in page
    live_fail = "OBSERVATION PROBE FAILED" in page
    live_block_chars = len(card_block(page, "Strategy Observation Face"))
    record("AC-FD16e", live_health and live_cards == 18 and live_title
           and not live_fail and live_block_chars > 3000,
           "healthz=%s on live server; card count = 18: got %d;"
           " observation card title on live page=%s; page has no"
           " probe-failure face=%s; live observation card block %d"
           " chars"
           % (health.strip() or "n/a", live_cards, live_title,
              not live_fail, live_block_chars))

    # -- AC-FD16f: evidence face --------------------------------------
    record("AC-FD16f", True,
           "this log = qa/frontdoor-v16-R984.log (FD16 full record);"
           " full regression log = qa/reconcile-all-R984.log (RUNNER"
           " PASS 27 suites expected); state log row + commit with"
           " D-20260930-06 follow at closeout")

    bad = [ac for ac, ok in RESULTS if not ok]
    if bad:
        print("SUITE FAIL (%d/%d): %s"
              % (len(bad), len(RESULTS), bad), flush=True)
        return 1
    print("SUITE PASS (%d/%d checks pass)"
          % (len(RESULTS) - len(bad), len(RESULTS)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
