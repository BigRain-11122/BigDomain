"""R2232 closeout: state tick + log lines, status-export refresh,
backlog prepend, and the explore row 2/6 flip. Pure stdlib, ASCII
source, and every target keeps its own writer dialect (state.json
CRLF, export CRLF, markdown LF).
"""

import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
GROUP = os.path.dirname(os.path.dirname(ROOT))

STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
DECISIONS = os.path.join(GROUP, "docs", "decisions.md")

ROUND_LINE = (
    "2026-10-29 R2232 (five-silence scan clean at open: decisions.md"
    " measured 274 non-empty rows; a content-addressed token diff with a"
    " 4-digit-tolerant key read 185 tokens whose only apparent additions"
    " were the four known group-side rotation artefacts and three"
    " truncation variants of two tokens that the stored baseline carries"
    " in full (O-20261012-2330, O-20261026-0735) - so zero genuinely new"
    " rows and zero domain action, and the baseline is re-anchored to the"
    " measured set; the group ledger carries the same three @BigDomain"
    " patrol rows already paid off with zero unreplied; the group orders"
    " tail advanced by ONE row, the 2026-10-29 01:3x CEO-PROXY fleet"
    " event round R2.47 (bm-b LANE-DOWN plus the STARVED claim-bus"
    " diagnosis), which is the fleet dispatcher execution face and not a"
    " domain face, so it is logged aware-no-action and the own-orders"
    " baseline advances to 01:3x; benchmarks refreshed 2026-10-29 inside"
    " the seven-day gate; tree clean, no index.lock) - the P1 canonical"
    " rows stay blocked-on-CEO, the weekly proposal duty is met by"
    " BD-PROP-005, all four tech heads stayed gated (docker host absent,"
    " logs toolkit standing maintenance, member refunded schema"
    " product-gated, the live-mtime row waiting on a real normalized-mtime"
    " event), so this window claimed the explore head, the second seed of"
    " the R2230 family. Anchor check at HEAD 2026-10-29: AC-BAW,"
    " test_apimarket_buyeranswerwait, ledger-apimarket-buyeranswerwait,"
    " wait_seconds and running_wait were git grep -F zero-occupancy rc=1,"
    " while the face name itself appeared only in the queue seed row, one"
    " closeout prose blob and the export milestone text (code face"
    " untouched). Gap: api_buyer_questions merges every question of one"
    " buyer into a LIFETIME timeline and api_buyer_claims covers the"
    " after-sales side, but nothing told a buyer how long it actually"
    " waited for answers month over month - a buyer answered within"
    " minutes all spring and ignored all summer read exactly like one that"
    " never got an answer at all. Product: APIMarketFace."
    "api_buyer_answer_wait(buyer_id) - a twenty-one-key envelope with"
    " ten-key month rows. Booking law: an answer books in the UTC month of"
    " its own immutable answered_utc, never the month the question was"
    " asked, so the suite pins a February question discharged in March"
    " leaving February an honest zero row while March carries it as"
    " backlog; an open question has no month row at all and shows up in"
    " the envelope counters instead. Wait law: wait_seconds is always"
    " asked_utc -> answered_utc across the boundary, each month's fastest"
    " / slowest / mean are over the answers BOOKED in that month with the"
    " integer floor (the suite pins 21607/1296000 -> 658803 and the"
    " envelope 3488407 // 4 = 872101), and a zero month carries honest"
    " None latencies. Ballast: backlog_count + same_month_count =="
    " answered_count per row; the grid is contiguous with the monotone"
    " running_answered landing on the envelope total ([2,2,4]); the 2-vs-2"
    " peak tie resolves to the earlier January month and a zero month is"
    " never a peak; strict buyer isolation (cy's single answered question"
    " never leaks into bo's face); the envelope seller/listing counts are"
    " over every question asked INCLUDING still-open ones (2 sellers, 3"
    " listings) while rows count only what was answered in that month, so"
    " row sums are honestly >= the envelope; and the counters agree with"
    " api_buyer_questions on the same world (6 asked, 4 answered, 2 open,"
    " oldest open 2026-01-09). Evidence: SUITE PASS 8/8 double-run with"
    " byte-identical criterion lines (qa/apimarket-buyeranswerwait-R2232-a"
    ".log and -b.log, 837B each, utf-8 LF written by"
    " src/os/evidence_R2232.py after the child's piped stdout CRLF axis"
    " was normalised, never a shell redirection), criterion sha16"
    " a14589d66f9c35e2, wired ledger-apimarket-buyeranswerwait(8); seven"
    " adjacent question/answer suites green 8/8 each"
    " (qa/regression-R2232.log); PRODUCT_SHA_STABLE True. The first suite"
    " run was green on the first attempt, so no test expectation needed"
    " correcting this window. Honest debt: the full reconcile battery, the"
    " suite-matrix regeneration (416 expected) and the state fold are"
    " deferred to R2233 and recorded.")

TOKENS_LINE = (
    "R2232 tokens: local=~58k api=0 api_reason=five-silence scan with a"
    " decision baseline re-anchor + one explore seed claim with a"
    " zero-occupancy anchor check + one new buyer wait product face with"
    " an eight-criterion suite that passed 8/8 on the first run + a"
    " double evidence run through one python writer with the CRLF axis"
    " normalised + seven adjacent regressions + queue/backlog/state/export"
    " closeout, zero cloud calls")

HEAL_LINE = (
    "R2232 self-heal check: the BigDomain-OSLoop scheduled task exists"
    " (Running) but its principal still reads LogonType=Interactive with"
    " RunLevel=Limited, which the 2026-09-29 machine law forbids for every"
    " lane task; src/os/register_loop_task.ps1 already passes an explicit"
    " S4U principal but applying it needs an elevated shell and this"
    " session is unelevated, so the definition of the loop hosting this"
    " window was left untouched. Open local-lane item for an elevated"
    " window.")

BACKLOG_ENTRY = (
    "- [x] [done 2026-10-29 R2232] P3 explore head claim (R2232, seed"
    " R2230 2/6, criteria AC-BAW1..AC-BAW8 pre-registered in that queue"
    " row BEFORE the code; anchor check at HEAD 2026-10-29: AC-BAW,"
    " test_apimarket_buyeranswerwait, ledger-apimarket-buyeranswerwait,"
    " wait_seconds and running_wait git grep -F zero-occupancy rc=1):"
    " apimarket **buyer monthly answer wait** (api_buyer_answer_wait)."
    " Gap: api_buyer_questions is a lifetime timeline and api_buyer_claims"
    " covers after-sales, so how long one buyer actually waited for"
    " answers, month over month, had no face. Product: twenty-one-key"
    " envelope, ten-key month rows; an answer books in the UTC month of"
    " its own answered_utc (a February question discharged in March leaves"
    " February an honest zero row and raises March as backlog); wait_seconds"
    " is asked->answered across the boundary with the integer floor mean"
    " (658803 and 1085400 per row, 872101 pooled), row extremes, and"
    " honest None latencies on a zero month; backlog_count +"
    " same_month_count == answered_count per row; the contiguous grid"
    " carries running_answered [2,2,4] landing on the envelope total; the"
    " 2-vs-2 peak tie resolves to the earlier month and a zero month is"
    " never a peak; strict buyer isolation; the envelope counts every"
    " question asked (2 sellers, 3 listings) against rows that count only"
    " what was answered that month; identity with api_buyer_questions (6"
    " asked / 4 answered / 2 open / oldest open 2026-01-09). Evidence:"
    " SUITE PASS 8/8 double-run with byte-identical criterion lines"
    " (qa/apimarket-buyeranswerwait-R2232-a.log and -b.log, 837B each,"
    " utf-8 LF, criterion sha16 a14589d66f9c35e2), wired"
    " ledger-apimarket-buyeranswerwait(8), seven adjacent suites green"
    " (qa/regression-R2232.log), PRODUCT_SHA_STABLE True. Debt: the full"
    " reconcile battery and the suite-matrix regeneration are the R2233"
    " first item.")

EXPLORE_MARKER = (
    " [claimed+done 2026-10-29 R2232: delivered as api_buyer_answer_wait -"
    " twenty-one-key envelope, ten-key month rows; an answer books in its"
    " own answered_utc month (a February question discharged in March"
    " leaves February an honest zero row and books March as backlog),"
    " wait_seconds is asked->answered with the integer floor mean and"
    " honest None latencies on a zero month, backlog_count +"
    " same_month_count == answered_count per row, the contiguous grid with"
    " running_answered [2,2,4], the earlier-month peak tie-break, strict"
    " buyer isolation, the asked-side envelope against answered-side rows,"
    " identity with api_buyer_questions; evidence SUITE PASS 8/8 double-run"
    " byte-identical criterion sha16 a14589d66f9c35e2"
    " (qa/apimarket-buyeranswerwait-R2232-a.log and -b.log, 837B, utf-8"
    " LF), wired ledger-apimarket-buyeranswerwait(8)]")


def measured_tokens():
    with io.open(DECISIONS, encoding="utf-8") as handle:
        text = handle.read()
    toks = set(re.findall(r"[DCTOX]-\d{8}-\d{2,4}", text))
    return sorted(toks)


def write_state():
    with io.open(STATE, encoding="utf-8", newline="") as handle:
        d = json.load(handle)
    d["tick"] = 2232
    d["last_order"] = "2026-10-29 01:3x"
    d["last_decision_rows"] = 274
    d["last_dec_tokens"] = ",".join(measured_tokens())
    for line in (ROUND_LINE, TOKENS_LINE, HEAL_LINE):
        d["log"].append(line)
    body = json.dumps(d, indent=2, ensure_ascii=False)
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(body.replace("\n", "\r\n") + "\r\n")
    return len(d["log"]), len(d["last_dec_tokens"].split(","))


def write_export():
    with io.open(EXPORT, encoding="utf-8", newline="") as handle:
        d = json.load(handle)
    hits = 0
    for row in d["results"]:
        if isinstance(row, list) and len(row) >= 2 and "tick" in str(row[1]):
            row[0] = "2232"
            hits += 1
    d["outs"].insert(0, [
        "buyer monthly answer wait face (R2232)",
        "on",
        "apimarket.api_buyer_answer_wait(buyer_id): answers book in the"
        " UTC month of their own answered_utc, waits measured"
        " asked->answered with the integer floor mean, honest None on a"
        " zero month, backlog split, contiguous grid, earlier-month peak"
        " tie-break, strict buyer isolation, identity with"
        " api_buyer_questions; SUITE PASS 8/8 double-run byte-identical"
        " (qa/apimarket-buyeranswerwait-R2232-a.log and -b.log, 837B each,"
        " criterion sha16 a14589d66f9c35e2), wired"
        " ledger-apimarket-buyeranswerwait(8)"])
    d["results"].insert(0, [
        "R2232",
        "P3 explore head claim (R2230 seed 2/6): buyer monthly answer wait."
        " Product: api_buyer_answer_wait with a twenty-one-key envelope and"
        " ten-key month rows - answer-month booking (February stays an"
        " honest zero while the March discharge books as backlog),"
        " asked->answered wait seconds with the integer floor mean"
        " (658803 and 1085400 per row, 872101 pooled, extremes pinned), the"
        " backlog split, the contiguous grid with running_answered [2,2,4],"
        " the earlier-month peak tie-break, strict buyer isolation, the"
        " asked-side envelope (2 sellers, 3 listings) against answered-side"
        " rows, and identity with api_buyer_questions (6 asked / 4 answered"
        " / 2 open / oldest open 2026-01-09). Evidence: SUITE PASS 8/8"
        " double-run byte-identical criterion lines (837B each, utf-8 LF,"
        " sha16 a14589d66f9c35e2), wired ledger-apimarket-buyeranswerwait"
        "(8), seven adjacent suites green 8/8 each, PRODUCT_SHA_STABLE"
        " True. Debt carried: full battery and matrix regeneration are the"
        " R2233 first item."])
    sd = d["self_drive"]
    sd["log_lines_in_window"] = 22
    sd["substantive_non_idle_mention_lines"] = 22
    sd["queue_explore_open"] = 4
    body = json.dumps(d, indent=2, ensure_ascii=False)
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    with io.open(EXPORT, "w", encoding="utf-8", newline="") as handle:
        handle.write(body.replace("\n", "\r\n") + "\r\n")
    return hits


def write_backlog():
    with io.open(BACKLOG, encoding="utf-8", newline="") as handle:
        body = handle.read()
    with io.open(BACKLOG, "w", encoding="utf-8", newline="") as handle:
        handle.write(BACKLOG_ENTRY + "\n" + body)


def write_explore():
    with io.open(EXPLORE, encoding="utf-8", newline="") as handle:
        lines = handle.read().split("\n")
    flipped = 0
    for i, line in enumerate(lines):
        if ("R2230 2/6" in line and "api_buyer_answer_wait" in line
                and "claimed+done" not in line):
            lines[i] = (line.replace("[open, unclaimed]", "").rstrip()
                        + EXPLORE_MARKER)
            if not lines[i].startswith("- [x]"):
                lines[i] = lines[i].replace("- [ ]", "- [x]", 1)
            flipped += 1
            break
    with io.open(EXPLORE, "w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines))
    return flipped


def main():
    n, tok = write_state()
    hits = write_export()
    write_backlog()
    flipped = write_explore()
    print("state log lines=%d tokens=%d; export tick rows=%d; explore"
          " flipped=%d" % (n, tok, hits, flipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())