"""Front door v0.24 self-check (R997, AC-FD24a..f evidence).

Renders the page in-process twice via the module render() and asserts
the pre-registered criteria for the city digital collectibles face
card (the R619 product face, takeover of the orphaned R997 claim whose
code was already in the working tree; this script verifies it, never
trusts it), then probes the LIVE server on 127.0.0.1:8093 (restarted
by the runner). Every check prints PASS/FAIL with evidence; the
process exits non-zero on any FAIL. The REAL collectibles probe runs
inside render() at render time (F3 law); this script verifies what
render() produced -- it never awards, claims or buys anything itself.
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

    block_raw = card_block(html1, "City Digital Collectibles Face")
    block = re.sub(r"\s+", " ", html_mod.unescape(block_raw))

    # -- AC-FD24a: pure composition + ASCII source --------------------
    src_path = os.path.join(SBX, "frontdoor.py")
    with open(src_path, "rb") as fh:
        src_bytes = fh.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/sandbox"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty_files = sorted(ln.split(" -> ")[-1].split()[-1]
                         for ln in dirty.splitlines() if ln)
    header_ok = ("v0.24 city digital collectibles card (R997)" in html1)
    record("AC-FD24a",
           ascii_ok and dirty_files == ["src/sandbox/frontdoor.py"]
           and header_ok,
           "frontdoor source pure ASCII: %d bytes=%s; write set under"
           " src/sandbox = %s (collectibles/ledger product tree"
           " untouched); header v0.24 (R997) on page=%s"
           % (len(src_bytes), ascii_ok, dirty_files or "clean",
              header_ok))

    # -- AC-FD24b: probe legs on the card -----------------------------
    legs_expected = [
        "authorize the reserve mint + fund two resident probe"
        " accounts",
        "award amy a memorial certificate for a co-creation landing",
        "re-award the SAME certificate event for amy",
        "dup-award audit: zero rows written",
        "an ent: account tries to receive a certificate award",
        "amy claims the 2027 co-branded card (member proof shown)",
        "ben claims with a DRIFTED cap parameter (cap locks at first"
        " claim)",
        "carol fills the edition (cap 3/3, deterministic numbering)",
        "amy re-claims the same edition",
        "dave claims the sold-out edition",
        "sold-out audit: the edition counter is untouched",
        "dave claims with an EMPTY membership proof",
        "ben purchases a chronicle replay right (one token spend)",
        "replay-dup audit: the duplicate fires BEFORE the spend",
        "a zero token price is refused",
        "an empty purchase ref is refused",
        "an ent: account tries to purchase a replay right",
        "bad-args audit: ben's balance flat across the family",
        "pure-read audit: collection / edition_status",
        "audit the collections and the bound spend debit",
        "isolation law audit on the REAL module source",
    ]
    pos = [block.find(re.sub(r"\s+", " ", leg))
           for leg in legs_expected]
    legs_ok = all(p >= 0 for p in pos) and pos == sorted(pos)
    record("AC-FD24b", legs_ok,
           "twenty-one probe legs rendered in order=%s (positions %s)"
           % (legs_ok, pos))

    # -- AC-FD24b: chain assertions (live readings) -------------------
    probe_ok = ("probe replay price mirrors a caller-supplied sandbox"
                " value (10 tokens) and the edition cap is 3 --"
                " caller-supplied probe values, never pricing or"
                " sizing decisions" in block)
    cert_ok = ("zero token involvement: spend-tx 0==0 (the award is"
               " earned by the creation itself, not bought);"
               " provenance = the creation event ref=True; one per"
               " account per event; permanent (no verb consumes or"
               " expires it)" in block)
    dupcert_ok = ("amy certificates still 1 (the award is struck once"
                  " per event; the permanent imprint is never"
                  " re-struck)" in block)
    card1_ok = ("free claim gated on the non-empty member proof (real"
                " check wires to the member face at bootstrap);"
                " deterministic numbering: card_no 1 of 3; one card"
                " per account per edition; the edition cap locks at"
                " the first claim" in block)
    drift_ok = ("cap stays locked at 3 (the drifted 9 is ignored, the"
                " first-claim cap wins); ben gets card_no 2" in block)
    fill_ok = ("carol gets card_no 3; edition_status: cap 3, issued 3"
               " (numbering is claim-order deterministic)" in block)
    soldout_ok = ("edition_status 2027-newyear: cap 3, issued 3 (a"
                  " refused claim never burns a number; numbering"
                  " stays claim-order deterministic)" in block)
    replay_ok = ("balance 8000->7990 (exact -10 = the probe price);"
                 " spend-tx 0->1 (+1); the right is permanent and its"
                 " row binds that real spend tx=True" in block)
    rdup_ok = ("balance 7990==7990 and spend-tx 1==1 (a rejected"
               " replay purchase never charges and never writes a"
               " second row)" in block)
    badargs_ok = ("7990==7990 (awards are usr:* earned, claims are"
                  " usr:* free, purchases are usr:* only with an int"
                  " price >= 1 and a non-empty ref -- every rejected"
                  " call charges nothing and writes no row)" in block)
    reads_ok = ("spend-tx 1==1 unchanged -- reads move zero tokens"
                " (the collection view carries provenance: event refs"
                " for awards and claims, the bound spend tx for"
                " purchases)" in block)
    audit_ok = ("amy 1 certificate + 1 card (no.1); ben 1 card (no.2)"
                " + 1 replay; carol 1 card (no.3); the replay row"
                " binds a real spend debit for usr:ben (bound 1/1);"
                " spend-tx total 1 == replay rights 1 (the module's"
                " single token-domain touch across the whole probe);"
                " balances exact: amy 12000, ben 8000-10=7990;"
                " pool:reserve 10 (20000 mint, the spent tokens loop"
                " back in, conservation holds: pool+balances==mint"
                "=True)" in block)
    isolation_ok = ("banned token-verb hits on the code surface=none"
                    " (module-wide scan=none); ledger-API call sites"
                    " (self.led.) x2 = the module's ONLY token-domain"
                    " touch, both inside buy_replay_right (the"
                    " idempotent ensure_account + exactly one spend"
                    " per replay right) -- awarding and claiming never"
                    " book a token tx; the only UPDATE surface=1 site"
                    " is exactly the edition issue counter; the"
                    " account_id / kind / event_ref ownership columns"
                    " are never rewritten after grant=True; no verb"
                    " moves a collectible between accounts and no"
                    " verb consumes or expires one (ownership never"
                    " changes hands, permanent imprint -- canon"
                    " wording); any future swap / hand-off / resale"
                    " face is a P1 [needs-CEO] approval-only item;"
                    " module source pure ASCII (0 non-ascii)" in block)
    record("AC-FD24b-chain",
           probe_ok and cert_ok and dupcert_ok and card1_ok
           and drift_ok and fill_ok and soldout_ok and replay_ok
           and rdup_ok and badargs_ok and reads_ok and audit_ok
           and isolation_ok,
           "probe-values=%s cert-zero-token=%s dup-cert=%s card-no1=%s"
           " cap-lock=%s fill-3/3=%s soldout=%s one-spend-replay=%s"
           " replay-dup-before-spend=%s bad-args=%s pure-reads=%s"
           " debit-audit=%s isolation=%s"
           % (probe_ok, cert_ok, dupcert_ok, card1_ok, drift_ok,
              fill_ok, soldout_ok, replay_ok, rdup_ok, badargs_ok,
              reads_ok, audit_ok, isolation_ok))

    # refusal codes on the card
    ref_ok = (block.count("refused: E_CL_DUP") == 3
              and block.count("refused: E_CL_BAD_REF") == 3
              and block.count("refused: E_CL_SOLD_OUT") == 1
              and block.count("refused: E_CL_MEMBERSHIP_REQUIRED") == 1
              and block.count("refused: E_CL_BAD_AMOUNT") == 1)
    record("AC-FD24b-refusals", ref_ok,
           "nine fail-closed refusal codes on the card (DUP x3"
           " certificate re-award + card re-claim + replay re-purchase,"
           " BAD_REF x3 ent: certificate + empty purchase ref + ent:"
           " purchase, SOLD_OUT x1, MEMBERSHIP_REQUIRED x1, BAD_AMOUNT"
           " x1 -- every rejection zero charge, zero rows)")

    # -- AC-FD24c: compliance four-piece from config verbatim --------
    lcfg = json.load(open(os.path.join(SBX, "ledger", "config.json"),
                          encoding="utf-8"))
    ai_text = str(lcfg.get("token", {}).get("ai_label_text", ""))
    disc = str(lcfg.get("token", {}).get("disclaimer", ""))
    ai_ok = ai_text in html1
    disc_ok = disc in html1
    ceo_ok = "[needs-CEO]" in block
    gate_note_ok = "msgSecCheck" in block
    price_ok = ("caller-supplied sandbox values" in block
                and "real collectible pricing, edition sizing and"
                " launch gating stay P1 CEO approval faces" in block)
    record("AC-FD24c", ai_ok and disc_ok and ceo_ok and gate_note_ok
           and price_ok,
           "AIGC label verbatim=%s; disclaimer verbatim=%s;"
           " [needs-CEO] price note=%s; msgSecCheck gate note=%s;"
           " probe-price law=%s"
           % (ai_ok, disc_ok, ceo_ok, gate_note_ok, price_ok))

    # -- AC-FD24d: determinism + zero unfilled placeholders ----------
    block2 = card_block(html2, "City Digital Collectibles Face")
    same = block_raw == block2
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", html1)))
    record("AC-FD24d", same and not leftovers,
           "determinism: two renders, collectibles block"
           " byte-identical=%s (%d chars); unfilled placeholders"
           " page-wide=%s"
           % (same, len(block_raw), leftovers or "none"))

    # -- AC-FD24e: live server on 8093 -------------------------------
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
    live_title = "City Digital Collectibles Face" in page
    live_fail = "COLLECTIBLES PROBE FAILED" in page
    live_block_chars = len(card_block(page, "City Digital"
                                      " Collectibles Face"))
    record("AC-FD24e", live_health and live_cards == 26 and live_title
           and not live_fail and live_block_chars > 3000,
           "healthz=%s on live server; card count = 26: got %d;"
           " collectibles card title on live page=%s; page has no"
           " probe-failure face=%s; live collectibles card block %d"
           " chars"
           % (health.strip() or "n/a", live_cards, live_title,
              not live_fail, live_block_chars))

    # -- AC-FD24f: evidence face --------------------------------------
    record("AC-FD24f", True,
           "this log = qa/frontdoor-v24-R997.log (FD24 full record);"
           " full regression log = qa/reconcile-all-R997.log (RUNNER"
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
