# ygo 共创同步层评估沙箱 PoC（backlog 转任务单·O-20261008-0650 域切片）

对象：Deln0r/ygo v1.22.0（Yjs CRDT 纯 Go 端口·MIT）——P-47①大厅 WebSocket 规格的
共创状态收敛层候选。判负核心=README「byte-for-byte V1/V2 wire-compatible with
yjs@13.6.31」宣称（B 级未实测→本 PoC 实测升 A 级）。

## 判据预注册（先于执行·诚实律）

- AC-YG1 V1 正向（yjs→ygo）：yjs@13.6.33 生成 V1 update（Map/Array/Text/嵌套
  类型/小数浮点/整型浮点探测）在 ygo ApplyUpdate 零错误，Go 侧关键槽位状态吻合。
- AC-YG2 V1 反向（ygo→yjs）：ygo 重编码状态 update 回灌 yjs 全量语义比对
  （map/array/text 三槽 JSON deepStrictEqual 对 yjs 源文档自身快照）。
- AC-YG3 V2 双向：同 AC-YG2 口径，走 encodeStateAsUpdateV2/applyUpdateV2。
- AC-YG4 状态向量字节级：ygo 状态向量编码与 Y.encodeStateVector 输出逐字节相等
  （「byte-for-byte」宣称的定点抽测）。
- AC-YG5 并发合并收敛：两个 clientID 并发编辑的 update 对在 ygo 合并，回灌 yjs
  与 yjs 自合并态 deepStrictEqual（CRDT 收敛律实测）。
- AC-YG6 yserve 传输层（预注册原口径=@hocuspocus/provider）：两 JS 客户端实时收敛
  <5s；yserve 杀进程重启后 SQLite 持久化态在新客户端可见。
  实测裁决（2026-10-08）：**AC-YG6a/b FAIL（根因=协议面不匹配非 CRDT 面）**——
  yserve v1.22.0 实现面=裸 y-websocket 信封（docName=URL 末段路径·消息不带
  docName 前缀·tag 0/1/3 only，server 包文档自证）；@hocuspocus/provider 2.15.3
  说的现役多文档 Hocuspocus 信封（每帧 docName 前缀·providerMap 路由）被 yserve
  静默丢弃→永不成握手。README「drop-in replacement for a Hocuspocus deployment
  /@hocuspocus/provider connect unchanged」宣称对 2.x provider 线=**证伪（C 级）
  →降 A 级证据=本 PoC**。补充判据（根因定位后追加·不替换预注册）：
- AC-YG6c 同收敛命题走 y-websocket 信封（yserve 实际文档化支持面·js/client-yws.mjs）。
- AC-YG6d 同持久化命题走 y-websocket 信封，yserve 重启后 SQLite 态可见。
- AC-YG7 证据链：run-poc.ps1 单命令全跑通，输出落 qa/ygo-poc-*.log（终态=
  混合裁决 exit 1=预注册 AC-YG6a/b FAIL 如实在档非崩溃）。

已知 pinned 差异面（上游自报·非判负项）：多键对象键序、整型 float64 varint、
rich-text/observers 若干 pinned——fixture 的整型浮点（count=8）即该面探测位，
语义收敛判过、字节差异如实记录。

## 方法与运行

本机无 Docker/系统 Go → 方法适配（同判据面）：可移植 Go 1.26.8 解压至仓内
src/sandbox/ygo-poc/data/toolchain（sha256 校验·零系统安装零注册表写入；
首版用 %TEMP% 被 AV/清理器中途删 go.exe 实测后改仓内·2026-10-08）+ 本仓
Node v24（原生 WebSocket）。Go 模块代理走 goproxy.cn。有 Docker 环境可将同
fixture/断言面搬进 compose。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File src\sandbox\ygo-poc\run-poc.ps1
```

结构：go-interop/（Go 互操作 harness）·js/（yjs fixture 生成/校验/yserve 客户端）
·data/（运行时产物·gitignored）。判负条件三（互操作不过/Go 运维超承载降级参照/
90 天维护停滞）见 backlog 行与登记簿 docs/oss-harvest/README.md。
