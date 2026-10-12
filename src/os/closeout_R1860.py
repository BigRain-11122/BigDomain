"""R1860 closeout surgery (five faces, all fail-closed, zero
json.dump full-file rewrite of state.json - R1710 discipline; byte
surgery per state_closeout_R1847.py / closeout_R1858.py precedent):
  1. state/queue/tech.md  : flip claim checkbox + append done note +
     reseed at FIFO tail
  2. src/os/state.json    : tick 1859->1860, gord baseline 283->285,
     +2 log lines
  3. heartbeat.txt        : +1 R1860 row (live ts stamp)
  4. docs/status-export.json : flush via check_export_consistency
     .recompute() single-source caliber (AC-EC2), +1 result row,
     tick row -> 1860, ceo_face three rows, export_ts now
Chinese payload lives in closeout_payload_R1860.json (encoding law).
Pure stdlib, zero network, pure ASCII source."""

import datetime as _dt
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_PAYLOAD = os.path.join(BASE, "closeout_payload_R1860.json")
P_STATE = os.path.join(BASE, "state.json")
P_TECH = os.path.join(ROOT, "state", "queue", "tech.md")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")


def detect_eol(text):
    return "\r\n" if "\r\n" in text else "\n"


def main():
    with open(P_PAYLOAD, encoding="utf-8") as fh:
        payload = json.load(fh)
    report = []

    # ---------- 1. tech.md ----------
    with open(P_TECH, "rb") as fh:
        raw = fh.read()
    tech_text = raw.decode("utf-8")
    eol = detect_eol(tech_text)
    tech_lines = tech_text.split(eol)
    prefix = payload["tech"]["claim_prefix"]
    hits = [i for i, l in enumerate(tech_lines) if l.startswith(prefix)]
    assert len(hits) == 1, "tech claim line expected 1 hit, got %d" % len(hits)
    idx = hits[0]
    assert tech_lines[idx].startswith("- [ ] "), \
        "claim line not open-checkbox state"
    assert "R1860 " in tech_lines[idx], \
        "claim note missing (pre-registration must precede closeout)"
    tech_lines[idx] = "- [x] " + tech_lines[idx][len("- [ ] "):] \
        + payload["tech"]["done_note"]
    reseed = payload["tech"]["reseed_line"]
    assert reseed.startswith("- [ ] "), "reseed line must be open-checkbox"
    assert reseed not in tech_text, "reseed line already present (dup)"
    while tech_lines and tech_lines[-1] == "":
        tech_lines.pop()
    tech_lines.append(reseed)
    tech_out = eol.join(tech_lines) + eol
    with open(P_TECH, "wb") as fh:
        fh.write(tech_out.encode("utf-8"))
    open_after = sum(1 for l in tech_lines if l.startswith("- [ ] "))
    report.append("tech.md ok: claim flipped + done note, reseed "
                  "appended; open=%d eol=%r" % (open_after, eol))

    # ---------- 2. state.json (CRLF byte surgery) ----------
    with open(P_STATE, "rb") as fh:
        raw = fh.read()
    assert raw[:3] != b"\xef\xbb\xbf", "unexpected BOM in state.json"
    text = raw.decode("utf-8")
    assert text.count("\n") == text.count("\r\n"), "bare LF in state.json"
    lines = text.split("\r\n")

    def replace_once(old, new):
        hits = [i for i, l in enumerate(lines) if old in l]
        assert len(hits) == 1, \
            "field %r expected 1 hit, got %d" % (old, len(hits))
        lines[hits[0]] = lines[hits[0]].replace(old, new)

    replace_once('"tick": 1859,', '"tick": 1860,')
    replace_once('"last_gord_tbl_rows": 283,',
                 '"last_gord_tbl_rows": %d,'
                 % payload["baselines"]["last_gord_tbl_rows"])

    tick_idx = [i for i, l in enumerate(lines) if '"tick": 1860,' in l]
    assert len(tick_idx) == 1, "tick line not found after bump"
    close_idx = None
    for i in range(tick_idx[0] + 1, len(lines)):
        if lines[i].strip() == "]":
            close_idx = i
            break
    assert close_idx is not None, "log array close not found"
    last_item = lines[close_idx - 1]
    assert last_item.startswith(" " * 16), "log item indent drift"
    stripped_last = last_item.rstrip()
    assert stripped_last.endswith('"') \
        and not stripped_last.endswith(","), "last log item layout drift"
    lines[close_idx - 1] = stripped_last + ","
    new_lines = payload["log_lines"]
    assert len(new_lines) == 2, "expected exactly 2 new log lines"
    items = []
    for i, l in enumerate(new_lines):
        item = " " * 16 + json.dumps(l, ensure_ascii=False)
        assert "\r" not in item and "\n" not in item, \
            "embedded newline in log item"
        items.append(item + ("," if i < len(new_lines) - 1 else ""))
    lines[close_idx:close_idx] = items

    out_text = "\r\n".join(lines)
    obj = json.loads(out_text)
    assert obj["tick"] == 1860, "tick not 1860 after surgery"
    assert len(obj["log"]) == 17, \
        "expected 17 log items after append, got %d" % len(obj["log"])
    assert obj["log"][-2].startswith("2026-10-12 R1860 "), \
        "round line prefix drift"
    assert obj["log"][-1].startswith("2026-10-12 R1860 tokens: "), \
        "tokens line prefix drift"
    assert obj["last_gord_tbl_rows"] == 285, "gord baseline drift"
    assert "O-20261012-1130" in obj["log"][-2] \
        and "O-20261012-1135" in obj["log"][-2], \
        "GORD ack full-number reference missing (delivery law)"
    with open(P_STATE, "wb") as fh:
        fh.write(out_text.encode("utf-8"))
    report.append("state.json ok: tick=1860 log_items=17 bytes=%d "
                  "gord=285" % len(out_text.encode("utf-8")))

    # ---------- 3. heartbeat.txt ----------
    with open(P_HB, "rb") as fh:
        raw = fh.read()
    hb_text = raw.decode("utf-8")
    hb_eol = detect_eol(hb_text)
    hb_lines = hb_text.split(hb_eol)
    while hb_lines and hb_lines[-1] == "":
        hb_lines.pop()
    ts = _dt.datetime.now().astimezone().strftime(
        "%Y-%m-%d %H:%M") + " +08:00"
    body = "%s | BigDomain OSLoop alive | tick 1860 | %s" \
        % (ts, payload["hb_body"])
    assert "tick 1860" not in hb_text, "hb row already present (dup)"
    hb_lines.append(body)
    hb_out = hb_eol.join(hb_lines) + hb_eol
    with open(P_HB, "wb") as fh:
        fh.write(hb_out.encode("utf-8"))
    report.append("heartbeat.txt ok: +1 row (R1860) eol=%r" % hb_eol)

    # ---------- 4. status-export.json flush ----------
    sys.path.insert(0, BASE)
    import check_export_consistency as cec
    derived, state_obj, export_obj, pat = cec.recompute()
    tick = state_obj["tick"]
    assert tick == 1860, "recompute saw stale tick: %s" % tick
    ex = payload["export"]
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
    assert isinstance(row, list) and len(row) == 2, "result row shape drift"
    results.insert(0, row)
    export_out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
    with open(P_EXPORT, "wb") as fh:
        fh.write(export_out.encode("utf-8"))
    report.append("export ok: +1 result row results=%d->%d tick_row=%s "
                  "self_drive W=%d sub=%d queues=%d/%d/%d"
                  % (n_before, len(results), tick,
                     derived["log_lines_in_window"],
                     derived["substantive_non_idle_mention_lines"],
                     derived["queue_main_open"],
                     derived["queue_tech_open"],
                     derived["queue_explore_open"]))

    for line in report:
        print(line)
    print("closeout surgery complete: 4 faces ok")


if __name__ == "__main__":
    main()
