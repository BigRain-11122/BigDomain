# -*- coding: utf-8 -*-
"""R1913 closeout driver (byte-surgery discipline,
closeout_R1912 precedent). Faces:
  1. state/queue/tech.md - done flip on the claimed row (done
     note inserted at the claim tail anchor) + reseed row at
     queue tail (ugc review-desk pool_query/chronicle_query
     persist seed; sanity probe first: seed honest only if both
     faces exist in pipeline.py)
  2. src/os/state.json - tick 1912->1913, +2 log lines (CRLF
     layout, 16-space items, zero json.dump full rewrite)
  3. heartbeat.txt - +1 row (EOL-matched append)
  4. docs/status-export.json - surgical flush (export_ts,
     ceo_face three lines, tick row 1912->1913, +1 results pair
     891->892, self_drive window counts 17->19 / 5->6 to the
     checker caliber) then check_export_consistency gate
Chinese payload: src/os/closeout_payload_R1913.json (data file).
Pure stdlib, zero network, pure ASCII source."""
import datetime
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_PAYLOAD = os.path.join(BASE, "closeout_payload_R1913.json")
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

    # -- 0. review-desk seed sanity probe (seed honesty) ----------
    seed_ok = False
    with open(P_PIPELINE, encoding="utf-8") as h:
        psrc = h.read()
    if "def pool_query" in psrc and "def chronicle_query" in psrc:
        seed_ok = True
    report.append("review-desk seed sanity: %s"
                  % ("both faces present (pipeline.py)" if seed_ok
                     else "PROBE FAILED - seed skipped"))

    # -- 1. tech.md surgery (claimed row done + reseed) ----------
    with open(P_TECH, encoding="utf-8") as h:
        tech = h.read()
    if "[done 2026-10-13 R1913]" in tech:
        report.append("tech.md: R1913 done already present -"
                      " skipped")
    else:
        row_head = u"- [ ] ugc pipeline drain_recover "
        assert tech.count(row_head) == 1, "claimed row head"
        tech = tech.replace(row_head,
                            row_head.replace("- [ ]", "- [x]"), 1)
        # claim tail anchor: the registered criteria block ends
        # the line (my claim order = EXPECTED check then runner
        # row, distinct from the R1912 claim order)
        tail_anchor = (u"EXPECTED \u6f02\u79fb\u68c0\u67e5"
                       u"+runner row wired")
        assert tech.count(tail_anchor) == 1, "claim tail anchor"
        idx = tech.find(tail_anchor)
        insert_at = idx + len(tail_anchor)
        tech = (tech[:insert_at] + payload["tech_done_note"]
                + tech[insert_at:])
        if seed_ok:
            eol = "\r\n" if "\r\n" in tech[:2000] else "\n"
            tech = tech.rstrip("\r\n") + eol + \
                payload["tech_seed_row"] + eol
        with open(P_TECH, "w", encoding="utf-8", newline="") as h:
            h.write(tech)
        report.append("tech.md: claimed row flipped [x] + done"
                      " note at claim tail; reseed=%s"
                      % ("ugc review-desk pool_query/chronicle"
                         "_query persist seed appended"
                         if seed_ok else "SKIPPED"))

    # -- 2. state.json byte surgery ------------------------------
    with open(P_STATE, "rb") as h:
        b = h.read()
    if b.count(b'"tick": 1913') == 1 and \
            q(payload["state_tokens_line"]) in b:
        report.append("state.json: already applied - skipped")
    else:
        old_state_bytes = len(b)
        assert b.count(b'"tick": 1912') == 1, "tick anchor"
        b = b.replace(b'"tick": 1912', b'"tick": 1913')
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
        assert parsed["tick"] == 1913, "tick bump failed"
        assert parsed["log"][-1] == payload["state_tokens_line"]
        assert parsed["log"][-2] == payload["state_round_line"]
        bare = b2.replace(b"\r\n", b"").count(b"\n")
        assert bare == 0, "bare LF introduced (%d)" % bare
        with open(P_STATE, "wb") as h:
            h.write(b2)
        report.append("state.json: tick 1913, +2 log lines, "
                      "%d->%d bytes"
                      % (old_state_bytes, len(b2)))

    # -- 3. heartbeat append ------------------------------------
    with open(P_HB, "rb") as h:
        hb = h.read()
    if b"tick 1913 |" in hb:
        report.append("heartbeat: R1913 row already present -"
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
    if b'"tick": 1913' in e and \
            q(payload["ceo_current"]) in e:
        report.append("status-export.json: R1913 flush already"
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
        # tick row 1912 -> 1913
        with open(P_PATTERNS, encoding="utf-8") as h:
            pat = json.load(h)
        label = pat["tick_row_label"]
        tick_anchor = ('[\n   "1912",\n   "%s' % label).encode(
            "utf-8")
        assert e.count(tick_anchor) == 1, "tick row anchor"
        e = e.replace(tick_anchor,
                      ('[\n   "1913",\n   "%s' % label).encode(
                          "utf-8"))
        # results pair append 891 -> 892
        tail_anchor = b'"\n  ]\n ],\n "self_drive": {'
        assert e.count(tail_anchor) == 1, "results tail anchor"
        new_tail = (b'"\n  ],\n  [\n   "2",\n   '
                    + q(payload["export_results_line"])
                    + b'\n  ]\n ],\n "self_drive": {')
        e = e.replace(tail_anchor, new_tail)
        # self_drive recomputed counts (checker caliber,
        # post-closeout): W = 19 (four 10-11 rolling lines +
        # gen502/503/504 + R1908..R1913 six round+tokens pairs);
        # sub = 6 (the six round mains only; fold lines are
        # paren summaries); queues unchanged (consume 1 +
        # reseed 1)
        for oldv, newv in (
                (b'"log_lines_in_window": 17',
                 b'"log_lines_in_window": 19'),
                (b'"substantive_non_idle_mention_lines": 5',
                 b'"substantive_non_idle_mention_lines": 6')):
            assert e.count(oldv) == 1, "sd anchor %r" % oldv
            e = e.replace(oldv, newv)
        parsed_e = json.loads(e.decode("utf-8"))
        assert len(parsed_e["results"]) == 892, \
            "results append count"
        assert parsed_e["ceo_face"]["next_milestone"] == \
            payload["ceo_next"], "ceo_face flush"
        assert parsed_e["self_drive"][
            "log_lines_in_window"] == 19
        with open(P_EXPORT, "wb") as h:
            h.write(e)
        report.append("status-export.json: export_ts + ceo_face"
                      " 3 lines + tick row 1913 + results pair"
                      " (891->892) + self_drive W=19 sub=6, "
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
