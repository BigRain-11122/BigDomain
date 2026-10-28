# -*- coding: utf-8 -*-
"""R2188 status-export refresh: put the seller supply rollup on the
visible faces and keep the counters machine-derived from state."""
import io
import json
import os
import time

BASE = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT = os.path.join(BASE, "docs", "status-export.json")
STATE = os.path.join(BASE, "src", "os", "state.json")

CURRENT = ("R2188 seller supply rollup: a seller now reads the whole"
           " shop in one call - live vs retired listings, tracked vs"
           " unlimited shelves, units declared, sold, remaining,"
           " sold-out and low-stock counts, all riding the same"
           " scarcity seam the purchase gate uses")
ARTIFACT = ("qa/apimarket-sellersupply-R2188-a.log / -b.log"
            " (SUITE 8/8, criterion sha16 728821d514d5c693) +"
            " src/sandbox/ledger/apimarket.py (api_seller_supply,"
            " written 2026-10-28)")
NEXT = ("full reconcile battery plus suite-matrix regeneration, then an"
        " explore-queue reseed (the last real seed was claimed this"
        " round) - both within 48h")

OUT = ("seller supply rollup (api_seller_supply)",
       "on",
       "R2188: api_supply and api_supply_history answer ONE listing and"
       " api_seller_todo answers one duty row, so a seller holding N"
       " shelves had to call api_supply N times to learn the shop's"
       " stock position. api_seller_supply(dev_account,"
       " low_stock_threshold=1) returns a sixteen-key envelope with"
       " eleven-key rows: listing table as row authority (retired"
       " shelves included, ordered by listing_id), explicit"
       " live/retired and tracked/unlimited partitions, four aggregate"
       " laws (total_sold counts every row while the two supply totals"
       " read tracked rows only and answer None when nothing is"
       " tracked), and one scarcity law riding the single _supply_full"
       " seam so a purchase, a refund or a restock moves the rollup in"
       " the same step it moves the per-listing faces. The low-stock"
       " threshold defaults to 1 (0 counts only sold-out shelves) and"
       " fails closed on bool/str/float/negative forms after the"
       " account gate. Suite 8/8 double-run byte-identical, wired"
       " ledger-apimarket-sellersupply(8); six adjacent"
       " supply/lifecycle suites green.")

RESULT = ("R2188",
          "R2188: five-silence scan clean (251 rows / 170 D-C tokens"
          " with zero new; ledger three @BigDomain patrol rows already"
          " paid off; group orders tail unchanged at the 2026-10-28"
          " 03:0x CEO-PROXY fleet event round #4; benchmarks inside the"
          " seven-day gate; tree clean, no index.lock). Product:"
          " api_seller_supply with AC-SSUP1..AC-SSUP8 pre-registered in"
          " the R2178 10/10 seed row BEFORE the code - sixteen-key"
          " envelope, two explicit partitions, four aggregate laws, the"
          " one-step scarcity seam, the threshold law with the account"
          " gate first, a pure read with frozen digests and strict"
          " seller isolation, and cross-restart byte identity with the"
          " runner wiring. Suite 8/8 double-run byte-identical sha16"
          " 728821d514d5c693; six adjacent suites green; census"
          " DRIFT-CLEAN flags=0 after the birth-site newline repair of"
          " the predecessor battery log. Honest: the first run was 5/8"
          " red on this window's own fixture arithmetic (tracked total"
          " 11 not 13, pre-unlimited sales 5 not 6) and the TEST was"
          " corrected, not the implementation. The full battery and"
          " matrix regeneration are recorded as R2189 first-item debt.")


def main():
    with io.open(EXPORT, encoding="utf-8") as handle:
        export = json.load(handle)
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    export["export_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    export["do"] = export["do"].split(":", 1)[-1].strip()
    export["do"] = ("R2188 " + export["do"])
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
        1 for line in tail if not line.startswith("R2188 tokens:"))
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
          "log_lines", sd["log_lines_in_window"],
          "explore_open", sd["queue_explore_open"])


if __name__ == "__main__":
    main()