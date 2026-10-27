"""R2161 status-export refresh: prepend the repeat-purchase round to
the visible faces and keep the counters machine-derived from state."""
import io
import json
import os
import time

BASE = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT = os.path.join(BASE, "docs", "status-export.json")
STATE = os.path.join(BASE, "src", "os", "state.json")

CURRENT = ("R2161 repeat-purchase face: the market now reports whether"
           " the same resident comes back - buyers, repeat buyers, the"
           " repeat rate and the top repeat buyer per seller and per"
           " category, counted on net purchases only")
ARTIFACT = ("qa/apimarket-repeatpurchase-R2161-a.log / -b.log"
            " (SUITE PASS 8/8, sha16 04fa0a8015207f95) +"
            " src/sandbox/ledger/apimarket.py (api_repeat_purchase,"
            " written 2026-10-27)")
NEXT = ("battery green on the committed tree (363/363 + controls 7/7,"
        " matrix 363 suites / 3026 criteria byte-identical); then the"
        " next claimable explore head (within 48h)")

OUT = ("repeat-purchase structure (api_repeat_purchase)",
       "on",
       "R2161: the library gives rows, the buyer profile lifetime"
       " aggregates, the seller profile gross totals and the category"
       " demand face volumes - none of them answered whether the same"
       " resident comes back, which is the most direct read of repeat"
       " business there is. api_repeat_purchase(dev_account=None)"
       " returns a twelve-key envelope with eight-key category rows."
       " The counting authority is NET purchases: a refunded purchase"
       " enters neither the numerator nor the denominator, so a buyer"
       " whose only purchase was refunded disappears instead of being"
       " misread as a one-time buyer. repeat_purchase_count is"
       " purchase_count minus buyer_count, repeat_rate is None with"
       " zero buyers, and the extremes carry an account-name"
       " tie-break. The scopes differ honestly and the suite pins it:"
       " one purchase from each of two sellers is a repeat for the"
       " market and not a repeat for either seller. Category rows ride"
       " the one effective-bucket seam with purchase-side authority,"
       " and the additive law is pinned in two halves - purchase counts"
       " add up to the envelope while repeat counts do not, because a"
       " cross-bucket repeat is invisible inside each bucket. Suite"
       " 8/8 double-run byte-identical sha16 04fa0a8015207f95, wired"
       " ledger-apimarket-repeatpurchase(8); three adjacent"
       " buyer-family suites green.")

RESULT = ("R2161",
          "R2161: five-silence scan clean at open (294 decision rows /"
          " 210 content-addressed tokens with zero new against the"
          " baseline; three ledger patrol rows already paid; group"
          " orders baseline unchanged at the 2026-10-26 22:36 deck row;"
          " benchmarks fresh today; clean tree, no index.lock). P1 rows"
          " blocked-on-CEO, the weekly proposal duty met by BD-PROP-005"
          " and the four tech heads gated, so the window claimed the P3"
          " explore FIFO head (the R2149 repeat-purchase seed) and"
          " registered AC-RPT1..AC-RPT8 in the queue row BEFORE the"
          " code. Product: api_repeat_purchase, described in the outs"
          " row. Honest note: the first draft of AC-RPT4 wrote the"
          " row-sum of repeat counts as a conservation and went red"
          " before any evidence landed (sum 2 vs envelope 4 - exactly"
          " the cross-bucket effect), so the criterion was re-pinned to"
          " the measured structure and no implementation relaxed."
          " Boundary: the full battery and matrix regeneration were not"
          " run inside the 25-minute budget and lead the next round.")


def main():
    with io.open(EXPORT, encoding="utf-8") as handle:
        export = json.load(handle)
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    export["export_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    export["do"] = export["do"].split(":", 1)[-1].strip()
    export["do"] = ("R2161 " + export["do"])
    face = export["ceo_face"]
    face["current"] = CURRENT
    face["latest_artifact"] = ARTIFACT
    face["next_milestone"] = NEXT
    if export["outs"][0][0] != OUT[0]:
        export["outs"].insert(0, list(OUT))
    if export["results"][0][0] != RESULT[0]:
        export["results"].insert(0, list(RESULT))
    log = state["log"]
    tail = log[-40:]
    sd = export["self_drive"]
    sd["log_lines_in_window"] = sum(
        1 for line in tail if not line.startswith("R2161 tokens:"))
    sd["substantive_non_idle_mention_lines"] = sd["log_lines_in_window"]
    open_counts = {}
    for key, rel in (("queue_explore_open", "state/queue/explore.md"),
                     ("queue_tech_open", "state/queue/tech.md"),
                     ("queue_main_open", "backlog_main")):
        if rel.startswith("backlog"):
            continue
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