"""R1902 closeout surgery (canonical family, closeout_R1900
pattern; state.json is mutated HERE by byte surgery per the R1710
discipline - PS5.1 form: CRLF, no BOM, PS-escape of the four
JSON-special chars in appended strings). Faces:
  1. state.json           : tick 1901 -> 1902, +2 log lines
     (round + tokens), verify-then-write (json.loads post-parse)
  2. tech.md              : verify claim flipped + done note +
     tail reseed present, open rows == 10
  3. heartbeat.txt        : +2 rows (tick 1901 backfill debt +
     tick 1902 live row)
  4. docs/status-export.json : flush via check_export_consistency
     .recompute() single-source caliber (AC-EC2), +1 result row,
     tick row -> 1902, ceo_face three rows, export_ts now
Chinese payload lives in closeout_payload_R1902.json (encoding
law). Pure stdlib, zero network, pure ASCII source."""

import datetime as _dt
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_PAYLOAD = os.path.join(
    BASE, "..", "..", ".codely-cli", "tmp",
    "closeout_payload_R1902.json")
P_STATE = os.path.join(BASE, "state.json")
P_TECH = os.path.join(ROOT, "state", "queue", "tech.md")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")


def ps_escape(text):
    return (text.replace("<", "\\u003c")
                .replace(">", "\\u003e")
                .replace("&", "\\u0026")
                .replace("'", "\\u0027"))


def detect_eol(text):
    return "\r\n" if "\r\n" in text else "\n"


def main():
    with open(P_PAYLOAD, encoding="utf-8") as fh:
        payload = json.load(fh)
    report = []

    # ---------- 1. state.json byte surgery -----------------------
    with open(P_STATE, "rb") as fh:
        raw = fh.read()
    assert raw[:3] != b"\xef\xbb\xbf", "unexpected BOM in state.json"
    text = raw.decode("utf-8")
    assert text.count("\n") == text.count("\r\n"), \
        "bare LF in state.json before surgery"
    obj = json.loads(text)
    assert obj["tick"] == 1901, "tick not 1901: %s" % obj["tick"]
    assert len(obj["log"]) == 17, \
        "log length expected 17, got %d" % len(obj["log"])
    assert obj["log"][-1].startswith(
        "2026-10-13 R1901 tokens: "), \
        "tail tokens line drift"
    old_tick = '"tick": 1901'
    new_tick = '"tick": 1902'
    assert text.count(old_tick) == 1, "tick anchor not unique"
    tail = '"\r\n    ]\r\n}'
    assert text.endswith(tail), "state tail anchor drift"
    new_text = text[:-len(tail)]
    rline = ps_escape(payload["state_round_line"])
    tline = ps_escape(payload["state_tokens_line"])
    new_text += ('",\r\n                "%s",\r\n'
                 '                "%s"\r\n    ]\r\n}'
                 % (rline, tline))
    new_text = new_text.replace(old_tick, new_tick)
    obj2 = json.loads(new_text)          # verify-then-write
    assert obj2["tick"] == 1902, "post tick drift"
    assert len(obj2["log"]) == 19, \
        "post log length expected 19, got %d" % len(obj2["log"])
    assert obj2["log"][-2].startswith(
        "2026-10-13 R1902 "), "post round line prefix drift"
    assert obj2["log"][-1].startswith(
        "2026-10-13 R1902 tokens: "), \
        "post tokens line prefix drift"
    for token in ("AC-DBL15", "AC-DBL21", "R1902"):
        assert token in obj2["log"][-2], \
            "criteria reference missing from round line: %s" % token
    with open(P_STATE, "wb") as fh:
        fh.write(new_text.encode("utf-8"))
    report.append("state.json ok: tick 1901->1902 log 17->19"
                  " bytes %d->%d" % (len(raw),
                                     len(new_text.encode("utf-8"))))

    # ---------- 2. tech.md verify (applied earlier this round) ---
    with open(P_TECH, "rb") as fh:
        tech_text = fh.read().decode("utf-8")
    eol = detect_eol(tech_text)
    tech_lines = tech_text.split(eol)
    tv = payload
    claim_hits = [l for l in tech_lines
                  if l.startswith(tv["tech_claim_prefix"])]
    assert len(claim_hits) == 1, \
        "tech claim row expected 1 hit, got %d" % len(claim_hits)
    assert tv["tech_done_marker"] in claim_hits[0], \
        "done note missing from claim row"
    assert "AC-DBL15" in claim_hits[0] \
        and "AC-DBL21" in claim_hits[0], \
        "pre-registered criteria block missing"
    reseed_hits = [l for l in tech_lines
                   if l.startswith("- [ ] ") and
                   tv["tech_reseed_marker"] in l]
    assert len(reseed_hits) == 1, \
        "reseed row expected exactly 1 open row, got %d" \
        % len(reseed_hits)
    open_rows = [l for l in tech_lines
                 if l.startswith("- [ ] ")]
    assert len(open_rows) == tv["tech_open_expected"], \
        "queue_tech_open expected %d, got %d" \
        % (tv["tech_open_expected"], len(open_rows))
    assert open_rows[-1].startswith("- [ ] apidev key_view "), \
        "reseed row not at queue tail"
    report.append("tech.md verified: claim flipped + done note +"
                  " tail reseed present; open=%d eol=%r"
                  % (len(open_rows), eol))

    # ---------- 3. heartbeat.txt (backfill + live) ---------------
    with open(P_HB, "rb") as fh:
        raw = fh.read()
    hb_text = raw.decode("utf-8")
    hb_eol = detect_eol(hb_text)
    hb_lines = hb_text.split(hb_eol)
    while hb_lines and hb_lines[-1] == "":
        hb_lines.pop()
    assert "tick 1900" in hb_text, "R1900 row missing"
    assert "tick 1901" not in hb_text, "backfill debt already paid"
    assert "tick 1902" not in hb_text, "live row already there"
    ts_now = _dt.datetime.now().astimezone().strftime(
        "%Y-%m-%dT%H:%M:%S+08:00")
    hb_lines.append("%s | BigDomain OSLoop alive | tick 1901 | %s"
                    % (ts_now, payload["hb_r1901_body"]))
    hb_lines.append("%s | BigDomain OSLoop alive | tick 1902 | %s"
                    % (ts_now, payload["hb_r1902_body"]))
    hb_out = hb_eol.join(hb_lines) + hb_eol
    with open(P_HB, "wb") as fh:
        fh.write(hb_out.encode("utf-8"))
    report.append("heartbeat.txt ok: +2 rows (R1901 backfill debt"
                  " cleared + R1902 live) eol=%r" % hb_eol)

    # ---------- 4. status-export.json flush ----------
    sys.path.insert(0, BASE)
    import check_export_consistency as cec
    derived, state_obj, export_obj, pat = cec.recompute()
    tick = state_obj["tick"]
    assert tick == 1902, "recompute saw stale tick: %s" % tick
    ex = payload
    export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
        timespec="seconds")
    export_obj["ceo_face"]["current"] = ex["ceo_current"]
    export_obj["ceo_face"]["latest_artifact"] = ex["ceo_artifact"]
    export_obj["ceo_face"]["next_milestone"] = ex["ceo_milestone"]
    sd = dict(derived)
    sd["method"] = ex["self_drive_method"]
    export_obj["self_drive"] = sd
    results = export_obj["results"]
    label = pat["tick_row_label"]
    tick_rows = [r for r in results if isinstance(r, list)
                 and len(r) >= 2 and r[1] == label]
    assert len(tick_rows) == 1, \
        "tick row expected exactly 1, got %d" % len(tick_rows)
    tick_rows[0][0] = str(tick)
    n_before = len(results)
    row = ex["result_row"]
    assert isinstance(row, list) and len(row) == 2, \
        "result row shape drift"
    results.insert(0, row)
    export_out = json.dumps(export_obj, indent=1,
                            ensure_ascii=False) + "\n"
    with open(P_EXPORT, "wb") as fh:
        fh.write(export_out.encode("utf-8"))
    report.append("export ok: +1 result row results=%d->%d"
                  " tick_row=%s self_drive W=%d sub=%d"
                  " queues=%d/%d/%d"
                  % (n_before, len(results), tick,
                     derived["log_lines_in_window"],
                     derived["substantive_non_idle_mention_lines"],
                     derived["queue_main_open"],
                     derived["queue_tech_open"],
                     derived["queue_explore_open"]))

    for line in report:
        print(line.encode("ascii", "backslashreplace")
              .decode("ascii"))
    print("closeout surgery complete: 4 faces ok")


if __name__ == "__main__":
    main()
