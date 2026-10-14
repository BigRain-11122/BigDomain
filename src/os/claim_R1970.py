# -*- coding: utf-8 -*-
# R1970 claim: annotate explore.md line 45 with pre-registered criteria
# AC-CB1..CB5 BEFORE any implementation code exists (honesty law).
# Explore.md is LF-only; preserve exact bytes outside the target line.
import io

P = "state/queue/explore.md"
raw = io.open(P, "r", encoding="utf-8", newline="").read()
lines = raw.split("\n")
i = 45
assert lines[i].startswith("- [ ]"), "line 45 must be an open item"
assert "curation hot_board" in lines[i], "line 45 must be the curation cold board line"
assert "R1970" not in lines[i], "claim already annotated"

claim = ("\u2014\u2014\u30142026-10-14 R1970 \u8ba4\u9886\u00b7\u5224\u636e\u9884\u6ce8\u518c"
         "\u5148\u4e8e\u4ee3\u7801\uff08\u672c\u884c\u5373 AC \u627f\u8f7d\u00b7\u5148\u4e8e"
         "\u5b9e\u73b0\uff09\u3015\u5224\u636e\u9884\u6ce8\u518c\uff1a**AC-CB1 \u4fe1\u5c01"
         "\u4e0e\u884c\u5f62\u9762**=CurationFace.cold_board\(\) \u4fe1\u5c01\u952e\u96c6"
         "\u6052\u7b49 {cold_board\uff0cdisclaimer}\u00b7\u884c\u952e\u96c6\u4e0e hot_board "
         "\u884c\u5168\u540c {rank\uff0ccuration_id\uff0ctitle\uff0cai_label\uff0c"
         "member_count\uff0cdisplayed_total}\u00b7\u96f6\u7b56\u5c55\u6ce8\u518c\u9762="
         "\u8bda\u5b9e\u7a7a\u699c {cold_board:\u6f6e\u7a7a\u884c\uff0cdisclaimer \u5e38"
         "\u9a7b}\uff1b**AC-CB2 \u9006\u6ee4\u4e92\u8865\u5f8b**=\u540c\u7a97 live \u8bfb"
         " cold \u96c6\u222a\u70ed\u96c6\uff08heat>0\uff09==hot_board \u5168\u96c6\u4e14"
         "\u4ea4\u96c6\u4e3a\u7a7a\uff08\u5355\u6e90\u4e92\u8bc1\uff09\u00b7\u5168\u70ed"
         "\u4e16\u754c\uff08\u552f\u4e00\u7b56\u5c55=\u6709\u5728\u5c55\u6210\u5458\uff09="
         "\u8bda\u5b9e\u7a7a\u699c\uff1b**AC-CB3 \u786e\u5b9a\u6027\u6392\u5e8f**="
         "curation_id ASC \u4e3b\u952e\u5168\u5e8f rank 1..N\u00b7\u96f6 RNG \u96f6\u65f6"
         "\u95f4\u952e\u96f6\u63d2\u5165\u5e8f\u952e\u00b7\u53cc\u8bfb dumps \u9010\u5b57"
         "\u8282\u540c\u4e00\uff1b**AC-CB4 \u5355\u6d3e\u751f\u6e90\u5f8b**=cold_board "
         "\u65b9\u6cd5\u4f53\u96f6\u76f4\u63a5 showcase \u8868\u8bfb/\u96f6 curation SQL "
         "\u8bfb\u6570\uff08\u7eaf self.hot_board\(\) \u59d4\u6258+\u8fc7\u6ee4\u00b7\u96f6"
         "\u7b2c\u4e8c\u805a\u5408\u5f15\u64ce\uff09\u00b7\u884c\u5e38\u9a7b ai_label"
         "\uff08\u5448\u73b0\u9762 AIGC \u6807\u8bc6\uff09\uff1b**AC-CB5 \u7eaf\u8bfb"
         "\u4e0e\u786c\u6cd5\u968f\u627f**=\u91cd\u590d\u8bfb\u96f6\u884c\u6570\u6f02"
         "\u79fb+ledger_tx \u8ba1\u6570\u6052\u5b9a+\u65b9\u6cd5\u4f53\u96f6\u5199\u8bed"
         "\u53e5\uff08INSERT/UPDATE/DELETE \u8bcd\u626b\uff09\u00b7\u6a21\u5757\u7eaf "
         "ASCII \u96f6 UPDATE \u6e90\u626b \u96f6 RNG \u96f6\u6d41\u901a\u52a8\u8bcd "
         "\u96f6\u7f51\u7edc\u5e93 import+shipped config.json \u5b57\u8282\u7a33\u2014"
         "\u2014\u8f7d\u4f53\uff1acuration.py \u589e cold_board\uff08\u7eaf ASCII \u6e90"
         "\uff09+test_curation.py \u6269 AC-CB1..CB5 \u4f8b+reconcile_all SUITES "
         "ledger-curation \u5224\u636e 19\u219224 \u63a5\u7ebf+\u8bc1\u636e "
         "qa/curation-coldboard-R1970.log\uff08\u5957\u4ef6+RUNNER \u5168\u91cf+\u77e9"
         "\u9635\u518d\u751f\u4e09\u8282\uff09")
lines[i] = lines[i] + claim
io.open(P, "w", encoding="utf-8", newline="").write("\n".join(lines))
print("CLAIM-OK line45 annotated len=%d" % len(lines[i]))
