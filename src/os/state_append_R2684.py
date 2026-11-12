"""R2684 verification adoption window closeout: honest log lines plus one tick.

Every number below was measured in this window (the five-silence scan, the debt
gate, the registry by import on four axes, the evidence bytes, the write-sensitive
re-run, the follow-up sections and the debt/board writers) rather than copied from
the register.

The indent is hard-coded at two spaces on purpose: state_io.ITEM_INDENT is 16
while this file own log items sit at 2.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
INDENT = 2


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))
    lines = [
        "2026-11-13 R2684 VERIFICATION window on the battery the debt gate named "
        "first (reconcile-battery-R2682, pre-registered 658 suites / 4924 "
        "criteria at R2682). Five readings at open: git status carried exactly "
        "ONE untracked file qa/reconcile-all-R2683.log, which is this window own "
        "adopted work and not residue, at HEAD 6d66183e with no index.lock; ZERO "
        "unreplied @BigDomain rows (atbd_lines=0 unreplied_groups=0); the "
        "content-addressed decisions scan read rows=120 tokens=64 new=0; the "
        "group orders tail max_ts still the 2026-11-12 12:45 bm-a ONBOARD row "
        "already carried as last_order and judged knowledge-only for this "
        "company; benchmarks_refreshed 2026-11-10 sitting three days inside the "
        "seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2682 "
        "opened=R2682 carried=2 open=45 first=1, and queue_head read tech "
        "line=680 prefix=AC-PNAL1 claimable=14 with queue_floor FLOOR-MET 5/5, "
        "14/10, 10/10.",
        "R2684 MEASURED NOT QUOTED: the pid chain (99984) was GONE by command "
        "line before any byte was read, the stream logs/battery-R2683.stream "
        "closed at 1131410B on RUNNER PASS (658/658 suites green, reconcile "
        "controls 7/7, 2990.1s) and BATTERY rc=0 2992.2s after TMP RECLAIM "
        "697/697 at 241.16 MiB, and qa/reconcile-all-R2683.log read 1122545B at "
        "adoption, utf-8, bom=False, crlf=0, lone_cr=0, nul=0, 8844 lines, 658 "
        "PASS suite rows carrying 658 UNIQUE names with ZERO FAIL rows and ZERO "
        "duplicate names, and an INDEPENDENT criteria recount over their "
        "declared criteria fields summing to EXACTLY 4924; the registry was "
        "re-measured BY IMPORT at 658 suites / 4924 criteria / 658 unique names "
        "/ 658 unique paths, byte for byte the registered number.",
        "R2684 R2614 DISCIPLINE WAS OWED AND IS HONOURED WITH ITS FIRST PASS RED "
        "NAMED: two closeout commits (eb2bbb9d, 6d66183e) landed UNDER the leg, "
        "so the write-sensitive set was re-run on the FINAL committed tree at "
        "HEAD 6d66183e and its FIRST pass read THREE red - "
        "artifact-disk-text-readability, evidence-name-text-coverage and "
        "stamp-text-coverage, each failing one criterion at rc=1. The cause was "
        "read off the shipped check own line and not guessed: "
        "suite_matrix.py --check named the EVIDENCE FACE, doc-recorded "
        "qa/reconcile-all-R2680.log against check-resolved "
        "qa/reconcile-all-R2683.log, so this is a face mismatch rather than "
        "content drift. The designed matrix FAIL was therefore recorded FIRST "
        "with NO byte written (on-disk 69049B against regenerated 69045B) while "
        "fingerprint read CLEAN domains=5, profile byte-identical and census "
        "DRIFT-CLEAN, for VERDICT R2684 FAIL failing=matrix.",
        "R2684 FOLLOW-UP IN THE DESIGNED ORDER: docs/sandbox-suite-matrix.md was "
        "regenerated STAMP-ALIGNED from THIS round own green leg through the "
        "shipped write face to 69045 bytes at 658 suites / 4924 criteria with "
        "its green line honestly reading 658/658, and --check then read "
        "byte-identical at rc=0; the SAME write-sensitive set re-ran at "
        "rc-failures=0 over FOURTEEN suites on that final tree "
        "(qa/write-sensitive-R2684.log, 1548B, utf-8 LF, single writer) and "
        "seven of them print no PASS line beyond their rc, named rather than "
        "implied. The four follow-up sections then ran through "
        "src/os/battery_followup.py in the designed order: matrix PASS "
        "byte-identical 69045B, fingerprint CLEAN domains=5, profile "
        "byte-identical, census DRIFT-CLEAN, for VERDICT R2684 PASS "
        "failing=none (APPENDED 1951B eol_ok=True).",
        "R2684 DEBT AND BOARD THROUGH THE SHIPPED WRITERS: "
        "reconcile-battery-R2682 was closed at its predicted and measured "
        "215656B -> 215659B (line 401, open 45->44, done 338->339, readback ok) "
        "and product-face-R2684 was opened first=yes at 215659B -> 216097B "
        "naming the next window a PRODUCT face on queue head state/queue/tech.md "
        "line 680 prefix AC-PNAL1 with claimable 14 and the queue floor "
        "FLOOR-MET on all three lines; NO successor battery is owed because this "
        "window moved no product src byte and the registry is unmoved at "
        "658 / 4924 re-measured by import. The board top line was closed through "
        "src/os/backlog_carry_R2684.py at its predicted and measured 1056837B -> "
        "1061418B (readback ok) and ONE carried row was seeded for the R2685 "
        "product face.",
        "R2684 honest disclosures: (a) ZERO product points - a green battery is "
        "evidence, not something a CEO can open, and every P-47 business face "
        "still waits on CEO physical pieces (merchant id, mini-program "
        "appid/secret); (b) the leg was authored by the PREVIOUS window and is "
        "adopted by its evidence path rather than relaunched; (c) the matrix doc "
        "is restamped from THIS round own green leg, which is why its green line "
        "now honestly reads 658/658 instead of carrying a borrowed leg; (d) the "
        "one-off measurement and write-sensitive scripts in tmp/ are DELETED "
        "before the commit rather than staged; (e) Docker is absent on this "
        "host; (f) tasks.md was not touched, it is the P-47 canonical board; (g) "
        "BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED "
        "shell for its S4U re-registration (carried ceo-pending physical item "
        "loop-s4u-reconcile); (h) the inherited residue R2165 still reads "
        "untriaged in the older rows and was carried, not triaged.",
        "R2684 tokens: local=~11k api=0 api_reason=verification adoption window "
        "- one five-silence scan run natively with the content-addressed "
        "decisions face, the group orders tail and the ledger face read, one "
        "debt gate read, one queue head plus one queue floor read, one pid-chain "
        "check and one stream-tail read before any byte, one evidence measurement "
        "on bytes with an independent criteria recount, one registry target "
        "re-measured by import on four axes, one write-sensitive pass that read "
        "three named reds, one designed matrix FAIL with no byte written and one "
        "stamp-aligned regeneration checked byte-identical, one write-sensitive "
        "re-run at fourteen suites green by rc, one follow-up run in the designed "
        "order landing VERDICT R2684 PASS, one debt close and one debt append "
        "with readback, one board row closed and one carried row seeded through "
        "their shipped writer, and the state/export/heartbeat closeout; zero "
        "cloud calls and zero external API touches",
    ]
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(lines)
    expected["tick"] = tick + 1
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(lines):
        suffix = "," if index < len(lines) - 1 else ""
        inserted.append(" " * INDENT + json.dumps(item, ensure_ascii=False) +
                        suffix)
    bumped = []
    old_tick = '"tick": %d,' % tick
    new_tick = '"tick": %d,' % (tick + 1)
    seen = 0
    for row in doc_lines:
        if row.strip() == old_tick and not seen:
            bumped.append(row.replace(old_tick, new_tick))
            seen += 1
        else:
            bumped.append(row)
    if seen != 1:
        print("REFUSED tick line not found exactly once")
        return 3
    out = state_io.EOL.join(bumped[:end] + inserted + bumped[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    print("PREDICTED bytes=%d (gate 78500, margin %d)"
          % (len(payload), 78500 - len(payload)))
    if "--dry" in sys.argv:
        print("DRY run, nothing written")
        return 0
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2684_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d items_off_indent=%d" %
          (tick + 1, after["bytes"], after["log_len"],
           after["items_off_indent"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
