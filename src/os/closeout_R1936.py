"""R1936 closeout: orphan-payload takeover + W24 daily-crawl smoke.

Crashed R1936 attempt left the full delivery on disk (suite + registry +
matrix + five-section evidence + the 2026-10-14 daily reconcile, zero
failed-run artifacts); this window verified live and closes out:
tech.md done-note + venue reseed, state.json tick/log, benchmarks W24
block, intelligence-wall W24 rows, smoke evidence pair, export refresh.
All edits anchor-exact with fail-fast asserts; EOL preserved per file."""

import datetime as _dt
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))


def read_txt(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        raw = fh.read()
    return raw.decode("utf-8")


def write_txt(rel, text):
    with open(os.path.join(ROOT, rel), "wb") as fh:
        fh.write(text.encode("utf-8"))


def eol_of(text):
    return "\r\n" if "\r\n" in text else "\n"


def must_count(text, needle, n, what):
    c = text.count(needle)
    assert c == n, "anchor %r count=%d expected=%d (%s)" % (needle, c, n, what)


# ---------------------------------------------------------------- tech.md
P_TECH = "state/queue/tech.md"
tech = read_txt(P_TECH)
NL = eol_of(tech)
claim_tail = "——〔2026-10-14 R1936 认领〕"
must_count(tech, claim_tail, 1, "observation claim tail")
done_note = (
    "——[done 2026-10-14 R1936]（执行注记：**孤儿载荷接管收口轮**"
    "〔R1922/R1924/R1925/R1934 谱系〕——前窗崩溃 R1936 尝试留盘件="
    "套件+注册行+认领行+矩阵+证据五节+daily 对账 10-14 全在盘·"
    "零败跑工件·收账面独缺〔tech done 注/state/export/heartbeat/"
    "commit〕→本轮接管 live 复验〔套件重跑 SUITE PASS 7/7+矩阵 "
    "--check byte-identical〕后收口：套件 test_observation_persist.py "
    "SUITE 7/7+双跑 stdout 逐字节同一 sha16 0ae114d64e2d4703〔rc 0/0〕"
    "三实例世界——①锚世界〔mint 20000+四账户注资 alice 2000/bob 3000/"
    "carol 1000/dave 500+双策略注册结果面+alice 单笔永续 99+bob pass "
    "2099-01@199 两 grant 绑真 spend tx〔SQL 交叉 ledger_tx type="
    "'spend'+账户 debit 分录〕+四门探针全拒零扣费+十三读面五余额快照 "
    "digest c184654e4fe640cb+五表计数交叉〔strategies 2/grants 2/"
    "spend-tx 2/tx 7/entries 14〕②两件套逆序全 close→同 db 同 cfg 重开"
    "→十三读面+五余额逐字节复原〔registered_utc=盘面持久值零钟回显="
    "派生读面零内存态漂移〕③五门探针跨重启全拒〔dup 单笔/dup pass 同月/"
    "unknown/carol 无权/bob 窗外月〕+探针批前后计数与余额恒定④真径续写"
    "〔bob buy_pass 2099-02@199+dave buy_single beta@49→两新 grant 绑真"
    "新 spend tx+派生面零缓存重算〔bob grants 1→2 月窗序 2099-01/2099-02+"
    "dave 0→1+observe bob@2099-02 kind=pass 新窗开+dave 远月 kind=single〕+"
    "表计数 grants 4/spend-tx 4/tx 9/entries 18〕⑤冻结面+窗隔离〔alice "
    "entitlements+observe==锚字节+carol 空脊==锚+strategy_view 双行==锚="
    "注册行不可变+bob 2099-01 pass 不罩 2099-03+alice 单笔永续跨重启远月 "
    "2099-12+carol 零渗透〕⑥纯读律〔电池双读+逐读三连计数恒定零副作用〕"
    "⑦实例③三开==实例②终态逐字节+config/observation/ledger sha16 三稳定"
    "〔32b018fad53fb8bc/f402f86fcd112163/4fcbe414fe9d7e5c〕+套件源纯 "
    "ASCII+世界 tmp 仓外〕——RUNNER PASS 174/174 判据 1550→1557 "
    "controls 7/7 251.4s=qa/reconcile-daily-20261014.log〔**双载体="
    "10-14 日戳 daily 对账=R1935 承传欠账当窗清偿**·sentinel ok+profile "
    "ok+census DRIFT-CLEAN flags=0〕+矩阵再生 174/1557 green --check "
    "byte-identical〔17105B〕——证据五节 qa/observation-persist-R1936."
    "log〔接管上下文+套件双跑+daily 载体摘录+矩阵+census〕·LF 归一单写者"
    "驱动=src/os/evidence_R1936.py〔R1932 模板族〕——tech consume 1 "
    "reseed 1〔queue_tech_open 10→10：observation done −1+ledger venue "
    "场地面读面族 persist 补种 +1·下轮 FIFO 队头=ledger expedite "
    "persist〕·产品零字节〔suite-only 轮〕）")
tech = tech.replace(claim_tail, claim_tail + done_note, 1)
venue_row = (
    "- [ ] ledger venue 场地面读面族跨重启持久化例窗"
    "（R1936 补种·查重前置已过：注册表 label 全形扫描零 venue-persist "
    "命名位 变体+套件源面扫描 test_venue.py 五 close 命中全为收尾清理"
    "非重启例=真活候选·AC-VNP 前缀全仓 git grep 零占用 2026-10-14"
    "〔rc=1〕·persist 例窗族 R1886 起谱系）")
obs_line_start = "- [x] ledger observation 观测面跨重启持久化例窗"
must_count(tech, obs_line_start, 1, "observation row head")
idx = tech.find(obs_line_start)
end = tech.find(NL, idx)
tech = tech[:end] + NL + venue_row + tech[end:]
write_txt(P_TECH, tech)
print("tech.md: done-note + venue reseed ok")

# ------------------------------------------------------------- state.json
P_STATE = "src/os/state.json"
state = read_txt(P_STATE)
SNL = eol_of(state)
must_count(state, '"tick": 1935,', 1, "tick")
state = state.replace('"tick": 1935,', '"tick": 1936,', 1)
must_count(state, '"benchmarks_refreshed": "2026-10-13",', 1, "bench date")
state = state.replace('"benchmarks_refreshed": "2026-10-13",',
                      '"benchmarks_refreshed": "2026-10-14",', 1)
must_count(state, '"last_gord_tbl_rows": 375,', 1, "gord rows")
state = state.replace('"last_gord_tbl_rows": 375,',
                      '"last_gord_tbl_rows": 376,', 1)
tok_anchor = '2026-10-14 R1935 tokens:'
must_count(state, tok_anchor, 1, "R1935 tokens anchor")
close_anchor = SNL + "    ]"
assert state.rstrip().endswith("}"), "state tail not }"
cidx = state.rfind(close_anchor)
assert cidx > state.find(tok_anchor), "log close before tokens anchor"
last_item_end = cidx  # position where "\n    ]" starts
prefix = state[:last_item_end]
assert prefix.endswith('"'), "last log item does not end with quote"
round_line = (
    "2026-10-14 R1936 ledger observation 观测面跨重启持久化例窗交付+"
    "崩溃轮孤儿载荷接管收口+QA charter W24 广告法规每日 crawl 轮"
    "（P2 tech FIFO=R1935 收账指针·轮计分 2=可跑实物）：五静扫描="
    "[QA] FLAG〔今日 smoke png/log 0+benchmarks 10-13 未刷=charter "
    "daily crawl 当日未做=本轮主修面〕+GORD 新 1 行〔10-13 23:5x "
    "@bm-c V3 修批两轮实况+QC 中继=BigStream MV 族 @bm-c 执行面零本司"
    "执行面→知悉不动作·基线 375→376 随收账〕+DEC PASS rows=309=基线"
    " 零新 owner token〔row_owner_tokens=124 如实注〕+LEDGER atbd=0+"
    "ORD 持平+BENCH 刷新窗内+HB lag=0+TREE 脏 7 件=崩溃轮孤儿载荷"
    "〔接管触发面〕——接管验真：留盘件六面 PRESENT〔套件+注册行+认领行"
    "已翻框+矩阵+证据五节+daily 对账 10-14〕+零败跑工件→本轮 live 复验"
    "〔套件重跑 SUITE PASS 7/7+矩阵 --check byte-identical〕后收口"
    "〔tech done 注+venue reseed+state/export/heartbeat+commit〕="
    "R1922/R1924/R1925/R1934 谱系第五例——判据 AC-OBP1..OBP7 预注册先于"
    "代码〔tech.md 认领行在册〕：套件 test_observation_persist.py "
    "SUITE 7/7+双跑 stdout 逐字节同一 sha16 0ae114d64e2d4703 三实例世界"
    "〔①锚世界〔四账户注资+双策略注册+alice 单笔永续+bob pass 窗 2099-01"
    " 绑真 spend tx+四门探针全拒+十三读面五余额快照 digest "
    "c184654e4fe640cb〕②两件套逆序全 close→同 db 同 cfg 重开电池逐字节"
    "复原〔registered_utc 盘面持久值零钟回显〕③五门探针跨重启全拒零漂移"
    "④真径续写 bob 2099-02+dave beta 绑真新 spend tx〔SQL 交叉〕+派生面"
    "零缓存重算⑤冻结面+窗隔离〔bob 2099-01 pass 不罩 2099-03+alice 远月"
    " 单笔永续+carol 零渗透〕⑥纯读律电池双读计数恒定⑦实例③三开==实例②"
    "终态逐字节+config/observation/ledger sha16 三稳定+纯 ASCII+tmp 仓外〕"
    "——RUNNER PASS 174/174 判据 1550→1557 controls 7/7 251.4s="
    "qa/reconcile-daily-20261014.log〔双载体=10-14 日戳 daily 对账="
    "R1935 承传欠账当窗清偿·sentinel ok+profile ok+census DRIFT-CLEAN "
    "flags=0〕+矩阵再生 174/1557 green --check byte-identical〔17105B〕"
    "——tech consume 1 reseed 1〔queue_tech_open 10→10：observation done "
    "−1+ledger venue 场地面读面族 persist 补种 +1〔查重预检：注册表零 "
    "venue-persist 位+test_venue.py 五 close 全非重启例+AC-VNP 全仓零"
    "占用〕·下轮 FIFO 队头=ledger expedite persist〕——QA charter 每日 "
    "crawl W24 片=《互联网广告管理办法》官方全文直采〔SAMR 令第 72 号·"
    "2023-02-25 公布·2023-05-01 施行·32 条·2016 暂行办法同时废止·"
    "samr.gov.cn 总局规章栏·search 1 试定位双证零判负〕：第九条可识别性+"
    "种草链接标广告+第十条弹窗一键关闭四禁+开屏适用+第十一条禁误导点击+"
    "第十二条未成年人媒介广告禁令+第十三至十五条档案 ≥3 年+算法推荐投放"
    "记录入档+第十六条平台六义务+第十七条禁扰推送+第十九条直播责任+罚则"
    "族〔5 千-5 万档〕→benchmarks §①广告法规块+§②行 9+§③源行+§④记录行"
    "+wall W24 双行〔主表+结论表〕→消费落点=P-47⑤ ads 广告位读面族"
    "〔tech 队列在册项法源直接供给〕+P-47③ UGC 种草标注+P-47② anti-farm "
    "虚假奖励禁令+未成年人广告层第四叠；benchmarks_refreshed=2026-10-14"
    "〔7 天周期下次 10-21〕+smoke-R1936.log/png〔render 真 log 渲染〕="
    "[QA] 面 smoke 证据对当日归位——产品零字节〔suite-only 轮〕·fold 承传"
    "注记：收账后 state 水位预测越 78500B 线=下轮轮首首测 fold R508 裁定"
    "〔R1898/R1908 fold 先行先例〕")
tokens_line = (
    "2026-10-14 R1936 tokens: local=unmeasured api=0 api_reason=纯本地"
    "进程件（五静扫描+接管验真+套件重跑+矩阵 check+收账手术全本地跑·"
    "W24 crawl=集团 charter 每日直采通道〔search+web fetch〕非 API 计费"
    "触点·三问门未涉及）")
new_block = ("," + SNL + '                "' + round_line + '",' + SNL
             + '                "' + tokens_line + '"')
state = prefix + new_block + state[last_item_end:]
parsed = json.loads(state.encode("utf-8").decode("utf-8"))
assert parsed["tick"] == 1936
assert len(parsed["log"]) >= 2
assert parsed["log"][-2].startswith("2026-10-14 R1936 ledger")
assert parsed["log"][-1].startswith("2026-10-14 R1936 tokens:")
assert parsed["benchmarks_refreshed"] == "2026-10-14"
assert parsed["last_gord_tbl_rows"] == 376
write_txt(P_STATE, state)
print("state.json: tick 1936, gord 376, bench 10-14, +2 log lines,",
      len(state.encode("utf-8")), "bytes")

# ------------------------------------------------- global-benchmarks.md
P_BENCH = "docs/global-benchmarks.md"
bench = read_txt(P_BENCH)
BNL = eol_of(bench)
ad_block = (
    "**互联网广告法规**（《互联网广告管理办法》·国家市场监督管理总局令"
    "第 72 号·2023-02-25 公布·**2023-05-01 施行**·32 条·2016《互联网"
    "广告管理暂行办法》同时废止·2026-10-14 A 级直采入册·R1936 QA W24 片）：")
ad_items = [
    "- **可识别性律（第九条）**：互联网广告应当具有可识别性，能够使消费者"
    "辨明其为广告＋竞价排名商品或服务显著标明「广告」与自然搜索结果明显区分"
    "＋**通过知识介绍、体验分享、消费测评等形式推销商品或服务并附加购物链接"
    "等购买方式的，广告发布者应当显著标明「广告」**——种草/测评带货标注条款"
    "=P-47③ UGC 商业内容标注面＋ads 广告位呈现面法源。",
    "- **弹窗一键关闭律（第十条）**：以弹出等形式发布互联网广告=显著标明"
    "关闭标志、确保一键关闭＋四禁〔无关闭标志或计时结束才能关闭／关闭标志"
    "虚假不可清晰辨识或难以定位／关闭广告须经两次以上点击／浏览同一页面同一"
    "文档过程中关闭后继续弹出〕＋**开屏广告适用前款规定**——与 W22 弹窗规定"
    "第五条八款叠为本司横幅/开屏广告面双层法源。",
    "- **禁误导点击（第十一条）**：虚假的系统或者软件更新、报错、清理、通知"
    "等提示＋虚假的播放、开始、暂停、停止、返回等标志＋**虚假的奖励承诺**"
    "＋其他欺骗、误导用户点击、浏览广告的方式——P-47② 代币/anti-farm 广告面"
    "禁令（虚假奖励=激励面红线）。",
    "- **未成年人媒介广告禁令（第十二条）**：针对未成年人的网站、网页、"
    "互联网应用程序、公众号等互联网媒介上不得发布医疗、药品、保健食品、"
    "特殊医学用途配方食品、医疗器械、化妆品、酒类、美容广告，以及不利于"
    "未成年人身心健康的网络游戏广告——未成年人面第四层叠（W11/W17/W22 后"
    "广告专属档）。",
    "- **广告档案律（第十三/十四/十五条）**：广告主自建渠道自行发布=广告"
    "发布者责任＋**广告档案保存 ≥3 年**；广告经营者、发布者=承接登记、审核、"
    "档案管理制度＋档案 ≥3 年＋配备广告审核人员或者设立广告审核机构；"
    "**利用算法推荐等方式发布互联网广告的，应当将其算法推荐服务相关规则、"
    "广告投放记录等记入广告档案**——ads 广告位读面族〔投放记录/审核/留存〕"
    "直接法源＋W17 算法推荐面叠加。",
    "- **平台六义务（第十六条）**：记录、保存发布广告用户真实身份信息 ≥3 年"
    "＋对发布广告内容监测、排查，发现违法广告采取通知改正、删除、屏蔽、"
    "断开发布链接等必要措施并保留记录＋建立投诉、举报受理和处置机制＋"
    "不得阻挠、妨碍广告监测＋配合调查如实提供身份/修改记录/交易信息＋"
    "依据服务协议和平台规则采取警示、暂停或者终止服务等措施——平台形态"
    "义务面〔P-47③ UGC 平台身份＋lobby 反馈面＋ads 监测面〕。",
    "- **禁扰推送（第十七条）**：发布、发送广告不得影响用户正常使用网络＋"
    "政务服务搜索结果中不得插入竞价排名广告＋**未经用户同意、请求或者用户"
    "明确表示拒绝的，不得向其交通工具、导航设备、智能家电等发送互联网广告"
    "＋不得在用户发送的电子邮件或者互联网即时通讯信息中附加广告或者广告"
    "链接**——W22 频次面同源补充档。",
    "- **直播责任（第十九条）**：直播推销构成商业广告=广告主责任；直播间"
    "运营者、直播营销人员受托=广告经营者、发布者责任；以自己名义或形象"
    "推荐证明=广告代言人责任——本司当前非直播形态如实注=预留法源。",
    "- **罚则族（第二十三至三十一条）**：弹窗未显著标明关闭标志未一键关闭"
    "=责令改正拒不改正处 5 千-3 万；欺骗误导点击=5 千-3 万；档案制度未建"
    "=广告法 60 条档；**互联网平台经营者违反第十六条=1 万-5 万**；明知应知"
    "违法广告不予制止=广告法 63 条；处罚决定依法公示＋性质恶劣情节严重="
    "列入严重违法失信名单。",
    "- 本司落点=**P-47⑤ ads 广告位读面族〔tech 队列在册项=W24 法源直接供给："
    "可识别标注＋一键关闭＋投放记录档案 ≥3 年＋审核面=例窗设计判据面〕**＋"
    "P-47③ UGC〔第九条种草链接「广告」标注＋第十六条平台监测处置〕＋P-47② "
    "anti-farm〔第十一条虚假奖励禁令〕＋未成年人广告层〔第四层叠〕"
    "（**2026-10-14 官方全文直采确认**：samr.gov.cn/zw/zfxxgk/fdzdgknr/"
    "fgs/art/2023/art_d93a579afd45413e8576e4623fab348f.html〔总局规章发布栏〕"
    "·32 条全文逐条核对·search 定位 1 试双证·零判负）。",
]
sec2_head = "## ②执行标准表"
must_count(bench, sec2_head, 1, "bench sec2 head")
insertion = ad_block + BNL + BNL.join(ad_items) + BNL + BNL
bench = bench.replace(sec2_head, insertion + sec2_head, 1)
row8_head = "| 8 | 发放原子性"
must_count(bench, row8_head, 1, "bench row 8")
r8_end = bench.find(BNL, bench.find(row8_head))
row9 = (
    "| 9 | 互联网广告可识别＋一键关闭＋投放档案 ≥3 年（W24·SAMR 令 72 号"
    "第九/十/十三至十五条） | 广告位呈现面显著标明「广告」＋关闭标志一键"
    "关闭（四禁形态 fail-closed）；算法推荐投放记录/审核/档案留存 ≥3 年="
    "ads 读面族设计判据 | `src/sandbox/ledger/test_ads.py`（ads 基础席 7 判据）"
    "＋ads persist 例窗〔tech 队列在册·W24 法源已入库〕·⬜例窗交付窗 | L3 |")
bench = bench[:r8_end] + BNL + row9 + bench[r8_end:]
ds_row_head = "| 数据安全法规 |"
must_count(bench, ds_row_head, 1, "bench sec3 ds row")
ds_end = bench.find(BNL, bench.find(ds_row_head))
ad_src_row = (
    "| 广告监管法规 | 《互联网广告管理办法》官方全文（国家市场监督管理总局令"
    "第 72 号·2023-02-25 公布·2023-05-01 施行·32 条·2016 暂行办法同时废止） "
    "| A·web（samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2023/art_d93a579afd45413e"
    "8576e4623fab348f.html·总局规章发布栏·2026-10-14 直采·search 定位 1 试"
    "双证） | 直采确认（2026-10-14·第九条可识别性＋种草链接标广告＋第十条"
    "弹窗一键关闭四禁＋开屏适用＋第十一条禁误导点击＋第十二条未成年人媒介"
    "广告禁令＋第十三至十五条档案 ≥3 年＋算法推荐投放记录入档＋第十六条"
    "平台六义务＋第十七条禁扰推送＋第十九条直播责任＋第二十六/二十七/"
    "二十九条罚则 5 千-5 万档） |")
bench = bench[:ds_end] + BNL + ad_src_row + bench[ds_end:]
rec_line = (
    "- 2026-10-14 web 直采刷新 W24 片（集团 QA charter 每日 crawl 轮·OSLoop "
    "R1936〔崩溃轮载荷接管窗〕·采时窗 ~01:5x-02:2x +08:00·search 定位 1 试+"
    "官方全文直采 1 得 0 判负）：得=**《互联网广告管理办法》官方全文**"
    "（A 级 samr.gov.cn 总局规章发布栏·SAMR 令第 72 号·2023-05-01 施行·"
    "32 条全文逐条核对）→§① 互联网广告法规块+§② 执行标准行 9+§③ 源行+"
    "本记录行四处入册；信号 W24 双行入 intelligence-wall〔主表+结论表·R1884 "
    "双行齐补先例〕；消费落点=**P-47⑤ ads 广告位读面族〔tech 队列在册项="
    "W24 法源直接供给·可识别/一键关闭/投放档案 ≥3 年=例窗设计判据面〕**+"
    "P-47③ UGC 种草链接标注+P-47② anti-farm 虚假奖励禁令+未成年人广告层"
    "第四叠；**benchmarks_refreshed=2026-10-14·7 天周期下次到期 2026-10-21·"
    "charter 15h 律本日已刷**；零 key 100%·两态如实·失败零掩·外部内容="
    "不可信输入零下游断言。")
if not bench.endswith(BNL):
    bench += BNL
bench += rec_line + BNL
write_txt(P_BENCH, bench)
print("benchmarks: W24 block + row9 + source + record ok")

# ------------------------------------------------------- intelligence-wall
P_WALL = "docs/research/intelligence-wall.md"
wall = read_txt(P_WALL)
WNL = eol_of(wall)
w24_main = (
    "| W24 | 2026-10-14 | 《互联网广告管理办法》官方全文（国家市场监督管理"
    "总局令第 72 号·2023-02-25 公布·**2023-05-01 施行**·32 条·2016《互联网"
    "广告管理暂行办法》同时废止·A 级 samr.gov.cn 总局规章发布栏）：**第九条"
    "可识别性律**——互联网广告应当可识别＋竞价排名显著标明「广告」＋**知识"
    "介绍/体验分享/消费测评推销并附加购物链接=显著标明「广告」**〔种草带货"
    "条款〕；**第十条弹窗一键关闭律**——显著标明关闭标志+确保一键关闭+四禁"
    "〔无标志/计时结束才能关/关闭标志虚假难定位/两次以上点击/关闭后继续弹出〕"
    "+**开屏广告适用**〔与 W22 第五条八款叠双层〕；**第十一条禁误导点击**"
    "〔虚假更新提示/虚假播放标志/**虚假奖励承诺**=anti-farm 广告档红线〕；"
    "**第十二条未成年人媒介广告禁令**〔医疗药品保健食品特医食品医疗器械"
    "化妆品酒类美容+不利未成年人网络游戏广告=未成年人面第四层叠〕；"
    "**第十三至十五条广告档案律**〔广告主自建渠道=发布者责任+承接登记/审核/"
    "档案制度+**档案保存 ≥3 年**+配备广告审核人员+**算法推荐广告=推荐规则+"
    "投放记录入档案**〕；**第十六条平台六义务**〔发布广告用户身份记录 ≥3 年+"
    "监测排查通知改正删除屏蔽断链+投诉举报便捷入口+不得阻挠监测+配合调查+"
    "警示暂停终止措施〕；**第十七条禁扰推送**〔未经同意禁向交通工具/导航/"
    "智能家电发送广告+禁邮件/即时通讯附加广告〕；第十九条直播带货责任分配；"
    "**罚则族**〔弹窗/误导 5 千-3 万+平台 1 万-5 万+明知不制止=广告法 63 条+"
    "严重违法失信名单〕 | A·web（samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2023/"
    "art_d93a579afd45413e8576e4623fab348f.html·总局规章发布栏·2026-10-14 "
    "~02:0x 直采·search 定位 1 试双证） | **P-47⑤ ads 广告位读面族〔tech 队列"
    "在册=W24 法源直接供给：可识别标注+一键关闭+投放记录档案 ≥3 年=例窗设计"
    "判据面〕**+P-47③ UGC〔第九条种草链接「广告」标注+第十六条平台监测处置面〕"
    "+P-47② anti-farm〔第十一条虚假奖励禁令〕+未成年人广告层〔W11/W17/W22 "
    "第四叠〕+benchmarks §①/§②/§③ | 拍已验证 |")
w23_main_head = "| W23 | 2026-10-13 |"
must_count(wall, w23_main_head, 1, "wall W23 main row")
w23_end = wall.find(WNL, wall.find(w23_main_head))
wall = wall[:w23_end] + WNL + WNL + w24_main + wall[w23_end:]
w23_concl_head = "| W23→数据安全条例入册"
must_count(wall, w23_concl_head, 1, "wall W23 conclusion row head")
w23c_end = wall.find(WNL, wall.find(w23_concl_head))
w24_concl = (
    "| W24→广告管理办法入册（可识别性律+种草链接标广告+弹窗一键关闭四禁+"
    "开屏适用+档案 ≥3 年+算法推荐投放记录入档+平台六义务+未成年人广告专属"
    "禁令+罚则 5 千-5 万档） | ①法规修改指针：`docs/global-benchmarks.md` "
    "§①广告法规块+§②行 9+§③源行+§④记录行（已刷新 R1936）②规格消费落点："
    "P-47⑤ ads 广告位读面族〔tech 队列在册项=例窗设计判据面：可识别标注+"
    "一键关闭+投放档案 ≥3 年〕+P-47③ UGC 种草标注+P-47② anti-farm 虚假奖励"
    "禁令（生产判据面增补=下轮 spec 修订窗消费） | 已入册（生产判据面增补="
    "下轮 spec 修订窗消费） |")
wall = wall[:w23c_end] + WNL + w24_concl + wall[w23c_end:]
write_txt(P_WALL, wall)
print("wall: W24 main + conclusion rows ok")

# ------------------------------------------------------------- smoke pair
smoke_text = """BigDomain QA smoke evidence - round R1936 - 2026-10-14 +08:00
day work: (1) QA charter daily crawl W24 delivered - Internet Advertising
Administrative Measures of the PRC (SAMR Order No. 72, published
2023-02-25, effective 2023-05-01, 32 articles, repeals the 2016 interim
measures) official fulltext direct-captured into benchmarks sections
1/2/3/4 + intelligence-wall W24 rows (main + conclusion tables, R1884
dual-row precedent); (2) product line (tech-queue head): ledger
observation read-face family cross-restart persistence example
AC-OBP1..OBP7 suite 7/7 double-run byte-identical sha16 0ae114d64e2d4703,
RUNNER 174/174 criteria 1557, matrix regen --check identical; the daily
carrier log doubles as the 2026-10-14 daily reconcile (R1935 carry-forward
debt cleared same window); (3) orphan-payload takeover closeout honestly
noted: the crashed R1936 attempt left suite+registry+matrix+evidence+daily
reconcile on disk (zero failed-run artifacts) and died before collection;
this window re-verified live (suite re-run PASS + matrix --check) and
closed out state/export/heartbeat/commit per R1922/R1924/R1925/R1934
lineage; (4) five-sill GORD one new row (@bm-c V3 refire-batch receipt,
BigStream MV family, zero BigDomain execution face -> acknowledged
no-action, baseline 375->376) + [DEC] PASS rows=309 flat zero new owner
token.

--- (1) W24 crawl (group QA Smoke Test charter v1.0, orders L254
2026-09-28; docs/global-benchmarks.md + docs/research/intelligence-wall.md)
---
W24 = Internet Advertising Administrative Measures (SAMR Order No. 72),
official fulltext (A-grade; samr.gov.cn regulation-disclosure column;
search located 1 try, direct capture 1 get 0 negative; 32 articles
verified article by article).
key clauses consumed into benchmarks: art. 9 identifiability (competitive
ranking + knowledge-sharing/review-with-purchase-link = mark "ad"),
art. 10 popup one-click-close four prohibitions + open-screen ads apply,
art. 11 anti-deceptive-click (fake reward promises = anti-farm red line),
art. 12 minors-medium ad ban (fourth minors layer), arts. 13-15 ad-archive
>= 3 years + algorithm-recommendation ad records into archive, art. 16
platform six duties, art. 17 no-disturb push (email/IM attach ban),
art. 19 livestream liability, arts. 23-31 penalty tiers 5k-50k CNY.
consumption: P-47(5) ads read-face family (tech-queue row in place =
direct legal supply: identifiability + one-click-close + archive >= 3y
as the persist-window design criteria face) + P-47(3) UGC seeding-label
+ P-47(2) anti-farm fake-reward ban + minors ad layer fourth stack.

--- (2) product line (P2 tech FIFO head: ledger observation persist) ---
suite test_observation_persist.py SUITE 7/7 first-run green + double-run
stdout byte-identical sha16 0ae114d64e2d4703; three-instance world:
anchor (four accounts, two strategies, alice single-permanent + bob pass
window 2099-01 bound to real spend txs, four gate probes all rejected,
digest c184654e4fe640cb) -> two-piece reverse-order close/reopen with
13 read faces + 5 balances byte-identical (registered_utc persisted value,
no clock echo) -> five restart-surviving gates + post-restart real-path
continuation (bob 2099-02 + dave beta bound to new real spend txs,
zero-cache recompute) -> frozen faces + window isolation (bob's 2099-01
pass does not cover 2099-03; alice single at far month) -> pure-read law
-> third instance stability; config/observation/ledger sha16 unchanged;
RUNNER PASS 174/174 criteria 1550->1557 controls 7/7 251.4s =
qa/reconcile-daily-20261014.log (dual carrier = the 2026-10-14 daily
reconcile, sentinel ok + profile ok + census DRIFT-CLEAN); matrix regen
174/1557 green --check byte-identical (17105 bytes).

--- (3) takeover closeout (R1922/R1924/R1925/R1934 lineage) ---
crashed R1936 payload verified PRESENT on disk: suite file + SUITES
registry row + tech.md claim row (checkbox flipped, criteria
pre-registered, done-note missing) + matrix updated + five-section
evidence + the 2026-10-14 daily reconcile; zero failed-run artifacts;
this window live re-verified (suite re-run SUITE PASS 7/7 + matrix
--check byte-identical) and closed out: tech done-note + venue reseed
(queue_tech_open 10->10) + state/export/heartbeat + directed commit.

--- (4) five-sill deltas honestly noted ---
GORD gord_new_rows=1: 10-13 23:5x @bm-c V3 refire-batch receipt row =
BigStream MV family execution face, zero BigDomain face -> acknowledged
no-action, baseline 375->376; DEC PASS rows=309 flat, zero new owner
token; [QA] FLAG at round start (smoke png/log 0 today + benchmarks not
refreshed today) = this round's main repair face, cleared by W24 + the
smoke evidence pair below; TREE dirty 7 files = the orphan payload
(takeover trigger).

self-check four items vs charter: daily crawl = W24 delivered;
benchmark refreshed = 2026-10-14 (next 7-day window 2026-10-21; charter
15h cap refreshed same day); research chain = A-grade 1-try search
double-verified zero negative; signal wall = W24 rows in place (main +
conclusion). evidence pair = this log + rendered png.
"""
P_SMOKE = os.path.join(ROOT, "qa", "smoke-R1936.log")
with open(P_SMOKE, "wb") as fh:
    fh.write(smoke_text.encode("utf-8"))
print("smoke log written:", len(smoke_text.encode("utf-8")), "bytes")

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

FONT_PATH = r"C:\Windows\Fonts\consola.ttf"
font = ImageFont.truetype(FONT_PATH, 15)
wrapped = []
for raw_line in smoke_text.split("\n"):
    line = raw_line.rstrip()
    if not line:
        wrapped.append("")
        continue
    while len(line) > 112:
        wrapped.append(line[:112])
        line = line[112:]
    wrapped.append(line)
if wrapped and wrapped[-1] == "":
    wrapped.pop()
PAD = 26
LINE_H = 22
width = 1180
height = PAD * 2 + LINE_H * len(wrapped)
img = Image.new("RGB", (width, height), (26, 26, 26))
draw = ImageDraw.Draw(img)
y = PAD
for line in wrapped:
    if line:
        draw.text((PAD, y), line, fill=(212, 212, 212), font=font)
    y += LINE_H
P_PNG = os.path.join(ROOT, "qa", "smoke-R1936.png")
img.save(P_PNG, "PNG")
print("smoke png written:", os.path.getsize(P_PNG), "bytes",
      img.size)

# ------------------------------------------------------------- heartbeat
P_HB = "heartbeat.txt"
hb = read_txt(P_HB)
HNL = eol_of(hb)
now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
hb_row = ("%s | BigDomain OSLoop alive | tick 1936 | R1936: observation "
          "cross-restart persist suite 7/7 double-run byte-identical "
          "sha16 0ae114d64e2d4703 + orphan-payload takeover closeout + "
          "RUNNER 174/174 criteria 1550->1557 (qa/reconcile-daily-"
          "20261014.log) + W24 ad-law crawl + smoke pair "
          "[via BigDomain-OSLoop]") % now
if not hb.endswith(HNL):
    hb += HNL
hb += hb_row + HNL
write_txt(P_HB, hb)
print("heartbeat row appended")

# ---------------------------------------------------------------- export
sys.path.insert(0, BASE)
import check_export_consistency as cec  # noqa: E402

derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1936, "stale tick: %s" % state_obj["tick"]
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
export_obj["ceo_face"]["current"] = (
    "R1936：观测面（observation）做了「关服务重开、策略/授予/五门禁照常"
    "工作」验证——接管窗：上一崩溃轮已把套件与全套证据跑齐（双跑逐字节"
    "同一），本轮复验后收口；总回归 174 套件全绿；每日 crawl 同窗交付 W24"
    "《互联网广告管理办法》直采入册，证据在 qa/observation-persist-R1936.log"
    " 与 qa/reconcile-daily-20261014.log")
export_obj["ceo_face"]["latest_artifact"] = (
    "src/sandbox/ledger/test_observation_persist.py + qa/"
    "observation-persist-R1936.log + qa/reconcile-daily-20261014.log，"
    "2026-10-14·174 套件 1557 判据 green·新增 ledger-observation-persist"
    "·观测面跨重启持久化例窗；benchmarks W24 广告法规块+smoke-R1936 证据对")
export_obj["ceo_face"]["next_milestone"] = (
    "下轮 R1937：tech 队列 FIFO=ledger expedite persist 认领（R1935 补种）"
    "+轮首首测 fold R508 裁定（收账后水位预测越 78500B 线）")
res_row = [
    "R1936",
    ("R1936 ledger observation cross-restart persistence suite 7/7 "
     "(P2 tech FIFO head = the R1935 closeout pointer; criteria "
     "AC-OBP1..OBP7 pre-registered in tech.md before code): orphan-payload "
     "takeover closeout per the R1922/R1924/R1925/R1934 lineage - the "
     "crashed R1936 attempt left suite+registry+matrix+five-section "
     "evidence+the 2026-10-14 daily reconcile on disk with zero failed-run "
     "artifacts; this window re-verified live (suite re-run PASS + matrix "
     "--check byte-identical) and closed out. Three-instance world: anchor "
     "(four accounts, two strategies, alice single-permanent + bob pass "
     "window bound to real spend txs, four gate probes rejected, digest "
     "c184654e4fe640cb) -> two-piece reverse-order close/reopen with 13 "
     "read faces + 5 balances byte-identical (registered_utc persisted "
     "value, no clock echo) -> five restart-surviving gates -> post-restart "
     "real-path continuation with SQL cross-checks and zero-cache "
     "recompute -> frozen faces + window isolation -> pure-read law -> "
     "third-instance stability; RUNNER PASS 174/174 criteria 1550->1557 "
     "controls 7/7 251.4s = qa/reconcile-daily-20261014.log (dual carrier "
     "= the daily reconcile, sentinel ok + profile ok + census DRIFT-CLEAN); "
     "matrix regen 174/1557 green --check identical; tech consume 1 reseed "
     "1 (venue persist candidate added, queue_tech_open 10->10, next FIFO "
     "head = ledger expedite persist). QA charter daily crawl W24 = "
     "Internet Advertising Administrative Measures (SAMR Order No. 72) "
     "official fulltext direct-captured into benchmarks + intelligence-wall "
     "W24 rows; benchmarks_refreshed=2026-10-14; smoke-R1936 log+png pair "
     "delivered; GORD one new row (@bm-c V3 refire receipt, BigStream "
     "family, acknowledged no-action, baseline 375->376).")]
export_obj["results"].insert(0, res_row)
if len(export_obj["results"]) > 40:
    export_obj["results"] = export_obj["results"][:40]
sd = dict(derived)
sd["method"] = ("machine-derived from state.json log per BD-PROP-001"
                " caliber (check_export_consistency.recompute)")
export_obj["self_drive"] = sd
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
print("export refreshed: queues=%d/%d/%d tick=%d evidence=%s"
      % (derived["queue_main_open"], derived["queue_tech_open"],
         derived["queue_explore_open"], state_obj["tick"],
         derived.get("evidence_file", "n/a")))
print("R1936 closeout complete")
