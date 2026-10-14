# claim_R1981.py - explore.md claim pre-registration (before code)
import io

QP = r"state\queue\explore.md"
q = io.open(QP, encoding="utf-8").read()
lines = q.splitlines()
hit = None
for i, ln in enumerate(lines):
    if ln.startswith("- [ ] ") and "honor_yearbook" in ln:
        hit = i
        break
assert hit is not None, "claim line not found"
old = lines[hit]
assert "R1979" in old and "git grep" in old, "unexpected line shape"
assert "R1981" not in old, "already claimed"

CLAIM = (
    "——2026-10-15 R1981 认领·判据预注册先于代码（本行即册·先于实现·"
    "AC-HYP 前缀全仓 git grep 零占用实锚 2026-10-15·栈勘正=种子行"
    "「db/cfg/pay」的 pay 字样系 member 族携带语·本面真实栈=civic.db+"
    "ledger.db+config 三件〔honorcert 纯编排面零自有存储·pay 域结构性"
    "零触及〕）：**AC-HYP1 重启前控制锚**=五户世界〔carol 12/aaron 7/"
    "bob 7 平局 id 升序/dave 3/erin 零行〕grant top-2 后年册钉死="
    "[(1,carol,12),(2,aaron,7)] 全 item_id 回声+信封键集恰五键"
    "{year,yearbook,certified_count,board_size,disclaimer}+certified_count"
    "==2==board 行内计数+合成律=年册行==honor_certs certified 子集逐行"
    "（board_rank==rank·points·item_id）+零 earn 年 2027 年册=诚实空"
    "（[]+双零计数）+双调 dumps 逐字节同一；**AC-HYP2 三件全栈跨重启逐"
    "字节同一**=cl.close→cv.close→led.close〔honorcert 面零自有存储零"
    "close〕→Ledger+CivicPointsFace+CollectiblesFace+HonorCertFace 同"
    "路径同 config 重建→年册（2026 与 2027 两面）重读==重启前快照 dumps"
    " sort_keys 逐字节同一（单源派生面零内存态漂移）；**AC-HYP3 重启后"
    "活态续接**=实例②上 erin 4×poll earn〔board 移动 erin 20 榜首〕→"
    "re-grant top-2=增量愈合〔granted=1 already=2·批中断愈律跨重启存活"
    "〕→年册 3 行=[(1,erin),(2,carol),(3,aaron)]〔aaron 掉出 top-2 仍"
    "保年册行+board_rank 随新榜位=R1979 AC-HY4 语义跨重启存活〕+全行"
    " item_id 回声+board_size=5·dave 2027 earn+grant top-1→年册 2027=1"
    "行〔跨年隔离跨重启存活〕+2026 年册在 2027 授证后复读逐字节不动"
    "〔跨读隔离〕；**AC-HYP4 年闸跨重启存活**=实例② CountingCivic 包裹"
    "上九坏年形态〔int/bool/短/长/字母/带符/空白/Unicode 数字/None·"
    "镜像 R1979 口径〕全拒 E_HC_BAD_ARGS+honor_board 调用计数==0〔门前"
    "拒零引用调用〕+civic 五表快照前后同一；**AC-HYP5 纯读律+零 token "
    "计**=读批〔年册双调+honor_certs+2027 面〕前后 civic 五表+"
    "collectibles+ledger_tx/ledger_entries 计数恒定+ledger_tx==0 恒"
    "〔证书=平台授予零 token 律贯穿全窗〕+年册双调 dumps 逐字节同一；"
    "**AC-HYP6 第三实例复读同一+产品件 sha 双证+卫生**=实例② close→第"
    "三实例同路径重建→年册两面连续两读==实例②终态逐字节同一+相互同"
    "一〔复读纯度〕+产品件 sha256 前后逐位同一〔honorcert.py/"
    "civicpoints.py/collectibles.py/本件零改动·shipped config.json 逐"
    "字节稳〕+套件源纯 ASCII+真 import 语句行零网络库〔R1678 自指假阳"
    "性教训〕+世界 db 系统临时仓外+honor_yearbook 方法体零写语句 "
    "inspect 机检——载体：src/sandbox/ledger/test_honorcert_yearbook_"
    "persist.py+reconcile_all SUITES 增一行 ledger-honorcert-"
    "yearbookpersist 判据 6+证据 qa/honorcert-yearbookpersist-R1981.log"
    "（套件双跑+RUNNER 全量+矩阵再生三节）"
)
lines[hit] = old + CLAIM
io.open(QP, "w", encoding="utf-8", newline="\n").write(
    "\n".join(lines) + "\n")
print("CLAIM-PRE-REGISTERED idx=%d len+=%d" % (hit, len(CLAIM)))
