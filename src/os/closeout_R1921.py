# -*- coding: utf-8 -*-
"""R1921 closeout driver (closeout_R1920 precedent, single-payload
flavor): the round's predecessor crashed at 16:3x-16:49 after the
full evidence chain landed (qa/channel-migrate-persist-R1921.log five
sections, RUNNER 162/162, matrix 162/1474) but before the accounting
surgery; this takeover round re-verified everything live
(qa/channelmigrate-takeover-R1921.log TAKEOVER VERDICT=PASS +
at-rest EOL closure) and this driver completes the closeout:
  1. tech.md anchors verify (done marker + checkbox + reseed
     applied by the predecessor's own r1921_closeout_tech.py)
  2. evidence chain verify (both logs on disk)
  3. src/os/state.json - tick 1920->1921 (gord baseline 358
     unchanged: gord_new_rows=0 this round), +2 log lines
     (CRLF layout, 16-space items, zero json.dump full rewrite)
  4. heartbeat.txt - +1 row (EOL-matched append)
  5. docs/status-export.json - surgical flush (export_ts,
     ceo_face three lines, tick row 1920->1921, +1 results
     pair 899->900, self_drive W 16->18 / sub 4->5 /
     queue_tech_open 8 unchanged net-flat) then
     check_export_consistency gate
Chinese payloads: src/os/closeout_payload_R1921.json.
Pure stdlib, zero network, pure ASCII source."""
import datetime
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
D = os.path.dirname(os.path.abspath(__file__))
P_PAYLOAD = os.path.join(D, "closeout_payload_R1921.json")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_CHECKER = os.path.join(ROOT, "src", "os",
                         "check_export_consistency.py")
P_TECH = os.path.join(ROOT, "state", "queue", "tech.md")
P_PATTERNS = os.path.join(ROOT, "src", "os",
                          "export_consistency_patterns.json")
P_EV_ORPHAN = os.path.join(ROOT, "qa",
                           "channel-migrate-persist-R1921.log")
P_EV_TAKEOVER = os.path.join(ROOT, "qa",
                             "channelmigrate-takeover-R1921.log")
PY = sys.executable

with open(P_PAYLOAD, encoding="utf-8-sig") as h:
    payload = json.load(h)


def q(text):
    return json.dumps(text, ensure_ascii=False).encode("utf-8")


def main():
    report = []
    ts = datetime.datetime.now().astimezone().isoformat(
        timespec="seconds")

    # -- 1. artifact verification --------------------------------
    with open(P_TECH, encoding="utf-8") as h:
        tech = h.read()
    assert "done 2026-10-13 R1921" in tech, "tech done marker"
    assert "- [x] pay channel_status_matrix" in tech, "tech checkbox"
    assert "R1921 补种" in tech, "reseed marker"
    assert "- [ ] ledger showcase" in tech, "reseed open row"
    report.append("tech.md: done marker + checkbox + reseed row"
                  " present")
    for path, name, anchors in (
            (P_EV_ORPHAN, "orphan evidence", (
                "SUITE PASS 5/5", "RUNNER PASS (162/162",
                "verdict CLEAN domains=5")),
            (P_EV_TAKEOVER, "takeover evidence", (
                "TAKEOVER VERDICT=PASS", "AT-REST VERDICT=PASS"))):
        with open(path, encoding="utf-8") as h:
            ev_text = h.read()
        for a in anchors:
            assert a in ev_text, "evidence %s: %s" % (name, a)
        report.append("evidence[%s]: %s anchors ok (%d bytes)"
                      % (name, os.path.basename(path), len(ev_text)))

    # -- 2. state.json byte surgery ------------------------------
    with open(P_STATE, "rb") as h:
        b = h.read()
    if b.count(b'"tick": 1921') == 1 and \
            q(payload["state_tokens_line"]) in b:
        report.append("state.json: already applied - skipped")
    else:
        old_state_bytes = len(b)
        assert b.count(b'"tick": 1920') == 1, "tick anchor"
        assert b.count(b'"last_gord_tbl_rows": 358') == 1, \
            "gord baseline anchor (unchanged this round)"
        b = b.replace(b'"tick": 1920', b'"tick": 1921')
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
        assert parsed["tick"] == 1921, "tick bump failed"
        assert parsed["last_gord_tbl_rows"] == 358, "gord kept"
        assert parsed["log"][-1] == payload["state_tokens_line"]
        assert parsed["log"][-2] == payload["state_round_line"]
        bare = b2.replace(b"\r\n", b"").count(b"\n")
        assert bare == 0, "bare LF introduced (%d)" % bare
        with open(P_STATE, "wb") as h:
            h.write(b2)
        report.append("state.json: tick 1921, gord 358 kept,"
                      " +2 log lines, %d->%d bytes"
                      % (old_state_bytes, len(b2)))

    # -- 3. heartbeat append -------------------------------------
    with open(P_HB, "rb") as h:
        hb = h.read()
    if b"tick 1921 |" in hb:
        report.append("heartbeat: R1921 row already present -"
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
        report.append("status-export.json: R1921 flush already"
                      " present - skipped")
    else:
        old_e = len(e)
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
        # tick row 1920 -> 1921
        with open(P_PATTERNS, encoding="utf-8") as h:
            pat = json.load(h)
        label = pat["tick_row_label"]
        tick_anchor = ('[\n   "1920",\n   "%s' % label).encode(
            "utf-8")
        assert nl.count(tick_anchor) == 1, "tick row anchor"
        nl = nl.replace(tick_anchor,
                        ('[\n   "1921",\n   "%s'
                         % label).encode("utf-8"))
        # results pair append 899 -> 900 (score-2 row shape,
        # newest appended at the tail)
        tail_anchor = b'"\n  ]\n ],\n "self_drive": {'
        assert nl.count(tail_anchor) == 1, "results tail anchor"
        new_tail = (b'"\n  ],\n  [\n   "2",\n   '
                    + q(payload["export_results_line"])
                    + b'\n  ]\n ],\n "self_drive": {')
        nl = nl.replace(tail_anchor, new_tail)
        # self_drive recomputed counts (checker caliber,
        # post-closeout): W = 18 (prior 16 + R1921 round+tokens
        # pair); sub = 5 (the R1921 round line; tokens line
        # excluded by caliber); queue_tech_open = 8 (consume 1
        # + reseed 1, net flat)
        for oldv, newv in (
                (b'"log_lines_in_window": 16',
                 b'"log_lines_in_window": 18'),
                (b'"substantive_non_idle_mention_lines": 4',
                 b'"substantive_non_idle_mention_lines": 5')):
            assert nl.count(oldv) == 1, "sd anchor %r" % oldv
            nl = nl.replace(oldv, newv)
        assert nl.count(b'"queue_tech_open": 8') == 1, \
            "queue_tech_open=8 anchor"
        parsed_e = json.loads(nl.decode("utf-8"))
        assert len(parsed_e["results"]) == 900, \
            "results append count"
        assert parsed_e["ceo_face"]["next_milestone"] == \
            payload["ceo_next"], "ceo_face flush"
        assert parsed_e["self_drive"][
            "log_lines_in_window"] == 18
        with open(P_EXPORT, "wb") as h:
            h.write(nl)
        report.append("status-export.json: export_ts + ceo_face"
                      " 3 lines + tick row 1921 + results pair"
                      " (899->900) + self_drive W=18 sub=5"
                      " queue_tech=8 net-flat, %d->%d bytes"
                      % (old_e, len(nl)))

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
