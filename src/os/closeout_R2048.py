# closeout_R2048.py - R2048 closeout driver (crashed-round
# orphan-payload takeover + QA-charter daily-crawl carrier round).
# (1) state.json byte surgery: tick 2047 -> 2048, DEC baseline
# top-up (last_decision_rows 383 -> 389, last_dec_tokens +=
# D-20261020-01/02/03 - all three judged this round: 01 = our
# tail-sweep face verified clean, 02/03 = non-company execution
# seats, knowledge-only per D-20260930-20 numbered-reference
# law), benchmarks_refreshed 2026-10-19 -> 2026-10-20 (QA
# charter W29 crawl), two-line log append via ps_escape (16
# -> 18 items); ROUND_LINE text lives in
# logs/tmp-closeout-R2048-roundline.txt (encoding law: CJK in
# data files, ASCII script logic); (2) heartbeat.txt: TWO rows
# = the missing tick-2047 backfill row (R2047 landed 23:47:39,
# [HB] lag=1 debt called by this round's five-silence scan) +
# the R2048 alive row. closeout_R2045.py precedent.
import io
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normcase(os.path.normpath(
    os.path.join(HERE, "..", "..")))
sys.path.insert(0, HERE)

P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_ROUND = os.path.join(ROOT, "logs",
                       "tmp-closeout-R2048-roundline.txt")

TOKENS_LINE = (
    "R2048 tokens: local=~900k api=0 api_reason=five-silence"
    " scan + orphan-takeover closeout (suite double-run"
    " re-verify + dialect-artifact rebuild + census check +"
    " full-battery RUNNER 257 suites + W29 E-Commerce-Law web"
    " crawl + four-place benchmarks + wall dual rows + smoke"
    " pair + closeout edits + export flush + directed commit),"
    " zero cloud calls"
)

HB_BACKFILL = (
    "R2047: tech-queue five-seed reseed round (five"
    " funnel-engine window seeds landed in state/queue/"
    "tech.md - CLI bad-args gates / ring cross-restart"
    " persist / cross-day rescan first-write-wins / late"
    " re-rollup / conservation chain; dedup-first all green"
    " label+source+AC greps rc=1; tech open 5->10 standing"
    " line met, deadline 10-20 landed early; DEC C-20261019-01"
    " note absorbed knowledge-only baseline flat; fold R574"
    " pre-closeout honored; export flush + consistency PASS."
    " [via BigDomain-OSLoop]"
)

HB_BODY_PATH = os.path.join(ROOT, "logs",
                            "tmp-closeout-R2048-hbbody.txt")


def die(msg):
    print("ABORT: %s" % msg)
    sys.exit(2)


def main():
    with io.open(P_ROUND, encoding="utf-8") as fh:
        round_lines = [x.strip() for x in fh if x.strip()]
    if len(round_lines) != 1:
        die("round line data file must hold exactly one line")
    ROUND_LINE = round_lines[0]
    if not ROUND_LINE.startswith(u"2026-10-20 R2048"):
        die("round line head wrong")
    with io.open(HB_BODY_PATH, encoding="utf-8") as fh:
        hb_rows = [x.rstrip("\n") for x in fh if x.strip()]
    if len(hb_rows) != 1:
        die("hb body data file must hold exactly one line")

    raw = open(P_STATE, "rb").read()
    text = raw.decode("utf-8")
    if text.count('"tick": 2047,') != 1:
        die("tick anchor not unique")
    text = text.replace('"tick": 2047,', '"tick": 2048,')
    if text.count('"last_decision_rows": 383,') != 1:
        die("decision-rows anchor not unique")
    text = text.replace('"last_decision_rows": 383,',
                       '"last_decision_rows": 389,')
    for tok in ("D-20261020-01", "D-20261020-02",
                "D-20261020-03"):
        if tok in text:
            die("dec token already present: %s" % tok)
    text, n = re.subn(
        r'"last_dec_tokens": "([^"]*)"',
        lambda m: ('"last_dec_tokens": "' + m.group(1)
                   + ',D-20261020-01,D-20261020-02,'
                     'D-20261020-03"'),
        text, count=1)
    if n != 1:
        die("last_dec_tokens anchor not hit")
    if text.count('"benchmarks_refreshed": "2026-10-19"') != 1:
        die("benchmarks anchor not unique")
    text = text.replace(
        '"benchmarks_refreshed": "2026-10-19"',
        '"benchmarks_refreshed": "2026-10-20"')

    tail_a = '"\r\n  ]\r\n}\r\n'
    tail_b = '"\r\n  ]\r\n}'
    if text.endswith(tail_a):
        tail = tail_a
    elif text.endswith(tail_b):
        tail = tail_b
    else:
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
    if st["tick"] != 2048 or len(st["log"]) != 18:
        die("tick/log shape wrong: %s %d" % (st["tick"],
                                             len(st["log"])))
    if not st["log"][-2].startswith(u"2026-10-20 R2048"):
        die("round line missing")
    if not st["log"][-1].startswith("R2048 tokens:"):
        die("tokens line missing")
    if "D-20261020-03" not in st["last_dec_tokens"]:
        die("dec tokens top-up missing")
    if st["benchmarks_refreshed"] != "2026-10-20":
        die("benchmarks top-up missing")
    open(P_STATE, "wb").write(new_bytes)
    print("state.json OK: tick=2048 log-items=18 bytes=%d "
          "dec_rows=389 bench=2026-10-20"
          % len(new_bytes))

    # ---------- 2. heartbeat.txt: backfill + current ----------
    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    hb += ("2026-10-19 23:47 +08:00 | BigDomain OSLoop alive"
           " | tick 2047 | " + HB_BACKFILL + "\r\n")
    now = datetime.now()
    stamp = (now.strftime("%Y-%m-%d %H:%M") + " +08:00"
             + " | BigDomain OSLoop alive | ")
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + stamp + "tick 2048 | " + hb_rows[0] + "\r\n")
    print("heartbeat.txt OK: tick-2047 backfill + R2048 row")
    print("R2048 CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
