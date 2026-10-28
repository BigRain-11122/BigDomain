# -*- coding: utf-8 -*-
"""R2188 pre-registration: write AC-SSUP1..AC-SSUP8 into the
R2178 10/10 explore-queue row BEFORE the product code exists."""
import io

P = "state/queue/explore.md"
s = io.open(P, encoding="utf-8").read()

OLD = ("- [ ] P3 explore \u79cd\u5b50\uff08R2178 \u8865\u79cd\u00b710/10\uff09"
       "apimarket **\u5356\u5bb6\u4f9b\u7ed9\u603b\u89c8\u9762**"
       "\uff08api_seller_supply\uff09")
NEW = ("- [ ] P3 explore \u961f\u5934\u8ba4\u9886\uff08R2188\u00b7\u6e90=R2178 "
       "\u8865\u79cd 10/10\u00b7\u5224\u636e AC-SSUP1..AC-SSUP8 "
       "\u9884\u6ce8\u518c\u4e8e\u672c\u884c\u4e14\u5148\u4e8e\u4ee3\u7801\uff09\uff1a"
       "apimarket **\u5356\u5bb6\u4f9b\u7ed9\u603b\u89c8\u9762**"
       "\uff08api_seller_supply\uff09")
assert s.count(OLD) == 1, s.count(OLD)
s = s.replace(OLD, NEW)

TAIL = ("\u53bb\u91cd\u524d\u7f6e\uff1aapi_seller_supply / "
        "test_apimarket_sellersupply / seller_supply "
        "\u4e09\u951a\u96f6\u5360\u7528 rc=1\uff082026-10-28\uff09\u3002")
assert s.count(TAIL) == 1, s.count(TAIL)

ADD = (
 "\u3010AC-SSUP1 \u5951\u7ea6\u4e0e\u8bda\u5b9e\u7a7a\u3011="
 "\u4fe1\u5c01\u6070\u5341\u516d\u952e "
 "{dev_account,listing_count,live_listing_count,retired_listing_count,"
 "tracked_listing_count,unlimited_listing_count,sold_out_listing_count,"
 "low_stock_listing_count,total_effective_supply,total_sold,"
 "total_remaining,total_restocked_units,total_restock_count,"
 "low_stock_threshold,disclaimer,listings}\uff1b"
 "\u884c\u6070\u5341\u4e00\u952e {listing_id,listing_key,delisted,supply,"
 "base_supply,restocked_units,restock_count,sold,remaining,sold_out,"
 "low_stock}\uff1b\u524d\u7f00\u5408\u6cd5\u96f6\u6302\u724c\u5356\u5bb6="
 "\u5168\u8ba1\u6570 0\u3001\u4e09\u9879\u603b\u989d 0\u3001"
 "total_effective_supply \u4e0e total_remaining \u4e3a None\u3001"
 "listings \u7a7a\u3001disclaimer \u5e38\u9a7b\uff1b"
 "\u4e03\u5f0f\u574f\u8d26\u6237\u5f62\uff08None/EMPTY/SPACES/123/[]/"
 "{...}/\u88f8\u540d\uff09\u5168 E_AM_BAD_ACCOUNT\u3002"
 "\u3010AC-SSUP2 \u5728\u67b6/\u9000\u5f79\u5206\u533a\u3011="
 "listing_count==live_listing_count+retired_listing_count==len(listings)\uff1b"
 "\u9000\u5f79\u4ef6\u4fdd\u7559\u884c\u4e0e delisted=True\u3001"
 "\u5176\u5386\u53f2 sold/effective \u4e00\u5206\u4e0d\u52a8\uff1b"
 "relist \u540e delisted \u7ffb\u56de False \u4e14\u5176\u4f59\u952e"
 "\u9010\u5b57\u8282\u4e0d\u53d8\uff08\u5468\u671f\u5f8b\u7ecf _cycle_state "
 "\u5355\u7f1d\uff09\u3002"
 "\u3010AC-SSUP3 \u8ffd\u8e2a\u5206\u533a\u3011="
 "tracked_listing_count==\u884c\u4e2d supply \u975e None \u7684\u6570=="
 "listing_count\u2212unlimited_listing_count\uff1b"
 "\u4e0d\u9650\u91cf\u884c supply/remaining \u5168 None\u3001"
 "sold_out=False\u3001low_stock=False \u4e14\u94b3\u5236\u4efb\u4f55\u9608\u503c\u3002"
 "\u3010AC-SSUP4 \u805a\u5408\u5b88\u6052\u3011="
 "total_sold==\u03a3\u5168\u90e8\u884c sold\uff08\u542b\u4e0d\u9650\u91cf\u884c\uff09\uff1b"
 "total_effective_supply/total_remaining \u53ea\u7531\u8ffd\u8e2a\u884c"
 "\u6c42\u548c\uff08\u65e0\u8ffd\u8e2a\u884c\u5219 None\uff09\uff1b"
 "total_restocked_units/total_restock_count==\u03a3\u884c\uff1b"
 "sold_out_listing_count==\u03a3\u8ffd\u8e2a\u884c sold_out\uff1b"
 "low_stock_listing_count==\u03a3\u8ffd\u8e2a\u884c low_stock\u3002"
 "\u3010AC-SSUP5 \u7a00\u7f3a\u5f8b\u4e00\u6b65\u751f\u6548\u3011="
 "\u4e00\u7b14\u8d2d\u4e70\u5373\u964d\u8be5\u884c remaining \u5e76\u5728"
 "\u8017\u5c3d\u65f6\u7ffb sold_out/low_stock\uff1b\u9000\u6b3e\u628a"
 "\u5355\u4f4d\u8fd8\u67b6\u5e76\u540c\u65f6\u7ffb\u56de\uff1b\u8865\u8d27"
 "\u62ac\u5347 remaining \u5e76\u6e05 sold_out\u2014\u2014\u5168\u7ecf "
 "_supply_full \u5355\u7f1d\uff0c\u4e00\u6b21\u8bfb\u9762\u8c03\u7528\u5185"
 "\u542b\u5168\u90e8\u53d8\u5316\u3002"
 "\u3010AC-SSUP6 \u4f4e\u5e93\u5b58\u9608\u503c\u3011="
 "\u7f3a\u7701 1\uff1b\u663e\u5f0f int>=0 \u5408\u6cd5\uff1b"
 "\u9608\u503c 0 \u65f6\u53ea\u6709\u552e\u7f44\u884c\u7b97\u4f4e\u5e93\u5b58\uff1b"
 "\u9608\u503c\u2265remaining \u5373\u8ba1\u5165\uff1b\u975e int/\u5e03"
 "\u5c14/\u8d1f\u6570\u5168 E_AM_BAD_ARGS\uff0c\u4e14\u8d26\u6237\u95e8"
 "\u5148\u4e8e\u9608\u503c\u95e8\uff08\u53cc\u574f\u63a2\u9488\u7b54 "
 "BAD_ACCOUNT\uff09\u3002"
 "\u3010AC-SSUP7 \u7eaf\u8bfb\u4e0e\u9694\u79bb\u3011="
 "\u8c03\u7528\u524d\u540e\u5168\u90e8\u8868\u6458\u8981\u4e0e ledger_tx "
 "\u96c6\u6052\u5b9a\uff1b\u4ed6\u5356\u5bb6\u6302\u724c\u96f6\u6e17\u900f\uff1b"
 "\u884c\u6309 listing_id \u5347\u5e8f\u3002"
 "\u3010AC-SSUP8 \u8de8\u91cd\u542f\u4e0e\u63a5\u7ebf\u3011="
 "\u4e24\u91cd\u542f\u4e09\u5b9e\u4f8b\u9010\u5b57\u8282\u540c\u4e00\uff1b"
 "\u4ea7\u54c1\u6587\u4ef6\u54c8\u5e0c\u4e0d\u53d8\uff1brunner \u6807\u7b7e "
 "ledger-apimarket-sellersupply(8) \u5df2\u6ce8\u518c\u3002"
)

s = s.replace(TAIL, TAIL + ADD)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("PREREG OK")