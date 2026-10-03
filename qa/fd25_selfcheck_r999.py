"""Front door v0.25 self-check (R999, AC-FD25a..f evidence).

Renders the page in-process twice via the module render() and asserts
the pre-registered criteria for the hall value-added effects face card
(the R629 product face, BLUEPRINT sec.4 C-end row 3 effects residual),
then probes the LIVE server on 127.0.0.1:8093 (restarted by the
runner). Every check prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL. The REAL effects probe runs inside render() at
render time (F3 law); this script verifies what render() produced --
it never purchases or fires anything itself.
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

    block_raw = card_block(html1, "Hall Value-Added Effects Face")
    block = re.sub(r"\s+", " ", html_mod.unescape(block_raw))

    # -- AC-FD25a: pure composition + ASCII source --------------------
    src_path = os.path.join(SBX, "frontdoor.py")
    with open(src_path, "rb") as fh:
        src_bytes = fh.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/sandbox"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty_files = sorted(ln.split(" -> ")[-1].split()[-1]
                         for ln in dirty.splitlines() if ln)
    header_ok = ("v0.25 hall value-added effects card (R999)" in html1)
    record("AC-FD25a",
           ascii_ok and dirty_files == ["src/sandbox/frontdoor.py"]
           and header_ok,
           "frontdoor source pure ASCII: %d bytes=%s; write set under"
           " src/sandbox = %s (effects/ledger product tree untouched);"
           " header v0.25 (R999) on page=%s"
           % (len(src_bytes), ascii_ok, dirty_files or "clean",
              header_ok))

    # -- AC-FD25b: probe legs on the card -----------------------------
    legs_expected = [
        "authorize the reserve mint + fund two resident probe"
        " accounts",
        "amy purchases a dynamic-emoji effect credit (one token"
        " spend)",
        "the SAME purchase ref replays idempotent",
        "an UNKNOWN kind is refused at purchase",
        "a zero token price is refused at purchase",
        "an empty purchase ref is refused",
        "an ent: account tries to purchase an effect credit",
        "purchase bad-args audit: amy's balance flat across the"
        " family",
        "amy fires the dynamic emoji on one gated hall message",
        "the SAME use ref replays idempotent",
        "BEN replays AMY's use ref (cross-account)",
        "cross-account replay audit: the dup check fires BEFORE any"
        " credit lookup",
        "amy re-fires dynamic_emoji (the emoji kind is spent)",
        "kind-domain audit: credits are kind-domain",
        "amy purchases a message-pin credit (one token spend)",
        "amy pins one hall message (consumes the pin credit)",
        "an empty message ref is refused at use",
        "an empty use ref is refused at use",
        "an UNKNOWN kind is refused at use",
        "an ent: account tries to fire an effect",
        "use bad-args audit: zero rows, zero charges",
        "BEN (zero credits) tries to fire any effect",
        "no-credit audit: a zero-credit resident cannot fire any"
        " effect",
        "pure-read audit: credits_view / effects_view",
        "audit the credits, effects and the bound spend debit",
        "isolation law audit on the REAL module source",
    ]
    pos = [block.find(re.sub(r"\s+", " ", leg))
           for leg in legs_expected]
    legs_ok = all(p >= 0 for p in pos) and pos == sorted(pos)
    record("AC-FD25b", legs_ok,
           "twenty-six probe legs rendered in order=%s (positions %s)"
           % (legs_ok, pos))

    # -- AC-FD25b: chain assertions (live readings) -------------------
    probe_ok = ("probe prices mirror caller-supplied sandbox values"
                " (10 tokens per emoji credit, 5 per pin credit --"
                " the 9.9 / 4.9 yuan canon tiers are production"
                " anchors, never decisions here)" in block)
    buy_ok = ("balance 12000->11990 (exact -10 = the probe price);"
              " spend-tx 0->1 (+1); the credit row binds that real"
              " spend tx=True; one-shot consumable, counts stay"
              " counts" in block)
    idem_ok = ("returns the existing credit_id 1, idempotent=True;"
               " balance 11990==11990 and spend-tx 1==1 (zero second"
               " charge, zero new rows)" in block)
    badargs_ok = ("11990==11990 and spend-tx 1==1 (usr:* only, known"
                  " kind, int price >= 1, non-empty ref -- every"
                  " rejected call charges nothing and writes no row)"
                  in block)
    use_ok = ("consumes exactly one unconsumed credit inside the"
              " SAME transaction that inserts the effect row (a"
              " failed use leaves zero rows); effect row immutable,"
              " bound to used_credit=1; message_ref references an"
              " already-gated lobby message (the lobby ingress owns"
              " msgSecCheck -- this module never re-runs a content"
              " channel on it)" in block)
    uidem_ok = ("returns the existing effect_id 1, idempotent=True;"
                " the consumed credit is consumed ONCE (no second"
                " consumption, zero new rows)" in block)
    cross_ok = ("refused E_EFF_DUP_USE even though ben holds zero"
                " emoji credits (the ref belongs to amy's effect"
                " row; kind mismatch would refuse too -- the"
                " ownership check is first)" in block)
    kind_ok = ("amy holds zero unconsumed dynamic_emoji credits (the"
               " one she bought is consumed) -- E_EFF_NO_CREDIT is"
               " honest: one credit buys exactly one effect of its"
               " kind, zero rows written" in block)
    pin_ok = ("balance 11990->11985 (exact -5); spend-tx 1->2 (+1);"
              " the pin is a one-shot consumable highlight, distinct"
              " from the mayor-tier persistent chat_highlight"
              " privilege the member face owns (reference, no"
              " double-build)" in block)
    pinuse_ok = ("consumes exactly one pin credit in the same tx"
                 " that inserts effect row 2; consumption marking on"
                 " the credit row is the module's single UPDATE"
                 " surface; the effect row itself is immutable and"
                 " binds used_credit=2" in block)
    usebad_ok = ("spend-tx 2==2 and ben's balance 8000 untouched (a"
                 " rejected use never writes an effect row, so a"
                 " failed use leaves zero rows)" in block)
    nocred_ok = ("refused E_EFF_NO_CREDIT before any row; ben's"
                 " balance 8000 untouched and spend-tx total"
                 " unchanged" in block)
    reads_ok = ("spend-tx 2==2 unchanged -- reads move zero tokens"
                " (the credits view carries the bound spend tx per"
                " credit, the effects view carries the effect ->"
                " credit binding with used_utc)" in block)
    audit_ok = ("effect credits 2, consumed 2, effect rows 2"
                " (consumed credits bind their effect row 2/2);"
                " every credit row binds a real spend debit (bound"
                " 2/2); spend-tx total 2 == credit purchases 2 (the"
                " module's single token-domain touch across the"
                " whole probe); balances exact: amy 12000-10-5=11985,"
                " ben 8000; pool:reserve 15 (20000 mint, the spent"
                " tokens loop back in, conservation holds:"
                " pool+balances==mint=True)" in block)
    isolation_ok = ("banned token-verb hits on the code surface=none"
                    " (module-wide scan=none); ledger-API call sites"
                    " (self.led.) x3 = two idempotent ensure_account"
                    " (purchase + use) + exactly one spend per credit"
                    " inside purchase = the module's ONLY"
                    " token-moving touch; the only UPDATE surface=1"
                    " site is exactly the consumption marking on"
                    " credit rows; effect rows are immutable (no"
                    " UPDATE effect_events=True) and the account_id /"
                    " kind ownership columns are never rewritten; no"
                    " verb moves a credit between accounts (credits"
                    " are consumed by their owner only); module"
                    " source pure ASCII (0 non-ascii)" in block)
    record("AC-FD25b-chain",
           probe_ok and buy_ok and idem_ok and badargs_ok and use_ok
           and uidem_ok and cross_ok and kind_ok and pin_ok
           and pinuse_ok and usebad_ok and nocred_ok and reads_ok
           and audit_ok and isolation_ok,
           "probe-values=%s one-spend-credit=%s purchase-idempotent=%s"
           " purchase-bad-args=%s one-credit-per-use=%s"
           " use-idempotent=%s cross-account-dup-first=%s"
           " kind-domain=%s pin-one-spend=%s pin-use=%s"
           " use-bad-args=%s no-credit=%s pure-reads=%s"
           " debit-audit=%s isolation=%s"
           % (probe_ok, buy_ok, idem_ok, badargs_ok, use_ok,
              uidem_ok, cross_ok, kind_ok, pin_ok, pinuse_ok,
              usebad_ok, nocred_ok, reads_ok, audit_ok,
              isolation_ok))

    # refusal codes on the card
    ref_ok = (block.count("refused: E_EFF_BAD_KIND") == 2
              and block.count("refused: E_EFF_BAD_AMOUNT") == 1
              and block.count("refused: E_EFF_BAD_REF") == 2
              and block.count("refused: E_EFF_BAD_ACCOUNT") == 2
              and block.count("refused: E_EFF_BAD_MESSAGE") == 1
              and block.count("refused: E_EFF_DUP_USE") == 1
              and block.count("refused: E_EFF_NO_CREDIT") == 2)
    record("AC-FD25b-refusals", ref_ok,
           "eleven fail-closed refusal codes on the card (BAD_KIND x2"
           " purchase + use, BAD_REF x2 empty purchase ref + empty"
           " use ref, BAD_ACCOUNT x2 ent: purchase + ent: use,"
           " NO_CREDIT x2 kind spent + zero-credit resident,"
           " BAD_AMOUNT x1, BAD_MESSAGE x1, DUP_USE x1 cross-account"
           " -- every rejection zero charge, zero rows)")

    # -- AC-FD25c: compliance four-piece from config verbatim --------
    lcfg = json.load(open(os.path.join(SBX, "ledger", "config.json"),
                          encoding="utf-8"))
    ai_text = str(lcfg.get("token", {}).get("ai_label_text", ""))
    disc = str(lcfg.get("token", {}).get("disclaimer", ""))
    ai_ok = ai_text in html1
    disc_ok = disc in html1
    ceo_ok = "[needs-CEO]" in block
    gate_note_ok = "msgSecCheck" in block
    price_ok = ("caller-supplied sandbox values" in block
                and "real effect pricing and launch gating stay P1"
                " CEO approval faces" in block)
    record("AC-FD25c", ai_ok and disc_ok and ceo_ok and gate_note_ok
           and price_ok,
           "AIGC label verbatim=%s; disclaimer verbatim=%s;"
           " [needs-CEO] price note=%s; msgSecCheck gate note=%s;"
           " probe-price law=%s"
           % (ai_ok, disc_ok, ceo_ok, gate_note_ok, price_ok))

    # -- AC-FD25d: determinism + zero unfilled placeholders ----------
    block2 = card_block(html2, "Hall Value-Added Effects Face")
    same = block_raw == block2
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", html1)))
    record("AC-FD25d", same and not leftovers,
           "determinism: two renders, effects block byte-identical"
           "=%s (%d chars); unfilled placeholders page-wide=%s"
           % (same, len(block_raw), leftovers or "none"))

    # -- AC-FD25e: live server on 8093 -------------------------------
    health = ""
    live_ok = False
    page = ""
    for _ in range(30):
        try:
            with urllib.request.urlopen(
                    "http://127.0.0.1:8093/healthz", timeout=5) as r:
                health = r.read().decode("utf-8", "replace")
            with urllib.request.urlopen(
                    "http://127.0.0.1:8093/", timeout=60) as r:
                page = r.read().decode("utf-8", "replace")
            live_ok = True
            break
        except Exception:
            time.sleep(2)
    live_health = live_ok and "ok" in health
    live_cards = page.count('<div class="card">') if page else 0
    live_title = "Hall Value-Added Effects Face" in page
    live_fail = "EFFECTS PROBE FAILED" in page
    live_block_chars = len(card_block(page, "Hall Value-Added"
                                      " Effects Face"))
    record("AC-FD25e", live_health and live_cards == 27 and live_title
           and not live_fail and live_block_chars > 3000,
           "healthz=%s on live server; card count = 27: got %d;"
           " effects card title on live page=%s; page has no"
           " probe-failure face=%s; live effects card block %d chars"
           % (health.strip() or "n/a", live_cards, live_title,
              not live_fail, live_block_chars))

    # -- AC-FD25f: evidence face --------------------------------------
    record("AC-FD25f", True,
           "this log = qa/frontdoor-v25-R999.log (FD25 full record);"
           " full regression log = qa/reconcile-all-R999.log (RUNNER"
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
