# -*- coding: utf-8 -*-
"""R1947 claim step: append the pre-registered criteria AC-EFP1..
AC-EFP7 to the effects persist row in state/queue/tech.md BEFORE
any suite code exists (honesty law: criteria registered first).
Fail-fast anchors; EOL preserved; CJK payload inline."""
import io

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
P_TECH = ROOT + r"\state\queue\tech.md"

with io.open(P_TECH, encoding="utf-8", newline="") as fh:
    raw = fh.read()
eol = "\r\n" if "\r\n" in raw else "\n"

ROW_HEAD = "- [ ] ledger effects " \
    "\u7279\u6548\u9762\u8bfb\u9762\u65cf\u8de8\u91cd\u542f\u6301" \
    "\u4e45\u5316\u4f8b\u7a97\uff08R1942 \u8865\u79cd"
assert raw.count(ROW_HEAD) == 1, "effects row head not unique"
idx = raw.find(ROW_HEAD)
end = raw.find(eol, idx)
assert end > idx, "effects row has no line end"

CLAIM = (
    "\u2014\u2014R1947 \u8ba4\u9886\u00b7\u5224\u636e\u9884\u6ce8"
    "\u518c\u5148\u884c\uff08\u672c\u884c\u5373\u518c\u00b7\u5148"
    "\u4e8e\u4ee3\u7801\u00b7\u4e24\u4ef6\u5957\u6808=fx \u76f4\u9a91"
    " ledger \u540c\u5e93\u3014effects \u53cc\u8868\u751f\u4e8e"
    " ledger.db\u00b7face \u81ea\u6301\u8fde\u63a5\u3015\u00b7AC-EFP"
    "1..EFP7 \u5168\u4ed3 git grep \u96f6\u5360\u7528\u5b9e\u951a "
    "2026-10-14\u3014rc=1\u00b7\u73b0\u5360\u4f4d=R1942 \u8865\u79cd"
    "\u6587\u4e0e closeout_R1942 \u9884\u7559\u3015\uff09\uff1a"
    "**AC-EFP1**\uff08\u951a\u4e16\u754c+\u5173\u524d\u7535\u6c60"
    "+\u4e5d\u95e8\u63a2\u9488\u5168\u62d2\u96f6\u6f02\u79fb\uff09="
    "\u771f\u4ea7\u54c1\u5f84\u4e16\u754c\u3014mint pool:reserve"
    " 1000+ada/bob/carol \u4e09\u6237\u6ce8\u8d44 300/100/200\uff08"
    "\u4f59\u989d 220/90/200\u00b7pool:reserve 490=\u6d88\u8d39\u56de"
    "\u6d41\u5165\uff09\u3015ada \u56db\u7c7b\u56db\u8d2d\u3014"
    "dynamic_emoji@50+limit_up@10+flood@10+pin@10=\u56db credit "
    "\u7ed1\u56db\u771f spend tx\u3015+bob flood@10 \u4e00\u8d2d"
    "\u3014\u8de8\u79cd\u63a2\u9488\u5f39\u836f\u3015+ada \u53cc\u7528"
    "\u3014use:efp-u1 \u52a8\u6001\u2192\u6548\u679c#1 \u6d88 credit#1+"
    "use:efp-u2 \u6da8\u505c\u2192\u6548\u679c#2 \u6d88 credit#2\u3015+"
    "carol \u96f6\u884c\u7eaf\u9762\u2014\u2014\u7535\u6c60\u3014"
    "credits_view\u00d73+effects_view\u00d73 dumps+\u56db\u4f59\u989d+"
    "\u53cc\u8868\u8ba1\u6570 credits=5 effects=2 spend_tx=5+\u53cc"
    "\u8868\u5168\u884c\u5feb\u7167\u3015+\u4e5d\u95e8\u63a2\u9488"
    "\u3014\u574f\u8d26\u6237\u8d2d/\u574f kind \u8d2d/\u574f kind "
    "\u7528/\u96f6\u4ef7/\u7a7a\u8d2d ref/\u7a7a message ref/\u7a7a "
    "use ref/bob \u65e0 credit \u7528 E_EFF_NO_CREDIT/bob \u8de8\u79cd"
    "\u7528 flood credit \u8bf7\u6c42 limit_up E_EFF_NO_CREDIT\u3015"
    "\u5168\u62d2+\u63a2\u9488\u6279\u524d\u540e\u8ba1\u6570\u7535"
    "\u6c60\u51bb\u7ed3\uff1b**AC-EFP2**\uff08\u8de8\u91cd\u542f"
    "\u5b57\u8282\u540c\u4e00\u6838\u5fc3\uff09=fx.close+led.close"
    "\u2192\u540c db/cfg \u91cd\u5f00\u4e24\u4ef6\u5957\u2192\u7535"
    "\u6c60\u516d dumps+\u56db\u4f59\u989d\u9010\u5b57\u8282==\u5173"
    "\u524d\uff08\u6d3e\u751f\u8bfb\u9762\u96f6\u5185\u5b58\u6001"
    "\u6f02\u79fb\uff09\uff1b**AC-EFP3**\uff08\u95e8\u8de8\u91cd"
    "\u542f\u540c\u7801\u51bb\u7ed3\uff09=\u5b9e\u4f8b\u2461\u4e5d"
    "\u63a2\u9488\u540c\u7801\u5168\u62d2+\u8ba1\u6570\u7535\u6c60"
    "\u51bb\u7ed3\uff1b**AC-EFP4**\uff08\u771f\u5f84\u7eed\u5199="
    "\u524d\u7a97 credit \u8de8\u91cd\u542f\u7eed\u670d\uff09=\u5b9e"
    "\u4f8b\u2461 ada \u7528 pin \u6d88\u5173\u524d credit#4\u3014"
    "\u524d\u7a97\u4fe1\u7528\u7eed\u670d\u3015+ada \u7528 flood "
    "\u6d88\u5173\u524d credit#3+carol \u5168\u65b0\u8d2d\u7528\u94fe"
    "\u3014\u8d2d dynamic@5 \u65b0 credit#6 \u7ed1\u65b0\u771f spend "
    "tx\u3014SQL cross type=spend+carol debit \u817f\u3015\u2192"
    "\u7528\u2192\u6548\u679c#5\u3015\u2014\u2014credits 5\u21926 "
    "effects 2\u21925 spend 5\u21926 \u4f59\u989d carol 200\u2192195 "
    "pool:reserve 490\u2192495+\u7535\u6c60\u96f6\u7f13\u5b58\u91cd"
    "\u7b97\uff1b**AC-EFP5**\uff08\u51bb\u7ed3\u884c+\u91cd\u653e"
    "\u95e8\uff09=\u53cc\u8868\u65e2\u6709\u884c\u5168\u5b57\u6bb5"
    "\u51bb\u7ed3 vs \u5173\u524d\u5feb\u7167\u3014\u542b consumed_"
    "utc/used_effect \u7ed1\u5b9a\u3015+\u8d2d ref \u91cd\u653e\u5e42"
    "\u7b49\u56de\u539f credit \u96f6\u4e8c\u6263+\u7528 ref \u91cd"
    "\u653e\u5e42\u7b49\u56de\u539f effect \u96f6\u4e8c\u6d88+\u8de8"
    "\u8d26\u6237\u91cd\u653e E_EFF_DUP_USE+\u8017\u5c3d\u7c7b\u518d"
    "\u7528 E_EFF_NO_CREDIT+\u63a2\u9488\u6279\u540e\u8ba1\u6570"
    "\u7535\u6c60\u51bb\u7ed3\uff1b**AC-EFP6**\uff08\u7eaf\u8bfb"
    "\u5f8b\uff09=\u7535\u6c60\u53cc\u8fde\u8bfb\u9010\u5b57\u8282"
    "\u540c\u4e00+\u8ba1\u6570\u6052\u5b9a\uff1b**AC-EFP7**\uff08"
    "\u4e09\u5b9e\u4f8b\u7a33\u5b9a+\u536b\u751f\uff09=\u7b2c\u4e09"
    "\u5b9e\u4f8b\u91cd\u5f00\u7535\u6c60==\u5b9e\u4f8b\u2461\u7ec8"
    "\u6001+shipped \u4e09\u4ef6\u3014config.json/effects.py/ledger."
    "py\u3015sha16 \u7a33\u5b9a+\u5957\u4ef6\u6e90\u7eaf ASCII+"
    "\u771f import \u884c\u96f6\u7f51\u7edc\u5e93+\u4e16\u754c tmp "
    "\u4ed3\u5916\u2014\u2014\u8bc1\u636e=qa/effects-persist-R1947."
    "log \u516d\u8282\u3014evidence_R1947.py LF \u5f52\u4e00\u5f8b"
    "\u3015\uff09"
)

raw = raw[:end] + CLAIM + raw[end:]
with io.open(P_TECH, "w", encoding="utf-8", newline="") as fh:
    fh.write(raw)

with io.open(P_TECH, encoding="utf-8", newline="") as fh:
    chk = fh.read()
assert chk.count(ROW_HEAD) == 1
assert "**AC-EFP1**" in chk and "**AC-EFP7**" in chk
print("claim appended: AC-EFP1..EFP7 pre-registered in tech.md "
      "effects row (before code); eol=%r" % eol)
