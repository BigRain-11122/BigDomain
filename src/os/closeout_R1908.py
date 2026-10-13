# -*- coding: utf-8 -*-
"""R1908 closeout driver (byte-surgery discipline, closeout_R1905
precedent). Faces:
  1. state/queue/tech.md - done flip + exec note on the claimed
     row + reseed row at queue tail (drain_recover sanity probe
     first: seed honest only if the face exists)
  2. src/os/state.json - tick 1907->1908, +2 log lines (CRLF
     layout, 16-space items, zero json.dump full rewrite)
  3. heartbeat.txt - +1 row (EOL-matched append)
  4. docs/status-export.json - surgical flush (export_ts, ceo_face
     three lines, results tick row 1907->1908, +1 results pair,
     self_drive window counts recomputed to the checker caliber)
     then check_export_consistency gate
Chinese payload: src/os/closeout_payload_R1908.json (data file).
Pure stdlib, zero network, pure ASCII source."""
import datetime
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_PAYLOAD = os.path.join(BASE, "closeout_payload_R1908.json")
P_STATE = os.path.join(BASE, "state.json")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_CHECKER = os.path.join(BASE, "check_export_consistency.py")
P_TECH = os.path.join(ROOT, "state", "queue", "tech.md")
P_PATTERNS = os.path.join(BASE, "export_consistency_patterns.json")
P_PIPELINE = os.path.join(ROOT, "src", "sandbox", "ugc",
                          "pipeline.py")
PY = sys.executable

with open(P_PAYLOAD, encoding="utf-8") as h:
    payload = json.load(h)


def q(text):
    return json.dumps(text, ensure_ascii=False).encode("utf-8")


def main():
    report = []
    ts = datetime.datetime.now().astimezone().isoformat(
        timespec="seconds")

    # -- 0. drain_recover sanity probe (seed honesty gate) -------
    seed_ok = False
    with open(P_PIPELINE, encoding="utf-8") as h:
        psrc = h.read()
    if "def drain_recover" in psrc:
        i = psrc.find("def drain_recover")
        seg = psrc[i:i + 1600]
        seed_ok = "window" in seg
    report.append("drain_recover seed sanity: %s"
                  % ("face+window present" if seed_ok
                     else "PROBE FAILED - seed skipped"))

    # -- 1. tech.md surgery (claimed row done + reseed) ----------
    with open(P_TECH, encoding="utf-8") as h:
        tech = h.read()
    if "[done 2026-10-13 R1908]" in tech:
        report.append("tech.md: R1908 done already present -"
                      " skipped")
    else:
        claim_marker = (u"R1908 \u8ba4\u9886\u00b7\u5224\u636e"
                        u"\u9884\u6ce8\u518c")
        assert tech.count(claim_marker) == 1, "claim anchor"
        row_head = (u"- [ ] apidev reject_tally "
                    u"\u7a97\u8bfb\u8de8\u91cd\u542f\u6301\u4e45"
                    u"\u5316\u4f8b\u7a97")
        assert row_head in tech, "claimed row head not found"
        tech = tech.replace(row_head, row_head.replace("- [ ]",
                                                      "- [x]"), 1)
        # append the done note right after the claim marker tail
        anchor = (u"\u51bb\u7ed3\u949f\u6062\u590d\u63a2\u9488"
                  u"\uff09\u2014\u2014\u30142026-10-13 R1908 "
                  u"\u8ba4\u9886\u3015")
        # anchor = "冻结钟恢复探针）——〔2026-10-13 R1908 认领〕"
        assert anchor in tech, "claim tail anchor not found"
        idx = tech.find(anchor) + len(anchor)
        tech = (tech[:idx] + payload["tech_done_note"]
                + tech[idx:])
        if seed_ok:
            eol = "\r\n" if "\r\n" in tech[:2000] else "\n"
            tech = tech.rstrip("\r\n") + eol + \
                payload["tech_seed_row"] + eol
        with open(P_TECH, "w", encoding="utf-8", newline="") as h:
            h.write(tech)
        report.append("tech.md: claimed row flipped [x] + done"
                      " note; reseed=%s"
                      % ("drain_recover seed appended"
                         if seed_ok else "SKIPPED"))

    # -- 2. state.json byte surgery ------------------------------
    with open(P_STATE, "rb") as h:
        b = h.read()
    if b.count(b'"tick": 1908') == 1 and \
            q(payload["state_tokens_line"]) in b:
        report.append("state.json: already applied - skipped")
    else:
        old_state_bytes = len(b)
        assert b.count(b'"tick": 1907') == 1, "tick anchor"
        b = b.replace(b'"tick": 1907', b'"tick": 1908')
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
        assert parsed["tick"] == 1908, "tick bump failed"
        assert parsed["log"][-1] == payload["state_tokens_line"]
        assert parsed["log"][-2] == payload["state_round_line"]
        bare = b2.replace(b"\r\n", b"").count(b"\n")
        assert bare == 0, "bare LF introduced (%d)" % bare
        with open(P_STATE, "wb") as h:
            h.write(b2)
        report.append("state.json: tick 1908, +2 log lines, "
                      "%d->%d bytes"
                      % (old_state_bytes, len(b2)))

    # -- 3. heartbeat append ------------------------------------
    with open(P_HB, "rb") as h:
        hb = h.read()
    if b"tick 1908 |" in hb:
        report.append("heartbeat: R1908 row already present -"
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
    old_ts_b = None
    with open(P_EXPORT, encoding="utf-8") as h:
        ex = json.load(h)
    old_ts_b = ('"export_ts": "%s"' % ex["export_ts"]).encode(
        "utf-8")
    if b'"tick": 1908' in e and \
            q(payload["ceo_current"]) in e:
        report.append("status-export.json: R1908 flush already"
                      " present - skipped")
    else:
        old_e = len(e)
        assert e.count(old_ts_b) == 1, "export_ts anchor"
        e = e.replace(old_ts_b,
                     b'"export_ts": "' + ts.encode("ascii")
                     + b'"')
        old_vals = ex["ceo_face"]
        for key, newval in (("current", payload["ceo_current"]),
                            ("latest_artifact",
                             payload["ceo_latest"]),
                            ("next_milestone",
                             payload["ceo_next"])):
            oldq = q(old_vals[key])
            assert e.count(oldq) == 1, "ceo_face %s anchor" % key
            e = e.replace(oldq, q(newval))
        # tick row 1907 -> 1908
        with open(P_PATTERNS, encoding="utf-8") as h:
            pat = json.load(h)
        label = pat["tick_row_label"]
        tick_anchor = ('[\n   "1907",\n   "%s' % label).encode(
            "utf-8")
        assert e.count(tick_anchor) == 1, "tick row anchor"
        e = e.replace(tick_anchor,
                     ('[\n   "1908",\n   "%s' % label).encode(
                         "utf-8"))
        # results pair append
        tail_anchor = b'"\n  ]\n ],\n "self_drive": {'
        assert e.count(tail_anchor) == 1, "results tail anchor"
        new_tail = (b'"\n  ],\n  [\n   "2",\n   '
                    + q(payload["export_results_line"])
                    + b'\n  ]\n ],\n "self_drive": {')
        e = e.replace(tail_anchor, new_tail)
        # self_drive recomputed counts (checker caliber,
        # post-fold + post-closeout):
        #   W  = 9 (four 10-11 rolling lines + gen502/503/504
        #            + R1908 round + R1908 tokens)
        #   sub= 1 (R1908 round main only)
        #   queues unchanged 6/10/10 (consume 1 + reseed 1)
        for oldv, newv in (
                (b'"log_lines_in_window": 26',
                 b'"log_lines_in_window": 9'),
                (b'"substantive_non_idle_mention_lines": 10',
                 b'"substantive_non_idle_mention_lines": 1')):
            assert e.count(oldv) == 1, "sd anchor %r" % oldv
            e = e.replace(oldv, newv)
        parsed_e = json.loads(e.decode("utf-8"))
        assert len(parsed_e["results"]) == 887, \
            "results append count"
        assert parsed_e["ceo_face"]["next_milestone"] == \
            payload["ceo_next"], "ceo_face flush"
        assert parsed_e["self_drive"][
            "log_lines_in_window"] == 9
        with open(P_EXPORT, "wb") as h:
            h.write(e)
        report.append("status-export.json: export_ts + ceo_face"
                      " 3 lines + tick row 1908 + results pair"
                      " (886->887) + self_drive W=9 sub=1, "
                      "%d->%d bytes" % (old_e, len(e)))

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
