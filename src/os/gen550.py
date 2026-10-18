# gen550_R2020.py - fold R550 (tail-3 -> one rolling line) + R2020 closeout surgery
# Byte-surgical: raw-text edits only, json.loads validated at the end.
import hashlib, json, re, sys, io
from datetime import datetime

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
STATE = ROOT + r"\src\os\state.json"
ARCHIVE = ROOT + r"\logs\state-log-archive-2026-10.md"
PREOP = ROOT + r"\logs\state-preop-R2020.bak"
HB = ROOT + r"\heartbeat.txt"

with io.open(STATE, "r", encoding="utf-8", newline="") as f:
    text = f.read()

gauge = len(text.encode("utf-8"))
preop_sha16 = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

# --- locate the log array tail-3 item lines ---
lines = text.split("\n")
def is_log_item(l):
    s = l.strip()
    return s.startswith('"') and (s.endswith('",') or s.endswith('"'))

idx = [i for i, l in enumerate(lines) if is_log_item(l)]
if len(idx) < 3:
    sys.exit("FATAL: cannot locate 3 log tail lines")
t3 = idx[-3:]
tail_lines = [lines[i] for i in t3]
markers = ["fold R549", "R2019\uff08\u4e94\u9759\u68c0\u51fa", "R2019 tokens"]
for m, l in zip(markers, tail_lines):
    if m not in l:
        sys.exit("FATAL: tail marker mismatch: expected %r in %r" % (m, l[:80]))
indent = tail_lines[0][:len(tail_lines[0]) - len(tail_lines[0].lstrip())]
folded_bytes = sum(len(l.encode("utf-8")) + 1 for l in tail_lines)

# --- preop backup + archive verbatim append ---
with io.open(PREOP, "w", encoding="utf-8", newline="") as f:
    f.write(text)
arch_hdr = ("\n# --- R2020 fold append (2026-10-18, 3 lines verbatim: fold R549 roll line + R2019 round "
            "+ R2019 tokens (R2019 = 36th-case takeover closeout: statsmonth re-place bounce persist "
            "suite landed with personal green re-verification; this R2020 fold archives the takeover "
            "closeout spectrum before the W27 crawl round appends), fold R550 window, pre-op sha16 "
            + preop_sha16 + ")\n")
with io.open(ARCHIVE, "a", encoding="utf-8", newline="") as f:
    f.write(arch_hdr)
    for l in tail_lines:
        f.write(l + "\n")

# --- mechanical token catalog from the 3 folded lines ---
tok_pat = re.compile(r"\b(?:AC|OH|BD|SD|XL|C|D|O|P|R|T|F|U|N|K|Q|MSG|HQ|J)-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")
toks = set()
for l in tail_lines:
    for m in tok_pat.findall(l):
        toks.add(m)
catalog = "|".join(sorted(toks))

# --- build the rolling line (fold R550) ---
rolling = ("2026-10-18 R2020 \u6536\u8d26\u8c31\u6eda\u7a97\u6536\u62e2\u884c\u00b7fold R550 \u627f R2020 "
           "\u6536\u8d26\u524d\u7f6e\u88c1\u5b9a\u5151\u73b0\uff08\u672c\u8f6e\u6536\u8d26\u524d gauge \u5b9e\u6d4b state "
           + str(gauge) + "B+R2020 round+tokens \u6536\u8d26\u9884\u7b97\u5fc5\u8d8a 78500B \u7ebf\uff1dP-2026-09-25-18 "
           "\u7b2c\u4e94\u767e\u4e94\u5341\u5200\u00b7\u5f00\u7a97\u5e8f=fold \u5148\u4e8e\u672c\u8f6e\u6536\u8d26 append"
           "\uff08R2018/R2019 \u540c\u4f4d\u5148\u4f8b\uff09\u00b7\u7a97=tail 3\uff1afold R549 \u6eda\u7a97\u884c+R2019 round line"
           "+R2019 tokens\uff1d3 \u884c " + str(folded_bytes) + "B \u538b 1 \u6eda\u7a97\u884c kept=0\u00b7" + str(len(toks))
           + " token \u5168\u5b57\u9762\u5d4c\u96f6\u4e22\u5931\uff08catalog \u673a\u68b0\u63d0\u53d6\u96f6\u624b\u6284\u00b7\u751f\u6210"
           "\u5668\u7a0b\u5e8f\u5316\u62fc\u63a5 gen550\uff09\u00b7\u539f\u6587\u5168\u91cf\u4fdd\u5168=archive \u00a7R2020 \u8282 3 \u884c "
           "verbatim+preop \u5907\u4efd\u4ef6 logs/state-preop-R2020.bak+git \u53f2\uff09\u2014\u2014\u627f\u524d\u6eda\u7a97\u6ce8\u8bb0\uff1a"
           "fold R549 \u6eda\u7a97\u884c\uff08\u627f fold R548\u3014R2008..R2016 \u8c31\u7cfb\u3011+R2017/R2018 \u4e3b\u7ebf\uff09\u5df2\u6298\u5165"
           "\u672c\u884c\uff0c\u5176 token \u57df\u5168\u5b57\u9762\u968f\u884c\uff08\u5404\u8f6e\u8be6\u7ec6\u53d9\u4e8b live verbatim in "
           "archive \u5bf9\u5e94\u8282\uff09\u2014\u2014R2019 \u4e3b\u7ebf=R2019 round line\uff08showcase statsmonth "
           "re-place \u56de\u5f39 persist \u4f8b\u7a97\u00b736th-case \u5d29\u8f6e\u63a5\u7ba1\u6536\u53e3\u00b7AC-SSMRP1..SSMRP7 "
           "\u5168\u8fc7\u00b7SUITE 7/7 \u53cc\u8dd1 sha16 8ec2106227a9816f\u00b7RUNNER PASS 236/236 \u5224\u636e 2004\u21922011\uff09"
           "\u2014\u2014catalog: " + catalog)

round_line = ("2026-10-18 R2020\uff08\u4e94\u9759\u68c0\u51fa=[DEC] FLAG \u65b0 token D-20261018-01 BigCompute "
              "\u590d\u5f79\u770b\u62a4\u5b9a\u8c23\u3010\u6279\u6ce8\u968f\u4ef6\u660e\u793a\u300cBigDomain "
              "\u96f6\u65b0\u5f85\u62cd\u677f\u300d+\u6267\u884c\u53f8=\u591c\u8f6e 03:07\u2192\u975e\u672c\u53f8\u6267\u884c\u9762\u77e5\u6089"
              "\u4e0d\u52a8\u4f5c\u00b7\u672c\u884c\u5373\u56de\u6267\u5f15\u7528 D-20261018-01\u3011\u57fa\u7ebf\u5e76\u5408 rows "
              "356\u2192360+[GORD] \u6587\u4ef6\u5c3e\u6279 10-18 01:53..13:5x \u4e94\u884c\u5168=MV \u4ea7\u7ebf\u57df\u6d3e\u5de5"
              "\u3010@bm-c \u661f\u6674\u5c31\u5730 INT8 \u76f4\u70e7/@bm-b whisper \u8bcd\u951a/bm-d V100 "
              "\u6269\u5bb9\u00b7\u96f6 BigDomain \u6267\u884c\u9762\u3011\u2192\u77e5\u6089\u4e0d\u52a8\u4f5c\u00b7last_order "
              "\u57fa\u7ebf 2026-10-17 13:5x\u21922026-10-18 13:5x\u00b7GORD 455 \u6301\u5e73 gord_new_rows=0+[QA] "
              "FLAG=R2019 \u9057\u7559\u672c\u8f6e\u9996\u9879\u7167\u529e\u2192QA charter \u6bcf\u65e5 crawl \u8f6e\u5168\u4ef6\u4ea4\u4ed8\uff1a"
              "\u2460\u5bf9\u8d26\u65e5\u5e38\u5316\u5e38\u8bbe\u884c\u5f53\u65e5\u6267\u884c\u5151\u73b0=python "
              "src/sandbox/reconcile_daily.py\u2192RECONCILE-DAILY 20261018 verdict=PASS exit=0 runner_exit=0 "
              "sentinel=ok profile=ok census=ok\u00b7RUNNER PASS 236/236 \u5957\u4ef6+reconcile controls 7/7 226.1s"
              "=qa/reconcile-daily-20261018.log\u3010\u5f53\u65e5\u95ed\u73af\u96f6\u5347\u7ea7\u00b7\u5e38\u8bbe\u884c\u7eed\u884c\u3011\uff1b"
              "\u2461W27 \u4fe1\u53f7\u6e90\u76f4\u91c7=search \u5b9a\u4f4d 1 \u8bd5+\u5b98\u65b9\u5168\u6587 1 \u5f97 0 "
              "\u5224\u8d1f=\u300a\u5177\u6709\u8206\u8bba\u5c5e\u6027\u6216\u793e\u4f1a\u52a8\u5458\u80fd\u529b\u7684\u4e92\u8054\u7f51\u4fe1\u606f"
              "\u670d\u52a1\u5b89\u5168\u8bc4\u4f30\u89c4\u5b9a\u300b\u3010A \u7ea7 gov.cn/zhengce/zhengceku/2018-11/30/"
              "content_5457763\u00b7\u56fd\u52a1\u9662\u653f\u7b56\u6587\u4ef6\u5e93\u00b7\u7f51\u4fe1\u529e+\u516c\u5b89\u90e8 "
              "2018-11-15 \u53d1\u5e03\u00b72018-11-30 \u65bd\u884c\u00b717 \u6761\u9010\u6761\u6838\u5bf9\u3011\u2192benchmarks "
              "\u00a7\u2460 \u8206\u8bba\u52a8\u5458\u5b89\u5168\u8bc4\u4f30\u6cd5\u89c4\u5757+\u00a7\u2461 \u6267\u884c\u6807\u51c6\u884c 11+"
              "\u00a7\u2462 \u6e90\u884c+\u00a7\u2463 \u8bb0\u5f55\u884c\u56db\u5904\u5165\u518c+intelligence-wall W27 "
              "\u53cc\u884c\u3010\u4e3b\u884c+\u7ed3\u8bba\u884c\u00b7R1884 \u5148\u4f8b\u3011+benchmarks_refreshed=2026-10-18\uff1b"
              "\u2462\u6d88\u8d39\u843d\u70b9=launch-ops \u4e0a\u7ebf\u95f8\u5b89\u5168\u8bc4\u4f30\u6b65\u9aa4\u6cd5\u6e90\u6b63\u8eab"
              "\u3010W13\u300c\u65b0\u529f\u80fd\u4e0a\u7ebf\u5b89\u5168\u8bc4\u4f30\u95f8\u300d\u5019\u9009\u6536\u53e3\u3011+P-47\u2460 "
              "\u5927\u5385\u3010\u5c0f\u7a0b\u5e8f/\u804a\u5929\u5ba4/\u901a\u8baf\u7fa4\u7ec4\u9002\u7528\u57df+\u65e5\u5fd7\u7559\u5b58\u3011+P-47\u2462 "
              "UGC\u3010\u8fdd\u6cd5\u4fe1\u606f\u5904\u7f6e\u8bb0\u5f55+AIGC \u65b0\u6280\u672f\u65b0\u5e94\u7528\u53d8\u66f4\u8bc4\u4f30\u3011+"
              "bootstrap\u3010\u5168\u56fd\u4e92\u8054\u7f51\u5b89\u5168\u7ba1\u7406\u670d\u52a1\u5e73\u53f0\u8d26\u53f7+\u5730\u5e02\u7ea7"
              "\u7f51\u4fe1/\u516c\u5b89\u63d0\u4ea4\u901a\u9053=\u63a5\u7ebf\u7a97\u524d\u7f6e\u4ef6+\u7b2c\u4e94\u6761\u2460\u7f16\u5236\u9762"
              "\u7b2c\u4e03\u6cd5\u6e90\u3011\uff1b\u2463\u8bc1\u636e\u5bf9=qa/smoke-R2020.log+qa/smoke-R2020.png"
              "\u3010render \u771f log \u6e32\u67d3\u3011+\u81ea\u9a8c\u6e05\u5355\u56db\u9879\u5bf9\u7167\u3010\u6bcf\u65e5 crawl W27 "
              "\u4ea4\u4ed8/benchmark 15h \u5f8b\u5f53\u65e5\u5df2\u5237/\u8c03\u7814\u6765\u6e90\u94fe A \u7ea7 1 \u8bd5 1 "
              "\u5f97\u96f6\u5224\u8d1f/\u4fe1\u53f7\u5899 W27 \u53cc\u884c\u5728\u4f4d\u3011\u2014\u2014score 2\u3010\u5f53\u65e5\u7535\u6c60 "
              "G0 \u7eff\u771f\u8dd1 236 \u5957\u4ef6+W27 \u6cd5\u6e90\u4ea7\u54c1\u7ba1\u7ebf\u56db\u5904\u5165\u518c\u3011\u00b7export "
              "\u5237\u65b0 R2020 \u884c")

tokens_line = ("R2020 tokens: local=~1.5M api=0 api_reason=five-silence scan + QA charter crawl round all "
               "local (daily reconcile battery 236 suites 226.1s + local session search/fetch + benchmarks "
               "4-place + intelligence-wall dual rows + fold R550 gen/execute + state/heartbeat/export edits "
               "+ smoke log/png + directed commit), zero cloud calls")

for s in (rolling, round_line, tokens_line):
    if '"' in s or "\\" in s:
        sys.exit("FATAL: illegal char in new line")

# --- replace tail-3 with rolling + append R2020 pair ---
new_items = [indent + '"' + rolling + '",',
             indent + '"' + round_line + '",',
             indent + '"' + tokens_line + '"']
lines[t3[0]:t3[2] + 1] = new_items
text = "\n".join(lines)

# --- top-field updates (byte-surgical) ---
def sub_once(pat, rep, label):
    global text
    new, n = re.subn(pat, rep, text, count=1)
    if n != 1:
        sys.exit("FATAL: field edit failed: " + label)
    text = new

sub_once(r'"tick": 2019', '"tick": 2020', "tick")
sub_once(r'"last_order": "2026-10-17 13:5x"', '"last_order": "2026-10-18 13:5x"', "last_order")
sub_once(r'"last_decision_rows": 356', '"last_decision_rows": 360', "last_decision_rows")
sub_once(r'"benchmarks_refreshed": "2026-10-17"', '"benchmarks_refreshed": "2026-10-18"', "benchmarks_refreshed")
if "D-20261018-01" in text.split('"log"')[0]:
    sys.exit("FATAL: D-20261018-01 already in dec tokens")
sub_once(r'("last_dec_tokens": ")([^"]*)(")',
         lambda m: m.group(1) + m.group(2) + ",D-20261018-01" + m.group(3), "last_dec_tokens")

# --- validate ---
json.loads(text)  # raises on bad json

with io.open(STATE, "w", encoding="utf-8", newline="") as f:
    f.write(text)
final_bytes = len(text.encode("utf-8"))

# --- heartbeat row ---
now = datetime.now()
hb_line = ("2026-10-18 %02d:%dx +08:00 | BigDomain OSLoop alive | tick 2020 | R2020: QA charter daily crawl "
           "round + same-day daily-reconcile standing row executed. (1) Daily reconcile battery: RECONCILE-DAILY "
           "20261018 verdict=PASS runner_exit=0 sentinel=ok profile=ok census=ok, RUNNER PASS 236/236 suites "
           "green + reconcile controls 7/7 in 226.1s = qa/reconcile-daily-20261018.log. (2) W27 legal-source "
           "harvest: Regulations on Security Assessment for Internet Information Services with Public-Opinion "
           "or Social-Mobilization Attributes (CAC+MPS, issued 2018-11-15, effective 2018-11-30, 17 articles) "
           "official fulltext A-grade direct-captured from gov.cn policy library (1-try search + 1-get, zero "
           "negatives), consumed into benchmarks sections 1/2/3/4 (new regulatory block + execution-standard "
           "row 11 + source row + record row) + intelligence-wall W27 dual rows; scope-of-application art. 2 "
           "directly names mini-programs/chatrooms/group messaging = our visitor mini-program and lobby rooms; "
           "art. 3 pre-launch/pre-new-function assessment gate + art. 7 platform submission before launch or "
           "within 30 working days + art. 13 public risk notice for refusal = launch-ops SOP security-assessment "
           "step statute body (closes the W13 candidate). benchmarks_refreshed=2026-10-18. (3) Group faces: "
           "DEC D-20261018-01 (BigCompute restoration-watch, explicit zero-BigDomain pending) acked no-action; "
           "group orders tail batch 10-18 01:53..13:5x all MV-lane dispatches acked no-action, baseline "
           "last_order -> 2026-10-18 13:5x. (4) fold R550 closeout-precedent honored (tail-3 -> one rolling "
           "line, %d tokens embedded zero-loss, archive verbatim + preop backup). Score 2."
           % (now.hour, now.minute // 10, len(toks)))
with io.open(HB, "a", encoding="utf-8", newline="") as f:
    f.write("\n" + hb_line + "\n")

print("FOLD-OK gauge=%dB folded=%dB tokens=%d preop_sha16=%s" % (gauge, folded_bytes, len(toks), preop_sha16))
print("STATE-FINAL=%dB (predicted %dB)" % (final_bytes, gauge - folded_bytes + sum(len(x.encode("utf-8")) + 1 for x in new_items) - 1 + 0))
print("HB-APPENDED tick=2020")
