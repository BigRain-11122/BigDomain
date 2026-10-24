# -*- coding: utf-8 -*-
"""R2072 state closeout: tick bump + round line + tokens line (surgical)."""
import io
import json

ST = "src/os/state.json"

ROUND = (
    "2026-10-24 R2072 (P2 tech-queue FIFO head after the docker-compose"
    " row stayed environment-gated) - the evidence-dialect suppression"
    " window seeded by R2068/R2069/R2070, where three consecutive rounds"
    " hand-normalised CRLF/LF mixed evidence logs after"
    " reconcile-daily-census cd7 failed. Five-silence scan clean:"
    " decisions.md 223 rows with zero new content-addressed tokens"
    " against the baseline, ledger zero new @BigDomain rows, group orders"
    " baseline unchanged at 2026-10-24 06:5x, benchmarks refreshed"
    " 2026-10-20 (inside 7 days), tree clean, no index.lock. Claimed the"
    " tech row with AC-EVD1..AC-EVD8 pre-registered in the queue row"
    " BEFORE the code existed (AC-EVD prefix git grep zero-occupancy,"
    " rc=1). Delivered src/os/evidence_writer.py: one canonical writer"
    " that normalises every EOL form to LF, encodes before touching disk,"
    " writes through a same-directory tempfile + os.replace, and then"
    " classifies the fresh file and raises EvidenceDialectError if the"
    " dialect is not tee; check_file is read-only and fix_file repairs the"
    " EOL axis only, refusing non utf-8 bytes; the CLI answers 0/2/3 for"
    " tee/non-tee/missing and prints the post class on fix."
    " src/os/evidence_census_R2072.py adds the production reading: a"
    " read-only census of all 1660 qa/ logs with a name/size/mtime_ns"
    " fingerprint taken before and after (unchanged, PASS) reporting"
    " tee=1134 cmd-raw=15 pwsh-capture=313 ps-utf16=98 other=100, and its"
    " own evidence file is self-checked tee ="
    " qa/evidence-writer-census-R2072.log. The suite"
    " src/os/test_evidence_writer.py passes 8/8 twice with identical"
    " stdout sha16 d39cf3aa81ac525120cd548859250b1d7a2c56937c9ded3d7321478d798659c5,"
    " is wired into reconcile_all as os-evidence-writer(8) -> RUNNER PASS"
    " 280/280 suites + controls 7/7 222.4s = qa/reconcile-all-R2072.log"
    " (that log self-checks class=tee crlf=0 through the new tool), and"
    " suite-matrix regenerates 280 suites / 2347 criteria with --check"
    " byte-identical. Honest boundaries: the funnel CLI already writes"
    " with an explicit LF newline so it needed zero change; the 328"
    " historical shell-captured copies stay outside code control, so the"
    " window delivers detection and repair tools instead of rewriting"
    " history bytes. Score 2 (runnable tool + passing suite + census"
    " evidence).")

TOKENS = (
    "R2072 tokens: local=~120k api=0 api_reason=five-silence scan +"
    " evidence writer suite 8/8 double-run + battery 280/280 + matrix"
    " regen/check + historical census reading + queue/state/export"
    " closeout, zero cloud calls")

path = ST
raw = io.open(path, encoding="utf-8", newline="").read()
before = json.loads(raw)

assert before["tick"] == 2071, before["tick"]
raw = raw.replace('"tick": 2071,', '"tick": 2072,', 1)

tail = ('"R2071 tokens: local=~135k api=0 api_reason=five-silence scan +'
        ' post-closure third-shape suite 7/7 double-run + battery 279/279 +'
        ' matrix regen/check + evidence log + state layout repair + proposal'
        ' BD-PROP-005 + state/export closeout, zero cloud calls"')
assert raw.count(tail) == 1, "tokens tail anchor count"
insert = tail + ",\r\n                " + json.dumps(ROUND) + ",\r\n" \
    + "                " + json.dumps(TOKENS)
raw = raw.replace(tail, insert, 1)

after = json.loads(raw)
assert after["tick"] == 2072
assert len(after["log"]) == len(before["log"]) + 2
assert after["log"][-2].startswith("2026-10-24 R2072")
assert after["log"][-1].startswith("R2072 tokens:")
io.open(path, "w", encoding="utf-8", newline="").write(raw)
print("state closeout ok tick=%d log=%d" % (after["tick"], len(after["log"])))