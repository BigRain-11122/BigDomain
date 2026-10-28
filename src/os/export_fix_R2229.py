import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

with io.open(EXPORT, encoding="utf-8", newline="") as handle:
    d = json.load(handle)

# tick row -> 2229 (the label is data-externalized, keep it as read)
label = None
for row in d["results"]:
    if isinstance(row, list) and len(row) >= 2 and row[1] != "on" \
            and "tick" in str(row[1]):
        label = row[1]
        row[0] = "2229"
assert label is not None

d["outs"].insert(0, [
    "按品类的月度售后索赔压力面（api_category_claim_months）",
    "on",
    "新面 8/8 双跑逐字节同一（sha16 018F0A7C4BBA3C27）；记账律按"
    "当月且按开户时刻生效品类入桶、状态四态恒分区、钱只记在索赔侧、"
    "连续网格含诚实零月、未分类桶钉末且开关重算全部聚合、峰值不落"
    "零月、跨面与全市场索赔月面七项逐值相等；七条相邻套件全绿。"])
d["results"].insert(0, [
    "R2229",
    "P3 explore head claim: apimarket api_category_claim_months - the"
    " per-category monthly after-sales claim pressure face. Booking law"
    " (own opened_utc month AND the category in force at that instant),"
    " the api_claims status seam partitioning claim_count, money on the"
    " claim side so a refund with no claim never appears, the contiguous"
    " grid with an honest zero month, the uncategorized bucket last with"
    " the flag recomputing every aggregate, six bad flag forms failing"
    " closed before any read, cross-face identity on seven shared totals"
    " against api_market_claim_months, the earlier-month peak tie-break"
    " and three-instance byte identity over two restarts. SUITE PASS 8/8"
    " double-run byte-identical sha16 018F0A7C4BBA3C27; wired"
    " ledger-apimarket-categoryclaimmonths(8); seven adjacent suites"
    " green. Battery and matrix regeneration carried to R2230."])

sd = d["self_drive"]
sd["log_lines_in_window"] = 18
sd["substantive_non_idle_mention_lines"] = 18
sd["queue_explore_open"] = 2

body = json.dumps(d, indent=2, ensure_ascii=False)
body = body.replace("\r\n", "\n").replace("\n", "\r\n")
with io.open(EXPORT, "w", encoding="utf-8", newline="") as handle:
    handle.write(body + "\r\n")
print("export updated; outs", len(d["outs"]), "results", len(d["results"]))