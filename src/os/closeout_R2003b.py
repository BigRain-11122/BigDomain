import io, json, re, datetime, sys

ROOT = r'C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain'
CST = datetime.timezone(datetime.timedelta(hours=8))
NOW = datetime.datetime.now(CST)
STAMP_ISO = NOW.strftime('%Y-%m-%dT%H:%M:%S+08:00')

# ---- 0. timestamp correction in the md rows written in part 1 ----
for p in (r'\docs\global-benchmarks.md', r'\docs\research\intelligence-wall.md'):
    t = io.open(ROOT + p, 'r', encoding='utf-8', newline='').read()
    t2 = t.replace(u'~05:xx', u'~02:5x').replace(u'~05:5x', u'~02:5x')
    io.open(ROOT + p, 'w', encoding='utf-8', newline='').write(t2)
print('ts corrected to 02:5x')

# ---- 1. smoke evidence pair ----
SMOKE = """BigDomain QA smoke evidence - round R2003 - 2026-10-17 +08:00
day work: (1) QA charter daily crawl for 2026-10-17 delivered this
round: W26 = Regulations on the Governance of Cyberbullying
Information (CAC/MPS/MCT/NRTA Order No. 17, signed 2024-06-12,
effective 2024-08-01, 7 chapters 34 articles), official fulltext
direct-captured from cac.gov.cn (A-grade, search located 1 try +
fulltext 1 get, zero negatives), consumed into benchmarks sections
1/2/3/4 + intelligence-wall W26 dual rows (main + conclusion, R1884
dual-row precedent); benchmarks_refreshed=2026-10-17 (next 7-day
window 2026-10-24; charter 15h cap met same day). Candidate-erratum
pair honestly noted: the consumer-protection-regulation candidate was
already on record as W10, and the comment-service candidate was
already on record as W13 (the 2022 revision - the 2017 text fetched
first had been repealed by it, caught before recording).

--- (1) W26 crawl (group QA Smoke Test charter v1.0, orders L254
2026-09-28; docs/global-benchmarks.md + docs/research/intelligence-wall.md) ---
key clauses consumed: art. 8 real-name fail-closed for
publish/instant-messaging services + account-auth assistance for
victims; art. 10 three prohibitions (cyberbullying illegal info,
heat-riding marketing speculation, batch-registration/account-
manipulation organization) = third anti-farm statute source; arts.
12-14 feature library + warning model (7 factors) + abnormal-account
dynamic verification + credit-management blacklist; arts. 15/18/19/21
stop-transmit + comment/reply/message/barrage/like disposition ladder
+ group-owner management duty + blacklist no-reregister + marketing
profit-suspension; arts. 23-27 protection mechanisms (blocking
options + private-message rules + quick forensics + dedicated quick
complaint entry + minors priority + notice-and-delete channel);
art. 30 penalty tiers 10k-200k CNY; art. 32 definition; art. 33
lawful-reporting carve-out. Consumption: P-47(1) lobby [real-name +
comment disposition + group duty + protection options + forensics/
evt_id logging] + P-47(3) UGC [feature library + stop-transmit +
quick-report entry] + P-47(2) anti-farm [art. 10 third source +
credit blacklist] + bootstrap [quick-report entry + forensics =
wiring-window hard prerequisite candidates].

--- (2) P2 claim (R1780 AC-OW2 observation-window adjudication row,
2026-10-16 governance-window gate arrived) ---
mechanical counter: grep of live-step marker lines across all daily
evidence logs = 11 markers, all "profile exit=0 (observation-window:
recorded, not gating)", plus 4 suite-level FAIL judgment lines
excluded per AC-OW3 (the 10-11 morning double-FAIL was a
test-fixture defect, not a drift reading) -> drift FLAG count == 0
-> AC-OW2 branch (1) holds: observation window maintained (not
promoted to gating, PROFILE_OBSERVATION_WINDOW unchanged), 7-day
rolling re-evaluation continues, next window 2026-10-24, threshold
caliber = AC-RP4 family zero-change. Successor rolling-re-eval seed
row registered in state/queue/tech.md.

--- (3) five-silence deltas honestly noted ---
DEC 2 new owner tokens judged (D-20261017-01 committee process-rules
overhaul v2 + D-20261017-02 three-dim fleet resource allocation
enforcement - both non-BigDomain dispatch faces, acknowledged
no-action; baselines rows 282->348, tokens merged; D-20261017-02
clause-1 spawn-gate fix pattern landed in bigmoney = the R2002-held
adaptation trigger -> tech-queue adaptation seed row registered).
ORD 3 new rows after the 00:5x baseline (01:1x / 01:2x / 02:1x all
MV-domain receipts, ack no-action, baseline -> 2026-10-17 02:1x,
GORD 571->455 table-format caliber drift noted). HB debt collected:
the R2002 heartbeat row lacked the tick marker (scan [HB] false-red
root) - this round's row carries tick 2003 in the canonical form,
history not rewritten. fold R536 pre-closeout honored (round-start
gauge 76257B + two-line budget over the 78500 line -> tail-3 window
[fold R535 rolling line + R2002 pair] folded to one rolling line,
19 tokens mechanically embedded zero-loss, archive section R2003
verbatim + preop backup, post 73103B == predicted).

--- (4) self-check four items vs charter ---
daily crawl = W26 delivered this day; benchmark refreshed = 2026-10-17
(next 7-day window 2026-10-24; charter 15h cap met same day); research
chain = A-grade 1-try search + 1-get fulltext, zero negatives, zero
repealed-text mistakes (candidate-erratum pair caught pre-record);
signal wall = W26 dual rows in place (main + conclusion). evidence
pair = this log + rendered png.
"""
io.open(ROOT + r'\qa\smoke-R2003.log', 'w', encoding='utf-8', newline='\n').write(SMOKE)

from PIL import Image, ImageDraw, ImageFont
font = ImageFont.truetype(r'C:\Windows\Fonts\consola.ttf', 15)
wrapped = []
for raw_line in SMOKE.split('\n'):
    line = raw_line.rstrip()
    if not line:
        wrapped.append('')
        continue
    while len(line) > 112:
        wrapped.append(line[:112])
        line = line[112:]
    wrapped.append(line)
while wrapped and wrapped[-1] == '':
    wrapped.pop()
PAD, LINE_H, width = 26, 22, 1180
height = PAD * 2 + LINE_H * len(wrapped)
img = Image.new('RGB', (width, height), (26, 26, 26))
draw = ImageDraw.Draw(img)
y = PAD
for ln in wrapped:
    draw.text((PAD, y), ln, fill=(216, 216, 216), font=font)
    y += LINE_H
img.save(ROOT + r'\qa\smoke-R2003.png')
print('smoke pair written: log %dB, png %dx%d' % (len(SMOKE.encode('utf-8')), width, height))

# ---- 2. state.json byte surgery ----
P = ROOT + r'\src\os\state.json'
raw = io.open(P, 'r', encoding='utf-8', newline='').read()
orig_len = len(raw.encode('utf-8'))

def rep1(text, old, new, label):
    n = text.count(old)
    assert n == 1, 'anchor %r count=%d' % (label, n)
    return text.replace(old, new, 1)

raw = rep1(raw, '"tick": 2002', '"tick": 2003', 'tick')
raw = rep1(raw, '"last_order": "2026-10-17 00:5x"', '"last_order": "2026-10-17 02:1x"', 'last_order')
raw = rep1(raw, '"last_gord_tbl_rows": 571', '"last_gord_tbl_rows": 455', 'gord')
raw = rep1(raw, '"last_decision_rows": 282', '"last_decision_rows": 348', 'decrows')
raw = rep1(raw, '"benchmarks_refreshed": "2026-10-15"', '"benchmarks_refreshed": "2026-10-17"', 'bench')
m = re.search(r'"last_dec_tokens": "([^"]*)"', raw)
assert m, 'last_dec_tokens not found'
raw = raw[:m.end(1)] + ',D-20261017-01,D-20261017-02' + raw[m.end(1):]

R2003_LINE = (u'2026-10-17 R2003（五静扫描非全静：DEC 2 新 token 判毕〔D-20261017-01 修法包 v2 委员会流程规则全量梳理=bm-c 集团治理面零 @BigDomain 派工=知悉不动作；D-20261017-02 机队三维资源极致分配执法案=拍板五件全 bm-c/bm-a/bm-b 域=知悉不动作+①闸门修法〔参数无头 -p 面貌·bigmoney 63943e50b 实测 live=0·fail-open 保持〕=本司 R2001 spawn 闸同缺陷的修法 spec 到位→tech 队列适配种子行入列〔诚实注：本司 loop 逐轮 api=0 纯本地·R2001 实测 live=7 假计数让路面在册〕·基线 rows 282→348+token 并入〕+ORD 新 3 行〔10-17 01:1x/01:2x/02:1x=@bm-c 星晴 T1 海选两级海审+@bm-a POOL-0013 轮播收编+@bm-a 星晴 T1 对审签章=全 MV 域零 BigDomain 执行面=知悉不动作·基线 last_order 00:5x→02:1x+GORD 571→455〔表格式口径漂移如实注〕〕——P2 认领=daily 剖面步观察窗转正裁定执行窗〔R1780 AC-OW2 机械三支·10-16 治理窗门已到〕：裁定计数器=live-step 标记行全仓机械 grep 11 条全 exit=0+套件级判行 4 条按 AC-OW3 不入计数→**支①成立：维持观察窗不转正·续 7 天滚动复评（下窗 2026-10-24）**·阈值口径=AC-RP4 家族式零改动·滚动复评种子行入列——[QA] FLAG 修复=W26 法规片直采（集团 charter 每日 crawl 份）：候选勘误两枚如实注〔①消保法实施条例=W10 在册撞车②跟帖评论规定=W13 在册 2022 修订版·2017 版已废止=拦下〕→终选=**《网络暴力信息治理规定》官方全文**（四部门令第17号·2024-06-12 公布·2024-08-01 施行·7 章 34 条·A 级 cac.gov.cn/2024-06/14/c_1720043894161555 官网全文页·search 定位 1 试 1 得零判负）→benchmarks 四节入册〔§①网暴法规块+§②执行标准行 10+§③源行+§④记录行〕+intelligence-wall W26 主行+结论行（R1884 双行先例）+消费落点=P-47① lobby〔第八条实名+第十八条评论/弹幕/点赞处置+第十九条群组管理者责任 W14 同向+第二十三条防护选项/私信规则+第二十五条快捷取证/evt_id 日志〕+P-47③ UGC〔第十二条特征库+第十五条立即停止传输+第二十六条快捷举报入口〕+P-47② anti-farm〔第十条批量注册/操纵账号/营销炒作三禁第三法源+第十四条信用黑名单〕+bootstrap〔快捷举报入口+取证=接线窗硬前置候选〕·证据对=qa/smoke-R2003.log+png〔render 自 log 渲染〕·benchmarks_refreshed=2026-10-17〔7 天窗下轮 10-24·charter 15h 帽当日刷新〕——HB 债收口=R2002 心跳行缺 tick 标记（scan [HB] 面假红根因）·本轮心跳行带 tick 2003 正格式入册〔史行不改写〕——fold R536 收账前置兑现〔轮首 gauge 76257B+收账两行必越 78500 线→tail-3 窗〔fold R535 滚窗行+R2002 双行〕压 1 滚窗行·19 token 机械提取全字面嵌零丢失·archive §R2003 verbatim+preop logs/state-preop-R2003.bak·post 73103B==predicted〕·P3 explore 队头〔civic 竞赛榜月份窗跨重启持久化例窗〕本轮未认领诚实注〔裁定+爬取+fold 占满轮预算〕·score 2〔转正裁定件+法规片=产品管线完整性件·诚实注零新可跑产品例窗〕）')
R2003_TOKENS = (u'R2003 tokens: local=~0.7M api=0 api_reason=five-silence scan + DEC 2-token judge + ORD 3-row sweep + P2 adjudication mechanical grep + W26 legal-source web direct-capture (search 1-try + fulltext 1-get, zero negatives, candidate-erratum pair caught pre-record) + benchmarks 4-section + wall dual-row + smoke-pair writes + fold R536 compose/execute + closeout surgery + directed commit, zero cloud calls')

# post-fold tail: the last log item is the fold R536 rolling line; anchor = log array close
tail_anchor = '\r\n    ]'
idx2 = raw.rindex(tail_anchor)
assert raw[idx2-1] == '"', 'log array close anchor mismatch'
eol = '\r\n'
insert = (',' + eol + ' ' * 16 + json.dumps(R2003_LINE, ensure_ascii=False)
          + ',' + eol + ' ' * 16 + json.dumps(R2003_TOKENS, ensure_ascii=False))
raw = raw[:idx2] + insert + raw[idx2:]
json.loads(raw)  # syntax check
io.open(P, 'w', encoding='utf-8', newline='').write(raw)
print('state.json surgery ok: %dB -> %dB' % (orig_len, len(raw.encode('utf-8'))))

# ---- 3. heartbeat row (canonical form with tick marker) ----
hb = io.open(ROOT + r'\heartbeat.txt', 'r', encoding='utf-8', newline='').read()
hbeol = '\r\n' if '\r\n' in hb else '\n'
if not hb.endswith(hbeol):
    hb += hbeol
hb += (u'2026-10-17 02:5x +08:00 | BigDomain OSLoop alive | tick 2003 | R2003: W26 cyberbullying-regulation crawl (Order No.17, 34 articles, benchmarks 4-section + wall dual rows + smoke pair, benchmarks_refreshed 10-17); DEC D-20261017-01/02 acked non-BD + ORD 3 MV rows acked (baselines ORD 02:1x/GORD 455/DEC 348); P2 AC-OW2 adjudication branch-1 (window maintained, re-eval 10-24); spawn-gate adaptation seed; HB tick backfill; fold R536 (19 tokens, 73103B); score 2 [via BigDomain-OSLoop]' + hbeol)
io.open(ROOT + r'\heartbeat.txt', 'w', encoding='utf-8', newline='').write(hb)
print('heartbeat row appended with tick 2003')

# ---- 4. export refresh ----
EP = ROOT + r'\docs\status-export.json'
ex_raw = io.open(EP, 'r', encoding='utf-8', newline='').read()
ex_eol = '\r\n' if '\r\n' in ex_raw else '\n'
ex = json.loads(ex_raw)
ex['export_ts'] = STAMP_ISO
ex['ceo_face']['current'] = ("R2003: DEC D-20261017-01/02 judged non-BigDomain acked (rows 282->348) + ORD 3 new MV-domain rows acked (baseline ORD 2026-10-17 02:1x, GORD 455) + P2 claim: R1780 AC-OW2 observation-window adjudication executed (drift FLAG count=0 -> branch 1, window maintained, rolling re-eval 2026-10-24) + W26 cyberbullying-regulation crawl delivered (Order No.17 fulltext, benchmarks 4-section entry + wall dual rows + smoke pair, benchmarks_refreshed 2026-10-17) + spawn-gate adaptation seed (D-20261017-02 fix pattern) + HB tick-2003 backfill + fold R536. Score 2.")
ex['ceo_face']['latest_artifact'] = "qa/smoke-R2003.log + qa/smoke-R2003.png (W26 crawl evidence pair, 2026-10-17)"
ex['ceo_face']['next_milestone'] = ("P3 explore queue head: civic honor-competition month-window cross-restart persistence example (R1999 reseed) claimable from next round, window <=48h (by 2026-10-19); AC-OW2 rolling re-eval window 2026-10-24")
res = ex['results']
new_row = ["R2003",
           "R2003: W26 cyberbullying-regulation crawl delivered (group QA charter daily-crawl face): Regulations on the Governance of Cyberbullying Information (four-department Order No. 17, effective 2024-08-01, 7 chapters 34 articles) official fulltext A-grade direct-capture from cac.gov.cn (1-try search + 1-get, zero negatives), consumed into benchmarks sections 1/2/3/4 + intelligence-wall W26 dual rows; candidate-erratum pair caught pre-record (consumer-protection reg = W10 already on record; comment-service reg = W13 on record in the 2022 revision, the fetched 2017 text repealed); evidence pair qa/smoke-R2003.log+png; benchmarks_refreshed=2026-10-17. P2 claim: the R1780 AC-OW2 observation-window adjudication row (gate arrived with the 2026-10-16 governance window) executed mechanically - live-step marker grep = 11 markers all exit=0, suite-level FAIL lines excluded per AC-OW3 -> drift FLAG count==0 -> branch (1): observation window maintained, rolling re-eval next window 2026-10-24; successor seed row registered. Five-silence deltas: DEC D-20261017-01 (committee process-rules overhaul v2) + D-20261017-02 (three-dim fleet resource allocation) both judged non-BigDomain dispatch faces, acked no-action (rows 282->348, tokens merged; D-20261017-02 clause-1 spawn-gate fix pattern = the R2002-held adaptation trigger -> tech-queue adaptation seed row); ORD 3 new rows 01:1x/01:2x/02:1x all MV-domain acks (baseline -> 2026-10-17 02:1x, GORD 571->455 format-caliber drift); HB debt collected (R2002 heartbeat row lacked the tick marker - this round's row carries tick 2003, history not rewritten); fold R536 pre-closeout (tail-3 window [fold R535 rolling line + R2002 pair] -> one rolling line, 19 tokens embedded zero-loss, post 73103B == predicted). P3 explore head not claimed - honest note: adjudication + crawl + fold consumed the round budget. Score 2 (adjudication piece + legal-source crawl = product-line integrity pieces; honest note: zero new runnable product suite this round)."]
ex['results'] = [new_row] + res
for row in ex['results']:
    if len(row) == 2 and row[0] == '2002' and row[1] == u'OSLoop 执行 tick':
        row[0] = '2003'
ex['self_drive']['log_lines_in_window'] = ex['self_drive']['log_lines_in_window'] + 1
ex['self_drive']['queue_tech_open'] = 6
ex_raw2 = json.dumps(ex, ensure_ascii=False, indent=2)
if not ex_raw2.endswith('\n'):
    ex_raw2 += '\n'
ex_raw2 = ex_raw2.replace('\n', ex_eol) if ex_eol == '\r\n' else ex_raw2
io.open(EP, 'w', encoding='utf-8', newline='').write(ex_raw2)
print('export refreshed, ts=' + STAMP_ISO)

# ---- 5. verify battery: export consistency checker ----
import subprocess
p = subprocess.run([sys.executable, ROOT + r'\src\os\check_export_consistency.py', '--out', ROOT + r'\qa\export-consistency-R2003.log'],
                   capture_output=True, cwd=ROOT)
print('consistency rc=%d' % p.returncode)
tail = p.stdout.decode('utf-8', errors='replace').strip().split('\n')
for ln in tail[-12:]:
    print('CHK:', ln)
