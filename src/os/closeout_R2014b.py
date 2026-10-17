# closeout_R2014b.py - R2014 takeover closeout surgery: state.json,
# heartbeat, explore queue, status-export. Run AFTER
# src/os/takeover_verify_R2014.py prints BATTERY PASS. ASCII script per the
# encoding law; every CJK string is loaded from
# closeout_payload_R2014.json (data file). Byte-surgical on state.json
# (no full json.dumps rewrite, R1991 disease prevention); export flushed
# with the single-caliber self_drive recompute imported from
# check_export_consistency (zero caliber drift by construction).
import datetime
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
P_EV = os.path.join(ROOT, "qa", "takeover-verify-R2014.log")
P_PAYLOAD = os.path.join(HERE, "closeout_payload_R2014.json")
LIMIT = 78500


def die(msg):
    print("FATAL: %s" % msg, flush=True)
    sys.exit(1)


def rd(p):
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def wr(p, text):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def eol_of(text, probe=400):
    return "\r\n" if "\r\n" in text[:probe] else "\n"


# 0. payload + battery evidence gate
payload = json.loads(rd(P_PAYLOAD))
ev = rd(P_EV)
if "BATTERY PASS" not in ev:
    die("battery evidence missing BATTERY PASS - refuse closeout")
evl = ev.splitlines()


def ev_line(prefix):
    for ln in evl:
        if ln.startswith(prefix):
            return ln
    return ""


runner_line = ev_line("RUNNER rc=")
if "RUNNER PASS" not in runner_line:
    die("runner line not PASS: %r" % runner_line[:120])
suite_line = ev_line("SUITE replay")
if "anchor_match=True" not in suite_line:
    die("suite anchor not matched: %r" % suite_line[:120])
tail_ts = ""
for ln in evl:
    if ln.startswith("ORD_TAIL_TS="):
        tail_ts = ln.split("=", 1)[1].strip()
if not tail_ts:
    die("ORD_TAIL_TS missing in evidence")
venv_line = ev_line("PROBE amb-venv")
if "rc=0" in venv_line:
    probe_note = ("ambient temp writable for both interpreters at the "
                  "takeover probe - the crashed-round venv temp denial "
                  "did not reproduce (transient drift, healed)")
else:
    probe_note = ("still reproducing for the venv interpreter at the "
                  "takeover probe (system python ambient-writable; the "
                  "suite replay kept the crashed round's env and the "
                  "battery used outside-repo temp)")
ord_scan = ev_line("ORD_SCAN")
if "bigdomain_hits=0" not in ord_scan:
    die("unexpected BigDomain faces in group orders: %r" % ord_scan)

tokens_line = (payload["tokens_line"]
               .replace("<TAIL>", tail_ts)
               .replace("<PROBE_NOTE>", probe_note))

# 1. state.json byte surgery
raw = rd(P_STATE)
eol = eol_of(raw)
new_gord = int(payload["new_gord"])
repls = [
    ('"tick": 2013', '"tick": %d' % int(payload["new_tick"]), 1),
    ('"last_decision_rows": 349',
     '"last_decision_rows": %d' % int(payload["new_dec_rows"]), 1),
    ('"last_gord_tbl_rows": 455',
     '"last_gord_tbl_rows": %d' % new_gord, 1),
    ('"last_order": "2026-10-17 09:0x"',
     '"last_order": "2026-10-17 %s"' % tail_ts, 1),
]
for old, new, cnt in repls:
    got = raw.count(old)
    if got != cnt:
        die("state anchor %r count=%d expected %d" % (old[:44], got,
                                                       cnt))
    raw = raw.replace(old, new)

prefix = '"last_dec_tokens": "'
i0 = raw.find(prefix)
if i0 < 0:
    die("last_dec_tokens anchor missing")
v0 = i0 + len(prefix)
j0 = raw.find('"', v0)
if j0 < 0:
    die("last_dec_tokens value terminator missing")
cur = raw[v0:j0]
add = [t for t in payload["dec_tokens_add"].split(",")
       if t and t not in cur]
if add:
    raw = raw[:j0] + "".join("," + t for t in add) + raw[j0:]

close_anchor = eol + "  ]"
idx = raw.rfind(close_anchor)
if idx < 0:
    die("log close anchor missing")
newline_bytes = (len(("," + eol + " " * 16).encode("utf-8"))
                + len(json.dumps(tokens_line, ensure_ascii=False)
                      .encode("utf-8")))
gauge = len(raw.encode("utf-8")) + newline_bytes
if gauge > LIMIT:
    die("fold gate: post-append state %dB > %dB - run fold first"
        % (gauge, LIMIT))
raw = (raw[:idx] + "," + eol + " " * 16
       + json.dumps(tokens_line, ensure_ascii=False) + raw[idx:])
json.loads(raw)  # structural gate
wr(P_STATE, raw)
print("state.json: tick/dec/gord/order updated, tokens line appended, "
      "post size %dB (limit %d)" % (gauge, LIMIT), flush=True)

# 2. heartbeat row
hb = rd(P_HB)
hb_eol = eol_of(hb[-400:] if len(hb) > 400 else hb) if hb else "\n"
ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
row = ("%s +08:00 | BigDomain OSLoop alive | tick %d | %s "
       "[via BigDomain-OSLoop]"
       % (ts, int(payload["new_tick"]), payload["hb_summary"]))
if hb and not hb.endswith(hb_eol):
    hb += hb_eol
wr(P_HB, hb + row + hb_eol)
print("heartbeat: row appended (tick %d)" % int(payload["new_tick"]),
     flush=True)

# 3. explore queue: done-flip + successor reseed
ex = rd(P_EXPLORE)
ex_eol = eol_of(ex)
flip_old = payload["explore_flip_old"]
flip_new = payload["explore_flip_new"]
if ex.count(flip_old) != 1:
    die("explore flip anchor count=%d" % ex.count(flip_old))
ex = ex.replace(flip_old, flip_new)
end_anchor = payload["explore_end_anchor"]
if ex.count(end_anchor) != 1:
    die("explore end anchor count=%d" % ex.count(end_anchor))
ex = ex.replace(end_anchor, end_anchor + payload["explore_done_note"])
if not ex.endswith(ex_eol):
    ex += ex_eol
ex += payload["explore_seed_row"] + ex_eol
wr(P_EXPLORE, ex)
print("explore: claim done-flipped + successor seed reseeded",
     flush=True)

# 4. status-export flush (single-caliber recompute imported)
import check_export_consistency as cec  # noqa: E402

derived, state, pat_obj = None, None, None
derived, state, export, pat = cec.recompute()
ex_json = rd(P_EXPORT)
data = json.loads(ex_json)
data["export_ts"] = datetime.datetime.now().strftime(
    "%Y-%m-%dT%H:%M:%S+08:00")
data["ceo_face"]["current"] = payload["ceo_current"]
data["ceo_face"]["latest_artifact"] = payload["ceo_latest"]
data["ceo_face"]["next_milestone"] = payload["ceo_milestone"]
data["results"].insert(0, [payload["results_row_0"],
                           payload["results_row_1"]])
label = pat["tick_row_label"]
fixed = 0
for row in data["results"]:
    if isinstance(row, list) and len(row) == 2 and row[1] == label:
        row[0] = str(state["tick"])
        fixed += 1
if fixed != 1:
    die("tick row count=%d expected 1" % fixed)
sd = data.get("self_drive")
if not isinstance(sd, dict):
    die("self_drive missing")
for k, v in derived.items():
    sd[k] = v
out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
if "\r\n" in ex_json[:400]:
    out = out.replace("\n", "\r\n")
wr(P_EXPORT, out)
print("export: ceo_face + R2014 results row + tick row -> %s, "
      "self_drive recomputed=%r" % (data["export_ts"], derived),
      flush=True)

# 5. consistency gate (the checker is the law)
rep_lines, n_pass, n_fail = cec.check()
for ln in rep_lines[:50]:
    print("  GATE::%s" % ln[:130], flush=True)
if n_fail:
    die("export consistency gate FAIL=%d" % n_fail)
print("CLOSEOUT PASS (gate %d checks green)" % n_pass, flush=True)
