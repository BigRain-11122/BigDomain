"""R2511 state append: tick 2511, the product-window round-log items, and the
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
    "2026-11-07 R2511 PRODUCT window on the tech head the register named (product-face-R2510, state/queue/tech.md:549 prefix AC-STPT1 stamp_text_coverage, criteria AC-STPT1..AC-STPT6 pinned in that row at R2509 BEFORE any code; five-silence scan clean at HEAD 7802a2da with git status empty, no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, content-addressed decisions diff new=0 over the stored token baseline at a measured 189 rows, group orders tail unchanged at 2026-11-06 23:46 so last_order stands, benchmarks 2026-11-03 inside the seven-day gate; debt_gate read CLAIM-FIRST item=product-face-R2510 opened=R2509, and the zero-occupancy anchor check read all five anchors free of shipped code). No battery was owed at open because R2510 discharged the register and nothing had moved but qa/, docs/ and state/.",
    "2026-11-07 R2511 SHIPPED src/os/stamp_text_coverage.py plus src/os/test_stamp_text_coverage.py and wired ONE guard statement into src/sandbox/suite_matrix.py::render, one statement after the evidence-name seam, at BOTH the check path and the generate path: the two CALLER-SUPPLIED strings the render prints - the generation stamp and the --stamp-from provenance source - were covered by no shipped reading, so a broken codepoint in either reached the CEO-visible artifact while every existing gate read publishable=True. The new reading derives the covered set by composing the real render ONCE with the values in hand and reading the result back through the shipped laws (suite_matrix.doc_stamp for the stamp line, matrix_stamp_provenance_line.recorded_source for the borrow), then asks patterns_label_readability.gate - the SAME shipped per-codepoint law - at CALL time; a render given no stamp_from prints no provenance line and the reading claims no such piece. A refusal is a readability verdict at exit 4 reading FAIL stamp-text with the piece and the value named and no artifact byte opened.",
    "2026-11-07 R2511 BIRTH-SITE REPAIR carried in the same window, named rather than buried: wiring the FIFTH guard seam made two already-shipped probes pay a second full composition, and R2509 had paid the same tax for the fourth seam. artifact_disk_text_readability and evidence_name_text_coverage now each read the new seam off the module through getattr instead of freezing the seam names they shipped with, so a probe that predates a seam still answers quietly. The gap that remains - every future seam must still be remembered per probe - is registered as the next tech seed rather than left implicit.",
    "2026-11-07 R2511 PROOF: AC-STPT1..AC-STPT6 SUITE PASS 6 of 6 TWICE with an identical digest plus three adjacent readability suites green (qa/stamp-text-coverage-R2511.log, legs=2 identical=True fails=0 adjacent=3, digest 52ADD8ADF4C4F5A3), and a live leg on the REAL tree reading CLEAN over both pieces with a doctored stamp and a doctored stamp_from each refused by the shipped law while the patterns file and the artifact kept identical digests (qa/stamp-text-coverage-live-R2511.log). The first suite run was RED on two counts and both were real: the committed matrix doc still carried 584 registry rows against the new 585, and this module docstring named the borrow path literally so AC-STPT4 caught it - the doc was regenerated stamp-aligned at 56263B over 585 suites and 4486 criteria with the check byte-identical, and the docstring was reworded at the birth site, after which the suite read 6 of 6 twice. Registry moved 584 suites / 4480 criteria to 585 / 4486 by exactly one row.",
    "2026-11-07 R2511 DEBT settled through the shipped writers: product-face-R2510 closed at line 231 (open 2->1, done 211->212, predicted 145469B -> 145472B and measured exactly, readback ok); reconcile-battery-R2511 appended first=yes (145472B -> 146223B, readback ok) because this window moved a registry module and added a suite, so the R2168 mixed-tree rule puts the full battery on the committed R2511 tree in the next window at the pre-registered 585 suites and 4486 criteria; product-face-R2511 appended first=no (146223B -> 146646B, readback ok) naming the next product face at tech head state/queue/tech.md:551 prefix AC-PSMR1 probe_seam_registry, whose six criteria were pinned there this window BEFORE any code. The tech floor was refilled to claimable=10 with that seed, and the queue head now reads line 551.",
    "2026-11-07 R2511 honest disclosures: (a) this is an INTERNAL technical face - it protects the CEO-visible document against broken text, but nothing a CEO could open was newly built, so it earns file-change credit rather than a shipped product. (b) the two red causes in the first suite run were mine and are named above rather than smoothed over. (c) the window ran past its 25-minute budget on the doc regeneration and the two-leg capture, disclosed rather than dressed up. (d) Docker is absent on this host so no containerised bring-up of the sandbox faces is claimed. (e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); tasks.md was not touched, it is the P-47 canonical board. (f) the S4U lane reconcile (loop-s4u-reconcile) still needs an ELEVATED shell and was not attempted here.",
    "R2511 tokens: local=~10k api=0 api_reason=product window - one six-criteria suite run twice with an identical digest plus three adjacent suites and one live leg, one matrix regeneration over the new 585-row registry, two shipped-probe birth-site repairs, one queue row closed plus one seed pinned, three debt rows settled through their shipped writers, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
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