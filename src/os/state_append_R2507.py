"""R2507 state append: tick 2507, six round-log items, decision baseline widened.

Appends in place at the canonical tail, keeps the file CRLF throughout, and
widens last_dec_tokens by the five decision tokens judged this window (all
knowledge-only for this company). ASCII source, stdlib only.
"""
import io
import json
import re
import sys

P = "src/os/state.json"

LINES = [
    "2026-11-07 R2507 PRODUCT window on the tech head the register named (product-face-R2506, state/queue/tech.md:544 prefix AC-ADTR1 artifact_disk_text_readability; the seed row stated the intent only and demanded the criteria land in a new row BEFORE any code, so this window first wrote src/os/claim_R2507.py and landed that claim row with AC-ADTR1..AC-ADTR6 on the board at 1657589 bytes, read back, before a single line of product code existed). Five-silence scan at open was clean at HEAD e4808d95 (git status empty, no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, group orders tail unchanged at 2026-11-06 23:46, benchmarks 2026-11-03 inside the seven-day gate). The content-addressed decisions diff read 5 new tokens over the 85-token baseline - D-20261107-08 subsidiary mtime patrol (0 violations), D-20261107-09 lane anchor promises with 89 of 329 tasks disabled, D-20261107-10 production backlog append, D-20261107-11 the bm-a branch split 771/511, and D-20261107-12 the ledger size red line - ALL judged KNOWLEDGE-ONLY with no BigDomain execution face, acknowledged with no action and the baseline widened by exactly those five. debt_gate read CLAIM-FIRST item=product-face-R2506 first=1 and no battery was owed because R2506 discharged it, so the product byte came first per the R2168 mixed-tree rule.",
    "2026-11-07 R2507 CLAIM AND SHIP: the R2505 non-label gate covers every string the render takes from the PATTERNS DOCUMENT, while the same render also interpolates text that comes from DISK - the registry suite labels and suite paths read live from reconcile_all.SUITES, and every string billable_faces pulls out of each product config.json (node keys, list items, the scalar itself). MEASURED at R2505: a registry label carrying U+FFFD rendered straight into docs/sandbox-suite-matrix.md while the shipped gate still read publishable=True (qa/patterns-non-label-live-R2505.log). SHIPPED src/os/artifact_disk_text_readability.py plus its suite, and src/sandbox/suite_matrix.py::render now asks it one statement after the non-label seam. The reading DERIVES its set, never lists it: the registry rows are handed to the real render as recording strings addressed registry[<i>].label and registry[<i>].path, and face_node is asked through a wrapper that hands back a recording view of the config node addressed config.<dotted.path>[<key>], so a suite added to the registry or a key added to a config.json is covered the moment the render reads it. The set goes to patterns_label_readability.gate - the SHIPPED per-codepoint law - at CALL time, and the refusal names the SOURCE (registry or config) beside the field path.",
    "2026-11-07 R2507 PROOF measured, not quoted: AC-ADTR1..AC-ADTR6 SUITE PASS 6/6 TWICE with an identical digest plus three adjacent suites green (qa/artifact-disk-text-readability-R2507.log, 4935B, utf-8 LF, legs=2 identical=True fails=0 adjacent=3) captured through the shipped evidence callable, which refuses a red or drifting leg. The CALL-time ask is proved by patching patterns_label_readability.gate and watching this face carry the gate own code verbatim with its refused field, and the source attribution is proved end to end: a doctored registry label refuses the REAL render and the SHIPPED tool at exit 4 with 'FAIL disk-text: E_PLR_SUSPECT source=registry field=registry[0].label', the artifact keeps every byte it had, no residue is left, and --check reports that same refusal instead of the drift exit 2 while a clean tree renders byte-identically to the committed 56095-byte doc and --check keeps exit 0. The coverage legs prove the derived set carries the live registry label and the config strings (1226 strings: registry 1166, config 60), that a key the render never reads is honestly not claimed, and that no literal registry label or config key lives in the module. TWO OF MY OWN ASSERTIONS FAILED FIRST and were fixed as TEST defects rather than loosened: the shipped-tool leg first passed a repo-relative evidence path to a tool that resolves it against the CWD, and the byte-identity leg first rendered with an empty status map instead of the doc's own parsed evidence.",
    "2026-11-07 R2507 REGISTRY, MATRIX, BOARD AND DEBT: one runner row os-artifact-disk-text-readability(6), so the registry reads 583 suites / 4474 criteria, recounted by importing reconcile_all.SUITES. The row moved the artifact, so docs/sandbox-suite-matrix.md was regenerated stamp-aligned from qa/reconcile-all-R2506-retry.log to 56095B at 583 suites / 4474 criteria with --check byte-identical and its green line honestly reading 582/583. The seed row 544 and this window's claim row were both closed through a per-round writer with their DISCHARGED note (predicted and measured 1661208B, readback ok) and ONE row was seeded from this window own MEASURED limit: the artifact also prints the evidence file NAME, and the coverage probe hands the render a constant there, so a copy of the real evidence named with U+FFFD rendered into the document with the codepoint carried while the reading still returned publishable=True (qa/adtr-evidence-name-live-R2507.log) - seeded as AC-EVNM1..AC-EVNM6, and queue_floor then read FLOOR-MET 5/5 10/10 10/10 with the new head at line 547.",
    "2026-11-07 R2507 LIVE LEG on the real tree: qa/artifact-disk-text-readability-live-R2507.log (373B, utf-8 LF, written through the shipped single writer) reads verdict=CLEAN publishable=True over 1226 disk-sourced strings, then swaps one registry label for a U+FFFD copy and records refused=True code=E_PLR_SUSPECT source=registry field=registry[0].label with the artifact digest unchanged before and after (ed6139f82dd894dc), and the patterns digest unmoved at ea5773ac0c113fe1.",
    "2026-11-07 R2507 honest disclosures: (a) two product points: a real shipped write path gained a refusal and the CEO-visible artifact can no longer carry unreadable disk-sourced text, but nothing new opens for a CEO - the artifact it protects is docs/sandbox-suite-matrix.md. (b) the defect was MEASURED by an earlier window of mine (R2505) and named there, so this is a repair rather than a new discovery. (c) DISCLOSED LIMIT: deriving the read set means composing the real render once, so four module attributes are patched for that single probe (the registry SUITES list, suite_matrix.face_node, and the two guard seams) and all four are restored in a finally block; a concurrent in-process caller could observe that window, which the single-process CLI and render path never do. (d) SECOND LIMIT, measured rather than assumed: the shipped law flags a script bucket no other label in the same set carries, so a legitimate mixed-script disk set could be named - this face exists for BROKEN codepoints and its suite proves that case. (e) no battery ran this window by design (product face), and the register now owes reconcile-battery-R2507 at 583/4474 BEFORE any further product byte. (f) Docker is absent on this host so no containerised bring-up of the sandbox faces is claimed. (g) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); tasks.md was not touched, it is the P-47 canonical board.",
    "R2507 tokens: local=~26k api=0 api_reason=product window - one claim row pre-registered on the board before any code, one face shipped with its six criteria, the render wired to it one statement after the non-label seam, one suite proved twice with three adjacent suites green, two of my own assertions repaired as test defects, one registry row recounted by import, one matrix stamp-aligned regeneration checked byte-identical, one live leg plus one measured limit seeded, one queue row closed with a per-round writer and one battery row opened through the shipped writers, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
]

NEW_TOKENS = ["D-20261107-08", "D-20261107-09", "D-20261107-10",
              "D-20261107-11", "D-20261107-12"]


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
    anchor = '"D-20261107-07"],'
    if text.count(anchor) != 1:
        print("FAIL token anchor hits=%d" % text.count(anchor))
        return 2
    added = "".join(',\r\n    "%s"' % token for token in NEW_TOKENS)
    text = text.replace(anchor, '"D-20261107-07"%s],' % added, 1)
    before = len(json.loads(raw.decode("utf-8"))["log"])
    block = "".join(",\r\n                " + json.dumps(line, ensure_ascii=False)
                    for line in LINES)
    text = text[:-len(tail)] + block + tail
    io.open(P, "w", encoding="utf-8", newline="").write(text)
    raw_after = io.open(P, "rb").read()
    state = json.loads(raw_after.decode("utf-8"))
    lf_only = raw_after.count(b"\n") - raw_after.count(b"\r\n")
    print("tick=%d loglen=%d tokens=%d bytes=%d crlf=%d lf_only=%d"
          % (state["tick"], len(state["log"]), len(state["last_dec_tokens"]),
             len(raw_after), raw_after.count(b"\r\n"), lf_only))
    return 0 if (state["tick"] == tick
                 and len(state["log"]) == before + len(LINES)
                 and lf_only == 0) else 1


if __name__ == "__main__":
    sys.exit(main())