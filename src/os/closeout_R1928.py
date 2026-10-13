# -*- coding: utf-8 -*-
"""R1928 closeout driver (closeout_R1921 single-payload precedent):
the round's predecessor (R1927) crashed at ~20:16 after its own
state surgery + heartbeat row + the full civic-persist evidence
chain landed, but before commit/push and before the export flush.
This takeover round re-verified everything live
(qa/civictakeover-R1928.log TAKEOVER VERDICT=PASS - civic suite
double-run byte-identical with sha16 f55b475347ce0afd exact match
under the R1884 capture-normalization law, seven-face at-rest
anchors, stray misfired-redirect artifact removed) and this
driver completes the closeout:
  1. tech.md anchors verify (pay duplicate-closed + civic done
     markers applied by the predecessor; open rows 8)
  2. evidence chain verify (both orphan logs + takeover log)
  3. src/os/state.json - tick 1927->1928 (gord baseline 367
     kept: gord_new_rows=0 this round), +2 log lines
     (CRLF layout, 16-space items, zero json.dump full rewrite)
  4. heartbeat.txt - +1 row (tick 1928, EOL-matched append)
  5. docs/status-export.json - surgical flush (export_ts with
     live clock - honest note: the R1926 closeout had written a
     future-stamp 21:10 vs the live clock 20:2x, clock-ahead
     artifact; ceo_face three lines; tick row 1926->1928; +2
     results rows R1928+R1927 prepended newest-first; self_drive
     recomputed via check_export_consistency.recompute - the
     canonical caliber: log_lines 15->19, sub 3->5,
     queue_tech_open 10->8) then check_export_consistency gate.
Chinese payloads: src/os/closeout_payload_R1928.json.
Pure stdlib, zero network, pure ASCII source."""
import datetime
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
D = os.path.dirname(os.path.abspath(__file__))
P_PAYLOAD = os.path.join(D, "closeout_payload_R1928.json")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_CHECKER = os.path.join(ROOT, "src", "os",
                         "check_export_consistency.py")
P_TECH = os.path.join(ROOT, "state", "queue", "tech.md")
P_PATTERNS = os.path.join(ROOT, "src", "os",
                          "export_consistency_patterns.json")
P_EV_ORPHAN = os.path.join(ROOT, "qa", "civicpersist-R1927.log")
P_EV_RUNNER = os.path.join(ROOT, "qa", "reconcile-all-R1927.log")
P_EV_TAKEOVER = os.path.join(ROOT, "qa",
                             "civictakeover-R1928.log")
P_MATRIX = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")
P_JUNK = os.path.join(ROOT, "src", "sandbox", "--help")
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

    # -- 1. artifact verification --------------------------------
    with open(P_TECH, encoding="utf-8") as h:
        tech = h.read()
    assert tech.count("duplicate-closed 2026-10-13 R1927") == 1, \
        "pay duplicate-closed marker"
    assert tech.count("done 2026-10-13 R1927") == 1, \
        "civic done marker"
    assert "- [ ] lobby" in tech, "next FIFO head open row"
    open_rows = sum(1 for ln in tech.splitlines()
                    if ln.startswith("- [ ]"))
    assert open_rows == 8, "tech open rows %d" % open_rows
    report.append("tech.md: pay duplicate-closed + civic done"
                  " markers x1, open rows = 8")
    for path, name, anchors in (
            (P_EV_ORPHAN, "orphan suite evidence", (
                "SUITE PASS (7/7 criteria green)",
                "RUNNER PASS (166/166 suites green",
                "byte-identical (16347 bytes",
                "verdict: DRIFT-CLEAN",
                "verdict CLEAN domains=5")),
            (P_EV_RUNNER, "orphan runner evidence", (
                "RUNNER PASS (166/166 suites green, reconcile"
                " controls 7/7, 178.8s)",)),
            (P_EV_TAKEOVER, "takeover evidence", (
                "sha16=f55b475347ce0afd",
                "TAKEOVER VERDICT=PASS"))):
        with open(path, encoding="utf-8") as h:
            ev_text = h.read()
        for a in anchors:
            assert a in ev_text, "evidence %s: %s" % (name, a)
        report.append("evidence[%s]: %d anchors ok"
                      % (name, len(anchors)))
    assert os.path.getsize(P_MATRIX) == 16347, "matrix size"
    report.append("matrix on disk: 16347 bytes")
    assert not os.path.exists(P_JUNK), "stray artifact back?"
    report.append("stray artifact src/sandbox/--help absent"
                  " (removed by takeover harness)")

    # -- 2. state.json byte surgery ------------------------------
    with open(P_STATE, "rb") as h:
        b = h.read()
    if b.count(b'"tick": 1928') == 1 and \
            q(payload["state_tokens_line"]) in b:
        report.append("state.json: already applied - skipped")
    else:
        old_state_bytes = len(b)
        assert b.count(b'"tick": 1927') == 1, "tick anchor"
        assert b.count(b'"last_gord_tbl_rows": 367') == 1, \
            "gord baseline anchor (unchanged this round)"
        parsed_pre = json.loads(b.decode("utf-8"))
        assert parsed_pre["log"][-1].startswith(
            "2026-10-13 R1927 tokens"), "pre tail = R1927 tokens"
        assert parsed_pre["log"][-2].startswith(
            "2026-10-13 R1927 "), "pre tail-1 = R1927 round"
        b = b.replace(b'"tick": 1927', b'"tick": 1928')
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
        assert parsed["tick"] == 1928, "tick bump failed"
        assert parsed["last_gord_tbl_rows"] == 367, "gord kept"
        assert parsed["log"][-1] == payload["state_tokens_line"]
        assert parsed["log"][-2] == payload["state_round_line"]
        bare = b2.replace(b"\r\n", b"").count(b"\n")
        assert bare == 0, "bare LF introduced (%d)" % bare
        with open(P_STATE, "wb") as h:
            h.write(b2)
        report.append("state.json: tick 1928, gord 367 kept,"
                      " +2 log lines, %d->%d bytes"
                      % (old_state_bytes, len(b2)))

    # -- 3. heartbeat append -------------------------------------
    with open(P_HB, "rb") as h:
        hb = h.read()
    if b"tick 1928 |" in hb:
        report.append("heartbeat: R1928 row already present -"
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
        report.append("status-export.json: R1928 flush already"
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
        # tick row 1926 -> 1928 (lag-2 catch-up: R1927 crash
        # skipped its flush)
        with open(P_PATTERNS, encoding="utf-8") as h:
            pat = json.load(h)
        label = pat["tick_row_label"]
        tick_anchor = ('[\n   "1926",\n   "%s' % label).encode(
            "utf-8")
        assert nl.count(tick_anchor) == 1, "tick row anchor"
        nl = nl.replace(tick_anchor,
                        ('[\n   "1928",\n   "%s'
                         % label).encode("utf-8"))
        # results prepend x2 (newest-first, R1922..R1926
        # precedent), before the current head row R1926
        head_anchor = b'"results": [\n [\n   "R1926",'
        assert nl.count(head_anchor) == 1, "results head anchor"
        new_head = (b'"results": [\n'
                   + b' [\n   "R1928",\n   '
                   + q(payload["export_results_line_r1928"])
                   + b'\n  ],\n'
                   + b' [\n   "R1927",\n   '
                   + q(payload["export_results_line_r1927"])
                   + b'\n  ],\n'
                   + b' [\n   "R1926",')
        nl = nl.replace(head_anchor, new_head)
        # self_drive: recompute via the canonical checker
        # caliber (state surgery already applied above)
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
        assert len(parsed_e["results"]) == old_results_n + 2, \
            "results prepend count"
        assert parsed_e["results"][0][0] == "R1928", "head row"
        assert parsed_e["results"][1][0] == "R1927", "second row"
        assert parsed_e["ceo_face"]["next_milestone"] == \
            payload["ceo_next"], "ceo_face flush"
        for key, newval in derived.items():
            assert parsed_e["self_drive"].get(key) == newval, \
                "self_drive %s mismatch" % key
        assert parsed_e["self_drive"].get("method") == \
            ex["self_drive"]["method"], "method note kept"
        bare_lf2 = nl.count(b"\r\n")
        assert bare_lf2 == 0, "export CRLF introduced"
        with open(P_EXPORT, "wb") as h:
            h.write(nl)
        report.append("status-export.json: export_ts (live clock,"
                      " clock-ahead artifact honest-noted)"
                      " + ceo_face 3 lines + tick row 1928"
                      " + results prepend x2 (%d->%d)"
                      " + self_drive recompute"
                      " (log_lines %d, sub %d, queue_tech_open"
                      " %d), %d->%d bytes"
                      % (old_results_n, old_results_n + 2,
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
