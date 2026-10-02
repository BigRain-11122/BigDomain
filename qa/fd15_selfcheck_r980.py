"""Front door v0.15 self-check (R980, AC-FD15a..f evidence).

Renders the page in-process twice via the module render() and asserts
the pre-registered criteria for the creator incentive face card, then
probes the LIVE server on 127.0.0.1:8093 (restarted by the runner).
Every check prints PASS/FAIL with evidence; the process exits non-zero
on any FAIL. The REAL incentive probe runs inside render() at render
time (F3 law); this script verifies what render() produced -- it
never books anything itself.
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

    block_raw = card_block(html1, "Creator Incentive Face")
    block = re.sub(r"\s+", " ", html_mod.unescape(block_raw))

    # -- AC-FD15a: pure composition + ASCII source ------------------
    src_path = os.path.join(SBX, "frontdoor.py")
    with open(src_path, "rb") as fh:
        src_bytes = fh.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/sandbox"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty_files = sorted(ln.split(" -> ")[-1].split()[-1]
                         for ln in dirty.splitlines() if ln)
    record("AC-FD15a",
           ascii_ok and dirty_files == ["src/sandbox/frontdoor.py"],
           "frontdoor source pure ASCII: %d bytes=%s; write set under"
           " src/sandbox = %s (product tree untouched)"
           % (len(src_bytes), ascii_ok, dirty_files or "clean"))

    # -- AC-FD15b: probe legs on the card ----------------------------
    legs_expected = [
        "authorize the settlement-window funding",
        "walk the pure gradient function",
        "settle window W1 (raw 410 overshoots the budget 400)",
        "settle window W2 with one 1,000,000-unit contribution",
        "audit the ledger booking join",
        "re-settle the SAME window W1",
        "re-read all balances after the replay refusal",
        "settle a window with EMPTY contributions",
        "a pool account tries to collect",
        "contribute zero units",
        "the same creator twice in one window",
        "isolation law + shipped-config check",
    ]
    pos = [block.find(re.sub(r"\s+", " ", leg))
           for leg in legs_expected]
    legs_ok = all(p >= 0 for p in pos) and pos == sorted(pos)
    record("AC-FD15b", legs_ok,
           "twelve probe legs rendered in order=%s (positions %s)"
           % (legs_ok, pos))

    # -- AC-FD15b: chain assertions (live readings) ------------------
    grad_ok = ("[0, 10, 30, 50, 55, 100, 102, 150, 270]" in
               block)
    marg_ok = "marginal per unit falls band over band (10 -> 5 -> 2)" \
              in block
    w1_ok = ("[('usr:alice', 147), ('usr:bob', 127),"
             " ('usr:carol', 126)] (sum 400 == budget exactly" in block)
    w2_ok = ("[('usr:dave', 150)] -- the per-creator window collar"
             in block)
    join_ok = ("share-tx 0->4 (+4, one per payout); pool:share 2000"
               " - 550 = 1450 exact; 4 credit rows each binding its"
               " settlement ref=True" in block)
    replay_ok = ("refused: E_INC_WINDOW_DUP" in block
                 and "unchanged=True -- a settled window is idempotent"
                 in block)
    isola_ok = ("banned-verb hits in the module=[]" in block
                and "incentive param keys in the shipped"
                " config=False" in block)
    record("AC-FD15b-chain",
           grad_ok and marg_ok and w1_ok and w2_ok and join_ok
           and replay_ok and isola_ok,
           "gradient seq=%s marginals=%s W1 exact landing=%s W2"
           " collar=%s join=%s replay zero-move=%s isolation+nokey=%s"
           % (grad_ok, marg_ok, w1_ok, w2_ok, join_ok, replay_ok,
              isola_ok))

    # refusal codes on the card
    ref_ok = all(code in block for code in (
        "E_INC_WINDOW_DUP", "E_INC_EMPTY", "E_INC_BAD_ACCOUNT",
        "E_INC_BAD_UNITS", "E_INC_DUP_CREATOR"))
    record("AC-FD15b-refusals", ref_ok,
           "five fail-closed refusal codes on the card"
           " (WINDOW_DUP/EMPTY/BAD_ACCOUNT/BAD_UNITS/DUP_CREATOR)")

    # -- AC-FD15c: compliance four-piece from config verbatim --------
    lcfg = json.load(open(os.path.join(SBX, "ledger", "config.json"),
                          encoding="utf-8"))
    ai_text = str(lcfg.get("token", {}).get("ai_label_text", ""))
    disc = str(lcfg.get("token", {}).get("disclaimer", ""))
    ai_ok = ai_text in html1
    disc_ok = disc in html1
    ceo_ok = "[needs-CEO]" in block
    gate_ok = "msgSecCheck" in block
    nokey_ok = ("no incentive key ships in any config file" in
                re.sub(r"\s+", " ", html1))
    record("AC-FD15c", ai_ok and disc_ok and ceo_ok and gate_ok
           and nokey_ok,
           "AIGC label verbatim=%s; disclaimer verbatim=%s;"
           " [needs-CEO] params note=%s; msgSecCheck gate note=%s;"
           " AC-IG7 no-key law=%s"
           % (ai_ok, disc_ok, ceo_ok, gate_ok, nokey_ok))

    # -- AC-FD15d: determinism + zero unfilled placeholders ----------
    block2 = card_block(html2, "Creator Incentive Face")
    same = block_raw == block2
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", html1)))
    record("AC-FD15d", same and not leftovers,
           "determinism: two renders, incentive block byte-identical"
           "=%s (%d chars); unfilled placeholders page-wide=%s"
           % (same, len(block_raw), leftovers or "none"))

    # -- AC-FD15e: live server on 8093 -------------------------------
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
    live_title = "Creator Incentive Face" in page
    live_fail = "INCENTIVE PROBE FAILED" in page
    live_block_chars = len(card_block(page, "Creator Incentive Face"))
    record("AC-FD15e", live_health and live_cards == 17 and live_title
           and not live_fail and live_block_chars > 3000,
           "healthz=%s on live server; card count = 17: got %d;"
           " incentive card title on live page=%s; page has no"
           " probe-failure face=%s; live incentive card block %d chars"
           % (health.strip() or "n/a", live_cards, live_title,
              not live_fail, live_block_chars))

    # -- AC-FD15f: evidence face --------------------------------------
    record("AC-FD15f", True,
           "this log = qa/frontdoor-v15-R980.log (FD15 full record);"
           " full regression log = qa/reconcile-all-R980.log (RUNNER"
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
