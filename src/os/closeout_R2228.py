"""R2228 closeout: bump the tick, append the round narrative, the token
ledger line and the self-heal line to src/os/state.json by text surgery
(layout preserved), stamp heartbeat.txt, refresh docs/status-export.json
(the Chinese payload lives in r2228_export_payload.json so this source
stays pure ASCII), prepend the product row to src/os/backlog.md and
recompute the self_drive derived face with the checker caliber (F3).
Verify-then-write.
"""
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
HEART = os.path.join(ROOT, "heartbeat.txt")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
PAYLOAD = os.path.join(BASE, "r2228_export_payload.json")

if BASE not in sys.path:
    sys.path.insert(0, BASE)
import check_export_consistency as C  # noqa: E402

EXPORT_TS = "2026-10-29T04:21:00+08:00"

ROUND_LINE = (
    "2026-10-29 R2228 (five-silence scan clean at open: decisions.md token "
    "set carried 178 content-addressed D/C/O/T tokens with zero additions "
    "and zero removals against the baseline, so no new decision rows; the "
    "group ledger still carries the same three @BigDomain patrol rows with "
    "zero unreplied; the group orders newest stamp is unchanged at "
    "2026-10-29 00:52; benchmarks refreshed 2026-10-29 inside the seven-day "
    "gate; tree clean, no index.lock) - P1 board and the P2 tech head were "
    "all blocked or gated (bootstrap/launch wait on CEO physical items, the "
    "docker sandbox row waits on docker, the refunded-state and mtime rows "
    "stay gated), so this window claimed the P3 explore head and shipped a "
    "product increment: apimarket face api_seller_repeat_months(dev_account) "
    "- the seller-scoped monthly returning-buyer reading. Gap: "
    "api_repeat_purchase answers the lifetime question only and "
    "api_market_buyer_cohort reads new-versus-returning at MARKET scope over "
    "the active months only, so a single seller could not read whether a "
    "month was carried by regulars or by newcomers. Product: an eighteen-key "
    "envelope with eleven-key month rows; the net authority (a refunded "
    "purchase is not a purchase, a refund removes the buyer from that month, "
    "moves a seller-first month forward and erases a fully refunded buyer - "
    "the suite pins the APR row going to zero after the refund and the JUL "
    "row disappearing with gina); the returning law (strictly earlier "
    "seller-first month only, so ivan's two AUG purchases are new here while "
    "api_repeat_purchase still reads him as a repeat buyer - the disclosed "
    "asymmetry is asserted, lifetime buyer_count/purchase_count still agree "
    "exactly at 5 and 8); the contiguous grid across the year boundary "
    "(2025-11 to 2026-10, five honest zero rows); newcomer credits summing "
    "to the envelope buyer_count; the new/returning money split (60/20 of "
    "80); the earlier-month peak tie-break (2025-12); strict seller "
    "isolation partitioning the market's nine net purchases into 8 plus 1; "
    "the seven-form gate family failing closed before any read; frozen "
    "fifteen-table digests, a constant ledger_tx set and byte-identical "
    "three-instance repeats over two restarts. Evidence: SUITE PASS 8/8 "
    "double-run byte-identical (qa/apimarket-sellerrepeatmonths-R2228-a.log "
    "and -b.log, 1422 bytes each, CRLF=0, sha16 2f24ae212a38627e), wired as "
    "ledger-apimarket-sellerrepeatmonths(8), seven adjacent seller/cohort/"
    "repeat suites green (qa/regression-R2228.log). Honest notes: the AC-SRM "
    "prefix turned out to be occupied by api_seller_reply_months, so the "
    "window used the verified-free AC-SRB prefix and recorded that decision "
    "in the queue row; the first suite run read 4/8 and all four reds were "
    "this-window test expectations (gina's refund erases her JUL row exactly "
    "as AC-SRB2 demands), corrected without widening any implementation. "
    "Debt carried: the full reconcile battery plus the suite-matrix "
    "regeneration were NOT run in this 25-minute window (the R2168 "
    "mixed-tree rule) and are the next window's first item."
)

TOKEN_LINE = (
    "R2228 tokens: local=~30k api=0 api_reason=product round on one explore "
    "seed - an anchor occupancy check, one new seller-scoped monthly face in "
    "apimarket.py, an eight-criterion suite run twice to byte-identical "
    "evidence, seven adjacent regression suites, then the "
    "state/export/backlog closeout; zero cloud calls"
)

SELFHEAL_LINE = (
    "R2228 self-heal check: the BigDomain-OSLoop scheduled task exists and is "
    "Running, but its principal still reads LogonType=Interactive with "
    "RunLevel=Limited, which the 2026-09-29 machine law forbids for every lane "
    "task. src/os/register_loop_task.ps1 already passes an explicit S4U "
    "principal and needs an elevated shell to apply it; this session runs "
    "unelevated, so the task was left untouched rather than risk replacing the "
    "definition of the loop hosting this window. Open local-lane item for an "
    "elevated window."
)

BACKLOG_ROW = (
    "- [x] [done 2026-10-29 R2228] P3 explore head claim (R2228, seed R2213, "
    "criteria AC-SRB1..AC-SRB8 registered in the queue row BEFORE the code; "
    "the AC-SRM prefix proved occupied by api_seller_reply_months so the "
    "window used the verified-free AC-SRB prefix, and repeat_share / "
    "first_seller_month / returning_share / repeat_gross were git grep -F "
    "zero-occupancy at HEAD 2026-10-29 rc=1): apimarket **seller monthly "
    "returning-buyer face** (api_seller_repeat_months(dev_account)). Gap: "
    "api_repeat_purchase answers lifetime repeat only and "
    "api_market_buyer_cohort reads new-versus-returning at market scope over "
    "active months, so one seller's month-by-month regulars share had no "
    "face. Product: eighteen-key envelope, eleven-key month rows; the net "
    "authority (a refund removes the buyer from the month, moves a "
    "seller-first month forward, erases a fully refunded buyer - APR goes to "
    "zero and JUL disappears with gina); the returning law on the strictly "
    "earlier seller-first month (ivan's same-month double purchase is new "
    "here while api_repeat_purchase counts him as repeat - asserted "
    "asymmetry, lifetime buyer_count 5 and purchase_count 8 still agree "
    "exactly); the contiguous 2025-11..2026-10 grid with five honest zero "
    "rows; newcomer credits summing to buyer_count; the 60/20 new-versus-"
    "returning money split of 80; the earlier-month peak tie-break "
    "(2025-12); strict seller isolation (market net purchases 9 = 8 + 1); "
    "the seven-form gate family failing closed before any read; frozen "
    "fifteen-table digests, a constant ledger_tx set and byte-identical "
    "three-instance repeats over two restarts. Evidence: SUITE PASS 8/8 "
    "double-run byte-identical sha16 2f24ae212a38627e "
    "(qa/apimarket-sellerrepeatmonths-R2228-a.log and -b.log, 1422B each, "
    "CRLF=0), wired as ledger-apimarket-sellerrepeatmonths(8), seven "
    "adjacent suites green (qa/regression-R2228.log). Honest note: the first "
    "run read 4/8 and all four reds were this-window test expectations "
    "corrected to the measured truth without widening the implementation. "
    "Debt carried: full reconcile battery + suite-matrix regeneration are "
    "the next window's first item (the R2168 mixed-tree rule).\n"
)

with io.open(STATE, "rb") as handle:
    raw = handle.read()
text = raw.decode("utf-8")
assert "\r\n" in text
lines = text.split("\r\n")

tick_rows = [i for i, ln in enumerate(lines)
             if re.match(r'^\s*"tick"\s*:\s*\d+,\s*$', ln)]
assert len(tick_rows) == 1, tick_rows
old_tick = int(re.match(r'^\s*"tick"\s*:\s*(\d+),',
                        lines[tick_rows[0]]).group(1))
lines[tick_rows[0]] = re.sub(r'(\d+)', str(old_tick + 1),
                             lines[tick_rows[0]], count=1)

log_start = [i for i, ln in enumerate(lines)
             if ln.strip().startswith('"log"') and ln.strip().endswith("[")]
assert len(log_start) == 1
log_start = log_start[0]
items = []
close_idx = None
for j in range(log_start + 1, len(lines)):
    if lines[j].strip() == "]":
        close_idx = j
        break
    items.append(j)
assert close_idx is not None
indent = re.match(r'^( *)', lines[items[0]]).group(1)

before = json.loads(text)
assert len(before["log"]) == len(items)

lines[items[-1]] = lines[items[-1]] + ","
new_items = ['%s%s,' % (indent, json.dumps(ROUND_LINE, ensure_ascii=False)),
             '%s%s,' % (indent, json.dumps(TOKEN_LINE, ensure_ascii=False)),
             '%s%s' % (indent, json.dumps(SELFHEAL_LINE, ensure_ascii=False))]
lines[close_idx:close_idx] = new_items
out = "\r\n".join(lines)
after = json.loads(out)
assert after["tick"] == old_tick + 1
assert after["log"][:-3] == before["log"]
assert after["log"][-3] == ROUND_LINE
assert after["log"][-2] == TOKEN_LINE
assert after["log"][-1] == SELFHEAL_LINE
assert "\n" not in "".join(out.split("\r\n"))

with io.open(STATE, "wb") as handle:
    handle.write(out.encode("utf-8"))
with io.open(HEART, "w", encoding="ascii", newline="\n") as handle:
    handle.write("tick %d\n" % (old_tick + 1))

# ---- status export -------------------------------------------------------
with io.open(PAYLOAD, "rb") as handle:
    payload = json.loads(handle.read().decode("utf-8"))
with io.open(EXPORT, "r", encoding="utf-8") as handle:
    ex = json.load(handle)
ex["export_ts"] = EXPORT_TS
ex["do"] = "product round R2228 (seller monthly returning-buyer face)"
ex["ceo_face"] = {
    "current": payload["ceo"]["current"],
    "latest_artifact": payload["ceo"]["latest_artifact"],
    "next_milestone": payload["ceo"]["next_milestone"],
}
ex["outs"].insert(0, [payload["out_name"], "on", payload["out_text"]])
ex["results"].insert(0, ["R2228", payload["result_text"]])

label = C._load_patterns()["tick_row_label"]
hit = 0
for row in ex["results"]:
    if isinstance(row, list) and len(row) >= 2 and row[1] == label:
        row[0] = str(after["tick"])
        hit += 1
if hit != 1:
    raise SystemExit("tick row count %d" % hit)

with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(ex, handle, ensure_ascii=False, indent=2)
    handle.write("\n")

derived, _state, _export, _pat = C.recompute()
with io.open(EXPORT, "rb") as handle:
    fresh = json.loads(handle.read().decode("utf-8"))
fresh["self_drive"] = dict(derived)
with io.open(EXPORT, "wb") as handle:
    handle.write((json.dumps(fresh, ensure_ascii=False, indent=2)
                  + "\n").encode("utf-8"))

# ---- backlog -------------------------------------------------------------
with io.open(BACKLOG, "r", encoding="utf-8") as handle:
    body = handle.read()
needle = "- [x] [done 2026-10-29 R2227]"
idx = body.find(needle)
assert idx == 0, idx
body = BACKLOG_ROW + body
with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(body)

with io.open(STATE, "rb") as handle:
    back = json.loads(handle.read().decode("utf-8"))
print("tick %d -> %d, log %d -> %d, bytes %d -> %d"
      % (old_tick, back["tick"], len(before["log"]), len(back["log"]),
         len(raw), os.path.getsize(STATE)))
print("export outs=%d results=%d self_drive=%d"
      % (len(fresh["outs"]), len(fresh["results"]), len(fresh["self_drive"])))