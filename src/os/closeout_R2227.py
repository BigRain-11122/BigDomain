"""R2227 closeout: bump the tick, append the round narrative, the token
ledger line and the self-heal line to src/os/state.json by text surgery
(layout preserved), stamp heartbeat.txt, refresh docs/status-export.json
(the Chinese payload lives in r2227_export_payload.json so this source
stays pure ASCII), prepend the discharged-debt row to src/os/backlog.md and
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
PAYLOAD = os.path.join(BASE, "r2227_export_payload.json")

if BASE not in sys.path:
    sys.path.insert(0, BASE)
import check_export_consistency as C  # noqa: E402

EXPORT_TS = "2026-10-29T04:29:00+08:00"

ROUND_LINE = (
    "2026-10-29 R2227 (five-silence scan clean at open: decisions.md carried 274 "
    "rows / 180 content-addressed D/C/O/T tokens with four apparent additions "
    "that are all the known group-side rotation artefacts (D-20261006-05, "
    "D-20261007-04, D-20261007-05, D-20261008-05), so zero genuinely new rows "
    "and zero domain action; the group ledger carries the same three @BigDomain "
    "patrol rows already paid off with zero unreplied; the group orders baseline "
    "is unchanged at the 2026-10-29 02:1x CEO-PROXY fleet event round R2.48 "
    "already consumed in R2226; benchmarks refreshed 2026-10-29 inside the "
    "seven-day gate; tree clean, no index.lock) - this window discharged the "
    "verification debt R2226 recorded as its own next first item, because R2226 "
    "shipped api_buyer_price_reaction and left the battery un-run, and a battery "
    "walking that tree is the only proof that the new suite is wired into the "
    "runner and that the adjacent faces still read green. No product code was "
    "touched (the R2168 mixed-tree rule). Battery on the committed tree 49a7637f: "
    "RUNNER PASS 413/413 suites green plus reconcile controls 7/7 in 996.5s "
    "(qa/reconcile-all-R2227.log, 752799 bytes, CRLF=0 lone CR=0, single-writer "
    "utf-8 LF through src/os/battery_stream.py, never a shell redirection), with "
    "the birth-site tmp sweep inside the same battery window reclaiming "
    "candidates=912 removed=912 busy=0 failed=0 reclaimed=320.71 MiB. Suites "
    "moved 412 -> 413 against R2225, which is exactly the R2226 suite joining "
    "the registry. The four post-battery sections then all passed in the new "
    "src/os/battery_followup_R2227.py and were appended to the same log: the "
    "suite matrix regenerated to 413 suites / 3427 criteria and read back "
    "(docs/sandbox-suite-matrix.md, 40254 bytes, evidence header reading 413/413 "
    "green, git diff +333/-332 for the one new suite row), the baseline "
    "fingerprint chain CLEAN over five domains, the runner profile --daily "
    "--check PASS, and the qa writer census re-frozen then DRIFT-CLEAN on both "
    "legs (files=2127 tee=1599 baselined=528 flags=0). Product score honestly "
    "zero - this window bought certainty, not features."
)

TOKEN_LINE = (
    "R2227 tokens: local=~22k api=0 api_reason=battery round on the committed "
    "tree - one full reconcile battery through battery_stream plus four "
    "follow-up sections in a new script, then the state/export/backlog "
    "closeout and the post-closeout gate re-runs; zero cloud calls and no "
    "product code changed (the R2168 mixed-tree rule)"
)

SELFHEAL_LINE = (
    "R2227 self-heal check: the BigDomain-OSLoop scheduled task exists and is "
    "Running, but its principal still reads LogonType=Interactive with "
    "RunLevel=Limited, which the 2026-09-29 machine law forbids for every lane "
    "task. src/os/register_loop_task.ps1 already passes an explicit S4U "
    "principal and needs an elevated shell to apply it; this session runs "
    "unelevated, so the task was left untouched rather than risk replacing the "
    "definition of the loop hosting this window. Open local-lane item for an "
    "elevated window."
)

BACKLOG_ROW = (
    "- [x] [done 2026-10-29 R2227] P2 verification head (R2226 debt, recorded "
    "there as its next first item): **full reconcile battery + suite-matrix "
    "regeneration** on the committed R2226 tree, so the newest face is proven "
    "wired and no adjacent face regressed. Executed on commit 49a7637f with "
    "zero product code changes (the R2168 mixed-tree rule): RUNNER PASS 413/413 "
    "suites plus reconcile controls 7/7 in 996.5s with TMP RECLAIM 912/912 "
    "worlds and 320.71 MiB (qa/reconcile-all-R2227.log, 752799B, single-writer "
    "utf-8 LF via battery_stream.py); four follow-up sections PASS in the new "
    "src/os/battery_followup_R2227.py - matrix 413 suites / 3427 criteria "
    "regenerated and read back, fingerprint CLEAN five domains, runner profile "
    "--daily --check PASS, writer census DRIFT-CLEAN files=2127 tee=1599 "
    "baselined=528 flags=0. Suites 412 -> 413 against R2225 = the R2226 suite "
    "joining the registry. Product score zero, honestly recorded.\n"
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
ex["do"] = payload["ceo"]["current"][:60].replace("\n", " ")
ex["do"] = "battery round R2227 (413/413 suites + controls 7/7)"
ex["ceo_face"] = {
    "current": payload["ceo"]["current"],
    "latest_artifact": payload["ceo"]["latest_artifact"],
    "next_milestone": payload["ceo"]["next_milestone"],
}
ex["outs"].insert(0, [payload["out_name"], "on", payload["out_text"]])
ex["results"].insert(0, ["R2227", payload["result_text"]])

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
needle = "- [x] [done 2026-10-29 R2226]"
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