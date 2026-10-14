# -*- coding: utf-8 -*-
"""R1971 closeout: 17th-case orphan takeover closeout.
State.json byte surgery (tick 1971 + round/tokens log lines),
heartbeat row, export refresh (F3 derived). Verify: checker,
gauge, eol. One writer per file; CRLF preserved for state.json;
payload commit already landed (9300f294)."""
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
already = ("R1971" in sraw and "tokens: local=unmeasured api=0" in sraw
           and sraw.count("R1971") >= 2)
if not already:
    assert sraw.count('"tick": 1970,') == 1, "tick occurrence != 1"
    sraw = sraw.replace('"tick": 1970,', '"tick": 1971,')
round_line = (
    "2026-10-14 R1971 \u5d29\u8f6e\u5b64\u513f\u8f7d\u8377\u63a5\u7ba1"
    "\u6536\u53e3\u8f6e\uff08\u7b2c\u5341\u4e03\u6848\u00b7\u4e94\u9759"
    "\u626b\u63cf\u6811\u810f\u68c0\u51fa\u00b7R1924/R1969 \u63a5\u7ba1"
    "\u5148\u4f8b\u901a\u9053\uff09\uff1aR1970 cold_board \u4ea4\u4ed8"
    "\u8f7d\u8377\u5d29\u4e8e commit \u524d\uff0815 \u6587\u4ef6 "
    "staged\uff1acuration.py cold_board \u53cd\u6ee4\u8bfb\u9762+"
    "test_curation.py \u6269\u4e94\u4f8b+reconcile_all SUITES \u5224"
    "\u636e 19\u219224+runner-profile-baseline \u91cd\u951a 202 \u6761"
    "+qa \u8bc1\u636e\u53cc\u4ef6+state/export/heartbeat R1970 \u884c"
    "\u5168\u5957\u5728\u76d8\u2014\u2014\u5d29\u6e83\u70b9=closeout "
    "\u6bd5 commit \u524d\uff09\u2014\u2014\u63a5\u7ba1\u9a8c\u8bc1\u94fe"
    "\u4e09\u7eff\u4eb2\u8dd1\uff1a\u2460\u5957\u4ef6\u53cc\u8dd1 "
    "SUITE PASS 24/24 exit 0/0\uff08AC-CB1..CB5 \u5224\u636e\u9884\u6ce8"
    "\u518c\u5728\u5148\u00b7\u63a5\u7ba1\u8005\u72ec\u7acb\u590d\u8dd1"
    "\u975e\u4fe1 log\uff09\u2461\u5168\u91cf RUNNER \u7535\u6c60\u63a5"
    "\u7ba1\u8005\u4eb2\u8dd1=RUNNER PASS 202/202 suites green+"
    "reconcile controls 7/7 170.1s \u96f6\u56de\u5f52\u2462suite_"
    "matrix --check=PASS byte-identical 19441B/202 suites/1763 "
    "criteria\u2014\u2014payload \u539f\u6587 directed commit "
    "9300f294 \u6536\u53e3\uff1b\u63a5\u7ba1\u536b\u751f\uff1a\u63a5"
    "\u7ba1\u8005 --probe \u65d7\u6807\u8bef\u4ea7\u7269 stray \u6587"
    "\u4ef6 436KB \u5df2\u5220\uff08runner \u628a\u65d7\u6807\u53c2\u6570"
    "\u5f53\u65e5\u5fd7\u540d\u843d\u76d8\u00b7\u5751\u5f55\u5728\u6848"
    "\uff09+R1970 \u8bc1\u636e\u4ef6 mtime 21:24/21:27 \u4fdd\u5168"
    "\u672a\u88ab\u590d\u8dd1\u8986\u5199\uff1b\u4e94\u9759\u9762=DEC "
    "token-flat\uff08\u73b0\u503c 164\u00b7\u65b0 token 0\uff09/ORD "
    "\u5c3e 16:2x=\u57fa\u7ebf\u6301\u5e73\u00b7GORD tbl 403 vs 405="
    "known-shape \u8d1f\u6f02\uff08\u5c3e\u951a 16:2x \u96f6\u65b0\u4ee4"
    "\uff09/LEDGER \u65e0\u65b0 @BigDomain \u8f6c\u529e/BENCH "
    "2026-10-14 \u65b0\u9c9c\uff1bO-20261014-1855 \u591c\u4ee4\uff08"
    "\u5168\u9762\u5f00\u5de5\u00b7MV \u4f18\u5148\u7ea7\u6700\u9ad8"
    "\uff09=BigStream \u6267\u884c\u9762\u975e\u672c\u53f8\u5c04\u7a0b"
    "\u77e5\u6089\u4e0d\u52a8\u4f5c\uff1b\u96f7\u8fbe\u5019\u9009\u6e05"
    "\u5355 OH-20261014-cph4 21:41 \u7a97\u672a\u8fbe\uff08\u4ec5 "
    "OH-20261014-fluxverse 16:01 \u4ed6\u53f8\u4ef6\uff09=backlog "
    "\u884c 1 \u7eed\u5019\u96f6\u9020\u6d3b\uff1bscore 1\uff08\u63a5"
    "\u7ba1\u6536\u53e3\u00b7\u5d29\u8f6e\u8f7d\u8377 R1970 score 2 "
    "\u4ea7\u54c1\u4ea4\u4ed8\u7ecf\u63a5\u7ba1\u9a8c\u8bc1\u5f52\u53f2"
    "\u00b7\u7eaf\u8bb0\u8d26\u9762 0 \u5206\u672a\u8ba1\uff09")
tokens_line = (
    "2026-10-14 R1971 tokens: local=unmeasured api=0 "
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
    print("1. state.json: tick 1971 + 2 log lines (parse-gated)")
else:
    print("1. state.json: R1971 rows already appended (skip)")

# ---------- 2. heartbeat row ----------
hb_raw = io.open(P_HB, "r", encoding="utf-8", newline="").read()
hb_eol = "\r\n" if hb_raw.endswith("\r\n") else "\n"
if " | tick 1971 | " in hb_raw:
    print("2. heartbeat: R1971 row already present (skip)")
else:
    hb_row = (
        _dt.datetime.now().astimezone().isoformat(timespec="seconds")
        + " | BigDomain OSLoop alive | tick 1971 | R1971: 17th-case "
        "orphan takeover closeout - R1970 curation cold_board payload "
        "re-verified three-green (suite SUITE PASS 24/24 x2, RUNNER "
        "PASS 202/202 controls 7/7 170.1s own re-run, matrix --check "
        "byte-identical 202/1763/19441B) and committed 9300f294; "
        "stray taker-arg artifact removed; DEC/ORD flat, radar list "
        "21:41 window still pending [via BigDomain-OSLoop]")
    if not hb_raw.endswith(("\r\n", "\n")):
        hb_raw += hb_eol
    hb_raw += hb_row + hb_eol
    io.open(P_HB, "w", encoding="utf-8", newline="").write(hb_raw)
    print("2. heartbeat: R1971 row appended")

# ---------- 3. export refresh (F3 derived) ----------
sys.path.insert(0, HERE)
import check_export_consistency as cec  # noqa: E402
derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1971, "stale tick in export refresh"
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
results_row = (
    "R1971: 17th-case crashed-round orphan takeover closeout - "
    "R1970's curation cold_board payload (15 files staged, crashed "
    "pre-commit) re-verified three-green by the taker per R1924/"
    "R1969 precedent: suite double-run SUITE PASS 24/24 exit 0/0 "
    "(own re-run, not log-trusting), full RUNNER battery PASS "
    "202/202 suites green + reconcile controls 7/7 170.1s zero "
    "regression, suite_matrix --check byte-identical 19441B/202 "
    "suites/1763 criteria. Payload committed 9300f294 (R1970 "
    "score-2 product delivery restored into history). Taker "
    "hygiene: stray --probe log artifact (runner wrote the flag "
    "as a log name) removed; R1970 evidence files mtime-"
    "preserved. Five-silence: DEC token-flat, ORD tail 16:2x = "
    "baseline (GORD tbl 403 vs 405 known-shape negative drift, "
    "zero new orders), no new ledger transfers, radar candidate "
    "list OH-20261014-cph4 still pending at the 21:41 window "
    "(row 1 gated on external arrival, no fabrication).")
export_obj["results"] = [r for r in export_obj["results"]
                         if not (isinstance(r, list) and len(r) == 2
                                 and r[0] == "R1971")]
export_obj["results"].insert(0, ["R1971", results_row])
tick_label = pat["tick_row_label"]
tick_idx = [j for j, r in enumerate(export_obj["results"])
             if len(r) == 2 and r[1] == tick_label]
if tick_idx:
    export_obj["results"][tick_idx[0]][0] = "1971"
else:
    export_obj["results"].append(["1971", tick_label])
if len(export_obj["results"]) > 40:
    export_obj["results"] = export_obj["results"][:40]
export_obj["ceo_face"]["current"] = (
    "R1971: 17th-case orphan takeover closeout - the crashed "
    "R1970 cold_board payload was re-verified three-green by the "
    "taker (suite 24/24 double-run, RUNNER 202/202 controls 7/7 "
    "own re-run, matrix --check byte-identical 202/1763) and "
    "committed; zero regression, DEC/ORD flat, radar candidate "
    "list arrival-gated.")
export_obj["ceo_face"]["latest_artifact"] = (
    "commit 9300f294 - src/sandbox/ledger/curation.py cold_board "
    "read face + qa/curation-coldboard-R1970.log + qa/reconcile-"
    "all-R1970.log (2026-10-14)")
export_obj["ceo_face"]["next_milestone"] = (
    "P3 read-face family continues FIFO (cold_board cross-restart "
    "persistence window = reseeded head); radar candidate list "
    "OH-20261014-cph4 arrival gated (backlog row 1, no "
    "fabrication); within 48h.")
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
print("CLOSEOUT-OK R1971")
