# -*- coding: utf-8 -*-
"""R1972 closeout: 18th-case crashed-round orphan takeover closeout.
The crashed round authored the coldpersist payload (suite file, SUITES
row, matrix regen, qa evidence, explore claim); it crashed before any
state bookkeeping. The taker re-verified three-green (suite double-run,
full RUNNER battery own re-run, matrix --check) and now closes out:
state.json tick 1972 + round/tokens log lines, heartbeat row, export
refresh (F3 derived), checker/gauge/eol verify. One writer per file;
CRLF preserved for state.json."""
import datetime as _dt
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

# ---------- 1. state.json byte surgery: tick + 2 log lines ----------
sraw = io.open(P_STATE, "r", encoding="utf-8", newline="").read()
already = ("R1972 \u5d29\u8f6e\u5b64\u513f\u8f7d\u8377\u63a5\u7ba1"
           in sraw and sraw.count("R1972") >= 2)
if not already:
    assert sraw.count('"tick": 1971,') == 1, "tick occurrence != 1"
    sraw = sraw.replace('"tick": 1971,', '"tick": 1972,')
round_line = (
    "2026-10-14 R1972 \u5d29\u8f6e\u5b64\u513f\u8f7d\u8377\u63a5\u7ba1"
    "\u6536\u53e3\u4ea4\u4ed8\u8f6e\uff08\u7b2c\u5341\u516b\u6848\u00b7"
    "\u4e94\u9759\u626b\u63cf\u6811\u810f\u68c0\u51fa\u00b7R1924/R1969/"
    "R1971 \u63a5\u7ba1\u5148\u4f8b\u901a\u9053\uff09\uff1a\u5d29\u8f6e"
    "\u8f7d\u8377=curation cold_board \u8de8\u91cd\u542f\u6301\u4e45\u5316"
    "\u4f8b\u7a97\uff08explore \u961f\u5934\u00b7AC-CZP1..CZP6 \u5224\u636e"
    "\u9884\u6ce8\u518c\u5148\u4e8e\u4ee3\u7801\u5728 explore.md \u884c"
    "\u5185\u5df2\u843d\uff09=test_curation_coldpersist.py \u65b0\u5957"
    "\u4ef6\u4ef6+reconcile_all SUITES \u589e\u4e00\u884c ledger-curation-"
    "coldpersist \u5224\u636e 6+\u77e9\u9635\u518d\u751f 203/1769+qa "
    "\u53cc\u8bc1\u636e\u4ef6\u5728\u76d8\u2014\u2014\u5d29\u6e83\u70b9="
    "closeout \u524d\uff08state \u6b62\u4e8e R1971 \u96f6 R1972 \u884c"
    "\uff09\u2014\u2014\u63a5\u7ba1\u9a8c\u8bc1\u94fe\u4e09\u7eff\u4eb2"
    "\u8dd1\uff08\u63a5\u7ba1\u8005\u72ec\u7acb\u590d\u8dd1\u975e\u4fe1 "
    "log\uff09\uff1a\u2460\u5957\u4ef6\u53cc\u8dd1 SUITE PASS 6/6 exit "
    "0/0 \u89e3\u7801\u9010\u5b57\u8282\u540c\u4e00\uff08PS5.1 \u91cd"
    "\u5b9a\u5411 UTF-16 \u65b9\u8a00\u9677\u9631\u4eb2\u5389=\u6309 "
    "utf-16 \u6b63\u89e3\u590d\u9a8c\u00b7R1969 \u5224\u4f8b\u65cf\uff09"
    "\u2461\u5168\u91cf RUNNER \u7535\u6c60\u63a5\u7ba1\u8005\u4eb2\u8dd1"
    "=RUNNER PASS 203/203 suites green+reconcile controls 7/7 168.3s "
    "\u96f6\u56de\u5f52\uff08tee \u843d\u76d8\u4ed3\u5916\u4e34\u65f6"
    "\u4ef6=\u5d29\u6e83\u8f6e\u539f\u8bc1\u636e\u4ef6 mtime \u4fdd\u5168"
    "\u96f6\u8986\u5199\u00b7R1971 \u5148\u4f8b\uff09\u2462suite_matrix "
    "--check=PASS byte-identical 19535B/203 suites/1769 criteria\u2014"
    "\u2014explore \u884c done \u6ce8+\u8865\u79cd 1 \u884c\uff08\u51b7"
    "\u70ed\u53cc\u699c\u8054\u8bfb\u9762\u79cd\u5b50=queue_explore_open "
    "10 \u5b88\u6052\u00b7self-drive \u5e38\u5907\u7ebf\uff09\uff1b\u4e94"
    "\u9759\u9762=DEC 328 \u884c\u57fa\u7ebf\u6301\u5e73/ORD \u5c3e "
    "16:2x \u57fa\u7ebf\u6301\u5e73/LEDGER \u5c3e 4 \u884c\u5168\u503c"
    "\u5b88\u6c34\u4f4d\u62a5\u544a\u96f6\u65b0\u8f6c\u529e/BENCH "
    "2026-10-14 \u65b0\u9c9c/GORD 403 vs 405 known-shape \u8d1f\u6f02"
    "\u96f6\u65b0\u4ee4/BD-PROP \u63d0\u6848\u7a97\u989d BD-PROP-004 "
    "\u5728\u7a97\u4e0d\u6b20\u8d26\uff1bscore 2\uff08\u5d29\u8f6e\u4ea7"
    "\u54c1\u4ea4\u4ed8\u7ecf\u63a5\u7ba1\u9a8c\u8bc1\u5f52\u53f2\uff1a"
    "\u53ef\u8dd1\u5957\u4ef6\u5b9e\u7269 6 \u5224\u636e+RUNNER 203 "
    "\u5168\u7eff\u96f6\u56de\u5f52\u2014\u2014\u63a5\u7ba1\u6536\u53e3"
    "\u7c07\u8bb0\u8d26\u9762\u4e0d\u53e6\u8ba1\u5206\uff09")
tokens_line = (
    "2026-10-14 R1972 tokens: local=unmeasured api=0 "
    "api_reason=zero external cloud calls (takeover closeout: "
    "five-silence scan + suite double-run + full RUNNER battery "
    "re-run + matrix --check + state/export/heartbeat writes all "
    "local stdlib; no cloud APIs this round)")
for ln in (round_line, tokens_line):
    assert '"' not in ln, "no dquote in log lines"
    assert "\\" not in ln, "no backslash in log lines"
if not already:
    tail_idx = sraw.rfind("\r\n    ]")
    assert tail_idx > 0, "log close bracket not found"
    insertion = (",\r\n                " + json.dumps(round_line,
                 ensure_ascii=False) +
                 ",\r\n                " + json.dumps(tokens_line,
                 ensure_ascii=False))
    sraw = sraw[:tail_idx] + insertion + sraw[tail_idx:]
    json.loads(sraw)  # parse gate: malformed -> refuse write
    io.open(P_STATE, "w", encoding="utf-8", newline="").write(sraw)
    print("1. state.json: tick 1972 + 2 log lines (parse-gated)")
else:
    print("1. state.json: R1972 rows already appended (skip)")

# ---------- 2. heartbeat row ----------
hb_raw = io.open(P_HB, "r", encoding="utf-8", newline="").read()
hb_eol = "\r\n" if hb_raw.endswith("\r\n") else "\n"
if " | tick 1972 | " in hb_raw:
    print("2. heartbeat: R1972 row already present (skip)")
else:
    hb_row = (
        _dt.datetime.now().astimezone().isoformat(timespec="seconds")
        + " | BigDomain OSLoop alive | tick 1972 | R1972: 18th-case "
        "crashed-round orphan takeover closeout - curation cold_board "
        "cross-restart persistence suite (AC-CZP1..CZP6) re-verified "
        "three-green by the taker (SUITE PASS 6/6 x2 byte-identical, "
        "RUNNER PASS 203/203 controls 7/7 168.3s own re-run, matrix "
        "--check byte-identical 19535B/203/1769); evidence mtime-"
        "preserved, tee outside repo; explore done-flip + reseed "
        "(open=10); DEC/ORD flat [via BigDomain-OSLoop]")
    if not hb_raw.endswith(("\r\n", "\n")):
        hb_raw += hb_eol
    hb_raw += hb_row + hb_eol
    io.open(P_HB, "w", encoding="utf-8", newline="").write(hb_raw)
    print("2. heartbeat: R1972 row appended")

# ---------- 3. export refresh (F3 derived) ----------
sys.path.insert(0, HERE)
import check_export_consistency as cec  # noqa: E402
derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1972, "stale tick in export refresh"
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
results_row = (
    "R1972: 18th-case crashed-round orphan takeover closeout - the "
    "crashed round authored the curation cold_board cross-restart "
    "persistence suite (explore head, AC-CZP1..CZP6 pre-registered "
    "in the claim row before code) and crashed pre-bookkeeping; the "
    "taker re-verified three-green per R1924/R1969/R1971 precedent: "
    "suite double-run SUITE PASS 6/6 exit 0/0 decoded byte-identical "
    "(PS5.1 redirect UTF-16 dialect re-decoded per R1969 family), "
    "full RUNNER battery PASS 203/203 suites green + reconcile "
    "controls 7/7 168.3s zero regression (tee to a temp file outside "
    "the repo - crashed-round evidence mtime-preserved), suite_matrix "
    "--check byte-identical 19535B/203 suites/1769 criteria. Payload "
    "committed this round (suite file + SUITES row + matrix regen + "
    "done-flip + reseed, explore open=10). Five-silence: DEC 328 "
    "rows flat, ORD tail 16:2x flat, no new ledger transfers, BENCH "
    "fresh, GORD 403 vs 405 known-shape, BD-PROP-004 in-window (no "
    "proposal debt).")
export_obj["results"] = [r for r in export_obj["results"]
                         if not (isinstance(r, list) and len(r) == 2
                                 and r[0] == "R1972")]
export_obj["results"].insert(0, ["R1972", results_row])
tick_label = pat["tick_row_label"]
tick_idx = [j for j, r in enumerate(export_obj["results"])
             if len(r) == 2 and r[1] == tick_label]
if tick_idx:
    export_obj["results"][tick_idx[0]][0] = "1972"
else:
    export_obj["results"].append(["1972", tick_label])
# 40-cap trim with tick-row preservation (R1970-pattern bug hard-fix)
if len(export_obj["results"]) > 40:
    rows = export_obj["results"]
    tick_rows = [r for r in rows
                 if isinstance(r, list) and len(r) >= 2 and r[1] == tick_label]
    others = [r for r in rows
              if not (isinstance(r, list) and len(r) >= 2 and r[1] == tick_label)]
    export_obj["results"] = others[:40 - len(tick_rows)] + tick_rows
export_obj["ceo_face"]["current"] = (
    "R1972: 18th-case orphan takeover closeout - the crashed "
    "coldpersist suite payload was re-verified three-green by the "
    "taker (suite 6/6 double-run, RUNNER 203/203 controls 7/7 own "
    "re-run, matrix --check byte-identical 203/1769) and committed; "
    "zero regression, DEC/ORD flat, explore queue reseeded to 10.")
export_obj["ceo_face"]["latest_artifact"] = (
    "src/sandbox/ledger/test_curation_coldpersist.py + qa/curation-"
    "coldpersist-R1972.log + qa/reconcile-all-R1972.log (2026-10-14)")
export_obj["ceo_face"]["next_milestone"] = (
    "P3 read-face family continues FIFO (cold+hot combined board "
    "row = reseeded head); within 48h.")
sd = dict(derived)
sd["method"] = ("machine-derived from state.json log per "
                "BD-PROP-001 caliber "
                "(check_export_consistency.recompute)")
export_obj["self_drive"] = sd
out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
print("3. export refreshed:", json.dumps(sd, sort_keys=True))

# ---------- 4. verify: checker + gauge + eol ----------
for cmd in (
    [sys.executable, os.path.join(HERE, "check_export_consistency.py")],
    [sys.executable, os.path.join(HERE, "logs_toolkit.py"), "gauge"],
    [sys.executable, os.path.join(HERE, "logs_toolkit.py"), "eol"],
):
    p = subprocess.run(cmd, capture_output=True, cwd=ROOT)
    tail = [l for l in p.stdout.decode("utf-8", errors="replace")
            .splitlines() if l.strip()][-3:]
    print("4. verify rc=%d :: %s" % (p.returncode,
                                      " | ".join(tail)))
    if p.returncode != 0:
        print("VERIFY-FAIL", cmd[-1])
        sys.exit(2)
print("CLOSEOUT-OK R1972")
