# -*- coding: utf-8 -*-
"""R1910 closeout driver (byte-surgery discipline,
closeout_R1909 precedent). Faces:
  1. state/queue/tech.md - done flip + exec note on the claimed
     row + reseed row at queue tail (lobby room_message_board
     sanity probe first: seed honest only if the face exists)
  2. src/os/state.json - tick 1909->1910, +2 log lines (CRLF
     layout, 16-space items, zero json.dump full rewrite)
  3. heartbeat.txt - +1 row (EOL-matched append)
  4. docs/status-export.json - surgical flush (export_ts,
     ceo_face three lines, tick row 1909->1910, +1 results pair,
     self_drive window counts recomputed to the checker caliber)
     then check_export_consistency gate
Chinese payload: src/os/closeout_payload_R1910.json (data file).
Pure stdlib, zero network, pure ASCII source."""
import datetime
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_PAYLOAD = os.path.join(BASE, "closeout_payload_R1910.json")
P_STATE = os.path.join(BASE, "state.json")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_CHECKER = os.path.join(BASE, "check_export_consistency.py")
P_TECH = os.path.join(ROOT, "state", "queue", "tech.md")
P_PATTERNS = os.path.join(BASE, "export_consistency_patterns.json")
P_LOBBY_STORE = os.path.join(ROOT, "src", "sandbox", "lobby",
                             "store.py")
P_LOBBY_SERVER = os.path.join(ROOT, "src", "sandbox", "lobby",
                              "server.py")
PY = sys.executable

with open(P_PAYLOAD, encoding="utf-8") as h:
    payload = json.load(h)


def q(text):
    return json.dumps(text, ensure_ascii=False).encode("utf-8")


def main():
    report = []
    ts = datetime.datetime.now().astimezone().isoformat(
        timespec="seconds")

    # -- 0. lobby room_message_board sanity probe (seed honesty)
    seed_ok = False
    with open(P_LOBBY_STORE, encoding="utf-8") as h:
        ssrc = h.read()
    if "def room_message_board" in ssrc:
        seed_ok = True
    with open(P_LOBBY_SERVER, encoding="utf-8") as h:
        vsrc = h.read()
    seed_ok = seed_ok and "handle_room_board" in vsrc
    report.append("lobby seed sanity: %s"
                  % ("face present (store+server)" if seed_ok
                     else "PROBE FAILED - seed skipped"))

    # -- 1. tech.md surgery (claimed row done + reseed) ----------
    with open(P_TECH, encoding="utf-8") as h:
        tech = h.read()
    if "[done 2026-10-13 R1910]" in tech:
        report.append("tech.md: R1910 done already present -"
                      " skipped")
    else:
        claim_marker = (u"\u5224\u636e\u8ba1\u6570\u81ea\u68c0"
                        u"\u2014\u2014\u30142026-10-13 R1910 "
                        u"\u8ba4\u9886\u3015")
        # claim_marker = "判据计数自检——〔2026-10-13 R1910 认领〕"
        assert tech.count(claim_marker) == 1, "claim anchor"
        row_head = (u"- [ ] water journal "
                    u"\u4e09\u59ca\u59b9\u8bfb\u9762")
        assert row_head in tech, "claimed row head not found"
        tech = tech.replace(row_head, row_head.replace("- [ ]",
                                                      "- [x]"), 1)
        anchor = claim_marker
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
                      % ("lobby room_message_board seed appended"
                         if seed_ok else "SKIPPED"))

    # -- 2. state.json byte surgery ------------------------------
    with open(P_STATE, "rb") as h:
        b = h.read()
    if b.count(b'"tick": 1910') == 1 and \
            q(payload["state_tokens_line"]) in b:
        report.append("state.json: already applied - skipped")
    else:
        old_state_bytes = len(b)
        assert b.count(b'"tick": 1909') == 1, "tick anchor"
        b = b.replace(b'"tick": 1909', b'"tick": 1910')
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
        assert parsed["tick"] == 1910, "tick bump failed"
        assert parsed["log"][-1] == payload["state_tokens_line"]
        assert parsed["log"][-2] == payload["state_round_line"]
        bare = b2.replace(b"\r\n", b"").count(b"\n")
        assert bare == 0, "bare LF introduced (%d)" % bare
        with open(P_STATE, "wb") as h:
            h.write(b2)
        report.append("state.json: tick 1910, +2 log lines, "
                      "%d->%d bytes"
                      % (old_state_bytes, len(b2)))

    # -- 3. heartbeat append ------------------------------------
    with open(P_HB, "rb") as h:
        hb = h.read()
    if b"tick 1910 |" in hb:
        report.append("heartbeat: R1910 row already present -"
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
    old_ts_b = ('"export_ts": "%s"' % ex["export_ts"]).encode(
        "utf-8")
    if b'"tick": 1910' in e and \
            q(payload["ceo_current"]) in e:
        report.append("status-export.json: R1910 flush already"
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
        # tick row 1909 -> 1910
        with open(P_PATTERNS, encoding="utf-8") as h:
            pat = json.load(h)
        label = pat["tick_row_label"]
        tick_anchor = ('[\n   "1909",\n   "%s' % label).encode(
            "utf-8")
        assert e.count(tick_anchor) == 1, "tick row anchor"
        e = e.replace(tick_anchor,
                      ('[\n   "1910",\n   "%s' % label).encode(
                          "utf-8"))
        # results pair append
        tail_anchor = b'"\n  ]\n ],\n "self_drive": {'
        assert e.count(tail_anchor) == 1, "results tail anchor"
        new_tail = (b'"\n  ],\n  [\n   "2",\n   '
                    + q(payload["export_results_line"])
                    + b'\n  ]\n ],\n "self_drive": {')
        e = e.replace(tail_anchor, new_tail)
        # self_drive recomputed counts (checker caliber,
        # post-closeout): W = 13 (four 10-11 rolling lines +
        # gen502/503/504 + R1908/R1909/R1910 round+tokens pairs);
        # sub = 3 (R1908 + R1909 + R1910 round mains only; fold
        # lines are paren summaries); queues unchanged 6/10/10
        # (consume 1 + reseed 1)
        for oldv, newv in (
                (b'"log_lines_in_window": 11',
                 b'"log_lines_in_window": 13'),
                (b'"substantive_non_idle_mention_lines": 2',
                 b'"substantive_non_idle_mention_lines": 3')):
            assert e.count(oldv) == 1, "sd anchor %r" % oldv
            e = e.replace(oldv, newv)
        parsed_e = json.loads(e.decode("utf-8"))
        assert len(parsed_e["results"]) == 889, \
            "results append count"
        assert parsed_e["ceo_face"]["next_milestone"] == \
            payload["ceo_next"], "ceo_face flush"
        assert parsed_e["self_drive"][
            "log_lines_in_window"] == 13
        with open(P_EXPORT, "wb") as h:
            h.write(e)
        report.append("status-export.json: export_ts + ceo_face"
                      " 3 lines + tick row 1910 + results pair"
                      " (888->889) + self_drive W=13 sub=3, "
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
