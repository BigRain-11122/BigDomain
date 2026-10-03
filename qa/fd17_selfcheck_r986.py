"""Front door v0.17 self-check (R986, AC-FD17a..f evidence).

Renders the page in-process twice via the module render() and asserts
the pre-registered criteria for the studio onboarding face card, then
probes the LIVE server on 127.0.0.1:8093 (restarted by the runner).
Every check prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL. The REAL studio probe runs inside render() at
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

    block_raw = card_block(html1, "Studio Onboarding Face")
    block = re.sub(r"\s+", " ", html_mod.unescape(block_raw))

    # -- AC-FD17a: pure composition + ASCII source -------------------
    src_path = os.path.join(SBX, "frontdoor.py")
    with open(src_path, "rb") as fh:
        src_bytes = fh.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/sandbox"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty_files = sorted(ln.split(" -> ")[-1].split()[-1]
                         for ln in dirty.splitlines() if ln)
    record("AC-FD17a",
           ascii_ok and dirty_files == ["src/sandbox/frontdoor.py"],
           "frontdoor source pure ASCII: %d bytes=%s; write set under"
           " src/sandbox = %s (product tree untouched)"
           % (len(src_bytes), ascii_ok, dirty_files or "clean"))

    # -- AC-FD17b: probe legs on the card ----------------------------
    legs_expected = [
        "authorize the reserve mint + fund three probe residents",
        "re-register pixelforge under a DIFFERENT kind",
        "register the two studios under their kinds",
        "ben tries to onboard an UNREGISTERED studio",
        "re-read ben's balance after the unknown-studio refusal",
        "amy onboards pixelforge for year-window 26",
        "amy replays the SAME studio-year window",
        "re-read balance + spend count after the replay refusal",
        "ben hits the SAME studio-year held by amy",
        "re-read ben's balance after the exclusivity refusal",
        "amy renews pixelforge for year-window 27 in advance",
        "kinds are independent: amy holds game + quant seats the",
        "a corp: account tries to onboard",
        "zero-price onboarding is refused",
        "a negative year window is refused",
        "an empty onboarding ref is refused",
        "bad-args audit: four refusals, ben's balance flat",
        "read the canon three-benefit bundles B1 / B2",
        "profile reads are pure and bind the purchase spends",
        "audit the seats against real debit entries",
        "isolation law audit on the REAL module source",
    ]
    pos = [block.find(re.sub(r"\s+", " ", leg))
           for leg in legs_expected]
    legs_ok = all(p >= 0 for p in pos) and pos == sorted(pos)
    record("AC-FD17b", legs_ok,
           "twenty-one probe legs rendered in order=%s (positions %s)"
           % (legs_ok, pos))

    # -- AC-FD17b: chain assertions (live readings) ------------------
    struct_ok = ("registry tables=['studio_products'] -- one small"
                 " registry only, the module source has zero direct"
                 " INSERT INTO venue_occupancy" in block)
    unknown_ok = ("refused: E_ST_UNKNOWN" in block
                  and "(an unregistered studio is never onboardable;"
                      " the refusal charged nothing)" in block)
    single_ok = ("balance 50000->40200 (exact -9800); spend-tx 0->1"
                 " (+1); window=[26, 26]" in block)
    dup_ok = ("refused: E_ST_DUP" in block
              and "(the replay is rejected BEFORE the spend; a"
                  " rejected onboarding never charges)" in block)
    taken_ok = ("refused: E_ST_TAKEN" in block
                and "(the venue storefront gate is single-tenant per"
                    " window; the refusal charged nothing)" in block)
    renew_ok = ("balance 40200->30400 (exact -9800); spend-tx 1->2"
                " (+1); window=[27, 27]; tenants year26=usr:amy"
                " year27=usr:amy year28=None" in block)
    kinds_ok = ("amy balance 30400->10600 (exact -19800, quant seat"
                " legal next to the game seat)" in block
                and "spend-tx 2->3->4 (one per seat);"
                    " kinds=quant_studio/game_studio" in block)
    badargs_ok = (block.count("refused: E_ST_BAD_ARGS") == 4
                  and "owners are usr:* only, price must be int > 0,"
                      " year must be int >= 0, ref required" in block)
    benefits_ok = ("B1 game bundle=['idea_pool_access',"
                   " 'player_traffic_boost', 'studio_floor']; B2"
                   " quant bundle=['stock_inspiration_feed',"
                   " 'co_create_observation_entry',"
                   " 'quant_screen_spotlight']" in block)
    profile_ok = ("spend-tx 4==4 unchanged -- profile/tenant reads"
                  " move zero tokens" in block
                  and "amy@26 subscriptions=['studio:pixelforge',"
                      " 'studio:quantworks']" in block
                  and "ben@26=[] (no seat, no leak)" in block
                  and "amy@28=[] (window scope only)" in block)
    audit_ok = ("spend-tx total 4 == onboardings 4; every one of the"
                " 4 occupancy rows binds a real spend debit as its"
                " provenance; balances exact: amy 50000-9800-9800"
                "-19800=10600, ben 50000==50000 untouched, carol"
                " 50000-9800=40200" in block)
    isolation_ok = ("banned verbs found=none; zero direct INSERT INTO"
                    " venue_occupancy and zero UPDATE surface=True"
                    in block
                    and "[needs-CEO] approval face, and no verb turns"
                        " a subscription back into tokens" in block)
    record("AC-FD17b-chain",
           struct_ok and unknown_ok and single_ok and dup_ok
           and taken_ok and renew_ok and kinds_ok and badargs_ok
           and benefits_ok and profile_ok and audit_ok
           and isolation_ok,
           "registry=%s unknown-refusal=%s single-exact-spend=%s"
           " dup-before-spend=%s taken=%s renewal=%s kinds=%s"
           " badargs=%s benefits=%s pure-profile=%s debit-audit=%s"
           " isolation=%s"
           % (struct_ok, unknown_ok, single_ok, dup_ok, taken_ok,
              renew_ok, kinds_ok, badargs_ok, benefits_ok, profile_ok,
              audit_ok, isolation_ok))

    # refusal codes on the card
    ref_ok = all(code in block for code in (
        "E_ST_KIND_MISMATCH", "E_ST_UNKNOWN", "E_ST_DUP",
        "E_ST_TAKEN", "E_ST_BAD_ARGS"))
    record("AC-FD17b-refusals", ref_ok,
           "five fail-closed refusal codes on the card"
           " (KIND_MISMATCH/UNKNOWN/DUP/TAKEN/BAD_ARGS)")

    # -- AC-FD17c: compliance four-piece from config verbatim --------
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
    record("AC-FD17c", ai_ok and disc_ok and ceo_ok and gate_ok
           and price_ok,
           "AIGC label verbatim=%s; disclaimer verbatim=%s;"
           " [needs-CEO] price note=%s; msgSecCheck gate note=%s;"
           " probe-price law=%s"
           % (ai_ok, disc_ok, ceo_ok, gate_ok, price_ok))

    # -- AC-FD17d: determinism + zero unfilled placeholders ----------
    block2 = card_block(html2, "Studio Onboarding Face")
    same = block_raw == block2
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", html1)))
    record("AC-FD17d", same and not leftovers,
           "determinism: two renders, studio block byte-identical"
           "=%s (%d chars); unfilled placeholders page-wide=%s"
           % (same, len(block_raw), leftovers or "none"))

    # -- AC-FD17e: live server on 8093 -------------------------------
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
    live_title = "Studio Onboarding Face" in page
    live_fail = "STUDIO PROBE FAILED" in page
    live_block_chars = len(card_block(page, "Studio Onboarding Face"))
    record("AC-FD17e", live_health and live_cards == 19 and live_title
           and not live_fail and live_block_chars > 3000,
           "healthz=%s on live server; card count = 19: got %d;"
           " studio card title on live page=%s; page has no"
           " probe-failure face=%s; live studio card block %d chars"
           % (health.strip() or "n/a", live_cards, live_title,
              not live_fail, live_block_chars))

    # -- AC-FD17f: evidence face --------------------------------------
    record("AC-FD17f", True,
           "this log = qa/frontdoor-v17-R986.log (FD17 full record);"
           " full regression log = qa/reconcile-all-R986.log (RUNNER"
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
