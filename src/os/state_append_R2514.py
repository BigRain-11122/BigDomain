"""R2514 state append: tick 2514, the verification-window round-log items.

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
    "2026-11-07 R2514 VERIFICATION window on the battery the register owed (reconcile-battery-R2513, pre-registered 586 suites / 4492 criteria, and the target was RE-MEASURED by importing reconcile_all.SUITES before the launch as 586 suites and 4492 criteria - byte for byte the registered number, nothing to name). Five-silence scan at open was clean at HEAD f91953fc: git status empty, no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, content-addressed decisions diff new=0 over the stored 90-token baseline at a measured 189 rows, group orders tail unchanged at 2026-11-06 23:46 so last_order stands, benchmarks 2026-11-03 inside the seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2513 opened=R2513 carried=1 stale=no open=4 first=1, so the R2168 mixed-tree rule ranked the battery ahead of the product face queue_head named at tech line 552 prefix AC-PSF1.",
    "2026-11-07 R2514 LEG 1 RED AND THE RED LEG KEPT (qa/reconcile-all-R2514.log, 894331B): 585/586 suites green in the run, exactly one failed suite, os-residue-triage, whose AC-RTR6 read 5/6 with 2 failed assertions. The suite own measured line named the shape rather than the cause: residue=296 triaged=291 untriaged=5 expired=0 when it evaluates at the newest round the declaration claims to cover. Reproduced alone in 3.1s and read the same 5/6, so it is a defect and not load noise. READ THE CAUSE, DID NOT GUESS IT: the live reading at THIS round is RESIDUE with residue=296 triaged=291 untriaged=5, and the set difference named exactly five rounds - R2503, R2505, R2507, R2509, R2511 - i.e. five product windows that shipped and were committed without a declaration row. MEASURED ONCE MORE with the judge the writers use: at current=R2514 the same declaration reads residue=291 expired=286, because 286 of its entries carried until=R2511 and had ALL expired, while the declaration head still stood at declared_by R2491/R2506. The suite could not see that expiry because it evaluates at the declaration own newest round; the writer faces the true round, so the declaration needed renewal as well as five new rows.",
    "2026-11-07 R2514 REPAIR AT THE BIRTH SITE, NOT AT THE DETECTOR: the batch writer was tried first and REFUSED honestly with E_RTAB_NOT_TRIAGED naming 286 rounds it would leave behind, so its refusal was obeyed rather than worked around; the general re-pin writer was then used, dry run first (PLANNED round=R2514 until=R2524 entries=291->296 dropped=0 bytes predicted 81310->82268, STATUS DELIVERED 276 plus STAMP-ONLY-OPEN 20, zero DISAGREES), then --execute which hit the prediction exactly with a byte read-back (PINNED, 81310B -> 82268B). The re-read then read TRIAGED 296/296 untriaged=0 expired=0 and the suite read SUITE PASS 6/6 alone. No criterion was widened and no entry was dropped to match a prose count. The repair plus the red leg were committed ALONE as 8772a924 so the retry ran on a committed tree.",
    "2026-11-07 R2514 RETRY GREEN ON THE COMMITTED REPAIR TREE, measured not quoted: qa/reconcile-all-R2514-retry.log is 894139B, bom=False, crlf=0, closing RUNNER PASS (586/586 suites green, reconcile controls 7/7, 1076.8s), zero FAIL suite rows, and an independent recount over the 586 PASS rows summing to EXACTLY 4492 criteria - the pre-registered total matched by measurement. Launched detached and unfiltered through src/os/battery_stream.py (pid in logs/battery-R2514-retry.pid) so the filtering-pipe trap was not re-paid. FOUR FOLLOW-UP SECTIONS in the designed order: dry run read VERDICT FAIL failing=matrix at on-disk 56372B against regenerated 56368B with NO byte written while fingerprint read CLEAN domains=5, profile byte-identical and census DRIFT-CLEAN; docs/sandbox-suite-matrix.md was then regenerated stamp-aligned from THIS round own green evidence through src/sandbox/suite_matrix.py --stamp-from (56368 bytes, 586 suites / 4492 criteria, green=586/586 self-describing), --check read byte-identical, and the re-run read all four PASS for VERDICT R2514 PASS failing=none (APPENDED 1950B eol_ok=True).",
    "2026-11-07 R2514 DEBT, BOARD AND REGISTRY: reconcile-battery-R2513 closed through the shipped debtor at its predicted 147666B -> 147669B (line=235, open 4->3, done 214->215, readback ok) and product-face-R2514 was appended first=yes through the shipped appender at its predicted 147669B -> 148756B (readback ok) naming the next window a PRODUCT face on tech head state/queue/tech.md:552 prefix AC-PSF1 probe_seam_forwarding_scope, whose AC-PSF1..AC-PSF6 were pinned in that row at R2513 BEFORE any code. NO successor battery is owed because this window moved no product src byte and the registry is unmoved at 586 suites / 4492 criteria, which is exactly what the retry measured. The registry count was re-read by import rather than trusted: reconcile_all.SUITES length 586, criteria summed 4492.",
    "2026-11-07 R2514 honest disclosures: (a) zero product points on the Executive Protocol scale - nothing a CEO could open was built this window and none is claimed; the deliverable is a green 586/4492 battery plus the placeholder push shown to be real. (b) the red cause was BORN in five earlier product windows (R2503, R2505, R2507, R2509, R2511 shipped without a declaration row) and the expiry was born at R2491/R2506 when the until window was set; both are named here rather than swept. (c) the suite cannot see the expiry because it evaluates at the declaration own newest round, so a green suite hid a declaration that was already stale at the true round - a real blind spot, MEASURED here, and left named rather than patched in a verification window. (d) the batch writer refusal E_RTAB_NOT_TRIAGED was obeyed and the general re-pin writer used instead; the batch face therefore cannot renew a declaration on its own, which is a measured limit rather than a defect of this round. (e) the first commit message was rejected by the 500-byte gate at 517B and retried trimmed, disclosed rather than hidden. (f) the window ran far past its 25-minute budget (two full batteries at 586 suites each) and says so. (g) the S4U lane reconcile (loop-s4u-reconcile) still needs an ELEVATED shell and was not attempted; BigDomain-OSLoop still reads InteractiveToken. (h) Docker is absent on this host so no containerised bring-up is claimed; the real 19.9 debit and the real msgSecCheck still wait on CEO physical items, and tasks.md was not touched because it is the P-47 canonical board.",
    "R2514 tokens: local=~18k api=0 api_reason=verification window - five-silence scan, one registry target re-measured by import, one full 586-suite battery kept red, one cause read from two independent faces rather than guessed, one declaration renewed through the shipped re-pin writer at its predicted bytes, one repair committed alone, one full 586-suite retry green at the pre-registered 4492 criteria, four follow-up sections plus one stamp-aligned matrix regeneration checked byte-identical, one debt row closed and one opened through their shipped writers, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
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