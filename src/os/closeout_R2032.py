# closeout_R2032.py - byte-surgical closeout driver for round R2032
# (state.json tick + two log lines appended via literal text surgery,
# NOT a full json rewrite - the R1710/R1991 layout-drift disease is
# avoided by construction; export face refreshed in place; heartbeat
# row appended). CJK payloads live in closeout_lines_R2032.json
# (data file law); this source stays pure ASCII.
import datetime
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HB = os.path.join(ROOT, "heartbeat.txt")
LINES = os.path.join(HERE, "closeout_lines_R2032.json")


def _read(path):
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def main():
    data = json.loads(_read(LINES))
    round_line = data["round"]
    tokens_line = data["tokens"]

    # ---- state.json: tick bump + two-line surgical append ----
    text = _read(STATE)
    assert '"tick": 2031' in text, "tick anchor missing"
    text = text.replace('"tick": 2031', '"tick": 2032', 1)
    m = re.search(
        r'(?m)^([ \t]*)("2026-10-19 R2032 [^"]*")[ \t]*\r?\n([ \t]*)\]',
        text,
    )
    assert m, "state log tail pattern not found"
    assert "fold R562" in m.group(2), "tail is not the fold rolling line"
    indent = m.group(1)
    keep = m.group(2)
    built = (
        keep
        + ",\n"
        + indent + json.dumps(round_line, ensure_ascii=False)
        + ",\n"
        + indent + json.dumps(tokens_line, ensure_ascii=False)
        + "\n" + m.group(3) + "]"
    )
    text = text[: m.start(2)] + built + text[m.end():]
    st = json.loads(text)
    assert st["tick"] == 2032, "tick bump failed"
    assert len(st["log"]) == 19, "log item count %d" % len(st["log"])
    assert st["log"][-1] == tokens_line, "tokens tail mismatch"
    assert st["log"][-2] == round_line, "round tail mismatch"
    _write(STATE, text)
    sz = os.path.getsize(STATE)
    assert sz < 78500, "state over the fold line: %d" % sz
    print("STATE ok bytes=%d tick=2032 log=%d" % (sz, len(st["log"])))

    # ---- export face: ts + ceo_face trio + results insert +
    # self_drive counters ----
    etext = _read(EXPORT)
    now = datetime.datetime.now().astimezone()
    ts = now.isoformat(timespec="seconds")
    etext = re.sub(r'"export_ts": "[^"]*"',
                   '"export_ts": "%s"' % ts, etext, count=1)
    etext = re.sub(r'"current": "[^"]*"',
                   '"current": %s'
                   % json.dumps(data["ceo_current"], ensure_ascii=False),
                   etext, count=1)
    etext = re.sub(r'"latest_artifact": "[^"]*"',
                   '"latest_artifact": %s'
                   % json.dumps(data["ceo_latest"], ensure_ascii=False),
                   etext, count=1)
    etext = re.sub(r'"next_milestone": "[^"]*"',
                   '"next_milestone": %s'
                   % json.dumps(data["ceo_next"], ensure_ascii=False),
                   etext, count=1)
    rm = re.search(r'(?m)^([ \t]*)"results": \[\r?\n', etext)
    assert rm, "results anchor missing"
    ins = (
        '  [\n    "R2032",\n    '
        + json.dumps(data["result"], ensure_ascii=False)
        + "\n  ],\n"
    )
    etext = etext[: rm.end()] + ins + etext[rm.end():]
    etext = etext.replace('"log_lines_in_window": 10',
                          '"log_lines_in_window": 12', 1)
    etext = etext.replace('"substantive_non_idle_mention_lines": 1',
                          '"substantive_non_idle_mention_lines": 2', 1)
    ex = json.loads(etext)
    assert ex["results"][0][0] == "R2032", "results head mismatch"
    assert ex["self_drive"]["log_lines_in_window"] == 12
    _write(EXPORT, etext)
    print("EXPORT ok ts=%s results-head=R2032" % ts)

    # ---- heartbeat row ----
    hb = _read(HB)
    stamp = now.strftime("%Y-%m-%d %H:%M") + " +08:00"
    row = ("%s | BigDomain OSLoop alive | tick 2032 | %s\n"
           % (stamp, data["heartbeat"]))
    if not hb.endswith("\n"):
        hb += "\n"
    _write(HB, hb + row)
    print("HEARTBEAT ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
