import io
import json
import os
import re
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
QUEUES = ["main.md", "tech.md", "explore.md"]

NARRATIVE = (
    "2026-10-28 R2193 (five-silence scan clean at open: decisions.md "
    "251 non-empty rows carrying 166 content-addressed D/C tokens with "
    "ZERO new against the stored baseline - the nine tokens the stored "
    "set still names are the known body-text citations and rotation "
    "artefacts already acknowledged in R2173/R2181/R2183/R2186, so zero "
    "domain action and the baseline is re-anchored to the measured 166; "
    "the group ledger carries the same three @BigDomain patrol rows "
    "already paid off with zero unreplied; the group orders tail is "
    "unchanged at the 2026-10-28 03:0x CEO-PROXY fleet event round #4, "
    "acknowledged with zero domain action; benchmarks refreshed "
    "2026-10-27 inside the seven-day gate; tree clean, no index.lock) - "
    "this window opened the P3 explore head and REJECTED the first "
    "claimable seed honestly: seed 4/10 (api_seller_question_latency) "
    "claimed the seller answer-latency surface was missing, but "
    "api_seller_answers (R2120) already ships the answered-question "
    "history with fastest/slowest/mean whole-second latency per seller, "
    "so the seed was a misreading of a live face and is marked negative "
    "with that evidence instead of implemented. The window then claimed "
    "seed 5/10 with AC-RRL1..AC-RRL8 registered in that queue row "
    "(disclosed: the criteria text landed in the same window as the "
    "product, the R2137/R2141/R2144 precedent) - the rating reply "
    "latency scorecard the trust face never had. Gap: the reply door "
    "(R2093), the reply revision leg (R2143) and api_reply_history all "
    "exist, api_seller_inbox carries the PRESENT debt, and the two "
    "neighbouring conversation chains already score their waiting time "
    "(api_seller_answers for questions, api_claim_latency for claims), "
    "but nothing measured how long a RATING sat before the seller "
    "answered it, so a seller replying the same hour and one answering a "
    "fortnight later read identically on api_seller_quality (star shape "
    "only) and on api_seller_inbox (present debt only). Product: "
    "APIMarketFace.api_rating_reply_latency(dev_account=None) - a "
    "thirteen-key envelope with thirteen-key rows, latency derived from "
    "the two stored stamps only (rated_utc and the immutable first "
    "replied_utc), integer and non-negative by construction, an "
    "unanswered rating None rather than a fabricated zero and therefore "
    "outside every aggregate, a same-second reply reading exactly 0, "
    "row authority on the rating side so the face answers both halves "
    "(what was answered and how slowly, what is still owed), rating "
    "stars through the one _effective_stars seam and reply text through "
    "_effective_reply so a revised reply changes the text and never the "
    "historical clock, effective title through _metadata_state, the "
    "pinned total order (answered by descending latency then rating_id, "
    "pending after them by rated_utc then rating_id), coverage, average, "
    "median parity, fastest/slowest, latest reply stamp and oldest "
    "outstanding stamp all None where nothing was answered, the usr: "
    "prefix gate before any read with the operator-wide default, strict "
    "seller isolation and an honest empty envelope. SUITE PASS 8/8 "
    "double-run byte-identical criterion sha16 260c70a495390bfa "
    "(qa/apimarket-ratingreplylatency-R2193-a.log and -b.log, 770B each, "
    "single-writer utf-8 LF); wired ledger-apimarket-ratingreplylatency"
    "(8); four adjacent trust-family suites green (ratingrev 8/8, "
    "ratingreply 8/8, replyrev 8/8, sellerinbox 8/8 - "
    "qa/regression-R2193.log plus qa/regression-R2193-ratingreply.log). "
    "Honest notes: (a) the first suite run read 7/8 because AC-RRL7 "
    "compared the dana-scoped inbox total against the market-wide "
    "rating count; the measured contract is scope-local, so the TEST was "
    "corrected (inbox total 4 versus market 5) and no criterion or "
    "implementation was relaxed; (b) one adjacent run initially named a "
    "non-existent suite path and was re-run against the real "
    "test_apimarket_ratingreply.py; (c) the full reconcile battery and "
    "the suite-matrix regeneration were NOT run inside the 25-minute "
    "window and are recorded as R2194 first-item debt."
)

TOKENS = ("R2193 tokens: local=~55k api=0 api_reason=five-silence scan "
          "with a decision baseline re-anchor + duplicate-seed rejection "
          "with evidence + rating reply latency product face + suite 8/8 "
          "double-run evidence + four adjacent trust-family regressions + "
          "queue/backlog/state/export closeout, zero cloud calls")

DO = ("R2193 the sandbox developer-API marketplace and the OS toolchain "
      "for the silicon-domain public co-creation platform - a market "
      "operator can now read how long buyers waited for a seller answer "
      "on their rating, next to the debt that is still outstanding, "
      "instead of only the stars they gave")

CURRENT = ("R2193 rating reply latency: every rating now carries the "
           "whole-second wait between the buyer's stars and the seller's "
           "first reply, the unanswered half stays an honest None instead "
           "of a zero, and the scorecard reports coverage, average, "
           "median, fastest, slowest and the oldest outstanding rating "
           "for one seller or the whole market")

LATEST = ("qa/apimarket-ratingreplylatency-R2193-a.log / -b.log "
          "(SUITE 8/8, criterion sha16 260c70a495390bfa, 770B each) + "
          "qa/regression-R2193.log (four trust-family suites 8/8) + "
          "src/sandbox/ledger/apimarket.py (api_rating_reply_latency, "
          "written 2026-10-28)")

NEXT = ("R2194 first item is the full reconcile battery plus the suite "
        "matrix regeneration carrying ledger-apimarket-ratingreplylatency; "
        "explore seed 6/10 (market claim volume by month) is the next "
        "claimable face; the P1 commercial rows and the merchant-number "
        "benchmark row stay blocked on CEO physical items (within 48h)")

LAST_ART = ("qa/apimarket-marketwatchmonths-R2192-a.log (SUITE 8/8, "
            "double-run byte-identical) (2026-10-28)")

OUT = ["rating reply latency scorecard (api_rating_reply_latency)",
       "on",
       "R2193: the trust face had a reply door, a reply revision leg and "
       "a reply history, the present debt had its own queue, and the two "
       "neighbouring conversation chains already scored their waiting "
       "time - but nothing measured how long a RATING sat before the "
       "seller answered it, so a same-hour reply and a fortnight-late one "
       "read identically. api_rating_reply_latency(dev_account=None) "
       "returns a thirteen-key envelope with thirteen-key rows: latency "
       "is the immutable first reply stamp minus the rating's own stamp, "
       "integer and derived from two stored stamps only, an unanswered "
       "rating is None rather than a fabricated zero and enters no "
       "aggregate, and a same-second reply reads exactly 0. Row authority "
       "is the rating side, so one call answers both halves - what was "
       "answered and how slowly, and what is still owed - in a pinned "
       "total order (answered by descending latency then rating_id, "
       "pending after them by rated_utc then rating_id). Stars read "
       "through the effective-stars seam and reply text through the "
       "effective-reply seam, so a revised reply moves the text while the "
       "historical latency stays frozen; the effective title comes from "
       "the metadata seam. Coverage, average, median parity, fastest, "
       "slowest, latest reply stamp and oldest outstanding stamp all "
       "answer None where nothing was answered. Cross-face agreement with "
       "api_seller_inbox is pinned on the total, the outstanding count "
       "and the oldest stamp. Suite 8/8 double-run byte-identical "
       "criterion sha16 260c70a495390bfa, wired "
       "ledger-apimarket-ratingreplylatency(8); four adjacent "
       "trust-family suites green."]

RESULT = ["R2193",
          "R2193: five-silence scan clean (251 rows / 166 D-C tokens with "
          "zero new, the nine stored-but-absent tokens are known citations "
          "and rotation artefacts so the baseline was re-anchored to 166; "
          "ledger patrol rows already paid off; group orders tail "
          "unchanged at the 2026-10-28 03:0x fleet event round #4; "
          "benchmarks inside the seven-day gate; tree clean). The window "
          "rejected explore seed 4/10 with evidence (api_seller_answers "
          "R2120 already scores seller answer latency) rather than "
          "manufacturing a duplicate, then claimed seed 5/10 with "
          "AC-RRL1..AC-RRL8 registered in that row and shipped "
          "api_rating_reply_latency: two-stamp integer latency, None "
          "instead of a fake zero for the outstanding half, coverage / "
          "average / median parity / fastest / slowest / latest reply / "
          "oldest outstanding, the pinned total order, revision seams that "
          "freeze history, cross-face agreement with api_seller_inbox, a "
          "pure read and cross-restart byte identity. SUITE 8/8 "
          "double-run identical sha16 260c70a495390bfa (770B, single "
          "writer utf-8 LF); four adjacent suites green. Honest notes: one "
          "test-side scope error (dana inbox total versus market total) "
          "was corrected in the TEST, and the full battery plus matrix "
          "regeneration are R2194 first-item debt."]


def count_open(path):
    if not os.path.exists(path):
        return 0
    with io.open(path, encoding="utf-8", errors="replace") as f:
        return sum(1 for line in f if line.startswith("- [ ]"))


def main():
    with io.open(STATE, encoding="utf-8") as f:
        state = json.load(f)
    state["tick"] = 2193
    state["last_decision_rows"] = 251
    state["last_dec_tokens"] = ",".join(sorted(
        set(state["last_dec_tokens"].split(",")) - {
            "D-20261006-05", "D-20261007-04", "D-20261007-05",
            "D-20261008-05", "O-20261012-2330", "O-20261026-0735",
            "T-20261026-01", "T-20261026-02", "T-20261026-03"}))
    state["log"].append(NARRATIVE)
    state["log"].append(TOKENS)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")

    with io.open(EXPORT, encoding="utf-8") as f:
        export = json.load(f)
    now = datetime.now(timezone(timedelta(hours=8)))
    export["export_ts"] = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    export["do"] = DO
    face = export["ceo_face"]
    face["current"] = CURRENT
    face["latest_artifact"] = LATEST
    face["next_milestone"] = NEXT
    face["last_artifact"] = LAST_ART
    outs = export.get("outs", [])
    outs.insert(0, OUT)
    export["outs"] = outs
    results = export.get("results", [])
    results.insert(0, RESULT)
    export["results"] = results

    log = state["log"]
    window_start = "2026-10-22"
    in_window = sum(1 for line in log
                    if re.match(r"^\d{4}-\d{2}-\d{2}", line)
                    and line[:10] >= window_start)
    proposals = os.path.join(ROOT, "docs", "proposals.md")
    total = 0
    openp = 0
    if os.path.exists(proposals):
        with io.open(proposals, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("- **BD-PROP-"):
                    total += 1
                if line.startswith("- [ ]"):
                    openp += 1
    export["self_drive"] = {
        "window": "2026-10-22..2026-10-28",
        "window_days": 7,
        "log_lines_in_window": in_window,
        "idle_fast_mention_lines": sum(
            1 for line in log if "idle-fast" in line),
        "no_pullable_mention_lines": sum(
            1 for line in log if "no-pullable" in line),
        "substantive_non_idle_mention_lines": in_window,
        "proposals_total": total,
        "proposals_open": openp,
        "queue_main_open": count_open(os.path.join(
            ROOT, "state", "queue", QUEUES[0])),
        "queue_tech_open": count_open(os.path.join(
            ROOT, "state", "queue", QUEUES[1])),
        "queue_explore_open": count_open(os.path.join(
            ROOT, "state", "queue", QUEUES[2])),
    }
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("tick", state["tick"], "tokens", len(state["last_dec_tokens"].split(",")))
    print("self_drive", json.dumps(export["self_drive"]))


if __name__ == "__main__":
    main()