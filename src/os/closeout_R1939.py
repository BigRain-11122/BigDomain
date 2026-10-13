# -*- coding: utf-8 -*-
"""R1939 closeout: minors guardian cross-restart persist delivery +
crashed-round orphan-payload takeover closeout (seventh case of the
R1937 lineage). tech.md done-note + settlement reseed, state.json
tick/log/round-line, heartbeat row, export refresh (F3 derived via
consistency tool). All edits anchor-exact with fail-fast asserts;
EOL preserved per file.
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
minors_open_head = "- [ ] minors 守护读面族跨重启持久化例窗（R1933 补种"
must_count(tech, minors_open_head, 1, "minors open row head")
tech = tech.replace(
    "- [ ] minors 守护读面族跨重启持久化例窗（R1933 补种",
    "- [x] minors 守护读面族跨重启持久化例窗（R1933 补种", 1)
done_row_head = "- [x] minors 守护读面族跨重启持久化例窗（R1933 补种"
must_count(tech, done_row_head, 1, "minors done row head")
done_note = (
    "——[done 2026-10-14 R1939]（执行注记：套件 test_minors_persist.py "
    "SUITE 7/7+双跑 stdout 逐字节同一 sha16 dbc04a064efb027a〔rc 0/0·LF "
    "归一口径=evidence 驱动器·R1939 接管轮 live 复验 stdout 逐行同一=电池/"
    "报告/三实例三 sha16 全同证据面·raw-bytes sha 差=探针口径非内容差〕三实例"
    "世界真产品径——minors.py 载体=可选 sqlite 持久化层〔db_path=None 缺省"
    "纯内存现行径逐字节零漂移=R939/R940 wiring 19+70 判据零回归·db_path 给值="
    "独立件单写者 hydrate-at-open+db-first 镜像〔record_spend 先 commit db "
    "行再提交内存=崩溃窗日帽 spend 行不丢=fail-closed 持久方向〕+三表 "
    "mg_residents/mg_limits/mg_day_spend〔日账 append-only·UNIQUE(resident,"
    "date,ref)·零 UPDATE·零墙钟=日期/分钟全 caller 供给〕〕——①锚世界〔四居"
    "民谱 kid1 单窗+kid2 双窗+adult1 pass-through+kidX 零限配〕+八探针全拒"
    "〔TIME/SPEND_SINGLE/SPEND_DAILY/NO_LIMIT/LIVE_BAN/MARKETING_BAN/"
    "GUARDIAN/DUP〕+adult 四门 pass-through+探针批前后三表计数恒定+电池 "
    "sha16 90ac70fd49071b9e②face.close→实例②同 db_path 重开电池逐字节复原"
    "+同参二读自同一③八探针跨重启全拒同码+计数恒定④真径续写〔kid1 700 "
    "tx-sub-3@10-03 过门重算 1200/[tx-sub-2,tx-sub-3]≠缓存+新居民 kid3 全链"
    "持久+adult record_spend→E_MG_NOT_MINOR 拒〕⑤冻结面+幂等域〔10-02 历史"
    "桶冻结+kid2 tx-b 幂等重放 re-gate 过态吸收 idempotent True·db 行数不变"
    "+kid1 tx-sub-2 重放 re-gate 先行保守拒 E_MG_SPEND_DAILY 零变异〔AC-MGP5 "
    "预注册文字同窗勘正=AC-W7 re-gate 律·R1883 AC-PN27 先例〕+同 ref 异日="
    "新行 ref 域桶律〕⑥纯读律电池双读+render_report 双跑 sha16 "
    "3f7fab498fdecc3b⑦实例③三开==实例②终态 sha16 749b6d6eced3f35a+缺省径"
    "零漂移+shipped config 零字节+指纹哨兵 CLEAN〔独立件零五域 schema 触碰〕"
    "+套件源纯 ASCII+零网络 import+世界 db tmp 仓外〕——RUNNER PASS 177/177 "
    "判据 1571→1578 controls 7/7 290.2s=qa/reconcile-all-R1939.log〔SUITES "
    "176→177·minors-guard-persist 席·census DRIFT-CLEAN flags=0〕+矩阵再生 "
    "177/1578 green --check byte-identical〔17303B〕——证据六节 qa/minors-"
    "persist-R1939.log〔套件双跑+RUNNER tail+矩阵双跑+census+指纹+git 卫生〕"
    "·LF 归一单写者驱动=src/os/evidence_R1939.py〔R1932/R1937/R1938 模板族〕"
    "——本轮=崩溃轮孤儿载荷接管收口〔R1937 谱系第七例〕——tech consume 1 "
    "reseed 1〔queue_tech_open 10→10：minors done −1+ledger settlement 跨司"
    "分账读面族 persist 补种 +1·下轮 FIFO 队头=ledger ads 广告位 persist"
    "〔R1934 补种·最老开项〕〕）")
v_idx = tech.find(done_row_head)
assert v_idx >= 0, "minors done row not found"
v_end = tech.find(NL, v_idx)
assert v_end >= 0, "minors row has no line end"
tech = tech[:v_end] + done_note + tech[v_end:]
settlement_row = (
    "- [ ] ledger settlement 跨司分账读面族跨重启持久化例窗（R1939 补种·查重"
    "前置已过：注册表 label 全形扫描零 settlement-persist 命名位 变体"
    "〔ledger-settlement 基础席 7 判据在册=套件存在锚〕+套件源面扫描 "
    "test_settlement.py 零 close 命中〔面现况=纯内存无 close=与 minors 同起"
    "点真活候选〕·AC-SEP 前缀全仓 git grep 零占用 2026-10-14〔rc=1〕·persist "
    "例窗族 R1886 起谱系）")
identity_line_start = "- [ ] ledger identity 城市身份面读面族跨重启持久化例窗（R1938 补种"
must_count(tech, identity_line_start, 1, "identity row head")
idx = tech.find(identity_line_start)
end = tech.find(NL, idx)
tech = tech[:end] + NL + settlement_row + tech[end:]
write_txt(P_TECH, tech)
print("tech.md: minors done-note + settlement reseed ok")

# ------------------------------------------------------------- state.json
P_STATE = "src/os/state.json"
state = read_txt(P_STATE)
SNL = eol_of(state)
must_count(state, '"tick": 1938,', 1, "tick")
state = state.replace('"tick": 1938,', '"tick": 1939,', 1)
tok_anchor = "2026-10-14 R1938 tokens:"
must_count(state, tok_anchor, 1, "R1938 tokens anchor")
close_anchor = SNL + "    ]"
assert state.rstrip().endswith("}"), "state tail not }"
cidx = state.rfind(close_anchor)
assert cidx > state.find(tok_anchor), "log close before tokens anchor"
last_item_end = cidx
prefix = state[:last_item_end]
assert prefix.endswith('"'), "last log item does not end with quote"
round_line = (
    "2026-10-14 R1939 minors 守护读面族跨重启持久化例窗交付+崩溃轮孤儿载荷"
    "接管收口轮（P2 tech FIFO=R1938 收账指针·轮计分 2=可跑实物）：五静面——"
    "GORD 持平〔尾行 10-13 23:5x @bm-c relay·零新 @BigDomain 行〕·DEC token "
    "集差零新〔最新 D-20261013-02/C-20261013-01 已在前窗基线内〕·LEDGER "
    "atbd=0·BENCH 当日 10-14·QA 当日证据在盘〔reconcile-daily-20261014 已毕"
    "零重跑〕·HB lag=0·TREE FLAG 脏 8 件=崩溃轮孤儿载荷〔接管触发面〕——雷达"
    "窗 6 清单 OH-20261014-cph4.md 21:40 到窗未达〔03:37 实测 False〕=雷达承接"
    "行 gated 续候合法——接管验真〔R1937 谱系第七例〕：前窗崩溃 R1939 尝试留盘"
    "件八面全在〔minors.py sqlite 持久层+套件+注册行+认领行+矩阵再生+证据六节"
    "双 log qa/minors-persist-R1939.log+qa/reconcile-all-R1939.log·VERDICT "
    "PASS 零败跑工件〕→本轮 live 复验〔套件 stdout 逐行同一（电池/报告/三实例"
    "三 sha16 全同证据面）+双跑逐字节同一+矩阵 --check 同一·raw-bytes sha 差="
    "探针口径（CRLF 原字节 vs LF 归一）非内容差〕后收口——判据 AC-MGP1..MGP7 "
    "预注册先于代码〔tech.md 认领行在册·AC-MGP5 同窗勘正注记=AC-W7 re-gate "
    "先行律·R1883 AC-PN27 先例〕：SUITE 7/7 三实例世界〔①锚世界四居民谱+八探"
    "针全拒+电池 sha16 90ac70fd49071b9e②close→同 db_path 重开电池逐字节复原"
    "③八探针跨重启全拒④真径续写 kid1 700 重算+kid3 新居民持久+adult "
    "E_MG_NOT_MINOR 拒⑤历史桶冻结+kid2 幂等重放吸收+kid1 重放 re-gate 保守拒"
    "+ref 域桶律⑥纯读律+report 双跑 sha16 3f7fab498fdecc3b⑦实例③三开==②终态"
    "+缺省径零漂移+指纹 CLEAN〕——RUNNER PASS 177/177 判据 1571→1578 "
    "controls 7/7 290.2s=qa/reconcile-all-R1939.log〔SUITES 176→177·census "
    "DRIFT-CLEAN flags=0〕+矩阵再生 177/1578 green --check byte-identical"
    "〔17303B〕——产品面=minors.py +115 行可选 sqlite 持久化层〔db_path=None "
    "缺省纯内存现行径逐字节零漂移〔19+70 wiring 判据零回归〕·db-first 镜像="
    "崩溃窗日帽 spend 行不丢=sec.31 未成年人守护 fail-closed 持久方向〕——提案"
    "轨：新窗 10-14~10-21 首轮 BD-PROP-004 当轮补交〔qa 证据面月度归档防膨胀·"
    "三句式+判据 ≤3 问〕——tech consume 1 reseed 1〔queue_tech_open 10→10："
    "minors done −1+ledger settlement 跨司分账读面族 persist 补种 +1〔查重预"
    "检当日实跑：注册表零 settlement-persist 位+test_settlement.py 零 close 命"
    "中〔纯内存无 close=minors 同起点真活候选〕+AC-SEP 全仓 git grep 零占用〕"
    "·下轮 FIFO 队头=ledger ads 广告位 persist〔R1934 补种·最老开项〕〕——fold "
    "承传注记：轮首 scan state 76138B 未越 78500B 线=零 fold 裁定〔收账后水位"
    "预测 ~79.1KB 越 78500B 线=fold R509 下轮轮首首测裁定候选〕")
tokens_line = (
    "2026-10-14 R1939 tokens: local=unmeasured api=0 api_reason=纯本地进程件"
    "（五静扫描+接管验真+套件双跑重跑+矩阵 check+证据读回+收账手术全本地跑·"
    "零外部 API 触点·三问门未涉及）")
new_block = ("," + SNL + '                "' + round_line + '",' + SNL
             + '                "' + tokens_line + '"')
state = prefix + new_block + state[last_item_end:]
parsed = json.loads(state.encode("utf-8").decode("utf-8"))
assert parsed["tick"] == 1939
assert len(parsed["log"]) >= 2
assert parsed["log"][-2].startswith("2026-10-14 R1939 minors 守护")
assert parsed["log"][-1].startswith("2026-10-14 R1939 tokens:")
write_txt(P_STATE, state)
print("state.json: tick 1939, +2 log lines,", len(state.encode("utf-8")),
      "bytes")

# ------------------------------------------------------------- heartbeat
P_HB = "heartbeat.txt"
hb = read_txt(P_HB)
HNL = eol_of(hb)
now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
hb_row = ("%s | BigDomain OSLoop alive | tick 1939 | R1939: minors guardian "
          "cross-restart persist suite 7/7 double-run byte-identical "
          "(stdout line-for-line == evidence record) + RUNNER 177/177 "
          "criteria 1571->1578 (qa/reconcile-all-R1939.log) + matrix "
          "177/1578 --check identical + orphan-payload takeover closeout "
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
assert state_obj["tick"] == 1939, "stale tick: %s" % state_obj["tick"]
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
export_obj["ceo_face"]["current"] = (
    "R1939：未成年人守护面（minors）做了「关服务重开、监护限配/日消费帽/"
    "账面全复原、八道拒付闸照常拦截」的跨重启验证，并把守护账本落成可选 "
    "sqlite 持久层（崩溃窗日帽不丢=fail-closed 方向）；总回归 177 套件全绿；"
    "本轮=前窗崩溃交付的接管收口（live 复验内容逐行同一后上链）")
export_obj["ceo_face"]["latest_artifact"] = (
    "src/sandbox/minors/test_minors_persist.py + src/sandbox/minors/"
    "minors.py（sqlite 持久层）+ qa/minors-persist-R1939.log + qa/"
    "reconcile-all-R1939.log，2026-10-14·177 套件 1578 判据 green·新增 "
    "minors-guard-persist·守护读面族跨重启持久化例窗")
export_obj["ceo_face"]["next_milestone"] = (
    "下轮 R1940：tech 队列 FIFO=ledger ads 广告位读面族 persist 认领"
    "（R1934 补种·最老开项）+雷达窗 6 清单 OH-20261014-cph4.md 今晚 21:40 "
    "到窗即过目")
res_row = [
    "R1939",
    ("R1939 minors guardian cross-restart persistence suite 7/7 "
     "(P2 tech FIFO head = the R1938 closeout pointer; criteria "
     "AC-MGP1..MGP7 pre-registered in tech.md before code, with the "
     "AC-MGP5 same-window erratum = AC-W7 re-gate-first law, R1883 "
     "precedent) + crashed-round orphan-payload takeover closeout "
     "(seventh case of the R1937 lineage): the crashed R1939 attempt "
     "left all eight payload faces on disk with zero failed-run "
     "artifacts; this round live re-verified (suite stdout "
     "line-for-line identical to the evidence record with all three "
     "battery/report/instance digests matching, double-run "
     "byte-identical, matrix 177/1578 --check identical; raw-byte sha "
     "difference = probe caliber CRLF-vs-LF, not a content difference) "
     "and closed out. Product face = minors.py optional sqlite "
     "persistence layer (+115 lines: db_path=None default pure-memory "
     "path byte-identical drift-free for the 19+70 wiring criteria; "
     "db-first mirror so a crash window cannot lose a day-cap spend "
     "row = fail-closed persistence for the sec.31 minor-protection "
     "compliance face; three tables mg_residents/mg_limits/"
     "mg_day_spend, append-only day ledger with UNIQUE(resident,date,"
     "ref)). Three-instance world: anchor (four-resident spectrum + "
     "8 refused probes + battery sha16 90ac70fd49071b9e) -> close/"
     "reopen byte-identical -> 8 restart-surviving gates -> real-path "
     "continuation (kid1 700 recompute + kid3 fresh-resident "
     "persistence + adult refused) -> frozen history + re-gate-"
     "passing idempotent replay absorbed + conservative re-gate "
     "refusal + ref-domain bucket law -> pure-read law -> third-"
     "instance stability; RUNNER PASS 177/177 criteria 1571->1578 "
     "controls 7/7 290.2s = qa/reconcile-all-R1939.log (census "
     "DRIFT-CLEAN flags=0, fingerprint CLEAN domains=5); matrix "
     "177/1578 green --check byte-identical (17303 bytes); proposal-"
     "track BD-PROP-004 delivered (window 10-14~10-21, qa evidence "
     "monthly archive step); tech consume 1 reseed 1 (settlement "
     "persist seeded, next FIFO head = ledger ads persist).")]
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
print("R1939 closeout complete")
