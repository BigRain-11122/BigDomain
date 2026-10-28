"""R2190 status-export refresh: put the seller-side refund reason
structure on the visible faces and keep the counters machine-derived
from state."""
import io
import json
import os
import sys
import time

BASE = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT = os.path.join(BASE, "docs", "status-export.json")
STATE = os.path.join(BASE, "src", "os", "state.json")

CURRENT = ("R2190 seller refund reasons: a seller now reads why their own"
           " money came back - one row per reason as written (case and"
           " whitespace folded, spellings kept apart), an honest"
           " unlabeled row pinned last and excluded from the leading"
           " cause, share/average per row, a concentration index, and"
           " the market refund rate plus this seller's share of the"
           " market refunded total as benchmarks")
ARTIFACT = ("qa/apimarket-sellerrefundreasons-R2190-a.log / -b.log"
            " (SUITE 8/8, criterion sha16 aea3ccbc7c14b8f2) +"
            " qa/regression-R2190.log + src/sandbox/ledger/apimarket.py"
            " (api_seller_refund_reasons, written 2026-10-28)")
NEXT = ("full reconcile battery and suite-matrix regeneration carried"
        " from this window, then explore seed 2/10 (buyer watchlist"
        " category mix) with its criteria pre-registered first (within"
        " 48h)")

OUT = ("seller refund reason structure (api_seller_refund_reasons)",
       "on",
       "R2190: api_refund_reasons aggregates the refund reason text"
       " market-wide and api_seller_quality carries only the seller's"
       " refund count and amount, so a seller could not read what their"
       " own refunds are caused by - a description mismatch and a"
       " service that keeps breaking were indistinguishable on their"
       " own ledger. api_seller_refund_reasons(dev_account=None)"
       " returns a seventeen-key envelope with eight-key reason rows and"
       " keeps the same narrow bucket law as the market face (strip()"
       " and lower() only; case and surrounding whitespace fold, a"
       " different spelling stays a different bucket, no stemming and no"
       " synonym merging). An empty reason is an HONEST bucket carrying"
       " reason=None, pinned LAST however large, excluded from"
       " top_reason and still counted as one bucket of the"
       " concentration measure. Refund rows are attributed by the stored"
       " dev_account so another seller's refunds never enter the"
       " envelope, and the seller purchase denominator comes from"
       " purchases joined to that seller's listings. Conservation holds"
       " against the scoped raw tables (count, amount, dev plus platform"
       " split, labeled plus unlabeled equals the refund count); share,"
       " average and top share are derived from the rows with None"
       " instead of a fabricated zero; reason_herfindahl is exact"
       " fractions (one bucket 10000.0, four buckets of 2/1/1/1 over"
       " five refunds 2800.0, the six-refund market 2777.78); and the"
       " total order (-refund_count, -refunded, reason ascending with"
       " the unlabeled bucket last) is stable between calls. The market"
       " scope never benchmarks itself (both benchmark keys None) while"
       " a seller scope carries the market refund rate and its own share"
       " of the market refunded total (0.878 for dana, 0.122 for frank)."
       " Suite 8/8 double-run byte-identical criterion lines sha16"
       " aea3ccbc7c14b8f2, wired"
       " ledger-apimarket-sellerrefundreasons(8); six adjacent refund"
       " and seller suites green.")

RESULT = ("R2190",
          "R2190: five-silence scan clean (251 rows / 170 D-C tokens"
          " with zero new against the stored baseline; ledger three"
          " @BigDomain patrol rows already paid off; group orders tail"
          " unchanged at the 2026-10-28 03:0x CEO-PROXY fleet event"
          " round #4, acknowledged with zero domain action; benchmarks"
          " inside the seven-day gate; tree clean, no index.lock)."
          " Product: api_seller_refund_reasons with AC-SRR1..AC-SRR8"
          " pre-registered in the R2189 seed row BEFORE the code -"
          " seventeen-key envelope, the shared narrow bucket law scoped"
          " by the stored dev_account, honest unlabeled bucket last and"
          " excluded from the leading cause, scoped conservation against"
          " the raw tables, share/average/top share with None instead of"
          " fake zeros, exact-fraction herfindahl, market benchmarks on a"
          " seller scope and None on the market scope, a pure read with"
          " frozen digests and frozen ledger_tx, three-instance byte"
          " identity after two restarts and five gate forms failing"
          " closed before any read. Honest notes: the first run read 6/8"
          " red on two of this window's own expectations (2800.0 not"
          " 3200.0; api_seller_quality carries no refund count, so"
          " api_refund_register is the cross-face witness) and one real"
          " test defect (double dumps on the retirement snapshot, plus a"
          " benchmark key that legitimately moves) - all three fixed in"
          " the TEST, no implementation loosened; the full battery and"
          " matrix regeneration are first-item debt for R2191.")


def main():
    with io.open(EXPORT, encoding="utf-8") as handle:
        export = json.load(handle)
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_export_consistency as C
    derived, _state, _export, pat = C.recompute()
    export["export_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    export["do"] = "R2190 " + export["do"].split(":", 1)[-1].strip()
    face = export["ceo_face"]
    face["current"] = CURRENT
    face["latest_artifact"] = ARTIFACT
    face["next_milestone"] = NEXT
    if export["outs"][0][0] != OUT[0]:
        export["outs"].insert(0, list(OUT))
    if export["results"][0][0] != RESULT[0]:
        export["results"].insert(0, list(RESULT))
    for row in export["results"]:
        if isinstance(row, list) and len(row) >= 2 and \
                row[1] == pat["tick_row_label"]:
            row[0] = str(state["tick"])
    sd = export["self_drive"]
    sd.update(derived)
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, ensure_ascii=False, indent=2))
        handle.write("\n")
    print("export_ts", export["export_ts"],
          "outs", len(export["outs"]), "results", len(export["results"]),
          "log_lines", sd["log_lines_in_window"],
          "sub", sd["substantive_non_idle_mention_lines"],
          "explore_open", sd["queue_explore_open"],
          "tech_open", sd["queue_tech_open"],
          "tick_row", str(state["tick"]))


if __name__ == "__main__":
    main()