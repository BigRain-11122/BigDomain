# export_refresh_R2024.py - CEO-face export refresh for the
# R2024 closeout (F3 law: every field derived from actual
# state; results row update; self_drive left to the machine
# caliber - checker re-verified after this write). Pure ASCII
# source; CJK lives only in the loaded/written data file.
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
P = os.path.join(ROOT, "docs", "status-export.json")

raw = io.open(P, "r", encoding="utf-8", newline="").read()
eol = "\r\n" if raw.count("\r\n") > raw.count("\n") - raw.count("\r\n") else "\n"
doc = json.loads(raw)

pat = json.loads(io.open(os.path.join(
    HERE, "export_consistency_patterns.json"),
    encoding="utf-8").read())
label = pat["tick_row_label"]

doc["export_ts"] = "2026-10-18T18:15:00+08:00"
doc["ceo_face"]["current"] = (
    "R2024: P3 explore queue FIFO head delivered: apimarket"
    " developer sales board zero-listing boundary world"
    " cross-restart persistence example window (the R2006"
    " reseed; criteria AC-AMZB1..AMZB7 pre-registered in the"
    " explore.md claim row before code; AC-AMZB prefix +"
    " suite name + registry label all git-grep zero-occupancy"
    " verified). Suite test_apimarket_devboardboundarypersist"
    ".py (suite-only round, five product sha256 pinned): the"
    " boundary isolates the listing axis only (ledger accounts"
    " + funding + an ada dev key stay populated while the"
    " apimarket three tables sit at zero rows), the pre-close"
    " default board pins the honest empty envelope {board: [],"
    " disclaimer} with double-call identity and a pure-read"
    " anchor; the write-side gate family fires before any read"
    " on the empty data face (off-register publish E_AM_NOT_DEV"
    " with the registry gate preceding the content gate, ada"
    " content-gate hit E_AM_CONTENT_REJECTED, zero price"
    " E_AM_BAD_PRICE, unknown-listing purchase"
    " E_AM_UNKNOWN_LISTING) with digests + ledger_tx constant"
    " over the probe batch; full-stack restart (am -> dk ->"
    " metered -> led close, same db_path same cfg bytes"
    " rebuild) replays the empty board byte-identically; the"
    " post-restart first listing joins the board as exactly"
    " one honest zero row (zero phantom, manual two-query"
    " cross equal); the first purchase recomputes zero-cache"
    " to (usr:ada, 1, 1, 10, 7, 3) with the 70/30 integer"
    " split, per-row conservation, and the spend_tx /"
    " dev_share_tx pair both present and distinct in the"
    " ledger_tx id set; third instance repeat-read purity."
    " One suite-side erratum healed in-round: the first run"
    " failed AC-AMZB5 on an unminted pool:share"
    " (E_NEGATIVE_BALANCE, single-pool omission of the R2006"
    " two-pool canon) - fixed same round, the product module"
    " itself passed on first proof. SUITE PASS 7/7 double-run"
    " LF-normalized byte-identical sha16 2980ce20fc93a049 ="
    " qa/apimarket-devboardboundary-R2024.log; reconcile_all"
    " wiring ledger-apimarket-devboardboundary (239->240"
    " suites, 2032->2039 criteria); RUNNER PASS 240/240 +"
    " reconcile controls 7/7 193.7s zero regression ="
    " qa/reconcile-all-R2024.log; matrix regen 240/2039"
    " green=240/240 --check byte-identical 23307B; census"
    " DRIFT-CLEAN files=1557 baselined=524; fingerprint CLEAN"
    " domains=5; profile --daily --check PASS. fold R554"
    " pre-closeout honored (gauge 77923B, tail-3 rolling"
    " line, 75 tokens embedded zero-loss, predicted =="
    " actual 77918B). Explore consume-1 reseed-1 (zero-listing"
    " gate-family cross-restart row). Score 2.")
doc["ceo_face"]["latest_artifact"] = (
    "src/sandbox/ledger/test_apimarket_devboardboundarypersist"
    ".py (zero-listing boundary persist suite, AC-AMZB1..AMZB7)"
    " + qa/apimarket-devboardboundary-R2024.log (SUITE 7/7"
    " double-run byte-identical sha16 2980ce20fc93a049) +"
    " qa/reconcile-all-R2024.log (RUNNER PASS 240/240) +"
    " docs/sandbox-suite-matrix.md regen (240 suites / 2039"
    " criteria, 2026-10-18)")
doc["ceo_face"]["next_milestone"] = (
    "P3 explore next open heads (dev_sales_board month-window"
    " zero-listing boundary persist [R2023 reseed], dev_sales"
    "_board zero-listing gate-family cross-restart [R2024"
    " reseed], yearbooks_combined multi-year persist,"
    " coverage dual-window month-roll, showcase stats"
    " gate-family cross-restart, proposal gate-family"
    " cross-restart, idem expiry-recharge billing, straddle"
    " netflow-exception) - one per round at the established"
    " cadence, next within 48h; P1/P2 lines stay gated on"
    " external arrivals (radar OH list, R777 review file,"
    " CEO physical items for bootstrap)")

row = doc["results"][-1]
if row[0] != "2023" or row[1] != label:
    raise SystemExit("FATAL: unexpected last results row " + str(row))
doc["results"][-1] = ["2024", label]

text = json.dumps(doc, ensure_ascii=False, indent=1)
if eol == "\r\n":
    text = text.replace("\n", "\r\n")
text += eol
io.open(P, "w", encoding="utf-8", newline="").write(text)
print("export refreshed: results rows=%d, ts=%s"
      % (len(doc["results"]), doc["export_ts"]))
