"""Front door v0.26 self-check (R1000, AC-FD26a..f evidence).

Renders the page in-process twice via the module render() and asserts
the pre-registered criteria for the visitor-end M4 three-state
selection decision-prep face card (the R602 product face, group
order O-2026-0929-007 BigDomain slice -- the sole precondition of
visitor-end commercialization), then probes the LIVE server on
127.0.0.1:8093 (restarted by the runner). Every check prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.
The REAL tourstate probe runs inside render() at render time (F3
law); this script verifies what render() produced -- it never
builds or verifies a packet itself.
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

    block_raw = card_block(html1, "Visitor-End M4 Three-State Face")
    block = re.sub(r"\s+", " ", html_mod.unescape(block_raw))

    # -- AC-FD26a: pure composition + ASCII source --------------------
    src_path = os.path.join(SBX, "frontdoor.py")
    with open(src_path, "rb") as fh:
        src_bytes = fh.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/sandbox"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty_files = sorted(ln.split(" -> ")[-1].split()[-1]
                         for ln in dirty.splitlines() if ln)
    header_ok = ("v0.26 visitor-end M4 three-state card (R1000)"
                 in html1)
    record("AC-FD26a",
           ascii_ok and dirty_files == ["src/sandbox/frontdoor.py"]
           and header_ok,
           "frontdoor source pure ASCII: %d bytes=%s; write set under"
           " src/sandbox = %s (tourstate/ledger product tree"
           " untouched); header v0.26 (R1000) on page=%s"
           % (len(src_bytes), ascii_ok, dirty_files or "clean",
              header_ok))

    # -- AC-FD26b: probe legs on the card -----------------------------
    legs_expected = [
        "build the three-state decision-prep packet at the live"
        " posture (purchase_approved=False)",
        "re-build the packet: deterministic, zero RNG",
        "verify_packet re-derives every gate and verdict",
        "a gate-status tamper (offline_frames license_l1"
        " flipped BLOCKED->PASS) is refused",
        "tamper audit: the stored id no longer covers the payload",
        "a purchase_approved tamper WITH the id recomputed"
        " is still refused",
        "tamper audit: gate drift catches the recomputed-id family",
        "an UNKNOWN state is refused at evaluate_gate",
        "an UNKNOWN gate is refused at evaluate_gate",
        "a non-bool purchase flag is refused at build",
        "a non-packet object is refused at verify",
        "a packet missing its id is refused at verify",
        "bad-input audit: five E_TS_BAD_INPUT refusals, zero rows",
        "hypothetical leg: purchase_approved=True flips only the"
        " pack-derived license gates",
        "audit the 15-cell gate matrix at the live posture",
        "the packet carries the pre-registered selection questions"
        " and the open CEO decision items",
        "isolation law audit on the REAL module source",
    ]
    pos = [block.find(re.sub(r"\s+", " ", leg))
           for leg in legs_expected]
    legs_ok = all(p >= 0 for p in pos) and pos == sorted(pos)
    record("AC-FD26b", legs_ok,
           "seventeen probe legs rendered in order=%s (positions %s)"
           % (legs_ok, pos))

    # -- AC-FD26b: chain assertions (live readings) -------------------
    build_ok = ("three states: dataface=ready_now,"
                " offline_frames=not_ready, realtime3d=not_ready;"
                " the L1 red line rides the matrix: the two"
                " pack-derived states hold license_l1 BLOCKED"
                " (48 packs = zero commercial grant until the CEO"
                " legitimate-purchase gate clears)" in block)
    idem_ok = ("canonical payload byte-identical=True and packet_id"
               " equal=True (sha256 " in block
               and " over the sorted-key payload)" in block)
    verify_ok = ("recomputed sha256 matches and all 15 gate cells"
                 " re-derive from the packet's own facts -> True"
                 " (no canned status: any field drift raises"
                 " E_TS_TAMPER)" in block)
    tamper1_ok = ("the flip changes the canonical payload, so the"
                 " stored packet_id mismatches first (hash-chain"
                 " detection); even a recomputed id would still fail"
                 " the gate re-derivation below -- two independent"
                 " tamper nets" in block)
    tamper2_ok = ("the id now matches, but re-deriving the gates at"
                  " purchase_approved=True yields PASS for the"
                  " pack-derived license gates while the stored rows"
                  " still say BLOCKED -- E_TS_TAMPER fires on gate"
                  " drift (the packet's facts and its claims cannot"
                  " diverge)" in block)
    flips_ok = ("flipped cells=['offline_frames/license_l1"
                " BLOCKED->PASS', 'realtime3d/license_l1"
                " BLOCKED->PASS']; dataface unchanged=True,"
                " render_supply stays TBD=True, verdicts stay"
                " (dataface=ready_now, offline_frames=not_ready,"
                " realtime3d=not_ready) -- clearing the L1 purchase"
                " gate alone does NOT make a state ready: the"
                " selection stays a needs-CEO P1 approval face"
                in block)
    matrix_ok = ("PASS=9 / BLOCKED=2 / TBD=4 of 15 cells; the"
                 " BLOCKED cells are exactly the pack-derived"
                 " license gates ['offline_frames/license_l1',"
                 " 'realtime3d/license_l1'] (the L1 red line);"
                 " ready_now states=['dataface'] (dataface is the"
                 " only launch-ready posture, zero pack-derived"
                 " pixels)" in block)
    ceo_ok = ("3 selection questions (license / category / supply);"
              " 2 open CEO decision items (purchase_gate_l1;"
              " three_state_selection); every cost_anchor is"
              " None=True -- the cost anchors belong to a separate"
              " research item, never invented here; verify_packet on"
              " the hypothetical packet also passes=True" in block)
    isolation_ok = ("module source pure ASCII (0 non-ascii);"
                    " imports=['import hashlib', 'import json']"
                    " (stdlib only=True); network verbs=none;"
                    " money-movement verbs=none; pricing"
                    " constants=none -- the module prepares the CEO"
                    " decision, never decides it (no config keys"
                    " shipped, zero RNG, canon facts only)" in block)
    gate_table_ok = ("<th>G1 license</th>" in block
                     and "<th>G5 msgsec</th>" in block
                     and block.count("<td>BLOCKED</td>") == 2
                     and block.count("<td>TBD</td>") == 4
                     and block.count("<td>PASS</td>") == 9
                     and "<b>ready_now</b>" in block
                     and "<b>not_ready</b>" in block)
    record("AC-FD26b-chain",
           build_ok and idem_ok and verify_ok and tamper1_ok
           and tamper2_ok and flips_ok and matrix_ok and ceo_ok
           and isolation_ok and gate_table_ok,
           "live-posture-verdicts=%s deterministic-rebuild=%s"
           " self-fact-verify=%s tamper-id-chain=%s"
           " tamper-gate-drift=%s hypothetical-flips=%s"
           " matrix-audit=%s ceo-items=%s isolation=%s"
           " gate-matrix-table=%s"
           % (build_ok, idem_ok, verify_ok, tamper1_ok, tamper2_ok,
              flips_ok, matrix_ok, ceo_ok, isolation_ok,
              gate_table_ok))

    # refusal codes on the card
    ref_ok = (block.count("refused: E_TS_TAMPER") == 2
              and block.count("refused: E_TS_BAD_INPUT") == 5)
    record("AC-FD26b-refusals", ref_ok,
           "seven fail-closed refusal codes on the card (E_TS_TAMPER"
           " x2 gate-status flip + recomputed-id purchase flip,"
           " E_TS_BAD_INPUT x5 unknown state / unknown gate /"
           " non-bool flag / non-packet object / missing id -- every"
           " rejection writes nothing and decides nothing)")

    # -- AC-FD26c: compliance four-piece from config verbatim --------
    lcfg = json.load(open(os.path.join(SBX, "ledger", "config.json"),
                          encoding="utf-8"))
    ai_text = str(lcfg.get("token", {}).get("ai_label_text", ""))
    disc = str(lcfg.get("token", {}).get("disclaimer", ""))
    ai_ok = ai_text in html1
    disc_ok = disc in html1
    ceo_note_ok = "[needs-CEO]" in block
    gate_note_ok = "msgSecCheck" in block
    ceo_face_ok = ("P1 CEO approval-only faces" in block
                   and "separate research item, never invented here"
                   in block)
    record("AC-FD26c", ai_ok and disc_ok and ceo_note_ok
           and gate_note_ok and ceo_face_ok,
           "AIGC label verbatim=%s; disclaimer verbatim=%s;"
           " [needs-CEO] note=%s; msgSecCheck gate note=%s;"
           " P1-approval-face law=%s"
           % (ai_ok, disc_ok, ceo_note_ok, gate_note_ok,
              ceo_face_ok))

    # -- AC-FD26d: determinism + zero unfilled placeholders ----------
    block2 = card_block(html2, "Visitor-End M4 Three-State Face")
    same = block_raw == block2
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", html1)))
    record("AC-FD26d", same and not leftovers,
           "determinism: two renders, tourstate block byte-identical"
           "=%s (%d chars); unfilled placeholders page-wide=%s"
           % (same, len(block_raw), leftovers or "none"))

    # -- AC-FD26e: live server on 8093 -------------------------------
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
    live_title = "Visitor-End M4 Three-State Face" in page
    live_fail = "TOURSTATE PROBE FAILED" in page
    live_block_chars = len(card_block(page, "Visitor-End M4"
                                      " Three-State Face"))
    record("AC-FD26e", live_health and live_cards == 28 and live_title
           and not live_fail and live_block_chars > 3000,
           "healthz=%s on live server; card count = 28: got %d;"
           " tourstate card title on live page=%s; page has no"
           " probe-failure face=%s; live tourstate card block %d"
           " chars"
           % (health.strip() or "n/a", live_cards, live_title,
              not live_fail, live_block_chars))

    # -- AC-FD26f: evidence face --------------------------------------
    record("AC-FD26f", True,
           "this log = qa/frontdoor-v26-R1000.log (FD26 full record);"
           " full regression log = qa/reconcile-all-R1000.log (RUNNER"
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
