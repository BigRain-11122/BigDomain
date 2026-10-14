# -*- coding: utf-8 -*-
"""R1970 closeout: board flip + reseed, state.json byte surgery,
export refresh (F3 derived), heartbeat row. Verify: checker,
gauge, eol. One writer per file; CRLF preserved for state.json
(byte surgery, zero json.dump full rewrite); LF preserved for
explore.md (its native convention)."""
import datetime as _dt
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
P_EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

# ---------- 1. explore.md: flip line 45 done + reseed ----------
raw = io.open(P_EXPLORE, "r", encoding="utf-8", newline="").read()
raw = raw.replace("hot_board\\(\\)", "hot_board()")
lines = raw.split("\n")
i = 45
if lines[i].startswith("- [x]") and "R1970" in lines[i]:
    print("1. explore.md: already done-flipped (idempotent skip)")
else:
    assert lines[i].startswith("- [ ]"), "line 45 open-item expected"
    assert "R1970" in lines[i], "claim annotation expected"
    done_note = ("\u2014\u2014\u3014done 2026-10-14 R1970\u3015\uff08"
                 "\u6267\u884c\u6ce8\u8bb0\uff1aAC-CB1..CB5 \u5168\u8fc7"
                 "\u2014\u2014cold_board \u4e09\u4ef6\u843d\u5730="
                 "curation.py \u589e cold_board\uff3bheat==0 \u9006"
                 "\u6ee4\u00b7\u5355 hot_board() \u6d3e\u751f\u6e90"
                 "\u96f6\u7b2c\u4e8c\u805a\u5408\u00b7curation_id ASC"
                 " rank 1..N\uff3d+test_curation.py \u6269\u4e94\u4f8b"
                 " SUITE PASS 24/24 \u53cc\u8dd1 exit 0/0\uff3bqa/"
                 "curation-coldboard-R1970.log\uff3d+reconcile_all "
                 "SUITES ledger-curation \u5224\u636e 19\u219224\uff3b"
                 "RUNNER PASS 202/202 \u5224\u636e 1758\u21921763 "
                 "controls 7/7 175.1s=qa/reconcile-all-R1970.log"
                 "\uff3d+\u77e9\u9635\u518d\u751f --check "
                 "byte-identical 202/1763/19441B\uff1bdrift \u9762 "
                 "ugc +2.2s FLAG \u9694\u79bb\u5f52\u56e0\uff3b\u5b64"
                 "\u7acb 3.4-3.5s\u2248\u7535\u6c60\u5185 4.1s=\u5957"
                 "\u4ef6\u589e\u957f\u5224\u636e 19\u219237\u00b7\u57fa"
                 "\u7ebf\u951a R1681 \u65e7\u5bb9\u91cf\u975e\u6027\u80fd"
                 "\u9000\u5316\u00b7R1698 \u540c\u65cf\uff3d\u2192"
                 "--update-baseline \u91cd\u951a 202 \u6761\u76ee "
                 "DRIFT-CLEAN\uff1bscore 2\uff09")
    lines[i] = "- [x] " + lines[i][len("- [ ] "):] + done_note
    reseed = ("- [ ] \u51b7\u699c\u8de8\u91cd\u542f\u6301\u4e45\u5316"
              "\u4f8b\u7a97\u63a2\u7d22\uff08cold_board \u540e\u7ee7"
              "\uff1aclose\u2192\u65b0\u5b9e\u4f8b\u540c\u5e93\u91cd"
              "\u5f00\u51b7\u699c\u9010\u5b57\u8282\u540c\u4e00\u4f8b"
              "\u7a97\u3014persist \u4f8b\u7a97\u65cf R1889/R1900/"
              "R1902 \u5224\u8bfb\u00b7\u8bfb\u65f6\u6d3e\u751f\u9762="
              "\u8de8\u91cd\u542f\u96f6\u6f02\u79fb\u4f8b+\u91cd\u542f"
              "\u540e\u65b0\u6570\u636e\u51b7\u70ed\u8fc1\u79fb\u7eed"
              "\u63a5\u00b7hot_board \u65cf R1923 \u540c\u6e90\u3015"
              "\uff09\u2014\u2014\u79cd\u5b50=curation.py cold_board "
              "R1970 \u5728\u518c\u00b7\u5165\u5217 2026-10-14"
              "\u3014R1970 \u8865\u79cd\u3015")
    if not any("R1970 \u8865\u79cd" in l for l in lines):
        lines.insert(i + 1, reseed)
    io.open(P_EXPLORE, "w", encoding="utf-8", newline="").write(
        "\n".join(lines))
    print("1. explore.md: line45 done-flip + reseed inserted")

# ---------- 2. state.json byte surgery: tick + 2 log lines ----------
sraw = io.open(P_STATE, "r", encoding="utf-8", newline="").read()
already = ("R1970 P3" in sraw)
if not already:
    assert sraw.count('"tick": 1969,') == 1, "tick occurrence != 1"
    sraw = sraw.replace('"tick": 1969,', '"tick": 1970,')
round_line = (
    "2026-10-14 R1970 P3 explore \u9a8c\u5934\u4ea4\u4ed8\u8f6e"
    "\uff08\u4e94\u9759\u5168\u7eff\u2192\u7ebf\u5e8f\u62c9\u6d3b"
    "\uff1aP1 \u5168\u95e8\u63a7\uff3b\u96f7\u8fbe\u6e05\u5355 "
    "21:41 \u672a\u8fbe/\u5bf9\u8d26\u5f53\u65e5 00:46 \u5df2\u8dd1/"
    "BigLife \u5916\u4ef6\u672a\u8fbe/bootstrap CEO \u7269\u7406\u4ef6"
    "\uff3d+P2 \u5168\u95e8\u63a7\uff3bdocker \u7f3a\u4f4d/\u81ea"
    "\u7136\u4e8b\u4ef6\u89c2\u5bdf\u7a97/10-16 \u6cbb\u7406\u7a97"
    "\uff3d\u2192P3 explore \u9a8c\u5934=\u7b56\u5c55\u51b7\u699c"
    "\u8bfb\u9762\uff3bcuration.py hot_board R1753 \u79cd\u5b50"
    "\uff3d\u8ba4\u9886\u00b7\u5224\u636e\u9884\u6ce8\u518c\u5148"
    "\u4e8e\u4ee3\u7801\uff3bAC-CB1..CB5 \u5168\u6587\u5148\u843d "
    "explore.md \u884c\u5185\u518d\u52a8\u5de5\uff3d\u2192\u4e09"
    "\u4ef6\u843d\u5730\uff1acuration.py \u589e cold_board\uff3b"
    "heat==0 \u9006\u6ee4\u00b7\u5355 hot_board \u6d3e\u751f\u6e90"
    "\u96f6\u7b2c\u4e8c\u805a\u5408\u00b7curation_id ASC rank 1..N"
    "\u00b7\u96f6\u7b56\u5c55\u6ce8\u518c\u9762=\u8bda\u5b9e\u7a7a"
    "\u699c\uff3d+test_curation.py \u6269\u4e94\u4f8b\uff3bSUITE "
    "PASS 24/24 \u53cc\u8dd1 exit 0/0=qa/curation-coldboard-"
    "R1970.log \u4e09\u8282\uff3d+reconcile_all SUITES "
    "ledger-curation \u5224\u636e 19\u219224 \u63a5\u7ebf\uff3b"
    "RUNNER PASS 202/202 \u5224\u636e 1758\u21921763 controls 7/7 "
    "175.1s=qa/reconcile-all-R1970.log\uff3d+\u77e9\u9635\u518d"
    "\u751f --check byte-identical\uff3b202/1763/19441B\uff3d"
    "\u2014\u2014runner_profile drift \u9762 ugc +2.2s FLAG \u9694"
    "\u79bb\u5f52\u56e0\uff3b\u5b64\u7acb\u8dd1 3.4-3.5s\u2248\u7535"
    "\u6c60\u5185 4.1s=\u975e\u5171\u9a7b\u566a\u58f0\u00b7\u771f"
    "\u56e0=\u5957\u4ef6\u589e\u957f\u5224\u636e 19\u219237\u00b7"
    "\u57fa\u7ebf\u951a R1681 \u65e7\u5bb9\u91cf\uff3d\u2192"
    "--update-baseline \u91cd\u951a 202 \u5168\u6761\u76ee\u2192"
    "DRIFT-CLEAN\uff3b202 compared 0 flagged\uff3d\uff3bR1698 "
    "\u5165\u518c\u589e\u957f\u975e\u5224\u636e\u6f02\u79fb\u540c"
    "\u65cf\uff3d\u2014\u2014explore \u9600\u5217\u6d88\u8d39 1 "
    "\u8865\u79cd 1\uff3bcold_board \u8de8\u91cd\u542f\u6301\u4e45"
    "\u5316\u4f8b\u7a97\u79cd\u5b50\u00b7persist \u4f8b\u7a97\u65cf "
    "R1923/R1926 \u540c\u6e90\uff3d=10 \u5b88\u6052\u00b7score 2"
    "\uff3b\u53ef\u8dd1/\u80fd\u770b/\u80fd\u7528\u4ea7\u54c1\u5b9e"
    "\u7269\uff3d\uff09")
tokens_line = (
    "2026-10-14 R1970 tokens: local=unmeasured api=0 "
    "api_reason=zero external cloud calls (P3 read-face "
    "delivery: five-silence scan + criteria pre-registration + "
    "suite double-run + full RUNNER battery + matrix regen + "
    "drift attribution and baseline re-anchor + evidence/export/"
    "heartbeat writes all local stdlib; no cloud APIs this "
    "round)")
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
    print("2. state.json: tick 1970 + 2 log lines (parse-gated)")
else:
    print("2. state.json: R1970 rows already appended"
          " (idempotent skip)")

# ---------- 3. heartbeat row ----------
hb_raw = io.open(P_HB, "r", encoding="utf-8", newline="").read()
hb_eol = "\r\n" if hb_raw.endswith("\r\n") else "\n"
if " | tick 1970 | " in hb_raw:
    print("3. heartbeat: R1970 row already present (skip)")
else:
    hb_row = (
        _dt.datetime.now().astimezone().isoformat(timespec="seconds")
        + " | BigDomain OSLoop alive | tick 1970 | R1970: curation "
        "zero-heat cold_board read face delivered (P3 explore head; "
        "criteria pre-registered pre-code AC-CB1..CB5; SUITE PASS "
        "24/24 double-run, RUNNER PASS 202/202 criteria 1758->1763 "
        "controls 7/7, matrix regen byte-identical; ugc drift flag "
        "attributed to suite growth 19->37 criteria, baseline "
        "re-anchored 202 entries DRIFT-CLEAN) "
        "[via BigDomain-OSLoop]")
    if not hb_raw.endswith(("\r\n", "\n")):
        hb_raw += hb_eol
    hb_raw += hb_row + hb_eol
    io.open(P_HB, "w", encoding="utf-8", newline="").write(hb_raw)
    print("3. heartbeat: R1970 row appended")

# ---------- 4. export refresh (F3 derived) ----------
sys.path.insert(0, HERE)
import check_export_consistency as cec  # noqa: E402
derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1970, "stale tick in export refresh"
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
results_row = (
    "R1970: P3 explore-queue head delivered - curation zero-heat "
    "cold board read face (cold_board: honest inverse filter of "
    "the theme heat board, single live hot_board() derivation "
    "source, zero second aggregation engine, curation_id ASC "
    "rank 1..N, honest empty board over zero-curation and "
    "all-hot worlds; criteria AC-CB1..CB5 pre-registered in the "
    "explore.md row before the code existed). Three artifacts: "
    "curation.py cold_board + test_curation.py five cases (SUITE "
    "PASS 24/24 double-run exit 0/0, qa/curation-coldboard-"
    "R1970.log) + reconcile_all SUITES ledger-curation 19->24 "
    "(RUNNER PASS 202/202 criteria 1758->1763 controls 7/7 "
    "175.1s, qa/reconcile-all-R1970.log); matrix regen --check "
    "byte-identical 202/1763. runner_profile drift face ugc "
    "+2.2s flag attributed by isolated re-run (3.4-3.5s isolated "
    "~= 4.1s in-battery = suite growth criteria 19->37 vs the "
    "R1681-era baseline, not degradation) and the baseline "
    "re-anchored to 202 entries -> DRIFT-CLEAN. Explore queue "
    "consumed 1 reseeded 1 (cold_board cross-restart "
    "persistence window, persist-family precedent) = 10 held.")
export_obj["results"] = [r for r in export_obj["results"]
                         if not (isinstance(r, list) and len(r) == 2
                                 and r[0] == "R1970")]
export_obj["results"].insert(0, ["R1970", results_row])
tick_label = pat["tick_row_label"]
tick_idx = [j for j, r in enumerate(export_obj["results"])
             if len(r) == 2 and r[1] == tick_label]
if tick_idx:
    export_obj["results"][tick_idx[0]][0] = "1970"
else:
    export_obj["results"].append(["1970", tick_label])
if len(export_obj["results"]) > 40:
    export_obj["results"] = export_obj["results"][:40]
export_obj["ceo_face"]["current"] = (
    "R1970: P3 explore-queue head delivered - the curation "
    "zero-heat cold board read face (cold_board honest inverse "
    "filter of the theme heat board, single live hot_board() "
    "derivation source, zero second aggregation engine; "
    "criteria pre-registered before code) - suite SUITE PASS "
    "24/24 double-run, full battery RUNNER PASS 202/202 "
    "controls 7/7, matrix regen byte-identical, criteria "
    "1758->1763; ugc drift flag attributed to suite growth and "
    "the profile baseline re-anchored 202 entries DRIFT-CLEAN.")
export_obj["ceo_face"]["latest_artifact"] = (
    "src/sandbox/ledger/curation.py cold_board read face + "
    "qa/curation-coldboard-R1970.log + qa/reconcile-all-"
    "R1970.log (2026-10-14)")
export_obj["ceo_face"]["next_milestone"] = (
    "P3 read-face family continues FIFO (civicpoints / "
    "apimarket / honorcert / datasub / showcase leaderboard "
    "seeds queued); radar candidate list OH-20261014-cph4 due "
    "tonight ~21:41 (backlog row 1 gated on external arrival, "
    "no fabrication); within 48h.")
sd = dict(derived)
sd["method"] = ("machine-derived from state.json log per "
                "BD-PROP-001 caliber "
                "(check_export_consistency.recompute)")
export_obj["self_drive"] = sd
out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
print("4. export refreshed:", json.dumps(sd, sort_keys=True))

# ---------- 5. verify: checker + gauge + eol ----------
for cmd in (
    [sys.executable, os.path.join(HERE, "check_export_consistency.py")],
    [sys.executable, os.path.join(HERE, "logs_toolkit.py"), "gauge"],
    [sys.executable, os.path.join(HERE, "logs_toolkit.py"), "eol"],
):
    p = subprocess.run(cmd, capture_output=True, cwd=ROOT)
    tail = [l for l in p.stdout.decode("utf-8", errors="replace")
            .splitlines() if l.strip()][-3:]
    print("5. verify rc=%d :: %s" % (p.returncode,
                                     " | ".join(tail)))
    if p.returncode != 0:
        print("VERIFY-FAIL", cmd[-1])
        sys.exit(2)
print("CLOSEOUT-OK R1970")
