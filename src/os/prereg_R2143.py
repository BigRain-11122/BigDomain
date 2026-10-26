"""R2143 pre-registration writer: inserts the reply-revision claim
row (AC-AMRY1..AC-AMRY8) at the head of state/queue/explore.md.

The criteria text below is written BEFORE apimarket.py gained the
reply-revision code, which is the honesty law this round claims.
ASCII-only script; the Chinese row text lives in ROW.
"""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "explore.md")

ROW = (
    "- [ ] P3 explore \u81ea\u8865\u79cd\u5e76\u540c\u7a97\u8ba4\u9886"
    "\uff08R2143\uff09apimarket **\u5356\u5bb6\u56de\u5e94\u4fee\u8ba2"
    "\u817f**\uff08revise_reply + api_reply_history + "
    "apimarket_reply_revisions\uff09\u2014\u2014\u7f3a\u53e3\u5b9e"
    "\u8bc1\uff1aR2093 \u7acb\u8d77\u7684\u56de\u5e94\u95e8 "
    "reply_to_rating \u662f\u5199\u4e00\u6b21\u9762\uff08\u8868"
    "\u7ea7 UNIQUE(rating_id) + \u95e8 E_AM_REPLY_DUP\uff09\uff0c"
    "\u800c R2094 \u7684 revise_rating \u5141\u8bb8\u4e70\u5bb6"
    "\u968f\u65f6\u6539\u661f\uff1a\u5356\u5bb6\u5728 5 \u661f"
    "\u4e0b\u7b54\u300c\u8c22\u8c22\uff0c\u5f88\u9ad8\u5174\u4f60"
    "\u6ee1\u610f\u300d\uff0c\u540c\u4e00\u8bc4\u5206\u88ab\u6539"
    "\u6210 1 \u661f\u540e\u5356\u5bb6\u6c38\u8fdc\u65e0\u6cd5"
    "\u56de\u5e94\u65b0\u7684\u90a3\u6761\u8bc4\u5206\uff1b\u540c"
    "\u65cf\u4e94\u6761\u5199\u4e00\u6b21\u8f74\u5747\u5df2\u8865"
    "\u4fee\u8ba2\u817f\uff08\u4ef7\u683c R2079\uff0f\u5143\u6570"
    "\u636e R2083\uff0f\u4f9b\u7ed9 R2095\uff0f\u8bc4\u5206 R2094"
    "\uff0f\u5e73\u53f0\u8eab\u4efd R2136\uff09\uff0c\u5ba1\u6838"
    "\u9762\u53e6\u6709\u5468\u671f\u5f8b\uff08R2133\uff09\uff0c\u552f"
    "\u56de\u5e94\u9762\u662f\u4fe1\u4efb\u9762\u6700\u540e\u4e00"
    "\u6761\u65e0\u6551\u6d4e\u8f74\u3002\u5224\u636e "
    "**AC-AMRY1..AC-AMRY8 \u9884\u6ce8\u518c\u4e8e\u672c\u884c"
    "\u4e14\u5148\u4e8e\u4ee3\u7801**\uff08AC-AMRY / revise_reply"
    " / api_reply_history / apimarket_reply_revisions / "
    "E_AM_REPLY_UNCHANGED / E_AM_UNKNOWN_REPLY / "
    "test_apimarket_replyrev / ledger-apimarket-replyrev \u516b"
    "\u951a\u5168\u4ed3 git grep -F \u96f6\u5360\u7528 rc=1 \u5b9e"
    "\u6d4b 2026-10-26\uff09\uff1a\n"
    "  **AC-AMRY1 \u8ffd\u52a0\u5f0f\u4e0e\u5951\u7ea6**=\u4fee"
    "\u8ba2\u6070\u5199\u4e00\u884c apimarket_reply_revisions"
    "\uff08previous_text + reply_text + revised_utc\uff0c\u65e0"
    "\u56de\u5199\u57fa\u7840\u884c\uff09\u00b7\u57fa\u7840\u56de"
    "\u5e94\u884c apimarket_rating_replies \u9010\u5b57\u6bb5"
    "\u6c38\u4e0d\u6539\u5199\u00b7\u8fd4\u56de\u4fe1\u5c01\u6070"
    "\u4e5d\u952e {revision_id,reply_id,rating_id,listing_id,"
    "dev_account,previous_text,reply_text,revised_utc,"
    "disclaimer}\u00b7\u6587\u53bb\u9996\u5c3e\u7a7a\u767d\u5b58"
    "\u50a8\uff1b\n"
    "  **AC-AMRY2 \u95e8\u5e8f fail-closed**=\u8d26\u6237\u5f62"
    "\u2192E_AM_BAD_ACCOUNT\uff1b\u56de\u5e94\u53f7\u5f62\u2192"
    "E_AM_BAD_ARGS\uff1b\u6587\u5f62\uff08\u975e str\uff0f\u7a7a"
    "\u4e32\uff0f\u7eaf\u7a7a\u767d\uff0f501 \u5b57\uff0f\u63a7"
    "\u5236\u5b57\u7b26\uff09\u2192E_AM_BAD_REPLY\uff08**\u5148"
    "\u4e8e\u5b58\u5728\u95e8**\uff09\uff1b\u672a\u77e5\u56de\u5e94"
    "\u2192E_AM_UNKNOWN_REPLY\uff1b\u975e\u672c\u5e8a\u5356\u5bb6"
    "\uff08\u542b\u6070\u597d\u8d1f\u8d23\u8be5\u8bc4\u5206\u6240"
    "\u5c5e\u6302\u724c\u7684\u4e70\u5bb6\uff09\u2192"
    "E_AM_NOT_OWNER\uff1b\u65e0\u53d8\u5316\u2192"
    "E_AM_REPLY_UNCHANGED\uff1b\u53cc\u574f\u63a2\u9488\u5404\u7b54"
    "\u524d\u8005\uff0c\u5168\u65cf\u96f6\u884c\u96f6 token\u3001"
    "\u62d2\u7edd\u524d\u540e\u5168\u90e8 apimarket_* \u8868\u6458"
    "\u8981\u4e0e ledger_tx \u96c6\u9010\u5b57\u8282\u4e0d\u53d8"
    "\uff1b\n"
    "  **AC-AMRY3 \u65e0\u53d8\u5316\u5224\u5b9a\u5bf9\u751f\u6548"
    "\u503c**=A\u2192B\u2192A \u5408\u6cd5\uff08\u7b2c\u4e09\u6b21"
    "\u4e0e\u751f\u6548\u503c\u4e0d\u540c\uff09\u00b7\u8fde\u7eed"
    "\u540c\u503c\u62d2\u7edd\u4e14\u9996\u4fee\u8ba2\u6233\u6c38"
    "\u4e0d\u88ab\u6539\u5199\uff1b\n"
    "  **AC-AMRY4 \u5355\u7f1d\u751f\u6548\u4e0e\u9000\u5f79**="
    "api_rating_replies \u7684 reply.reply_text \u8d70\u5355\u4e00"
    "\u751f\u6548\u7f1d _effective_reply\uff1b\u4fee\u8ba2\u540e "
    "reply_id\uff0freplied_utc\uff0f\u661f\u503c\uff0f\u672a\u5e94"
    "\u7b54\u884c\u7684 reply=None \u9010\u5b57\u8282\u4e0d\u53d8"
    "\uff1b\u9000\u5f79\u6302\u724c\u7684\u56de\u5e94\u4ecd\u53ef"
    "\u4fee\u8ba2\u4e14\u53f2\u53ef\u8bfb\uff08\u9000\u5f79\u4e0d"
    "\u51bb\u7ed3\u56de\u5e94\u817f\uff09\uff1b\n"
    "  **AC-AMRY5 \u5386\u53f2\u8bfb\u9762**=api_reply_history "
    "\u6070\u5341\u4e8c\u952e {reply_id,rating_id,listing_id,"
    "dev_account,buyer_id,stars,effective_text,base_text,"
    "revision_count,latest_revised_utc,disclaimer,revisions}"
    "\uff1brevisions \u6309 revision_id \u5347\u5e8f\u4e14\u9010"
    "\u952e\u56db\u5143 {revision_id,previous_text,reply_text,"
    "revised_utc}\uff1beffective_text==\u672b\u4fee\u8ba2\u6587"
    "\uff08\u65e0\u4fee\u8ba2=\u57fa\u7840\u6587\uff09\uff1b"
    "revision_count==len(revisions)\uff1b\u5c1a\u672a\u56de\u5e94"
    "\u7684\u8bc4\u5206\u770b\u4e0d\u5230\u4efb\u4f55\u56de\u5e94"
    "\uff0c\u5fd8\u5f55\u56de\u5e94\u53f7\u2192E_AM_UNKNOWN_REPLY"
    "\uff0c\u574f\u5f62\u5148\u4e8e\u5b58\u5728\u95e8\uff1b\n"
    "  **AC-AMRY6 \u7eaf\u8bfb\u4e0e\u96f6 token**=\u4e24\u9762"
    "\u524d\u540e\u96f6\u884c\u53d8\u66f4\u3001\u5168\u90e8\u8868"
    "\u6458\u8981\u51bb\u7ed3\u3001ledger_tx \u96c6\u4e0e\u56db"
    "\u8d26\u6237\u4f59\u989d\u6052\u5b9a\uff1b\u540c\u53c2\u91cd"
    "\u590d\u8c03\u7528\u9010\u5b57\u8282\u540c\u4e00\uff1b\n"
    "  **AC-AMRY7 \u4e0e\u8bc4\u5206\u4fee\u8ba2\u6b63\u4ea4**="
    "\u4e70\u5bb6 revise_rating \u540e\u56de\u5e94\u6587\u4e0e "
    "revision_count \u9010\u5b57\u8282\u51bb\u7ed3\u800c\u661f"
    "\u503c\u53d8\uff1b\u5356\u5bb6 revise_reply \u540e \u661f"
    "\u503c\uff0frating_count\uff0f\u5747\u5206\uff0f"
    "api_rating_history \u7684 effective_stars \u9010\u5b57\u8282"
    "\u51bb\u7ed3\u800c\u56de\u5e94\u6587\u53d8\uff1b\n"
    "  **AC-AMRY8 \u8de8\u91cd\u542f\u4e0e\u63a5\u7ebf**=\u4e24"
    "\u6b21\u5168\u6808\u91cd\u542f\u540e\u4e09\u5b9e\u4f8b\u7684"
    "\u4e09\u9762\uff08\u56de\u5e94\u9762\uff0f\u5386\u53f2\u9762"
    "\uff0f\u56de\u5e94\u8bc4\u5206\u96c6\uff09\u9010\u5b57\u8282"
    "\u540c\u4e00\uff1b\u63a5\u7ebf reconcile_all \u5728\u518c "
    "ledger-apimarket-replyrev(8)\uff1b\u5957\u4ef6\u6e90\u7eaf "
    "ASCII \u96f6\u7f51\u7edc import\uff1bshipped config \u96f6"
    "\u6539\u52a8\u3002\n"
)


def main():
    with io.open(QUEUE, encoding="utf-8") as handle:
        body = handle.read()
    if "AC-AMRY1" in body:
        print("already pre-registered")
        return 0
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(ROW + body)
    print("prepended %d chars" % len(ROW))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())