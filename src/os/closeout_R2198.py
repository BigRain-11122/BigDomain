"""R2198 closeout: state tick and log, backlog rows, status export.

The repricing step-size band face shipped this window; every counter the
export carries is derived by check_export_consistency so no figure is
written dead.
"""
import io
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(BASE, "src", "os", "state.json")
EXPORT = os.path.join(BASE, "docs", "status-export.json")
BACKLOG = os.path.join(BASE, "src", "os", "backlog.md")

NARRATIVE = (
    "2026-10-28 R2198 (five-silence scan clean at open: decisions.md "
    "251 non-empty rows carrying 172 content-addressed D/C/O tokens, "
    "of which the two apparent additions O-20261012-2330 and "
    "O-20261026-0735 are the known O-family citations the group-side "
    "rotation restores inside other seats' rows - neither is a "
    "BigDomain execution face, so zero action and the stored baseline "
    "equals the measured set exactly; the group ledger carries the "
    "same three @BigDomain patrol rows already paid off with zero "
    "unreplied; the group orders tail advanced by one row, the "
    "2026-10-28 15:01 fleet auto-dispatch OB-20261028-150100-267 "
    "ordering bm-b/bm-c to full production, which is the fleet "
    "dispatcher execution face and not a domain face, so it is logged "
    "aware-no-action and the own-orders baseline advances to 15:01; "
    "benchmarks refreshed 2026-10-27 inside the seven-day gate; tree "
    "clean, no index.lock; both daily standing rows for 2026-10-28 "
    "were already on disk so neither was re-run) - the P1 canonical "
    "rows stay blocked-on-CEO and the weekly proposal duty is met by "
    "BD-PROP-005, all four tech heads stayed gated (docker host "
    "absent, logs toolkit standing maintenance, member refunded schema "
    "product-gated, the live-mtime row waiting on a real "
    "normalized-mtime event) and the explore head above the seeds is "
    "the merchant-gated benchmark row, so this window claimed the next "
    "real seed (R2189 8/10) and registered AC-PSD1..AC-PSD8 in that "
    "queue row BEFORE the code existed (AC-PSD and the face name each "
    "occupied one file - the seed row text itself - while "
    "test_apimarket_pricesteps, ledger-apimarket-pricesteps, "
    "step_band, band_share, most_common_band and _STEP_BANDS were all "
    "git grep -F zero-occupancy against HEAD 2026-10-28, rc=1). Gap "
    "statement: api_price_history lists one listing's revisions and "
    "api_price_volatility collapses every step into scalar aggregates, "
    "so a market built from timid micro-adjustments and one built from "
    "half-price cuts read identically and the shape of 'how big is a "
    "typical reprice' had no face. Product: APIMarketFace."
    "api_price_step_distribution(dev_account=None) - a thirteen-key "
    "envelope with ten-key band rows over five pinned bands (micro, "
    "small, medium, large, sweep). The five bands are ALWAYS present "
    "in fixed order even on an empty world, because a missing band and "
    "an empty band must never be confused; the intervals are half-open "
    "with the LOWER bound included, so a boundary value lands in the "
    "larger band (2.0 -> small, 10.0 -> medium, 25.0 -> large, 50.0 -> "
    "sweep) and a zero step is impossible because the write side "
    "already refuses E_AM_PRICE_UNCHANGED. Step arithmetic is the "
    "volatility law exactly (round((new - previous) / previous * 100, "
    "2) from two stored prices, no wall clock). The face pins count "
    "conservation per band and across faces (revision / up / down all "
    "equal api_price_volatility on the same scope), the share law "
    "(step_share sums to 1.0, up_share None on an empty band rather "
    "than a fabricated 0.0), within-band aggregates plus pooled "
    "absolute aggregates (avg 19.25 / median 7.5 / max 100.0 on the "
    "seeded eight-step world, all None on zero steps), and the "
    "modal-band law with the SMALLER-magnitude tie-break (micro, "
    "small and medium tie at two and micro wins). Scope law: a market "
    "call carries no self-benchmark, a seller call carries the "
    "market-wide pooled absolute mean (19.25, equal to the unscoped "
    "face), sellers never leak into each other and a never-repricing "
    "seller reads honestly empty. Suite "
    "src/sandbox/ledger/test_apimarket_pricesteps.py SUITE PASS 8/8 "
    "double-run rc=0/0 with byte-identical evidence (qa/"
    "apimarket-pricesteps-R2198-a.log and -b.log, 980 bytes each, "
    "sha256 51e45d79332416bd, criterion sha16 d7a3d48b0aabb5ad, "
    "single-writer utf-8 LF through src/os/evidence_writer.py), wired "
    "as ledger-apimarket-pricesteps(8); five adjacent price-family "
    "suites re-ran green (pricevolatility, pricepercentiles, pricerev, "
    "categorypricemonths, listingposition at 8/8 each). Honest notes: "
    "the registered AC-PSD2 first wrote the intervals as (0,2] while "
    "simultaneously demanding 'exactly 2.0 -> small', a self-"
    "contradiction; the notation was corrected in the same window to "
    "lower-inclusive/upper-open - the explicit boundary examples were "
    "kept, the criterion was NOT loosened - and two test-side "
    "expectation errors (the band law anchor list and the post-reprice "
    "step count, which is append-only so a second revision on a3 takes "
    "the world from 8 to 9 steps) were fixed with zero product change. "
    "The full reconcile battery and the suite-matrix regeneration were "
    "NOT run inside this window and are recorded as R2199 first-item "
    "debt.")

TOKENS = ("R2198 tokens: local=~75k api=0 api_reason=five-silence scan "
          "+ explore seed 8/10 claim with criteria pre-registered before "
          "code + repricing step-band product face + suite 8/8 "
          "double-run byte-identical + five adjacent price-family "
          "regressions + state/backlog/export closeout, zero cloud calls "
          "(full battery deferred to R2199 and recorded as debt)")

BACKLOG_ROW = (
    "- [x] P3 explore head claim (R2198, seed R2189 8/10, criteria "
    "AC-PSD1..AC-PSD8 registered in state/queue/explore.md BEFORE the "
    "code): apimarket repricing step-size band face "
    "api_price_step_distribution - five pinned bands with half-open "
    "intervals (lower bound included, boundary lands in the larger "
    "band), five bands always present with zero counts, per-band and "
    "cross-face count conservation against api_price_volatility, the "
    "share law with None instead of 0.0 on an empty band, within-band "
    "plus pooled absolute aggregates, the modal band with the "
    "smaller-magnitude tie-break, the market/seller scope law with the "
    "market pooled benchmark, the seven-form account gate before any "
    "read, a pure read with frozen digests and zero token movement, and "
    "two-restart byte identity. Evidence=qa/apimarket-pricesteps-R2198-a.log "
    "/ -b.log (SUITE PASS 8/8 double-run, 980 bytes each, sha256 "
    "51e45d79332416bd, criterion sha16 d7a3d48b0aabb5ad, single-writer "
    "utf-8 LF); wired ledger-apimarket-pricesteps(8); five adjacent "
    "price-family suites green.\n"
    "- [ ] P2 tech head (R2198 debt): the FULL reconcile battery plus "
    "the suite-matrix regeneration were NOT run inside the R2198 window "
    "(shipping apimarket.py while the battery walks the tree would have "
    "measured a mixed tree) - first item of the next round, on the "
    "committed tree, through src/os/battery_stream.py with the four "
    "follow-up sections (matrix regen/check, fingerprint --chain "
    "--check, runner profile --daily --check, writer census re-freeze "
    "then --check) appended to the same evidence file.\n")


def main():
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = 2198
    state["last_decision_rows"] = 251
    state["last_order"] = "2026-10-28 15:01"
    state["log"].append(NARRATIVE)
    state["log"].append(TOKENS)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(state, ensure_ascii=False, indent=2))
        handle.write("\n")

    with io.open(BACKLOG, "r", encoding="utf-8", newline="") as handle:
        existing = handle.read()
    if "R2198 debt" not in existing:
        with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(BACKLOG_ROW + existing)

    with io.open(EXPORT, encoding="utf-8") as handle:
        export = json.load(handle)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_export_consistency as C
    derived, _state, _export, pat = C.recompute()
    export["export_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    export["do"] = ("R2198 " + export["do"].split(":", 1)[-1].strip())
    face = export["ceo_face"]
    face["current"] = (
        "R2198 repricing step-size distribution: the market can now "
        "show how big a typical reprice is across five pinned bands, so "
        "a shelf of timid micro-adjustments and one cut in half are no "
        "longer indistinguishable")
    face["latest_artifact"] = (
        "qa/apimarket-pricesteps-R2198-a.log / -b.log (SUITE PASS 8/8 "
        "double-run, 980 bytes each, sha256 51e45d79332416bd) + "
        "src/sandbox/ledger/apimarket.py (api_price_step_distribution, "
        "written 2026-10-28)")
    face["next_milestone"] = (
        "R2199 runs the full reconcile battery plus suite-matrix "
        "regeneration carried from this window, then claims explore "
        "seed 9/10 (market-wide relist months) with its criteria "
        "pre-registered first; the P1 commercial rows and the "
        "merchant-number benchmark row stay blocked on CEO physical "
        "items (within 48h)")
    out = (
        "repricing step-size band distribution (api_price_step_distribution)",
        "on",
        "R2198: api_price_history lists one listing's revisions and "
        "api_price_volatility collapses every step into scalar "
        "aggregates, so a market of timid micro-adjustments and one of "
        "half-price cuts read identically and the shape of a typical "
        "reprice had no face. "
        "api_price_step_distribution(dev_account=None) returns a "
        "thirteen-key envelope with ten-key band rows over five pinned "
        "bands (micro, small, medium, large, sweep). The five bands are "
        "always present in fixed order even on an empty world, because "
        "a missing band and an empty band must not be confused; the "
        "intervals are half-open with the lower bound included so a "
        "boundary value lands in the larger band (2.0 small, 10.0 "
        "medium, 25.0 large, 50.0 sweep) and a zero step is impossible "
        "because the write side already refuses a same-price revision. "
        "Step arithmetic is the volatility law exactly, from two stored "
        "prices and never a wall clock. Count conservation holds per "
        "band and against api_price_volatility on the same scope; "
        "step_share sums to 1.0 and an empty band reports None instead "
        "of a fabricated 0.0; within-band and pooled absolute "
        "aggregates are pinned; the modal band breaks ties toward the "
        "smaller magnitude. A market call carries no self-benchmark "
        "while a seller call carries the market-wide pooled mean, with "
        "strict isolation and an honest empty read for a seller who "
        "never repriced. Suite 8/8 double-run byte-identical, sha256 "
        "51e45d79332416bd, wired ledger-apimarket-pricesteps(8); five "
        "adjacent price-family suites green.")
    result = (
        "R2198",
        "R2198: five-silence scan clean (251 rows / 172 content tokens "
        "equal to the stored baseline, the two O-family rotation "
        "citations acknowledged and zero BigDomain action; ledger three "
        "paid-off patrol rows; group orders tail advanced to the 15:01 "
        "fleet auto-dispatch row, aware-no-action; benchmarks inside the "
        "seven-day gate; tree clean, no index.lock). Product: "
        "api_price_step_distribution with AC-PSD1..AC-PSD8 "
        "pre-registered in the R2189 seed 8/10 row BEFORE the code - "
        "five always-present bands with lower-inclusive intervals and "
        "the boundary law, count conservation per band and across "
        "faces, the share law, within-band plus pooled absolute "
        "aggregates, the modal band with the smaller-magnitude "
        "tie-break, the market/seller scope law, the seven-form account "
        "gate before any read, a pure read with frozen digests and "
        "zero token movement, and two-restart byte identity. Evidence: "
        "SUITE PASS 8/8 double-run rc=0/0, 980 bytes each, sha256 "
        "51e45d79332416bd, criterion sha16 d7a3d48b0aabb5ad; five "
        "adjacent price-family suites green. Honest notes: the "
        "registered interval notation contradicted its own boundary "
        "examples and was corrected in the same window without "
        "loosening the criterion, two test-side expectation errors were "
        "fixed with zero product change, and the full battery plus "
        "matrix regeneration are R2199 first-item debt.")
    if export["outs"][0][0] != out[0]:
        export["outs"].insert(0, list(out))
    if export["results"][0][0] != result[0]:
        export["results"].insert(0, list(result))
    for row in export["results"]:
        if isinstance(row, list) and len(row) >= 2 and \
                row[1] == pat["tick_row_label"]:
            row[0] = str(state["tick"])
    export["self_drive"].update(derived)
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, ensure_ascii=False, indent=2))
        handle.write("\n")
    print("tick", state["tick"], "log_lines", len(state["log"]),
          "export_ts", export["export_ts"],
          "explore_open", export["self_drive"]["queue_explore_open"],
          "tech_open", export["self_drive"]["queue_tech_open"],
          "results", len(export["results"]))


if __name__ == "__main__":
    main()