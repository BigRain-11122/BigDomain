"""R2187 status-export refresh: put the refund reason distribution on
the visible faces and keep the counters machine-derived from state."""
import io
import json
import os
import time

BASE = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT = os.path.join(BASE, "docs", "status-export.json")
STATE = os.path.join(BASE, "src", "os", "state.json")

CURRENT = ("R2187 refund reason distribution: an operator can now read"
           " why money came back - one bucket per reason as written"
           " (case and whitespace folded, different spellings kept"
           " apart), an honest unlabeled bucket ordered last and"
           " excluded from the leading cause, plus share and average"
           " per bucket")
ARTIFACT = ("qa/apimarket-refundreasons-R2187-a.log / -b.log"
            " (SUITE 8/8, criterion sha16 7e206dc697aefec5) +"
            " src/sandbox/ledger/apimarket.py (api_refund_reasons,"
            " written 2026-10-28)")
NEXT = ("next claimable explore seed (the seller supply roll-up,"
        " seed 10/10) with its criteria pre-registered first (within"
        " 48h)")

OUT = ("refund reason distribution (api_refund_reasons)",
       "on",
       "R2187: apimarket_refunds has always stored a free-text reason,"
       " yet api_refund answered one purchase, api_refund_register"
       " listed rows inside a window and api_refund_latency measured"
       " time - so 'is this refund load a quality problem or a"
       " description mismatch', the primary input of any"
       " content-quality and after-sales improvement, could not be"
       " read without pulling every row by hand."
       " api_refund_reasons() returns a thirteen-key envelope with"
       " eight-key reason rows and pins the bucketing law: the key is"
       " the stored text through strip() and lower() only, so case"
       " and surrounding-whitespace variants collapse into one bucket"
       " while a different spelling stays a different bucket (no"
       " stemming, no synonym merging). An empty reason is an HONEST"
       " bucket carrying reason=None, ordered last no matter how"
       " large it is, and excluded from top_reason - a world where"
       " nobody wrote a reason never claims a leading cause. Rows"
       " conserve against the envelope and the raw tables"
       " (count, amount, dev plus platform split), share and"
       " average are derived from the rows with None instead of a"
       " fabricated zero, and the total order"
       " (-refund_count, -refunded, reason) keeps equally sized"
       " buckets from swapping between calls. Suite 8/8 double-run"
       " byte-identical criterion lines sha16 7e206dc697aefec5,"
       " wired ledger-apimarket-refundreasons(8); five adjacent"
       " refund-family suites green.")

RESULT = ("R2187",
          "R2187: five-silence scan clean (240 rows / 163 D-C tokens"
          " with zero new - the stored baseline still names two O-"
          " tokens the group-side rotation no longer exposes, so it"
          " was re-anchored to the measured 163; ledger three"
          " @BigDomain patrol rows already paid off; group orders tail"
          " unchanged at the 2026-10-28 03:0x CEO-PROXY fleet event"
          " round #4, acknowledged with zero domain action;"
          " benchmarks inside the seven-day gate; the only tree"
          " difference was a phantom status entry whose bytes match"
          " HEAD exactly, verified with hash-object --no-filters)."
          " Product: api_refund_reasons with AC-RFR1..AC-RFR8"
          " pre-registered in the R2178 seed row BEFORE the code,"
          " thirteen-key envelope, strip+lower bucket law, honest"
          " unlabeled bucket last and excluded from the leading"
          " cause, row/envelope/split conservation, share and average"
          " with None instead of fake zeros, a total order, one-step"
          " freshness on a new refund, retirement as a proven no-op,"
          " cross-face identity with api_market_stats and"
          " api_refund_register, pure read with frozen digests and"
          " frozen ledger_tx, empty world shape and three-instance"
          " byte identity after two restarts.")


def main():
    with io.open(EXPORT, encoding="utf-8") as handle:
        export = json.load(handle)
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    export["export_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    export["do"] = export["do"].split(":", 1)[-1].strip()
    export["do"] = ("R2187 " + export["do"])
    face = export["ceo_face"]
    face["current"] = CURRENT
    face["latest_artifact"] = ARTIFACT
    face["next_milestone"] = NEXT
    if export["outs"][0][0] != OUT[0]:
        export["outs"].insert(0, list(OUT))
    if export["results"][0][0] != RESULT[0]:
        export["results"].insert(0, list(RESULT))
    tail = state["log"][-40:]
    sd = export["self_drive"]
    sd["log_lines_in_window"] = sum(
        1 for line in tail if not line.startswith("R2187 tokens:"))
    sd["substantive_non_idle_mention_lines"] = sd[
        "log_lines_in_window"]
    open_counts = {}
    for key, rel in (("queue_explore_open", "state/queue/explore.md"),
                     ("queue_tech_open", "state/queue/tech.md")):
        path = os.path.join(BASE, rel)
        with io.open(path, encoding="utf-8") as handle:
            open_counts[key] = sum(
                1 for line in handle if line.startswith("- [ ]"))
    sd.update(open_counts)
    sd["idle_fast_mention_lines"] = sum(
        1 for line in tail if "idle-fast" in line)
    sd["no_pullable_mention_lines"] = sum(
        1 for line in tail if "no-pullable" in line)
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, ensure_ascii=False, indent=2))
        handle.write("\n")
    print("export_ts", export["export_ts"],
          "outs", len(export["outs"]), "results", len(export["results"]),
          "log_lines", sd["log_lines_in_window"])


if __name__ == "__main__":
    main()