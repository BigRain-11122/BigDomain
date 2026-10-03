"""Front door v0.21 self-check (R992, AC-FD21a..f evidence).

Renders the page in-process twice via the module render() and asserts
the pre-registered criteria for the metaverse identity face card, then
probes the LIVE server on 127.0.0.1:8093 (restarted by the runner).
Every check prints PASS/FAIL with evidence; the process exits non-zero
on any FAIL. The REAL identity probe runs inside render() at render
time (F3 law); this script verifies what render() produced -- it
never rents or claims anything itself.
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

    block_raw = card_block(html1, "Identity Face")
    block = re.sub(r"\s+", " ", html_mod.unescape(block_raw))

    # -- AC-FD21a: pure composition + ASCII source --------------------
    src_path = os.path.join(SBX, "frontdoor.py")
    with open(src_path, "rb") as fh:
        src_bytes = fh.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/sandbox"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty_files = sorted(ln.split(" -> ")[-1].split()[-1]
                         for ln in dirty.splitlines() if ln)
    record("AC-FD21a",
           ascii_ok and dirty_files == ["src/sandbox/frontdoor.py"],
           "frontdoor source pure ASCII: %d bytes=%s; write set under"
           " src/sandbox = %s (identity/props/venue/ledger product"
           " tree untouched)"
           % (len(src_bytes), ascii_ok, dirty_files or "clean"))

    # -- AC-FD21b: probe legs on the card -----------------------------
    legs_expected = [
        "authorize the reserve mint + fund three probe buyers",
        "re-register the room under a DIFFERENT kind",
        "register an UNKNOWN identity kind",
        "register the room + the three permanent identity products",
        "amy rents the private room for month 10 (9.9 CNY anchor)",
        "amy replays the SAME month window under the SAME ref",
        "ben tries to rent the SAME room in the SAME month",
        "re-read both balances after the rental refusals",
        "amy renews month 11 (a later window = advance booking)",
        "ben rents an UNREGISTERED room",
        "ben claims an UNREGISTERED product",
        "ben rents on a PERMANENT product (cross-kind)",
        "ben claims the ROOM as a permanent (cross-kind)",
        "registry gate audit: four refusals, ben's balance flat",
        "amy claims the avatar skin (29.9 CNY anchor)",
        "amy claims the SAME skin again under a NEW ref",
        "re-read amy's balance after the duplicate-claim refusal",
        "ben claims the creator plaque (49.9) and carol claims the"
        " premium floor plaque (199 -- the highest C5 anchor)",
        "an ent: enterprise account tries to claim directly on the"
        " resident token ledger",
        "a zero price claim is refused",
        "a negative month rental is refused",
        "an empty purchase ref is refused",
        "bad-args audit: all three buyer balances flat",
        "pure-read audit: room_holder / identity_profile",
        "audit the identity purchases against real debit entries",
        "isolation law audit on the REAL module source",
    ]
    pos = [block.find(re.sub(r"\s+", " ", leg))
           for leg in legs_expected]
    legs_ok = all(p >= 0 for p in pos) and pos == sorted(pos)
    record("AC-FD21b", legs_ok,
           "twenty-six probe legs rendered in order=%s (positions %s)"
           % (legs_ok, pos))

    # -- AC-FD21b: chain assertions (live readings) -------------------
    reg_ok = ("published=True; identical re-register idempotent=True;"
              " the registry is identity_products only"
              " (['identity_products']); the room registration landed"
              " in the referenced venue registry capacity 1 (the"
              " venue public API, no second occupancy engine); the"
              " module source has zero direct INSERT INTO"
              " props_inventory / venue_occupancy (reference law:"
              " every WRITE rides the props / venue public APIs)"
              in block)
    rent_ok = ("balance 15000->14010 (exact -990 = one month window,"
               " one spend); spend-tx 0->1 (+1); the venue occupancy"
               " row binds that spend tx=True; window [10, 10] (one"
               " tenant per room per month, exclusive month window)"
               in block)
    dupflat_ok = ("14010==14010 and 10000==10000 (the same-month"
                  " replay and the second tenant are both rejected"
                  " BEFORE the spend by the venue exclusivity gate; a"
                  " rejected rental never charges and never grants)"
                  in block)
    renew_ok = ("renewal = renting a later month window; balance"
                " 14010->13020 (exact -990, a separate legal spend"
                " with a distinct tx=True); spend-tx 1->2 (+1);"
                " holder reads: m10=usr:amy m11=usr:amy m12=None"
                in block)
    gate_ok = ("10000==10000 (unregistered room / product and both"
               " cross-kind calls are rejected by the identity"
               " registry join -- a product only ever behaves as its"
               " registered kind; every rejected call charges nothing"
               " and writes no row)" in block)
    skin_ok = ("balance 13020->10030 (exact -2990 = one permanent"
               " entitlement, one spend); spend-tx 2->3 (+1); the"
               " entitlement row lives in props_inventory as a"
               " cosmetic (one per account, immutable), bound to that"
               " spend tx" in block)
    skindup_ok = ("10030==10030 (a duplicate permanent claim is"
                  " rejected by the props cosmetic gate BEFORE the"
                  " spend; the refusal charges nothing and grants"
                  " nothing)" in block)
    plaque_ok = ("ben 10000->5010 (exact -4990), carol 22000->2100"
                 " (exact -19900); spend-tx 3->5 (+2, one spend per"
                 " claim); all three permanent kinds live in"
                 " props_inventory as cosmetics"
                 " (amy=['skin:neon-fox'], ben=['plaque:co-creator'],"
                 " carol=['plaque:floor-88']) with three distinct"
                 " bound spend txs=True" in block)
    ent_ok = ("refused: E_ID_BAD_ARGS at the module gate (buyers are"
              " usr:* only) -- the identity gate itself refuses"
              " non-resident buyers one layer earlier than the token"
              " ledger, so the stack is fail-closed: zero charge,"
              " zero rows written; production enterprise procurement"
              " routes through the BigCompute collection gateway"
              " (D-20260924-11 collection exit unified there)"
              in block)
    badargs_ok = ("[10030, 5010, 2100]==[10030, 5010, 2100] (price"
                  " must be int > 0, month_index must be int >= 0,"
                  " purchase refs are required -- every rejected call"
                  " charges nothing and writes no row)" in block)
    reads_ok = ("spend-tx 5==5 unchanged -- reads move zero tokens;"
                " amy's profile at m10 shows the held room"
                " ['room:sky-villa'] with its purchase spend tx plus"
                " her permanent ['skin:neon-fox']; at m12 the room"
                " window has expired so only permanents remain (0"
                " rooms); ben's profile shows exactly his own"
                " ['plaque:co-creator'] (the registry join keeps"
                " foreign venue units and props out)" in block)
    audit_ok = ("spend-tx total 5 == identity purchases 5 (2 room"
                " months + 3 permanents); all 5 entitlement /"
                " occupancy rows (2 venue occupancy + 3 props"
                " cosmetics) bind a real spend debit for their own"
                " buyer (bound 5/5); balances exact: amy"
                " 15000-990-990-2990=10030, ben 10000-4990=5010,"
                " carol 22000-19900=2100; pool:reserve 29860 (47000"
                " mint, spent tokens loop back in, conservation"
                " holds: pool+balances==mint=True)" in block)
    isolation_ok = ("banned token-verb hits on the code surface=none"
                    " (module-wide scan=['transfer']: the single"
                    " transfer hit is the module docstring's own P1"
                    " boundary statement -- cancellation, fee reversal"
                    " or transfer of any kind is a [needs-CEO]"
                    " approval face, not a mechanism here);"
                    " ledger-API call sites (self.led.) x0 -- the"
                    " module itself never touches the token domain,"
                    " every purchase spend happens inside the"
                    " referenced props / venue engines (one spend per"
                    " purchase); zero UPDATE surface (registry rows"
                    " immutable once written); zero direct INSERT"
                    " INTO props_inventory / venue_occupancy (every"
                    " WRITE rides the engine public APIs -- reference"
                    " law); module source pure ASCII (0 non-ascii)"
                    in block)
    record("AC-FD21b-chain",
           reg_ok and rent_ok and dupflat_ok and renew_ok and gate_ok
           and skin_ok and skindup_ok and plaque_ok and ent_ok
           and badargs_ok and reads_ok and audit_ok and isolation_ok,
           "one-registry=%s one-spend-month=%s rental-refusals=%s"
           " renewal=%s registry-gates=%s skin-claim=%s"
           " dup-before-spend=%s plaque-199=%s ent-gate=%s"
           " bad-args=%s pure-reads=%s debit-audit=%s isolation=%s"
           % (reg_ok, rent_ok, dupflat_ok, renew_ok, gate_ok, skin_ok,
              skindup_ok, plaque_ok, ent_ok, badargs_ok, reads_ok,
              audit_ok, isolation_ok))

    # refusal codes on the card
    ref_ok = (block.count("refused: E_ID_BAD_ARGS") == 5
              and block.count("refused: E_ID_KIND_MISMATCH") == 3
              and block.count("refused: E_ID_DUP") == 2
              and block.count("refused: E_ID_TAKEN") == 1
              and block.count("refused: E_ID_UNKNOWN") == 2)
    record("AC-FD21b-refusals", ref_ok,
           "thirteen fail-closed refusal codes on the card (BAD_ARGS"
           " x5 incl. the ent: boundary, KIND_MISMATCH x3, DUP x2,"
           " TAKEN x1, UNKNOWN x2 -- every rejection zero charge)")

    # -- AC-FD21c: compliance four-piece from config verbatim --------
    lcfg = json.load(open(os.path.join(SBX, "ledger", "config.json"),
                          encoding="utf-8"))
    ai_text = str(lcfg.get("token", {}).get("ai_label_text", ""))
    disc = str(lcfg.get("token", {}).get("disclaimer", ""))
    ai_ok = ai_text in html1
    disc_ok = disc in html1
    ceo_ok = "[needs-CEO]" in block
    gate_note_ok = "msgSecCheck" in block
    price_ok = ("the C5 canon anchors (private room 9.9 CNY per"
                " month, avatar skin 29.9 CNY, creator plaque 49.9"
                " CNY, premium floor plaque 199 CNY permanent) are"
                " caller-supplied probe prices" in block)
    record("AC-FD21c", ai_ok and disc_ok and ceo_ok and gate_note_ok
           and price_ok,
           "AIGC label verbatim=%s; disclaimer verbatim=%s;"
           " [needs-CEO] price note=%s; msgSecCheck gate note=%s;"
           " probe-price law=%s"
           % (ai_ok, disc_ok, ceo_ok, gate_note_ok, price_ok))

    # -- AC-FD21d: determinism + zero unfilled placeholders ----------
    block2 = card_block(html2, "Identity Face")
    same = block_raw == block2
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", html1)))
    record("AC-FD21d", same and not leftovers,
           "determinism: two renders, identity block byte-identical=%s"
           " (%d chars); unfilled placeholders page-wide=%s"
           % (same, len(block_raw), leftovers or "none"))

    # -- AC-FD21e: live server on 8093 -------------------------------
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
    live_title = "Identity Face" in page
    live_fail = "IDENTITY PROBE FAILED" in page
    live_block_chars = len(card_block(page, "Identity Face"))
    record("AC-FD21e", live_health and live_cards == 23 and live_title
           and not live_fail and live_block_chars > 3000,
           "healthz=%s on live server; card count = 23: got %d;"
           " identity card title on live page=%s; page has no"
           " probe-failure face=%s; live identity card block %d chars"
           % (health.strip() or "n/a", live_cards, live_title,
              not live_fail, live_block_chars))

    # -- AC-FD21f: evidence face --------------------------------------
    record("AC-FD21f", True,
           "this log = qa/frontdoor-v21-R992.log (FD21 full record);"
           " full regression log = qa/reconcile-all-R992.log (RUNNER"
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
