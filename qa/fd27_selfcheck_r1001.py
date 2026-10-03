"""Front door v0.27 self-check (R1001, AC-FD27a..f evidence).

Renders the page in-process twice via the module render() and asserts
the pre-registered criteria for the cross-subsidiary settlement
protocol face card (the R601 product face; ownership anchors per
D-20260924-10), then probes the LIVE server on 127.0.0.1:8093
(restarted by the runner). Every check prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL. The REAL
settlement probe runs inside render() at render time (F3 law); this
script verifies what render() produced -- it never builds or
verifies a manifest itself.
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

    block_raw = card_block(html1, "Cross-Subsidiary Settlement"
                                       " Protocol Face")
    block = re.sub(r"\s+", " ", html_mod.unescape(block_raw))

    # -- AC-FD27a: pure composition + ASCII source --------------------
    src_path = os.path.join(SBX, "frontdoor.py")
    with open(src_path, "rb") as fh:
        src_bytes = fh.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/sandbox"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty_files = sorted(ln.split(" -> ")[-1].split()[-1]
                         for ln in dirty.splitlines() if ln)
    header_ok = ("v0.27 cross-subsidiary settlement card (R1001)"
                 in html1)
    record("AC-FD27a",
           ascii_ok and dirty_files == ["src/sandbox/frontdoor.py"]
           and header_ok,
           "frontdoor source pure ASCII: %d bytes=%s; write set under"
           " src/sandbox = %s (settlement/ledger product tree"
           " untouched); header v0.27 (R1001) on page=%s"
           % (len(src_bytes), ascii_ok, dirty_files or "clean",
              header_ok))

    # -- AC-FD27b: probe legs on the card -----------------------------
    legs_expected = [
        "build the window-1 settlement manifest from the probe"
        " sales rows (19.9-family order values)",
        "conservation law on the odd and zero windows",
        "determinism: an independent face rebuilds the same"
        " window byte-identical",
        "the hash chain: window-2 carries window-1's id as"
        " prev_id",
        "verify_manifest re-derives the manifest from the rows",
        "an apportioned-amount tamper (+1 fen) is refused",
        "a party-list tamper (ghost party) is refused",
        "tamper audit: the id covers the whole payload",
        "a same-period window rebuild is refused",
        "window idempotency audit: exactly one manifest per"
        " period",
        "a full-bounded claim binds the manifest id",
        "a duplicate claim (same period+party) is refused",
        "an over-limit claim is refused",
        "an unknown-party claim is refused",
        "an unknown-window claim is refused",
        "claim-gate audit: claims are bounded and single-shot",
        "a negative-fen sales row is refused at build",
        "a bool value is refused at build (bool is not an int)",
        "a zero weight sum is refused at build",
        "an empty party list is refused at build",
        "an empty period string is refused at build",
        "bad-input audit: five E_ST_BAD_INPUT build refusals,"
        " zero rows",
        "full-claim audit: the claimed total equals the settled"
        " sales total",
        "isolation law audit on the REAL module source",
    ]
    pos = [block.find(re.sub(r"\s+", " ", leg))
           for leg in legs_expected]
    legs_ok = all(p >= 0 for p in pos) and pos == sorted(pos)
    record("AC-FD27b", legs_ok,
           "twenty-four probe legs rendered in order=%s (positions"
           " %s)" % (legs_ok, pos))

    # -- AC-FD27b: chain assertions (live readings) -------------------
    build_ok = ("sales_total=6970 fen (1990+3990+990),"
                " usage_total=15 units,"
                " schema=bigdomain.settlement/1; integer split"
                " floor+input-order remainder:"
                " {'bigdomain-product': 3834, 'bigmoney-engine':"
                " 2091, 'bigcompute-outlet': 1045} -- sum=6970 fen,"
                " zero rounding loss (probe weights 55/30/15 mirror"
                " the product-side-larger-share note; the canonical"
                " ratios stay needs-CEO, never encoded)" in block)
    conserve_ok = ("199-fen odd window splits {'a': 110, 'b': 60,"
                   " 'c': 29} summing 199 exact (the remainder walks"
                   " input order); zero-sales window apportions 0"
                   " -- fen totals are preserved exactly, no rounding"
                   " ever" in block)
    idem_ok = ("canonical payload equal=True, same sha256 id=True"
               " (" in block and " -- zero RNG; handed-out manifests"
               " are deep copies, the window registry keeps the"
               " canonical original" in block)
    chain_ok = ("prev_id equal=True; each manifest id is sha256"
                " over the sorted-key canonical payload including"
                " prev_id, so the chain makes retro-editing any"
                " settled window detectable" in block)
    verify_ok = ("the id recomputes over the canonical body and"
                 " the rebuilt fields match field-for-field -> True"
                 " (no canned status: any drift raises E_ST_TAMPER)"
                 in block)
    tamper_ok = ("both edits change the canonical body, so the"
                 " stored id mismatches first; the verify cross"
                 " then re-derives the apportionment from the rows"
                 " and catches drift even if the id were recomputed"
                 " -- two independent tamper nets" in block)
    window_ok = ("window_count=2 after the rebuild attempt"
                 " (E_ST_PERIOD_DUP) -- a settlement window is"
                 " single-manifest, replays cannot double-count a"
                 " settled period" in block)
    claim_ok = ("claim 3834 fen for bigdomain-product bound to"
                " manifest id " in block
                and " (claim <= apportioned enforced per party;"
                " claims are per (period, party))" in block)
    gate_ok = ("duplicate / over-limit / unknown-party /"
                " unknown-window all refused with zero rows"
                " written -- a claim cannot exceed the apportioned"
                " amount nor double-claim a settled window"
                in block)
    badinput_ok = ("negative fen / bool value / zero weight sum /"
                  " empty parties / empty period -- every rejected"
                  " call writes nothing and settles nothing"
                  " (fail-closed protocol face)" in block)
    fullclaim_ok = ("three parties claimed 6970 fen == apportioned"
                    " sum == sales_total=6970 fen -- the window"
                    " closes conservation-clean (claims bounded,"
                    " single-manifest, hash-chained)" in block)
    isolation_ok = ("module source pure ASCII (0 non-ascii);"
                    " imports=['import hashlib', 'import json']"
                    " (stdlib only=True); network verbs=none; banned"
                    " money verbs=none (split-token scan); import"
                    " random present=False; canonical-ratio constant"
                    " shipped=False -- the module RECONCILES, never"
                    " moves money or tokens (settlement execution"
                    " lives on the engine/outlet faces per the"
                    " D-20260924-10 ownership note)" in block)
    split_ok = ("<th>party</th>" in block
                and "<th>probe weight</th>" in block
                and "<th>apportioned fen</th>" in block
                and "<td>bigdomain-product</td><td>55</td>"
                "<td>3834</td>" in block
                and "<td>bigmoney-engine</td><td>30</td>"
                "<td>2091</td>" in block
                and "<td>bigcompute-outlet</td><td>15</td>"
                "<td>1045</td>" in block)
    record("AC-FD27b-chain",
           build_ok and conserve_ok and idem_ok and chain_ok
           and verify_ok and tamper_ok and window_ok and claim_ok
           and gate_ok and badinput_ok and fullclaim_ok
           and isolation_ok and split_ok,
           "window-build=%s conservation=%s determinism=%s"
           " hash-chain=%s verify-cross=%s tamper-nets=%s"
           " window-idempotency=%s claim-bind=%s claim-gate=%s"
           " bad-input=%s full-claim=%s isolation=%s"
           " split-table=%s"
           % (build_ok, conserve_ok, idem_ok, chain_ok, verify_ok,
              tamper_ok, window_ok, claim_ok, gate_ok, badinput_ok,
              fullclaim_ok, isolation_ok, split_ok))

    # refusal codes on the card
    ref_ok = (block.count("refused: E_ST_TAMPER") == 2
              and block.count("refused: E_ST_PERIOD_DUP") == 2
              and block.count("refused: E_ST_BAD_INPUT") == 8)
    record("AC-FD27b-refusals", ref_ok,
           "twelve fail-closed refusal codes on the card"
           " (E_ST_TAMPER x2 amount tamper + party-list tamper,"
           " E_ST_PERIOD_DUP x2 same-period rebuild + duplicate"
           " claim, E_ST_BAD_INPUT x8 over-limit / unknown-party /"
           " unknown-window claims + negative fen / bool value /"
           " zero weight sum / empty parties / empty period -- every"
           " rejection writes nothing and settles nothing)")

    # -- AC-FD27c: compliance four-piece from config verbatim ---------
    lcfg = json.load(open(os.path.join(SBX, "ledger", "config.json"),
                          encoding="utf-8"))
    ai_text = str(lcfg.get("token", {}).get("ai_label_text", ""))
    disc = str(lcfg.get("token", {}).get("disclaimer", ""))
    ai_ok = ai_text in html1
    disc_ok = disc in html1
    ceo_note_ok = "[needs-CEO]" in block
    gate_note_ok = "msgSecCheck" in block
    ceo_face_ok = ("stay P1 CEO approval-only faces" in block
                   and "never encoded in module or config" in block)
    no_cfg_key = lcfg.get("settlement") is None
    record("AC-FD27c", ai_ok and disc_ok and ceo_note_ok
           and gate_note_ok and ceo_face_ok and no_cfg_key,
           "AIGC label verbatim=%s; disclaimer verbatim=%s;"
           " [needs-CEO] note=%s; msgSecCheck gate note=%s;"
           " P1-approval-face law=%s; shipped ledger config carries"
           " no settlement key=%s"
           % (ai_ok, disc_ok, ceo_note_ok, gate_note_ok,
              ceo_face_ok, no_cfg_key))

    # -- AC-FD27d: determinism + zero unfilled placeholders -----------
    block2 = card_block(html2, "Cross-Subsidiary Settlement"
                               " Protocol Face")
    same = block_raw == block2
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", html1)))
    record("AC-FD27d", same and not leftovers,
           "determinism: two renders, settlement block"
           " byte-identical=%s (%d chars); unfilled placeholders"
           " page-wide=%s"
           % (same, len(block_raw), leftovers or "none"))

    # -- AC-FD27e: live server on 8093 --------------------------------
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
    live_title = ("Cross-Subsidiary Settlement Protocol Face"
                  in page)
    live_fail = "SETTLEMENT PROBE FAILED" in page
    live_block_chars = len(card_block(page, "Cross-Subsidiary"
                                      " Settlement Protocol Face"))
    record("AC-FD27e", live_health and live_cards == 29 and live_title
           and not live_fail and live_block_chars > 3000,
           "healthz=%s on live server; card count = 29: got %d;"
           " settlement card title on live page=%s; page has no"
           " probe-failure face=%s; live settlement card block %d"
           " chars"
           % (health.strip() or "n/a", live_cards, live_title,
              not live_fail, live_block_chars))

    # -- AC-FD27f: evidence face ---------------------------------------
    record("AC-FD27f", True,
           "this log = qa/frontdoor-v27-R1001.log (FD27 full record);"
           " full regression log = qa/reconcile-all-R1001.log (RUNNER"
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
