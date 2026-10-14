# -*- coding: utf-8 -*-
"""R1981 closeout driver (closeout_R1978 family precedent):
  0. evidence section-5 append (runner + matrix verdicts, twin
     note, DONE marker) then explore.md surgery: claimed row
     [ ]->[x] + done note append + reseed row append (consume 1
     reseed 1, open=10 held)
  1. markers verify (done marker x1, open rows 10) + evidence
     chain verify (suite log + runner log + matrix)
  2. src/os/state.json - tick 1980->1981, GORD baseline 421->403
     (group-side compression -18, zero new @BigDomain rows,
     tail rows all consumed 10-14 state), +2 log lines (CRLF
     layout, 16-space items, zero json.dump rewrite) - fold
     R524 already executed pre-closeout (post==predicted
     74368B, census DRIFT-CLEAN)
  3. heartbeat.txt - +1 row (tick 1981, EOL-matched append)
  4. docs/status-export.json - surgical flush (export_ts live
     clock, ceo_face three lines, tick row 1980->1981, +1
     results row prepended newest-first, self_drive recomputed
     via check_export_consistency.recompute) then the gate.
Chinese payloads: src/os/closeout_payload_R1981.json.
Pure stdlib, zero network, pure ASCII source."""
import datetime
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
D = os.path.dirname(os.path.abspath(__file__))
P_PAYLOAD = os.path.join(D, "closeout_payload_R1981.json")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_CHECKER = os.path.join(ROOT, "src", "os",
                         "check_export_consistency.py")
P_EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
P_PATTERNS = os.path.join(ROOT, "src", "os",
                          "export_consistency_patterns.json")
P_EV = os.path.join(ROOT, "qa", "honorcert-yearbookpersist-R1981.log")
P_RUNNER = os.path.join(ROOT, "qa", "reconcile-all-R1981.log")
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

    # -- 0a. evidence section-5 append ----------------------------
    with open(P_EV, "rb") as h:
        ev_raw = h.read()
    if b"DONE R1981" in ev_raw:
        report.append("evidence: section 5 already present - skip")
    else:
        sec5 = [
            "",
            "-- section 5: full regression closeout --",
            "RUNNER PASS 210/210 suites green, reconcile controls"
            " 7/7, 176.9s (SUITES 209->210, criteria 1808->1814"
            " with AC-HYP1..HYP6)",
            "suite_matrix regen green=210/210 (20206 bytes, 210"
            " suites, 1814 criteria) + --check byte-identical",
            "census post-RUNNER re-check: flags=0 DRIFT-CLEAN",
            "evidence twin: qa/reconcile-all-R1981.log (runner"
            " Tee)",
            "DONE R1981",
        ]
        add = ("\n".join(sec5) + "\n").encode("utf-8")
        if ev_raw and not ev_raw.endswith(b"\n"):
            add = b"\n" + add
        with open(P_EV, "ab") as h:
            h.write(add)
        report.append("evidence: section 5 appended (+DONE marker)")

    # -- 0b. explore.md surgery (done-flip + reseed) ---------------
    with open(P_EXPLORE, "rb") as h:
        eb = h.read()
    etext = eb.decode("utf-8")
    if "done 2026-10-15 R1981" in etext:
        report.append("explore.md: done marker already present"
                      " - surgery skipped")
    else:
        lines = etext.splitlines(keepends=True)
        claim_idx = [i for i, ln in enumerate(lines)
                     if ln.startswith("- [ ] ")
                     and "R1981 " + chr(0x8ba4) + chr(0x9886)
                     in ln]
        assert len(claim_idx) == 1, "claim row not unique: %r" \
            % claim_idx
        i = claim_idx[0]
        body = lines[i]
        if not body.endswith("\n"):
            body_eol = ""
        elif body.endswith("\r\n"):
            body_eol = "\r\n"
        else:
            body_eol = "\n"
        stripped = body.rstrip("\r\n")
        assert stripped.startswith("- [ ] "), "claim flip anchor"
        flipped = ("- [x] "
                   + stripped[len("- [ ] "):].rstrip()
                   + payload["explore_done_note"])
        eol = body_eol if body_eol else (
            "\r\n" if eb.endswith(b"\r\n") else "\n")
        lines[i] = flipped + eol
        reseed = payload["explore_reseed_row"] + eol
        out = "".join(lines)
        if not out.endswith("\n"):
            out += eol
        out += reseed
        with open(P_EXPLORE, "wb") as h:
            h.write(out.encode("utf-8"))
        report.append("explore.md: claim row flipped + done note"
                      " + reseed row appended")

    # -- 1. markers + evidence verification ----------------------
    with open(P_EXPLORE, encoding="utf-8") as h:
        ex_text = h.read()
    assert ex_text.count("done 2026-10-15 R1981") == 1, \
        "explore done marker"
    open_rows = sum(1 for ln in ex_text.splitlines()
                    if ln.startswith("- [ ]"))
    assert open_rows == 10, "explore open rows %d" % open_rows
    report.append("explore.md: done marker x1, open rows = 10")
    for path, name, anchors in (
            (P_EV, "suite evidence", (
                "SUITE PASS 6/6",
                "run1 exit=0 run2 exit=0 stdout-byte-identical=True",
                "VERDICT PASS",
                "DONE R1981")),
            (P_RUNNER, "runner evidence", (
                "RUNNER PASS (210/210 suites green, reconcile"
                " controls 7/7, 176.9s)",)),
            (P_MATRIX, "matrix", (
                "ledger-honorcert-yearbookpersist | ledger/"
                "test_honorcert_yearbook_persist.py | 6 | green |",
                "RUNNER PASS 210/210 suites green, reconcile"
                " controls 7/7"))):
        with open(path, encoding="utf-8") as h:
            ev_text = h.read()
        for a in anchors:
            assert a in ev_text, "evidence %s: %s" % (name, a)
        report.append("evidence[%s]: %d anchors ok"
                      % (name, len(anchors)))

    # -- 2. state.json byte surgery ------------------------------
    with open(P_STATE, "rb") as h:
        b = h.read()
    if b.count(b'"tick": 1981') == 1 and \
            q(payload["state_tokens_line"]) in b:
        report.append("state.json: already applied - skipped")
    else:
        old_state_bytes = len(b)
        assert b.count(b'"tick": 1980') == 1, "tick anchor"
        parsed_pre = json.loads(b.decode("utf-8"))
        assert parsed_pre["tick"] == 1980, "pre tick"
        assert parsed_pre["last_gord_tbl_rows"] == 421, \
            "gord baseline expected 421"
        assert parsed_pre["last_decision_rows"] == 266, \
            "dec baseline expected 266 (token-flat kept)"
        b = b.replace(b'"tick": 1980', b'"tick": 1981')
        assert b.count(b'"last_gord_tbl_rows": 421') == 1, \
            "gord anchor"
        b = b.replace(b'"last_gord_tbl_rows": 421',
                      b'"last_gord_tbl_rows": 403')
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
        assert parsed["tick"] == 1981, "tick bump failed"
        assert parsed["last_gord_tbl_rows"] == 403, "gord updated"
        assert parsed["last_decision_rows"] == 266, "dec kept"
        assert parsed["log"][-1] == payload["state_tokens_line"]
        assert parsed["log"][-2] == payload["state_round_line"]
        bare = b2.replace(b"\r\n", b"").count(b"\n")
        assert bare == 0, "bare LF introduced (%d)" % bare
        assert len(b2) < 78500, "fold line exceeded pre-write"
        with open(P_STATE, "wb") as h:
            h.write(b2)
        report.append("state.json: tick 1981, GORD 421->403,"
                      " +2 log lines, %d->%d bytes"
                      " (fold line 78500 ok)"
                      % (old_state_bytes, len(b2)))

    # -- 3. heartbeat append -------------------------------------
    with open(P_HB, "rb") as h:
        hb = h.read()
    if b"tick 1981 |" in hb:
        report.append("heartbeat: R1981 row already present -"
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
        report.append("status-export.json: R1981 flush already"
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
        tick_anchor = ('[\n   "1980",\n   "%s' % label).encode(
            "utf-8")
        assert nl.count(tick_anchor) == 1, "tick row anchor"
        nl = nl.replace(tick_anchor,
                        ('[\n   "1981",\n   "%s'
                         % label).encode("utf-8"))
        head_anchor = b'"results": [\n  [\n   "R1980",'
        assert nl.count(head_anchor) == 1, "results head anchor"
        new_head = (b'"results": [\n'
                   + b'  [\n   "R1981",\n   '
                   + q(payload["export_results_line_r1981"])
                   + b'\n  ],\n'
                   + b'  [\n   "R1980",')
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
        assert parsed_e["results"][0][0] == "R1981", "head row"
        assert parsed_e["results"][-1][1] == label, "tick tail"
        assert parsed_e["ceo_face"]["next_milestone"] == \
            payload["ceo_next"], "ceo_face flush"
        for key, newval in derived.items():
            assert parsed_e["self_drive"].get(key) == newval, \
                "self_drive %s mismatch" % key
        if "method" in ex["self_drive"]:
            assert parsed_e["self_drive"].get("method") == \
                ex["self_drive"]["method"], "method note kept"
        crlf2 = nl.count(b"\r\n")
        assert crlf2 == 0, "export CRLF introduced"
        with open(P_EXPORT, "wb") as h:
            h.write(nl)
        report.append("status-export.json: export_ts + ceo_face"
                      " 3 lines + tick row 1981 + results"
                      " prepend x1 (%d->%d) + self_drive"
                      " recompute, %d->%d bytes"
                      % (old_results_n, old_results_n + 1,
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
