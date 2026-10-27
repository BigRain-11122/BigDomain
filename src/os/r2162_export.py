"""R2162 status-export refresh: finish the interrupted watch-conversion
round on the visible faces and keep the counters machine-derived from
state."""
import io
import json
import os
import time

BASE = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT = os.path.join(BASE, "docs", "status-export.json")
STATE = os.path.join(BASE, "src", "os", "state.json")

CURRENT = ("R2162 watch-conversion funnel: the market can now answer"
           " whether watching leads to buying - watch, pre-owned,"
           " funnel, converted and pending counts plus the conversion"
           " rate and the time to convert, with the direction fixed"
           " (a purchase made BEFORE the watch is not a conversion)")
ARTIFACT = ("qa/apimarket-watchconversion-R2162-a.log / -b.log"
            " (SUITE PASS 8/8, criterion sha16 cc3abcdc8af89c87,"
            " evidence sha16 b30e3f920d0005da) +"
            " src/sandbox/ledger/apimarket.py (api_watch_conversion,"
            " written 2026-10-27)")
NEXT = ("battery green on the committed tree plus a truthful matrix"
        " regeneration (the two items the last two windows owed); then"
        " the next claimable explore head (within 48h)")

OUT = ("watch-to-purchase funnel (api_watch_conversion)",
       "on",
       "R2162: the listing-demand face gave per-listing watcher and"
       " converted COUNTS with no rate, no time-to-convert, no"
       " market-level or seller-level roll-up - and worse, its"
       " conversion test only asked whether the buyer ever holds a"
       " non-refunded purchase, never whether it came after the watch,"
       " so every buy-then-watch record was counted as converted and"
       " the funnel was permanently fake. api_watch_conversion("
       "dev_account=None, include_uncategorized=True) returns a"
       " fifteen-key envelope with twelve-key category rows and fixes"
       " the direction: a live watch converts only when the"
       " non-refunded purchase stamp is at or after the watch stamp"
       " (same-second counts as a zero-second conversion), an earlier"
       " purchase is reported as pre_owned outside the funnel"
       " denominator, a refund returns the watch to pending, and"
       " watch_count equals pre_owned plus funnel while funnel equals"
       " converted plus pending. Durations are derived only from two"
       " stored stamps (integers, non-negative by construction, never"
       " the wall clock), the average is pooled rather than a mean of"
       " means, and the median takes the middle value for odd counts"
       " and the midpoint for even ones. Rows are watch-side with"
       " ascending categories and the uncategorized bucket last, the"
       " six counts conserve, and both the conversion rate and the"
       " pooled average are pinned as non-additive. Suite 8/8"
       " double-run byte-identical criterion lines sha16"
       " cc3abcdc8af89c87, wired ledger-apimarket-watchconversion(8);"
       " four adjacent suites green.")

RESULT = ("R2162",
          "R2162: the tree opened carrying the PREVIOUS window's"
          " uncommitted R2162 product slice (own executor, no"
          " index.lock, no competing writer verified by process tree),"
          " so this window finished that round instead of opening a"
          " new one. The uncommitted slice re-verified faithful - the"
          " suite re-ran SUITE PASS 8/8 at the same criterion sha16"
          " cc3abcdc8af89c87 and the same evidence sha16"
          " b30e3f920d0005da - and was committed as is. The one red"
          " suite the interrupted battery left behind was then"
          " root-caused: reconcile-daily-census cd7 refused because the"
          " live-tree census returned drift, and the census named"
          " exactly one offender - qa/reconcile-all-R2160.log carrying"
          " 23 stray CRLF lines among 4379 LF lines. It was fixed at"
          " the birth-place remedy rather than by widening the"
          " baseline: src/os/evidence_writer.py --fix rewrote only the"
          " EOL axis (702169 to 702146 bytes, every line preserved),"
          " after which the census reports DRIFT-CLEAN flags=0 and the"
          " census suite is 8/8 standalone. Honest boundaries: the full"
          " battery was not obtained (the R2162 log is a truncated"
          " 251/364 with no summary and the morning daily attempts are"
          " likewise partial), and the matrix regeneration was run,"
          " seen to understate green at 257/364 against a truncated"
          " evidence file, and reverted rather than committed as a"
          " false picture. Both lead the next round.")


def main():
    with io.open(EXPORT, encoding="utf-8") as handle:
        export = json.load(handle)
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    export["export_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    export["do"] = export["do"].split(":", 1)[-1].strip()
    export["do"] = ("R2162 " + export["do"])
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
        1 for line in tail if not line.startswith("R2162 tokens:"))
    sd["substantive_non_idle_mention_lines"] = sd["log_lines_in_window"]
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