# -*- coding: utf-8 -*-
"""R1956 closeout driver: tech.md dual-row edit (proposal persist
done + pay reconcile reseed) + state.json text surgery (tick 1956 +
round/tokens log lines per the R1953 closeout convention) +
heartbeat row + export refresh via check_export_consistency.
recompute. Fail-fast anchors; EOL preserved; CJK payload read from
closeout_payload_R1956.json (ASCII law)."""
import datetime as _dt
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
P_TECH = os.path.join(ROOT, "state", "queue", "tech.md")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_PAYLOAD = os.path.join(HERE, "closeout_payload_R1956.json")

with io.open(P_PAYLOAD, encoding="utf-8") as fh:
    payload = json.load(fh)

# -- tech.md: flip proposal row done + append done note + reseed ----
with io.open(P_TECH, encoding="utf-8", newline="") as fh:
    raw = fh.read()
eol = "\r\n" if "\r\n" in raw else "\n"

head = payload["row_head"]
lines = raw.split(eol)
hits = [i for i, ln in enumerate(lines)
        if ln.startswith(head)]
assert len(hits) == 1, "proposal persist row head not unique"
idx = hits[0]
assert lines[idx].startswith("- [ ] "), "row not open"
assert "AC-PLP1" in lines[idx] and "R1956" in lines[idx], \
    "claim block missing before done flip"
lines[idx] = ("- [x] " + lines[idx][len("- [ ] "):]
              + payload["done_note"])

assert not any(ln.startswith(payload["reseed_row"][:40])
               for ln in lines), "reseed row already present"
while lines and not lines[-1].strip():
    lines.pop()
lines.append(payload["reseed_row"])
lines.append("")
raw = eol.join(lines)
with io.open(P_TECH, "w", encoding="utf-8", newline="") as fh:
    fh.write(raw)
with io.open(P_TECH, encoding="utf-8", newline="") as fh:
    chk = fh.read()
chk_lines = chk.split(eol)
assert sum(1 for ln in chk_lines
           if ln.startswith("- [x] ledger proposal")) == 1
assert "**done 2026-10-14 R1956**" in chk
assert "pay reconcile" in chk
open_rows = sum(1 for ln in chk_lines if ln.startswith("- [ ]"))
assert open_rows == 10, "open rows drift: %d" % open_rows
print("tech.md: proposal done flip + pay reconcile reseed; "
      "open rows=%d" % open_rows)

# -- state.json: text surgery (tick + round/tokens lines) -------------
with io.open(P_STATE, encoding="utf-8", newline="") as fh:
    state = fh.read()
NL = "\r\n" if "\r\n" in state else "\n"
assert state.count('"tick": 1955,') == 1, "tick anchor not unique"
state = state.replace('"tick": 1955,', '"tick": 1956,', 1)
close_anchor = NL + "    ]"
cidx = state.rfind(close_anchor)
assert cidx > 0, "log close anchor not found"
prefix = state[:cidx]
assert prefix.rstrip().endswith('"'), "last log item not a string"
new_block = ("," + NL + '                "'
             + payload["round_line"] + '",' + NL
             + '                "'
             + payload["tokens_line"] + '"')
state = prefix + new_block + state[cidx:]
parsed = json.loads(state)
assert parsed["tick"] == 1956
assert parsed["log"][-2].startswith(
    "2026-10-14 R1956 ledger proposal")
assert parsed["log"][-1].startswith("2026-10-14 R1956 tokens:")
with io.open(P_STATE, "w", encoding="utf-8", newline="") as fh:
    fh.write(state)
print("state.json: tick 1956 + 2 log lines, %d bytes"
      % len(state.encode("utf-8")))

# -- heartbeat ---------------------------------------------------------
with io.open(P_HB, encoding="utf-8", newline="") as fh:
    hb = fh.read()
HNL = "\r\n" if "\r\n" in hb else "\n"
now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
hb_row = payload["hb_row"] % now
if not hb.endswith(HNL):
    hb += HNL
hb += hb_row + HNL
with io.open(P_HB, "w", encoding="utf-8", newline="") as fh:
    fh.write(hb)
print("heartbeat: tick 1956 row appended")

# -- export refresh ----------------------------------------------------
sys.path.insert(0, os.path.join(ROOT, "src", "os"))
import check_export_consistency as cec  # noqa: E402

derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1956, "stale tick: %s" % state_obj["tick"]
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
export_obj["ceo_face"]["current"] = (
    "R1956: ledger proposal cross-restart persist suite delivered "
    "(7/7; fold R514 honored at round start; RUNNER 194/194 "
    "criteria 1690->1697)")
export_obj["ceo_face"]["latest_artifact"] = (
    "qa/proposal-persist-R1956.log + src/sandbox/ledger/"
    "test_proposal_persist.py (2026-10-14)")
export_obj["ceo_face"]["next_milestone"] = (
    "next FIFO persist seat (ledger clawback persist suite) by "
    "2026-10-16")
results_row = (
    "R1956: ledger proposal cross-restart persist suite 7/7 "
    "(AC-PLP1..PLP7; two-piece restart, memorial certificates "
    "persist via collectibles public API, twelve restart-surviving "
    "gates same-code, crossing award + new registration "
    "post-restart continuation, frozen prefix rows, pre-award "
    "idempotence across restart, zero-token structure law, "
    "RUNNER 194/194 criteria 1690->1697); fold R514 executed at "
    "round start (state 81030B -> 73825B); tech consume 1 reseed "
    "1 (pay reconcile persist seeded; next FIFO head = ledger "
    "clawback persist)")
export_obj["results"].insert(0, ["R1956", results_row])
tick_label = pat["tick_row_label"]
tick_idx = [i for i, r in enumerate(export_obj["results"])
            if len(r) == 2 and r[1] == tick_label]
if tick_idx:
    export_obj["results"][tick_idx[0]][0] = "1956"
else:
    export_obj["results"].append(["1956", tick_label])
if len(export_obj["results"]) > 40:
    export_obj["results"] = export_obj["results"][:40]
if not any(len(r) == 2 and r[1] == tick_label
           for r in export_obj["results"]):
    for _i in range(len(export_obj["results"]) - 1, -1, -1):
        row = export_obj["results"][_i]
        if len(row) == 2 and row[1] != tick_label:
            export_obj["results"].pop(_i)
            break
    export_obj["results"].append(["1956", tick_label])
sd = dict(derived)
sd["method"] = ("machine-derived from state.json log per BD-PROP-001"
                " caliber (check_export_consistency.recompute)")
export_obj["self_drive"] = sd
out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
print("export refreshed: queues=%d/%d/%d tick=%d"
      % (derived["queue_main_open"], derived["queue_tech_open"],
         derived["queue_explore_open"], state_obj["tick"]))
