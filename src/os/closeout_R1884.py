"""R1884 closeout surgery (byte surgery per closeout_R1883
precedent; zero json.dump full-file rewrite of state.json - the
R1710 discipline). Mutating faces:
  1. state/queue/tech.md  : claim row [ ]->[x] with done note,
     +1 reseed row (authorize persistence seed)
  2. src/os/state.json    : tick 1883->1884,
     last_decision_rows 301->308, benchmarks_refreshed ->10-13,
     last_dec_tokens +2 (D-20261013-01/02), +2 log lines
  3. heartbeat.txt        : +1 R1884 row
  4. docs/status-export.json : flush via check_export_consistency
     .recompute() single-source caliber (AC-EC2), +1 result row,
     tick row -> 1884, ceo_face three rows, export_ts now
Chinese payload lives in closeout_payload_R1884.json (encoding
law). Pure stdlib, zero network, pure ASCII source."""

import datetime as _dt
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_PAYLOAD = os.path.join(BASE, "closeout_payload_R1884.json")
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

    # ---------- 1. tech.md: flip claim + reseed ----------
    with open(P_TECH, "rb") as fh:
        tech_text = fh.read().decode("utf-8")
    eol = detect_eol(tech_text)
    tf = payload["tech_flip"]
    claim_prefix = tf["claim_prefix"]
    old_tail = tf["done_note"]
    new_tail = tf["done_tail"]
    hits = [l for l in tech_text.split(eol)
            if l.startswith(claim_prefix)]
    assert len(hits) == 1, \
        "claim row expected 1 hit, got %d" % len(hits)
    assert old_tail in hits[0], "claim tail anchor mismatch"
    for ref in tf["criteria_refs"]:
        assert ref in hits[0], "criteria ref missing: %s" % ref
    flipped = hits[0].replace("- [ ] ", "- [x] ", 1)
    flipped = flipped.replace(old_tail, new_tail, 1)
    assert tf["done_marker"] in flipped, "done marker missing"
    tech_text = tech_text.replace(hits[0], flipped, 1)
    reseed = payload["reseed_row"]
    assert tf["reseed_prefix"] not in tech_text, "reseed dup"
    lines = tech_text.split(eol)
    idx = [i for i, l in enumerate(lines)
           if l.startswith(flipped[:60])][0]
    lines.insert(idx + 1, reseed)
    tech_out = eol.join(lines)
    if not tech_out.endswith(eol):
        tech_out += eol
    with open(P_TECH, "wb") as fh:
        fh.write(tech_out.encode("utf-8"))
    open_count = sum(1 for l in tech_out.split(eol)
                     if l.startswith("- [ ] "))
    report.append("tech.md ok: claim flipped + done note + "
                  "reseed added; open now %d" % open_count)

    # ---------- 2. state.json (CRLF byte surgery) ----------
    with open(P_STATE, "rb") as fh:
        raw = fh.read()
    assert raw[:3] != b"\xef\xbb\xbf", "unexpected BOM"
    text = raw.decode("utf-8")
    assert text.count("\n") == text.count("\r\n"), "bare LF"
    lines = text.split("\r\n")

    def replace_once(old, new):
        h = [i for i, l in enumerate(lines) if old in l]
        assert len(h) == 1, "field %r hits=%d" % (old, len(h))
        lines[h[0]] = lines[h[0]].replace(old, new)

    replace_once('"tick": 1883,', '"tick": 1884,')
    replace_once('"last_decision_rows": 301,',
                '"last_decision_rows": 308,')
    replace_once('"benchmarks_refreshed": "2026-10-12",',
                '"benchmarks_refreshed": "2026-10-13",')

    # last_dec_tokens: append the two adjudicated tokens
    tok_idx = [i for i, l in enumerate(lines)
               if '"last_dec_tokens": "' in l]
    assert len(tok_idx) == 1, "dec token line hits=%d" % len(tok_idx)
    tok_line = lines[tok_idx[0]]
    assert tok_line.rstrip().endswith('",'), \
        "dec token tail layout drift"
    for probe in ("D-20261013-01", "D-20261013-02"):
        assert probe not in tok_line, "token dup: " + probe
    tail = tok_line.rstrip()
    assert tail.endswith('",'), "dec token tail layout drift"
    lines[tok_idx[0]] = tail[:-2] + ",D-20261013-01,D-20261013-02\","

    tick_idx = [i for i, l in enumerate(lines)
                if '"tick": 1884,' in l]
    assert len(tick_idx) == 1, "tick line not found"
    close_idx = None
    for i in range(tick_idx[0] + 1, len(lines)):
        if lines[i].strip() == "]":
            close_idx = i
            break
    assert close_idx is not None, "log close not found"
    last_item = lines[close_idx - 1]
    assert last_item.startswith(" " * 16), "indent drift"
    stripped = last_item.rstrip()
    assert stripped.endswith('"') \
        and not stripped.endswith(","), "tail layout drift"
    assert "R1883 tokens" in stripped, \
        "expected R1883 tokens as pre-surgery tail"
    lines[close_idx - 1] = stripped + ","
    new_lines = payload["log_lines"]
    assert len(new_lines) == 2, "expected 2 log lines"
    items = []
    for i, l in enumerate(new_lines):
        item = " " * 16 + json.dumps(l, ensure_ascii=False)
        assert "\r" not in item and "\n" not in item
        items.append(item + ("," if i < len(new_lines) - 1 else ""))
    lines[close_idx:close_idx] = items

    out_text = "\r\n".join(lines)
    obj = json.loads(out_text)
    assert obj["tick"] == 1884, "tick not 1884"
    assert obj["last_gord_tbl_rows"] == 332, "gord drift"
    assert obj["last_decision_rows"] == 308, "dec rows drift"
    assert obj["benchmarks_refreshed"] == "2026-10-13", \
        "bench date drift"
    assert "D-20261013-01" in obj["last_dec_tokens"] \
        and "D-20261013-02" in obj["last_dec_tokens"], \
        "dec tokens not in"
    assert obj["log"][-2].startswith("2026-10-13 R1884 "), \
        "round line prefix drift"
    assert obj["log"][-1].startswith(
        "2026-10-13 R1884 tokens: "), "tokens prefix drift"
    assert "AC-PN30" in obj["log"][-2], "criteria ref missing"
    assert "W23" in obj["log"][-2], "crawl ref missing"
    with open(P_STATE, "wb") as fh:
        fh.write(out_text.encode("utf-8"))
    report.append("state.json ok: tick=1884 log=%d bytes=%d"
                  % (len(obj["log"]),
                     len(out_text.encode("utf-8"))))

    # ---------- 3. heartbeat.txt ----------
    with open(P_HB, "rb") as fh:
        hb_text = fh.read().decode("utf-8")
    hb_eol = detect_eol(hb_text)
    hb_lines = hb_text.split(hb_eol)
    while hb_lines and hb_lines[-1] == "":
        hb_lines.pop()
    ts = _dt.datetime.now().astimezone().strftime(
        "%Y-%m-%dT%H:%M:%S+08:00")
    body = "%s | BigDomain OSLoop alive | tick 1884 | %s" \
        % (ts, payload["hb_body"])
    assert "tick 1884" not in hb_text, "hb dup"
    hb_lines.append(body)
    with open(P_HB, "wb") as fh:
        fh.write((hb_eol.join(hb_lines) + hb_eol)
                 .encode("utf-8"))
    report.append("heartbeat.txt ok: +1 row (R1884)")

    # ---------- 4. status-export.json flush ----------
    sys.path.insert(0, BASE)
    import check_export_consistency as cec
    derived, state_obj, export_obj, pat = cec.recompute()
    tick = state_obj["tick"]
    assert tick == 1884, "recompute stale tick: %s" % tick
    ex = payload["export"]
    export_obj["export_ts"] = _dt.datetime.now().astimezone(
    ).isoformat(timespec="seconds")
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
    assert len(tick_rows) == 1, "tick row not exactly 1"
    tick_rows[0][0] = str(tick)
    n_before = len(results)
    row = ex["result_row"]
    results.insert(0, row)
    with open(P_EXPORT, "wb") as fh:
        fh.write((json.dumps(export_obj, indent=1,
                             ensure_ascii=False) + "\n")
                 .encode("utf-8"))
    report.append("export ok: results %d->%d tick_row=%s"
                  " queues main/tech/explore=%d/%d/%d"
                  % (n_before, len(results), tick,
                     derived["queue_main_open"],
                     derived["queue_tech_open"],
                     derived["queue_explore_open"]))

    for line in report:
        print(line)
    print("closeout surgery complete: 4 faces ok")


if __name__ == "__main__":
    main()
