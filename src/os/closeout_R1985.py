# -*- coding: utf-8 -*-
"""R1985 takeover closeout driver (closeout_R1981 family precedent):
  0. evidence section-5 append (takeover verification + runner +
     matrix verdicts + DONE marker) then explore.md surgery:
     claimed row [ ]->[x] + claim/done note append + reseed row
     append (consume 1 reseed 1, open-count conservation asserted)
  1. state.json byte surgery: tick 1984->1985, baselines kept
     (gord 416 / dec-rows 266 - five-silence FLAT probe), +2 log
     lines (CRLF layout, 16-space items, zero json.dump rewrite);
     fold R527 already executed pre-closeout (post==predicted
     67957B)
  2. heartbeat.txt +1 row (tick 1985, EOL-matched append)
  3. docs/status-export.json surgical flush (export_ts live clock,
     ceo_face three lines, tick row 1984->1985, +1 results row
     prepended newest-first, self_drive recomputed via
     check_export_consistency.recompute) then the gate.
Chinese payloads: src/os/closeout_payload_R1985.json.
Pure stdlib, zero network, pure ASCII source."""
import datetime
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
D = os.path.dirname(os.path.abspath(__file__))
P_PAYLOAD = os.path.join(D, "closeout_payload_R1985.json")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_CHECKER = os.path.join(ROOT, "src", "os",
                         "check_export_consistency.py")
P_EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
P_PATTERNS = os.path.join(ROOT, "src", "os",
                          "export_consistency_patterns.json")
P_EV = os.path.join(ROOT, "qa", "coverageboard-window-R1985.log")
P_RUNNER2 = os.path.join(ROOT, "qa", "reconcile-all-R1985b-2.log")
P_MATRIX = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")
PY = sys.executable

sys.path.insert(0, D)
import check_export_consistency as cec  # noqa: E402

with open(P_PAYLOAD, encoding="utf-8-sig") as h:
    payload = json.load(h)

RE_OPEN = re.compile(r"^- \[ \]")


def q(text):
    return json.dumps(text, ensure_ascii=False).encode("utf-8")


def jrep(value):
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def main():
    report = []
    ts = datetime.datetime.now().astimezone().isoformat(
        timespec="seconds")

    # -- 0a. evidence section-5 append ----------------------------
    with open(P_EV, "rb") as h:
        ev_raw = h.read()
    if b"DONE R1985" in ev_raw:
        report.append("evidence: section 5 already present - skip")
    else:
        assert ev_raw.endswith(b"\n"), "evidence EOL layout"
        assert b"VERDICT PASS" in ev_raw, "evidence base verdict"
        assert b"57d176daa223d55f" in ev_raw, "evidence anchor"
        sec5 = "\n".join(payload["evidence_sec5"]) + "\n"
        with open(P_EV, "ab") as h:
            h.write(sec5.encode("utf-8"))
        report.append("evidence: section-5 appended (%d lines)"
                      % len(payload["evidence_sec5"]))

    # -- 0b. explore.md surgery (claim + done + reseed) -----------
    with open(P_EXPLORE, "rb") as h:
        exb = h.read()
    ex_text = exb.decode("utf-8")
    if payload["claim_anchor"] in ex_text and \
            "- [x] " + "" not in ex_text:
        pass
    if "done 2026-10-15 R1985" in ex_text:
        report.append("explore: claim already applied - skip")
    else:
        lines = ex_text.split("\n")
        idx = [i for i, ln in enumerate(lines)
               if ln.startswith("- [ ] ")
               and payload["claim_anchor"] in ln]
        assert len(idx) == 1, "claim row not unique: %d" % len(idx)
        pre_open = sum(1 for ln in lines if RE_OPEN.match(ln))
        row = lines[idx[0]]
        row2 = row.replace("- [ ] ", "- [x] ", 1) + \
            payload["claim_done_note"]
        lines[idx[0]] = row2
        tail_eol = "\r\n" if "\r\n" in ex_text[:2000] else "\n"
        body = "\n".join(lines)
        if not body.endswith("\n"):
            body += "\n"
        body += payload["reseed_row"] + "\n"
        with open(P_EXPLORE, "wb") as h:
            h.write(body.encode("utf-8"))
        post_open = sum(1 for ln in body.split("\n")
                        if RE_OPEN.match(ln))
        assert post_open == pre_open, ("open drift pre=%d post=%d"
                                       % (pre_open, post_open))
        report.append("explore: claimed row [x] + done note +"
                      " reseed; open %d->%d conservation ok"
                      % (pre_open, post_open))

    # -- 0c. evidence chain verify --------------------------------
    for name, path, anchors in (
            ("runner2", P_RUNNER2,
             ("RUNNER PASS (214/214 suites green, reconcile"
              " controls 7/7, 176.6s)",)),
            ("matrix", P_MATRIX,
             ("| 214 | 1842 | 214/214 | R1985 |",))):
        with open(path, encoding="utf-8") as h:
            ev_text = h.read()
        for a in anchors:
            assert a in ev_text, "evidence %s: %s" % (name, a)
        report.append("evidence[%s]: anchor ok" % name)

    # -- 1. state.json byte surgery ------------------------------
    with open(P_STATE, "rb") as h:
        b = h.read()
    if b.count(b'"tick": 1985') == 1:
        report.append("state.json: already applied - skipped")
    else:
        old_state_bytes = len(b)
        assert b.count(b'"tick": 1984') == 1, "tick anchor"
        parsed_pre = json.loads(b.decode("utf-8"))
        assert parsed_pre["tick"] == 1984, "pre tick"
        assert parsed_pre["last_gord_tbl_rows"] == 416, \
            "gord baseline expected 416"
        assert parsed_pre["last_decision_rows"] == 266, \
            "dec baseline expected 266 (token-flat kept)"
        b = b.replace(b'"tick": 1984', b'"tick": 1985')
        tail = b'"\r\n    ]\r\n}\r\n'
        assert b.endswith(tail), "state tail layout drift"
        prefix = b[: -len(tail)]
        add = (b'",'
               + b'\r\n                '
               + q(payload["state_round_line"])
               + b','
               + b'\r\n                '
               + q(payload["state_tokens_line"])
               + b'\r\n    ]\r\n}\r\n')
        b2 = prefix + add
        parsed = json.loads(b2.decode("utf-8"))
        assert parsed["tick"] == 1985, "tick bump failed"
        assert parsed["last_gord_tbl_rows"] == 416, "gord kept"
        assert parsed["last_decision_rows"] == 266, "dec kept"
        assert parsed["log"][-1] == payload["state_tokens_line"]
        assert parsed["log"][-2] == payload["state_round_line"]
        bare = b2.replace(b"\r\n", b"").count(b"\n")
        assert bare == 0, "bare LF introduced (%d)" % bare
        assert len(b2) < 78500, "fold line exceeded pre-write"
        with open(P_STATE, "wb") as h:
            h.write(b2)
        report.append("state.json: tick 1985, +2 log lines,"
                      " %d->%d bytes (fold line 78500 ok)"
                      % (old_state_bytes, len(b2)))

    # -- 2. heartbeat append -------------------------------------
    with open(P_HB, "rb") as h:
        hb = h.read()
    if b"tick 1985 |" in hb:
        report.append("heartbeat: R1985 row already present -"
                      " skipped")
    else:
        eol = b"\r\n" if hb.endswith(b"\r\n") else b"\n"
        row = (ts.encode("ascii")
               + payload["hb_body"].encode("utf-8") + eol)
        with open(P_HB, "ab") as h:
            h.write(row)
        report.append("heartbeat: +1 row ts=%s" % ts)

    # -- 3. export surgical flush --------------------------------
    with open(P_EXPORT, "rb") as h:
        e = h.read()
    with open(P_EXPORT, encoding="utf-8") as h:
        ex = json.load(h)
    nl = e.replace(b"\r\n", b"\n")
    old_ts_b = ('"export_ts": "%s"' % ex["export_ts"]).encode(
        "utf-8")
    if q(payload["ceo_current"]) in nl:
        report.append("status-export.json: R1985 flush already"
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
        tick_anchor = ('[\n   "1984",\n   "%s' % label).encode(
            "utf-8")
        assert nl.count(tick_anchor) == 1, "tick row anchor"
        nl = nl.replace(tick_anchor,
                        ('[\n   "1985",\n   "%s'
                         % label).encode("utf-8"))
        head_anchor = b'"results": [\n  [\n   "R1984",'
        assert nl.count(head_anchor) == 1, "results head anchor"
        new_head = (b'"results": [\n'
                   + b'  [\n   "R1985",\n   '
                   + q(payload["export_results_line_r1985"])
                   + b'\n  ],\n'
                   + b'  [\n   "R1984",')
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
        assert parsed_e["results"][0][0] == "R1985", "head row"
        assert parsed_e["results"][-1][1] == label, "tick tail"
        assert parsed_e["ceo_face"]["next_milestone"] == \
            payload["ceo_next"], "ceo_face flush"
        for key, newval in derived.items():
            assert parsed_e["self_drive"].get(key) == newval, \
                "self_drive %s mismatch" % key
        crlf2 = nl.count(b"\r\n")
        assert crlf2 == 0, "export CRLF introduced"
        with open(P_EXPORT, "wb") as h:
            h.write(nl)
        report.append("status-export.json: export_ts + ceo_face"
                      " 3 lines + tick row 1985 + results"
                      " prepend x1 (%d->%d) + self_drive"
                      " recompute, %d->%d bytes"
                      % (old_results_n, old_results_n + 1,
                         old_e, len(nl)))

    # -- 4. consistency gate --------------------------------------
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
