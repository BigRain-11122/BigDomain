"""R1880 closeout surgery (byte surgery per closeout_R1878
precedent; zero json.dump full-file rewrite of state.json -
the R1710 discipline). The tech.md face was applied earlier
this round via the editing tool (claim -> done note + successor
reseed), so this closeout only VERIFIES it; the other three
faces mutate:
  2. src/os/state.json    : tick 1879->1880,
     last_gord_tbl_rows 314->324 (ten new group-order rows,
     all other-company faces), +2 log lines
  3. heartbeat.txt        : +1 R1880 row (live ts stamp)
  4. docs/status-export.json : flush via check_export_consistency
     .recompute() single-source caliber (AC-EC2), +1 result row,
     tick row -> 1880, ceo_face three rows, export_ts now
Chinese payload lives in closeout_payload_R1880.json (encoding
law). Pure stdlib, zero network, pure ASCII source."""

import datetime as _dt
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_PAYLOAD = os.path.join(BASE, "closeout_payload_R1880.json")
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

    # ---------- 1. tech.md verify (applied earlier this round) --
    with open(P_TECH, "rb") as fh:
        tech_text = fh.read().decode("utf-8")
    eol = detect_eol(tech_text)
    tech_lines = tech_text.split(eol)
    tv = payload["tech_verify"]
    claim_hits = [l for l in tech_lines
                  if l.startswith(tv["claim_prefix"])]
    assert len(claim_hits) == 1, \
        "tech claim row expected 1 hit, got %d" % len(claim_hits)
    assert tv["done_marker"] in claim_hits[0], \
        "done note missing from claim row"
    for ref in tv["criteria_refs"]:
        assert ref in claim_hits[0], \
            "pre-registered criteria ref missing: %s" % ref
    open_count = sum(1 for l in tech_lines
                     if l.startswith("- [ ] "))
    assert open_count == tv["open_expected"], \
        "queue_tech_open expected %d, got %d" \
        % (tv["open_expected"], open_count)
    reseed_hits = [l for l in tech_lines
                   if l.startswith(tv["reseed_prefix"])]
    assert len(reseed_hits) == 1, \
        "successor reseed row expected 1, got %d" % len(reseed_hits)
    report.append("tech.md verified: claim flipped + done note"
                  " + reseed present; open=%d eol=%r"
                  % (open_count, eol))

    # ---------- 2. state.json (CRLF byte surgery) ----------
    with open(P_STATE, "rb") as fh:
        raw = fh.read()
    assert raw[:3] != b"\xef\xbb\xbf", "unexpected BOM in state.json"
    text = raw.decode("utf-8")
    assert text.count("\n") == text.count("\r\n"), \
        "bare LF in state.json"
    lines = text.split("\r\n")

    def replace_once(old, new):
        hits2 = [i for i, l in enumerate(lines) if old in l]
        assert len(hits2) == 1, \
            "field %r expected 1 hit, got %d" % (old, len(hits2))
        lines[hits2[0]] = lines[hits2[0]].replace(old, new)

    replace_once('"tick": 1879,', '"tick": 1880,')
    replace_once('"last_gord_tbl_rows": 314,',
                 '"last_gord_tbl_rows": 324,')

    tick_idx = [i for i, l in enumerate(lines) if '"tick": 1880,' in l]
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
        and not stripped_last.endswith(","), \
        "last log item layout drift"
    assert "R1879 tokens" in stripped_last, \
        "expected R1879 tokens as the pre-surgery tail"
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
    assert obj["tick"] == 1880, "tick not 1880 after surgery"
    assert obj["last_gord_tbl_rows"] == 324, "gord baseline drift"
    assert obj["log"][-2].startswith("2026-10-12 R1880 "), \
        "round line prefix drift"
    assert obj["log"][-1].startswith(
        "2026-10-12 R1880 tokens: "), \
        "tokens line prefix drift"
    assert "AC-CVR8..CVR14" in obj["log"][-2], \
        "pre-registration reference missing from round line"
    assert "R1874" in obj["log"][-2], \
        "seed reference missing from round line"
    with open(P_STATE, "wb") as fh:
        fh.write(out_text.encode("utf-8"))
    report.append("state.json ok: tick=1880 log_items=%d bytes=%d"
                  " gord=324"
                  % (len(obj["log"]),
                     len(out_text.encode("utf-8"))))

    # ---------- 3. heartbeat.txt ----------
    with open(P_HB, "rb") as fh:
        raw = fh.read()
    hb_text = raw.decode("utf-8")
    hb_eol = detect_eol(hb_text)
    hb_lines = hb_text.split(hb_eol)
    while hb_lines and hb_lines[-1] == "":
        hb_lines.pop()
    ts = _dt.datetime.now().astimezone().strftime(
        "%Y-%m-%dT%H:%M:%S+08:00")
    body = "%s | BigDomain OSLoop alive | tick 1880 | %s" \
        % (ts, payload["hb_body"])
    assert "tick 1880" not in hb_text, "hb row already present (dup)"
    hb_lines.append(body)
    hb_out = hb_eol.join(hb_lines) + hb_eol
    with open(P_HB, "wb") as fh:
        fh.write(hb_out.encode("utf-8"))
    report.append("heartbeat.txt ok: +1 row (R1880) eol=%r" % hb_eol)

    # ---------- 4. status-export.json flush ----------
    sys.path.insert(0, BASE)
    import check_export_consistency as cec
    derived, state_obj, export_obj, pat = cec.recompute()
    tick = state_obj["tick"]
    assert tick == 1880, "recompute saw stale tick: %s" % tick
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
    assert isinstance(row, list) and len(row) == 2, \
        "result row shape drift"
    results.insert(0, row)
    export_out = json.dumps(export_obj, indent=1,
                            ensure_ascii=False) + "\n"
    with open(P_EXPORT, "wb") as fh:
        fh.write(export_out.encode("utf-8"))
    report.append("export ok: +1 result row results=%d->%d tick_row=%s"
                  " self_drive W=%d sub=%d queues=%d/%d/%d"
                  % (n_before, len(results), tick,
                     derived["log_lines_in_window"],
                     derived["substantive_non_idle_mention_lines"],
                     derived["queue_main_open"],
                     derived["queue_tech_open"],
                     derived["queue_explore_open"]))

    for line in report:
        print(line)
    print("closeout surgery complete: 3 faces ok")


if __name__ == "__main__":
    main()
