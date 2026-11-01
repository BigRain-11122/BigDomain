"""heartbeat_R2367.py - append this round's heartbeat line (tick token included).

The scanner reads the last non-blank heartbeat line and needs "tick <n>" in it;
the R2366 line was pure narrative, which is why [HB] flagged this window open.
This round writes the token into the line itself instead of adding a second row.
"""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
PATH = os.path.join(ROOT, "heartbeat.txt")

LINE = (
    "R2367 (tick 2367): QA charter daily crawl round - one official source read "
    "and three design gates taken from it, zero product code. The scan at open "
    "was clean on ledger (0 unreplied @BigDomain), decisions (no new token over "
    "81 known), orders (baseline ahead, no new order), benchmarks (1 day old) "
    "and tree (clean, no index.lock), and raised exactly two flags: [QA] the "
    "daily crawl was due, and [HB] the heartbeat was unparsed. The HB cause is "
    "measured, not guessed: the scanner takes the LAST non-blank heartbeat line "
    "and requires 'tick <n>' in it, and the R2366 line was pure narrative, so "
    "the row existed but could not be parsed - this line carries the token. "
    "CRAWL: wx.requestVirtualPayment official API page, one fetch, zero key, "
    "read finished - signData must be passed as a JSON STRING, its nine fields "
    "and their required/conditional status are now on file, and the twenty-five "
    "error codes are recorded verbatim including -15011 (live builds accept "
    "env=0 only, so sandbox is not a production verification path), -15002 plus "
    "the page own note that outTradeNo is one-use but NOT guaranteed unique "
    "(so the idempotency key stays ours), and -15013 (goodsPrice is checked "
    "against the console item price, so an item must be published and priced "
    "before any order). Consumed into benchmarks section 1/3/4, wall W37 plus "
    "its conclusion row, and the pay-spec field gate. Battery NOT run: "
    "reconcile-battery-R2367 stays OPEN with its measured target of 494 suites "
    "and 3940 criteria and is the next window first item on a committed tree. "
    "Zero product points, disclosed rather than dressed up.\n"
)


def main():
    with io.open(PATH, "r", encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    if "tick 2367" in text:
        print("REFUSE already present")
        return 2
    body = text if text.endswith("\n") else text + "\n"
    body += LINE
    with io.open(PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    with io.open(PATH, "r", encoding="utf-8", errors="replace") as handle:
        back = handle.read()
    ok = back.endswith(LINE) and "tick 2367" in back.splitlines()[-1]
    print("HEARTBEAT appended=%s lines=%d" % (ok, len(back.splitlines())))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())