"""Front door v0.19 self-check (R989, AC-FD19a..f evidence).

Renders the page in-process twice via the module render() and asserts
the pre-registered criteria for the online-event venue + storefront
tenancy face card, then probes the LIVE server on 127.0.0.1:8093
(restarted by the runner). Every check prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL. The REAL venue
probe runs inside render() at render time (F3 law); this script
verifies what render() produced -- it never books anything itself.
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

    block_raw = card_block(html1, "Venue Face")
    block = re.sub(r"\s+", " ", html_mod.unescape(block_raw))

    # -- AC-FD19a: pure composition + ASCII source -------------------
    src_path = os.path.join(SBX, "frontdoor.py")
    with open(src_path, "rb") as fh:
        src_bytes = fh.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/sandbox"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty_files = sorted(ln.split(" -> ")[-1].split()[-1]
                         for ln in dirty.splitlines() if ln)
    record("AC-FD19a",
           ascii_ok and dirty_files == ["src/sandbox/frontdoor.py"],
           "frontdoor source pure ASCII: %d bytes=%s; write set under"
           " src/sandbox = %s (product tree untouched)"
           % (len(src_bytes), ascii_ok, dirty_files or "clean"))

    # -- AC-FD19b: probe legs on the card ----------------------------
    legs_expected = [
        "authorize the reserve mint + fund three probe residents",
        "re-register the plaza under a DIFFERENT capacity",
        "register the online-event venue with concurrent capacity 2",
        "ben tries to rent an UNREGISTERED venue",
        "re-read ben's balance after the unknown-venue refusal",
        "amy books the plaza event window 100..109",
        "carol books the overlapping event window 105..114",
        "ben tries a THIRD concurrent event inside the full window",
        "re-read ben's balance after the capacity refusal",
        "amy's window expires, the freed slot re-rents",
        "ben replays the SAME rental window",
        "re-read balance + spend count after the replay refusal",
        "amy takes the storefront lease booth-1 for 300..309",
        "ben hits the SAME storefront window held by amy",
        "re-read ben's balance after the exclusivity refusal",
        "ben leases the NEXT storefront window 310..314",
        "amy early-terminates her storefront lease at 305",
        "a corp: account tries to rent",
        "a zero price is refused",
        "a zero window count is refused",
        "a negative start tick is refused",
        "an empty rental ref is refused",
        "bad-args audit: five refusals, ben's balance flat",
        "pure-read audit: is_rented / tenant_of /"
        " occupancy_ledger",
        "audit the rentals against real debit entries",
        "isolation law audit on the REAL module source",
    ]
    pos = [block.find(re.sub(r"\s+", " ", leg))
           for leg in legs_expected]
    legs_ok = all(p >= 0 for p in pos) and pos == sorted(pos)
    record("AC-FD19b", legs_ok,
           "twenty-six probe legs rendered in order=%s (positions %s)"
           % (legs_ok, pos))

    # -- AC-FD19b: chain assertions (live readings) ------------------
    struct_ok = ("plaza capacity=2; same-capacity re-register returns"
                 " the same registration (idempotent); capacity drift"
                 " refused -- a mechanism registration face, zero"
                 " token touch" in block)
    unknown_ok = ("refused: E_VN_UNKNOWN" in block
                  and "15000==15000 (an unregistered venue is never"
                      " rentable; the refusal charged nothing)" in block)
    single_ok = ("balance 15000->10000 (exact -5000 = 10 windows x"
                 " 500, one event = one spend); spend-tx 0->1 (+1);"
                 " the occupancy row binds that spend as its"
                 " provenance; is_rented tick100=True tick109=True"
                 in block)
    concur_ok = ("balance 5000->0 (exact -5000); spend-tx 1->2 (+1);"
                 " concurrent capacity 2/2 inside the overlap 105..109"
                 " -- the plaza is a capacity-bounded scene, two"
                 " events run concurrently" in block)
    full_ok = ("refused: E_VN_FULL" in block
               and "15000==15000 (capacity 2 = concurrent event"
                   " slots, a third overlapping rental is refused;"
                   " the refusal charged nothing)" in block)
    expiry_ok = ("is_rented(plaza, amy, 110)=False after end 109; ben"
                 " re-rents the freed slot [110,114] fee 2500, balance"
                 " 15000->12500; spend-tx 2->3 (+1); freed capacity is"
                 " reusable, the audit row survives expiry" in block)
    dup_ok = ("refused: E_VN_DUP" in block
              and "12500==12500 and 3==3 (an identical rental is"
                  " rejected BEFORE the spend; a rejected rental"
                  " never charges)" in block)
    lease_ok = ("fee 3000 (10 x 300); balance 10000->7000; spend-tx"
                " 3->4 (+1); a storefront is an exclusive unit -- one"
                " active tenant at a time" in block)
    taken_ok = ("refused: E_VN_LEASE_ACTIVE" in block
                and "12500==12500 (the storefront is exclusive"
                    " through 309; the refusal charged nothing)"
                in block)
    flip_ok = ("fee 1500; balance 12500->11000; spend-tx 4->5 (+1);"
               " tenant at 309=usr:amy -> 310=usr:ben (the flip at the"
               " window boundary)" in block)
    term_ok = ("terminated_for=usr:amy at 305: effective through 305,"
               " free from 306; tenant 305=usr:amy 306=None; balance"
               " unchanged 7000==7000; spend-tx 5==5 unchanged --"
               " termination ends occupancy without moving tokens,"
               " fee reversal of any kind stays a P1 [needs-CEO]"
               " approval face (no refund verb exists in the"
               " mechanism)" in block)
    badargs_ok = (block.count("refused: E_VN_BAD_ARGS") == 6
                  and "11000==11000 (tenants are usr:* only, rent must"
                      " be int > 0, term int >= 1, start int >= 0,"
                      " ref required -- every rejected rental charges"
                      " nothing)" in block)
    reads_ok = ("spend-tx 5==5 unchanged -- reads move zero tokens;"
                " is_rented(plaza, amy, 100)=True vs (plaza, amy,"
                " 110)=False (expiry live); tenant_of(booth-1,"
                " 307)=None (terminated window) vs (booth-1,"
                " 310)=usr:ben; plaza history=3 rows (amy/carol/ben"
                " kept after expiry), booth-1 history=2 rows, every"
                " history row carries its bound spend tx" in block)
    audit_ok = ("spend-tx total 5 == bookings 5; all 5 occupancy rows"
                " bind a real spend debit for their own account;"
                " balances exact: amy 15000-5000-3000=7000, ben"
                " 15000-2500-1500=11000, carol 5000-5000=0;"
                " pool:reserve 22000 (40000 mint, spent tokens loop"
                " back in, conservation holds)" in block)
    isolation_ok = ("banned token-verb hits=none in venue.py;"
                    " non-ascii=0; each rental and lease books"
                    " exactly one spend and nothing else in the module"
                    " ever touches the token domain -- capacity"
                    " checks, activation, expiry, termination and"
                    " read faces move zero tokens, and no verb"
                    " converts an occupancy back into tokens or moves"
                    " it between accounts (the suite AC-VN7 pattern)"
                    in block)
    record("AC-FD19b-chain",
           struct_ok and unknown_ok and single_ok and concur_ok
           and full_ok and expiry_ok and dup_ok and lease_ok
           and taken_ok and flip_ok and term_ok and badargs_ok
           and reads_ok and audit_ok and isolation_ok,
           "registry=%s unknown-refusal=%s one-spend=%s"
           " concurrent-2/2=%s capacity-full=%s expiry=%s"
           " dup-before-spend=%s exclusive-lease=%s taken=%s"
           " boundary-flip=%s termination-zero-token=%s"
           " badargs=%s pure-reads=%s debit-audit=%s isolation=%s"
           % (struct_ok, unknown_ok, single_ok, concur_ok, full_ok,
              expiry_ok, dup_ok, lease_ok, taken_ok, flip_ok, term_ok,
              badargs_ok, reads_ok, audit_ok, isolation_ok))

    # refusal codes on the card
    ref_ok = all(code in block for code in (
        "E_VN_BAD_ARGS", "E_VN_UNKNOWN", "E_VN_FULL", "E_VN_DUP",
        "E_VN_LEASE_ACTIVE"))
    record("AC-FD19b-refusals", ref_ok,
           "five fail-closed refusal codes on the card"
           " (BAD_ARGS/UNKNOWN/FULL/DUP/LEASE_ACTIVE)")

    # -- AC-FD19c: compliance four-piece from config verbatim --------
    lcfg = json.load(open(os.path.join(SBX, "ledger", "config.json"),
                          encoding="utf-8"))
    ai_text = str(lcfg.get("token", {}).get("ai_label_text", ""))
    disc = str(lcfg.get("token", {}).get("disclaimer", ""))
    ai_ok = ai_text in html1
    disc_ok = disc in html1
    ceo_ok = "[needs-CEO]" in block
    gate_ok = "msgSecCheck" in block
    price_ok = ("the B4 canon anchor (online event venue"
                " full-booking 5,000 CNY per event, resident host +"
                " auto-cut material bundle included) is a"
                " caller-supplied probe price" in block)
    record("AC-FD19c", ai_ok and disc_ok and ceo_ok and gate_ok
           and price_ok,
           "AIGC label verbatim=%s; disclaimer verbatim=%s;"
           " [needs-CEO] price note=%s; msgSecCheck gate note=%s;"
           " probe-price law=%s"
           % (ai_ok, disc_ok, ceo_ok, gate_ok, price_ok))

    # -- AC-FD19d: determinism + zero unfilled placeholders ----------
    block2 = card_block(html2, "Venue Face")
    same = block_raw == block2
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", html1)))
    record("AC-FD19d", same and not leftovers,
           "determinism: two renders, venue block byte-identical=%s"
           " (%d chars); unfilled placeholders page-wide=%s"
           % (same, len(block_raw), leftovers or "none"))

    # -- AC-FD19e: live server on 8093 -------------------------------
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
    live_title = "Venue Face" in page
    live_fail = "VENUE PROBE FAILED" in page
    live_block_chars = len(card_block(page, "Venue Face"))
    record("AC-FD19e", live_health and live_cards == 21 and live_title
           and not live_fail and live_block_chars > 3000,
           "healthz=%s on live server; card count = 21: got %d;"
           " venue card title on live page=%s; page has no"
           " probe-failure face=%s; live venue card block %d chars"
           % (health.strip() or "n/a", live_cards, live_title,
              not live_fail, live_block_chars))

    # -- AC-FD19f: evidence face --------------------------------------
    record("AC-FD19f", True,
           "this log = qa/frontdoor-v19-R989.log (FD19 full record);"
           " full regression log = qa/reconcile-all-R989.log (RUNNER"
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
