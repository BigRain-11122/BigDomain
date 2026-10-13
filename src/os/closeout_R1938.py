# -*- coding: utf-8 -*-
"""R1938 closeout: ledger venue cross-restart persist delivery.
tech.md done-note + identity reseed, state.json tick/log/round-line,
heartbeat row, export refresh (F3 derived via consistency tool).
All edits anchor-exact with fail-fast asserts; EOL preserved per file.
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
venue_open_head = ("- [ ] ledger venue 场地面读面族跨重启持久化例窗"
                   "（R1936 补种·查重前置已过")
must_count(tech, venue_open_head, 1, "venue open row head")
tech = tech.replace(
    "- [ ] ledger venue 场地面读面族跨重启持久化例窗（R1936 补种",
    "- [x] ledger venue 场地面读面族跨重启持久化例窗（R1936 补种", 1)
done_row_head = ("- [x] ledger venue 场地面读面族跨重启持久化例窗"
                 "（R1936 补种")
must_count(tech, done_row_head, 1, "venue done row head")
done_note = (
    "——〔2026-10-14 R1938 认领〕——[done 2026-10-14 R1938]（执行注记："
    "套件 test_venue_persist.py SUITE 7/7 首跑一锚失败=E_VN_UNKNOWN plaza"
    "〔世界装载漏 register_venue 首行·产品无缺陷〕同窗补 register_venue"
    "(\"plaza\",2) 后全绿如实注+双跑 stdout 逐字节同一 sha16 "
    "0da016a9e9cd807a〔rc 0/0〕三实例世界真产品径——①锚世界〔mint 20000+"
    "三 adjust 注资 alice 2000/bob 600/carol 400+plaza cap2 并发三租"
    "〔alice [100,109]@50+bob [105,114]@40+carol [200,204]@15〕+booth-1 "
    "租终止谱〔alice [300,309]@30+terminate@305 零 token+bob [310,314]"
    "@15〕+五门探针全拒〔unknown/full/dup/lease-active/no-lease〕探针批"
    "前后 registry 2/occupancy 5/spend-tx 5+四余额 1920/545/385/17150 "
    "恒定+电池快照〔is_rented 九探针+tenant_of 八探针〔终止效应 305=alice/"
    "306=None〕+双单元全史〕digest c8315611ef644e8f②两件套逆序全 close"
    "→实例②同 db 同 cfg 重开→电池重读逐字节复原〔读面全 tick 参数化纯值"
    "零 ts 回显=零冻结钟需求·bound_spend_tx=盘面持久值〕③五门探针跨重启"
    "全拒同码+计数余额恒定④真径续写〔alice 再租 freed slot [110,114]@25+"
    "carol 租终止释放位 [306,309]@12→两新占行各绑真新 spend tx〔SQL 交叉"
    " type='spend'+debit 分录·tx_id 不入证〕+触面零缓存重算〔is_rented"
    "(plaza,alice,112) False→True/tenant_of(booth-1,307) None→carol/"
    "plaza 史 3→4·booth-1 史 2→3〕+occupancy 5→7/spend-tx 5→7/余额 "
    "1895/545/373/17187〕⑤冻结面+dup/容量门跨重启〔预存占行六持久字段"
    "逐字节冻结+同窗异 ref 再租 E_VN_DUP ref-blind+carol [112,116] "
    "E_VN_FULL 两活跃满位〕⑥纯读律电池双读计数恒定⑦实例③三开==实例②终态"
    "逐字节+config/venue/ledger sha16 三稳定+纯 ASCII+零网络 import+世界 "
    "tmp 仓外〕——RUNNER PASS 176/176 判据 1564→1571 controls 7/7 211.8s="
    "qa/reconcile-all-R1938.log〔SUITES 175→176·ledger-venue-persist 席·"
    "census DRIFT-CLEAN flags=0〕+矩阵再生 176/1571 green --check "
    "byte-identical〔17228B〕——证据五节 qa/venue-persist-R1938.log〔套件"
    "双跑+RUNNER tail+矩阵双跑+census+git 卫生〕·LF 归一单写者驱动=src/os/"
    "evidence_R1938.py〔R1932/R1937 模板族〕——tech consume 1 reseed 1"
    "〔queue_tech_open 10→10：venue done −1+ledger identity 城市身份面"
    "读面族 persist 补种 +1·下轮 FIFO 队头=minors 守护读面族 persist"
    "〔R1933 补种·最老开项〕〕·产品零字节〔suite-only 轮〕）")
v_idx = tech.find(done_row_head)
assert v_idx >= 0, "venue done row not found"
v_end = tech.find(NL, v_idx)
assert v_end >= 0, "venue row has no line end"
tech = tech[:v_end] + done_note + tech[v_end:]
identity_row = (
    "- [ ] ledger identity 城市身份面读面族跨重启持久化例窗"
    "（R1938 补种·查重前置已过：注册表 label 全形扫描零 identity-persist "
    "命名位 变体〔ledger-identity 基础席 7 判据在册=套件存在锚〕+套件源面"
    "扫描 test_identity.py 六 close 命中全为收尾清理非重启例=真活候选·"
    "AC-IDP 前缀全仓 git grep 零占用 2026-10-14〔rc=1〕·persist 例窗族 "
    "R1886 起谱系）")
props_line_start = "- [ ] ledger props 道具/装扮经济面读面族"
must_count(tech, props_line_start, 1, "props row head")
idx = tech.find(props_line_start)
end = tech.find(NL, idx)
tech = tech[:end] + NL + identity_row + tech[end:]
write_txt(P_TECH, tech)
print("tech.md: venue done-note + identity reseed ok")

# ------------------------------------------------------------- state.json
P_STATE = "src/os/state.json"
state = read_txt(P_STATE)
SNL = eol_of(state)
must_count(state, '"tick": 1937,', 1, "tick")
state = state.replace('"tick": 1937,', '"tick": 1938,', 1)
tok_anchor = "2026-10-14 R1937 tokens:"
must_count(state, tok_anchor, 1, "R1937 tokens anchor")
close_anchor = SNL + "    ]"
assert state.rstrip().endswith("}"), "state tail not }"
cidx = state.rfind(close_anchor)
assert cidx > state.find(tok_anchor), "log close before tokens anchor"
last_item_end = cidx
prefix = state[:last_item_end]
assert prefix.endswith('"'), "last log item does not end with quote"
round_line = (
    "2026-10-14 R1938 ledger venue 场地面读面族跨重启持久化例窗交付轮"
    "（P2 tech FIFO=R1937 收账指针·轮计分 2=可跑实物）：五静全绿——"
    "GORD gord_new_rows=0 基线 376 持平·DEC rows=309=基线 零新 owner "
    "token·LEDGER atbd=0·ORD 持平·BENCH 当日 10-14·QA 当日证据在盘"
    "〔smoke-R1936 对+daily 对账 10-14 在盘·常设行当日已毕零重跑〕·HB "
    "lag=0·TREE 净——雷达窗 6 清单 OH-20261014-cph4.md 21:40 今晚到窗="
    "雷达承接行 gated 续候合法〔下窗到达即过目〕——判据 AC-VNP1..VNP7 "
    "预注册先于代码〔tech.md 认领行在册·前缀认领轮复扫唯一命中族皆前向"
    "指针〕：套件 test_venue_persist.py SUITE 7/7〔首跑一锚失败=世界装载"
    "漏 register_venue·产品无缺陷·同窗修〕+双跑 stdout 逐字节同一 sha16 "
    "0da016a9e9cd807a 三实例世界〔①锚世界〔plaza cap2 三租并发+booth-1 "
    "租终止谱+五门探针全拒+电池 digest c8315611ef644e8f〕②两件套逆序关重"
    "开电池逐字节复原〔读面零 ts 回显零冻结钟需求〕③五门探针跨重启全拒"
    "④真径续写〔freed slot+终止释放位两新租绑真 spend tx·触面零缓存重算〕"
    "⑤冻结面+dup/容量门跨重启〔同窗异 ref E_VN_DUP ref-blind〕⑥纯读律"
    "⑦实例③三开==实例②终态+config/venue/ledger sha16 三稳定〕——RUNNER "
    "PASS 176/176 判据 1564→1571 controls 7/7 211.8s=qa/reconcile-all-"
    "R1938.log〔SUITES 175→176·census DRIFT-CLEAN flags=0〕+矩阵再生 "
    "176/1571 green --check byte-identical〔17228B〕——tech consume 1 "
    "reseed 1〔queue_tech_open 10→10：venue done −1+ledger identity "
    "persist 补种 +1〔查重预检：注册表零 identity-persist 位+test_identity"
    ".py 六 close 全非重启例+AC-IDP 全仓零占用〕·下轮 FIFO 队头=minors "
    "守护读面族 persist〔R1933 补种·最老开项〕〕——产品零字节〔suite-"
    "only 轮〕·fold 承传注记：轮首 scan state 73820B 未越 78500B 线="
    "零 fold 裁定〔收账后水位预测 ~76.5KB 仍在线下·下轮轮首首测照查〕")
tokens_line = (
    "2026-10-14 R1938 tokens: local=unmeasured api=0 api_reason=纯本地"
    "进程件（五静扫描+套件双跑+RUNNER 全量回归+矩阵 check+census+收账"
    "手术全本地跑·零外部 API 触点·三问门未涉及）")
new_block = ("," + SNL + '                "' + round_line + '",' + SNL
             + '                "' + tokens_line + '"')
state = prefix + new_block + state[last_item_end:]
parsed = json.loads(state.encode("utf-8").decode("utf-8"))
assert parsed["tick"] == 1938
assert len(parsed["log"]) >= 2
assert parsed["log"][-2].startswith("2026-10-14 R1938 ledger venue")
assert parsed["log"][-1].startswith("2026-10-14 R1938 tokens:")
write_txt(P_STATE, state)
print("state.json: tick 1938, +2 log lines,", len(state.encode("utf-8")),
      "bytes")

# ------------------------------------------------------------- heartbeat
P_HB = "heartbeat.txt"
hb = read_txt(P_HB)
HNL = eol_of(hb)
now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
hb_row = ("%s | BigDomain OSLoop alive | tick 1938 | R1938: venue "
          "cross-restart persist suite 7/7 double-run byte-identical "
          "sha16 0da016a9e9cd807a + RUNNER 176/176 criteria 1564->1571 "
          "(qa/reconcile-all-R1938.log) + matrix 176/1571 --check "
          "identical + census DRIFT-CLEAN "
          "[via BigDomain-OSLoop]") % now
if not hb.endswith(HNL):
    hb += HNL
hb += hb_row + HNL
write_txt(P_HB, hb)
print("heartbeat row appended")

# ---------------------------------------------------------------- export
sys.path.insert(0, BASE)
import check_export_consistency as cec  # noqa: E402

derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1938, "stale tick: %s" % state_obj["tick"]
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
export_obj["ceo_face"]["current"] = (
    "R1938：场地/店面租约面（venue）做了「关服务重开、读数一字不差、"
    "五道闸照常拦截」验证——租期/容量/提前退租/审计轨迹跨重启全保真；"
    "总回归 176 套件全绿；证据在 qa/venue-persist-R1938.log 与 "
    "qa/reconcile-all-R1938.log")
export_obj["ceo_face"]["latest_artifact"] = (
    "src/sandbox/ledger/test_venue_persist.py + qa/venue-persist-R1938.log"
    " + qa/reconcile-all-R1938.log，2026-10-14·176 套件 1571 判据 green·"
    "新增 ledger-venue-persist·场地读面族跨重启持久化例窗")
export_obj["ceo_face"]["next_milestone"] = (
    "下轮 R1939：tech 队列 FIFO=minors 守护读面族 persist 认领（R1933 "
    "补种·最老开项）+雷达窗 6 清单 OH-20261014-cph4.md 今晚 21:40 到窗"
    "即过目")
res_row = [
    "R1938",
    ("R1938 ledger venue cross-restart persistence suite 7/7 "
     "(P2 tech FIFO head = the R1937 closeout pointer; criteria "
     "AC-VNP1..VNP7 pre-registered in tech.md before code): "
     "three-instance world on the real product path - anchor "
     "(plaza capacity-2 concurrent rentals + storefront lease/"
     "terminate/re-lease spectrum, five gate probes rejected "
     "zero-charge, digest c8315611ef644e8f) -> two-piece reverse-order "
     "close/reopen with the is_rented/tenant_of/occupancy_ledger "
     "battery byte-identical (tick-parameterized pure-value read "
     "faces, zero clock echo, no frozen clock needed) -> five "
     "restart-surviving gates -> post-restart real-path continuation "
     "(freed plaza slot + termination-freed storefront window both "
     "re-rented, bound to real spend txs via SQL cross, zero-cache "
     "recompute) -> frozen faces + ref-blind dup gate + capacity gate "
     "across restart -> pure-read law -> third-instance stability; "
     "first-run one-anchor fail (world build missed register_venue, "
     "not a product defect) fixed same window, honestly noted; "
     "RUNNER PASS 176/176 criteria 1564->1571 controls 7/7 211.8s = "
     "qa/reconcile-all-R1938.log (census DRIFT-CLEAN); matrix regen "
     "176/1571 green --check byte-identical (17228 bytes); tech "
     "consume 1 reseed 1 (identity persist candidate added, "
     "queue_tech_open 10->10, next FIFO head = minors persist).")]
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
print("R1938 closeout complete")
