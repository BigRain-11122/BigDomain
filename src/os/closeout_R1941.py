# -*- coding: utf-8 -*-
"""R1941 closeout: ledger companion cross-restart persist delivery
(the companion seat of the R1886 persist family; P2 tech FIFO head
= the R1940 closeout pointer). tech.md done-note + apimarket
reseed, state.json tick/log/round-line, heartbeat row, export
refresh (F3 derived via consistency tool). All edits anchor-exact
with fail-fast asserts; EOL preserved per file.
Round scoring: 2 (runnable artifact, Executive Protocol v1.1)."""

import datetime as _dt
import io
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


# ---------------------------------------------------------------- tech.md
P_TECH = "state/queue/tech.md"
tech = read_txt(P_TECH)
NL = eol_of(tech)
cmp_open_head = "- [ ] ledger companion 伴生读面族跨重启持久化例窗（R1934 补种"
must_count(tech, cmp_open_head, 1, "companion open row head")
tech = tech.replace(
    "- [ ] ledger companion 伴生读面族跨重启持久化例窗（R1934 补种",
    "- [x] ledger companion 伴生读面族跨重启持久化例窗（R1934 补种", 1)
done_row_head = "- [x] ledger companion 伴生读面族跨重启持久化例窗（R1934 补种"
must_count(tech, done_row_head, 1, "companion done row head")
done_note = (
    "——[done 2026-10-14 R1941]（执行注记：套件 test_companion_persist.py "
    "SUITE 7/7 首跑 5/7〔AC-CMP1/CMP4 两败=pool 期望值笔误：ledger spend "
    "对腿回流 pool:reserve=产品行为正身〔ads 席 17150=20000−3000+150 同律互"
    "证〕→判据注册行同轮勘正 19000→19330/19090→19420〔R1883 AC-PN27 同轮笔"
    "误修先例〕后复跑全绿〕+双跑 stdout 逐字节同一 sha16 dff152fd13809909"
    "〔rc 0/0·掩码口径=created_utc/spend_tx/tx 三掩码进证据 digest·全字段"
    "落位比较不掩码〕三实例世界真产品径〔Ledger+SecGate〔lobby 产品引用注入"
    "非复制·bad_word=词表运行时载入·源纯 ASCII 律不破〕+CompanionFace 三件"
    "套〕——①锚世界〔通行证谱 jan alice/bob fee120+feb carol fee90 各绑真 "
    "spend tx·四余额 180/380/110/19330+对话谱 alice 双轮〔各归档 memory "
    "preference 同 kind 二连=append 非 unique〕+bob 单轮+carol feb 单轮=8 "
    "msg〔ai_label 0/1 交替结构标签谱〕+memory 2 行全锚 companion 回复〕"
    "+can_ 五探针〔a/b jan True·c jan False·c feb True·a feb False〕"
    "+transcript 四窗 4/2/0/2+memory 三视图 2/0/0+subs 三视图 1/1/1+表计"
    "数 subs 3/msgs 8/memories 2/spend-tx 3+五门探针全拒〔dup-pass/"
    "E_CP_PASS_DUP·denied/E_CP_DENIED·content/E_CP_CONTENT_REJECTED·"
    "bad-month/E_CP_BAD_MONTH·gate-fault/E_CP_GATE_ERROR〔故障闸注入 "
    "face 重建同库 fail-closed〕〕探针批前后计数电池+读面电池零漂移"
    "②cf.close→led.close→同 db/cfg+SecGate+CompanionFace 新实例→电池逐字"
    "节==关前快照〔created_utc=库存值非钟回声·派生面零内存态漂移〕③五探针"
    "跨重启全拒同码+计数电池冻结〔零扣费零新行零 memory 追加〕④真径续写"
    "〔carol 补购 jan fee90 绑真 spend tx〔SQL cross type=spend+debit 腿·"
    "tx_id 不入证〕→denied→allowed 翻转证〔can_c_jan False→True+tr_c_jan "
    "0→2〕+carol/bob 各续一轮+memory 各 1 行→subs 3→4/msgs 8→12/memories "
    "2→4/spend-tx 3→4+四余额 180/380/20/19420+触面零缓存重算〔新行 "
    "msg_id/memory_id 递归续尾〕+非触面冻结〔tr_a_jan 逐字节==锚〕〕⑤冻结"
    "面+门跨重启〔三表既存行 SQL 全行快照逐字节冻结〔subs 前 3 行含 "
    "bound_spend_tx+granted_utc/msgs 前 8 行含 created_utc/memories 前 2 "
    "行含 content_json〕+dup 门〔carol 持 jan 同月新 ref 拒 E_CP_PASS_DUP "
    "ref-blind 零扣费〕+denied 门〔alice 无 feb 通行证拒〕+content 门〔bob "
    "bad_word 拒零行〕〕⑥纯读律电池双读逐字节同一+表计数恒定⑦实例③三开=="
    "实例②终态逐字节+config/ledger/companion/sec_gate 四 sha16 零改动+套件"
    "源纯 ASCII〔0 non-ascii〕+零网络 import+世界 tmp 仓外〕——RUNNER "
    "PASS 179/179 判据 1585→1592 controls 7/7 304.7s=qa/reconcile-all-"
    "R1941.log〔SUITES 178→179·ledger-companion-persist 席 0.8s·census "
    "DRIFT-CLEAN flags=0·指纹 CLEAN domains=5〕+矩阵再生 179/1592 green "
    "--check byte-identical〔17468B〕——证据六节 qa/companion-persist-"
    "R1941.log〔套件双跑+RUNNER tail+矩阵双跑+census+指纹+git 卫生〕·LF "
    "归一单写者驱动=src/os/evidence_R1941.py〔R1932/R1937..R1940 模板族〕"
    "——tech consume 1 reseed 1〔queue_tech_open 10→10：companion done "
    "−1+ledger apimarket 开发者 API 市场读面族 persist 补种 +1〔查重当日实"
    "跑：注册表零 apimarket-persist 位+AC-AMP 全仓 git grep rc=1+"
    "apimarket_persist 同扫零占用+test_apimarket.py close 五命中全为收尾清"
    "理/门故障探针闭合非重启例=单 Ledger 实例真活候选〕·下轮 FIFO 队头="
    "ledger props 道具/装扮经济面 persist〔R1937 补种·最老开项〕〕）")
v_idx = tech.find(done_row_head)
assert v_idx >= 0, "companion done row not found"
v_end = tech.find(NL, v_idx)
assert v_end >= 0, "companion row has no line end"
tech = tech[:v_end] + done_note + tech[v_end:]
reseed_row = (
    "- [ ] ledger apimarket 开发者 API 市场读面族跨重启持久化例窗（R1941 补"
    "种·查重前置已过：注册表 label 全形扫描零 apimarket-persist 命名位 变体"
    "〔ledger-apimarket 基础席 7 判据在册=R1763 developer API marketplace "
    "face=套件存在锚〕+套件源面扫描 test_apimarket.py close 五命中全为收尾"
    "清理/门故障探针闭合非重启例〔单 Ledger 实例=零 close→reopen 重启例〕="
    "真活候选·AC-AMP 前缀全仓 git grep 零占用 2026-10-14〔rc=1·"
    "apimarket_persist 同扫零占用〕·persist 例窗族 R1886 起谱系）")
devshare_head = "- [ ] ledger devshare 开发者分成读面族跨重启持久化例窗（R1940 补种"
must_count(tech, devshare_head, 1, "devshare row head")
idx = tech.find(devshare_head)
end = tech.find(NL, idx)
assert end >= 0, "devshare row has no line end"
tech = tech[:end + len(NL)] + reseed_row + tech[end + len(NL):]
write_txt(P_TECH, tech)
print("tech.md: companion done-note + apimarket reseed ok")

# ------------------------------------------------------------- state.json
P_STATE = "src/os/state.json"
state = read_txt(P_STATE)
SNL = eol_of(state)
must_count(state, '"tick": 1940,', 1, "tick")
state = state.replace('"tick": 1940,', '"tick": 1941,', 1)
tok_anchor = "2026-10-14 R1940 tokens:"
must_count(state, tok_anchor, 1, "R1940 tokens anchor")
close_anchor = SNL + "    ]"
assert state.rstrip().endswith("}"), "state tail not }"
cidx = state.rfind(close_anchor)
assert cidx > state.find(tok_anchor), "log close before tokens anchor"
last_item_end = cidx
prefix = state[:last_item_end]
assert prefix.endswith('"'), "last log item does not end with quote"
round_line = (
    "2026-10-14 R1941 ledger companion 伴生读面族跨重启持久化例窗交付轮"
    "（P2 tech FIFO=R1940 收账指针·轮计分 2=可跑实物）：五静面——GORD "
    "gord_new_rows=0·DEC 行基线 309 持平零新·LEDGER atbd=0·ORD 持平·BENCH "
    "当日 10-14·QA 当日证据在盘零重跑·HB lag=0·TREE clean——STATE 面轮首 "
    "FLAG eol_bare_lf=25〔R1940 收账写裸 LF〕当轮修复〔logs_toolkit eol "
    "--fix --execute·post 74422B·post_bare_lf=0·predicted_eq_actual〕——"
    "判据 AC-CMP1..CMP7 预注册先于代码〔tech.md 认领行在册〕：同轮勘正两枚"
    "=pool 期望值 19000→19330/19090→19420〔ledger spend 对腿回流 "
    "pool:reserve=产品行为正身·ads 席 17150=20000−3000+150 同律互证·R1883 "
    "AC-PN27 同轮笔误修先例·首跑 5/7 两败→修后全绿〕——套件 "
    "test_companion_persist.py SUITE 7/7+双跑 stdout 逐字节同一 sha16 "
    "dff152fd13809909：三实例世界真产品径〔①锚世界=通行证谱 jan alice/bob "
    "fee120+feb carol fee90 各绑真 spend tx+对话谱 8 msg 结构标签 0/1 交替"
    "+memory 2 行 append 非 unique+can_ 五探针+transcript 四窗 4/2/0/2+表"
    "计数 subs 3/msgs 8/memories 2/spend-tx 3+五门探针全拒〔含 gate-fault="
    "故障闸 face 重建同库 fail-closed〕电池零漂移②close→reopen 电池逐字节"
    "==关前〔created_utc=库存值〕③五探针跨重启同码+计数冻结④真径续写 "
    "carol 补购 jan〔SQL cross type=spend+debit〕denied→allowed 翻转+两新"
    "轮两 memory→subs 4/msgs 12/memories 4/spend-tx 4+四余额 "
    "180/380/20/19420⑤三表既存行 SQL 全行快照逐字节冻结+dup/denied/"
    "content 门跨重启⑥纯读律双读同一⑦实例③==②终态+四 sha16 零改动+纯 "
    "ASCII+零网络+tmp 仓外〕——RUNNER PASS 179/179 判据 1585→1592 "
    "controls 7/7 304.7s=qa/reconcile-all-R1941.log〔SUITES 178→179·census "
    "DRIFT-CLEAN flags=0·指纹 CLEAN domains=5〕+矩阵再生 179/1592 green "
    "--check byte-identical〔17468B〕——证据六节 qa/companion-persist-"
    "R1941.log·驱动=src/os/evidence_R1941.py〔R1932..R1940 模板族〕——tech "
    "consume 1 reseed 1〔queue_tech_open 10→10：companion done −1+ledger "
    "apimarket 开发者 API 市场读面族 persist 补种 +1〔查重当日实跑：注册表"
    "零 apimarket-persist 位+AC-AMP git grep rc=1+test_apimarket.py close "
    "五命中全为收尾清理非重启例=真活候选〕·下轮 FIFO 队头=ledger props 道"
    "具/装扮经济面 persist〔R1937 补种·最老开项〕〕——收账后水位预测 ~76.6KB"
    " 未越 78500B 线=零 fold〔下轮轮首首测裁定候选〕")
tokens_line = (
    "2026-10-14 R1941 tokens: local=unmeasured api=0 api_reason=纯本地进程件"
    "（五静扫描+EOL 修复+套件双跑+RUNNER 全量回归+矩阵+census+指纹+收账手"
    "术全本地跑·零外部 API 触点·三问门未涉及）")
new_block = ("," + SNL + '                "' + round_line + '",' + SNL
             + '                "' + tokens_line + '"')
state = prefix + new_block + state[last_item_end:]
parsed = json.loads(state.encode("utf-8").decode("utf-8"))
assert parsed["tick"] == 1941
assert len(parsed["log"]) >= 2
assert parsed["log"][-2].startswith("2026-10-14 R1941 ledger companion")
assert parsed["log"][-1].startswith("2026-10-14 R1941 tokens:")
write_txt(P_STATE, state)
print("state.json: tick 1941, +2 log lines,", len(state.encode("utf-8")),
      "bytes")

# ------------------------------------------------------------- heartbeat
P_HB = "heartbeat.txt"
hb = read_txt(P_HB)
HNL = eol_of(hb)
now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
hb_row = ("%s | BigDomain OSLoop alive | tick 1941 | R1941: ledger "
          "companion cross-restart persist suite 7/7 double-run "
          "byte-identical (sha16 dff152fd13809909) + RUNNER 179/179 "
          "criteria 1585->1592 (qa/reconcile-all-R1941.log) + matrix "
          "179/1592 --check identical + census DRIFT-CLEAN + fingerprint "
          "CLEAN + state.json EOL bare-LF repair (25->0) [via "
          "BigDomain-OSLoop]") % now
if not hb.endswith(HNL):
    hb += HNL
hb += hb_row + HNL
write_txt(P_HB, hb)
print("heartbeat row appended")

# ---------------------------------------------------------------- export
sys.path.insert(0, BASE)
import check_export_consistency as cec  # noqa: E402

derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1941, "stale tick: %s" % state_obj["tick"]
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
export_obj["ceo_face"]["current"] = (
    "R1941：伴生 AI 伴侣面（companion）做了「关服务重开、通行证/对话/记忆"
    "档案全复原、五道闸照常拦截、重启后补购通行证照样入账」的跨重启验证；"
    "总回归 179 套件全绿")
export_obj["ceo_face"]["latest_artifact"] = (
    "src/sandbox/ledger/test_companion_persist.py + qa/companion-persist-"
    "R1941.log + qa/reconcile-all-R1941.log，2026-10-14·179 套件 1592 判据"
    " green·新增 ledger-companion-persist·伴生读面族跨重启持久化例窗")
export_obj["ceo_face"]["next_milestone"] = (
    "下轮 R1942：tech 队列 FIFO=ledger props 道具/装扮经济面读面族 persist "
    "认领（R1937 补种·最老开项）")
res_row = [
    "R1941",
    ("R1941 ledger companion cross-restart persistence suite 7/7 (P2 "
     "tech FIFO head = the R1940 closeout pointer; criteria "
     "AC-CMP1..CMP7 pre-registered in tech.md before code, with the "
     "same-round pool-expectation erratum 19000->19330 and "
     "19090->19420 = the ledger spend counter-leg flows back to the "
     "pool, product-behavior orthodoxy cross-attested by the ads "
     "seat 17150 = 20000-3000+150; R1883 AC-PN27 same-round pen-slip "
     "precedent; first run 5/7 -> fixed -> green). Double-run stdout "
     "byte-identical sha16 dff152fd13809909. Three-instance world on "
     "the real product path (Ledger + SecGate lobby-product reference "
     "injection + CompanionFace): anchor (jan passes alice/bob fee 120 "
     "+ feb pass carol fee 90 each bound to one real spend tx; "
     "dialogue spectrum alice two archived rounds with same-kind "
     "memories twice = append-not-unique + bob one round + carol feb "
     "one round = 8 structural ai_label rows; can_ five probes "
     "a/b-jan True, c-jan False, c-feb True, a-feb False; transcript "
     "windows 4/2/0/2; memory views 2/0/0; subs views 1/1/1; balances "
     "180/380/110/19330; five gate probes all-reject incl. "
     "gate-fault = injected fault-gate face rebuilt on the same db "
     "fails closed; zero drift across the probe batch) -> close/"
     "reopen byte-identical (created_utc = stored values, zero "
     "in-memory drift) -> restart-surviving gates -> real-path "
     "continuation (carol buys the missing jan pass bound to a real "
     "spend tx with SQL cross type=spend + debit leg, denied->allowed "
     "flip proven, two new rounds + two memory appends, counts subs "
     "3->4 msgs 8->12 memories 2->4 spend-tx 3->4, balances "
     "180/380/20/19420) -> frozen faces (SQL full-row snapshots of "
     "all pre-existing rows byte-frozen incl. granted_utc/"
     "created_utc/content_json) + dup/denied/content gates across "
     "restart -> pure-read law -> third-instance stability. RUNNER "
     "PASS 179/179 criteria 1585->1592 controls 7/7 304.7s = qa/"
     "reconcile-all-R1941.log (ledger-companion-persist seat 0.8s, "
     "census DRIFT-CLEAN flags=0, fingerprint CLEAN domains=5); "
     "matrix 179/1592 green --check byte-identical (17468 bytes); "
     "state.json EOL bare-LF repair at round start (25 lines -> 0, "
     "74422B predicted==actual); evidence six-section qa/companion-"
     "persist-R1941.log via src/os/evidence_R1941.py; tech consume 1 "
     "reseed 1 (apimarket persist seeded with same-day dedup scans: "
     "registry zero apimarket-persist seat + AC-AMP git-grep rc=1 + "
     "base-suite close hits all cleanup/probe closes non-restart = "
     "single-Ledger true-activity candidate; next FIFO head = ledger "
     "props persist).")]
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
print("export refreshed: queues=%d/%d/%d tick=%d"
      % (derived["queue_main_open"], derived["queue_tech_open"],
         derived["queue_explore_open"], state_obj["tick"]))
print("R1941 closeout complete")
