"""R2223 closeout: bump the tick and append the round narrative plus the
token ledger line to src/os/state.json by text surgery on the existing item
block (no full re-serialization, so the committed layout is preserved), then
stamp heartbeat.txt. ASCII source, ASCII log text, verify-then-write.
"""
import io
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
HEART = os.path.join(ROOT, "heartbeat.txt")

ROUND_LINE = (
    "2026-10-29 R2223 (five-silence scan clean at open: decisions.md carries "
    "zero new content-addressed tokens against the stored baseline, ledger "
    "carries no new @BigDomain row, orders baseline unchanged, benchmarks "
    "fresh, tree clean, QA today green, export 0h; claim = the P2 tech head "
    "carried from R2222, the state.json waterline fold). The fold was "
    "executed and then REVERTED on evidence, which is this window finding: "
    "the fold itself ran clean (logs_toolkit.py eol --fix-indent --execute "
    "re-indented 228 log items with zero content change, then fold 590 moved "
    "log lines 1:222 = 386259 content bytes into "
    "logs/state-log-archive-2026-10.md and left one 4341B summary line naming "
    "all 455 window tokens, token_missing=[]; gauge went 402828B -> 16265B, "
    "fold_needed=False, census pass=True unknown mismatches 0). The battery "
    "then ran on that committed tree and turned RED: 409/411 suites green, "
    "expected criteria total=3411, with os-ledger-lines (AC-LGR8) and "
    "os-ledger-baseline (AC-LGB8) both failing because the live-gate law "
    "wants at least 30 ledger lines and 30 round lines in the LIVE state.json "
    "log while the fold had left 7. Measurement over the pre-fold log "
    "(logs/tmp-script/fold_tension_R2223.py on git 2795a60e): 228 lines carry "
    "100 ledger and 102 round lines, the smallest live window satisfying "
    "30/30 is 70-ish lines, but only 50 lines fit a 76500B log budget "
    "(mean line 1733.5B) - so the 78500B waterline gate and the live-gate "
    "30/30 law are mutually unsatisfiable at current line sizes, and no fold "
    "window can satisfy both. Reverted state.json to 2795a60e byte-exact, "
    "trimmed the duplicate archive section back to 4264954B, and re-ran both "
    "suites on the restored tree: os-ledger-lines 8/8 PASS, "
    "os-ledger-baseline 8/8 PASS, ledger_lines VERDICT CLEAN with the two "
    "historical gaps 2090/2095 still baselined. Battery evidence kept as the "
    "red-tree proof: qa/reconcile-all-R2223.log (748907B, single-writer utf-8 "
    "LF via battery_stream.py, TMP RECLAIM 910/910 worlds and 320.12 MiB). "
    "Product score honestly zero this window; the real deliverable is the "
    "measured conflict plus its fix design: make the ledger coverage law "
    "archive-aware (audit live log plus the folded archive sections instead "
    "of demanding 30 live lines). Registered as the R2224 head item together "
    "with the suite-matrix regeneration that the red battery never reached."
)

TOKEN_LINE = (
    "R2223 tokens: local=~85k api=0 api_reason=fold surgery plus layout "
    "normalisation, a full 1006s reconcile battery on the committed tree, the "
    "root-cause measurement of the live-gate versus waterline conflict, a "
    "byte-exact revert and the two live-gate suite re-runs - all local, zero "
    "cloud calls"
)

with io.open(STATE, "rb") as handle:
    raw = handle.read()
text = raw.decode("utf-8")
assert "\r\n" in text
lines = text.split("\r\n")

# tick bump
tick_idx = [i for i, ln in enumerate(lines)
            if re.match(r'^\s*"tick"\s*:\s*\d+,\s*$', ln)]
assert len(tick_idx) == 1, tick_idx
old_tick = int(re.match(r'^\s*"tick"\s*:\s*(\d+),', lines[tick_idx[0]]).group(1))
lines[tick_idx[0]] = re.sub(r'(\d+)', str(old_tick + 1),
                            lines[tick_idx[0]], count=1)

# log item block
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
             '%s%s' % (indent, json.dumps(TOKEN_LINE, ensure_ascii=False))]
lines[close_idx:close_idx] = new_items
out = "\r\n".join(lines)
after = json.loads(out)
assert after["tick"] == old_tick + 1
assert after["log"][:-2] == before["log"]
assert after["log"][-2] == ROUND_LINE and after["log"][-1] == TOKEN_LINE

with io.open(STATE, "wb") as handle:
    handle.write(out.encode("utf-8"))
with io.open(HEART, "w", encoding="ascii", newline="\n") as handle:
    handle.write("tick %d\n" % (old_tick + 1))

with io.open(STATE, "rb") as handle:
    back = json.loads(handle.read().decode("utf-8"))
print("tick %d -> %d, log %d -> %d, bytes %d -> %d"
      % (old_tick, back["tick"], len(before["log"]), len(back["log"]),
         len(raw), os.path.getsize(STATE)))