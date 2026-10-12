"""R1858 interrupted-round closeout surgery (adopted by successor session).

Four faces, all fail-closed, zero json.dump full-file rewrite of state.json
(R1710 discipline; byte surgery per state_closeout_R1847.py precedent):
  1. state/queue/tech.md  : flip claim checkbox + append done note + reseed
  2. src/os/state.json    : tick 1857->1858, baselines, +2 log lines
  3. heartbeat.txt        : R1857 backfill row (HB lag=1 debt) + R1858 row
  4. docs/status-export.json : flush via check_export_consistency.recompute()
     single-source caliber (AC-EC2), results backfill R1856/R1857/R1858,
     tick row -> 1858, ceo_face three rows, export_ts now.
Chinese payload lives in state_payload_R1858.json (encoding law).
Pure stdlib, zero network, pure ASCII source.
"""

import datetime as _dt
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_PAYLOAD = os.path.join(BASE, "state_payload_R1858.json")
P_STATE = os.path.join(BASE, "state.json")
P_TECH = os.path.join(ROOT, "state", "queue", "tech.md")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_CHECKER = BASE  # for importing check_export_consistency


def detect_eol(text):
    if "\r\n" in text:
        return "\r\n"
    return "\n"


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
    line = tech_lines[idx]
    assert line.startswith("- [ ] "), "claim line not open-checkbox state"
    tech_lines[idx] = "- [x] " + line[len("- [ ] "):] + payload["tech"]["done_note"]
    reseed = payload["tech"]["reseed_line"]
    assert reseed.startswith("- [ ] "), "reseed line must be open-checkbox"
    assert reseed not in tech_text, "reseed line already present (dup)"
    # append reseed at file end (FIFO tail convention, R1857 reseed precedent)
    while tech_lines and tech_lines[-1] == "":
        tech_lines.pop()
    tech_lines.append(reseed)
    tech_out = eol.join(tech_lines) + eol
    with open(P_TECH, "wb") as fh:
        fh.write(tech_out.encode("utf-8"))
    open_after = sum(1 for l in tech_lines if l.startswith("- [ ] "))
    done_after = sum(1 for l in tech_lines if l.startswith("- [x] "))
    report.append("tech.md ok: claim flipped + done note, reseed appended; "
                  "open=%d done=%d eol=%r" % (open_after, done_after, eol))

    # ---------- 2. state.json (CRLF byte surgery) ----------
    with open(P_STATE, "rb") as fh:
        raw = fh.read()
    assert raw[:3] != b"\xef\xbb\xbf", "unexpected BOM in state.json"
    text = raw.decode("utf-8")
    assert text.count("\n") == text.count("\r\n"), "bare LF present in state.json"
    lines = text.split("\r\n")

    def replace_once(old, new):
        hits = [i for i, l in enumerate(lines) if old in l]
        assert len(hits) == 1, "state.json field %r expected 1 hit, got %d" % (old, len(hits))
        lines[hits[0]] = lines[hits[0]].replace(old, new)

    replace_once('"tick": 1857,', '"tick": 1858,')
    replace_once('"last_decision_rows": 288,',
                 '"last_decision_rows": %d,' % payload["baselines"]["last_decision_rows"])
    replace_once('"last_gord_tbl_rows": 278,',
                 '"last_gord_tbl_rows": %d,' % payload["baselines"]["last_gord_tbl_rows"])
    tok_hits = [i for i, l in enumerate(lines) if '"last_dec_tokens"' in l]
    assert len(tok_hits) == 1, "last_dec_tokens line expected 1 hit"
    t = tok_hits[0]
    stripped = lines[t].rstrip()
    assert stripped.endswith('",'), "last_dec_tokens value layout drift"
    lines[t] = stripped[:-2] + ",%s\"," % payload["baselines"]["dec_token_add"]

    tick_idx = [i for i, l in enumerate(lines) if '"tick": 1858,' in l]
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
    assert stripped_last.endswith('"') and not stripped_last.endswith(","), \
        "last log item layout drift"
    lines[close_idx - 1] = stripped_last + ","
    new_lines = payload["log_lines"]
    assert len(new_lines) == 2, "expected exactly 2 new log lines"
    items = []
    for i, l in enumerate(new_lines):
        item = " " * 16 + json.dumps(l, ensure_ascii=False)
        assert "\r" not in item and "\n" not in item, "embedded newline in log item"
        items.append(item + ("," if i < len(new_lines) - 1 else ""))
    lines[close_idx:close_idx] = items

    out_text = "\r\n".join(lines)
    obj = json.loads(out_text)
    assert obj["tick"] == 1858, "tick not 1858 after surgery"
    assert len(obj["log"]) == 13, "expected 13 log items after append, got %d" % len(obj["log"])
    assert obj["log"][-2].startswith("2026-10-12 R1858 "), "round line prefix drift"
    assert obj["log"][-1].startswith("2026-10-12 R1858 tokens: "), "tokens line prefix drift"
    assert obj["log"][-1] == new_lines[1], "tokens line payload drift"
    assert "C-20261012-01" in obj["last_dec_tokens"], "dec token not merged"
    with open(P_STATE, "wb") as fh:
        fh.write(out_text.encode("utf-8"))
    report.append("state.json ok: tick=1858 log_items=13 bytes=%d dec_token=merged"
                  % len(out_text.encode("utf-8")))

    # ---------- 3. heartbeat.txt ----------
    with open(P_HB, "rb") as fh:
        raw = fh.read()
    hb_text = raw.decode("utf-8")
    hb_eol = detect_eol(hb_text)
    hb_lines = hb_text.split(hb_eol)
    while hb_lines and hb_lines[-1] == "":
        hb_lines.pop()
    hb_rows = payload["hb_rows"]
    assert len(hb_rows) == 2, "expected 2 hb rows"
    ticks = [1857, 1858]
    for row, tick in zip(hb_rows, ticks):
        body = "%s | BigDomain OSLoop alive | tick %d | %s" % (row["ts"], tick, row["body"])
        assert body not in hb_text, "hb row already present (dup)"
        hb_lines.append(body)
    hb_out = hb_eol.join(hb_lines) + hb_eol
    with open(P_HB, "wb") as fh:
        fh.write(hb_out.encode("utf-8"))
    report.append("heartbeat.txt ok: +2 rows (R1857 backfill + R1858) eol=%r" % hb_eol)

    # ---------- 4. status-export.json flush (single-source caliber) ----------
    sys.path.insert(0, P_CHECKER)
    import check_export_consistency as cec
    derived, state_obj, export_obj, pat = cec.recompute()
    tick = state_obj["tick"]
    assert tick == 1858, "recompute saw stale tick: %s" % tick
    ex = payload["export"]
    export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
    export_obj["ceo_face"]["current"] = ex["ceo_current"]
    export_obj["ceo_face"]["latest_artifact"] = ex["ceo_artifact"]
    export_obj["ceo_face"]["next_milestone"] = ex["ceo_milestone"]
    sd = dict(derived)
    sd["method"] = ex["self_drive_method"]
    export_obj["self_drive"] = sd
    results = export_obj["results"]
    label = pat["tick_row_label"]
    tick_rows = [r for r in results if isinstance(r, list) and len(r) >= 2 and r[1] == label]
    assert len(tick_rows) == 1, "tick row expected exactly 1, got %d" % len(tick_rows)
    tick_rows[0][0] = str(tick)
    n_before = len(results)
    for row in ex["result_rows"]:
        assert isinstance(row, list) and len(row) == 2, "result row shape drift"
        results.insert(0, row)
    export_out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
    with open(P_EXPORT, "wb") as fh:
        fh.write(export_out.encode("utf-8"))
    report.append("export ok: +3 result rows (R1858/R1857/R1856 backfill) "
                  "results=%d->%d tick_row=%s self_drive W=%d sub=%d "
                  "queues=%d/%d/%d"
                  % (n_before, len(results), tick, derived["log_lines_in_window"],
                     derived["substantive_non_idle_mention_lines"],
                     derived["queue_main_open"], derived["queue_tech_open"],
                     derived["queue_explore_open"]))

    for line in report:
        print(line)
    print("closeout surgery complete: 4 faces ok")


if __name__ == "__main__":
    main()
