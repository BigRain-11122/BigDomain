# Unity UI 自动拼装 SOP 学习件+小程序栈适配注记（BigDomain 执行面·O-2026-0929-002）

> **溯源**：集团 orders O-2026-0929-002 Unity UI 自动拼装 SOP 全员学习令（CEO 原话「Design/handoff/Unity_UI自动拼装SOP.md 所有涉及2D界面的子公司全部学习这个文档并根据自己的业务迭代改进流程，更加适配自身业务模式和需求」·25d14d8 落账 09-29 10:52·回执窗 ≤10-01 12:00）·执法面定谳=涉 2D 界面三司：@Biggame（主战场）/@FluxVerse（双栈适配律）/@BigDomain=**M4 参观端微信小程序+大厅 UI 设计面**（本件）。
> **学习对象**：Biggame 仓 `gaming/MiniGame/Design/handoff/Unity_UI自动拼装SOP.md`（8,841B·09-29 10:36 盘面新到件·**只读引用·跨仓写禁令**·本司零复制其资产零复制其判例）。
> **行数律**：≤80 行。**判据预注册**：AC-O2a..d 先落 backlog R577 承接行（册=backlog 行）。

## 一、学习件：SOP 装配工序律吸收（本司业务迭代面）

**装配五律**（流程基线·全栈通用）：①**资产先行律**——拼装开工前资产清单齐备且过规格硬指标（固定目录约定·禁自由发挥）；②**锚点律**——不拖位置只挂 Anchor，一切定位=锚点+偏移；③**分层律**——ScreenRoot 五层结构（Bg/TopBar/Content/BottomBar/Popup·弹窗默认隐藏+半透遮罩）；④**组件预制律**——先做零件（按钮/卡片/进度条/红点）再拼屏，禁逐个手摆；⑤**数据绑定律**——数字/文字运行时注入禁写死，红点状态由数据驱动。
**禁忌六条**（原文承·通用于本司）：禁绝对坐标摆元素/禁文字画进图片/禁一张大图铺屏/禁手动逐个摆卡片/禁数字写死 prefab/禁自由 Layout 当对齐手段。
**自检律**：交付前双分辨率截图核对+照表打勾（基准屏+小屏两档）。

## 二、小程序栈适配注记（Unity UGUI → 微信小程序 WXML/WXSS 映射表）

| SOP Unity 面 | 本司小程序对应面 | 适配注记 |
|---|---|---|
| Canvas+CanvasScaler（1080×1920·Match 0.5） | rpx 响应式单位（750rpx=屏宽基准·设计稿 1080×1920 按 1.44 折 rpx） | 缩放面由平台内建·禁手调缩放系数 |
| Anchor+Offset（禁绝对 Position） | flex 主轴布局+边缘锚定 absolute（top/left/right/bottom 对父容器边距） | 锚点律同构承行·禁中心坐标硬摆 |
| Sliced 九切片（胶囊/卡片/弹窗圆角不变形） | CSS `border-image` 九宫格（简单面=border-radius+纯色底） | 圆角 ≥40px 折 rpx ≥28·拉伸不变形判据同 |
| TMP 文字 | `<text>`/`<view>` 原生文字节点（系统字体栈） | 「文字必须实时排」同律·禁烘焙进图 |
| Grid/Vertical Layout Group+Spacing | CSS `display:grid/flex`+`gap` | Cell Size/Spacing→grid-template+gap 数值直译 |
| Prefab 可复用预制体（PillButton/CardPanel/IconButton/ProgressBar/RedDot 五件） | 自定义 Component（wxml+wxss+js+json 四件套） | 零件先做再拼屏同律·组件库五件对应 |
| UIManager 数据注入（`text` 字段 Awake/OnEnable 注入） | Page `data`+`setData` 绑定 | 「不写死」同律·数字/进度/红点全走数据 |
| Button Sprite Swap 反馈+88×88 热区 | `hover-class` 态+热区最小尺寸律（≥88px 折 rpx） | 可感知反馈+热区下限两判据同 |
| 红点（右上角 Anchor·32×32） | 组件内绝对定位子节点（top-right·32rpx 正圆） | 数据驱动显隐（`HasUnclaimedReward`→wx:if） |
| 双分辨率自检（1080×1920+750×1334） | 开发者工具机型预览（小屏 iPhone SE+大屏 Pro Max 双档）+真机预览 | 检查表七项逐条照打（骑跨/切边/重叠/基线/错位/裁切/红点位置） |
| 资产目录约定（Common/Characters/Chapters/Screens） | `assets/art/` 同构四目录+规格表（PNG-24 透明/icon 96-128px/立绘 8px 呼吸边/背景上下 200px 安全区） | 「禁交付」四条（整屏大图/带字图/烘焙阴影/JPG 透明通道）原文承 |

## 三、大厅 UI 设计面适配（lobby 面·设计先行期）

- 大厅 UI 设计件（待开单）以本件 §一 装配五律+ScreenRoot 五层结构为**布局分层基线**；lobby-websocket-spec=业务规格单源（AC-S1..S13 在册·**零双建零改动**）——本件只覆盖 UI 呈现面分层与装配流程，不碰协议与城市数据面。
- M4 参观端（m4-visitor-end-spec 在册）=付费转化页挂载面：ScreenRoot 五层映射到小程序页面容器（Bg=转化页背景/TopBar=返回+标题+货币胶囊/Content=转化件挂载区〔19.9 会员锚〕/BottomBar=主 CTA/Popup=支付确认弹窗）——分层律直接沿用。
- 与本司沙箱件关系：零触碰（沙箱=服务面判据件·本件=纯设计流程面）。

## 四、判负注记（诚实律·Unity 专属工序不硬搬）

Sprite Editor 九宫格 Border 设定/PPU=100/Mesh Full Rect/导入设置→小程序栈无导入管线=以设计交付规格表直替；TMP Essential Resources 导入→原生字体栈零导入步；Graphic Raycaster/EventSystem→平台事件系统内建（bind:tap）；Button Transition Sprite Swap→CSS hover-class 面（不同面同目标：可感知反馈）。四项判负=如实注记非缺学。

## 五、落点与验证声明

- **落点**：①m4-visitor-end-spec §六 输入面指针行（本轮同步落）；②大厅 UI 设计件开单时以本件为流程基线；③bootstrap 待 CEO 物理件到位后实施期照 §二 映射表执行——**零新代码零新 schema 零新 API**（本件=纯流程适配注记·设计先行期产物）。
- **验证声明**：学习=对象件 8,841B 全文只读吸收（本司仓内零复制原文资产）；三问门未涉（零外部 API）；AC-O2a 五律六禁全表 ✓/AC-O2b 映射逐条+判负四项如实 ✓/AC-O2c 落点+单源不双建+零代码 ✓/AC-O2d 回执三载体=state log 行+backlog done 行+commit 含 O-2026-0929-002 ✓（回执窗内提前 ~35h）。
