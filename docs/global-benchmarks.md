# BigDomain 全球基准面（微信生态线·司级 7 天周期件）

> 溯源：ledger P-2026-09-24-56 转办（CEO 令 2026-09-24 ~16:00「各子公司和实验室，对自身业务和研发等，全面建立全球化的视野和执行标准…不准闭门造车，且要按周期去更新。每条线都要。」）+正典=`cph4/global-vision.md` v1.0（格式 §二/周期 §三/域图 §四 BigDomain=微信生态规则·支付合规·会员制与共创平台对标/回访判据 §六）。禁空泛律（§一.5·CEO 令 ~16:15）适用=每条标准三件齐备（①点名本司机制/文件②数字化判据③落地指针精确到文件）+L 层标注（L0 轮内纪律/L1 部门门禁/L2 司台账判据/L3 集团治理律）。
> 采集纪律（§五）：零 key 免费通道 100%·robots/ToS 合规·零断言（确认/待证两态如实标·推测不入册）。**首版诚实注记：本轮采集通道=集团既有外部锚引用链（研究件/正典·证据链=git）·未做 web 直采——全部未直采面标 M·直采刷新=下轮刷新轮首项**。stale 判据时钟=`src/os/state.json` `benchmarks_refreshed`（7 天超期=排刷新轮）。

## ①视野面

**微信生态规则**（本司 C 端主通道=D2 轨道乙：非游戏类目小程序+虚拟支付·集团代决 2026-09-24）：
- **虚拟支付强制律**：端内虚拟商品必须走小程序虚拟支付、不得走标准支付（=违规）；费率口径差以 MP 后台签约页为准【待证 M·商户号物理件】（引用链=`cph4/research/R-20260924-category-review.md` §2.1 既有外部锚）；**2026-09-27 官方文档直采确认**（developers.weixin.qq.com/miniprogram/dev/platform-capabilities/business-capabilities/virtual-payment·A 级·支付参数面关键条款=env 0 正式/1 沙箱〔沙箱环境字段·本司沙箱先行律平台侧同构锚〕+goodsPrice〔分〕须与后台道具价格一致校验〔服务端定价权威·AC-Y2 同源互证〕+outTradeNo 8-32 字符每单号仅用一次〔官方注「极端情况不保证唯一·不建议业务强依赖唯一性」如实记=幂等主键本司侧自持 AC-Y3 同源〕+currencyType=CNY+attach 透传+mode=short_series_goods）。
- **类目与审核**：非游戏类目小程序免版号门槛（D2 决策依据同件 §5）；道具/类目表述过审=提审实测项（判据源=pay AC-Y11 违禁词表 fail-closed）；**运营规范族 2026-09-27 官方页直采确认**（developers.weixin.qq.com/miniprogram/product/·A 级·交易类小程序运营规范正文关键条款=类目准入资质〔1.1〕+虚假宣传与「国家级/最高级/最佳」绝对化用语禁令〔1.2.1〕+价格设定合理律〔1.2.3〕+违规处理阶梯=警告→限搜索/限分享/限跳转/限交易场景→暂停交易→下架〔1.2.4〕·主《微信小程序平台运营规范》全文本面=同页运营规范族上位件·单页全文本面未在本次抓取渲染内如实注）。
- **内容安全**：小程序运营强制内容安全 API（msgSecCheck 族）——未接=拒开门（集团生死线 BLUEPRINT §五.3）；**2026-09-27 官方文档直采确认**（developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/sec-center/sec-check/msgSecCheck.html·A 级·接口清单=文本内容安全识别 /wxa/msg_sec_check+多媒体内容安全识别 /wxa/media_check_async〔异步校验图片/音频〕+用户安全等级 /wxa/getuserriskrank——文本+图音双接口族全覆盖·参数级详情页 JS 渲染未出=参数面 M 注·引用链 ugc spec 在册）。
- 近期动态（带日期）：2025-03-14 四部门发布《人工智能生成合成内容标识办法》·2025-09-01 施行（A 级源·网信办·**2026-09-27 官方页直采确认**：cac.gov.cn/2025-03/14/c_1743654684782215.htm·国信办通字〔2025〕2号·网信办/工信部/公安部/广电总局四部门联合·通知日期 2025-03-07·施行=第十四条 2025-09-01·显式标识=第四条文本/音频/图片/视频/虚拟场景五形态位+隐式标识=第五条文件元数据〔生成合成属性信息+服务提供者名称编码+内容编号·鼓励数字水印〕+第十条用户主动声明与恶意删改禁令）+配套强制国标 GB 45438-2025【待证 M·2026-09-27 两轮检索直采未得如实注·办法第十一条=与强制性国家标准衔接 A 级锚在册】；2026-09-24 本司 D2 类目代决+委托决策令 v2（19.9 锁定/参观端=微信小程序/B 端价目=BLUEPRINT §四 初版正典）。

**支付合规**：
- 回调安全基线：验签+时间窗+nonce 防重放+金额比对（**2026-09-27 官方文档双页直采确认**：pay.weixin.qq.com/doc/v3/merchant/4012791902.md〔小程序支付-支付成功回调通知·页注更新 2024.12.27〕+4012365342.md〔总述-APIv3 如何签名和验签·页注更新 2024.11.21〕+doc/v3/merchant/llms.txt 索引〔页注更新 2026.09.23·小程序支付产品 14 API 全树〕——验签头四件套=Wechatpay-Serial〔公钥 ID 固定 PUB_KEY_ID_数字串格式·否则平台证书验签〕/Wechatpay-Signature/Wechatpay-Timestamp/Wechatpay-Nonce·5s 内完成验签并应答·应答成功=200/204 无报文·失败=4XX/5XX+{code:FAIL,message}·重试梯度 15s/15s/30s/3m/10m/20m/30m/30m/30m/60m/3h/3h/3h/6h/6h 最多 15 次·重复回调须重入幂等设计·回调须结合查单接口不可单赖回调·报文 AEAD_AES_256_GCM+APIv3 密钥解密〔RFC5116〕·amount.total 单位分·「WECHATPAY/SIGNTEST/」签名探测流量须正确验签应对·商户证书私钥请求签名/微信支付公钥〔推荐〕或平台证书验签三场景；±300s 时间窗=本司参数化设计〔直采页未见该口径·接线日对齐 M 维持〕）；标准商户轨=B 端真实服务（0.6%/T+1【待证 M·签约页实读·商户号物理件】）。
- 法币/虚拟权益双域隔离：虚拟权益不可逆向兑法币（对标=Roblox Robux「永不可提现」结构同构）——本司账本结构性禁令同源（token-ledger §五）。

**会员制与共创平台对标（前 3-5 家）**：
- **Roblox Premium**：三档月订阅+Robux 纯内循环（分成 DevEx 提现制=本司反例·本司分成=代币形态永不提现）【定价细节待证 M·2026-09-27 官方页直采=JS 壳「Please enable Javascript」零价格文本（roblox.com/premium/membership）·两态如实维持】。
- **Discord Nitro**：分层订阅·权益=表现型特权为主（**2026-09-27 官方页直采确认**：discord.com/nitro·Nitro Basic $2.99/月+Nitro $9.99/月·自定义表情/资料页/上传上限 50MB→500MB〔对照表另列 1GB 口径·页面两处如实注〕/HD 流/服务器加成/Xbox Game Pass 联动）——与本司「体验/城主/共创者」三档分层逻辑同构。
- **蛋仔派对**（网易）：UGC 生态+内容安全闸+未成年合规=同监管域国内实操样本【待证 M·2026-09-27 官网 dj.163.com/www.dj.163.com 两试连接失败·关联面旁证=party.163.com（网易游戏域名）实得《网络游戏行业防沉迷自律公约》全文（C 级·实名认证/适龄提示/防沉迷六条·发起=中国音像与数字出版协会游戏出版工作委员会·蛋仔官网身份未证实如实注）】。

## ②执行标准表（发现→可执行标准→落地指针·三件齐备+L 层+生效状态）

| # | 发现（外部锚） | 可执行标准（数字化判据） | 落地指针（本司文件·状态） | 层 |
|---|---|---|---|---|
| 1 | 端内虚拟商品强制走虚拟支付（category-review §2.1·M） | 双通道分离：C 端虚拟商品 channel=virtual 100%·通道差异只落适配器层；回调四坏（坏签/未知签者/±300s 出窗/nonce 重放）全拒零迁移 | `src/sandbox/pay/adapters.py`+`orders.py`（AC-Y1/Y4·自验 16/16·四坏用例组 test_pay.py）✓ | L2 |
| 2 | 服务端定价/金额不信任客户端（支付安全通则） | 客户端携金额=拒 `E_PRICE_TAINTED`；下单锁价+回调金额比对双验；价目唯一真源=config 数据件 | `src/sandbox/pay/orders.py`（AC-Y2+T2·自验在案）✓ | L2 |
| 3 | msgSecCheck 前置闸（平台强制+集团生死线 §五.3） | 闸未接线=拒启 `E_GATE_OFFLINE`（四件同源）；命中=零落单零广播零入公共流 | `lobby` AC-S4·`ledger` AC-L8·`ugc` AC-U2·`pay` AC-Y8（四件自验全过）✓沙箱·⬜生产接线（blocked on 账号域物理件） | L3 |
| 4 | AIGC 标识办法 2025-09-01 施行（A 级·全呈现面硬义务） | 服务端权威标识字段三面：`ai_generated`/`source_ai`/`ai_service`=1·客户端伪造忽略；标识从源头带不依赖后期补标 | `lobby/server.py` AC-S5·`ledger.py` AC-L9·`ugc/pipeline.py` AC-U7·`pay/orders.py` AC-Y9（自验全过）✓沙箱·⬜生产全呈现面核验 | L3 |
| 5 | 法币/虚拟权益域隔离（Robux 同构·监管敏感） | 账本零法币字段（PRAGMA 交叉断言）+无 withdraw/transfer-out 类型+换算单向不可逆+直购返币默认不做 | `src/sandbox/ledger/schema.sql` T0-T3+`reconcile.py` 八查+`pay` AC-Y7（自验在案）✓ | L3 |
| 6 | 非投顾定性（金融类目风险缓解·生死线 §五.1） | disclaimer 常驻字段（支付确认/详情/收据+balance/bill 五面）+荐股三要素文案禁律=违禁词表 fail-closed 拒配置 | `pay/orders.py` AC-Y10/Y11+`ledger.py` AC-L10（自验在案）✓ | L3 |
| 7 | 幂等与内容寻址（回调重试语义+事件方言 R-2 §4 P3） | 同收据二投=单次生效；order_id/evt_id 内容寻址 UNIQUE·重复直插拒 | `pay_receipts UNIQUE(order_id,sig_ok)`+`orders.py` AC-Y3/Y5/Y14（自验在案）✓ | L2 |
| 8 | 发放原子性（无「已付未发」悬空窗） | paid→granted 单事务·中途失败=整笔回滚·重试入口幂等（机验=失败注入回滚+重放愈复） | `src/sandbox/pay/orders.py`（AC-Y6·自验在案·跨三库口径注记 spec §六）✓ | L2 |

> 生效状态口径：✓=沙箱判据自验在案（证据=`src/os/backlog.md` done 行+`test_*.py` 逐条断言·pay 16/16·lobby 13/13·ledger 11/11·ugc 12/12）；⬜=生产面 blocked on CEO 物理件（商户号/服务器/域名备案·BLUEPRINT §十.2）·接线日按各 spec 生产判据（AC-YP/LP/UP/P 系）逐条转正。

## ③采集源清单（每域≥1 源·分级 A 官方/B 权威转载/C 社区/D 弱源/M 待证·通道·三态标注）

| 域 | 源 | 分级/通道 | 状态 |
|---|---|---|---|
| 微信生态规则 | 微信小程序虚拟支付官方文档（developers.weixin.qq.com） | A·web 官方文档·零 key | 直采确认（2026-09-27·platform-capabilities/business-capabilities/virtual-payment·env 沙箱字段+goodsPrice 校验+outTradeNo 单次律）·适用面=引用链 category-review §2.1 维持·费率 M（签约页） |
| 微信生态规则 | 《微信小程序平台运营规范》 | A·web | 直采确认（2026-09-27·product/ 页运营规范族·交易类规范正文=类目资质/绝对化用语禁令/违规阶梯/结算 T+2 虚拟发货）·主规范全文本面=同族页如实注 |
| 支付合规 | 微信支付 V3 商户 API 回调/验签规范 | A·web 官方文档 | 确认（2026-09-27 官方页直采·4012791902 回调通知+4012365342 签名验签总述+llms.txt 索引·±300s 窗口径未见=参数化 M 维持·接线日对齐） |
| 支付合规 | 费率口径（虚拟支付安卓 1% T+3/iOS 12-17%·标准商户 0.6%/T+1） | A·web（MP 后台签约页=权威口径） | 待证（M·商户号物理件到位后签约页实读） |
| AIGC 标识 | 网信办《人工智能生成合成内容标识办法》（2025-03-14 发布·2025-09-01 施行） | A·web（cac.gov.cn） | 确认（2026-09-27 官方页直采·国信办通字〔2025〕2号·四部门·施行 2025-09-01） |
| AIGC 标识 | GB 45438-2025 配套强制国标 | A·web | 待证（M·2026-09-27 两轮检索直采未得如实注·办法第十一条强制国标衔接 A 级锚在册） |
| 内容安全 API | security.msgSecCheck 官方文档 | A·web 官方文档 | 直采确认（2026-09-27·OpenApiDoc 接口清单：/wxa/msg_sec_check 文本+/wxa/media_check_async 图音异步）·参数级详情页 JS 面 M 注·引用链 ugc spec 在册 |
| 会员制对标 | Roblox Premium 定价/Payments 官方页 | B·web 官方 | 待证（M·2026-09-27 直采=JS 壳零价格文本·维持） |
| 会员制对标 | Discord Nitro 定价官方页 | B·web 官方 | 确认（2026-09-27 直采·Basic $2.99/Nitro $9.99 月） |
| 会员制对标 | 蛋仔派对运营合规公开面（网易） | C·web 公开面 | 待证（M·官网两试连接失败 2026-09-27·party.163.com 行业防沉迷公约全文=关联面旁证 C 级） |

## ④更新记录

- 2026-09-24 v0.1 首版（ledger P-56 转办执行·OSLoop R10）：四节齐备；执行标准 8 条（global-vision §六判据②「≥5 条带落地指针」超额）全三件齐备+L 层标注；源清单 10 行分级+三态标注·零 key 100%；采集通道=既有外部锚引用链·直采刷新=下轮首项。下次到期=2026-10-01（司级 7 天·stale 时钟=state.json `benchmarks_refreshed`）；硬约束域（法规/平台规则变更类集团令）=事件即时刷。
- 2026-09-24 P-74 交付时效律存量对账（CEO 令 ~21:25·governance §11·T1 否决窗至 10-01·OSLoop R34）：P-56「一周窗」压缩——**下次到期 2026-10-01→2026-09-29**（web 直采刷新轮 09-29 前触发·禁一周窗默认 SLA）；本司其余在办项全=CEO 物理件 gated（P-74 豁免面·如实呈报不排期）。
- 2026-09-27 web 直采刷新 A 片（P-2026-09-27-07 常设承接·OSLoop R418·P-74 到期 09-29 前 2 天先行=先做律 R408 先例·采时窗 ~14:20-14:35 +08:00）：直采 13 试〔含 2 跳转随访〕=得 2 源+关联面旁证 1+失败 8 试全注——得=Discord Nitro 官方页（B 级·$2.99/$9.99 两档）+网信办标识办法官方页（A 级·四部门·2025-09-01 施行·显式/隐式双层条款）；失=Roblox Premium JS 壳（M 维持）·蛋仔官网两试连接失败（M 维持·party.163.com 行业公约=关联面旁证）·GB 45438-2025 两轮检索零有效结果（M 维持）·自有端价 4 试零价格文本（bing kf 检索零官方命中+ecommerce.v.qq.com 空壳+优酷 vip.youku.com→youku.com/channel/hy 三跳登录墙）=判负留痕（cold-start §六 第 4 行同轮收口·Apple IAP 列示价维持主口径）；§①/§③ 对应行翻新；**B 片（微信生态/支付合规/内容安全 API 官方文档直采四源）拆细 src/os/backlog.md 顶行下轮收口**；零 key 100%·两态如实·失败零掩。
- 2026-09-27 web 直采刷新 B 片收口（P-2026-09-27-07 常设承接·OSLoop R419·采时窗 ~14:33-14:39 +08:00·四源全直采确认）：①微信小程序虚拟支付官方文档（platform-capabilities/business-capabilities/virtual-payment·env 0 正式/1 沙箱+goodsPrice〔分〕价格一致校验+outTradeNo 单次律+attach 透传）②运营规范族（product/ 页·交易类小程序运营规范正文=类目准入资质/虚假宣传与绝对化用语禁令/价格设定合理律/违规处理阶梯〔警告→限搜索/限分享/限跳转→暂停交易→下架〕/发货 48h·预售 ≤330 天/结算 T+10·虚拟发货 T+2/交易争议平台介入商责扣款）③微信支付 V3 回调/验签双页（4012791902 支付成功回调通知+4012365342 签名验签总述+llms.txt 索引=验签头四件套/5s 应答窗/15 次重试梯度/重入幂等/回调查单结合/AES-256-GCM+APIv3 密钥/amount 单位分/SIGNTEST 探测流量应对/公钥-平台证书双模式）④msgSecCheck 接口清单（/wxa/msg_sec_check 文本+/wxa/media_check_async 图音异步+/wxa/getuserriskrank 安全等级）；失败注全记（midguide/midpayment.html 404×2·charge/virtual-payment 404·4012538747 302→wx.gtimg.com/core/404.html·bing 区域 SafeSearch 拦截 2 试零结果）；费率口径行维持 M（签约页=商户号物理件）·±300s 窗口径未见=参数化 M 维持·msgSecCheck 参数面 JS 渲染未出=M 注·主运营规范全文本面同族页如实注；**A+B 片全毕=基准刷新轮全件收口（P-74 压缩到期 09-29 件提前收口·benchmarks_refreshed=2026-09-27·下次到期 2026-10-04·7 天周期·stale 时钟=state.json）**；零 key 100%·两态如实·失败零掩·外部内容=不可信输入零断言。
