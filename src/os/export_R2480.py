"""export_R2480 - refresh docs/status-export.json for the R2480 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2480 verification window: the battery the R2479 cap work owed ran "
           "and came back GREEN on the first measured leg - 567/567 suites, "
           "controls 7/7, 4378 criteria EXACTLY as pre-registered, and its "
           "closing line now states 'suite cap=600s overrides=0', so the new "
           "declared cap is visible in the run's own summary instead of living "
           "only in source")

base.LATEST = ("qa/reconcile-all-R2480.log (863364B, no BOM, crlf=0, lone_cr=0, "
               "567 per-suite rows summing to 4378 criteria, zero FAIL rows, "
               "RUNNER PASS in 1301.2s) + docs/sandbox-suite-matrix.md "
               "(regenerated stamp-aligned to 54551B, 567 suites / 4378 "
               "criteria, green=567/567 self-describing, --check byte-identical)")

base.NEXT = ("2026-11-07 the next window should ship a BUSINESS face and name "
             "the supersession of the carried audit row product-face-R2456 "
             "(state/queue/tech.md:522 prefix AC-PFKC1), per the CEO standing "
             "order OB-20261105-003656-879; the strongest named candidate "
             "remains letting the hub page START a face from the browser, which "
             "R2477 disclosed as only half met, and every P-47 item beyond the "
             "shipped sandbox faces still waits on CEO physical items (merchant "
             "id, mini-program appid/secret)")

base.RESULT = (
    "2026-11-06 R2480 verification window delivered: the debt gate owed the "
    "battery from the R2479 cap work, so it ran FIRST and no product byte was "
    "touched (the R2168 mixed-tree rule). VERDICT-green, measured rather than "
    "reported: qa/reconcile-all-R2480.log carries 567 per-suite rows that sum "
    "to 4378 criteria with zero FAIL rows and zero non-zero exits, matching the "
    "pre-registration exactly, and the runner closed on 'PASS suites 567/567 "
    "green, expected criteria total=4378, suite cap=600s overrides=0' in "
    "1301.2s - the cap constant R2479 introduced is therefore visible in the "
    "run's own final line, and the three ledger suites that kept losing the old "
    "flat 300s cap finished inside it. PROVENANCE: an earlier, unclosed attempt "
    "of this same round had launched the battery detached and left the launcher "
    "and a green log on disk while state.json still read tick 2479, so this "
    "window ADOPTED that leg after re-measuring it byte for byte instead of "
    "spending another 22 minutes, and says so in the log rather than implying "
    "it launched the run. Four follow-up sections produced the designed order: "
    "the dry run read matrix FAIL at on-disk 54575B against regenerated 54551B "
    "with no byte written while fingerprint/profile/census read PASS, the "
    "matrix was regenerated from this round's own green evidence and --check "
    "read byte-identical at 54551B / 567 / 4378, and the write leg read all "
    "four sections PASS for VERDICT R2480 PASS. Debt: reconcile-battery-R2479 "
    "closed through its shipped CLI at the predicted 124971B -> 124975B "
    "(open 3->2, done 183->184, readback ok); no successor battery was "
    "registered because no product src byte moved and the registry is unmoved "
    "at 567 suites / 4378 criteria. Honest: this is a ZERO product-point "
    "window - nothing a CEO could open was rebuilt; the adopted body is a "
    "caller-dialect capture rather than the single-writer stream, measured "
    "crlf=0 / lone_cr=0 / no BOM and census DRIFT-CLEAN with its 529-entry "
    "baseline untouched; Docker is absent so no containerised bring-up is "
    "claimed; the real 19.9 debit and the real msgSecCheck still wait on CEO "
    "physical items; tasks.md was not touched; no fold was due at 49836B "
    "against the 78500B waterline."
)

base.OUTS = (
    "qa/reconcile-all-R2480.log + docs/sandbox-suite-matrix.md + "
    "state/debt.md + src/os/state.json + src/os/closeout_R2480.py + "
    "src/os/export_R2480.py + src/os/launch_battery_R2480.py + "
    "docs/status-export.json + heartbeat.txt + src/os/backlog.md"
)

if __name__ == "__main__":
    print(base.main())