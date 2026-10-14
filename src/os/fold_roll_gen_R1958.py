# -*- coding: utf-8 -*-
"""Fold R516 rolling-line generator (gen516 caliber): measures the
tail-5 window line byte sizes, extracts the full token catalog
mechanically (logs_toolkit PAT, zero hand-copying), and writes the
one-line rolling summary to fold_roll_R1958.txt for the fold tool.
Pure stdlib; CJK payload embedded (data file writer, ASCII-law
exemption for md/rolling summary text per encoding law)."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from logs_toolkit import PAT  # noqa: E402

P_STATE = os.path.join(ROOT, "src", "os", "state.json")
OUT = os.path.join(HERE, "fold_roll_R1958.txt")

with io.open(P_STATE, encoding="utf-8") as fh:
    st = json.load(fh)
log = st["log"]
assert len(log) == 19, "expected 19 lines, got %d" % len(log)
window = log[-5:]
labels = ["fold R515 rolling line", "R1957 round line",
          "R1957 tokens", "R1958 round line", "R1958 tokens"]
sizes = [len(ln.encode("utf-8")) for ln in window]
total = sum(sizes)
toks = set()
for ln in window:
    toks |= set(PAT.findall(ln))
catalog = ",".join(sorted(toks))

size_bits = "+".join("%s [%dB]" % (lab, sz)
                     for lab, sz in zip(labels, sizes))

head = (
    "2026-10-14\uff08R1957..R1958 \u6eda\u7a97\u5e76\u6298\u6458\u8981\u00b7"
    "fold R516 \u627f R1958 \u6536\u8d26\u540e\u6c34\u4f4d\u88c1\u5b9a"
    "\u5151\u73b0\uff3b\u6536\u8d26\u5bf9\u8ffd\u52a0\u540e\u5b9e\u6d4b "
    "80191B \u8d8a 78500B \u7ebf\uff0b\u9884\u7559 reserve 3000="
    "\uff1dP-2026-09-25-18 \u7b2c\u4e94\u767e\u4e00\u5341\u516d\u5200\u00b7"
    "R1957 \u6536\u8d26\u9762\u672a\u89c1 fold \u627f\u4f20\u6ce8\u8bb0="
    "\u6536\u8d26\u65f6\u88c1\u5b9a\uff08R1908/R1917/R1943 \u540c\u65cf"
    "\u5148\u4f8b\uff09\u00b7\u5f00\u7a97\u5e8f=\u4ea7\u54c1\u4ef6+\u6536"
    "\u8d26\u5148\u4e8e fold\uff08R1886/R1898/R1943 \u4ea7\u54c1\u4ef6"
    "\u5148\u4e8e fold \u5148\u4f8b\u00b7R1898/R1908/R1923 fold \u5148"
    "\u884c\u5e8f=\u540c\u5f8b\u5f02\u5e8f\u4e24\u6001\u5e76\u5217\u5b58"
    "\u6863\uff09\uff3d\u00b7\u7a97=tail 5\uff1a")

mid = ("\u00b75 \u884c %dB \u538b 1 \u6eda\u7a97\u884c kept=0\u00b7"
       "%d token \u5168\u5b57\u9762\u5d4c\u96f6\u4e22\u5931\uff3bcatalog "
       "\u673a\u68b0\u63d0\u53d6\u96f6\u624b\u6284\u00b7\u751f\u6210\u5668"
       "\u7a0b\u5e8f\u5316\u62fc\u63a5 gen516\uff3d\u00b7\u539f\u6587\u5168"
       "\u91cf\u4fdd\u5168=archive \u00a7R1958 \u8282 5 \u884c verbatim+"
       "preop \u5907\u4efd\u4ef6 logs/state-preop-R1958.bak+git \u53f2"
       "\uff09\u2014\u2014carried rolling line: the R1956 fold R515 line "
       "is folded in here (its token catalog re-embedded below with "
       "zero loss; its detailed narrative lives verbatim in archive "
       "section R1957; R1953/R1956 carry precedent caliber)"
       "\u2014\u2014\u6bb5\u5185\u5bb9=R1957..R1958 \u4e24\u8f6e\uff08"
       "pay clawback \u63a5\u7ebf\u9762+ledger incentive \u6fc0\u52b1"
       "\u9762\u4e24\u65cf persist \u4f8b\u7a97\u00b7\u6bcf\u8f6e\u5224"
       "\u636e\u9884\u6ce8\u518c\u5148\u4e8e\u4ee3\u7801+RUNNER \u5168"
       "\u91cf\u56de\u5f52\u96f6\u6f02\u79fb+\u53cc\u8dd1 stdout \u9010"
       "\u5b57\u8282\u540c\u4e00\u8282\u5f8b\uff09\uff1aR1957 pay clawback "
       "\u8ffd\u56de\u63a5\u7ebf\u9762\u8bfb\u9762\u65cf\u8de8\u91cd\u542f"
       "\u6301\u4e45\u5316\u4f8b\u7a97\uff08AC-CKP1..CKP7\u00b7\u516d\u5e8f"
       "\u4e16\u754c heal \u56de\u51b2/\u8d85\u652f\u5e3d claw=40/\u96f6 "
       "token/\u95ed\u5355\u62d2+close_refund \u6b63 heal \u8def\u5f84\u5e8f"
       "\u540c\u8f6e\u4fee\u00b7RUNNER 195/195 \u5224\u636e 1697\u2192"
       "1704\u00b7fold R515 \u8f6e\u9996\u5151\u73b0 78783\u219273108B"
       "\uff09\uff1bR1958 ledger incentive \u6fc0\u52b1\u9762\u8bfb\u9762"
       "\u65cf\u8de8\u91cd\u542f\u6301\u4e45\u5316\u4f8b\u7a97\uff08"
       "AC-ICP1..ICP7\u00b7W1 \u9884\u7b97\u7ed1\u7a97 410\u2192400 \u6574"
       "\u7f29\u6070\u843d\u96f6\u820d\u5165\u635f/W2 \u9879\u5708\u7ed1 "
       "10^6\u2192150/W3 \u771f\u5f84\u7eed\u5199\u96f6\u7f13\u5b58 pool "
       "1210/\u4e03\u95e8\u6279\u53cc\u5b9e\u4f8b\u7801\u5e8f\u540c\u4e00/"
       "\u51bb\u7ed3\u951a append-only \u96f6 UPDATE \u673a\u68c0/\u7eaf"
       "\u8bfb\u5f8b/\u7b2c\u4e09\u5b9e\u4f8b\u7a33\u5b9a\u00b7RUNNER "
       "196/196 \u5224\u636e 1704\u21921711\uff3bSUITES 195\u2192196"
       "\uff3d+DEC \u4e09\u65b0 token \u77e5\u6089\u4e0d\u52a8\u4f5c"
       "\uff3bD-20261014-05/06/07 \u5747\u96c6\u56e2 HQ \u6267\u884c"
       "\u9762\u00b7last_dec_tokens 177\u2192180\uff3d+GORD +1 \u77e5\u6089"
       "\uff3bO-20261014-1330 B\u7ad9=bm-b \u7ebf\u00b7393\u2192394"
       "\uff3d+tech consume 1 reseed 1\uff3blobby \u4e8b\u4ef6\u9762 "
       "persist \u79cd\u5b50\u00b7AC-LBP \u96f6\u5360\u7528\uff3d+HB "
       "1957/1958 \u53cc\u884c\u8865\uff09\u2014\u2014token catalog=")

line = head + size_bits + mid + catalog
assert "\n" not in line
with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
    fh.write(line)
print("fold_roll_R1958.txt written: %d bytes, %d tokens, window=%dB"
      % (len(line.encode("utf-8")), len(toks), total))
