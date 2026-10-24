# -*- coding: utf-8 -*-
"""R2110 export row-shape repair: keep the file's list-row convention."""
import io
import json

EP = "docs/status-export.json"
exp = json.loads(io.open(EP, encoding="utf-8").read())

exp["outs"] = [row for row in exp["outs"]
               if not (isinstance(row, dict)
                       and row.get("artifact", "").endswith(
                           "apimarket-report-buyers.html"))]
exp["results"] = [row for row in exp["results"]
                  if not (isinstance(row, dict)
                          and row.get("suite", "").startswith(
                              "test_apimarket_report_buyerhistory"))]

exp["outs"].insert(0, [
    "apimarket 结算报告买家全史档案段（library/watchlist/refund/"
    "rating-history 四面接线 + REPORT_SCHEMA 4→5）",
    "on",
    "R2110：四张买家侧历史面此前零产品调用点，且 api_rating_history 的 "
    "rating_id 入参无任何列表级读面暴露（事实不可达）；本窗给评分行加法暴露 "
    "rating_id，每买家名下新增四张子表（持有库/关注/退款/评分史），"
    "空态诚实呈现；呈看件 preview/apimarket-report-buyers.html"])
exp["results"].insert(0, [
    "R2110",
    "R2110: buyer history section on the settlement report. The four "
    "buyer-side faces (api_library, api_watchlist, api_refund, "
    "api_rating_history) had zero product call sites, and the last one "
    "was unreachable by construction because its only handle, rating_id, "
    "was never exposed on a listing-wide face - the rating rows now "
    "carry it as an additive key. collect_buyer_history() reads the four "
    "faces once per buyer into a history block with exactly "
    "BUYER_HISTORY_KEYS; refund rows are the provenance envelopes minus "
    "the resident disclaimer; rating_history_rows folds base-only "
    "ratings into one base row and revised ones into one row per "
    "revision. render_html adds four sub-tables per buyer with honest "
    "empty states; REPORT_SCHEMA moves 4 -> 5 additively with every v4 "
    "value equal to its direct face call and a legacy degrade path. "
    "Suite 10/10 double-run sha16 50999cbdeecb5975; battery 315/315 + "
    "controls 7/7 404.5s; matrix 315/2628 byte-identical; census "
    "CENSUS-COMPLETE files=1769 flags=0. Repairs disclosed: the dossier "
    "and workbench suites pinned the exact buyer key set and the dossier "
    "suite pinned schema == 4, so both now pin a literal v4 SUBSET and "
    ">= 4; rich_world wrote watches with the real clock, so the "
    "determinism face failed until both clocks were pinned."])

tick_rows = [row for row in exp["results"]
             if isinstance(row, list) and len(row) >= 2
             and row[1] == "OSLoop 执行 tick"]
assert len(tick_rows) == 1, len(tick_rows)
tick_rows[0][0] = "2110"

exp["self_drive"]["log_lines_in_window"] = 34

io.open(EP, "w", encoding="utf-8", newline="\n").write(
    json.dumps(exp, ensure_ascii=False, indent=1) + "\n")
print("rows fixed: tick=%s outs=%d results=%d"
      % (tick_rows[0][0], len(exp["outs"]), len(exp["results"])))