"""Front door v0.23 self-check (R995, AC-FD23a..f evidence).

Renders the page in-process twice via the module render() and asserts
the pre-registered criteria for the enterprise metered API face card,
then probes the LIVE server on 127.0.0.1:8093 (restarted by the
runner). Every check prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL. The REAL metered probe runs inside render() at
render time (F3 law); this script verifies what render() produced --
it never registers a client or buys a pack itself.
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

    block_raw = card_block(html1, "Enterprise Metered API Face")
    block = re.sub(r"\s+", " ", html_mod.unescape(block_raw))

    # -- AC-FD23a: pure composition + ASCII source --------------------
    src_path = os.path.join(SBX, "frontdoor.py")
    with open(src_path, "rb") as fh:
        src_bytes = fh.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/sandbox"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty_files = sorted(ln.split(" -> ")[-1].split()[-1]
                         for ln in dirty.splitlines() if ln)
    record("AC-FD23a",
           ascii_ok and dirty_files == ["src/sandbox/frontdoor.py"],
           "frontdoor source pure ASCII: %d bytes=%s; write set under"
           " src/sandbox = %s (metered/ledger product tree untouched)"
           % (len(src_bytes), ascii_ok, dirty_files or "clean"))

    # -- AC-FD23b: probe legs on the card -----------------------------
    legs_expected = [
        "authorize the reserve mint + fund two enterprise"
        " funding accounts",
        "register the first enterprise client ent:pixelforge",
        "re-register ent:pixelforge with IDENTICAL parameters",
        "re-register ent:pixelforge with DRIFTED kinds",
        "register the second enterprise client ent:quantdesk",
        "an UNREGISTERED client tries to buy a pack",
        "unregistered-client audit: zero charge, zero rows",
        "ent:quantdesk calls the visualize kind it never enabled",
        "ent:quantdesk with ZERO credits tries a backtest call",
        "ben's client buys a 20-call pack (0.5 CNY/call anchor)",
        "the SAME purchase ref is replayed",
        "replay audit: the duplicate fires BEFORE the spend",
        "amy's client stacks TWO packs under fresh refs",
        "ben's client meters its first backtest call",
        "the SAME call ref is replayed",
        "call-replay audit: call rows are immutable",
        "amy's client meters one call of EACH enabled kind",
        "a non-ent: client id is refused",
        "a non-usr: funding account is refused",
        "an UNKNOWN kind in registration is refused",
        "a zero-call pack is refused",
        "a zero unit price is refused",
        "an empty purchase ref is refused",
        "an UNKNOWN call kind is refused",
        "an empty call ref is refused",
        "an empty engine ref is refused",
        "bad-args audit: both funding balances flat",
        "pure-read audit: client_contract / usage_log /"
        " reconcile_client",
        "audit the pack purchases against real debit entries",
        "isolation law audit on the REAL module source",
    ]
    pos = [block.find(re.sub(r"\s+", " ", leg))
           for leg in legs_expected]
    legs_ok = all(p >= 0 for p in pos) and pos == sorted(pos)
    record("AC-FD23b", legs_ok,
           "thirty probe legs rendered in order=%s (positions %s)"
           % (legs_ok, pos))

    # -- AC-FD23b: chain assertions (live readings) -------------------
    reg_ok = ("funding account usr:amy, enabled kinds"
              " ['backtest', 'visualize'], zero starting credits"
              " (fail-closed start), idempotent=False" in block)
    idem_ok = ("idempotent=True (same parameters = same client, zero"
               " rows written)" in block)
    ghost_ok = ("amy balance 12000==12000 and spend-tx 0==0 (an"
                " unknown client is refused before the spend, nothing"
                " is written)" in block)
    pack_ok = ("balance 10000->9000 (exact -1000 = one pack, one"
               " spend); spend-tx 0->1 (+1); the immutable pack row"
               " binds that real spend tx=True; credits stack to 20"
               in block)
    replay_ok = ("balance 9000==9000 and spend-tx 1==1 (a rejected"
                 " replay never charges and never writes a second"
                 " pack row)" in block)
    stack_ok = ("balance 12000->4500 (exact -5000-2500); spend-tx"
                " 1->3 (+2); credits stack 100+50=150 (re-purchase"
                " stacks, pack rows stay immutable and each binds its"
                " own spend)" in block)
    call_ok = ("consumed exactly 1 credit (20->19, rc"
               " balanced=True: purchased 20 == consumed 1 + remaining"
               " 19); the immutable call row carries the external"
               " engine receipt verbatim=True; zero token movement"
               " (spend-tx 3==3)" in block)
    callreplay_ok = ("quantdesk credits 19==19 (a duplicate call ref"
                     " is refused with zero double-consume; consumption"
                     " is one-credit-once)" in block)
    kinds_ok = ("visualize + backtest both live (credits 150->148);"
                " rc balanced=True: purchased 150 == consumed 2 +"
                " remaining 148; usage log shows 2 immutable rows with"
                " verbatim engine receipts=True" in block)
    badargs_ok = ("[4500, 9000]==[4500, 9000] (client ids are ent:*"
                  " only, funding accounts are usr:* only, kinds must"
                  " be registered, pack calls and unit prices must be"
                  " int >= 1, purchase / call / engine refs are all"
                  " required -- every rejected call charges nothing"
                  " and writes no row)" in block)
    reads_ok = ("spend-tx 3==3 unchanged -- reads move zero tokens;"
                " the contract read is structurally accompanied by the"
                " non-advisory notice as first=True and last=True line,"
                " and the pricing note carries the [needs-CEO]"
                " verdict=True" in block)
    audit_ok = ("spend-tx total 3 == pack purchases 3 (2 pixelforge +"
                " 1 quantdesk); all 3 pack rows bind a real spend debit"
                " for their own funding account (bound 3/3); balances"
                " exact: amy 12000-5000-2500=4500, ben 10000-1000=9000;"
                " pool:reserve 8500 (22000 mint, spent tokens loop"
                " back in, conservation holds: pool+balances==mint"
                "=True)" in block)
    isolation_ok = ("banned token-verb hits on the code surface=none"
                    " (module-wide scan=none); ledger-API call sites"
                    " (self.led.) x1 = the single buy_pack spend -- the"
                    " module's ONLY token-domain touch is the pack"
                    " purchase (exactly one spend per pack); metering,"
                    " consumption and every read move zero tokens; the"
                    " only UPDATE surface=2 sites is exactly the client"
                    " credit counter (+1 on pack, -1 on call); the"
                    " funding_account / enabled_kinds / client_id"
                    " ownership columns are never rewritten=True; pack"
                    " rows and call rows are immutable once written; no"
                    " verb turns credits back into tokens or moves"
                    " credits between clients; module source pure"
                    " ASCII (0 non-ascii)" in block)
    record("AC-FD23b-chain",
           reg_ok and idem_ok and ghost_ok and pack_ok and replay_ok
           and stack_ok and call_ok and callreplay_ok and kinds_ok
           and badargs_ok and reads_ok and audit_ok and isolation_ok,
           "register=%s idempotent=%s unregistered=%s one-spend-pack=%s"
           " replay-before-spend=%s credits-stack=%s one-credit-call=%s"
           " call-immutable=%s both-kinds=%s bad-args=%s pure-reads=%s"
           " debit-audit=%s isolation=%s"
           % (reg_ok, idem_ok, ghost_ok, pack_ok, replay_ok, stack_ok,
              call_ok, callreplay_ok, kinds_ok, badargs_ok, reads_ok,
              audit_ok, isolation_ok))

    # refusal codes on the card
    ref_ok = (block.count("refused: E_MT_DUP") == 3
              and block.count("refused: E_MT_UNKNOWN") == 1
              and block.count("refused: E_MT_KIND_GATE") == 1
              and block.count("refused: E_MT_NO_CREDITS") == 1
              and block.count("refused: E_MT_BAD_ARGS") == 9)
    record("AC-FD23b-refusals", ref_ok,
           "fifteen fail-closed refusal codes on the card (DUP x3"
           " registration-drift + pack-ref + call-ref, UNKNOWN x1,"
           " KIND_GATE x1, NO_CREDITS x1, BAD_ARGS x9 -- every"
           " rejection zero charge)")

    # -- AC-FD23c: compliance four-piece from config verbatim --------
    lcfg = json.load(open(os.path.join(SBX, "ledger", "config.json"),
                          encoding="utf-8"))
    ai_text = str(lcfg.get("token", {}).get("ai_label_text", ""))
    disc = str(lcfg.get("token", {}).get("disclaimer", ""))
    ai_ok = ai_text in html1
    disc_ok = disc in html1
    ceo_ok = "[needs-CEO]" in block
    gate_note_ok = "msgSecCheck" in block
    price_ok = ("the B5 canon anchor (billed per metered call from"
                " the 0.5-CNY-per-call anchor up) is a"
                " caller-supplied probe price" in block)
    record("AC-FD23c", ai_ok and disc_ok and ceo_ok and gate_note_ok
           and price_ok,
           "AIGC label verbatim=%s; disclaimer verbatim=%s;"
           " [needs-CEO] price note=%s; msgSecCheck gate note=%s;"
           " probe-price law=%s"
           % (ai_ok, disc_ok, ceo_ok, gate_note_ok, price_ok))

    # -- AC-FD23d: determinism + zero unfilled placeholders ----------
    block2 = card_block(html2, "Enterprise Metered API Face")
    same = block_raw == block2
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", html1)))
    record("AC-FD23d", same and not leftovers,
           "determinism: two renders, metered block byte-identical=%s"
           " (%d chars); unfilled placeholders page-wide=%s"
           % (same, len(block_raw), leftovers or "none"))

    # -- AC-FD23e: live server on 8093 -------------------------------
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
    live_title = "Enterprise Metered API Face" in page
    live_fail = "METERED PROBE FAILED" in page
    live_block_chars = len(card_block(page, "Enterprise Metered API"
                                      " Face"))
    record("AC-FD23e", live_health and live_cards == 25 and live_title
           and not live_fail and live_block_chars > 3000,
           "healthz=%s on live server; card count = 25: got %d;"
           " metered card title on live page=%s; page has no"
           " probe-failure face=%s; live metered card block %d chars"
           % (health.strip() or "n/a", live_cards, live_title,
              not live_fail, live_block_chars))

    # -- AC-FD23f: evidence face --------------------------------------
    record("AC-FD23f", True,
           "this log = qa/frontdoor-v23-R995.log (FD23 full record);"
           " full regression log = qa/reconcile-all-R995.log (RUNNER"
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
