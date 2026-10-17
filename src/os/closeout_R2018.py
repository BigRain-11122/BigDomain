# closeout_R2018.py - R2018 (35th-case takeover closeout)
# driver: (1) state.json byte surgery (tick 2017 -> 2018,
# two-line log append via ps_escape; baselines unchanged:
# last_order 13:5x / DEC 356 / GORD 455 all held flat this
# round), (2) heartbeat.txt row (scan [HB] law: 'tick N'
# segment per R532, R2017 surgery precedent), (3)
# state/queue/explore.md done-flip + done note + consume-1
# reseed-1 conservation, (4) status-export.json refresh
# (ceo_face + results R2018 row prepend + tick row 2018 +
# self_drive recompute). ASCII script logic; CJK content
# lives in closeout_payload_R2018.json (data file law).
import io
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_QUEUE = os.path.join(ROOT, "state", "queue", "explore.md")
P_PAYLOAD = os.path.join(HERE, "closeout_payload_R2018.json")

with io.open(P_PAYLOAD, encoding="utf-8") as fh:
    payload = json.load(fh)

ROUND_LINE = payload["round_line"]
TOKENS_LINE = payload["tokens_line"]
HB_BODY = payload["hb_body"]
CEO_CURRENT = payload["ceo_current"]
CEO_LATEST = payload["ceo_latest"]
CEO_NEXT = payload["ceo_next"]
RESULTS_ROW = payload["results_row"]
QUEUE_FLIP_OLD = payload["queue_flip_old"]
QUEUE_END_ANCHOR = payload["queue_end_anchor"]
QUEUE_DONE_NOTE = payload["queue_done_note"]
QUEUE_RESEED = payload["queue_reseed"]


def die(msg):
    print("ABORT: %s" % msg)
    sys.exit(2)


def main():
    # ---------- 1. state.json byte surgery ----------------------
    raw = open(P_STATE, "rb").read()
    text = raw.decode("utf-8")
    if text.count('"tick": 2017,') != 1:
        die("tick anchor not unique")
    text = text.replace('"tick": 2017,', '"tick": 2018,')
    tail = '"\r\n  ]\r\n}\r\n'
    if not text.endswith(tail):
        die("state tail layout unexpected")
    import logs_toolkit as LT                     # noqa: E402
    lit1 = " " * 16 + LT.ps_escape(ROUND_LINE)
    lit2 = " " * 16 + LT.ps_escape(TOKENS_LINE)
    text = (text[:-len(tail)] + '",\r\n' + lit1 + ',\r\n' + lit2
            + '\r\n  ]\r\n}\r\n')
    new_bytes = text.encode("utf-8")
    if len(new_bytes) >= 78500:
        die("state over the line: %d" % len(new_bytes))
    st = json.loads(text)
    if st["tick"] != 2018 or len(st["log"]) != 19:
        die("tick/log shape wrong: %s %d" % (st["tick"],
                                             len(st["log"])))
    if not st["log"][-2].startswith(u"2026-10-17 R2018"):
        die("round line missing")
    if not st["log"][-1].startswith("R2018 tokens:"):
        die("tokens line missing")
    if st["log"][-3].find(u"fold R548") < 0:
        die("fold rolling line missing")
    open(P_STATE, "wb").write(new_bytes)
    print("state.json OK: tick=2018 log-items=19 bytes=%d"
          % len(new_bytes))

    # ---------- 2. heartbeat.txt -------------------------------
    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")[:-1] + "x +08:00"
    row = (stamp + " | BigDomain OSLoop alive | tick 2018 | "
           + HB_BODY)
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + row + "\r\n")
    print("heartbeat.txt OK: R2018 row appended (tick 2018)")

    # ---------- 3. state/queue/explore.md ----------------------
    q = io.open(P_QUEUE, encoding="utf-8", newline="").read()
    if q.count(QUEUE_FLIP_OLD) != 1:
        die("queue claim line not unique")
    q = q.replace(QUEUE_FLIP_OLD, QUEUE_FLIP_OLD.replace(
        "- [ ]", "- [x]"), 1)
    if q.count(QUEUE_END_ANCHOR) != 1:
        die("queue end anchor not unique")
    q = q.replace(
        QUEUE_END_ANCHOR,
        QUEUE_END_ANCHOR + QUEUE_DONE_NOTE + "\r\n" + QUEUE_RESEED,
        1)
    io.open(P_QUEUE, "w", encoding="utf-8", newline="").write(q)
    print("queue OK: done-flip + done note + reseed line")

    # ---------- 4. status-export.json --------------------------
    import check_export_consistency as cec          # noqa: E402
    derived, _state, _exp, pat = cec.recompute()
    exp = json.loads(io.open(P_EXPORT, encoding="utf-8").read())
    exp["export_ts"] = now.astimezone().isoformat(timespec="seconds")
    exp["ceo_face"] = {
        "current": CEO_CURRENT,
        "latest_artifact": CEO_LATEST,
        "next_milestone": CEO_NEXT,
    }
    results = exp["results"]
    label = pat["tick_row_label"]
    tick_row = ["2018", label]
    rrows = [r for r in results
             if isinstance(r, list) and len(r) >= 2
             and r[1] != label]
    new_results = ([["R2018", RESULTS_ROW]]
                   + rrows[:38] + [tick_row])
    exp["results"] = new_results
    sd = dict(derived)
    sd["method"] = ("machine-derived from state.json log per "
                    "BD-PROP-001 caliber (check_export_consistency"
                    ".recompute)")
    exp["self_drive"] = sd
    io.open(P_EXPORT, "w", encoding="utf-8", newline="").write(
        json.dumps(exp, ensure_ascii=False, indent=2) + "\n")
    print("status-export.json OK: results=%d self_drive window=%s"
          % (len(new_results), sd.get("window")))
    print("R2018 CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
