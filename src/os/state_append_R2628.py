"""R2628 state append: six log lines, one tick, the order watermark and the
decision-token baseline.

This window adopted the battery the previous window launched, watched it to
completion and closed the debt row it belonged to. Every line below carries a
measured number rather than a quoted one.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
NEW_ORDER = "2026-11-11 06:0x"

NEW_TOKENS = [
    "D-20261026-24",
    "D-20261111-01",
    "D-20261111-02",
    "D-20261111-03",
    "D-20261111-04",
    "D-20261111-05",
    "D-20261111-06",
]

LINES = [
    "2026-11-11 R2628 VERIFICATION window that CLOSED the battery the debt "
    "gate named first (reconcile-battery-R2624, pre-registered 643 suites / "
    "4834 criteria at R2624). Five readings at open: git status EMPTY at HEAD "
    "fa5d4a7f equal to origin/main with no index.lock, ZERO @BigDomain rows in "
    "cph4/evolution-ledger.md (atbd_lines=0 unreplied=0), the "
    "content-addressed D-/C- decisions scan read tokens=189 with new=7 over "
    "323 rows, the group orders tail carried ONE new row dated 2026-11-11 "
    "06:0x (committee batch 56, a bm-b host-offline physical-piece reminder "
    "addressed to the CEO and the HQ fleet seat), and benchmarks_refreshed "
    "2026-11-10 sits one day inside the seven-day gate. debt_gate read "
    "CLAIM-FIRST item=reconcile-battery-R2624 opened=R2624 carried=4 stale=yes "
    "open=42 first=1; queue_head named tech line 653 prefix AC-EDMI1 "
    "claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, 10/10.",

    "2026-11-11 R2628 THE SEVEN NEW DECISION TOKENS WERE JUDGED: "
    "D-20261111-01 is the batch-56 collection review and names BigDomain "
    "among the five companies carrying zero same-day rows, recorded at group "
    "level as a chronic violation reviewed but not acted on; D-20261111-02 "
    "repairs the backlog-merge deadline and corrects the BigCompute retrieval "
    "source; D-20261111-03 splits bm-b, bm-m and bm-d into physical, "
    "mechanism and un-onboarded classes with a 12:00 evidence deadline; "
    "D-20261111-04 moves the ledger split wave forward to 12:00 today; "
    "D-20261111-05 makes the external-audit stand-down final now that its "
    "seven-day objection window has expired; D-20261111-06 consumes the "
    "reflection line by attaching one owner and one deadline to three carried "
    "items; and D-20261026-24 appears only as the citation of that same "
    "objection window inside D-05. NOT ONE of the seven carries an execution "
    "face for this company - our own ledger files sit far below the group "
    "split thresholds and bm-b custody belongs to the fleet seat - so all "
    "seven are recorded as knowledge and the baseline advanced by exactly "
    "those seven tokens.",

    "2026-11-11 R2628 THE BATTERY THE R2627 WINDOW LAUNCHED WAS ADOPTED, NOT "
    "RE-RUN, AND IS GREEN BY MEASUREMENT: at open pid 82760 with its "
    "reconcile_all child 82032 were live at 463 PASS suite rows and zero red "
    "rows, so the leg was watched rather than restarted; it finished at "
    "06:37:54 local. MEASURED NOT QUOTED: qa/reconcile-all-R2627.log is "
    "1092115 bytes, utf-8 bom=False crlf=0 lone_cr=0 nul=0, 8575 lines, 643 "
    "PASS suite rows with 643 UNIQUE names, ZERO non-zero-exit rows, an "
    "INDEPENDENT recount over their own criteria fields summing to EXACTLY "
    "4834, and a closing line reading 'RUNNER PASS (643/643 suites green, "
    "reconcile controls 7/7, 2454.3s)'. The stream was polled four times while "
    "it ran (463 -> 528 -> 589 -> 637 PASS rows) with zero red rows at every "
    "read, so the green was watched rather than assumed.",

    "2026-11-11 R2628 REGISTRY, DOCUMENT, DEBT AND BOARD: "
    "reconcile_all.SUITES was recounted by import at 643 suites / 4834 "
    "criteria / 643 unique names / 643 unique paths, byte for byte the "
    "registered target, so no pre-registration moved. "
    "docs/sandbox-suite-matrix.md read FAIL (stale) BEFORE any byte was "
    "written, and the shipped check face named the cause honestly as an "
    "evidence face-mismatch (doc-recorded qa/reconcile-all-R2622.log against "
    "check-resolved qa/reconcile-all-R2627.log); it was then regenerated "
    "stamp-aligned from THIS round own green leg to 65690 bytes at 643 suites "
    "/ 4834 criteria whose green line reads 643/643, after which --check read "
    "byte-identical. DEBT through the shipped writers: "
    "reconcile-battery-R2624 was closed at its predicted and measured 200288B "
    "-> 200291B (line 367, open 42->41, done 308->309, readback ok) and "
    "product-face-R2628 was appended first=yes (200291B -> 200661B, readback "
    "ok) naming the next window a PRODUCT face on the queue head "
    "state/queue/tech.md:653 prefix AC-EDMI1, whose AC-EDMI1..AC-EDMI6 were "
    "pinned in that row at R2624 BEFORE any code. NO successor battery is "
    "owed: this window moved no product src byte and the registry is unmoved. "
    "queue_head re-read line 653 claimable=15 and queue_floor read FLOOR-MET "
    "at 5/5, 15/10, 10/10; no queue row was opened or closed, because a "
    "verification window writes no board row.",

    "R2628 honest disclosures: (a) ZERO product points on the Executive "
    "Protocol scale - nothing a CEO could newly open was built and none is "
    "claimed; the deliverable is the first GREEN 643/4834 battery this "
    "company has landed on a committed tree after five carried windows, a "
    "matrix document whose evidence column names this round own leg, and one "
    "debt row closed with one opened; (b) the leg was LAUNCHED BY THE "
    "PREVIOUS WINDOW and is only adopted and judged here, so those 2454.3 "
    "seconds of compute are not this window own work and are not presented as "
    "such; (c) this window spent most of its budget WAITING for that leg, "
    "which is disclosed rather than dressed up as a fast round; (d) the "
    "22-suite pass-lines=0 dialect fact recorded at R2584 was not re-measured "
    "this window and is not claimed; (e) the fold was NOT run here, so the "
    "FOLD-CLEAR reading at closeout is the only state-size evidence this "
    "window carries; (f) Docker is absent on this host so no containerised "
    "bring-up of the sandbox faces is claimed; (g) the real 19.9 debit and the "
    "real msgSecCheck still wait on CEO physical items (merchant id, "
    "mini-program appid/secret); (h) tasks.md was not touched, it is the P-47 "
    "canonical board; (i) BigDomain-OSLoop still needs an ELEVATED shell for "
    "its S4U re-registration (carried ceo-pending physical item "
    "loop-s4u-reconcile).",

    "R2628 tokens: local=~12k api=0 api_reason=verification window - one "
    "five-silence scan with the content-addressed decisions scan, the group "
    "orders tail and the ledger face actually read, seven new decision tokens "
    "judged and recorded as knowledge, one debt gate plus queue head and floor "
    "read, one live battery watched to completion and measured on encoding, "
    "row uniqueness and criteria faces with an independent recount to exactly "
    "4834, one registry target recounted by import, one designed matrix FAIL "
    "then one stamp-aligned regeneration checked byte-identical, one debt row "
    "closed and one opened through their shipped writers, and the "
    "state/export/heartbeat closeout; zero cloud calls and zero external API "
    "touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    merged = sorted(set(list(data["last_dec_tokens"]) + NEW_TOKENS))
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(LINES)
    expected["tick"] = int(data["tick"]) + 1
    expected["last_order"] = NEW_ORDER
    expected["last_dec_tokens"] = merged
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    item_indent = None
    for line in lines[start + 1:end]:
        stripped = line.strip()
        if stripped.startswith('"'):
            item_indent = len(line) - len(line.lstrip(" "))
            break
    if item_indent is None:
        print("REFUSED no item line to measure the indent")
        return 6
    inserted = [" " * item_indent + json.dumps(item, ensure_ascii=False) + ","
                for item in LINES[:-1]]
    inserted.append(" " * item_indent
                    + json.dumps(LINES[-1], ensure_ascii=False))
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    out = _retick(out, data["tick"], expected["tick"])
    out = _reorder(out, data["last_order"], NEW_ORDER)
    out = _retokens(out, merged)
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2628_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d layout_ok=%s tokens=%d"
          % (expected["tick"], after["bytes"], after["log_len"],
             after["layout_ok"], len(merged)))
    return 0


def _retick(text, old, new):
    needle = '"tick": %d' % int(old)
    if needle not in text:
        raise SystemExit("REFUSED tick field not found as %r" % needle)
    return text.replace(needle, '"tick": %d' % int(new), 1)


def _reorder(text, old, new):
    needle = '"last_order": %s' % json.dumps(old, ensure_ascii=False)
    if needle not in text:
        raise SystemExit("REFUSED order field not found as %r" % needle)
    return text.replace(needle, '"last_order": %s'
                        % json.dumps(new, ensure_ascii=False), 1)


def _retokens(text, merged):
    lines = state_io._lf_lines(text)
    head = None
    tail = None
    for index, line in enumerate(lines):
        if line.strip().startswith('"last_dec_tokens"'):
            head = index
        elif head is not None and line.strip().startswith("]"):
            tail = index
            break
    if head is None or tail is None:
        raise SystemExit("REFUSED last_dec_tokens block not found")
    closing = lines[tail]
    indent = len(lines[head + 1]) - len(lines[head + 1].lstrip(" "))
    block = [" " * indent + json.dumps(tok, ensure_ascii=False) + ","
             for tok in merged[:-1]]
    block.append(" " * indent + json.dumps(merged[-1], ensure_ascii=False))
    return state_io.EOL.join(lines[:head + 1] + block + [closing]
                             + lines[tail + 1:])


if __name__ == "__main__":
    sys.exit(main())
