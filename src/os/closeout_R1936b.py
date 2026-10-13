"""R1936 closeout part 2 (resume after anchor fix): the main script
applied tech.md + state.json + benchmarks before the wall anchor
mis-read abort; this companion finishes wall W24 rows + smoke evidence
pair + heartbeat + export. Single-shot companion to closeout_R1936.py
(same single-shot pattern as closeout_R1876 + export_refresh_R1876)."""

import datetime as _dt
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))


def read_txt(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        raw = fh.read()
    return raw.decode("utf-8")


def write_txt(rel, text):
    with open(os.path.join(ROOT, rel), "wb") as fh:
        fh.write(text.encode("utf-8"))


def eol_of(text):
    return "\r\n" if "\r\n" in text else "\n"


def must_count(text, needle, n, what):
    c = text.count(needle)
    assert c == n, "anchor %r count=%d expected=%d (%s)" % (needle, c, n, what)


# ------------------------------------------------------- intelligence-wall
P_WALL = "docs/research/intelligence-wall.md"
wall = read_txt(P_WALL)
WNL = eol_of(wall)
w24_main = (
    "| W24 | 2026-10-14 | 《互联网广告管理办法》官方全文（国家市场监督管理"
    "总局令第 72 号·2023-02-25 公布·**2023-05-01 施行**·32 条·2016《互联网"
    "广告管理暂行办法》同时废止·A 级 samr.gov.cn 总局规章发布栏）：**第九条"
    "可识别性律**——互联网广告应当可识别＋竞价排名显著标明「广告」＋**知识"
    "介绍/体验分享/消费测评推销并附加购物链接=显著标明「广告」**〔种草带货"
    "条款〕；**第十条弹窗一键关闭律**——显著标明关闭标志+确保一键关闭+四禁"
    "〔无标志/计时结束才能关/关闭标志虚假难定位/两次以上点击/关闭后继续弹出〕"
    "+**开屏广告适用**〔与 W22 第五条八款叠双层〕；**第十一条禁误导点击**"
    "〔虚假更新提示/虚假播放标志/**虚假奖励承诺**=anti-farm 广告档红线〕；"
    "**第十二条未成年人媒介广告禁令**〔医疗药品保健食品特医食品医疗器械"
    "化妆品酒类美容+不利未成年人网络游戏广告=未成年人面第四层叠〕；"
    "**第十三至十五条广告档案律**〔广告主自建渠道=发布者责任+承接登记/审核/"
    "档案制度+**档案保存 ≥3 年**+配备广告审核人员+**算法推荐广告=推荐规则+"
    "投放记录入档案**〕；**第十六条平台六义务**〔发布广告用户身份记录 ≥3 年+"
    "监测排查通知改正删除屏蔽断链+投诉举报便捷入口+不得阻挠监测+配合调查+"
    "警示暂停终止措施〕；**第十七条禁扰推送**〔未经同意禁向交通工具/导航/"
    "智能家电发送广告+禁邮件/即时通讯附加广告〕；第十九条直播带货责任分配；"
    "**罚则族**〔弹窗/误导 5 千-3 万+平台 1 万-5 万+明知不制止=广告法 63 条+"
    "严重违法失信名单〕 | A·web（samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2023/"
    "art_d93a579afd45413e8576e4623fab348f.html·总局规章发布栏·2026-10-14 "
    "~02:0x 直采·search 定位 1 试双证） | **P-47⑤ ads 广告位读面族〔tech 队列"
    "在册=W24 法源直接供给：可识别标注+一键关闭+投放记录档案 ≥3 年=例窗设计"
    "判据面〕**+P-47③ UGC〔第九条种草链接「广告」标注+第十六条平台监测处置面〕"
    "+P-47② anti-farm〔第十一条虚假奖励禁令〕+未成年人广告层〔W11/W17/W22 "
    "第四叠〕+benchmarks §①/§②/§③ | 拍已验证 |")
w23_main_head = "| W23 | 2026-10-13 |"
must_count(wall, w23_main_head, 1, "wall W23 main row")
if w24_main not in wall:
    w23_end = wall.find(WNL, wall.find(w23_main_head))
    wall = wall[:w23_end] + WNL + WNL + w24_main + wall[w23_end:]
w23_concl_head = "| W23→数据安全条例入册"
must_count(wall, w23_concl_head, 1, "wall W23 conclusion row head")
w24_concl = (
    "| W24→广告管理办法入册（可识别性律+种草链接标广告+弹窗一键关闭四禁+"
    "开屏适用+档案 ≥3 年+算法推荐投放记录入档+平台六义务+未成年人广告专属"
    "禁令+罚则 5 千-5 万档） | ①法规修改指针：`docs/global-benchmarks.md` "
    "§①广告法规块+§②行 9+§③源行+§④记录行（已刷新 R1936）②规格消费落点："
    "P-47⑤ ads 广告位读面族〔tech 队列在册项=例窗设计判据面：可识别标注+"
    "一键关闭+投放档案 ≥3 年〕+P-47③ UGC 种草标注+P-47② anti-farm 虚假奖励"
    "禁令（生产判据面增补=下轮 spec 修订窗消费） | 已入册（生产判据面增补="
    "下轮 spec 修订窗消费） |")
if w24_concl not in wall:
    w23c_end = wall.find(WNL, wall.find(w23_concl_head))
    wall = wall[:w23c_end] + WNL + w24_concl + wall[w23c_end:]
write_txt(P_WALL, wall)
print("wall: W24 main + conclusion rows ok")

# ------------------------------------------------------------- smoke pair
smoke_text = """BigDomain QA smoke evidence - round R1936 - 2026-10-14 +08:00
day work: (1) QA charter daily crawl W24 delivered - Internet Advertising
Administrative Measures of the PRC (SAMR Order No. 72, published
2023-02-25, effective 2023-05-01, 32 articles, repeals the 2016 interim
measures) official fulltext direct-captured into benchmarks sections
1/2/3/4 + intelligence-wall W24 rows (main + conclusion tables, R1884
dual-row precedent); (2) product line (tech-queue head): ledger
observation read-face family cross-restart persistence example
AC-OBP1..OBP7 suite 7/7 double-run byte-identical sha16 0ae114d64e2d4703,
RUNNER 174/174 criteria 1557, matrix regen --check identical; the daily
carrier log doubles as the 2026-10-14 daily reconcile (R1935 carry-forward
debt cleared same window); (3) orphan-payload takeover closeout honestly
noted: the crashed R1936 attempt left suite+registry+matrix+evidence+daily
reconcile on disk (zero failed-run artifacts) and died before collection;
this window re-verified live (suite re-run PASS + matrix --check) and
closed out state/export/heartbeat/commit per R1922/R1924/R1925/R1934
lineage; (4) five-sill GORD one new row (@bm-c V3 refire-batch receipt,
BigStream MV family, zero BigDomain execution face -> acknowledged
no-action, baseline 375->376) + [DEC] PASS rows=309 flat zero new owner
token.

--- (1) W24 crawl (group QA Smoke Test charter v1.0, orders L254
2026-09-28; docs/global-benchmarks.md + docs/research/intelligence-wall.md)
---
W24 = Internet Advertising Administrative Measures (SAMR Order No. 72),
official fulltext (A-grade; samr.gov.cn regulation-disclosure column;
search located 1 try, direct capture 1 get 0 negative; 32 articles
verified article by article).
key clauses consumed into benchmarks: art. 9 identifiability (competitive
ranking + knowledge-sharing/review-with-purchase-link = mark "ad"),
art. 10 popup one-click-close four prohibitions + open-screen ads apply,
art. 11 anti-deceptive-click (fake reward promises = anti-farm red line),
art. 12 minors-medium ad ban (fourth minors layer), arts. 13-15 ad-archive
>= 3 years + algorithm-recommendation ad records into archive, art. 16
platform six duties, art. 17 no-disturb push (email/IM attach ban),
art. 19 livestream liability, arts. 23-31 penalty tiers 5k-50k CNY.
consumption: P-47(5) ads read-face family (tech-queue row in place =
direct legal supply: identifiability + one-click-close + archive >= 3y
as the persist-window design criteria face) + P-47(3) UGC seeding-label
+ P-47(2) anti-farm fake-reward ban + minors ad layer fourth stack.

--- (2) product line (P2 tech FIFO head: ledger observation persist) ---
suite test_observation_persist.py SUITE 7/7 first-run green + double-run
stdout byte-identical sha16 0ae114d64e2d4703; three-instance world:
anchor (four accounts, two strategies, alice single-permanent + bob pass
window 2099-01 bound to real spend txs, four gate probes all rejected,
digest c184654e4fe640cb) -> two-piece reverse-order close/reopen with
13 read faces + 5 balances byte-identical (registered_utc persisted value,
no clock echo) -> five restart-surviving gates + post-restart real-path
continuation (bob 2099-02 + dave beta bound to new real spend txs,
zero-cache recompute) -> frozen faces + window isolation (bob's 2099-01
pass does not cover 2099-03; alice single at far month) -> pure-read law
-> third instance stability; config/observation/ledger sha16 unchanged;
RUNNER PASS 174/174 criteria 1550->1557 controls 7/7 251.4s =
qa/reconcile-daily-20261014.log (dual carrier = the 2026-10-14 daily
reconcile, sentinel ok + profile ok + census DRIFT-CLEAN); matrix regen
174/1557 green --check byte-identical (17105 bytes).

--- (3) takeover closeout (R1922/R1924/R1925/R1934 lineage) ---
crashed R1936 payload verified PRESENT on disk: suite file + SUITES
registry row + tech.md claim row (checkbox flipped, criteria
pre-registered, done-note missing) + matrix updated + five-section
evidence + the 2026-10-14 daily reconcile; zero failed-run artifacts;
this window live re-verified (suite re-run SUITE PASS 7/7 + matrix
--check byte-identical) and closed out: tech done-note + venue reseed
(queue_tech_open 10->10) + state/export/heartbeat + directed commit.

--- (4) five-sill deltas honestly noted ---
GORD gord_new_rows=1: 10-13 23:5x @bm-c V3 refire-batch receipt row =
BigStream MV family execution face, zero BigDomain face -> acknowledged
no-action, baseline 375->376; DEC PASS rows=309 flat, zero new owner
token; [QA] FLAG at round start (smoke png/log 0 today + benchmarks not
refreshed today) = this round's main repair face, cleared by W24 + the
smoke evidence pair below; TREE dirty 7 files = the orphan payload
(takeover trigger).

self-check four items vs charter: daily crawl = W24 delivered;
benchmark refreshed = 2026-10-14 (next 7-day window 2026-10-21; charter
15h cap refreshed same day); research chain = A-grade 1-try search
double-verified zero negative; signal wall = W24 rows in place (main +
conclusion). evidence pair = this log + rendered png.
"""
P_SMOKE = os.path.join(ROOT, "qa", "smoke-R1936.log")
with open(P_SMOKE, "wb") as fh:
    fh.write(smoke_text.encode("utf-8"))
print("smoke log written:", len(smoke_text.encode("utf-8")), "bytes")

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

FONT_PATH = r"C:\Windows\Fonts\consola.ttf"
font = ImageFont.truetype(FONT_PATH, 15)
wrapped = []
for raw_line in smoke_text.split("\n"):
    line = raw_line.rstrip()
    if not line:
        wrapped.append("")
        continue
    while len(line) > 112:
        wrapped.append(line[:112])
        line = line[112:]
    wrapped.append(line)
if wrapped and wrapped[-1] == "":
    wrapped.pop()
PAD = 26
LINE_H = 22
width = 1180
height = PAD * 2 + LINE_H * len(wrapped)
img = Image.new("RGB", (width, height), (26, 26, 26))
draw = ImageDraw.Draw(img)
y = PAD
for line in wrapped:
    if line:
        draw.text((PAD, y), line, fill=(212, 212, 212), font=font)
    y += LINE_H
P_PNG = os.path.join(ROOT, "qa", "smoke-R1936.png")
img.save(P_PNG, "PNG")
print("smoke png written:", os.path.getsize(P_PNG), "bytes", img.size)

# ------------------------------------------------------------- heartbeat
P_HB = "heartbeat.txt"
hb = read_txt(P_HB)
HNL = eol_of(hb)
now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
hb_row = ("%s | BigDomain OSLoop alive | tick 1936 | R1936: observation "
          "cross-restart persist suite 7/7 double-run byte-identical "
          "sha16 0ae114d64e2d4703 + orphan-payload takeover closeout + "
          "RUNNER 174/174 criteria 1550->1557 (qa/reconcile-daily-"
          "20261014.log) + W24 ad-law crawl + smoke pair "
          "[via BigDomain-OSLoop]") % now
if "R1936: observation" not in hb:
    if not hb.endswith(HNL):
        hb += HNL
    hb += hb_row + HNL
    write_txt(P_HB, hb)
    print("heartbeat row appended")
else:
    print("heartbeat row already present, skip")

# ---------------------------------------------------------------- export
sys.path.insert(0, BASE)
import check_export_consistency as cec  # noqa: E402

derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1936, "stale tick: %s" % state_obj["tick"]
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
export_obj["ceo_face"]["current"] = (
    "R1936：观测面（observation）做了「关服务重开、策略/授予/五门禁照常"
    "工作」验证——接管窗：上一崩溃轮已把套件与全套证据跑齐（双跑逐字节"
    "同一），本轮复验后收口；总回归 174 套件全绿；每日 crawl 同窗交付 W24"
    "《互联网广告管理办法》直采入册，证据在 qa/observation-persist-R1936.log"
    " 与 qa/reconcile-daily-20261014.log")
export_obj["ceo_face"]["latest_artifact"] = (
    "src/sandbox/ledger/test_observation_persist.py + qa/"
    "observation-persist-R1936.log + qa/reconcile-daily-20261014.log，"
    "2026-10-14·174 套件 1557 判据 green·新增 ledger-observation-persist"
    "·观测面跨重启持久化例窗；benchmarks W24 广告法规块+smoke-R1936 证据对")
export_obj["ceo_face"]["next_milestone"] = (
    "下轮 R1937：tech 队列 FIFO=ledger expedite persist 认领（R1935 补种）"
    "+轮首首测 fold R508 裁定（收账后水位预测越 78500B 线）")
if not export_obj["results"] or export_obj["results"][0][0] != "R1936":
    res_row = [
        "R1936",
        ("R1936 ledger observation cross-restart persistence suite 7/7 "
         "(P2 tech FIFO head = the R1935 closeout pointer; criteria "
         "AC-OBP1..OBP7 pre-registered in tech.md before code): orphan-"
         "payload takeover closeout per the R1922/R1924/R1925/R1934 lineage "
         "- the crashed R1936 attempt left suite+registry+matrix+five-section "
         "evidence+the 2026-10-14 daily reconcile on disk with zero "
         "failed-run artifacts; this window re-verified live (suite re-run "
         "PASS + matrix --check byte-identical) and closed out. Three-"
         "instance world: anchor (four accounts, two strategies, alice "
         "single-permanent + bob pass window bound to real spend txs, four "
         "gate probes rejected, digest c184654e4fe640cb) -> two-piece "
         "reverse-order close/reopen with 13 read faces + 5 balances "
         "byte-identical (registered_utc persisted value, no clock echo) -> "
         "five restart-surviving gates -> post-restart real-path "
         "continuation with SQL cross-checks and zero-cache recompute -> "
         "frozen faces + window isolation -> pure-read law -> third-"
         "instance stability; RUNNER PASS 174/174 criteria 1550->1557 "
         "controls 7/7 251.4s = qa/reconcile-daily-20261014.log (dual "
         "carrier = the daily reconcile, sentinel ok + profile ok + census "
         "DRIFT-CLEAN); matrix regen 174/1557 green --check identical; "
         "tech consume 1 reseed 1 (venue persist candidate added, "
         "queue_tech_open 10->10, next FIFO head = ledger expedite "
         "persist). QA charter daily crawl W24 = Internet Advertising "
         "Administrative Measures (SAMR Order No. 72) official fulltext "
         "direct-captured into benchmarks + intelligence-wall W24 rows; "
         "benchmarks_refreshed=2026-10-14; smoke-R1936 log+png pair "
         "delivered; GORD one new row (@bm-c V3 refire receipt, BigStream "
         "family, acknowledged no-action, baseline 375->376).")]
    export_obj["results"].insert(0, res_row)
if len(export_obj["results"]) > 40:
    export_obj["results"] = export_obj["results"][:40]
sd = dict(derived)
sd["method"] = ("machine-derived from state.json log per BD-PROP-001"
                " caliber (check_export_consistency.recompute)")
export_obj["self_drive"] = sd
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
print("export refreshed: queues=%d/%d/%d tick=%d evidence=%s"
      % (derived["queue_main_open"], derived["queue_tech_open"],
         derived["queue_explore_open"], state_obj["tick"],
         derived.get("evidence_file", "n/a")))
print("R1936 closeout part 2 complete")
