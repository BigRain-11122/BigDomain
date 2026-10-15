# claim_R1990.py - append the R1990 claim note with the
# pre-registered AC-SSDP1..SSDP7 criteria to the explore-queue
# seed row (criteria registered BEFORE any suite code exists;
# honesty law). Verify-then-write, single anchor.
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
P_EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")

CLAIM_NOTE = (
    "——R1990 认领·判据预注册先行（本行即册·先于代码·AC-SSDP"
    " 前缀全仓 git grep 零占用实锚 2026-10-15·persist 例窗族"
    " R1889/R1900/R1902 判读+R1987 AC-SSBP 同族参照）："
    "**AC-SSDP1** 世界+重启前双窗快照族=R1989 同形世界〔五注册"
    "混合序+六收藏品+跨窗收置链·决序 beta/gamma/alpha/omega/"
    "delta〕pre-close 双窗读族 {1,2,50} 三帽：信封键集钉死"
    "（DUAL 四键/window 四键/行六键）+全窗区==直读 stats_board() "
    "行逐字节+帽区==全窗尾窗切片+镜像 SQL 第三径（limit=2）==帽区 "
    "id 序+window.total==5 诚实；**AC-SSDP2** 跨重启字节同一="
    "全栈 close（sh→led）→同 db_path+同 cfg 字节+无态 SecGate+同 "
    "sh_path rebuild→双窗读族三帽 dumps 逐字节同一（读时派生面="
    "跨重启零漂移例）+同参二读自稳；**AC-SSDP3** 重启后新注册双区"
    "续接=实例②注册 zeta-win 零事件行→全窗区 5→6〔零事件诚实零行"
    "入榜·决序尾 delta<zeta id 升序〕+window.total 5→6+帽区随尾窗"
    "滑移〔limit=2 尾 [omega,delta]→[delta,zeta]〕+五旧行字节"
    "冻结；**AC-SSDP4** 重启后新收置双区续接=实例② retract cl_d "
    "出 alpha+cross-place 入 delta→双区零缓存重算〔alpha places 恒 "
    "3·retracts 1→2·displayed_now 2→1·净流恒等全行 "
    "displayed_now==places−retracts〕+决序移位〔alpha 3p2r 与 "
    "beta/gamma 同分·id 升序 alpha 升首〕+未触行字节冻结"
    "〔beta/gamma/omega 行前后逐字节同〕；**AC-SSDP5** 第三实例"
    "三开稳定=实例② close→实例③ 同库三开→双窗读族==实例②终态"
    "逐字节同一+表计数恒定；**AC-SSDP6** 纯读律=读批（双窗 "
    "1/2/50×2+缺省全读）前后 showcases/exhibit_events/collectibles "
    "三表计数恒定+重复读对逐字节同一+stats_board_dual 方法段零 "
    "SQL 零写语句零 RNG 单推导源（体内恰一次 stats_board() 调用·"
    "AC-SSD6 重钉于重启语境）；**AC-SSDP7** 卫生=产品三件 sha256 "
    "前后双证零改动〔showcase.py+ledger config.json+lobby "
    "config.json〕+套件源纯 ASCII+真 import 语句行零网络库+注册表"
    "接线〔reconcile_all.py 含 ledger-showcase-statsdual-persist "
    "行〕+世界 tmp 仓外+判据数==7——〔2026-10-15 R1990 认领〕")

ANCHOR = "种子源=showcase.py stats_board_dual R1989 在册·R1989 收账补种）"


def main():
    raw = io.open(P_EXPLORE, encoding="utf-8", newline="").read()
    if raw.count(ANCHOR) != 1:
        print("ABORT: anchor count=%d" % raw.count(ANCHOR))
        return 2
    if "R1990 认领" in raw:
        print("ABORT: claim note already present")
        return 2
    idx = raw.index(ANCHOR) + len(ANCHOR)
    raw2 = raw[:idx] + CLAIM_NOTE + raw[idx:]
    io.open(P_EXPLORE, "w", encoding="utf-8", newline="").write(raw2)
    print("CLAIM-OK: R1990 note appended with AC-SSDP1..SSDP7 "
          "pre-registered (before code)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
