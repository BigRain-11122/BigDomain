"""R2513 state append: tick 2513, the product-window round-log items.

Appends in place at the canonical tail, keeps the file CRLF throughout, and
carries no new decision token because the content-addressed decisions diff read
zero new rows this window (189 rows, 89 live tokens over a 90-token baseline
whose one extra entry is the known prose artifact). ASCII source, stdlib only.
"""
import io
import json
import re
import sys

P = "src/os/state.json"
DEC_ROWS = 189

LINES = [
    "2026-11-07 R2513 PRODUCT window on the tech head the register named (product-face-R2512, state/queue/tech.md:551 prefix AC-PSMR1 probe_seam_registry, criteria AC-PSMR1..AC-PSMR6 pinned in that row at R2511 BEFORE any code). Five-silence scan at open was clean at HEAD ef3eb183 (git status empty, no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, content-addressed decisions diff new=0 over the stored 90-token baseline at a measured 189 rows, group orders tail unchanged at 2026-11-06 23:46 so last_order stands, benchmarks 2026-11-03 inside the seven-day gate). debt_gate read CLAIM-FIRST item=product-face-R2512 opened=R2512 carried=1 stale=no and no battery was owed because R2512 discharged it, so this window shipped a product byte first per the R2168 mixed-tree rule while queue_head named tech line 551 prefix AC-PSMR1 with claimable=10.",
    "2026-11-07 R2513 CLAIM AND SHIP: R2511 disclosed that wiring the FIFTH guard seam into src/sandbox/suite_matrix.py::render cost TWO hand edits to probes that had already shipped, because each probe enumerated the seam names it quieted and the list it shipped with could not see a seam that landed later; the repair made each probe read the newest seam off the module, which fixes today and still leaves the next seam to be remembered per probe. SHIPPED src/os/probe_seam_registry.py plus its suite. The seam set is DERIVED from the SHIPPED render at CALL time - every global name the render own code object asks, kept only when that global really carries a callable guard - so the module source spells none of the seam names, a seam added to the render appears the moment it is asked, and a global that stops carrying a guard leaves the set. Every module in the root that QUIETS at least one seam is a PROBE and reads COVERED or MISSING-SEAM naming the seam it forgets and its own file, and no probe is ever imported: the reading walks syntax trees as text, so a stale probe is NAMED rather than RUN and its composition is never paid.",
    "2026-11-07 R2513 PROOF measured, not quoted: AC-PSMR1..AC-PSMR6 SUITE PASS 6/6 TWICE with an identical digest plus three adjacent readability suites green (qa/probe-seam-registry-R2513.log, 4885B, utf-8 LF, legs=2 identical=True fails=0 adjacent=3) captured through the shipped evidence callable. The CALL-time derivation is proved TWO ways: the derived set equals an independent AST reading of the render SOURCE (five names), and replacing SM.render with a stand-in that asks one new guard global moves the set to exactly that new name, restored afterwards. A stale fixture probe reads MISSING-SEAM naming the forgotten seam and its file while the fixture carries a module-level raise that would have fired had it been imported, and the shipped tool refuses the fixture tree at exit 2. A module that names no seam reads OUT-OF-SCOPE and is explicitly not counted as clean, an unparseable source reads UNREADABLE rather than being skipped, and a file whose name carries a round token reads HISTORICAL - the same rule the library dialect sweep uses. A probe is never asked to quiet its OWN seam, which the owner answers through its own depth flag, so no invented defect is reported.",
    "2026-11-07 R2513 REGISTRY, MATRIX, BOARD AND DEBT: one runner row os-probe-seam-registry(6), so the registry reads 586 suites / 4492 criteria, recounted by importing reconcile_all.SUITES. The row moved the artifact, so docs/sandbox-suite-matrix.md was regenerated stamp-aligned from qa/reconcile-all-R2512-retry.log to 56372B at 586 suites / 4492 criteria with --check byte-identical and its green line honestly reading 585/586. The claimed row 551 was closed through a per-round writer with its DISCHARGED note (predicted and measured 1671421B, readback ok) and ONE row was seeded from this window own MEASURED limit: a probe that forwards its quieting through a shared helper module reads OUT-OF-SCOPE while the helper reads COVERED (fixture read forwarding_probe.py OUT-OF-SCOPE quieted=0 beside quiet_helper.py COVERED quieted=5), so the forwarding shape is invisible - seeded as AC-PSF1..AC-PSF6, and queue_floor then read FLOOR-MET 5/5 10/10 10/10 with the new head at line 552.",
    "2026-11-07 R2513 LIVE LEG on the real tree through the shipped single evidence writer: qa/probe-seam-registry-live-R2513.log (849B, class=tee) reads verdict=SEAMS-COVERED over 3 covered probes, 166 out-of-scope modules and 1191 historical one-shot scripts, with the render and the artifact digests unchanged across the reading, then swaps in a fixture stale probe and records MISSING-SEAM missing=STPT with the fixture tree reading SEAMS-STALE.",
    "2026-11-07 R2513 honest disclosures: (a) one product point: a runnable CLI reading plus its computed registry now names a stale probe instead of letting it silently fall behind the render, but nothing a CEO could open was newly built - it protects the shipped readability probes behind docs/sandbox-suite-matrix.md. (b) the defect was MEASURED at R2511 in that window own birth-site repair and re-measured here, so this is a repair rather than a new discovery. (c) DISCLOSED LIMIT, measured this window rather than assumed: a probe that forwards its quieting through a shared helper module reads OUT-OF-SCOPE while the helper reads COVERED, so the forwarding shape is invisible; it can only ever UNDER-report a stale probe and is seeded as the next tech row. (d) SECOND LIMIT: a helper module that only ever quiets on someone else behalf is itself counted COVERED, which inflates the covered count by one in that fixture shape - named rather than swept. (e) no battery ran this window by design (product face) and the register now owes reconcile-battery-R2513 at the pre-registered 586 suites / 4492 criteria BEFORE any further product byte. (f) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); tasks.md was not touched, it is the P-47 canonical board. (g) the S4U lane reconcile (loop-s4u-reconcile) still needs an ELEVATED shell and was not attempted here. (h) Docker is absent on this host so no containerised bring-up of the sandbox faces is claimed.",
    "R2513 tokens: local=~15k api=0 api_reason=product window - one pre-registered face shipped with its six criteria, one suite proved twice with three adjacent suites and one live leg, one seam set derived from the shipped render and proved by patching it, one stale probe named without being run, one registry row recounted by import, one matrix stamp-aligned regeneration checked byte-identical, one measured limit seeded as the next row, one queue row closed and one battery row opened through their shipped writers, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    raw = io.open(P, "rb").read()
    text = raw.decode("utf-8")
    tail = "\r\n  ]\r\n}\r\n"
    if not text.endswith(tail):
        print("FAIL state tail %r" % text[-30:])
        return 2
    tick_hits = re.findall(r'^\{\r\n  "tick": (\d+),', text)
    if len(tick_hits) != 1:
        print("FAIL tick anchor hits=%d" % len(tick_hits))
        return 2
    tick = int(tick_hits[0]) + 1
    text = text.replace('{\r\n  "tick": %d,' % int(tick_hits[0]),
                        '{\r\n  "tick": %d,' % tick, 1)
    text = re.sub(r'"last_decision_rows": \d+,',
                  '"last_decision_rows": %d,' % DEC_ROWS, text, count=1)
    before = len(json.loads(raw.decode("utf-8"))["log"])
    block = "".join(",\r\n                " + json.dumps(line, ensure_ascii=False)
                    for line in LINES)
    text = text[:-len(tail)] + block + tail
    io.open(P, "w", encoding="utf-8", newline="").write(text)
    raw_after = io.open(P, "rb").read()
    state = json.loads(raw_after.decode("utf-8"))
    lf_only = raw_after.count(b"\n") - raw_after.count(b"\r\n")
    print("tick=%d loglen=%d tokens=%d dec_rows=%d bytes=%d crlf=%d lf_only=%d"
          % (state["tick"], len(state["log"]), len(state["last_dec_tokens"]),
             state["last_decision_rows"], len(raw_after),
             raw_after.count(b"\r\n"), lf_only))
    return 0 if (state["tick"] == tick
                 and len(state["log"]) == before + len(LINES)
                 and lf_only == 0) else 1


if __name__ == "__main__":
    sys.exit(main())