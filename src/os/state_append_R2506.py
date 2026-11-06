"""R2506 closeout: tick advance and this round's log lines.

Same in-place law the earlier appenders use: the file is CRLF with the log
array at sixteen spaces, so the new rows are inserted as JSON-escaped items
before the closing bracket and the tick is moved with an anchored substitution
that must hit exactly once. last_decision_rows is left alone because this
window measured zero new decision tokens and inventing a new count would
replace one unmeasured number with another.
"""

import io
import json
import re
import sys

P = "src/os/state.json"
LINES = [
    "2026-11-07 R2506 VERIFICATION window on the battery the register owed (reconcile-battery-R2505, opened by the R2505 product window as first=yes at a pre-registered 582 suites / 4468 criteria). Five-silence scan at open was clean at HEAD 62f68212 (git status empty, no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, content-addressed decisions diff new=0 over the 85-token baseline, group orders tail unchanged at 2026-11-06 23:46, benchmarks 2026-11-03 inside the seven-day gate). debt_gate read CLAIM-FIRST item=reconcile-battery-R2505 first=1 stale=no, so the R2168 mixed-tree rule ranked the battery ahead of the product face the queue head names (tech line 544 prefix AC-ADTR1, claimable=10). The target was re-measured BEFORE the run by importing reconcile_all.SUITES: 582 suites and 4468 criteria, byte for byte the register number.",
    "2026-11-07 R2506 LEG 1 RED ON A REAL BIRTH-SITE DEFECT, kept as evidence rather than rerun away: qa/reconcile-all-R2506.log (884071B) closes 'RUNNER FAIL (2 failed assertions)' after 1058.7s with 581/582 suites green and the single red os-residue-triage, whose AC-RTR6 read residue=291 triaged=286 untriaged=5 unmatched=0 expired=0 verdict=RESIDUE. The cause was measured rather than guessed: state/residue_triage.json was declared at R2491 with 286 entries while the live residue carried 291, the five undeclared rounds being R2494, R2497, R2498, R2501 and R2502, every one of them a product window that shipped and was committed without a declaration row. REPAIRED AT THE BIRTH SITE through the shipped batch writer residue_triage_append_batch (dry run first, predicted 80235B -> 81310B, delta 1075, entries 286 -> 291) at the MEASURED status DELIVERED for all five, declared_by R2506 until R2516; the executed write hit the prediction exactly with readback ok, no criterion was widened and no exemption was added. The repair plus the red leg were committed ALONE as eafb86ea before the retry, so the battery ran on a committed tree.",
    "2026-11-07 R2506 RETRY GREEN, MEASURED NOT QUOTED: qa/reconcile-all-R2506-retry.log is 883879B, utf-8 with bom=False, crlf=0 and lone_cr=0, closing line 'RUNNER PASS (582/582 suites green, reconcile controls 7/7, 1065.3s)', zero FAIL suite rows, and an independent recount over the 582 PASS suite rows sums criteria to EXACTLY 4468 - the pre-registered total, matched by measurement with nothing to name. Birth-site tmp reclaim read candidates=932 removed=932 busy=0 failed=0 at 326.59 MiB. The battery was launched detached through the shipped single writer src/os/battery_stream.py (pid in logs/battery-R2506.pid and logs/battery-R2506-retry.pid) with progress on the gitignored logs face, so the filtering-pipe trap was not re-paid and no capture landed in qa/.",
    "2026-11-07 R2506 FOUR FOLLOW-UP SECTIONS in the designed order: the dry run read SECTION matrix FAIL at on-disk 55964B against regenerated 55982B with no byte written while fingerprint/profile/census read PASS; docs/sandbox-suite-matrix.md was then regenerated stamp-aligned from THIS round own green evidence through --evidence plus --stamp-from, printing 55982 bytes at 582 suites / 4468 criteria with green=582/582, i.e. the document names the battery that actually passed rather than a borrowed older leg; --check read byte-identical at 55982B / 582 / 4468 and the re-run read all four sections PASS for VERDICT R2506 PASS failing=none (APPENDED 1950B eol_ok=True).",
    "2026-11-07 R2506 DEBT settled through the shipped writers: reconcile-battery-R2505 closed at line 226 (open 2->1, done 206->207, predicted 138541B -> 138544B and measured exactly, readback ok) and product-face-R2506 appended first=yes through debt_append (predicted 138544B -> 139598B, measured exactly, readback ok) naming the next window a PRODUCT face on the tech head state/queue/tech.md:544 prefix AC-ADTR1 artifact_disk_text_readability, whose criteria AC-ADTR1..AC-ADTR6 were pinned there at R2505 BEFORE any code. NO successor battery is registered: this window changed only state/, qa/ and docs/ - no registry module and no suite - so the registry stands unmoved at 582 suites / 4468 criteria. The first append attempt was REFUSED E_DEBTA_BAD_FIELD because the note carried equals signs, and the note was rewritten rather than the field law loosened.",
    "2026-11-07 R2506 honest disclosures: (a) this is an INTERNAL verification face - zero points on the Executive Protocol scale and nothing a CEO could open was built; what it buys is that the tree R2505 shipped is proved green end to end, and that five rounds of undeclared residue that nobody had noticed are now declared at their measured status. (b) the window overshot its 25-minute budget because the battery alone runs about 1065s and ran twice plus four follow-up sections, and that is disclosed rather than dressed up. (c) the red leg is the FIRST leg of this same round and is kept in git; the green is claimed only from the retry on the committed repair tree. (d) Docker is absent on this host so no containerised bring-up of the sandbox faces is claimed. (e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); tasks.md was not touched, it is the P-47 canonical board. (f) the S4U lane reconcile (loop-s4u-reconcile) still needs an ELEVATED shell and was not attempted here.",
    "R2506 tokens: local=~15k api=0 api_reason=verification window - one pre-registered battery re-measured by import before the run, one red leg kept with its real birth-site defect named by the shipped checker, one repair through the shipped batch writer at its predicted bytes and committed alone, one green retry at 582/582 with exactly 4468 criteria recounted independently, four follow-up sections PASS with the matrix regenerated stamp-aligned from this round own evidence, one debt row closed and the successor opened through their shipped writers, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
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
    before = len(json.loads(io.open(P, encoding="utf-8").read())["log"])
    block = "".join(",\r\n                " + json.dumps(line, ensure_ascii=False)
                    for line in LINES)
    text = text[:-len(tail)] + block + tail
    io.open(P, "w", encoding="utf-8", newline="").write(text)
    raw_after = io.open(P, "rb").read()
    state = json.loads(raw_after.decode("utf-8"))
    print("tick=%d loglen=%d bytes=%d crlf=%d lf_only=%d"
          % (state["tick"], len(state["log"]), len(raw_after),
             raw_after.count(b"\r\n"),
             raw_after.count(b"\n") - raw_after.count(b"\r\n")))
    return 0 if (state["tick"] == tick
                 and len(state["log"]) == before + len(LINES)) else 1


if __name__ == "__main__":
    sys.exit(main())