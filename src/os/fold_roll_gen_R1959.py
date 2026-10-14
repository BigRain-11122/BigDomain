# -*- coding: utf-8 -*-
"""Fold R517 rolling-line generator (gen517 caliber): measures the
tail-3 window line byte sizes, extracts the full token catalog
mechanically (logs_toolkit PAT, zero hand-copying), and writes the
one-line rolling summary to fold_roll_R1959.txt for the fold tool.
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
OUT = os.path.join(HERE, "fold_roll_R1959.txt")

with io.open(P_STATE, encoding="utf-8") as fh:
    st = json.load(fh)
log = st["log"]
assert len(log) == 17, "expected 17 lines, got %d" % len(log)
window = log[-3:]
labels = ["fold R516 rolling line", "R1959 round line",
          "R1959 tokens"]
sizes = [len(ln.encode("utf-8")) for ln in window]
total = sum(sizes)
toks = set()
for ln in window:
    toks |= set(PAT.findall(ln))
catalog = ",".join(sorted(toks))

size_bits = "+".join("%s [%dB]" % (lab, sz)
                     for lab, sz in zip(labels, sizes))

head = (
    "2026-10-14\uff08R1957..R1959 \u6eda\u7a97\u5e76\u6298\u6458\u8981\u00b7"
    "fold R517 \u627f R1959 \u6536\u8d26\u540e\u6c34\u4f4d\u88c1\u5b9a"
    "\u5151\u73b0\uff3b\u6536\u8d26\u5bf9\u8ffd\u52a0\u540e\u5b9e\u6d4b "
    "76180B\uff0b\u9884\u7559 reserve 3000 \u8d8a 78500B \u7ebf\uff1d"
    "P-2026-09-25-18 \u7b2c\u4e94\u767e\u4e00\u5341\u4e03\u5200\u00b7"
    "\u5f00\u7a97\u5e8f=\u4ea7\u54c1\u4ef6+\u6536\u8d26\u5148\u4e8e fold"
    "\uff08R1886/R1898/R1943 \u4ea7\u54c1\u4ef6\u5148\u4e8e fold \u5148"
    "\u4f8b\u00b7R1898/R1908/R1923 fold \u5148\u884c\u5e8f=\u540c\u5f8b"
    "\u5f02\u5e8f\u4e24\u6001\u5e76\u5217\u5b58\u6863\uff09\uff3d\u00b7"
    "\u7a97=tail 3\uff1a")

mid = ("\u00b73 \u884c %dB \u538b 1 \u6eda\u7a97\u884c kept=0\u00b7"
       "%d token \u5168\u5b57\u9762\u5d4c\u96f6\u4e22\u5931\uff3bcatalog "
       "\u673a\u68b0\u63d0\u53d6\u96f6\u624b\u6284\u00b7\u751f\u6210\u5668"
       "\u7a0b\u5e8f\u5316\u62fc\u63a5 gen517\uff3d\u00b7\u539f\u6587\u5168"
       "\u91cf\u4fdd\u5168=archive \u00a7R1959 \u8282 3 \u884c verbatim+"
       "preop \u5907\u4efd\u4ef6 logs/state-preop-R1959.bak+git \u53f2"
       "\uff09\u2014\u2014carried rolling line: the R1957..R1958 fold "
       "R516 line is folded in here (its token catalog re-embedded "
       "below with zero loss; its detailed narratives live verbatim "
       "in archive section R1958; R1953/R1956/R1958 carry precedent "
       "caliber)\u2014\u2014\u6bb5\u5185\u5bb9=R1959 \u5355\u8f6e\u4ea4"
       "\u4ed8\uff08ledger growth-archive \u6210\u957f\u6863\u6848\u9762"
       " persist \u4f8b\u7a97\u00b7\u5224\u636e\u9884\u6ce8\u518c\u5148"
       "\u4e8e\u4ee3\u7801+RUNNER \u5168\u91cf\u56de\u5f52\u96f6\u6f02"
       "\u79fb+\u53cc\u8dd1 stdout \u9010\u5b57\u8282\u540c\u4e00\u8282"
       "\u5f8b\uff09\uff1aR1959 ledger growth-archive \u8bfb\u9762\u65cf"
       "\u8de8\u91cd\u542f\u6301\u4e45\u5316\u4f8b\u7a97\uff08AC-GAP1.."
       "GAP7\u00b7\u53cc\u5c45\u6c11\u53cc\u7a97\u53cc\u6237\u4e16\u754c"
       "\u6bcf\u8ba2\u9605\u6070\u7ed1\u4e00\u771f spend tx/2099-01 "
       "\u9875\u56db\u8282\u5224\u8bfb+**\u7a97\u5185\u8fc7\u6ee4\u62a4"
       "\u65e7\u7a97\u96f6\u6e17\u900f**/\u4e03\u95e8\u63a2\u9488\u6279"
       "\u53cc\u5b9e\u4f8b\u7801\u5e8f\u540c\u4e00/\u51bb\u7ed3\u951a"
       " append-only+\u91cd\u653e\u95f8 dup-before-spend \u8de8\u91cd\u542f"
       "/\u7eaf\u8bfb\u5f8b/\u7b2c\u4e09\u5b9e\u4f8b+\u536b\u751f\u96f6 "
       "UPDATE \u673a\u68c0\u00b7\u9996\u8dd1 5/7 \u4e24 harness \u4fee"
       "\u540e\u5168\u7eff\u5982\u5b9e\u6ce8\uff3bAC-GAP5 \u951a id \u8fc7"
       "\u6ee4\u5f0f+AC-GAP7 ga_ \u524d\u7f00\u00b7\u5224\u636e\u8bed\u4e49"
       "\u4e0d\u53d8\uff3d\u00b7RUNNER 197/197 \u5224\u636e 1711\u2192"
       "1718\uff3bSUITES 196\u2192197\uff3d+DEC/GORD \u53cc\u6301\u5e73"
       "\uff3brows 326/tokens 180/394\uff3d+tech consume 1 reseed 1"
       "\uff3bmember reminder persist \u79cd\u5b50\u00b7AC-RMP \u96f6"
       "\u5360\u7528\uff3d+export tick \u884c trim \u5751\u540c\u8f6e\u4fee"
       "\u5982\u5b9e\u6ce8\uff3bR1958 fallback \u5757\u590d\u539f\u00b7"
       "\u7ec8\u6001 21/21 PASS\uff3d\uff09\u2014\u2014token catalog=")

line = head + size_bits + mid + catalog
assert "\n" not in line
with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
    fh.write(line)
print("fold_roll_R1959.txt written: %d bytes, %d tokens, window=%dB"
      % (len(line.encode("utf-8")), len(toks), total))
