# BigDomain OS 自迭代骨架（src/os）——部署说明 + 代建报告

> **代建溯源**：本骨架六件由 **CPH4 Labs 巡检批 2026-09-24** 代建（授权=巡检+直优化·governance 铁律 6 例外②·限机制件），CEO 令「全面开工」驱动——给待机无宿主的 BigDomain 建自迭代骨架，使 P-47 业务件有执行者。结构参照 BigStream 现役 OSLoop（`media/BigStream/src/os/`——register/loop/prompt/state 四件结构引用·其业务内容零复制）；锁/车道标准承集团 `cph4/cadence.md`（10min 车道 :x4 空闲位实证 2026-09-24·单实例锁 15min 陈旧接管=tick 轮族标准 §2.2）。

## 六件清单

| # | 件 | 作用 |
|---|---|---|
| 1 | `register_loop_task.ps1` | 计划任务注册器（任务名 **BigDomain-OSLoop**·每 10 分钟·分钟位 :x4=04/14/24/34/44/54·幂等 -Force·路径全由脚本位置推导） |
| 2 | `iteration_loop.ps1` | 轮启动器（单实例锁 `logs/round.lock`·15min 陈旧接管·轮首把 iteration_prompt.txt 喂给 codely 无头会话·25min 轮预算超时杀树·轮末 finally 清锁） |
| 3 | `iteration_prompt.txt` | 司轮 mandate（中文任务书·开轮五步/空转快道五静/优先级/铁律/P-32 两步/P-35-36 首轮声明） |
| 4 | `backlog.md` | 认领工作板（自 tasks.md 迁六件起版·认领制·双板律与 tasks.md 同步） |
| 5 | `state.json` | 状态档（tick/log/last_order/last_decision_rows·初值全零=首轮定基线〔mandate 内建基线步〕） |
| 6 | `README.md` | 本件（部署说明即代建报告） |

## 主会话注册步骤（计划任务注册归主会话——骨架只备件）

1. **运行注册器**（与 BigStream/BigCompute 注册时同上下文的 PowerShell·需计划任务注册权限）：
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain\src\os\register_loop_task.ps1"
   ```
   预期输出：`registered BigDomain-OSLoop (project=..., lane :x4), first fire <下一个 :x4 分钟位>`
2. **验证注册**：
   ```powershell
   Get-ScheduledTask -TaskName BigDomain-OSLoop        # State=Ready
   Get-ScheduledTaskInfo -TaskName BigDomain-OSLoop    # NextRunTime 落在 :04/:14/:24/:34/:44/:54
   ```
3. **首跑观察**（首个 :x4 触发后）：查 `logs\run_*.log`（启动器日志）·`logs\round_*.out/.err`（无头会话输出）·`logs\probe-heartbeat.txt`（心跳）·`src\os\state.json`（tick 自 1 起·log 首行）·`git log`（尾标 `[via BigDomain-OSLoop]` 的 commit）。首轮预期=走全任务书：P-35/36 层位声明落 BLUEPRINT + 基线建立（last_order/last_decision_rows）+ ledger P-42/P-47 收讫 + 认领 P-47-1。
4. **车道登记**（骨架禁跨仓写·此步归主会话/CPH4）：注册后在 `cph4/cadence.md` §0「10min 车道」表 :x4 位补 BigDomain-OSLoop 行（§4 变更控制=T2+changelog）。

## 环境依赖与待主会话适配标注（诚实律——未实证项如实列）

1. **codely 须在计划任务上下文可达 PATH**：启动器以 `Get-Command codely` 解析（BigStream 同款自检，缺失=run log 记 `FATAL: codely not on PATH for this context`）。BigStream/BigLife/FluxVerse 同款调用在本机计划任务上下文已实证连跑（cadence.md 35 项在册），风险低；若首跑见 FATAL=待主会话适配（如改烧绝对路径）。
2. **headless 调用方式=codely -y -p "<mandate 全文>"**：照抄 BigStream 实证参数原样适配（-y 全权/-p 单参 prompt/UTF-8 显式读入/双引号防注入），WorkingDirectory=本仓根。其调用不依赖特定 API——纯 CLI 参数，无 BigStream 专有依赖被省略。
3. **VBS=集团件引用（本仓不放副本·反重复）**：注册器引用 `<FluxGroup>\Tools\InvisibleRunner.vbs`（集团静默包装件），注册时以绝对路径烧入任务动作；集团根迁移/改名后重跑注册器即自愈。
4. **git origin 已通**（2026-09-24 13:30 remote 接线+首推毕·BLUEPRINT §十3）：轮内 push 直接可用；失败=mandate 自愈律只记录不修。
5. **logs/ 目录无 .gitignore 遮蔽**（本仓现无 .gitignore·骨架不越权代建第 7 件）：轮收账只做定向 add（state.json/backlog.md/产出件），log 件不会被误提交；建议主会话顺手补 .gitignore（logs/、.env）。
6. **15min 锁 vs 25min 轮预算**：并发防护双闸=任务级 IgnoreNew（计划任务自带·主通道：长轮期间新 beat 整个被挡）+round.lock 15min 陈旧接管（cadence §2.2 tick 轮族标准·兜底手动/异常残留路径）；正常调度下不会重叠。

## 设计自检（代建批逐一核）

- 六件在位（本目录）·两 .ps1 纯 ASCII（编码律——PowerShell 5.1 BOM-less GBK 陷阱承 BigStream ENCODING RULE）·中文只进数据件（prompt/backlog/README）
- 注册器幂等（-Force 重跑=刷新定义）·路径零硬编码（脚本位置推导·克隆到任何机器重跑即用）
- :x4 车道确定性落位（`(4 - minute%10 +10)%10` 求下一个 :x4·不依赖注册时刻运气——BigStream 那种「从整点累加 8 分钟」写法会随注册时刻漂车道，此处已改确定性算法）
- 锁与幂等：round.lock 15min 陈旧接管 + 任务级 IgnoreNew + 25min 超时杀树 + finally 清锁
- mandate 首轮基线步（last_decision_rows=0 起步→首轮全读定基线·UTF-8 口径计数防 GBK 少读）+ P-35/36 首轮必做项
- 诚实标注：未实证项（计划任务触发态/codely PATH 上下文）已列「待主会话适配」·BigStream 专有业务内容零复制·计划任务注册本身未执行（授权=只备件）

## 读序

本件 → `iteration_prompt.txt`（司轮 mandate）→ `backlog.md`（认领板）→ 仓根 `tasks.md`/`BLUEPRINT.md`（正典）→ 集团 `cph4/cadence.md`（车道）
