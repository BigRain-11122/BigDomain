"""R2564 state append: bump tick and add this window own log lines.

state_fold still ships only a --check face and its layout reader refuses this
json.dump file (defect open since R2522), so the append is a proved load plus
dump round-trip: the file is re-serialised first and compared byte for byte
before any mutation, and a mismatch refuses instead of writing.
"""

import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-08 R2564 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2563, pre-registered 611 suites / 4642 criteria at "
    "R2563 because that window moved the registry by one row and shipped a "
    "document). Five-silence state at open was clean: git status empty, no "
    "index.lock, zero unreplied @BigDomain rows in cph4/evolution-ledger.md, "
    "content-addressed decisions diff new=0 over the stored baseline at a "
    "measured 273 rows / 164 tokens, group orders tail still 2026-11-08 12:06, "
    "and benchmarks 2026-11-03 inside the seven-day gate. The debt gate read "
    "CLAIM-FIRST item=reconcile-battery-R2563 first=1 with open=26, and the "
    "target was RE-MEASURED before anything ran by importing "
    "reconcile_all.SUITES from src/sandbox: 611 suites, 4642 criteria, 611 "
    "unique names and 611 unique paths - byte for byte the registered number, "
    "with my own first pass corrected because it summed a criteria list that "
    "is in fact a plain integer field.",
    "2026-11-08 R2564 A DUPLICATE LAUNCH HAPPENED AND IS DISCLOSED RATHER THAN "
    "HIDDEN: the first detached launch was read as dead five seconds later and "
    "was not, so a second battery was started on the same evidence path. Two "
    "runners were confirmed live by command line, the OLDER tree (pid 97104 "
    "then 59704) was killed and one single writer was kept. Killing the older "
    "leg made its parent write a PARTIAL evidence file (574130B, 329 pass "
    "rows, one row reading 'FAIL suite lobby-hub-ledger exit=2 pass-lines=0', "
    "no RUNNER line) which is disclosed here and is NOT this round evidence; "
    "the surviving leg overwrote that path on completion. MY MEASUREMENT ALSO "
    "TRAPPED ME ONCE: a progress count read a stale slice of the task output "
    "and I reported 335 suites as a stall before re-reading the file mtime.",
    "2026-11-08 R2564 GREEN LEG MEASURED NOT QUOTED (qa/reconcile-all-R2564."
    "log): 1026305B at the green leg and 1028256B after the follow-up block "
    "appended its own 1951B, utf-8 bom=False crlf=0 lone_cr=0 nul=0, closing "
    "RUNNER PASS (611/611 suites green, reconcile controls 7/7, 1727.0s) with "
    "ZERO FAIL suite rows, 611 unique suite names, and an independent recount "
    "over their criteria fields summing to EXACTLY 4642 - the registered total "
    "matched by measurement, not by trust. TMP RECLAIM closed 1343 candidates "
    "removed=1343 busy=0 failed=0 reclaimed=465.22 MiB.",
    "2026-11-08 R2564 FOLLOW-UP IN THE DESIGNED ORDER: the dry run read matrix "
    "FAIL first BY DESIGN at on-disk 59642B against regenerated 59700B with no "
    "byte written while fingerprint read CLEAN domains=5, profile byte-"
    "identical and census DRIFT-CLEAN; docs/sandbox-suite-matrix.md was then "
    "regenerated stamp-aligned from THIS round own green evidence through "
    "suite_matrix.py --stamp-from to 59700B at 611 suites / 4642 criteria with "
    "its green line honestly reading 611/611 self-describing, --check read "
    "byte-identical at rc=0, and the four sections re-ran to VERDICT R2564 "
    "PASS failing=none (APPENDED 1951B eol_ok=True). BIRTH SITE: my first "
    "matrix render omitted --stamp-from, which is the same AC-MSC4 class that "
    "turned R2560 red; it was caught by the follow-up dry run in this window "
    "and repaired before any commit.",
    "2026-11-08 R2564 DEBT AND BOARD: reconcile-battery-R2563 was closed "
    "through the shipped debtor at its predicted 175984B -> 175987B (line 306, "
    "open 26->25, done 263->264, readback ok) and product-face-R2564 was "
    "appended first=yes at its predicted 175987B -> 176429B (readback ok) "
    "naming the next window a PRODUCT face on tech head state/queue/tech.md:"
    "601 prefix AC-PNDCE1 probe_seam_name_binding_arm_mixed_residual_alias_"
    "attribute_import_alias_scope_from_scope, whose AC-PNDCE1..AC-PNDCE6 were "
    "pinned in that row at R2563 BEFORE any code. NO successor battery is owed "
    "because this window moved no product src byte and the registry is unmoved "
    "at 611 suites / 4642 criteria, which is exactly what the green leg "
    "measured; queue_head read claimable=12 at line 601 with the floor MET.",
    "R2564 tokens: local=~12k api=0 api_reason=verification window - one "
    "five-silence scan, one debt gate read naming the owed battery, one "
    "registry target re-measured by import, one duplicate-launch incident "
    "diagnosed by command line and resolved to a single writer, one 611-suite "
    "battery measured at its runner, criteria and encoding faces, one designed "
    "matrix FAIL, one stamp-aligned regeneration checked byte-identical, one "
    "four-section follow-up to PASS, one debt row closed and one opened "
    "through their shipped writers, and the state/export/backlog/heartbeat "
    "closeout; zero cloud calls and zero external API touches",
]

NEW_TOKENS = []


def main():
    raw = io.open(PATH, "rb").read()
    doc = json.loads(raw.decode("utf-8"))
    again = json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8")
    if again != raw:
        print("REFUSE: round-trip not byte-identical (%d vs %d)"
              % (len(again), len(raw)))
        return 2
    if doc["tick"] != 2563:
        print("REFUSE: tick is %s, expected 2563" % doc["tick"])
        return 2
    doc["tick"] = 2564
    doc["log"].extend(LINES)
    have = set(doc["last_dec_tokens"])
    have.update(NEW_TOKENS)
    doc["last_dec_tokens"] = sorted(have)
    doc["last_decision_rows"] = 273
    out = json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8")
    io.open(PATH, "wb").write(out)
    back = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    ok = (back["tick"] == 2564 and len(back["log"]) == len(doc["log"])
          and back["log"][-1].startswith("R2564 tokens")
          and back["last_decision_rows"] == 273)
    print("STATE tick=%s log_lines=%d tokens=%d rows=%d bytes=%d ok=%s"
          % (back["tick"], len(back["log"]), len(back["last_dec_tokens"]),
             back["last_decision_rows"], len(out), ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())