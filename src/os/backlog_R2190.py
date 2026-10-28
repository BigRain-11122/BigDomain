import io
import os

BASE = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKLOG = os.path.join(BASE, "src", "os", "backlog.md")

LINE = (
    "- [x] P3 explore 队头认领（R2190·种子 R2189 1/10·判据 AC-SRR1..AC-SRR8"
    " 预注册于 state/queue/explore.md 同窗且先于代码）apimarket **卖家侧退款"
    "理由结构**（api_seller_refund_reasons）——缺口实证：api_refund_reasons"
    " 只给全市场理由分布、api_seller_quality 只给退款计数与金额，卖家读不到"
    "「我的退款都因何而起」，描述不实与服务中断在自己账上无法区分。产品=十七"
    "键信封／八键理由行：桶律与市场面同源（strip+lower·空理由诚实桶钉末且不计"
    "入 top_reason）、按存储 dev_account 归属（跨卖家隔离）、卖家购买分母取"
    " purchases×listings 连接、作用域守恒对齐原始表、share/avg/top_share 由行"
    "派生、reason_herfindahl 精确分数、市场域不自比（两基准 None）卖家域携带"
    "市场基准、纯读零 token、坏账户形五例 fail-closed。证据=SUITE 8/8 双跑判据"
    "行逐字节同一 sha16 aea3ccbc7c14b8f2（qa/apimarket-sellerrefundreasons-"
    "R2190-a.log + -b.log·各 1355B·crlf=0）+ 六邻域回归 qa/regression-R2190.log；"
    "接线 ledger-apimarket-sellerrefundreasons(8)；全量电池与矩阵再生列 R2191"
    " 首项债务。 [done 2026-10-28 R2190]")

with io.open(BACKLOG, encoding="utf-8") as handle:
    text = handle.read()
with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(LINE + "\n" + text)
print("prepended", len(LINE))