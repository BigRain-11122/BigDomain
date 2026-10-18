#!/usr/bin/env python3
"""R2033 closeout: state.json text-surgical append (tick/last_order/log),
heartbeat row append, status-export flush (ceo_face + results prepend +
tick-row sync + self_drive recompute via check_export_consistency).

Chinese round/heartbeat/export content lives in a UTF-8 data file OUTSIDE
the repo (temp); this script source stays pure ASCII (coding law, same
pattern as the funnel config.json data-file split). State surgery is
text-surgical on the canonical on-disk serialization (CRLF, 16-space log
items) - never a json.dumps whole-file rewrite (the R1991 disease).
"""
import datetime as _dt
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_export_consistency as cec  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(REPO, "src", "os", "state.json")
HEART = os.path.join(REPO, "heartbeat.txt")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
DATA = os.path.join(os.environ.get("TEMP", "."), "bd-r2033-closeout-data.json")

TICK_OLD = '"tick": 2032,'
TICK_NEW = '"tick": 2033,'
ORDER_OLD = '"last_order": "2026-10-18 23:46",'
ORDER_NEW = '"last_order": "2026-10-19 02:18",'
TAIL_ANCHOR = '"\r\n  ]\r\n}\r\n'
ITEM_INDENT = " " * 16


def fail(msg):
    raise SystemExit("FATAL: " + msg)


def main():
    with io.open(DATA, "r", encoding="utf-8") as f:
        d = json.load(f)
    for key in ("round_line", "tokens_line", "heartbeat_line",
                "export_current", "export_artifact", "export_milestone",
                "result_row"):
        if not d.get(key):
            fail("missing data key " + key)

    # --- 1. state.json text surgery ---
    with io.open(STATE, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    if TICK_OLD not in raw:
        fail("tick anchor missing")
    if ORDER_OLD not in raw:
        fail("last_order anchor missing")
    if not raw.endswith(TAIL_ANCHOR):
        fail("state tail anchor missing (layout drift)")
    raw = raw.replace(TICK_OLD, TICK_NEW, 1)
    raw = raw.replace(ORDER_OLD, ORDER_NEW, 1)
    esc_round = json.dumps(d["round_line"], ensure_ascii=False)
    esc_tokens = json.dumps(d["tokens_line"], ensure_ascii=False)
    body = raw[: -len(TAIL_ANCHOR)]
    body += '",\r\n' + ITEM_INDENT + esc_round
    body += ',\r\n' + ITEM_INDENT + esc_tokens
    body += '\r\n  ]\r\n}\r\n'
    try:
        json.loads(body)  # parse gate
    except json.JSONDecodeError as exc:
        print("PARSE-FAIL line=%s col=%s pos=%s total=%d"
              % (exc.lineno, exc.colno, exc.pos, len(body)))
        print("CONTEXT %r" % body[max(0, exc.pos - 120):exc.pos + 120])
        raise
    bare_lf = body.count("\n") - body.count("\r\n")
    if bare_lf:
        fail("bare LF would be written: %d" % bare_lf)
    if len(body.encode("utf-8")) > 78500:
        fail("state over waterline: %d" % len(body.encode("utf-8")))
    with io.open(STATE, "w", encoding="utf-8", newline="") as f:
        f.write(body)
    print("state: tick=2033 log+2 bytes=%d"
          % len(body.encode("utf-8")))

    # --- 2. heartbeat row append (detect newline convention) ---
    with io.open(HEART, "r", encoding="utf-8", newline="") as f:
        hb = f.read()
    nl = "\r\n" if "\r\n" in hb else "\n"
    if hb and not hb.endswith(("\n", "\r")):
        hb += nl
    stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M") + " +08:00"
    row = "%s | BigDomain OSLoop alive | tick 2033 | %s%s" % (
        stamp, d["heartbeat_line"], nl)
    with io.open(HEART, "a", encoding="utf-8", newline="") as f:
        f.write(row)
    print("heartbeat: tick 2033 row appended")

    # --- 3. export flush (same caliber as closeout_R2020) ---
    with io.open(EXPORT, "r", encoding="utf-8") as f:
        export = json.load(f)
    export["export_ts"] = _dt.datetime.now().astimezone().strftime(
        "%Y-%m-%dT%H:%M:%S+08:00")
    export["ceo_face"]["current"] = d["export_current"]
    export["ceo_face"]["latest_artifact"] = d["export_artifact"]
    export["ceo_face"]["next_milestone"] = d["export_milestone"]
    if not export["results"] or export["results"][0][0] != "R2033":
        export["results"].insert(0, ["R2033", d["result_row"]])
    with io.open(os.path.join(HERE, "export_consistency_patterns.json"),
                 "r", encoding="utf-8-sig") as f:
        tick_label = json.load(f)["tick_row_label"]
    hit = 0
    for row_ in export["results"]:
        if len(row_) >= 2 and row_[1] == tick_label:
            row_[0] = "2033"
            hit += 1
    if hit != 1:
        fail("tick row count=%d (expected 1)" % hit)
    derived, _state, _export, _pat = cec.recompute()
    sd = dict(derived)
    sd["method"] = export["self_drive"].get("method")
    export["self_drive"] = sd
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)
        f.write("\n")
    report, n_pass, n_fail = cec.check()
    print("\n".join(report[-4:]))
    print("CHECK n_pass=%d n_fail=%d" % (n_pass, n_fail))
    if n_fail:
        raise SystemExit(2)
    print("CLOSEOUT-OK tick=2033")


if __name__ == "__main__":
    main()
