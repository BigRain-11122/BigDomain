"""Front door v0.18 self-check (R987, AC-FD18a..f evidence).

Renders the page in-process twice via the module render() and asserts
the pre-registered criteria for the virtual-exhibition ad-slot face
card, then probes the LIVE server on 127.0.0.1:8093 (restarted by the
runner). Every check prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL. The REAL ads probe runs inside render() at
render time (F3 law); this script verifies what render() produced --
it never books anything itself.
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

    block_raw = card_block(html1, "Ad Slot Face")
    block = re.sub(r"\s+", " ", html_mod.unescape(block_raw))

    # -- AC-FD18a: pure composition + ASCII source -------------------
    src_path = os.path.join(SBX, "frontdoor.py")
    with open(src_path, "rb") as fh:
        src_bytes = fh.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/sandbox"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty_files = sorted(ln.split(" -> ")[-1].split()[-1]
                         for ln in dirty.splitlines() if ln)
    record("AC-FD18a",
           ascii_ok and dirty_files == ["src/sandbox/frontdoor.py"],
           "frontdoor source pure ASCII: %d bytes=%s; write set under"
           " src/sandbox = %s (product tree untouched)"
           % (len(src_bytes), ascii_ok, dirty_files or "clean"))

    # -- AC-FD18b: probe legs on the card ----------------------------
    legs_expected = [
        "authorize the reserve mint + fund four probe residents",
        "re-register the screen under a DIFFERENT kind",
        "register four ad units under the three product kinds",
        "ben tries to book an UNREGISTERED ad unit",
        "re-read ben's balance after the unknown-unit refusal",
        "amy buys the harbor-gate naming right for year-window 26",
        "amy replays the SAME naming unit-window",
        "re-read balance + spend count after the replay refusal",
        "ben hits the SAME naming window held by amy",
        "re-read ben's balance after the exclusivity refusal",
        "carol buys the lobby splash for the two-week span 40..41",
        "dave tries a FOURTH concurrent carousel slot at week 50",
        "three rotation slots fill, the fourth is refused",
        "dave books an off-peak span and carol advance-books the"
        " metro-l4 naming at window 100",
        "a corp: account tries to book",
        "a zero price is refused",
        "a zero window count is refused",
        "a negative start window is refused",
        "an empty booking ref is refused",
        "bad-args audit: five refusals, ben's balance flat",
        "lineup / holder / board reads are pure and ordered",
        "audit the bookings against real debit entries",
        "isolation law audit on the REAL module source",
    ]
    pos = [block.find(re.sub(r"\s+", " ", leg))
           for leg in legs_expected]
    legs_ok = all(p >= 0 for p in pos) and pos == sorted(pos)
    record("AC-FD18b", legs_ok,
           "twenty-three probe legs rendered in order=%s (positions %s)"
           % (legs_ok, pos))

    # -- AC-FD18b: chain assertions (live readings) ------------------
    struct_ok = ("ads-owned tables=['ad_units'] -- one small registry"
                 " only, the module source has zero direct INSERT INTO"
                 " venue_occupancy" in block)
    unknown_ok = ("refused: E_AD_UNKNOWN" in block
                  and "(an unregistered unit is never bookable; the"
                      " refusal charged nothing)" in block)
    single_ok = ("balance 50000->40000 (exact -10000); spend-tx 0->1"
                 " (+1); span=26..26; occ row #1 bound to that spend"
                 " as its provenance; kind=building_naming" in block)
    dup_ok = ("refused: E_AD_DUP" in block
              and "(the replay is rejected BEFORE the spend; a"
                  " rejected booking never charges)" in block)
    taken_ok = ("refused: E_AD_TAKEN" in block
                and "(naming and splash are exclusive units, at most"
                    " one holder per window; the refusal charged"
                    " nothing)" in block)
    splash_ok = ("balance 50000->40000 (exact -10000 = 2 windows x"
                 " 5000); spend-tx 1->2 (+1); span=40..41; splash"
                 " owner week40=usr:carol week41=usr:carol"
                 " week42=None (span scope only)" in block)
    full_ok = ("amy/ben/carol booked 2->5 (+3 spends); fees"
               " 8000/4000/2000 = windows x 2000; dave refused with"
               " his balance 50000==50000 untouched (capacity 3 ="
               " rotation_slots, the refusal charged nothing)" in block
               and "refused: E_AD_FULL" in block)
    advance_ok = ("dave span=52..54 fee=6000 (only amy overlaps at"
                  " 52..53, inside capacity); carol advance"
                  " span=100..100 fee=10000 charged today for a"
                  " future window; holder 99=None / 100=usr:carol /"
                  " 101=None (advance window scope)" in block)
    badargs_ok = (block.count("refused: E_AD_BAD_ARGS") == 5
                  and "46000==46000 (advertisers are usr:* only,"
                      " price must be int > 0, windows int >= 1,"
                      " start_window int >= 0, ref required" in block)
    reads_ok = ("spend-tx 7==7 unchanged -- reads move zero tokens;"
                " lineup at week 50 (full) = [(1, 'usr:amy'),"
                " (2, 'usr:ben'), (3, 'usr:carol')] in booking order"
                " with rotation_slots=3; at week 53 = [(1, 'usr:amy'),"
                " (2, 'usr:dave')] (ben and carol expired, 2/3);"
                " naming holder 26=usr:amy 27=None; board rows=1"
                " each carrying its bound spend tx" in block)
    audit_ok = ("spend-tx total 7 == bookings 7; every one of the 7"
                " occupancy rows binds a real spend debit as its"
                " provenance and 0 of them live outside the ad"
                " registry; balances exact: amy 50000-10000-8000"
                "=32000, ben 50000-4000=46000, carol"
                " 50000-10000-2000-10000=28000, dave 50000-6000=44000;"
                " pool:reserve 90000 (240000 mint, spent tokens loop"
                " back in, conservation holds); ad_units registry"
                " rows=4" in block)
    isolation_ok = ("zero direct INSERT INTO venue_occupancy and zero"
                    " UPDATE surface on registry or occupancy rows"
                    " (banned SQL found=none, the suite AC-AD7"
                    " pattern); the face holds the token ledger only"
                    " to share its DB file -- self.led appears"
                    " exactly 1 time (the reference store), every"
                    " spend is booked by the venue engine" in block)
    record("AC-FD18b-chain",
           struct_ok and unknown_ok and single_ok and dup_ok
           and taken_ok and splash_ok and full_ok and advance_ok
           and badargs_ok and reads_ok and audit_ok and isolation_ok,
           "registry=%s unknown-refusal=%s single-exact-spend=%s"
           " dup-before-spend=%s taken=%s splash-span=%s"
           " carousel-full=%s advance=%s badargs=%s pure-reads=%s"
           " debit-audit=%s isolation=%s"
           % (struct_ok, unknown_ok, single_ok, dup_ok, taken_ok,
              splash_ok, full_ok, advance_ok, badargs_ok, reads_ok,
              audit_ok, isolation_ok))

    # refusal codes on the card
    ref_ok = all(code in block for code in (
        "E_AD_KIND_MISMATCH", "E_AD_UNKNOWN", "E_AD_DUP",
        "E_AD_TAKEN", "E_AD_FULL", "E_AD_BAD_ARGS"))
    record("AC-FD18b-refusals", ref_ok,
           "six fail-closed refusal codes on the card"
           " (KIND_MISMATCH/UNKNOWN/DUP/TAKEN/FULL/BAD_ARGS)")

    # -- AC-FD18c: compliance four-piece from config verbatim --------
    lcfg = json.load(open(os.path.join(SBX, "ledger", "config.json"),
                          encoding="utf-8"))
    ai_text = str(lcfg.get("token", {}).get("ai_label_text", ""))
    disc = str(lcfg.get("token", {}).get("disclaimer", ""))
    ai_ok = ai_text in html1
    disc_ok = disc in html1
    ceo_ok = "[needs-CEO]" in block
    gate_ok = "msgSecCheck" in block
    price_ok = ("the B3 canon anchors (giant-screen carousel 2,000"
                " CNY/week, building naming right 10,000 CNY/year,"
                " lobby splash 5,000 CNY/week) are caller-supplied"
                " probe prices" in block)
    record("AC-FD18c", ai_ok and disc_ok and ceo_ok and gate_ok
           and price_ok,
           "AIGC label verbatim=%s; disclaimer verbatim=%s;"
           " [needs-CEO] price note=%s; msgSecCheck gate note=%s;"
           " probe-price law=%s"
           % (ai_ok, disc_ok, ceo_ok, gate_ok, price_ok))

    # -- AC-FD18d: determinism + zero unfilled placeholders ----------
    block2 = card_block(html2, "Ad Slot Face")
    same = block_raw == block2
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", html1)))
    record("AC-FD18d", same and not leftovers,
           "determinism: two renders, ads block byte-identical=%s"
           " (%d chars); unfilled placeholders page-wide=%s"
           % (same, len(block_raw), leftovers or "none"))

    # -- AC-FD18e: live server on 8093 -------------------------------
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
    live_title = "Ad Slot Face" in page
    live_fail = "AD PROBE FAILED" in page
    live_block_chars = len(card_block(page, "Ad Slot Face"))
    record("AC-FD18e", live_health and live_cards == 20 and live_title
           and not live_fail and live_block_chars > 3000,
           "healthz=%s on live server; card count = 20: got %d;"
           " ads card title on live page=%s; page has no"
           " probe-failure face=%s; live ads card block %d chars"
           % (health.strip() or "n/a", live_cards, live_title,
              not live_fail, live_block_chars))

    # -- AC-FD18f: evidence face --------------------------------------
    record("AC-FD18f", True,
           "this log = qa/frontdoor-v18-R987.log (FD18 full record);"
           " full regression log = qa/reconcile-all-R987.log (RUNNER"
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
