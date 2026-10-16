import io, json, re, sys, datetime

ROOT = r'C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain'
CST = datetime.timezone(datetime.timedelta(hours=8))
NOW = datetime.datetime.now(CST)
STAMP = NOW.strftime('%Y-%m-%d %H:%M') + ' +08:00'

def rd(p):
    return io.open(ROOT + p, 'r', encoding='utf-8', newline='').read()

def wr(p, t):
    io.open(ROOT + p, 'w', encoding='utf-8', newline='').write(t)

checks = []

# ============ 1. benchmarks 4-section entry ============
bm = rd(r'\docs\global-benchmarks.md')
eol = '\r\n' if '\r\n' in bm else '\n'

S1_BLOCK = (
u'**网络暴力信息治理法规**（《网络暴力信息治理规定》·国家互联网信息办公室/公安部/文化和旅游部/国家广播电视总局令第17号·2024-06-12 公布·**2024-08-01 施行**·7 章 34 条·评论/弹幕/点赞/私信/群组全形态治理规章·2026-10-17 A 级直采入册·R2003 QA W26 片）：' + eol +
u'- **实名与账号面（第八条）**：信息发布/即时通讯服务=真实身份信息认证 fail-closed（不提供=不得提供服务）+账号信息管理+**为遭受网暴主体提供账号信息认证协助**+防范假冒仿冒恶意关联——lobby/即时通讯实名面第四法源叠层（W12 第十二条/W19 第九条/W13 第四条同向）。' + eol +
u'- **预警与识别（第十二至十四条）**：网暴信息分类标准+**特征库+典型案例样本库**+AI/大数据+人工审核结合+**预警模型七因素**〔事件类别/针对主体/参与人数/信息内容/发布频次/环节场景/举报投诉〕+异常账号动态核验/弹窗提示/违规警示/**限制流量**+**用户信用管理体系：涉网暴违规记入信用记录+降级/黑名单+限制功能/停止服务**（W19 第十八条/W13 第八条同向第三源）。' + eol +
u'- **处置阶梯（第十五/十八/十九/二十一条）**：涉网暴违法信息=**立即停止传输+删除/屏蔽/断链+保存记录+报告**；评论/回复/留言/**弹幕/点赞**面网暴=删除/屏蔽/**关闭评论**/停止服务；群组环节禁匿名投稿/隔空喊话+**建立者管理者管理责任**〔限制发言/移出群组=W14 同向〕；组织煽动多次发布=**黑名单禁重注**+营销炒作=清理订阅关注/暂停营利权限。' + eol +
u'- **保护机制（第二十三至二十七条）**：防护选项〔屏蔽陌生/特定用户+本人发布信息可见范围+禁转载/禁评论本人发布〕+**私信规则**〔仅好友私信/拒收私信/智能屏蔽/自定义屏蔽词〕+风险显著提示+保护救助+报告〔未成年/老年人/残疾人/隐私/人身财产〕+**快捷取证功能**〔保存信息内容与浏览评论转发数据+维权便利〕+**专门快捷投诉举报入口**+未成年人优先处理+通知删除权功能渠道。' + eol +
u'- 本司落点=P-47① 大厅〔第八条实名+第十八条评论处置+第十九条群组管理者责任+第二十三条屏蔽/私信防护选项+第二十五条快捷取证/evt_id 日志〕+P-47③ UGC〔第十二条特征库+第十五条立即停止传输+第二十六条快捷举报入口〕+P-47② anti-farm〔第十条批量注册/操纵账号/营销炒作三禁=第三法源+第十四条信用黑名单〕+bootstrap〔第二十六条快捷举报入口+第二十五条取证=接线窗硬前置候选〕（**2026-10-17 官方全文直采确认**：cac.gov.cn/2024-06/14/c_1720043894161555·国家网信办官网全文页·34 条逐条核对·search 定位 1 试零判负）。' + eol + eol
)
m = re.search(r'^## .{0,3}\u6267\u884c\u6807\u51c6', bm, re.M)
assert m, 'section2 header not found'
bm = bm[:m.start()] + S1_BLOCK + bm[m.start():]
checks.append('S1 block inserted before section2 header')

S2_ROW = (u'| 10 | 网暴信息防护选项＋一键取证＋预警模型（W26·四部门令第17号第八/十二至十五/十八/二十三/二十五/二十六条） | 评论/弹幕/点赞面网暴信息立即停止传输＋删除/屏蔽/关闭评论 fail-closed；预警模型七因素＋特征库＋异常账号动态核验/限制流量；屏蔽陌生/特定用户＋仅好友私信/拒收私信＋自定义屏蔽词防护选项＋快捷取证＋专门快捷举报入口=lobby/UGC 防护读面族设计判据 | `src/sandbox/lobby/`（server.py evt_id 日志族）＋`src/sandbox/ugc/`（sec_batch/pipeline 特征库面）·⬜例窗交付窗 | L3 |')
m2 = re.search(r'^\| 9 \| [^\n]*$', bm, re.M)
assert m2, 'S2 row9 not found'
bm = bm[:m2.end()] + eol + S2_ROW + bm[m2.end():]
checks.append('S2 row10 inserted after row9')

S3_ROW = (u'| 网络暴力信息治理 | 《网络暴力信息治理规定》官方全文（国家互联网信息办公室/公安部/文化和旅游部/国家广播电视总局令第17号·2024-06-12 公布·2024-08-01 施行·7 章 34 条） | A·web（cac.gov.cn/2024-06/14/c_1720043894161555·国家网信办官网全文页·2026-10-17 直采·search 定位 1 试零判负） | 直采确认（2026-10-17·第八条实名 fail-closed+第十条三禁+第十二条特征库+第十三条预警模型七因素+第十四条信用黑名单+第十五条立即停止传输+第十八条评论/弹幕/点赞处置+第二十三条防护选项/私信规则+第二十五条快捷取证+第二十六条快捷举报入口+第三十条罚则 1-20 万档） |')
m3 = re.search(r'^\| \u513f\u7ae5\u4e2a\u4eba\u4fe1\u606f\u4fdd\u62a4 \| [^\n]*$', bm, re.M)
assert m3, 'S3 W25 row not found'
bm = bm[:m3.end()] + eol + S3_ROW + bm[m3.end():]
checks.append('S3 source row inserted after W25 row')

if not bm.endswith(eol):
    bm += eol
S4_ROW = (u'- 2026-10-17 web 直采刷新·W26 片（集团 QA charter 每日 crawl 份·OSLoop R2003·采时窗 ~05:xx +08:00·search 定位 1 试+官方全文直采 1 得 0 判负）：得=**《网络暴力信息治理规定》官方全文**（A 级 cac.gov.cn 官网全文页·四部门令第17号·2024-08-01 施行·7 章 34 条全文逐条核对）→§① 网暴法规块+§② 执行标准行 10+§③ 源行+本记录行四处入册；信号 W26 双行入 intelligence-wall（主行+结论行·R1884 双行先例）；消费落点=P-47① 大厅〔防护选项/私信规则/取证日志〕+P-47③ UGC〔特征库/停止传输/快捷举报〕+P-47② anti-farm〔第十条三禁第三法源〕+bootstrap〔快捷举报入口=接线窗硬前置候选〕；候选勘误两枚如实注〔①消保法实施条例=W10 在册撞车②跟帖评论规定=W13 在册 2022 修订版·2017 版已废止=拦下〕；**benchmarks_refreshed=2026-10-17（7 天窗下次刷新 2026-10-24·charter 15h 帽当日刷新）**·取信 key 100%·动态实采失败为零·不涉及外部歧义源·换源与再核验零次。')
bm += S4_ROW + eol
wr(r'\docs\global-benchmarks.md', bm)
checks.append('S4 record row appended')

# ============ 2. intelligence-wall W26 dual rows ============
wall = rd(r'\docs\research\intelligence-wall.md')
weol = '\r\n' if '\r\n' in wall else '\n'
W26_MAIN = (u'| W26 | 2026-10-17 | 《网络暴力信息治理规定》官方全文（国家互联网信息办公室/公安部/文化和旅游部/国家广播电视总局令第17号·2024-06-12 公布·**2024-08-01 施行**·7 章 34 条·A 级=cac.gov.cn 官网全文页）：**第三十二条网暴信息定义**〔对个人集中发布+侮辱谩骂/造谣诽谤/煽动仇恨/威逼胁迫/侵犯隐私/影响身心健康的指责嘲讽贬低歧视〕+**第八条实名 fail-closed**〔信息发布/即时通讯不提供真实身份=不得提供服务+为受害主体提供账号认证协助〕+**第十条三禁**〔禁网暴违法信息+禁蹭炒热度营销炒作+禁批量注册/操纵账号组织传播+明知不得提供数据技术流量资金支持〕+**第十二条特征库+典型案例样本库**+AI/人工审核结合+**第十三条预警模型七因素**+异常账号动态核验/弹窗提示/违规警示/限制流量+**第十四条信用管理体系**〔涉网暴记入信用记录+降级/黑名单+限功能/停服务〕+第十五条立即停止传输+第十六条新闻跟帖先审后发+第十七条直播/短视频阻断+**第十八条评论/回复/留言/弹幕/点赞处置**〔删除/屏蔽/**关闭评论**/停止服务〕+第十九条群组管理者责任〔限制发言/移出群组〕+第二十一条组织煽动=黑名单禁重注+营销炒作=暂停营利权限+**第二十三条防护选项**〔屏蔽陌生/特定用户+可见范围+禁转载/禁评论+私信规则=仅好友/拒收/智能屏蔽/自定义屏蔽词〕+第二十四条风险提示+保护救助+报告〔未成年/老年人/残疾人/隐私/人身财产〕+**第二十五条快捷取证**〔保存内容与浏览评论转发数据+维权便利〕+**第二十六条专门快捷投诉举报入口**+第二十七条未成年人优先+通知删除权渠道+第三十条罚则〔1-10 万+严重 10-20 万+组织煽动/恶意炒作从重〕+第三十三条依法检举舆论监督不适用 | A·web（cac.gov.cn/2024-06/14/c_1720043894161555·国家网信办官网全文页·2026-10-17 ~05:xx 直采·search 定位 1 试零判负） | P-47① lobby〔实名+评论处置+群组责任+防护选项+取证/日志〕+P-47③ UGC〔特征库+停止传输+快捷举报〕+P-47② anti-farm〔第十条三禁第三法源+信用黑名单〕+bootstrap〔快捷举报入口+取证=接线窗硬前置候选〕+benchmarks §①/§②/§③ | ✓已验证 |')
anchor = weol + weol + u'## 本墙结论应用表'
assert anchor in wall, 'conclusion-table anchor missing'
wall = wall.replace(anchor, weol + weol + W26_MAIN + weol + weol + u'## 本墙结论应用表', 1)
W26_CONCL = (u'| W26→网络暴力信息治理规定入册（实名 fail-closed+三禁营销炒作/批量注册+特征库+预警模型七因素+信用黑名单+评论/弹幕/点赞处置阶梯+防护选项/私信规则+快捷取证+专门快捷举报入口+未成年人优先+罚则 1-20 万档） | ①法规修改指针：`docs/global-benchmarks.md` §① 网暴法规块+§②行 10+§③源行+§④记录行（2026-10-17 直采）②规格消费落点：P-47① lobby〔防护选项/私信规则=lobby 防护读面族设计判据·第十八条评论处置=moderation 阶梯法源〕+P-47③ UGC〔特征库+立即停止传输+快捷举报入口〕+P-47② anti-farm〔第十条三禁=第三法源 W16 第二十四条/W17 第十四条同向〕（生产判据面增补=下窗 spec 修订窗消费） | 已入册（生产判据面增补=下窗 spec 修订窗消费） |')
if not wall.endswith(weol):
    wall += weol
wall += W26_CONCL + weol
wr(r'\docs\research\intelligence-wall.md', wall)
checks.append('wall W26 main+conclusion rows inserted')

# ============ 3. tech.md: adjudication row flip + 2 seeds ============
tq = rd(r'\state\queue\tech.md')
teol = '\r\n' if '\r\n' in tq else '\n'
mk = u'- [ ] daily 剖面步观察窗转正裁定执行窗'
assert mk in tq, 'adjudication row missing'
tq = tq.replace(mk, u'- [x] daily 剖面步观察窗转正裁定执行窗', 1)
DONE_NOTE = (u'——〔**done 2026-10-17 R2003**：AC-OW2 机械三支裁定兑现（10-16 治理窗门已到·R2003 认领）——裁定计数器=live-step 标记行全仓机械 grep=11 条全 exit=0+套件级判行 4 条按 AC-OW3 不入计数→漂移 FLAG 计数==0→**支①成立：维持观察窗不转正·续 7 天滚动复评**（下窗 2026-10-24·阈值口径=AC-RP4 家族式零改动·PROFILE_OBSERVATION_WINDOW 不动）·滚动复评种子行已入列〕')
# find the line containing the (now [x]) row and append note at line end
lines = tq.split(teol)
for i, ln in enumerate(lines):
    if ln.startswith(u'- [x] daily 剖面步观察窗转正裁定执行窗'):
        lines[i] = ln + DONE_NOTE
        break
else:
    raise SystemExit('x-row not found for note append')
tq = teol.join(lines)
if not tq.endswith(teol):
    tq += teol
SEED1 = (u'- [ ] daily 剖面步观察窗滚动复评窗（R2003 裁定后继：AC-OW2 支①滚动复评义律·下窗=2026-10-24 复评〔裁定计数器机械 grep 同律零改动〕·计数仍 0=续维持·计数 ≥1=同证据 log 复跑交叉定噪声/真漂移→真漂移=PROFILE_OBSERVATION_WINDOW=False+runbook §三 G5 升格门控——种子=R2003 裁定兑现〔R2003 补种〕）')
SEED2 = (u'- [ ] cloud-cap spawn 闸参数无头面貌适配窗（D-20261017-02 ①修法 spec 已到位〔参数无头 -p 面貌·bigmoney 63943e50b 实测 live=0·fail-open 保持〕→本司 iteration_loop.ps1 R2001 交付闸同缺陷适配：探针计全 codely.exe→参数化无头判别·适配后 live 计数=非无头窗实数·诚实注=本司 loop 逐轮 api=0 纯本地·R2001 实测 live=7 假计数让路面在册〔防假拦面非产能面〕·三变体行为测试随批——种子=D-20261017-02 ①〔R2003 补种〕）')
tq += SEED1 + teol + SEED2 + teol
wr(r'\state\queue\tech.md', tq)
checks.append('tech.md adjudication done + 2 seeds')

print('; '.join(checks))
print('STAMP=' + STAMP)
