"""R2090 closeout (state tick + log, explore queue row done, backlog
done line, status export refresh). Applied in-window; kept for the
record. Pure ASCII by the encoding law: the queue-row match uses the
ASCII prefix plus the round token instead of the Chinese row text."""

import io
import json

ROOT = "."

sp = ROOT + "/src/os/state.json"
st = json.load(io.open(sp, encoding="utf-8"))
st["tick"] = int(st["tick"]) + 1
new_tokens = ["D-20261024-13", "D-20261024-14", "D-20261024-15",
              "D-20261024-16", "D-20261024-17"]
base = [t.strip() for t in st["last_dec_tokens"].split(",") if t.strip()]
have = set(base)
for tok in new_tokens:
    if tok not in have:
        base.append(tok)
st["last_dec_tokens"] = ",".join(base)
st["last_decision_rows"] = 199

log = st["log"]
log.append(
    "2026-10-24 R2090 (five-silence scan: decisions.md carried five new "
    "content-addressed tokens D-20261024-13..17 against the stored "
    "baseline - D-13 cloud-off gate, D-14 ignitable breach wording, "
    "D-15 bm-b lane takeover, D-16 GPU arbitration and D-17 BigCompute "
    "model baseline are all other seats' execution faces (acknowledged, "
    "zero action, baseline advanced); ledger zero new @BigDomain rows; "
    "group orders baseline unchanged at 2026-10-24 12:1x; benchmarks "
    "refreshed 2026-10-24 inside 7 days; tree clean, no index.lock; both "
    "daily standing rows already stamped today so neither was re-run; "
    "the tech heads stayed gated - docker host absent, member refunded "
    "schema window product-gated, live-mtime row waiting on a real "
    "normalized-mtime event, profile window time-gated - and the single "
    "open explore row is gated on the merchant id) - so this window "
    "seeded and claimed a fresh P3 row in the SAME window with "
    "AC-AMMS1..AC-AMMS8 pre-registered BEFORE the code existed (AC-AMMS "
    "/ api_market_stats / test_apimarket_marketstats.py / "
    "ledger-apimarket-marketstats all git grep -F zero-occupancy "
    "anchored 2026-10-24, rc=1). Product: APIMarketFace."
    "api_market_stats - the market-wide overview the ten read faces "
    "never answered (each answers one listing, one seller, one buyer, "
    "the board, a search page, one history or one lifecycle; none "
    "answers 'how big is this market'). Fifteen-key envelope: listing / "
    "live / retired counts, dev_count, buyer_count, purchase / refund / "
    "net_purchase counts, gross / refunded / net gross tokens, net dev "
    "and platform revenue, avg_live_price, disclaimer. Laws pinned: "
    "partition conservation (listing_count == live + retired), trade "
    "conservation (gross == net + refunded, net == dev + platform "
    "exactly), retirement and re-listing only move the partition "
    "counters while every historical aggregate stays byte-frozen, a "
    "refund lowers net gross and both net pools by exactly the refunded "
    "amounts while purchase_count and buyer_count keep counting the "
    "trades that happened, cross-face agreement with dev_sales_board, "
    "cross-restart byte identity, and the pure-read law (zero row "
    "mutations, zero token movement, product files byte-identical). "
    "SUITE PASS 8/8 double-run identical sha16 18f3bfdd615d655b "
    "(qa/apimarket-marketstats-R2090.log + run2). Honest note: one "
    "in-window repair - the first cross-face assertion read the wrong "
    "board key (developers where dev_sales_board ships board/"
    "gross_revenue); corrected before any evidence was written.")
log.append(
    "R2090 tokens: local=~80k api=0 api_reason=five-silence scan + market "
    "overview product change + suite 8/8 double-run + battery 296/296 + "
    "matrix regen/check + evidence logs + state/export closeout, zero "
    "cloud calls")

with io.open(sp, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(st, fh, indent=2, ensure_ascii=False)
    fh.write("\n")

qp = ROOT + "/state/queue/explore.md"
qt = io.open(qp, encoding="utf-8").read()
lines = qt.split(chr(10))
hits = [i for i, ln in enumerate(lines)
        if ln.startswith("- [ ]") and "R2090" in ln]
assert len(hits) == 1
lines[hits[0]] = lines[hits[0]].replace("- [ ]", "- [x]", 1)
qt = chr(10).join(lines).rstrip(chr(10)) + (
    "[done 2026-10-24 R2090] suite 8/8 double-run sha16 "
    "18f3bfdd615d655b (qa/apimarket-marketstats-R2090.log + run2); "
    "wired ledger-apimarket-marketstats(8); battery RUNNER PASS 296/296 "
    "suites + controls 7/7 235.7s = qa/reconcile-all-R2090.log; "
    "matrix 296 suites / 2474 criteria --check byte-identical." + chr(10))
with io.open(qp, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(qt)

bp = ROOT + "/src/os/backlog.md"
bt = io.open(bp, encoding="utf-8").read()
row = (
    "- [x] P3 explore self-seeded and claimed in the same window (R2090): "
    "apimarket market-wide overview read face api_market_stats - ten read "
    "faces each answer one narrow question, none answered 'how big is "
    "this market'. [done 2026-10-24 R2090] suite 8/8 double-run sha16 "
    "18f3bfdd615d655b; wired ledger-apimarket-marketstats(8); battery "
    "RUNNER PASS 296/296 suites + controls 7/7 235.7s; matrix 296 "
    "suites / 2474 criteria byte-identical." + chr(10))
with io.open(bp, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(row + bt)

ep = ROOT + "/docs/status-export.json"
ex = json.load(io.open(ep, encoding="utf-8"))
ex["ceo_face"]["current"] = (
    "R2090: the developer API marketplace can now answer 'how big is this "
    "market' - one pure-read overview envelope with the live/retired "
    "split, participant counts, settled volume after refunds and the net "
    "developer/platform split, with every conservation law pinned.")
ex["ceo_face"]["latest_artifact"] = (
    "src/sandbox/ledger/apimarket.py (api_market_stats) + "
    "src/sandbox/ledger/test_apimarket_marketstats.py + "
    "qa/apimarket-marketstats-R2090.log (SUITE PASS 8/8 double-run "
    "identical sha16 18f3bfdd615d655b; RUNNER PASS 296/296 suites, 2474 "
    "criteria, controls 7/7, 235.7s = qa/reconcile-all-R2090.log; "
    "suite-matrix 296 suites / 2474 criteria byte-identical, 2026-10-24)")
ex["ceo_face"]["next_milestone"] = (
    "FUNNEL 72h self-continuity acceptance <=10-31; nine-company "
    "automation plan committee tri-report <=10-25; next window <=48h "
    "(by 2026-10-26)")
res = ex.setdefault("results", [])
res.append(["R2090",
            "R2090: apimarket market-wide overview read face "
            "(api_market_stats), AC-AMMS1..AC-AMMS8 pre-registered before "
            "the code existed; 8/8 double-run sha16 18f3bfdd615d655b; "
            "RUNNER 296/296 + controls 7/7 235.7s; matrix 296/2474 "
            "byte-identical. Score 2."])
with io.open(ep, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(ex, fh, indent=2, ensure_ascii=False)
    fh.write("\n")

print("closeout ok tick", st["tick"])