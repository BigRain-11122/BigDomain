"""R2206 closeout: state log, status export, backlog row (ASCII source)."""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
DECISIONS = os.path.abspath(os.path.join(
    ROOT, "..", "..", "docs", "decisions.md"))

ROUND = "R2206"

ROUND_LINE = (
    "2026-10-28 R2206 (five-silence scan at open: decisions.md 261 "
    "non-empty rows carrying 176 content-addressed D/C/O tokens, four "
    "new against the stored 172 baseline - D-20261006-05, D-20261007-04, "
    "D-20261007-05 and D-20261008-05 - each one a citation inside "
    "another seat's BigMoney/BigStream row rather than a BigDomain "
    "action face, so zero domain action and the baseline is re-anchored "
    "to the measured 176; the ledger carries the same three @BigDomain "
    "patrol rows already paid off with zero unreplied; the group orders "
    "tail is unchanged at the 2026-10-28 15:01 fleet auto-dispatch "
    "OB-20261028-150100-267; benchmarks refreshed 2026-10-27 inside the "
    "seven-day gate; tree clean, no index.lock) - the P1 canonical rows "
    "stay blocked-on-CEO, the weekly proposal duty is met by BD-PROP-005, "
    "all four tech heads stayed gated (docker host absent, logs toolkit "
    "standing maintenance, member refunded schema product-gated, the "
    "live-mtime row waiting on a real normalized-mtime event), so this "
    "window claimed the next explore seed (R2202 2/8). Gap statement: "
    "api_seller_answers reports lifetime fastest/slowest/mean latency and "
    "one answered count, so a seller who answered everything promptly "
    "last quarter and went silent this month read exactly like one that "
    "never answered; cadence had no face. Product: "
    "api_seller_answer_months(dev_account) - a nineteen-key envelope with "
    "ten-key month rows on two pinned laws. The cadence law books an "
    "answer in the UTC month of its own immutable answered_utc, never the "
    "asked month, so a March discharge of a January question raises only "
    "the March row, the January row does not move and a silent month "
    "stays an honest zero row; the fixture proves it with January one "
    "answer, February zero and March two. The latency law still measures "
    "response seconds from the question's asked_utc to the answer's "
    "answered_utc across the boundary, so the March backlog leg carries "
    "its true 4492800s wait while the same-month leg carries 10800s, the "
    "month mean is the same integer floor api_seller_answers uses, and a "
    "zero month carries None latencies rather than a fabricated zero. "
    "backlog_count plus same_month_count equals answered_count per row, "
    "the grid is contiguous from the first to the last answering month, "
    "running_answered is monotone and lands on the envelope total, and "
    "the peak takes the highest month with the earlier-month tie-break. "
    "Cross-face identity holds value for value against "
    "api_seller_answers (answered, buyer, listing, fastest, slowest, "
    "mean), while the envelope listing_count is every listing the seller "
    "owns against the answered-listing row asymmetry, the disclosed gap. "
    "Verification: SUITE PASS 8/8 double-run byte-identical sha256 "
    "3970c1195027e827 (qa/apimarket-sellermonths-R2206-a.log and -b.log, "
    "860 bytes each, crlf=0, single writer utf-8 LF), wired "
    "ledger-apimarket-sellermonths(8), seven adjacent question and "
    "monthly-family suites green (qa/regression-R2206.log: "
    "questionmonths, qna, selleranswers, buyerquestions, ratingmonths, "
    "marketwatchmonths, claimmonths). Honest notes: the anchor check for "
    "AC-SAM, the face name, suite, runner label and both key names "
    "preceded the code (six anchors git grep -F zero-occupancy against "
    "HEAD, rc=1) while the criterion TEXT landed in the same window as "
    "the code, the R2137/R2141/R2144/R2202/R2205 precedent, disclosed in "
    "the queue row; and the full reconcile battery plus the suite-matrix "
    "regeneration were NOT run inside this window, so the matrix still "
    "reads 400 suites until the next full battery walks this tree, which "
    "leads the next round."
)

TOKENS_LINE = (
    "R2206 tokens: local=~40k api=0 api_reason=five-silence scan with a "
    "four-token citation re-anchor + explore seed claim (criteria "
    "registered in the same window as the code, disclosed) + seller "
    "monthly answer cadence product face (cadence law on answered_utc, "
    "cross-month latency, backlog split, honest zero month, peak "
    "tie-break, cross-face identity) + suite 8/8 double-run "
    "byte-identical + seven adjacent regressions + state/export closeout, "
    "zero cloud calls; battery and matrix regeneration deferred"
)

BACKLOG_ROW = (
    "- [x] P3 explore head claim (R2206, seed R2202 2/8, criteria "
    "AC-SAM1..AC-SAM8 registered in state/queue/explore.md in this "
    "window): apimarket seller monthly answer cadence "
    "api_seller_answer_months(dev_account) - an answer books in the UTC "
    "month of its own answered_utc (never the asked month, so a silent "
    "seller reads as an honest zero row), response seconds still "
    "measured across the boundary with the integer-floor mean, the "
    "backlog split per row, a contiguous grid with None latencies on a "
    "zero month, the monotone running accumulator, the earlier-month "
    "peak tie-break, strict seller isolation, cross-face identity "
    "against api_seller_answers and a pure read. SUITE PASS 8/8 "
    "double-run byte-identical sha16 3970c1195027e827 "
    "(qa/apimarket-sellermonths-R2206-a.log / -b.log), wired "
    "ledger-apimarket-sellermonths(8), seven adjacent suites green. "
    "[done 2026-10-28 R2206] Honest debt: full reconcile battery and "
    "suite-matrix regeneration deferred to R2207 (matrix currently 400 "
    "suites).\n"
)

DO_TEXT = (
    "R2206 the sandbox developer-API marketplace and the OS toolchain "
    "for the silicon-domain public co-creation platform - the market can "
    "now read a seller's answering cadence month by month instead of one "
    "lifetime average: an answer books in the month the seller actually "
    "did the work, a silent month is an honest zero, and backlog "
    "discharged from an older month carries its true older wait."
)

OUTS = [
    "seller monthly answer cadence (api_seller_answer_months)",
    "on",
    "R2206: a seller whose answers are prompt one quarter and silent the "
    "next read exactly like one that never answered, because the "
    "lifetime latency face carries one flat aggregate. The face books "
    "each answer in the UTC month of its own answered_utc, keeps "
    "response seconds measured from the question's asked_utc so a "
    "cross-month discharge keeps its true older wait, splits backlog "
    "from same-month work per row, keeps an honest zero month with None "
    "latencies, runs a monotone accumulator and takes the earlier-month "
    "peak tie-break, all identical to api_seller_answers on the "
    "envelope.",
]

RESULTS = [
    [ROUND, "R2206: five-silence scan clean with four apparent new "
     "decision tokens, all citation-only inside other seats' rows, so "
     "zero domain action and the baseline re-anchored at 176. Product: "
     "api_seller_answer_months with AC-SAM1..AC-SAM8 anchored before "
     "the code and the criterion text in the same window (disclosed), "
     "SUITE PASS 8/8 double-run byte-identical (sha256 "
     "3970c1195027e827), wired as ledger-apimarket-sellermonths(8), "
     "seven adjacent suites green. Honest debt: full battery and "
     "suite-matrix regeneration deferred to R2207."],
]


def main():
    with io.open(STATE, encoding="utf-8") as fh:
        state = json.load(fh)

    with io.open(DECISIONS, encoding="utf-8") as fh:
        dec = fh.read()
    tokens = sorted(set(re.findall(r"(?:D|C|O)-20\d{6}-\d{2,4}", dec)))
    rows = sum(1 for line in dec.splitlines() if line.strip())

    state["tick"] = int(state.get("tick", 0)) + 1
    state["last_decision_rows"] = rows
    state["last_dec_tokens"] = ",".join(tokens)
    state["log"].append(ROUND_LINE)
    state["log"].append(TOKENS_LINE)

    with io.open(STATE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(state, ensure_ascii=False, indent=2) + "\n")

    with io.open(BACKLOG, encoding="utf-8") as fh:
        back = fh.read()
    if "R2206" not in back.splitlines()[0]:
        with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(BACKLOG_ROW + back)

    with io.open(EXPORT, encoding="utf-8") as fh:
        exp = json.load(fh)
    exp["export_ts"] = "2026-10-28T21:05:00+08:00"
    exp["do"] = DO_TEXT
    face = exp["ceo_face"]
    face["last_artifact"] = face.get("latest_artifact")
    face["current"] = (
        "R2206 seller monthly answer cadence: api_seller_answer_months() "
        "puts each answer in the month the seller actually answered, "
        "keeps the true cross-month wait, splits backlog from same-month "
        "work and shows a silent month as an honest zero")
    face["latest_artifact"] = (
        "qa/apimarket-sellermonths-R2206-a.log / -b.log (SUITE 8/8, "
        "sha256 3970c1195027e827..., byte-identical double run) + "
        "qa/regression-R2206.log (seven adjacent suites 8/8) + "
        "src/sandbox/ledger/apimarket.py (api_seller_answer_months, "
        "written 2026-10-28)")
    face["next_milestone"] = (
        "full reconcile battery plus suite-matrix regeneration on this "
        "tree (matrix 400 -> 401 suites), then the next explore seed "
        "with its criteria registered before the code - within 48h")
    exp["outs"].insert(0, OUTS)
    exp["results"].insert(0, RESULTS[0])
    sd = exp.get("self_drive", {})
    sd["log_lines_in_window"] = int(sd.get("log_lines_in_window", 0)) + 2
    sd["queue_explore_open"] = max(
        0, int(sd.get("queue_explore_open", 0)) - 1)
    exp["self_drive"] = sd

    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(exp, ensure_ascii=False, indent=2) + "\n")

    print("tick", state["tick"], "rows", rows, "tokens", len(tokens))


if __name__ == "__main__":
    main()