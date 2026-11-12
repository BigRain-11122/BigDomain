"""R2677 verification window closeout: honest log lines plus one tick.

Every number typed below was measured in this window (the pid chain by command
line, the evidence bytes and their counters, the suite row and criteria
recounts, the registry by import, the matrix regeneration, the write-sensitive
re-run, the follow-up four sections and the debt readbacks) rather than copied
from the register.

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
        "2026-11-12 R2677 VERIFICATION window ADOPTED the retry leg R2676 left "
        "running by its evidence path and CLOSED reconcile-battery-R2675 GREEN at "
        "the pre-registered 655 suites / 4906 criteria. At open the tree carried "
        "no index.lock at HEAD d4c50260 and exactly TWO untracked files - the "
        "retry evidence and one one-off write-sensitive script the aborted "
        "attempt left behind - and both are named rather than swept. The "
        "five-silence scan ran in this window: ZERO unreplied @BigDomain rows "
        "(atbd_lines=0 unreplied_groups=0), the content-addressed decisions scan "
        "read rows=120 tokens=64 with ONE new token D-20261112-16, the group "
        "orders tail max_ts still the 2026-11-12 12:45 bm-a station ONBOARD row "
        "already carried as last_order, and benchmarks_refreshed 2026-11-10 "
        "sitting two days inside the seven-day gate.",
        "2026-11-12 R2677 MEASURED NOT QUOTED: pid 79940 and every battery_stream "
        "or reconcile_all process were GONE by command line before any byte was "
        "read, the stream closed on RUNNER PASS (655/655 suites green, reconcile "
        "controls 7/7, 3299.3s) and BATTERY rc=0 3300.6s, and qa/reconcile-all-"
        "R2676-retry.log read 1112947B at adoption and 1114898B after the "
        "follow-up append, utf-8, bom=False, crlf=0, lone_cr=0, nul=0, 8741 "
        "lines, 655 PASS suite rows carrying 655 UNIQUE names with ZERO FAIL "
        "rows, and an INDEPENDENT criteria recount summing to EXACTLY 4906; the "
        "registry was re-measured by import at 655 suites / 4906 criteria / 655 "
        "unique names / 655 unique paths, byte for byte the registered number.",
        "2026-11-12 R2677 R2614 DISCIPLINE WAS OWED AND IS HONOURED WITH ONE REAL "
        "RED NAMED: two closeout commits landed under the leg, so the "
        "write-sensitive set was re-run on the FINAL committed tree and its FIRST "
        "pass read THREE red suites (artifact-disk-text-readability, "
        "evidence-name-text-coverage, stamp-text-coverage, each failing AC-xx3 at "
        "rc=2), whose cause was read off the shipped tool own evidence line and "
        "not guessed - docs/sandbox-suite-matrix.md recorded qa/reconcile-all-"
        "R2673.log while the check resolved the NEWEST PASS leg qa/reconcile-all-"
        "R2676-retry.log, an evidence-face mismatch rather than content drift. A "
        "designed matrix FAIL was therefore recorded FIRST with NO byte written, "
        "then the doc was regenerated stamp-aligned from THIS round own green leg "
        "through the shipped write face to 67641B at 655 suites / 4906 criteria "
        "with its green line honestly reading 655/655, --check read byte-identical "
        "at rc=0, and the SAME write-sensitive set re-ran at rc-failures=0 over "
        "ELEVEN suites (qa/write-sensitive-R2677.log, 1024B) with SIX of them "
        "printing no PASS line and resting on their exit code alone, named rather "
        "than implied. The four follow-up sections then ran in the designed order: "
        "matrix PASS byte-identical 67641B, fingerprint CLEAN domains=5, profile "
        "byte-identical, census DRIFT-CLEAN, for VERDICT R2677 PASS failing=none "
        "(APPENDED 1951B eol_ok=True).",
        "2026-11-12 R2677 DEBT AND DECISION: reconcile-battery-R2675 was closed "
        "through the shipped debtor at its predicted and measured 213076B -> "
        "213079B (line 395, open 45->44, done 332->333, readback ok) and "
        "product-face-R2677 was opened first=yes at 213079B -> 213487B naming the "
        "next window a PRODUCT face on queue head state/queue/tech.md:677 prefix "
        "AC-PNAH1 while queue_head reads claimable=14 and queue_floor FLOOR-MET "
        "5/5 14/10 10/10; NO successor battery is owed because this window moved "
        "no product src byte and the registry is unmoved at 655/4906 re-measured "
        "by import. D-20261112-16 (the decision-round.ps1 cloud-gate third-site "
        "repair, executed by @HQ in the same shift) was judged KNOWLEDGE-ONLY "
        "with its number referenced and no BigDomain execution face. HONEST: (a) "
        "zero product points - nothing a CEO could newly open was built, and every "
        "P-47 business face still waits on CEO physical pieces (merchant id, "
        "mini-program appid/secret); (b) the leg was authored by the PREVIOUS "
        "window and is adopted by its evidence path rather than relaunched; (c) "
        "the one-off write-sensitive script the aborted attempt left untracked was "
        "USED for the R2614 re-run and is DELETED before the commit rather than "
        "staged; (d) src/os/state_io.py still pins ITEM_INDENT at 16 against this "
        "file own 2 and that shared constant is left alone deliberately, because "
        "other shipped writers read it and a change there deserves its own suite; "
        "(e) Docker is absent on this host; (f) tasks.md was not touched, it is "
        "the P-47 canonical board; (g) BigDomain-OSLoop still reads "
        "InteractiveToken and needs an ELEVATED shell for its S4U re-registration "
        "(carried ceo-pending physical item loop-s4u-reconcile).",
        "R2677 tokens: local=~9k api=0 api_reason=verification adoption window - "
        "one five-silence scan with the content-addressed decisions face, the "
        "group orders tail and the ledger face read, one pid-chain and stream-tail "
        "measurement before any byte, one evidence measurement on bytes with an "
        "independent suite and criteria recount, one registry target re-measured "
        "by import on four axes, one designed matrix FAIL with no byte written and "
        "one stamp-aligned regeneration checked byte-identical, two write-sensitive "
        "passes (three named reds then eleven green by rc) on the final committed "
        "tree, one follow-up run in the designed order landing VERDICT R2677 PASS, "
        "one debt close and one debt append with readback, one new decision token "
        "judged knowledge-only, one carried one-off script deleted before the "
        "commit, and the state/export/heartbeat closeout; zero cloud calls and "
        "zero external API touches",
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2677_")
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
