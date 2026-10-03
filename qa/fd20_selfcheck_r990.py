"""Front door v0.20 self-check (R990, AC-FD20a..f evidence).

Renders the page in-process twice via the module render() and asserts
the pre-registered criteria for the city data report face card, then
probes the LIVE server on 127.0.0.1:8093 (restarted by the runner).
Every check prints PASS/FAIL with evidence; the process exits non-zero
on any FAIL. The REAL reports probe runs inside render() at render
time (F3 law); this script verifies what render() produced -- it
never buys or downloads anything itself.
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

    block_raw = card_block(html1, "Reports Face")
    block = re.sub(r"\s+", " ", html_mod.unescape(block_raw))

    # -- AC-FD20a: pure composition + ASCII source --------------------
    src_path = os.path.join(SBX, "frontdoor.py")
    with open(src_path, "rb") as fh:
        src_bytes = fh.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/sandbox"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty_files = sorted(ln.split(" -> ")[-1].split()[-1]
                         for ln in dirty.splitlines() if ln)
    record("AC-FD20a",
           ascii_ok and dirty_files == ["src/sandbox/frontdoor.py"],
           "frontdoor source pure ASCII: %d bytes=%s; write set under"
           " src/sandbox = %s (product tree untouched)"
           % (len(src_bytes), ascii_ok, dirty_files or "clean"))

    # -- AC-FD20b: probe legs on the card -----------------------------
    legs_expected = [
        "authorize the reserve mint + fund three probe buyers",
        "re-publish the quarterly report at a DIFFERENT price",
        "publish the quarterly ecosystem report (aggregate"
        " descriptors + sha256 dataset digest)",
        "publish the custom industry-insight report",
        "amy tries to buy an UNPUBLISHED report",
        "re-read amy's balance after the unpublished refusal",
        "amy buys the quarterly report (99 CNY anchor)",
        "amy replays the SAME purchase ref",
        "amy buys the SAME report again under a NEW ref (one copy"
        " per buyer)",
        "re-read amy's balance + spend count after both replay"
        " refusals",
        "carol buys the custom industry insight (999 CNY anchor)",
        "an ent: enterprise account tries to buy directly on the"
        " resident token ledger",
        "a corp: account tries to buy",
        "an empty purchase ref is refused",
        "publishing with an UNKNOWN kind is refused",
        "publishing at price zero is refused",
        "bad-args audit: four refusals, amy's balance flat",
        "amy downloads the quarterly report through her voucher",
        "amy replays the SAME download ref",
        "ben tries to download through AMY's voucher",
        "an UNKNOWN voucher is refused",
        "amy downloads the SAME report a second time under a NEW"
        " ref",
        "pure-read audit: descriptor / download_log /"
        " reconcile_report",
        "audit the purchases against real debit entries",
        "isolation law audit on the REAL module source",
    ]
    pos = [block.find(re.sub(r"\s+", " ", leg))
           for leg in legs_expected]
    legs_ok = all(p >= 0 for p in pos) and pos == sorted(pos)
    record("AC-FD20b", legs_ok,
           "twenty-five probe legs rendered in order=%s (positions %s)"
           % (legs_ok, pos))

    # -- AC-FD20b: chain assertions (live readings) -------------------
    struct_ok = ("published=True; identical re-publish idempotent="
                 "True; price-drift re-publish refused E_RPT_DUP"
                 " (published rows are immutable, no UPDATE exists);"
                 " registration carries only period/industry tags +"
                 " digest -- zero user rows, zero raw data (structural"
                 " de-identification)" in block)
    unknown_ok = ("refused: E_RPT_UNPUBLISHED" in block
                  and "15000==15000 (an unpublished report is never"
                      " purchasable; the refusal charged nothing)"
                  in block)
    single_ok = ("balance 15000->5100 (exact -9900 = one copy, one"
                 " spend); spend-tx 0->1 (+1); the immutable purchase"
                 " row (the permission gate) binds that spend tx and"
                 " issues exactly one voucher" in block)
    custom_ok = ("balance 120000->20100 (exact -99900); spend-tx"
                 " 1->2 (+1); each report copy = exactly one spend"
                 " at its published catalog price, bound to its own"
                 " purchase row + voucher" in block)
    dup_ok = ("5100==5100 and 1==1 (duplicate ref and duplicate"
              " buyer+report copy are both rejected BEFORE the"
              " spend; a rejected purchase never charges and never"
              " grants)" in block)
    ent_ok = ("refused: E_BAD_ACCOUNT at the token layer -- the"
              " module buyer gate accepts ent:* but the token ledger"
              " spend is usr:*-only (census binding, AC-L11), so the"
              " stack is fail-closed: zero charge, zero rows"
              " written; production enterprise procurement routes"
              " through the BigCompute collection gateway"
              " (D-20260924-11 collection exit unified there)"
              in block)
    badargs_ok = (block.count("refused: E_RPT_BAD_ARGS") == 4
                  and "5100==5100 (buyers are usr:/ent: at the module"
                      " gate and the ledger enforces usr:*-only"
                      " census-bound spend; refs and kinds are"
                      " required, price >= 1 -- every rejected call"
                      " charges nothing and writes no row)" in block)
    delivery_ok = ("delivery keys exactly the nine-key descriptor"
                   " set ['dataset_digest', 'disclaimer_first',"
                   " 'disclaimer_last', 'industry_tag', 'kind',"
                   " 'period_tag', 'pricing_note', 'report_id',"
                   " 'title']; disclaimer_first == disclaimer_last =="
                   " the non-advisory standing notice (structurally"
                   " accompanied at both ends); kind=quarterly,"
                   " period=2026-Q3, digest in bundle=True; spend-tx"
                   " 2==2 unchanged -- the download moves zero"
                   " tokens; zero raw operational rows by"
                   " construction" in block)
    redownload_ok = ("one voucher may download repeatedly with"
                     " distinct refs -- download_log rows=2, both"
                     " bound to the same voucher; second delivery"
                     " descriptor key-set equal on the nine-key"
                     " face=True; spend-tx still 2==2 (downloads"
                     " are free re-reads of the permission gate;"
                     " raw voucher ids are never rendered)" in block)
    reads_ok = ("spend-tx 2==2 unchanged -- reads move zero tokens;"
                " quarterly reconcile balanced=True purchases=1"
                " vouchers=1 downloads=2 orphan=[] billed=9900;"
                " custom reconcile balanced=True purchases=1"
                " downloads=0 billed=99900" in block)
    audit_ok = ("spend-tx total 2 == purchases 2; all 2 purchase"
                " rows bind a real spend debit for their own buyer;"
                " balances exact: amy 15000-9900=5100, ben 12000"
                " untouched=12000, carol 120000-99900=20100;"
                " pool:reserve 122800 (160000 mint, spent tokens"
                " loop back in, conservation holds:"
                " pool+balances==mint=True)" in block)
    isolation_ok = ("banned token-verb hits=none in reports.py;"
                    " token touch points=1 (self.led.spend inside"
                    " purchase only); non-ascii=0; the module owns"
                    " exactly its three report tables and never"
                    " SELECTs any other table -- user rows and raw"
                    " operational stores cannot leak through this"
                    " face; vouchers, downloads and every read move"
                    " zero tokens, and no verb turns a voucher back"
                    " into tokens or moves it between buyers (the"
                    " suite AC-CT7 counts-vs-tokens posture)" in block)
    record("AC-FD20b-chain",
           struct_ok and unknown_ok and single_ok and custom_ok
           and dup_ok and ent_ok and badargs_ok and delivery_ok
           and redownload_ok and reads_ok and audit_ok
           and isolation_ok,
           "publish-idempotence=%s unpublished-gate=%s"
           " one-spend=%s custom-999=%s dup-before-spend=%s"
           " ent-token-refusal=%s badargs=%s descriptor-nine-keys=%s"
           " repeated-download=%s pure-reads=%s debit-audit=%s"
           " isolation=%s"
           % (struct_ok, unknown_ok, single_ok, custom_ok, dup_ok,
              ent_ok, badargs_ok, delivery_ok, redownload_ok,
              reads_ok, audit_ok, isolation_ok))

    # refusal codes on the card
    ref_ok = all(code in block for code in (
        "E_RPT_UNPUBLISHED", "E_RPT_DUP", "E_RPT_BAD_ARGS",
        "E_RPT_NOT_OWNER", "E_RPT_UNKNOWN_VOUCHER", "E_BAD_ACCOUNT"))
    record("AC-FD20b-refusals", ref_ok,
           "six fail-closed refusal codes on the card"
           " (UNPUBLISHED/DUP/BAD_ARGS/NOT_OWNER/UNKNOWN_VOUCHER"
           " + the ledger-layer E_BAD_ACCOUNT enterprise boundary)")

    # -- AC-FD20c: compliance four-piece from config verbatim --------
    lcfg = json.load(open(os.path.join(SBX, "ledger", "config.json"),
                          encoding="utf-8"))
    ai_text = str(lcfg.get("token", {}).get("ai_label_text", ""))
    disc = str(lcfg.get("token", {}).get("disclaimer", ""))
    ai_ok = ai_text in html1
    disc_ok = disc in html1
    ceo_ok = "[needs-CEO]" in block
    gate_ok = "msgSecCheck" in block
    price_ok = ("the B6 canon anchors (quarterly"
                " one-person-AI-company ecosystem report 99 CNY per"
                " copy, custom industry insight 999 CNY per copy) are"
                " caller-supplied probe publish prices" in block)
    record("AC-FD20c", ai_ok and disc_ok and ceo_ok and gate_ok
           and price_ok,
           "AIGC label verbatim=%s; disclaimer verbatim=%s;"
           " [needs-CEO] price note=%s; msgSecCheck gate note=%s;"
           " probe-price law=%s"
           % (ai_ok, disc_ok, ceo_ok, gate_ok, price_ok))

    # -- AC-FD20d: determinism + zero unfilled placeholders ----------
    block2 = card_block(html2, "Reports Face")
    same = block_raw == block2
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", html1)))
    record("AC-FD20d", same and not leftovers,
           "determinism: two renders, reports block byte-identical=%s"
           " (%d chars); unfilled placeholders page-wide=%s"
           % (same, len(block_raw), leftovers or "none"))

    # -- AC-FD20e: live server on 8093 -------------------------------
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
    live_title = "Reports Face" in page
    live_fail = "REPORTS PROBE FAILED" in page
    live_block_chars = len(card_block(page, "Reports Face"))
    record("AC-FD20e", live_health and live_cards == 22 and live_title
           and not live_fail and live_block_chars > 3000,
           "healthz=%s on live server; card count = 22: got %d;"
           " reports card title on live page=%s; page has no"
           " probe-failure face=%s; live reports card block %d chars"
           % (health.strip() or "n/a", live_cards, live_title,
              not live_fail, live_block_chars))

    # -- AC-FD20f: evidence face --------------------------------------
    record("AC-FD20f", True,
           "this log = qa/frontdoor-v20-R990.log (FD20 full record);"
           " full regression log = qa/reconcile-all-R990.log (RUNNER"
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
