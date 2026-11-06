"""R2510 state append: tick 2510, the verification-window round-log items, and
the auxiliary decisions row count re-measured this window.

Appends in place at the canonical tail, keeps the file CRLF throughout, and
carries no new decision token because the content-addressed decisions diff read
zero new rows this window. ASCII source, stdlib only.
"""
import io
import json
import re
import sys

P = "src/os/state.json"
DEC_ROWS = 190

LINES = [
    "2026-11-07 R2510 VERIFICATION window on the battery the register owed (reconcile-battery-R2509, opened by the R2509 product window as first=yes at a pre-registered 584 suites / 4480 criteria). Five-silence scan at open was clean at HEAD 66b99a20 plus this round own receipt commit (git status empty, no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, content-addressed decisions diff new=0 over the stored 89-token baseline at a measured 190 rows, group orders tail unchanged at 2026-11-06 23:46 so last_order stands, benchmarks 2026-11-03 inside the seven-day gate). debt_gate read CLAIM-FIRST item=reconcile-battery-R2509 opened=R2509 carried=1 stale=no, so the R2168 mixed-tree rule ranked the battery ahead of the product face the queue head names (tech line 549 prefix AC-STPT1, claimable=10). The target was re-measured BEFORE the run by importing reconcile_all.SUITES: 584 suites and 4480 criteria, byte for byte the register number.",
    "2026-11-07 R2510 BATTERY GREEN ON THE FIRST LEG, measured not quoted: qa/reconcile-all-R2510.log is 889025B, utf-8 with bom=False, crlf=0 and lone_cr=0, closing with RUNNER PASS (584/584 suites green, reconcile controls 7/7, 1062.1s), zero FAIL suite rows, and an independent recount over the 584 PASS suite rows sums criteria to EXACTLY 4480 - the pre-registered total, matched by measurement with nothing to name. Birth-site tmp reclaim read candidates=932 removed=932 busy=0 failed=0 at 326.59 MiB. The battery was launched detached and unfiltered through the shipped single writer src/os/battery_stream.py (pid 67884 in logs/battery-R2510.pid, progress streamed to logs/battery-R2510.diag.log) so the filtering-pipe trap was not re-paid and no capture landed in qa by shell redirection. No red leg exists for this round because none was produced, stated rather than implied.",
    "2026-11-07 R2510 FOUR FOLLOW-UP SECTIONS in the designed order through the shipped src/os/battery_followup.py: the dry run read SECTION matrix FAIL at on-disk 56176B against regenerated 56172B with NO byte written while fingerprint/profile/census read PASS, then docs/sandbox-suite-matrix.md was regenerated stamp-aligned from THIS round own green evidence through the evidence flag plus stamp-from, printing 56172 bytes at 584 suites / 4480 criteria with green=584/584, i.e. the document the CEO might open names the battery that actually passed rather than a borrowed older leg; the check read byte-identical at 56172B / 584 / 4480 and the re-run read all four sections PASS for VERDICT R2510 PASS failing=none (APPENDED 1950B eol_ok=True).",
    "2026-11-07 R2510 DEBT settled through the shipped writers: reconcile-battery-R2509 closed at line 230 (open 2->1, done 210->211, predicted 143413B -> 143416B and measured exactly, readback ok) and product-face-R2510 appended first=yes through debt_append (predicted and measured 143416B -> 145469B, readback ok) naming the next window a PRODUCT face on the tech head state/queue/tech.md:549 prefix AC-STPT1 stamp_text_coverage, whose criteria AC-STPT1..AC-STPT6 were pinned in that row at R2509 BEFORE any code. NO successor battery is registered: this window changed only qa/, docs/ and state/ plus the register - no registry module and no suite - so the registry stands unmoved at 584 suites / 4480 criteria. The first append attempt was REFUSED E_DEBTA_BAD_FIELD because the note carried equals signs, and the note was rewritten without them rather than the field law loosened.",
    "2026-11-07 R2510 honest disclosures: (a) this is an INTERNAL verification face - zero points on the Executive Protocol scale and nothing a CEO could open was built; what it buys is that the tree R2509 shipped is proved green end to end rather than assumed. (b) the window overshot its 25-minute budget because the battery alone runs about 1062s plus four follow-up sections, and that is disclosed rather than dressed up. (c) the only reading that changed on a shipped artifact is the matrix doc, regenerated stamp-aligned from this round own evidence and checked byte-identical; no product module and no suite was touched. (d) Docker is absent on this host so no containerised bring-up of the sandbox faces is claimed. (e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); tasks.md was not touched, it is the P-47 canonical board. (f) the S4U lane reconcile (loop-s4u-reconcile) still needs an ELEVATED shell and was not attempted here.",
    "R2510 tokens: local=~11k api=0 api_reason=verification window - one pre-registered battery re-measured by import before the run, one green first leg at 584/584 with exactly 4480 criteria recounted independently, four follow-up sections PASS with the matrix regenerated stamp-aligned from this round own green evidence and checked byte-identical, one debt row closed and one product-face row opened through their shipped writers, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
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