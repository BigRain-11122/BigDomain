"""R2509 state append: tick 2509, the product-window round-log items, and the
auxiliary decisions row count re-measured this window.

Appends in place at the canonical tail, keeps the file CRLF throughout, and
carries no new decision token because the content-addressed decisions diff read
zero new rows this window. ASCII source, stdlib only.
"""
import io
import json
import re
import sys

P = "src/os/state.json"
DEC_ROWS = 189

LINES = [
    "2026-11-07 R2509 PRODUCT window on the tech head the register named (product-face-R2508, state/queue/tech.md:547 prefix AC-EVNM1 evidence_name_text_coverage, criteria AC-EVNM1..AC-EVNM6 pinned in that row at R2507 BEFORE any code). Five-silence scan at open was clean at HEAD 0625ef55 plus this round own closeout (git status empty, no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, content-addressed decisions diff new=0 over the stored token baseline at a measured 189 rows, no 2026-11-07 row in either orders tail so last_order stands at 2026-11-06 23:46, benchmarks 2026-11-03 inside the seven-day gate). debt_gate read CLAIM-FIRST item=product-face-R2508 opened=R2508 carried=1 stale=no and no battery was owed because R2508 discharged it, so this window shipped a product byte first per the R2168 mixed-tree rule while queue_head named tech line 547 prefix AC-EVNM1 with claimable=10.",
    "2026-11-07 R2509 CLAIM AND SHIP: the R2507 disk-text gate derives everything the render reads off DISK through recording wrappers, but ITS coverage probe hands the render a CONSTANT evidence path, so the evidence file NAME the artifact prints sat outside every shipped reading - MEASURED at R2507, a copy of the real evidence named with U+FFFD rendered into docs/sandbox-suite-matrix.md while the shipped reading still returned publishable=True (qa/adtr-evidence-name-live-R2507.log). SHIPPED src/os/evidence_name_text_coverage.py plus its suite, and src/sandbox/suite_matrix.py::render now asks it one statement after the disk-text seam. The reading DERIVES what the render really prints from that path by composing the real render once against a recording os.path proxy (basename, recorded only when the path asked about IS the evidence path) and a recording rel() wrapper (the relative path the command line prints), plus the round tag the render own EVID_ROUND_RE law produces when it differs from the basename - then hands that set to patterns_label_readability.gate, the SHIPPED per-codepoint law, at CALL time. No second classifier exists here.",
    "2026-11-07 R2509 PROOF measured, not quoted: AC-EVNM1..AC-EVNM6 SUITE PASS 6/6 TWICE with an identical digest plus two adjacent readability suites green (qa/evidence-name-text-coverage-R2509.log, 5505B, legs=2 identical=True fails=0 adjacent=2) captured through the shipped evidence callable, which refuses a red or drifting leg. The CALL-time ask is proved by patching patterns_label_readability.gate and watching this face carry the gate own code and its refused piece verbatim. A doctored evidence name refuses the REAL render and the SHIPPED tool at exit 4 with 'FAIL evidence-name: E_PLR_SUSPECT piece=evidence.basename', the artifact keeps every byte it had, no residue is left, and --check reports that same refusal instead of the drift exit 2 - while a clean name renders byte-identically to the committed 56176-byte doc and --check keeps exit 0. The derivation legs prove the live basename and the closed relative path are in the set, that a different path yields its own pieces and its own round tag, that a name carrying no round tag claims no separate piece, and that no literal evidence name or path lives in the module. THREE OF MY OWN ASSERTIONS FAILED FIRST and were fixed as TEST or PRODUCT defects rather than loosened: the console could not encode the doctored name it was reporting (fixed with an ascii_safe rendering on the shipped tool path, which is the very case this face exists for), the recorded relative path carried backslashes because the probe recorded os.path.relpath before rel() normalised the separator (fixed by recording rel() own return, which is what the render prints), and the literal-scan leg had to name the live basename instead of banning the citation in the docstring.",
    "2026-11-07 R2509 BIRTH-SITE REPAIR DISCLOSED IN A SHIPPED MODULE: artifact_disk_text_readability.disk_strings patched only the two guard seams that existed when it shipped, so the FOURTH seam this window added to suite_matrix.render recursed into a live guard inside a probe and inherited whatever verdict was in flight - the ADTR suite went red with EvidenceNameRefused raised out of its own coverage probe. Repaired at the birth site: the probe now reads every remaining guard seam off the module (PLRC/PNLT plus whatever EVNM exists) and quietens each for the duration of the single probe, restoring all of them in a finally block, and its LIMIT docstring says so rather than claiming four attributes. No criterion was widened and every ADTR criterion still reads PASS 6/6.",
    "2026-11-07 R2509 REGISTRY, MATRIX, BOARD AND DEBT: one runner row os-evidence-name-text-coverage(6), so the registry reads 584 suites / 4480 criteria, recounted by importing reconcile_all.SUITES. docs/sandbox-suite-matrix.md was regenerated stamp-aligned from qa/reconcile-all-R2508.log to 56176B at 584 suites / 4480 criteria with --check byte-identical and its green line honestly reading 583/584. The claimed row 547 was closed through a per-round writer with its DISCHARGED note (predicted and measured 1664500B, readback ok) and ONE row was seeded from this window own MEASURED limit: composing the real render with a stamp and a stamp_from carrying U+FFFD printed both codepoints into the artifact while artifact_disk_text_readability and evidence_name_text_coverage both still returned publishable=True - seeded as AC-STPT1..AC-STPT6, and queue_floor then read FLOOR-MET 5/5 10/10 10/10 with the new head at line 549.",
    "2026-11-07 R2509 LIVE LEG on the real tree: qa/evidence-name-text-coverage-live-R2509.log reads verdict=CLEAN publishable=True over the three derived pieces (evidence.basename, evidence.relpath, evidence.round_tag) for the doc own evidence qa/reconcile-all-R2508.log at artifact digest 22fafc4c48d0b7e4, then swaps in a copy named with U+FFFD and records refused=True code=E_PLR_SUSPECT piece=evidence.basename name=reconcile-all-R2508-retr\\ufffdy.log codepoints=U+FFFD, with both the evidence digest and the artifact digest unchanged before and after.",
    "2026-11-07 R2509 honest disclosures: (a) two product points by the Executive Protocol reading - a real shipped write path gained a refusal and the CEO-visible artifact can no longer carry an unreadable evidence name - but nothing new opens for a CEO; the artifact it protects is docs/sandbox-suite-matrix.md. (b) the defect was MEASURED by an earlier window of mine (R2507) and named there, so this is a repair rather than a new discovery. (c) DISCLOSED LIMIT: deriving the set means composing the real render once, so five suite_matrix attributes are patched for that single probe (os, rel, PLRC, PNLT, ADTR) and all five are restored in a finally block; a concurrent in-process caller could observe that window, which the single-process CLI and render path never do. (d) SECOND LIMIT, measured rather than assumed: the recording only fires for the evidence path itself, so any future render that prints the evidence path through a different door would need that door added to the probe - stated so the seam list is not mistaken for a guarantee. (e) no battery ran this window by design (product face), and the register now owes reconcile-battery-R2509 at 584/4480 BEFORE any further product byte. (f) Docker is absent on this host so no containerised bring-up of the sandbox faces is claimed. (g) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); tasks.md was not touched, it is the P-47 canonical board. (h) the S4U lane reconcile (loop-s4u-reconcile) still needs an ELEVATED shell and was not attempted here.",
    "R2509 tokens: local=~21k api=0 api_reason=product window - one pre-registered face shipped with its six criteria, the render wired to it one statement after the disk-text seam, one suite proved twice with two adjacent suites green, three of my own assertions repaired as test or product defects, one shipped probe repaired at its birth site and disclosed, one registry row recounted by import, one matrix stamp-aligned regeneration checked byte-identical, one live leg plus one measured limit seeded, one queue row closed and one battery row opened through their shipped writers, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
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