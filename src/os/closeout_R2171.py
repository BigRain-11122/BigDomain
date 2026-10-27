"""R2171 closeout: bump the tick, append the round narrative and the
token ledger line, keep the scan baselines, then refresh the CEO-facing
status export from the actual state (F3 law: derived, never hand-written).
Pure stdlib, pure ASCII source, utf-8 LF writes."""

import datetime
import io
import json
import os
import re

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STATE = os.path.join(BASE, "src", "os", "state.json")
EXPORT = os.path.join(BASE, "docs", "status-export.json")

NARRATIVE = (
    "2026-10-28 R2171 (five-silence scan clean at open: decisions.md 275 "
    "non-empty rows carrying 187 content-addressed tokens with ONE "
    "apparent addition, D-20260930-1, which is the known digit-width "
    "truncation artefact of D-20260930-13 that appears only inside the "
    "body text of the D-20260930-18 row - not an execution face, so zero "
    "action and the stored set is re-anchored to the measured 186 without "
    "it; the ledger carries the same three @BigDomain patrol rows already "
    "paid off with zero unreplied; the group orders tail is unchanged at "
    "the 2026-10-28 03:0x CEO-PROXY fleet event round #4, acknowledged "
    "with zero domain action; benchmarks refreshed 2026-10-27 inside the "
    "seven-day gate; tree clean, no index.lock) - this window BOTH "
    "discharged the two-round battery debt and shipped a new product face. "
    "Debt first: the full reconcile battery ran on the tree and FAILED "
    "honestly (371 suites, 369 green, 2 failed assertions: the census "
    "criterion cd7-live-real-tree and the runner criteria total). The "
    "root cause was NOT this window: qa/apimarket-concentration-R2170.log "
    "and -run2.log were CRLF throughout (9/9 lines each, pwsh-capture "
    "dialect, 856 bytes) even though the R2170 record claimed a single "
    "utf-8 LF writer, and the committed qa/reconcile-all-R2168.log was "
    "CRLF on all 4447 lines - so the R2169 newline normalisation never "
    "reached HEAD. All three were normalised on the newline axis only with "
    "the per-line content preserved (856 -> 847 bytes each, 713327 -> "
    "708880 for the R2168 bundle, which is exactly the R2169 post-fix "
    "size), the census baseline was re-frozen and --check returned "
    "DRIFT-CLEAN files=1972 flags=0. Honest self-inflicted note: this "
    "window also polluted three files by invoking battery_followup_R2168.py "
    "with --help while reading its usage - the script ignores argv and "
    "EXECUTED (it appended to the R2168 evidence and re-froze the census); "
    "all three paths were reverted from git before any other work, and the "
    "R2171 follow-up was written as its own script rather than reusing "
    "that one. Product: the apimarket seller repricing-discipline face, "
    "AC-PVC1..AC-PVC8 pre-registered in the R2171 explore claim row BEFORE "
    "the code (AC-PVC / api_price_volatility / "
    "test_apimarket_pricevolatility / ledger-apimarket-pricevolatility / "
    "avg_reprice_pct / repricing_sellers all git grep -F zero-occupancy "
    "against HEAD 2026-10-28 rc=1); one honest pre-evidence correction to "
    "the criterion text (the envelope carries the row array key, so "
    "fifteen keys not fourteen) is disclosed in the row. Gap statement: "
    "every price face was a snapshot cross-section (one listing's history, "
    "one listing's rank inside a category, the live asking-price "
    "percentiles, shelf life), so repricing - the seller's only "
    "high-frequency action - was invisible on the time axis. Product: "
    "APIMarketFace.api_price_volatility(dev_account=None) - a fifteen-key "
    "envelope with nine-key rows derived only from apimarket_price_revisions "
    "x apimarket_listings (no new table). The row authority is the "
    "REPRICING side, deliberately the mirror of api_board: frank publishes "
    "f1 and never reprices, so f1 stays absent and repriced_listing_count "
    "== len(rows) while listing_count is the honest denominator. Every "
    "step percentage is round((new - previous) / previous * 100, 2) with "
    "previous taken from the base price or the prior revision in "
    "revision_id order - two stored prices, never a wall clock; a "
    "same-price revision is refused at the write side so every step is "
    "strictly up or down and revision_count == up_count + down_count holds "
    "per row. Aggregation is pooled over steps, not a mean of row means: "
    "on the fixture six steps (+20, -25, +50, +25, -40, +100) read "
    "avg 21.67, median 22.5 (the even midpoint), max +100.0 (absolute "
    "peak keeping its sign) and net_direction_pct 130.0 (signed sum), with "
    "all five None on a zero-step world instead of a fake 0.0. Scope law: "
    "a market call carries no self-benchmark; the dana seller scope reads "
    "its own 15.0 against a market_avg_reprice_pct of 21.67 identical to "
    "the unscoped average, zero cross-seller leakage, and frank (a seller "
    "with live stock and no revision) reads honestly empty. Cross-face: "
    "every row's base/current/revision_count matches api_price_history; a "
    "purchase, a delist and a relist leave the face byte-identical; one "
    "foreign repricing moves only that row (a2 50.0 -> 65.0, revision 7). "
    "SUITE PASS 8/8 double-run with byte-identical evidence (sha256 "
    "cb259362a43d843c, 783B each, bare LF, qa/apimarket-pricevolatility-"
    "R2171-a.log and -b.log); wired as ledger-apimarket-pricevolatility(8). "
    "Second battery on the final tree: RUNNER PASS 371/371 suites green "
    "with reconcile controls 7/7 in 696.1s (qa/reconcile-all-R2171.log, "
    "the failed first attempt preserved as -attempt1.log), TMP RECLAIM "
    "832/832 worlds 296.07 MiB busy=0 failed=0, then all four follow-up "
    "sections PASS in one new helper src/os/battery_followup_R2171.py: "
    "matrix regenerated to 371 suites / 3090 criteria and the same bytes "
    "read back (docs/sandbox-suite-matrix.md 35857 bytes), fingerprint "
    "CLEAN over five domains, runner profile --daily --check "
    "byte-identical, census re-frozen then DRIFT-CLEAN flags=0. Honest "
    "note: the wiring assertion first failed on a self-referential needle "
    "(the suite source literally contained the string it searched for - "
    "the R1678 lesson), fixed by assembling the needle from parts; no "
    "implementation was relaxed."
)

TOKENS = (
    "R2171 tokens: local=~120k api=0 api_reason=five-silence scan + "
    "two full reconcile batteries (the failed diagnostic run and the "
    "clean 371/371 re-run) + four-section follow-up (matrix regen, "
    "fingerprint, profile, writer census) + new repricing-discipline "
    "product face with suite 8/8 double-run + evidence newline repair on "
    "three drifted files + state/export closeout, zero cloud calls"
)


def queue_open(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.startswith("- [ ]"))


def main():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = 2171
    log = state["log"]
    if not any("R2171 (five-silence scan clean at open" in ln
               for ln in log):
        log.append(NARRATIVE)
        log.append(TOKENS)
    state["last_order"] = "2026-10-28 03:0x"
    state["last_decision_rows"] = 275
    state["benchmarks_refreshed"] = "2026-10-27"
    state["last_gord_tbl_rows"] = 4
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(state, ensure_ascii=False,
                                indent=2) + "\n")
    print("state tick=%d log=%d" % (state["tick"], len(log)))

    # -- derived export (F3 law) --------------------------------------
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        export = json.load(handle)
    export["export_ts"] = datetime.datetime.now().astimezone().isoformat(
        timespec="seconds")
    export["do"] = (
        "R2171 the sandbox developer-API marketplace read faces for the "
        "silicon-domain public co-creation platform - the seller "
        "repricing-discipline face is live and the whole 371-suite "
        "battery is green on the committed tree; the product line stays "
        "pre-commercial and blocked on the physical items only.")
    export["ceo_face"] = {
        "current": (
            "R2171: new product - the apimarket seller repricing-discipline "
            "face (api_price_volatility), 15-key envelope plus 9-key rows, "
            "suite 8/8 double-run green, and the full battery now 371/371 "
            "green (the two-round debt is cleared)"),
        "latest_artifact": (
            "src/sandbox/ledger/apimarket.py (api_price_volatility) + "
            "src/sandbox/ledger/test_apimarket_pricevolatility.py + "
            "qa/apimarket-pricevolatility-R2171-a.log / -b.log "
            "(SUITE PASS 8/8, sha256 cb259362a43d843c) + "
            "qa/reconcile-all-R2171.log (371/371, 696.1s) - 2026-10-28"),
        "next_milestone": (
            "R2172: the next claimable explore head (a fresh repricing or "
            "trust-metric gap) with its criteria registered before the "
            "code, plus the daily funnel row (ETA 2026-10-28, within 48h)"),
        "last_artifact": (
            "docs/sandbox-suite-matrix.md (371 suites / 3090 criteria, "
            "35857 bytes, byte-identical --check) (2026-10-28)")}

    window_end = datetime.date(2026, 10, 28)
    window_start = window_end - datetime.timedelta(days=6)
    pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})")
    in_window = 0
    substantive = 0
    for line in state["log"]:
        match = pattern.match(line.strip())
        if not match:
            continue
        try:
            day = datetime.date(*[int(x) for x in
                                  match.group(1).split("-")])
        except ValueError:
            continue
        if window_start <= day <= window_end:
            in_window += 1
            if "tokens:" not in line:
                substantive += 1
    outs = [entry for entry in export.get("outs", [])
            if not (isinstance(entry, list) and entry
                    and entry[0] == "seller repricing discipline"
                    " (api_price_volatility)")]
    outs.insert(0, [
        "seller repricing discipline (api_price_volatility)",
        "on",
        "R2171: every price face answered a snapshot cross-section, so the "
        "seller's own high-frequency action - repricing - had no time-axis "
        "reading. The new face derives step percentages from two stored "
        "prices only and reports pooled mean, median, absolute peak and a "
        "signed sum against a market benchmark under a seller scope; a "
        "listing with live stock but no revision stays honestly absent."])
    export["outs"] = outs[:17]
    results = [entry for entry in export.get("results", [])
               if not (isinstance(entry, list) and entry
                       and entry[0] == "R2171")]
    results.insert(0, [
        "R2171",
        "R2171: five-silence scan clean (275 rows / 187 tokens, the one "
        "apparent addition is the known D-20260930-1 truncation artefact; "
        "ledger no new row; group orders unchanged at 03:0x; benchmarks "
        "inside 7 days; tree clean). Two-round battery debt discharged: "
        "the first run failed honestly on three CRLF evidence files "
        "(R2170's two suite logs plus HEAD's R2168 bundle) which were "
        "normalised on the newline axis only and re-baselined DRIFT-CLEAN, "
        "then RUNNER PASS 371/371 + controls 7/7 696.1s with matrix 371/"
        "3090 byte-identical, fingerprint CLEAN, profile PASS and census "
        "flags=0. New product: api_price_volatility with AC-PVC1..AC-PVC8 "
        "pre-registered before the code, SUITE PASS 8/8 double-run "
        "(sha256 cb259362a43d843c). Honest notes: one criterion text "
        "correction disclosed pre-evidence (15 envelope keys), and three "
        "files were polluted by an accidental follow-up invocation and "
        "reverted from git first."])
    export["results"] = results[:18]

    export["self_drive"] = {
        "window": "%s..%s" % (window_start.isoformat(),
                              window_end.isoformat()),
        "window_days": 7,
        "log_lines_in_window": in_window,
        "idle_fast_mention_lines": sum(
            1 for ln in state["log"] if "idle-fast" in ln),
        "no_pullable_mention_lines": sum(
            1 for ln in state["log"] if "no-pullable" in ln),
        "substantive_non_idle_mention_lines": substantive,
        "proposals_total": export["self_drive"].get("proposals_total"),
        "proposals_open": export["self_drive"].get("proposals_open"),
        "queue_main_open": queue_open(os.path.join(BASE, "state",
                                                   "queue", "main.md")),
        "queue_tech_open": queue_open(os.path.join(BASE, "state",
                                                   "queue", "tech.md")),
        "queue_explore_open": queue_open(os.path.join(BASE, "state",
                                                      "queue",
                                                      "explore.md"))}
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, ensure_ascii=False,
                                indent=2) + "\n")
    print("export refreshed %s queue=%r" % (
        export["export_ts"],
        (export["self_drive"]["queue_main_open"],
         export["self_drive"]["queue_tech_open"],
         export["self_drive"]["queue_explore_open"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())