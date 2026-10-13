# -*- coding: utf-8 -*-
"""R1909 claim registration: append the pre-registered criteria
note (AC-TRW8..AC-TRW14 + three rulings) to the claimed tech.md
row BEFORE any test code runs (honesty law: criteria first).
Idempotent: skips if the claim marker is already present."""
import io
import sys

P = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain\state\queue\tech.md"
ANCHOR = (u"\u5165\u5217 2026-10-13\u3014R1904 "
          u"\u8865\u79cd\u00b7\u961f\u5c3e\u3015\uff09")
CLAIM_TAIL = u"\u3014R1909 \u8ba4\u9886\u3015"
CLAIM_NOTE = (
    u"\u2014\u2014\u30142026-10-13 R1909 \u8ba4\u9886\u3015"
    u"\u2014\u2014\u5224\u636e\u9884\u6ce8\u518c\uff08\u5148\u4e8e"
    u"\u4ee3\u7801\u00b7\u672c\u884c\u5373\u518c\u00b7AC-TRW8.."
    u"AC-TRW14 \u7eed\u7f16\u524d\u7f00\u5168\u4ed3 git grep "
    u"\u96f6\u5360\u7528\u5b9e\u951a 2026-10-13\uff09"
    u"+\u4e09\u88c1\u5b9a\u5165\u518c\uff1a"
    u"\u88c1\u5b9a\u4e00\u91cd\u542f\u8f7d\u4f53=\u4e09\u4ef6"
    u"\u5957\u5168\u6808\u9006\u4f9d\u8d56\u5e8f\u5173\u91cd\u5f00"
    u"\uff08DevKeyFace\u2192MeteredFace\u2192Ledger \u9006\u5e8f"
    u"\u5168\u5173\u00b7\u540c db \u8def\u5f84+\u540c config "
    u"\u5b57\u8282\u91cd\u5f00\uff09\uff1b"
    u"\u88c1\u5b9a\u4e8c\u4e16\u754c=\u5341\u6708\u951a=active "
    u"\u4e2d\u4f4d\u952e chain-b\uff08issue chain-a\u2192rotate "
    u"chain-b=\u5341\u6708 rotate_in \u771f\u4ea7\u54c1\u4e8b"
    u"\u4ef6\u00b7status=active\uff09+lone-e \u7ec8\u6001\u952e"
    u"\uff08\u5341\u6708 revoke\u00b7E_AD_ALREADY \u53cc\u95e8"
    u"\u95ed\u94fe=\u96f6\u65b0\u884c\u53ef\u8fbe=\u5341\u6708"
    u"\u7a97\u8bfb\u5168\u4fe1\u5c01\u51bb\u7ed3\u552f\u4e00"
    u"\u9762\uff09+\u5341\u4e00\u6708\u672c\u952e\u6ce8\u5165="
    u"rotate chain-b\u2192chain-c \u771f\u4ea7\u54c1\u5f84\uff08"
    u"\u7ec8\u6001\u952e revoke/rotate \u53cc\u95e8 E_AD_ALREADY="
    u"\u540c\u952e\u65b0\u884c\u552f\u4e00\u6d3b\u8def=active "
    u"\u952e rotate\uff09\uff1b"
    u"\u88c1\u5b9a\u4e09\u6bd4\u8f83\u9762=trail-scoped \u51bb"
    u"\u7ed3\uff08lifecycle_trace \u7a97\u8bfb\u4fe1\u5c01\u8f7d"
    u"\u5168\u91cf\u6d3e\u751f\u952e\u4e8b\u5b9e\uff08status+\u53cc"
    u" pair\u00b7R1875 \u7a97\u900f\u955c\u5f8b\uff09\u2192\u540c"
    u"\u952e\u5341\u4e00\u6708\u6ce8\u5165\u540e\u5341\u6708\u7a97"
    u"\u8bfb trail \u5757\uff08api_key/dev_account/key_name/"
    u"key_id/events/total/window/disclaimer \u516b\u5b57\u6bb5\uff09"
    u"\u9010\u5b57\u8282\u51bb\u7ed3+\u4e09\u952e\u4e8b\u5b9e\u5b57"
    u"\u6bb5\u91cd\u7b97\u81f3\u8bbe\u8ba1\u503c\uff08status "
    u"active\u2192rotated_out\u00b7rotated_to None\u2192id_c\uff09"
    u"\u5982\u5b9e\u6ce8\u00b7lone-e \u5341\u6708\u7a97\u8bfb=\u5168"
    u"\u4fe1\u5c01\u9010\u5b57\u8282\u51bb\u7ed3\uff1b\u2460\u2461"
    u"\u2463\u4e09\u9762=\u5168\u4fe1\u5c01\u9010\u5b57\u8282\uff08"
    u"\u7eaf\u91cd\u542f\u96f6\u949f\u79fb+\u7b2c\u4e09\u5b9e\u4f8b"
    u"\u96f6\u949f\u79fb\uff09\uff09\u2014\u2014"
    u"AC-TRW8 \u5341\u6708\u951a\u4e16\u754c+\u5173\u524d\u56db"
    u"\u5143\u5feb\u7167\uff08W=chain-b rotate_in \u884c record-"
    u"time window SQL \u6d3e\u751f=\u6708\u62bd\u8c61\u5f8b+\u7f3a"
    u"\u7701 10 \u952e/\u7a97\u8bfb 11 \u952e/\u4e8b\u4ef6\u884c 4 "
    u"\u952e\u9489\u6b7b+\u7a97\u8bfb\u4e8b\u4ef6\u5217==manual "
    u"SQL \u7a97\u5207\u7247\u4ea4\u53c9+lone-e \u7ec8\u6001\u9762 "
    u"[revoke]+\u53cc\u952e status/pair \u9489\u6b7b\uff09\uff1b"
    u"AC-TRW9 \u8de8\u91cd\u542f\u5341\u6708\u663e\u5f0f\u7a97"
    u"\u8bfb\u5168\u4fe1\u5c01\u9010\u5b57\u8282\u590d\u539f+\u540c"
    u"\u53c2\u4e8c\u8bfb\u81ea\u540c\u4e00\uff1b"
    u"AC-TRW10 \u7f3a\u7701\u5168\u4e8b\u4ef6\u8bfb+lone-e \u7f3a"
    u"\u7701/\u7a97\u53cc\u8bfb\u590d\u539f\u9010\u5b57\u8282\uff08"
    u"\u949f\u672a\u52a8\uff09\uff1b"
    u"AC-TRW11 +23d \u51bb\u7ed3\u949f\u2192\u672c\u952e\u5341"
    u"\u4e00\u6708 rotate chain-c \u771f\u4ea7\u54c1\u5f84\uff08"
    u"key_events \u540c\u4e8b\u52a1\u540c\u6233 pair \u53cc\u5411="
    u"chain-b rotate_out+chain-c rotate_in\u00b7record-time "
    u"2026-11 SQL \u6233\u8bc1\uff09\u2192\u7f3a\u7701\u5168\u4e8b"
    u"\u4ef6\u8bfb\u91cd\u7b97\uff08total 1\u21922\u00b7\u4e0e\u5173"
    u"\u524d\u7f3a\u7701\u5feb\u7167\u5b57\u8282\u76f8\u5f02=\u96f6"
    u"\u7f13\u5b58\uff09+nov \u7a97\u8bfb=[rotate_out]+status "
    u"\u91cd\u7b97+rotated_to \u91cd\u7b97\uff1b"
    u"AC-TRW12 \u8001\u7a97\u96f6\u6e17\u900f\uff08\u5341\u6708"
    u"\u7a97\u8bfb trail \u5757==\u5173\u524d\u9010\u5b57\u8282+"
    u"\u4e09\u952e\u4e8b\u5b9e\u8bbe\u8ba1\u503c\u91cd\u7b97\u5982"
    u"\u5b9e\u6ce8+lone-e \u5341\u6708\u7a97\u8bfb\u5168\u4fe1"
    u"\u5c01==\u5173\u524d+\u53cc revoke E_AD_ALREADY \u95ed\u94fe"
    u"\u63a2\u9488\u96f6\u65b0\u884c+\u671b\u8fdc\u955c\u672c\u952e "
    u"key_events 2==oct 1+nov 1\u00b7\u5168\u5e93 5==3+2 \u4e0d"
    u"\u53ef\u53d8\u884c\u96f6\u4e22\u5931\uff09\uff1b"
    u"AC-TRW13 \u7b2c\u4e09\u5b9e\u4f8b\u540c\u5e93\u4e09\u5f00"
    u"\u56db\u8bfb\u4e24\u4e24\u9010\u5b57\u8282\u540c\u4e00+\u5341"
    u"\u6708\u7a97\u8bfb trail \u5757\u4ecd==\u539f\u59cb\u5173"
    u"\u524d\uff08\u91cd\u542f\u00d7\u65b0\u6570\u636e\u53cc\u52ab"
    u"\u4e0d\u6f02\uff09\uff1b"
    u"AC-TRW14 \u7eaf\u8bfb\u5f8b+\u536b\u751f\uff08\u8bfb\u7535"
    u"\u6c60\u53cc\u952e+\u672a\u77e5\u952e/\u574f\u7a97\u53cc"
    u"\u95f8\u63a2\u9488 fired \u56db\u8868\u8ba1\u6570\u6052\u5b9a"
    u"+lifecycle_trace \u6bb5 code-strip \u96f6\u5199\u5173\u952e"
    u"\u8bcd+apidev.py/config sha \u53cc\u8bc1\u96f6\u6539\u52a8+"
    u"\u7eaf ASCII+\u96f6\u7f51\u7edc+\u51bb\u7ed3\u949f\u6062"
    u"\u590d\u63a2\u9488+runner row wired\uff09"
)

with io.open(P, encoding="utf-8") as h:
    tech = h.read()
if CLAIM_TAIL in tech:
    print("claim note already present - skipped")
    sys.exit(0)
assert tech.count(ANCHOR) == 1, "seed row anchor not unique"
idx = tech.find(ANCHOR) + len(ANCHOR)
tech = tech[:idx] + CLAIM_NOTE + tech[idx:]
with io.open(P, "w", encoding="utf-8", newline="") as h:
    h.write(tech)
print("R1909 claim note registered: AC-TRW8..TRW14 + 3 rulings,"
      " %d chars appended" % len(CLAIM_NOTE))
