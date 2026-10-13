# -*- coding: utf-8 -*-
"""R1905 closeout driver (byte-surgery discipline, closeout_R1868
precedent; R1710 indent-disease / R1646 NUL-clobber lessons).
Faces:
  1. src/os/state.json - tick 1904->1905, +2 log lines (CRLF layout,
     16-space items, zero json.dump full rewrite)
  2. heartbeat.txt - +1 row (EOL-matched append)
  3. docs/status-export.json - surgical flush (export_ts, ceo_face
     three lines, results tick row 1904->1905, +1 results pair,
     self_drive window counts) then check_export_consistency gate
Chinese payload: src/os/closeout_payload_R1905.json (data file).
Pure stdlib, zero network, pure ASCII source."""
import datetime
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_PAYLOAD = os.path.join(BASE, "closeout_payload_R1905.json")
P_STATE = os.path.join(BASE, "state.json")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_CHECKER = os.path.join(BASE, "check_export_consistency.py")
PY = sys.executable

with open(P_PAYLOAD, encoding="utf-8") as h:
    payload = json.load(h)


def q(text):
    return json.dumps(text, ensure_ascii=False).encode("utf-8")


def main():
    report = []
    # -- 1. state.json byte surgery (idempotent guard) --------------
    with open(P_STATE, "rb") as h:
        b = h.read()
    if b.count(b'"tick": 1905') == 1 and \
            q(payload["state_tokens_line"]) in b:
        report.append("state.json: already applied (tick 1905 + "
                      "R1905 log lines present) - skipped")
    else:
        old_state_bytes = len(b)
        assert b.count(b'"tick": 1904') == 1, "tick anchor not unique"
        b = b.replace(b'"tick": 1904', b'"tick": 1905')
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
        assert parsed["tick"] == 1905, "tick bump failed"
        assert parsed["log"][-1] == payload["state_tokens_line"], \
            "log append failed"
        assert parsed["log"][-2] == payload["state_round_line"]
        bare = b2.replace(b"\r\n", b"").count(b"\n")
        assert bare == 0, "bare LF introduced (%d)" % bare
        crlf = b2.count(b"\r\n")
        with open(P_STATE, "wb") as h:
            h.write(b2)
        report.append("state.json: tick 1905, +2 log lines, "
                      "%d->%d bytes, crlf=%d bare_lf=0"
                      % (old_state_bytes, len(b2), crlf))

    # -- 2. heartbeat append (idempotent guard) --------------------
    with open(P_HB, "rb") as h:
        hb = h.read()
    if b"tick 1905 |" in hb:
        report.append("heartbeat: R1905 row already present - "
                      "skipped")
    else:
        eol = b"\r\n" if hb.endswith(b"\r\n") else b"\n"
        ts = datetime.datetime.now().astimezone().isoformat(
            timespec="seconds")
        row = (ts.encode("ascii")
               + payload["hb_body"].encode("utf-8") + eol)
        with open(P_HB, "ab") as h:
            h.write(row)
        report.append("heartbeat: +1 row ts=%s (eol=%s)"
                      % (ts, "CRLF" if eol == b"\r\n" else "LF"))

    ts = datetime.datetime.now().astimezone().isoformat(
        timespec="seconds")

    # -- 3. export surgical flush (single buffer) -------------------
    with open(P_EXPORT, "rb") as h:
        e = h.read()
    old_ts = b'"export_ts": "2026-10-13T07:44:49+08:00"'
    if old_ts not in e:
        report.append("status-export.json: R1905 flush already "
                      "present - skipped")
    else:
        old_e = len(e)
        assert e.count(old_ts) == 1, "export_ts anchor"
        e = e.replace(old_ts,
                      b'"export_ts": "' + ts.encode("ascii") + b'"')
        old_vals = json.loads(e.decode("utf-8"))["ceo_face"]
        for key, newval in (("current", payload["ceo_current"]),
                            ("latest_artifact", payload["ceo_latest"]),
                            ("next_milestone", payload["ceo_next"])):
            oldq = q(old_vals[key])
            assert e.count(oldq) == 1, "ceo_face %s anchor" % key
            e = e.replace(oldq, q(newval))
        tick_anchor = b'[\n   "1904",\n   "OSLoop'
        assert e.count(tick_anchor) == 1, "tick row anchor"
        e = e.replace(tick_anchor, b'[\n   "1905",\n   "OSLoop')
        tail_anchor = b'"\n  ]\n ],\n "self_drive": {'
        assert e.count(tail_anchor) == 1, "results tail anchor"
        new_tail = (b'"\n  ],\n  [\n   "2",\n   '
                    + q(payload["export_results_line"])
                    + b'\n  ]\n ],\n "self_drive": {')
        e = e.replace(tail_anchor, new_tail)
        assert e.count(b'"log_lines_in_window": 20') == 1, "W anchor"
        e = e.replace(b'"log_lines_in_window": 20',
                      b'"log_lines_in_window": 22')
        assert e.count(
            b'"substantive_non_idle_mention_lines": 7') == 1, \
            "sub anchor"
        e = e.replace(b'"substantive_non_idle_mention_lines": 7',
                      b'"substantive_non_idle_mention_lines": 8')
        parsed_e = json.loads(e.decode("utf-8"))
        assert len(parsed_e["results"]) == 884, "results append count"
        assert parsed_e["ceo_face"]["next_milestone"] == \
            payload["ceo_next"], "ceo_face flush"
        with open(P_EXPORT, "wb") as h:
            h.write(e)
        report.append("status-export.json: export_ts + ceo_face 3"
                      " lines + tick row 1905 + results pair +"
                      " self_drive counts, %d->%d bytes"
                      % (old_e, len(e)))

    # -- 4. consistency gate ----------------------------------------
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
