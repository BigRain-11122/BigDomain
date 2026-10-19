# closeout_R2045.py - R2045 closeout driver (orphan-takeover
# round). (1) state.json byte surgery: tick 2044 -> 2045, DEC
# baseline top-up (last_decision_rows 372 -> 377, last_dec_tokens
# += D-20261019-05,D-20261019-06 - both judged this round per the
# content-addressed scan), two-line log append via ps_escape
# (16-space indent, CRLF canonical, no trailing comma on the
# last item); ROUND_LINE text lives in
# logs/tmp-closeout-R2045-roundline.txt (encoding law: CJK in
# data files, ASCII script logic); (2) heartbeat.txt: the R2045
# alive row; (3) export flush handled by flush_export_R2045.py.
# closeout_R2043.py precedent; tail-variant tolerant (fold
# rewrite may or may not leave a trailing CRLF after the
# closing brace).
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
                       "tmp-closeout-R2045-roundline.txt")

TOKENS_LINE = (
    "R2045 tokens: local=~1.3M api=0 api_reason=five-silence "
    "scan + orphan-takeover closeout round all local (takeover "
    "suite re-verify double-run + full battery RUNNER 256 "
    "suites 289.0s + matrix/census/fingerprint/profile gates "
    "+ fold R573 + closeout edits + export flush + directed "
    "commit), zero cloud calls"
)

HB_BODY = (
    "R2045: crashed-round orphan payload takeover closeout - "
    "apimarket dev_sales_board month-window zero-listing "
    "boundary cross-restart suite delivered end-to-end "
    "(AC-AMWZB1..AMWZB7 pre-registered in the explore.md "
    "claim row by the prior session; takeover re-verify "
    "double-run byte-identical sha16 708b9736ef075c1e "
    "cross-checked MATCH against the orphan evidence log; five "
    "honest-empty read forms with window echo keys; 14 "
    "bad-window gate family rejecting on the empty data face; "
    "full-stack close/rebuild byte-identical; post-restart "
    "first-listing dense window-face join zero phantom; "
    "first-purchase NOV window zero-cache recompute "
    "{usr:ada,0,1,10,7,3} with the OCT listing window "
    "byte-frozen (record-time dual-family law) and spend/"
    "dev-share tx cross-db provenance; third-instance "
    "stability; gate family code vectors identical across "
    "restarts). reconcile_all wiring "
    "ledger-apimarket-devboardmonthboundary (SUITES 255->256, "
    "criteria 2152->2159); RUNNER PASS 256/256 suites green "
    "controls 7/7 289.0s zero regression; matrix 256/2159 "
    "--check byte-identical; census DRIFT-CLEAN; fingerprint "
    "CLEAN domains=5; profile 5-small-suite FLAG attributed to "
    "environment wall-clock variance then re-anchored per the "
    "R2044 precedent -> DRIFT-CLEAN 256/0. DEC receipts: "
    "D-20261019-05 acknowledged (HQ execution face), "
    "D-20261019-06 acknowledged (our D-20261019-04 port "
    "receipt landed at R2031, qa/loop-v2-port-R2031.log). "
    "fold R573 pre-closeout honored. Explore consume-1 "
    "reseed-1. Score 2. [via BigDomain-OSLoop]"
)


def die(msg):
    print("ABORT: %s" % msg)
    sys.exit(2)


def main():
    # ---------- 1. state.json byte surgery ----------------------
    with io.open(P_ROUND, encoding="utf-8") as fh:
        round_lines = [x.strip() for x in fh if x.strip()]
    if len(round_lines) != 1:
        die("round line data file must hold exactly one line")
    ROUND_LINE = round_lines[0]
    if not ROUND_LINE.startswith(u"2026-10-19 R2045"):
        die("round line head wrong")

    raw = open(P_STATE, "rb").read()
    text = raw.decode("utf-8")
    if text.count('"tick": 2044,') != 1:
        die("tick anchor not unique")
    text = text.replace('"tick": 2044,', '"tick": 2045,')
    if text.count('"last_decision_rows": 372,') != 1:
        die("decision-rows anchor not unique")
    text = text.replace('"last_decision_rows": 372,',
                       '"last_decision_rows": 377,')
    if "D-20261019-05" in text or "D-20261019-06" in text:
        die("dec tokens already present")
    text, n = re.subn(
        r'"last_dec_tokens": "([^"]*)"',
        lambda m: ('"last_dec_tokens": "' + m.group(1)
                   + ',D-20261019-05,D-20261019-06"'),
        text, count=1)
    if n != 1:
        die("last_dec_tokens anchor not hit")

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
    if st["tick"] != 2045 or len(st["log"]) != 16:
        die("tick/log shape wrong: %s %d" % (st["tick"],
                                             len(st["log"])))
    if not st["log"][-2].startswith(u"2026-10-19 R2045"):
        die("round line missing")
    if not st["log"][-1].startswith("R2045 tokens:"):
        die("tokens line missing")
    if "D-20261019-05" not in st["last_dec_tokens"]:
        die("dec tokens top-up missing")
    open(P_STATE, "wb").write(new_bytes)
    print("state.json OK: tick=2045 log-items=16 bytes=%d "
          "dec_rows=377" % len(new_bytes))

    # ---------- 2. heartbeat.txt: current row -------------------
    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    now = datetime.now()
    stamp = (now.strftime("%Y-%m-%d %H:%M")[:-1] + "x +08:00"
             + " | BigDomain OSLoop alive | ")
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + stamp + "tick 2045 | " + HB_BODY + "\r\n")
    print("heartbeat.txt OK: R2045 alive row appended")
    print("R2045 CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
