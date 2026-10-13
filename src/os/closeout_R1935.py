# -*- coding: utf-8 -*-
"""R1935 closeout driver (closeout_R1932 family precedent):
  1. tech.md markers verify (datasub row done, open rows 10)
  2. evidence chain verify (datasub log + runner log + matrix)
  3. src/os/state.json - tick 1934->1935, +2 log lines (CRLF
     layout, 16-space items, zero json.dump rewrite; the R1934
     indent disease was pre-fixed via eol --fix-indent)
  4. heartbeat.txt - +1 row (tick 1935, EOL-matched append)
  5. docs/status-export.json - surgical flush (export_ts live
     clock, ceo_face three lines, tick row 1934->1935, +1
     results row prepended newest-first, self_drive recomputed
     via check_export_consistency.recompute) then the gate.
Chinese payloads: src/os/closeout_payload_R1935.json.
Pure stdlib, zero network, pure ASCII source."""
import datetime
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
D = os.path.dirname(os.path.abspath(__file__))
P_PAYLOAD = os.path.join(D, "closeout_payload_R1935.json")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_CHECKER = os.path.join(ROOT, "src", "os",
                         "check_export_consistency.py")
P_TECH = os.path.join(ROOT, "state", "queue", "tech.md")
P_PATTERNS = os.path.join(ROOT, "src", "os",
                          "export_consistency_patterns.json")
P_EV = os.path.join(ROOT, "qa", "datasub-persist-R1935.log")
P_RUNNER = os.path.join(ROOT, "qa", "reconcile-all-R1935.log")
P_MATRIX = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")
PY = sys.executable

sys.path.insert(0, D)
import check_export_consistency as cec  # noqa: E402

with open(P_PAYLOAD, encoding="utf-8-sig") as h:
    payload = json.load(h)


def q(text):
    return json.dumps(text, ensure_ascii=False).encode("utf-8")


def jrep(value):
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def main():
    report = []
    ts = datetime.datetime.now().astimezone().isoformat(
        timespec="seconds")

    # -- 1. tech + evidence verification --------------------------
    with open(P_TECH, encoding="utf-8") as h:
        tech = h.read()
    assert tech.count("[done 2026-10-14 R1935]") == 1, \
        "datasub done marker"
    open_rows = sum(1 for ln in tech.splitlines()
                    if ln.startswith("- [ ]"))
    assert open_rows == 10, "tech open rows %d" % open_rows
    report.append("tech.md: datasub done marker x1,"
                  " open rows = 10")
    for path, name, anchors in (
            (P_EV, "datasub evidence", (
                "sha16 run1=c620990d4f1170e8"
                " run2=c620990d4f1170e8 byte-identical=True",
                "RUNNER PASS (173/173 suites green, reconcile"
                " controls 7/7, 243.7s)",
                "VERDICT PASS")),
            (P_RUNNER, "runner evidence", (
                "PASS suite ledger-datasub-persist exit=0"
                " pass-lines=7 fail-lines=0 criteria=7",)),
            (P_MATRIX, "matrix", (
                "| 173 | ledger-datasub-persist"
                " | ledger/test_datasub_persist.py | 7"
                " | green | 0.3 |",))):
        with open(path, encoding="utf-8") as h:
            ev_text = h.read()
        for a in anchors:
            assert a in ev_text, "evidence %s: %s" % (name, a)
        report.append("evidence[%s]: %d anchors ok"
                      % (name, len(anchors)))

    # -- 2. state.json byte surgery ------------------------------
    with open(P_STATE, "rb") as h:
        b = h.read()
    if b.count(b'"tick": 1935') == 1 and \
            q(payload["state_tokens_line"]) in b:
        report.append("state.json: already applied - skipped")
    else:
        old_state_bytes = len(b)
        assert b.count(b'"tick": 1934') == 1, "tick anchor"
        parsed_pre = json.loads(b.decode("utf-8"))
        assert parsed_pre["tick"] == 1934, "pre tick"
        assert parsed_pre["last_gord_tbl_rows"] == 375, \
            "gord baseline expected 375 (no new rows)"
        assert parsed_pre["last_decision_rows"] == 309, \
            "dec baseline expected 309 (no new rows)"
        b = b.replace(b'"tick": 1934', b'"tick": 1935')
        tail = b'"\r\n    ]\r\n}'
        assert b.endswith(tail), "state tail layout drift"
        prefix = b[: -len(tail)]
        add = (b'",'
               + b'\r\n                '
               + q(payload["state_round_line"])
               + b','
               + b'\r\n                '
               + q(payload["state_tokens_line"])
               + b'\r\n    ]\r\n}')
        b2 = prefix + add
        parsed = json.loads(b2.decode("utf-8"))
        assert parsed["tick"] == 1935, "tick bump failed"
        assert parsed["last_gord_tbl_rows"] == 375, "gord kept"
        assert parsed["last_decision_rows"] == 309, "dec kept"
        assert parsed["log"][-1] == payload["state_tokens_line"]
        assert parsed["log"][-2] == payload["state_round_line"]
        bare = b2.replace(b"\r\n", b"").count(b"\n")
        assert bare == 0, "bare LF introduced (%d)" % bare
        assert len(b2) < 78500, "fold line exceeded pre-write"
        with open(P_STATE, "wb") as h:
            h.write(b2)
        report.append("state.json: tick 1935, +2 log lines,"
                      " %d->%d bytes (fold line 78500 ok)"
                      % (old_state_bytes, len(b2)))

    # -- 3. heartbeat append -------------------------------------
    with open(P_HB, "rb") as h:
        hb = h.read()
    if b"tick 1935 |" in hb:
        report.append("heartbeat: R1935 row already present -"
                      " skipped")
    else:
        eol = b"\r\n" if hb.endswith(b"\r\n") else b"\n"
        row = (ts.encode("ascii")
               + payload["hb_body"].encode("utf-8") + eol)
        with open(P_HB, "ab") as h:
            h.write(row)
        report.append("heartbeat: +1 row ts=%s" % ts)

    # -- 4. export surgical flush --------------------------------
    with open(P_EXPORT, "rb") as h:
        e = h.read()
    with open(P_EXPORT, encoding="utf-8") as h:
        ex = json.load(h)
    nl = e.replace(b"\r\n", b"\n")
    old_ts_b = ('"export_ts": "%s"' % ex["export_ts"]).encode(
        "utf-8")
    if q(payload["ceo_current"]) in nl:
        report.append("status-export.json: R1935 flush already"
                      " present - skipped")
    else:
        old_e = len(e)
        old_results_n = len(ex["results"])
        assert nl.count(old_ts_b) == 1, "export_ts anchor"
        nl = nl.replace(old_ts_b,
                        b'"export_ts": "' + ts.encode("ascii")
                        + b'"')
        old_vals = ex["ceo_face"]
        for key, newval in (("current", payload["ceo_current"]),
                            ("latest_artifact",
                             payload["ceo_latest"]),
                            ("next_milestone",
                             payload["ceo_next"])):
            oldq = q(old_vals[key])
            assert nl.count(oldq) == 1, "ceo_face %s" % key
            nl = nl.replace(oldq, q(newval))
        with open(P_PATTERNS, encoding="utf-8") as h:
            pat = json.load(h)
        label = pat["tick_row_label"]
        tick_anchor = ('[\n   "1934",\n   "%s' % label).encode(
            "utf-8")
        assert nl.count(tick_anchor) == 1, "tick row anchor"
        nl = nl.replace(tick_anchor,
                        ('[\n   "1935",\n   "%s'
                         % label).encode("utf-8"))
        head_anchor = b'"results": [\n  [\n   "R1934",'
        assert nl.count(head_anchor) == 1, "results head anchor"
        new_head = (b'"results": [\n'
                   + b'  [\n   "R1935",\n   '
                   + q(payload["export_results_line_r1935"])
                   + b'\n  ],\n'
                   + b'  [\n   "R1934",')
        nl = nl.replace(head_anchor, new_head)
        derived, _st, _ex, _pat = cec.recompute()
        for key, newval in derived.items():
            if key not in ex["self_drive"]:
                continue
            oldval = ex["self_drive"][key]
            if oldval == newval:
                continue
            oldb = ('"%s": ' % key).encode("utf-8") + jrep(oldval)
            newb = ('"%s": ' % key).encode("utf-8") + jrep(newval)
            assert nl.count(oldb) == 1, "sd anchor %s" % key
            nl = nl.replace(oldb, newb)
        parsed_e = json.loads(nl.decode("utf-8"))
        assert len(parsed_e["results"]) == old_results_n + 1, \
            "results prepend count"
        assert parsed_e["results"][0][0] == "R1935", "head row"
        assert parsed_e["ceo_face"]["next_milestone"] == \
            payload["ceo_next"], "ceo_face flush"
        for key, newval in derived.items():
            assert parsed_e["self_drive"].get(key) == newval, \
                "self_drive %s mismatch" % key
        assert parsed_e["self_drive"].get("method") == \
            ex["self_drive"]["method"], "method note kept"
        crlf2 = nl.count(b"\r\n")
        assert crlf2 == 0, "export CRLF introduced"
        with open(P_EXPORT, "wb") as h:
            h.write(nl)
        report.append("status-export.json: export_ts + ceo_face"
                      " 3 lines + tick row 1935 + results"
                      " prepend x1 (%d->%d) + self_drive"
                      " recompute (log_lines %d, sub %d,"
                      " queue_tech_open %d), %d->%d bytes"
                      % (old_results_n, old_results_n + 1,
                         derived["log_lines_in_window"],
                         derived["substantive_non_idle_"
                                 "mention_lines"],
                         derived["queue_tech_open"],
                         old_e, len(nl)))

    # -- 5. consistency gate --------------------------------------
    proc = subprocess.run([PY, P_CHECKER], cwd=ROOT,
                          capture_output=True)
    out = proc.stdout.decode("utf-8", "replace").replace(
        "\r\n", "\n")
    verdict = [ln for ln in out.splitlines()
               if ln.startswith("VERDICT")]
    summary = [ln for ln in out.splitlines()
               if ln.startswith("SUMMARY")]
    report.append("check_export_consistency: rc=%d %s"
                  % (proc.returncode,
                     verdict[-1] if verdict else "NO-VERDICT"))
    if summary:
        report.append(summary[-1])
    for line in report:
        print(line, flush=True)
    ok = (proc.returncode == 0
          and verdict and verdict[-1].strip() == "VERDICT PASS")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
