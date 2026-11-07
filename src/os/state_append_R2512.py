"""R2512 state append: tick 2512, the verification-window round-log items, and
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
DEC_ROWS = 189

LINES = [
    "2026-11-07 R2512 VERIFICATION window on the battery the register owed (reconcile-battery-R2511, pre-registered at 585 suites / 4486 criteria, target re-measured by importing reconcile_all.SUITES before the launch). Five-quiet scan clean at HEAD fbafb177: git status empty, no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, content-addressed decisions diff new=0 over the stored token baseline at a measured 189 rows, group orders tail unchanged at 2026-11-06 23:46 so last_order stands, benchmarks 2026-11-03 inside the seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2511 opened=R2511 carried=1 stale=no open=3 first=1, so the R2168 mixed-tree rule put the battery on the committed R2511 tree ahead of any product byte.",
    "2026-11-07 R2512 FIRST LEG RED and KEPT: qa/reconcile-all-R2512.log (891669B class) read 584/585 green with exactly one failed suite, reconcile-daily-census cd7-live-real-tree exit=2 drift, and the cause was a REAL birth-site defect born in R2511 rather than load noise - the census named it in one line, qa/stamp-text-coverage-R2511.log class=pwsh-capture, i.e. the evidence file the previous window committed carried CRLF instead of the shipped utf-8 LF contract. Reproducing the census by hand read the same single flag (files=2635 flags=1 DRIFT-FLAG), so the red was confirmed alone before anything was touched.",
    "2026-11-07 R2512 REPAIR AT THE BIRTH SITE, NOT AT THE DETECTOR: the offending file was deleted and re-taken through the SHIPPED src/os/evidence_capture.py (--round R2511 --suite src/os/test_stamp_text_coverage.py --adjacent test_artifact_disk_text_readability.py,test_evidence_name_text_coverage.py --evidence qa/stamp-text-coverage-R2511.log), reading legs=2 identical=True adjacent=2 fails=0 at 5451B with crlf=0 lonecr=0 bom=False verified from raw bytes, and the census then read flags=0 DRIFT-CLEAN. Note the capture writes 5451B where the old file held 5627B because the shipped capture normalises line endings; the criterion content is unchanged. The repair was committed ALONE as efaf9e18 before the retry, so the retry ran on a committed tree (the R2496 order). One rough edge re-confirmed and deleted before commit: a probe invocation with an unsupported --help flag left a stray qa file named --help, the same unfixed edge R2483 disclosed.",
    "2026-11-07 R2512 RETRY GREEN: qa/reconcile-all-R2512-retry.log 891669B, bom=False, crlf=0, lone_cr=0 over raw bytes, closing line RUNNER PASS (585/585 suites green, reconcile controls 7/7, 1040.8s), zero FAIL suite rows, and an independent recount over the PASS rows summing to exactly 4486 criteria - the pre-registered total matched by measurement, not assumed. TMP reclaim read 932/932 worlds, 326.59 MiB.",
    "2026-11-07 R2512 FOLLOW-UP four sections through src/os/battery_followup.py in the designed order: the dry run FAILED on matrix by design (on-disk 56263B vs regenerated 56281B) with fingerprint CLEAN domains=5, profile byte-identical and census DRIFT-CLEAN; docs/sandbox-suite-matrix.md was then regenerated from THIS round own evidence through src/sandbox/suite_matrix.py with --stamp-from (PASS 56281 bytes, registry suites=585 criteria=4486, green=585/585), --check read byte-identical, and the write leg read four PASS for VERDICT R2512 PASS failing=none (APPENDED 1950B, eol_ok=True).",
    "2026-11-07 R2512 DEBT settled through the shipped writers: reconcile-battery-R2511 closed (line 232, open 3->2, done 212->213, 146646B -> 146649B, readback ok); NO successor battery is owed because the registry did not move this window (no module or suite changed - only an evidence file, the matrix document, the debt register and the closeout), so the next window owes a PRODUCT face; product-face-R2512 was appended first=yes naming the tech head state/queue/tech.md:551 prefix AC-PSMR1 probe_seam_registry (six criteria pinned there at R2511 BEFORE any code) at 146649B -> 146882B, readback ok, and the tech floor reads claimable=10 FLOOR-MET.",
    "2026-11-07 R2512 honest disclosures: (a) zero product points on the Executive Protocol scale - this window verified and repaired evidence, it built nothing a CEO could open. (b) the red cause was born in the PREVIOUS window (R2511 committed a CRLF evidence file) and is named as such rather than blamed on load. (c) the stray --help file and the two cancelled waits are disclosed. (d) Docker is absent on this host so no containerised bring-up is claimed. (e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); tasks.md was not touched. (f) the S4U lane reconcile (loop-s4u-reconcile) still needs an ELEVATED shell and was not attempted here. (g) no fold was due (state 67064B at open against the 78500B waterline).",
    "R2512 tokens: local=~14k api=0 api_reason=verification window - two full 585-suite batteries (one red leg kept, one green retry), one census reproduction, one birth-site evidence repair through the shipped capture, one matrix regeneration, three debt rows settled through their shipped writers, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
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