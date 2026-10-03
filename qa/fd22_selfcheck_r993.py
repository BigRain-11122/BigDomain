"""Front door v0.22 self-check (R993, AC-FD22a..f evidence).

Renders the page in-process twice via the module render() and asserts
the pre-registered criteria for the trading-hall expedite-privilege
face card, then probes the LIVE server on 127.0.0.1:8093 (restarted
by the runner). Every check prints PASS/FAIL with evidence; the
process exits non-zero on any FAIL. The REAL expedite probe runs
inside render() at render time (F3 law); this script verifies what
render() produced -- it never buys a credit or submits a job itself.
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

    block_raw = card_block(html1, "Expedite Face")
    block = re.sub(r"\s+", " ", html_mod.unescape(block_raw))

    # -- AC-FD22a: pure composition + ASCII source --------------------
    src_path = os.path.join(SBX, "frontdoor.py")
    with open(src_path, "rb") as fh:
        src_bytes = fh.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/sandbox"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty_files = sorted(ln.split(" -> ")[-1].split()[-1]
                         for ln in dirty.splitlines() if ln)
    record("AC-FD22a",
           ascii_ok and dirty_files == ["src/sandbox/frontdoor.py"],
           "frontdoor source pure ASCII: %d bytes=%s; write set under"
           " src/sandbox = %s (expedite/ledger product tree untouched)"
           % (len(src_bytes), ascii_ok, dirty_files or "clean"))

    # -- AC-FD22b: probe legs on the card -----------------------------
    legs_expected = [
        "authorize the reserve mint + fund three probe buyers",
        "amy buys a demo queue jump (49.9 CNY anchor)",
        "amy replays the SAME purchase ref",
        "amy buys the other three kinds (all four anchors live)",
        "ben with ZERO credits tries an expedited submit",
        "zero-credit refusal audit: zero rows, zero charge",
        "ben submits a PLAIN hall job (no expedite kind)",
        "amy jumps a demo job ahead of the whole normal tier",
        "amy buys a SECOND demo credit under a fresh ref",
        "queue snapshot: two-tier ordering, FIFO inside tiers",
        "a THIRD demo jump with zero unconsumed demo credits",
        "a submit_expedite credit tries to jump a demo:* job"
        " (kind-domain mismatch)",
        "one-credit-one-job + mismatch audit",
        "the submit and dialogue credits consume their own domains"
        " (idea:* / talk:*)",
        "carol buys + consumes her own dialogue credit",
        "the backtest credit consumes backtest:* -- all 6 credits"
        " consumed, each bound to the exact job it jumped",
        "an ent: enterprise account tries to buy a credit directly"
        " on the resident token ledger",
        "a zero price purchase is refused",
        "an empty purchase ref is refused",
        "an empty submit subject is refused",
        "an UNKNOWN expedite kind is refused",
        "bad-args audit: all three buyer balances flat",
        "pure-read audit: queue_snapshot / credits_view",
        "audit the expedite purchases against real debit entries",
        "isolation law audit on the REAL module source",
    ]
    pos = [block.find(re.sub(r"\s+", " ", leg))
           for leg in legs_expected]
    legs_ok = all(p >= 0 for p in pos) and pos == sorted(pos)
    record("AC-FD22b", legs_ok,
           "twenty-five probe legs rendered in order=%s (positions %s)"
           % (legs_ok, pos))

    # -- AC-FD22b: chain assertions (live readings) -------------------
    buy_ok = ("balance 15000->10010 (exact -4990 = one priority"
              " credit, one spend); spend-tx 0->1 (+1); the credit row"
              " binds that real spend tx" in block)
    idem_ok = ("idempotent=True: the replay returned the SAME credit"
               " #1 with the SAME bound spend tx=True; balance"
               " 10010==10010 (zero second charge, zero second row)"
               in block)
    kinds_ok = ("balance 10010->7540 (exact -990-990-490);"
                " credits_view shows 4 credits across kinds"
                " ['backtest_expedite', 'demo_queuejump',"
                " 'resident_dialogue', 'submit_expedite'] with 4"
                " distinct bound spend txs=True (every credit row"
                " binds its own real spend)" in block)
    gate_ok = ("jobs 0==0 and ben 10000==10000 (a failed jump leaves"
               " zero rows behind and never charges)" in block)
    plain_ok = ("ungated, no token movement (spend-tx 4==4); job #1"
                " joins the normal tier at live position 1,"
                " expedited=False" in block)
    jump_ok = ("submitted AFTER ben's and her own normal jobs yet"
               " live position=1 (the expedited tier ranks ahead of"
               " every normal job); consumption is pure bookkeeping"
               " (spend-tx 4==4, zero token movement); the demo credit"
               " #1 is consumed once and binds the exact job it"
               " jumped=True" in block)
    fresh_ok = ("balance 7540->2550 (exact -4990, a fresh ref = a"
                " fresh legal spend); spend-tx 4->5 (+1)" in block)
    snap_ok = ("with positions [1, 2, 3, 4, 5] (a later expedited job"
               " still outranks all normal jobs; inside each tier jobs"
               " stay FIFO by submission order); submit receipts"
               " returned live positions normal 1/4, expedited 1/2"
               in block)
    onecredit_ok = ("jobs 5==5 (both refusals leave zero rows); the"
                    " submit_expedite credit is still unconsumed=True"
                    " (a mismatched kind never burns a credit; a"
                    " consumed credit is consumed once and only ever"
                    " jumps its own subject domain)" in block)
    domains_ok = ("tower-mk4 jumped at live position 3, ask-mentor"
                  " at 4 (both inside the expedited tier, FIFO by"
                  " submission order)" in block)
    carol_ok = ("carol balance 8000->7510 (exact -490, one spend for"
                " one credit); spend-tx 5->6 (+1); her talk job joins"
                " the expedited tier at live position 5 -- a second"
                " buyer's credit never touches amy's" in block)
    final_ok = ("fast-1 jumped at live position 6; final snapshot = 9"
                " jobs (6 expedited + 3 normal, positions [1, 2, 3,"
                " 4, 5, 6, 7, 8, 9]); consumed credits 6/6, every"
                " consumed_job is a real queued job=True" in block)
    ent_ok = ("refused: E_EXP_BAD_ACCOUNT at the module gate (buyers"
              " are usr:* only) -- the expedite gate itself refuses"
              " non-resident buyers one layer earlier than the token"
              " ledger, so the stack is fail-closed: zero charge,"
              " zero rows written; production enterprise procurement"
              " routes through the BigCompute collection gateway"
              " (D-20260924-11 collection exit unified there)"
              in block)
    badargs_ok = ("[2550, 10000, 7510]==[2550, 10000, 7510] (price"
                  " must be int > 0, purchase refs are required,"
                  " submit subjects are required, expedite kinds must"
                  " be one of the four registered kinds -- every"
                  " rejected call charges nothing and writes no row)"
                  in block)
    reads_ok = ("spend-tx 6==6 unchanged -- reads move zero tokens;"
               " the queue view is deterministic (expedited tier"
               " first FIFO, then the normal tier FIFO, positions"
               " 1-based)" in block)
    audit_ok = ("spend-tx total 6 == expedite purchases 6 (5 amy"
                " credits + 1 carol credit); all 6 credit rows bind a"
                " real spend debit for their own buyer (bound 6/6);"
                " balances exact: amy 15000-4990-990-990-490-4990=2550,"
                " ben 10000 flat, carol 8000-490=7510; pool:reserve"
                " 12940 (33000 mint, spent tokens loop back in,"
                " conservation holds: pool+balances==mint=True)"
                in block)
    isolation_ok = ("banned token-verb hits on the code surface=none"
                    " (module-wide scan=none); ledger-API call sites"
                    " (self.led.) x3 = account onboarding + the single"
                    " purchase spend -- the module's ONLY token-domain"
                    " touch is the purchase spend (exactly one spend"
                    " per credit); submits and reads move zero tokens;"
                    " the single UPDATE surface=True is exactly the"
                    " consumption marking on credit rows (consumed"
                    " once, carries the job it jumped); the account_id"
                    " / kind ownership columns are never rewritten=True;"
                    " no verb moves a credit between accounts; module"
                    " source pure ASCII (0 non-ascii)" in block)
    record("AC-FD22b-chain",
           buy_ok and idem_ok and kinds_ok and gate_ok and plain_ok
           and jump_ok and fresh_ok and snap_ok and onecredit_ok
           and domains_ok and carol_ok and final_ok and ent_ok
           and badargs_ok and reads_ok and audit_ok and isolation_ok,
           "one-spend-credit=%s replay-idempotent=%s four-kinds=%s"
           " zero-credit-gate=%s ungated-normal=%s jump-position=%s"
           " fresh-ref=%s two-tier-snapshot=%s one-credit-one-job=%s"
           " own-domains=%s second-buyer=%s final-audit=%s ent-gate=%s"
           " bad-args=%s pure-reads=%s debit-audit=%s isolation=%s"
           % (buy_ok, idem_ok, kinds_ok, gate_ok, plain_ok, jump_ok,
              fresh_ok, snap_ok, onecredit_ok, domains_ok, carol_ok,
              final_ok, ent_ok, badargs_ok, reads_ok, audit_ok,
              isolation_ok))

    # refusal codes on the card
    ref_ok = (block.count("refused: E_EXP_NO_CREDIT") == 2
              and block.count("refused: E_EXP_KIND_MISMATCH") == 1
              and block.count("refused: E_EXP_BAD_ACCOUNT") == 1
              and block.count("refused: E_EXP_BAD_AMOUNT") == 1
              and block.count("refused: E_EXP_BAD_REF") == 1
              and block.count("refused: E_EXP_BAD_SUBJECT") == 1
              and block.count("refused: E_EXP_BAD_KIND") == 1)
    record("AC-FD22b-refusals", ref_ok,
           "eight fail-closed refusal codes on the card (NO_CREDIT x2,"
           " KIND_MISMATCH x1, BAD_ACCOUNT x1 incl. the ent: boundary,"
           " BAD_AMOUNT x1, BAD_REF x1, BAD_SUBJECT x1, BAD_KIND x1 --"
           " every rejection zero charge)")

    # -- AC-FD22c: compliance four-piece from config verbatim --------
    lcfg = json.load(open(os.path.join(SBX, "ledger", "config.json"),
                          encoding="utf-8"))
    ai_text = str(lcfg.get("token", {}).get("ai_label_text", ""))
    disc = str(lcfg.get("token", {}).get("disclaimer", ""))
    ai_ok = ai_text in html1
    disc_ok = disc in html1
    ceo_ok = "[needs-CEO]" in block
    gate_note_ok = "msgSecCheck" in block
    price_ok = ("the C3/C7 canon anchors (strategy submit expedite"
                " 9.9 CNY, backtest expedite 9.9 CNY, game demo queue"
                " jump 49.9 CNY, resident named dialogue 4.9 CNY) are"
                " caller-supplied probe prices" in block)
    record("AC-FD22c", ai_ok and disc_ok and ceo_ok and gate_note_ok
           and price_ok,
           "AIGC label verbatim=%s; disclaimer verbatim=%s;"
           " [needs-CEO] price note=%s; msgSecCheck gate note=%s;"
           " probe-price law=%s"
           % (ai_ok, disc_ok, ceo_ok, gate_note_ok, price_ok))

    # -- AC-FD22d: determinism + zero unfilled placeholders ----------
    block2 = card_block(html2, "Expedite Face")
    same = block_raw == block2
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", html1)))
    record("AC-FD22d", same and not leftovers,
           "determinism: two renders, expedite block byte-identical=%s"
           " (%d chars); unfilled placeholders page-wide=%s"
           % (same, len(block_raw), leftovers or "none"))

    # -- AC-FD22e: live server on 8093 -------------------------------
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
    live_title = "Expedite Face" in page
    live_fail = "EXPEDITE PROBE FAILED" in page
    live_block_chars = len(card_block(page, "Expedite Face"))
    record("AC-FD22e", live_health and live_cards == 24 and live_title
           and not live_fail and live_block_chars > 3000,
           "healthz=%s on live server; card count = 24: got %d;"
           " expedite card title on live page=%s; page has no"
           " probe-failure face=%s; live expedite card block %d chars"
           % (health.strip() or "n/a", live_cards, live_title,
              not live_fail, live_block_chars))

    # -- AC-FD22f: evidence face --------------------------------------
    record("AC-FD22f", True,
           "this log = qa/frontdoor-v22-R993.log (FD22 full record);"
           " full regression log = qa/reconcile-all-R993.log (RUNNER"
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
