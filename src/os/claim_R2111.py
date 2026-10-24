"""R2111 claim-row registration (explore queue FIFO head).

Prepends the pre-registered AC-AMRR1..AC-AMRR8 claim row to
state/queue/explore.md BEFORE the implementation exists (honesty law).
Idempotent: a second run detects its own marker and does nothing.
"""

import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
QUEUE = os.path.join(BASE, "state", "queue", "explore.md")
BACKLOG = os.path.join(BASE, "src", "os", "backlog.md")
MARK = "AC-AMRR1"

ROW = (
    "- [ ] P3 explore \u81ea\u7814\u65b0\u9762\u5b54\uff08R2111\uff09"
    "apimarket **\u9000\u6b3e\u767b\u8bb0\u7c3f**"
    "\uff1a\u5e02\u573a\u7ea7\u9000\u6b3e\u9762"
    "\uff08api_refund_register\uff1a\u7a97\u53e3+\u5356\u65b9+"
    "\u6302\u724c\u4e09\u91cd\u8fc7\u6ee4\u00b7\u6309\u6708/"
    "\u6309\u5356\u65b9/\u6309\u884c\u4e09\u6bb5\u5bf9\u8d26"
    "\u00b7\u91d1\u989d\u5b88\u6052\uff09+ \u62a5\u8868 Refund"
    " register \u6bb5 + REPORT_SCHEMA 5\u21926 \u52a0\u6cd5"
    "\u3002\u7f3a\u53e3\u5b9e\u8bc1=\u9000\u6b3e\u53ea\u80fd\u6309"
    " purchase_id\uff08api_refund\uff09\u6216\u6309\u4e70\u5bb6"
    "\uff08buyer history\uff09\u53d6\uff0c\u6ca1\u6709\u4efb\u4f55"
    "\u9762\u5b54\u56de\u7b54\u300c\u672c\u6708\u5168\u5e02\u573a"
    "\u9000\u4e86\u591a\u5c11\u3001\u54ea\u5bb6\u5356\u65b9\u9000"
    "\u6b3e\u6700\u591a\u3001\u5f02\u5e38\u5728\u54ea\u300d\uff0c"
    "\u8fd0\u8425\u5bf9\u8d26\u5fc5\u987b\u624b\u5de5\u5e76\u8868"
    "\u3002\u7814\u7a76 AC-AMRR1..AC-AMRR8 \u9884\u6ce8\u518c\u4e8e"
    "\u4ee3\u7801\u4e4b\u524d\u3002AC-AMRR \u524d\u7f00 /"
    " api_refund_register / REFUND_KEYS / refund_block /"
    " test_apimarket_report_refundregister.py /"
    " ledger-apimarket-refundregister \u5168\u4e32 git grep -F"
    " \u96f6\u5360\u7528 rc=1\uff082026-10-25\uff09\u3002"
    "\u3010**AC-AMRR1 \u5951\u7ea6\u4e0e\u6d3e\u751f\u96c6**"
    "\u3011=report['refunds'] \u56fa\u5b9a\u5341\u4e09\u952e"
    " {kind,since_utc,until_utc,dev_account,listing_id,"
    "refund_count,amount,dev_share,platform_share,months,"
    "by_dev,refunds,disclaimer}\uff1brefund_count==len(refunds)"
    "\uff1b\u96f6\u9000\u6b3e\u4e16\u754c\u8bda\u5b9e\u7a7a"
    "\uff08count 0 \u4e14\u4e09\u6bb5\u5747\u4e3a\u7a7a\u8868"
    "\uff09\u3002\u3010**AC-AMRR2 \u540c\u6e90\u65e0\u7f13\u5b58**"
    "\u3011=\u62a5\u8868\u503c==\u76f4\u8c03 api_refund_register"
    " \u540c\u53c2\u503c\uff1b\u91c7\u96c6\u540e\u65b0\u589e\u4e00"
    "\u7b14\u9000\u6b3e\u4e0b\u6b21\u91c7\u96c6\u5373\u73b0\uff1b"
    " dev_account/listing_id \u8fc7\u6ee4\u7cbe\u786e\u6536\u7a84"
    "\uff08\u4ed6\u5356\u65b9/\u4ed6\u6302\u724c\u96f6\u884c"
    "\uff09\u3002\u3010**AC-AMRR3 \u534a\u5f00\u7a97\u53e3**"
    "\u3011=refunded_utc \u6070\u7b49 since \u5165\u3001\u6070"
    "\u7b49 until \u51fa\uff1bsince>until \u62a5 E_AM_BAD_WINDOW"
    "\uff1b\u7a97\u53e3\u4e0e\u5356\u65b9\u8fc7\u6ee4\u53ef\u53e0"
    "\u52a0\u4e14\u7ed3\u679c==\u4e24\u6b21\u8fc7\u6ee4\u4ea4\u96c6"
    "\u3002\u3010**AC-AMRR4 \u91d1\u989d\u5b88\u6052**\u3011="
    "\u6bcf\u884c dev_share+platform_share==amount\uff1bmonths "
    "\u5408\u8ba1==by_dev \u5408\u8ba1==\u603b\u989d\uff1b\u6bcf"
    "\u884c\u91d1\u989d\u4e0e apimarket_refunds \u5b58\u50a8\u503c"
    "\u9010\u5b57\u6bb5\u76f8\u7b49\u3002\u3010**AC-AMRR5 \u52a0"
    "\u6cd5\u5951\u7ea6**\u3011=REPORT_SCHEMA 5\u21926\uff1bJSON "
    "\u4ecd\u6070 schema_version/report/attention \u4e09\u952e"
    "\uff1bmarket/board/sellers/buyers\uff08months,profile,"
    "todo,watch_alerts,history\uff09/activity/dossiers/"
    "attention \u5404\u5757\u503c\u4e0d\u53d8\u3002\u3010**AC-AMRR6 "
    "\u95e8\u65cf fail-closed**\u3011=\u574f\u7a97\u53e3/\u574f"
    "\u8fc7\u6ee4\u5341\u4e00\u5f0f\u5168\u62d2\uff08E_AM_BAD_WINDOW/"
    "E_AM_BAD_ARGS\uff09\uff0c\u62d2\u7edd\u524d\u540e\u5341\u4e09"
    "\u8868\u6458\u8981\u4e0e ledger_tx \u8ba1\u6570\u96f6\u53d8\u5316"
    "\u3002\u3010**AC-AMRR7 \u7eaf\u8bfb\u4e0e\u786e\u5b9a\u6027**"
    "\u3011=\u4e00\u6b21 collect \u5341\u4e09\u8868\u6458\u8981\u4e0e"
    " ledger_tx \u8ba1\u6570\u4e0d\u53d8\uff1b\u4e24\u540c\u79cd\u5b50"
    "\u4e16\u754c HTML \u4e0e JSON \u9010\u5b57\u8282\u540c\u4e00"
    "\u3002\u3010**AC-AMRR8 HTML \u9762\u4e0e\u964d\u7ea7\u56de"
    "\u5f52**\u3011=\u9875\u9762\u542b Refund register \u6bb5"
    "\u4e09\u6bb5\u8868\u5934\u4e0e\u8bda\u5b9e\u7a7a\u6001\uff1b"
    "\u6076\u610f reason \u8f6c\u4e49\uff1b\u7f3a\u952e\u65e7\u62a5"
    "\u8868\u5b57\u5178\u4ecd\u6e32\u67d3\uff1b\u516d\u4e2a\u65e2"
    "\u6709\u62a5\u8868\u5957\u4ef6\u5168\u7eff\uff1brunner \u6807"
    "\u7b7e\u5df2\u6ce8\u518c\u3002\n"
)


def main():
    for path in (QUEUE, BACKLOG):
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        if MARK in text.split("\n")[0]:
            print("SKIP claim row already first in %s"
                  % os.path.basename(path))
            continue
        if MARK in text:
            print("SKIP claim row already present in %s"
                  % os.path.basename(path))
            continue
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(ROW + text)
        print("PASS claim row prepended to %s (%d bytes)"
              % (os.path.basename(path), len(ROW.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())