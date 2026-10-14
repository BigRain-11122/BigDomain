# -*- coding: utf-8 -*-
"""R1952 closeout: crashed-round orphan-payload takeover (festival
persist delivery). Steps: (1) takeover addendum appended to the
crashed round's evidence log (LF single-writer, crashed content
preserved as-is per evidence-integrity law), (2) tech.md festival
done-note flip + clawback persist reseed, (3) state.json tick
1952 + last_decision_rows 310 (line-count drift, token-flat) +
round/tokens log lines, (4) heartbeat row, (5) export refresh
(F3 derived via consistency tool). Anchor-exact fail-fast asserts;
EOL preserved per file. Round scoring: 2 (runnable artifact,
Executive Protocol v1.1). CJK strings live in
closeout_payload_R1952.json (encoding law)."""

import datetime as _dt
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))

with open(os.path.join(BASE, "closeout_payload_R1952.json"),
          encoding="utf-8") as fh:
    P = json.load(fh)


def read_txt(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        raw = fh.read()
    return raw.decode("utf-8")


def write_txt(rel, text):
    with open(os.path.join(ROOT, rel), "wb") as fh:
        fh.write(text.encode("utf-8"))


def eol_of(text):
    return "\r\n" if "\r\n" in text else "\n"


def must_count(text, needle, n, what):
    c = text.count(needle)
    assert c == n, "anchor %r count=%d expected=%d (%s)" % (
        needle, c, n, what)


# ------------------------------------------------- [1] festival log addendum
P_LOG = P["festival_log_rel"]
log = read_txt(P_LOG)
assert log.rstrip().endswith("VERDICT FAIL"), (
    "crashed log tail is not the FAIL verdict line")
assert "takeover addendum" not in log, "addendum already present"
if not log.endswith("\n"):
    log += "\n"
log += P["addendum_text"]
write_txt(P_LOG, log)
print("festival log: takeover addendum appended (LF single-writer)")

# ---------------------------------------------------------------- tech.md
P_TECH = "state/queue/tech.md"
tech = read_txt(P_TECH)
NL = eol_of(tech)
must_count(tech, P["tech_row_head_old"], 1, "festival open row head")
idx = tech.find(P["tech_row_head_old"])
end = tech.find(NL, idx)
assert end >= 0, "festival row has no line end"
tech = (tech[:idx] + P["tech_row_head_new"]
        + tech[idx + len(P["tech_row_head_old"]):end]
        + P["tech_done_note"] + tech[end:])
must_count(tech, P["tech_row_head_old"], 0, "no open head left")
must_count(tech, P["tech_row_head_new"], 1, "done head in place")
must_count(tech, P["reseed_anchor_head"], 1, "proposal open row head")
idx2 = tech.find(P["reseed_anchor_head"])
end2 = tech.find(NL, idx2)
tech = tech[:end2] + NL + P["tech_reseed_row"] + tech[end2:]
must_count(tech, P["tech_reseed_row"], 1, "reseed row in place")
write_txt(P_TECH, tech)
print("tech.md: festival done-note + clawback reseed ok")

# ------------------------------------------------------------- state.json
P_STATE = "src/os/state.json"
state = read_txt(P_STATE)
SNL = eol_of(state)
must_count(state, P["state_tick_old"], 1, "tick")
state = state.replace(P["state_tick_old"], P["state_tick_new"], 1)
must_count(state, P["state_decrows_old"], 1, "last_decision_rows")
state = state.replace(P["state_decrows_old"], P["state_decrows_new"], 1)
must_count(state, P["state_tail_anchor"], 1,
           "R1951 tokens tail line (pre-append tail anchor)")
close_anchor = SNL + "    ]"
assert state.rstrip().endswith("}"), "state tail not }"
cidx = state.rfind(close_anchor)
assert cidx > state.find(P["state_tail_anchor"]), (
    "log close before the R1951 tokens line")
prefix = state[:cidx]
assert prefix.endswith('"'), "last log item does not end with quote"
new_block = ("," + SNL + '                "'
             + P["state_round_line"] + '",' + SNL + '                "'
             + P["state_tokens_line"] + '"')
state = prefix + new_block + state[cidx:]
parsed = json.loads(state)
assert parsed["tick"] == 1952
assert parsed["last_decision_rows"] == 310
assert parsed["last_gord_tbl_rows"] == 376
assert parsed["log"][-2].startswith("2026-10-14 R1952 ledger festival")
assert parsed["log"][-1].startswith("2026-10-14 R1952 tokens:")
assert len(parsed["log"]) == 19  # 17 pre-append + 2 new rows
write_txt(P_STATE, state)
print("state.json: tick 1952, dec_rows 310, gord 376 held, +2 log lines,",
      len(state.encode("utf-8")), "bytes")

# ------------------------------------------------------------- heartbeat
P_HB = "heartbeat.txt"
hb = read_txt(P_HB)
HNL = eol_of(hb)
now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
hb_row = "%s | BigDomain OSLoop alive | tick %d | %s" % (
    now, P["hb_tick"], P["hb_row_suffix"])
if not hb.endswith(HNL):
    hb += HNL
hb += hb_row + HNL
write_txt(P_HB, hb)
print("heartbeat row appended")

# ---------------------------------------------------------------- export
sys.path.insert(0, BASE)
import check_export_consistency as cec  # noqa: E402

derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1952, "stale tick: %s" % state_obj["tick"]
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
export_obj["ceo_face"]["current"] = P["ceo_current"]
export_obj["ceo_face"]["latest_artifact"] = P["ceo_artifact"]
export_obj["ceo_face"]["next_milestone"] = P["ceo_milestone"]
export_obj["results"].insert(0, P["results_row"])
tick_label = pat["tick_row_label"]
tick_idx = [i for i, r in enumerate(export_obj["results"])
            if len(r) == 2 and r[1] == tick_label]
if tick_idx:
    export_obj["results"][tick_idx[0]][0] = "1952"
else:
    if len(export_obj["results"]) > 39:
        export_obj["results"] = export_obj["results"][:39]
    export_obj["results"].append(["1952", tick_label])
if len(export_obj["results"]) > 40:
    export_obj["results"] = export_obj["results"][:40]
# tick-row survival guard (R1946 truncation erratum family,
# patch_export_tick_R1946 law): if the cap dropped the tail tick
# row, restore it by dropping the oldest non-tick row instead.
if not any(len(r) == 2 and r[1] == tick_label
           for r in export_obj["results"]):
    for _i in range(len(export_obj["results"]) - 1, -1, -1):
        row = export_obj["results"][_i]
        if len(row) == 2 and row[1] != tick_label:
            export_obj["results"].pop(_i)
            break
    export_obj["results"].append(["1952", tick_label])
sd = dict(derived)
sd["method"] = ("machine-derived from state.json log per BD-PROP-001"
                " caliber (check_export_consistency.recompute)")
export_obj["self_drive"] = sd
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
print("export refreshed: queues=%d/%d/%d tick=%d evidence=%s"
      % (derived["queue_main_open"], derived["queue_tech_open"],
         derived["queue_explore_open"], state_obj["tick"],
         derived.get("evidence_file", "n/a")))
print("R1952 takeover closeout complete")
